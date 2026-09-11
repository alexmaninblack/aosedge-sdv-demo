# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit OEM assignment of published demo identities to current Test only."""

from .environment import EnvironmentError, JOURNAL, atomic_json
from .status import object_id, read_json, now

LABEL = "AosEdge SDV demo Test"
STEPS = ("create", "bind", "assign")


def _pages(cloud, path, identity):
    from urllib.parse import urlencode
    from .unit_cloud import CloudFailure
    rows, seen, total = [], set(), None
    for offset in range(0, 800, 100):
        page = cloud.call(path + "?" + urlencode(dict(limit=100, offset=offset)))
        if (not isinstance(page, dict) or type(page.get("total")) is not int or page["total"] < 0
                or page.get("offset") != offset or not isinstance(page.get("items"), list)
                or len(page["items"]) > 100 or total is not None and total != page["total"]):
            raise CloudFailure("SERVICE_ASSIGNMENT_COLLECTION_INVALID_OR_CHANGED")
        total = page["total"]
        for row in page["items"]:
            key = identity(row)
            if key in seen:
                raise CloudFailure("SERVICE_ASSIGNMENT_DUPLICATE_IDENTITY")
            seen.add(key)
            rows.append(row)
        if len(rows) == total:
            return rows
        if len(rows) > total or len(page["items"]) != 100:
            raise CloudFailure("SERVICE_ASSIGNMENT_COLLECTION_INCOMPLETE")
    raise CloudFailure("SERVICE_ASSIGNMENT_COLLECTION_LIMIT")


def _subject(row, expected_id=None, created_by=None):
    from .unit_cloud import CloudFailure
    identifier = object_id(row["id"])
    creator = object_id(row["created_by"])
    if (expected_id is not None and identifier != expected_id or row.get("label") != LABEL
            or row.get("is_group") is not True or row.get("is_protected") is not False
            or type(row.get("priority")) is not int or row["priority"] != 0
            or created_by is not None and creator != created_by):
        raise CloudFailure("SERVICE_SUBJECT_IDENTITY_TYPE_OR_OWNER_CONFLICT")
    return dict(id=identifier, label=LABEL, isGroup=True, priority=0, createdBy=creator)


