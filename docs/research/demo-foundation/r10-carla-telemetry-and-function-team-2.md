<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R10 — Native CARLA Vehicle Telemetry Inventory

Status: **research complete; original Function Team 2 candidate superseded by
ADR 0008**.

## Purpose and boundary

This checkpoint inventories what the examined CARLA simulator itself can
produce for a simulated vehicle. It is intentionally independent of the
current VISS tree, Vehicle Data Platform provider, KUKSA configuration, and
AosEdge service deployment.

Those later layers will decide which selected CARLA data becomes part of the
vehicle's service-facing contract. They must not constrain the initial CARLA
capability inventory.

## Examined CARLA baseline

| Item | Value |
| --- | --- |
| Source revision | `0.10.0-191-gac7d882ca` |
| Exact commit | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| Vehicle physics | Unreal Engine 5 Chaos |
| Runtime telemetry API | Upstream UE5 `VehicleTelemetryData` plus the project's wheel-steering correction |

The inventory distinguishes four kinds of data:

1. **vehicle/actor state** — queryable directly without attaching a sensor;
2. **built-in sensor output** — native CARLA sensors attached to the vehicle;
3. **simulator ground truth/context** — map and world knowledge that a real
   vehicle would obtain through a different subsystem;
4. **not natively available** — values requiring an explicit simulated
   component model or deeper physics implementation.

## 1. Direct vehicle and actor state

### Identity and pose

CARLA exposes:

- actor ID, blueprint/type, role and blueprint attributes;
- vehicle location `x/y/z` in world coordinates;
- orientation as roll, pitch, and yaw;
- the complete transform;
- vehicle bounding box;
- component, socket, and skeletal-bone transforms where the actor provides
  them.

### Kinematics

Every world snapshot exposes:

- three-axis linear velocity in m/s;
- three-axis angular velocity in degrees/s;
- three-axis acceleration in m/s².

These are world-coordinate values. A client can transform them into the
vehicle coordinate system and derive forward speed, longitudinal/lateral/
vertical acceleration, yaw rate, jerk, traveled distance, and similar
features.

### Controls and transmission

The vehicle API exposes the last applied control:

- throttle in `[0, 1]`;
- steering command in `[-1, 1]`;
- brake in `[0, 1]`;
- handbrake state;
- reverse state;
- manual-gear-shift state;
- requested/current gear.

These are control inputs or state proxies, not measured pedal travel,
hydraulic brake pressure, or actuator current.

### Live Chaos vehicle telemetry

The examined CARLA source exposes one live runtime record containing:

- forward speed;
- last applied steer, throttle, and brake;
- engine RPM;
- current gear;
- for every wheel:
  - lateral slip angle;
  - longitudinal slip magnitude;
  - angular velocity.

The physical steering angle of an individual wheel is also queryable. Vehicle
physics configuration supplies the wheel radius, so a client can derive each
wheel's linear speed from angular velocity.

The current Chaos implementation deliberately does **not** report legacy
PhysX-style live tire load, wheel torque, longitudinal/lateral force, or
normalized force. The corresponding Chaos debug members are not populated;
reporting them would create plausible-looking permanent zeroes.

### Vehicle and road-interaction state

CARLA also exposes:

- vehicle light-state flags: position, low/high beam, brake, indicators,
  reverse, fog, interior, and special lights;
- current speed limit affecting the vehicle;
- whether a traffic light currently affects the vehicle;
- the current traffic-light state and traffic-light actor;
- vehicle failure state. The API defines rollover, engine, and tire-puncture
  values, but the current documentation states that only rollover is actually
  implemented as a meaningful failure state.

## 2. Built-in sensors attachable to the vehicle

These sensors exist in the examined CARLA source and do not require creation
of a new physical sensor model. They still require spawning, configuration,
synchronization, ownership, and consumer code.

### Motion and position

| Sensor | Native output |
| --- | --- |
| GNSS | Latitude, longitude, altitude, frame, simulation timestamp, sensor pose; configurable bias/noise |
| IMU | Three-axis accelerometer, three-axis gyroscope in rad/s, compass heading, frame/time/pose; configurable bias/noise |

### Event detectors

| Sensor | Native output |
| --- | --- |
| Collision | One event per collision/frame with the other actor and three-axis normal impulse |
| Lane invasion | Event with all lane markings crossed by the vehicle footprint |
| Obstacle detector | Detected actor and distance ahead; configurable range, hit radius, dynamic-only mode, and cadence |

### Environment perception

