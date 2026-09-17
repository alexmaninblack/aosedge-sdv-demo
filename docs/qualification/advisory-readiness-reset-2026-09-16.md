<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness and independent Reset — preserved Test

Status: partial qualification, 16 September 2026. Functional CLI and targeted
UI proofs passed on the preserved staging Test; no clean Factory acceptance,
full fresh UI lifecycle or final cleanup is claimed by this report.

## Scope

Staging `aws-stage.epmp-aos.projects.epam.com`, Test Unit
`42c0bf43-4eb7-44e6-8c74-f60f9959da66`, original Factory .33.
Production was not changed. Runtime/build/package actions used Demo Control;
backend Reset actions were also exercised through Presenter and observed in
the native Driving Control telemetry. The dashboard reads only Gateway/VISS.
The backend results use real vehicle signals and explicitly labelled demo
synthetic estimators, not production diagnoses.

| Artifact | Functional profile | Confirmed runtime |
| --- | --- | --- |
| VDP 70.0.0 | V3 | Installed and running from 17:49:06 UTC; 23 telemetry paths |
| Brake 49.0.0 | V3 | Native instance active, real KUKSA, backend poll connected |
| Tire 30.0.0 | V1 | Native instance active, real KUKSA, backend poll connected |

Tire's accepted first functional profile includes advisory. Release numbers
are provenance and are not used as a substitute for functional capability.

## Exact functional evidence

1. Brake warning -> CLI Reset `da889d3c-9f16-4652-af41-dbf38d55924d`
   at 17:44:44.433 UTC -> correlated Gateway CLEARED at 17:44:47.099.
   CLEAR request `6646743c-f995-5730-9b2c-38c60575e611`, sequence 594,
   unchanged producer epoch `803f6948-17ee-4bdd-912d-b8ae1ea2bdda`.
   Tire was unchanged.
2. New real Brake maneuvers yielded MONITOR and then INSPECTION_RECOMMENDED.
   The 17:46:49.789 assessment `4d83a0d3-d5d2-55c6-bda4-c4a66ad771b9`
   had score 34, 25 active braking and 12 straight qualified samples. Gateway
   applied the renewed warning with a higher sequence. No threshold change.
3. Tire CLI Reset `b5594904-3d71-472c-a63e-145430c00083` at 17:49:28.185
   was CLEARED at 17:49:30.526; sequence 405, unchanged epoch
   `80e393f6-2c89-4000-9093-7b29889eda58`.
4. Presenter Brake Reset cancellation did nothing. Confirmed Brake Reset
   completed and cleared only its native warning. Retained historical
   assessments were excluded from the new current result, not deleted.
5. Presenter Tire Reset `5277e069-2fbd-49fd-bc3b-1ed9d15767a9` at
   18:10:40.384 was Gateway CLEARED at 18:10:42.512, request
   `a8664bdc-3c03-51c7-b67a-533f69154295`, sequence 453. The native screen
   subsequently showed Brake Inspection recommended / Tire Monitoring.
6. The final real Tire maneuver completed collision-free in 13 seconds,
   260 frames, maximum 35.105 km/h. New assessment at 18:12:54.359,
   `fd2965e4-865f-5415-a00d-a468ffc2d6c1`, moved NOT_EVALUATED to
   INSPECTION_RECOMMENDED, score 69, confidence 98%, 39 samples. Gateway
   APPLIED request `7ae026ac-d5e0-5db1-8bdd-b40b89f7e400`, sequence 455,
   at 18:13:14.441. Both native advisory warnings and the corresponding
   Tire backend result were visually observed again at 18:20 UTC.

Earlier long Tire maneuvers collided at a junction and are explicitly **not**
qualified. The test maneuver was shortened to stop before the junction; its
steering amplitude is 0.3. It uses real CARLA physics, no substituted signals
and no model-threshold changes. An intermediate 0.15 run completed but did
not establish a new warning after a clean estimator reset; it is not used as
the final warning proof.

## Corrections proven during this cycle

