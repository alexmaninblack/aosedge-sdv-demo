<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .35: continuous clean-cycle qualification

Date: 19 September 2026. Status: blocked at CM reconnect; not a passing E2E report.
Authority: the operator requested a complete clean run and explicitly confirmed
permanent/no-backup retirement of the preceding Test before this attempt.
The accepted [ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md)
excludes Park/Resume and another native CM patch, not SOTA/model/queue continuity.

## Preserved boundary and method

- Reuse immutable Factory `.35`, built from Platform `bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74`;
  no successor image is needed for the current host/VDP/service changes.
- Selected Cloud: `aws-stage.epmp-aos.projects.epam.com`. Production remains
  excluded; its stopped overlay is not a cleanup target.
- Use Presenter/native controls for operator flow and visible status; bounded
  read-only engineering evidence supplements, never substitutes, product/UI proof.
- Keep publication/installation/function/advisory evidence separate. Real CARLA
  maneuvers supply stimuli; no fabricated product data or model-threshold changes.
- Use the operator-provided VM password only for native first-access enrollment;
  do not persist the password or place it in this report.

## Prior Test retirement

At 08:35:04 UTC, one Presenter Finish request was accepted for prior run
`ac456637-7e30-474f-be40-5716f944a21b`, Unit
`a842a53e-a30b-481c-8747-f73a96c351d7`. Factory, published artifacts and release
continuity are preserved. Finish completed at 08:35:46.117574 UTC, **42.07 s**.
The receipt confirms simulator/Test shutdown, Subject reconciliation,
deprovisioning, Unit/Node absence, scoped backend cleanup and local retirement.
There was no thirty-minute Cloud Offline wait. UI returned to empty slots,
No controller created and enabled Create controller. Deletion is permanent;
Factory, published releases, release continuity and Production were retained.

## Clean creation

One UI Create request was accepted at 08:37:06.032108 UTC for `.35`.
New local run: `1ac3b4f2-cfe7-4e89-88e6-974637ab7afc`.
It reached the native first-access prompt. At that point computer-use reported
the Mac locked and unable to unlock automatically. No password was entered;
the operator was asked to unlock, not to resend the password. Do not report
guest-ready, provisioning or a complete Create from an accepted request alone.

The original Create returned PARTIAL at 08:40:13.025217 UTC, phase `start-test`,
reason `VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`, with no uncertain operation.
Do not Create a second environment: continue this same checkpoint after native
access is available. No enrollment, provisioning or service publication occurred.

Read-only build-catalog preflight found the current Brake source's V3 product
build, but not V1/V2. Build those profiles through the existing development
build command before their respective UI Prepare actions. This is a service
package prerequisite, not a Factory rebuild or publication.

Both missing builds then completed through `democtl service build`: Brake V1
at 08:41:21.230065 UTC and V2 at 08:41:41.600570 UTC, from clean source
`52d7c4ff67898cac44d4fc5b1ed49c9c6218dd7a`. The normal export gate accepted
their ARM64 binaries and passing CTest receipts; dependencies were reused.
No release was allocated, signed or uploaded by these development builds.

## Resumed after unlock

At about 09:49 UTC the Mac became accessible. The first-access system dialog
is not an addressable application in the available native-control tool, so one
explicit `democtl vm start test` used the operator-provided password through
the ordinary hidden terminal prompt. Password/host-key checks were not bypassed;
the credential was not printed or stored by this proof. Initial console/SSH/
DNS enrollment completed in 61.4 seconds and confirmed an unprovisioned guest.
This bootstrap exception means this run is not claimed as strictly UI-only.

The same local run was then continued from Presenter. Create completed at
09:52:00.779735 UTC after 14.68 seconds, preserving the already-running VM and
starting both backends. The guide offered Start simulator before provisioning.
One UI simulation-start request ran from 09:52:56.520243 to
09:53:39.536543 UTC (**43.02 s**). Presenter reported RUNNING_UNASSIGNED;
native Driving Control showed Not assigned, stationary Safe Stop and both
advisories Not available. This is the detached pre-Provision stage.

## Initial VDP publication and provisioning

UI Prepare selected VDP V1 / **80.0.0**, seven read paths and no advisory.
One Sign & publish request completed from 09:58:11.988458 to
09:58:17.636189 UTC (**5.65 s**), using the selected staging OEM context.
The signed bundle SHA-256 is
`821bb1739fe4a9304f1246a8c3de11268a931eb96138a1219c4feb7d7272d44b`.
Cloud then reported publication READY at 09:58:21.412584 UTC, deployment
`b358ee1d-f059-487f-b0be-145fc7283280`, version UUID
`e88428b6-34dc-4737-ac99-1a34126ec411`. No Unit existed at that point;
publication readiness was not mistaken for installation.

