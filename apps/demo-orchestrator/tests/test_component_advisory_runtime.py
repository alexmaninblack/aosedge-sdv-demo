# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline reviewed V3 composition; no Factory, VM, credentials or Cloud."""

import ast
import contextlib
import copy
import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import component_build as build
from aosedge_demo_orchestrator.component_sources import UNSIGNED_SHA
from aosedge_demo_orchestrator.components import ComponentService, archive_files, sha
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, FACTORY, MANIFEST
from test_component_replay import inputs
from aosedge_demo_orchestrator import source_guest


class AdvisoryObservationTests(unittest.TestCase):
    def test_new_configuration_never_claims_application_success(self):
        self.assertEqual("NOT_APPLICABLE", source_guest.advisory_configuration_observation({}))
        capability = dict(advisoryEndpoints=["brake", "tire"])
        self.assertEqual("DEFERRED", source_guest.advisory_configuration_observation(capability))
        capability["contracts"] = dict(typedQmAdvisory=build.ADVISORY_CONTRACT)
        self.assertEqual("CONFIGURED_NOT_APPLICATION_PROOF", source_guest.advisory_configuration_observation(capability))
        capability["contracts"] = dict(typedQmAdvisory=dict(build.ADVISORY_CONTRACT, sha256="0" * 64))
        self.assertEqual("DEFERRED", source_guest.advisory_configuration_observation(capability))
        for contract in build.ADVISORY_RUNTIME_CONTRACT_HISTORY.values():
            capability["contracts"] = dict(typedQmAdvisory=contract)
            self.assertEqual("CONFIGURED_NOT_APPLICATION_PROOF", source_guest.advisory_configuration_observation(capability))

    def test_log_projection_preserves_only_fixed_endpoints_and_results(self):
        message = "INFO QM_ADVISORY endpoint=Vehicle.OEM.TireHealth.Advisory.Request result=VISS_SET_ACCEPTED"
        raw = "\n".join(json.dumps(dict(MESSAGE=value, __REALTIME_TIMESTAMP="123")) for value in (
            message, message + " token=secret", "QM_ADVISORY endpoint=secret result=INVALID_VALUE",
            "QM_ADVISORY endpoint=transport result=UNKNOWN_SECRET", [1, 2, 3]))
        self.assertEqual([dict(time="123", endpoint="Vehicle.OEM.TireHealth.Advisory.Request", result="VISS_SET_ACCEPTED")],
            source_guest.advisory_log_observation(raw))
        self.assertEqual(40, len(source_guest.advisory_log_observation("\n".join(
            json.dumps(dict(MESSAGE=message)) for _ in range(50)))))
        readiness = message.replace(".Request", ".Availability")
        self.assertEqual("Vehicle.OEM.TireHealth.Advisory.Availability",
            source_guest.advisory_log_observation(json.dumps(dict(MESSAGE=readiness)))[0]["endpoint"])
        self.assertEqual([], source_guest.advisory_log_observation(json.dumps(dict(MESSAGE=readiness + " secret"))))

    def test_readiness_transition_projection_is_fixed_and_not_an_application_ack(self):
        endpoint = "Vehicle.OEM.BrakeHealth.Advisory.Availability"
        for state in ("READY", "NOT_READY"):
            message = "QM_ADVISORY endpoint=" + endpoint + ":readiness result=" + state
            self.assertEqual([dict(time="123", endpoint=endpoint, result="READINESS_" + state)],
                source_guest.advisory_log_observation(json.dumps(dict(MESSAGE=message, __REALTIME_TIMESTAMP="123"))))
            for invalid in (message + " token=secret", message.replace(":readiness", ":secret"),
                            message.replace(".Availability", ".Request"), message.replace(state, "SECRET")):
                self.assertEqual([], source_guest.advisory_log_observation(json.dumps(dict(MESSAGE=invalid))))


class AdvisoryRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline, self.digest, self.compatibility = inputs("v3")
        capability = json.loads(self.baseline["config/capability-manifest.json"])
        capability["contracts"] = {"typedQmAdvisory": {"contractId": build.ADVISORY_CONTRACT["contractId"],
            "contractVersion": "1.0.2", "sha256": "f" * 64}}
        old_manifest = sha(self.baseline["config/capability-manifest.json"])
        self.baseline["config/capability-manifest.json"] = build.encoded(capability)
        new_manifest = sha(self.baseline["config/capability-manifest.json"])
        self.baseline["config/provider.json"] = build.encoded(dict(semanticVersion="3.0.0", capabilityManifestSha256=new_manifest))
        profile = build.PACKAGE + "releases/v3.py"
        self.baseline[profile] = build.replace_constant(self.baseline[profile], "MANIFEST_SHA256", old_manifest, new_manifest)
        self.baseline[build.PACKAGE + "advisory.py"] = b"POLICY = 'frozen legacy policy'\n"
        self.baseline[build.PACKAGE + "manifest.py"] = b"POLICY = 'frozen legacy manifest'\n"
        self.original = copy.deepcopy(self.baseline)
        self.contract = (Path(__file__).resolve().parents[3] /
            "contracts/qm-advisory-profile/qm-advisory-profile.v1.json").read_bytes()
        self.modules = {
            "runtime.py": b"from .advisory_transport import Transport\n",
            "bridge.py": b"REPEATED_FRAME_IS_NOT_A_NEW_MEASUREMENT = True\n",
            "advisory.py": b"POLICY = 'reviewed profile independent of release'\n",
            "advisory_transport.py": b"class Transport: pass\n",
            "manifest.py": b"CURRENT_ADVISORY_CONTRACT = " + build.encoded(build.ADVISORY_CONTRACT) + b"\n",
        }
        self.pin = {"revision": "a" * 40, "tree": "b" * 40,
                    "modules": {name: sha(raw) for name, raw in self.modules.items()}}
        self.factory = {"version": "6.1.1-maninblack.33", "sha256": "unchanged-factory"}
        self.environment = SimpleNamespace(root=self.root,
            catalog=SimpleNamespace(project=self.root / "artifacts"), _writer=contextlib.nullcontext)
        self.service = ComponentService(self.environment)
        self.service.root.mkdir(parents=True)
        self.pin_patch = patch.object(build, "ADVISORY_RUNTIME_PIN", self.pin)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.release_patch = patch.object(build, "ADVISORY_RUNTIME_RELEASE_ENABLED", True)
        self.release_patch.start()
        self.addCleanup(self.release_patch.stop)

    def git(self, args, **kwargs):
        self.assertEqual(self.root, kwargs["cwd"])
        if args[:2] == ["git", "rev-parse"]:
            self.assertEqual(self.pin["revision"] + "^{tree}", args[2])
            return SimpleNamespace(stdout=self.pin["tree"] + "\n")
        self.assertEqual(["git", "show"], args[:2])
        prefix = self.pin["revision"] + ":" + build.SOURCE_PACKAGE
        self.assertTrue(args[2].startswith(prefix))
        return SimpleNamespace(stdout=self.modules[args[2].removeprefix(prefix)])

    def compose(self):
        with patch.object(build.subprocess, "run", side_effect=self.git):
            return build.compose_advisory_runtime("69.0.0", self.baseline, self.digest, self.root,
                self.compatibility, self.factory, self.contract, unsigned_source_sha=UNSIGNED_SHA["3.0.0"])

    def payload(self, transport):
        return archive_files(transport["vehicle-data-platform/vdp-69.0.0-arm64.tar.gz"])

    def put(self, payload):
        destination = self.service._directory("69.0.0")
        destination.mkdir(exist_ok=True)
        transport, _ = build._transport(payload, "69.0.0", "fixture", {})
        path = destination / "aosedge-vdp-component-69.0.0-linux-arm64.unsigned.tar.gz"
        path.write_bytes(build.pack(transport))
        return path

    def test_pending_pin_blocks_before_cloud_or_version_reservation(self):
        with patch.object(build, "ADVISORY_RUNTIME_PIN", None), \
                patch.object(self.service, "_worker") as worker:
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_CHECKPOINT_REQUIRED"):
                self.service.prepare(None, "v3")
        worker.assert_not_called()
        self.assertFalse((self.root / ".local/release-continuity.json").exists())
        self.assertEqual([], list(self.service.root.iterdir()))

    def test_pin_rejects_extra_module_and_nonimmutable_reference(self):
        for pin in (dict(self.pin, revision="HEAD"), dict(self.pin, modules=dict(self.pin["modules"], **{"unreviewed.py": "c" * 64})),
                    dict(self.pin, modules={key: value for key, value in self.pin["modules"].items() if key != "bridge.py"})):
            with self.subTest(pin=pin), patch.object(build, "ADVISORY_RUNTIME_PIN", pin):
                with self.assertRaisesRegex(EnvironmentError, "SOURCE_PIN_INVALID"):
                    build.advisory_runtime_pin()

    def test_deterministic_reviewed_source_and_unchanged_frozen_dependencies(self):
        first, record = self.compose()
        second, repeated = self.compose()
        self.assertEqual(build.pack(first), build.pack(second))
        self.assertEqual(record, repeated)
        self.assertEqual(self.original, self.baseline)
        payload = self.payload(first)
        for name in ("lib/native.so", "bin/vehicle-data-provider", build.PACKAGE + "vdp_release_profile.py"):
            self.assertEqual(self.baseline[name], payload[name])
        for name, raw in self.modules.items():
            self.assertEqual(raw, payload[build.PACKAGE + name])
        self.assertNotEqual(self.baseline[build.PACKAGE + "runtime.py"], payload[build.PACKAGE + "runtime.py"])
        self.assertIn(build.PACKAGE + "advisory_transport.py", record["changedPayloadFiles"])
        self.assertEqual(build.ADVISORY_RUNTIME_BUILD_TYPE, record["buildType"])
        self.assertEqual("ENABLED", record["advisoryRuntimeReleaseGate"])
        self.assertEqual("IMPLEMENTED_NOT_LIVE_QUALIFIED", record["advisory"])
        self.assertNotEqual("TELEMETRY_ONLY_ADVISORY_DEFERRED", record["qualificationScope"])
        capability = json.loads(payload["config/capability-manifest.json"])
        self.assertEqual(build.ADVISORY_CONTRACT, capability["contracts"]["typedQmAdvisory"])
        self.assertEqual("69.0.0", capability["semanticVersion"])
        self.assertEqual(sha(payload["config/capability-manifest.json"]),
                         json.loads(payload["config/provider.json"])["capabilityManifestSha256"])
        profile = {node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(payload[build.PACKAGE + "releases/v3.py"]).body if isinstance(node, ast.Assign)}
        self.assertEqual(build.ADVISORY_CONTRACT, profile["ADVISORY_CONTRACT"])
        self.assertEqual(record["capabilityManifestSha256"], profile["MANIFEST_SHA256"])
        self.put(payload)
        self.assertEqual([], self.service.inspect("69.0.0")["problems"])

    def test_contract_or_source_digest_change_cannot_be_relabelled(self):
        with patch.object(build.subprocess, "run", side_effect=self.git):
            with self.assertRaisesRegex(EnvironmentError, "CONTRACT_DIGEST_MISMATCH"):
                build.compose_advisory_runtime("69.0.0", self.baseline, self.digest, self.root,
                    self.compatibility, self.factory, self.contract + b" ", unsigned_source_sha=UNSIGNED_SHA["3.0.0"])
        self.modules["runtime.py"] += b"CHANGED = True\n"
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_DIGEST_MISMATCH"):
            self.compose()

    def test_previous_reviewed_release_remains_inspectable_without_accepting_unknown_pins(self):
        transport, _ = self.compose()
        payload = self.payload(transport)
        provenance = json.loads(payload["provenance/provenance.json"])
        previous = dict(self.pin, revision="c" * 40, tree="d" * 40,
            modules={key: value for key, value in self.pin["modules"].items() if key != "bridge.py"})
        provenance.update(sourceRevision=previous["revision"], sourceTree=previous["tree"],
            runtimeSourceModules=previous["modules"])
        with patch.object(build, "ADVISORY_RUNTIME_HISTORY", (previous,)), patch.object(
                build, "ADVISORY_RUNTIME_CONTRACT_HISTORY", {previous["revision"]: build.ADVISORY_CONTRACT}):
            build.validate_advisory_payload(payload, provenance)
            provenance["sourceTree"] = "e" * 40
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_PROVENANCE_MISMATCH"):
                build.validate_advisory_payload(payload, provenance)
        provenance["sourceRevision"] = "f" * 40
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_PROVENANCE_MISMATCH"):
            build.validate_advisory_payload(payload, provenance)

    def test_retained_source_cannot_claim_new_contract_or_unregistered_pair(self):
        transport, _ = self.compose()
        payload = self.payload(transport)
        provenance = json.loads(payload["provenance/provenance.json"])
        previous = dict(self.pin, revision="c" * 40)
        provenance["sourceRevision"] = previous["revision"]
        old_contract = dict(build.ADVISORY_CONTRACT, contractVersion="1.1.0", sha256="f" * 64)
        with patch.object(build, "ADVISORY_RUNTIME_HISTORY", (previous,)), patch.object(
                build, "ADVISORY_RUNTIME_CONTRACT_HISTORY", {previous["revision"]: old_contract}):
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_PROVENANCE_MISMATCH"):
                build.validate_advisory_payload(payload, provenance)
            provenance["typedQmAdvisory"] = old_contract
            with self.assertRaisesRegex(EnvironmentError, "CAPABILITY_CONTRACT_MISMATCH"):
                build.validate_advisory_payload(payload, provenance)
        with patch.object(build, "ADVISORY_RUNTIME_HISTORY", (previous,)), patch.object(
                build, "ADVISORY_RUNTIME_CONTRACT_HISTORY", {}):
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_PROVENANCE_MISMATCH"):
                build.validate_advisory_payload(payload, provenance)

    def test_missing_git_object_is_fail_closed(self):
        with patch.object(build.subprocess, "run", side_effect=subprocess.CalledProcessError(128, "git")):
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_UNAVAILABLE"):
                build.advisory_source(self.root)

    def test_source_tree_and_runtime_contract_pin_are_independent_gates(self):
        with patch.object(build.subprocess, "run", return_value=SimpleNamespace(stdout="c" * 40)):
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_TREE_MISMATCH"):
                build.advisory_source(self.root)
        self.modules["manifest.py"] = b"CURRENT_ADVISORY_CONTRACT = {}\n"
        self.pin["modules"]["manifest.py"] = sha(self.modules["manifest.py"])
        with self.assertRaisesRegex(EnvironmentError, "RUNTIME_CONTRACT_MISMATCH"):
            self.compose()

    def test_explicit_new_profile_pin_cannot_be_omitted_or_disguised_in_provenance(self):
        transport, _ = self.compose()
        payload = self.payload(transport)
        profile = build.PACKAGE + "releases/v3.py"
        payload[profile] = payload[profile].split(b"\nADVISORY_CONTRACT = ", 1)[0] + b"\n"
        provenance = json.loads(payload["provenance/provenance.json"])
        provenance["buildInputs"] = [dict(path=name, sha256=sha(raw)) for name, raw in sorted(payload.items())
            if not name.startswith(("provenance/", "sbom/"))]
        payload["provenance/provenance.json"] = build.encoded(provenance)
        self.put(payload)
        self.assertIn("COMPONENT_ADVISORY_PROFILE_CONTRACT_MISMATCH", self.service.inspect("69.0.0")["problems"])

    def test_inspection_rejects_changed_runtime_even_with_self_consistent_hashes(self):
        transport, _ = self.compose()
        payload = self.payload(transport)
        payload[build.PACKAGE + "runtime.py"] += b"ALTERED = True\n"
        provenance = json.loads(payload["provenance/provenance.json"])
        provenance["runtimeSourceModules"]["runtime.py"] = sha(payload[build.PACKAGE + "runtime.py"])
        provenance["buildInputs"] = [dict(path=name, sha256=sha(raw)) for name, raw in sorted(payload.items())
            if not name.startswith(("provenance/", "sbom/"))]
        payload["provenance/provenance.json"] = build.encoded(provenance)
        self.put(payload)
        self.assertIn("COMPONENT_ADVISORY_SOURCE_PROVENANCE_MISMATCH", self.service.inspect("69.0.0")["problems"])

    def test_inspection_rejects_new_runtime_claiming_frozen_replay(self):
        transport, _ = self.compose()
        payload = self.payload(transport)
        provenance = json.loads(payload["provenance/provenance.json"])
        provenance["buildType"] = "democtl-profile-replay-v1"
        payload["provenance/provenance.json"] = build.encoded(provenance)
        self.put(payload)
        self.assertIn("COMPONENT_ADVISORY_SOURCE_PROVENANCE_MISMATCH", self.service.inspect("69.0.0")["problems"])

    def test_prepare_v3_uses_existing_operation_and_packs_once_per_layer(self):
        compat = self.root / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json"
        compat.parent.mkdir(parents=True)
        compat.write_bytes(build.encoded(self.compatibility))
        advisory = self.root / "contracts/qm-advisory-profile/qm-advisory-profile.v1.json"
        advisory.parent.mkdir(parents=True)
        advisory.write_bytes(self.contract)
        (self.root / JOURNAL).parent.mkdir(parents=True)
        (self.root / JOURNAL).write_bytes(build.encoded(dict(factory=dict(self.factory,
            format="raw", path=FACTORY["raw"], manifestPath=MANIFEST))))
        inspected = dict(source={"legacyArchiveSha256": self.digest, "unsignedSha256": UNSIGNED_SHA["3.0.0"]},
                         sourceIntegrity="VERIFIED_PINNED_DIGESTS")
        with patch("aosedge_demo_orchestrator.component_sources.source", return_value=(inspected, self.baseline)) as source, \
                patch.object(build, "advisory_source", return_value={build.PACKAGE + name: raw for name, raw in self.modules.items()}), \
                patch.object(self.service, "_worker", side_effect=AssertionError("No Cloud for explicit version")), \
                patch.object(build, "compose_advisory_runtime", wraps=build.compose_advisory_runtime) as compose, \
                patch.object(build, "pack", wraps=build.pack) as compress:
            record = self.service.prepare("69.0.0", "v3")
        source.assert_called_once_with(self.service, "3.0.0", materialize=True)
        self.assertEqual(1, compose.call_count)
        self.assertEqual(2, compress.call_count)
        self.assertEqual(build.ADVISORY_RUNTIME_BUILD_TYPE, record["buildType"])
        self.assertEqual("ENABLED", record["advisoryRuntimeReleaseGate"])
        self.assertEqual([], self.service.inspect("69.0.0")["problems"])


