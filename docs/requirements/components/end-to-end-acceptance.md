<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# End-to-End Acceptance Requirements

- Status: D3 design-reviewed; implementation and live qualification open
- Package: [`CR-E2E`](../component-decomposition-and-interface-register.md#cr-e2e)
- Version: 0.8
- Prepared: 2026-08-26
- Accepted: 2026-08-27
- Owner: System Acceptance with Platform, Function, Gateway and Demo Solution teams
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Previous accepted package: Version 0.6
- Accepted D4 source decision: [D4-005 Exclusive Live-Source Assignment](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Accepted D4 VISS decision: [D4-006 VISS Trust and Telemetry Profile](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Accepted D4 advisory decision: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Accepted D4 publication decision: [D4-010.3 Artifact Publication Credential Profile](../../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)
- Accepted D4 Cloud authority decision: [D4-011 Cloud Role and Action Matrix](../d4-decision-register.md#d4-011)
- Accepted D4 qualification decision: [D4-026.1–.20 Qualification, Presentation, Update-State, Workspace and Icon/Terminal Policy](../d4-decision-register.md#d4-026)
- Implementation, signing, Cloud, Unit, VM or CARLA mutation authorized: no

## Purpose

This package defines how the complete accepted demonstration is judged as one
system. It composes the already reviewed component, contract and integration
evidence into the canonical
`M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` acceptance sequence on
the Validation and Production Units.

`CR-E2E` adds no product behavior. It does not replace component requirements,
repeat their unit tests, own AosCloud state or become a runtime dependency. It
defines entry gates, exact acceptance scenarios, failure/abort rules, evidence
bindings and the scope of claims that may be shown to an audience.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | System-level acceptance of the complete staged demonstration and its bounded failure proofs |
| What this package does not own | Component logic, Cloud state, release decisions, credentials, product algorithms, a new test/runtime service or demo-run history |
| Intended result | One repeatable and truthful run proves manufacturing-to-retirement lifecycle, post-SOP evolution, two independent service teams, local/offline behavior and AosCore isolation |
| Accountable lifecycle owner | System Acceptance coordinates evidence; each Platform or Function Team retains its release decision and lifecycle ownership |
| Primary repository or external source | Acceptance specifications and orchestration references in `aosedge-sdv-demo`; product evidence remains in its owning repository or authoritative external system |

## Component Boundary

### In scope

- the complete canonical stage order and the entry/exit gate for every stage;
- Validation Unit qualification and owning-team acceptance before independent
  OEM Release Authority authorization of identical Production Unit rollout;
- one exclusive live CARLA/Gateway source used sequentially for the two roles;
- exact artifact, metadata, Unit, Node, Unit Set, source and evidence identity;
- current-recipient, owner-acceptance and OEM-authorization proof;
- VDP v1-v3, Brake Health v1-v3 and Tire Health v1.0 audience claims;
- native identity/permission, QM containment, logging and chronology proof;
- one targeted vehicle external-connectivity loss and same-Unit recovery;
- one AosCore-enforced Tire CPU-quota isolation proof with Brake as control;
- ordered retirement, functional-data cleanup, scenario reset, overlay disposal
  and unchanged Factory Image evidence; and
- clear separation of live audience proof, controlled qualification evidence,
  documentary evidence and explicitly deferred claims.

The accepted D4-026.1 vocabulary is `STATIC_CONFORMANCE`,
`CONTROLLED_DISPOSABLE_QUALIFICATION`, `LIVE_BASELINE_POSITIVE` and
`AUDIENCE_PRESENTATION`. Only an explicitly predesignated
`LIVE_BASELINE_POSITIVE` run may create the Demo Baseline Qualification
Dossier. An `AUDIENCE_PRESENTATION` uses current authoritative preflights and
fresh current-run identities but creates no dossier and retains no ordinary
run history.

D4-026.2 keeps the once-issued OEM, SP1 and SP2 Cloud certificates and their
fixed publication/operation profiles stable across runs. They are neither Unit
credentials nor R0-owned state. Fresh per-run overlays, Units, Main Nodes,
`system_uid` values and vehicle credentials are disposable; Aos IAM Service-
instance identity and short-lived KUKSA JWT are runtime-derived. Qualification
and audience runs use these fresh vehicle identities sequentially in the same
two persistent, empty-at-entry Verification and Production Unit Sets.

D4-026.5 keeps one current sealed local dossier at
`.local/qualification/current/` and one bounded status at
`.local/qualification/qualification-status.json`. A candidate is assembled in
`.local/qualification/candidate/`, validated, human-reviewed and sealed before
atomic replacement. No dossier history is kept and no dossier is uploaded
automatically. R0 preserves the current dossier/status while removing ordinary
run data; baseline mismatch makes the status `STALE`, and human withdrawal can
be cleared only by a new complete qualification.

D4-026.6 gives the audience presentation a planned 30-minute core narrative in
a 45-minute reserved slot, with Q&A separate. It keeps the complete M0/M1,
G0–G4, T1 and R0 story plus real preflights, VU validation, owner/OEM decisions,
recipient checks and authoritative re-reads mandatory. The presenter UI may
summarize those controls but cannot skip or simulate them. Real Cloud waiting
remains visible and may affect human presenter acceptance, but is not treated
as a vehicle or AosCloud performance claim. Negative/destructive/interruption
qualification remains outside the audience flow.

### Out of scope

- implementing or repairing any component during an acceptance run;
- source editing, compilation, image/container build, packaging, model training
  or full qualification execution during the presentation;
- a project admission controller, resource manager, identity provider, log
  archive, replay component or second lifecycle database;
- simultaneous VU and PU CARLA vehicles, production fleet/Fleet Operator,
  third-party Service Provider, safety certification or production driver HMI;
- Cloud-operation timing as a vehicle KPI and broad network-fault testing;
- native Cloud admission of a SOTA service against a required FOTA Vehicle
  Data Platform Component version until an implementing AosEdge release is
  available and qualified; and
- retaining telemetry, events, advisories or dashboard history from ordinary
  completed demo runs after `R0`.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Accepted component packages | Every `CR-*` owner | D3 design reviewed; D4 contracts and required implementation evidence complete for the attempted scope | E2E execution is blocked, not waived |
| OEM Demo Factory Image and prepared candidates | Platform and Function Teams | Exact immutable versions/digests, compatibility and secret-negative evidence | `M0` or affected release stage cannot start |
| Validation and Production lanes | AosCloud/OEM + Demo Solution | Fresh Units, exact disjoint Unit Set membership and current authoritative state | Every Unit-affecting action is blocked |
| One live CARLA/Gateway source | Simulator/Gateway owner | Exclusive attach, detach, canonical reset and new generation are provable | Next Unit role cannot attach |
| Authoritative Cloud and functional surfaces | AosCloud and Function Teams | Current scoped APIs and honest unavailable/stale states | Claim remains unproved or explicitly unavailable |
| Native KUKSA/Aos security and runtime | Platform/AosEdge | Accepted identity/permission, `CMP-KAC`, signer/verifier, trusted Provider integration and quota mechanisms | Service readiness or affected proof fails closed |
| R0 qualified destructive operations | AosCloud integration + Demo Solution | Exact selectors, preview, ordering, reconciliation and recovery | Records/overlays are preserved for reconciliation; next run is blocked |

## Testability Boundary

`CR-E2E` owns no independent product decision or runtime executable and creates
no `UT-E2E-*` obligations. Unit, component and contract tests remain blocking
in their accepted owner packages. This package consumes their version-bound
results and defines stable `AT-E2E-*` system acceptance scenarios.

Any reusable acceptance runner, fixture catalogue or evidence normalizer may
live in `aosedge-sdv-demo`, but its owned branching logic remains covered by
`CR-DEMO` unit obligations. It must not reimplement product policy, create a
parallel desired state or become an in-vehicle dependency.

## Interface Summary

| Interface group | Direction | System acceptance concern | Failure behavior | Authority |
| --- | --- | --- | --- | --- |
| [`IF-VEH-001`–`007`](../component-decomposition-and-interface-register.md#if-veh-001) | CARLA ↔ Gateway/VISS/Dashboard/OEM runtime | Vehicle profile, applied control, VSS telemetry, source generation, factual state and read-only Platform-update Safe Stop evidence | Safe stop, unavailable/degraded state or stage block | CARLA/Gateway facts; OEM runtime update policy |
| [`IF-DATA-001`–`002`](../component-decomposition-and-interface-register.md#if-data-001), [`IF-TIRE-001`](../component-decomposition-and-interface-register.md#if-tire-001) | VDP/KUKSA → services | Versioned read contracts and data quality | Service not ready or `NOT_EVALUATED`; no fabricated normal state | Installed VDP contract and KUKSA |
| [`IF-ADV-001`–`005`](../component-decomposition-and-interface-register.md#if-adv-001), [`IF-TIRE-002`](../component-decomposition-and-interface-register.md#if-tire-002) | Services → KUKSA/VDP/VISS/Gateway | Typed QM maintenance advisories and factual status | Fail closed; Gateway remains final authority | IAM/KUKSA, VDP defense in depth and Gateway policy |
| [`IF-AUTH-007`–`010`](../component-decomposition-and-interface-register.md#if-auth-007) | Services ↔ `CMP-KAC` ↔ Aos IAM/KUKSA security substrate | Fixed-resource bootstrap, private volatile scoped JWT and verifier/signer lifecycle | No credential/readiness; no cached/static fallback | Aos IAM result plus per-Unit platform trust; Provider remains a separate trusted OEM integration |
| [`IF-FUNC-001`–`002`](../component-decomposition-and-interface-register.md#if-func-001), [`IF-TIRE-003`–`004`](../component-decomposition-and-interface-register.md#if-tire-003) | Services ↔ functional Cloud products | Bounded, versioned, idempotent results and exact cleanup | Queue/degraded/loss state is explicit | Owning Function Team contract |
| [`IF-LC-001`–`010`](../component-decomposition-and-interface-register.md#if-lc-001) | Teams/Dashboard/AosCloud/AosCore | Publication, approval, desired/actual state, targeting, runtime and quota enforcement | Mutation blocked or reconciled from authoritative state | Owning team decision, OEM identity and AosCloud/AosCore state |
| [`IF-OBS-001`](../component-decomposition-and-interface-register.md#if-obs-001) | OEM Software Delivery / Brake / Tire Dashboard ↔ AosCloud | OEM Unit system/VDP logs versus separate SP1/SP2 Service-owned service/crash logs | Wrong role/owner blocks; documented states remain verbatim; no second archive or retention-duration claim | AosCloud request/file state while retained |
| [`IF-DEMO-001`](../component-decomposition-and-interface-register.md#if-demo-001) | Orchestrator → local actors | Session, VM/source lifecycle, faults and safe retirement | Partial/uncertain state blocks progression | Local session manifest plus authoritative external state |
| [`IF-DEMO-002`](../component-decomposition-and-interface-register.md#if-demo-002) | Presenter Launcher/workspace ↔ shared header and visible surfaces | Measured full-screen composition, stable native/browser window ownership, readability and local restoration without changing lifecycle state | `WORKSPACE INCOMPLETE`; protected actions remain blocked while authoritative read-only facts stay available | Presenter Launcher owns the physical shell; Representation Layer owns header meaning from the same read model; each surface owner retains its content |

## Verification Strategy

| Level | Purpose | Required | Evidence consumed by `CR-E2E` |
| --- | --- | --- | --- |
| Unit | Prove deterministic owner decisions and failure branches | Yes, in owner packages; no duplicate E2E unit suite | Exact owner-suite revision and result |
| Component | Prove each packaged executable through its public boundary | Yes where allocated | Component report, artifact digest and configuration identity |
| Contract | Prove every producer/consumer agreement and negative matrix | Yes | Versioned fixture/conformance digest and result |
| Integration | Prove real adjacent components and external-platform behavior | Yes | Validation-environment record tied to exact revisions and Unit role |
| End-to-end | Prove the accepted audience claim and bounded failure scenarios | Yes | `AT-E2E-*` result, authoritative state and sanitized evidence dossier |

Not every negative or destructive test is repeated live for an audience. The
D3 review must decide which scenarios are live, which are controlled
qualification, and which are documentary/deferred. A stored green result
never substitutes for current prerequisite/target checks where the action can
affect a Unit.

## Acceptance State Model

Acceptance shall preserve three different kinds of state rather than flatten
them into one dashboard status:

| State layer | Values or source | Meaning |
| --- | --- | --- |
| Authoritative external state | Exact, unmodified AosCloud, AosCore, CARLA/Gateway or Function Backend value plus source timestamp and object identity | What the owning external system currently reports; examples include Fleet Validation `Waiting_validation`/`Valid`/`Invalid`, Campaign state/statistics and Unit-reported actual state |
| Orchestration state | `READY`, `BLOCKED`, `WAITING`, `SUBMITTING`, `UNCERTAIN`, `RECONCILING`, `RECOVERY_REQUIRED` | Whether `CR-DEMO` may perform or continue one bounded action; this is local control state and is never presented as an AosCloud state. `WAITING` means a known external prerequisite is pending without resubmission; `RECOVERY_REQUIRED` means bounded reconciliation or local restoration is required before another protected action |
| Acceptance result | `NOT_EVALUATED`, `PASSED`, `FAILED`, `ABORTED` | The verdict for one entry-gate/action/re-read/exit-gate attempt; it is assigned only from the accepted evidence rule and is never written back as Cloud lifecycle state |

Stable `AT-E2E-*` identifiers are acceptance cases. A complex case contains
ordered atomic stages identified as `AT-E2E-NNN/SNN`; each atomic stage follows
`entry gate -> one bounded action -> authoritative re-read -> exit gate`.
The case verdict composes all mandatory stage verdicts without renumbering the
accepted case. `BLOCKED` means that no mutation was submitted. A timeout,
transport loss or lost response after submission becomes `UNCERTAIN`, never a
guessed failure or success and never an automatic retry. Reconciliation moves
the local state to `RECONCILING`, re-reads the owning external system and then
either resumes from the discovered applied state, permits a new explicit
action after proving that the mutation was not applied, or remains blocked.

Cloud-native words such as Campaign `success`/`fail`, Fleet Validation
`Valid`/`Invalid` and Unit/service `failed` remain visible verbatim. They are
inputs to an acceptance result, not interchangeable aliases for it.

## Evidence Retention Model

Evidence retention distinguishes three cases:

| Case | Retained after successful R0 | Deleted at R0 |
| --- | --- | --- |
| Ordinary audience demo run | No project-owned run history; AosCloud retains its own authoritative audit history | Functional telemetry, windows, events, assessments, advisories, Function Dashboard records, dashboard cache/presentation state, CARLA run-local evidence, temporary log downloads and the reconciled operation journal |
| Pre-designated Demo Solution Qualification Run | One sealed Demo Baseline Qualification Dossier containing an evidence ID, exact subject/artifact and metadata digests, AosEdge/API release, configuration digest, verification time, verdict, claim boundary, cleanup result and fingerprinted references to authoritative Cloud audit objects | Raw telemetry and functional payloads, raw secret-bearing responses, reusable credentials, unredacted Unit identities, complete Cloud-state copies, temporary downloads and replayable run history |
| Failed or uncertain operation | Only the minimal redacted recovery journal required to reconcile the external mutation and prevent unsafe continuation | The journal is deleted immediately after successful reconciliation; it never becomes ordinary demo history |

A platform defect or other incident may produce a separate sanitized incident
dossier only through an explicit operator decision. Incident capture is not an
automatic side effect of a demo run. Cleanup proof may retain bounded counts,
digests and verdicts, but never the payload that R0 was required to delete.
The dashboard and orchestrator do not duplicate AosCloud's audit database or
native log archive.

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| [Factory and candidate preflight (`REQ-E2E-001`)](#req-e2e-001) | Admit only the exact clean factory artifact, fresh overlays and prepared candidates | Inspection, Integration, End-to-end | Design reviewed |
| [Provisioned baseline and source truth (`REQ-E2E-002`)](#req-e2e-002) | Establish fresh VU/PU identities, disjoint sets and one honest live source at G0 | Integration, End-to-end | Design reviewed |
| [Authoritative release governance (`REQ-E2E-003`)](#req-e2e-003) | Prove team decision, OEM authorization, exact recipients and validation-first identical promotion | Contract, Integration, Audit, End-to-end | Design reviewed |
| [G1 platform data capability (`REQ-E2E-004`)](#req-e2e-004) | Prove VDP v1 delivery and the first honest VISS-to-KUKSA data path | Integration, End-to-end | Design reviewed |
| [G2 bounded Brake Health acquisition (`REQ-E2E-005`)](#req-e2e-005) | Prove independent SOTA 1 and bounded v1 braking-window delivery | Integration, End-to-end | Design reviewed |
| [G3 independent platform/service evolution (`REQ-E2E-006`)](#req-e2e-006) | Prove backward-compatible VDP v2 plus local synthetic Brake assessment and derived-only Cloud output | Integration, End-to-end | Design reviewed |
| [G4 advisory and external-connectivity continuity (`REQ-E2E-007`)](#req-e2e-007) | Prove typed QM advisory, local offline operation and same-Unit convergence | Integration, Analysis, End-to-end | Design reviewed |
| [T1 peer service and tenant isolation (`REQ-E2E-008`)](#req-e2e-008) | Prove independent Tire SOTA 2 and AosCore CPU-quota isolation from Brake | Integration, End-to-end | Design reviewed |
| [Cross-stage security and truthful evidence (`REQ-E2E-009`)](#req-e2e-009) | Preserve least privilege, containment, correlation, chronology, native logs and honest claim state | Contract, Integration, Analysis, End-to-end | Design reviewed |
| [R0 retirement and next-run readiness (`REQ-E2E-010`)](#req-e2e-010) | Retire both identities and run data, reset local state and preserve the immutable factory source | Integration, Analysis, End-to-end | Design reviewed |
| [Bounded abort, recovery and repeatability (`REQ-E2E-011`)](#req-e2e-011) | Stop safely on uncertain evidence and repeat the accepted sequence without hidden state reuse | Integration, Analysis, End-to-end | Design reviewed |
| [Composed presenter workspace (`REQ-E2E-012`)](#req-e2e-012) | Qualify the exact full-screen workspace, shared header and local restoration without creating another authority or state store | Integration, Human, End-to-end | Design reviewed |

## Detailed Requirements

<a id="req-e2e-001"></a>
### Factory and candidate preflight

- Statement: Acceptance shall start only from the exact clean OEM Demo Factory Image, two fresh role-bound overlays and the complete set of prebuilt, tested and content-frozen VDP, Brake and Tire candidates whose versions, artifact/metadata digests, compatibility and secret-negative evidence match the accepted baseline.
- Parents: [`SYS-MFG-001`–`003`](../system-requirements-and-traceability.md#sys-mfg-001), [`SYS-REL-001`](../system-requirements-and-traceability.md#sys-rel-001) and [`SYS-RET-005`](../system-requirements-and-traceability.md#sys-ret-005)
- Flows: [`AF-M0-LC`](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc), [`AF-M0-OB`](../../architecture/demo-scenario-architecture-flows.md#af-m0-ob), [`AF-M0-FR`](../../architecture/demo-scenario-architecture-flows.md#af-m0-fr)
- Acceptance: any digest, compatibility, identity-cleanliness, overlay-freshness or secret-negative mismatch blocks `M1`; no presentation-time build fallback exists.

<a id="req-e2e-002"></a>
### Provisioned baseline and source truth

- Statement: `M1/G0` shall prove one unique Unit/Main Node and per-Unit VISS client identity per overlay, exact disjoint Verification/Production Unit Set membership, current online/graph state, a healthy empty VDP slot, a working authenticated CARLA/Gateway/VISS/Engineering Dashboard path and one exclusive selected-Unit live-source assignment. The audience sees Test Vehicle and Production Vehicle, exactly one `CURRENT VEHICLE`, and a plain `Continue with Production Vehicle` transition; Test Vehicle maps only at the Representation Layer to the technical Validation Unit in the Verification Unit Set. Technical details preserve exact Unit/source/certificate-fingerprint evidence without presenting host assignment plumbing as in-vehicle behavior or implying two simultaneous live vehicles.
- Parents: [`SYS-ID-001`–`004`](../system-requirements-and-traceability.md#sys-id-001), [`SYS-SRC-001`–`004`](../system-requirements-and-traceability.md#sys-src-001), [`SYS-CTRL-001`–`003`](../system-requirements-and-traceability.md#sys-ctrl-001), [`SYS-VDP-001`](../system-requirements-and-traceability.md#sys-vdp-001)
- Flows: `AF-M1-*`, `AF-G0-*`, [`AF-X-SOURCE`](../../architecture/demo-scenario-architecture-flows.md#af-x-source), [`AF-X-DRIVE`](../../architecture/demo-scenario-architecture-flows.md#af-x-drive)
- Executable contracts: [Exclusive Live-Source Assignment 1.0.0](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json) and [VISS Trust and Telemetry Profile 1.0.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Acceptance: partial provisioning, crossed/stale Unit membership, ambiguous source ownership, failed canonical reset or non-empty feature state blocks the next stage.

<a id="req-e2e-003"></a>
### Authoritative release governance

- Statement: Every FOTA/SOTA stage shall bind the D4-013 producer manifest, pinned Demo Release Set entry, exact prepared/signed/Cloud identity chain, effective recipients, validation evidence, owning-team acceptance and active D4-011 `oem-delivery` role/effective permissions. Technical publication shall use only the fixed D4-010.3 profile and reach `PUBLISHED` only after independent Cloud re-read; publisher identity shall never satisfy the delivery-authority gate. Independent OEM Release Authority shall separately authorize Test deployment and, after owning-team Validation acceptance, Production rollout; AosCloud shall record and execute each explicit `oem-delivery` decision. Different teams' protected operations remain independent when their exact candidate/operation and resource-conflict key sets are disjoint; only overlapping keys block, while provisioning, source handover and R0 remain run-exclusive. Ambiguity shall enter `UNCERTAIN` without blind retry. PU shall receive the same accepted Cloud Component or Service Version used on VU, with no rebuild, re-sign, re-publication or re-upload; PU desired/actual/readiness reads confirm rollout health and are not a second product-validation cycle. SOTA evidence shall retain the locally verified signed digest without claiming a Cloud-side content digest absent from API 6.1.26. Vehicle-state evidence shall prove the factory-installed OEM Component Runtime inside AosCore Service Manager holds Platform FOTA in a durable waiting state until fresh Gateway evidence proves Safe Stop, while accepted Brake/Tire QM Service SOTA may be exercised in motion; neither the dashboard nor AosCloud shall be presented as the physical-motion enforcement point.
- Parents: [`SYS-REL-002`–`012`](../system-requirements-and-traceability.md#sys-rel-002) and [`SYS-OBS-002`](../system-requirements-and-traceability.md#sys-obs-002), [`SYS-OBS-006`](../system-requirements-and-traceability.md#sys-obs-006)
- Flows: [`AF-X-RELEASE`](../../architecture/demo-scenario-architecture-flows.md#af-x-release), all stage lifecycle flows
- Acceptance: wrong publication profile/candidate/type/path/URL, local credential custody failure, missing independent publication re-read, stale/unprovable recipients, wrong `oem-delivery` role or effective permission, missing owner, changed digest, incomplete/stale evidence, documented API error, ambiguous result or post-action mismatch blocks progression. Technical publication never counts as technical-verification, validation or deployment approval in the demo. Existing AosEdge component-to-component and service-to-layer dependency mechanisms remain accepted platform capabilities. Only native Cloud admission of a SOTA service against a required FOTA Vehicle Data Platform Component version remains visibly deferred until an implementing release is qualified; no local substitute is accepted.

<a id="req-e2e-004"></a>
### G1 platform data capability

- Statement: The accepted VDP v1 FOTA candidate shall be validated on VU and promoted identically to PU, with both OEM-runtime applications occurring only after the accepted Safe Stop policy is proven from fresh Gateway facts. It shall become ready only with its accepted VISS contract and publish the exact v1 read-only signal subset into KUKSA with factual quality, freshness, availability and provenance. Each vehicle resumes driving only through an explicit post-readiness control action.
- Parents: [`SYS-VDP-001`](../system-requirements-and-traceability.md#sys-vdp-001), [`SYS-VDP-002`](../system-requirements-and-traceability.md#sys-vdp-002), [`SYS-VDP-005`](../system-requirements-and-traceability.md#sys-vdp-005), [`SYS-REL-004`](../system-requirements-and-traceability.md#sys-rel-004)
- Flows: `AF-G1-*`, `AF-X-RELEASE`, `AF-X-SOURCE`
- Executable VISS input: [VISS Trust and Telemetry Profile 1.0.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Executable Safe Stop contract: [Platform FOTA Safe Stop 1.0.1](../../../contracts/platform-fota-safe-stop/platform-fota-safe-stop-profile.v1.json)
- Acceptance: a non-selected or unauthenticated Unit is rejected; missing/stale/malformed source data becomes atomically unavailable and recovers only from a complete valid snapshot; moving/stale/reset-discontinuous update evidence cannot cross the runtime gate; no service is required at G1 and no fabricated normal value is accepted.

<a id="req-e2e-005"></a>
### G2 bounded Brake Health acquisition

- Statement: Function Team 1 shall independently publish Brake Health Service v1 and accept its exact VU result; OEM Release Authority shall separately authorize Test deployment and identical PU rollout. On PU, one deterministic braking event produces a bounded pre/active/post window, ordered chunks/completion, idempotent backend reconstruction and factual dashboard evidence.
- Parents: [`SYS-BHS-005`](../system-requirements-and-traceability.md#sys-bhs-005), [`SYS-BHS-004`](../system-requirements-and-traceability.md#sys-bhs-004), [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001), [`SYS-REL-003`](../system-requirements-and-traceability.md#sys-rel-003)
- Flows: `AF-G2-*`, `AF-X-AUTH`, `AF-X-OBS`
- Acceptance: no trigger produces no window; overflow/duplicate/transport failure remains bounded and explicit; continuous unrestricted raw streaming is not accepted.

<a id="req-e2e-006"></a>
### G3 independent platform and service evolution

- Statement: VDP v2 shall be a backward-compatible superset of v1, and Brake Health Service v2 shall use its prepared synthetic model for deterministic local assessment while normal Cloud output changes from v1 windows to bounded derived assessments/events. Platform and Function Team decisions, OEM authorizations, Cloud objects and readiness outcomes shall remain independent. PU shall apply VDP v2 first, preserve the prior compatible Brake Service, and only then permit the separately authorized Brake v2 rollout. G3 shall be derived after both releases and live behavior are proven rather than promoted as a group.
- Parents: [`SYS-VDP-003`](../system-requirements-and-traceability.md#sys-vdp-003), [`SYS-BHS-002`](../system-requirements-and-traceability.md#sys-bhs-002), [`SYS-BHS-006`](../system-requirements-and-traceability.md#sys-bhs-006), [`SYS-REL-007`–`009`](../system-requirements-and-traceability.md#sys-rel-007)
- Flows: `AF-G3-LC`, `AF-G3-RT`, `AF-G3-OB`, `AF-G3-FR`
- Acceptance: the existing v1 consumer contract remains valid, model/result identity is visible, normal v2 behavior does not emit v1 high-detail windows, VDP-only Production readiness is a valid `G3 · 1 of 2` state, Service failure does not roll back VDP, and G3 completes only after the separate Service release and live behavior succeed.

<a id="req-e2e-007"></a>
### G4 advisory and external-connectivity continuity

- Statement: VDP v3 and Brake Health Service v3 shall retain separate owner acceptance, OEM authorization, Cloud lifecycle and readiness chains, with provider-first PU application and a derived G4 milestone only after both exact releases and live behavior are proven. Together they shall complete the exact D4-008 Request/Status round trip through KUKSA, VDP, VISS and the authoritative Gateway, including application evidence distinct from Set success, explicit clear, auto-expiry and stale/replay/cross-target/motion-write rejection. One atomic PU external-connectivity fault shall interrupt AosCloud and all installed functional-backend paths together while local assessment/advisory continues, then reconnect the same Unit and synchronize bounded messages idempotently without reinstall or restart.
- Parents: [`SYS-VDP-004`](../system-requirements-and-traceability.md#sys-vdp-004), [`SYS-BHS-003`–`004`](../system-requirements-and-traceability.md#sys-bhs-003), [`SYS-SEC-003`](../system-requirements-and-traceability.md#sys-sec-003), [`SYS-SEC-007`](../system-requirements-and-traceability.md#sys-sec-007), [`SYS-OBS-007`](../system-requirements-and-traceability.md#sys-obs-007)
- Flows: `AF-G4-*`, [`AF-X-QM`](../../architecture/demo-scenario-architecture-flows.md#af-x-qm), [`AF-X-OFFLINE`](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Acceptance: VDP-only readiness is a valid `G4 · 1 of 2` state, Brake v3 failure does not roll back healthy VDP v3, no group approval/object is created, presenter-to-AosCloud and in-vehicle connectivity remain available; only matching Gateway `APPLIED`/`CLEARED` is success, unauthorized/arbitrary/replay/motion writes fail closed, lease expiry is factual, and original/Gateway/synchronization times remain distinct.

<a id="req-e2e-008"></a>
### T1 peer service and tenant isolation

- Statement: Function Team 2 shall independently deliver one Tire Health v1.0 candidate against accepted VDP v3, prove local persistent condition estimation, bounded result/advisory behavior and independent backend/dashboard state, then run the fixed prepared Tire CPU load to its approved quota. The proof shall use three consecutive fresh AosCloud samples for baseline, qualified saturation and recovery; a separately labelled cgroup cap/throttle qualification bound to the exact runtime baseline; the same Tire instance without restart/redeployment; and one completed deterministic Brake event with Brake, VDP, KUKSA, Gateway, AosCore and Unit healthy. It shall introduce no new latency KPI.
- Parents: [`SYS-TIRE-001`–`006`](../system-requirements-and-traceability.md#sys-tire-001), [`SYS-RES-001`](../system-requirements-and-traceability.md#sys-res-001)
- Flows: `AF-TIRE-LC`, `AF-TIRE-RT`, `AF-TIRE-OB`, `AF-TIRE-FR`, [`AF-TIRE-RES`](../../architecture/demo-scenario-architecture-flows.md#af-tire-res)
- Acceptance: Tire and Brake identities, permissions, quotas, SOTA lifecycles and products remain distinct; `PASS`, `FAIL`, `INCONCLUSIVE` and `NOT_READY` follow the D4-023.5 sample/evidence rules and a quota alert never determines the verdict by itself; Mac-local backends and aggregate multi-service-per-provider quota enforcement remain outside the AosCore claim.

<a id="req-e2e-009"></a>
### Cross-stage security and truthful evidence

- Statement: Across all stages, accepted evidence shall prove native Aos-derived least-privilege KUKSA authority through fixed-resource `CMP-KAC` bootstrap, private volatile short-lived JWT delivery, protected per-Unit signing, stop/removal/reboot cleanup, trusted OEM Provider separation, Gateway-final QM containment, D4-014 role-separated native logs, exact run/Unit/source correlation and distinct source/local/receipt/synchronization chronology without secrets, false retention, false latency or widened claims. OEM Unit system/VDP log access and SP1/SP2 Service-owned service/crash access shall use distinct endpoint/credential allowlists, expose no browser credential or second archive, and state that retention policy is not exposed by current API. The first demo shall not claim dynamic Provider IAM/JWT or malicious/substituted-Provider containment.
- Parents: [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001), [`SYS-SEC-003`](../system-requirements-and-traceability.md#sys-sec-003), [`SYS-SEC-004`](../system-requirements-and-traceability.md#sys-sec-004), [`SYS-SEC-007`](../system-requirements-and-traceability.md#sys-sec-007), [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008), [`SYS-OBS-001`–`006`](../system-requirements-and-traceability.md#sys-obs-001), [`SYS-TIM-002`](../system-requirements-and-traceability.md#sys-tim-002)
- Flows: `AF-X-AUTH`, `AF-X-QM`, `AF-X-OBS`, `AF-X-SOURCE`
- Acceptance: invalid/stale/cross-Service identities, caller-selected authority, expiry, permission removal, cross-team/system log access and unsafe advisory requests fail without side effects; reboot, Service stop/unregistration and R0 remove volatile authorization state; trusted Provider evidence is separate and bounded to the declared first-demo assumption; dashboard evidence preserves verbatim external state or is explicitly unavailable/stale/deferred.
- State: D4-024 shared correlation, chronology, sanitized projection and ordering design reviewed; executable/live evidence is allocated to D4-025 qualification.

<a id="req-e2e-010"></a>
### R0 retirement and next-run readiness

- Statement: After the final stage, R0 shall capture each final Unit UUID/`system_uid`/Main Node/set/state, make both Units authoritatively `Offline`, invoke the offline-only Unit deprovision API through `oem-delivery`, reconcile every no-content result by a fresh Unit read, and prove old credentials cannot return either Unit `Online`. It shall then stop each VM, delete only the exact current-run native-log request IDs, remove each `system_uid` from its exact role Unit Set and re-read membership, delete the Unit records, and prove through active-Unit/detail/nested-Node/set reads that both Units and their Unit-owned Nodes are inaccessible and both sets are empty before functional-data deletion, CARLA/Gateway reset and overlay disposal. API v11 exposes no standalone Node-delete operation and the demo shall not invent one. The unchanged Factory Image digest remains the source for two fresh next-run overlays and identities.
- Parents: [`SYS-RET-001`–`006`](../system-requirements-and-traceability.md#sys-ret-001), [`SYS-ID-004`](../system-requirements-and-traceability.md#sys-id-004)
- Flows: `AF-R0-LC`, `AF-R0-OB`, `AF-R0-FR`
- Acceptance: a timeout or lost response enters `UNCERTAIN` then `RECONCILING` and never causes blind retry; an authorization-masked `404` is not absence proof without independently established visibility; a reachable Unit-owned Node or uncertain deprovision/delete/membership state preserves records and overlays and blocks the next run. R0 is never labelled an in-field OTA rollback or fleet policy.

<a id="req-e2e-011"></a>
### Bounded abort, recovery and repeatability

- Statement: Every stage shall have a defined entry gate, one bounded action, authoritative re-read, exit gate and safe abort/reconciliation boundary. It shall preserve exact external source state separately from local orchestration state and acceptance result. A missing, stale, failed, partial or ambiguous prerequisite shall prevent the next irreversible action, and a new accepted run shall reproduce the same stage outcomes from the unchanged Factory Image and new identities without reusing old target, source or functional-data assumptions.
- Parents: [`SYS-ID-002`](../system-requirements-and-traceability.md#sys-id-002), [`SYS-REL-002`](../system-requirements-and-traceability.md#sys-rel-002), [`SYS-OBS-004`](../system-requirements-and-traceability.md#sys-obs-004), [`SYS-RET-006`](../system-requirements-and-traceability.md#sys-ret-006)
- Flows: every `*-FR` flow plus `AF-X-RELEASE` and `AF-X-SOURCE`
- Acceptance: `BLOCKED` submits no mutation; `UNCERTAIN` never triggers a blind retry; `RECONCILING` requires a fresh authoritative read; and only a passed exit gate permits the next stage. `PASSED`, `FAILED` and `ABORTED` remain acceptance verdicts rather than claimed AosCloud states. No automatic approval, ambiguous continuation or destructive cleanup is accepted. Repeatability requires two consecutive complete live-positive cycles rather than retained ordinary-run history. Cycle B is also a human presenter rehearsal. Final qualification requires both machine pass and human acceptance; human rejection vetoes machine success, while human acceptance can never waive a non-passing machine result.

<a id="req-e2e-012"></a>
### Composed presenter workspace

- Statement: Formal acceptance shall qualify the exact presenter-Mac display profile as one composed full-screen workspace containing the shared header, CARLA, Vehicle Controller, Engineering Telematics Dashboard and active browser stage without required tab switching. Presenter Launcher shall own only physical window discovery, placement, visibility, non-overlap, readability and local restoration; the stateless Representation Layer shall own shared-header meaning, team navigation and the title-selected right-hand global Demo Lifecycle page from the same browser read model; every visible surface owner shall retain its content. In every producer perspective, the one-line team purpose, compact non-selectable Release Authority line, state summaries and current team evidence panels shall remain fixed and fully readable while only the release/version region scrolls; Platform, Brake and Tire shall restore independent release/version scroll and focus context. The global page shall present the bounded Qualification Status, M0/M1/G0, current lifecycle/recovery and R0 without becoming a fourth producer or duplicating native launcher actions and may use its own independent whole-page right-region scroll. Workspace restoration and browser navigation shall neither mutate AosCloud/vehicle lifecycle state nor create another state store.
- Parents: [`SYS-SRC-002`](../system-requirements-and-traceability.md#sys-src-002) and [`SYS-OBS-001`](../system-requirements-and-traceability.md#sys-obs-001)
- Interface: [`IF-DEMO-002`](../component-decomposition-and-interface-register.md#if-demo-002)
- Interaction contract: [`UI-INT-004`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-int-004), [`UI-INT-008`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-int-008), [`UI-INT-010`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-int-010), [`UI-INT-078`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-int-078), [`UI-INT-079`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-int-079), [`UI-AT-002`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-at-002), [`UI-AT-004`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-at-004), [`UI-AT-049`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-at-049) and [`UI-AT-050`](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-at-050)
- Acceptance: wrong/missing window ownership, obscured required surface, reserved-header overlap, unreadable measured geometry or failed restoration produces `WORKSPACE INCOMPLETE` and blocks protected actions. Title/global/team navigation changes only the right region, preserves team state, keeps left evidence visible and renders the exact bounded Qualification/lifecycle facts without manual green override or launcher-action duplication. At the qualified viewport, each team context remains fixed, unscrolled and fully readable, only its release/version region scrolls, and returning to a team restores only that team's release/version scroll and focus. Read-only authoritative facts remain available where their owners are healthy. A successful local restore or navigation action changes no Cloud, Unit, source or release state.

## System Requirement Coverage Allocation

| Active system-requirement family | E2E allocation |
| --- | --- |
| `SYS-MFG-001..003` | `REQ-E2E-001`, `002` |
| `SYS-ID-001..004` | `REQ-E2E-002`, `010`, `011` |
| `SYS-SRC-001..004` | `REQ-E2E-002`, `009`, `011`, `012` |
| `SYS-CTRL-001..003` | `REQ-E2E-002`, `009` |
| `SYS-REL-001..012` | `REQ-E2E-001`, `003`, `004..008`, `011`; `SYS-REL-006` remains deferred |
| `SYS-VDP-001..005` | `REQ-E2E-002`, `004`, `006`, `007`, `008` |
| active Brake requirements `SYS-BHS-002..006` excluding retired `SYS-BHS-001` | `REQ-E2E-005`, `006`, `007` |
| `SYS-TIRE-001..006` | `REQ-E2E-008` |
| active Security requirements `SYS-SEC-001`, `003`, `004`, `007`, `008` | `REQ-E2E-005`, `007`, `008`, `009` |
| `SYS-OBS-001..007` | `REQ-E2E-002`, `003`, `007`, `009`, `011`, `012` |
| `SYS-TIM-002` | `REQ-E2E-007`, `009` |
| `SYS-RES-001` | `REQ-E2E-008` |
| `SYS-RET-001..006` | `REQ-E2E-001`, `010`, `011` |

Retired `SYS-BHS-001`, `SYS-EVT-001..005`, `SYS-SEC-002`, `SYS-SEC-005`,
`SYS-SEC-006` and `SYS-TIM-001`
remain linkable historical records and are not active acceptance inputs.

## End-to-End Acceptance Scenarios

| Acceptance scenario | Main requirements | Mode | Required outcome |
| --- | --- | --- | --- |
| <a id="at-e2e-001"></a>`AT-E2E-001` — M0 preflight | `REQ-E2E-001` | `STATIC_CONFORMANCE` + `LIVE_BASELINE_POSITIVE` inspection | Exact clean factory/candidate identities and two fresh overlays; mismatch blocks |
| <a id="at-e2e-002"></a>`AT-E2E-002` — M1/G0 baseline | `REQ-E2E-002`, `009` | `LIVE_BASELINE_POSITIVE` | Fresh identities/sets, empty feature graph and one honest working vehicle source |
| <a id="at-e2e-003"></a>`AT-E2E-003` — Common release gate | `REQ-E2E-003`, `011` | `LIVE_BASELINE_POSITIVE`; related negatives are `AT-E2E-009`/`011` instances | Exact fixed publication profile/candidate/digests, independent Cloud publication re-read, exact recipients/evidence, separate `oem-delivery` role/effective permissions and approval, authoritative error/reconciliation behavior, VU first, identical PU promotion and deferred feature labelled honestly |
| <a id="at-e2e-004"></a>`AT-E2E-004` — G1 platform capability | `REQ-E2E-004` | `LIVE_BASELINE_POSITIVE` | VDP v1 data reaches KUKSA with factual quality and accepted graph state |
| <a id="at-e2e-005"></a>`AT-E2E-005` — G2 Brake v1 | `REQ-E2E-005` | `LIVE_BASELINE_POSITIVE` | Bounded event window reaches Function Team 1 product independently |
| <a id="at-e2e-006"></a>`AT-E2E-006` — G3 independent platform/service evolution | `REQ-E2E-003`, `006` | `LIVE_BASELINE_POSITIVE`; compatibility negatives are `AT-E2E-009` instances | Backward-compatible VDP v2 and deterministic derived-only Brake v2 behavior through two independent releases and a derived milestone |
| <a id="at-e2e-007"></a>`AT-E2E-007` — G4 advisory/offline | `REQ-E2E-007`, `009` | `LIVE_BASELINE_POSITIVE` | Typed advisory, atomic external disconnect, local continuity and same-Unit convergence |
| <a id="at-e2e-008"></a>`AT-E2E-008` — T1 peer/isolation | `REQ-E2E-008`, `009` | `LIVE_BASELINE_POSITIVE` | Independent Tire SOTA 2 plus AosCore cap with unaffected Brake/platform |
| <a id="at-e2e-009"></a>`AT-E2E-009` — Cross-stage negative matrix | `REQ-E2E-009`, `011` | `CONTROLLED_DISPOSABLE_QUALIFICATION` | Fixed-resource bootstrap, identity/permission, expiry, stop/removal/reboot, cross-Service, trusted-Provider separation, cross-team/system log access, log redaction/size/offline/delete, QM, stale-evidence and unsafe-action cases fail closed |
| <a id="at-e2e-010"></a>`AT-E2E-010` — R0 retirement | `REQ-E2E-010`, `011` | `LIVE_BASELINE_POSITIVE`; destructive/interruption negatives are `AT-E2E-009`/`011` instances | Offline-only deprovision, post-`204` re-read, old-credential rejection, exact `system_uid` set removal, Unit deletion, Unit-owned Node disappearance without standalone Node delete, scoped log/functional cleanup, uncertainty reconciliation, clean local state, unchanged factory and next run unblocked |
| <a id="at-e2e-011"></a>`AT-E2E-011` — Interruption/reconciliation | `REQ-E2E-003`, `010`, `011` | `CONTROLLED_DISPOSABLE_QUALIFICATION` | Every uncertain external mutation is reconciled without blind retry or unsafe cleanup |
| <a id="at-e2e-012"></a>`AT-E2E-012` — Composed presenter workspace | `REQ-E2E-012` | `LIVE_BASELINE_POSITIVE`, `AUDIENCE_PRESENTATION`, human inspection | Exact presenter-Mac profile keeps required native/browser surfaces visible, non-overlapping and readable; shared-header state comes from the same browser read model; team context remains fixed and only the release/version region scrolls with independent per-team restoration; local restoration changes no lifecycle state |

## Verification Traceability

| Requirement | Owner evidence prerequisite | E2E scenarios | Acceptance surface |
| --- | --- | --- | --- |
| `REQ-E2E-001` | Factory, Platform, Brake, Tire candidate evidence | `AT-E2E-001` | Preflight dossier |
| `REQ-E2E-002` | Simulator, Gateway, Aos lifecycle and Demo packages | `AT-E2E-002` | CARLA, Engineering Dashboard, AosCloud |
| `REQ-E2E-003` | Aos lifecycle, all release owners and Demo package | `AT-E2E-003`, `006`, `011` | Software Delivery Dashboard + AosCloud re-read/audit |
| `REQ-E2E-004` | VDP, Gateway and Aos lifecycle packages | `AT-E2E-004` | AosCloud, KUKSA contract evidence, Engineering Dashboard |
| `REQ-E2E-005` | Brake service/Cloud and VDP packages | `AT-E2E-005` | CARLA, Brake Dashboard, AosCloud |
| `REQ-E2E-006` | VDP, Brake service/Cloud and release evidence | `AT-E2E-006` | Both delivery and Brake functional surfaces |
| `REQ-E2E-007` | Gateway, VDP, Brake, Aos and Demo packages | `AT-E2E-007` | Engineering, Software Delivery and Brake Dashboards |
| `REQ-E2E-008` | Tire service/Cloud, Aos, Cross and Demo packages | `AT-E2E-008` | Software Delivery, Tire, Brake and Engineering surfaces |
| `REQ-E2E-009` | All owner security/observability obligations | `AT-E2E-002..009` | Authoritative per-fact surfaces plus controlled negative dossier |
| `REQ-E2E-010` | Aos, Demo, functional Cloud and Simulator packages | `AT-E2E-010`, `011` | AosCloud, empty Function Dashboards and local state inspection |
| `REQ-E2E-011` | Every owner failure/recovery obligation | `AT-E2E-003`, `009`, `010`, `011` | Verbatim external state, explicit orchestration state and separate acceptance verdict |
| `REQ-E2E-012` | Demo Orchestration, Representation Layer and visible-surface ownership | `AT-E2E-012` | Measured presenter-Mac workspace record plus human acceptance |

## Cross-Cutting Constraints

| Concern | Acceptance invariant | Verification |
| --- | --- | --- |
| Authority | Team acceptance, OEM authorization, AosCloud execution and dashboard presentation remain distinct | Role/audit matrix and stage preflight |
| Security | No secret, caller-selected authority or widened permission enters evidence; `CMP-KAC` state is volatile; Provider trust remains explicit; Gateway remains final QM boundary | Contract negatives and `AT-E2E-009` |
| Resources | AosCore alone caps the actual Tire service; Brake/platform remain healthy | `AT-E2E-008` |
| Connectivity | Only vehicle external connectivity is faulted; presenter and in-vehicle paths remain available | `AT-E2E-007` |
| Chronology | Source, local decision, backend receipt and synchronization times remain distinct; no Cloud-duration KPI | Message/evidence inspection |
| Evidence retention | R0 deletes ordinary demo-owned functional history; exactly one sanitized, version-bound current qualification dossier and bounded status remain locally under `.local/qualification/`; candidate replacement is validated and atomic, with no retained dossier history or automatic remote upload | Cleanup, status-schema and atomic-replacement inspection |
| Identity lifetime | Once-issued OEM/SP certificates remain stable; vehicle and runtime-derived identities follow their distinct provisioning/instance/R0 lifecycles | Role preflight, fresh provisioning, IAM/JWT and R0 evidence |
| Human acceptance | Cycle B is executed through reviewed presenter surfaces and observed by a human reviewer; visible/semantic rejection vetoes machine success | Machine verdict plus sanitized `HUMAN_PRESENTER_REHEARSAL_ACCEPTED` or rejection reason |
| Audience usability | The mandatory end-to-end story fits the reviewed 30-minute core narrative inside a 45-minute slot without skipping lifecycle gates; optional drill-down only expands the story | Cycle B presenter rehearsal and human review |
| Destructive safety | Exact preview, authoritative re-read and reconciliation precede deletion/disposal | `AT-E2E-010`, `011` |

## D3 Review Decisions

| Decision | Proposed resolution | Review state |
| --- | --- | --- |
| `E2E-D1` — Package nature | `CR-E2E` is a no-code system-acceptance package; it adds no component, runtime service, product policy or duplicate `UT-*` suite. Any reusable execution, evidence-normalization or verdict logic remains owned and unit-tested by existing `CR-DEMO`; `CR-E2E` defines only the accepted `AT-E2E-*` outcomes and evidence composition | **Confirmed 2026-08-20** |
| `E2E-D2` — Proof modes | Use exactly four D4-026.1 modes: `STATIC_CONFORMANCE`, `CONTROLLED_DISPOSABLE_QUALIFICATION`, `LIVE_BASELINE_POSITIVE` and non-qualifying `AUDIENCE_PRESENTATION`. Run the complete positive story through successful R0 live, including current target/role/digest/evidence preflights before each mutation. Execute interrupted/destructive failure cases, malformed/security negatives and the broad fault matrix as controlled qualification on disposable targets. Stored evidence is valid only for the exact bound baseline, becomes `STALE` on mismatch and never replaces current authoritative preflight | **Confirmed 2026-08-20; exact vocabulary accepted 2026-08-23** |
| `E2E-D3` — One-source execution and update-state policy | Use sequential VU qualification, confirmed detach, canonical reset/new generation and exclusive PU binding, with the reverse handover available for a later release cycle. Before Platform rollout, show the PU as the Domain Controller of the normally moving CARLA vehicle on its current software graph; OEM Release Authority may authorize while it moves, the factory-installed OEM Component Runtime then visibly waits for fresh Safe Stop evidence, the presenter enters Safe Stop, the runtime applies the identical accepted VDP FOTA and readiness is confirmed before driving resumes explicitly. For Brake/Tire QM Service SOTA, the same actor/generation may continue moving without source reset; vehicle control, Gateway/VISS and the independent Engineering Dashboard remain continuous and any Service activation gap is bounded and explicit. PU checks inside formal `CR-E2E` qualification prove the demo solution before presentation and shall not be shown as Production product validation. Never claim AosCloud evaluates physical motion, imply two simultaneous vehicles or implement replay in the first iteration | **Corrected 2026-08-25; runtime enforcement clarified by ADR 0014 on 2026-08-26** |
| `E2E-D4` — Progression and abort | Every stage uses `entry gate -> one bounded action -> authoritative re-read -> exit gate`. Preserve exact Cloud/Unit/source state separately from local `READY/BLOCKED/WAITING/SUBMITTING/UNCERTAIN/RECONCILING/RECOVERY_REQUIRED` orchestration state and `NOT_EVALUATED/PASSED/FAILED/ABORTED` acceptance result. `BLOCKED` submits no mutation; `WAITING` is a known external prerequisite without resubmission; uncertainty forbids blind retry; reconciliation resumes from discovered external state; `RECOVERY_REQUIRED` blocks the next protected action until bounded recovery completes; only a passed exit gate permits progression; VU failure blocks PU promotion; uncertain source cleanup blocks the next binding; and partial R0 preserves records/overlays rather than presenting rollback theatre | **Confirmed 2026-08-21; visible recovery vocabulary synchronized 2026-08-26** |
| `E2E-D5` — Evidence retention | Keep exactly one sanitized, version-bound current dossier at `.local/qualification/current/` only for an explicitly designated formal qualification/acceptance run, plus bounded `.local/qualification/qualification-status.json`; build candidates separately, validate and seal them, and replace current atomically without retaining dossier history or automatically uploading evidence. Successful R0 deletes all ordinary project-owned telemetry, functional results, advisories, dashboard/run state, CARLA run-local evidence, temporary log downloads and the reconciled recovery journal while preserving current dossier/status. A failed/uncertain candidate never replaces current and is deleted after reconciliation; a sanitized incident requires explicit operator action. Baseline mismatch is `STALE`, human rejection is `NOT_QUALIFIED`, and withdrawal requires a new complete qualification | **Confirmed 2026-08-21; exact storage/status/replacement accepted 2026-08-23** |
| `E2E-D6` — Dependency boundary | Preserve existing AosEdge component-to-component and service-to-layer dependency mechanisms as supported platform capabilities. Keep only native AosCloud admission of a SOTA Service against a required FOTA Vehicle Data Platform Component version as explicitly deferred. Until an implementing release is available and qualified, use provider-first ordering, OEM validation and fail-closed service readiness without presenting them as equivalent to Cloud-native admission and without introducing a project-side admission controller | **Confirmed 2026-08-21** |

<a id="open-d4-gates"></a>
## Open Implementation and Qualification Gates

| Gate | Impact | Owner |
| --- | --- | --- |
| Implement and qualify the complete design-reviewed D4-025 atomic-stage, assertion/evidence, Demo Baseline Qualification Dossier, exact parameterized map and verdict-composition framework | Every `AT-E2E-*` verdict | System Acceptance + Demo Solution |
| Exact common-helper request/result transport and authoritative AosCloud publication-reconciliation lookup | Implements accepted D4-010.3 profile/custody/state semantics for `AT-E2E-003`; decision itself is closed | Demo Solution + Platform/Function Team release owners + AosCloud integration |
| Update-state continuity: Platform VDP/KUKSA Safe-Stop readiness plus Brake/Tire QM Service in-motion readiness, unchanged actor/generation/control ownership where applicable and uninterrupted Gateway/VISS evidence | `REQ-E2E-003..008` and `E2E-D3` | Platform + Function Teams + Gateway + Demo Solution |
| Live-qualify D4-015 on both disposable Units: bounded offline mechanism, post-`204` Unit state, retired-credential reconnect, exact `system_uid` set removal, Unit deletion, Unit-owned Node disappearance without a Node-delete call, authorization-masked `404` and uncertain-result reconciliation | `REQ-E2E-010`, `AT-E2E-010` and `REQ-DEMO-013` | AosCloud integration + Demo Solution |
| D4 values still open in every accepted owner package | Blocks its dependent acceptance scenario | Respective package owner |
| Exact destructive/negative-vector allocation that cannot revoke, replace or corrupt shared stable OEM/SP credentials | `AT-E2E-009..011` inside the accepted D4-026.2 identity boundary | AosCloud/OEM administration + Demo Solution |
| Freeze the implementation-characterized VDP/KUKSA Safe-Stop readiness maximum and separate Brake/Tire in-motion Service readiness maxima before formal qualification | `AT-E2E-003..008`; no guessed performance claim | Platform/Function Teams + Gateway + Demo Solution |

## Version 0.8 Acceptance and Delta

Version 0.8 was accepted as the current D3 design baseline on 2026-08-27. The
acceptance confirms the six decisions above, the complete stage and proof
model, and the presenter-workspace cascade through D4-026.20. The gates in the
preceding section remain implementation and live-qualification prerequisites;
they do not reopen the accepted system behavior and they are not waived by
this acceptance.

The previous package was accepted for D3 design review on 2026-08-21 after
reviewers confirmed that:

1. all six review decisions are confirmed;
2. every one of the 62 active system requirements is allocated without
   silently reactivating a retired or deferred requirement;
3. every stage identifies its entry-gate obligations, observable pass/fail
   exit and safe abort/reconciliation boundary; exact machine-readable
   assertions, thresholds and tolerances remain D4 gates;
4. live, controlled-qualification, documentary and deferred proofs are clearly
   distinguished;
5. no E2E scenario duplicates component unit policy or creates a runtime
   dependency, desired-state database, resource manager or history archive;
6. VU always precedes identical PU promotion and one live source is bound
   exclusively and truthfully;
7. external/destructive actions remain blocked until D4 qualification and
   explicit authorization; and
8. the documentation quality gate passes.

Version 0.5 was the review candidate that replaced retired authorization
interfaces, added `CMP-KAC` bootstrap/reboot/removal proof and recorded the
trusted OEM Provider assumption. Version 0.6 synchronizes the package with
`SYS-REL-012`, D4-026.17, `IF-DEMO-002`, the complete D4-026.1–.17 baseline,
the accepted visible recovery vocabulary and composed presenter-workspace
acceptance. Version 0.7 adds the right-hand global Demo Lifecycle page and
bounded Qualification Status under D4-026.18. Stage order, product behavior,
authority and lifecycle semantics remain unchanged.

Version 0.8 synchronizes the existing composed-workspace acceptance with
D4-026.19/.20, Interaction Specification 2.5 and the accepted clickable review
mockup. `REQ-E2E-012` and `AT-E2E-012` now qualify fixed, fully readable team
context, version-only scrolling and independent Platform/Brake/Tire
release-scroll restoration on the presenter Mac, consistent icon vocabulary
in browser-owned surfaces, and a native terminal boundary with no HTML icon
injection. Product behavior, stage order, authority, interfaces and pass/fail
semantics are unchanged. This acceptance does not authorize implementation,
signing, Cloud calls, VM operations, provisioning, deployment, CARLA control,
retirement or data deletion.

## Change Rules

- Editorial clarification preserves stable `REQ-E2E-*` and `AT-E2E-*` IDs.
- A changed authority, component, interface, lifecycle, data direction or
  claim follows the Level-C architecture cascade before this package changes.
- A changed stage behavior or proof mode inside accepted architecture follows
  the Level-B cascade and updates the scenario, flows, parent requirements,
  owner packages and acceptance mapping together.
- An owner package may strengthen its own evidence without changing E2E IDs
  when the accepted system claim, stage order and pass/fail semantics remain
  unchanged.
