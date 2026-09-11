# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import build_parser, render_human, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, digest
from aosedge_demo_orchestrator.releases import ReleaseContinuity, number
from aosedge_demo_orchestrator.service_packages import ServicePackages, RELEASE_FILE, package_configuration, product_files
from aosedge_demo_orchestrator.services import ServiceCatalog
from aosedge_demo_orchestrator import service_cloud

ROOT = Path(__file__).resolve().parents[3]
OWNER = "11111111-1111-4111-8111-111111111111"
SERVICE = "22222222-2222-4222-8222-222222222222"


class ServicePackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "solution"
        self.root.mkdir()
        (self.root / "contracts").symlink_to(ROOT / "contracts", target_is_directory=True)
        self.environment = EnvironmentService(self.root, catalog=SimpleNamespace(project=self.base / "catalog"))
        self.packages = ServicePackages(self.environment)
        self.packages._validate = Mock()
        self.build = dict(sourceRevision="a" * 40, outputPath=str(self.base / "product"), binaries={})
        for name in ("bootstrap", "service"):
            path = self.base / "product/rootfs/usr/bin" / ("brake-health-" + name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + b"\xb7\x00" + b"test fixture")
            path.chmod(0o755)
            self.build["binaries"][str(path.relative_to(self.base / "product"))] = digest(path)
        license_file = self.base / "product/rootfs/usr/share/licenses/brake-health-service/LICENSE"
        license_file.parent.mkdir(parents=True)
        license_file.write_text("Fixture public license\n")
        builder_patch = patch("aosedge_demo_orchestrator.service_packages.ServiceBuilder")
        self.builder = builder_patch.start()
        self.addCleanup(builder_patch.stop)
        self.builder.return_value.execute.return_value = self.build
        catalog_patch = patch("aosedge_demo_orchestrator.service_packages.ServiceCatalog")
        self.catalog = catalog_patch.start()
        self.addCleanup(catalog_patch.stop)
        self.catalog.return_value.release_versions.return_value = dict(serviceId=SERVICE, ownerId=OWNER, versions=["7.0.0"])

    def test_prepare_before_vehicle_uses_one_version_and_returns_handle(self):
        result = self.packages.prepare("brake", "v1")
        self.assertEqual(("8.0.0", "brake/8.0.0", "PREPARED"), (result["version"], result["releaseHandle"], result["state"]))
        directory = Path(result["packagePath"])
        outer = json.loads((directory / "config.yaml").read_text())
        inner = json.loads((directory / "service/arm64" / RELEASE_FILE).read_text())
        self.assertEqual(inner, dict(schemaVersion=1, serviceVersion=outer["items"][0]["version"]))
        self.assertEqual(0o444, (directory / "service/arm64" / RELEASE_FILE).stat().st_mode & 0o777)
        # The shared writer uses a local lock, not a vehicle lifecycle journal.
        self.assertFalse((self.root / ".run/demo-current/journal.json").exists())
        self.assertFalse((self.base / "product/rootfs" / RELEASE_FILE).exists())
        self.assertEqual("PREPARED_NOT_RUNTIME_QUALIFIED", result["qualification"])
        self.builder.return_value.execute.assert_called_once_with("brake", "v1", build_missing=False)
        self.catalog.return_value.release_versions.assert_called_once_with("brake", "service-provider")
        for name, expected in result["files"].items():
            self.assertEqual(expected, digest(directory / name))
        raw = (directory / "config.yaml").read_text()
        for forbidden in ("unitSystemUid", "serviceInstance", "AOS_SECRET", "serviceArtifactSha256", "signKey", "tlsKey"):
            self.assertNotIn(forbidden, raw)

    def test_new_release_same_profile_keeps_payload_and_preserves_old_package(self):
        first = self.packages.prepare("brake", "v1")
        second = self.packages.prepare("brake", "v1")
        self.assertEqual("9.0.0", second["version"])
        changed = [key for key in first["files"] if first["files"][key] != second["files"][key]]
        self.assertEqual({"config.yaml", "service/arm64/" + RELEASE_FILE}, set(changed))
        self.assertEqual(first, json.loads((Path(first["packagePath"]) / "prepared.json").read_text()))

    def test_explicit_delivery_only_mode_removes_only_permissions(self):
        for team, profile in (("brake", "v1"), ("brake", "v2"), ("brake", "v3"), ("tire", "v1")):
            expected = package_configuration(ROOT, team, profile, "42.0.0")
            del expected["items"][0]["configuration"]["permissions"]
            self.assertEqual(expected, package_configuration(ROOT, team, profile, "42.0.0", without_permissions=True))
            self.assertIn("permissions", package_configuration(ROOT, team, profile, "42.0.0")["items"][0]["configuration"])
        first = self.packages.prepare("brake", "v1")
        second = self.packages.prepare("brake", "v1", without_permissions=True)
        self.assertTrue(second["withoutPermissions"])
        self.assertEqual("DELIVERY_ONLY_NO_KUKSA_AUTH", second["qualification"])
        self.assertEqual({"config.yaml", "service/arm64/" + RELEASE_FILE},
            {name for name in first["files"] if first["files"][name] != second["files"][name]})
        self.assertNotIn("permissions", json.loads((Path(second["packagePath"]) / "config.yaml").read_text())["items"][0]["configuration"])

    def test_delivery_only_flag_reaches_shared_dispatch_and_is_not_global(self):
        request = request_from_arguments(build_parser().parse_args(["service", "prepare", "brake", "--profile", "v1", "--without-permissions"]))
        self.assertTrue(request.without_permissions)
        with patch("aosedge_demo_orchestrator.service_packages.ServicePackages", return_value=self.packages):
            result = DemoOrchestrator(environment_service=self.environment).execute(request)
        self.assertEqual("COMPLETED", result.state.value)
        self.assertEqual("DELIVERY_ONLY_NO_KUKSA_AUTH", result.data["qualification"])
        from aosedge_demo_orchestrator.models import OperationRequest
        self.assertIsNotNone(OperationRequest("service", "upload", without_permissions=True).selection_error())

    def test_private_operator_umask_does_not_hide_payload_from_native_uid(self):
        previous = os.umask(0o077)
        try:
            result = self.packages.prepare("brake", "v1")
        finally:
            os.umask(previous)
        for directory, _, _ in os.walk(Path(result["packagePath"]) / "service"):
            self.assertEqual(0o755, Path(directory).stat().st_mode & 0o777)

    def test_catalog_team_symlink_cannot_redirect_new_package(self):
        parent = self.base / "catalog/services"
        parent.mkdir(parents=True)
        (parent / "tire").mkdir()
        (parent / "brake").symlink_to(parent / "tire", target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, "PATH_UNSAFE"):
            self.packages.prepare("brake", "v1")
        self.assertEqual([], list((parent / "tire").iterdir()))
        self.assertEqual({}, ReleaseContinuity(self.environment).read()["versions"])

    def test_finder_metadata_is_not_a_release_number(self):
        directory = self.base / "catalog/services/brake/releases"
        directory.mkdir(parents=True)
        (directory / ".DS_Store").write_bytes(b"Finder fixture")
        self.assertEqual("8.0.0", self.packages.prepare("brake", "v1")["version"])
        self.assertEqual(b"Finder fixture", (directory / ".DS_Store").read_bytes())

    def test_failed_validation_consumes_number_but_never_commits_package(self):
        self.packages._validate.side_effect = EnvironmentError("SERVICE_PACKAGE_SCHEMA_INVALID")
        with self.assertRaisesRegex(EnvironmentError, "SCHEMA_INVALID"):
            self.packages.prepare("brake", "v1")
        self.assertEqual("8.0.0", ReleaseContinuity(self.environment).read()["versions"]["brake"])
        self.assertEqual([], list((self.base / "catalog/services/brake/releases").iterdir()))
        self.packages._validate.side_effect = None
        self.assertEqual("9.0.0", self.packages.prepare("brake", "v1")["version"])

    def test_unavailable_catalog_never_allocates_or_writes_package(self):
        self.catalog.return_value.release_versions.side_effect = EnvironmentError("SERVICE_RELEASE_CATALOG_UNAVAILABLE")
        with self.assertRaisesRegex(EnvironmentError, "CATALOG_UNAVAILABLE"):
            self.packages.prepare("brake", "v1")
        self.assertEqual({}, ReleaseContinuity(self.environment).read()["versions"])
        self.assertFalse((self.base / "catalog").exists())

    def test_unknown_build_never_calls_cloud_or_builds(self):
        self.builder.return_value.execute.side_effect = EnvironmentError("SERVICE_BUILD_REQUIRED")
        with self.assertRaisesRegex(EnvironmentError, "BUILD_REQUIRED"):
            self.packages.prepare("brake", "v1")
        self.catalog.assert_not_called()

    def test_unexpected_file_symlink_and_modified_elf_are_rejected(self):
        path = self.base / "product/rootfs/metadata.json"
        path.write_text("must not be packaged")
        with self.assertRaisesRegex(EnvironmentError, "UNEXPECTED_FILE"):
            product_files(self.build, "brake")
        path.unlink()
        path.symlink_to(self.base / "outside")
        with self.assertRaisesRegex(EnvironmentError, "LINK_UNSUPPORTED"):
            product_files(self.build, "brake")
        path.unlink()
        path = self.base / "product/rootfs/usr/bin/brake-health-service"
        path.write_bytes(b"not the built executable")
        with self.assertRaisesRegex(EnvironmentError, "BINARY_MISMATCH"):
            product_files(self.build, "brake")

    def test_cli_shared_dispatch_has_no_vehicle_selectors_or_browser_mutation(self):
        args = build_parser().parse_args(["service", "prepare", "brake", "--profile", "v3"])
        request = request_from_arguments(args)
        self.assertEqual(("brake", "v3", "service-provider"), (request.team, request.content_profile, request.profile))
        with patch("aosedge_demo_orchestrator.service_packages.ServicePackages", return_value=self.packages):
            result = DemoOrchestrator(environment_service=self.environment).execute(request)
        self.assertEqual("COMPLETED", result.state.value)
        self.assertIn("brake/8.0.0", render_human(result))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="prepare", team="brake", content_profile="v1"), Mock())

    def test_fixed_schema_configuration_preserves_team_and_profile_scope(self):
        for team, profile, count in (("brake", "v1", 6), ("brake", "v2", 12), ("brake", "v3", 14), ("tire", "v1", 17)):
            with self.subTest(team=team, profile=profile):
                config = package_configuration(ROOT, team, profile, "42.0.0")["items"][0]
                runtime = config["configuration"]
                self.assertEqual(count, len(runtime["permissions"]["kuksa"]))
                self.assertEqual(1, runtime["instances"]["minInstances"])
                self.assertEqual("P7D", runtime["offlineTTL"])
                self.assertEqual({"kuksa", "kuksa-auth-client", team + "-runtime-inputs"}, {x["name"] for x in runtime["resources"]})
                self.assertEqual(["Server/55555/tcp", "10.0.0.1/" + ("18091" if team == "brake" else "18092") + "/tcp"], runtime["allowedConnections"])
                writes = [key for key, mode in runtime["permissions"]["kuksa"].items() if mode == "rw"]
                expected = ["Vehicle.OEM." + team.title() + "Health.Advisory.Request"] if count in (14, 17) else []
                self.assertEqual(expected, writes)
                self.assertNotIn("env", runtime)
        with self.assertRaisesRegex(EnvironmentError, "PROFILE_INVALID"):
            package_configuration(ROOT, "tire", "v3", "1.0.0")

    def test_version_bound_matches_both_native_readers_and_ledger(self):
        for value in ("01.0.0", "1.0.0-beta", "1" * 29 + ".0.0", "", None):
            with self.assertRaisesRegex(EnvironmentError, "VERSION_INVALID"):
                number(value)
        ReleaseContinuity(self.environment).remember("brake", "9" * 28 + ".0.0")
        with self.assertRaisesRegex(EnvironmentError, "VERSION_INVALID"):
            ReleaseContinuity(self.environment).reserve("brake")


