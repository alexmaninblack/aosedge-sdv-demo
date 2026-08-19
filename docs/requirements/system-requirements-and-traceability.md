<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# System Requirements and Traceability 0.9

- Status: Review candidate
- Version: 0.9
- Prepared: 2026-08-19
- Proposed successor to: 0.8
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.4](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 1.7](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 1.6](../architecture/demo-scenario-architecture-flows.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0010](../architecture/decisions/0010-aos-kuksa-credential-broker.md), and
  [ADR 0011](../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md)
- Implementation, repository creation, signing, Cloud, or Unit mutation authorized: no

## Purpose

This document converts the accepted architecture-flow model and its twenty-one
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

1. High-Level Architecture 1.4 owns boundaries, authority and invariants.
2. Demo Scenario 1.7 owns the audience-visible stage progression.
3. Architecture Flows 1.6 owns detailed lifecycle, runtime, observability and
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
| `SYS-CTRL` | Vehicle control safety and continuous mode handover |
| `SYS-REL` | FOTA/SOTA targeting, dependency, validation and rollback |
| `SYS-VDP` | Vehicle Data Platform Component |
| `SYS-BHS` | Brake Health functional behavior |
| `SYS-TIRE` | Tire Health estimation, bounded reporting and advisory behavior |
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

Each Function Team owns the engineering release decision for its service. It
uses its Service Provider identity to publish and technically verify artifacts,
but records validation acceptance and any deployment or promotion approval
affecting OEM Units through an authorized OEM identity. The Platform Team owns
the corresponding FOTA decision and also records it through an OEM identity.
AosCloud remains the lifecycle system of record and execution control plane.

| Repository | Ownership boundary | Lifecycle | State |
| --- | --- | --- | --- |
| `CarlaSim` | Virtual physical vehicle and upstream simulator behavior | Simulator source | Existing |
| `carla-ego-runtime` | Vehicle Gateway, control, VSS projection, VISS and Engineering Telematics Dashboard | Gateway tooling | Existing |
| `aos-vehicle-platform` | Shared Vehicle Data Platform Component, KUKSA integration, provider runtime, thin Aos–KUKSA Credential Broker and platform-credential integration | Platform FOTA | Existing; broker/provider-identity target not yet implemented |
| `brake-health-service` | Function Team 1 on-board Brake Health application and local inference | Service Provider 1 / SOTA 1 | Existing |
| `tire-health-service` | Function Team 2 on-board tire-condition estimation, bounded reporting and inspection advisory | Service Provider 2 / SOTA 2 | **Proposed repository** |
| `brake-health-cloud` | Function Team 1 backend and Function Dashboard | Function Team 1 Cloud product | **Planned repository** |
| `tire-health-cloud` | Function Team 2 backend and Function Dashboard | Function Team 2 Cloud product | **Planned repository** |
| `aosedge-sdv-demo` | Cross-repository orchestration, dashboards, system requirements and end-to-end qualification | Demo solution | Existing |

The proposed Function Team 2 repository shall not own CARLA integration,
VISS transport, platform signal publication, KUKSA authorization, VM
provisioning, or AosCloud desired state. It consumes only an accepted,
versioned KUKSA contract.

The Function Team 1 and Function Team 2 backends and dashboards are distinct
functional products. Each backend and its dashboard share one Cloud-product
repository, `brake-health-cloud` or `tire-health-cloud`, and must not be placed
inside either in-vehicle service repository.

The proposed repository is not added to `workspace/repositories.json` until it
exists and its initial accepted revision is available. This preserves the
current workspace doctor's validity.

## System Requirements

