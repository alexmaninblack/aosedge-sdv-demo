<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Simulator Control and Context Contract

- Decision: [`D4-004`](../../docs/requirements/d4-decision-register.md#d4-004)
- Contract version: 1.0.0
- Lifecycle state: accepted contract; implementation and qualification remain open

This cross-repository contract freezes the drive-mode/world-context transition
matrix and the simulator-specific engineering projection shared by Vehicle
Simulation, Vehicle Gateway and the Engineering Telematics Dashboard.

- [JSON Schema](simulator-control-context.schema.json)
- [Accepted contract 1.0.0](simulator-control-context.v1.json)

The contract keeps control mode separate from simulated-world context. It also
makes reset teleportation visible through a monotonic generation and frame
marker so a consumer cannot interpret a reset as physical travel.

The paths are project-owned `Vehicle.CarlaSimulation.*` engineering signals.
They are not implied to belong to an accepted production VDP subset, and the
Engineering Telematics Dashboard remains a read-only subscriber.

Reverse remains a declared physical vehicle capability, but is not authorized
for the first-demo Control UI. Deterministic recovery uses Scenario restart or
the accepted cleanup/reset before free-drive Autopilot.
