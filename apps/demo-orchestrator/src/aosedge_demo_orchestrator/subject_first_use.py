# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit first-use references; existing assignment remains the only binder."""

from .service_assignment import LABELS, _pages, _subject, confirm_retired_subjects
from .service_cloud import service_view
from .status import object_id, now
from .unit_cloud import CloudFailure

def inspect_reference(cloud, provider, reference):
    """Fresh exact-ID, authority, membership and zero-recipient proof; GET only."""
    if not isinstance(reference, dict) or set(reference) != {'team', 'ownerId', 'serviceProviderId', 'id', 'serviceId', 'createdBy'}:
        raise CloudFailure('FIRST_USE_EXACT_REFERENCE_REQUIRED')
    team = reference['team']
    for key in set(reference) - {'team'}: object_id(reference[key])
    if (team not in LABELS or cloud.user['role'] != 'oem' or cloud.user['ownerId'] != reference['ownerId']
            or provider.user['role'] != 'service provider'
            or provider.user['ownerId'] != reference['serviceProviderId']):
        raise CloudFailure('FIRST_USE_AUTHORITY_CHANGED')
    cloud.require('subjects_list', 'services_read', 'services_units_list')
    provider.require('services_read')
    candidates = _pages(cloud, 'subjects/', lambda r: object_id(r['id']))
    matching = [r for r in candidates if r.get('label') == LABELS[team]]
    if len(matching) != 1 or matching[0]['id'] != reference['id']:
        raise CloudFailure('FIRST_USE_EXACT_SUBJECT_NOT_UNIQUE')
    service_id = reference['serviceId']
    for actor in (cloud, provider):
        service = service_view(actor.call('services/' + service_id + '/'), actor.user, detail=True)
        if (service['id'] != service_id or service['codename'] != team + '-health-service'
                or service['serviceProviderId'] != reference['serviceProviderId']):
            raise CloudFailure('FIRST_USE_SERVICE_BINDING_CHANGED')
    entry = dict(id=reference['id'], serviceId=service_id, createdBy=reference['createdBy'], label=LABELS[team])
    confirm_retired_subjects(cloud, dict(ownerId=reference['ownerId'], retainedSubjects=[entry]))
    if _pages(cloud, 'services/' + service_id + '/units/', lambda r: object_id(r['id'])):
        raise CloudFailure('FIRST_USE_SERVICE_HAS_RECIPIENTS')
    return dict(reference, status='EXACT_UNBOUND_REFERENCE_OBSERVED', adopted=False, cloudMutation=False)


def execute(cloud, provider, request):
    cloud.require("service_providers_list")
    if not any(row.get("id") == provider.user["ownerId"] for row in cloud.pages("service-providers/")):
        raise CloudFailure("FIRST_USE_OEM_SP_ASSOCIATION_REQUIRED")
    if request["action"] == "first-use-subject-check":
        return inspect_reference(cloud, provider, request["reference"])
    if request["action"] != "first-use-subjects":
        raise CloudFailure("FIRST_USE_ACTION_INVALID")
    cloud.require("subjects_list", "subjects_read", "subjects_services_list")
    candidates = _pages(cloud, "subjects/", lambda r: object_id(r["id"]))
    rows = []
    for team, label in LABELS.items():
        for candidate in [v for v in candidates if v.get("label") == label]:
            if len(rows) >= 16:
                raise CloudFailure("FIRST_USE_CANDIDATE_LIMIT")
            identity = object_id(candidate["id"])
            row = dict(team=team, id=identity, state="BLOCKED", reason="EXACT_BINDING_NOT_CONFIRMED")
            try:
                subject = _subject(cloud.call("subjects/" + identity + "/"), label, identity)
                services = _pages(cloud, "subjects/" + identity + "/services/", lambda v: object_id(v["service"]["id"]))
                if len(services) != 1:
                    raise CloudFailure("FIRST_USE_EXACT_SERVICE_REQUIRED")
                reference = dict(team=team, ownerId=cloud.user["ownerId"],
                    serviceProviderId=provider.user["ownerId"], id=identity,
                    serviceId=object_id(services[0]["service"]["id"]), createdBy=subject["createdBy"])
                inspect_reference(cloud, provider, reference)
                row.update(state="ELIGIBLE", reason="EXACT_UNBOUND_REFERENCE_OBSERVED", reference=reference)
            except CloudFailure:
                # Never echo Cloud response text or treat inaccessible as missing.
                pass
            rows.append(row)
    return dict(rows=rows, ownerId=cloud.user["ownerId"],
                serviceProviderId=provider.user["ownerId"], cloudMutation=False)


