#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Temporary read-resource policy, armed rollback, unchanged canonical stores."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('/run/vision-camera-store-proof')
TIMER='vision-camera-resource-policy-rollback'


def run(args,timeout=60):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError('RESOURCE_POLICY_COMMAND_FAILED:'+Path(args[0]).name)
    return p.stdout


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def stop():
    record=json.loads((ROOT/'policy-state.json').read_bytes())
    run(['systemctl','stop','aos-sm'],timeout=45)
    run([str(ROOT/'exec/vision-policy-load'),'restore'])
    assert sha(Path('/sys/fs/selinux/policy'))==record['stockPolicySha256']
    run(['systemctl','stop',TIMER+'.timer'])
    audit=Path('/var/log/audit/audit.log')
    with audit.open('rb') as f:
        f.seek(record['auditCursor']);lines=f.read(1024**2+1).decode(errors='replace').splitlines()
    avc=[v[:1800] for v in lines if 'avc:' in v and ('camera_access' in v or 'vision-camera' in v)]
    run(['umount',str(ROOT/'exec')]);shutil.rmtree(ROOT)
    return dict(stockPolicyRestored=True,canonicalStoresUnchanged=True,temporaryMountRemoved=True,scopedAvcs=avc,
        enforcing=Path('/sys/fs/selinux/enforce').read_text().strip()=='1')


def start():
    assert ROOT.is_dir() and not (ROOT/'policy-state.json').exists()
    assert Path('/sys/fs/selinux/enforce').read_text().strip()=='1'
    stock=Path('/sys/fs/selinux/policy').read_bytes()
    saved=ROOT/'stock-policy.bin';saved.write_bytes(stock);saved.chmod(0o600)
    run(['chcon','--reference=/etc/selinux/aos/policy/policy.33',str(saved)])
    (ROOT/'exec').mkdir(mode=0o700)
    run(['mount','-t','tmpfs','-o','size=4m,mode=0700,nodev','tmpfs',str(ROOT/'exec')])
    loader=ROOT/'exec/vision-policy-load';shutil.copyfile(ROOT/'vision-policy-load',loader);loader.chmod(0o500)
    run(['chcon','--reference=/usr/sbin/load_policy',str(loader)])
    for name in ('policy-base','policy-proof'):
        (ROOT/name/'etc').mkdir(parents=True);(ROOT/name/'var/lib').mkdir(parents=True)
        shutil.copytree('/etc/selinux',ROOT/name/'etc/selinux',symlinks=True)
        shutil.copytree('/var/lib/selinux',ROOT/name/'var/lib/selinux',symlinks=True)
    module=ROOT/'vision_camera_resource_probe.pp';module.chmod(0o600)
    run(['chcon','-t','semanage_tmp_t',str(module)])
    audit=Path('/var/log/audit/audit.log')
    state=dict(stockPolicySha256=hashlib.sha256(stock).hexdigest(),auditCursor=audit.stat().st_size)
    (ROOT/'policy-state.json').write_text(json.dumps(state));(ROOT/'policy-state.json').chmod(0o600)
    rollback=ROOT/'rollback.py'
    rollback.write_text("import subprocess\nsubprocess.run(['systemctl','stop','aos-sm'],timeout=45)\nsubprocess.run("+repr([str(loader),'restore'])+",check=True,timeout=40)\n")
    run(['systemd-run','--unit='+TIMER,'--on-active=10m','/usr/bin/python3',str(rollback)])
    try:
        run(['semodule','-p',str(ROOT/'policy-proof'),'-S','/var/lib/selinux','-s','aos','-i',str(module)],timeout=90)
        run([str(loader),'load'])
        assert sha(Path('/sys/fs/selinux/policy'))!=state['stockPolicySha256']
        state['auditCursor']=audit.stat().st_size
        (ROOT/'policy-state.json').write_text(json.dumps(state))
        run(['systemctl','restart','aos-sm'],timeout=45)
        return dict(temporaryPolicyLoaded=True,rollbackArmed=True,canonicalStoresUnchanged=True,enforcing=True)
    except BaseException:
        stop();raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('start','stop'));a=p.parse_args()
    print(json.dumps(start() if a.action=='start' else stop()))


if __name__=='__main__':main()
