<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0008: Use Tire Health for Function Team 2

- Status: Accepted
- Date: 2026-08-18
- Decision owner: System Architecture
- Supersedes: the Vehicle Stability / Low-Friction Event candidate recorded by
  R10 and the HLA 1.1 review draft
- Cloud or Unit mutation authorized: no

## Context

The architecture requires a second OEM functional vertical that is a peer of
Brake Health, owns an independent AosCloud Service Provider identity, and can
evolve through its own SOTA lifecycle. The earlier Vehicle Stability /
Low-Friction Event candidate demonstrated local event reduction, but it did
not exercise a second long-lived vehicle-health model or the shared outbound
advisory capability as clearly as the proposed Tire Health function.

CARLA exposes useful native dynamics evidence, including vehicle speed,
acceleration, applied controls, engine state, and per-wheel slip and angular
velocity. It does not expose a production-equivalent live tire-pressure,
temperature, tread-depth, wear, puncture, load, force, or torque measurement.
The demonstration therefore needs an explicit simulation-only tire degradation
model and must not present its hidden truth as a production vehicle signal.

## Decision

Function Team 2 / Service Provider 2 will own an independently delivered
**Tire Health In-Vehicle Service** and a separate Tire Health backend and
dashboard.

The in-vehicle service will:

1. consume an accepted versioned subset of vehicle-dynamics signals through
   KUKSA;
2. maintain a bounded, persistent, versioned estimate of tire condition;
3. produce a condition band and inspection/replacement recommendation rather
   than claim an exact measured tread depth;
4. send only bounded summaries and threshold events to its backend instead of
   continuously streaming raw vehicle telemetry;
5. continue local analysis and recommendation generation while Cloud
   connectivity is unavailable; and
6. request an allowlisted Tire Health advisory through KUKSA, the Vehicle Data
   Platform Capability, VISS, and the Vehicle Gateway. The current demo shows
   the result only on the Engineering Telematics Dashboard and does not claim a
   production driver HMI.

The CARLA scenario will use a clearly labelled accelerated-time or pre-aged
tire condition so the audience can observe a meaningful transition during a
short demonstration. Hidden deterministic degradation truth may be used only
for qualification and must remain unavailable to the service and functional
backend as a production signal.

The source repository for the in-vehicle service will be
`tire-health-service`. Its Cloud backend/dashboard repository boundary remains
a separate decision.

## Consequences

- Function Team 2 remains independent of Function Team 1 and the Brake Health
  product.
- The shared Vehicle Data Platform Capability must support typed, allowlisted
  advisory requests rather than a Brake Health-only return path.
- The Vehicle Gateway advisory handler and Engineering Telematics Dashboard
  must distinguish Brake Health and Tire Health status without becoming a
  production HMI.
- New Tire Health component, requirement, interface, flow, and gap identifiers
  are introduced. Existing `EVENT`, `EVT`, `FT2`, and Low-Friction identifiers
  are retired with explicit replacement mappings; their meanings are not
  silently reused.
- The R10 CARLA telemetry inventory remains valid research evidence, while its
  former Function Team 2 candidate recommendation becomes historical.
- Detailed design must freeze the degradation model, initial/pre-aged state,
  persistence, input subset, thresholds, upload schema, offline bounds, and
  qualification oracle before implementation.

## Rejected Alternative

Retaining Vehicle Stability / Low-Friction Event as the active Function Team 2
product would remain technically feasible, but it would provide less visible
separation from the braking demonstration and would not exercise the same
condition-estimation and maintenance-advisory lifecycle.
