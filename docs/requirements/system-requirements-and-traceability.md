<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# System Requirements and Traceability 0.1

- Status: Review candidate
- Version: 0.1
- Prepared: 2026-08-18
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.1](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake Health Demo Scenarios 1.1](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 1.0](../architecture/demo-scenario-architecture-flows.md)
- Implementation, repository creation, signing, Cloud, or Unit mutation authorized: no

## Purpose

This document converts the accepted architecture-flow model and its twenty
open gaps into reviewable system requirements and an allocation plan for
component requirements.

It deliberately separates four different things:

1. an unresolved architecture or qualification gap;
2. a system-level obligation visible across component boundaries;
3. a component or interface requirement allocated to one owner;
4. a verification method and retained evidence proving the obligation.

A gap is not closed merely because code exists. It closes only after the
governing decision is accepted, requirements are allocated, the implementation
passes its acceptance criteria, and the evidence is retained.

## Source Precedence

1. High-Level Architecture 1.1 owns boundaries, authority and invariants.
2. Demo Scenario 1.1 owns the audience-visible stage progression.
3. Architecture Flows 1.0 owns detailed lifecycle, runtime, observability and
   failure-flow mapping.
4. This document owns system requirement identifiers, gap traceability,
   verification intent and the next component-allocation boundary.

An inconsistency must be resolved in its owning source. It must not be hidden
by weakening a requirement here.

## Requirement and Verification Conventions

Normative requirements use **shall**. Their identifiers remain stable after
acceptance even if wording is clarified.

| Prefix | Requirement area |
| --- | --- |
| `SYS-MFG` | Factory image and manufacturing output |
| `SYS-ID` | Provisioning, identity and Cloud registration |
| `SYS-SRC` | CARLA source and Unit binding |
| `SYS-REL` | FOTA/SOTA targeting, dependency, validation and rollback |
| `SYS-VDP` | Vehicle Data Platform Capability |
| `SYS-BHS` | Brake Health functional behavior |
| `SYS-EVT` | Vehicle Stability / Low-Friction event behavior |
| `SYS-SEC` | Security and authorization |
| `SYS-OBS` | Dashboards, logs, correlation and evidence |
| `SYS-TIM` | Timing and resource bounds |
| `SYS-RET` | End-of-run retirement and next-run reset |

| Method | Meaning |
| --- | --- |
| `T` | Automated or controlled test |
| `I` | Inspection of immutable artifact, configuration or authoritative state |
| `A` | Analysis of measurements, logs or failure evidence |
| `D` | Audience-visible demonstration |

## Repository and Ownership Decision

The two OEM functional teams are peer AosCloud Service Providers and require
separate source and SOTA lifecycles.

| Repository | Ownership boundary | Lifecycle | State |
| --- | --- | --- | --- |
| `CarlaSim` | Virtual physical vehicle and upstream simulator behavior | Simulator source | Existing |
| `carla-ego-runtime` | Vehicle Gateway, control, VSS projection, VISS and Engineering Telematics Dashboard | Gateway tooling | Existing |
| `aos-vehicle-platform` | Shared Vehicle Data Platform Capability, KUKSA integration, provider runtime and authorization adapter | Platform FOTA | Existing |
| `brake-health-service` | Function Team 1 on-board Brake Health application and local inference | Service Provider 1 / SOTA 1 | Existing |
| `vehicle-stability-event-service` | Function Team 2 on-board low-friction event detection, bounded queue and upload client | Service Provider 2 / SOTA 2 | **Proposed repository** |
| `aosedge-sdv-demo` | Cross-repository orchestration, dashboards, system requirements and end-to-end qualification | Demo solution | Existing |

The proposed Function Team 2 repository shall not own CARLA integration,
VISS transport, platform signal publication, KUKSA authorization, VM
provisioning, or AosCloud desired state. It consumes only an accepted,
versioned KUKSA contract.

The Function Team 1 and Function Team 2 backends and dashboards are distinct
functional products. Their final repository layout remains a later decision;
they must not be silently placed inside either in-vehicle service repository.

