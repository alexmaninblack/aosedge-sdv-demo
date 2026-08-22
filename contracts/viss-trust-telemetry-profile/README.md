<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# VISS Trust and Telemetry Profile

- Decision: [`D4-006`](../../docs/requirements/d4-decision-register.md#d4-006)
- Contract version: 1.0.0
- Accepted contract SHA-256: `24484919d916ade153111fd6075d06cecdf77d0bed7cfd016c0a4163e1b8fd53`
- Lifecycle state: accepted contract; implementation and live qualification remain open

This contract freezes the private in-vehicle VISS trust boundary, authenticated
peer roles, read-only operation profile, timing and failure semantics, and the
complete Gateway engineering-path superset derived from D4-002 and D4-004.

- [JSON Schema](viss-trust-telemetry-profile.schema.json)
- [Accepted contract 1.0.0](viss-trust-telemetry-profile.v1.json)

The selected Platform Unit and the independent Engineering Telematics
Dashboard are different authenticated peer roles. D4-005 exclusivity applies
to Unit peers only; the read-only Engineering Dashboard may remain connected.

Every D4-002 hardware capability is either mapped to one or more exact VISS
paths/applied-state paths or retained as an explicit excluded/unavailable
capability. D4-007 selects staged VDP v1-v3 subsets from this superset. This
baseline still denies every other `Set`; the accepted D4-008 profile adds only
the two exact typed QM advisory targets for the selected Platform Unit. The
Engineering Dashboard remains permanently read-only.

Standard path/type/unit values are pinned to the official
[COVESA VSS 6.0 release](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v6.0),
whose `vss.json` SHA-256 is
`b77785180dbe7fc674e4965ab9c1c58dcc97433867cf4abf4e3f78c013550e78`.
In particular, acceleration uses `m/s^2` and standard wheel angular speed uses
`degrees/s`; the current CARLA runtime's native `rad/s` value therefore needs
an explicit target conversion before that path is qualified.
