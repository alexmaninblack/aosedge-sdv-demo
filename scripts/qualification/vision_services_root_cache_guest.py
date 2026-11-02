# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact immutable Rootfs .6 blob reconciliation, never a database/spec rewrite."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

MANIFEST='57cf756b0006640927d12508d146d6f8cfb72270b0bebbf03dded70cdf53ddd4'
LAYER='8aa022a71190f6c6b153a36f3a6840bc9d1b0e37da0352292badc36c4ae9e07c'
OLD=Path('/var/aos/workdirs/cm/imagemanager/install/blobs/sha256')
NEW=Path('/var/aos/downloads/vision-services/cm-images/blobs/sha256')


def require(ok,code):
    if not ok:raise ValueError(code)


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):value.update(block)
    return value.hexdigest()


def owner():
    raw=subprocess.check_output(['systemctl','show','aos-cm','-p','ActiveState','-p','MainPID','-p','NRestarts'],text=True)
    return dict(line.split('=',1) for line in raw.splitlines())


def closure(spec,manifest_size):
    require(spec.get('schemaVersion')==2 and len(spec.get('layers',[]))==1,'ROOT_CACHE_MANIFEST_CHANGED')
    require(spec['layers'][0]==dict(digest='sha256:'+LAYER,size=130248720,
        mediaType='application/vnd.aos.image.component.full.v1+squashfs'),'ROOT_CACHE_LAYER_CHANGED')
    require(spec.get('config')==dict(digest='sha256:ae0b9e133e12f4b2312450cc0473844950645728712062f7978f09f21bee1da0',
        size=160,mediaType='application/vnd.oci.image.config.v1+json'),'ROOT_CACHE_OCI_CONFIG_CHANGED')
    require(spec.get('aosItemConfig')==dict(digest='sha256:93716e27fd5a4af8304a4590a870ef79ebadbdc8268c4b9f14d063f2908b259c',
        size=176,mediaType='application/vnd.aos.item.config.v1+json'),'ROOT_CACHE_ITEM_CONFIG_CHANGED')
    raw_sizes={LAYER:130248704,
        'ae0b9e133e12f4b2312450cc0473844950645728712062f7978f09f21bee1da0':152,
        '93716e27fd5a4af8304a4590a870ef79ebadbdc8268c4b9f14d063f2908b259c':169}
    rows={MANIFEST:manifest_size}
    for row in [spec['config'],spec['aosItemConfig'],*spec['layers']]:
        hash_=row['digest'].removeprefix('sha256:')
        # The CM store contains verified decrypted bytes, not the encrypted
        # transfer length in the immutable OCI descriptor. Verify the raw
        # layer against the original signed payload size AND SHA-256.
        rows[hash_]=raw_sizes[hash_]
    require(len(rows)==4,'ROOT_CACHE_CLOSURE_CHANGED');return rows


def complete_index_closure(rows):
    """CM retains blobs through its stored item INDEX, not the manifest alone."""
    candidates=[]
    for path in OLD.iterdir():
        if len(path.name)!=64 or any(c not in '0123456789abcdef' for c in path.name) or path.is_symlink() or not path.is_file() or path.stat().st_size>65536:continue
        try:spec=json.loads(path.read_bytes())
        except (ValueError,UnicodeError):continue
        if not isinstance(spec,dict) or not isinstance(spec.get('manifests'),list):continue
        if not any(isinstance(row,dict) and row.get('digest')=='sha256:'+MANIFEST for row in spec['manifests']):continue
        require(spec.get('schemaVersion')==2 and len(spec['manifests'])==1 and digest(path)==path.name,
            'ROOT_CACHE_ORIGINAL_INDEX_INVALID')
        require(spec['manifests'][0].get('mediaType')=='application/vnd.oci.image.manifest.v1+json','ROOT_CACHE_INDEX_MEDIA_INVALID')
        candidates.append(path)
    require(len(candidates)==1,'ROOT_CACHE_ORIGINAL_INDEX_NOT_UNIQUE')
    path=candidates[0];result=dict(rows);result[path.name]=path.stat().st_size
    require(len(result)==5,'ROOT_CACHE_FULL_CLOSURE_CHANGED');return result


