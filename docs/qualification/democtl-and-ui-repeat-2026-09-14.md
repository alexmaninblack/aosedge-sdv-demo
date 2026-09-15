<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CLI and UI repeat — 14 September 2026

Status: **CLOSED WITH FINDINGS — Test retirement completed after recovery**.
The operator requested two consecutive complete
Test-only cycles: first through Demo Control CLI with real timings, then from
a clean state exclusively through Demo UI and native Driving Control. The
second cycle's acceptance observations must also come from visible UI, without
CLI, SSH or hidden API confirmation. Production .31 is preserved.

Factory: existing immutable `6.1.1-maninblack.33/main-qemuarm64`; no build.
The current uncommitted Studio and performance changes are under test, not a
clean-tree release. Services explicitly use synthetic data without permissions;
native service-to-KUKSA and real vehicle advisory remain excluded.

## Later operator-run follow-up: Finish with Cloud-only VDP 37

After the two cycles, the operator created a new Test from .31 (not the
qualified .33), published VDP v1 as 37.0.0 and requested diagnosis without
mutation. Cloud reported baseline 0.0.0 / pending 37.0.0 `to be installed`.
The native CM retained idle state `none` with zero desired items. A read-only
guest VISS probe observed fresh `SAFE_STOP` / `STABLE`, zero speed and full
brake. This localizes the immediate failure before receipt of the update;
it does not prove that the image selection alone caused Cloud non-delivery.

The operator's UI Finish was blocked before shutdown by the shared Park guard.
The user approved a narrow Finish correction: allow a current Cloud-only VDP
assignment when CM confirms idle/unreceived and connected Test is already
physically stopped. Park, active/unknown/failed-update protection, published
releases and Production are preserved. No force or Cloud cancellation exists.

Verification: 30 lifecycle tests, 32 simulation tests and 16 Presenter-operation
tests passed (78 total). The Presenter tests required permission to bind
temporary loopback ports; their initial sandbox denial was not a product failure.
`git diff --check` passed. Only the idle UI server was restarted to load the
correction. The operator retains control of the next live Finish; no live
retirement success is claimed for this follow-up.

The operator's next Finish passed that first guard, then exposed a separate
retained-Subject defect: the new Test had no `serviceOperations`, while the
previous cycle's two permanent `demoSubjects` correctly remained. The validator
incorrectly required equality between these key sets. It now permits the unused
subset only with confirmed identities and fresh GET-only Cloud absence proof;
uncertain/current foreign assignments remain blocked. No live binding or
Subject was changed to make the test pass.

The requested whole-flow audit also found that the UI treated every retirement
pause as an Offline wait, even before VM shutdown or after Unit deletion. The
lifecycle now preserves the exact leaf reason and the UI restricts that wait
instruction to `deprovision-test` with `CLOUD_OFFLINE`. Other phases expose
explicit remaining-step continuation through the same `demo retire` command.

| Audited path | Automated evidence |
| --- | --- |
| Cloud-only VDP, no native update receipt | Park remains blocked; Finish checks idle CM and existing Safe Stop; active/received/unknown/failed updates remain blocked |
| Retained Subjects with no service deployment | Exact unused subset is read from Cloud; no POST, fake assignment or Subject deletion; uncertain and foreign bindings reject |
| Repeat cycles with two, zero, one, zero assigned services | Real temporary local overlay create/retire logic; old operation receipts removed; Subjects, Production, factory bytes and version ledger preserved |
| Each of seven Finish phases fails once | Explicit continuation repeats the failed phase only; completed source/Cloud/local steps are not replayed |
| Empty Test backend records | Cleanup succeeds without a data-delete request; peer records/storage remain; exact containers and context are released |
| Backend response loss, interrupted unlink and stopped containers | Existing reconciliation tests pass without blind destructive retries or Docker Desktop restart |
| UI pause before stop / at Offline wait / after Unit deletion | Appropriate Refresh or Continue action; no simulator startup/publication; confirmation still required |
| Finish completed outside the browser | Open Studio returns to Create from fresh local state without submitting a new operation |

