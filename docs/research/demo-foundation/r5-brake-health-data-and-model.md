<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R5 — Brake Health Data Contract and Demo Model

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream defines the P1/P2/P3 data progression, where simulated brake
condition belongs, and which on-vehicle model can be deterministic,
understandable, and honest for the demonstration.

## Recommendation

Use a transparent versioned demo model based on:

1. deterministic hard-braking events;
2. per-wheel simulated pad-wear state;
3. braking-energy and temperature proxies;
4. a prediction expressed as remaining equivalent severe-braking events before
   a configured simulated wear threshold.

Do not call this production diagnostics, probability of brake failure, actual
remaining useful life, a validated thermal twin, or a model trained live.

## Current data baseline

| Finding | Classification |
| --- | --- |
| The Gateway samples velocity, vehicle-frame acceleration, throttle, brake, steering, gear, RPM, and front-wheel steering angles. | **PROVEN** |
| Its VSS projection includes speed, three accelerations, pedal proxies, steering, gear/RPM, GNSS, and simulation metadata. | **PROVEN** |
| The brake value is the last applied control proxy, not hydraulic pressure. | **PROVEN** |
| Current telemetry contract `0.1.1` publishes seven KUKSA paths, expects nominal 30/minimum 20 Hz, and marks values unavailable after 250 ms. | **PROVEN** |
| Qualification observed atomic KUKSA batches near 20 Hz. | **PROVEN** |
| Brake Health Service is still only a package scaffold with no KUKSA or model behavior. | **PROVEN** |

The local custom CARLA build also exposes per-wheel lateral slip, longitudinal
slip magnitude, and angular velocity from Chaos physics. The Gateway does not
currently copy these wheel values into normalized state.

Wheel order, angular-velocity unit/sign, effective tire radius, and slip
semantics are **REQUIRES EXPERIMENT** before standard VSS mapping.

## Standards and provenance

VSS 6.0 contains standard paths for:

- per-wheel speed and angular speed;
- per-wheel brake pad wear;
- brake pedal position;
- driver emergency braking detection;
- ABS and EBA engaged state.

Do not assert `IsDriverEmergencyBrakingDetected` for an autopilot/script event,
or ABS/EBA engaged merely because the brake command is high. Those standard
booleans have specific behavioral meanings. VSS 6.0 has no standard brake
rotor temperature or cumulative braking-energy signal; use clearly named
project overlay entries rather than reusing unrelated tire signals.

Every expanded value should declare one provenance class:

- `SIMULATOR_PHYSICS` — direct CARLA/Chaos value;
- `CONTROL_PROXY` — requested/applied control;
- `DERIVED_ESTIMATE` — calculated from physical signals;
- `SIMULATED_COMPONENT_STATE` — intentionally simulated vehicle condition.

The Function Dashboard must visibly label estimated and simulated values.

## Version progression

| Element | Contract and behavior |
| --- | --- |
| P1 | Brake Health Data v1: four read-only base signals |
| S1 | Requires Data v1+: bounded relay/visualization; no diagnosis |
| P2 | Data v2: backward-compatible v1 superset plus calibrated wheel and simulated brake-health state |
| S2 | Requires Data v2+: local event extraction and deterministic inference; asynchronous Cloud report |
| P3 | Data v2 unchanged plus separate Advisory Capability v1 |
| S3 | Requires Data v2 + Advisory v1: reuses S2 inference, requests local advisory, works offline |

This keeps bidirectionality separate from the telemetry schema. The scenario
may call the combined graph `VDP Component v3`, while implementation can use
separate inbound and outbound providers.

## P1 and Service v1

P1 exposes exactly:

- `Vehicle.Speed`;
- `Vehicle.Acceleration.Longitudinal`;
- `Vehicle.Chassis.Brake.PedalPosition`;
- `Vehicle.Chassis.Accelerator.PedalPosition`.

If the audience claim is that only the approved v1 subset reaches KUKSA, P1
cannot simply publish all seven current profile signals. Timing semantics are
nominal 30 Hz source, approximately 20 Hz qualified KUKSA output, 250 ms
freshness bound, and no zero substitution for unavailable values.

S1:

- subscribes through KUKSA only;
- validates type and freshness;
- down-samples to a bounded Function Backend rate, with 5 Hz as a candidate;
- may publish one-second min/max/mean/latest aggregates;
- displays speed, brake, acceleration, and freshness;
- performs no health classification or advisory.

The exact rate and aggregation are **REQUIRES EXPERIMENT** for smoothness,
bandwidth, and offline behavior.

## P2 signal expansion

P2 is a backward-compatible P1 superset adding:

1. calibrated per-wheel speed or angular speed using standard VSS paths and
   `SIMULATOR_PHYSICS` provenance;
2. per-wheel `...Brake.PadWear` using standard VSS paths and
   `SIMULATED_COMPONENT_STATE` provenance;
3. project-overlay per-wheel estimated rotor temperature in Celsius;
4. project-overlay per-wheel cumulative braking-energy proxy in joules or
   kilojoules;
5. source timestamp, availability, provenance, and contract/model metadata.

No simulated hydraulic pressure is needed initially. P1 already carries a
brake-demand proxy, and relabeling it as pressure would be misleading.
Deceleration-versus-demand and wheel-speed asymmetry are S2 derived features,
not additional source sensors.

## Placement of simulated brake state

```text
CARLA physics
  -> Vehicle Gateway sampling
  -> simulated brake component state and derived estimates
  -> VSS/VISS
  -> platform provider
  -> KUKSA
  -> Brake Health service
```

