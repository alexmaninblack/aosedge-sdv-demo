# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Retained-Test upgrade fixtures: no native runtime, network or payload execution."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_distribution_versions as fixtures
from version_management import Versions, control
with patch.object(sys, 'path', [str(fixtures.fixtures.SCRIPTS), *sys.path]):
    import retained_update as update

TEST = 'ec72a0cf-5751-41ef-9939-d7c39c3cbfd7'


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.VersionTests(); f.addCleanup = self.addCleanup; f.setUp()
        self.f = f; f.selected(); self.pin = f.new_version()
        root = f.state
        for name in ('.run/demo-current', '.local/demo-current'):
            (root/name).mkdir(mode=0o700, parents=True)
        (root/'.run/demo-current/writer.lock').touch(mode=0o600)
        (root/'.local/demo-current/validation.qcow2').write_bytes(b'preserved VM fixture')
        (root/'.local/demo-current/validation.qcow2').chmod(0o600)
        self.journal = root/'.run/demo-current/journal.json'
        self.state = dict(schemaVersion=1,kind='democtl.current-run',stage='LOCAL_STOPPED',
            scope='SINGLE_ROLE_ENGINEERING',selectedCloudDomain='aoscloud.io',
            currentVehicle=None,operations=[dict(id=TEST,**{'class':'LOCAL_CREATE'},state='COMPLETED',reconciliation='APPLIED')],
            vehicles=dict(test=dict(localVmId=TEST,overlay='.local/demo-current/validation.qcow2',state='MANUFACTURED',
                mac='02:ec:72:a0:cf:57',sshPort=10022,runtime=dict(state='STOPPED'))),
            factory=dict(format='raw',path='.local/factory/oem-demo-factory.img',
                manifestPath='.local/factory/oem-demo-factory.manifest.json',version='39',sha256='a'*64))
        self.save()
        self.before = update.state_stamp(root)
        for mock in (patch.object(update,'compatibility'),patch.object(update,'local_idle')):
            mock.start(); self.addCleanup(mock.stop)

    def save(self):
        self.journal.write_text(json.dumps(self.state));self.journal.chmod(0o600)

    def upgrade(self, revision=1):
        return self.f.versions.change('upgrade',revision,self.pin)

    def test_upgrade_repeat_restart_preserve_test_bytes_and_predecessor(self):
        old = self.f.pin1
        result = self.upgrade()
        self.assertTrue(result['testPreserved']); self.assertFalse(result['migrationPerformed'])
        self.assertEqual(result['previous'],old)
        self.assertEqual(self.before,update.state_stamp(self.f.state))
        record=self.f.record()
        self.assertTrue(Versions(self.f.store,self.f.state).change('upgrade',2,self.pin)['reused'])
        self.assertEqual(record,self.f.record())
        self.assertEqual(self.before,update.state_stamp(self.f.state))

    def test_ordinary_select_rollback_unselect_remain_blocked(self):
        for action,pin in [('select',self.pin),('rollback',None),('unselect',None)]:
            with self.subTest(action=action),self.assertRaisesRegex(ValueError,'CURRENT_RUN_RETAINED'):
                self.f.versions.change(action,1,pin)

    def test_stale_and_busy_do_not_select(self):
        before=self.f.record()
        with self.assertRaisesRegex(ValueError,'STALE_REVISION'):self.upgrade(0)
        with control.lease(self.f.state/'.run/demo-current/writer.lock',exclusive=True):
            with self.assertRaisesRegex(ValueError,'IN_USE'):self.upgrade()
        self.assertEqual(before,self.f.record())

    def test_invalid_active_pending_or_production_state_fails_closed(self):
        base=copy.deepcopy(self.state); before=self.f.record()
        for change in [dict(stage='LOCAL_ACTIVE'),dict(currentVehicle='test'),dict(vehicles={'production':base['vehicles']['test']}),
                       dict(source=dict(state='STOPPED',operation={'id':TEST})),dict(demoLifecycle=dict(state='UNCERTAIN')),
                       dict(backends=dict(brake=dict(state='RUNNING')))]:
            self.state=dict(base,**change);self.save()
            with self.subTest(change=change),self.assertRaises(ValueError):self.upgrade()
            self.assertEqual(before,self.f.record())
        self.state=base;self.save()
        self.journal.with_name('journal.json.pending').touch(mode=0o600)
        with self.assertRaisesRegex(ValueError,'PENDING'):self.upgrade()
        self.assertEqual(before,self.f.record())

    def test_missing_or_linked_writer_is_not_recreated(self):
        lock=self.f.state/'.run/demo-current/writer.lock';lock.unlink()
        with self.assertRaises(FileNotFoundError):self.upgrade()
        self.assertFalse(lock.exists())
        lock.symlink_to(self.journal)
        with self.assertRaises(ValueError):self.upgrade()

    def test_compatibility_and_native_unknown_preserve_selection(self):
        before=self.f.record()
        for name in ('compatibility','local_idle'):
            with patch.object(update,name,side_effect=ValueError('UPDATE_FIXTURE_BLOCKED')):
                with self.assertRaisesRegex(ValueError,'BLOCKED'):self.upgrade()
            self.assertEqual(before,self.f.record())

    def test_atomic_commit_failure_preserves_data_and_retry_is_explicit(self):
        before=self.f.record()
        with patch.object(control.os,'replace',side_effect=OSError('fixture')):
            with self.assertRaises(OSError):self.upgrade()
        self.assertEqual(before,self.f.record())
        self.assertEqual(self.before,update.state_stamp(self.f.state))
        self.assertEqual(self.upgrade()['current'],self.pin)


