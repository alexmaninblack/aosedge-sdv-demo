<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CM reconnect blocked by Monitoring/Communication lock inversion

Date: 19 September 2026. Historical status: live failure reproduced and
diagnosed; no native patch or restart during that investigation. The later
[authorized source correction and isolated qualification](cm-disconnect-lock-fix-2026-09-19.md)
are recorded separately. No live deployment, upstream submission or completed
E2E qualification is implied by that follow-up.

## Preserved reproduction

The [continuous Factory .35 run](continuous-factory-35-e2e-2026-09-19.md)
uses staging `aws-stage.epmp-aos.projects.epam.com`, current Test Unit
`cb64acb2-12fd-4340-8962-eca8d43465f1`, system UID
`1ac3b4f2cfe74e8988e6974637ab7afc`. Factory source is Platform
`bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74`; the existing image is patched,
not stock mainline. VDP 82/V3, Brake 63/V3 and Tire 36/V1 were installed.
Tire 37/V1 was published while the external link was off and is pending.

1. Native External network off at about 10:37:45 UTC. Cloud became Offline.
2. Local services continued real analytics, typed advisory and two token
   renewal cycles. Backend ingestion stopped; products accumulated durably.
3. Native External network on at about 10:44:55. The owned guest filter
   reported ON. Service backend communication recovered independently.
4. At **10:45:07**, CM logged `Received close frame, disconnecting`,
   `Disconnect from web socket server`, `Close web socket connection`,
   `Send close frame`, then `Connection lost`. No later reconnect attempt
   was observed in the bounded journal checks. Cloud remained Offline.
5. CM PID **1588** remained active, `NRestarts=0`, `ExecMainStatus=0`.
   It was not stopped/restarted to make the run pass.

The server-side cause of the close frame was not established by this probe.
It is distinct from the local failure to complete disconnect and reconnect.
No thirty-minute RabbitMQ timeout is needed to explain the blocked CM threads.

## Live stack evidence

One read-only GDB attachment briefly paused only CM, printed backtraces with
frame arguments/entry values disabled, and detached successfully. No locals,
credential bytes, token claims or core dump were read or persisted. Relevant
symbol-only chains from the same snapshot:

| LWP | Stack, outer caller to blocked operation |
| --- | --- |
| 1698 | `HandleConnection → Disconnect → CloseConnection → NotifyConnectionLost → Monitoring::OnDisconnect → pthread_mutex_lock` |
| 1668 | `Monitoring::SendMonitoringData → Communication::SendMonitoring → EnqueueMessage → pthread_mutex_lock` |
| 1667 | Another `Monitoring::SendMonitoringData → pthread_mutex_lock` |
| 1979 | `SMHandler::ProcessMessages → ProcessInstantMonitoring → Monitoring::OnMonitoringReceived → pthread_mutex_lock` |
| 1691 | `DesiredStatusHandler::Run → SendFullUnitStatus → SendUnitStatus → EnqueueMessage → pthread_mutex_lock` |

The first two stacks and the source lock scopes establish the AB/BA cycle:

- Disconnect owns **Communication mutex**, invokes subscriber callbacks and
  waits for **Monitoring mutex** in `Monitoring::OnDisconnect`.
- Monitoring owns **Monitoring mutex**, calls the sender and waits for
  **Communication mutex** inside `EnqueueMessage`.

The full-status worker and SM monitoring receiver are additional victims,
not evidence that service analytics or backend delivery are broken.

## Source and current upstream comparison

The local Communication source inspected at
`da50b60b7d72208bf17ad51250d24dbc727bc679` has the same relevant file as
the recorded `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` baseline.
The local library Monitoring file is unchanged from accepted library pin
`60cb83535f773762c61ac5f544b31b7b88c502e3`. These source comparisons do not
claim an unpatched runtime A/B experiment.

Official upstream HEADs were resolved read-only on 19 September, then exact
immutable source files were retrieved. The same lock order remains in:

