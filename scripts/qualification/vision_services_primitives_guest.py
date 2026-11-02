#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reversible same-VM NSS/resource/policy transaction, never a crun launcher.

Private original IAM bytes stay in this process only. All candidates live in
/run, canonical rootfs/policy stores remain unchanged, and native owners stop
before each read-only config bind is changed. A coordinator may hold this
context while normal Source and native Aos perform their accepted operations.
"""
import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import re
import copy
import shutil
import stat
import socket
import struct
import subprocess
import time

ROOT=Path('/run/aos-vision-services-proof')
POLICY=Path('/run/vision-camera-store-proof')
RUNTIME=Path('/run/aos-vision-exchange')
UNIT=Path('/run/systemd/system/aos-vision-exchange.service')
IAM_DROPIN=Path('/run/systemd/system/aos-iam.service.d/36-vision-cpuinfo-proof.conf')
CPU=Path('/run/aos-vision-cpuinfo')
OWNERS=('aos-cm.service','aos-sm.service','aos-iam.service')
ROLES=('perception-publish','perception-read','context-read','assessment-publish')


def require(ok,code):
    if not ok:raise ValueError(code)


def call(args,timeout=30):
    done=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    require(done.returncode==0,'VISION_PRIMITIVES_'+Path(args[0]).name.upper().replace('-','_')+'_FAILED');return done.stdout


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def properties(name):
    return dict(row.split('=',1) for row in call(['systemctl','show',name,'--property=ActiveState,MainPID,NRestarts,Result']).splitlines() if '=' in row)


def stop_native():
    call(['systemctl','stop',*OWNERS],45)
    require(all(properties(name)['MainPID']=='0' and properties(name)['ActiveState'] in ('inactive','failed') for name in OWNERS),'VISION_PRIMITIVES_OWNERS_NOT_STOPPED')


def start_native():
    for name in reversed(OWNERS):call(['systemctl','start',name],25)
    require(all(properties(name)['ActiveState']=='active' and properties(name)['NRestarts']=='0' and int(properties(name)['MainPID'])>0 for name in OWNERS),'VISION_PRIMITIVES_OWNERS_NOT_HEALTHY')


def stores():
    result={}
    for root in (Path('/etc/selinux'),Path('/var/lib/selinux')):
        for path in sorted(root.rglob('*')):
            if path.is_symlink():result[str(path)]=('link',str(path.readlink()))
            elif path.is_file():result[str(path)]=(digest(path),stat.S_IMODE(path.stat().st_mode))
    return result


class Transaction:
    def __init__(self,inputs):
        self.inputs=inputs;self.original={};self.bound=[];self.policy_loaded=False;self.exec_mounted=False;self.broker_exec_mounted=False;self.started=False;self.stock=None;self.canonical=None
        self.unit_text=None;self.iam_text=None;self.created_dirs=[];self.ready=False
        self.audit_cursor=0;self.owner_overrides=[];self.owner_exec_mounted=False;self.image_cache=None;self.exec_diagnosis=None

    def bind(self,source,target):
        require(not os.path.ismount(target),'VISION_PRIMITIVES_CONFIG_ALREADY_BOUND')
        self.original[target]=target.read_bytes();call(['chcon','--reference='+str(target),str(source)])
        call(['mount','--bind',str(source),str(target)]);self.bound.append((source,target))
        call(['mount','-o','remount,bind,ro',str(target)])
        require(os.stat(source).st_ino==os.stat(target).st_ino,'VISION_PRIMITIVES_BIND_CHANGED')

    def open(self):
        require(os.geteuid()==0 and Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc','VISION_PRIMITIVES_SAME_VM_REQUIRED')
        require(call(['getenforce']).strip()=='Enforcing' and not any(p.exists() or p.is_symlink() for p in (ROOT,POLICY,RUNTIME,UNIT,IAM_DROPIN,CPU)),'VISION_PRIMITIVES_CLEAN_BASELINE_REQUIRED')
        require(all(properties(name)['ActiveState']=='active' and properties(name)['NRestarts']=='0' for name in OWNERS),'VISION_PRIMITIVES_HEALTHY_BASELINE_REQUIRED')
        names={'aos-vision-exchange'}|{'aos-vision-'+role for role in ROLES}
        require(not any(u.pw_name in names for u in pwd.getpwall()) and not any(g.gr_name in names for g in grp.getgrall()),'VISION_PRIMITIVES_NSS_COLLISION')
        self.stock=Path('/sys/fs/selinux/policy').read_bytes();self.canonical=stores()
        self.audit_cursor=Path('/var/log/audit/audit.log').stat().st_size
        ROOT.mkdir(mode=0o755);self.started=True;(ROOT/'private').mkdir(mode=0o700)
        POLICY.mkdir(mode=0o700);saved=POLICY/'stock-policy.bin';saved.write_bytes(self.stock);saved.chmod(0o600)
        call(['chcon','--reference=/etc/selinux/aos/policy/policy.33',str(saved)])
        (POLICY/'exec').mkdir(mode=0o700);call(['mount','-t','tmpfs','-o','size=2m,mode=0700,nodev','tmpfs',str(POLICY/'exec')]);self.exec_mounted=True
        loader=POLICY/'exec/vision-policy-load';shutil.copyfile(self.inputs/'vision-policy-load',loader);loader.chmod(0o500)
        call(['chcon','--reference=/usr/sbin/load_policy',str(loader)])
        for name in ('policy-base','policy-proof'):
            (POLICY/name/'etc').mkdir(parents=True);(POLICY/name/'var/lib').mkdir(parents=True)
            shutil.copytree('/etc/selinux',POLICY/name/'etc/selinux',symlinks=True)
            shutil.copytree('/var/lib/selinux',POLICY/name/'var/lib/selinux',symlinks=True)
        module=POLICY/'vision_exchange.pp';shutil.copyfile(self.inputs/module.name,module);module.chmod(0o600)
        call(['chcon','-t','semanage_tmp_t',str(module)])
        call(['semodule','-p',str(POLICY/'policy-proof'),'-S','/var/lib/selinux','-s','aos','-i',str(module)],100)
        self.policy_loaded=True;call([str(loader),'load'])
        require(Path('/sys/fs/selinux/policy').read_bytes()!=self.stock and stores()==self.canonical,'VISION_PRIMITIVES_TEMPORARY_POLICY_UNCONFIRMED')
        # /run itself is nosuid. Do not grant nosuid_transition: as in the
        # already qualified ingress proof, use an owned executable tmpfs to
        # reproduce the permanent /usr launcher transition without that flag.
        (ROOT/'exec').mkdir(mode=0o755)
        call(['mount','-t','tmpfs','-o','size=2m,mode=0755,nodev','tmpfs',str(ROOT/'exec')]);self.broker_exec_mounted=True
        for name,source,label in (('camera-access','camera-access','camera_access_store_t'),
                ('aos-vision-exchange-launcher','aos-vision-exchange-proof','vision_exchange_exec_t'),
                ('vision_cpuinfo_projection.py','vision_cpuinfo_projection.py',None)):
            target=(ROOT/'exec'/name) if name=='aos-vision-exchange-launcher' else ROOT/name
            shutil.copyfile(self.inputs/source,target);target.chmod(0o555 if not name.endswith('.py') else 0o444)
            call(['chcon','-t',label,str(target)] if label else ['chcon','--reference=/usr/libexec/aos-demo-service-inputs.py',str(target)])
        call(['chcon','-t','camera_access_store_t',str(ROOT)])
        used_uids={u.pw_uid for u in pwd.getpwall()};used_gids={g.gr_gid for g in grp.getgrall()}
        uid=next(i for i in range(989,199,-1) if i not in used_uids)
        gids=[i for i in range(989,199,-1) if i not in used_gids][:5];require(len(gids)==5,'VISION_PRIMITIVES_ACCOUNT_CAPACITY')
        self.uid=uid;self.gids=dict(zip(('owner',*ROLES),gids))
        passwd=Path('/etc/passwd').read_text();group=Path('/etc/group').read_text()
        passwd+='\naos-vision-exchange:x:'+str(uid)+':'+str(gids[0])+':Vision exchange:/nonexistent:/bin/false\n'
        group+='\n'+'\n'.join(name+':x:'+str(gid)+':' for name,gid in zip(('aos-vision-exchange',*('aos-vision-'+r for r in ROLES)),gids))+'\n'
        resources=json.loads(Path('/etc/aos/resources.cfg').read_bytes());require([r['name'] for r in resources]==['vision-camera-read'],'VISION_PRIMITIVES_RESOURCE_BASELINE_CHANGED')
        resources += [dict(name='vision-'+role,sharedCount=1,groups=['aos-vision-'+role],mounts=[dict(source=str(RUNTIME/role),destination='/run/aosedge/vision/'+role,type='bind',options=['bind','ro','nosuid','nodev','noexec'])]) for role in ROLES]
        iam=json.loads(Path('/etc/aos/iam.cfg').read_bytes());require(iam['nodeInfo'].get('maxDmips')==10000 and 'cpuInfoPath' not in iam['nodeInfo'],'VISION_PRIMITIVES_NODE_BUDGET_CHANGED')
        iam['nodeInfo']['cpuInfoPath']=str(CPU)
        candidates={'passwd':(Path('/etc/passwd'),passwd),'group':(Path('/etc/group'),group),
            'resources.cfg':(Path('/etc/aos/resources.cfg'),json.dumps(resources)),'iam.cfg':(Path('/etc/aos/iam.cfg'),json.dumps(iam))}
        stop_native()
        if (self.inputs/'native-image-path-proof.json').exists():
            plan=json.loads((self.inputs/'native-image-path-proof.json').read_bytes())
            reuse=plan.get('reuseRecordedCache',False)
            require(plan==dict(schemaVersion=1,imagePath='/var/aos/downloads/vision-services/sm-images',preserveOriginal=True,**({'reuseRecordedCache':True} if reuse else {})),'VISION_IMAGE_PATH_PROOF_PLAN_CHANGED')
            source=Path('/var/aos/workdirs/sm/images');parent=Path('/var/aos/downloads/vision-services');target=parent/'sm-images'
            require(source.is_dir() and not source.is_symlink() and os.path.ismount('/var/aos/downloads')
                and shutil.disk_usage('/var/aos/downloads').free>900*1024**2,'VISION_IMAGE_PATH_CAPACITY_OR_OWNERSHIP_CONFLICT')
            # Native immutable cache only; no database, application storage,
            # state, credential, runtime or Camera store is moved or deleted.
            require(all(p.is_symlink() or p.stat().st_uid==0 for p in source.rglob('*')),'VISION_IMAGE_PATH_CACHE_OWNER_CHANGED')
            original={str(p.relative_to(source)):(p.stat().st_size,digest(p)) for p in source.rglob('*') if p.is_file() and not p.is_symlink()}
            if reuse:
                require(parent.is_dir() and target.is_dir() and not parent.is_symlink() and not target.is_symlink()
                    and parent.stat().st_uid==target.stat().st_uid==0 and stat.S_IMODE(parent.stat().st_mode)==0o700,'VISION_IMAGE_PATH_RECORDED_CACHE_OWNER_CHANGED')
            else:
                require(not target.exists() and not parent.exists(),'VISION_IMAGE_PATH_UNRECORDED_CACHE_EXISTS')
                parent.mkdir(mode=0o700);call(['chcon','--reference=/var/aos/workdirs/sm',str(parent)])
                call(['cp','-a','--',str(source),str(target)],45)
            copied={str(p.relative_to(target)):(p.stat().st_size,digest(p)) for p in target.rglob('*') if p.is_file() and not p.is_symlink()}
            require(reuse or copied==original,'VISION_IMAGE_PATH_CACHE_COPY_CHANGED')
            self.image_cache=dict(path=str(target),originalCachePreserved=True,files=len(copied),bytes=sum(row[0] for row in copied.values()),
                partitionBytes=shutil.disk_usage(target).total,freeBytes=shutil.disk_usage(target).free,reusedRecordedNativeCache=reuse)
            sm=json.loads(Path('/etc/aos/sm.cfg').read_bytes());require('imagePath' not in sm.get('imageManager',{}),'VISION_IMAGE_PATH_EXISTING_OVERRIDE')
            sm.setdefault('imageManager',{})['imagePath']=str(target);candidates['sm.cfg']=(Path('/etc/aos/sm.cfg'),json.dumps(sm))
        if (self.inputs/'aos_sm_app').exists():
            require((self.inputs/'aos_cm_app').is_file(),'VISION_CAPACITY_OWNER_PAIR_REQUIRED')
            owners=ROOT/'owners';owners.mkdir(mode=0o700)
            call(['mount','-t','tmpfs','-o','size=128m,mode=0700,nodev','tmpfs',str(owners)]);self.owner_exec_mounted=True
            for unit,name,config in (('aos-sm','aos_sm_app','sm'),('aos-cm','aos_cm_app','cm')):
                stock=Path('/usr/bin')/name;target=owners/name;shutil.copyfile(self.inputs/name,target);target.chmod(0o500)
                require(target.read_bytes()[:6]==b'\x7fELF\x02\x01' and target.read_bytes()[18:20]==b'\xb7\x00','VISION_CAPACITY_OWNER_NOT_ARM64')
                call(['chcon','--reference='+str(stock),str(target)])
                drop=Path('/run/systemd/system')/(unit+'.service.d/37-vision-resource-capacity-proof.conf')
                require(not drop.exists() and not drop.is_symlink(),'VISION_CAPACITY_OVERRIDE_EXISTS')
                drop.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
                text='[Service]\nExecStart=\nExecStart='+str(target)+' -c /etc/aos/'+config+'.cfg -v debug -j\n'
                drop.write_text(text);drop.chmod(0o644);self.owner_overrides.append((drop,text))
        for name,(target,text) in candidates.items():
            source=ROOT/'private'/name;source.write_text(text);source.chmod(stat.S_IMODE(target.stat().st_mode));self.bind(source,target)
        require(pwd.getpwnam('aos-vision-exchange').pw_uid==uid and all(grp.getgrnam('aos-vision-'+r).gr_gid==self.gids[r] for r in ROLES),'VISION_PRIMITIVES_NATIVE_NSS_UNCONFIRMED')
        self.iam_text='[Service]\nExecStartPre=/usr/bin/python3 -I -B '+str(ROOT/'vision_cpuinfo_projection.py')+' --write-profile\n'
        IAM_DROPIN.parent.mkdir(mode=0o755,parents=True,exist_ok=True);IAM_DROPIN.write_text(self.iam_text);IAM_DROPIN.chmod(0o644)
        self.unit_text=(self.inputs/'aos-vision-exchange.service').read_text().replace('ExecStart=/usr/libexec/aos-vision-exchange-launcher','ExecStart='+str(ROOT/'exec/aos-vision-exchange-launcher'))
        require('ReadWritePaths=/run/aos-vision-exchange\n' in self.unit_text,'VISION_PRIMITIVES_WRITE_BOUNDARY_REQUIRED')
        UNIT.write_text(self.unit_text);UNIT.chmod(0o644);call(['chcon','--reference=/usr/lib/systemd/system/aos-camera-access.service',str(UNIT)])
        RUNTIME.mkdir(mode=0o750);os.chown(RUNTIME,uid,gids[0]);self.created_dirs.append(RUNTIME);call(['chcon','-t','vision_exchange_runtime_t',str(RUNTIME)])
        for role in ROLES:
            path=RUNTIME/role;path.mkdir(mode=0o750);os.chown(path,uid,self.gids[role]);self.created_dirs.append(path);call(['chcon','-t','vision_exchange_socket_t',str(path)])
        call(['systemctl','daemon-reload']);start_native();self.ready=True
        require(CPU.is_file() and CPU.read_text().count('cpu cores\t: 4')==4,'VISION_PRIMITIVES_IAM_CPU_WRITER_UNCONFIRMED')
        return dict(outcome='PASS_REVERSIBLE_NATIVE_PRIMITIVES_PREPARATION',nativeOwnersHealthy=True,quotaTopologyCores=4,
            resourcesConfigured=['vision-'+r for r in ROLES],brokerStarted=False,canonicalStoresUnchanged=True,selinuxEnforcing=True,
            artifactDeployment='NOT_RUN',realNativeResourceAllocation='NOT_RUN',nativeImageCache=self.image_cache)

    def observe(self):
        state=properties('aos-vision-exchange.service');pid=int(state.get('MainPID','0'));facts=dict(unit=state,socketCount=0)
        if pid:
            proc=Path('/proc')/str(pid);values=dict(row.split(':',1) for row in (proc/'status').read_text().splitlines() if ':' in row)
            facts.update(uid=list(map(int,values['Uid'].split())),gid=list(map(int,values['Gid'].split())),groups=list(map(int,values['Groups'].split())),
                nnp=values['NoNewPrivs'].strip(),capabilities={k:values[k].strip() for k in ('CapEff','CapPrm','CapInh','CapBnd','CapAmb')},
                context=(proc/'attr/current').read_text().strip())
            mounts=[row.split() for row in (proc/'mountinfo').read_text().splitlines()]
            credentials=[row for row in mounts if row[4]=='/run/credentials/aos-vision-exchange.service']
            facts['credentialMountReadonly']=len(credentials)==1 and 'ro' in credentials[0][5].split(',')
            sockets=[]
            for role in ROLES:
                path=RUNTIME/role/'exchange.sock'
                if path.exists():
                    info=path.lstat();sockets.append(dict(role=role,isSocket=stat.S_ISSOCK(info.st_mode),ownerCorrect=info.st_uid==self.uid,
                        groupCorrect=info.st_gid==self.gids[role],mode=stat.S_IMODE(info.st_mode)))
            facts['sockets']=sockets;facts['socketCount']=len(sockets)
        audit=Path('/var/log/audit/audit.log')
        with audit.open('rb') as stream:stream.seek(self.audit_cursor);raw=stream.read(1048577)
        require(len(raw)<=1048576,'VISION_PRIMITIVES_AUDIT_LIMIT')
        facts['scopedAvcs']=[row[:1800] for row in raw.decode(errors='replace').splitlines() if 'avc:' in row and ('vision_exchange' in row or 'camera_ingress_t' in row)]
        # Native owner/application denials are a separate functional gate, not
        # silently covered by a broker-only empty AVC filter.
        facts['nativeScopedAvcCount']=sum('avc:' in row and any(tag in row for tag in
            ('container_engine_t','comm="aos_sm_app"','comm="aos_cm_app"','vision-services/sm-images')) for row in raw.decode(errors='replace').splitlines())
        return facts

    def storage(self):
        def public(value):
            if isinstance(value,dict):
                return {key:found for key,item in value.items() if not any(word in key.lower() for word in ('cert','credential','key','secret','token'))
                    and (found:=public(item)) is not None}
            if type(value) in (int,float,bool):return value
            if isinstance(value,str) and value.startswith('/var/aos/'):return value
            return None
        cm=json.loads(Path('/etc/aos/cm.cfg').read_bytes());sm=json.loads(Path('/etc/aos/sm.cfg').read_bytes())
        space={}
        for path in ('/var/aos','/var/aos/downloads','/var/aos/workdirs','/var/aos/storages','/var/aos/states'):
            p=Path(path);disk=shutil.disk_usage(p);space[path]=dict(bytes=disk.total,free=disk.free,device=p.stat().st_dev)
        return dict(space=space,imageManager=public(cm.get('imageManager',{})),serviceImageManager=public(sm.get('imageManager',{})),runtimeConfiguration=public(sm.get('runtimes',[])) if isinstance(sm.get('runtimes'),dict) else [],
            ownedMeasurementInputPresent=Path('/var/aos/workdirs/vision-services-measure-inputs').exists())

    def diagnose(self):
        logs={}
        for owner in OWNERS:
            raw=call(['journalctl','-b','-u',owner,'--no-pager','-n','220','-o','cat'],15)
            rows=[]
            for row in raw.splitlines():
                if not any(word in row.lower() for word in ('resource','failed','denied','error','space','instance','layer','image')):continue
                if any(word in row.lower() for word in ('message={','fingerprint','-----begin','privatekey','private_key','password','authorization:')):continue
                row=re.sub(r'https?://[^\s\"\x27]+','<url>',row)
                row=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','<token>',row)
                rows.append(row[:1800])
            logs[owner]=rows[-70:]
        def resources(value,path=''):
            found=[]
            if isinstance(value,dict):
                for key,item in value.items():found+=resources(item,path+'/'+key)
            elif isinstance(value,list):
                for i,item in enumerate(value):found+=resources(item,path+'/'+str(i))
            elif isinstance(value,str) and value.startswith('vision-'):found.append(dict(path=path,value=value))
            return found
        sm=properties('aos-sm.service');pid=int(sm['MainPID'])
        actual=json.loads((Path('/proc')/str(pid)/'root/etc/aos/resources.cfg').read_bytes()) if pid else None
        try:unit_resources=resources(json.loads(Path('/var/aos/aos_unit.cfg').read_bytes()))
        except (OSError,ValueError):unit_resources=None
        return dict(logs=logs,storage=self.storage(),resourceFile=json.loads(Path('/etc/aos/resources.cfg').read_bytes()),smVisibleResourceFile=actual,
            readOnlyExecDiscovery=self.exec_diagnosis,
            mountNamespaces=dict(proof=os.readlink('/proc/self/ns/mnt'),systemManager=os.readlink('/proc/1/ns/mnt'),serviceManager=os.readlink('/proc/'+str(pid)+'/ns/mnt')) if pid else None,
            unitConfigurationResourceReferences=unit_resources)

    def retire_measurement_duplicates(self,expected):
        base=Path('/var/aos/workdirs/vision-services-measure-inputs')
        require(base.is_dir() and not base.is_symlink() and base.stat().st_uid==0,'VISION_MEASUREMENT_INPUT_OWNER_CHANGED')
        names={p.name for p in base.iterdir()};require(names==set(expected),'VISION_MEASUREMENT_INPUT_SET_CHANGED')
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():continue
            for link in [proc/'cwd',proc/'root',*(proc/'fd').glob('*')]:
                try:target=os.readlink(link)
                except (FileNotFoundError,ProcessLookupError,PermissionError,OSError):continue
                require(not (target==str(base) or target.startswith(str(base)+'/')),'VISION_MEASUREMENT_INPUT_STILL_IN_USE')
        removed=[]
        for name,pin in expected.items():
            path=base/name;info=path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1 and info.st_size==pin['bytes']
                and digest(path)==pin['sha256'],'VISION_MEASUREMENT_INPUT_CHANGED')
        for name,pin in expected.items():(base/name).unlink();removed.append(dict(name=name,bytes=pin['bytes']))
        base.rmdir();return dict(outcome='PASS_OWNED_MEASUREMENT_DUPLICATES_RETIRED',removed=removed,bytesFreed=sum(row['bytes'] for row in removed),
            verifiedArchivesRetainedOnSSD=True,testDataAndRuntimeCachesUnchanged=True,storage=self.storage())

    def native(self):
        result={}
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():continue
            try:
                values=dict(row.split(':',1) for row in (proc/'status').read_text().splitlines() if ':' in row)
                uid=list(map(int,values['Uid'].split()))
                if uid[0]<5000:continue
                manifest=proc/'root/app/service-manifest.json'
                if not manifest.is_file() or manifest.stat().st_size>16384:continue
                identity=json.loads(manifest.read_bytes());name=identity.get('codename')
                if name not in ('vision-perception','vision-assessment'):continue
                require(name not in result,'VISION_NATIVE_INSTANCE_AMBIGUOUS')
                rows=[row[3:] for row in (proc/'cgroup').read_text().splitlines() if row.startswith('0::')]
                require(len(rows)==1 and rows[0].startswith('/'),'VISION_NATIVE_CGROUP_INVALID');cgroup=Path('/sys/fs/cgroup'+rows[0])
                mounts=[row.split() for row in (proc/'mountinfo').read_text().splitlines()]
                resources={row[4]:dict(readonly='ro' in row[5].split(','),nosuid='nosuid' in row[5].split(','),nodev='nodev' in row[5].split(','),noexec='noexec' in row[5].split(','))
                    for row in mounts if row[4].startswith('/run/aosedge/')}
                def limit(path):return (cgroup/path).read_text().strip() if (cgroup/path).exists() else None
                open_files=[row.split() for row in (proc/'limits').read_text().splitlines() if row.startswith('Max open files')]
                require(len(open_files)==1,'VISION_NATIVE_FD_LIMIT_UNAVAILABLE')
                temporary=os.statvfs(proc/'root/tmp')
                result[name]=dict(pid=int(proc.name),identity=identity,uid=uid,gid=list(map(int,values['Gid'].split())),groups=list(map(int,values['Groups'].split())),
                    nnp=values['NoNewPrivs'].strip(),seccomp=values.get('Seccomp','').strip(),capabilities={k:values[k].strip() for k in ('CapEff','CapPrm','CapInh','CapBnd','CapAmb')},
                    context=(proc/'attr/current').read_text().strip().rstrip('\x00'),cpuMax=limit('cpu.max'),memoryMax=limit('memory.max'),memoryPeak=limit('memory.peak'),pidsMax=limit('pids.max'),
                    noFileLimits=open_files[0][3:5],tmpFilesystemBytes=temporary.f_blocks*temporary.f_frsize,
                    resourceMounts=resources,credentialMountPresent=any('/run/credentials' in row[4] for row in mounts),
                    forbiddenRolePathsPresent=[role for role in ROLES if (proc/'root/run/aosedge/vision'/role).exists() and '/run/aosedge/vision/'+role not in resources],
                    pythonSha256=digest(proc/'exe'),namespaces={kind:os.readlink(proc/'ns'/kind) for kind in ('mnt','net','pid')},
                    groupMapping=dict(camera=grp.getgrnam('aos-camera-read').gr_gid,**self.gids))
            except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        return dict(instances=result,storage=self.storage())

    def root_denial(self):
        results=[]
        for role in ROLES:
            try:
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                    connection.settimeout(2);connection.connect(str(RUNTIME/role/'exchange.sock'))
                    request=b'{"schemaVersion":1,"operation":"status"}';connection.sendall(struct.pack('!I',len(request))+request)
                    def receive(size):
                        result=bytearray()
                        while len(result)<size:
                            block=connection.recv(size-len(result));require(bool(block),'VISION_PRIMITIVES_PROBE_TRUNCATED');result.extend(block)
                        return bytes(result)
                    size=struct.unpack('!I',receive(4))[0];require(0<size<=4096,'VISION_PRIMITIVES_PROBE_LIMIT')
                    value=json.loads(receive(size));denied=value.get('state')=='REJECTED' and value.get('reason')=='REQUEST_REJECTED'
                    results.append(dict(role=role,denied=denied,layer='PROTOCOL_PEER_IDENTITY'))
            except PermissionError:results.append(dict(role=role,denied=True,layer='KERNEL'))
            except (ConnectionResetError,BrokenPipeError):
                # A rejected SO_PEERCRED peer can be closed before its queued
                # request is consumed; Linux then resets instead of delivering
                # the bounded rejection. Positive native peers are a separate
                # gate; the coordinator also verifies this owner stayed alive.
                results.append(dict(role=role,denied=True,layer='CLOSED_CONNECTION'))
        self.audit_cursor=Path('/var/log/audit/audit.log').stat().st_size
        return dict(outcome='PASS_WRONG_ROOT_PEER_DENIED' if all(row['denied'] for row in results) else 'NOT_COMPLETE',roles=results)

    def native_calibration_diagnosis(self):
        """Read through real existing OCI instances, never launch a substitute."""
        actual=self.native()['instances'];require(set(actual)=={'vision-perception','vision-assessment'},'VISION_CALIBRATION_NATIVE_PAIR_REQUIRED')
        config=json.loads(Path('/etc/aos/sm.cfg').read_bytes());plugins=[row for row in config['runtimes'] if row['plugin']=='container']
        require(len(plugins)==1,'VISION_CALIBRATION_CONTAINER_RUNTIME_AMBIGUOUS')
        root=plugins[0]['config'].get('crunStateRoot','/run/crun');require(root=='/run/crun','VISION_CALIBRATION_NATIVE_RUNTIME_ROOT_CHANGED')
        crun=['crun','--root',root];listing=json.loads(call([*crun,'list','--format=json']))
        self.exec_diagnosis=dict(runtimeRoot=root,listing=[{key:row.get(key) for key in ('id','pid','status')} for row in listing],expectedPids={key:value['pid'] for key,value in actual.items()})
        def execute(role,body):
            observed=actual['vision-'+role];rows=[row for row in listing if row.get('pid')==observed['pid'] and row.get('status')=='running']
            require(len(rows)==1,'VISION_CALIBRATION_EXISTING_OCI_ID_REQUIRED');identifier=rows[0]['id']
            state=json.loads(call([*crun,'state',identifier]));bundle=Path(state['bundle'])
            require(bundle.is_relative_to('/run/aos/runtime') and state['pid']==observed['pid'],'VISION_CALIBRATION_OCI_BINDING_CHANGED')
            spec=json.loads((bundle/'config.json').read_bytes());process=copy.deepcopy(spec['process'])
            require(process['user']['uid']==observed['uid'][0] and process['user']['gid']==observed['gid'][0]
                and set(process['user'].get('additionalGids',[]))==set(observed['groups']) and process.get('noNewPrivileges') is True,'VISION_CALIBRATION_NATIVE_EXEC_IDENTITY_CHANGED')
            process['env']=['PATH=/usr/bin:/bin','PYTHONDONTWRITEBYTECODE=1','PYTHONNOUSERSITE=1']
            for key in ('effective','permitted','inheritable','ambient'):process['capabilities'][key]=[]
            prefix='''import json,os,pathlib,sys
sys.path[:0]=['/app/common','/app','/app/libraries']
uid=list(map(int,next(row.split(':',1)[1] for row in pathlib.Path('/proc/self/status').read_text().splitlines() if row.startswith('Uid:')).split()))
assert uid==EXPECTED_UID and os.getgroups()==EXPECTED_GROUPS
assert {key:os.readlink('/proc/self/ns/'+key) for key in ('mnt','net','pid')}==EXPECTED_NAMESPACES
status=dict(row.split(':',1) for row in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in row)
assert status['NoNewPrivs'].strip()=='1' and status.get('Seccomp','').strip()==EXPECTED_SECCOMP
assert all(int(status[key].strip(),16)==0 for key in ('CapEff','CapPrm','CapInh','CapAmb'))
'''.replace('EXPECTED_UID',repr(observed['uid'])).replace('EXPECTED_GROUPS',repr(sorted(observed['groups']))).replace('EXPECTED_NAMESPACES',repr(observed['namespaces'])).replace('EXPECTED_SECCOMP',repr(observed.get('seccomp','')))
            process['args']=['/usr/bin/python3.12','-I','-B','-c',prefix+body];process['terminal']=False
            path=ROOT/'private/native-read-only-process.json';require(not path.exists(),'VISION_CALIBRATION_EXEC_PROCESS_EXISTS')
            path.write_text(json.dumps(process));path.chmod(0o600)
            streams=[ROOT/'private'/('native-read-only-'+name) for name in ('stdin','stdout','stderr')]
            try:
                for stream in streams:
                    require(not stream.exists(),'VISION_NATIVE_EXEC_STDIO_EXISTS');stream.touch(mode=0o600)
                    call(['chcon','--reference=/proc/'+str(observed['pid'])+'/root/app/service-manifest.json',str(stream)])
                # Owned, correctly labelled diagnostic streams; never chown
                # the SSH control pipe or another owner's standard handles.
                with streams[0].open('rb') as stdin,streams[1].open('wb') as stdout,streams[2].open('wb') as stderr:
                    done=subprocess.run([*crun,'exec','--process',str(path),identifier],stdin=stdin,stdout=stdout,stderr=stderr,timeout=15)
                output=streams[1].read_text();diagnostic=streams[2].read_text()[-1800:]
                self.exec_diagnosis['lastExec']=dict(role=role,exit=done.returncode,stderr=diagnostic)
                require(done.returncode==0 and len(output)<16384,'VISION_CALIBRATION_NATIVE_READ_ONLY_EXEC_FAILED')
                return json.loads(output)
            finally:
                path.unlink()
                for stream in streams:
                    if stream.exists():stream.unlink()
        pair=execute('perception',"from vision_common.client import camera_pair\npair=camera_pair();assert pair is not None\nprint(json.dumps(dict(binding=pair[0],frame=pair[1][-1])))\n")
        body="from vision_common.client import Client\nreader=Client('context-read');reader.request('status');context=reader.request('context',binding="+repr(pair['binding'])+",frame="+repr(pair['frame'])+")\nassert context['kind']=='context'\nvalue=context['calibration'];reason=value['reason']\nassert reason in ('CURRENT','PLANE_UNAVAILABLE','MOUNT_INCOMPATIBLE','CALIBRATION_GEOMETRY_INVALID','CALIBRATION_UNAVAILABLE')\nprint(json.dumps(dict(calibrationAvailable=value['available'],reason=reason,nativeIdentitiesAndNamespacesVerified=True,cameraHashContextMatched=True,credentialUsed=False)))\n"
        return execute('assessment',body)

    def close(self):
        result={}
        if not self.started:return result
        if UNIT.exists():
            call(['systemctl','stop','aos-vision-exchange.service'])
            require(properties('aos-vision-exchange.service')['MainPID']=='0','VISION_PRIMITIVES_BROKER_REMAINS')
        stop_native()
        for source,target in reversed(self.bound):
            require(os.path.ismount(target) and os.stat(source).st_ino==os.stat(target).st_ino,'VISION_PRIMITIVES_CONFIG_OWNER_CHANGED')
            call(['umount',str(target)]);require(target.read_bytes()==self.original[target],'VISION_PRIMITIVES_ORIGINAL_CONFIG_CHANGED')
        result['originalConfigsRestored']=True
        for path,text in ((UNIT,self.unit_text),(IAM_DROPIN,self.iam_text),*self.owner_overrides):
            if text is not None and path.exists():require(path.read_text()==text,'VISION_PRIMITIVES_UNIT_OWNER_CHANGED');path.unlink()
        if CPU.exists():require(CPU.stat().st_uid==0 and not CPU.is_symlink(),'VISION_PRIMITIVES_CPU_FILE_CHANGED');CPU.unlink()
        if self.policy_loaded:
            call([str(POLICY/'exec/vision-policy-load'),'restore']);require(Path('/sys/fs/selinux/policy').read_bytes()==self.stock,'VISION_PRIMITIVES_STOCK_POLICY_NOT_RESTORED')
        require(stores()==self.canonical,'VISION_PRIMITIVES_CANONICAL_STORE_CHANGED');result['stockPolicyAndStoresRestored']=True
        for path in reversed(self.created_dirs):
            require(not path.is_symlink() and path.stat().st_uid==self.uid,'VISION_PRIMITIVES_RUNTIME_OWNER_CHANGED')
            path.rmdir()
        if self.exec_mounted:call(['umount',str(POLICY/'exec')])
        if self.broker_exec_mounted:call(['umount',str(ROOT/'exec')])
        if self.owner_exec_mounted:call(['umount',str(ROOT/'owners')])
        shutil.rmtree(POLICY);shutil.rmtree(ROOT);call(['systemctl','daemon-reload']);start_native()
        result.update(nativeOwnersHealthy=True,selinuxEnforcing=call(['getenforce']).strip()=='Enforcing',ownedScratchRemoved=True)
        return result


def run(inputs):
    transaction=Transaction(Path(inputs));result=dict(outcome='NOT_COMPLETE',cleanup={});started=time.monotonic()
    try:result.update(transaction.open())
    except Exception as error:
        value=str(error);result['code']=value if value.isupper() and len(value)<160 else type(error).__name__
    finally:
        try:result['cleanup']=transaction.close()
        except Exception as error:
            value=str(error);result['cleanupCode']=value if value.isupper() and len(value)<160 else type(error).__name__
    if 'code' in result or 'cleanupCode' in result or not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
    result['seconds']=round(time.monotonic()-started,2);return result
