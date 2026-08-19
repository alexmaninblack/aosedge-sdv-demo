<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Decomposition and Interface Register 0.6

- Status: Accepted component baseline
- Version: 0.6
- Prepared: 2026-08-19
- Accepted: 2026-08-19
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.3](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 1.4](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 1.3](../architecture/demo-scenario-architecture-flows.md)
- Requirements input: [System Requirements and Traceability 0.6](system-requirements-and-traceability.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md)
  and [ADR 0010](../architecture/decisions/0010-aos-kuksa-credential-broker.md)
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

1. High-Level Architecture 1.3 owns system boundaries, authorities and
   invariants.
2. Demo Scenario 1.4 owns the audience-visible lifecycle and stage sequence.
3. Architecture Flows 1.3 owns detailed runtime, lifecycle, observability and
   failure flows.
4. System Requirements 0.6 owns normative `SYS-*` obligations and gap
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

The Vehicle Data Platform Component is one logical platform component delivered
in independently versioned FOTA artifacts. It owns the inbound/outbound
providers, versioned KUKSA contract/configuration, thin Aos–KUKSA Credential
Broker, and provider platform-credential integration. Aos Service Manager and
IAM retain the SOTA identity, secret and registered-permission lifecycle; no
parallel project-owned identity or per-service policy store is added. Brake
Health and Tire Health are
two peer functional components delivered in separate SOTA lifecycles. Version
changes do not create new logical components.

The `OEM Factory Baseline Assembly` is a build-time logical component. It
reproducibly produces the immutable `OEM Demo Factory Image` artifact. That
artifact contains the factory-installed runtime graph and is the source for
fresh Validation and Demonstration Unit deployments; the artifact is not
itself a `CMP-*` component.

The same pinned assembly may also produce a rootfs platform-update envelope.
That envelope targets the AosVM rootfs A/B runtime for retrofit or later
platform maintenance of an already manufactured Unit. It is not the Factory
Image and it is not the independently delivered Vehicle Data Platform
Component. In the normal manufacturing flow, the empty-slot runtime is already
present in the Factory Image before provisioning.

### Dashboard is not authority

Every dashboard is a presentation surface over one authoritative source:

| Dashboard | Authoritative source |
| --- | --- |
| Engineering Telematics Dashboard | Vehicle Gateway VISS endpoint |
| OEM Software Delivery Dashboard | AosCloud lifecycle and native log APIs plus current Unit state |
| Brake Health Function Dashboard | Function Team 1 backend |
| Tire Health Function Dashboard | Function Team 2 backend |

No dashboard becomes an alternate desired-state database, vehicle-data broker,
functional backend, or vehicle-control path.

### Release decision is not Cloud execution

The Platform Team and each Function Team own their engineering release
decisions. A Function Team uses its Service Provider identity to publish and
technically verify a service artifact, but an approval affecting OEM Units is
recorded with an authorized OEM identity. AosCloud stores and executes the
resulting lifecycle transition. The Software Delivery Dashboard and Demo
Orchestrator may facilitate that interaction, but they own neither the decision
nor authoritative lifecycle state.

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
| <a id="cmp-carla"></a>`CMP-CARLA` | CARLA Virtual Physical Vehicle | Vehicle dynamics, road environment, versioned installed-hardware capability manifest, native sensor state and actuators | Vehicle simulation | `CarlaSim`; restricted Unreal dependency remains separate | Native behavior `CURRENT`; accepted manifest `EXTEND` |
| <a id="cmp-scene"></a>`CMP-SCENE` | Deterministic Scenario Controller | Repeatable obstacle/braking stimulus, explicit free-drive/brake-event context, context-aware mode transition/reset, actor cleanup, and accelerated/pre-aged tire-degradation stimulus | Demo vehicle tooling | `carla-ego-runtime` | Brake scenario core `CURRENT`; complete context matrix and Tire Health stimulus `EXTEND` |
| <a id="cmp-control"></a>`CMP-CONTROL` | Vehicle Control UI | Manual/autopilot selection, throttle, brake, steering and safe-stop commands over the separate control channel | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT` |
| <a id="cmp-gw"></a>`CMP-GW` | Vehicle Gateway Runtime | Complete CARLA hardware-profile accounting, control arbitration, applied-control feedback, signal normalization and Gateway health/state | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / EXTEND` |
| <a id="cmp-viss"></a>`CMP-VISS` | Vehicle Gateway VISS 3.1 Server | TLS-protected VSS Get/Subscribe and the future narrowly scoped advisory Set contract | Vehicle Gateway tooling | `carla-ego-runtime` | Read path `CURRENT`; write path `EXTEND` |
| <a id="cmp-gw-adv"></a>`CMP-GW-ADV` | Gateway Advisory Handler | Validate typed allowlisted Brake Health and Tire Health advisory targets and publish factual reception/status without claiming driver display | Vehicle Gateway tooling | `carla-ego-runtime` | `NEW` |
| <a id="cmp-eng-dash"></a>`CMP-ENG-DASH` | Engineering Telematics Dashboard | Independent read-only engineering view of Gateway telemetry, drive-mode/world-context/reset facts and typed advisory/status evidence | Demo engineering tooling | `carla-ego-runtime` | Telemetry `CURRENT`; transition and advisory/status `EXTEND` |

