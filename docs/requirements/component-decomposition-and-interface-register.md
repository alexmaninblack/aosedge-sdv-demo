<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Decomposition and Interface Register 0.1

- Status: Review candidate
- Version: 0.1
- Prepared: 2026-08-18
- Architecture input: [High-Level Architecture 1.1](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake Health Demo Scenarios 1.1](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 1.0](../architecture/demo-scenario-architecture-flows.md)
- Requirements input: [System Requirements and Traceability 0.1](system-requirements-and-traceability.md)
- Implementation, repository creation, Cloud, or Unit mutation authorized: no

## Purpose

This document establishes the component boundaries that must be accepted before
component requirements or implementation plans are written. It answers four
questions for every logical component:

1. what responsibility the component owns;
2. which organization and lifecycle own it;
3. whether it exists, must be extended, is new, is externally supplied, or is
   deliberately deferred;
4. which versioned interfaces connect it to the rest of the demonstration.

The register deliberately separates architecture components from Git
repositories, deployable artifacts, runtime instances, and audience-visible
surfaces. Those concepts are related, but they are not interchangeable.

## Source Precedence

1. High-Level Architecture 1.1 owns system boundaries, authorities and
   invariants.
2. Demo Scenario 1.1 owns the audience-visible lifecycle and stage sequence.
3. Architecture Flows 1.0 owns detailed runtime, lifecycle, observability and
   failure flows.
4. System Requirements 0.1 owns normative `SYS-*` obligations and gap
   traceability.
5. This register owns stable component and interface identifiers, component
   allocation, implementation state and repository placement candidates.

An inconsistency must be corrected in its owning source. It must not be hidden
by redefining a component or interface here.

## Decomposition Rules

### Component is not repository

A component is a cohesive logical responsibility with an owner and an
interface boundary. A repository is a source-governance boundary. One
repository may own several closely related components, while externally
supplied components may have no project-owned repository at all.

### Component is not runtime instance

The Validation Unit and Demonstration Unit are two instances of the same
Domain Controller component graph. They are roles in the demo lifecycle, not
different software components. Likewise, a fresh overlay is an instance of an
accepted factory image, not a new component.

### Component is not deployment artifact

The Vehicle Data Platform Capability is one platform component delivered in
independently versioned FOTA artifacts. Brake Health and Vehicle Stability are
two peer functional components delivered in separate SOTA lifecycles. Version
changes do not create new logical components.

### Dashboard is not authority

Every dashboard is a presentation surface over one authoritative source:

| Dashboard | Authoritative source |
| --- | --- |
| Engineering Telematics Dashboard | Vehicle Gateway VISS endpoint |
| OEM Software Delivery Dashboard | AosCloud API and current Unit state |
| Brake Health Function Dashboard | Function Team 1 backend |
| Event-Based Data Dashboard | Function Team 2 backend |
| Vehicle and Service Log View | Accepted centralized log store |

No dashboard becomes an alternate desired-state database, vehicle-data broker,
functional backend, or vehicle-control path.

## State Vocabulary

| State | Meaning |
| --- | --- |
| `CURRENT` | Accepted behavior exists and is used by the current baseline. |
| `EXTEND` | A component exists, but one or more target responsibilities are not implemented or accepted. |
| `EVIDENCE` | Engineering implementation or qualification evidence exists, but it is not yet the accepted clean demo baseline. |
| `NEW` | No accepted implementation exists; component design and implementation are required. |
| `EXTERNAL` | Supplied or operated outside the custom project repositories; integration still requires qualification. |
| `DEFERRED` | Architecturally recorded, but deliberately excluded from the current implementation scope. |

A component may carry two states where origin and maturity differ, for example
`EXTERNAL / EXTEND` for an externally supplied mechanism whose exact demo
integration has not been qualified.

## Component Catalogue

