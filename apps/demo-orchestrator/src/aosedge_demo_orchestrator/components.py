# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""VDP artifact operations. Fixed catalog selectors, shared by CLI and API."""

import hashlib
import io
import json
import os
import re
import tarfile
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from .environment import EnvironmentError


COMPONENT = "aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider"
MEDIA_TYPE = "application/vnd.aos.image.component.full.v1+gzip"
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_files(data):
    """Bound expansion and reject links, devices, duplicate and escaping paths."""
    if len(data) > MAX_ARCHIVE:
        raise EnvironmentError("COMPONENT_ARCHIVE_TOO_LARGE")
    files, names, total = {}, set(), 0
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r|*") as archive:
            for index, member in enumerate(archive):
                path = PurePosixPath(member.name)
                name = path.as_posix()
                if (index >= 10000 or path.is_absolute() or ".." in path.parts
                        or "\\" in name or len(name) > 512 or any(ord(c) < 32 for c in name)
                        or not (member.isdir() or member.isfile())):
                    raise EnvironmentError("COMPONENT_ARCHIVE_UNSAFE")
                if name == "." and member.isdir():
                    continue
                if name in names:
                    raise EnvironmentError("COMPONENT_ARCHIVE_DUPLICATE")
                names.add(name)
                if member.isdir():
                    continue
                total += member.size
                if member.size < 0 or total > MAX_EXPANDED:
                    raise EnvironmentError("COMPONENT_EXPANSION_LIMIT")
                stream = archive.extractfile(member)
                content = stream.read(member.size + 1)
                if len(content) != member.size:
                    raise EnvironmentError("COMPONENT_ARCHIVE_TRUNCATED")
                files[name] = content
    except (tarfile.TarError, EOFError, OSError):
        raise EnvironmentError("COMPONENT_ARCHIVE_INVALID") from None
    if any(parent.as_posix() in files for name in files for parent in PurePosixPath(name).parents):
        raise EnvironmentError("COMPONENT_ARCHIVE_PATH_CONFLICT")
    return files


def document(files, name):
    # The qualified producer emits JSON (a YAML subset) in config.yaml.
    # Do not guess another producer's YAML schema or silently change metadata.
    try:
        content = files[name]
        if len(content) > 1024 * 1024:
            raise ValueError()
        value = json.loads(content)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (KeyError, ValueError, UnicodeError):
        raise EnvironmentError("COMPONENT_METADATA_INVALID:" + name) from None


