# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Closed, Apple-signed Vision input catalog; existing owners keep lifecycle."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import stat
import subprocess
from types import MappingProxyType

from .images import ImageCatalog, ImageError, ImageRecord

IDENTIFIER = 'org.aosedge.sdvlab.vision.bootstrap'
TEAM = '3NF57VKB3V'
PROFILE = 'vision-bootstrap-v1'
VM_PROFILE = 'aos-vision-main-qemuarm64-v1'
VERSION = '6.1.1-vision-camera.3'
SELECTOR = VERSION+'/main-qemuarm64'
MODEL = {'name': 'aos-vision-vm', 'version': '1.0.0'}
NODE_TYPE = 'aos-vision-vm-main'
COMPONENT = 'aos-vision-vm-1.0.0-main-qemuarm64-camera-access'
SET_TITLE = 'SDV Vision Camera Image Verification'
INSTANCE_NAME = 'SDV-Vision-Camera-Image-Lab-Data'
RETAINED_INSTANCE_NAMES = ('SDV-Lab-Data', 'SDV-Vision-Lab-Data',
                           'SDV-Vision-Native-Lab-Data', 'SDV-Vision-Camera-Lab-Data')
MAX_IMAGE = 16*1024**3
SHA = re.compile('[0-9a-f]{64}')
REV = re.compile('[0-9a-f]{40}')
HOST_PREFIX = 'tooling/vision-host/'
HOST_DESCRIPTOR = HOST_PREFIX+'host-runtime.json'
HOST_RUNTIME = HOST_PREFIX+'native/carla-ego-runtime'
HOST_RUNNER = HOST_PREFIX+'tools/run_m6_interactive.py'


def require(ok, code):
    if not ok:
        raise ImageError('VISION_BOOTSTRAP_'+code)


def canonical(path):
    path = Path(path).absolute()
    require('..' not in path.parts and not any(p.is_symlink() for p in (path,*path.parents)), 'PATH_UNSAFE')
    return path


def stamp(path):
    path = canonical(path)
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid == os.getuid(), 'FILE_UNSAFE')
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid,s.st_nlink)


