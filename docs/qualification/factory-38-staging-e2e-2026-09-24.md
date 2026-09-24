<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .38 fresh staging E2E — 24 September 2026

Status: continuous sequential E2E passed; separate cold recovery failed.
Test .38 is preserved for diagnosis. Image is not promoted; Finish is deferred.

## Scope and authority

The operator's continuation approves the previously requested exact retirement
of diagnostic Test .37, Unit `2737ef63-4781-4ee6-a770-52e0a01e95e0`, and creation
of a fresh Test from .38. Production, Factory .36/.37/.38, published releases,
and compact diagnostic evidence remain preserved. New signing/publication will
use a separately enumerated release set, strictly one version at a time.

Candidate identity and completed offline gates are recorded in
[the build report](factory-38-build-2026-09-24.md). Historical VDP109 SIGSEGV is
not claimed fixed. Stop on recurrence and preserve evidence.

## Execution

- 12:50:49 UTC: authoritative old-Test preflight: Online, .37 firmware,
  VDP114 installed, Brake89 and Tire48 active, no pending component/service
  update. Exact local VM and Cloud identity match the approved target.
- Presenter agrees with those installed versions and no-pending state. It
  displays retained backend results separately from current input/activity
  WAITING; stock .37 has the already documented KAC renewal restriction.
- Diagnostic/security closure receipts are present on the host before
  retirement. Production journal metadata is guarded before/after lifecycle
  operations; its remembered runtime state is not treated as a fresh probe.
- Normal Demo Control retirement12:52:26→12:53:19UTC completed in53s. Cloud
  Unit/Node absence and backend cleanup confirmed by the normal lifecycle;
  Test overlay/access/workdirs removed. Production metadata remained identical.
- Fresh create12:53:40→12:54:57UTC completed in77s; local VM
  `7072b110-0522-4400-9a6c-fec18379f628`, .38, enrolled SSH10022. Existing native
  access was available; no user password prompt was required. Guest DNS resolves
  and bridge port matches. No Cloud Unit exists yet.
- 12:57:44UTC: Enforcing; no provision marker or diagnostic core receiver,
  core pattern `|/bin/false`, pipe limit0. Provisioning IAM active, normal managers
  and VDP conditionally inactive, all results success/restarts0. No SEGV in the
  bounded journal. The three-minute audit window has one systemd-generator
  user-TTY read/write denial and three sshd→aos_var_run directory-search denials;
  this is not a zero-AVC claim.
- Simulator start completed; CARLA, Controller/Gateway and keyboard UI RUNNING,
  Current Vehicle none, as expected before provisioning. Presenter advances to
  “Prepare the platform release” and reports Not provisioned, no installed
  services, and disabled Reset controls; old results/reset receipts are gone.

## Prepared set — historical pre-publication inventory

| Package | Release/profile | Packaging checks |
| --- | --- | --- |
| VDP |115/V1,116/V2,117/V3|7/15/23 read paths,0/0/2 advisory endpoints; common reviewed runtime; no packaging problems|
| Brake |90/V1,91/V2,92/V3|Real build230cdd45; permissions6/12/15; pids24; no mock/no-telemetry/workaround flags|
| Tire |49/V1|Real build8639b575; permissions18; pids16; no mock/no-telemetry/workaround flags|

At preparation time, selected OEM certificate and destination agree on
`aws-stage.epmp-aos.projects.epam.com`. Exact signing/publication/provision
confirmation was requested for this set. No upload/assignment/provision had
been attempted at that point; the executed serial results follow below.

Operator subsequently explicitly approved this exact set and all steps of the
current Test38 E2E, including serial publication/provisioning, driving maneuvers,
independent resets, network OFF/ON and normal final retirement. Routine steps do
not need repeated confirmation. Preserve Production and all source/evidence;
stop mutations on a new unexplained failure rather than restarting around it.

### Execution authorization boundary

- Fresh preflight13:13UTC: staging OEM/SP prerequisites READY, current .38
  unprovisioned/healthy, Gateway detached, Production observed stopped.
