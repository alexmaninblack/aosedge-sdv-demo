<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Remaining work and delivery plans

Plans describe required work; reading one grants no build, publication, Cloud
mutation or deletion authority. Current implementation and exact proof are
owned by the [baseline](../qualification/current-baseline.md), not a plan's date.

## Remaining work

- [Presenter stability and clarity](active/presenter-ui-stability.md): one
  source/fixture/package/API/UI packet; retained Test and separate review branch.

- [Current roadmap](roadmap.md): all remaining delivery/reproduction gates,
  including independent fresh-host developer reproduction.
- [Host sleep/wake recovery](active/native-sleep-wake-recovery-2026-09-21.md):
  accepted recovery behavior not yet implemented/qualified; separate from ignition.
- [Formal stimulus calibration](../qualification/d4-003-stimulus-calibration-plan.md):
  outstanding verification, not a passed result.

## Implemented behavior and execution

- [Setup contract](../../contracts/distribution-installation/native-setup.md):
  ordinary Install / Connect / Open and transaction boundaries.
- [M1 scenario guide](../../scripts/qualification/README.md): scenario-first
  execution, private test access, reconciliation and mandatory cleanup.
- [Release campaign](../development/release-campaign.md): exact-candidate
  source/tag/delivery and consumer gates.
- [Readiness and Reset](../../contracts/qm-advisory-profile/readiness-and-reset.md):
  the current service contract, not an active implementation packet.

Completed work packets are retained in Git, not as competing active plans.
Their removal does not waive accepted requirements or change selected artifacts.