The proposed repository is not added to `workspace/repositories.json` until it
exists and its initial accepted revision is available. This preserves the
current workspace doctor's validity.

## System Requirements

### Manufacturing and identity

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-mfg-001"></a>`SYS-MFG-001` | Reproducible factory image | The Platform Team shall produce a reproducible, immutable and digest-addressed OEM Demo Factory Image from an identified AosEdge release and accepted integration inputs. | `I,T` | `GAP-AF-01` |
| <a id="sys-mfg-002"></a>`SYS-MFG-002` | Clean SOP substrate | The factory image shall contain AosCore, KUKSA, security/update support and the provider-specific empty-slot runtime, but no provider payload, functional service, Cloud registration, Cloud credential or reusable per-vehicle secret. | `I,T` | `GAP-AF-01` |
| <a id="sys-mfg-003"></a>`SYS-MFG-003` | Unique fresh overlays | Two fresh copy-on-write overlays created from the factory image shall generate distinguishable local identity material before provisioning and shall never share provisioned identity material. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-001"></a>`SYS-ID-001` | One identity per overlay | The provisioning flow shall create exactly one unique Unit and Main Node identity for each fresh overlay and bind them to the Validation and Demonstration roles for one demo run. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-002"></a>`SYS-ID-002` | Reconcile partial provisioning | A timeout or partial provisioning result shall enter reconciliation and shall not be blindly retried or treated as a clean unprovisioned overlay. | `T,A` | `GAP-AF-03` |
| <a id="sys-id-003"></a>`SYS-ID-003` | Prove current Unit state | Before any update, the system shall prove the current Unit ID, Node ID, role, Unit Set membership, online state and current software graph of both Units. | `T,I` | `GAP-AF-03`, `GAP-AF-06` |
| <a id="sys-id-004"></a>`SYS-ID-004` | Qualify identity retirement | Retirement qualification shall prove deprovisioning, old-certificate rejection, Unit deletion, qualified Node handling, audit retention and recoverable partial-failure behavior. | `T,A` | `GAP-AF-03` |

### Vehicle source and release lifecycle

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-src-001"></a>`SYS-SRC-001` | Exact source-to-Unit binding | Each qualification or demonstration observation shall identify the exact CARLA/VISS source, target Unit and frame/trace range, using either exclusive live binding or deterministic versioned replay. | `T,I,D` | `GAP-AF-04` |
| <a id="sys-src-002"></a>`SYS-SRC-002` | Honest single-source presentation | The demo shall not imply that two simulated vehicles were running simultaneously when one CARLA/Gateway source was reused sequentially. | `I,D` | `GAP-AF-04` |
| <a id="sys-rel-001"></a>`SYS-REL-001` | Immutable release candidates | Every FOTA and SOTA candidate shall be immutable and identified by version and digest before presentation-time deployment. | `I` | `GAP-AF-05`, `GAP-AF-07`, `GAP-AF-20` |
| <a id="sys-rel-002"></a>`SYS-REL-002` | Current effective-target validation | Immediately before approval, the delivery workflow shall derive effective targets from current Unit pending-batch state and shall block stale, missing or unexpected targets. | `T,I` | `GAP-AF-06` |
| <a id="sys-rel-003"></a>`SYS-REL-003` | Service capability compatibility | Each SOTA service artifact shall carry a versioned Vehicle Data Platform Capability compatibility range and shall fail closed at startup/readiness when the installed capability is absent or incompatible. | `T,I` | `GAP-AF-20` |
| <a id="sys-rel-004"></a>`SYS-REL-004` | Validate before promotion | A candidate shall be installed and qualified on the Validation Unit before the identical accepted bytes and digest are promoted to the Demonstration Unit. | `T,I,D` | `GAP-AF-06`, `GAP-AF-20` |
| <a id="sys-rel-005"></a>`SYS-REL-005` | Dependent-first rollback | Rollback shall remove or roll back a dependent SOTA service before a platform capability on which it depends, while preserving unaffected service and platform lifecycles. | `T,A` | `GAP-AF-05`, `GAP-AF-20` |
| <a id="sys-rel-006"></a>`SYS-REL-006` | Native Cloud dependency rejection | AosCloud shall natively reject a SOTA request whose declared Vehicle Data Platform Capability range is not satisfied on the intended Unit before changing Subject-service desired state, creating a validation batch or campaign, or transferring update content to the Unit, and shall return an authoritative machine-readable reason. | `T,I,D` | `GAP-AF-20` |

