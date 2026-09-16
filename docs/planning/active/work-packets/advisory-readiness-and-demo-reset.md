<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness and independent demo scenario reset

Status: preserved-Test CLI and targeted UI functional proofs passed,
16 September 2026. Clean Factory/UI lifecycle qualification remains open.
See [execution evidence](../../../qualification/advisory-readiness-reset-2026-09-16.md).

## Boundary and order

Current staging Test only; Production is excluded. Preserve current identity,
overlays, historical records and approved model thresholds. Implement on the
existing Test, prove through Demo Control and Presenter, consolidate the known
guest fixes in one Factory successor, then run the complete clean UI story.
Do not describe a source test or an upload as end-to-end acceptance.

Pre-change checkpoints: solution `0a0e604`, Gateway `1ad3212`, platform
`1d8429b`, Brake service `b88ba79`, Tire service `6fe0f18`, Brake backend
`8060ea3`, Tire backend `76a5cd2`. No build artifacts or credentials enter Git.

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
heartbeat only (the preserved Test measured a 9–10 ms lead). It still rejects
older-than-15-second or non-increasing observations. No warning request or
Safe Stop authorization window changes. Gateway publishes a read-only projection with its own observed time and a
15-second expiry. Its six fields are `schemaVersion`, `supported`, `ready`,
`everReady`, `gatewayObservedAt` and `expiresAt`. `everReady` describes only the
current selection lifetime. V1/V2 do not announce support. Handover clears the state;
old support expires after a VDP stop/downgrade. Readiness never creates,
clears, renews or proves application of a recommendation.

## Reset semantics

The separate Brake/Tire backend view offers `Reset demo scenario`. It resets
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
The UI shows Resetting, confirmed completion or explicit failure. Offline
commands expire rather than executing unexpectedly in a later demonstration.

## Implementation and verification gates

1. Freeze these contracts and preserve pre-change source checkpoints.
2. Backend command storage/routes; service durable reset/clear, outbound poll
   and readiness; VDP/Gateway readiness; Demo Control and UI composition.
3. Focused tests: fresh/unsupported/stale readiness; actual warning wins;
   peer isolation; repeat, restart recovery, expired/foreign command rejection;
   retained sequence/history; no success before matching CLEARED.
4. New packages through Demo Control; real maneuvers -> warning -> Reset ->
   new real maneuvers -> renewed warning, each team independently. Then UI.
5. Close previously documented transient guest/schema/security fixes, build
   once with warm caches, and complete clean UI qualification and cleanup.

CM/SM/IAM are not modified for this feature. Their already approved permission
capacity fixes remain part of the separately tracked Factory consolidation.