Before provisioning, source run `8c8b5767-66f9-43e9-8ec0-579951ab37d8`
had actor 25, Unreal PID 37672, Gateway PID 38076 and native-control PID
38082. One UI Provision request completed from 10:01:15.870580 to
10:01:47.663457 UTC (**31.79 s**). New Unit:
`cb64acb2-12fd-4340-8962-eca8d43465f1`; Node:
`3de335f8-defc-4869-a10d-ce5c075a5928`. Cloud reported Online and confirmed
role-set membership. Source run, actor and all three PIDs remained unchanged;
only assignment generation advanced 12→13. Native UI showed selected Test,
stationary Manual. Presenter showed component 80.0.0 pending, not installed.

Explicit native Safe Stop at about 10:02:25 UTC permitted the first component
application. The next Cloud inventory reported installed 80.0.0. Autopilot
was explicitly selected later, at about 10:04:09 UTC, before first service
assignment, to distinguish SOTA from the component Safe Stop prerequisite.

## Brake V1 publication

UI Prepare produced real-data Brake V1 / **61.0.0**. Its one Sign & publish
request completed from 10:03:51.722787 to 10:04:01.165123 UTC (**9.44 s**),
through the configured staging SP. Signed SHA-256:
`c33959c68695323d612b8b83d8b98f3bbaea1838b53f3b56a45e4ddf6a58c661`.
Service identity: `cabba557-061d-4f44-9385-5b1b03e34186`.
The initial receipt was ACCEPTED/PROCESSING, not runtime or product proof.

First Deploy used only the service ID and its retained Brake Group Subject,
with CARLA in Autopilot. UI showed 61.0.0 active, one instance, at 10:05:56.
The first input observation briefly reported ACCESS_DENIED / KUKSA_AUTH_UNAVAILABLE
at 10:05:45; it recovered to RECEIVING by the 10:06:26 observation without
service restart, permission edits or another Deploy. The journal confirmed
one initial not-ready transition. This transient was not a persistent failure.

The native Brake maneuver produced window `21de5041-9598-45cd-813e-d757c8e0496b`:
COMPLETE, 75 samples (30 PRE / 25 ACTIVE / 20 POST), 8/8 chunks, no missing
sample indices, receipt 10:07:18.407 UTC. Source times span 7.391 s over
74 intervals: about 10.01 retained samples/s, not the old every-third-frame
cadence. The UI graph and sample pages were inspected. Window SHA-256:
`97b3b067e3e5f9430c499728a618606841c64efcf11ce0851d0abd9feb3bbf5b`.
V1 emitted windows, not condition/advisory products; native advisories stayed
Not available. An earlier additional window also completed honestly.

## VDP V2 and retained Brake V1

VDP V2 / **81.0.0** was published through UI from 10:09:21.695339 to
10:09:27.156338 UTC. Cloud READY version UUID:
`943d37c0-2e9c-462f-b42b-006e43d8f147`. Signed SHA-256:
`89d6219d9d5e5201f734e509e3beacc766195bae49fa5127714c1a61784a222b`.
Presenter kept 80.0.0 installed and 81.0.0 pending in Autopilot, including
an autonomous stopped frame. An explicit Safe Stop then permitted installation;
UI and Cloud inventory reported 81.0.0 before the next maneuver.

The unchanged Brake61/V1 recovered and produced window
`6eeadab5-3114-4fa4-ab75-3259cf7e46cd`: COMPLETE, 75 samples, 8/8 chunks,
SHA-256 `2bc9d9516f5e7528591a0f51f6812a16a896b64e977e1b821bf1706f3abca73b`.
No Brake redeployment was used. Function observation generation remained 1.

## V1 backlog through the V2 service upgrade

UI prepared Brake V2 / **62.0.0**. A scoped engineering `backend stop brake`
then stopped only the owned Brake container with `dataPreserved=true`;
Tire backend, VM and CARLA remained running. This is explicitly an engineering
fault-injection exception, not a UI-only operator action.

A native Brake maneuver accumulated V1 window
`fb47f6ae-d7ba-40db-a6ae-9c5155c87c0a` in its existing persistent storage:
eight chunk messages and one completion. Bounded read-only inspection recorded
their byte hashes, original 61.0.0 provenance and function generation 1.
No message or model content was changed. Autopilot was explicitly resumed;
one UI publication of Brake62/V2 began at about 10:15:26 UTC. Keep the backend
stopped until installed-version and byte-preservation checks complete.

