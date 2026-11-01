#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Native prerequisites, dummy credential projection or owned nft roundtrip.

No Source process, simulator, Cloud mutation, key/certificate read or SELinux
policy change. The network mode creates/removes only the Camera Source table.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

PROJECTION=r'''import gzip,grp,json,os,pathlib,pwd,subprocess
def call(args):return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=15)
root=pathlib.Path('/run/vision-credential-projection-probe');assert not root.exists();root.mkdir(mode=0o700)
dummy=root/'dummy';dummy.write_text('non-secret credential mechanism fixture');dummy.chmod(0o600)
name='vision-credential-projection-probe'
try:
 call(['systemd-run','--quiet','--unit='+name,'-p','User=aos-camera-access','-p','Group=aos-camera-read',
  '-p','LoadCredential=probe:'+str(dummy),'-p','IPAddressDeny=any','-p','IPAddressAllow=10.0.0.1/32','/usr/bin/sleep','20'])
 pid=int(call(['systemctl','show',name,'--value','-p','MainPID']).strip());assert pid>0
 path=pathlib.Path('/proc')/str(pid)/'root/run/credentials'/(name+'.service')/'probe'
 info=path.stat()
 versions=call(['systemctl','--version']).splitlines()
 cfg=pathlib.Path('/proc/config.gz');flags={}
 if cfg.exists():
  text=gzip.decompress(cfg.read_bytes()).decode()
  for name2 in ('CONFIG_CGROUP_BPF','CONFIG_BPF','CONFIG_BPF_SYSCALL'):
   flags[name2]=next((v.split('=',1)[1] for v in text.splitlines() if v.startswith(name2+'=')),'NOT_ENABLED')
 print(json.dumps(dict(uid=info.st_uid,gid=info.st_gid,mode=oct(info.st_mode&0o777),nlink=info.st_nlink,
  bytes=info.st_size,expectedUid=pwd.getpwnam('aos-camera-access').pw_uid,systemdFeatures=versions[1] if len(versions)>1 else '',kernelFlags=flags)))
finally:
 call(['systemctl','stop',name]);dummy.unlink();root.rmdir()
'''

NETWORK=r'''import gzip,json,pathlib,pwd,subprocess,types
module=types.ModuleType('source_network_proof');exec(SOURCE,module.__dict__)
errors=[]
class Trust:
 @staticmethod
 def call(args,data=None):
  p=subprocess.run(args,input=data,capture_output=True,text=True,timeout=15)
  if p.returncode:
   errors.append(dict(exit=p.returncode,message=p.stderr[-3000:]))
   raise ValueError('NATIVE_NFT_OPERATION_FAILED')
  return p.stdout
item=dict(localVmId=LOCAL_VM)
facts={}
try:
 facts['created']=module.camera_egress(Trust,item,True)
 facts['idempotent']=module.camera_egress(Trust,item,True)
except Exception as error:
 facts['failure']=str(error) if isinstance(error,ValueError) else type(error).__name__
 p=subprocess.run(['nft','-j','list','table','inet',module.CAMERA_EGRESS],capture_output=True,text=True,timeout=10)
 if p.returncode==0:facts['nativeTable']=json.loads(p.stdout)
 # Dry-run each prefix in a single atomic transaction, never install a weaker
 # rule while localizing a missing expression in the retained kernel.
 rules=module.camera_egress_rules(pwd.getpwnam('aos-camera-access').pw_uid)
 table=dict(family='inet',name=module.CAMERA_EGRESS)
 chain=dict(family='inet',table=module.CAMERA_EGRESS,name='output',type='filter',hook='output',prio=-250,policy='accept')
 base=[{'add':{'table':table}},{'add':{'chain':chain}}]
 checks=[('table',base[:1]),('chain',base)]
 for n in range(1,len(rules[0]['expr'])+1):
  rule=dict(rules[0],expr=rules[0]['expr'][:n]+([] if n==len(rules[0]['expr']) else [{'counter':None}]))
  checks.append(('allow-prefix-'+str(n),base+[{'add':{'rule':rule}}]))
 checks.append(('reject',base+[{'add':{'rule':rules[1]}}]))
 facts['dryChecks']=[]
 for label,commands in checks:
  p=subprocess.run(['nft','-c','-j','-f','-'],input=json.dumps(dict(nftables=commands)),capture_output=True,text=True,timeout=15)
  facts['dryChecks'].append(dict(stage=label,exit=p.returncode,message=p.stderr[-1500:]))
 cfg=pathlib.Path('/proc/config.gz')
 if cfg.exists():
  text=gzip.decompress(cfg.read_bytes()).decode()
  facts['kernelNft']=[v for v in text.splitlines() if any(v.startswith(key) for key in ('CONFIG_NFT_','CONFIG_NF_TABLES','CONFIG_NF_REJECT'))]
 facts['kernelRelease']=pathlib.Path('/proc/sys/kernel/osrelease').read_text().strip()
 p=subprocess.run(['modprobe','-n','-v','nft_reject_inet'],capture_output=True,text=True,timeout=10)
 facts['rejectModuleDryRun']=dict(exit=p.returncode,message=(p.stdout+p.stderr)[-3000:])
finally:
 try:facts['removed']=module.camera_egress(Trust,item,False)
 except Exception as error:facts['cleanupFailure']=str(error) if isinstance(error,ValueError) else type(error).__name__
facts['nftErrors']=errors
print(json.dumps(facts))
'''

