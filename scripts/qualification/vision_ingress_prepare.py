#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prepare exact reversible ingress proof inputs on SSD, not a release image."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
GATEWAY=ROOT.parent/'vision-camera-gateway'
PLATFORM=ROOT.parent/'vision-camera-platform'
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')
SDK=Path('/Volumes/SDV-Dev/sdv/inputs/build-inputs/988daa40871bf8e2defc602c750fc2a899251c5a2daa229e3cbe39cdcec43b83/gateway-sdk')
sys.path.insert(0,str(ROOT/'scripts/distribution'))
from build_scratch import directory

OBSERVER='''import errno,json,socket,sys
if sys.argv[1:]==['--ingress']:
 for operation in ('outside-peer','bind'):
  with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
   probe.settimeout(.2)
   try:
    if operation=='outside-peer':probe.connect(('203.0.113.1',6443))
    else:probe.bind(('0.0.0.0',0))
    code=0
   except OSError as error:code=error.errno;timed_out=isinstance(error,TimeoutError)
   else:timed_out=False
   print(json.dumps(dict(networkProof=operation,denied=code in (errno.EPERM,errno.EACCES) or (operation=='outside-peer' and timed_out),errno=code)),flush=True)
 from aos_camera_access import ingress
 original=ingress.forward
 observed=[0]
 def forward(reader,selection,stopped):
  def exchange(request,payload=b''):
   result=ingress.oem(request,payload)
   if request['operation']=='frame' and result.get('state')=='ACCEPTED' and observed[0]<6000:
    info=request['metadata'];observed[0]+=1
    print(json.dumps(dict(ingressFrame=info['frame'],sha256=info['sha256'],sourceEpoch=info['sourceEpoch'],simulationTimeNs=info['simulationTimeNs'])),flush=True)
   return result
  return original(reader,selection,stopped,exchange)
 ingress.forward=forward
 from aos_camera_access.ingress_main import main
else:
 from aos_camera_access.__main__ import main
raise SystemExit(main())
'''


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):return subprocess.run(args,check=True,capture_output=True,timeout=40)


