<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 UI qualification timing and optimization

- Date: 12 October 2026
- Branch: `codex/presenter-human-friendly`
- Source checkpoint: `fd15f7d`
- Status: Timing analysis recorded; optimization direction accepted; implementation not started

The six visible UI attempts in the clean M1 campaign took 42 minutes 22 seconds
of measured runner time. Three early harness failures accounted for 10 minutes
6 seconds. Browser navigation was fast; repeated controller/simulator startup,
agent-assisted native clicks and independent result checks dominated the runs.
Retain Playwright and improve those boundaries before considering another
browser framework. No optimized-run timing or unattended native acceptance is
claimed yet.

The [candidate qualification receipt](presenter-human-friendly-2026-10-11.md)
defines the installed successor, Test, artifact pins and separate acceptance
results. This analysis covers that campaign on 11–12 October, not the earlier
weeks of installer development. All live checks used M1 internal storage and
Aos Cloud staging. Main, Production and the video repository remain outside
this follow-up.

## Current execution model

The development-side [Python coordinator](../../scripts/qualification/ui_pilot.py)
starts the fixed scenario over the pinned SSH connection and collects bounded
evidence. [The M1 adapter](../../scripts/qualification/ui_m1.py) runs Node.js
and Playwright against the installed Presenter server in a visible, signed
Chrome app-mode window on M1. CARLA, Driving Control and Presenter must occupy
the verified operator layout. The coordinator does not run a live acceptance
test on the development Mac.

[The browser scenario](../../scripts/qualification/ui_journey.mjs) locates actual
controls by accessible role/name, clicks them and waits for the real submission
acknowledgement and operation result. It neither mocks responses nor substitutes
direct mutations for UI clicks. An exact command/session/request guard rejects
unarmed or repeated mutations. Independent read-only product-owner queries
confirm versions, identity, controller state and correlated backend results.
They do not perform the action under test.

Safe Stop, Brake maneuver, Tire maneuver, Return to road and Autopilot are
native Driving Control buttons, not HTML controls. The current scenario emits
a native gate and waits for the agent to click the visible button through CUA.
[The witness helper](../../scripts/qualification/ui_native_gate.py) only records
an already performed click; it cannot click or establish success. The runner
then checks the physical/result postcondition independently. This is hybrid
agent-assisted execution, not an unattended native UI runner.

Native Setup and the installed WKWebView Presenter shell were checked separately
through Screen Sharing/CUA. Chrome browser acceptance does not qualify those
native surfaces. The current CUA-only witness contract remains in force until
a supported replacement execution method and its guards are defined.

## Measurement boundaries

- `pilot-report.json` records monotonic runner duration. Its timer starts after
  transport preflight, the initial owner observation and reusable UI-tool
  preparation. It includes media work inside the scenario, Presenter bootstrap,
  browser execution and final cleanup. It is not the duration of the entire
  work session.
- `browser-report.json` records monotonic successful-stage durations. These
  include owner startup, independent reads, native-click waiting and result
  settlement when those occur inside a stage. Failed stages have no stored
  monotonic stage duration; do not treat them as zero-cost steps.
- `attempt-*.json` records individual media/setup/API/cleanup operations.
  `ui-events.jsonl` provides timestamped events, not a separately timed native
  click or a complete latency breakdown.
- Native-stage time currently combines agent response, the click, physical
  execution and postcondition checks. The records cannot attribute all of
  that time to the vehicle or all of it to the agent.
- Diagnosis, edits, one-time tooling and separate native acceptance are not
  fully covered by these timers. Wall-clock gaps are not a benchmark of one
  uninterrupted scenario. Displayed elapsed times below round to the nearest
  second; calculations use the recorded fractional seconds.

Compact private evidence remains under `.local/remote-qualification/` using
the run names below. Raw credentials, browser profiles and network traces are
not part of this Git document.

## Visible UI attempt totals

Run names in this table follow the `m1-clean-20261011-` prefix. Each duration
includes that attempt's final shutdown.

