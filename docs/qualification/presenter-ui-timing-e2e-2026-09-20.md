<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI-only E2E and response-time observation — 20 September 2026

Status: CLEAN CONTINUOUS UI CYCLE COMPLETE THROUGH FINISH (06:46 UTC);
PRESENTER CORRECTIONS BUILT AND REGRESSION-PASSED. The 20 September follow-up localized a separate
cross-clock advisory rejection (T09 below). Its approved 100 ms amendment has
passed local regression and targeted live renewal/OFF/ON proof on the retained
Test. Confirmed UI Finish completed at04:35UTC; the subsequent clean.36 UI
cycle started at04:36UTC, paused for the approved layout correction, then
completed versions, real products, independent resets, OFF/ON and Finish.
This closes the recorded continuous operator scenario, not every broader P8
engineering/negative branch. Exact exclusions remain below.
Started 19 September 22:09 UTC / 20 September 00:09 CEST.

At 22:27 UTC the operator authorized completing this run, consolidating all
findings/timing issues in this file, planning corrections, implementing them and
running regression checks. Compilation/builds are authorized inside that scope.
The observation phase remains unchanged until evidence is collected; it does
not authorize a new product contract, Production change or unchecked deletion.

## Scope and method

The operator requested a new complete UI-only cycle, observing messages,
cross-surface consistency, action feedback latency and old/new status regressions.
No implementation corrections were made during the live observation phase.
Corrections below began after the version/offline/reconnect evidence was collected.
The previous run is
recorded separately in [the 19 September report](presenter-ui-e2e-2026-09-19.md).

Actions use Presenter and native Driving Control. Results are checked in those
UIs, not inferred from CLI or guest probes. The selected Cloud and certificate
domain both show `aws-stage.epmp-aos.projects.epam.com`; Production is excluded.
Initial state has no controller and selects Factory `6.1.1-maninblack.36`.

Times below are UTC. Click timestamps bracket UI actions; observation timestamps
are upper bounds from completed UI snapshots, not sub-frame performance traces.
Human/agent reading time between actions is not product latency. Operation receipt
duration, backend source time, backend receipt time and UI observation time are
different measurements. Polling may miss intermediate states; none are invented.
No telemetry real-time requirement or threshold is changed by this audit.

## Timing record

| Action | Confirmed click | First feedback observed | Completion / observation |
| --- | --- | --- | --- |
| Create controller | 22:10:02.986 | ACCEPTED 22:10:03.232, within 0.25 s | UI receipt COMPLETED in 77 s, at 22:11:20; next action observed 22:11:23.732 |
| Start simulator | 22:11:47.877 | ACCEPTED 22:11:48.055, within 0.18 s | Receipt COMPLETED in 43 s at 22:12:31; Platform next step observed 22:12:44.989 |
| Prepare VDP V1 / 89.0.0 | 22:13:33.481 | ACCEPTED 22:13:33.733, within 0.26 s | Receipt completed 22:13:35; candidate observed 22:13:48.239 |
| Prepare VDP V2 / 90.0.0 | 22:14:12.347 | ACCEPTED 22:14:12.526, within 0.18 s | Receipt completed 22:14:14; candidate observed 22:14:27.148 |
| Prepare VDP V3 / 91.0.0 | 22:14:43.126 | ACCEPTED 22:14:43.293, within 0.17 s | Receipt completed 22:14:45; unblocked navigation observed 22:14:52.500 |
| Prepare Brake V1 / 70.0.0 | 22:15:18.044 | ACCEPTED 22:15:18.260, within 0.22 s | Receipt completed 22:15:19; candidate observed 22:15:29.410 |
| Prepare Brake V2 / 71.0.0 | 22:15:57.965 | ACCEPTED 22:15:58.222, within 0.26 s | Receipt completed 22:15:58; candidate observed 22:16:13.270 |
| Prepare Brake V3 / 72.0.0 | 22:16:27.724 | ACCEPTED 22:16:27.901, within 0.18 s | Receipt completed 22:16:28; candidate visually confirmed before 22:16:42 |
| Prepare Tire V1 / 41.0.0 | 22:16:59.181 | ACCEPTED 22:16:59.413, within 0.24 s | Receipt completed 22:17:00; completed trace observed 22:17:06.477 |
| Publish VDP 89 | 22:18:39.706 | Operation in progress by 22:18:40.505, within 0.80 s | Receipt 6 s, completed 22:18:46.694; publication.stage ACCEPTED; Provision offered by 22:18:53.618 |
| Provision Test | 22:19:26.693 | RUNNING by 22:19:27.333, within 0.64 s | Receipt 30 s, completed 22:19:58; native selected Test/Manual 22:20:04; overview ONLINE and VDP89 pending 22:20:10.137 |
| Safe Stop for VDP89 | 22:20:25.118 | Selected-mode banner by 22:20:26.069, within 0.96 s | Cloud detail installed V1/89, no pending, by 22:20:38.785 (13.67 s upper bound) |
| Publish Brake 70 | 22:21:27.242 | ACCEPTED by 22:21:28.153, within 0.92 s | Receipt 11 s, completed 22:21:39; READY/Deploy enabled observed 22:21:59.042 |
| Deploy Brake 70 | 22:22:23.245 | ACCEPTED by 22:22:23.582, within 0.34 s | At 22:22:44.438 backend WAITING/AWAITING_INPUT, no false access-denied claim; RECEIVING source 22:22:54.945, UI 22:23:01.345 |
| Autopilot | 22:22:53.763 | Selected-mode banner by 22:22:54.345, within 0.59 s | Actual 19.4 km/h observed before 22:23:12.861 |
| Brake V1 maneuver | 22:23:12.861 | Preparing scene and disabled maneuver buttons by 22:23:13.442, within 0.59 s | Source event22:23:21, receipt22:23:28; COMPLETE visible22:23:52.941 |
| Inspect V1 result | 22:24:01.604 | Complete detail by 22:24:01.793, within 0.19 s | 76 samples, PRE30/ACTIVE26/POST20, 8/8 chunks, COMPLETE; real speed/brake charts visible |
| Publish VDP90 | 22:24:46.899 | ACCEPTED by 22:24:47.144, within 0.25 s | Pending90 while installed89 and native Autopilot19.4km/h by 22:25:14.711 |
| Safe Stop for VDP90 | 22:25:22.332 | Stopping / Safe Stop by 22:25:22.934, within 0.61 s | V2/90 installed, no pending by 22:25:33.162 (10.83 s upper bound) |
| Publish Brake71 | 22:26:03.049 | ACCEPTED by 22:26:03.263, within 0.22 s | V2 input report source22:26:25.383, visible22:26:32.343; Cloud active71 visible22:26:43.349. No second Deploy or Safe Stop; native19.5km/h at22:26:22 |
| Brake V2 maneuver | 22:26:43.405 | Preparing scene by22:26:43.995, within0.59s | ACTIVE observed22:27:03.127; MONITOR40 source/receipt22:26:59, inspected22:27:37.856 |
| Publish Tire41 | 22:27:57.470 | ACCEPTED by22:27:58.482, within1.02s | READY observed22:28:33.816 |
| Deploy Tire41 | 22:28:53.791 | ACCEPTED by22:28:54.600, within0.81s | Cloud active22:29:37.817; required VDP V3 correctly not installed yet |
| Publish VDP91 | 22:30:23.025 | ACCEPTED by22:30:24.144, within1.12s | Pending91 / installed90 observed22:30:38.060 |
| Safe Stop for VDP91 | 22:30:45.861 | Selected mode by22:30:46.447, within0.59s | Installed91 visible22:31:09.093 (23.24s upper bound); no restart/redeploy of Tire |
| Publish Brake72 | 22:31:45.405 | ACCEPTED by22:31:46.586, within1.19s | Cloud v3/72 shown last-known22:32:20.581 then current22:32:29.034; current input, no relabelled V2 assessment |
| Brake V3 maneuver | 22:32:41.602 | Preparing scene by22:32:42.203, within0.61s | Result34/100 source/receipt22:32:56; native Inspection recommended and service ACK confirmed22:33:35 |
| Tire maneuver | 22:33:47.269 | Preparing within0.61s | Result67/100 source/receipt22:34:01; native warning22:34:10; ACK confirmed22:34:22 |
| Tire Reset | 22:34:42.457 | Submitting within1.18s | Waiting for CLEAR22:34:48; native Monitoring22:34:59; confirmed-clear dialog22:35:14.824 |
| Brake Reset | 22:39:32 | Submitting by22:39:33.267 | Confirmed CLEAR and native Monitoring22:39:52.098 |
| Return to road | 22:40:05.350 | Accepted within0.57s | Lane-aligned stationary Manual by22:40:23; Autopilot required a separate explicit action |
| External network OFF | 22:40:33.4 | CHANGING within0.60s | OFF visible22:40:55; Cloud Offline22:41:41, within68s observation bound |
| External network ON | 22:45:52.750 | CHANGING by22:45:53.366, within0.62s | Cloud Online visible22:46:39; Tire backlog receipt22:46:08, Brake22:46:23; both queues0 and input RECEIVING |
| Historical chart shortcut after correction | 23:03:14 | Filtered V1 records visible within1.28s | First record detail visible23:03:20, within0.88s of inspection;59 samples/6 chunks, real graphs |

