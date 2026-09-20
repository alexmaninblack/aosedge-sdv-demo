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
# Reviewed Platform checkpoint; no working-tree input is accepted. A missing
# pin blocks new V3 preparation instead of falling back to deferred V3.
PREVIOUS_ADVISORY_RUNTIME_PIN = {
    "revision": "4bc0f7e1fd9746ec8a5e612f0281c294c1dca115",
    "tree": "303bcf1b7e3cd5628757b4d9ff3255dc51821391",
    "modules": {
        "runtime.py": "4dd787652dcca4be6d3bfea1018f93d4c14a72c1e1d821d46756ff3a54c675c6",
        "advisory.py": "a9150d817b95b4aa6b9dbe5ac5a873d02f9efce02f02ff1949e22e06b7242bef",
        "advisory_transport.py": "76379cbf36121a6a9a12d689ea2e7d88cc303f5a06c56f13cafed58862c73d0a",
        "manifest.py": "94f57fd9a280d83d2d9c28ced213f5a860e46e41e6cc8ef86c3c0d70e5b8c635",
    },
}
# Older retained releases remain inspectable against their original reviewed
# pin. New preparation always uses the current complete source set.
PREVIOUS_CLOCK_STRICT_RUNTIME_PIN = {
    "revision": "fb1d2b3a2d8e0a12213990b635c873a676d5bf67",
    "tree": "024e46350de1f832708e2d12f89c28b19f3dbc4d",
    "modules": {
        "runtime.py": "7261e09690795a7f8b89981179f4c296e5f60f6c6522c0c8dcfb18c93fc506da",
        "bridge.py": "a84e8feb0bd66964400f43de6f05c947d05daa358202ed153e9ffcf7ec2d2102",
        "advisory.py": "a9150d817b95b4aa6b9dbe5ac5a873d02f9efce02f02ff1949e22e06b7242bef",
        "advisory_transport.py": "76379cbf36121a6a9a12d689ea2e7d88cc303f5a06c56f13cafed58862c73d0a",
        "manifest.py": "94f57fd9a280d83d2d9c28ced213f5a860e46e41e6cc8ef86c3c0d70e5b8c635",
    },
}
ADVISORY_RUNTIME_HISTORY = (PREVIOUS_ADVISORY_RUNTIME_PIN, PREVIOUS_CLOCK_STRICT_RUNTIME_PIN)
ADVISORY_RUNTIME_PIN = {
    "revision": "394a645664f44a922b6a54388dfac7cfe9763221",
    "tree": "fb09614830c8c9fa264d78f6df1fd74c885d8062",
    "modules": {
        **PREVIOUS_CLOCK_STRICT_RUNTIME_PIN["modules"],
        "advisory.py": "5c28f83b779f6394244cd4a6dfb4c49bafcb461b19d4dbeab996d6a7d7d55c0f",
        "manifest.py": "9788cf7c256bcee61061792e7686f8866859b57e6f236c2c50ef688ec8673259",
    },
}
# Source release gate, not a runtime fallback or an operator/UI flag. On
# 16 September the preserved staging Test passed actual selected-VDP and
# Dashboard mTLS, repeat/no-restart, and anonymous-client TLS denial. Publishing
# this payload now enables the next Safe Stop/advisory qualification gate; it
# does not claim that advisory or the future clean Factory run already passed.
ADVISORY_RUNTIME_RELEASE_ENABLED = True
ADVISORY_RUNTIME_MODULES = ("runtime.py", "bridge.py", "advisory.py", "advisory_transport.py", "manifest.py")
ADVISORY_RUNTIME_BUILD_TYPE = "democtl-reviewed-advisory-runtime-v1"
ADVISORY_CONTRACT = {
    "contractId": "aosedge-demo-typed-qm-advisory",
    "contractVersion": "1.2.0",
    "sha256": "e055578130968e69344de981634dd69a43a1b851e437fa8dcfa77771b6c1e24c",
}
# A retained payload must match its own reviewed source/contract pair, never
# the new policy merely because the operator has updated democtl.
ADVISORY_RUNTIME_CONTRACT_HISTORY = {
    pin["revision"]: {
        "contractId": "aosedge-demo-typed-qm-advisory",
        "contractVersion": "1.1.0",
        "sha256": "343e128bf9a0cac60a4f1b573315716f440accef17933fbcd9f6af49bc88300c",
    } for pin in ADVISORY_RUNTIME_HISTORY
}


