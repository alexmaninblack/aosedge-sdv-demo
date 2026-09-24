# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Restore an existing selected Test after guest boot; never select or enroll."""
import subprocess
import re
import threading
from uuid import UUID, uuid4
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL
from aosedge_demo_orchestrator.status import read_json, now
from aosedge_demo_orchestrator.guest_access import ssh_command
from aosedge_demo_orchestrator.vm import access_path
from aosedge_demo_orchestrator import source_authentication as auth


def boot_id(service, state):
    item=state['vehicles']['test']
    machine=UUID(item['localVmId']).hex
    if machine!=item['systemUid'] or machine!=item['cloud']['identity']['nodeHardwareId']:
        raise EnvironmentError('SOURCE_BOOT_IDENTITY_MISMATCH')
    # Only an allowlisted public boot identifier crosses SSH, never credentials.
    script=("python3 - <<'BOOT_ID'\nfrom pathlib import Path\nfrom uuid import UUID\n"
            "assert Path('/etc/machine-id').read_text().strip()=="+repr(machine)+"\n"
            "print(str(UUID(Path('/proc/sys/kernel/random/boot_id').read_text().strip())))\nBOOT_ID\n")
    r=subprocess.run(ssh_command(access_path(service.root,'test'),item['sshPort'],3),input=script,
                     capture_output=True,text=True,timeout=5)
    if r.returncode or len(r.stdout)>64:
        raise EnvironmentError('SOURCE_BOOT_PROBE_UNAVAILABLE')
    return str(UUID(r.stdout.strip()))


def eligible(state):
    source=state.get('source') or {};item=state.get('vehicles',{}).get('test') or {}
    trust=source.get('trust') or {};onboarding=trust.get('onboarding') or {}
    return (state.get('currentVehicle')=='test' and source.get('state')=='RUNNING'
        and not any(op.get('state') in ('SUBMITTING','UNCERTAIN') for op in state.get('operations',[]))
        and not source.get('operation') and not source.get('stopOperation') and not trust.get('pending')
        and trust.get('enabled') is True and onboarding.get('state')=='COMPLETE'
        and item.get('unitId') and item.get('nodeId') and item.get('systemUid')
        and onboarding.get('unitId')==item['unitId'] and onboarding.get('nodeId')==item['nodeId']
        and item.get('runtime',{}).get('state')=='RUNNING')


def pending(service):
    """Read-only boot probe. Idle checks do not take the journal writer lock."""
    state=read_json(service.root/JOURNAL)
    if not eligible(state):return False
    item=state['vehicles']['test'];source=state['source']
    network=item.get('runtime',{}).get('externalConnectivity')
    # A newly provisioned Test has no operator link-fault record yet. It must
    # be observed under the writer, never assumed ON or physically toggled.
    if network is not None and network.get('state')!='ON':return False
    if not service.vm._owned_pid(service.vm._command(state,'test'),str(service.root/item['overlay'])):return False
    previous=source.get('bootRecovery') or {}
    identity=dict(localVmId=item['localVmId'],unitId=item['unitId'],nodeId=item['nodeId'],
        runId=source['runId'],assignmentGeneration=source['assignmentGeneration'],bootId=boot_id(service,state))
    return not all(previous.get(k)==v for k,v in identity.items())


