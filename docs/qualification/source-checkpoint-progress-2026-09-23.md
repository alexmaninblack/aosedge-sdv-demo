<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Source checkpoint reconciliation — 23 September 2026

Status: **local corrections and regression completed; publication incomplete**.
This is a progress receipt, not a remotely recoverable cross-repository tag,
green hosted CI claim, Factory promotion or live E2E qualification.

## Authorized scope and retained state

The operator approved source/CI fixes, documentation reconciliation, dependency
publication before integration, pin alignment and a named return point. A later
addition requests a disk-usage audit before selecting deletion targets.
No VM, Cloud Unit, simulator, service deployment or private video was changed.
No artifact was deleted. Factory .36, the Production .31 backing chain, release
continuity, warm caches and unique worktree/source data remain preserved.

## Corrections completed locally

- Platform IAM inspection no longer writes bytecode into the layer. Source
  validation ignores generated `.pyc` only directly inside `__pycache__`, while
  unrelated binary/text content and tracked-binary policy remain checked.
  The old failure was reproduced before the fix; the fixed layer was validated
  twice with normal in-tree bytecode enabled.
- Platform REUSE metadata was repaired without changing accepted patch bytes
  or relicensing upstream code. Negative tests cover exact MIT source ownership
  and missing/unlicensed patch sidecars. CI now fetches history required by
  patch-provenance tests.
- Two integration negative fixtures retain their exact runtime values without
  presenting their synthetic token/key-marker literals as real credentials to
  the source scanner. No redaction assertion was removed.
- Current READMEs and baseline navigation now distinguish the retained .36,
  dated VDP98/Brake78/Tire44 readiness proof, old .11/.33 workaround history,
  source publication and remaining P8/calibration/negative checks. Tire's README
  now matches its accepted 1024-file / 16-PID package quotas.
- The earlier accepted demo name and host sleep/wake plan are preserved.
  Automatic sleep/wake recovery is still planned, not implemented or qualified.

## Local validation evidence

| Scope | Result |
| --- | --- |
| Platform full Python suite | 193 passed |
| Platform contract, layer and repository policy | Passed |
| Platform repeated Linux-style in-tree cache proof | Passed twice |
| Platform unchanged source-publication scan | Passed |
| Platform REUSE | 225/225 files have licensing and copyright metadata |
| Integration solution suite | 352 passed |
| Component delivery regression | 28 passed |
| Presenter typecheck and unit tests | Passed; 322 tests across 31 files |
| Brake Python | 23 discovered; 5 skipped; remaining passed |
| Brake compiled host tests | 8/8 CTest plus separate V2 test passed |
| Tire compiled host tests | 5/5 CTest passed |
| Tire Python | 26 discovered; 5 skipped; remaining passed |
| Tire backend | 20/20 tests passed with local loopback enabled |
| Integration docs, confidential-input/history, component/R6.1 locks | Passed |

These source/fixture checks do not replace ARM64 deployment, native-window UI,
Cloud or complete live E2E acceptance. Sandbox loopback denial in the first Tire
backend attempt was a harness restriction; the scoped loopback rerun passed.

## Local dependency commits (not pushed by this packet)

| Repository | Local HEAD |
| --- | --- |
| aos-vehicle-platform | `50a66b73dfc11361c2b8457934b3a0d4a7118dfe` |
| brake-health-service | `230cdd4515d1be94ef342197ff56f6b76498aff2` |
| tire-health-service | `8639b57535e32e3fb2ce68f10794c90d39bb5ae5` |
| tire-health-cloud | `026018a47daa3b37ff1f4404954e8e48e70336b4` |

The first three include the previously unpublished readiness correction in
their history. Other clean dependencies were not rewritten. The immutable VDP
payload pin `1fe5649` is intentionally unchanged: source/CI documentation does
not silently select new payload bytes or promote a Factory.

## Open publication boundaries

1. The integration scanner also rejects its own 57 already tracked PNG/JPEG
   source assets and documented private QEMU-host URLs. A proposed exact
   path/digest inventory exists locally but is **not active or committed**.
   Automatic safety review rejected changing the guard without explicit scope
   confirmation. Requested scope: only those existing visual digests and the
   established QEMU-host routes in four exact files, with negative tests; no
   broad binary/private-network exemption. The original guard remains intact.
2. Automatic safety review separately rejected the platform fast-forward push
   to default `main` pending exact publication confirmation. No alternative
   remote, branch, transport or bypass was used; no push succeeded.

Therefore workspace/workflow dependency pins are not yet promoted, published
CI has not been rerun on the correction, and no final cross-repository tag is
created. Remaining workflow work includes current dependency revisions/history
and explicit Python/REUSE encoding dependencies. The current boundary job covers
integration, Platform, Brake and Gateway source boundaries; it is not whole-demo
hosted CI for Tire and both backends.

## Workspace and disk follow-up

Legacy `manual-drive` and `route` launchers still refer to the old M4 runtime
build, not the accepted final build. They are not the current Demo Control path;
no launcher was rewritten or used in this source packet. The old Brake core-v3
worktree contains untracked V3 source, so it must not be treated as disposable.
One absent temporary Brake worktree has only a stale Git registration; pruning
it would reclaim negligible disk space and was not performed.

The separate local disk audit totals 235.51 GiB under the project workspace.
The 6.10 GiB VDP/Brake/Tire package pool is a cleanup-review pool, **not** an exact
reclaimable amount. Film originals and current render dependencies, Production
backing images, CARLA content and engine caches are not scratch artifacts.
Prepare reference-aware keep/delete lists before any cleanup authorization.

## Resume order

1. Resolve the exact source-guard and default-branch publication confirmations.
2. Implement the approved narrow guard correction and negative tests; repeat
   the unchanged secret, restricted-source and unrelated-private-URL denials.
3. Publish verified dependency commits, reconcile authoritative remote HEADs,
   then align workspace/workflow pins and run clean-checkout source gates.
4. Publish integration, verify hosted results within their actual scope and
   create the dated cross-repository checkpoint/return instructions.
5. Separately review an exact artifact cleanup manifest. No live demo restart,
   E2E run, image rebuild or deletion is implied by completing source publication.
