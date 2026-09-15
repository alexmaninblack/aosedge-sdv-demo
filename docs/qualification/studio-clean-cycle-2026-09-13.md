<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Studio clean operator cycle — 13 September 2026

Status: **Working final Test state reached with assistance; not a passed
unassisted clean UI cycle.**

## Scope

The user authorized Finish of the retained Test and a complete fresh cycle
through the implemented UI. Use immutable Factory .33, preserve Production,
published releases and release-number continuity. No image rebuild, Cloud
permission change or direct guest/Cloud mutation is part of this test.
Service inputs remain synthetic; real KUKSA/advisory are excluded.

## Execution record (UTC)

| Time | Observed outcome |
| --- | --- |
| 12:32 | Presenter Finish demo confirmed for the existing Test only. Demo Control stopped simulation and prepared scoped backend cleanup. |
| 12:32:49.768 | Bounded `democtl component logs test` confirms `Stopped AOS Communication Manager`; transport disconnect events precede this line. |
| 12:32:49.469 | Independently observed in Cloud WebSocket logs: the exact Test connection closed normally, code 1000. No later connection for this Test appears in the queried interval through 12:54 UTC. |
| 12:34:23 | Retirement returned PARTIAL at deprovision-test, `UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE`. The Cloud deprovision request and local disk deletion had not started. |
| 12:35:27 | `democtl unit cloud-status test` still reports the same Unit provisioned/Online. Factory .33, working overlay, Subjects and exact Unit identity remain preserved for continuation. |
| 13:02:49.508691 | RabbitMQ logs a consumer acknowledgement timeout on the connection-event queue: `1800000 ms` (30 minutes). Infrastructure identifiers are omitted here. |
| 13:02:49.510 | The Cloud Unit message handler receives the Test disconnect with `is_connected=false` and embedded event timestamp `1789302769.471034` = 12:32:49.471034 UTC. The event-to-handler delay is 1800.039 s. |
| By 13:04 | Presenter observes authoritative Offline and the already-authorized Finish continuation is submitted. |
| By 13:10 | The durable journal records `testRetirement.state=COMPLETED`, contains only the non-target Production vehicle, and Presenter offers Create controller for a fresh Test. |

The same delayed Offline gate was independently observed during the earlier
.31/.32 retirement in the [Factory .33 execution receipt](factory-33-e2e-2026-09-13.md).
That history is not proof of the exact current Cloud consumer cause or a
guarantee that this event will recover within the same interval. Do not bypass
the Offline guard or restart CM to manufacture a different session.

Both the current Unit Manager and historical handler log selectors returned no
matching Test entries after the disconnect in the bounded window. The API still
showed Online after the full VM was stopped. This establishes divergence between
the closed transport and stored Unit status, not ongoing keepalive from this VM.
The subsequently observed connection-queue acknowledgement timeout and the
handler's delayed receipt establish this incident's 30-minute event-processing
delay. The handler receives the original disconnect timestamp, not a new
keepalive. These logs do not establish why the original consumer failed to
acknowledge the delivery; that internal cause remains unresolved.

The live partial state exposed a UI guidance defect: after Finish stopped the
simulator, the guide offered Start simulator. The corrected guide keeps this
run in Retirement paused, permits read-only refresh and only offers Continue
Finish when Cloud reports Offline. New preparation/publication/start actions
are blocked for the retiring run. Two new ONLINE/OFFLINE regression cases and
the four existing Studio cases passed; TypeScript and the production UI build
passed. This correction does not change the retirement protocol or Cloud.

## Planned remaining proof

### Whole-VM shutdown amendment

The user subsequently requested whole-VM shutdown instead of stopping CM
separately. `democtl vm stop test` completed graceful Test shutdown in 4.98 s;
Production remained untouched. At 12:49:36 UTC Cloud still reported this
stopped Test as provisioned/Online. No deprovision/delete request was sent.

The shared UnitService now uses the existing owned, graceful, idempotent VM
stop primitive before the Offline gate. A stopped-VM continuation needs no
guest/SSH readiness and never restarts CM. The separate CM-stop helper was
removed. All 33 Unit regression tests passed, including stop-before-Cloud,
already-stopped continuation, failed-stop refusal and Offline-timeout retention.
The idle Presenter server was reloaded to adopt this source; no VM was restarted.

### Remaining sequence

1. Resume the recorded Finish only after authoritative Offline; verify scoped
   deprovision/delete and local cleanup, preserving the non-target. **Completed:**
   Test retirement journal and fresh-create UI confirmed; no claim of a passed
   fresh E2E cycle follows from this cleanup alone.
2. Create fresh Test from the same .33; connect stationary Manual.
3. Publish a newly numbered VDP v1 before Provision, then observe first
   installation through native Safe Stop.
