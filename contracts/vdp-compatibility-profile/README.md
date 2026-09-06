<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# VDP Compatibility Profile

This directory is the canonical cross-component contract for
[`D4-007`](../../docs/requirements/d4-decision-register.md#d4-007). It freezes
the additive Vehicle Data Platform Component v1-v3 graph, service compatibility
ranges, installed-capability identity and fail-closed readiness behavior.

- [accepted profile 1.0.1](vdp-compatibility-profile.v1.json) — metadata-only
  repin to VISS Trust and Telemetry Profile 1.1.0; the VDP v1-v3 capability
  graph and service compatibility semantics are unchanged
- [JSON schema](vdp-compatibility-profile.schema.json)

The profile selects only paths already accepted by the
[VISS Trust and Telemetry Profile](../viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json).
It does not define the exact Brake or Tire advisory targets; those remain owned
by `D4-008`.

Operator-approved repeat-cycle interpretation (2026-09-06): `VDP_V1`,
`VDP_V2`, `VDP_V3` identify functional capability profiles, not every future
Cloud release number. Demo Control can package the same profile as a newer
release (for example 4.0.0 contains VDP_V1). Consumers must use signed
capabilities/profile identity rather than infer functionality from release
major. Contract JSON, digests, signal graph and service compatibility semantics
are unchanged. See [Demo Control](../../docs/architecture/demo-control.md) for
the separate monotonic publication sequence.

The current AosCloud release does not provide native pre-transfer admission for
a SOTA service that requires a newer FOTA VDP Component. Therefore this
contract requires fail-closed service readiness and factual dashboard guidance,
but prohibits a project-built Cloud-admission substitute. A service can be
installed and process-healthy while its functional readiness is `NOT_READY`.
