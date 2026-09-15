<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# One-hour UI E2E repeat — 15 September 2026

Status: **Functional UI cycle completed after human VM-access input. Test
deprovisioning, Cloud deletion and local retirement completed. Observation
closed at the user's request once the lifecycle outcome was confirmed.**

## Scope

User-authorized repeat of the corrected Presenter, through the real Demo UI
and its existing Demo Control operations. Test only, Factory `.33`, selected
Cloud `aoscloud.io`. Production is excluded. Planned coverage: Create/connect,
VDP V1/V2/V3 with Safe Stop, service installation/replacement without Safe Stop,
synthetic backend receipts, external-link OFF/ON with separate Cloud state
observation, and Finish. No product change or manager restart was attempted.

## Observed sequence (UTC)

| Time | UI observation |
| --- | --- |
| 06:24:42 | Start of the test window. |
| 06:25 | Vehicle showed No controller created; `.33` was selected. Session confirmed `aoscloud.io` and the configured OEM certificate domain. |
| 06:26:22 approximately | Create controller confirmed once. |
| 06:26:46 | Create RUNNING; `WAITING_FOR_ACCESS` requested the native macOS VM password dialog. Vehicle showed Not provisioned. |
| During access wait | Native dialog could not be acquired through computer-use surfaces. User was asked to enter the password in the existing dialog; no second Create was dispatched. |
| 06:29:30.435995 | Create became PARTIAL after 188 seconds. Result: phase `start-test`, reason `VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`, `completedSteps: []`. UI offered Continue preparation. |

The returned reason covers cancellation or an unavailable dialog; it does not
prove which macOS condition prevented input. No claim of a Cloud, VM firmware,
or password-validity defect is made. Source inspection confirmed that the
existing native prompt gives up after 180 seconds. The password was not placed
in a browser, shell command, evidence file, or log.

## Additional UI finding

During Create, the main view correctly displayed the active operation and
access-wait message, but View progress opened an empty current-run Trace.
After the operation became PARTIAL, Trace contained its receipt and expandable
steps. The initial-operation progress dialog is therefore still inconsistent
with the main active-operation display. This observation is not a code fix.

## Initial blocked attempt: preserved state and continuation

At this initial pause, the partially created Test was retained for Continue
preparation after native access became available. It was not recreated and
terminal enrollment was not substituted. Cloud provisioning, software
publication, backend functionality, network transitions and Finish were still
untested at that point. The resumed cycle below completed that coverage;
access-wait time is not successful E2E coverage.

## Resumed real UI cycle

The user supplied native access and requested continuation. The resumed window
started at 06:38:12 UTC. The existing Test was continued, not recreated.
All lifecycle, publication and assignment mutations were invoked through the
Presenter; driving and network changes used native Driving Control. Cloud
events were additionally read in the authenticated Grafana UI. No terminal
VM enrollment, direct guest probe, standalone CM/SM restart, Factory rebuild,
Cloud configuration change or source fix was substituted for the UI test.

Factory: `6.1.1-maninblack.33/main-qemuarm64`.
Test system UID: `2efb10ecd47340ed8751d1b73adf9bd5`.
Base commit: `52dd2c0bedbad43944ee05e2569e51d7306d9774`, with the existing
working-tree corrections. This is not a clean-source qualification.

### Functional observations (UTC)

Times describe visible observations, not invented command-duration measurements.

