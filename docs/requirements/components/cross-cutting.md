<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross-Cutting Security and Operations Requirements

- Status: D3 design-reviewed
- Package: [`CR-CROSS`](../component-decomposition-and-interface-register.md#cr-cross)
- Version: 0.4
- Prepared: 2026-08-21
- Accepted: 2026-08-28
- Previous accepted package: Version 0.3
- Owner: System Architecture with Platform, Gateway, Function and Demo Solution owners
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Accepted D4 VISS trust decision: [D4-006 VISS Trust and Telemetry Profile](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Accepted D4 advisory decision: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Accepted D4 publication decision: [D4-010.3 Artifact Publication Credential Profile](../../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)
- Accepted D4 Cloud authority decision: [D4-011 Cloud Role and Action Matrix](../d4-decision-register.md#d4-011)

## Purpose

This package defines the security and operational invariants that must remain
true across several already accepted component packages. It does not introduce
a deployable component, a shared runtime daemon, a second identity provider, a
parallel policy database or a new lifecycle authority.

The package closes the seams between component owners: Aos service identity to
KUKSA authorization, per-Unit key custody, trusted Provider boundary, the
complete QM advisory path, native log evidence, run correlation, chronology,
targeted vehicle external-connectivity continuity and AosCore-enforced service-
tenant isolation. Each product owner retains its
implementation and tests; `CR-CROSS` adds common contract and integration
acceptance over those owner boundaries.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Cross-component invariants, shared negative matrices and qualification evidence |
| What this package does not own | Product logic, AosCore/AosCloud or KUKSA source, `CMP-KAC`, credentials, desired state, functional data or deployment approval |
| Intended result | Independent owners can evolve their components without widening authority, leaking secrets, misrepresenting vehicle external-connectivity state or breaking another tenant |
| Accountable lifecycle owner | System Architecture accepts the shared contract; each component owner implements its allocated part through its existing lifecycle |
| Primary repository or external source | No product repository; shared contract fixtures and qualification orchestration belong in `aosedge-sdv-demo` |

## Component Boundary

### In scope

- one authoritative Aos-to-KUKSA identity and permission chain;
- per-Unit signer/verifier lifecycle without artifact-baked secrets;
- role-bound artifact-publication credential custody without browser,
  container, VM, artifact or repository exposure;
- separation of trusted OEM Provider integration and functional-Service authority;
- defense-in-depth VDP checks plus authoritative Gateway QM containment;
- native operational-log evidence controls and redaction;
- consistent run, Unit, source and message correlation across surfaces;
- separate source, local-decision and Cloud-receipt chronology;
- one atomic Production Unit external-connectivity loss/restoration control
  that interrupts Unit-to-AosCloud and installed service-to-functional-backend
  paths together while presenter-to-AosCloud and the simulated in-vehicle
  network remain available; and
- independently approved service resource envelopes, with AosCore as the sole
  in-vehicle enforcement/monitoring authority, and one bounded Tire CPU-
  saturation proof in which Brake and the platform graph remain healthy.

### Out of scope

- changing upstream Eclipse KUKSA, AosCore or AosCloud;
- embedding an authorization helper in VDP or creating a local per-service policy store;
- replacing Aos IAM, Service Manager identity or native permission lifecycle;
- functional-safety certification, driver HMI, motion authority or a safety
  argument for the QM services;
- the deferred native AosCloud Service-to-FOTA VDP Component admission
  feature; released component-to-component and service-to-layer dependencies
  remain platform capabilities;
- product-specific algorithms, telemetry schemas, UI layout or lifecycle
  workflow already owned by another accepted package; and
- presenter-to-AosCloud or simulated in-vehicle connectivity-loss demo
  scenarios, and independently switched functional-backend faults;
- quantitative Cloud lifecycle timing or first-demo vehicle performance KPIs;
- any project/demo resource manager, scheduler or quota-enforcement service;
- Mac-local functional-backend isolation as evidence of AosCore enforcement;
  and
- aggregate quota enforcement across multiple services owned by one Service
  Provider; the current claim is one Aos-managed service instance per provider.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Aos Service Manager and IAM permission lifecycle | External AosEdge platform | Per-instance identity, `AOS_SECRET` and registered `kuksa` permissions are authoritative | No SOTA KUKSA credential is issued |
| Unmodified Eclipse KUKSA | Platform Team integration / upstream Eclipse | Accepted verifier, audience and path-level authorization | KUKSA access fails closed |
| KUKSA Authorization Compatibility helper | Platform Team / `CMP-KAC` | Separate removable fixed-resource IAM translation; no parallel identity/policy store and no telemetry proxy | Services remain not ready; no static-token fallback |
| Gateway QM advisory handler | Vehicle Gateway owner | Final deny-by-default typed non-safety boundary | Advisory is rejected with factual status |
| Native Aos logging path | AosCore/AosCloud | OEM Unit logs and SP1/SP2 Service logs are role-separated; request, status, result, deletion and offline behavior qualified; retention explicitly not exposed when absent from API | Evidence is unavailable or explicitly unqualified |
| Aos Service Manager/container runtime | External AosEdge platform | Enforces and monitors accepted service-instance quotas through its runtime/cgroup mechanisms | Tenant-isolation proof cannot be accepted |
| Owner service resource contracts | Brake and Tire service owners | D4 freezes independently approved quotas and application overflow/recovery behavior | Combined graph cannot be accepted |
| Artifact publication profiles | Platform, Function Team release owners and Demo Solution | D4-010.3 fixed `platform-oem`, `brake-sp1` and `tire-sp2` bindings with independent Cloud reconciliation | Sign/publish remains disabled or `UNCERTAIN`; OEM approval is never inferred |
| OEM delivery authority | OEM administration and Demo Solution | D4-011 separate `oem-delivery` context with `/users/me/` role/effective-permission preflight and authoritative post-read | Lifecycle mutation remains blocked or `UNCERTAIN`; publisher presence never satisfies delivery authority |

## Testability Boundary

`CR-CROSS` owns no executable product logic, so it defines no duplicate
`UT-CROSS-*` unit-test suite. Deterministic unit decisions remain in the
repositories that own them. This package instead requires:

1. exact reuse of accepted owner-package unit obligations;
2. versioned cross-component fixtures for identity, permissions, advisory,
   chronology, correlation, connectivity and resource contracts;
3. contract tests at every producer/consumer boundary; and
4. integration tests proving the complete negative path rather than assuming
   that two individually green components compose safely.

The shared fixture catalogue and qualification harness may live in
`aosedge-sdv-demo`, but must not reimplement product policy or become a runtime
dependency.

## Interface Summary

| Interface | Direction | Data or command | Failure behavior | Authority |
| --- | --- | --- | --- | --- |
| [`IF-AUTH-007`–`009`](../component-decomposition-and-interface-register.md#if-auth-007) | Service ↔ `CMP-KAC` ↔ Aos IAM | Named-resource/private-Unix-socket bootstrap, fixed TLS loopback `127.0.0.1:8090` native-IAM lookup, current registered permissions and atomic private-tmpfs short-lived JWT | Reject without token; no cached/static fallback, DNS/external IAM destination or KAC TCP listener; analytics never receives `AOS_SECRET` | Aos Service identity and current IAM result; mount/group/peer and fixed-loopback restrictions are defense in depth |
| [`IF-AUTH-010`](../component-decomposition-and-interface-register.md#if-auth-010) | Platform security substrate → `CMP-KAC`/KUKSA | Permission handler, protected signing operation and public verifier preparation | Not ready; no key bytes or privilege reuse | Per-Unit platform trust |
| [`IF-ADV-001`](../component-decomposition-and-interface-register.md#if-adv-001), [`IF-TIRE-002`](../component-decomposition-and-interface-register.md#if-tire-002), [`IF-ADV-002`–`005`](../component-decomposition-and-interface-register.md#if-adv-002) | QM services → KUKSA → VDP → VISS → Gateway | Typed Brake/Tire maintenance advisory and factual result | Fail closed at every boundary; Gateway is final authority | IAM/KUKSA scope, VDP contract, then Gateway QM policy |
| [`IF-OBS-001`](../component-decomposition-and-interface-register.md#if-obs-001) | OEM Software Delivery / Brake / Tire Dashboard ↔ AosCloud | Role-scoped Unit-log or Service-log request/status/result/file | Exact endpoint/owner filtering, verbatim state, explicit unavailable/failed state and bounded temporary cleanup | AosCloud request and file state while retained; API exposes no retention policy |
| [`IF-DEMO-001`](../component-decomposition-and-interface-register.md#if-demo-001) | Orchestrator → local actors | Run/role/source binding and session boundary | Ambiguity blocks the affected operation | Local run manifest plus authoritative Unit state |
| [`IF-FUNC-001`](../component-decomposition-and-interface-register.md#if-func-001), [`IF-TIRE-003`](../component-decomposition-and-interface-register.md#if-tire-003) | In-vehicle service → functional backend | Correlated bounded messages with original event time | Bounded queue/retry or explicit loss/degraded state | Function Team data contract |
| [`IF-LC-006`](../component-decomposition-and-interface-register.md#if-lc-006) | AosCore → VDP and services | Runtime lifecycle, readiness and resource enforcement | Explicit failed/degraded instance state | Unit actual state |
| [`IF-LC-001`](../component-decomposition-and-interface-register.md#if-lc-001), [`IF-LC-002`](../component-decomposition-and-interface-register.md#if-lc-002), [`IF-LC-007`](../component-decomposition-and-interface-register.md#if-lc-007) | Platform/Function release views → common native publication helper → AosCloud | Exact prepared candidate and fixed role-bound publication profile | Reject caller-selected profile/path/URL or candidate mismatch; reconcile ambiguity without blind retry | Technical publication identity and authoritative AosCloud re-read; no OEM Unit approval |
| [`IF-LC-005`](../component-decomposition-and-interface-register.md#if-lc-005), [`IF-LC-008`](../component-decomposition-and-interface-register.md#if-lc-008)–[`010`](../component-decomposition-and-interface-register.md#if-lc-010) | Software Delivery Dashboard → AosCloud | Active `oem-delivery` role/effective-permission preflight, exact confirmed lifecycle mutation and authoritative post-read | Wrong role/permission or ambiguous result blocks; no blind retry or server-idempotency claim | Owning-team acceptance plus separately authenticated OEM delivery authority; AosCloud remains system of record |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove each owner's local validator and state machine | External peers replaced by deterministic doubles | Yes, in owner packages; no duplicate `UT-CROSS-*` | Linked accepted `UT-*` obligations |
| Component | Prove each packaged component exposes the required security/operational behavior | Controlled fixtures and fake adjacent services | Yes | Owner-package component reports |
| Contract | Prove every producer/consumer agrees on identity, schema, error, time and limit semantics | Versioned cross-owner fixture catalogue | Yes | Cross-package conformance report and fixture digest |
| Integration | Prove layered enforcement and recovery with real adjacent components | Accepted Validation environment | Yes | Negative matrix, disconnect/reconnect, resource and log evidence |
| End-to-end | Prove audience claims without widening them | VU before identical PU promotion | Yes, allocated to `CR-E2E` | Stage and failure-path acceptance record |

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| [Native identity and least privilege (`REQ-CROSS-001`)](#req-cross-001) | Preserve one Aos-authoritative service identity and exact KUKSA permissions | Unit, Contract, Integration | D3 design-reviewed |
| [Per-Unit KUKSA trust lifecycle (`REQ-CROSS-002`)](#req-cross-002) | Protect one signer per Unit provisioning lifecycle, prepare only its public verifier and bound JWT issue/refresh/retirement | Unit, Component, Contract, Integration | D4-010.1 decided; implementation open |
| [Trusted Provider and Service-authority separation (`REQ-CROSS-010`)](#req-cross-010) | Keep trusted OEM Provider integration unreachable through functional Service credentials | Contract, Integration, Review | D3 design-reviewed |
| [Role-bound protected artifact publication (`REQ-CROSS-011`)](#req-cross-011) | Keep Platform, Brake and Tire technical-publication credentials non-interchangeable and outside product/runtime boundaries | Unit, Contract, Integration, Audit | D4-010.3 decided; implementation open |
| [End-to-end QM advisory containment (`REQ-CROSS-004`)](#req-cross-004) | Reject every unauthorized or unsafe advisory at layered boundaries | Unit, Contract, Integration, End-to-end | D3 design-reviewed |
| [Controlled native-log evidence (`REQ-CROSS-005`)](#req-cross-005) | Present role-separated OEM/SP logs without secrets, false retention or a second archive | Unit, Contract, Integration | D4-014 design accepted; live qualification open |
| [Cross-surface run correlation (`REQ-CROSS-006`)](#req-cross-006) | Bind facts to the exact run, role, Unit and source without global history | Unit, Contract, Integration, End-to-end | D4-024 design reviewed; implementation/live qualification open |
| [Separated on-board and Cloud chronology (`REQ-CROSS-007`)](#req-cross-007) | Preserve event, decision and synchronization times without a false latency claim | Unit, Contract, Integration, End-to-end | D4-024 design reviewed; implementation/live qualification open |
| [Targeted vehicle external-connectivity continuity (`REQ-CROSS-008`)](#req-cross-008) | Keep the installed graph active while one atomic fault interrupts AosCloud and functional-backend paths, then reconnect and synchronize | Contract, Integration, End-to-end | D3 design-reviewed |
| [AosCore service-tenant isolation (`REQ-CROSS-009`)](#req-cross-009) | Cap a prepared Tire CPU load at its own quota while Brake and the platform remain healthy | Unit, Component, Contract, Integration, End-to-end | D3 design-reviewed |

## Detailed Requirements

### Native identity and least privilege

<a id="req-cross-001"></a>

- ID: `REQ-CROSS-001`
- Statement: The accepted component graph shall derive each running SOTA instance's KUKSA authority from its current Aos identity and registered path/mode permissions through fixed-resource `CMP-KAC` bootstrap, and issue no caller-selected, broader or reusable authority.
- Parents: [least-privilege identities (`SYS-SEC-001`)](../system-requirements-and-traceability.md#sys-sec-001) and [current-release KUKSA authorization compatibility (`SYS-SEC-008`)](../system-requirements-and-traceability.md#sys-sec-008)
- Flow: [Aos-to-KUKSA credential flow (`AF-X-AUTH`)](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: [`CMP-AOS-CORE`](../component-decomposition-and-interface-register.md#cmp-aos-core), [`CMP-KAC`](../component-decomposition-and-interface-register.md#cmp-kac), [`CMP-KUKSA`](../component-decomposition-and-interface-register.md#cmp-kuksa), [`CMP-BHS`](../component-decomposition-and-interface-register.md#cmp-bhs), [`CMP-TIRE`](../component-decomposition-and-interface-register.md#cmp-tire)
- Interfaces: `IF-AUTH-007` through `IF-AUTH-009`
- State: D3 design-reviewed; target integration

#### Acceptance criteria

1. Exact registered Brake and Tire mode `r` produces only `read:<path>` and `rw` only `actuate:<path>`; `w`, wildcards and provider actions produce no token.
2. Invalid/stale secret, caller-selected authority, unknown mode, malformed path, removed permission or cross-Service identity produces no token; no partial trimming is allowed.
3. No component stores a parallel service identity/policy database or persists/logs the secret or JWT.

### Per-Unit KUKSA trust lifecycle

<a id="req-cross-002"></a>

- ID: `REQ-CROSS-002`
- Statement: Successful provisioning shall give each Unit one unique
  non-exported RSA signer in the dedicated `kuksa-jwt` PKCS#11 token and shall
  atomically prepare only its public verifier before `CMP-KAC` and KUKSA
  start. Helper JWTs shall be `RS256` tokens with fixed audience `kuksa.val`,
  300-second expiry, renewal at 180 seconds and exact path permissions; every
  successful renewal shall reconnect/recreate KUKSA subscriptions with the
  replacement token. The pinned KUKSA is not
  claimed to enforce `iss`. Permission removal shall prevent renewal, the
  first demo shall not perform live rotation, the next provisioning lifecycle
  shall create a new signer, and R0 shall destroy the retired signer with the
  VM overlay. No private key, shared static verifier or reusable token shall
  enter a Factory Image, FOTA/SOTA artifact, browser, container, command line
  or log.
- Parent: [KUKSA verifier and token lifetime (`SYS-SEC-004`)](../system-requirements-and-traceability.md#sys-sec-004)
- Flow: [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: `CMP-FACTORY`, `CMP-AOS-CORE`, `CMP-KAC`, `CMP-KUKSA`
- Interface: `IF-AUTH-010`
- State: D4-010.1 decided; implementation and live qualification remain open

#### Acceptance criteria

1. VU and PU expose different public-key fingerprints; same-Unit JWTs pass and
   cross-Unit JWTs fail.
2. Missing/malformed preparation state prevents `CMP-KAC`/KUKSA startup; expired,
   wrong-audience, wrong-signature, excessive-scope and non-renewable
   credentials fail without data/advisory side effects.
3. Reprovisioning changes the signer, and deprovision plus reconciled R0
   overlay discard makes the old signer unusable; no live-rotation claim is
   made.
4. Artifact, filesystem, process, command, environment and log inspection
   finds no private key, shared static verifier or reusable token.

### Retired: Dynamic Provider authority

<a id="req-cross-003"></a>

- ID: `REQ-CROSS-003`
- Disposition: Retired by Version 0.4 and replaced by
  [`REQ-CROSS-010`](#req-cross-010). Dynamic Provider IAM/JWT and malicious or
  substituted Provider containment are outside the first-demo claim.
- Historical parent: [`SYS-SEC-005`](../system-requirements-and-traceability.md#sys-sec-005)

### Trusted Provider and Service-authority separation

<a id="req-cross-010"></a>

- ID: `REQ-CROSS-010`
- Statement: The VDP Provider shall be treated as an OEM-qualified trusted
  platform integration with a fixed bounded KUKSA-side connection mechanism.
  Brake and Tire Service bootstrap/JWT material shall never grant, inherit or
  emulate Provider publication authority. The first demo shall explicitly
  avoid claims of dynamic Provider IAM/JWT, per-component attestation or
  containment of a malicious/substituted Provider.
- Parents: [least-privilege identities (`SYS-SEC-001`)](../system-requirements-and-traceability.md#sys-sec-001) and [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003)
- Flow: [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: `CMP-VDP`, `CMP-KUKSA`, `CMP-KAC`, `CMP-BHS`, `CMP-TIRE`
- State: D3 design-reviewed

#### Acceptance criteria

1. The exact Provider/configuration is qualified on both Unit roles against the accepted VDP data/advisory contract.
2. Brake/Tire `AOS_SECRET`, private JWT and bootstrap resources cannot be reused as Provider authority.
3. Documentation and dashboard evidence state the trusted-Provider assumption and do not claim malicious-Provider containment.

### Role-bound protected artifact publication

<a id="req-cross-011"></a>

- ID: `REQ-CROSS-011`
- Statement: Current-demo technical artifact publication shall use exactly
  three non-interchangeable profiles: `platform-oem` for VDP v1-v3 FOTA,
  `brake-sp1` for Brake Health v1-v3 SOTA and `tire-sp2` for Tire Health v1.0
  SOTA. One session-scoped non-root native helper may implement them, but each
  dashboard surface shall be pre-bound to one profile and shall never supply a
  profile, credential path, arbitrary candidate path or Cloud URL. The current
  `aos-signer` 2.0.1 path shall keep one mode-`0600` local passwordless PKCS#12
  per profile outside Git, browser, containers, VMs, artifacts and logs. Only
  an independent AosCloud re-read may establish `PUBLISHED`; ambiguity shall
  become `UNCERTAIN` without blind retry, and publication shall never perform
  OEM deployment approval.
- Parent: [role-bound protected publication (`SYS-REL-011`)](../system-requirements-and-traceability.md#sys-rel-011)
- Flow: [`AF-X-RELEASE`](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: `CMP-SW-DASH`, `CMP-BRAKE-DASH`, `CMP-TIRE-DASH`, `CMP-ORCH`,
  `CMP-AOS-CLOUD`
- Interfaces: `IF-LC-001`, `IF-LC-002`, `IF-LC-007`
- Executable contract: [Artifact Publication Credential Profile 1.0.0](../../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)
- State: D4-010.3 decided; exact helper request/result transport and Cloud
  reconciliation lookup remain implementation gates

#### Acceptance criteria

1. Wrong profile, artifact type, candidate identity, caller-selected path/URL
   or missing local custody prerequisite fails before signing.
2. No private key, PKCS#12, raw tool output or credential selector reaches a
   dashboard, container, VM, artifact, repository or log.
3. `PUBLISHED` binds the exact prepared/signed/Cloud identity chain only after
   authoritative re-read; timeout/interruption never causes blind retry.
4. Successful technical publication exposes no Unit target or approval side
   effect and cannot replace owning-team acceptance or OEM authorization.

### End-to-end QM advisory containment

<a id="req-cross-004"></a>

- ID: `REQ-CROSS-004`
- Statement: The Brake and Tire advisory chain shall permit only their two D4-008 schema-bound non-safety maintenance Request targets through KUKSA and VDP defense in depth, while the Gateway independently validates identity/schema/size/value/freshness/lease/rate/replay, authoritatively rejects arbitrary VSS writes, cross-service targets, motion and safety-critical operations, and publishes the matching factual read-only Gateway Status.
- Parents: [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003) and [QM/Gateway containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Flow: [QM advisory containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Components: `CMP-BHS`, `CMP-TIRE`, `CMP-KUKSA`, `CMP-VDP`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH`
- Interfaces: `IF-ADV-001` through `IF-ADV-005` and `IF-TIRE-002`
- Executable contract: [Typed QM Advisory Profile 1.0.2](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- State: D3 design-reviewed; D4-008 contract accepted, implementation and qualification open

#### Acceptance criteria

1. Each accepted typed Brake/Tire request reaches only the correct Gateway target and produces matching `APPLIED`/`CLEARED` factual status; broker/protocol success alone is not accepted.
2. Wrong caller/path/endpoint, malformed/oversized/noncanonical payload, enum, freshness, lease, rate, correlation, replay or sequence rollback is rejected without an unintended write; explicit clear, auto-expiry and restart idempotency are proved.
3. Every throttle, brake, steer, gear, motion and safety-critical request from the QM route is rejected even if an upstream check is deliberately bypassed in a test.

### Controlled native-log evidence

<a id="req-cross-005"></a>

- ID: `REQ-CROSS-005`
- Statement: Cross-component operational evidence shall use the native AosCore/AosCloud log path. OEM system/VDP evidence shall use `unit-logs` through `oem-delivery`, while Brake and Tire service/crash evidence shall use `service-logs` through distinct SP1/SP2 operational contexts and matching Function Dashboards. Requests shall preserve verbatim Cloud states, structured allowlisted redaction and source time; temporary downloads shall be bounded and removed, and no demo component shall create a second archive. Because the current API does not expose retention policy, the demo shall state that fact rather than claim a duration.
- Parent: [operational log controls (`SYS-OBS-003`)](../system-requirements-and-traceability.md#sys-obs-003)
- Flow: [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, `CMP-SW-DASH`, `CMP-BRAKE-DASH`, `CMP-TIRE-DASH` and every emitting owner
- Interface: `IF-OBS-001`
- State: D3 design-reviewed; D4-014 design accepted, live identifier/permission/state/file/deletion/offline qualification remains required

#### Acceptance criteria

1. OEM Unit-log and SP1/SP2 Service-log requests cannot cross their endpoint, owner or dashboard boundary and present documented Cloud states without invented success/timeout labels.
2. Secret, token, private-certificate, VIN and unrestricted or high-rate raw-telemetry fixtures do not appear in accepted logs or dashboard previews.
3. Temporary downloads are bounded and deleted, while Cloud-owned audit/log state is not silently copied; R0 deletes only exact current-run request IDs and proves their detail/file unavailable afterward.

### Cross-surface run correlation

<a id="req-cross-006"></a>

- ID: `REQ-CROSS-006`
- Statement: Every audience-visible functional or operational fact shall be attributable before provisioning to one bounded start time and overlay role, and afterward to the exact VU/PU Unit ID, role, source generation/frame evidence and same bounded session window; successful R0 shall remove demo-owned run data without creating a historical run database.
- Parent: [per-run correlation (`SYS-OBS-004`)](../system-requirements-and-traceability.md#sys-obs-004)
- Flows: [one source/two roles (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source) and [`AF-X-OBS`](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: `CMP-ORCH`, `CMP-GW`, `CMP-BRAKE-BE`, `CMP-TIRE-BE`, all dashboards
- Interfaces: `IF-DEMO-001`, `IF-VEH-004`–`006`, `IF-FUNC-001`/`002`, `IF-TIRE-003`/`004`
- State: D4-024 design reviewed; implementation and live qualification remain open

#### Acceptance criteria

1. Equal event IDs from VU and PU or two Function Teams cannot collide because Unit role/source binding remains explicit.
2. Missing, conflicting, stale or cross-run correlation prevents a success/accepted presentation.
3. After successful R0, functional dashboards are empty for the retired run while AosCloud-owned lifecycle/audit history remains outside demo storage.

### Separated on-board and Cloud chronology

<a id="req-cross-007"></a>

- ID: `REQ-CROSS-007`
- Statement: Brake and Tire data products and advisory evidence shall preserve distinct source-event, local-decision/advisory, Gateway receipt, backend receipt and synchronization times, including delayed reconnect delivery, without presenting Cloud delivery as part of the on-board decision path or as a first-demo latency benchmark.
- Parent: [separate on-board and Cloud chronology (`SYS-TIM-002`)](../system-requirements-and-traceability.md#sys-tim-002)
- Flows: [`AF-X-QM`](../../architecture/demo-scenario-architecture-flows.md#af-x-qm) and owner-package backend transport/recovery flows
- Components: Gateway, both services, both functional backends and dashboards
- Interfaces: `IF-ADV-005`, `IF-FUNC-001`, `IF-TIRE-003`
- State: D4-024 design reviewed; implementation and live qualification remain open

#### Acceptance criteria

1. Normal online evidence preserves an internally consistent causal order without requiring synchronized receipt times.
2. During the vehicle external-connectivity proof, delayed functional messages preserve original event/decision times and record later receipt/synchronization separately.
3. Missing/inconsistent chronology is explicit and no UI derives a Cloud-operation or vehicle KPI from it.
4. The accepted evidence is explicitly limited to demo causal linkage and reconnect behavior; it makes no production clock-synchronization, worst-case latency, real-time, network or safety claim.

### Targeted vehicle external-connectivity continuity

<a id="req-cross-008"></a>

- ID: `REQ-CROSS-008`
- Statement: One stateful demo control shall atomically block or restore the currently selected Validation or Production Unit's external vehicle connectivity; the normative `G4/X-OFFLINE` presentation uses PU. D4-022.1 shall change only that Unit's external QEMU plane. The disconnected state shall block both selected-Unit-to-AosCloud and installed service-to-functional-backend paths while the other VM, presenter-to-AosCloud, the simulated in-vehicle QEMU plane and the installed on-board graph remain available. The helper shall set an exact desired state rather than toggle, persist intent before mutation, never treat a lost response as success or retry it blindly, reconcile after restart, and compensate a partial/forbidden effect only to the last confirmed state. The Software Delivery Dashboard shall show authoritative offline/online state, reachable Function Dashboards shall show delayed/offline and later synchronized results, local inference/advisory shall continue, and reconnect shall use the same Unit and installed graph without reprovisioning, reinstalling or restarting. No separate per-channel fault control shall be exposed.
- Parent: [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](../system-requirements-and-traceability.md#sys-obs-007)
- Flow: [targeted vehicle external-connectivity loss (`AF-X-OFFLINE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, installed `CMP-VDP`/services, `CMP-SW-DASH`, and qualification orchestration
- Interfaces: `IF-LC-004`, `IF-LC-005`, `IF-LC-006`, `IF-OBS-001`
- State: D3 design-reviewed; allocation confirmed by `CROSS-D3`

#### Acceptance criteria

1. One visible control transition proves that the selected Unit's AosCloud and all installed service-to-functional-backend traffic are blocked together; partial or independently switched channel states are rejected. The other VM, presenter-to-AosCloud and simulated in-vehicle connections remain available.
2. AosCloud reports the selected Unit offline and affected lifecycle/log actions unavailable, while a deterministic CARLA event still reaches local inference, the advisory chain and Engineering Telematics Dashboard; reachable Function Dashboards receive no new result and show delayed/offline state. The normative presentation selects PU.
3. One restore transition makes AosCloud report the same Unit and installed versions online without provisioning, reinstall or service/provider restart and synchronizes bounded functional messages idempotently with original and receipt times distinct; no presenter-loss or in-vehicle-loss claim is shown.
4. Duplicate achieved-state requests are probed no-ops; lost responses and restarts reconcile before any explicit idempotent reissue, and failed/unproven compensation remains `FAILED/PARTIAL` rather than fabricating success.

### AosCore service-tenant isolation

<a id="req-cross-009"></a>

- ID: `REQ-CROSS-009`
- Statement: Brake Health and Tire Health shall carry independently approved service quotas in their accepted Aos metadata, while AosCore/Service Manager remains the sole in-vehicle enforcement and monitoring authority. The first audience proof shall use the Tire Function Dashboard and its backend to deliver only one fixed, identity-bound, idempotent start/stop profile over the actual Tire Service's existing outbound backend route. At most one worker shall run inside the actual Tire Aos-managed cgroup, with no caller-selected load parameters, separate load container, administrative bypass or persistence/resume across restart; backend-lease loss and a 180-second ceiling stop it. AosCore shall cap that instance and expose authoritative usage/status or alert evidence through AosCloud; at the same time Brake Health shall remain ready without restart and shall process the deterministic CARLA event, while VDP, KUKSA, Gateway and AosCore remain healthy. Stopping the load shall return Tire to normal without reinstall or restart. Function Team control status is not quota proof, and no project resource manager shall be added.
- Parent: [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](../system-requirements-and-traceability.md#sys-res-001)
- Flows: [AosCore tenant isolation (`AF-TIRE-RES`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-res) and [common release/runtime enforcement (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, `CMP-TIRE`, `CMP-BHS`, `CMP-VDP`, `CMP-KUKSA`, `CMP-GW`, `CMP-SW-DASH`, `CMP-ORCH`
- Interfaces: `IF-LC-005`, `IF-LC-006`, `IF-DEMO-001`
- State: D3 design-reviewed; D4-023 design reviewed through D4-023.6; implementation and the complete live qualification dossier remain acceptance gates

#### Acceptance criteria

1. The exact approved Brake/Tire metadata and actual AosCore instance state
   show distinct quotas; the Software Delivery Dashboard reads but cannot set
   or enforce them.
2. The actual Tire instance reaches 100% of its approved CPU quota and cannot
   consume beyond the qualified tolerance; AosCore reports the cap and factual
   instance state/monitoring or alert evidence.
3. During the cap, Brake processes the deterministic event/advisory without
   restart or degraded readiness and VDP, KUKSA, Gateway and AosCore remain
   healthy. Stopping the load returns Tire to normal without reinstall or
   restart.
4. Memory, storage, PID and network boundaries remain qualification evidence
   rather than extra audience controls. Mac-local backends are not presented
   as AosCore tenants, and no aggregate multi-service-per-provider claim is
   made.
5. The audience view uses fresh exact-instance AosCloud monitoring in DMIPS;
   a quota alert is supplementary. A separately labelled sanitized read-only
   cgroup `cpu.max`/`cpu.stat` record proves technical enforcement and is bound
   to the exact Factory Image, AosCore, Tire artifact, signed configuration and
   Node DMIPS baseline. Service/backend control status is never proof, and
   missing, stale or mismatched evidence blocks `PASS`.
6. Baseline, saturation and recovery each require three consecutive fresh
   samples. Exact freshness, DMIPS bands and runtime rounding tolerance come
   from the bound qualification profile, never an arbitrary percentage.
   Mapping/cap, restart, peer/platform or recovery failure is `FAIL`;
   incomplete evidence is `INCONCLUSIVE`; an offline/wrong-version/stale-profile
   start is `NOT_READY`. Brake completion uses the existing scenario timeout,
   not a new latency KPI.

## Reused Owner-Package Unit Obligations

No `UT-CROSS-*` identifiers are created because this package owns no executable
decision. The following accepted obligations remain blocking in their owner
repositories and are composed by the cross-package contract/integration gate.

| Cross requirement | Reused unit obligations |
| --- | --- |
| `REQ-CROSS-001` | [`UT-KAC-001`–`006`](kuksa-authorization-compatibility.md#ut-kac-001), [`UT-BHS-013`](brake-health-service.md#ut-bhs-013), [`UT-TIRE-013`](tire-health-service.md#ut-tire-013) |
| `REQ-CROSS-002` | [`UT-FACTORY-009`](factory-substrate.md#ut-factory-009), [`UT-KAC-003`–`007`](kuksa-authorization-compatibility.md#ut-kac-003) |
| `REQ-CROSS-010` | [`UT-VDP-008`](vehicle-data-platform.md#ut-vdp-008), [`UT-KAC-010`](kuksa-authorization-compatibility.md#ut-kac-010), [`UT-BHS-001`](brake-health-service.md#ut-bhs-001), [`UT-TIRE-001`](tire-health-service.md#ut-tire-001) |
| `REQ-CROSS-011` | [`UT-DEMO-015`](demo-orchestration.md#ut-demo-015), [`UT-DEMO-017`](demo-orchestration.md#ut-demo-017), [`UT-BRAKE-CLOUD-003`](brake-health-cloud.md#ut-brake-cloud-003), [`UT-BRAKE-CLOUD-014`](brake-health-cloud.md#ut-brake-cloud-014), [`UT-TIRE-CLOUD-003`](tire-health-cloud.md#ut-tire-cloud-003), [`UT-TIRE-CLOUD-010`](tire-health-cloud.md#ut-tire-cloud-010) |
| `REQ-CROSS-004` | [`UT-VDP-003`](vehicle-data-platform.md#ut-vdp-003), [`UT-GATEWAY-010`](vehicle-gateway.md#ut-gateway-010), [`UT-GATEWAY-011`](vehicle-gateway.md#ut-gateway-011), [`UT-BHS-007`](brake-health-service.md#ut-bhs-007), [`UT-TIRE-007`](tire-health-service.md#ut-tire-007) |
| `REQ-CROSS-005` | [`UT-DEMO-011`](demo-orchestration.md#ut-demo-011), [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-010`](tire-health-service.md#ut-tire-010) |
| `REQ-CROSS-006` | [`UT-DEMO-001`](demo-orchestration.md#ut-demo-001), [`UT-GATEWAY-003`](vehicle-gateway.md#ut-gateway-003), [`UT-BRAKE-CLOUD-009`](brake-health-cloud.md#ut-brake-cloud-009), [`UT-TIRE-CLOUD-007`](tire-health-cloud.md#ut-tire-cloud-007) |
| `REQ-CROSS-007` | [`UT-GATEWAY-012`](vehicle-gateway.md#ut-gateway-012), [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-010`](tire-health-service.md#ut-tire-010), [`UT-BRAKE-CLOUD-008`](brake-health-cloud.md#ut-brake-cloud-008), [`UT-TIRE-CLOUD-006`](tire-health-cloud.md#ut-tire-cloud-006) |
| `REQ-CROSS-008` | [`UT-VDP-007`](vehicle-data-platform.md#ut-vdp-007), [`UT-BHS-008`](brake-health-service.md#ut-bhs-008), [`UT-TIRE-006`](tire-health-service.md#ut-tire-006), [`UT-BRAKE-CLOUD-008`](brake-health-cloud.md#ut-brake-cloud-008), [`UT-TIRE-CLOUD-006`](tire-health-cloud.md#ut-tire-cloud-006), [`UT-DEMO-005`](demo-orchestration.md#ut-demo-005), [`UT-DEMO-011`](demo-orchestration.md#ut-demo-011), [`UT-DEMO-018`](demo-orchestration.md#ut-demo-018); AosCore/AosCloud behavior uses the accepted external-component test exception |
| `REQ-CROSS-009` | [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-009`](tire-health-service.md#ut-tire-009), [`UT-DEMO-019`](demo-orchestration.md#ut-demo-019); AosCore/AosCloud enforcement and monitoring use the accepted external-component test exception |

## Verification Traceability

| Requirement | Unit proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- |
| `REQ-CROSS-001` | Reused owner obligations | `IF-AUTH-007`–`009` conformance | Real Service Manager/IAM, `CMP-KAC`, both services and KUKSA | `CR-E2E` G2/T1 authorization |
| `REQ-CROSS-002` | Reused owner obligations | JWT/trust/key-custody profile | Independent VU/PU signer/verifier lifecycle | `CR-E2E` issue/expiry/revocation |
| `REQ-CROSS-010` | Reused owner obligations | Trusted Provider/Service separation contract | Real trusted Provider connection plus SOTA credential-reuse negatives | `CR-E2E` G1/G3 readiness under the declared trust assumption |
| `REQ-CROSS-011` | Reused owner obligations | D4-010.3 profile/custody/helper conformance | Three fixed profile paths, credential-exclusion proof and authoritative Cloud reconciliation | `AT-E2E-003` publication/approval separation |
| `REQ-CROSS-004` | Reused owner obligations | Full advisory positive/negative matrix | Real KUKSA→VDP→Gateway chain with bypass injection | G4/T1 accepted and rejected advisories |
| `REQ-CROSS-005` | Reused owner obligations | Log API/redaction/retention contract | Scoped native request/result/download/delete | Operational evidence view |
| `REQ-CROSS-006` | Reused owner obligations | Correlation-field and cleanup contracts | Sequential VU/reset/PU plus both backends | Cross-surface evidence and R0 |
| `REQ-CROSS-007` | Reused owner obligations | Timestamp semantics and delayed-delivery fixtures | Owner-qualified backend delay/reconnect correlation | Local advisory versus delayed Cloud result |
| `REQ-CROSS-008` | Reused owner obligations plus external-platform exception | Atomic fault scope, state and synchronization contract | PU external-connectivity loss, local continuity, backend delay/synchronization and same-Unit reconnect | One accepted G4 offline/online scenario |
| `REQ-CROSS-009` | Reused owner obligations plus external-platform exception | Approved service metadata, load-control and quota/monitoring evidence schemas | Actual Tire cgroup CPU cap plus concurrent Brake/platform continuity | `AF-TIRE-RES` bounded audience proof and clean recovery |

## Cross-Cutting Constraint Matrix

| Concern | Required invariant | Primary enforcement | Independent proof |
| --- | --- | --- | --- |
| Identity | One Aos identity/permission authority | Service Manager/IAM + removable `CMP-KAC` translation | Fixed-resource, exact-scope and cross-Service negatives |
| Secret custody | No artifact-baked or exposed private material | Per-Unit platform-protected operation | Image/package/process/log scans |
| Artifact publication | Fixed non-interchangeable Platform/Brake/Tire profiles; current local PKCS#12 readable only by the native helper; publication is not approval | D4-010.3 helper boundary plus AosCloud authoritative re-read | Wrong-profile/path/URL/candidate negatives, custody scan, interruption reconciliation and no-approval-side-effect proof |
| OEM delivery actions | Publisher identity never becomes delivery authority; exact D4-011 `oem-delivery` role/permission is current for every mutation | `/users/me/` preflight plus AosCloud action and authoritative post-read | Wrong-role/missing-permission/error-class/response-loss fixtures and no-blind-retry proof |
| Provider boundary | Functional identity never becomes Provider authority | Trusted OEM Provider integration separated from Service bootstrap/JWT | Credential-reuse negatives and explicit first-demo trust claim |
| QM containment | No arbitrary or motion/safety operation | Gateway final boundary | Upstream-bypass negative matrix |
| Logs/privacy | Native scoped evidence only | AosCore/AosCloud + emitting owners | Redaction, retention and bounded-download qualification |
| Correlation | Exact run/role/Unit/source binding | Orchestrator and producer contracts | Cross-Unit/cross-team collision cases |
| Chronology | Event/local/receipt/sync times remain distinct | Message contracts and dashboards | Delayed/out-of-order reconnect cases |
| Vehicle external connectivity | One control changes only the selected VU/PU external QEMU plane and interrupts its AosCloud/service-backend paths together; the other VM, presenter and in-vehicle plane remain available; normative presentation uses PU | Demo Orchestrator/native-helper fixed QMP operation, AosCloud/AosCore state and Function Team queues/backends | Exact selected-role/netdev proof, local advisory, delayed dashboards, synchronization and same-Unit reconnect |
| Service resources | AosCore is the sole in-vehicle enforcement/monitor authority; applications declare quotas and own bounded behavior | Aos Service Manager/container runtime/cgroups | Tire CPU cap, authoritative Cloud evidence, concurrent Brake event and healthy platform graph |

## D3 Review Decisions

| Decision | Proposed resolution | Review state |
| --- | --- | --- |
| `CROSS-D1` — Package nature | `CR-CROSS` is a no-code assurance package, not a deployable component, shared runtime service, identity provider, policy store or product repository | **Confirmed 2026-08-20** |
| `CROSS-D2` — Test ownership | Reuse owner-package unit obligations rather than duplicate them as `UT-CROSS-*`; keep shared versioned fixtures and orchestration in `aosedge-sdv-demo`; prove composition through contract/integration gates and pass their evidence to `CR-E2E` without duplicating the negative matrix | **Confirmed 2026-08-20** |
| `CROSS-D3` — Connectivity allocation | The only deliberate first-demo fault is one atomic loss of Production Unit external connectivity: Unit-to-AosCloud and installed service-to-functional-backend paths are interrupted/restored together by one stateful control; presenter-to-AosCloud and simulated in-vehicle links remain available; separate per-channel switches are prohibited | **Confirmed 2026-08-20** |
| `CROSS-D4` — Resource allocation | Use one prepared bounded CPU load inside the actual Tire instance; AosCore/Service Manager alone enforces and monitors its approved quota; Brake is the healthy control tenant. The Dashboard only presents authoritative state. Mac-local backends and aggregate multi-service-per-provider quotas are outside the claim; memory/storage/PID/network limits remain qualification evidence | **Confirmed 2026-08-20** |

## Open D4 Gates

| Gate | Impact | Owner |
| --- | --- | --- |
| Implement and qualify the accepted D4-027.1–.6 fixed-resource IAM lookup, non-widening permission mapping, private JWT delivery/timing and D4-010.1 per-Unit signer/verifier lifecycle | `REQ-CROSS-001`, `REQ-CROSS-002` | Platform Team + Aos IAM/security owner |
| Implement and qualify the complete accepted D4-027.7/.8 trustworthy-time, retry, rate, queue, process-resource and redaction envelope | `REQ-CROSS-001`, `REQ-CROSS-002` | Platform Team + Aos security owner |
| Exact trusted Provider connection/configuration qualification | `REQ-CROSS-010`; dynamic Provider IAM/JWT is not a first-demo gate | Platform Team |
| Exact common publication-helper request/result transport and AosCloud reconciliation lookup | `REQ-CROSS-011`; D4-010.3 profile/custody/state semantics are accepted | Demo Solution + Platform/Function Team release owners + AosCloud integration |
| Typed Brake/Tire targets, values, correlation, freshness, rate and replay bounds | `REQ-CROSS-004` | Gateway + Platform + Function Teams |
| Native log API roles, retention, deletion, offline and redaction behavior | `REQ-CROSS-005` | AosCloud integration + emitting owners |
| Implement and live-qualify the complete design-reviewed D4-024 correlation, chronology, sanitized projection, ordering/anomaly and qualification contract | `REQ-CROSS-006`, `007` | Demo Solution + Gateway + Function Teams |
| Atomic PU external-connectivity control, dual-path fault mechanism, excluded-path probes, functional-message synchronization and same-Unit reconnect contract | `REQ-CROSS-008` | Demo Solution + AosCloud and both Function Team integrations |
| Implement and live-qualify design-reviewed D4-023, including profile characterization/freeze, two independent VU passes, fault matrix, one PU rehearsal and sanitized retained dossier | `REQ-CROSS-009` | AosCore integration + both Function Teams + Demo Solution |
| Versioned shared fixture catalogue and conformance harness layout | All contract proofs | System Architecture + repository owners |

## Package Acceptance and Version 0.4 Delta

The package is ready for D3 acceptance when:

1. all four review decisions are confirmed;
2. every requirement maps to accepted owner-package obligations and a named
   cross-component contract/integration proof;
3. no new component, runtime service, identity provider, policy store,
   authority or product repository is created;
4. security enforcement remains layered and the Gateway remains the final QM
   boundary;
5. external components are qualified by contract/integration evidence rather
   than project-owned unit tests;
6. resource, targeted vehicle-connectivity, chronology, correlation and log behaviors retain one
   primary owner per fact and failure;
7. open D4 values are visible and no target behavior is presented as current;
8. the documentation quality gate passes.

Version 0.4 was design-reviewed on 2026-08-28. It moves Service authorization
from VDP to `CMP-KAC`, replaces retired authorization interfaces, retires
dynamic Provider authorization, adds `REQ-CROSS-010`, and records the accepted
D4-010.3 role-bound artifact-publication invariant as `REQ-CROSS-011`. All QM,
observability, connectivity, chronology and resource-isolation requirements
remain unchanged. Acceptance authorizes the shared architectural requirement
baseline only. It does not authorize implementation, repository creation,
signing, AosCloud calls, VM operations, provisioning, CARLA control or data
deletion.

## D3 Acceptance Record

Version 0.1 was accepted on 2026-08-20 after all four review decisions were
confirmed. In particular, `CROSS-D4` keeps AosCore/Service Manager as the sole
in-vehicle quota-enforcement and monitoring authority. The first audience
proof drives the actual Tire Health service instance to its independently
approved CPU quota while Brake Health processes the deterministic CARLA event
without restart and the shared platform remains healthy. The Demo Orchestrator
only starts and stops a prepared bounded in-instance load; it never sets or
enforces quotas. Mac-local backends and aggregate multi-service-per-provider
quota enforcement are explicitly outside the claim.

Version 0.4 was accepted as the current architectural requirement baseline on
2026-08-28. It does not authorize implementation, signing, AosCloud mutation,
VM operations, provisioning, CARLA control or data deletion.

The same-day native-IAM transport correction preserves the package version and
authority model. Cross-component qualification now proves that KAC's only
`AF_INET` use is fixed TLS loopback `127.0.0.1:8090`, while DNS, external IP
and any KAC TCP listener remain denied.

## Change Rules

- Editorial clarification preserves stable `REQ-CROSS-*` IDs.
- A material semantic replacement receives a new ID and retains the prior
  mapping in a retired section.
- A changed authority, lifecycle, trust boundary, data direction or component
  follows the Level-C architecture cascade before this package changes.
- A changed shared behavior inside accepted boundaries follows the Level-B
  cascade and updates every affected owner requirement, test, fixture and
  evidence link together.
- This package may reference owner tests but never silently reassign their
  implementation ownership.