Final focused verification: **267 Python tests** passed (33 lifecycle, 39
service assignment, 34 Unit lifecycle, 32 simulation, 15 VM, 21 Test-only local
environment, 34 backend retirement, 6 backend context, 29 backend operations,
16 Presenter operations, 8 Tire product retirement). The latter includes empty
Brake/Tire product and isolated mock stores with peer data retained and no
cleanup-delete call. **21 UI tests** passed: 11 unit and 10 browser tests
with intercepted API responses, plus TypeScript/build validation. These are
automated regressions, not a new live E2E qualification. Production and the
current .31 Test were not stopped or deleted. A delayed Cloud Offline transition
can still pause real deprovisioning; it is not bypassed or represented as fixed.

The idle server was then stopped/started through `democtl ui stop` and
`democtl ui serve`. The updated live page was reloaded; Session shows enabled
Finish, while Park and Resume are disabled for this pending-update run. Only
the Session dialog was opened. Finish itself and its confirmation were not
submitted; the real Test, simulator and Cloud state remain operator-controlled.

## Cycle 1 — CLI

Direct commands run from `apps/demo-orchestrator`, timed with `/usr/bin/time -p`.
JSON output projections omit large package-file lists or synthetic sample
payloads; they do not replace commands or their prerequisites. Native vehicle
controls use their actual buttons. All first-service deployments retain
successful public-input preparation before assignment and do not overlap FOTA.

Initial Test was absent, simulator stopped, Production running. The first
create stopped at the native access dialog while the Mac was locked (187.78 s,
PARTIAL). After unlock, the same lifecycle/overlay resumed; no second VM was
created. The operator/native dialog supplied access and create completed in
94.31 s, including first console enrollment. These are not pure boot timings.

Current Test Unit: `48df9721-d1db-4291-b5ef-036a2a311fc4`.
System UID: `0e0b502a1f1c4b039c9e58ffdf1a6196`.
Node: `4768c4d2-23e5-4d63-847c-b4ea687f3109`.
Test Vehicles verification-set membership and Online were confirmed by CLI.

| Command / stage | Wall seconds | Result |
| --- | ---: | --- |
| Local status | 0.23 / 0.32 | Test absent, then preserved stopped partial Test; Production running |
| Image list | 0.06 | Existing .31/.33 metadata |
| Unchanged `vm start test` | 2.97 | Fresh SSH/DNS/role successful; no new process; previous run 5.46 s |
| VDP31/v1 prepare / sign / upload | 2.19 / 0.95 / 5.56 | One accepted Deployment Bundle upload |
| `simulation start --target test` | 44.48 | Simulator, Gateway, native controls running |
| `vehicle initialize test` | 4.31 | Stationary Manual, Test selected |
| `unit provision test` | 26.84 | Official SDK once, Online, role set; internal 25.48 s |
| VDP31 Cloud / guest reads | 1.20 / 1.98–2.47 | Cloud pending then active guest after Safe Stop |
| First public-input preparation | 4.39 | Four public files; no SM activation/restart |
| Unchanged public-input preparation | 4.68 | noOp, no file replacement; no live speedup demonstrated versus previous 4.32–4.57 s |
| Brake19/v1 prepare / sign / upload / assign | 1.09 / 3.21 / 5.61 / 8.68 | Dedicated retained Brake Subject, Test only |
| Tire14/v1 prepare / sign / upload / assign | 1.27 / 3.09 / 4.80 / 9.09 | Separate retained Tire Subject, Test only |
| Backend reads | 0.13–0.16 | Real synthetic records for this Test |
| VDP32/v2 prepare / sign / upload | 2.06 / 0.92 / 4.00 | Publish-only component successor |
| Brake20/v2 prepare / sign / upload | 1.11 / 3.12 / 4.45 | Automatic replacement, no reassignment/Safe Stop |
| Cloud runtime read | 1.02 | Online, Brake20 and Tire14 active; VDP32 installed |
| Tire15/v1 successor prepare / sign / upload | 1.12 / 3.03 / 4.65 | Automatic replacement with same accepted Tire content profile |
| VDP33/v3 prepare / sign / upload | 2.32 / 1.04 / 3.68 | 23-path profile; installed after Safe Stop |
| Brake21/v3 prepare / sign / upload | 1.14 / 3.21 / 5.28 | Automatic replacement while driving |
| Unchanged simulation start / vehicle select | 0.31 / 3.17 | Existing runtime reused |
| Unit resource monitoring | 0.80 | CPU 617 DMIPS, RAM 363311104 bytes; disk not reported |
| Brake backend stop / stopped inspect | 0.53 / 0.19 | Independent backend outage |
| Tire backend restart | 6.02 | Restored after independent outage |
| Test external network OFF | 2.24 | Packet filter only; local vehicle remains LIVE and moving |