The V1 maneuver produced source event22:23:21, receipt22:23:28 and a complete
record observed22:23:52.941. Long inspection gaps in this table are observation
bounds, not proof of an equal UI delay. VDP90 activation interrupted a separate
V1 recording; the overview correctly displayed source data gap and retained the
already completed historical recording. A later natural episode completed59
samples/6chunks before Brake71 activation. V2 then showed no current-release
result until its own assessment arrived; old V1 content was not relabelled V2.

Tire41 is Cloud active by22:29:37.817. Its service detail explicitly reports
required VDP V3 / installed VDP V2, while its backend reports STALE/SOURCE_GAP,
no assessment and a separately recent reset channel. After VDP91, Tire input
is RECEIVING (source22:31:19.400; UI22:31:28.718) without redeployment. The
native dashboard shows Tire Monitoring and Brake Waiting for service until
Brake72 is installed. Natural driving supplies Tire Good before22:32:20.

Create used existing native VM access without a new password request. The
console-wait stage was visible and changed to credentials submitted before
completion. No Cloud provisioning is inferred from Create.

All seven unsigned candidates were prepared first to batch the exact staging
publication authorization, not to publish or install later profiles early.
Publication and installed-profile proof remain sequential. No CLI build or live
action was used for this run's scenario. Later Presenter builds and isolated
fixture regressions are engineering verification, not substitutes for live UI
evidence. A 22:17 grouped request covers only the enumerated releases,
selected OEM/SP certificates, staging and the current Test. The operator accepted
the complete enumerated set before the first publication.

The 43-second simulator receipt is distinct from browser observation overhead.
Native CARLA shows the initial lane-aligned stationary vehicle; Driving Control
shows Not assigned, Safe Stop, 0 km/h and both advisories Not available before
Provision. No premature Domain Controller connection is inferred.

## Findings collected during the unchanged observation phase

| ID | Observation | Evidence / disposition |
| --- | --- | --- |
| T01 | View progress is empty during first Create despite a running operation. | At 22:10:11, modal says No operations recorded; inline RUNNING and steps remain visible. Previous E01 reproduced. |
| T02 | New Full story retains the previous run's selected V3 in Platform and Brake authoring. | First visits at 22:12:44 and 22:14:52 selected V3 with no candidate in the new run. The operator can accidentally skip V1; this run explicitly selected V1. Navigation preference retention is observed, not a release downgrade or status regression. |
| T03 | Pre-Provision empty backend copy implies earlier records/incomplete history. | At 22:16:05, no Cloud identity/result exists, but Brake says Product history is incomplete and Earlier results remain in Records. Previous E02 reproduced. |
| T04 | Publication confirmation still hides exact selected Cloud and SP context. | VDP89 and Tire41 dialogs say Configured Cloud publication context; selected staging is verified separately in Session. Previous E06 reproduced; no wrong-destination request occurred. |
| T05 | Browser observation can briefly regress from ONLINE to Last known/Reading Cloud with OBSERVER_HIDDEN. | Observed during native/browser returns and a team-tab transition (22:21:07, 22:22:33). Restored without network action. This is an observer visibility transition, not evidence that Unit went Offline. The exact contribution of the embedded test surface versus desktop Presenter requires isolation. |
| T06 | Tire stale-input helper calls its next output a recording. | At22:29:53 it says Waiting for fresh input before the next recording; receiving helper correctly calls it a driving exercise. Previous E07 reproduced. |
| T07 | First resource read prematurely claims no sample exists. | Cloud Resources simultaneously shows Reading and No sample reported, before any response. Reproduced in a focused regression before correction; loading, failed read and confirmed empty response must differ. |
| T08 | Reload briefly reports Cloud unavailable before the first Cloud observation. | At23:08, the existing registered controller is known locally but no Cloud response has arrived. Reproduced by regression; absence of the first observation is not a failed connection. |

Read-only code inspection narrows T05: `VisibleCloudObserver.enter()` cleanup
marks state OBSERVER_HIDDEN as soon as its final panel unmounts, even if another
perspective mounts immediately. The trace also reproduces on same-browser
perspective changes with a zero-second-old Cloud observation. A regression test
must distinguish navigation handover from genuine document hiding; this is not
permission to suppress true unavailable/slow observations.

Native action feedback and confirmed telemetry are distinct: immediately after
Safe Stop/Autopilot/maneuver clicks the left selected-mode banner changes before
the right telemetry mode/speed. The snapshots below one second are transitional,
not proof of a stuck command. Their settling time remains a separate observation.

## Reset, road recovery and offline observations

- Brake V3 produced Inspection recommended, 34/100, source/receipt22:32:56;
  native warning and backend ACK CONFIRMED were visible22:33:35.
- Tire maneuver22:33:47.269 acknowledged Preparing within0.61s, produced
  Inspection recommended67, source/receipt22:34:01. Backend refresh returned
  the result within0.93s. Native warning22:34:10; ACK confirmed22:34:22.
- Tire Reset22:34:42.457 acknowledged within1.18s, waited for CLEAR22:34:48;
  native Monitoring22:34:59 and confirmed-clear dialog22:35:14.824.
- Brake Reset22:39:32 acknowledged by22:39:33.267; confirmed CLEAR and native
  Monitoring by22:39:52.098. Both histories remain, no synthetic GOOD result.
- Return to road22:40:05 acknowledged within0.57s. By22:40:23, native state is
  stationary Manual, CARLA is lane-aligned and no automatic Autopilot starts.
  Explicit Autopilot then produces19.4km/h before external OFF.
- External OFF22:40:33 acknowledged CHANGING within0.60s, OFF visible22:40:55.
  Cloud Offline visible22:41:41 (68s observation upper bound, not exact delay).
  Brake last report source22:40:09, Tire22:40:20; both become Last known.
- Offline Brake maneuver22:41:42 and Tire maneuver22:42:28 complete locally.
  Both native Inspection recommended indications are visible22:42:45.179.
  Neither backend has received those new results while disconnected.

Additional confirmed issues: E10 (post-reset release-never-produced wording),
E11 (Cloud Software modal omits Offline) and E13 (disabled Reset still describes
earlier CLEAR rather than current unavailability) are reproduced. A transient
native Brake Monitoring indication between warnings during scene/exercise
changes is observed, but its cause is not established by the UI alone; it is not
classified as model loss. Current versus retained advisory must remain distinct.