### Virtual vehicle and Vehicle Gateway domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| `CMP-CARLA` | CARLA Virtual Physical Vehicle | Vehicle dynamics, road environment, native sensor state and actuators | Vehicle simulation | `CarlaSim`; restricted Unreal dependency remains separate | `CURRENT` |
| `CMP-SCENE` | Deterministic Scenario Controller | Repeatable obstacle/braking stimulus, manual takeover, safe stop, actor cleanup, and future low-friction stimulus | Demo vehicle tooling | `carla-ego-runtime` | Brake scenario `CURRENT`; low-friction `EXTEND` |
| `CMP-CONTROL` | Vehicle Control UI | Manual/autopilot selection, throttle, brake, steering and safe-stop commands over the separate control channel | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT` |
| `CMP-GW` | Vehicle Gateway Runtime | CARLA sampling, control arbitration, signal normalization and Gateway health/state | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / EXTEND` |
| `CMP-VISS` | Vehicle Gateway VISS 3.1 Server | TLS-protected VSS Get/Subscribe and the future narrowly scoped advisory Set contract | Vehicle Gateway tooling | `carla-ego-runtime` | Read path `CURRENT`; write path `EXTEND` |
| `CMP-GW-ADV` | Gateway Advisory Handler | Validate the accepted Brake Health advisory target and publish factual reception/status without claiming driver display | Vehicle Gateway tooling | `carla-ego-runtime` | `NEW` |
| `CMP-ENG-DASH` | Engineering Telematics Dashboard | Independent read-only engineering view of Gateway telemetry and future advisory/status evidence | Demo engineering tooling | `carla-ego-runtime` | Telemetry `CURRENT`; advisory/status `EXTEND` |

`CMP-SCENE`, `CMP-CONTROL`, and `CMP-ENG-DASH` are demonstration tools. They
must remain outside the logical production vehicle architecture even though
they interact with its simulated boundaries.

### Domain Controller substrate and Vehicle Data Platform

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| `CMP-FACTORY` | OEM Demo Factory Image | Immutable unprovisioned SOP substrate with no feature payload, Cloud identity or reusable vehicle secret | Platform Team; manufacturing/FOTA baseline | Integration recipes in `aos-vehicle-platform`; immutable image remains outside Git | `EVIDENCE`; clean accepted artifact `NEW` |
| `CMP-RUNTIME` | Provider-Specific Empty-Slot Runtime | Preinstalled Service Manager runtime, bounded provider slot, health and storage boundary for the Vehicle Data Platform payload | Platform Team; factory image | `aos-vehicle-platform` | `EVIDENCE`; final factory qualification required |
| `CMP-AOS-CORE` | AosCore and Service Manager | Unit identity, desired state, security, update lifecycle, service execution and status | AosEdge platform | External AosVM/AosCore release | `EXTERNAL / CURRENT` |
| `CMP-KUKSA` | KUKSA Databroker | Stable in-vehicle service-facing VSS data boundary | SOP substrate; Platform Team governs the exposed contract | External executable plus configuration/contract in `aos-vehicle-platform` | Executable `CURRENT`; final contract `EXTEND` |
| `CMP-VDP` | Vehicle Data Platform Capability | Privileged VISS client, signal selection, validation, normalization, KUKSA actual-value publication, versioned contract and future allowlisted outbound advisory path | Platform Team; independent FOTA | `aos-vehicle-platform` | Inbound `EVIDENCE`; accepted v1-v3 graph `EXTEND` |
| `CMP-KUKSA-AUTH` | Aos-to-KUKSA Authorization Adapter | Derive least-privilege KUKSA access from platform/service identity without artifact-embedded shared tokens | Platform security; factory/platform lifecycle | Future `aos-vehicle-platform` integration | `DEFERRED` production hardening; prototype tokens remain temporary fixtures |

`CMP-RUNTIME` is provider-specific and hosts one bounded component type. This
register makes no claim that the current runtime is a generic arbitrary
component runtime.

### Function Team 1 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| `CMP-BHS` | Brake Health In-Vehicle Service | Read the accepted KUKSA contract, perform local analysis, retain bounded reports and request the allowlisted advisory | Function Team 1 / Service Provider 1; SOTA 1 | `brake-health-service` | Scaffold `CURRENT`; product behavior `NEW` |
| `CMP-BRAKE-BE` | Brake Health Backend | Idempotent report ingestion, persistence and API for functional results | Function Team 1; functional Cloud product | Repository decision pending | `NEW` |
| `CMP-BRAKE-DASH` | Brake Health Function Dashboard | Present Brake Health inputs, local result, service/capability versions and online/offline delivery state from the backend | Function Team 1; functional Cloud product | Repository decision pending | `NEW` |

The backend and dashboard are not part of the in-vehicle SOTA artifact and do
not participate in the time-critical local advisory decision.

