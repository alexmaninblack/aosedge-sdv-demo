<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore mainline migration — 23 September 2026

Status: authorized by the operator; source/native/package/image gates and
isolated .37 boot/repeat complete. Live replacement is not qualified yet.
See the [Factory .37 qualification report](../../qualification/factory-37-mainline-build-2026-09-23.md).

Current continuation (24September12:16UTC): diagnostic/security stage closed
for constructing successor **.38 candidate**. SM/KAC corrections have live
functional/negative/rollback proof; seven optional VDP probes remain denied
with exact tested audit exclusions. Temporary core capture was explicitly
disabled and removed without a captured dump. Historical109 SIGSEGV remains
unresolved/not reproduced, not claimed fixed. Preserve the .37 Test and .36/.37
images until successor qualification; stop the next live run on recurrence.
The detailed current closure is at the end of the
[live report](../../qualification/factory-37-staging-e2e-2026-09-23.md).
Historical progress entries below retain their original time-scoped status.
Successor [Factory .38 build packet](../../qualification/factory-38-build-2026-09-24.md)
pins Platform378c00ef and retains the full native/package/image/offline/live gates.

## Decision and immutable inputs

Use a coordinated mainline baseline rather than an isolated UID-pool backport.
Fresh official main refs were resolved on 23 September:

| Input | Commit |
| --- | --- |
| aos_core_cpp | `9d613a46df3c7f550062e2f19ae3406c57715694` |
| aos_core_lib_cpp | `5560291ba6914e36a5b841ade4d8fc54134a9e91` (v9.1.2) |
| aos_core_api | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` |

Do not follow floating main/develop refs during the build. Keep the existing
Yocto/toolchain baseline unless a demonstrated compatibility requirement needs
a separately recorded change. Upgrade CM, SM and IAM together, including their
private library dependencies; do not leave IAM or KUKSA integration linked to
an incompatible header/library pair.

## Preservation and ownership

- Preserve Factory .36, its immutable manifest, current Test/Cloud identity,
  storage and diagnostic evidence. No in-place repair, restart or cleanup is
  implied by this work packet.
- Source changes belong to `aos-vehicle-platform`; build orchestration and
  solution evidence belong to `aosedge-sdv-demo`. Application services, models,
  thresholds, CARLA, Presenter semantics and the video repository are outside
  this migration.
- First prove changes in `/private/tmp/aos-mainline-migration-20260923.A2qEwO`.
  Compile only affected native targets with no network and no live mounts.
  Consolidate recipe patches only after their local proof passes.
- Reuse the warm Builder/caches and require the existing disk/build guards.
  New package publication, provisioning and irreversible Finish retain their
  exact target/action authorization gates.

## Patch disposition to verify

The [19 September audit](../../qualification/aoscore-mainline-sync-and-patch-audit-2026-09-19.md)
and [23 September UID diagnosis](../../qualification/demo-v1.0-ui-e2e-2026-09-23.md)
are the starting evidence, not blanket permission to remove residual fixes.

1. Omit the duplicate shared-gRPC-write backport; retain its regression.
2. Retain only residual node-snapshot validation; upstream owns desired-version
   reconciliation. Retain startup-rebalance and idle-full-status behavior until
   equivalent tests prove it redundant.
3. Port disconnect notification discipline and final-owner storage retention.
   Preserve upstream stable UID/reference counting. Failure/retry must not
   release another version's UID or destroy surviving data.
4. Adapt the VDP systemd-slot runtime to allocator/InitInstances interfaces,
   preserving explicit Safe Stop, durable recovery and truthful statuses.
5. Re-evaluate SM teardown/replacement/reprepare patches against new lifecycle
   phases; remove only behavior proved superseded.
6. Keep permission key capacity256 and IAM permission-reply capacity correction.
   Update PKCS#11 checks for the injected allocator without weakening the
   three-session-key topology or renewal checks.

## Ordered gates

| Gate | Scope | State |
| --- | --- | --- |
| M0 | Source/recipe inventory, upstream pins, preserve existing baseline | Complete |
| M1 | Negative-control regressions and minimal adaptations in isolated source | Complete |
| M2 | CM/SM/IAM and VDP native tests; permission, storage, UID and disconnect regressions; source/license gates | Complete; live quota/image checks remain M4 |
| M3 | Commit pinned source, affected package tests/QA, one successor Factory build | Complete; .37 frozen, offline boot/repeat checked |
| M4 | Clean Test installation and sequential E2E with UI observation | Sequential VDP112→113→114, Brake87→88→89 and Tire48 installation proved under an authorized temporary SM/KAC candidate. Stable Brake UID/storage/quotas and Cloud metrics survive upgrades; VDP114 waits for actual Safe Stop. Both real advisory paths, independent UI Reset/CLEAR/history retention, Return to road and subsequent Autopilot/Safe Stop pass. A separate KAC-only proof passes five-minute OFF with local Brake/Tire inference, applied advisory, token renewal, stopped backend ingress, then queued delivery and Online recovery after ON, with no workload restart. Original policy restored at11:03UTC. Cold persistence, crash/security closure, permanent image integration and final Finish remain open |

M4 must publish each next VDP/Brake version only after the preceding version is
installed and verified. VDP uses Safe Stop; QM service updates remain independent
of that gate. Check persisted analytics/outbox, resource metrics, local advisory
and authorization during external network OFF, stopped backend ingress, queued
delivery and Online recovery after ON, and owned-Test Finish. Startup alone does
not qualify this migration. Do not claim a fresh-image proof repairs legacy
records with mismatched UIDs in the preserved Test.

Record executed tests and exclusions before advancing a gate. No image build
while any required native test is failing.

The [live .37 report](../../qualification/factory-37-staging-e2e-2026-09-23.md)
records two open migration defects: premature VDP active reporting and the new
crun executable's SELinux-domain mismatch for the KAC resource mount. Preserve
the failing .37 Test and its authorized publications; no later release is
uploaded and no new image is built until the rapid-debug gates close. The
authorized directory-only temporary policy proof passed: stock fails, one
`getattr/search` rule permits the isolated mount and `/bin/true`, and rollback
reproduces the failure. Canonical policy and all managers are unchanged;
SELinux remains Enforcing and the broad container-mount boolean remains off.
The separately authorized socket proof also passed: under UID5000 and the
actual new container_engine_t context, two status requests and an invalid
request behave correctly, including a rate-limited repeat and negative
rollback controls. Only two precise socket rules were added to the previous
directory candidate during the <=240second proof; stock policy was restored.
Real Brake/token/telemetry remains unqualified. The source cause is upstream
`9c8a27ec` switching in-process libcrun to the crun executable without our
Factory KAC policy being adapted to its SELinux domain. The live report also
records a separate VDP SEGV at03:43UTC on24September, before the socket tests;
its cause remains open and must not be attributed to those tests.

Follow-up24September found a second VDP SEGV at07:04:03UTC. Both occur about
0.5seconds after a non-monotonic VISS-frame/reconnect warning. Neither a native
stack nor causation by the AosCore upgrade is established. Core output was
disabled at that investigation (`|/bin/false`); subsequently authorized temporary
capture is recorded below. Preserve the separate diagnostic gate;
do not describe the crash as fixed by reducing reconnects alone.

The same audit proved a distinct packaging gap:109/V1 replays the old1.0.16
runtime byte-for-byte. Current common duplicate-frame/readiness-log fixes reach
only the reviewed V3 overlay; V1/V2 still replay old functional code. Before
the next full sequential qualification, carry reviewed common fixes into all
three new profiles while preserving their7/15/23 signal sets, V3-only advisory,
Safe Stop, strict freshness/trust and historical immutable release inspection.
Do not alter published109 or silently replace reserved110/111. Native crash
localization and new payload source qualification precede signing/publication.
The live report records isolated synthetic probe results and their exclusions;
passing transport loops or15 current-source readiness tests do not qualify
the installed VDP or close M4 stability.

## Regression origin and prevention —24 September continuation

The live report now records immutable .36/.37 comparison, not just symptoms:
app9c8a27ec changes libcrun-in-SM to a crun executable and its Factory SELinux
domain, while our KAC/refpolicy/resource integration was unchanged. This missed
migration adaptation affects both service bootstraps. Lib9eb7d42e separately
forces Active after successful asynchronous StartInstance; old lib60cb8353
preserved returned runtime status. Safe Stop stayed enforced; reporting was early.

The V1/V2 common-source packaging gap predates migration (solutionf21476f,
20September). None of those findings proves the native VDP SIGSEGV cause.
At11:23:48 current114 is READY/LIVE,0restarts,70m21s continuous, no core;
restricted capture and its removal checklist remain open.

Historical-policy negative controls reject both old policies for the *new*
runner contract and accept the corrected tree. Platform199passed/2skipped and
component154passed/3skipped; source/license/secret gate passes242tracked files.
Migration gates must check effective crun identity plus KAC renewal,
asynchronous runtime status and common code in every prepared profile, not
assume compilation/native mocks/unprovisioned boot cover these live boundaries.
No new Factory build before the existing crash/security gates are classified;
no live mutation, commit/push or permanent-policy activation in this audit.

## Native proof progress (23 September)

### Temporary VDP crash capture — mandatory removal gate (24 September)

Operator authorized a VDP-only core capture and current-runtime V1/V2/V3
preparation. Never include crash collection in a Factory image or release.

- [x] Arm and verify guest-local `/run/factory37-vdp-core`, root-only0700/0600;
  one dump, max256MiB uncompressed/64MiB compressed,20second receiver deadline.
  Filter UID998, exact VDP systemd cgroup, Python executable and SELinux domain;
  discard every other process. No raw dump, credentials or memory in Git/logs.
- [x] Restore original `kernel.core_pattern=|/bin/false` and
  `kernel.core_pipe_limit=0` after capture/diagnosis; automatic one-shot and
  24hour expiry are backstops, not substitutes for this explicit check.
- [x] No real core was captured; analysis is not applicable, native cause stays
  unresolved. If a later core is captured, analyze only restricted local core;
  report function/line-only backtrace,
  never arguments/locals/environment. Delete the exact raw diagnostic dump
  when diagnosis is complete; retain only sanitized cause/test evidence.
- [x] Remove the transient collector/timer and verify no debug configuration
  entered published VDP or Factory. Restore any temporary source overlays.
- [x] New V1/V2 contain the reviewed current common runtime, with7/15
  signals and no advisory; V3 keeps23 signals and its reviewed advisory.
  Preserve existing release bytes and inspect historical releases unchanged.

Capture is armed with unchanged real VDP PID71204/NRestarts2. Synthetic core
proof passed and its exact disposable dump was removed. Rollback command in
the guest: `python3 -I /run/factory37-vdp-core/collector.py disable`.
The transient `factory37-vdp-core-expiry.timer` is the24hour backstop.
VDP112/V1 was prepared, inspected, explicitly authorized, signed and published
once to staging. Actual installation08:09:03UTC:slot b,PID142419,7paths,
READY/LIVE,0 restarts. Its common runtime hash matches1fe5649; managers remain
unchanged. Core capture remains armed for the new VDP process, no core yet.
162 component tests passed,3 crypto-environment tests skipped; ARM64 synthetic
112 runtime completed194 mTLS/gRPC reconnect cycles in80seconds without SEGV.
Neither result establishes the cause or repair of the earlier native crashes.
Full orchestrator regression:1023 passed/16 skipped; documentation gate passes.

The live report records whether capture is actually armed and proof results.
This checklist is a required M4 closure item, not optional housekeeping.

24September08:30–08:41UTC continuation: one CM-only restart and the exact
three-rule candidate started native Brake87 without changing SM/IAM/KAC/VDP
PIDs. Standard public-input preparation resolved the bootstrap WAITING stage;
the existing .37 run had no metadata projection. A150-second no-restart proof
then completed KAC/KUKSA/backend operation and two V1 windows, one from the
standard CARLA braking maneuver. Stock policy was restored after every proof.
The platform source now contains only that three-rule integration correction;
26 targeted tests and198 platform tests pass (2 skipped). No new image or upload.
VDP112 remains READY/LIVE with0 restarts after32minutes; core capture remains
armed. Separate getsched AVCs and rejected mixed-timestamp inputs are recorded,
not silently fixed or included in the KAC grant. Investigate public-input startup
projection, correct SM async status, and keep these diagnostic exclusions before
the next build/sequential qualification. UI's failed-as-pending count is also
recorded separately; the fresh inventory now reports no pending update.

24September09:37UTC continuation: the SM-only production-toolchain candidate is
built and staged inactive in the preserved Test; no live replacement, restart or
policy load was attempted. The execution safety review requires explicit approval
for that bounded replacement plus the previously proved KAC-policy window; this
was requested from the operator. Complete that live gate before further deployment.
VDP112 remainsPID142419, READY/LIVE, NRestarts0 after88minutes17seconds, without
reconnect, stale transition, SEGV or core. The independent same-domain gRPC probe
passes10/10 synthetic RPCs despite the reproduced scheduler/bind denials; no new
permission or audit suppression was added. These observations do not close the
crash/security gate or substitute for sequential updates and network OFF/ON.

24September09:44–09:55UTC continuation: after exact operator confirmation, the
production-toolchain SM candidate ran on the preserved Test under the proved
three-rule KAC-policy candidate. First start and explicit repeat restart passed;
automatic rollback protection remained armed until verified restoration. Stock
SM is nowPID155513; original binary, canonical policy store and active stock
policy are unchanged, and the ExecStart override is removed. VDP112PID142419,
IAM1795, CM145206 and KAC2232 did not restart. Brake87 reached CONNECTED/RECEIVING,
Cloud remained Online with112 installed and87 active, no pending versions.
No KAC/container/VDP AVC occurred in that bounded interval; separate generator/
SSH denials remain recorded, so this is not a whole-system security acceptance.

All three SM starts ran the public-input cold/verify hooks successfully without
rewriting the existing08:35 metadata. This closes the warm-restart question,
not cold boot or next-version recovery. VDP112 was READY/LIVE with0restarts and
no core after99minutes53seconds at09:48:56UTC; capture remains armed. Native
32/32 launcher tests and this same-version live start/repeat do not substitute
for a real new-version Safe Stop/status transition.

Fresh unsigned113/V2 and114/V3 use the reviewed current runtime tree
`cfc2e0c790c179ddc10f734f0def0361535154c0`. Inspection passes with15/23 read paths
and0/2 advisory endpoints respectively; no signing/upload/installation occurred.
Historical110/111 remain unchanged and excluded from the next run. Baseline
Brake87 UID5000 has numeric state/storage quotas and fresh Cloud CPU/RAM/disk
rows. Record that baseline before88/89; same-version success is not proof of
the upstream stable-UID upgrade correction. The live report contains digests,
read times, rollback evidence and the next exact authorization boundary.

24September10:06–10:27UTC continuation supersedes the unsigned-candidate gate
above. Exact authorization covered113/114 publication and a maximum90minute
transient SM/KAC window, protected by an independent guest rollback watchdog.
Each release was signed, uploaded, reconciled and checked before the next one:
113/V2, Brake88/V2,114/V3, Brake89/V3, then Tire48/V1 and its dedicated assignment.
While CARLA was moving19.4km/h,114 remained pending and113 remained installed;
native Safe Stop then installed114. Both ordinary public-input prepare checks
were no-ops, verifying existing metadata rather than recreating it.

Brake retained UID5000, state inode64772 and storage inode15 across87/88/89,
with numeric quotas and fresh CPU/RAM/disk samples after each upgrade. Tire
uses UID5001 with its own quotas. Real CARLA maneuvers produced new backend
assessments and Gateway APPLIED recommendations for both services. Separately
approved UI Reset actions confirmed CLEAR at10:25:48/10:26:31UTC; resetting
Brake left Tire's warning unchanged, and both histories remained intact.
Return to road completed in stationary Manual, with both advisories Monitoring.
The subsequent Autopilot action and the earlier five-minute network OFF test
were rejected by execution safety review before execution; exact confirmations
are pending. Do not count either as passed. Transient reauthentication readiness
changes remain visible in fixed diagnostics and are not hidden by this result.
No new image, Production operation, cleanup, commit or push occurred. Consult
the live report for the final temporary-patch rollback and remaining boundaries.

At10:31UTC the lease was explicitly ended: stock SM/policy verified restored,
canonical policy store and original binary unchanged, transient drop-in removed,
Enforcing retained. VDP/CM/IAM/KAC PIDs did not change. Both service containers
restarted normally with SM and retained their histories. At10:32, Cloud remains
Online with114/89/48, no pending versions; native UI is stationary Manual with
both advisories Monitoring. Stock KAC restrictions are again in force, so this
does not claim permanent fix deployment or close future renewal/cold-start gates.

24September10:35–10:43UTC: post-return Autopilot driving (19.2km/h observed)
and Safe Stop passed. With stock policy retained, both bootstrap processes hit
KAC directory-search denials at10:34:14 and lost authorization at10:36:14,
before external networkOFF. The five-minute OFF/ON control check nevertheless
returned the same Unit Online at10:42:51 without any manager/provider/service
restart, and backend transport resumed. Do not mistake this for a local
offline-inference pass. A new maximum20minute, automatically rolled-back
three-rule KAC-only window was requested; no SM replacement or restart is
needed for that next proof. Network is ON and CARLA remains in Safe Stop.

24September10:51–11:03UTC supersedes the pending KAC-only gate above. Exact
operator approval covered only the three existing rules, maximum20minutes,
with automatic rollback. SM stayed stock; no manager, provider or service
restarted. Both services recovered before OFF. External network was OFF by
10:52:40, ON was invoked once at10:57:57, and Cloud reported the same Unit
ONLINE at10:58:42. Both native maneuvers completed while OFF and produced
new local assessments plus Gateway APPLIED warnings; both advisories visibly
showed Inspection recommended while offline. Token replacement/reauthentication
also occurred offline and recovered without Cloud.

Backend heads and result counts stayed fixed during OFF. Brake/Tire outboxes
grew to11/15files and were empty at10:58:44 after ON. Brake assessments3→5
and Tire3→4 retain original source times and distinct10:58 receipt times;
repeated metadata reads show no duplicate assessment/event IDs. Presenter and
native UI agree on the new recommendations, Online and networkON. No KAC
denial occurred during the temporary-policy interval. Brief readiness changes,
VDP getsched/SSH denials and the historical VDP SEGV remain explicit exclusions;
this is not a30minute RabbitMQ or uninterrupted-readiness qualification.

The lease ended early at11:03:10.917UTC; restoration receipt11:03:11.964
confirms stock policy, unchanged stock SM/canonical store, Enforcing and
unchanged manager PIDs. Network staysON, vehicle Safe Stop, diagnostic Test
preserved. Stock KAC restrictions will affect later renewals again: the fix
has source/live proof, not permanent Factory deployment. The separate bounded
VDP core-capture/removal checklist remains open. No image, publication,
Production change, retirement, cleanup, commit or push in this continuation.

At11:07 the expected rollback-negative state is confirmed: Tire/Brake again
report KUKSA_AUTH_PENDING from11:05:47/11:05:59 with fresh client search denials,
while VDP stays READY/LIVE and Cloud ONLINE, all PIDs unchanged. Current local
analytics must not be presented as permanently repaired. KAC/mainline16/16,
documentation and both repository whitespace gates pass after the evidence update.

- Unmodified main library plus adapted shared-storage regressions: 26/43 pass,
  17 fail. The storage adaptation restores 43/43; extended CM launcher suite
  now passes 47/47, including upstream stable-UID updates and failure ownership.
- An additional negative control exposed an unsuccessful legacy-UID acquire
  followed by cleanup releasing a surviving version's UID reference. Track
  successful UID/GID acquisition explicitly before release. This is a residual
  migration patch, not an assertion that pristine main already fixes it.
- Idle full status: 11/11 native tests pass after allocator API adaptation.
- SM startup now adopts persisted instances rather than executing installation
  preparation. Adapt the old retry fixture to a new install and wait for startup
  completion. The corrected negative control passes 20/25, fails 5. The candidate
  passes 27/27, adding failed network-stop/batch and successful retry checks.
  Retain failed teardown ownership, its durable record and image; never clear it
  while preparing a replacement. Network release precedes durable-row removal.
- CM, IAM and SM application binaries compile against the pinned triplet. SM
  native proof includes container and VDP; boot/rootfs targets remain the package
  gate. VDP:81 pass/2 VM-only tests skipped; container42 pass/2 upstream-disabled; actual crun adapter
  with injected error returns5/5; network93/93; namespace4/4; IAM gRPC61/61;
  permission handler7/7; storage/state15/15; CM lock harness17/17; PKCS#11 with
  three real SoftHSM tokens14/14. Cache reset/reopen covers20 cycles with a
  retained old session. No product capability or authorization was widened.
- Platform source is consolidated on `codex/aoscore-mainline-20260923`; all three
  recipes select the triplet above. Obsolete patches are removed or consolidated,
  with mapping in the platform migration document. Reconstructing each recipe
  from pristine pinned Git objects matches the native-proof files byte-for-byte.
  Platform Python regressions198/198; source/license gate passes. Factory .36 and
  current Test are unchanged. Builder is started only for package qualification.
- Native test environment uses disposable Linux ARM64 containers. Debian 12's
  OpenSSL 3.0 lacks `BN_signed_bin2bn`; build the application's declared OpenSSL
  3.2.1 (`a7e992847de83aa36be0c399c89db3fb827b0be2`) only in the proof directory.
  Host/VM libraries and production toolchain are unchanged. Debug/`-O3` with GCC12
  hit upstream stack/string diagnostics; `-O2` (RelWithDebInfo) builds the native
  lifecycle tests without suppressing warnings. Production package gate remains
  required. Crypto-free lifecycle tests do not count as crypto qualification.

Compact XML/log evidence remains alongside the isolated source. A test-harness
startup assertion left one disposable negative-control container running; that
exact container was stopped and the fixture corrected. No demo container, Test,
Cloud object, current Factory, or video artifact was changed.

## Source checkpoint and package gate

- Platform source checkpoint: `28454adaad54b8d1797aa912f3e50246b1b63042`.
  Candidate .37 offline specification: `77d99770a3d9476736da55c3e2196396899bc563`.
  Both are local commits on `codex/aoscore-mainline-20260923`, not an accepted
  deployed baseline and not pushed yet. No `.36` bytes or accepted solution pin
  changed.
- The first package attempt was rejected: a post-read BitBake override changed
  the displayed layer list too late to select the new recipes. Actual source
  inspection still found the legacy app pin in all three builds. No image was
  built; the attempt is not qualification. Shut down only the isolated Builder
  cleanly, retain logs/caches, bind the layer before parsing, and check effective
  pins for all managers before the corrected compile attempt.
- Builder access now uses the existing Demo Control adapter and dedicated10024
  port. The first start used the standalone script's legacy10023 default on the
  same Builder disk; no Production VM or Test was connected or mutated.
  Compiler concurrency is bounded to two tasks with four compiler jobs each
  while the current demo remains available.

## Production-toolchain closure and Factory .37 build gate

- Corrected compile resolved all three actual app/lib/API checkouts and CMake
  bindings to the pinned triplet. All1743 compile tasks succeeded. SM includes
  boot, rootfs, container and VDP runtimes; production OpenSSL3.2.6 is unchanged.
- Native checks using each recipe's compiler and target sysroot passed:
  CM launcher/UID47, idle11, storage15; SM replacement27; IAM permissions7,
  three-token PKCS#11 cache14 and gRPC61; VDP81 (2 VM-only skips), container42
  (2 upstream-disabled host-device tests), crun5, network97; CM lock17.
  Total:424 passed,2 skipped,2 upstream-disabled; KAC/provider/verifier programs
  also exited0. Core tests use upstream fixture configuration, not a duplicate
  application configuration header. Application flags are checked separately.
- Two evidence-harness corrections did not change product code: retain
  root-owned synthetic storage fixtures instead of failing unprivileged cleanup;
  count42 executed container cases separately from2 disabled upstream cases.
  Reconcile existing XML instead of rerunning a successful uncertain attempt.
- Package/QA completed all6484 tasks,59 executed. Nine nonfatal `buildpaths`
  warnings refer to paths of the private upstream library sources in manager,
  debug and staticdev packages. This known category is also recorded for earlier
  Factory releases; no warning/error checks were disabled. Package dependencies
  also refreshed the initramfs/kernel deploy output; no Factory disk or
  `aos-image-vm` was built by that package command.
- Packaged IAM retains enabled permissions and exactly the aoscloud/aoscore/
  aos-kuksa token topology. No identity, permissions or trust scope was widened.
- Demo Control .37 pins Platform `77d99770a3d9476736da55c3e2196396899bc563`.
  Its committed qualification helper checks effective pins before compile,
  checks actual sources/flags after compile, executes the matrix above before
  packaging/image construction, and preserves compact XML/logs in the image
  artifact. Old .35/.36 build paths and expected counts remain unchanged.
  Tooling must be committed and clean; retries cannot overwrite evidence.
- Demo Control regression:1035 cases,1019 passed and16 skipped in the project
  environment. The initial sandboxed run is excluded:28 local socket/process
  permission errors plus a historical fixture expecting the old rejection
  boundary. Preserve that .36 fixture and add the mainline rejection separately;
  no product guard was loosened. Focused Factory tests33/33, permission tests15/15.
- Keep two BitBake tasks/four compiler jobs and the60GiB disk guards. The new
  image remains `BUILT_NOT_LIVE_QUALIFIED` until a clean isolated smoke and the
  separately authorized sequential staging matrix pass. The accepted solution
  platform pin, immutable .36, current Test and video repository remain unchanged.

Compact evidence is retained in the transient proof directory, particularly
`production-compile-v3.log`, `production-native-v2.log` through
`production-native-v4.log`, `production-lock.log`, `production-kac.log` and
`production-package.log`. Failed/rejected attempts remain explicitly excluded.