- A valid unexpired Gateway warning takes precedence over an absent/stale
  availability heartbeat. Invalid readiness can never hide that warning.
- Availability heartbeats initially failed because the VM timestamp led the
  host by 9–10 ms. The already agreed five-second demo skew tolerance now
  applies only to that display heartbeat. Expiry remains the Gateway's own
  15-second wall/monotonic deadline; older-than-15-second and non-increasing
  observations remain rejected. No Safe Stop or warning-request window changed.
- The transient credential proof restarted its oneshot preparer; the native
  Requires dependency stopped VDP69. The proof harness omitted resuming it,
  producing PROVIDER_MARK_UNAVAILABLE_FAILED. The exact committed VDP69 was
  resumed without selector/database/manager changes. Native retry installed
  VDP70 at 17:49:06, with no new upload. This was a proof-harness fault, not a
  change to Cloud delivery or component Safe Stop semantics.
- Presenter now labels a newly submitted Reset as in progress instead of
  briefly displaying the previous command's CLEARED result as its completion.
- Bounded diagnostic output includes readiness transport and only allowlisted
  update/mount labels; secret-redaction regression cases pass.
- Final status reconciliation exposed the owned run journal's old 64 KiB
  input limit (the preserved long-run journal reached 65,723 bytes). Only
  `.run/demo-current/journal.json` now has a bounded 1 MiB read budget.
  Other JSON inputs retain 64 KiB; explicit caller limits still take priority.
  No history was deleted. After correction, VDP70 was independently observed
  active, LIVE/REPORTED_READY, with zero restarts. Presenter alone was restarted
  to load the correction; VM, CARLA and Driving Control were preserved.

## Security and transient disposition

The exact KAC time-marker read/search proof policy was restored to the saved
stock policy through `service runtime-activate test --kac-only
--kac-recovery-remove`. A second invocation was a verified no-op. The canonical
policy store was not changed, the owned recovery drop-in was removed, and no
VM/CM/SM/IAM/container was restarted by this rollback.

The same approved policy was then reactivated under its six-hour rollback
lease to preserve the working Test while the successor is built. This is
explicitly transient, not clean-image acceptance.

Current Test also retains previously inventoried transient manager capacity
binaries, VSS supplement and Provider preparer/29-scope credential proof.
The Provider executable runs from a private root-owned read-only filesystem;
global /run flags, NoNewPrivileges, rootfs and SELinux enforcement are unchanged.
Do not reboot .33 with its migrated token and old preparer without an owned
rollback. None of these live inputs may be copied into Factory .34.

## Local gates and remaining work

- Demo Control final full suite: 936 run, 16 skipped, no failures (69 seconds).
  The first rerun exposed five journal fixture call-count mismatches and a
  status test coupled to live workstation state. Fixtures were corrected and
  status collection isolated; no runtime behavior was weakened to pass.
  After the journal-budget correction, the full suite passed again. Presenter
  was reloaded and visibly confirmed current Test Online, Brake49/V3,
  Tire30/V1 and VDP70/V3; .34 appeared in the firmware catalog while the
  running Test remained on .33.
- Latest targeted gates: 34 service-input, 46 component-runtime, 8 Factory
  compatibility and 13 permission-capacity tests; Presenter backend UI 9 tests,
  typecheck and production build; full Presenter suite 135 passed;
  CARLA scenario 5 + qualification maneuver 3.
- Platform: permission storage 3 (including actual C++ 32/256 boundary proof),
  advisory transport 13, KAC Factory integration 14, VSS schema 6 passed.
- Gateway warning-precedence and heartbeat skew/expiry native suites passed.

Factory .34 completed from pinned source
`81e7e1fda991c133a7dc83188c1dcf0f966fd62e`. Three-manager 256 flag parity,
five native Factory regressions, ten KAC tests and Provider/verifier test
executables passed before image construction. Manager package QA and image
QA completed; package QA retained build-path warnings (not zero-warning QA).
No source rebuild or image retry was needed. Builder stopped cleanly.

