<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter operator experience

- Status: Branch DMG built and verified; native/live M1 review pending
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
the accepted package and credentials remain. Product installation is still
blocked by an idle Docker file-sharing holder, with zero running containers.
A single explicit M1-only Engine restart request is pending. Packaging/local
checks continue independently; the M1 gate is not a successful deployment.

The complete media was subsequently delivered and verified on M1. Transfer,
read-only mount and exact signed Setup/application pins passed. Installation
and live/native tests were not dispatched through the blocked state gate.
