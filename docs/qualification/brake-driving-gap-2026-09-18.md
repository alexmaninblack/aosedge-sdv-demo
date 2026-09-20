<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake driving-result and Presenter diagnosis — 18 September 2026

## Scope and checkpoint

Preserve the operator's running staging Test, Factory .35 and Tire V1 release
34.0.0. The starting VDP V3 release was 78.0.0. Do not reset the drive/model, reprovision,
restart CARLA/Driving Control/the VM, or touch Production. The operator
authorized diagnosis and correction of the missing Brake result and misleading
Presenter wording, then explicitly authorized diagnostic Brake V3 release
59.0.0 upload to `aws-stage.epmp-aos.projects.epam.com`.
The operator subsequently authorized a normal VDP update with explicit Safe
Stop for installation and Autopilot restoration afterward. VDP 79.0.0 is now
installed through that authorized path; Factory .35 itself is unchanged.

Brake 59.0.0 source: `90a9e2b1f290303f66ecb1a8239c8e2613cb9c48` in
`brake-health-service`. It adds bounded repeated episode outcomes, a missing
input mask and a one-shot freshness-watchdog event. It does **not** change
model thresholds, capture rules, permissions or quotas. Source was committed
locally for the pinned build; no push is claimed here.

The signed bundle was accepted with HTTP 201, deployment
`a578aaa8-0ff3-4276-917a-ebef1d654923`; subsequent Cloud read reported READY.
The existing Subject assignment delivered the release without another
assignment operation. Presenter Cloud inventory shows Brake V3 59.0.0. Both
service processes remain alive; bounded runtime failure counters show no
allocation or thread-creation errors.

## Confirmed findings

| Boundary | Evidence | Interpretation |
| --- | --- | --- |
| Brake input | Repeated `KUKSA_INPUT_SUMMARY`, `missingMask=4095` | All twelve required values were unavailable simultaneously, not simply a lack of braking. |
| Interrupted episode | `WINDOW_TRIGGERED` at 06:48:09.029162 UTC; `INCOMPLETE_SOURCE_GAP` at 06:48:09.123093 | Brake discarded an interrupted capture; there was no assessment to deliver. |
| Upstream VDP | `VISS source frame is not monotonic` at 06:48:09.123643 UTC, followed by reconnection | The same interruption is visible upstream of the service. The existing branch covers equal and regressing timestamps. |
| Completed episodes | `ASSESSMENT_SKIPPED_INPUT_QUALITY / INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES` at 06:54:59.789944 and 06:57:15.651945 UTC | Some Autopilot stops complete capture but fail the existing wheel-sample qualification. Driving alone does not guarantee an assessment. |
| Backend contact | Current control polls; no new matching Brake assessment | Contact proves the service can reach its backend, not that its telemetry or model result is ready. |
| Tire | Repeated `EXERCISE_COMPLETED` and new backend assessments | Tire's different capture rules must not be used to infer that Brake has a qualifying episode. |

No telemetry payload, credential, JWT, PIN or private-key content was printed
or added to evidence. A separate read-only VISS timing probe closed during
connection setup. The selected Unit role already has its one allowed connection,
so this is consistent with the documented additional-session rejection; the
close alone does not establish its exact reason. The limit was not changed.
The precise equal-versus-regressing timestamp on the live failure is not yet
independently observed. The protocol mismatch below is reproduced locally.

## Reproduced VDP protocol defect and candidate

Gateway `VissSessionProtocol::CollectDueSubscriptionEvents` sends the latest
snapshot on each due time-based interval. If CARLA has not advanced, this can
repeat the same source timestamp and identical values. Provider `BridgeState`
previously treated `timestamp <= previous` as failure, cleared the entire
selected KUKSA subset and raised an exception that forced reconnection.

An isolated before/after reproduction using the original committed Bridge
confirms that an identical repeated V3 frame clears all values before the fix;
the candidate ignores it without publication. The candidate:

- suppresses only complete, identical same-timestamp snapshots;
- does not republish values, advance model time or renew freshness;
- checks the existing freshness timer even if a socket continuously supplies
  duplicate envelopes; a stopped source still becomes unavailable;
- does not use a duplicate to recover an already stale/disconnected state;
- retains fail-closed handling for missing/invalid data, changed values at the
  same timestamp, and actual backward source time;
- logs bounded duplicate counts, not values; logs data-ready only on transition.

This is transport deduplication, not interpolation, a model-threshold change,
a longer timeout, or a new measurement. The operator chose a normal signed
release update. No transient guest override was used.

## Authorized VDP 79.0.0 update and bounded live observation

Platform source commit: `fb1d2b3a2d8e0a12213990b635c873a676d5bf67`.
The packager now includes the changed `bridge.py` as well as the previously
pinned advisory modules. Historical 78.0.0 validation remains supported only
against its exact frozen previous source/tree/module hashes; unknown or altered
provenance is rejected. Source commit is local; no push is claimed.

