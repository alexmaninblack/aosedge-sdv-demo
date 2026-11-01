# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import vision_source_guest as v

LOCAL='11111111-1111-4111-8111-111111111111'
REQUEST=dict(role='test',vmProfile=v.PROFILE,vehicle=dict(localVmId=LOCAL))


class VisionProjectionTests(unittest.TestCase):
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


if __name__=='__main__':unittest.main()
