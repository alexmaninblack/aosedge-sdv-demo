# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "artifact-publication-profile"
CONTRACT = CONTRACT_ROOT / "artifact-publication-profile.v1.json"
SCHEMA = CONTRACT_ROOT / "artifact-publication-profile.schema.json"
ACCEPTED_CONTRACT_SHA256 = (
    "52bafd7b1249ec8bc10265e913265cdc7c2975f5f56db7ff3cd5cdbad4001c39"
)


class ArtifactPublicationProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_identity_schema_and_digest_are_frozen(self) -> None:
        self.assertEqual("D4-010.3", self.contract["decision"])
        self.assertEqual("1.0.0", self.contract["contractVersion"])
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./artifact-publication-profile.schema.json",
            self.contract["$schema"],
        )
        self.assertEqual(
            ACCEPTED_CONTRACT_SHA256,
            hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        )

    def test_current_aos_signer_limitation_is_explicit(self) -> None:
        baseline = self.contract["toolBaseline"]
        self.assertEqual("aos-signer", baseline["tool"])
        self.assertEqual("2.0.1", baseline["version"])
        self.assertEqual(
            "SAME_PKCS12_PER_PROFILE_FOR_SIGN_AND_MTLS_UPLOAD",
            baseline["credentialRelationship"],
        )
        self.assertEqual("EMPTY_PASSWORD", baseline["pkcs12PasswordMode"])
        self.assertFalse(baseline["nativeKeychainOperation"])
        self.assertFalse(baseline["nativePkcs11Operation"])
        self.assertTrue(baseline["privateKeyLoadedIntoProcessMemory"])

    def test_exactly_three_non_interchangeable_profiles_exist(self) -> None:
        profiles = {item["profileId"]: item for item in self.contract["profiles"]}
        self.assertEqual({"platform-oem", "brake-sp1", "tire-sp2"}, set(profiles))
        self.assertEqual("OEM", profiles["platform-oem"]["cloudRole"])
        self.assertEqual(["component"], profiles["platform-oem"]["allowedItemTypes"])
        self.assertEqual("SERVICE_PROVIDER_1", profiles["brake-sp1"]["cloudRole"])
        self.assertEqual(["service"], profiles["brake-sp1"]["allowedItemTypes"])
        self.assertEqual("SERVICE_PROVIDER_2", profiles["tire-sp2"]["cloudRole"])
        self.assertEqual(["service"], profiles["tire-sp2"]["allowedItemTypes"])
        self.assertTrue(all(not item["approvalAuthority"] for item in profiles.values()))

    def test_file_credentials_stay_local_and_outside_all_consumers(self) -> None:
        custody = self.contract["credentialCustody"]
        self.assertEqual(3, custody["credentialCount"])
        self.assertEqual("~/.aos/security", custody["localDirectory"])
        self.assertEqual("0600", custody["requiredFileMode"])
        self.assertFalse(custody["gitTracked"])
        self.assertFalse(custody["callerPathAllowed"])
        self.assertEqual(["SESSION_SCOPED_NATIVE_HELPER"], custody["allowedConsumers"])
        self.assertTrue(
            {"GIT", "BROWSER", "DOCKER_CONTAINER", "VM_IMAGE", "LOG"}
            <= set(custody["forbiddenConsumers"])
        )

    def test_helper_has_no_generic_profile_path_or_url_selector(self) -> None:
        helper = self.contract["helperBoundary"]
        self.assertEqual("ONE_COMMON_NATIVE_HELPER", helper["implementation"])
        self.assertEqual("ONE_AUTHENTICATED_DEMO_SESSION", helper["lifetime"])
        self.assertFalse(helper["runsAsRoot"])
        self.assertFalse(helper["persistentDaemon"])
        self.assertFalse(helper["callerMaySelectProfile"])
        self.assertFalse(helper["callerMaySelectCredentialPath"])
        self.assertFalse(helper["callerMaySelectCloudUrl"])

    def test_operation_is_prebuilt_reconciled_and_not_blindly_retried(self) -> None:
        operation = self.contract["operation"]
        self.assertEqual(
            ["PREPARED", "SIGNING", "SIGNED", "PUBLISHING", "PUBLISHED", "FAILED", "UNCERTAIN"],
            operation["states"],
        )
        self.assertFalse(operation["presentationTimeBuild"])
        self.assertTrue(operation["digestReverification"])
        self.assertTrue(operation["publishedRequiresAuthoritativeCloudRead"])
        self.assertEqual("UNCERTAIN", operation["lostResultState"])
        self.assertFalse(operation["blindRetryAllowed"])

    def test_technical_publication_cannot_approve_unit_delivery(self) -> None:
        authority = self.contract["authoritySeparation"]
        self.assertFalse(authority["technicalPublicationIsApproval"])
        self.assertEqual("MATCHING_SERVICE_PROVIDER", authority["servicePublicationRole"])
        self.assertEqual("PLATFORM_TEAM_OEM", authority["fotaPublicationRole"])
        self.assertEqual("AUTHORIZED_OEM", authority["unitDeploymentApprovalRole"])
        self.assertFalse(authority["automaticApprovalAllowed"])

    def test_diagnostics_exclude_credentials_and_raw_tool_output(self) -> None:
        diagnostics = self.contract["diagnostics"]
        self.assertIn("signedBundleDigest", diagnostics["allowed"])
        self.assertIn("cloudObjectIdentity", diagnostics["allowed"])
        self.assertTrue(
            {"privateKey", "pkcs12Bytes", "credentialPath", "rawToolOutput"}
            <= set(diagnostics["forbidden"])
        )


if __name__ == "__main__":
    unittest.main()
