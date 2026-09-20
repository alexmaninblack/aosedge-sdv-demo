<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness and independent demo scenario reset

18 September preserved-Test follow-up: diagnostic Brake 59.0.0 distinguishes
upstream missing-data aborts from completed-but-unqualified Autopilot episodes.
Presenter contact/reset/result wording is corrected and tested. The operator-
authorized VDP 79.0.0 update is installed through staging after explicit Safe
Stop; Autopilot is restored. Identical periodic snapshots are ignored without
freshness renewal, and the bounded live window shows no previous non-monotonic
reconnect. Brief missing-input episodes remain under investigation; no new
complete Brake end-to-end pass is claimed. See
[driving-gap diagnosis](../../../qualification/brake-driving-gap-2026-09-18.md).

17 September successor checkpoint: Factory .35 completed the authorized
clean staging Test cycle by 05:32 UTC. Platform build source is pinned to
`bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74`. Build and qualification results
are tracked in [Factory .35 execution evidence](../../../qualification/factory-35-e2e-2026-09-17.md).
VDP V1/V2/V3, Brake V1/V2/V3, Tire V1, real KUKSA/backend results, both native
warnings, independent Reset/CLEAR/renewed warnings, Offline/reconnect,
first-attempt packaged Park/Resume and final UI retirement all passed.
Lifecycle/publication/observation used Presenter/native UI; authorized real
maneuvers used Demo Control. No Production work was included. Factory .34
was retained at qualification time. The separate 17 September cleanup request
supersedes that retention: the obsolete .34 image was deleted after dependency
checks; compact evidence remains. See the pre-UI checkpoint audit.

The earlier status below is historical and superseded by the .35 result.

Status: preserved-Test CLI and targeted UI functional proofs passed,
16 September 2026. Factory .34 built; automatic strict Test Provision and
retirement support implemented and regression-tested. After the operator
unlocked the Mac and entered VM access, clean .34 UI creation, stationary
Manual connection, strict Provision, VDP71/V1 -> 72/V2 -> 73/V3 and
Brake50/V1 -> 51/V2 -> 52/V3 delivery passed. Tire31/V1 produced a real
assessment; both independent Reset commands received correlated CLEAR.
Offline/reconnect passed. Park passed; Resume required a diagnosed recovery
and is not yet qualified as a clean first-attempt restart. Full V2 assessment,
warning -> Reset -> renewed warning, final UI/restart and retirement gates
remain open. After unlock on 17 September, native post-recovery inspection
passed. The corrected guest bootstrap passed a new UI Park/Resume attempt,
but Resume stopped later on an unexpected native component removal transaction.
The preserved .34 Test was blocked at source restoration at that checkpoint;
no final full-cycle pass is claimed. At 03:44 UTC on 17 September, the approved
CM startup fix passed native red/green tests and was applied transiently to the
preserved Test. UI Continue Resume then completed in nine seconds, with Test
selected, LIVE stationary Manual and both advisories Monitoring. The native
patch is in the CM recipe; .34 is unchanged and the `/run` override does not
survive reboot. First-attempt restart on a successor remains open.
On 17 September the operator authorized a bounded
CM/SM startup-reconciliation fix on this preserved Test: diagnose the native
stop request, prove the smallest reversible correction, and repeat the UI
restart gate. Cloud, Production, Safe Stop policy and retained identity remain
unchanged. No transaction may be manually removed or bypassed.
See [execution evidence](../../../qualification/advisory-readiness-reset-2026-09-16.md).

## Boundary and order

Current staging Test only; Production is excluded. Preserve current identity,
overlays, historical records and approved model thresholds. Implement on the
existing Test, prove through Demo Control and Presenter, consolidate the known
guest fixes in one Factory successor, then run the complete clean UI story.
Do not describe a source test or an upload as end-to-end acceptance.

Approved clean-run prerequisite: integrate strict Gateway enrollment into Test
Provision, through the shared Demo Control path. Close the guest source gate
before the first post-Provision attachment; reopen only after stationary Manual
and authenticated connection are confirmed. Preserve VM/Cloud identity and
Production. Do not require a deployed VDP at the empty Factory baseline or
mistake a baseline TLS read for live VDP telemetry. Operator Safe Stop remains
explicit. Qualify this order on .34 through UI before declaring the work done.

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

The accepted 20 September UI amendment moves **Reset scenario** to each
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

CM/SM/IAM are not modified for the readiness/reset feature itself. The separate
17 September authorized startup-reconciliation correction is limited to the
observed Resume defect. Their already approved permission capacity fixes remain
part of the separately tracked Factory consolidation.

## 17 September: control continuity and offline reconnection amendment

Additional operator-approved first-drive corrections: fix the immediate Manual
first-command timeout without relaxing the 250 ms expiry; verify control socket
responsiveness independently of CARLA ticks; prepare the native Unreal DDC for
Town10HD explicitly through `simulation prepare-cache`, with the simulator
stopped and Test VM/Cloud/service identity preserved. No image rebuild or
graphics-quality reduction belongs to this correction.

Operator-approved corrections on the preserved staging Test:

- Start the local simulator, strict Gateway and native telemetry independently,
  without a Unit attachment. After Provision confirms Cloud Online, enroll the
  exact Unit/Main Node under the existing CA and attach via the existing private
  assignment protocol. Do not restart any source process or reset the actor.
  Preserve fresh stationary-frame/native-session checks and confirm Manual
  before opening the guest gate. First VDP installation follows the operator's
  later Safe Stop. No Gateway hot-reload or anonymous fallback is introduced.
  This supersedes Q03's former pre-Provision connection and the earlier draft
  Gateway-only replacement. Older running development-profile Gateways require
  an explicit development restart, not a hidden restart inside Provision.
- Pedal release smoothing must never overlap nonzero throttle and brake.
  A rejected pedal command requests Safe Stop without closing the UI channel;
  a genuinely lost channel is recovered only by explicit operator input and
  reacquires stopped, without replaying driving commands.
- Both service bootstraps choose gRPC's native resolver before process start.
  Aos's existing container-local `Server` hosts entry resolves KUKSA even with
  external networking disabled, including reconnect after JWT renewal.
  TLS hostname checks, permissions, model thresholds and the offline firewall
  remain unchanged. No CM/SM/IAM or Factory modification is required.

Proof order: focused source/protocol/native build tests; normal democtl package
build/sign/upload for the same functional profiles; actual offline reconnection
and control recovery; then the Provision continuity path. A source-only result
must not be reported as a live first-Provision qualification.
