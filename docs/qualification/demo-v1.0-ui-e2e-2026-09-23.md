<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo v1.0 — fresh UI-led end-to-end run, 23 September 2026

Status: **CONTINUOUS FUNCTIONAL CYCLE THROUGH OFF/ON COMPLETED WITH FINDINGS;
TEST RETAINED; FINISH NOT RUN**. This is not a clean full-qualification claim.

## Outcome at 13:14 UTC

- The authorized staging releases were published strictly sequentially, with
  installation and behavior checks before advancing: VDP106/107/108
  (V1/V2/V3), Brake84/85/86 (V1/V2/V3), Tire47 (V1).
- Create, simulator startup, Provision, all version transitions, real Brake
  recordings/assessments, Tire assessment, local advisories, independent
  resets and six-minute external-network OFF/ON completed. VDP installation
  used explicit Safe Stop; Brake container upgrades proceeded while driving.
- This was UI-led, with one explicit CLI prerequisite build and bounded
  read-only diagnostics. It was not a claim of a completely UI-only build.
- Final observed Test is Online, VDP108/V3, Brake86/V3 and Tire47/V1 active,
  no pending updates, network ON and Autopilot driving. Production unchanged.
- Two findings remain open: missing Brake resource telemetry due to guest SM
  quota parsing, and one transient native motion-label inconsistency. Minor
  loading/pending-update wording observations are also recorded below.
- Preserve the running Test and backend history for diagnosis. Finish,
  deprovisioning and deletion have not been attempted in this run. No Factory
  promotion or complete P8 acceptance follows from these results.

## Scope and baseline

The operator requested a fresh end-to-end run after the published `demo-v1.0`
checkpoint and cleanup. Source starts at integration `58dd619` (the source tag
is `3ed04d7`; the additional commit only records completed cleanup). Dependency
revisions are the tagged workspace manifest. Factory remains `.36`; no image
or software rebuild is planned merely to start this run.

Use Presenter and native Driving Control for scenario actions. CLI use is
limited initially to starting the local UI server and read-only diagnosis.
Confirm staging and the selected OEM/SP context before any Cloud mutation.
Production, Factory originals and private film materials are excluded.
Any irreversible Finish confirmation is handled at action time. Preserve a
failed or uncertain operation; do not blindly resubmit or reprovision.

## Planned continuous operator sequence

1. Session/Cloud prerequisites; empty Test; Factory `.36`.
2. Create controller; start the local simulation detached, preserving the same
   scene/processes through subsequent Provision.
3. Prepare VDP V1/V2/V3, Brake V1/V2/V3 and Tire V1; record exact candidates.
4. Sign/publish VDP V1, Provision to Test, confirm Cloud Online and attachment,
   then Safe Stop and actual VDP installation.
5. Brake V1 publication/deployment, real maneuver and complete recording.
6. VDP V2 through Safe Stop; Brake V2 while driving; real assessment.
7. Early Tire V1 installation; truthful waiting for missing VDP V3 inputs.
8. VDP V3 through Safe Stop; automatic Tire recovery without redeployment;
   Brake V3 update, real results and both native advisories.
9. Independent Reset Driver Advisory, new results, Manual/Return to road and
   explicitly selected subsequent Autopilot.
10. External network OFF for at least five minutes: backend ingress stops,
    local inputs/analytics/advisory and authorization continue; ON restores
    Cloud and drains queued products without false duplicate/lost claims.
11. Readiness through token renewal, Cloud resource/detail checks, final Finish
    subject to exact confirmation; preserve originals and release continuity.

Guest/CM restart, host sleep/lock and the full calibration/negative matrix are
separate engineering checks, not silently treated as passed by this cycle.

## Measurement method

Record UTC click and UI observation timestamps. Observation intervals are upper
bounds, not internal product latency. Separate operation receipt duration,
Cloud installation, source event time, backend receipt time and native vehicle
confirmation. Record old/new status regressions and cross-surface differences.
No telemetry substitution, model threshold change or UI implementation change
is part of this observation phase.