class SourceBootRecovery:
    """Presenter-owned worker using the existing writer and action interlocks."""
    def __init__(self,service,operations):
        self.service,self.operations=service,operations
        self.stopped=threading.Event()
        self.thread=threading.Thread(target=self.run,name='source-boot-recovery',daemon=True)

    def tick(self):
        with self.operations.lock:
            if self.operations.active or self.operations.uncertain or self.operations.workspace_busy:return
        if not pending(self.service):
            self.observe()
            return
        with self.operations.lock:
            if self.operations.active or self.operations.uncertain or self.operations.workspace_busy:return
            self.operations.source_recovery_busy=True
        try:
            tick(self.service)
        finally:
            self.observe()
            with self.operations.lock:
                self.operations.source_recovery_busy=False

    def observe(self):
        try:
            state=read_json(self.service.root/JOURNAL)
            record=(state.get('source') or {}).get('bootRecovery') or {}
        except (OSError,ValueError):record={}
        with self.operations.lock:
            self.operations.source_recovery={k:record[k] for k in ('state','phase','reason','finishedAt') if k in record}

    def run(self):
        while not self.stopped.wait(10):
            try:self.tick()
            except (EnvironmentError,OSError,ValueError,KeyError,subprocess.SubprocessError):
                pass  # Failed attempts stay journalled; the same boot is never resubmitted.

    def close(self):
        self.stopped.set()
        if self.thread.is_alive():self.thread.join(timeout=20)