4. Exercise VDP v1 → v2 → v3, Brake v1 → v2 → v3 and Tire v1 through the UI;
   service replacement does not depend on Safe Stop. Check real synthetic
   backend receipts separately from Cloud installed/runtime facts.
5. Check retained-identity Park/Resume and final visible state. Human visual
   acceptance remains separate from agent-driven execution.

Only actually observed results will be promoted to passed below. The prior
retained-Test smoke and fixture tests do not substitute for this cycle.

## Fresh UI execution resumed at 14:59 UTC

The user explicitly requested the complete working VDP/service cycle again.
No unidentified upstream release is adopted. Current immutable .33 and its
packaged CM/SM are retained; Production is excluded.

- UI selected `6.1.1-maninblack.33/main-qemuarm64` explicitly; Create completed
  at 15:01:23 UTC. New local Test VM ID:
  `4e5a174d-4cdf-4980-967c-1b8ac77fc376`.
- The recorded factory SHA remains
  `a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761`.
  First guest enrollment waited for console boot, then completed SSH/DNS and
  staged the Test factory role before SM. Both owned backends started.
- UI Start simulator and Connect in Manual completed. At 15:04:40 UTC the
  header selected Test; native telemetry showed LIVE, Manual, 0.0 km/h and
  STOPPED. No Safe Stop update gate had been requested yet.
- UI prepared and published VDP V1 as `25.0.0` before Provision. The new Cloud
  Test is `ed3ee855-f01e-4eb4-bb26-dad2751e8496`; authoritative observation
  confirms provisioned/Online and membership in Test Vehicles.
- Cloud first showed factory VDP `0.0.0` with `25.0.0` pending. Native Safe Stop
  then installed it: guest process active since 15:11:29 UTC, slot `a`, matching
  process/slot, seven read paths, LIVE/READY and zero VDP restarts. Cloud
  independently reports installed `25.0.0`; it does not report process state.
- Brake V1 `13.0.0` was prepared and published through UI and reached READY.
  Native Autopilot showed 19.4 km/h/MOVING before first assignment. The first
  Deploy returned PARTIAL at 15:15:11 with `noOp=true` and
  `UNIT_CLOUD_UNAVAILABLE_URLError`. A fresh Cloud read at 15:16:05 confirmed
  Online and only the default Subject, with no service assignment. One
  reconciled Deploy retry was then submitted; no VM/manager restart was used.
- At the user's additive request, a separate read-only agent exported the
  actually running .33 CM/SM executables and a sanitized handover archive
  outside Git. Source/running/exported hashes match; both managers remained
  active with zero restarts. The export did not interrupt this run.

### Live continuation and preflight accounting correction

- The second Deploy made no POST: the first worker had left its durable bind
  intent at `ATTEMPTING` after a pre-POST transport failure. The no-replay guard
  correctly refused that old incomplete record, but the worker had failed to
  distinguish a failed read-only preflight from a submitted POST.
- Source now returns `BLOCKED`, `attempted=false` for transport failure during
  worker authentication or assignment preflight. A transport failure inside
  POST remains `UNCERTAIN`, `attempted=true`; lost worker responses still block
  replay. Thirty-six focused assignment tests passed, including these negative
  paths, secret redaction, idempotent repeat and Production-selector refusal.
- The user authorized exact legacy recovery. Existing `service assign` accepts
  the explicit operator attestation `--confirm-bind-not-submitted-at` with the
  exact legacy bind `startedAt`, only after independent proof that POST was not
  sent. It requires an unchanged recorded ATTEMPTING bind, no HTTP receipt,
  exact owned Subject/current Test, and fresh authoritative absence. It retains
  the old attempt and operator confirmation in `preflightRecovery`. Ordinary
  Deploy does not infer non-submission from absence and does not use this flag.
- Recovery of `2026-09-13T15:14:58.911973Z` completed at 15:25:41 UTC through
  democtl: Brake Subject is bound to the new Test and contains only Brake.
  No manual journal edit, VM/manager restart or Cloud UI mutation was used.
- VDP `26.0.0` / V2 remained pending while native Autopilot showed 19.4 km/h.
  Safe Stop then installed it at 15:25:10 UTC: slot `b`, active/slot match,
  fifteen read paths, LIVE/READY and zero VDP restarts.
- First Brake `13.0.0` reached the VM but exited before backend delivery.
  Engineering observation found both public metadata files absent. This run
  had omitted the documented first-service `service runtime-prepare test`
  step (Factory .33 receipt, executed sequence step 5); the current UI Deploy
  plan also omits it. The existing democtl preparation completed against VDP26
  without SM activation/restart. This is a UI-sequence gap and an assisted run,
  not a passed unassisted clean UI cycle. Service recovery is not yet claimed.

