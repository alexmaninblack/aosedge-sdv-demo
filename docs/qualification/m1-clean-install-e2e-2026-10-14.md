<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 cleanup and installed demo testing on 14 October 2026

The M1 was cleaned and the unchanged engineering DMG was installed again.
All 118 API steps passed. The continuous visible UI campaign passed 40 stages
and failed its restart preservation check. A separate diagnostic restart and
all 15 stages of the focused visible UI restart scenario then passed on the
same preserved Test. **Full uninterrupted E2E remains NOT_COMPLETE**: those
later passes do not replace the first failure. One instrumented full UI repeat
then stopped at Brake V1 because its newly delivered window had an incomplete
source gap, despite a completed physical maneuver.

## Installation and test scope

The target was the dedicated Apple Silicon M1 with internal storage, connected
to Aos Cloud staging. The development Mac orchestrated the scripts and ran
unit tests; it did not run the installed demo or live UI qualification.

| Item | Value |
| --- | --- |
| Starting integration source | `d4a1c72d17e21123a61babed9888315ff7deaae9` |
| DMG | `AosEdge-SDV-Lab-Native-Live-20261012.dmg` |
| Bytes | `14165529112` |
| SHA256 | `5e0dbf77f6b48e9efcaee8a38b85157dd691c0bb11369f316e5919fe5fa6f719` |
| Application manifest | `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c` |
| Factory | `6.1.1-maninblack.41/main-qemuarm64` |
| Preserved new Test | `50674c94-d590-437a-8d6c-acf4d0d341c9` |

The existing verified M1 media copy was reused. No multi-gigabyte download,
CARLA or Factory rebuild, new product package, or public publication was needed.
Signing remains an Apple Development engineering preview, not notarized
distribution. Native Setup button-input and clean-first-user acceptance were
not part of this scripted installation.

## Cleanup before installation

The previous current Test was retired through the normal owner with Cloud
absence, empty Test selection, absent journal and absent overlay confirmed.
A legacy R5 VM had no Cloud identity, but its historical shutdown evidence did
not satisfy the normal Finish guard. Its PARTIAL receipt was retained; the
abandoned local experiment was disposed of separately after ownership and
absence of Cloud and Production identities were checked.

Old package stores, experimental state directories, the obsolete launcher and
an old DMG were removed before installing the selected package. This freed
`271054102528` bytes. Final housekeeping removed 19 obsolete qualification
application copies and the older Chrome 154 tool cache, freeing another
`1679798272` bytes. Total observed recovery was **272733900800 bytes**, about
273 GB or 254 GiB. Final observed free space was **340826267648 bytes**.

Current media, the newly installed package and Test, current UI tools, signed
native runner, credentials, compact reports and reusable Docker images were
preserved. Deleted old run data cannot be restored; deleted programs remain
recoverable from their retained media and source.

One Docker Engine restart was needed during cleanup because its virtualization
process retained old backend bind references after those containers had been
removed. It was an explicit host-maintenance action with zero remaining
containers, not a routine test restart. The engine identity was unchanged.
The development Mac's unrelated Docker project was untouched.

## API results

The complete 118-step API scenario passed, including fresh controller creation
and provisioning; serial VDP V1, V2 and V3 updates through Safe Stop; serial
Brake V1, V2 and V3 plus Tire V1 installation; real maneuver products and
advisory observations; independent resets with history preserved; a five-minute
offline soak, queued delivery after reconnection; ignition off and on; and
ordinary Stop and Start with retained identity, models and new products.

The scenario owned the normal actions, independent observations and shutdown.
VM access used the already authorized private test input without a human
password pause. Shared Docker stayed running during the test sequence.

## Visible UI results and restart failure

The browser and native control runner executed on the M1 with Presenter,
CARLA and Driving Control visible. The first campaign passed release delivery,
installed views, independent resets, cancellation, real maneuvers and moving
Brake and Tire QM updates. It then failed at `continuous-restart-preserved`
with `CONTINUOUS_RESTART_STATE_CHANGED`. Final `confirmed-stop` was not run
as a business stage; mandatory shutdown still passed.