class ReviewedSourceIntegrationTests(unittest.TestCase):
    def test_real_pinned_source_and_frozen_dependency_payload_import_with_new_contract(self):
        """Local optional proof only: never reserve, sign, publish or access a VM."""
        project = Path.home() / "OpenAI/demo-artifacts/aosedge-sdv-demo"
        repository = Path(__file__).resolve().parents[4] / "aos-vehicle-platform"
        if not (project / "components/vehicle-data-provider/.source-profiles/3.0.0/package.tar.gz").is_file() or not repository.is_dir():
            self.skipTest("Reviewed local Platform checkout and frozen unsigned V3 dependency source unavailable")
        from aosedge_demo_orchestrator.component_sources import source
        service = ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=project)))
        inspected, baseline = source(service, "3.0.0", materialize=False)
        solution = Path(__file__).resolve().parents[3]
        contract = json.loads((solution / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json").read_bytes())
        advisory = (solution / "contracts/qm-advisory-profile/qm-advisory-profile.v1.json").read_bytes()
        before = {name: sha(raw) for name, raw in baseline.items()}
        transport, record = build.compose_advisory_runtime("69.0.0", baseline,
            inspected["source"]["legacyArchiveSha256"], repository, contract,
            {"version": "offline-test-only", "sha256": "no-live-image"}, advisory,
            unsigned_source_sha=inspected["source"]["unsignedSha256"])
        self.assertEqual(before, {name: sha(raw) for name, raw in baseline.items()})
        self.assertEqual(build.ADVISORY_RUNTIME_PIN["revision"], record["sourceRevision"])
        self.assertTrue(build.ADVISORY_RUNTIME_RELEASE_ENABLED)
        self.assertEqual("ENABLED", record["advisoryRuntimeReleaseGate"])
        payload = archive_files(transport["vehicle-data-platform/vdp-69.0.0-arm64.tar.gz"])
        package_name = "advisory_packaging_proof"
        self.assertNotIn(package_name, sys.modules)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, raw in payload.items():
                if name.startswith((build.PACKAGE, "config/")):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
            package = root / build.PACKAGE
            spec = importlib.util.spec_from_file_location(package_name, package / "__init__.py",
                submodule_search_locations=[str(package)])
            module = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = module
            try:
                spec.loader.exec_module(module)
                runtime = importlib.import_module(package_name + ".runtime")
                advisory_transport = importlib.import_module(package_name + ".advisory_transport")
                configuration = runtime.load_payload_configuration(root / "config/provider.json")
                self.assertTrue(configuration.advisory_enabled)
                self.assertEqual("69.0.0", configuration.semantic_version)
                self.assertEqual(23, len(configuration.signals))
                self.assertTrue(callable(advisory_transport.AdvisoryTransport))
                bridge = importlib.import_module(package_name + ".bridge")
                self.assertIn("repeated", bridge.Snapshot.__dataclass_fields__)
                for test_only in (True, False):
                    selected = runtime.Configuration(configuration,
                        runtime.VissConfiguration("wss://offline.invalid", Path("/not-read"), "offline.invalid",
                            server_authenticated_test_only=test_only),
                        runtime.KuksaConfiguration("127.0.0.1", 55555, Path("/not-read"), "127.0.0.1", Path("/not-read")))
                    connect = Mock(side_effect=AssertionError("No live connection allowed"))
                    with self.subTest(test_only=test_only), \
                            patch.object(runtime, "_readiness_tracker", return_value=None), \
                            patch.object(runtime.ssl, "create_default_context"), \
                            patch.object(runtime, "KuksaSink") as sink:
                        with self.assertRaisesRegex(ValueError, "requires selected-Unit mutual TLS"):
                            runtime.run(selected, threading.Event(), threading.Event(), connect_factory=connect)
                    connect.assert_not_called()
                    sink.return_value.publish.assert_not_called()
            finally:
                for name in list(sys.modules):
                    if name == package_name or name.startswith(package_name + "."):
                        del sys.modules[name]


if __name__ == "__main__":
    unittest.main()