VDP31 was pending from factory 0.0.0, then active at 02:20:20 UTC with seven
LIVE/READY paths and zero restarts. Autopilot was selected but initially
stationary; this first transition is not claimed as a witnessed moving-to-stop
test. Subsequent native observation showed 19.4 km/h. VDP31 remained active
with `waiting-for-safe-stop` during the VDP32 transition; native Safe Stop
then produced active VDP32 at 02:25:26 UTC, 15 LIVE/READY paths, zero restarts.

Brake19 records arrived by 02:22:26 UTC; Tire14 by 02:23:27 UTC. Brake20 was
Cloud-active and its backend records received by 02:26:33 UTC, without another
assignment or Safe Stop. The backend read attempted adjacent to Brake20 upload
completed in 0.13 s, but its 02:26:25 timestamp follows the upload's 02:26:23
completion: this is not a demonstrated live writer-overlap test.

Tire15 records arrived by 02:28:58 UTC. With Autopilot at 19.4 km/h, VDP33
waited for Safe Stop while VDP32 remained active. After the native Safe Stop
action, VDP33 was active at 02:30:50 UTC, slot a, PID 3969, 23 LIVE/READY paths,
zero restarts. Brake21 records arrived by 02:32:01 UTC while driving, without
reassignment or another Safe Stop. Cloud reported Online with Brake21 and
Tire15 active at 02:33:33 UTC.

Independent backend outages were exercised in order: Brake stopped, then
restored; Tire stopped, then restored. At 02:37:47 UTC Brake was receiving
new version-21 records while Tire was STOPPED. Tire restart completed before
the network test. An earlier command's tool output was lost during context
transfer; backend states were reconciled with read-only commands instead of
blindly repeating mutations. Exact timing and uninterrupted Tire receipts
during the Brake outage are not claimed from that lost output.

At 02:38:33 UTC the Test external network OFF command began. The prior Cloud
read reported Online. Native controls then showed EXTERNAL NETWORK: OFF,
Autopilot at 19.4 km/h and LIVE local telemetry. Cloud Offline transition and
recovery were observed separately; filter state is not treated as Cloud proof.
Cloud still reported Online at 02:39:38, 02:40:31, 02:41:33, 02:42:31 and
02:43:25 UTC (approximately 4 min 52 s after the OFF command began), with
unchanged `last_online_changed_at=2026-09-14T02:26:04+00:00`. A fresh filter
read confirmed OFF in 2.62 s; Tire's latest backend receipts remained at
02:38:30 UTC. **Cloud Offline was not observed within this bounded outage.**
This is a failed/unconfirmed Cloud-transition acceptance check, not proof of
an incorrect timestamp source or a specific Cloud/CM root cause. No manager
restart, reprovisioning or Cloud mutation was used to force the observation.

