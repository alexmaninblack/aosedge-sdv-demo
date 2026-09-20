<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Typed QM Advisory Profile

This directory is the canonical cross-component contract for
[`D4-008`](../../docs/requirements/d4-decision-register.md#d4-008). It freezes
the two non-safety QM maintenance-advisory paths, schema-bound Request/Status
envelopes, authority, freshness, replay/rate limits and clear/expiry behavior.

- [accepted profile 1.2.0](qm-advisory-profile.v1.json) — operator-approved
  100 ms future-clock tolerance for the two QM advisory endpoints on
  20 September 2026. Version 1.1.0 separated functional profiles from package
  release numbers on 16 September 2026. Earlier 1.0.2 repinned VDP Compatibility Profile 1.0.1;
  1.0.1 replaced retired `D4-009` authorization with `D4-027`.
- [Request schema](qm-advisory-request.schema.json)
- [Gateway Status schema](qm-advisory-status.schema.json)

The first implementation transports one canonical UTF-8 JSON object in one
VSS `string` leaf. This preserves atomic message semantics through the current
primitive `kuksa.val.v1` datapoint API. It is not arbitrary display text: the
VDP and Gateway independently validate the exact schema, endpoint-specific
enums, size, freshness, replay and QM allowlist.

Brake's compatible functional profile is `v3`; Tire's is `v1`. Neither is an
allowlist of Cloud release numbers. `serviceVersion` carries the installed
package version unchanged (for example Tire `29.0.0`), including on retained
retries and in correlated backend provenance. It must not be rewritten to
`1.0.0` or `3.0.0` to satisfy compatibility checks.

Authorization still comes from native IAM and exact KUKSA actuator permissions.
The trusted bridge binds its two fixed endpoints to their qualified functional
profiles; a payload cannot select a service identity, profile, authority or
alternate path. The request's release number is checked for the existing
numeric three-part format, not treated as authentication or independent proof
of the installed software version. Cross-service writes and motion commands
remain denied; replay/lease/rate and Gateway acknowledgement rules are unchanged.

Both VDP and Gateway accept an `issuedAt` up to 100 ms ahead of their own UTC
receipt time, inclusive; greater future offsets still fail `STALE_REQUEST`.
The 2000 ms maximum past age and 30000 ms maximum declared lease are unchanged.
Gateway caps effective `activeUntil` at the earlier of the original `expiresAt`
and its acceptance time plus 30000 ms, and uses that same duration for its
monotonic deadline. Either wall-clock expiry or monotonic expiry clears the
warning. Original request bytes/timestamps remain unchanged for provenance
and replay equality. Identical duplicates never extend either deadline.
This is not a telemetry-age, readiness-heartbeat or motion-control tolerance.

This contract update does not modify released bundles or qualify the dormant
VDP advisory transport. A future payload must bind the updated policy/profile
digest during its normal preparation and signing, without rewriting frozen
VDP3.0.0 artifacts.

Future end-to-end support for VSS struct actuators may replace the wire
encoding without changing the semantic fields or authority model. Driver HMI,
safety warnings, arbitrary vehicle writes and motion commands remain outside
this contract.