`CMP-SCENE`, `CMP-CONTROL`, and `CMP-ENG-DASH` are demonstration tools. They
must remain outside the logical production vehicle architecture even though
they interact with its simulated boundaries.

### Domain Controller substrate and Vehicle Data Platform

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-factory"></a>`CMP-FACTORY` | OEM Factory Baseline Assembly | Reproducibly compose, build, qualify and freeze the unprovisioned SOP substrate, including enabled stock Aos IAM permission handling and the non-secret IAM/PKCS#11 signing-key integration seam | Platform Team; pre-SOP manufacturing/build lifecycle | Integration recipes and qualification inputs in `aos-vehicle-platform`; output image remains outside Git | Build evidence `EVIDENCE`; accepted assembly process and output artifact `NEW` |
| <a id="cmp-runtime"></a>`CMP-RUNTIME` | Provider-Specific Empty-Slot Runtime | Preinstalled Service Manager runtime, bounded provider slot, health and storage boundary for the Vehicle Data Platform payload | Platform Team; factory image | `aos-vehicle-platform` | `EVIDENCE`; final factory qualification required |
| <a id="cmp-aos-core"></a>`CMP-AOS-CORE` | AosCore and Service Manager | Unit identity, desired state, security, update lifecycle, service execution and status | AosEdge platform | External AosVM/AosCore release | `EXTERNAL / CURRENT` |
| <a id="cmp-kuksa"></a>`CMP-KUKSA` | Eclipse KUKSA Databroker | Stable in-vehicle service-facing VSS data boundary and verification of broker-issued JWTs using a configured public key | External Eclipse component in the SOP substrate; Platform Team governs integration and exposed contract | Unmodified external executable; configuration/contract in `aos-vehicle-platform` | Executable `CURRENT`; final contract/trust integration `EXTEND` |
| <a id="cmp-vdp"></a>`CMP-VDP` | Vehicle Data Platform Component | Privileged VISS client, signal selection, validation, normalization, KUKSA actual-value publication, versioned contract, allowlisted outbound advisory path, thin Aos–KUKSA Credential Broker, and separate provider platform-credential integration | Platform Team; independent FOTA | `aos-vehicle-platform` | Inbound `EVIDENCE`; accepted v1-v3 graph and credential flow `EXTEND` |

`CMP-RUNTIME` is provider-specific and hosts one bounded component type. This
register makes no claim that the current runtime is a generic arbitrary
component runtime.

### Function Team 1 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-bhs"></a>`CMP-BHS` | Brake Health In-Vehicle Service | Read the accepted KUKSA contract, perform local analysis, retain bounded reports and request the allowlisted advisory | Function Team 1 / Service Provider 1; SOTA 1 | `brake-health-service` | Scaffold `CURRENT`; product behavior `NEW` |
| <a id="cmp-brake-be"></a>`CMP-BRAKE-BE` | Brake Health Backend | Idempotent report ingestion, persistence and API for functional results | Function Team 1; functional Cloud product | Planned `brake-health-cloud` | `NEW` |
| <a id="cmp-brake-dash"></a>`CMP-BRAKE-DASH` | Brake Health Function Dashboard | Present Brake Health inputs, local result, service/capability versions and online/offline delivery state from the backend | Function Team 1; functional Cloud product | Planned `brake-health-cloud` | `NEW` |

The backend and dashboard are not part of the in-vehicle SOTA artifact and do
not participate in the time-critical local advisory decision.

### Function Team 2 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-tire"></a>`CMP-TIRE` | Tire Health In-Vehicle Service | Maintain a bounded persistent tire-condition estimate from the accepted KUKSA contract, create bounded reports/events, and request the typed inspection advisory | Function Team 2 / Service Provider 2; SOTA 2 | Proposed `tire-health-service` | `NEW` |
| <a id="cmp-tire-be"></a>`CMP-TIRE-BE` | Tire Health Backend | Idempotent condition-summary/event ingestion, persistence and API | Function Team 2; functional Cloud product | Planned `tire-health-cloud` | `NEW` |
| <a id="cmp-tire-dash"></a>`CMP-TIRE-DASH` | Tire Health Function Dashboard | Present condition band, event state, service/capability version, Unit role and delivery status from the Tire Health backend | Function Team 2; functional Cloud product | Planned `tire-health-cloud` | `NEW` |

Function Team 2 is a peer of Function Team 1. Its service, backend, dashboard,
identity and SOTA lifecycle must not be placed inside the Brake Health product
or routed through it.

