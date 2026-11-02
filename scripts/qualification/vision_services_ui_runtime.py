#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Deliver an isolated headed-browser test runtime; never run a browser on Dev."""
import argparse
import json
from pathlib import Path,PurePosixPath
import posixpath
import shlex
import subprocess
import tarfile
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--signed-browser',action='store_true');parser.add_argument('--finish-signed-browser',action='store_true');args=parser.parse_args();c=configuration(args.config)
    build=Path('/Volumes/SDV-Dev/sdv/build/vision-services/ui-runtime-01');archive=build/'headed-runtime.tar'
    node=Path('/Users/alexagizim/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    module=build/'node_modules/playwright-core';browser=build/'browsers/chromium-1234/chrome-mac-arm64'
    h.require(json.loads((module/'package.json').read_bytes())['version']=='1.62.1','UI_RUNTIME_VERSION_CHANGED')
    if args.finish_signed_browser:return finish_signed_browser(c,build,node)
    if args.signed_browser:return signed_browser(c,build,node)
    h.require(not archive.exists(),'UI_RUNTIME_ARCHIVE_EXISTS_RECONCILE')
    with tarfile.open(archive,'w') as output:
        output.add(node,arcname='node',recursive=False)
        output.add(module,arcname='playwright-core');output.add(browser,arcname='chromium')
    pin=h.digest(archive);remote=Path(c['remoteRoot'])/'vision-services-ui-runtime-01'
    h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(archive),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=180)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    code='''import pathlib,hashlib,tarfile,subprocess,json,posixpath,shutil
p=pathlib.Path(REMOTE);f=p/'headed-runtime.tar';assert not p.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==PIN
assert shutil.disk_usage(p).free>f.stat().st_size*2+1024**3
with tarfile.open(f) as archive:
 seen=set()
 for row in archive:
  name=pathlib.PurePosixPath(row.name)
  assert not name.is_absolute() and '..' not in name.parts and row.name not in seen and name.parts[0] in ('node','playwright-core','chromium')
  assert row.isfile() or row.isdir() or row.issym();seen.add(row.name)
  if row.issym():
   target=posixpath.normpath(posixpath.join(str(name.parent),row.linkname));assert not row.linkname.startswith('/') and target.split('/')[0]==name.parts[0]
 archive.extractall(p,filter='fully_trusted')
browser=p/'chromium/Google Chrome for Testing.app'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(browser)],check=True,capture_output=True,timeout=120)
node=subprocess.check_output([str(p/'node'),'--version'],text=True).strip()
print(json.dumps(dict(outcome='PASS_ISOLATED_HEADED_UI_RUNTIME_DELIVERY',path=str(p),archiveSha256=PIN,browserSignatureVerified=True,nodeVersion=node,browserStarted=False,systemToolsChanged=False)))
'''.replace('REMOTE',repr(str(remote))).replace('PIN',repr(pin))
    value=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=180))
    h.atomic(build/'delivery.json',value);print(json.dumps(value));return 0


