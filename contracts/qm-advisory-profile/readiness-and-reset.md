<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness and independent Reset

- Status: Accepted readiness and Reset contract
- Version: 1.0
- Owner: SDV Lab integration and Brake/Tire producers

This contract defines readiness and demo Reset used by the current
Brake and Tire contracts. The typed advisory profiles and their golden bytes
remain authoritative. Runtime qualification and remaining matrices are owned
by the [current baseline](../../docs/qualification/current-baseline.md).

Services publish actual boolean readiness transitions at the next worker
iteration and retain the five-second heartbeat. VDP forwards changes without
waiting for its heartbeat. Successful writes/attempts are bounded to at most
one per 100 ms; unaccepted writes retry with current state after one second.
KUKSA RPC/entry errors and VISS responses/timeouts are checked. Credential,
schema, freshness, model, reset and AosCore authority retain their existing
contract boundaries.

## Vehicle display

The native vehicle dashboard reads only Gateway/VISS. It never reads Cloud,
guest files, service-package inventories or functional backends.

- No live VDP advisory support: `Not available`.
- Live support, no confirmed compatible producer: `Waiting for service`.
- Fresh producer readiness, no active warning: `Monitoring`.
- A currently valid Gateway-confirmed warning: its existing recommendation.
- Lost producer readiness after it was established: `Unavailable`, not healthy.

Brake functional V3 and Tire functional V1 are the compatible producers.
Allocated publication versions remain provenance, not authorization.

Each producer writes a fixed own-team KUKSA actuator
`Vehicle.OEM.{BrakeHealth|TireHealth}.Advisory.Readiness`, containing exactly
`schemaVersion:1`, boolean `ready`, and UTC `observedAt`. It is refreshed every
five seconds from actual telemetry readiness, independent of external backend
connectivity. VDP reads only those two authorized targets. Values older than
15 seconds, malformed or future-dated values never establish readiness.

VDP V3 sends a bounded five-second heartbeat to the two corresponding VISS
`Advisory.Availability` paths, containing exactly `schemaVersion:1`, boolean
`ready`, and current UTC `observedAt`. Sending it means the running VDP has
advisory support. Only the selected Unit mTLS role may write these paths.
Gateway accepts at most five seconds of forward VM clock skew for this display
heartbeat only. It still rejects
older-than-15-second or non-increasing observations. No warning request or
Safe Stop authorization window changes. Gateway publishes a read-only projection with its own observed time and a
15-second expiry. Its six fields are `schemaVersion`, `supported`, `ready`,
`everReady`, `gatewayObservedAt` and `expiresAt`. `everReady` describes only the
current selection lifetime. V1/V2 do not announce support. Handover clears the state;
old support expires after a VDP stop/downgrade. Readiness never creates,
clears, renews or proves application of a recommendation.

## Reset semantics

**Reset Driver Advisory** is on each
Brake/Tire backend summary card with one-click protected submission and no
additional confirmation. Details retain outcome/history, not a second action.
Immediate submission, backend PENDING and correlated CLEAR remain distinct;
the previous reset cannot establish completion of a new request. It resets
only that service's demo estimator and current capture, not the VM, installed
versions, Subject, credentials, peer service, historical records or outbox.
Brake returns to its existing preconditioned initial model; Tire returns to
NOT_EVALUATED. Thresholds and real telemetry are unchanged. A reset event is
not a fabricated GOOD assessment or a repair claim.

Stop refreshing the old condition; issue a fresh existing typed CLEAR request
with the reset command ID as decisionId, preserving producer epoch and strictly
increasing sequence. This explicitly extends the accepted clear cause to an
operator-requested demo model reset. Only a matching Gateway CLEARED result
closes the command successfully. Network/transport acceptance is not success.
Retained old facts remain historical and cannot become the new current result.

## Fixed backend command protocol

No arbitrary command, URL, path, shell or inbound guest listener is added.
The existing private demo service-to-backend route is reused. This is local
demo control, not a production remote-management/authentication claim.
Command creation is restricted to the existing private backend admin socket,
called by Demo Control; no public browser mutation endpoint is added.

- `democtl backend reset-scenario brake|tire --target test` creates one command.
- `democtl backend reset-status brake|tire --target test` observes it.
- Admin POST `/api/v1/<team>/admin/demo-reset` creates a UUID command with
  current Test UID, native service/Subject/instance, producer epoch and a
  60-second execution deadline. The binding must match a producer poll within
  15 seconds. At most one pending command per current Test/team.
- Service POST `/api/v1/<team>/demo-control/poll`: closed body
  `{schemaVersion:1,unitSystemUid,serviceVersion,serviceInstance,producerEpoch}`.
  Native `serviceInstance` has exactly `serviceId`, `subjectId`, `instanceIndex`
  and `instanceId`; release changes never inherit pending reset authority.
  Polling uses the existing delivery worker, every five seconds, independently
  of whether product records are waiting. Response is `{schemaVersion:1,
  command:null}` or a fixed RESET_DEMO_SCENARIO envelope with commandId,
  the same immutable binding and issuedAt/expiresAt.
- Service POST `/api/v1/<team>/demo-control/ack`: same binding plus commandId,
  result and correlated clear request/status. Accepted outcomes distinguish
  CLEARED, REJECTED and FAILED; expiry is not successful reset.
- Read-only current command status is included in backend observation.

Persist command/ack in the backend's existing SQLite store and reset intent in
the service's existing private state. Duplicate delivery is idempotent;
recovery completes the same intent without resetting twice or reusing a
sequence. Old/foreign/expired commands cannot start a reset. Limit retained
command history to 32 per Unit/team; include it in owned final cleanup.
The UI shows **Resetting driver advisory…**, **Driver advisory reset** after
correlated CLEAR, or explicit failure. This accepted wording does not rename
`reset-scenario` or change its reset scope. Offline
commands expire rather than executing unexpectedly in a later demonstration.

## Implementation boundaries

The native dashboard reads Gateway/VISS only. Backend command administration
is private and remains under Demo Control; it is not a public management API.
The service bootstraps use the native gRPC resolver and the existing container
`Server` hosts entry for KUKSA, including offline JWT-renewal reconnection.
Readiness and Reset use existing CM/SM/IAM authority; no parallel lifecycle is introduced.

Pedal release smoothing must not overlap nonzero throttle and brake. A rejected
pedal command requests Safe Stop without closing the UI channel. A genuinely
lost channel requires explicit operator input, reacquires stationary and never
replays driving commands. The command-expiry boundary remains 250 ms.

The simulator/Gateway may start without a Unit attachment. After Provision
confirms the exact Cloud Unit, enrollment and attachment use the existing CA
and private assignment protocol without restarting the source or actor.
Stationary-frame and authenticated-session checks remain required before the
guest gate opens. First VDP installation still requires explicit Safe Stop.

Current source attachment/provisioning and vehicle-control behavior follow
[Demo Control](../../docs/architecture/demo-control.md) and the
[current operator sequence](../../docs/operations/current-demo-workflow.md).
They do not inherit old one-session staging permissions or the retired
Park/Resume implementation order.