That error covered several predicates but did not retain which one failed.
It therefore does not establish a VM crash, lost model, lost history, service
restart or VDP timeout. The original failure remains unresolved.

The bounded API diagnostic compared state around one further Stop and Start.
Three fresh observations confirmed a changed boot ID, unchanged Test identity,
preserved Brake and Tire model hashes and history, fresh stationary Manual
control, and all four platform services active with successful results and zero
restarts. No publication, Reset, reprovisioning or Finish occurred.

The subsequent `restart-check` visible UI scenario passed all 15 stages,
including the unchanged restart predicates, exact installed versions and final
confirmed Stop. It used the same Test and package, with no new release or Reset.
This is a separate experiment, not a continuation that qualifies the failed
continuous campaign's original baseline.

The test harness now records fixed Boolean restart predicates and offers this
bounded scenario. Deadlines, freshness checks, VDP timeout, service algorithms
and product authority were not relaxed. Product bytes did not change.

## Instrumented full UI repeat

One further full continuous campaign used the improved restart diagnostics,
the same package and Test, and its confirmed current baseline. It passed eight
stages, including VDP V1 installation, before `brake-v1` failed with
`NATIVE_UI_POSTCONDITION_FAILED`. Later release and lifecycle stages were not
run. Its signed native receipt confirms the exact Brake mouse input, and the
retained source-owner result confirms a new completed Brake exercise with
physical Stop, matching run and operation identities, and no no-op.

A bounded backend-only diagnostic read the retained window through the normal
API. Brake release `153.0.0` produced window
`7b44daf1-651b-4123-8ad4-e9e97ca1cd6c`, beginning at 08:48:48.595 UTC. All
seven chunks were durably received, but its terminal state was
`INCOMPLETE_SOURCE_GAP`. The test correctly excluded it from complete products.
Pagination did not hide a successful result: the backend held only three raw
windows, and the other two complete windows belonged to older releases.

This establishes an invalid input window, not a missing UI click or missing
backend delivery. It does not establish whether the interruption came from
scheduling, timestamp coherence, transport or another source condition. The
VDP timeout remains deferred, and no timing or quality rule was relaxed.

The harness now projects bounded window quality fields alongside its unchanged
complete-product projection. A completed physical exercise plus a new fully
delivered invalid window can fail promptly with its specific reason instead of
waiting for the generic deadline. This addition passed unit tests against the
observed window shape; it has not been exercised in another full live campaign.
Final targeted gates passed: **20 JavaScript and 91 Python unit tests**. Three
temporary Unix-socket fixtures initially hit the development sandbox restriction
and passed when rerun with only that local unit-test access.

A controller-only historical-log diagnostic did not retain a usable quality
projection and exceeded its graceful Stop observation budget. QEMU subsequently
exited without forced termination. After a read confirmed the original PID was
absent, the normal owner reconciled the journal to STOPPED without sending
another guest signal. This later diagnostic shutdown is separate from the
passing API and UI cleanup results.

## Timings

| Recorded phase | Duration | Result |
| --- | --- | --- |
| Removing old installations | 10.414 s | PASS after old owner disposal |
| Fresh installation and preparation | 211.232 s | PASS |
| Complete API scenario | 1681.892 s, 28 min 2 s | 118 PASS |
| First visible UI campaign including cleanup | 1351.269 s, 22 min 31 s | FAIL |
| Bounded diagnostic including cleanup | 336.273 s, 5 min 36 s | Diagnostic complete |
| Focused visible UI scenario including cleanup | 380.272 s, 6 min 20 s | 15 PASS |
| Instrumented full UI repeat including cleanup | 469.140 s, 7 min 49 s | FAIL at Brake V1 after 8 PASS |