Immutable raw image: 6,997,147,648 bytes, mode 0444, SHA-256
`fac0cccfd5c4ededaf068bbd574b0f0a83b9af1b94f1df94022fa0ca5893eeeb`.
The remote assembly and host-transfer digests matched. Artifact location is
`demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.34/`,
outside Git. `democtl image list` discovers it without issues as selector
`6.1.1-maninblack.34/main-qemuarm64`. Manifest state is deliberately
`BUILT_NOT_LIVE_QUALIFIED`; metadata availability is not boot or E2E evidence.
Original .33 and the live staging Test remain preserved.

The operator approved automatic strict Gateway onboarding in Test Provision:
close the guest source gate, restart only the local simulator group once,
enroll the real Cloud identity, confirm stationary Manual before reopening the
gate. The operator's Safe Stop remains the component installation gate.
Implementation and focused regression checks are in progress; the clean .34
UI-only lifecycle remains unqualified until the live run completes.

The clean-run retirement started through Presenter at 18:57 UTC. Cloud Offline,
deprovision and Unit/Node absence completed within the 31-second operation;
no thirty-minute queue wait was needed. Local cleanup then correctly stopped
on unrecognized newly introduced Test guest-proof receipts, followed by the
shared DNS log absent from its directory allowlist. The fix recognizes only
those exact Test receipts, preserves shared DNS/Production, and removes only
the retired Test's identity-bound VISS credentials so a new Test cannot inherit
them. Existing unknown-field and foreign-identity guards remain.

At 19:07 UTC Presenter returned to `No controller created` after the continued
Finish action. The .34 image was explicitly selected and Create controller
started through UI. At 19:09 UTC it reported `WAITING_FOR_ACCESS`; native
automation reported the Mac locked, so the VM password dialog cannot be
completed until the operator unlocks the Mac. No provisioning or new release
publication has been attempted for this new Test. This is a blocked clean run,
not a passed boot or end-to-end qualification.

Post-change local regressions: 945 Demo Control tests completed in 65.530 s
(16 skipped, no failures); 135 Presenter tests passed, and the production UI
build/type check passed. These cover source-before-membership ordering, gate
closure before internal Safe Stop, stationary Manual before reopening, exact
identity-bound onboarding, empty-vs-failed provider distinction, Test receipt
cleanup and preservation of the Production peer/shared DNS. They do not replace
the currently blocked native/UI run.

The native access request subsequently ended without input. Presenter now
shows `Create controller · PARTIAL` after 185 seconds,
`VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`, and `Continue preparation`.
Resume that existing creation after unlocking; do not create another Test or
repeat the completed retirement.

## Clean .34 UI continuation — 16 September, 22:49–23:01 UTC

After the operator unlocked the Mac and entered the one-time VM password,
the existing Create continued successfully. All live lifecycle actions below
were submitted and their results observed through Presenter/native UI:

- Create completed at 22:49:08; Start simulation at 22:52:46; initial
  stationary Manual connection at 22:53:16.
- VDP71/V1 was prepared and published before Provision; publication completed
  at 22:54:41. No duplicate upload was made.
- Provision completed at 22:56:33 in 75 seconds. Its UI trace recorded strict
  Gateway enrollment, one local simulator-group restart, stationary Manual
  reconnection, and only then role Unit Set confirmation. Test was Online.
- The native dashboard showed Manual, 0.0 km/h, both advisory states
  `Not available`. Cloud still reported baseline 0.0.0 with 71.0.0 pending.
  After the explicit native Safe Stop, the 22:59:09 Cloud observation reported
  71.0.0 installed. No guest transient patch or VM rebuild was used.
- Brake V1 preparation correctly blocked before publication with
  `SERVICE_BUILD_REQUIRED`: current source had only its V3 product export.
  The missing V1 and V2 exports were built through the existing engineering
  `democtl service build` commands from committed Brake source `d34a19a`.
  These were local prerequisite builds, not UI actions or runtime acceptance.
  UI preparation resumed after their successful completion at 23:01:06.

