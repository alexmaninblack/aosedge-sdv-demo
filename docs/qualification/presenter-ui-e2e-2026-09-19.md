<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI E2E observation run — 19 September 2026

Status: MAIN CONTINUOUS CYCLE COMPLETED WITH FINDINGS; FULL P8 MATRIX REMAINS OPEN.
Started at 20:57 UTC. This is an observation run, not an
implementation or defect-correction pass. Normal Finish completed by 21:57:29
UTC. The observed main path passed; UI findings and excluded matrix branches
remain explicitly open.

## Scope

The operator explicitly requested that the agent execute the end-to-end run
and inspect all UI states and inconsistencies. Actions use the Presenter and
native driving UI. Read-only diagnostics are distinguished from visible UI
evidence. Do not fix defects, retry mutations blindly, or replace failed
evidence during this run. Production and immutable factory images remain
unchanged. Factory .36 is the candidate; .35 remains preserved.

The main path is Create, Start simulator, publish VDP V1, Provision, Safe Stop
and installation, Brake V1/V2/V3 and VDP V2/V3 updates, Tire V1, genuine driving
results and advisory, Reset/Return to road, external network OFF/ON, and Finish.
VM reboot remains a separate engineering check, not a demo chapter.

## Observations

| UTC | Step | Actual UI evidence / result |
| --- | --- | --- |
| 20:57 | Initial state | Existing tab advertised a newer UI. Explicit reload loaded the current interface; no controller and empty service slots. Factory selector reset from .36 to default .35 on reload; .36 selected explicitly for this run. |
| 20:58 | Session / Cloud | Selected Cloud and inspected OEM certificate both report `aws-stage.epmp-aos.projects.epam.com`. No credential contents captured. |
| 20:58:47 | Create | One confirmed Create request for `6.1.1-maninblack.36/main-qemuarm64`. Running progress reports native access available, then serial-console boot readiness; no password prompt required. |
| 20:59 | Progress navigation | While Create is RUNNING, View progress opens Current run activity with `No operations recorded for the current run.` Inline operation details do show Create progress. |
| 21:00:05 | Create completed | Trace reports COMPLETED; approximately 78 s after acceptance. No manual credential entry needed. Next action is Start simulator, not Provision or installation. |
| 21:00–21:02 | Simulator | One Start simulator request. Native panel is LIVE, unassigned, stationary at 0.0 km/h, Safe Stop, both advisory fields Not available. Return to road and both maneuver buttons are present. Guide advances to pre-Provision platform publication. |
| 21:03 | VDP V1 | Prepared candidate 86.0.0 and submitted one Sign & publish through Presenter to the already verified staging session. Cloud installation is not expected before Provision. |
| 21:04 | Provision | One UI request completed; Test ONLINE. VDP86 pending, installed factory placeholder 0.0.0. Native panel selected Test, 0.0 km/h, Manual. Read-only process inspection confirmed CARLA/Gateway/Driving Control start times at 21:00:45/21:01:22/21:01:23, preceding Provision; no second launch. |
| 21:05 | VDP installation | Native Safe Stop clicked once. Presenter reports Cloud installed 86.0.0 and advances to Brake V1. Cloud monitoring subsequently lists VDP86, root filesystem .36, boot firmware 6.1.0, no services. |
| 21:05:44 | Brake V1 Prepare | BLOCKED: `SERVICE_COMMITTED_SOURCE_REQUIRED`; no candidate prepared, no service upload or assignment. Read-only inspection finds six changed tracked files in each service repository, including missing-token classification and tests. |
| 21:06 | Local driving | Autopilot is visibly MOVING at 15.3 km/h. Both advisories remain Not available, appropriate for VDP V1 and no installed services. |
| 21:07–21:08 | Preserved checkpoint | Native Safe Stop confirmed, 0.0 km/h and Brake 100%; external network ON. Test/Cloud identity/simulator retained. No retry, source edit, commit, push or cleanup performed. Approval requested for reviewing/testing and locally committing only the existing service fixes before resuming the same run. |
| 21:07–21:08 | Cloud resource dialog | CPU displays 504 DMIPS with distinct sample/read timestamps. Memory displays raw `363102208 · unit not specified`, with explicit warning that Cloud has not supplied a verified unit. A read transiently changed to `CLOUD_SOURCE_UNAVAILABLE`, retaining previous samples and marking them last known. Not represented as a guest Offline transition. |

