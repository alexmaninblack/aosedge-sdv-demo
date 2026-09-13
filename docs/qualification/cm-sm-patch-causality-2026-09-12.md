<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CM/SM service-update patches versus delayed Cloud Offline

Publication note: private evidence links, infrastructure identifiers and source
locations have been removed. The detailed working report is retained outside
Git under the confidential-input policy; timings and our own conclusions remain.

Date: 12 September 2026. Scope: read-only source and historical-log analysis.
No VM/Cloud restart, binary change, build or deployment was performed.

## Question and result

Why did Cloud connectivity failures become visible during qualification of our
service-update patches? Do the patches change timing or Cloud message traffic?

**Yes, the patches change reachable service workflows, reported states and
timing. Unchanged WebSocket source does not prove absence of indirect effects.**
However, new historical evidence shows the exact same Cloud RabbitMQ consumer
timing out before the recent SM teardown and CM reconciliation patches were
applied. Their introduction is therefore not required to explain the existence
of that consumer failure. The earlier statement that an unpatched comparison
cleared the patch set would be incorrect: that comparison removed only one CM
patch, retained patched SM, did not perform a service update, and lasted too
briefly to exclude delayed failure.

This analysis does not clear all historical demo changes or prove the original
cause of the Cloud consumer's broken state.

## Timeline that separates code change from the replacement operation

All times UTC, 11 September 2026 unless explicitly dated otherwise.

| Time | Evidence |
| --- | --- |
| 10:26:48.672771 | RabbitMQ ACK timeout for consumer `CONSUMER_A`, queue `connection-event queue`, channel 999, delivery tag 1, timeout 1800000 ms. |
| 14:22:50.668747 | Same consumer/queue, channel 1249, delivery tag 1, same timeout. |
| Approximately 16:11 | New service-teardown/failed-replacement SM applied to the retained .31 Test. CM was not restarted in this operation. |
| 16:49:17.262728 | Same Cloud consumer timeout, channel 1251, delivery tag 1. |
| 21:08:42.085540 | Embedded disconnect timestamp associated with stopping the previous CM during installation of the reconciliation binary. |
| 21:08:42.358910 | New CM process began; service-update workflows then completed. |
| 21:17:11.612674 | Same Cloud consumer timeout, channel 1253, delivery tag 1. |
| 21:17:11.613180 | Broker channel closure on connection `<0.4199631.0>`, client `PRIVATE_ENDPOINT`. |
| 21:17:11.614 body / .615 Grafana entry | UMH received the disconnect timestamped 21:08:42.085540 for System UID `d53d05cd4c4649c9a896534b23b88273`. |
| 21:17:11 | Retained .31 Test Unit API's recorded Offline transition. |

The delayed disconnect in the first post-CM-patch episode belongs to the old
connection closed during binary replacement, not a new connection failure
created eight minutes later by the new service update logic.

The pre-patch broker queries establish failure of the same Cloud consumer, not
an Offline transition for this exact Test at 10:26 or 14:22. Bounded exact-UID
UMH queries around those two times returned no records; do not claim otherwise.

Evidence:

- Broker consumer before CM patch application (private evidence reference omitted).
- First post-patch UMH Offline window (private evidence reference omitted).
- Matching broker closure (private evidence reference omitted).
- [Recorded SM and CM application receipts](aoscore-service-update-teardown-2026-09-11.md).

## What actually changed

Patch paths below are under the Platform repository's
`meta-aos-vehicle-platform/recipes-aos/` directory.

| Change | Previous behavior | Changed behavior / possible Cloud consequence |
| --- | --- | --- |
| CM `0001-serialize-sm-stream-writes.patch` | Independent writers could write concurrently to one gRPC stream, causing the reproduced gRPC assertion. | Shared write serialization changes contention. A Cloud-connect notification to SM can wait behind another writer. This is an upstream backport already qualified on 5 September, not a new 11 September service-update patch. |
| CM `0002-reconcile-stale-instance-snapshot.patch` | An old Active/Failed instance version could produce NotFound and abort the full-node-status callback before resend and status notification. | Preserve old observed version without attributing it to the desired one; continue STOP-old/START-desired reconciliation and normal status notifications. This changes actual service states/versions and the timing/count of Cloud UnitStatus updates. |
| SM `0002-idempotent-service-container-teardown.patch` | Already-absent process/state/veth or an empty unmounted namespace placeholder could block cleanup. | Classify these narrowly as absent and permit teardown to complete; previously blocked replacement can now proceed. Real permission/I/O errors remain failures. |
| SM `0003-preserve-failed-service-replacement.patch` | Service could be marked inactive before asynchronous teardown finished; retained old identity/failure could be reset inappropriately. | Mark inactive only after successful service teardown/network release, retain failed ownership and image references, and prevent starting an old identity as a new version. Observable states and their ordering intentionally change. |
| SM `0004-retry-failed-service-preparation.patch` | A failed same-version service could skip preparation on the next native request and fail for missing network/config again. | Retry preparation for that failed same-identity service; this can repeat native preparation/network work and subsequent status transitions. It does not add a periodic Cloud reconnect. |
| Factory .32 public-input startup hooks | Required runtime mount inputs were transient and could disappear on reboot. | Pre-start projection and post-start verification change SM startup timing. Verification has a nominal 15-second retry window for provider readiness, with individual subprocess timeouts. It does not establish a 15-second total boot guarantee or directly reconnect CM. |

