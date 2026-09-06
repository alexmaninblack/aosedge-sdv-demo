# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline VDP family composition from frozen source and qualified dependencies."""

import gzip
import ast
import io
import json
import re
import subprocess
import tarfile
from pathlib import PurePosixPath

from .components import COMPONENT, MEDIA_TYPE, document, sha
from .environment import EnvironmentError

SOURCE = "0a2c8249ec780e822bff90f29f9d3d5ba5dd7feb"
BASE_SHA = "b36e3064166739c98ec028fc75980bf4ea937d531a7e7a7889e11283dd1d7d9c"
PACKAGE = "python/carla_viss_kuksa_provider/"
SOURCE_PACKAGE = "providers/carla-viss-kuksa/src/carla_viss_kuksa_provider/"
PROFILE_BASES = {
    "v1": ("1.0.16", BASE_SHA, "v1_0_16", 7),
    "v2": ("2.0.0", "8cea21f1280961f997fe38c724b346a1c4ee2cb246d7da660849afac87599450", "v2", 15),
    "v3": ("3.0.0", "451965e1d03259a7edf66a4c742125c290f5efbfb2089530572395da2a1901fd", "v3", 23),
}


def version_number(version):
    from .components import VERSION
    if not isinstance(version, str) or len(version) > 32 or not VERSION.fullmatch(version):
        raise EnvironmentError("COMPONENT_VERSION_INVALID")
    return tuple(map(int, version.split(".")))


def replace_constant(data, name, old, new):
    text = data.decode()
    pattern = r'(?m)^' + re.escape(name) + r' = "' + re.escape(old) + r'"$'
    changed, count = re.subn(pattern, name + ' = "' + new + '"', text)
    if count != 1:
        raise EnvironmentError("COMPONENT_PROFILE_CONSTANT_MISMATCH:" + name)
    return changed.encode()