### Function Team 2 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| `CMP-EVENT` | Vehicle Stability Event In-Vehicle Service | Detect a low-friction event locally from an existing KUKSA contract and upload only a bounded event package | Function Team 2 / Service Provider 2; SOTA 2 | Proposed `vehicle-stability-event-service` | `NEW` |
| `CMP-EVENT-BE` | Vehicle Stability Event Backend | Idempotent event-package ingestion, persistence and API | Function Team 2; functional Cloud product | Repository decision pending | `NEW` |
| `CMP-EVENT-DASH` | Event-Based Data Dashboard | Present event time, state, service/capability version, Unit role and delivery status from the event backend | Function Team 2; functional Cloud product | Repository decision pending | `NEW` |

Function Team 2 is a peer of Function Team 1. Its service, backend, dashboard,
identity and SOTA lifecycle must not be placed inside the Brake Health product
or routed through it.

### Software delivery, operations and demo domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| `CMP-AOS-CLOUD` | AosCloud Lifecycle Authority | Provisioning, Unit/Node state, authoritative desired/actual state, FOTA/SOTA lifecycle, validation and promotion | AosEdge platform / OEM Cloud | External AosCloud service | `EXTERNAL / CURRENT`; exact demo operations require qualification |
| `CMP-SW-DASH` | OEM Software Delivery Dashboard | Simplified presentation and scoped approved actions over current AosCloud state; no parallel desired-state store | Demo solution | `aosedge-sdv-demo` | `NEW` |
| `CMP-LOG-PIPE` | AosEdge Log Collection and Delivery | Select, buffer and transport approved system/service operational logs | AosEdge platform integration | External mechanisms plus deployment configuration; final repository allocation pending | `EXTERNAL / EXTEND` |
| `CMP-ELK` | Vehicle and Service Log View | Access-controlled storage, search and presentation of selected operational evidence | OEM operational environment | External deployment/integration | `NEW` integration; product itself `EXTERNAL` |
| `CMP-ORCH` | Demo Orchestrator | Factory-overlay creation, role binding, provisioning reconciliation, CARLA source selection/replay, release sequencing, evidence correlation, retirement and reset | Demo solution | `aosedge-sdv-demo` | Existing helpers `EVIDENCE`; unified orchestrator `NEW` |

The native future AosCloud SOTA-to-FOTA dependency-admission capability is a
deferred feature of `CMP-AOS-CLOUD`, not a new project component. In
particular, `CMP-SW-DASH` must not implement a temporary admission controller.

## Runtime Roles and Deployable Products

| Item | Kind | Component graph or payload | Lifecycle |
| --- | --- | --- | --- |
| Validation Unit (`VU`) | Runtime role/instance | One fresh instance of `CMP-FACTORY`, `CMP-RUNTIME`, `CMP-AOS-CORE`, `CMP-KUKSA`, plus stage-selected payloads | Per demo run |
| Demonstration Unit (`DU`) | Runtime role/instance | A separate fresh instance of the same accepted graph | Per demo run |
| OEM Demo Factory Image | Immutable product artifact | `CMP-FACTORY`, including `CMP-RUNTIME`, `CMP-AOS-CORE` and `CMP-KUKSA`, without feature payloads | Manufacturing baseline |
| Vehicle Data Platform Capability v1-v3 | FOTA artifact family | `CMP-VDP` | Platform Team FOTA |
| Brake Health Service v1-v3 | SOTA artifact family | `CMP-BHS` | Service Provider 1 / SOTA 1 |
| Vehicle Stability Event Service | SOTA artifact family | `CMP-EVENT` | Service Provider 2 / SOTA 2 |

The same accepted artifact bytes and digest move from `VU` qualification to
`DU` promotion. Rebuilding an artifact for promotion is not permitted.

## Repository Allocation

| Repository or external boundary | Allocated components | Decision |
| --- | --- | --- |
| `CarlaSim` | `CMP-CARLA` | Keep simulator source and Apple Silicon port separate from solution code. |
| `UnrealEngine5_carla` | Restricted build dependency of `CMP-CARLA` | Keep private and outside all public repositories. |
| `carla-ego-runtime` | `CMP-SCENE`, `CMP-CONTROL`, `CMP-GW`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH` | One coherent simulated Vehicle Gateway and demo-vehicle tooling boundary. |
| `aos-vehicle-platform` | `CMP-FACTORY` integration, `CMP-RUNTIME`, `CMP-VDP`, future `CMP-KUKSA-AUTH`, `CMP-KUKSA` contract/configuration | Platform Team source and FOTA boundary. |
| `brake-health-service` | `CMP-BHS` | Function Team 1 in-vehicle SOTA source only. |
| Proposed `vehicle-stability-event-service` | `CMP-EVENT` | Function Team 2 in-vehicle SOTA source only; repository not yet created. |
| Future Function Team 1 Cloud repository | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | Name and whether backend/dashboard share one repository require review. |
| Future Function Team 2 Cloud repository | `CMP-EVENT-BE`, `CMP-EVENT-DASH` | Name and whether backend/dashboard share one repository require review. |
| `aosedge-sdv-demo` | `CMP-SW-DASH`, `CMP-ORCH`, cross-component contracts, qualification and system documentation | Solution integration; must not absorb component product source. |
| AosEdge/AosCloud | `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, base `CMP-LOG-PIPE` mechanisms | External platform dependency. |
| OEM operational deployment | `CMP-ELK` and deployment-specific log integration | External environment; configuration ownership still requires a decision. |

