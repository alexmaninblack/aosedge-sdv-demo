<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Remaining work and delivery plans

Plans describe required work; reading one grants no build, publication, Cloud
mutation or deletion authority. Current implementation and exact proof are
owned by the [baseline](../qualification/current-baseline.md), not a plan's date.

## Current plans and execution rules

- [Distribution and reproducibility](active/installable-distribution-and-reproducibility.md):
  completed engineering-preview slices and the remaining acceptance boundaries.
- [Human-friendly reproduction](active/work-packets/human-friendly-reproduction.md):
  R1–R3 implemented boundaries; separate R4 fresh-host source-build proof.
- [Autonomous M1 qualification](active/autonomous-m1-qualification.md):
  scenario-first execution, private test access, bounded diagnostics and cleanup.
- [Integrated Setup scenario](active/work-packets/integrated-setup-scenario.md):
  accepted Install / Connect / Open behavior and transaction boundaries.
- [Host sleep/wake recovery](active/native-sleep-wake-recovery-2026-09-21.md):
  still an unimplemented/unqualified planning item, separate from controller ignition.
- [Current roadmap](roadmap.md): consolidated remaining gates.

Presenter, integrated Setup, semantic native/browser runners, the unified
launcher and engineering-preview main/tag/publication flow are implemented.
The current M1 runtime API/UI and separate native certificate first-use
profiles passed. Do not reintroduce their completed gates as pending work.

Implemented readiness and independent Reset rules are maintained in the
[advisory contract](../../contracts/qm-advisory-profile/readiness-and-reset.md),
not in an active execution packet.

Closed P0/P1 implementation packets, prior migration/storage plans and old
experiment journals have been removed. Accepted obligations remain in
architecture, requirements and contracts; exact original plans are accessible
through immutable Git citations and the
[documentation retirement record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/d14e837c4cca30d8d9ebe83df996974b92c46f3b/workspace/checkpoints/documentation-retirement-20261015.json).
