<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter operator experience

- Status: Branch ready for review; 117 scripted steps and bounded native Start/Stop passed; main integration pending
- Date: 2026-10-11
- Branch: `codex/presenter-human-friendly`
- Baseline: `a4afa82` on main
- Scope: Presenter UI and its fixed Test operation plans

The operator approved the Presenter audit and requested implementation on a
separate branch. Keep main and the accepted installed candidate unchanged.
The ordinary interface supports the demonstration; environment configuration
and engineering diagnostics are secondary. Project documents remain English.

## Accepted behavior

Keep Vehicle, Platform, Brake and Tire perspectives, serial release preparation
and publication, native maneuvers, independent backend evidence and per-service
Reset. Preserve exact ownership, scope, freshness, Safe Stop and at-most-once
submission checks.

- Provide one Demo controls entry. Default to the full story. Offer quick
  preparation under Advanced preparation before Create only; freeze that choice
  while a run exists. Show a single Factory image as information, not a choice.
- Keep installed details and release management as separate, labelled actions.
  Empty slots identify Brake/Tire and offer their release view explicitly.
- Make next-step guidance contextual. On the appropriate team screen, offer
  Prepare, Publish or first assignment rather than navigating to that same
  screen. Results guidance names the native Brake/Tire maneuver. Completion
  means observed software/results, not complete qualification, and does not
  promote destructive deletion as the normal next action.
- Routine local preparation, Create, simulator start, controller start and
  layout restoration use one deliberate click. Publication, first assignment,
  provisioning, quick preparation (which publishes), Cloud changes, shutdown
  and deletion retain short, effect-specific confirmations. Technical execution
  detail is expandable. Reset retains its accepted one-click contract.
- Stop demo and keep data composes the existing Test-scoped simulation stop,
  Test VM stop and owned Tire/Brake backend stop operations in that order.
  Do not retire a Unit, delete a disk, reset a model, stop Docker Engine or
  mutate Production. Stop on the first unconfirmed step; unknown results never
  authorize replay. Keep Presenter available to show the receipt.
- Start controller on a known stopped Test composes existing Test VM start and
  owned backend starts. Do not create/provision/publish again. Guide simulator
  start and attachment afterward through existing operations; do not start
  Autopilot. This is separate from automatic ignition attachment recovery.
- Rename destructive Finish to Delete Test & start over, preserving the exact
  retirement owner and confirmation. Closing Presenter keeps the demo running;
  it is not Stop or deletion. Legacy `reset` remains the wire action.
- Put Cloud/OEM/SP configuration diagnostics under Advanced settings. Explain
  that complete pair setup belongs in Setup, explicitly name OEM-only selection
  and show certificate presence separately from authenticated access. Preserve
  existing check/prepare operations; hide neither failures nor authority.
- Rename Trace to Activity. Keep scope-specific refresh actions and existing
  automated observation. Mock-history inspection is an engineering disclosure,
  not an ordinary result choice. Keep record filters, charts and pagination.

These fixed composition changes add no credential channel, lifecycle journal,
CLI interface, automatic retry, safety-policy change or new Cloud authority.

## Implementation and qualification

1. Amend the current interaction contract and fixed operation-plan tests.
2. Implement the UI and bounded native plan compositions on this branch.
3. Run TypeScript, Python owner-plan, UI unit and browser regression gates.
   Cover stopped/unknown/partial/uncertain states, first assignment, repeats,
   cancellation, single-click preparation and unchanged peer/Production scope.
4. Build only Presenter after local gates; use retained Factory/CARLA inputs.
   Keep any branch candidate separate from the accepted installed candidate.
5. Record evidence and push this branch, never merge it automatically. Native
   M1 and live stop/start acceptance remain separate from fixture test results.

## Completion criteria

The ordinary flow contains no duplicate controls entry, ambiguous destructive
Finish, self-navigation prompt or mandatory mock/certificate debugging step.
Known stopped controllers have an explicit power-on path. Publications remain
serial and separately confirmed; VDP application remains vehicle-owned Safe
Stop. Stop and deletion have different effects and receipts. Negative and
uncertain paths fail closed. Branch qualification is not main acceptance.

## Local qualification evidence — 2026-10-11

The following gates passed against this branch, not the installed M1 kit:

| Gate | Result |
| --- | --- |
| Presenter TypeScript check | PASS |
| Presenter unit suite | 359 tests passed across 34 files |
| Presenter browser suite | 142 tests passed |
| Orchestrator Presenter family | 61 tests passed |
| Backend owner suite | 35 tests passed |
| Simulation owner suite | 37 tests passed |
| VM owner suite | 30 tests passed |
| Repository documentation and whitespace checks | PASS |

Browser coverage includes the ordinary service flow, first assignment,
publication cancellation, both supported operator window layouts, distinct
Stop/Delete actions, same-Test restart without Create or Cloud mutation, and
uncertain-result guards. Browser responses are fixtures; they do not prove
native or live Cloud execution. Owner tests verify the fixed stop/start plans,
partial-stop interruption and at-most-once submission.

At the initial local-gate checkpoint, only the Presenter web assets were built. The separate, mutable branch-review
output is at
`/Volumes/SDV-Build/sdv/build/candidates/presenter-human-friendly-20261011/presenter-ui`.
It is not a signed installer, a new release kit or an accepted installed demo.
Factory and CARLA were not rebuilt. Compact local logs are under
`.local/presenter-human-friendly/`; browser screenshots remain in the ignored
Presenter test-results directory. The test-owned browser server was stopped.

