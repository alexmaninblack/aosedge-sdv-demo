# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit first-use Test setup, behind the existing Demo Control boundary."""

from .environment import EnvironmentError, JOURNAL, atomic_json
from .status import load_configuration, read_json, now, object_id
from .cloud_connection import CloudConnection, CONFIG, LEGACY_DOMAIN, cloud_binding
from .package_artifacts import digest, credential_stamp

MODEL = {"name": "aos-vm", "version": "1.0.0"}
TITLE = "Test Vehicles"


def inspect_setup(cloud, request, sp_factory=None):
    """GET-only, complete collections; an inaccessible object is never absent."""
    from .unit_cloud import Cloud, CloudFailure
    from concurrent.futures import ThreadPoolExecutor
    sp_factory = sp_factory or Cloud
    checks, objects = [], {}

    def row(key, label, fn):
        try:
            state, detail = fn()
        except (CloudFailure, KeyError, TypeError, ValueError, OSError) as error:
            state = "BLOCKED"
            detail = str(error) if isinstance(error, CloudFailure) else "CLOUD_SETUP_READ_UNAVAILABLE"
        checks.append(dict(key=key, label=label, state=state, detail=detail))

    owners = {"oem": cloud.user["ownerId"]}
    checks.append(dict(key="oem", label="OEM access", state="READY", detail="Authenticated OEM"))

    def provider():
        sp_request = dict(credential=request["spCredential"], cloudDomain=request["cloudDomain"])
        from .cloud_connection import inspect_certificate
        inspect_certificate(sp_request["credential"])
        return sp_factory(sp_request, expected_role="service provider")

    # The SP account is independent from the OEM model inventory.
    with ThreadPoolExecutor(max_workers=1) as pool:
        sp_future = pool.submit(provider)

        def fleet():
            cloud.require("fleets_default")
            value = cloud.call("fleets/default/")
            if value.get("is_default") is not True:
                return "CONFLICT", "Default fleet was not confirmed"
            objects["fleetId"] = object_id(value["id"])
            return "READY", "Existing Default fleet"
        row("fleet", "Default fleet", fleet)

        def architecture():
            cloud.require("oems_architectures_read")
            value = cloud.call("oems/" + cloud.user["ownerId"] + "/architectures/")
            return ("READY", "arm64 supported") if "arm64" in value["architectures"] else ("BLOCKED", "OEM_ARM64_ARCHITECTURE_REQUIRED")
        row("architecture", "Package architecture", architecture)

        def model():
            cloud.require("unit_models_list", "unit_models_read")
            matches = [item for item in cloud.pages("unit-models/")
                       if item.get("name") == MODEL["name"] and item.get("version") == MODEL["version"]]
            if not matches:
                cloud.require("unit_models_create")
                return "MISSING", "Create aos-vm 1.0.0 with the single-node Factory configuration"
            if len(matches) != 1:
                return "CONFLICT", "FACTORY_MODEL_AMBIGUOUS"
            value = cloud.call("unit-models/" + object_id(matches[0]["id"]) + "/")
            if (value.get("oem_id") != cloud.user["ownerId"] or value.get("name") != MODEL["name"]
                    or value.get("version") != MODEL["version"] or value.get("unit_config") != request["unitConfig"]):
                return "CONFLICT", "FACTORY_MODEL_CONFIGURATION_MISMATCH"
            objects["modelId"] = object_id(value["id"])
            return "READY", "aos-vm 1.0.0 · one aos-vm-main node"
        row("model", "Factory model and configuration", model)

        def node():
            cloud.require("node_types_list")
            matches = [v for v in cloud.pages("node-types/") if v.get("name") == "aos-vm-main"]
            if len(matches) > 1:
                return "CONFLICT", "FACTORY_NODE_TYPE_AMBIGUOUS"
            if not matches:
                if request.get("testUnitId"):
                    return "BLOCKED", "PROVISIONED_TEST_NODE_TYPE_NOT_CONFIRMED"
                # The documented Node Types confirmation follows provisioning.
                # Model creation alone does not populate this catalog in staging.
                # Requiring it here would block the operation that creates it.
                return "AFTER_PROVISION", "aos-vm-main configured; catalog registration is verified after provisioning"
            return "READY", "aos-vm-main"
        row("nodeType", "Node type", node)

        def test_set():
            cloud.require("unit_sets_list", "unit_sets_units_list")
            all_sets = cloud.pages("unit-sets/")
            matches = [v for v in all_sets if v.get("title") == TITLE or str(v.get("title", "")).endswith(" / " + TITLE)]
            objects["unrelatedSetIds"] = sorted(object_id(v["id"]) for v in all_sets if v not in matches)
            if not objects.get("fleetId"):
                return "BLOCKED", "DEFAULT_FLEET_REQUIRED"
            if not matches:
                cloud.require("unit_sets_create")
                return "MISSING", "Create dedicated Test Vehicles verification set in Default"
            if len(matches) != 1:
                return "CONFLICT", "TEST_UNIT_SET_AMBIGUOUS"
            value = matches[0]
            if (value.get("is_validation_set") is not True or value.get("fleet") != objects["fleetId"]
                    or value.get("allow_unknown_components") is not False):
                return "CONFLICT", "TEST_UNIT_SET_CONFIGURATION_MISMATCH"
            identity = object_id(value["id"])
            members = cloud.pages("unit-sets/" + identity + "/units/")
            if any(v.get("id") != request.get("testUnitId") for v in members):
                return "CONFLICT", "TEST_UNIT_SET_HAS_OTHER_UNITS"
            objects["testSetId"] = identity
            return "READY", "Test Vehicles · verification enabled · Production unchanged"
        row("testSet", "Test verification set", test_set)

        def sp_access():
            sp = sp_future.result()
            owners["sp"] = sp.user["ownerId"]
            return "READY", "Authenticated Service Provider"
        row("sp", "Service Provider access", sp_access)

    def association():
        if not owners.get("sp"):
            return "BLOCKED", "SP_AUTHORITY_REQUIRED"
        cloud.require("service_providers_list")
        matched = any(v.get("id") == owners["sp"] for v in cloud.pages("service-providers/"))
        return ("READY", "Selected SP is visible to OEM") if matched else ("BLOCKED", "OEM_SP_ASSOCIATION_REQUIRED")
    row("association", "OEM / SP association", association)
    failed = any(v["state"] in ("BLOCKED", "CONFLICT") for v in checks)
    missing = any(v["state"] == "MISSING" for v in checks)
    return dict(stage="BLOCKED" if failed else "MISSING" if missing else "READY",
        checks=checks, objects=objects, owners=owners, domain=request["cloudDomain"],
        observedAt=now(), productionPreserved=True,
        steps=[key for key in ("model", "testSet") if any(v["key"] == key and v["state"] == "MISSING" for v in checks)])


