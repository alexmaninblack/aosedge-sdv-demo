# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import dataclasses
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService
from aosedge_demo_orchestrator.vm import VMService
from aosedge_demo_orchestrator.vm_profiles import MAIN, VISION, PROFILES, binding, resolve


class VMProfileTests(unittest.TestCase):
    def test_executable_contract_matches_fixed_vision(self):
        root = Path(__file__).resolve().parents[3]
        value = json.loads((root/'contracts/vision-vm/vision-vm-profile.v1.json').read_bytes())
        self.assertEqual((VISION.name, VISION.cpus, VISION.memory_mib, VISION.test_ssh_port, VISION.test_only),
                         tuple(value[k] for k in ('profile','cpus','memoryMiB','testSshPort','testOnly')))
        self.assertEqual('hvf', value['accelerator'])
        self.assertFalse(value['graphicsPassthrough'])

    def test_profiles_are_fixed(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            VISION.cpus = 8
        with self.assertRaises(TypeError):
            PROFILES['new'] = VISION
        for name in (None, {}, 'custom', {'cpus': 4}, 4):
            with self.assertRaisesRegex(ValueError, 'VM_RESOURCE_PROFILE_UNSUPPORTED'):
                resolve(name)

    def test_legacy_is_main_not_vision(self):
        self.assertEqual(MAIN, binding({'vehicles': {'test': {}}}, MAIN.name))
        with self.assertRaisesRegex(ValueError, 'BINDING_MISMATCH'):
            binding({'vehicles': {'test': {}}}, VISION.name)

    def test_vision_cannot_be_adopted_by_main(self):
        with self.assertRaisesRegex(ValueError, 'BINDING_MISMATCH'):
            binding({'vmProfile': VISION.name, 'vehicles': {'test': {}}}, MAIN.name)

    def test_vision_is_test_only(self):
        for roles in ({}, {'production': {}}, {'test': {}, 'production': {}}):
            with self.assertRaisesRegex(ValueError, 'TEST_ONLY'):
                binding({'vmProfile': VISION.name, 'vehicles': roles}, VISION.name)

    def test_environment_default_and_vision_ports(self):
        main = EnvironmentService()
        vision = EnvironmentService(vm_profile=VISION.name)
        self.assertEqual((MAIN.name, 10022, 10023), (main.vm_profile, main.ssh_port('test'), main.ssh_port('production')))
        self.assertEqual(12022, vision.ssh_port('test'))
        with self.assertRaisesRegex(EnvironmentError, 'TEST_ONLY'):
            vision.ssh_port('production')
        for target in ('all', 'production'):
            with self.assertRaisesRegex(EnvironmentError, 'TEST_ONLY'):
                vision.create(target, selector='unused')

    def test_command_changes_only_profile_resources_and_owned_port(self):
        commands = {}
        for profile in (MAIN, VISION):
            environment = EnvironmentService(root=Path('/private/tmp/vision-fixture'), vm_profile=profile.name)
            runtime = VMService(environment)
            item = dict(localVmId='00000000-0000-4000-8000-000000000001', overlay='overlay.qcow2',
                        sshPort=profile.test_ssh_port, mac='02:00:00:00:00:01')
            state = dict(vehicles={'test': item})
            if profile == VISION:state['vmProfile'] = profile.name
            with patch.object(runtime, '_portable', return_value=None), patch('shutil.which', return_value='/fixed/qemu'):
                commands[profile.name] = runtime._command(state, 'test')
            command = commands[profile.name]
            self.assertEqual(str(profile.cpus), command[command.index('-smp')+1])
            self.assertEqual(str(profile.memory_mib), command[command.index('-m')+1])
            self.assertEqual('virt-11.0,accel=hvf', command[command.index('-machine')+1])
            self.assertEqual('host', command[command.index('-cpu')+1])
            self.assertEqual('none', command[command.index('-display')+1])
            self.assertIn('hostfwd=tcp:127.0.0.1:'+str(profile.test_ssh_port), command[command.index('-netdev')+1])

    def test_wrong_profile_fails_before_qemu_or_state_mutation(self):
        environment = EnvironmentService(vm_profile=VISION.name)
        runtime = VMService(environment)
        with patch.object(runtime, '_portable', side_effect=AssertionError('must not inspect assets')):
            with self.assertRaisesRegex(EnvironmentError, 'BINDING_MISMATCH'):
                runtime._command({'vehicles': {'test': {}}}, 'test')
            with self.assertRaisesRegex(EnvironmentError, 'BINDING_MISMATCH'):
                runtime._validate({'vehicles': {'test': {}}}, 'start', ('test',))


class VMProfileLifecycleTests(unittest.TestCase):
    def setUp(self):
        import test_images_environment as fixtures
        from test_vm import FakeRuntime
        support=fixtures.ImagesAndCreateTests()
        with patch('tempfile.tempdir','/private/tmp'):support.setUp()
        self.addCleanup(support.doCleanups)
        self.env=EnvironmentService(support.root,support.catalog,vm_profile=VISION.name)
        self.root=support.root
        if not self.env.qemu_img:self.skipTest('qemu-img fixture prerequisite')
        self.state=self.env.create('test',selector='version-one/main-qemuarm64')
        class VisionRuntime(FakeRuntime):
            def guest(this,access,port,*args,**kwargs):
                self.assertEqual(12022,port)
                return super().guest(access,10022,*args,**kwargs)
        self.runtime=VisionRuntime(self.env)
        from aosedge_demo_orchestrator.guest_access import ACCESS_FILES
        from aosedge_demo_orchestrator.vm import access_path
        access=access_path(self.root,'test');access.mkdir(mode=0o700)
        for name in ACCESS_FILES:
            path=access/name;path.write_text('fixture-not-a-real-key');path.chmod(0o600)
        self.state['vehicles']['test']['runtime']=dict(profile=VISION.name,state='STOPPED',everStarted=False,accessCreated=True,stopProof=None)
        from aosedge_demo_orchestrator.environment import atomic_json,JOURNAL
        atomic_json(self.root/JOURNAL,self.state)
        for name,value in (('qmp',lambda *a:{'status':'running'}),('read_guest',self.runtime.guest),('os.kill',self.runtime.kill)):
            p=patch('aosedge_demo_orchestrator.vm.'+name,value);p.start();self.addCleanup(p.stop)

    def test_fresh_profile_survives_start_stop_restart(self):
        from aosedge_demo_orchestrator.environment import JOURNAL
        for action in ('start','stop','start','stop'):
            value=self.runtime.execute(action,'test',1)
            self.assertEqual('COMPLETED',value['vehicles']['test']['state'])
            saved=json.loads((self.root/JOURNAL).read_bytes())
            self.assertEqual(VISION.name,saved['vmProfile'])
            self.assertEqual(VISION.name,saved['vehicles']['test']['runtime']['profile'])
        qemu=[r for r in self.runtime.spawned if '-smp' in r]
        self.assertEqual(2,len(qemu))
        self.assertTrue(all(r[r.index('-smp')+1]=='4' and r[r.index('-m')+1]=='4096' for r in qemu))

    def test_existing_journal_cannot_be_reprofiled_on_create_or_start(self):
        from aosedge_demo_orchestrator.environment import JOURNAL
        before=(self.root/JOURNAL).read_bytes()
        main=EnvironmentService(self.root,self.env.catalog)
        with self.assertRaisesRegex(EnvironmentError,'BINDING_MISMATCH'):
            main.create('test',selector='version-one/main-qemuarm64')
        with self.assertRaisesRegex(EnvironmentError,'BINDING_MISMATCH'):
            VMService(main).execute('start','test',1)
        self.assertEqual(before,(self.root/JOURNAL).read_bytes())


if __name__ == '__main__':unittest.main()
