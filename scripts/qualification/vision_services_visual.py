# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""M4-only headed semantic UI scenario over the real Source projection."""
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time


def require(ok,code):
    if not ok:raise ValueError(code)


def visual(app,env,records,c,observation,guest_request):
    from aosedge_demo_orchestrator import presenter,vision_presenter
    from aosedge_demo_orchestrator.source import SourceService
    from aosedge_demo_orchestrator.units import UnitService
    from aosedge_demo_orchestrator.vm import VMService
    desktop=subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True)
    require(not re.search('CGSSessionScreenIsLocked[^\r\n]{0,16}Yes',desktop),'M4_DESKTOP_LOCKED_UI_NOT_RUN')
    root=records/'visual';root.mkdir(mode=0o700)
    source=SourceService(VMService(env),UnitService(VMService(env)))
    server=presenter.make_server(vision_presenter.assets(root/'assets'),address=('127.0.0.1',18080),reader=vision_presenter.VisionReader(source),vision_only=True)
    # The ordinary Presenter reader also remains bound to this captured root.
    require(server.server_address==('127.0.0.1',18080),'VISION_UI_ADDRESS_CHANGED')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();proc=None;lines=queue.Queue(maxsize=32);facts={}
    def receive(expected,timeout=45):
        value=json.loads(lines.get(timeout=timeout))
        with (root/'browser-protocol.jsonl').open('a') as log:log.write(json.dumps(value)+'\n')
        require(value.get('phase')==expected,'VISION_BROWSER_'+value.get('phase','LOST'))
        return value['data']
    def command(name):proc.stdin.write(name+'\n');proc.stdin.flush();return receive(name)
    try:
        runtime=c['uiRuntime'];executable=Path(runtime['browserExecutable'])
        subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R',
            '=identifier "com.google.Chrome" and anchor apple generic and certificate leaf[subject.OU] = "EQHXZ8M8AV"',str(executable.parents[2])],check=True,capture_output=True,timeout=120)
        request=dict(runtime=runtime['path'],executable=str(executable),records=str(root))
        proc=subprocess.Popen([str(Path(runtime['path'])/'node'),str(records/'vision_services_browser.cjs'),json.dumps(request)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def read():
            for line in proc.stdout:lines.put(line)
        reader=threading.Thread(target=read,daemon=True);reader.start();facts['browser']=receive('READY');facts['baseline']=command('BASELINE')
        before=observation();before_native=guest_request('NATIVE')['instances']
        app.source_service.camera_ingress('stop');facts['inputLoss']=command('UNAVAILABLE')
        require(observation()['state']=='UNAVAILABLE','API_LOSS_NOT_REFLECTED')
        app.source_service.camera_ingress('start');facts['recovery']=command('RECOVERED')
        after=observation();after_native=guest_request('NATIVE')['instances']
        require(after['state']=='AVAILABLE' and after['reference']!=before['reference'],'API_FRESH_RECOVERY_NOT_CONFIRMED')
        require(all(after_native[name]['pid']==row['pid'] for name,row in before_native.items()),'UI_INPUT_LOSS_RESTARTED_NATIVE_APP')
        facts['nativePidsUnchanged']=True
        security=guest_request('OBSERVE');require(not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'PERMANENT_UI_FUNCTIONAL_AVC')
        facts['freshScopedAvcs']=0
        (root/'checkpoint.json').write_text(json.dumps(facts,indent=2)+'\n')
    finally:
        active_error=sys.exc_info()[0] is not None
        browser_error=None
        try:
            if proc is not None:
                if proc.poll() is None:
                    proc.stdin.write('STOP\n');proc.stdin.flush();proc.stdin.close();facts['cleanup']=receive('CLOSED',20)
                proc.wait(timeout=20)
                if proc.returncode:browser_error='VISION_BROWSER_FAILED'
        except Exception:
            browser_error='VISION_BROWSER_CLEANUP_UNCONFIRMED'
            if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=15)
        finally:
            server.shutdown();thread.join(timeout=5);server.server_close();facts['serverStopped']=not thread.is_alive()
        processes=subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True)
        require(not any('--user-data-dir='+str(root/'browser-profile') in row for row in processes.splitlines()),'OWNED_BROWSER_STILL_RUNNING')
        (root/'cleanup.json').write_text(json.dumps(dict(serverStopped=facts['serverStopped'],browserError=browser_error,primaryErrorPreserved=active_error),indent=2)+'\n')
        if browser_error and not active_error:raise ValueError(browser_error)
    (root/'result.json').write_text(json.dumps(facts,indent=2)+'\n');return facts