def create_step(cloud, request):
    """Exactly one fixed create, with its own authoritative pre/post-read."""
    from .unit_cloud import CloudFailure
    step = request.get("step")
    if step not in ("model", "testSet") or cloud.user["ownerId"] != request["owners"]["oem"]:
        raise CloudFailure("CLOUD_SETUP_SCOPE_CHANGED")
    before = inspect_setup(cloud, request)
    if before["owners"] != request["owners"] or before["stage"] == "BLOCKED":
        return dict(attempted=False, stage="BLOCKED", report=before)
    if step not in before["steps"]:
        return dict(attempted=False, stage="READY", report=before)
    if step == "model":
        body, route = dict(MODEL, unit_config=request["unitConfig"]), "unit-models/"
        cloud.require("unit_models_create")
    else:
        body = dict(title=TITLE, fleet=before["objects"]["fleetId"],
                    description="AosEdge SDV demo Test verification set",
                    is_validation_set=True, allow_unknown_components=False,
                    auto_provision_new_nodes=False, update_strategy="MinimizeRestarts")
        route = "unit-sets/"
        cloud.require("unit_sets_create")
    try:
        result = cloud.call(route, method="POST", body=body, expected=201)
        identity = object_id(result["id"])
    except Exception:
        # No automatic retry, including a lost successful HTTP response.
        return dict(attempted=True, stage="UNCERTAIN", reason="CLOUD_SETUP_CREATE_RECONCILIATION_REQUIRED")
    try:
        after = inspect_setup(cloud, request)
        key = "modelId" if step == "model" else "testSetId"
        if after["objects"].get(key) != identity:
            raise CloudFailure("CLOUD_SETUP_POSTCONDITION_FAILED")
        return dict(attempted=True, stage="CONFIRMED", objectId=identity, report=after)
    except Exception:
        return dict(attempted=True, stage="UNCERTAIN", objectId=identity, reason="CLOUD_SETUP_POST_READ_REQUIRED")


