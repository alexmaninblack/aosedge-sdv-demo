<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed First-use Reconciliation — 28 September 2026

## Boundary

Stage 3 continuation under [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md)
and the [native setup contract](../../contracts/distribution-installation/native-setup.md).
The [current plan](../planning/active/installable-distribution-and-reproducibility.md)
requires one coherent installed-package journey, not another vehicle rebuild.
`VDP-TIMEOUT-01` remains explicitly user-deferred; it is not investigated or
declared fixed by this work.

This record distinguishes source gates, immutable candidate verification,
native local installation and authenticated Cloud access. None alone qualifies
the complete installer, new-user enrollment, first launch or a clean Mac.

## Reconciled candidate

Kit 008: `/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-008-20260928`.
Independent application-manifest SHA-256:
`4a4c081db2da116e96cedc4cfe9d09204472720c6661d1184dc3fafbd72c9f8d`.

The candidate exports 86 application files from source checkpoint `22ee79e`
plus the recorded working-tree UI/lock changes. Compared with Kit 007 it includes
the current Cloud pair selection/prerequisite checks, managed lease correction,
and the Stage 2 corrected Presenter/Driving Control bytes. The embedded host
helper payload remains exactly the separately qualified Stage 2 payload;
installed CLI and Cloud workers use the current top-level application export,
not its older, unused embedded copy of the orchestrator. No source default is
substituted for a missing packaged input.

All **17,682 files / 35,114,354,531 logical bytes** passed transfer verification.
The refresh changed 12 existing/new program or metadata paths, removed one
superseded JavaScript asset from this new candidate only, and retained Kit 007.
Factory .39, CARLA Game, Python/native dependencies, backend archive and vehicle
payloads were not rebuilt. VM input changes are only the host-manifest reference.
APFS same-volume clones retain unchanged large blocks; logical size is not new
physical allocation. At completion, internal/Work free space was 90.75/562.17 GiB.

The initial native installation used preview 006 at
`/Volumes/SDV-Work/AosEdge-SDV/setup-preview-006-20260928/`.
Executable SHA-256:
`b94d19e767bf7b04b3d8fd5e1c4f7117645006f2af08d097273eb93b8b479390`.
It carries the independent Kit 008 pin and 2,430 verified private Python files.
Native compile, protocol/deadline self-test, local ad-hoc signature verification
and embedded helper startup passed. This is not Developer ID signing or
notarization. The corrected UI is preview 007, described below; no large payload
was rebuilt for that correction.

## Source gates

- Distribution: **206 tests pass**, including the explicit disposable-process
  ownership exclusion proof.
- Demo Control: **1,190 tests complete successfully; two intentional skips**.
- The first test invocation used the host Python without the test-only
  `packaging` dependency. The corrected invocation used the existing packaged
  Cloud Python; nothing was downloaded or installed into the runtime.
- A sandbox-only application run could not create local fixture sockets or
  inspect processes. Re-running with the reviewed local-test permission passed;
  no product guard was weakened. Fixture log messages are not live VM actions.

## Native journey

Target store: existing private `install-tests/stage3-store-001` on Work UUID
`591578E3-8196-4B44-A575-CEC76B406789`. Target instance is the new disposable
`/private/tmp/sdv8.k1qZuT/state`, not the working demo or earlier synthetic instance.

Native folder preflight passed, followed by a **fresh installation**, not reuse.
Its receipt reports `INSTALLED_NOT_ACTIVATED`; runtime, Cloud access, state-copy
and active-selection flags are false. The separate **Prepare local data** action
then selected Kit 008 at instance revision 1. The window showed **Local setup
complete — Cloud setup remains**, not a running or Cloud-ready demo.

UI observation bounds, not stopwatch measurements of the exact completion:

| Action | Last observed busy | First observed complete |
| --- | --- | --- |
| Fresh verified installation | 350.4 s | 387.2 s |
| Separate local preparation | 90.7 s | 117.7 s |

The actual installed-state probe passed using the installed Python with network,
developer repository, Homebrew, Xcode and developer credential paths denied;
the installed store was non-writable. It covered 71 application modules, all
five selectors, Factory .39, two packaged CLI executions, retained history and
release-ledger fixtures, and missing-credential/TLS negatives. This is installed
isolation evidence on this Mac, not a clean-Mac claim.