### Confirmed runtime progression

| Observation (UTC) | Evidence |
| --- | --- |
| 15:31:35 | Cloud `27.0.0` pending over installed `26.0.0`; native Autopilot/MOVING, 17.7 km/h before Safe Stop. |
| 15:31:54 | VDP27/V3 active in slot `a`, 23 read paths, process/slot match, LIVE/READY, zero provider restarts. |
| By 15:32 | Native Brake13 container alive after normal update processing with public inputs present; CM/SM were not manually restarted. |
| 15:34:26 | Brake backend confirms 54 synthetic chunks and six completed windows from Brake13/V1, exact current Test and dedicated Subject. |
| 15:34:33 | Cloud-only service collection is CURRENT but empty (total 0), despite the independently observed native service/backend. The UI's Not reported state must not be substituted with guest evidence. |
| 15:35:58 | Brake14/V2 produces synthetic assessment/event receipts, replacing Brake13 after SP publication only; no second assignment or Safe Stop. Native vehicle remains in Autopilot/MOVING. |

The first Brake13 startup failure and assisted input preparation remain part of
this result. Later recovery does not retroactively qualify a clean first launch.

## Final working handoff — 15:44 UTC

- Same fresh Factory .33 Test is Online. VDP progression `25.0.0` / V1 →
  `26.0.0` / V2 → `27.0.0` / V3 completed. V2/V3 stayed pending while moving
  and installed after native Safe Stop; final VDP has 23 LIVE/READY read paths.
- Brake `13.0.0` / V1 → `14.0.0` / V2 → `15.0.0` / V3 completed after the
  documented assistance. Both replacements happened while driving by SP
  publication only, without another Deploy or Safe Stop. Backend receipts
  prove each release; Brake15 assessment first observed at 15:39:01 UTC.
- Tire `11.0.0` / V1 first assignment/install/run completed while driving.
  Backend received assessment, band-change and function-status messages at
  15:42:34 UTC. Brake assignment and active process were preserved.
- At 15:44:50 Cloud independently reports both exact services installed, one
  active instance each (Brake15 and Tire11), with their separate retained
  Subjects. The earlier empty service inventory resolved; at 15:38 the UI
  briefly showed Connected, then returned Online without a recovery restart.
  No Cloud log correlation was collected for this specific transient, so its
  exact cause is not asserted here.
- Both actual product dashboards opened in the implemented UI: Tire showed
  five stored mock messages and Brake109 at their respective observations.
  Each labels inputs MOCK DATA and vehicle advisory Not connected. Native
  telemetry is LIVE; final driving state is Safe Stop, 0.0 km/h, brake100%.
- Production local VM ID remains `54d45d8f-7813-43aa-81c9-09152cbee0f7`.
  No new VM image, manager replacement/restart or Production mutation occurred.
- Focused source gates: assignment36, CLI6 and Presenter-operation10 tests
  passed; `git diff --check` passed. No commit/push was performed for this
  increment. Binary handover artifacts remain outside Git.

### Still open after this run

1. Integrate the documented public-input preparation/refresh into the UI
   deployment sequence. The first-launch omission required engineering
   assistance and cannot be presented as an unassisted UI pass. This run's
   explicit preparation used VDP26; no claim is made that the later synthetic
   receipts establish fresh VDP27-derived service telemetry/provenance.
2. Real service KUKSA permissions, vehicle-derived analytics/advisory and
   server-side stale-connection repair retain their existing exclusions.
3. Retained-identity Park/Resume, Tire successor replacement and the complete
   outage matrix were not repeated in this UI continuation. Their previous
   .33 engineering results are separate evidence, not new observations.
4. Human visual acceptance remains pending. The VM/simulator/backends were
   initially left running in Safe Stop at 15:44; the subsequent user-requested
   retirement below supersedes that runtime handoff.

### Post-audit source corrections — 13 September 2026

The user authorized correction of both command-audit findings. Studio Deploy
now composes `service runtime-prepare test` before first assignment for either
team. The protected worker stops before assignment on blocked, partial or
unknown preparation; duplicate request IDs do not repeat either step. An
unchanged preparation still permits normal assignment reconciliation. There
is no new standalone browser capability, SM activation/restart or Safe Stop
dependency. Higher service releases retain publication-only updates.

Presenter simulation Start/Stop now explicitly carry `target=test`. The shared
API adapter accepts and preserves that scope and rejects Production/all scope;
the existing unscoped non-Presenter API form is retained for compatibility.
The runtime-input step is likewise admitted only with its fixed Test fields.

