#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Visible M1 browser executor. No product mutation or additional SSH port."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import subprocess
import select
import time
import remote_harness as h
from build_scratch import directory
from ui_native_gate import validate

HERE=Path(__file__).resolve().parent
NODE_VERSION='22.23.3'
NODE_SHA='23b25245dcfb9af7262f8ff142e9e2e0af025368117329e7a7458a51e5922f53'
CHROME=Path('/Applications/Google Chrome.app')


def read_request(request,sequence):
    h.require(isinstance(request,dict) and set(request)=={'uiRead','id','kind','args'}
              and request['uiRead'] is True and type(request['id']) is int
              and request['id']==sequence+1 and isinstance(request['args'],dict),
              'UI_BROKER_REQUEST_INVALID')
    args=request['args'];kind=request['kind']
    fields={'observe':({'label'},{'label'}),'query':({'name','team','release'},{'name'}),'native':(None,None)}
    h.require(kind in fields,'UI_BROKER_KIND_INVALID')
    if kind=='native': validate(args,args.get('stage'),args.get('action'))
    else:
        allowed,required=fields[kind]
        h.require(set(args)<=allowed and required<=set(args),'UI_BROKER_FIELDS_INVALID')
    return request['id'],kind,args


def transfer(transport,source,target):
    shell=shlex.join(h.ssh_args(transport)[:-1])
    # Copy only named qualification inputs. No --delete, ownership changes,
    # application registration, system install or broad directory targets.
    subprocess.run(['/usr/bin/rsync','-rlpt','-e',shell,str(source),
        transport['user']+'@'+transport['host']+':'+shlex.quote(target)],
        check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=180)


def prepare(transport,workspace,repository,python):
    """Reuse signed local Chrome and installed Playwright, vendor-pinned Node."""
    signature=subprocess.run(['/usr/bin/codesign','-dv','--verbose=4',str(CHROME)],
        check=True,capture_output=True,text=True,timeout=10).stderr
    h.require('TeamIdentifier=EQHXZ8M8AV' in signature,'GOOGLE_BROWSER_SIGNATURE_REQUIRED')
    info=plistlib.loads((CHROME/'Contents/Info.plist').read_bytes())
    modules=repository/'apps/presenter-ui/node_modules'
    versions={name:json.loads((modules/name/'package.json').read_text())['version']
              for name in ('@playwright/test','playwright','playwright-core')}
    cdhash=next(line.split('=',1)[1] for line in signature.splitlines() if line.startswith('CDHash='))
    pin=dict(nodeVersion=NODE_VERSION,nodeArchiveSha256=NODE_SHA,googleChromeCodeDirectory=cdhash,
             googleChromeVersion=info['CFBundleShortVersionString'],modules=versions)
    digest=hashlib.sha256(json.dumps(pin,sort_keys=True).encode()).hexdigest()[:20]
    root=f"/Users/{transport['user']}/SDV-Qualification/ui-tools/{digest}"
    cache=h.unlinked(workspace/'build/qualification-ui-tools'/digest)
    cache.mkdir(parents=True,exist_ok=True,mode=0o700)
    node=cache/'node'
    if not node.exists():
        with directory(workspace) as scratch:
            archive=scratch/'node.tar.gz'
            subprocess.run(['/usr/bin/curl','--fail','--location','--progress-bar','--connect-timeout','10',
                '--max-time','120','--output',str(archive),
                f'https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-darwin-arm64.tar.gz'],check=True)
            h.require(hashlib.sha256(archive.read_bytes()).hexdigest()==NODE_SHA,'NODE_VENDOR_DIGEST_MISMATCH')
            subprocess.run(['/usr/bin/tar','-xzf',str(archive),'-C',str(scratch),
                f'node-v{NODE_VERSION}-darwin-arm64/bin/node'],check=True)
            (scratch/f'node-v{NODE_VERSION}-darwin-arm64/bin/node').replace(node)
    h.require(subprocess.run([str(node),'--version'],capture_output=True,text=True,check=True).stdout.strip()
              =='v'+NODE_VERSION,'NODE_RUNTIME_VERSION_CHANGED')
    installed=h.remote(transport,'test -f '+shlex.quote(root+'/tools.json')+
        ' && /bin/cat '+shlex.quote(root+'/tools.json')+' || true',timeout=10).strip()
    if installed:
        h.require(json.loads(installed)==pin,'UI_TOOLS_PIN_CHANGED')
    else:
        h.remote(transport,'umask 077; /bin/mkdir -p '+shlex.quote(root+'/node_modules/@playwright')+
                 ' '+shlex.quote(root+'/runs'),timeout=10)
        print('visible-m1-tools: copying signed Chrome and browser driver (once)',flush=True)
        transfer(transport,str(CHROME),root+'/')
        transfer(transport,str(node),root+'/node')
        for name in versions:
            transfer(transport,str(modules/name),root+'/node_modules/'+('@playwright/' if '/' in name else ''))
        # rsync intentionally does not copy Finder/resource-fork metadata. Strict
        # signature verification is performed on the copied signed app BEFORE
        # any execution. The original user's app and attributes are untouched.
        h.remote(transport,'/usr/bin/codesign --verify --deep --strict '+shlex.quote(root+'/Google Chrome.app'),timeout=90)
        # Receipt is non-secret, separate from installed product and credentials.
        program='import json, pathlib; pathlib.Path('+repr(root+'/tools.json')+').write_text('+repr(json.dumps(pin))+')'
        h.remote(transport,shlex.quote(python)+" -I -B -c "+shlex.quote(program),timeout=15)
    observed=h.remote(transport,'/usr/bin/codesign -dv --verbose=4 '+shlex.quote(root+'/Google Chrome.app')+
        ' 2>&1; '+shlex.quote(root+'/node')+' --version',timeout=15)
    h.require('CDHash='+cdhash+'\n' in observed and 'TeamIdentifier=EQHXZ8M8AV\n' in observed
              and observed.rstrip().endswith('v'+NODE_VERSION),'COPIED_UI_TOOLS_CHANGED')
    for name in ('ui_journey.mjs','ui_pilot.mjs','ui_observer.mjs','ui_read_broker.mjs'):
        transfer(transport,str(HERE/name),root+'/'+name)
    print('visible-m1-tools: ready; no Docker or product installation changes',flush=True)
    return root,pin


