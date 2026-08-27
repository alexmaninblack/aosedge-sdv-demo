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

For the Tire CPU proof, live audience facts come from fresh exact-instance
AosCloud monitoring in DMIPS and current instance state; quota alerts are
supplementary. The Cloud API does not expose raw cgroup cap/throttle counters,
so a separately labelled sanitized qualification record proves `cpu.max`,
`cpu.stat` throttle growth and no instance replacement. That record is valid
only for its exact Factory Image, AosCore, Tire artifact, signed configuration
and Node DMIPS baseline. Missing, stale or mismatched evidence remains
`UNKNOWN`; Tire Function control status is never enforcement proof.

Verdict evaluation is sample-driven. Three consecutive fresh Cloud samples are
required for baseline, saturation and recovery; the exact freshness and DMIPS
bands come from the current baseline-bound qualification profile rather than a
hard-coded percentage. The Dashboard distinguishes `PASS`, `FAIL`,
`INCONCLUSIVE` and `NOT_READY`. It introduces no new latency KPI and never lets
a quota alert determine the verdict by itself.