def tick(service):
    """One serialized, bounded attempt per exact guest boot and source run."""
    with service.environment._writer(), service.driver.operation(timeout=160):
        state=read_json(service.root/JOURNAL)
        if not eligible(state):return dict(state='NOT_APPLICABLE')
        item=state['vehicles']['test'];source=state['source'];driver=service.driver
        network=item.get('runtime',{}).get('externalConnectivity')
        if network is None:
            observed=driver.guest(state,'test','connectivity-status')
            if observed.get('state') in ('ON','OFF'):
                network=dict(state=observed['state'],source='GUEST_OBSERVATION',observedAt=now())
                item['runtime']['externalConnectivity']=network
                service.vm._save(state)
        if (network or {}).get('state')!='ON':
            return dict(state='DEFERRED',reason='COLD_OFFLINE_AUTHORIZATION_NOT_QUALIFIED')
        command=service.vm._command(state,'test')
        if not service.vm._owned_pid(command,str(service.root/item['overlay'])):
            return dict(state='WAITING_FOR_GUEST')
        identity=dict(localVmId=item['localVmId'],unitId=item['unitId'],nodeId=item['nodeId'],
            runId=source['runId'],assignmentGeneration=source['assignmentGeneration'],bootId=boot_id(service,state))
        previous=source.get('bootRecovery') or {}
        same=all(previous.get(k)==v for k,v in identity.items())
        if same and previous.get('state') in ('ATTEMPTED','FAILED','COMPLETED'):
            return dict(state=previous['state'],noOp=True)
        views=driver.guests(state,'status')
        if views['test']['gate']=='OPEN':
            if not same:
                source['bootRecovery']=dict(identity,state='OBSERVED',observedAt=now())
                service.vm._save(state)
            return dict(state='OBSERVED',noOp=True)
        # Never interpret an explicit BLOCKED gate as a reboot, or repair a
        # deleted gate during a boot already observed healthy.
        if same or views['test']['gate']!='ABSENT':
            return dict(state='BLOCKED',reason='SOURCE_BOOT_GATE_NOT_NEW_BOOT')
        if any(v.get('gate')!='BLOCKED' for role,v in views.items() if role!='test'):
            raise EnvironmentError('SOURCE_BOOT_PEER_NOT_DETACHED')
        actual=auth.observe(driver)
        if (actual.get('state')!='SELECTED' or actual.get('selectedSource')!=auth.selection(state)
            or actual.get('assignmentGeneration')!=source['assignmentGeneration']):
            raise EnvironmentError('SOURCE_BOOT_ASSIGNMENT_MISMATCH')
        control=driver.ready(state)
        if not control.get('fresh') or control.get('held'):
            return dict(state='DEFERRED',reason='SOURCE_BOOT_CONTROL_NOT_AVAILABLE')
        op=str(uuid4())
        record=dict(identity,state='ATTEMPTED',operationId=op,startedAt=now(),phase='SAFE_STOP')
        source['bootRecovery']=record;service.vm._save(state)
        held=False;opened=False
        try:
            driver.rpc(source,'safe_stop',op);held=True
            driver.wait(source,op,'SAFE_STOP')
            record['phase']='RESTORE_EXISTING_GUEST';service.vm._save(state)
            # Existing VM start reconstructs the same retained credential
            # projection and debug endpoint; never creates a new VM or Unit.
            started=service.vm.execute('start','test',120)
            # Nested VM operations are journal writers too. Always reread even
            # on PARTIAL, preserving their UNCERTAIN intent and observations.
            state=read_json(service.root/JOURNAL);source=state['source'];record=source['bootRecovery']
            if started['vehicles']['test']['state']!='COMPLETED':
                result=started['vehicles']['test']
                record['guestRestoreState']=result['state']
                reason=result.get('reason','')
                if isinstance(reason,str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}',reason):
                    record['guestRestoreReason']=reason
                raise EnvironmentError('SOURCE_BOOT_GUEST_RESTORE_INCOMPLETE')
            current=state['vehicles']['test']
            current_identity=dict(localVmId=current['localVmId'],unitId=current['unitId'],nodeId=current['nodeId'],
                runId=source['runId'],assignmentGeneration=source['assignmentGeneration'])
            if (not eligible(state) or any(record.get(k)!=v for k,v in identity.items())
                or any(identity[k]!=v for k,v in current_identity.items())):
                raise EnvironmentError('SOURCE_BOOT_CONTEXT_CHANGED')
            if boot_id(service,state)!=identity['bootId']:
                raise EnvironmentError('SOURCE_BOOT_CHANGED_DURING_RESTORE')
            actual=auth.observe(driver)
            if (actual.get('state')!='SELECTED' or actual.get('selectedSource')!=auth.selection(state)
                or actual.get('assignmentGeneration')!=identity['assignmentGeneration']):
                raise EnvironmentError('SOURCE_BOOT_ASSIGNMENT_MISMATCH')
            if not driver.guest(state,'test','trust-status').get('mutualTlsConfigured'):
                raise EnvironmentError('SOURCE_BOOT_TRUST_NOT_RESTORED')
            record['phase']='RESTORE_ROUTE';service.vm._save(state)
            opened=True
            if driver.guest(state,'test','allow')['gate']!='OPEN':
                raise EnvironmentError('SOURCE_BOOT_ROUTE_UNCONFIRMED')
            if not auth.connection(driver,state,'test',wait=True).get('serverTls'):
                raise EnvironmentError('SOURCE_BOOT_CONNECTION_NOT_READY')
            final=driver.rpc(source,'release',op)
            if final.get('held') or final.get('phase')!='RELEASED':
                raise EnvironmentError('SOURCE_BOOT_RELEASE_UNCONFIRMED')
            held=False
            record.update(state='COMPLETED',phase='READY_SAFE_STOP',finishedAt=now())
            source['lastConnectionConfirmation']=dict(role='test',confirmedAt=now(),runId=source['runId'],
                serverTls=True,initialManual=False,advancingVissFrames=False)
            service.vm._save(state)
            return dict(state='COMPLETED',bootId=identity['bootId'],carMode='SAFE_STOP',newIdentity=False)
        except (EnvironmentError,OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
            if opened:
                try:driver.guest(state,'test','block')
                except (EnvironmentError,OSError,ValueError,subprocess.SubprocessError):pass
            record.update(state='FAILED',reason='SOURCE_BOOT_RECOVERY_REQUIRES_RECONCILIATION',finishedAt=now())
            reason=str(error)
            if isinstance(error,EnvironmentError) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}',reason):record['failureCode']=reason
            latest=read_json(service.root/JOURNAL)
            current=(latest.get('source') or {}).get('bootRecovery') or {}
            if current.get('operationId')==op:
                latest['source']['bootRecovery']=record
                service.vm._save(latest)
            raise EnvironmentError(record['reason']) from None
        finally:
            if held:
                # Release only our own hold, never resume driving or reset scene.
                try:
                    current=driver.rpc(source,'status',op)
                    if current.get('held') and current.get('operationId')==op:
                        driver.rpc(source,'release',op)
                except (EnvironmentError,OSError,ValueError,subprocess.SubprocessError):pass