These are script durations, not the total elapsed session. The recorded
operational window from the first retirement intent at 06:56:32 UTC to the
final closure observation at 09:10:12 UTC was about 134 minutes. It also
included resolving the legacy cleanup guard, stale Docker handles, missing
failure diagnostics and a private display helper pinned to a deleted old
package, the incomplete-window investigation and late diagnostic shutdown.
Those preparation and investigation intervals are not hidden inside the API
or UI success times.

## Final state and next check

All owned demo processes, listeners, browser and native clients, media mounts
and display assertions were closed. The two new backend containers were
retained in `exited` state, and Docker Engine remained available. The new Test,
VM disk, model data, release receipts and history were preserved.
The interrupted repeat left VDP `171.0.0` and Brake `153.0.0` at their V1
profiles, with Tire `76.0.0` retained. This is a preserved failure reproduction,
not a ready-to-show V3 capability baseline. No automatic rollback or later
release publication was substituted for the failed step.

Private receipts are retained under
`.local/remote-qualification/m1-full-e2e-20261014`, with the first campaign,
restart diagnostic and UI restart scenario in separate directories. Original
FAIL and PARTIAL receipts were not rewritten.

Before another full campaign, investigate the actual source-quality gap in one
bounded maneuver scenario rather than replaying all releases. The first restart
failure also remains open: its separate passing repeats did not identify the
original failing predicate. Native Setup input and clean-first-user acceptance
remain separate gates.

## Subsequent production investigation — separate from staging acceptance

The later production campaign used `aoscloud.io`, the dedicated M1 and
integration branch `codex/production-demo-migration`. Its installed application
manifest was `a751faa5922d0f14a4af6f19048e788250d7d29a7870247318090576ffcbfe7a`,
built from integration commit `79857d07ec95f278fa3c5ea073ab3fe9d3a42ad4`.
It did not qualify the failed staging scenarios above or the complete
production API/UI journey.

Production initially assigned an older VDP `56.0.0`. Preserved provider logs
show repeated successful VISS connections and DATA_READY transitions followed
by `VISS source frame is not monotonic` and reconnects. Consequently, the
subsequent `VISS_MTLS_UNAVAILABLE` status is not proof of an invalid certificate:
the original failure is inside the installed provider's frame-order handling.
The old diagnostic does not distinguish identical repeats, changed values at
the same timestamp and actual time regression; original raw frames were not
retained, so the exact historical packet subtype remains unproved.

A pure synthetic fixture executed against the actual installed VDP 56 bridge
and the already prepared VDP `57.0.0` payload reproduced a concrete difference:
56 rejected an identical periodic snapshot and published unavailability; 57
ignored it without creating a new measurement. The 57 payload still expired
stale data and rejected changed values at an unchanged timestamp. All
39 focused frame-order and VDP-family unit tests passed. No installed provider
bytes, credentials, timeout or freshness rule were changed for this proof.
The repeated-frame correction is already present in 57; it does not require a
new Factory, CARLA build or another publication merely to obtain the fix.

The later FOTA/boot refusals have a separate, demonstrated preparation chain:

1. Normal failed-run cleanup detached and stopped the source.
2. The retained recovery scenario restarted the simulator but did not select
   the Test before publishing 57. Its Source restore check accepted
   RUNNING_UNASSIGNED as owner availability, not connection readiness.
3. Replacement requires Safe Stop through the selected, authenticated Update
   Runtime path. With that path absent, the durable removal of 56 remained in
   `waiting-for-safe-stop` while CM retained the desired 57 request.
4. Normal VM boot then returned `SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE`.
   SSH was available and CM/SM/VDP processes were active: this was a refused
   preparation step, not proof of a VM crash or missing Cloud authority.

One bounded recovery proof left the normal 480-second wait unchanged. A new
waiting removal transaction was observed after that interval; the Test did not
become quiescent within the diagnostic deadline. The scenario did not bypass
the active-transaction guard, re-enroll, reprovision or publish another release.
Its final cleanup and exact timing are retained in the private scenario result;
no live VDP 57 installation or complete UI acceptance is claimed here.
That recovery diagnostic took 769.208 seconds, including the unchanged wait
and graceful shutdown. The first Stop observation exceeded its budget; later
actual QEMU exit was independently confirmed and the normal journal was
reconciled without another guest shutdown signal. Final owned process and
listener counts were both zero. The retained Test and its disks were not deleted.