def resource(root, relative):
    require(isinstance(relative,str) and len(relative)<512 and '\\' not in relative, 'RESOURCE_PATH_INVALID')
    p = PurePosixPath(relative)
    require(relative==p.as_posix() and not p.is_absolute() and '..' not in p.parts
            and all(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*',part) for part in p.parts), 'RESOURCE_PATH_INVALID')
    return canonical(root/relative)


def unique(pairs):
    result={}
    for k,v in pairs:
        require(k not in result,'DUPLICATE_FIELD');result[k]=v
    return result


def _signature(bundle):
    requirement='identifier "'+IDENTIFIER+'" and anchor apple generic and certificate leaf[subject.OU] = "'+TEAM+'"'
    try:
        p=subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R','='+requirement,str(bundle)],capture_output=True,timeout=120)
        require(p.returncode==0,'SIGNATURE_INVALID')
        p=subprocess.run(['/usr/bin/codesign','-dvv',str(bundle)],capture_output=True,text=True,timeout=10)
        lines=(p.stdout+p.stderr).splitlines()
        require(p.returncode==0 and 'Identifier='+IDENTIFIER in lines and 'TeamIdentifier='+TEAM in lines
                and any(s.startswith('Authority=Apple Development: ') for s in lines)
                and 'Signature=adhoc' not in lines,'SIGNATURE_IDENTITY_INVALID')
    except (OSError,subprocess.SubprocessError):
        raise ImageError('VISION_BOOTSTRAP_SIGNATURE_UNAVAILABLE') from None


@dataclass(frozen=True)
class VisionImageRecord(ImageRecord):
    runtime_profile: str = VM_PROFILE


@dataclass(frozen=True)
class VerifiedBootstrap:
    bundle: Path
    resources: Path
    manifest_sha256: str
    source_revision: str
    platform_revision: str
    image: VisionImageRecord
    stamps: object

    def unchanged(self):
        require(all(stamp(path)==before for path,before in self.stamps.items()),'CHANGED_AFTER_VERIFICATION')


def verify(bundle, base_program_manifest_sha256):
    """Verify trust before loading any bundled tooling. No arbitrary image input."""
    bundle=canonical(bundle)
    require(bundle.is_dir() and bundle.suffix=='.bundle','BUNDLE_INVALID')
    root=bundle/'Contents/Resources';path=root/'bootstrap.json'
    before=stamp(path);require(0<before[2]<=2**20,'MANIFEST_LIMIT')
    raw=path.read_bytes();value=json.loads(raw,object_pairs_hook=unique)
    require(set(value)=={'schemaVersion','kind','profile','bundleIdentifier','teamIdentifier','baseProgramManifestSha256',
                         'sources','factory','cameraPayload','files'},'MANIFEST_FIELDS_INVALID')
    require(type(value['schemaVersion']) is int and value['schemaVersion']==1 and value['kind']=='signed-vision-bootstrap'
            and value['profile']==PROFILE and value['bundleIdentifier']==IDENTIFIER and value['teamIdentifier']==TEAM,
            'MANIFEST_IDENTITY_INVALID')
    require(isinstance(base_program_manifest_sha256,str) and SHA.fullmatch(base_program_manifest_sha256)
            and value['baseProgramManifestSha256']==base_program_manifest_sha256,'BASE_PROGRAM_MISMATCH')
    sources=value['sources']
    require(set(sources)=={'integration','platform'} and all(isinstance(v,str) and REV.fullmatch(v) for v in sources.values()),'SOURCE_IDENTITY_INVALID')
    factory=value['factory'];payload=value['cameraPayload']
    require(set(factory)=={'version','architecture','format','path','bytes','sha256','unitModel','nodeType','componentType'}
            and factory['version']==VERSION and factory['architecture']=='main-qemuarm64' and factory['format']=='raw'
            and factory['path']=='images/main-qemuarm64.img' and factory['unitModel']==MODEL
            and factory['nodeType']==NODE_TYPE and factory['componentType']==COMPONENT,'FACTORY_PROFILE_INVALID')
    require(set(payload)=={'version','path','bytes','sha256'} and payload['version']=='0.1.0'
            and payload['path']=='camera-access/payload.tar','CAMERA_PAYLOAD_INVALID')
    stamps={path:before};records={};total=0
    files=value['files'];require(isinstance(files,list) and 4<=len(files)<=4000,'FILE_COUNT_INVALID')
    for row in files:
        require(isinstance(row,dict) and set(row)=={'path','bytes','sha256'},'FILE_RECORD_INVALID')
        name=row['path'];target=resource(root,name)
        require(name not in records and name!='bootstrap.json' and name.startswith(('images/','camera-access/','tooling/')),'FILE_RECORD_INVALID')
        require(type(row['bytes']) is int and 0<=row['bytes']<=MAX_IMAGE and isinstance(row['sha256'],str)
                and SHA.fullmatch(row['sha256']),'FILE_RECORD_INVALID')
        observed=stamp(target);require(observed[2]==row['bytes'] and not observed[5]&0o222,'FILE_MODE_OR_SIZE_INVALID')
        if name!=factory['path']:
            require(row['bytes']<=(32 if name==HOST_RUNTIME else 8)*2**20,'SMALL_FILE_LIMIT')
            require(hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256'],'FILE_DIGEST_CHANGED')
        stamps[target]=observed;records[name]=row;total+=row['bytes']
    require(total<=MAX_IMAGE+64*2**20,'TOTAL_SIZE_LIMIT')
    for item in (factory,payload):
        require(type(item['bytes']) is int and item['bytes']>0 and records.get(item['path'])==
                {k:item[k] for k in ('path','bytes','sha256')},'PAYLOAD_RECORD_MISMATCH')
    actual=set()
    for parent,dirs,names in os.walk(root,followlinks=False):
        require(not any((Path(parent)/name).is_symlink() for name in dirs),'LINKED_DIRECTORY')
        actual.update((Path(parent)/name).relative_to(root).as_posix() for name in names)
    require(actual==set(records)|{'bootstrap.json'},'UNDECLARED_RESOURCE')
    require('tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator/vision_bootstrap.py' in records,
            'TOOLING_MISSING')
    info=bundle/'Contents/Info.plist';stamps[info]=stamp(info)
    plist=plistlib.loads(info.read_bytes())
    require(plist.get('CFBundleIdentifier')==IDENTIFIER and plist.get('CFBundlePackageType')=='BNDL','PLIST_IDENTITY_INVALID')
    _signature(bundle)
    image=VisionImageRecord(SELECTOR,VERSION,'main-qemuarm64',root/factory['path'],factory['bytes'],factory['sha256'],
                            'raw',('signed-vision-bootstrap/bootstrap.json',),())
    result=VerifiedBootstrap(bundle,root,hashlib.sha256(raw).hexdigest(),sources['integration'],sources['platform'],image,MappingProxyType(stamps))
    result.unchanged()
    _host_assets(result)
    return result


def _host_assets(bootstrap):
    """Optional sealed ingress extension; old manufacture provenance is frozen."""
    bootstrap.unchanged()
    meta=bootstrap.resources/HOST_DESCRIPTOR
    runtime=bootstrap.resources/HOST_RUNTIME
    if meta not in bootstrap.stamps:
        require(not any(p.is_relative_to(bootstrap.resources/HOST_PREFIX) for p in bootstrap.stamps),'HOST_DESCRIPTOR_MISSING')
        return {}
    value=json.loads(meta.read_bytes(),object_pairs_hook=unique)
    envelope=json.loads((bootstrap.resources/'bootstrap.json').read_bytes(),object_pairs_hook=unique)
    require(set(value)=={'schemaVersion','kind','profile','baseProgramManifestSha256','rootfsVersion','cameraVersion','sources','assets'}
        and type(value['schemaVersion']) is int and value['schemaVersion']==1
        and value['kind']=='signed-vision-ingress-host' and value['profile']==PROFILE
        and value['baseProgramManifestSha256']==envelope['baseProgramManifestSha256']
        and value['rootfsVersion']=='6.1.1-vision-camera.5' and value['cameraVersion']=='0.1.1'
        and value['assets']==dict(runtime=HOST_RUNTIME,runner=HOST_RUNNER),'HOST_DESCRIPTOR_INVALID')
    sources=value['sources']
    require(set(sources)=={'integration','platform','gateway'}
        and all(isinstance(v,str) and REV.fullmatch(v) for v in sources.values())
        and sources['integration']==bootstrap.source_revision,'HOST_SOURCE_BINDING_INVALID')
    for name in (HOST_RUNTIME,HOST_RUNNER,HOST_PREFIX+'tools/run_m5.py',HOST_PREFIX+'tools/behavior_agent_controller.py',
                 HOST_PREFIX+'native/lib/libssl.3.dylib',HOST_PREFIX+'native/lib/libcrypto.3.dylib'):
        require(bootstrap.resources/name in bootstrap.stamps,'HOST_RESOURCE_MISSING')
    require(runtime.stat().st_mode&0o111,'HOST_RUNTIME_NOT_EXECUTABLE')
    return dict(runtime=runtime,runner=bootstrap.resources/HOST_RUNNER)


class SignedVisionCatalog(ImageCatalog):
    """One authenticated input; QEMU/SDK inputs remain the normal base selection."""
    required_vm_profile=VM_PROFILE
    cloud_setup_profile=PROFILE

    def __init__(self, bootstrap, base_catalog=None):
        require(isinstance(bootstrap,VerifiedBootstrap),'VERIFIED_SELECTION_REQUIRED')
        bootstrap.unchanged();self.bootstrap=bootstrap
        base=base_catalog or ImageCatalog()
        for name in ('root','workspace','project','input_root','input_project'):
            setattr(self,name,getattr(base,name))

    def resolve(self, selector=None, image_path=None):
        require(image_path is None and selector==SELECTOR,'EXACT_VISION_SELECTOR_REQUIRED')
        self.bootstrap.unchanged()
        return self.bootstrap.image

    def records(self):
        self.bootstrap.unchanged()
        return [self.bootstrap.image],[]

    def list(self):
        self.bootstrap.unchanged()
        return dict(images=[dict(selector=SELECTOR,version=VERSION,architecture='main-qemuarm64',
                                state='SIGNED_ENGINEERING_INPUT',qualified=False)],issues=[])

    @property
    def unit_configuration(self):
        return dict(nodes=[dict(nodeType=NODE_TYPE,labels=['main'],priority=100)])

    def component_support(self,*args,**kwargs):
        raise ImageError('VISION_BOOTSTRAP_NOT_A_VDP_FACTORY')

    def source_assets(self):
        return _host_assets(self.bootstrap)
