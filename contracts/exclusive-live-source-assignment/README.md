<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Exclusive Live-Source Assignment Contract

- Decision: [`D4-005`](../../docs/requirements/d4-decision-register.md#d4-005)
- Contract version: 1.0.0
- Lifecycle state: accepted contract; implementation and qualification remain open

This contract separates the audience story from the first-demo implementation
constraint:

- the audience sees a **Test Vehicle** and a **Production Vehicle**;
- AosCloud manages the corresponding **Validation Unit** and
  **Production Unit** Domain Controllers;
- the host-side demo implementation assigns one live CARLA/Gateway source
  sequentially and exclusively to those Units.

- [JSON Schema](exclusive-live-source-assignment.schema.json)
- [Accepted contract 1.0.0](exclusive-live-source-assignment.v1.json)

`Test Vehicle` is a display label only. The contract's stable internal
`VALIDATION_VEHICLE` role maps to it at the Representation Layer; technical
Unit, API and evidence terminology remains `Validation Unit` / `VU` in the
`Verification Unit Set`.

The primary UI never presents attach/detach, VM plumbing or source-gate
operations as vehicle behavior. It exposes one `CURRENT VEHICLE`, retains
completed validation evidence for the other logical vehicle, and places exact
Unit/source information behind technical details.

The logical vehicle role is orchestration/presentation state. It shall not be
published into the in-vehicle VSS/KUKSA production data path. The technical
view remains honest that the first implementation reuses one visual CARLA
source sequentially and implements no telemetry replay.

Exclusivity applies to the selected **Unit** peer. The independently
authenticated, read-only Engineering Telematics Dashboard may remain connected
under the separate D4-006 role and is never counted as a Unit binding.
