<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Planning Documentation

Planning documents decompose accepted architecture into controlled delivery
gates. A plan does not itself authorize a build, signature, Cloud mutation,
assignment, VM restart, or provisioned-Unit change.

- [Current design and delivery roadmap](roadmap.md)
- [Repository inventory and migration plan](repository-inventory-and-migration-plan.md)
  — completed migration and local-cleanup execution record.

## Active Architecture Changes

Active plans are temporary, tracked execution controls for accepted changes.
They do not become a second source of architectural truth and are removed from
the current tree when their change closes; ADRs, canonical requirements,
contracts and Git history retain the lasting decision and evidence.

- [KUKSA JWT current-release architecture and delivery change](active/kuksa-jwt-current-release-change-plan.md)
  — review candidate for the class-C authorization-boundary cascade; no
  implementation, build or Cloud/Unit mutation is authorized.
