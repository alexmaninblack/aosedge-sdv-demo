# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_automation import CampaignError
from release_operator_proof import allowed_amendment


class AmendmentTests(unittest.TestCase):
    def test_explicit_operator_only_scope(self):
        allowed_amendment(['scripts/launcher/drive-download-macos.pl','tests/test_drive_download_parser.py'],[])
    def test_packaged_product_or_empty_scope_is_not_a_tooling_correction(self):
        for paths in ([],['apps/demo-orchestrator/src/aosedge_demo_orchestrator/vm.py'],
                      ['scripts/distribution/setup_build.py'],['workspace/repositories.json']):
            with self.assertRaises(CampaignError):allowed_amendment(paths,[])
    def test_existing_catalog_projection_is_explicit_not_arbitrary(self):
        allowed_amendment(['workspace/launcher-catalog.json'],['workspace/launcher-catalog.json'])
        with self.assertRaises(CampaignError):allowed_amendment(['workspace/foreign.json'],[])
