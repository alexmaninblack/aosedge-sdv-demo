#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded, read-only diagnostics of the fixed native Vision guest."""
import argparse
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration

PROBE=r'''import json,pathlib,subprocess
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=8);return p.stdout[-16000:]
r={name:run(['systemctl','show',name,'-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID','-p','ExecMainStatus']) for name in ('aos-sm','aos-camera-access','aos-camera-access-selftest@a','aos-camera-access-selftest@b')}
r['selftestLog']=run(['journalctl','-b','-u','aos-camera-access-selftest@a','-u','aos-camera-access-selftest@b','-n','35','--no-pager','-o','cat'])
p=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
r['tree']=run(['find',str(p),'-maxdepth','4','-printf','%M %u %g %p\n'])
r['labels']=run(['ls','-Zd',str(p),str(p/'slots'),str(p/'slots/a'),str(p/'slots/a/bin'),str(p/'slots/a/bin/camera-access')])
r['expectedLabels']=run(['matchpathcon',str(p),str(p/'slots/a/bin/camera-access'),'/usr/libexec/aos-camera-access-launcher'])
r['launcherLabel']=run(['ls','-Z','/usr/libexec/aos-camera-access-launcher'])
r['workdirsMount']=[line for line in pathlib.Path('/proc/mounts').read_text().splitlines() if ' /var/aos/workdirs ' in line]
r['systemdFeatures']=run(['systemd','--version'])
r['storeProof']=run(['journalctl','-b','-u','vision-camera-store-proof','-n','15','--no-pager','-o','cat'])
audit=pathlib.Path('/var/log/audit/audit.log')
if audit.is_file():
 with audit.open('rb') as f:
  f.seek(max(0,audit.stat().st_size-131072));raw=f.read().decode(errors='replace')
 r['auditAvc']=[line[:1800] for line in raw.splitlines() if 'avc:' in line and ('camera' in line or 'aos_var_run_t' in line)][-15:]
kernel=run(['journalctl','-k','-b','-n','400','--no-pager','-o','cat'])
r['avc']=[line[:1500] for line in kernel.splitlines() if 'avc:' in line][-15:]
r['cameraLog']=run(['journalctl','-b','-u','aos-camera-access','-n','20','--no-pager','-o','cat'])
print(json.dumps(r))
'''


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
 c=configuration(a.config);base=c['main']['packageRoot'];q=shlex.quote
 script="python3 - <<'READ_VISION'\n"+PROBE+"\nREAD_VISION\n"
 code="""import pathlib,sys,subprocess,json
sys.path.insert(0,BASE+'/aosedge-sdv-demo/apps/demo-orchestrator/src')
from aosedge_demo_orchestrator.guest_access import ssh_command
from aosedge_demo_orchestrator.vm import access_path
p=pathlib.Path.home()/'SDV-Vision-Native-Lab-Data'
s=json.loads((p/'.run/demo-current/journal.json').read_bytes());v=s['vehicles']['test']
assert v['cloud']['identity']['model']=='aos-vision-vm'
r=subprocess.run(ssh_command(access_path(p,'test'),v['sshPort'],5),input=SCRIPT,text=True,capture_output=True,timeout=40)
assert r.returncode==0
print(r.stdout)
""".replace('BASE',repr(base)).replace('SCRIPT',repr(script))
 print(h.remote(c['transport'],q(base+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12')+' -I -B -c '+q(code),timeout=45))


if __name__=='__main__':main()