No repository is created, renamed or added to `workspace/repositories.json` by
this review candidate.

## Runtime Data Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| `IF-VEH-001` | `CMP-CARLA` | `CMP-GW` | Native CARLA vehicle, dynamics and sensor state | CARLA runtime state | `CURRENT` |
| `IF-VEH-002` | `CMP-CONTROL` | `CMP-GW` | Authenticated manual/autopilot/safe-stop control request | Gateway control state | `CURRENT` |
| `IF-VEH-003` | `CMP-GW` | `CMP-CARLA` | CARLA actuator/control commands | Gateway control arbitration | `CURRENT` |
| `IF-VEH-004` | `CMP-GW` | `CMP-VISS` | Normalized VSS signal model and source status | Gateway VSS projection | `CURRENT / EXTEND` |
| `IF-VEH-005` | `CMP-VISS` | `CMP-VDP` | TLS VISS 3.1 Get/Subscribe for accepted telemetry and status paths | Gateway VISS contract | `EVIDENCE`; freeze v1-v3 contract |
| `IF-VEH-006` | `CMP-VISS` | `CMP-ENG-DASH` | Independent read-only telemetry and Gateway-status subscription | Gateway VISS contract | Telemetry `CURRENT`; status `EXTEND` |
| `IF-DATA-001` | `CMP-VDP` | `CMP-KUKSA` | Validated actual values, availability, freshness and provenance | Versioned Vehicle Data Platform contract | `EVIDENCE / EXTEND` |
| `IF-DATA-002` | `CMP-KUKSA` | `CMP-BHS` | `kuksa.val.v1` read/subscribe subset for Brake Health | Vehicle Data Platform contract | `NEW` accepted service contract |
| `IF-DATA-003` | `CMP-KUKSA` | `CMP-EVENT` | `kuksa.val.v1` read/subscribe dynamics subset for low-friction detection | Vehicle Data Platform contract | `NEW` accepted service contract |
| `IF-ADV-001` | `CMP-BHS` | `CMP-KUKSA` | Allowlisted Brake Health advisory write/actuate request | Brake Health request constrained by platform policy | `NEW` |
| `IF-ADV-002` | `CMP-KUKSA` | `CMP-VDP` | Advisory target change plus caller authorization context | Vehicle Data Platform outbound contract | `NEW` |
| `IF-ADV-003` | `CMP-VDP` | `CMP-VISS` | Narrow VISS Set request for the accepted advisory target | Platform outbound allowlist | `NEW` |
| `IF-ADV-004` | `CMP-VISS` | `CMP-GW-ADV` | Validated advisory target delivery | Gateway contract | `NEW` |
| `IF-ADV-005` | `CMP-GW-ADV` | `CMP-VISS` | Factual received/rejected/status signal | Gateway state | `NEW` |

The advisory chain proves only request handling and Gateway state. It does not
prove a production driver display, acknowledgement, or brake actuation.

## Functional Cloud Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| `IF-FUNC-001` | `CMP-BHS` | `CMP-BRAKE-BE` | Versioned, bounded, idempotent Brake Health report with original event time | Function Team 1 data contract | `NEW` |
| `IF-FUNC-002` | `CMP-BRAKE-BE` | `CMP-BRAKE-DASH` | Query/subscription API for persisted Brake Health results | Function Team 1 backend | `NEW` |
| `IF-FUNC-003` | `CMP-EVENT` | `CMP-EVENT-BE` | Versioned, bounded, idempotent low-friction event package | Function Team 2 data contract | `NEW` |
| `IF-FUNC-004` | `CMP-EVENT-BE` | `CMP-EVENT-DASH` | Query/subscription API for persisted event results | Function Team 2 backend | `NEW` |