After a 5m20s external-OFF hold, network ON at22:45:52.750 restored delivery
without restarting VM, CM, CARLA, Gateway or services. Tire result66/100 had
source22:42:42 and receipt22:46:08; Brake32/100 had source22:42:43 and
receipt22:46:23. Source timestamps stayed in the offline interval. Cloud Online
was visible22:46:39, both function reports became RECEIVING and both queues
reached0. No30-minute blocked-Offline condition occurred in this run.

E12 resource-source freeze did not reproduce: after OFF, CPU sample22:39:46 /
read22:41:22 was correctly last known. After reconnect, CPU sample22:58:26 /
read22:59:02 and RAM sample23:00:46 / read23:00:53 progressed. This is recovery
evidence, not proof of a fix for the earlier run. RAM remains explicitly
`unit not specified`; no byte/percentage unit is inferred.

## Consolidated correction plan

This file owns the complete follow-up list, including prior E01–E14. Existing
source/VM/Cloud contracts and guardrails remain unchanged.

| Priority | Items | Bounded correction / proof |
| --- | --- | --- |
| P1 | T01/E01, E14 | Show the actual active job before first run identity exists; preserve a short-lived Finish acknowledgment inside an already-open Trace. Test first Create, run isolation, terminal Finish and expiry. |
| P1 | T05 | Eliminate false hidden transitions during perspective handover without suppressing genuine document-hidden, slow-read, failed-read or post-action states. Test single-flight and no extra background polling. |
| P1 | T04/E06, E11 | Show actual selected Cloud and signing role in publication confirmation; explicitly distinguish Cloud Unit connectivity from retained instance reports in monitoring. No credentials exposed. |
| P2 | T02, E04/E05 | Start a genuinely new story at V1; explain blocked source/build prerequisites and engineering preflight. Do not bypass committed-source checks or silently introduce automatic builds. |
| P2 | E08/E09 | Fit architecture at the observed compact browser geometry without hiding controls; add a direct historical V1 recording route/filter using actual retained data. No invented charts/results. |
| P2 | E12 | Recheck source/read timestamps after recovery and inspect the existing monitoring query if still stale. Change only a reproduced query/formatting defect; unknown units stay unknown. |
| P3 | T03/E02, T06/E07, T07/T08, E10/E13 | Distinguish not started/first observation from partial or failed reads, use team-appropriate episode wording, scope no-result text to Reset, and show current Reset disabled reason separately from dated historical success. |
| Gate | E03 | Already resolved by reviewed service source checkpoints and four prebuilt products; intentional reproducibility guard is retained. |

For each source correction: reproduce with a focused test, apply the minimal
delta, run affected tests/typecheck, then the Presenter suite/build and UI
verification. Preserve the current Test for live UI regression. No factory,
model, permission, lease or backend protocol change is implied. No additional
publication or destructive action is inferred from this plan.

## Implemented corrections and verification boundaries

| Items | Change | Verification |
| --- | --- | --- |
| T01/E01 | Trace uses the active session job before Create allocates a run identity. Previous-run history stays scoped. | Focused failure reproduced, then unit regression passed. No second live Create needed to exercise a display-only fix. |
| E14 | An already-open Trace keeps the existing short-lived Finish acknowledgment after retirement removes the run ID. | Unit coverage includes completion and expiry. Live final Finish is pending approval, not claimed passed. |
| T02 | Authoring selections return to V1 only when the run identity changes. Same-run navigation preserves the operator's selection. | New-run/same-run unit checks passed. No package downgrade or mutation. |
| T03/E02 | Unprovisioned backend explains setup; an unreceived first observation is not an incomplete history. Earlier records are mentioned only when present. | Empty/setup and partial/failure regressions passed. |
| T04/E06 | Confirmation names selected Cloud and session OEM/SP signing role. SP identity is shown only from a completed receipt for this exact release and Cloud; otherwise explicitly not yet reported. | Selected destination and matching/wrong-Cloud/wrong-release receipt tests. No certificate contents exposed and no new upload. |
| T05 | Cloud visibility subscription now belongs to the mounted workspace, not each team perspective. Navigation still explicitly refreshes. | Reproduced3 subscriptions before fix,1 after. Existing hidden/slow/failed/post-action and single-flight regressions passed. |
| T06/E07 | Tire helper uses driving-exercise wording; Brake keeps recording terminology. | Team-specific missing/stale/active/skipped/completed input checks passed. |
| E04/E05 | Blocked Prepare explains the source-checkpoint or compiled-profile prerequisite and directs to actual progress. | Prerequisite tests; source/build guards and no-retry behavior unchanged. See preflight below. |
| E08 | Compact workspace uses bounded spacing and an inline factory selector. Icons, arrows and controls remain visible. | Failure reproduced at1327×923 (603px content/543px available); seven geometry cases subsequently pass, including851/900/923px boundaries. |
| E09 | Backend Overview directly opens retained braking recordings, with an explicit record-type filter. | Live V3→historical V1 path,59 real samples/6chunks and actual charts; browser test verifies current V3 result remains unchanged and all-records route remains accessible. |
| E10/E13 | Empty result is scoped to the confirmed Reset. Current reset-channel/failed-read reason precedes a dated historical CLEAR; newer result is stated separately. | Reset boundary, offline channel and newer-result unit/browser tests; live retained result/date verified. |
| E11 | Cloud Software modal repeats Unit connectivity and distinguishes retained instance reports from live input/results. | Existing inventory/read regressions; post-fix live OFF/ON verification recorded below. |
| T07 | First resource observation, unavailable read and confirmed empty response have separate copy. Previous metric remains visible during refresh. | Reproduced failing test, then passed for waiting/error/empty/retained758DMIPS cases. |
| T08 | Initial Cloud absence says not yet observed; a completed unavailable observation still says unavailable. | Reproduced failing test before correction; pending-versus-failed unit regression passed. |
| E12 | No source/query change. Resource timestamps resumed in this run; unknown RAM units stay explicit. | Earlier stale-sample cause remains unlocalized, not silently closed. |

### Engineering preflight, not an operator retry loop

Before a new manual demo, the owning engineering preparation must have reviewed
and checkpointed service source, then built Brake V1/V2/V3 and Tire V1 products
using the existing supported service-build path. UI Prepare consumes these
products; it does not compile uncommitted source. In this run the products from
the preceding approved checkpoint were already available, so all seven UI
preparations succeeded in1–2seconds without a CLI exception. A failed Prepare
must not be retried unchanged or bypassed by publishing an old artifact.

### Final gates and activation

- TypeScript checking and production build passed.
- Final unit suite: **280/280**, 26 files, 2.39 seconds.
- Final isolated browser suite: **125/125**, 36.4 seconds. It uses fixture API
  responses on port18070, not the running staging Test. Earlier failures were
  reproduced defects (first Create, false visibility handover, first observation,
  compact geometry), or explicitly adjusted expectations for corrected copy;
  the final runs have no ignored failures.
- Geometry coverage includes1280×720,1327×851,1327×900,1327×923,1440×900,
  1728×1117 and native-browser1118×1124. Detailed charts and dialogs retain
  separate bounded-pagination checks. This is not a promise for arbitrary sizes.
- Final assets: `index-C-SRkLC6.js` and `index-CUfsLc_F.css`. The existing
  UI server serves this build. The live browser adopted it through Reload UI
  at23:14UTC; no VM, simulator, backend or service restart was used to activate it.
- Live post-fix check at23:10 showed the entire architecture, including Factory
  firmware and VSS subtitle, at the previously failing1327×923 viewport.
