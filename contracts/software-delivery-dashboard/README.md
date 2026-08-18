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
to a successful result. `PARTIAL`, `PLANNED`, and `DOCUMENTARY_ONLY` are also
visually distinct from accepted proof.
