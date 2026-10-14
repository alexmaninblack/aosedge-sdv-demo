<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Autonomous native controls campaign

One entry runs the current M1 native-controls scenario without conversational
step scheduling. It checks prerequisites before mounting media or starting the
vehicle environment, prepares the declared baseline through normal owners,
executes visible browser/native actions, and writes results after cleanup.
The runner and scripts remain qualification tools, outside the product payload.

This is the five-control live gate, not complete installer or release E2E.
API preparation does not count as UI acceptance. Real mouse input and separately
observed physical and backend effects are required by the existing
[native pilot contract](../planning/active/work-packets/native-ui-runner-pilot.md).

## Single entry

From the integration checkout, launch the already reviewed private plan:

```sh
python3 -B scripts/qualification/native_controls_campaign.py --plan PRIVATE_CAMPAIGN_JSON
```

Do not issue the individual preparation or UI commands alongside this campaign.
The working Mac only orchestrates M1; its qualification restriction remains
unit-only. No DMG, Factory or CARLA build is part of this entry.

## Plan and prerequisites

The plan is an owned mode-0600 JSON file. Schema version 1 accepts exactly:

| Field | Meaning |
| --- | --- |
| `schemaVersion`, `scenario` | `1` and `native-controls` |
| `mode`, `test` | `fresh` with null Test, or `retained` with the exact compatible Test UUID |
| `config`, `journey` | Absolute paths to the existing private, pinned transport and installed-instance inputs |
| `nativeBuild`, `nativeRunId` | Verified signed helper build and a new `native-ui-live-YYYYMMDD[-suffix]` identity |
| `dmg`, `remoteDmg`, `mediaRecords` | Existing immutable media and its earlier consumer verification records |
| `records`, `workspace` | New private campaign directory and existing build/scratch workspace |
| `versions` | Exact `vdp`, `brake`, `tire` baseline versions; never `latest` |

The normal package must already be installed and selected in the declared
instance, with the approved certificate references saved through Setup. This
entry is not a replacement for first-use installer enrollment. Existing explicit
VM-access input/profile, Factory and backend images must be available. Credentials
remain referenced by the private inputs; no password, certificate or token enters
the plan, report or Git.

Preflight verifies candidate selection, exact Test policy, idle owners, console,
unlocked desktop, shared Docker, VM access, Factory/backend availability and the
normal read-only Cloud prerequisites. Check shared Test-set occupancy before
media work. A local instance directory is not an independent Cloud tenant.
Require normal same-provider publication receipts and their exact baseline
versions before creating a vehicle; Cloud version availability alone is not
assignment authority. Preserve authoring history through normal quiescent
version selection, not by copying/adopting receipts or migrating a Test journal.
When those checks pass, the same signed Native UI Runner reports its own current
Accessibility grant and closes without a fixture, target or mouse input. Missing
permissions are BLOCKED, not automatically granted. The live client checks again
before actual input.

The controls entry itself preserves existing Tests: `fresh` stops immediately
if the shared verification set contains another Unit. The operator-authorized
clean replacement wrapper first binds the exact old Test/Unit/Node, journals one
normal Finish intent and confirms Cloud absence, an empty set and local
journal/overlay removal. Only then does it invoke this fresh controls entry.
Neither entry edits set membership directly, bypasses occupancy or migrates a
retained journal. Reusable packages, certificates, releases and shared Docker
remain outside retirement.

## Ordered execution

1. Validate the private plan, small source/build/media receipts and M1 preflight.
2. Mount the verified signed Setup media. In fresh mode, configure explicit VM
   access, save exact Subject references, create/provision the controller and
   prepare VDP/Brake/Tire using existing published releases. The normal workspace
   owner opens a visible Presenter before controller creation; CARLA and Driving
   Control join the same layout once the simulator starts. Require fresh native
   Presenter geometry and ordering, not HTTP-server readiness alone. Confirm each declared
   version through normal owners. There is no new publication, Reset or deletion.
3. Close API preparation before this profile's deliberate cold UI-startup checks.
   Start the normal visible Presenter, CARLA and Driving Control through actual
   browser controls. This second startup is explicit cold-start coverage, not a
   warm-reuse speed benchmark.
4. Pin the fresh installed versions before any native input. Execute Autopilot,
   Safe Stop, Brake maneuver, Return to road, Tire maneuver and Return to road.
   Require real movement/stopping, new completed source-bound maneuver receipts,
   new same-version backend products, stationary Manual return and unchanged
   installed releases. No agent/CUA callback schedules these six inputs.
