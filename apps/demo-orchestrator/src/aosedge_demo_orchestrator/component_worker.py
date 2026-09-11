# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private Demo Control adapter for the installed official Aos signing runtime."""

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aosedge_demo_orchestrator.components import archive_files, sha
from aosedge_demo_orchestrator.environment import EnvironmentError


def verify(path, credential, expected=None):
    import jwt
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    raw = path.read_bytes()
    if expected and sha(raw) != expected:
        raise EnvironmentError("COMPONENT_SIGNED_DIGEST_CHANGED")
    outer = archive_files(raw)
    if set(outer) != {"package.sign", "config.yaml", "batch.tar.gz"}:
        raise EnvironmentError("COMPONENT_SIGNED_ENVELOPE_INVALID")
    _, certificate, _ = load_key_and_certificates(credential.read_bytes(), b"")
    payload = jwt.decode(outer["package.sign"], certificate.public_key(), algorithms=["RS256"])
    records = payload.get("data")
    if not isinstance(records, list) or len(records) != 2:
        raise EnvironmentError("COMPONENT_SIGNATURE_CONTENTS_INVALID")
    expected_records = [dict(name=name, size=len(outer[name]), hash=hashlib.sha3_512(outer[name]).hexdigest())
                        for name in ("batch.tar.gz", "config.yaml")]
    if sorted(records, key=lambda item: item["name"]) != sorted(expected_records, key=lambda item: item["name"]):
        raise EnvironmentError("COMPONENT_SIGNED_HASH_MISMATCH")
    if archive_files(outer["batch.tar.gz"])["config.yaml"] != outer["config.yaml"]:
        raise EnvironmentError("COMPONENT_SIGNED_CONFIG_MISMATCH")
    return dict(sha256=sha(raw), sizeBytes=len(raw), signatureVerification="VERIFIED_RS256",
                verificationTrust="CONFIGURED_OEM_SIGNING_CERTIFICATE")


def execute(request):
    if request["action"] == "validate-service":
        from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
        path = Path(request["directory"]) / "config.yaml"
        config = UpdateBundleConfiguration(path)
        if len(config.upload_meta_config.items) != 1 or config.upload_meta_config.items[0].identity.type != "service":
            raise EnvironmentError("SERVICE_PACKAGE_TYPE_INVALID")
        return dict(state="VALIDATED_SERVICE_CONFIG")
    if request["action"] in ("service-sign", "service-verify", "service-upload", "service-cloud-status"):
        if request["action"] in ("service-upload", "service-cloud-status"):
            from aosedge_demo_orchestrator.service_publication import execute as publish
            from aosedge_demo_orchestrator.unit_cloud import CloudFailure
            try:
                return publish(request)
            except CloudFailure as error:
                raise EnvironmentError(str(error)) from None
        if request["action"] == "service-verify":
            return verify_service(request)
        return sign_service(request)
    credential = Path(request["credential"])
    if credential.is_symlink() or credential.stat().st_mode & 0o077:
        raise EnvironmentError("OEM_CREDENTIAL_UNSAFE")
    if request["action"] == "verify":
        return verify(Path(request["bundle"]), credential, request["expectedSha256"])
    if request["action"] == "sign":
        from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
        from aos_signer.signer.signer import Signer
        directory, output = Path(request["directory"]), Path(request["output"])
        if output.exists() or output.is_symlink():
            raise EnvironmentError("COMPONENT_SIGN_OUTPUT_EXISTS")
        # Official signer writes batch.tar.gz to its working directory. Isolate
        # that staging output; input config and payload remain immutable.
        with tempfile.TemporaryDirectory(prefix=".sign-", dir=directory) as temporary:
            stage = Path(temporary)
            raw_config = (directory / "config.yaml").read_bytes()
            (stage / "config.yaml").write_bytes(raw_config)
            config = json.loads(raw_config)
            item = config["items"][0]
            name = item["sourceFolder"] + "/" + item["images"][0]["path"]
            target = stage / name
            target.parent.mkdir()
            target.write_bytes((directory / name).read_bytes())
            os.chdir(stage)
            path = stage / "config.yaml"
            Signer(UpdateBundleConfiguration(path), path, pkcs12_path=str(credential)).process()
            result = verify(stage / "batch.tar.gz", credential)
            os.link(stage / "batch.tar.gz", output)
        return result
    if request["action"] in ("release-catalog", "cloud-status", "upload", "approve", "unapprove", "send"):
        from aosedge_demo_orchestrator.component_cloud import execute as cloud_execute
        from aosedge_demo_orchestrator.unit_cloud import CloudFailure
        try:
            return cloud_execute(request)
        except CloudFailure as error:
            raise EnvironmentError(str(error)) from None
    raise EnvironmentError("COMPONENT_WORKER_ACTION_INVALID")


