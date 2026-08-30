<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Simulator Control and Context Contract

- Decision: [`D4-004`](../../docs/requirements/d4-decision-register.md#d4-004)
- Contract version: 1.1.1
- Lifecycle state: accepted contract; implementation and qualification remain open

This cross-repository contract freezes the drive-mode/world-context transition
matrix and the simulator-specific engineering projection shared by Vehicle
Simulation, Vehicle Gateway and the Engineering Telematics Dashboard.

- [JSON Schema](simulator-control-context.schema.json)
- [Accepted contract 1.1.1](simulator-control-context.v1.json)
- [Valid controller-to-Gateway record](fixtures/controller-gateway-handoff-record.valid.json)

The contract keeps control mode separate from simulated-world context. It also
makes reset teleportation visible through a monotonic generation and frame
marker so a consumer cannot interpret a reset as physical travel.

Version 1.1.1 freezes the cross-platform local Python-controller-to-C++-
Gateway handoff. One non-blocking length-framed UTF-8 JSON record is carried
for each real completed CARLA frame over one connected `AF_UNIX`
`SOCK_STREAM` per run. The owner-only runtime directory/socket and effective-
UID peer verification use `getpeereid`/`LOCAL_PEERCRED` on Darwin and
`SO_PEERCRED` on Linux. A zero, oversize, truncated or invalid frame,
backpressure timeout, EOF or disconnect makes the channel unavailable and
omits the complete six-path group; there is no reconnect, replay or last-known
reuse within a run. The Gateway joins a record only to the physical snapshot
with the exact same frame ID and simulation time. The four-per-side, 250-ms
host-monotonic join buffer is transport tolerance only.

A blocking reset does not fabricate CARLA frames. Its last real pre-reset frame
may carry `PREPARING`, `Reset.InProgress=true` and the current generations. The
first real post-reset frame carries the successfully incremented reset
generation, the new control generation where applicable,
`Reset.InProgress=false` and one-frame `Reset.Discontinuity=true`; the next
real frame clears discontinuity. A failed reset with no completed frame creates
no success evidence. Presenter progress remains separate UI operation state.

The paths are project-owned `Vehicle.CarlaSimulation.*` engineering signals.
They are not implied to belong to an accepted production VDP subset, and the
Engineering Telematics Dashboard remains a read-only subscriber.

Reverse remains a declared physical vehicle capability, but is not authorized
for the first-demo Control UI. Deterministic recovery uses Scenario restart or
the accepted cleanup/reset before free-drive Autopilot.
