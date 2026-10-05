<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Distribution Stage 2 Closure — 28 September 2026

- Status: Functional/UI checks passed in their recorded scope; timeout follow-up explicitly user-deferred. Stage 3 continuation allowed; no unconditional Stage 2 exit or clean-install claim.
- Owner: Demo Solution Team.
- Scope: Resume the [accepted delivery sequence](../planning/active/installable-distribution-and-reproducibility.md), close existing gates, preserve the current demo.
- Change: Execution/evidence reconciliation only; no new runtime behavior or architectural decision.

## Acceptance checklist

| Check | Evidence required | Current result |
| --- | --- | --- |
| Preserved restart point | Same source branch, Test/Production disks and selected runtime; no competing live owners | Observed before starting work |
| SSD identity | Original Work/Clean UUIDs, ownership and available capacity | Pass; Work approximately 572 GiB free |
| Source checkpoint | Reviewed source/contract/docs set, source gates and a local commit | PASS; local commit `70dac05`; no push or baseline tag change |
| Live resource preflight | Existing 90-GiB internal reserve before guarded live qualification | Restored to approximately 90.5 GiB after authorized cache retention; recheck before launch |
| Native/operator UI | Complete panels, correct profiles/status/freshness, popup behavior, layout/order and bounded feedback | Retained-Test UI E2E and bounded correction recheck passed; prior transport causality remains open |
| Fresh-engine import | Empty independent image store, pinned archive load, exact identities, repeat and networkless startup | PASS in a separate rootless nested engine; not clean-OS qualification |
| Preservation | No replacement/deletion of Production, Factory, identities, ledgers or backend histories; unrelated Docker resources intact | Same Test/Production identities and all seven existing container IDs retained; histories not reset |

No successful row authorizes silently closing another row. Stage 3 preview 005
and Kit 007 remain the existing candidates; there is no new setup preview,
Game cook, Factory build, service build, publication or provisioning here.

## Reconnection and resource preflight

Work UUID is `591578E3-8196-4B44-A575-CEC76B406789`; Clean UUID is
`870130E1-51A1-4ED8-841E-DB84B7941376`. Both match the accepted disk plan.
Work enforces file ownership. Clean remains reserved; no macOS installation is
performed. The existing installed selection and local setup fixture survive.

The 27 September shutdown was retained: no CARLA, QEMU, Driving Control,
Presenter or setup preview owner was observed. Both demo backend containers
remain exited with status zero. Five unrelated Watt containers remain running;
do not stop/reset their engine to create an apparently empty test environment.

Initial internal available space was below the existing 90-GiB reserve. The
operator explicitly authorized retaining the unused Editor-era Zen cache on
Work and removing its verified internal original. The five payload targets
(`cache`, `cas`, `gc`, `root_manifest`, `state_marker`) were copied to the private
Work directory `AosEdge-SDV/staging/zen-retention-20260928.KutobN`. A complete
checksum comparison found no differences. Repeated open-handle and consumer
checks were empty before removing those exact internal targets.

Internal free space increased by 9,539,264 KiB (approximately 9.10 GiB) to
94,909,868 KiB (approximately 90.51 GiB). The retained copy contains 495 regular
files and 10,043,819,383 logical bytes and remains recoverable. Authentication,
logs and project metadata stayed internal; the separate standalone CARLA DDC,
warm builds, Factory images and all demo state were unchanged. This is a narrow
reserve, not permission for additional large copies; recheck each live gate.

## Source-gate execution

An initial test invocation used the old orchestrator development environment.
Distribution discovery failed because `packaging` was absent; orchestrator
discovery lacked `cryptography`. These are test-environment failures, not
evidence of a product regression. No dependencies were installed to hide them.

The retained source-gate environment passed all 206 distribution cases,
including the opt-in isolated process-lease test. A subsequent SDK invocation
without the explicit source import path failed at discovery before executing
the application tests. The corrected invocation uses the already packaged
Python 3.12 SDK and the explicit orchestrator source path, with synthetic
credential/signing fixtures only.

Two stale test expectations were corrected: the documentation corruption test
now substitutes the actual scenario version rather than hard-coding 2.0, and
the CI checkout assertion includes the two already-pinned backend repositories.
Neither change relaxes the product checks or changes runtime behavior.

The Cloud SDK integrity check correctly rejected 22 undeclared Python bytecode
files. Their pinned source files were verified, then only the generated files
(596,387 bytes) were moved to a private temporary quarantine with a receipt.
The complete pinned runtime subsequently passed verification. Further tests
disabled bytecode generation for both parent and child interpreters; no library,
manifest, credential or integrity rule was changed.

Final local source results:

- Repository suite: 573 tests, PASS (35.309 seconds).
- Orchestrator suite: 1,190 tests, PASS with one opt-in native test skipped
  (146.154 seconds). This does not close visible UI acceptance.
- Distribution suite using packaged Python 3.12: 206 tests, PASS, including the
  isolated process-lease check (5.732 seconds).
- Official-schema/service targeted suite: 25 tests, PASS (7.713 seconds).
- Documentation, component locks, whitespace, confidential-input and public
  source gates: PASS; confidential-input and documentation gates repeated at
  the source commit.

The first retained-VM start was blocked by the equivalent host-runtime inventory
guard: 49 additional CPython cache files (1,184,907 bytes), dated before this
continuation, existed beside the pinned host Python sources. After verifying
their corresponding pinned sources, these exact generated files were moved to
a separate recoverable private quarantine. The complete host Python group passed
verification and one corrected start completed. No integrity exception or
fallback was introduced.

## Independent empty-engine proof

The fixture used the official ARM64 `docker:29.7.2-dind-rootless` manifest
`sha256:cac84af5928c5d88e920165ce675b17c03ab2165e5418abb3c0c25cb8a1e3cbf`.
Its independent daemon reported zero images and zero containers before import.
There were no published ports, external network, host mounts or shared Docker
socket. Image data lived in bounded tmpfs storage; outer limits were 2 GiB of
memory with no additional swap, two CPUs and 512 processes.

The official nested rootless setup requires an outer privileged container.
Inner cgroups were unavailable; this is **not** evidence of service quota
enforcement, VM-grade isolation, a fresh Docker Desktop installation or a clean
Mac. Those limitations are explicit, not inferred away from the import result.