Full clean lifecycle acceptance remains open. The Provision receipt's generic
summary still says `no CARLA`, contrary to its detailed, accurate simulator
restart steps; correct this text before final handoff. Initial pre-Provision
simulation used the legacy display label `Unavailable`; strict onboarding
launched the reviewed runtime and displayed the accepted `Not available`.

Brake50/V1 reached publication Ready, was assigned at 23:03:09, and Cloud
reported one active instance at 23:03:18 while the native dashboard showed
Autopilot at 19.3 km/h. Service installation did not require Safe Stop.
An explicit native stop generated a real braking window; the backend UI
reported COMPLETE, 41 samples and 5/5 chunks, received at 23:03:33, VDP
contract 1.0.1. Before final completion the partial row briefly displayed
`2/null chunks`; retain this as a presentation defect, not data loss.

VDP72/V2 was observed pending in Autopilot, then installed after explicit
Safe Stop at 23:05:43. Brake51/V2 replaced Brake50 without another Deploy,
with one active Cloud-reported instance at 23:07:31. A native stop did not
produce a V2 assessment. Bounded read-only `service runtime-inspect test`
at 23:09 localized this: KUKSA TLS verified and token present; a completed
capture was rejected by the existing model as
`INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`. Intermittent source gaps also occurred;
no allocation/thread failure was reported. No model thresholds were relaxed.
The clean V2 functional assessment gate remains open. An explicit proposal
to expose the existing real Demo Control maneuvers in the backend UI is
awaiting operator approval; CLI maneuvers are not relabelled as UI proof.

VDP73/V3 was pending while the native UI showed Autopilot at 19.4 km/h.
After native Safe Stop at 23:11:12, both dashboard advisory labels became
`Waiting for service`, with Brake still V2 and Tire absent. Brake52/V3 then
replaced V2 without another assignment; at 23:13:36 Cloud reported one active
52.0.0 instance and the native dashboard showed Brake `Monitoring`, Tire
`Waiting for service`, Autopilot and 19.4 km/h. This proves independent
readiness on clean .34, not a new warning or Reset cycle.

Two presentation-only corrections were added to source during observation:
the Provision summary now discloses its possible simulator-group restart;
an incomplete window shows received chunks with `total pending` rather than
printing null/undefined. Unit operation regressions: 40 passed. Backend UI
regressions: 12 passed plus typecheck. The first new UI fixture used the
wrong wrapped format for product-window rows; the fixture was corrected to
the existing unwrapped backend projection. These text fixes have not yet
been loaded into the running Presenter.

Tire31/V1 was published and first-assigned through UI. Cloud reported one
active instance at 23:16:55, while Brake52 was retained. At 23:17:04 the
Tire backend showed OPERATIONAL/READY, real-input score 94/100, confidence
100%; both native advisory labels showed `Monitoring` in Autopilot.
Tire Reset was submitted through UI at 23:17:22 and later showed Gateway
confirmed CLEAR. A new source event at 23:17:39 yielded score 93, without
reusing the earlier result. Brake Reset submitted at 23:18:14 likewise
showed confirmed CLEAR by 23:18:28; its UI correctly waited for a new drive
result. These are reset/ack proofs without an active warning on clean .34;
they do not replace the pending warning -> reset -> renewed-warning gate.

The native external-network button was switched OFF at 23:18:43. Local
telemetry and both Monitoring states continued at 19.3 km/h. Cloud still
reported Online at 23:19:13; its Offline transition is not yet confirmed.

Follow-up UI observations closed that connectivity gate: Cloud reported
Offline at 23:20:08 (85 seconds after the switch). Native telemetry remained
LIVE with both advisory producers Monitoring. Reconnect was pressed at
approximately 23:20:22, and Cloud reported Online at 23:20:41 without a VM
restart. This is a bounded successful offline/reconnect test, not a general
claim that the historical Cloud queue defect is fixed upstream.

Park was submitted through UI at 23:21:30 and completed before 23:21:51;
Cloud was Offline, current vehicle unassigned, and .34/VDP73/Brake52/Tire31
remained visible. The updated Presenter build was loaded through its own
Reload UI button and reconstructed the parked state. Resume was submitted
at 23:22:41 on the same identity; restart qualification is still in progress.