| Sensor | Native output |
| --- | --- |
| Radar | Points containing azimuth, altitude, depth, and relative radial velocity |
| Ray-cast lidar | 3D point cloud with intensity |
| Semantic lidar | Point cloud plus incidence information, object instance ID, and semantic tag |
| HSS lidar | Non-rotating lidar implementation present in the examined source |
| RGB camera | Color image stream |
| Depth camera | Per-pixel depth image |
| Semantic-segmentation camera | Per-pixel semantic class |
| Instance-segmentation camera | Per-pixel object instance |
| Normals camera | Per-pixel surface normal |
| Optical-flow camera | Per-pixel motion vectors |
| DVS camera | Asynchronous brightness-change events |
| Wide-angle camera variants | RGB, depth, semantic, and instance wide-angle implementations present in the source |

### Cooperative and safety data

| Sensor | Native output |
| --- | --- |
| V2X CAM | Cooperative Awareness Messages with configurable channel/radio/noise model |
| Custom V2X | Application-defined byte messages between sensors on the same channel |
| RSS | Responsibility-Sensitive Safety response through CARLA's RSS integration |

Camera/lidar/radar streams can be high bandwidth and are intentionally not
assumed to be appropriate for the current demonstration. Their presence is
recorded so the architecture does not accidentally imply that CARLA is
limited to scalar vehicle data.

## 3. CARLA world and map ground truth

CARLA can provide additional context without adding a physical sensor:

- OpenDRIVE road, section, lane, and junction IDs;
- longitudinal road coordinate, lane width/type, legal lane-change direction,
  and left/right lane markings;
- nearby landmarks, traffic signs, traffic lights, crosswalks, and road
  topology;
- exact state, transform, velocity, and classification of other simulated
  actors;
- current weather and environment configuration.

This data is useful for deterministic scenarios and oracle/qualification
logic. It must be labelled **simulator ground truth**, not presented as if a
production vehicle measured it directly. A production mapping would normally
come from localization, map, perception, V2X, or another vehicle subsystem.

## 4. Physics and scenario configuration, not telemetry

CARLA exposes configurable vehicle model parameters including:

- mass, drag, center of mass, inertia and downforce;
- torque curve, maximum/idle RPM, transmission ratios and efficiency;
- wheel radius, width, mass, steering limit, brake/handbrake torque;
- suspension geometry and damping;
- wheel friction multiplier, slip/skid thresholds;
- configuration flags for ABS and traction control.

These describe or modify the simulated plant. They are valuable scenario
metadata, but they are not live measurements. In particular, `abs_enabled`
does not mean that ABS is currently engaged.

CARLA also provides a stock `static.trigger.friction` actor. A scenario can
place a bounded low-friction region on the road and observe the resulting
vehicle/wheel dynamics without writing a new physics model.

## 5. Data not natively available as truthful live telemetry

The examined CARLA/Chaos vehicle does not directly provide:

- hydraulic or brake-fluid pressure;
- brake-pad or rotor temperature;
- brake-pad wear or remaining useful life;
- actual ABS or traction-control engagement state;
- live per-wheel load, drive/brake torque, or longitudinal/lateral tire force;
- tire pressure, temperature, tread wear, or puncture-health telemetry;
- battery state of charge, state of health, or temperature;
- fuel level;
- production ECU diagnostic trouble codes;
- a probability of component failure.

Any such value used in the demo must come from an explicit, versioned
simulated-component model and be labelled accordingly. It must not be
presented as native CARLA sensor output.

## 6. Local events derivable from native CARLA data

These are analytics results, not raw CARLA fields:

| Event concept | Native CARLA input |
| --- | --- |
| Severe braking | Speed, longitudinal acceleration, brake command, wheel dynamics |
| Severe acceleration | Speed, longitudinal acceleration, throttle command |
| Harsh cornering | Speed, lateral acceleration, steering/wheel angle, yaw rate/IMU |
| Loss of traction / low-friction event | Vehicle speed, per-wheel angular velocity and slip, acceleration, steering; stock friction trigger for stimulus |
| Vertical shock / rough-road candidate | Vertical acceleration, IMU, speed, location; reproducible road stimulus still needs validation |
| Collision/impact event | Collision sensor, normal impulse, speed and acceleration |
| Near-obstacle/near-collision event | Obstacle detector or radar, relative velocity, ego speed |
| Lane-departure event | Lane-invasion detector, steering and vehicle motion |
| Speed-limit or signal-compliance event | Vehicle speed plus CARLA map/traffic-light ground truth |
| Geolocated event | Any event plus GNSS |
| Rollover event | Failure state, pose, angular velocity, IMU and collision context |

