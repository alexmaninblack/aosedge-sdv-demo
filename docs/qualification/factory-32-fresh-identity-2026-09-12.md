<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .32: fresh Test identity qualification

Publication note: private evidence links, infrastructure identifiers and source
locations have been removed. The detailed working report is retained outside
Git under the confidential-input policy; timings and our own conclusions remain.

Status: delivery recovered; VDP and both mock-data services active. False Cloud
Offline reproduced at 02:24:30 on 13 September by delayed disconnect delivery
after the same consumer's ACK timeout. The live failing state is preserved.
Clean cold E2E and Cloud event ordering remain unqualified.
Date: 12–13 September 2026. All times UTC.

The preceding status is the dated experiment result. The .32 Unit was later
retired for the [.33 clean cycle](factory-33-e2e-2026-09-13.md); it is no longer
the current Test or a preserved live failing session. The Cloud defect itself
remains open, with packaged client recovery on .33. See the
[working baseline](current-baseline.md).

## Authorized scope

Replace only the current Test through Demo Control: deprovision/delete its
Cloud Unit, retire its owned local state, create a fresh VM from the unchanged
Factory .32, provision into Test Vehicles, and prove VDP/service delivery and
service replacement without transient manager binaries or CM/SM restarts.
Production .31, retained service Subjects, published releases and original
Factory artifacts are preserved. No new Factory build is needed: all current
CM/SM patches are already integrated in .32.

- Immutable Platform source: `04fc8270c55ff5c35f1e98af534a5efccb035464`.
- Factory SHA-256: `f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14`.
- Retiring Unit: `923b9820-999b-41bb-91db-b2a2c469e743`.
- Retiring System UID: `5aa1f8e4a1114467a6ccfb269c62a7a8`.
- Production Unit: `d87ba9cb-b21f-45db-8773-553e52d0353e` (excluded).

This experiment removes the previous Test identity's queued-event history.
It does not fix or waive the source-confirmed Cloud stale-event/consumer defect.
Service backend tests remain explicit synthetic-data tests without KUKSA
permissions or actual vehicle advisory qualification.

## Execution

- 18:25: `democtl status all` confirmed Test .32 and Production .31 running.
- First `democtl demo retire` stopped before lifecycle mutation with
  `SERVICE_RETIREMENT_BINDINGS_REQUIRE_RECONCILIATION`.
- Root cause: assignment skipped journaling an already observed service-to-
  retained-Subject relation; retirement required that confirmation. Both local
  assignment records were `ASSIGNED` with a confirmed bind but no assign receipt.
- Narrow source correction records successful authoritative observation as
  `CONFIRMED`, `attempted=false`; no fabricated POST receipt or relaxed scope
  validation. Thirty assignment tests and twenty lifecycle tests passed.
- 18:27: explicit `democtl service assign` for each existing service returned
  `noOp=true`, confirmed its exact existing Subject and current Test association,
  and repaired the local observation receipts without new Cloud assignments.
- 18:28: retirement stopped simulation, deprovisioned Test, confirmed Unit and
  Node absence, and stopped the VM. Local cleanup then rejected the unregistered
  completed CM comparison receipt, before deleting local files.
- Test-only cleanup now recognizes that exact comparison receipt only after
  confirmed restoration without a transient drop-in, and the existing completed
  unchanged-CM control receipt. Nineteen Test lifecycle tests passed, including
  refusal to discard an unrestored experiment. Unknown fields remain rejected.
- Resumed `democtl demo retire` completed `RETIRED`; completed Cloud mutations
  were not replayed. Old Test overlay, access material and separate factory copy
  were removed without backup; original .32 and Production .31 were preserved.
- Fresh `environment create --image 6.1.1-maninblack.32/main-qemuarm64 --target test`
  completed; no image build was performed.
- `vm start test`: completed in 61.52 s, SSH/DNS ready, role staged before SM.
- `unit provision test`: completed in 19.94 s; Online and Test Vehicles
  membership confirmed. New Unit `d90798f6-a32c-40cc-8129-26a0f1343a67`,
  System UID `c7b8f9d868ea4b65b4448b01595eb110`,
  Node `412cd3d1-9f78-4889-a944-b178a7366711`.
