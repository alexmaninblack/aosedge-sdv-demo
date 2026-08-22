<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Software Delivery Dashboard Contracts

[`coverage-matrix.v1.json`](coverage-matrix.v1.json) is the sanitized,
machine-readable catalogue of automotive concerns, demo-stage mappings,
evidence fields, acceptance criteria, current coverage, and claim boundaries.
[`coverage-matrix.schema.json`](coverage-matrix.schema.json) defines its stable
version 1 shape.

The dashboard may combine this catalogue with live normalized AosCloud state
and accepted qualification evidence. It must not embed, fetch, name, or expose
the confidential OEM source from which the neutral concern catalogue was
derived.

Coverage state is evidence state, not desired state. Unknown or missing live
data remains `UNKNOWN` in the presentation layer and must never be converted
to a successful result. `PARTIAL`, `PLANNED`, `DOCUMENTARY_ONLY`, and `STALE`
are visually distinct from `ACCEPTED` proof.

`ACCEPTED` is valid only when `acceptedEvidence` binds the evidence ID and
verification time to the exact subject version/digest, AosEdge platform
release and configuration digest. If any bound value no longer matches the
current demo baseline, the dashboard renders `STALE` with an explicit reason;
it never silently carries the former green state forward.

For `AO-06`, the dashboard is an evidence surface only. AosCore/Service Manager
is the sole in-vehicle quota-enforcement and monitoring authority. The first
proof uses one prepared Tire Health CPU load and treats Brake Health as the
unaffected control tenant; it does not add a demo resource manager or treat the
Mac-local functional backends as AosCore tenants.