def replay(version, profile, baseline, baseline_sha, contract, factory):
    """New Cloud release, frozen functional profile; no application-code change."""
    if profile not in PROFILE_BASES or version_number(version) < (4, 0, 0):
        raise EnvironmentError("COMPONENT_REPLAY_PROFILE_OR_VERSION_INVALID")
    base_version, expected_sha, module, path_count = PROFILE_BASES[profile]
    if baseline_sha != expected_sha:
        raise EnvironmentError("COMPONENT_REPLAY_BASE_NOT_PINNED")
    files = dict(baseline)
    capability = document(files, "config/capability-manifest.json")
    expected = next(item for item in contract["componentVersions"] if item["id"] == "VDP_" + profile.upper())
    if (capability["readPaths"] != expected["readPaths"] or len(capability["readPaths"]) != path_count
            or capability["capabilities"] != expected["capabilities"]
            or capability["semanticVersion"] != base_version):
        raise EnvironmentError("COMPONENT_RELEASE_PATH_SET_MISMATCH")
    old_manifest_sha = sha(files["config/capability-manifest.json"])
    capability["semanticVersion"] = version
    files["config/capability-manifest.json"] = encoded(capability)
    manifest_sha = sha(files["config/capability-manifest.json"])
    provider = document(files, "config/provider.json")
    if provider["semanticVersion"] != base_version or provider["capabilityManifestSha256"] != old_manifest_sha:
        raise EnvironmentError("COMPONENT_RELEASE_DIGEST_MISMATCH")
    provider.update(semanticVersion=version, capabilityManifestSha256=manifest_sha)
    files["config/provider.json"] = encoded(provider)
    metadata = document(files, "component.json")
    if metadata["version"] != base_version:
        raise EnvironmentError("COMPONENT_VERSION_MISMATCH")
    metadata["version"] = version
    files["component.json"] = encoded(metadata)
    imports = ast.parse(files[PACKAGE + "vdp_release_profile.py"]).body
    if (len(imports) != 1 or not isinstance(imports[0], ast.ImportFrom)
            or imports[0].level != 1 or imports[0].module != "releases." + module
            or [item.name for item in imports[0].names] != ["*"]):
        raise EnvironmentError("COMPONENT_PROFILE_SELECTION_MISMATCH")
    module_path = PACKAGE + "releases/" + module + ".py"
    files[module_path] = replace_constant(files[module_path], "VERSION", base_version, version)
    files[module_path] = replace_constant(files[module_path], "MANIFEST_SHA256", old_manifest_sha, manifest_sha)
    files[PACKAGE + "__init__.py"] = replace_constant(files[PACKAGE + "__init__.py"], "__version__", base_version, version)
    sbom = document(files, "sbom/spdx.json")
    sbom["name"] = "aosedge-vdp-component-" + version + "-linux-arm64"
    sbom["documentNamespace"] = sbom["documentNamespace"].replace("/" + base_version + "/", "/" + version + "/")
    files["sbom/spdx.json"] = encoded(sbom)
    provenance = document(files, "provenance/provenance.json")
    provenance.update(semanticVersion=version, buildType="democtl-profile-replay-v1",
        contentProfile=profile, baseContentVersion=base_version, baselineBundleSha256=baseline_sha,
        factoryImageVersion=factory["version"], factoryImageRawSha256=factory["sha256"],
        qualificationScope="TELEMETRY_ONLY_ADVISORY_DEFERRED",
        buildInputs=[dict(path=name, sha256=sha(content)) for name, content in sorted(files.items())
                     if not name.startswith(("provenance/", "sbom/"))])
    files["provenance/provenance.json"] = encoded(provenance)
    allowed = {"component.json", "config/provider.json", "config/capability-manifest.json",
               module_path, PACKAGE + "__init__.py", "sbom/spdx.json", "provenance/provenance.json"}
    if set(files) != set(baseline) or any(files[name] != baseline[name] for name in files.keys() - allowed):
        raise EnvironmentError("COMPONENT_REPLAY_CHANGED_FUNCTIONAL_CONTENT")
    for name in allowed:
        if name.endswith(".py"):
            compile(files[name], name, "exec")
    layer_name = "vdp-" + version + "-arm64.tar.gz"
    layer = pack(files)
    config = encoded(dict(schemaVersion=2, publisher=dict(author="maninblack"), items=[dict(
        identity=dict(codename=COMPONENT, type="component", title="Vehicle Data Platform",
                      description="Telemetry " + profile + "; advisory deferred"),
        version=version, sourceFolder="vehicle-data-platform",
        configuration=dict(runtimes=[dict(codename=COMPONENT, type="runtime")]),
        images=[dict(path=layer_name, mediaType=MEDIA_TYPE, archInfo=dict(architecture="arm64"), osInfo=dict(os="linux"))])]))
    return {"config.yaml": config, "vehicle-data-platform/" + layer_name: layer}, dict(
        version=version, contentProfile=profile, baseContentVersion=base_version,
        baseBundleSha256=baseline_sha, payloadSha256=sha(layer), readPathCount=path_count,
        capabilityManifestSha256=manifest_sha, qualificationScope="TELEMETRY_ONLY",
        advisory="DEFERRED" if profile == "v3" else "NOT_APPLICABLE", deterministic=True,
        changedPayloadFiles=sorted(name for name in files if files[name] != baseline[name]))


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def pack(files):
    buffer = io.BytesIO()
    directories = {p.as_posix() for name in files for p in PurePosixPath(name).parents if p.as_posix() != "."}
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name in sorted(set(files) | directories):
            item = tarfile.TarInfo(name)
            item.uid = item.gid = item.mtime = 0
            item.uname = item.gname = "root"
            if name in directories:
                item.type, item.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(item)
            else:
                item.mode = 0o755 if name == "bin/vehicle-data-provider" else 0o644
                item.size = len(files[name])
                archive.addfile(item, io.BytesIO(files[name]))
    return gzip.compress(buffer.getvalue(), mtime=0)


def source_file(repository, name):
    result = subprocess.run(["git", "show", SOURCE + ":" + name], cwd=repository,
                            capture_output=True, timeout=10)
    if result.returncode:
        raise EnvironmentError("COMPONENT_PINNED_SOURCE_UNAVAILABLE")
    return result.stdout