Functional Cloud interfaces are asynchronous. Loss of Cloud connectivity must
not stop local Brake Health analysis, advisory generation, or low-friction
event detection.

## Lifecycle and Operational Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| `IF-LC-001` | Platform Team release pipeline | `CMP-AOS-CLOUD` | Immutable, signed and digest-addressed Vehicle Data Platform FOTA artifact | Platform Team artifact plus AosCloud record | `EXTEND / QUALIFY` |
| `IF-LC-002` | Function Team 1 pipeline | `CMP-AOS-CLOUD` | Immutable Brake Health SOTA artifact and compatibility metadata | Service Provider 1 artifact plus AosCloud record | `NEW / QUALIFY` |
| `IF-LC-003` | Function Team 2 pipeline | `CMP-AOS-CLOUD` | Immutable Vehicle Stability Event SOTA artifact and compatibility metadata | Service Provider 2 artifact plus AosCloud record | `NEW / QUALIFY` |
| `IF-LC-004` | `CMP-AOS-CLOUD` | `CMP-AOS-CORE` | Provisioning, desired state, update delivery, validation, status and retirement | AosCloud and current Unit state | `EXTERNAL / EXTEND` qualification |
| `IF-LC-005` | `CMP-SW-DASH` | `CMP-AOS-CLOUD` | Scoped API reads, effective-target preview and explicitly approved actions | AosCloud; dashboard holds no parallel desired state | `NEW` |
| `IF-LC-006` | `CMP-AOS-CORE` | `CMP-RUNTIME` / `CMP-BHS` / `CMP-EVENT` | Install, start, stop, update, rollback, readiness and resource enforcement | Unit actual state | Platform mechanism `CURRENT`; target graph `EXTEND` |
| `IF-OBS-001` | In-vehicle platform and services | `CMP-LOG-PIPE` | Selected structured operational logs with redaction and correlation fields | Originating component plus log policy | `EXTERNAL / EXTEND` |
| `IF-OBS-002` | `CMP-LOG-PIPE` | `CMP-ELK` | Authenticated, buffered Cloud log delivery | Accepted centralized log store | `NEW` integration |
| `IF-DEMO-001` | `CMP-ORCH` | QEMU/AosVM instances | Overlay creation, role binding, start/stop, source selection and safe retirement | Local session manifest plus authoritative Unit state | `EVIDENCE / EXTEND` |

Native SOTA-to-FOTA compatibility admission is a future behavior on
`IF-LC-004`. Until an implementing AosEdge release is available and qualified,
the corresponding negative-path demo remains `DEFERRED` and no local
interface substitutes for it.

## Provisional Component Requirement Packages

This allocation is the bridge to the next document set. It does not yet define
component-level normative requirements.

| Package | Components | Principal interfaces | Parent system requirements |
| --- | --- | --- | --- |
| `CR-VEHICLE-SIM` | `CMP-CARLA`, `CMP-SCENE` | `IF-VEH-001`, `IF-VEH-003` | `SYS-SRC-001–002`, `SYS-BHS-002`, `SYS-EVT-002`, `SYS-EVT-005`, `SYS-RET-003` |
| `CR-GATEWAY` | `CMP-CONTROL`, `CMP-GW`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH` | `IF-VEH-002–006`, `IF-ADV-003–005` | `SYS-SRC-001–002`, `SYS-VDP-004–005`, `SYS-BHS-003`, `SYS-SEC-003`, `SYS-OBS-001`, `SYS-TIM-002` |
| `CR-FACTORY` | `CMP-FACTORY`, `CMP-RUNTIME` | `IF-LC-004`, `IF-LC-006`, `IF-DEMO-001` | `SYS-MFG-001–003`, `SYS-ID-001–002`, `SYS-VDP-001`, `SYS-RET-003` |
| `CR-VDP` | `CMP-KUKSA`, `CMP-VDP` | `IF-VEH-005`, `IF-DATA-001–003`, `IF-ADV-002–003`, `IF-LC-001`, `IF-LC-006` | `SYS-REL-001`, `SYS-REL-003–005`, `SYS-VDP-001–005`, `SYS-SEC-001–003` |
| `CR-BHS` | `CMP-BHS` | `IF-DATA-002`, `IF-ADV-001`, `IF-FUNC-001`, `IF-LC-002`, `IF-LC-006` | `SYS-REL-001`, `SYS-REL-003–005`, `SYS-BHS-001–004`, `SYS-TIM-002` |
| `CR-EVT` | `CMP-EVENT` | `IF-DATA-003`, `IF-FUNC-003`, `IF-LC-003`, `IF-LC-006` | `SYS-REL-001`, `SYS-REL-003–005`, `SYS-EVT-001–005` |
| `CR-AOS` | `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, `CMP-LOG-PIPE` | `IF-LC-001–006`, `IF-OBS-001–002` | `SYS-ID-001–004`, `SYS-REL-001–006`, `SYS-OBS-002–004`, `SYS-TIM-001`, `SYS-RET-001` |
| `CR-BRAKE-CLOUD` | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | `IF-FUNC-001–002` | `SYS-BHS-001`, `SYS-BHS-004`, `SYS-OBS-001`, `SYS-OBS-003–004`, `SYS-RET-002` |
| `CR-EVENT-CLOUD` | `CMP-EVENT-BE`, `CMP-EVENT-DASH` | `IF-FUNC-003–004` | `SYS-EVT-003–004`, `SYS-OBS-001`, `SYS-OBS-003–004`, `SYS-RET-002` |
| `CR-DEMO` | `CMP-SW-DASH`, `CMP-ORCH`, `CMP-ELK` integration | `IF-LC-005`, `IF-OBS-002`, `IF-DEMO-001` | `SYS-ID-001–003`, `SYS-SRC-001–002`, `SYS-REL-002`, `SYS-REL-004`, `SYS-OBS-001–004`, `SYS-TIM-001`, `SYS-RET-001–004` |
| `CR-CROSS` | All components; future `CMP-KUKSA-AUTH` | All trust, resource, timing and offline boundaries | `SYS-SEC-001–003`, `SYS-OBS-003–004`, `SYS-TIM-001–002` |
| `CR-E2E` | Complete accepted graph on `VU` and `DU` | All accepted interfaces | Every parent `SYS-*` requirement and relevant `AF-*` flow |