[Native Cloud dependency rejection (`SYS-REL-006`)](#sys-rel-006) is
**deferred and blocked on an implementing AosEdge platform
release**. The Platform Team reported the capability as roadmap work on
2026-08-18, without an available release or date. No project-side admission
controller is an acceptable substitute. `SYS-REL-003` remains required as
defense in depth before and after the native Cloud feature becomes available.

### Vehicle Data Platform Capability

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-vdp-001"></a>`SYS-VDP-001` | Healthy empty capability slot | The provider-specific runtime shall report a healthy empty slot at G0 and shall support the independently versioned Vehicle Data Platform Capability without claiming arbitrary component-type support. | `T,I` | `GAP-AF-01`, `GAP-AF-05` |
| <a id="sys-vdp-002"></a>`SYS-VDP-002` | Versioned v1 signal contract | Capability v1 shall expose only its accepted read-only signal subset with defined type, unit, range, cadence, freshness, unavailable-state and provenance behavior. | `T,I` | `GAP-AF-05` |
| <a id="sys-vdp-003"></a>`SYS-VDP-003` | Backward-compatible v2 capability | Capability v2 shall be a backward-compatible superset of v1 and shall preserve existing v1 consumers while adding the accepted Brake Health inputs. | `T` | `GAP-AF-08` |
| <a id="sys-vdp-004"></a>`SYS-VDP-004` | Allowlisted outbound advisory | Capability v3 shall provide a narrowly scoped outbound advisory path with an allowlisted KUKSA actuator, validation policy, VISS Set operation and factual Gateway status. | `T,I,D` | `GAP-AF-10` |
| <a id="sys-vdp-005"></a>`SYS-VDP-005` | Explicit degraded data | Missing, stale, malformed or disconnected source data shall become explicit unavailable/degraded state and shall never be replaced with fabricated normal values. | `T` | `GAP-AF-05`, `GAP-AF-08` |

### Brake Health function

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-bhs-001"></a>`SYS-BHS-001` | Bounded v1 functional report | Service v1 shall consume only the accepted KUKSA contract and send a bounded, versioned and idempotent functional report to the Brake Health backend. | `T,I` | `GAP-AF-07` |
| <a id="sys-bhs-002"></a>`SYS-BHS-002` | Deterministic v2 inference | Service v2 shall use an immutable prepared model, distinguish native, derived, estimated and simulated inputs, and produce deterministic results for the accepted scenario and input version. | `T,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-003"></a>`SYS-BHS-003` | Allowlisted v3 advisory | Service v3 shall request only the accepted Brake Health advisory target and shall not gain arbitrary display-text or vehicle-motion authority. | `T,I` | `GAP-AF-10`, `GAP-AF-15` |
| <a id="sys-bhs-004"></a>`SYS-BHS-004` | Offline local continuity | Brake Health local inference and advisory shall continue without Cloud connectivity; functional reports shall use bounded retention, retry and idempotent synchronization with original event time. | `T,A,D` | `GAP-AF-11` |

### Function Team 2 event function

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-evt-001"></a>`SYS-EVT-001` | Existing platform contract only | The Vehicle Stability service shall consume only dynamics signals already present in an accepted Vehicle Data Platform Capability and shall not require a new platform feature in the current demo. | `I,T` | `GAP-AF-13` |
| <a id="sys-evt-002"></a>`SYS-EVT-002` | Local low-friction detection | The service shall detect a Vehicle Stability / Low-Friction Event locally using a versioned input subset, state machine, thresholds and bounded pre/post-event window qualified against repeatable CARLA runs. | `T,A,D` | `GAP-AF-12` |
| <a id="sys-evt-003"></a>`SYS-EVT-003` | Bounded event upload | The service shall upload a bounded event package rather than an unrestricted continuous raw-telemetry stream and shall retain it within explicit offline, rate and storage limits. | `T,I,A` | `GAP-AF-12`, `GAP-AF-14` |
| <a id="sys-evt-004"></a>`SYS-EVT-004` | Independent event backend | Function Team 2's backend shall ingest event packages idempotently and its dashboard shall expose event time, status, service version, Unit role and online/offline delivery state. | `T,D` | `GAP-AF-14` |
| <a id="sys-evt-005"></a>`SYS-EVT-005` | Ground-truth isolation | CARLA ground truth may qualify the detector but shall not be exposed to the service or backend as if it were a production vehicle signal. | `I,T` | `GAP-AF-12`, `GAP-AF-13` |

### Security, observability and timing

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-sec-001"></a>`SYS-SEC-001` | Least-privilege KUKSA identities | KUKSA publishers, readers and actuators shall use distinct least-privilege identities and path-level permissions appropriate to their lifecycle owners. | `I,T` | `GAP-AF-15` |
| <a id="sys-sec-002"></a>`SYS-SEC-002` | Authorization-adapter migration | The accepted design shall define migration from prototype tokens to the platform authorization adapter without embedding credentials in artifacts, source, command lines or logs. | `I,T` | `GAP-AF-15` |
| <a id="sys-sec-003"></a>`SYS-SEC-003` | Fail-closed advisory security | Unauthorized, malformed, stale or replayed advisory requests shall fail closed and produce factual non-driver status evidence. | `T,A` | `GAP-AF-10`, `GAP-AF-15` |
| <a id="sys-obs-001"></a>`SYS-OBS-001` | Authoritative demo surfaces | Every audience claim shall identify its authoritative surface: CARLA for physical stimulus, Engineering Telematics Dashboard for Gateway state, AosCloud for software lifecycle, ELK for operational logs, and each functional dashboard for its own backend data. | `I,D` | `GAP-AF-17` |
| <a id="sys-obs-002"></a>`SYS-OBS-002` | Cloud-authoritative delivery dashboard | The Software Delivery Dashboard shall read and re-read authoritative AosCloud state and shall not maintain an independent desired-state database. | `T,I` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-obs-003"></a>`SYS-OBS-003` | Operational log controls | Operational log delivery shall define access control, redaction, retention, offline buffering and failure visibility before ELK is presented as demo evidence. | `T,I,A` | `GAP-AF-16` |
| <a id="sys-obs-004"></a>`SYS-OBS-004` | Per-run correlation | Before provisioning, a demo run shall be correlated by start time and local overlay roles; after provisioning it shall be correlated by the two Unit IDs and the same bounded time window. | `T,I` | `GAP-AF-19` |
| <a id="sys-tim-001"></a>`SYS-TIM-001` | Lifecycle timing bounds | Each lifecycle stage shall have measured normal duration, timeout, stalled-state and recovery criteria for both technical and executive presentation modes. | `T,A,D` | `GAP-AF-18` |
| <a id="sys-tim-002"></a>`SYS-TIM-002` | Separate local and Cloud latency | Local Brake Health decision and Gateway advisory latency shall be measured separately from Cloud report synchronization latency. | `T,A,D` | `GAP-AF-18` |

### Retirement and next-run reset

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ret-001"></a>`SYS-RET-001` | Retire Units and overlays | R0 shall stop both Units, perform qualified Cloud deprovisioning and deletion, prove retired credentials cannot reconnect, and discard only the corresponding provisioned overlays after reconciliation succeeds. | `T,I,A` | `GAP-AF-03`, `GAP-AF-19` |
| <a id="sys-ret-002"></a>`SYS-RET-002` | Clear functional run data | Functional backends and dashboards shall clear or archive run-scoped data using exact Unit IDs and the bounded session time window without deleting authoritative Cloud audit history. | `T,I` | `GAP-AF-19` |
| <a id="sys-ret-003"></a>`SYS-RET-003` | Reset CARLA and preserve factory | R0 shall reset CARLA actors and local run evidence and shall prove that the immutable factory image and digest remain unchanged for the next M0. | `T,I` | `GAP-AF-01`, `GAP-AF-04` |
| <a id="sys-ret-004"></a>`SYS-RET-004` | No rollback or fleet claim | The normal demo reset shall not be presented as a G4-to-G0 OTA rollback or as a production-fleet vehicle deletion policy. | `I,D` | `GAP-AF-03`, `GAP-AF-18` |

## Gap Coverage Matrix

| Gap | Governing system requirements |
| --- | --- |
| `GAP-AF-01` | `SYS-MFG-001`, `SYS-MFG-002`, `SYS-VDP-001`, `SYS-RET-003` |
| `GAP-AF-02` | `SYS-MFG-003`, `SYS-ID-001` |
| `GAP-AF-03` | `SYS-ID-002`, `SYS-ID-003`, `SYS-ID-004`, `SYS-RET-001`, `SYS-RET-004` |
| `GAP-AF-04` | `SYS-SRC-001`, `SYS-SRC-002`, `SYS-RET-003` |
| `GAP-AF-05` | `SYS-REL-001`, `SYS-REL-005`, `SYS-VDP-001`, `SYS-VDP-002`, `SYS-VDP-005` |
| `GAP-AF-06` | `SYS-ID-003`, `SYS-REL-002`, `SYS-REL-004`, `SYS-OBS-002` |
| `GAP-AF-07` | `SYS-REL-001`, `SYS-BHS-001` |
| `GAP-AF-08` | `SYS-VDP-003`, `SYS-VDP-005`, `SYS-BHS-002` |
| `GAP-AF-09` | `SYS-BHS-002` |
| `GAP-AF-10` | `SYS-VDP-004`, `SYS-BHS-003`, `SYS-SEC-003` |
| `GAP-AF-11` | `SYS-BHS-004` |
| `GAP-AF-12` | `SYS-EVT-002`, `SYS-EVT-003`, `SYS-EVT-005` |
| `GAP-AF-13` | `SYS-EVT-001`, `SYS-EVT-005` |
| `GAP-AF-14` | `SYS-EVT-003`, `SYS-EVT-004` |
| `GAP-AF-15` | `SYS-BHS-003`, `SYS-SEC-001`, `SYS-SEC-002`, `SYS-SEC-003` |
| `GAP-AF-16` | `SYS-OBS-003` |
| `GAP-AF-17` | `SYS-OBS-001`, `SYS-OBS-002` |
| `GAP-AF-18` | `SYS-TIM-001`, `SYS-TIM-002`, `SYS-RET-004` |
| `GAP-AF-19` | `SYS-OBS-004`, `SYS-RET-001`, `SYS-RET-002` |
| `GAP-AF-20` | `SYS-REL-001`, `SYS-REL-003`, `SYS-REL-004`, `SYS-REL-005`, deferred `SYS-REL-006` |

All twenty architecture-flow gaps have explicit requirement coverage. This
does not mean they are resolved; each remains open until its linked
requirements have accepted evidence.

## Component Requirement Package Allocation

The canonical component IDs, interface IDs, repository candidates and package
boundaries are defined in the
[Component Decomposition and Interface Register 0.1](component-decomposition-and-interface-register.md).
The next derivation step shall expand the following packages. A system
requirement may allocate obligations to several packages and one integration
test.

| Package | Primary repository or owner | Main allocation |
| --- | --- | --- |
| [Vehicle simulation (`CR-VEHICLE-SIM`)](component-decomposition-and-interface-register.md#cr-vehicle-sim) | `CarlaSim` plus scenario tooling in `carla-ego-runtime` | Deterministic braking and low-friction stimuli, reset, timestamps and ground-truth qualification |
| [Vehicle Gateway (`CR-GATEWAY`)](component-decomposition-and-interface-register.md#cr-gateway) | `carla-ego-runtime` | Vehicle sampling, VSS/VISS contracts, source status, advisory handler and Engineering Telematics Dashboard |
| [Factory substrate (`CR-FACTORY`)](component-decomposition-and-interface-register.md#cr-factory) | Platform Team / `aos-vehicle-platform` | Factory image, provider-specific empty-slot runtime, identity absence and overlay creation |
| [Vehicle Data Platform (`CR-VDP`)](component-decomposition-and-interface-register.md#cr-vdp) | `aos-vehicle-platform` | Provider v1-v3, KUKSA contract, outbound policy and authorization integration |
| [Brake Health service (`CR-BHS`)](component-decomposition-and-interface-register.md#cr-bhs) | `brake-health-service` | Service v1-v3 behavior, model, report queue, advisory request and resource limits |
| [Vehicle Stability service (`CR-EVT`)](component-decomposition-and-interface-register.md#cr-evt) | proposed `vehicle-stability-event-service` | Local detector, event window/package, offline queue, SOTA 2 metadata and resource limits |
| [Aos lifecycle (`CR-AOS`)](component-decomposition-and-interface-register.md#cr-aos) | AosCore/AosCloud integration | Provisioning, desired/actual state, FOTA/SOTA lifecycle, targeting, native cross-lifecycle dependency admission and log transport |
| [Brake Health Cloud (`CR-BRAKE-CLOUD`)](component-decomposition-and-interface-register.md#cr-brake-cloud) | Function Team 1 | Brake Health backend ingestion, idempotency, retention and function dashboard |
| [Vehicle Stability Cloud (`CR-EVENT-CLOUD`)](component-decomposition-and-interface-register.md#cr-event-cloud) | Function Team 2 | Low-friction event ingestion, idempotency, retention and event dashboard |
| [Demo orchestration (`CR-DEMO`)](component-decomposition-and-interface-register.md#cr-demo) | `aosedge-sdv-demo` | Overlay lifecycle, Unit binding, release orchestration, Software Delivery Dashboard, evidence and retirement |
| [Cross-cutting concerns (`CR-CROSS`)](component-decomposition-and-interface-register.md#cr-cross) | Security and operational concerns across owners | Identities, permissions, credentials, authorization adapter, redaction, timing and offline bounds |
| [End-to-end acceptance (`CR-E2E`)](component-decomposition-and-interface-register.md#cr-e2e) | Cross-repository qualification | Stage acceptance, failure/offline/recovery, latency and traceability evidence |

Component requirements shall reference both their parent `SYS-*` requirement
and the relevant `AF-*` flow. Tests shall reference the component requirement,
system requirement and retained evidence identifier.

## Proposed Function Team 2 Repository Creation Gate

Before creating `vehicle-stability-event-service`, reviewers shall confirm:

1. the repository name and functional ownership boundary;
2. public visibility and Apache-2.0 licensing with copyright `maninblack`;
3. a `main`-only workflow for the current single-developer phase;
4. an ARM64 Aos service scaffold equivalent in quality to
   `brake-health-service`, but with a distinct service identity and SOTA 2
   provider metadata;
5. no CARLA, VISS, VM, platform-provider or Cloud credential dependency;
6. a versioned compatibility declaration for the accepted KUKSA contract;
7. explicit CPU, memory, state, temporary storage, file, process, event-rate
   and offline-queue limits;
8. addition to `workspace/repositories.json` only after the initial repository
   revision exists and passes its repository gates.

No remote repository creation is authorized by this review candidate.

## Acceptance Gate for Version 0.1

This document is ready to become the requirements baseline only when reviewers
confirm that:

1. every Architecture Flows 1.0 gap is covered without claiming it is already
   implemented;
2. requirements are externally observable and testable;
3. the two Service Providers remain independent peers;
4. `vehicle-stability-event-service` is the accepted repository name and owns
   only the in-vehicle SOTA 2 service;
5. backend and dashboard repository ownership is intentionally left for a
   separate decision;
6. no requirement expands vehicle-control, driver-HMI or production-fleet
   scope;
7. component requirement packages can be derived without changing HLA 1.1 or
   Demo Scenario 1.1.
8. deferred [native Cloud dependency rejection (`SYS-REL-006`)](#sys-rel-006)
   is not treated as implemented or replaced by custom
   dashboard policy before an implementing AosEdge release is qualified.

After acceptance of this document and the Component Decomposition and
Interface Register, the next document set is the component requirement package
listed above. Implementation planning follows only after those packages and
their acceptance tests are reviewed.