### Software delivery, operations and demo domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-aos-cloud"></a>`CMP-AOS-CLOUD` | AosCloud Lifecycle Control Plane | Provisioning, authoritative Unit/Node desired and reported actual state, batches, campaigns, recorded approvals, audit history, FOTA/SOTA delivery and promotion execution | AosEdge platform / OEM Cloud | External AosCloud service | `EXTERNAL / CURRENT`; exact demo operations require qualification |
| <a id="cmp-sw-dash"></a>`CMP-SW-DASH` | OEM Software Delivery Dashboard | Stateless presentation of current AosCloud lifecycle state, native system/service/crash-log requests and results, qualification evidence, business decision owner and active Cloud role; invoke only explicitly confirmed OEM-authorized actions | Demo solution | `aosedge-sdv-demo` | `NEW` |
| <a id="cmp-orch"></a>`CMP-ORCH` | Demo Orchestrator | Factory-overlay creation, role binding, provisioning reconciliation, CARLA source selection/replay, release sequencing, transient evidence correlation, retirement and reset without owning lifecycle state or approval decisions | Demo solution | `aosedge-sdv-demo` | Existing helpers `EVIDENCE`; unified orchestrator `NEW` |

The native future AosCloud SOTA-to-FOTA dependency-admission capability is a
deferred feature of `CMP-AOS-CLOUD`, not a new project component. In
particular, `CMP-SW-DASH` must not implement a temporary admission controller.

## Runtime Roles and Deployable Products