The next fresh campaign must preserve the initial authenticated Test assignment
established by Provision, request physical Safe Stop and install the current
V1 before redundantly confirming full provider-data connection readiness.
A retained-source recovery must independently confirm its actual assignment
before publication; a running but unassigned simulator is insufficient.
Do not detach the source in the middle of the update and then infer that a
timeout or certificate reset will restore the prerequisites. An incompatible
pending retained Test must be classified explicitly rather than fed another
publication.

Compact private evidence is under
`.local/remote-qualification/m1-production-fota-cause-20261014` and
`.local/remote-qualification/m1-production-retained-recovery-20261014`.
The earlier failure receipts are preserved. Existing Production-role resources,
shared Docker, Factory inputs and public release pointers were not changed by
this investigation.

### Overnight campaign readiness and execution boundary

The follow-up full API/visible-UI campaign was prepared to reuse the already
verified installed candidate, M1-local production credentials and cached DMG.
It declares a fresh Test policy and normal retirement of the classified failed
Test; it does not attempt another publication into the pending retained Test.
The execution safety review refused dispatch because exact production Test
retirement was not yet explicitly confirmed. No deletion, replacement Test,
release publication or live API/UI step was dispatched by that campaign.
An exact-target confirmation was requested; the refusal was not bypassed.

The unaffected checks completed: 191 offline qualification/UI/Cloud-scope,
source-assignment and Safe Stop contract tests passed. A subsequent read-only
M1/Cloud preflight authenticated the pinned production owners and both existing
subject references. It confirmed the selected installed candidate, an unlocked
M1 desktop, the preserved failed Test and Production Unit, no running demo
processes/listeners or containers, and the unchanged shared Docker Engine.
The occupied Cloud setup remained BLOCKED, not READY or qualified.

The retained Test is `554b4905-dd7d-4e62-94ea-3fbdfcd7b01c`, Cloud Unit
`989e8027-3e3f-4648-a73d-d2a494f73294`. Any authorized fresh replacement must
continue to exclude Production Unit `d87ba9cb-b21f-45db-8773-553e52d0353e`.
The read-only result is retained privately as
`m1-production-fota-cause-20261014/overnight-preflight.json` below the existing
qualification evidence root. Unit checks and campaign preparation are not
reported as a completed production end-to-end test.

### Authorized fresh replacement and baseline readiness correction

The operator subsequently explicitly authorized deletion of the historical
Test data and a fresh production campaign. Normal retirement removed Test
`554b4905-dd7d-4e62-94ea-3fbdfcd7b01c`, its overlay, journal, backend run data
and Cloud Unit `989e8027-3e3f-4648-a73d-d2a494f73294`. Independent absence
checks preserved Production Unit `d87ba9cb-b21f-45db-8773-553e52d0353e`.
A wrapper incorrectly called BackendService after retirement had already
removed its required journal; authoritative reconciliation confirmed APPLIED
without repeating retirement. A changed DMG ctime was reconciled by one
consumer checksum, not a new copy or a content-corruption claim.

Fresh Test `b30d3a8f-4dae-430c-a480-9f5402811637` / Cloud Unit
`d37edb31-6386-4e19-aa42-003373fcec0d` completed native SDK provisioning and
Cloud Online, but its initial local connection returned
`SOURCE_SELECTED_DATA_NOT_READY:UNKNOWN`. Its fixed-role assignment and
certificates existed; there was no installed VDP, pending slot transaction,
Test-set membership or new release publication. The blanket cleanup could
not finish the still-incomplete source handoff; this was not a completed E2E.

