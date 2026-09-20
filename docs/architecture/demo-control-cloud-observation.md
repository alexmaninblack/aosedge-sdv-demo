<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: bounded Cloud observations

Implemented P2 source increment, 10 September 2026; Cloud-first profile
projection updated 18 September 2026. This implements the
read-only portion of the [accepted delivery plan](../planning/active/demo-studio-delivery-plan.md#p2-make-cloud-observations-and-publication-results-truthful),
not publication, Presenter refresh timers, service assignment or runtime qualification.

## Commands and authority

```bash
democtl unit cloud-status test
democtl unit monitoring test
democtl unit monitoring-history test
democtl --output json unit cloud-status test
```

The transport-neutral API takes exactly
`{"domain":"unit","action":"cloud-status","target":"test"}` or the same
request with `"action":"monitoring"` or `"action":"monitoring-history"`. It accepts no paths, credentials,
Unit IDs, endpoints or guest-read flags. Production/all are not accepted.

The existing run journal selects the exact current Test `unitId`/`systemUid`
and OEM owner. The configured `oem-delivery` credential is used by the existing
isolated Aos SDK worker. The journal supplies no displayed software,
connectivity or resource state. Publication receipts may bind an installed
release to its inspected package description as specified below; they never
establish installation. Missing identity is a local binding blocker,
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
| `GET /units/{U}/monitoring/dashboard/` | Only for `unit monitoring-history`; exact Unit and `units_monitoring_dashboard` permission checked independently of latest samples; no guessed `not_older_than` format |

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
`target: "test"`, `data`. The outer state is `OBSERVED` when no material
observation problems remain, otherwise `PARTIAL`; missing local binding is
`BLOCKED`. Supplementary absence is retained explicitly in `notices`, not
silently changed into a current or empty observation.

`data` contains:

```text
schemaVersion: 1
source: AOS_CLOUD_ONLY
target: test
unitId, systemUid
readCompletedAt
problems: [{section, state, reason}]
notices: [{section, state, reason}]
serviceDetails: {service UUID: Observation<service-subject rows>}

cloud-status: unit, components, nodes, layers,
              assignedSubjects, reportedSubjects, services
monitoring:   monitoring
monitoring-history: history
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

Only successful `AVAILABLE` observations with `UNKNOWN`, `NOT_REPORTED` and
null value qualify as supplementary absence: `layers`, `reportedSubjects`,
the service list of a protected non-Group default Subject, and `usedDisk`
when a current non-null `disk` observation is available. Group Subject
services, component/service inventory, transport/schema failures and stale
observations remain problems. A notice does not establish the missing fact.

## Installed functional profile — 18 September 2026

The selected staging read returned null installed-component `metadata_info`;
the exact catalog version described its runtime binding but did not report a
V1/V2/V3 functional profile. Forwarding arbitrary metadata cannot close this
binding. Cloud installation remains authoritative, independently of whether
the local package description is available.

`StudioCloudReader` adds the same bounded `installedProfile` projection to
the overview and the matching VDP component row:

```text
state: CURRENT | STALE | UNKNOWN
profile: v1 | v2 | v3 | null
releaseVersion, cloudVersionId
source: CLOUD_INSTALLATION_AND_PACKAGE
reason: fixed diagnostic code | null
```

The binding requires the exact selected Cloud/OEM/Unit/system UID, Cloud
installed release and version UUID, matching READY publication and deployment
receipt, successful upload, consistent preparation/signing receipts, and a
package inspection matching the prepared unsigned digest and declared profile.
Inspection validates existing package/provenance rules; this is not new
cryptographic signature verification or live process/telemetry proof. No
credential content, raw metadata or artifact paths are exposed in this view.

Reuse the existing bounded publication reader and component inspector; add
no new Cloud endpoint, guest access, timer or persistent observation store.
After the first inventory is available, an installed release takes precedence
over a processing successor when its publication receipt needs reconciliation.
An existing in-flight request is consumed first, preserving independent
concurrent reads and avoiding duplicate requests. The previous inventory is
only a scheduling hint, never a substitute for the displayed observation. The reader
interleaves successor observations if the installed receipt remains unavailable,
and still issues at most one component-publication read per invocation. Its
cache and asynchronous identity include Cloud/OEM/run/Unit scope.
The inspected artifact is cached by path, device/inode, size and modification/
change timestamps; an unchanged package is not rehashed on every UI refresh.

Missing/mismatched evidence leaves the functional profile unknown while
preserving the Cloud-reported release. The guide does not treat unknown as
absent and offer V1 as a required restart. Prepared jobs/candidates cannot
substitute for installed-profile evidence. A retained installation is labelled
last known. A fresh Cloud report of an Offline Unit may still establish its
last reported installed software; it never establishes current function or
advisory. Backend product observations and native telemetry remain separate.

## Monitoring semantics

`monitoring.value` has `cpu`, `ram`, `usedDisk`, `disk`, `inTraffic`, `outTraffic`
observations. Each metric has `unit` and `unitEvidence`, with an array of
documented `ParameterMonitoringModel` sample projections. Samples retain raw
`value`, `time`, `system_uid`, `nodeId`, `serviceId`, `subjectId`, `instance`,
`partition`, `parameter` and `measurementType`; `sourceTimestamp` copies only
the supplied `time`. Missing sample value/time remains `UNKNOWN` and marks
the metric incomplete. A supplied different system UID rejects the response.

CPU has `unit: "DMIPS"` and `unitEvidence: "CLOUD_DMIPS_DOCUMENTATION"`.
RAM has `unit: "bytes"`, `unitEvidence: "CLOUD_OEM_RAM_BYTES"`. Verified on
20 September 2026 against the platform team's deployed [OEM frontend source](https://oem.aws-stage.epmp-aos.projects.epam.com/chunk-5VTGQMUH.js):
the latest `ram` value is assigned without scaling and displayed with
`bytesIEC`; dashboard `ram` pairs are used directly as chart data, whose axis
formatter divides by 1024 into B/KiB/MiB/GiB. A selected-tenant dashboard read
also returned controller and both service series. This supplements the Core
source byte contract rather than assuming the REST layer preserves it.
Presenter converts verified bytes to MiB for graph scales. Unknown-unit inputs
remain raw. Disk/traffic retain `unit: null`, `UNIT_NOT_VERIFIED`; no rate or
percentage denominator is invented.

`[]` means a successful empty source response. Missing/null means not reported.
`0` is a measured zero, never substituted for missing. A 403/404/timeout does not
mean Offline, no services or zero resource use. HTTP 404 deliberately remains
not-found-or-inaccessible, matching the API's documented ambiguity.

## Sharing, freshness and remaining integration

The additive history projection contains `series` keyed by Node, service,
Subject, allocation index and metric (`cpu`/`ram`), each with UTC timestamp/value
pairs. Both documented service arrays and observed keyed objects are accepted;
unknown shapes fail closed. Bounds: eight response groups, eight Nodes per
group, sixteen service entries per Node, 64 series, 1,000 points per input
metric and 4,096 total input points, in addition to existing byte/time limits.
Repeated equal instants deduplicate; conflicting values become explicit null
gaps with `INCOMPLETE`, never arbitrary last-write-wins readings. Coverage
reports actual returned dates/counts, not guaranteed retention. No point is
attributed to a software release.

Presenter exposes fixed GET `/api/presenter/monitoring-history` for current
Test only. Latest/history have independent errors, retained values and nominal
30-second asynchronous observers shared by card and popup. Identity changes
drop previous scope data; hidden surfaces suspend scheduling. No identical
read overlaps; other observers and protected commands remain independent.
Charts use source instants in the current five-minute window. Gaps over three
nominal polling intervals are not joined; old values stay aged outside an empty
live window. This is presentation freshness, not a real-time service deadline.
Disk aliases resolve per Node/service/Subject/index/partition/measurement type;
equal value/time/unit aliases display once, disagreements remain unresolved.

One persistent `UnitService` shares simultaneous reads per exact
selected Cloud/OEM owner/Unit UUID/system UID/action through an in-memory future, and retains
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

The 19 September U4 correction includes status-only component activity in the
same pending predicate used by the UI; a missing pending-version expansion does
not force the observer to idle cadence. This changes no Cloud API or source of
truth. Separately, the functional-backend read adapter now includes Docker
ownership preflight in a ten-second request budget (six seconds for exact-window
detail). Its existing per-exchange HTTP watchdog also covers window response
bodies. Ownership, binding checks, data caps and no-retry behavior are preserved.
See the [U1–U5 correction record](../qualification/presenter-ui-reaudit-fixes-2026-09-19.md).

The initial 10 September increment did not bind the Studio architecture and
monitor screens. Subsequent P4/2.10 integration reuses this normalized Unit
inventory and visible-only resource observer. The 18 September source increment
adds exact installed-profile provenance, with fixture and selected staging
read-only proof in the [qualification record](../qualification/cloud-installed-profile-2026-09-18.md).
The operator subsequently authorized its Presenter-only activation on the
same date; the qualification record contains build and live read/display proof.
Inventory read time still does not establish a fresh Unit report. Service-local
compatibility recovery and product-function status are not closed by this work.

The separate [service catalog/ownership inspection](demo-control-service-observation.md)
adds read-only, per-profile OEM/SP catalog and service-to-Unit observations.
It does not infer team publication authority from OEM visibility.

Deterministic tests use synthetic API fixtures and cover multi-component
inventory, missing/empty/error distinctions, real multi-instance versions,
pagination/fan-out bounds, zero/missing metrics, source times, identity mismatch,
secret redaction, stale retention, single-flight reads and identical CLI/API
dispatch. No live Cloud mutation is part of these tests.