def snapshot(cloud, request):
    """Bounded, sanitized authoritative preflight; never adopts by label."""
    from .service_cloud import service_view, unit_view, version_view
    from .unit_cloud import CloudFailure
    if cloud.user["role"] != "oem" or cloud.user["ownerId"] != request["ownerId"]:
        raise CloudFailure("SERVICE_ASSIGNMENT_OEM_BINDING_CHANGED")
    cloud.require("services_read", "services_service_versions_list", "services_units_list", "units_read",
        "unit_sets_read", "subjects_list", "subjects_read", "subjects_units_list", "subjects_units_reported",
        "subjects_services_list")
    identifier = object_id(request["serviceId"])
    current = request["test"]
    unit = cloud.unit(object_id(current["unitId"]), nodes=False)
    if (not unit or unit["id"] != current["unitId"] or unit["system_uid"] != current["systemUid"]
            or unit["status"] != "provisioned" or current["unitSetId"] not in unit["unit_sets"]):
        raise CloudFailure("SERVICE_ASSIGNMENT_CURRENT_TEST_MISMATCH")
    unit_set = cloud.call("unit-sets/" + object_id(current["unitSetId"]) + "/")
    if unit_set.get("id") != current["unitSetId"] or unit_set.get("is_validation_set") is not True:
        raise CloudFailure("SERVICE_ASSIGNMENT_VERIFICATION_TEST_REQUIRED")
    service = service_view(cloud.call("services/" + identifier + "/"), cloud.user, detail=True)
    if (service["id"] != identifier or request["team"] not in ("brake", "tire")
            or service.get("codename") != request["team"] + "-health-service"
            or service["serviceProviderId"] != request["serviceProviderId"]):
        raise CloudFailure("SERVICE_ASSIGNMENT_PUBLICATION_BINDING_CHANGED")
    versions = [version_view(row) for row in _pages(cloud, "services/" + identifier + "/service-versions/", lambda row: object_id(row["id"]))]
    selected = [row for row in versions if row["version"] == request["publishedVersion"]]
    if len(selected) != 1 or str(selected[0].get("container_state") or "").lower() != "ready":
        raise CloudFailure("SERVICE_ASSIGNMENT_PUBLISHED_VERSION_NOT_READY")
    recipients = [unit_view(row) for row in _pages(cloud, "services/" + identifier + "/units/", lambda row: object_id(row["id"]))]
    if any(row["id"] != current["unitId"] or row["system_uid"] != current["systemUid"] or row["oemId"] != request["ownerId"] for row in recipients):
        raise CloudFailure("SERVICE_ASSIGNMENT_NON_TEST_RECIPIENT_PRESENT")
    retained = request.get("subject") or {}
    subjects = _pages(cloud, "subjects/", lambda row: object_id(row["id"]))
    matches = [row for row in subjects if row.get("label") == LABEL]
    result = dict(subject=None, candidateSubjectIds=[object_id(row["id"]) for row in matches],
        unitBound=False, serviceBound=False, serviceIds=[], source="AOS_CLOUD_ONLY", observedAt=now())
    if not retained.get("id"):
        if matches:
            raise CloudFailure("SERVICE_SUBJECT_UNRECORDED_LABEL_COLLISION")
        if recipients:
            raise CloudFailure("SERVICE_ASSIGNMENT_UNRECORDED_BINDING_PRESENT")
        return result
    subject_id = object_id(retained["id"])
    if len(matches) != 1 or object_id(matches[0]["id"]) != subject_id:
        raise CloudFailure("SERVICE_SUBJECT_RECORDED_ID_NOT_UNIQUE")
    result["subject"] = _subject(cloud.call("subjects/" + subject_id + "/"), subject_id, retained["createdBy"])
    for row in recipients:
        if row["subjectIds"] is None or any(value != subject_id for value in row["subjectIds"]):
            raise CloudFailure("SERVICE_ASSIGNMENT_UNRELATED_SUBJECT_PRESENT")
    def scoped_units(path):
        rows = _pages(cloud, path, lambda row: object_id(row["id"]))
        if any(object_id(row["id"]) != current["unitId"] or row.get("system_uid") != current["systemUid"] for row in rows):
            raise CloudFailure("SERVICE_SUBJECT_NON_TEST_UNIT_PRESENT")
        return rows
    assigned = scoped_units("subjects/" + subject_id + "/units/")
    scoped_units("subjects/" + subject_id + "/units/reported/")
    rows = _pages(cloud, "subjects/" + subject_id + "/services/", lambda row: object_id(row["service"]["id"]))
    service_ids = [object_id(row["service"]["id"]) for row in rows]
    allowed = {identifier, *request.get("ownedServiceIds", [])}
    if set(service_ids) - allowed:
        raise CloudFailure("SERVICE_SUBJECT_UNRELATED_SERVICE_PRESENT")
    if not assigned and service_ids:
        raise CloudFailure("SERVICE_SUBJECT_STALE_SERVICE_BINDINGS")
    result.update(unitBound=bool(assigned), serviceBound=identifier in service_ids, serviceIds=service_ids)
    if request.get("runtime"):
        from .cloud_observation import service as runtime_service
        cloud.require("units_subjects_services_list", "units_subjects_services_read")
        listing = _pages(cloud, "units/" + current["unitId"] + "/subjects-services/",
            lambda row: (row.get("subject"), (row.get("service") or {}).get("id")))
        details = _pages(cloud, "units/" + current["unitId"] + "/subjects-services/" + identifier + "/",
            lambda row: (row.get("subject"), (row.get("service") or {}).get("id")))
        if any((row.get("service") or {}).get("id") != identifier for row in details):
            raise CloudFailure("SERVICE_ASSIGNMENT_RUNTIME_IDENTITY_MISMATCH")
        result["runtime"] = dict(services=[runtime_service(row) for row in listing if
            (row.get("service") or {}).get("id") == identifier], details=[runtime_service(row) for row in details])
    return result


