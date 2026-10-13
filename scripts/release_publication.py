# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Ordered source fan-in and immutable public preview delivery through normal owners."""
import json
from pathlib import Path
import shutil

from release_automation import ROOT, require, atomic, read
from release_owners import git, metadata, sha


def remote_main(repo):
    rows=git(repo,'ls-remote','origin','refs/heads/main').splitlines()
    require(len(rows)==1 and rows[0].split()[1]=='refs/heads/main','REMOTE_MAIN_UNAVAILABLE')
    return rows[0].split()[0]


def active_sources(owner):
    from developer_build import selected_plan
    from reproduction.chain import read_plan
    from reproduction.core import Release
    path=selected_plan(ROOT);plan=read_plan(Release(),path)
    require(plan.get('schemaVersion')==3 and
            plan['nativeSources']['vehicle-gateway']['revision']==git(owner.gateway,'rev-parse','HEAD'),
            'DEVELOPER_BUILD_SELECTION_STILL_HISTORICAL')
    return dict(plan=path.relative_to(ROOT).as_posix(),sha256=sha(path),nativeSources=plan['nativeSources'])


def integrate(owner):
    selected=active_sources(owner)
    targets=dict(integration=git(ROOT,'rev-parse','HEAD'),gateway=git(owner.gateway,'rev-parse','HEAD'))
    intent=owner.root/'main-intent.json'
    if intent.exists():
        require(read(intent)==dict(before=owner.config['expectedMain'],targets=targets),
                'MAIN_INTENT_CHANGED')
    else:atomic(intent,dict(before=owner.config['expectedMain'],targets=targets))
    for role,repo in [('gateway',owner.gateway),('integration',ROOT)]:
        target=targets[role];before=owner.config['expectedMain'][role];observed=remote_main(repo)
        require(observed in (before,target),'REMOTE_MAIN_CHANGED')
        if observed!=target:
            # A normal fast-forward push rejects races; no force or reset.
            git(repo,'push','origin',target+':refs/heads/main')
        require(remote_main(repo)==target,'MAIN_PUSH_UNCONFIRMED')
        local=git(repo,'rev-parse','refs/heads/main')
        require(local in (before,target),'LOCAL_MAIN_CHANGED')
        if local!=target and 'branch refs/heads/main' not in git(repo,'worktree','list','--porcelain').splitlines():
            git(repo,'update-ref','refs/heads/main',target,local)
    return dict(main=targets,activeBuild=selected)


def client(owner):
    from reproduction.delivery import Client
    gcloud=shutil.which('gcloud');require(gcloud is not None,'GOOGLE_CLI_UNAVAILABLE')
    return Client(gcloud,owner.config['delivery']['account'])


def descriptor(owner):
    files=list(owner.candidate.glob('*.dmg'));require(len(files)==1,'EXACT_MEDIA_REQUIRED')
    receipt=metadata(files[0].with_suffix('.receipt.json'))
    manifest=metadata(owner.candidate/'Runtime Kit/application-manifest.json')
    return dict(schemaVersion=1,productVersion=owner.config['version'],
        status='ENGINEERING_CANDIDATE_NOT_QUALIFIED',file='AosEdge-SDV-Lab-'+owner.config['version']+'.dmg',
        bytes=receipt['dmgBytes'],sha256=receipt['dmgSha256'],
        buildKey=manifest['packagingCheckpoint']['sha256'],producerRevision=manifest['sourceRevision'],
        manifestSha256=receipt['manifestSha256'],signing='apple-development-local-only',notarized=False)


def publish(owner):
    if owner.config['delivery'].get('provider')=='dropbox':
        # The operator has already copied this artifact to the shared folder.
        # Adopt its exact reviewed link by metadata, never upload it again.
        from reproduction.dropbox_public import observe
        expected=descriptor(owner)
        atomic(owner.root/'delivery-descriptor.json',expected)
        facts=observe(owner.config['delivery']['downloadURL'],expected['bytes'])
        return dict(provider='dropbox',downloadURL=facts['publicDownloadURL'],
                    metadata=facts,descriptorSha256=sha(owner.root/'delivery-descriptor.json'))
    from reproduction.delivery import upload
    expected=descriptor(owner);selected=owner.config['delivery'];c=client(owner)
    c.preflight(selected['folderId'],expected,public=True)
    atomic(owner.root/'delivery-descriptor.json',expected)
    def progress(stage,count):
        if stage=='UPLOAD_BYTES':
            fraction=min(1,count/expected['bytes']);width=30;done=int(fraction*width)
            print('\r    '+expected['file']+' ['+'#'*done+'-'*(width-done)+f'] {100*fraction:5.1f}%',end='',flush=True)
            if count==expected['bytes']:print()
        else:print('    '+stage,flush=True)
    source=next(owner.candidate.glob('*.dmg'))
    meta=upload(c,source,expected,selected['folderId'],owner.root/'upload-intent.json',
                check=owner.storage,progress=progress,public=True,
                verified_source=read(owner.root/'artifact-verification.json'))
    return dict(fileId=meta['id'],folderId=selected['folderId'],sha256=meta['sha256Checksum'],
        bytes=int(meta['size']),providerVersion=meta['version'],descriptorSha256=sha(owner.root/'delivery-descriptor.json'))


def stage(owner,name):
    if name=='main-integration':return integrate(owner)
    if name=='publication':return publish(owner)
    from release_operator_proof import promote
    return promote(owner)


def verify_saved(owner,name,facts):
    if name=='main-integration':
        expected=dict(facts['main'])
        promotion=owner.root/'operator-promotion.json'
        if promotion.exists() and read(promotion).get('outcome')=='PASS':
            expected['integration']=read(promotion)['facts']['main']
        require(all(remote_main(repo)==expected[role] for role,repo in
                    [('gateway',owner.gateway),('integration',ROOT)]),'PUBLISHED_MAIN_CHANGED')
    elif name=='publication':
        if facts.get('provider')=='dropbox':
            from reproduction.dropbox_public import observe
            require(facts['downloadURL']==owner.config['delivery']['downloadURL'],'DROPBOX_LINK_CHANGED')
            require(observe(facts['downloadURL'],descriptor(owner)['bytes'])==facts['metadata'],
                    'DROPBOX_METADATA_CHANGED')
        else:
            from reproduction.delivery import check_remote
            check_remote(client(owner).metadata(facts['fileId']),facts['fileId'],facts['folderId'],descriptor(owner),public=True)
    else:
        from release_operator_proof import verify_saved as verify_operator
        verify_operator(owner,facts)


def reconcile(owner,name,previous):
    if name=='main-integration':
        p=owner.root/'main-intent.json'
        if not p.exists():return False
        intent=read(p)
        return all(remote_main(repo) in (intent['before'][role],intent['targets'][role]) for role,repo in
                   [('gateway',owner.gateway),('integration',ROOT)])
    if name=='publication':
        if owner.config['delivery'].get('provider')=='dropbox':
            from reproduction.dropbox_public import observe
            observe(owner.config['delivery']['downloadURL'],descriptor(owner)['bytes'])
            return True  # HEAD only; there was no external publication mutation.
        p=owner.root/'upload-intent.json'
        if not p.exists():return False
        intent=read(p)
        meta=client(owner).metadata(intent['fileId'])
        if meta is None:return False
        from reproduction.delivery import check_remote
        check_remote(meta,intent['fileId'],owner.config['delivery']['folderId'],descriptor(owner),public=True)
        return True
    from release_operator_proof import reconcile as reconcile_operator
    return reconcile_operator(owner,previous)
