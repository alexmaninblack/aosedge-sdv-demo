<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0017: Continuous Demo Lifecycle and Upstream Core

- Status: Accepted by the operator
- Date: 2026-09-19
- Scope: current Test-only Demo Studio and its P7/P8 qualification

## Context

The retained Test lost service model/outbox/function-observation storage during
Park/Resume. Native CM retired old version records that share a version-less
storage identity with the current version. The same removal is reachable from
expired-version cleanup. The pinned upstream library reproduces both cases;
source inspection of newer main still finds the unconditional removal.
See the [upstream handoff](../../qualification/aoscore-shared-storage-handoff-2026-09-19.md)
and [retained-Test evidence](../../qualification/preserved-test-function-observation-2026-09-19.md).

The operator prefers using native AosCore facilities without another demo-only
CM patch. Removing a demonstration action does not fix the storage defect.

## Decision

### Authorized storage correction — 19 September 2026

After platform-team confirmation of the shared-storage defect, the operator
explicitly authorized a minimal native correction and local regression proof,
followed by a successor Factory build only if the local gates pass. This
supersedes the storage-patch exclusion in item 1 below; the remaining lifecycle
decisions, including removal of operator Park/Resume, are unchanged. Preserve
storage while another version of the same instance still owns it; retain final
owner cleanup. Do not restore or reset the damaged Test implicitly, change Cloud,
or treat local tests as live restart/E2E qualification.

The following list records the original accepted decision with that amendment.

1. Do not implement or install a new native CM storage patch in this increment.
   Prepare a reproducible upstream report. Keep the accepted Factory `.35`
   unchanged; its existing, separately qualified deltas are not silently
   reverted or described as stock mainline. Adopting another upstream baseline
   requires a separate pinned-source and image qualification.
2. Remove Park/Resume from the operator Session panel and reject those actions
   at the Presenter command boundary, including requests from an older open
   browser. Historical receipts remain readable. Existing CLI primitives stay
   engineering-only, with an explicit storage-retention warning in help.
3. For a pause, use native Safe Stop and leave the controller running. Finish
   the run before shutting down the computer; create a fresh controller for the
   next run. A historical parked/partially resumed run or an established stopped
   controller offers confirmed Finish, not automatic same-run restart.
4. Finish retains its exact ownership, confirmation, uncertainty and Cloud
   retirement guards. Page entry never deletes anything. Preserve Factory,
   infrastructure, published releases and release-number continuity.
5. External network off/on, service upgrades, independent model Reset and
   Return to road remain separate operations. None implies Park, VM restart,
   model reset, relaxed conflict checks or fabricated observation generations.

## Qualification boundary

P7/P8 qualify a **continuous clean demonstration**:

- Create the empty Factory controller; start/reuse detached simulation;
  publish initial VDP; Provision and observe Cloud Online; attach the same
  source in stationary Manual; use explicit Safe Stop for component application.
- Exercise VDP V1/V2/V3, Brake V1/V2/V3 and Tire V1 plus same-profile replacement.
  Prove actual products, update continuity and old-record provenance, not merely
  upload/installation. SOTA remains independent of the component Safe Stop gate.
- Verify native advisory, independent Reset/CLEAR/renewed warnings, Manual and
  Return to road, source interruption, external-offline local authorization and
  analytics, stopped backend ingress and exact queued delivery after reconnect.
- Finish/deprovision/delete the owned Test and return to empty Create state.

CM/VM restart retention remains **known failing upstream**, outside this
mandatory operator flow; it is not marked passed or removed as a platform
storage requirement. Page reload, Presenter/backend recovery, service updates
and negative/partial-result handling remain applicable tests.

Periodic old-version cleanup can also execute during uninterrupted operation.
Therefore no guarantee of indefinite storage retention follows from this
decision. If it deletes state during the clean cycle, fail that cycle, preserve
evidence and report it; do not conceal the failure with retries or ledger edits.

Build a successor Factory only for a proved factory-owned delta after its gates
pass. UI/backend/service-package changes alone do not justify an image rebuild.
The current damaged Test is diagnostic evidence, not a clean acceptance run.

## Replacement map

This decision supersedes the Park/Resume operator action and mandatory same-run
restart stage in UI-STUDIO-026, the versioned-service audit and P7/P8 packet.
Earlier dated qualifications remain historical evidence with their exclusions.
The retained 2.10 mockup is not overwritten: its Park/Resume controls are a
documented intentional difference pending a separately versioned mockup update.

The current implementation/evidence status is in the
[delivery plan](../../planning/active/demo-studio-delivery-plan.md).