- `simulation start --target test` completed. Automatic window placement was
  reported incomplete; no visual-composition acceptance is claimed.
- 18:36:29: `vehicle select test` connected the fresh Test in physical Safe Stop;
  Production's already blocked source gate remained blocked. Both backend
  containers subsequently started from retained artifacts without Docker restart.
- `service assign` bound each retained per-service Group Subject to the fresh
  Test and confirmed its existing service membership: Brake 8.0.0, Tire 7.0.0.
  Both packages are Cloud ready; observed runtime service lists remained empty.

## Delivery result at 18:41 UTC

| Boundary | Result |
| --- | --- |
| Cloud Unit | Provisioned / Online; Test Vehicles membership confirmed |
| VDP | Cloud reports installed baseline 0.0.0 and pending 18.0.0, `to be installed`, no reported component error |
| CM desired state | Two initial desiredStatus messages received around 18:34:48–49; retained payload has zero items, zero instances and only the initial Group Subject |
| Service assignment | Exact Brake/Tire Subject bindings confirmed, but no service runtime rows and no subsequent desiredStatus observed |
| Transport | One connection establishment; ongoing Pongs and acknowledged monitoring, including ACK at 18:40:47 |
| CM | PID 1472, Active/success, zero automatic restarts; SHA `85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d` |
| SM | PID 1691, Active/success, zero automatic restarts; SHA `936fbd563f7e9d54651504f5aeba84fee0f3736861d30c2efb60eb564e039783`; no observed launcher-start failure |
| Guest VDP | Inactive; no committed provider runtime state or active version |
| Production | Original .31 VM/Unit retained and running; no provisioning, stop or software change |

No VM/CM/SM restart or transient manager application was performed after fresh
provisioning. No replacement package was published to hide the initial delivery
failure. The fresh identity did not unblock the complete delivery chain.

The old false-Offline symptom did not recur during this approximately six-minute
window; this is **not** proof of sustained recovery of the Cloud consumer defect.
Current evidence localizes the immediate failure before delivery of the assigned
items to CM, rather than VDP activation at Safe Stop. It does not establish the
exact Cloud dispatcher cause or exclude influence from the initial UnitStatus.
Cloud also reports automatically selected Campaign unit sets; this run did not
create or modify those sets.

## Remaining gates

Native VDP/service installation, new-Test backend identity correlation, service
replacement and full E2E remain unqualified. Preserve the current running Test
for the initial UnitStatus/Cloud-dispatch trace. The received initial desired
transaction `2cafe962-6065-41dd-95e9-68aeb1f6c25c` at 18:34:49.652 is an exact
correlation point. No claimed fix to AosCore or the production Cloud was made.

Local source verification: 30 assignment tests, 20 lifecycle composition tests
and 19 Test-only environment tests passed; `git diff --check` passed. Changes
and evidence are local/uncommitted; unrelated earlier changes were preserved.

## Cloud log investigation — 13 September

Read-only investigation through the existing authenticated Grafana session and
`democtl unit cloud-status test`. No guest, Cloud configuration, package, or
Production mutation was performed. Times below are UTC on 12 September unless
explicitly stated otherwise.

### Initial UnitStatus was received, including SM runtimes

The `CLOUD_INSTANCE_A` log confirms two full protocol-7 UnitStatus messages:

| Received at | Transaction | Observed processing |
| --- | --- | --- |
| 18:34:48.242 | `e02648cc-5668-4ae6-86d1-1fe7064c1822` | Initial node reported disconnected; no items or instances. Cloud wrote Online at 18:34:48.364 and produced a response. |
| 18:34:49.230 | `6d0a6273-ef35-4e92-bd43-32a4754e24b9` | Node reported connected; configuration 6.0.0 and all four expected arm64 runtimes were present. Cloud updated node runtimes at 18:34:49.420 and produced a response at 18:34:49.635. |

This excludes the narrower hypothesis that Cloud never received the SM node
and runtime information. The second response correlates with the empty desired
transaction already observed by CM. Baseline instance processing also emitted
missing-subject warnings for `aos-vm-main`; their causal role is not established.

### VDP dispatch used the wrong transport path

The relevant dispatcher is logged under `CLOUD_INSTANCE_A`, module
`api.tasks.desired_status`. `CLOUD_INSTANCE_A` is unit monitoring, not this dispatcher.

