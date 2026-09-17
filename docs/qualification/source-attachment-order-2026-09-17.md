<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Source attachment order — 17 September 2026

Status: implementation and targeted regressions passed; preserved-Test repeat
passed. A new clean first-Provision cycle is not claimed by this checkpoint.

## Approved behavior and implementation

Local CARLA/Gateway/Driving Control/telemetry start independently of provisioning.
Gateway starts strict and DETACHED, with local dashboard trust only. Provision
confirms Online and the real Unit/Main Node before issuing Unit-specific leaves
under that same CA and assigning the existing Gateway. The guest stays blocked
until a fresh stationary Manual frame is confirmed. No process/scene restart,
actor replacement, reset generation advance or automatic FOTA authorization.
First VDP installation still requires the operator's subsequent Safe Stop.

Presenter guidance and Quick preparation follow the same shared Demo Control
order. Initial connection before provisioning is rejected. Normal explicit
Test/Production handover retains its separate reset contract; Production was
not touched. Pre-Provision retirement now includes the smaller local-only trust
inventory, without inventing missing Unit credential files.

The earlier uncommitted Gateway hot-reload draft was removed. Its fixed legacy
control metadata remains recognized by cleanup because the preserved running
session was started with that draft. No new reload command is exposed.

## Verification

- 149 targeted Demo Control tests passed: trust, enrollment, selection,
  simulation, preparation, Unit ordering and Test retirement.
- 19 controller protocol tests passed, including first attachment without reset
  and rejection of motion, stale frames, insufficient brake or absent native
  operator session. Release still needs a real completed Manual frame.
- Four bridge recovery tests and four runner trust tests passed.
- 12 Presenter status/flow regressions passed; TypeScript/Vite build passed.
- Swift Driving Control type-check passed.
- Live `democtl vehicle initialize test`: COMPLETED, noOp=true, 2.88 seconds;
  same run and assignment generation, actor 25, reset generation 1. No simulator,
  VM or Cloud identity replacement. Repeat reports driving mode unchanged.
- Native observation: LIVE, stopped, external network ON; Brake recommendation
  visible and Tire Monitoring. Presenter restarted independently and displayed
  staging Test Online and Brake 58.0.0 backend results.

The preceding offline proof used Brake 58.0.0/V3 and Tire 34.0.0/V1 with the
native gRPC resolver: KUKSA reconnected after token renewal while external
networking was disabled. Telemetry and controls remained operational. This
checkpoint did not repeat that entire test or publish additional releases.

## Preserved state and exclusions

Preserved Factory .35 Test, VDP 78.0.0/V3, Brake 58.0.0/V3, Tire 34.0.0/V1,
Cloud identity and current simulator. No Factory rebuild, deprovisioning,
cleanup of the live run, Production mutation, commit or push in this increment.
Existing unrelated working-tree changes were retained. No credentials enter
this record. No temporary live patch was added.

The already-running native controller retains its loaded protocol until the
next normal simulator start; it was deliberately not restarted to claim a clean
first-Provision pass. The next fresh cycle must confirm detached local startup,
first Provision/attachment, unchanged actor/window/process identities, and
factory-baseline Safe Stop delivery through the updated startup path.
