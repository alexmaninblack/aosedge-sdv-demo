# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from aosedge_demo_orchestrator import vision_first_enrollment as host,vision_source_guest as guest

U='11111111-1111-4111-8111-111111111111'
N='22222222-2222-4222-8222-222222222222'


def state():
    return dict(vmProfile=host.PROFILE,currentVehicle=None,vehicles=dict(test=dict(unitId=U,nodeId=N,
        cloud=dict(identity=dict(model='aos-vision-vm')))),source=dict(state='STOPPED',assignmentGeneration=1,
        runnerCommand=['runner'],simulatorCommand=['simulator'],operation=None,
        trust=dict(enabled=True,profile='SELECTED_UNIT_MUTUAL_TLS',target='test',
            fingerprints=dict(dashboard='a'*64,vdp='b'*64,runtime='c'*64),onboarding=dict(state='PENDING',unitId=U,nodeId=N))))


class HostTests(unittest.TestCase):
    def test_only_bound_stopped_pending_vision_defers_restore(self):
        self.assertTrue(host.deferred_boot(state()))
        changes=[lambda s:s.update(vmProfile='main'),lambda s:s.update(currentVehicle='test'),
            lambda s:s['source'].update(state='RUNNING'),lambda s:s['source'].update(operation=dict(id=U)),
            lambda s:s['source']['trust']['onboarding'].update(state='COMPLETE'),
            lambda s:s['source']['trust']['onboarding'].update(unitId=N),
            lambda s:s['source']['trust'].update(pending=dict(action='select')),
            lambda s:s['source']['trust']['fingerprints'].update(runtime='bad'),
            lambda s:s['vehicles']['test']['cloud']['identity'].update(model='aos-vm')]
        for change in changes:
            s=state();change(s);self.assertFalse(host.deferred_boot(s))

    def test_absent_actor_cancellation_preserves_original_intent(self):
        s=state();s['source'].update(state='RUNNING',operation=dict(id=U,initialManual=True,target='test',previous=None,phase='RESET_CONFIRMED'))
        original=copy.deepcopy(s['source']['operation']);driver=Mock();driver.live_process.return_value=None
        service=SimpleNamespace(driver=driver,vm=Mock(),_detach=Mock(return_value={'test':dict(gate='BLOCKED')}))
        value=host.cancel(service,s)
        self.assertTrue(value['initializationCancelled']);self.assertFalse(value['safeStopClaim'])
        self.assertEqual(s['source']['initializationCancellation']['operation'],original)
        self.assertIsNone(s['source']['operation']);self.assertEqual(s['source']['state'],'STOPPED')
        self.assertEqual(s['source']['trust']['onboarding']['state'],'PENDING')
        driver.rpc.assert_not_called();service._detach.assert_called_once_with(s,'test',stopping=True)

    def test_live_manual_ready_cancel_requires_independent_stationary_hold(self):
        for field,value in (('fresh',False),('held',False),('operationId',N),('phase','RELEASED')):
            s=state();s['source'].update(operation=dict(id=U,initialManual=True,target='test',previous=None,phase='RESET_CONFIRMED'))
            frame=dict(fresh=True,held=True,operationId=U,phase='MANUAL_READY',frame=dict(activeMode='MANUAL',speedKmh=0,brake=1));frame[field]=value
            driver=Mock();driver.live_process.return_value=100;driver.rpc.return_value=frame
            with self.assertRaisesRegex(ValueError,'HOLD_UNCONFIRMED'):
                host.cancel(SimpleNamespace(driver=driver),s)
            driver.stop.assert_not_called()


