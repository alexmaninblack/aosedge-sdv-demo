# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Demo Control service package preparation, independent of a running vehicle."""

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

from .environment import EnvironmentError, atomic_json, digest
from .releases import ReleaseContinuity, number
from .service_build import ServiceBuilder
from .services import ServiceCatalog
from .status import load_configuration, now, read_json

RELEASE_FILE = "usr/share/aosedge/service-release.json"
QUOTAS = ("cpuLimit", "ramLimit", "storageLimit", "stateLimit", "tmpLimit", "noFileLimit", "pidsLimit")


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def package_record(directory, team, version):
    """Read bounded identity metadata; status never rehashes payload files."""
    number(version)
    if team not in ("brake", "tire") or directory.is_symlink() or (directory / "prepared.json").is_symlink():
        raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
    record = read_json(directory / "prepared.json", limit=1048576)
    if (record.get("schemaVersion") != 1 or record.get("state") != "PREPARED" or record.get("team") != team
            or record.get("version") != version or record.get("releaseHandle") != team + "/" + version
            or record.get("packagePath") != str(directory) or not isinstance(record.get("files"), dict)
            or not 4 <= len(record["files"]) <= 4098):
        raise EnvironmentError("SERVICE_PACKAGE_RECEIPT_INVALID")
    return record


def read_package(directory, team, version):
    """Check the prepared snapshot at signing/publication trust boundaries."""
    record = package_record(directory, team, version)
    files, total = {}, 0
    binary_names = {"service/arm64/usr/bin/" + team + "-health-" + name for name in ("bootstrap", "service")}
    for name, expected in record["files"].items():
        from pathlib import PurePosixPath
        if not isinstance(name, str):
            raise EnvironmentError("SERVICE_PACKAGE_FILE_INVALID")
        parts = PurePosixPath(name).parts
        if (not isinstance(name, str) or not parts or name != "/".join(parts) or name.startswith("/") or ".." in parts
                or (name not in ("config.yaml", "service/arm64/" + RELEASE_FILE) and name not in binary_names
                    and not name.startswith("service/arm64/usr/share/licenses/" + team + "-health-service/"))):
            raise EnvironmentError("SERVICE_PACKAGE_FILE_INVALID")
        path = directory.joinpath(*parts)
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent.is_relative_to(directory)) or not path.is_file():
            raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
        if name != "config.yaml" and stat.S_IMODE(path.stat().st_mode) != (0o755 if name in binary_names else 0o444):
            raise EnvironmentError("SERVICE_PACKAGE_MODE_CHANGED")
        total += path.stat().st_size
        if total > 256 * 1024 * 1024:
            raise EnvironmentError("SERVICE_PACKAGE_SIZE_LIMIT")
        with path.open("rb") as stream:
            raw = stream.read(256 * 1024 * 1024 + 1)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise EnvironmentError("SERVICE_PACKAGE_CONTENT_CHANGED")
        files[name] = raw
    payload = directory / "service"
    actual = set()
    for parent, dirs, names in os.walk(payload, followlinks=False):
        if any((Path(parent) / name).is_symlink() for name in dirs):
            raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
        actual.update((Path(parent) / name).relative_to(directory).as_posix() for name in names)
    if actual != set(files) - {"config.yaml"}:
        raise EnvironmentError("SERVICE_PACKAGE_CONTENT_CHANGED")
    if not binary_names <= files.keys():
        raise EnvironmentError("SERVICE_PACKAGE_BINARY_MISSING")
    config = json.loads(files["config.yaml"])
    items = config.get("items", [])
    release = json.loads(files["service/arm64/" + RELEASE_FILE])
    if (len(items) != 1 or items[0].get("version") != version or items[0].get("identity", {}).get("type") != "service"
            or items[0]["identity"].get("codename") != team + "-health-service" or items[0].get("sourceFolder") != "service"
            or items[0].get("images") != [dict(sourceFolder="arm64", archInfo=dict(architecture="arm64"))]
            or "env" in items[0].get("configuration", {})
            or release != dict(schemaVersion=1, serviceVersion=version)):
        raise EnvironmentError("SERVICE_PACKAGE_VERSION_OR_IDENTITY_MISMATCH")
    return record, files


