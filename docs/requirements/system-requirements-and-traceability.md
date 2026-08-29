<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# System Requirements and Traceability 2.0

- Status: Accepted
- Version: 2.0
- Prepared: 2026-08-22
- Accepted: 2026-08-26
- Previous accepted version: 1.0
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.5](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0011](../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md),
  [ADR 0013](../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md),
  [ADR 0014](../architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Brake Cloud repository creation completed on 2026-08-28; no additional
  repository creation, implementation, signing, Cloud or Unit mutation is
  authorized by this requirements baseline alone

## Purpose

This document converts the accepted architecture-flow model and its twenty-two
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

1. High-Level Architecture 1.5 owns boundaries, authority and invariants.
2. Demo Scenario 2.0 owns the audience-visible stage progression.
3. Architecture Flows 2.0 owns detailed lifecycle, runtime, observability and
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
| `SYS-REL` | FOTA/SOTA targeting, dependency, validation and recovery |
| `SYS-VDP` | Vehicle Data Platform Component |
| `SYS-BHS` | Brake Health functional behavior |
| `SYS-TIRE` | Tire Health estimation, bounded reporting and advisory behavior |
| `SYS-SEC` | Security and authorization |
| `SYS-OBS` | Dashboards, logs, correlation and evidence |
| `SYS-TIM` | On-board/Cloud chronology; quantitative performance deferred |
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
then records acceptance of the exact Validation Unit result. The Platform Team
owns the corresponding FOTA validation and acceptance decision. OEM Release
Authority is an independent governance role outside those producer teams and
separately authorizes each Test deployment and Production rollout through the
authorized OEM delivery context. AosCloud remains the lifecycle system of
record and execution control plane.

| Repository | Ownership boundary | Lifecycle | State |
| --- | --- | --- | --- |
| `CarlaSim` | Virtual physical vehicle and upstream simulator behavior | Simulator source | Existing |
| `carla-ego-runtime` | Vehicle Gateway, control, VSS projection, VISS and Engineering Telematics Dashboard | Gateway tooling | Existing |
| `aos-vehicle-platform` | Shared Vehicle Data Platform Component, factory-installed KUKSA integration, provider runtime, separately packaged current-release Service-authorization helper and trusted Provider-side connection configuration | Platform FOTA plus separately governed factory/system integration | Existing; helper and accepted factory integration not yet implemented |
| `brake-health-service` | Function Team 1 on-board Brake Health application and local inference | Service Provider 1 / SOTA 1 | Existing |
| `tire-health-service` | Function Team 2 on-board tire-condition estimation, bounded reporting and inspection advisory | Service Provider 2 / SOTA 2 | **Proposed repository** |
| `brake-health-cloud` | Function Team 1 backend and Function Dashboard | Function Team 1 Cloud product | Isolated source foundation `68fe61b` over governance baseline `6da2926`; data packet proposed/review required |
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
| <a id="sys-mfg-002"></a>`SYS-MFG-002` | Clean SOP substrate | The factory image shall contain AosCore, KUKSA, security/update support, one stock Aos IAM configuration with `enablePermissionsHandler: true` independent of provisioning state, the dedicated non-secret `kuksa-jwt` certificate-module/PKCS#11 and verifier-preparation wiring, and the provider-specific empty-slot runtime, but no pre-populated service permission or `AOS_SECRET`, provider payload, functional service, Cloud registration, Cloud credential, signing key, shared static verifier or reusable per-vehicle secret. | `I,T` | `GAP-AF-01`, `GAP-AF-15` |
| <a id="sys-mfg-003"></a>`SYS-MFG-003` | Unique fresh overlays | Two fresh copy-on-write overlays created from the factory image shall generate distinguishable local identity material before provisioning and shall never share provisioned identity material. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-001"></a>`SYS-ID-001` | One identity per overlay | The provisioning flow shall create exactly one unique Unit and Main Node identity for each fresh overlay and bind them to the Validation and Production roles for one demo run. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-002"></a>`SYS-ID-002` | Reconcile partial provisioning | A timeout or partial provisioning result shall enter reconciliation and shall not be blindly retried or treated as a clean unprovisioned overlay. | `T,A` | `GAP-AF-03` |
| <a id="sys-id-003"></a>`SYS-ID-003` | Prove current Unit state | Before any update, the system shall prove the current Unit ID, Node ID, role, Unit Set membership, online state and current software graph of both Units. | `T,I` | `GAP-AF-03`, `GAP-AF-06` |
| <a id="sys-id-004"></a>`SYS-ID-004` | Qualify identity retirement | Retirement qualification shall prove offline-only deprovisioning, authoritative post-`204` reconciliation, old-certificate reconnect rejection, scoped Unit Set removal, Unit deletion, Unit-owned Node disappearance without inventing a Node-delete API, audit retention and recoverable partial-failure behavior. | `T,A` | `GAP-AF-03` |

### Vehicle source and release lifecycle

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-src-001"></a>`SYS-SRC-001` | Exact source-to-Unit binding | Each qualification or demonstration observation shall identify the exact live CARLA/VISS source, target Unit and frame range. The current demo shall use sequential exclusive live binding: Validation first, then explicit detach/reset and Production binding. Telemetry-trace replay is a deferred future option and is not part of the first implementation. | `T,I,D` | `GAP-AF-04` |
| <a id="sys-src-002"></a>`SYS-SRC-002` | Honest single-source presentation | The demo shall not imply that two simulated vehicles were running simultaneously when one CARLA/Gateway source was reused sequentially. | `I,D` | `GAP-AF-04` |
| <a id="sys-src-003"></a>`SYS-SRC-003` | Versioned vehicle hardware profile | The selected virtual vehicle shall have one digest-addressed Vehicle Hardware Capability Manifest that identifies the CARLA revision and ego blueprint and classifies every installed signal, sensor and actuator with its type, unit, frame, cadence or command range, availability semantics and provenance; a capability that CARLA can theoretically create but that is not installed in the selected profile shall be declared `NOT_INSTALLED` rather than implied to exist. | `T,I` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-src-004"></a>`SYS-SRC-004` | Complete Simulator–Gateway accounting | Across the selected hardware profile, the Simulator and Gateway shall account for every declared capability without silent loss: installed state shall be delivered or explicitly unavailable/unsupported; actuator commands shall be accepted or rejected with bounded status and the actually applied control state shall be observable; simulator ground truth and qualification-only oracle state shall remain outside the production vehicle-data interface. | `T,I,A` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-rel-001"></a>`SYS-REL-001` | Immutable release candidates | Every FOTA and SOTA candidate shall have a producer-owned canonical manifest and immutable prepared artifact identified by semantic version, prepared SHA-256 and canonical manifest SHA-256 before presentation. The pinned Demo Release Set shall select only approved candidate IDs; presentation-time work may verify, sign and upload frozen inputs but shall not build, regenerate or silently substitute content. Prepared, signed/uploaded and Cloud identities shall remain distinct and traceably linked. | `T,I` | `GAP-AF-05`, `GAP-AF-07`, `GAP-AF-20` |
| <a id="sys-rel-002"></a>`SYS-REL-002` | Current effective-target validation | Immediately before approval, the delivery workflow shall enumerate every Unit in the applicable Fleet/OEM visibility scope, derive effective targets from their current pending-batch state, compare the resulting exact Unit-ID set with the intended Unit Set and block stale, missing, unexpected or unprovable targets. | `T,I` | `GAP-AF-06` |
| <a id="sys-rel-003"></a>`SYS-REL-003` | Service capability compatibility | Each SOTA service artifact shall carry a versioned Vehicle Data Platform Component compatibility range and shall fail closed at startup/readiness when the installed capability is absent or incompatible. | `T,I` | `GAP-AF-20` |
| <a id="sys-rel-004"></a>`SYS-REL-004` | Validate once, then apply by update-state policy | A candidate shall be installed, qualified and explicitly accepted by its owning team on the Validation Unit before the identical accepted bytes and digest are promoted to the Production Unit. The Production Unit shall be an authorized rollout and live-operation target, not a second product-validation lane; post-rollout actual-state/readiness checks confirm delivery health only. Vehicle Data Platform Component FOTA shall be delivered through AosCloud/AosCore but applied only after the factory-installed OEM Component Runtime proves the accepted Safe Stop policy from Gateway samples fresh at acquisition, a consecutive stability history that is not current-state authority, and a latest complete sample revalidated immediately before every destructive step; the UI shall present, but not duplicate, that in-vehicle gate and shall not claim that AosCloud evaluates physical motion. The accepted Brake/Tire QM Service SOTA may be applied while the vehicle moves, subject to all other release gates. | `T,I,D` | `GAP-AF-06`, `GAP-AF-20` |
| <a id="sys-rel-005"></a>`SYS-REL-005` | Dependent-first recovery | Recovery shall stop/remove the dependent SOTA service before changing a platform capability on which it depends, preserve unaffected service/platform lifecycles and then revalidate/reassign the dependent service. FOTA may use `RevertUpdate` only before `ApplyUpdate`; after Apply it shall use a new signed forward-repair version. SOTA removal is supported, while exact selection of a previous Service Version remains unqualified and shall not be claimed. | `T,A` | `GAP-AF-05`, `GAP-AF-20` |
| <a id="sys-rel-006"></a>`SYS-REL-006` | Native Cloud Service-to-VDP rejection | AosCloud shall natively reject a SOTA request whose declared FOTA Vehicle Data Platform Component range is not satisfied on the intended Unit before changing Subject-service desired state, creating a validation batch or campaign, or transferring update content to the Unit, and shall return an authoritative machine-readable reason. Existing component-to-component and service-to-layer dependency mechanisms remain supported platform capabilities and are outside this deferred cross-lifecycle requirement. | `T,I,D` | `GAP-AF-20` |
| <a id="sys-rel-007"></a>`SYS-REL-007` | Team-owned release decisions | The Platform Team shall own every Vehicle Data Platform Component release decision, Function Team 1 shall own every Brake Health release decision, and Function Team 2 shall own every Tire Health release decision; passing evidence or a dashboard action shall not silently substitute for explicit owner acceptance. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-rel-008"></a>`SYS-REL-008` | Separate producer acceptance and OEM deployment authorization | A Function Team shall use its Service Provider identity to publish and technically verify its service artifact. The owning Platform, Brake or Tire team shall explicitly accept the exact Validation Unit result. OEM Release Authority, as an independent governance role outside those producer teams, shall separately authorize every Test or Production Unit deployment through the authorized OEM delivery context. AosCloud shall record the owner acceptance, Release Authority decision, artifact version/object identity, target and transition; the demo shall bind those records to the exact retained publication digest chain and shall not claim a Cloud-side SOTA content digest where the released API exposes none. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-rel-009"></a>`SYS-REL-009` | Dependent-release milestone gate | Every VDP FOTA and dependent Service SOTA shall retain its own owner acceptance, OEM authorization, Cloud lifecycle object and result. A dependent Service shall not be promoted to a target until the required VDP is actually ready there. G3/G4 shall be derived capability milestones only, complete after both releases and their live behavior are proven, with no combined Cloud object, atomic group approval or cross-team rollback. | `T,I,D` | `GAP-AF-17`, `GAP-AF-20` |
| <a id="sys-rel-010"></a>`SYS-REL-010` | Evidence-backed OEM Release Authority decision | Before a Test deployment or Production rollout action is enabled, the workflow shall present and bind the exact artifact and service-metadata digests, requested permissions, effective target, required evidence with freshness/status, applicable owning-team acceptance and active OEM Release Authority context. Any missing, stale, failed or mismatched prerequisite shall block the action; passing evidence shall never auto-authorize; the explicit Release Authority decision shall be recorded in AosCloud and followed by an authoritative state re-read. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-rel-011"></a>`SYS-REL-011` | Role-bound protected publication | Exactly three non-interchangeable current-demo publication profiles shall bind Platform OEM to VDP Component FOTA, Service Provider 1 to Brake Health SOTA and Service Provider 2 to Tire Health SOTA. One session-scoped non-root native helper may implement all profiles, but each dashboard surface shall be pre-bound to one profile and shall not select a credential path, profile, arbitrary candidate path or Cloud URL. The installed `aos-signer` 2.0.1 compatibility path shall use one local mode-`0600`, Git-excluded passwordless PKCS#12 per profile for both signing and mTLS upload; no dashboard, container, VM image or artifact may receive it. Only an independent AosCloud re-read may establish `PUBLISHED`; an ambiguous result shall be reconciled as `UNCERTAIN` without blind retry, and technical publication shall never perform OEM deployment approval. | `T,I,A,D` | `GAP-AF-17` |
| <a id="sys-rel-012"></a>`SYS-REL-012` | Independent resource-scoped release operations | Platform, Brake and Tire protected mutations shall be coordinated per exact candidate/operation and resource-conflict key set rather than through a demo-wide operation lock. Active or unresolved operations on disjoint candidate/digest/profile, Cloud-object, Batch/Campaign, Unit and Unit-Set keys may proceed independently; only overlapping keys shall block. Provisioning, identity retirement, exclusive live-source handover/reset and R0 freeze/cleanup shall remain run-exclusive. Restart shall reconcile every non-terminal operation from fresh authoritative state without blind retry, while read-only views remain available. Local helper capacity shall affect only the requested operation and shall neither be presented as an AosCloud restriction nor automatically queue or trigger another team's action. | `T,I,A,D` | `GAP-AF-17` |

[Native Cloud Service-to-VDP rejection (`SYS-REL-006`)](#sys-rel-006) is
**deferred and blocked on an implementing AosEdge platform
release**. The Platform Team reported the capability as roadmap work on
2026-08-18, without an available release or date. No project-side admission
controller is an acceptable substitute. `SYS-REL-003` remains required as
defense in depth before and after the native Cloud feature becomes available.
This deferral is not a claim that AosEdge lacks dependency management:
released component-to-component runtime dependencies and version-bounded
service-to-layer dependencies remain available and shall be used where their
native contracts fit the graph.

### Vehicle control and handover

`SYS-CTRL-001` and `SYS-CTRL-002` are corrective allocations discovered while
deriving the first component packages. `SYS-CTRL-003` preserves the historical
Scenario 1.4 and Architecture Flows 1.3 mode/context refinement now carried
forward by Scenario 1.9 and Flows 1.8. The
set does not add a demo stage, authority, architectural boundary or data
direction.

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ctrl-001"></a>`SYS-CTRL-001` | Fail-safe exclusive vehicle control | The vehicle-control path shall remain separate from VISS/KUKSA vehicle-data paths, permit exactly one authenticated control owner, reject invalid, replayed, out-of-mode or simultaneous throttle/brake commands, enforce bounded command and ownership deadlines, and select safe stop on startup, timeout, release, disconnect, applicable focus loss, shutdown or controller failure. No functional SOTA service shall gain vehicle-motion authority. | `T,I,D` | Accepted HLA/flow baseline correction |
| <a id="sys-ctrl-002"></a>`SYS-CTRL-002` | Continuous control-mode handover | Transitions among manual, autopilot, scripted scenario and safe stop shall preserve one ego actor, one synchronous clock owner, the active run/frame identity and uninterrupted Gateway telemetry; transitions shall be pedal-safe and bounded, and manual takeover of an unfinished scripted attempt shall record an abort rather than a false pass or failure. | `T,I,D` | Accepted HLA/flow baseline correction |
| <a id="sys-ctrl-003"></a>`SYS-CTRL-003` | Deterministic mode/context transition | The solution shall implement the complete `AF-X-DRIVE` matrix with independent drive-mode and `FREE_DRIVE`/`BRAKE_EVENT` world-context state: manual takeover shall retain brake-event position and obstacle; entry to Scenario shall perform a canonical reset and new generation; entry to Autopilot from brake-event context shall safe-stop, remove scenario-owned obstacle state, reset the same actor to an accepted free-drive start with zero motion and validate lane alignment before enabling Traffic Manager; safe stop alone shall not reset context. The controller shall publish state only for real completed CARLA frames: no frame is fabricated while reset blocks, the first successful post-reset frame alone marks discontinuity with the incremented reset generation, and a failed reset with no completed frame creates no success evidence. Any failed transition shall remain in safe stop without partial mode activation. Reverse and Autopilot obstacle avoidance shall not be required or claimed. | `T,I,D` | `GAP-AF-24` |

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
| <a id="sys-bhs-005"></a>`SYS-BHS-005` | Bounded v1 Brake Telemetry Window | Service v1 shall derive only `HARD_BRAKING_EPISODE_V1` from its accepted six-path Brake subset of VDP v1, retain deterministic 10 Hz valid samples, and produce one idempotent 3-second PRE, no-more-than-10-second ACTIVE and 2-second POST window bounded to 150 samples. Transfer begins while braking is visible; RFC-8785/SHA-256 chunks are bounded to ten samples/64 KiB and become eligible only after crash-safe local persistence. Completion states and the unacknowledged spool remain bounded to the accepted D4-016.1/.2 limits, with no continuous upload, fabricated input, database dependency, pre-durability send or eviction of retained windows. | `T,I,D` | `GAP-AF-07` |
| <a id="sys-bhs-002"></a>`SYS-BHS-002` | Deterministic v2 edge assessment | Service v2 shall use the immutable digest-bound `brake-condition-demo-v1` model and disclosed `DEMO_PRECONDITIONED` profile on an exact VDP v2 subset: speed, longitudinal acceleration, brake pedal, steering angle and four linear plus four angular wheel speeds. It shall derive local braking features, maintain bounded crash-safe synthetic condition state, prevent double-counting after restart and produce deterministic `BrakeHealthAssessment` results and band-change events without claiming production diagnostic accuracy or a safety function. Invalid/insufficient input shall not advance state or produce `GOOD`. | `T,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-006"></a>`SYS-BHS-006` | Derived v2 Cloud data product | Normal Service v2 operation shall send only bounded, versioned and idempotent `BrakeHealthAssessment` and threshold/change `BrakeHealthEvent` messages to the functional backend rather than Service v1 high-detail telemetry windows; the dashboard shall make that processing and traffic change visible. | `T,I,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-003"></a>`SYS-BHS-003` | Allowlisted v3 advisory | Service v3 shall request only the accepted Brake Health advisory target and shall not gain arbitrary display-text or vehicle-motion authority. | `T,I` | `GAP-AF-10`, `GAP-AF-15` |
| <a id="sys-bhs-004"></a>`SYS-BHS-004` | Offline local continuity | Brake Health local assessment and advisory shall continue without Cloud connectivity; in-progress/completed v1 windows and v2/v3 derived functional messages shall use bounded retention, retry and idempotent synchronization with original sample/event times. | `T,A,D` | `GAP-AF-11` |

D4-016.1/.2/.3/.4/.5 are accepted. The D4-017 Cloud transport/store/reset
values remain an executable review candidate in the
[contract index](../../contracts/README.md). D4-003 calibration remains an
implementation-acceptance gate for the accepted model. These contracts refine
the stable system requirements without changing their authority or adding a
new component.

### Tire Health function

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-tire-001"></a>`SYS-TIRE-001` | Single mature service on VDP v3 | The current demo shall deliver one mature Tire Health Service v1.0 candidate after VDP Component v3 is accepted; the service shall consume only the dynamics and advisory contract already present in VDP v3 and shall not require a new Platform Team feature request or a Tire v1-v3 product progression. | `I,T,D` | `GAP-AF-21` |
| <a id="sys-tire-002"></a>`SYS-TIRE-002` | Local persistent condition estimate | The service shall maintain a bounded, persistent and versioned tire-condition estimate from its accepted input subset and shall produce an estimated condition band rather than claim an exact measured tread depth. | `T,A,D` | `GAP-AF-21` |
| <a id="sys-tire-003"></a>`SYS-TIRE-003` | Explicit simulation model | The CARLA scenario shall provide a deterministic, clearly labelled accelerated-time or pre-aged tire-degradation stimulus with hidden ground truth used only for qualification. | `T,I,D` | `GAP-AF-21` |
| <a id="sys-tire-004"></a>`SYS-TIRE-004` | Bounded Cloud reporting | The service shall upload only bounded, versioned and idempotent condition summaries or threshold events and shall retain them within explicit offline, rate and storage limits instead of continuously streaming raw telemetry. | `T,I,A` | `GAP-AF-21`, `GAP-AF-23` |
| <a id="sys-tire-005"></a>`SYS-TIRE-005` | Independent Tire Health product | Function Team 2's backend shall ingest bounded Tire Health results idempotently and its dashboard shall expose condition band, event time/status, service and capability versions, Unit role and online/offline delivery state. | `T,D` | `GAP-AF-23` |
| <a id="sys-tire-006"></a>`SYS-TIRE-006` | Offline inspection advisory | Local estimation and inspection-advisory generation shall continue without Cloud connectivity, and the service shall request only its typed allowlisted Tire Health target without vehicle-motion or arbitrary-display authority. | `T,I,A,D` | `GAP-AF-22`, `GAP-AF-23` |

Accepted D4-018 and D4-019 define the exact in-vehicle and Cloud contracts.
D4-020 proposes their physical Mac/QEMU route.
The first demo uses lightweight isolated local functional-backend transport
without per-Unit backend credentials; `system_uid` is correlation-only and
production backend authentication remains independently Function Team-owned
and out of scope. Signed updates, OEM authorization and in-vehicle
Aos IAM/KUKSA/Gateway security remain unchanged. The candidate numeric values
and two-VM route integration require human review and live qualification before
implementation acceptance.

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

### Security, observability and chronology

#### Retired Security Requirement

The former `SYS-SEC-002` required a second FOTA-managed per-Service OEM policy
inside the VDP-owned broker. Architecture 1.3 removed that duplicate policy,
and Architecture 1.5 subsequently moved current-release translation out of
VDP. `SYS-SEC-005` is also retired because the first demo explicitly trusts the
OEM-qualified VDP as platform integration rather than adding a dynamic
Provider credential protocol. `SYS-SEC-006` is retired because its actor and
authority boundary changed materially.

| Retired identifier | Replacement | Reason |
| --- | --- | --- |
| <a id="sys-sec-002"></a>`SYS-SEC-002` | [`SYS-SEC-008`](#sys-sec-008) | Duplicate local OEM policy remains prohibited; active Aos IAM state is authoritative |
| <a id="sys-sec-005"></a>`SYS-SEC-005` | Trusted VDP platform integration in [`SYS-SEC-001`](#sys-sec-001) | Dynamic Provider credential/attestation is outside first-demo scope; no Service JWT grants provider authority |
| <a id="sys-sec-006"></a>`SYS-SEC-006` | [`SYS-SEC-008`](#sys-sec-008) | Service authorization translation moved from VDP into separately packaged current-release `CMP-KAC` with new lifecycle semantics |

#### Retired Lifecycle Timing Requirement

`SYS-TIM-001` is no longer an active first-demo requirement. Measuring Cloud
lifecycle stage duration and building technical/executive timing views did not
support the primary vehicle demonstration. Per-operation uncertainty and
reconciliation remain covered by their owning lifecycle requirements; future
in-Unit performance benchmarking is tracked separately in the roadmap.

| Retired identifier | Replacement | Reason |
| --- | --- | --- |
| <a id="sys-tim-001"></a>`SYS-TIM-001` | Deferred Edge Runtime Performance Qualification | Replaced Cloud lifecycle timing KPIs with a future vehicle/VM-focused benchmark workstream |

#### Active Security, Observability and Chronology Requirements

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-sec-001"></a>`SYS-SEC-001` | Least-privilege KUKSA identities | Brake Health and Tire Health Service instances shall use distinct IAM-derived least-privilege identities and path-level permissions. Provider-side KUKSA access shall belong only to the OEM-qualified trusted VDP integration and shall never be obtainable through a functional Service credential. The first demo shall not claim dynamic Provider IAM/JWT, per-component attestation, or containment of a malicious/substituted VDP. | `I,T` | `GAP-AF-15` |
| <a id="sys-sec-003"></a>`SYS-SEC-003` | Fail-closed advisory security | Unauthorized, malformed, stale or replayed advisory requests shall fail closed and produce factual non-driver status evidence. | `T,A` | `GAP-AF-10`, `GAP-AF-15`, `GAP-AF-22` |
| <a id="sys-sec-004"></a>`SYS-SEC-004` | Per-Unit KUKSA signer and verifier | Successful provisioning shall establish one unique non-exported RSA signing key per Unit lifecycle through the dedicated Aos certificate-module/PKCS#11 integration, then atomically install only its public verifier before the current-release helper and unmodified KUKSA start. KUKSA shall enforce `RS256` signature, fixed audience `kuksa.val`, expiry and path permissions; its pinned implementation shall not be credited with enforcing `iss`. Service JWT lifetime shall be 300 seconds with renewal at 180 seconds through a fresh IAM lookup and mandatory KUKSA reconnect/subscription recreation; permission removal shall prevent renewal, Validation and Production fingerprints shall differ, and cross-Unit tokens shall fail. No signing key or shared static verifier shall be baked into the Factory Image or an FOTA/SOTA artifact; first-demo rotation occurs only through fresh provisioning, and R0 destroys the key with the retired VM overlay. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-sec-007"></a>`SYS-SEC-007` | QM service and Gateway containment | Brake Health and Tire Health shall remain QM-domain maintenance/inspection applications with no allocated safety goal, direct driver-HMI claim, vehicle-motion authority or safety-critical actuator access. The VDP shall validate outbound advisories as defense in depth, and the Vehicle Gateway shall be the final authoritative boundary for the QM-origin channel: it shall accept only Platform-owned typed non-safety advisories, validate target/type/range/freshness/rate/correlation, report factual status, and reject arbitrary VSS writes and every throttle, brake, steer, gear, motion or safety-critical operation. | `T,I,A,D` | `GAP-AF-10`, `GAP-AF-15`, `GAP-AF-22` |
| <a id="sys-sec-008"></a>`SYS-SEC-008` | Current-release KUKSA Service authorization compatibility | A separately packaged platform helper outside VDP and both SOTA payloads shall accept only an active Service instance's native `AOS_SECRET` plus one fixed KUKSA resource identifier, call Aos IAM `GetPermissions` through fixed TLS loopback `127.0.0.1:8090` with Aos CA trust and expected server name `main` and no DNS, caller-selected endpoint, external IP or KAC TCP listener, map only exact `r` paths to KUKSA `read` and exact `rw` paths to KUKSA `actuate`, and reject `w`, wildcards, partial trimming and all Service `provide/create` authority. It shall deliver a 300-second JWT only to that Service's private volatile location, renew at 180 seconds through a fresh IAM lookup, and require reconnect/subscription recreation with the replacement. Each provisioned Unit shall own one non-exportable `kuksa-jwt` RSA key; a protected sign/verify preparation gate shall atomically publish only the volatile public verifier, and KUKSA plus the helper shall fail closed unless KUKSA starts with that exact verifier. Authorization readiness shall require one NTP synchronization and 10 stable seconds per boot; epoch claims shall use UTC while scheduling uses boottime. The temporary helper shall compare elapsed wall/boottime immediately before every issue or renewal and reject a deviation greater than five seconds as `TIME_UNTRUSTED`, but shall add no anchor, continuous monitor, KUKSA lifecycle controller or instant revocation; an already issued JWT may remain usable only until signed expiry. Normal later external-connectivity loss shall not revoke trust or disable the inside-Unit IAM loopback. Recovery requires synchronized time plus a new stable window, while cold offline boot remains authorization `NOT_READY` without blocking unrelated AosCore. Frames, permission/path/JWT size, concurrency, backlog, rate, timeout, retry and process resources shall follow the closed D4-027.8 envelope and emit only fixed redacted diagnostics. The caller shall not select paths, operations, subject, audience, TTL, claims or signing input. Invalid, inactive, stale, broadened, malformed, cross-instance/Unit or unsupported authority, unavailable IAM/helper, or failed signer/verifier/time preparation shall issue no new JWT. The Service shall connect directly to KUKSA after preparation. Reboot shall recreate the verifier and reconstruct authority from active platform state; stop, removal or unregistration shall prevent renewal and remove private credential state. VU and PU trust shall remain distinct, and R0 overlay disposal shall retire the Unit key. No parallel Service identity/policy database, file-key fallback or instant-revocation claim is permitted. The future released native AosCore contract shall be requalified for trustworthy time, bounded credential invalidation and recovery before this helper is removed. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-obs-001"></a>`SYS-OBS-001` | Authoritative demo surfaces | Every audience claim shall identify its authoritative surface: CARLA for physical stimulus, Engineering Telematics Dashboard for Gateway state, AosCloud for software lifecycle and native log requests/results, OEM Software Delivery Dashboard for role-scoped system/VDP log presentation, and each functional dashboard for its own backend data plus its own Service-owned service-instance/crash-log presentation. | `I,D` | `GAP-AF-17` |
| <a id="sys-obs-002"></a>`SYS-OBS-002` | Cloud-authoritative delivery dashboard | The Software Delivery Dashboard shall read and re-read authoritative AosCloud lifecycle plus Cloud-retained OEM-scoped Unit system/VDP log request/result/file state, display the business decision owner and active Cloud role, require explicit confirmation before an OEM-authorized mutation or system-log request, and shall not maintain an independent desired-state database, second log archive or automatic approval policy. Service-instance and crash-log requests belong to the matching Brake or Tire Function Dashboard under a separately allowlisted SP operational context; they shall not create an omni-credential in the Software Delivery Dashboard. Presenter Mac/Native Helper connectivity to AosCloud is a demo precondition rather than an automotive offline claim: its loss blocks administrative actions with an infrastructure error and is never displayed as Unit offline behavior. | `T,I` | `GAP-AF-06`, `GAP-AF-16`, `GAP-AF-17` |
| <a id="sys-obs-003"></a>`SYS-OBS-003` | Operational log controls | Native system logs shall use the role-scoped `/api/v11/unit-logs/` list/create/read/download/delete family through `oem-delivery`; Brake and Tire service-instance/crash logs shall use the corresponding `/api/v11/service-logs/` family through separate SP1/SP2 operational contexts. Before those logs are presented as demo evidence, the solution shall qualify exact Unit/Node identifiers, timestamps, effective permissions and ownership filtering, create-response cardinality, documented Cloud states, file/archive bounds, explicit deletion effect and online/offline/reconnect behavior. Emitters and dashboards shall enforce structured allowlisted redaction, temporary downloads shall be bounded and removed, and no second archive shall be created. Because current API v11 exposes no retention policy, the demo shall state `Retention policy not exposed by current API`; it shall not claim a fixed or indefinite duration or present retrieval duration as a vehicle KPI. | `T,I,A` | `GAP-AF-16` |
| <a id="sys-obs-004"></a>`SYS-OBS-004` | Per-run correlation | Before provisioning, a demo run shall be correlated by start time and local overlay roles; after provisioning it shall be correlated by the two Unit IDs and the same bounded time window. | `T,I` | `GAP-AF-19` |
| <a id="sys-obs-005"></a>`SYS-OBS-005` | Truthful control-transition evidence | The Gateway engineering projection and Engineering Telematics Dashboard shall expose the current drive mode, world context, scenario state/result, generation and reset/discontinuity state as simulator-derived facts so that reset teleportation is never interpreted as physical vehicle motion. Controller-derived facts shall join physical state only on exact CARLA frame ID and simulation time; an absent or rejected controller record shall omit the entire control/reset group for that frame rather than reuse prior state. Presenter operation progress shall remain separate from vehicle telemetry. | `T,I,D` | `GAP-AF-24` |
| <a id="sys-obs-006"></a>`SYS-OBS-006` | Visible approval decision basis | The Software Delivery Dashboard shall distinguish validation evidence, owning-team acceptance and the final OEM authorization; show the exact candidate, requested permissions, target, evidence status and active role before confirmation; explain blocked prerequisites; and shall not claim that its button, passing tests or locally retained data constitute the approval, authoritative lifecycle state, proof that software is safe, or functional-safety certification. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-obs-007"></a>`SYS-OBS-007` | Targeted vehicle external-connectivity continuity | One stateful demo control shall atomically remove or restore the currently selected Validation or Production Unit's external vehicle connectivity; the normative `G4/X-OFFLINE` presentation uses the Production Unit. In the disconnected state, both selected-Unit-to-AosCloud and installed service-to-functional-backend paths shall be blocked, while the other running VM, presenter-to-AosCloud and simulated in-vehicle CARLA/Gateway/VISS/KUKSA paths remain available. The dashboard shall continue to read AosCloud, show authoritative Unit offline/online state and unavailable lifecycle/log actions; reachable Function Dashboards shall show delayed/offline rather than current vehicle results. Local inference and advisory shall continue. On reconnect, the same selected Unit shall return online without reprovisioning, reinstalling or restarting, and bounded functional messages shall synchronize idempotently with original event time separate from receipt/synchronization time. Separate per-channel fault switches shall not be exposed. | `T,I,D` | `GAP-AF-25` |
| <a id="sys-res-001"></a>`SYS-RES-001` | AosCore-enforced service-tenant isolation | Accepted service metadata shall carry independently approved Brake and Tire service quotas, and AosCore/Service Manager shall be the sole in-vehicle enforcement and monitoring authority. The first demo shall run one prepared bounded CPU-load profile inside the actual Tire Health service cgroup until that instance reaches its own quota; AosCore shall cap it and report fresh exact-instance usage/state in DMIPS through AosCloud while Brake Health processes the deterministic CARLA event without restart or degradation and VDP, KUKSA, Gateway and AosCore remain healthy. A quota alert is supplementary. Final technical acceptance shall additionally use separately labelled read-only cgroup cap/throttle evidence bound to the exact Factory Image, AosCore, Service artifact/configuration and Node DMIPS baseline; Service/backend control state is not enforcement proof. Stopping the load shall return Tire to normal without reinstall or restart. No project resource manager shall be introduced. Mac-local functional backends and aggregate quota enforcement across several services owned by one Service Provider are outside this proof. | `T,I,D` | `GAP-AF-26` |
| <a id="sys-tim-002"></a>`SYS-TIM-002` | Separate on-board and Cloud chronology | Brake Health and Tire Health messages shall preserve distinct source-event, local-decision/advisory, Gateway-observation and backend receipt/synchronization timestamps so that Cloud delivery is never presented as part of the on-board decision path. Causality is proven by identifiers, producer epoch/sequence, source generation/frame and states rather than cross-clock comparison. The evidence proves only demo causal linkage and reconnect behavior; production clock synchronization, worst-case latency, real-time, network and safety claims are excluded. | `T,A,D` | D4-024 design reviewed; implementation/live qualification open |

### Retirement and next-run reset

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ret-001"></a>`SYS-RET-001` | Retire Units and overlays | R0 shall finish the final authoritative read, place both Units offline through a qualified bounded local operation, wait until AosCloud reports each `Offline`, call the OEM offline-only deprovision API, reconcile its no-body `204`, prove retired credentials cannot return either Unit `Online`, stop the VMs, delete exact current-run log requests, remove each Unit from its role set by `system_uid`, delete each Unit by Cloud UUID, and prove Unit absence, empty sets and inaccessible Unit-owned Nodes before discarding the provisioned overlays. The current API exposes no standalone Node-delete operation and none shall be invented. | `T,I,A` | `GAP-AF-03`, `GAP-AF-19` |
| <a id="sys-ret-002"></a>`SYS-RET-002` | Clear functional run data | Functional backends shall first preview and then permanently delete all dashboard-visible data selected by exact equality with the current Test Vehicle and Production Vehicle Unit `system_uid` values supplied by the injected current-run provisioning context. The Test Vehicle retains the internal `VALIDATION` wire role. Empty, wildcard, partial, non-current or additional recipients shall block deletion. The preview shall bind an explicitly enumerated RFC-8785/SHA-256 logical row-set digest and counts; a process-local HMAC token shall be bounded to 1024 characters, expire after 60 seconds and require a new preview after every backend restart. Malformed, bad-MAC, expired and previous-process tokens shall return `409 PREVIEW_TOKEN_EXPIRED`; only a valid-MAC token bound to a changed current row set shall return `409 PREVIEW_STALE`. Fresh provisioning gives every run new Unit identities, so no `demoRunId`, independent time-window selector or historical demo-run archive is required. After successful R0, no matching demo telemetry, events, advisories or dashboard records remain; authoritative AosCloud lifecycle and audit history remains owned and retained by AosCloud. | `T,I` | `GAP-AF-19` |
| <a id="sys-ret-003"></a>`SYS-RET-003` | Reset vehicle simulation state | R0 shall safe-stop the ego vehicle, remove only scenario-owned CARLA actors and sensors, restore changed CARLA world and Traffic Manager settings, clear run-local simulation evidence and report incomplete cleanup before the next run. | `T,I` | `GAP-AF-04` |
| <a id="sys-ret-004"></a>`SYS-RET-004` | No rollback or fleet claim | The normal demo reset shall not be presented as a G4-to-G0 OTA rollback or as a production-fleet vehicle deletion policy. | `I,D` | `GAP-AF-03` |
| <a id="sys-ret-005"></a>`SYS-RET-005` | Preserve immutable factory artifact | R0 shall not modify or replace the accepted OEM Demo Factory Image; after provisioned overlays are retired and discarded, the system shall verify and retain the same immutable factory-image digest as the source for the next M0 deployments. | `T,I` | `GAP-AF-01`, `GAP-AF-19` |
| <a id="sys-ret-006"></a>`SYS-RET-006` | Reconcile Unit Sets for the next run | R0 shall prove that the persistent Verification and Production Unit Sets contain no retired Unit and are empty after Cloud deprovisioning and Unit deletion. The next M1 shall provision new Unit and Node identities, assign exactly one new Validation Unit and one new Production Unit to their correct disjoint sets, and shall not reuse prior-run batch, validation, Campaign or target assumptions after membership changes. | `T,I,A` | `GAP-AF-03`, `GAP-AF-06`, `GAP-AF-19` |

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
| `GAP-AF-15` | `SYS-MFG-002`, `SYS-BHS-003`, `SYS-TIRE-006`, `SYS-SEC-001`, `SYS-SEC-003`, `SYS-SEC-004`, `SYS-SEC-007`, `SYS-SEC-008` |
| `GAP-AF-16` | `SYS-OBS-003` |
| `GAP-AF-17` | `SYS-REL-007`, `SYS-REL-008`, `SYS-REL-009`, `SYS-REL-010`, `SYS-REL-012`, `SYS-OBS-001`, `SYS-OBS-002`, `SYS-OBS-006` |
| `GAP-AF-19` | `SYS-OBS-004`, `SYS-RET-001`, `SYS-RET-002`, `SYS-RET-005`, `SYS-RET-006` |
| `GAP-AF-20` | `SYS-REL-001`, `SYS-REL-003`, `SYS-REL-004`, `SYS-REL-005`, deferred `SYS-REL-006` |
| `GAP-AF-21` | `SYS-TIRE-001`, `SYS-TIRE-002`, `SYS-TIRE-003`, `SYS-TIRE-004` |
| `GAP-AF-22` | `SYS-VDP-004`, `SYS-TIRE-006`, `SYS-SEC-003`, `SYS-SEC-007` |
| `GAP-AF-23` | `SYS-TIRE-004`, `SYS-TIRE-005`, `SYS-TIRE-006` |
| `GAP-AF-24` | `SYS-CTRL-003`, `SYS-OBS-005` |
| `GAP-AF-25` | `SYS-OBS-007` |
| `GAP-AF-26` | `SYS-RES-001` |

All twenty-two active architecture-flow gaps have explicit requirement coverage.
Retired gaps `GAP-AF-12` through `GAP-AF-14` and `GAP-AF-18` resolve to their replacements in
Architecture Flows 2.0. This
does not mean they are resolved; each remains open until its linked
requirements have accepted evidence.

## Component Requirement Package Allocation

The canonical component IDs, interface IDs, repository candidates and package
boundaries are defined in the
[Component Decomposition and Interface Register 2.0](component-decomposition-and-interface-register.md).
The next derivation step shall expand the following packages. A system
requirement may allocate obligations to several packages and one integration
test.

| Package | Primary repository or owner | Main allocation |
| --- | --- | --- |
| [Vehicle simulation (`CR-VEHICLE-SIM`)](component-decomposition-and-interface-register.md#cr-vehicle-sim) | `CarlaSim` plus scenario tooling in `carla-ego-runtime` | Versioned vehicle hardware profile, complete installed signal/actuator boundary, deterministic braking and tire stimuli, reset, timestamps and isolated hidden-ground-truth qualification |
| [Vehicle Gateway (`CR-GATEWAY`)](component-decomposition-and-interface-register.md#cr-gateway) | `carla-ego-runtime` | Complete hardware-profile accounting, actuator-command/applied-state traceability, vehicle sampling, VSS/VISS contracts, source status, authoritative QM-channel advisory containment and Engineering Telematics Dashboard |
| [Factory substrate (`CR-FACTORY`)](component-decomposition-and-interface-register.md#cr-factory) | Platform Team / `aos-vehicle-platform` | Factory image with `enablePermissionsHandler: true` in the shared IAM configuration, no pre-populated service permission/secret state, dedicated non-secret `kuksa-jwt` certificate-module/PKCS#11 and verifier-preparation wiring but no key/shared verifier, provider-specific empty-slot runtime, identity absence, overlay creation and immutable artifact preservation |
| [Vehicle Data Platform (`CR-VDP`)](component-decomposition-and-interface-register.md#cr-vdp) | `aos-vehicle-platform` | Component v1-v3, KUKSA data/advisory contract, defense-in-depth outbound policy and OEM-trusted Provider-side connection qualification; no Service JWT issuance |
| [Current-release KUKSA authorization compatibility (`CR-KAC`)](component-decomposition-and-interface-register.md#cr-kac) | Platform Team / `aos-vehicle-platform` | Separately packaged removable helper, fixed-resource bootstrap, IAM mapping, protected signing, private volatile delivery, renewal/reboot/stop/removal lifecycle and native-migration deletion seam |
| [Brake Health service (`CR-BHS`)](component-decomposition-and-interface-register.md#cr-bhs) | `brake-health-service` | v1 event-window recorder, v2 synthetic local assessment/derived messages, v3 advisory, bounded offline state and resource limits |
| [Tire Health service (`CR-TIRE`)](component-decomposition-and-interface-register.md#cr-tire) | proposed `tire-health-service` | One mature v1.0 candidate on VDP v3: local persistent condition model, bounded summary/event, offline queue, inspection advisory, SOTA 2 metadata and resource limits |
| [Aos lifecycle (`CR-AOS`)](component-decomposition-and-interface-register.md#cr-aos) | AosCore/AosCloud integration | Provisioning and retirement contracts, authoritative desired/reported actual and Unit Set state, recorded OEM-authorized approvals, FOTA/SOTA execution, targeting, native cross-lifecycle dependency admission, log transport and AosCore quota enforcement/monitoring qualification |
| [Brake Health Cloud (`CR-BRAKE-CLOUD`)](component-decomposition-and-interface-register.md#cr-brake-cloud) | Function Team 1 | v1 window reconstruction, v2/v3 derived-message ingestion, idempotency, exact-Unit retention and Function Dashboard; Query/SSE/admin scope uses an injected exact current Test/Production Unit context sourced from the provisioning journal, with live wiring deferred and no invented Cloud state; event VDP provenance remains nullable/pending until exact assessment correlation; the proposed data packet excludes synchronization-complete, source-generation/run binding and Test/Production comparative-success claims pending D4-024 |
| [Tire Health Cloud (`CR-TIRE-CLOUD`)](component-decomposition-and-interface-register.md#cr-tire-cloud) | Function Team 2 | One prepared v1.0 candidate catalogue, protected delegated publication, Tire result ingestion/idempotency/retention, separated Function Dashboard views and isolated Mac-local ARM64 hosting without OEM lifecycle authority |
| [Demo orchestration (`CR-DEMO`)](component-decomposition-and-interface-register.md#cr-demo) | `aosedge-sdv-demo` | Overlay lifecycle, Unit and Unit Set binding, stateless release workflow facilitation, per-operation resource-scoped conflict/recovery coordination, evidence-backed final-approval presentation, owner/role-visible Software Delivery Dashboard, bounded Tire load orchestration, ordered retirement, next-run provisioning and factory-digest verification |
| [Cross-cutting concerns (`CR-CROSS`)](component-decomposition-and-interface-register.md#cr-cross) | Security and operational concerns across owners | Native Aos identity/permission lifecycle, KUKSA authorization compatibility, redaction, chronology, targeted vehicle external-connectivity continuity and AosCore-enforced service-tenant isolation; the helper is separate from `CR-VDP` |
| [End-to-end acceptance (`CR-E2E`)](component-decomposition-and-interface-register.md#cr-e2e) | Cross-repository qualification | Stage acceptance, failure/offline/recovery, service-tenant isolation and traceability evidence |

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

## Acceptance Record and Delta for Version 2.0

Version 2.0 preserves all accepted manufacturing, lifecycle, functional,
observability, offline, resource and retirement obligations from Version 1.0.
It retires `SYS-SEC-005` and `SYS-SEC-006`, introduces `SYS-SEC-008` for the
separately packaged current-release Service authorization helper and scopes
`SYS-SEC-001` to distinguish IAM-derived SOTA authority from the explicitly
trusted OEM VDP integration. Provider-side connectivity is no longer an open
dynamic-credential requirement, and VDP no longer issues Service JWTs.
The complete C3 cascade was accepted on 2026-08-26.

The 2026-08-28 native-IAM transport correction refines `SYS-SEC-008` without
changing its authority or topology: the released `GetPermissions` interface is
called only through fixed TLS loopback `127.0.0.1:8090`; no KAC TCP listener,
DNS, caller-selected endpoint, external IP or vehicle-external dependency is
introduced.

The 2026-08-25 Level-B revalidation adds `SYS-REL-012` inside the accepted
component and authority boundaries. It replaces the local demo-wide mutation
lock assumption with bounded per-operation recovery and exact resource-scoped
conflicts while preserving run-exclusive provisioning, source handover and R0.

## Acceptance Record for Version 1.0

Version 1.0 adds [`SYS-OBS-007`](#sys-obs-007) for the accepted targeted loss
of Production Unit external vehicle connectivity. It preserves HLA 1.4 and
all component, interface and lifecycle authorities. One stateful control
interrupts Unit-to-AosCloud and installed service-to-functional-backend paths
together while presenter-to-AosCloud and simulated in-vehicle paths remain
available. `GAP-AF-25` and `CR-CROSS` own shared proof; Aos lifecycle owns
authoritative Unit disconnect/reconnect state, and Function Team products own
bounded backend synchronization. It also adds [`SYS-RES-001`](#sys-res-001)
for the `AF-TIRE-RES` proof: AosCore caps the actual Tire service at its
approved CPU quota while Brake and the shared platform remain functional.
`GAP-AF-26` allocates the exact runtime mapping, monitoring evidence, safe load
trigger and tolerance design without adding a project resource manager.

## Acceptance Record for Version 0.9

Version 0.9 retires the accepted low-rate `SYS-BHS-001` report concept while
preserving its anchor. `SYS-BHS-005` defines the bounded v1 braking-event
window and `SYS-BHS-006` defines the v2 derived Cloud data product;
`SYS-BHS-002` is clarified as a synthetic deterministic edge assessment and
`SYS-BHS-004` covers offline continuity for both window chunks and derived
messages. No HLA boundary, lifecycle owner or QM-authority decision changes.

The same requirement set was revalidated on 2026-08-19 against Demo Scenario
1.8 and Architecture Flows 1.7. The Platform Releases catalogue and delegated
protected publication refine the already allocated immutable-candidate,
team-owned-release and Cloud-authoritative-dashboard obligations; they add no
new system requirement or lifecycle authority.

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
