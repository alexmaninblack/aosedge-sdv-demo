<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vehicle Gateway Component Requirements

- Status: D3 design-reviewed
- Package: [`CR-GATEWAY`](../component-decomposition-and-interface-register.md#cr-gateway)
- Version: 1.1
- Prepared: 2026-08-21
- Owner: Vehicle Gateway Tooling
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Accepted architecture decision: [ADR 0011](../../architecture/decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md)
- Accepted D4 decision: [D4-002 Vehicle Hardware Capability Profile](../d4-decision-register.md#d4-002)
- Accepted D4 control decision: [D4-004 Simulator Control and Context Contract](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Accepted D4 source decision: [D4-005 Exclusive Live-Source Assignment](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Accepted D4 VISS decision: [D4-006 VISS Trust and Telemetry Profile](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Accepted D4 Safe Stop freshness decision: [D4-028](../d4-decision-register.md#d4-028)
- Accepted D4 advisory decision: [D4-008 Typed QM Advisory Profile](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Implementation baseline: `carla-ego-runtime@22864c5` against `CarlaSim@ac7d882c`

## Purpose

This package defines the simulated Vehicle Gateway ECU and its engineering
tools. The Gateway owns the bidirectional VSS/VISS vehicle boundary: the
implemented read path publishes normalized vehicle state through VISS
Get/Subscribe, while the target write path accepts only narrowly typed,
allowlisted advisory Set requests. It also preserves the implemented separate
vehicle-control and telemetry-dashboard behavior while specifying the
still-missing advisory return, factual Gateway status and local chronology
evidence.

For Brake Health and Tire Health, the Domain Controller route is a QM-origin
channel. VDP validation is defense in depth; this Gateway package owns the
final authoritative deny-by-default boundary and never exposes vehicle-motion
or safety-critical authority to either service.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Vehicle control UI/channel, complete Vehicle Hardware Capability Manifest accounting, CARLA sampling, actuator-command/applied-state traceability, signal normalization, VSS projection, VISS endpoint, future advisory handler and Engineering Telematics Dashboard |
| What this package does not own | CARLA scenario truth, Domain Controller provider, KUKSA, service decisions, functional backends, AosCloud lifecycle or production driver HMI |
| Intended result | A stable Gateway exposes truthful vehicle data and accepts only narrowly scoped typed advisory requests without exposing vehicle-motion authority |
| Accountable lifecycle owner | Vehicle Gateway Tooling; host-side demo build and qualification lifecycle |
| Primary repository | `carla-ego-runtime`; native CARLA adapter depends on the accepted `CarlaSim` baseline |

## Component Boundary

### In scope

- [Vehicle Control UI (`CMP-CONTROL`)](../component-decomposition-and-interface-register.md#cmp-control);
- [Vehicle Gateway Runtime (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw);
- [Vehicle Gateway VISS Server (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss);
- target [Gateway Advisory Handler (`CMP-GW-ADV`)](../component-decomposition-and-interface-register.md#cmp-gw-adv);
- [Engineering Telematics Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash).

### Out of scope

- deterministic physical stimulus and simulation-only truth, owned by
  `CR-VEHICLE-SIM`;
- VISS-to-KUKSA mapping, authorization policy and outbound provider, owned by
  `CR-VDP`;
- deciding whether Brake Health or Tire Health should request an advisory;
- a production driver display, acknowledgement or vehicle-motion actuation;
- the Software Delivery Dashboard and authoritative Cloud lifecycle state.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| CARLA vehicle state | Vehicle Simulation | [Native state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001), compatible revision and increasing frames | Gateway exposes source loss/degraded state and never fabricates normal values |
| Control client | Vehicle Gateway Tooling | Authenticated owner on the private local control channel | Safe stop remains selected |
| Vehicle Data Platform client | Platform Team | TLS VISS contract and, for Set, accepted advisory identity/policy | Unauthorized or malformed request fails closed |
| Engineering Dashboard | Demo Engineering Tooling | Independent read-only VISS subscription | Display becomes disconnected/stale without changing Gateway state |

## Current Implementation Baseline

| Capability | Evidence | State |
| --- | --- | --- |
| CARLA sampling, normalization and VSS 6.0 projection | [Telemetry contract v0.2](../../../../carla-ego-runtime/docs/telemetry-contract.md) | `CURRENT` |
| Selected hardware-profile coverage | [R10 native CARLA inventory](../../research/demo-foundation/r10-carla-telemetry-and-function-team-2.md) exists, but the Gateway has no accepted manifest-driven coverage report | `PARTIAL`; D4 manifest and accounting contract required |
| TLS VISS 3.1 Get/Subscribe/Unsubscribe | [VISS compatibility profile](../../../../carla-ego-runtime/docs/viss-profile.md) | `CURRENT` on the loopback development profile; broader trust contract remains D4 |
| Authenticated manual/autopilot/safe-stop control | [External control contract v2](../../../../carla-ego-runtime/docs/external-control-contract.md) and protocol v3 scenario extension | `CURRENT` |
| Continuous actor, telemetry and camera through handover | [M6.2 accepted behavior](../../../../carla-ego-runtime/docs/m6-2-live-handover.md) | `CURRENT` |
| Engineering telemetry dashboard | Independent `carla-viss-client --monitor` for vehicle and wheel data | `CURRENT` |
| Explicit source availability/status signal | Optional malformed values are omitted and dashboard connection is visible; no complete versioned Gateway source-status contract exists | `PARTIAL` |
| Typed advisory Set and Gateway handler | Current VISS correctly rejects every Set to a read-only node | `TARGET` |
| Advisory status in Engineering Dashboard | No accepted signal or UI exists | `TARGET` |
| Local decision-to-Gateway chronology evidence | Vehicle and VISS timestamps exist; end-to-end advisory correlation does not | `TARGET` |

All 18 registered tests in the existing native build passed on 2026-08-18,
including isolated logic, TLS loopback, Unix control socket and native Swift
type-checking. The live CARLA scene was not started for this requirements pass.

## Testability Boundary

The normalizer, clock anchor, GNSS freshness store, VSS mapper/latest-value
store, VISS protocol engine, control state machine, handover calculation,
dashboard health parser and future advisory validator/state machine are owned
units. They shall run deterministically with in-memory snapshots, fake clocks
and transport doubles.

TLS WebSocket behavior, Unix socket permissions, the native CARLA adapter,
Swift panel, real dashboard and full advisory round trip are component,
contract or integration tests. They do not replace the isolated tests of the
decisions they exercise.

## Interface Summary

| Interface | Direction | Data or command | Current/target contract | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) | In | Vehicle Hardware Capability Manifest plus native installed vehicle/sensor values, availability and applied-control state | Existing subset `CURRENT`; exact D4 manifest and complete coverage contract to freeze | Reject malformed mandatory frame; explicitly account for missing/unsupported entries; expose source loss; reject qualification-only truth | CARLA runtime state and accepted hardware profile |
| [Control request (`IF-VEH-002`)](../component-decomposition-and-interface-register.md#if-veh-002) | In | Manual, autopilot, scenario and safe-stop mode/commands | Local authenticated protocol v1-v3 `CURRENT` | Invalid, stale, replayed or lost ownership selects/requires safe stop | Gateway control state |
| [CARLA actuator command (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003) | Out | Commands for every manifest-declared actuator; current authorized subset is throttle, brake and steering | Existing subset `CURRENT`; complete actuator/status contract `EXTEND` | No competing owner; explicit reject/status; safe stop on loss/failure; actual applied state returns through `IF-VEH-001` | Gateway arbitration |
| [Normalized VSS model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004) | Internal out | Frame-aligned VSS values and source status | Telemetry `CURRENT`; explicit source/advisory status `EXTEND` | No fabricated zero for unavailable optional data | Gateway projection |
| [Platform VISS read connection (`IF-VEH-005`)](../component-decomposition-and-interface-register.md#if-veh-005) | Out | TLS Get/Subscribe for accepted telemetry and status paths | Read path `CURRENT`; D4 contract freeze required | Bounded errors/queues; slow or failed client cannot block simulation | Gateway VISS read contract |
| [Engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006) | Out | Read-only telemetry and status subscription | Telemetry `CURRENT`; advisory/status `EXTEND` | Dashboard shows disconnected/stale and cannot mutate Gateway | Gateway VISS contract |
| [Platform-update vehicle state (`IF-VEH-007`)](../component-decomposition-and-interface-register.md#if-veh-007) | Out | Purpose-bound `PLATFORM_UPDATE_RUNTIME` mTLS role exposing only `FrameId`, applied mode, transition/reset state and factual stop signals for the OEM Component Runtime | `TARGET`; contract accepted | Missing/stale/reset-discontinuous or repeated-frame evidence remains explicit and cannot be interpreted as stopped | Gateway facts; runtime evaluates Safe Stop policy |
| [Outbound advisory Set (`IF-ADV-003`)](../component-decomposition-and-interface-register.md#if-adv-003) | In | Narrow typed VISS Set request from the Vehicle Data Platform outbound provider | `TARGET` | Unauthorized path, identity, type, value, stale or replayed request fails closed | Platform outbound allowlist and Gateway write contract |
| [Advisory delivery (`IF-ADV-004`)](../component-decomposition-and-interface-register.md#if-adv-004) | Internal in | Validated typed Brake or Tire advisory target | `TARGET` | Reject unknown path/type/value, stale/replay and unauthorized source | Gateway contract |
| [Advisory status (`IF-ADV-005`)](../component-decomposition-and-interface-register.md#if-adv-005) | Internal out | Factual received/rejected/status signal | `TARGET` | Never claim displayed or acknowledged | Gateway state |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove normalization, protocol, control, advisory and status decisions | Fake clocks, in-memory snapshots and transport doubles | Yes | `UT-GATEWAY-*` obligations in the normal repository gate |
| Component | Prove packaged runtime, TLS endpoint, local socket, dashboard and UI | Local ephemeral TLS/socket and controlled processes | Yes | CTest/component reports and redacted manifests |
| Contract | Prove VSS/VISS, control and advisory schemas and semantics | Versioned fixtures/conformance harness | Yes | D4 contract suites and fixture digests |
| Integration | Prove real CARLA sampling/control and real Domain Controller VISS exchange | Pinned CARLA and selected AosVM | Yes | Validation-lane integration record |
| End-to-end | Prove current telemetry plus G4/T1 advisory return and R0 cleanup | Complete staged demo | Yes | Exact Unit, run/frame range, status and chronology evidence |

## Requirement Summary

| Requirement | Plain-language obligation | Implementation | Verification levels |
| --- | --- | --- | --- |
| [Frame-coherent CARLA acquisition (`REQ-GATEWAY-001`)](#req-gateway-001) | Sample one attributable vehicle frame without mixing source time | `CURRENT` | Unit, Contract, Integration |
| [Truthful normalization and provenance (`REQ-GATEWAY-002`)](#req-gateway-002) | Convert native values to defined physical/VSS semantics | `CURRENT` | Unit, Contract, Integration |
| [Bounded latest-value and unavailable behavior (`REQ-GATEWAY-003`)](#req-gateway-003) | Retain only the newest frame and never fabricate missing values | `CURRENT / PARTIAL` | Unit, Contract, Integration |
| [Bounded TLS VISS read service (`REQ-GATEWAY-004`)](#req-gateway-004) | Serve the accepted read/subscribe profile without blocking simulation | `CURRENT / PARTIAL` | Unit, Component, Contract |
| [Source identity and selected-Unit evidence (`REQ-GATEWAY-005`)](#req-gateway-005) | Carry run/ego/generation/frame identity through sequential exclusive live VU and PU bindings | `PARTIAL` | Unit, Integration, End-to-end |
| [Authenticated fail-safe vehicle control (`REQ-GATEWAY-006`)](#req-gateway-006) | Permit one valid owner and safe-stop on invalid or lost control | `CURRENT` | Unit, Component, Integration |
| [Continuous manual/autopilot handover (`REQ-GATEWAY-007`)](#req-gateway-007) | Switch modes without replacing actor, clock or telemetry and wait for the accepted world-context transition | `PARTIAL` | Unit, Integration, End-to-end |
| [Independent engineering telemetry view (`REQ-GATEWAY-008`)](#req-gateway-008) | Show Gateway facts without joining the control or service path | `CURRENT` | Unit, Component, End-to-end |
| [Explicit source-loss state (`REQ-GATEWAY-009`)](#req-gateway-009) | Turn missing, stale or disconnected input into degraded/unavailable status | `PARTIAL` | Unit, Contract, Integration |
| [Authoritative QM advisory Set boundary (`REQ-GATEWAY-010`)](#req-gateway-010) | Accept only typed non-safety Brake/Tire advisories and reject arbitrary VSS, motion and safety-critical operations | `TARGET` | Unit, Component, Contract, Integration |
| [Factual advisory status (`REQ-GATEWAY-011`)](#req-gateway-011) | Publish received/rejected Gateway state without a driver-display claim | `TARGET` | Unit, Contract, End-to-end |
| [Local advisory chronology (`REQ-GATEWAY-012`)](#req-gateway-012) | Correlate local advisory delivery independently of Cloud synchronization without a first-demo latency KPI | `TARGET` | Unit, Integration, End-to-end |
| [Truthful mode/context engineering projection (`REQ-GATEWAY-013`)](#req-gateway-013) | Expose mode, context, scenario generation/result and reset discontinuity without joining the control path | `TARGET` | Unit, Contract, Integration, End-to-end |
| [Complete hardware-profile accounting (`REQ-GATEWAY-014`)](#req-gateway-014) | Account for every installed capability without silently losing data before VSS selection | `PARTIAL` | Unit, Contract, Integration |
| [Actuator command and applied-state traceability (`REQ-GATEWAY-015`)](#req-gateway-015) | Distinguish physical actuator capability, authorized commands and actual applied state | `PARTIAL` | Unit, Contract, Integration, End-to-end |

## Detailed Requirements

### Frame-coherent CARLA acquisition

<a id="req-gateway-001"></a>

- ID: `REQ-GATEWAY-001`
- Statement: The Gateway shall sample the selected ego vehicle against one
  CARLA world frame, preserve its run, actor, frame and simulation-time identity
  and prevent future, duplicate or out-of-order sensor data from being merged
  as current state.
- Parent system requirements: [Exact source-to-Unit binding (`SYS-SRC-001`)](../system-requirements-and-traceability.md#sys-src-001) and [explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [one visible source (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) and [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004)
- Required evidence: frame-aligned snapshot fixtures, rejection counters and live frame correlation
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT`

### Truthful normalization and provenance

<a id="req-gateway-002"></a>

- ID: `REQ-GATEWAY-002`
- Statement: The Gateway shall validate mandatory CARLA values and
  deterministically convert coordinates, units, steering geometry, pedal
  proxies and four-wheel dynamics into the accepted VSS 6.0 plus project-overlay
  meanings, preserving source type and never presenting a proxy, derived or
  simulated value as a measured production sensor.
- Parent system requirement: [Explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005)
- Architecture flow: [G1 telemetry runtime (`AF-G1-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-rt)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) and [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004)
- Required evidence: normal, limit, sign, non-finite and contradictory-value fixtures
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT`

### Bounded latest-value and unavailable behavior

<a id="req-gateway-003"></a>

- ID: `REQ-GATEWAY-003`
- Statement: The Gateway shall atomically retain only the newest complete VSS
  frame, reject duplicate or older frame publication and represent invalid,
  missing, future or stale optional data as absent/unavailable rather than zero
  or another plausible normal value.
- Parent system requirements: [Versioned v1 signal contract (`SYS-VDP-002`)](../system-requirements-and-traceability.md#sys-vdp-002) and [explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005)
- Architecture flow: [G1 telemetry runtime (`AF-G1-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-rt)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw) and [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss)
- Interface: [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004)
- Required evidence: store ordering, GNSS freshness, optional-value omission and unavailable read results
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT` for data points; complete source-level degraded status belongs to `REQ-GATEWAY-009`

### Bounded TLS VISS read service

<a id="req-gateway-004"></a>

- ID: `REQ-GATEWAY-004`
- Statement: The Gateway shall expose the accepted VISS 3.1 Get, Subscribe and
  Unsubscribe subset over mutual TLS 1.2 or newer, require the `VISSv3`
  subprotocol and authenticate exactly the selected Unit VDP peer, its
  distinct purpose-bound read-only Platform Update Runtime, independent
  read-only Engineering Dashboard and qualification-client roles. Each of the
  two selected-Unit roles shall be limited to one connection and the runtime
  role to the ten Safe Stop paths. It shall
  reject unknown, additional and non-selected Unit peers, bound clients,
  subscriptions and pending messages, return protocol-valid errors and
  prevent a slow subscriber from blocking CARLA frame processing.
- Parent system requirements: [Versioned v1 signal contract (`SYS-VDP-002`)](../system-requirements-and-traceability.md#sys-vdp-002) and [authoritative demo surfaces (`SYS-OBS-001`)](../system-requirements-and-traceability.md#sys-obs-001)
- Architecture flows: [G1 telemetry runtime (`AF-G1-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-rt) and [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss)
- Interfaces: [platform VISS (`IF-VEH-005`)](../component-decomposition-and-interface-register.md#if-veh-005) and [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Executable contract: [VISS Trust and Telemetry Profile 1.1.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Required evidence: protocol suite, real mTLS suite, role/selected-Unit negative matrix and bounded-delivery metrics
- Requirement state: D3 design-reviewed; D4-006 contract accepted
- Implementation state: `PARTIAL`; current server-authenticated read profile must add accepted mTLS roles and selected-Unit enforcement

### Source identity and selected-Unit evidence

<a id="req-gateway-005"></a>

- ID: `REQ-GATEWAY-005`
- Statement: Every Gateway stream used as qualification or demo evidence shall
  expose the simulation profile, run, ego, frame and simulation time and shall
  be correlated outside the signal tree with exactly one selected Unit and
  bounded live frame range. Telemetry replay is deferred beyond the first
  implementation.
- Parent system requirements: [Exact source-to-Unit binding (`SYS-SRC-001`)](../system-requirements-and-traceability.md#sys-src-001) and [honest single-source presentation (`SYS-SRC-002`)](../system-requirements-and-traceability.md#sys-src-002)
- Architecture flow: [one visible source (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss) and [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash)
- Interfaces: [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004), [platform VISS (`IF-VEH-005`)](../component-decomposition-and-interface-register.md#if-veh-005) and [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Executable contract: [Exclusive Live-Source Assignment 1.0.0](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Required evidence: VISS metadata plus orchestrator-owned selected live Unit binding
- Requirement state: D3 design-reviewed; D4-005 contract accepted
- Implementation state: `PARTIAL`

### Authenticated fail-safe vehicle control

<a id="req-gateway-006"></a>

- ID: `REQ-GATEWAY-006`
- Statement: The Gateway control channel shall allow one authenticated owner,
  reject invalid/replayed/out-of-mode commands and simultaneous throttle/brake,
  enforce separate command and ownership deadlines and apply full-brake safe
  stop on startup, timeout, release, disconnect, focus loss where applicable,
  client close or controller failure.
- Parent system requirement: [Fail-safe exclusive vehicle control (`SYS-CTRL-001`)](../system-requirements-and-traceability.md#sys-ctrl-001)
- Architecture flows: [G0 baseline failure boundaries (`AF-G0-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-fr) and [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt)
- Components: [Control UI (`CMP-CONTROL`)](../component-decomposition-and-interface-register.md#cmp-control) and [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interfaces: [control requests (`IF-VEH-002`)](../component-decomposition-and-interface-register.md#if-veh-002) and [CARLA commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Executable contract: [Simulator Control and Context 1.1.1](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Required evidence: isolated state-machine suite, local socket permission/lifecycle test and live safe-stop observation
- Requirement state: D3 design-reviewed; D4-004 contract accepted
- Implementation state: `CURRENT`

### Continuous manual/autopilot handover

<a id="req-gateway-007"></a>

- ID: `REQ-GATEWAY-007`
- Statement: The Gateway shall switch the same ego actor among manual,
  synchronous Traffic Manager autopilot, scripted scenario and safe stop while
  retaining one clock owner and uninterrupted VISS identity; autopilot shall be
  accepted only near an aligned driving lane and automatic-to-manual control
  shall avoid overlapping pedals and unbounded steering steps. A requested
  mode shall become active only after its required `AF-X-DRIVE` world-context
  cleanup/reset has completed; any failure shall retain safe stop.
- Parent system requirements: [Continuous control-mode handover (`SYS-CTRL-002`)](../system-requirements-and-traceability.md#sys-ctrl-002) and [deterministic mode/context transition (`SYS-CTRL-003`)](../system-requirements-and-traceability.md#sys-ctrl-003)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [drive-mode/world-context transitions (`AF-X-DRIVE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-drive)
- Components: [Control UI (`CMP-CONTROL`)](../component-decomposition-and-interface-register.md#cmp-control) and [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), jointly with [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interfaces: [control requests (`IF-VEH-002`)](../component-decomposition-and-interface-register.md#if-veh-002) and [CARLA commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Executable contract: [Simulator Control and Context 1.1.1](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Required evidence: mode-transition suite, stable actor/run/frame identity and visual handover acceptance
- Requirement state: D3 design-reviewed; D4-004 contract accepted
- Implementation state: `PARTIAL`; current same-actor handover, lane validation and automatic-to-manual blend exist, while context-aware obstacle cleanup/reset before Autopilot does not

### Independent engineering telemetry view

<a id="req-gateway-008"></a>

- ID: `REQ-GATEWAY-008`
- Statement: The Engineering Telematics Dashboard shall use only an independent
  read-only VISS subscription and shall show Gateway telemetry, source
  connection/freshness and future factual advisory status without controlling
  the vehicle or claiming KUKSA receipt, functional decision, Cloud delivery or
  production driver display.
- Parent system requirement: [Authoritative demo surfaces (`SYS-OBS-001`)](../system-requirements-and-traceability.md#sys-obs-001)
- Architecture flow: [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash) and [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss)
- Interface: [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Required evidence: dashboard command, observed VISS-only connection, factual labels and negative inspection for control/KUKSA/Cloud coupling
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT` for telemetry; advisory/status extension belongs to `REQ-GATEWAY-011`

### Explicit source-loss state

<a id="req-gateway-009"></a>

- ID: `REQ-GATEWAY-009`
- Statement: Missing, stale, malformed or disconnected CARLA/Gateway data shall
  become explicit point-level unavailable or source-level degraded/disconnected
  state with source time; recovery shall restore live state only after a valid
  newer frame and shall never fill the outage with fabricated normal values.
- Parent system requirements: [Explicit degraded data (`SYS-VDP-005`)](../system-requirements-and-traceability.md#sys-vdp-005) and [authoritative demo surfaces (`SYS-OBS-001`)](../system-requirements-and-traceability.md#sys-obs-001)
- Architecture flow: [G1 failure boundaries (`AF-G1-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-fr)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss) and [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash)
- Interfaces: [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004), [platform VISS (`IF-VEH-005`)](../component-decomposition-and-interface-register.md#if-veh-005) and [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Required evidence: point omission/unavailable tests, source disconnect/stale/recovery fixtures and dashboard state
- Executable contract: [VISS Trust and Telemetry Profile 1.1.0](../../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json)
- Requirement state: D3 design-reviewed; D4-006 contract accepted
- Implementation state: `PARTIAL`; exact states and timing are accepted, implementation and live qualification remain open

### Authoritative QM advisory Set boundary

<a id="req-gateway-010"></a>

- ID: `REQ-GATEWAY-010`
- Statement: The VISS endpoint and Gateway Advisory Handler shall treat the
  Domain Controller advisory route as QM-origin and shall be the final
  authoritative boundary. It shall accept Set only for the D4-008
  `Vehicle.OEM.BrakeHealth.Advisory.Request` and
  `Vehicle.OEM.TireHealth.Advisory.Request` schema-bound non-safety targets;
  validate target, 2048-byte canonical envelope, endpoint-specific enum/value,
  2000 ms age, 30000 ms lease, rate, request/epoch/sequence and replay identity;
  and reject arbitrary VSS writes and every throttle, brake, steering, gear,
  vehicle-motion or safety-critical operation without changing vehicle state.
- Parent system requirements: [allowlisted outbound advisory (`SYS-VDP-004`)](../system-requirements-and-traceability.md#sys-vdp-004), [allowlisted Brake Health advisory (`SYS-BHS-003`)](../system-requirements-and-traceability.md#sys-bhs-003), [offline Tire Health advisory (`SYS-TIRE-006`)](../system-requirements-and-traceability.md#sys-tire-006), [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003), and [QM service and Gateway containment (`SYS-SEC-007`)](../system-requirements-and-traceability.md#sys-sec-007)
- Architecture flows: [G4 advisory runtime (`AF-G4-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-rt), [Tire Health runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt), and [QM advisory containment (`AF-X-QM`)](../../architecture/demo-scenario-architecture-flows.md#af-x-qm)
- Components: [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss) and [Advisory Handler (`CMP-GW-ADV`)](../component-decomposition-and-interface-register.md#cmp-gw-adv)
- Interfaces: [outbound advisory Set (`IF-ADV-003`)](../component-decomposition-and-interface-register.md#if-adv-003) and [advisory delivery (`IF-ADV-004`)](../component-decomposition-and-interface-register.md#if-adv-004)
- Required evidence: positive contract cases for each typed target plus wrong
  path/type/value, missing identity, stale, replay, excessive-rate,
  cross-service, arbitrary-write, throttle, brake, steer, gear and other
  safety/motion negative cases with no side effects
- Executable contract: [Typed QM Advisory Profile 1.0.2](../../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)
- Requirement state: D3 design-reviewed; D4-008 contract accepted
- Implementation state: `TARGET`; current all-Set rejection remains correct until the complete accepted endpoints and negative matrix are implemented

### Factual advisory status

<a id="req-gateway-011"></a>

- ID: `REQ-GATEWAY-011`
- Statement: For each advisory request, explicit clear and automatic lease
  expiry, the Gateway shall publish the matching schema-bound read-only status
  with request/epoch/sequence, Gateway time, active recommendation and one of
  `RECEIVED`, `APPLIED`, `CLEARED`, `REJECTED`, `EXPIRED` or `FAILED` plus the
  accepted D4-008 reason enum suitable for
  read-only dashboard observation; it shall not publish `DISPLAYED` or
  `ACKNOWLEDGED` because no driver HMI exists.
- Parent system requirements: [allowlisted outbound advisory (`SYS-VDP-004`)](../system-requirements-and-traceability.md#sys-vdp-004), [fail-closed advisory security (`SYS-SEC-003`)](../system-requirements-and-traceability.md#sys-sec-003) and [authoritative demo surfaces (`SYS-OBS-001`)](../system-requirements-and-traceability.md#sys-obs-001)
- Architecture flows: [G4 advisory runtime (`AF-G4-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-rt) and [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: [Advisory Handler (`CMP-GW-ADV`)](../component-decomposition-and-interface-register.md#cmp-gw-adv), [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss) and [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash)
- Interfaces: [advisory status (`IF-ADV-005`)](../component-decomposition-and-interface-register.md#if-adv-005) and [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Required evidence: status transition/size/schema fixtures, VISS subscription result and factual dashboard labels
- Executable contract: [Gateway Status schema](../../../contracts/qm-advisory-profile/qm-advisory-status.schema.json)
- Requirement state: D3 design-reviewed; D4-008 contract accepted
- Implementation state: `TARGET`

### Local advisory chronology

<a id="req-gateway-012"></a>

- ID: `REQ-GATEWAY-012`
- Statement: The advisory Request and Gateway Status contract shall preserve
  exact request/producer-epoch/sequence correlation plus distinct source-event,
  local advisory and Gateway-reception
  timestamps independently of functional Cloud report delivery. The first
  demo shall use them to prove ordering and that Cloud is not in the local
  decision path, without presenting a quantitative latency benchmark.
- Parent system requirement: [Separate on-board and Cloud chronology (`SYS-TIM-002`)](../system-requirements-and-traceability.md#sys-tim-002)
- Architecture flows: [G4 observability (`AF-G4-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-g4-ob) and [Tire Health observability (`AF-TIRE-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-ob)
- Components: [Advisory Handler (`CMP-GW-ADV`)](../component-decomposition-and-interface-register.md#cmp-gw-adv), [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss) and [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash)
- Interfaces: [advisory delivery (`IF-ADV-004`)](../component-decomposition-and-interface-register.md#if-adv-004), [advisory status (`IF-ADV-005`)](../component-decomposition-and-interface-register.md#if-adv-005) and [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006)
- Required evidence: deterministic timestamp fixtures and a correlated local chronology record distinct from backend synchronization
- Requirement state: D4-024 shared correlation/chronology design reviewed; implementation and live qualification remain open
- Implementation state: `TARGET`

### Truthful mode/context engineering projection

<a id="req-gateway-013"></a>

- ID: `REQ-GATEWAY-013`
- Statement: The Gateway engineering projection shall publish the current
  drive mode, `FREE_DRIVE`/`BRAKE_EVENT` context, scenario state/result,
  scenario/reset generation and an explicit reset/discontinuity indication
  through simulator-specific read-only VSS paths. The same projection plus
  factual speed, throttle and brake shall be available with monotonic
  `FrameId` through the distinct purpose-bound `PLATFORM_UPDATE_RUNTIME` mTLS
  role for Safe Stop evaluation. The source timestamp shall let the runtime
  prove that each sample was fresh when acquired and revalidate the latest
  complete sample at each destructive gate; the retained observation sequence
  is stability evidence only. The six controller/reset facts shall be included
  only when one non-blocking, length-framed record from the exclusive
  controller is carried over the owner-only connected `AF_UNIX` stream for
  that run, authenticated by effective UID on Darwin or Linux, and joined to
  the physical snapshot by exact CARLA frame ID and simulation time. The
  transport shall reject zero/truncated/oversize input before JSON processing,
  treat backpressure timeout, EOF or disconnect as unavailable without
  reconnect or prior-value reuse,
  bound unmatched records to four per side for 250 ms host-monotonic residence
  and omit the complete six-fact group on invalid, missing, duplicate,
  out-of-order, expired or overflowed input, without last-known reuse. These
  are local transport bounds, not Runtime Safe Stop freshness policy. Gateway
  publishes facts and shall not decide whether a Platform update may apply.
  The Engineering Telematics Dashboard shall show those facts without issuing control commands and
  without presenting a reset teleport as physical motion or adding them to an
  accepted production VDP signal subset by implication.
- Parent system requirement: [Truthful control-transition evidence (`SYS-OBS-005`)](../system-requirements-and-traceability.md#sys-obs-005)
- Architecture flows: [drive-mode/world-context transitions (`AF-X-DRIVE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-drive) and [cross-stage evidence (`AF-X-OBS`)](../../architecture/demo-scenario-architecture-flows.md#af-x-obs)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), [VISS (`CMP-VISS`)](../component-decomposition-and-interface-register.md#cmp-viss), [OEM Component Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime) and [Engineering Dashboard (`CMP-ENG-DASH`)](../component-decomposition-and-interface-register.md#cmp-eng-dash)
- Interfaces: [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004), [engineering subscription (`IF-VEH-006`)](../component-decomposition-and-interface-register.md#if-veh-006) and [Platform-update vehicle state (`IF-VEH-007`)](../component-decomposition-and-interface-register.md#if-veh-007)
- Required evidence: state/path/type/freshness fixtures including per-sample acquisition freshness and latest-sample gate-time freshness; accepted controller-record schema, peer/permission and exact frame/time join fixtures; bounded missing/drop/duplicate/out-of-order/overflow/expiry negatives; monotonic generation checks; real-frame-only reset discontinuity sequence; runtime-role allowlist; dashboard rendering; and negative proof that neither the dashboard nor Gateway owns the update decision
- Executable contracts: [Simulator Control and Context 1.1.1](../../../contracts/simulator-control-context/simulator-control-context.v1.json) and [Platform FOTA Safe Stop 1.1.1](../../../contracts/platform-fota-safe-stop/platform-fota-safe-stop-profile.v1.json)
- Requirement state: D3 design-reviewed; D4-004 contract accepted
- Implementation state: `TARGET`; current controller status contains part of the state outside VISS, but the accepted engineering projection and dashboard fields do not exist

### Complete hardware-profile accounting

<a id="req-gateway-014"></a>

- ID: `REQ-GATEWAY-014`
- Statement: On startup the Gateway shall validate the accepted Vehicle
  Hardware Capability [profile 1.0.0](../../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.v1.json)
  and [schema](../../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.schema.json)
  against the live CARLA source, blueprint, sensors and adapter. It shall bind
  its coverage result to the accepted profile digest and maintain exactly one
  disposition for every entry: retained native, normalized, explicit
  unavailable, reviewed unsupported, excluded qualification/demo or not
  installed. A mismatch invalidates the run. It shall not mutate the accepted
  profile, fabricate an uninstalled capability or admit qualification-only
  ground truth into the production state pipeline.
- Parent system requirements: [versioned vehicle hardware profile (`SYS-SRC-003`)](../system-requirements-and-traceability.md#sys-src-003) and [complete Simulator–Gateway accounting (`SYS-SRC-004`)](../system-requirements-and-traceability.md#sys-src-004)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [G1 telemetry runtime (`AF-G1-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g1-rt)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), jointly with [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) and [normalized model (`IF-VEH-004`)](../component-decomposition-and-interface-register.md#if-veh-004)
- Required evidence: manifest digest and schema validation, manifest-to-adapter coverage report, optional/unavailable/unsupported cases and qualification-truth rejection
- Requirement state: D3 design-reviewed; D4-002 contract accepted
- Implementation state: `PARTIAL`; the current adapter maps the accepted
  scalar/wheel/GNSS subset, but startup reconciliation and complete target
  coverage against the canonical profile are not implemented

Acceptance does not require every ingested hardware value to be published by
VSS/VISS or KUKSA. It requires the Gateway to account for the complete physical
profile before the Platform Team selects a narrower service-facing contract.

### Actuator command and applied-state traceability

<a id="req-gateway-015"></a>

- ID: `REQ-GATEWAY-015`
- Statement: The Gateway shall account for every actuator declared by the
  accepted hardware profile: throttle, brake, steering, handbrake,
  transmission/reverse/manual shift and vehicle lights. It shall distinguish
  physical capability from current control-owner authorization, send only
  valid authorized commands, record an explicit accepted or rejected execution
  result and correlate the command with the actually applied CARLA state.
  Scenario, Manual, Autopilot and Safe Stop are control modes governed by
  D4-004, not actuators. A declared capability shall not imply that the current
  Control UI or any SOTA service is authorized to operate it.
- Parent system requirement: [Complete Simulator–Gateway accounting (`SYS-SRC-004`)](../system-requirements-and-traceability.md#sys-src-004)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [drive-mode/world-context transitions (`AF-X-DRIVE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-drive)
- Components: [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw), [Control UI (`CMP-CONTROL`)](../component-decomposition-and-interface-register.md#cmp-control) and [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla)
- Interfaces: [control request (`IF-VEH-002`)](../component-decomposition-and-interface-register.md#if-veh-002), [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003) and [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001)
- Required evidence: capability-versus-authority matrix, valid/invalid command fixtures, command/result/applied-state correlation and negative tests proving that functional services have no vehicle-motion authority
- Requirement state: D3 design-reviewed; D4-002 contract accepted
- Implementation state: `PARTIAL`; throttle/brake/steer control and applied-control sampling exist, while the complete declared actuator set and execution-status contract are not frozen

## Unit-Test Obligations

| Unit-test obligation | Requirements proved | Behavior and branches | Current evidence | State |
| --- | --- | --- | --- | --- |
| <a id="ut-gateway-001"></a>`UT-GATEWAY-001` — vehicle normalization | [Normalization (`REQ-GATEWAY-002`)](#req-gateway-002), [unavailable data (`REQ-GATEWAY-003`)](#req-gateway-003) | Units, signs, steering geometry, proxy bounds, malformed mandatory and invalid optional values | [`vehicle_state_test.cpp`](../../../../carla-ego-runtime/tests/vehicle_state_test.cpp) | `CURRENT` |
| <a id="ut-gateway-002"></a>`UT-GATEWAY-002` — clock and GNSS freshness | [Frame acquisition (`REQ-GATEWAY-001`)](#req-gateway-001), [source loss (`REQ-GATEWAY-009`)](#req-gateway-009) | Simulation clock, future/stale/out-of-order/malformed GNSS and recovery | [`gnss_test.cpp`](../../../../carla-ego-runtime/tests/gnss_test.cpp) and vehicle-state clock tests | `CURRENT` for GNSS; full source recovery `PARTIAL` |
| <a id="ut-gateway-003"></a>`UT-GATEWAY-003` — VSS projection and latest store | [Normalization (`REQ-GATEWAY-002`)](#req-gateway-002), [latest-value behavior (`REQ-GATEWAY-003`)](#req-gateway-003), [source identity (`REQ-GATEWAY-005`)](#req-gateway-005) | Paths, values, timestamps, metadata, optional omission and frame ordering | [`vss_projection_test.cpp`](../../../../carla-ego-runtime/tests/vss_projection_test.cpp) | `CURRENT` |
| <a id="ut-gateway-004"></a>`UT-GATEWAY-004` — VISS request semantics | [VISS read service (`REQ-GATEWAY-004`)](#req-gateway-004) | Get, paths filter, Subscribe/Unsubscribe, malformed/unsupported request, reconnect and read-only Set rejection | [`viss_protocol_test.cpp`](../../../../carla-ego-runtime/tests/viss_protocol_test.cpp) | `CURRENT` |
| <a id="ut-gateway-005"></a>`UT-GATEWAY-005` — bounded VISS delivery | [VISS read service (`REQ-GATEWAY-004`)](#req-gateway-004) | Client/subscription/message caps, event drop/coalescing and response priority | Existing VISS protocol fixtures | `CURRENT` |
| <a id="ut-gateway-006"></a>`UT-GATEWAY-006` — control validation and ownership | [Fail-safe control (`REQ-GATEWAY-006`)](#req-gateway-006) | Authentication, exclusive owner, command ranges, pedal conflict, monotonic sequence and invalid modes | [`external_control_protocol_test.py`](../../../../carla-ego-runtime/tests/external_control_protocol_test.py) | `CURRENT` |
| <a id="ut-gateway-007"></a>`UT-GATEWAY-007` — control deadlines and safe stop | [Fail-safe control (`REQ-GATEWAY-006`)](#req-gateway-006) | Startup, command timeout, ownership timeout, release, disconnect and shutdown | Existing control state-machine tests | `CURRENT` |
| <a id="ut-gateway-008"></a>`UT-GATEWAY-008` — live handover decisions | [Continuous handover (`REQ-GATEWAY-007`)](#req-gateway-007) | Lane/alignment gating, idempotent modes, complete context transition outcomes, scenario generation, pedal-safe blend and bounded metrics | Existing handover/protocol tests cover same-actor modes and blend but not the complete context matrix | `PARTIAL` |
| <a id="ut-gateway-009"></a>`UT-GATEWAY-009` — engineering dashboard facts | [Engineering view (`REQ-GATEWAY-008`)](#req-gateway-008), [source loss (`REQ-GATEWAY-009`)](#req-gateway-009) | Connection, rates, event latency, escape-sequence handling and manifest extraction | [`m5_tools_test.py`](../../../../carla-ego-runtime/tests/m5_tools_test.py) | `CURRENT` for existing health; explicit source-state contract `PARTIAL` |
| <a id="ut-gateway-010"></a>`UT-GATEWAY-010` — authoritative QM-channel policy | [Advisory Set (`REQ-GATEWAY-010`)](#req-gateway-010) | Correct Brake/Tire target plus wrong caller/path/type/value, stale/replay/rate/correlation, arbitrary VSS and all motion/safety-operation negatives with no side effects | No implementation | `TARGET` |
| <a id="ut-gateway-011"></a>`UT-GATEWAY-011` — advisory status state machine | [Factual status (`REQ-GATEWAY-011`)](#req-gateway-011) | Accepted/rejected reasons, correlation, bounded state, reconnect and prohibited HMI claims | No implementation | `TARGET` |
| <a id="ut-gateway-012"></a>`UT-GATEWAY-012` — advisory chronology | [Local chronology (`REQ-GATEWAY-012`)](#req-gateway-012) | Source/advisory/Gateway ordering, correlation, missing or inconsistent timestamps and Cloud separation | No implementation | `TARGET` |
| <a id="ut-gateway-013"></a>`UT-GATEWAY-013` — frame-coherent mode/context projection | [Transition projection (`REQ-GATEWAY-013`)](#req-gateway-013) | Closed length-framed schema; owner-only connected stream and Darwin/Linux peer credentials; non-blocking partial-frame/backpressure/EOF/oversize/truncation behavior; exact frame/time joins in both arrival orders; four-per-side/250-ms bounds; missing/drop/duplicate/out-of-order/overflow/expiry whole-group omission; no reconnect or last-known reuse; generation monotonicity; real-frame-only reset/discontinuity lifetime; dashboard separation | Candidate correction not started | `TARGET` |
| <a id="ut-gateway-014"></a>`UT-GATEWAY-014` — hardware-manifest accounting | [Hardware accounting (`REQ-GATEWAY-014`)](#req-gateway-014) | Manifest identity/schema/digest, unique complete every-entry disposition, source/blueprint/sensor/adapter mismatch, unavailable/unsupported handling and qualification/demo-truth rejection | Canonical profile/schema accepted; existing state/projection tests cover only the mapped subset | `PARTIAL` |
| <a id="ut-gateway-015"></a>`UT-GATEWAY-015` — actuator capability/authority/applied state | [Actuator traceability (`REQ-GATEWAY-015`)](#req-gateway-015) | Declared versus authorized actuators, command bounds, accepted/rejected status, applied-state correlation and unauthorized gear/reverse/handbrake cases | Existing control tests cover current throttle/brake/steer authority only | `PARTIAL` |

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| [Frame acquisition (`REQ-GATEWAY-001`)](#req-gateway-001) | [`UT-GATEWAY-002`](#ut-gateway-002), [`UT-GATEWAY-003`](#ut-gateway-003) | Runtime snapshot/status | CARLA state fixture | Live frame correlation | Not separately required |
| [Normalization (`REQ-GATEWAY-002`)](#req-gateway-002) | [`UT-GATEWAY-001`](#ut-gateway-001), [`UT-GATEWAY-003`](#ut-gateway-003) | Runtime projection | VSS path/type/unit fixtures | Live telemetry comparison | G1/G3 telemetry evidence |
| [Latest/unavailable (`REQ-GATEWAY-003`)](#req-gateway-003) | [`UT-GATEWAY-001`](#ut-gateway-001), [`UT-GATEWAY-002`](#ut-gateway-002), [`UT-GATEWAY-003`](#ut-gateway-003) | Store/status metrics | Unavailable VISS cases | Source interruption | Owner qualification only; not a first-demo connectivity step |
| [VISS read (`REQ-GATEWAY-004`)](#req-gateway-004) | [`UT-GATEWAY-004`](#ut-gateway-004), [`UT-GATEWAY-005`](#ut-gateway-005) | Existing TLS network test | D4 VISS conformance suite | Real platform client | G1 live values |
| [Source identity (`REQ-GATEWAY-005`)](#req-gateway-005) | [`UT-GATEWAY-003`](#ut-gateway-003) | VISS metadata | D4 live-handover schema | Sequential selected VU then PU | `AF-X-SOURCE` evidence |
| [Fail-safe control (`REQ-GATEWAY-006`)](#req-gateway-006) | [`UT-GATEWAY-006`](#ut-gateway-006), [`UT-GATEWAY-007`](#ut-gateway-007) | Existing Unix socket test | Control protocol suite | Live safe-stop cases | G0 vehicle operation |
| [Continuous handover (`REQ-GATEWAY-007`)](#req-gateway-007) | [`UT-GATEWAY-008`](#ut-gateway-008) | Controller/UI status | Mode/control contract | Live visual handover | G0 vehicle operation |
| [Engineering view (`REQ-GATEWAY-008`)](#req-gateway-008) | [`UT-GATEWAY-009`](#ut-gateway-009) | Dashboard process/manifest | Read-only VISS subscription | Live telemetry | G0/G4/T1 factual surface |
| [Source loss (`REQ-GATEWAY-009`)](#req-gateway-009) | [`UT-GATEWAY-002`](#ut-gateway-002), [`UT-GATEWAY-009`](#ut-gateway-009) | Source-status transition | D4 degraded-state contract | Link loss/recovery | Owner qualification only; not a first-demo connectivity step |
| [Advisory Set (`REQ-GATEWAY-010`)](#req-gateway-010) | [`UT-GATEWAY-010`](#ut-gateway-010) | TLS Set handler | Typed advisory conformance | VDP-to-Gateway round trip | G4 and T1 advisory proof |
| [Advisory status (`REQ-GATEWAY-011`)](#req-gateway-011) | [`UT-GATEWAY-011`](#ut-gateway-011) | Status publication | Status schema/enum suite | Dashboard subscription | G4/T1 factual receipt |
| [Local chronology (`REQ-GATEWAY-012`)](#req-gateway-012) | [`UT-GATEWAY-012`](#ut-gateway-012) | Correlated timestamp output | Chronology field semantics | Local-path correlation | Separate on-board/Cloud chronology display |
| [Transition projection (`REQ-GATEWAY-013`)](#req-gateway-013) | [`UT-GATEWAY-013`](#ut-gateway-013) | Controller framed-stream join, VSS snapshot and dashboard | Simulator-control handoff record plus reset-sequence fixtures | Live all-transition sequence | G0 truthful mode/context evidence |
| [Hardware accounting (`REQ-GATEWAY-014`)](#req-gateway-014) | [`UT-GATEWAY-014`](#ut-gateway-014) | Startup coverage report | Manifest/adapter coverage fixtures | Live installed-state comparison | G0 complete-profile evidence |
| [Actuator traceability (`REQ-GATEWAY-015`)](#req-gateway-015) | [`UT-GATEWAY-015`](#ut-gateway-015) | Command/result/applied-state record | `IF-VEH-002`/`003`/`001` sequence fixtures | Live accepted/rejected controls | G0 capability-versus-authority proof |

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Safety | [Fail-safe control (`REQ-GATEWAY-006`)](#req-gateway-006) and [advisory Set (`REQ-GATEWAY-010`)](#req-gateway-010) | Safe stop on lost control; advisory cannot control motion | Unit, component and live negative tests |
| Security | [Advisory Set (`REQ-GATEWAY-010`)](#req-gateway-010) | Authenticated private path, exact allowlist, fail closed | Contract and integration negative matrix |
| Data truth | [Normalization (`REQ-GATEWAY-002`)](#req-gateway-002) and [source loss (`REQ-GATEWAY-009`)](#req-gateway-009) | Explicit origin/units and unavailable state | Unit fixtures and live disconnect |
| Resource bounds | [VISS read (`REQ-GATEWAY-004`)](#req-gateway-004) | Latest-value store and bounded client queues | Protocol unit/component metrics |
| Chronology | [Local chronology (`REQ-GATEWAY-012`)](#req-gateway-012) | Source, advisory and receipt timestamps with correlation; no first-demo benchmark | Deterministic clocks and live correlation |
| Observability | [Engineering view (`REQ-GATEWAY-008`)](#req-gateway-008) | Read-only facts; no functional/Cloud/HMI claim | UI inspection and end-to-end evidence |
| Transition truth | [Transition projection (`REQ-GATEWAY-013`)](#req-gateway-013) | Mode, context, generation and discontinuity remain explicit | Contract sequence and live dashboard inspection |
| Hardware completeness | [Hardware accounting (`REQ-GATEWAY-014`)](#req-gateway-014) and [actuator traceability (`REQ-GATEWAY-015`)](#req-gateway-015) | Complete physical profile is accounted before service-facing selection; actuator capability never expands authority silently | Manifest coverage, negative authority matrix and live applied-state comparison |

## D3 Review Closure and Product Acceptance

The component boundary, fifteen requirement obligations, interface ownership,
verification levels and stable `UT-GATEWAY-*` obligations were design-reviewed
on 2026-08-19 and are accepted as input to D4. This closes the `CR-GATEWAY` D3
package; it does not claim that the target advisory path, complete manifest
coverage or every transition behavior is implemented.

Product acceptance remains open until the remaining D4 work freezes the
source-handover/VISS/control-mode/advisory/status contracts, explicit
source-loss and VU/PU binding are qualified, the typed advisory and factual
dashboard extension pass their complete negative matrix, all `UT-*`
obligations are green, and live CARLA plus Validation-Unit integration
evidence is retained.

## Open Issues

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| Implement and qualify the accepted mTLS roles, selected-Unit gate and per-Unit credential lifecycle | Blocks final `REQ-GATEWAY-004` security acceptance; contract choice is closed | Vehicle Gateway + Platform Team + Demo Orchestration | Accepted [`D4-006`](../d4-decision-register.md#d4-006) |
| Implement and qualify the accepted source-status projection, 250 ms freshness and recovery semantics | Blocks complete `REQ-GATEWAY-009`; contract choice is closed | Vehicle Gateway + Platform Team | Accepted [`D4-006`](../d4-decision-register.md#d4-006) |
| Implement and qualify the accepted typed Brake/Tire Request/Status targets, schema, freshness, lease, rate, replay and clear/expiry behavior | Contract choice is closed; blocks `REQ-GATEWAY-010` through `REQ-GATEWAY-012` implementation acceptance | Vehicle Gateway + Platform Team + Function Teams | Accepted [`D4-008`](../d4-decision-register.md#d4-008) |
| Implement and qualify the accepted selected-Unit gate, independent read-only Dashboard peer and bounded VU/PU frame ranges | Blocks complete `REQ-GATEWAY-005`; both contract choices are closed | Demo Orchestration + Vehicle Gateway | Accepted [`D4-005`](../d4-decision-register.md#d4-005) and [`D4-006`](../d4-decision-register.md#d4-006), followed by live qualification |
| Implement the accepted mode/context/scenario/reset VSS projection and context-aware transactional activation | Blocks complete `REQ-GATEWAY-007`, `REQ-GATEWAY-013` and `UT-GATEWAY-008`/`013`; contract choice is closed | Vehicle Gateway + Vehicle Simulation | Accepted [`D4-004`](../d4-decision-register.md#d4-004), followed by implementation and qualification |
| Implement live profile reconciliation and remaining target adapter/actuator coverage against the accepted manifest | Blocks complete `REQ-GATEWAY-014`, `REQ-GATEWAY-015` and `IF-VEH-001`/`IF-VEH-003` qualification; the profile decision itself is closed | Vehicle Gateway + Vehicle Simulation | Accepted [`D4-002`](../d4-decision-register.md#d4-002), followed by implementation and live qualification |

## Change Rules

- Adding a read-only signal inside the accepted Gateway/VDP boundary follows a
  Level-B change and updates VSS fixtures, the relevant component packages and
  tests together.
- Changing control authority, VISS data direction, advisory trust or actuator
  scope follows the Level-C architecture cascade.
- Current all-Set rejection remains the safe baseline until the typed advisory
  contract and its negative tests are accepted.
- Implementation test names may change, but accepted `UT-GATEWAY-*`
  obligations and their requirement mappings remain stable until retired.