The VDP systemd-slot runtime integration is a separate preexisting component
implementation. It must not be confused with the recent container service
teardown/reconciliation patches.

## Exact indirect paths

### CM reconciliation changes the workload seen by Cloud

In the pinned shared-library source:

1. `Launcher::OnNodeInstancesStatusesReceived()` receives the SM snapshot.
2. `InstanceManager::UpdateRunningInstances()` now tolerates observed old or
   unassigned non-preinstalled versions while retaining them for reconciliation.
3. The caller reaches `UpdateInstanceStatuses()`, queues the updated node and
   notifies the worker instead of returning NotFound.
4. `Node::ResendInstances()` computes STOP-old/START-desired.
5. Instance-status listeners feed `UnitStatusHandler::OnInstancesStatusesChanged()`
   and its existing coalesced delta publication path.

Therefore, successful service updates are not wire-equivalent to the previous
stuck-service run. They can also exercise native persistent-state and monitoring
paths that failed/non-running services exercised differently. A specific causal
link from those messages to the RabbitMQ connection consumer has not been shown.
The generic message queues and connection-event queue have separate consumer
tasks; shared infrastructure effects still cannot be excluded merely from that.

### Preexisting synchronous CM-SM/Cloud coupling

`Communication::ConnectToCloud()` calls `NotifyConnectionEstablished()` before
returning to `HandleConnection()` and entering `ReceiveFrames()`. Subscriber
callbacks run synchronously. One callback invokes `SMController::OnConnect()`,
then `SMHandler::SendCloudConnectionStatus()` and a gRPC stream write.

Contention or a blocked write can therefore delay the first WebSocket reads
and initial status handling even without changing WebSocket source. However:

- Synchronous gRPC writes already existed before the backport.
- The backport shares a write mutex; it releases that mutex before waiting for
  a synchronous response. It does not hold every write for the five-second
  response timeout.
- Factory .31 source `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` already includes
  this patch in its CM recipe. Earlier working .31 was not free of that patch.
- The current incident has ongoing Pongs and accepted monitoring, and old close
  timestamps were recorded promptly by Cloud. This timing path alone does not
  explain their much later Cloud status application.

No direct service-update -> Cloud WebSocket close call was found in the reviewed
CM/SM paths. SM stream disconnection updates node information; it does not itself
invoke the Cloud transport's Disconnect method.

Source references: Platform `build/aos_core_cpp/src/cm/communication/communication.cpp`
(`ConnectToCloud`, `NotifyConnectionEstablished`, `CloseConnection`, `HandleConnection`),
`src/cm/smcontroller/smcontroller.cpp`, deployed CM patch 0001; shared library
`src/core/cm/launcher/{launcher,instancemanager,node}.cpp`,
`src/core/cm/updatemanager/unitstatushandler.cpp`, SM patches 0002-0004.
The local cpp checkout does not itself have the recipe's write-lock patch
applied; the patch file is authoritative for the deployed mutex delta.

## What the previous A/B experiment does and does not establish

The [recorded experiment](cm-online-controlled-comparison-2026-09-12.md) removed
only CM patch 0002. CM patch 0001 and the same patched SM remained. B was observed
for 5 minutes 17 seconds; restored A failed approximately 19 minutes later.
An unchanged-A restart also initially recovered Online.

No new service version transition was performed during that comparison. With
Brake 8/Tire 7 already matching desired state, the substantive stale-version
branch might not have been exercised at all. Equal bounded message counts are
not proof of equal payloads or sustained connectivity.

It is consequently incorrect to label that result “unpatched SM/CM works,
patched SM/CM fails.” It is a limited warm-reconnect comparison of one CM delta.

## Interpretation and next boundary

The best supported explanation of the visible association is currently:

- Cloud already had a failing connection-event consumer.
- Installing the CM patch required a normal CM restart, producing an old-session
  disconnect and a new connection.
- The old disconnect was processed only after a broker timeout and overwrote
  the new connection's status through the source-confirmed missing stale guard.
- Service patches also changed actual workload and timing; their independent
  influence on exposure frequency has not been isolated.

Do not remove a known-needed shared-write fix or introduce periodic reconnects
as a causal conclusion. The remaining VM-side discriminator, if needed, is
bounded non-secret timing of connect callbacks, SM writes and service-status
transitions. Any future A/B must exercise the changed old-to-new service path,
retain a matched Cloud/assignment context and account for outstanding stale
events; a short idle warm restart is not that test. No such mutation was made
in this analysis.
