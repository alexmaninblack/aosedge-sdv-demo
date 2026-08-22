<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross-Cutting Security and Operations Requirements

- Status: D3 design-reviewed
- Package: [`CR-CROSS`](../component-decomposition-and-interface-register.md#cr-cross)
- Version: 0.3
- Prepared: 2026-08-21
- Accepted: 2026-08-20
- Owner: System Architecture with Platform, Gateway, Function and Demo Solution owners
- Architecture input: [High-Level Architecture 1.4](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 1.9](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 1.8](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 1.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 1.1](../component-decomposition-and-interface-register.md)
- Accepted D4 VISS trust decision: [D4-006 VISS Trust and Telemetry Profile](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Accepted D4 advisory decision: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)

## Purpose

This package defines the security and operational invariants that must remain
true across several already accepted component packages. It does not introduce
a deployable component, a shared runtime daemon, a second identity provider, a
parallel policy database or a new lifecycle authority.

The package closes the seams between component owners: Aos service identity to
KUKSA authorization, per-Unit key custody, provider privilege separation, the
complete QM advisory path, native log evidence, run correlation, chronology,
targeted vehicle external-connectivity continuity and AosCore-enforced service-
tenant isolation. Each product owner retains its
implementation and tests; `CR-CROSS` adds common contract and integration
acceptance over those owner boundaries.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Cross-component invariants, shared negative matrices and qualification evidence |
| What this package does not own | Product logic, AosCore/AosCloud or KUKSA source, a broker component, credentials, desired state, functional data or deployment approval |
| Intended result | Independent owners can evolve their components without widening authority, leaking secrets, misrepresenting vehicle external-connectivity state or breaking another tenant |
| Accountable lifecycle owner | System Architecture accepts the shared contract; each component owner implements its allocated part through its existing lifecycle |
| Primary repository or external source | No product repository; shared contract fixtures and qualification orchestration belong in `aosedge-sdv-demo` |

## Component Boundary

### In scope

- one authoritative Aos-to-KUKSA identity and permission chain;
- per-Unit signer/verifier lifecycle without artifact-baked secrets;
- separation of privileged provider and functional-service authority;
- defense-in-depth VDP checks plus authoritative Gateway QM containment;
- native operational-log evidence controls and redaction;
- consistent run, Unit, source and message correlation across surfaces;
- separate source, local-decision and Cloud-receipt chronology;
- one atomic Demonstration Unit external-connectivity loss/restoration control
  that interrupts Unit-to-AosCloud and installed service-to-functional-backend
  paths together while presenter-to-AosCloud and the simulated in-vehicle
  network remain available; and
- independently approved service resource envelopes, with AosCore as the sole
  in-vehicle enforcement/monitoring authority, and one bounded Tire CPU-
  saturation proof in which Brake and the platform graph remain healthy.

### Out of scope

- changing upstream Eclipse KUKSA, AosCore or AosCloud;
- creating a separate authorization adapter or local per-service policy store;
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
| Vehicle Data Platform Credential Broker | Platform Team / `CMP-VDP` | Thin IAM translation only; no parallel identity/policy store | Services remain not ready; no static-token fallback |
| Gateway QM advisory handler | Vehicle Gateway owner | Final deny-by-default typed non-safety boundary | Advisory is rejected with factual status |
| Native Aos logging path | AosCore/AosCloud | Scoped request, status, result, retention and deletion behavior qualified | Evidence is unavailable or explicitly unqualified |
| Aos Service Manager/container runtime | External AosEdge platform | Enforces and monitors accepted service-instance quotas through its runtime/cgroup mechanisms | Tenant-isolation proof cannot be accepted |
| Owner service resource contracts | Brake and Tire service owners | D4 freezes independently approved quotas and application overflow/recovery behavior | Combined graph cannot be accepted |

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
| [`IF-AUTH-001`–`003`](../component-decomposition-and-interface-register.md#if-auth-001) | Service ↔ VDP broker ↔ Aos IAM | Per-instance secret validation, registered permissions and short-lived JWT | Reject without token; no cached/static fallback | Aos service identity and IAM result, bounded by VDP contract |
| [`IF-AUTH-004`–`006`](../component-decomposition-and-interface-register.md#if-auth-004) | Platform security substrate → VDP/KUKSA | Verifier, protected signing operation and separate provider credential | Not ready; no key bytes or privilege reuse | Per-Unit platform trust and distinct provider identity |
| [`IF-ADV-001`](../component-decomposition-and-interface-register.md#if-adv-001), [`IF-TIRE-002`](../component-decomposition-and-interface-register.md#if-tire-002), [`IF-ADV-002`–`005`](../component-decomposition-and-interface-register.md#if-adv-002) | QM services → KUKSA → VDP → VISS → Gateway | Typed Brake/Tire maintenance advisory and factual result | Fail closed at every boundary; Gateway is final authority | IAM/KUKSA scope, VDP contract, then Gateway QM policy |
| [`IF-OBS-001`](../component-decomposition-and-interface-register.md#if-obs-001) | Software Delivery Dashboard ↔ AosCloud | Native log request/status/result/file | Explicit unavailable/failed state and bounded temporary cleanup | AosCloud-retained request and file state |
| [`IF-DEMO-001`](../component-decomposition-and-interface-register.md#if-demo-001) | Orchestrator → local actors | Run/role/source binding and session boundary | Ambiguity blocks the affected operation | Local run manifest plus authoritative Unit state |
| [`IF-FUNC-001`](../component-decomposition-and-interface-register.md#if-func-001), [`IF-TIRE-003`](../component-decomposition-and-interface-register.md#if-tire-003) | In-vehicle service → functional backend | Correlated bounded messages with original event time | Bounded queue/retry or explicit loss/degraded state | Function Team data contract |
| [`IF-LC-006`](../component-decomposition-and-interface-register.md#if-lc-006) | AosCore → VDP and services | Runtime lifecycle, readiness and resource enforcement | Explicit failed/degraded instance state | Unit actual state |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove each owner's local validator and state machine | External peers replaced by deterministic doubles | Yes, in owner packages; no duplicate `UT-CROSS-*` | Linked accepted `UT-*` obligations |
| Component | Prove each packaged component exposes the required security/operational behavior | Controlled fixtures and fake adjacent services | Yes | Owner-package component reports |
| Contract | Prove every producer/consumer agrees on identity, schema, error, time and limit semantics | Versioned cross-owner fixture catalogue | Yes | Cross-package conformance report and fixture digest |
| Integration | Prove layered enforcement and recovery with real adjacent components | Accepted Validation environment | Yes | Negative matrix, disconnect/reconnect, resource and log evidence |
| End-to-end | Prove audience claims without widening them | VU before identical DU promotion | Yes, allocated to `CR-E2E` | Stage and failure-path acceptance record |

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| [Native identity and least privilege (`REQ-CROSS-001`)](#req-cross-001) | Preserve one Aos-authoritative service identity and exact KUKSA permissions | Unit, Contract, Integration | D3 design-reviewed |
| [Per-Unit KUKSA trust lifecycle (`REQ-CROSS-002`)](#req-cross-002) | Protect one signer per Unit provisioning lifecycle, prepare only its public verifier and bound JWT issue/refresh/retirement | Unit, Component, Contract, Integration | D4-010.1 decided; implementation open |
| [Separate provider authority (`REQ-CROSS-003`)](#req-cross-003) | Never grant privileged provider rights through a functional service identity | Unit, Contract, Integration | D3 design-reviewed |
| [End-to-end QM advisory containment (`REQ-CROSS-004`)](#req-cross-004) | Reject every unauthorized or unsafe advisory at layered boundaries | Unit, Contract, Integration, End-to-end | D3 design-reviewed |
| [Controlled native-log evidence (`REQ-CROSS-005`)](#req-cross-005) | Present useful scoped logs without secrets, false retention or a second archive | Unit, Contract, Integration | D3 design-reviewed |
| [Cross-surface run correlation (`REQ-CROSS-006`)](#req-cross-006) | Bind facts to the exact run, role, Unit and source without global history | Unit, Contract, Integration, End-to-end | D3 design-reviewed |
| [Separated on-board and Cloud chronology (`REQ-CROSS-007`)](#req-cross-007) | Preserve event, decision and synchronization times without a false latency claim | Unit, Contract, Integration, End-to-end | D3 design-reviewed |
| [Targeted vehicle external-connectivity continuity (`REQ-CROSS-008`)](#req-cross-008) | Keep the installed graph active while one atomic fault interrupts AosCloud and functional-backend paths, then reconnect and synchronize | Contract, Integration, End-to-end | D3 design-reviewed |
| [AosCore service-tenant isolation (`REQ-CROSS-009`)](#req-cross-009) | Cap a prepared Tire CPU load at its own quota while Brake and the platform remain healthy | Unit, Component, Contract, Integration, End-to-end | D3 design-reviewed |

## Detailed Requirements

### Native identity and least privilege

<a id="req-cross-001"></a>

- ID: `REQ-CROSS-001`
- Statement: The accepted component graph shall derive each running SOTA instance's KUKSA authority from its current Aos identity and registered path/mode permissions, narrow that result to the installed VDP contract, and issue no broader or reusable authority.
- Parents: [least-privilege identities (`SYS-SEC-001`)](../system-requirements-and-traceability.md#sys-sec-001) and [native-IAM-derived credentials (`SYS-SEC-006`)](../system-requirements-and-traceability.md#sys-sec-006)
- Flow: [Aos-to-KUKSA credential flow (`AF-X-AUTH`)](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: [`CMP-AOS-CORE`](../component-decomposition-and-interface-register.md#cmp-aos-core), [`CMP-VDP`](../component-decomposition-and-interface-register.md#cmp-vdp), [`CMP-KUKSA`](../component-decomposition-and-interface-register.md#cmp-kuksa), [`CMP-BHS`](../component-decomposition-and-interface-register.md#cmp-bhs), [`CMP-TIRE`](../component-decomposition-and-interface-register.md#cmp-tire)
- Interfaces: `IF-AUTH-001` through `IF-AUTH-003`
- State: D3 design-reviewed; target integration

#### Acceptance criteria

1. Exact registered Brake and Tire read/write permissions produce only the corresponding short-lived scopes.
2. Invalid/stale secret, unknown mode, malformed path, contract excess, removed permission or cross-service identity produces no token.
3. No component stores a parallel service identity/policy database or persists/logs the secret or JWT.

### Per-Unit KUKSA trust lifecycle

<a id="req-cross-002"></a>

- ID: `REQ-CROSS-002`
- Statement: Successful provisioning shall give each Unit one unique
  non-exported RSA signer in the dedicated `kuksa-jwt` PKCS#11 token and shall
  atomically prepare only its public verifier before the Broker and KUKSA
  start. Broker JWTs shall be short-lived `RS256` tokens with fixed audience
  `kuksa.val`, bounded expiry and path permissions; the pinned KUKSA is not
  claimed to enforce `iss`. Permission removal shall prevent renewal, the
  first demo shall not perform live rotation, the next provisioning lifecycle
  shall create a new signer, and R0 shall destroy the retired signer with the
  VM overlay. No private key, shared static verifier or reusable token shall
  enter a Factory Image, FOTA/SOTA artifact, browser, container, command line
  or log.
- Parent: [KUKSA verifier and token lifetime (`SYS-SEC-004`)](../system-requirements-and-traceability.md#sys-sec-004)
- Flow: [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: `CMP-FACTORY`, `CMP-AOS-CORE`, `CMP-VDP`, `CMP-KUKSA`
- Interfaces: `IF-AUTH-004`, `IF-AUTH-005`
- State: D4-010.1 decided; implementation and live qualification remain open

#### Acceptance criteria

1. VU and DU expose different public-key fingerprints; same-Unit JWTs pass and
   cross-Unit JWTs fail.
2. Missing/malformed preparation state prevents Broker/KUKSA startup; expired,
   wrong-audience, wrong-signature, excessive-scope and non-renewable
   credentials fail without data/advisory side effects.
3. Reprovisioning changes the signer, and deprovision plus reconciled R0
   overlay discard makes the old signer unusable; no live-rotation claim is
   made.
4. Artifact, filesystem, process, command, environment and log inspection
   finds no private key, shared static verifier or reusable token.

### Separate provider authority

<a id="req-cross-003"></a>

- ID: `REQ-CROSS-003`
- Statement: The privileged provider inside `CMP-VDP` shall use a separately bound short-lived platform credential limited to accepted KUKSA `provide`/`create` paths; no SOTA service credential shall acquire, inherit or renew provider authority.
- Parent: [separate provider authority (`SYS-SEC-005`)](../system-requirements-and-traceability.md#sys-sec-005)
- Flow: [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: `CMP-AOS-CORE`, `CMP-VDP`, `CMP-KUKSA`
- Interface: `IF-AUTH-006`
- State: D3 design-reviewed; exact FOTA-component identity binding remains a D4 architecture/qualification gate

#### Acceptance criteria

1. The accepted provider identity obtains only its declared platform paths and loses them on revocation/expiry.
2. Brake/Tire identities and invalid provider bindings cannot obtain `provide`/`create` authority.
3. Identity-service unavailability yields explicit not-ready state and never a static-token fallback.

### End-to-end QM advisory containment

<a id="req-cross-004"></a>

- ID: `REQ-CROSS-004`
- Statement: The Brake and Tire advisory chain shall permit only their two D4-008 schema-bound non-safety maintenance Request targets through KUKSA and VDP defense in depth, while the Gateway independently validates identity/schema/size/value/freshness/lease/rate/replay, authoritatively rejects arbitrary VSS writes, cross-service targets, motion and safety-critical operations, and publishes the matching factual read-only Gateway Status.
- Parents: [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003) and [QM/Gateway containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Flow: [QM advisory containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Components: `CMP-BHS`, `CMP-TIRE`, `CMP-KUKSA`, `CMP-VDP`, `CMP-VISS`, `CMP-GW-ADV`, `CMP-ENG-DASH`
- Interfaces: `IF-ADV-001` through `IF-ADV-005` and `IF-TIRE-002`
- Executable contract: [Typed QM Advisory Profile 1.0.0](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- State: D3 design-reviewed; D4-008 contract accepted, implementation and qualification open

#### Acceptance criteria

1. Each accepted typed Brake/Tire request reaches only the correct Gateway target and produces matching `APPLIED`/`CLEARED` factual status; broker/protocol success alone is not accepted.
2. Wrong caller/path/endpoint, malformed/oversized/noncanonical payload, enum, freshness, lease, rate, correlation, replay or sequence rollback is rejected without an unintended write; explicit clear, auto-expiry and restart idempotency are proved.
3. Every throttle, brake, steer, gear, motion and safety-critical request from the QM route is rejected even if an upstream check is deliberately bypassed in a test.

### Controlled native-log evidence

<a id="req-cross-005"></a>

- ID: `REQ-CROSS-005`
- Statement: Cross-component operational evidence shall use the native AosCore/AosCloud log path with scoped request and result visibility, structured redaction, source time, qualified Cloud retention/deletion behavior and bounded removal of temporary local downloads; no demo component shall create a second archive.
- Parent: [operational log controls (`SYS-OBS-003`)](../system-requirements-and-traceability.md#sys-obs-003)
- Flow: [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, `CMP-SW-DASH` and every emitting owner
- Interface: `IF-OBS-001`
- State: D3 design-reviewed; exact live API permission, retention and deletion behavior remain D4 qualification gates

#### Acceptance criteria

1. A scoped request presents authoritative pending/success/failure state and its source scope/time without claiming indefinite retention.
2. Secret, token, private-certificate and unrestricted raw-telemetry fixtures do not appear in accepted logs or the dashboard.
3. Temporary downloads are bounded and deleted, while Cloud-owned audit/log state is not silently copied or erased by the demo.

### Cross-surface run correlation

<a id="req-cross-006"></a>

- ID: `REQ-CROSS-006`
- Statement: Every audience-visible functional or operational fact shall be attributable before provisioning to one bounded start time and overlay role, and afterward to the exact VU/DU Unit ID, role, source generation/frame evidence and same bounded session window; successful R0 shall remove demo-owned run data without creating a historical run database.
- Parent: [per-run correlation (`SYS-OBS-004`)](../system-requirements-and-traceability.md#sys-obs-004)
- Flows: [one source/two roles (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source) and [`AF-X-OBS`](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: `CMP-ORCH`, `CMP-GW`, `CMP-BRAKE-BE`, `CMP-TIRE-BE`, all dashboards
- Interfaces: `IF-DEMO-001`, `IF-VEH-004`–`006`, `IF-FUNC-001`/`002`, `IF-TIRE-003`/`004`
- State: D3 design-reviewed

#### Acceptance criteria

1. Equal event IDs from VU and DU or two Function Teams cannot collide because Unit role/source binding remains explicit.
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
- State: D3 design-reviewed

#### Acceptance criteria

1. Normal online evidence preserves an internally consistent causal order without requiring synchronized receipt times.
2. During the vehicle external-connectivity proof, delayed functional messages preserve original event/decision times and record later receipt/synchronization separately.
3. Missing/inconsistent chronology is explicit and no UI derives a Cloud-operation or vehicle KPI from it.

### Targeted vehicle external-connectivity continuity

<a id="req-cross-008"></a>

- ID: `REQ-CROSS-008`
- Statement: One stateful demo control shall atomically block or restore the Demonstration Unit's external vehicle connectivity. The disconnected state shall block both Unit-to-AosCloud and installed service-to-functional-backend paths while presenter-to-AosCloud, the simulated in-vehicle network and the installed on-board graph remain available. The Software Delivery Dashboard shall show authoritative offline/online state, reachable Function Dashboards shall show delayed/offline and later synchronized results, local inference/advisory shall continue, and reconnect shall use the same Unit and installed graph without reprovisioning, reinstalling or restarting. No separate per-channel fault control shall be exposed.
- Parent: [targeted vehicle external-connectivity continuity (`SYS-OBS-007`)](../system-requirements-and-traceability.md#sys-obs-007)
- Flow: [targeted vehicle external-connectivity loss (`AF-X-OFFLINE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, installed `CMP-VDP`/services, `CMP-SW-DASH`, and qualification orchestration
- Interfaces: `IF-LC-004`, `IF-LC-005`, `IF-LC-006`, `IF-OBS-001`
- State: D3 design-reviewed; allocation confirmed by `CROSS-D3`

#### Acceptance criteria

1. One visible control transition proves that DU-to-AosCloud and all installed service-to-functional-backend traffic are blocked together; partial or independently switched channel states are rejected. Presenter-to-AosCloud and simulated in-vehicle connections remain available.
2. AosCloud reports DU offline and affected lifecycle/log actions unavailable, while a deterministic CARLA event still reaches local inference, the advisory chain and Engineering Telematics Dashboard; reachable Function Dashboards receive no new result and show delayed/offline state.
3. One restore transition makes AosCloud report the same Unit and installed versions online without provisioning, reinstall or service/provider restart and synchronizes bounded functional messages idempotently with original and receipt times distinct; no presenter-loss or in-vehicle-loss claim is shown.

### AosCore service-tenant isolation

<a id="req-cross-009"></a>

- ID: `REQ-CROSS-009`
- Statement: Brake Health and Tire Health shall carry independently approved service quotas in their accepted Aos metadata, while AosCore/Service Manager remains the sole in-vehicle enforcement and monitoring authority. The first audience proof shall run one prebuilt bounded CPU-load profile inside the actual Tire Health service instance until it reaches its own quota. AosCore shall cap that instance and expose authoritative usage/status or alert evidence through AosCloud; at the same time Brake Health shall remain ready without restart and shall process the deterministic CARLA event, while VDP, KUKSA, Gateway and AosCore remain healthy. Stopping the load shall return Tire to normal without reinstall or restart. No project resource manager shall be added.
- Parent: [AosCore-enforced service-tenant isolation (`SYS-RES-001`)](../system-requirements-and-traceability.md#sys-res-001)
- Flows: [AosCore tenant isolation (`AF-TIRE-RES`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-res) and [common release/runtime enforcement (`AF-X-RELEASE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-release)
- Components: `CMP-AOS-CORE`, `CMP-AOS-CLOUD`, `CMP-TIRE`, `CMP-BHS`, `CMP-VDP`, `CMP-KUKSA`, `CMP-GW`, `CMP-SW-DASH`, `CMP-ORCH`
- Interfaces: `IF-LC-005`, `IF-LC-006`, `IF-DEMO-001`
- State: D3 design-reviewed; exact quota mapping, CPU unit/tolerance, monitoring API and prepared load-control contract remain D4 gates

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

## Reused Owner-Package Unit Obligations

No `UT-CROSS-*` identifiers are created because this package owns no executable
decision. The following accepted obligations remain blocking in their owner
repositories and are composed by the cross-package contract/integration gate.

| Cross requirement | Reused unit obligations |
| --- | --- |
| `REQ-CROSS-001` | [`UT-VDP-004`](vehicle-data-platform.md#ut-vdp-004), [`UT-BHS-003`](brake-health-service.md#ut-bhs-003), [`UT-TIRE-003`](tire-health-service.md#ut-tire-003) |
| `REQ-CROSS-002` | [`UT-FACTORY-009`](factory-substrate.md#ut-factory-009), [`UT-VDP-005`](vehicle-data-platform.md#ut-vdp-005) |
| `REQ-CROSS-003` | [`UT-VDP-006`](vehicle-data-platform.md#ut-vdp-006) |
| `REQ-CROSS-004` | [`UT-VDP-003`](vehicle-data-platform.md#ut-vdp-003), [`UT-GATEWAY-010`](vehicle-gateway.md#ut-gateway-010), [`UT-GATEWAY-011`](vehicle-gateway.md#ut-gateway-011), [`UT-BHS-007`](brake-health-service.md#ut-bhs-007), [`UT-TIRE-007`](tire-health-service.md#ut-tire-007) |
| `REQ-CROSS-005` | [`UT-DEMO-011`](demo-orchestration.md#ut-demo-011), [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-010`](tire-health-service.md#ut-tire-010) |
| `REQ-CROSS-006` | [`UT-DEMO-001`](demo-orchestration.md#ut-demo-001), [`UT-GATEWAY-003`](vehicle-gateway.md#ut-gateway-003), [`UT-BRAKE-CLOUD-009`](brake-health-cloud.md#ut-brake-cloud-009), [`UT-TIRE-CLOUD-007`](tire-health-cloud.md#ut-tire-cloud-007) |
| `REQ-CROSS-007` | [`UT-GATEWAY-012`](vehicle-gateway.md#ut-gateway-012), [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-010`](tire-health-service.md#ut-tire-010), [`UT-BRAKE-CLOUD-008`](brake-health-cloud.md#ut-brake-cloud-008), [`UT-TIRE-CLOUD-006`](tire-health-cloud.md#ut-tire-cloud-006) |
| `REQ-CROSS-008` | [`UT-VDP-007`](vehicle-data-platform.md#ut-vdp-007), [`UT-BHS-008`](brake-health-service.md#ut-bhs-008), [`UT-TIRE-006`](tire-health-service.md#ut-tire-006), [`UT-BRAKE-CLOUD-008`](brake-health-cloud.md#ut-brake-cloud-008), [`UT-TIRE-CLOUD-006`](tire-health-cloud.md#ut-tire-cloud-006), [`UT-DEMO-005`](demo-orchestration.md#ut-demo-005), [`UT-DEMO-011`](demo-orchestration.md#ut-demo-011), [`UT-DEMO-018`](demo-orchestration.md#ut-demo-018); AosCore/AosCloud behavior uses the accepted external-component test exception |
| `REQ-CROSS-009` | [`UT-BHS-010`](brake-health-service.md#ut-bhs-010), [`UT-TIRE-009`](tire-health-service.md#ut-tire-009), [`UT-DEMO-019`](demo-orchestration.md#ut-demo-019); AosCore/AosCloud enforcement and monitoring use the accepted external-component test exception |

## Verification Traceability

| Requirement | Unit proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- |
| `REQ-CROSS-001` | Reused owner obligations | `IF-AUTH-001`–`003` conformance | Real Service Manager/IAM, both services and KUKSA | `CR-E2E` G2/T1 authorization |
| `REQ-CROSS-002` | Reused owner obligations | JWT/trust/key-custody profile | Independent VU/DU signer/verifier lifecycle | `CR-E2E` issue/expiry/revocation |
| `REQ-CROSS-003` | Reused owner obligation | Provider identity/scope contract | Real provider issue/renew/revoke and SOTA negatives | `CR-E2E` G1/G3 readiness |
| `REQ-CROSS-004` | Reused owner obligations | Full advisory positive/negative matrix | Real KUKSA→VDP→Gateway chain with bypass injection | G4/T1 accepted and rejected advisories |
| `REQ-CROSS-005` | Reused owner obligations | Log API/redaction/retention contract | Scoped native request/result/download/delete | Operational evidence view |
| `REQ-CROSS-006` | Reused owner obligations | Correlation-field and cleanup contracts | Sequential VU/reset/DU plus both backends | Cross-surface evidence and R0 |
| `REQ-CROSS-007` | Reused owner obligations | Timestamp semantics and delayed-delivery fixtures | Owner-qualified backend delay/reconnect correlation | Local advisory versus delayed Cloud result |
| `REQ-CROSS-008` | Reused owner obligations plus external-platform exception | Atomic fault scope, state and synchronization contract | DU external-connectivity loss, local continuity, backend delay/synchronization and same-Unit reconnect | One accepted G4 offline/online scenario |
| `REQ-CROSS-009` | Reused owner obligations plus external-platform exception | Approved service metadata, load-control and quota/monitoring evidence schemas | Actual Tire cgroup CPU cap plus concurrent Brake/platform continuity | `AF-TIRE-RES` bounded audience proof and clean recovery |

## Cross-Cutting Constraint Matrix

| Concern | Required invariant | Primary enforcement | Independent proof |
| --- | --- | --- | --- |
| Identity | One Aos identity/permission authority | Service Manager/IAM + thin VDP broker | Exact-scope and cross-service negatives |
| Secret custody | No artifact-baked or exposed private material | Per-Unit platform-protected operation | Image/package/process/log scans |
| Provider privilege | Functional identity never becomes provider | Separate platform credential | Excess-scope and identity-substitution negatives |
| QM containment | No arbitrary or motion/safety operation | Gateway final boundary | Upstream-bypass negative matrix |
| Logs/privacy | Native scoped evidence only | AosCore/AosCloud + emitting owners | Redaction, retention and bounded-download qualification |
| Correlation | Exact run/role/Unit/source binding | Orchestrator and producer contracts | Cross-Unit/cross-team collision cases |
| Chronology | Event/local/receipt/sync times remain distinct | Message contracts and dashboards | Delayed/out-of-order reconnect cases |
| Vehicle external connectivity | One control interrupts DU-to-AosCloud and service-to-functional-backend paths together; presenter and in-vehicle paths remain available | Demo Orchestrator fault harness, AosCloud/AosCore state and Function Team queues/backends | Atomic fault-scope proof, local advisory, delayed dashboards, synchronization and same-Unit reconnect |
| Service resources | AosCore is the sole in-vehicle enforcement/monitor authority; applications declare quotas and own bounded behavior | Aos Service Manager/container runtime/cgroups | Tire CPU cap, authoritative Cloud evidence, concurrent Brake event and healthy platform graph |

## D3 Review Decisions

| Decision | Proposed resolution | Review state |
| --- | --- | --- |
| `CROSS-D1` — Package nature | `CR-CROSS` is a no-code assurance package, not a deployable component, shared runtime service, identity provider, policy store or product repository | **Confirmed 2026-08-20** |
| `CROSS-D2` — Test ownership | Reuse owner-package unit obligations rather than duplicate them as `UT-CROSS-*`; keep shared versioned fixtures and orchestration in `aosedge-sdv-demo`; prove composition through contract/integration gates and pass their evidence to `CR-E2E` without duplicating the negative matrix | **Confirmed 2026-08-20** |
| `CROSS-D3` — Connectivity allocation | The only deliberate first-demo fault is one atomic loss of Demonstration Unit external connectivity: Unit-to-AosCloud and installed service-to-functional-backend paths are interrupted/restored together by one stateful control; presenter-to-AosCloud and simulated in-vehicle links remain available; separate per-channel switches are prohibited | **Confirmed 2026-08-20** |
| `CROSS-D4` — Resource allocation | Use one prepared bounded CPU load inside the actual Tire instance; AosCore/Service Manager alone enforces and monitors its approved quota; Brake is the healthy control tenant. The Dashboard only presents authoritative state. Mac-local backends and aggregate multi-service-per-provider quotas are outside the claim; memory/storage/PID/network limits remain qualification evidence | **Confirmed 2026-08-20** |

## Open D4 Gates

| Gate | Impact | Owner |
| --- | --- | --- |
| Exact Aos IAM `GetPermissions` request/response and `kuksa` mode mapping | `REQ-CROSS-001` contract | Platform Team + Aos IAM owner |
| Implement and qualify the accepted D4-010.1 per-Unit signer/verifier preparation, startup, renewal-denial, cross-Unit rejection and overlay-retirement lifecycle | `REQ-CROSS-002` | Platform Team + Aos security owner |
| FOTA-component provider identity binding | `REQ-CROSS-003` | Platform Team + Aos architecture |
| Typed Brake/Tire targets, values, correlation, freshness, rate and replay bounds | `REQ-CROSS-004` | Gateway + Platform + Function Teams |
| Native log API roles, retention, deletion, offline and redaction behavior | `REQ-CROSS-005` | AosCloud integration + emitting owners |
| Shared correlation and timestamp field schemas | `REQ-CROSS-006`, `007` | Demo Solution + Gateway + Function Teams |
| Atomic DU external-connectivity control, dual-path fault mechanism, excluded-path probes, functional-message synchronization and same-Unit reconnect contract | `REQ-CROSS-008` | Demo Solution + AosCloud and both Function Team integrations |
| Exact Brake/Tire service-metadata-to-AosCore quota mapping, CPU units and pass/fail tolerance, Cloud usage/status or alert API, prepared Tire in-instance load trigger and Brake/platform unaffected thresholds | `REQ-CROSS-009` | AosCore integration + both Function Teams + Demo Solution |
| Versioned shared fixture catalogue and conformance harness layout | All contract proofs | System Architecture + repository owners |

## Package Acceptance

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

Acceptance authorizes D4 shared-contract design only. It does not authorize
implementation, repository creation, signing, AosCloud calls, VM operations,
provisioning, CARLA control or data deletion.

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

This acceptance closes D3 design review for `CR-CROSS` and authorizes only D4
shared-contract design. It does not authorize implementation, signing,
AosCloud mutation, VM operations, provisioning, CARLA control or data deletion.

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