- Final live build identity was verified from the loaded script at23:16:
  `index-C-SRkLC6.js`; the architecture body had575px available and575px content,
  without overflow. Platform→Brake→Tire→Vehicle navigation retained ONLINE in
  each observed header while independently indicating the refresh in progress.
  The original same-tab OBSERVER_HIDDEN transition did not recur. This is
  sampled live confirmation plus deterministic regression, not a frame trace.
- Live post-fix OFF at23:10:17.664 and ON at23:12:20.295 preserved local advisory.
  Cloud dialog explicitly showed OFFLINE with retained-instance context. Brake
  Reset was disabled with the missing-contact reason plus the separately dated
  previous CLEAR. Source/result timestamps remained unchanged during disconnection.
  Cloud was visibly ONLINE by23:13:17; Brake input had resumed and Tire's
  subsequent report returned to RECEIVING by23:14:39. No restart or manual
  queue replay was required. These are observation bounds, not exact delays.
- Read-only process inspection confirmed the existing native Presenter process
  remains running. Its paired WebKit views have an idle-only build refresh in
  the existing shell code. The automation surface could not select that
  unbundled native process, so independent visual confirmation of the desktop
  WebKit window is not claimed; browser/live data and native-browser fixture
  layout are the evidence here. CARLA/Driving Control were directly inspected.
- `git diff --check` passed. Existing unrelated changes were preserved.

The material response times are the boot/simulator operations (77/43seconds),
provisioning (30seconds), FOTA application (observed within11–24seconds after
Safe Stop) and eventual Cloud connectivity. Immediate action feedback in the
measured cases was0.17–1.19seconds. There is no evidence here that lifecycle
work should be replaced by an optimistic success. Corrections remove false
transitions and empty/ambiguous progress; they do not invent a faster backend.

### Remaining qualification boundary

At22:47UTC final Finish was opened, but irreversible deletion requires an
action-time confirmation. The request was sent and the unsubmitted dialog
cancelled while Presenter corrections continued. Until the response arrives,
retain this Test in stationary Safe Stop with external networking restored.
Do not substitute a CLI cleanup for the pending UI confirmation.

This pass does not claim complete P8 coverage or zero possible side effects.
The separate reboot matrix, occupied-spawn/collision recovery matrix and earlier
unlocalized source-sample freeze are not closed by a successful continuous run.
No factory/CM/SM/IAM/VDP/service binary, model, quota, permission, lease or backend
wire protocol is changed by the Presenter correction pass. Production is untouched.
Existing unrelated worktree changes are preserved; no commit/push is performed
under this turn's build-and-repair authorization.

### Handoff state and open items

At23:17UTC the retained .36 Test is Online in staging, VDP V3/91.0.0,
Brake V3/72.0.0 and Tire V1/41.0.0 installed. Both backend inputs are RECEIVING,
both retained assessments are Inspection recommended, and there is no pending
software update. Native Driving Control remains Safe Stop,0km/h,external
network ON. No new mutation is running. The live browser is left on Vehicle.

| Item | Next step / reason it is not marked complete |
| --- | --- |
| Final live Finish | Obtain the pending action-time confirmation, execute it once through UI, verify the in-dialog completion acknowledgment and empty initial state. This is the only unexecuted step of this run's main scenario. |
| Earlier E12 source-sample freeze | If it recurs, preserve source/read timestamps and localize Cloud query versus guest reporting before changing either. It did not recur here. |
| Brief native Monitoring between exercise warnings | UI alone did not establish the cause. Preserve it as an observation, not a claim of model loss or a Presenter fix. |
| Native WebKit visual confirmation | Recheck the existing desktop Presenter at the operator's display geometry; its process remains running, but this automation surface could not inspect it directly. |
| Broader P8 branches | Keep separate reboot, occupied-spawn and collision-recovery matrix entries open; the continuous scenario and fixture suite do not replace those live checks. |

## 20 September continuation: reconnect and advisory localization

The operator accepted the follow-up sequence: investigate the retained Test,
correct proven causes, regress, Finish through UI, then one fresh full UI cycle.
At03:23UTC the existing .36 Test was still Online with VDP91, Brake72 and
Tire41, both inputs RECEIVING, external network ON and stationary Safe Stop.
No VM, CM, service, simulator or backend restart was used for this investigation.
Read-only guest journals and local backend status records supplement the UI
observations below; they are diagnostics, not a substitute for scenario actions.

### Tire reconnect: transport delay is not an input-state delay

The earlier23:12:20.295 network-ON action produced the first queued Tire
function-report receipt at23:12:25.099: **4.804seconds**, not139seconds.
The queued reports drained through23:12:25.764. Subsequent source/receipt pairs
include23:13:09.356/23:13:09.423 and23:13:15.411/23:13:15.523. Receipt latency
for those status messages was milliseconds. Product delivery independently
reported CONNECTED at23:12:53.104.

The Tire guest journal reports actual input interruptions:23:13:04.313→04.511,
23:13:05.738→05.911 and23:13:10.021→15.412. Its current complete-frame policy
requires all15 source timestamps to match and age at most250ms; its watcher
also marks a gap after250ms without a complete frame. Gateway summary frames
continued during this interval. Those summaries do not establish per-signal
VDP/KUKSA timing, so they do not identify the exact cause of the local gap.
Older full function payloads were already pruned under the accepted1024-payload
bound; compact source/receipt records remain. Do not claim an exact historical
UI state from a now-pruned payload, or a proved139-second service outage.

A UI-only repeat used OFF03:26:08.087 and ON03:27:25.759. Cloud Offline was
visible by03:27:04 and Online with both inputs RECEIVING by03:27:53. Native
warnings remained visible during OFF and after ON. Tire queued status receipt
resumed at03:27:30.024 (**4.265seconds** after the ON click), and a report of
queue0 arrived at03:27:35.098 (**9.339seconds**). Retained offline reports
explicitly show RECEIVING, including a separate REAUTHENTICATING advisory axis.
There was no restart, reset, replay command or delayed-Tire UI reproduction.
The earlier local input gap remains distinct from the disproved transport-delay
hypothesis. No freshness threshold was enlarged.

### T09 — millisecond clock lead rejects advisory refresh

**Proven chain, not model loss:** stored Brake Gateway facts show:

| Request issued (VM UTC) | Gateway observed (Mac UTC) | Outcome |
| --- | --- | --- |
| 22:33:56.887 | 22:33:56.874 | REJECTED / STALE_REQUEST; existing warning valid until22:34:06.874 |
| 22:34:16.900 | 22:34:16.894 | REJECTED / STALE_REQUEST; no active warning |
| 22:39:17.742 | 22:39:17.724 | REJECTED / STALE_REQUEST; existing warning valid until22:39:27.684 |

Separate EXPIRED facts at22:34:06.896 and22:39:27.702 confirm that the earlier
warning leases ended. Tire has the same rejection pattern, with recorded
positive leads of2–29ms (for example02:00:56.031 issued versus02:00:56.002
Gateway-observed). These observations establish different wall-clock readings,
not which machine has the correct absolute UTC time or an NTP failure. A
read-only timedatectl query was denied; do not claim its synchronization result.

Source correlation:

- `carla-ego-runtime/src/qm_advisory.cpp`: any `issued > now` is rejected,
  independently of the2000ms maximum request age. The old active lease is
  retained until its normal expiry, not immediately cleared by rejection.
- `brake-health-service/src/runtime/advisory_runtime.cpp` marks observed
  rejection written; the normal same-decision refresh waits20seconds.
- `tire-health-service/src/runtime.cpp` also treats REJECTED as sent and
  normally refreshes after20seconds.
- `aos-vehicle-platform/.../advisory.py` retains a request in replay tracking
  before the Gateway response; an identical retry is IDEMPOTENT_NO_NEW_EFFECT,
  not another forwarding attempt. Therefore a service-only identical retry
  is **not** a valid complete fix for the current chain.