Correlation `acf0610aceea4a08a553f1300f8cce52`:

- 18:34:52: component assignment and desired-state preparation ran for the fresh
  Test. No campaign was selected; preparation proceeded through its default path.
- 18:34:53.345: the prepared outbound envelope explicitly used protocol **6**,
  despite the inbound protocol-7 UnitStatus messages above. Its component list
  included historical VDP 1.0.0. This is not evidence that the pending 18.0.0 was
  delivered, nor an assertion that 1.0.0 was the only component in that envelope.
- 18:34:53.486: the sender logged both RabbitMQ user and session as absent.
- 18:34:53.487: it warned that no active RabbitMQ user could be found and logged
  failure to send desiredStatus.

Thus the first observed component dispatch failed in Cloud before delivery to
the guest. Safe Stop and the VDP launcher cannot resolve this send-path failure.
Signed URLs and package encryption material from the logs are deliberately not
copied into this document.

### Subject bindings trigger dispatch, but service selection fails

| Time | Correlation | Result |
| --- | --- | --- |
| 18:39:07.525 | `c9ff084f3f5847efb39a1d6343c1a2d6` | Cloud created the Brake 8.0.0 update item for the exact retained Brake Subject and new Test. |
| 18:39:08.626 | Same | desiredStatus preparation failed: no built Brake service version for this OEM and **x86_64**. |
| 18:39:42.825 | `eb23c2ff9ae240179f0421a1757949ca` | Cloud created the Tire 7.0.0 update item for the retained Tire Subject and new Test. |
| 18:39:45.053 | Same | Preparation again failed on the Brake **x86_64** lookup, with both service Subjects present. |

The assignments therefore reached Cloud's update selection and dispatch task;
missing Subject binding is not the explanation for these two failures. A single
service selection error prevents completion of these desiredStatus attempts.
The logs do not establish a separate Tire architecture error or successful
delivery of either service. Building x86_64 packages is not a justified fix for
an arm64 Test.

### Current observation and resolved causal chain

At 01:18:58 on **13 September**, `democtl unit cloud-status test` reported
**Connected**, rather than the earlier Online. VDP remained baseline 0.0.0 with
18.0.0 pending. Brake and Tire now both had pending service-version records,
without installed versions or reported instances. These records do not prove
guest receipt.

After the user unlocked the Mac, the connection-event trace established:

- Event timestamp `1789238088.211162` = **18:34:48.211162**: protocol 7,
  `is_connected=true`, exact new Test UID.
- UMH received this event at **18:58:15.748**: approximately **23 min 27.537 s**
  after its timestamp, and well after both initial UnitStatus responses and all
  failed dispatch attempts above.
- RabbitMQ logged an acknowledgement timeout at **18:58:15.745696**, then closed
  channel **1271** at **18:58:15.746210**. Queue: `connection-event queue`;
  delivery tag: **1**; timeout: **1800000 ms**; consumer:
  `CONSUMER_A`. The consumer and peer
  `PRIVATE_ENDPOINT` match the earlier Cloud consumer investigation.

The source was inspected in the existing authenticated GitLab session. The
default branch remains `master`, HEAD
`private source revision withheld`; the user previously confirmed this
mainline is deployed. No private source file is added to this public repository.

| Source boundary | Actual behavior and implication |
| --- | --- |
| `private Cloud dispatcher` | Background dispatch requires the Unit to be **Online**, then selects a strategy from the stored `unit.protocol`. Incoming UnitStatus header version is not its selection input. |
| `private Cloud sender` | Protocol 7 selects the V7 strategy; 5 selects V5; all other values fall back to **V6**. The observed V6 envelope proves the wrong strategy was selected, but does not by itself establish the precise stored pre-event protocol value. |
| Same file, base strategy `legacy instance selection` | Legacy service selection reads the top-level desired-config architecture and defaults it to **x86_64**. Its exception text exactly matches the Brake dispatch errors. V7 is a separate strategy, not a subclass of this legacy base. No x86_64 guest or package is required to produce this error. |
| `private Cloud connection-state handler` | Processing a successful connection event writes the event's protocol and **Connected** status, without a timestamp/session freshness guard. Thus a late connect can demote an already Online Unit. |
| V7 sender `private Cloud sender` | V7 prepares the message through UnitProcessor and sends through WebSocket; the observed failed RabbitMQ-user lookup belongs to the legacy path. |