def package_configuration(root, team, content_profile, version):
    """Native schema-2 input, using accepted exact product permissions/quotas."""
    number(version)
    contracts = root / "contracts"
    if team == "brake" and content_profile in ("v1", "v2", "v3"):
        source = ("brake-telemetry-window/brake-telemetry-window-profile.v1.json" if content_profile == "v1"
                  else "brake-health-model/brake-health-model-profile.v1.json")
        paths = read_json(contracts / source)["input"]["paths"]
        quotas = read_json(contracts / "brake-health-runtime/brake-health-runtime-profile.v1.json")["aosRequestedQuotas"]
        advisory, port = content_profile == "v3", 18091
    elif team == "tire" and content_profile == "v1":
        product = read_json(contracts / "tire-health-model/tire-health-product-profile.v1.json")
        paths, quotas = product["input"]["paths"], product["runtime"]["requestedQuota"]
        advisory, port = True, 18092
    else:
        raise EnvironmentError("SERVICE_CONTENT_PROFILE_INVALID")
    permissions = dict.fromkeys(paths, "r")
    if advisory:
        prefix = "Vehicle.OEM." + team.title() + "Health.Advisory."
        permissions[prefix + "GatewayStatus"] = "r"
        permissions[prefix + "Request"] = "rw"
    return dict(schemaVersion=2, publisher=dict(author="maninblack"), items=[dict(
        identity=dict(type="service", codename=team + "-health-service", title=team.title() + " Health Service"),
        version=version, sourceFolder="service", images=[dict(sourceFolder="arm64", archInfo=dict(architecture="arm64"))],
        configuration=dict(workingDir="/", cmd="/usr/bin/" + team + "-health-bootstrap"
            " --metadata-file /run/aosedge/platform/service-inputs/metadata.json"
            " --ca-file /run/aosedge/platform/service-inputs/kuksa-ca.pem",
            instances=dict(minInstances=1, priority=10), offlineTTL="P7D",
            quotas={key: quotas[key] for key in QUOTAS}, alertRules=None,
            resources=[dict(name=name) for name in ("kuksa", "kuksa-auth-client", team + "-runtime-inputs")],
            permissions=dict(kuksa=permissions), allowedConnections=["Server/55555/tcp", "10.0.0.1/" + str(port) + "/tcp"]),
        dependencies=[])])


def product_files(build, team):
    """Read only exported executable/public-license leaves, never host state."""
    output = Path(build["outputPath"])
    rootfs = output / "rootfs"
    if rootfs.is_symlink() or not rootfs.is_dir():
        raise EnvironmentError("SERVICE_PRODUCT_ROOTFS_UNSAFE")
    files, total = {}, 0
    binaries = {"usr/bin/" + team + "-health-" + name for name in ("bootstrap", "service")}
    for directory, dirs, names in os.walk(rootfs, followlinks=False):
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise EnvironmentError("SERVICE_PRODUCT_LINK_UNSUPPORTED")
        for name in names:
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(rootfs).as_posix()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise EnvironmentError("SERVICE_PRODUCT_LINK_UNSUPPORTED")
            if relative not in binaries and not relative.startswith("usr/share/licenses/" + team + "-health-service/"):
                raise EnvironmentError("SERVICE_PRODUCT_UNEXPECTED_FILE")
            total += info.st_size
            if total > 256 * 1024 * 1024 or len(files) >= 4096:
                raise EnvironmentError("SERVICE_PRODUCT_SIZE_LIMIT")
            with path.open("rb") as stream:
                raw = stream.read(info.st_size + 1)
            if len(raw) != info.st_size:
                raise EnvironmentError("SERVICE_PRODUCT_CHANGED_DURING_READ")
            if relative in binaries:
                if (raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00" or not info.st_mode & 0o111
                        or hashlib.sha256(raw).hexdigest() != build["binaries"].get("rootfs/" + relative)):
                    raise EnvironmentError("SERVICE_PRODUCT_BINARY_MISMATCH")
            files[relative] = (raw, 0o755 if relative in binaries else 0o444)
    if not binaries <= files.keys() or not (files.keys() - binaries):
        raise EnvironmentError("SERVICE_PRODUCT_EXECUTABLES_AND_LICENSES_REQUIRED")
    return files