class FirstUseSubjects:
    def __init__(self, units):
        self.units = units
        self.environment = units.environment
        self.root = units.root

    def perform(self, oem, sp, token, reference=None):
        from .cloud_connection import CloudConnection, CONFIG
        from .cloud_setup import CloudSetup
        from .environment import EnvironmentError, atomic_json
        from .package_artifacts import digest
        connection = CloudConnection(self.environment)
        with self.environment._writer():
            metadata = connection.inspect_pair(oem, sp)
            if metadata["selectionToken"] != token:
                raise EnvironmentError("CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW")
            config = connection._configuration()
            profiles = config.get("cloudProfiles", {})
            if (profiles.get("oem-delivery", {}).get("credential") != oem
                    or profiles.get("service-provider", {}).get("credential") != sp
                    or config.get("cloudConnection", {}).get("domain") != metadata["domain"]):
                raise EnvironmentError("SETUP_SAVE_PAIR_FIRST")
            request = dict(CloudSetup(self.units)._request())
            action = "first-use-subject-check" if reference is not None else "first-use-subjects"
            if reference is not None:
                request["reference"] = reference
            observed = self.units._cloud(action, **request)
            if connection._pair_stamp(oem, sp) != token:
                raise EnvironmentError("CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW")
            if reference is None:
                return dict(metadata, status="CLOUD_SUBJECTS_OBSERVED", cloudAccessed=True,
                    runtimeChanged=False, demoReady=False, subjects=observed["rows"])
            if (observed != dict(reference, status="EXACT_UNBOUND_REFERENCE_OBSERVED", adopted=False, cloudMutation=False)):
                raise EnvironmentError("FIRST_USE_REFERENCE_CHANGED")
            key = digest(dict(domain=metadata["domain"], ownerId=reference["ownerId"]))
            context = config.setdefault("cloudSetupContexts", {}).setdefault(key, {})
            if any(context.get(k, v) != v for k, v in dict(domain=metadata["domain"], ownerId=reference["ownerId"]).items()):
                raise EnvironmentError("FIRST_USE_CONTEXT_CHANGED")
            context.update(domain=metadata["domain"], ownerId=reference["ownerId"])
            references = context.setdefault("subjectReferences", {})
            previous = references.get(reference["team"])
            if previous is not None and previous != reference:
                raise EnvironmentError("FIRST_USE_REFERENCE_REPLACEMENT_BLOCKED")
            if previous is None:
                references[reference["team"]] = reference
                atomic_json(self.root / CONFIG, config)
            return dict(metadata, selectionToken=connection._pair_stamp(oem, sp),
                status="CLOUD_SUBJECT_REFERENCE_SAVED", cloudAccessed=True,
                runtimeChanged=False, demoReady=False)


def selected_reference(units, state, publication, service_id):
    """Called under the assignment owner's writer; fresh validation before use."""
    from .cloud_connection import CloudConnection, cloud_binding, selected_domain
    from .cloud_setup import CloudSetup
    from .package_artifacts import digest, credential_stamp
    from .environment import EnvironmentError
    connection = CloudConnection(units.environment)
    config = connection._configuration()
    domain, owner = selected_domain(state), cloud_binding(state)["ownerId"]
    context = config.get("cloudSetupContexts", {}).get(digest(dict(domain=domain, ownerId=owner)), {})
    reference = context.get("subjectReferences", {}).get(publication["team"])
    if reference is None:
        return None
    if (context.get("domain") != domain or context.get("ownerId") != owner
            or reference.get("ownerId") != owner or reference.get("serviceId") != service_id
            or reference.get("serviceProviderId") != publication["serviceProviderId"]):
        raise EnvironmentError("FIRST_USE_REFERENCE_BINDING_CHANGED")
    profiles = config["cloudProfiles"]
    from pathlib import Path
    paths = [Path(profiles[key]["credential"]) for key in ("oem-delivery", "service-provider")]
    stamps = [credential_stamp(path) for path in paths]
    if not all(stamps):
        raise EnvironmentError("FIRST_USE_CREDENTIAL_UNSAFE")
    request = CloudSetup(units)._request()
    if request["cloudDomain"] != domain:
        raise EnvironmentError("FIRST_USE_DOMAIN_CHANGED")
    observed = units._cloud("first-use-subject-check", **request, reference=reference)
    if (observed != dict(reference, status="EXACT_UNBOUND_REFERENCE_OBSERVED", adopted=False, cloudMutation=False)
            or connection._configuration() != config or [credential_stamp(path) for path in paths] != stamps):
        raise EnvironmentError("FIRST_USE_REFERENCE_CHANGED")
    return dict(id=reference["id"], ownerId=owner, label=LABELS[publication["team"]],
        createdBy=reference["createdBy"], isGroup=True, priority=0,
        create=dict(stage="CONFIRMED", attempted=False, source="EXPLICIT_FIRST_USE_REFERENCE", confirmedAt=now()))
