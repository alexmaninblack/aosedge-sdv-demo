#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reversible ingress proof: alternative policy, namespace-only payload, rollback.

Inputs are exact non-secret compiled artifacts staged by the named campaign.
No rootfs, OEM slot, credentials or canonical policy store is rewritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('/run/vision-camera-store-proof') # fixed path of the retained loader
TIMER='vision-camera-ingress-rollback'
UNIT=Path('/run/systemd/system/aos-camera-ingress.service')
DROPIN=Path('/run/systemd/system/aos-camera-ingress.service.d/85-democtl-camera-mtls.conf')
SELECTION=Path('/run/democtl-source/camera-selection.json')


def run(args,timeout=45):
    done=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if done.returncode:raise RuntimeError('INGRESS_PROOF_'+Path(args[0]).name.upper().replace('-','_')+'_FAILED')
    return done.stdout


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def stores():
    result={}
    for root in (Path('/etc/selinux'),Path('/var/lib/selinux')):
        for path in sorted(root.rglob('*')):
            if path.is_symlink():result[str(path)]=dict(link=str(path.readlink()))
            elif path.is_file():result[str(path)]=dict(sha256=digest(path),mode=path.stat().st_mode&0o777)
    return result


def stop():
    record=json.loads((ROOT/'policy-state.json').read_bytes())
    run(['systemctl','stop','aos-camera-ingress.service'])
    pid=run(['systemctl','show','aos-camera-ingress.service','--value','-p','MainPID']).strip()
    assert pid=='0','INGRESS_PROCESS_REMAINS'
    assert digest(Path(record['originalTarget']))==record['originalPayloadSha256'],'INGRESS_NATIVE_PAYLOAD_CHANGED'
    # Remove the credential projection only after the process/mount are gone.
    for path in (DROPIN,SELECTION):path.unlink(missing_ok=True)
    UNIT.unlink(missing_ok=True);run(['systemctl','daemon-reload'])
    run([str(ROOT/'exec/vision-policy-load'),'restore'])
    assert digest(Path('/sys/fs/selinux/policy'))==record['stockPolicySha256'],'INGRESS_STOCK_POLICY_CHANGED'
    assert stores()==record['canonicalStores'],'INGRESS_CANONICAL_STORES_CHANGED'
    run(['systemctl','stop',TIMER+'.timer'])
    audit=Path('/var/log/audit/audit.log')
    with audit.open('rb') as stream:
        stream.seek(record['auditCursor']);raw=stream.read(1024**2+1)
    assert len(raw)<=1024**2,'INGRESS_AUDIT_LIMIT'
    avc=[v[:1800] for v in raw.decode(errors='replace').splitlines() if 'avc:' in v and 'camera_ingress' in v]
    run(['umount',str(ROOT/'exec')]);shutil.rmtree(ROOT)
    return dict(stockPolicyRestored=True,canonicalStoresUnchanged=True,transientUnitRemoved=True,
        transientMountRemoved=True,ingressStopped=True,enforcing=Path('/sys/fs/selinux/enforce').read_text().strip()=='1',scopedAvcs=avc)


def start():
    assert ROOT.is_dir() and not (ROOT/'policy-state.json').exists() and not UNIT.exists() and not DROPIN.exists()
    assert not SELECTION.exists() and Path('/sys/fs/selinux/enforce').read_text().strip()=='1'
    native=Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
    active=(native/'active').readlink();assert str(active) in ('slots/a','slots/b')
    target=native/active/'bin/camera-access';assert target.is_file() and target.stat().st_uid==0
    stock=ROOT/'stock-policy.bin';stock.write_bytes(Path('/sys/fs/selinux/policy').read_bytes());stock.chmod(0o600)
    run(['chcon','--reference=/etc/selinux/aos/policy/policy.33',str(stock)])
    (ROOT/'exec').mkdir(mode=0o755)
    run(['mount','-t','tmpfs','-o','size=4m,mode=0755,nodev','tmpfs',str(ROOT/'exec')])
    for name in ('vision-policy-load','aos-camera-ingress-launcher','camera-access'):
        path=ROOT/'exec'/name;shutil.copyfile(ROOT/name,path);path.chmod(0o555)
    run(['chcon','--reference=/usr/sbin/load_policy',str(ROOT/'exec/vision-policy-load')])
    for name in ('policy-base','policy-proof'):
        (ROOT/name/'etc').mkdir(parents=True);(ROOT/name/'var/lib').mkdir(parents=True)
        shutil.copytree('/etc/selinux',ROOT/name/'etc/selinux',symlinks=True)
        shutil.copytree('/var/lib/selinux',ROOT/name/'var/lib/selinux',symlinks=True)
    module=ROOT/'camera_ingress_probe.pp';module.chmod(0o600);run(['chcon','-t','semanage_tmp_t',str(module)])
    record=dict(stockPolicySha256=digest(stock),canonicalStores=stores(),
        auditCursor=Path('/var/log/audit/audit.log').stat().st_size,originalPayloadSha256=digest(target),originalTarget=str(target))
    (ROOT/'policy-state.json').write_text(json.dumps(record));(ROOT/'policy-state.json').chmod(0o600)
    rollback=ROOT/'rollback.py'
    rollback.write_text("import subprocess\nsubprocess.run(['systemctl','stop','aos-camera-ingress.service'],timeout=10)\nsubprocess.run("+
        repr([str(ROOT/'exec/vision-policy-load'),'restore'])+",check=True,timeout=40)\n")
    run(['systemd-run','--unit='+TIMER,'--on-active=10m','/usr/bin/python3',str(rollback)])
    try:
        run(['semodule','-p',str(ROOT/'policy-proof'),'-S','/var/lib/selinux','-s','aos','-i',str(module)],timeout=100)
        run([str(ROOT/'exec/vision-policy-load'),'load'])
        profile=ROOT/'policy-profile.json';code_label='camera_ingress_code_t'
        if profile.exists():
            assert json.loads(profile.read_bytes())==dict(profile='native-store'),'INGRESS_POLICY_PROFILE_INVALID'
            code_label='camera_access_store_t'
        for name,label in (('aos-camera-ingress-launcher','camera_ingress_exec_t'),('camera-access',code_label)):
            run(['chcon','-t',label,str(ROOT/'exec'/name)])
        ROOT.chmod(0o755)
        # Only this service's read-only namespace sees the candidate zip.
        text=(ROOT/'aos-camera-ingress.service').read_text()
        assert 'ExecStart=/usr/libexec/aos-camera-ingress-launcher\n' in text
        text=text.replace('ExecStart=/usr/libexec/aos-camera-ingress-launcher\n',
            'ExecStart=/run/vision-camera-store-proof/exec/aos-camera-ingress-launcher\n'+
            'BindReadOnlyPaths=/run/vision-camera-store-proof/exec/camera-access:'+str(target)+'\n')
        UNIT.write_text(text);UNIT.chmod(0o644)
        run(['chcon','--reference=/usr/lib/systemd/system/aos-camera-access.service',str(UNIT)])
        run(['systemctl','daemon-reload'])
        return dict(prepared=True,rollbackArmed=True,rootfsUnchanged=True,policyEnforcing=True,
            originalPayloadSha256=record['originalPayloadSha256'])
    except BaseException:
        stop();raise


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('start','stop'));a=p.parse_args()
    print(json.dumps(start() if a.action=='start' else stop()))


if __name__=='__main__':main()