Network ON completed in 1.93 s. Both backends resumed without a VM/CM/SM
restart: Tire15 receipts at 02:44:22–23 UTC and Brake21 at 02:44:25 UTC.
Cloud still reported Online (1.05 s read); because Offline was never observed,
this is **not** evidence of a Cloud Offline→Online transition.
The subsequent Test-only Park completed in 15.94 s.
Resume completed in 81.60 s without provisioning. Cloud reported the same
Unit ID Online, Brake21/Tire15 active (0.90 s read). VDP33 was active after
reboot with 23 LIVE/READY paths and zero restarts (1.97 s read). Both backends
had new post-resume records by 02:46:37 UTC; reads took 0.14/0.16 s. Native
controls showed selected Test, stationary Manual, LIVE telemetry and network
ON. Complete retirement follows this preserved-identity recovery check.
`demo retire` completed in **33.02 s**: entire Test stopped, Cloud Offline and
deprovisioned/new confirmed, memberships removed, Unit and Node absence
confirmed, then owned local cleanup. There was no thirty-minute Offline wait
on graceful retirement. This differs from the network-filter outage, where
Cloud Offline was not observed; the two cases must not be conflated.

## Cycle 2 — UI only

Started after the completed CLI retirement. No CLI/SSH/hidden API observations
may be used to fill missing UI evidence in this cycle. Missing UI actions or
status are findings, not permission to bypass the interface.

The CLI cycle's final local status (0.24 s, 02:49:32 UTC) confirmed Test not
configured, simulator stopped, no selected vehicle, Production .31 running.
From that boundary onward all live operations and acceptance observations
were through the existing Demo UI tab and native UI only.

UI showed Full story, no assigned vehicle and Create controller. The factory
picker defaulted to .31; .33 was explicitly selected. Create controller and
its scoped confirmation were clicked once. At 02:51 UTC the visible UI showed
`Create controller · RUNNING` and `WAITING_FOR_ACCESS: enter the VM password in
the macOS Demo Control dialog (Cancel stops preparation)`.

The desktop UI tool reported that the Mac was locked and automatic unlock
could not unlock it. **UI-only progress is blocked on manual Mac unlock and
native access-dialog completion.** No CLI, SSH, hidden API or password
workaround was used. On unlock, UI reconciliation showed the attempt had
completed PARTIAL with `VM_ACCESS_INPUT_INVALID`, phase `start-test`, no
completed steps. A safety review rejected its confirmation; the operator
explicitly authorized resuming this same partial Create. A new native password
prompt was completed by the operator using the UI, not CLI or stored evidence.
The resumed attempt started at 02:58:47 UTC and UI Trace confirmed COMPLETED
at 03:00:17 UTC. This approximately 90-second span includes credential entry
and console enrollment, not only VM boot.

### UI-only software sequence

The following are visible UI observations, not independent guest inspection:

| UI action / transition | Visible result |
| --- | --- |
| Start simulator → Connect in Manual | Native Test selected, Manual, 0 km/h, LIVE, network ON |
| Platform Prepare v1 → Sign & publish → Provision to Test | Allocated VDP34; Test Online; Cloud installed 0.0.0, pending 34.0.0 |
| Autopilot → Safe Stop | 19.4 km/h → 0; Cloud installed 34.0.0 by 03:06:30 UTC |
| Brake v1 prepare/publish → Refresh publication → Deploy | READY 22.0.0; first dedicated Subject assignment; backend 30 messages and WINDOW COMPLETION by 03:10:35 UTC |
| Tire v1 prepare/publish → Refresh publication → Deploy | READY 16.0.0; one active instance; backend result 40/100, confidence 75%, received 03:11:28 UTC |
| Platform v2 prepare/publish while moving | Allocated 35.0.0; installed 34 / pending 35; Safe Stop → installed 35 by 03:13:42 UTC |
| Brake v2 prepare/publish | Allocated 23.0.0; replaced 22 without another Deploy or Safe Stop; active while native speed 19.4 km/h; backend assessment 38/100 received 03:14:55 UTC |
| Platform v3 prepare/publish while moving | Allocated 36.0.0; installed 35 / pending 36 while speed 19.5; Safe Stop → installed 36 by 03:17:09 UTC |
| Brake v3 prepare/publish | Allocated 24.0.0; replaced 23; backend VALID DEMO SYNTHETIC assessment received 03:19:17 UTC |
| Tire v1 prepare/publish again | Allocated successor 17.0.0; replaced 16 without another Deploy/Safe Stop; backend 40 messages and fresh version-17 result received 03:20:42 UTC |
| Cloud monitoring → Software | At 03:20:11 UTC VDP36, no pending component, Brake24 and Tire17 with one active instance each |
| Cloud monitoring → Resources | CPU 757 DMIPS; memory 362217472 with explicit “unit not specified”; resource identity `9e91bc14ac46451bb22595fe142b3538` |