## Preflight observations

- Integration tracked state was clean before this run record.
- No named QEMU/CARLA/Driving Control/Presenter runtime process or listener on
  port18080 was found; existing browser tab reported site unreachable.
- Local Test overlay was absent at the source checkpoint; do not infer current
  Cloud absence from that local observation.
- Approximately237 GiB disk space is available; warm engine/Builder caches and
  current/rollback packages survived the previous cleanup.

## Execution and findings

- UI server started from the existing installed orchestrator. The old browser
  error tab could not be inspected because its generated data URL was rejected
  by the browser tool; a normal new tab at the already-authorized local HTTP
  address loaded successfully. This is a browser harness issue, not a demo
  lifecycle failure.
- Session confirms selected Cloud and OEM certificate domain both equal
  `aws-stage.epmp-aos.projects.epam.com`. The initial certificate read briefly
  shows `Not available` plus `An operation is in progress`; it then resolves
  successfully. Record as loading-copy ambiguity, not invalid credentials.
- Check Cloud setup clicked11:58:21.141UTC; UI reports last checked11:58:22.
  Full READY result observed11:58:44.569: OEM, Default fleet, arm64, one-node
  model/config, node type, Test verification set, SP and OEM/SP association.
  No Prepare Cloud mutation was needed.
- Create controller `.36` confirmed once11:59:42.031UTC. First post-click state
  shows ACCEPTED; View progress shows the running operation and console wait
  after11s. The progress dialog is not empty during first Create.

- Create completed at12:00:58UTC, receipt duration76s. Post-operation Vehicle
  correctly reports Not provisioned and offers Start simulator. No password
  handoff or repeated submission was required.
- Start simulator confirmed once12:05:01.337UTC. Immediate UI acknowledgement;
  progress at14s names CARLA startup.

- Start simulator completed12:05:48UTC, receipt47s. Native Driving Control
  displays Not assigned, Safe Stop/0km/h, both advisories Not available.
  Local process baseline: QEMU82216; Unreal83672; desktop Presenter84088.
- UI Prepare succeeded for VDP V1=106.0.0, V2=107.0.0, V3=108.0.0.
  These are local unsigned candidates, not Cloud publications.
- Brake V1 Prepare correctly blocked immediately with SERVICE_BUILD_REQUIRED.
  The current clean source checkpoint lacks exact-revision compiled exports.
  UI explains engineering setup is needed and no upload/assignment started.
  An explicit engineering prerequisite build used the normal service.build
  command, not a hidden UI substitution: Brake V1/V2/V3 and Tire V1 completed
  with ARM64 ELF and product test proof on current committed revisions,
 12:14:11–12:15:28UTC. Factory and guest were unchanged. UI Prepare V1 was
  retried only after that proven prerequisite changed.
- Operator reiterated sequential publication: publish one profile, observe
  actual installation and its behavior, only then publish its next version.
  Local preparation/build is separate. No bulk version upload is permitted.

- All unsigned candidates now observed in UI: VDP106/107/108(V1/V2/V3),
  Brake84/85/86(V1/V2/V3), Tire47(V1). No publication has occurred.
  Exact selected-certificate/staging/current-Test publication authorization
  was requested as one group; execution remains strictly sequential.
- Before Provision, Tire detail truthfully says current identity is not
  observed in Cloud and no vehicle data is expected before setup. It does not
  mislabel an empty new run as lost or incomplete history.

## Receipt durations (not browser/tool latency)

Read-only reconciliation of the existing UI operation receipts found no active
or uncertain command at12:22UTC. Durations below derive from server accepted /
finished timestamps; UI observation gaps are not counted as operation time.