The initial component and later service failures are consequently consistent
parts of one source/log-backed chain: the V7 connection event was delayed while
full UnitStatus processing made the Unit Online; background dispatch selected
legacy preparation/transport; eventual event processing wrote V7 but demoted the
Unit to Connected, which the background task excludes. There is no evidence that
the factory VM changed architecture or that Safe Stop caused these failures.
The precise original cause of the consumer not acknowledging its delivery is
still not established by these logs; the earlier ACK-path hypotheses remain
hypotheses. A live database transaction trace was not available.

Read-only `democtl component cm-status test` additionally confirmed at 01:27 UTC
on 13 September: original CM PID **1472**, unchanged packaged SHA, **zero restarts**,
one observed connection establishment, **415 incoming ACK records**, and still
only two initial desiredStatus messages. The stored desired state remained empty
of items and instances. This corroborates live transport without assigned-item
delivery; no replacement test has been performed.

A suitable next controlled experiment is to request a fresh full UnitStatus
after the V7 connection event has been processed, then observe Online and V7
desiredStatus delivery. This is a proposed runtime action, **not performed by this
investigation**, and does not fix the Cloud consumer or stale-event handling.
No new image, x86_64 service build, package version, or architecture patch is
justified by this failure trace.

<a id="same-binary-recovery-and-link-control"></a>

## 13 September: same-binary recovery and external-link control

The user authorized continued Test experiments and narrow VM changes, excluding
Cloud changes. This follow-up preserves the exact fresh identity above, Factory
image, CM/SM binaries, published versions, assignments and Production. Every
runtime operation below used the existing Demo Control CLI. Grafana/GitLab
access was read-only; no production configuration, code or catalog write ran.

### Explicit recovery control — not a silent full-status resend

The installed native CM has no exposed command to resend a full UnitStatus.
In `aos_core_lib_cpp/src/core/updatemanager/unitstatushandler.cpp`,
`SendFullUnitStatus()` is invoked by `OnConnect`; ordinary node/status changes
use the delta timer. A service state-sync request is not a full UnitStatus
request. Therefore this experiment used one explicitly disclosed **CM restart**
with its existing binary; it necessarily created a new connection event. It
does not prove that an in-place full report alone would have been sufficient.

The existing `component cm-apply test --restart-cm` control was narrowly extended
to accept this exact VM/Unit pair as well as the previously authorized pair.
Crossed identities, wrong factory hash and changed manager binaries remain
rejected; a completed control is not restarted on repeat invocation.

| Time | Evidence |
| --- | --- |
| 01:54:29, approximately | One native CM restart: PID 1472 -> 55106. CM SHA unchanged; SM PID 1691 and its SHA unchanged. |
| 01:54:31.390085 | New protocol-7 connect event timestamp `1789264471.390085`. |
| 01:54:31.400 | UMH received that event, about 10 ms later, rather than the prior 23-minute delay. |
| By 01:54:42 | VDP 18.0.0 installed and active in slot `a`. |
| 01:54:43.325 | CM received follow-up desiredStatus `f8a07132-be39-4a27-ac21-570bf36ac408`; retained desired state contained VDP 18, Brake 8 and Tire 7. |
| Subsequent Cloud read | Unit Online, VDP 18 installed with no pending version; both service package versions installed. |

This is positive evidence for the previously identified Cloud selection/state
chain: after a timely V7 connection event and fresh full status, the same
ARM64 packages were delivered without a new upload, Subject assignment,
architecture change or VM rebuild. It is a recovery control, not a Cloud fix.

### Separate first-service-launch input gap

Package delivery initially did not mean running services. Guest inspection found
both native container records but dead processes and missing Brake/Tire public
`metadata.json` inputs. SM logs showed startup retries reaching the burst limit.
The bounded adapter did not capture an exact bootstrap exception; no specific
stderr text is asserted here.

The current fresh factory had deferred public-input projection while VDP was
absent. Delivery of the first VDP and both already assigned services did not
automatically prepare the now-valid public files before successful service
launch. This is a distinct Demo Control sequencing gap, not evidence of a
container capability or Cloud transport failure. ADR 0015 assigns this metadata
refresh to Demo Control. A clean-run qualification must still close that order
without relying on a post-failure restart.

