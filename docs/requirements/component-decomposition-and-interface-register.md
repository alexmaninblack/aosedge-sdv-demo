<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Decomposition and Interface Register 2.3

- Status: Accepted
- Version: 2.3
- Prepared: 2026-08-22
- Accepted: 2026-09-27
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.8](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 2.2](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 2.3](../architecture/demo-scenario-architecture-flows.md)
- Requirements input: [System Requirements and Traceability 2.3](system-requirements-and-traceability.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0011](../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md),
  [ADR 0013](../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md),
  [ADR 0014](../architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Document approval alone authorizes no implementation, publication or live mutation.

## Installed workstation allocation

The existing [Demo Orchestrator](#cmp-orch) owns the local installation and
instance-path selection adapter for [separate installed data authority](system-requirements-and-traceability.md#sys-dist-001).
It reuses the existing lifecycle and presentation interfaces; it does not
introduce a second VM/Cloud controller or a vehicle wire protocol. The private
instance marker and separate input/output roots are specified by the
[installed-state contract](../../contracts/distribution-installation/installed-state.md).
The package-store transaction has no runtime readiness authority.

The same adapter owns the [version-selection/recovery detail](../../contracts/distribution-installation/version-selection.md).
Instance selection and package-use leases introduce no vehicle wire interface
or independent controller; destructive removal and native activation remain gated.

| Parent obligation | Allocation | Derived package |
| --- | --- | --- |
| `SYS-DIST-001` | `CMP-ORCH`, `IF-DEMO-001` | `REQ-DEMO-025` |

<a id="current-implementation-view--24-september-2026"></a>
## Current implementation view

Factory owns KUKSA integration and its documented scope-path/source-timestamp
compatibility patches. These do not transfer authority to a service.
See the [implementation map](../architecture/current-implementation.md).

Current package selection and qualification are owned by the launcher catalog and
[current baseline](../qualification/current-baseline.md).
[Implemented architecture and traceability](../architecture/current-implementation.md) maps
the effective requirements, protocols, component owners and proof.
Full acceptance still requires the explicitly outstanding tests; this view
does not change stable IDs or grant deployment authority.

<a id="native-service-input-amendment--2026-09-11"></a>
## Native service input allocation

[ADR 0015](../architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
changes application provenance and credential placement, not component ownership
or interface direction. Demo Control projects public Unit/VDP/trust inputs;
packages carry releases; native Aos supplies instance identity. Private token
sessions use the existing resource without an SM ownership extension.
The [input contract](../architecture/demo-control-service-inputs.md) owns exact
package/native provenance and public/private placement. Interface rows below
use those current meanings; legacy message formats retain separate decoders.

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

1. High-Level Architecture 1.8 owns system boundaries, authorities and
   invariants.
2. Demo Scenario 2.2 owns the audience-visible lifecycle and stage sequence.
3. Architecture Flows 2.3 owns detailed runtime, lifecycle, observability and
   failure flows.
4. System Requirements 2.3 owns normative `SYS-*` obligations and gap
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

The installed Test is one instance of the Domain Controller graph. The
expanded profile adds an independent Production instance of that same graph. They are roles in the demo lifecycle, not
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

Updated implementation columns: 24 September 2026. `SCOPED` means behavior
exists and has bounded source/live evidence, not full acceptance of every
listed responsibility. `PARTIAL` / `EXTEND` retain unmet obligations. Read
[implementation traceability](../architecture/current-implementation.md)
before interpreting historical D3 allocation states in downstream packages.

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
| <a id="cmp-carla"></a>`CMP-CARLA` | CARLA Virtual Physical Vehicle | Vehicle dynamics, road environment, versioned installed-hardware capability manifest, native sensor state and actuators | Vehicle simulation | `CarlaSim`; restricted Unreal dependency remains separate | `CURRENT`; full installed-hardware qualification remains scoped |
| <a id="cmp-scene"></a>`CMP-SCENE` | Deterministic Scenario Controller | Repeatable obstacle/braking stimulus, explicit free-drive/brake-event context, context-aware mode transition/reset, actor cleanup, and accelerated/pre-aged tire-degradation stimulus | Demo vehicle tooling | `carla-ego-runtime` | `CURRENT / SCOPED`; Brake/Tire maneuvers implemented; full calibration matrix open |
| <a id="cmp-control"></a>`CMP-CONTROL` | Vehicle Control UI | Manual/autopilot selection, throttle, brake, steering and safe-stop commands over the separate control channel | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT` |
| <a id="cmp-gw"></a>`CMP-GW` | Vehicle Gateway Runtime | Complete CARLA hardware-profile accounting, control arbitration, applied-control feedback, signal normalization and Gateway health/state | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / EXTEND`; current signal path implemented; full hardware/actuator scope separate |
| <a id="cmp-viss"></a>`CMP-VISS` | Vehicle Gateway VISS 3.1 Server | TLS-protected VSS Get/Subscribe and the narrowly scoped typed advisory Set contract | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / SCOPED`; strict Test trust and typed advisory Set implemented |
| <a id="cmp-gw-adv"></a>`CMP-GW-ADV` | Gateway QM-Channel Advisory Handler | Act as the final authoritative boundary for the QM-origin channel: validate typed non-safety Brake/Tire advisories, deny arbitrary VSS and motion/safety-critical operations, and publish factual reception/status without claiming driver display | Vehicle Gateway tooling | `carla-ego-runtime` | `CURRENT / SCOPED`; typed validation, lease and status implemented |
| <a id="cmp-eng-dash"></a>`CMP-ENG-DASH` | Engineering Telematics Dashboard | Independent read-only engineering view of Gateway telemetry, drive-mode/world-context/reset facts and typed advisory/status evidence | Demo engineering tooling | `carla-ego-runtime` | `CURRENT / SCOPED`; combined native telemetry/control and advisory |

`CMP-SCENE`, `CMP-CONTROL`, and `CMP-ENG-DASH` are demonstration tools. They
must remain outside the logical production vehicle architecture even though
they interact with its simulated boundaries.

### Domain Controller substrate and Vehicle Data Platform

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-factory"></a>`CMP-FACTORY` | OEM Factory Baseline Assembly | Reproducibly compose, build, qualify and freeze the unprovisioned SOP substrate, including one stock Aos IAM configuration with `enablePermissionsHandler: true`, factory-installed Factory-owned KUKSA, separately packaged removable `CMP-KAC`, no pre-populated Service authority/secret state, and dedicated non-secret `kuksa-jwt` signer/verifier preparation wiring without a key, JWT or shared production verifier | Platform Team; pre-SOP manufacturing/build lifecycle | Integration recipes and qualification inputs in `aos-vehicle-platform`; output image remains outside Git | `IMPLEMENTED`; Controller image and installed API/UI profiles have scoped evidence in the current baseline; the complete requirement matrix remains open |
| <a id="cmp-runtime"></a>`CMP-RUNTIME` | Provider-Specific Empty-Slot Runtime | Preinstalled OEM Service Manager runtime, bounded provider slot, health/storage boundary and Safe Stop application gate for the Vehicle Data Platform payload; owns durable transaction metadata and asynchronous bounded waiting/recovery, consumes fresh monotonic Gateway frames through a purpose-bound mTLS `VehicleStateProviderItf`, and never persists Safe Stop samples | Platform Team; factory image | `aos-vehicle-platform` | `CURRENT / SCOPED`; FOTA and retained-component boot recovery implemented |
| <a id="cmp-aos-core"></a>`CMP-AOS-CORE` | AosCore and Service Manager | Unit identity, desired state, security, update lifecycle, service execution and status | AosEdge platform | External AosVM/AosCore release | `EXTERNAL / CURRENT` |
| <a id="cmp-kuksa"></a>`CMP-KUKSA` | Eclipse KUKSA Databroker | Stable factory-installed in-vehicle VSS resource server, direct authorized Service access and verification of short-lived Service JWTs using the configured per-Unit public verifier | External Eclipse component in the SOP substrate; Platform Team governs integration and exposed contract | Unmodified external executable; configuration/contract in `aos-vehicle-platform` | `CURRENT`; real VDP data and authorized service access have scoped .39 proof |
| <a id="cmp-kac"></a>`CMP-KAC` | Current-Release KUKSA Authorization Compatibility Helper | Separately packaged removable platform helper reached by Services only through a named-resource-mounted private Unix socket; it accepts the bootstrap's instance-bound `AOS_SECRET` for implicit resource `kuksa`, resolves active permissions through the released Aos IAM public gRPC interface using fixed TLS loopback `127.0.0.1:8090`, maps only `r -> read` and `rw -> actuate`, signs through the protected per-Unit key, returns a 300-second JWT with renewal at 180 seconds, uses UTC claims plus boottime scheduling, and enforces the accepted bounded/redacted process envelope. Its exact volatile paths, private systemd PIN delivery, pinned SoftHSM/OpenSSL token path and separate least-privilege KAC/verifier-preparation SELinux domains are factory-owned current-demo integration; it starts empty after verifier/time reconstruction on reboot and owns no persistent state, parallel identity/policy database, shared token directory, TCP listener, external IP access or functional data path | Platform Team; factory/system integration for the current AosCore release | `aos-vehicle-platform/authorization/aos-kuksa-compat/`; separate `aos-kuksa-auth-compat` package/unit, outside VDP and SOTA payloads | `IMPLEMENTED / TRANSITIONAL`; scoped real renewal/offline proof on .39 |
| <a id="cmp-vdp"></a>`CMP-VDP` | Vehicle Data Platform Component | OEM-trusted privileged VISS client, signal selection, validation, normalization, KUKSA actual-value publication, versioned contract and defense-in-depth allowlisted outbound QM advisory path; Provider-side KUKSA connectivity is fixed Platform Team integration and Service JWT issuance is excluded | Platform Team; independent FOTA | `aos-vehicle-platform` | `CURRENT / SCOPED`; V1–V3 artifacts delivered, fresh serial .39 qualification open |

`CMP-RUNTIME` is provider-specific and hosts one bounded component type. This
register makes no claim that the current runtime is a generic arbitrary
component runtime.

### Function Team 1 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-bhs"></a>`CMP-BHS` | Brake Health In-Vehicle Service | QM-domain maintenance application: v1 records bounded pre/active/post braking-event windows, v2 performs synthetic local assessment and sends derived events, and v3 requests only the typed non-safety advisory; no safety goal or motion authority | Function Team 1 / Service Provider 1; SOTA 1 | `brake-health-service` | `CURRENT / SCOPED`; V1–V3 runtime, products and V3 advisory |
| <a id="cmp-brake-be"></a>`CMP-BRAKE-BE` | Brake Health Backend | Idempotently reconstruct and persist v1 event windows, ingest v2/v3 derived assessments/events/advisory facts, and expose the Function Team API | Function Team 1; functional Cloud product | `brake-health-cloud` | `CURRENT / SCOPED`; ingestion/query/reset/cleanup and live receipts |
| <a id="cmp-brake-dash"></a>`CMP-BRAKE-DASH` | Brake Health Function Dashboard | Host separated Vehicle Data, Release Candidates and Service Logs views: present v1 growing/completed windows and v2/v3 derived data only from the backend; present immutable prepared v1-v3 candidate purpose/digests/permissions/quotas/compatibility and delegate explicit sign/publish actions; and request/present only SP1-owned service-instance/crash logs through a separate operational context without owning keys, OEM approval, Unit lifecycle state or a second log archive | Function Team 1; functional Cloud product | `brake-health-cloud` | `PARTIAL`; live integrated Presenter implemented; standalone fixture/log scope not fully live |

The backend and dashboard are not part of the in-vehicle SOTA artifact and do
not participate in the time-critical local advisory decision.

### Function Team 2 product domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-tire"></a>`CMP-TIRE` | Tire Health In-Vehicle Service | One mature v1.0 QM-domain maintenance product on accepted VDP v3: maintain a bounded persistent tire-condition estimate, create bounded reports/events, and request only the typed non-safety inspection advisory; no safety goal or motion authority | Function Team 2 / Service Provider 2; SOTA 2 | `tire-health-service` | `CURRENT / SCOPED`; functional V1 analysis/advisory |
| <a id="cmp-tire-be"></a>`CMP-TIRE-BE` | Tire Health Backend | Idempotent condition-summary/event ingestion, persistence and API | Function Team 2; functional Cloud product | `tire-health-cloud` | `CURRENT / SCOPED`; separate ingestion/query/reset/cleanup |
| <a id="cmp-tire-dash"></a>`CMP-TIRE-DASH` | Tire Health Function Dashboard | Host separated Vehicle Data, Release Candidates and Service Logs views: present condition/event/version/delivery facts only from the Tire Health backend; present the one immutable v1.0 candidate and delegate explicit sign/publish actions; expose the fixed D4-023.3 Tire CPU-isolation proof control through its backend; and request/present only SP2-owned service-instance/crash logs through a separate operational context without owning keys, OEM approval, Unit lifecycle state, quota authority or a second log archive | Function Team 2; functional Cloud product | `tire-health-cloud` | `PARTIAL`; live Presenter views; standalone dashboard and CPU proof not implemented |

Function Team 2 is a peer of Function Team 1. Its service, backend, dashboard,
identity and SOTA lifecycle must not be placed inside the Brake Health product
or routed through it.

### Software delivery, operations and demo domain

| ID | Component | Responsibility | Owner and lifecycle | Source boundary | State |
| --- | --- | --- | --- | --- | --- |
| <a id="cmp-aos-cloud"></a>`CMP-AOS-CLOUD` | AosCloud Lifecycle Control Plane | Provisioning, authoritative Unit/Node desired and reported actual state, batches, campaigns, recorded approvals, audit history, FOTA/SOTA delivery and promotion execution | AosEdge platform / OEM Cloud | External AosCloud service | `EXTERNAL / CURRENT`; exact demo operations require qualification |
| <a id="cmp-sw-dash"></a>`CMP-SW-DASH` | OEM Software Delivery Dashboard | Stateless Platform Releases catalogue and protected publication delegation for prebuilt VDP candidates, including exact Factory Image/runtime compatibility and distinct prepared/signed/AosCloud identities, plus authoritative AosCloud lifecycle and OEM-scoped Unit system/VDP log state, exact artifact/metadata digests, requested permissions, target, evidence status, owning-team acceptance and active D4-011 `oem-delivery` role/effective permissions; own the shared-header title, Current Vehicle/team-summary projection and perspective navigation from the same browser read model; expose only explicitly confirmed actions and then re-read Cloud state | Demo solution | `aosedge-sdv-demo` | `CURRENT / EXTEND`; Studio Cloud/software/resources and publication; full formal coverage/log scope separate |
| <a id="cmp-orch"></a>`CMP-ORCH` | Demo Orchestrator | Factory-overlay creation, role binding, provisioning reconciliation, sequential exclusive live CARLA source handover, release sequencing, transient evidence correlation, retirement and reset without owning lifecycle state or approval decisions; its trusted macOS launcher starts and supervises the non-root session-scoped native helper boundary and owns measured physical header/native/browser window composition, visibility/readability proof and safe local layout restoration without owning surface content; telemetry replay is deferred | Demo solution | `aosedge-sdv-demo` | `CURRENT / EXTEND`; shared commands, lifecycle and ignition recovery; host sleep/wake planned |

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
| `tire-health-service` | `CMP-TIRE` | Implemented Function Team 2 in-vehicle SOTA source; functional V1. |
| `brake-health-cloud` | `CMP-BRAKE-BE`, `CMP-BRAKE-DASH` | Implemented team backend/API/container and retained standalone fixture shell. The integrated live Presenter consumes its API from the solution repository; protected signing credentials remain host-local. |
| `tire-health-cloud` | `CMP-TIRE-BE`, `CMP-TIRE-DASH` | Implemented independent team backend/API/container; integrated audience views are in Presenter. No standalone live dashboard or CPU-load endpoint is claimed. |
| `aosedge-sdv-demo` | `CMP-SW-DASH`, `CMP-ORCH`, cross-component contracts, qualification and system documentation | Solution integration; must not absorb component product source. |
| AosEdge/AosCloud | `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, including native system/service/crash-log collection, Cloud delivery and storage | External platform dependency. |

The [current repository map](../../workspace/repository-map.json) describes
maintenance ownership. Accepted design alone creates no repository or source
revision. Frozen selected-build pins remain separate and unchanged.

## Runtime Data Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-veh-001"></a>`IF-VEH-001` | `CMP-CARLA` | `CMP-GW` | Vehicle Hardware Capability Manifest plus frame-coherent state and availability for every installed hardware-equivalent signal/sensor; excludes qualification-only ground truth | CARLA runtime state and accepted hardware profile | Existing subset `CURRENT`; complete manifest/accounting `EXTEND` |
| <a id="if-veh-002"></a>`IF-VEH-002` | `CMP-CONTROL` | `CMP-GW` | Authenticated manual/autopilot/safe-stop control request | Gateway control state | `CURRENT` |
| <a id="if-veh-003"></a>`IF-VEH-003` | `CMP-GW` | `CMP-CARLA` | Commands for every actuator declared in the selected hardware profile, with accepted/rejected execution status and applied-control state returning through `IF-VEH-001` | Gateway control arbitration; CARLA applied state | Throttle/brake/steer `CURRENT`; complete declared set/status `EXTEND` |
| <a id="if-veh-004"></a>`IF-VEH-004` | `CMP-GW` | `CMP-VISS` | Normalized VSS signal model and source status | Gateway VSS projection | `CURRENT / EXTEND` |
| <a id="if-veh-005"></a>`IF-VEH-005` | `CMP-VISS` | `CMP-VDP` | TLS VISS 3.1 Get/Subscribe for accepted telemetry and status paths | Gateway VISS contract | `CURRENT / SCOPED`; strict VISS telemetry to profile-bound VDP |
| <a id="if-veh-006"></a>`IF-VEH-006` | `CMP-VISS` | `CMP-ENG-DASH` | Independent read-only telemetry and Gateway-status subscription | Gateway VISS contract | `CURRENT / SCOPED`; telemetry and advisory status |
| <a id="if-veh-007"></a>`IF-VEH-007` | `CMP-VISS` | `CMP-RUNTIME` | Distinct purpose-bound per-Unit `PLATFORM_UPDATE_RUNTIME` mTLS role with one connection and only ten read-only Safe Stop paths: monotonic `FrameId`, applied control mode, transition/reset generation and discontinuity, factual speed, throttle and brake with freshness semantics. The six control/reset facts form one atomic group only after the Gateway joins the controller record to the physical snapshot by exact CARLA frame ID and simulation time; missing, invalid, duplicate, out-of-order, expired or overflowed handoff input omits that entire group for the frame, never reuses prior values and therefore cannot be interpreted as Safe Stop evidence | Gateway is physical-state authority and frame-coherence authority; OEM Component Runtime evaluates the accepted Safe Stop policy. The local four-record/250-ms join bound is transport tolerance, not Runtime freshness policy | `CURRENT / SCOPED`; framed handoff, selected identity and runtime Safe Stop; Test timing amendment applies |
| <a id="if-data-001"></a>`IF-DATA-001` | `CMP-VDP` | `CMP-KUKSA` | Validated actual values, availability, freshness and provenance | Versioned Vehicle Data Platform contract | `CURRENT / SCOPED`; real KUKSA publication with quality/freshness |
| <a id="if-data-002"></a>`IF-DATA-002` | `CMP-KUKSA` | `CMP-BHS` | `kuksa.val.v1` read/subscribe subset for Brake Health; v2/v3 supplies the accepted twelve paths with source unit/time/quality, followed by one adapter-owned normative-unit conversion and fixed-point quantization before the model core | Vehicle Data Platform path/unit/freshness contract; Brake model owns conversion rejection and fixed-point boundary | `CURRENT / SCOPED`; Brake profile-specific input validation and processing |
| <a id="if-tire-001"></a>`IF-TIRE-001` | `CMP-KUKSA` | `CMP-TIRE` | `kuksa.val.v1` read/subscribe dynamics subset for tire-condition estimation | Vehicle Data Platform contract | `CURRENT / SCOPED`; Tire V1 consumes actual VDP V3 dynamics |
| <a id="if-adv-001"></a>`IF-ADV-001` | `CMP-BHS` | `CMP-KUKSA` | Typed QM Brake Health maintenance-advisory write/actuate request | Brake Health request constrained by IAM and platform contract; no safety/motion authority | `CURRENT / SCOPED`; only Brake typed request |
| <a id="if-tire-002"></a>`IF-TIRE-002` | `CMP-TIRE` | `CMP-KUKSA` | Typed QM Tire Health inspection-advisory write/actuate request | Tire Health request constrained by IAM and platform contract; no safety/motion authority | `CURRENT / SCOPED`; only Tire typed request |
| <a id="if-adv-002"></a>`IF-ADV-002` | `CMP-KUKSA` | `CMP-VDP` | Advisory target change plus caller authorization context | Vehicle Data Platform outbound contract | `CURRENT / SCOPED`; authenticated typed outbound bridge |
| <a id="if-adv-003"></a>`IF-ADV-003` | `CMP-VDP` | `CMP-VISS` | Narrow VISS Set request for the accepted QM advisory target | Platform outbound defense-in-depth allowlist | `CURRENT / SCOPED`; exact allowlisted VISS Set |
| <a id="if-adv-004"></a>`IF-ADV-004` | `CMP-VISS` | `CMP-GW-ADV` | Restricted QM-origin advisory delivery | Authoritative Gateway deny-by-default contract | `CURRENT / SCOPED`; Gateway-correlated factual advisory status |
| <a id="if-adv-005"></a>`IF-ADV-005` | `CMP-GW-ADV` | `CMP-VISS` | Factual received/rejected/status signal | Gateway state | `CURRENT / SCOPED`; native observation independent of backend delivery |
| <a id="if-auth-007"></a>`IF-AUTH-007` | `CMP-BHS` / `CMP-TIRE` compatibility bootstrap | `CMP-KAC` | Strict `aos-kuksa-auth-compat/v1` `status` or `issue` over private `request.sock`; `issue` carries only current instance `AOS_SECRET`; implicit fixed `kuksa` resource; one LF-terminated JSON request/response per connection | Aos IAM is authoritative; strict schema plus named resource, group and Unix peer credentials are defense in depth | `CURRENT / TRANSITIONAL`; private fixed-resource KAC exchange |
| <a id="if-auth-008"></a>`IF-AUTH-008` | `CMP-KAC` | `CMP-AOS-CORE` IAM | Native `GetPermissions(AOS_SECRET, fixed-resource)` through fixed TLS loopback `127.0.0.1:8090`, Aos CA trust and expected server name `main`, returning active Service identity and registered path/mode permissions or rejection; no DNS, caller-selected endpoint or external IP | Service Manager registration and current Aos IAM state | `CURRENT / SCOPED`; native IAM permission lookup; full negative matrix separate |
| <a id="if-auth-009"></a>`IF-AUTH-009` | `CMP-KAC` | requesting `CMP-BHS` / `CMP-TIRE` compatibility bootstrap | Strict `ready`, `issued` or `rejected` response; only `issued` carries a 300-second JWT and renewal-at-180-second instant; only fixed error codes and KAC-generated correlation; bootstrap atomically maintains `/run/aosedge/secrets/kuksa/session-<random>/token.jwt`, then reconnects/recreates KUKSA subscriptions with each replacement token and starts analytics without `AOS_SECRET` | Aos IAM result plus non-widening `r -> read`, `rw -> actuate` mapping; no caller correlation, `w`, wildcards, provider actions, free-text error, parallel Service policy store or shared host token directory | `CURRENT / TRANSITIONAL`; private short-lived service JWT |
| <a id="if-auth-010"></a>`IF-AUTH-010` | `CMP-AOS-CORE` / factory security substrate | `CMP-KAC` and `CMP-KUKSA` | Shared IAM configuration with permission handler enabled; one protected per-Unit `kuksa-jwt` RSA signing operation; `aos-kuksa-verifier-prepare.service` protected sign/verify self-test and atomic root-owned mode-`0444` `/run/aos-kuksa-verifier/kuksa-jwt-public.pem`; mandatory KUKSA `--jwt-public-key`; one-sync-per-boot plus 10-second startup time gate and helper-side issue/renew wall-to-boot deviation check; fail-closed startup, reboot reconstruction and teardown of volatile/runtime authority; no helper anchor/continuous time monitor/KUKSA lifecycle controller and no key/JWT/shared verifier enters an artifact or log | Stock Aos IAM plus dedicated certificate-module/PKCS#11 and systemd-timesyncd integration; D4-010.1 and simplified D4-027.6/.7 current-release compatibility scope; stronger native time/invalidation behavior requalified at migration | `CURRENT / SCOPED`; per-Unit preparation and retained .39 cold integration |

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
| <a id="if-func-001"></a>`IF-FUNC-001` | `CMP-BHS` | `CMP-BRAKE-BE` | Versioned bounded Brake Health message family. D4-016.2 freezes the v1 [RFC-8785/SHA-256 chunk/completion and local-spool contract](../../contracts/brake-telemetry-window/README.md); D4-017 freezes isolated local HTTP delivery and durable acknowledgement. Later messages are idempotent v2/v3 `BrakeHealthAssessment`, threshold/change `BrakeHealthEvent`, and correlated advisory fact; preserve original sample/event times. Reported `system_uid` is demo correlation, not authenticated backend identity; production authentication is Function Team 1-owned and out of scope | Function Team 1 data contract | `CURRENT / SCOPED`; durable asynchronous product delivery |
| <a id="if-func-002"></a>`IF-FUNC-002` | `CMP-BRAKE-BE` | `CMP-BRAKE-DASH` / `CMP-ORCH` | Query/subscription API for reconstructed v1 windows and persisted v2/v3 Brake Health derived results, scoped by the journal-injected required Test and optional Production context; installed cleanup selects only Test, while explicit expanded cleanup may select all sorted context UIDs, with no time selector; later out-of-order chunks remain hidden until authoritative window start, and event VDP provenance remains nullable/pending until exact assessment correlation. The exact preview-and-delete operation freezes an explicitly ordered RFC-8785/SHA-256 row set and maximum-1024-character process-local HMAC confirmation; malformed, bad-MAC, expired or previous-process tokens are `409 PREVIEW_TOKEN_EXPIRED`, while only a valid-MAC changed-row-set token is `409 PREVIEW_STALE`. Live context wiring is implemented; all ten current record categories are covered, peer data is preserved transactionally and no Cloud state is inferred | Function Team 1 backend | `CURRENT / SCOPED`; live query/detail/reset/cleanup; retained design fields use current protocol amendments |
| <a id="if-tire-003"></a>`IF-TIRE-003` | `CMP-TIRE` | `CMP-TIRE-BE` | Versioned, bounded and idempotent `TireHealthAssessment`, band-change event, advisory fact and Function Team-reported `TIRE_FUNCTION_STATUS` over the isolated local demo route. Reported `system_uid` is correlation, not authenticated backend identity; production authentication is Function Team 2-owned and out of scope | Function Team 2 data contract | `CURRENT / SCOPED`; v2 products and separate observation v3 |
| <a id="if-tire-004"></a>`IF-TIRE-004` | `CMP-TIRE-BE` | `CMP-TIRE-DASH` / `CMP-ORCH` | Query/subscription API for persisted Tire Health results; one fixed, identity-bound D4-023.3 CPU-isolation proof command path with no arbitrary load parameters or enforcement claim; plus private exact-Test or explicit full-context cleanup with a 60-second process-held opaque token and ten-category proof; invalid tokens are INVALID_PREVIEW and changed selected/nonmatching rows are STALE_PREVIEW, not Brake HMAC errors | Function Team 2 backend | `PARTIAL`; query/cleanup implemented; fixed CPU qualification control absent |

Functional Cloud interfaces are asynchronous. Loss of Cloud connectivity must
not stop local Brake Health or Tire Health analysis and advisory generation.

## Lifecycle and Operational Interface Register

| ID | Producer | Consumer | Contract and direction | Authority | State |
| --- | --- | --- | --- | --- | --- |
| <a id="if-lc-001"></a>`IF-LC-001` | Platform Team release pipeline | `CMP-AOS-CLOUD` | Exact prepared VDP v1-v3 candidate signed and published through D4-010.3 profile `platform-oem`, followed by independent Cloud identity/digest reconciliation | Platform Team OEM technical-publication identity; no automatic Validation deployment or promotion approval | `CURRENT / SCOPED`; unsigned preparation and selected OEM publication |
| <a id="if-lc-002"></a>`IF-LC-002` | Function Team 1 Service Provider pipeline | `CMP-AOS-CLOUD` | Exact prepared Brake Health v1-v3 candidate signed and published through D4-010.3 profile `brake-sp1`, followed by independent Cloud identity/digest reconciliation | Service Provider 1 technical-publication identity; no OEM Unit deployment approval | `CURRENT / SCOPED`; selected Brake SP publication |
| <a id="if-lc-007"></a>`IF-LC-007` | Function Team 2 Service Provider pipeline | `CMP-AOS-CLOUD` | Exact prepared Tire Health v1.0 candidate signed and published through D4-010.3 profile `tire-sp2`, followed by independent Cloud identity/digest reconciliation | Service Provider 2 technical-publication identity; no OEM Unit deployment approval | `CURRENT / SCOPED`; selected Tire SP publication |
| <a id="if-lc-008"></a>`IF-LC-008` | Platform Team acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Platform Team records exact Validation Unit FOTA acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact artifact/metadata digests, effective target and applicable evidence | Platform Team owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-009"></a>`IF-LC-009` | Function Team 1 acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Function Team 1 records exact Brake Health Validation Unit acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact service/metadata digests, requested permissions, effective target and applicable evidence | Function Team 1 owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-010"></a>`IF-LC-010` | Function Team 2 acceptance + OEM Release Authority | `CMP-AOS-CLOUD` | Function Team 2 records exact Tire Health Validation Unit acceptance; independent OEM Release Authority separately uses D4-011 `oem-delivery` for Test deployment and Production rollout after reviewing exact service/metadata digests, requested permissions, effective target and applicable evidence | Function Team 2 owns engineering acceptance; Release Authority owns authorization; AosCloud records/executes the mutation; passing tests never auto-authorize | `NEW / QUALIFY` |
| <a id="if-lc-004"></a>`IF-LC-004` | `CMP-AOS-CLOUD` | `CMP-AOS-CORE` | Provisioning, desired state, update delivery, validation, status and retirement | AosCloud and current Unit state | `EXTERNAL / EXTEND` qualification |
| <a id="if-lc-005"></a>`IF-LC-005` | `CMP-SW-DASH` | `CMP-AOS-CLOUD` | D4-011 `/users/me/` role/effective-permission preflight; scoped API reads; exact digest/permissions/target/evidence/team-acceptance presentation; blocked-reason display; final explicitly confirmed `oem-delivery` call; authoritative post-action re-read and `UNCERTAIN` reconciliation without blind retry | AosCloud; dashboard holds no parallel desired/evidence state, release decision, automatic approval policy or claimed server-idempotency mechanism | `CURRENT / SCOPED`; Test lifecycle observation and reconciliation; broader Production matrix separate |
| <a id="if-lc-006"></a>`IF-LC-006` | `CMP-AOS-CORE` | `CMP-RUNTIME` / `CMP-BHS` / `CMP-TIRE` | Install, start, stop, update, SOTA removal, pre-Apply FOTA revert, post-Apply forward repair, readiness and resource enforcement; for VDP FOTA, the factory-installed OEM runtime persists transaction metadata, returns native `Activating` and asynchronously gates destructive `StopInstance` and activation `StartInstance` transitions on `IF-VEH-007` frames that are fresh when acquired, while retained history proves stability only and the latest complete frame is revalidated immediately before each destructive step; the runtime does not hold its main mutex while waiting or change Service SOTA motion policy | AosCloud/AosCore own desired/actual lifecycle; OEM Component Runtime owns Platform FOTA Safe Stop application enforcement; Gateway owns vehicle facts | `CURRENT / SCOPED`; .39 runtime gate, component recovery and native service lifecycle; not full fresh serial qualification |
| <a id="if-obs-001"></a>`IF-OBS-001` | `CMP-SW-DASH` / `CMP-BRAKE-DASH` / `CMP-TIRE-DASH` | `CMP-AOS-CLOUD` and the matching dashboard | Explicit role-scoped request plus authoritative request/status/result/file through supported AosCloud APIs: `CMP-SW-DASH` uses `/api/v11/unit-logs/` under `oem-delivery` for system/VDP evidence; Brake and Tire dashboards use `/api/v11/service-logs/` under distinct SP1/SP2 operational contexts for only their own service-instance/crash evidence. No browser receives a credential; every dashboard keeps no second archive and removes bounded temporary downloads | Cloud request and related stored file remain authoritative while retained; current API exposes no retention policy | Native platform storage/API path `EXTERNAL / CURRENT`; role-scoped dashboard adapters and live log-lifecycle qualification `NEW / QUALIFY` |
| <a id="if-demo-001"></a>`IF-DEMO-001` | `CMP-ORCH` | Native macOS helper, QEMU/AosVM instances and CARLA/Gateway launchers | Launcher-owned non-root session boundary, overlay creation, role binding, start/stop, source selection and safe retirement | Authenticated local session, allowlisted operations, local session manifest plus authoritative Unit state | `CURRENT / SCOPED`; shared CLI/Presenter core and owned process lifecycle |
| <a id="if-demo-002"></a>`IF-DEMO-002` | `CMP-ORCH` | `CMP-SW-DASH` Representation Layer and launcher-owned CARLA, Controller, Engineering Telematics and browser window surfaces | Session-scoped measured workspace profile, exact owned-window identity, reserved header strip, physical bounds/visibility/non-overlap/readability probes and safe local layout restoration; the dashboard supplies the stateless shared-header read model and team navigation while every surface owner retains its content | `CMP-ORCH` owns physical composition only; `CMP-SW-DASH` owns header meaning from the existing browser read model; no Cloud/vehicle/release mutation, content authority, native-window embedding or second state store | `CURRENT / SCOPED`; current Test source binding; dual-role and host sleep/wake scope separate |

Accepted 29 September 2026 clarification of `IF-DEMO-002`: the existing window
owner may retain physical layout metadata in its own workspace directory, but
not duplicate lifecycle state. Opening Presenter does not create or rewrite the
vehicle-run journal; Create Controller remains its initialization boundary.
See the [native setup contract](../../contracts/distribution-installation/native-setup.md#independent-window-metadata--accepted-29-september-2026).

Native admission of a SOTA service against a required FOTA Vehicle Data
Platform Component version is a future behavior on `IF-LC-004`. Until an
implementing AosEdge release is available and qualified, the corresponding
negative-path demo remains `DEFERRED` and no local interface substitutes for
it. Existing component-to-component and service-to-layer dependency contracts
remain available through their native platform paths.

<a id="provisional-component-requirement-packages"></a>
## Component requirement packages

This register allocates all thirteen [component packages](components/README.md).
The table is a reader summary; each package owns its exact obligations, stable
IDs, verification levels and remaining acceptance gates. Design acceptance is
not a claim of implemented or qualified behavior.

| Package | Human-readable responsibility | Primary components | Requirement themes |
| --- | --- | --- | --- |
| <a id="cr-vehicle-sim"></a>`CR-VEHICLE-SIM` | Define the installed Vehicle Hardware Capability Manifest, provide every declared physical signal/actuator behavior, repeatable braking and tire stimuli, exact source evidence, hidden ground-truth isolation and clean CARLA scenario reset. | CARLA vehicle and Scenario Controller | Hardware-profile completeness, determinism, source integrity, simulation truth and reset |
| <a id="cr-gateway"></a>`CR-GATEWAY` | Account for the complete hardware profile, distinguish actuator capability from authority, expose VISS, arbitrate control, enforce the authoritative QM-channel advisory boundary and present factual engineering status. | Control UI, Gateway, VISS, Advisory Handler and Engineering Dashboard | Hardware coverage, telemetry contract, unavailable data, control traceability, deny-by-default QM containment and chronology |
| <a id="cr-factory"></a>`CR-FACTORY` | Reproducibly assemble and preserve the clean unprovisioned Factory Image artifact, enable stock Aos IAM permission handling, carry the dedicated non-secret per-Unit signer/verifier preparation seam without key material, and create an identity-safe Test deployment with a healthy empty slot; the expanded profile additionally requires an independent Production deployment. | Factory Baseline Assembly and Empty-Slot Runtime | Reproducibility, artifact immutability, IAM substrate, identity/key/shared-verifier absence, overlay uniqueness and preservation |
| <a id="cr-kac"></a>`CR-KAC` | Realize the current-release Service credential boundary without entering VDP or SOTA business logic: named-resource-mounted Unix socket, implicit fixed-resource bootstrap, IAM lookup, bounded JWT derivation, Service-private tmpfs delivery and lifecycle cleanup. | Current-Release KUKSA Authorization Compatibility Helper | Peer isolation, bootstrap-only secret use, no caller-selected authority, mapping, protected signing, renewal, reboot, stop/removal and native-migration deletion seam |
| <a id="cr-vdp"></a>`CR-VDP` | Deliver the versioned VISS-to-KUKSA data capability and defense-in-depth outbound QM advisory path as an OEM-trusted FOTA component without issuing Service JWTs. | KUKSA contract/configuration and Vehicle Data Platform Component | Compatibility, data quality, outbound validation, trusted Provider integration, FOTA and recovery |
| <a id="cr-bhs"></a>`CR-BHS` | Capture bounded v1 braking-event windows; apply the closed twelve-path/fixed-point v2 synthetic assessment with atomic derived admission and crash-safe state; operate offline; and request only the approved v3 advisory. | Brake Health In-Vehicle Service | Trigger/window determinism, exact model input/arithmetic/identity/time, model/data-product evolution, compatibility, offline operation and advisory scope |
| <a id="cr-tire"></a>`CR-TIRE` | Deliver one mature Tire Health v1.0 product on accepted VDP v3: estimate condition locally, persist bounded state, upload bounded results and request the typed inspection advisory through an independent SOTA lifecycle. | Tire Health In-Vehicle Service | Exact VDP v3 prerequisite, model, persistence, bounded reporting, advisory and multi-tenant isolation |
| <a id="cr-aos"></a>`CR-AOS` | Provide identity, authoritative desired/reported actual and Unit Set state, recorded owner approvals, FOTA/SOTA execution, dependency behavior, resource enforcement and native operational-log collection/delivery. | AosCore and AosCloud | Provisioning, lifecycle state and execution, Unit Set contracts, OEM-authorized validation, pre-Apply revert, SOTA removal, forward repair, native logging and retirement |
| <a id="cr-brake-cloud"></a>`CR-BRAKE-CLOUD` | Reconstruct and present v1 Brake Telemetry Windows; ingest/present v2/v3 derived messages; expose a separate prepared-candidate view that delegates protected sign/publish actions; with its backend in a Mac-local ARM64 container and live views in host Presenter, without entering the vehicle decision path or owning OEM lifecycle state. | Brake Health Backend and Function Dashboard | Candidate integrity, protected publication delegation, chunk reconstruction, idempotency, data-product evolution, offline synchronization, local hosting, exact-current-Unit persistence and complete R0 deletion |
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

Installed workstation allocation: [separate installed data authority (`SYS-DIST-001`)](system-requirements-and-traceability.md#sys-dist-001)
is owned by [Demo Orchestrator](#cmp-orch), through the existing
[local lifecycle interface](#if-demo-001), and derives
[installed instance separation](components/demo-orchestration.md#req-demo-025).

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
  (D4-016.1/.2/.3/.4/.5 and D4-017 accepted; D4-016.3 complete
  byte/arithmetic/input/persistence closure accepted 2026-08-29;
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

- Accepted executable D4 design refinement:
  [Tire Health In-Vehicle Product Contract](../../contracts/tire-health-model/README.md)
  (`ACCEPTED` design input; D4-003 empirical qualification and implementation
  remain open).

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

- Accepted/design-reviewed executable D4 refinements:
  [Tire Health Cloud API](../../contracts/tire-cloud-api/README.md),
  [Tire Health In-Vehicle Product Contract](../../contracts/tire-health-model/README.md)
  and [Local Demo Hosting and VM Route](../../contracts/local-demo-hosting/README.md)
  (D4-018/D4-019 `ACCEPTED`, D4-020 `DESIGN_REVIEWED`; no repository or
  executable exists).

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

- Accepted/design-reviewed executable D4 refinements:
  [Brake Cloud API](../../contracts/brake-cloud-api/README.md),
  [Tire Cloud API](../../contracts/tire-cloud-api/README.md), and
  [Local Demo Hosting and VM Route](../../contracts/local-demo-hosting/README.md)
  (Cloud APIs `ACCEPTED`, hosting `DESIGN_REVIEWED`; no local/Cloud/VM action
  is authorized).

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

This topic-based summary states the effective boundaries, not a sequence of
past review deltas. Component/interface IDs and owning detailed requirements
above remain authoritative. Acceptance is not implementation qualification.

### Platform and native authorization

- Factory assembly, its immutable image and each deployed controller are
  separate concepts. The image has an empty VDP slot, IAM permissions enabled
  independently of provisioning, and no reusable identity or service secret.
- Factory-installed KUKSA and separately packaged `CMP-KAC` are outside VDP.
  Native IAM/Service Manager own instance identity and permissions; KAC derives
  bounded JWTs from the fixed-resource exchange. The retired VDP-owned broker
  is not an alternative. D4-027 and ADR 0013 own this contract.
- Provider is trusted OEM integration, not an untrusted SOTA tenant. No dynamic
  Provider credential or malicious-Provider isolation claim is introduced.
- The current KUKSA compatibility patches are recorded in the implementation
  map; the as-built image is not byte-identical upstream KUKSA.

### Independent products and deployment authority

- Gateway owns CARLA control/integration, VISS, typed advisory enforcement and
  engineering telemetry. Brake/Tire consume KUKSA only and have no motion
  authority. VDP validates outbound requests; Gateway is the final QM boundary.
- `brake-health-service` and `tire-health-service` are existing separate SOTA
  owners. Each has its own Cloud-product repository; backends do not belong in
  the in-vehicle repositories. Tire V1 uses VDP V3 and does not repeat Brake's
  V1/V2/V3 evolution. No native pre-transfer dependency admission is implied.
- Teams own engineering acceptance/publication. OEM deployment authorization
  and authoritative Aos Cloud execution remain separate. The installed Test
  scope is UI-STUDIO-026; expanded two-SP/dual-role promotion retains its
  accepted evidence-backed approval obligations. Passing tests never approves.
- Prepared, signed, Cloud and installed identities remain distinct. Browser
  publication uses only verified prebuilt content and role-bound native helpers;
  no browser build, key handling, arbitrary command or repackaging fallback.
  ADR 0015/0016 govern native inputs and destination-specific signing.
- Before-Apply revert, after-Apply forward repair, dependent-first removal,
  exact identity retirement and no-blind-retry belong to CR-AOS/CR-DEMO. No
  standalone Node-delete API or project lifecycle authority is invented.

### Connectivity, resources and evidence

- Vehicle external, presenter administrative and in-vehicle networks are
  separate. One atomic external-offline control affects Unit Cloud and service
  backend routes together; it preserves excluded links. A partial fault is not
  success and presenter Cloud loss is not a Unit-offline fact.
- Services maintain bounded local models/outboxes through offline operation.
  D4-016 owns Brake acquisition/chunk/spool limits; the accepted source-time
  contract governs current acquisition; frame-count examples are not an alternate policy.
  Backend production authentication remains outside the example-product claim.
- Native AosCore alone enforces per-instance quotas. The accepted fixed Tire
  CPU proof uses a bounded in-instance worker, exact fixed-profile command,
  180-second ceiling and Brake control tenant, with no SSH/exec fallback. It
  remains an unclosed proof, not an available UI feature inferred from a graph.
- Native Unit/Service operational logs stay role-scoped with explicit request,
  redaction, bounded temporary download and no second archive. Unqualified
  retention/negative cases remain obligations, not silently accepted behavior.
- Coverage states remain UNKNOWN/PARTIAL/PLANNED/DOCUMENTARY_ONLY/ACCEPTED/STALE.
  ACCEPTED binds exact evidence, subject, platform/configuration and verification
  time; baseline mismatch is STALE. Functional, install and advisory facts must
  not be inferred from one another.

### Orchestration and presentation

- Existing `CMP-ORCH` and `CMP-SW-DASH` compose the session/read model without
  owning Cloud state. Trusted helpers are session-scoped, allowlisted and
  supervised; they are not permanent login services or new HLA components.
- Physical window composition belongs to orchestration (`IF-DEMO-002`);
  shared-header meaning, navigation and team context belong to Presenter.
  CARLA/native controls remain separate visible surfaces. Integrated backend
  cards/dialogs are the installed UI; terminal-only and five-stage mockup rules
  belong to the expanded profile where not replaced by UI-STUDIO-026.
- Platform/Brake/Tire ownership and release state remain independent. Installed
  mutations are serialized; expanded disjoint-resource concurrency is not a
  current prerequisite. Provisioning, retirement and live-source handover remain
  run-exclusive; uncertain operations require reconciliation.
- Stop/Start preserves the same Test and durable data; Finish is explicit
  retirement. Park/Resume is not an operator action. Ignition and host sleep
  have separate contracts and qualification boundaries.

The [pre-consolidation register](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/1a0d66f4b340bfc7b487062f7bb316623ad86af8/docs/requirements/component-decomposition-and-interface-register.md) preserves review
chronology. Requirements and stable identifiers are not retired by this summary.

<a id="review-provenance"></a>
## Authority and verification

This document owns its current obligations, stable IDs and acceptance criteria.
Use the linked current baseline for exact scoped evidence. Accepted design is
not a claim that the complete implementation or live matrix has passed.