| Operation | Start UTC | Finish UTC | Duration |
| --- | --- | --- | --- |
| Cloud setup check | 11:58:21.161 | 11:58:22.445 | 1.28s |
| Create controller | 11:59:42.046 | 12:00:58.295 | 76.25s |
| Start simulator | 12:05:01.355 | 12:05:48.764 | 47.41s |
| Prepare VDP106 | 12:07:24.765 | 12:07:26.924 | 2.16s |
| Prepare VDP107 | 12:09:56.985 | 12:09:58.847 | 1.86s |
| Prepare VDP108 | 12:11:19.694 | 12:11:21.911 | 2.22s |
| Brake missing-build rejection | 12:12:46.435 | 12:12:46.487 | 0.052s |
| Prepare Brake84 after build | 12:18:10.996 | 12:18:12.167 | 1.17s |
| Prepare Brake85 | 12:19:22.537 | 12:19:23.435 | 0.90s |
| Prepare Brake86 | 12:20:36.376 | 12:20:37.263 | 0.89s |
| Prepare Tire47 | 12:21:31.576 | 12:21:32.425 | 0.85s |

- Operator approved the exact seven releases, selected OEM/SP credentials,
  staging, Provision and assignment only to this Test, explicitly one version
  at a time. No irreversible Finish deletion is included in that confirmation.
- UI explicitly reselected VDP V1/106.0.0 before Sign & publish. Confirmation
  names staging, selected OEM authority and release106.0.0. Command submitted
  once at12:24:53.471UTC. VDP107/108 and all services remain unpublished.

- VDP106 publication completed12:24:57; Provision submitted12:25:42.405UTC,
  completed12:26:18, receipt35s. Native panel selects Test in stationary Manual;
  same QEMU82216, CARLA83672 and Presenter84088 processes survived. CARLA scene
  remained unchanged visually. Controller process identity not yet separately
  recorded, so do not claim its PID proof from the others.
- Before Safe Stop, Platform correctly shows Cloud installed0.0.0 and pending
  106.0.0. Minor wording ambiguity: disabled publish helper says "Another
  component update" although the selected106 is exactly the pending update.
- Native Safe Stop clicked12:27:19.220, confirmed visually. Cloud-installed
  106.0.0 observed12:28:03, pending cleared; next action Open Brake v1.
  The observation interval is an upper bound, not measured activation latency.
- Brake V1/84.0.0 selected explicitly. Sign/publish confirmation names staging,
  selected SP authority and exact release. Submitted12:28:58.920UTC; no BrakeV2
  or V3 publication and no VDPV2/V3 publication has occurred.

- Brake84 publication READY observed12:29:36. First Deploy clicked
 12:29:58.718; Cloud active84.0.0 observed12:30:33. Autopilot clicked
 12:30:13.316; native19.3km/h/MOVING confirmed.
- Brake input RECEIVING; natural Autopilot episode produced a complete V1
  window:60samples,6/6chunks,PRE30/ACTIVE10/POST20,zero missing indices,
  source12:30:41,received12:30:47. Real speed/brake charts visually verified;
  the V1 page explicitly says no condition estimate and ACK not supported.
- Scripted Brake maneuver clicked12:31:41.092. RUNNING and later complete
  Safe Stop observed. Its new recording is complete76samples,8/8chunks;
  source12:31:48,received12:31:56. No threshold or telemetry substitution.
- V1 result gate passed before proceeding. Autopilot resumed. VDP107/V2
  publication submitted12:33:46.238; native19.3km/h confirmed during publication.

- VDP107 Pending while installed106 and native Autopilot19.3km/h verified.
  Safe Stop clicked12:34:50.281; installed107 and pending cleared observed
 12:35:12. Native Safe Stop/0km/h confirmed. Autopilot resumed before next step.
- Brake85/V2 publication submitted12:35:57.028. Native19.4km/h confirmed
  during this update; no second Deploy and no Safe Stop for the container.

- Cloud active85.0.0 observed12:36:55 without another Deploy. Backend before
  the new episode shows RECEIVING, no result for85 yet, earlier results in
  Records; old V1 output was not relabelled as V2.
- V2 maneuver clicked12:37:27.817. New assessment MONITOR40/100,
  quality VALID_DEMO_SYNTHETIC (demo model contract), source/received12:37:44,
  observed12:37:55. Local advisory correctly remains unavailable without VDPV3.