- `carla-ego-runtime/src/viss_client.cpp` deliberately returns the ready idle
  label MONITORING once the confirmed warning expires; native Swift renders
  that projection. It does not mean that the health model became GOOD.

This localizes the observed warning→Monitoring transition class. It does not
prove every past screenshot transition had this cause. A fresh UI Brake
maneuver at03:28:02.281 completed with source/receipt03:28:17, score26,
confirmed ACK and native warning visible by03:28:44. No transient Monitoring
was caught in those snapshots. CM, SM, IAM and VDP reported active, exit0,
NRestarts0 in the03:29UTC read-only check.

### Bounded change decision before another clean cycle

The operator accepted the 100 ms amendment on 20 September 2026. Do not hide
the rejection, backdate requests, extend warning leases, weaken replay rules
or patch AosCore. The follow-up is an explicit small cross-clock tolerance for
these two non-safety QM advisory endpoints, consistently in VDP and Gateway,
with effective activation lifetime still capped at30seconds. Keep
2000ms old-request rejection, endpoint authorization, sequence/replay, rate
limits and correlated APPLIED/CLEARED proof. Future offsets outside the new
explicit bound must still fail. Approval alone does not qualify a new package
or Factory image. Profile1.2.0 records this amendment; Brake policy1.0.4 only
repins that shared contract and does not change producer behavior.

Required gates after approval: deterministic boundary and clock-step tests;
unchanged negative authority/replay/expiry cases; one targeted live successor
with original timestamps and repeated lease renewals; offline renewal; then
Finish and the fresh UI-only version cycle. Review the native expired-warning
label separately instead of silently replacing the accepted idle semantics.
Preserve this Test and all evidence until the targeted live proof. The earlier
diagnostic follow-up made no runtime patch, publication, cleanup or Factory build.

### Accepted amendment: local regression progress

New deterministic tests failed on the original VDP policy at +1/+100 ms for
both endpoints and on the original Gateway future-clock boundary. After the
fix, VDP family37 and advisory transport13 tests pass; Gateway QM advisory and
native dashboard projection targets both pass. Tests cover +100 accepted,
+101 rejected, past age2000 accepted/2001 rejected, original-byte forwarding,
declared lease30001 rejected, effective lease clipped to30000, earlier expiry,
duplicate non-renewal, replay conflicts, and UTC forward/backward steps with
monotonic expiry. Existing authorization/rate/isolation negative tests remain.
The build uses the existing cache; no running simulator, VM or Cloud mutation
occurred during that local correction gate.

Subsequent local gates: Platform178 tests passed; Gateway6 affected targets
passed (QM, dashboard, VISS protocol/access/assignment/network); Demo Control
1010 tests ran, 995 passed and15 optional tests skipped; shared QM/Brake
contract suites8+7 passed. The component subset ran160 tests with3 skips,
including composition/import against real frozen dependency files. These are
local fixture/packaging gates, not live VM/Cloud qualification.

- Platform source checkpoint: `394a645664f44a922b6a54388dfac7cfe9763221`.
- Gateway source checkpoint: `dee511041f3abf62ad135b5d04e8ed7ccb5a2461`.
- New arm64 Mac Gateway executable SHA-256:
  `dac36ffd3400f4a46f0d25824a9bba3ced60e78ff0d4e805c25459c8ef4ba007`.
- Prepared unsigned VDP93.0.0 SHA-256:
  `c7c11587ae9e9a994d18e13bf9ab4ecd034b990a5acbd8aaa81d522027bffccb`.
- Both retained VDP91/profile1.1.0 and successor93/profile1.2.0 inspect with
  no packaging problems. Historical source/contract pairs remain exact; the
  new policy is not retroactively claimed by earlier releases.
- Local commits contain only the bounded correction. Unrelated Platform
  source-order diagnostics and Gateway control changes remain untouched;
  no push is claimed. Solution integration/doc changes remain in its working tree.

### Amendment activation: retained Test, not a new clean E2E

The first local UI Prepare at04:13:58.542 was blocked by the old Presenter
process's in-memory contract pin. No package upload or VM mutation occurred.
The idle Presenter server alone was restarted through its guarded stop/start;
CARLA, Gateway, VM, services and Cloud stayed running. The failed allocation92
was not reused. A second UI Prepare at04:16:13.692 completed in2seconds as
93.0.0; current installed91 remained visible, not replaced optimistically.

The operator then explicitly authorized signing/publishing93 to the selected
staging Cloud and one simulator/Gateway/Driving Control restart, preserving
the Test VM, Cloud identity, Brake/Tire and accumulated state. UI Sign & Publish
confirmed at04:18:54.875; the UI snapshot carrying local timestamp04:19:11
showed Cloud installed93, and the later04:19:42 snapshot had a confirmed
profile binding. The brief catalog processing/profile
unconfirmed state was displayed separately from Cloud installation.

No standalone Gateway-restart control exists in the current Presenter.
For this engineering activation only, the approved standard
`democtl simulation stop --target test` confirmed physical Safe Stop, detached
the source and stopped only its simulation group. This is explicitly **not**
UI-only scenario evidence. The existing UI Start simulator was confirmed at
04:20:37.031 to load the newly built Gateway. No Factory rebuild or AosCore
change is included. Live renewal/offline results are recorded below when observed.

### Retained-Test live result after the approved amendment

- UI Start completed; UI Connect in Manual confirmed at04:21:41.134. The
  first native snapshot had Brake warning and Tire Monitoring; both showed
  Inspection recommended after their first fresh acknowledgments. No model
  reset was performed. Historical pre-Gateway-start targets were not replayed.
- Autopilot confirmed at04:24:17.877 and actual19.4km/h was visible before OFF.
- Network OFF clicked04:24:32.425; ON clicked04:26:34.098 (121.673seconds).
  Native OFF and both warnings remained visible beyond several lease periods.
  Cloud Offline was visible in the04:25:39 UI snapshot. Backend function reports
  first retained the last accepted04:24:30 source/receipt, then correctly became
  Last known/Not confirmed after the existing90second freshness allowance.
  This allowance was not changed by the QM amendment; Backend checked time
  remains a separate local read time, not receipt of new vehicle telemetry.
- A real Tire maneuver was started through native UI at04:25:08.475 while OFF
  and completed in Safe Stop. After ON the Tire popup showed a new score67,
  source event04:25:22, received04:26:37, confirmed Service ACK and0 queued.
  This demonstrates work performed while disconnected, not fabricated data.
- Read-only backend correlation found **zero new stored messages** in either
  backend during04:24:34–04:26:34. Both services produced6 APPLIED Gateway facts
  locally in that interval. Tire's first queued advisory receipt04:26:37.390
  was3.292seconds after ON; Brake's first04:27:05.931 was31.833seconds after ON.
  These are product/advisory-channel receipt latencies, not Cloud Online time
  and not necessarily first function-status receipt latency.
- The UI observation at04:27:44 showed Cloud Online, both inputs RECEIVING,
  no pending update, VDP93/Brake72/Tire41, and both native warnings. Native
  network state returned ON. The exact earlier Online transition was not sampled.
- At the subsequent bounded database read each endpoint had22 APPLIED facts
  since connection, no REJECTED/EXPIRED/FAILED facts in that window. Maximum
  effective leases were29987ms Brake and29989ms Tire. All sampled live leads
  were negative (closest to future: -13ms/-11ms); the positive+100ms case is
  deterministic regression proof, **not** a forced live-clock experiment.
- Read-only health: CM, SM, IAM and VDP active; exit0/NRestarts0. No VM or
  manager restart, service update, permission change or Factory rebuild occurred.