def execute(cloud, request):
    """One optional POST per worker; host journals before dispatch."""
    from .unit_cloud import CloudFailure
    if request["action"] == "service-assignment-observe":
        return snapshot(cloud, request)
    if request["action"] != "service-assignment-step" or request.get("step") not in STEPS:
        raise CloudFailure("SERVICE_ASSIGNMENT_ACTION_INVALID")
    step = request["step"]
    try:
        before = snapshot(cloud, request)
        cloud.require({"create": "subjects_create", "bind": "subjects_units_create", "assign": "subjects_services_create"}[step])
        if ((step == "create" and before["subject"] is not None) or
                (step == "bind" and before["unitBound"]) or (step == "assign" and before["serviceBound"])):
            return dict(stage="OBSERVED", attempted=False, observation=before)
        if step != "create" and before["subject"] is None or step == "assign" and not before["unitBound"]:
            raise CloudFailure("SERVICE_ASSIGNMENT_ORDER_REQUIRED")
    except (CloudFailure, ValueError, TypeError, KeyError) as error:
        return dict(stage="BLOCKED", attempted=False, reason=str(error) if isinstance(error, CloudFailure) else "SERVICE_ASSIGNMENT_PREFLIGHT_SCHEMA_INVALID")
    subject_id = before["subject"]["id"] if before["subject"] else None
    path, body = ("subjects/", dict(label=LABEL, is_group=True)) if step == "create" else (
        "subjects/" + subject_id + ("/units/" if step == "bind" else "/services/"),
        {"system_uids": [request["test"]["systemUid"]]} if step == "bind" else {"service_ids": [request["serviceId"]]})
    try:
        response = cloud.call(path, "POST", body, expected=201)
        if step == "create":
            subject = _subject(response, created_by=cloud.user["userId"])
            return dict(stage="ACCEPTED", attempted=True, httpStatus=201, subject=subject)
        key, value = ("system_uids", request["test"]["systemUid"]) if step == "bind" else ("service_ids", request["serviceId"])
        if object_id(response["subject_id"]) != subject_id or response.get(key) != [value]:
            raise CloudFailure("SERVICE_ASSIGNMENT_RESPONSE_BINDING_MISMATCH")
        return dict(stage="ACCEPTED", attempted=True, httpStatus=201)
    except Exception:
        return dict(stage="UNCERTAIN", attempted=True, reason="SERVICE_ASSIGNMENT_POST_RESPONSE_UNCERTAIN")