def binding():
    require(os.geteuid()==0 and Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc','ROOT_CACHE_TARGET_CHANGED')
    require(Path('/etc/aos/version').read_text().strip()=='VERSION="6.1.1-vision-camera.6"'
        and Path('/sys/fs/selinux/enforce').read_text().strip()=='1','ROOT_CACHE_PLATFORM_CHANGED')
    runtime=Path('/var/aos/workdirs/sm/runtimes/rootfs')
    installed=json.loads((runtime/'installed_instance.json').read_bytes())
    require(installed['version']=='6.1.1-vision-camera.6' and installed['manifestDigest']=='sha256:'+MANIFEST
        and installed['itemId']=='40ed2e6e-2aee-45f5-af80-3ab6928771ff','ROOT_CACHE_NATIVE_ARTIFACT_CHANGED')
    require(not any((runtime/name).exists() for name in ('pending_instance.json','do_update','updated','do_apply','failed')),'ROOT_CACHE_UPDATE_ACTIVE')
    camera=Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
    require(json.loads((camera/'state/installed.json').read_bytes())['Version']=='0.1.2' and not (camera/'state/transaction.json').exists(),'ROOT_CACHE_CAMERA_UPDATE_ACTIVE')
    require(json.loads(Path('/etc/aos/cm.cfg').read_bytes())['imageManager']['installPath']==str(NEW.parents[1])
        and os.path.ismount('/var/aos/downloads'),'ROOT_CACHE_CURRENT_OWNER_PATH_CHANGED')
    for root in (OLD,NEW):
        require(root.is_dir() and not any(p.is_symlink() for p in (root,*root.parents)) and root.stat().st_uid==0,'ROOT_CACHE_PATH_UNSAFE')
    manifest=OLD/MANIFEST;require(manifest.is_file() and manifest.stat().st_size<65536 and digest(manifest)==MANIFEST,'ROOT_CACHE_ORIGINAL_MANIFEST_CHANGED')
    spec=json.loads(manifest.read_bytes());rows=complete_index_closure(closure(spec,manifest.stat().st_size))
    for hash_,size in rows.items():
        path=OLD/hash_;info=path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022 and info.st_size==size and digest(path)==hash_,'ROOT_CACHE_ORIGINAL_BLOB_CHANGED')
        target=NEW/hash_
        if target.exists():require(not target.is_symlink() and target.is_file() and target.stat().st_size==size and digest(target)==hash_,'ROOT_CACHE_CURRENT_BLOB_CONFLICT')
    return rows