def compose(version, baseline, baseline_sha, repository, contract):
    if version not in ("2.0.0", "3.0.0") or baseline_sha != BASE_SHA:
        raise EnvironmentError("COMPONENT_PREPARATION_INPUT_NOT_PINNED")
    # Keep the exact qualified ARM64 dependencies and common runtime. Prove
    # common code matches the pinned Platform source instead of mixing branches.
    for name in ("bridge.py", "manifest.py", "readiness.py", "runtime.py", "__main__.py"):
        if baseline[PACKAGE + name] != source_file(repository, SOURCE_PACKAGE + name):
            raise EnvironmentError("COMPONENT_BASE_RUNTIME_SOURCE_MISMATCH")
    files = dict(baseline)
    for name in list(files):
        if name.startswith(PACKAGE + "releases/") and name != PACKAGE + "releases/__init__.py":
            del files[name]
    module = "v" + version[0]
    files[PACKAGE + "releases/" + module + ".py"] = source_file(repository, SOURCE_PACKAGE + "releases/" + module + ".py")
    files[PACKAGE + "vdp_release_profile.py"] = ("from .releases." + module + " import *\n").encode()
    files[PACKAGE + "__init__.py"] = ('__version__ = "' + version + '"\n').encode()
    for name in ("provider.json", "capability-manifest.json"):
        files["config/" + name] = source_file(repository, "providers/carla-viss-kuksa/releases/" + version + "/" + name)
    if version == "3.0.0":
        files[PACKAGE + "advisory.py"] = source_file(repository, SOURCE_PACKAGE + "advisory.py")
    elif PACKAGE + "advisory.py" in files:
        raise EnvironmentError("COMPONENT_V2_CONTAINS_ADVISORY")
    capability = document(files, "config/capability-manifest.json")
    expected = next(item for item in contract["componentVersions"] if item["contractVersion"] == version)
    if capability["readPaths"] != expected["readPaths"] or len(capability["readPaths"]) != {"2.0.0": 15, "3.0.0": 23}[version]:
        raise EnvironmentError("COMPONENT_RELEASE_PATH_SET_MISMATCH")
    provider = document(files, "config/provider.json")
    if provider["semanticVersion"] != version or provider["capabilityManifestSha256"] != sha(files["config/capability-manifest.json"]):
        raise EnvironmentError("COMPONENT_RELEASE_DIGEST_MISMATCH")
    metadata = document(files, "component.json")
    metadata["version"] = version
    files["component.json"] = encoded(metadata)
    provenance = document(files, "provenance/provenance.json")
    provenance.update(semanticVersion=version, sourceRevision=SOURCE,
        buildType="democtl-qualified-base-dependency-reuse-v1",
        baselineBundleSha256=baseline_sha, qualificationScope="TELEMETRY_ONLY_ADVISORY_DEFERRED",
        buildInputs=[dict(path=name, sha256=sha(content)) for name, content in sorted(files.items())
                     if not name.startswith(("provenance/", "sbom/"))])
    # The original record's factory .27 was the qualification input, not a
    # runtime restriction. Bind this preparation explicitly to unchanged .28.
    provenance["factoryImageVersion"] = "6.1.1-maninblack.28"
    provenance["factoryImageRawSha256"] = "5154a312598e3712666e27573adee149a730c1816d712f6cdb77bddb3f54da01"
    provenance["sourceTree"] = subprocess.run(["git", "rev-parse", SOURCE + "^{tree}"], cwd=repository,
        capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    files["provenance/provenance.json"] = encoded(provenance)
    sbom = document(files, "sbom/spdx.json")
    sbom["name"] = "aosedge-vdp-component-" + version + "-linux-arm64"
    sbom["documentNamespace"] = "https://github.com/alexmaninblack/aos-vehicle-platform/sbom/vehicle-data-platform/" + version + "/" + SOURCE
    files["sbom/spdx.json"] = encoded(sbom)
    for name, data in files.items():
        if name.endswith(".py"):
            compile(data, name, "exec")
    # This slice does not pretend the target advisory manifest is runtime proof.
    # Gateway Set remains rejected; no advisory transport is activated here.
    layer_name = "vdp-" + version + "-arm64.tar.gz"
    layer = pack(files)
    config = encoded(dict(schemaVersion=2, publisher=dict(author="maninblack"), items=[dict(
        identity=dict(codename=COMPONENT, type="component", title="Vehicle Data Platform",
                      description="Telemetry qualification; advisory deferred"),
        version=version, sourceFolder="vehicle-data-platform",
        configuration=dict(runtimes=[dict(codename=COMPONENT, type="runtime")]),
        images=[dict(path=layer_name, mediaType=MEDIA_TYPE, archInfo=dict(architecture="arm64"), osInfo=dict(os="linux"))])]))
    transport = {"config.yaml": config, "vehicle-data-platform/" + layer_name: layer}
    return transport, dict(version=version, sourceRevision=SOURCE, baseBundleSha256=baseline_sha,
        payloadSha256=sha(layer), readPathCount=len(expected["readPaths"]),
        qualificationScope="TELEMETRY_ONLY", advisory="DEFERRED", deterministic=True)