def advisory_runtime_pin():
    pin = ADVISORY_RUNTIME_PIN
    if pin is None:
        raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_CHECKPOINT_REQUIRED")
    if (not isinstance(pin, dict) or set(pin) != {"revision", "tree", "modules"}
            or any(not isinstance(pin[key], str) or not re.fullmatch(r"[0-9a-f]{40}", pin[key])
                   for key in ("revision", "tree"))
            or not isinstance(pin["modules"], dict) or set(pin["modules"]) != set(ADVISORY_RUNTIME_MODULES)
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in pin["modules"].values())):
        raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_PIN_INVALID")
    return pin


def advisory_source(repository):
    """Read only the fixed reviewed commit, never the working tree or a caller ref."""
    pin = advisory_runtime_pin()
    try:
        tree = subprocess.run(["git", "rev-parse", pin["revision"] + "^{tree}"], cwd=repository,
            capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        if tree != pin["tree"]:
            raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_TREE_MISMATCH")
        files = {}
        for name in ADVISORY_RUNTIME_MODULES:
            raw = subprocess.run(["git", "show", pin["revision"] + ":" + SOURCE_PACKAGE + name],
                cwd=repository, capture_output=True, timeout=10, check=True).stdout
            if len(raw) > 1024 * 1024 or sha(raw) != pin["modules"][name]:
                raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_DIGEST_MISMATCH")
            compile(raw, name, "exec")
            files[PACKAGE + name] = raw
    except (OSError, subprocess.SubprocessError, SyntaxError, UnicodeError):
        raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_UNAVAILABLE") from None
    return files


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


def _replay_files(version, profile, baseline, baseline_sha, contract, factory, *, unsigned_source_sha=None):
    """Rebase frozen metadata without packing or changing application code."""
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
    if unsigned_source_sha is not None:
        from .component_sources import UNSIGNED_SHA
        if unsigned_source_sha != UNSIGNED_SHA[base_version]:
            raise EnvironmentError("COMPONENT_SOURCE_DIGEST_MISMATCH")
        provenance["unsignedSourceSha256"] = unsigned_source_sha
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
    return files, dict(
        version=version, contentProfile=profile, baseContentVersion=base_version,
        baseBundleSha256=baseline_sha, readPathCount=path_count,
        capabilityManifestSha256=manifest_sha, qualificationScope="TELEMETRY_ONLY",
        advisory="DEFERRED" if profile == "v3" else "NOT_APPLICABLE", deterministic=True,
        changedPayloadFiles=sorted(name for name in files if files[name] != baseline[name]))


def _transport(files, version, description, record):
    layer_name = "vdp-" + version + "-arm64.tar.gz"
    layer = pack(files)
    config = encoded(dict(schemaVersion=2, publisher=dict(author="maninblack"), items=[dict(
        identity=dict(codename=COMPONENT, type="component", title="Vehicle Data Platform", description=description),
        version=version, sourceFolder="vehicle-data-platform",
        configuration=dict(runtimes=[dict(codename=COMPONENT, type="runtime")]),
        images=[dict(path=layer_name, mediaType=MEDIA_TYPE, archInfo=dict(architecture="arm64"), osInfo=dict(os="linux"))])]))
    return {"config.yaml": config, "vehicle-data-platform/" + layer_name: layer}, dict(record, payloadSha256=sha(layer))


def replay(version, profile, baseline, baseline_sha, contract, factory, *, unsigned_source_sha=None):
    """New Cloud release, frozen functional profile; no application-code change."""
    files, record = _replay_files(version, profile, baseline, baseline_sha, contract, factory,
        unsigned_source_sha=unsigned_source_sha)
    return _transport(files, version, "Telemetry " + profile + "; advisory deferred", record)


def compose_advisory_runtime(version, baseline, baseline_sha, repository, contract, factory,
                             advisory_contract, *, unsigned_source_sha):
    """New reviewed V3 runtime; frozen profile/dependencies remain untouched."""
    pin = advisory_runtime_pin()
    if sha(advisory_contract) != ADVISORY_CONTRACT["sha256"]:
        raise EnvironmentError("COMPONENT_ADVISORY_CONTRACT_DIGEST_MISMATCH")
    modules = advisory_source(repository)
    files, record = _replay_files(version, "v3", baseline, baseline_sha, contract, factory,
        unsigned_source_sha=unsigned_source_sha)
    capability = document(files, "config/capability-manifest.json")
    if not isinstance(capability.get("contracts"), dict) or "typedQmAdvisory" not in capability["contracts"]:
        raise EnvironmentError("COMPONENT_ADVISORY_BASE_CONTRACT_MISSING")
    previous_digest = sha(files["config/capability-manifest.json"])
    capability["contracts"]["typedQmAdvisory"] = dict(ADVISORY_CONTRACT)
    files["config/capability-manifest.json"] = encoded(capability)
    manifest_sha = sha(files["config/capability-manifest.json"])
    provider = document(files, "config/provider.json")
    provider["capabilityManifestSha256"] = manifest_sha
    files["config/provider.json"] = encoded(provider)
    profile_path = PACKAGE + "releases/v3.py"
    files[profile_path] = replace_constant(files[profile_path], "MANIFEST_SHA256", previous_digest, manifest_sha)
    if any(isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ADVISORY_CONTRACT"
            for target in node.targets) for node in ast.parse(files[profile_path]).body):
        raise EnvironmentError("COMPONENT_ADVISORY_BASE_PROFILE_CHANGED")
    files[profile_path] += b"\nADVISORY_CONTRACT = " + encoded(ADVISORY_CONTRACT) + b"\n"
    files.update(modules)
    # Validate the build-selected contract constant without executing source.
    constants = {node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(files[PACKAGE + "manifest.py"]).body if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "CURRENT_ADVISORY_CONTRACT"}
    if constants.get("CURRENT_ADVISORY_CONTRACT") != ADVISORY_CONTRACT:
        raise EnvironmentError("COMPONENT_ADVISORY_RUNTIME_CONTRACT_MISMATCH")
    provenance = document(files, "provenance/provenance.json")
    provenance.update(buildType=ADVISORY_RUNTIME_BUILD_TYPE,
        baselineSourceRevision=provenance.get("sourceRevision"), sourceRevision=pin["revision"],
        sourceTree=pin["tree"], runtimeSourceModules=dict(pin["modules"]),
        typedQmAdvisory=dict(ADVISORY_CONTRACT),
        advisoryRuntimeReleaseGate=("ENABLED" if ADVISORY_RUNTIME_RELEASE_ENABLED
                                    else "PENDING_SELECTED_UNIT_MUTUAL_TLS"),
        qualificationScope="ADVISORY_RUNTIME_IMPLEMENTED_NOT_LIVE_QUALIFIED",
        buildInputs=[dict(path=name, sha256=sha(content)) for name, content in sorted(files.items())
                     if not name.startswith(("provenance/", "sbom/"))])
    files["provenance/provenance.json"] = encoded(provenance)
    sbom = document(files, "sbom/spdx.json")
    sbom["documentNamespace"] = ("https://github.com/alexmaninblack/aos-vehicle-platform/sbom/vehicle-data-platform/"
                                 + version + "/" + pin["revision"])
    files["sbom/spdx.json"] = encoded(sbom)
    allowed = set(record["changedPayloadFiles"]) | set(modules)
    if set(files) != set(baseline) | set(modules) or any(
            files[name] != baseline[name] for name in baseline.keys() - allowed):
        raise EnvironmentError("COMPONENT_ADVISORY_CHANGED_UNREVIEWED_CONTENT")
    validate_advisory_payload(files, provenance)
    record.update(sourceRevision=pin["revision"], sourceTree=pin["tree"],
        runtimeSourceModules=dict(pin["modules"]), buildType=ADVISORY_RUNTIME_BUILD_TYPE,
        typedQmAdvisory=dict(ADVISORY_CONTRACT), capabilityManifestSha256=manifest_sha,
        advisoryRuntimeReleaseGate=provenance["advisoryRuntimeReleaseGate"],
        qualificationScope="ADVISORY_RUNTIME_IMPLEMENTED_NOT_LIVE_QUALIFIED",
        advisory="IMPLEMENTED_NOT_LIVE_QUALIFIED",
        changedPayloadFiles=sorted(name for name in files if baseline.get(name) != files[name]))
    return _transport(files, version, "Telemetry v3 and typed QM advisory; live qualification pending", record)


