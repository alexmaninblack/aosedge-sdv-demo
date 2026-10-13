<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 UI campaign comparison and acceptance

- Date: 12 October 2026
- Status: Step 5 PASS; overall runtime improvement NOT ESTABLISHED
- Branch: `codex/presenter-human-friendly`
- Target: Dedicated M1, internal storage, Aos Cloud staging

The autonomous continuous UI scenario passes the agreed functional and cleanup
criteria. Two comparable campaigns completed all 42 stages, 32 guarded Presenter
submissions, 14 native mouse inputs and nine serial publications. They took
20:10 and 20:20 respectively. Native clicks no longer depend on agent scheduling,
and independent reads use asynchronous waiting and one pinned SSH connection.
These improvements do not establish a reduction in complete campaign time.

This closes Step 5 of the [ordered optimization plan](ui-qualification-timing-2026-10-12.md).
It does not close complete installer E2E or authorize main integration. This
comparison reused retained results; no new live campaign, publication, build,
download or product change was needed.

## Comparable scope

The [Step 3 campaign](continuous-ui-campaign-2026-10-12.md) and
[Step 4 campaign](asynchronous-ui-reads-2026-10-12.md) used the same M1, installed
package, retained Test, signed native executor and ordered stage and submission
names. Both began with stopped vehicle owners, started the controller and CARLA,
retained healthy owners across the story, then exercised explicit Stop/Start
and final shutdown. Neither is a wholly warm-runtime benchmark.

New release numbers differ because each campaign published fresh test versions.
The VDP V1/V2/V3, Brake V1/V2/V3 and Tire V1 profiles and order remained the same.
The starting installed versions and accumulated persistent histories therefore
also differ. Machine load and Cloud/backend latency were not experimentally
controlled; one successful observation per source revision is not a statistical
performance benchmark.

The historical 42:22 is the sum of six attempts with failures and different
coverage, not one equivalent passing campaign. Three early harness failures
accounted for 10:06, and a later story stopped at the agent-assisted native Tire
gate. Separate continuations did not convert that failure into PASS. Keep this
history as evidence of investigation and scheduling cost, not as the denominator
for a claimed twofold speedup. The mechanical native fixture and the shorter
five-control pilot also have different scope.

## Timing comparison

Group rows sum successful browser-stage timers, including independent checks
and result settlement. They do not isolate actuator or installation latency.
Other campaign work includes preflight, VM access, bootstrap, transport/client
work between stages and final cleanup. A positive difference means Step 4 was
longer. All values are seconds; elapsed labels round to the nearest second.

| Boundary | Step 3 | Step 4 | Difference |
| --- | ---: | ---: | ---: |
| Cold vehicle startup and installed baseline, stages 01–07 | 158.986 | 160.684 | +1.698 |
| Retained runtime: serial story and Return, stages 08–15 | 476.491 | 473.966 | −2.525 |
| Retained runtime: views, Reset and cancellation, stages 16–26 | 38.153 | 31.683 | −6.470 |
| Retained runtime: moving updates and result checks, stages 27–35 | 250.072 | 262.340 | +12.268 |
| Explicit Stop/Start and preservation, stages 36–41 | 149.661 | 145.355 | −4.306 |
| Final confirmed Stop, stage 42 | 21.590 | 18.196 | −3.394 |
| Successful browser-stage total | 1,094.953 | 1,092.224 | −2.729 |
| Campaign work outside those stage timers | 115.154 | 128.057 | +12.903 |
| Complete campaign including cleanup | 1,210.107 (20:10) | 1,220.281 (20:20) | +10.174 |

Step 4 was 0.84% longer overall. The 2.729-second reduction in summed stage
timers does not prove a performance improvement. The accepted result is
functional autonomy, responsive browser waiting, fresh evidence and safe
transport reuse—not a guaranteed sub-20-minute test.

Work-session elapsed time is separate. The Step 3 development and qualification
turn took about 59 minutes, including preparation, failed starts, diagnosis,
unlocking and reporting; only 20:10 was the passing campaign. Step 4's recorded
session interval, 21:02:20–21:44:36 Europe/Berlin, was 42:16: 17:53 before the
passing campaign, 20:20 in it and 4:03 afterward. These intervals have different
development/reporting boundaries and must not be presented as scenario speedups.