- The execution safety reviewer rejected the combined VDP115 sign/verify/upload
  command **before process creation**, requiring exact payload/destination
  confirmation despite the operator's contextual all-E2E approval. No signing,
  upload or provisioning occurred. Do not work around this via UI or another
  wrapper. One consolidated exact-set confirmation was requested; unaffected
  read-only checks continue.
- 13:15:58UTC repeated .38 health is unchanged: provisioning IAM PID718,
  zero restarts, Enforcing, core capture off, no bounded SEGV. Only the known
  SSH directory-search denials occur in this three-minute window. Layout
  verification now has no problems and z-order VERIFIED without a restart or
  layout mutation. The earlier second accessibility window was transient;
  its exact origin remains unproved, so no product fix is claimed.
- Presenter Platform view selects V1/115 (not the highest prepared V3/117),
  shows Prepared but not Published/Installed, and does not claim a running VDP.
  This confirms that preparing the full unsigned set did not skip serial flow.

## First publication, provisioning and Safe Stop gate

- Operator reconfirmed the exact-set safety question; the command is now
  permitted. VDP115 sign/verify passed, upload HTTP201 at13:18:49UTC,
  deployment`8bafd0ee-38a5-4d56-ad5e-5ea033954698`. READY/Done authoritative
  read13:19:28; UI already offers Provision by13:19:12.
- Provision13:20:16→13:20:50UTC,33.89s: Unit
  `a6cf9e5f-5859-4302-9f8f-791d603e58a8`, Node
  `5264ac42-49a6-403b-952a-79f2294caa75`, system UID
  `7072b110052244009a6cfec18379f628`. Online/verification set confirmed;
  Gateway connects in stationary Manual without simulator restart.
- Autopilot confirmed moving13:21:38; Cloud reports installed0.0.0,
  pending115, and guest transaction waiting-for-safe-stop/provider inactive.
  This closes the previously premature-active-report reproduction on stock .38.
- Native Safe Stop approximately13:22:16; physical stop confirmed13:22:32.
  Guest active115 and Cloud installed115/no pending by13:22:35. By13:23:02,
  VDP PID2440 READY/LIVE,0restarts. IAM1748/SM2139/CM1808/KAC2185 active,
  all0restarts, Enforcing, no VDP/KAC AVC in bounded window, no SEGV.
- Autopilot resumed; only Brake90/V1 signing/publication started next.

## Brake V1 first-create and real data

- Brake90 accepted HTTP201 at13:23:44UTC, authoritative READY13:25:01.
  Normal Presenter-equivalent runtime-input preparation4.54s then dedicated
  Subject assignment7.35s completed while Autopilot was moving.
- Container/bootstrap PID2982, service2983, UID5000. KUKSA auth READY and
  CONNECTED/RECEIVING by13:26:15; no transient policy or manager restart used.
  Storage inode15, numeric storage/state quotas8192/1024KiB. Cloud has service
  CPU11DMIPS, RAM1601536bytes and states0/storages28672bytes in the first sample;
  private-network service traffic remains0 as previously explained.
- Real Brake maneuver13:26:55→13:27:11 completed in16.05s. Native service
  reports WINDOW_COMPLETED; backend/UI shows **Recording complete,76samples,
  8/8chunks**, source13:27:03/received13:27:11. V1 correctly has no condition
  estimate or advisory; Reset disabled. Prior Autopilot also produced windows.
- Isolated MIXED_TIMESTAMPS input rejections were observed and retained, not
  suppressed; service remains OPERATIONAL/RECEIVING and completes the recording.
  This is not a claim that every simulator sample was accepted.
- Only after these gates did VDP116/V2 signing/publication start. The maneuver
  left a confirmed Safe Stop, so this update may install without another stop.

## V2 installation, assessment and persistence baseline

- VDP116 accepted13:28:07UTC, READY read13:28:50, installed116 confirmed
  13:29:09; slot b,15signals,READY/LIVE,0restarts. Standard runtime-input
  preparation4.34s is a no-op. Autopilot resumed before the service upgrade.