Executed:

```sh
democtl service runtime-prepare test
democtl service runtime-activate test --restart-sm
```

The first command projected only the four public files under
`/run/aos-demo-service-inputs/{brake,tire}/`: `metadata.json` and `kuksa-ca.pem`.
They refer to the current Test UID and committed VDP 18, contract 1.0.1 with SHA
`8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871`.
No token or private key was introduced.

The existing activation path was extended to recognize the **already packaged**
factory projector, native resources and exact cold/verify hooks. It verifies
the packaged projector equals the supplied source and reuses those files; it
does not install a transient executable, resource overlay or drop-in.
One SM-only restart changed PID 1691 -> 56660, with unchanged SHA. The packaged
cold hook reported PREPARED, and post-start verification reported VERIFIED for
the committed and running VDP 18. CM remained PID 55106.

At 02:03:13, Cloud still reported Online and both native service instances
`active`: Brake **8.0.0** and Tire **7.0.0**, instance index 0. Guest inspection
independently confirmed both processes alive. Backend reads at 02:09 returned
fresh records for this exact Test UID and those versions. Brake's latest
observed receipt was 02:09:11.220; Tire's was 02:09:41.326. Both report
`source=DEMO_MOCK`, `vehicleTelemetry=false`. This verifies real service-to-
backend transport/storage with synthetic data, **not KUKSA or vehicle advisory**.

### One network interruption without manager restarts

The external-link implementation was inspected before use: it adds/removes only
the owned Test guest packet-filter table and preserves the maintenance and
in-vehicle paths. No host-wide filter or Production rule is changed.

```sh
democtl vehicle connectivity off --target test
democtl vehicle connectivity on --target test
```

| Time | Evidence |
| --- | --- |
| 02:10:04.302 | Off command completed, owned Test filter observed OFF. |
| 02:10:32.730 | Cloud WS recorded the Test WebSocket disconnect, code 1006, trace `d9b937da438376013b41d1dfe29ad547`. |
| 02:11:08.039 | Cloud API still reported Online with its 01:54:31 status-change timestamp, despite the server-observed disconnect. |
| 02:12:11.143 | On command completed; owned Test filter removed, observed ON. |
| 02:12:17.627593 | New connect event timestamp `1789265537.627593`. |
| 02:12:17.639 | UMH received the new `is_connected=true` event, about 11 ms after its timestamp. |
| 02:12:18.477 | CM received desiredStatus `b9d69887-8c5c-4678-b018-ed0af0e8ea4f`. |
| 02:12:47.752 | Cloud API Online, last status change 02:12:17. VDP 18 remains installed. CM inspection confirmed original PID 55106, unchanged SHA, zero automatic restarts. |

Thus the same patched CM automatically reconnected about 6.5 seconds after link
restoration. The Cloud UI status did not accurately show the disconnection in
the sampled interval. UMH queries through the immediate recovery window showed
the new connect but no corresponding disconnect receipt. That absence does not
yet establish whether this particular false event was queued, unacknowledged
or not published; the known older broker incidents must not be substituted
for evidence of its exact delivery path. No additional recovery restart was
performed, and connectivity was left ON.

The earlier restart's WS close was independently located at **01:54:30.556**,
code 1000, trace `c9dd53dc7d28c4c91bb65fbd4a869ade`. Through 02:20, the combined
UMH connection-event query contained only the 01:54 and 02:12 successful
connects. The latter was processed by pod
`CLOUD_INSTANCE_A`, as observed in the log's Labels panel. This is
the same pod previously associated with the stale consumer, so the evidence is
not a complete outage of that pod: some consumers/messages are processing.

Post-interruption observations: VDP 18 remains active, zero provider restarts,
23 read paths, gate OPEN and source LIVE. Brake and Tire backend receipts at
02:18:43.851 and 02:21:44.115 respectively confirm resumed synthetic traffic
for the exact current UID and existing 8.0.0 / 7.0.0 service versions.

Local verification: 36 focused tests passed across the old/new exact-identity
CM controls, factory service activation and public-input projection. They cover
crossed-identity rejection, packaged-program/resource/hook matching, single
unchanged-binary restart and accurate factory-versus-transient CLI reporting.
`git diff --check` passed. The Platform worktree remained clean.

