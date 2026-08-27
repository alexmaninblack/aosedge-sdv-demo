<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Planning Documentation

Planning documents decompose accepted architecture into controlled delivery
gates. A plan does not itself authorize a build, signature, Cloud mutation,
assignment, VM restart, or provisioned-Unit change.

- [Current design and delivery roadmap](roadmap.md)
- [Accepted Demo Implementation Plan 1.1](active/demo-implementation-plan.md)
  — bounded implementation increments, repository ownership, dependencies,
  verification and per-increment authorization gates.
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
