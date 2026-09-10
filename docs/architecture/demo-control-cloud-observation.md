<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: bounded Cloud observations

Implemented P2 source increment, 10 September 2026. This implements the
read-only portion of the [accepted delivery plan](../planning/active/demo-studio-delivery-plan.md#p2-make-cloud-observations-and-publication-results-truthful),
not publication, Presenter refresh timers, service assignment or runtime qualification.

## Commands and authority

```bash
democtl unit cloud-status test
democtl unit monitoring test
democtl --output json unit cloud-status test
```

The transport-neutral API takes exactly
`{"domain":"unit","action":"cloud-status","target":"test"}` or the same
request with `"action":"monitoring"`. It accepts no paths, credentials,
Unit IDs, endpoints or guest-read flags. Production/all are not accepted.

The existing run journal selects the exact current Test `unitId`/`systemUid`
and OEM owner. The configured `oem-delivery` credential is used by the existing
isolated Aos SDK worker. The journal supplies no displayed software,
connectivity or resource state. Missing identity is a local binding blocker,
not a Cloud-empty result. No VM inspection, image hash, permission change,
provisioning, component mutation, log request or lifecycle journal write occurs.

## Documented reads and bounds

Sources: [public OpenAPI v11, implementation 6.1.53](https://api.aoscloud.io/api/v11/openapi.json),
[Cloud DMIPS description](https://docs.aosedge.tech/docs/aos-cloud/components-view/dmips-and-cpu-usage),
and [monitoring pipeline](https://docs.aosedge.tech/docs/aos-core/monitoring/monitoring-pipeline).
Schemas and descriptions take precedence over illustrative examples.

| Read | Projection and bounds |
| --- | --- |
| `GET /users/me/` | Existing OEM authentication/owner context, once per worker call; not proof of mutation authority |
| `GET /units/{U}/` | Exact UUID and system UID must match; all reported `unit_update_components`, `nodes`, `layers`, assigned/reported Subjects; safe Unit/config identity fields |
| `GET /units/{U}/subjects-services/?limit=100&offset=0` | One page; subject/service identity, installed/pending version IDs, counts, priority, instances and errors |
| `GET /units/{U}/subjects-services/{S}/?limit=100&offset=0` | One page per distinct observed service, up to eight services in parallel; all returned subjects/instances, actual installed/pending version detail and per-instance version/run state |
| `GET /units/{U}/monitoring/?datetime_from=latest` | Only for `unit monitoring`; exact Unit read first, then one latest-sample request, no inventory/detail scan |

Every HTTP read uses the existing 12-second timeout and 2 MiB response cap.
The observation worker has a 60-second overall process budget; its sanitized
IPC result is capped by the existing 256 KiB result boundary. No retries,
long poll, timer-driven completion or account-wide scans are added.

Service list/detail pages carry `coverage: {offset, returned, total, complete}`.
An unfinished page becomes `INCOMPLETE`, not confirmed absence. More than eight
observed service identities marks the list `INCOMPLETE` with
`CLOUD_SERVICE_DETAIL_LIMIT`; no unbounded detail fan-out occurs. This bounded
first increment does not silently enumerate arbitrary account-sized inventories.

## Result shape

Existing `OperationResult` is retained: `operation`, `state`, `message`,
`target: "test"`, `data`. The outer state is `OBSERVED` if all requested
observations are current, otherwise `PARTIAL`; missing local binding is `BLOCKED`.

`data` contains:

```text
schemaVersion: 1
source: AOS_CLOUD_ONLY
target: test
unitId, systemUid
readCompletedAt
problems: [{section, state, reason}]
serviceDetails: {service UUID: Observation<service-subject rows>}

cloud-status: unit, components, nodes, layers,
              assignedSubjects, reportedSubjects, services
monitoring:   monitoring
```

Each named read uses the existing observation envelope:

```text
value: object | array | null
source: AOSCLOUD_OEM
sourceTimestamp: string | null
readCompletedAt: local UTC read timestamp
state: CURRENT | UNKNOWN | INCOMPLETE | STALE
transport: AVAILABLE | UNAUTHENTICATED | FORBIDDEN |
           NOT_FOUND_OR_INACCESSIBLE | SCHEMA_INVALID | SOURCE_UNAVAILABLE
reason: string | null
```

The projections preserve documented source field names. Component rows expose
`installed_component`, `pending_component`, raw `pending_component_status`,
`pending_component_error`, reported/installed IDs and checksums where provided.
`runtimeState: NOT_REPORTED_BY_CLOUD` is explicit: the documented component
schema has no version-bound process runtime report. This is not a claim that
VDP is stopped, running or healthy. General Cloud object `updated_at` is not
treated as a device report timestamp.

Service rows expose `subject`, `service`, `service_versions`, `num_instance`,
`pending_num_instance`, errors, and an `instances` observation. Instances retain
`instance_id`, `version`, `version_id`, raw `run_state`, node scope and error
codes/message. Zero instances, a missing instance array, installed version and
an old running instance remain distinct. No product-health or update-completion
inference is performed here.

Nested `assignedSubjects`/`reportedSubjects` retain their explicit identity and
service lists. Raw Unit config, environment, component metadata, container
configuration, certificates, checksums of secrets and arbitrary response fields
are not forwarded. Text is bounded; credential-like text, URLs, JWTs and PEM
blocks in public error fields are redacted.

## Monitoring semantics

`monitoring.value` has `cpu`, `ram`, `usedDisk`, `disk`, `inTraffic`, `outTraffic`
observations. Each metric has `unit` and `unitEvidence`, with an array of
documented `ParameterMonitoringModel` sample projections. Samples retain raw
`value`, `time`, `system_uid`, `nodeId`, `serviceId`, `subjectId`, `instance`,
`partition`, `parameter` and `measurementType`; `sourceTimestamp` copies only
the supplied `time`. Missing sample value/time remains `UNKNOWN` and marks
the metric incomplete. A supplied different system UID rejects the response.

CPU has `unit: "DMIPS"` and `unitEvidence: "CLOUD_DMIPS_DOCUMENTATION"`.
The REST schema does not define RAM/disk/traffic scaling. Those fields retain
raw values with `unit: null`, `unitEvidence: "UNIT_NOT_VERIFIED"`; no invented
KiB/bytes/rate conversion or percentage denominator is applied. The Core source
pipeline's bytes alone do not prove the REST layer has no scaling. One tenant
integration read and authoritative unit mapping remain required.

`[]` means a successful empty source response. Missing/null means not reported.
`0` is a measured zero, never substituted for missing. A 403/404/timeout does not
mean Offline, no services or zero resource use. HTTP 404 deliberately remains
not-found-or-inaccessible, matching the API's documented ambiguity.

## Sharing, freshness and remaining integration

One persistent `UnitService` shares simultaneous reads per exact
OEM owner/Unit UUID/system UID/action through an in-memory future, and retains
the previous snapshot in memory. A failed refresh retains available last-known
values as `STALE`, preserving the failed attempt's transport/read time and a
separate `lastKnownReadCompletedAt`. Identity changes cannot reuse that cache;
an explicit successful empty inventory clears the corresponding previous facts.
No on-disk observation database is added. Separate CLI processes perform fresh
one-shot reads. The Presenter must reuse its application instance to share reads.

Visible-panel scheduling is implemented in the shared Presenter observer for
the existing Cloud-only Platform read: one in-flight request; entry and
post-action refresh; pending intervals of 2, 4, 8, then 10 seconds; 10 seconds
idle. Both panel exit and a hidden browser document stop scheduling. They do
not cancel an in-flight read or an operation. Concurrent post-action requests
coalesce into one subsequent read; actions while hidden invalidate last-known
data and defer the read until entry. Read failure retains the previous value
and timestamp with STALE, rather than inventing Offline or empty inventory.
The old Platform projection now visibly labels retained values as last known.

This does not bind the new Studio architecture/monitor screens. Their use of
the complete normalized Unit identity/inventory and visible-only metrics is
still part of P4 integration; the current Presenter Platform route remains the
focused VDP overview. Inventory read time does not establish a fresh Unit
report. Upload receipts/reconciliation, profile provenance, runtime completion
rules and SOTA identity remain separate concerns.

The separate [service catalog/ownership inspection](demo-control-service-observation.md)
adds read-only, per-profile OEM/SP catalog and service-to-Unit observations.
It does not infer team publication authority from OEM visibility.

Deterministic tests use synthetic API fixtures and cover multi-component
inventory, missing/empty/error distinctions, real multi-instance versions,
pagination/fan-out bounds, zero/missing metrics, source times, identity mismatch,
secret redaction, stale retention, single-flight reads and identical CLI/API
dispatch. No live Cloud mutation is part of these tests.
