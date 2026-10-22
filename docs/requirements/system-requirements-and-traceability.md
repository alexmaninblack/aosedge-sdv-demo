<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# System Requirements and Traceability 2.4

- Status: Accepted
- Version: 2.4
- Updated: 2026-10-22
- Prepared: 2026-08-22
- Accepted: 2026-09-27
- Owner: System Architecture
- Architecture input: [High-Level Architecture 1.8](../architecture/high-level-architecture.md)
- Scenario input: [Staged Post-SOP Brake and Tire Health Demo Scenarios 2.3](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Demo Scenario Architecture Flows 2.4](../architecture/demo-scenario-architecture-flows.md)
- Accepted architecture decisions: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0011](../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md),
  [ADR 0013](../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md),
  [ADR 0014](../architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Document approval alone authorizes no implementation, publication or live mutation.

## Installed workstation obligations

| ID | Requirement | Statement | Verification | Basis |
| --- | --- | --- | --- | --- |
| <a id="sys-dist-001"></a>`SYS-DIST-001` | Separate installed data authority | Installed Demo Control shall read code/contracts/locked inputs from the selected immutable version and keep journal, release counters, credentials, generated artifacts and working data in an explicit private instance. Missing inputs/access, unsafe or unknown instance state, and conflicting paths shall block without developer fallback or adoption of another setup. Repeat installation/version selection shall not reset durable data or change Cloud. | Unit, Contract, isolated installed-package integration; live activation separately gated | ADR 0018 |

This obligation refines [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md)
and the [distribution entry flow](../architecture/demo-scenario-architecture-flows.md#af-dist-entry).
The accepted first-use scope is one OEM and one associated SP for two separate
services, not cross-provider qualification.

The [version-selection/recovery contract](../../contracts/distribution-installation/version-selection.md)
is an implementation refinement of this same data-preservation obligation:
explicit compatibility, leased runtime use, atomic version selection and
program-only recovery. Its explicit stopped-Test upgrade preserves the existing
run under exact-owner and compatibility proofs; it does not authorize general
state migration, data removal, retained-Production updates or runtime activation.

For that first-install scope, the logical OEM/Brake/Tire publication roles in
[role-bound publication](#sys-rel-011) remain distinct, but the two service
roles may use the same authorized SP identity. The earlier two-provider count
is an expanded scenario, not a requirement for a second account/certificate.
Setup implements the selected-domain OEM/SP connection, certificate enrollment
and bounded recovery through the existing Cloud owner. These capabilities do
not grant publication authority merely because local paths are separated.
New-account registration and remaining native recovery acceptance are tracked
by the current baseline.

<a id="current-implementation-view--24-september-2026"></a>
## Current implementation view

Current package selection and qualification are owned by the launcher catalog and
[current baseline](../qualification/current-baseline.md).
[Implemented architecture and traceability](../architecture/current-implementation.md) maps
the effective requirements, protocols, component owners and proof.
Full acceptance still requires the explicitly outstanding tests; this view
does not change stable IDs or grant deployment authority.

<a id="native-service-inputs-amendment--2026-09-11"></a>
## Service provenance and credential requirements

The accepted [ADR 0015](../architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
and [runtime-input contract](../architecture/demo-control-service-inputs.md)
define package-release/native-instance provenance and private volatile token
sessions for current products. Legacy records retain their original decoder. Allocation remains Brake/Tire services, their backends,
Demo Control and OEM named-resource configuration; no SM API extension is added.

Current product schemas must not require serviceArtifactSha256 or its
modelArtifactSha256 alias. Retain real model-configuration and VDP-contract
digests, native identity, queued legacy data and persistent producer epochs.
Package/publication versions must agree; provenance is application-reported,
not an authorization or attestation claim. Credentials use private volatile
sessions with unchanged KAC authority and lifetime. Cold-start readiness
requires input restoration before automatic service launch. These rules do
not mark implementation, functional analytics or live qualification done.

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

1. High-Level Architecture 1.8 owns boundaries, authority and invariants.
2. Demo Scenario 2.3 owns the audience-visible stage progression.
3. Architecture Flows 2.4 owns detailed lifecycle, runtime, observability and
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

The two functional teams require independent source, service and SOTA
lifecycles. Installed use shares one associated SP; expanded use additionally
separates the SP organizations. Account count does not merge product ownership.

Each Function Team owns the engineering release decision for its service. It
uses its Service Provider identity to publish and technically verify artifacts,
then records acceptance of the exact Validation Unit result. The Platform Team
owns the corresponding FOTA validation and acceptance decision. OEM Release
Authority is an independent governance role outside those producer teams and
owns exact targeting and assignment through the authorized OEM delivery
context. Expanded governance additionally requires separate exact-release
Test authorization and Production rollout decisions. Installed verification
recipients use native delivery, not a fictional extra approval stage. AosCloud remains the lifecycle system of
record and execution control plane.

| Repository | Ownership boundary | Lifecycle | State |
| --- | --- | --- | --- |
| `CarlaSim` | Virtual physical vehicle and upstream simulator behavior | Simulator source | Existing |
| `carla-ego-runtime` | Vehicle Gateway, control, VSS projection, VISS and Engineering Telematics Dashboard | Gateway tooling | Existing |
| `aos-vehicle-platform` | Shared Vehicle Data Platform Component, factory-installed KUKSA integration, provider runtime, separately packaged current-release Service-authorization helper and trusted Provider-side connection configuration | Platform FOTA plus separately governed factory/system integration | Implemented within the retained controller image; formal acceptance remains separately scoped |
| `brake-health-service` | Function Team 1 on-board Brake Health application and local inference | Service Provider 1 / SOTA 1 | Existing |
| `tire-health-service` | Function Team 2 on-board tire-condition estimation, bounded reporting and inspection advisory | Service Provider 2 / SOTA 2 | Existing; independent in-vehicle product |
| `brake-health-cloud` | Function Team 1 backend and Function Dashboard | Function Team 1 Cloud product | Existing; durable product ingestion, queries, reset and cleanup implemented; proof is separately scoped |
| `tire-health-cloud` | Function Team 2 backend and Function Dashboard | Function Team 2 Cloud product | Existing; separate functional backend |
| `aosedge-sdv-demo` | Cross-repository orchestration, dashboards, system requirements and end-to-end qualification | Demo solution | Existing |

The Function Team 2 service repository shall not own CARLA integration,
VISS transport, platform signal publication, KUKSA authorization, VM
provisioning, or AosCloud desired state. It consumes only an accepted,
versioned KUKSA contract.

The Function Team 1 and Function Team 2 backends and dashboards are distinct
functional products. Each backend and its dashboard share one Cloud-product
repository, `brake-health-cloud` or `tire-health-cloud`, and must not be placed
inside either in-vehicle service repository.

Current repository existence is not acceptance of every allocated requirement.
Use the [repository map](../../workspace/repository-map.json) for current source
ownership and the immutable source locks for a selected build. The installed
one-associated-SP Test profile does not merge the two products; two-SP/dual-role
deployment and approval obligations below apply to the expanded profile defined
by HLA and UI-STUDIO-026, not to every installed Test action.

## System Requirements

### Manufacturing and identity

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-mfg-001"></a>`SYS-MFG-001` | Reproducible factory image | The Platform Team shall produce a reproducible, immutable and digest-addressed OEM Demo Factory Image from an identified AosEdge release and accepted integration inputs. | `I,T` | `GAP-AF-01` |
| <a id="sys-mfg-002"></a>`SYS-MFG-002` | Clean SOP substrate | The factory image shall contain AosCore, KUKSA, security/update support, one stock Aos IAM configuration with `enablePermissionsHandler: true` independent of provisioning state, the dedicated non-secret `kuksa-jwt` certificate-module/PKCS#11 and verifier-preparation wiring, and the provider-specific empty-slot runtime, but no pre-populated service permission or `AOS_SECRET`, provider payload, functional service, Cloud registration, Cloud credential, signing key, shared static verifier or reusable per-vehicle secret. | `I,T` | `GAP-AF-01`, `GAP-AF-15` |
| <a id="sys-mfg-003"></a>`SYS-MFG-003` | Unique fresh overlays | Every fresh copy-on-write overlay created from the factory image shall generate distinguishable local identity material before provisioning and shall never share provisioned identity material. Installed use creates one Test; expanded use additionally proves an independent Production overlay. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-001"></a>`SYS-ID-001` | One identity per overlay | The provisioning flow shall create exactly one unique Unit and Main Node identity for each fresh overlay and bind the selected Test role for one run; expanded use additionally binds a separate Production role. | `T,I` | `GAP-AF-02` |
| <a id="sys-id-002"></a>`SYS-ID-002` | Reconcile partial provisioning | A timeout or partial provisioning result shall enter reconciliation and shall not be blindly retried or treated as a clean unprovisioned overlay. | `T,A` | `GAP-AF-03` |
| <a id="sys-id-003"></a>`SYS-ID-003` | Prove current Unit state | Before any update, the system shall prove the current Unit ID, Node ID, role, Unit Set membership, online state and current software graph of the selected Test; expanded promotion additionally proves its independent Production target. | `T,I` | `GAP-AF-03`, `GAP-AF-06` |
| <a id="sys-id-004"></a>`SYS-ID-004` | Qualify identity retirement | Retirement qualification shall prove offline-only deprovisioning, authoritative post-`204` reconciliation, old-certificate reconnect rejection, scoped Unit Set removal, Unit deletion, Unit-owned Node disappearance without inventing a Node-delete API, audit retention and recoverable partial-failure behavior. | `T,A` | `GAP-AF-03` |

### Vehicle source and release lifecycle

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-src-001"></a>`SYS-SRC-001` | Exact source-to-Unit binding | Each qualification or demonstration observation shall identify the exact live CARLA/VISS source, target Unit and frame range. Installed use shall bind the exact Test exclusively; expanded use shall additionally prove Validation attach/run/detach, canonical reset/new generation and exclusive Production binding. Telemetry-trace replay is a deferred future option and is not part of the current profile. | `T,I,D` | `GAP-AF-04` |
| <a id="sys-src-002"></a>`SYS-SRC-002` | Honest single-source presentation | The demo shall not imply that two simulated vehicles were running simultaneously when one CARLA/Gateway source was reused sequentially. | `I,D` | `GAP-AF-04` |
| <a id="sys-src-003"></a>`SYS-SRC-003` | Versioned vehicle hardware profile | The selected virtual vehicle shall have one digest-addressed Vehicle Hardware Capability Manifest that identifies the CARLA revision and ego blueprint and classifies every installed signal, sensor and actuator with its type, unit, frame, cadence or command range, availability semantics and provenance; a capability that CARLA can theoretically create but that is not installed in the selected profile shall be declared `NOT_INSTALLED` rather than implied to exist. | `T,I` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-src-004"></a>`SYS-SRC-004` | Complete Simulator–Gateway accounting | Across the selected hardware profile, the Simulator and Gateway shall account for every declared capability without silent loss: installed state shall be delivered or explicitly unavailable/unsupported; actuator commands shall be accepted or rejected with bounded status and the actually applied control state shall be observable; simulator ground truth and qualification-only oracle state shall remain outside the production vehicle-data interface. | `T,I,A` | Accepted HLA and native-CARLA-inventory baseline correction |
| <a id="sys-rel-001"></a>`SYS-REL-001` | Immutable release candidates | Every FOTA and SOTA candidate shall bind verified functional inputs, its allocated package version, prepared SHA-256 and canonical metadata identity before signing. Installed Prepare may assemble release-specific metadata/package from reviewed prebuilt inputs without compilation, source edits or arbitrary content changes. Expanded frozen-catalogue use shall prepare candidates before presentation and pin their approved IDs through the Demo Release Set; it shall not regenerate content during promotion. Prepared, signed/uploaded and Cloud identities shall remain distinct and traceably linked. | `T,I` | `GAP-AF-05`, `GAP-AF-07`, `GAP-AF-20` |
| <a id="sys-rel-002"></a>`SYS-REL-002` | Current effective-target validation | Immediately before approval, the delivery workflow shall enumerate every Unit in the applicable Fleet/OEM visibility scope, derive effective targets from their current pending-batch state, compare the resulting exact Unit-ID set with the intended Unit Set and block stale, missing, unexpected or unprovable targets. | `T,I` | `GAP-AF-06` |
| <a id="sys-rel-003"></a>`SYS-REL-003` | Service capability compatibility | Each SOTA artifact shall carry its versioned VDP compatibility requirement. Services shall fail closed on missing/invalid authorized local inputs or advisory capability, independently of Cloud. Presenter shall join native Cloud inventory with verified artifact/profile evidence for the installed-version verdict; missing local data alone shall not prove incompatibility. Valid returning inputs shall permit same-instance recovery. | `T,I` | `GAP-AF-20` |
| <a id="sys-rel-004"></a>`SYS-REL-004` | Validate once, then apply by update-state policy | For expanded Production promotion, a candidate shall be installed, qualified and explicitly accepted by its owning team on the Validation Unit before the identical accepted bytes and digest are promoted to the Production Unit. The Production Unit shall be an authorized rollout and live-operation target, not a second product-validation lane; post-rollout actual-state/readiness checks confirm delivery health only. In both profiles, Vehicle Data Platform Component FOTA shall be delivered through AosCloud/AosCore but applied only after the factory-installed OEM Component Runtime proves the accepted Safe Stop policy from Gateway samples fresh at acquisition, a consecutive stability history that is not current-state authority, and a latest complete sample revalidated immediately before every destructive step; the UI shall present, but not duplicate, that in-vehicle gate and shall not claim that AosCloud evaluates physical motion. The accepted Brake/Tire QM Service SOTA may be applied while the vehicle moves, subject to all other release gates. | `T,I,D` | `GAP-AF-06`, `GAP-AF-20` |
| <a id="sys-rel-005"></a>`SYS-REL-005` | Dependent-first recovery | Recovery shall stop/remove the dependent SOTA service before changing a platform capability on which it depends, preserve unaffected service/platform lifecycles and then revalidate/reassign the dependent service. FOTA may use `RevertUpdate` only before `ApplyUpdate`; after Apply it shall use a new signed forward-repair version. SOTA removal is supported, while exact selection of a previous Service Version remains unqualified and shall not be claimed. | `T,A` | `GAP-AF-05`, `GAP-AF-20` |
| <a id="sys-rel-006"></a>`SYS-REL-006` | Native Cloud Service-to-VDP rejection | AosCloud shall natively reject a SOTA request whose declared FOTA Vehicle Data Platform Component range is not satisfied on the intended Unit before changing Subject-service desired state, creating a validation batch or campaign, or transferring update content to the Unit, and shall return an authoritative machine-readable reason. Existing component-to-component and service-to-layer dependency mechanisms remain supported platform capabilities and are outside this deferred cross-lifecycle requirement. | `T,I,D` | `GAP-AF-20` |
| <a id="sys-rel-007"></a>`SYS-REL-007` | Team-owned release decisions | The Platform Team shall own every Vehicle Data Platform Component release decision, Function Team 1 shall own every Brake Health release decision, and Function Team 2 shall own every Tire Health release decision; passing evidence or a dashboard action shall not silently substitute for explicit owner acceptance. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-rel-008"></a>`SYS-REL-008` | Separate producer acceptance and OEM deployment authorization | A Function Team shall use its Service Provider identity to publish and technically verify its service artifact. The owning Platform, Brake or Tire team shall explicitly accept the exact Validation Unit result. OEM Release Authority, as an independent governance role outside those producer teams, shall authorize exact targeting/assignment through the OEM delivery context; expanded governance shall additionally record the independent per-release Test and Production decisions. AosCloud shall record the owner acceptance, Release Authority decision, artifact version/object identity, target and transition; the demo shall bind those records to the exact retained publication digest chain and shall not claim a Cloud-side SOTA content digest where the released API exposes none. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-rel-009"></a>`SYS-REL-009` | Dependent-release milestone gate | Every VDP FOTA and dependent Service SOTA shall retain its own owner acceptance, OEM authorization, Cloud lifecycle object and result. A dependent Service shall not be promoted to a target until the required VDP is actually ready there. G3/G4 shall be derived capability milestones only, complete after both releases and their live behavior are proven, with no combined Cloud object, atomic group approval or cross-team rollback. | `T,I,D` | `GAP-AF-17`, `GAP-AF-20` |
| <a id="sys-rel-010"></a>`SYS-REL-010` | Evidence-backed OEM Release Authority decision | When the expanded profile exposes Test deployment or Production authorization, the workflow shall present and bind the exact artifact and service-metadata digests, requested permissions, effective target, required evidence with freshness/status, applicable owning-team acceptance and active OEM Release Authority context. Any missing, stale, failed or mismatched prerequisite shall block the action; passing evidence shall never auto-authorize; the explicit Release Authority decision shall be recorded in AosCloud and followed by an authoritative state re-read. | `T,I,A,D` | `GAP-AF-06`, `GAP-AF-17` |
| <a id="sys-rel-011"></a>`SYS-REL-011` | Role-bound protected publication | Exactly three non-interchangeable current-demo publication profiles shall bind Platform OEM to VDP Component FOTA, the Brake SP context to Brake Health SOTA and the Tire SP context to Tire Health SOTA. Installed use shall require one OEM credential and one associated-SP credential; both service profiles may reference the same SP file without duplication. Expanded cross-provider use requires independent SP domains. One session-scoped non-root native helper may implement all profiles, but each dashboard surface shall be pre-bound to one profile and shall not select a credential path, profile, arbitrary candidate path or Cloud URL. The installed `aos-signer` 2.0.1 compatibility path shall bind each profile to a local mode-`0600`, Git-excluded passwordless PKCS#12 for both signing and mTLS upload; no dashboard, container, VM image or artifact may receive it. Only an independent AosCloud re-read may establish `PUBLISHED`; an ambiguous result shall be reconciled as `UNCERTAIN` without blind retry, and technical publication shall never perform OEM deployment approval. | `T,I,A,D` | `GAP-AF-17` |
| <a id="sys-rel-012"></a>`SYS-REL-012` | Independent resource-scoped release operations | Installed protected mutations shall serialize under the existing writer while read-only observations remain independent. Expanded disjoint-resource concurrency shall be coordinated per exact candidate/operation and resource-conflict key set without inventing independent authority or an automatic mutation queue. Active or unresolved operations on disjoint candidate/digest/profile, Cloud-object, Batch/Campaign, Unit and Unit-Set keys may proceed independently; only overlapping keys shall block. Provisioning, identity retirement, exclusive live-source handover/reset and R0 freeze/cleanup shall remain run-exclusive. Restart shall reconcile every non-terminal operation from fresh authoritative state without blind retry, while read-only views remain available. Local helper capacity shall affect only the requested operation and shall neither be presented as an AosCloud restriction nor automatically queue or trigger another team's action. | `T,I,A,D` | `GAP-AF-17` |

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

The requirements below define exclusive vehicle control, continuous handover
and deterministic mode/context transitions. The
[drive-mode flow](../architecture/demo-scenario-architecture-flows.md#af-x-drive)
owns their sequence. They preserve the existing vehicle-control authority,
architectural boundary and data direction; they add no demonstration stage.

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
| <a id="sys-bhs-002"></a>`SYS-BHS-002` | Deterministic v2 edge assessment | Service v2 shall use the immutable digest-bound `brake-condition-demo-v1` model and disclosed `DEMO_PRECONDITIONED` profile on the exact twelve-path VDP v2 subset. One adapter conversion supplies fixed-point speed, acceleration, brake, steering and wheel values; the core shall apply the accepted ACTIVE-only five-feature arithmetic to the full retained episode, maintain bounded crash-safe exactly-once synthetic state and produce deterministic `BrakeHealthAssessment` results plus events only on real band changes. The accepted local invalid-input outcome and derived-pair overflow shall not fabricate a healthy result/message. The 5000-load and seven/eight-second values are demo qualification only, not runtime/production filters or KPIs. | `T,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-006"></a>`SYS-BHS-006` | Derived v2 Cloud data product | Normal Service v2 operation shall send only bounded, versioned and idempotent `BrakeHealthAssessment` and band-change `BrakeHealthEvent` messages to the functional backend rather than Service v1 high-detail telemetry windows. Assessment plus optional event is admitted atomically; overflow advances deterministic local state once but publishes neither and cannot later fabricate a message. Source-window, local-assessment, event-effective and backend times remain distinct, and the dashboard shall make the processing/traffic change visible without production-latency claims. | `T,I,A,D` | `GAP-AF-08`, `GAP-AF-09` |
| <a id="sys-bhs-003"></a>`SYS-BHS-003` | Allowlisted v3 advisory | Service v3 shall request only the accepted Brake Health advisory target and shall not gain arbitrary display-text or vehicle-motion authority. | `T,I` | `GAP-AF-10`, `GAP-AF-15` |
| <a id="sys-bhs-004"></a>`SYS-BHS-004` | Offline local continuity | Brake Health local assessment and advisory shall continue without Cloud connectivity; in-progress/completed v1 windows and v2/v3 derived functional messages shall use bounded retention, retry and idempotent synchronization with original sample/event times. | `T,A,D` | `GAP-AF-11` |

D4-016.1/.2/.3/.4/.5 and D4-017 Cloud transport/store/cleanup are accepted
design contracts in the [contract index](../../contracts/README.md), with
implemented paths and scoped evidence in the current baseline. D4-003 calibration remains an
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
D4-020 defines their design-reviewed physical Mac/QEMU hosting and route:
two independent Linux/arm64 backend containers and host Presenter/Demo Control,
CARLA and native Driving Control, not a third dashboard container.
The first demo uses lightweight isolated local functional-backend transport
without per-Unit backend credentials; `system_uid` is correlation-only and
production backend authentication remains independently Function Team-owned
and out of scope. Signed updates, OEM authorization and in-vehicle
Aos IAM/KUKSA/Gateway security remain unchanged. Accepted numeric/model design
does not close calibration or resource qualification. Expanded two-VM routing,
helper isolation and LAN negatives require their own live proof before full
implementation acceptance; scoped installed passes do not supply that proof.

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

Retired IDs remain resolvable for traceability; the table below supplies their
effective replacements. Native IAM remains authoritative, translation belongs
to separately packaged `CMP-KAC`, and the trusted OEM Provider is outside
dynamic Service-credential authorization. Superseded broker proposals are not
alternative current requirements.

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
| <a id="sys-sec-004"></a>`SYS-SEC-004` | Per-Unit KUKSA signer and verifier | Successful provisioning shall establish one unique non-exported RSA signing key per Unit lifecycle through the dedicated Aos certificate-module/PKCS#11 integration, then atomically install only its public verifier before the current-release helper and Factory-owned KUKSA start. KUKSA shall enforce `RS256` signature, fixed audience `kuksa.val`, expiry and path permissions; its pinned implementation shall not be credited with enforcing `iss`. Service JWT lifetime shall be 300 seconds with renewal at 180 seconds through a fresh IAM lookup and mandatory KUKSA reconnect/subscription recreation; permission removal shall prevent renewal, Validation and Production fingerprints shall differ, and cross-Unit tokens shall fail. No signing key or shared static verifier shall be baked into the Factory Image or an FOTA/SOTA artifact; first-demo rotation occurs only through fresh provisioning, and R0 destroys the key with the retired VM overlay. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-sec-007"></a>`SYS-SEC-007` | QM service and Gateway containment | Brake Health and Tire Health shall remain QM-domain maintenance/inspection applications with no allocated safety goal, direct driver-HMI claim, vehicle-motion authority or safety-critical actuator access. The VDP shall validate outbound advisories as defense in depth, and the Vehicle Gateway shall be the final authoritative boundary for the QM-origin channel: it shall accept only Platform-owned typed non-safety advisories, validate target/type/range/freshness/rate/correlation, report factual status, and reject arbitrary VSS writes and every throttle, brake, steer, gear, motion or safety-critical operation. | `T,I,A,D` | `GAP-AF-10`, `GAP-AF-15`, `GAP-AF-22` |
| <a id="sys-sec-008"></a>`SYS-SEC-008` | Current-release KUKSA Service authorization compatibility | A separately packaged platform helper outside VDP and both SOTA payloads shall accept only an active Service instance's native `AOS_SECRET` plus one fixed KUKSA resource identifier, call Aos IAM `GetPermissions` through fixed TLS loopback `127.0.0.1:8090` with Aos CA trust and expected server name `main` and no DNS, caller-selected endpoint, external IP or KAC TCP listener, map only exact `r` paths to KUKSA `read` and exact `rw` paths to KUKSA `actuate`, and reject `w`, wildcards, partial trimming and all Service `provide/create` authority. It shall deliver a 300-second JWT only to that Service's private volatile location, renew at 180 seconds through a fresh IAM lookup, and require reconnect/subscription recreation with the replacement. Each provisioned Unit shall own one non-exportable `kuksa-jwt` RSA key; a protected sign/verify preparation gate shall atomically publish only the volatile public verifier, and KUKSA plus the helper shall fail closed unless KUKSA starts with that exact verifier. Authorization readiness shall require one NTP synchronization and 10 stable seconds per boot; epoch claims shall use UTC while scheduling uses boottime. The temporary helper shall compare elapsed wall/boottime immediately before every issue or renewal and reject a deviation greater than five seconds as `TIME_UNTRUSTED`, but shall add no anchor, continuous monitor, KUKSA lifecycle controller or instant revocation; an already issued JWT may remain usable only until signed expiry. Normal later external-connectivity loss shall not revoke trust or disable the inside-Unit IAM loopback. Recovery requires synchronized time plus a new stable window, while cold offline boot remains authorization `NOT_READY` without blocking unrelated AosCore. Frames, permission/path/JWT size, concurrency, backlog, rate, timeout, retry and process resources shall follow the closed D4-027.8 envelope and emit only fixed redacted diagnostics. The caller shall not select paths, operations, subject, audience, TTL, claims or signing input. Invalid, inactive, stale, broadened, malformed, cross-instance/Unit or unsupported authority, unavailable IAM/helper, or failed signer/verifier/time preparation shall issue no new JWT. The Service shall connect directly to KUKSA after preparation. Reboot shall recreate the verifier and reconstruct authority from active platform state; stop, removal or unregistration shall prevent renewal and remove private credential state. VU and PU trust shall remain distinct, and R0 overlay disposal shall retire the Unit key. No parallel Service identity/policy database, file-key fallback or instant-revocation claim is permitted. The future released native AosCore contract shall be requalified for trustworthy time, bounded credential invalidation and recovery before this helper is removed. | `T,I,A` | `GAP-AF-15` |
| <a id="sys-obs-001"></a>`SYS-OBS-001` | Authoritative demo surfaces | Every audience claim shall identify its authoritative surface: CARLA for physical stimulus, Engineering Telematics Dashboard for Gateway state, AosCloud for software lifecycle and native log requests/results, OEM Software Delivery Dashboard for role-scoped system/VDP log presentation, and each functional dashboard for its own backend data plus its own Service-owned service-instance/crash-log presentation. | `I,D` | `GAP-AF-17` |
| <a id="sys-obs-002"></a>`SYS-OBS-002` | Cloud-authoritative delivery dashboard | The Software Delivery Dashboard shall read and re-read authoritative AosCloud lifecycle plus Cloud-retained OEM-scoped Unit system/VDP log request/result/file state, display the business decision owner and active Cloud role, require explicit confirmation before an OEM-authorized mutation or system-log request, and shall not maintain an independent desired-state database, second log archive or automatic approval policy. Service-instance and crash-log requests belong to the matching Brake or Tire Function Dashboard under a separately allowlisted SP operational context; they shall not create an omni-credential in the Software Delivery Dashboard. Presenter Mac/Native Helper connectivity to AosCloud is a demo precondition rather than an automotive offline claim: its loss blocks administrative actions with an infrastructure error and is never displayed as Unit offline behavior. | `T,I` | `GAP-AF-06`, `GAP-AF-16`, `GAP-AF-17` |
| <a id="sys-obs-003"></a>`SYS-OBS-003` | Operational log controls | Native system logs shall use the role-scoped `/api/v11/unit-logs/` list/create/read/download/delete family through `oem-delivery`; Brake and Tire service-instance/crash logs shall use the corresponding `/api/v11/service-logs/` family through separate SP1/SP2 operational contexts. Before those logs are presented as demo evidence, the solution shall qualify exact Unit/Node identifiers, timestamps, effective permissions and ownership filtering, create-response cardinality, documented Cloud states, file/archive bounds, explicit deletion effect and online/offline/reconnect behavior. Emitters and dashboards shall enforce structured allowlisted redaction, temporary downloads shall be bounded and removed, and no second archive shall be created. Because current API v11 exposes no retention policy, the demo shall state `Retention policy not exposed by current API`; it shall not claim a fixed or indefinite duration or present retrieval duration as a vehicle KPI. | `T,I,A` | `GAP-AF-16` |
| <a id="sys-obs-004"></a>`SYS-OBS-004` | Per-run correlation | Before provisioning, a demo run shall be correlated by start time and local overlay roles; after provisioning it shall be correlated by the exact Test identity and bounded time window; expanded use additionally binds its independent Production identity. | `T,I` | `GAP-AF-19` |
| <a id="sys-obs-005"></a>`SYS-OBS-005` | Truthful control-transition evidence | The Gateway engineering projection and Engineering Telematics Dashboard shall expose the current drive mode, world context, scenario state/result, generation and reset/discontinuity state as simulator-derived facts so that reset teleportation is never interpreted as physical vehicle motion. Controller-derived facts shall join physical state only on exact CARLA frame ID and simulation time; an absent or rejected controller record shall omit the entire control/reset group for that frame rather than reuse prior state. Presenter operation progress shall remain separate from vehicle telemetry. | `T,I,D` | `GAP-AF-24` |
| <a id="sys-obs-006"></a>`SYS-OBS-006` | Visible approval decision basis | The Software Delivery Dashboard shall distinguish validation evidence, owning-team acceptance and the final OEM authorization; show the exact candidate, requested permissions, target, evidence status and active role before confirmation; explain blocked prerequisites; and shall not claim that its button, passing tests or locally retained data constitute the approval, authoritative lifecycle state, proof that software is safe, or functional-safety certification. | `T,I,D` | `GAP-AF-17` |
| <a id="sys-obs-007"></a>`SYS-OBS-007` | Targeted vehicle external-connectivity continuity | One stateful demo control shall atomically remove or restore the currently selected Validation or Production Unit's external vehicle connectivity; installed `G4/X-OFFLINE` uses Test, while expanded use separately proves the Production target. In the disconnected state, both selected-Unit-to-AosCloud and installed service-to-functional-backend paths shall be blocked, while the other running VM, presenter-to-AosCloud and simulated in-vehicle CARLA/Gateway/VISS/KUKSA paths remain available. The dashboard shall continue to read AosCloud, show authoritative Unit offline/online state and unavailable lifecycle/log actions; reachable Function Dashboards shall show delayed/offline rather than current vehicle results. Local inference and advisory shall continue. On reconnect, the same selected Unit shall return online without reprovisioning, reinstalling or restarting, and bounded functional messages shall synchronize idempotently with original event time separate from receipt/synchronization time. Separate per-channel fault switches shall not be exposed. | `T,I,D` | `GAP-AF-25` |
| <a id="sys-res-001"></a>`SYS-RES-001` | AosCore-enforced service-tenant isolation | Accepted service metadata shall carry independently approved Brake and Tire service quotas, and AosCore/Service Manager shall be the sole in-vehicle enforcement and monitoring authority. The first demo shall run one prepared bounded CPU-load profile inside the actual Tire Health service cgroup until that instance reaches its own quota; AosCore shall cap it and report fresh exact-instance usage/state in DMIPS through AosCloud while Brake Health processes the deterministic CARLA event without restart or degradation and VDP, KUKSA, Gateway and AosCore remain healthy. A quota alert is supplementary. Final technical acceptance shall additionally use separately labelled read-only cgroup cap/throttle evidence bound to the exact Factory Image, AosCore, Service artifact/configuration and Node DMIPS baseline; Service/backend control state is not enforcement proof. Stopping the load shall return Tire to normal without reinstall or restart. No project resource manager shall be introduced. Mac-local functional backends and aggregate quota enforcement across several services owned by one Service Provider are outside this proof. | `T,I,D` | `GAP-AF-26` |
| <a id="sys-tim-002"></a>`SYS-TIM-002` | Separate on-board and Cloud chronology | Brake Health and Tire Health messages shall preserve distinct source-event, local-decision/advisory, Gateway-observation and backend receipt/synchronization timestamps so that Cloud delivery is never presented as part of the on-board decision path. Causality is proven by identifiers, producer epoch/sequence, source generation/frame and states rather than cross-clock comparison. The evidence proves only demo causal linkage and reconnect behavior; production clock synchronization, worst-case latency, real-time, network and safety claims are excluded. | `T,A,D` | D4-024 design reviewed; correlation/local timestamps implemented; complete source/chronology qualification remains required |

### Retirement and next-run reset

| ID | Short name | System requirement | Verification | Gap source |
| --- | --- | --- | --- | --- |
| <a id="sys-ret-001"></a>`SYS-RET-001` | Retire Units and overlays | Installed Finish shall stop owned source/VM/backends, retire only its exact current Test, reconcile Unit/Node/Subject/Set and backend effects, prove absence and empty desired/reported recipients, dispose only owned working files and remove the reconciled journal last. Permanent topology, releases, credentials, Factory and unrelated/Production state shall survive. Ordinary Finish shall not require a deliberate old-credential reconnect. In the expanded Validation/Production profile, R0 shall finish the final authoritative read, place both owned Units offline through a qualified bounded operation, wait for AosCloud `Offline`, invoke OEM offline-only deprovision, reconcile its no-body `204`, prove retired credentials cannot restore either Unit `Online`, stop the VMs, delete exact current-run log requests, remove each role membership by `system_uid`, delete each Unit by Cloud UUID and prove Unit absence, empty role sets and inaccessible Unit-owned Nodes before overlay disposal. Neither profile may invent a standalone Node-delete API or automatically create/provision the next run. | `T,I,A` | `GAP-AF-03`, `GAP-AF-19` |
| <a id="sys-ret-002"></a>`SYS-RET-002` | Clear functional run data | Each functional backend shall expose preview/confirmed permanent deletion only to local Demo Control through its private mode-`0600` Unix admin boundary, using the injected journal-owned current-Unit context. Installed Finish selects exactly `[currentTestUid]`; explicit expanded cleanup may select all sorted current-context UIDs. Test retains the internal `VALIDATION` role. Missing, empty, duplicate, wildcard, foreign, Production-only or other unauthorized partial selectors shall delete nothing. Preview shall bind the exact selector, current canonical RFC-8785/SHA-256 record-set digest/counts and 60-second expiry; invalid, expired, previous-process or stale previews require a fresh preview without deletion. The backend-specific token/error protocol remains D4-017 for Brake and D4-019 for Tire, not a universal HMAC wire. One transaction shall delete all selected functional, reset and observation records, prove zero selected rows and unchanged nonmatching digest across deletion, preserving peers. Uncertain response requires authoritative read-only reconciliation, never blind execution retry. Fresh Unit identities define scope; no `demoRunId`, independent time-window selector or historical run archive is required. Model Reset shall preserve history and is not this cleanup. AosCloud lifecycle/audit history remains AosCloud-owned and retained. | `T,I` | `GAP-AF-19` |
| <a id="sys-ret-003"></a>`SYS-RET-003` | Reset vehicle simulation state | R0 shall safe-stop the ego vehicle, remove only scenario-owned CARLA actors and sensors, restore changed CARLA world and Traffic Manager settings, clear run-local simulation evidence and report incomplete cleanup before the next run. | `T,I` | `GAP-AF-04` |
| <a id="sys-ret-004"></a>`SYS-RET-004` | No rollback or fleet claim | The normal demo reset shall not be presented as a G4-to-G0 OTA rollback or as a production-fleet vehicle deletion policy. | `I,D` | `GAP-AF-03` |
| <a id="sys-ret-005"></a>`SYS-RET-005` | Preserve immutable factory artifact | R0 shall not modify or replace the accepted OEM Demo Factory Image; after provisioned overlays are retired and discarded, the system shall verify and retain the same immutable factory-image digest as the source for the next M0 deployments. | `T,I` | `GAP-AF-01`, `GAP-AF-19` |
| <a id="sys-ret-006"></a>`SYS-RET-006` | Reconcile Unit Sets for the next run | Installed Setup may prepare only the absent model/empty Test verification set through its accepted Cloud owner; reuse requires exact authenticated selection, not title-based adoption. Finish shall preserve permanent topology, reconcile only current-Test membership/recipients and preserve unrelated/Production objects. In the expanded profile, OEM administration shall create and pin once `AosEdge SDV Demo Fleet` and its dedicated Test/Production role sets; Demo Orchestrator shall never create, rename, reconfigure, move or delete those definitions. Expanded R0 shall prove both role memberships empty; the next expanded M1 shall verify pinned UUIDs/titles/validation flags and place fresh distinct Unit/Node identities into the correct disjoint sets. Neither profile shall reuse retired batch, validation, Campaign or target assumptions after membership changes or implicitly create/provision the next run. | `T,I,A` | `GAP-AF-03`, `GAP-AF-06`, `GAP-AF-19` |

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
Retired identifiers resolve through the
[flow retirement map](../architecture/demo-scenario-architecture-flows.md#retired-architecture-flow-gaps).
Coverage is not closure: each active gap remains open until its linked
requirements have accepted evidence.

## Component Requirement Package Allocation

The canonical component IDs, interface IDs, repository candidates and package
boundaries are defined in the
[Component Decomposition and Interface Register 2.3](component-decomposition-and-interface-register.md).
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
| [Tire Health service (`CR-TIRE`)](component-decomposition-and-interface-register.md#cr-tire) | `tire-health-service` | One mature v1.0 candidate on VDP v3: local persistent condition model, bounded summary/event, offline queue, inspection advisory, SOTA 2 metadata and resource limits |
| [Aos lifecycle (`CR-AOS`)](component-decomposition-and-interface-register.md#cr-aos) | AosCore/AosCloud integration | Provisioning and retirement contracts, authoritative desired/reported actual and Unit Set state, recorded OEM-authorized approvals, FOTA/SOTA execution, targeting, native cross-lifecycle dependency admission, log transport and AosCore quota enforcement/monitoring qualification |
| [Brake Health Cloud (`CR-BRAKE-CLOUD`)](component-decomposition-and-interface-register.md#cr-brake-cloud) | Function Team 1 | v1 window reconstruction, v2/v3 derived-message ingestion, idempotency, exact-Unit retention and Function Dashboard; Query/SSE/admin scope uses an injected exact current Test/Production Unit context sourced from the provisioning journal, with installed Test context and no invented Cloud state; event VDP provenance remains nullable/pending until exact assessment correlation; complete source-generation/correlation and expanded Test/Production comparative proof remain separately required by D4-024 |
| [Tire Health Cloud (`CR-TIRE-CLOUD`)](component-decomposition-and-interface-register.md#cr-tire-cloud) | Function Team 2 | One prepared v1.0 candidate catalogue, protected delegated publication, Tire result ingestion/idempotency/retention, separated Function Dashboard views and isolated Mac-local ARM64 hosting without OEM lifecycle authority |
| [Demo orchestration (`CR-DEMO`)](component-decomposition-and-interface-register.md#cr-demo) | `aosedge-sdv-demo` | Overlay lifecycle, Unit and Unit Set binding, stateless release workflow facilitation, per-operation resource-scoped conflict/recovery coordination, evidence-backed final-approval presentation, owner/role-visible Software Delivery Dashboard, bounded Tire load orchestration, ordered retirement, next-run provisioning and factory-digest verification |
| [Cross-cutting concerns (`CR-CROSS`)](component-decomposition-and-interface-register.md#cr-cross) | Security and operational concerns across owners | Native Aos identity/permission lifecycle, KUKSA authorization compatibility, redaction, chronology, targeted vehicle external-connectivity continuity and AosCore-enforced service-tenant isolation; the helper is separate from `CR-VDP` |
| [End-to-end acceptance (`CR-E2E`)](component-decomposition-and-interface-register.md#cr-e2e) | Cross-repository qualification | Stage acceptance, failure/offline/recovery, service-tenant isolation and traceability evidence |

Component requirements shall reference both their parent `SYS-*` requirement
and the relevant `AF-*` flow. Tests shall reference the component requirement,
system requirement and retained evidence identifier.

<a id="proposed-function-team-2-repository-creation-gate"></a>
## Repository ownership

The independent Tire repository exists and is listed in the
[workspace map](../../workspace/repository-map.json). Its current service/data,
licensing, resource, compatibility and verification obligations remain in the
[Tire package](components/tire-health-service.md). New component repositories
follow [contribution and ownership rules](../../CONTRIBUTING.md), not a pending
creation gate for an already implemented component.

<a id="review-provenance"></a>
## Authority and verification

This document owns its current obligations, stable IDs and acceptance criteria.
Use the linked current baseline for exact scoped evidence. Accepted design is
not a claim that the complete implementation or live matrix has passed.
