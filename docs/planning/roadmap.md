<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current Design and Delivery Roadmap

- Status: Working gate map
- Updated: 2026-08-27
- Current accepted architecture: High-Level Architecture 1.5
- Cloud or Unit mutation authorized: no

## Purpose

This roadmap identifies the current design baseline and the order in which the
demonstration may move from architecture into implementation. It replaces the
obsolete R6.1 plan that proposed a separate `vehicle-data-integration`
component, a generic component runtime, and a `G4`-to-`G0` reset on retained
Unit identities.

The current target uses:

- one OEM Factory Baseline Assembly that reproducibly produces the immutable
  OEM Demo Factory Image artifact;
- one provider-specific empty-slot runtime in the OEM Demo Factory Image;
- one independently versioned Vehicle Data Platform Component FOTA family;
- two peer OEM functional services with independent SOTA lifecycles;
- fresh Validation and Production Unit identities per demo run;
- controlled retirement and disposable-overlay replacement for the normal
  next-run reset.

## Completed Engineering Foundations

The following achievements are retained as engineering evidence. They do not
by themselves prove the final manufacturing-to-retirement demonstration:

1. native CARLA and Unreal Engine operation on Apple Silicon;
2. Vehicle Gateway control, VSS normalization, TLS VISS 3.1 read/subscription,
   and the Engineering Telematics Dashboard;
3. deterministic emergency-braking scenario, manual takeover, safe stop and
   actor cleanup;
4. official AArch64 AosVM boot under QEMU/HVF;
5. single-Main-Node provisioning, persistent identity, DNS mobility and
   lifecycle safety tooling;
6. live CARLA/VISS-to-KUKSA provider qualification evidence;
7. provider-specific empty-slot runtime, isolated store and SELinux evidence
   in local rootfs candidate `.11`;
8. immutable local provider `0.2.0` evidence;
9. repository ownership split, workspace contract and post-cleanup acceptance.

Exact retained versions and limitations remain recorded in the
[current accepted engineering baseline](../qualification/current-baseline.md).

## Current Documentation Baseline

The following documents form one ordered design chain:

1. [High-Level Architecture 1.5](../architecture/high-level-architecture.md)
   owns boundaries, authorities and invariants.
2. [Demo Scenario 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md)
   owns the accepted audience-visible stage sequence.