## Resume fault, bounded recovery and remaining gates — 23:23–23:40 UTC

First Resume stopped PARTIAL at `start-test`,
`CLOUD_GUEST_CONFIGURATION_UNCONFIRMED` after 31 seconds. Preserve this as
a failed first-attempt restart, not a completed qualification.

Read-only Demo Control evidence localized two boundaries:

- `cloud_guest.apply` performs synchronous `systemctl restart aos-cm.service`
  inside a guest read with a ten-second budget. The guest journal recorded
  CM stopping with a timeout, then starting and receiving Cloud ACKs. The
  effective CM endpoint was exactly `aws-stage.epmp-aos.projects.epam.com`,
  HTTPS, with the runtime configuration projection present. No endpoint or
  certificate mismatch was inferred.
- Both enrolled VISS identities survived in their owned IAM store, while
  the SM and VDP mTLS `LoadCredential` drop-ins under `/run` had disappeared
  at reboot. SM reported `can't start launcher: job finished with status=failed`
  and repeated startup failures; VDP exited during startup. Test role and
  persistent public binding files remained present. No re-enrollment, data
  deletion, permission relaxation or image rebuild was attempted.

The UI did not offer Resume for an existing partial Resume. That presentation
guard was corrected. The stationary-Manual admission guard was also extended
to the exact current-Test Resume `restore-test-connection` phase, requiring
the completed onboarding's original Unit/Node binding and retained connection.
Other phases, identities and Production remain rejected. The runtime guest
read now includes fixed non-secret endpoint and credential-projection presence
facts to distinguish this fault without exposing credentials.

After endpoint reconciliation, only the idle Presenter was restarted to load
these corrections. `Continue Resume` was invoked and confirmed once through
UI. It reused the running VM, launched the stopped simulation group and
restored the existing selected-Unit credential projections. The UI trace
reported COMPLETED in 61 seconds at 23:37:52, same Test Online and selected.
Read-only post-recovery evidence: SM PID 3171, active, Result success,
NRestarts 0, both drop-ins present, retained enrolled leaves present,
SELinux Enforcing, complete fresh audit window with zero denials.

This is a successful bounded recovery, **not** a clean first-attempt Resume.
The initial staging bootstrap timeout and early reboot projection ordering
remain open for source correction and another restart qualification.
The native post-recovery inspection was blocked by the Mac lock screen;
no native display or new functional result after this restart is claimed.
The Test remains running and is deliberately preserved, not retired.

Checks run after these scoped changes: 54 focused Demo Control tests passed,
then the expanded 94-test source/VM/access set passed; all 139 Presenter unit
tests passed; Presenter typecheck/build and `git diff --check` passed. The
first expanded invocation had test-import-path and sandbox Unix-socket errors;
the same fixture-only set passed with its required test path/socket access,
without product changes or live VM actions.
The earlier Provision receipt and incomplete-chunk text fixes were loaded
with the Presenter restart. No new source commit/push is claimed here.

Still open: clean Brake V2 assessment; both real warning -> Reset -> renewed
warning cycles on .34; approved access to those maneuvers from UI; native
post-recovery check; corrected first-attempt restart; final UI Finish.
Ordinary Autopilot input rejected as insufficient by the unchanged model must
not be reported as a successful advisory test.

## Unlocked native check and second restart attempt — 17 September

After unlock, the retained recovery state was inspected in native Driving
Control: Test selected, LIVE, stationary Manual, both Brake/Tire Monitoring
and external network ON. This closes only the prior post-recovery display gate.

The existing Demo Control boot path was corrected without rebuilding .34:

- Queue the already-required selected-endpoint CM restart with `--no-block`;
  remove its duplicate unbounded DNS lookup. The existing two-second guest
  DNS check remains, and guest readiness does not assert Cloud Online.