def main():
    p=argparse.ArgumentParser();p.add_argument('--name',required=True)
    p.add_argument('--native-policy',action='store_true')
    p.add_argument('--primitives',type=Path,default=BUILD/'primitives-01');a=p.parse_args()
    assert a.name.startswith('candidate-') and a.name.removeprefix('candidate-').isdecimal()
    output=BUILD/a.name;assert not output.exists(),'CANDIDATE_EXISTS_RECONCILE'
    primitives=json.loads((a.primitives/'result.json').read_bytes())
    assert primitives['outcome']=='PASS_TARGETED_INGRESS_PRIMITIVES'
    policy=PLATFORM/'meta-aos-vehicle-platform/recipes-security/refpolicy/files/camera_ingress.te' if a.native_policy else PLATFORM/'tests/camera_ingress_probe.te'
    assert primitives['inputs'][policy.name]==digest(policy),'POLICY_COMPILE_SOURCE_CHANGED'
    with directory(Path('/Volumes/SDV-Dev/sdv')) as scratch:
        stage=scratch/'candidate';stage.mkdir(mode=0o700)
        native=stage/'native';(native/'lib').mkdir(parents=True)
        shutil.copyfile(BUILD/'gateway-live/carla-ego-runtime',native/'carla-ego-runtime')
        (native/'carla-ego-runtime').chmod(0o555)
        for name in ('libssl.3.dylib','libcrypto.3.dylib'):
            shutil.copyfile(SDK/'openssl/lib'/name,native/'lib'/name)
        binary=native/'carla-ego-runtime';binary.chmod(0o755)
        for path in (binary,native/'lib/libssl.3.dylib',native/'lib/libcrypto.3.dylib'):
            libraries=run(['otool','-L',str(path)]).stdout.decode().splitlines()[1:]
            for index,line in enumerate(libraries):
                old=line.strip().split(' ',1)[0]
                if not old.startswith('/opt/homebrew/'):continue
                name=Path(old).name
                assert name in ('libssl.3.dylib','libcrypto.3.dylib'),'UNEXPECTED_NATIVE_DEPENDENCY'
                replacement='@loader_path/'+('lib/' if path==binary else '')+name
                if path!=binary and index==0:run(['install_name_tool','-id',replacement,str(path)])
                else:run(['install_name_tool','-change',old,replacement,str(path)])
        for path in (native/'lib/libcrypto.3.dylib',native/'lib/libssl.3.dylib',binary):
            # Transient target, explicitly not a release/notarized distribution.
            run(['codesign','--force','--sign','-',str(path)])
            run(['codesign','--verify','--strict',str(path)]);path.chmod(0o555)
        for path in (binary,native/'lib/libssl.3.dylib',native/'lib/libcrypto.3.dylib'):
            assert '/opt/homebrew' not in run(['otool','-L',str(path)]).stdout.decode()
        shutil.copytree(GATEWAY/'tools',stage/'tools',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        source=stage/'source-proof';source.mkdir()
        for name in ('source.py','source_authentication.py','vision_source_guest.py','vm.py','vision_first_enrollment.py'):
            shutil.copyfile(ROOT/'apps/demo-orchestrator/src/aosedge_demo_orchestrator'/name,source/name)
        guest=stage/'guest';guest.mkdir()
        for name in ('aos-camera-ingress-launcher','camera_ingress.pp' if a.native_policy else 'camera_ingress_probe.pp'):
            assert digest(a.primitives/name)==primitives['files'][name]['sha256'],'PRIMITIVE_BINARY_CHANGED'
            shutil.copyfile(a.primitives/name,guest/('camera_ingress_probe.pp' if name=='camera_ingress.pp' else name))
        if a.native_policy:(guest/'policy-profile.json').write_text(json.dumps(dict(profile='native-store'))+'\n')
        shutil.copyfile('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/evidence/camera-store-policy-loader-01/vision-policy-load',guest/'vision-policy-load')
        shutil.copyfile(PLATFORM/'meta-aos-vehicle-platform/recipes-aos/aos-camera-access-platform/files/aos-camera-ingress.service',guest/'aos-camera-ingress.service')
        shutil.copyfile(ROOT/'scripts/qualification/vision_camera_ingress_guest.py',guest/'vision_camera_ingress_guest.py')
        spec=importlib.util.spec_from_file_location('vision_payload',PLATFORM/'tools/build_camera_access_payload.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tarfile.open(fileobj=io.BytesIO(module.payload('0.1.0'))) as archive:
            zipbytes=archive.extractfile('bin/camera-access').read()
        with zipfile.ZipFile(io.BytesIO(zipbytes)) as original:
            entries={n:original.read(n) for n in original.namelist()}
        entries['__main__.py']=OBSERVER.encode()
        data=io.BytesIO();data.write(b'#!/usr/bin/env python3\n')
        with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,raw in sorted(entries.items()):archive.writestr(name,raw)
        (guest/'camera-access').write_bytes(data.getvalue())
        files={str(path.relative_to(stage)):dict(sha256=digest(path),bytes=path.stat().st_size)
            for path in sorted(stage.rglob('*')) if path.is_file()}
        manifest=dict(kind='REVERSIBLE_VISION_INGRESS_PROOF',releaseImage=False,nativePolicy=a.native_policy,files=files,
            source={name:run(['git','-C',str(path),'rev-parse','HEAD']).stdout.decode().strip()
                for name,path in (('integration',ROOT),('gateway',GATEWAY),('platform',PLATFORM))})
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        stage.rename(output)
    print(json.dumps(dict(outcome='PASS_INGRESS_INPUT_PREPARATION',candidate=str(output),files=len(files),releaseImage=False)))


if __name__=='__main__':main()