The first two attempts preserved a harness failure: default image listing hid
the imported untagged OCI indices. Import output already reported both expected
IDs, and the archive digest remained correct. Docker's
[image-list documentation](https://docs.docker.com/reference/cli/docker/image/ls/)
and CLI help confirmed that `--all` is required. The fixture was corrected to
enumerate all images without changing the exact-ID assertion or adding tags.

The corrected fresh attempt passed:

- First archive import: **1.901 seconds**; exactly the two pinned image IDs.
- Repeat import: **0.775 seconds**; unchanged image set.
- Both images: exact source revision and Linux/arm64 identity, non-root `node`
  user, read-only rootfs, no network, dropped capabilities and no-new-privileges.
- Both processes: readiness HTTP 200, missing Unit context correctly rejected
  with HTTP 503, private admin socket and a newly created empty SQLite database.
- Both disposable backends and the test daemon were removed. All seven existing
  outer container IDs were retained, including the five running Watt containers.
  The exact test-daemon image downloaded for this proof was also removed after
  confirming no container used it; required backend images were retained.

Compact evidence: `Build-distribution-stage2-20260926/empty-engine-20260928-003.json`
in the ignored CARLA workspace. Failed attempts 001/002 remain separately
recorded; they are not relabelled as successful runs.

## Preserved Test restart and native visual review

Test Unit `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb` was reused with its existing
VM, enrollment and stored backend data. Corrected VM start took 33.24 seconds.
The packaged simulation started once; selecting its exact registered app path
did not create another simulator process. Normal authentication/selection
confirmed stationary Safe Stop, reset the simulator scene through the existing
handover path, and established one selected-platform role and one dashboard
role. There were zero qualification clients. Production remained stopped.

At 08:05:21 UTC, AosCloud independently reported ONLINE, Factory .39, VDP117,
Brake92 and Tire49; both service instances were active, with no pending release
or reported error. No Cloud publication, new release allocation, provisioning,
model reset or new image build occurred.

Direct native observations confirmed:

- CARLA displays the expected vehicle and Town10HD scene, not a blank window.
- Driving Control's Dashboard, Vehicle and Data tabs render live values;
  observed Data values include 20 Hz simulation and approximately 4 events/s.
- Both retained inspection recommendations appear on the driver dashboard and
  agree with fresh backend APPLIED advisory facts.
- Autopilot was requested through the native UI. The source frame independently
  reported AUTOPILOT at 19.397 km/h. Native Safe Stop then showed STOPPING and
  finally STOPPED at 0.0 km/h. The car was left in Safe Stop, network ON.
- Window geometry matched the requested layout and ordering reported VERIFIED.
  This does not substitute for inspection of Presenter cards/popups.

### Open findings and proof limits

1. The built-in browser retained a `data:` error page from the earlier shutdown.
   Computer-use policy rejected selecting that page. The operator was asked to
   reopen the allowed local HTTP address; no alternate browser or indirect UI
   workaround was used. Presenter cards, detailed dialogs and their feedback
   timing remain unreviewed in this continuation.
2. At the normal 914-by-503-point control-window size, the Return-to-road
   explanatory line overlaps the upper area of the external-network button.
   Primary button labels remain readable, but this is a visual defect to triage
   before closing the complete native presentation gate.
   Read-only source inspection located the overlap: `KeyboardControl.swift`
   draws `sceneDetail` in a 50-unit-high text rectangle starting at y=70,
   intersecting the network button's y=86..122 rectangle. This is drawing
   geometry, not a window-placement or connectivity failure. A bounded caption
   rectangle in the existing inter-row gap is the proposed correction; no
   native binary or pinned artifact was changed in this continuation.
3. Bounded guest logs contain VISS response timeouts during this session, while
   current readiness is READY/LIVE, automatic SM/CM/VDP restart counts are zero,
   and fresh backend advisory facts say APPLIED. These observations do not prove
   uninterrupted advisory transport or explain the timeout cause. Keep this
   distinct from the previously retained readiness-flap follow-up; do not close
   either merely because the dashboard currently displays recommendations.
   A second snapshot after the import fixture was removed still showed those
   timeouts, so they cannot be dismissed as a short import-only load spike.
   At 08:06:21 UTC the car was independently confirmed SAFE_STOP, 0 km/h,
   brake 1.0; fresh APPLIED receipts and READY/LIVE continued. Cause remains open.
   Source inspection distinguishes the two signals: `AdvisoryTransport` expires
   an unconsumed Set reply after two monotonic seconds; APPLIED is a separate
   Gateway status delivered through the subscription. Therefore a visible
   recommendation and a Set-reply timeout are not logically contradictory.
   The next diagnostic must correlate the exact request/reply arrival and
   consumption timings before selecting a transport fix; increasing the
   deadline or changing model/readiness policy is not justified yet.

The read-only comparison is recorded in
`Build-distribution-stage2-20260926/packaged-live-stage2-ui-20260928.json` and
`packaged-live-stage2-post-import-20260928.json` in the same directory.
Stage 2 remains open; no new Stage 3 installer feature starts on this evidence.

## Next bounded work

The operator reopened Presenter and requested a full E2E check. The subsequent
[retained-Test live E2E report](distribution-stage2-live-e2e-2026-09-28.md)
supersedes the earlier Presenter-pending status above: popups, team views,
independent resets, real maneuvers, a five-minute-plus network outage, queued
delivery, ignition recovery and post-boot maneuvers were exercised. All 23
recorded-state assertions passed; no clean install or serial-release run is
claimed. The intentional resets preserved assessment/event history.

1. **Completed:** Presenter ignition/Finish classification and native caption
   corrections are deployed and rechecked. See the
   [UI correction report](distribution-stage2-ui-corrections-2026-09-28.md) for
   red/green tests, actual power-cycle UI proof and preserved retirement guards.
2. **User-deferred on 28 September — `VDP-TIMEOUT-01`:** later correlate VDP request/response timeouts
   with Gateway evidence before selecting any fix. Do not rebuild from a symptom
   or widen security. Do not merge this with the existing readiness-flap issue
   without evidence. The actual runtime loop reproduces expiry-before-consumption
   under controlled local delay, but that is not yet the old incident's cause.
   The user requested parking this investigation and returning to the main
   packaging plan. Preserve the evidence; do not mark the issue fixed.
3. Maintain the internal reserve and preserve all current runtime inputs,
   Factory .39/.31, overlays, credentials, source, video assets and warm build
   caches. After test-image removal, the observed reserve was approximately
   92.17 GiB; values remain time-dependent.
4. Resume the accepted installed-package first-use journey with the explicit
   timeout deferral recorded above. Reconcile corrected UI inputs, verify the
   native install/access path and complete guarded first launch; do not add
   unrelated wizard features or repeat completed import work. Clean-system and
   external-release acceptance remain separate gates; the deferral does not
   convert the timeout into a passed transport test.

**Subsequent authorized clean-install checkpoint:** the operator explicitly
authorized retiring the old Test, superseding its overlay-preservation boundary
for that run only. Normal Finish completed; Production's local data, original
Factories and published releases were preserved. The
[clean installation report](clean-installation-2026-09-28.md) records new native
installation/selection, real existing-access checks and installed Presenter
startup against empty state. Native launch UX, new-user enrollment and fresh
installed E2E remain separate gates; `VDP-TIMEOUT-01` remains deferred.

Raw local test logs remain in the ignored CARLA workspace. Project documentation
and compact qualification facts are English; secrets and private runtime state
are excluded from the source checkpoint.