def verify_service(request):
    from aosedge_demo_orchestrator.service_packages import read_package
    credential = Path(request["credential"])
    if credential.is_symlink() or not credential.is_file() or credential.stat().st_mode & 0o077:
        raise EnvironmentError("SERVICE_SP_CREDENTIAL_UNSAFE")
    bundle = Path(request["bundle"])
    if bundle.is_symlink() or not bundle.is_file():
        raise EnvironmentError("SERVICE_SIGNED_PATH_UNSAFE")
    _, files = read_package(Path(request["directory"]), request["team"], request["version"])
    result = verify(bundle, credential, request.get("expectedSha256"))
    outer = archive_files(bundle.read_bytes())
    if archive_files(outer["batch.tar.gz"]) != files:
        raise EnvironmentError("SERVICE_SIGNED_PAYLOAD_CHANGED")
    return dict(result, payloadMatchesPrepared=True, verificationTrust="CONFIGURED_SP_SIGNING_CERTIFICATE")


def sign_service(request):
    from aosedge_demo_orchestrator.service_packages import read_package
    from aosedge_demo_orchestrator.unit_cloud import Cloud, CloudFailure
    from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
    from aos_signer.signer.signer import Signer
    credential = Path(request["credential"])
    if credential.is_symlink() or not credential.is_file() or credential.stat().st_mode & 0o077:
        raise EnvironmentError("SERVICE_SP_CREDENTIAL_UNSAFE")
    # Confirm the configured signing account once; the prepared SP must not
    # silently change with a different certificate at the same local path.
    try:
        Cloud(request, expected_role="service provider")
    except CloudFailure as error:
        raise EnvironmentError(str(error)) from None
    directory, output = Path(request["directory"]), Path(request["bundle"])
    if output.exists() or output.is_symlink():
        raise EnvironmentError("SERVICE_SIGN_OUTPUT_EXISTS")
    _, files = read_package(directory, request["team"], request["version"])
    with tempfile.TemporaryDirectory(prefix=".sign-", dir=directory) as temporary:
        stage = Path(temporary)
        for name, raw in files.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            target.chmod((directory / name).stat().st_mode & 0o777)
        for parent, _, _ in os.walk(stage / "service"):
            Path(parent).chmod(0o755)
        old_cwd = Path.cwd()
        try:
            os.chdir(stage)
            path = stage / "config.yaml"
            Signer(UpdateBundleConfiguration(path), path, pkcs12_path=request["credential"]).process()
        finally:
            os.chdir(old_cwd)
        result = verify_service(dict(request, bundle=str(stage / "batch.tar.gz")))
        os.link(stage / "batch.tar.gz", output)
    return result


def main():
    try:
        request = json.loads(sys.stdin.read(65537))
        # Never forward raw signer diagnostics, certificates, paths or headers.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            data = execute(request)
        result = dict(ok=True, data=data)
    except EnvironmentError as error:
        result = dict(ok=False, reason=str(error))
    except Exception as error:
        result = dict(ok=False, reason="COMPONENT_ADAPTER_FAILED_" + type(error).__name__)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
