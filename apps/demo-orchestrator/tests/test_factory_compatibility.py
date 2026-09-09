# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.component_runtime import (
    factory_component_support, register_factory_support, build_factory, FACTORY_REVISION, FACTORY_VERSION)
from aosedge_demo_orchestrator.environment import EnvironmentError


class FactoryCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.destination = self.root / "aosedge-sdv-demo/factory-images" / FACTORY_VERSION
        self.destination.mkdir(parents=True)
        self.image = self.destination / "main-qemuarm64.img"
        self.image.write_bytes(b"immutable fixture")
        self.image.chmod(0o444)
        self.manifest_path = self.destination / "manifest.json"
        self.manifest = dict(schemaVersion=1, state="BUILT_NOT_LIVE_QUALIFIED",
            source=dict(repository="aos-vehicle-platform", revision=FACTORY_REVISION),
            factoryImage=dict(version=FACTORY_VERSION, path=self.image.name,
                architecture="main-qemuarm64", byteLength=self.image.stat().st_size,
                format="raw", sha256="a" * 64), build=dict(offline=True))
        self.manifest_path.write_text(json.dumps(self.manifest))
        from aosedge_demo_orchestrator.components import COMPONENT
        self.support = dict(schemaVersion=1, runtimeProfile="aos-main-qemuarm64-v1",
            componentType=COMPONENT, sourceRevision=FACTORY_REVISION,
            supportedReadPaths=["Vehicle.Speed"])

    def test_declaration_uses_packaged_source_schema_not_release_version_guess(self):
        paths = tuple("Vehicle.Signal" + str(number) for number in range(23))
        with patch("aosedge_demo_orchestrator.component_runtime.runpy.run_path", return_value={
                "BASE_PATHS": paths[:7], "WHEEL_PATHS": paths[7:15], "SLIP_PATHS": paths[15:]}):
            value = factory_component_support(FACTORY_REVISION)
        self.assertEqual(list(paths), value["supportedReadPaths"])
        self.assertEqual(FACTORY_REVISION, value["sourceRevision"])
        self.assertNotIn("qualified", value)

    def test_unpinned_source_and_incomplete_schema_fail_before_build(self):
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_REVISION_MISMATCH"):
            factory_component_support("b" * 40)
        with patch("aosedge_demo_orchestrator.component_runtime.runpy.run_path", return_value={
                "BASE_PATHS": ("Vehicle.Speed",), "WHEEL_PATHS": (), "SLIP_PATHS": ()}):
            with self.assertRaisesRegex(EnvironmentError, "SCHEMA_DECLARATION_MISMATCH"):
                factory_component_support(FACTORY_REVISION)

    def test_existing_registration_preserves_image_and_qualification_then_noops(self):
        before = self.image.stat()
        result = register_factory_support(self.destination, FACTORY_VERSION, self.support)
        self.assertFalse(result["noOp"])
        self.assertFalse(result["rebuilt"])
        self.assertFalse(result["digestChecked"])
        updated = json.loads(self.manifest_path.read_text())
        self.assertEqual(self.support, updated.pop("demoCompatibility"))
        self.assertEqual(self.manifest, updated)
        after = self.image.stat()
        self.assertEqual((before.st_ino, before.st_mtime_ns, before.st_size, before.st_mode),
                         (after.st_ino, after.st_mtime_ns, after.st_size, after.st_mode))
        self.assertEqual(b"immutable fixture", self.image.read_bytes())
        manifest_time = self.manifest_path.stat().st_mtime_ns
        self.assertTrue(register_factory_support(self.destination, FACTORY_VERSION, self.support)["noOp"])
        self.assertEqual(manifest_time, self.manifest_path.stat().st_mtime_ns)

    def test_conflicting_source_or_declaration_is_not_overwritten(self):
        for changed in (dict(source=dict(repository="aos-vehicle-platform", revision="b" * 40)),
                        dict(demoCompatibility=dict(self.support, supportedReadPaths=["Vehicle.Other"]))):
            with self.subTest(changed=changed):
                text = json.dumps(dict(self.manifest, **changed))
                self.manifest_path.write_text(text)
                with self.assertRaisesRegex(EnvironmentError, "BINDING_MISMATCH|COMPATIBILITY_CONFLICT"):
                    register_factory_support(self.destination, FACTORY_VERSION, self.support)
                self.assertEqual(text, self.manifest_path.read_text())

    def test_mutable_image_or_linked_manifest_is_not_annotated(self):
        self.image.chmod(0o644)
        with self.assertRaisesRegex(EnvironmentError, "METADATA_UNAVAILABLE"):
            register_factory_support(self.destination, FACTORY_VERSION, self.support)
        self.image.chmod(0o444)
        other = self.destination / "saved.json"
        self.manifest_path.rename(other)
        self.manifest_path.symlink_to(other)
        with self.assertRaisesRegex(EnvironmentError, "MANIFEST_NOT_OWNED"):
            register_factory_support(self.destination, FACTORY_VERSION, self.support)

    def test_secondary_declaration_source_conflict_fails_before_any_write(self):
        inventory = self.root / "aosedge-sdv-demo/manifest"
        inventory.mkdir()
        secondary = dict(self.manifest, demoCompatibility=self.support,
            source=dict(repository="aos-vehicle-platform", revision="b" * 40),
            factoryImage=dict(self.manifest["factoryImage"], path=str(self.image)))
        (inventory / "retained.json").write_text(json.dumps(secondary))
        before = self.manifest_path.read_text()
        with self.assertRaisesRegex(EnvironmentError, "COMPATIBILITY_CONFLICT"):
            register_factory_support(self.destination, FACTORY_VERSION, self.support)
        self.assertEqual(before, self.manifest_path.read_text())

    def test_metadata_only_missing_artifact_never_starts_builder_or_checks_disk(self):
        with patch("aosedge_demo_orchestrator.component_runtime.ARTIFACT",
                   self.root / "missing/runtime-proofs/proof"), \
                patch("aosedge_demo_orchestrator.component_runtime.subprocess.check_output",
                      side_effect=[b"", FACTORY_REVISION.encode()]), \
                patch("aosedge_demo_orchestrator.component_runtime.factory_component_support", return_value=self.support), \
                patch("aosedge_demo_orchestrator.component_runtime.builder") as builder, \
                patch("aosedge_demo_orchestrator.component_runtime.shutil.disk_usage") as disk:
            with self.assertRaisesRegex(EnvironmentError, "METADATA_UNAVAILABLE"):
                build_factory(FACTORY_VERSION, metadata_only=True)
            builder.assert_not_called()
            disk.assert_not_called()

    def test_metadata_only_cli_and_api_share_fixed_scope(self):
        request = request_from_arguments(build_parser().parse_args(
            ["image", "build", FACTORY_VERSION, "--metadata-only"]))
        app = Mock()
        payload = dict(domain="image", action="build", image=FACTORY_VERSION, metadata_only=True)
        execute_operation(payload, app)
        self.assertEqual(request, app.execute.call_args.args[0])
        for field in (dict(metadata_only="true"), dict(path="/arbitrary"), dict(image="another")):
            with self.assertRaises(ValueError):
                execute_operation(dict(payload, **field), app)
