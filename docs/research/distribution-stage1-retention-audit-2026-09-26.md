<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Post-Stage-1 Disk Retention Audit

- Date: 2026-09-26.
- Status: audit complete; operator-authorized cleanup of A and B completed.
  No build, recook, Docker start or runtime restart performed.
- Scope: completed standalone CARLA experiments and previously identified demo
  build artifacts, before Stage 2 portable-runtime assembly.
- References: [delivery plan](../planning/active/installable-distribution-and-reproducibility.md),
  [Stage 1 qualification](../qualification/standalone-carla-stage1-2026-09-25.md),
  [previous retention audit and completed Builder cleanup](disk-usage-retention-audit-2026-09-25.md).

## Current measurements and interpretation

The Data volume reports approximately **98.94 GiB available**, 796.61 GiB used.
No recovery is claimed. Values below are `du` allocated-block accounting, not
exclusive APFS extents. Clone sharing prevents summing directory sizes into a
promise of recovered space. Final recovery must be measured after an approved
cleanup, allowing for concurrent filesystem activity.

| Area | Reported GiB | Interpretation |
| --- | ---: | --- |
| CARLA Stage 1 build workspace | 73.30 | Includes warm build, cook inputs, cache and a build-tree app |
| Relocated initial app and small proof files | 19.24 | Initial failing comparison baseline |
| Fixed-app family | 57.69 | Three approximately 19.23 GiB APFS-related apps; one is qualified |
| Docker virtual disk | 14.35 | Shared runtime data; not a disposable cache directory |
| Historical AosCore migration workspace | 2.48 | Only six build-output children are recommended below |

These are overlapping/shared storage views. In particular, the fixed-app family
is **not evidence of three independently allocated 19 GiB copies**. The previous
Builder cleanup already recovered about 27.9 GiB; it is not a new opportunity.

## Recommended first cleanup, subject to authorization

### A. Retire historical AosCore build outputs

Parent: `/private/tmp/aos-mainline-migration-20260923.A2qEwO`.
Delete only the following completed build-output children, about **2.09 GiB**
in the fresh measurement (previous audit rounded/recorded about 2.12 GiB):

| Child | Allocated KiB |
| --- | ---: |
| `app-build` | 1,660,840 |
| `lib-build` | 304,364 |
| `cm-build` | 62,252 |
| `cm-lock-build` | 76,288 |
| `openssl-build` | 62,512 |
| `gtest-1.14-build` | 27,388 |

Preserve the parent, sources, installed dependency outputs, recipe proofs,
reports and compact evidence. These are historical host diagnostics, not the
canonical Yocto warm build. A fresh elevated `lsof` traversal found no open
handles under the parent, unlike the prior Docker-held observation. Recheck
immediately before deletion; a subsequent Docker start can change this.

### B. Retire three superseded relocated CARLA apps

Candidates, each reporting approximately 19.23 GiB:

1. `/private/tmp/aosedge-stage1.fxRsYN/CarlaUnreal.app` — initial shutdown-failing
   baseline, superseded by the tested shutdown/source fixes.
2. `/private/tmp/aosedge-stage1-fixed.w9IUrj/CarlaUnreal.app` — shutdown-only
   comparison baseline, superseded by the complete qualified profile.
3. `/private/tmp/aosedge-stage1-fixed.w9IUrj/content-profile.6j3x19s_/CarlaUnreal.app`
   — intermediate catalogue-only candidate, superseded by the shader/profile fix.

**Keep** `/private/tmp/aosedge-stage1-fixed.w9IUrj/content-profile.a38_dfdp/CarlaUnreal.app`.
It is the qualified Stage 1 candidate and input to Stage 2. Preserve the
matching Python wheel, relocation evidence, comparison manifests, source fixes,
tests and all small proof directories. Do not remove either temporary parent
wholesale. Removing comparison apps retires direct execution of those old
baselines; their diagnosis remains in the retained reports and source evidence.

No Game, Editor, compiler or build process was observed. Elevated `lsof`
traversals of both temporary roots and the build workspace returned no open
handles. APFS clone sharing means **57.69 GiB is not a recovery estimate**.
Record exact identities and reconcile references/signatures before deleting;
the qualified application must remain unmodified.

## Deferred opportunities and items to preserve

