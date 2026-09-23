<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore mainline migration — 23 September 2026

Status: authorized by the operator; production-toolchain native/package gates
passed; successor Factory build tooling ready for local qualification.
No successor image or live replacement is qualified yet.

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
| M3 | Commit pinned source, affected package tests/QA, one successor Factory build | In progress; no image built |
| M4 | Clean Test installation and sequential E2E with UI observation | Not started |

M4 must publish each next VDP/Brake version only after the preceding version is
installed and verified. VDP uses Safe Stop; QM service updates remain independent
of that gate. Check persisted analytics/outbox, resource metrics, local advisory
and authorization during external network OFF, stopped backend ingress, queued
delivery and Online recovery after ON, and owned-Test Finish. Startup alone does
not qualify this migration. Do not claim a fresh-image proof repairs legacy
records with mismatched UIDs in the preserved Test.

Record executed tests and exclusions before advancing a gate. No image build
while any required native test is failing.

## Native proof progress (23 September)

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