## Findings — collect before correction

| ID | Severity | Finding | Evidence / impact |
| --- | --- | --- | --- |
| E01 | Medium | View progress / Trace does not expose the active first Create operation. | The guide directs the operator to Trace, but the dialog says no operations recorded. Inline expandable details remain available; creation itself is not shown to have failed. |
| E02 | Low | Empty, unprovisioned Brake dialog describes incomplete product history and earlier results. | Before first service installation: `Current Test identity not observed in Cloud`, `No result yet`, followed by `Product history is incomplete` and `Earlier results remain in Records`. No earlier result in this new run is established; copy should distinguish not started/not queried from an incomplete result. |
| E03 | Blocking prerequisite | Neither service can be prepared from its current dirty source checkout. | `service_build.py` rejects nonempty `git status --porcelain` before building. Brake and Tire each have six modified tracked files. This is an intentional reproducibility guard, not a Cloud permissions or deployment failure. Existing changes distinguish `KUKSA_AUTH_PENDING` from Access denied. Review/test/commit authority is needed; do not bypass the guard or silently publish old code. |
| E04 | Medium | Blocked Prepare offers no actionable recovery guidance. | UI shows the raw error code and a normal `Prepare this service profile` / `Next software profile` guide; the receipt has empty facts. It does not explain that an engineering source checkpoint is required and retrying unchanged cannot succeed. |
| E05 | Engineering setup dependency | UI Prepare does not build a missing committed service product. | After the source checkpoint, it returned `SERVICE_BUILD_REQUIRED:democtl service build brake --content-profile v1`. This may be a deliberate operator/developer boundary, but the required prebuilt profiles must be part of documented preflight; UI gives only a raw CLI instruction and no build action. |
| E06 | Medium / usability | Publication confirmation hides the concrete Cloud destination. | The confirmation shows `Configured Cloud publication context` and `configured Service Provider`, but not the selected staging domain or SP identity. The endpoint can be verified separately in Session, yet this consequential confirmation should make its actual destination directly apparent, especially across Cloud instances. No wrong-destination publication was observed. |
| E07 | Low | Tire missing-input explanation uses Brake recording terminology. | Early Tire40 on VDP V2 correctly reports no result and `STALE / SOURCE GAP`, but the helper says `Waiting for fresh input before the next recording.` Tire produces assessments, not the Brake V1 recording product. Its installed-service dialog correctly identifies the missing VDP V3 profile. |
| E08 | Medium / layout | Architecture bottom is clipped in the current browser viewport. | At the unchanged 1327×923 browser size, the sticky story panel covers the lower Factory firmware selector and Gateway subtitle. The controls exist in AX but are not all visible simultaneously. This is a viewport-specific observation, not a claim that the native Presenter window has identical geometry. |
| E09 | Medium / discoverability | Existing Brake telemetry charts are difficult to find after an upgrade. | The operator explicitly could not find the charts. They exist in Brake backend → Records → a V1 `WINDOW_COMPLETION` record, several pages behind V2/V3 events. On the live run the complete 76-sample recording required page 4. Technical record names and two-record pagination obscure the feature; latest V2/V3 assessment detail does not expose a comparable history graph. No chart was fabricated or added during this audit. |
| E10 | Low | Post-reset explanatory sentence ignores the reset boundary. | Correct heading `No new result after reset` is followed by `No result for release 69.0.0 yet` (also Tire40), although that release already produced retained results. The sentence should scope absence to the latest reset, not imply the release has never worked. |
| E11 | Medium / context | Cloud monitoring's Software dialog omits the Unit Offline context. | Architecture correctly reports Offline, but the opened dialog shows service `active` and a fresh `Cloud checked` time without repeating Offline or an explicit last-unit-report qualifier. These are genuine retained Cloud values, not proven live process observations. The separate service detail disclaimer helps, but the aggregate modal can still be misread. |
| E12 | Investigation / data freshness | Resource source samples are much older than the successful Cloud read. | At 21:50 UTC, CPU/RAM source sample is 21:07:57 while the read is 21:50:21. UI explicitly labels last known and shows both timestamps (correct); it must not be accepted as current resource telemetry. This audit has not yet localized whether the unchanged sample originates in Cloud data, query selection or guest reporting. No inferred RAM unit is introduced. |
| E13 | Low / context | Completed-reset copy hides the current disabled reason and lacks its historical time. | While Offline, Reset is correctly disabled, but its nearby explanation still says `Scenario reset · Gateway confirmed CLEAR` rather than explaining the missing reset-channel contact. The same sentence remains after a subsequent warning has been generated. The separate top-line `not recent` is truthful; the local button explanation should distinguish historical success from current availability. |
| E14 | Medium / completion visibility | Open Trace empties on successful Finish instead of showing its terminal outcome. | The active Finish trace showed Cloud Offline/deprovisioning/Unit-and-Node absence, then became `No operations recorded for the current run.` Closing it revealed `Demo finished` and the correct empty initial screen. Retain a clear completion acknowledgment within the already-open modal; this does not require retaining deleted runtime data. |