- Brake91 accepted13:30:07, READY and Cloud active91/no pending by13:30:42.
  CARLA remained moving in Autopilot. UID5000, state inode64772 and storage
  inode15 survived; storage/state quotas remain8192/1024KiB. Bootstrap3716,
  service3717; auth READY, real input receiving. No manager restart/policy change.
- Real Brake maneuver13:31:16→13:31:31 completed in15.38s. V2 assessment
  source13:31:31.295Z received13:31:31.394Z; Presenter correctly changes from
  waiting/no current-release result to Result received/Monitor. It did not
  misrepresent the retained V1 recording as a V2 assessment.
- Pre-V3 model baseline13:36:31: generation1, recentEventCount1,
  hasAssessment=true, nextAdvisorySequence1, MONITOR; outbox empty. These are
  metadata only, not raw model/telemetry evidence. A brief KUKSA reauthentication
  readiness change recovered to OPERATIONAL13:36:16 without process restart.
- Autopilot moving confirmed13:36:56. Only then VDP117/V3 signed/verified and
  uploaded: HTTP20113:37:01, deployment9f0e875e-2ca7-48cb-ae63-91213fe73b00.
  Await actual Safe Stop/installation proof before advancing to Brake92.

## V3 Safe Stop and Brake model retention

- VDP117 READY13:37:40. While moving, Cloud installed116/pending117 and
  guest transaction waiting-for-safe-stop agree. Presenter13:37:52 displays
  one pending update and explicit native Safe Stop instruction.
- Native Safe Stop13:38:10 approximately; physical stop verified13:38:23.
  Actual117 installed13:38:11, slot a,23signals; READY/LIVE/0restarts and
  Cloud installed117/no pending by13:38:27. IAM1748/SM2139/CM1808/KAC2185
  unchanged; new VDP PID4845 is the expected update, not crash recovery.
  Enforcing, core capture off; only known SSH directory-search AVCs observed.
- Standard runtime prepare4.23s/noOp. Autopilot resumed; moving13:39:14.
  Brake92 accepted13:39:21, READY/active13:39:45. Its UID5000, state inode64772,
  storage inode15 and quotas remain unchanged. Model generation1, recent1,
  MONITOR and nextAdvisorySequence1 survive V2→V3 unchanged; identical model
  file inode36/541bytes before any V3 assessment. Bootstrap5125/service5126.
- Native UI13:39:56 shows Brake Monitoring, Tire Waiting for service; Tire is
  not yet assigned. Brief startup authorization/readiness transitions and one
  V2 Autopilot episode rejected for insufficient wheel samples are recorded,
  not treated as loss of retained analytics or a V3 assessment.

## Both services, independent Reset and Return to road

- Brake V3 real maneuver13:40:08→13:40:24 produced assessment and condition
  change to INSPECTION_RECOMMENDED. Gateway APPLIED13:40:24.343Z; backend
  assessment received13:40:24.442Z. The retained V2 assessment remains present.
- Tire49 accepted13:41:08, READY13:41:29, normal input prepare noOp then
  assignment7.55s; Cloud active49 by13:41:41. UID5001, state inode32388,
  storage inode34, state/storage quotas2048/4096KiB. Bootstrap5478/service5479.
- Real Tire maneuver13:42:15→13:42:30,14.94s: assessment source13:42:29.717Z,
  backend receipt13:42:29.813Z, Gateway APPLIED13:42:29.819Z. Both native and
  Presenter advisories show Inspection recommended. Tire maneuver also provides
  a qualifying braking episode: Brake assessment count2→3; expected real physics.
- Cloud monitoring13:42:23 source sample reports both services: Brake72DMIPS/
  4161536bytesRAM/81920bytesstorage; Tire32DMIPS/3006464bytesRAM/49152bytesstorage.
  Service network counters0 are the previously accepted private-path limitation,
  not proof of no traffic; node traffic counters are nonzero.
- UI Brake Reset clicked approximately13:43:15, CLEAR confirmed13:43:22;
  native Brake Monitoring while Tire Inspection recommended. Tire Reset clicked
  approximately13:43:55, CLEAR13:44:03. Presenter gives immediate Resetting,
  then confirmation and No new result after reset, not a false new assessment.
  Backend histories remain Brake3assessments/1event and Tire1/1.
