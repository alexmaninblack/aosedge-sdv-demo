<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Decomposition and Interface Register 0.2

- Status: Review candidate
- Version: 0.2
- Prepared: 2026-08-18
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.2](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 1.2](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 1.1](../architecture/demo-scenario-architecture-flows.md)
- Requirements input: [System Requirements and Traceability 0.2](system-requirements-and-traceability.md)
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

1. High-Level Architecture 1.2 owns system boundaries, authorities and
   invariants.
2. Demo Scenario 1.2 owns the audience-visible lifecycle and stage sequence.
3. Architecture Flows 1.1 owns detailed runtime, lifecycle, observability and
   failure flows.
4. System Requirements 0.2 owns normative `SYS-*` obligations and gap
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
different software components. Each is a runtime deployment created from the
accepted factory-image artifact; neither is an instance of the build-time
Factory Baseline Assembly component.

### Component is not deployment artifact

The Vehicle Data Platform Capability is one platform component delivered in
independently versioned FOTA artifacts. Brake Health and Tire Health are
two peer functional components delivered in separate SOTA lifecycles. Version
changes do not create new logical components.

The `OEM Factory Baseline Assembly` is a build-time logical component. It
reproducibly produces the immutable `OEM Demo Factory Image` artifact. That
artifact contains the factory-installed runtime graph and is the source for
fresh Validation and Demonstration Unit deployments; the artifact is not
itself a `CMP-*` component.

### Dashboard is not authority

Every dashboard is a presentation surface over one authoritative source:

| Dashboard | Authoritative source |
| --- | --- |
| Engineering Telematics Dashboard | Vehicle Gateway VISS endpoint |
| OEM Software Delivery Dashboard | AosCloud API and current Unit state |
| Brake Health Function Dashboard | Function Team 1 backend |
| Tire Health Function Dashboard | Function Team 2 backend |
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
| <a id="cmp-carla"></a>`CMP-CARLA` | CARLA Virtual Physical Vehicle | Vehicle dynamics, road environment, native sensor state and actuators | Vehicle simulation | `CarlaSim`; restricted Unreal dependency remains separate | `CURRENT` |
| <a id="cmp-scene"></a>`CMP-SCENE` | Deterministic Scenario Controller | Repeatable obstacle/braking stimulus, manual takeover, safe stop, actor cleanup, and explicit accelerated/pre-aged tire-degradation stimulus | Demo vehicle tooling | `carla-ego-runtime` | Brake scenario `CURRENT`; Tire Health stimulus `EXTEND` |
| <a id="cmp-control"></a>`CMP-CONTROL` | Vehicle Control UI | Manual/autopilot selection, throttle, brake, steering and safe-stop commands over the separate control channel | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT` |
| <a id="cmp-gw"></a>`CMP-GW` | Vehicle Gateway Runtime | CARLA sampling, control arbitration, signal normalization and Gateway health/state | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / EXTEND` |
| <a id="cmp-viss"></a>`CMP-VISS` | Vehicle Gateway VISS 3.1 Server | TLS-protected VSS Get/Subscribe and the future narrowly scoped advisory Set contract | Vehicle Gateway tooling | `carla-ego-runtime` | Read path `CURRENT`; write path `EXTEND` |
| <a id="cmp-gw-adv"></a>`CMP-GW-ADV` | Gateway Advisory Handler | Validate typed allowlisted Brake Health and Tire Health advisory targets and publish factual reception/status without claiming driver display | Vehicle Gateway tooling | `carla-ego-runtime` | `NEW` |
| <a id="cmp-eng-dash"></a>`CMP-ENG-DASH` | Engineering Telematics Dashboard | Independent read-only engineering view of Gateway telemetry and typed advisory/status evidence | Demo engineering tooling | `carla-ego-runtime` | Telemetry `CURRENT`; advisory/status `EXTEND` |

`CMP-SCENE`, `CMP-CONTROL`, and `CMP-ENG-DASH` are demonstration tools. They
must remain outside the logical production vehicle architecture even though
they interact with its simulated boundaries.

### Domain Controller substrate and Vehicle Data Platform

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-factory"></a>`CMP-FACTORY` | OEM Factory Baseline Assembly | Reproducibly compose, build, qualify and freeze the unprovisioned SOP substrate from identified upstream and OEM integration inputs | Platform Team; pre-SOP manufacturing/build lifecycle | Integration recipes and qualification inputs in `aos-vehicle-platform`; output image remains outside Git | Build evidence `EVIDENCE`; accepted assembly process and output artifact `NEW` |
| <a id="cmp-runtime"></a>`CMP-RUNTIME` | Provider-Specific Empty-Slot Runtime | Preinstalled Service Manager runtime, bounded provider slot, health and storage boundary for the Vehicle Data Platform payload | Platform Team; factory image | `aos-vehicle-platform` | `EVIDENCE`; final factory qualification required |
| <a id="cmp-aos-core"></a>`CMP-AOS-CORE` | AosCore and Service Manager | Unit identity, desired state, security, update lifecycle, service execution and status | AosEdge platform | External AosVM/AosCore release | `EXTERNAL / CURRENT` |
| <a id="cmp-kuksa"></a>`CMP-KUKSA` | KUKSA Databroker | Stable in-vehicle service-facing VSS data boundary | SOP substrate; Platform Team governs the exposed contract | External executable plus configuration/contract in `aos-vehicle-platform` | Executable `CURRENT`; final contract `EXTEND` |
| <a id="cmp-vdp"></a>`CMP-VDP` | Vehicle Data Platform Capability | Privileged VISS client, signal selection, validation, normalization, KUKSA actual-value publication, versioned contract and future allowlisted outbound advisory path | Platform Team; independent FOTA | `aos-vehicle-platform` | Inbound `EVIDENCE`; accepted v1-v3 graph `EXTEND` |
| <a id="cmp-kuksa-auth"></a>`CMP-KUKSA-AUTH` | Aos-to-KUKSA Authorization Adapter | Derive least-privilege KUKSA access from platform/service identity without artifact-embedded shared tokens | Platform security; factory/platform lifecycle | Future `aos-vehicle-platform` integration | `DEFERRED` production hardening; prototype tokens remain temporary fixtures |

