# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Tests for signed R6.1 bootstrap verification."""

from __future__ import annotations

import base64
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-r6-1-signed-bootstrap"


def load_validator():
    loader = importlib.machinery.SourceFileLoader("r6_1_signed_bootstrap", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create signed-bootstrap validator module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def archive(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as bundle:
        for name, content in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o644
            info.mtime = 0
            bundle.addfile(info, io.BytesIO(content))
    return output.getvalue()


@unittest.skipUnless(shutil.which("openssl"), "openssl is required")
class R61SignedBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.candidate = self.root / "candidate"
        self.candidate.mkdir()
        self.rootfs_name = "rootfs-full/rootfs.squashfs"
        self.rootfs = b"accepted-rootfs"
        self.config = b'{"schemaVersion":2}\n'
        rootfs_path = self.candidate / self.rootfs_name
        rootfs_path.parent.mkdir()
        rootfs_path.write_bytes(self.rootfs)
        (self.candidate / "config.yaml").write_bytes(self.config)
        (self.candidate / "candidate.json").write_text(
            json.dumps(
                {
                    "config": {
                        "sha256": hashlib.sha256(self.config).hexdigest(),
                        "size": len(self.config),
                    },
                    "rootfs": {
                        "fileName": self.rootfs_name,
                        "sha256": hashlib.sha256(self.rootfs).hexdigest(),
                        "size": len(self.rootfs),
                    },
                    "signingState": "unsigned",
                    "version": "6.1.1-maninblack.2",
                }
            ),
            encoding="utf-8",
        )
        self.key = self.root / "key.pem"
        self.cert = self.root / "cert.pem"
        self.pkcs12 = self.root / "signer.p12"
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(self.key),
                "-out",
                str(self.cert),
                "-subj",
                "/CN=r6-1-bootstrap-test",
                "-days",
                "1",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "openssl",
                "pkcs12",
                "-export",
                "-inkey",
                str(self.key),
                "-in",
                str(self.cert),
                "-out",
                str(self.pkcs12),
                "-passout",
                "pass:",
            ],
            check=True,
            capture_output=True,
        )
        self.bundle = self.root / "batch.tar.gz"
        self.write_bundle(self.rootfs)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_bundle(self, rootfs: bytes, corrupt_signature: bool = False) -> None:
        inner = archive({"config.yaml": self.config, self.rootfs_name: rootfs})
        payload = {
            "data": [
                {
                    "name": "batch.tar.gz",
                    "hash": hashlib.sha3_512(inner).hexdigest(),
                    "size": len(inner),
                },
                {
                    "name": "config.yaml",
                    "hash": hashlib.sha3_512(self.config).hexdigest(),
                    "size": len(self.config),
                },
            ]
        }
        header = {"alg": "RS256", "kid": "test", "typ": "JWT"}
        header_part = encode(json.dumps(header, separators=(",", ":")).encode())
        payload_part = encode(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        input_path = self.root / "signing-input"
        signature_path = self.root / "signature.bin"
        input_path.write_bytes(signing_input)
        subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-sign",
                str(self.key),
                "-out",
                str(signature_path),
                str(input_path),
            ],
            check=True,
            capture_output=True,
        )
        signature = signature_path.read_bytes()
        if corrupt_signature:
            signature = signature[:-1] + bytes([signature[-1] ^ 1])
        token = f"{header_part}.{payload_part}.{encode(signature)}\n".encode("ascii")
        self.bundle.write_bytes(
            archive({"batch.tar.gz": inner, "config.yaml": self.config, "package.sign": token})
        )

    def test_valid_signed_bundle_passes(self) -> None:
        evidence = VALIDATOR.validate(self.candidate, self.bundle, self.pkcs12)
        self.assertEqual("6.1.1-maninblack.2", evidence["version"])
        self.assertEqual(hashlib.sha256(self.rootfs).hexdigest(), evidence["rootfsSha256"])

    def test_changed_embedded_rootfs_is_rejected(self) -> None:
        self.write_bundle(b"changed-rootfs")
        with self.assertRaisesRegex(VALIDATOR.SignedBundleError, "differs"):
            VALIDATOR.validate(self.candidate, self.bundle, self.pkcs12)

    def test_invalid_rs256_signature_is_rejected(self) -> None:
        self.write_bundle(self.rootfs, corrupt_signature=True)
        with self.assertRaisesRegex(VALIDATOR.SignedBundleError, "RS256"):
            VALIDATOR.validate(self.candidate, self.bundle, self.pkcs12)


if __name__ == "__main__":
    unittest.main()
