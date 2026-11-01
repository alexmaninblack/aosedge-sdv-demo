#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One offline Vision image delta in the retained SSD-backed ARM64 Builder.

The caller exports committed Platform source. This specialist scenario preserves
the warm Main configuration byte-for-byte, gates package/image work, and never
launches a guest or changes a previously assembled Main image.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time

VERSION = '6.1.1-vision-camera.3'


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*2**20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'source', 'evidence', 'manifest', 'native-proof', 'store-proof', 'resource-proof'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--fresh-empty-proof', type=Path)
    a = p.parse_args()
    version='6.1.1-vision-camera.5' if a.fresh_empty_proof else VERSION
    require(os.uname().machine == 'aarch64' and os.uname().sysname == 'Linux', 'ARM64_BUILDER_REQUIRED')
    require(re.fullmatch('[a-f0-9]{40}', a.revision), 'REVISION_REQUIRED')
    for path in (a.project, a.source, a.evidence, a.manifest, a.native_proof, a.store_proof, a.resource_proof):
        require(path.is_absolute() and '..' not in path.parts and not any(q.is_symlink() for q in (path, *path.parents)), 'PATH_UNSAFE')
    require(a.project.name == 'factory42-475dc7c1ef3ac303', 'PINNED_WARM_PROJECT_REQUIRED')
    require(not a.evidence.exists(), 'BUILD_ATTEMPT_EXISTS_RECONCILE')
    proof = json.loads(a.native_proof.read_bytes())
    require(proof['outcome'] == 'PASS_TARGETED_NATIVE_UNIT' and proof['tests'] == 86, 'NATIVE_GATE_REQUIRED')
    store=json.loads(a.store_proof.read_bytes())
    require(store['outcome']=='PASS_TRANSIENT_STORE_ONLY' and all(store['cleanup'].values()),'STORE_TRANSIENT_GATE_REQUIRED')
    resource=json.loads(a.resource_proof.read_bytes())
    require(resource['outcome']=='PASS_TRANSIENT_CAMERA_OEM_AND_AOS_READ'
            and resource['cameraRestart']=='PASS_FRESH_EPOCH_WITHOUT_SOURCE'
            and resource['resourceRevocation']=='PASS' and all(resource['cleanup'].values()),'RESOURCE_TRANSIENT_GATE_REQUIRED')
    require(a.source.name == 'aos-vehicle-platform-'+a.revision, 'SOURCE_REVISION_BINDING_REQUIRED')
    require((a.source/'qualification/vision-bootstrap-1.conf').is_file(), 'VISION_SOURCE_REQUIRED')
    if a.fresh_empty_proof:
        empty=json.loads(a.fresh_empty_proof.read_bytes())
        require(empty['outcome']=='PASS_EMPTY_VISION_PUBLICATION_GATE' and empty['facts']['ready']
            and empty['facts']['oldUnitAbsent'] and empty['facts']['allVerificationMembersAbsent']
            and all(empty['cleanup'].values()),'FRESH_EMPTY_RECIPIENT_GATE_REQUIRED')
    a.evidence.mkdir(mode=0o700)
    lock = (a.project/'.vision-bootstrap-build.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    result = dict(scenario='VISION_BOOTSTRAP_IMAGE', outcome='NOT_COMPLETE', platformRevision=a.revision,
                  phases=[], mainConfigurationRestored=False, carlaRebuilt=False)
    config = a.project/'yocto/build-main/conf/bblayers.conf'
    before = config.read_bytes()
    old = str(a.project/'yocto/aos-vehicle-platform/meta-aos-vehicle-platform').encode()
    require(before.count(old) == 1, 'MAIN_LAYER_BINDING_UNEXPECTED')
    selected = before.replace(old, str(a.source/'meta-aos-vehicle-platform').encode())
    prefix = 'cd '+shlex.quote(str(a.project/'yocto'))+'; . poky/oe-init-build-env build-main >/dev/null; '
    flags = ['-R', str(a.source/'qualification'/('vision-fresh-1.conf' if a.fresh_empty_proof else 'vision-bootstrap-1.conf'))]
    started = time.monotonic()

    def save():
        path = a.evidence/'result.json'
        temporary = path.with_suffix('.pending')
        temporary.write_text(json.dumps(result, indent=2)+'\n')
        os.replace(temporary, path)

    def run(name, args, timeout, bitbake=True):
        require(shutil.disk_usage(a.project).free >= 60*1024**3, 'BUILDER_FREE_SPACE_BELOW_60_GIB')
        print(json.dumps(dict(stage=name, state='STARTED')), flush=True)
        begin = time.monotonic()
        with (a.evidence/(name+'.log')).open('wb') as log:
            command = prefix+shlex.join(['bitbake', *flags, *args]) if bitbake else shlex.join(args)
            done = subprocess.run(['bash', '-e', '-c', command], cwd=a.project, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        result['phases'].append(dict(stage=name, exit=done.returncode, seconds=round(time.monotonic()-begin, 2)))
        save()
        require(done.returncode == 0, 'VISION_BUILD_STAGE_FAILED:'+name)
        print(json.dumps(dict(stage=name, state='COMPLETE')), flush=True)

    try:
        config.write_bytes(selected)
        run('configuration', ['-e', 'aos-image-vision'], 300)
        data = (a.evidence/'configuration.log').read_text()
        def variable(name):
            values = re.findall('^'+re.escape(name)+'="(.*)"$', data, re.M)
            require(len(values) == 1, 'CONFIGURATION_VARIABLE_MISSING:'+name)
            return values[0]
        for name, value in {'BB_NO_NETWORK':'1', 'AOS_UNIT_MODEL':'aos-vision-vm',
                            'AOS_NODE_TYPE':'aos-vision-vm-main', 'AOS_ROOTFS_IMAGE_VERSION':version,
                            'AOS_COMPONENT_RUNTIME_PREFIX':'aos-vision-vm-1.0.0-main-qemuarm64-'}.items():
            require(variable(name) == value, 'CONFIGURATION_MISMATCH:'+name)
        rootfs = Path(variable('IMAGE_ROOTFS'))
        require(rootfs.is_relative_to(a.project/'yocto/build-main/tmp'), 'ROOTFS_SCOPE_INVALID')
        run('compile', ['-c', 'compile', 'aos-servicemanager', 'refpolicy-aos', 'aos-camera-access-platform'], 3600)
        run('package-qa', ['aos-servicemanager', 'refpolicy-aos', 'aos-camera-access-platform'], 3600)
        run('image', ['aos-image-vision'], 5400)
        sm = json.loads((rootfs/'etc/aos/sm.cfg').read_bytes())
        targets = [v for v in sm['runtimes'] if v['plugin'] == 'systemd-slot-component']
        require(len(targets) == 1 and targets[0]['type'] == 'aos-vision-vm-1.0.0-main-qemuarm64-camera-access', 'VISION_TARGET_NOT_BUILT')
        require(targets[0]['config']['componentProfile'] == 'camera-access-v1', 'VISION_PROFILE_NOT_BUILT')
        resources = json.loads((rootfs/'etc/aos/resources.cfg').read_bytes())
        require([r['name'] for r in resources] == ['vision-camera-read'], 'VISION_RESOURCE_NOT_BUILT')
        require(not (rootfs/'usr/libexec/aos-vehicle-data-provider-launcher').exists(), 'VDP_INCLUDED')
        require(not (rootfs/'etc/systemd/system/aos-sm.service.d/40-aos-demo-service-inputs.conf').exists(), 'VDP_PROJECTION_INCLUDED')
        require('aos-camera-access:' in (rootfs/'etc/passwd').read_text(), 'CAMERA_STATIC_ACCOUNT_MISSING')
        require((rootfs/'usr/libexec/aos-camera-access-store-check').is_file(), 'CAMERA_STORE_OWNER_MISSING')
        require((rootfs/r'usr/lib/systemd/system/var-aos-workdirs-sm-runtimes-systemd\x2dslot\x2dcamera\x2daccess.mount').is_file(), 'CAMERA_STORE_MOUNT_NOT_SHIPPED')
        if a.fresh_empty_proof:
            require((rootfs/'etc/aos/version').read_text().strip()=='VERSION="'+version+'"','FRESH_VERSION_NOT_BUILT')
            require((rootfs/'usr/libexec/aos-camera-ingress-launcher').is_file(),'FRESH_INGRESS_LAUNCHER_MISSING')
            def enabled(name):return any(p.name==name and p.is_symlink() and p.parent.name.endswith(('.wants','.requires'))
                for p in (rootfs/'etc/systemd/system').rglob('*'))
            require(enabled('systemd-networkd.service') and enabled('sshd.socket'),'FRESH_NETWORK_OR_SSH_PRESET_MISSING')
            require(not enabled('aos-camera-ingress.service'),'FRESH_INGRESS_BOOT_ENABLED')
            run('rootfs-fota',['aos-rootfs-vision'],3600)
            payload=a.project/'yocto/build-main/tmp/deploy/images/qemuarm64/update'/('aos-vision-rootfs-'+version+'.squashfs')
            require(payload.is_file() and not payload.is_symlink(),'FRESH_FOTA_MISSING')
            result['rootfsArtifact']=dict(rootfsVersion=version,path=str(payload),bytes=payload.stat().st_size,sha256=sha(payload))
        # Derive only image assembly variables; do not regenerate Main's graph.
        manifest = a.manifest.read_text()
        for key, old_value, new_value in (
            ('UNIT_MODEL', 'aos-vm', 'aos-vision-vm'),
            ('ROOTFS_IMAGE_VERSION', '6.1.1-maninblack.42', version),
            ('AOS_BASE_IMAGE', 'aos-image-vm', 'aos-image-vision')):
            pattern = '  '+key+': "'+old_value+'"'
            require(manifest.count(pattern) == 1, 'ASSEMBLY_MANIFEST_CHANGED:'+key)
            manifest = manifest.replace(pattern, '  '+key+': "'+new_value+'"')
        platform_old = '81d098e5a958710d8c12a6bfdb86c7c493274920'
        require(manifest.count(platform_old) == 1, 'ASSEMBLY_SOURCE_PIN_CHANGED')
        manifest = manifest.replace(platform_old, a.revision)
        selected_manifest = a.evidence/'vision.yaml'
        selected_manifest.write_text(manifest)
        output = a.project/('main-qemuarm64-'+version+'.img')
        require(not output.exists(), 'ASSEMBLED_IMAGE_EXISTS_RECONCILE')
        run('assemble', ['/home/yocto/.local/bin/rouge', str(selected_manifest), '--MACHINE=qemuarm64',
                         '--NODE_TYPE=main', '--WITH_MESSAGE_PROXY=no', '--CACHE_LOCATION=outside',
                         '-fi', 'main-qemuarm64', '-o', str(output)], 600, False)
        require(output.is_file() and 0 < output.stat().st_size <= 16*1024**3, 'IMAGE_INVALID')
        result.update(outcome='IMAGE_BUILT_NOT_LIVE_QUALIFIED', factoryVersion=version,
                      path=str(output), bytes=output.stat().st_size, sha256=sha(output),
                      rootfsQa='PASS', offline=True)
    except Exception as error:
        result['code'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
    finally:
        require(config.read_bytes() == selected, 'LAYER_CONFIGURATION_CONCURRENT_CHANGE')
        config.write_bytes(before)
        result.update(mainConfigurationRestored=config.read_bytes() == before, seconds=round(time.monotonic()-started, 2))
        save()
        print(json.dumps(result), flush=True)
        lock.close()
    return 0 if result['outcome'] == 'IMAGE_BUILT_NOT_LIVE_QUALIFIED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
