<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# VISS Trust and Telemetry Profile

- Decision: [`D4-006`](../../docs/requirements/d4-decision-register.md#d4-006)
- Contract version: 1.1.0
- Accepted contract SHA-256: `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c`
- Lifecycle state: accepted contract; implementation and live qualification remain open

This contract freezes the private in-vehicle VISS trust boundary, authenticated
peer roles, read-only operation profile, timing and failure semantics, and the
complete Gateway engineering-path superset derived from D4-002 and D4-004.

- [JSON Schema](viss-trust-telemetry-profile.schema.json)
- [Accepted contract 1.1.0](viss-trust-telemetry-profile.v1.json)

The selected Platform Unit, its purpose-bound Platform Update Runtime and the
independent Engineering Telematics Dashboard are different authenticated peer
roles. The two selected-Unit roles use distinct per-Unit credentials and permit
one connection each; D4-005 binds both to the same current Unit and assignment
generation. The read-only Engineering Dashboard may remain connected.

`PLATFORM_UPDATE_RUNTIME` is permanently read-only and can access only the ten
paths required by the Platform FOTA Safe Stop contract, including `FrameId`.
It receives no general VDP telemetry or QM advisory authority.

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