| Run suffix | Seconds | Elapsed | Result and limiting condition |
| --- | ---: | ---: | --- |
| `ui-story` | 228.227 | 3:48 | FAIL; native layout had not been requested |
| `ui-story-restored` | 189.735 | 3:10 | FAIL; Advanced settings inspection was not armed |
| `ui-story-restored-r2` | 188.313 | 3:08 | FAIL; existing bounded layout recovery was treated as terminal failure |
| `ui-story-restored-r3` | 1132.407 | 18:52 | FAIL; serial VDP/Brake stages passed and Tire published, but the native Tire witness expired |
| `ui-tire-review` | 376.667 | 6:17 | PASS; 21 installed-browser stages with fresh Tire maneuver and Return to road |
| `ui-moving` | 426.581 | 7:07 | PASS; 12 stages including Brake/Tire installation while moving |
| Total | 2541.930 | 42:22 | Six attempts, not a single passing full-E2E run |

The first three failures took 606.275 seconds (10:06) without publication.
Their diagnosed harness corrections are already in the source checkpoint.
They are avoidable repeat-attempt cost, not normal platform processing time.
The Tire witness expired after approximately 120 seconds of waiting; retaining
the later continuation does not turn the interrupted story into PASS.

## Successful installed UI breakdown

The 21-stage `ui-tire-review` run has the following grouping. Screen navigation
here means the scripted control/content assertions and screenshots; it is not
a standalone proof of fresh Cloud metric delivery or human visual readability.

| Group | Seconds |
| --- | ---: |
| Open, controller, CARLA, Manual attachment, layout and visible workspace | 139.486 |
| Current installed-release observations | 8.819 |
| Tire maneuver and Return to road | 90.160 |
| Installed dialogs, team screens, Cloud/resources, backend/records and Activity | 1.584 |
| Independent Brake and Tire Reset with preservation checks | 28.784 |
| Stop cancellation and confirmed Stop | 22.402 |
| Remaining runner time outside measured browser stages | 85.432 |
| Total | 376.667 |

Controller startup took 49.332 seconds, CARLA startup 70.981 seconds, Manual
attachment 12.941 seconds and layout restoration 4.217 seconds. The remaining
runner time included a required changed-media digest re-verification
(44.540 seconds), bootstrap and cleanup. It must not be labelled entirely
as browser overhead.

The Brake/Tire Reset operations reached their observed Presenter completion
receipts in approximately one second each. The complete correlated stages took
16.680 and 12.104 seconds, including before/after owner queries and preservation
checks. A completion receipt alone cannot replace those checks.

## Moving service update breakdown

| Group in `ui-moving` | Seconds |
| --- | ---: |
| Startup through verified visible workspace | 146.865 |
| Current installed releases | 9.969 |
| Native Autopilot and motion confirmation | 39.253 |
| Brake preparation, publication and moving installation confirmation | 54.582 |
| Tire preparation, publication and moving installation confirmation | 50.527 |
| Native Safe Stop and physical confirmation | 64.776 |
| Confirmed Stop | 17.978 |
| Remaining runner time outside measured browser stages | 42.631 |
| Total | 426.581 |

Test identity, boot and VDP remained unchanged. These stage durations include
independent reads and, for native stages, agent-assisted clicks. They are not
pure download, installation or actuator timings.

## Installation and API context

| Recorded operation | Seconds | Elapsed |
| --- | ---: | ---: |
| DMG delivery and consumer verification | 216.502 | 3:37 |
| Initial media mount and verification | 71.370 | 1:11 |
| Setup installation | 127.393 | 2:07 |
| Setup backend preparation | 38.526 | 0:39 |
| Sum of those four operations | 453.791 | 7:34 |
| All 127 API attempts, including support/reconciliation | 1845.882 | 30:46 |
| Latest 117 successful API step durations only | 1624.056 | 27:04 |

The API attempt window was 22:10:12–22:49:21 on 11 October, Europe/Berlin:
39:09 wall-clock, with approximately 8:23 outside timed attempts. It includes
Cloud-503 diagnosis and resumption, not an uninterrupted source-identical run.
The latest successful steps and all-attempt totals overlap and must not be
added together. The actual offline soak was 302.920 seconds and remains a
required test duration, not removable waiting overhead.