| Step | Observed result |
| --- | --- |
| Prepare | Demo Control allocated V3 release 79.0.0, 23 read paths. |
| Sign | Selected staging OEM credential; `VERIFIED_RS256`. Signed bundle SHA-256 `314047634838b9d0516406255c8e95795fe212c3e2f65457fe5c6840f28c6299`. |
| Upload | HTTP 201 at 07:14:26 UTC; deployment `ea5719d0-6654-4b1c-b9ae-aae3318f0b1c`. |
| Publication | Cloud READY at 07:14:51 UTC; old 78.0.0 installed, 79.0.0 pending before Safe Stop. |
| Install | Explicit native Safe Stop, visually confirmed stationary with full brake. VDP 79.0.0 entered active at 07:15:08 UTC, slot `a`, process/slot matched, zero restarts, exit status 0, data `REPORTED_READY`. |
| Cloud reconciliation | Presenter Cloud projection at 07:16:11 UTC: Test Online, installed 79.0.0, no pending component. |
| Resume | Native Autopilot restored; visually confirmed moving about 19.5 km/h. Brake Monitoring; Tire retained Inspection recommended. |

Installed `bridge.py` SHA-256 matches the pinned source:
`a84e8feb0bd66964400f43de6f05c947d05daa358202ed153e9ffcf7ec2d2102`.
VM, CARLA, Driving Control and Tire were not restarted; no identity, assignment
or advisory reset occurred.

The bounded provider journal from 07:15:08 through approximately 07:21 UTC
contains 36 duplicate-count reports totalling 462 ignored frames, one CARLA
VISS connection establishment, no non-monotonic-frame error, no stale-timeout
warning and no connection-loss/reconnect warning. This confirms live duplicate
suppression without the previous false reconnect in this observation window.
It does **not** establish that every telemetry discontinuity has been fixed.

Brake 59.0.0 still reports brief `MISSING_VALUE` / `missingMask=4095` events
after the update. Provider readiness returns to READY repeatedly without a
logged reconnect. Source inspection shows that incomplete selected snapshots
also clear values, without the non-monotonic exception; the exact remaining
missing-field cause is not yet established from live evidence. Do not present
that hypothesis as a confirmed diagnosis or relax completeness checks.

Two post-update Brake captures completed at 07:19:54.874492 and
07:20:40.082633 UTC, both with `INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`; neither
produced a new assessment. Tire continued producing completed exercises.
Both service processes remained alive, diagnostic allocation/thread failure
counters were zero, and no post-update Brake watchdog-expiry event appeared in
the bounded projection. Existing backend Brake assessments were still retained
58.0.0 records, not new 59.0.0 results.

Final visual read at approximately 07:25 UTC confirms Presenter VDP V3
79.0.0, Brake V3 59.0.0 and Tire V1 34.0.0, with Test Online. Native Driving
Control shows Autopilot moving at 19.4 km/h, LIVE telemetry and both advisories
Monitoring at that instant. Presenter correctly says Waiting for braking
result / No new result after reset, with recent service contact; it does not
claim that a new Brake assessment has arrived.

## Presenter correction

Vehicle summary and backend detail now share the same evidence distinctions:

- replace `Ready for a new drive` with `No new result after reset`;
- replace `Awaiting drive data` with `Waiting for braking result` / `Waiting
  for drive result` and describe the qualifying episode requirement;
- show recent service **contact** separately, without calling it telemetry
  readiness; a confirmed reset means only correlated Gateway CLEAR;
- select only the team's actual assessment (or Brake window completion) as a
  product result, never an advisory fact or Tire function-status record;
- retain source-event time from backend envelopes and use it, not delayed
  receipt time, to exclude pre-reset records;
- preserve the Cloud-observed service release when no new result exists;
- label retained records as history rather than new-drive results.

Presenter continues to read operational installation state through Aos Cloud
and product records through the corresponding backend. It does not read guest
journals or infer the native advisory from package versions. Native advisory
remains exclusively Gateway/VISS-derived.

## Executed checks and remaining gate

- Brake diagnostic build: targeted subscription guards and ARM64 build/tests
  passed before sign/upload; Cloud publication and installed release observed.
- Presenter: type check, 150 unit tests and all 97 browser fixture tests passed,
  including nine targeted dialog tests; dialogs fit 1280×720, 1728×1117 and
  1118×1124 without scrolling.
- Presenter production build completed; live Vehicle summary and Brake modal
  display the new distinctions with the actual Test's 59.0.0 release.
- Demo Control: 35 service-input tests passed, including bounded numeric
  diagnostic projection, malformed-field rejection and payload redaction.
- VDP candidate: 35 family tests and 14 baseline Provider tests passed,
  including a busy duplicate stream expiring without reconnect and recovery
  only on an advancing frame; isolated original/candidate reproduction passed.
- Component packaging: 14 advisory-runtime tests and six replay tests passed;
  historical 78.0.0 inspection returned no problems after the pin change.

Still open: localize the remaining brief missing-input episodes, then qualify
a real braking maneuver, new backend assessment and native advisory on this
release. The normal VDP update and duplicate-frame branch are live-verified;
the complete Brake functional regression is **not** closed. A natural Autopilot
stop may remain correctly unqualified after the transport fix. Leave Autopilot
running as requested; do not silently reset the scene or model for this check.
