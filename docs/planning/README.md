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
- [Consolidated Implementation Execution Trains](active/infrastructure-first-critical-path-proposal.md)
  — the completed Platform Train authorization record and bounded Demo
  Interface Train authorization. Its macOS handoff correction is now accepted;
  the train may begin only after the synchronized contract checkpoint and
  exact clean entry gates pass, and authorizes no live source or external
  mutation.
- Completed P0 work packets:
  [UI readiness](active/work-packets/p0-ui-readiness.md),
  [Vehicle/Gateway readiness](active/work-packets/p0-vehicle-gateway-readiness.md)
  and [Platform readiness](active/work-packets/p0-platform-readiness.md).
  Their P0 read-only assessment and local-test execution completed on
  2026-08-28. They are retained as the evidence that admitted the later P1
  work; current authorization state is recorded by the consolidated execution
  trains and their linked detailed packets.
- Authorized P1 work packets:
  [Presenter UI implementation](active/work-packets/p1-ui-presenter-shell.md)
  and
  [Vehicle/Gateway wheel-unit correction](active/work-packets/p1-vehicle-gateway-wheel-units.md).
  Both are stored in Git as reviewable execution-control records and were
  explicitly authorized on 2026-08-28. Their authorization is limited to the
  exact repository, paths, dependencies, commands, tests and exclusions in
  each packet; it does not authorize push, merge or live external operations.
- The completed Platform Train provenance includes the
  [Factory/Runtime source packet](active/work-packets/p1-platform-factory-runtime.md)
  and its [compile qualification](active/work-packets/p1-platform-runtime-compile-qualification.md),
  KAC compile/Row2 checkpoints and the
  [KAC Factory stage](active/work-packets/p1-platform-kac-factory-integration.md).
  Their source/fan-in/qualification result is accepted Factory baseline `.21`;
  these historical execution records grant no residual product, Builder, VM
  or Cloud authority. The Demo Interface Train is separately authorized but
  remains not started until the synchronized contract checkpoint lands.
- The next Platform execution boundary is the authorized
  [VDP deployable artifact preparation packet](active/work-packets/p1-platform-vdp-artifacts.md),
  which is offline-only and not started. It owns no signing, Cloud, VM or FOTA
  operation.
- The [Gateway controller handoff packet](active/work-packets/p1-vehicle-gateway-controller-cpp.md)
  records the preserved `d4a20c` candidate and its macOS/full-CARLA compile
  blockers; its bounded
  [macOS correction packet](active/work-packets/p1-vehicle-gateway-controller-macos-correction.md)
  is accepted/authorized but not started. The [Brake v2 packet](active/work-packets/p1-brake-health-core-v2.md)
  is source-only authorized/not started; the
  [Brake Cloud Data packet](active/work-packets/p1-brake-cloud-data.md) preserves
  its existing candidate in quarantine with only its exact bounded correction
  authorized/not started.
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
