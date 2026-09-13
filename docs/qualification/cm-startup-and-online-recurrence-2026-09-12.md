<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CM startup ordering and delayed Online loss — 12 September 2026

Publication note: private evidence links, infrastructure identifiers and source
locations have been removed. The detailed working report is retained outside
Git under the confidential-input policy; timings and our own conclusions remain.

Status: read-only investigation; delayed delivery localized to a Cloud UMH
consumer acknowledgement timeout. The stale-event overwrite is now reproduced
from Cloud source; conditional ACK/cancellation failure paths are reproduced
locally. Exact production consumer failure attribution remains open. See the
[source and ACK-path follow-up](#source-and-ack-path-follow-up). A later
Offline recurrence supersedes any interpretation of the earlier five-minute
warm-restart observations as a sustained-connectivity pass.

**Patch-causality follow-up:** [CM/SM changes versus the historical Cloud
failure](cm-sm-patch-causality-2026-09-12.md) identifies the same consumer timeout
before application of the recent service-update patches, distinguishes their
real timing/message effects, and corrects the scope of the earlier A/B result.

**Cloud-log follow-up:** the user subsequently provided authenticated Grafana
access. Both Offline transitions coincide with receipt of stale disconnect
events in `CLOUD_INSTANCE_A`, after newer connections. See
[the server-side correlation below](#cloud-log-correlation) and the subsequent
[publisher/broker/consumer trace](#disconnect-delivery-trace). RabbitMQ logs now
identify the queue, consumer and 30-minute acknowledgement timeout at both
transitions. The earlier startup-only hypothesis is not a basis for a CM/SM fix.

## Scope and result

Follow-up to the [controlled CM A/B/A comparison](cm-online-controlled-comparison-2026-09-12.md).
The question was whether cold CM/SM startup differs from an individually
restarted CM. Existing logs and pinned sources were compared. No VM, CM, SM,
VDP, backend or Builder restart, binary replacement, configuration change,
Cloud write, deployment or Production action was performed in this follow-up.

There is an observed startup-order difference and a source-supported difference
in full versus delta UnitStatus generation. However, the restored original CM
subsequently lost Cloud Online **without another restart**, while bidirectional
Cloud traffic and independent Cloud monitoring receipt continued. Startup order
alone therefore does not explain the complete observed failure.

## Exact target and evidence provenance

- Test VM: `5aa1f8e4-a111-4467-a6cc-fb269c62a7a8`, Factory .32.
- Unit: `923b9820-999b-41bb-91db-b2a2c469e743`.
- System UID: `5aa1f8e4a1114467a6ccfb269c62a7a8`.
- Current CM PID: `43568`; active, `NRestarts=0`, original installed SHA
  `85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d`.
- Earlier cold CM PID `1057`, unchanged-binary warm control PID `41710`;
  SM PID `1120` throughout the comparison.

Live observations used Demo Control: `component cm-status test`,
`component cm-compare-startup test`, `unit cloud-status test`, and
`unit monitoring test`. The fixed startup diagnostic is read-only, Test-only,
CLI-only, and reads three bounded journal windows. It returns allowlisted
stages, public identifiers, header fields and booleans, not raw protocol bodies.

The 05:12–05:16 guest journal window is no longer retained: its current read
returned zero records. The cause of that absence was not established. Cold
timestamps and counts below were recovered from previously captured, redacted
Demo Control outputs in this task's local transcript, not a new full wire
capture. The original transcript was neither copied into the project nor
published. Its earlier cold snapshots reported 678 and 1,063 records, with no
reader cap reached. The old projection omitted `isDeltaInfo` and `isConnected`.
Cold flag values must therefore remain inferences, not observations.

## Startup comparison

All times are UTC on 12 September 2026.

| Event | Cold VM startup, CM 1057 | Unchanged CM restart, CM 41710 |
| --- | --- | --- |
| CM starts | 05:12:13.465348 | 10:06:04.978362 |
| Cloud connection established | 05:12:13.902962 | 10:06:05.542862 |
| First UnitStatus sent | 05:12:13.905069; full inferred from source path | 10:06:05.543676; `isDeltaInfo=false` observed; preceding node log has `isConnected=0` |
| SM connects | 05:12:14.357450, before desiredStatus | 10:06:14.937162, after desiredStatus |
| First desiredStatus received | 05:12:14.612554 | 10:06:06.862001 |
| Reconciliation state transitions | None in the preserved filtered snapshots | Downloading → Pending → Installing → Launching → Activating → Finalizing → None |
| Later UnitStatus | 05:12:24.365874; delta inferred, flag unavailable | 10:06:14.984098; `isDeltaInfo=false` observed; preceding node log has `isConnected=1` |
| Bounded Cloud result | Offline transition 05:15:09 | Online beyond five minutes; this leg was then replaced for A/B/A |

The successful warm control also sends its first full report while the node
is not yet connected to CM. Thus “CM connects before SM” is not sufficient to
distinguish success from failure. The cold second report occurs approximately
ten seconds after the node-info update, consistent with the native delta timer;
the surviving evidence does not prove its complete body or flag.

Initial state requests with an empty system ID occur in both cold and warm
starts. Their headers can be constructed while the launcher starts, before
`Communication::Start` loads system information. Associated startup mismatch
errors also occur in the earlier comparison. This is a separate finding, not
an isolated explanation of the delayed Offline transition.

## Source and documentation checks

Sources: `aos_core_cpp` at `da50b60b7d72208bf17ad51250d24dbc727bc679`,
`aos_core_lib_cpp` at `0b82a6bfcb5296ae7cdc97fcd8e9ab58048c30ec`,
API pin `af3552a0a5eb0237eff7f5f183780ca46c339cd3`. The inspected CM startup,
communication, node-info and update-manager files have no diff from the pinned
pre-service-update bases `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` (cpp) and
`60cb83535f773762c61ac5f544b31b7b88c502e3` (lib). This is a scoped comparison,
not a claim that all CM/SM source or packaging is unchanged.

| Code boundary | Behavior in the inspected source |
| --- | --- |
| cpp `src/cm/app/app.cpp`, `src/cm/app/aoscore.cpp` | CM sends systemd readiness after starting its modules. Communication starts after Launcher, SMController and UpdateManager. Readiness is not proof that an SM snapshot or Cloud reconciliation has completed. |
| lib `src/core/cm/updatemanager/unitstatushandler.cpp`: `OnConnect`, `SendFullUnitStatus` | On Cloud connect, send full UnitStatus from the information currently available. |
| Same file: `OnNodeInfoChanged`, `StartTimer` | Accumulate changed node information and send a delta report when the timer fires. |
| lib `src/core/cm/updatemanager/desiredstatushandler.cpp`: `ProcessDesiredStatus`, worker | If desired state already matches, return without a full report. Completion of a reconciliation cycle sends a full report. |
| lib `src/core/cm/nodeinfoprovider/nodeinfocache.cpp` | A provisioned node with SM is connected only when its SM information is available. |
| cpp `src/cm/communication/communication.cpp` | Incoming WebSocket Ping frames are answered with Pong; the recurrence below exercises this path. |

The effective systemd units are both `Type=notify`; SM is ordered after CM.
Making CM readiness wait for SM under that ordering risks a dependency wait.
No new wait, delay, systemd ordering or periodic status workaround was added.
The recent SM pre/post-start service-input preparation can affect timing, but
these observations do not establish it as the cause.

The [protocol schema](https://docs.aosedge.tech/docs/reference/communication-protocol/unit-cloud-protocol)
distinguishes full/delta UnitStatus via `isDeltaInfo`; node `isConnected`
describes its connection to the main node, not the Cloud Unit's Online badge.
The [monitoring guide](https://docs.aosedge.tech/docs/how-to/advanced-device-operation/monitor-device)
distinguishes Offline, Connected and Online, but does not specify the server's
session expiry/state-update algorithm. The [communication description](https://docs.aosedge.tech/docs/aos-core/cloud-communication/)
describes transaction-correlated acknowledgments. An ACK is not proof that
every downstream Cloud status projection was updated.

No external “request full UnitStatus” operation was found in the inspected
protocol, pinned gRPC definitions or CM handler call sites. `stateRequest`
concerns service persistent state; it must not be repurposed as a status request.
This is a statement about the inspected interfaces, not all internal Cloud APIs.

## Decisive follow-up: Offline while the same connection remains active

The final Cloud read unexpectedly showed a new Offline transition at
**10:36:04 UTC**. This is approximately 19 minutes 13 seconds after restored A
became Online at 10:16:51, not another cold startup. Exact Unit API reads at
10:41:26.169925 and 10:41:53.548504 confirmed Offline. The outer CLI result is
PARTIAL because other observations are incomplete; the Unit observation itself
is CURRENT with available transport and no error.

The fixed 10:34–10:42 journal window contains 616 records, with neither the
journal cap nor the event cap reached:

- 24 Pong responses, spaced approximately 20 seconds apart.
- Eight monitoring messages and eight received/handled matching ACKs.
- No logged connection re-establishment, disconnect, new UnitStatus, desired
  status, node-info change or update-state transition in that window.
- The same CM PID and original binary remain active, without a service restart.

| Evidence around the Offline timestamp | UTC timestamp / correlation |
| --- | --- |
| Pong immediately before transition | 10:35:52.485233 |
| Cloud Unit's Offline transition | 10:36:04 |
| Pong immediately after transition | 10:36:12.501866 |
| Monitoring sent after transition | 10:36:50.821905; txn `95647c91-0164-456d-a4d8-caed75d404c9` |
| Matching Cloud ACK received | 10:36:50.874683; same txn and exact system UID |
| Independent monitoring API read | 10:41:55.037394, with node and both services sampled at 10:41:42.107248 |

The independent API receipt matters: this is not merely a successful socket
write or a Pong-only connection. Cloud continues to ingest this Unit's node and
service monitoring while its Unit record says Offline. It does not prove that
new deployments would be dispatched, because no deployment was attempted.

## Conclusions and next boundary

1. The earlier five-minute A/B/A observations remain valid within their windows;
   they are **not** sustained Online qualification. The unpatched B leg was not
   observed for the approximately nineteen minutes now known to precede this
   recurrence, so delayed behavior cannot be cleared for either variant.
2. Initial full/delta report ordering is real evidence to retain, but is not a
   complete explanation or an approved fix. Warm reconnection is not a durable
   recovery, and a cold-start-only explanation is contradicted by this episode.
3. The narrowed boundary is the relationship between a live CM/Cloud session,
   accepted monitoring and the Cloud Unit connectivity record. Which side or
   interaction is wrong remains unproven without server-side correlation.
4. The next useful evidence is the Cloud-side reason for setting this exact
   Unit Offline at 10:36:04: session identifier/owner, any disconnect or expiry
   event, and correlation with the post-transition ACK transaction above.
   Determine whether the status event belongs to the active session or an
   earlier session; do not assume a stale-session event occurred.
5. Keep the current failing session intact for that correlation. Do not reboot,
   reprovision, publish a new version, or add periodic reconnect/full-status
   behavior simply to make the badge green. No such changes are performed here.

Only the fixed read-only Demo Control diagnostic, its tests and documentation
were changed locally. Focused tests: 11 comparison tests and 38 component-runtime
tests passed (49 total); these are local mocked tests, not new live restart runs.
No commit, push, image build, artifact cleanup or Production operation was made.

<a id="cloud-log-correlation"></a>

## Cloud-log correlation supplied through Grafana

This follow-up used the user-provided Grafana Logs UI in the already
authenticated Chrome session. No credentials were extracted, no Cloud or guest
configuration was changed, and no service was restarted. Only bounded historical
queries and English documentation were added; existing source changes belong
to the earlier investigation. No raw log export, token or unrestricted payload
was saved to the repository. Browser display time is CEST (UTC+02:00); all times
in this section are converted to UTC using the log timestamps and query bounds.

The provided `CLOUD_INSTANCE_A` stream is **unit monitoring**. It confirms receipt
and storage of node and service metrics, but it is not the stream containing
the decisive connectivity events. Those are in `CLOUD_INSTANCE_A` (logger
`aos-unit-mh`). `CLOUD_INSTANCE_A` provides the independent acknowledgment trace.

### New connection accepted before old disconnects arrive

In the 10:16:45–10:16:56 Unit Message Handler window (private evidence reference omitted):

- **10:16:51.185:** UMH receives `is_connected=true` for the exact system UID,
  with payload `timestamp=1789208211.175304` (10:16:51.175304 UTC).
- **10:16:51.281–.282:** it receives and begins processing a full UnitStatus,
  `isDeltaInfo=false`, txn `63144f51-9be3-4e3e-9266-533dab2940c9`.
- **10:16:51.356:** the server explicitly logs `Unit status set to online`
  for Unit `923b9820-999b-41bb-91db-b2a2c469e743`.
- **10:16:51.940:** it logs completion of UnitStatus processing. The logs
  identify Brake 8.0.0, Tire 7.0.0, VDP 18.0.0 and Factory .32 rootfs.

In the 10:36:00–10:36:08 UMH window (private evidence reference omitted),
exactly three records report receipt of `is_connected=false` for that same UID:

| UMH receipt, UTC | Timestamp inside the disconnect event | Converted event time, UTC | Event age at receipt |
| --- | --- | --- | --- |
| 10:36:04.949 | `1789207564.910946` | 10:06:04.910946 | 30 min 0.038 s |
| 10:36:04.949 | `1789207889.355056` | 10:11:29.355056 | 24 min 35.594 s |
| 10:36:04.977 | `1789208210.544536` | 10:16:50.544536 | 19 min 14.432 s |

The three embedded times align with the previous CM stop/restart boundaries
in A/B/A. All precede the accepted new connection at 10:16:51.175304. They are
not timestamps of a fresh disconnect at 10:36. Their receipt coincides with
the previously observed Unit API `last_online_changed_at=10:36:04`.
The complete unfiltered eight-second UMH query also returned only these three
records; there is no explicit database-write line for Offline in that window.

### The first cold-start failure has the same signature

The 05:15:00–05:15:20 UMH window (private evidence reference omitted)
returns two disconnect messages for the same system UID:

| UMH receipt, UTC | Timestamp inside the event | Converted event time, UTC |
| --- | --- | --- |
| 05:15:09.622 | `1789188533.048453` | 04:48:53.048453 |
| 05:15:09.633 | `1789189930.847289` | 05:12:10.847289 |

Both predate the new VM/CM connection at 05:12:13.902962. Their receipt again
coincides with the earlier Unit API Offline transition, 05:15:09. Thus this
correlation is not confined to the warm-restart comparison.

### Independent server-side evidence of the live data path

The WS stream around the transition (private evidence reference omitted)
continues logging ACKs with trace `f413036d341b52b1cf880566f1e73369` and span
`5ae25a723e6cd461`, also present at the new connection's 10:16:51 report.
At 10:36:50.868 UMH receives monitoring txn
`95647c91-0164-456d-a4d8-caed75d404c9`; at .869 it starts processing, and at
.920 reports completion (51.363 ms). Unit monitoring logs storage at .880,
with trace `28cbb593ebfe1c21f44f16c0a464422c`.
This independently matches the guest-side transaction recorded earlier.

The exact-UID monitoring query over 10:30–10:45 returned 15 storage records,
one per minute. Recent monitoring for the same UID was also visible in the
original user-provided view. No new release was sent to test dispatch while
Offline, so successful monitoring must not be reported as successful deployment.

### Interpretation before the broker trace

**High-confidence incident explanation:** delayed disconnect events for earlier
connections reach UMH after a newer connection has already been accepted; the
Unit's Offline timestamp changes at their receipt despite the current data path
remaining active. This points to Cloud connectivity-event ordering/handling,
not an established need to change SM startup or CM reconnect logic.

What is directly proven is event contents, receipt ordering, the earlier
explicit Online write, two matching Offline transition times, and continued
monitoring. The exact Offline database-write call, stale-event guard behavior,
queue topology, and cause of delayed receipt were not visible in that first
log set. The subsequent investigation below closes the broker boundary, not
the exact consumer code defect. An event age close to thirty minutes does **not** by itself prove a
particular broker timeout, TTL or retry mechanism.

The bounded checks of `cms` and `mh` with the exact UID over 10:30–10:45,
and `ws`, `qm`, and `bg-tasks` without a text filter over 10:36:00–10:36:08,
did not expose a producer/queue explanation. These empty searches are not
proof that those services cannot participate in the path.

For the Aos Cloud team, the next precise checks are:

1. Trace publication, delivery and any redelivery of the five disconnect
   events above; establish why receipt lagged behind newer connection events.
2. Inspect the consumer's protection against stale connectivity transitions:
   can an older disconnect overwrite a newer connection/Online state? Verify
   using actual session identity/generation and timestamp semantics, not an
   assumed time-only rule.
3. Reproduce delayed and out-of-order disconnect delivery against an active
   session, then verify both Unit Online and desiredStatus dispatch. No Cloud
   patch or new runtime workaround was implemented by this investigation.

## Disconnect delivery trace

The next read-only investigation followed the user's question about who sets
disconnect timestamps, delayed delivery, and possible influence of the recent
CM changes. All times below are UTC on 12 September 2026 unless stated otherwise.

### WebSocket closure was observed promptly by Cloud

Unfiltered, narrow `CLOUD_INSTANCE_A` windows show actual server-side closes of
the exact System UID, not merely local CM intent to close:

| WS log body: websocket disconnected | Later event timestamp | WS trace ID |
| --- | --- | --- |
| 10:06:04.909, close code 1000 | 10:06:04.910946 | `bb6365a88a76ebab3e6f63f7c8354c24` |
| 10:11:29.352, close code 1000 | 10:11:29.355056 | `1cb309243db37e166c5cd732c9cfba63` |
| 10:16:50.542, close code 1000 | 10:16:50.544536 | `952efa51eaa2e0fa04cffb1ed472c435` |

The second row's Grafana entry timestamp is 10:11:29.353; its log body reports
10:11:29.352. These millisecond-level differences are not the minute-scale
delivery problem. Generic `connection closed` records follow each entry.
The last closure is the unpatched-B session stopped for restoration of A.

Last close window (private evidence reference omitted).

**Timestamp interpretation:** these are old but temporally consistent closure
timestamps, not evidence of a bad VM clock. The internal numeric timestamp
tracks Cloud's observation of the old connection closing. The precise Cloud
function that constructs it has not been inspected; assigning it to a specific
Python function or claiming its clock source from source code would overstate
the evidence.

### RabbitMQ identifies the delayed-delivery mechanism

The 10:35:55–10:36:10 broker window (private evidence reference omitted)
contains three relevant records:

- **10:36:04.946749:** consumer acknowledgement timeout on queue
  `connection-event queue`, channel **1267**, delivery tag **1**;
  timeout **1800000 ms**.
- **10:36:04.947303:** `precondition_failed` channel exception and closure.
- Connection identity: `<0.4199631.0>`, client `PRIVATE_ENDPOINT`, broker
  `PRIVATE_ENDPOINT`; consumer tag
  `CONSUMER_A`.

UMH receives the first two old disconnects at **10:36:04.949**, approximately
two milliseconds after channel closure; the third arrives at **10:36:04.977**.

The 05:15:00–05:15:15 broker window (private evidence reference omitted)
shows the same queue, connection, client, consumer tag and timeout: warning at
**05:15:09.619685**, channel **1263** closure at **05:15:09.620499**, followed by
UMH disconnect receipt at **05:15:09.622** and **05:15:09.633**.

[RabbitMQ's acknowledgement-timeout documentation](https://www.rabbitmq.com/docs/consumers#acknowledgement-timeout)
explains that an unacknowledged delivery causes channel closure and requeueing
of outstanding deliveries. That documented mechanism fits both observed
bursts. The timeout is for consumer acknowledgement, not a configured delay
before CM sends a disconnect. Different message ages in one burst are
consistent with multiple outstanding deliveries on the channel. The retrieved
UMH logs do not expose AMQP `redelivered` flags or map delivery tag 1 to a
specific payload; those details remain unverified.

### The consumer belongs to Cloud UMH

A historical Prometheus query, `kube_pod_info{pod_ip="PRIVATE_ENDPOINT"}`, over
**10:35–10:37** identifies namespace `production`, pod
`CLOUD_INSTANCE_A`, owned by ReplicaSet
`CLOUD_INSTANCE_A`. This is the client address from the broker's error,
not the VM. A current-time query returned no data, so the mapping is explicitly
historical, not a claim about the current pod inventory.

The same pod's UMH logs contain repeated
`connection events consumer stuck, restarting channel` warnings, including
**10:07:09.978**, **10:11:05.564**, **10:16:30.032**, **10:21:30.047**,
**10:21:51.197**, **10:26:30.059**, **10:26:51.208**, **10:31:30.072**, and
**10:31:51.221**. They establish that the Cloud application itself reports
consumer recovery activity. They do not prove which coroutine was blocked,
whether an ACK was omitted, or whether a channel was incorrectly replaced.

Separately, the pod logs reject state messages after three retries at
**10:17:21** with `Actual state for service ... instance 0 not found`, for
both the exact Brake and Tire service IDs. Their transaction IDs are
`a87b4ad6-993a-4a4f-9c37-7bc16fd906da` and
`8cde88b1-45a1-4403-b02a-5203196889dc`. These are service-state errors, not
established causes of the connection-event ACK timeout; do not conflate them.

### What the CM source comparison establishes

The pinned CM transport source, `src/cm/communication/communication.cpp`, is
unchanged against the pre-service-update cpp base recorded above:

- `Communication::Stop` calls `CloseConnection` before joining its threads.
- `CloseConnection` calls WebSocket `shutdown()` and resets the client session.
- `NotifyConnectionLost` invokes local subscribers' `OnDisconnect` callbacks;
  it does not create the Cloud internal `is_connected=false` JSON envelope.
- Normal CM message headers set `createdAt` using `Time::Now()`; this is a
  different field/envelope from the numeric timestamp in the Cloud event.

Both packaged CM patches were inspected: `0001-serialize-sm-stream-writes`
shares a mutex for CM–SM gRPC writes; `0002-reconcile-stale-instance-snapshot`
changes running-instance reconciliation. Neither edits WebSocket close logic
or constructs the internal connectivity event. Cloud also observes closure of
the unpatched-B session promptly. Therefore, **a CM-side delay in emitting
these closes is contradicted by the server logs**. This is not blanket proof
that all CM changes are harmless: new message content/order could expose a
Cloud consumer defect, and that indirect relationship remains untested.

### Remaining precise Cloud-team checks

1. Locate the `connection-event queue` consumer corresponding to the tag
   above. Inspect ACK/NACK, exception/cancellation and channel-recovery paths,
   including the code that emits `connection events consumer stuck`.
2. Confirm which deliveries were held unacknowledged and then redelivered;
   correlate the old timestamps with publisher records and AMQP delivery data.
3. Inspect the event timestamp constructor and the protection preventing an
   older session's disconnect from setting a newer session Offline.
4. Determine whether the independent service-state errors share a failing
   processing path; no causality is assigned from timing alone.

No Cloud backend source was available in the inspected local repositories;
public-source lookup did not resolve the internal handler. A broker search
for this queue over 10 September returned no matches; it neither establishes
the first occurrence nor clears indirect regression influence. No runtime or
configuration change, restart, deployment, broker operation, build, commit,
push or cleanup was performed. Only this evidence and the plan checkpoint
were updated; the failing VM/session is preserved.

<a id="source-and-ack-path-follow-up"></a>

## Cloud source and ACK-path follow-up

### Scope and baseline clarification

The user supplied access to the private Cloud repository and subsequently
confirmed that the mainline implementation is deployed in production. GitLab
identifies the default branch as `master`, not literally `main`; the observed
repository HEAD is `private source revision withheld`. The deployment
equivalence is user-confirmed, not independently verified from an image digest.
Earlier statements in this chronological report that source was unavailable,
the timestamp constructor was unknown, or the state-write guard was uninspected
are superseded by this section.

The current instruction prohibits production modifications. VM code changes
are permitted, but none were necessary or performed in this follow-up. Browser
access was used only for authenticated repository reading and historical
Grafana queries because equivalent authenticated CLI access was unavailable.
No Cloud/VM restarts, deployments, builds, mutations or new reconnects occurred.
Private Cloud source copies and isolated tests remain in temporary directories,
not in this public-source repository. No commit or push was performed.

### Confirmed stale-event overwrite

Cloud WebSocket API `the disconnect publisher` constructs `event_ts` using its own
`datetime.now().timestamp()` after attempting Redis deletion and before
publishing the disconnect. The corresponding connect path creates its own
Cloud timestamp. See WebSocket connection lifecycle (private evidence reference omitted).

`the connection-state handler` does not pass the event's
timestamp into `the state update operation`. The database update matches only
`Unit.system_uid`, writes Connected or Offline from the boolean flag, and sets
`last_online_changed_at` to processing time. No event ordering or session guard
exists in that method. A full UnitStatus subsequently promotes Connected to
Online. See the handler (private evidence reference omitted).

Unchanged extracted handler methods with a mocked database and clock reproduce:
new connection -> Online fixture -> older disconnect -> Offline. This proves
the source behavior; it is not an actual PostgreSQL or production integration
test. The previous production timeline strongly matches this mechanism.

### Exact ACK/reject/NACK paths

These are Cloud UMH-to-RabbitMQ acknowledgements, not the application-level
Cloud ACKs sent back to CM for monitoring transactions.

| Consumer path | What settles the delivery | Where settlement can be absent |
| --- | --- | --- |
| Handler succeeds | `message.ack()` after handler completion | Handler/DB wait or channel write can prevent completion. |
| Malformed connection event | `message.reject(requeue=False)` | Reject can fail on a broken channel. |
| Handler exception, retry count below three | Republish with incremented retry header, then ACK original | Republish must complete before original ACK; it has no explicit deadline here. |
| Retry budget exhausted | Reject without requeue | No guaranteed settlement if the channel operation fails. |
| Iterator shutdown | Library NACKs buffered messages with requeue | The NACK loop occurs only after consumer cancellation completes. |
| Channel/connection disappears with unsettled deliveries | Broker requeues outstanding messages | Client need not send NACK; the broker channel-close path handles redelivery. |

The Cloud business-error path uses republish-plus-ACK or reject; it does not
normally call NACK. The relevant NACK loop is in aio-pika iterator cleanup.
`ack()` sends `basic_ack`; it does not receive a broker confirmation of that
ACK. See UMH consumer (private evidence reference omitted)
and [aio-pika ACK implementation](https://github.com/mosquito/aio-pika/blob/9.6.2/aio_pika/message.py#L441).

### Locally reproduced cancellation hole

Cloud common requirements pin `aio-pika==9.6.2`. The following conditional path
was reproduced using unchanged method bodies extracted from Cloud and that
library version:

1. Cloud constructs `queue.iterator()` without an iterator timeout and awaits
   `__anext__()` through `asyncio.wait_for(..., timeout=300)`.
2. Expiry cancels `__anext__`, but Python waits for cancellation to finish.
3. `RobustQueueIterator.__anext__` catches cancellation and awaits its own
   `close()`. With empty iterator timeout kwargs, this wait has no deadline.
4. Iterator close deletes its consumer tag and then awaits queue cancellation.
5. Buffered messages are NACKed only after cancellation returns.
6. If cancellation stalls, callbacks can buffer deliveries while the application
   handler, ACK/NACK, timeout warning and Cloud's later five-second cleanup are
   all unreached.

Sources: [Python wait_for semantics](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait_for),
[robust iterator cancellation](https://github.com/mosquito/aio-pika/blob/9.6.2/aio_pika/robust_queue.py#L229),
[queue close ordering](https://github.com/mosquito/aio-pika/blob/9.6.2/aio_pika/queue.py#L476).

Test results, using scaled timeouts and mocked transport/DB:

- Healthy idle timeout: cancellation and channel cleanup complete.
- Injected cancellation wait: still blocked beyond five times the configured
  idle timeout; three buffered messages; ACK=NACK=reject=0; no handler-entry or
  timeout warning. Releasing the wait permits NACKs and then the warning.
- Injected handler/DB wait: first delivery in flight, two buffered, no settlement
  until the wait is released; the 300-second next-message guard does not apply.
- Injected retry-publication wait: same unsettled-delivery behavior, with the
  retry warning already emitted.

The injected cancellation/DB/publication stalls are test preconditions, not
observed production stack traces. All cases passed in the root agent's rerun.

### Conditional restored consumer with no active reader

A second exact-method test reproduced this library lifecycle hazard:

1. Iterator close deletes `_consumer_tag` before awaiting `RobustQueue.cancel`.
2. If cancellation raises, the robust queue retains its callback in
   `_consumers`, because removal occurs only after the cancellation RPC succeeds.
3. A later close sees no iterator tag, skips the buffered-message NACK loop,
   and marks the iterator closed.
4. If that queue is subsequently restored, the retained callback can be
   registered again under the same consumer tag.
5. Messages then enter the closed iterator's buffer; `__anext__` immediately
   stops and does not process or acknowledge them.

Sources: [cancel bookkeeping](https://github.com/mosquito/aio-pika/blob/9.6.2/aio_pika/robust_queue.py#L150),
[consumer restoration](https://github.com/mosquito/aio-pika/blob/9.6.2/aio_pika/robust_queue.py#L57).
Successful Cloud channel cleanup normally prevents continued use of a retired
channel. The test injects cancellation failure and later restoration; production
occurrence of those prerequisites is not yet proven.

Reproduction location: `/private/tmp/aos-ack-analysis.8Fbpq0/reproduce_ack_paths.py`.
Dependency source and original Cloud excerpts remain outside Git. No broker,
socket, live database or VM is used by this test.

### Additional historical log evidence

A query across **all UMH streams**, 10:05:50–10:36:10, matching the three exact
disconnect timestamps returned exactly three records, all at 10:36:04.949/.977.
No earlier handler-entry record for these events was retrieved. Subject to log
completeness, this disfavors those particular events entering the handler and
then waiting in the database at their original timestamp. A previously blocked
different delivery on the same consumer remains possible.

An affected-pod query for connection events over 09:35–10:06:10 returned one
record: our new connection at 10:06:05.541. An affected-pod error/retry/idle query
over 09:55–10:36:10 returned 14 idle warnings, no connection-event retry/error
records. Warnings continued in two interleaved log-prefix sequences every five
minutes. This shows ongoing consumer activity, but the prefix was not mapped
to a consumer tag or coroutine.

A broader broker query for the exact consumer tag (private evidence reference omitted)
returned four acknowledgement timeouts:

| UTC | Channel | Delivery tag | Timeout |
| --- | --- | --- | --- |
| 04:39:53.061738 | 1261 | 1 | 1800000 ms |
| 05:15:09.619685 | 1263 | 1 | 1800000 ms |
| 07:52:09.605758 | 1265 | 1 | 1800000 ms |
| 10:36:04.946749 | 1267 | 1 | 1800000 ms |

The same consumer tag repeatedly appearing on replacement channels and timing
out on delivery 1 is consistent with a restored consumer that does not make
processing progress. It strengthens the orphan/restore hypothesis but does not
prove which cancellation, restore or handler wait caused it.

An all-UMH query over 09:55–10:36:10 for the exact consumer tag, Basic.cancel,
iterator-cancellation, failed-NACK, ChannelInvalidState and PRECONDITION_FAILED
signatures returned no records. Library debug logging may not be collected;
this absence is not proof that cancellation succeeded or failed.

### Current conclusion and VM boundary

The stale-event status overwrite is confirmed in source and locally reproduced.
There are code-reproduced ways for Cloud deliveries to remain unsettled despite
the nominal timeouts. Repeated broker failures now make consumer lifecycle and
restoration the leading investigation direction; exact incident attribution
remains conditional without consumer-level callback/cancel/ACK traces.

Changing CM cannot directly ACK this queue: its consumer runs in Cloud UMH and
uses Cloud-internal AMQP delivery tags/channels. A VM reconnect can create a new
connection event and temporarily recover status, but can also create another
old disconnect to be processed later. It is not an ACK-path fix. No VM code
change or reconnect workaround was introduced merely to hide the failure.
