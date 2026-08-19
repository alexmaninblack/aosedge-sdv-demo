<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Tire Health In-Vehicle Service Component Requirements

- Status: D3 design-reviewed
- Package: [`CR-TIRE`](../component-decomposition-and-interface-register.md#cr-tire)
- Version: 0.1
- Prepared: 2026-08-19
- Accepted: 2026-08-19
- Owner: Function Team 2 / Service Provider 2 / SOTA 2
- Architecture input: [High-Level Architecture 1.4](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 1.7](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 1.6](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 0.9](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 1.0](../component-decomposition-and-interface-register.md)
- Accepted architecture decisions: [ADR 0008](../../architecture/decisions/0008-use-tire-health-for-function-team-2.md), [ADR 0009](../../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md), [ADR 0010](../../architecture/decisions/0010-aos-kuksa-credential-broker.md), and [ADR 0011](../../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md)
- Implementation baseline: no `tire-health-service` repository or executable exists
- Implementation, repository creation, signing, Cloud, or Unit mutation authorized: no

## Purpose

This package defines one independently deployable Tire Health Service v1.0
candidate owned by Function Team 2. The service uses the already accepted VDP
Component v3 contract to estimate tire condition locally, retain bounded
persistent state, send only bounded derived results to its backend, continue
locally while Cloud connectivity is unavailable, and request one narrowly
typed inspection advisory.

Tire Health does not repeat the three-version Brake Health evolution. Brake
Health demonstrates staged product and platform evolution; Tire Health
demonstrates a second independent OEM Function Team, Service Provider identity,
functional data product, and SOTA lifecycle sharing a sufficiently capable
vehicle-data platform. Its `v1.0` label is the first Tire Health product release,
not a hidden `v3` following two omitted candidates.

At `T1`, Tire Health v1.0 and Brake Health v3 run as separate service
instances on the same Domain Controller. Their publication identities,
metadata, IAM-derived permissions, quotas, SOTA lifecycles, functional
backends, dashboards and failure boundaries remain distinct. This is the
bounded multi-tenancy claim of the current OEM-internal demo; third-party
provider and fleet-operator tenancy remain out of scope.

The service is a QM-domain maintenance and inspection application. It has no
allocated safety goal, no vehicle-motion authority, no direct driver-HMI claim,
and no access to simulator-only tire-degradation truth. Service Provider
publication is not deployment approval. Function Team 2 owns the release
decision, and an authorized OEM identity confirms validation deployment and
promotion affecting OEM Units.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | One immutable ARM64 Tire Health v1.0 service candidate, exact VDP v3 compatibility declaration, least-privilege KUKSA client use, bounded persistent synthetic condition estimate, bounded functional-message queue, typed inspection advisory, health, resources, logs and tests |
| What this package does not own | CARLA stimulus or hidden truth, VISS, VDP/KUKSA/Credential Broker implementation, Gateway enforcement, Aos lifecycle execution, Tire Health backend/dashboard, Cloud dependency admission, production tire diagnostics or driver HMI |
| Intended result | A second independent SOTA product runs beside Brake Health, derives a local tire-condition band, survives Cloud loss, sends bounded results and requests only its approved inspection advisory |
| Accountable lifecycle owner | Function Team 2; Service Provider 2 publishes, and an authorized OEM identity approves validation and promotion through SOTA 2 |
| Primary repository | Proposed public `tire-health-service`; repository creation remains a later implementation action |

## Component Boundary

### In scope

- reproducible credential-free ARM64 Aos service packaging for one v1.0 candidate;
- exact VDP Component v3 compatibility and fail-closed startup/readiness;
- per-instance `AOS_SECRET` use at the local Credential Broker boundary;
- short-lived path-scoped KUKSA credential acquisition, refresh and rejection;
- validated subscription to the accepted native vehicle-dynamics subset;
- explicit source quality, freshness, timestamp and unavailable-state handling;
- bounded persistent versioned tire-condition state and deterministic synthetic
  estimation;
- condition-band, confidence and inspection-decision production without exact
  tread-depth claims;
- bounded versioned/idempotent summary and threshold-event delivery;
- one narrowly typed Tire Health inspection-advisory request;
- bounded offline persistence, retry, overflow and reconnect behavior;
- health, readiness, resource, timing, log, uninstall and failure-isolation behavior.

### Out of scope

- creating the accelerated/pre-aged CARLA stimulus or its hidden qualification truth;
- direct CARLA, VISS, Gateway or simulator-oracle access;
- KUKSA Databroker, VDP provider, Credential Broker or Gateway implementation;
- continuous raw vehicle-telemetry upload or Cloud-side model training;
- exact measured tread depth, pressure, temperature, puncture, load, force or
  torque claims unsupported by the selected CARLA vehicle profile;
- arbitrary KUKSA/VSS writes, display text, throttle, brake, steering, gear or
  safety-critical vehicle operation;
- backend ingestion, persistence or Tire Health Function Dashboard;
- SOTA target selection, OEM approval, native Cloud dependency admission or
  AosCloud execution;
- production driver HMI, functional-safety certification or production
  predictive-maintenance accuracy.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Accepted VDP Component v3 contract | `CR-VDP` | Exact compatible contract, required read paths, typed Tire advisory target, units, quality, freshness and factual Gateway status | Service remains not ready, produces no accepted condition result, and sends no advisory |
| Native Aos service identity and IAM permissions | `CR-AOS` plus VDP Credential Broker | Current instance registered, valid `AOS_SECRET`, exact `kuksa` path/mode permissions | Credential request fails closed; no reusable or widened authority |
| Deterministic Tire Health stimulus | `CR-VEHICLE-SIM`, `CR-GATEWAY`, `CR-VDP` | Versioned accelerated/pre-aged scenario and accepted native signal provenance; hidden truth remains inaccessible | Qualification is invalid; service must not infer success from oracle data |
| Tire Health backend contract | Future `CR-TIRE-CLOUD` | Authenticated bounded summary/event schemas and idempotent acknowledgement | Messages remain in the bounded queue; local estimate/advisory continues |
| Aos runtime and resource enforcement | `CR-AOS` | SOTA install/start/stop/uninstall/readiness and declared quotas enforced | Service reports unavailable/error; VDP and Brake Health remain active |
| One source and two Unit roles | Future `CR-DEMO` | Exact sequential VU/DU source binding or deterministic replay correlation | Evidence is incomplete and cannot support promotion |

## Current Implementation Baseline

| Capability | Current evidence | State for this package |
| --- | --- | --- |
| Repository and source boundary | Component Register allocates proposed `tire-health-service`; repository does not exist | `NEW` |
| ARM64 Aos service candidate | No payload, metadata, build or secret-negative scan | `NEW` |
| VDP v3 compatibility declaration | Accepted architecture and flow require it; no machine-readable service metadata exists | `NEW` |
| KUKSA credential and subscription client | Accepted broker architecture exists; no Tire client implementation | `NEW` |
| Persistent condition estimator | ADR 0008 and system requirements define the boundary; model/state contract absent | `NEW` |
| Functional backend transport | `IF-TIRE-003` defines direction; schema, authentication, queue and acknowledgement absent | `NEW` |
| Typed advisory request | VDP/Gateway target is accepted design; no Tire service request implementation | `NEW` |
| Unit tests and quality gate | No Tire repository or test suite | `NEW` |

## Testability Boundary

Owned logic shall be separated from KUKSA transport, credential acquisition,
backend transport, persistence, clocks and model configuration. Unit tests
inject:

- accepted, stale, missing, malformed and reordered dynamics samples;
- Credential Broker success, rejection, expiry and refresh results;
- deterministic model/configuration bytes and numeric fixtures;
- persistent-state versions, corruption, capacity and restart outcomes;
- backend acknowledgement, duplicate, disconnect, retry and overflow faults;
- advisory target/status fixtures and unauthorized requests;
- monotonic and wall-clock test clocks without sleeping.

The estimator, schema validation, readiness, provenance handling, persistent
state machine, queue, advisory builder and compatibility checks must run
without CARLA, Unreal Engine, QEMU, AosCloud, a real KUKSA Databroker, network
access or credentials. Component and integration tests then prove the packaged
executable against controlled adjacent components.

## Interface Summary

| Interface | Direction | Data or command | Contract/version | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| [Tire dynamics subscription (`IF-TIRE-001`)](../component-decomposition-and-interface-register.md#if-tire-001) | In | Accepted KUKSA vehicle/wheel dynamics, quality and timestamps | VDP Component v3 over `kuksa.val.v1` | Missing/stale/malformed input yields `NOT_EVALUATED` or explicit degraded state | Values published by accepted VDP contract |
| [Credential request (`IF-AUTH-001`)](../component-decomposition-and-interface-register.md#if-auth-001) | Out | Per-instance `AOS_SECRET`, resource and requested path/mode set | Local Credential Broker contract | Rejection/timeout yields no KUKSA connection | Current Aos service instance identity |
| [Short-lived credential (`IF-AUTH-003`)](../component-decomposition-and-interface-register.md#if-auth-003) | In | Rejection or path-scoped short-lived KUKSA JWT | Aos IAM result plus installed VDP contract | Fail closed; never persist, log or widen authority | Aos IAM and VDP contract |
| [Tire functional result (`IF-TIRE-003`)](../component-decomposition-and-interface-register.md#if-tire-003) | Out | Versioned/idempotent condition summary or threshold event | Function Team 2 contract | Queue within fixed bounds; expose overflow/drop; never block local estimate | Service result; backend acknowledgement owns ingestion state |
| [Tire advisory request (`IF-TIRE-002`)](../component-decomposition-and-interface-register.md#if-tire-002) | Out | Typed Tire inspection advisory and correlation | Accepted VDP v3/KUKSA target | Invalid/unavailable/unauthorized path yields no alternate write | Service requests; VDP and Gateway enforce |
| [Tire Health SOTA (`IF-LC-007`)](../component-decomposition-and-interface-register.md#if-lc-007) | Out from release pipeline | Immutable v1.0 ARM64 artifact plus compatibility/permission metadata | Service Provider 2 publication | Technical failure creates no OEM Unit deployment | Function Team 2 artifact; SP publication |
| [Function Team 2 approval (`IF-LC-010`)](../component-decomposition-and-interface-register.md#if-lc-010) | Out from release owner | Explicit validation/promotion decision for exact evidence | Authorized OEM role | Missing/stale/mismatched evidence blocks action | Function Team 2 decision; AosCloud record |
| [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006) | In | Install/start/stop/uninstall/readiness/resource state | Aos service lifecycle | Failure remains factual and does not stop VDP or Brake Health | AosCore/Service Manager actual state |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove all service-owned decisions, validation and state transitions | Deterministic fakes for KUKSA, broker, backend, storage, clocks and model | Yes | `UT-TIRE-*` suite in `tire-health-service` |
| Component | Prove packaged executable and local configuration | Controlled doubles plus built ARM64 artifact | Yes | Process/readiness/resource/restart/uninstall suite |
| Contract | Prove VDP v3 paths, permissions, state schema, results and advisory payload | Digest-addressed fixtures shared with VDP and Tire Cloud | Yes | Positive/negative conformance fixtures |
| Integration | Prove real KUKSA/broker/backend/Aos runtime boundaries | Validation Unit with accepted adjacent revisions | Yes | `T1` integration and fault records |
| End-to-end | Prove local result, Cloud-loss continuity, advisory and independent SOTA promotion | Validation then identical Demonstration promotion | Yes | `AF-TIRE-*` evidence |

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| [One immutable mature v1.0 candidate (`REQ-TIRE-001`)](#req-tire-001) | Produce exactly one prepared credential-free ARM64 Tire Health candidate for this demo | Unit, Component, Contract, Integration | D3 design-reviewed |
| [VDP v3 compatibility and fail-closed readiness (`REQ-TIRE-002`)](#req-tire-002) | Run only against the accepted VDP v3 contract without claiming native Cloud admission | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Least-privilege KUKSA credential lifecycle (`REQ-TIRE-003`)](#req-tire-003) | Acquire and refresh only current IAM-derived path-scoped authority | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Validated native dynamics subscription (`REQ-TIRE-004`)](#req-tire-004) | Consume only accepted dynamics and never consume hidden simulation truth | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Bounded persistent local condition estimate (`REQ-TIRE-005`)](#req-tire-005) | Deterministically maintain a versioned synthetic condition band without exact tread claims | Unit, Component, Analysis, End-to-end | D3 design-reviewed |
| [Explicit degraded behavior (`REQ-TIRE-006`)](#req-tire-006) | Never turn stale, missing or inconsistent data into a healthy result | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Bounded derived Cloud product (`REQ-TIRE-007`)](#req-tire-007) | Send idempotent summaries/events rather than continuous raw telemetry | Unit, Component, Contract, Integration, End-to-end | D3 design-reviewed |
| [Typed inspection advisory (`REQ-TIRE-008`)](#req-tire-008) | Request only the accepted non-safety Tire Health target | Unit, Component, Contract, Integration, End-to-end | D3 design-reviewed |
| [Offline continuity and synchronization (`REQ-TIRE-009`)](#req-tire-009) | Keep local estimation/advisory active and synchronize safely after reconnect | Unit, Component, Integration, Analysis, End-to-end | D3 design-reviewed |
| [Safe uninstall and future state compatibility (`REQ-TIRE-010`)](#req-tire-010) | Remove or replace Tire Health without changing VDP or Brake Health and retain explicit state compatibility | Unit, Component, Integration, Analysis | D3 design-reviewed |
| [Health, resources and tenant isolation (`REQ-TIRE-011`)](#req-tire-011) | Stay inside qualified quotas and isolate failures from other services | Unit, Component, Integration | D3 design-reviewed |
| [Redacted logs and separated timing (`REQ-TIRE-012`)](#req-tire-012) | Emit useful secret-free evidence and separate local latency from Cloud sync | Unit, Component, Integration, Analysis, End-to-end | D3 design-reviewed |

## Detailed Requirements

### One immutable mature v1.0 candidate

<a id="req-tire-001"></a>

- ID: `REQ-TIRE-001`
- Statement: The repository shall produce exactly one prepared immutable credential-free ARM64 Tire Health Service v1.0 candidate for the current demo, identified by semantic version, artifact digest and metadata digest, with exact command, quotas, permissions and VDP v3 compatibility.
- Rationale: Tire Health demonstrates independent multi-tenant lifecycle, not another three-release evolution story.
- Parents: [immutable candidates (`SYS-REL-001`)](../system-requirements-and-traceability.md#sys-rel-001) and [single mature Tire service (`SYS-TIRE-001`)](../system-requirements-and-traceability.md#sys-tire-001)
- Flows: [independent Tire lifecycle (`AF-TIRE-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-lc)
- Verification: Unit, Component, Contract, Integration
- Evidence: reproducible staging bytes, secret-negative scan, exact artifact/metadata digests and release manifest
- State: D3 design-reviewed; no repository or candidate exists

Changed content shall produce a new immutable version/digest. Validation and
Demonstration promotion use identical accepted bytes; no presentation-time
source change, compilation or repackaging is permitted.

### VDP v3 compatibility and fail-closed readiness

<a id="req-tire-002"></a>

- ID: `REQ-TIRE-002`
- Statement: Service v1.0 shall declare the accepted VDP Component v3 compatibility range, verify the installed contract and every mandatory read/advisory path before readiness, and remain fail-closed with a machine-readable reason when the contract is absent, incompatible or incomplete.
- Rationale: Release sequencing and OEM evidence do not replace runtime compatibility enforcement.
- Parent: [service capability compatibility (`SYS-REL-003`)](../system-requirements-and-traceability.md#sys-rel-003)
- Flows: [Tire lifecycle (`AF-TIRE-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-lc) and [failure boundaries (`AF-TIRE-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-fr)
- Verification: Unit, Component, Contract, Integration
- Evidence: compatible/incompatible manifests, readiness reasons and absence of result/advisory side effects
- State: D3 design-reviewed; design only

This is service defense in depth, not native pre-transfer AosCloud admission.
The latter remains deferred until an implementing AosEdge release is available
and qualified; no project-side substitute is permitted.

### Least-privilege KUKSA credential lifecycle

<a id="req-tire-003"></a>

- ID: `REQ-TIRE-003`
- Statement: The service shall use its current per-instance `AOS_SECRET` to request only its declared VDP v3 KUKSA read and Tire advisory permissions, hold only a short-lived JWT in memory, refresh it before expiry, and fail closed after rejection, expiry, permission removal or instance replacement.
- Parents: [least privilege (`SYS-SEC-001`)](../system-requirements-and-traceability.md#sys-sec-001), [KUKSA verifier (`SYS-SEC-004`)](../system-requirements-and-traceability.md#sys-sec-004), and [native-IAM translation (`SYS-SEC-006`)](../system-requirements-and-traceability.md#sys-sec-006)
- Flow: [QM advisory containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Verification: Unit, Component, Contract, Integration
- Evidence: permission matrix, expiry/refresh/revocation fixtures, secret-negative logs and package scan
- State: D3 design-reviewed; design only

### Validated native dynamics subscription

<a id="req-tire-004"></a>

- ID: `REQ-TIRE-004`
- Statement: The service shall subscribe only to the frozen VDP v3 Tire input subset, validate path, type, unit, quality, source timestamp, freshness and ordering before use, and shall have no interface to hidden CARLA tire-degradation truth.
- Parents: [complete source accounting (`SYS-SRC-004`)](../system-requirements-and-traceability.md#sys-src-004), [explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005), and [explicit simulation model (`SYS-TIRE-003`)](../system-requirements-and-traceability.md#sys-tire-003)
- Flow: [Tire runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt)
- Verification: Unit, Component, Contract, Integration
- Evidence: frozen path manifest, provenance matrix, stale/malformed fixtures and oracle-negative proof
- State: D3 design-reviewed; exact subset remains a D4 gate

Candidate inputs may include native vehicle speed, acceleration, steering,
applied controls, per-wheel angular velocity, longitudinal slip and lateral
slip angle. Unsupported tire measurements shall not be fabricated.

### Bounded persistent local condition estimate

<a id="req-tire-005"></a>

- ID: `REQ-TIRE-005`
- Statement: From valid accepted inputs, the service shall deterministically update one bounded versioned persistent synthetic condition state and emit a condition band, confidence and inspection decision without claiming exact measured tread depth or production diagnostic accuracy.
- Parent: [local persistent condition estimate (`SYS-TIRE-002`)](../system-requirements-and-traceability.md#sys-tire-002)
- Flow: [Tire runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt)
- Verification: Unit, Component, Analysis, End-to-end
- Evidence: immutable model/config digest, numeric fixtures, restart sequence and ten-repeat scenario result
- State: D3 design-reviewed; model, bands, thresholds and persistence format remain D4 gates

The demo may use a labelled accelerated or pre-aged initial condition, but the
service must reach its result from observable inputs and service-owned state,
not a hidden simulator oracle.

### Explicit degraded behavior

<a id="req-tire-006"></a>

- ID: `REQ-TIRE-006`
- Statement: Missing, stale, malformed, contradictory or insufficient mandatory inputs shall produce `NOT_EVALUATED` or an equally explicit degraded result, shall not advance condition as if evidence were valid, and shall never be reported as healthy.
- Parents: [explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005) and [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003)
- Flow: [Tire failure boundaries (`AF-TIRE-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-fr)
- Verification: Unit, Component, Contract, Integration
- Evidence: missing/stale/malformed/contradictory matrix and recovery fixtures
- State: D3 design-reviewed

### Bounded derived Cloud product

<a id="req-tire-007"></a>

- ID: `REQ-TIRE-007`
- Statement: Normal operation shall send only bounded, versioned and idempotent tire-condition summaries and threshold/change events with original event time, Unit/source correlation and service/VDP versions; it shall not continuously stream raw vehicle telemetry.
- Parents: [bounded Cloud reporting (`SYS-TIRE-004`)](../system-requirements-and-traceability.md#sys-tire-004) and [independent Tire product (`SYS-TIRE-005`)](../system-requirements-and-traceability.md#sys-tire-005)
- Flows: [Tire runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt) and [observability (`AF-TIRE-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-ob)
- Verification: Unit, Component, Contract, Integration, End-to-end
- Evidence: schema/size/rate fixtures, duplicate handling, backend acknowledgement and dashboard record
- State: D3 design-reviewed; message schema and bounds remain D4 gates

### Typed inspection advisory

<a id="req-tire-008"></a>

- ID: `REQ-TIRE-008`
- Statement: When the accepted local state meets the frozen advisory policy, the service shall request only its typed VDP v3 Tire Health inspection target with bounded value, severity/reason, freshness and correlation and shall never issue arbitrary text or a vehicle-motion command.
- Parents: [allowlisted outbound advisory (`SYS-VDP-004`)](../system-requirements-and-traceability.md#sys-vdp-004), [offline Tire advisory (`SYS-TIRE-006`)](../system-requirements-and-traceability.md#sys-tire-006), and [QM containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Flows: [Tire runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt) and [QM containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Verification: Unit, Component, Contract, Integration, End-to-end
- Evidence: allowlisted target fixture, malformed/unauthorized negatives, correlation and factual Gateway status
- State: D3 design-reviewed; target payload and policy remain D4 gates

### Offline continuity and synchronization

<a id="req-tire-009"></a>

- ID: `REQ-TIRE-009`
- Statement: Cloud/backend loss shall not stop valid local estimation or advisory generation; unsent derived messages shall use bounded persistent retention, backoff and idempotent reconnect synchronization while preserving original event times and explicit overflow/drop evidence.
- Parents: [bounded reporting (`SYS-TIRE-004`)](../system-requirements-and-traceability.md#sys-tire-004) and [offline advisory (`SYS-TIRE-006`)](../system-requirements-and-traceability.md#sys-tire-006)
- Flow: [offline continuity (`AF-X-OFFLINE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Verification: Unit, Component, Integration, Analysis, End-to-end
- Evidence: disconnect/restart/reconnect sequence, bounded-state measurement, duplicate proof and original-time dashboard result
- State: D3 design-reviewed; capacities, retention and retry remain D4 gates

### Safe uninstall and future state compatibility

<a id="req-tire-010"></a>

- ID: `REQ-TIRE-010`
- Statement: Removal or failed installation of Tire Health v1.0 shall leave VDP v3, Brake Health and their state/lifecycles unchanged; persistent state shall carry an explicit schema version and future service candidates shall declare migrate, preserve or reject behavior before readiness.
- Parents: [dependent-first rollback (`SYS-REL-005`)](../system-requirements-and-traceability.md#sys-rel-005) and [team-owned release decisions (`SYS-REL-007`)](../system-requirements-and-traceability.md#sys-rel-007)
- Flows: [Tire lifecycle (`AF-TIRE-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-lc) and [failure boundaries (`AF-TIRE-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-fr)
- Verification: Unit, Component, Integration, Analysis
- Evidence: failed-install/uninstall test, unaffected-service evidence and state-version fixtures
- State: D3 design-reviewed

### Health, resources and tenant isolation

<a id="req-tire-011"></a>

- ID: `REQ-TIRE-011`
- Statement: The service shall expose truthful health/readiness, declare and remain within qualified CPU, memory, storage, file and process bounds, stop safely on quota/resource failure, and shall not degrade VDP, Brake Health or vehicle control.
- Parents: [independent Tire product (`SYS-TIRE-005`)](../system-requirements-and-traceability.md#sys-tire-005) and [QM containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Flow: [Tire failure boundaries (`AF-TIRE-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-fr)
- Verification: Unit, Component, Integration
- Evidence: quota/load/crash matrix, restart status and unaffected Brake/VDP evidence
- State: D3 design-reviewed; budgets remain D4 measurement gates

### Redacted logs and separated timing

<a id="req-tire-012"></a>

- ID: `REQ-TIRE-012`
- Statement: The service shall emit bounded structured English logs with Unit/service/version/correlation and factual state transitions while redacting secrets/tokens and shall measure local input-to-condition/advisory latency separately from backend synchronization latency.
- Parents: [native operational logs (`SYS-OBS-001`)](../system-requirements-and-traceability.md#sys-obs-001), [operational log controls (`SYS-OBS-003`)](../system-requirements-and-traceability.md#sys-obs-003), and [separate timing (`SYS-TIM-002`)](../system-requirements-and-traceability.md#sys-tim-002)
- Flow: [Tire observability (`AF-TIRE-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-ob)
- Verification: Unit, Component, Integration, Analysis, End-to-end
- Evidence: redaction fixtures, native-log retrieval record and separated latency report
- State: D3 design-reviewed

## Stable Unit-Test Obligations

| Test obligation | Requirement coverage | Required proof |
| --- | --- | --- |
| <a id="ut-tire-001"></a>`UT-TIRE-001` | `REQ-TIRE-001` | Reproducible candidate identity, changed-content digest and secret-negative package scan |
| <a id="ut-tire-002"></a>`UT-TIRE-002` | `REQ-TIRE-002` | Compatible v3 readiness and absent/incompatible/incomplete fail-closed reasons |
| <a id="ut-tire-003"></a>`UT-TIRE-003` | `REQ-TIRE-003` | Exact permission request, expiry/refresh/revocation and no token persistence/logging |
| <a id="ut-tire-004"></a>`UT-TIRE-004` | `REQ-TIRE-004`, `REQ-TIRE-006` | Path/type/unit/quality/freshness validation and oracle-negative boundary |
| <a id="ut-tire-005"></a>`UT-TIRE-005` | `REQ-TIRE-005` | Deterministic model vectors, bounded state, persistence restart and band transition |
| <a id="ut-tire-006"></a>`UT-TIRE-006` | `REQ-TIRE-007`, `REQ-TIRE-009` | Bounded result rate/size, queue overflow, retry, idempotency and original event time |
| <a id="ut-tire-007"></a>`UT-TIRE-007` | `REQ-TIRE-008` | Only the accepted typed target succeeds; malformed/arbitrary/motion requests fail |
| <a id="ut-tire-008"></a>`UT-TIRE-008` | `REQ-TIRE-010` | Failed install/uninstall leaves unrelated state intact and state-version policy is explicit |
| <a id="ut-tire-009"></a>`UT-TIRE-009` | `REQ-TIRE-011` | Health/readiness truth, quota failure and isolation from VDP/Brake test doubles |
| <a id="ut-tire-010"></a>`UT-TIRE-010` | `REQ-TIRE-012` | Secret redaction, bounded logs and separate local/Cloud timing fields |

Each obligation must execute deterministically without CARLA, QEMU, AosCloud,
a real KUKSA Databroker, network access or credentials. Integration and
end-to-end tests supplement these obligations; they do not replace them.

## Open D4 Gates

| Gate | Why it blocks implementation acceptance | Owner |
| --- | --- | --- |
| Exact VDP v3 Tire input paths, types, units, cadence, quality and freshness | Blocks subscription contract and compatibility metadata | Platform Team + Function Team 2 |
| Accelerated/pre-aged stimulus, service-visible initial estimate and hidden qualification oracle | Blocks honest deterministic demonstration without oracle leakage | Vehicle Simulation + Function Team 2 |
| Synthetic estimator, state schema, bands, confidence, thresholds and tolerance | Blocks deterministic model/state tests | Function Team 2 |
| Summary/event schemas, authentication, idempotency key, rate/size and acknowledgement | Blocks service-to-backend contract | Function Team 2 + future `CR-TIRE-CLOUD` |
| Tire advisory target, payload, debounce/hysteresis, freshness and Gateway correlation | Blocks typed outbound request | Function Team 2 + Platform Team + Gateway |
| Queue/state capacity, retention, retry/backoff, overflow and future migration policy | Blocks offline and uninstall qualification | Function Team 2 |
| CPU/RAM/storage/file/process quotas and health/readiness endpoint | Blocks resource and failure-isolation acceptance | Function Team 2 + Aos integration |
| Local decision and Cloud synchronization timing budgets plus log schema/redaction | Blocks observability and timing acceptance | Function Team 2 + Demo experience |
| Native Cloud service-to-VDP dependency admission | Deferred platform roadmap item; does not block v1.0 when sequencing, OEM evidence and fail-closed readiness are proved | AosEdge Platform Team |

## Change Rules

- Editorial clarification preserves stable `REQ-TIRE-*` and `UT-TIRE-*` IDs.
- A material semantic replacement receives a new ID and retains the old
  definition in a clearly labelled retired section with a replacement link.
- A changed component, interface, lifecycle, authority, credential boundary,
  QM boundary or data direction follows the Level-C architecture cascade.
- A model, state, signal subset, payload, threshold, resource or timing change
  inside accepted boundaries follows the Level-B cascade and updates
  requirements, fixtures, tests and evidence together.
- Adding a future Tire service release does not rewrite v1.0; it creates a new
  immutable candidate with explicit compatibility and state-migration rules.
