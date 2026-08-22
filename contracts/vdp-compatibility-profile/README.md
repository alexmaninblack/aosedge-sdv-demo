<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# VDP Compatibility Profile

This directory is the canonical cross-component contract for
[`D4-007`](../../docs/requirements/d4-decision-register.md#d4-007). It freezes
the additive Vehicle Data Platform Component v1-v3 graph, service compatibility
ranges, installed-capability identity and fail-closed readiness behavior.

- [accepted profile](vdp-compatibility-profile.v1.json)
- [JSON schema](vdp-compatibility-profile.schema.json)

The profile selects only paths already accepted by the
[VISS Trust and Telemetry Profile](../viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json).
It does not define the exact Brake or Tire advisory targets; those remain owned
by `D4-008`.

The current AosCloud release does not provide native pre-transfer admission for
a SOTA service that requires a newer FOTA VDP Component. Therefore this
contract requires fail-closed service readiness and factual dashboard guidance,
but prohibits a project-built Cloud-admission substitute. A service can be
installed and process-healthy while its functional readiness is `NOT_READY`.