## Completion gates

### Authorized continuation

The operator explicitly authorized reviewing/testing and locally committing the
existing Brake/Tire source changes, then continuing this same E2E run. No new
product changes or push were authorized/performed. Both diffs passed whitespace
and scope review. Warm native compilation and all eight Brake/five Tire CTest
groups passed, plus seven/five Python subscription wiring checks respectively.
Local commits: Brake `4f75373`, Tire `20e6a23`. Both service worktrees are clean.
At 21:12:32 UTC one new UI Prepare Brake V1 request was submitted after closing
the exact prerequisite; the earlier blocked attempt had produced no candidate
or external publication. The Test, VDP86 and simulator are preserved.

That request returned `SERVICE_BUILD_REQUIRED` before candidate allocation.
The existing supported `democtl service build` path is used to build all four
required products (Brake V1/V2/V3 and Tire V1) against these commits. This is a
recorded engineering-preparation CLI exception, not UI-only proof; signing,
publication, installation and result checks remain through the UI. No source
correction or new lifecycle action is added.

All four production ARM64 builds completed successfully by 21:15:37 UTC,
including their package CTest gates and binary/provenance validation. At
21:16:15 the same UI preparation was submitted once after this second exact
prerequisite was resolved. Autopilot was visibly moving at 19.3 km/h during
preparation; component installation had already completed, and no subsequent
Safe Stop was used during local service preparation. Service delivery has not
yet occurred.

UI prepared Brake V1 as 67.0.0. The first Sign & publish click was rejected by
execution safety **before submission** because this exact new release/payload
was not covered by the older exact-release upload confirmation. No alternate
tool/path or repeated publication was used. The unsubmitted dialog was closed.
Remaining candidates are being prepared through UI without signing/uploading
so the operator can approve one exact list: Brake V2 68.0.0, Brake V3 69.0.0,
Tire V1 40.0.0, VDP V2 87.0.0 and VDP V3 88.0.0. Publication/installation
must subsequently remain ordered, not bundled into a single unobserved jump.

All six preparations are complete. One explicit grouped approval request names
the exact releases above, selected OEM/SP signing, destination
`aws-stage.epmp-aos.projects.epam.com`, and sequential installation on the
current Test. Until approval, no publication retry is made. The Test remains
Online with VDP86 and no services; native Safe Stop was requested while waiting.
UI guide correctly returns to the retained Brake V1 candidate 67 rather than
the more recently prepared V3 candidate 69. Package details confirm V1/67,
ARM64, Native inputs, minInstances 1, P7D, Not published, Not signed.