- Return to road13:44:33→13:44:35 completed1.8s, stationary Manual, no
  model reset or identity change. Managers and service processes unchanged,
  VDP READY/LIVE/0restarts, Enforcing; only known SSH AVCs in bounded window.
- Network OFF initiated13:45:08 for the separate five-minute local-continuity
  test. Do not count this as passed until ON recovery and delivery reconcile.

## External network OFF — observations before restoration

- OFF completed13:45:10.8UTC. Backend baseline Brake3assessments/1event,
  Tire1/1; function-observation heads13:44:56.476/13:44:42.393. Re-read13:47:59
  matches all result counts/heads; function observations correctly become stale.
  Cloud authoritatively OFFLINE, no new pending versions.
- Brake maneuver13:45:58→13:46:13 and Tire13:46:13→13:46:28 completed with
  genuine local motion. New local assessments and Gateway APPLIED warnings were
  observed; native UI13:47 shows both Inspection recommended, external OFF, LIVE.
  Presenter independently shows Offline/Input not confirmed/Last known and
  disables remote Reset rather than claiming fresh backend data.
- At13:48:45, managers/provider and both service PIDs unchanged. Brake model
  generation6/recent5 and Tire recent2 demonstrate new offline processing;
  queued files Brake12 (v2=5,v3=7), Tire17. Brief reauthentication/readiness
  changes remain explicit; no claim of uninterrupted readiness. Core capture
  stays off, no bounded SEGV; no KAC/VDP AVC, known SSH denials retained.
- Twenty contract/policy tests pass (8network,8SafeStop,4rapid-debug); docs gate
  passes259documents/658identifiers/38diagrams. Initial pytest invocation ran no
  tests because pytest is not installed in the project venv; the native unittest
  runner above is the valid result. No product dependency was installed.

## ON recovery closes the continuous scenario

- ON13:50:36→13:50:39UTC; external OFF lasted approximately5m28s. Brake
  reconnect13:50:46.664 (~7.4s after ON); Tire13:51:05.548 (~26.3s).
  Cloud authoritative ONLINE at13:51:45 read; this is an observation upper
  bound, not a measured exact reconnect duration. Presenter also returns Online.
- Brake assessments3→5/events1→2 and Tire1→2/events1→2. Every assessment and
  event ID is present and unique. Source times remain13:46 while delivery times
  correctly show13:50/13:51. Queues all0 by13:51:49; both same bootstrap/service
  PIDs and all managers survive. Native warnings remain applied.
- The test proves short-outage local processing, renewal and queued recovery
  on stock .38. It does not prove thirty-minute RabbitMQ behavior or uninterrupted
  readiness: brief reauthentication/coherence rejections are still observed.
- The separate controlled guest-reboot/persistence test follows this completed
  continuous scenario; it must not be conflated with an automatic recovery restart.

## Separate guest reboot — not an autonomous recovery pass

- One graceful guest reboot accepted13:52:59UTC in physical Safe Stop/network
  ON. No repeated reboot/force reset. First SSH observation was unavailable;
  at13:54:06 boot ID changed and uptime52.84s. QEMU remains running.
- Cloud returns Online but VDP fails exit1: “VISS client certificate is
  unavailable”. SM startup consequently fails launcher initialization; native
  logs contain “terminate called without an active exception”/core-dump result.
  This is not the earlier VDP SIGSEGV. Core output remains disabled. At13:56:13
  SM has2automatic restarts; VDP13 and ongoing auto-restart, no service containers.
- Model data is retained: Brake UID5000/generation6/recent5/Inspection recommended;
  Tire UID5001/recent2/Inspection recommended. Backend histories remain5/2
  assessments and2/2events. This is not recurrence of shared-storage deletion.
- Source localization: `source_trust_guest.py` intentionally writes the SM/VDP
  `85-democtl-viss-mtls.conf` credential projection under `/run/systemd/system`.
  Direct guest reboot discards it. `VMService._start()` explicitly calls the
  existing trust-restore path using previously enrolled persistent material;
  raw guest reboot alone does not run that host-owned step. Existing unit tests
  cover reconstruction/idempotency. No new trust/persistence mechanism added.