def signed_browser(c,build,node):
    """Use the ordinary signed Chrome distribution; keep the failed test build."""
    dmg=build/'googlechrome.dmg';h.require(dmg.is_file() and 1024**2<dmg.stat().st_size<800*1024**2,'SIGNED_BROWSER_MEDIA_REQUIRED')
    remote=Path(c['remoteRoot'])/'vision-services-ui-runtime-01'
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(dmg),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/official-chrome.dmg'],timeout=180)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    code='''import pathlib,hashlib,subprocess,json,plistlib,os
p=pathlib.Path(REMOTE);dmg=p/'official-chrome.dmg';mount=p/'chrome-mount';target=p/'Google Chrome.app'
assert not target.exists() and not mount.exists() and hashlib.sha256(dmg.read_bytes()).hexdigest()==PIN
assert hashlib.sha256((p/'node').read_bytes()).hexdigest()==NODE_PIN
mount.mkdir(mode=0o700);attached=False
try:
 r=subprocess.run(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-plist','-mountpoint',str(mount),str(dmg)],capture_output=True,timeout=90)
 assert r.returncode==0;entities=plistlib.loads(r.stdout)['system-entities'];assert any(e.get('mount-point')==str(mount) for e in entities);attached=True
 source=mount/'Google Chrome.app';assert source.is_dir() and not source.is_symlink()
 requirement='=identifier "com.google.Chrome" and anchor apple generic and certificate leaf[subject.OU] = "EQHXZ8M8AV"'
 subprocess.run(['/usr/bin/ditto',str(source),str(target)],check=True,capture_output=True,timeout=120)
 # Apple QA1940: Finder metadata/resource forks are forbidden by codesign.
 # Normalize only those two attributes on this new, unexecuted private copy.
 # Preserve quarantine and every other attribute; strict Apple/Google signature
 # verification below remains mandatory before any browser launch.
 normalized=normalize_finder_metadata(target)
 subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R',requirement,str(target)],check=True,capture_output=True,timeout=120)
finally:
 if attached:subprocess.run(['/usr/bin/hdiutil','detach',str(mount)],check=True,capture_output=True,timeout=30)
 if mount.exists():mount.rmdir()
value=dict(outcome='PASS_ISOLATED_SIGNED_HEADED_UI_RUNTIME',path=str(p),browserExecutable=str(target/'Contents/MacOS/Google Chrome'),browserSignatureVerified=True,mediaSha256=PIN,browserStarted=False,systemToolsChanged=False,mediaDetached=True,finderMetadataNormalized=normalized,quarantinePreserved=True)
print(json.dumps(value))
'''.replace('REMOTE',repr(str(remote))).replace('NODE_PIN',repr(h.digest(node))).replace('PIN',repr(h.digest(dmg)))
    code=XATTR_HELPER+'\n'+code
    value=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=420))
    h.atomic(build/'signed-delivery.json',value);print(json.dumps(value));return 0


XATTR_HELPER='''def normalize_finder_metadata(target):
 import subprocess
 def quarantine():
  p=subprocess.run(['/usr/bin/xattr','-p','com.apple.quarantine',str(target)],capture_output=True,timeout=10)
  return p.returncode,p.stdout
 before=quarantine()
 for name in ('com.apple.FinderInfo','com.apple.ResourceFork'):
  p=subprocess.run(['/usr/bin/xattr','-r','-d',name,str(target)],capture_output=True,timeout=30)
  assert p.returncode in (0,1)
 assert quarantine()==before
 return True
'''


def finish_signed_browser(c,build,node):
    remote=Path(c['remoteRoot'])/'vision-services-ui-runtime-01'
    code='''import pathlib,subprocess,json,hashlib,os
p=pathlib.Path(REMOTE);target=p/'Google Chrome.app'
assert p.is_dir() and not p.is_symlink() and p.stat().st_uid==os.getuid() and target.is_dir() and not target.is_symlink()
assert hashlib.sha256((p/'node').read_bytes()).hexdigest()==NODE_PIN and not (p/'chrome-mount').exists()
normalized=normalize_finder_metadata(target)
requirement='=identifier "com.google.Chrome" and anchor apple generic and certificate leaf[subject.OU] = "EQHXZ8M8AV"'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R',requirement,str(target)],check=True,capture_output=True,timeout=120)
print(json.dumps(dict(outcome='PASS_ISOLATED_SIGNED_HEADED_UI_RUNTIME',path=str(p),browserExecutable=str(target/'Contents/MacOS/Google Chrome'),browserSignatureVerified=True,browserStarted=False,systemToolsChanged=False,mediaDetached=True,finderMetadataNormalized=normalized,quarantinePreserved=True)))
'''.replace('REMOTE',repr(str(remote))).replace('NODE_PIN',repr(h.digest(node)))
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    value=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',XATTR_HELPER+'\n'+code]),timeout=200))
    h.atomic(build/'signed-delivery.json',value);print(json.dumps(value));return 0


if __name__=='__main__':raise SystemExit(main())
