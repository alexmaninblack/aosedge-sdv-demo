<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Planning Documentation

Planning documents decompose accepted architecture into controlled delivery
gates. A plan does not itself authorize a build, signature, Cloud mutation,
assignment, VM restart, or provisioned-Unit change.

## Current implementation and remaining work

- [Installable distribution and reproducibility](active/installable-distribution-and-reproducibility.md):
  accepted Stage 0–7 plan for a portable Apple Silicon runtime, operator/developer
  documentation and clean-system acceptance; Kit028 installed scripted sequence passed; complete native first-use,
  moving SOTA, secure token entry, interruption/repair and release gates remain open.
- [Human-friendly repository and release reproduction](active/work-packets/human-friendly-reproduction.md):
  detailed R1–R4 plan for one release definition, automated preparation/builds,
  three human documentation routes and fresh-environment proof. Planning only;
  subordinate to the distribution plan, not an implemented build interface.
- [Cross-repository change journal](repository-change-journal.md): maintainer
  record of coordinated changes, evidence, publication state and next actions;
  not a second release lock or an operator prerequisite.
- [External SSD deployment plan](active/external-ssd-deployment.md):
  prepared 1 TB Work/Clean split, verified Kit 004 transfer, isolated/native
  proof and invalid-input rejection;
  installer and clean macOS qualification remain future gates.
- [Distribution Stage 0 inventory](../research/distribution-stage0-inventory-2026-09-25.md):
  completed input/ownership audit, preservation, portability risks and bounded
  next packets; inventory alone is not runtime qualification.
- [Standalone CARLA Stage 1 proof](../qualification/standalone-carla-stage1-2026-09-25.md):
  completed scoped simulator/runtime and window-layout feasibility checks;
  portable host helpers and clean-install acceptance remain later gates.
- [demo-v1.1 return point](../qualification/demo-v1.1-return-point.md): published
  source composition and retained Factory39; Production31 is preserved.
- [Implemented architecture](../architecture/current-implementation.md) and
  [documentation audit](../qualification/documentation-reconciliation-2026-10-07.md):
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

Current candidate and acceptance are in the [baseline](../qualification/current-baseline.md).
Kit028's installed scripted serial run and subsequent retirement are complete.
Native UI/moving-SOTA/token-entry/interruption gates remain open. Cold
externalOFF ignition/nonempty-outbox power loss, calibration/negative/resource
matrices and executable Tire cleanup contract synchronization remain separate.
Brief readiness and VDP timeout work are deferred. Charts do not implement
the missing CPU worker; host sleep/wake and SSD are excluded from the M1 campaign.

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
current Kit028/.41 baseline.

## Active Architecture Changes

Active plans are temporary, tracked execution controls for accepted changes.
They do not become a second source of architectural truth and are removed from
the current tree when their change closes; ADRs, canonical requirements,
contracts and Git history retain the lasting decision and evidence.

The [installable distribution plan](active/installable-distribution-and-reproducibility.md)
now implements [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md)
in gated slices; offline package installation precedes installed-state/runtime
integration. ADR 0013 and its
canonical requirements/contracts retain the accepted KUKSA compatibility
boundary. The active Demo Implementation Plan is a delivery control derived
from that baseline, not a competing architecture source; implementation
remains separately gated per increment.