- One normal `democtl vm start test --timeout90` reconciliation is now attempted
  to restore that established projection on the already running VM. Do not count
  it as spontaneous reboot recovery. Preserve this Test instead of Finish until
  the recovery outcome and remaining cold-start gap are classified.

## Cold recovery diagnosis and bounded restoration outcome

The following supersedes the pending restoration outcome above. These recovery
actions are explicit interventions, not an autonomous reboot pass.

1. Normal `vm start test` completed13:57:35→13:57:39UTC,4.47s. It restored the
   existing credential projections without creating identity/material. SM and
   VDP restarted through that existing helper; the normal debug-Cloud bootstrap
   also restarted CM. Post-recovery PIDs are IAM1005, CM2101, SM2142, KAC1043;
   Brake bootstrap2207/service2208 and Tire2206/2210. Reset restart counters do
   not erase the automatic startup failures documented above.
2. VDP then stayed active but NOT_READY. Bounded logs show repeated TCP
   `Connection refused`, not a rejected certificate. At14:05:03, the exact
   source gate is ABSENT while mTLS configuration is present; Gateway admission
   remains SELECTED, its identity/generation matches the journal, and the
   engineering dashboard remains connected. No new enrollment is warranted.
3. One guarded transient restoration14:05:29.310 recreated only the existing
   owned VISS route10.0.0.1:6443→16443 using the existing `allow` implementation.
   Physical Safe Stop, externalON, exact Test identity, matching selected
   admission/generation and absent gate were verified first. This does not
   alter external-network filtering, accepted identities or TLS validation.
   The rule now reads OPEN. No process restart was issued by this action.
4. That restored the Safe Stop input for an **already pending SM removal**:
   VDP stopped successfully14:05:30.056, exit0, not SIGSEGV. CM had requested
   StopInstance at13:57:39.354, before the route repair. Do not attribute this
   removal to an invented network-rule side effect or manually restart VDP
   outside its component lifecycle to hide the state.

The authoritative persistence reads locate the second lifecycle defect:

- At13:53:04 CM loaded seven active/cached rows, including active VDP117.
  Cleaning old cached versions was separate from the subsequent loss.
- At13:53:05 the desired request still included Brake92, Tire49 and VDP117.
  VDP has `numInstances=0`, the actual mainline generated-per-runtime component
  form, not an empty deployment request.
- At13:54:04, while SM was unavailable, CM balanced, removed the generated VDP
  instance and reported `node not found`. At the13:57 recovery it loaded only
  the two Service rows, then received active VDP117 from SM but classified it
  as not in the active instance list and sent the stop request.
- Read-only SQLite inspection14:11:18 confirms all three desired run requests
  still exist, including117; only the two Service rows remain in CM's launcher
  table. SM retains Brake/Tire plus factory boot/rootfs rows, but no VDP row.
  The component slot has `stopped.json` written14:05:30.067, no `installed.json`,
  no transaction and no active link. Cloud still reports117 installed, with no
  pending version. Cloud installation history is not current local execution.
- Source evidence narrows the next native regression: generated components are
  removed before regeneration in `RunRequestsLoader::CreateInstances`; startup
  `ProcessNotScheduledInstances` only examines existing active rows for empty
  node IDs. When the missing generated row is absent entirely, late SM status
  can resend the incomplete plan rather than reconstruct the desired component.
  This source reading is not yet a compiled failing regression or a proved fix.

The route and existing credential projection are restored. The Test remains
Online/externalON/Safe Stop; VDP is inactive and both advisory displays are Not
available. Brake/Tire processes, UID5000/5001, storage inodes15/34, state
inodes64772/32388, quotas and model metadata survive: Brake generation6/recent5
and Tire recent2, both retained Inspection recommended, queues0. No reset,
reprovisioning, direct database/slot edit, new release, new Factory or permission
expansion was used. Production metadata remains unchanged. Preserve this state.