The operator explicitly approved the full six-package list and sequential Test
installation. At 21:24 UTC one Brake67 Sign & publish request was accepted in
Presenter; the preceding rejected click had not executed. Native Autopilot is
resumed before first service assignment to exercise the no-Safe-Stop SOTA path.

### Live service and version observations after approval

- 21:25: Brake67 publication READY. One first Deploy used its dedicated Subject;
  21:26:22 Cloud showed installed 67.0.0, one active instance, while native UI
  showed Autopilot MOVING at 19.3 km/h. No Safe Stop was required for SOTA.
- Brake details show Compatible / VDP V1 from Cloud/package evidence and
  explicitly separate installation from input/results. Initial function report
  WAITING/AWAITING INPUT did not become Access denied; subsequent report was
  RECEIVING/NONE. V1 Reset correctly unavailable and advisory NOT SUPPORTED.
- A native Brake maneuver produced a COMPLETE V1 window, source 21:27:20,
  backend receipt 21:27:28. UI reports 75 samples, 8/8 chunks, zero missing
  indices, PRE29/ACTIVE26/POST20. Actual samples/graphs are inspectable, no
  condition score is invented. Modal fits the current viewport. Native maneuver
  finished stationary Safe Stop with a consistent banner. Both advisories are
  still Not available, as expected for VDP V1.
- Autopilot explicitly resumed. At 21:28 UTC VDP87/V2 publication submitted
  once, retaining Brake67/V1 for the component-transition recovery check.
- VDP87 stayed Pending while native Autopilot was MOVING at 19.3 km/h, with
  VDP86 still installed. After explicit Safe Stop, Cloud reported VDP87/V2.
  Brake67 remained installed and its function report returned to RECEIVING.
  A window spanning replacement correctly reports source gap (42 samples)
  separately from complete delivery (5/5 chunks); this is not called a complete
  source recording. Prior records remain available. A new native Brake maneuver
  was started after recovery, without redeploying the service.

- The recovered V1 maneuver completed with 76 samples and 8/8 chunks, source
  21:30:47 and receipt 21:30:54. History remained available and Vehicle summary
  agreed with backend details. Autopilot was explicitly resumed.
- At 21:34:30 Brake68/V2 publication was submitted once during visible motion
  (19.4 km/h). Cloud reported one active 68.0.0 instance by 21:34:54, without
  another Deploy or Safe Stop. Its backend correctly showed current inputs but
  no result yet for release 68; seven earlier V1 records remained in Records.
  V2 Reset and advisory were correctly unsupported. A native Brake maneuver
  was started at 21:35:08 for the first actual V2 assessment.

- Brake V2's real maneuver produced MONITOR, score 40, at 21:35:24; durable
  receipt had the same displayed second. Current-release identity was 68.0.0.
  `VALID_DEMO_SYNTHETIC` / `DEMO_SYNTHETIC` is the existing model contract,
  not evidence that a mock-input package was deployed. V2 advisory remains
  NOT SUPPORTED. Native maneuver ended in Safe Stop; Autopilot resumed.
- Tire40/V1 publication READY; one first assignment to its separate Group
  Subject completed with one active instance by 21:37:36. No Safe Stop or peer
  reassignment. On VDP V2 the service dialog says VDP V3 is required; backend
  has no assessment and reports stale/source-gap input, not Access denied or
  an invented compatible profile. VDP88/V3 publication was submitted once at
  21:38:25 to test automatic recovery without another Tire Deploy.

- VDP88 remained Pending at 21:39:23 while actual motion was 19.4 km/h.
  Explicit Safe Stop at 21:39:35 led to Cloud-installed VDP V3 by 21:39:50.
  Tire40 automatically changed to RECEIVING without service redeploy. Native
  Tire showed Monitoring; Brake68/V2 showed Waiting for service for advisory,
  while its backend retained the MONITOR assessment. Brake69/V3 publication
  was submitted once at 21:40:24 after explicitly resuming Autopilot.