Cloud does not report the VDP process state in this UI. The UI explicitly says
so; Installed is **not** claimed as an independently verified running VDP or
23-path guest read. Native telemetry remained LIVE, but that alone does not
prove VDP process state. Service Running is supported by Cloud instance state
and fresh backend receipts. All service data remains synthetic.

### UI coverage findings before recovery

- No individual backend Start/Stop controls were present in the inspected
  backend pages (Overview/Records), service pages or Session dialog. Independent
  Brake/Tire backend outages cannot be repeated UI-only with these controls.
  They were not substituted with CLI calls. Session exposes Park, Resume and
  Finish demo; native controls expose the shared external-network switch.
- During routine Cloud refresh the story briefly changes to “Cloud not
  current / Observe the current controller”; one attempt to click the prior
  “Open monitoring” story action found it had disappeared. The persistent
  Vehicle → Aos Cloud card worked. This is a visible interaction instability,
  not a failed backend operation.
- Resource memory has no verified unit in the UI and is deliberately not
  reinterpreted as bytes. CPU is displayed in DMIPS.

At approximately 03:22 UTC, external network was switched OFF using the native
Driving Control button. UI Cloud was Online before the action. The native
panel then showed OFF, LIVE and continued Autopilot movement. Cloud Offline
is being observed through the Demo UI only.

### Operator-requested Grafana side investigation

The operator interrupted the bounded UI outage test and explicitly requested
Cloud Grafana inspection to determine whether incoming keepalive/activity
really stopped. The network remained OFF; no reconnect, VM/manager restart,
Park or retirement was performed during this investigation. These Grafana
observations are a separately authorized diagnostic, not substituted UI-only
acceptance evidence for missing guest/backend controls.

Current Test identity, also visible in OEM Units: system UID
`9e91bc14ac46451bb22595fe142b3538`, Unit
`073aec7e-2361-4ca0-ac9a-2218ab009a0a`.

Grafana `aos-prod01-ws`, UID filter, 03:18 UTC to query time, returned 165 log
entries (below the 1000-line limit). The latest matching entry was the
disconnect below, not ongoing incoming traffic. A second exact connection
trace query, `5f373b1ab10c1c6d2aa6b65124df9586`, 03:21:30–03:23:05 UTC,
returned six entries. Grafana's Show context identified the last message type.

| UTC | Cloud evidence |
| --- | --- |
| 03:21:42.676 | WS `message from unit`; UMH subsequently finished unit-status processing at 03:21:43.506 |
| 03:22:08.340 | Last observed WS `message from unit`: `monitoringData`; header createdAt `03:22:08.328694Z`, transaction `5ec2cf4f-589c-4195-b16e-bc1b1d69711f` |
| 03:22:08.354 | WS logged its outgoing ACK for that transaction |
| 03:22:08.353–03:22:08.386 | UMH received/processed that monitoringData; processing time 32.502 ms |
| 03:22:50.130 | WS logged `Unit's websocket is disconnected [1006:]` for this exact Test |
| 03:32:20 | Demo UI still displayed Test ONLINE with current Cloud-read timestamp |

The UID-filtered UMH query from 03:21 UTC to query time returned 34 entries,
latest at 03:22:08.386. No later Test activity appeared in that result.
Application-message activity stopped, and WS explicitly detected disconnection.
Therefore the continuing Online badge is not evidence of a still-live WS
connection or ongoing application keepalive. Individual protocol-level
ping/pong frames are not independently evidenced by these application logs.
The downstream disconnect-event/Online-state failure boundary has not yet
been proven; this report does not assign a new root cause or claim a fix.