- Restore SM/VDP `/run` credential projections before guest readiness using
  only retained guest material and the exact previously enrolled Test binding.
  Require matching VM, Unit, Node, leaf fingerprints, safe files and no active
  component transaction. Do not enroll, transfer new host secrets or select a
  source. Identical repetition does not restart the consumers.
- Preserve an unconfirmed restoration as PARTIAL, without an automatic retry.

All 63 focused Cloud/guest/VM/trust tests passed. The idle Presenter was
restarted through Demo Control to load the correction; existing VM/simulator
processes were untouched until the explicit UI Park.

Park submitted at 00:41:28 UTC completed at 00:41:43 (14 seconds). UI showed
Offline and Not assigned, retaining .34 and the installed versions. One
Resume submitted at 00:42:13 passed `start-test`, `start-backends` and
`start-simulation`. It stopped PARTIAL at 00:44:09 (115 seconds), in
`restore-test-connection`, reason
`SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE:test`. No Continue Resume was
submitted for this attempt.

Read-only Demo Control observations:

- SM PID 1263, active, Result success, NRestarts 0; both mTLS drop-ins and
  retained leaves present. SELinux Enforcing, complete fresh window after this
  SM start, zero denials. The initial pre-projection boot still recorded an
  earlier launcher failure; zero restarts applies to the restored process,
  not to the entire boot history.
- VDP73 remains active in slot a; its source gate is BLOCKED. A transaction
  created at 00:43:08 has operation `remove`, candidate/previous VDP73/slot a,
  phase `waiting-for-safe-stop`. It has not removed the installed version.
- CM PID 1222 is active with zero restarts after its selected-endpoint start;
  the effective endpoint is exactly staging over HTTPS. Its retained desired
  items are still VDP73, Brake52 and Tire31. Component `numInstances:0` must
  not be interpreted as a Cloud deletion: the pinned native run-request
  loader uses this value to generate component instances for matching nodes.
- The bounded redacted native chronology reports all three installed items
  starting at 00:43:08.454, then their active snapshot reaching CM at
  00:43:08.641. SM logs Stop instance for VDP/Brake/Tire at 00:43:08.642.
  CM logs `not found (instancemanager.cpp:198)` at 00:43:08.649. The first
  fresh desiredStatus arrives at 00:43:09.415, with the same three releases.
  This establishes ordering, not the exact root cause of the stop request.

The existing `component logs` projection now retains at most 80 already
redacted reconciliation events separately from the latest provider messages,
so reconnect noise cannot hide this startup boundary. All 28 targeted
component-delivery/diagnostic tests passed, including redaction and retention.
An initial read command used an unsupported `--json` spelling and exited
before any guest action; the corrected global `--output json` form was used.

