<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R4 — Deterministic CARLA Scenario and Signal Production

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream determines how to create a repeatable obstacle and hard-braking
stimulus, what owns CARLA ticks and actors, and which record becomes the
acceptance oracle across G0–G4.

## Evidence summary

| Finding | Classification |
| --- | --- |
| The current M6 baseline pins `Town10HD_Opt`, a CARLA commit, 30 Hz fixed step, ego blueprint/spawn, Traffic Manager seed, and lane-change behavior. | **PROVEN** |
| Existing controllers already implement map/pre-existing-hero checks, one synchronous tick owner, deterministic spawning, safe stop, owned-actor cleanup, and world-setting restoration. | **PROVEN** |
| `carla-ego-runtime` already runs as `--no-spawn --observe-ticks` and is therefore a non-owning telemetry observer. | **PROVEN** |
| Accepted visual evidence showed stable 30 Hz simulation near the current safe operating speed. | **PROVEN** |
| No scenario state machine, obstacle actor, collision sensor, hard-brake trigger, result contract, or repeated-run qualification exists today. | **PROVEN** |
| A dedicated scenario controller reusing the existing tick-owner pattern is the lowest-risk first implementation. | **PROPOSED** |

Official CARLA guidance supports synchronous mode plus fixed timestep for best
precision, exactly one ticking client, world reload for strongest deterministic
repetition, and synchronous Traffic Manager with a fixed seed.

## Recommended ownership

```text
Dedicated Brake Scenario Controller
  owns world tick, ego, obstacle, collision sensor, control state and cleanup

carla-ego-runtime
  observes ticks, samples vehicle state, maintains VSS and serves VISS

Engineering Dashboard
  independently subscribes to VISS; never controls the scenario
```

The Brake Health service observes the resulting signals. It never commands
the physical braking maneuver.

## Options

| Option | Evaluation |
| --- | --- |
| Dedicated deterministic scenario tick owner | **Recommended.** Small dependency surface, exact frame-based decisions, explicit result and cleanup ownership. |
| Script commands through current keyboard/control socket | Reuses M6, but command deadlines are wall-clock based and obstacle ownership remains missing. |
| Traffic Manager or BehaviorAgent obstacle reaction | Visually realistic but controller-dependent brake onset; useful as a secondary view, not acceptance oracle. |
| ScenarioRunner | Mature, but compatibility with the custom CARLA `0.10.0` development build is unproven and adds a second versioned framework. |
| CARLA recorder/replayer as primary | Helpful for forensics, but a live scripted state machine better demonstrates the active telemetry path. |

## Versioned scenario contract

Define an immutable scenario such as `brake-health-obstacle-v1` containing:

- expected CARLA revision and map;
- ego and obstacle blueprints and exact transforms;
- fixed delta and seed;
- target speed band;
- stabilization and cruise frames;
- conservative braking guard distance;
- brake command;
- stop-speed threshold and maximum duration;
- vehicle-condition profile;
- expected signal-contract version;
- configuration digest.

The obstacle should exist before the controlled approach and become visible as
the ego reaches it. Spawning it immediately in front of a moving vehicle adds
race risk without strengthening the architecture story.

## State machine

1. **PREFLIGHT** — verify CARLA/map/config, one tick owner, no unknown hero or
   scenario-owned actor, and required blueprints.
2. **SPAWN** — create ego, obstacle, and attached collision sensor at fixed
   transforms, then publish them with one synchronous tick.
3. **ACCELERATE** — closed-loop acceleration to a bounded target-speed band.
4. **STABILIZE** — hold that band for a fixed number of simulation frames.
5. **APPROACH** — advance to a fixed frame or route coordinate.
6. **BRAKE** — apply zero throttle, configured hard brake, and fixed steering;
   trigger from simulation frame/time, never wall-clock time.
7. **HOLD** — maintain braking until stationary.
8. **EVALUATE** — require no collision, valid telemetry, expected
   deceleration, stopping margin, and complete evidence.
9. **CLEANUP** — stop/destroy sensor first, destroy only owned actors, restore
   world/TM settings, and verify no owned actor remains.

## Result manifest

Every run should emit one bounded machine-readable record:

```text
scenarioId, scenarioVersion, configurationDigest
CARLA revision, map, fixedDelta
ego/obstacle IDs and transforms
start/stable/brake/stop frames and simulation times
speed at brake onset
peak longitudinal deceleration
braking duration and stopping distance
minimum obstacle separation
collision count and collision frame
VISS first/last frames, gaps and stale counters
vehicleConditionProfile
PASS, FAIL, or ABORTED plus reason codes
cleanup result
```

This manifest is the repeatability and acceptance oracle. The Engineering
Dashboard is the audience surface and may be visually sampled; it is not the
test oracle.

## Reset levels

### Qualification reset

Enable synchronous settings, reload the same world, and batch-spawn the same
actors. A world reload invalidates the previous ego actor, so orchestration
must wait for the new hero and reattach runtime/dashboard observation.

### Presentation fast reset

Destroy only scenario-owned actors/sensors, restore settings and simulated
brake state, then respawn. Permit this shorter path only after repeated strict
reset runs prove equivalent tolerances.

CARLA recorder data can remain an optional diagnostic artifact rather than the
primary G0–G4 replay mechanism.

## Failure behavior

| Failure | Required behavior |
| --- | --- |
| Wrong map/build/config | Abort before spawning. |
| Existing unknown hero or occupied transform | Abort; never delete unknown actors. |
| Obstacle/collision-sensor spawn failure | Abort before motion. |
| Missed trigger or conservative guard crossed | Immediate full-brake safe stop and fail. |
| Collision | Full brake, mark fail, retain bounded evidence, clean owned actors. |
| Second tick source or frame jump | Abort and restore settings. |
| VISS stale/lost | Physical braking continues; observability result fails. |
| Manual input during script | Reject/isolate it; retain a separate emergency-abort action. |
| Cleanup leak | Block the next run until explicit recovery. |
| UI/backend failure | Do not affect braking; mark only presentation evidence incomplete. |
| Wall-clock slowdown | Continue by simulation time and report presentation slowdown separately. |

## Repeatability gate

Run at least 20 strict-reset repetitions before accepting the scenario and
require:

- zero collisions and actor leaks;
- identical state-transition order;
- no duplicate or out-of-order VISS frames;
- brake onset, speed, peak deceleration, stopping distance, and obstacle
  separation inside calibrated bounds;
- identical Brake Health feature vectors within declared numeric tolerances;
- successful world and actor cleanup every time.

The exact tolerances and quantitative definition of `hard braking` are
**REQUIRES EXPERIMENT** and must be calibrated for this build, map, vehicle,
and safe speed.

## Required experiments

1. Unit-test the state machine and configuration without CARLA.
2. Calibrate obstacle transform, brake trigger, stopping margin, and collision
   sensor using the existing safe speed.
3. Run the 20 strict-reset repeatability series.
4. Calibrate wheel order, angular-speed units/sign, effective radius, and slip
   semantics for R5.
5. Exercise telemetry loss, second-tick detection, actor collision, and cleanup
   failure.
6. Compare optional recorder evidence only after the live scenario is accepted.

## Impact on Architecture 1.0

No HLA boundary change is required. `SCENE` becomes a concrete workstation
component and `carla-ego-runtime` remains the Vehicle Gateway observer. The
same scenario digest and vehicle-condition profile should drive G2, G3, and G4;
only the deployed software graph changes.

## Sources

- [`carla-ego-runtime` M6 configuration](../../../../carla-ego-runtime/config/m6_2_town10hd_handover.json)
- [`carla-ego-runtime` external control contract](../../../../carla-ego-runtime/docs/external-control-contract.md)
- [Post-cleanup acceptance](../../qualification/post-cleanup-acceptance.md)
- [CARLA synchrony, timestep, and determinism](https://carla.readthedocs.io/en/latest/adv_synchrony_timestep/)
- [CARLA Python API](https://carla.readthedocs.io/en/latest/python_api/)
- [CARLA collision sensor](https://carla.readthedocs.io/en/latest/core_sensors/#collision-detector)
- [CARLA recorder](https://carla.readthedocs.io/en/latest/adv_recorder/)
- [Official ScenarioRunner repository](https://github.com/carla-simulator/scenario_runner)