class GuestTests(unittest.TestCase):
    def setUp(self):
        self.tx=dict(schemaVersion=2,operation='install-or-replace',phase='waiting-for-safe-stop',candidateSlot='a',
            candidateItemId=U,candidateSubjectId=N,candidateInstance=0,candidateVersion='0.1.0',
            candidateManifestDigest='sha256:'+'a'*64,candidateRuntimeId=U,candidatePreinstalled=False,hasPrevious=False)
        self.meta=dict(schemaVersion=1,slot='a',**{k:self.tx['candidate'+k] for k in
            ('ItemId','SubjectId','Instance','Version','ManifestDigest','RuntimeId','Preinstalled')})

    def check(self):
        def read(p,m):
            self.assertEqual(m,0o600 if p.name=='transaction.json' else 0o400)
            return json.dumps(self.tx if p.name=='transaction.json' else self.meta)
        with patch.object(guest,'read',side_effect=read), \
                patch.object(guest.os.path,'lexists',return_value=False):
            return guest.first_install_state()

    def test_valid_first_wait_snapshot(self):self.assertEqual(len(self.check()),2)

    def test_wrong_phase_previous_identity_or_candidate_is_rejected(self):
        for field,value in (('phase','committing'),('hasPrevious',True),('candidateVersion','2.0.0'),
                ('candidateRuntimeId','invalid'),('candidateInstance',True),('candidateSlot','../a')):
            with self.subTest(field=field):
                old=self.tx[field];self.tx[field]=value
                with self.assertRaises(ValueError):self.check()
                self.tx[field]=old
        self.meta['RuntimeId']=N
        with self.assertRaisesRegex(ValueError,'CANDIDATE_CHANGED'):self.check()

    def test_existing_active_slot_denies_projection(self):
        with patch.object(guest,'read',return_value=json.dumps(self.tx)),patch.object(guest.os.path,'lexists',return_value=True):
            with self.assertRaisesRegex(ValueError,'PREVIOUS_DEPLOYMENT'):guest.first_install_state()

    def test_partial_enrollment_denied_before_stop_or_write(self):
        trust=Mock()
        with patch.object(guest,'first_install_state',return_value=('tx','candidate')), \
                patch.object(guest.os.path,'lexists',return_value=True):
            with self.assertRaisesRegex(ValueError,'PARTIAL_ENROLLMENT'):
                guest.initial_projection(dict(action='trust-configure'),trust,{}, {},{Path('/fixed') : ('data',0o600)})
        trust.call.assert_not_called();trust.write.assert_not_called()

    def test_state_change_while_writer_stops_denies_writes_and_restores_owner(self):
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        with patch.object(guest,'first_install_state',side_effect=[('tx','candidate'),('changed','candidate'),('changed','candidate')]), \
                patch.object(guest,'validate_material'),patch.object(guest.os.path,'lexists',return_value=False):
            with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):
                guest.initial_projection(dict(action='trust-configure'),trust,{}, {},{Path('/fixed'):('data',0o600)})
        trust.write.assert_not_called()
        trust.call.assert_any_call(['systemctl','--no-block','start','aos-sm.service'])

    def test_first_projection_preserves_wait_and_resumes_native_writer(self):
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        with patch.object(guest,'first_install_state',return_value=('tx','candidate')), \
                patch.object(guest,'validate_material'),patch.object(guest.os.path,'lexists',return_value=False), \
                patch.object(guest,'status',return_value={}):
            value=guest.initial_projection(dict(action='trust-configure'),trust,{}, {},{Path('/fixed'):('data',0o600)})
        self.assertTrue(value['transactionPreservedAtResume']);trust.write.assert_called_once_with(Path('/fixed'),'data',0o600)
        trust.activate_consumers.assert_called_once_with(['aos-sm.service'])

    def test_failed_write_rolls_back_only_new_exact_files_and_restores_writer(self):
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        first,second=Path('/fixed-one'),Path('/fixed-two')
        trust.write.side_effect=[True,OSError('injected write failure')]
        with patch.object(guest,'first_install_state',return_value=('tx','candidate')), \
                patch.object(guest,'validate_material'),patch.object(guest.os.path,'lexists',return_value=False), \
                patch.object(guest,'read',return_value='first'),patch.object(Path,'unlink',autospec=True) as remove:
            with self.assertRaises(OSError):
                guest.initial_projection(dict(action='trust-configure'),trust,{}, {},{first:('first',0o600),second:('second',0o600)})
        remove.assert_called_once_with(first)
        trust.call.assert_any_call(['systemctl','--no-block','start','aos-sm.service'])
        trust.activate_consumers.assert_not_called()

    def test_restore_is_not_first_enrollment(self):
        trust=Mock()
        with self.assertRaisesRegex(ValueError,'CONFIGURE_ONLY'):
            guest.initial_projection(dict(action='trust-restore'),trust,{}, {},{})
        trust.call.assert_not_called()

    def test_foreign_san_and_wrong_key_are_denied_before_persistence(self):
        item=dict(unitId=U,nodeId=N)
        material=dict(vdpCertificate='vdp-cert',vdpKey='vdp-key',runtimeCertificate='runtime-cert',runtimeKey='runtime-key')
        for failure in ('san','key'):
            def call(args,data=None):
                if '-ext' in args:
                    return 'X509v3 Subject Alternative Name:\n URI:urn:aosedge:demo:viss-client:v1:selected-platform-unit:'+('foreign' if failure=='san' else U)+':'+N+'\n'
                return 'wrong' if failure=='key' and args[1]=='pkey' else 'public'
            trust=SimpleNamespace(call=call,write=Mock())
            with self.assertRaisesRegex(ValueError,'IDENTITY_INVALID|KEY_MISMATCH'):
                guest.validate_material(trust,item,material)
            trust.write.assert_not_called()

    def test_executable_contract_has_same_fixed_boundary(self):
        root=Path(__file__).resolve().parents[3]
        value=json.loads((root/'contracts/vision-vm/first-enrollment.v1.json').read_bytes())
        self.assertEqual(value['profile'],host.PROFILE)
        for key,v in value['nativeWait'].items():self.assertEqual(self.tx[key],v)


if __name__=='__main__':unittest.main()
