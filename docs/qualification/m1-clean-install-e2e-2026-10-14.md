<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 cleanup and installed demo testing on 14 October 2026

The M1 was cleaned and the unchanged engineering DMG was installed again.
All 118 API steps passed. The continuous visible UI campaign passed 40 stages
and failed its restart preservation check. A separate diagnostic restart and
all 15 stages of the focused visible UI restart scenario then passed on the
same preserved Test. **Full uninterrupted E2E remains NOT_COMPLETE**: those
later passes do not replace the first failure. One instrumented full UI repeat
then stopped at Brake V1 because its newly delivered window had an incomplete
source gap, despite a completed physical maneuver.

## Installation and test scope

The target was the dedicated Apple Silicon M1 with internal storage, connected
to Aos Cloud staging. The development Mac orchestrated the scripts and ran
unit tests; it did not run the installed demo or live UI qualification.

| Item | Value |
| --- | --- |
| Starting integration source | `d4a1c72d17e21123a61babed9888315ff7deaae9` |
| DMG | `AosEdge-SDV-Lab-Native-Live-20261012.dmg` |
| Bytes | `14165529112` |
| SHA256 | `5e0dbf77f6b48e9efcaee8a38b85157dd691c0bb11369f316e5919fe5fa6f719` |
| Application manifest | `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c` |
| Factory | `6.1.1-maninblack.41/main-qemuarm64` |
| Preserved new Test | `50674c94-d590-437a-8d6c-acf4d0d341c9` |

The existing verified M1 media copy was reused. No multi-gigabyte download,
CARLA or Factory rebuild, new product package, or public publication was needed.
Signing remains an Apple Development engineering preview, not notarized
distribution. Native Setup button-input and clean-first-user acceptance were
not part of this scripted installation.

## Cleanup before installation

The previous current Test was retired through the normal owner with Cloud
absence, empty Test selection, absent journal and absent overlay confirmed.
A legacy R5 VM had no Cloud identity, but its historical shutdown evidence did
not satisfy the normal Finish guard. Its PARTIAL receipt was retained; the
abandoned local experiment was disposed of separately after ownership and
absence of Cloud and Production identities were checked.

Old package stores, experimental state directories, the obsolete launcher and
an old DMG were removed before installing the selected package. This freed
`271054102528` bytes. Final housekeeping removed 19 obsolete qualification
application copies and the older Chrome 154 tool cache, freeing another
`1679798272` bytes. Total observed recovery was **272733900800 bytes**, about
273 GB or 254 GiB. Final observed free space was **340826267648 bytes**.

Current media, the newly installed package and Test, current UI tools, signed
native runner, credentials, compact reports and reusable Docker images were
preserved. Deleted old run data cannot be restored; deleted programs remain
recoverable from their retained media and source.

One Docker Engine restart was needed during cleanup because its virtualization
process retained old backend bind references after those containers had been
removed. It was an explicit host-maintenance action with zero remaining
containers, not a routine test restart. The engine identity was unchanged.
The development Mac's unrelated Docker project was untouched.

## API results

The complete 118-step API scenario passed, including fresh controller creation
and provisioning; serial VDP V1, V2 and V3 updates through Safe Stop; serial
Brake V1, V2 and V3 plus Tire V1 installation; real maneuver products and
advisory observations; independent resets with history preserved; a five-minute
offline soak, queued delivery after reconnection; ignition off and on; and
ordinary Stop and Start with retained identity, models and new products.

The scenario owned the normal actions, independent observations and shutdown.
VM access used the already authorized private test input without a human
password pause. Shared Docker stayed running during the test sequence.

## Visible UI results and restart failure

The browser and native control runner executed on the M1 with Presenter,
CARLA and Driving Control visible. The first campaign passed release delivery,
installed views, independent resets, cancellation, real maneuvers and moving
Brake and Tire QM updates. It then failed at `continuous-restart-preserved`
with `CONTINUOUS_RESTART_STATE_CHANGED`. Final `confirmed-stop` was not run
as a business stage; mandatory shutdown still passed.

That error covered several predicates but did not retain which one failed.
It therefore does not establish a VM crash, lost model, lost history, service
restart or VDP timeout. The original failure remains unresolved.

The bounded API diagnostic compared state around one further Stop and Start.
Three fresh observations confirmed a changed boot ID, unchanged Test identity,
preserved Brake and Tire model hashes and history, fresh stationary Manual
control, and all four platform services active with successful results and zero
restarts. No publication, Reset, reprovisioning or Finish occurred.

