<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio implementation checkpoint — 10 September 2026

Status: **partial implementation; not ready for final operator E2E**.
The [accepted P1–P8 plan](../planning/active/demo-studio-delivery-plan.md)
remains authoritative. No mockup flow or live Presenter composition was changed.

Latest result: **Test VDP18 is actually running, READY/LIVE, with 23 read paths**
after the authorized queued-recovery SM proof. Cloud reports installed18,
Online and no pending component. The immutable Factory .31 is unchanged;
this remains a transient runtime proof, not a clean-image/full-Studio claim.

## Resumed: bounded Test timing correction — 10 September

The user restored the connection and asked to continue. Before changing SM,
`component status test` confirmed VDP **17.0.0 actually running**, slot b,
PID 9639, 15 read paths, READY/LIVE, matching process/slot and zero restarts.
Its start time was **00:23:49 UTC**. The reconciled Cloud read at 00:30:32 UTC
also reports installed 17.0.0 and Online. This completed under the original
SM, not the new timing patch; the earlier timeout remains historical evidence.
No duplicate publication or forced retry was used.

The operator separately authorized relaxed local-demo timing. The
[revised Test allowance](../../contracts/platform-fota-safe-stop/README.md#local-test-timing-2026-09-10)
admits signed age ±5000 ms and a 1000-ms read deadline. Production/standard and
physical Safe Stop conditions remain unchanged. Platform source candidate
`0e645a549b299dfa88ae7fc3725a1c1dee2bf3a1` has 22 passing targeted source/static
tests; native execution and live proof are recorded below when completed.

An experimental bounded root-network probe observed 179 future-timestamp reads
out of 400 (age range -19.967 to +32.829 ms), 339 repeated frames and no stable
window under the old future-rejecting policy. This was Python/root evidence,
not a native SM trace or proof of a sole cause. Its temporary window evaluator
was removed after diagnosis; no second policy evaluator is retained in Demo
Control. The existing two-snapshot read-only diagnostic remains.

The existing `component sm-build test` / `sm-apply test` path is pinned to this
source and current Test identity, not the retired .30 proof. It compiles only
SM offline, tests natively, exports outside Git, stops Builder and permits one
transient Test-only restart with no active transaction. Factory image bytes,
Cloud identity and Production are preserved. Next functional transition is the
already prepared **17 → 18**; 17 is not reinstalled to repeat a completed step.

### Targeted native build and transient application: passed

`democtl component sm-build test` compiled only `aos-servicemanager` offline;
1708 of 1716 tasks were reused. All **18 selected native tests passed** in
105 ms, including signed-age boundaries, unchanged standard future rejection,
role-specific read deadlines, physical/reset/frame gates and stop cancellation.
Builder stopped cleanly. Binary SHA256:
`9abeebc94ff10061743c4d2ba1c7fe0873c989369405bb525e3e9412e800a786`.
Artifact: `demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-clock-skew`.
The Solution component suite passed **71 tests**; the existing probe suite
passed five tests. This is not a full-image build or full-suite claim.

`component sm-apply test` applied one temporary read-only bind mount and one
SM restart. Process PID 13860 has the exact new binary hash, effective
`demo-5s`, initialized Test role and both public inputs. SELinux remained
Enforcing with zero fresh AVCs. VDP17 PID 9639 stayed active with zero restarts.
The transient source is `/run/democtl-sm-demo-clock-skew/aos_sm_app`; the
drop-in is `/run/systemd/system/aos-sm.service.d/91-democtl-sm-demo-clock-skew.conf`.
These disappear on VM reboot; no immutable Factory bytes were changed.

### Next live gate: VDP18 ready, Test Cloud transport unavailable

Native Autopilot and independent `democtl status test --guest` confirmed
movement (18.32 km/h), fresh frames and connected Test. VDP18 was uploaded
once at 00:58:43 UTC, deployment `663a9d45-a06e-4f1f-b2b2-ef6cd6cca05c`.
At 00:59:15 UTC Cloud reported **READY**, version UUID
`9c2165e9-ff2f-40a4-8c5c-ab134d32a1b8`, assigned to Test as `to be installed`,
but Test **Offline**. No batch approval, duplicate upload or Production
operation was performed.

CM is active and guest DNS resolves, but bounded logs repeatedly report
message-delivery failure. No desired status for 18 was observed in those logs;
the latest completed update remains 17. Therefore the revised SM live
replacement gate is **not yet proven**. A separate bounded proposal is to
expose an explicit `democtl unit reconnect test` and restart only CM once,
preserving identity, VM, VDP, source and Production. That new operation has
not been implemented or executed. The user instead explicitly requested a
restart of the Test VM; no new `unit reconnect` command was added.

The existing selected-vehicle stop guard required detachment first. Through
Demo Control, `simulation stop --target test` confirmed physical Safe Stop and
detached Test, then its CARLA stop wait expired at 30 seconds. `vm stop test`
also exceeded its 90-second wait. Subsequent read-only process/status checks
confirmed **both processes had exited normally**, without force termination.
Reconciliation reported `alreadyStopped` for Test and completed the simulator
stop. `vm start test` then booted the same overlay in **26.62 seconds**, with
guest SSH/DNS ready, persistent Test role unchanged and provisioned identity
preserved. No backup, reprovisioning or new image was involved.

### Post-restart result: separate queued-update recovery defect

Cloud returned Online for the same Unit and delivered 18. Reapplying the
temporary SM returned `SM_ACTIVE_TRANSACTION_PRESERVED` before any mutation:
the queued removal had already resumed. The new timing binary is therefore
**not currently applied after this VM restart**. The simulator was restarted
and selected Test through Demo Control; physical Safe Stop and fresh source
frames were confirmed, with Production's source gate still blocked.

Fresh guest status disagrees with an interpretation of Cloud's installed-17
row as Running: provider is **inactive**, activeVersion is null, read paths
are zero. `installed.json` still records the prior installation; the retained
transaction is remove17 / `waiting-for-safe-stop`. SM entered an automatic
restart loop (13 restarts observed); CM remained active. VDP18 has not been
proven running, and the revised timing gate has not been live-qualified.

The existing `component logs` now retains the earliest twelve redacted SM
launcher errors from a bounded 4000-event current-boot window, separately from
the latest 200 general events. The first launcher error at epoch microseconds
1789002598565357 is the `aos-vehicle-data-provider-health active` command
failure. Subsequent errors say `waiting transaction lost its healthy active
release`. This establishes the initial health failure before link-loss errors,
rather than inferring the first failure from the restart loop.

Source analysis identifies a separate defect: waiting-transaction recovery
validates the committed previous slot but checks its running health without
starting the provider. The VDP unit intentionally has no boot enable target.
Unlike ordinary installed recovery, this path calls FailClosed, which stops
the provider and removes the active selector while retaining both durable
JSON records. Later starts fail on the now-missing selector before they can
resume the Safe Stop worker. Timing is not evaluated on this failed path.

The bounded repair proposal is to start and health-check the validated
committed predecessor during queued-update recovery, preserving waiting
intent and the unchanged stopped-predecessor/empty-first-install branches.
The already affected Test also needs an explicitly authorized restoration of
its prior active selector from validated durable slot records; source repair
alone must not silently manufacture a missing selection. The user approved
both corrections; their execution is recorded below.

### Authorized queued-update recovery: targeted build passed

Platform commit `7f168e9bd5338dd9320ebbd6fe0f6043fcc1eb65` changes only the
waiting-with-committed-predecessor startup path and its native fixtures on top
of the accepted timing correction. It tries StartProvider and a health recheck
without deleting valid waiting state when either fails. Missing active links
are not automatically recreated, intentionally stopped predecessors stay
stopped, and empty first install is unchanged.

`democtl component sm-build test` compiled only SM offline, reused 1708 of
1716 tasks, and passed **29 native tests in 545 ms**, including 11 new queued
remove/replacement, failure-preservation and stopped-predecessor executions.
Builder stopped cleanly. Binary SHA256:
`cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee`.
Artifact: `demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-queued-recovery`.
Solution tests passed 78 component cases and 16 source cases.

The existing Test-only `sm-apply` validates installed17/slot b against both
transaction predecessors and the slot record, rejects stopped/foreign state,
then stops SM, revalidates, restores only the missing relative selector and
starts the corrected runtime. No installed or transaction JSON is rewritten.
The first 108,313,720-byte uncompressed proof transfer returned unavailable.
Read-only reconciliation confirmed stock SM, no proof directory/drop-in, no
active selector and unchanged durable records. The same binary is therefore
transferred using bounded gzip transport inside the existing command; no
rebuild, image change, new VDP or Cloud write was performed.

### Live queued recovery and pending VDP18: passed

The corrected transport completed the authorized apply once: it restored only
`active -> slots/b`, retained installed17 and the pending-remove JSON, and
performed one SM stop/start. SM PID5538 initially became active with the exact
proof binary, Test demo timing, public inputs present, SELinux Enforcing and
zero fresh AVCs. The native recovery started the committed predecessor.

Native logs then show CM's existing target18 driving stop17 / start18, with
the slot-a payload self-test passing and version18 becoming active at
**01:44:55 UTC** (epoch microseconds 1789004695181778). This was approximately
three seconds after corrected SM startup at 01:44:52; no ten-minute delay,
batch approval, duplicate publication, new desired-status request, CM restart,
VM restart or reprovision was introduced by this repair. A stale launcher
start17 initially reported `a different component transaction is already
active`; CM reconciled its existing18 intent and the transition completed.
This is not a claim that historical/current-boot logs contain no errors.

`component status test` independently observed active slot **a**, version
**18.0.0**, PID5637, **23** configured read paths, matching process/slot,
`VDP data READY; source LIVE; reason NONE`, success and zero provider restarts.
The durable transaction is gone after native completion; installed.json now
records18/slot a. The retained last-failure record concerns historical16 and
was not deleted or presented as a current18 failure. The capability digest is
`ef96d8e18c018daf6dba9f6a928ace0a9a1a6c9ea96cd37810c2461fc483fb09`.
This remains provider-reported readiness, not Brake/Tire consumer qualification;
advisory is still DEFERRED.

At **01:45:49 UTC**, `component cloud-status 18.0.0` independently reports the
same Test Online, installed version UUID `9c2165e9-ff2f-40a4-8c5c-ab134d32a1b8`,
with pending component, pending error and validation batch all null. Current
CM, SM and VDP services are active, successful and show zero automatic restarts.
Factory bytes, Unit identity, Production and all existing Cloud releases are
preserved. New Studio UI and real Brake/Tire E2E remain open in the P1–P8 plan.

The explicit idempotent `sm-apply test` repeat returned noOp with the same
SM PID5538, NRestarts0, active slot a and unchanged proof hash. It issued no
second stop/start; the final audit still has a complete window, zero fresh
AVCs and Enforcing mode. The 78 component fixtures were rerun after the
transport adjustment and passed.

## Earlier continuation — functional Test cycle, paused at user request

The user granted standing publication authority for the agreed Test-cycle
VDP/Brake/Tire artifacts and the agreed public source repositories. Routine
release uploads no longer require a separate question. This does not authorize
Production mutation, new access grants or bypassing execution safety review.
The user subsequently deferred native Driving Control/telemetry visual alignment
until the functional chain works. No UI/mockup or native visual change was made.

### Confirmed live results

- VDP v1 **16.0.0** was uploaded through Demo Control, deployment
  `430e27ba-dfac-49e7-93d7-e36712a23f18`, then independently observed Ready.
  No batch approval or duplicate upload was used.
- The already running, locally connected fresh `.31` Test was provisioned in
  39.24 seconds, without a source reset or SM restart. Current Unit is
  `2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, system UID
  `d53d05cd4c4649c9a896534b23b88273`, Node
  `7dc03f51-539b-4a8c-bb33-5a8bb7290e6f`. Cloud Online and Test Vehicles
  membership were confirmed. Production was preserved.
- During native Autopilot, independent Controller observation showed
  19.37 km/h while first installation waited for Safe Stop. Native Safe Stop
  then installed **16.0.0**, slot a, PID 5035, seven read paths, READY/LIVE,
  matching process/slot and zero restarts, at 22:37:14 UTC.
- VDP v2 **17.0.0** was prepared, signed and uploaded once, deployment
  `7352f437-a05d-47fb-885d-335ffeaa9a14`. Cloud Ready and pending Test delivery
  were confirmed while v1 remained active during driving. Signed SHA256:
  `98f2841aa4241c55464b63df5c5455057da28510d6862eac58fb0fa275bfa76f`.
- VDP v3 **18.0.0** is prepared and signed, **not uploaded**. Signed SHA256:
  `6953945c3d0dac8efcdc6fcf85bb0122b47d9bec63e76eb57ffb74bd736033ae`.
  Do not publish it to work around the unfinished v2 transition.

### Preserved failure and next diagnostic boundary

Native Safe Stop for v2 is confirmed by fresh SAFE_STOP/STABLE, zero speed,
zero accelerator, full brake and advancing coherent VISS frames. However SM
retains the remove transaction for 16.0.0 in `waiting-for-safe-stop`. A
`safe_stop_timeout` was recorded and the native framework began another stop
attempt; Demo Control did not issue a retry. VDP16 remains active and READY.
SM PID 4412, binary SHA256
`df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86`,
effective `demo-5s`, initialized Test role, exact public binding and zero fresh
AVC denials were confirmed. No clock adjustment, guest binary replacement,
VM/SM restart or speculative publication was performed.

The existing read-only `component sm-status` now exposes bounded wait-channel
and resource counts, without argv, environment, descriptor targets or memory.
The existing `component diagnose` records each snapshot's acquisition time
and elapsed time. Six runtime-boundary tests and five probe tests pass.
One observed snapshot was 14 ms in the future at acquisition, which the pinned
Safe Stop evaluator rejects even under `demo-5s`. Another read obtained its
first TLS snapshot in 5.187 ms with positive age. These are root network probe
observations, **not an SM evaluator trace**; they do not prove the sole cause.
The earlier approved age exception explicitly preserves future rejection.
Do not silently broaden it or claim a clock fix.

Next: if still needed after resumption, reproduce the exact SM acquisition
sequence read-only (new TLS connection per frame, 250 ms total read deadline,
ten coherent facts, twelve distinct-frame window and immediate refresh).
Native code currently discards both ReadFrame errors and evaluator reasons,
so existing logs alone cannot distinguish them. Preserve this attempt rather
than rebuilding/reprovisioning or allocating another release. Only after v2
actually completes may v3 publication and Park/Resume qualification continue.

A proposed live Park-refusal test was rejected before execution by safety
review; it was not bypassed. The subsequent explicit user request to park for
closing the computer is handled through the standard `environment park` and
its actual result must be recorded below. UI remains unbound: 64516 serves
mockup 2.8; 18080 serves the previous Presenter. P3 and later phases are open.

At the explicit pause request, `environment park` returned **BLOCKED** with
`DEMO_COMPONENT_UPDATE_PENDING_OR_FAILED`, before stopping any process. The
earlier mistaken `demo park` spelling was rejected by argument parsing and
made no change. Work is paused, but this is **not a powered-off environment**:
the simulator, Test/Production VMs and backend processes remain running.
No guard bypass was attempted. Stopping despite the unfinished update needs
explicit operator direction; all disks and Cloud identities remain preserved.

Independent Brake work adds local commit `b6ba7a2` after `4434082` in
`/private/tmp/brake-growing-window-fmQtdV`: all-five-kind ACK retention and
accepted POST-to-ACTIVE retrigger corrections. Four CTest targets, quality and
boundary tests passed; main Brake checkout, Docker and live services were not
changed. Its runtime wiring audit identifies unresolved v2/v3 executable
integration and old schemas/validators restricting service release versions.
No P5/P6 completion is claimed. GitHub authentication remains unresolved as
recorded in the preceding checkpoint; no new source push succeeded.

## Earlier continuation — Docker recovery and Brake source publication

The user explicitly authorized one Docker Desktop restart with temporary
interruption/restoration of the five existing `watt-the-app` containers, without
data deletion, and publication of Brake Service commit `3ad5b23` to the public
`alexmaninblack/brake-health-service` branch `codex/studio-brake-runtime`.
That source push completed without force. No compiled artifact was published.

`democtl backend recover-file-sharing --restart-project watt-the-app` performed
exactly one engine restart. All five original containers were restored with the
same container IDs, image IDs and data mounts; previously healthy containers
were checked healthy. A mount-array ordering difference initially prevented
confirmation of the API container. Read-only reconciliation proved the mount
sets identical; comparing by destination resolved that observation defect.
Resuming recovery did not restart Docker again. No Watt container or volume was
deleted, recreated or pruned, and no QEMU guest was restarted by this operation.
The 23 backend regression tests pass, including five-container restoration,
unordered equivalent mounts, foreign-container refusal and once-only restart.

The exact context file is no longer held open. Resuming `democtl demo retire`
completed local old-Test context/overlay removal without repeating the already
completed Cloud deprovision/delete steps. Production's Unit, overlay and shared
factory/DNS resources were preserved. A fresh Test overlay was subsequently
created from the same immutable `.31` image. Its native password prompt could
not be automated under the host's accessibility permissions; that prompt alone
was cancelled and the existing `democtl vm start test` terminal input path was
used. This is not a new image build or an alternate VM-management helper.
Fresh Test qualification and P3–P8 remain open.

### Fresh Test startup findings

Fresh Test boot/SSH/DNS completed in 63.43 seconds, followed by both backend
process starts. CARLA Controller startup initially failed with `std::exception`.
A fixed owned-call-site diagnostic localized the native failure to
`client.get_trafficmanager(8000)`. Read-only listener evidence confirmed Docker
owned that port. A subsequent attempt encountered the actor left in that
failed scene. The owned scene was stopped through Demo Control, without VM or
Watt restarts. Using the dedicated demo TM port `18000` then started the real
CARLA/Controller/Gateway/native telemetry group successfully. Layout placement
completed; operator visual approval is still pending.

The first pre-Provision source connection exposed an old requirement for
Cloud `unitId`/`nodeId`. The agreed ordering now stages public local TLS trust
only before Provision; real SM/VDP identity binding is performed after
provisioning and before verification membership. The actual initial connection
passed: fresh completed Manual frame, full brake, advancing TLS/VISS frames,
Test gate OPEN and Production gate BLOCKED. No provider runtime was claimed
before installation. Focused fixtures passed: 26 simulation, 16 source,
3 Factory source, 27 Unit and 9 native controller-tool tests. Live post-Provision
binding and OTA qualification remain the next gate.

### Publication gate — VDP v1 16.0.0

`democtl component prepare --profile v1` allocated **16.0.0**, preserving the
seven-signal functional profile from the pinned v1 baseline. Signing completed
with `VERIFIED_RS256` against the configured OEM signing certificate; signed
bundle SHA256 is
`073a58b5d4f6db8ee49bea1cbf5a35f47371e28bcf9d8cd1ced9b50c2c88ef25`.
The execution permission review rejected `component upload 16.0.0` **before
process creation**, requesting explicit authorization for that version and Aos
Cloud destination. No upload attempt started, no deployment ID exists for
this release, and no indirect route or automatic retry was used. The reserved
version and signed artifact are retained; do not allocate another release to
work around the gate. Provisioning has not begun because the accepted sequence
publishes before Provision. Fresh Test remains connected in stationary Manual.

The integrated Demo Control fixture suite passes **443 tests** in 63.519
seconds. Nine native Controller-tool tests pass, including non-secret native
failure call-site reporting. Runtime source checkpoint is `2fc57a9` on
`codex/studio-controller-startup-diagnostic` (local, not pushed). These results
do not close live post-Provision binding, OTA or the later service/UI phases.

Solution source checkpoints `4199321` and `c346345` are committed locally.
Publishing them to the already approved implementation branch failed before
authentication (`could not read Username`). The existing GitHub CLI account
check then reported an invalid token. No alternative credential search, login
or remote rewrite was attempted. GitHub authentication must be restored before
that push; the earlier confirmed Brake `3ad5b23` push is unaffected. The
Controller diagnostic branch remains local, and all pre-implementation return
points are preserved. No source push failure is treated as a successful remote
checkpoint.

Independent Brake source work produced local commit `4434082` on
`codex/brake-growing-window`: sealed PRE and full ACTIVE/POST chunks during
capture, durable ACK/restart handling and exact completion semantics. Four
host CTest targets (13 runtime groups), repository quality and two boundary
tests passed. That isolated source worktree is not integrated or pushed; the
main Brake checkout remains the published `3ad5b23`. No actual ARM64 service
build or service deployment has been qualified by this source result.

## Earlier continuation — three authorizations accepted

The user approved all three proposals listed below. Tire source branch
`codex/studio-tire-backend` was pushed to the public
`alexmaninblack/tire-health-cloud` repository. The accepted temporary authority
model now permits the existing SP for a distinct Tire service identity.
The Test-only read-only metadata/public-trust proof is authorized without a
Factory rebuild; it has not yet been applied to a guest.

The next cleanup attempt corrected dependency order: both exact owned stopped
backend containers were removed before context unlink. Their volume/network
storage and Production were preserved. The file remains held by Docker
Desktop's Virtual Machine process even after both mounts/containers disappear.
Read-only `democtl backend status brake` identifies that holder, and bounded
`backend recover-file-sharing` proved the same process owns Docker.raw.
Recovery refused **before restart** because five unrelated containers remain
running: `watt-the-app-admin-1`, `watt-the-app-tunnel-1`, `watt-the-app-api-1`,
`watt-the-app-db-1`, `watt-the-app-redis-1`. None was stopped or changed.
The exact open-handle check is not bypassed; Test overlay/context remain.

This matches the residual VirtioFS descriptor behavior reported in
[Docker's issue tracker](https://github.com/docker/desktop-feedback/issues/168).
The official [Docker Desktop restart operation](https://docs.docker.com/reference/cli/docker/desktop/restart/)
would interrupt those unrelated containers, so that action requires a separate
bounded authorization or their owner to make the engine idle. No engine
restart or Docker storage pruning has occurred.

Brake source `3ad5b23` adds a pinned Linux ARM64 product recipe and verified
export schema, not a built artifact. Demo Control now has a CLI-only
`service build brake` entry with real ELF/source/test-proof checks. Five build
adapter tests and 22 backend tests passed. The cleanup increment passed 28
backend retirement and 15 Test-environment tests. No actual product Docker
build, fresh Test, service assignment or new Cloud upload was started here.

The earlier sections are retained as timestamped progress history. Their
three outstanding authorization statements are superseded by this section;
the unrelated Docker workloads were the then-current live-cycle blocker,
subsequently resolved by the explicit authorization and recovery above.

## <a id="resumed-execution"></a>Resumed execution — 10 September, supersedes the initial gates below

The user authorized scoped current-Test deprovision/delete, owned data/overlay
removal and a fresh Test from the same `.31` image. Existing Production and
shared dependencies are preserved. Source branch publication was separately
authorized to the existing Solution, Brake Cloud and Brake Service GitHub
repositories, with no force-push or main-branch changes. The Tire repository
was created at `alexmaninblack/tire-health-cloud` and verified **public** after
the user's public-only repository rule. Its source push was rejected by
execution review because repository creation did not explicitly authorize that
source export. No alternate export was attempted; local work is unaffected.

- Docker is now available. Real `democtl backend build/start` succeeded for
  both teams. Tire image: `sha256:8dac4d0e6a40090010a0242082e907931a01cd66937ed60a35aef6f09ea22895`
  from `565c3da`. The updated Brake image is
  `sha256:48eb81d1caec2b2fa51207e3a3405b5ba83210ed315ae7ef042909ce41fb7966`
  from `6a5889d`. Explicit Brake stop/activation/start passed without deleting
  its database. Process health is not product qualification.
- Fresh OEM/SP access reads passed. Both profiles are valid; the visible
  service catalog contains three existing non-demo services under the one
  configured SP, and no Brake or Tire service. This proves usable access, not
  an agreed independent Tire authority mapping or permission to create roles.
- Test was observed external-connectivity **OFF** through the existing owned
  fault control. Host DNS answered; SSH and all three Aos daemons worked.
  There is no evidence requiring another image rebuild for DNS.
- Test-only retirement/recreation leaves Production, shared DNS and factory
  identity unchanged in fixtures. Full-story Create, Park/Resume and scoped
  Retire now use the shared application boundary. Cloud-only inventory is
  consulted before shutdown; an uncompleted/unknown update refuses before
  automatic Safe Stop. Quick preparation also starts both prepared backends
  and permits a preserved Production peer without provisioning that peer.
- Combined Demo Control suite passed **395 tests** (63.460 seconds) before
  the final retirement/Quick-preparation additions. Subsequent focused suites
  passed: backend lifecycle/activation 19, Studio lifecycle 16, Quick
  preparation 7, source handover 15, simulation 24, Brake Cloud contract 17.
  Scoped cleanup tests and later full-suite results are recorded at the next
  integration checkpoint; these fixtures are not a live E2E claim.
- Final integration checkpoint: **425 Demo Control tests passed** in 55.154
  seconds; Brake Cloud contract tests passed 17/17. Documentation validation
  passed for 165 Markdown documents, 658 stable identifiers and 38 diagrams;
  `git diff --check` passed. No live VM/Cloud action is implied by these fixture
  suites, including their mocked Builder progress output.
- Brake backend source `6a5889d`: 39 tests, compile/typecheck and quality
  gates passed. Private Test-scoped cleanup preserves nonmatching records;
  whole-store emptiness requires schema/integrity proof, not a missing UID.
- Brake service source `6fb8e02`: bootstrap and domain/input tests passed
  (4 CTest targets plus two repository-boundary tests). The real gRPC adapter
  exists in source but is **not yet compiled or deployable**. Pinned Linux
  ARM64 dependency assembly and authoritative service-visible metadata/public
  KUKSA TLS leaf delivery remain real integration work. No insecure fallback,
  guessed UID, private-key exposure or Factory rebuild was performed.

The real scoped `democtl demo retire` reached confirmed Test deprovisioning,
graceful VM shutdown and deletion of the Test Unit and its Node. Cloud steps
are recorded complete and must not be replayed. Brake's exact-Test record
counts are zero; Tire's result is foundation-only, not a product-data claim.
Both backend containers are stopped, their storage retained. Local cleanup is
**PARTIAL** at `retire-test-data-and-overlay`: `CLEANUP_FILE_IN_USE` while
removing the old current-Test context. Its removal receipt is `REMOVE_PENDING`.
The context and old Test overlay have not been declared removed. Do not
delete them outside Demo Control or weaken the open-handle check. No retirement
process remains running; the journal is the recovery authority.

The two preceding integration defects were corrected: the legacy journal's
known `workspace` field is preserved, and exact Docker Desktop `/host_mnt`
aliases are accepted for the owned read-only context bind on macOS only.
The cleanup regression suite passes 24 tests. These fixes do not override an
actual open handle or authorize removal of a foreign path.

Production's Unit identity, overlay and shared factory/DNS resources remain
outside the retirement target. Its current runtime/Cloud availability has not
been independently re-qualified by the cleanup result. No fresh Test was
created and no new VDP/service release was published in this resumed cycle.
P3–P8 and final visual acceptance are not complete.

### Current decisions needed for full service E2E

- Approve or supply the bounded platform-owned, read-only service metadata and
  public KUKSA TLS trust interface described in the delivery plan. Native
  service identity alone does not supply Unit role, artifact provenance or
  active VDP contract evidence. An exact proposal must identify the producer,
  fields, resource mapping and transient Test proof before any guest change;
  this is not permission for a Factory rebuild or broad service access.
- Establish the Tire publication binding: the accepted plan requires separate
  team-SP authority, but only one configured SP profile has been observed.
  Sharing that profile would amend the accepted authority model; no such
  amendment or credential creation is inferred.
- Explicit Tire source publication permission remains separate from creation
  of its public repository. The rejected source push was not retried.

ARM64 dependency assembly, service packaging, Brake/Tire product wiring and
the P4–P8 implementation remain engineering work even after these decisions.
There is no basis yet for promising a completed morning visual review.

The sections below preserve the initial checkpoint and its then-current
evidence; Docker, repository and cleanup-authority statements there are
historical, not current blockers.

## Return point and owned changes

The remote pre-implementation checkpoint remains
`pre-studio-implementation-2.8-2026-09-09`, Solution commit
`b997e6e6cffba02b61a588c40f14dba30942d17d`.
The implementation branch is `codex/demo-studio-implementation`; `main` was
not advanced. Source increments are isolated from Factory images and runtime data.

| Repository | Implemented source boundary | Local checkpoint |
| --- | --- | --- |
| `aosedge-sdv-demo` | Test-targeted preparation, initial Manual operation, release continuity, backend context/lifecycle primitives, Cloud-only reads, publication reconciliation, image support reader/producer | `619d107`, `755125d`, `f196a20`, `58a9116`, `eb25666`, `5b61970`, `bdee1b2`; later commits on the same branch contain metadata-only registration and this checkpoint |
| `brake-health-cloud` | Current Test context with optional Production, durable backend, private scoped cleanup, Docker recipe | `f55bd74` |
| `tire-health-cloud` | Independent process/SQLite/context foundation and Docker recipe, not product ingestion | `565c3da`; new local repository, no remote configured |
| `brake-health-service` | Host-tested Brake v1 composition and bounded transport primitives, not a deployable service executable | `dca3190` |
| `aos-vehicle-platform` | Unchanged | `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` |
| `carla-ego-runtime` | Unchanged | `f506e4b206725317c83346c4f46069235ca8f038` |

No image, bundle, executable, database, credential or temporary socket was
committed. No implementation branch was pushed: execution review denied the
push without explicit approval of the exact remote destination. No alternate
export route or force-push was attempted.

## Evidence actually obtained

- Full combined Demo Control suite with the metadata-only increment: **342 tests
  passed** in 57.910 seconds, using local fixtures, not a live VM/Cloud lifecycle.
  A final secondary-manifest conflict regression was subsequently added and the
  complete eight-test metadata suite passed again.
- Subsequent backend ownership/error tests: **10 passed**; context tests: **6
  passed**, including the non-secret read-only container export. Image/create/retire tests: **40 passed**, including the new
  declaration reader. Initial sandbox process-listing denials were resolved
  by running the same fixture suite with permitted process reads; product
  logic was not weakened.
- Eight Factory producer/migration tests and five unchanged runtime tests passed.
  The explicit metadata-only registration on .31 passed and an intentional
  repeat returned `noOp=true`. It registered 23 source-derived read paths,
  preserving image bytes, recorded SHA and qualification state; no Builder ran.
- Brake Cloud: 34 backend tests, four architecture groups, typecheck and
  source gates passed. Tire: four lifecycle groups passed. Brake service:
  three CTest targets (domain v1/v2 and seven runtime groups) passed.
- Confidential-input and documentation-quality gates passed at local commits.
- Actual `democtl unit cloud-status test` and `unit monitoring test` performed
  only bounded Cloud reads. At 2026-09-09 15:32 UTC, Cloud reported the current
  Test Offline, VDP **15.0.0 installed**, no service rows, and no resource
  samples. Missing samples remain unknown. This does not assert VDP Running.
- Actual `democtl component cloud-status 15.0.0` reconciled the recorded bundle
  as `done`, its exact catalog version as `Ready`, and publication as `READY`
  at 2026-09-09 16:07 UTC. The Unit remained Offline; no publication was replayed.
- Actual `democtl backend build brake` and `... tire` stopped before
  compilation. A subsequent `backend status brake` confirmed
  `BACKEND_DOCKER_ENGINE_UNAVAILABLE`; no container, volume or new image was
  created. Docker build/start/restart and guest-routing tests are not passed.
- Actual `democtl demo plan --image 6.1.1-maninblack.31/main-qemuarm64 --target
  test` returned the expected existing-role conflict. The old two-role run
  was not silently converted or destroyed.

## Live state deliberately preserved

The existing Test/Production run, Cloud identities, selected Test, simulator
assignment, overlay disks, factory copy and immutable source image remain.
No provisioning/deprovisioning/delete, source switch, Cloud upload, validation
approval, service assignment, VM restart or backend start was performed.

Factory `.31` remains SHA256
`a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4`.
Only its producer compatibility metadata was added through Demo Control;
`BUILT_NOT_LIVE_QUALIFIED` and the original image binding were retained.
No broad disk cleanup was performed. Existing Builder/cache and unrelated
CarlaSim scratch directories were preserved. Isolated source worktrees are
retained until their changes are integrated and qualified.

## Work that remains, not completion claims

| Phase | Current boundary |
| --- | --- |
| P1 | Source primitives and image registration implemented/tested; complete composed lifecycle, exact backend R0 and Docker live proof remain |
| P2 | Cloud inventory/monitoring and publication reconciliation integrated/fixture-tested; actual inventory and historical bundle reads passed; new live publication and Presenter observer remain |
| P3 | Not qualified: fresh Test CLI lifecycle, v1/v2/v3 transitions, Park/Resume and Retire still required |
| P4 | Not started: no new UI bound before P3 passes |
| P5 | Not deployable: Brake product process/bootstrap, KUKSA adapter and authoritative runtime bindings are incomplete |
| P6–P7 | Product advisory chain and real Tire algorithm/service/backend remain unimplemented |
| P8 | Not started: no full fresh-run/repeat/visual acceptance or final housekeeping claim |

## Bounded decisions before the next live stage

1. **Make Docker engine available.** The accepted startup preflight fails
   closed; this increment does not silently start Docker Desktop or substitute
   native backend processes.
2. **Resolve the pre-existing two-role run.** The new Test-only default cannot
   assume permission to delete the preserved Production VM/Unit. Select an
   explicitly authorized migration/retirement scope before the fresh P3 run.
3. **Close service runtime bindings.** Native IAM provides Unit system identity,
   but `.31` has no accepted service-visible combination of role, service
   artifact provenance, active VDP contract/digest and KUKSA public TLS trust.
   See the evidence table in the delivery plan. A read-only, platform-owned
   metadata/trust resource is a proposed bounded interface change, not an
   implemented or approved fallback. Do not bake a current Unit UID into a
   reusable package, substitute expected VDP metadata for active state, disable
   TLS, expose private keys or rebuild the Factory image implicitly.
4. **Bind Tire SP authority.** Only one configured SP credential/profile was
   observed. Independent Tire publication authority is not established; no
   credential/role creation or Brake-profile reuse has been assumed.
5. **Approve exact remote publication destinations when resuming push.** Local
   source commits exist, but sending repository contents remains blocked by
   execution review; the new Tire repository also needs an approved remote.

These are separate from ordinary remaining source tasks. Docker availability
alone would not make the unfinished product stages or full demo qualified.