- Brake69/V3 replaced 68 with one active instance by 21:40:53, while native
  Autopilot was moving at 19.4 km/h. No new Deploy or Safe Stop. Earlier V1/V2
  records remained available. A real Brake maneuver started at 21:41:08;
  current-release assessment, event and advisory fact were durably received
  at 21:41:24. Detailed result/native advisory verification is next.
- At the operator's request the V1 complete window received 21:30:54 was
  opened again: 76 actual retained samples, PRE30/ACTIVE26/POST20, 8/8 chunks,
  speed and brake-pedal charts, no interpolation. This visibly proves that
  historical V1 window detail survived both service upgrades.

- Brake69's assessment was INSPECTION_RECOMMENDED, score 34, with CONFIRMED
  advisory ACK and matching native indication. Tire40's first normal-driving
  result was GOOD, score 92. A native Tire maneuver at 21:44:34 produced
  INSPECTION_RECOMMENDED, score 67, source/receipt 21:44:48 and CONFIRMED ACK;
  both native warnings were visible together. Planned reauthentication was
  separately visible and recovered; it did not replace the condition result.
- Tire-only Reset submitted at 21:45:08 progressed through submitting and
  waiting for Gateway CLEAR; the function report at 21:45:17 and subsequent
  dialog confirmed CLEAR. Tire native returned to Monitoring; Brake warning
  remained. UI showed No new result after reset, not a fabricated GOOD result.
  A second real Tire maneuver regenerated its warning. Brake-only Reset was
  submitted at 21:46:12 for the converse isolation check.

- Brake-only Reset confirmed CLEAR (function source 21:46:16). Native Brake
  became Monitoring while Tire retained its warning. Both reset paths expose
  pending versus confirmed outcomes and preserve history.
- Return to road was exercised from stationary Manual at 21:47 UTC. Native
  UI completed `On road · stationary Manual · select Autopilot when ready`;
  CARLA screenshot visibly shows a lane-aligned car at a clear position.
  Brake Monitoring/Tire warning were unchanged. Explicit subsequent Autopilot
  produced actual 19.3 km/h motion. This does not qualify an occupied spawn,
  collision/off-road starting position or lost-response negative branch.
- External network OFF requested at 21:47:50, visibly OFF by 21:48:03. Native
  controls and advisory remained live. Last Brake function source/receipt was
  21:47:46.896/.907; no post-reset result at disconnection. A genuine Brake
  maneuver was started offline at 21:48:10 to generate a new local result.

- Cloud Offline visibly confirmed by 21:49:18, within about 88 seconds of
  the OFF request (not an exact transition latency). Backend input/activity
  moved to Last known / Not confirmed; reset disabled once contact aged out.
  Tire last function source/receipt stayed 21:47:43.820/.833, product receipt
  21:45:54, with 25 records at 21:49:50. Brake retained no post-reset result.
- Two genuine offline Brake maneuvers generated a new native Inspection
  recommended indication by 21:49:43 while backend remained unchanged. Tire
  warning remained valid locally. A Tire maneuver was then run offline as well.
  Cached backend condition is kept separate from unconfirmed current input.

- Offline was held for over five minutes (request 21:47:50; reconnect request
  21:53:17). At 21:53:08 Brake's function source/receipt still remained
  21:47:46.896/.907 and no new result appeared. Native Brake/Tire warnings
  remained active well beyond their advisory lease interval. Individual token
  rotation events were not instrumented; this is functional offline evidence,
  not a token-file or exact queue-digest proof.
- Immediately after reconnect, Brake's actual offline assessment appeared:
  source 21:50:10, received 21:53:23, score 26 / Inspection recommended.
  Presenter did not replace its original source time with receipt time. Initial
  delayed product delivery coexisted with last-known function data and Cloud
  Offline; these independent observations were not forced into one status.

- At 21:54:19 Brake reported current RECEIVING, IDLE/0 queued and CONFIRMED
  advisory ACK. At 21:54:27 Presenter visibly confirmed Cloud ONLINE again;
  no VM, CM, service or simulator recovery restart was used and no 30-minute
  wait was needed. Tire then showed its offline result with source 21:50:09,
  receipt 21:53:36, score 67, current RECEIVING, IDLE/0 and CONFIRMED ACK.
  These UI observations demonstrate backlog recovery and preserved event time,
  not exact-once canonical-digest verification of every queued message.