- **Finding UI-02:** one native screenshot during scripted V2 maneuver shows
  speed30.0km/h with SCENARIO/STOPPED simultaneously, while throttle0/brake50%.
  Subsequent completed frame is consistent Safe Stop/0km/h/STOPPED. This is
  an observed transient display inconsistency; source/capture cause remains
  unclassified. Do not infer the car truly stopped at30km/h or call it fixed.

- Tire47 published12:40:00.700; READY observed12:40:27. First Deploy
  submitted12:41:02.360; Cloud active47 observed12:41:52. Software detail
  correctly says VDPV3 required / VDPV2 installed. Tire backend has recent
  contact and CURRENT function report, but input STALE/SOURCE_GAP, no product
  result and waiting for fresh input. No false Good or local version claim.
- VDP108/V3 publication submitted12:43:25.744. Pending108 / installed107
  verified with native Autopilot19.3km/h. Safe Stop clicked12:44:33.369.
  No Tire redeployment and no BrakeV3 publication yet.

- Cloud installed108 / no pending observed12:45:14. Native Tire Monitoring
  and Brake Waiting for service correctly distinguish platform availability
  from the still-installed BrakeV2. Tire backend subsequently RECEIVING,
  current source12:45:38, no result yet while stationary. Same Tire47 with no
  new Deploy; temporary Service ACK REAUTHENTICATING is displayed separately.
- Autopilot resumed. Brake86/V3 publication submitted12:47:04.979, only after
  the earlier V2 assessment and VDPV3 installation gates. No second assignment.

- Brake86 active observed12:47:45; native Autopilot19.3km/h, both Monitoring.
  BrakeV3 maneuver submitted12:48:17.825. Backend initially shows current
  episode ACTIVE/no new86 result (earlier V2 result not relabelled), temporary
  ACK UNAVAILABLE; then new34/100 INSPECTION_RECOMMENDED source12:48:33,
  received12:48:34, ACK CONFIRMED by12:48:57. Native warning matches.
- Tire maneuver submitted12:49:13.442. Tire result67/100/confidence100%,
  source and received12:49:27; ACK CONFIRMED and both native warnings verified.
  Tire detail briefly has1queued despite the latest result already received;
  queue scope is separate from latest-result delivery, not classified as loss.
- Vehicle overview reports exact installed versions/no pending updates and
  both real results. Resource history initially loads without claiming zero;
  then CPU768DMIPS and RAM383.69MiB with sample age are visible.
- Tire Reset Driver Advisory clicked on main card12:50:58.722. One-click
  submission, no service-name re-confirmation. UI explicitly waits for Gateway
  CLEAR; no immediate false success. Peer Reset temporarily disabled while busy.

- Tire CLEAR confirmed12:51:00; native Tire Monitoring with Brake warning
  preserved. Overview truthfully says no new result after reset; history remains.
- Repeated Tire maneuver clicked12:52:14.194; main cards again show a new Tire
  warning/result, while last reset remains explicitly timestamped.
- **Finding monitoring-01:** Resources CPU/RAM shows current node and Tire
  samples, but Brake has no samples in the last five minutes despite Cloud
  active86 and demonstrated inputs/results. Disk and network service scopes
  likewise list only Tire. Root cause (Cloud report vs query/filter/adapter)
  not yet classified; do not claim this surface fully passes.
- Disk units correctly show used Aos partitions, e.g. states135KiB,
  storages400KiB,var70.14MiB,workdirs623.75MiB, not physical capacity.
  Service rows use B/KiB. Network explicitly documents accounting-day volume,
  not rate, with local/private traffic excluded; no "unit not specified".
- Brake Reset submitted12:54:17.106 while Tire warning is retained.

- Brake CLEAR confirmed12:54:21. Native Brake Monitoring/Tire warning verifies
  peer independence. Return to road from stationary Manual submitted
 12:56:14.390; outcome On road/stationary Manual, no implicit Autopilot and
  same advisory states. This is not an off-road/collision negative-matrix proof.