Validation: 144 focused tests passed across Presenter/API/session shutdown,
service inputs, simulation, source selection, service assignment and Test
lifecycle; `git diff --check` passed. Regression tests reproduced the original
omissions and the API-adapter rejection before correction. The test workers
use isolated fixtures; no live VM/Cloud operation, service deployment, image
build, commit or push is claimed. Finding 1 above is source-corrected but its
unassisted fresh-VM UI acceptance remains open; the historical assisted run
is not relabelled as a clean pass.

## User-requested end of demo — retirement completed

- `democtl demo retire` stopped the simulator, native Driving Control and
  Gateway, then gracefully shut down the entire current Test VM. No separate
  CM stop, replacement or restart was performed for this retirement.
- Cloud WebSocket logs independently record normal disconnect code1000 at
  **16:09:45.607 UTC**, exact Test system UID
  `4e5a174d4cdf4980967c1b8ac77fc376`, trace
  `9e39bce415775dc79f693cbf2f948c3e`. The latest preceding full Unit status
  arrived at the message handler at 16:09:34.598 UTC. The inspected result
  contains no subsequent connection or Unit message for this Test.
- Retirement returned `PARTIAL`, phase `deprovision-test`, at 16:11:18 UTC:
  `UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE`. An authoritative Cloud read at
  16:14:59 UTC still reported provisioned/Online for Unit
  `ed3ee855-f01e-4eb4-bb26-dad2751e8496`. No deprovision/delete request had
  been submitted and the Test overlay/local factory copy were not deleted.
- This is a recurrence of a stopped transport with stale stored Cloud status;
  the earlier 1800-second incident is not proof of the same internal cause or
  of the completion time of this new incident. Resume the existing retirement
  only after authoritative Offline, without restarting the Test to recover
  status or bypassing the gate.
- Scope remains the current Test run. Preserve Production, immutable Factory
  .33, retained service Subjects and service associations, published releases,
  automatic release-number continuity, source/qualification documents and the
  sanitized SM/CM handover archive. Cleanup completion is not yet claimed.

### Completion after authoritative Offline

- At **16:55:14.955622 UTC**, `democtl unit cloud-status test` confirmed
  provisioned/**Offline** for the same exact Unit. This is the observation
  time, not a measured time of the Cloud's transition to Offline.
- The already-authorized `democtl demo retire` resumed from its recorded
  phase. Cloud deprovisioning reached new/Offline, membership removal
  completed, and Unit plus Node absence were authoritatively confirmed.
- Retirement completed with `COMPLETED`, phase `RETIRED`, by 16:56:47 UTC.
  The retained journal now contains only Production and
  `testRetirement.state=COMPLETED`; the transient Test lifecycle record is gone.
- The following disposable Test files are confirmed absent, deleted without
  backup: `.local/demo-current/validation.qcow2`,
  `.local/factory/test-factory.img`, and
  `.local/factory/test-factory.manifest.json`. Owned Test runtime/backend
  cleanup completed through the same lifecycle operation. No raw shell
  deletion or replay of a submitted Cloud mutation was used.
- Production identity remains `d87ba9cb-b21f-45db-8773-553e52d0353e`, local VM
  `54d45d8f-7813-43aa-81c9-09152cbee0f7`. Retained Brake/Tire Subjects remain
  recorded. Immutable Factory .33, release continuity, published releases,
  source/evidence and the binary handover archive are preserved.
- No source implementation change, rebuild, new test run or commit/push was
  performed during this retirement. No reclaimed-byte total was measured.

## Follow-up UI lifecycle refresh correction

The user observed that the already-open Studio retained `Retirement paused`
after CLI retirement had completed. A page reload returned to Create. Local
snapshots previously polled only on a visible 10-second timer; foreground/focus
did not trigger a read, and manual Refresh/post-action observation updated only
Cloud, not the local lifecycle snapshot.

The authorized correction adds foreground/focus reconciliation to the existing
local adapter, deduplicates its in-flight snapshot read, and refreshes the local
snapshot alongside explicit Refresh and post-action Cloud observation. Hidden
tabs schedule no local polling; the visible idle interval remains 10 seconds.
No lifecycle order, Cloud authority, mutation replay or direct-guest UI access
was added. Production and the retired Test disposition remain unchanged.

- Five new targeted cases reproduced the old behavior before the correction.
- After correction, 33 focused unit tests passed, including the added visible
  idle-poll case, adapter cleanup/deduplication and manual/focus reconciliation.
- Three isolated browser scenarios passed: partial Online retirement remains
  blocked, partial Offline offers continuation, and external CLI completion
  returns the existing page to enabled Create with no reload or mutation.
  These tests used intercepted API fixtures, not a new live lifecycle cycle.
- Type checking and frontend build passed; only frontend assets were rebuilt.
  Changed-file whitespace checks passed. No VM, service or Cloud operation,
  commit or push was performed for this correction.
