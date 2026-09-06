# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import main
from aosedge_demo_orchestrator.components import ComponentService, COMPONENT, MEDIA_TYPE, archive_files, sha
from aosedge_demo_orchestrator.environment import EnvironmentError


def tar(files):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        for name, value in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(value)
            archive.addfile(entry, io.BytesIO(value))
    return data.getvalue()


def encode(value):
    return json.dumps(value).encode()


def bundle(version="2.0.0", signed=True, inner_version=None, media=MEDIA_TYPE):
    capability = encode(dict(semanticVersion=version, readPaths=["Vehicle.Speed"], advisoryEndpoints=[]))
    layer = tar({
        "component.json": encode(dict(version=inner_version or version, architecture="arm64",
            entrypoint="bin/vehicle-data-provider", configuration="config/provider.json", runtimeInterface=1)),
        "config/provider.json": encode(dict(semanticVersion=version, capabilityManifestSha256=sha(capability))),
        "config/capability-manifest.json": capability,
        "bin/vehicle-data-provider": b"fixture-not-an-executable",
    })
    config = encode(dict(schemaVersion=2, items=[dict(version=version,
        identity=dict(type="component", codename=COMPONENT), sourceFolder="vehicle-data-platform",
        images=[dict(path="vdp.tar.gz", mediaType=media, archInfo=dict(architecture="arm64"))],
        configuration=dict(runtimes=[dict(codename=COMPONENT, type="runtime")]))]))
    inner = tar({"config.yaml": config, "vehicle-data-platform/vdp.tar.gz": layer})
    return tar({"config.yaml": config, "batch.tar.gz": inner, "package.sign": b"NOT_A_REAL_SIGNATURE"}) if signed else inner


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = SimpleNamespace(catalog=SimpleNamespace(project=self.root), _writer=contextlib.nullcontext)
        self.service = ComponentService(self.environment)

    def put(self, data=None, signed=True):
        directory = self.service.root / "2.0.0"
        directory.mkdir(parents=True)
        name = "vdp-2.0.0-deployment-bundle.tar.gz" if signed else "aosedge-vdp-component-2.0.0-linux-arm64.unsigned.tar.gz"
        target = directory / name
        target.write_bytes(data or bundle(signed=signed))
        return target

    def test_inspect_signed_is_read_only_and_not_signature_proof(self):
        path = self.put()
        before = path.read_bytes()
        result = self.service.inspect("2.0.0")
        self.assertEqual([], result["problems"])
        self.assertEqual("NOT_PERFORMED", result["signatureVerification"])
        self.assertNotIn("NOT_A_REAL_SIGNATURE", json.dumps(result))
        self.assertEqual(before, path.read_bytes())
        self.assertFalse((path.parent / "unpacked").exists())

    def test_unsigned_and_empty_catalog(self):
        self.assertEqual({"components": []}, self.service.list())
        self.put(signed=False)
        self.assertFalse(self.service.inspect("2.0.0")["signedEnvelope"])

    def test_mismatched_versions_and_media_are_visible_not_successful_unpack(self):
        self.put(bundle(inner_version="1.0.16", media="old"))
        result = self.service.inspect("2.0.0")
        self.assertIn("COMPONENT_VERSION_MISMATCH", result["problems"])
        self.assertIn("COMPONENT_MEDIA_TYPE_MISMATCH", result["problems"])
        with self.assertRaisesRegex(EnvironmentError, "PACKAGING_INVALID"):
            self.service.unpack("2.0.0")

    def test_unpack_is_scoped_nonexecutable_and_refuses_overwrite(self):
        path = self.put()
        result = self.service.unpack("2.0.0")
        destination = Path(result["destination"])
        self.assertEqual(path.parent / "unpacked", destination)
        self.assertEqual(0o600, (destination / "bin/vehicle-data-provider").stat().st_mode & 0o777)
        with self.assertRaisesRegex(EnvironmentError, "DESTINATION_EXISTS"):
            self.service.unpack("2.0.0")

    def test_catalog_selectors_and_links_rejected(self):
        for version in ("../other", "2.0.0/../../", "latest", None, "01.0.0"):
            with self.assertRaises(EnvironmentError):
                self.service.inspect(version)
        path = self.put()
        path.unlink()
        path.symlink_to(self.root / "outside")
        with self.assertRaises(EnvironmentError):
            self.service.inspect("2.0.0")

    def test_tar_traversal_file_parent_and_symlink_rejected(self):
        for files in ({"../escape": b"bad"}, {"/escape": b"bad"}, {"a": b"bad", "a/b": b"bad"}):
            with self.assertRaises(EnvironmentError):
                archive_files(tar(files))
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w") as archive:
            entry = tarfile.TarInfo("link")
            entry.type = tarfile.SYMTYPE
            entry.linkname = "outside"
            archive.addfile(entry)
        with self.assertRaises(EnvironmentError):
            archive_files(data.getvalue())

    def test_tar_duplicate_and_expansion_limits(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w") as archive:
            for _ in range(2):
                archive.addfile(tarfile.TarInfo("same"), io.BytesIO())
        with self.assertRaisesRegex(EnvironmentError, "DUPLICATE"):
            archive_files(data.getvalue())
        with patch("aosedge_demo_orchestrator.components.MAX_EXPANDED", 1):
            with self.assertRaisesRegex(EnvironmentError, "EXPANSION_LIMIT"):
                archive_files(tar({"a": b"too large"}))

    def test_cli_and_api_same_core_and_path_credential_rejection(self):
        with patch.object(ComponentService, "inspect", return_value={"problems": []}) as operation:
            result = execute_operation(dict(domain="component", action="inspect", component_version="2.0.0"))
            self.assertEqual("OBSERVED", result["state"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, main(["--output", "json", "component", "inspect", "2.0.0"]))
            self.assertEqual(2, operation.call_count)
        for field in ("path", "credential", "url", "target", "force"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="component", action="unpack", component_version="2.0.0", **{field: "x"}))


if __name__ == "__main__":
    unittest.main()
