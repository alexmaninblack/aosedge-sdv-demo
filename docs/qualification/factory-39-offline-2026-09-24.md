<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .39 — existing-installation offline qualification

Status: focused external-OFF local processing and ON delivery **PASS**, with
readiness/presentation observations and proof boundaries below. No baseline
promotion or product change.

## Scope and identity

The operator requested offline testing on what was already installed. This
retains the [ignition-qualified Test .39](factory-39-ignition-2026-09-24.md):
VM `48a0e19c-857f-44b8-9b68-38b585a8278f`, staging Unit
`5395f7d6-2ff3-4d10-9e7f-efa85e7994eb`, VDP117/V3, Brake92/V3 and Tire49/V1.
Solution source is `e24422e`; Factory .39 platform source is
`793b1fc035d2b7c123f9a4161788955f389bb81d`.

No signing, upload, assignment, reset, provisioning, VM/service restart, scene
recreation, new credential or transient guest policy/configuration is used.
Production metadata is unchanged. Existing recommendations/history are retained.
The normal `democtl vehicle connectivity` gate changes only this Test's external
traffic; local CARLA/VISS/control remains available.

## Observed sequence — UTC, 24 September 2026

| Stage | Observation |
| --- | --- |
| Preflight18:38:03 | Cloud ONLINE,117/92/49 installed, no pending/error; empty outboxes; fresh/unheld Safe Stop,0km/h, brake1.0 |
| OFF18:38:07.479→18:38:09.803 | One normal OFF command; authoritative status confirms OFF |
| Brake maneuver18:38:23.363→18:38:38.521 | Real CARLA physics,15.10s, physical stop confirmed |
| Tire maneuver18:38:38.521→18:38:53.447 | Real CARLA physics,14.88s, physical stop confirmed |
| Offline final18:43:15.308 | Cloud OFFLINE; local models advanced, queues accumulated; control still fresh/unheld Safe Stop |
| ON18:43:15.308→18:43:17.602 | One normal ON command, completed; OFF-observed to ON-request interval305.50s |
| Cloud ONLINE observed18:43:23.433 | Same Unit, unchanged releases/no pending/error;8.13s upper bound from ON request |
| Captured backlog delivered | Brake latest receipt18:43:24.848; Tire assessment/advisory18:43:29.731; legacy status18:43:29.826 |
| Empty queues confirmed18:43:44.610 | Both empty,29.30s upper bound from ON request; inspection cadence is not an exact drain timestamp |
| UI observed18:44:24 | Both RECEIVING/WAITING, recommendations retained, Reset controls enabled, Cloud Online/fresh resources |

Four offline snapshots keep the same backend message heads/counts/receipt
timestamps. There are no receipts with timestamps inside the OFF window.
Compare with the first settled-OFF read, not the earlier non-atomic preflight:
ordinary messages arrived between that preflight and OFF, all timestamped before
OFF. This distinction corrects an evidence-comparison artifact, not a product
network leak.

## Local work and durable delivery

| Evidence | Brake | Tire |
| --- | --- | --- |
| Local model processed-event count |4→6|2→3|
| Backend assessments during OFF |4, unchanged|2, unchanged|
| Backend assessments after ON |6, all IDs unique|3, all IDs unique|
| Captured offline assessment messages |2|1|
| Captured offline Gateway APPLIED facts |15|15|
| Exact queued identity matches after ON |17/17, each once|16/16, each once|
| Other queued messages |none|10 legacy FUNCTION_STATUS|
| Final outboxes |empty|empty|

The second Brake assessment is generated during the Tire maneuver's braking,
not a duplicate: separate source episodes/assessment IDs. All original assessment,
event and advisory identities remain. Backend lists have no pagination tail and
no duplicate identity. Every identity-tracked queued message has a backend receipt
after ON. Tire's10 legacy status messages also appear with offline source times,
post-ON receipt times and10 unique backend status IDs; the pre-ON projection
counted them but did **not** retain their `statusId`, so that category has
count/time evidence, not a per-queued-ID bijection.

Both models keep INSPECTION_RECOMMENDED. Storage UID/GID/inodes are unchanged.
Boot ID remains `2d803274-c9fb-44b5-b107-8b041d6fea1e`. IAM1051, SM1139,
CM1318, KAC1079, VDP1165 and container bootstraps Tire1207/Brake1208 remain
unchanged; automatic manager restarts0. Service children are Tire1209/Brake1210.
Full-interval bounded journal projection records no SEGV and only the known
SSH `sshd_t → aos_var_run_t:dir search` AVC category99 times; no VDP/KAC/service
denial is observed. Enforcing and disabled core capture remain intact.

Read-only local source checks during OFF18:39:57 and after ON18:44:19 show
OPEN gate, VDP READY/LIVE, selected admission/generation unchanged, strict mTLS
configured and physical Safe Stop. No qualification-client identity is added.

## Observations — do not call this uninterrupted readiness

1. Brake reports KUKSA_REAUTHENTICATING twice during OFF:18:39:33.654 and
   18:42:33.759. Its NOT_READY phase lasts~0.20/~0.40s; recovery to the ordinary
   backlog-DEGRADED state takes~3.91/~4.50s. Authorization recovers locally while
   external connectivity is still OFF, without a restart.
2. Advisory readiness publications briefly toggle NOT_READY→READY for both
   services (~0.10–0.20s). The VDP availability projection observes four Brake
   toggles during OFF (~0.20–0.21s) and one after ON (~0.24s). Similar transitions
   were already present before OFF. These are a retained readiness-flap follow-up,
   not proof that external OFF caused a new regression. Native Driver Control
   was not continuously filmed; this test does not claim zero visible flicker.
3. Presenter eventually marks backend inputs Last known/activity Not confirmed,
   Cloud Offline, old resource samples Last known and disables Reset. Backend
   checked continues advancing because it timestamps host-to-backend reads,
   not receipt of vehicle telemetry. Both cards recover without a refresh action.
4. Delivery and the current function-observation channel recover at different
   times: Brake results/backlog are delivered by18:43:24.848, but its observation
   is still stale at the18:43:39 read. Both observations are fresh at18:44:20,
   and the UI at18:44:24. Preserve this separate feedback-latency observation;
   do not equate Cloud Online with immediate freshness of every card.
5. The existing reused-release117 `Installed profile not confirmed` Presenter
   observation remains open and unchanged by this test.

## Evidence and exclusions

Private compact proof set: `/private/tmp/test39-offline-20260924.h5LhXu`, including
intent, OFF/ON receipts, baseline/intermediate/final snapshots, bounded interval
audit and corrected `analysis-v2.json`. The first analysis remains for provenance:
it compared preflight instead of settled-OFF and omitted the separate legacy
status endpoint. All corrected functional assertions pass. No secret, key/token
content or raw sensor payload is retained. These are compact proof files, not
build artifacts; no disk cleanup is needed for this run.

This is one~five-minute continuously running offline interval on the existing
installation, including two reauthentication cycles. It does not qualify cold
boot while externalOFF, nonempty-queue power loss,30-minute soak or the full
serial V1→V2→V3 update matrix. No product source/build/image changed. Test is
left online in Safe Stop, without Autopilot.

Documentation navigation gate passes262 Markdown documents; `git diff --check`
and the tracked confidential-input guard pass. No compile/unit suite is rerun
for this observation-only qualification; the installed bytes are unchanged.
