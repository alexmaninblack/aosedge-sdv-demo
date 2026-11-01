#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prepare measured Vision-only package inputs on SSD, never sign or publish."""
import argparse
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[2]
SERVICES=ROOT.parent/'vision-pilot-services'
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-services')
sys.path.insert(0,str(ROOT/'scripts/distribution'))
from build_scratch import directory


def require(ok,code):
    if not ok:raise ValueError(code)


def freeze(allocation,cpu,observed,measured,closures):
    require(cpu['outcome']=='PASS_NATIVE_QUOTA_MAPPING_AND_STOCK_RESTORATION' and all(cpu['cleanup'].values()),'VISION_QUOTA_PROOF_REQUIRED')
    require(observed['outcome']=='PASS_TRANSIENT_FOUR_CPU_NATIVE_QUOTA_MAPPING'
        and observed['actualProfileWriterInNativeIAM'] is True and observed['ownersRestartCountZero'] is True
        and observed['topology']==dict(packages=1,cores=4,threads=4,online=[0,1,2,3])
        and observed['projectedNativeQuota']==[40000,100000] and observed['restoredNativeQuota']==[10000,100000]
        and all(observed['cleanup'].values()),'VISION_QUOTA_NATIVE_MAPPING_CHANGED')
    require(measured['outcome']=='PASS_SAME_VM_ISOLATED_CLOSURE_MEASUREMENTS' and all(measured['cleanup'].values()),'VISION_CLOSURE_MEASUREMENT_REQUIRED')
    require(allocation['node']==dict(vcpus=4,memoryMiB=4096,maxDmips=10000,quotaPeriodMicroseconds=100000),'VISION_NODE_ALLOCATION_CHANGED')
    require(sum(allocation[role]['cpuLimit'] for role in ('perception','assessment'))+allocation['retainedDiagnosticDmips']+allocation['remainingDmips']==10000,'VISION_DMIPS_OVERCOMMIT')
    for role in ('perception','assessment'):
        quota=allocation[role]['cpuLimit']*100000*4//10000
        require(allocation['expectedCpuMax'][role]==[quota,100000],'VISION_NATIVE_CPU_FORMULA_CHANGED')
        require(closures[role]['licenseNoticesIncluded'] is True
            and closures[role]['status']=='MEASURED_CLOSURE_NOT_SIGNABLE_WITHOUT_NATIVE_MEASUREMENTS_AND_DELIVERY_GATES','VISION_CLOSURE_NOT_READY')
    return {role:allocation[role] for role in ('perception','assessment')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    from vision_vm_campaign import configuration
    c=configuration(args.config);records=Path(c['records']);target=BUILD/'packages-01'
    require(not target.exists() and target.parent.stat().st_dev==ROOT.stat().st_dev,'VISION_PACKAGE_OUTPUT_EXISTS_OR_WRONG_DISK')
    allocation=json.loads((ROOT/'contracts/vision-vm/services-allocation.v1.json').read_bytes())
    closure=BUILD/'closure-08';closures={role:json.loads((closure/role/'closure.json').read_bytes()) for role in ('perception','assessment')}
    quotas=freeze(allocation,json.loads((records/'vision-services-cpu-04/result.json').read_bytes()),
        json.loads((records/'vision-services-cpu-04/cpu-topology-observed.json').read_bytes()),
        json.loads((records/'vision-services-closure-06/result.json').read_bytes()),closures)
    campaign=json.loads((closure/'campaign.json').read_bytes())
    require(campaign['verifiedDeliveryComplete'] is True and campaign['builderStopped'] is True,'VISION_CLOSURE_TRANSFER_UNVERIFIED')
    package=runpy.run_path(str(SERVICES/'tools/aos_package.py'));result={}
    with directory(BUILD) as scratch:
        staged=scratch/'packages';staged.mkdir(mode=0o700)
        for role in ('perception','assessment'):
            artifact=campaign['closure']['artifacts'][role];source=closure/(role+'-rootfs.tar.gz')
            result[role]=package['prepare'](source,closures[role],role,quotas[role],staged/role,artifact['sha256'])
        receipt=dict(outcome='PASS_MEASURED_VISION_PACKAGE_PREPARATION',allocation=allocation,
            rootfs={role:dict(bytes=campaign['closure']['artifacts'][role]['bytes'],sha256=result[role]['rootfsSha256'],sourceRevision=result[role]['sourceRevision']) for role in result},
            signing='NOT_RUN',publication='NOT_RUN',nativeExecution='NOT_RUN')
        (staged/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');staged.rename(target)
    print(json.dumps(receipt));return 0


if __name__=='__main__':raise SystemExit(main())