- The build-tree `source/Unreal/CarlaUnreal/Binaries/Mac/CarlaUnreal.app` reports
  another 19.23 GiB. Do not remove it as part of the first batch: retain the
  incremental build product until the Stage 2 artifact is frozen. Its eventual
  retirement is distinct from removing temporary comparison apps.
- Remaining loose `stage` data reports 1.18 GiB. It is already intentionally
  incomplete after the documented staging-content cleanup. It may be retired
  after checking the remaining files against retained package inputs and
  preserving staging manifests; no additional space is promised here.
- Preserve `cooked` (18.42 GiB), `filesystem-ddc` (12.00 GiB), and the snapshot's
  `Intermediate` (20.55 GiB). These are reusable cook/compiler inputs, not just
  failed experiments. Removing them now risks another expensive preparation.
- Docker is currently stopped: its socket is absent and the Docker API cannot
  provide fresh cache accounting. The earlier approximately 4.14 GiB selective
  demo-cache candidate remains **unverified today**. Do not start Docker or
  prune the shared disk merely to make the audit total larger. Do not touch
  unrelated application's resources, backend data or volumes.
- Preserve the canonical Yocto Builder, downloads/sstate and current work;
  Factory .39, Production's .31 and all dependent VM overlays; the running Test
  and its identity; Unreal/CARLA source and content; private video materials;
  credentials, release ledgers, manifests and qualification evidence.
- System-managed swap is not a cleanup target. No OS cache purge is proposed.

The existing Test QEMU (PID 37277) and Presenter processes (2139/2422) were still
present at inspection. This is preservation evidence, not a new functional
qualification. The known retained-demo DNS condition is not changed here.

## Original execution boundary

Recommended next action is approval of A and B only, followed by an exact-path
manifest, fresh owner/open-handle check, removal receipts and before/after disk
measurement. Do not use broad `/tmp`, project-root, Docker or build-cache prune
commands. The inspection itself produced no cleanup or new package output.

<a id="authorized-cleanup"></a>

## Authorized cleanup receipt — 26 September

The operator approved A and B above. Exactly the six listed historical build
children and three superseded `.app` directories were removed. All nine are
confirmed absent, with flushed per-target ATTEMPTED / REMOVED journal entries.
Parent directories, comparison evidence, sources and non-target siblings remain.
No deferred candidate, Docker cache, VM, source checkout or warm cache was removed.

The qualified `content-profile.a38_dfdp/CarlaUnreal.app` passed deep strict
signature verification before deletion. Fresh exact-path checks found no open
handles and no running Game, Editor, compiler or Docker backend. Metadata
inventories before and after match for all eight protected roots: qualified
app, retained migration-source/evidence files, matching wheel, cooked content,
DDC, build-source tree (including intermediates/build app), native build and
Factory backings. These inventories compare identity, mode, owner, size,
mtime and symlink targets without rehashing immutable multi-gigabyte images.

| Observation | Bytes | GiB |
| --- | ---: | ---: |
| Free immediately before removal | 108,528,758,784 | 101.08 |
| Free at post-removal reconciliation | 112,225,472,512 | 104.52 |
| Observed increase during removal | 3,696,713,728 | 3.44 |

The observed increase is not the sum of directory sizes and is not a claim of
exclusive APFS extents freed: concurrent system writes can affect it. The
earlier audit's 98.94 GiB is a different observation, not the cleanup baseline.

Preserved QEMU 37277, native Presenter 2422 and DNS bridge 24917 retained their
process/start identities. Presenter server PID 2139 was already absent in the
cleanup preflight; cleanup did not stop it or attempt recovery. This operation
does not establish healthy full-demo/Cloud operation.

Exact evidence is in the ignored CARLA build workspace:
`Build-distribution-stage1-20260925/evidence/cleanup-approved-20260926-v2/`
(`manifest.json`, `journal.jsonl`, `result.json`). The preceding preparation-only
directory is retained too; it incorrectly included its own short-lived audit
process in the keep set. That check was corrected before any deletion, and the
first directory contains no deletion journal.

Removal was direct, not Trash. Rebuilding old diagnostic binaries/candidates
requires retained source inputs; there is no application undo for the removed
directories. Current functional artifacts, compact diagnostic reports and the
qualified successor remain available. No functional E2E or new build is claimed
by cleanup.