## Complete ordered stage results

Each row passed in both campaigns. Native input receipts establish delivery
to the actual semantic control; fresh physical and backend postconditions in
the enclosing stage establish the real result. Short view timings establish
navigation/assertions, not new vehicle data or first-user native acceptance.

| Order | Stage | Step 3 seconds | Step 4 seconds | Results |
| --- | --- | ---: | ---: | --- |
| 01 | `open-installed-presenter` | 3.202 | 4.786 | PASS / PASS |
| 02 | `start-controller` | 54.661 | 50.619 | PASS / PASS |
| 03 | `start-simulator` | 66.883 | 67.897 | PASS / PASS |
| 04 | `connect-in-manual` | 15.671 | 16.373 | PASS / PASS |
| 05 | `restore-window-layout` | 9.123 | 10.190 | PASS / PASS |
| 06 | `visible-m1-workspace` | 0.018 | 0.021 | PASS / PASS |
| 07 | `continuous-baseline` | 9.428 | 10.798 | PASS / PASS |
| 08 | `vdp-v1` | 51.836 | 57.113 | PASS / PASS |
| 09 | `brake-v1` | 79.644 | 77.230 | PASS / PASS |
| 10 | `vdp-v2` | 44.495 | 45.524 | PASS / PASS |
| 11 | `brake-v2` | 76.962 | 80.500 | PASS / PASS |
| 12 | `vdp-v3` | 45.579 | 44.295 | PASS / PASS |
| 13 | `brake-v3` | 80.216 | 77.196 | PASS / PASS |
| 14 | `tire-v1` | 82.326 | 80.868 | PASS / PASS |
| 15 | `return-to-road` | 15.433 | 11.240 | PASS / PASS |
| 16 | `installed-details` | 0.329 | 0.363 | PASS / PASS |
| 17 | `platform-team` | 0.097 | 0.105 | PASS / PASS |
| 18 | `brake-team` | 0.097 | 0.119 | PASS / PASS |
| 19 | `tire-team` | 0.106 | 0.119 | PASS / PASS |
| 20 | `cloud-software-and-resources` | 0.243 | 0.206 | PASS / PASS |
| 21 | `brake-backend-evidence` | 0.225 | 0.248 | PASS / PASS |
| 22 | `brake-independent-reset` | 18.186 | 13.451 | PASS / PASS |
| 23 | `tire-backend-evidence` | 0.217 | 0.204 | PASS / PASS |
| 24 | `tire-independent-reset` | 13.921 | 12.221 | PASS / PASS |
| 25 | `activity-receipts` | 0.306 | 0.293 | PASS / PASS |
| 26 | `cancel-stop` | 4.426 | 4.354 | PASS / PASS |
| 27 | `moving-sota-autopilot` | 10.582 | 9.896 | PASS / PASS |
| 28 | `brake-moving-sota` | 55.502 | 51.660 | PASS / PASS |
| 29 | `tire-moving-sota` | 59.763 | 68.658 | PASS / PASS |
| 30 | `moving-sota-safe-stop` | 10.882 | 15.282 | PASS / PASS |
| 31 | `campaign-brake-moving-maneuver` | 35.961 | 34.531 | PASS / PASS |
| 32 | `campaign-brake-moving-return` | 11.726 | 15.834 | PASS / PASS |
| 33 | `campaign-tire-moving-maneuver` | 39.253 | 38.208 | PASS / PASS |
| 34 | `campaign-tire-moving-return` | 17.122 | 16.779 | PASS / PASS |
| 35 | `continuous-final-releases` | 9.281 | 11.492 | PASS / PASS |
| 36 | `continuous-stop-preserve` | 23.759 | 17.837 | PASS / PASS |
| 37 | `continuous-restart-controller` | 48.219 | 50.973 | PASS / PASS |
| 38 | `continuous-restart-simulator` | 47.808 | 48.009 | PASS / PASS |
| 39 | `continuous-restart-connect` | 12.519 | 12.668 | PASS / PASS |
| 40 | `continuous-restart-layout` | 4.242 | 4.213 | PASS / PASS |
| 41 | `continuous-restart-preserved` | 13.114 | 11.655 | PASS / PASS |
| 42 | `confirmed-stop` | 21.590 | 18.196 | PASS / PASS |

