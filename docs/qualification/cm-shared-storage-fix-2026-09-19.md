<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CM shared-storage retention correction

Date: 19 September 2026. Status: local native/source gates and Factory .36
build passed; live acceptance pending. No current-Test restart or data reset.

## Authority and design

Following platform-team confirmation of the bug, the operator authorized a
minimal patch, local verification first and a conditional successor Factory
build. This amends the storage-patch exclusion in
[ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md).
Operator Park/Resume remains removed. Production and Cloud code are unchanged.

The reproduced defect and original two negative tests remain in the
[upstream handoff](aoscore-shared-storage-handoff-2026-09-19.md).
Platform patch `0007-preserve-shared-instance-storage.patch` targets
`aos_core_lib_cpp@60cb83535f773762c61ac5f544b31b7b88c502e3`.

The native instance manager decides whether another instance owns the same
full, version-less InstanceIdent by checking active, cached and scheduled
collections, excluding the object being retired. ServiceInstance always retires
its version-specific database row, but removes shared storage only for the final
owner. Components retain their prior no-service-storage behavior. Failed removal
remains in the collection so later checks/retries cannot lose that owner.
Expiry uses the same guarded retirement path as missing-image cleanup.

No new database/API, storage layout, background process, service-specific ID,
TTL, permission, model threshold or Cloud logic is introduced. Existing CM
connection correction is independent and is retained in the successor recipe.

## Local proof

Linux ARM64, network-disabled disposable containers, exact pinned product
sources, retained GoogleTest 1.14.0. No live volumes, credentials or guest data.
The harness compiles native CM launcher/instance-manager code; image and storage
interfaces are test doubles, not a rewritten cleanup algorithm.

| Source / gate | Result |
| --- | --- |
| Original product, expanded tests | 26 passed / 17 failed, as negative control |
| Storage correction, same expanded tests | 43/43 passed |
| Full accepted CM library patch stack | 45/45 passed; repeated ten times (450 executions) |
| Full stack with ASan + UBSan | 45/45 passed; no sanitizer failures |
| Platform Python gates | 174/174 passed |
| Demo Control Factory gates | 25/25 passed |
| Documentation check | PASS; 232 Markdown documents |

Cases cover missing old image and old cached-version expiry, active/cached/
disabled survivors, one/three obsolete versions, repeated start/stop, final-owner
cleanup exactly once, subject/index/service/type isolation, invalid old active
record, database retirement failure and storage removal failure with retry.
The existing 19 launcher/reconciliation cases remain green with the full stack.
Scheduled-owner protection is source-reviewed, not a distinct executed scenario.

The first candidate test run had two fixture errors: distinct services were
assigned the same GID. Correcting only the fixture to native per-service GIDs
removed these setup failures; product identity/security behavior was not weakened.

Proof directory: `/private/tmp/aos-storage-fix.T0LxA2`, deliberately retained.
It contains pinned original/baseline/candidate source, synthetic tests and compact
logs/JUnit, not live service data. The reusable Builder/download caches remain.

## Limitations and next gate

No claim of arbitrary concurrent cleanup, power-failure atomicity, real SQLite
or guest filesystem preservation, or a 24-hour periodic timer experiment.
The native timer invokes the same corrected expiry method by source inspection.
No attempt was made to reconstruct deleted Brake state, clear backend history,
reset models, deploy packages, publish to Cloud or replace the current Test.

The warm committed-source Factory .36 build subsequently passed the
production-toolchain native tests, package/image QA and transfer verification.
Preserve .35. Actual service-data retention and the full fresh UI-led
version/offline/E2E cycle remain required; neither local tests nor an image
artifact closes P8.

## Factory build source checkpoint

Platform source commit: `a0f88d8fc47d5e84df874883cb01872e25516fd5` (local;
not pushed or submitted upstream in this increment). Its tree includes the
previously verified connection fix, storage fix, recipe bindings, packaging
tests and offline Factory .36 configuration. Storage patch SHA-256:
`b50cd173b25636fb4c01842c3fba7cbc1a58327cbb36c0481859f1ea0692e474`.

`democtl image build 6.1.1-maninblack.36` was started after the local gates.
It reuses the existing warm Builder, rejects dirty/unpinned Platform source,
runs 45 native CM tests before image creation, and retains the five SM
Factory-input, KAC/Provider, permission-capacity and package/image QA gates.
Build log: `factory36-build.log` in the proof directory above.

## Completed Factory .36 build

`image.build` returned COMPLETED. Native production-toolchain tests passed:
45 CM launcher/storage/reconciliation cases and five SM Factory-input cases.
The 10 KAC cases, Provider and verifier preparation tests completed, and all
three manager builds retain the 256-character permission key capacity.
Package and image QA succeeded. Three non-fatal package-QA warning entries
report build-path references in CM runtime/debug/static artifacts; they were
not suppressed and remain in the build log. No packaging error was reported.

- Selector: `6.1.1-maninblack.36/main-qemuarm64`.
- Source: Platform `a0f88d8fc47d5e84df874883cb01872e25516fd5`.
- Artifact: `demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.36/main-qemuarm64.img`.
- Raw six-partition image size: 6,997,147,648 bytes.
- SHA-256: `9ff1377a0261028bc7583bbca09be2e2c6f55f4754988071f873cbc630ab50c6`.
- Creation/host-transfer digests matched; image frozen read-only. Subsequent
  catalog validation found no binding/ownership/metadata problems; no redundant
  full-image hash was run. `qemu-img info` confirms raw format and size.
- Manifest state: **BUILT_NOT_LIVE_QUALIFIED**. The guarded Builder shut down
  cleanly. Factory .35, diagnostic Test, Cloud objects, CARLA and service state
  were not changed; deleted Brake state was not reconstructed.

The Platform source checkpoint is local only; no push or upstream submission.
Demo Control .36 registration/tests and solution evidence are working-tree
changes alongside preserved earlier work. Disposable native proof artifacts
are intentionally retained until live qualification; test containers exited
with automatic removal and build/download/shared-state caches were preserved.