- Read-only monitoring API confirms missing Brake is already absent from the
  normalized Cloud monitoring response, not merely a hidden graph: node and
  Tire rows exist for CPU/RAM/disk/in/out, Brake rows absent. Adapter code
  preserves metric samples, no team-specific filter in this normalization.
  Exact upstream cause still unclassified; preserve current Test evidence.
- Explicit Autopilot resumed. External network OFF clicked12:57:39.207,
  native OFF confirmed with19.4km/h/MOVING and local advisory. Brake offline
  maneuver submitted12:58:36.113 after its independent reset. Cloud OFFLINE
  observed12:58:45; controller graphs correctly mark retained samples Last known.

The following section completes the planned OFF/ON observation; findings and
remaining gates are summarized at the end.

- Offline Brake maneuver produced a new native Inspection recommended after
  its earlier CLEAR. Backend12:59:55 still says no result since Reset; last
  source/receipt remain12:57:25, both before OFF. Function report is LAST KNOWN,
  input/activity/delivery Not confirmed rather than falsely live. Tire offline
  maneuver submitted12:59:40.213; native warnings remain available afterwards.
- **monitoring-01 narrowed:** read-only SSH finds SM repeatedly reading Brake
  CPU/RAM successfully then failing whole instance monitoring with
  `can't parse quota output (monitoring.cpp:216)`. Tire metrics succeed in the
  same cycles. This is guest SM quota parsing, not Presenter chart rendering.
  No policy/state/source changes or restart were used to diagnose it. SM/CM/IAM
  active with NRestarts=0 and activation timestamps from original Provision.
  Preserve this running Test for further exact quota/parser investigation;
  do not erase evidence through an unapproved Finish.

## Reconnect and delayed delivery

- External network ON clicked13:03:40.748UTC, after6min1.541s OFF. Native
  ON/Autopilot18.2km/h and both local warnings were observed.
- At13:03:57 Brake reports RECEIVING with function source13:03:43,
  received13:03:46, but still RETRYING/15queued and no new result. The UI does
  not conflate restored contact with completed backlog delivery.
- By13:04:56 Brake reports IDLE/0queued, ACK CONFIRMED and a new
  INSPECTION_RECOMMENDED32/100 assessment: source12:59:56 while OFF,
  received13:03:56 after ON. These separate timestamps prove delayed delivery
  of an offline-created product, not merely refresh of a cached result.
- Cloud ONLINE observed13:05:32 with the same installed releases and no
  pending update. Tire at13:05:44 reports RECEIVING, IDLE/0queued and
  ACK CONFIRMED. SM/CM/IAM remain active with NRestarts=0 and original
  Provision activation timestamps; no guest runtime restart was used.
- The current-Test Tire assessment history was read through the local
  backend's supported read-only endpoint. Three retained offline-created
  assessments have DURABLE_ACCEPTED receipt after reconnect:

| Tire source time UTC | Backend receipt UTC | Service release |
| --- | --- | --- |
| 12:57:45.295 | 13:04:14.783 | 47.0.0 |
| 12:58:34.543 | 13:04:15.641 | 47.0.0 |
| 12:59:54.454 | 13:04:15.955 | 47.0.0 |

The same burst includes an online-created13:04:00.185 assessment received
13:04:15.943. Receipt order differs from source order; those times must not be
substituted for one another. This read confirms representative retained
offline products and an empty reported queue, not an exhaustive exactly-once
reconciliation of every generated message.

- At13:13UTC the overview remains Online/VDP108/Brake86/Tire47/no pending,
  both service inputs RECEIVING. Native screenshot shows Autopilot19.3km/h,
  Brake Inspection recommended and Tire Monitoring. The latest Tire backend
  estimate is Good; earlier warning evidence remains in history.
- Read-only evidence collection initially used a malformed jq projection;
  it was corrected without any mutation. The Presenter's bounded latest-ten
  read no longer contained the reconnect burst; the backend's supported
  limit100 read did. Neither condition is a telemetry-loss finding.