Targeted T09 regression passes. This does not close the earlier unlocalized
Tire input gap, the broader P8 matrix or the pending clean UI-only version
cycle. Final Finish was opened for exact operator confirmation; no deletion
has occurred at this checkpoint. The active Test remains in Safe Stop/Network ON.

### Confirmed retirement and clean-cycle handover

The operator confirmed the exact irreversible Finish. The final UI confirmation
was clicked at04:34:36.320UTC. ACCEPTED was visible immediately; RUNNING showed
12s, Offline by the22s observation, and Unit/Node absence confirmed in the
expanded operation steps by41s. The intermediate deleted-Unit read showed
`CLOUD_HTTP_404` with explicitly last-known inventory, not a fresh installed
claim. At04:35:27.617 the UI showed `Demo finished`, no controller/Cloud Unit,
empty service slots and a Factory VDP slot; the displayed snapshot time was
04:35:24.989. Thus completed empty state was observed within51.297seconds of
confirmation (snapshot time48.669seconds), not a30-minute wait. Exact server
completion time was not sampled. Runtime Trace reset to0, while the separate
completion acknowledgment remained visible. No CLI lifecycle fallback was used.

The current Test Cloud identity, working VM and run-scoped backend state were
retired through the normal UI operation. This is irreversible; factory.35/.36,
published releases, version continuity and this report remain preserved.
The next clean UI-only cycle will explicitly select.36 because the empty-state
factory selector defaults to.35. The retired Test is not the next run.

### Corrected-build clean UI cycle (in progress)

Factory.36 was selected explicitly. Create controller confirmed at
04:36:24.752UTC; ACCEPTED was visible in the same call. View progress showed
the actual running Create and console-readiness stage before identity
allocation (14s and17s samples), closing the live T01 reproduction for this
path. VM access was already available in the native process; no password
prompt or secret input was required. Completion is recorded only when observed.

The Create receipt subsequently reported COMPLETED at04:37:40 (about75s after
confirmation); the main next step was visible at04:37:47. The pre-Provision
Brake popup correctly said that Test identity was not observed and no vehicle
data was expected before setup, instead of implying missing historical records
(T03 live check). Start simulator confirmed04:38:00.633; the next-step UI was
visible by04:38:48. Native Driving Control showed0km/h, Safe Stop, no assignment
and both advisories Not available. No premature Gateway-to-Test assignment was
shown. Platform opened atV1 in the new run (T02 live check).

Session selected Cloud remained `aws-stage.epmp-aos.projects.epam.com`.
Certificate domain initially said Not available until explicitly read; that
display alone is not an authentication failure. Reading/selection was disabled
while Create was running, as required by the operation guard.

### T10 — native placement failure is not exposed by Start simulator

The operator noticed that CARLA and Driving Control did not occupy their
assigned desktop regions. Read-only investigation paused further scenario
actions before confirming Brake preparation; no process was stopped/restarted.
The native screenshots show CARLA1100x732 and Driving Control1040x632,
matching their default launch sizes. The generated layout instead requests
CARLA `[8,131,914,614]` and Controller `[8,753,914,502]` on the built-in display.
The run records `builtin-v1` restore at04:38:36.178315; therefore auto-placement
was invoked, not omitted because the profile was absent.

The UI operation reports Start simulator COMPLETED at04:38:36.720858
(36.069seconds after04:38:00.651842). Source inspection shows that placement
errors are collected as workspace INCOMPLETE while simulation remains RUNNING;
the Presenter public-result allowlist omits that workspace result. Thus the
operator receives no placement warning even though the native scene is not
composed correctly. The exact underlying window-operation error was not retained
in the public receipt. A scoped macOS log read did not establish a TCC denial;
do not label this an Accessibility permission failure without further proof.

Required bounded follow-up: retain/expose non-secret per-surface placement
diagnostics, distinguish a running simulator from a correctly placed workspace,
and support layout-only recovery without restarting CARLA/VM or recreating the
scene. No layout source change or desktop permission change was made during
this investigation. VDP94/V1 and95/V2 were visibly prepared; the V3 preparation
completed but its allocated version has not yet been read on screen. No new
package has been published, no Cloud provisioning has been attempted, and Brake
preparation was cancelled before submission. The new Test remains preserved.

#### T10 investigation: placement ran while the macOS session was locked

The operator requested investigation, not a live layout/source correction.
Scoped macOS logs with explicit UTC offsets establish this timeline:

| UTC | Observed event |
| --- | --- |
| 04:36:17.778 | loginwindow reports idle display sleep is no longer blocked. |
| 04:36:17.781–17.914 | Screen saver triggers lock; session screenIsLocked becomes1. |
| 04:38:03 | Owned CARLA process starts (PID11421). |
| 04:38:35 | Owned Driving Control starts (PID11769). |
| 04:38:35.601–36.702 | Five workspace AppleScript probes execute while locked. Event log shows initial reads, not successful size/position writes. |
| 04:38:36.178 | Workspace records restore attempt; this field is not placement proof. |
| 04:38:36.721 | Start simulator reports COMPLETED. |
| 04:38:44.789–44.865 | Session screenIsLocked becomes0; unlock notification follows. |

Thus the only initial auto-placement attempt preceded unlock by about8seconds.
The failure is localized to locked-session window access, not the geometry
calculation or absent simulator/controller processes. The exact original
AppleScript error/count remains unavailable because the operation did not retain
the workspace result; do not invent its numeric error or window count. The
current System Settings UI shows Accessibility and System Events Automation
enabled for the responsible app; no permission toggle was changed.

Source inspection confirms that native Presenter restores its own windows at
startup/SIGUSR1 only; there is no unlock-triggered retry of third-party windows.
`source.py` returns a nested workspace result while keeping simulation RUNNING,
and `presenter_operations.public_result` drops that nested result. A non-live
fixture using the existing mapper confirms that internal workspace INCOMPLETE
becomes public operation COMPLETED with only RUNNING visible. This fixture is
not claimed as a replay of the missing original error.

Recommended correction is layout-only: expose bounded placement state/problems,
defer placement while locked and retry after an unlocked/ready session, reconcile
actual rectangles before claiming placement, and provide an explicit recovery
action without a simulation restart. Preserve process ownership/uniqueness
checks and never weaken macOS security settings. No runtime/source correction,
permission change, Cloud call, service action or VM/simulation restart occurred
in this investigation. Final native view remains Safe Stop0km/h, Not assigned;
the new clean cycle remains paused before service preparation/publication.

#### T10 correction and unchanged-process verification

The operator subsequently authorized the bounded correction. Implemented in
the existing workspace owner, native screen probe, Presenter session projection
and UI; no Gateway, service, Factory or AosCore change:

- A locked/inactive desktop defers placement. The Presenter server continues
  the pending layout after unlock without consuming readiness attempts while
  locked. Unknown desktop state fails closed.
- Missing windows/geometry get at most three follow-up attempts. Each attempt
  re-resolves current-run process ownership; an ambiguous window, permission
  error or unclassified failure does not loop. Closing the native Presenter or
  changing the run cancels automatic recovery.
- Actual positions are retained separately from the simulator's successful
  startup. A bounded public layout summary appears in Session and as a warning
  while incomplete/deferred. Restore window layout is a fixed confirmed action,
  with no browser-selected PID, path or lifecycle target. An active restore
  does not label an earlier verified placement as its current success.
- Existing operation exclusion and journal locking serialize layout recovery
  with lifecycle work. No security settings are changed.

Local gates: 1,017 orchestrator tests ran (1,001 passed, 16 skipped), including
20 workspace tests; targeted Presenter suite37 passed; final UI suite284 passed;
125 browser fixture tests passed before the final wording/active-feedback-only
adjustment. Final targeted feedback tests and TypeScript/Vite build passed.
The changed Swift helper compiled and read the real unlocked desktop correctly.
Locked→unlocked, no-mutation-while-locked, bounded readiness failure, permission
denial, ambiguity, run replacement, closed Presenter, idempotence and public
redaction were tested with isolated fixtures. The Mac was not deliberately
locked for live testing; do not claim a fresh physical lock/unlock experiment.