`CMP-RUNTIME` is provider-specific and hosts one bounded component type. This
register makes no claim that the current runtime is a generic arbitrary
component runtime.

### Function Team 1 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-bhs"></a>`CMP-BHS` | Brake Health In-Vehicle Service | Read the accepted KUKSA contract, perform local analysis, retain bounded reports and request the allowlisted advisory | Function Team 1 / Service Provider 1; SOTA 1 | `brake-health-service` | Scaffold `CURRENT`; product behavior `NEW` |
| <a id="cmp-brake-be"></a>`CMP-BRAKE-BE` | Brake Health Backend | Idempotent report ingestion, persistence and API for functional results | Function Team 1; functional Cloud product | Repository decision pending | `NEW` |
| <a id="cmp-brake-dash"></a>`CMP-BRAKE-DASH` | Brake Health Function Dashboard | Present Brake Health inputs, local result, service/capability versions and online/offline delivery state from the backend | Function Team 1; functional Cloud product | Repository decision pending | `NEW` |

The backend and dashboard are not part of the in-vehicle SOTA artifact and do
not participate in the time-critical local advisory decision.

### Function Team 2 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-tire"></a>`CMP-TIRE` | Tire Health In-Vehicle Service | Maintain a bounded persistent tire-condition estimate from the accepted KUKSA contract, create bounded reports/events, and request the typed inspection advisory | Function Team 2 / Service Provider 2; SOTA 2 | Proposed `tire-health-service` | `NEW` |
| <a id="cmp-tire-be"></a>`CMP-TIRE-BE` | Tire Health Backend | Idempotent condition-summary/event ingestion, persistence and API | Function Team 2; functional Cloud product | Repository decision pending | `NEW` |
| <a id="cmp-tire-dash"></a>`CMP-TIRE-DASH` | Tire Health Function Dashboard | Present condition band, event state, service/capability version, Unit role and delivery status from the Tire Health backend | Function Team 2; functional Cloud product | Repository decision pending | `NEW` |

Function Team 2 is a peer of Function Team 1. Its service, backend, dashboard,
identity and SOTA lifecycle must not be placed inside the Brake Health product
or routed through it.

### Software delivery, operations and demo domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-aos-cloud"></a>`CMP-AOS-CLOUD` | AosCloud Lifecycle Authority | Provisioning, Unit/Node state, authoritative desired/actual state, FOTA/SOTA lifecycle, validation and promotion | AosEdge platform / OEM Cloud | External AosCloud service | `EXTERNAL / CURRENT`; exact demo operations require qualification |
| <a id="cmp-sw-dash"></a>`CMP-SW-DASH` | OEM Software Delivery Dashboard | Simplified presentation and scoped approved actions over current AosCloud state; no parallel desired-state store | Demo solution | `aosedge-sdv-demo` | `NEW` |
| <a id="cmp-log-pipe"></a>`CMP-LOG-PIPE` | AosEdge Log Collection and Delivery | Select, buffer and transport approved system/service operational logs | AosEdge platform integration | External mechanisms plus deployment configuration; final repository allocation pending | `EXTERNAL / EXTEND` |
| <a id="cmp-elk"></a>`CMP-ELK` | Vehicle and Service Log View | Access-controlled storage, search and presentation of selected operational evidence | OEM operational environment | External deployment/integration | `NEW` integration; product itself `EXTERNAL` |
| <a id="cmp-orch"></a>`CMP-ORCH` | Demo Orchestrator | Factory-overlay creation, role binding, provisioning reconciliation, CARLA source selection/replay, release sequencing, evidence correlation, retirement and reset | Demo solution | `aosedge-sdv-demo` | Existing helpers `EVIDENCE`; unified orchestrator `NEW` |

The native future AosCloud SOTA-to-FOTA dependency-admission capability is a
deferred feature of `CMP-AOS-CLOUD`, not a new project component. In
particular, `CMP-SW-DASH` must not implement a temporary admission controller.

## Runtime Roles and Deployable Products

