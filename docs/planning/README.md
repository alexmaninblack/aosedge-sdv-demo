<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Planning Documentation

Planning documents decompose accepted architecture into controlled delivery
gates. A plan does not itself authorize a build, signature, Cloud mutation,
assignment, VM restart, or provisioned-Unit change.

## Current implementation and remaining work

- [demo-v1.1 return point](../qualification/demo-v1.1-return-point.md): published
  source composition and retained Factory39; Production31 is preserved.
- [Implemented architecture](../architecture/current-implementation.md) and
  [documentation audit](../qualification/documentation-implementation-audit-2026-09-24.md):
  current requirements/code/protocol mapping and explicit gaps.
- [Studio delivery plan](active/demo-studio-delivery-plan.md): dated execution
  chronology, not a fresh authorization to repeat old work.
- [AosCore migration](active/aoscore-mainline-migration-2026-09-23.md):
  mainline-derived Factory39 with retained native corrections.
- [Host sleep/wake recovery](active/native-sleep-wake-recovery-2026-09-21.md):
  accepted planning, not implemented or qualified by controller ignition.
- [Presenter amendments](active/work-packets/presenter-ui-amendments-implementation.md):
  implemented card Reset, consolidated Disk and CPU/RAM history.
- [Versioned service observability](active/work-packets/versioned-service-observability.md):
  product/function/Cloud authority and qualification exclusions.
- [Roadmap](roadmap.md): design/delivery order and original milestones.

Current gaps include fresh serial .39 all-version/Finish acceptance,
cold externalOFF ignition/nonempty-outbox power loss, remaining calibration and
negative/resource matrices, readiness transitions, and executable Tire cleanup
contract synchronization. Cloud charts do not implement the missing CPU worker.

## Historical execution packets

The [implementation plan](active/demo-implementation-plan.md),
[execution trains](active/infrastructure-first-critical-path-proposal.md),
[native desktop plan](active/native-demo-desktop.md), P0/P1 packets and
[repository migration](repository-inventory-and-migration-plan.md) retain their
dated scope and ownership. “Not started” in an old packet describes its
checkpoint; it is not today's status or residual permission to mutate a Unit.

VDP artifact preparation, native Gateway handoff, Brake V2/V3, real backend
window detail, KAC and Factory integration have subsequently been implemented.
Their original bounded packets remain traceability:
[VDP](active/work-packets/p1-platform-vdp-artifacts.md),
[Gateway](active/work-packets/p1-vehicle-gateway-controller-macos-correction.md),
[Brake V2](active/work-packets/p1-brake-health-core-v2.md),
[Brake V3](active/work-packets/p1-brake-health-core-v3.md),
[window detail](active/work-packets/p1-brake-cloud-window-detail.md),
[KAC](active/work-packets/p1-platform-kac-factory-integration.md),
[Factory/runtime source](active/work-packets/p1-platform-factory-runtime.md) and
[runtime compile qualification](active/work-packets/p1-platform-runtime-compile-qualification.md).
The [.33 audit](../qualification/factory-33-consolidation-audit-2026-09-13.md)
is historical; its old permissions/source-publication blockers are not the
current .39 baseline.

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