Main remains at `a4afa82e2dd2e6007102797cb785e5f004e46db6`. The installed M1
candidate, persistent Test data and shared Docker Engine were not changed by
this work. Publish only `codex/presenter-human-friendly` for review. Before any
main integration, review the branch UI and qualify the real existing-Test
stop/start sequence through its native owners.

## Requested DMG and M1 campaign — 2026-10-11

The operator subsequently requested a complete DMG with this Presenter and an
autonomous M1 end-to-end run, still on this branch. The candidate is assembled
on `SDV-Build` using the canonical packaging owners and retained Factory/CARLA
inputs. Neither heavy component is recompiled. Setup retains the authorized
Apple Development signature; this is an engineering preview, not a notarized
external release. Detailed evidence is recorded in the
[branch candidate qualification](../../../qualification/presenter-human-friendly-2026-10-11.md).

The scripted journey now has 117 fixed steps, including serial VDP/Brake
versions, Tire, maneuvers and product delivery, independent resets, offline
delivery, ignition, and the new same-Test Stop/Start plans. The qualification
harness suite passes 78 tests, including fresh stop-state observations,
unchanged identity/Docker Engine and interrupted-experiment guards. Fixture
results do not close native or live gates. The exact installed candidate binds
all subsequent evidence; no previous M1 candidate's passes are inherited.

M1 preparation retired the old Test through its normal lifecycle owner after
the tool-required exact-target approval. The agreed unused copies were removed;
the accepted package and credentials remain. Product installation was
blocked by an idle Docker file-sharing holder, with zero running containers.
The operator approved one M1-only Engine restart; it completed and the unchanged
product quiescence check passed, with images/data and Engine identity preserved.
This exceptional host maintenance is not part of the routine campaign.

The complete media was subsequently delivered and verified on M1. Transfer,
read-only mount and exact signed Setup/application pins passed. Installation
and live/native tests were not dispatched through the blocked state gate.
After that gate cleared, a changed media `ctime` caused another fail-closed
preflight. Full consumer digest re-verification confirmed unchanged bytes and
recorded the current stable identity without retransmission. Signed Setup
installation and backend preparation passed.

The first installed journey stopped at redundant connection confirmation after
provisioning. Diagnosis found an incoming VDP transaction waiting for Safe Stop;
the existing-assignment and trust guards remained unchanged. The harness now
observes physical Safe Stop and settlement of that incoming update before
confirming the connection. All 78 harness tests pass; the DMG needs no rebuild.
Normal retirement removed only that failed disposable Test after diagnosis.
The corrected clean journey reused the same verified installed package. Serial
releases, products, resets, offline operation and ignition passed. Its final
same-Test preservation assertion revealed a harness expectation defect:
explicit connection selects stationary Manual, unlike raw ignition's Safe Stop.
The assertion was corrected without relaxing freshness, identity or history
requirements; all 79 harness tests pass. The campaign remains 110 PASS, one
failed assertion and six not run. A separate fresh 26-step Stop/Start experiment
passed completely, including new results and ordinary shutdown.

Native Setup Cloud connection and Open SDV Lab were observed. Review exposed
a real stopped-controller UI defect: an empty `preparation` object was treated
as an unfinished quick recipe and hid Start controller. The source correction
keeps nonempty partial checkpoints guarded. TypeScript, 361 unit tests and
142 browser tests passed; a corrected complete DMG was assembled with
retained heavy inputs. No prior candidate's passes are transferred to it.

Before corrected installation, the ordinary installer required its 90 GiB
reserve and the current instance retained the tested run.
Auto-review rejected proposed retirement/media cleanup before execution.
The operator then approved the specific completed Test/Unit and two old DMGs.
Normal retirement confirmed COMPLETED / RETIRED and an absent journal; only
the named unused media copies were deleted. Both installed packages, rollback,
credentials and compact evidence remain intact. A fresh 117-step campaign is
bound to the corrected media manifest, without inherited candidate results.
The preceding native review runtime and Setup were closed, the review media
detached, and a fresh host probe confirmed zero owned processes/listeners.
Shared Docker remains running; it was not restarted for this new cycle.

The corrected campaign subsequently passed all 117 steps on new Test
`918df550-d41a-4e06-8052-23df0f60a74f`, including serial VDP 147/148/149,
Brake 124/125/126 and Tire 64, real products/advisories, independent resets,
300-second offline processing/recovery, ignition and same-Test Stop/Start with
preserved models/history and new results. No failed or uncertain campaign steps
or source-revision warnings remain. Source correction is committed at
`3863db63b2d04c8e5e43174c11f311e878ccbf44`.

The corrected signed Setup also passed native existing-pair Cloud connection,
Continue installation and Open SDV Lab. Presenter offered Start controller,
started that same Test, left it running after Stop cancellation, and stopped
it with data preserved after one confirmed Stop. Fresh normal-owner reads
corroborated each transition. This closes the stopped-controller button check,
not full native layout, token-entry or operator-journey acceptance.

Final ordinary shutdown and Setup Quit were verified by read-only reconciliation
and a host probe: zero demo processes/listeners, zero Setup processes and zero
running containers. Docker retains its original running identity. The corrected
media was normally detached; Test, packages, credentials and evidence remain.
The branch is ready for operator review. Main stays unchanged; moving SOTA,
complete native acceptance and installation interruption/repair retain their
separate gates, and VDP-TIMEOUT-01 stays deferred.
