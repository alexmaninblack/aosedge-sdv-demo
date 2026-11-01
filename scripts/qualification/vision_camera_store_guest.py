#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reversible fixed Camera-store proof in an unprovisioned disposable guest."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path('/run/vision-camera-store-proof')
STORE=Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
BACKING=STORE.parent/'.camera-access-store.ext4'
IDENTITY=STORE.parent/'.camera-access-store.identity'
PRESERVED=STORE.parent/'.camera-access-store-proof-preserved'
MOUNT=r'var-aos-workdirs-sm-runtimes-systemd\x2dslot\x2dcamera\x2daccess.mount'
UNITS=['aos-camera-access-bootstrap.service',MOUNT,'aos-camera-access-store-attach.service',
       'aos-camera-access-store-prepare.service','aos-camera-access-store-layout.service']


def run(args,timeout=40,expected=0):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode!=expected:
        # Retain bounded non-secret owner diagnostics, never arbitrary input.
        (ROOT/'command-failure.json').write_text(json.dumps(dict(command=Path(args[0]).name,
            exit=p.returncode,diagnostic=(p.stdout+p.stderr)[-4000:])))
        raise RuntimeError('STORE_COMMAND_FAILED:'+Path(args[0]).name)
    return p.stdout


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result=dict(scenario='VISION_CAMERA_STORE_TRANSIENT',outcome='NOT_COMPLETE',phases=[],cleanup={},
                nativeCameraActivation='NOT_RUN',aosConsumer='NOT_RUN',vmColdBoot='NOT_RUN')
    start=time.monotonic();kernel=Path('/sys/fs/selinux/policy');stock=None;armed=False;units=[];parked=False
    exec_root=ROOT/'exec';exec_mounted=False;owned_store=False;loop_loaded=False
    audit_file=Path('/var/log/audit/audit.log');audit_start=audit_file.stat().st_size if audit_file.exists() else 0
    def phase(name,action):
        began=time.monotonic();value=action()
        result['phases'].append(dict(name=name,seconds=round(time.monotonic()-began,2),facts=value))
        return value
    def service(action,name):return run(['systemctl',action,name],timeout=45)
    def stop_store():
        for name in UNITS:
            service('stop',name)
        assert not os.path.ismount(STORE)
        assert not list(Path('/sys/block').glob('loop*/loop/backing_file')) or all(
            str(BACKING) not in p.read_text().strip() for p in Path('/sys/block').glob('loop*/loop/backing_file'))
    def clear_failure(name):
        p=subprocess.run(['systemctl','is-failed','--quiet',name],capture_output=True,timeout=8)
        if p.returncode==0:service('reset-failed',name)
        else:assert p.returncode in (1,3,4),'UNIT_FAILURE_STATE_UNOBSERVABLE'
    def start_store():
        # Inactive units can be garbage-collected; reset only an actual failure.
        clear_failure('aos-camera-access-store-prepare.service')
        service('start','aos-camera-access-bootstrap.service')
        assert os.path.ismount(STORE)
        assert 'camera_access_store_t' in run(['stat','-c','%C',str(STORE)])
        return dict(mounted=True,identity=digest(IDENTITY),readonlyRootfs=True)
    def denied_prepare(reason):
        clear_failure('aos-camera-access-store-prepare.service')
        p=subprocess.run(['systemctl','start','aos-camera-access-store-prepare.service'],capture_output=True,text=True,timeout=20)
        assert p.returncode!=0,'UNSAFE_PREPARATION_ACCEPTED'
        logs=run(['journalctl','-b','-u','aos-camera-access-store-prepare.service','-n','8','--no-pager','-o','cat'])
        assert reason in logs,'EXPECTED_PREPARATION_DENIAL_NOT_OBSERVED'
        assert not os.path.ismount(STORE)
        assert not Path('/run/aos-camera-access-store/loop').exists()
    try:
        assert os.getuid()==0 and Path('/sys/fs/selinux/enforce').read_text().strip()=='1'
        assert Path('/var/aos/.provisionstate').exists(),'PROVISIONED_WORKDIRS_REQUIRED'
        assert STORE.is_dir() and not STORE.is_symlink() and not os.path.ismount(STORE)
        assert not BACKING.exists() and not IDENTITY.exists()
        assert not IDENTITY.with_name(IDENTITY.name+'.partial').exists(),'PREEXISTING_PARTIAL_IDENTITY'
        owned_store=True
        assert 'context=system_u:object_r:aos_var_run_t:s0' in next(
            line for line in Path('/proc/mounts').read_text().splitlines() if ' /var/aos/workdirs ' in line)
        if not Path('/sys/module/loop').exists():
            module=ROOT/'kernel/loop.ko';record=json.loads((module.parent/'result.json').read_bytes())
            assert os.uname().release==record['kernelRelease'] and digest(module)==record['sha256']
            run(['chcon','-t','modules_object_t',str(module)])
            run(['insmod',str(module)]);loop_loaded=True
        assert Path('/dev/loop-control').exists(),'LOOP_DEVICE_NOT_CREATED'
        assert not PRESERVED.exists(),'PRESERVED_CAMERA_ROOT_EXISTS_RECONCILE'
        stock=digest(kernel);result['stockPolicySha256']=stock
        # /run is nosuid. A package daemon's SELinux transition cannot be
        # qualified from that filesystem. Use a private executable tmpfs with
        # the package's normal (non-nosuid) execution semantics, not a grant.
        exec_root.mkdir(mode=0o700)
        run(['mount','-t','tmpfs','-o','size=4m,mode=0700,nodev','tmpfs',str(exec_root)])
        exec_mounted=True
        run(['chcon','-t','var_run_t',str(exec_root)])
        options=run(['findmnt','-rn','-M',str(exec_root),'-o','OPTIONS']).strip().split(',')
        assert 'nosuid' not in options and 'noexec' not in options
        files=exec_root/'files';shutil.copytree(ROOT/'files',files)
        tools=exec_root/'tools';shutil.copytree(ROOT/'tools',tools)
        for p in tools.iterdir():
            p.chmod(0o755);run(['chcon','-t','fsadm_exec_t',str(p)])
        saved_policy=ROOT/'stock-policy.bin';saved_policy.write_bytes(kernel.read_bytes());saved_policy.chmod(0o600)
        run(['chcon','--reference=/etc/selinux/aos/policy/policy.33',str(saved_policy)])
        # Both policy root and module store are independent copies. Canonical
        # /etc/selinux and /var/lib/selinux are never an installation target.
        # semodule -p is a filesystem prefix: store-path is appended to it,
        # including when -S is absolute. Keep an actual root-shaped copy.
        for name in ('policy-base','policy-proof'):
            (ROOT/name/'etc').mkdir(parents=True)
            (ROOT/name/'var/lib').mkdir(parents=True)
            shutil.copytree('/etc/selinux',ROOT/name/'etc/selinux',symlinks=True)
            shutil.copytree('/var/lib/selinux',ROOT/name/'var/lib/selinux',symlinks=True)
        semodule=shutil.which('semodule');assert semodule
        loader=files/'vision-policy-load';loader.chmod(0o500)
        run(['chcon','--reference=/usr/sbin/load_policy',str(loader)])
        module=files/'camera_access.pp'
        # semodule enters its real administrative domain. Its input is trusted
        # policy data, not an arbitrary var_run_t file. Use its existing
        # temporary-input type (read/map), without a new domain permission.
        run(['chown','0:0',str(module)])
        run(['chcon','-t','semanage_tmp_t',str(module)])
        restore=[str(loader),'restore']
        rollback=ROOT/'rollback.py'
        rollback.write_text('import pathlib,subprocess\n'
            + 'units='+repr(UNITS)+'\n'
            + "for n in units:subprocess.run(['systemctl','stop',n],capture_output=True,timeout=45)\n"
            + 'root=pathlib.Path('+repr(str(STORE))+');saved=pathlib.Path('+repr(str(PRESERVED))+')\n'
            + "if saved.exists():\n root.rmdir();saved.rename(root)\n"
            + 'subprocess.run('+repr(restore)+',check=True,timeout=40)\n'
            + "subprocess.run(['systemctl','start','aos-sm'],check=True,timeout=40)\n")
        run(['systemd-run','--unit=vision-camera-store-policy-rollback','--on-active=8m','/usr/bin/python3',str(rollback)])
        armed=True
        # Arm rollback before moving any persistent path or changing the kernel.
        # Rename retains the failing subtree; nothing is hidden below a mount.
        run(['systemctl','stop','aos-sm'],timeout=45)
        original_inode=STORE.stat().st_ino
        STORE.rename(PRESERVED);STORE.mkdir(mode=0o755);parked=True
        phase('temporary-policy',lambda:run([semodule,'-p',str(ROOT/'policy-proof'),'-S','/var/lib/selinux','-s','aos','-i',str(module)],timeout=80))
        # Alternate-root semodule intentionally builds without loading into the
        # host kernel. Load that exact compiled policy through the same kernel
        # transaction as load_policy, with a fixed-path diagnostic identity.
        phase('temporary-kernel-policy',lambda:run([str(loader),'load']))
        assert digest(kernel)!=stock,'NEW_POLICY_NOT_LOADED'
        # Place product-equivalent fixed helper/units in /run only. Only the
        # immutable tool/config locations are translated; storage paths are not.
        for name in ('aos-camera-access-store-layout','aos-camera-access-store-prepare','aos-camera-access-store-check'):
            p=files/name;value=p.read_text().replace('/usr/lib/aos-camera-access/store.conf',str(files/'camera-store.conf'))
            p.write_text(value);p.chmod(0o755)
        (files/'aos-camera-access-loop').chmod(0o755)
        run(['chcon','-t','camera_access_store_prepare_exec_t',str(files/'aos-camera-access-store-prepare')])
        run(['chcon','-t','camera_access_store_admin_exec_t',str(files/'aos-camera-access-loop')])
        for original in files.glob('*.service'):
            name=original.name
            if name not in UNITS:continue
            value=original.read_text().replace('/usr/libexec/',str(files)+'/')
            value=value.replace('[Service]\n','[Service]\nEnvironment=PATH='+str(tools)+':/usr/sbin:/usr/bin:/sbin:/bin\n')
            if name=='aos-camera-access-store-attach.service':
                # systemd's normal file-context DB is deliberately unchanged.
                # Assign just the new runtime directory's declared type.
                value=value.replace('ExecStart=',
                    'ExecStartPre=+/usr/bin/chcon -t camera_access_store_runtime_t /run/aos-camera-access-store\nExecStart=')
            dest=Path('/run/systemd/system')/name;assert not dest.exists();dest.write_text(value);units.append(dest)
        dest=Path('/run/systemd/system')/MOUNT;assert not dest.exists()
        dest.write_text((files/'aos-camera-access-store.mount').read_text());units.append(dest)
        run(['systemctl','daemon-reload'])
        audit=Path('/var/log/audit/audit.log');cursor=audit.stat().st_size if audit.exists() else 0
        first=phase('first-create',start_store);identity=IDENTITY.read_bytes()
        (STORE/'proof-retained').write_text('same filesystem after detach/attach\n')
        phase('idempotent-bootstrap',start_store)
        stop_store()
        phase('detach-attach-recovery',start_store)
        assert IDENTITY.read_bytes()==identity and (STORE/'proof-retained').read_text()=='same filesystem after detach/attach\n'
        stop_store()
        original=IDENTITY.read_bytes();IDENTITY.write_bytes(original.replace(b'label=aos-camera-store',b'label=wrong-store'))
        try:phase('wrong-identity-denied',lambda:(denied_prepare('store identity label changed'),dict(denied=True))[1])
        finally:IDENTITY.write_bytes(original)
        values=original.decode().splitlines();uuid=next(v for v in values if v.startswith('uuid='))
        IDENTITY.write_bytes(original.replace(uuid.encode(),b'uuid=not-a-uuid'))
        try:phase('malformed-uuid-denied',lambda:(denied_prepare('store filesystem UUID is not canonical'),dict(denied=True))[1])
        finally:IDENTITY.write_bytes(original)
        BACKING.chmod(0o644)
        try:phase('unsafe-backing-mode-denied',lambda:(denied_prepare('store file mode is not 0600'),dict(denied=True))[1])
        finally:BACKING.chmod(0o600)
        marker=STORE/'must-not-be-hidden';marker.touch()
        try:phase('nonempty-root-denied',lambda:(denied_prepare('unmounted component root is not empty'),dict(denied=True))[1])
        finally:marker.unlink()
        partial=IDENTITY.with_name(IDENTITY.name+'.partial');partial.write_text('uncommitted\n');partial.chmod(0o600)
        try:phase('partial-identity-denied',lambda:(denied_prepare('partial store identity requires manual reconciliation'),dict(denied=True))[1])
        finally:partial.unlink()
        phase('valid-recovery-after-denials',start_store)
        fresh=''
        if audit.exists():
            with audit.open('rb') as f:f.seek(cursor);fresh=f.read(262145).decode(errors='replace')
        assert len(fresh)<=262144,'AUDIT_BOUND_EXCEEDED'
        avcs=[line[:1600] for line in fresh.splitlines() if 'avc:' in line and 'camera_access' in line]
        result['freshScopedAvcs']=avcs;assert not avcs,'CAMERA_STORE_AVC_PRESENT'
        assert Path('/sys/fs/selinux/enforce').read_text().strip()=='1'
        result['outcome']='PASS_TRANSIENT_STORE_ONLY'
    except Exception as error:
        value=str(error);result['code']=value[:150] if isinstance(error,(RuntimeError,AssertionError)) else type(error).__name__
        audit=Path('/var/log/audit/audit.log')
        if audit.exists():
            with audit.open('rb') as f:
                f.seek(max(audit_start,audit.stat().st_size-65536));lines=f.read().decode(errors='replace').splitlines()
            result['failureAvcs']=[line[:1800] for line in lines if 'avc:' in line and any(
                n in line for n in ('semanage_t','semodule','camera_access','store-prepare','chcon'))][-15:]
        try:
            logs=subprocess.run(['journalctl','-b','-u','aos-camera-access-*','-n','45','--no-pager','-o','cat'],capture_output=True,text=True,timeout=8)
            result['unitDiagnostics']=logs.stdout[-10000:]
        except Exception:pass
    finally:
        try:
            if units:stop_store()
            for p in units:p.unlink(missing_ok=True)
            if units:run(['systemctl','daemon-reload'])
            result['cleanup']['unmountedAndDetached']=not os.path.ismount(STORE) and not Path('/run/aos-camera-access-store/loop').exists()
        except Exception:result['cleanup']['unmountedAndDetached']=False
        if parked and result['cleanup'].get('unmountedAndDetached'):
            try:
                STORE.rmdir();PRESERVED.rename(STORE)
                assert STORE.stat().st_ino==original_inode and not PRESERVED.exists()
                result['cleanup']['originalCameraRootRestored']=True
            except Exception:result['cleanup']['originalCameraRootRestored']=False
        elif not parked:result['cleanup']['originalCameraRootRestored']=True
        if armed:
            try:
                if digest(kernel)!=stock:run(restore,timeout=40)
                result['cleanup']['stockPolicyRestored']=digest(kernel)==stock
                if result['cleanup'].get('originalCameraRootRestored'):
                    run(['systemctl','start','aos-sm'],timeout=45)
                    run(['systemctl','stop','vision-camera-store-policy-rollback.timer'])
            except Exception:result['cleanup']['stockPolicyRestored']=False
        if exec_mounted:
            try:
                assert not armed or result['cleanup'].get('stockPolicyRestored') is True
                assert result['cleanup'].get('originalCameraRootRestored') is True
                run(['umount',str(exec_root)])
                result['cleanup']['execMountRemoved']=not os.path.ismount(exec_root)
            except Exception:result['cleanup']['execMountRemoved']=False
        if loop_loaded and result['cleanup'].get('unmountedAndDetached'):
            try:
                run(['rmmod','loop']);result['cleanup']['loopModuleRemoved']=not Path('/sys/module/loop').exists()
            except Exception:result['cleanup']['loopModuleRemoved']=False
        if owned_store and result['cleanup'].get('unmountedAndDetached'):
            # Newly created proof backing only; never the retained Test tree.
            for p in (BACKING,IDENTITY):
                if p.exists() and not p.is_symlink() and p.stat().st_uid==0:p.unlink()
        result['seconds']=round(time.monotonic()-start,2)
        if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['diagnostics']=json.loads((ROOT/'command-failure.json').read_bytes()) if (ROOT/'command-failure.json').exists() else None
        (ROOT/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_TRANSIENT_STORE_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
