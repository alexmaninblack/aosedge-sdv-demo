# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static safety tests for the isolated R6.1 builder lifecycle."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6-1-builder"


def load_builder():
    loader = importlib.machinery.SourceFileLoader("r6_1_builder", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create builder module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


BUILDER = load_builder()


class R61BuilderTests(unittest.TestCase):
    def test_download_url_is_https_and_allowlisted(self) -> None:
        BUILDER.validate_download_url(BUILDER.IMAGE_URL)
        with self.assertRaisesRegex(BUILDER.BuilderError, "unexpected URL"):
            BUILDER.validate_download_url("https://example.com/builder.img")
        with self.assertRaisesRegex(BUILDER.BuilderError, "unexpected URL"):
            BUILDER.validate_download_url(
                "http://cloud-images.ubuntu.com/insecure.img"
            )

    def test_cloud_init_has_no_password_or_private_key(self) -> None:
        public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest r61-test"
        files = BUILDER.cloud_init_files(public_key)
        rendered = "\n".join(files.values())
        self.assertIn(public_key, rendered)
        self.assertIn("ssh_pwauth: false", rendered)
        self.assertIn("lock_passwd: true", rendered)
        self.assertNotIn("PRIVATE KEY", rendered)
        self.assertNotIn("aos-user-", rendered)
        self.assertIn(f"DNS=10.0.2.2:{BUILDER.DNS_PORT}", rendered)

    def test_qemu_network_is_loopback_only(self) -> None:
        original = BUILDER.command_path
        try:
            BUILDER.command_path = lambda name: f"/qualified/{name}"
            command = BUILDER.qemu_command(daemonize=True)
        finally:
            BUILDER.command_path = original
        rendered = " ".join(command)
        self.assertIn(
            f"hostfwd=tcp:127.0.0.1:{BUILDER.SSH_PORT}-:22", rendered
        )
        self.assertNotIn("0.0.0.0", rendered)
        self.assertNotIn("tap", rendered)
        self.assertIn("-daemonize", command)

    def test_builder_identity_is_explicitly_forbidden(self) -> None:
        files = BUILDER.cloud_init_files(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest r61-test"
        )
        self.assertIn("unit_identity=forbidden", files["user-data"])
        self.assertIn("signing_credentials=forbidden", files["user-data"])

    def test_seed_temporary_name_already_has_iso_suffix(self) -> None:
        temporary = BUILDER.SEED_ISO.with_name(
            f".{BUILDER.SEED_ISO.stem}.partial.iso"
        )
        self.assertEqual(temporary.suffix, ".iso")
        self.assertNotEqual(temporary, BUILDER.SEED_ISO)

    def test_ssh_uses_explicit_identity_and_quoted_known_hosts(self) -> None:
        original = BUILDER.command_path
        try:
            BUILDER.command_path = lambda name: f"/qualified/{name}"
            command = BUILDER.ssh_base()
        finally:
            BUILDER.command_path = original
        self.assertIn(str(BUILDER.PRIVATE_KEY), command)
        self.assertIn(
            f'UserKnownHostsFile="{BUILDER.KNOWN_HOSTS}"', command
        )
        self.assertIn("StrictHostKeyChecking=yes", command)

    def test_scp_uses_the_same_strict_identity_boundary(self) -> None:
        original = BUILDER.command_path
        try:
            BUILDER.command_path = lambda name: f"/qualified/{name}"
            command = BUILDER.scp_base()
        finally:
            BUILDER.command_path = original
        self.assertIn(str(BUILDER.PRIVATE_KEY), command)
        self.assertIn(
            f'UserKnownHostsFile="{BUILDER.KNOWN_HOSTS}"', command
        )
        self.assertIn("StrictHostKeyChecking=yes", command)

    def test_fetch_is_limited_to_ignored_r6_1_image_artifacts(self) -> None:
        source, destination = BUILDER.validate_fetch_paths(
            "/home/yocto/r61-build/upstream/main-qemuarm64.img",
            "artifacts/r6-1/upstream/main-qemuarm64.img",
        )
        self.assertEqual(
            source, "/home/yocto/r61-build/upstream/main-qemuarm64.img"
        )
        self.assertEqual(
            destination,
            (BUILDER.ARTIFACT_ROOT / "upstream/main-qemuarm64.img").resolve(),
        )
        with self.assertRaisesRegex(BUILDER.BuilderError, "below /home/yocto"):
            BUILDER.validate_fetch_paths(
                "/etc/shadow", "artifacts/r6-1/upstream/shadow.img"
            )
        with self.assertRaisesRegex(BUILDER.BuilderError, "allowed"):
            BUILDER.validate_fetch_paths(
                "/home/yocto/r61-build/upstream/aos-user-oem.p12",
                "artifacts/r6-1/upstream/aos-user-oem.p12",
            )
        with self.assertRaisesRegex(BUILDER.BuilderError, "below artifacts"):
            BUILDER.validate_fetch_paths(
                "/home/yocto/r61-build/upstream/main-qemuarm64.img",
                "/tmp/main-qemuarm64.img",
            )

    def test_builder_tool_bootstrap_is_pinned_and_identity_free(self) -> None:
        script = BUILDER.build_tools_script()

        self.assertIn(f"conan=={BUILDER.CONAN_VERSION}", script)
        self.assertIn(f"cmake=={BUILDER.CMAKE_VERSION}", script)
        self.assertIn("softhsm2", script)
        self.assertIn("mtools", script)
        self.assertIn("mmd --version", script)
        self.assertIn("R6_1_BUILDER_TOOLS=PASS", script)
        self.assertNotIn("certificate", script.lower())
        self.assertNotIn("signing", script.lower())

    def test_moulin_toolchain_pins_the_compatible_gpt_image_wheel(self) -> None:
        script = BUILDER.moulin_tools_script()

        self.assertIn(BUILDER.MOULIN_REVISION, script)
        self.assertIn(BUILDER.GPT_IMAGE_VERSION, script)
        self.assertIn(BUILDER.GPT_IMAGE_WHEEL_URL, script)
        self.assertIn(BUILDER.GPT_IMAGE_WHEEL_SHA256, script)
        self.assertIn(
            f"gpt_image-{BUILDER.GPT_IMAGE_VERSION}-py3-none-any.whl", script
        )
        self.assertIn("sha256sum --check --status", script)
        self.assertIn("--force-reinstall --no-deps", script)
        self.assertIn(BUILDER.PYDANTIC_VERSION, script)
        self.assertIn(BUILDER.PYDANTIC_WHEEL_SHA256, script)
        self.assertIn(BUILDER.PYDANTIC_CORE_VERSION, script)
        self.assertIn(BUILDER.PYDANTIC_CORE_WHEEL_SHA256, script)
        self.assertIn(BUILDER.ANNOTATED_TYPES_WHEEL_SHA256, script)
        self.assertIn(BUILDER.TYPING_EXTENSIONS_WHEEL_SHA256, script)
        self.assertIn('hasattr(BaseModel, "model_dump")', script)
        self.assertIn("R6_1_MOULIN_TOOLS=PASS", script)
        self.assertNotIn("certificate", script.lower())
        self.assertNotIn("signing", script.lower())

    def test_yocto_cache_is_persistent_ext4_and_identity_free(self) -> None:
        script = BUILDER.yocto_cache_script()

        self.assertIn(BUILDER.YOCTO_DOWNLOADS_DIR, script)
        self.assertIn(BUILDER.YOCTO_SSTATE_DIR, script)
        self.assertIn("findmnt -n -o FSTYPE -T", script)
        self.assertIn("r6-1-yocto-cache-v1", script)
        self.assertIn("R6_1_YOCTO_CACHE=PASS", script)
        self.assertNotIn("aos-user-", script)
        self.assertNotIn("PRIVATE KEY", script)


if __name__ == "__main__":
    unittest.main()
