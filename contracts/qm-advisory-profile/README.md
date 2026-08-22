<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Typed QM Advisory Profile

This directory is the canonical cross-component contract for
[`D4-008`](../../docs/requirements/d4-decision-register.md#d4-008). It freezes
the two non-safety QM maintenance-advisory paths, schema-bound Request/Status
envelopes, authority, freshness, replay/rate limits and clear/expiry behavior.

- [accepted profile](qm-advisory-profile.v1.json)
- [Request schema](qm-advisory-request.schema.json)
- [Gateway Status schema](qm-advisory-status.schema.json)

The first implementation transports one canonical UTF-8 JSON object in one
VSS `string` leaf. This preserves atomic message semantics through the current
primitive `kuksa.val.v1` datapoint API. It is not arbitrary display text: the
VDP and Gateway independently validate the exact schema, endpoint-specific
enums, size, freshness, replay and QM allowlist.

Future end-to-end support for VSS struct actuators may replace the wire
encoding without changing the semantic fields or authority model. Driver HMI,
safety warnings, arbitrary vehicle writes and motion commands remain outside
this contract.

