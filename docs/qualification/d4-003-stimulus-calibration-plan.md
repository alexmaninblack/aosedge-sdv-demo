<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# D4-003 Brake and Tire Stimulus Calibration Plan

- Status: approved working direction; calibration not yet executed
- Version: 0.1
- Prepared: 2026-08-21
- Decision owner: [`D4-003`](../requirements/d4-decision-register.md#d4-003)
- Implementation, CARLA execution or qualification authorized by this document: no

## Purpose

This plan separates pre-demonstration engineering calibration and
qualification from the audience-facing live demonstration. The live
demonstration never compiles, tunes, calibrates or chooses a coefficient. It
executes one previously accepted immutable stimulus profile.

The plan owns physical stimulus and qualification truth. Brake Health and Tire
Health service algorithms, thresholds, payloads and advisory policies remain
owned by `D4-016` and `D4-018`.

## Shared Invariants

1. CARLA runs with the accepted hardware profile, one synchronous tick owner
   and simulation time rather than wall-clock decision timing.
2. Every stimulus has one version, canonical configuration digest, CARLA and
   hardware-profile identity, exact initial state and bounded result schema.
3. Scenario/world truth is available only to the qualification harness. It is
   absent from Gateway production state, VISS, KUKSA, service inputs,
   functional payloads and audience dashboards.
4. A failed run is never discarded and silently retried into a passing result.
   The failure reason remains in the qualification series.
5. Strict reset restores the CARLA world, actors, sensors and vehicle physics
   and proves that no scenario-owned state remains before another run.
6. Presentation uses one live run per selected stage. Calibration and repeat
   series are completed and accepted beforehand.

## Brake Stimulus Direction

The implemented `stationary-obstacle-braking-v1` is the current calibration
input. Its unattended qualification profile is
`carla-ego-runtime/config/brake_event_town10hd.json`, currently SHA-256
`5449b17e3a02a7104111c284f281e4a355c1801981949ff0759c716d4e4827a5`.
The interactive hybrid launcher shall use the same canonical scenario core;
duplicate parameter copies may not drift.

| Parameter | Current value |
| --- | ---: |
| Map | `Carla/Maps/Town10HD_Opt` |
| Fixed simulation step | 1/30 s |
| Ego and obstacle blueprint | `vehicle.lincoln.mkz` |
| Obstacle placement | 70 m before motion |
| Target speed | 20 km/h |
| Target-speed tolerance | ±1 km/h |
| Brake-trigger gap | 13 m |
| Brake command | 0.75 |
| Stable-stop threshold | ≤0.3 km/h for 12 frames |
| Hold time | 2 s |
| Accepted final gap | 2–11 m |
| Minimum peak deceleration magnitude | 2.5 m/s² |
| Maximum scenario duration | 40 s |
| Accepted collisions | 0 |

The Brake physical stimulus does not create native pad wear, brake pressure,
brake temperature or Brake Health ground truth. Its qualification-only truth
is scenario identity, obstacle geometry, phase/frame chronology, collision
state and measured physical result. The synthetic v2 assessment is driven by
the visible braking episode and is defined later by `D4-016`.

## Tire Stimulus Direction

The first implementation shall use `preaged-tire-dynamics-v1` with two
profiles:

- `HEALTHY`: retain the selected vehicle's original wheel physics;
- `PRE_AGED`: apply one calibrated relative reduction to the
  `friction_force_multiplier` of all four wheels before motion.

The Scenario Controller shall save the complete original
`VehiclePhysicsControl`, apply and read back the selected profile, run one
bounded low-speed acceleration/stabilization/left-right-steering/moderate-
braking exercise, restore the exact original physics and verify restoration.
Using the same relative factor on all wheels is the safe first-demo choice: it
avoids an intentionally induced asymmetric yaw while still exciting native
wheel-speed and slip behavior.

Only native dynamics declared by the accepted hardware profile are visible to
the service: speed, acceleration, steering/applied controls, wheel angular and
linear speed, and wheel slip. The exact profile and friction multiplier are
qualification-only truth. The Tire service shall estimate a condition band;
it shall not receive or claim measured tread depth, exact wear, tire pressure,
temperature or production diagnostic accuracy.

The exact exercise values and `PRE_AGED` multiplier remain calibration
outputs. They shall not be invented in documentation or changed during a
presentation.

## Pre-Demonstration Calibration

Calibration is engineering work performed before the independent acceptance
series:

1. execute five strict-reset Brake runs and five strict-reset runs for each
   Tire profile;
2. confirm safe vehicle behavior and complete cleanup;
3. select the Tire exercise values and relative friction multiplier;
4. select absolute metric bounds and feature-separation margins from the
   observed stable region with reviewed engineering guard bands;
5. freeze new immutable configuration versions and digests; and
6. discard calibration runs from the independent qualification pass/fail
   population while retaining their engineering record.

Bounds are frozen before qualification. Qualification may not derive new
limits from the same runs it judges.

## Independent Qualification

### Brake

Run 20 strict-reset repetitions. Acceptance requires 20/20 runs to satisfy the
frozen physical bounds, zero collisions and actor/sensor leaks, identical
phase order, valid monotonic frame evidence, complete Gateway-visible source
coverage and successful cleanup.

### Tire

Run 10 `HEALTHY` and 10 `PRE_AGED` strict-reset repetitions. Acceptance
requires every run to remain safe and within its frozen physical bounds,
successful physics restoration, no oracle leakage and the frozen native-
dynamics feature separation between the two profiles. Tire Health model-band
accuracy is not judged here; deterministic estimator behavior belongs to
`D4-018`.

## Required Result Record

Each run records, without credentials or private Cloud identity:

- stimulus/profile/version and configuration digest;
- CARLA, hardware-profile, map, ego and scenario identity;
- strict-reset generation and start/end frame/simulation time;
- phase transitions and bounded physical metrics;
- qualification-only profile/oracle reference in a separated evidence field;
- Gateway-visible frame range and missing/stale counters;
- `PASS`, `FAIL` or `ABORTED` with exact reason codes; and
- actor, sensor, vehicle-physics and world-settings cleanup result.

## D4-003 Closure Gate

`D4-003` remains `RESEARCHING` until:

1. one canonical schema covers both stimulus profiles and result records;
2. the Tire stimulus and original-physics restoration are implemented and
   unit-tested;
3. calibration freezes exact Tire values and all numeric tolerances;
4. the 20-run Brake and 10+10 Tire independent series pass; and
5. oracle-negative checks pass across Gateway, VISS, KUKSA, service fixtures,
   functional payloads and dashboards.

`D4-026` later defines the overall system qualification modes and presenter
flow. It may reference these accepted stimulus-specific series but shall not
silently replace their bounds or repeat counts.
