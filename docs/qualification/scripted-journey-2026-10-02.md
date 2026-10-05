<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Scripted installed journey qualification

The [3 October live continuation](m1-live-journey-2026-10-03.md) records actual
installed controller/publication results, runner corrections and the replacement
sequence. This dated implementation receipt is not a claim of full live success.

- Date: 2026-10-02
- Status: Runner implemented; local regression and M1 host smoke passed;
  complete live journey and native acceptance remain open
- Source: uncommitted test-tooling changes on `22ee79e`, preserving existing work
- Candidate: installed Runtime Kit 025 and signed Setup 039, Factory .39
- Plan: [Installable distribution](../planning/active/installable-distribution-and-reproducibility.md)
- Usage: [Qualification runner](../../scripts/qualification/README.md#resumable-installed-journey)

## Implemented boundary

The test-only runner consolidates fixed signed-Setup and installed Demo Control
operations, serial version gates, real maneuvers, Reset, external-OFF recovery,
ignition and demo shutdown. It streams a reviewed adapter through pinned SSH
using the installed private Python in isolated, no-bytecode mode. It does not
copy a development tree, modify the immutable package, loosen authentication,
create credentials or replace product lifecycle owners.

Intent is persisted before mutation; uncertain outcomes reconcile the same
request, never blindly replay. Continuation re-observes dependencies instead of
trusting a past running state. Interrupted Reset/offline/ignition experiments
cannot be spliced across shutdown. Per-step durations and provenance remain in
private append-only attempts, with a derived report separate from product state.

On 2 October the user explicitly rejected repeated Docker lifecycle handling.
The runner now reuses the Engine, does not open Dashboard, and starts through
CLI only if the backend is confirmed absent and required. Shutdown closes demo
owners and containers but never stops/restarts/quits Docker. This exception is
also recorded in repository instructions and the debugging policy.

## Verification

The local qualification suites pass: **54 tests** across the journey and remote
harness, plus **15 installed-scenario tests**. These cover checkpoint reuse,
lost-response reconciliation without redispatch, strict target binding, serial
gates, stale product rejection, advisory correlation, Reset independence,
actual soak duration, interrupted-experiment rejection, source/support reporting,
and Docker preservation. Fixture success is not a live service result.

The earlier initial M1 run passed installation binding, backend-image
preparation, authorized existing OEM/SP reference selection and read-only Cloud
access. It created no automotive journal or Cloud Unit. A subsequent Presenter
smoke exposed a harness race: ordinary `ui.stop` returns before process exit.
The first immediate port read therefore reported `LISTENERS_REMAIN`. Read-only
reconciliation showed the ports had closed; the runner now waits up to ten
seconds for actual exit. No forced kill or product rebuild was used.

The corrected host smoke used the same installed candidate:

| Check | Elapsed | Result |
| --- | --- | --- |
| Installed selection and receipt | 0.742 s | Passed |
| Docker readiness and initial CLI startup | 4.824 s | Passed |
| Installed Presenter readiness | 13.957 s | Passed |
| Demo shutdown and actual exit | 11.050 s | Passed; Engine preserved |
| Engine reuse after demo shutdown | 1.971 s | Passed; no new Engine start, zero running containers |

The smoke created no VM, CARLA scene or Cloud Unit, and published/reset/deleted
nothing. No new kit, Factory or service build was necessary. Native windows were
not used as evidence. The prior failure and its successful reconciliation remain
in the attempt history; they were not overwritten.

The `status` command was also corrected to read records without creating a
directory or opening a writable lock. It works under a read-only access profile
and still checks the immutable record identity. Status is not a runtime action.

## Remaining acceptance

The new runner has not yet completed the live controller/serial-release,
Reset, five-minute offline and ignition sequence. Earlier manual/batched M1
results remain recorded in the [prior receipt](m1-installation-2026-10-01.md),
not relabelled as results of this runner. It starts after installed selection;
media transfer, installation repair and initial consent are separate gates.
Moving SOTA, secure native token entry and the final continuous native operator
journey remain open. No automatic Finish wrapper is implemented. Host sleep/wake
and external SSD checks are excluded; `VDP-TIMEOUT-01` remains deferred.

The exact candidate pins and previous installation evidence are in the
[complete-media receipt](m1-complete-media-2026-10-02.md). Private records are in
`.local/remote-qualification/m1-journey-025-20261002/`; they contain references
and sanitized facts, not passwords, tokens or certificate contents. No commit,
push, public release, cleanup of installed versions or credential migration was
performed for this tooling change.