The native existing-access sheet passed local inspection of a matching synthetic
OEM/SP pair, explicit reference save, path-change invalidation, different-domain
rejection, and recovery to the matching pair. Synthetic certificate fixtures
use reserved `.test` names and grant no real access. **Check Cloud access** was
not submitted to a fake domain or with real credentials. Exact authorization
for a real staging GET-only check remains pending.

## Native message correction and recovery

The different-domain negative reproduced a real presentation defect: the sheet
correctly rejected the pair, but the main window incorrectly advised replacing
“Kit 007”. The failure was a certificate mismatch, not package corruption.
Both surfaces now use the same action-scoped explanation; obsolete hard-coded
kit wording is removed. A successful Cloud-local step also restores the normal
status color after an error. Five native self-test assertions cover the routing.

Corrected preview 007:
`/Volumes/SDV-Work/AosEdge-SDV/setup-preview-007-20260928/`.
Executable SHA-256:
`cec8360eff24628d3ed2984cc98c1b70701dc77ebc9751454f28834437432833`.
Native compile/self-test, ad-hoc signature and embedded bootstrap checks passed;
22 targeted installer tests also passed. Actual UI confirmed the matching
domain-specific explanation in the main window, then successful inspection/save
after restoring the valid synthetic pair. The immutable Kit 008 did not change.
The final documentation gate passed: 303 Markdown documents, 662 stable IDs and
38 Mermaid diagrams; `git diff --check` passed. No commit, push or release tag
was created in this slice.

Post-check reconciliation confirmed the saved config's inode, size, mode and
mtime unchanged on exact repeat; selection revision, history and release ledger
were preserved. Only file references were saved. No credential copy, run journal,
VM overlay or Cloud object was created in this instance.

## Native cold-start delay remains open

The first preview 007 launch reproduced the earlier long wait before Cloud
access, at `CLOUD_PACKAGE_LEASE`. The helper began at **13:45:13.967 CEST** on
28 September. A one-second sample at **13:46:08.931** showed Python `os.open`
waiting in kernel `__open`; it did **not** show a wait inside `flock`. It later
returned the expected different-domain rejection before a deadline error.
The first terminal UI observation was at 130.0 seconds; this is an observation
bound, **not** a measured 130-second helper runtime.

That progress stage includes package metadata reads, volume checks and usage
leases. The stack does not identify the filename, so an instance-lock root cause
is not established. Scoped system logs show TCC attribution to the preview and
its worker during this attempt, but correlation does not establish a permission
or OS-service cause. No locks were deleted and no security setting was weakened.

The exact unmodified preview 007 helper, invoked independently with network
denied, passed synthetic inspection in **3.711 seconds**: package stage at 0.526,
configuration lock at 0.661, pair check at 0.661 seconds. A subsequent actual
quit/relaunch of the same native preview passed local inspection, observed
complete by **14.0 seconds**. Warm success and this later relaunch do not explain
or qualify away the first-launch stall. Preserve it as a Stage 3 stability gate;
the next diagnostic must distinguish the exact file-open boundary and native
launch/OS attribution without bypassing trust, locks or permissions.

## Preservation and remaining gates

Working CARLA, Driving Control, Test QEMU and Presenter were observed at
PIDs 18124, 18215, 20333 and 72832 during the separate setup run. No live source
stop/start, Cloud mutation, model Reset, Factory replacement, Production change,
credential copy or VDP timeout change is part of this slice.

Still open: earlier file-open delay qualification; authorized real GET-only
access; strict-trust enrollment and
uncertain-response reconciliation; guarded first launch; retained-run lifecycle
and removal; signing/redistribution review; clean-system E2E. A local installed
result must not be presented as a completed Stage 3 exit gate.

Compact refresh proof and script are retained under
`CarlaSim/Build-distribution-stage2-20260926/kit-008-refresh-20260928.json`
and `refresh_kit_008_20260928.py`. The same evidence directory retains
`setup8-local-final.json`, `setup8-cli-timing.json`, the bounded stack sample and
before/after native message screenshots. Build receipts stay beside their exact
previews. Final local preservation audit observed 90.50 GiB internal and
561.91 GiB Work free; no broad cleanup was performed.
