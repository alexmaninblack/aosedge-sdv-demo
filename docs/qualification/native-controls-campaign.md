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
When those checks pass, the same signed Native UI Runner reports its own current
Accessibility grant and closes without a fixture, target or mouse input. Missing
permissions are BLOCKED, not automatically granted. The live client checks again
before actual input.

The current plan preserves the earlier Test. `fresh` therefore stops immediately
if its shared verification set contains another Unit. This runner does not retire
Tests, alter set membership, bypass occupancy or migrate retained journals. That
plan boundary is distinct from the standing authorization for ordinary disposable
staging replacement; it must not be silently reinterpreted by a script.

## Ordered execution

1. Validate the private plan, small source/build/media receipts and M1 preflight.
2. Mount the verified signed Setup media. In fresh mode, configure explicit VM
   access, save exact Subject references, create/provision the controller and
   prepare VDP/Brake/Tire using existing published releases. Confirm each declared
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
