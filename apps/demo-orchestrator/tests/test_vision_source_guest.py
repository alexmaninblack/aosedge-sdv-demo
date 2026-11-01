# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import subprocess
import stat
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import vision_source_guest as v

LOCAL='11111111-1111-4111-8111-111111111111'
REQUEST=dict(role='test',vmProfile=v.PROFILE,vehicle=dict(localVmId=LOCAL))


class VisionProjectionTests(unittest.TestCase):
    def test_active_exec_does_not_substitute_for_native_broker_readiness(self):
        values=dict(Uid='991 991 991 991',Gid='989 989 989 989',Groups='985 986 987 988 989',NoNewPrivs='1',
            **{key:'0000000000000000' for key in ('CapEff','CapPrm','CapInh','CapBnd','CapAmb')})
        args=(991,989,{985,986,987,988},'system_u:system_r:vision_exchange_t:s0\x00',True,[True]*4)
        self.assertTrue(v.exchange_ready_facts(values,*args))
        for changed in (dict(values,NoNewPrivs='0'),dict(values,CapEff='0000000000000001'),dict(values,Groups='985 986 987 989'),dict(values,Uid='0 0 0 0')):
            self.assertFalse(v.exchange_ready_facts(changed,*args))
        self.assertFalse(v.exchange_ready_facts(values,991,989,{985,986,987,988},'system_u:system_r:initrc_t:s0',True,[True]*4))
        self.assertFalse(v.exchange_ready_facts(values,*args[:-1],[True]*3+[False]))

    def test_exchange_hello_is_native_bounded_and_duplicate_free(self):
        for text,accepted in ((json.dumps(dict(schemaVersion=1,componentEpoch=LOCAL,state='OEM_HELLO')),True),
            ('{"schemaVersion":1,"componentEpoch":"'+LOCAL+'","state":"OEM_HELLO","state":"OEM_HELLO"}',False),('[]',False)):
            data=text.encode();pending=bytearray(struct.pack('!I',len(data))+data)
            connection=Mock();connection.__enter__=Mock(return_value=connection);connection.__exit__=Mock(return_value=False)
            def recv(size):
                chunk=bytes(pending[:size]);del pending[:size];return chunk
            connection.recv.side_effect=recv
            with patch.object(v.socket,'socket',return_value=connection):
                if accepted:self.assertEqual(v.camera_component_epoch(),LOCAL)
                else:
                    with self.assertRaises(ValueError):v.camera_component_epoch()
            connection.connect.assert_called_once_with('/run/aos-camera-access/oem/producer.sock')

    def test_exchange_requires_exact_scope_and_installed_unit_before_credentials(self):
        for scopes,loaded in (([],True),(list(reversed(v.EXCHANGE_SCOPES)),True),(v.EXCHANGE_SCOPES,False)):
            trust=Mock();trust.call.return_value='LoadState='+('loaded' if loaded else 'not-found')+'\n'
            with patch.object(v,'read') as read:
                with self.assertRaisesRegex(ValueError,'EXCHANGE_'):
                    v.exchange(dict(exchangeScopes=scopes),trust,{},start=True)
                read.assert_not_called();trust.write.assert_not_called()

    def test_exchange_stop_does_not_remove_egress_until_processes_and_jobs_exit(self):
        for after,accepted in (('ActiveState=inactive\nMainPID=0\nJob=0\nControlGroup=\n',True),
                ('ActiveState=inactive\nMainPID=9\nJob=0\n',False),('ActiveState=inactive\nMainPID=0\nJob=4\n',False)):
            trust=Mock();trust.call.side_effect=['LoadState=loaded\nActiveState=active\nMainPID=9\n','',after]
            with patch.object(v,'_egress') as firewall:
                if accepted:
                    self.assertTrue(v.exchange(dict(exchangeScopes=v.EXCHANGE_SCOPES),trust,{},start=False)['stopped'])
                    firewall.assert_called_once_with(trust,{},False,exchange=True)
                else:
                    with self.assertRaisesRegex(ValueError,'EXCHANGE_STOP_'):v.exchange(dict(exchangeScopes=v.EXCHANGE_SCOPES),trust,{},start=False)
                    firewall.assert_not_called()

    def test_pending_first_boot_restore_writes_only_missing_volatile_binding(self):
        expected={Path('/persisted-enrollment'):('same',0o600),v.DROPIN:('dropin',0o644)}
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        with patch.object(v,'first_install_state',return_value=('transaction','candidate')) as native, \
                patch.object(v,'read',return_value='same'),patch.object(v.os.path,'lexists',return_value=False), \
                patch.object(v,'validate_material'),patch.object(v,'status',return_value={}):
            value=v.restore_initial_projection(dict(action='trust-restore'),trust,{}, {},expected)
        trust.write.assert_called_once_with(v.DROPIN,'dropin',0o644)
        trust.activate_consumers.assert_called_once_with(['aos-sm.service'])
        self.assertEqual(native.call_count,3);self.assertTrue(value['persistentEnrollmentUnchanged'])

    def test_pending_first_restore_rejects_changed_material_and_conflicting_dropin(self):
        expected={Path('/persisted-enrollment'):('same',0o600),v.DROPIN:('dropin',0o644)}
        for material,exists in (('different',False),('same',True)):
            trust=Mock()
            with patch.object(v,'first_install_state',return_value=('a','b')),patch.object(v,'read',return_value=material), \
                    patch.object(v.os.path,'lexists',return_value=exists):
                with self.assertRaises(ValueError):v.restore_initial_projection(dict(action='trust-restore'),trust,{}, {},expected)
            trust.call.assert_not_called();trust.write.assert_not_called()

    def test_pending_first_restore_preserves_changed_native_state(self):
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        expected={Path('/persisted-enrollment'):('same',0o600),v.DROPIN:('dropin',0o644)}
        with patch.object(v,'first_install_state',side_effect=[('a','b'),('changed','b')]), \
                patch.object(v,'read',return_value='same'),patch.object(v.os.path,'lexists',return_value=False),patch.object(v,'validate_material'):
            with self.assertRaisesRegex(ValueError,'FIRST_INSTALL_STATE_CHANGED'):
                v.restore_initial_projection(dict(action='trust-restore'),trust,{}, {},expected)
        trust.write.assert_not_called()
        self.assertIn((['systemctl','--no-block','start','aos-sm.service'],),[call.args for call in trust.call.call_args_list])

    def test_host_accepts_only_fixed_closed_vision_failure_codes(self):
        from aosedge_demo_orchestrator.source import SourceDriver
        driver=SourceDriver(SimpleNamespace(root=Path('/unit-test'),progress=lambda _:None))
        state=dict(vmProfile=v.PROFILE,vehicles=dict(test=dict(sshPort=12022)))
        cases=[(dict(ok=False,reason='VISION_SOURCE_FILE_UNSAFE'),'VISION_SOURCE_FILE_UNSAFE'),
               (dict(ok=False,reason='VISION_SOURCE_DO_NOT_PRINT secret'),'SOURCE_GUEST_UNAVAILABLE'),
               (dict(ok=False,reason='VISION_SOURCE_FILE_UNSAFE',extra='secret'),'SOURCE_GUEST_UNAVAILABLE'),
               (None,'SOURCE_GUEST_UNAVAILABLE')]
        for value,expected in cases:
            with patch('aosedge_demo_orchestrator.source.ssh_command',return_value=['unit-ssh']), \
                    patch('aosedge_demo_orchestrator.source.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout=json.dumps(value),stderr='DO_NOT_PRINT')):
                with self.assertRaisesRegex(ValueError,expected) as error:
                    driver.guest(state,'test','trust-status')
                self.assertNotIn('DO_NOT_PRINT',str(error.exception))

    def test_foreign_profile_role_and_main_target_are_rejected_before_mutation(self):
        for extra in (dict(vmProfile='aos-main-qemuarm64-v1'),dict(role='production')):
            with self.assertRaisesRegex(ValueError,'PROFILE_REQUIRED'):
                v.identity(dict(REQUEST,**extra),False)
        data=dict(runtimes=[dict(plugin='systemd-slot-component',type='aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider',config={})])
        with patch.object(Path,'read_bytes',return_value=json.dumps(data).encode()):
            with self.assertRaisesRegex(ValueError,'TARGET_MISMATCH'):
                v.identity(REQUEST,False)

    def test_preprovision_projects_only_server_trust_not_vdp_or_runtime_identity(self):
        trust=Mock()
        with patch.object(v,'identity',return_value=(REQUEST['vehicle'],LOCAL.replace('-',''))):
            value=v.execute(dict(REQUEST,action='configure',ca='public-server-ca'),trust)
        trust.write.assert_called_once_with(Path('/run/democtl-source/ca.pem'),'public-server-ca',0o644)
        trust.call.assert_not_called()
        self.assertTrue(value['preProvision'])
        self.assertEqual('DEFERRED_UNTIL_MUTUAL_TLS',value['runtimeBinding'])

    def test_fixed_test_profile_has_no_legacy_role_projection(self):
        trust=Mock()
        with patch.object(v,'identity',return_value=(REQUEST['vehicle'],LOCAL.replace('-',''))):
            result=v.execute(dict(REQUEST,action='factory-role'),trust)
        self.assertEqual('test',result['role'])
        trust.write.assert_not_called()

    def test_probe_uses_existing_physical_source_owner_and_explicit_vision_path(self):
        source=Mock()
        with patch.object(v,'identity',return_value=(dict(REQUEST['vehicle'],unitId=LOCAL),LOCAL.replace('-',''))):
            v.execute(dict(REQUEST,action='trust-probe'),Mock(),source)
        source.probe.assert_called_once_with(preprovision=False,mutual_tls=True,vision=True)

    def test_status_reports_runtime_not_fabricated_vdp_or_camera_readiness(self):
        trust=SimpleNamespace(call=lambda args:'ActiveState=active\nResult=success\nNRestarts=0\n')
        with patch.object(Path,'is_file',return_value=True):
            result=v.status(trust)
        self.assertFalse(result['vdpInstalled'])
        self.assertNotIn('vdpProcess',result)
        self.assertNotIn('cameraReady',result)
        self.assertEqual('active',result['updateRuntime']['ActiveState'])

    def test_guest_script_fails_closed_and_never_logs_request_material(self):
        request=dict(REQUEST,vmProfile='wrong',action='trust-configure',material={'secret':'DO_NOT_PRINT'})
        code=v.script(request,source_code='',trust_code='')
        completed=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True)
        self.assertEqual(1,completed.returncode)
        self.assertEqual(dict(ok=False,reason='VISION_SOURCE_PROFILE_REQUIRED'),json.loads(completed.stdout))
        self.assertNotIn('DO_NOT_PRINT',completed.stdout+completed.stderr)

    def test_ingress_stop_does_not_require_a_new_image_or_material(self):
        trust=Mock();trust.call.return_value='LoadState=not-found\nActiveState=inactive\nMainPID=0\n'
        with patch.object(v,'camera_egress'):
            value=v.camera(dict(REQUEST,action='camera-stop'),trust,REQUEST['vehicle'])
        self.assertEqual(value,dict(stopped=True,noOp=True));trust.write.assert_not_called()

    def test_ingress_start_rejects_missing_native_unit_before_credential_read(self):
        trust=Mock();trust.call.return_value='LoadState=not-found\n'
        with patch.object(v,'read') as read,patch.object(v,'native_store') as native:
            with self.assertRaisesRegex(ValueError,'INGRESS_NOT_INSTALLED'):
                v.camera(dict(REQUEST,action='camera-start'),trust,REQUEST['vehicle'])
            read.assert_not_called();native.assert_not_called();trust.write.assert_not_called()

    def test_ingress_checks_selected_unit_node_generation_before_projection(self):
        item=dict(unitId=LOCAL,nodeId=LOCAL)
        trust=Mock();trust.call.side_effect=['LoadState=loaded\nActiveState=inactive\n','active\n']
        selected=dict(unitId=LOCAL,nodeId=LOCAL,role='SELECTED_PLATFORM_UNIT',assignmentGeneration=3)
        with patch.object(v,'read',return_value=json.dumps(dict(selectedSource=selected))),patch.object(v,'native_store'):
            with self.assertRaisesRegex(ValueError,'CAMERA_SELECTION_MISMATCH'):
                v.camera(dict(REQUEST,action='camera-start',generation=4,sourceId=LOCAL),trust,item)
        trust.write.assert_not_called()

    def test_ingress_failed_unit_can_stop_only_with_no_pid_job_or_cgroup_process(self):
        for after,accepted in (
            ('ActiveState=failed\nMainPID=0\nJob=0\nControlGroup=\n',True),
            ('ActiveState=failed\nMainPID=22\nJob=0\n',False),
            ('ActiveState=inactive\nMainPID=0\nJob=12\n',False),
            ('ActiveState=inactive\nMainPID=0\nJob=0\nControlGroup=/foreign\n',False)):
            trust=Mock();trust.call.side_effect=['LoadState=loaded\nActiveState=failed\nMainPID=0\n','',after]
            with patch.object(v,'camera_egress') as firewall:
                if accepted:self.assertTrue(v.camera(dict(REQUEST,action='camera-stop'),trust,REQUEST['vehicle'])['stopped'])
                else:
                    with self.assertRaisesRegex(ValueError,'CAMERA_STOP_'):v.camera(dict(REQUEST,action='camera-stop'),trust,REQUEST['vehicle'])
                    firewall.assert_not_called()

    def test_native_egress_is_camera_uid_and_exact_gateway_tuple_before_dnat(self):
        rules=v.camera_egress_rules(992)
        owner={'match':{'op':'==','left':{'meta':{'key':'skuid'}},'right':992}}
        self.assertEqual([r['expr'][0] for r in rules],[owner,owner])
        self.assertEqual(rules[0]['expr'][-1],{'accept':None})
        self.assertEqual(rules[1]['expr'][-2:],[{'counter':None},{'drop':None}])
        self.assertEqual(rules[0]['expr'][1]['match']['right'],'10.0.0.1')
        # TCP payload already implies l4proto; nft removes a redundant explicit
        # meta match when it serializes the installed native rule.
        self.assertEqual(rules[0]['expr'][2]['match']['left']['payload']['protocol'],'tcp')
        self.assertEqual(rules[0]['expr'][2]['match']['right'],6443)
        with self.assertRaisesRegex(ValueError,'UID_INVALID'):v.camera_egress_rules(0)

    def test_egress_counter_normalization_preserves_every_permission(self):
        expected=v.camera_egress_rules(992)[1]
        observed=dict(expected,handle=10,expr=[expected['expr'][0],{'counter':dict(packets=2,bytes=120)},{'drop':None}])
        self.assertEqual(v.camera_egress_observed_rule(observed),expected)
        for counter in ({'packets':-1,'bytes':1},{'packets':1,'bytes':1,'extra':0},{'packets':True,'bytes':1}):
            observed['expr'][1]={'counter':counter}
            with self.assertRaisesRegex(ValueError,'COUNTER_INVALID'):v.camera_egress_observed_rule(observed)

    def test_native_egress_first_repeat_remove_and_foreign_owner_refusal(self):
        current=[];mutations=[]
        def call(args,data=None):
            if args==['nft','-j','list','tables']:
                return json.dumps(dict(nftables=[{'table':dict(name='unrelated',family='inet')}]
                    +[{'table':row['table']} for row in current if 'table' in row]))
            if args==['nft','-j','list','table','inet',v.CAMERA_EGRESS]:
                return json.dumps(dict(nftables=current))
            self.assertEqual(args,['nft','-j','-f','-']);commands=json.loads(data)['nftables'];mutations.append(commands)
            if 'delete' in commands[0]:current.clear()
            else:
                for row in commands:
                    entry=row['add']
                    if 'rule' in entry:
                        rule=entry['rule'];rule['expr']=[{'counter':dict(packets=1,bytes=60)} if x=={'counter':None} else x for x in rule['expr']]
                    current.append(entry)
            return ''
        trust=SimpleNamespace(call=call)
        with patch.object(v.pwd,'getpwnam',return_value=SimpleNamespace(pw_uid=992)):
            self.assertEqual(v.camera_egress(trust,REQUEST['vehicle'],True),dict(enforced=True,noOp=False))
            self.assertEqual(v.camera_egress(trust,REQUEST['vehicle'],True),dict(enforced=True,noOp=True))
            current[0]['table']['comment']='foreign'
            with self.assertRaisesRegex(ValueError,'OWNER_OR_RULES_CHANGED'):v.camera_egress(trust,REQUEST['vehicle'],False)
            self.assertEqual(len(mutations),1)
            current[0]['table']['comment']='democtl-vision-camera:'+LOCAL.replace('-','')
            self.assertEqual(v.camera_egress(trust,REQUEST['vehicle'],False),dict(enforced=False,noOp=False))
            self.assertEqual(v.camera_egress(trust,REQUEST['vehicle'],False),dict(enforced=False,noOp=True))
            self.assertEqual(len(mutations),2)

    def test_native_runtime_requires_its_own_verified_camera_mount(self):
        info=SimpleNamespace(st_mode=stat.S_IFDIR|0o755,st_uid=0,st_dev=4)
        parent=SimpleNamespace(st_dev=3)
        trust=Mock();trust.call.return_value='Camera Access isolated component store is ready.'
        with patch.object(Path,'is_symlink',return_value=False),patch.object(Path,'stat',autospec=True,side_effect=lambda p:info if p==v.RUNTIME else parent), \
             patch.object(Path,'read_text',return_value='/dev/mapper/aosvg-workdirs /var/aos/workdirs ext4 rw 0 0\n'), \
             patch.object(v.os.path,'ismount',return_value=True):
            v.native_store(trust)
            trust.call.assert_called_once_with(['/usr/libexec/aos-camera-access-store-check','verify'])
            trust.call.return_value='not verified'
            with self.assertRaisesRegex(ValueError,'IDENTITY_INVALID'):v.native_store(trust)
            trust.call.return_value='Camera Access isolated component store is ready.'
            info.st_dev=3
            with self.assertRaisesRegex(ValueError,'STORE_UNSAFE'):v.native_store(trust)
            info.st_dev=4
            info.st_uid=1000
            with self.assertRaisesRegex(ValueError,'STORE_UNSAFE'):v.native_store(trust)
            info.st_uid=0;info.st_mode=stat.S_IFDIR|0o777
            with self.assertRaisesRegex(ValueError,'STORE_UNSAFE'):v.native_store(trust)

    def test_missing_native_volume_never_creates_or_mounts_a_replacement(self):
        with patch.object(Path,'is_symlink',return_value=False),patch.object(Path,'read_text',return_value=''), \
             patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(ValueError,'NATIVE_VOLUME_NOT_MOUNTED'):v.native_store(Mock())
            mkdir.assert_not_called()


if __name__=='__main__':unittest.main()