The continuous run has reached VDP V3 / Brake V3 / Tire V1 with both real
advisories, independent Reset, basic Return to road and recovered OFF/ON.
Normal Finish confirmation was opened at 21:55 UTC and explicitly disclosed
permanent/no-backup removal of owned Test Unit, working files and scoped backend
data. The operator then supplied exact approval. One Finish was submitted at
21:56:40. Its UI trace showed simulation/VM/backend shutdown, Subject
reconciliation, Cloud Offline and deprovisioned confirmation, membership removal
and Unit/Node absence, followed by scoped cleanup. By 21:57:29 the acknowledgment
said Demo finished; no assigned vehicle, no Cloud Unit, empty service slots and
Create controller were visible. This is a less-than-one-minute observed bound,
not a precisely instrumented duration. No 30-minute Cloud wait occurred.

Afterward both backend dialogs showed setup preview and no stale retired-Test
result. Factory .35/.36 remain selectable, .36 stays selected, and published
releases/version continuity are preserved by the accepted Finish workflow.
Working Test/Cloud identity and scoped backend data were permanently removed,
without backup as explicitly confirmed. Production was untouched. The Presenter
is left open at the initial state; no new run was started.

## Acceptance summary

| Gate | This run |
| --- | --- |
| Fresh .36 Create and detached simulator | Observed via UI; native stored VM access worked. |
| Publish VDP before Provision | VDP86/V1 ready before first provisioning. |
| Provision without restarting simulator | Observed; bounded process-start evidence supports no duplicate launch. |
| Component V1 → V2 → V3 | 86 → 87 → 88; both updates held during motion and installed after native Safe Stop. |
| Brake V1 → V2 → V3 | 67 → 68 → 69; later versions replaced the assigned service without Deploy/Safe Stop; historical V1/V2 products remained accessible. |
| Version-specific real results | V1 complete source window/graphs; V2 MONITOR 40; V3 inspection warning; native Tire inspection result and warning. |
| Early Tire | 40 installed on VDP V2; no false assessment; recovered automatically after VDP V3. |
| Independent Reset | Pending and confirmed CLEAR observed for each; no fabricated GOOD result; peer advisory retained and warnings regenerated through real maneuvers. |
| Return to road | Stationary Manual → lane-aligned stationary Manual; explicit Autopilot resumes motion; model/advisory retained. |
| External OFF | Cloud Offline; frozen backend source/receipt times; no-current-function wording; fresh Brake warning generated locally and both warnings retained beyond five minutes. |
| Reconnect | Cloud Online and both current function reports/zero queues without restart; delayed real products preserve original source time. |
| Finish | Completed after exact approval; Cloud retirement/absence in Trace, Demo finished acknowledgment, empty slots and setup-preview dialogs. |

This is **not a pure UI-only run**: committed product compilation used the
explicitly recorded CLI preparation exception. All live publication, deployment,
driving, reset and connection actions above used Presenter/native controls.
No new product defect fixes were made during observation. Only existing service
changes were reviewed/tested/locally committed with explicit approval. No push.

Do not equate this main-path result with full P8 closure. Unexecuted branches
include collision/off-road and occupied-spawn recovery, lost-response/double-click
negatives, reset failure/expiry/conflict, same-profile service replacement,
exact-once canonical queue-digest verification, independent calibration series,
and guest/CM reboot (a separately agreed engineering test). Individual credential
rotation and fresh AVC/process restart-counter proofs were not instrumented in
this UI observation run. No Production change or factory rebuild occurred.
Fourteen findings/observations are retained above. E03 was an intentional
prerequisite resolved by the approved local source checkpoints; E05 records the
remaining engineering-build dependency. E12 is a data-freshness investigation,
not a proved formatting or Cloud defect. The other entries are concrete UI
copy, discoverability, context or layout issues. No new UI correction was
implemented during the run. Review/prioritize these separately before changes.