class CompatibilityTests(unittest.TestCase):
    def test_completed_upload_is_preserved_not_replayed_or_misreported_ready(self):
        state=dict(selectedCloudDomain='aoscloud.io',vehicles={'test':{}},componentOperations={
            '85.0.0':dict(deploymentId=TEST,target='test',publicationPath='VERIFICATION_TEST',cloudDomain='aoscloud.io',
                upload=dict(attemptStarted=True,state='RESPONDED',response=dict(httpStatus=201,deploymentId=TEST)),
                publication=dict(stage='ACCEPTED',deploymentId=TEST))})
        before=copy.deepcopy(state)
        update.publication_idle(state);self.assertEqual(before,state)
        for field,value in [('state','UNCERTAIN'),('response',{'httpStatus':201,'deploymentId':'different'})]:
            bad=copy.deepcopy(state);bad['componentOperations']['85.0.0']['upload'][field]=value
            with self.assertRaises(ValueError):update.publication_idle(bad)

    def test_idle_proof_rejects_unknown_vm_and_owned_container_without_changes(self):
        from types import SimpleNamespace
        with patch.object(sys,'path',[str(fixtures.fixtures.SCRIPTS),*sys.path]):
            import setup_backends
        from aosedge_demo_orchestrator import probes
        root=Path('/private/tmp/unit-state');store=Path('/private/tmp/unit-store')
        state=dict(vehicles={'test':{'overlay':'.local/demo-current/validation.qcow2'}},operations=[{'id':TEST}])
        def docker(ids='',rows=None):
            def read(*args):return json.dumps(rows) if args[:2]==('container','inspect') else ids
            return SimpleNamespace(engine=lambda:'engine',read=read)
        with patch.object(control,'unused'),patch.object(probes,'process_snapshot',return_value=[]) as processes, \
             patch.object(setup_backends,'Docker',return_value=docker()) as selected:
            update.local_idle(root,store,state)
            processes.return_value=None
            with self.assertRaisesRegex(ValueError,'UNKNOWN'):update.local_idle(root,store,state)
            processes.return_value=[]
            rows=[dict(Id='a'*64,Config={'Labels':{'tech.aosedge.demo.owner':TEST}},Mounts=[])]
            selected.return_value=docker('a'*64,rows)
            with self.assertRaisesRegex(ValueError,'ACTIVE'):update.local_idle(root,store,state)
            rows[0]['Config']['Labels']={};rows[0]['Mounts']=[{'Source':str(root/'data')}]
            with self.assertRaisesRegex(ValueError,'HOLDS_DATA'):update.local_idle(root,store,state)
            rows[0]['Mounts']=[{'Source':'/private/tmp/unrelated'}]
            update.local_idle(root,store,state)

    def test_only_declared_non_migrating_inputs_are_accepted(self):
        before=object();after=object()
        base={'preparation-inputs':dict(factory={'sha256':'f'},vdpProfiles=['1'],runtimePin='r',serviceProfiles=['1']),
              'host-runtime':dict(simulator={'sha256':'s'}),'vm-runtime':dict(files=[{'sha256':'v'}]),
              'cloud-runtime':dict(files=[{'sha256':'c'}])}
        changed=copy.deepcopy(base)
        def descriptor(bundle,group):return (base if bundle is before else changed)[group]
        with patch.object(update,'descriptor',side_effect=descriptor):
            update.compatibility(before,after)
            for group,field in [('preparation-inputs','factory'),('preparation-inputs','runtimePin'),
                                ('host-runtime','simulator'),('vm-runtime','files'),('cloud-runtime','files')]:
                changed=copy.deepcopy(base);changed[group][field]='incompatible'
                with self.subTest(group=group,field=field),self.assertRaises(ValueError):
                    update.compatibility(before,after)

    def test_state_stamp_rejects_links_and_detects_durable_changes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'sentinel').write_bytes(b'old');before=update.state_stamp(root)
            (root/'sentinel').write_bytes(b'new');self.assertNotEqual(before,update.state_stamp(root))
            (root/'link').symlink_to(root/'sentinel')
            with self.assertRaises(ValueError):update.state_stamp(root)


if __name__=='__main__':unittest.main()