Thresholds, debounce, event windows, confidence, and severity are service or
scenario logic. CARLA supplies the inputs; it does not supply these business
events as finished decisions.

## Historical Function Team 2 candidate

This research originally recommended **Vehicle Stability / Low-Friction Event
Uploader** for detailed design.

Function Team 2 / Service Provider 2 will own an independently delivered SOTA
service that:

1. receives the vehicle-dynamics signals made available through the accepted
   Vehicle Data Platform Capability;
2. processes those signals locally on the Domain Controller;
3. detects a bounded Vehicle Stability / Low-Friction Event;
4. retains the event locally while connectivity is unavailable;
5. sends the event, rather than a continuous raw-telemetry stream, to Function
   Team 2's own backend when connectivity is available;
6. exposes the received event and its status on Function Team 2's Event-Based
   Data Dashboard.

CARLA's per-wheel angular velocity, longitudinal slip, lateral slip angle,
vehicle motion, steering, and stock friction trigger make this candidate
technically plausible without inventing a new CARLA sensor.

This was a candidate commitment, not an accepted detailed design. The exact
input subset, platform-contract dependency, event state machine, thresholds,
severity/confidence model, pre/post window, bounded Cloud payload, offline
queue, dashboard fields, and acceptance tolerances remain open.

ADR 0008 supersedes this candidate with Tire Health. The low-friction,
Road-Impact, Near-Collision, Lane-Departure, and Impact Recorder concepts remain
research alternatives only and are not part of the planned demo.

## Tire Health interpretation of the inventory

The accepted Function Team 2 concept can reuse native vehicle speed,
acceleration, steering, applied controls, engine state, and per-wheel angular
velocity and slip as model inputs. CARLA does **not** expose live production-
equivalent tire pressure, temperature, tread depth, wear, puncture health,
wheel load, tire force, or wheel torque. Therefore:

1. the service reports an estimated condition band and inspection/replacement
   recommendation, not an exact measured tread depth;
2. the scenario provides a clearly labelled accelerated-time or pre-aged tire
   condition so the transition is visible during a short demo;
3. deterministic degradation truth is hidden qualification input, not a VISS,
   KUKSA, service, backend, or dashboard production signal;
4. the local persistent-state model, input subset, thresholds, payload,
   offline limits, advisory and acceptance tolerances require detailed design.

## Historical low-friction verification recipe

This recipe is retained only as evidence for the superseded candidate. Static
source inspection proves API and sensor availability, not signal quality for
the exact demo vehicle and map:

1. enumerate the actual runtime blueprint library of the packaged Mac build;
2. record representative values and units from direct vehicle telemetry, IMU,
   collision, lane-invasion, obstacle, and radar sensors;
3. verify timestamps, frame alignment, cadence, noise and missing-data behavior;
4. run normal and low-friction segments with the same control profile;
5. test whether the low-friction event is repeatable and visually explainable;
6. avoid all provider, KUKSA, AosVM, and AosCloud changes.

## Sources

- [Pinned CARLA actor API](https://github.com/carla-simulator/carla/blob/ac7d882cac496ccbf8b40aa543d6b38513e1173c/LibCarla/source/carla/client/Actor.h)
- [Pinned CARLA vehicle API](https://github.com/carla-simulator/carla/blob/ac7d882cac496ccbf8b40aa543d6b38513e1173c/LibCarla/source/carla/client/Vehicle.h)
- [Pinned CARLA runtime telemetry record](https://github.com/carla-simulator/carla/blob/ac7d882cac496ccbf8b40aa543d6b38513e1173c/LibCarla/source/carla/rpc/VehicleTelemetryData.h)
- [Pinned CARLA wheel telemetry record](https://github.com/carla-simulator/carla/blob/ac7d882cac496ccbf8b40aa543d6b38513e1173c/LibCarla/source/carla/rpc/WheelTelemetryData.h)
- [Pinned live Chaos telemetry implementation](https://github.com/carla-simulator/carla/blob/ac7d882cac496ccbf8b40aa543d6b38513e1173c/Unreal/CarlaUnreal/Plugins/Carla/Source/Carla/Vehicle/CarlaWheeledVehicle.cpp)
- [CARLA sensors reference](https://carla.readthedocs.io/en/latest/ref_sensors/)
- [CARLA sensors and data overview](https://carla.readthedocs.io/en/latest/core_sensors/)
- [CARLA Python API reference](https://carla.readthedocs.io/en/latest/python_api/)