5. Close native/browser clients and normal demo owners, verify their exit and
   detach only owned media. Preserve Test data and shared Docker. Write the final
   campaign report even when an earlier phase was BLOCKED or failed.

## Results and recovery

`campaign-report.json` contains the complete elapsed time, candidate/Test binding,
each phase's outcome and duration, explicit NOT_RUN phases, cleanup result and
separate native-controls/full-E2E status. `summary.txt` is a small readable result.
Baseline owner attempts remain under `baseline/`; UI intents, receipts, stages
and bounded evidence remain under `ui/`. No raw exception or credential output
is copied into reports.

Exit codes are 0 for PASS, 2 for BLOCKED, and 1 for FAIL/UNCERTAIN. A failed cleanup
cannot produce PASS. An existing campaign directory is never replayed or
overwritten. A lost mutation/input response remains uncertain: inspect the same
owner/request evidence, not a new click. Reuse or repair must follow a diagnosed
outcome and verified cleanup, with a separately bound campaign where appropriate.

Local unit tests use mocks only and launch no GUI:

```sh
PYTHONPATH=scripts/qualification python3 -B -m unittest \
  scripts/qualification/test_native_controls_campaign.py -v
node --test scripts/qualification/test_ui_journey.mjs
```

## Continuous release and lifecycle campaign

The separate `continuous-campaign` profile retains the compatible Test and
reuses its assigned Subjects. It composes the release story, installed views,
moving QM updates and explicit same-Test Stop/Start in one healthy runtime
sequence. It never creates or retires a Test, reassigns Subjects or deletes
backend history. UI preparation/publication is serial, with installation
confirmed before advancing and physical Safe Stop for VDP.

```sh
python3 -B scripts/qualification/continuous_ui_campaign.py \
  --plan PRIVATE_CONTINUOUS_CAMPAIGN_JSON \
  --display-assertion-helper APPROVED_PRIVATE_DISPLAY_HELPER
```

Use the same exact plan schema above, with `scenario` set to
`continuous-campaign`, `mode` set to `retained`, the current compatible baseline
versions and a new `native-ui-live-YYYYMMDD-continuousSUFFIX` run identity.
The helper is the already approved `native_live_awake.py` in the private
qualification directory, not an arbitrary program. It temporarily holds the
unlocked M1 display active and closes its own assertion in the entry's finalizer;
it neither unlocks the screen nor changes persistent settings.

The signed input client has a separate campaign-stage allowlist and remains
bound to its original process. No native input follows the explicit restart.
The scenario independently proves preservation and stationary Manual attachment
through the normal owners, then confirms final Stop and closes all owned clients,
runtime and media. An uncertain input/publication is never replayed. Shared
Docker and persistent Test data remain intact. The report distinguishes Step 3
PASS from full installer E2E, which remains separate.

The [M1 receipt](continuous-ui-campaign-2026-10-12.md) records the passing 42-stage
campaign, exact releases, timings and final closure.

## Focused restart diagnostic

The 14 October visibility amendment checks the Team view and its completed
publication/installation stages, then the Vehicle card and detail dialog for
each exact profile/version before the next release. Moving updates retain
independent platform-version and motion checks. Fixed Cloud response, source
timestamp, binding and local-process diagnostics accompany the visible run;
they do not override status or product-quality gates. The separate
`ui_pilot.py --scenario status-observation --display m1` scenario starts the
retained Test, connects in Manual, observes status while switching Vehicle and
Platform Team for about one minute, and closes all owners. It publishes,
resets, provisions and deletes nothing. Results and scope are in the
[status report](presenter-status-and-release-views-2026-10-14.md).

The `ui_pilot.py --scenario restart-check --display m1` profile starts the
preserved installed Test, binds its live VDP and service versions, performs one
explicit Stop and Start, checks identity, models, backend history, stationary
Manual control and platform service health, and confirms final Stop. It uses
the same private connection, journey, media, new records and workspace inputs
as the other visible UI profiles. It does not require native maneuver input,
publish releases, reset models, reassign Subjects, provision or retire a Test.

Both this profile and the continuous campaign record fixed Boolean restart
predicates when their values change. The existing predicates and 120-second
deadline are unchanged. A separate restart pass does not turn an earlier
failed continuous campaign into PASS; see the
[14 October results](m1-clean-install-e2e-2026-10-14.md).

The release-story section also records bounded Brake window terminal and chunk
fields without treating invalid windows as complete products. In the continuous
profile, a new fully delivered invalid V1 window plus a completed independent
exercise result fails with `MANEUVER_INCOMPLETE_SOURCE_GAP` or the corresponding
fixed abort reason. No click, publication or maneuver is automatically retried,
and the existing quality criteria and deadline remain intact.