Ranges such as `SYS-VDP-001–005` refer to the inclusive identifiers already
defined in System Requirements 0.1; they do not create new requirements.
`SYS-REL-006` remains deferred and is allocated only to `CR-AOS`. It is not a
requirement on `CMP-SW-DASH`.

## Boundary Decisions Requiring Review

1. Confirm the component IDs and the separation between logical components,
   deployable artifacts, repositories and Unit instances.
2. Confirm that the existing `carla-ego-runtime` repository remains the owner
   of scenario tooling, Gateway behavior, VISS, advisory handling and the
   Engineering Telematics Dashboard.
3. Confirm `vehicle-stability-event-service` as the future Function Team 2
   in-vehicle repository name and scope before creating it.
4. Decide whether each functional backend and dashboard share one Cloud-product
   repository. The recommendation is one repository per Function Team Cloud
   product, separate from its in-vehicle SOTA repository.
5. Confirm that `CMP-SW-DASH` and `CMP-ORCH` remain solution components in
   `aosedge-sdv-demo` rather than becoming lifecycle authorities.
6. Decide where deployment-specific `CMP-LOG-PIPE` to `CMP-ELK` configuration
   is owned after the actual AosEdge logging topology is qualified.
7. Confirm that `CMP-KUKSA-AUTH` remains an explicit deferred production
   hardening component rather than being hidden inside prototype token files.

## Acceptance Gate for Version 0.1

The register is ready to become the component baseline when reviewers confirm:

1. every HLA 1.1 box has exactly one primary component owner;
2. every audience-visible dashboard has exactly one authoritative data source;
3. the three independent FOTA/SOTA lifecycles remain separated;
4. Function Team 1 and Function Team 2 are peer product domains;
5. `VU` and `DU` remain runtime roles rather than duplicated component sets;
6. current, engineering-evidence, target, external and deferred states are not
   presented as equivalent;
7. all runtime, functional Cloud, lifecycle and observability boundaries needed
   by Scenario 1.1 and the Function Team 2 extension have interface IDs;
8. deferred native Cloud dependency admission and authorization-adapter work
   are not presented as implemented;
9. no component claims a production driver HMI, continuous raw-telemetry Cloud
   stream, third-party Service Provider, Fleet Operator or production fleet;
10. the provisional requirement packages can be expanded without changing HLA
    1.1 or the accepted demo scenarios.

After acceptance, component requirements shall be written package by package,
starting with `CR-VEHICLE-SIM` and `CR-GATEWAY`. Each requirement shall cite a
parent `SYS-*` requirement, an `AF-*` flow, an interface ID, a verification
method and retained evidence. Implementation planning begins only after the
relevant package and acceptance tests are reviewed.
