# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import vision_ingress_live_worker as worker


class IngressScenarioTests(unittest.TestCase):
    def test_only_exact_correlated_frame_hash_pairs_count(self):
        value=dict(ingressFrames=[dict(ingressFrame=10,sha256='a'),dict(ingressFrame=12,sha256='b')],
            messages=[dict(probe='LIVE_PAIR',frames=[10,12],sha256=['a','b'],bytesVerified=True)])
        self.assertEqual(len(worker.correlated(value)),1)
        value['messages'][0]['sha256'][1]='foreign';self.assertEqual(worker.correlated(value),[])
        value['messages'][0]['sha256'][1]='b';value['messages'][0]['bytesVerified']=False
        self.assertEqual(worker.correlated(value),[])

    def test_owner_credentials_and_fingerprints_never_enter_evidence(self):
        result=worker.evidence(dict(sha256='artifact',source=dict(fingerprints={'vdp':'DO_NOT_PERSIST'},
            selectedSource=dict(selectedPlatformUnitCertificateSha256='DO_NOT_PERSIST'),
            runnerCommand=['DO_NOT_PERSIST']),camera=dict(sourceEpoch='public-simulation-epoch')))
        self.assertNotIn('DO_NOT_PERSIST',str(result));self.assertEqual(result['sha256'],'artifact')

    def test_only_the_exact_bind_negative_is_expected_audit(self):
        line='type=AVC avc:  denied  { bind } for pid=1 comm="python3" scontext=system_u:system_r:camera_ingress_t:s0 tcontext=system_u:system_r:camera_ingress_t:s0 tclass=tcp_socket permissive=0'
        self.assertTrue(worker.expected_bind_denial(line))
        for before,after in (('{ bind }','{ bind read }'),('permissive=0','permissive=1'),('tcp_socket','file'),('comm="python3"','comm="foreign"')):
            self.assertFalse(worker.expected_bind_denial(line.replace(before,after)))

    def test_native_inactive_bounding_set_is_preserved_not_dropped_or_expanded(self):
        row=dict(nnp='1',capabilities={k:'0' for k in ('CapEff','CapPrm','CapInh','CapAmb')})
        row['capabilities']['CapBnd']='20000420'
        self.assertTrue(worker.inactive_native_capabilities(row,'20000420'))
        self.assertFalse(worker.inactive_native_capabilities(row,'0'))
        row['capabilities']['CapEff']='20'
        self.assertFalse(worker.inactive_native_capabilities(row,'20000420'))
        row['capabilities']['CapEff']='0';row['nnp']='0'
        self.assertFalse(worker.inactive_native_capabilities(row,'20000420'))


if __name__=='__main__':unittest.main()