class Observer:
    """Read-only website viewer, never evidence of engineering action via UI."""
    def __init__(self,transport,root,records,python,test,bounds):
        self.transport,self.root,self.python=transport,root,python
        self.records=root+'/runs/'+records.name+'-observer'
        self.process=None
        payload=dict(test=test,records=self.records,windowBounds=dict(zip(('left','top','width','height'),bounds)),
            modulePath=root+'/node_modules/@playwright/test/package.json',
            browserExecutable=root+'/Google Chrome.app/Contents/MacOS/Google Chrome',
            profileDirectory=self.records+'/browser-profile')
        program='import pathlib,os; os.umask(0o077); p=pathlib.Path('+repr(self.records)+'); '+\
            'p.mkdir(mode=0o700); (p/"input.json").write_text('+repr(json.dumps(payload))+')'
        h.remote(transport,shlex.quote(python)+' -I -B -c '+shlex.quote(program),timeout=15)

    def start(self):
        self.process=subprocess.Popen(h.ssh_args(self.transport)+[shlex.join(
            [self.root+'/node',self.root+'/ui_observer.mjs',self.records+'/input.json'])],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        ready,_,_=select.select([self.process.stdout],[],[],45)
        h.require(ready and self.process.stdout.readline().strip()=='OBSERVER_READY','OBSERVER_START_UNCONFIRMED')

    def close(self):
        if self.process is None:return True
        if self.process.poll() is None:
            program='import pathlib; p=pathlib.Path('+repr(self.records+'/observer-stop.json')+'); '+\
                'p.write_text("{}") if not p.exists() else None'
            h.remote(self.transport,shlex.quote(self.python)+' -I -B -c '+shlex.quote(program),timeout=15)
        code=self.process.wait(timeout=30)
        output=self.process.stdout.read();self.process.stdout.close()
        closed=code==0 and 'OBSERVER_CLOSED' in output
        # Stop the owned viewer, but retain its private profile on M1 for
        # operator review. Profiles are never exported with evidence.
        program='import subprocess; '+\
            'names=subprocess.run(["/bin/ps","-axo","comm="],capture_output=True,text=True,check=True).stdout.splitlines(); '+\
            'assert not any(n.startswith('+repr(self.root+'/Google Chrome.app/')+') for n in names)'
        h.remote(self.transport,shlex.quote(self.python)+' -I -B -c '+shlex.quote(program),timeout=20)
        return closed


def remote_run_directory(root,records):
    # Basenames such as "ui" recur under many local campaign roots. Keep
    # deterministic at-most-once ownership, but bind the complete record path.
    digest=hashlib.sha256(str(records.resolve()).encode()).hexdigest()[:24]
    return root+'/runs/'+records.name+'-'+digest


def execute(transport,root,value,records,observe,query,python,native=None):
    """Read broker over SSH stdin/stdout; UI clicks execute on M1, not the broker."""
    remote_records=remote_run_directory(root,records)
    payload=dict(value,visibleM1=True,records=remote_records,modulePath=root+'/node_modules/@playwright/test/package.json',
        browserExecutable=root+'/Google Chrome.app/Contents/MacOS/Google Chrome',
        profileDirectory=remote_records+'/browser-profile')
    # The remote input contains paths, Test and card expectations, never an SSH
    # key, VM password, Cloud certificate, token or development-side config.
    for key in ('python','helper','config','journey','repository'):
        payload.pop(key,None)
    program='import json, pathlib, os; os.umask(0o077); p=pathlib.Path('+repr(remote_records)+'); '+\
        'p.mkdir(mode=0o700); (p/"input.json").write_text('+repr(json.dumps(payload))+')'
    h.remote(transport,shlex.quote(python)+' -I -B -c '+shlex.quote(program),timeout=15)
    process=subprocess.Popen(h.ssh_args(transport)+[shlex.join([root+'/node',root+'/ui_journey.mjs',remote_records+'/input.json'])],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    sequence=0
    try:
        for line in process.stdout:
            if not line.startswith('{'):
                print(line.rstrip(),flush=True);continue
            request=h.parse(line)
            sequence,kind,args=read_request(request,sequence)
            try:
                if kind=='observe':
                    h.require(set(args)=={'label'},'UI_BROKER_FIELDS_INVALID');answer=observe(args['label'])
                elif kind=='query':
                    h.require(set(args)<={'name','team','release'} and 'name' in args,'UI_BROKER_FIELDS_INVALID')
                    answer=query(args['name'],args.get('team'),args.get('release'))
                elif kind=='native':
                    validate(args,args.get('stage'),args.get('action'))
                    if native is not None:
                        answer=native(args)
                    else:
                        h.atomic(records/'native-ui-gate.json',args)
                        deadline=time.monotonic()+120
                        while not (records/'native-ui-click.json').exists():
                            h.require(time.monotonic()<deadline,'NATIVE_UI_GATE_NOT_EXECUTED');time.sleep(.2)
                        answer=h.parse((records/'native-ui-click.json').read_bytes())
                        h.require(answer==dict(args,state='CLICKED_THROUGH_CUA'),'NATIVE_UI_WITNESS_MISMATCH')
                        (records/'native-ui-click.json').unlink();(records/'native-ui-gate.json').unlink()
                else:
                    raise h.Error('UI_BROKER_KIND_INVALID')
                response=dict(id=sequence,ok=True,value=answer)
            except (OSError,ValueError,subprocess.SubprocessError) as error:
                code=str(error) if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',str(error)) else 'UI_BROKER_CHECK_FAILED'
                h.atomic(records/('broker-failure-'+str(sequence)+'.json'),
                    dict(kind=kind,stage=args.get('stage'),code=code,inputReplayed=False,
                         query=args.get('name') if kind=='query' and args.get('name') in
                         ('component','component-idle','service','backend','combined','local','platform','publication','exercise') else None))
                response=dict(id=sequence,ok=False)
            process.stdin.write(json.dumps(response)+'\n');process.stdin.flush()
        code=process.wait(timeout=15)
    finally:
        if process.poll() is None:
            process.terminate();process.wait(timeout=15)
        process.stdin.close();process.stdout.close()
        # Only bounded private reports and masked screenshots, not a browser
        # profile, downloads, cookies or raw trace, leave the test computer.
        shell=shlex.join(h.ssh_args(transport)[:-1])
        subprocess.run(['/usr/bin/rsync','-rpt','--include=*.json','--include=*.jsonl','--include=*.png',
            '--exclude=*','-e',shell,transport['user']+'@'+transport['host']+':'+shlex.quote(remote_records+'/'),
            str(records)+'/'],check=True,capture_output=True,timeout=30)
        # Closing processes is not authorization to delete review materials.
        # Leave the private browser profile on M1; never copy it to evidence.
        cleanup='import subprocess; '+\
            'names=subprocess.run(["/bin/ps","-axo","comm="],capture_output=True,text=True,check=True).stdout.splitlines(); '+\
            'assert not any(n.startswith('+repr(root+'/Google Chrome.app/')+') for n in names),"OWNED_BROWSER_REMAINS"'
        h.remote(transport,shlex.quote(python)+' -I -B -c '+shlex.quote(cleanup),timeout=20)
    return code
