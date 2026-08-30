<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health In-Vehicle Service Component Requirements

- Status: D4 exact v2 contract complete; ready for implementation review
- Package: [`CR-BHS`](../component-decomposition-and-interface-register.md#cr-bhs)
- Version: 0.9
- Prepared: 2026-08-29
- Owner: Function Team 1 / Service Provider 1 / SOTA 1
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Accepted architecture decisions: [ADR 0009](../../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md), [ADR 0011](../../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md), [ADR 0012](../../architecture/decisions/0012-authorize-running-workloads-not-software-artifacts.md) and [ADR 0013](../../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md)
- Previous accepted package: Version 0.8
- Reviewed D4 working direction: [D4-003 deterministic stimuli and calibration](../d4-decision-register.md#d4-003)
- Accepted D4 compatibility input: [D4-007 VDP Compatibility Profile](../../../contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json)
- Accepted D4 advisory input: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Accepted D4 v1 contract: [D4-016.1/.2 decision](../d4-decision-register.md#d4-016) and [executable Brake Telemetry Window Contract](../../../contracts/brake-telemetry-window/README.md)
- Accepted D4 exact contracts: [v2 synthetic model](../../../contracts/brake-health-model/README.md), [v3 advisory policy](../../../contracts/brake-health-advisory-policy/README.md), [runtime/evidence profile](../../../contracts/brake-health-runtime/README.md) and [Brake Cloud API](../../../contracts/brake-cloud-api/README.md)
- Implementation baseline: `brake-health-service@04abe5b`

## Purpose

This package defines the independently deployable in-vehicle Brake Health
service owned by Function Team 1. The service consumes only the accepted
Vehicle Data Platform KUKSA contract and evolves one post-SOP product through
three audience-visible data-processing stages: bounded high-detail braking
event acquisition in v1, deterministic synthetic local assessment and
derived-event reporting in v2, and a narrowly typed maintenance advisory in
v3. Its local decision path continues when Cloud connectivity is unavailable.

The service is a QM-domain maintenance and inspection application. It has no
allocated safety goal, no vehicle-motion authority, no direct driver-HMI
claim, and no authority to bypass the Vehicle Data Platform or Vehicle
Gateway. Service Provider publication is not deployment approval; Function
Team 1 owns Validation Unit testing and acceptance, while independent OEM
Release Authority separately authorizes every Test deployment and Production
rollout affecting OEM Units.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Service v1-v3 application behavior, KUKSA client use, v1 pre-trigger/event/post-trigger recorder, deterministic synthetic v2 assessment, bounded functional message queue, typed v3 advisory request, service packaging, compatibility, resources, health, logs and tests |
| What this package does not own | CARLA or brake-condition ground truth, VISS, Vehicle Data Platform Provider/policy, KUKSA executable/trust, `CMP-KAC` implementation, Gateway advisory enforcement, Aos lifecycle execution, backend persistence or functional dashboard |
| Intended result | The same independently deployable SOTA product progresses from finite high-detail event windows to on-board derived assessments/events and finally to an offline-capable typed maintenance advisory |
| Accountable lifecycle owner | Function Team 1 publishes and accepts the exact Validation Unit result; independent OEM Release Authority authorizes Test deployment and Production rollout through SOTA 1 |
| Primary repository | [`brake-health-service` architecture](../../../../brake-health-service/docs/architecture.md) |

## Component Boundary

### In scope

- ARM64 Aos service packaging and immutable Service v1-v3 release metadata;
- declared Vehicle Data Platform compatibility range and fail-closed readiness;
- fixed-resource bootstrap with per-instance `AOS_SECRET` at the local
  `CMP-KAC` boundary;
- private volatile short-lived KUKSA JWT consumption, refresh and rejection handling;
- accepted KUKSA read/subscription inputs and data-quality handling;
- v1 bounded ring buffer, braking trigger, pre/active/post event-window state
  machine and ordered/idempotent chunk transfer;
- v2 immutable synthetic demo model, deterministic local assessment,
  provenance-labelled result and derived-only normal Cloud data product;
- v3 narrowly typed Brake Health maintenance-advisory request;
- bounded offline functional-message persistence, retry, overflow and
  idempotency behavior;
- service-owned health, readiness, resource, timing, logging and recovery behavior.

### Out of scope

- simulator signals, hidden qualification truth or obstacle/braking scenario;
- VISS transport, KUKSA publication, OEM policy or `CMP-KAC` implementation;
- KUKSA Databroker modification or an embedded reusable KUKSA token;
- arbitrary VSS/KUKSA writes, display text, throttle, brake, steer, gear or any
  safety-critical or vehicle-motion command;
- Brake Health backend ingestion/persistence and Function Dashboard;
- SOTA verification batches, Unit targeting, OEM approval or AosCloud execution;
- live model training, production driver HMI or functional-safety certification.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Accepted Vehicle Data Platform contract | `CR-VDP` | Exact compatible version, KUKSA paths, types, units, quality and freshness behavior | Service remains not ready and produces no accepted report/advisory |
| Native Aos service identity and IAM permissions | `CR-AOS` plus `CR-KAC` | Current instance registered, valid `AOS_SECRET`, fixed `kuksa` bootstrap resource and exact registered path/mode permissions | Bootstrap/JWT acquisition fails closed; no cached privilege extension |
| Deterministic Brake Health stimulus and input truth | `CR-VEHICLE-SIM`, `CR-GATEWAY`, `CR-VDP` | Versioned scenario/profile and accepted provenance labels | Model qualification is invalid; no audience prediction claim |
| Brake Health backend contract | `CR-BRAKE-CLOUD` | Versioned authenticated endpoint, v1 chunk/completion reconstruction, v2/v3 derived-message schemas and idempotent acknowledgement | Functional messages remain in bounded local queue; local assessment/advisory continues |
| Aos runtime and resource enforcement | `CR-AOS` | Service install/start/stop/update state and declared quotas enforced | Service reports unavailable/error; platform and vehicle-data path remain active |
| Accepted advisory capability | `CR-VDP` and `CR-GATEWAY` | Typed target, permission, payload, freshness, correlation and factual status contract | Service v3 remains not ready for advisory or reports rejection without fallback command |

## Current Implementation Baseline

| Capability | Current evidence | State for this package |
| --- | --- | --- |
| Repository and ownership boundary | [`architecture`](../../../../brake-health-service/docs/architecture.md) and boundary tests reject CARLA/VISS/provider coupling | `CURRENT` scaffold boundary |
| ARM64 Aos packaging | Schema-v2 service metadata, unsigned staging builder and credential-negative tests | `CURRENT` scaffold; signing/deployment unqualified |
| Compatibility declaration | `>=0.1.0,<0.2.0`, `kuksa.val.v1`, ARM64 and read-only resource intent | `CURRENT` draft metadata; runtime enforcement absent |
| Resource declaration | 250 DMIPS CPU, 16 MiB RAM, 8 MiB storage, 1 MiB state, 8 MiB tmp, 64 files and 16 processes | D4-023.2 requested envelope accepted; live OCI/cgroup mapping and headroom evidence absent |
| Executable behavior | Prints one English diagnostic line and exits | `CURRENT`; no product behavior |
| KUKSA credential and subscription client | Architecture boundary documented; no implementation | `NEW` |
| v1 event-window recorder and backend transport | Acquisition, logical chunk/completion, local spool and D4-017 transport/durable-ack contracts accepted; no implementation; production backend authentication remains out of scope | `NEW` |
| v2 synthetic model, local assessment and derived output | No model, input/output contract or implementation | `NEW` |
| v3 advisory request | Current scaffold intentionally requests read-only `kuksa`; no target or write permission | `NEW`; contract accepted, implementation and real platform/Gateway qualification open |
| Unit tests and quality gate | Four scaffold/boundary tests and repository quality gate pass | `CURRENT` foundation; product obligations below are not implemented |

The source packaging guide still reflects an obsolete caller-selected
permission request and separate-policy model. Before implementation acceptance,
it must use the fixed-resource `CMP-KAC` bootstrap: the Service supplies no
paths, operations, subject, audience, TTL or claims, and the helper derives the
JWT only from the current Aos IAM result.

## Testability Boundary

Owned logic shall be separated from KUKSA transport, authorization bootstrap,
backend transport, persistence, clocks and model loading. Unit tests inject:

- KUKSA samples, quality, source/event timestamps, braking-trigger transitions
  and connection transitions;
- `CMP-KAC` private-JWT success, rejection, expiry and refresh results;
- immutable model bytes/configuration and deterministic numeric fixtures;
- monotonic and wall-clock test clocks without sleeping;
- bounded ring-buffer/window/chunk storage, backend acknowledgement, retry and
  overflow faults;
- advisory target/status fixtures and malformed or unauthorized requests.

The trigger/window engine, decision engine, schema validation, provenance
handling, queue state machine, compatibility/readiness logic and payload
builders must run without
Unreal Engine, CARLA, QEMU, AosCloud, a real KUKSA Databroker, network access or
credentials. Component and integration tests then prove the packaged
executable against controlled real adjacent components.

## Accepted Implementation Decomposition

The accepted implementation remains one `brake-health-service` repository and
one independently deployable Service product family. Versions v1, v2 and v3
are immutable release compositions from that codebase, not separate logical
components or repositories. The implementation baseline is C++17 with CMake so
the deterministic domain logic can be tested without a VM, KUKSA, KAC, Cloud
or backend and the ARM64 runtime envelope can be measured rather than hidden
behind a heavyweight language runtime.

Implementation proceeds through bounded sequential Service packets:

1. `BHS-CORE-001` — domain foundation, v1 event-window state machine, bounded
   ring buffer/local spool and canonical chunk/completion contract tests;
2. `BHS-CORE-002` — deterministic v2 model, assessment/event output,
   persistent state and v1-to-v2 transition;
3. `BHS-CORE-003` — v3 advisory request lifecycle, matching factual Gateway
   Status and correlated backend advisory fact;
4. `BHS-ADAPTERS-001` — KAC/token lifecycle, KUKSA transport, backend durable
   delivery, bounded offline synchronization, health and structured logs; and
5. `BHS-PACKAGING-001` — exact v1/v2/v3 composition, metadata, permissions,
   quotas, compatibility and reproducible unsigned ARM64 Aos artifacts.

These packets are sequential writers in the same repository. The independent
`brake-health-cloud` repository may be implemented concurrently after its own
repository-creation and work-packet gates close. `BHS-CORE-001` through the
pure domain portions of `BHS-CORE-003` do not depend on a working KAC package;
real KAC/KUKSA/backend integration begins only in `BHS-ADAPTERS-001`.

## Interface Summary

| Interface | Direction | Data or command | Contract/version | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| [Brake Health data subscription (`IF-DATA-002`)](../component-decomposition-and-interface-register.md#if-data-002) | In | Accepted KUKSA read/subscribe values, quality and timestamps | Versioned Vehicle Data Platform contract over `kuksa.val.v1` | Missing/stale/malformed/disconnected input becomes explicit degraded/unavailable state | KUKSA values published by accepted VDP contract |
| [Fixed-resource bootstrap (`IF-AUTH-007`)](../component-decomposition-and-interface-register.md#if-auth-007) | Out | Per-instance `AOS_SECRET` plus fixed `kuksa` resource; no caller-selected authority | Local `CMP-KAC` contract | Rejection, timeout or invalid response yields no KUKSA connection | Current Aos service instance identity |
| [Private JWT or rejection (`IF-AUTH-009`)](../component-decomposition-and-interface-register.md#if-auth-009) | In | Rejection or short-lived path-scoped KUKSA JWT through a Service-private volatile location | Current Aos IAM result translated by `CMP-KAC` | Fail closed; never persist, log or widen token authority | Aos IAM result and protected platform signer |
| [Functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001) | Out | Ordered/idempotent v1 `BrakeTelemetryWindow` chunks plus completion; v2/v3 `BrakeHealthAssessment`, threshold/change `BrakeHealthEvent`, and correlated advisory fact | Function Team 1 contract | Resume/queue within fixed bounds, retry by policy, expose overflow/drop; never block local assessment | Service result; backend acknowledgement owns ingestion state |
| [Advisory request (`IF-ADV-001`)](../component-decomposition-and-interface-register.md#if-adv-001) | Out | Typed Brake Health maintenance-advisory target and correlated payload | Accepted v3 VDP/KUKSA advisory contract | Invalid/unavailable/unauthorized path yields no alternate write or motion command | Service requests; VDP and Gateway enforce |
| [Brake Health SOTA (`IF-LC-002`)](../component-decomposition-and-interface-register.md#if-lc-002) | Out from release pipeline | Immutable ARM64 service artifact and compatibility/permission metadata | Service Provider 1 publication contract | Technical failure creates no OEM Unit deployment | Function Team 1 artifact; SP publication |
| [Function Team 1 acceptance and OEM Release Authority authorization (`IF-LC-009`)](../component-decomposition-and-interface-register.md#if-lc-009) | Out from release owner / governance handoff | Function Team 1 accepts exact Validation evidence; independent Release Authority separately authorizes Test deployment and Production rollout | Owning team plus authorized OEM delivery role | Missing/stale/mismatched evidence or either missing decision blocks action | Separate Function Team acceptance, Release Authority authorization and AosCloud record |
| [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006) | In | Install/start/stop/update/removal/readiness/resource state | Aos service lifecycle | Failure remains factual and does not stop VDP or unrelated services | AosCore/Service Manager actual state |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove all owned decisions, validation and state transitions | Deterministic fakes for KUKSA, KAC result, backend, storage, clocks and model | Yes | `UT-BHS-*` suite in `brake-health-service` |
| Component | Prove packaged executable and service-local configuration | Controlled in-process or containerized doubles plus built ARM64 artifact | Yes | Process/readiness/resource/restart and contract-fixture suite |
| Contract | Prove schemas, compatibility, permissions, model identity, reports and advisory payload | Versioned fixtures shared with `CR-VDP` and `CR-BRAKE-CLOUD` | Yes | Digest-addressed conformance fixtures and negative cases |
| Integration | Prove real KUKSA/KAC/backend/Aos runtime boundaries | Validation Unit with accepted adjacent revisions | Yes | G2/G3/G4 integration records and fault matrix |
| End-to-end | Prove local result, offline continuity and advisory presentation | Validation then identical Production promotion | Yes | `AF-G2-*`, `AF-G3-*`, `AF-G4-*` evidence |

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| [Immutable versioned service product (`REQ-BHS-001`)](#req-bhs-001) | Produce credential-free immutable ARM64 v1-v3 service candidates with exact metadata | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Compatibility and fail-closed readiness (`REQ-BHS-002`)](#req-bhs-002) | Start only with a compatible installed Vehicle Data Platform contract | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Fixed-resource KUKSA authorization lifecycle (`REQ-BHS-013`)](#req-bhs-013) | Bootstrap without caller-selected authority and use only private volatile IAM-derived JWTs | Unit, Component, Contract, Integration | D4 design accepted; implementation/qualification open |
| [Validated KUKSA subscription (`REQ-BHS-004`)](#req-bhs-004) | Consume only accepted paths and make data quality/freshness explicit | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Bounded v1 Brake Telemetry Window (`REQ-BHS-005`)](#req-bhs-005) | Detect the accepted hard-braking episode and transfer one fixed 3 s PRE / bounded ACTIVE / 2 s POST window without continuous Cloud streaming | Unit, Component, Contract, Integration, End-to-end | D4-016.1/.2 and D4-017 transport/ack accepted; implementation/qualification open |
| [Deterministic v2 edge assessment (`REQ-BHS-006`)](#req-bhs-006) | Run an immutable synthetic model locally and replace normal v1 window upload with derived assessments/events | Unit, Component, Contract, Analysis, End-to-end | D4-016.3 exact contract accepted; D4-003 calibration qualification open |
| [Degraded and invalid-input behavior (`REQ-BHS-007`)](#req-bhs-007) | Never convert missing, stale or malformed input into a healthy result | Unit, Component, Contract, Integration | D3 design-reviewed |
| [Typed v3 maintenance advisory (`REQ-BHS-008`)](#req-bhs-008) | Request only the accepted non-safety Brake Health advisory | Unit, Component, Contract, Integration, End-to-end | D3 design-reviewed |
| [Offline local continuity and bounded synchronization (`REQ-BHS-009`)](#req-bhs-009) | Keep local analysis/advisory active and synchronize reports safely after reconnect | Unit, Component, Integration, Analysis, End-to-end | D3 design-reviewed |
| [Recovery-safe persistent state (`REQ-BHS-010`)](#req-bhs-010) | Preserve a valid dependent-first removal and recovery path across service versions | Unit, Component, Integration, Analysis | D4-015 design accepted; live qualification open |
| [Health, resources and failure isolation (`REQ-BHS-011`)](#req-bhs-011) | Expose truthful readiness and stay inside qualified quotas without affecting VDP | Unit, Component, Integration | D3 design-reviewed |
| [Redacted native logs and separated chronology (`REQ-BHS-012`)](#req-bhs-012) | Emit useful secret-free evidence and preserve local event/advisory chronology separately from Cloud sync | Unit, Component, Integration, Analysis, End-to-end | D3 design-reviewed |

## Detailed Requirements

### Immutable versioned service product

<a id="req-bhs-001"></a>

- ID: `REQ-BHS-001`
- Statement: The repository shall produce immutable credential-free ARM64 Aos Service v1-v3 candidates identified by semantic version, artifact digest and metadata digest, with exact command, quotas, requested resources/permissions, VDP compatibility and dependency declarations.
- Rationale: Validation and promotion must operate on one unambiguous independently deployable Function Team 1 product.
- Parent system requirement: [Immutable release candidates (`SYS-REL-001`)](../system-requirements-and-traceability.md#sys-rel-001)
- Architecture flows: [Service v1 lifecycle (`AF-G2-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-lc), [joint v2 lifecycle (`AF-G3-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-lc) and [v3 lifecycle (`AF-G4-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-lc)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [Brake Health SOTA (`IF-LC-002`)](../component-decomposition-and-interface-register.md#if-lc-002) and [Function Team 1 approval (`IF-LC-009`)](../component-decomposition-and-interface-register.md#if-lc-009)
- Verification levels: Unit, Component, Contract, Integration
- Required evidence: reproducible unsigned staging result, secret-negative scan, exact artifact/metadata digests, architecture and release manifest
- State: D3 design-reviewed; scaffold packaging exists, product candidates do not

Acceptance requires repeatable bytes from identical inputs, different identity
for changed content, no private key/token/Unit identity, complete third-party
notices, English product content and no CARLA/VISS/platform source dependency.

### Compatibility and fail-closed readiness

<a id="req-bhs-002"></a>

- ID: `REQ-BHS-002`
- Statement: Each service version shall declare and enforce the D4-007 range—Brake v1 on VDP v1-v3, Brake v2 on v2-v3 and Brake v3 only on v3—verify installed identity/capabilities plus its D4-016 read and D4-008 advisory paths before readiness, and remain process-healthy but functionally `NOT_READY` with a machine-readable reason when the capability is absent, incompatible or incomplete. It shall produce no functional report/advisory and shall not crash-loop.
- Rationale: Current AosCloud releases do not yet provide native pre-transfer Service-to-FOTA admission, so service readiness remains required defense in depth.
- Parent system requirement: [Service capability compatibility (`SYS-REL-003`)](../system-requirements-and-traceability.md#sys-rel-003)
- Architecture flows: [Service isolation (`AF-G2-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-fr), [deferred native rejection (`AF-G3-DEP`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-dep) and [joint v2 lifecycle (`AF-G3-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-lc)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [data subscription (`IF-DATA-002`)](../component-decomposition-and-interface-register.md#if-data-002) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Unit, Component, Contract, Integration
- Required evidence: compatible and incompatible manifests, readiness/status reason, absence of report/advisory side effects, no restart loop and automatic recovery after a compatible VDP change
- State: D3 design-reviewed; D4-007 ranges and readiness behavior accepted, runtime enforcement not implemented

This requirement must not be presented as native Cloud admission. After an
implementing platform release is qualified, Cloud rejection and service
readiness remain separate controls.

### Retired: Caller-selected KUKSA credential lifecycle

<a id="req-bhs-003"></a>

- ID: `REQ-BHS-003`
- Disposition: Retired by Version 0.5 and replaced by
  [`REQ-BHS-013`](#req-bhs-013). The Service no longer requests paths, modes or
  JWT claims from a broker inside VDP.
- Historical parent: [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001)

### Validated KUKSA subscription

<a id="req-bhs-004"></a>

- ID: `REQ-BHS-004`
- Statement: The service shall read or subscribe only to the accepted version-specific KUKSA paths, validate type, unit, range, source/event time, quality and freshness, preserve source order or explicitly handle reordering, and expose connection/subscription state without connecting directly to VISS or CARLA.
- Rationale: Functional results are valid only when their input contract and temporal quality are explicit.
- Parent system requirements: [Bounded v1 Brake Telemetry Window (`SYS-BHS-005`)](../system-requirements-and-traceability.md#sys-bhs-005) and [deterministic v2 edge assessment (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002)
- Architecture flows: [Service v1 runtime (`AF-G2-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-rt) and [v2 edge assessment (`AF-G3-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-rt)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interface: [Brake Health data subscription (`IF-DATA-002`)](../component-decomposition-and-interface-register.md#if-data-002)
- Verification levels: Unit, Component, Contract, Integration
- Required evidence: accepted path manifest and fixtures for valid, boundary, malformed, stale, reordered, unavailable and reconnect cases
- State: D3 design-reviewed

### Bounded v1 Brake Telemetry Window

<a id="req-bhs-005"></a>

- ID: `REQ-BHS-005`
- Statement: Service v1 shall implement the accepted [Brake Telemetry Window Contract](../../../contracts/brake-telemetry-window/README.md). It consumes its six-path Brake acquisition subset of VDP v1—speed, longitudinal/lateral/vertical acceleration and accelerator/brake pedal positions—and not the otherwise available VDP v1 steering-angle path; deterministically retains every third complete valid 30 Hz frame as 10 Hz while preserving source time/quality/freshness; and detects only `HARD_BRAKING_EPISODE_V1` after speed at least 10 km/h and brake pedal at least 50% for 200 ms. Longitudinal acceleration is evidence, not an alternate trigger. One UUIDv4 event contains 3 seconds PRE, at most 10 seconds ACTIVE and 2 seconds POST, bounded to 15 seconds/150 samples. ACTIVE clears after 500 ms with pedal below 10% or speed below 0.5 km/h; POST retrigger resumes the same event. The Service durably writes RFC-8785/SHA-256 logical chunks of at most ten samples and 64 KiB canonical uncompressed JSON plus exactly one completion before transport eligibility. Its mode-`0700`/`0600` service-local spool is bounded to eight unacknowledged windows or 4 MiB, needs no database runtime, never evicts retained events for a new one and deletes an event only after D4-017 proves durable acknowledgement of every chunk and completion.
- Rationale: G2 makes acquisition visible and supplies high-detail event evidence for later model work without continuously streaming vehicle telemetry to Cloud.
- Parent system requirement: [Bounded v1 Brake Telemetry Window (`SYS-BHS-005`)](../system-requirements-and-traceability.md#sys-bhs-005)
- Architecture flows: [Service v1 lifecycle (`AF-G2-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-lc), [bounded event acquisition (`AF-G2-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-rt) and [first-service proof (`AF-G2-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-ob)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interface: [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001)
- Verification levels: Unit, Component, Contract, Integration, End-to-end
- Required evidence: exact six-path v1 input manifest; 30-to-10 Hz selection; trigger/clear/POST-reactivation timelines; 3/10/2-second and 150-sample bounds; invalid/stale mandatory-input negatives; terminal-state and queue-overflow fixtures; maximum encoded chunk size; duplicate/reconnect proof; original-sample-time preservation and backend reconstruction/acknowledgement correlation
- State: D4-016.1 acquisition, D4-016.2 logical-message/local-spool and D4-017 transport/durable-ack contracts accepted; implementation and qualification remain open

Accepted terminal states are `COMPLETE`, `TRUNCATED_MAX_DURATION`,
`INCOMPLETE_SOURCE_GAP`, `ABORTED_SERVICE_STOP` and `ABORTED_RESTART`. A
maximum-duration result suppresses retrigger until the clear condition is
observed. No trigger means no functional Cloud upload. Missing, stale or
incomplete mandatory inputs never fabricate or activate a trigger. Backend
disconnect may delay or resume retained chunks but shall not create a new
unrelated event identity or unbounded local capture. At queue capacity, the
new event is not retained and `WINDOW_DROPPED_QUEUE_FULL` is counted and
logged without evicting an older unacknowledged window.

After trigger, canonical event files under
`/storage/brake-health/v1/events/<eventId>/` become transport-eligible only
after same-directory temporary write, synchronization, atomic rename and
directory synchronization. A graceful stop completes a capture as
`ABORTED_SERVICE_STOP`; recovery of an incomplete capture records
`ABORTED_RESTART`; corrupt retained content is quarantined. Unavailable or full
storage yields `NOT_READY_STORAGE` rather than volatile-only success.

### Deterministic v2 edge assessment

<a id="req-bhs-006"></a>

- ID: `REQ-BHS-006`
- Statement: Service v2 shall apply immutable digest-bound `brake-condition-demo-v1` with the disclosed `DEMO_PRECONDITIONED` profile to each eligible completed D4-016.1 episode. Its exact VDP v2/v3 model subset is speed, longitudinal acceleration, brake-pedal position, steering angle, four wheel-linear-speed paths and four wheel-angular-speed paths; lateral/vertical acceleration and accelerator pedal are excluded. One adapter conversion supplies the accepted fixed-point units; the core performs the exact integer feature reduction over the complete retained PRE/ACTIVE/POST episode, with features restricted to ACTIVE and wheel dispersion to qualified near-straight ACTIVE samples. It shall maintain one bounded crash-safe synthetic condition state and atomically admit one idempotent `BrakeHealthAssessment` plus a `BrakeHealthEvent` only on an actual band change. Invalid input returns only the accepted local/non-wire/non-persistent reason and mutates no state/ledger. Derived-pair overflow advances state/ledger once, enqueues neither and cannot fabricate a later message. Restart shall not double-count a source event, alter its processing timestamp or duplicate a message. Normal v2 operation sends only derived messages, not Service v1 high-detail windows, and local assessment does not require Cloud/backend connectivity.
- Rationale: The demo proves that post-SOP processing moved from Cloud data exploration into the vehicle and reduced normal Cloud data volume; it does not sell or qualify a production brake-diagnostic algorithm.
- Parent system requirements: [Deterministic v2 edge assessment (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002) and [derived v2 Cloud data product (`SYS-BHS-006`)](../system-requirements-and-traceability.md#sys-bhs-006)
- Architecture flows: [joint v2 lifecycle (`AF-G3-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-lc), [local assessment (`AF-G3-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-rt) and [edge-analytics proof (`AF-G3-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-ob)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [data subscription (`IF-DATA-002`)](../component-decomposition-and-interface-register.md#if-data-002) and [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001)
- Verification levels: Unit, Component, Contract, Analysis, End-to-end
- Required evidence: model/config/input/output digests, golden normal/degraded/invalid fixtures, repeated and reordered execution, provenance/result schemas, correlated local chronology and proof that normal v2 operation emits no v1 window chunks
- State: D4-016.3 complete input/invalid/boundary fixtures, exact arithmetic, identities/provenance/timestamps, derived-message admission and state recovery accepted; D4-003 scripted-stimulus/demo-timing qualification and implementation review remain open

No live training, nondeterministic network model call, mutable downloaded
model or Cloud result may be part of the local decision path. The synthetic
model must be causally driven by the visible CARLA braking episode and explicit
enough for deterministic tests, but D3 does not prescribe a scientifically
validated wear or failure-prediction algorithm and permits no production
accuracy, remaining-useful-life or safety-function claim.

The CARLA/Gateway boundary shall not fabricate brake-pad wear, temperature,
pressure or a health result for this service. D4-003 freezes and qualifies the
visible native braking episode as the causal stimulus; the service-owned
synthetic assessment and its exact input/threshold contract are frozen under
D4-016.3. Hidden scenario truth shall not be used as a service input.

### Degraded and invalid-input behavior

<a id="req-bhs-007"></a>

- ID: `REQ-BHS-007`
- Statement: Missing, stale, malformed, out-of-range, contradictory or disconnected required input shall produce an explicit bounded unavailable/degraded result, shall never be replaced with a fabricated normal value, and shall suppress any advisory whose accepted preconditions cannot be proved.
- Rationale: A false healthy result or ungrounded maintenance advisory would make the audience-visible edge-assessment claim misleading.
- Parent system requirement: [Deterministic v2 edge assessment (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002)
- Architecture flows: [local assessment (`AF-G3-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-rt), [v2 failure ownership (`AF-G3-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-fr) and [fail-closed advisory (`AF-G4-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-fr)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [data subscription (`IF-DATA-002`)](../component-decomposition-and-interface-register.md#if-data-002), [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001) and [advisory request (`IF-ADV-001`)](../component-decomposition-and-interface-register.md#if-adv-001)
- Verification levels: Unit, Component, Contract, Integration
- Required evidence: complete invalid/degraded fixture matrix, emitted result/reason and proof of no advisory side effect
- State: D3 design-reviewed

### Typed v3 maintenance advisory

<a id="req-bhs-008"></a>

- ID: `REQ-BHS-008`
- Statement: Service v3 shall retain the v2 derived assessment/event behavior and write only a D4-008 canonical Request to `Vehicle.OEM.BrakeHealth.Advisory.Request` when an accepted assessment newly enters `INSPECTION_RECOMMENDED`, or exactly once on v3 activation when persistent accepted state is already in that band and no advisory is recorded for its last assessment ID. Activation shall reuse that assessment as `decisionId` and fabricate no assessment or band-change event. The Service shall use persistent producer epoch and monotonic sequence, unique request/decision correlation, explicit `SET`/`CLEAR`, only `INSPECTION_RECOMMENDED` and `PREDICTED_BRAKE_DEGRADATION`, the accepted freshness/lease/rate bounds, and shall have no code or permission path for arbitrary text, Tire target, arbitrary VSS/KUKSA write, vehicle motion or safety-critical actuation.
- Rationale: The demo needs a local offline-capable maintenance indication while preserving authoritative platform and Gateway containment.
- Parent system requirements: [Allowlisted v3 advisory (`SYS-BHS-003`)](../system-requirements-and-traceability.md#sys-bhs-003), [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003) and [QM service and Gateway containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Architecture flows: [v3 lifecycle (`AF-G4-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-lc), [local advisory (`AF-G4-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-rt), [advisory proof (`AF-G4-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-ob) and [fail-closed advisory (`AF-G4-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-fr)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [advisory request (`IF-ADV-001`)](../component-decomposition-and-interface-register.md#if-adv-001) and [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001)
- Verification levels: Unit, Component, Contract, Integration, End-to-end
- Required evidence: exact Request/Status schema fixtures, D4-016 threshold/debounce behavior, request/backend-fact correlation, duplicate/replay/clear/expiry/restart cases and negative proof for every prohibited authority
- Executable contract: [Typed QM Advisory Profile 1.0.2](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- State: D3 design-reviewed; D4-008 interface and exact D4-016.4 v3 policy accepted; real KUKSA/VDP/VISS/Gateway qualification remains open

The accepted audience claim ends at the matching factual Gateway Status,
including `APPLIED`, `CLEARED`, `REJECTED`, `EXPIRED` or `FAILED`, in the
Engineering Telematics Dashboard. KUKSA/VISS Set success is not application
evidence, and no status is driver display or acknowledgement.

### Offline local continuity and bounded synchronization

<a id="req-bhs-009"></a>

- ID: `REQ-BHS-009`
- Statement: Loss of the vehicle external-connectivity domain shall not stop KUKSA consumption, local assessment or an otherwise authorized advisory. The single demo fault removes Unit-to-AosCloud and functional-backend transport together; in-progress/completed v1 chunks and v2/v3 derived messages shall enter bounded persistent state/queues with explicit capacity, overflow, retry/backoff, acknowledgement and idempotent resume behavior while preserving original sample/event times.
- Rationale: The primary value of on-board analysis is timely local behavior independent of coverage.
- Parent system requirement: [Offline local continuity (`SYS-BHS-004`)](../system-requirements-and-traceability.md#sys-bhs-004)
- Architecture flows: [service isolation (`AF-G2-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-fr), [local advisory (`AF-G4-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-rt), [offline proof (`AF-G4-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-ob), [offline continuity (`AF-G4-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-fr) and [targeted vehicle external-connectivity loss (`AF-X-OFFLINE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interface: [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001)
- Verification levels: Unit, Component, Integration, Analysis, End-to-end; the single vehicle fault proves both local continuity and functional-backend delay/reconnect
- Required evidence: disconnect/reconnect timelines during each v1 window phase and v2/v3 messaging, bounded queue/disk use, overflow fact, retry schedule, duplicate-safe acknowledgement, reconstruction/resume identity and unchanged local decision/advisory behavior
- State: D3 design-reviewed

### Recovery-safe persistent state

<a id="req-bhs-010"></a>

- ID: `REQ-BHS-010`
- Statement: Service state, model/configuration and offline queue formats shall be versioned and bounded so accepted dependent-first recovery can stop or remove the newer Service through Subject-service unassignment before its required VDP capability changes, preserve unrelated services, and either read, migrate or explicitly quarantine existing state without silent loss or incompatible execution. Reassignment occurs only after the VU-qualified VDP repair; selection of an arbitrary previous Service Version is not claimed.
- Rationale: An independently updateable SOTA product must not make the platform graph or its own recovery path irreversibly invalid.
- Parent system requirement: [Dependent-first recovery (`SYS-REL-005`)](../system-requirements-and-traceability.md#sys-rel-005)
- Architecture flows: [v2 failure ownership (`AF-G3-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-fr), [v3 failure recovery (`AF-G4-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-fr) and [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interface: [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Unit, Component, Integration, Analysis
- Required evidence: state compatibility matrix, forward/backward fixtures, interrupted transition, Service removal/absence, VU-qualified VDP repair and safe reassignment sequence
- State: D4-015 design accepted; scaffold has no persistent state and live recovery qualification remains open

### Health, resources and failure isolation

<a id="req-bhs-011"></a>

- ID: `REQ-BHS-011`
- Statement: The service shall expose AosCore-owned process health separately from `OPERATIONAL`, `DEGRADED` and `NOT_READY` functional capability. Backend/AosCloud loss shall not gate local analytics; absence of an eligible episode, one insufficient-input result or one failed advisory command shall remain an outcome rather than a readiness failure. The service shall remain within qualified CPU, memory, storage, state, temporary-storage, file, process, capture/chunk and derived-message-rate bounds and shall implement no resource manager. CPU enforcement shall throttle at the approved limit without stop, restart or redeployment; no equivalent behavior is claimed for non-CPU overruns. A Service crash, resource failure or backend failure shall not stop the Vehicle Data Platform, KUKSA or unrelated services.
- Rationale: Aos lifecycle state must not report a running but unusable or unbounded functional service as accepted.
- Parent system requirements: [Service capability compatibility (`SYS-REL-003`)](../system-requirements-and-traceability.md#sys-rel-003), [offline local continuity (`SYS-BHS-004`)](../system-requirements-and-traceability.md#sys-bhs-004) and [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](../system-requirements-and-traceability.md#sys-res-001)
- Architecture flows: [service isolation (`AF-G2-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-fr), [v2 failure ownership (`AF-G3-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-fr), [runtime enforcement (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release) and [AosCore tenant isolation (`AF-TIRE-RES`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-res)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interface: [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Unit, Component, Integration
- Required evidence: process/capability state matrix, v3 initial advisory-ready acceptance followed by degraded recovery, resource measurements and AosCore limit faults, restart/state recovery or quarantine and adjacent-component continuity; during the prepared Tire CPU saturation proof, Brake remains ready without restart and processes the deterministic CARLA event/result/advisory
- State: D4-016.5 design accepted; scaffold quotas remain provisional until D4-023 qualification

### Redacted native logs and separated chronology

<a id="req-bhs-012"></a>

- ID: `REQ-BHS-012`
- Statement: The service shall emit bounded English structured allowlisted events sufficient to correlate version, start/readiness, KUKSA/backend connection state, v1 window phase/chunk state, model/input-quality state, derived event, queue transition and advisory request/result. Repetitions shall be rate-limited and aggregated. It shall not log credentials, tokens, certificates, VIN, raw protocol frames or raw/high-rate telemetry samples, shall not claim CPU/RAM quota enforcement, and shall rely on AosCore/AosCloud native evidence for those resource facts. It shall preserve distinct source-event, local result/advisory and backend receipt/synchronization timestamps so the Cloud path is never presented as part of the on-board decision path; quantitative latency benchmarking is deferred.
- Rationale: Technical evidence must diagnose local behavior without leaking credentials or conflating Cloud delay with on-board response.
- Parent system requirements: [Operational log controls (`SYS-OBS-003`)](../system-requirements-and-traceability.md#sys-obs-003) and [separate on-board and Cloud chronology (`SYS-TIM-002`)](../system-requirements-and-traceability.md#sys-tim-002)
- Architecture flows: [first-service proof (`AF-G2-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-ob), [edge-analytics proof (`AF-G3-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-ob) and [advisory proof (`AF-G4-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-ob)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [functional message family (`IF-FUNC-001`)](../component-decomposition-and-interface-register.md#if-func-001), [advisory request (`IF-ADV-001`)](../component-decomposition-and-interface-register.md#if-adv-001) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Unit, Component, Integration, Analysis, End-to-end
- Required evidence: log schema, secret/raw-data negative scan, timestamp/correlation fixtures and separate on-board/backend chronology
- State: D4-014 allocation and D4-024 shared evidence design reviewed; implementation and live qualification remain open

### Fixed-resource KUKSA authorization lifecycle

<a id="req-bhs-013"></a>

- ID: `REQ-BHS-013`
- Statement: The Service shall request the platform-owned `kuksa-auth-client`
  resource. Its compatibility bootstrap, and not the analytics application,
  shall read the current per-instance `AOS_SECRET`, call the mounted private
  Unix socket for the implicit fixed `kuksa` resource and atomically maintain
  only `/run/aosedge/secrets/kuksa/token.jwt` in the Service-private tmpfs. The
  bootstrap shall start analytics with only `KUKSA_TOKEN_FILE`, without
  `AOS_SECRET`; it shall not submit paths, operations, subject, audience, TTL or
  claims. It shall consume only the `r -> read` and `rw -> actuate` profile,
  renew a 300-second JWT at 180 seconds, atomically replace the token and
  reconnect/recreate every KUKSA subscription with the replacement. It shall
  fail closed on rejection, malformed response, expiry, permission removal,
  stop/unregistration, container replacement or VM restart. Terminal denial
  deletes and disconnects immediately; transient failure may use the current
  token only until expiry. Neither credential shall be persisted or logged.
- Rationale: The Service uses native Aos instance authority while the
  current-release translation remains outside VDP and outside the Service
  product.
- Parent system requirements: [Least-privilege KUKSA identities (`SYS-SEC-001`)](../system-requirements-and-traceability.md#sys-sec-001), [KUKSA verifier and token lifetime (`SYS-SEC-004`)](../system-requirements-and-traceability.md#sys-sec-004) and [current-release KUKSA authorization compatibility (`SYS-SEC-008`)](../system-requirements-and-traceability.md#sys-sec-008)
- Architecture flows: [Service v1 runtime (`AF-G2-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-rt), [authorization (`AF-X-AUTH`)](../../architecture/demo-scenario-architecture-flows.md#af-x-auth) and [QM containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Component: [Brake Health service (`CMP-BHS`)](../component-decomposition-and-interface-register.md#cmp-bhs)
- Interfaces: [fixed-resource bootstrap (`IF-AUTH-007`)](../component-decomposition-and-interface-register.md#if-auth-007) and [private JWT or rejection (`IF-AUTH-009`)](../component-decomposition-and-interface-register.md#if-auth-009)
- Verification levels: Unit, Component, Contract, Integration
- Required evidence: no-caller-selected-authority negative cases, bounded refresh/expiry trace, stop/unregister/reboot cleanup, cross-Service isolation and secret/JWT-negative artifacts/logs/state
- State: D4-027-compatible design accepted; implementation and qualification remain open

## Unit-Test Obligations

| Unit-test obligation | Requirements proved | Behavior and branches | Isolation / doubles | Required assertions | Repository / suite | State |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="ut-bhs-001"></a>`UT-BHS-001` — Artifact and metadata integrity | [`REQ-BHS-001`](#req-bhs-001) | Reproducible staging, metadata completeness, changed input, forbidden credentials/boundaries | Temporary filesystem and deterministic fixture manifest | Stable digests, correct ARM64 metadata, no secrets/CARLA/VISS/platform coupling | `brake-health-service` packaging tests | D3 design-reviewed |
| <a id="ut-bhs-002"></a>`UT-BHS-002` — Compatibility readiness | [`REQ-BHS-002`](#req-bhs-002), [`REQ-BHS-011`](#req-bhs-011) | Compatible, missing, lower/upper boundary, malformed contract, recovery | Fake installed-capability reader and readiness sink | Ready only for complete compatible contract; exact blocked reason; no report/advisory | `brake-health-service` unit suite | D3 design-reviewed |
| <a id="ut-bhs-013"></a>`UT-BHS-013` — Fixed-resource authorization lifecycle | [`REQ-BHS-013`](#req-bhs-013) | Named-resource bootstrap, private-socket request, reject caller-selected authority, atomic token replacement, 300-second expiry, renewal at 180 seconds, reconnect/subscription recreation, permission removal, stop/replace/unregister/reboot and malformed delivery | Fake KAC result, private tmpfs/token file, controllable clock and KUKSA transport | Analytics receives `KUKSA_TOKEN_FILE` but no `AOS_SECRET`; no caller-selected claims; exact renewal/reconnect; no access after rejection/removal/expiry; cross-Service denial and no secret/JWT persistence/logging | `brake-health-service` unit suite | D4 design accepted; implementation/qualification open |
| <a id="ut-bhs-004"></a>`UT-BHS-004` — Subscription and temporal validation | [`REQ-BHS-004`](#req-bhs-004), [`REQ-BHS-007`](#req-bhs-007) | Valid, boundary, wrong type/unit/range, stale, reordered, unavailable, reconnect | Fake KUKSA stream and clocks | Accepted sample sequence or explicit degraded reason; no fabricated value/advisory | `brake-health-service` unit suite | D3 design-reviewed |
| <a id="ut-bhs-005"></a>`UT-BHS-005` — v1 event-window state machine | [`REQ-BHS-005`](#req-bhs-005) | Six-path 30 Hz input; every-third-frame retention; trigger below/at/above 10 km/h, 50%, 200 ms; 500 ms clear; 3/10/2-second bounds; POST reactivation; cap/retrigger suppression; all terminal states; eight-window/4 MiB queue boundary; canonical 64 KiB chunk bound; atomic spool writes; restart/corruption/storage-full; duplicate/resume and invalid input | Fake KUKSA stream, clocks, bounded filesystem spool and fake backend | Exact 10 Hz samples/phases and one UUIDv4 event; no trigger from incomplete/stale input; contract-valid ordered idempotent chunks of at most 10 samples; exactly one completion; verified RFC-8785/SHA-256 digests; no send before durability or delete before durable ack; explicit stop/restart/quarantine/not-ready/overflow facts | `brake-health-service` unit/contract suite plus shared fixtures | D4-016.1/.2 and D4-017 accepted; implementation/qualification open |
| <a id="ut-bhs-006"></a>`UT-BHS-006` — Deterministic model and derived-data transition | [`REQ-BHS-006`](#req-bhs-006), [`REQ-BHS-007`](#req-bhs-007) | Complete 80-sample 10 Hz PRE/ACTIVE/POST golden input; every fixed-point below/half/above boundary; exact five reductions/clamps/load/state; all eight invalid reasons; UUID delimiter/forbidden bytes; lower-load assessment; band/no-band paths; pair count/byte overflow; every journal/state/bundle/marker interruption; duplicate/reorder and invalid model/config | Immutable synthetic-model input/invalid/quantization/output/state fixtures, deterministic clocks, injected deployment metadata and bounded temporary filesystem | Exact schema-valid bytes/digests/UUIDv5/timestamps/provenance; wear `54 -> 62`; invalid input has no state/message mutation; atomic pair or neither; exactly-once recovery/quarantine; no later overflow fabrication, second quantization, network/training side effect or normal v1 window output | `brake-health-service` model/contract suite plus shared D4-016.3 fixtures | D4 exact contract complete; implementation review open |
| <a id="ut-bhs-007"></a>`UT-BHS-007` — Advisory decision and payload | [`REQ-BHS-008`](#req-bhs-008) | Thresholds, hysteresis/debounce, stale/low-quality result, duplicate, prohibited targets/types | Fake KUKSA actuator client and clock | Only accepted typed target/payload, bounded correlation/freshness, no motion/text/arbitrary write | `brake-health-service` unit/contract suite | D3 design-reviewed |
| <a id="ut-bhs-008"></a>`UT-BHS-008` — Offline queue and synchronization | [`REQ-BHS-009`](#req-bhs-009) | Disconnect during v1 pre/active/post/chunk completion and v2/v3 messages, capacity boundary, overflow, retry/backoff, restart, duplicate acknowledgement, reconnect | In-memory/temp persistent stores, fake backend and clocks | Bounded bytes/items, explicit overflow, same v1 window/chunk resume identity, original times, idempotent replay, unchanged local assessment/advisory path | `brake-health-service` unit suite | D3 design-reviewed |
| <a id="ut-bhs-009"></a>`UT-BHS-009` — State and recovery compatibility | [`REQ-BHS-010`](#req-bhs-010) | v1/v2/v3 state, upgrade, incompatible state, removal/reassignment, interrupted migration | Versioned state fixtures and failure injection | Read/migrate/quarantine result, no silent loss, dependent-Service removal precondition | `brake-health-service` state suite | D4-015 design accepted |
| <a id="ut-bhs-010"></a>`UT-BHS-010` — Health, resources, logs and chronology | [`REQ-BHS-011`](#req-bhs-011), [`REQ-BHS-012`](#req-bhs-012) | Process versus capability state, operational/degraded/not-ready transitions, ring/window/queue owned limits, crash/restart, secret/raw-value log inputs and local/Cloud timestamps | Capability/log sinks, fake owned-bound signals and clocks; AosCore integration supplies quota evidence | Factual state, insufficient-input and single-command outcomes do not misstate readiness, bounded/aggregated output, no Service CPU/RAM-enforcement claim, redaction and separated source/result/advisory/synchronization chronology without adjacent-component side effects | `brake-health-service` unit/component suite | D3 design-reviewed |

Every obligation is blocking, deterministic and credential-free. Existing
scaffold tests are useful evidence for `UT-BHS-001`, but they do not satisfy
the product obligations until assertions and implementation cover the complete
accepted behavior.

<a id="ut-bhs-003"></a>`UT-BHS-003` is retired with `REQ-BHS-003` and is
replaced by [`UT-BHS-013`](#ut-bhs-013).

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| [`REQ-BHS-001`](#req-bhs-001) | [`UT-BHS-001`](#ut-bhs-001) | Built ARM64 process/package | Artifact/metadata schema | SOTA install/start/stop | N/A; packaging is supporting evidence |
| [`REQ-BHS-002`](#req-bhs-002) | [`UT-BHS-002`](#ut-bhs-002) | Readiness process state | VDP compatibility fixtures | Compatible/incompatible Unit graph | G2/G3 blocked/ready evidence |
| [`REQ-BHS-004`](#req-bhs-004) | [`UT-BHS-004`](#ut-bhs-004) | Packaged subscription client | KUKSA path/type/time fixtures | Real KUKSA disconnect/reconnect | G2/G3 input-quality evidence |
| [`REQ-BHS-005`](#req-bhs-005) | [`UT-BHS-005`](#ut-bhs-005) | Packaged ring-buffer/window process | Shared trigger/chunk/completion fixtures | Real backend live reconstruction and resume | `AF-G2-OB` growing/completed dashboard window |
| [`REQ-BHS-006`](#req-bhs-006) | [`UT-BHS-006`](#ut-bhs-006) | Packaged synthetic-model execution | Model/input/assessment/event fixture digest | Accepted VDP v2 signal stream and backend | `AF-G3-OB` derived-only repeated result |
| [`REQ-BHS-007`](#req-bhs-007) | [`UT-BHS-004`](#ut-bhs-004), [`UT-BHS-006`](#ut-bhs-006) | Degraded process state | Invalid/degraded fixture matrix | Source loss/reconnect | No false healthy/advisory evidence |
| [`REQ-BHS-008`](#req-bhs-008) | [`UT-BHS-007`](#ut-bhs-007) | Packaged advisory client | Typed target/payload/prohibition fixtures | Real KUKSA, VDP and Gateway | `AF-G4-OB` factual status |
| [`REQ-BHS-009`](#req-bhs-009) | [`UT-BHS-008`](#ut-bhs-008) | Restarted process with queue | Report/ack/idempotency schema | Backend/Cloud disconnect/reconnect | `AF-G4-OB` offline/local proof |
| [`REQ-BHS-010`](#req-bhs-010) | [`UT-BHS-009`](#ut-bhs-009) | State format process matrix | State/version compatibility manifest | Service removal, VDP repair and reassignment sequence | N/A; recovery supports accepted flow |
| [`REQ-BHS-011`](#req-bhs-011) | [`UT-BHS-002`](#ut-bhs-002), [`UT-BHS-010`](#ut-bhs-010) | Health/resource/fault suite | Readiness/status schema | Aos resource and adjacent continuity | G2-G4 actual-state evidence |
| [`REQ-BHS-012`](#req-bhs-012) | [`UT-BHS-010`](#ut-bhs-010) | Log/timestamp process output | Structured log/metric schema | Native log request and correlated faults | Technical chronology/evidence view |
| [`REQ-BHS-013`](#req-bhs-013) | [`UT-BHS-013`](#ut-bhs-013) | Service-private bootstrap/delivery boundary | `IF-AUTH-007`/`009` and JWT fixture schema | Real Aos IAM, `CMP-KAC` and KUKSA | G2/G4 permission, restart and removal evidence |

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Security and least privilege | [`REQ-BHS-013`](#req-bhs-013), [`REQ-BHS-008`](#req-bhs-008) | Native per-instance identity, fixed-resource bootstrap, private short-lived token and typed advisory only | Unit negatives, contract fixtures and real IAM/KAC/KUKSA integration |
| QM containment | [`REQ-BHS-008`](#req-bhs-008) | Maintenance request only; no safety goal, HMI, motion or arbitrary write authority | Prohibited-permission/source scan and end-to-end Gateway status |
| Privacy and redaction | [`REQ-BHS-005`](#req-bhs-005), [`REQ-BHS-006`](#req-bhs-006), [`REQ-BHS-012`](#req-bhs-012) | Bounded event-only v1 capture, derived-only normal v2/v3 output and structured redacted evidence rather than continuous raw streaming | Window/message schema size, no-trigger/no-v1-output cases, content allowlist and secret/raw-log negative scan |
| Resource bounds | [`REQ-BHS-009`](#req-bhs-009), [`REQ-BHS-011`](#req-bhs-011) | Fixed queue/quotas and explicit overflow/resource state | Boundary/fault injection plus Aos enforcement |
| Chronology | [`REQ-BHS-006`](#req-bhs-006), [`REQ-BHS-012`](#req-bhs-012) | Deterministic model plus distinct source, local result/advisory and synchronization timestamps; no first-demo performance KPI | Controlled clocks and correlated integration runs |
| Offline and recovery | [`REQ-BHS-009`](#req-bhs-009), [`REQ-BHS-010`](#req-bhs-010) | Local decision continuity, bounded replay and versioned recovery-safe state | Disconnect/restart/reconnect and state matrix |
| Observability | [`REQ-BHS-011`](#req-bhs-011), [`REQ-BHS-012`](#req-bhs-012) | Separate process health/readiness and bounded native log evidence | Component state matrix and native log integration |

## Acceptance Record and Version 0.8 Reconciliation

The previously accepted package established that:

1. the in-vehicle service, backend/dashboard and Vehicle Data Platform remain separate products and repositories;
2. v1-v3 are one independent SOTA product family with explicit compatibility, not three architecture components;
3. v1 is a bounded pre/active/post braking-event recorder, v2 moves a clearly labelled synthetic assessment on-board and normally emits derived data only, and v3 adds the typed advisory while retaining the v2 backend result;
4. local assessment and advisory do not depend on Cloud connectivity;
5. Aos IAM is authoritative, `CMP-KAC` only translates its current result, and no duplicate policy database or caller-selected JWT authority is introduced;
6. the advisory is a typed QM maintenance request with no driver-HMI, safety or motion claim;
7. every owned behavior has a stable deterministic unit-test obligation;
8. current scaffold evidence is not presented as implemented product behavior;
9. the open interface/model/resource decisions below are resolved in D4 before implementation claims acceptance.

Version 0.5 introduced the reviewed security delta. It retires
`REQ-BHS-003`/`UT-BHS-003`, adds
`REQ-BHS-013`/`UT-BHS-013`, and replaces caller-selected broker requests with
fixed-resource `CMP-KAC` bootstrap and private volatile JWT delivery. All
functional v1-v3 semantics remain unchanged. Version 0.8 reconciled the
package with accepted D4-016, D4-017 and D4-027 decisions. Version 0.9 records
the accepted D4-016.3 byte/arithmetic/fixture closure and its exact
implementation-test obligations. This acceptance authorizes no service implementation,
signing, upload, deployment, OEM approval, Cloud mutation or VM changes;
implementation still requires an exact work packet.

## Open Issues

The D4-016.3/.4/.5 and D4-017 machine-readable packages linked above replace
the former undefined-design gaps and are accepted. Live D4-003 calibration,
CARLA separation,
Aos quota, KUKSA/Gateway and backend-route qualification remain genuine
implementation gates after design acceptance.

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| D4-016.1/.2 v1 acquisition, logical-message and local-spool implementation/qualification | Design is accepted; executable behavior and shared-fixture conformance remain to be built | Function Team 1 + Platform Team | D4 implementation and qualification |
| Implement accepted D4-017 local backend transport, ordered reconstruction/resume and acknowledgement | Executable conformance and live route qualification block `REQ-BHS-005`/`009` implementation acceptance; production backend authentication is Function Team 1-owned and out of scope | Function Team 1 Cloud | D4-017 implementation plus D4-020 qualification |
| Exact Aos metadata representation of KUKSA paths/modes; current SDK read-mode enum/default inconsistency | Blocks least-privilege packaging proof | AosEdge Platform Team + Platform Team | D4 SDK/metadata qualification |
| Implement and qualify the complete accepted D4-027 named-resource/private-socket/tmpfs, strict-wire, JWT mapping, 300/180-second timing, per-Unit signer/verifier, trustworthy-time, retry and resource/failure boundary | Blocks `REQ-BHS-013` acceptance, but no D4-027 design question remains | Platform Team + Function Team 1 | D4-027 implementation and qualification |
| Native Service-to-FOTA dependency admission unavailable in current release | Pre-transfer rejection remains deferred; service readiness still required | AosEdge Platform Team | Official release qualification |
| Implement and qualify the accepted D4-016.3 exact model contract | Design is accepted; D4-003 calibration/conformance and executable tests still block `REQ-BHS-006`/`007` implementation acceptance | Function Team 1 + Platform Team | [`D4-016`](../d4-decision-register.md#d4-016), coordinated with D4-003 calibration |
| Implement and qualify the accepted D4-016.4 model-to-advisory activation, lease, refresh and Gateway-status contract | Design is accepted; real upgrade/restart/KUKSA/VDP/VISS/Gateway conformance still blocks complete `REQ-BHS-008` acceptance | Function Team 1 + Platform + Gateway | [`D4-016`](../d4-decision-register.md#d4-016) |
| Implement matching factual Gateway Status consumption and correlated backend advisory fact | D4-016.4 design is accepted; Engineering Telematics Dashboard remains the audience-visible Gateway authority | Function Team 1 + Gateway | D4-016.4 implementation and real Gateway conformance |
| Per-version v2/v3 queue/state, D4-017 backend acknowledgement and transport retry/backoff | D4-016.3/.5 and D4-017 behavior is accepted; live restart/backend conformance still blocks `REQ-BHS-009`/`010` | Function Team 1 | Implementation and qualification |
| Qualify accepted readiness schema and measured CPU/RAM/storage/state budgets | D4-016.5 design is accepted; live D4-023 evidence still blocks `REQ-BHS-011` implementation acceptance | Function Team 1 + Aos integration | D4-023 resource qualification |
| Implement and qualify accepted structured log schema, redaction and chronology fields | D4-016.5 design is accepted; executable/native-log proof still blocks `REQ-BHS-012` implementation acceptance | Function Team 1 + Demo experience | D4 implementation and observability qualification |
| Packaging guide still describes caller-selected paths and a separate FOTA-managed OEM policy | Conflicts with ADR 0013 and could mislead implementation | Function Team 1 | Correct before D4 implementation starts |

## Change Rules

- Editorial clarification preserves stable `REQ-BHS-*` and `UT-BHS-*` IDs.
- A material semantic replacement receives a new ID and retains the old
  definition in a clearly labelled retired section with a replacement link.
- A changed data direction, service/backend boundary, lifecycle authority,
  credential authority, QM boundary or advisory authority follows the Level-C
  architecture cascade before this package changes.
- A model, queue, schema, threshold, resource or timing change inside accepted
  boundaries follows the Level-B cascade and updates requirements, fixtures,
  tests and evidence together.
- Implementation function/test names may change, but accepted obligation IDs
  and their mappings remain stable until deliberately retired.
