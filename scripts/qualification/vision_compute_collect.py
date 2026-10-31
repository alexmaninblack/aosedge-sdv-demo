#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reconcile completed costs after the known observer-close reporting fault.

Never edits an old result or reruns a model. Only an exactly attributed orphaned
caffeinate may be normally terminated; all persistent state is read-only.
"""
import argparse
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration


REMOTE=r'''
import json,os,pathlib,signal,socket,subprocess,time
r=pathlib.Path(ROOT);raw=json.loads((r/'result.json').read_bytes())
assert raw['outcome']=='NOT_COMPLETE' and raw['code']=='AttributeError'
assert all(raw['cleanup'].values()) and raw['modelResult']['outcome']=='PASS_TENSOR_EXECUTION_ONLY'
assert raw['modelResult']['steady']['samples']==300 and raw['modelResult']['steady']['seconds']>=60
worker=(r/'vision_compute_worker.py').read_text()
assert 'class LoadObserver:' in worker and 'def close(' not in worker
phases=[json.loads((r/'camera'/f'{name}.json').read_bytes()) for name in (
 'replay-capture-baseline','models-with-live-camera','camera-removed-recovery')]
assert all(p['settingsUnchanged'] and p['controllerStaleSamples']==0 for p in phases)
assert not (r/'camera/camera-report.json').exists()
# Cross-check the immutable recorded input against its original acquisition.
original=json.loads((r.parent/'compute-continuation/sequence/sequence.json').read_bytes())
replay=json.loads((r/'sequence/sequence.json').read_bytes())
assert original==replay
assert all(b['frame']>a['frame'] and b['simulationTime']>a['simulationTime'] for a,b in zip(original['frames'],original['frames'][1:]))
def processes():
 text=subprocess.check_output(['/bin/ps','-axo','pid=,uid=,ppid=,lstart=,args='],text=True)
 return [v.split(None,8) for v in text.splitlines()]
helpers=[]
for row in processes():
 if len(row)!=9 or row[8]!='/usr/bin/caffeinate -d -i -u -t 900':continue
 epoch=time.mktime(time.strptime(' '.join(row[3:8]),'%a %b %d %H:%M:%S %Y'))
 start=(r/'camera/replay-capture-baseline.json').stat().st_mtime-12
 if abs(epoch-start)>5:continue
 assert int(row[1])==os.getuid() and row[2]=='1'
 helpers.append(int(row[0]))
assert len(helpers)<=1
for pid in helpers:
 # Re-read exact process identity immediately before normal termination.
 row=next(p for p in processes() if p[0]==str(pid))
 assert int(row[1])==os.getuid() and row[2]=='1' and row[8]=='/usr/bin/caffeinate -d -i -u -t 900'
 os.kill(pid,signal.SIGTERM)
 end=time.monotonic()+5
 while any(p[0]==str(pid) for p in processes()) and time.monotonic()<end:time.sleep(.05)
 assert not any(p[0]==str(pid) for p in processes())
assert not any(len(p)==9 and VISION in p[8] and 'qemu-system' in p[8] for p in processes())
for port in (12022,2000,16443,18053):
 with socket.socket() as s:
  s.settimeout(.2);assert s.connect_ex(('127.0.0.1',port))!=0
print(json.dumps(dict(outcome='PASS_COST_CHARACTERIZATION_RECONCILED',originalScenarioOutcome=raw['outcome'],
 originalReportFault='Missing LoadObserver.close; source fix unit-tested, original evidence preserved',
 modelResult=raw['modelResult'],cameraPhases=[{k:p[k] for k in ('phase','measurementSeconds','worldFps','cameraFps','controllerStaleSamples')} for p in phases],
 modelContinuousSeconds=raw['modelResult']['steady']['seconds'],cameraLoadPhaseSeconds=phases[1]['measurementSeconds'],
 exactActiveSubwindowMetrics='NOT_RECONSTRUCTED; no timing evidence invented',
 replaySource=original['source'],retainedFrameCount=len(original['frames']),
 cleanup=dict(raw['cleanup'],orphanedAwakeHelperClosed=True),closedHelperCount=len(helpers),
 calibration='NOT_VALIDATED',accuracy='NOT_QUALIFIED',assessment='NOT_RUN',nativeAosDeployment='NOT_RUN',fullE2E='NOT_RUN')))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();c=configuration(a.config)
    local=Path(c['records'])/'model-compute/compute-steady'
    output=local/'reconciled-cost-result.json'
    h.require(not output.exists(),'RECONCILIATION_EXISTS')
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    script='ROOT='+repr(c['remoteRoot']+'/model-compute/compute-steady')+'\nVISION='+repr(c['visionRoot'])+'\n'+REMOTE
    text=h.remote(c['transport'],shlex.quote(python)+" -I -B - <<'RECONCILE_COST'\n"+script+'\nRECONCILE_COST\n',timeout=20)
    value=json.loads(text);h.atomic(output,value)
    print(json.dumps(dict(outcome=value['outcome'],steady=value['modelResult']['steady'],cleanup=value['cleanup'])))


if __name__=='__main__':main()