DELIVERY=r'''import json,pathlib,subprocess
cfg=json.loads(pathlib.Path('/etc/aos/sm.cfg').read_bytes())
rows=[]
for item in cfg['runtimes']:
 if item['plugin'] not in ('rootfs','boot'):continue
 c=item['config'];fields=('versionFilePath','healthCheckServices','loader','detectMode','partitions','versionFile')
 row=dict(plugin=item['plugin'],type=item['type'],isComponent=item.get('isComponent'),config={k:c[k] for k in fields if k in c})
 working=c.get('workingDir')
 if working:
  p=pathlib.Path(working);row['workingDirectoryExists']=p.is_dir()
 rows.append(row)
mounts=[]
for line in pathlib.Path('/proc/mounts').read_text().splitlines():
 f=line.split()
 if f[1] in ('/','/boot','/var/aos/workdirs','/var/aos/iam'):
  mounts.append(dict(target=f[1],source=f[0],filesystem=f[2],readOnly='ro' in f[3].split(',')))
p=subprocess.run(['lsblk','-J','-b','-o','NAME,TYPE,FSTYPE,LABEL,PARTLABEL,SIZE,RO'],capture_output=True,text=True,timeout=10)
assert p.returncode==0 and len(p.stdout)<32768
version=pathlib.Path('/etc/aos/version').read_text().strip();assert len(version)<128
camera=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
print(json.dumps(dict(nativeDelivery=rows,mounts=mounts,blockDevices=json.loads(p.stdout),rootfsVersion=version,
 cameraInstalled=(camera/'state/installed.json').is_file(),cameraTransactionPresent=(camera/'state/transaction.json').exists(),
 enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',upgradeAttempted=False)))
'''


def validate_delivery_inventory(facts):
    assert {v['plugin'] for v in facts['nativeDelivery']}=={'rootfs','boot'},'NATIVE_DELIVERY_DECLARATIONS_INCOMPLETE'
    assert facts['upgradeAttempted'] is False and facts['enforcing'],'DELIVERY_INVENTORY_INVALID'
    return 'DECLARATIONS_ONLY_NOT_UPGRADE_OR_ROLLBACK_ACCEPTANCE'