Final read14:15:59UTC: the four manager PIDs above are unchanged with success
and0restarts since explicit restoration; VDP remains inactive/exit0. SELinux is
Enforcing, core receiver absent, core pattern disabled, no bounded new SEGV.
The last three minutes contain37known SSH directory-search denials, not a clean
audit claim. Isolated regression results: VM28/28, trust guest8/8, external
connectivity contract8/8 and Safe Stop contract8/8. Their passing mocks do not
cover the missing generated-component/late-SM integration case. Documentation
gate259documents/658identifiers/38diagrams and both repository whitespace gates
pass. Permanent product source, immutable images and accepted pins are unchanged;
no commit or push was made during this continuation.

## UI observations to retain

- During cold recovery both backend cards retain historical Inspection
  recommended results with advancing receipt age while clearly marking Input
  STALE/Activity WAITING. Native advisory correctly becomes Not available.
  Cloud and the platform card still show117 installed/No pending updates;
  the main CTA says Software story complete. These are different facts, but
  their combination can imply operational readiness incorrectly. Record this
  conflict; do not replace Cloud authority with guessed local statuses.
- VDP's `AUTHENTICATION_FAILED / VISS_MTLS_UNAVAILABLE` label also covers a TCP
  connection refusal in this run. The label is overly broad; there is no proof
  of a bad certificate. Keep transport reachability distinct from TLS rejection.

- Before provision, Cloud resource widgets have no samples and correctly state
  “Provision Test to observe”, but also show “unit not verified” and a fabricated
  empty0–1 chart scale. Values are not presented as measured data; the empty-state
  wording is visually noisy and should be reviewed separately, not hidden during
  this qualification.
- Native Driving Control at914x503 logical pixels places the small “Repositions
  the car; keeps models and advisory state” caption over the top of the external
  network button. Controls remain usable, but this is a retained layout defect,
  observed in both ON/OFF screenshots, outside the AosCore migration changes.
- During controller creation a stale previous layout observation briefly appears
  with an unverified warning; it clears when the lifecycle finishes. Real simulator
  layout still needs visual confirmation, not just the placement receipt.
- Native Driving Control screenshot at approximately13:00UTC confirms LIVE,
  Not assigned, Safe Stop/Stopped,0km/h, both advisories Not available; this
  matches the unprovisioned state. CARLA screenshot confirms the car is on the
  road. No operator-driving command or service Reset was issued at this stage.
- 13:01:11UTC read-only layout verification reports INCOMPLETE because CARLA
  exposes two accessibility windows (`WORKSPACE_WINDOW_COUNT:2`). One owned
  Unreal process83374 is running; its Window menu lists only one normal
  CarlaUnreal game window. Therefore a second simulator process is ruled out,
  but the extra accessibility window is not yet classified. Z-order reports
  VERIFIED independently. No arbitrary window was closed and no restart or
  layout fix was attempted; keep this observation separate from VM health.

## Gate disposition and next bounded work

| Gate | Result |
| --- | --- |
| Fresh .38 create/access, detached simulator, provision | PASS |
| Serial VDP115→116→117 and Brake90→91→92; Tire49 | PASS; actual preceding install verified before each publication |
| VDP Safe Stop vs QM service update while driving | PASS |
| Storage/UID/quotas and service Cloud resource samples | PASS |
| Real Brake/Tire input, backend results and native advisory | PASS before the separate reboot |
| Independent Reset/history and Return to road | PASS |
| ExternalOFF local inference/renewal, paused ingress, ON delivery recovery | PASS for5m28s; no30minute or uninterrupted-readiness claim |
| Guest reboot data persistence | PASS for retained models, UID, inodes and quotas |
| Guest reboot functional recovery | FAIL: volatile integration not restored automatically, then CM generated-component reconciliation removes VDP |
| Final Finish / new accepted baseline | DEFERRED: preserve failing Test; no promotion |

Next work, in order:

1. Reproduce the exact CM generated-component startup/late-SM sequence locally:
   desired117 survives, active generated row is missing, SM later reports that
   same installed component. Assert no undesired stop and correct regeneration;
   retain explicit-removal and stale/wrong-version negative controls. Only after
   that proof may a minimal migration patch be selected.