| Item | Kind | Component graph or payload | Lifecycle |
| --- | --- | --- | --- |
| Validation Unit (`VU`) | Runtime role/deployment | One fresh deployment created from the accepted OEM Demo Factory Image; runs `CMP-RUNTIME`, `CMP-AOS-CORE`, `CMP-KUKSA` and stage-selected payloads | Per demo run |
| Demonstration Unit (`DU`) | Runtime role/deployment | A separate fresh deployment created from the same accepted image and running the same stage-selected component graph | Per demo run |
| OEM Demo Factory Image | Immutable product artifact | Produced by `CMP-FACTORY`; contains `CMP-RUNTIME`, `CMP-AOS-CORE` and `CMP-KUKSA`, without feature payloads or reusable vehicle identity | Manufacturing baseline |
| Vehicle Data Platform Capability v1-v3 | FOTA artifact family | `CMP-VDP` | Platform Team FOTA |
| Brake Health Service v1-v3 | SOTA artifact family | `CMP-BHS` | Service Provider 1 / SOTA 1 |
| Tire Health Service | SOTA artifact family | `CMP-TIRE` | Service Provider 2 / SOTA 2 |

The same accepted artifact bytes and digest move from `VU` qualification to
`DU` promotion. Rebuilding an artifact for promotion is not permitted.

## Repository Allocation

| Repository or external boundary | Allocated components | Decision |
| --- | --- | --- |
| `CarlaSim` | `CMP-CARLA` | Keep simulator source and Apple Silicon port separate from solution code. |
| `UnrealEngine5_carla` | Restricted build dependency of `CMP-CARLA` | Keep private and outside all public repositories. |
| `carla-ego-runtime` | `CMP-SCENE`, `CMP-CONTROL`, `CMP-GW`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH` | One coherent simulated Vehicle Gateway and demo-vehicle tooling boundary. |
| `aos-vehicle-platform` | `CMP-FACTORY` assembly source, `CMP-RUNTIME`, `CMP-VDP`, future `CMP-KUKSA-AUTH`, `CMP-KUKSA` contract/configuration | Platform Team source and FOTA boundary; immutable Factory Image output remains outside Git. |
| `brake-health-service` | `CMP-BHS` | Function Team 1 in-vehicle SOTA source only. |
| Proposed `tire-health-service` | `CMP-TIRE` | Function Team 2 in-vehicle SOTA source only; repository not yet created. |
| Future Function Team 1 Cloud repository | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | Name and whether backend/dashboard share one repository require review. |
| Future Function Team 2 Cloud repository | `CMP-TIRE-BE`, `CMP-TIRE-DASH` | Name and whether backend/dashboard share one repository require review. |
| `aosedge-sdv-demo` | `CMP-SW-DASH`, `CMP-ORCH`, cross-component contracts, qualification and system documentation | Solution integration; must not absorb component product source. |
| AosEdge/AosCloud | `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, base `CMP-LOG-PIPE` mechanisms | External platform dependency. |
| OEM operational deployment | `CMP-ELK` and deployment-specific log integration | External environment; configuration ownership still requires a decision. |

No repository is created, renamed or added to `workspace/repositories.json` by
this review candidate.

## Runtime Data Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-veh-001"></a>`IF-VEH-001` | `CMP-CARLA` | `CMP-GW` | Native CARLA vehicle, dynamics and sensor state | CARLA runtime state | `CURRENT` |
| <a id="if-veh-002"></a>`IF-VEH-002` | `CMP-CONTROL` | `CMP-GW` | Authenticated manual/autopilot/safe-stop control request | Gateway control state | `CURRENT` |
| <a id="if-veh-003"></a>`IF-VEH-003` | `CMP-GW` | `CMP-CARLA` | CARLA actuator/control commands | Gateway control arbitration | `CURRENT` |
| <a id="if-veh-004"></a>`IF-VEH-004` | `CMP-GW` | `CMP-VISS` | Normalized VSS signal model and source status | Gateway VSS projection | `CURRENT / EXTEND` |
| <a id="if-veh-005"></a>`IF-VEH-005` | `CMP-VISS` | `CMP-VDP` | TLS VISS 3.1 Get/Subscribe for accepted telemetry and status paths | Gateway VISS contract | `EVIDENCE`; freeze v1-v3 contract |
| <a id="if-veh-006"></a>`IF-VEH-006` | `CMP-VISS` | `CMP-ENG-DASH` | Independent read-only telemetry and Gateway-status subscription | Gateway VISS contract | Telemetry `CURRENT`; status `EXTEND` |
| <a id="if-data-001"></a>`IF-DATA-001` | `CMP-VDP` | `CMP-KUKSA` | Validated actual values, availability, freshness and provenance | Versioned Vehicle Data Platform contract | `EVIDENCE / EXTEND` |
| <a id="if-data-002"></a>`IF-DATA-002` | `CMP-KUKSA` | `CMP-BHS` | `kuksa.val.v1` read/subscribe subset for Brake Health | Vehicle Data Platform contract | `NEW` accepted service contract |
| <a id="if-tire-001"></a>`IF-TIRE-001` | `CMP-KUKSA` | `CMP-TIRE` | `kuksa.val.v1` read/subscribe dynamics subset for tire-condition estimation | Vehicle Data Platform contract | `NEW` accepted service contract |
| <a id="if-adv-001"></a>`IF-ADV-001` | `CMP-BHS` | `CMP-KUKSA` | Allowlisted Brake Health advisory write/actuate request | Brake Health request constrained by platform policy | `NEW` |
| <a id="if-tire-002"></a>`IF-TIRE-002` | `CMP-TIRE` | `CMP-KUKSA` | Allowlisted Tire Health advisory write/actuate request | Tire Health request constrained by platform policy | `NEW` |
| <a id="if-adv-002"></a>`IF-ADV-002` | `CMP-KUKSA` | `CMP-VDP` | Advisory target change plus caller authorization context | Vehicle Data Platform outbound contract | `NEW` |
| <a id="if-adv-003"></a>`IF-ADV-003` | `CMP-VDP` | `CMP-VISS` | Narrow VISS Set request for the accepted advisory target | Platform outbound allowlist | `NEW` |
| <a id="if-adv-004"></a>`IF-ADV-004` | `CMP-VISS` | `CMP-GW-ADV` | Validated advisory target delivery | Gateway contract | `NEW` |
| <a id="if-adv-005"></a>`IF-ADV-005` | `CMP-GW-ADV` | `CMP-VISS` | Factual received/rejected/status signal | Gateway state | `NEW` |

