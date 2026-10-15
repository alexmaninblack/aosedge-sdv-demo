<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installable distribution and reproducibility

- Status: engineering-preview implementation delivered; remaining qualification gates explicit
- Version: 2.0
- Prepared: 2026-09-25
- Updated: 2026-10-15
- Owner: SDV Lab integration
- Authority: planning only; no new runtime, signing, publication or deletion authorization

## Current execution route

Use the [README launcher](../../../README.md#start-here), the
[current baseline](../../qualification/current-baseline.md) and
[release selection](../../getting-started/release-status.md).
The selected operator package is an engineering preview, not a notarized release.

| Original stage | Implemented / measured state | Remaining boundary |
| --- | --- | --- |
| 0 — Inventory | Source, binary-input and ownership definitions implemented | Maintain exact pins and redistribution obligations |
| 1 — Standalone simulator | Packaged CARLA and native Driving Control operate on M1 without Unreal Editor | Fresh source-build recipe and formal stimulus/calibration matrix are separate |
| 2 — Portable runtime | Complete controller/simulator/Gateway/backend inputs and installed runtime available | Deferred VDP timeout and broader fault matrices are not hidden |
| 3 — Installation and access | One DMG, native Install / Connect / Open, persistent launcher, existing pair and new issuance for existing accounts | New account registration, broad consent and target-host interruption/repair/update/removal cases |
| 4 — Reproduction documentation | One A/B/C launcher, task-oriented guides, pinned source/input resolution | R4 independent fresh-host developer build |
| 5 — Automation | Named API/browser/native scenarios with timing, bounded evidence and mandatory cleanup | Missing acceptance cases must be implemented as scenarios, not agent click loops |
| 6 — Target qualification | Current M1 Production Test passed 118 API, 42 visible browser UI and required native input; native Setup issuance passed separately | Not blanket acceptance of every host, permission, calibration, negative or dual-role case |
| 7 — Preview release | Current source fan-in, tags, anonymous DMG consumer and option A promotion passed | Developer ID/notarization and complete general-public release closure |

## Remaining order

1. Reproduce the developer build on a declared fresh environment with only
   documented tools and obtainable inputs; record reuse, time and peak space.
2. Close candidate-bound installation/recovery/permission and new-account paths
   only through their explicit independent scenarios.
3. Reconcile license/source obligations and Developer ID/notarization before
   claiming general-public macOS distribution.
4. Close formal calibration/resource/negative/expanded-scope obligations when
   their work is authorized; do not claim them from a scoped Test result.
5. Maintain the [release campaign](../../development/release-campaign.md) so
   only exact accepted media becomes option A; retain truthful exclusions.

R1–R4 scope and exclusions are in the
[reproduction packet](work-packets/human-friendly-reproduction.md).
The [roadmap](../roadmap.md) is the compact remaining-work view.

## Execution and preservation

All installed/live qualification runs on the dedicated M1 and its internal disk.
The development Mac runs unit/static checks and authorized builds/orchestration,
not an alternate live acceptance environment. Each named scenario owns
preflight, ordered actions, independent effects, timings, bounded diagnostics
and final shutdown. System consent and genuine account prerequisites remain
explicit; there is no uncertain-mutation replay.

Stop and keep data is not Finish/deletion. Reuse shared Docker Engine and close
only test-owned containers, VMs, windows, helpers and listeners after checks.
Keep credentials and private state out of media, source and reports.
Publish software versions serially and verify each before publishing the next.
VDP FOTA requires Safe Stop; QM SOTA does not inherit that gate.

Sources, caches and heavy build work use the declared storage policy. Normal
developer builds allow internal or external writable APFS storage and check
Docker's actual backing disk independently. M1 installation does not depend on
a development SSD. Never move shared Docker data as a build side effect.

## Design and history

[ADR 0018](../../architecture/decisions/0018-installable-demo-and-first-use.md)
and the [native Setup contract](../../../contracts/distribution-installation/native-setup.md)
own enduring installation boundaries. The
[original staged execution record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/planning/active/installable-distribution-and-reproducibility.md)
preserves earlier decisions, deferrals and measurements. Closed execution
chronology is not a second current plan and grants no continuing mutation authority.