2. Close the Demo Control cold-recovery ordering gap without a new trust store:
   existing projection plus exact selected-source gate must be reconciled before
   their consumers rely on them. Autonomous raw guest reboot versus an explicit
   host recovery step needs a recorded lifecycle decision; do not silently bake
   demo identity or persistent credentials into Factory to satisfy this check.
3. Re-test cold recovery and same-version idempotency, persisted models/queues,
   fresh authorization, readiness, Safe Stop and exact negative identity/gate
   cases. Then do any necessary warm incremental build and clean qualification.
4. Treat retained UI wording/layout issues separately from this migration's
   source boundary. Finish the owned Test only after diagnostic preservation is
   no longer needed; do not erase an unexplained failing state.

Historical VDP109 SIGSEGV remains unresolved/not reproduced. Current core
capture is disabled, SELinux Enforcing; bounded final checks show only the known
SSH directory-search AVCs and no new SEGV. No permanent product fix is claimed
by the temporary route restoration or by passing the continuous E2E portion.

## Ignition recovery continuation —24 September,15:42UTC

The operator selected automatic restoration of the same retained connection:
same VM/Unit/Node/enrolled credentials, no provisioning, no CARLA reset and no
Autopilot. All evidence below concerns the same preserved .38 Test. The earlier
failed-boot observations above remain historical, not the current state.

### CM generated-component recovery

- Stock negative control reproduced the bug: desired component117 with a
  missing active row was sent a stop when its retained SM status arrived.
- Minimal patch0007 regenerates persisted generated-component requests during
  launcher startup before processing/resending the incomplete active plan.
  Intentional removal, stale version, foreign subject, absent SM instance and
  repeated startup are covered. It does not reapply desired status on every
  monitoring message and does not edit native databases.
- Native CM suite53/53 passed, including actual .38 target-toolchain gates.
  AArch64 candidate SHA256:
  `20280f7b6ab201216e4fc422709595ad9dc8f291272b76f872f5a2457e43d343`.
- At15:05:18UTC candidate CM started; retained VDP117 was READY/LIVE at15:05:29
  (~11s). CM repeat preserved the VDP process and both service processes.
  Stock CM was restored; no undesired component stop, new SEGV or changed policy.
  A second reconciled recovery at15:27–15:28 also passed and rolled back.
- Platform source contains the recipe patch and two packaging tests. Exact
  recipe application closure matches the four tested CM files. No new package
  or image has been built and stock .38 does not contain the patch.

### Host reconstruction and partial-result handling

The first autonomous prototype reboot at15:15:49UTC reached a partial restore.
SM restart waits behind CM, but its synchronous helper had a25s command timeout.
The systemd operations later completed; the host had already abandoned the
sequence before restoring the source route. It was not a new certificate or
Cloud-identity failure. The prototype also incorrectly saved a stale journal
after the nested VM operation failed, dropping its UNCERTAIN observation.
Both defects were classified; no blind reboot or restore retry was performed.
Exact route/transaction/manager state was reconciled before continuing.

The corrected path queues SM/VDP restart together once, then observes systemd
completion within65s, with an expanded enclosing SSH budget. It preserves
nested journal writes on every outcome, records only allowlisted failure
codes, rejects unchanged failed boots and rechecks identity/boot/assignment
before opening the retained route. First-create/no-VDP remains supported.
The Presenter worker probes outside the writer lock and shares the action
interlock with foreground operations and desktop placement. UI distinguishes
controller recovery from layout recovery, keeps the vehicle in Safe Stop and
does not claim full readiness from connection completion alone.

### Combined functional proof

One further graceful reboot was requested15:30:34UTC; SSH disconnected as
expected at15:30:37. New boot was observed15:31:06. The already-tested CM binary
was staged transiently under `/run`, with a bounded automatic stock rollback;
the immutable rootfs and SELinux policy were unchanged. The normal endpoint
projection activated that candidate. The isolated host candidate then completed
automatic connection recovery at15:31:47, and VDP READY/LIVE was observed by
15:31:52. This is ~78s from request including proof-only binary staging, **not**
a final product startup performance measurement.