- [AosCore Communication, 9d613a46](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/src/cm/communication/communication.cpp#L716):
  `Disconnect` holds its mutex through `CloseConnection`; that method calls
  `NotifyConnectionLost`, which synchronously invokes `OnDisconnect`.
  `EnqueueMessage` acquires the Communication mutex at line 1078.
- [AosCore Monitoring, 5560291b](https://github.com/aosedge/aos_core_lib_cpp/blob/5560291ba6914e36a5b841ade4d8fc54134a9e91/src/core/cm/monitoring/monitoring.cpp#L201):
  `OnDisconnect` acquires the Monitoring mutex. `SendMonitoringData` at
  line 274 holds that same mutex through the external sender call.

Therefore simply choosing those current HEADs does not remove this source
cycle. Neither current upstream revision was built or installed in this test.
Existing demo stream-write/status-refresh patches were not proven to be the
root cause: the conflicting lock scopes exist outside those changed sites.
They may affect scheduling; no claim about their effect on probability is made.

## Independent results and remaining boundary

The deliberately stopped Tire backend was restored with its database intact.
All **18 captured Brake** and **30 captured Tire** offline product hashes
matched exactly one durable receipt each, with no missing/duplicate rows.
Both function-report queues drained and current real input returned in UI.
The Tire popup distinguished source time 10:39:33 from receipt 10:48:15;
the late receipt was not relabelled as a new drive or new service release.

Tire replacement is **not passed**: Cloud still reports installed 36 and
pending 37. Preserve this Test, pending release and CM failure; do not Finish,
rebuild, reprovision or restart before deciding the bounded recovery approach.

Recommended next decision: review this lock-order defect with the platform
team, agree the smallest upstream-candidate correction, and require a
deterministic disconnect-versus-monitoring concurrency regression followed by
this real external-off/on scenario. Do not delete mutexes or add a watchdog
restart as a substitute. Current ADR 0017 does not authorize installing another
native CM patch in this increment. This handoff has not been sent externally.

## Read-only second review before any recovery

The operator requested another analysis before starting or restarting anything.
This review changed no product source, guest configuration, network rule,
service, package or Cloud object. It reused the preceding symbol-only stack
snapshot; it did not attach GDB again, run a candidate or build an image.

### Fresh observations, 11:08–11:11 UTC

- CM still has PID 1588, `active/running`, exit status 0 and zero restarts.
  The five previously identified blocked LWPs still wait in
  `futex_wait_queue`. This follow-up alone is not a new full-stack proof;
  it corroborates persistence of the earlier diagnosed failure.
- The filtered CM journal still ends its connection sequence at 10:45:07
  `Connection lost`; no subsequent connection/retry event was found.
- The standard read-only connectivity command at 11:11:20 reports ON,
  `OWNED_GUEST_PACKET_FILTER`, `noOp=true` for this Test.
- The selected staging Cloud observation at 11:10:48 reports the exact Unit
  as provisioned and Offline. Cloud reports `last_online_changed_at`
  10:38:16 UTC. This is the server-reported transition time, not a separately
  measured packet-loss latency. Installed VDP remains 82.0.0.

### What the network action does, and does not do

`ConnectivityService.execute` dispatches only the selected guest connectivity
action. In `source_guest.py`, `external_connectivity` adds/removes an owned
`inet` nftables table, covering input/output/forward and IPv4/IPv6. OFF silently
drops external traffic while retaining the explicit local maintenance/VISS
paths. ON removes that table and verifies its absence.

There is no CM stop/restart, WebSocket close request, guest reboot or direct
Cloud mutation in that action. ON is evidence about this owned filter, not a
promise that every application session has recovered. A silent drop also need
not immediately notify a socket consumer. The exact server decision behind the
subsequently received close frame remains unknown. Even a legitimate server
close must not leave the client's reconnect worker mutually blocked.

### Comparison with the successful run

The [preceding preserved-Test run](preserved-test-function-observation-2026-09-19.md#external-network-off-and-queued-delivery)
used the same accepted Factory .35 baseline and staging endpoint:

| Observation | Earlier successful run | Current blocked run |
| --- | --- | --- |
| External OFF / ON, UTC | 04:55:28.769 / 05:00:18.596 | About 10:37:45 / 10:44:55 |
| Cloud outcome | Offline observed 04:58:56; Online observed 05:01:22 | Offline; no return Online in the bounded checks |
| Installed profiles during outage | VDP79/V3, Brake60/V3, Tire35/V1 | VDP82/V3, Brake63/V3, Tire36/V1 |
| Captured queued products | All 31 received exactly once | All 48 received exactly once |
| Update context | Retained-Test successor proof | Clean profile transitions; Tire37 published while OFF |

No new Factory image separates these two tests. The current platform recipe
diff against Factory source `bb691efc` is empty for the inspected CM/SM/IAM
recipe directories. The earlier run was not an unpatched-versus-patched A/B
experiment, and its thread interleaving was not captured. Different duration,
message backlog and update context are possible timing factors, not established
causes. Neither “the longer outage caused it” nor “a service version caused it”
is supported by these observations.

### Patch causality review

| Accepted delta | Actual affected boundary | Relevance to this occurrence |
| --- | --- | --- |
| Shared gRPC write mutex, `0001` | `SMHandler` and `SyncMessageSender`; upstream backport `6e0b1980` | Not the two mutexes in the live cycle. Removing it would undo stream-write serialization, not establish a fix for this cycle. |
| Stale-instance reconciliation, `0002` | Launcher instance identity/version reconciliation | Does not edit Communication/Monitoring lock scopes. |
| Idle full status, `0003`/`0004` | Existing desired-status worker, snapshot handling and 60-second configuration | Adds status traffic; its worker is blocked behind Communication in the snapshot. A probability/timing effect has not been measured. |
| Pending startup rebalance, `0005` | Launcher scheduling trigger preservation | Does not edit the conflicting lock scopes. |
| Permission-key capacity 256 | Compile-time string capacity in native modules | Does not change the demonstrated synchronization order. |

Local Communication is unchanged against its recorded `9eecb80c` baseline;
Monitoring is unchanged against library pin `60cb8353`. The exact official
upstream source links above were retrieved again and retain the same cycle.
These are source comparisons, not proof that the entire deployed image is
unmodified upstream or that all indirect effects of our deltas are excluded.

### Additional source risks and the missing test

The local Alerts implementation has the same structural pattern:
`Alerts::SendAlerts` holds its mutex while calling the Communication sender;
`Alerts::OnDisconnect` needs that mutex under Communication's disconnect
callback. This is a source-level second route, **not** the observed active
deadlock, which remains Monitoring. A Monitoring-only workaround would not
address the common callback-under-transport-lock design.

`Communication::Stop` also calls `CloseConnection` while holding the transport
mutex. Moving only the call in `Disconnect` would leave that entry point
unreviewed. Callback subscription uses a separate mutex and raw listener
pointers, and `IsConnected` reads under the transport mutex whereas the
notification functions assign under the subscription mutex. A proposed
correction must explicitly preserve listener lifetime, event ordering and
consistent connection-state synchronization; simply unlocking around raw
pointer iteration is not a reviewed solution. These are review requirements,
not additional live-failure claims. Normal application cleanup is reverse
startup order; arbitrary concurrent unsubscribe has not been reproduced here.

The inspected native `CMCommunicationTest.Reconnect` uses a simple connection
subscriber stub. `CMCommunicationTest.SendMonitoring` sends a message as a
separate test. Library `CMMonitoring` tests use a `SenderStub` and mocked Cloud
connection, not the real Communication object. Thus those tests do not exercise
the demonstrated mutual lock dependency. This review inspected their source;
it did not rerun them or claim a new concurrency regression has passed.

### Required next proof, not an implementation approval

1. Preserve this Test and the separate known shared-storage defect. Restart is
   not a correctness test and may re-enter the previously diagnosed cleanup
   path; no automatic recovery action is authorized by this analysis.
2. Add an isolated native concurrency regression that deliberately overlaps a
   monitoring send with disconnect notification using deterministic barriers,
   rather than relying on repeated sleeps or Cloud outages. Require bounded
   completion and the next successful connection. Run the equivalent Alerts
   case and cover Stop, notification ordering and listener lifetime.
3. Review a minimal upstream-candidate correction at the shared connection
   notification boundary. Protect transport/queue objects but avoid calling
   subscribers under the transport lock. A sender-side snapshot alternative
   must also preserve concurrent new samples and failed-send retention. Neither
   alternative is implemented or installed by this review.
4. Only after approval and isolated gates, perform a scoped live correction
   and repeat network OFF/ON with active monitoring, backlog and service
   publication. Independently require Cloud Online, installed Tire37 evidence,
   preserved state, local analytics and exact backlog delivery. A rebuilt image
   with unchanged synchronization logic cannot establish that this is fixed.

The Cloud close-frame origin and patch-related timing effects remain open.
They do not negate the demonstrated local wait cycle, and this review does not
reclassify the incident as the historical thirty-minute Cloud/RabbitMQ problem:
here Cloud did observe Offline; the client fails to reconnect afterwards.

## Follow-up mainline and patch inventory

The operator subsequently requested a wider review of mainline synchronization
fixes and obsolete demo patches. The
[main/develop and patch audit](aoscore-mainline-sync-and-patch-audit-2026-09-19.md)
records exact current refs, related SM/timer fixes, develop-only reconnect
changes, residual lock scopes and per-patch migration disposition. It does not
authorize or claim an upstream runtime upgrade; the failing Test is preserved.

## Authorized repeat network OFF/ON, 2026-09-19

The operator requested one additional network cycle before a correction. This
was a recovery test of the already blocked CM, not an independent reproduction
starting Online. No CM/VM restart, native patch, service publication or driving
mode change was added to the experiment.

| Observation (UTC) | Result |
| --- | --- |
| 11:29:44–46 preflight | Cloud Unit `cb64acb2-12fd-4340-8962-eca8d43465f1` already Offline; external network ON; CM PID 1588 active, zero restarts; previously diagnosed threads 1698 and 1668 waiting on futexes. |
| 11:30:42.697879 | `vehicle connectivity off --target test` completed, OFF, not a no-op. |
| 11:31:53 | Same CM PID, zero restarts, same two threads still waiting. |
| 11:32:00.291172 | `vehicle connectivity on --target test` completed, ON, not a no-op; approximately 77.59 seconds between OFF and ON completion. |
| 11:32:22–24 | Fresh Cloud observation still Offline; same CM PID; no new filtered connection/retry events. |
| 11:38:25–33 | Fresh Cloud observation still Offline, installed VDP `82.0.0`; CM PID 1588 active with zero restarts; both previously diagnosed threads still in `futex_wait_queue`; no matching connection/retry events since 11:30:35. |
| 11:38:41.935616 | Final owned-packet-filter observation confirms external connectivity ON. |

Restoring network access did not release the existing mutex wait cycle or
produce a CM reconnect attempt during the observation window. The repeated
thread wait-channel checks are consistent with the earlier full stack proof;
they do not independently establish a new lock ownership snapshot. The Cloud
still reports `last_online_changed_at` as `2026-09-19T10:38:16+00:00`.

The Test is left intact with external connectivity ON. Backend receipt counts
and backlog integrity were not requalified in this repeat. A fresh
Online-to-Offline-to-Online experiment first needs a separately scoped recovery
step; the existing shared-storage cleanup risk must be accounted for before
restarting CM. This result is not evidence that a network toggle fixes the
deadlock, nor that a new mainline binary has been tested.

## Deterministic native regression — authorized and executed

The operator then authorized the proposed isolated test. The new
[native lock harness](../../tests/upstream/cm-lock-harness/CMakeLists.txt)
compiles real Communication, Monitoring and Alerts implementation files with
their supporting source. No native source correction or live recovery was
included. The preserved VM, CM, CARLA, network settings, services and Cloud
objects were not changed by this test execution.

### Exact inputs and isolation

- Local core checkout HEAD: `da50b60b7d72208bf17ad51250d24dbc727bc679`.
- Local library checkout HEAD: `0b82a6bfcb5296ae7cdc97fcd8e9ab58048c30ec`.
- Existing unrelated worktree edits were preserved, not reset. The three
  implementation files below have exactly the same SHA-256 as the recorded
  upstream core `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` and library
  `60cb83535f773762c61ac5f544b31b7b88c502e3` blobs respectively:

| Implementation | SHA-256 |
| --- | --- |
| Communication | `4550ebc0003a8aa663672453140ad3d17df7a0c41c27b03c219562be34cd5991` |
| Monitoring | `cab2eaf12d2f058dff833697c393ac8126adaba88aad0386adef48d7be79b72f` |
| Alerts | `4d21d60ef57ba113809dac4469e57f377384f2a1aed704e1983a58aae27dcc05` |

The test ran in an isolated Linux ARM64 container with external networking
disabled, read-only source mounts and no VM/runtime/credential mounts. Test
dependencies were prepared separately in a disposable image; none was installed
on the guest. The test uses GCC 12.2, Debian Poco 1.11.0, OpenSSL 3.0.20 and
function-only GDB stack capture. It is not a byte-identical deployment build.

The executable is an ARM64 ELF, dynamically linked, with debug information:
12,082,816 bytes, SHA-256
`b8f64551278f47e42636c3eefd4e7fdcd46f432f2fb391acffbd1ddb504d668e`.
The isolated build and evidence remain under
`/private/tmp/aos-cm-lock-test.5CpXWu` (approximately 63 MiB).
The initial eight-case run is in `results/`; the two repeated runs are in
`repeated-results/`. Both contain structured results and synthetic-process
stacks. Temporary test containers were removed after execution; the test image
and incremental build cache are deliberately retained. No core dump was made.

### Scheduling and result

An actual local WebSocket exists before each disconnect. The real sender is
paused at its UUID dependency after the running-state guard and before queue
locking. Its Monitoring/Alerts mutex is already held. A second thread invokes
real Disconnect or Stop; the forwarding subscriber marks callback entry and
calls the real OnDisconnect. The coordinator observes the native lock state,
then releases the sender gate. Both operations must finish. A generic timeout
alone is insufficient: each recorded failure also requires completed gates and
the paired native blocked stacks.

| Case | Serial schedule, three runs | Forced overlap, three runs |
| --- | --- | --- |
| Monitoring + Disconnect | 3 PASS | 3 FAIL: confirmed native deadlock |
| Monitoring + Stop | 3 PASS | 3 FAIL: confirmed native deadlock |
| Alerts + Disconnect | 3 PASS | 3 FAIL: confirmed native deadlock |
| Alerts + Stop | 3 PASS | 3 FAIL: confirmed native deadlock |

Totals: **12 PASS controls; 12 FAIL regressions**, all twelve failures with
completed rendezvous, released test gate and matching native wait-cycle stacks.
The runner returns failure, not an expected-pass result. Serial cases complete
in approximately 0.26 seconds; concurrent cases fail the two-second completion
check, are captured at the five-second process deadline and then terminated.
These are test watchdogs, not a change to demo timing policy. An additional
initial Monitoring/Disconnect serial smoke also passed before the matrix.

Representative paired stacks, excluding the test forwarding frame:

```text
Disconnect or Stop
  -> CloseConnection -> NotifyConnectionLost
  -> Monitoring::OnDisconnect -> pthread_mutex_lock

Monitoring::SendMonitoringData
  -> Communication::SendMonitoring -> EnqueueMessage
  -> pthread_mutex_lock

Disconnect or Stop
  -> CloseConnection -> NotifyConnectionLost
  -> Alerts::OnDisconnect -> pthread_mutex_lock

Alerts::SendAlerts
  -> Communication::SendAlerts -> EnqueueMessage
  -> pthread_mutex_lock
```

The Monitoring pair matches the prior live VM stack. Alerts and Stop were
previously source risks; they are now reproduced **in this isolated test**, not
claimed to have occurred in the live Test. No test thread remained blocked on
the UUID/event gate in the captured native wait pairs.

### Interpretation and next boundary

This proves an executable source-level lock inversion without staging Cloud,
RabbitMQ, demo service packages or the idle-full-status worker participating.
It does not measure natural occurrence probability or exclude indirect timing
effects of our patches. The callback and sender paths themselves are unchanged
from the recorded upstream blobs; the complete test binary is not described as
an unmodified official release.

Control recovery verifies a new local WebSocket, native connection notification
and a second queued message. It does not run the full discovery/reconnect
worker, send the queue to Cloud, or prove ACK/NACK/backlog integrity. Current
main/develop were source-reviewed earlier, not rebuilt by this execution.

The next correction should address subscriber callbacks under the transport
mutex at every relevant close path, preserving state synchronization, callback
ordering and listener lifetime. A Monitoring-only workaround leaves the
independently reproduced Alerts route. Removing all mutex protection or adding
a watchdog restart is not supported by these tests. Before deployment, add the
remaining ordering/lifetime/close-exception coverage and qualify the complete
reconnect worker and live OFF/ON path. No corrective native patch, deployment,
Factory rebuild, commit, push or upstream submission was performed here.