### UI-only recovery and preserved-identity restart

After the operator resumed UI testing, external network was restored through
the native Driving Control button at approximately 03:39:30 UTC. The button
progressed through CHANGING to ON; native telemetry remained LIVE and Autopilot
showed 19.4 km/h. No VM or manager restart was used for network recovery.
Brake backend showed 138 stored messages, release 24.0.0 and a new receipt at
03:39:42 UTC. Tire backend showed 48 messages, release 17.0.0 and a new receipt
at 03:39:39 UTC, then 50 messages with a 03:40:09 receipt. These are actual
service-to-backend synthetic deliveries, not vehicle-derived advisory.

Session → Park → scoped confirmation completed at
`2026-09-14T03:40:45.286179Z`. Expanded UI Trace reported phase PARKED and
completed steps `stop-simulation`, `stop-test`, `stop-backends`, including
physical Safe Stop before simulator detach and graceful Test shutdown.
The UI then showed Test OFFLINE, no selected vehicle, backend unavailable
with prior records explicitly marked last known, and Resume enabled.
This is a witnessed Cloud Offline observation after graceful shutdown,
distinct from the failed packet-filter Offline check above.

Session → Resume → scoped confirmation was accepted at approximately
03:41:36 UTC. UI showed Test ONLINE while the simulator was still starting;
at 03:43:07 UTC it showed Test selected and Software story complete, with no
operation running. Tire backend showed 59 messages and a new 17.0.0 receipt
at 03:43:01 UTC. Before native controls and expanded Resume receipt could be
inspected, the desktop tool reported that the Mac was locked and could not
be unlocked automatically. No fallback CLI/SSH/API checks were substituted.
After manual unlock, native Driving Control showed selected Test, stationary
Manual, 0 km/h, LIVE telemetry and external network ON. Expanded Trace showed
Resume COMPLETED at `2026-09-14T03:42:57.577408Z`, phase RESUMED, with
`start-test`, `start-backends`, `start-simulation`, `restore-test-connection`.
This is approximately 81 seconds after acceptance; UI timing, not a shell
wall-clock measurement. The receipt explicitly states no provisioning.

Post-resume UI confirmed Tire17 receipts at 03:44:31 UTC (65 messages) and
Brake24 receipts at 03:45:01 UTC (147 messages). Cloud Software showed VDP36
with no pending release, Brake24 and Tire17 with one active instance each.
Resources showed the same system UID `9e91bc14ac46451bb22595fe142b3538` and
572 DMIPS (sample 03:45:28, read 03:45:59 UTC). No independent guest process
inspection was used or implied.

Session → Finish demo → scoped permanent-deletion confirmation was issued
at approximately 03:46:20 UTC for the current owned Test only. The UI states
that Factory originals, published releases, release continuity and Production
are preserved. The operation is under observation; no repeat was issued.

### UI-only final retirement failure

Expanded Trace reported Finish demo PARTIAL at
`2026-09-14T03:47:01.141910Z`: operation `demo.retire`, phase
`stop-simulation`, `completedSteps: []`, reason
`SIMULATION_STOP_TIMEOUT:simulatorCommand`. Visible progress reached Safe Stop,
Controller/Gateway/UI shutdown and then stopping CARLA. This attempt did not
reach Test shutdown, Subject cleanup, deprovisioning, Cloud deletion or local
retirement. No successful deletion is claimed.

At 03:47:41 UTC the Vehicle page showed Test ONLINE, current vehicle unavailable
(`SIMULATION_NOT_READY`), the existing VDP36/Brake24/Tire17 cards, and
“Retirement paused — Cleanup is incomplete”. No repeat Finish, simulator
restart, publication, CLI cleanup or hidden API fallback was issued.

