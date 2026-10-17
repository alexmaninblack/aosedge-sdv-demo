<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Exclusive Live-Source Assignment Contract

Implementation and qualification: [protocol status](../implementation-status.md).

The installed Test uses strict selected-Unit mTLS with separate observer and
safety roles. Its exact current proof is linked from
[implementation status](../implementation-status.md); legacy server-only
fixtures are not an installed trust mode or strict-mTLS evidence.
The expanded dual-role contract below adds sequential Validation/Production
handover; those additional duties are not ordinary single-Test prerequisites.

- Decision: [`D4-005`](../../docs/requirements/d4-decision-register.md#d4-005)
- Contract version: 1.0.0
- Lifecycle state: accepted contract; implementation and qualification remain open

The expanded profile separates the audience story from its source-assignment
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
view remains honest that the current profile reuses one visual CARLA
source sequentially and implements no telemetry replay.

Exclusivity applies to the selected **Unit** peer. The independently
authenticated, read-only Engineering Telematics Dashboard may remain connected
under the separate D4-006 role and is never counted as a Unit binding.