class ServicePackages:
    def __init__(self, environment, progress=None):
        self.environment = environment
        self.progress = progress or (lambda message: None)

    def _record(self, handle, *, verify_payload=True):
        parts = handle.split("/") if isinstance(handle, str) else []
        if len(parts) != 2 or parts[0] not in ("brake", "tire"):
            raise EnvironmentError("SERVICE_RELEASE_HANDLE_REQUIRED")
        team, version = parts
        number(version)
        directory = self.environment.catalog.project / "services" / team / "releases" / version
        if (any(path.is_symlink() for path in (directory, *directory.parents) if path.is_relative_to(self.environment.catalog.project))
                or not directory.resolve().is_relative_to(self.environment.catalog.project.resolve())):
            raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
        return directory, (read_package(directory, team, version)[0] if verify_payload else package_record(directory, team, version))

    def _worker(self, action, directory, record, **values):
        from .status import object_id
        config = load_configuration(self.environment.root)
        profile = config["cloudProfiles"].get(record["cloudProfile"])
        if (not profile or profile["expectedRole"] != "service provider"
                or profile.get("expectedOwnerId", record["serviceProviderId"]) != record["serviceProviderId"]):
            raise EnvironmentError("SERVICE_SP_BINDING_CHANGED")
        credential = profile["credential"]
        if credential.is_symlink() or not credential.is_file() or credential.stat().st_mode & 0o077:
            raise EnvironmentError("SERVICE_SP_CREDENTIAL_UNSAFE")
        request = dict(values, action=action, credential=str(credential), ownerId=object_id(record["serviceProviderId"]),
            serviceId=record.get("serviceId"), team=record["team"], version=record["version"], directory=str(directory))
        try:
            process = subprocess.run([str(config["cloudPython"]), "-I", "-B",
                str(Path(__file__).with_name("component_worker.py"))], text=True, capture_output=True,
                timeout=90, env={"PATH": os.defpath}, input=json.dumps(request))
            if process.returncode or len(process.stdout) > 262144:
                raise EnvironmentError("SERVICE_WORKER_RESPONSE_UNAVAILABLE")
            result = json.loads(process.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            raise EnvironmentError("SERVICE_WORKER_RESPONSE_UNAVAILABLE") from None
        if not isinstance(result, dict):
            raise EnvironmentError("SERVICE_WORKER_RESPONSE_UNAVAILABLE")
        if result.get("ok") is not True:
            # Worker messages contain only fixed diagnostics. Never relay raw
            # HTTP/signer output or credentials across the application boundary.
            import re
            reason = result.get("reason", "")
            raise EnvironmentError(reason if isinstance(reason, str) and re.fullmatch(r"[A-Z_0-9:,-]{1,160}", reason)
                else "SERVICE_WORKER_FAILED")
        if not isinstance(result.get("data"), dict):
            raise EnvironmentError("SERVICE_WORKER_RESPONSE_UNAVAILABLE")
        return result["data"]

    def sign(self, handle):
        with self.environment._writer():
            directory, record = self._record(handle)
            bundle = directory / "deployment-bundle.tar.gz"
            receipt = directory / "signed.json"
            if bundle.is_symlink() or receipt.is_symlink():
                raise EnvironmentError("SERVICE_SIGNED_PATH_UNSAFE")
            if receipt.exists() and not bundle.exists():
                raise EnvironmentError("SERVICE_SIGNED_BUNDLE_MISSING")
            existing = bundle.exists()
            expected = read_json(receipt).get("sha256") if receipt.exists() else None
            result = self._worker("service-verify" if existing else "service-sign", directory, record,
                bundle=str(bundle), expectedSha256=expected)
            if result.get("signatureVerification") != "VERIFIED_RS256" or result.get("payloadMatchesPrepared") is not True:
                raise EnvironmentError("SERVICE_SIGNATURE_NOT_VERIFIED")
            atomic_json(receipt, result)
            return dict(result, releaseHandle=handle, bundlePath=str(bundle), noOp=existing)

    def _test_scope(self):
        from .environment import JOURNAL
        from .status import object_id
        path = self.environment.root / JOURNAL
        if not path.exists():
            return None
        if path.is_symlink():
            raise EnvironmentError("SERVICE_TEST_SCOPE_UNSAFE")
        journal = read_json(path)
        value = journal.get("vehicles", {}).get("test") or {}
        if not value.get("unitId"):
            return None
        if (not value.get("localVmId") or not value.get("systemUid")
                or value.get("cloud", {}).get("lifecycle") in ("DEPROVISIONED", "DELETED")):
            raise EnvironmentError("SERVICE_TEST_SCOPE_UNAVAILABLE")
        return dict(unitId=object_id(value["unitId"]), systemUid=value["systemUid"])

    def upload(self, handle):
        with self.environment._writer():
            directory, record = self._record(handle, verify_payload=False)
            path = directory / "publication.json"
            if path.is_symlink():
                raise EnvironmentError("SERVICE_PUBLICATION_PATH_UNSAFE")
            if path.exists():
                previous = read_json(path)
                if previous.get("attempted") is not False:
                    return dict(self.cloud_status(handle), noOp=True)
            read_package(directory, record["team"], record["version"])
            bundle, receipt = directory / "deployment-bundle.tar.gz", directory / "signed.json"
            if bundle.is_symlink() or receipt.is_symlink() or not bundle.is_file() or not receipt.is_file():
                raise EnvironmentError("SERVICE_SIGNED_PACKAGE_REQUIRED")
            signed = read_json(receipt)
            if signed.get("signatureVerification") != "VERIFIED_RS256" or digest(bundle) != signed.get("sha256"):
                raise EnvironmentError("SERVICE_SIGNED_BUNDLE_CHANGED")
            test = self._test_scope()
            intent = dict(schemaVersion=1, releaseHandle=handle, stage="ATTEMPTING", attempted=True,
                sha256=signed["sha256"], startedAt=now())
            atomic_json(path, intent)
            self.progress(record["team"] + ": SP preflight and one Deployment Bundle upload; no assignment or approval")
            try:
                response = self._worker("service-upload", directory, record, bundle=str(bundle),
                    expectedSha256=signed["sha256"], test=test)
            except EnvironmentError:
                response = dict(stage="UNCERTAIN", attempted=True, reason="SERVICE_UPLOAD_WORKER_RESPONSE_LOST")
            if (not isinstance(response, dict) or response.get("stage") not in ("ACCEPTED", "ERROR", "UNCERTAIN", "BLOCKED")
                    or type(response.get("attempted")) is not bool
                    or (response["stage"] == "BLOCKED") != (response["attempted"] is False)):
                response = dict(stage="UNCERTAIN", attempted=True, reason="SERVICE_UPLOAD_RESPONSE_INVALID")
            intent.update(response, observedAt=now())
            atomic_json(path, intent)
            return dict(intent, noOp=False)

    def cloud_status(self, handle):
        with self.environment._writer():
            directory, record = self._record(handle, verify_payload=False)
            path = directory / "publication.json"
            if path.is_symlink():
                raise EnvironmentError("SERVICE_PUBLICATION_PATH_UNSAFE")
            if not path.exists():
                return dict(stage="NOT_PUBLISHED", releaseHandle=handle)
            intent = read_json(path)
            if intent.get("attempted") is False:
                return intent
            result = self._worker("service-cloud-status", directory, record, deploymentId=intent.get("deploymentId"))
            # Preserve the actual mutation receipt; observations do not erase
            # it, claim installation, retry upload or allocate another release.
            intent["lastObservation"] = result
            atomic_json(path, intent)
            return dict(result, releaseHandle=handle)

    def _validate(self, directory):
        # Reuse the installed official signer adapter. Validation reads source
        # paths/schema only; it neither reads a signing key nor signs/uploads.
        config = load_configuration(self.environment.root)
        process = subprocess.run([str(config["cloudPython"]), "-I", "-B",
            str(Path(__file__).with_name("component_worker.py"))], text=True, capture_output=True, timeout=30,
            env={"PATH": os.defpath}, input=json.dumps(dict(action="validate-service", directory=str(directory))))
        if process.returncode or len(process.stdout) > 4096:
            raise EnvironmentError("SERVICE_PACKAGE_SCHEMA_INVALID")
        result = json.loads(process.stdout)
        if result != {"ok": True, "data": {"state": "VALIDATED_SERVICE_CONFIG"}}:
            raise EnvironmentError("SERVICE_PACKAGE_SCHEMA_INVALID")

    def prepare(self, team, content_profile, cloud_profile="service-provider"):
        if team not in ("brake", "tire") or content_profile not in ("v1", "v2", "v3"):
            raise EnvironmentError("SERVICE_CONTENT_PROFILE_INVALID")
        with self.environment._writer():
            # Preparation must never invoke Docker, boot a VM or collect guest
            # metadata. An absent real product export is an explicit build step.
            build = ServiceBuilder(self.environment, self.progress).execute(team, content_profile, build_missing=False)
            files = product_files(build, team)
            self.progress(team + ": existing product build selected; reading SP release catalog")
            binding = ServiceCatalog(self.environment).release_versions(team, cloud_profile)
            directory = self.environment.catalog.project / "services" / team / "releases"
            if (any(path.is_symlink() for path in (directory, directory.parent, directory.parent.parent))
                    or not directory.resolve().is_relative_to(self.environment.catalog.project.resolve())):
                raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
            observed = list(binding["versions"])
            if directory.exists():
                for path in directory.iterdir():
                    if path.name.startswith(".prepare-"):
                        continue
                    number(path.name)
                    if path.is_symlink() or not path.is_dir():
                        raise EnvironmentError("SERVICE_PACKAGE_PATH_UNSAFE")
                    observed.append(path.name)
            version = ReleaseContinuity(self.environment).reserve(team, observed)
            self.progress(team + ": preparing release " + version + "; no build or VM action")
            config = package_configuration(self.environment.root, team, content_profile, version)
            files[RELEASE_FILE] = (encoded(dict(schemaVersion=1, serviceVersion=version)), 0o444)
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            target = directory / version
            if target.exists() or target.is_symlink():
                raise EnvironmentError("SERVICE_RELEASE_ALREADY_PREPARED")
            with tempfile.TemporaryDirectory(prefix=".prepare-", dir=directory) as temporary:
                stage = Path(temporary)
                (stage / "config.yaml").write_bytes(encoded(config))
                inventory = {"config.yaml": digest(stage / "config.yaml")}
                for name, (raw, mode) in sorted(files.items()):
                    path = stage / "service/arm64" / name
                    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                    path.write_bytes(raw)
                    path.chmod(mode)
                    inventory[path.relative_to(stage).as_posix()] = hashlib.sha256(raw).hexdigest()
                # Caller umask must not make payload directories inaccessible
                # to the native service UID inside the resulting image.
                for parent, _, _ in os.walk(stage / "service"):
                    Path(parent).chmod(0o755)
                self._validate(stage)
                result = dict(schemaVersion=1, team=team, contentProfile=content_profile, version=version,
                    releaseHandle=team + "/" + version, state="PREPARED", preparedAt=now(),
                    sourceRevision=build["sourceRevision"], files=inventory,
                    serviceId=binding["serviceId"], serviceProviderId=binding["ownerId"], cloudProfile=cloud_profile,
                    qualification="PREPARED_NOT_RUNTIME_QUALIFIED", packagePath=str(target))
                atomic_json(stage / "prepared.json", result)
                stage.rename(target)
            return result