The advisory chain proves only request handling and Gateway state. It does not
prove a production driver display, acknowledgement, or brake actuation.

## Functional Cloud Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-func-001"></a>`IF-FUNC-001` | `CMP-BHS` | `CMP-BRAKE-BE` | Versioned, bounded, idempotent Brake Health report with original event time | Function Team 1 data contract | `NEW` |
| <a id="if-func-002"></a>`IF-FUNC-002` | `CMP-BRAKE-BE` | `CMP-BRAKE-DASH` | Query/subscription API for persisted Brake Health results | Function Team 1 backend | `NEW` |
| <a id="if-tire-003"></a>`IF-TIRE-003` | `CMP-TIRE` | `CMP-TIRE-BE` | Versioned, bounded and idempotent tire-condition summary or threshold event | Function Team 2 data contract | `NEW` |
| <a id="if-tire-004"></a>`IF-TIRE-004` | `CMP-TIRE-BE` | `CMP-TIRE-DASH` | Query/subscription API for persisted Tire Health results | Function Team 2 backend | `NEW` |

Functional Cloud interfaces are asynchronous. Loss of Cloud connectivity must
not stop local Brake Health or Tire Health analysis and advisory generation.

## Lifecycle and Operational Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-lc-001"></a>`IF-LC-001` | Platform Team release pipeline | `CMP-AOS-CLOUD` | Immutable, signed and digest-addressed Vehicle Data Platform FOTA artifact | Platform Team artifact plus AosCloud record | `EXTEND / QUALIFY` |
| <a id="if-lc-002"></a>`IF-LC-002` | Function Team 1 pipeline | `CMP-AOS-CLOUD` | Immutable Brake Health SOTA artifact and compatibility metadata | Service Provider 1 artifact plus AosCloud record | `NEW / QUALIFY` |
| <a id="if-lc-007"></a>`IF-LC-007` | Function Team 2 pipeline | `CMP-AOS-CLOUD` | Immutable Tire Health SOTA artifact and compatibility metadata | Service Provider 2 artifact plus AosCloud record | `NEW / QUALIFY` |
| <a id="if-lc-004"></a>`IF-LC-004` | `CMP-AOS-CLOUD` | `CMP-AOS-CORE` | Provisioning, desired state, update delivery, validation, status and retirement | AosCloud and current Unit state | `EXTERNAL / EXTEND` qualification |
| <a id="if-lc-005"></a>`IF-LC-005` | `CMP-SW-DASH` | `CMP-AOS-CLOUD` | Scoped API reads, effective-target preview and explicitly approved actions | AosCloud; dashboard holds no parallel desired state | `NEW` |
| <a id="if-lc-006"></a>`IF-LC-006` | `CMP-AOS-CORE` | `CMP-RUNTIME` / `CMP-BHS` / `CMP-TIRE` | Install, start, stop, update, rollback, readiness and resource enforcement | Unit actual state | Platform mechanism `CURRENT`; target graph `EXTEND` |
| <a id="if-obs-001"></a>`IF-OBS-001` | In-vehicle platform and services | `CMP-LOG-PIPE` | Selected structured operational logs with redaction and correlation fields | Originating component plus log policy | `EXTERNAL / EXTEND` |
| <a id="if-obs-002"></a>`IF-OBS-002` | `CMP-LOG-PIPE` | `CMP-ELK` | Authenticated, buffered Cloud log delivery | Accepted centralized log store | `NEW` integration |
| <a id="if-demo-001"></a>`IF-DEMO-001` | `CMP-ORCH` | QEMU/AosVM instances | Overlay creation, role binding, start/stop, source selection and safe retirement | Local session manifest plus authoritative Unit state | `EVIDENCE / EXTEND` |

Native SOTA-to-FOTA compatibility admission is a future behavior on
`IF-LC-004`. Until an implementing AosEdge release is available and qualified,
the corresponding negative-path demo remains `DEFERRED` and no local
interface substitutes for it.

## Provisional Component Requirement Packages

This allocation is the bridge to the next document set. It does not yet define
component-level normative requirements. The reader view explains the purpose
of each package without requiring another document. The detailed traceability
below is the single allocation record for exact identifiers.