### Manufacturing and identity

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-mfg-001"></a>`SYS-MFG-001` | Reproducible factory image | The Platform Team shall produce a reproducible, immutable and digest-addressed OEM Demo Factory Image from an identified AosEdge release and accepted integration inputs. | `I,T` | `GAP-AF-01` |
| <a id="sys-mfg-002"></a>`SYS-MFG-002` | Clean SOP substrate | The factory image shall contain AosCore, KUKSA, security/update support, enabled stock Aos IAM permission handling, the non-secret IAM/PKCS#11 signing-key integration seam and the provider-specific empty-slot runtime, but no provider payload, functional service, Cloud registration, Cloud credential, signing key or reusable per-vehicle secret. | `I,T` | `GAP-AF-01`, `GAP-AF-15` |
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
| <a id="sys-src-003"></a>`SYS-SRC-003` | Versioned vehicle hardware profile | The selected virtual vehicle shall have one digest-addressed Vehicle Hardware Capability Manifest that identifies the CARLA revision and ego blueprint and classifies every installed signal, sensor and actuator with its type, unit, frame, cadence or command range, availability semantics and provenance; a capability that CARLA can theoretically create but that is not installed in the selected profile shall be declared `NOT_INSTALLED` rather than implied to exist. | `T,I` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-src-004"></a>`SYS-SRC-004` | Complete Simulator–Gateway accounting | Across the selected hardware profile, the Simulator and Gateway shall account for every declared capability without silent loss: installed state shall be delivered or explicitly unavailable/unsupported; actuator commands shall be accepted or rejected with bounded status and the actually applied control state shall be observable; simulator ground truth and qualification-only oracle state shall remain outside the production vehicle-data interface. | `T,I,A` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-rel-001"></a>`SYS-REL-001` | Immutable release candidates | Every FOTA and SOTA candidate shall be immutable and identified by version and digest before presentation-time deployment. | `I` | `GAP-AF-05`, `GAP-AF-07`, `GAP-AF-20` |
| <a id="sys-rel-002"></a>`SYS-REL-002` | Current effective-target validation | Immediately before approval, the delivery workflow shall derive effective targets from current Unit pending-batch state and shall block stale, missing or unexpected targets. | `T,I` | `GAP-AF-06` |
| <a id="sys-rel-003"></a>`SYS-REL-003` | Service capability compatibility | Each SOTA service artifact shall carry a versioned Vehicle Data Platform Component compatibility range and shall fail closed at startup/readiness when the installed capability is absent or incompatible. | `T,I` | `GAP-AF-20` |
| <a id="sys-rel-004"></a>`SYS-REL-004` | Validate before promotion | A candidate shall be installed and qualified on the Validation Unit before the identical accepted bytes and digest are promoted to the Demonstration Unit. | `T,I,D` | `GAP-AF-06`, `GAP-AF-20` |
| <a id="sys-rel-005"></a>`SYS-REL-005` | Dependent-first rollback | Rollback shall remove or roll back a dependent SOTA service before a platform capability on which it depends, while preserving unaffected service and platform lifecycles. | `T,A` | `GAP-AF-05`, `GAP-AF-20` |
| <a id="sys-rel-006"></a>`SYS-REL-006` | Native Cloud dependency rejection | AosCloud shall natively reject a SOTA request whose declared Vehicle Data Platform Component range is not satisfied on the intended Unit before changing Subject-service desired state, creating a validation batch or campaign, or transferring update content to the Unit, and shall return an authoritative machine-readable reason. | `T,I,D` | `GAP-AF-20` |
| <a id="sys-rel-007"></a>`SYS-REL-007` | Team-owned release decisions | The Platform Team shall own every Vehicle Data Platform Component release decision, Function Team 1 shall own every Brake Health release decision, and Function Team 2 shall own every Tire Health release decision; passing evidence or a dashboard action shall not silently substitute for explicit owner acceptance. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-rel-008"></a>`SYS-REL-008` | OEM-authorized deployment approval | A Function Team shall use its Service Provider identity to publish and technically verify its service artifact, while every validation acceptance and deployment or promotion approval affecting OEM Units shall be explicitly confirmed through an authorized OEM identity and recorded in AosCloud with the owner, artifact version, digest, target and transition. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-rel-009"></a>`SYS-REL-009` | Combined-graph owner gate | AosCloud promotion of a combined FOTA/SOTA graph shall remain blocked until the Platform Team has accepted the exact platform artifact and the relevant Function Team has accepted the exact service artifact and integration result for the same versions, digests and targets. | `T,I,D` | `GAP-AF-17`, `GAP-AF-20` |
| <a id="sys-rel-010"></a>`SYS-REL-010` | Evidence-backed final OEM approval | Before an OEM-authorized deployment or promotion action is enabled, the workflow shall present and bind the exact artifact and service-metadata digests, requested permissions, effective target, required validation evidence with freshness/status, owning-team acceptance and active OEM role. Any missing, stale, failed or mismatched prerequisite shall block the action; passing evidence shall never auto-approve; an explicit final decision shall be recorded in AosCloud and followed by an authoritative state re-read. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |

[Native Cloud dependency rejection (`SYS-REL-006`)](#sys-rel-006) is
**deferred and blocked on an implementing AosEdge platform
release**. The Platform Team reported the capability as roadmap work on
2026-08-18, without an available release or date. No project-side admission
controller is an acceptable substitute. `SYS-REL-003` remains required as
defense in depth before and after the native Cloud feature becomes available.

### Vehicle control and handover

`SYS-CTRL-001` and `SYS-CTRL-002` are corrective allocations discovered while
deriving the first component packages. `SYS-CTRL-003` preserves the historical
Scenario 1.4 and Architecture Flows 1.3 mode/context refinement now carried
forward by Scenario 1.5 and Flows 1.4. The
set does not add a demo stage, authority, architectural boundary or data
direction.

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ctrl-001"></a>`SYS-CTRL-001` | Fail-safe exclusive vehicle control | The vehicle-control path shall remain separate from VISS/KUKSA vehicle-data paths, permit exactly one authenticated control owner, reject invalid, replayed, out-of-mode or simultaneous throttle/brake commands, enforce bounded command and ownership deadlines, and select safe stop on startup, timeout, release, disconnect, applicable focus loss, shutdown or controller failure. No functional SOTA service shall gain vehicle-motion authority. | `T,I,D` | Accepted HLA/flow baseline correction |
| <a id="sys-ctrl-002"></a>`SYS-CTRL-002` | Continuous control-mode handover | Transitions among manual, autopilot, scripted scenario and safe stop shall preserve one ego actor, one synchronous clock owner, the active run/frame identity and uninterrupted Gateway telemetry; transitions shall be pedal-safe and bounded, and manual takeover of an unfinished scripted attempt shall record an abort rather than a false pass or failure. | `T,I,D` | Accepted HLA/flow baseline correction |
| <a id="sys-ctrl-003"></a>`SYS-CTRL-003` | Deterministic mode/context transition | The solution shall implement the complete `AF-X-DRIVE` matrix with independent drive-mode and `FREE_DRIVE`/`BRAKE_EVENT` world-context state: manual takeover shall retain brake-event position and obstacle; entry to Scenario shall perform a canonical reset and new generation; entry to Autopilot from brake-event context shall safe-stop, remove scenario-owned obstacle state, reset the same actor to an accepted free-drive start with zero motion and validate lane alignment before enabling Traffic Manager; safe stop alone shall not reset context. Any failed transition shall remain in safe stop without partial mode activation. Reverse and Autopilot obstacle avoidance shall not be required or claimed. | `T,I,D` | `GAP-AF-24` |

### Vehicle Data Platform Component

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-vdp-001"></a>`SYS-VDP-001` | Healthy empty capability slot | The provider-specific runtime shall report a healthy empty slot at G0 and shall support the independently versioned Vehicle Data Platform Component without claiming arbitrary component-type support. | `T,I` | `GAP-AF-01`, `GAP-AF-05` |
| <a id="sys-vdp-002"></a>`SYS-VDP-002` | Versioned v1 signal contract | Component v1 shall expose only its accepted read-only signal subset with defined type, unit, range, cadence, freshness, unavailable-state and provenance behavior. | `T,I` | `GAP-AF-05` |
| <a id="sys-vdp-003"></a>`SYS-VDP-003` | Backward-compatible v2 component | Component v2 shall be a backward-compatible superset of v1 and shall preserve existing v1 consumers while adding the accepted Brake Health inputs. | `T` | `GAP-AF-08` |
| <a id="sys-vdp-004"></a>`SYS-VDP-004` | Allowlisted outbound advisory | Component v3 shall provide a narrowly scoped typed advisory path with per-service allowlisted KUKSA actuators, validation policy, VISS Set operation and factual Gateway status. | `T,I,D` | `GAP-AF-10`, `GAP-AF-22` |
| <a id="sys-vdp-005"></a>`SYS-VDP-005` | Explicit degraded data | Missing, stale, malformed or disconnected source data shall become explicit unavailable/degraded state and shall never be replaced with fabricated normal values. | `T` | `GAP-AF-05`, `GAP-AF-08` |

### Brake Health function

#### Retired Brake Health requirement

The accepted `SYS-BHS-001` low-rate report concept is retired because Service
v1 now owns a finite high-detail braking-event acquisition product. Its anchor
remains resolvable for historical traceability.

| Retired identifier | Replacement | Reason |
| --- | --- | --- |
| <a id="sys-bhs-001"></a>`SYS-BHS-001` — Bounded v1 functional report | [`SYS-BHS-005`](#sys-bhs-005) | Service v1 now transfers a finite pre-trigger/braking/post-trigger telemetry window rather than a low-rate selected report |

#### Active Brake Health requirements

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-bhs-005"></a>`SYS-BHS-005` | Bounded v1 Brake Telemetry Window | Service v1 shall continuously retain only a bounded in-memory pre-trigger buffer from the accepted KUKSA contract; an accepted braking trigger shall produce one versioned and idempotent finite window containing configurable bounded pre-trigger, active-braking and post-trigger intervals. Transfer shall begin with the pre-trigger chunk while braking is visible, continue with ordered bounded chunks, and close with one completion record. | `T,I,D` | `GAP-AF-07` |
| <a id="sys-bhs-002"></a>`SYS-BHS-002` | Deterministic v2 edge assessment | Service v2 shall use an immutable prepared synthetic demo model, distinguish native, derived, estimated and simulated inputs, and produce deterministic local `BrakeHealthAssessment` results for the accepted scenario and input version without claiming production diagnostic accuracy or a safety function. | `T,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-006"></a>`SYS-BHS-006` | Derived v2 Cloud data product | Normal Service v2 operation shall send only bounded, versioned and idempotent `BrakeHealthAssessment` and threshold/change `BrakeHealthEvent` messages to the functional backend rather than Service v1 high-detail telemetry windows; the dashboard shall make that processing and traffic change visible. | `T,I,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-003"></a>`SYS-BHS-003` | Allowlisted v3 advisory | Service v3 shall request only the accepted Brake Health advisory target and shall not gain arbitrary display-text or vehicle-motion authority. | `T,I` | `GAP-AF-10`, `GAP-AF-15` |
| <a id="sys-bhs-004"></a>`SYS-BHS-004` | Offline local continuity | Brake Health local assessment and advisory shall continue without Cloud connectivity; in-progress/completed v1 windows and v2/v3 derived functional messages shall use bounded retention, retry and idempotent synchronization with original sample/event times. | `T,A,D` | `GAP-AF-11` |

### Tire Health function

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-tire-001"></a>`SYS-TIRE-001` | Existing platform contract only | The Tire Health service shall consume only dynamics signals already present in an accepted Vehicle Data Platform Component and shall not require a new platform feature request in the current demo. | `I,T` | `GAP-AF-21` |
| <a id="sys-tire-002"></a>`SYS-TIRE-002` | Local persistent condition estimate | The service shall maintain a bounded, persistent and versioned tire-condition estimate from its accepted input subset and shall produce an estimated condition band rather than claim an exact measured tread depth. | `T,A,D` | `GAP-AF-21` |
| <a id="sys-tire-003"></a>`SYS-TIRE-003` | Explicit simulation model | The CARLA scenario shall provide a deterministic, clearly labelled accelerated-time or pre-aged tire-degradation stimulus with hidden ground truth used only for qualification. | `T,I,D` | `GAP-AF-21` |
| <a id="sys-tire-004"></a>`SYS-TIRE-004` | Bounded Cloud reporting | The service shall upload only bounded, versioned and idempotent condition summaries or threshold events and shall retain them within explicit offline, rate and storage limits instead of continuously streaming raw telemetry. | `T,I,A` | `GAP-AF-21`, `GAP-AF-23` |
| <a id="sys-tire-005"></a>`SYS-TIRE-005` | Independent Tire Health product | Function Team 2's backend shall ingest bounded Tire Health results idempotently and its dashboard shall expose condition band, event time/status, service and capability versions, Unit role and online/offline delivery state. | `T,D` | `GAP-AF-23` |
| <a id="sys-tire-006"></a>`SYS-TIRE-006` | Offline inspection advisory | Local estimation and inspection-advisory generation shall continue without Cloud connectivity, and the service shall request only its typed allowlisted Tire Health target without vehicle-motion or arbitrary-display authority. | `T,I,A,D` | `GAP-AF-22`, `GAP-AF-23` |

### Retired Function Team 2 candidate requirements

These identifiers remain resolvable for historical links but are not active
requirements after ADR 0008:

| Retired identifier | Replacement |
| --- | --- |
| <a id="sys-evt-001"></a>`SYS-EVT-001` | `SYS-TIRE-001` |
| <a id="sys-evt-002"></a>`SYS-EVT-002` | `SYS-TIRE-002`, `SYS-TIRE-003` |
| <a id="sys-evt-003"></a>`SYS-EVT-003` | `SYS-TIRE-004` |
| <a id="sys-evt-004"></a>`SYS-EVT-004` | `SYS-TIRE-005` |
| <a id="sys-evt-005"></a>`SYS-EVT-005` | `SYS-TIRE-003` |

### Security, observability and timing

#### Retired Security Requirement

The former `SYS-SEC-002` required a second FOTA-managed per-service OEM policy
inside the broker. Architecture 1.3 corrected that duplication: Aos Service
Manager and IAM are authoritative for the running SOTA instance and its
registered permissions, while the broker performs only bounded translation.

| Retired identifier | Replacement | Reason |
| --- | --- | --- |
| <a id="sys-sec-002"></a>`SYS-SEC-002` | [`SYS-SEC-006`](#sys-sec-006) | Replaced the duplicate local OEM-policy comparison with the native Aos IAM permission lifecycle and contract-bounded KUKSA translation |

#### Active Security, Observability and Timing Requirements

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-sec-001"></a>`SYS-SEC-001` | Least-privilege KUKSA identities | KUKSA publishers, readers and actuators shall use distinct least-privilege identities and path-level permissions appropriate to their lifecycle owners. | `I,T` | `GAP-AF-15` |
| <a id="sys-sec-003"></a>`SYS-SEC-003` | Fail-closed advisory security | Unauthorized, malformed, stale or replayed advisory requests shall fail closed and produce factual non-driver status evidence. | `T,A` | `GAP-AF-10`, `GAP-AF-15`, `GAP-AF-22` |
| <a id="sys-sec-004"></a>`SYS-SEC-004` | KUKSA verifier and token lifetime | Unmodified Eclipse KUKSA shall trust only the Platform Team's configured public verifier; the broker signing key shall be established per Unit and protected through the Aos IAM/certificate-module and PKCS#11 integration, token lifetime and refresh shall be bounded, and service permission removal shall prevent renewal. No signing key shall be baked into a Factory Image or FOTA/SOTA artifact. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-sec-005"></a>`SYS-SEC-005` | Separate provider authority | The privileged Vehicle Data Provider shall obtain a separate short-lived platform credential for only the accepted KUKSA `provide`/`create` paths; no functional SOTA credential shall grant provider authority. Its FOTA-component identity binding shall be explicitly designed and qualified rather than reusing a static provider token or assuming automatic `AOS_SECRET` injection. | `T,I` | `GAP-AF-15` |
| <a id="sys-sec-006"></a>`SYS-SEC-006` | Native-IAM-derived SOTA KUKSA credentials | The Vehicle Data Platform Component shall authenticate a SOTA service's per-instance `AOS_SECRET` through Aos IAM and translate only the currently registered `kuksa` path/mode set into a short-lived, path-scoped KUKSA JWT. It shall reject invalid or stale secrets, unknown modes, malformed paths and permissions outside the installed VDP contract, shall never widen the IAM result, and shall not maintain a parallel service identity or per-service policy database. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-sec-007"></a>`SYS-SEC-007` | QM service and Gateway containment | Brake Health and Tire Health shall remain QM-domain maintenance/inspection applications with no allocated safety goal, direct driver-HMI claim, vehicle-motion authority or safety-critical actuator access. The VDP shall validate outbound advisories as defense in depth, and the Vehicle Gateway shall be the final authoritative boundary for the QM-origin channel: it shall accept only Platform-owned typed non-safety advisories, validate target/type/range/freshness/rate/correlation, report factual status, and reject arbitrary VSS writes and every throttle, brake, steer, gear, motion or safety-critical operation. | `T,I,A,D` | `GAP-AF-10`, `GAP-AF-15`, `GAP-AF-22` |
| <a id="sys-obs-001"></a>`SYS-OBS-001` | Authoritative demo surfaces | Every audience claim shall identify its authoritative surface: CARLA for physical stimulus, Engineering Telematics Dashboard for Gateway state, AosCloud for software lifecycle and native log requests/results, and each functional dashboard for its own backend data. | `I,D` | `GAP-AF-17` |
| <a id="sys-obs-002"></a>`SYS-OBS-002` | Cloud-authoritative delivery dashboard | The Software Delivery Dashboard shall read and re-read authoritative AosCloud lifecycle and native-log state, display the business decision owner and active Cloud role, require explicit confirmation before an OEM-authorized mutation or log request, and shall not maintain an independent desired-state database, log archive or automatic approval policy. | `T,I` | `GAP-AF-06`, `GAP-AF-16`, `GAP-AF-17` |
| <a id="sys-obs-003"></a>`SYS-OBS-003` | Operational log controls | Before native system, service-instance or crash logs are presented as demo evidence, the solution shall qualify scoped AosCloud API access, request latency and failure visibility, retention/deletion, online/offline behavior, redaction, and source timestamps. | `T,I,A` | `GAP-AF-16` |
| <a id="sys-obs-004"></a>`SYS-OBS-004` | Per-run correlation | Before provisioning, a demo run shall be correlated by start time and local overlay roles; after provisioning it shall be correlated by the two Unit IDs and the same bounded time window. | `T,I` | `GAP-AF-19` |
| <a id="sys-obs-005"></a>`SYS-OBS-005` | Truthful control-transition evidence | The Gateway engineering projection and Engineering Telematics Dashboard shall expose the current drive mode, world context, scenario state/result, generation and reset/discontinuity state as simulator-derived facts so that reset teleportation is never interpreted as physical vehicle motion. | `T,I,D` | `GAP-AF-24` |
| <a id="sys-obs-006"></a>`SYS-OBS-006` | Visible approval decision basis | The Software Delivery Dashboard shall distinguish validation evidence, owning-team acceptance and the final OEM authorization; show the exact candidate, requested permissions, target, evidence status and active role before confirmation; explain blocked prerequisites; and shall not claim that its button, passing tests or locally retained data constitute the approval, authoritative lifecycle state, proof that software is safe, or functional-safety certification. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-tim-001"></a>`SYS-TIM-001` | Lifecycle timing bounds | Each lifecycle stage shall have measured normal duration, timeout, stalled-state and recovery criteria for both technical and executive presentation modes. | `T,A,D` | `GAP-AF-18` |
| <a id="sys-tim-002"></a>`SYS-TIM-002` | Separate local and Cloud latency | Local Brake Health and Tire Health decision/Gateway-advisory latency shall be measured separately from Cloud report synchronization latency. | `T,A,D` | `GAP-AF-18` |

### Retirement and next-run reset

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ret-001"></a>`SYS-RET-001` | Retire Units and overlays | R0 shall stop both Units, perform qualified Cloud deprovisioning and deletion, prove retired credentials cannot reconnect, and discard only the corresponding provisioned overlays after reconciliation succeeds. | `T,I,A` | `GAP-AF-03`, `GAP-AF-19` |
| <a id="sys-ret-002"></a>`SYS-RET-002` | Clear functional run data | Functional backends and dashboards shall clear or archive run-scoped data using exact Unit IDs and the bounded session time window without deleting authoritative Cloud audit history. | `T,I` | `GAP-AF-19` |
| <a id="sys-ret-003"></a>`SYS-RET-003` | Reset vehicle simulation state | R0 shall safe-stop the ego vehicle, remove only scenario-owned CARLA actors and sensors, restore changed CARLA world and Traffic Manager settings, clear run-local simulation evidence and report incomplete cleanup before the next run. | `T,I` | `GAP-AF-04` |
| <a id="sys-ret-004"></a>`SYS-RET-004` | No rollback or fleet claim | The normal demo reset shall not be presented as a G4-to-G0 OTA rollback or as a production-fleet vehicle deletion policy. | `I,D` | `GAP-AF-03`, `GAP-AF-18` |
| <a id="sys-ret-005"></a>`SYS-RET-005` | Preserve immutable factory artifact | R0 shall not modify or replace the accepted OEM Demo Factory Image; after provisioned overlays are retired and discarded, the system shall verify and retain the same immutable factory-image digest as the source for the next M0 deployments. | `T,I` | `GAP-AF-01`, `GAP-AF-19` |
| <a id="sys-ret-006"></a>`SYS-RET-006` | Reconcile Unit Sets for the next run | R0 shall prove that the persistent Verification and Demonstration Unit Sets contain no retired Unit and are empty after Cloud deprovisioning and Unit deletion. The next M1 shall provision new Unit and Node identities, assign exactly one new Validation Unit and one new Demonstration Unit to their correct disjoint sets, and shall not reuse prior-run batch, validation, Campaign or target assumptions after membership changes. | `T,I,A` | `GAP-AF-03`, `GAP-AF-06`, `GAP-AF-19` |

## Gap Coverage Matrix

| Gap | Governing system requirements |
| --- | --- |
| `GAP-AF-01` | `SYS-MFG-001`, `SYS-MFG-002`, `SYS-VDP-001`, `SYS-RET-005` |
| `GAP-AF-02` | `SYS-MFG-003`, `SYS-ID-001` |
| `GAP-AF-03` | `SYS-ID-002`, `SYS-ID-003`, `SYS-ID-004`, `SYS-RET-001`, `SYS-RET-004`, `SYS-RET-006` |
| `GAP-AF-04` | `SYS-SRC-001`, `SYS-SRC-002`, `SYS-RET-003` |
| `GAP-AF-05` | `SYS-REL-001`, `SYS-REL-005`, `SYS-VDP-001`, `SYS-VDP-002`, `SYS-VDP-005` |
| `GAP-AF-06` | `SYS-ID-003`, `SYS-REL-002`, `SYS-REL-004`, `SYS-REL-010`, `SYS-OBS-002`, `SYS-RET-006` |
| `GAP-AF-07` | `SYS-REL-001`, `SYS-BHS-005` |
| `GAP-AF-08` | `SYS-VDP-003`, `SYS-VDP-005`, `SYS-BHS-002`, `SYS-BHS-006` |
| `GAP-AF-09` | `SYS-BHS-002`, `SYS-BHS-006` |
| `GAP-AF-10` | `SYS-VDP-004`, `SYS-BHS-003`, `SYS-SEC-003`, `SYS-SEC-007` |
| `GAP-AF-11` | `SYS-BHS-004` |
| `GAP-AF-15` | `SYS-MFG-002`, `SYS-BHS-003`, `SYS-TIRE-006`, `SYS-SEC-001`, `SYS-SEC-003`, `SYS-SEC-004`, `SYS-SEC-005`, `SYS-SEC-006`, `SYS-SEC-007` |
| `GAP-AF-16` | `SYS-OBS-003` |
| `GAP-AF-17` | `SYS-REL-007`, `SYS-REL-008`, `SYS-REL-009`, `SYS-REL-010`, `SYS-OBS-001`, `SYS-OBS-002`, `SYS-OBS-006` |
| `GAP-AF-18` | `SYS-TIM-001`, `SYS-TIM-002`, `SYS-RET-004` |
| `GAP-AF-19` | `SYS-OBS-004`, `SYS-RET-001`, `SYS-RET-002`, `SYS-RET-005`, `SYS-RET-006` |
| `GAP-AF-20` | `SYS-REL-001`, `SYS-REL-003`, `SYS-REL-004`, `SYS-REL-005`, deferred `SYS-REL-006` |
| `GAP-AF-21` | `SYS-TIRE-001`, `SYS-TIRE-002`, `SYS-TIRE-003`, `SYS-TIRE-004` |
| `GAP-AF-22` | `SYS-VDP-004`, `SYS-TIRE-006`, `SYS-SEC-003`, `SYS-SEC-007` |
| `GAP-AF-23` | `SYS-TIRE-004`, `SYS-TIRE-005`, `SYS-TIRE-006` |
| `GAP-AF-24` | `SYS-CTRL-003`, `SYS-OBS-005` |

All twenty-one active architecture-flow gaps have explicit requirement coverage.
Retired gaps `GAP-AF-12` through `GAP-AF-14` resolve to their replacements in
Architecture Flows 1.4. This
does not mean they are resolved; each remains open until its linked
requirements have accepted evidence.

## Component Requirement Package Allocation

The canonical component IDs, interface IDs, repository candidates and package
boundaries are defined in the
[Component Decomposition and Interface Register 0.9](component-decomposition-and-interface-register.md).
The next derivation step shall expand the following packages. A system
requirement may allocate obligations to several packages and one integration
test.

| Package | Primary repository or owner | Main allocation |
| --- | --- | --- |
| [Vehicle simulation (`CR-VEHICLE-SIM`)](component-decomposition-and-interface-register.md#cr-vehicle-sim) | `CarlaSim` plus scenario tooling in `carla-ego-runtime` | Versioned vehicle hardware profile, complete installed signal/actuator boundary, deterministic braking and tire stimuli, reset, timestamps and isolated hidden-ground-truth qualification |
| [Vehicle Gateway (`CR-GATEWAY`)](component-decomposition-and-interface-register.md#cr-gateway) | `carla-ego-runtime` | Complete hardware-profile accounting, actuator-command/applied-state traceability, vehicle sampling, VSS/VISS contracts, source status, authoritative QM-channel advisory containment and Engineering Telematics Dashboard |
| [Factory substrate (`CR-FACTORY`)](component-decomposition-and-interface-register.md#cr-factory) | Platform Team / `aos-vehicle-platform` | Factory image, enabled Aos IAM permission handling, non-secret IAM/PKCS#11 seam, provider-specific empty-slot runtime, identity absence, overlay creation and immutable artifact preservation |
| [Vehicle Data Platform (`CR-VDP`)](component-decomposition-and-interface-register.md#cr-vdp) | `aos-vehicle-platform` | Component v1-v3, KUKSA contract/trust, defense-in-depth outbound policy, thin Credential Broker and separately bound provider platform credential |
| [Brake Health service (`CR-BHS`)](component-decomposition-and-interface-register.md#cr-bhs) | `brake-health-service` | v1 event-window recorder, v2 synthetic local assessment/derived messages, v3 advisory, bounded offline state and resource limits |
| [Tire Health service (`CR-TIRE`)](component-decomposition-and-interface-register.md#cr-tire) | proposed `tire-health-service` | Local persistent condition model, bounded summary/event, offline queue, inspection advisory, SOTA 2 metadata and resource limits |
| [Aos lifecycle (`CR-AOS`)](component-decomposition-and-interface-register.md#cr-aos) | AosCore/AosCloud integration | Provisioning and retirement contracts, authoritative desired/reported actual and Unit Set state, recorded OEM-authorized approvals, FOTA/SOTA execution, targeting, native cross-lifecycle dependency admission and log transport |
| [Brake Health Cloud (`CR-BRAKE-CLOUD`)](component-decomposition-and-interface-register.md#cr-brake-cloud) | Function Team 1 | v1 window reconstruction, v2/v3 derived-message ingestion, idempotency, retention and Function Dashboard |
| [Tire Health Cloud (`CR-TIRE-CLOUD`)](component-decomposition-and-interface-register.md#cr-tire-cloud) | Function Team 2 | Tire condition/event ingestion, idempotency, retention and Function Dashboard |
| [Demo orchestration (`CR-DEMO`)](component-decomposition-and-interface-register.md#cr-demo) | `aosedge-sdv-demo` | Overlay lifecycle, Unit and Unit Set binding, stateless release workflow facilitation, evidence-backed final-approval presentation, owner/role-visible Software Delivery Dashboard, ordered retirement, next-run provisioning and factory-digest verification |
| [Cross-cutting concerns (`CR-CROSS`)](component-decomposition-and-interface-register.md#cr-cross) | Security and operational concerns across owners | Native Aos identity/permission lifecycle, credentials, redaction, timing and offline bounds; broker ownership remains in `CR-VDP` |
| [End-to-end acceptance (`CR-E2E`)](component-decomposition-and-interface-register.md#cr-e2e) | Cross-repository qualification | Stage acceptance, failure/offline/recovery, latency and traceability evidence |

Component requirements shall reference both their parent `SYS-*` requirement
and the relevant `AF-*` flow. Tests shall reference the component requirement,
system requirement and retained evidence identifier.

## Proposed Function Team 2 Repository Creation Gate

Before creating `tire-health-service`, reviewers shall confirm:

1. the initial source layout conforms to the accepted repository name and
   in-vehicle SOTA ownership boundary;
2. public visibility and Apache-2.0 licensing with copyright `maninblack`;
3. a `main`-only workflow for the current single-developer phase;
4. an ARM64 Aos service scaffold equivalent in quality to
   `brake-health-service`, but with a distinct service identity and SOTA 2
   provider metadata;
5. no CARLA, VISS, VM, platform-provider or Cloud credential dependency;
6. a versioned compatibility declaration for the accepted KUKSA contract;
7. explicit CPU, memory, persistent state, temporary storage, file, process, report-rate
   and offline-queue limits;
8. addition to `workspace/repositories.json` only after the initial repository
   revision exists and passes its repository gates.

No remote repository creation is authorized by acceptance of this baseline.

## Review Notes for Version 0.9

Version 0.9 retires the accepted low-rate `SYS-BHS-001` report concept while
preserving its anchor. `SYS-BHS-005` defines the bounded v1 braking-event
window and `SYS-BHS-006` defines the v2 derived Cloud data product;
`SYS-BHS-002` is clarified as a synthetic deterministic edge assessment and
`SYS-BHS-004` covers offline continuity for both window chunks and derived
messages. No HLA boundary, lifecycle owner or QM-authority decision changes.

## Acceptance Record for Version 0.8

Version 0.8 preserves the accepted Version 0.7 requirement set and adds
[`SYS-RET-006`](#sys-ret-006). The new requirement makes the cross-run boundary
explicit: R0 proves persistent Unit Sets empty after retirement, while the next
M1 creates new identities, assigns them to the correct disjoint sets and uses
only fresh lifecycle objects. Platform-contract obligations are allocated to
`CR-AOS`; sequencing, guards and overlay lifecycle are allocated to `CR-DEMO`;
the complete transition is allocated to `CR-E2E`.

## Acceptance Record for Version 0.7

Version 0.7 preserves the accepted Version 0.6 requirement set and adds
`SYS-REL-010`, `SYS-SEC-007`, and `SYS-OBS-006` for evidence-backed final OEM
approval, explicit QM classification, authoritative Gateway containment and
truthful Dashboard presentation.

The baseline was accepted on 2026-08-19 after reviewers confirmed
that:

1. every active Architecture Flows 1.4 gap is covered without claiming it is already
   implemented;
2. requirements are externally observable and testable;
3. the two Service Providers remain independent peers;
4. `tire-health-service` is the accepted repository name and owns
   only the in-vehicle SOTA 2 service;
5. each Function Team's backend and dashboard share its accepted independent
   Cloud-product repository and remain separate from its in-vehicle SOTA
   repository;
6. no requirement expands vehicle-control, driver-HMI or production-fleet
   scope;
7. component requirement packages align with HLA 1.4 and Demo Scenario 1.5;
8. deferred [native Cloud dependency rejection (`SYS-REL-006`)](#sys-rel-006)
   is not treated as implemented or replaced by custom
   dashboard policy before an implementing AosEdge release is qualified.
9. team-owned release decisions, Service Provider publication, OEM-authorized
   deployment approval, and AosCloud state/execution remain distinct as
   required by [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md).
10. fail-safe exclusive control and continuous mode handover now have stable,
    testable `SYS-CTRL-*` parents without expanding functional-service
    authority or changing the accepted audience scenario.
11. Service Manager and Aos IAM remain authoritative for SOTA instance
    identity, secret and registered permissions; no project-owned parallel
    identity or per-service policy store is required.
12. the broker signing key is per Unit and platform-protected, while the
    Factory Image and update artifacts contain neither that key nor static
    provider/service tokens.
13. both functional services are QM-domain applications and the Gateway is the
    final authoritative deny-by-default boundary for their outbound channel;
    and
14. the Software Delivery Dashboard exposes the evidence dossier preceding
    final OEM authorization without owning the decision, evidence or lifecycle
    state, and passing tests never auto-approve.
15. simulator cleanup is owned independently from factory-image preservation;
    the two remain coordinated only by the cross-system R0 lifecycle.
16. all Scenario, Manual, Autopilot and Safe Stop transitions have explicit
    world-context, obstacle, reset, failure and evidence semantics without
    adding reverse or obstacle-avoidance claims.
17. every installed hardware-equivalent signal, sensor and actuator is defined
    by one digest-addressed selected-vehicle profile rather than by the entire
    set of capabilities CARLA could theoretically instantiate;
18. complete Simulator–Gateway accounting, applied-control feedback and
    qualification-ground-truth isolation are required without implying that
    every native value is published through VSS/VISS or that every physical
    actuator is authorized for the current Control UI.

Following acceptance of this document and the Component Decomposition and
Interface Register, D3 expands the component requirement packages listed above.
Implementation planning follows only after those packages and their acceptance
tests are reviewed.