| Observation | Result |
| --- | --- |
| 06:39:22 | Continued Create reached the Start simulator stage; no provisioning yet. |
| 06:40:55–06:41:35 | Simulator and native surfaces started; Connect in Manual selected Test. Native telemetry: LIVE, Manual, 0 km/h. |
| 06:42–06:43 | VDP V1 prepared as 53.0.0 and signed/published through the selected OEM before provisioning. |
| 06:44:32 | Initial Cloud connect; Presenter subsequently showed Online and VDP53 Pending, with factory 0.0.0 installed. |
| By 06:45:35 | Native Safe Stop led to Cloud-installed VDP53. First Autopilot selection had shown 0 km/h; that initial stationary observation is not claimed as a moving-update proof. |
| 06:47:48 | Native Autopilot movement confirmed at 19.4 km/h. No runtime/source repair was made. |
| 06:48:39–06:48:53 | Brake V1/33.0.0 first publication and dedicated Subject assignment completed; active instance 33.0.0 and real synthetic backend records observed. |
| 06:50:23–06:51:19 | VDP V2/54.0.0 published during observed 19.4 km/h movement. Detail dialog showed Installed 53 / Pending 54. Native Safe Stop stopped the vehicle; the same open dialog updated to Installed 54 / no pending without reopening. |
| 06:53:27–06:53:39 | Brake V2/34.0.0 installed and active through its existing assignment, without Safe Stop; native movement 19.3 km/h. Backend selected release34 and received its assessment. |
| 06:55:21–06:56:08 | VDP V3/55.0.0 Pending while VDP54 remained installed and native speed was 19.3 km/h. Native Safe Stop released the update; Cloud confirmed Installed55. |
| 06:58:14–06:59:12 | Brake V3/35.0.0 installed/active without another assignment or Safe Stop; native movement subsequently observed at 19.4 km/h. Backend displayed release35 and its assessment. |
| 06:59:32 | Backend pagination reached page 2 of 2 and exposed the remaining current-release record. |
| 07:03:10–07:03:26 | Tire V1/23.0.0 installed/active after first assignment to its separate retained Subject; its backend displayed matching results. Brake remained assigned. |
| 07:05:27–07:05:50 | Higher Tire24.0.0 replaced Tire23 through the existing assignment, with no Safe Stop. Backend showed release24 and fresh results. Autopilot remained selected; a momentary 0 km/h observation is not represented as continuous movement. |
| Approximately 07:08:00 | Native external-network OFF accepted. Two earlier clicks were rejected by computer-use concurrent-user protection; OFF was not claimed until the accepted click and explicit OFF display. |
| 07:08:33 | Cloud disconnect event; Presenter subsequently showed OFFLINE. Tire backend retained 22 messages and its last pre-OFF receipt. Native telemetry remained LIVE; 19.4 km/h was observed while external network was OFF. |
| 07:10:00 | Native reconnect restored Cloud Online without VM or manager restart. |
| 07:10:21 / 07:10:33 | Tire24 and Brake35 respectively resumed backend receipts. This confirms resumed delivery, not a separate exhaustive proof of every queued record or duplicate suppression. |
| 07:12:26 | Finish accepted through its explicit UI confirmation for current disposable Test. |
| 07:12:40 | Whole-VM shutdown generated final Cloud disconnect. |
| 07:12:56 approximately | UI progress already confirmed Cloud new/Offline, Unit/Node absence and subsequent cleanup stages. No 30-minute Offline wait. |
| By 07:13:30 | Finish returned the UI to No controller created. Current-run Trace 0, no selected vehicle, empty installed slots and available Create were confirmed on Vehicle at 07:13:57. Working Test data was irreversibly retired; Factory original, published releases and release continuity were preserved. Production was excluded throughout. |

### Cloud event correlation

Use the UTC timestamp inside the UMH log body, not local browser display time.

| Event | Publisher timestamp UTC | UMH receipt UTC | Approximate delivery delay |
| --- | --- | --- | --- |
| Initial connect | 06:44:32.448185 | 06:44:32.457 | 8.8 ms |
| Network OFF | 07:08:33.264883 | 07:08:33.274 | 9.1 ms |
| Network ON | 07:10:00.223750 | 07:10:00.241 | 17.3 ms |
| Whole-VM Finish | 07:12:40.757151 | 07:12:40.764 | 6.8 ms |

The interval from packet-filter OFF to Cloud disconnect is transport detection,
not the above event-delivery delay. Four matching events were visible after
Finish. The scoped RabbitMQ queue query returned zero matches in the observed
period. The user then explicitly ended the proposed 30-minute observation
tail: the failure under investigation was a Unit remaining Online and thereby
preventing deprovisioning/deletion. Here, Cloud confirmed Offline and both
operations completed, so that lifecycle failure did not recur in this run.

No full 30-minute post-disconnect observation is claimed. The resumed
functional cycle ran from 06:38:12 until completion observed by 07:13:30
(approximately 35 minutes), with subsequent read-only log checks. This is not
reported as a completed one-hour soak or proof of a permanent RabbitMQ fix.
No additional VM run or background monitor was scheduled.

### UI coverage and limits

- Installed component versions, exact active service versions and backend
  results agreed. Process state for VDP remained explicitly Not reported by
  Cloud; no independent VDP-process qualification is claimed from this UI run.
- Open component details updated across a real pending-to-installed transition.
  Previous installed service versions remained visible while a new release was
  being published, rather than being prematurely labelled Running.
- Cloud resources showed CPU in DMIPS (615 observed), separate sample/read
  times, and explicit unverified memory units instead of invented percentages.
- Native Autopilot distinguished MODE SELECTED from actual telemetry MOVING;
  network OFF was not misrepresented as instant Cloud Offline.
- Changing perspectives briefly labelled the old Cloud observation last-known
  while the new read was outstanding; successful reads restored Online. This
  was visible rather than silently presenting cached state as live.
- The earlier initial-Create empty-Trace finding remains open. The native
  access step required human assistance, so this is not an unassisted run.
- KUKSA permissions, real vehicle-derived service analytics/advisory, Production
  rollout and a permanent fix of the Cloud queue defect remain unqualified.
  No new product code, commit or push is part of this verification.