class ComponentService:
    def __init__(self, environment):
        self.environment = environment
        self.catalog = environment.catalog
        self.root = self.catalog.project / "components/vehicle-data-provider"

    def _directory(self, version):
        if not isinstance(version, str) or not VERSION.fullmatch(version) or len(version) > 32:
            raise EnvironmentError("COMPONENT_VERSION_INVALID")
        path = self.root / version
        if self.root.is_symlink() or path.is_symlink() or not path.resolve().is_relative_to(self.catalog.project.resolve()):
            raise EnvironmentError("COMPONENT_OUTSIDE_CATALOG")
        return path

    def list(self):
        items = []
        for directory in sorted(self.root.glob("*")):
            if not VERSION.fullmatch(directory.name):
                continue
            try:
                path = self._bundle(directory.name)
                items.append(dict(version=directory.name, bundle=path.name, sizeBytes=path.stat().st_size))
            except EnvironmentError as error:
                items.append(dict(version=directory.name, reason=str(error)))
        return {"components": items}

    def _bundle(self, version):
        directory = self._directory(version)
        candidates = [directory / ("vdp-" + version + "-deployment-bundle.tar.gz"),
                      directory / ("aosedge-vdp-component-" + version + "-linux-arm64.unsigned.tar.gz")]
        found = [p for p in candidates if p.exists() or p.is_symlink()]
        if not found:
            raise EnvironmentError("COMPONENT_BUNDLE_NOT_FOUND")
        # Signed and unsigned are deliberately separate representations; prefer
        # the published representation for inspection when both are retained.
        path = found[0]
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
            raise EnvironmentError("COMPONENT_BUNDLE_UNSAFE")
        return path

    def _inspect(self, version):
        path = self._bundle(version)
        raw = path.read_bytes()
        outer = archive_files(raw)
        signed = "package.sign" in outer
        if signed and set(outer) != {"batch.tar.gz", "config.yaml", "package.sign"}:
            raise EnvironmentError("COMPONENT_SIGNED_ENVELOPE_INVALID")
        inner = archive_files(outer["batch.tar.gz"]) if signed else outer
        config = document(inner, "config.yaml")
        items = config.get("items")
        if config.get("schemaVersion") != 2 or not isinstance(items, list) or len(items) != 1:
            raise EnvironmentError("COMPONENT_ENVELOPE_SCHEMA_INVALID")
        item = items[0]
        if item.get("identity", {}).get("type") != "component" or item.get("identity", {}).get("codename") != COMPONENT:
            raise EnvironmentError("COMPONENT_IDENTITY_MISMATCH")
        images = item.get("images")
        if not isinstance(images, list) or len(images) != 1:
            raise EnvironmentError("COMPONENT_IMAGE_COUNT_INVALID")
        image = images[0]
        layer_path = str(PurePosixPath(item.get("sourceFolder", "")) / image.get("path", ""))
        if layer_path not in inner:
            raise EnvironmentError("COMPONENT_PAYLOAD_MUST_BE_FILE")
        if set(inner) != {"config.yaml", layer_path}:
            raise EnvironmentError("COMPONENT_ENVELOPE_MEMBERS_INVALID")
        payload = archive_files(inner[layer_path])
        metadata = document(payload, "component.json")
        provider = document(payload, "config/provider.json")
        capability = document(payload, "config/capability-manifest.json")
        problems = []
        if item.get("version") != version or metadata.get("version") != version:
            problems.append("COMPONENT_VERSION_MISMATCH")
        if provider.get("semanticVersion") != version or capability.get("semanticVersion") != version:
            problems.append("COMPONENT_RELEASE_VERSION_MISMATCH")
        if provider.get("capabilityManifestSha256") != sha(payload["config/capability-manifest.json"]):
            problems.append("COMPONENT_CAPABILITY_DIGEST_MISMATCH")
        if metadata.get("configuration") != "config/provider.json" or metadata.get("runtimeInterface") != 1:
            problems.append("COMPONENT_RUNTIME_INTERFACE_MISMATCH")
        if image.get("mediaType") != MEDIA_TYPE:
            problems.append("COMPONENT_MEDIA_TYPE_MISMATCH")
        if image.get("archInfo", {}).get("architecture") != "arm64" or metadata.get("architecture") != "arm64":
            problems.append("COMPONENT_ARCHITECTURE_MISMATCH")
        if item.get("configuration", {}).get("runtimes") != [{"codename": COMPONENT, "type": "runtime"}]:
            problems.append("COMPONENT_RUNTIME_BINDING_MISMATCH")
        if metadata.get("entrypoint") not in payload:
            problems.append("COMPONENT_ENTRYPOINT_MISSING")
        provenance = document(payload, "provenance/provenance.json") if "provenance/provenance.json" in payload else {}
        if int(version.split(".")[0]) >= 4:
            import ast
            from .component_build import PROFILE_BASES, PACKAGE
            profile = provenance.get("contentProfile")
            if profile not in PROFILE_BASES or provenance.get("semanticVersion") != version:
                problems.append("COMPONENT_CONTENT_PROFILE_MISMATCH")
            else:
                base_version, base_sha, module, _ = PROFILE_BASES[profile]
                if (provenance.get("baseContentVersion") != base_version
                        or provenance.get("baselineBundleSha256") != base_sha):
                    problems.append("COMPONENT_CONTENT_PROFILE_MISMATCH")
                for name, expected_values in (
                    (PACKAGE + "releases/" + module + ".py", {"VERSION": version,
                        "MANIFEST_SHA256": sha(payload["config/capability-manifest.json"])}),
                    (PACKAGE + "__init__.py", {"__version__": version})):
                    assignments = {node.targets[0].id: ast.literal_eval(node.value)
                        for node in ast.parse(payload[name]).body if isinstance(node, ast.Assign)
                        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id in expected_values}
                    if assignments != expected_values:
                        problems.append("COMPONENT_RUNTIME_PROFILE_METADATA_MISMATCH")
        result = dict(version=version, bundle=path.name, sha256=sha(raw), sizeBytes=len(raw),
            signedEnvelope=signed, signatureVerification="NOT_PERFORMED",
            componentId=COMPONENT, outerVersion=item.get("version"), innerVersion=metadata.get("version"),
            mediaType=image.get("mediaType"), payloadFile=layer_path, payloadSha256=sha(inner[layer_path]),
            payloadFileCount=len(payload), providerVersion=provider.get("semanticVersion"),
            capabilityVersion=capability.get("semanticVersion"),
            capabilityManifestSha256=sha(payload["config/capability-manifest.json"]),
            readPathCount=len(capability.get("readPaths", [])),
            advisoryEndpointCount=len(capability.get("advisoryEndpoints", [])), problems=problems,
            contentProfile=provenance.get("contentProfile"), baseContentVersion=provenance.get("baseContentVersion"),
            claim="Packaging inspection only; not signature, runtime or Cloud qualification.")
        return result, payload

    def inspect(self, version):
        return self._inspect(version)[0]

    def _worker(self, action, **values):
        from .status import load_configuration
        config = load_configuration(self.environment.root)
        profile = config["cloudProfiles"].get("oem-delivery")
        if not profile or profile["expectedRole"] != "oem":
            raise EnvironmentError("OEM_DELIVERY_PROFILE_REQUIRED")
        credential = profile["credential"]
        if credential.is_symlink() or not credential.is_file() or credential.stat().st_mode & 0o077:
            raise EnvironmentError("OEM_CREDENTIAL_MISSING_OR_UNSAFE")
        owner = values.get("ownerId") or profile.get("expectedOwnerId")
        if (values.get("ownerId") and profile.get("expectedOwnerId")
                and values["ownerId"] != profile["expectedOwnerId"]):
            raise EnvironmentError("COMPONENT_OEM_OWNER_CHANGED")
        request = dict(values, action=action, credential=str(credential), ownerId=owner)
        try:
            process = subprocess.run([str(config["cloudPython"]), "-I", "-B",
                str(Path(__file__).with_name("component_worker.py"))], input=json.dumps(request),
                text=True, capture_output=True, timeout=30 if values.get("purpose") == "overview" else 90, env={"PATH": os.defpath})
            if process.returncode or len(process.stdout) > 262144:
                raise EnvironmentError("COMPONENT_WORKER_RESULT_UNAVAILABLE")
            result = json.loads(process.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise EnvironmentError("COMPONENT_WORKER_RESULT_UNAVAILABLE") from None
        if not result.get("ok"):
            raise EnvironmentError(result.get("reason", "COMPONENT_WORKER_FAILED"))
        return result["data"]

    def verify(self, version):
        inspected = self.inspect(version)
        if inspected["problems"] or not inspected["signedEnvelope"]:
            raise EnvironmentError("COMPONENT_SIGNED_VALID_PACKAGE_REQUIRED")
        return self._worker("verify", bundle=str(self._bundle(version)), expectedSha256=inspected["sha256"])

    def _cloud_scope(self, version, state=None):
        from .status import read_json
        from .environment import JOURNAL
        self._directory(version)
        state = state or read_json(self.environment.root / JOURNAL)
        if "test" not in state["vehicles"] or set(state["vehicles"]) - {"test", "production"}:
            raise EnvironmentError("COMPONENT_TEST_PRODUCTION_SCOPE_REQUIRED")
        vehicles = {role: {key: value.get(key) for key in ("unitId", "unitSetId", "systemUid")}
                    for role, value in state["vehicles"].items()}
        record = state.get("componentOperations", {}).get(version, {})
        scope = dict(version=version, vehicles=vehicles, deploymentId=record.get("deploymentId"))
        batch_id = record.get("batchId") or record.get("approve", {}).get("response", {}).get("batchId")
        if batch_id:
            scope["batchId"] = batch_id
        if record.get("roleSetIds"):
            scope["roleSetIds"] = record["roleSetIds"]
        if all(not item.get("unitId") for item in state["vehicles"].values()):
            from .component_runtime import FACTORY_VERSION
            if (set(vehicles) != {"test", "production"} or state.get("stage") not in ("MANUFACTURED", "LOCAL_STOPPED")
                    or state.get("factory", {}).get("version") != FACTORY_VERSION
                    or state.get("currentVehicle") is not None
                    or any(item.get("cloud") or item.get("systemUid") or item.get("nodeId")
                           for item in state["vehicles"].values())):
                raise EnvironmentError("COMPONENT_PRISTINE_DUAL_FACTORY_REQUIRED")
            scope["preProvisioning"] = True
        if "production" not in vehicles:
            binding = state.get("cloudBinding", {})
            if not binding.get("sets", {}).get("production"):
                raise EnvironmentError("COMPONENT_PRODUCTION_GUARD_BINDING_REQUIRED")
            scope["productionSetId"] = binding["sets"]["production"]
        return scope

    def cloud_status(self, version=None):
        if version is None:
            from .status import read_json
            from .environment import JOURNAL
            state = read_json(self.environment.root / JOURNAL)
            identity = state.get("vehicles", {}).get("test", {})
            if not all(identity.get(key) for key in ("unitId", "systemUid", "unitSetId")):
                raise EnvironmentError("COMPONENT_TEST_CLOUD_BINDING_REQUIRED")
            # The journal selects the exact owned Unit, never supplies its
            # displayed state. No guest access or local bundle inspection.
            return self._worker("cloud-status", purpose="overview", vehicles={"test": {
                key: identity[key] for key in ("unitId", "systemUid", "unitSetId")}})
        return self._worker("cloud-status", **self._verification_scope(version))

    def logs(self, target):
        return self.status(target, action="component-logs")

    def diagnose(self, target):
        return self.status(target, action="component-diagnose")

    def sm_status(self, target):
        return self.status(target, action="component-sm-status")

    def schema_apply(self, target):
        return self._schema_change(target, "apply")

    def schema_remove(self, target):
        return self._schema_change(target, "remove")

    def _schema_change(self, target, action):
        from .environment import JOURNAL, atomic_json
        from .status import read_json, now
        from .vm import VMService
        from .source import SourceDriver
        from .source_guest import VSS_PATHS
        if target != "test":
            raise EnvironmentError("COMPONENT_VSS_TEST_ONLY")
        with self.environment._writer():
            state = read_json(self.environment.root / JOURNAL)
            contract = read_json(self.environment.root / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json")
            versions = {item["contractVersion"]: set(item["readPaths"]) for item in contract["componentVersions"]}
            if versions["3.0.0"] - versions["2.0.0"] != set(VSS_PATHS):
                raise EnvironmentError("COMPONENT_VSS_CONTRACT_CHANGED")
            if state.get("currentVehicle") is not None:
                raise EnvironmentError("COMPONENT_VSS_DETACH_SIMULATION_FIRST")
            record = state.setdefault("componentSchema", {})
            record.update(target="test", localVmId=state["vehicles"]["test"]["localVmId"],
                          action=action, state="ATTEMPT_STARTED", startedAt=now())
            atomic_json(self.environment.root / JOURNAL, state)
            driver = SourceDriver(VMService(self.environment))
            try:
                with driver.operation(timeout=25):
                    result = driver.guest(state, "test", "component-schema-" + action,
                        target="test", additionalPaths=list(VSS_PATHS))
            except EnvironmentError as error:
                record.update(state="RECONCILIATION_REQUIRED", reason=str(error))
                atomic_json(self.environment.root / JOURNAL, state)
                raise
            record.update(state=result["state"], result=result, confirmedAt=now())
            record.pop("reason", None)
            atomic_json(self.environment.root / JOURNAL, state)
            return result

    def status(self, target, action="component-status"):
        from .environment import JOURNAL
        from .status import read_json
        from .vm import VMService
        from .source import SourceDriver
        if target not in ("test", "production"):
            raise EnvironmentError("COMPONENT_STATUS_SINGLE_ROLE_REQUIRED")
        state = read_json(self.environment.root / JOURNAL)
        driver = SourceDriver(VMService(self.environment))
        extra = {}
        if action == "component-diagnose":
            contract = read_json(self.environment.root / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json")
            extra["readPaths"] = next(item["readPaths"] for item in contract["componentVersions"] if item["contractVersion"] == "3.0.0")
        with driver.operation(timeout=25):
            return dict(target=target, **driver.guest(state, target, action, **extra))

    def upload(self, version):
        """Publish once to verification recipients; approval is not a stage."""
        from .status import read_json, now
        from .environment import JOURNAL, atomic_json
        from .component_build import PROFILE_BASES, version_number
        with self.environment._writer():
            state = read_json(self.environment.root / JOURNAL)
            scope = self._verification_scope(version, state)
            previous = state.get("componentOperations", {}).get(version, {})
            if previous.get("upload", {}).get("attemptStarted") and not previous.get("deploymentId"):
                raise EnvironmentError("COMPONENT_UPLOAD_RECONCILIATION_REQUIRED")
            # An exact response ID can be reconciled without opening an archive,
            # contacting a guest or issuing a second upload.
            if previous.get("deploymentId"):
                observed = self._worker("cloud-status", **scope)
                stage = observed["publication"]["stage"]
                previous["publication"] = observed["publication"]
                if stage == "READY":
                    previous["upload"].update(state="CONFIRMED", confirmedAt=now())
                elif previous.get("publicationPath") == "VERIFICATION_TEST":
                    previous["upload"]["state"] = "RESPONDED"
                atomic_json(self.environment.root / JOURNAL, state)
                return dict(observed, noOp=stage == "READY", reconciled=True)
            prepared = read_json(self._directory(version) / "prepared.json")
            if (prepared.get("version") != version or prepared.get("contentProfile") not in PROFILE_BASES
                    or version_number(version) < (4, 0, 0)):
                raise EnvironmentError("COMPONENT_PUBLICATION_VERSION_NOT_AUTHORIZED")
            inspected, files = self._inspect(version)
            if inspected["problems"] or not inspected["signedEnvelope"]:
                raise EnvironmentError("COMPONENT_SIGNED_VALID_PACKAGE_REQUIRED")
            if inspected.get("contentProfile") != prepared["contentProfile"]:
                raise EnvironmentError("COMPONENT_PREPARED_PROFILE_MISMATCH")
            self._factory_support(state, files)
            operations = state.get("componentOperations", {})
            outstanding = [(number, record) for number, record in operations.items()
                if number != version and record.get("upload", {}).get("attemptStarted")]
            if any(not record.get("deploymentId") for _, record in outstanding):
                raise EnvironmentError("COMPONENT_PREVIOUS_PUBLICATION_RECONCILIATION_REQUIRED")
            if outstanding:
                latest, record = max(outstanding, key=lambda item: version_number(item[0]))
                scope["previousPublication"] = dict(version=latest, deploymentId=record["deploymentId"])
            before = self._worker("cloud-status", **scope, purpose="upload")
            if before["versions"] or before["deploymentBundles"]:
                raise EnvironmentError("COMPONENT_VERSION_ALREADY_IN_CLOUD")
            if before.get("latestPublishedVersion") and version_number(version) <= version_number(before["latestPublishedVersion"]):
                raise EnvironmentError("COMPONENT_PUBLICATION_MUST_INCREMENT_VERSION")
            if outstanding:
                prior = before.get("previousPublication", {})
                if prior.get("stage") != "READY":
                    raise EnvironmentError("COMPONENT_PREVIOUS_PUBLICATION_NOT_READY")
                if not scope["preProvisioning"] and not any(
                        (row.get("installed_component") or {}).get("version") == latest
                        for row in before.get("test", {}).get("components", [])):
                    raise EnvironmentError("COMPONENT_PREVIOUS_UPDATE_NOT_INSTALLED")
            if any(row.get("pending_component") or row.get("pending_component_error")
                   for row in before.get("test", {}).get("components", [])):
                raise EnvironmentError("COMPONENT_OTHER_UPDATE_PENDING_OR_FAILED")
            if before.get("recipientCoverage", {}).get("complete") is not True or not before.get("ownerId"):
                raise EnvironmentError("COMPONENT_VERIFICATION_RECIPIENT_COVERAGE_REQUIRED")
            record = state.setdefault("componentOperations", {}).setdefault(version, {})
            record.update(sha256=inspected["sha256"], target="test", publicationPath="VERIFICATION_TEST",
                          ownerId=before["ownerId"], recipientCoverage=before["recipientCoverage"])
            record["upload"] = dict(attemptStarted=True, startedAt=now(), state="UNCERTAIN")
            atomic_json(self.environment.root / JOURNAL, state)
            response = self._worker("upload", **dict(scope, ownerId=before["ownerId"],
                bundle=str(self._bundle(version)), expectedSha256=inspected["sha256"]))
            if response.get("httpStatus") != 201 or not response.get("deploymentId"):
                raise EnvironmentError("COMPONENT_UPLOAD_RESPONSE_UNCERTAIN")
            record["deploymentId"] = response["deploymentId"]
            record["upload"].update(state="RESPONDED", response=response)
            record["publication"] = dict(stage="ACCEPTED", deploymentId=response["deploymentId"],
                bundleState=response.get("state"), buildInfo=response.get("buildInfo"), observedAt=now())
            problems = []
            if str(response.get("state") or "").lower() == "error":
                record["publication"].update(stage="ERROR", reason="COMPONENT_CLOUD_PROCESSING_ERROR")
                problems.append("COMPONENT_CLOUD_PROCESSING_ERROR")
            atomic_json(self.environment.root / JOURNAL, state)
            return dict(response, publication=record["publication"], requestAccepted=True, noOp=False, problems=problems)

    def _verification_scope(self, version, state=None):
        from .environment import JOURNAL
        from .status import read_json
        self._directory(version)
        state = state if state is not None else read_json(self.environment.root / JOURNAL)
        identity = state.get("vehicles", {}).get("test")
        if not isinstance(identity, dict) or not identity.get("localVmId"):
            raise EnvironmentError("COMPONENT_OWNED_TEST_REQUIRED")
        fields = ("unitId", "systemUid", "unitSetId")
        provisioned = all(identity.get(key) for key in fields)
        if ((not provisioned and (any(identity.get(key) for key in fields) or identity.get("cloud")))
                or (identity.get("cloud") or {}).get("lifecycle") in ("DEPROVISIONED", "DELETED")):
            raise EnvironmentError("COMPONENT_TEST_CLOUD_BINDING_INCOMPLETE_OR_RETIRED")
        record = state.get("componentOperations", {}).get(version, {})
        owner = state.get("cloudBinding", {}).get("ownerId") or record.get("ownerId")
        if (record.get("ownerId") and owner != record["ownerId"]):
            raise EnvironmentError("COMPONENT_OEM_OWNER_CHANGED")
        return dict(version=version, verificationTest=True, preProvisioning=not provisioned, ownerId=owner,
                    deploymentId=record.get("deploymentId"),
                    vehicles={"test": {key: identity[key] for key in fields}} if provisioned else {})

    def _factory_support(self, state, files):
        """Verify the owned copy receipt and catalog declaration, not a guest."""
        from .environment import MANIFEST, digest
        from .images import ImageError
        from .status import read_json
        factory = state.get("factory", {})
        path = self.environment.root / MANIFEST
        if (factory.get("manifestPath") != MANIFEST or path.is_symlink() or not path.is_file()
                or path.stat().st_size > 65536 or digest(path) != factory.get("manifestSha256")):
            raise EnvironmentError("COMPONENT_FACTORY_RECEIPT_NOT_PROVEN")
        manifest = read_json(path)
        if (manifest.get("kind") != "democtl.factory-copy" or manifest.get("schemaVersion") != 1
                or any(manifest.get("image", {}).get(key) != factory.get(key) for key in ("path", "version", "sha256", "format"))):
            raise EnvironmentError("COMPONENT_FACTORY_RECEIPT_MISMATCH")
        provenance = document(files, "provenance/provenance.json")
        if (provenance.get("factoryImageRawSha256") != factory["sha256"]
                or provenance.get("factoryImageVersion") != factory["version"]):
            raise EnvironmentError("COMPONENT_FACTORY_PROVENANCE_MISMATCH")
        support = getattr(self.catalog, "component_support", None)
        if support is None:
            raise EnvironmentError("COMPONENT_FACTORY_COMPATIBILITY_NOT_DECLARED")
        try:
            return support(manifest.get("sourceSelector"), factory["sha256"], COMPONENT,
                           document(files, "config/capability-manifest.json")["readPaths"])
        except ImageError as error:
            raise EnvironmentError(str(error)) from None

    def approve(self, version):
        return self._publish("approve", version)

    def unapprove(self, version):
        return self._publish("unapprove", version)

    def send(self, version):
        """One explicit Test-only request for an existing approved component."""
        from .status import read_json, now
        from .environment import JOURNAL, atomic_json
        from .component_cloud import guard, batch_guard, send_observed
        from .unit_cloud import CloudFailure
        if version not in ("2.0.0", "3.0.0"):
            raise EnvironmentError("COMPONENT_PUBLICATION_VERSION_NOT_AUTHORIZED")
        with self.environment._writer():
            verified = self.verify(version)
            state = read_json(self.environment.root / JOURNAL)
            scope = self._cloud_scope(version, state)
            if scope.get("preProvisioning"):
                raise EnvironmentError("COMPONENT_SEND_REQUIRES_PROVISIONED_UNIT")
            before = self._worker("cloud-status", **scope)
            try:
                guard(before)
                if len(before["verificationBatches"]) != 1:
                    raise CloudFailure("COMPONENT_VERIFICATION_BATCH_NOT_READY_OR_AMBIGUOUS")
                batch = before["verificationBatches"][0]
                batch_guard(batch, scope, before["ownerId"])
                if (batch.get("approval_states") or {}).get("arm64", {}).get("is_approved") is not True:
                    raise CloudFailure("COMPONENT_SEND_REQUIRES_APPROVAL")
            except CloudFailure as error:
                raise EnvironmentError(str(error)) from None
            versions = before["versions"]
            bundles = before["deploymentBundles"]
            if (len(versions) != 1 or versions[0].get("state") != "Ready"
                    or versions[0].get("is_fake") is not False
                    or len(bundles) != 1 or bundles[0].get("state") != "done"):
                raise EnvironmentError("COMPONENT_SEND_ARTIFACT_NOT_READY_OR_AMBIGUOUS")
            values = dict(unitId=scope["vehicles"]["test"]["unitId"], updateComponentId=versions[0]["id"])
            record = state.setdefault("componentOperations", {}).setdefault(version, {})
            if record.get("sha256", verified["sha256"]) != verified["sha256"]:
                raise EnvironmentError("COMPONENT_PUBLICATION_DIGEST_CHANGED")
            if record.get("productionBefore", before["production"]) != before["production"]:
                raise EnvironmentError("COMPONENT_PRODUCTION_GUARD_CHANGED")
            previous = record.get("send", {})
            if previous and any(previous.get(key) != value for key, value in values.items()):
                raise EnvironmentError("COMPONENT_SEND_IDENTITY_CHANGED")
            observed = send_observed(before, values["updateComponentId"])
            if observed or previous.get("state") == "CONFIRMED":
                record["send"] = dict(previous, **values, state="CONFIRMED", confirmedAt=now())
                atomic_json(self.environment.root / JOURNAL, state)
                return dict(**values, noOp=True, requestAccepted=True,
                    deliveryObservation=observed or "PREVIOUSLY_CONFIRMED_REQUEST")
            if previous.get("attemptStarted"):
                raise EnvironmentError("COMPONENT_SEND_RECONCILIATION_REQUIRED")
            if any(item.get("pending_component") for item in before["test"].get("components", [])):
                raise EnvironmentError("COMPONENT_SEND_OTHER_UPDATE_PENDING")
            record.update(sha256=verified["sha256"], deploymentId=bundles[0]["id"],
                target="test", qualificationScope="TELEMETRY_ONLY")
            record.setdefault("productionBefore", before["production"])
            record["send"] = dict(**values, attemptStarted=True, startedAt=now(), state="UNCERTAIN")
            atomic_json(self.environment.root / JOURNAL, state)
            result = self._worker("send", **scope, **values)
            record["send"].update(state="RESPONDED", response=result)
            atomic_json(self.environment.root / JOURNAL, state)
            after = self._worker("cloud-status", **self._cloud_scope(version, state))
            if after["production"] != record["productionBefore"]:
                raise EnvironmentError("COMPONENT_PRODUCTION_GUARD_CHANGED")
            observed = send_observed(after, values["updateComponentId"])
            if result.get("requestAccepted") is not True or not observed:
                raise EnvironmentError("COMPONENT_SEND_RECONCILIATION_REQUIRED")
            record["send"].update(state="CONFIRMED", confirmedAt=now(), deliveryObservation=observed)
            atomic_json(self.environment.root / JOURNAL, state)
            return dict(result, productionUnchanged=True, deliveryObservation=observed)

    def _publish(self, action, version):
        """Retained explicit engineering approval; never a publication path."""
        from .status import read_json, now
        from .environment import JOURNAL, atomic_json
        from .component_cloud import batch_guard, reconcile_list_guard
        from .unit_cloud import CloudFailure
        if action not in ("approve", "unapprove"):
            raise EnvironmentError("COMPONENT_EXPLICIT_APPROVAL_ACTION_REQUIRED")
        if version not in ("2.0.0", "3.0.0"):
            from .component_build import PROFILE_BASES, version_number
            prepared = read_json(self._directory(version) / "prepared.json")
            if (version_number(version) < (4, 0, 0) or prepared.get("version") != version
                    or prepared.get("contentProfile") not in PROFILE_BASES):
                raise EnvironmentError("COMPONENT_PUBLICATION_VERSION_NOT_AUTHORIZED")
        with self.environment._writer():
            state = read_json(self.environment.root / JOURNAL)
            previous = state.get("componentOperations", {}).get(version, {})
            # Approval targets an already uploaded Cloud batch, not a local
            # archive. Do not unpack/hash/verify that archive again for PATCH.
            verified = dict(sha256=previous.get("sha256"))
            scope = self._cloud_scope(version, state)
            if scope.get("preProvisioning") and (action != "approve"
                    or version in ("2.0.0", "3.0.0") or prepared.get("contentProfile") != "v1"):
                raise EnvironmentError("COMPONENT_PREPROVISION_V1_ONLY")
            before = self._worker("cloud-status", **scope, purpose=action)
            record = state.setdefault("componentOperations", {}).setdefault(version, {})
            if reconcile_list_guard(record, before):
                atomic_json(self.environment.root / JOURNAL, state)
            if scope.get("preProvisioning") and "testSet" in before:
                record["roleSetIds"] = {role: before[role + "Set"]["id"] for role in ("test", "production")}
            if record.get("sha256", verified["sha256"]) != verified["sha256"]:
                raise EnvironmentError("COMPONENT_PUBLICATION_DIGEST_CHANGED")
            if "productionBefore" in record and before["production"] != record["productionBefore"]:
                raise EnvironmentError("COMPONENT_PRODUCTION_GUARD_CHANGED")
            if len(before["verificationBatches"]) != 1:
                raise EnvironmentError("COMPONENT_VERIFICATION_BATCH_NOT_READY_OR_AMBIGUOUS")
            batch = before["verificationBatches"][0]
            try:
                batch_guard(batch, scope, before["ownerId"])
            except CloudFailure as error:
                raise EnvironmentError(str(error)) from None
            if not record.get("deploymentId"):
                bundles = before["deploymentBundles"]
                if len(bundles) != 1 or bundles[0]["state"] != "done":
                    raise EnvironmentError("COMPONENT_DEPLOYMENT_NOT_READY_OR_AMBIGUOUS")
                record["deploymentId"] = bundles[0]["id"]
            desired = action == "approve"
            if (batch.get("approval_states") or {}).get("arm64", {}).get("is_approved") is desired:
                record.setdefault(action, {}).update(state="CONFIRMED", confirmedAt=now(),
                    response=dict(batchId=batch["id"], approved=desired))
                atomic_json(self.environment.root / JOURNAL, state)
                return dict(batchId=batch["id"], approved=desired, noOp=True)
            values = dict(batchId=batch["id"])
            record["batchId"] = batch["id"]
            if record.get(action, {}).get("attemptStarted"):
                if record[action].get("state") != "CONFIRMED":
                    raise EnvironmentError("COMPONENT_" + action.upper() + "_RECONCILIATION_REQUIRED")
                record.setdefault("approvalHistory", []).append(dict(record[action], action=action))
            record.update(sha256=verified["sha256"], target="test", qualificationScope="TELEMETRY_ONLY")
            intent = dict(attemptStarted=True, startedAt=now(), state="UNCERTAIN", **values)
            # Local path is not a Cloud identity; journal only the digest/IDs.
            intent.pop("bundle", None)
            record[action] = intent
            record.setdefault("productionBefore", before["production"])
            atomic_json(self.environment.root / JOURNAL, state)
            result = self._worker(action, **dict(scope, **values))
            record[action].update(state="RESPONDED", response=result)
            atomic_json(self.environment.root / JOURNAL, state)
            confirmation = dict(self._cloud_scope(version, state), purpose="confirm")
            after = self._worker("cloud-status", **confirmation)
            if after["production"] != record["productionBefore"]:
                raise EnvironmentError("COMPONENT_PRODUCTION_GUARD_CHANGED")
            if action in ("approve", "unapprove"):
                batches = after.get("verificationBatches", [])
                if (result.get("approved") is not (action == "approve") or len(batches) != 1
                        or batches[0]["id"] != values["batchId"]
                        or (batches[0].get("approval_states") or {}).get("arm64", {}).get("is_approved") is not (action == "approve")):
                    raise EnvironmentError("COMPONENT_APPROVAL_NOT_CONFIRMED")
            record[action].update(state="CONFIRMED", confirmedAt=now())
            atomic_json(self.environment.root / JOURNAL, state)
            return dict(result, productionUnchanged=True)

    def prepare(self, version, content_profile=None):
        from .component_build import compose, replay, pack, encoded, PROFILE_BASES, version_number
        from .status import read_json
        from .environment import JOURNAL
        with self.environment._writer():
            from .releases import ReleaseContinuity
            continuity = ReleaseContinuity(self.environment)
            if version is None:
                if content_profile not in PROFILE_BASES:
                    raise EnvironmentError("COMPONENT_CONTENT_PROFILE_REQUIRED")
                cloud = self._worker("release-catalog")
                observed = [item["version"] for item in self.list()["components"]] + cloud["versions"]
                version = continuity.reserve("vdp", observed)
            destination = self._directory(version)
            if destination.exists() or destination.is_symlink():
                raise EnvironmentError("COMPONENT_PREPARE_DESTINATION_EXISTS")
            if content_profile is not None and content_profile not in PROFILE_BASES:
                raise EnvironmentError("COMPONENT_REPLAY_PROFILE_OR_VERSION_INVALID")
            if version not in ("2.0.0", "3.0.0") and content_profile is None:
                raise EnvironmentError("COMPONENT_CONTENT_PROFILE_REQUIRED")
            continuity.remember("vdp", version)
            if content_profile is not None:
                previous = [version_number(item.name) for item in self.root.iterdir()
                            if item.is_dir() and VERSION.fullmatch(item.name)]
                if previous and version_number(version) <= max(previous):
                    raise EnvironmentError("COMPONENT_PREPARATION_MUST_INCREMENT_VERSION")
            base_version = PROFILE_BASES[content_profile][0] if content_profile is not None else "1.0.16"
            self.verify(base_version)
            inspected, files = self._inspect(base_version)
            contract = read_json(self.environment.root / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json")
            repository = self.environment.root.parent / "aos-vehicle-platform"
            if content_profile is None:
                first, record = compose(version, files, inspected["sha256"], repository, contract)
                second, repeat = compose(version, files, inspected["sha256"], repository, contract)
            else:
                factory = read_json(self.environment.root / JOURNAL)["factory"]
                first, record = replay(version, content_profile, files, inspected["sha256"], contract, factory)
                second, repeat = replay(version, content_profile, files, inspected["sha256"], contract, factory)
            unsigned = pack(first)
            if unsigned != pack(second) or record != repeat:
                raise EnvironmentError("COMPONENT_PREPARATION_NOT_DETERMINISTIC")
            record["preparedSha256"] = sha(unsigned)
            record["files"] = {name: sha(data) for name, data in first.items()}
            with tempfile.TemporaryDirectory(prefix=".prepare-", dir=self.root) as temporary:
                stage = Path(temporary) / "candidate"
                stage.mkdir(mode=0o700)
                for name, data in first.items():
                    path = stage.joinpath(*PurePosixPath(name).parts)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                (stage / ("aosedge-vdp-component-" + version + "-linux-arm64.unsigned.tar.gz")).write_bytes(unsigned)
                (stage / "prepared.json").write_bytes(encoded(record))
                os.rename(stage, destination)
            return record

    def sign(self, version):
        from .status import read_json
        from .environment import atomic_json
        with self.environment._writer():
            directory = self._directory(version)
            record = read_json(directory / "prepared.json")
            inspected = self.inspect(version)
            if inspected["problems"]:
                raise EnvironmentError("COMPONENT_PACKAGING_INVALID")
            if inspected["signedEnvelope"]:
                return dict(self.verify(version), noOp=True)
            if inspected["sha256"] != record["preparedSha256"]:
                raise EnvironmentError("COMPONENT_PREPARED_DIGEST_CHANGED")
            inputs = archive_files(self._bundle(version).read_bytes())
            if record["files"] != {name: sha(data) for name, data in inputs.items()}:
                raise EnvironmentError("COMPONENT_SIGN_INPUT_CHANGED")
            for name, expected in record["files"].items():
                path = directory.joinpath(*PurePosixPath(name).parts)
                if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink() or sha(path.read_bytes()) != expected:
                    raise EnvironmentError("COMPONENT_SIGN_INPUT_CHANGED")
            signed = directory / ("vdp-" + version + "-deployment-bundle.tar.gz")
            if signed.exists() or signed.is_symlink():
                raise EnvironmentError("COMPONENT_SIGN_OUTPUT_EXISTS")
            result = self._worker("sign", directory=str(directory), output=str(signed))
            if self.inspect(version)["payloadSha256"] != record["payloadSha256"]:
                raise EnvironmentError("COMPONENT_SIGN_CHANGED_PAYLOAD")
            atomic_json(directory / "signed.json", result)
            return result

    def unpack(self, version):
        with self.environment._writer():
            result, files = self._inspect(version)
            if result["problems"]:
                raise EnvironmentError("COMPONENT_PACKAGING_INVALID")
            destination = self._directory(version) / "unpacked"
            if destination.exists() or destination.is_symlink():
                raise EnvironmentError("COMPONENT_UNPACK_DESTINATION_EXISTS")
            destination.mkdir(mode=0o700)
            # No extractall: validated regular files only, never archive owners,
            # permissions, links, devices, absolute paths or executable hooks.
            for name, content in files.items():
                target = destination.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(content)
            return dict(version=version, destination=str(destination), files=len(files),
                        bundleSha256=result["sha256"], executable=False)