def run(action):
    global STEP
    STEP='binding'
    if action=='audit':
        require(digest(OLD/MANIFEST)==MANIFEST,'ROOT_CACHE_ORIGINAL_MANIFEST_CHANGED')
        rows=complete_index_closure(closure(json.loads((OLD/MANIFEST).read_bytes()),(OLD/MANIFEST).stat().st_size))
        result=[]
        for hash_,size in rows.items():
            pair={}
            for label,root in (('original',OLD),('current',NEW)):
                path=root/hash_;row=dict(present=path.exists())
                if path.exists():
                    info=path.lstat();row.update(regular=stat.S_ISREG(info.st_mode),uid=info.st_uid,
                        mode=oct(stat.S_IMODE(info.st_mode)),bytes=info.st_size,digestMatches=digest(path)==hash_)
                pair[label]=row
            result.append(dict(sha256=hash_,expectedBytes=size,**pair))
        pending=[]
        for hash_,size in rows.items():
            path=NEW/('.root6-'+hash_+'.pending')
            if path.exists():pending.append(dict(sha256=hash_,bytes=path.stat().st_size,digestMatches=digest(path)==hash_,uid=path.stat().st_uid))
        indices={}
        for name,path in (('original',OLD.parents[1]/'index.json'),('current',NEW.parents[1]/'index.json')):
            indices[name]=dict(present=path.is_file(),referencesRoot6=path.is_file() and MANIFEST.encode() in path.read_bytes())
        databases=[]
        try:
            import sqlite3
            for path in Path('/var/aos/workdirs/cm').rglob('*.db'):
                if path.is_symlink() or not path.is_file():continue
                with path.open('rb') as stream:magic=stream.read(16)
                if magic!=b'SQLite format 3\x00':continue
                connection=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)
                try:
                    connection.execute('PRAGMA query_only=ON')
                    found=connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imagemanager'").fetchone()
                    if found:
                        rows_=connection.execute('SELECT itemID,type,version,indexDigest,state FROM imagemanager WHERE itemID=?',
                            ('40ed2e6e-2aee-45f5-af80-3ab6928771ff',)).fetchall()
                        databases.append(dict(relativePath=str(path.relative_to('/var/aos/workdirs/cm')),rootfsRows=[
                            dict(zip(('itemId','type','version','indexDigest','state'),row)) for row in rows_]))
                finally:connection.close()
        except ImportError:databases=[dict(readOnlySqliteUnavailable=True)]
        return dict(blobs=result,readOnly=True,pending=pending,cm=owner(),ociIndices=indices,chconAvailable=shutil.which('chcon') is not None,
            readOnlyRootfsCatalog=databases,
            protectedFilesPresent={p:Path(p).is_file() for p in ('/etc/aos/cm.cfg','/etc/aos/sm.cfg','/etc/aos/iam.cfg','/etc/aos/resources.cfg',
                '/sys/fs/selinux/policy','/var/aos/workdirs/sm/runtimes/rootfs/installed_instance.json',
                '/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access/state/installed.json')})
    require(action in ('inspect','repair','native'),'ROOT_CACHE_OPERATION_DENIED');rows=binding()
    if action=='native':
        root=next(line.split() for line in Path('/proc/mounts').read_text().splitlines() if line.split()[1]=='/')
        require(root[0]=='/dev/sda3' and root[2]=='ext4' and 'ro' in root[3].split(','),'ROOT_CACHE_NATIVE_ROOT_CHANGED')
        state=owner();require(state['ActiveState']=='active' and state['NRestarts']=='0','ROOT_CACHE_OWNER_NOT_HEALTHY')
        uid=next(line.split()[1:] for line in (Path('/proc')/state['MainPID']/'status').read_text().splitlines() if line.startswith('Uid:'))
        return dict(rootfsCommittedReadOnly=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',cmUids=uid,
            immutableConfiguration={str(p):digest(p) for p in map(Path,('/etc/aos/cm.cfg','/etc/aos/sm.cfg','/etc/aos/iam.cfg',
                '/etc/aos/resources.cfg','/sys/fs/selinux/policy','/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access/state/installed.json'))})
    missing={hash_:size for hash_,size in rows.items() if not (NEW/hash_).exists()}
    facts=dict(originalClosureVerified=True,manifestSha256=MANIFEST,layerSha256=LAYER,missing=missing,missingBytes=sum(missing.values()),
        originalsPreserved=True,databaseChanged=False,rootfsChanged=False)
    if action=='inspect':return facts
    STEP='protected-before'
    require(missing and shutil.disk_usage(NEW).free>=sum(missing.values())+32*1024**2,'ROOT_CACHE_REPAIR_NOT_REQUIRED_OR_CAPACITY')
    before={str(p):digest(p) for p in map(Path,('/etc/aos/cm.cfg','/etc/aos/sm.cfg','/etc/aos/iam.cfg','/etc/aos/resources.cfg','/sys/fs/selinux/policy',
        '/var/aos/workdirs/sm/runtimes/rootfs/installed_instance.json','/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access/state/installed.json'))}
    STEP='owner-before';state=owner();require(state['ActiveState']=='active' and state['NRestarts']=='0','ROOT_CACHE_OWNER_NOT_HEALTHY')
    references=[p for p in NEW.iterdir() if p.name not in rows and p.is_file() and not p.is_symlink()]
    require(references,'ROOT_CACHE_CURRENT_LABEL_REFERENCE_REQUIRED');reference=references[0];copied=[]
    STEP='owner-stop';subprocess.run(['systemctl','stop','aos-cm'],check=True,capture_output=True,timeout=30)
    try:
        require(owner()['MainPID']=='0','ROOT_CACHE_OWNER_NOT_QUIESCENT')
        for hash_,size in missing.items():
            STEP='blob-copy-'+hash_
            target=NEW/hash_;temporary=NEW/('.root6-'+hash_+'.pending');require(not target.exists() and not temporary.exists(),'ROOT_CACHE_DESTINATION_OCCUPIED')
            with temporary.open('xb') as output,(OLD/hash_).open('rb') as source:
                os.fchmod(output.fileno(),stat.S_IMODE((OLD/hash_).stat().st_mode));shutil.copyfileobj(source,output,1024**2);output.flush();os.fsync(output.fileno())
            require(temporary.stat().st_size==size and digest(temporary)==hash_,'ROOT_CACHE_COPY_CHANGED')
            subprocess.run(['chcon','--reference='+str(reference),str(temporary)],check=True,capture_output=True,timeout=5)
            os.link(temporary,target);temporary.unlink();copied.append(dict(sha256=hash_,bytes=size))
    finally:
        previous=STEP;STEP='owner-start'
        subprocess.run(['systemctl','start','aos-cm'],check=True,capture_output=True,timeout=30)
        STEP=previous
    require(owner()['ActiveState']=='active' and owner()['NRestarts']=='0','ROOT_CACHE_OWNER_RESTART_UNCONFIRMED')
    STEP='protected-after';require(all(digest(Path(p))==pin for p,pin in before.items()),'ROOT_CACHE_PROTECTED_CONTENT_CHANGED')
    require(all(digest(OLD/hash_)==digest(NEW/hash_)==hash_ for hash_ in rows),'ROOT_CACHE_RECONCILIATION_FAILED')
    return dict(facts,copied=copied,currentClosureVerified=True,cmRestartedOnce=True,canonicalConfigurationAndPolicyUnchanged=True)
