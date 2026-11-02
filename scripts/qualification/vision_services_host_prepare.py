#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Sealed host inputs for transient native proof, not a qualified image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-services')
GATEWAY=ROOT.parent/'vision-camera-gateway'
PLATFORM=ROOT.parent/'vision-camera-platform'
SERVICES=ROOT.parent/'vision-pilot-services'
sys.path.insert(0,str(ROOT/'scripts/distribution'))
from build_scratch import directory


def require(ok,code):
    if not ok:raise ValueError(code)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args,**kwargs):return subprocess.run(args,check=True,capture_output=True,timeout=60,**kwargs)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--name',choices=('host-candidate-01','host-candidate-02','host-candidate-03','host-candidate-04','host-candidate-05'),default='host-candidate-01');a=p.parse_args()
    from vision_vm_campaign import configuration
    c=configuration(a.config);records=Path(c['records']);output=BUILD/a.name
    require(not output.exists(),'VISION_HOST_INPUT_EXISTS_RECONCILE')
    cpu=json.loads((records/'vision-services-cpu-04/result.json').read_bytes())
    require(cpu['outcome']=='PASS_NATIVE_QUOTA_MAPPING_AND_STOCK_RESTORATION' and all(cpu['cleanup'].values()),'VISION_HOST_CPU_PROOF_REQUIRED')
    successor=a.name in ('host-candidate-04','host-candidate-05')
    packages=json.loads((BUILD/('signed-04' if successor else 'signed-03')/'result.json').read_bytes())
    require(packages['outcome']==('PASS_TWO_INDEPENDENT_OFFICIAL_VISION_SUCCESSOR_SIGNATURES' if successor else 'PASS_TWO_INDEPENDENT_OFFICIAL_VISION_SIGNATURES')
        and packages['scratchRemoved'],'VISION_HOST_SIGNED_SERVICE_INPUT_REQUIRED')
    sources={}
    for name,path in (('services',SERVICES),('platform',PLATFORM),('gateway',GATEWAY),('integration',ROOT)):
        require(not run(['git','-C',str(path),'diff','HEAD','--name-only']).stdout,'VISION_HOST_COMMITTED_SOURCES_REQUIRED')
        sources[name]=run(['git','-C',str(path),'rev-parse','HEAD']).stdout.decode().strip()
    with directory(ROOT,root=Path('/Volumes/SDV-Dev/.s501/.tmp')) as scratch:
        junit=scratch/'gateway-unit.xml'
        names={'runtime_options','vision_calibration','vision_exchange','vision_camera','viss_network'}
        if a.name!='host-candidate-01':names.add('viss_assignment_control')
        run(['ctest','--test-dir',str(BUILD/'gateway-unit'),'-R','^('+'|'.join(sorted(names))+')$','--output-on-failure','--output-junit',str(junit)],env=dict(os.environ,TMPDIR=str(scratch)))
        require(junit.is_file() and junit.stat().st_size<1024**2,'VISION_HOST_GATEWAY_REPORT_MISSING')
        cases=ET.parse(junit).getroot().findall('testcase')
        require(len(cases)==len(names) and {row.attrib.get('name') for row in cases}==names
            and all(row.find('failure') is None and row.find('skipped') is None and row.find('error') is None for row in cases),'VISION_HOST_GATEWAY_TESTS_FAILED')
    with directory(BUILD) as scratch:
        stage=scratch/'candidate';native=stage/'native';(native/'lib').mkdir(parents=True)
        binary=native/'carla-ego-runtime';shutil.copyfile(BUILD/'gateway-live/carla-ego-runtime',binary);binary.chmod(0o755)
        for name in ('libssl.3.dylib','libcrypto.3.dylib'):
            shutil.copyfile(Path('/opt/homebrew/opt/openssl@3/lib')/name,native/'lib'/name)
        for path in (binary,native/'lib/libssl.3.dylib',native/'lib/libcrypto.3.dylib'):
            for index,line in enumerate(run(['/usr/bin/otool','-L',str(path)]).stdout.decode().splitlines()[1:]):
                old=line.strip().split(' ',1)[0]
                if not old.startswith('/opt/homebrew/'):continue
                name=Path(old).name;require(name in ('libssl.3.dylib','libcrypto.3.dylib'),'VISION_HOST_UNKNOWN_DEPENDENCY')
                replacement='@loader_path/'+('lib/' if path==binary else '')+name
                args=['/usr/bin/install_name_tool','-id',replacement,str(path)] if path!=binary and index==0 else ['/usr/bin/install_name_tool','-change',old,replacement,str(path)]
                run(args)
            require(b'/opt/homebrew/' not in run(['/usr/bin/otool','-L',str(path)]).stdout,'VISION_HOST_NOT_PORTABLE')
        # This candidate is not executable proof or a signed delivery. The
        # assembler applies the authorized Apple identity to all native assets.
        for name in run(['git','-C',str(GATEWAY),'ls-files','tools']).stdout.decode().splitlines():
            path=GATEWAY/name;require(path.is_file() and not path.is_symlink(),'VISION_HOST_TOOL_NOT_REGULAR')
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        files={path.relative_to(stage).as_posix():dict(sha256=digest(path),bytes=path.stat().st_size) for path in sorted(stage.rglob('*')) if path.is_file()}
        manifest=dict(kind='VISION_SERVICES_HOST_ENGINEERING_INPUT',releaseImage=False,nativeQualified=False,source=sources,files=files,
            contractSha256=digest(ROOT/'contracts/vision-vm/services.v1.json'),allocationSha256=digest(ROOT/'contracts/vision-vm/services-allocation.v1.json'))
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (stage/'context.json').write_text(json.dumps(dict(candidateManifestSha256=digest(stage/'manifest.json')),indent=2)+'\n')
        result=dict(outcome='PASS_VISION_SERVICES_HOST_SOURCE_PREREQUISITES',gatewayUnitTestsPassed=len(names),cpuProofRestored=True,
            nativeExchange='NOT_RUN',imageBuild='NOT_RUN',sources=sources)
        (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n');stage.rename(output)
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