3. [Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
   owns the accepted lifecycle, runtime, observability and failure flows.
4. [System Requirements and Traceability 2.0](../requirements/system-requirements-and-traceability.md)
   owns `SYS-*` obligations and coverage of all twenty-two gaps.
5. [Component Decomposition and Interface Register 2.0](../requirements/component-decomposition-and-interface-register.md)
   owns component/interface IDs and provisional requirement-package
   allocation.

A downstream document may not silently redefine an upstream decision.

## Active Design Gates

### D0 — Component register review — completed 2026-08-18

Component names, responsibilities, current/target state, interfaces, owners,
lifecycles and repository candidates were first accepted in Component
Decomposition and Interface Register 0.2. This includes the Vehicle Gateway and Tire Health
boundaries, one backend-plus-dashboard Cloud repository per Function Team,
stateless Software Delivery Dashboard and Demo Orchestrator boundaries, native
AosEdge logging ownership. The historical ADR 0010 VDP-owned Credential Broker
allocation was subsequently superseded by accepted ADR 0013: removable
`CMP-KAC` is separate factory/system integration, VDP owns no Service JWT
issuance, and native Aos IAM retains SOTA instance identity and permission
ownership.

Exit evidence: Component Decomposition and Interface Register 0.3 closed D0;
the accepted register has since advanced to 0.4 through controlled downstream
refinement.

### D1 — Documentation housekeeping — completed 2026-08-18

Remove superseded active design documents and unreferenced generated files;
retain ADRs, research evidence, qualification records and operations manuals
with clear authority labels. Provide task-oriented entry paths for running
AosVM, reproducing the current demonstration, understanding the system,
modifying components and adding scenarios. Keep the current repeatable
engineering paths visibly separate from the unfinished full staged demo.
Validate indexes, internal links and source precedence.

Exit: the documentation tree presents one current design chain without broken
links or competing active plans.

The completed gate also establishes stable identifier anchors,
human-readable package summaries, direct traceability links, the documented
architecture-change cascade, and the deterministic `docs-check` commit/CI
gate.

### D2 — Baseline acceptance — completed 2026-08-18

HLA 1.4, Scenario 1.5, Architecture Flows 1.4, System Requirements 0.7 and the
Component Register 0.7 form one consistent design baseline. Scenario 1.5 and
Flows 1.4 retain the accepted drive-mode/world-context transition contract;
Requirements and Register 0.7 allocate it to Vehicle Simulation, Vehicle
Gateway and the Engineering Dashboard. HLA 1.4 also preserves the native Aos
IAM credential authority, classifies both services as QM, makes Gateway
containment authoritative and requires evidence-backed final OEM approval.
Deferred platform capabilities and
open qualification or implementation gates remain explicit and are not
presented as current behavior.

HLA 1.5, Scenario 2.0, Architecture Flows 2.0, System Requirements 2.0 and
Component Register 2.0 are the current accepted cascade. They preserve
the accepted topology and replace the former v1 low-rate report narrative with
a bounded pre/active/post `BrakeTelemetryWindow`, make v2 a clearly labelled
synthetic on-board assessment with derived-only normal Cloud reporting, and
retain v3 advisory plus correlated backend facts. They also preserve the
explicit `R0 -> M0 -> M1` Unit Set reconciliation and responsibility split
accepted during `CR-AOS` review. They additionally define one atomic first-
demo vehicle-connectivity fault: Production Unit-to-AosCloud and installed
service-to-functional-backend paths are interrupted together, while presenter-
to-AosCloud and simulated in-vehicle connectivity remain available.

Exit evidence: each baseline document records its accepted status and date,
and the documentation quality gate passes for the complete design chain.

### D3 — Component requirement packages

Create and review packages in this order:

1. [Vehicle simulation (`CR-VEHICLE-SIM`)](../requirements/component-decomposition-and-interface-register.md#cr-vehicle-sim)
   and [Vehicle Gateway (`CR-GATEWAY`)](../requirements/component-decomposition-and-interface-register.md#cr-gateway);
2. [Factory substrate (`CR-FACTORY`)](../requirements/component-decomposition-and-interface-register.md#cr-factory)
   and [Vehicle Data Platform (`CR-VDP`)](../requirements/component-decomposition-and-interface-register.md#cr-vdp);
3. [Aos lifecycle (`CR-AOS`)](../requirements/component-decomposition-and-interface-register.md#cr-aos);
4. [Brake Health service (`CR-BHS`)](../requirements/component-decomposition-and-interface-register.md#cr-bhs)
   and [Brake Health Cloud (`CR-BRAKE-CLOUD`)](../requirements/component-decomposition-and-interface-register.md#cr-brake-cloud);
5. [Tire Health service (`CR-TIRE`)](../requirements/component-decomposition-and-interface-register.md#cr-tire)
   and [Tire Health Cloud (`CR-TIRE-CLOUD`)](../requirements/component-decomposition-and-interface-register.md#cr-tire-cloud);
6. [Demo orchestration (`CR-DEMO`)](../requirements/component-decomposition-and-interface-register.md#cr-demo),
   [cross-cutting concerns (`CR-CROSS`)](../requirements/component-decomposition-and-interface-register.md#cr-cross)
   and [end-to-end acceptance (`CR-E2E`)](../requirements/component-decomposition-and-interface-register.md#cr-e2e).

Groups 1 through 5 established design-reviewed baselines on 2026-08-19;
subsequent security and exact-contract deltas retain their per-package review
state in the component-package index rather than inheriting acceptance. Demo
Orchestration (`CR-DEMO`) is revalidated as 1.1; Cross-Cutting Security and
Operations (`CR-CROSS`) remains a review candidate at 0.4; End-to-End
Acceptance (`CR-E2E`) 0.8 is D3 design-reviewed as of 2026-08-27. Their target,
partial and qualification states remain open. The complete D4-026.1–.20
interaction/qualification design and D4-027.1–.8 compatibility-helper contract
are accepted, but implementation and live qualification are not authorized.

Create every package from the
[component requirement package template](../requirements/components/template.md).
Every component requirement must cite its named parent `SYS-*` requirement,
relevant `AF-*` flow, component and interface definitions, verification levels
and required evidence. Owned executable logic must also define stable `UT-*`
unit-test obligations covering applicable normal, boundary, malformed,
unavailable and recovery behavior. External executables and packages with no
owned executable logic may record a reasoned unit-test exception and allocate
their proof to contract, integration, qualification or end-to-end verification.

Exit: every system obligation is allocated, every interface has an owner on
both sides, every component requirement has complete verification
traceability, and every owned unit of behavior has a unit-test obligation or a
reviewed exception.

### D4 — Interface contracts and acceptance tests

Use the
[D4 Interface and Qualification Decision Register 1.0](../requirements/d4-decision-register.md)
as the single sequencing and decision-control surface. Package-level open
issues remain authoritative owner inputs; repeated questions are resolved once
under a shared stable `D4-*` ID and then cascaded to every consumer.

Freeze the versioned VISS, KUKSA, typed advisory, functional-report/event,
AosCloud, log and dashboard contracts. Define executable cases, fixtures,
suites and evidence locations for normal, unavailable, stale, malformed,
unauthorized, offline, retry, pre-Apply revert, post-Apply forward repair,
SOTA removal and resource-bound behavior. D4 refines
how D3 obligations are proved; it does not silently change component behavior.

Exit: tests can be written without inventing missing architecture decisions.

### D5 — Implementation plan

Build a new implementation plan from the accepted component packages. Reuse
existing qualified code and artifacts only where their exact contracts match
the accepted design. Do not revive the superseded R6.1 two-component plan.

Before any audience-visible interface is implemented or materially changed,
complete an **Audience-Visible UI Mockup Gate**. Produce and review
low-fidelity mockups plus state-transition flows for the launcher/controller,
Engineering Telematics Dashboard, OEM Software Delivery Dashboard, Brake
Health Function Dashboard, Tire Health Function Dashboard and every other
presenter- or audience-visible interface introduced by the implementation
plan. Existing interface areas that remain unchanged may be reused by
reference; every new or changed view, control and visible state must be
mocked.

Each mockup must identify its actor, purpose, authoritative data source,
protected action owner and relevant component/interface/requirement IDs. It
must cover the normal path and every applicable blocked, submitting,
uncertain/reconciling, failed, incomplete, stale, offline and redacted state.
This is an interaction and information-architecture review, not a visual-
polish exercise. Mockups remain derived views of accepted requirements and
contracts; they must not create a second behavior specification or a second
source of lifecycle state.

The I0 surface register 0.14, Interaction Specification 2.5 and UI
Traceability Register 1.1 are accepted. The standalone HTML review artifact is
reconciled to that contract, including fixed team context and version-only
scrolling. The
[Demo Implementation Plan 1.0](active/demo-implementation-plan.md) is the
current D5 review candidate and decomposes the accepted baseline into bounded
repository-owned increments. The older linear-flow HTML remains
comparison-only and is not an implementation baseline.

Exit: independently reviewable implementation increments, repository changes,
build boundaries and authorization gates are defined; the complete visible-
surface inventory and all new or changed low-fidelity mockups/state flows are
reviewed before the affected UI implementation begins.

## Future Implementation Workstreams

These workstreams are sequencing guidance, not authorization to implement:

| Workstream | Main outcome |
| --- | --- |
| `I0` Audience experience and UI mockups | Accepted surface register 0.14, Interaction Specification 2.5, UI Traceability Register 1.1 and reconciled standalone HTML review artifact with fixed team context/version-only scrolling; next freeze the implementation plan and reviewable UI increments. This gate precedes the UI portions of `I1`, `I3`, `I4` and `I5`. |
| `I1` Vehicle stimulus and Gateway | Qualify emergency-braking and explicit accelerated/pre-aged tire stimuli; add typed narrowly scoped advisory handling and dashboard status. |
| `I2` Factory and Vehicle Data Platform | Build and freeze the clean factory image with one IAM configuration containing `enablePermissionsHandler: true` for both modes, no pre-populated service permission/secret state, unmodified KUKSA, the separately packaged removable `CMP-KAC`, and the D4-010.1 dedicated non-secret `kuksa-jwt` PKCS#11/verifier-preparation wiring but no key/shared verifier. Qualify unique per-Unit signer bootstrap and atomic verifier preparation; independently implement and qualify the accepted VDP Component v1-v3 contract and its fixed OEM-trusted Provider integration through FOTA. |
| `I3` Brake Health product | Build the in-vehicle service, local model, bounded offline reporting, backend and function dashboard, including the release client surface statically pre-bound to D4-010.3 profile `brake-sp1`. |
| `I4` Tire Health product | Build the independent persistent condition estimator, bounded reporting, inspection advisory, backend and function dashboard, including the release client surface statically pre-bound to D4-010.3 profile `tire-sp2`. |
| `I5` Software delivery experience | Build the Software Delivery Dashboard over authoritative AosCloud APIs and the manufacturing/provisioning/promotion/retirement orchestration. Implement one session-scoped non-root native publication helper with separate fixed `platform-oem`, `brake-sp1` and `tire-sp2` surfaces; enforce the current local mode-`0600` PKCS#12 custody boundary, independent Cloud reconciliation and strict separation between technical publication and OEM approval. Add the single D4-020/D4-026.15 `Start or Restore Demo Environment` preflight: support-stack readiness with no VM/Unit dependency at `READY_FOR_M0`, one shared session-scoped DNS bridge, exact safe stale-runtime recovery and exact active-run VM restoration with per-role local/DNS/AosCore/Cloud readiness and fresh dual-Unit Online proof without creation or reprovisioning. Implement D4-026.17/`.19` and `REQ-DEMO-023`: Presenter Launcher-owned measured physical header/native/browser workspace composition, visibility/readability proof and safe local layout restoration, with shared-header meaning/navigation owned by the stateless Dashboard read model, fixed team context, version-only scrolling, independent team scroll restoration and no native-window embedding or lifecycle mutation. Implement D4-026.18/`REQ-DEMO-024`: title-selected right-hand Demo Lifecycle view for bounded Qualification Status, M0/M1/G0, current lifecycle/recovery and R0, with no fourth producer or duplication of native launcher actions. Keep M0 creation and M1 provisioning as separate explicit operations. Implement the D4-015 R0 planner with offline-only deprovision, post-`204` re-read, old-credential rejection, exact `system_uid` Unit Set removal, Unit deletion, Unit-owned Node-disappearance proof and no invented Node-delete operation; stop at `READY_FOR_M0` without automatically starting the next run. |
| `I6` Security and operations | Qualify native Aos IAM instance/permission lifecycle, `CMP-KAC` fixed-resource translation, short-lived JWT refresh/expiry and renewal denial, D4-010.1 unique per-Unit PKCS#11 signing and verifier startup/cross-Unit rejection/overlay retirement, the explicit trusted-Provider scope boundary, D4-014 OEM Unit-log versus SP1/SP2 Service-log role routing, exact identifiers/states/file bounds, deletion and offline/reconnect behavior, retention-policy exposure, redaction and bounded temporary-download removal. |
| `I7` End-to-end release proof | Execute `M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` on Validation and Production Units with retained evidence. |
| `I8` Edge Runtime Performance Qualification — deferred | After the first demo, benchmark VM power-on to AosCore readiness, Unit reconnect to service readiness, deployment-to-container readiness, crash/power-cycle recovery, offline continuation, reconnect synchronization, local event-to-advisory processing and CPU/RAM/storage/startup overhead. Cloud authentication, signing, approval and operator-interaction duration are not vehicle-performance KPIs. |

Each workstream requires the relevant component requirements and acceptance
tests before code or deployment work begins. Any workstream that creates or
changes an audience-visible interface additionally requires its accepted `I0`
mockup and state-flow package before UI code begins.

## Deferred Platform Capabilities

- Native AosCloud rejection of a SOTA request whose required Vehicle Data
  Platform Component version is absent or incompatible remains blocked on an
  implementing platform release. No project-side admission controller will be
  built as a substitute.
- Cloud-side pre-transfer rejection of a SOTA service whose requested KUKSA
  paths exceed an independent OEM upper bound remains future native platform
  behavior. The current broker validates native IAM identity and registered
  permissions against the installed VDP contract; it must not be presented as
  a second OEM-policy database or as Cloud admission.
- Production driver HMI, third-party Service Providers, Fleet Operators, a
  production fleet, and production vehicle-network/hardware selection remain
  outside the current demo.

## Current Stop Point

Documentation housekeeping gate D1, component-register gate D0 and joint
baseline gate D2 are complete. HLA 1.5, Scenario 2.0, Architecture Flows 2.0,
System Requirements 2.0, Component Register 2.0, ADR 0013 and ADR 0014 form the
accepted design baseline. The shared D4 contract and qualification decisions
are design-reviewed through D4-026.20 and D4-027.8; CR-E2E 0.8 completed D3
design review on 2026-08-27 while its implementation and live-qualification
gates remain open;
`D4-003` remains deliberately `RESEARCHING` only for implementation-time Tire
stimulus, calibration values and independent physical qualification series.
That empirical work belongs to I1 before audience presentation and is not a
missing invitation to invent values in design.

The standalone HTML review mockup is reconciled to Interaction Specification
2.5. The current next gate is review of
[Demo Implementation Plan 1.0](active/demo-implementation-plan.md), followed
by explicit authorization of one bounded first increment. No product UI,
component, Cloud or VM implementation is authorized by creating that plan.
Existing `CURRENT`, `EVIDENCE`,
`PARTIAL`, `GAP`, `TARGET` and implementation/qualification labels remain
truthful gates rather than implementation acceptance. No new repository,
component code, build, signature, Cloud upload, assignment, approval, VM
restart, provisioning, deprovisioning or Unit mutation is authorized by this
roadmap.