UI/Cloud reported Brake62 active at 10:16:28 UTC, with Autopilot still selected.
All nine previously captured V1 files remained present with identical hashes.
Additional legitimate V1 messages created before cutover also remained.
Function observation generation advanced 1→2; the new V2 model started at wear
54, epoch `b3cde273-90ec-4ea0-8057-87708c890f9f`. A native Brake maneuver while
the backend remained stopped produced assessment
`bb20599e-f000-5263-82ea-0706c288f7bd`, wear 60, score 40 / MONITOR.

The ordinary backend start restored its preserved storage. A read-only
database comparison proved **all 17** captured queued messages received exactly
once with their original canonical hashes: 16 V1 window messages and one V2
assessment. UI showed delivery IDLE / 0 queued, current MONITOR 40/100, and
late 61.0.0 windows in Receipt history without replacing the V2 result.
Source time 10:17:21 and receipt 10:18:40 were displayed separately.
The V1 spool did not block V2 analytics. No Cloud/VM restart or model Reset
was used. Native advisory remained Not available with VDP V2.

## VDP V3 and inherited Brake V3 advisory

UI published VDP V3 / **82.0.0**; Cloud reported READY at
10:22:03.599266 UTC, deployment `bda5c4a5-20ac-4ae4-b805-345034d9a86c`,
version UUID `addbd6e4-79b4-4e61-8667-7d94d9f33d85`. Existing Safe Stop
permitted installation, confirmed in UI by 10:22:12. With Brake V2 still
installed, native advisory changed to Waiting for service, not Monitoring.

The next native Brake maneuver produced V2 assessment
`2dda276b-d568-5c0c-b327-014a265b73cd` at 10:22:56.108 UTC:
wear 66, score 34, INSPECTION_RECOMMENDED. V2 did not emit an advisory.
Stationary Manual was then selected before publishing Brake V3 / **63.0.0**.
UI reported installed/active at 10:25:44; no Safe Stop was required for SOTA.

Before any V3 maneuver, the model file's SHA-256 was unchanged:
`eb4c7c449fe4b333bd70a2fa32e2335c09168d7fd8f9e046c5485c96e6df109d`.
Wear, score, model generation 2, producer epoch and last assessment ID all
survived. Function-observation generation advanced 2→3. Native telemetry
immediately displayed Inspection recommended. Backend confirmed APPLIED SET
facts from 63.0.0 linked to the preceding V2 decision ID, with recurring renewal,
while the assessment count remained two. No fabricated V3 assessment was made.
The backend popup correctly separated No result for release 63.0.0 yet from
Service ACK CONFIRMED; earlier V2 assessments remained history.
This proves the inherited INSPECTION branch, not a separate MONITOR branch.

## Tire V1, independent Reset and external Offline

UI published Tire V1 / **36.0.0** at 10:32:27.021973 UTC and completed first
assignment through its separate Subject at 10:33:45.334937. UI reported one
active instance. Initial function input was RECEIVING before any assessment.
A native Tire maneuver produced real-input assessment
`41a7a0f9-738c-5da7-982d-9622bf7e7df8`, score 67, confidence 100%,
INSPECTION_RECOMMENDED, received 10:34:13.591 UTC. Native telemetry displayed
the matching warning independently of Brake. Physical braking in that maneuver
also legitimately produced a new Brake V3 assessment, score 26 / wear 74.

UI Tire Reset `a89651c7-dc5a-41a8-a6b7-2b7785c2dc70` matched Gateway CLEAR
request `3e28667e-2ad8-59a4-b686-d9fa95e65208`, sequence 5. Tire changed to
Monitoring; the Brake model hash and warning remained unchanged. UI Brake
Reset `2f7e2e3f-6874-4145-964f-fca369dc2119` subsequently matched CLEAR
`9348822f-3330-5f1f-bf12-36927d8900bf`, sequence 37. Brake returned to its
initial wear 54; Tire remained reset with no new assessment. Both popup results
said No new result after reset, not a fabricated GOOD assessment. Histories
and producer epochs were retained.

Native External network off at about **10:37:45 UTC** preserved local control,
KUKSA and services. Presenter showed Aos Cloud OFFLINE by 10:39:17 and stale
service-function facts as Last known / Not confirmed. After a settling interval,
read-only backend counters stayed unchanged through 10:42:53: Brake 89 product
records / 98 function observations; Tire 15 / 15. Last function receipts were
10:37:44.035 and 10:37:45.486 respectively. This is actual absence of new
ingress, not merely a frozen chart.