## Open findings and follow-up order

| ID | Evidence and impact | Next bounded action |
| --- | --- | --- |
| monitoring-01 | Brake resource rows disappear after V1-to-V2. Follow-up below finds CM skips quota setup for the new UID when limits are unchanged; `quota` returns none and SM suppresses whole-instance monitoring. Node/Tire remain observable. | Preserve this Test; add a same-identity/new-UID quota regression and prove the scoped correction before any image rebuild. No fix applied. |
| UI-02 | One scripted-maneuver screenshot shows30.0km/h and SCENARIO/STOPPED together. The completed stationary frame is consistent. | Correlate motion-label and speed sample timestamps and reproduce under a maneuver; distinguish snapshot/render timing from control-state error. |
| copy-01 | Initial Session certificate load briefly says Not available while an operation is in progress, then resolves. | Consider explicit loading wording; not a credential failure. |
| copy-02 | Selected pending VDP release is described as Another component update. | Distinguish the selected pending release from a different pending update. |

No source/runtime fixes, policy changes or diagnostic overrides were applied.
Only this qualification record was added; normal compiled service outputs,
approved release packages and the current Test are retained outside Git.
No cleanup, commit or push is part of this run's completion statement.

### Unexecuted or incompletely evidenced gates

- Finish/deprovision/delete: not run; exact action-time confirmation and
  release of diagnostic preservation are still required.
- Local authorization remained operational across the OFF interval, but
  renewal events were not independently counted/correlated; do not claim a
  fully instrumented token-renewal proof.
- Queue empty plus representative delayed records is not an exhaustive
  no-loss/no-duplicate message-ID audit.
- Return to road was tested from stationary Manual, not from an actual
  off-road/collision position. Occupied-placement/busy/uncertain cases and
  interrupted-capture/discontinuity proofs remain outside this run's evidence.
- CM/VM restart, host sleep/lock, independent model calibration and a fresh
  security/AVC acceptance matrix were not run and are not marked passed.

## Follow-up: Brake monitoring scope and native motion display

The operator requested confirmation whether monitoring-01 also affects Tire,
and authorized investigation/correction of UI-02 on23September.

- Current Cloud samples at13:29:51UTC contain Tire CPU/RAM/disk/in/out rows,
  with no Brake rows. A later retained sample at13:35:41 has the same scope;
  the latter read is marked STALE, not falsely claimed fresh.
- A bounded SM journal count since13:34UTC finds6 Brake instance monitoring
  errors,0 Tire errors,0 other-instance errors and6 quota-parse errors. The
  observed failure is Brake-only in this Test. This is a shared SM code path,
  not proof that Tire can never encounter the same parser failure.
- Native motion diagnosis used two additional real Brake maneuvers, beginning
  13:32:22.638 and13:36:08.820UTC. Observed states include19.7km/h with
  SCENARIO/MOVING, then0.0 with SCENARIO/STOPPED and terminal
  SAFE STOP/STOPPED. Neither run reproduced30km/h/STOPPED.
- Telemetry acceptance and drawing execute on the main queue. Both displayed
  speed and motion derive from the same accepted sample; motion is not copied
  from the separate engineering Safe Stop projection. The current-source
  optimized build's entire Mach-O `__TEXT,__text` section matches the installed
  binary (SHA-256
  `464885ffa50b7b5f0b46d9e61b89b8fa1f52d53d15964e69974d5f8483fd3582`).
  An outdated executable is therefore not supported as the explanation.
- Added `tests/native_motion_status_test.py` in carla-ego-runtime and registered
  it with CTest. It compiles the production TelemetryView in an isolated
  optimized Swift harness, creates no window and touches no live telemetry.
  20000 accepted sample transitions plus missing/non-finite/reset/stale/
  rejected-input cases pass. All6 native Python-discovered tests pass; the
  registered CTest `native_motion_status` separately passes1/1 in5.66s.