The simulated state must not originate inside the service or provider. This is
what makes the scenario honest: the vehicle already has the data, and the
Platform Team makes it available to services through P2.

A fixed condition profile such as `normal` or
`degraded-front-right-pad` belongs in the scenario contract and resets with the
CARLA world.

## Transparent demo plant

For each braking event, use an energy proxy:

```text
deltaEnergy = max(0, 0.5 * effectiveMass *
                  (startSpeed^2 - endSpeed^2)) * brakeFraction
```

Distribute that proxy by versioned front/rear and left/right factors. For each
wheel, update a first-order cooling/heat estimate and cumulative wear:

```text
nextTemperature = ambient
  + (temperature - ambient) * exp(-deltaTime / coolingTimeConstant)
  + heatFraction * wheelEnergy / thermalCapacity

nextWear = wear + wearCoefficient * wheelEnergy
```

All coefficients, initial conditions, bounds, and the condition profile are
versioned configuration rather than hidden constants. Real brake thermal
behavior is substantially richer; this remains an energy/temperature proxy.

## Service v2 event and model

The event detector:

- arms above a minimum speed;
- starts a severe-braking event only after brake demand and measured
  deceleration satisfy calibrated conditions for a physical duration;
- closes after stop or brake release;
- uses timestamps, never fixed sample counts;
- returns `NOT_EVALUATED` when mandatory input is stale or incomplete.

Per-event features include initial/final speed, peak/mean deceleration, brake
peak/duration, stopping-time/distance proxy, energy proxy, wheel asymmetry,
estimated temperature, pad wear, freshness, contract identity, and model
identity.

The model projects per-wheel equivalent events:

```text
remainingEquivalentEvents =
  (configuredWearLimit - currentWear)
  / max(EWMAWearPerReferenceEvent, epsilon)
```

Output states:

- `NOT_EVALUATED`;
- `NOMINAL`;
- `WATCH`;
- `INSPECTION_RECOMMENDED`.

Audience language should be:

> Deterministic demo estimate of equivalent severe-braking events remaining
> before the configured simulated wear threshold.

The result contract includes event/unit pseudonyms, times, data/model versions
and digest, `processingLocation = ON_VEHICLE`, state, score, remaining-event
estimate, reason codes, quality, simulated/estimated input lists, local
latency, and `demoOnly = true`.

## Why this model

| Option | Evaluation |
| --- | --- |
| Wear + energy event projection | **Recommended:** explainable, deterministic, safe, versionable, offline-capable |
| Temperature-only | Visually strong but poorly excited at the current safe speed without conspicuous demo tuning |
| Brake demand vs deceleration efficiency | Useful secondary feature but confounded by road, slope, speed, drag, and mass |
| Physically reduce per-wheel brake torque | Dramatic but adds collision risk and extensive calibration; defer |
| Untrained ML anomaly model | Not credible without dataset, labels, and validation lifecycle; reject |

## P3 and Service v3 boundary

P3 retains P2 reads and adds one least-privilege advisory capability. S3 reuses
the exact accepted S2 model, requests an inspection advisory only for accepted
local results, operates while disconnected, queues its report with original
event time, and never claims driver display or acknowledgement. Detailed
KUKSA/VISS authorization belongs to R6.

## Required experiments

1. Calibrate wheel ordering, omega unit/sign, effective radius, and slip.
2. Replay fixed VISS/KUKSA traces for fresh, stale, missing, duplicate, and
   out-of-order data near the qualified 20 Hz rate.
3. Compare normal and seeded degraded vehicle-condition profiles.
4. Require byte-equivalent model results for identical trace/model digests,
   excluding processing-time fields.
5. Calibrate hard-brake thresholds, plant coefficients, and decision bounds.
6. Review parameter sensitivity so the visible result does not depend on one
   accidental constant.
7. Measure S1 dashboard rate/aggregation and S2 event-envelope size.
8. Integrate on Validation only after signal and model contracts are approved.

## Impact on Architecture 1.0

No new top-level ECU is needed. The HLA should later clarify that simulated
brake component state and derived vehicle-side estimates are an internal
Vehicle Gateway responsibility. Requirements must separately cover scenario
determinism, provenance, P1/P2 compatibility, S1 relay, S2 inference/model
identity, P3 advisory semantics, and cross-surface trace correlation.

## Sources

- [`carla-ego-runtime` telemetry contract](../../../../carla-ego-runtime/docs/telemetry-contract.md)
- [`aos-vehicle-platform` telemetry profile](../../../../aos-vehicle-platform/contracts/vehicle-telemetry-profile/)
- [Current CARLA-to-KUKSA qualification](../../qualification/carla-viss-to-kuksa.md)
- [COVESA VSS 6.0 wheel signals](https://raw.githubusercontent.com/COVESA/vehicle_signal_specification/v6.0/spec/Chassis/Wheel.vspec)
- [COVESA VSS 6.0 chassis signals](https://raw.githubusercontent.com/COVESA/vehicle_signal_specification/v6.0/spec/Chassis/Chassis.vspec)
- [COVESA VSS 6.0 ADAS signals](https://raw.githubusercontent.com/COVESA/vehicle_signal_specification/v6.0/spec/ADAS/ADAS.vspec)
- [Aerodynamic and Thermal Modelling of Disc Brakes](https://www.mdpi.com/1996-1073/13/1/203)
- [Current Demo Scenario 1.6](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
