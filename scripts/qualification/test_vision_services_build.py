# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""No Builder/VM/model execution; target command generation regression."""
import ast
from pathlib import Path
import runpy
import unittest
import tempfile
import hashlib


class ClosureCommandTests(unittest.TestCase):
    def test_live_owner_evidence_does_not_persist_enrollment_fingerprints(self):
        module=runpy.run_path(str(Path(__file__).with_name('vision_services_live.py')))
        value=dict(status='CURRENT',selectedSource=dict(unitId='public-native-id',selectedPlatformUnitCertificateSha256='DO_NOT_COPY'),
            token='DO_NOT_COPY',runnerCommand=['DO_NOT_COPY'],credentialMountReadonly=True)
        cleaned=module['evidence'](value)
        self.assertNotIn('DO_NOT_COPY',str(cleaned));self.assertTrue(cleaned['credentialMountReadonly'])

    def test_allocation_requires_real_writer_proof_and_no_dmips_overcommit(self):
        module=runpy.run_path(str(Path(__file__).with_name('vision_services_prepare.py')))
        root=Path(__file__).resolve().parents[2]
        import json,copy
        allocation=json.loads((root/'contracts/vision-vm/services-allocation.v1.json').read_bytes())
        cpu=dict(outcome='PASS_NATIVE_QUOTA_MAPPING_AND_STOCK_RESTORATION',cleanup=dict(restored=True))
        observed=dict(outcome='PASS_TRANSIENT_FOUR_CPU_NATIVE_QUOTA_MAPPING',actualProfileWriterInNativeIAM=True,
            ownersRestartCountZero=True,topology=dict(packages=1,cores=4,threads=4,online=[0,1,2,3]),
            projectedNativeQuota=[40000,100000],restoredNativeQuota=[10000,100000],cleanup=dict(restored=True))
        measured=dict(outcome='PASS_SAME_VM_ISOLATED_CLOSURE_MEASUREMENTS',cleanup=dict(stopped=True))
        closures={role:dict(licenseNoticesIncluded=True,status='MEASURED_CLOSURE_NOT_SIGNABLE_WITHOUT_NATIVE_MEASUREMENTS_AND_DELIVERY_GATES') for role in ('perception','assessment')}
        self.assertEqual(module['freeze'](allocation,cpu,observed,measured,closures)['perception']['cpuLimit'],7000)
        for value in (dict(observed,actualProfileWriterInNativeIAM=False),dict(observed,restoredNativeQuota=[40000,100000])):
            with self.assertRaises(ValueError):module['freeze'](allocation,cpu,value,measured,closures)
        over=copy.deepcopy(allocation);over['perception']['cpuLimit']=10000
        with self.assertRaises(ValueError):module['freeze'](over,cpu,observed,measured,closures)

    def test_cloud_capacity_projection_does_not_copy_credential_or_identity_fields(self):
        module=runpy.run_path(str(Path(__file__).with_name('vision_services_cloud_preflight.py')))
        raw=dict(cpu=dict(count=4,maxDmips=10000,model='unit'),memory=dict(total=4096),credentials=dict(privateKey='DO_NOT_COPY',expires=1234),nodeId='not-a-number')
        self.assertEqual(module['numeric_capacity'](raw),dict(cpu=dict(count=4,maxDmips=10000),memory=dict(total=4096)))

    def test_streaming_digest_supports_the_macos_system_interpreter(self):
        module=runpy.run_path(str(Path(__file__).resolve().parents[1]/'guest/vision_services_closure_build.py'))
        # Unit fixture only; no model/package input or external operation.
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'fixture';path.write_bytes(b'bounded-unit-input')
            self.assertEqual(module['file_digest'](path),hashlib.sha256(path.read_bytes()).hexdigest())

    def test_shared_source_helper_is_not_misclassified_as_vdp(self):
        module=runpy.run_path(str(Path(__file__).with_name('vision_services_campaign.py')))
        facts=dict(cpuCount=4,selinux='Enforcing',mainServicesPresent=False,sharedSourceHelperPresent=True)
        self.assertTrue(module['native_profile_valid'](facts));facts['mainServicesPresent']=True
        self.assertFalse(module['native_profile_valid'](facts))

    def test_overlapping_placeholders_are_not_partial_substitutions(self):
        module=runpy.run_path(str(Path(__file__).resolve().parents[1]/'guest/vision_services_closure_build.py'))
        values=dict(WORKSPACE='/ssd/closure',NAME='closure-unit',SOURCE_SHA='1'*64,SOURCE_REVISION='4'*40,CLEAN_ROOTFS='/ssd/clean',
            MODEL_DIGEST='2'*64,LIBRARY='/ssd/library.so',LIBRARY_SHA='3'*64,OUTPUT_PATH='/ssd/output',RESUME_OWNED=False,
            INCLUDE_LICENSES=True,QUARANTINE_INCOMPLETE_ASSESSMENT=False,PKGDATA_ROOT='/ssd/pkgdata',LICENSE_ROOT='/ssd/licenses')
        code=module['guest_code'](values);ast.parse(code)
        self.assertIn("'--assessment-library','/ssd/library.so','--assessment-sha256','"+'3'*64+"'",code)
        self.assertIn("'--source-revision','"+'4'*40+"'",code)


if __name__=='__main__':unittest.main()