Source comparison used the exact pinned upstream
[`launcher.cpp`](https://github.com/aosedge/aos_core_lib_cpp/blob/60cb83535f773762c61ac5f544b31b7b88c502e3/src/core/cm/launcher/launcher.cpp),
[`instancemanager.cpp`](https://github.com/aosedge/aos_core_lib_cpp/blob/60cb83535f773762c61ac5f544b31b7b88c502e3/src/core/cm/launcher/instancemanager.cpp)
and [`runrequestsloader.cpp`](https://github.com/aosedge/aos_core_lib_cpp/blob/60cb83535f773762c61ac5f544b31b7b88c502e3/src/core/cm/launcher/runrequestsloader.cpp),
plus the local stale-snapshot patch and systemd-slot runtime StopInstance.
No native source/binary change, Cloud mutation, transaction removal or security
bypass was made. The test remains preserved at the partial Resume boundary.
A CM/SM reconciliation scope extension has been requested. .34 is not yet
fully live-qualified; remaining functional, first-attempt restart and final
retirement gates stay open.

## Approved CM startup correction — 17 September, 03:37–03:45 UTC

The operator approved the bounded correction. The same .34 Test, overlay,
Unit and native stores were retained. Before this correction, the native
eight-minute removal wait expired with `safe_stop_timeout`; VDP73 remained
installed. No transaction was manually removed, completed or bypassed.

The read-only `component cm-status test` projection now includes bounded,
allowlisted launcher headings/counts and fixed SQLite launcher columns. The
old process loaded two active entries, then sent `stopInstances=3,
startInstances=0` at 00:43:08.642008, before the new Cloud desiredStatus.
This was a native startup decision, not evidence of a new Cloud removal.

In pinned native `Launcher::ProcessUpdate`, `doRebalance` starts from
`mForceRebalance`, but `SetSubjects` overwrote it with false for an unchanged
subject list. The resend branch could therefore stop an instance that SM had
already started while CM had not reconstructed its scheduling. The correction
combines these independent triggers with OR. No SM, IAM, update gate, Subject
authorization, Cloud or production behavior was deliberately changed.

Production-equivalent red/green proof ran through the existing Demo Control
`component cm-test test --startup-reconcile` and `cm-build` variant. The
stored-unscheduled native fixture reports an already-running instance on SM
and asserts that no startup request stops it. Original code fails on that
exact assertion; corrected code passes all 19 selected native launcher and
service-reconciliation tests. Only the launcher test and CM app were built.
The first fixture compile had a test-only enum/interface error; it did not
touch the Test. Builder sources were restored after each proof and the app
cache was rebuilt from restored sources after exporting the candidate.

Qualified transient artifact:

- Directory: `runtime-proofs/cm-startup-reconcile-20260917/proof-wfi3wx05`
  under the existing demo artifact root.
- ARM64 CM: 5,598,976 bytes; SHA-256
  `0c491e8a744458b01bf81126f99ecdab3367795f757c419b92ab338b6518da23`.
- Previous .34 CM SHA-256:
  `3fffb5b89c742c233a634246c807d74e0bbc206dc143f8222c9b8283e0d78c98`.

`component cm-apply test --startup-reconcile` installed only this fixed binary
under `/run/democtl-cm-startup-20260917`, with the installed executable's
SELinux label and verified root ownership/mode. The fixed, Test-bound drop-in
`/run/systemd/system/aos-cm.service.d/96-democtl-startup-reconcile.conf`
binds it read-only over the executable in CM's service namespace. One CM
restart retained SM and VDP PIDs and the installed record. CM PID 4831 was
active with `NRestarts=0`. The later reconciliation sent three starts and
zero stops. Two earlier `Can't load instance` headings were followed by
successful scheduling; the heading-only evidence does not establish their
underlying cause, and they are not silently classified as a Cloud fault.

The first UI continuation exposed a separate recovery-composition guard:
Resume replayed simulator start while the same manual selection operation was
still pending. That path now reuses only a live, fresh, exact-operation
Controller during the recorded Test Resume, with matching enrolled Unit/Node.
It does not clear the pending operation, fabricate a connection, start another
actor or bypass `_select`'s guest gate/mTLS checks. Wrong operation or lifecycle
still blocks. The idle Presenter alone was restarted through Demo Control.

At 03:44:14, UI **Continue Resume** completed in **9 seconds**. Presenter
showed Current vehicle Test, Online, VDP73/V3, Brake52/V3 and Tire31/V1.
Native visual inspection showed LIVE telemetry, stationary Manual at 0.0 km/h,
Brake Monitoring, Tire Monitoring and external network ON. This is a successful
continuation on the preserved VM, not a new clean reboot qualification.

Final read-only checks retained SM PID 1263 with Result success and NRestarts 0,
SELinux Enforcing and zero denials in a complete window since that SM start.
VDP73 was active/REPORTED_READY with NRestarts 0 and gate OPEN. No active
component transaction remained; the earlier timeout is retained as historical
`last-failure.json` evidence, not erased or presented as a new failure.

The exact native change and regression are packaged as
`0005-preserve-pending-startup-rebalance.patch` in the CM recipe. Local focused
Demo Control/source/lifecycle tests: 139 passed. The immutable .34 image has
not been modified; the live binary override is deliberately reboot-volatile.
An image successor and first-attempt full Park/Resume remain required before
claiming reboot persistence or closing the complete clean-run work packet.
