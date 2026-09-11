# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, atomic_json, digest
from aosedge_demo_orchestrator.service_build import ServiceBuilder

REVISION = "a" * 40


class ServiceBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.root = self.parent / "solution"
        self.root.mkdir()
        repo = self.parent / "brake-health-service"
        repo.mkdir()
        (repo / "Dockerfile").write_text("fixture only")
        self.environment = EnvironmentService(self.root, catalog=SimpleNamespace(project=self.parent / "catalog"))
        self.builder = ServiceBuilder(self.environment)
        self.builder.commands._run = Mock(side_effect=lambda args, **kwargs:
            REVISION if args[1] == "rev-parse" else "" if args[1] == "status" else "1234")
        self.builder._build = Mock(side_effect=self.export)

    def export(self, args):
        directory = Path(args[args.index("--output") + 1].split("dest=", 1)[1])
        rows = []
        for name in ("brake-health-bootstrap", "brake-health-service"):
            path = directory / "rootfs/usr/bin" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + b"\xb7\x00" + b"fixture")
            path.chmod(0o755)
            rows.append(dict(path=str(path.relative_to(directory)), sha256=digest(path)))
        atomic_json(directory / "product-build.json", dict(schemaVersion=1,
            kind="brake-health-linux-arm64-product", sourceRevision=REVISION, sourceDateEpoch=1234,
            architecture="arm64", os="linux", productTarget="BHS_BUILD_KUKSA_RUNTIME=ON",
            functionalProfile=next(value.split("=", 1)[1] for value in args if value.startswith("BHS_FUNCTIONAL_PROFILE=")),
            tests=dict(ctest="passed"), binaries=rows))

    def test_build_checks_actual_elf_and_repeat_reuses_exact_artifact(self):
        with patch("aosedge_demo_orchestrator.service_build.shutil.which", return_value="/fixed/docker"):
            result = self.builder.execute("brake")
            self.assertEqual("BUILT", result["state"])
            self.assertEqual("BUILT_NOT_LIVE_QUALIFIED", result["qualification"])
            self.assertTrue(self.builder.execute("brake")["noOp"])
        self.assertEqual(1, self.builder._build.call_count)
        self.assertFalse((self.root / ".run/demo-current/journal.json").exists())

    def test_changed_output_not_rebuilt_or_silently_reused(self):
        with patch("aosedge_demo_orchestrator.service_build.shutil.which", return_value="/fixed/docker"):
            result = self.builder.execute("brake")
            (Path(result["outputPath"]) / "rootfs/usr/bin/brake-health-service").write_bytes(b"changed")
            with self.assertRaisesRegex(EnvironmentError, "ARTIFACT_CHANGED"):
                self.builder.execute("brake")
        self.assertEqual(1, self.builder._build.call_count)

    def test_failed_product_proof_never_becomes_built(self):
        original = self.export
        def failed(args):
            original(args)
            directory = Path(args[args.index("--output") + 1].split("dest=", 1)[1])
            atomic_json(directory / "product-build.json", dict(tests=dict(ctest="failed")))
        self.builder._build.side_effect = failed
        with patch("aosedge_demo_orchestrator.service_build.shutil.which", return_value="/fixed/docker"):
            with self.assertRaisesRegex(EnvironmentError, "PROOF_INVALID"):
                self.builder.execute("brake")
        self.assertFalse((self.parent / "catalog/services/brake/builds" / REVISION / "v1/build.json").exists())

    def test_functional_profiles_have_distinct_build_outputs(self):
        with patch("aosedge_demo_orchestrator.service_build.shutil.which", return_value="/fixed/docker"):
            first = self.builder.execute("brake", "v1")
            second = self.builder.execute("brake", "v2")
        self.assertNotEqual(first["outputPath"], second["outputPath"])
        self.assertEqual(("v1", "v2"), (first["contentProfile"], second["contentProfile"]))

    def test_cli_build_is_not_a_browser_capability(self):
        request = request_from_arguments(build_parser().parse_args(["service", "build", "brake"]))
        self.assertEqual(("service", "build", "brake"), (request.domain, request.action, request.team))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="build", team="brake"), Mock())

    def test_tire_is_not_a_diagnostic_product_fallback(self):
        with self.assertRaisesRegex(EnvironmentError, "NOT_IMPLEMENTED"):
            self.builder.execute("tire")
        self.builder._build.assert_not_called()

    def test_runtime_inspection_is_explicit_test_cli_not_browser_capability(self):
        request = request_from_arguments(build_parser().parse_args(["service", "runtime-inspect", "test"]))
        self.assertEqual(("service", "runtime-inspect", "test"), (request.domain, request.action, request.target.value))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="runtime-inspect", target="test"), Mock())