The subsequent `restart-check` visible UI scenario passed all 15 stages,
including the unchanged restart predicates, exact installed versions and final
confirmed Stop. It used the same Test and package, with no new release or Reset.
This is a separate experiment, not a continuation that qualifies the failed
continuous campaign's original baseline.

The test harness now records fixed Boolean restart predicates and offers this
bounded scenario. Deadlines, freshness checks, VDP timeout, service algorithms
and product authority were not relaxed. Product bytes did not change.

## Instrumented full UI repeat

One further full continuous campaign used the improved restart diagnostics,
the same package and Test, and its confirmed current baseline. It passed eight
stages, including VDP V1 installation, before `brake-v1` failed with
`NATIVE_UI_POSTCONDITION_FAILED`. Later release and lifecycle stages were not
run. Its signed native receipt confirms the exact Brake mouse input, and the
retained source-owner result confirms a new completed Brake exercise with
physical Stop, matching run and operation identities, and no no-op.

A bounded backend-only diagnostic read the retained window through the normal
API. Brake release `153.0.0` produced window
`7b44daf1-651b-4123-8ad4-e9e97ca1cd6c`, beginning at 08:48:48.595 UTC. All
seven chunks were durably received, but its terminal state was
`INCOMPLETE_SOURCE_GAP`. The test correctly excluded it from complete products.
Pagination did not hide a successful result: the backend held only three raw
windows, and the other two complete windows belonged to older releases.

This establishes an invalid input window, not a missing UI click or missing
backend delivery. It does not establish whether the interruption came from
scheduling, timestamp coherence, transport or another source condition. The
VDP timeout remains deferred, and no timing or quality rule was relaxed.

The harness now projects bounded window quality fields alongside its unchanged
complete-product projection. A completed physical exercise plus a new fully
delivered invalid window can fail promptly with its specific reason instead of
waiting for the generic deadline. This addition passed unit tests against the
observed window shape; it has not been exercised in another full live campaign.
Final targeted gates passed: **20 JavaScript and 91 Python unit tests**. Three
temporary Unix-socket fixtures initially hit the development sandbox restriction
and passed when rerun with only that local unit-test access.

A controller-only historical-log diagnostic did not retain a usable quality
projection and exceeded its graceful Stop observation budget. QEMU subsequently
exited without forced termination. After a read confirmed the original PID was
absent, the normal owner reconciled the journal to STOPPED without sending
another guest signal. This later diagnostic shutdown is separate from the
passing API and UI cleanup results.

## Timings

| Recorded phase | Duration | Result |
| --- | --- | --- |
| Removing old installations | 10.414 s | PASS after old owner disposal |
| Fresh installation and preparation | 211.232 s | PASS |
| Complete API scenario | 1681.892 s, 28 min 2 s | 118 PASS |
| First visible UI campaign including cleanup | 1351.269 s, 22 min 31 s | FAIL |
| Bounded diagnostic including cleanup | 336.273 s, 5 min 36 s | Diagnostic complete |
| Focused visible UI scenario including cleanup | 380.272 s, 6 min 20 s | 15 PASS |
| Instrumented full UI repeat including cleanup | 469.140 s, 7 min 49 s | FAIL at Brake V1 after 8 PASS |

These are script durations, not the total elapsed session. The recorded
operational window from the first retirement intent at 06:56:32 UTC to the
final closure observation at 09:10:12 UTC was about 134 minutes. It also
included resolving the legacy cleanup guard, stale Docker handles, missing
failure diagnostics and a private display helper pinned to a deleted old
package, the incomplete-window investigation and late diagnostic shutdown.
Those preparation and investigation intervals are not hidden inside the API
or UI success times.

## Final state and next check

All owned demo processes, listeners, browser and native clients, media mounts
and display assertions were closed. The two new backend containers were
retained in `exited` state, and Docker Engine remained available. The new Test,
VM disk, model data, release receipts and history were preserved.
The interrupted repeat left VDP `171.0.0` and Brake `153.0.0` at their V1
profiles, with Tire `76.0.0` retained. This is a preserved failure reproduction,
not a ready-to-show V3 capability baseline. No automatic rollback or later
release publication was substituted for the failed step.

Private receipts are retained under
`.local/remote-qualification/m1-full-e2e-20261014`, with the first campaign,
restart diagnostic and UI restart scenario in separate directories. Original
FAIL and PARTIAL receipts were not rewritten.

Before another full campaign, investigate the actual source-quality gap in one
bounded maneuver scenario rather than replaying all releases. The first restart
failure also remains open: its separate passing repeats did not identify the
original failing predicate. Native Setup input and clean-first-user acceptance
remain separate gates.
