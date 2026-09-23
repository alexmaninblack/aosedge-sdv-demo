<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo v1.0 — completed publication and cleanup

Completed 23 September 2026. Scope: published demo source, documentation,
recoverable version marker and reference-aware removal of obsolete local
artifacts/worktrees. No live VM, Cloud Unit, simulator, service package rollout
or private video edit was performed.

## Published return point

The annotated integration tag **`demo-v1.0`** is published and verified:

- Tag object: `2b12fffdb410c74b9c8dbe5d1b59e003a444a31c`.
- Peeled source commit: `3ed04d7138186fc59f699ba19073873684468287`.
- Hosted source CI on `main`: run `35855060234`, **success**.
- Hosted source CI on the tag: run `35855476306`, **success**.
- All eight dependency HEADs matched their authoritative remote branches and
  the tagged workspace manifest. Tracked working changes were clean.

The [return instructions](demo-v1.0-return-point.md) define exact repositories,
image provenance, restore procedure and qualification limitations. This receipt
is a subsequent documentation-only commit; the immutable tag is not moved.
This is a source milestone backed by earlier scoped staging evidence, not a new
full E2E run or a promotion of the Factory qualification state.

## Removed obsolete artifact directories

The exact 219-directory plan was recorded before deletion. Plan SHA-256:
`ad0458916d6bd138244503d8491a5ff0a7eea13c5ed6762f6a732a0150089f01`.
Paths below are relative to the external artifact root
`demo-artifacts/aosedge-sdv-demo`, not the integration checkout.

| Area | Removed selection | Directories |
| --- | --- | ---: |
| `components/vehicle-data-provider` | Existing versions 4–88, including 13.0.1; 57 absent | 84 |
| `services/brake/releases` | Versions 1–69 | 69 |
| `services/tire/releases` | Versions 1–40 | 40 |
| `services/brake/builds` | Superseded source revisions, all reachable from published main | 17 |
| `services/tire/builds` | Superseded source revisions, all reachable from published main | 9 |

The removed directories occupied **4.87566 GiB** of allocated blocks before
cleanup. The observed filesystem free-space increase during deletion was
**4.89727 GiB**; APFS accounting and concurrent host activity mean this is not
a byte-for-byte attribution. The private compact metadata backup occupies
38,864 KiB (about 37.95 MiB), retaining 4,963 configuration/source/receipt files
and the retirement index. Old prepared receipts were removed from the active
catalog along with their payloads; no phantom usable package entries remain.

The first deletion gate stopped after backup because a file was transiently
open. Reconciliation proved all 219 targets remained and deletion had not begun.
The existing archive was verified byte-for-byte, the exact plan revalidated,
open handles checked again, and only then was deletion resumed. The durable
per-target receipt records completion. No guard was disabled.

## Preserved state and post-cleanup checks

- All 3,210 inventoried retained artifact/runtime files kept the same device,
  inode, size, modification time and mode. No image was rehashed merely for
  status, and no runtime/credential contents were printed.
- Factory `.36`, its original manifest and the Production `.31` backing image
  plus dependent overlay remain unchanged. No image inside integration was
  deleted; the old `.35` image had already been removed before this audit.
- Base VDP inputs 1.0.16/2.0.0/3.0.0, source profiles and existing VDP 89+, Brake 70+
  and Tire 41+ releases remain. Their retained 38 preparation receipts contain
  no absolute references into the deleted directories.
- The retained Brake build revisions are
  `4f75373123cbc00a5b7a3541b1d289cb07affd39` and
  `a7f7b0b5021c271c51a2196b620f2631fd788edc`; Tire retains
  `20e6a23dcb97c29a0315fedd2e720ab537f01ff8` and
  `fed2161a9c77703cef04d3df4d4dae2cbdca3f0d`.
- Release continuity remains VDP105 / Brake83 / Tire46. Backend data, main
  integration runtime files, source caches, Builder/Docker/engine caches and
  the private film repository remain untouched.
- Unclassified local source, older diagnostic proof binaries and Docker-held
  temporary directories were retained; age alone was not treated as permission
  to delete them. No global Docker prune or unrelated container stop occurred.

## Worktree cleanup and recovery

Three obsolete secondary worktrees were removed using `git worktree remove`
without force. All 32 ignored/untracked files were moved intact into a private
recovery directory first, checking inode/size/mtime/mode after each move.
This includes the six uncommitted Brake V3 drafts and private historical
diagnostics; no private data was copied to Git or displayed in evidence.

| Former checkout | Preserved tracked source |
| --- | --- |
| `CarlaSim/.worktrees/aos-platform-ltvp-finalize-27` | Platform archive tag `archive/20260913/ltvp-finalize-27`, commit `0a2c8249ec780e822bff90f29f9d3d5ba5dd7feb` |
| `CarlaSim/.worktrees/aosedge-ltvp-finalize-27` | Integration archive tag `archive/20260913/ltvp-finalize-27`, commit `6a943c45976cbba6ecd33d77e248dd2c9ce5765f` |
| `brake-health-service-imp-04-bhs-core-v3` | Published main contains base `63b0c5fd43572ff96c508abc5e35818218d3500a`; unique drafts are in the private backup |

These checkouts previously occupied 14,028 KiB; the private backup initially
occupied 476 KiB. One additional absent temporary Brake checkout had only a
stale registration. A single-target dry run preceded its pruning; its commit
is already in published main. The nine demo repositories now retain only their
primary registered working checkouts. Historical commits/tags were not deleted.

Private local recovery locations under the artifact root:

- `retired-metadata/demo-v1.0-20260923`: compact receipts/configuration/source,
  **not** deleted package binaries.
- `preserved-worktrees/demo-v1.0-20260923`: opaque ignored/untracked files and
  per-checkout base/ref restore metadata, protected by owner-only directories.

Exact local plan and per-target cleanup receipts remain under `CarlaSim/.tmp`.
Removed old binary bundles are not recoverable from these metadata backups;
rebuilding source does not promise byte-identical historical signatures.
All current/rollback release families and immutable Factory originals remain.