Only the idle Presenter server and its changed native host were reloaded.
Two Restore actions were then submitted and observed through the real UI:

| UTC start → finish | Result | Duration |
| --- | --- | --- |
| 05:38:08.561490 → 05:38:13.768316 | Verified; no problems; includes native-host compile/reload | 5.207s |
| 05:39:57.360934 → 05:39:58.534998 | Verified repeat; same native owners | 1.174s |

On the current2056×1220 visible desktop, observed versus requested rectangles
are CARLA `[8,131,911,612]` versus `[8,131,914,612]`; Driving Control
`[8,751,914,502]` versus `[8,751,914,500]`. Native rounding/minimum-size differences
are within the existing3px tolerance. Header `[8,47,2040,76]`, right panel
`[930,131,1118,1120]` and background `[0,39,2056,1220]` match exactly.
CUA screenshots confirmed the resized road view and complete controls/telemetry.

CARLA PID11421 (started04:38:03UTC) and Driving Control PID11769
(started04:38:35UTC) did not restart. Presenter host31824 was reused by the second
action. The source run remains `a76dadd7-b3dd-448f-9ae5-2e1670d37a7c`;
native telemetry still shows Safe Stop,0km/h, Not assigned. Test remains
MANUFACTURED without a Cloud Unit. No provisioning, publication, driving or
service action was performed. This closes the observed T10 placement defect,
not the paused fresh-cycle E2E or broader P8 qualification. Source changes remain
uncommitted in the existing mixed worktree; no unrelated changes were staged.

#### T10 follow-up: native z-order, approved and exercised

The operator reported a separate longstanding symptom: Presenter can cover
CARLA/Driving Control until each is clicked. The original code ordered the
background once and never verified the resulting stack; application activation
followed initial restore, without a post-activation ordering check. This is a
confirmed implementation gap, not a claim that every historical overlap had
one recorded cause. Positions alone cannot qualify visibility.