def main():
    context=json.loads(Path(sys.argv[1]).read_bytes());records=Path(sys.argv[1]).parent
    package=Path(context['main']['packageRoot']);bundle=Path(context['bundle'])
    assert not (records/'result.json').exists(),'EXISTING_ATTEMPT_RECONCILE'
    for name,digest in context.get('files',{}).items():assert hashlib.sha256((records/name).read_bytes()).hexdigest()==digest,'PREFLIGHT_INPUT_CHANGED'
    assert hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==context['main']['manifestSha256']
    subprocess.run(['codesign','--verify','--deep','--strict','-R',
        '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
        str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    # Installed scope must be the trusted base package, not bootstrap tooling.
    # Its CODE_ROOT is captured at import; load it before the verified overlay.
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    bootstrap=v.verify(bundle,context['main']['manifestSha256']);assert bootstrap.manifest_sha256==context['bootstrapManifestSha256']
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
    before=json.loads((native/JOURNAL).read_bytes());item=before['vehicles']['test']
    assert item['runtime']['state']=='STOPPED' and before['source']['state']=='STOPPED'
    result=dict(scenario='VISION_INGRESS_NATIVE_PREFLIGHT',outcome='NOT_COMPLETE',cleanup={})
    start=time.monotonic()
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
        vm=VMService(env,progress=lambda message:print(json.dumps(dict(stage='native-owner',message=str(message)[:100])),flush=True))
        try:
            print(json.dumps(dict(stage='native-preflight-start')),flush=True)
            value=vm.execute('start','test',timeout=150);assert value['vehicles']['test']['state']=='COMPLETED'
            current=json.loads((native/JOURNAL).read_bytes());assert current['vehicles']['test']['unitId']==item['unitId']
            command=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script=r'''import grp,json,os,pathlib,pwd,subprocess,time
def call(args):return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=10)
end=time.monotonic()+20
while True:
 unit=dict(v.split('=',1) for v in call(['systemctl','show','aos-camera-access','-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID']).splitlines())
 if unit['ActiveState']=='active' or time.monotonic()>=end:break
 time.sleep(.25)
names=['/run/credentials','/run/credentials/aos-sm.service','/run/aos-camera-access/oem/producer.sock','/usr/bin/python3','/usr/libexec/aos-camera-access-launcher']
facts=[]
for name in names:
 p=pathlib.Path(name)
 if p.exists():
  s=p.stat();facts.append(dict(kind=p.name,uid=s.st_uid,gid=s.st_gid,mode=oct(s.st_mode&0o777),context=os.getxattr(p,'security.selinux').decode().rstrip('\0')))
pid=int(unit['MainPID']);p=pathlib.Path('/proc')/str(pid)
status=dict(v.split(':',1) for v in (p/'status').read_text().splitlines() if ':' in v) if pid else {}
print(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',unit=unit,
 uid=pwd.getpwnam('aos-camera-access').pw_uid,gid=grp.getgrnam('aos-camera-read').gr_gid,
 nativeContext=(p/'attr/current').read_text().strip() if pid else None,nativeCaps=status.get('CapEff','').strip(),
 labels=facts,credentialMounts=[v for v in pathlib.Path('/proc/1/mountinfo').read_text().splitlines() if ' /run/credentials/' in v],
 pythonVersion=call(['python3','-V']).strip(),systemdVersion=call(['systemctl','--version']).splitlines()[0])))
'''
            if context.get('projectionProbe'):script=PROJECTION
            if context.get('deliveryInventory'):script=DELIVERY
            if context.get('bootInventory'):script=(records/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(run('boot-inventory')))\n"
            if context.get('networkSource'):
                script=NETWORK.replace('SOURCE',repr(context['networkSource'])).replace('LOCAL_VM',repr(item['localVmId']))
            import textwrap
            wrapped='import json,traceback\ntry:\n'+textwrap.indent(script,' ')+'\nexcept Exception as error:\n print(json.dumps(dict(probeError=type(error).__name__,line=traceback.extract_tb(error.__traceback__)[-1].lineno)))\n'
            done=subprocess.run(command,input="python3 - <<'VISION_PREFLIGHT'\n"+wrapped+"\nVISION_PREFLIGHT\n",capture_output=True,text=True,timeout=50)
            assert done.returncode==0,'NATIVE_PREFLIGHT_OBSERVATION_FAILED'
            result['facts']=json.loads(done.stdout)
            assert 'probeError' not in result['facts'],'NATIVE_PREFLIGHT_PROBE_ERROR'
            if context.get('bootInventory'):
                assert result['facts']['readOnlyInspection'] and not result['facts']['bootChanged'],'BOOT_INVENTORY_MUTATION'
                result['acceptance']='READ_ONLY_BOOT_INSPECTION_NOT_UPDATE_ACCEPTANCE'
            elif context.get('deliveryInventory'):
                result['acceptance']=validate_delivery_inventory(result['facts'])
            elif context.get('networkSource'):
                assert result['facts'].get('created',{}).get('enforced') and not result['facts'].get('removed',{}).get('enforced',True),'NETWORK_ROUNDTRIP_FAILED'
            elif context.get('projectionProbe'):
                assert result['facts']['uid']==result['facts']['expectedUid']>0,'PROJECTION_IDENTITY_INVALID'
            else:assert result['facts']['unit']['ActiveState']=='active','NATIVE_CAMERA_NOT_ACTIVE'
            if context.get('permanentCloudPreflight'):
                from aosedge_demo_orchestrator.units import UnitService
                from aosedge_demo_orchestrator.status import read_json,load_configuration
                from aosedge_demo_orchestrator.cloud_runtime import launch
                from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
                with env._writer():
                    UnitService(vm)._wait(read_json(native/JOURNAL),'test',
                        lambda value:value and value['online_status']=='Online','CLOUD_ONLINE',timeout=60)
                config=load_configuration(native)
                sdk,sdk_environment=launch(native,config['cloudPython'],'unit_cloud.py')
                request=dict(cloudDomain=selected_domain(before),oemOwner=cloud_binding(before)['ownerId'],
                    oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                    vehicles={'test':{k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}})
                request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
                tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_cloud.py'),str(tooling)],
                    input=json.dumps(request),text=True,capture_output=True,env=sdk_environment,timeout=120)
                assert done.returncode==0 and len(done.stdout)<262144,'PERMANENT_CLOUD_SDK_FAILED'
                value=json.loads(done.stdout)
                assert value.get('ok'),value.get('reason','PERMANENT_CLOUD_PREFLIGHT_FAILED')
                result['facts']['cloud']=value['data']
                result['acceptance']='READ_ONLY_ACCOUNT_PREFLIGHT_NOT_UPDATE_ACCEPTANCE'
                assert value['data']['ready'],'PERMANENT_CLOUD_SCOPE_BLOCKED'
            result['outcome']='PASS_NATIVE_PREREQUISITES'
        except Exception as error:
            result['code']=str(error) if isinstance(error,AssertionError) else type(error).__name__
        finally:
            try:
                stopped=vm.execute('stop','test',timeout=150)
                result['cleanup']['visionStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
            except Exception:result['cleanup']['visionStopped']=False
            result['cleanup']['retainedUnchanged']=all((path/JOURNAL).read_bytes()==raw for path,raw in retained.items())
            result['seconds']=round(time.monotonic()-start,2)
            if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
            (records/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:val for k,val in result.items() if k!='facts'}),flush=True)
    return 0 if result['outcome']=='PASS_NATIVE_PREREQUISITES' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        # Early verification/import failures must also leave a bounded result.
        # No guessed cleanup claim: these booleans remain false until observed.
        path=Path(sys.argv[1]).parent/'result.json'
        if not path.exists():
            value=dict(scenario='VISION_INGRESS_NATIVE_PREFLIGHT',outcome='NOT_COMPLETE',
                code=type(error).__name__,cleanupVerified=False)
            path.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value),flush=True)
        raise SystemExit(1)