An exact-owner reversible proof used the normal Test gate and enrolled
update-runtime identity. It obtained server-verified mTLS and advancing VISS
frames with unchanged credentials, then restored the blocked gate. Inspection
also showed that connection(wait=True) returned immediately on a failed
Factory-baseline sample, unlike its installed-provider branch. The original
failing sample's cause was discarded as UNKNOWN; its exact transport/frame
subtype is not claimed as proven.

The correction applies the existing 12-second read-only observation window to
that baseline branch and preserves the last refusal reason. It changes no
deadline, freshness requirement, certificate, assignment authority or FOTA
guard. Regression tests cover transient refusal followed by valid frames,
deadline failure, no mutation replay and unchanged non-waiting behavior.
A transient in-process adapter then completed the same Test's local first
connection in 8.748 seconds, with real mTLS/advancing frames and unchanged
Unit identity. The original adapter was restored, installed package bytes
were unchanged, and normal shutdown independently confirmed zero owned demo
processes/listeners. This proof is not acceptance of a corrected immutable
installer; the corrected package still requires a new full API/UI campaign.

Private follow-up evidence is in
`.local/remote-qualification/m1-production-overnight-20261014`.

The source gate passed 189 affected orchestrator/crypto/provisioning/boot tests
using the existing Cloud SDK Python, and 191 qualification/semantic-UI/contract
tests. An initial broader developer run used system Python and found missing
SDK dependencies plus crypto fixtures inadvertently consuming the developer
workspace's obsolete host-runtime catalog. The fixtures now explicitly isolate
their temporary crypto inputs; SourceDriver's read-only asset assertion uses
a mock packaged-runtime boundary. Product runtime verification was not relaxed.
The corrected affected modules and the documentation quality gate passed before
preparing the package-only successor. These unit counts are not live acceptance.

### Readiness successor: complete API pass, visible-UI input-quality failure

The immutable successor from integration `36e8b99` has manifest
`ae7a6454f3aeab159499361cdfe3e1633af8bc77a134790412eeab604c182c5c`.
Fresh installation and native production enrollment completed on M1 Test
`6a1fae4b-1a53-4d8f-9d39-ac0c30abc94a`. The complete API journey passed
118/118 checks in 1701.537 seconds, including serial VDP/Brake versions,
Tire, real model products/advisories, independent reset/history, five-minute
offline/recovery, ignition off/on, persistence and Stop/Start. Production's
existing Unit was excluded; staging was not touched.

The separate visible UI journey passed startup/layout, VDP V1/V2/V3 and Brake
V1/V2. Brake V3 installed as 42.0.0, but its real native-input maneuver produced
no new assessment. The signed click receipt and persisted exercise confirm
actual input and motion: 267 frames, maximum 30.579 km/h and 31 braking frames
above 10 km/h. It was not a missed UI click. Previous-boot bounded quality logs
show FUTURE_TIMESTAMP rejections with 1–20 ms clock lead and an incomplete
source-gap capture. Exact original raw samples were not retained, so individual
sample-to-abort causality is not overstated. Later UI gates were NOT_RUN.
The campaign is NOT_COMPLETE, not a full-E2E pass. Normal shutdown confirmed
zero owned processes/listeners and closed the runner, tunnel and mounted media.

A production-equivalent isolated clock proof reproduced the old publisher's
future exposure and proved source-preserving publication ordering. Platform
`fade0de2412efa71d739cf6e5d7e41308838f0b8` waits for the original source time
inside the existing two-second publication budget, including connection and
Set. It adds no timestamp rewrite, queue, future tolerance or freshness change.
Large lead/nonadvancing clock fails closed; unavailability is immediate. Seven
new regressions plus 55 provider/profile/order/provenance tests and the Platform
quality gate passed. All three new VDP profiles use that reviewed common runtime;
retained releases remain inspectable against their original pin. Brake, model
arithmetic, consumer future guards, Factory and CARLA bytes are unchanged.
The new immutable artifact requires its own live API/UI qualification.

Private API/UI receipts, quality logs, clock proof, timing and cleanup evidence:
`.local/remote-qualification/m1-production-readiness-full-20261014`.
