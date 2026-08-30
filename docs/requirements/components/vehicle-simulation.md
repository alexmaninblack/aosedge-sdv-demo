<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vehicle Simulation Component Requirements

- Status: D3 design-reviewed
- Package: [`CR-VEHICLE-SIM`](../component-decomposition-and-interface-register.md#cr-vehicle-sim)
- Version: 0.8
- Prepared: 2026-08-21
- Owner: Vehicle Simulation / Demo Vehicle Tooling
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 2.0](../component-decomposition-and-interface-register.md)
- Accepted D4 decision: [D4-002 Vehicle Hardware Capability Profile](../d4-decision-register.md#d4-002)
- Reviewed D4 working direction: [D4-003 deterministic stimuli and calibration](../d4-decision-register.md#d4-003)
- Accepted D4 control decision: [D4-004 Simulator Control and Context Contract](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Accepted D4 source decision: [D4-005 Exclusive Live-Source Assignment](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Implementation baseline: `CarlaSim@ac7d882c` and `carla-ego-runtime@22864c5`

## Purpose

This package expands the Vehicle simulation allocation into testable
requirements for the virtual physical vehicle and deterministic scenario
controller. It preserves the already working CARLA braking demonstration and
identifies the Tire Health stimulus and complete source-binding proof that
remain to be implemented.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | CARLA physical behavior, the selected Vehicle Hardware Capability Manifest, complete installed signal/actuator behavior, deterministic scenario stimulus, scenario-owned actors and sensors, qualification truth and CARLA-side reset |
| What this package does not own | Control-client authentication, VSS/VISS projection, Domain Controller software, KUKSA, functional analytics, Cloud lifecycle or driver HMI |
| Intended result | One visible vehicle can produce repeatable braking and future tire-degradation evidence without fabricating production signals |
| Accountable lifecycle owner | Vehicle Simulation / Demo Vehicle Tooling; host-side demonstration lifecycle |
| Primary repositories | `CarlaSim` for CARLA and `carla-ego-runtime` for scenario tooling |

## Component Boundary

### In scope

- [CARLA Virtual Physical Vehicle (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla), including road environment, vehicle dynamics, native state and actuators;
- the digest-addressed installed-hardware profile and its signal, sensor,
  actuator, availability and provenance declarations;
- [Deterministic Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene), including obstacle creation, scripted braking, scenario restart and owned-actor cleanup;
- explicit simulation-only truth needed to qualify Tire Health without exposing
  that truth as a production vehicle measurement;
- CARLA-side source identity, frame range and result evidence used by the
  selected Validation or Production Unit binding.

### Out of scope

- [Vehicle Control UI (`CMP-CONTROL`)](../component-decomposition-and-interface-register.md#cmp-control) authentication and arbitration;
- [Vehicle Gateway Runtime (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw) signal normalization and VISS;
- Brake Health or Tire Health inference and Cloud reporting;
- orchestration of the accepted sequential live binding between the one
  visible vehicle source and the two Unit roles;
- a production tire-physics or remaining-useful-life claim.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Native Apple Silicon CARLA baseline | Vehicle Simulation | Accepted repository revision, map and server/API compatibility | Scenario preflight fails before actor creation |
| Gateway actuator interface | Vehicle Gateway | [Gateway actuator commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003) | Scenario enters safe stop or fails without inventing control |
| Town and vehicle profile | Demo Vehicle Tooling | Versioned configuration and deterministic fixed step | Qualification result is rejected as non-reproducible |
| Source-to-Unit selection | Demo Orchestration | Exact sequential live selected Unit, generation and bounded frame range | Evidence cannot be attributed and the stage fails |

## Current Implementation Baseline

| Capability | Evidence | State |
| --- | --- | --- |
| Native CARLA physical vehicle and wheel telemetry | `CarlaSim@ac7d882c`; behavioral source pin `385927b6` in the checked-in scenario profile | `CURRENT` |
| Native capability inventory | [R10 native CARLA inventory](../../research/demo-foundation/r10-carla-telemetry-and-function-team-2.md) distinguishes direct state, attachable sensors, ground truth and unavailable data | Source research `CURRENT`; selected installed-profile manifest and runtime qualification `TARGET` |
| Selected installed-hardware contract | [Vehicle Hardware Capability Profile 1.0.0](../../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.v1.json), SHA-256 `ac0ba26464219482dcb41e56ebbc1538489e13bd6c84725dbc124e59514cb7e5` | D4-002 contract `ACCEPTED`; live reconciliation and complete adapter implementation `TARGET / PARTIAL` |
| Stationary-obstacle braking state machine | [Brake-event design and evidence](../../../../carla-ego-runtime/docs/brake-event-scenario.md) and [hybrid profile](../../../../carla-ego-runtime/config/brake_event_hybrid_town10hd.json) | `CURRENT` |
| Scripted/manual/autopilot/safe-stop continuity | [Live handover design](../../../../carla-ego-runtime/docs/m6-2-live-handover.md) | `CURRENT` jointly with `CR-GATEWAY` |
| Scenario result and cleanup manifest | Brake onset, deceleration, gap, collision, actor and process evidence in the existing launcher workflow | `CURRENT`; repeated-run qualification remains open |
| Pre-aged Tire Health dynamics stimulus | D4-003 selects `preaged-tire-dynamics-v1`, with `HEALTHY` and `PRE_AGED` profiles and a symmetric four-wheel friction reduction; implementation and calibration remain open | Working direction `REVIEWED`; implementation `TARGET` |
| Exact source-to-Unit binding | Run, ego and frame identifiers exist; sequential live VU attach/detach, reset/new generation and PU attach/detach are not implemented | `PARTIAL` |

The current implementation baseline was checked on 2026-08-18 using the
existing native build: all 18 registered `carla-ego-runtime` tests passed. This
is implementation evidence, not acceptance of the target requirements below.

## Testability Boundary

The scenario configuration parser, lane-branch selection, steering helper,
state machine, result evaluator, mode-generation behavior and bounded metrics
are isolated from a live CARLA server and use deterministic fakes in the
existing test suite. Live CARLA physics, actor spawning, collision callbacks,
visual motion and full cleanup are integration or end-to-end concerns and are
not represented as unit tests.

The Tire Health stimulus shall follow the same split: deterministic profile
selection, physics-control application/restoration and state transitions are
unit-testable; CARLA application, resulting dynamics and hidden-truth isolation
require live integration evidence. Calibration and qualification runs occur
before a demonstration; the live demo executes only the frozen qualified
configuration.

## Interface Summary

| Interface | Direction | Data or command | Contract/version | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| [CARLA state to Gateway (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) | Out | Vehicle Hardware Capability Manifest plus frame-coherent value, availability and applied-control state for every installed hardware-equivalent capability | Existing subset plus D4 manifest/coverage contract | Missing or invalid installed state is explicit; no silent omission; qualification-only truth is rejected from this interface | CARLA runtime state and accepted hardware profile |
| [Gateway actuator commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003) | In | Commands for every actuator declared by the profile; initially throttle, brake and steering, with gear/reverse/handbrake capability accounted separately from current UI authorization | Existing CARLA `VehicleControl` subset plus D4 complete actuator contract | Command is applied or explicitly rejected with bounded status; loss selects Gateway safe stop | Gateway control arbitration; CARLA applied state returns through `IF-VEH-001` |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove deterministic scenario decisions, bounds and result classification | CARLA actors and geometry replaced by fakes | Yes | `UT-VEHICLE-SIM-*` obligations in the normal Gateway repository gate |
| Component | Prove the scenario process, configuration and artifact/result lifecycle | Controlled CARLA adapter or live isolated CARLA session | Yes | Scenario controller status, result and cleanup artifacts |
| Contract | Prove expected CARLA revision/API, state shape and control shape | Version and fixture checks | Yes | Frozen D4 CARLA/Gateway contract evidence |
| Integration | Prove obstacle, braking, collision sensor, tire stimulus and cleanup in live CARLA | Pinned Town, vehicle and fixed-step profile | Yes | Repeatable live-run qualification records |
| End-to-end | Prove selected source attribution during G0, G3, T1 and R0 | Full demo Validation and Production lanes | Yes | Stage evidence with Unit, run and frame/trace range |

## Requirement Summary

| Requirement | Plain-language obligation | Implementation | Verification levels |
| --- | --- | --- | --- |
| [Pinned and attributable simulation source (`REQ-VEHICLE-SIM-001`)](#req-vehicle-sim-001) | Identify the exact simulator source and every produced frame range | `PARTIAL` | Unit, Contract, Integration, End-to-end |
| [Deterministic stationary-obstacle braking (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002) | Produce a repeatable physical braking event without teleporting an obstacle into the controlled path | `CURRENT` | Unit, Integration, End-to-end |
| [Continuous hybrid scenario ownership (`REQ-VEHICLE-SIM-003`)](#req-vehicle-sim-003) | Keep one actor and clock while moving among scripted, manual, autopilot and safe stop | `CURRENT` | Unit, Integration, End-to-end |
| [Bounded braking result evidence (`REQ-VEHICLE-SIM-004`)](#req-vehicle-sim-004) | Classify a run from measured motion, gap and collision evidence | `CURRENT` | Unit, Integration |
| [Explicit Tire Health simulation stimulus (`REQ-VEHICLE-SIM-005`)](#req-vehicle-sim-005) | Provide deterministic accelerated/pre-aged degradation with isolated hidden truth | `TARGET` | Unit, Contract, Integration, End-to-end |
| [Owned-actor cleanup and repeatable reset (`REQ-VEHICLE-SIM-006`)](#req-vehicle-sim-006) | Remove scenario-owned state and restore CARLA for the next run | `PARTIAL` | Unit, Integration, End-to-end |
| [Honest single-source operation (`REQ-VEHICLE-SIM-007`)](#req-vehicle-sim-007) | Never present one CARLA source as two simultaneous vehicles | `PARTIAL` | Inspection, Integration, End-to-end |
| [Context-aware obstacle and reset lifecycle (`REQ-VEHICLE-SIM-008`)](#req-vehicle-sim-008) | Keep manual takeover inside the brake event but remove/reset it before free-drive Autopilot | `PARTIAL` | Unit, Contract, Integration, End-to-end |
| [Versioned installed-hardware profile (`REQ-VEHICLE-SIM-009`)](#req-vehicle-sim-009) | Freeze what the selected virtual vehicle physically has, not everything CARLA could theoretically spawn | `PARTIAL` | Unit, Contract, Integration |
| [Complete signal and actuator boundary (`REQ-VEHICLE-SIM-010`)](#req-vehicle-sim-010) | Deliver or explicitly account for every installed capability and keep hidden truth outside the production interface | `PARTIAL` | Unit, Contract, Integration, End-to-end |

## Detailed Requirements

### Pinned and attributable simulation source

<a id="req-vehicle-sim-001"></a>

- ID: `REQ-VEHICLE-SIM-001`
- Statement: The simulation shall reject an incompatible CARLA source and
  shall record the accepted CARLA revision, map, scenario profile, ego actor,
  run identifier, start/end frame and simulation-time range for every retained
  qualification result.
- Parent system requirements: [Exact source-to-Unit binding (`SYS-SRC-001`)](../system-requirements-and-traceability.md#sys-src-001) and [deterministic v2 inference (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [one visible source (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001)
- Required evidence: immutable effective configuration plus source/run/frame metadata in the result manifest
- Requirement state: D3 design-reviewed
- Implementation state: `PARTIAL`; CARLA and frame/run identity exist, while selected Unit attribution is owned jointly with demo orchestration

Acceptance requires incompatible source/map preflight failure, non-empty and
monotonic frame identity for a successful run, and an unambiguous link from the
retained frame range to exactly one selected Unit. Telemetry replay is deferred
beyond the first implementation.

### Deterministic stationary-obstacle braking

<a id="req-vehicle-sim-002"></a>

- ID: `REQ-VEHICLE-SIM-002`
- Statement: From the accepted initial state, the Scenario Controller shall
  create the stationary obstacle before ego motion, follow a deterministic lane
  branch, reach the configured speed band and apply the configured brake input
  at the configured physical gap within bounded simulated time.
- Parent system requirement: [Deterministic v2 inference (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002)
- Architecture flow: [Brake Health predictive runtime (`AF-G3-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-rt)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interfaces: [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003) and [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001)
- Required evidence: phase transitions, obstacle identity, brake-onset frame/speed/gap and immutable profile
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT`

Acceptance rejects an obstacle created after controlled motion begins, an
unbounded route choice, a missed deadline or a brake onset outside the accepted
calibration tolerance.

### Continuous hybrid scenario ownership

<a id="req-vehicle-sim-003"></a>

- ID: `REQ-VEHICLE-SIM-003`
- Statement: Scripted scenario start/restart and transitions to manual,
  autopilot or safe stop shall retain one ego actor, one synchronous tick owner
  and one uninterrupted telemetry run; manual takeover shall mark an unfinished
  scripted attempt aborted rather than passed or failed.
- Parent system requirements: [Exact source-to-Unit binding (`SYS-SRC-001`)](../system-requirements-and-traceability.md#sys-src-001) and [continuous control-mode handover (`SYS-CTRL-002`)](../system-requirements-and-traceability.md#sys-ctrl-002)
- Architecture flow: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt)
- Components: [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene), jointly with [Vehicle Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interface: [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Executable contract: [Simulator Control and Context 1.1.1](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Required evidence: stable actor/run identity, monotonic mode generation, aborted-attempt record and continuous frame range
- Requirement state: D3 design-reviewed; D4-004 contract accepted
- Implementation state: `CURRENT`

Acceptance covers restart, manual takeover during an active attempt, completion
to safe stop and re-entry into the scripted mode without spawning a second ego
vehicle or tick owner.

### Bounded braking result evidence

<a id="req-vehicle-sim-004"></a>

- ID: `REQ-VEHICLE-SIM-004`
- Statement: The scenario shall produce a deterministic pass/fail result from
  collision count, brake-onset speed, peak longitudinal deceleration, stable
  stop and final obstacle gap, preserving exact failure reasons and never
  serializing non-finite metrics as valid values.
- Parent system requirement: [Deterministic v2 inference (`SYS-BHS-002`)](../system-requirements-and-traceability.md#sys-bhs-002)
- Architecture flow: [Brake Health predictive runtime (`AF-G3-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g3-rt)
- Components: [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001)
- Required evidence: structured result and exact failure-reason list
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT`; repeated-run statistical acceptance remains a D4 qualification definition

### Explicit Tire Health simulation stimulus

<a id="req-vehicle-sim-005"></a>

- ID: `REQ-VEHICLE-SIM-005`
- Statement: The Tire Health scenario shall implement the versioned
  `preaged-tire-dynamics-v1` stimulus with `HEALTHY` and `PRE_AGED` profiles.
  `PRE_AGED` shall apply one calibrated symmetric relative reduction to the
  `friction_force_multiplier` of all four wheels before motion, read back the
  applied control, execute one deterministic low-speed
  acceleration/stabilization/left-right-steering/moderate-braking exercise,
  and restore and verify the complete original `VehiclePhysicsControl` on
  completion, exit or failure. The exact profile and multiplier shall remain
  qualification-only truth and shall never enter the Gateway, VISS, KUKSA,
  service, backend or dashboard data path.
- Parent system requirement: [Explicit simulation model (`SYS-TIRE-003`)](../system-requirements-and-traceability.md#sys-tire-003)
- Architecture flow: [Tire Health runtime (`AF-TIRE-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-tire-rt)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001); the hidden truth is explicitly outside this interface
- Required evidence: stimulus version, original/applied/restored physics-control
  digests, profile identity in qualification evidence only, native dynamics,
  collision/cleanup result and proof that the production signal tree excludes
  the profile and multiplier
- Requirement state: D3 design-reviewed; D4-003 working direction reviewed
- Implementation state: `TARGET`; schema, implementation, calibration,
  frozen tolerances and passing repeat series remain open

Acceptance must distinguish native dynamics inputs, derived values and
simulation-only truth. An exact measured tread-depth claim is prohibited unless
a future architecture change introduces a corresponding sensor.

### Owned-actor cleanup and repeatable reset

<a id="req-vehicle-sim-006"></a>

- ID: `REQ-VEHICLE-SIM-006`
- Statement: On normal completion, operator exit, failure or R0 reset, the
  scenario shall safe-stop the ego, destroy only scenario-owned actors and
  sensors, restore changed CARLA world and Traffic Manager settings, remove
  run-local control secrets and report any incomplete cleanup before another
  run begins.
- Parent system requirement: [Reset vehicle simulation state (`SYS-RET-003`)](../system-requirements-and-traceability.md#sys-ret-003)
- Architecture flows: [controlled retirement (`AF-R0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-lc) and [retirement evidence (`AF-R0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-ob)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interface: [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Required evidence: actor/sensor inventory, settings restoration, cleanup status and no leaked run-local secret
- Requirement state: D3 design-reviewed
- Implementation state: `PARTIAL`; normal interactive cleanup is implemented, while a complete repeatable R0 proof is not yet accepted

Factory-image preservation is outside this package. It is independently
allocated to [Factory substrate (`CR-FACTORY`)](../component-decomposition-and-interface-register.md#cr-factory)
and [Demo orchestration (`CR-DEMO`)](../component-decomposition-and-interface-register.md#cr-demo)
under [preserve immutable factory artifact (`SYS-RET-005`)](../system-requirements-and-traceability.md#sys-ret-005).

### Honest single-source operation

<a id="req-vehicle-sim-007"></a>

- ID: `REQ-VEHICLE-SIM-007`
- Statement: When the same CARLA source is used sequentially for Validation and
  Production roles, the scenario evidence and audience surfaces shall show
  the selected role and shall not imply that two vehicles run simultaneously.
- Parent system requirement: [Honest single-source presentation (`SYS-SRC-002`)](../system-requirements-and-traceability.md#sys-src-002)
- Architecture flow: [one visible source (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene)
- Interface: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001)
- Executable contract: [Exclusive Live-Source Assignment 1.0.0](../../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json)
- Required evidence: selected role, Unit, bounded live frame range and presentation label
- Requirement state: D3 design-reviewed; D4-005 contract accepted
- Implementation state: `PARTIAL`; current runs identify CARLA but do not yet implement VU/PU selection and sequential live handover

### Context-aware obstacle and reset lifecycle

<a id="req-vehicle-sim-008"></a>

- ID: `REQ-VEHICLE-SIM-008`
- Statement: The Scenario Controller shall maintain explicit `FREE_DRIVE` and
  `BRAKE_EVENT` world context and implement the complete `AF-X-DRIVE` matrix.
  Manual takeover of an active scripted attempt shall retain the ego pose and
  scenario obstacle; entry to Scenario shall prepare the canonical obstacle,
  reset the same ego actor with zero motion and start a new generation; entry
  to Autopilot from brake-event context shall safe-stop, remove all
  scenario-owned obstacle state and reset the same actor to the accepted
  free-drive start before Traffic Manager can be enabled. Safe stop alone
  shall not reset context. A failed cleanup or reset shall leave safe stop
  active and shall not partially activate the requested mode. Only a real
  completed CARLA frame may carry transition/reset facts: the last such frame
  before a blocking reset may show `PREPARING`, reset in progress and current
  generations; no frame is fabricated while blocked; the first real successful
  post-reset frame carries the incremented reset generation, a new control
  generation where applicable, reset not in progress and one-frame
  discontinuity, which clears on the next real frame. A failed reset without a
  completed frame creates no reset-success evidence.
- Parent system requirements: [Deterministic mode/context transition (`SYS-CTRL-003`)](../system-requirements-and-traceability.md#sys-ctrl-003) and [truthful control-transition evidence (`SYS-OBS-005`)](../system-requirements-and-traceability.md#sys-obs-005)
- Architecture flow: [drive-mode and world-context transitions (`AF-X-DRIVE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-drive)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla) and [Scenario Controller (`CMP-SCENE`)](../component-decomposition-and-interface-register.md#cmp-scene), jointly with [Vehicle Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interface: [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Executable contract: [Simulator Control and Context 1.1.1](../../../contracts/simulator-control-context/simulator-control-context.v1.json)
- Required evidence: complete source-mode/context/target-mode matrix, obstacle inventory, actor identity, exact frame/time-attributed controller records, reset/control generation sequence, zero-motion reset, no fabricated blocking-reset frame, exactly one real discontinuity frame and injected cleanup/reset failures
- Requirement state: D3 design-reviewed; D4-004 contract accepted
- Implementation state: `PARTIAL`; scenario restart, same-actor continuity and manual abort exist, but the obstacle is currently session-lived and Scenario/brake-event Manual to Autopilot does not yet perform the accepted cleanup/reset

Acceptance requires every matrix row to be deterministic and idempotent where
applicable. Collision, missing obstacle, failed destruction, failed reset or
invalid free-drive start must select safe stop. Reverse and Traffic Manager
obstacle avoidance are explicitly outside this package's recovery claims.

### Versioned installed-hardware profile

<a id="req-vehicle-sim-009"></a>

- ID: `REQ-VEHICLE-SIM-009`
- Statement: The Vehicle Simulation shall produce one canonical,
  digest-addressed Vehicle Hardware Capability Manifest for the selected ego
  profile. It shall conform to the accepted
  [schema](../../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.schema.json)
  and exact [profile 1.0.0](../../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.v1.json).
  The profile identifies the checked CARLA source and runtime-compatibility
  revisions, Unreal Engine 5 Chaos, `vehicle.lincoln.mkz`, and every declared
  state source, sensor and actuator with installation, provenance, type, unit,
  frame, cadence or command range, availability and Gateway disposition.
  Optional CARLA facilities that are not instantiated are `NOT_INSTALLED`;
  qualification-only and demo-visualization facilities are explicitly outside
  the production vehicle-data interface.
- Parent system requirement: [Versioned vehicle hardware profile (`SYS-SRC-003`)](../system-requirements-and-traceability.md#sys-src-003)
- Architecture flow: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) and [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Required evidence: exact accepted manifest digest, schema validation,
  source/API inventory comparison and live installed-actor/sensor reconciliation
- Requirement state: D3 design-reviewed; D4-002 contract accepted
- Implementation state: `PARTIAL`; the manifest and source inventory are
  accepted, while live runtime reconciliation is not implemented or qualified

Acceptance distinguishes installed vehicle hardware from CARLA-wide optional
capabilities and from scenario/world ground truth. It prohibits permanent
plausible-looking zero values for native fields that the pinned Chaos runtime
does not populate.

### Complete signal and actuator boundary

<a id="req-vehicle-sim-010"></a>

- ID: `REQ-VEHICLE-SIM-010`
- Statement: For every capability declared installed by the accepted manifest,
  the Simulator shall provide frame-coherent value and availability state to
  the Gateway or an explicit unavailable/reviewed-unsupported reason. It shall
  execute or explicitly reject throttle, brake, steering, handbrake,
  transmission/reverse/manual-shift and vehicle-light commands and return the
  actually applied control state. Physical capability does not grant operator
  or service authority. Qualification-only oracle state, scenario truth,
  demo-only camera output and uninstalled sensor output shall not appear on the
  production Simulator–Gateway vehicle-data interface.
- Parent system requirement: [Complete Simulator–Gateway accounting (`SYS-SRC-004`)](../system-requirements-and-traceability.md#sys-src-004)
- Architecture flows: [working vehicle baseline (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt) and [one visible source (`AF-X-SOURCE`)](../../architecture/demo-scenario-architecture-flows.md#af-x-source)
- Components: [CARLA (`CMP-CARLA`)](../component-decomposition-and-interface-register.md#cmp-carla), jointly with [Gateway (`CMP-GW`)](../component-decomposition-and-interface-register.md#cmp-gw)
- Interfaces: [CARLA state (`IF-VEH-001`)](../component-decomposition-and-interface-register.md#if-veh-001) and [Gateway commands (`IF-VEH-003`)](../component-decomposition-and-interface-register.md#if-veh-003)
- Required evidence: manifest-to-runtime coverage report, positive and unavailable signal fixtures, actuator accepted/rejected/applied-state fixtures and negative proof for qualification-only truth
- Requirement state: D3 design-reviewed; D4-002 contract accepted
- Implementation state: `PARTIAL`; the current Gateway consumes a scalar and wheel subset and controls throttle/brake/steer, while complete installed-profile coverage and gear/reverse/handbrake accounting are not frozen

Acceptance requires every manifest entry to resolve to delivered, explicitly
unavailable, qualification-only, not-installed or reviewed unsupported state;
an entry may not disappear silently. Declaring an actuator in this physical
profile does not grant the current Control UI authority to use it.

## Unit-Test Obligations

| Unit-test obligation | Requirements proved | Behavior and branches | Current evidence | State |
| --- | --- | --- | --- | --- |
| <a id="ut-vehicle-sim-001"></a>`UT-VEHICLE-SIM-001` — profile validation | [Pinned source (`REQ-VEHICLE-SIM-001`)](#req-vehicle-sim-001), [braking stimulus (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002) | Required fields, bounds, fixed step, source/map/profile rejection | [`brake_event_scenario_test.py`](../../../../carla-ego-runtime/tests/brake_event_scenario_test.py) and configuration validation tests | `CURRENT` |
| <a id="ut-vehicle-sim-002"></a>`UT-VEHICLE-SIM-002` — deterministic route and steering | [Braking stimulus (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002) | Heading-first branch choice, stable tie breaking, bounded steering | Existing fake waypoint/transform tests | `CURRENT` |
| <a id="ut-vehicle-sim-003"></a>`UT-VEHICLE-SIM-003` — brake state machine | [Braking stimulus (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002), [hybrid ownership (`REQ-VEHICLE-SIM-003`)](#req-vehicle-sim-003) | Accelerate, stabilize, approach, brake, hold, complete, timeout and restart generation | Existing scenario and protocol tests; timeout branch needs explicit D4 case | `PARTIAL` |
| <a id="ut-vehicle-sim-004"></a>`UT-VEHICLE-SIM-004` — result classification | [Bounded result (`REQ-VEHICLE-SIM-004`)](#req-vehicle-sim-004) | Collision, stop-gap, speed, deceleration and non-finite metric failures | Existing result evaluator and bounded-metrics tests | `CURRENT` |
| <a id="ut-vehicle-sim-005"></a>`UT-VEHICLE-SIM-005` — hybrid attempt accounting | [Hybrid ownership (`REQ-VEHICLE-SIM-003`)](#req-vehicle-sim-003) | Restart, abort on manual takeover, completion to safe stop, actor/run continuity | Existing mode-generation tests; full attempt ledger needs an explicit case | `PARTIAL` |
| <a id="ut-vehicle-sim-006"></a>`UT-VEHICLE-SIM-006` — tire stimulus model | [Tire stimulus (`REQ-VEHICLE-SIM-005`)](#req-vehicle-sim-005) | Initial condition, deterministic progression, threshold boundaries, reset and hidden-truth separation | No implementation | `TARGET` |
| <a id="ut-vehicle-sim-007"></a>`UT-VEHICLE-SIM-007` — cleanup reconciliation | [Cleanup (`REQ-VEHICLE-SIM-006`)](#req-vehicle-sim-006) | Normal, interrupted, partially failed and repeated cleanup with owned versus foreign actors | Launcher cleanup checks exist; actor/sensor reconciliation test is missing | `PARTIAL` |
| <a id="ut-vehicle-sim-008"></a>`UT-VEHICLE-SIM-008` — mode/context transition and reset emission | [Context lifecycle (`REQ-VEHICLE-SIM-008`)](#req-vehicle-sim-008) | Every source mode/context/target mode, repeated requests, obstacle create/remove, same-actor reset, abort, collision, real-frame-only PREPARING/post-reset sequence, exactly one discontinuity frame, failed-reset no-evidence behavior and injected cleanup/reset failures | Existing scenario-generation and manual-abort tests cover only part of the matrix | `PARTIAL` |
| <a id="ut-vehicle-sim-009"></a>`UT-VEHICLE-SIM-009` — capability-manifest validation | [Hardware profile (`REQ-VEHICLE-SIM-009`)](#req-vehicle-sim-009) | Required identity/schema fields, unique capabilities, units/frames/ranges, provenance classes, digest stability and installed/not-installed distinction | Canonical profile/schema accepted; repository validator and live reconciliation remain missing | `PARTIAL` |
| <a id="ut-vehicle-sim-010"></a>`UT-VEHICLE-SIM-010` — signal/actuator coverage and truth isolation | [Complete boundary (`REQ-VEHICLE-SIM-010`)](#req-vehicle-sim-010) | Every manifest entry accounted, signal unavailable behavior, command accept/reject/applied state and qualification-only negative cases | Existing scalar/control tests cover only the current subset | `PARTIAL` |

All obligations use deterministic fakes and require no live CARLA process.
Physical dynamics and actual actor cleanup remain integration obligations.

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| [Pinned source (`REQ-VEHICLE-SIM-001`)](#req-vehicle-sim-001) | [`UT-VEHICLE-SIM-001`](#ut-vehicle-sim-001) | Effective-config/result manifest | CARLA/Gateway D4 source contract | Version/map/frame preflight | `AF-X-SOURCE` selected Unit evidence |
| [Braking stimulus (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002) | [`UT-VEHICLE-SIM-002`](#ut-vehicle-sim-002), [`UT-VEHICLE-SIM-003`](#ut-vehicle-sim-003) | Scenario process status/result | `IF-VEH-001`/`IF-VEH-003` fixtures | Repeated live braking run | G3 audience-visible event |
| [Hybrid ownership (`REQ-VEHICLE-SIM-003`)](#req-vehicle-sim-003) | [`UT-VEHICLE-SIM-003`](#ut-vehicle-sim-003), [`UT-VEHICLE-SIM-005`](#ut-vehicle-sim-005) | Controller status and attempt ledger | External-control D4 contract | Live handover without actor/frame reset | G0 vehicle-operation evidence |
| [Bounded result (`REQ-VEHICLE-SIM-004`)](#req-vehicle-sim-004) | [`UT-VEHICLE-SIM-004`](#ut-vehicle-sim-004) | Structured result schema | D4 evidence schema | Accepted repeated-run calibration | Not separately required |
| [Tire stimulus (`REQ-VEHICLE-SIM-005`)](#req-vehicle-sim-005) | [`UT-VEHICLE-SIM-006`](#ut-vehicle-sim-006) | Versioned stimulus component | Hidden-truth/production-data separation | Live dynamics response | T1 condition-estimation proof |
| [Cleanup (`REQ-VEHICLE-SIM-006`)](#req-vehicle-sim-006) | [`UT-VEHICLE-SIM-007`](#ut-vehicle-sim-007) | Cleanup manifest | Owned-actor inventory schema | Interrupted and repeated cleanup | R0 retirement evidence |
| [Honest source (`REQ-VEHICLE-SIM-007`)](#req-vehicle-sim-007) | Reasoned N/A: presentation/source selection is cross-component | Role-labelled result | Live handover contract | Sequential VU attach/detach, reset and PU attach/detach qualification | `AF-X-SOURCE` audience evidence |
| [Context lifecycle (`REQ-VEHICLE-SIM-008`)](#req-vehicle-sim-008) | [`UT-VEHICLE-SIM-008`](#ut-vehicle-sim-008) | Context/obstacle/reset state machine | `AF-X-DRIVE` transition plus controller-handoff reset fixtures | Live all-transition matrix | G0 mode/context/dashboard evidence |
| [Hardware profile (`REQ-VEHICLE-SIM-009`)](#req-vehicle-sim-009) | [`UT-VEHICLE-SIM-009`](#ut-vehicle-sim-009) | Canonical manifest and digest | Manifest/schema/coverage contract | Live actor/sensor reconciliation | G0 hardware-profile evidence |
| [Complete boundary (`REQ-VEHICLE-SIM-010`)](#req-vehicle-sim-010) | [`UT-VEHICLE-SIM-010`](#ut-vehicle-sim-010) | Runtime coverage report | `IF-VEH-001`/`IF-VEH-003` complete fixtures | Live signal/control comparison | G0 no-silent-loss evidence |

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Safety | [Cleanup (`REQ-VEHICLE-SIM-006`)](#req-vehicle-sim-006) | Safe stop precedes owned actor destruction | Unit plus interrupted live run |
| Provenance | [Pinned source (`REQ-VEHICLE-SIM-001`)](#req-vehicle-sim-001) | Revision, profile, run, ego and frame range are retained | Manifest inspection and source binding |
| Timing | [Braking stimulus (`REQ-VEHICLE-SIM-002`)](#req-vehicle-sim-002) | Fixed simulated step and bounded phase duration | Unit clock fixtures and live cadence evidence |
| Truth separation | [Tire stimulus (`REQ-VEHICLE-SIM-005`)](#req-vehicle-sim-005) | Hidden degradation truth never enters the production signal contract | Contract-negative test and end-to-end inspection |
| Resource bounds | [Bounded result (`REQ-VEHICLE-SIM-004`)](#req-vehicle-sim-004) | Bounded actors, sensors, duration and result size | Component and cleanup evidence |
| Transition truth | [Context lifecycle (`REQ-VEHICLE-SIM-008`)](#req-vehicle-sim-008) | Explicit context and generation expose every reset discontinuity | Unit matrix plus live dashboard inspection |
| Hardware completeness | [Hardware profile (`REQ-VEHICLE-SIM-009`)](#req-vehicle-sim-009) and [complete boundary (`REQ-VEHICLE-SIM-010`)](#req-vehicle-sim-010) | Every installed signal and actuator is versioned and accounted without confusing optional CARLA APIs with installed hardware | Manifest unit/contract checks plus live reconciliation |

## D3 Review Closure and Product Acceptance

The component boundary, ten requirement obligations, interface ownership,
verification levels and stable `UT-VEHICLE-SIM-*` obligations were
design-reviewed on 2026-08-19 and are accepted as input to D4. This closes the
`CR-VEHICLE-SIM` D3 package; it does not claim that every target behavior is
implemented or qualified.

Product acceptance remains open until the source-selection owner closes the
VU/PU attribution boundary, the Tire Health stimulus design is accepted,
repeated live Brake Event qualification passes, cleanup failure/recovery is
proved, every `UT-*` obligation is green or has a reviewed exception, and the
repository and documentation gates pass.

## Open Issues

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| Implement and qualify the accepted sequential VU/PU live-source assignment and bounded frame evidence | Blocks complete `REQ-VEHICLE-SIM-001` and `REQ-VEHICLE-SIM-007`; contract choice is closed | Demo Orchestration + Vehicle Simulation | Accepted [`D4-005`](../d4-decision-register.md#d4-005), followed by implementation and qualification |
| Implement the reviewed `preaged-tire-dynamics-v1` stimulus, schema, physics restoration and oracle-negative proof | Blocks `REQ-VEHICLE-SIM-005` and `UT-VEHICLE-SIM-006` | Vehicle Simulation + Function Team 2 | [`D4-003`](../d4-decision-register.md#d4-003) closure |
| Calibrate exact Tire values and absolute tolerances, then pass the frozen Brake 20/20 and Tire 10+10 strict-reset qualification series | Blocks final stimulus acceptance; calibration runs are not acceptance runs | Vehicle Simulation + both Function Teams | [`D4-003`](../d4-decision-register.md#d4-003) closure and D4-026 overall qualification |
| Define reconciliation after partial actor/sensor cleanup | Blocks complete R0 reset proof | Vehicle Simulation + Demo Orchestration | D4 failure/recovery cases |
| Implement the accepted dynamic obstacle, transactional activation and context-aware reset matrix | Blocks complete `REQ-VEHICLE-SIM-008` and honest transition evidence; contract choice is closed | Vehicle Simulation + Vehicle Gateway | Accepted [`D4-004`](../d4-decision-register.md#d4-004), followed by implementation and qualification |
| Implement schema enforcement, live installed-actor/sensor reconciliation and remaining target signal/actuator coverage against the accepted profile | Blocks complete `REQ-VEHICLE-SIM-009`, `REQ-VEHICLE-SIM-010` and `IF-VEH-001`/`IF-VEH-003` qualification; the contract itself is no longer open | Vehicle Simulation + Vehicle Gateway | Accepted [`D4-002`](../d4-decision-register.md#d4-002), followed by implementation and live qualification |

## Change Rules

- Editing scenario thresholds without changing their semantics preserves IDs
  but produces a new immutable profile version and qualification evidence.
- Changing physical stimulus semantics, hidden-truth exposure, control ownership
  or CARLA/Gateway data direction requires the architecture cascade.
- Existing test function names may change, but accepted `UT-VEHICLE-SIM-*`
  obligations and their requirement mappings remain stable until retired.