Read-only evidence views:

- Test connection event order (private evidence reference omitted).
- Server-observed network disconnection (private evidence reference omitted).

### Qualification boundary

- Recovered: correct V7 delivery, installed/running VDP 18, both native services
  active, and synthetic service data in both real backends.
- Passed: one restored-link automatic reconnect with unchanged running CM.
- Still open: the exact original consumer stall/cancellation in production;
  stale-event ordering protection; clean first-service-start metadata ordering;
  full no-restart cold E2E and service replacement on this exact fresh identity.
- No Cloud change, new release, image build, Production mutation, commit or push
  was performed in these controls.

<a id="controlled-false-offline-reproduction"></a>

## Decisive follow-up: false Offline reproduced at 02:24:30 UTC

No restart, filter change or other runtime mutation occurred after the link was
restored at 02:12:11. The observation window was explicitly extended beyond
30 minutes from the earlier WS close to test the previously observed broker
timeout, rather than declare success from a short Online interval.

| Boundary | Exact observation |
| --- | --- |
| RabbitMQ warning | **02:24:30.595724**: consumer `CONSUMER_A`, queue `connection-event queue`, channel **1273**, delivery tag **1**, ACK timeout **1800000 ms**. |
| Broker channel close | **02:24:30.596400**: `precondition_failed`, delivery acknowledgement timeout; peer `PRIVATE_ENDPOINT`. |
| First delayed false event | UMH **02:24:30.598**; event timestamp **1789264470.558413** = **01:54:30.558413**, about **30 min 0.040 s** old. This matches the same-binary restart's WS close at 01:54:30.556. |
| Second delayed false event | UMH **02:24:30.599**; event timestamp **1789265432.731863** = **02:10:32.731863**, about **13 min 57.867 s** old. This matches the deliberate external-link interruption's WS close at 02:10:32.730. |
| Newer valid session | Its connect timestamp was **02:12:17.627593**, consumed promptly and followed by Online and desiredStatus. Both delivered disconnects predate this session. |
| Cloud API | Read at **02:25:12.730**: Offline, `last_online_changed_at=2026-09-13T02:24:30+00:00`; both service instances still reported active. |
| Live guest transport | Same CM PID **55106**, unchanged factory SHA, zero automatic restarts. Monitoring sent at **02:25:31.016804**, ACK received **02:25:31.053943**, Pong sent **02:25:38.476388**, all after the false Offline. |

The exact same consumer tag recurs across historical incidents and the new
channel 1273 timeout. Together with the prior isolated library reproduction,
this strengthens the restored/inactive-consumer hypothesis, but it does not
replace a production coroutine/AMQP trace identifying its original cancellation
or handler stall. The **source of the incorrect Online status is established**:
stale Cloud connection events are released after broker channel timeout, and
the handler blindly applies their boolean state to the Unit without checking
event time or current session. The precise reason that consumer first stops
settling deliveries remains open.

This control also proves the guest did not delay creating those Cloud events:
each embedded timestamp agrees with the Cloud WS close log within milliseconds.
One close followed an explicit CM restart, the other a normal network loss;
neither delayed event represents loss of the current 02:12 session. The same
unchanged CM continues processing acknowledgements after the API says Offline.

Cloud must address both settlement/recovery and stale-event protection. A VM
periodic restart or forced-status timer would only mask the symptom and produce
more connection events; none was added. No restart was made to erase this
reproduction. The external link is ON, services remain running, and the
incorrect Cloud Offline state is deliberately preserved for investigation.

- Broker ACK timeout and channel close (private evidence reference omitted).
- Both stale disconnect receipts (private evidence reference omitted).

Evidence views:

- Initial protocol-7 processing (private evidence reference omitted).
- VDP send failure (private evidence reference omitted).
- Service assignment and dispatch failures (private evidence reference omitted).
- Delayed V7 connection event (private evidence reference omitted).
- Matching broker timeout (private evidence reference omitted).
- Background task selection (private evidence reference omitted), legacy architecture fallback (private evidence reference omitted), strategy factory (private evidence reference omitted), connection-event update (private evidence reference omitted).