The native host now observes front-to-back window-server metadata and checks
the background against every observed owned demo window. Restore, application
activation, key/main-window and Space changes schedule a post-event check;
a one-second metadata-only watchdog covers missed events. A repair only moves
our normal-level, nonactivating, mouse-transparent background behind the group.
It does not activate/raise CARLA, Driving Control or unrelated apps, change
their levels, reposition windows continually or implement always-on-top mode.
Each unresolved episode has at most three repair attempts. Current generation,
host PID and a15-second evidence age bind the private local ordering receipt;
the browser receives only state/time/repair count. Missing/stale/incorrect
order prevents a geometry-only success. Relevant AppKit semantics are documented
by Apple under [window ordering](https://developer.apple.com/documentation/appkit/nswindow/order(_:relativeto:))
and [orderBack](https://developer.apple.com/documentation/appkit/nswindow/orderback(_:)).

Live proof preserved the same native simulator/control processes and Test:

- First updated restore05:50:43.628609–05:50:47.163394UTC: order VERIFIED,
  no repairs needed. UI showed both geometry and order confirmation.
- A transient one-shot launch hook tried ordinary `orderFront`; it did not
  produce a recorded violation. This attempt is not counted as repair proof.
- The controlled follow-up used `orderFrontRegardless` on our background only,
  then the normal guard. The05:57:26.225740–05:57:29.694491UTC action completed;
  native host36919 recorded exactly one BACKGROUND_ABOVE_DEMO→VERIFIED recovery.
  No CARLA/Driving Control click or process restart was used to recover.
- The transient hook was removed from source and the installed native host
  rebuilt via the normal UI Restore action. The final05:59:13.274228–
  05:59:17.637777UTC action completed in4.364s; host37472 reports VERIFIED with
  zero induced repairs. The live UI explicitly displays verified window order.
  CARLA11421 and Driving Control11769 retain their original start times.

The final source has a regression assertion excluding the transient hook and
`orderFrontRegardless`. Additional tests cover order receipt generation/PID/age,
geometry-only false success, recovery to current order, no peer-activation APIs
in the guard, and suppression of old success during a new restore. The tested
guard is active; the broader fresh-run UI E2E remains paused and unprovisioned.
No Cloud, VM, driving mode, service, Factory or macOS permission changes occurred.

Final z-order regression gate:1,020 orchestrator tests ran (1,004 passed,
16 skipped), including23 workspace tests;284 UI unit tests and125 browser
fixture tests passed. TypeScript/Vite and native Swift builds passed, as did
`git diff --check`. The scratch compile binary in `/private/tmp` was removed;
the installed native host contains no deliberate-fault hook. No commits/pushes
or unrelated cleanup were performed during this bounded correction.

### Resumed clean UI cycle after T10 (20 September, completed)

The operator authorized continuation of the agreed staging-only plan, including
the version cycle, corrections, regression and final checkpoint, without routine
questions. The preserved manufactured Test and native scene were reused. All
scenario actions below use Presenter/native Driving Control, not CLI substitutes.

| Action | UTC click | UI-confirmed outcome |
| --- | --- | --- |
| Publish VDP94/V1 | 06:11:16.264 | Receipt completed06:11:22; Provision became the next step before any recipient existed. Confirmation named selected staging and OEM role. |
| Provision | 06:11:54.997 | Completed06:12:25; Online, existing source attached in stationary Manual. |
| Safe Stop / VDP94 | 06:12:38.833 | Installed94, no pending update at06:13:00 observation. |
| Prepare / publish Brake73/V1 | 06:12:54.544 / 06:13:26.803 | Prepare completed06:12:56; publish completed06:13:36. Refresh publication read READY; no second upload. |
| First Brake assignment | 06:14:29.696 | Completed06:14:43; active73 and then RECEIVING. Initial AWAITING_INPUT did not claim denied access. |
| Brake V1 maneuver | 06:15:20.806 | Complete75-sample window, PRE30/ACTIVE25/POST20,8/8chunks, zero missing indices. Source06:15:28, receipt06:15:36; real charts inspected06:15:51. |
| Publish VDP95/V2 | 06:16:48.032 | Receipt5s; remained pending over installed94 while native Autopilot19.4km/h. |
| Safe Stop / VDP95 | 06:17:20.554 | Installed95 confirmed by06:18:18. A V1 capture interrupted by FOTA honestly reports source gap; earlier complete window remains. |
| Prepare / publish Brake74/V2 | 06:18:11.107 / 06:18:49.152 | Cloud active74 at06:19:10, native motion observed during replacement; no Deploy or Safe Stop for SOTA. |
| Brake V2 maneuver | 06:19:28.826 | MONITOR40, source06:19:44/receipt06:19:45. Old V1 result not relabelled V2. |
| Second V2 maneuver | 06:20:29.864 | INSPECTION_RECOMMENDED34, source/receipt06:20:44, retained for V2-to-V3 inheritance proof. |
| Prepare / publish Tire42/V1 | 06:19:57.115 / 06:20:55.428 | READY; assigned once06:21:47.990 while VDP V2 still installed. |
| Early Tire | — | Cloud active42 at06:22:03; service detail says VDP V3 required / VDP V2 installed. No invented assessment; input STALE. |
| Publish VDP96/V3 | 06:23:49.403 | Pending while native Autopilot19.3km/h. |
| Safe Stop / VDP96 | 06:24:16.092 | Installed96 visible06:24:39; Tire source report06:24:21 RECEIVING and native Monitoring observed06:24:48 without redeploy. Brake V2 correctly remains Waiting for service on native advisory. |
| Prepare / publish Brake75/V3 | 06:24:25.920 / 06:25:32.099 | Preparation/publish accepted; keep stationary to distinguish inherited warning from a new driving assessment. Qualification continues. |

Resource baseline: first Resources opening said Waiting for the first Cloud
resource observation, not No sample. CPU569DMIPS source06:21:08/read06:22:13;
RAM380858368 with explicitly unspecified unit source06:21:43/read06:22:21.
These independent samples will be compared after OFF/ON; unknown RAM units
are not guessed. Brief post-FOTA last-known service inventory was observed
06:24:39 and current again by06:24:52; investigate only with its underlying
observation classification, not by suppressing legitimate incomplete reads.

Observation times are upper bounds. Individual tool calls occasionally took
longer before returning; that is not by itself a measured product delay.
At the checkpoint above V3 advisory, reset, OFF/ON and Finish were still open;
the continuation below supplies those observations. No Factory/AosCore change occurred.

### Final continuation and results (06:26–06:46 UTC)

| Check | Action / observation UTC | Confirmed result |
| --- | --- | --- |
| V2 condition inherited by Brake V3 | No maneuver after Brake75 activation; inspected06:26:45 | Native Inspection recommended while no new75 assessment exists. Current75 function report and advisory SET/APPLIED record inspected06:26:53. Historical74 result is not relabelled75. |
| Tire maneuver | Click06:27:51.385 | Tire69/100, source/receipt06:28:05; Brake also assessed its real physical braking,26/100 at06:28:07. Both native warnings; ACK confirmed. |
| Independent Tire reset | Click06:28:36.108 | CLEAR06:28:41, native Tire Monitoring; Brake warning retained. No invented GOOD result. |
| Independent Brake reset | Click06:29:38.924 | CLEAR06:29:40; both Monitoring by06:29:57. Retained history remains inspectable. |
| Return to road | Click06:30:39.136 | Lane-aligned stationary Manual by06:31:03, no automatic Autopilot or model reset. This attempt started stationary, not from a live collision. |
| External OFF | Click06:31:13.218 | Native OFF and local control continue. Backend source/receipt stops; Cloud OFFLINE visible06:35:18.981. This sparse observation only bounds the transition, not its exact latency. |
| Fresh offline results | Brake maneuver06:31:53.501; Tire06:35:18.981 | After the earlier confirmed resets, both native warnings are visible06:35:39.569 while backends still show pre-OFF data. Not merely an old warning surviving disconnection. |
| External ON | Click06:36:27.990, after314.772s OFF | Tire source06:35:33 received06:36:38; Brake source06:35:34 received06:36:49. Queues0/current RECEIVING and Cloud ONLINE visible06:37:09. No manager/VM/simulator restart. |
| Same-profile repair | Prepare click06:37:36.006; publish76 click06:38:28.844 | Brake V3/76 active by06:38:48. Car remains stationary; native warning and current76 confirmed ACK remain through06:40:14, beyond the old lease. No second Deploy. Previous75 reset is correctly historical, not a new76 reset. |
| New result after repair | Maneuver06:42:31.097 | Brake76 assessment26/100 source/receipt06:42:46; current ACK confirmed and native warning. Software story complete. |
| Cloud resources after reconnect | CPU read06:43:15; memory06:43:26 | Both source06:42:43, later than pre-OFF samples. CPU960DMIPS; memory408850432 with explicitly unspecified unit. No repeated frozen sample in this run. |
| Finish | Operator confirmed exact irreversible scope; clicked06:45:07.233 | Trace shows RUNNING, then Demo finished. Empty initial UI recorded06:46:05.199: Not assigned, No controller created, empty service/VDP slots, No Cloud Unit yet.58s observation upper bound; no30-minute wait or CLI cleanup. |

The current staging Test, its local working VM/data and scoped backend data were
retired by the confirmed Finish operation; this deletion is not recoverable.
Factory.35/.36 originals, published releases and release continuity remain.
No fresh Test was created afterwards. The normal selector defaults to.35;
the .36 qualification image remains separately selectable and is not silently
promoted by this report.

### T11–T12: bounded corrections from the resumed run

- **T11a, history wording:** the empty Tire view advertised earlier results
  when its bounded history contained only service/status records. The helper
  now checks product record types; otherwise it says Service records remain
  in Records. It does not invent an assessment or alter current-result proof.
- **T11b, advisory explanation:** V2-to-V3 and V3-to-V3 inheritance passed, but
  no-current-release-result copy did not explain why native warning can remain.
  A shared conditional explanation now states that Brake V3 *can* continue
  advisory from retained state before a new assessment. It is not a claim of
  active warning, exact historical provenance or a new result. The native
  dashboard remains authoritative. Current input/binding and reset state gate
  the explanation; stale/invalid/reset-pending states retain their diagnostics.
  The live76 dialog displayed it before the next maneuver. Compact summary
  layouts retain their existing rules for hiding long secondary explanations.
- **T12, post-Finish layout:** after expected CARLA/control shutdown, the old
  placement receipt becomes unverified and incorrectly offered recovery on the
  empty Vehicle screen. A confirmed absent controller/run plus STOPPED or
  NOT_PREPARED source now suppresses that obsolete warning. Session explains
  that no vehicle-window recovery is needed. Partial/unknown lifecycle, a live
  simulator and an actual Restore operation keep normal warning/progress.
  No placement, focus, process or z-order policy changes are made.

Each reproduced defect first failed an isolated test. Final local gates:
292 Presenter unit tests;125 full browser cases before T12 plus48 affected
lifecycle/dialog cases after T12; TypeScript/Vite build;1,020 orchestrator tests
(1,019 passed, one environment-dependent skip). The earlier16-skip result used
a different Python environment; the project venv covers those crypto cases.
No runtime fixture or mocked product is counted as live E2E evidence.

Final empty-screen activation was also inspected in the live Presenter: no
obsolete layout warning; Session explains the stopped vehicle windows.
Additional source checkpoint gates passed:352 solution tests,104 contract/mockup
tests with four explicitly opt-in browser skips,47 targeted Gateway tests,
native Driving Control Swift typecheck and two Platform ordering tests.
The first root-suite interpreter lacked PyYAML; rerunning with the existing
configured interpreter passed without changing dependencies. The Swift
typecheck used the existing writable module cache after the default cache
was sandbox-denied. Neither harness issue was a product defect.
Documentation validation passed242 Markdown files,658 stable IDs and38 Mermaid
diagrams. Outgoing/staged source blobs in the seven public repositories passed
the private-key/token, artifact-size and artifact-extension scan; the solution
confidential-input guard also passed. Preserve exact contract bytes and unified
patch context: the staged whitespace check notes two contract EOF blank lines
and two required blank context lines in the upstream regression patch.

The completed source checkpoint and subsequent authorized artifact cleanup are
recorded in the [checkpoint receipt](source-checkpoint-and-cleanup-2026-09-20.md).

### Remaining boundaries after the clean operator cycle

The main version/product/advisory/reset/offline/Finish sequence passed.
This report does not claim zero possible side effects or blanket P8 closure:

- full guest reboot is the separately agreed engineering check, with existing
  host-managed volatile credential restoration requirements;
- live collision/off-road/occupied-spawn recovery and every response-loss,
  double-click/reset-expiry/conflict variant are not all exercised here;
- quantitative calibration counts and byte-by-byte offline outbox accounting
  belong to their explicit proof matrix; UI source/receipt/queue observations
  do not replace them;
- the earlier intermittent source-input gap did not recur as an outage here;
  that does not establish its root cause. Resource sampling resumed normally;
- post-FOTA partial inventory and independent catalog-processing observations
  are retained as observations, not hidden or called defects without cause;
- the current completion proof is the actual Presenter receipt and empty UI,
  not an additional direct Cloud inventory/guest audit. Production is untouched.
