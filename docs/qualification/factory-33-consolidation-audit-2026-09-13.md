<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .33 consolidation audit — 13 September 2026

Status: documentation/source/artifact audit and authorized one-off cleanup
**completed**. Payload removal finished on 13 September at 10:24:37 UTC;
available disk space increased by 15.84 GiB. See the
[exact cleanup receipt](factory-33-cleanup-2026-09-13.md).
No live runtime, Cloud, permission or deployment change was made.

## Current working baseline

The [scoped .33 E2E report](factory-33-e2e-2026-09-13.md) is the runtime evidence,
not the older .21/.27/.31 baseline notes. Immutable .33 image SHA:
`a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761`;
build source `f7922b02b15f6cf816f181e1bf97572b61859aea`.

- Test: .33, Cloud Unit `7e09f53d-d716-4ed3-a8b4-a8f0793c987c`, VDP23/V3,
  Brake11/V3 and Tire9/V1; latest E2E Cloud read Online, both services active.
- Production: existing .31, Unit `d87ba9cb-b21f-45db-8773-553e52d0353e`;
  preserved, not qualified or mutated by this work.
- Local read at 09:58 UTC: Test PID 47744 and Production PID 28620 running;
  current source Test, native controller Safe Stop at 0 km/h. These are dated
  observations, not permanent assertions of current process state.
- VDP application requires Safe Stop. Brake/Tire replacement was proven in
  moving Autopilot and does not inherit that gate.
- Services use explicit synthetic data. Native process/backend success is
  not KUKSA access, live analytics or Driver Advisory acceptance.

## Source and remote audit

Remote branch tips were read directly with `git ls-remote`; no fetch, commit,
push, merge, branch removal or remote mutation was performed.

