<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# End-to-End Acceptance Requirements

- Status: D3 review candidate
- Package: [`CR-E2E`](../component-decomposition-and-interface-register.md#cr-e2e)
- Version: 0.5
- Prepared: 2026-08-21
- Owner: System Acceptance with Platform, Function, Gateway and Demo Solution teams
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Previous accepted package: Version 0.4
- Accepted D4 source decision: [D4-005 Exclusive Live-Source Assignment](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Accepted D4 VISS decision: [D4-006 VISS Trust and Telemetry Profile](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Accepted D4 advisory decision: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Accepted D4 publication decision: [D4-010.3 Artifact Publication Credential Profile](../../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)
- Implementation, signing, Cloud, Unit, VM or CARLA mutation authorized: no

## Purpose

This package defines how the complete accepted demonstration is judged as one
system. It composes the already reviewed component, contract and integration
evidence into the canonical
`M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` acceptance sequence on
the Validation and Demonstration Units.

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
- Validation Unit qualification before identical Demonstration Unit promotion;
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

### Out of scope

- implementing or repairing any component during an acceptance run;
- source editing, compilation, image/container build, packaging, model training
  or full qualification execution during the presentation;
- a project admission controller, resource manager, identity provider, log
  archive, replay component or second lifecycle database;
- simultaneous VU and DU CARLA vehicles, production fleet/Fleet Operator,
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
| Validation and Demonstration lanes | AosCloud/OEM + Demo Solution | Fresh Units, exact disjoint Unit Set membership and current authoritative state | Every Unit-affecting action is blocked |
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
| [`IF-VEH-001`–`006`](../component-decomposition-and-interface-register.md#if-veh-001) | CARLA ↔ Gateway/VISS/Dashboard | Vehicle profile, applied control, VSS telemetry, source generation and factual state | Safe stop, unavailable/degraded state or stage block | CARLA/Gateway actual state |
| [`IF-DATA-001`–`002`](../component-decomposition-and-interface-register.md#if-data-001), [`IF-TIRE-001`](../component-decomposition-and-interface-register.md#if-tire-001) | VDP/KUKSA → services | Versioned read contracts and data quality | Service not ready or `NOT_EVALUATED`; no fabricated normal state | Installed VDP contract and KUKSA |
| [`IF-ADV-001`–`005`](../component-decomposition-and-interface-register.md#if-adv-001), [`IF-TIRE-002`](../component-decomposition-and-interface-register.md#if-tire-002) | Services → KUKSA/VDP/VISS/Gateway | Typed QM maintenance advisories and factual status | Fail closed; Gateway remains final authority | IAM/KUKSA, VDP defense in depth and Gateway policy |
| [`IF-AUTH-007`–`010`](../component-decomposition-and-interface-register.md#if-auth-007) | Services ↔ `CMP-KAC` ↔ Aos IAM/KUKSA security substrate | Fixed-resource bootstrap, private volatile scoped JWT and verifier/signer lifecycle | No credential/readiness; no cached/static fallback | Aos IAM result plus per-Unit platform trust; Provider remains a separate trusted OEM integration |
| [`IF-FUNC-001`–`002`](../component-decomposition-and-interface-register.md#if-func-001), [`IF-TIRE-003`–`004`](../component-decomposition-and-interface-register.md#if-tire-003) | Services ↔ functional Cloud products | Bounded, versioned, idempotent results and exact cleanup | Queue/degraded/loss state is explicit | Owning Function Team contract |
| [`IF-LC-001`–`010`](../component-decomposition-and-interface-register.md#if-lc-001) | Teams/Dashboard/AosCloud/AosCore | Publication, approval, desired/actual state, targeting, runtime and quota enforcement | Mutation blocked or reconciled from authoritative state | Owning team decision, OEM identity and AosCloud/AosCore state |
| [`IF-OBS-001`](../component-decomposition-and-interface-register.md#if-obs-001) | Dashboard ↔ AosCloud | Native log request/status/result/file | Explicit unavailable/failed/expired state; no second archive | AosCloud-retained state |
| [`IF-DEMO-001`](../component-decomposition-and-interface-register.md#if-demo-001) | Orchestrator → local actors | Session, VM/source lifecycle, faults and safe retirement | Partial/uncertain state blocks progression | Local session manifest plus authoritative external state |

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
| Orchestration state | `READY`, `BLOCKED`, `SUBMITTING`, `UNCERTAIN`, `RECONCILING` | Whether `CR-DEMO` may perform or continue one bounded action; this is local control state and is never presented as an AosCloud state |
| Acceptance result | `NOT_EVALUATED`, `PASSED`, `FAILED`, `ABORTED` | The verdict for one entry-gate/action/re-read/exit-gate attempt; it is assigned only from the accepted evidence rule and is never written back as Cloud lifecycle state |

Every stage follows `entry gate -> one bounded action -> authoritative re-read
-> exit gate`. `BLOCKED` means that no mutation was submitted. A timeout,
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
| Explicit formal qualification or acceptance run | One sanitized, version-bound dossier containing an evidence ID, exact subject/artifact and metadata digests, AosEdge/API release, configuration digest, verification time, verdict, claim boundary, cleanup result and references to authoritative Cloud audit objects | Raw telemetry and functional payloads, raw secret-bearing responses, reusable credentials, unredacted Unit identities, complete Cloud-state copies, temporary downloads and replayable run history |
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
| [Factory and candidate preflight (`REQ-E2E-001`)](#req-e2e-001) | Admit only the exact clean factory artifact, fresh overlays and prepared candidates | Inspection, Integration, End-to-end | Draft |
| [Provisioned baseline and source truth (`REQ-E2E-002`)](#req-e2e-002) | Establish fresh VU/DU identities, disjoint sets and one honest live source at G0 | Integration, End-to-end | Draft |
| [Authoritative release governance (`REQ-E2E-003`)](#req-e2e-003) | Prove team decision, OEM authorization, exact recipients and validation-first identical promotion | Contract, Integration, Audit, End-to-end | Draft |
| [G1 platform data capability (`REQ-E2E-004`)](#req-e2e-004) | Prove VDP v1 delivery and the first honest VISS-to-KUKSA data path | Integration, End-to-end | Draft |
| [G2 bounded Brake Health acquisition (`REQ-E2E-005`)](#req-e2e-005) | Prove independent SOTA 1 and bounded v1 braking-window delivery | Integration, End-to-end | Draft |
| [G3 independent platform/service evolution (`REQ-E2E-006`)](#req-e2e-006) | Prove backward-compatible VDP v2 plus local synthetic Brake assessment and derived-only Cloud output | Integration, End-to-end | Draft |
| [G4 advisory and external-connectivity continuity (`REQ-E2E-007`)](#req-e2e-007) | Prove typed QM advisory, local offline operation and same-Unit convergence | Integration, Analysis, End-to-end | Draft |
| [T1 peer service and tenant isolation (`REQ-E2E-008`)](#req-e2e-008) | Prove independent Tire SOTA 2 and AosCore CPU-quota isolation from Brake | Integration, End-to-end | Draft |
| [Cross-stage security and truthful evidence (`REQ-E2E-009`)](#req-e2e-009) | Preserve least privilege, containment, correlation, chronology, native logs and honest claim state | Contract, Integration, Analysis, End-to-end | Draft |
| [R0 retirement and next-run readiness (`REQ-E2E-010`)](#req-e2e-010) | Retire both identities and run data, reset local state and preserve the immutable factory source | Integration, Analysis, End-to-end | Draft |
| [Bounded abort, recovery and repeatability (`REQ-E2E-011`)](#req-e2e-011) | Stop safely on uncertain evidence and repeat the accepted sequence without hidden state reuse | Integration, Analysis, End-to-end | Draft |

## Detailed Requirements

<a id="req-e2e-001"></a>
### Factory and candidate preflight

- Statement: Acceptance shall start only from the exact clean OEM Demo Factory Image, two fresh role-bound overlays and the complete set of prebuilt, tested and content-frozen VDP, Brake and Tire candidates whose versions, artifact/metadata digests, compatibility and secret-negative evidence match the accepted baseline.
- Parents: [`SYS-MFG-001`–`003`](../system-requirements-and-traceability.md#sys-mfg-001), [`SYS-REL-001`](../system-requirements-and-traceability.md#sys-rel-001) and [`SYS-RET-005`](../system-requirements-and-traceability.md#sys-ret-005)
- Flows: [`AF-M0-LC`](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc), [`AF-M0-OB`](../../architecture/demo-scenario-architecture-flows.md#af-m0-ob), [`AF-M0-FR`](../../architecture/demo-scenario-architecture-flows.md#af-m0-fr)
- Acceptance: any digest, compatibility, identity-cleanliness, overlay-freshness or secret-negative mismatch blocks `M1`; no presentation-time build fallback exists.

<a id="req-e2e-002"></a>
### Provisioned baseline and source truth

- Statement: `M1/G0` shall prove one unique Unit/Main Node and per-Unit VISS client identity per overlay, exact disjoint Validation/Demonstration Unit Set membership, current online/graph state, a healthy empty VDP slot, a working authenticated CARLA/Gateway/VISS/Engineering Dashboard path and one exclusive selected-Unit live-source assignment. The audience sees Validation Vehicle and Demonstration Vehicle, exactly one `CURRENT VEHICLE`, and a plain `Continue with Demonstration Vehicle` transition; technical details preserve exact Unit/source/certificate-fingerprint evidence without presenting host assignment plumbing as in-vehicle behavior or implying two simultaneous live vehicles.
- Parents: [`SYS-ID-001`–`004`](../system-requirements-and-traceability.md#sys-id-001), [`SYS-SRC-001`–`004`](../system-requirements-and-traceability.md#sys-src-001), [`SYS-CTRL-001`–`003`](../system-requirements-and-traceability.md#sys-ctrl-001), [`SYS-VDP-001`](../system-requirements-and-traceability.md#sys-vdp-001)
- Flows: `AF-M1-*`, `AF-G0-*`, [`AF-X-SOURCE`](../../architecture/demo-scenario-architecture-flows.md#af-x-source), [`AF-X-DRIVE`](../../architecture/demo-scenario-architecture-flows.md#af-x-drive)
- Executable contracts: [Exclusive Live-Source Assignment 1.0.0](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json) and [VISS Trust and Telemetry Profile 1.0.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Acceptance: partial provisioning, crossed/stale Unit membership, ambiguous source ownership, failed canonical reset or non-empty feature state blocks the next stage.

<a id="req-e2e-003"></a>
### Authoritative release governance

- Statement: Every FOTA/SOTA stage shall bind the exact candidate and metadata, effective recipients, validation evidence, owning-team acceptance and active authorized OEM role. Technical publication shall use only the release surface's fixed D4-010.3 profile — `platform-oem`, `brake-sp1` or `tire-sp2` — and shall reach `PUBLISHED` only after independent AosCloud re-read; ambiguity shall enter `UNCERTAIN` and shall not be blindly retried. AosCloud shall separately record and execute the explicit OEM decision, and the identical accepted digest shall reach DU only after VU acceptance.
- Parents: [`SYS-REL-002`–`011`](../system-requirements-and-traceability.md#sys-rel-002) and [`SYS-OBS-002`](../system-requirements-and-traceability.md#sys-obs-002), [`SYS-OBS-006`](../system-requirements-and-traceability.md#sys-obs-006)
- Flows: [`AF-X-RELEASE`](../../architecture/demo-scenario-architecture-flows.md#af-x-release), all stage lifecycle flows
- Acceptance: wrong publication profile/candidate/type/path/URL, local credential custody failure, missing independent publication re-read, stale/unprovable recipients, wrong OEM role, missing owner, changed digest, incomplete/stale evidence or post-action mismatch blocks progression. Technical publication never counts as deployment approval. Existing AosEdge component-to-component and service-to-layer dependency mechanisms remain accepted platform capabilities. Only native Cloud admission of a SOTA service against a required FOTA Vehicle Data Platform Component version remains visibly deferred until an implementing release is qualified; no local substitute is accepted.

<a id="req-e2e-004"></a>
### G1 platform data capability

- Statement: The accepted VDP v1 FOTA candidate shall be validated on VU and promoted identically to DU, become ready only with its accepted VISS contract and publish the exact v1 read-only signal subset into KUKSA with factual quality, freshness, availability and provenance.
- Parents: [`SYS-VDP-001`](../system-requirements-and-traceability.md#sys-vdp-001), [`SYS-VDP-002`](../system-requirements-and-traceability.md#sys-vdp-002), [`SYS-VDP-005`](../system-requirements-and-traceability.md#sys-vdp-005), [`SYS-REL-004`](../system-requirements-and-traceability.md#sys-rel-004)
- Flows: `AF-G1-*`, `AF-X-RELEASE`, `AF-X-SOURCE`
- Executable VISS input: [VISS Trust and Telemetry Profile 1.0.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Acceptance: a non-selected or unauthenticated Unit is rejected; missing/stale/malformed source data becomes atomically unavailable and recovers only from a complete valid snapshot; no service is required at G1 and no fabricated normal value is accepted.

<a id="req-e2e-005"></a>
### G2 bounded Brake Health acquisition

- Statement: Function Team 1 shall independently publish and approve Brake Health Service v1, validate it on VU and promote identical bytes to DU, where one deterministic braking event produces a bounded pre/active/post window, ordered chunks/completion, idempotent backend reconstruction and factual dashboard evidence.
- Parents: [`SYS-BHS-005`](../system-requirements-and-traceability.md#sys-bhs-005), [`SYS-BHS-004`](../system-requirements-and-traceability.md#sys-bhs-004), [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001), [`SYS-REL-003`](../system-requirements-and-traceability.md#sys-rel-003)
- Flows: `AF-G2-*`, `AF-X-AUTH`, `AF-X-OBS`
- Acceptance: no trigger produces no window; overflow/duplicate/transport failure remains bounded and explicit; continuous unrestricted raw streaming is not accepted.

<a id="req-e2e-006"></a>
### G3 independent platform and service evolution

- Statement: VDP v2 shall be a backward-compatible superset of v1, and Brake Health Service v2 shall use its prepared synthetic model for deterministic local assessment while normal Cloud output changes from v1 windows to bounded derived assessments/events. Platform and Function Team decisions remain independently evidenced before joint promotion.
- Parents: [`SYS-VDP-003`](../system-requirements-and-traceability.md#sys-vdp-003), [`SYS-BHS-002`](../system-requirements-and-traceability.md#sys-bhs-002), [`SYS-BHS-006`](../system-requirements-and-traceability.md#sys-bhs-006), [`SYS-REL-007`–`009`](../system-requirements-and-traceability.md#sys-rel-007)
- Flows: `AF-G3-LC`, `AF-G3-RT`, `AF-G3-OB`, `AF-G3-FR`
- Acceptance: the existing v1 consumer contract remains valid, model/result identity is visible, normal v2 behavior does not emit v1 high-detail windows, and either owner's failed acceptance blocks the combined graph.

<a id="req-e2e-007"></a>
### G4 advisory and external-connectivity continuity

- Statement: VDP v3 and Brake Health Service v3 shall complete the exact D4-008 Request/Status round trip through KUKSA, VDP, VISS and the authoritative Gateway, including application evidence distinct from Set success, explicit clear, auto-expiry and stale/replay/cross-target/motion-write rejection. One atomic DU external-connectivity fault shall interrupt AosCloud and all installed functional-backend paths together while local assessment/advisory continues, then reconnect the same Unit and synchronize bounded messages idempotently without reinstall or restart.
- Parents: [`SYS-VDP-004`](../system-requirements-and-traceability.md#sys-vdp-004), [`SYS-BHS-003`–`004`](../system-requirements-and-traceability.md#sys-bhs-003), [`SYS-SEC-003`](../system-requirements-and-traceability.md#sys-sec-003), [`SYS-SEC-007`](../system-requirements-and-traceability.md#sys-sec-007), [`SYS-OBS-007`](../system-requirements-and-traceability.md#sys-obs-007)
- Flows: `AF-G4-*`, [`AF-X-QM`](../../architecture/demo-scenario-architecture-flows.md#af-x-qm), [`AF-X-OFFLINE`](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Acceptance: presenter-to-AosCloud and in-vehicle connectivity remain available; only matching Gateway `APPLIED`/`CLEARED` is success, unauthorized/arbitrary/replay/motion writes fail closed, lease expiry is factual, and original/Gateway/synchronization times remain distinct.

<a id="req-e2e-008"></a>
### T1 peer service and tenant isolation

- Statement: Function Team 2 shall independently deliver one Tire Health v1.0 candidate against accepted VDP v3, prove local persistent condition estimation, bounded result/advisory behavior and independent backend/dashboard state, then run the prepared Tire CPU load to its approved quota while AosCore caps it and Brake processes the deterministic event without restart or platform degradation.
- Parents: [`SYS-TIRE-001`–`006`](../system-requirements-and-traceability.md#sys-tire-001), [`SYS-RES-001`](../system-requirements-and-traceability.md#sys-res-001)
- Flows: `AF-TIRE-LC`, `AF-TIRE-RT`, `AF-TIRE-OB`, `AF-TIRE-FR`, [`AF-TIRE-RES`](../../architecture/demo-scenario-architecture-flows.md#af-tire-res)
- Acceptance: Tire and Brake identities, permissions, quotas, SOTA lifecycles and products remain distinct; Mac-local backends and aggregate multi-service-per-provider quota enforcement remain outside the AosCore claim.

<a id="req-e2e-009"></a>
### Cross-stage security and truthful evidence

- Statement: Across all stages, accepted evidence shall prove native Aos-derived least-privilege KUKSA authority through fixed-resource `CMP-KAC` bootstrap, private volatile short-lived JWT delivery, protected per-Unit signing, stop/removal/reboot cleanup, trusted OEM Provider separation, Gateway-final QM containment, native scoped logs, exact run/Unit/source correlation and distinct source/local/receipt/synchronization chronology without secrets, false retention, false latency or widened claims. The first demo shall not claim dynamic Provider IAM/JWT or malicious/substituted-Provider containment.
- Parents: [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001), [`SYS-SEC-003`](../system-requirements-and-traceability.md#sys-sec-003), [`SYS-SEC-004`](../system-requirements-and-traceability.md#sys-sec-004), [`SYS-SEC-007`](../system-requirements-and-traceability.md#sys-sec-007), [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008), [`SYS-OBS-001`–`006`](../system-requirements-and-traceability.md#sys-obs-001), [`SYS-TIM-002`](../system-requirements-and-traceability.md#sys-tim-002)
- Flows: `AF-X-AUTH`, `AF-X-QM`, `AF-X-OBS`, `AF-X-SOURCE`
- Acceptance: invalid/stale/cross-Service identities, caller-selected authority, expiry, permission removal and unsafe advisory requests fail without side effects; reboot, Service stop/unregistration and R0 remove volatile authorization state; trusted Provider evidence is separate and bounded to the declared first-demo assumption; dashboard evidence is authoritative or explicitly unavailable/stale/deferred.

<a id="req-e2e-010"></a>
### R0 retirement and next-run readiness

- Statement: After the final stage, R0 shall capture the final online state, make both Units authoritatively `Offline`, deprovision each through the qualified offline-only Cloud operation, reconcile the no-content result, prove old credentials cannot return either Unit `Online`, then complete qualified VM stop, Unit Set reconciliation, Unit/Node deletion, current-run functional-data deletion, CARLA/Gateway reset and overlay disposal while retaining the unchanged Factory Image digest for two fresh next-run overlays and identities.
- Parents: [`SYS-RET-001`–`006`](../system-requirements-and-traceability.md#sys-ret-001), [`SYS-ID-004`](../system-requirements-and-traceability.md#sys-id-004)
- Flows: `AF-R0-LC`, `AF-R0-OB`, `AF-R0-FR`
- Acceptance: uncertain deprovision/delete/membership state preserves records and overlays for reconciliation and blocks the next run; R0 is never labelled an in-field OTA rollback or fleet policy.

<a id="req-e2e-011"></a>
### Bounded abort, recovery and repeatability

- Statement: Every stage shall have a defined entry gate, one bounded action, authoritative re-read, exit gate and safe abort/reconciliation boundary. It shall preserve exact external source state separately from local orchestration state and acceptance result. A missing, stale, failed, partial or ambiguous prerequisite shall prevent the next irreversible action, and a new accepted run shall reproduce the same stage outcomes from the unchanged Factory Image and new identities without reusing old target, source or functional-data assumptions.
- Parents: [`SYS-ID-002`](../system-requirements-and-traceability.md#sys-id-002), [`SYS-REL-002`](../system-requirements-and-traceability.md#sys-rel-002), [`SYS-OBS-004`](../system-requirements-and-traceability.md#sys-obs-004), [`SYS-RET-006`](../system-requirements-and-traceability.md#sys-ret-006)
- Flows: every `*-FR` flow plus `AF-X-RELEASE` and `AF-X-SOURCE`
- Acceptance: `BLOCKED` submits no mutation; `UNCERTAIN` never triggers a blind retry; `RECONCILING` requires a fresh authoritative read; and only a passed exit gate permits the next stage. `PASSED`, `FAILED` and `ABORTED` remain acceptance verdicts rather than claimed AosCloud states. No automatic approval, ambiguous continuation or destructive cleanup is accepted. Repeatability is proven by a qualified acceptance run, not by retaining ordinary demo-run history.

## System Requirement Coverage Allocation

| Active system-requirement family | E2E allocation |
| --- | --- |
| `SYS-MFG-001..003` | `REQ-E2E-001`, `002` |
| `SYS-ID-001..004` | `REQ-E2E-002`, `010`, `011` |
| `SYS-SRC-001..004` | `REQ-E2E-002`, `009`, `011` |
| `SYS-CTRL-001..003` | `REQ-E2E-002`, `009` |
| `SYS-REL-001..011` | `REQ-E2E-001`, `003`, `004..008`, `011`; `SYS-REL-006` remains deferred |
| `SYS-VDP-001..005` | `REQ-E2E-002`, `004`, `006`, `007`, `008` |
| active Brake requirements `SYS-BHS-002..006` excluding retired `SYS-BHS-001` | `REQ-E2E-005`, `006`, `007` |
| `SYS-TIRE-001..006` | `REQ-E2E-008` |
| active Security requirements `SYS-SEC-001`, `003`, `004`, `007`, `008` | `REQ-E2E-005`, `007`, `008`, `009` |
| `SYS-OBS-001..007` | `REQ-E2E-002`, `003`, `007`, `009`, `011` |
| `SYS-TIM-002` | `REQ-E2E-007`, `009` |
| `SYS-RES-001` | `REQ-E2E-008` |
| `SYS-RET-001..006` | `REQ-E2E-001`, `010`, `011` |

Retired `SYS-BHS-001`, `SYS-EVT-001..005`, `SYS-SEC-002` and `SYS-TIM-001`
remain linkable historical records and are not active acceptance inputs.

## End-to-End Acceptance Scenarios

| Acceptance scenario | Main requirements | Mode | Required outcome |
| --- | --- | --- | --- |
| <a id="at-e2e-001"></a>`AT-E2E-001` — M0 preflight | `REQ-E2E-001` | Controlled qualification + live inspection | Exact clean factory/candidate identities and two fresh overlays; mismatch blocks |
| <a id="at-e2e-002"></a>`AT-E2E-002` — M1/G0 baseline | `REQ-E2E-002`, `009` | Live demo | Fresh identities/sets, empty feature graph and one honest working vehicle source |
| <a id="at-e2e-003"></a>`AT-E2E-003` — Common release gate | `REQ-E2E-003`, `011` | Live positive + controlled negatives | Exact fixed publication profile/candidate/digests, independent Cloud publication re-read, exact recipients/roles/evidence, separate OEM approval, VU first, identical DU promotion and deferred feature labelled honestly |
| <a id="at-e2e-004"></a>`AT-E2E-004` — G1 platform capability | `REQ-E2E-004` | Live demo | VDP v1 data reaches KUKSA with factual quality and accepted graph state |
| <a id="at-e2e-005"></a>`AT-E2E-005` — G2 Brake v1 | `REQ-E2E-005` | Live demo | Bounded event window reaches Function Team 1 product independently |
| <a id="at-e2e-006"></a>`AT-E2E-006` — G3 joint evolution | `REQ-E2E-003`, `006` | Live demo + controlled compatibility negatives | Backward-compatible VDP v2 and deterministic derived-only Brake v2 behavior |
| <a id="at-e2e-007"></a>`AT-E2E-007` — G4 advisory/offline | `REQ-E2E-007`, `009` | Live demo | Typed advisory, atomic external disconnect, local continuity and same-Unit convergence |
| <a id="at-e2e-008"></a>`AT-E2E-008` — T1 peer/isolation | `REQ-E2E-008`, `009` | Live demo | Independent Tire SOTA 2 plus AosCore cap with unaffected Brake/platform |
| <a id="at-e2e-009"></a>`AT-E2E-009` — Cross-stage negative matrix | `REQ-E2E-009`, `011` | Controlled qualification | Fixed-resource bootstrap, identity/permission, expiry, stop/removal/reboot, cross-Service, trusted-Provider separation, QM, stale-evidence and unsafe-action cases fail closed |
| <a id="at-e2e-010"></a>`AT-E2E-010` — R0 retirement | `REQ-E2E-010`, `011` | Live positive retirement | Cloud identities retired, functional/local state clean, factory unchanged, next run unblocked |
| <a id="at-e2e-011"></a>`AT-E2E-011` — Interruption/reconciliation | `REQ-E2E-003`, `010`, `011` | Disposable controlled qualification | Every uncertain external mutation is reconciled without blind retry or unsafe cleanup |

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

## Cross-Cutting Constraints

| Concern | Acceptance invariant | Verification |
| --- | --- | --- |
| Authority | Team acceptance, OEM authorization, AosCloud execution and dashboard presentation remain distinct | Role/audit matrix and stage preflight |
| Security | No secret, caller-selected authority or widened permission enters evidence; `CMP-KAC` state is volatile; Provider trust remains explicit; Gateway remains final QM boundary | Contract negatives and `AT-E2E-009` |
| Resources | AosCore alone caps the actual Tire service; Brake/platform remain healthy | `AT-E2E-008` |
| Connectivity | Only vehicle external connectivity is faulted; presenter and in-vehicle paths remain available | `AT-E2E-007` |
| Chronology | Source, local decision, backend receipt and synchronization times remain distinct; no Cloud-duration KPI | Message/evidence inspection |
| Evidence retention | R0 deletes ordinary demo-owned functional history; retained qualification evidence is sanitized, version-bound proof rather than a replayable demo-run database | Cleanup plus dossier inspection |
| Destructive safety | Exact preview, authoritative re-read and reconciliation precede deletion/disposal | `AT-E2E-010`, `011` |

## D3 Review Decisions

| Decision | Proposed resolution | Review state |
| --- | --- | --- |
| `E2E-D1` — Package nature | `CR-E2E` is a no-code system-acceptance package; it adds no component, runtime service, product policy or duplicate `UT-*` suite. Any reusable execution, evidence-normalization or verdict logic remains owned and unit-tested by existing `CR-DEMO`; `CR-E2E` defines only the accepted `AT-E2E-*` outcomes and evidence composition | **Confirmed 2026-08-20** |
| `E2E-D2` — Proof modes | Run the complete positive story through successful R0 live, including current target/role/digest/evidence preflights before each mutation. Execute interrupted/destructive failure cases, malformed/security negatives and the broad fault matrix as controlled qualification on disposable targets. Stored evidence is valid only for the exact subject digest, AosEdge release and configuration, becomes `STALE` on mismatch and never replaces current authoritative preflight | **Confirmed 2026-08-20** |
| `E2E-D3` — One-source execution and in-motion update | Use sequential VU qualification, confirmed detach, canonical reset/new generation and then exclusive DU binding. Before promotion, prove the DU is the Domain Controller of the normally moving CARLA vehicle on its current software graph; promote the identical accepted QM VDP/service candidate while that same vehicle continues moving, without safe stop, actor replacement, reset or generation change. Vehicle control, Gateway/VISS and the independent Engineering Dashboard must remain continuous; a VDP/KUKSA/service activation gap may appear only as bounded explicit `UNAVAILABLE/NOT_READY` and must recover automatically. The claim applies only to the qualified QM graph, not arbitrary automotive FOTA. Never imply two simultaneous vehicles or implement replay in the first iteration | **Confirmed 2026-08-20** |
| `E2E-D4` — Progression and abort | Every stage uses `entry gate -> one bounded action -> authoritative re-read -> exit gate`. Preserve exact Cloud/Unit/source state separately from local `READY/BLOCKED/SUBMITTING/UNCERTAIN/RECONCILING` orchestration state and `NOT_EVALUATED/PASSED/FAILED/ABORTED` acceptance result. `BLOCKED` submits no mutation; uncertainty forbids blind retry; reconciliation resumes from the discovered external state; only a passed exit gate permits progression; VU failure blocks DU promotion; uncertain source cleanup blocks the next binding; and partial R0 preserves records/overlays rather than presenting rollback theatre | **Confirmed 2026-08-21** |
| `E2E-D5` — Evidence retention | Keep one sanitized, version-bound dossier only for an explicitly designated formal qualification/acceptance run, containing evidence identity, exact baseline binding, verdict, claim boundary, cleanup proof and references to authoritative AosCloud audit objects without copying Cloud authority or raw payloads. Successful R0 deletes all ordinary project-owned telemetry, functional results, advisories, dashboard/run state, CARLA run-local evidence, temporary log downloads and the reconciled recovery journal. A failed/uncertain operation retains only a minimal redacted journal until reconciliation; a sanitized incident dossier requires an explicit operator decision | **Confirmed 2026-08-21** |
| `E2E-D6` — Dependency boundary | Preserve existing AosEdge component-to-component and service-to-layer dependency mechanisms as supported platform capabilities. Keep only native AosCloud admission of a SOTA Service against a required FOTA Vehicle Data Platform Component version as explicitly deferred. Until an implementing release is available and qualified, use provider-first ordering, OEM validation and fail-closed service readiness without presenting them as equivalent to Cloud-native admission and without introducing a project-side admission controller | **Confirmed 2026-08-21** |

## Open D4 Gates

| Gate | Impact | Owner |
| --- | --- | --- |
| Exact stage entry/exit assertions and machine-readable evidence dossier schema | Every `AT-E2E-*` verdict | System Acceptance + Demo Solution |
| Exact common-helper request/result transport and authoritative AosCloud publication-reconciliation lookup | Implements accepted D4-010.3 profile/custody/state semantics for `AT-E2E-003`; decision itself is closed | Demo Solution + Platform/Function Team release owners + AosCloud integration |
| In-motion VDP/service update continuity: allowed readiness gap, recovery timeout, unchanged actor/generation/control ownership and uninterrupted Gateway/VISS evidence | `REQ-E2E-003..008` and `E2E-D3` | Platform + Function Teams + Gateway + Demo Solution |
| Qualify the bounded offline mechanism, authoritative post-204 state, retired-credential reconnect test and exact stop/deprovision/delete order required by the corrected offline-only R0 design | `REQ-E2E-010`, `AT-E2E-010` and `REQ-DEMO-013` | AosCloud integration + Demo Solution |
| Exact division between live audience steps and controlled qualification evidence | Presentation length, safety and repeatability | Demo owner + all engineering owners |
| D4 values still open in every accepted owner package | Blocks its dependent acceptance scenario | Respective package owner |
| Qualification environment identities, disposable Units and destructive-test policy | `AT-E2E-009..011` | AosCloud/OEM administration + Demo Solution |
| Minimum repeatability count and allowed deterministic tolerance per stage | Final acceptance confidence | System Acceptance + Simulator/Function teams |
| Sanitized qualification dossier retention/location and confidential-evidence handling | Auditability without demo-run history or secret leakage | System Acceptance + Security |
| Final presenter duration and optional-step policy | Which accepted proofs fit one audience session without weakening claims | Demo owner |

## Package Acceptance and Version 0.5 Delta

The package was accepted for D3 design review on 2026-08-21 after reviewers
confirmed that:

1. all six review decisions are confirmed;
2. every one of the 61 active system requirements is allocated without
   silently reactivating a retired or deferred requirement;
3. every stage identifies its entry-gate obligations, observable pass/fail
   exit and safe abort/reconciliation boundary; exact machine-readable
   assertions, thresholds and tolerances remain D4 gates;
4. live, controlled-qualification, documentary and deferred proofs are clearly
   distinguished;
5. no E2E scenario duplicates component unit policy or creates a runtime
   dependency, desired-state database, resource manager or history archive;
6. VU always precedes identical DU promotion and one live source is bound
   exclusively and truthfully;
7. external/destructive actions remain blocked until D4 qualification and
   explicit authorization; and
8. the documentation quality gate passes.

Version 0.5 is a review candidate that replaces retired authorization
interfaces, adds `CMP-KAC` bootstrap/reboot/removal proof and records the
trusted OEM Provider assumption. Stage order and functional acceptance claims
are unchanged. D3 acceptance authorizes only detailed D4 acceptance-contract design. It
will not authorize implementation, signing, Cloud calls, VM operations,
provisioning, deployment, CARLA control, retirement or data deletion.

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