| Item | Kind | Component graph or payload | Lifecycle |
| --- | --- | --- | --- |
| Validation Unit (`VU`) | Runtime role/deployment | One fresh deployment created from the accepted OEM Demo Factory Image; runs `CMP-RUNTIME`, `CMP-AOS-CORE`, `CMP-KUKSA` and stage-selected payloads | Per demo run |
| Demonstration Unit (`DU`) | Runtime role/deployment | A separate fresh deployment created from the same accepted image and running the same stage-selected component graph | Per demo run |
| OEM Demo Factory Image | Immutable product artifact | Produced by `CMP-FACTORY`; contains `CMP-RUNTIME`, `CMP-AOS-CORE` and `CMP-KUKSA`, without feature payloads or reusable vehicle identity | Manufacturing baseline |
| Rootfs platform-update envelope | FOTA artifact family | Optional complete rootfs payload containing a later or retrofit Platform Team baseline; targets the factory-installed AosVM rootfs A/B runtime | Platform Team rootfs FOTA; not part of normal M0-M1 |
| Vehicle Data Platform Component v1-v3 | FOTA artifact family | `CMP-VDP` | Platform Team FOTA |
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
| `aos-vehicle-platform` | `CMP-FACTORY` assembly source, `CMP-RUNTIME`, `CMP-VDP` including the thin Credential Broker and provider platform-credential integration, and `CMP-KUKSA` contract/trust configuration | Platform Team source and FOTA boundary; immutable Factory Image output remains outside Git. |
| `brake-health-service` | `CMP-BHS` | Function Team 1 in-vehicle SOTA source only. |
| Proposed `tire-health-service` | `CMP-TIRE` | Function Team 2 in-vehicle SOTA source only; repository not yet created. |
| Planned `brake-health-cloud` | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | One Function Team 1 Cloud-product repository, separate from the in-vehicle SOTA source; repository not yet created. |
| Planned `tire-health-cloud` | `CMP-TIRE-BE`, `CMP-TIRE-DASH` | One Function Team 2 Cloud-product repository, separate from the in-vehicle SOTA source; repository not yet created. |
| `aosedge-sdv-demo` | `CMP-SW-DASH`, `CMP-ORCH`, cross-component contracts, qualification and system documentation | Solution integration; must not absorb component product source. |
| AosEdge/AosCloud | `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, including native system/service/crash-log collection, Cloud delivery and storage | External platform dependency. |

No repository is created, renamed or added to `workspace/repositories.json` by
acceptance of this baseline.

## Runtime Data Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-veh-001"></a>`IF-VEH-001` | `CMP-CARLA` | `CMP-GW` | Vehicle Hardware Capability Manifest plus frame-coherent state and availability for every installed hardware-equivalent signal/sensor; excludes qualification-only ground truth | CARLA runtime state and accepted hardware profile | Existing subset `CURRENT`; complete manifest/accounting `EXTEND` |
| <a id="if-veh-002"></a>`IF-VEH-002` | `CMP-CONTROL` | `CMP-GW` | Authenticated manual/autopilot/safe-stop control request | Gateway control state | `CURRENT` |
| <a id="if-veh-003"></a>`IF-VEH-003` | `CMP-GW` | `CMP-CARLA` | Commands for every actuator declared in the selected hardware profile, with accepted/rejected execution status and applied-control state returning through `IF-VEH-001` | Gateway control arbitration; CARLA applied state | Throttle/brake/steer `CURRENT`; complete declared set/status `EXTEND` |
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
| <a id="if-auth-001"></a>`IF-AUTH-001` | `CMP-BHS` / `CMP-TIRE` | `CMP-VDP` Credential Broker | Local credential request using the per-instance `AOS_SECRET`; no reusable KUKSA token in the service artifact | Running Aos service identity | `NEW` |
| <a id="if-auth-002"></a>`IF-AUTH-002` | `CMP-VDP` Credential Broker | `CMP-AOS-CORE` IAM | `GetPermissions(secret, "kuksa")` request and authenticated service identity plus declared path/mode response | Aos IAM registration made by Service Manager | `EXTERNAL / EXTEND` qualification |
| <a id="if-auth-003"></a>`IF-AUTH-003` | `CMP-VDP` Credential Broker | `CMP-BHS` / `CMP-TIRE` | Rejection or short-lived, path-scoped KUKSA JWT that exactly maps the currently registered IAM permissions and installed VDP contract | Aos IAM result plus VDP contract; no parallel service policy store | `NEW` |
| <a id="if-auth-004"></a>`IF-AUTH-004` | `CMP-VDP` | `CMP-KUKSA` | Public verifier, audience and trust configuration for broker-issued JWTs; private signing material remains per-Unit platform state protected through IAM/certificate-module and PKCS#11 integration | Platform trust configuration | `EXTEND` |
| <a id="if-auth-005"></a>`IF-AUTH-005` | `CMP-AOS-CORE` / factory security substrate | `CMP-VDP` Credential Broker | Enabled permission-handler availability and access to a per-Unit platform-protected signing operation; no signing key bytes cross into the component artifact | Aos IAM/certificate-module and PKCS#11 integration | `NEW / QUALIFY` |
| <a id="if-auth-006"></a>`IF-AUTH-006` | `CMP-AOS-CORE` / platform identity facility | privileged provider inside `CMP-VDP` | Short-lived provider credential limited to accepted KUKSA `provide`/`create` paths | Separate FOTA-component identity binding; exact mechanism unresolved | `NEW / DESIGN GATE` |

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
| <a id="if-lc-002"></a>`IF-LC-002` | Function Team 1 Service Provider pipeline | `CMP-AOS-CLOUD` | Publish and technically verify immutable Brake Health SOTA artifact and compatibility metadata | Service Provider 1 identity; no OEM Unit deployment approval | `NEW / QUALIFY` |
| <a id="if-lc-007"></a>`IF-LC-007` | Function Team 2 Service Provider pipeline | `CMP-AOS-CLOUD` | Publish and technically verify immutable Tire Health SOTA artifact and compatibility metadata | Service Provider 2 identity; no OEM Unit deployment approval | `NEW / QUALIFY` |
| <a id="if-lc-008"></a>`IF-LC-008` | Platform Team release owner | `CMP-AOS-CLOUD` | Explicit FOTA validation acceptance and deployment or promotion approval for exact artifact, digest and target | Platform Team decision through authorized OEM identity | `NEW / QUALIFY` |
| <a id="if-lc-009"></a>`IF-LC-009` | Function Team 1 release owner | `CMP-AOS-CLOUD` | Explicit Brake Health validation acceptance and deployment or promotion approval for exact service, integration evidence and target | Function Team 1 decision through authorized OEM identity | `NEW / QUALIFY` |
| <a id="if-lc-010"></a>`IF-LC-010` | Function Team 2 release owner | `CMP-AOS-CLOUD` | Explicit Tire Health validation acceptance and deployment or promotion approval for exact service, integration evidence and target | Function Team 2 decision through authorized OEM identity | `NEW / QUALIFY` |
| <a id="if-lc-004"></a>`IF-LC-004` | `CMP-AOS-CLOUD` | `CMP-AOS-CORE` | Provisioning, desired state, update delivery, validation, status and retirement | AosCloud and current Unit state | `EXTERNAL / EXTEND` qualification |
| <a id="if-lc-005"></a>`IF-LC-005` | `CMP-SW-DASH` | `CMP-AOS-CLOUD` | Scoped API reads, effective-target preview, owner/role display and explicitly confirmed calls using the correct OEM identity | AosCloud; dashboard holds no parallel desired state or approval policy | `NEW` |
| <a id="if-lc-006"></a>`IF-LC-006` | `CMP-AOS-CORE` | `CMP-RUNTIME` / `CMP-BHS` / `CMP-TIRE` | Install, start, stop, update, rollback, readiness and resource enforcement | Unit actual state | Platform mechanism `CURRENT`; target graph `EXTEND` |
| <a id="if-obs-001"></a>`IF-OBS-001` | `CMP-SW-DASH` / `CMP-AOS-CLOUD` | `CMP-AOS-CLOUD` / `CMP-SW-DASH` | Explicit operator request plus authoritative system, service-instance or crash-log status/result through supported AosCloud APIs; dashboard keeps no independent archive | AosCloud request and stored-log state | Native platform path `EXTERNAL / CURRENT`; dashboard presentation `NEW / QUALIFY` |
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
| <a id="cr-vehicle-sim"></a>`CR-VEHICLE-SIM` | Define the installed Vehicle Hardware Capability Manifest, provide every declared physical signal/actuator behavior, repeatable braking and tire stimuli, exact source evidence, hidden ground-truth isolation and clean CARLA scenario reset. | CARLA vehicle and Scenario Controller | Hardware-profile completeness, determinism, source integrity, simulation truth and reset |
| <a id="cr-gateway"></a>`CR-GATEWAY` | Account for the complete hardware profile, distinguish actuator capability from authority, acquire and normalize vehicle state, expose VISS, arbitrate control, handle bounded advisory status and present the engineering view. | Control UI, Gateway, VISS, Advisory Handler and Engineering Dashboard | Hardware coverage, telemetry contract, unavailable data, control traceability, advisory safety and latency |
| <a id="cr-factory"></a>`CR-FACTORY` | Reproducibly assemble and preserve the clean unprovisioned Factory Image artifact, enable stock Aos IAM permission handling and its non-secret PKCS#11 seam, and create two identity-safe deployments with a healthy empty capability slot. | Factory Baseline Assembly and Empty-Slot Runtime | Reproducibility, artifact immutability, IAM substrate, identity/key absence, overlay uniqueness and preservation |
| <a id="cr-vdp"></a>`CR-VDP` | Deliver the versioned VISS-to-KUKSA data capability, narrowly allowlisted outbound advisory path, and least-privilege short-lived KUKSA credentials derived from native Aos identity. | KUKSA and Vehicle Data Platform Component | Compatibility, data quality, thin credential translation, provider identity, FOTA and rollback |
| <a id="cr-bhs"></a>`CR-BHS` | Run Brake Health analysis locally, report bounded results, operate offline and request only the approved advisory. | Brake Health In-Vehicle Service | Model determinism, reports, compatibility, offline operation and advisory scope |
| <a id="cr-tire"></a>`CR-TIRE` | Estimate tire condition locally, persist bounded state, upload bounded results and request the typed inspection advisory through an independent SOTA lifecycle. | Tire Health In-Vehicle Service | Existing signal contract, model, persistence, bounded reporting, advisory and isolation |
| <a id="cr-aos"></a>`CR-AOS` | Provide identity, authoritative desired/reported actual state, recorded owner approvals, FOTA/SOTA execution, dependency behavior, resource enforcement and native operational-log collection/delivery. | AosCore and AosCloud | Provisioning, lifecycle state and execution, OEM-authorized validation, rollback, native logging, timing and retirement |
| <a id="cr-brake-cloud"></a>`CR-BRAKE-CLOUD` | Ingest and present Brake Health reports without entering the local decision path. | Brake Health Backend and Function Dashboard | Idempotency, offline synchronization, evidence and run-data retention |
| <a id="cr-tire-cloud"></a>`CR-TIRE-CLOUD` | Ingest and present Tire Health summaries/events as an independent Function Team product. | Tire Health Backend and Function Dashboard | Bounded results, idempotency, delivery state and run-data retention |
| <a id="cr-demo"></a>`CR-DEMO` | Orchestrate manufactured overlays, Unit roles, staged releases, authoritative dashboards, evidence and end-of-run retirement. | Software Delivery Dashboard and Demo Orchestrator | Target safety, source binding, native-log presentation, observability, timing and reset |
| <a id="cr-cross"></a>`CR-CROSS` | Define security, authorization, redaction, timing, resource and offline constraints shared by multiple owners. | Cross-component concerns; the Credential Broker itself remains allocated to `CMP-VDP` | Least privilege, fail-closed behavior, evidence controls and latency |
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
  [versioned vehicle hardware profile (`SYS-SRC-003`)](system-requirements-and-traceability.md#sys-src-003),
  [complete Simulator–Gateway accounting (`SYS-SRC-004`)](system-requirements-and-traceability.md#sys-src-004),
  [continuous control-mode handover (`SYS-CTRL-002`)](system-requirements-and-traceability.md#sys-ctrl-002),
  [deterministic mode/context transition (`SYS-CTRL-003`)](system-requirements-and-traceability.md#sys-ctrl-003),
  [deterministic v2 inference (`SYS-BHS-002`)](system-requirements-and-traceability.md#sys-bhs-002),
  [explicit Tire Health simulation model (`SYS-TIRE-003`)](system-requirements-and-traceability.md#sys-tire-003),
  [truthful control-transition evidence (`SYS-OBS-005`)](system-requirements-and-traceability.md#sys-obs-005), and
  [reset vehicle simulation state (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003).

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
  [versioned vehicle hardware profile (`SYS-SRC-003`)](system-requirements-and-traceability.md#sys-src-003),
  [complete Simulator–Gateway accounting (`SYS-SRC-004`)](system-requirements-and-traceability.md#sys-src-004),
  [fail-safe exclusive vehicle control (`SYS-CTRL-001`)](system-requirements-and-traceability.md#sys-ctrl-001),
  [continuous control-mode handover (`SYS-CTRL-002`)](system-requirements-and-traceability.md#sys-ctrl-002),
  [deterministic mode/context transition (`SYS-CTRL-003`)](system-requirements-and-traceability.md#sys-ctrl-003),
  [allowlisted outbound advisory (`SYS-VDP-004`)](system-requirements-and-traceability.md#sys-vdp-004),
  [explicit degraded data (`SYS-VDP-005`)](system-requirements-and-traceability.md#sys-vdp-005),
  [allowlisted v3 advisory (`SYS-BHS-003`)](system-requirements-and-traceability.md#sys-bhs-003),
  [offline Tire Health inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [truthful control-transition evidence (`SYS-OBS-005`)](system-requirements-and-traceability.md#sys-obs-005), and
  [separate local and Cloud latency (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-FACTORY` — Factory assembly, artifact and empty slot