## Acceptance and closure

Both campaigns confirmed each installation before the next publication, VDP
Safe Stop, independent Brake/Tire Reset with peer/history preservation, moving
QM updates with unchanged boot/Test/VDP, and explicit Stop/Start with changed
boot, preserved state and stationary Manual attachment. All 32 Presenter action
names and their order match; cancellation submitted no Stop. Fourteen native
inputs were delivered in each run without conversational scheduling.

Both independent final inventories recorded zero owned demo processes,
listeners and qualification clients, preserved Test data and the same Docker
Engine identity. The browser and native executor closed, owned media detached
and temporary display assertions ended. Step 4 additionally confirmed closure
of its read master and active client. Normal cleanup preserved shared Docker;
no Engine restart, Test retirement or history deletion occurred.

Step 4 recorded 166 fresh reads, zero failed reads, one SSH connection and no
automatic reconnect. Aggregate transport read time was 311.551 seconds; the
browser observed 313.413 seconds of read waiting, with median 0.866 seconds.
These overlap stage timers and cannot be added to total campaign time. They
do not isolate packaged Python, guest SSH, Cloud or backend cost. The separate
expected timeout fixture verified exact-client cleanup and subsequent fresh
reads; it is not a failed request in the positive campaign.

The bounded asynchronous broker and connection reuse are accepted. Do not cache
green owner responses, reuse mutable Python owner objects, remove freshness
checks or skip cold/lifecycle gates to achieve a shorter number. Further speed
work would first need isolated read/result timing and a separately agreed scope.

## Evidence and source boundary

Comparison validation matched all 42 table rows to the stored reports, checked
the complete ordered submission names and counted nine publications and 14
native inputs per campaign. Closure assertions passed. The repeated local gates
passed 64 Python tests, 25 JavaScript tests, documentation validation (357
Markdown documents, 662 stable identifiers, 38 Mermaid diagrams) and whitespace
checks. The Python socket fixtures required the normal authorized unit-test
permissions after the sandbox refused socket binding; no product or live
scenario failure followed from that local restriction.

Private evidence roots are `.local/remote-qualification/m1-continuous-ui-20261012-r4/`
and `.local/remote-qualification/m1-async-reads-20261012-r2/`. Each retains
`campaign-report.json`, `ui/browser-report.json`, native input receipts,
`ui/pilot-report.json` and independent `final-closure.json`. Step 4 also retains
`ui/read-transport-report.json` and `work-session-timing.json`. The separate
transport proof remains in `m1-read-transport-proof-20261012/`.

| Pin | Value |
| --- | --- |
| Installed package, both campaigns | `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c` |
| Retained Test | `3bb88ede-8c78-4c1a-80b6-41264982aeaa` |
| Step 3 qualification source pin | `328779c4642d099d9ae539ac447b398b07a78c19913671adb7db30c05d2e3d89` |
| Step 4 qualification source pin | `72e6b9221b9e263ff701b6eb7c6ac39e39aeef09dee53a718b26c417bdef6ae3` |
| Signed native executor, both campaigns | `35e5f9cf6548e42ee44cc1fed7ef2eecf4f295400257c510d5098def8f48372b` |
| Preserved Docker Engine | `fa9259a6-f8b1-44e2-80ba-2ad68e9d00d6` |

Final installed versions after Step 4 are VDP 164.0.0, Brake 145.0.0 and Tire
73.0.0. Compact evidence and reusable caches remain; this comparison created
no bulk artifacts or live scratch. Credentials and browser profiles stay out
of Git. Development-Mac execution remains unit-only plus M1 orchestration.

Native Setup/WKWebView, new-account/token entry, first-time permissions,
installation interruption/repair and offline soak retain their separate
acceptance boundaries. External release/notarization and main integration are
not closed by this UI optimization receipt. Product/DMG, Factory, CARLA,
Production, video and the deferred VDP timeout remain unchanged.
