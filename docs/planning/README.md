<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Planning Documentation

Planning documents decompose accepted architecture into controlled delivery
gates. A plan does not itself authorize a build, signature, Cloud mutation,
assignment, VM restart, or provisioned-Unit change.

- [Current design and delivery roadmap](roadmap.md)
- [Accepted Demo Implementation Plan 1.2](active/demo-implementation-plan.md)
  — bounded implementation increments, repository ownership, dependencies,
  verification and per-increment authorization gates.
- Completed P0 work packets:
  [UI readiness](active/work-packets/p0-ui-readiness.md),
  [Vehicle/Gateway readiness](active/work-packets/p0-vehicle-gateway-readiness.md)
  and [Platform readiness](active/work-packets/p0-platform-readiness.md).
  Their P0 read-only assessment and local-test execution completed on
  2026-08-28. UI and the first bounded Vehicle/Gateway slice are ready for
  separate code-packet review; Platform is baseline-ready while its code
  packets remain blocked. Product implementation and external operations
  remain unauthorized until their exact packet is accepted.
- Authorized P1 work packets:
  [Presenter UI implementation](active/work-packets/p1-ui-presenter-shell.md)
  and
  [Vehicle/Gateway wheel-unit correction](active/work-packets/p1-vehicle-gateway-wheel-units.md).
  Both are stored in Git as reviewable execution-control records and were
  explicitly authorized on 2026-08-28. Their authorization is limited to the
  exact repository, paths, dependencies, commands, tests and exclusions in
  each packet; it does not authorize push, merge or live external operations.
- [Repository inventory and migration plan](repository-inventory-and-migration-plan.md)
  — completed migration and local-cleanup execution record.

## Active Architecture Changes

Active plans are temporary, tracked execution controls for accepted changes.
They do not become a second source of architectural truth and are removed from
the current tree when their change closes; ADRs, canonical requirements,
contracts and Git history retain the lasting decision and evidence.

There is currently no active architecture-change plan. ADR 0013 and its
canonical requirements/contracts retain the accepted KUKSA compatibility
boundary. The active Demo Implementation Plan is a delivery control derived
from that baseline, not a competing architecture source; implementation
remains separately gated per increment.