- UI-02 remains an **unconfirmed display/capture observation**, not a proven
  product defect or a fixed issue. Current evidence does not justify changing
  movement thresholds, control state, source telemetry or the rendering logic.
  A future recurrence needs contemporaneous frame/render evidence. No native
  app, CARLA, guest or service replacement/restart was performed for this check.
- Explicit Autopilot restored after the checks; final native screenshot shows
  19.3km/h, AUTOPILOT/MOVING, network ON and both inspection advisories.

## Historical resource comparison and quota root cause

The operator asked whether resource monitoring had worked in earlier versions.
This investigation was read-only; no quota, source, service or runtime change
was made.

### Earlier success is documented

- [20 September UI qualification](presenter-ui-amendments-qualification-2026-09-20.md)
  explicitly records six live controller/Brake/Tire CPU/RAM series, both service
  disk scopes, and new samples after network reconnect. At11:39UTC it records
  Brake storage100KiB and Tire52KiB on Factory .36, VDP97/V3, Brake77/V3,
  Tire43/V1. These are live observations, not fixture-only assertions.
- [The preparation record](presenter-ui-timing-e2e-2026-09-20.md) records direct
  publication/deployment of Brake77/V3 on that Test. That resource inspection
  did not exercise V1-to-V2-to-V3 upgrades on the same service identity.
- Today's own retained SM journal proves successful Brake84/V1 monitoring at
  12:35:36UTC: CPU31, RAM3316KiB, storage28KiB, state0, inbound/outbound0.
  Thus the new Presenter and Factory .36 can report Brake resources.

### First failure aligns with V1-to-V2 UID migration

| UTC | Actual observation |
| --- | --- |
| 12:30:09 | CM sets up Brake84/V1 as UID5000 and executes Set quotas: storage8MiB, state1MiB. |
| 12:35:36 | SM still obtains all Brake resource groups successfully. |
| 12:36:10 | Brake85/V2 storage setup receives UID5001, unchanged quota sizes. No Set quotas event follows. |
| 12:36:46 | First Brake `can't parse quota output` monitoring failure. |
| 12:41:14 | Tire47 initial setup gets UID5002 and executes Set quotas: storage4MiB, state2MiB. |
| 12:47:18 | Brake86/V3 setup receives UID5003, unchanged quota sizes; again no Set quotas event. |

Current process inspection confirms Brake UID5003 and Tire UID5002. Read-only
`quota -u <uid> -w --filesystem <mount>` queries return `none` for Brake's
UID5001 and5003 on both state/storage filesystems. Tire UID5002 has numeric
quota rows and the expected limits. Both filesystems have usrquota enabled.
Brake's storage instance directory is owned by the current UID5003; this is
not simply a query against the wrong running UID.

### Source mechanism and corrected classification

In the Factory-pinned Core library `60cb83535f773762c61ac5f544b31b7b88c502e3`:

1. `src/core/cm/storagestate/storagestate.cpp:237` calls `SetQuotas` only when
   `QuotasAreEqual` is false.
2. `QuotasAreEqual` at line623 compares storage/state sizes only; it does not
   compare the UID to which filesystem user quotas are applied. A version
   change can therefore create a new UID while unchanged limits suppress
   setting that UID's quotas. The storage identity itself is versionless.
3. SM `src/sm/launcher/runtimes/container/monitoring.cpp:183` asks `quota` for
   that UID and expects a numeric filesystem row. The observed `none` output
   reaches the error at line216.
4. Disk retrieval is inside the same whole-instance monitoring operation,
   after CPU/RAM and before network. Its error suppresses the entire instance
   result; this explains why apparently unrelated CPU/RAM graphs disappear.

The inspected local library checkout is `0b82a6bf`; the storage-state and
launcher storage-state files have no diff against that Factory pin. No local
SM recipe patch changes this quota parser. The existing shared-storage
retirement patch changes final-owner removal, not this quota-setup condition.

This narrows monitoring-01 beyond the initial SM parser symptom: the primary
observed fault is CM quota setup after service UID migration, with whole-row
loss as the SM consequence. It is not a proven new Presenter regression, and
not a Brake analytics-specific defect. Tire has not changed version in this
run, so its successful monitoring does not qualify that same upgrade path.
No claim is made about an untested newer upstream revision.