A read-only desktop app inventory still listed UnrealEditor as running. An
attempt to inspect its native UI timed out (`timeoutReached`); a broader UI
inventory had also timed out and reset the automation session. These are
separate observations, not proof of a particular simulator-process root cause.
The UI-only run is blocked on resolving the simulator stop failure. The partial
state is retained for diagnosis instead of bypassing the failed lifecycle step.

## Disposition before the authorized repair

CLI cycle completed, with Cloud Offline during packet-filter outage explicitly
not observed. UI-only software sequence, network recovery and preserved-identity
Park/Resume are verified within the evidence limits above. **UI final retirement
failed and the overall second cycle is not qualified as complete.** Test has
not been deprovisioned/deleted by that attempt; Production was outside its scope.

Open findings are the CARLA stop timeout blocking Finish, incorrect Cloud Online
during network loss, unavailable independent backend Start/Stop actions in UI,
and refresh-induced story-action instability. Cloud does not expose VDP process
state in this UI; KUKSA permissions and real vehicle advisory remain excluded.
No implementation change, commit or push has been made as part of these live
tests. Only this English test report was updated.

## Authorized stop-failure investigation and correction

After the UI-only failure was preserved, the operator explicitly authorized
source/log/process diagnosis and a targeted fix. This separate repair phase
uses read-only host diagnostics and Demo Control CLI; it is not retroactively
counted as UI-only acceptance evidence.

UI `reset` dispatches `demo.retire`, which calls the same
`SourceService.simulation("stop", target="test")` and `SourceDriver.stop` as
the CLI. There is no different UI simulator-stop timeout: both used one SIGTERM
and a 30-second exit wait.

The runner log confirmed vehicle/sensor destruction, Traffic Manager/world
settings restoration and clean runner exit at 03:46:30 UTC. The Unreal log
then reported SIGSEGV in `_longjmp`/`_sigtramp` at 03:46:30.993. A one-second
sample of exact owned PID 59162 at 03:52:12 showed its main thread in
`EngineFullCrashHandler` → `FMacErrorOutputDevice::HandleError` →
`HandleErrorRestoreUI`/cursor restoration; other threads were in crash-handler
allocation waits. This is an actual simulator crash/failed exit, not a frontend
request timeout or a zombie falsely counted as running.

Historical CLI logs also contain the same crash signature at 02:45:09 and
02:48:33; those reached `StaticShutdownAfterError` and exited. The successful
UI Park at 03:40:38 likewise exited after this crash. Earlier COMPLETED
receipts prove process disappearance, not a clean Unreal shutdown; that
qualification is explicitly corrected here.

The operator authorized one forced termination of only PID 59162. Its exact
command was rechecked against the current journal immediately before the
signal. This was a one-time recovery, not a new automatic force-stop policy.
`democtl simulation stop --target test` then reconciled STOPPED with the
existing confirmed physical-stop/detach evidence; no Cloud identity changed.