class ServiceReleaseCatalogTests(unittest.TestCase):
    def test_catalog_uses_sp_service_and_versions_only_no_units_or_manifest(self):
        from test_services import FixtureCloud
        cloud = FixtureCloud()
        cloud.collections["services/"][0]["codename"] = "brake-health-service"
        result = service_cloud.inspect(cloud, dict(action="release-catalog", serviceId="brake-health-service"))
        self.assertEqual(2, len(cloud.calls))
        self.assertTrue(all("units" not in x and "manifest" not in x for x in cloud.calls))
        self.assertEqual("1.0.0", result["versions"]["value"]["items"][0]["version"])
        cloud.calls.clear()
        cloud.collections["services/"] = []
        result = service_cloud.inspect(cloud, dict(action="release-catalog", serviceId="brake-health-service"))
        self.assertEqual([], result["versions"]["value"]["items"])
        self.assertEqual(1, len(cloud.calls))

    def test_catalog_rejects_duplicate_identity_and_unavailable_pages(self):
        from test_services import FixtureCloud, OTHER
        cloud = FixtureCloud()
        cloud.collections["services/"][0]["codename"] = "brake-health-service"
        cloud.collections["services/"].append(dict(cloud.collections["services/"][0], id=OTHER))
        with self.assertRaisesRegex(service_cloud.CloudFailure, "AMBIGUOUS"):
            service_cloud.inspect(cloud, dict(action="release-catalog", serviceId="brake-health-service"))
        cloud = FixtureCloud("oem")
        with self.assertRaisesRegex(service_cloud.CloudFailure, "REQUIRES_SP"):
            service_cloud.inspect(cloud, dict(action="release-catalog", serviceId="brake-health-service"))

    def test_catalog_adapter_has_no_manifest_dependency_and_fails_closed(self):
        from test_services import FixtureCloud
        cloud = FixtureCloud()
        cloud.collections["services/"][0]["codename"] = "brake-health-service"
        response = service_cloud.inspect(cloud, dict(action="release-catalog", serviceId="brake-health-service"))
        catalog = ServiceCatalog(SimpleNamespace(root=ROOT))
        catalog._read = Mock(return_value=response)
        config = dict(cloudProfiles={"service-provider": dict(expectedRole="service provider")})
        with patch("aosedge_demo_orchestrator.services.load_configuration", return_value=config):
            result = catalog.release_versions("brake")
            self.assertEqual(["1.0.0"], result["versions"])
            bad = copy.deepcopy(response)
            bad["versions"]["value"]["coverage"]["complete"] = False
            catalog._read.return_value = bad
            with self.assertRaisesRegex(EnvironmentError, "INCOMPLETE"):
                catalog.release_versions("brake")
            bad["versions"]["state"] = "UNKNOWN"
            with self.assertRaisesRegex(EnvironmentError, "UNAVAILABLE"):
                catalog.release_versions("brake")


class OfficialServiceConfigTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("AOS_SIGNER_PYTHON"), "explicit installed signer runtime required")
    def test_all_fixed_profiles_validate_with_installed_official_schema_without_credentials(self):
        packages = ServicePackages(SimpleNamespace(root=ROOT))
        for team, profile in (("brake", "v1"), ("brake", "v2"), ("brake", "v3"), ("tire", "v1")):
            with self.subTest(team=team, profile=profile), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                (directory / "service/arm64").mkdir(parents=True)
                (directory / "config.yaml").write_text(json.dumps(package_configuration(ROOT, team, profile, "42.0.0")))
                with patch("aosedge_demo_orchestrator.service_packages.load_configuration",
                           return_value=dict(cloudPython=os.environ["AOS_SIGNER_PYTHON"])):
                    packages._validate(directory)


if __name__ == "__main__":
    unittest.main()