class CloudSetup:
    def __init__(self, units):
        self.units = units
        self.environment = units.environment
        self.root = units.root

    def _request(self):
        config = load_configuration(self.root)
        profiles = config["cloudProfiles"]
        sp = profiles.get("service-provider")
        if not sp or sp.get("expectedRole") != "service provider":
            raise EnvironmentError("SERVICE_PROVIDER_PROFILE_REQUIRED")
        for p in (profiles["oem-delivery"], sp):
            if not credential_stamp(p["credential"]):
                raise EnvironmentError("CLOUD_CREDENTIAL_MISSING_OR_UNSAFE")
        journal = self.root / JOURNAL
        state = read_json(journal) if journal.exists() else {}
        domain = config.get("cloudConnection", {}).get("domain", LEGACY_DOMAIN)
        return dict(cloudDomain=domain, spCredential=str(sp["credential"]),
                    testUnitId=state.get("vehicles", {}).get("test", {}).get("unitId"),
                    unitConfig=read_json(self.root / "config/aosvm-single-node-unitconfig.json"))

    def check(self):
        report = self.units._cloud("cloud-setup-check", **self._request())
        self._check_owner_switch(report, apply=False)
        return report

    def _check_owner_switch(self, report, apply=False):
        config = CloudConnection(self.environment)._configuration()
        old = (config.get("cloudConnection") or {}).get("owners") or {}
        journal = self.root / JOURNAL
        state = read_json(journal) if journal.exists() else {}
        binding_owner = cloud_binding(state).get("ownerId") if state else None
        changed = bool(old and old != report["owners"]) or bool(binding_owner and binding_owner != report["owners"].get("oem"))
        if not changed:
            return
        test = state.get("vehicles", {}).get("test", {})
        unsafe = any(test.get(k) for k in ("unitId", "nodeId", "systemUid", "cloud"))
        unsafe |= bool(state.get("serviceOperations")) or any(
            v.get("upload", {}).get("attemptStarted") for v in state.get("componentOperations", {}).values())
        if unsafe:
            if apply:
                raise EnvironmentError("CLOUD_TENANT_SWITCH_REQUIRES_FINISH_TEST")
            report["stage"] = "BLOCKED"
            report["checks"].append(dict(key="tenant", label="Tenant context", state="BLOCKED",
                detail="CLOUD_TENANT_SWITCH_REQUIRES_FINISH_TEST"))

    def prepare(self):
        with self.environment._writer():
            request = self._request()
            report = self.units._cloud("cloud-setup-check", **request)
            self._check_owner_switch(report, apply=True)
            if report["stage"] == "BLOCKED":
                return report
            config = CloudConnection(self.environment)._configuration()
            key = digest(dict(domain=report["domain"], ownerId=report["owners"]["oem"]))
            setup = config.setdefault("cloudSetupContexts", {}).setdefault(key, {})
            setup.update(domain=report["domain"], ownerId=report["owners"]["oem"])
            path = self.root / CONFIG
            attempts = setup.setdefault("attempts", {})
            # An exact response ID can be reread, never an absent/unknown POST retried.
            for step, receipt in attempts.items():
                if receipt.get("stage") in ("ATTEMPTING", "UNCERTAIN"):
                    object_key = "modelId" if step == "model" else "testSetId"
                    if not receipt.get("objectId") or report["objects"].get(object_key) != receipt["objectId"]:
                        raise EnvironmentError("CLOUD_SETUP_CREATE_RECONCILIATION_REQUIRED:" + step)
                    receipt["stage"] = "CONFIRMED"
            changed = False
            for step in list(report["steps"]):
                self.units.progress("Cloud preparation: " + step + "; one create and authoritative read")
                attempts[step] = dict(stage="ATTEMPTING", startedAt=now(), owners=report["owners"],
                                      specification=digest(request["unitConfig"]))
                atomic_json(path, config)
                result = self.units._cloud("cloud-setup-step", **request, step=step, owners=report["owners"])
                attempts[step].update({k: v for k, v in result.items() if k != "report"}, observedAt=now())
                atomic_json(path, config)
                if result.get("stage") not in ("CONFIRMED", "READY"):
                    return dict(result.get("report") or report, stage="BLOCKED", reason=result.get("reason", "CLOUD_SETUP_CREATE_BLOCKED"))
                report = result["report"]
                changed |= result.get("attempted") is True
            if report["stage"] != "READY":
                return report
            # Public owner IDs, not keys. Configuration survives run retirement.
            connection = config.setdefault("cloudConnection", {})
            connection.update(domain=report["domain"], owners=report["owners"], source="OEM_CERTIFICATE_ORGANIZATION")
            from .cloud_connection import DEFAULT_PROFILES
            profiles = config.setdefault("cloudProfiles", {k: dict(v) for k, v in DEFAULT_PROFILES.items()})
            for name, role in (("oem-delivery", "oem"), ("service-provider", "sp")):
                profiles[name]["expectedOwnerId"] = report["owners"][role]
            setup.update(objects=report["objects"], checkedAt=now())
            journal = self.root / JOURNAL
            if journal.exists():
                state = read_json(journal)
                from .cloud_connection import bind_tenant
                scope = bind_tenant(state, report["domain"], report["owners"])
                binding = scope.setdefault("cloudBinding", {})
                binding.update(ownerId=report["owners"]["oem"], fleetId=report["objects"]["fleetId"])
                binding.setdefault("sets", {})["test"] = report["objects"]["testSetId"]
                atomic_json(journal, state)
            atomic_json(path, config)
            return dict(report, noOp=not changed)
