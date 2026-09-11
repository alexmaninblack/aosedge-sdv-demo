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