Same-boot repeat was a no-op. Physical Safe Stop, unchanged source run and
assignment generation28, same Unit/Node and unchanged Production metadata were
verified. Stock rollback was submitted15:31:55 and subsequently observed.
Brake/Tire retained UID5000/5001, storage inodes15/34, state inodes64772/32388,
their original quotas, Brake generation6/recent5 and Tire recent2. Both retained
Inspection recommended; queues were0. Live service logs returned READY/
OPERATIONAL and backend connectivity. No Reset was issued.

15:41UTC authoritative re-read: staging Unit ONLINE; VDP117 installed with no
pending update/error; Brake92 and Tire49 active without Cloud instance errors.
VDP is READY/LIVE, source gate OPEN, exact Gateway assignment matches and the
vehicle remains physically stopped. No new credential or identity was created.

### Remaining gate: early boot input ordering

The combined proof **does not qualify a clean cold start**. Before host
restoration, VDP logged `VISS client certificate is unavailable` nine times,
giving8automatic retries; SM startup also exited with ABRT after its launcher
could not start that component. After restoration, these counts stopped
advancing. Do not reset counters to manufacture a clean pass.

The accepted early-input restoration boundary must be completed before native
consumers start. Do not solve this by weakening authentication, delaying all
native SM/container recovery behind an invented Cloud dependency, writing
credentials into Factory or suppressing the actual failures. This is the next
bounded source/proof item before package/image construction and fresh cold
qualification. Continuous-run externalOFF remains previously qualified;
externalOFF cold boot is not newly claimed here.

The host source/interlocks are implemented but the running Presenter process
has not been restarted onto them. Preserve Test .38 and the proof workspace;
do not promote .38, build a successor while this ordering gate is open, or
Finish/clean the diagnostic state. No commit/push was made in this continuation.

## Early input ordering closure —24 September,15:54UTC

The subsequent bounded proof closes the early-input source gate above. The
existing VDP store bootstrap now reconstructs only the two transient systemd
credential declarations from an already enrolled strict Test identity, before
SM starts. It validates retained binding/schema/generation, local machine and
Unit/Node identity, certificate identity and matching private keys, safe file
ownership/modes/ancestry and conflicting declarations. It neither enrolls nor
copies credentials, opens routes, restarts services, contacts Cloud or adds a
new daemon. Empty/unassigned Factory and Production are no-op cases.

At15:54:53UTC the same Test underwent one controlled consumer stop/start with
only the two verified85 runtime declarations removed. A temporary hook in the
existing bootstrap restored them before SM's credential snapshot. Native
startup completed in approximately1.2s after the consumers had stopped; SM and
VDP both had0automatic restarts and no process failure in this proof. VDP was
READY/LIVE; CM/SM/VDP PIDs were5146/5292/5318. IAM/KAC were not restarted.
Brake/Tire models, UIDs and storage/state inodes were unchanged. The source gate
remained OPEN and the car remained in Safe Stop. The temporary bootstrap hook
was removed, the restored85 declarations matched their original bytes, and
stock binaries and SELinux policy were unchanged. The only scoped fresh AVC
was the already known SSH directory-search denial.

This is an ordered-start proof on the preserved Test, **not a new-image reboot**.
The historical8VDP retries/SM ABRT above remain evidence of the original bug;
the later explicit consumer stop/start is a separate test, not a reset-failed
operation used to hide those results. Full cold-start qualification remains
mandatory on the successor Factory.

Source gates: CM native53/53, platform217 cases (215 passed,2 skipped), Demo
Control1069 cases (1053 passed,16 skipped), Presenter324 tests/32files and
TypeScript checking passed. Early projection has13 real-crypto/packaging tests
plus10 cross-checks against actual Demo Control enrollment fixtures. The unit
fixtures substitute privileged ancestor ownership only; real guest proof
exercises the deployed owner/mode/security model. No private material enters
the evidence. Current .38 remains immutable and lacks these fixes; no accepted
baseline is promoted. The known rapid-debug gates now permit the source
checkpoint, affected-package QA and one warm successor image build.