class ServiceAssignment:
    def __init__(self, environment, units):
        self.environment, self.units = environment, units
        self.path = environment.root / JOURNAL

    def _publication(self, service_id):
        from .service_packages import ServicePackages
        packages = ServicePackages(self.environment)
        matches = []
        for team in ("brake", "tire"):
            root = self.environment.catalog.project / "services" / team / "releases"
            paths = list(root.glob("*/publication.json"))
            if len(paths) > 256:
                raise EnvironmentError("SERVICE_ASSIGNMENT_PUBLICATION_SCAN_LIMIT")
            for path in paths:
                if any(part.is_symlink() for part in (path, *path.parents)
                        if part.is_relative_to(self.environment.catalog.project)):
                    raise EnvironmentError("SERVICE_PUBLICATION_PATH_UNSAFE")
                receipt = read_json(path)
                observation = receipt.get("lastObservation") or {}
                if observation.get("serviceId") != service_id or observation.get("stage") != "READY":
                    continue
                _, record = packages._record(team + "/" + path.parent.name, verify_payload=False)
                if (observation.get("version") != record["version"] or record.get("serviceId") not in (None, service_id)
                        or receipt.get("attempted") is not True or not receipt.get("deploymentId")
                        or observation.get("deploymentId") != receipt["deploymentId"]
                        or observation.get("source") != "AOS_CLOUD_ONLY"
                        or str(observation.get("bundleState") or "").lower() != "done"
                        or str(observation.get("versionState") or "").lower() != "ready"):
                    raise EnvironmentError("SERVICE_ASSIGNMENT_PUBLICATION_RECEIPT_MISMATCH")
                matches.append(dict(team=team, serviceProviderId=record["serviceProviderId"], publishedVersion=record["version"]))
        if not matches or len({(item["team"], item["serviceProviderId"]) for item in matches}) != 1:
            raise EnvironmentError("SERVICE_ASSIGNMENT_READY_PUBLICATION_REQUIRED")
        from .releases import number
        return max(matches, key=lambda item: number(item["publishedVersion"]))

    def assign(self, service_id):
        service_id = object_id(service_id)
        with self.environment._writer():
            if self.path.is_symlink():
                raise EnvironmentError("SERVICE_ASSIGNMENT_JOURNAL_UNSAFE")
            state = read_json(self.path)
            item = state.get("vehicles", {}).get("test") or {}
            owner = object_id((state.get("cloudBinding") or {})["ownerId"])
            if (state.get("kind") != "democtl.current-run" or not item.get("localVmId") or not item.get("systemUid")
                    or item.get("cloud", {}).get("lifecycle") in ("DEPROVISIONED", "DELETED")
                    or state.get("demoLifecycle", {}).get("action") == "retire"):
                raise EnvironmentError("SERVICE_ASSIGNMENT_CURRENT_TEST_REQUIRED")
            test = dict(unitId=object_id(item["unitId"]), systemUid=item["systemUid"], unitSetId=object_id(item["unitSetId"]))
            publication = self._publication(service_id)
            subject = state.get("demoSubject")
            if subject and (subject.get("ownerId") != owner or subject.get("label") != LABEL):
                raise EnvironmentError("SERVICE_SUBJECT_RECORDED_OWNER_CONFLICT")
            subject = state.setdefault("demoSubject", dict(ownerId=owner, label=LABEL))
            operations = state.setdefault("serviceOperations", {})
            binding = dict(serviceId=service_id, **publication, test=test, ownerId=owner)
            previous = operations.get(service_id)
            if previous and any(previous.get(key) != binding[key] for key in ("serviceId", "team", "serviceProviderId", "test", "ownerId")):
                raise EnvironmentError("SERVICE_ASSIGNMENT_RECORDED_BINDING_CHANGED")
            record = operations.setdefault(service_id, dict(binding, state="PREPARING", steps={}))
            owned = [identifier for identifier, value in operations.items() if value.get("ownerId") == owner
                and value.get("test") == test and value.get("state") == "ASSIGNED"]
            request = dict(binding, subject=subject, ownedServiceIds=owned)
            changed = False
            def save():
                atomic_json(self.path, state)
            def observe(runtime=False):
                return self.units._cloud("service-assignment-observe", **request, runtime=runtime)
            def partial(reason):
                record.update(state="UNCERTAIN", reason=reason, observedAt=now())
                save()
                return dict(state="UNCERTAIN", serviceId=service_id, subjectId=subject.get("id"), reason=reason,
                    noOp=not changed, runtimeQualified=False)
            try:
                # A lost create response has no authoritative UUID to reconcile.
                # A matching label is never sufficient proof of ownership.
                if not subject.get("id") and subject.get("create", {}).get("attempted") is True:
                    return partial("SERVICE_SUBJECT_CREATE_ID_UNCERTAIN_NO_REPLAY")
                current = observe()
                for step in STEPS:
                    done = current["subject"] is not None if step == "create" else current["unitBound"] if step == "bind" else current["serviceBound"]
                    attempt = subject.get("create", {}) if step == "create" else record["steps"].get(step, {})
                    if done:
                        if attempt:
                            attempt.update(stage="CONFIRMED", confirmedAt=now())
                            save()
                        continue
                    if attempt.get("attempted") is True:
                        return partial("SERVICE_ASSIGNMENT_" + step.upper() + "_NOT_OBSERVED_NO_REPLAY")
                    attempt = dict(stage="ATTEMPTING", attempted=True, startedAt=now())
                    if step == "create":
                        subject["create"] = attempt
                    else:
                        record["steps"][step] = attempt
                    save()
                    response = self.units._cloud("service-assignment-step", **request, step=step)
                    if (response.get("stage") not in ("ACCEPTED", "OBSERVED", "BLOCKED", "UNCERTAIN")
                            or type(response.get("attempted")) is not bool):
                        return partial("SERVICE_ASSIGNMENT_WORKER_RESPONSE_INVALID")
                    attempt.update(response)
                    changed = changed or response["attempted"]
                    if step == "create" and response.get("subject"):
                        subject.update(response["subject"])
                    save()
                    if response["stage"] == "BLOCKED":
                        record.update(state="BLOCKED", reason=response["reason"])
                        save()
                        return dict(state="BLOCKED", reason=response["reason"], serviceId=service_id, noOp=not changed)
                    if step == "create" and not subject.get("id"):
                        return partial("SERVICE_SUBJECT_CREATE_ID_UNCERTAIN_NO_REPLAY")
                    current = observe()
                    confirmed = current["subject"] is not None if step == "create" else current["unitBound"] if step == "bind" else current["serviceBound"]
                    if not confirmed:
                        return partial("SERVICE_ASSIGNMENT_" + step.upper() + "_NOT_OBSERVED_NO_REPLAY")
                    attempt.update(stage="CONFIRMED", confirmedAt=now())
                    save()
                current = observe(runtime=True)
                record.update(state="ASSIGNED", subjectId=subject["id"], observedAt=now())
                record.pop("reason", None)
                save()
                return dict(state="ASSIGNED", serviceId=service_id, subjectId=subject["id"], test=test,
                    noOp=not changed, runtimeQualified=False, observation=current)
            except EnvironmentError as error:
                return partial(str(error))
