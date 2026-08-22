<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Aos Lifecycle Component Requirements

- Status: D3 review candidate
- Package: [`CR-AOS`](../component-decomposition-and-interface-register.md#cr-aos)
- Version: 0.3
- Prepared: 2026-08-21
- Owner: AosEdge Platform integration / OEM lifecycle qualification
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Accepted architecture decisions: [ADR 0004](../../architecture/decisions/0004-single-main-node-for-aos1.md), [ADR 0009](../../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md), [ADR 0011](../../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md), [ADR 0012](../../architecture/decisions/0012-authorize-running-workloads-not-software-artifacts.md) and [ADR 0013](../../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md)
- Previous accepted package: Version 0.2
- Accepted D4 compatibility input: [D4-007 VDP Compatibility Profile](../../../contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json)
- Accepted D4 publication input: [D4-010.3 Artifact Publication Credential Profile](../../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)

## Purpose

This package defines the AosCore and AosCloud lifecycle behavior that makes the
manufacturing-to-retirement demonstration possible. It covers unique Unit and
Main Node provisioning, authoritative desired and reported actual state,
artifact verification, validation and campaign execution, recorded
OEM-authorized approvals, dependency and rollback behavior, native operational
logs, chronology and qualified retirement.

The package does not make engineering release decisions for the Platform Team
or either Function Team. It does not make the Software Delivery Dashboard or
Demo Orchestrator authoritative. AosCloud remains the lifecycle system of
record and execution control plane; the owning team remains accountable for
its explicit decision, and an authorized OEM identity confirms every mutation
affecting OEM Units.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Required behavior and qualification of external AosCore, Service Manager, IAM and AosCloud lifecycle/logging mechanisms used by the demo |
| What this package does not own | Factory image creation, FOTA/Service artifact contents, team release decisions, dashboard presentation logic, VM overlay orchestration, functional data or vehicle control |
| Intended result | Two freshly provisioned Units can receive independently governed FOTA/SOTA releases through Validation and Demonstration lanes, expose authoritative state/log evidence and retire without identity reuse |
| Accountable lifecycle owner | AosEdge Platform integration with OEM-authorized Cloud operation; individual release decisions remain with Platform Team, Function Team 1 or Function Team 2 |
| Primary source | External AosCore/AosCloud platform plus project-owned qualification evidence in `aosedge-sdv-demo`; no fork of the platform is introduced |

## Component Boundary

### In scope

- [AosCore and Service Manager (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core): Unit identity, desired-state reconciliation, actual state, service/component execution, IAM permission lookup, resource enforcement and native log collection;
- [AosCloud Lifecycle Control Plane (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud): provisioning records, Units/Nodes/Unit Sets, verification and validation batches, campaigns, recorded approvals, desired/reported state, audit and native log requests/results;
- exact qualification of the public lifecycle and logging APIs used by the demo;
- explicit current, target, deferred and limitation classifications for every claimed platform behavior.

### Out of scope

- deciding whether Platform, Brake Health or Tire Health software is ready to release;
- storing independent desired state, evidence, approvals or log archives in demo tooling;
- implementing the Software Delivery Dashboard or Demo Orchestrator;
- modifying upstream AosCore/AosCloud to emulate an unavailable roadmap capability;
- production fleet policy, production driver HMI or functional-safety certification.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Fresh identity-free Validation and Demonstration overlays | `CR-FACTORY` and `CR-DEMO` | Exact accepted Factory Image backing digest and distinct pre-provision local identity | Provisioning is blocked before any Cloud mutation |
| Immutable FOTA/SOTA candidates | Platform Team or owning Function Team | Accepted version, digest/metadata identity, architecture and requested permissions | Artifact cannot enter validation |
| Evidence and final-confirmation presentation | `CR-DEMO` | Stateless view over qualified AosCloud APIs with active-role display and authoritative re-read | Approval remains disabled or uses the original AosCloud UI |
| Runtime/service health | `CR-FACTORY`, `CR-VDP`, `CR-BHS`, `CR-TIRE` | Versioned health/readiness contracts and bounded resources | Unit actual state cannot be accepted as stage-ready |
| Stable Unit Set configuration and run-scoped membership control | `CR-DEMO` over qualified `CMP-AOS-CLOUD` APIs | One designated Verification Unit Set and one distinct Demonstration Unit Set; no unresolved prior-run membership or lifecycle objects | M1 or any release approval remains blocked |
| External platform release | AosEdge Platform Team | Exact Cloud/API/Core versions identified and compatible | Qualification result is invalidated; deferred features remain unavailable |

## Current Implementation Baseline

| Capability | Evidence | State for this package |
| --- | --- | --- |
| Single-Main-Node provisioning and persistent restart identity | [Single-node provisioning qualification](../../qualification/aosvm-single-node-provisioning.md) | `CURRENT` engineering evidence on existing Units; fresh two-Unit M1 flow and partial-result reconciliation remain `TARGET` |
| Desired/actual SOTA reconciliation | Official Hello World assignment, Active state, removal and recreation in the same qualification record | `CURRENT` for one development Unit |
| FOTA provider delivery and A/B runtime interaction | [Current baseline](../../qualification/current-baseline.md) and provider qualification evidence | `EVIDENCE`; final staged v1-v3 lifecycle remains `TARGET` |
| Verification Batch, Fleet Validation Batch and Campaign object model | [R2 lifecycle research](../../research/demo-foundation/r2-aoscloud-lifecycle.md) | `EXTERNAL / PROVEN model`; exact demo promotion sequence requires qualification |
| Verification and Demonstration Unit Set separation | Existing qualification proved that corrected topology plus a fresh batch can isolate the Validation Unit, while stale-batch behavior remains hazardous | `PARTIAL`; persistent set configuration, run-scoped membership and complete campaign targeting remain `TARGET / QUALIFY` |
| Effective target truth | [Stale-batch scope defect](../../qualification/r6-1-validation-set-scope-defect.md) proves Unit Set membership alone is unsafe | `GAP`; pending-recipient reconciliation required before approval |
| Team decision, Service Provider publication and OEM-authorized approval separation | Accepted architecture and role research | `TARGET / QUALIFY`; current account-specific approval paths are not complete proof |
| Role-bound technical publication | D4-010.3 contract and installed `aos-signer` 2.0.1 inspection | `DECIDED / IMPLEMENTATION OPEN`; `platform-oem`, `brake-sp1` and `tire-sp2` are distinct pre-bound profiles, each using a local mode-`0600` PKCS#12 in the current compatibility path; publication still requires an authoritative Cloud re-read and grants no Unit approval |
| Native system/service/crash logging | [R8 native logging research](../../research/demo-foundation/r8-aosedge-native-logging.md) and Hello World log retrieval | Collection, Cloud storage and Unit/Service log API contract `CURRENT`; live permissions, progress/failure visibility, exact retention duration, deletion effect and offline behavior `TARGET / QUALIFY` |
| Component-to-component dependencies | Official component-manifest contract provides predecessor/version constraints and `runtimeDependencies`; update state includes dependency waiting | `EXTERNAL / CURRENT`; preserve and qualify where used rather than reimplement |
| Service-to-layer dependencies | Official service-configuration contract provides version-bounded layer dependencies; Cloud prevents deletion of a layer still required by service versions | `EXTERNAL / CURRENT`; preserve and qualify where used rather than reimplement |
| Native Service-to-FOTA VDP Component dependency admission | Platform Team roadmap statement and released API inspection show no implementing cross-lifecycle rule | `DEFERRED`; no project-side substitute permitted |
| Offline-only Unit deprovision API contract | [AosCloud OpenAPI v11](https://api.aoscloud.io/api/v11/openapi.json) implementation `6.1.26` documents `DELETE /units/{item_id}/deprovision/`, successful `204` without a response body and an offline precondition | `EXTERNAL / PROVEN contract`; resulting state, credential invalidation and complete two-Unit ordering remain `TARGET / QUALIFY` |

Existing `.1` and `.2` Units are retained engineering evidence. They are not
fresh M1 proof and shall not be relabelled as manufactured Validation and
Demonstration Units for final acceptance.

## Unit Set and Demo Lane Model

The terms below describe different layers of the release lifecycle and shall
not be used as synonyms:

| Concept | Meaning in this demo | Lifetime and authority |
| --- | --- | --- |
| Validation lane | Demo role for the disposable vehicle computer on which a candidate is qualified first | Exists for one demo run and is bound to exactly one current Validation Unit |
| Verification Unit Set | AosCloud cohort designated to implement the Validation lane and receive verification delivery | The set object is stable configuration; its membership is authoritative Cloud state and is run-scoped |
| Demonstration lane | Demo role representing the already manufactured field vehicle used after candidate acceptance | Exists for one demo run and is bound to exactly one current Demonstration Unit |
| Demonstration Unit Set | Separate AosCloud cohort used as the Campaign target for accepted promotion | The set object is stable configuration; its membership is authoritative Cloud state and is run-scoped |
| Artifact Verification Batch | Candidate/architecture verification object and its approval state | Fresh for the exact candidate; it is not a Unit Set or vehicle-validation result |
| Fleet Validation Batch | Record of fleet-validation state for the accepted candidate | Fresh for the release candidate and validation decision; it is not the Demonstration target |
| Campaign | Promotion/execution object bound to an accepted Fleet Validation Batch and the Demonstration Unit Set | Fresh for each promotion attempt; its per-Unit result remains authoritative Cloud evidence |

The two Unit Set objects may remain in AosCloud between demo runs as named,
controlled configuration. Their memberships do not persist as demo state. At
the start of M1 both sets must be empty of prior-run Units and free of
unresolved lifecycle references. After fresh provisioning, `CR-DEMO` assigns
the new Validation Unit to the Verification Unit Set and the new Demonstration
Unit to the Demonstration Unit Set, then proves exact disjoint membership
before a release begins. R0 uses the qualified Cloud operations and
authoritative reads to prove that retired Units are absent from both sets and
that both memberships are empty before `CR-DEMO` may discard local overlays.
The stable set objects need not be deleted and recreated for every run.

Verification batches, Fleet Validation Batches and Campaigns are never reused
after candidate identity or Unit Set membership changes. Unit Set membership
expresses intended cohort only: immediately before approval, effective
recipients are derived from pending-batch references across the complete
applicable Fleet/OEM Unit visibility scope and, for promotion, Campaign target
and per-Unit records. A mismatch or incomplete visibility blocks the action
and requires a fresh corrected lifecycle object.

`CR-AOS` owns qualification of these external Cloud semantics. `CR-DEMO` owns
the project-side configuration, membership reconciliation, target guard,
operator presentation and isolated tests for that logic. The exact current
API field and role operations remain a D4 qualification item and must not be
inferred from the logical lane names.

## Testability Boundary and Unit-Test Exception

`CMP-AOS-CORE` and `CMP-AOS-CLOUD` are externally supplied executables and
services. This package owns no replacement scheduler, desired-state database,
admission controller, IAM server, log collector or Cloud implementation.
Therefore no project-owned `UT-AOS-*` obligations are created for the external
platform internals.

Each requirement instead has mandatory contract, integration, analysis and/or
end-to-end proof. Any project-owned API normalizer, target guard, approval UI
or orchestration state machine is tested in `CR-DEMO`; component/runtime and
service logic is tested in its owning package. This exception must be revisited
if project-owned executable lifecycle logic is later moved into `CR-AOS`.

## Interface Summary

| Interface | Direction at Aos platform | Data or action | Failure behavior | Authority |
| --- | --- | --- | --- | --- |
| [Platform FOTA (`IF-LC-001`)](../component-decomposition-and-interface-register.md#if-lc-001) | In to Cloud | Immutable VDP artifact, architecture and digest identity | Invalid/unverified artifact never becomes deployable | Platform Team artifact plus Cloud verification record |
| [Brake Health SOTA (`IF-LC-002`)](../component-decomposition-and-interface-register.md#if-lc-002) | In to Cloud | Service artifact and metadata published through Service Provider 1 identity | Technical verification or publication failure creates no OEM Unit deployment | Function Team 1 artifact; Cloud verification record |
| [Tire Health SOTA (`IF-LC-007`)](../component-decomposition-and-interface-register.md#if-lc-007) | In to Cloud | Independent Service Provider 2 artifact and metadata | Failure leaves Brake Health and platform lifecycles unchanged | Function Team 2 artifact; Cloud verification record |
| [Platform approval (`IF-LC-008`)](../component-decomposition-and-interface-register.md#if-lc-008) | In to Cloud | Explicit Platform Team final FOTA decision through authorized OEM identity | Wrong role, stale target or incomplete evidence blocks the mutation | Platform Team decision; AosCloud audit/execution |
| [Brake approval (`IF-LC-009`)](../component-decomposition-and-interface-register.md#if-lc-009) | In to Cloud | Explicit Function Team 1 SOTA decision through authorized OEM identity | SP publication alone cannot approve OEM Unit deployment | Function Team 1 decision; AosCloud audit/execution |
| [Tire approval (`IF-LC-010`)](../component-decomposition-and-interface-register.md#if-lc-010) | In to Cloud | Explicit Function Team 2 SOTA decision through authorized OEM identity | SP publication alone cannot approve OEM Unit deployment | Function Team 2 decision; AosCloud audit/execution |
| [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) | Bidirectional | Provisioning, complete desired state, update delivery, validation, actual state and retirement | Offline/stalled/error state is explicit; no fabricated convergence | AosCloud desired state and current Unit-reported actual state |
| [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005) | Out/read plus explicitly confirmed action | Scoped lifecycle reads, final mutations and authoritative post-action re-read | Missing/ambiguous/stale data remains blocked or `UNKNOWN` | AosCloud; dashboard has no parallel lifecycle authority |
| [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006) | Out from AosCore | Install, start, stop, update, rollback, readiness and resource enforcement | Failed candidate/service reports error and preserves qualified recovery state | Service Manager actual state |
| [Native logs (`IF-OBS-001`)](../component-decomposition-and-interface-register.md#if-obs-001) | Bidirectional | Explicit system/service/crash-log request, status, Cloud-retained result, download and delete | Offline, permission, timeout, retention and deletion states remain factual | AosCloud request and related stored-file state |
| [IAM permission lookup (`IF-AUTH-008`)](../component-decomposition-and-interface-register.md#if-auth-008) | Out from Aos IAM | `GetPermissions` result for a running SOTA instance and fixed `kuksa` resource | Invalid/stale/unregistered secret returns no permission result | Service Manager registration and Aos IAM; `CMP-KAC` only translates the current result |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove project-owned isolated logic | No such logic is owned here | No; reviewed external-component exception above | N/A; tests belong to `CR-DEMO` or the component/service owner |
| Component | Prove AosCore/Service Manager behavior on one disposable Unit | Real AosCore with controlled artifact/service fixtures | Yes | Provisioning, reconciliation, runtime, IAM, resource and log qualification record |
| Contract | Prove Cloud/Core/API schemas, role permissions, status semantics and error behavior | Exact external platform/API release and sanitized fixtures | Yes | Versioned endpoint/field/permission/error conformance report |
| Integration | Prove Cloud-to-Unit lifecycle across VU/DU and adjacent real components | Two disposable Units and qualified artifacts | Yes | Target, approval, FOTA/SOTA, rollback, offline/log and retirement records |
| End-to-end | Prove M1 through R0 audience-visible lifecycle without invented state | Complete Validation and Demonstration lanes | Yes | Stage evidence tied to exact Unit IDs, time window, candidates and audit records |

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | Design state | Platform state |
| --- | --- | --- | --- | --- |
| [Unique provisioning and lane binding (`REQ-AOS-001`)](#req-aos-001) | Create exactly one Unit/Main Node identity per fresh overlay and bind the two roles | Contract, Integration, End-to-end | D3 design-reviewed | `PARTIAL` |
| [Partial provisioning reconciliation (`REQ-AOS-002`)](#req-aos-002) | Preserve and reconcile uncertain results instead of blind retry | Contract, Integration, Analysis | D3 design-reviewed | `TARGET` |
| [Authoritative Unit state and run correlation (`REQ-AOS-003`)](#req-aos-003) | Expose current identity, lane, connection, desired/actual graph and source time | Contract, Integration, End-to-end | D3 design-reviewed | `PARTIAL` |
| [Distinct immutable lifecycle objects (`REQ-AOS-004`)](#req-aos-004) | Keep candidate verification, fleet validation and campaign identity/state separate | Contract, Integration, Inspection | D3 design-reviewed | `EXTERNAL / EXTEND` |
| [Effective-recipient truth (`REQ-AOS-005`)](#req-aos-005) | Make pending recipients provable and block stale or unexpected targets | Contract, Integration, Analysis, End-to-end | D3 design-reviewed | `GAP / PARTIAL` |
| [Validation-first identical promotion (`REQ-AOS-006`)](#req-aos-006) | Qualify on VU before promoting identical accepted bytes to DU | Contract, Integration, End-to-end | D3 design-reviewed | `PARTIAL` |
| [Recorded owner and OEM approval (`REQ-AOS-007`)](#req-aos-007) | Separate SP publication, team acceptance and explicit OEM-authorized mutation | Contract, Integration, Audit, End-to-end | D3 design-reviewed | `TARGET / QUALIFY` |
| [Combined-graph owner gate (`REQ-AOS-008`)](#req-aos-008) | Require all owners for the exact FOTA/SOTA graph before promotion | Contract, Integration, End-to-end | D3 design-reviewed | `TARGET / QUALIFY` |
| [Desired/actual reconciliation and bounded execution (`REQ-AOS-009`)](#req-aos-009) | Converge through Service Manager with factual state, health and resource enforcement | Contract, Component, Integration | D3 design-reviewed | Platform mechanism `CURRENT`; target graph `EXTEND` |
| [Compatibility metadata and fail-closed runtime (`REQ-AOS-010`)](#req-aos-010) | Preserve service capability requirements and expose actual platform version to readiness logic | Contract, Integration, End-to-end | D3 design-reviewed | `PARTIAL` |
| [Deferred native Service-to-VDP admission (`REQ-AOS-011`)](#req-aos-011) | Reject incompatible SOTA against its required FOTA VDP Component in Cloud before desired-state change or transfer | Contract, Integration, Inspection | D3 design-reviewed | `DEFERRED` |
| [Dependent-first rollback and recovery (`REQ-AOS-012`)](#req-aos-012) | Remove/rollback dependent SOTA before its FOTA capability while preserving unrelated lifecycles | Contract, Integration, Analysis, End-to-end | D3 design-reviewed | `PARTIAL / UNQUALIFIED` |
| [Native operational-log lifecycle (`REQ-AOS-013`)](#req-aos-013) | Provide scoped factual system/service/crash-log requests and results | Contract, Integration, Analysis | D3 design-reviewed | Product path `CURRENT`; API behavior `TARGET / QUALIFY` |
| [Qualified identity retirement (`REQ-AOS-015`)](#req-aos-015) | Expose separate deprovision/delete outcomes, reject old credentials and retain audit | Contract, Integration, Analysis, End-to-end | D3 design-reviewed | `TARGET` |
| [Unit Set isolation and run-scoped membership (`REQ-AOS-016`)](#req-aos-016) | Expose authoritative isolated Unit Set state and qualified membership operations | Contract, Integration, Analysis, End-to-end | D3 design-reviewed | `PARTIAL / TARGET` |

## Detailed Requirements

### Unique provisioning and lane binding

<a id="req-aos-001"></a>

- ID: `REQ-AOS-001`
- Statement: The provisioning lifecycle shall create exactly one unique Unit and one Main Node identity for each accepted fresh overlay, bind one to the Validation role and one to the Demonstration role, and preserve those bindings through G0–T1 without reprovisioning.
- Rationale: Every lifecycle observation and approval must address one unambiguous vehicle-computer identity and lane.
- Parent system requirement: [One identity per overlay (`SYS-ID-001`)](../system-requirements-and-traceability.md#sys-id-001)
- Architecture flows: [Provisioning (`AF-M1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-lc) and [provisioning evidence (`AF-M1-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-ob)
- Components: [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core) and [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interface: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004)
- Verification levels: Contract, Integration, End-to-end
- Required evidence: redacted overlay/Unit/Node/certificate uniqueness, exact role/Unit Set binding and stable identity across accepted restarts
- State: D3 design-reviewed; existing one-Unit provisioning is implementation evidence, not final two-Unit acceptance

Acceptance requires two different Unit and Node identities from two fresh
overlays, exactly one current-run lane per Unit and stable bindings throughout
the staged lifecycle. Duplicate identity, reused provisioning material,
additional Node or ambiguous role blocks M1.

### Partial provisioning reconciliation

<a id="req-aos-002"></a>

- ID: `REQ-AOS-002`
- Statement: A provisioning timeout, transport loss or partial result shall enter an explicit reconciliation state and shall never be blindly retried, labelled clean or deleted locally while Cloud identity outcome is uncertain.
- Rationale: Repeating provisioning can duplicate or orphan vehicle identities.
- Parent system requirement: [Reconcile partial provisioning (`SYS-ID-002`)](../system-requirements-and-traceability.md#sys-id-002)
- Architecture flow: [Fail-closed provisioning (`AF-M1-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-fr)
- Components: [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core) and [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interface: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004)
- Verification levels: Contract, Integration, Analysis
- Required evidence: operation/result correlation, post-timeout Cloud/guest re-read, explicit reconciliation decision and preservation of unresolved overlay/records
- State: D3 design-reviewed

Acceptance covers success, timeout before response, response loss after Cloud
creation, one-Unit success/one-Unit failure and interrupted cleanup. Only a
proven no-identity result may return an overlay to the unprovisioned state.

### Authoritative Unit state and run correlation

<a id="req-aos-003"></a>

- ID: `REQ-AOS-003`
- Statement: Before every update or approval, AosCloud and AosCore integration shall expose the current Unit ID, Node ID, role, Unit Set membership, connection/last-reported state, complete desired and reported actual software graph, pending lifecycle references and source timestamps for both current-run Units.
- Rationale: Stage labels and update decisions must be derived from current authoritative facts rather than dashboard memory.
- Parent system requirements: [Prove current Unit state (`SYS-ID-003`)](../system-requirements-and-traceability.md#sys-id-003), [Cloud-authoritative dashboard (`SYS-OBS-002`)](../system-requirements-and-traceability.md#sys-obs-002) and [per-run correlation (`SYS-OBS-004`)](../system-requirements-and-traceability.md#sys-obs-004)
- Architecture flows: [Provisioning evidence (`AF-M1-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-ob), [evidence architecture (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs) and [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core) and [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005)
- Verification levels: Contract, Integration, End-to-end
- Required evidence: authoritative pre-action snapshot and post-action re-read tied to Unit IDs and the bounded run time window
- State: D3 design-reviewed

Acceptance reports absent, stale, conflicting or eventually consistent state
as `UNKNOWN` or blocked. Installed state alone does not prove application
readiness, and Unit Set membership alone does not prove update targeting.

### Distinct immutable lifecycle objects

<a id="req-aos-004"></a>

- ID: `REQ-AOS-004`
- Statement: The lifecycle shall retain immutable candidate identity and distinguish Artifact Verification Batch, Fleet Validation Batch and Campaign state, identifiers, transitions and evidence without collapsing them into one approval or stage object.
- Rationale: Architecture verification, fleet validation and Demonstration promotion are different controls with different evidence.
- Parent system requirement: [Immutable release candidates (`SYS-REL-001`)](../system-requirements-and-traceability.md#sys-rel-001)
- Architecture flows: [FOTA lifecycle (`AF-G1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc) and [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core)
- Interfaces: [Platform FOTA (`IF-LC-001`)](../component-decomposition-and-interface-register.md#if-lc-001), [Brake SOTA (`IF-LC-002`)](../component-decomposition-and-interface-register.md#if-lc-002), [Tire SOTA (`IF-LC-007`)](../component-decomposition-and-interface-register.md#if-lc-007) and [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004)
- Verification levels: Contract, Integration, Inspection
- Required evidence: exact candidate/version/digest or documented artifact identity plus separate verification, validation and campaign records
- State: D3 design-reviewed

Acceptance rejects mutable candidate bytes, reused identity for different
content, conflated batch/campaign status or any display that presents artifact
verification as vehicle validation.

### Effective-recipient truth

<a id="req-aos-005"></a>

- ID: `REQ-AOS-005`
- Statement: The platform integration shall expose a complete paginated Unit inventory for the applicable Fleet/OEM visibility scope plus current per-Unit component and service pending-batch references sufficient to derive every effective recipient. The release workflow shall compare the resulting exact Unit-ID set with the intended fresh Validation or Demonstration Unit Set and block approval when the sets differ or completeness cannot be proven.
- Rationale: A stale batch previously retained a Unit after Unit Set membership changed.
- Parent system requirements: [Current effective-target validation (`SYS-REL-002`)](../system-requirements-and-traceability.md#sys-rel-002), [prove current Unit state (`SYS-ID-003`)](../system-requirements-and-traceability.md#sys-id-003) and [evidence-backed approval (`SYS-REL-010`)](../system-requirements-and-traceability.md#sys-rel-010)
- Architecture flows: [FOTA validation (`AF-G1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc) and [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005)
- Verification levels: Contract, Integration, Analysis, End-to-end
- Required evidence: intended Unit Set, complete Fleet/OEM inventory pagination, API visibility scope, every applicable Unit pending-batch reference, batch/campaign identity, exact-set comparison, mismatch result and fresh corrected-batch proof
- State: D3 design-reviewed; current API requires recipient derivation because Verification Batch has no direct target-Unit list

Acceptance never infers effective targets from current Unit Set membership
alone and never scans only the intended members. Missing or incomplete Fleet
pagination, insufficient OEM visibility, missing pending references, an
unexpected Unit, stale batch or changed membership blocks the action and
requires a fresh reconciled lifecycle object.

### Validation-first identical promotion

<a id="req-aos-006"></a>

- ID: `REQ-AOS-006`
- Statement: Each FOTA or SOTA candidate shall reach and pass its required qualification on the Validation Unit before the identical accepted artifact identity is promoted through a Campaign to the Demonstration Unit.
- Rationale: Demonstration deployment must reuse validated bytes rather than rebuild or bypass the Validation lane.
- Parent system requirement: [Validate before promotion (`SYS-REL-004`)](../system-requirements-and-traceability.md#sys-rel-004)
- Architecture flows: [FOTA validation (`AF-G1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc), [Brake SOTA (`AF-G2-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-lc) and [Tire SOTA (`AF-TIRE-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-lc)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and the applicable FOTA/SOTA interface
- Verification levels: Contract, Integration, End-to-end
- Required evidence: VU actual state/readiness, accepted validation record, candidate identity comparison, campaign target and DU actual state/readiness
- State: D3 design-reviewed

Acceptance rejects DU-first delivery, rebuilt promotion content, changed
metadata/permissions, missing VU result, unsuccessful Campaign Unit result or
an actual-state mismatch after promotion.

### Recorded owner and OEM approval

<a id="req-aos-007"></a>

- ID: `REQ-AOS-007`
- Statement: AosCloud integration shall distinguish technical publication through fixed D4-010.3 profile `platform-oem`, `brake-sp1` or `tire-sp2`, owning-team acceptance and the final explicitly confirmed OEM-authorized validation/deployment/promotion action. It shall record the active role, owner, exact artifact/metadata identity, requested permissions, effective target, evidence status/freshness and resulting transition. `PUBLISHED` is accepted only after an independent authoritative Cloud re-read; an ambiguous publication is reconciled without blind retry and never implies Unit approval.
- Rationale: Passing tests and dashboard buttons do not own release decisions or authorize OEM Unit mutation by themselves.
- Parent system requirements: [Team-owned release decisions (`SYS-REL-007`)](../system-requirements-and-traceability.md#sys-rel-007), [OEM-authorized deployment (`SYS-REL-008`)](../system-requirements-and-traceability.md#sys-rel-008), [evidence-backed approval (`SYS-REL-010`)](../system-requirements-and-traceability.md#sys-rel-010) and [role-bound protected publication (`SYS-REL-011`)](../system-requirements-and-traceability.md#sys-rel-011)
- Architecture flows: [Common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release), [Brake SOTA (`AF-G2-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-lc) and [Tire SOTA (`AF-TIRE-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-lc)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interfaces: [Platform approval (`IF-LC-008`)](../component-decomposition-and-interface-register.md#if-lc-008), [Brake approval (`IF-LC-009`)](../component-decomposition-and-interface-register.md#if-lc-009), [Tire approval (`IF-LC-010`)](../component-decomposition-and-interface-register.md#if-lc-010) and [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005)
- Verification levels: Contract, Integration, Audit, End-to-end
- Required evidence: D4-010.3 profile binding, role/permission matrix, complete decision basis, explicit confirmation, prepared/signed/Cloud identity chain, independent Cloud publication re-read, immutable Cloud audit result and authoritative post-approval re-read
- State: D3 design-reviewed; D4-010.3 profile/custody/publication-state decision accepted; exact Cloud endpoint/role qualification remains open

Acceptance blocks wrong role, SP-only deployment approval, missing or stale
evidence, mismatched digests/permissions/target or missing team acceptance.
Passing prerequisites never auto-approve and the dashboard stores no parallel
approval state.

### Combined-graph owner gate

<a id="req-aos-008"></a>

- ID: `REQ-AOS-008`
- Statement: Promotion of a combined VDP FOTA and dependent Brake or Tire SOTA graph shall remain blocked until each accountable owner has accepted the exact candidate it owns and the relevant integration result for the same versions, identities and effective targets.
- Rationale: One team cannot silently approve another team's release or a different combined graph.
- Parent system requirements: [Combined-graph owner gate (`SYS-REL-009`)](../system-requirements-and-traceability.md#sys-rel-009) and [evidence-backed approval (`SYS-REL-010`)](../system-requirements-and-traceability.md#sys-rel-010)
- Architecture flows: [Joint Brake lifecycle (`AF-G3-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-lc) and [bidirectional lifecycle (`AF-G4-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-lc)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interfaces: [Platform approval (`IF-LC-008`)](../component-decomposition-and-interface-register.md#if-lc-008), [Brake approval (`IF-LC-009`)](../component-decomposition-and-interface-register.md#if-lc-009) and [Tire approval (`IF-LC-010`)](../component-decomposition-and-interface-register.md#if-lc-010)
- Verification levels: Contract, Integration, End-to-end
- Required evidence: per-owner acceptance records bound to one graph manifest, negative missing-owner/mismatch cases and ordered DU promotion
- State: D3 design-reviewed; exact native enforcement in the current Cloud requires qualification

Acceptance rejects one-owner approval, mismatched FOTA/SOTA identity, stale
integration evidence or promotion of the service before the required platform
capability reports ready.

### Desired/actual reconciliation and bounded execution

<a id="req-aos-009"></a>

- ID: `REQ-AOS-009`
- Statement: AosCloud shall remain authoritative for the complete desired graph, while AosCore and Service Manager shall reconcile and report factual actual component, service-instance, health, error and bounded-resource state without treating assignment or installation as readiness.
- Rationale: Lifecycle state must distinguish intent, transfer/install state, running state and application readiness.
- Parent system requirements: [Prove current Unit state (`SYS-ID-003`)](../system-requirements-and-traceability.md#sys-id-003), [validate before promotion (`SYS-REL-004`)](../system-requirements-and-traceability.md#sys-rel-004), [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](../system-requirements-and-traceability.md#sys-obs-007) and [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](../system-requirements-and-traceability.md#sys-res-001)
- Architecture flows: [G0 baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt), [G1 FOTA (`AF-G1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc), [Brake SOTA (`AF-G2-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g2-lc), [targeted vehicle external-connectivity loss (`AF-X-OFFLINE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-offline) and [AosCore tenant isolation (`AF-TIRE-RES`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-res)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Contract, Component, Integration
- Required evidence: desired/actual/status sequence, Service Manager instance/resource state, health/readiness evidence, errors and reconnect convergence
- State: D3 design-reviewed

Acceptance covers install/start/stop/restart/removal, per-instance cgroup
resource enforcement and monitoring, bounded resource failure,
Unit disconnect/reconnect and current-state re-read. The system must preserve
local installed behavior during Cloud loss where specified, while new
lifecycle operations remain unavailable. The `AF-TIRE-RES` proof uses the
external AosCore implementation and therefore requires contract/integration
evidence rather than a project-owned unit test.

### Compatibility metadata and fail-closed runtime

<a id="req-aos-010"></a>

- ID: `REQ-AOS-010`
- Statement: The lifecycle shall preserve each service's D4-007 VDP compatibility range, expose the current installed component identity and capability manifest to deployment/readiness evidence, and shall distinguish an installed/process-healthy service from functional `READY`. It shall not present an incompatible or dependency-unready service as an accepted running graph.
- Rationale: Current platform releases do not provide native pre-transfer Service-to-FOTA admission, so runtime defense in depth remains mandatory.
- Parent system requirement: [Service capability compatibility (`SYS-REL-003`)](../system-requirements-and-traceability.md#sys-rel-003)
- Architecture flows: [Deferred dependency flow (`AF-G3-DEP`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-dep) and [joint Brake lifecycle (`AF-G3-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-lc)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core), jointly with the owning service package
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Contract, Integration, End-to-end
- Required evidence: declared range, installed identity/capability manifest, compatible/incompatible readiness result, automatic blocked-to-ready transition after a compatible component change and exact accepted graph manifest
- State: D3 design-reviewed; D4-007 compatibility/readiness contract accepted

Acceptance requires compatible startup and fail-closed incompatible readiness
without claiming that this service-side check is native Cloud admission.

### Deferred native Service-to-VDP Component admission

<a id="req-aos-011"></a>

- ID: `REQ-AOS-011`
- Statement: After an implementing AosEdge release is available, AosCloud shall natively reject a SOTA request whose required FOTA Vehicle Data Platform Component range is unsatisfied on the intended Unit before Subject-service desired-state change, batch/campaign creation or content transfer and shall return an authoritative machine-readable reason. This deferred cross-lifecycle rule does not replace or diminish the released component-to-component and service-to-layer dependency mechanisms.
- Rationale: Early Cloud rejection is an accepted future demo point, but no project-side approximation is truthful or economical.
- Parent system requirement: [Native Cloud dependency rejection (`SYS-REL-006`)](../system-requirements-and-traceability.md#sys-rel-006)
- Architecture flow: [Deferred native rejection (`AF-G3-DEP`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-dep)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interfaces: [Brake SOTA (`IF-LC-002`)](../component-decomposition-and-interface-register.md#if-lc-002), [Tire SOTA (`IF-LC-007`)](../component-decomposition-and-interface-register.md#if-lc-007) and [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004)
- Verification levels: Contract, Integration, Inspection
- Required evidence: official release/API support, incompatible pre-mutation rejection, absence of desired-state/batch/campaign/transfer side effects, machine-readable reason and compatible retry
- State: D3 requirement retained as `DEFERRED`; not executable and not an implementation input until platform release qualification

No Software Delivery Dashboard admission controller, local proxy or alternate
policy database may be presented as satisfying this requirement.

### Dependent-first rollback and recovery

<a id="req-aos-012"></a>

- ID: `REQ-AOS-012`
- Statement: Recovery or rollback of a graph containing a dependent SOTA service and VDP capability shall stop/remove or roll back the dependent service before changing the platform capability, preserve unrelated lifecycles and report each transition and failure factually.
- Rationale: Removing a capability beneath a running consumer can produce an invalid graph.
- Parent system requirement: [Dependent-first rollback (`SYS-REL-005`)](../system-requirements-and-traceability.md#sys-rel-005)
- Architecture flows: [Provider failure (`AF-G1-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-fr), [Brake failure (`AF-G3-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-fr) and [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Verification levels: Contract, Integration, Analysis, End-to-end
- Required evidence: ordered service-first transition, previous-state recovery, unaffected-service continuity and post-failure desired/actual re-read
- State: D3 design-reviewed; SOTA removal is proven, pre-Apply FOTA revert is documented, committed component downgrade/removal remains unqualified

Acceptance distinguishes cancel/invalidate, pre-Apply revert, SOTA removal and
post-Apply recovery. Stopping a campaign or invalidating a batch must not be
presented as rollback of Units that already applied an update.

### Native operational-log lifecycle

<a id="req-aos-013"></a>

- ID: `REQ-AOS-013`
- Statement: AosCore and AosCloud shall provide scoped, explicitly requested system, service-instance and crash-log collection with source time range, persistent Cloud request state, a Cloud-retained downloadable result, bounded archive parts and failure visibility. The exact retention duration, explicit deletion effect, online/offline and redaction behavior shall be qualified, and no indefinite-retention claim shall be made.
- Rationale: Operational diagnosis should use the native platform path rather than a demo-owned secondary collection and storage pipeline.
- Parent system requirements: [Operational log controls (`SYS-OBS-003`)](../system-requirements-and-traceability.md#sys-obs-003) and [Cloud-authoritative dashboard (`SYS-OBS-002`)](../system-requirements-and-traceability.md#sys-obs-002)
- Architecture flow: [Cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core) and [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud)
- Interface: [Native logs (`IF-OBS-001`)](../component-decomposition-and-interface-register.md#if-obs-001)
- Verification levels: Contract, Integration, Analysis
- Required evidence: scoped role matrix, request/poll/result/download/delete sequence, archive metadata, timestamps, progress/failure visibility, deployed retention policy, deletion result and disconnect/reconnect results with secret-negative inspection
- State: D3 design-reviewed

Acceptance treats the Cloud request and stored result as authoritative while
retained, never presents requested archives as a continuous live stream or an
indefinite archive, and never requires the Software Delivery Dashboard to
retain a second log archive. Any temporary dashboard download is bounded and
removed. Unsupported API actions fall back to the original AosCloud UI as the
technical drill-down.

### Retired lifecycle timing requirement

<a id="req-aos-014"></a>

- ID: `REQ-AOS-014`
- Retired parent: [retired lifecycle timing (`SYS-TIM-001`)](../system-requirements-and-traceability.md#sys-tim-001)
- State: Retired from the first-demo scope together with `SYS-TIM-001` and
  `REQ-DEMO-012`.
- Replacement: Operation-specific timeout/uncertainty reconciliation remains
  in the relevant provisioning, action and retirement requirements. Future
  performance qualification is vehicle/VM-focused and is tracked as the
  deferred Edge Runtime Performance Qualification roadmap workstream.
- Reason: Cloud lifecycle duration and presenter timing KPIs do not prove the
  value of the in-vehicle demo.

### Qualified identity retirement

<a id="req-aos-015"></a>

- ID: `REQ-AOS-015`
- Statement: After a final authoritative online read, the Aos lifecycle shall require each current-run Unit to be placed offline through a qualified bounded local operation and reported `Offline` by AosCloud before invoking the qualified offline-only deprovision API. Because successful deprovision returns no operation body, the lifecycle shall re-read and reconcile authoritative state, perform a bounded old-credential reconnect test proving that neither retired identity can return `Online`, then expose separately observable qualified API operations for Unit deletion and any required Unit-owned Node handling. It shall retain authoritative Cloud audit history and expose every unresolved result so `CR-DEMO` keeps VM stop/deletion ordering and local overlay disposal blocked until the corresponding retirement gate is proven.
- Rationale: A reusable demo must retire identities cleanly without treating disk deletion as deprovisioning.
- Parent system requirements: [Qualify identity retirement (`SYS-ID-004`)](../system-requirements-and-traceability.md#sys-id-004) and [retire Units and overlays (`SYS-RET-001`)](../system-requirements-and-traceability.md#sys-ret-001)
- Architecture flows: [Controlled retirement (`AF-R0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-lc), [retirement evidence (`AF-R0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-ob) and [partial retirement (`AF-R0-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-fr)
- Components: [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core) and [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud), jointly with `CR-DEMO`
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005)
- Verification levels: Contract, Integration, Analysis, End-to-end
- Required evidence: final online snapshot, qualified offline action, Cloud-reported `Offline` precondition, separate API deprovision response and authoritative re-read, bounded retired-certificate reconnect rejection, final VM stop, Unit/Node deletion result, retained audit and overlay-release authorization
- State: D3 design-reviewed

Acceptance keeps an uncertain deprovision or delete result authoritative and
visible so `CR-DEMO` preserves the corresponding Cloud record and overlay. It
never submits deprovision before AosCloud reports the Unit `Offline`, never
infers completion from a no-content response without a re-read, never assumes
Unit deletion also deletes Nodes, and never calls R0 a production vehicle
rollback or fleet-deletion policy.

### Unit Set isolation and run-scoped membership

<a id="req-aos-016"></a>

- ID: `REQ-AOS-016`
- Statement: AosCloud shall expose separately identifiable Verification and Demonstration Unit Set objects, authoritative membership reads, qualified membership-mutation and Unit-deletion effects, pending-recipient references and Campaign targets sufficient for `CR-DEMO` to prove exact disjoint current-run membership, require fresh lifecycle objects after membership changes and prove both sets empty after R0.
- Rationale: Persistent Cloud set configuration is reusable, but stale Unit membership or lifecycle objects can silently target retired or unintended vehicles.
- Parent system requirements: [One identity per overlay (`SYS-ID-001`)](../system-requirements-and-traceability.md#sys-id-001), [prove current Unit state (`SYS-ID-003`)](../system-requirements-and-traceability.md#sys-id-003), [current effective-target validation (`SYS-REL-002`)](../system-requirements-and-traceability.md#sys-rel-002), [validate before promotion (`SYS-REL-004`)](../system-requirements-and-traceability.md#sys-rel-004), [retire Units and overlays (`SYS-RET-001`)](../system-requirements-and-traceability.md#sys-ret-001) and [reconcile Unit Sets for the next run (`SYS-RET-006`)](../system-requirements-and-traceability.md#sys-ret-006)
- Architecture flows: [Provisioning (`AF-M1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-lc), [provisioning evidence (`AF-M1-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-ob), [fail-closed provisioning (`AF-M1-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-m1-fr), [FOTA lifecycle (`AF-G1-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc), [common release flow (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release), [controlled retirement (`AF-R0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-lc) and [partial retirement (`AF-R0-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-fr)
- Components: [AosCloud (`CMP-AOS-CLOUD`)](../component-decomposition-and-interface-register.md#cmp-aos-cloud), jointly with `CR-DEMO`
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [Software Delivery API (`IF-LC-005`)](../component-decomposition-and-interface-register.md#if-lc-005)
- Verification levels: Contract, Integration, Analysis, End-to-end
- Required evidence: designated set identifiers and roles, pre-M1 empty membership, exact VU/DU membership and disjointness, fresh batch/validation/campaign identities, pending-recipient and Campaign-target reconciliation, and post-R0 empty membership
- State: D3 design-reviewed; isolated fresh-batch behavior has evidence, while complete persistent-set and campaign qualification remains target work

Acceptance proves the external platform contract needed for exactly one
current Validation Unit in the Verification Unit Set, exactly one current
Demonstration Unit in the Demonstration Unit Set, no overlap and no prior-run
Unit in either set. It exposes enough authoritative state for `CR-DEMO` to
invalidate all unapproved target assumptions after membership changes and
require fresh lifecycle objects. Only the Demonstration Unit may be a
promotion Campaign recipient. R0 remains unresolved until both retired Units
have no membership and both stable sets are empty; `CR-DEMO` owns the resulting
block on overlay deletion and the next M1.

## Unit-Test Obligations

| Requirement group | Unit obligation | Reviewed rationale and replacement proof |
| --- | --- | --- |
| `REQ-AOS-001`–`003` | Reasoned N/A | Provisioning, identity and current state belong to external SDK/AosCore/AosCloud; use contract, two-Unit integration and reconciliation evidence. Project-owned orchestration tests belong to `CR-DEMO`. |
| `REQ-AOS-004`–`008` | Reasoned N/A | Verification, validation, campaign and approval records are external Cloud behavior; use API contract, role-negative, audit and end-to-end tests. Dashboard logic belongs to `CR-DEMO`. |
| `REQ-AOS-009`–`012` | Reasoned N/A | Desired-state reconciliation and runtime scheduling are external AosCore/AosCloud behavior; use component/integration fault tests. Provider/service unit logic belongs to its package. |
| `REQ-AOS-013`, `015`–`016` | Reasoned N/A | Native log transport, retirement and Unit Set APIs are external lifecycle behavior; use contract, live integration and failure/recovery analysis. Membership, target and cleanup guards belong to `CR-DEMO`. |

The exception is part of this D3 review. Adding project-owned lifecycle logic
to this package requires stable `UT-AOS-*` IDs before implementation begins.

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| [`REQ-AOS-001`](#req-aos-001) | N/A; external provisioning | Single-Node identity gate | Provisioning/identity schema | Two fresh overlays and Units | M1 lane evidence |
| [`REQ-AOS-002`](#req-aos-002) | N/A; external provisioning | SDK/guest state inspection | Result/error/reconciliation contract | Interrupted and partial provisioning | M1 fail-closed evidence |
| [`REQ-AOS-003`](#req-aos-003) | N/A; external state authority | Unit actual-state report | Unit/Node/Set/software/status API | Pre/post action re-read | M1–R0 correlated state |
| [`REQ-AOS-004`](#req-aos-004) | N/A; external Cloud objects | Candidate state inspection | Verification/validation/campaign schemas | One complete lifecycle object chain | G1/G2 lifecycle labels |
| [`REQ-AOS-005`](#req-aos-005) | N/A; derivation belongs to `CR-DEMO` | Pending-recipient inspection | Unit pending/batch/campaign fields | Stale/fresh target comparison | Approval-block evidence |
| [`REQ-AOS-006`](#req-aos-006) | N/A; external execution | Unit install/readiness state | Validation/campaign identity | VU then identical DU promotion | G1–T1 promotion evidence |
| [`REQ-AOS-007`](#req-aos-007) | N/A; external role/audit | Cloud action/result state | SP/OEM permissions and approval record | Positive/wrong-role/stale-evidence cases | Visible final decision and audit |
| [`REQ-AOS-008`](#req-aos-008) | N/A; external owner gate | Combined graph state | Owner acceptance schema | Missing/mismatched owner negatives | G3/G4 ordered promotion |
| [`REQ-AOS-009`](#req-aos-009) | N/A; external scheduler | Service Manager lifecycle/resource proof | Desired/actual/status semantics | Install/restart/remove/offline/reconnect | G0–T1 actual graph |
| [`REQ-AOS-010`](#req-aos-010) | N/A; service unit tests elsewhere | Incompatible readiness state | Compatibility metadata/version contract | Compatible/incompatible startup | G3 graph evidence |
| [`REQ-AOS-011`](#req-aos-011) | N/A; deferred external feature | N/A until release | Official API support and reason schema | Pre-mutation reject/compatible retry | Deferred demo point only |
| [`REQ-AOS-012`](#req-aos-012) | N/A; external recovery | Runtime state sequence | Revert/remove/recovery semantics | Dependent-first fault matrix | G3/G4 recovery evidence |
| [`REQ-AOS-013`](#req-aos-013) | N/A; external log path | Service Manager log provider | Request/status/result/permission API | Online/offline log request lifecycle | Selected native-log evidence |
| [`REQ-AOS-015`](#req-aos-015) | N/A; external retirement | Guest identity shutdown state | Deprovision/delete/Node/audit semantics | Certificate rejection and partial failures | R0 retirement evidence |
| [`REQ-AOS-016`](#req-aos-016) | N/A; guards belong to `CR-DEMO` | Unit Set membership inspection | Set role/membership, pending-reference and Campaign-target schemas | Empty/start, exact VU/DU, stale/fresh and post-R0 cases | M1–R0 lane-isolation evidence |

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Authority and separation of duties | [`REQ-AOS-007`](#req-aos-007), [`REQ-AOS-008`](#req-aos-008) | SP publication, team acceptance, OEM authorization and Cloud execution remain distinct | Role matrix, audit and wrong-role negatives |
| Identity and secrets | [`REQ-AOS-001`](#req-aos-001), [`REQ-AOS-002`](#req-aos-002), [`REQ-AOS-015`](#req-aos-015) | One identity per overlay, no blind retry/reuse, retired certificate rejection and redacted evidence | Contract/integration plus secret-negative inspection |
| State truth and target isolation | [`REQ-AOS-003`](#req-aos-003), [`REQ-AOS-005`](#req-aos-005), [`REQ-AOS-009`](#req-aos-009), [`REQ-AOS-016`](#req-aos-016) | Cloud desired and Unit actual state remain authoritative; sets are disjoint and current-run only; stale/unknown state blocks mutation | API conformance, membership reconciliation, target negatives and pre/post action re-read |
| Dependency and recovery | [`REQ-AOS-010`](#req-aos-010), [`REQ-AOS-011`](#req-aos-011), [`REQ-AOS-012`](#req-aos-012) | Current runtime fail-closed defense, deferred native admission and dependent-first recovery are never conflated | Compatibility, no-side-effect and ordered-failure tests |
| Observability and privacy | [`REQ-AOS-013`](#req-aos-013) | Native scoped logs only; no demo-owned pipeline/archive; no secrets/raw telemetry | Permission, retention, redaction and bounded archive tests |
| Vehicle external-connectivity lifecycle behavior | [`REQ-AOS-002`](#req-aos-002), [`REQ-AOS-009`](#req-aos-009), [`REQ-AOS-015`](#req-aos-015) | Explicit uncertain/offline state and operation-specific reconciliation for the Unit-to-AosCloud portion of the atomic vehicle fault | Integration and same-Unit disconnect/reconnect evidence |
| Service-tenant resource isolation | [`REQ-AOS-009`](#req-aos-009) | AosCore/Service Manager is the sole in-vehicle quota-enforcement and monitoring authority; no project resource manager | Actual Tire cgroup CPU cap, Cloud-reported usage/status and unaffected Brake/platform evidence |

## D3 Acceptance Record and Version 0.3 Delta

This 0.1 package was design-reviewed on 2026-08-19 after reviewers agreed that:

1. AosCloud is the authoritative lifecycle/audit source but not the engineering release-decision owner;
2. the Software Delivery Dashboard and Demo Orchestrator remain outside this component boundary;
3. effective recipients are derived from current pending references across a completely paginated applicable Fleet/OEM Unit scope rather than Unit Set membership alone;
4. Artifact Verification, Fleet Validation and Campaign are visibly distinct;
5. current runtime compatibility defense is not presented as future native Cloud admission;
6. external-platform requirements use the reviewed unit-test exception and mandatory contract/integration proof;
7. stable Unit Set objects are separated from run-scoped membership and fresh lifecycle objects;
8. retirement is Cloud identity and empty-set reconciliation before local overlay disposal.
9. one first-demo control removes the Demonstration Unit's external connectivity; `REQ-AOS-009` owns authoritative same-Unit AosCloud disconnect/reconnect state, while Function Team packages own the simultaneously interrupted backend paths and their synchronization.
10. AosCore/Service Manager is the sole in-vehicle resource authority; the
    first tenant-isolation proof caps the actual Tire service CPU cgroup while
    Brake and the platform graph remain healthy, using external-platform
    contract/integration evidence rather than project-owned scheduler logic.

Version 0.2 preserved that acceptance. Version 0.3 is a review candidate that
replaces the retired authorization-interface reference with `IF-AUTH-008` and
makes clear that Aos IAM remains authoritative while `CMP-KAC` only translates
its current result. No `REQ-AOS-*` lifecycle semantics change. It does not
claim platform-feature implementation or authorize provisioning, Cloud
mutation, update, rollback, log request, retirement or VM changes.

## Open Issues

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| Exact current OEM role/API operations for validation acceptance and promotion | Blocks final `REQ-AOS-007`/`008` contract | AosCloud integration + OEM account administration | D4 role/API qualification |
| Exact current Verification Unit Set designation, membership mutation and Campaign target operations | Blocks final `REQ-AOS-016` contract and `CR-DEMO` guard design | AosCloud integration + Demo Orchestration | D4 Unit Set/API qualification |
| Exact service artifact digest/metadata identity exposed by the current public API | Blocks uniform candidate identity in `REQ-AOS-004`/`007` | AosCloud integration + Function Teams | D4 artifact contract |
| Effective service-update recipient derivation | FOTA pending component references are understood; equivalent SOTA proof needs qualification | AosCloud integration | D4 target contract |
| Combined-graph multi-owner enforcement | Native current behavior is not yet proven | AosEdge Platform Team + System Architecture | Before G3 implementation plan |
| Post-Apply component removal/downgrade/recovery | SOTA removal and pre-Apply revert do not prove committed FOTA rollback | AosEdge Platform Team + Platform Team | D4 rollback/recovery matrix |
| Native Service-to-FOTA admission | No implementing release exists | AosEdge Platform Team | Deferred until official release qualification |
| Native log POST/download permissions, offline and retention behavior | Product path exists but the demo API contract is unqualified | AosCloud integration | D4 log contract |
| Offline transition mechanism, authoritative state after no-content deprovision, Unit/Node deletion and retired-certificate behavior | The API's offline precondition is proven, but complete two-Unit retirement has not been executed | AosCloud integration + Demo Orchestration | D4 retirement contract before R0 implementation |

## Change Rules

- Editorial clarification preserves stable `REQ-AOS-*` IDs.
- A material semantic replacement receives a new ID and retires the old
  definition with a replacement link.
- A changed lifecycle authority, identity model, approval ownership, data
  direction or reset model follows the Level-C architecture cascade.
- New support in an AosEdge release changes `REQ-AOS-011` from `DEFERRED` only
  after official API evidence and qualification; documentation alone is not
  sufficient.
- If project-owned executable lifecycle logic enters this package, stable
  `UT-AOS-*` obligations are added before implementation.