| Package | Human-readable responsibility | Primary components | Requirement themes |
| --- | --- | --- | --- |
| <a id="cr-vehicle-sim"></a>`CR-VEHICLE-SIM` | Provide repeatable braking and explicit accelerated/pre-aged tire stimuli, exact source evidence, hidden ground-truth isolation and clean scenario reset. | CARLA vehicle and Scenario Controller | Determinism, source integrity, simulation truth and reset |
| <a id="cr-gateway"></a>`CR-GATEWAY` | Acquire and normalize vehicle state, expose VISS, arbitrate control, handle bounded advisory status and present the engineering view. | Control UI, Gateway, VISS, Advisory Handler and Engineering Dashboard | Telemetry contract, unavailable data, advisory safety and latency |
| <a id="cr-factory"></a>`CR-FACTORY` | Reproducibly assemble the clean unprovisioned Factory Image artifact and use it to create two identity-safe deployments with a healthy empty capability slot. | Factory Baseline Assembly and Empty-Slot Runtime | Reproducibility, artifact immutability, identity absence, overlay uniqueness and reset |
| <a id="cr-vdp"></a>`CR-VDP` | Deliver the versioned VISS-to-KUKSA data capability and the narrowly allowlisted outbound advisory path. | KUKSA and Vehicle Data Platform Capability | Compatibility, data quality, authorization, FOTA and rollback |
| <a id="cr-bhs"></a>`CR-BHS` | Run Brake Health analysis locally, report bounded results, operate offline and request only the approved advisory. | Brake Health In-Vehicle Service | Model determinism, reports, compatibility, offline operation and advisory scope |
| <a id="cr-tire"></a>`CR-TIRE` | Estimate tire condition locally, persist bounded state, upload bounded results and request the typed inspection advisory through an independent SOTA lifecycle. | Tire Health In-Vehicle Service | Existing signal contract, model, persistence, bounded reporting, advisory and isolation |
| <a id="cr-aos"></a>`CR-AOS` | Provide identity, desired/actual state, FOTA/SOTA lifecycle, dependency behavior, resource enforcement and operational log transport. | AosCore, AosCloud and Log Pipeline | Provisioning, lifecycle authority, validation, rollback, timing and retirement |
| <a id="cr-brake-cloud"></a>`CR-BRAKE-CLOUD` | Ingest and present Brake Health reports without entering the local decision path. | Brake Health Backend and Function Dashboard | Idempotency, offline synchronization, evidence and run-data retention |
| <a id="cr-tire-cloud"></a>`CR-TIRE-CLOUD` | Ingest and present Tire Health summaries/events as an independent Function Team product. | Tire Health Backend and Function Dashboard | Bounded results, idempotency, delivery state and run-data retention |
| <a id="cr-demo"></a>`CR-DEMO` | Orchestrate manufactured overlays, Unit roles, staged releases, authoritative dashboards, evidence and end-of-run retirement. | Software Delivery Dashboard, Demo Orchestrator and ELK integration | Target safety, source binding, observability, timing and reset |
| <a id="cr-cross"></a>`CR-CROSS` | Define security, authorization, redaction, timing, resource and offline constraints shared by multiple owners. | Cross-component concerns and future Authorization Adapter | Least privilege, fail-closed behavior, evidence controls and latency |
| <a id="cr-e2e"></a>`CR-E2E` | Prove the complete accepted graph on Validation and Demonstration Units across normal, failure, offline, recovery and retirement paths. | All accepted components | End-to-end acceptance and retained evidence |

## Retired Function Team 2 Identifiers

ADR 0008 replaced the Low-Friction candidate with Tire Health. The old IDs
remain resolvable for history, but must not be used by new requirements or
implementation:

| Retired identifier | Replacement |
| --- | --- |
| <a id="cmp-event"></a>`CMP-EVENT` | `CMP-TIRE` |
| <a id="cmp-event-be"></a>`CMP-EVENT-BE` | `CMP-TIRE-BE` |
| <a id="cmp-event-dash"></a>`CMP-EVENT-DASH` | `CMP-TIRE-DASH` |
| <a id="if-data-003"></a>`IF-DATA-003` | `IF-TIRE-001` |
| <a id="if-func-003"></a>`IF-FUNC-003` | `IF-TIRE-003` |
| <a id="if-func-004"></a>`IF-FUNC-004` | `IF-TIRE-004` |
| <a id="if-lc-003"></a>`IF-LC-003` | `IF-LC-007` |
| <a id="cr-evt"></a>`CR-EVT` | `CR-TIRE` |
| <a id="cr-event-cloud"></a>`CR-EVENT-CLOUD` | `CR-TIRE-CLOUD` |

## Detailed Package Traceability

The short labels below are reader aids. The linked System Requirements remain
the only normative definitions.

### `CR-VEHICLE-SIM` — Vehicle simulation and deterministic stimuli

