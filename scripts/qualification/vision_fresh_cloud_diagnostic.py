#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read native service exit facts from Cloud without booting a guest."""
import argparse
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--attempt',choices=('07','08'),default='07');a=p.parse_args();c=configuration(a.config)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    code=r'''import pathlib,sys,subprocess,json
main=MAIN;bundle=pathlib.Path(BUNDLE)
subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True,capture_output=True)
sys.path.insert(0,main['packageRoot']+'/aosedge-sdv-demo/apps/demo-orchestrator/src')
import aosedge_demo_orchestrator
from aosedge_demo_orchestrator import runtime_paths
aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
from aosedge_demo_orchestrator import vision_bootstrap as v
from aosedge_demo_orchestrator.environment import EnvironmentService
from aosedge_demo_orchestrator.vm import VMService
from aosedge_demo_orchestrator.units import UnitService
verified=v.verify(bundle,main['manifestSha256']);native=pathlib.Path.home()/v.INSTANCE_NAME
with runtime_paths.installed_session(native):
 env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE)
 value=UnitService(VMService(env)).observe('cloud-status','test')
 print(json.dumps(dict(services=value.get('services'),unit=value.get('unit'),problems=value.get('problems'))))
'''.replace('MAIN',repr(c['main'])).replace('BUNDLE',repr(str(Path(c['remoteRoot'])/'vision-fresh-accept-07/AosEdge Vision Bootstrap 0.5.0.bundle')))
    value=json.loads(h.remote(c['transport'],shlex.quote(python)+' -I -B -c '+shlex.quote(code),timeout=90))
    path=Path(c['records'])/('vision-fresh-accept-'+a.attempt)/'cloud-reader-diagnostic.json';h.require(not path.exists(),'CLOUD_DIAGNOSTIC_EXISTS')
    h.atomic(path,value);print(json.dumps(value,indent=2))


if __name__=='__main__':main()