def validate_advisory_payload(files, provenance):
    """Inspection of reviewed composition uses independent source pins, not self-claimed hashes."""
    pin = advisory_runtime_pin()
    expected_contract = ADVISORY_CONTRACT
    if provenance.get("sourceRevision") != pin["revision"]:
        pin = next((old for old in ADVISORY_RUNTIME_HISTORY
                    if old["revision"] == provenance.get("sourceRevision")), None)
        if pin is None:
            raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_PROVENANCE_MISMATCH")
        expected_contract = ADVISORY_RUNTIME_CONTRACT_HISTORY.get(pin["revision"])
        if expected_contract is None:
            raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_PROVENANCE_MISMATCH")
    if (provenance.get("buildType") != ADVISORY_RUNTIME_BUILD_TYPE
            or provenance.get("contentProfile") != "v3"
            or provenance.get("sourceRevision") != pin["revision"]
            or provenance.get("sourceTree") != pin["tree"]
            or provenance.get("runtimeSourceModules") != pin["modules"]
            or provenance.get("typedQmAdvisory") != expected_contract
            or provenance.get("advisoryRuntimeReleaseGate") not in ("ENABLED", "PENDING_SELECTED_UNIT_MUTUAL_TLS")
            or provenance.get("qualificationScope") != "ADVISORY_RUNTIME_IMPLEMENTED_NOT_LIVE_QUALIFIED"):
        raise EnvironmentError("COMPONENT_ADVISORY_SOURCE_PROVENANCE_MISMATCH")
    if any(name not in files or sha(files[name]) != pin["modules"][name.removeprefix(PACKAGE)]
           for name in (PACKAGE + module for module in pin["modules"])):
        raise EnvironmentError("COMPONENT_ADVISORY_RUNTIME_DIGEST_MISMATCH")
    if document(files, "config/capability-manifest.json").get("contracts", {}).get("typedQmAdvisory") != expected_contract:
        raise EnvironmentError("COMPONENT_ADVISORY_CAPABILITY_CONTRACT_MISMATCH")
    profile_constants = {node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(files.get(PACKAGE + "releases/v3.py", b"")).body if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "ADVISORY_CONTRACT"}
    if profile_constants.get("ADVISORY_CONTRACT") != expected_contract:
        raise EnvironmentError("COMPONENT_ADVISORY_PROFILE_CONTRACT_MISMATCH")
    actual = [dict(path=name, sha256=sha(content)) for name, content in sorted(files.items())
              if not name.startswith(("provenance/", "sbom/"))]
    if provenance.get("buildInputs") != actual:
        raise EnvironmentError("COMPONENT_ADVISORY_BUILD_INPUTS_CHANGED")


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
