<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Distribution Stage 2 Closure — 28 September 2026

- Status: In progress; no Stage 2 exit or clean-install claim.
- Owner: Demo Solution Team.
- Scope: Resume the [accepted delivery sequence](../planning/active/installable-distribution-and-reproducibility.md), close existing gates, preserve the current demo.
- Change: Execution/evidence reconciliation only; no new runtime behavior or architectural decision.

## Acceptance checklist

| Check | Evidence required | Current result |
| --- | --- | --- |
| Preserved restart point | Same source branch, Test/Production disks and selected runtime; no competing live owners | Observed before starting work |
| SSD identity | Original Work/Clean UUIDs, ownership and available capacity | Pass; Work approximately 572 GiB free |
| Source checkpoint | Reviewed source/contract/docs set, source gates and a local commit | Source gates pass; local commit pending |
| Live resource preflight | Existing 90-GiB internal reserve before guarded live qualification | Restored to approximately 90.5 GiB after authorized cache retention; recheck before launch |
| Native/operator UI | Complete panels, correct profiles/status/freshness, popup behavior, layout/order and bounded feedback | Not run in this continuation |
| Fresh-engine import | Empty independent image store, pinned archive load, exact identities, repeat and networkless startup | Not run in this continuation |
| Preservation | No Production/Factory/identity/ledger/backend-data changes; unrelated Docker resources intact | Observed preflight; repeat after execution |

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
  source gates: PASS before the final evidence update; rerun before committing.

## Next bounded work

1. Finish the source gates and preserve the reviewed branch checkpoint without
   moving `demo-v1.1` or claiming a published installer.
2. Recheck the restored internal reserve; preserve current runtime inputs,
   Factory .39/.31, overlays, credentials, source, video assets and warm
   standalone build caches.
3. Qualify the ordinary packaged runtime's visible UI against authoritative
   observations, not just native geometry. Reuse current Test, with no new
   release allocation, Cloud publication or model reset.
4. Verify backend archive import in a genuinely separate empty engine/store.
   Never clear the shared Docker engine or describe its idempotent load as a
   clean import. Any nested-engine proof is an artifact test, not clean-macOS
   or fresh Docker Desktop installation evidence.
5. Update the stage verdict with actual results. Only then resume the accepted
   installed-package first-use journey; do not add unrelated wizard features.

Raw local test logs remain in the ignored CARLA workspace. Project documentation
and compact qualification facts are English; secrets and private runtime state
are excluded from the source checkpoint.