- Components: [CARLA Virtual Physical Vehicle (`CMP-CARLA`)](#cmp-carla) and
  [Deterministic Scenario Controller (`CMP-SCENE`)](#cmp-scene).
- Interfaces: [CARLA state to Gateway (`IF-VEH-001`)](#if-veh-001) and
  [Gateway actuator commands (`IF-VEH-003`)](#if-veh-003).
- Parent requirements: [Exact source-to-Unit binding (`SYS-SRC-001`)](system-requirements-and-traceability.md#sys-src-001),
  [honest single-source presentation (`SYS-SRC-002`)](system-requirements-and-traceability.md#sys-src-002),
  [deterministic v2 inference (`SYS-BHS-002`)](system-requirements-and-traceability.md#sys-bhs-002),
  [explicit Tire Health simulation model (`SYS-TIRE-003`)](system-requirements-and-traceability.md#sys-tire-003), and
  [reset CARLA and preserve factory (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003).

### `CR-GATEWAY` — Vehicle Gateway and engineering view

- Components: [Vehicle Control UI (`CMP-CONTROL`)](#cmp-control),
  [Vehicle Gateway Runtime (`CMP-GW`)](#cmp-gw),
  [VISS Server (`CMP-VISS`)](#cmp-viss),
  [Gateway Advisory Handler (`CMP-GW-ADV`)](#cmp-gw-adv), and
  [Engineering Telematics Dashboard (`CMP-ENG-DASH`)](#cmp-eng-dash).
- Interfaces: [manual/autopilot control (`IF-VEH-002`)](#if-veh-002),
  [Gateway actuator commands (`IF-VEH-003`)](#if-veh-003),
  [normalized VSS projection (`IF-VEH-004`)](#if-veh-004),
  [VISS telemetry to the platform (`IF-VEH-005`)](#if-veh-005),
  [engineering telemetry subscription (`IF-VEH-006`)](#if-veh-006),
  [outbound VISS Set (`IF-ADV-003`)](#if-adv-003),
  [advisory delivery (`IF-ADV-004`)](#if-adv-004), and
  [factual Gateway status (`IF-ADV-005`)](#if-adv-005).
- Parent requirements: [exact source-to-Unit binding (`SYS-SRC-001`)](system-requirements-and-traceability.md#sys-src-001),
  [honest single-source presentation (`SYS-SRC-002`)](system-requirements-and-traceability.md#sys-src-002),
  [allowlisted outbound advisory (`SYS-VDP-004`)](system-requirements-and-traceability.md#sys-vdp-004),
  [explicit degraded data (`SYS-VDP-005`)](system-requirements-and-traceability.md#sys-vdp-005),
  [allowlisted v3 advisory (`SYS-BHS-003`)](system-requirements-and-traceability.md#sys-bhs-003),
  [offline Tire Health inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001), and
  [separate local and Cloud latency (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-FACTORY` — Factory assembly, artifact and empty slot

- Components: [OEM Factory Baseline Assembly (`CMP-FACTORY`)](#cmp-factory) and
  [Provider-Specific Empty-Slot Runtime (`CMP-RUNTIME`)](#cmp-runtime).
- Produced artifact: immutable `OEM Demo Factory Image`, from which separate
  Validation and Demonstration Unit runtime deployments are created.
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006), and
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001).
- Parent requirements: [reproducible factory image (`SYS-MFG-001`)](system-requirements-and-traceability.md#sys-mfg-001),
  [clean SOP substrate (`SYS-MFG-002`)](system-requirements-and-traceability.md#sys-mfg-002),
  [unique fresh overlays (`SYS-MFG-003`)](system-requirements-and-traceability.md#sys-mfg-003),
  [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001), and
  [reset CARLA and preserve factory (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003).

### `CR-VDP` — Vehicle Data Platform Capability

- Components: [KUKSA Databroker (`CMP-KUKSA`)](#cmp-kuksa) and
  [Vehicle Data Platform Capability (`CMP-VDP`)](#cmp-vdp).
- Interfaces: [VISS telemetry input (`IF-VEH-005`)](#if-veh-005),
  [KUKSA publication (`IF-DATA-001`)](#if-data-001),
  [Brake Health subscription (`IF-DATA-002`)](#if-data-002),
  [Tire Health subscription (`IF-TIRE-001`)](#if-tire-001),
  [Tire Health advisory request (`IF-TIRE-002`)](#if-tire-002),
  [KUKSA advisory target (`IF-ADV-002`)](#if-adv-002),
  [outbound VISS Set (`IF-ADV-003`)](#if-adv-003),
  [platform FOTA artifact (`IF-LC-001`)](#if-lc-001), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001),
  [versioned v1 signal contract (`SYS-VDP-002`)](system-requirements-and-traceability.md#sys-vdp-002),
  [backward-compatible v2 capability (`SYS-VDP-003`)](system-requirements-and-traceability.md#sys-vdp-003),
  [allowlisted outbound advisory (`SYS-VDP-004`)](system-requirements-and-traceability.md#sys-vdp-004),
  [explicit degraded data (`SYS-VDP-005`)](system-requirements-and-traceability.md#sys-vdp-005),
  [existing Tire Health platform contract (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [offline Tire Health inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [authorization-adapter migration (`SYS-SEC-002`)](system-requirements-and-traceability.md#sys-sec-002), and
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003).

### `CR-BHS` — Brake Health in-vehicle service

- Component: [Brake Health In-Vehicle Service (`CMP-BHS`)](#cmp-bhs).
- Interfaces: [Brake Health data subscription (`IF-DATA-002`)](#if-data-002),
  [advisory request (`IF-ADV-001`)](#if-adv-001),
  [functional report (`IF-FUNC-001`)](#if-func-001),
  [Brake Health SOTA artifact (`IF-LC-002`)](#if-lc-002), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [bounded v1 functional report (`SYS-BHS-001`)](system-requirements-and-traceability.md#sys-bhs-001),
  [deterministic v2 inference (`SYS-BHS-002`)](system-requirements-and-traceability.md#sys-bhs-002),
  [allowlisted v3 advisory (`SYS-BHS-003`)](system-requirements-and-traceability.md#sys-bhs-003),
  [offline local continuity (`SYS-BHS-004`)](system-requirements-and-traceability.md#sys-bhs-004), and
  [separate local and Cloud latency (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-TIRE` — Tire Health in-vehicle service

- Component: [Tire Health In-Vehicle Service (`CMP-TIRE`)](#cmp-tire).
- Interfaces: [dynamics subscription (`IF-TIRE-001`)](#if-tire-001),
  [typed inspection advisory (`IF-TIRE-002`)](#if-tire-002),
  [bounded condition result (`IF-TIRE-003`)](#if-tire-003),
  [Tire Health SOTA artifact (`IF-LC-007`)](#if-lc-007), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [existing platform contract only (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [local persistent condition estimate (`SYS-TIRE-002`)](system-requirements-and-traceability.md#sys-tire-002),
  [explicit simulation model (`SYS-TIRE-003`)](system-requirements-and-traceability.md#sys-tire-003),
  [bounded Cloud reporting (`SYS-TIRE-004`)](system-requirements-and-traceability.md#sys-tire-004),
  [independent Tire Health product (`SYS-TIRE-005`)](system-requirements-and-traceability.md#sys-tire-005), and
  [offline inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006).

### `CR-AOS` — AosCore and AosCloud lifecycle

- Components: [AosCore and Service Manager (`CMP-AOS-CORE`)](#cmp-aos-core),
  [AosCloud Lifecycle Authority (`CMP-AOS-CLOUD`)](#cmp-aos-cloud), and
  [AosEdge Log Pipeline (`CMP-LOG-PIPE`)](#cmp-log-pipe).
- Interfaces: [platform FOTA (`IF-LC-001`)](#if-lc-001),
  [Brake Health SOTA (`IF-LC-002`)](#if-lc-002),
  [Tire Health SOTA (`IF-LC-007`)](#if-lc-007),
  [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006),
  [vehicle log collection (`IF-OBS-001`)](#if-obs-001), and
  [ELK delivery (`IF-OBS-002`)](#if-obs-002).
- Parent requirements: [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [prove current Unit state (`SYS-ID-003`)](system-requirements-and-traceability.md#sys-id-003),
  [qualify identity retirement (`SYS-ID-004`)](system-requirements-and-traceability.md#sys-id-004),
  [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [current effective-target validation (`SYS-REL-002`)](system-requirements-and-traceability.md#sys-rel-002),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [native Cloud dependency rejection (`SYS-REL-006`)](system-requirements-and-traceability.md#sys-rel-006),
  [Cloud-authoritative delivery dashboard (`SYS-OBS-002`)](system-requirements-and-traceability.md#sys-obs-002),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [lifecycle timing bounds (`SYS-TIM-001`)](system-requirements-and-traceability.md#sys-tim-001), and
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001).

[Native Cloud dependency rejection (`SYS-REL-006`)](system-requirements-and-traceability.md#sys-rel-006)
remains deferred and is allocated only to
[Aos lifecycle (`CR-AOS`)](#cr-aos); it is not a requirement on the Software
Delivery Dashboard.

### `CR-BRAKE-CLOUD` — Brake Health Cloud product

- Components: [Brake Health Backend (`CMP-BRAKE-BE`)](#cmp-brake-be) and
  [Brake Health Function Dashboard (`CMP-BRAKE-DASH`)](#cmp-brake-dash).
- Interfaces: [functional report (`IF-FUNC-001`)](#if-func-001) and
  [dashboard query API (`IF-FUNC-002`)](#if-func-002).
- Parent requirements: [bounded v1 functional report (`SYS-BHS-001`)](system-requirements-and-traceability.md#sys-bhs-001),
  [offline local continuity (`SYS-BHS-004`)](system-requirements-and-traceability.md#sys-bhs-004),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004), and
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002).

### `CR-TIRE-CLOUD` — Tire Health Cloud product

- Components: [Tire Health Backend (`CMP-TIRE-BE`)](#cmp-tire-be)
  and [Tire Health Function Dashboard (`CMP-TIRE-DASH`)](#cmp-tire-dash).
- Interfaces: [bounded condition result (`IF-TIRE-003`)](#if-tire-003) and
  [Tire Health dashboard API (`IF-TIRE-004`)](#if-tire-004).
- Parent requirements: [bounded Cloud reporting (`SYS-TIRE-004`)](system-requirements-and-traceability.md#sys-tire-004),
  [independent Tire Health product (`SYS-TIRE-005`)](system-requirements-and-traceability.md#sys-tire-005),
  [offline inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004), and
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002).

### `CR-DEMO` — Demonstration orchestration and delivery view

- Components: [Software Delivery Dashboard (`CMP-SW-DASH`)](#cmp-sw-dash),
  [Demo Orchestrator (`CMP-ORCH`)](#cmp-orch), and
  [Vehicle and Service Log View (`CMP-ELK`)](#cmp-elk).
- Interfaces: [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [ELK delivery (`IF-OBS-002`)](#if-obs-002), and
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001).
- Parent requirements: [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [prove current Unit state (`SYS-ID-003`)](system-requirements-and-traceability.md#sys-id-003),
  [exact source-to-Unit binding (`SYS-SRC-001`)](system-requirements-and-traceability.md#sys-src-001),
  [honest single-source presentation (`SYS-SRC-002`)](system-requirements-and-traceability.md#sys-src-002),
  [current effective-target validation (`SYS-REL-002`)](system-requirements-and-traceability.md#sys-rel-002),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [Cloud-authoritative delivery dashboard (`SYS-OBS-002`)](system-requirements-and-traceability.md#sys-obs-002),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [lifecycle timing bounds (`SYS-TIM-001`)](system-requirements-and-traceability.md#sys-tim-001),
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001),
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002),
  [reset CARLA and preserve factory (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003), and
  [no rollback or fleet claim (`SYS-RET-004`)](system-requirements-and-traceability.md#sys-ret-004).

### `CR-CROSS` — Cross-cutting security and operations

- Component focus: all components plus the future
  [Aos-to-KUKSA Authorization Adapter (`CMP-KUKSA-AUTH`)](#cmp-kuksa-auth).
- Interface focus: every trust, resource, timing, log and offline boundary.
- Parent requirements: [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [authorization-adapter migration (`SYS-SEC-002`)](system-requirements-and-traceability.md#sys-sec-002),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [lifecycle timing bounds (`SYS-TIM-001`)](system-requirements-and-traceability.md#sys-tim-001), and
  [separate local and Cloud latency (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-E2E` — End-to-end acceptance

- Component and interface focus: the complete accepted graph on Validation and
  Demonstration Units.
- Parent requirements: every accepted System Requirement and every relevant
  Architecture Flow. The package proves integration; it does not replace the
  more specific allocations above.

## Boundary Decision Status

1. **Accepted 2026-08-18:** logical components, repositories, immutable
   deployable artifacts and runtime deployments are separate concepts.
   `CMP-FACTORY` is the build-time OEM Factory Baseline Assembly, the OEM Demo
   Factory Image is its artifact, and `VU`/`DU` are deployments created from
   that artifact.
2. **Accepted 2026-08-18:** the existing `carla-ego-runtime` repository owns
   deterministic scenario tooling, vehicle control, Gateway behavior, VISS,
   advisory handling and the Engineering Telematics Dashboard.
3. **Accepted 2026-08-18:** Function Team 2 owns the Tire Health product
   selected by ADR 0008. Its in-vehicle SOTA 2 source belongs in the future
   `tire-health-service` repository; backend and dashboard remain separate
   Cloud-product components.
4. **Open:** decide whether each functional backend and dashboard share one
   Cloud-product repository. The recommendation is one repository per Function
   Team Cloud product, separate from its in-vehicle SOTA repository.
5. **Open:** confirm that `CMP-SW-DASH` and `CMP-ORCH` remain solution
   components in `aosedge-sdv-demo` rather than becoming lifecycle authorities.
6. **Open:** decide where deployment-specific `CMP-LOG-PIPE` to `CMP-ELK`
   configuration is owned after the actual AosEdge logging topology is
   qualified.
7. **Open:** confirm that `CMP-KUKSA-AUTH` remains an explicit deferred
   production hardening component rather than being hidden inside prototype
   token files.

## Acceptance Gate for Version 0.2

The register is ready to become the component baseline when reviewers confirm:

1. every HLA 1.2 box has exactly one primary component owner;
2. every audience-visible dashboard has exactly one authoritative data source;
3. the three independent FOTA/SOTA lifecycles remain separated;
4. Function Team 1 and Function Team 2 are peer product domains;
5. `VU` and `DU` remain runtime roles rather than duplicated component sets;
6. current, engineering-evidence, target, external and deferred states are not
   presented as equivalent;
7. all runtime, functional Cloud, lifecycle and observability boundaries needed
   by Scenario 1.2 and the Function Team 2 extension have interface IDs;
8. deferred native Cloud dependency admission and authorization-adapter work
   are not presented as implemented;
9. no component claims a production driver HMI, continuous raw-telemetry Cloud
   stream, third-party Service Provider, Fleet Operator or production fleet;
10. the provisional requirement packages can be expanded without changing HLA
    1.2 or the accepted demo scenarios.

After acceptance, component requirements shall be written package by package,
starting with [Vehicle simulation (`CR-VEHICLE-SIM`)](#cr-vehicle-sim) and
[Vehicle Gateway (`CR-GATEWAY`)](#cr-gateway). Each requirement shall cite a
named and linked parent System Requirement, Architecture Flow and interface,
plus a verification method and retained evidence. Implementation planning
begins only after the relevant package and acceptance tests are reviewed.