### Proposed next proof, not implemented

Add a focused Core test: same instance identity, unchanged storage/state quota
sizes, new UID; require quotas for the new UID, with existing first-create,
same-UID repeat, changed-limit and preserved-state cases. Then qualify one
scoped runtime correction before considering an image rebuild. Do not hide
missing quota configuration by merely substituting zero for the SM parser
failure, and do not claim resource limits are enforced for the new UID from
the package's declared limits alone.

## Upstream recheck: stable instance UID already implemented

On 23 September the operator requested a fresh upstream check before any local
fix. Public Git remote refs and fetched source/history were inspected in
isolated temporary clones; existing build checkouts and the live Test were not
changed.

Resolved revisions:

| Repository | main | develop |
| --- | --- | --- |
| aos_core_lib_cpp | `5560291ba6914e36a5b841ade4d8fc54134a9e91` (v9.1.2) | `dd3c20a3a377237801b394e1e669c8520e26e5ab` |
| aos_core_cpp | `9d613a46df3c7f550062e2f19ae3406c57715694` | `673f857241b9a2c140cbeef93f9901f5597adcc2` |

### Relevant upstream correction

Library commit
[`c68690aa`](https://github.com/aosedge/aos_core_lib_cpp/commit/c68690aac2a4b90560d7975decce4c7496098dce),
`cm: launcher: add UID pool for the same instance ident`, is contained in both
main/develop and release tags v9.1.1 and v9.1.2. It was committed on
18 August 2026.

- `ServiceInstance::Init()` now acquires UID by the versionless `InstanceIdent`
  instead of allocating a new UID for each version. Existing identity entries
  reuse their UID and increment a reference count.
- Removing one cached version releases only its reference; the UID remains
  reserved while another reference exists.
- The upstream `CMLauncherTest.ServiceUpdate` source explicitly changes its
  expectation from new UIDs5002/5003 for version1.0.1 to retaining5000/5001
  from version1.0.0. The test was inspected, not executed in this audit.
- Consequently, this source change removes the demonstrated trigger on a
  clean upgrade path: unchanged quotas still apply to the same UID. This is
  the source-supported correction to qualify before inventing a separate
  quota-setup patch.

Current main still compares only quota sizes in `QuotasAreEqual`, and SM still
rejects the observed `quota ...: none` output. This alone does **not** mean the
upstream upgrade path is unfixed: the relevant fix is earlier, at UID
allocation. Application commit `a69a95bc` allowing quota exit codes0/1 is a
different change and does not, by itself, configure missing quotas.

Our CM recipe explicitly pins its embedded library to `60cb8353` / v9.1.0,
which lacks the stable-UID change. Updating only the application revision
would not update this separately pinned dependency.

### Revised recommendation and remaining gates

This supersedes the implementation direction in "Proposed next proof" above:
prefer qualifying the upstream stable-UID solution, with a compatible bounded
backport or a separately audited dependency upgrade, rather than immediately
adding a new local `SetQuotas` workaround.

Before selecting a backport, review the related main changes `b46d2a27`
(ID-pool capacity during removal) and `765f84c6` (release references despite
storage-removal errors), plus interaction with our final-owner shared-storage
retention patch. Their relevance was inspected; a minimal dependency set and
full upgrade compatibility are not yet qualified. Other local patches must
not be removed on the strength of this finding.

Required proof remains first installation, sequential V1-to-V2-to-V3 updates,
unchanged/changed limits, persisted data, cached-version cleanup, restart,
quota readback, and fresh Cloud CPU/RAM/disk/network rows for both services.

Do not treat this as automatic repair of the current Test: its quota state is
already missing for the active Brake UID. The new pool also rejects an
explicit stored UID that conflicts with an existing entry for the same
identity; migration of legacy records needs separate verification. No claim
of a successful live repair, build or upstream test execution is made.