- Components: [OEM Factory Baseline Assembly (`CMP-FACTORY`)](#cmp-factory) and
  [Provider-Specific Empty-Slot Runtime (`CMP-RUNTIME`)](#cmp-runtime).
- Produced artifact: immutable `OEM Demo Factory Image`, from which separate
  Validation and Demonstration Unit runtime deployments are created.
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006),
  [broker IAM/PKCS#11 substrate (`IF-AUTH-005`)](#if-auth-005), and
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001).
- Parent requirements: [reproducible factory image (`SYS-MFG-001`)](system-requirements-and-traceability.md#sys-mfg-001),
  [clean SOP substrate (`SYS-MFG-002`)](system-requirements-and-traceability.md#sys-mfg-002),
  [unique fresh overlays (`SYS-MFG-003`)](system-requirements-and-traceability.md#sys-mfg-003),
  [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001), and
  [preserve immutable factory artifact (`SYS-RET-005`)](system-requirements-and-traceability.md#sys-ret-005).

### `CR-VDP` — Vehicle Data Platform Component

- Components: [KUKSA Databroker (`CMP-KUKSA`)](#cmp-kuksa) and
  [Vehicle Data Platform Component (`CMP-VDP`)](#cmp-vdp).
- Interfaces: [VISS telemetry input (`IF-VEH-005`)](#if-veh-005),
  [KUKSA publication (`IF-DATA-001`)](#if-data-001),
  [Brake Health subscription (`IF-DATA-002`)](#if-data-002),
  [Tire Health subscription (`IF-TIRE-001`)](#if-tire-001),
  [Tire Health advisory request (`IF-TIRE-002`)](#if-tire-002),
  [KUKSA advisory target (`IF-ADV-002`)](#if-adv-002),
  [outbound VISS Set (`IF-ADV-003`)](#if-adv-003),
  [service credential request (`IF-AUTH-001`)](#if-auth-001),
  [Aos IAM permission lookup (`IF-AUTH-002`)](#if-auth-002),
  [short-lived JWT or rejection (`IF-AUTH-003`)](#if-auth-003),
  [KUKSA verifier configuration (`IF-AUTH-004`)](#if-auth-004),
  [broker IAM/PKCS#11 substrate (`IF-AUTH-005`)](#if-auth-005),
  [provider platform credential (`IF-AUTH-006`)](#if-auth-006),
  [platform FOTA artifact (`IF-LC-001`)](#if-lc-001),
  [Platform Team OEM-authorized approval (`IF-LC-008`)](#if-lc-008), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [combined-graph owner gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001),
  [versioned v1 signal contract (`SYS-VDP-002`)](system-requirements-and-traceability.md#sys-vdp-002),
  [backward-compatible v2 capability (`SYS-VDP-003`)](system-requirements-and-traceability.md#sys-vdp-003),
  [allowlisted outbound advisory (`SYS-VDP-004`)](system-requirements-and-traceability.md#sys-vdp-004),
  [explicit degraded data (`SYS-VDP-005`)](system-requirements-and-traceability.md#sys-vdp-005),
  [existing Tire Health platform contract (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [offline Tire Health inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [native-IAM-derived SOTA KUKSA credentials (`SYS-SEC-006`)](system-requirements-and-traceability.md#sys-sec-006),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [KUKSA verifier and token lifetime (`SYS-SEC-004`)](system-requirements-and-traceability.md#sys-sec-004), and
  [separate provider authority (`SYS-SEC-005`)](system-requirements-and-traceability.md#sys-sec-005).

### `CR-BHS` — Brake Health in-vehicle service

- Component: [Brake Health In-Vehicle Service (`CMP-BHS`)](#cmp-bhs).
- Interfaces: [Brake Health data subscription (`IF-DATA-002`)](#if-data-002),
  [advisory request (`IF-ADV-001`)](#if-adv-001),
  [credential request (`IF-AUTH-001`)](#if-auth-001),
  [short-lived JWT or rejection (`IF-AUTH-003`)](#if-auth-003),
  [functional report (`IF-FUNC-001`)](#if-func-001),
  [Brake Health SOTA artifact (`IF-LC-002`)](#if-lc-002),
  [Function Team 1 OEM-authorized approval (`IF-LC-009`)](#if-lc-009), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [combined-graph owner gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [bounded v1 functional report (`SYS-BHS-001`)](system-requirements-and-traceability.md#sys-bhs-001),
  [deterministic v2 inference (`SYS-BHS-002`)](system-requirements-and-traceability.md#sys-bhs-002),
  [allowlisted v3 advisory (`SYS-BHS-003`)](system-requirements-and-traceability.md#sys-bhs-003),
  [offline local continuity (`SYS-BHS-004`)](system-requirements-and-traceability.md#sys-bhs-004), and
  [separate local and Cloud latency (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-TIRE` — Tire Health in-vehicle service

- Component: [Tire Health In-Vehicle Service (`CMP-TIRE`)](#cmp-tire).
- Interfaces: [dynamics subscription (`IF-TIRE-001`)](#if-tire-001),
  [typed inspection advisory (`IF-TIRE-002`)](#if-tire-002),
  [credential request (`IF-AUTH-001`)](#if-auth-001),
  [short-lived JWT or rejection (`IF-AUTH-003`)](#if-auth-003),
  [bounded condition result (`IF-TIRE-003`)](#if-tire-003),
  [Tire Health SOTA artifact (`IF-LC-007`)](#if-lc-007),
  [Function Team 2 OEM-authorized approval (`IF-LC-010`)](#if-lc-010), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first rollback (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [combined-graph owner gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [existing platform contract only (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [local persistent condition estimate (`SYS-TIRE-002`)](system-requirements-and-traceability.md#sys-tire-002),
  [explicit simulation model (`SYS-TIRE-003`)](system-requirements-and-traceability.md#sys-tire-003),
  [bounded Cloud reporting (`SYS-TIRE-004`)](system-requirements-and-traceability.md#sys-tire-004),
  [independent Tire Health product (`SYS-TIRE-005`)](system-requirements-and-traceability.md#sys-tire-005), and
  [offline inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006).

### `CR-AOS` — AosCore and AosCloud lifecycle

- Components: [AosCore and Service Manager (`CMP-AOS-CORE`)](#cmp-aos-core) and
  [AosCloud Lifecycle Control Plane (`CMP-AOS-CLOUD`)](#cmp-aos-cloud).
- Interfaces: [platform FOTA (`IF-LC-001`)](#if-lc-001),
  [Brake Health SOTA (`IF-LC-002`)](#if-lc-002),
  [Tire Health SOTA (`IF-LC-007`)](#if-lc-007),
  [Platform Team OEM-authorized approval (`IF-LC-008`)](#if-lc-008),
  [Function Team 1 OEM-authorized approval (`IF-LC-009`)](#if-lc-009),
  [Function Team 2 OEM-authorized approval (`IF-LC-010`)](#if-lc-010),
  [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006), and
  [native log API (`IF-OBS-001`)](#if-obs-001), and
  [Aos IAM permission lookup (`IF-AUTH-002`)](#if-auth-002).
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
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [combined-graph owner gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
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

- Components: [Software Delivery Dashboard (`CMP-SW-DASH`)](#cmp-sw-dash)
  and [Demo Orchestrator (`CMP-ORCH`)](#cmp-orch).
- Interfaces: [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [Platform Team OEM-authorized approval (`IF-LC-008`)](#if-lc-008),
  [Function Team 1 OEM-authorized approval (`IF-LC-009`)](#if-lc-009),
  [Function Team 2 OEM-authorized approval (`IF-LC-010`)](#if-lc-010),
  [native log API (`IF-OBS-001`)](#if-obs-001), and
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001).
- Parent requirements: [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [prove current Unit state (`SYS-ID-003`)](system-requirements-and-traceability.md#sys-id-003),
  [exact source-to-Unit binding (`SYS-SRC-001`)](system-requirements-and-traceability.md#sys-src-001),
  [honest single-source presentation (`SYS-SRC-002`)](system-requirements-and-traceability.md#sys-src-002),
  [current effective-target validation (`SYS-REL-002`)](system-requirements-and-traceability.md#sys-rel-002),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [combined-graph owner gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [Cloud-authoritative delivery dashboard (`SYS-OBS-002`)](system-requirements-and-traceability.md#sys-obs-002),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [lifecycle timing bounds (`SYS-TIM-001`)](system-requirements-and-traceability.md#sys-tim-001),
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001),
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002),
  [reset vehicle simulation state (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003),
  [preserve immutable factory artifact (`SYS-RET-005`)](system-requirements-and-traceability.md#sys-ret-005), and
  [no rollback or fleet claim (`SYS-RET-004`)](system-requirements-and-traceability.md#sys-ret-004).

### `CR-CROSS` — Cross-cutting security and operations

- Component focus: all components. The thin Aos–KUKSA Credential Broker is an
  internal responsibility of
  [Vehicle Data Platform Component (`CMP-VDP`)](#cmp-vdp), not a separate
  logical component.
- Interface focus: every trust, resource, timing, log and offline boundary.
- Parent requirements: [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [native-IAM-derived SOTA KUKSA credentials (`SYS-SEC-006`)](system-requirements-and-traceability.md#sys-sec-006),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [KUKSA verifier and token lifetime (`SYS-SEC-004`)](system-requirements-and-traceability.md#sys-sec-004),
  [separate provider authority (`SYS-SEC-005`)](system-requirements-and-traceability.md#sys-sec-005),
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
4. **Accepted 2026-08-18:** each Function Team owns one Cloud-product
   repository containing its backend and dashboard: `brake-health-cloud` and
   `tire-health-cloud`. Each remains separate from the corresponding
   in-vehicle SOTA repository.
5. **Accepted 2026-08-18:** `CMP-SW-DASH` and `CMP-ORCH` remain stateless
   solution components in `aosedge-sdv-demo`. Owning teams make engineering
   release decisions, OEM identities authorize Cloud mutations, and
   `CMP-AOS-CLOUD` stores and executes lifecycle state as defined by
   [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md).
6. **Accepted 2026-08-18:** no separate log pipeline or external log-view
   component is part of the demo. AosCore and AosCloud own native system,
   service-instance, and crash-log collection, delivery, and authoritative
   storage. The stateless `CMP-SW-DASH` uses supported AosCloud APIs to create
   explicitly confirmed requests and present their status/results without an
   independent log archive. Emitting teams own useful, redacted log content;
   API permissions, latency, retention/deletion, and offline behavior remain
   qualification requirements rather than repository-allocation decisions.
7. **Amended 2026-08-19:** ADR 0010 removes the previously proposed separate
   authorization-component concept and the duplicate local per-service OEM
   policy store. The thin Aos–KUKSA Credential Broker is an internal
   responsibility of `CMP-VDP`; Service Manager and Aos IAM own SOTA instance
   identity, `AOS_SECRET` and registered permissions. Upstream `CMP-KUKSA`
   remains unchanged and validates short-lived JWTs with the Platform Team's
   public verifier. The provider's separate platform identity remains a
   qualification gate.

## Acceptance Record for Version 0.6

Version 0.6 preserves the accepted Version 0.5 component graph and corrects
the credential ownership boundary. It adds `IF-AUTH-005` for the factory
IAM/PKCS#11 substrate and `IF-AUTH-006` for the provider's separate platform
credential, while removing the duplicate per-service OEM policy store from
`CMP-VDP`.

The baseline was accepted on 2026-08-19 after reviewers confirmed:

1. every HLA 1.3 box has exactly one primary component owner;
2. every audience-visible dashboard has exactly one authoritative data source;
3. the three independent FOTA/SOTA lifecycles remain separated;
4. Function Team 1 and Function Team 2 are peer product domains;
5. `VU` and `DU` remain runtime roles rather than duplicated component sets;
6. current, engineering-evidence, target, external and deferred states are not
   presented as equivalent;
7. all runtime, functional Cloud, lifecycle and observability boundaries needed
   by Scenario 1.4, including the `T1` Function Team 2 stage, have interface
   IDs;
8. deferred native Cloud dependency admission and the not-yet-implemented
   Credential Broker are not presented as current behavior;
9. no component claims a production driver HMI, continuous raw-telemetry Cloud
   stream, third-party Service Provider, Fleet Operator or production fleet;
10. the provisional requirement packages can be expanded without changing HLA
    1.3 or the accepted demo scenarios.
11. team-owned release decisions, Service Provider publication, OEM-authorized
    deployment approval, AosCloud state/execution, and stateless demo tooling
    remain distinct as required by
    [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md).
12. Service Manager and Aos IAM own SOTA instance identity, `AOS_SECRET` and
    registered permissions; the VDP broker has no parallel identity or
    per-service policy store.
13. the Factory Image supplies only the enabled IAM permission handler and
    non-secret signing-key seam, while per-Unit key material and static tokens
    remain outside immutable artifacts.

Following acceptance, component requirements shall be written package by package,
starting with [Vehicle simulation (`CR-VEHICLE-SIM`)](#cr-vehicle-sim) and
[Vehicle Gateway (`CR-GATEWAY`)](#cr-gateway). Each requirement shall cite a
named and linked parent System Requirement, Architecture Flow and interface,
plus a verification method and retained evidence. Implementation planning
begins only after the relevant package and acceptance tests are reviewed.