| Repository / active branch | Local HEAD | Remote branch result | Working-tree disposition |
| --- | --- | --- | --- |
| Solution / `codex/demo-studio-implementation` | `9228677ca763e94e0f8f8a1e0e00b660ba35e1d3` | `6cf443ae28464ab2a373ead2d38e739e34d02b0f`; local is 9 commits ahead, no remote-only commits | Existing CLI/test/diagnostic changes plus current documentation remain uncommitted |
| Platform / `codex/demo-safe-stop-clock-skew` | `d963bb9f8e92069463eb00c28630dcc7f4c4f1aa` | `1c901cf75fb834b5c93224d846660b91137dd126`; local is 9 commits ahead, no remote-only commits | Qualification documentation uncommitted; image source is f7922b0, not this later docs HEAD |
| Brake service / `codex/studio-brake-runtime` | `76d80e9373c64ba815487254fe6c8820be0c22bb` | Exact match | Clean |
| Tire service / `codex/studio-tire-runtime` | `fc81a37dbb68425bf659f7bbd683898d64966792` | Exact match | Clean |
| Brake backend / `codex/studio-backend-container` | `da7ee6b12fbc7c4a85fcd0c3d75566982e7f8f34` | Exact match | Clean |
| Tire backend / `codex/studio-tire-backend` | `76a5cd2e8f40da842f16d6ad6c955b5472f4594b` | Exact match | Clean |
| Vehicle runtime / `codex/studio-controller-startup-diagnostic` | `2fc57a9bb6517d2d439d4d4c3e02b7aafad2713d` | This branch does not exist on remote | Clean locally; publication/reconciliation still required |
| CARLA / `macos-apple-silicon` | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` | Not revalidated remotely in this audit | Existing untracked scratch/worktrees preserved; no tracked source changes |

All project remotes above belong to `alexmaninblack`. No new repository is
created. Restricted Unreal Engine and the confidential Cloud source reference
are dependencies, not candidates for publication into a public repository.
The absence of the runtime branch is not a claim that its commit is absent
from every other remote ref; that broader reachability was not checked.

## Open issues and exact closure conditions

| ID | Current fact and impact | Current workaround / boundary | Required closure |
| --- | --- | --- | --- |
| OPEN-01 — Cloud service permissions | Platform team reported that service `permissions` breaks Cloud processing. Normal native permission-backed KUKSA access is not live-qualified. No new failing upload was performed merely for this audit. | Prepare packages through Demo Control with `--without-permissions --demo-mocked-data`; no service KUKSA connection or real advisory, separate mock queues/storage and explicit provenance. Do not weaken IAM, KAC, TLS or broker policy. | Team confirms deployed fix; publish automatically numbered normal packages with the accepted permission map and without mock flags; prove native registration/secret, KAC authorization, TLS/subscriptions, renewal/denial, real results and complete advisory chain. |
| OPEN-02 — Cloud connectivity event ordering | Code/log investigation proved delayed connect/disconnect consumption after a 30-minute broker acknowledgement timeout, with stale status overwriting a newer session. Original consumer-stall trigger remains unresolved. Main was identified by the user as deployed production source. | .33 packages optional CM `idleFullStatusInterval: 60s`; default source behavior remains disabled. The existing idle worker sends full status while connected. .33 recovered Connected -> Online without restart; this is client recovery, not a Cloud fix or a fixed recovery SLA. | Cloud team fixes/validates consumer settlement and stale-session handling. Repeat the controlled stale-event and real-link tests on their deployed fix, then qualify removal of the client workaround in a planned image. Never remove it from the current demo ad hoc. |
| OPEN-03 — Source checkpoint / upstream review | Local Solution/Platform changes and ahead commits are not fully published; runtime diagnostic branch is local. Native SM/CM bug fixes are integrated in .33 but upstream acceptance is not established. | Preserve exact source, patches and compact tests; no cleanup of Git/worktrees or force push. | Review scoped diffs/secrets/tests, commit documentation and code in dependency order, push named public branches and reconcile remote SHAs; submit/reconcile AosCore review separately. No images, binaries, credentials or private Cloud source enter Git. |
| OPEN-04 — Full product/UI acceptance | Native lifecycle/SOTA and synthetic backend paths pass. Real Brake/Tire analytics/advisory, current Studio dashboard integration and the complete human visual repeat are not proven by that result. | Continue UI integration against honest Cloud/backend read models and visibly synthetic data; native CARLA remains unchanged. | Complete the remaining P4/P5/P6/P7 gates, then the full same-image-SHA CLI/visual P8 repeat. Do not re-run the already passed .33 engineering cycle between every UI edit. |
| OPEN-05 — Workspace/reproduction metadata | `workspace/repositories.json` and legacy lock docs still describe older main-branch inputs and omit Tire; they are not a fresh-checkout manifest of this working feature-branch set. | This audit is the explicit current source map. Do not silently change executable accepted-revision guards or present workspace-doctor failures as runtime regressions. | Reconcile the machine-readable workspace/lock and launcher contracts with the reviewed source checkpoint; validate them once, without widening accepted branches arbitrarily. |
| CLOSED-06 — This artifact cleanup | Demo Control has no old-bundle/runtime-proof prune operation. The user explicitly authorized exact direct deletion for this one-off cleanup. | Completed without a new helper or CLI change; .33/Production/current inputs preserved, 15.84 GiB available-space increase. | [Exact receipt](factory-33-cleanup-2026-09-13.md). A reusable maintenance command remains absent; this exception creates no new standing authority or implementation commitment. |

Permission semantics were checked against the official
[service schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-service-config)
and [security model](https://docs.aosedge.tech/docs/aos-core/security-model/):
declared permissions and native instance authorization are distinct from network
reachability. The [Subject description](https://docs.aosedge.tech/docs/how-to/tutorials/service-management/subject/)
allows Group Subjects on multiple Units; our stricter binding to current Test
is a demo ownership rule. These documents do not confirm a Cloud bug fix has
been deployed. The bug status comes from the team's report and scoped run.

## Artifact ownership and retention

Artifact root: `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo`.
Sizes below are rounded `du` allocated-space observations, not guaranteed APFS
reclamation or purgeable capacity. All destructive targets require final
regular-file/symlink/open-handle checks immediately before removal.
The data volume reported **231 GiB available** during this audit (`df`, before
any deletion); purgeable capacity is not included as a separate measured value.
Candidate allocations sum to roughly **16 GiB**, not a promise of equal physical
reclamation on APFS.

### Preserve: inputs needed by the working demo and next run

| Artifact / state | Why it must stay |
| --- | --- |
| `factory-images/6.1.1-maninblack.33/` | Canonical qualified immutable image and manifest; no rebuild required |
| Canonical `.local/factory/test-factory.img`, `.local/demo-current/validation.qcow2`, current `.run/demo-current` | Active .33 Test working copy, child disk, access and operational state |
| .31 original and canonical Production Factory copy/overlay/access | Production still runs on .31; no Production action authorized |
| VDP `1.0.16`, `2.0.0`, `3.0.0` directories | Hard-pinned `PROFILE_BASES` inputs, not disposable historical releases; deleting them breaks `component prepare --profile` |
| VDP21/22/23 full prepared/signed directories | Current .33 functional V1/V2/V3 qualification/replay artifacts and receipts |
| Brake current build `76d80e9…` profiles v1/v2/v3 and releases9/10/11 | Inputs to the next automatic release without recompilation; current qualified packages |
| Tire current build `fc81a37…/v1` and releases8/9 | Same for Tire; only functional v1 exists |
| `.local/release-continuity.json` | Current maxima: VDP23, Brake11, Tire9; next local floors 24/12/10, additionally reconciled with Cloud. Never reset/reuse old numbers |
| Published Cloud components/services, dedicated Subjects, Test/Production sets | Persistent platform/release objects, not local intermediate artifacts; no Cloud deletion in housekeeping |
| Backend active images/volumes, signer credentials, shared DNS, native app/runtime, Builder/download/sstate caches | Required runtime/build infrastructure; no blanket Docker/Yocto/cache prune |
| Source repositories/worktrees, patch files, compact manifests and qualification logs | Source/upstream evidence; source availability and publication are not yet fully reconciled |
| Private Cloud read-only source reference | Still needed for OPEN-02; never copy into public Git |

### Completed deletion: superseded engineering output, not current inputs

| Exact scope | Observed allocation / proof | Disposition |
| --- | --- | --- |
| `.32/main-qemuarm64.img` beneath Factory artifact directory | 6.5 GiB; canonical Test now .33; compact .32 manifest/log retained | Removed |
| `aosedge-sdv-demo-qual-31/.local/demo-current/validation.qcow2` and `.local/factory/oem-demo-factory.img` | About 7.3 GiB; comparison Unit already DELETED/absenceConfirmed; no open handles | Removed child then backing; compact report/journal retained |
| Superseded `runtime-proofs` SM/CM executables | Ten binaries, 834 MiB; fixes packaged in .33 | Removed executables; manifests/tests/review material retained |
| VDP `1.0.15`, `4.0.0`–`20.0.0` (including `13.0.1`) | About 329 MiB; required bases and21/22/23 excluded | Removed archives/payload trees; small historical metadata and release continuity retained |
| Brake releases1–8; Tire releases1–7 | About 490 MiB; local snapshots only | Removed archives/payload trees; historical publication metadata retained; no Cloud deletion |
| Older Brake/Tire build outputs | About 263 MiB; source commits confirmed present | Removed old rootfs exports; compact build/test receipts retained; current exact builds untouched |
| Scoped `/private/tmp` Brake/Tire native fixture build outputs | About 173 MiB; no open owners | Removed selected executables/libraries/CMakeFiles and obsolete Tire fixture state; source fixtures and compact test evidence retained |

Retained metadata describes historical, now-removed payloads; it is not a
reusable prepared release or complete build cache. The exact receipt lists
every removed target, including the additional empty directory shells.

Existing CARLA presentation scratch, old source worktrees and unrelated project
files are not silently included. Neither a folder name containing `.27` nor an
untracked Git status proves that its contents are disposable. This audit does
not delete branches or rewrite Git history.

## Validation and changes in this audit

- Reused the qualified image and .33 E2E; no rebuild, reprovision, publication,
  simulator/VM restart or new helper was performed.
- Inspected actual CLI/source dependencies, public runtime status, exact local
  Git/remotes, artifact allocation and the completed .31 retirement record.
- Updated the current baseline, documentation entry points, service-input
  implementation status and delivery-plan checkpoint. Historical qualification
  evidence is labelled as history rather than being presented as current.
- Corrected obsolete reproduction claims that Tire/backends and the native
  dashboard do not exist, and removed stale “implementation unauthorized”
  wording from current navigation. The roadmap remains historical design
  rationale; the active plan now owns the current P0–P8 position explicitly.
- Preserved the raw CM review-patch bytes under `components/upstream-review/`
  instead of unsupported patch artifacts in the documentation tree. Removed
  personal absolute paths from the two new diagnostic reports. No runtime
  implementation changed during this audit.
- Existing evidence remains 694 local tests (six skips), followed by focused
  cleanup/publication regressions and the actual .33 E2E. Documentation editing
  does not claim those tests were rerun today.
- Documentation quality gate **PASS** after cleanup: 182 Markdown documents, 658 stable
  identifiers and 38 Mermaid diagrams. `git diff --check` passed in Solution
  and Platform. No Cyrillic text was found in the new audit/baseline or updated
  plan/input/reproduction documents. These checks do not repeat live E2E or
  claim unpublished source has been committed.
- Authorized cleanup removed 166 payload targets and five empty directory shells.
  Available space increased by **15.84 GiB** to **247.23 GiB**. Removal is
  permanent, with no Trash/backup. No Cloud object, branch, worktree, current
  VM, Docker volume or Builder cache was deleted.
- Post-cleanup Demo Control catalog has only .31/.33 and no issues. Local status
  at 10:25:41 UTC confirms the same Test/Production PIDs still running, current
  selection Test and Safe Stop at 0 km/h. All 20 retained input/state paths and
  the unchanged 23/11/9 release ledger were verified. No guest/Cloud probe or
  new E2E qualification is inferred from this read.