The bounded source correction replaces only macOS simulator SIGTERM with
native `NSRunningApplication.terminate()` addressed by the already matched
PID and verified executable path. Unreal's local `LaunchMac.cpp` implements
native Quit through `requestQuit` and a game-thread deferred EXIT, separate
from the failing signal path. Apple documents this as normal termination,
not forced termination: [NSRunningApplication](https://developer.apple.com/documentation/appkit/nsrunningapplication).
The runner still uses SIGTERM. Exit, listener and socket checks remain;
Quit refusal or timeout preserves PARTIAL without signal fallback or replay.
No new public CLI command, wrapper or Unreal/VM rebuild was introduced.

Targeted tests: 32 simulation tests and 20 lifecycle tests passed. All 16
Presenter-operation tests passed after granting their local ephemeral socket
binds; the initial sandbox run's two PermissionErrors were test-harness access
failures, not source failures. A native absent-PID probe returned ABSENT.
Live normal-Quit and resumed UI Finish verification follow below.

### Repair verification and final disposition

Only the simulation group was relaunched through existing Demo Control for
the live repair proof; no VM restart, provisioning, new image or publication
was performed. `democtl simulation stop --target test` completed in **6.43 s**.
The Unreal log records `UGameEngine::HandleExitCommand` / `Mac RequestExit`
at 04:00:48.778, then Game engine shut down and Exiting by 04:00:50.621 UTC,
without SIGSEGV. The stopped repeat completed unchanged in **0.19 s**.

The idle UI server was restarted with `democtl ui stop` / `democtl ui serve`
to load the shared Python fix. Its ephemeral Trace generation reset; previous
results remain recorded above. Only the simulator was started once more for
the live UI Finish test. This diagnostic preparation is explicitly separate
from the original UI-only run and does not turn it into a clean passing cycle.

The operator-facing Session → Finish demo confirmation started the retry at
04:05:35 UTC. UI Trace advanced beyond `stop-simulation` to
`start-cleanup-backends`, `bind-cleanup-context`, `deprovision-test`, graceful
VM shutdown and `waiting for CLOUD_OFFLINE`. The second normal-Quit Unreal log
shows RequestExit at 04:05:37.911 and Exiting at 04:05:38.906, without SIGSEGV.
Thus the corrected stop path passed both CLI and UI execution.

At `2026-09-14T04:07:17.187593Z`, UI Trace returned PARTIAL with progress
`UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE`. Its completed-step list contains the three
steps before deprovision-test. The whole Test VM was shut down, but Cloud still
showed ONLINE; no deprovision/delete/local-retirement completion is claimed.
The lifecycle receipt's generic `reason` does not repeat the child timeout,
but the exact child failure is visible in Trace progress. No additional retry,
manager restart or Cloud mutation was used to force completion.

The CARLA stop defect is fixed and live-tested. Complete retirement and overall
Cycle 2 acceptance remain blocked by the separate Cloud Offline problem.
Current Test identity/local files are retained; Production remained outside
the mutation scope. Factory originals, release continuity and published
VDP/service releases are unchanged. Source/test/document changes remain
uncommitted; no commit or push was requested for this repair.

The one-second diagnostic sample remains at
`/tmp/democtl-unreal-stop-59162.sample.txt` for the crash investigation; no raw
process sample, build artifact or secret was added to Git. The temporary native
Quit proof script was removed. No new persistent wrapper/helper was added.

### Final UI continuation after Cloud Offline

The operator subsequently reported that the Unit had become Offline and
explicitly requested completion. The Demo UI confirmed Test OFFLINE on the
fresh 06:36:59 UTC Cloud observation, with “Continue Finish” available. This
does not establish the precise time at which Cloud changed state; no continuous
Offline observation is claimed during the operator's absence.

Session → Finish demo → scoped confirmation resumed the same retirement
at approximately 06:37:32 UTC. Expanded UI Trace reported **COMPLETED / RETIRED**
at `2026-09-14T06:37:58.350321Z` (approximately 26 seconds for this continuation,
not the full interrupted retirement). Progress began at `deprovision-test`,
without restarting the simulator or repeating the completed earlier stages.
It explicitly confirmed:

- Cloud new/Offline after deprovision, while the VM remained stopped;
- Unit Set membership removal;
- Unit deletion and authoritative Unit/Node absence;
- retired identity absence before local cleanup; and
- final RETIRED state after the scoped local-data/overlay cleanup.

The visible end state is no assigned vehicle, empty service cards, no installed
VDP Cloud report, an enabled factory picker and Create controller. Ordinary
run history is cleared (`Trace · 0`), but opening Trace still exposes the final
COMPLETED receipt and its expanded steps. No CLI/SSH/hidden API verification
was substituted in this continuation.

The current Test has now been deprovisioned/deleted and its owned working data
retired; Production was not targeted. Factory originals and published releases
and version continuity were preserved by the scoped Finish contract. The
reported UI lifecycle is complete after repair/recovery, **not an uninterrupted
all-green UI-only cycle**: the original CARLA failure, authorized repair phase,
delayed Cloud Offline behavior and other coverage exclusions remain recorded.
No additional source changes, commits or pushes were made for this final
continuation; only this report was updated.