Native Tire and Brake maneuvers during the outage produced new model results
and both local warnings. Token-file modification times (metadata only; no token
contents/claims read) showed Brake renewal at 10:40:22 and 10:43:22 and Tire
at 10:39:43 and 10:42:42, after external connectivity was cut. Processes and
function generations remained unchanged. Before reconnect, captured queues
contained 18 Brake products (2 assessments, 1 event, 15 advisory facts) and
30 Tire products/status records; pending function-observation ledgers held
19 and 21 reports. These are bounded snapshots; later legitimate messages can
also be created before reconnection.

UI prepared and published same-profile Tire **37.0.0** while the Unit remained
Offline; the UI correctly retained installed 36.0.0 and pending 37.0.0. A scoped
engineering stop of only the Tire backend preserved its database so queued
message/model continuity can be inspected after SOTA and before backlog drain.
This is another explicit non-UI-only fault-injection exception. At about
10:44:55 stationary Manual was selected and the native network button restored
external connectivity; installation, byte preservation and drain proof follow.

## Reconnect: service delivery passes, CM fails

The external guest filter reported ON and both service/backend paths recovered.
The Tire backend was restored with its database preserved. Read-only database
comparison proved every captured offline product delivered exactly once with
its original canonical bytes: **18/18 Brake and 30/30 Tire**, missing 0,
duplicate rows 0. Function-observation pending queues returned to zero.
UI showed current receiving/idle input and the late Tire assessment with source
10:39:33 versus receipt 10:48:15. No model reset or synthetic input was used.

The same run exposed a distinct native CM failure. At 10:45:07, after restored
connectivity, CM received a WebSocket close frame and blocked during subscriber
disconnect notification. Live thread backtraces and source identify an AB/BA
Monitoring/Communication mutex cycle. Both current official upstream HEADs
retain those lock scopes. See the
[bounded diagnosis](cm-monitoring-disconnect-deadlock-2026-09-19.md).
Cloud remains Offline; Tire 37 is pending and its same-profile installation/
storage preservation are not passed. No new CM patch, VM/CM restart or final
Finish was performed; preserve the failure for the next approved decision.

## Bounded native recovery check

While preserving the unrelated CM failure, Return to road was invoked once
from stationary Manual. Native UI confirmed On road / stationary Manual and
required explicit subsequent Autopilot. Brake's model file and producer epoch
remained byte-identical; both native warnings survived and no Reset was sent.
Tire's aggregate model digest changes during legitimate advisory sequence
renewal (`write_model` includes `nextAdvisorySequence`), so that whole-object
digest alone is not a valid exact analytics-state comparison. Its warning and
producer epoch remained intact; a complete semantic pre/post comparison is
still needed for the broader recovery matrix.

Autopilot was then explicitly selected. The source retained actor 25 and the
same run, with zero command/ownership timeouts or disconnects; accumulated
distance advanced from 2707.03 to 3097.83 m after the post-recovery snapshot.
The later UI snapshot showed Autopilot at a stopped frame, not a captured
moving-speed frame. Safe Stop was selected afterward. This does not claim the
unexecuted manual off-road/collision or occupied-placement branches passed.

## UI observations requiring follow-up

- V1 dialog says `Service contact: not recent` because that label uses Reset
  polling, even while fresh function observations and complete windows arrive.
  V1 has no Reset poll. The function/input rows are correct; the contact label
  should identify reset-channel contact or use appropriately scoped actual
  function receipt evidence, not suggest general service disconnection.
  A focused regression failed against the old wording. The correction names
  Reset channel contact and explicitly names Brake V3/Tire V1 as reset-capable
  profiles, without changing authority, readiness, reset guards or behavior.
  All 225 unit tests, 23 focused browser tests, TypeScript and production build
  pass. Existing hashed assets were retained; the operator Reload UI action
  activated the new entry point without restarting any runtime. The live Brake
  popup showed the corrected Reset channel contact label and the same result.

## Qualification matrix and remaining work

- Passed: prior Finish; empty Create/bootstrap exception; detached simulator;
  initial publication/Provision/Online; same-source attachment; Safe Stop gates.
- Passed: VDP V1→V2→V3, Brake V1→V2→V3 (INSPECTION inheritance), first Tire V1.
- Passed: real windows/assessments/advisories, both independent resets/CLEAR,
  retained V1 backlog through V2 and exact offline-product drain.
- Passed: offline local authorization renewal and analytics/advisory, no new
  backend ingress; service/backend recovery independent of Cloud failure.
- Blocked: Cloud reconnect and Tire 36→37 same-profile installation/continuity.
- Open: separate Brake V2→V3 MONITOR inheritance branch and broader calibration
  series; they are not silently covered by the INSPECTION branch.
- Open: full Manual off-road/collision recovery matrix and final Finish.

Record each actual result and any skipped or failing branch. Earlier preserved
Test evidence and fixture tests are not silently counted as this clean run.
