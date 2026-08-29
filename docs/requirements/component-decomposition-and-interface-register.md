<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Decomposition and Interface Register 2.0

- Status: Accepted
- Version: 2.0
- Prepared: 2026-08-22
- Accepted: 2026-08-26
- Previous accepted version: 1.1
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.5](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
- Requirements input: [System Requirements and Traceability 2.0](system-requirements-and-traceability.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0011](../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md),
  [ADR 0013](../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md),
  [ADR 0014](../architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Brake Cloud repository creation completed on 2026-08-28; no additional
  repository creation, implementation, Cloud or Unit mutation is authorized by
  this component baseline alone

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

1. High-Level Architecture 1.5 owns system boundaries, authorities and
   invariants.
2. Demo Scenario 2.0 owns the audience-visible lifecycle and stage sequence.
3. Architecture Flows 2.0 owns detailed runtime, lifecycle, observability and
   failure flows.
4. System Requirements 2.0 owns normative `SYS-*` obligations and gap
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

The Validation Unit and Production Unit are two instances of the same
Domain Controller component graph. They are roles in the demo lifecycle, not
different software components. Each is a runtime deployment created from the
accepted factory-image artifact; neither is an instance of the build-time
Factory Baseline Assembly component.

The Production Unit is the technical demo implementation of the Production
Vehicle business role: a vehicle already released from manufacturing with the
approved SOP baseline. It does not introduce a separate demo-only vehicle
architecture or claim deployment to an actual customer fleet.

### Component is not deployment artifact

The Vehicle Data Platform Component is one logical platform component delivered
in independently versioned FOTA artifacts. It owns the inbound/outbound
providers, versioned KUKSA data/advisory contract and trusted OEM Provider
integration. The separately packaged KUKSA Authorization Compatibility helper
owns current-release Service bootstrap and JWT translation; Aos Service
Manager and IAM retain SOTA identity, secret and registered-permission
lifecycle. Brake Health and Tire Health are
two peer functional components delivered in separate SOTA lifecycles. Version
changes do not create new logical components.

The `OEM Factory Baseline Assembly` is a build-time logical component. It
reproducibly produces the immutable `OEM Demo Factory Image` artifact. That
artifact contains the factory-installed runtime graph and is the source for
fresh Validation and Production Unit deployments; the artifact is not
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
| OEM Software Delivery Dashboard — Platform Releases view | Immutable Platform Team candidate catalogue plus protected publication-pipeline result |
| OEM Software Delivery Dashboard — Delivery and Approvals views | AosCloud lifecycle, OEM-scoped Unit system/VDP log APIs and current Unit state |
| Brake Health Function Dashboard — Vehicle Data and Service Logs views | Function Team 1 backend plus SP1-owned AosCloud service/crash-log records |
| Brake Health Function Dashboard — Release Candidates view | Immutable prepared catalogue plus Function Team 1 release-pipeline result; never OEM lifecycle state |
| Tire Health Function Dashboard — Vehicle Data and Service Logs views | Function Team 2 backend plus SP2-owned AosCloud service/crash-log records |

No dashboard becomes an alternate desired-state database, vehicle-data broker,
functional backend, or vehicle-control path.

The two Brake Health views may be hosted in one web application for the demo,
but they remain logically separated. `Vehicle Data` reads only the functional
backend. `Release Candidates` presents immutable prepared service metadata and
delegates an explicitly confirmed sign/publish request to the common native
helper surface pre-bound to `brake-sp1`. It does not hold a private signing
key, approve deployment or become an AosCloud state store.

The Software Delivery Dashboard must keep Platform publication and Unit
delivery visibly separate. Its Platform Releases view presents only the
prebuilt content-frozen catalogue and delegates one explicitly confirmed
sign/publish request to the common native helper surface pre-bound to
`platform-oem`. Its Delivery and
Approvals views make the decision basis visible: exact artifact and metadata
digests, requested permissions, effective target, required evidence and
freshness, owning-team acceptance and active OEM role. The later approval
control is only the final explicit OEM decision; passing evidence does not
approve and the Dashboard stores neither evidence nor lifecycle state as an
authority.

### Release decision is not Cloud execution

The Platform Team and each Function Team own their engineering release
decisions. A Function Team uses its Service Provider identity to publish and
technically verify a service artifact, but an approval affecting OEM Units is
recorded with an authorized OEM identity. AosCloud stores and executes the
resulting lifecycle transition. The Software Delivery Dashboard and Demo
Orchestrator may facilitate that interaction, but they own neither the decision
nor authoritative lifecycle state.

The identity names above define roles and authority, not credential reuse. The
API client certificate/credential and artifact-signing key/certificate may be
distinct even when operated by the same role. Their exact mapping, certificate
chains, protected storage and SDK operations are a D4 contract; no document may
assume they are the same credential until that contract is qualified.

### QM service is not safety authority

Brake Health and Tire Health are QM-domain maintenance/inspection services in
this demo. Aos IAM/KUKSA scope and VDP validation are cybersecurity and
defense-in-depth controls. The Vehicle Gateway is the final authoritative
boundary for the QM-origin channel and accepts only typed non-safety
advisories; it rejects arbitrary VSS writes and all vehicle-motion or
safety-critical operations.

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
| <a id="cmp-gw-adv"></a>`CMP-GW-ADV` | Gateway QM-Channel Advisory Handler | Act as the final authoritative boundary for the QM-origin channel: validate typed non-safety Brake/Tire advisories, deny arbitrary VSS and motion/safety-critical operations, and publish factual reception/status without claiming driver display | Vehicle Gateway tooling | `carla-ego-runtime` | `NEW` |
| <a id="cmp-eng-dash"></a>`CMP-ENG-DASH` | Engineering Telematics Dashboard | Independent read-only engineering view of Gateway telemetry, drive-mode/world-context/reset facts and typed advisory/status evidence | Demo engineering tooling | `carla-ego-runtime` | Telemetry `CURRENT`; transition and advisory/status `EXTEND` |

`CMP-SCENE`, `CMP-CONTROL`, and `CMP-ENG-DASH` are demonstration tools. They
must remain outside the logical production vehicle architecture even though
they interact with its simulated boundaries.

### Domain Controller substrate and Vehicle Data Platform

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-factory"></a>`CMP-FACTORY` | OEM Factory Baseline Assembly | Reproducibly compose, build, qualify and freeze the unprovisioned SOP substrate, including one stock Aos IAM configuration with `enablePermissionsHandler: true`, factory-installed unmodified KUKSA, separately packaged removable `CMP-KAC`, no pre-populated Service authority/secret state, and dedicated non-secret `kuksa-jwt` signer/verifier preparation wiring without a key, JWT or shared production verifier | Platform Team; pre-SOP manufacturing/build lifecycle | Integration recipes and qualification inputs in `aos-vehicle-platform`; output image remains outside Git | Build evidence `EVIDENCE`; accepted successor assembly and output artifact `NEW` |
| <a id="cmp-runtime"></a>`CMP-RUNTIME` | Provider-Specific Empty-Slot Runtime | Preinstalled OEM Service Manager runtime, bounded provider slot, health/storage boundary and Safe Stop application gate for the Vehicle Data Platform payload; owns durable transaction metadata and asynchronous bounded waiting/recovery, consumes fresh monotonic Gateway frames through a purpose-bound mTLS `VehicleStateProviderItf`, and never persists Safe Stop samples | Platform Team; factory image | `aos-vehicle-platform` | A/B lifecycle `EVIDENCE`; `IMP-03-RUNTIME-001` Safe Stop enforcement accepted; implementation and final factory qualification required |
| <a id="cmp-aos-core"></a>`CMP-AOS-CORE` | AosCore and Service Manager | Unit identity, desired state, security, update lifecycle, service execution and status | AosEdge platform | External AosVM/AosCore release | `EXTERNAL / CURRENT` |
| <a id="cmp-kuksa"></a>`CMP-KUKSA` | Eclipse KUKSA Databroker | Stable factory-installed in-vehicle VSS resource server, direct authorized Service access and verification of short-lived Service JWTs using the configured per-Unit public verifier | External Eclipse component in the SOP substrate; Platform Team governs integration and exposed contract | Unmodified external executable; configuration/contract in `aos-vehicle-platform` | Executable `CURRENT`; final contract/trust integration `EXTEND` |
| <a id="cmp-kac"></a>`CMP-KAC` | Current-Release KUKSA Authorization Compatibility Helper | Separately packaged removable platform helper reached by Services only through a named-resource-mounted private Unix socket; it accepts the bootstrap's instance-bound `AOS_SECRET` for implicit resource `kuksa`, resolves active permissions through the released Aos IAM public gRPC interface using fixed TLS loopback `127.0.0.1:8090`, maps only `r -> read` and `rw -> actuate`, signs through the protected per-Unit key, returns a 300-second JWT with renewal at 180 seconds, uses UTC claims plus boottime scheduling, and enforces the accepted bounded/redacted process envelope. Its exact volatile paths, private systemd PIN delivery, pinned SoftHSM/OpenSSL token path and separate least-privilege KAC/verifier-preparation SELinux domains are factory-owned current-demo integration; it starts empty after verifier/time reconstruction on reboot and owns no persistent state, parallel identity/policy database, shared token directory, TCP listener, external IP access or functional data path | Platform Team; factory/system integration for the current AosCore release | `aos-vehicle-platform/authorization/aos-kuksa-compat/`; separate `aos-kuksa-auth-compat` package/unit, outside VDP and SOTA payloads | `NEW / TRANSITIONAL`; D4-027.1 through D4-027.8 and `IMP-03-KAC-006` decided; implementation open |
| <a id="cmp-vdp"></a>`CMP-VDP` | Vehicle Data Platform Component | OEM-trusted privileged VISS client, signal selection, validation, normalization, KUKSA actual-value publication, versioned contract and defense-in-depth allowlisted outbound QM advisory path; Provider-side KUKSA connectivity is fixed Platform Team integration and Service JWT issuance is excluded | Platform Team; independent FOTA | `aos-vehicle-platform` | Inbound `EVIDENCE`; accepted v1-v3 graph and trusted Provider integration `EXTEND` |

`CMP-RUNTIME` is provider-specific and hosts one bounded component type. This
register makes no claim that the current runtime is a generic arbitrary
component runtime.

### Function Team 1 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-bhs"></a>`CMP-BHS` | Brake Health In-Vehicle Service | QM-domain maintenance application: v1 records bounded pre/active/post braking-event windows, v2 performs synthetic local assessment and sends derived events, and v3 requests only the typed non-safety advisory; no safety goal or motion authority | Function Team 1 / Service Provider 1; SOTA 1 | `brake-health-service` | Scaffold `CURRENT`; product behavior `NEW` |
| <a id="cmp-brake-be"></a>`CMP-BRAKE-BE` | Brake Health Backend | Idempotently reconstruct and persist v1 event windows, ingest v2/v3 derived assessments/events/advisory facts, and expose the Function Team API | Function Team 1; functional Cloud product | `brake-health-cloud` | Repository baseline `CURRENT`; product `NEW` |
| <a id="cmp-brake-dash"></a>`CMP-BRAKE-DASH` | Brake Health Function Dashboard | Host separated Vehicle Data, Release Candidates and Service Logs views: present v1 growing/completed windows and v2/v3 derived data only from the backend; present immutable prepared v1-v3 candidate purpose/digests/permissions/quotas/compatibility and delegate explicit sign/publish actions; and request/present only SP1-owned service-instance/crash logs through a separate operational context without owning keys, OEM approval, Unit lifecycle state or a second log archive | Function Team 1; functional Cloud product | `brake-health-cloud` | Repository baseline `CURRENT`; product `NEW` |

The backend and dashboard are not part of the in-vehicle SOTA artifact and do
not participate in the time-critical local advisory decision.

### Function Team 2 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-tire"></a>`CMP-TIRE` | Tire Health In-Vehicle Service | One mature v1.0 QM-domain maintenance product on accepted VDP v3: maintain a bounded persistent tire-condition estimate, create bounded reports/events, and request only the typed non-safety inspection advisory; no safety goal or motion authority | Function Team 2 / Service Provider 2; SOTA 2 | Proposed `tire-health-service` | `NEW` |
| <a id="cmp-tire-be"></a>`CMP-TIRE-BE` | Tire Health Backend | Idempotent condition-summary/event ingestion, persistence and API | Function Team 2; functional Cloud product | Planned `tire-health-cloud` | `NEW` |
| <a id="cmp-tire-dash"></a>`CMP-TIRE-DASH` | Tire Health Function Dashboard | Host separated Vehicle Data, Release Candidates and Service Logs views: present condition/event/version/delivery facts only from the Tire Health backend; present the one immutable v1.0 candidate and delegate explicit sign/publish actions; expose the fixed D4-023.3 Tire CPU-isolation proof control through its backend; and request/present only SP2-owned service-instance/crash logs through a separate operational context without owning keys, OEM approval, Unit lifecycle state, quota authority or a second log archive | Function Team 2; functional Cloud product | Planned `tire-health-cloud` | `NEW` |

Function Team 2 is a peer of Function Team 1. Its service, backend, dashboard,
identity and SOTA lifecycle must not be placed inside the Brake Health product
or routed through it.

### Software delivery, operations and demo domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-aos-cloud"></a>`CMP-AOS-CLOUD` | AosCloud Lifecycle Control Plane | Provisioning, authoritative Unit/Node desired and reported actual state, batches, campaigns, recorded approvals, audit history, FOTA/SOTA delivery and promotion execution | AosEdge platform / OEM Cloud | External AosCloud service | `EXTERNAL / CURRENT`; exact demo operations require qualification |
| <a id="cmp-sw-dash"></a>`CMP-SW-DASH` | OEM Software Delivery Dashboard | Stateless Platform Releases catalogue and protected publication delegation for prebuilt VDP candidates, including exact Factory Image/runtime compatibility and distinct prepared/signed/AosCloud identities, plus authoritative AosCloud lifecycle and OEM-scoped Unit system/VDP log state, exact artifact/metadata digests, requested permissions, target, evidence status, owning-team acceptance and active D4-011 `oem-delivery` role/effective permissions; own the shared-header title, Current Vehicle/team-summary projection and perspective navigation from the same browser read model; expose only explicitly confirmed actions and then re-read Cloud state | Demo solution | `aosedge-sdv-demo` | `NEW` |
| <a id="cmp-orch"></a>`CMP-ORCH` | Demo Orchestrator | Factory-overlay creation, role binding, provisioning reconciliation, sequential exclusive live CARLA source handover, release sequencing, transient evidence correlation, retirement and reset without owning lifecycle state or approval decisions; its trusted macOS launcher starts and supervises the non-root session-scoped native helper boundary and owns measured physical header/native/browser window composition, visibility/readability proof and safe local layout restoration without owning surface content; telemetry replay is deferred | Demo solution | `aosedge-sdv-demo` | Existing helpers `EVIDENCE`; unified orchestrator and session helper `NEW` |

The native future AosCloud admission of a SOTA service against a required FOTA
Vehicle Data Platform Component version is a deferred feature of
`CMP-AOS-CLOUD`, not a new project component. Released component-to-component
and service-to-layer dependency mechanisms remain external platform
capabilities. In particular, `CMP-SW-DASH` must not implement a temporary
admission controller.

## Runtime Roles and Deployable Products

| Item | Kind | Component graph or payload | Lifecycle |
| --- | --- | --- | --- |
| Validation Unit (`VU`) | Runtime role/deployment | One fresh deployment created from the accepted OEM Demo Factory Image; runs `CMP-RUNTIME`, `CMP-AOS-CORE`, `CMP-KUKSA` and stage-selected payloads | Per demo run |
| Production Unit (`PU`) | Runtime role/deployment | A separate fresh deployment created from the same accepted image and running the same stage-selected component graph | Per demo run |
| OEM Demo Factory Image | Immutable product artifact | Produced by `CMP-FACTORY`; contains `CMP-RUNTIME`, `CMP-AOS-CORE`, `CMP-KUKSA` and separately packaged removable `CMP-KAC`, without feature payloads, active Service authority, JWT, signer key or reusable vehicle identity | Manufacturing baseline |
| Rootfs platform-update envelope | FOTA artifact family | Optional complete rootfs payload containing a later or retrofit Platform Team baseline; targets the factory-installed AosVM rootfs A/B runtime | Platform Team rootfs FOTA; not part of normal M0-M1 |
| Vehicle Data Platform Component v1-v3 | FOTA artifact family | `CMP-VDP` | Platform Team FOTA |
| Brake Health Service v1-v3 | SOTA artifact family | `CMP-BHS` | Service Provider 1 / SOTA 1 |
| Tire Health Service v1.0 | One immutable SOTA candidate in the current demo | `CMP-TIRE`; requires accepted VDP Component v3 | Service Provider 2 / SOTA 2 |

The same accepted artifact bytes and digest move from `VU` qualification to
`PU` promotion. Rebuilding an artifact for promotion is not permitted.

## Repository Allocation

| Repository or external boundary | Allocated components | Decision |
| --- | --- | --- |
| `CarlaSim` | `CMP-CARLA` | Keep simulator source and Apple Silicon port separate from solution code. |
| `UnrealEngine5_carla` | Restricted build dependency of `CMP-CARLA` | Keep private and outside all public repositories. |
| `carla-ego-runtime` | `CMP-SCENE`, `CMP-CONTROL`, `CMP-GW`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH` | One coherent simulated Vehicle Gateway and demo-vehicle tooling boundary. |
| `aos-vehicle-platform` | `CMP-FACTORY` assembly source, `CMP-RUNTIME`, separately packaged `CMP-KAC` under `authorization/aos-kuksa-compat/`, OEM-trusted `CMP-VDP`, and `CMP-KUKSA` contract/trust plus Provider-side connection configuration | Platform Team source; VDP FOTA and separately governed factory/system-integration boundaries; immutable Factory Image output remains outside Git. |
| `brake-health-service` | `CMP-BHS` | Function Team 1 in-vehicle SOTA source only. |
| Proposed `tire-health-service` | `CMP-TIRE` | Function Team 2 in-vehicle SOTA source only; repository not yet created. |
| `brake-health-cloud` | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | Public Function Team 1 Cloud-product repository, separate from the in-vehicle SOTA source; owns the future native ARM64 local-demo container and client integration with the common native publication helper pre-bound to `brake-sp1`; the current PKCS#12 remains in protected host-local custody outside the repository. Isolated source foundation `68fe61b` exists over governance baseline `6da2926`; data implementation is not authorized. |
| Planned `tire-health-cloud` | `CMP-TIRE-BE`, `CMP-TIRE-DASH` | One Function Team 2 Cloud-product repository, separate from the in-vehicle SOTA source; owns the native ARM64 local-demo container and client integration with the common native publication helper pre-bound to `tire-sp2`; the current PKCS#12 remains in protected host-local custody outside the repository; repository not yet created. |
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
| <a id="if-veh-007"></a>`IF-VEH-007` | `CMP-VISS` | `CMP-RUNTIME` | Distinct purpose-bound per-Unit `PLATFORM_UPDATE_RUNTIME` mTLS role with one connection and only ten read-only Safe Stop paths: monotonic `FrameId`, applied control mode, transition/reset generation and discontinuity, factual speed, throttle and brake with freshness semantics. The six control/reset facts form one atomic group only after the Gateway joins the controller record to the physical snapshot by exact CARLA frame ID and simulation time; missing, invalid, duplicate, out-of-order, expired or overflowed handoff input omits that entire group for the frame, never reuses prior values and therefore cannot be interpreted as Safe Stop evidence | Gateway is physical-state authority and frame-coherence authority; OEM Component Runtime evaluates the accepted Safe Stop policy. The local four-record/250-ms join bound is transport tolerance, not Runtime freshness policy | `NEW`; Simulator Control 1.1.0, VISS 1.1.0 and Safe Stop 1.1.1 contracts accepted, implementation open |
| <a id="if-data-001"></a>`IF-DATA-001` | `CMP-VDP` | `CMP-KUKSA` | Validated actual values, availability, freshness and provenance | Versioned Vehicle Data Platform contract | `EVIDENCE / EXTEND` |
| <a id="if-data-002"></a>`IF-DATA-002` | `CMP-KUKSA` | `CMP-BHS` | `kuksa.val.v1` read/subscribe subset for Brake Health | Vehicle Data Platform contract | `NEW` accepted service contract |
| <a id="if-tire-001"></a>`IF-TIRE-001` | `CMP-KUKSA` | `CMP-TIRE` | `kuksa.val.v1` read/subscribe dynamics subset for tire-condition estimation | Vehicle Data Platform contract | `NEW` accepted service contract |
| <a id="if-adv-001"></a>`IF-ADV-001` | `CMP-BHS` | `CMP-KUKSA` | Typed QM Brake Health maintenance-advisory write/actuate request | Brake Health request constrained by IAM and platform contract; no safety/motion authority | `NEW` |
| <a id="if-tire-002"></a>`IF-TIRE-002` | `CMP-TIRE` | `CMP-KUKSA` | Typed QM Tire Health inspection-advisory write/actuate request | Tire Health request constrained by IAM and platform contract; no safety/motion authority | `NEW` |
| <a id="if-adv-002"></a>`IF-ADV-002` | `CMP-KUKSA` | `CMP-VDP` | Advisory target change plus caller authorization context | Vehicle Data Platform outbound contract | `NEW` |
| <a id="if-adv-003"></a>`IF-ADV-003` | `CMP-VDP` | `CMP-VISS` | Narrow VISS Set request for the accepted QM advisory target | Platform outbound defense-in-depth allowlist | `NEW` |
| <a id="if-adv-004"></a>`IF-ADV-004` | `CMP-VISS` | `CMP-GW-ADV` | Restricted QM-origin advisory delivery | Authoritative Gateway deny-by-default contract | `NEW` |
| <a id="if-adv-005"></a>`IF-ADV-005` | `CMP-GW-ADV` | `CMP-VISS` | Factual received/rejected/status signal | Gateway state | `NEW` |
| <a id="if-auth-007"></a>`IF-AUTH-007` | `CMP-BHS` / `CMP-TIRE` compatibility bootstrap | `CMP-KAC` | Strict `aos-kuksa-auth-compat/v1` `status` or `issue` over private `request.sock`; `issue` carries only current instance `AOS_SECRET`; implicit fixed `kuksa` resource; one LF-terminated JSON request/response per connection | Aos IAM is authoritative; strict schema plus named resource, group and Unix peer credentials are defense in depth | `NEW / TRANSITIONAL` |
| <a id="if-auth-008"></a>`IF-AUTH-008` | `CMP-KAC` | `CMP-AOS-CORE` IAM | Native `GetPermissions(AOS_SECRET, fixed-resource)` through fixed TLS loopback `127.0.0.1:8090`, Aos CA trust and expected server name `main`, returning active Service identity and registered path/mode permissions or rejection; no DNS, caller-selected endpoint or external IP | Service Manager registration and current Aos IAM state | `EXTERNAL / EXTEND` qualification |
| <a id="if-auth-009"></a>`IF-AUTH-009` | `CMP-KAC` | requesting `CMP-BHS` / `CMP-TIRE` compatibility bootstrap | Strict `ready`, `issued` or `rejected` response; only `issued` carries a 300-second JWT and renewal-at-180-second instant; only fixed error codes and KAC-generated correlation; bootstrap atomically maintains `/run/aosedge/secrets/kuksa/token.jwt`, then reconnects/recreates KUKSA subscriptions with each replacement token and starts analytics without `AOS_SECRET` | Aos IAM result plus non-widening `r -> read`, `rw -> actuate` mapping; no caller correlation, `w`, wildcards, provider actions, free-text error, parallel Service policy store or shared host token directory | `NEW / TRANSITIONAL` |
| <a id="if-auth-010"></a>`IF-AUTH-010` | `CMP-AOS-CORE` / factory security substrate | `CMP-KAC` and `CMP-KUKSA` | Shared IAM configuration with permission handler enabled; one protected per-Unit `kuksa-jwt` RSA signing operation; `aos-kuksa-verifier-prepare.service` protected sign/verify self-test and atomic root-owned mode-`0444` `/run/aos-kuksa-verifier/kuksa-jwt-public.pem`; mandatory KUKSA `--jwt-public-key`; one-sync-per-boot plus 10-second startup time gate and helper-side issue/renew wall-to-boot deviation check; fail-closed startup, reboot reconstruction and teardown of volatile/runtime authority; no helper anchor/continuous time monitor/KUKSA lifecycle controller and no key/JWT/shared verifier enters an artifact or log | Stock Aos IAM plus dedicated certificate-module/PKCS#11 and systemd-timesyncd integration; D4-010.1 and simplified D4-027.6/.7 current-release compatibility scope; stronger native time/invalidation behavior requalified at migration | `NEW / QUALIFY` |

The advisory chain proves only QM maintenance-request handling and Gateway
state. VDP validation is defense in depth; the Gateway is the authoritative
boundary. The chain does not prove a safety function, production driver
display, acknowledgement, vehicle-motion or brake actuation.

### Retired authorization interfaces

The former interfaces assigned Service JWT issuance to VDP and required a
dynamic Provider credential. Architecture 1.5 retires them without silently
changing their historical meaning.

| Retired identifier | Replacement or disposition |
| --- | --- |
| <a id="if-auth-001"></a>`IF-AUTH-001` | [`IF-AUTH-007`](#if-auth-007) |
| <a id="if-auth-002"></a>`IF-AUTH-002` | [`IF-AUTH-008`](#if-auth-008) |
| <a id="if-auth-003"></a>`IF-AUTH-003` | [`IF-AUTH-009`](#if-auth-009) |
| <a id="if-auth-004"></a>`IF-AUTH-004` | Direct Service-to-KUKSA data interfaces plus [`IF-AUTH-009`](#if-auth-009) and [`IF-AUTH-010`](#if-auth-010) |
| <a id="if-auth-005"></a>`IF-AUTH-005` | [`IF-AUTH-010`](#if-auth-010) |
| <a id="if-auth-006"></a>`IF-AUTH-006` | Retired without dynamic-authorization successor; trusted Provider connectivity is Platform Team integration on `IF-DATA-001` / `IF-ADV-002` |

## Functional Cloud Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-func-001"></a>`IF-FUNC-001` | `CMP-BHS` | `CMP-BRAKE-BE` | Versioned bounded Brake Health message family. D4-016.2 freezes the v1 [RFC-8785/SHA-256 chunk/completion and local-spool contract](../../contracts/brake-telemetry-window/README.md); D4-017 freezes isolated local HTTP delivery and durable acknowledgement. Later messages are idempotent v2/v3 `BrakeHealthAssessment`, threshold/change `BrakeHealthEvent`, and correlated advisory fact; preserve original sample/event times. Reported `system_uid` is demo correlation, not authenticated backend identity; production authentication is Function Team 1-owned and out of scope | Function Team 1 data contract | `NEW`; design contract accepted, implementation/qualification open |
| <a id="if-func-002"></a>`IF-FUNC-002` | `CMP-BRAKE-BE` | `CMP-BRAKE-DASH` / `CMP-ORCH` | Query/subscription API for reconstructed v1 windows and persisted v2/v3 Brake Health derived results, scoped by an injected exact current Test/Production Unit context sourced from the provisioning journal; later out-of-order chunks remain hidden until authoritative window start, and event VDP provenance remains nullable/pending until exact assessment correlation. The exact preview-and-delete operation freezes an explicitly ordered RFC-8785/SHA-256 row set and maximum-1024-character process-local HMAC confirmation; malformed, bad-MAC, expired or previous-process tokens are `409 PREVIEW_TOKEN_EXPIRED`, while only a valid-MAC changed-row-set token is `409 PREVIEW_STALE`. Live context wiring remains integration work and no Cloud state is inferred | Function Team 1 backend | `NEW`; design contract accepted, implementation/qualification open |
| <a id="if-tire-003"></a>`IF-TIRE-003` | `CMP-TIRE` | `CMP-TIRE-BE` | Versioned, bounded and idempotent `TireHealthAssessment`, band-change event, advisory fact and Function Team-reported `TIRE_FUNCTION_STATUS` over the isolated local demo route. Reported `system_uid` is correlation, not authenticated backend identity; production authentication is Function Team 2-owned and out of scope | Function Team 2 data contract | `NEW`; D4-018/D4-019 accepted design contract |
| <a id="if-tire-004"></a>`IF-TIRE-004` | `CMP-TIRE-BE` | `CMP-TIRE-DASH` / `CMP-ORCH` | Query/subscription API for persisted Tire Health results; one fixed, identity-bound D4-023.3 CPU-isolation proof command path with no arbitrary load parameters or enforcement claim; plus an exact preview-and-delete administration operation for current-run cleanup | Function Team 2 backend | `NEW` |

Functional Cloud interfaces are asynchronous. Loss of Cloud connectivity must
not stop local Brake Health or Tire Health analysis and advisory generation.

## Lifecycle and Operational Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-lc-001"></a>`IF-LC-001` | Platform Team release pipeline | `CMP-AOS-CLOUD` | Exact prepared VDP v1-v3 candidate signed and published through D4-010.3 profile `platform-oem`, followed by independent Cloud identity/digest reconciliation | Platform Team OEM technical-publication identity; no automatic Validation deployment or promotion approval | `EXTEND / QUALIFY` |
| <a id="if-lc-002"></a>`IF-LC-002` | Function Team 1 Service Provider pipeline | `CMP-AOS-CLOUD` | Exact prepared Brake Health v1-v3 candidate signed and published through D4-010.3 profile `brake-sp1`, followed by independent Cloud identity/digest reconciliation | Service Provider 1 technical-publication identity; no OEM Unit deployment approval | `NEW / QUALIFY` |
| <a id="if-lc-007"></a>`IF-LC-007` | Function Team 2 Service Provider pipeline | `CMP-AOS-CLOUD` | Exact prepared Tire Health v1.0 candidate signed and published through D4-010.3 profile `tire-sp2`, followed by independent Cloud identity/digest reconciliation | Service Provider 2 technical-publication identity; no OEM Unit deployment approval | `NEW / QUALIFY` |
| <a id="if-lc-008"></a>`IF-LC-008` | Platform Team acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Platform Team records exact Validation Unit FOTA acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact artifact/metadata digests, effective target and applicable evidence | Platform Team owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-009"></a>`IF-LC-009` | Function Team 1 acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Function Team 1 records exact Brake Health Validation Unit acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact service/metadata digests, requested permissions, effective target and applicable evidence | Function Team 1 owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-010"></a>`IF-LC-010` | Function Team 2 acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Function Team 2 records exact Tire Health Validation Unit acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact service/metadata digests, requested permissions, effective target and applicable evidence | Function Team 2 owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-004"></a>`IF-LC-004` | `CMP-AOS-CLOUD` | `CMP-AOS-CORE` | Provisioning, desired state, update delivery, validation, status and retirement | AosCloud and current Unit state | `EXTERNAL / EXTEND` qualification |
| <a id="if-lc-005"></a>`IF-LC-005` | `CMP-SW-DASH` | `CMP-AOS-CLOUD` | D4-011 `/users/me/` role/effective-permission preflight; scoped API reads; exact digest/permissions/target/evidence/team-acceptance presentation; blocked-reason display; final explicitly confirmed `oem-delivery` call; authoritative post-action re-read and `UNCERTAIN` reconciliation without blind retry | AosCloud; dashboard holds no parallel desired/evidence state, release decision, automatic approval policy or claimed server-idempotency mechanism | `NEW` |
| <a id="if-lc-006"></a>`IF-LC-006` | `CMP-AOS-CORE` | `CMP-RUNTIME` / `CMP-BHS` / `CMP-TIRE` | Install, start, stop, update, SOTA removal, pre-Apply FOTA revert, post-Apply forward repair, readiness and resource enforcement; for VDP FOTA, the factory-installed OEM runtime persists transaction metadata, returns native `Activating` and asynchronously gates destructive `StopInstance` and activation `StartInstance` transitions on `IF-VEH-007` frames that are fresh when acquired, while retained history proves stability only and the latest complete frame is revalidated immediately before each destructive step; the runtime does not hold its main mutex while waiting or change Service SOTA motion policy | AosCloud/AosCore own desired/actual lifecycle; OEM Component Runtime owns Platform FOTA Safe Stop application enforcement; Gateway owns vehicle facts | Platform lifecycle `CURRENT`; `IMP-03-RUNTIME-001` extension accepted, implementation open |
| <a id="if-obs-001"></a>`IF-OBS-001` | `CMP-SW-DASH` / `CMP-BRAKE-DASH` / `CMP-TIRE-DASH` | `CMP-AOS-CLOUD` and the matching dashboard | Explicit role-scoped request plus authoritative request/status/result/file through supported AosCloud APIs: `CMP-SW-DASH` uses `/api/v11/unit-logs/` under `oem-delivery` for system/VDP evidence; Brake and Tire dashboards use `/api/v11/service-logs/` under distinct SP1/SP2 operational contexts for only their own service-instance/crash evidence. No browser receives a credential; every dashboard keeps no second archive and removes bounded temporary downloads | Cloud request and related stored file remain authoritative while retained; current API exposes no retention policy | Native platform storage/API path `EXTERNAL / CURRENT`; role-scoped dashboard adapters and live log-lifecycle qualification `NEW / QUALIFY` |
| <a id="if-demo-001"></a>`IF-DEMO-001` | `CMP-ORCH` | Native macOS helper, QEMU/AosVM instances and CARLA/Gateway launchers | Launcher-owned non-root session boundary, overlay creation, role binding, start/stop, source selection and safe retirement | Authenticated local session, allowlisted operations, local session manifest plus authoritative Unit state | `EVIDENCE / EXTEND` |
| <a id="if-demo-002"></a>`IF-DEMO-002` | `CMP-ORCH` | `CMP-SW-DASH` Representation Layer and launcher-owned CARLA, Controller, Engineering Telematics and browser window surfaces | Session-scoped measured workspace profile, exact owned-window identity, reserved header strip, physical bounds/visibility/non-overlap/readability probes and safe local layout restoration; the dashboard supplies the stateless shared-header read model and team navigation while every surface owner retains its content | `CMP-ORCH` owns physical composition only; `CMP-SW-DASH` owns header meaning from the existing browser read model; no Cloud/vehicle/release mutation, content authority, native-window embedding or second state store | `NEW / QUALIFY` |

Native admission of a SOTA service against a required FOTA Vehicle Data
Platform Component version is a future behavior on `IF-LC-004`. Until an
implementing AosEdge release is available and qualified, the corresponding
negative-path demo remains `DEFERRED` and no local interface substitutes for
it. Existing component-to-component and service-to-layer dependency contracts
remain available through their native platform paths.

## Provisional Component Requirement Packages

This allocation is the bridge to the component requirement documents. It does
not itself define component-level normative requirements. `CR-VEHICLE-SIM`,
`CR-VEHICLE-SIM`, `CR-GATEWAY`, `CR-FACTORY`, `CR-KAC`, `CR-VDP`, `CR-DEMO`,
`CR-CROSS` and `CR-E2E` have completed D3 design review in the
[component package set](components/README.md); the remaining allocations retain
their own recorded review state. The reader view explains each purpose without
requiring another document, while the detailed traceability below remains the
single allocation record for exact identifiers.

| Package | Human-readable responsibility | Primary components | Requirement themes |
| --- | --- | --- | --- |
| <a id="cr-vehicle-sim"></a>`CR-VEHICLE-SIM` | Define the installed Vehicle Hardware Capability Manifest, provide every declared physical signal/actuator behavior, repeatable braking and tire stimuli, exact source evidence, hidden ground-truth isolation and clean CARLA scenario reset. | CARLA vehicle and Scenario Controller | Hardware-profile completeness, determinism, source integrity, simulation truth and reset |
| <a id="cr-gateway"></a>`CR-GATEWAY` | Account for the complete hardware profile, distinguish actuator capability from authority, expose VISS, arbitrate control, enforce the authoritative QM-channel advisory boundary and present factual engineering status. | Control UI, Gateway, VISS, Advisory Handler and Engineering Dashboard | Hardware coverage, telemetry contract, unavailable data, control traceability, deny-by-default QM containment and chronology |
| <a id="cr-factory"></a>`CR-FACTORY` | Reproducibly assemble and preserve the clean unprovisioned Factory Image artifact, enable stock Aos IAM permission handling, carry the dedicated non-secret per-Unit signer/verifier preparation seam without key material, and create two identity-safe deployments with a healthy empty capability slot. | Factory Baseline Assembly and Empty-Slot Runtime | Reproducibility, artifact immutability, IAM substrate, identity/key/shared-verifier absence, overlay uniqueness and preservation |
| <a id="cr-kac"></a>`CR-KAC` | Realize the current-release Service credential boundary without entering VDP or SOTA business logic: named-resource-mounted Unix socket, implicit fixed-resource bootstrap, IAM lookup, bounded JWT derivation, Service-private tmpfs delivery and lifecycle cleanup. | Current-Release KUKSA Authorization Compatibility Helper | Peer isolation, bootstrap-only secret use, no caller-selected authority, mapping, protected signing, renewal, reboot, stop/removal and native-migration deletion seam |
| <a id="cr-vdp"></a>`CR-VDP` | Deliver the versioned VISS-to-KUKSA data capability and defense-in-depth outbound QM advisory path as an OEM-trusted FOTA component without issuing Service JWTs. | KUKSA contract/configuration and Vehicle Data Platform Component | Compatibility, data quality, outbound validation, trusted Provider integration, FOTA and recovery |
| <a id="cr-bhs"></a>`CR-BHS` | Capture bounded v1 braking-event windows, move synthetic assessment and derived reporting on-board in v2, operate offline, and request only the approved v3 advisory. | Brake Health In-Vehicle Service | Trigger/window determinism, model/data-product evolution, compatibility, offline operation and advisory scope |
| <a id="cr-tire"></a>`CR-TIRE` | Deliver one mature Tire Health v1.0 product on accepted VDP v3: estimate condition locally, persist bounded state, upload bounded results and request the typed inspection advisory through an independent SOTA lifecycle. | Tire Health In-Vehicle Service | Exact VDP v3 prerequisite, model, persistence, bounded reporting, advisory and multi-tenant isolation |
| <a id="cr-aos"></a>`CR-AOS` | Provide identity, authoritative desired/reported actual and Unit Set state, recorded owner approvals, FOTA/SOTA execution, dependency behavior, resource enforcement and native operational-log collection/delivery. | AosCore and AosCloud | Provisioning, lifecycle state and execution, Unit Set contracts, OEM-authorized validation, pre-Apply revert, SOTA removal, forward repair, native logging and retirement |
| <a id="cr-brake-cloud"></a>`CR-BRAKE-CLOUD` | Reconstruct and present v1 Brake Telemetry Windows; ingest/present v2/v3 derived messages; expose a separate prepared-candidate view that delegates protected sign/publish actions; and run as a Mac-local ARM64 container without entering the vehicle decision path or owning OEM lifecycle state. | Brake Health Backend and Function Dashboard | Candidate integrity, protected publication delegation, chunk reconstruction, idempotency, data-product evolution, offline synchronization, local hosting, exact-current-Unit persistence and complete R0 deletion |
| <a id="cr-tire-cloud"></a>`CR-TIRE-CLOUD` | Present one prepared Tire v1.0 candidate, delegate protected publication and ingest/present real bounded Tire Health results as an independent Mac-local Function Team product without owning OEM lifecycle state. | Tire Health Backend and Function Dashboard | Candidate integrity, protected publication delegation, idempotency, delivery/freshness, product isolation, local hosting, current-run persistence and complete R0 deletion |
| <a id="cr-demo"></a>`CR-DEMO` | Orchestrate manufactured overlays, Unit roles and Unit Set membership; present the immutable Platform candidate catalogue and delegate protected FOTA publication; facilitate staged releases, evidence-backed final OEM approval, authoritative dashboards, ordered retirement and next-run provisioning. | Software Delivery Dashboard and Demo Orchestrator | Candidate integrity, protected publication, target safety, source binding, membership reconciliation, decision-basis presentation, native logs, observability and reset |
| <a id="cr-cross"></a>`CR-CROSS` | Define security, authorization, redaction, chronology, resource and offline constraints shared by multiple owners. | Cross-component concerns; helper implementation remains allocated to `CMP-KAC` / `CR-KAC` | Least privilege, fail-closed behavior, evidence controls and chronology |
| <a id="cr-e2e"></a>`CR-E2E` | Prove the complete accepted graph on Validation and Production Units across normal, failure, offline, recovery and retirement paths. | All accepted components | End-to-end acceptance and retained evidence |

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
  [Platform-update Safe Stop evidence (`IF-VEH-007`)](#if-veh-007),
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
  [QM service and Gateway containment (`SYS-SEC-007`)](system-requirements-and-traceability.md#sys-sec-007),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [truthful control-transition evidence (`SYS-OBS-005`)](system-requirements-and-traceability.md#sys-obs-005), and
  [separate on-board and Cloud chronology (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002).

### `CR-FACTORY` — Factory assembly, artifact and empty slot

- Components: [OEM Factory Baseline Assembly (`CMP-FACTORY`)](#cmp-factory) and
  [Provider-Specific Empty-Slot Runtime (`CMP-RUNTIME`)](#cmp-runtime).
- Produced artifact: immutable `OEM Demo Factory Image`, from which separate
  Validation and Production Unit runtime deployments are created.
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006),
  [helper IAM/PKCS#11 and verifier substrate (`IF-AUTH-010`)](#if-auth-010), and
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001).
- Parent requirements: [reproducible factory image (`SYS-MFG-001`)](system-requirements-and-traceability.md#sys-mfg-001),
  [clean SOP substrate (`SYS-MFG-002`)](system-requirements-and-traceability.md#sys-mfg-002),
  [unique fresh overlays (`SYS-MFG-003`)](system-requirements-and-traceability.md#sys-mfg-003),
  [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001), and
  [per-Unit KUKSA signer and verifier (`SYS-SEC-004`)](system-requirements-and-traceability.md#sys-sec-004),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008), and
  [preserve immutable factory artifact (`SYS-RET-005`)](system-requirements-and-traceability.md#sys-ret-005).

### `CR-KAC` — Current-release KUKSA authorization compatibility

- Component: [Current-Release KUKSA Authorization Compatibility Helper (`CMP-KAC`)](#cmp-kac).
- Packaging boundary: separately packaged Platform Team factory/system
  integration in `aos-vehicle-platform`; outside VDP, Brake Health and Tire
  Health payloads and business logic.
- Interfaces: [Service fixed-resource bootstrap (`IF-AUTH-007`)](#if-auth-007),
  [Aos IAM permission lookup (`IF-AUTH-008`)](#if-auth-008),
  [private JWT delivery or rejection (`IF-AUTH-009`)](#if-auth-009), and
  [IAM/PKCS#11 plus verifier substrate (`IF-AUTH-010`)](#if-auth-010).
- Parent requirements: [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [per-Unit KUKSA signer and verifier (`SYS-SEC-004`)](system-requirements-and-traceability.md#sys-sec-004),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008),
  [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](system-requirements-and-traceability.md#sys-obs-007), and
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001).

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
  [platform FOTA artifact (`IF-LC-001`)](#if-lc-001),
  [Platform acceptance and OEM Release Authority authorization (`IF-LC-008`)](#if-lc-008), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first recovery (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [dependent-release milestone gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [evidence-backed final OEM approval (`SYS-REL-010`)](system-requirements-and-traceability.md#sys-rel-010),
  [healthy empty capability slot (`SYS-VDP-001`)](system-requirements-and-traceability.md#sys-vdp-001),
  [versioned v1 signal contract (`SYS-VDP-002`)](system-requirements-and-traceability.md#sys-vdp-002),
  [backward-compatible v2 capability (`SYS-VDP-003`)](system-requirements-and-traceability.md#sys-vdp-003),
  [allowlisted outbound advisory (`SYS-VDP-004`)](system-requirements-and-traceability.md#sys-vdp-004),
  [QM service and Gateway containment (`SYS-SEC-007`)](system-requirements-and-traceability.md#sys-sec-007),
  [explicit degraded data (`SYS-VDP-005`)](system-requirements-and-traceability.md#sys-vdp-005),
  [existing Tire Health platform contract (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [offline Tire Health inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  and [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003).

### `CR-BHS` — Brake Health in-vehicle service

- Accepted/design-reviewed executable D4 refinements:
  [Brake Health Synthetic Model](../../contracts/brake-health-model/README.md),
  [Brake Health v3 Advisory Policy](../../contracts/brake-health-advisory-policy/README.md),
  [Brake Health Runtime and Evidence](../../contracts/brake-health-runtime/README.md),
  and [Brake Cloud API](../../contracts/brake-cloud-api/README.md)
  (D4-016.1/.2/.3/.4/.5 and D4-017 accepted;
  D4-003 calibration and D4-023 quota qualification remain live gates).

- Component: [Brake Health In-Vehicle Service (`CMP-BHS`)](#cmp-bhs).
- Interfaces: [Brake Health data subscription (`IF-DATA-002`)](#if-data-002),
  [advisory request (`IF-ADV-001`)](#if-adv-001),
  [fixed-resource bootstrap (`IF-AUTH-007`)](#if-auth-007),
  [private JWT or rejection (`IF-AUTH-009`)](#if-auth-009),
  [versioned functional message family (`IF-FUNC-001`)](#if-func-001),
  [Brake Health SOTA artifact (`IF-LC-002`)](#if-lc-002),
  [Function Team 1 acceptance and OEM Release Authority authorization (`IF-LC-009`)](#if-lc-009), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first recovery (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [dependent-release milestone gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [bounded v1 Brake Telemetry Window (`SYS-BHS-005`)](system-requirements-and-traceability.md#sys-bhs-005),
  [deterministic v2 edge assessment (`SYS-BHS-002`)](system-requirements-and-traceability.md#sys-bhs-002),
  [derived v2 Cloud data product (`SYS-BHS-006`)](system-requirements-and-traceability.md#sys-bhs-006),
  [allowlisted v3 advisory (`SYS-BHS-003`)](system-requirements-and-traceability.md#sys-bhs-003),
  [offline local continuity (`SYS-BHS-004`)](system-requirements-and-traceability.md#sys-bhs-004),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008),
  [separate on-board and Cloud chronology (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002), and
  [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](system-requirements-and-traceability.md#sys-res-001).

### `CR-TIRE` — Tire Health in-vehicle service

- Prepared executable D4 refinement:
  [Tire Health In-Vehicle Product Contract](../../contracts/tire-health-model/README.md)
  (`REVIEW_CANDIDATE`, not implemented or accepted).

- Component: [Tire Health In-Vehicle Service (`CMP-TIRE`)](#cmp-tire).
- Interfaces: [dynamics subscription (`IF-TIRE-001`)](#if-tire-001),
  [typed inspection advisory (`IF-TIRE-002`)](#if-tire-002),
  [fixed-resource bootstrap (`IF-AUTH-007`)](#if-auth-007),
  [private JWT or rejection (`IF-AUTH-009`)](#if-auth-009),
  [bounded condition result (`IF-TIRE-003`)](#if-tire-003),
  [Tire Health SOTA artifact (`IF-LC-007`)](#if-lc-007),
  [Function Team 2 acceptance and OEM Release Authority authorization (`IF-LC-010`)](#if-lc-010), and
  [runtime enforcement (`IF-LC-006`)](#if-lc-006).
- Parent requirements: [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first recovery (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [dependent-release milestone gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [existing platform contract only (`SYS-TIRE-001`)](system-requirements-and-traceability.md#sys-tire-001),
  [local persistent condition estimate (`SYS-TIRE-002`)](system-requirements-and-traceability.md#sys-tire-002),
  [explicit simulation model (`SYS-TIRE-003`)](system-requirements-and-traceability.md#sys-tire-003),
  [bounded Cloud reporting (`SYS-TIRE-004`)](system-requirements-and-traceability.md#sys-tire-004),
  [independent Tire Health product (`SYS-TIRE-005`)](system-requirements-and-traceability.md#sys-tire-005), and
  [offline inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008), and
  [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](system-requirements-and-traceability.md#sys-res-001).

### `CR-AOS` — AosCore and AosCloud lifecycle

- Components: [AosCore and Service Manager (`CMP-AOS-CORE`)](#cmp-aos-core) and
  [AosCloud Lifecycle Control Plane (`CMP-AOS-CLOUD`)](#cmp-aos-cloud).
- Interfaces: [platform FOTA (`IF-LC-001`)](#if-lc-001),
  [Brake Health SOTA (`IF-LC-002`)](#if-lc-002),
  [Tire Health SOTA (`IF-LC-007`)](#if-lc-007),
  [Platform acceptance and OEM Release Authority authorization (`IF-LC-008`)](#if-lc-008),
  [Function Team 1 acceptance and OEM Release Authority authorization (`IF-LC-009`)](#if-lc-009),
  [Function Team 2 acceptance and OEM Release Authority authorization (`IF-LC-010`)](#if-lc-010),
  [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [runtime enforcement (`IF-LC-006`)](#if-lc-006),
  [native log API (`IF-OBS-001`)](#if-obs-001),
  [Aos IAM permission lookup (`IF-AUTH-008`)](#if-auth-008), and
  [helper trust substrate (`IF-AUTH-010`)](#if-auth-010).
- Parent requirements: [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [prove current Unit state (`SYS-ID-003`)](system-requirements-and-traceability.md#sys-id-003),
  [qualify identity retirement (`SYS-ID-004`)](system-requirements-and-traceability.md#sys-id-004),
  [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [current effective-target validation (`SYS-REL-002`)](system-requirements-and-traceability.md#sys-rel-002),
  [service capability compatibility (`SYS-REL-003`)](system-requirements-and-traceability.md#sys-rel-003),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  [dependent-first recovery (`SYS-REL-005`)](system-requirements-and-traceability.md#sys-rel-005),
  [native Cloud dependency rejection (`SYS-REL-006`)](system-requirements-and-traceability.md#sys-rel-006),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [dependent-release milestone gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [evidence-backed final OEM approval (`SYS-REL-010`)](system-requirements-and-traceability.md#sys-rel-010),
  [Cloud-authoritative delivery dashboard (`SYS-OBS-002`)](system-requirements-and-traceability.md#sys-obs-002),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008),
  [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](system-requirements-and-traceability.md#sys-res-001),
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001), and
  [reconcile Unit Sets for the next run (`SYS-RET-006`)](system-requirements-and-traceability.md#sys-ret-006).

[Native Cloud dependency rejection (`SYS-REL-006`)](system-requirements-and-traceability.md#sys-rel-006)
remains deferred and is allocated only to
[Aos lifecycle (`CR-AOS`)](#cr-aos); it is not a requirement on the Software
Delivery Dashboard.

### `CR-BRAKE-CLOUD` — Brake Health Cloud product

- Accepted/design-reviewed executable D4 refinements:
  [Brake Health Cloud API](../../contracts/brake-cloud-api/README.md) and
  [Local Demo Hosting and VM Route](../../contracts/local-demo-hosting/README.md)
  (D4-017 accepted and D4-020 design reviewed; two-VM route/LAN-negative qualification remains
  required; production backend authentication is out of scope).

- Components: [Brake Health Backend (`CMP-BRAKE-BE`)](#cmp-brake-be) and
  [Brake Health Function Dashboard (`CMP-BRAKE-DASH`)](#cmp-brake-dash).
- Interfaces: [versioned functional message family (`IF-FUNC-001`)](#if-func-001),
  [dashboard query API (`IF-FUNC-002`)](#if-func-002), role-scoped
  [native log API (`IF-OBS-001`)](#if-obs-001), and the delegated
  [Brake Health SOTA publication boundary (`IF-LC-002`)](#if-lc-002).
- Parent requirements: [bounded v1 Brake Telemetry Window (`SYS-BHS-005`)](system-requirements-and-traceability.md#sys-bhs-005),
  [derived v2 Cloud data product (`SYS-BHS-006`)](system-requirements-and-traceability.md#sys-bhs-006),
  [offline local continuity (`SYS-BHS-004`)](system-requirements-and-traceability.md#sys-bhs-004),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004), and
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002).

### `CR-TIRE-CLOUD` — Tire Health Cloud product

- Prepared executable D4 refinements:
  [Tire Health Cloud API](../../contracts/tire-cloud-api/README.md),
  [Tire Health In-Vehicle Product Contract](../../contracts/tire-health-model/README.md)
  and [Local Demo Hosting and VM Route](../../contracts/local-demo-hosting/README.md)
  (`REVIEW_CANDIDATE`; no repository or executable exists).

- Components: [Tire Health Backend (`CMP-TIRE-BE`)](#cmp-tire-be)
  and [Tire Health Function Dashboard (`CMP-TIRE-DASH`)](#cmp-tire-dash).
- Interfaces: [bounded condition result (`IF-TIRE-003`)](#if-tire-003) and
  [Tire Health dashboard API (`IF-TIRE-004`)](#if-tire-004), role-scoped
  [native log API (`IF-OBS-001`)](#if-obs-001), delegated
  [Tire Health SOTA publication (`IF-LC-007`)](#if-lc-007), and the external
  [Function Team 2 acceptance and OEM Release Authority authorization handoff (`IF-LC-010`)](#if-lc-010).
- Parent requirements: [bounded Cloud reporting (`SYS-TIRE-004`)](system-requirements-and-traceability.md#sys-tire-004),
  [independent Tire Health product (`SYS-TIRE-005`)](system-requirements-and-traceability.md#sys-tire-005),
  [offline inspection advisory (`SYS-TIRE-006`)](system-requirements-and-traceability.md#sys-tire-006),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004), and
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002).

### `CR-DEMO` — Demonstration orchestration and delivery view

- Prepared executable D4 refinements:
  [Brake Cloud API](../../contracts/brake-cloud-api/README.md),
  [Tire Cloud API](../../contracts/tire-cloud-api/README.md), and
  [Local Demo Hosting and VM Route](../../contracts/local-demo-hosting/README.md)
  (`REVIEW_CANDIDATE`; no local/Cloud/VM action is authorized).

- Components: [Software Delivery Dashboard (`CMP-SW-DASH`)](#cmp-sw-dash)
  and [Demo Orchestrator (`CMP-ORCH`)](#cmp-orch).
- Interfaces: delegated [Platform FOTA publication (`IF-LC-001`)](#if-lc-001),
  [Cloud-to-Unit lifecycle (`IF-LC-004`)](#if-lc-004),
  [Software Delivery Dashboard API (`IF-LC-005`)](#if-lc-005),
  [Platform acceptance and OEM Release Authority authorization (`IF-LC-008`)](#if-lc-008),
  [Function Team 1 acceptance and OEM Release Authority authorization (`IF-LC-009`)](#if-lc-009),
  [Function Team 2 acceptance and OEM Release Authority authorization (`IF-LC-010`)](#if-lc-010),
  [native log API (`IF-OBS-001`)](#if-obs-001),
  [orchestrated VM lifecycle (`IF-DEMO-001`)](#if-demo-001),
  [presenter workspace composition (`IF-DEMO-002`)](#if-demo-002), and the exact
  current-run cleanup operations on [Brake Health dashboard API
  (`IF-FUNC-002`)](#if-func-002) and [Tire Health dashboard API
  (`IF-TIRE-004`)](#if-tire-004).
- Parent requirements: [one identity per overlay (`SYS-ID-001`)](system-requirements-and-traceability.md#sys-id-001),
  [reconcile partial provisioning (`SYS-ID-002`)](system-requirements-and-traceability.md#sys-id-002),
  [prove current Unit state (`SYS-ID-003`)](system-requirements-and-traceability.md#sys-id-003),
  [qualify identity retirement (`SYS-ID-004`)](system-requirements-and-traceability.md#sys-id-004),
  [unique fresh overlays (`SYS-MFG-003`)](system-requirements-and-traceability.md#sys-mfg-003),
  [exact source-to-Unit binding (`SYS-SRC-001`)](system-requirements-and-traceability.md#sys-src-001),
  [honest single-source presentation (`SYS-SRC-002`)](system-requirements-and-traceability.md#sys-src-002),
  [immutable release candidates (`SYS-REL-001`)](system-requirements-and-traceability.md#sys-rel-001),
  [current effective-target validation (`SYS-REL-002`)](system-requirements-and-traceability.md#sys-rel-002),
  [validate before promotion (`SYS-REL-004`)](system-requirements-and-traceability.md#sys-rel-004),
  deferred [native Cloud dependency rejection (`SYS-REL-006`)](system-requirements-and-traceability.md#sys-rel-006),
  [team-owned release decisions (`SYS-REL-007`)](system-requirements-and-traceability.md#sys-rel-007),
  [OEM-authorized deployment approval (`SYS-REL-008`)](system-requirements-and-traceability.md#sys-rel-008),
  [dependent-release milestone gate (`SYS-REL-009`)](system-requirements-and-traceability.md#sys-rel-009),
  [evidence-backed final OEM approval (`SYS-REL-010`)](system-requirements-and-traceability.md#sys-rel-010),
  [independent resource-scoped release operations (`SYS-REL-012`)](system-requirements-and-traceability.md#sys-rel-012),
  [authoritative demo surfaces (`SYS-OBS-001`)](system-requirements-and-traceability.md#sys-obs-001),
  [Cloud-authoritative delivery dashboard (`SYS-OBS-002`)](system-requirements-and-traceability.md#sys-obs-002),
  [visible approval decision basis (`SYS-OBS-006`)](system-requirements-and-traceability.md#sys-obs-006),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](system-requirements-and-traceability.md#sys-obs-007),
  [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](system-requirements-and-traceability.md#sys-res-001),
  [retire Units and overlays (`SYS-RET-001`)](system-requirements-and-traceability.md#sys-ret-001),
  [clear functional run data (`SYS-RET-002`)](system-requirements-and-traceability.md#sys-ret-002),
  [reset vehicle simulation state (`SYS-RET-003`)](system-requirements-and-traceability.md#sys-ret-003),
  [preserve immutable factory artifact (`SYS-RET-005`)](system-requirements-and-traceability.md#sys-ret-005),
  [no rollback or fleet claim (`SYS-RET-004`)](system-requirements-and-traceability.md#sys-ret-004), and
  [reconcile Unit Sets for the next run (`SYS-RET-006`)](system-requirements-and-traceability.md#sys-ret-006).

### `CR-CROSS` — Cross-cutting security and operations

- Component focus: all components. `CMP-KAC` is a separate transitional
  component with its own `CR-KAC` package; `CR-CROSS` owns only shared
  constraints and integration evidence.
- Interface focus: every trust, resource, chronology and log boundary plus one
  targeted Production Unit external-connectivity fault. It interrupts
  Unit-to-AosCloud and installed service-to-functional-backend paths together;
  presenter-control and simulated in-vehicle link loss are not demo scenarios.
- Parent requirements: [least-privilege KUKSA identities (`SYS-SEC-001`)](system-requirements-and-traceability.md#sys-sec-001),
  [role-bound protected publication (`SYS-REL-011`)](system-requirements-and-traceability.md#sys-rel-011),
  [current-release KUKSA Service authorization compatibility (`SYS-SEC-008`)](system-requirements-and-traceability.md#sys-sec-008),
  [fail-closed advisory security (`SYS-SEC-003`)](system-requirements-and-traceability.md#sys-sec-003),
  [KUKSA verifier and token lifetime (`SYS-SEC-004`)](system-requirements-and-traceability.md#sys-sec-004),
  [QM service and Gateway containment (`SYS-SEC-007`)](system-requirements-and-traceability.md#sys-sec-007),
  [operational log controls (`SYS-OBS-003`)](system-requirements-and-traceability.md#sys-obs-003),
  [per-run correlation (`SYS-OBS-004`)](system-requirements-and-traceability.md#sys-obs-004),
  [separate on-board and Cloud chronology (`SYS-TIM-002`)](system-requirements-and-traceability.md#sys-tim-002), and
  [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](system-requirements-and-traceability.md#sys-obs-007), and
  [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](system-requirements-and-traceability.md#sys-res-001).

### `CR-E2E` — End-to-end acceptance

- Component and interface focus: the complete accepted graph on Validation and
  Production Units.
- Parent requirements: every accepted System Requirement and every relevant
  Architecture Flow. The package proves integration; it does not replace the
  more specific allocations above.

## Boundary Decision Status

1. **Accepted 2026-08-18:** logical components, repositories, immutable
   deployable artifacts and runtime deployments are separate concepts.
   `CMP-FACTORY` is the build-time OEM Factory Baseline Assembly, the OEM Demo
   Factory Image is its artifact, and `VU`/`PU` are deployments created from
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
6. **Amended 2026-08-22:** no separate log pipeline or external log-view
   component is part of the demo. AosCore and AosCloud own native system,
   service-instance, and crash-log collection, delivery, and authoritative
   request/result storage. `CMP-SW-DASH` uses the Unit-log API under
   `oem-delivery` only for system/VDP evidence; `CMP-BRAKE-DASH` and
   `CMP-TIRE-DASH` use the Service-log API under separate SP1/SP2 operational
   contexts only for their own service/crash evidence. All use explicitly
   confirmed requests, keep no second archive and remove bounded temporary
   downloads. Emitting teams own useful allowlisted redaction. The current API
   exposes no retention policy; identifiers, permissions, lifecycle states,
   delete effect and offline/reconnect behavior remain live qualification
   requirements.
7. **Amended 2026-08-19:** ADR 0010 removes the previously proposed separate
   authorization-component concept and the duplicate local per-service OEM
   policy store. The thin Aos–KUKSA Credential Broker is an internal
   responsibility of `CMP-VDP`; Service Manager and Aos IAM own SOTA instance
   identity, `AOS_SECRET` and registered permissions. Upstream `CMP-KUKSA`
   remains unchanged and validates short-lived JWTs with the Platform Team's
   per-Unit public verifier. D4-010.1 fixes one RSA/RS256 key and verifier per
   provisioning lifecycle, no live rotation, and no `iss` enforcement claim;
   the provider's separate platform identity remains a qualification gate.
8. **Accepted 2026-08-19:** ADR 0011 classifies both functional services as
   QM-domain maintenance/inspection applications. `CMP-VDP` validates outbound
   advisories as defense in depth, while `CMP-GW-ADV` is the final
   authoritative deny-by-default boundary for the QM-origin channel.
9. **Accepted 2026-08-19:** `CMP-SW-DASH` must present exact artifact and
   metadata digests, requested permissions, target, evidence status,
   owning-team acceptance and active OEM role before exposing the final OEM
   approval action. It owns neither the decision, evidence nor lifecycle
   state, and passing tests never auto-approve.
10. **Accepted 2026-08-19:** `CMP-BRAKE-DASH` may host separated `Release
    Candidates` and `Vehicle Data` views. The former delegates explicit
    sign/publish actions to the Function Team 1 pipeline; the latter reads the
    Brake Health Backend. The Mac-local ARM64 container and common native
    helper pre-bound to `brake-sp1` are deployment refinements, not new HLA
    components or lifecycle authorities.
11. **Accepted 2026-08-19:** `CMP-TIRE` is one mature Tire Health Service v1.0
    candidate requiring accepted VDP Component v3. It does not repeat the
    Brake Health v1-v3 product evolution. Its purpose is to prove a second
    independent Function Team, Service Provider identity, functional data
    product and SOTA lifecycle on the shared platform. Release sequencing,
    evidence-backed OEM approval and service-side fail-closed readiness do not
    claim or replace the deferred native AosCloud dependency-admission feature.
12. **Accepted 2026-08-19:** `CMP-TIRE-DASH` hosts separated `Release
    Candidates` and `Vehicle Data` views. It delegates confirmed publication to
    the Function Team 2 pipeline and reads functional results from
    `CMP-TIRE-BE`; it owns neither keys, OEM approval nor lifecycle state. The
    Mac-local ARM64 container, dedicated persistent volume and native-helper
    `tire-sp2` profile remain isolated from their Brake Health peers.
13. **Accepted 2026-08-19:** `CMP-SW-DASH` adds a `Platform Releases` view for
    exactly the prebuilt, content-frozen VDP v1-v3 candidates and delegates an
    explicitly confirmed sign/publish request to the protected Platform Team
    pipeline. The helper is an internal deployment refinement, not a new HLA
    component, authority or repository. Private keys, source edits,
    compilation, Yocto/rootfs/container builds, packaging/metadata generation,
    model training, full qualification runs and repackaging remain outside the
    browser and presentation flow; technical
    publication remains distinct from later OEM-authorized Unit deployment
    and promotion approval.
14. **Accepted 2026-08-20:** the trusted `CMP-ORCH` macOS demo launcher starts
    the native helper under the logged-in non-root user for one authenticated
    demo session before starting the dashboard backend and browser. The helper
    is not a persistent `launchd`/login service, exposes only allowlisted
    operations, is supervised by the launcher and exits on orderly session end
    or a bounded launcher-loss/orphan condition. This is an internal deployment
    refinement of `CMP-ORCH` and `IF-DEMO-001`, not a new HLA component,
    authority or repository.
15. **Accepted 2026-08-20:** the sanitized coverage contract uses the explicit
    evidence states `UNKNOWN`, `PARTIAL`, `PLANNED`, `DOCUMENTARY_ONLY`,
    `ACCEPTED` and `STALE`. `ACCEPTED` requires a concrete evidence ID and
    verification time bound to the exact subject version/digest, AosEdge
    platform release and configuration digest. Any baseline mismatch converts
    the presentation to `STALE` with a reason. Deferred native dependency
    admission remains disabled and cannot be replaced by local dashboard
    logic. This refines `CMP-SW-DASH` evidence presentation without adding a
    component, authority or repository.
16. **Accepted 2026-08-20:** the `CMP-SW-DASH` Platform Releases catalogue
    contains exactly the prebuilt, tested and content-frozen VDP v1-v3
    candidates. Each candidate binds its unsigned artifact/metadata digests to
    the exact compatible OEM Demo Factory Image digest and component-runtime
    version. The view preserves distinct prepared, signed and AosCloud
    component-version identities and shows their verified mapping without
    treating technical publication as Validation deployment or OEM promotion
    approval. Mismatched bytes, baseline, evidence or identity block
    publication without an in-demo build fallback. This adds no HLA component,
    authority or repository.
17. **Accepted 2026-08-20:** connectivity is separated into vehicle external,
    presenter control-plane and simulated in-vehicle domains. Automotive
    offline/reconnect claims apply only to the Unit's external connectivity;
    the Mac Dashboard/Native Helper connection to AosCloud is an available
    demo precondition whose loss blocks administrative operations without a
    `Unit offline` label. `REQ-DEMO-019` retains `UNCERTAIN` only for defensive
    reconciliation after a helper/process interruption or lost local result,
    and requires an independent AosCloud re-read before `PUBLISHED`. This
    refines `CMP-SW-DASH` and `IF-LC-005` without adding a component, authority
    or repository.
18. **Accepted 2026-08-20:** `CR-DEMO` 0.1 completes D3 design review for
    `CMP-SW-DASH` and `CMP-ORCH` with eighteen active requirements and sixteen
    defined unit-test obligations. Retired `REQ-DEMO-012` and `UT-DEMO-012`
    remain traceable. The accepted package preserves the component graph,
    interfaces, repository allocation and authority boundaries; it authorizes
    D4 contract design only, not implementation or external operations.
19. **Accepted 2026-08-20:** the only deliberate connectivity fault in the
    first demo is one atomic loss of Production Unit external connectivity.
    A single stateful control interrupts Unit-to-AosCloud and installed
    service-to-functional-backend paths together; presenter-to-AosCloud and
    simulated in-vehicle links remain available. `CR-CROSS` proves the shared
    continuity/claim boundary and `CR-E2E` executes the fault; no separate
    per-channel control, component, interface or runtime service is added.
20. **Accepted 2026-08-20:** `CR-DEMO` 0.2 adds `REQ-DEMO-020` and
    `UT-DEMO-018` for the single stateful `Vehicle External Connectivity`
    control. The control applies and restores the complete dual-path fault
    policy atomically, proves excluded paths remain available and rejects
    partial state as success. `CR-DEMO` now contains nineteen active
    requirements and seventeen active unit-test obligations; no lifecycle
    authority or product component is added.
21. **Accepted 2026-08-20:** the first audience-visible resource proof uses a
    prepared bounded CPU-load profile inside the actual Tire Health service
    instance. AosCore/Service Manager remains the sole in-vehicle enforcement
    and monitoring authority and caps Tire at its independently approved
    quota; Brake Health is the control tenant and must remain ready and process
    the deterministic CARLA event while the shared platform remains healthy.
    No project resource manager is introduced. Mac-local functional backends
    and aggregate quota enforcement across multiple services owned by one
    Service Provider are outside this proof. `CR-DEMO` 0.3 adds
    `REQ-DEMO-021` and `UT-DEMO-019` and now contains twenty active
    requirements and eighteen active unit-test obligations.

    D4-023.3 further assigns the single `Start CPU Isolation Proof` control to
    the Tire Function Dashboard and Mac-local Tire backend. The actual Tire
    instance obtains only fixed idempotent start/stop commands over its
    existing outbound backend route, bound to current Unit, Service version,
    artifact digest and fixed profile. The in-instance worker shares the
    Aos-managed cgroup, has a 180-second absolute ceiling and never persists or
    resumes across Service/VM restart. No SSH/exec/signal/admin fallback is
    permitted, and Function Team status is not quota-enforcement evidence.

22. **Proposed 2026-08-22:** HLA 1.5 and ADR 0013 separate factory-installed
    unmodified `CMP-KUKSA`, transitional `CMP-KAC` and FOTA-owned `CMP-VDP`.
    Service JWT issuance moves to `CR-KAC`; Services use fixed-resource
    bootstrap and then connect directly to KUKSA. The VDP is an OEM-qualified
    trusted platform component, so former dynamic Provider-credential
    requirements/interfaces are retired without claiming malicious-Provider
    containment. Acceptance is pending the complete C3 review.
23. **Accepted 2026-08-22:** D4-011 keeps the three artifact-publication
    profiles and introduces one separate non-publication `oem-delivery`
    operational context. Owning teams retain engineering acceptance;
    `oem-delivery` performs the explicitly confirmed Verification Batch, Fleet
    Validation, Campaign and Subject-service lifecycle mutations after
    `/users/me/` role/effective-permission preflight. The Dashboard suppresses
    duplicate clicks but claims no server idempotency and reconciles every
    ambiguous response from authoritative AosCloud state. This refines
    `CMP-SW-DASH` and `IF-LC-005`/`008`–`010` without adding an HLA component,
    repository or lifecycle state authority.
24. **Accepted 2026-08-22:** D4-015 refines lifecycle and retirement behavior
    without adding a component or interface. `CR-AOS` owns qualification of
    Subject-service removal, pre-Apply `RevertUpdate`, post-Apply signed
    forward repair, offline-only deprovision, exact Unit Set removal, Unit
    deletion and Unit-owned Node disappearance. `CR-DEMO` owns dependent-first
    orchestration, post-mutation reconciliation and the no-blind-retry guard.
    API v11 exposes no standalone Node-delete operation and none is invented.
25. **Accepted 2026-08-22:** D4-016.1 freezes the existing `CMP-BHS` v1
    acquisition behavior inside `CR-BHS`: six VDP v1 inputs, deterministic
    10 Hz sampling, the `HARD_BRAKING_EPISODE_V1` trigger, fixed 3/10/2-second
    window bounds, terminal states and the eight-window/4 MiB queue boundary.
    D4-016.2 freezes the existing `IF-FUNC-001` v1 logical chunks/completion,
    64 KiB canonical-message limit, hashes/idempotency and crash-safe
    service-local filesystem spool. It adds no component, interface,
    repository or database runtime. D4-017 proposes isolated local delivery
    and exact durable backend acknowledgement. Production functional-backend
    authentication remains Function Team 1-owned and outside the first demo.
26. **Accepted 2026-08-25:** the Level-B interaction cascade preserves the
    existing component graph, repositories, interfaces and authority model but
    replaces the over-broad demo-wide external-mutation lock. `CMP-SW-DASH`
    and `CMP-ORCH` now keep a bounded per-operation recovery registry and block
    only exact overlapping release resources. Platform, Brake and Tire may
    operate independently on disjoint resources; provisioning, identity
    retirement, live-source handover/reset and R0 remain run-exclusive.
27. **Accepted 2026-08-26:** D4-026.17 assigns the physical composed workspace
    to `CMP-ORCH` and its trusted Presenter Launcher, while `CMP-SW-DASH` owns
    the stateless shared-header meaning and team navigation from the existing
    browser read model. `IF-DEMO-002` records this measured local composition,
    visibility/readability and safe restoration contract. Surface owners keep
    their content, and no new HLA component, repository, Cloud/vehicle/release
    authority, browser embedding or second state store is introduced. The
    exact macOS window mechanism remains implementation qualification under
    `CR-DEMO` 0.9.
28. **Accepted 2026-08-26:** D4-026.18 and `CR-DEMO` 1.0 assign the
    title-selected global Demo Lifecycle page to the existing stateless
    `CMP-SW-DASH` right-hand browser workspace. It composes bounded
    Qualification Status, M0/M1/G0, current lifecycle/recovery and R0 while
    fixed vehicle-evidence surfaces remain visible. It is not a fourth
    producer, duplicates no native Presenter Launcher action and adds no HLA
    component, interface, repository, Cloud authority or state store.
29. **Accepted 2026-08-26:** D4-026.19, `CR-DEMO` 1.1 and `CR-E2E` 0.8
    refine the existing `CMP-SW-DASH` right-hand team perspectives. The compact
    team purpose, OEM Release Authority, current-state summaries and applicable
    team evidence remain fixed while only the release/version region scrolls;
    each producer perspective restores its own release scroll/focus. This
    Level-A presentation change adds no component, interface, repository,
    authority, lifecycle state or system requirement.
30. **Accepted 2026-08-27:** D4-026.20 standardizes the existing browser-owned
    presenter surfaces on the accepted lightweight icon vocabulary while the
    native Engineering Telematics Dashboard remains a terminal and uses a
    plain text label rather than injected HTML imagery. The change refines
    only presentation of existing `CMP-SW-DASH`, `CMP-ORCH` and
    `CMP-ENG-DASH` responsibilities; it adds no component, interface,
    repository, authority, lifecycle state or system requirement.

## Acceptance Record and Delta for Version 2.0

Version 2.0 preserves the accepted vehicle, Cloud, FOTA/SOTA, functional and
dashboard decomposition from Version 1.1. It adds transitional `CMP-KAC` and
`CR-KAC`, retires `IF-AUTH-001` through `IF-AUTH-006`, introduces
`IF-AUTH-007` through `IF-AUTH-010`, removes Service JWT issuance from VDP,
and records the explicit OEM-trusted Provider integration assumption. No
repository is created, no external system is mutated and no future native
AosCore interface is invented.

D4-010.3 further refines the existing publication interfaces without adding a
component: one common session-scoped native-helper implementation exposes
three non-interchangeable profiles (`platform-oem`, `brake-sp1`, `tire-sp2`).
The installed `aos-signer` 2.0.1 compatibility path reads one host-local
mode-`0600` passwordless PKCS#12 per profile for signing and mTLS upload; those
credentials remain outside Git, browsers, containers, VM images and
deployable artifacts. Technical publication remains separate from the
authorized OEM decision on `IF-LC-008` through `IF-LC-010`.

D4-011 further fixes that authorized OEM decision as a separately
authenticated `oem-delivery` context with exact public endpoint, role,
permission, failure and authoritative-reconciliation semantics. It adds no
publication profile and no dashboard-owned lifecycle state.

D4-015 further fixes recovery and retirement semantics: dependent SOTA is
removed first; FOTA may revert only before `ApplyUpdate` and uses a new signed,
VU-qualified forward-repair release afterward. R0 removes exact `system_uid`
memberships before Unit deletion and proves Unit-owned Nodes inaccessible
without inventing a Node-delete API. Live two-Unit qualification remains open.

The 2026-08-25 Level-B revalidation adds `SYS-REL-012` and `CR-DEMO` 0.8
without adding a component, interface, repository or authority. It replaces a
local global-lock simplification with exact resource-scoped coordination and a
bounded per-operation recovery registry; run-wide destructive and source
operations remain exclusive.

The 2026-08-26 workspace-ownership revalidation adds `IF-DEMO-002` and
`CR-DEMO` 0.9 without adding an HLA component, repository or authority.
`CMP-ORCH` owns measured physical window composition and local restoration;
`CMP-SW-DASH` owns only shared-header meaning and navigation from its existing
stateless read model. Native/browser surface content remains with its original
owner, and workspace readiness never becomes Cloud or vehicle lifecycle truth.

The 2026-08-26 global-lifecycle revalidation adds `CR-DEMO` 1.0 and extends
the existing `CMP-SW-DASH`/`CMP-ORCH` allocation without adding an interface.
The shared title navigates only the right browser region to Qualification,
M0/M1/G0, lifecycle/recovery and R0; native launcher preflight/layout actions
and all authoritative state owners remain unchanged.

The 2026-08-26 team-context revalidation adds `CR-DEMO` 1.1 and synchronizes
`CR-E2E` 0.8 without changing the component/interface register. Existing
`CMP-SW-DASH` ownership now explicitly covers fixed team context and
version-only scrolling at the qualified presenter viewport; all product,
authority, source and lifecycle boundaries remain unchanged.

The complete Version 2.0 register cascade was accepted on 2026-08-26. Its
acceptance records component/interface ownership only; implementation,
qualification and external mutation remain separately gated.

The 2026-08-28 native-IAM transport correction refines existing `CMP-KAC` and
`IF-AUTH-008` only. It records the released fixed TLS loopback
`127.0.0.1:8090` client path and explicit denial of DNS, external IP and a KAC
TCP listener; it adds no component, interface, repository or authority.

## Acceptance Record for Version 1.1

Version 1.1 preserves the Version 1.0 graph and adds no component, interface,
repository or authority. It updates the `CR-CROSS` allocation for
[`SYS-OBS-007`](system-requirements-and-traceability.md#sys-obs-007): one
stateful demo control interrupts the Production Unit's AosCloud and
functional-backend paths together while keeping presenter-to-AosCloud and the
simulated in-vehicle network available. It also allocates
[`SYS-RES-001`](system-requirements-and-traceability.md#sys-res-001) across
`CR-AOS`, `CR-BHS`, `CR-TIRE`, `CR-DEMO`, `CR-CROSS` and `CR-E2E` without
adding a component, interface, repository or authority: AosCore caps the Tire
service CPU quota while Brake and the platform graph remain healthy.

## Acceptance Record for Version 1.0

Version 1.0 preserves the accepted component graph, repository boundaries and
interface identifiers. It expands `CMP-BRAKE-DASH` and `CR-BRAKE-CLOUD` with
the accepted prepared-candidate view, protected delegated publication, native
ARM64 local-demo container, persistent functional data and native macOS
helper. The earlier Keychain-only implementation assumption is superseded by
D4-010.3. `CMP-BRAKE-BE` remains authoritative only for functional
data; AosCloud and the OEM Software Delivery Dashboard retain lifecycle state,
targeting, approval, deployment and promotion authority.

The accepted Tire Health clarification preserves the same component and
interface graph: `CMP-TIRE` has one v1.0 candidate on VDP v3. Brake Health owns
the multi-version evolution story; Tire Health owns the independent second-
provider lifecycle story. `CMP-TIRE-DASH` and `CR-TIRE-CLOUD` add the accepted
prepared-candidate view, protected delegated publication, real bounded-result
presentation, Mac-local ARM64 container, dedicated persistent data and native
macOS helper without changing HLA ownership or authority. The helper's
current-release credential custody is defined by D4-010.3 rather than by the
earlier Keychain-only assumption.

The accepted Platform release clarification also preserves the same component
and interface graph. `CMP-SW-DASH` now explicitly presents the prepared VDP
v1-v3 catalogue and delegates protected publication over `IF-LC-001`; it owns
neither signing keys, the Platform Team release decision, OEM Unit approval nor
AosCloud lifecycle state. The register was revalidated against Demo Scenario
1.8 and Architecture Flows 1.7 without adding a component, interface or
repository.

The accepted Demo Orchestration 0.3, Cross-Cutting Security and Operations 0.1
and End-to-End Acceptance 0.1 packages close D3 group 6. They preserve the
accepted graph and authority boundaries while defining safe run setup,
authoritative Cloud presentation, evidence-backed lifecycle controls,
sequential VU/PU use, one atomic vehicle-external-connectivity button, one
AosCore-enforced Tire CPU isolation proof, ordered R0 retirement and the
complete acceptance-state/evidence model. Exact machine-readable assertions,
thresholds, tolerances and qualification procedures remain D4 work; this
acceptance authorizes no implementation or external mutation.

## Acceptance Record for Version 0.9

Version 0.9 preserves the accepted component graph and repositories. It
clarifies `CMP-BHS`, `CMP-BRAKE-BE`, `CMP-BRAKE-DASH`, `CR-BHS`,
`CR-BRAKE-CLOUD`, `IF-FUNC-001`, and `IF-FUNC-002` for the v1 event-window and
v2/v3 derived-message family. These are contract refinements inside the
existing Function Team 1 direction and authority, not new interfaces or
components.

## Acceptance Record for Version 0.8

Version 0.8 preserves the accepted Version 0.7 component graph and clarifies
the retirement boundary. `CR-AOS` owns qualification of authoritative
deprovisioning, deletion, Unit Set state and membership APIs. `CR-DEMO` owns
VM shutdown, ordered API use, partial-result reconciliation, overlay disposal,
next-run provisioning, new identity binding and fresh lifecycle-object guards.
`CR-E2E` proves the complete `R0 -> M0 -> M1` cycle.

No HLA component or interface is added by Version 0.8.

## Acceptance Record for Version 0.7

Version 0.7 preserves the accepted Version 0.6 component graph, strengthens
`CMP-GW-ADV` and `IF-ADV-004` as the authoritative QM boundary, and expands
`CMP-SW-DASH` and `IF-LC-005` to expose the evidence dossier preceding final
OEM approval.

The baseline was accepted on 2026-08-19 after reviewers confirmed:

1. every HLA 1.4 box has exactly one primary component owner;
2. every audience-visible dashboard has exactly one authoritative data source;
3. the three independent FOTA/SOTA lifecycles remain separated;
4. Function Team 1 and Function Team 2 are peer product domains;
5. `VU` and `PU` remain runtime roles rather than duplicated component sets;
6. current, engineering-evidence, target, external and deferred states are not
   presented as equivalent;
7. all runtime, functional Cloud, lifecycle and observability boundaries needed
   by Scenario 1.5, including the `T1` Function Team 2 stage, have interface
   IDs;
8. deferred native Cloud dependency admission and the not-yet-implemented
   Credential Broker are not presented as current behavior;
9. no component claims a production driver HMI, continuous raw-telemetry Cloud
   stream, third-party Service Provider, Fleet Operator or production fleet;
10. the provisional requirement packages can be expanded without changing HLA
    1.4 or the accepted demo scenarios.
11. team-owned release decisions, Service Provider publication, OEM-authorized
    deployment approval, AosCloud state/execution, and stateless demo tooling
    remain distinct as required by
    [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md).
12. Service Manager and Aos IAM own SOTA instance identity, `AOS_SECRET` and
    registered permissions; the VDP broker has no parallel identity or
    per-service policy store.
13. the Factory Image supplies one IAM configuration with
    `enablePermissionsHandler: true` independent of provisioning state, no
    pre-populated service permission or `AOS_SECRET`, and a non-secret
    signing-key seam, while per-Unit key material and static tokens remain
    outside immutable artifacts.
14. both functional services remain QM and no component treats IAM/KUKSA
    permissions as a safety case or bypasses authoritative Gateway
    containment; and
15. OEM approval remains an explicit final decision after evidence review,
    never an automatic result of tests or a Dashboard-owned state transition.

Component requirements are written and reviewed package by package. The
[component-package index](components/README.md) is authoritative for the exact
review state of each current version: an accepted earlier baseline does not
silently accept a later security or exact-contract delta. `CR-DEMO` 1.1 and
`CR-E2E` 0.8 are D3 design-reviewed; the latest Factory, KAC, VDP, Aos, Tire
and Cross-Cutting deltas keep their explicit package gates. Each requirement
shall cite a named and linked parent System Requirement, Architecture Flow and
interface, plus a verification method and retained evidence. Implementation
planning may proceed, but an increment starts only after its exact package and
acceptance-test inputs are reviewed and explicitly authorized.