The session extended from delivery around 22:02 to the source commit at 00:15
on 12 October, approximately 2 hours 12 minutes. That includes separate native
checks, investigation and documentation; it is not the runner benchmark.

## Bottlenecks and optimization priorities

1. **Agent-assisted native execution.** A missed native gate caused the Tire
   interruption. Removing the dependency on conversational agent scheduling
   is the highest-priority execution improvement. The exact native mechanism
   still needs to be selected; a fabricated witness or driver RPC is not an
   equivalent UI test.
2. **Repeated healthy startup.** Across six attempts, controller startup
   totalled 294.529 seconds and CARLA startup 401.759 seconds: 11:36 together,
   before attachment. One healthy campaign can retain owners between logical
   sections. Failure cleanup and explicit Stop/Start acceptance must remain.
3. **Independent read transport.** Owner queries currently start separate SSH/
   packaged-Python executions. The browser query broker waits synchronously;
   unlike the already asynchronous native-witness reader, it can block the
   Playwright event loop. The avoidable portion is not separately measured yet.
4. **Media and cleanup overhead.** Two changed-identity digest checks took
   45.831 and 44.540 seconds. Preserve integrity guards and reuse evidence only
   for unchanged copies. Investigate unnecessary identity changes rather than
   suppressing re-verification. Normal shutdown remains mandatory; its
   read-only reconciliation must never become a repeated stop mutation.

Observed Presenter snapshot-read medians were approximately 149–202 ms across
these runs, with isolated delays up to 7.596 seconds. The small screen-navigation
durations support retaining Playwright, not attributing every delay to browser
automation. They do not establish a guaranteed future runtime.

## Ordered follow-up plan

The operator requested recording this direction on 12 October. This checkpoint
changes documentation only. The steps below remain planned; it does not launch
tests, change permissions, choose a new native framework or merge main.

| Step | Work | Required exit evidence |
| --- | --- | --- |
| 1 | Add separate native-wait, click, acknowledgement, owner-completion, installation/result and cleanup timings | Correlated fixed-field events and local monotonic durations; missing/failed phases are explicit, not zero or PASS |
| 2 | Define and implement supported native UI execution on M1, removing conversational click scheduling | Actual visible button execution, exact window/action/Test/session binding, independent physical/result proof and negative guard coverage |
| 3 | Compose one healthy campaign across release story, installed views and moving updates | Serial install-before-next-publish retained; no repeated healthy section startup, no skipped lifecycle test; failure and final cleanup verified |
| 4 | Make independent query handling asynchronous and reuse a bounded read-only transport/worker where compatible | Fresh exact owner reads without cached green state, mutation authority or widened access; cancellation and timeout cleanup verified |
| 5 | Compare the optimized campaign with this baseline and publish its separate acceptance receipt | Cold and retained-runtime timings distinguished, explicit exclusions, complete ordered results, zero owned processes/listeners and unchanged Docker/Test data |

Step 2 first records the supported execution method and changes to the current
CUA witness contract before implementation. UI input must still act on the
actual native control. No broad Accessibility grant, extra network listener,
credential channel or direct mutation fallback follows from this plan.

The campaign in Step 3 retains the already running environment only inside one
active healthy sequence. Its final boundary and any failed sequence close owned
applications, VM, backends, browser/profile and helpers through normal owners.
Keep an explicit same-Test Stop/Start check; do not optimize away its purpose.
Unknown outcomes stop advancement and permit read-only reconciliation only.

Keep VDP Safe Stop, serial VDP/Brake publication, independent Reset/history
proofs, real native postconditions, freshness and the accepted offline soak.
Reuse shared Docker without Dashboard/restart cycles. Development-Mac tests
remain unit-only. Qualification tools are separate from the installed product;
rebuild the DMG only if its actual product payload changes.

No absolute optimized-run target is promised before the split timing baseline.
Historical failures remain intact, and implementation/unit coverage alone
cannot close a native gate or produce a full-E2E PASS. New-account/token entry,
first-time OS permissions, installation repair, external notarization and main
integration retain their separate acceptance boundaries.
