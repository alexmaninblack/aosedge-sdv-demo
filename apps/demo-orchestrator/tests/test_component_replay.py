# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator.component_build import PROFILE_BASES, PACKAGE, encoded, pack, replay
from aosedge_demo_orchestrator.components import ComponentService, archive_files, sha
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import main


def inputs(profile):
    version, digest, module, count = PROFILE_BASES[profile]
    paths = ["Vehicle.Signal" + str(i) for i in range(count)]
    caps = ["CAP_" + profile]
    capability = encoded(dict(semanticVersion=version, readPaths=paths, capabilities=caps,
        advisoryEndpoints=[{"id": "existing-advisory"}] if profile == "v3" else []))
    files = {
        "component.json": encoded(dict(version=version, architecture="arm64", entrypoint="bin/vehicle-data-provider",
            configuration="config/provider.json", runtimeInterface=1)),
        "config/capability-manifest.json": capability,
        "config/provider.json": encoded(dict(semanticVersion=version, capabilityManifestSha256=sha(capability))),
        PACKAGE + "vdp_release_profile.py": ("from .releases." + module + " import *\n").encode(),
        PACKAGE + "releases/" + module + ".py": ('VERSION = "' + version + '"\nMANIFEST_SHA256 = "'
            + sha(capability) + '"\nSIGNALS = ("unchanged",)\n').encode(),
        PACKAGE + "__init__.py": ('__version__ = "' + version + '"\n').encode(),
        "provenance/provenance.json": encoded(dict(semanticVersion=version, sourceRevision="frozen")),
        "sbom/spdx.json": encoded(dict(name="original", documentNamespace="https://example.test/" + version + "/source",
            packages=[{"name": "retained-native-dependency", "versionInfo": "1.2.3"}])),
        "bin/vehicle-data-provider": b"frozen-launcher",
        PACKAGE + "runtime.py": b"VALUE = 'unchanged runtime'\n",
        "lib/native.so": b"retained ARM64 binary bytes",
    }
    contract = {"componentVersions": [dict(id="VDP_" + profile.upper(), readPaths=paths, capabilities=caps)]}
    return files, digest, contract


class ReplayTests(unittest.TestCase):
    factory = {"version": "6.1.1-maninblack.29", "sha256": "immutable-factory"}

    def test_content_profile_is_independent_of_release_major_and_all_metadata_agrees(self):
        for version, profile in (("4.0.0", "v1"), ("5.0.0", "v2"), ("6.0.0", "v3"), ("10.1.0", "v2")):
            with self.subTest(version=version, profile=profile), tempfile.TemporaryDirectory() as temporary:
                baseline, digest, contract = inputs(profile)
                first, record = replay(version, profile, baseline, digest, contract, self.factory)
                second, repeated = replay(version, profile, baseline, digest, contract, self.factory)
                self.assertEqual(pack(first), pack(second))
                self.assertEqual(record, repeated)
                payload = archive_files(first["vehicle-data-platform/vdp-" + version + "-arm64.tar.gz"])
                self.assertEqual(set(baseline), set(payload))
                self.assertEqual(PROFILE_BASES[profile][3], record["readPathCount"])
                for path in ("bin/vehicle-data-provider", "lib/native.so", PACKAGE + "runtime.py", PACKAGE + "vdp_release_profile.py"):
                    self.assertEqual(baseline[path], payload[path])
                old_cap = json.loads(baseline["config/capability-manifest.json"])
                new_cap = json.loads(payload["config/capability-manifest.json"])
                self.assertEqual(dict(old_cap, semanticVersion=version), new_cap)
                provider = json.loads(payload["config/provider.json"])
                self.assertEqual(version, provider["semanticVersion"])
                self.assertEqual(sha(payload["config/capability-manifest.json"]), provider["capabilityManifestSha256"])
                self.assertEqual(json.loads(baseline["sbom/spdx.json"])["packages"], json.loads(payload["sbom/spdx.json"])["packages"])
                service = ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=Path(temporary))))
                destination = service._directory(version)
                destination.mkdir(parents=True)
                (destination / ("aosedge-vdp-component-" + version + "-linux-arm64.unsigned.tar.gz")).write_bytes(pack(first))
                result = service.inspect(version)
                self.assertEqual([], result["problems"])
                self.assertEqual(profile, result["contentProfile"])
                self.assertEqual(version, result["outerVersion"])
                self.assertEqual(version, result["innerVersion"])

    def test_changed_base_wrong_profile_and_old_release_are_rejected(self):
        files, digest, contract = inputs("v1")
        for version, profile, base_sha in (("4.0.0", "v1", "changed"), ("4.0.0", "v4", digest), ("3.0.0", "v1", digest)):
            with self.subTest(version=version, profile=profile), self.assertRaises(EnvironmentError):
                replay(version, profile, files, base_sha, contract, self.factory)

    def test_profile_constant_and_selector_cannot_silently_mismatch(self):
        files, digest, contract = inputs("v1")
        for path, value in ((PACKAGE + "releases/v1_0_16.py", b'VERSION = "wrong"\n'),
                            (PACKAGE + "vdp_release_profile.py", b"from .releases.v3 import *\n")):
            with self.subTest(path=path), self.assertRaises(EnvironmentError):
                replay("4.0.0", "v1", dict(files, **{path: value}), digest, contract, self.factory)

    def test_cli_and_api_prepare_share_explicit_profile_and_reject_other_overrides(self):
        with patch.object(ComponentService, "prepare", return_value={}) as prepare:
            result = execute_operation(dict(domain="component", action="prepare", component_version="4.0.0", content_profile="v1"))
            self.assertEqual("COMPLETED", result["state"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["component", "prepare", "4.0.0", "--profile", "v1"]))
            self.assertEqual(2, prepare.call_count)
            prepare.assert_called_with("4.0.0", "v1")
        for field in ("path", "target", "credential", "source_version"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="component", action="prepare", component_version="4.0.0", content_profile="v1", **{field: "x"}))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="component", action="upload", component_version="4.0.0", content_profile="v1"))


if __name__ == "__main__":
    unittest.main()
