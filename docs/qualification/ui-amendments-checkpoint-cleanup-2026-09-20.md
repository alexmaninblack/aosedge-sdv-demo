<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# UI amendments: audit, cleanup and source checkpoint

Date: 20 September 2026. Authority: operator requested a full audit of the
recent changes, deletion of obsolete artifacts (explicitly including Factory
.35), followed by commits and pushes. The current staging Test and Production
are not retirement targets.

## Audited scope and result

Source checkpoint at entry: `90c80aee809bfc2d6e06f6cc1465586ccdafa4be` on
`main`, with five commits ahead of the freshly fetched `origin/main`:

| Commit | Boundary |
| --- | --- |
| `90386c7` | Honest pending/uncertain Reset guidance |
| `de5e038` | Independent backend outage/timeout qualification |
| `397e657` | Card Reset actions and independent Cloud resource history |
| `ff8931b` | Verified disk units and daily network accounting |
| `90c80ae` | Consistent Reset Driver Advisory wording |

Review covered the 46 changed files, accepted UIA0–UIA8 packet, Cloud
observation contract, Reset contract, tests, current artifact dependencies and
actual remote refs. No new functional defect was established in the audited
changes. This is not a claim that every deferred live branch has passed.

Corrected documentation drift: .35 still described as the current immutable
Factory, an obsolete pending-push statement, already implemented history
described as future work, an incomplete UIA0–UIA6 heading, and repository
ownership text claiming that Tire repositories did not exist. Historical
qualification records and mockup versions remain evidence, not disposable
scratch; they are linked to the new inventory rather than rewritten or deleted.

## Repeated regression

| Gate | Result |
| --- | --- |
| Presenter typecheck | PASS |
| Presenter unit tests | 322 passed |
| Presenter fixture browser tests | 137 passed |
| Demo Control | 1,024 passed; one skipped (1,025 total) |
| Solution Python suite | 352 passed |
| Historical mockup suites | 173 passed; eight opt-in browser skips |
| Function observation contract | 30 passed |
| Confidential-input/history guard | PASS |
| Outgoing source scan | No private-key/token pattern or large/binary artifact finding in the audited delta |
| Documentation and diff checks | PASS: 247 Markdown documents, 658 stable identifiers, 38 Mermaid diagrams; no whitespace errors |

The initial solution-suite attempt used a Python without PyYAML and failed two
module imports. A disposable environment with PyYAML 6.0.3 passed the entire
352-test suite; no product behavior or installed demo dependency was changed.
Mockups are Node tests, not Python discovery targets. Passing fixture suites
does not imply that a new live lifecycle, network fault or Reset was executed.

Workspace-doctor confirmed repository/remote/pin consistency, but retains two
pre-existing launcher-contract errors: `manual-drive` and `route` do not refer
to `runtime-build`. CarlaSim also retains unique untracked work. These are
explicit housekeeping debt, not silently marked green or deleted. The running
Demo Control-owned simulator path was not replaced with those legacy launchers.

## Removed artifacts

Paths below are exact reviewed targets. The Factory path is relative to the
OpenAI workspace; scratch paths are absolute. Physical allocation was measured
before removal. Dependency chains, file types, mounts and zero open handles
were checked before deletion.

| Removed target | Allocated KiB |
| --- | ---: |
| `demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.35/main-qemuarm64.img` | 6,833,152 |
| `/private/tmp/presenter-uia-build.B9AlnW` | 4,064 |
| `/private/tmp/presenter-uia-rollback.lY6Fqa` | 5,488 |
| `/private/tmp/presenter-resource-units.YplMAR` | 7,296 |
| `/private/tmp/brake-runtime-gates` | 47,180 |
| **Total** | **6,897,180 (approximately 6.58 GiB)** |

These are permanent deletions, not Trash moves. The image can only be rebuilt
from retained pinned inputs; there is no promise of byte-identical recovery or
instant rollback to .35. Its manifest and configuration-test log remain.
Compact Brake test results were preserved under artifact qualification
directory `cleanup-ui-20260920/brake-runtime-gates-Testing` before compiled
scratch was removed. Available disk space was approximately 255 GiB after
cleanup; this is a changing APFS observation, not an exact reclaimed-space
counter. The additional 13,384 KiB disposable audit Python environment at
`/private/tmp/aos-audit-tests.nxhuJX` was removed after the tests and a zero-open-
handle check; it is not included in the obsolete-artifact total above.

## Preserved dependencies and cleanup exclusions

- Current immutable Factory .36 and its recorded SHA-256/build revision remain
  as listed in the [working baseline](current-baseline.md#immutable-factory).
  Its manifest is still `BUILT_NOT_LIVE_QUALIFIED`; source auditing does not
  promote it to complete P8 acceptance.
- The active `validation.qcow2` chain uses `.local/factory/test-factory.img`
  (.36). The separate `production.qcow2` chain uses
  `.local/factory/oem-demo-factory.img` (.31). Both chains were inspected;
  deleting Production's older backing file would corrupt its existing overlay.
- Latest UI rollback remains at
  `/private/tmp/presenter-advisory-label.igNif1/previous-dist`; the current
  compiled distribution and assets still possibly loaded by native windows
  remain. Earlier rollback-path statements in the amendment report are dated
  evidence and superseded by this inventory.
- Docker still holds handles beneath `aos-cm-lock-fix.WfcfVL`,
  `aos-cm-lock-test.5CpXWu` and `aos-storage-fix.T0LxA2` in `/private/tmp`.
  The six checked compiled build subdirectories were not removed. Earlier
  service worktree retention under `aos-service-p4.MutJS1` also remains; no
  Docker shutdown or forced deletion was used to recover more space.
- Unique CarlaSim drafts/worktrees, the stage-A credential-template source,
  helper scripts, Git objects, accepted package inputs, published releases,
  continuity ledger, factory manifests, compact logs, Builder, downloads,
  shared-state/Unreal caches, credentials and live backend data remain.
  These are not all safely classifiable as obsolete.

## Runtime preservation

The read-only Presenter catalog after cleanup lists only Test Factory
`6.1.1-maninblack.36`, with `METADATA_AVAILABLE` (not a new qualification claim).
The Presenter server retained session
`3201e40b-5b17-42b0-a87f-7dbd7669e042` and served UI build
`68fea053d6447e5a5b8fb3340a39a30678645ebc74f68b9978577f5ad3339cf5`.
The original desktop Presenter, QEMU, CARLA, Gateway, Driving Control and VISS
processes remained present. No restart, source reconnect, network toggle,
advisory reset, upload, service deployment or Finish was issued by this audit.
This is process/source preservation, not a newly measured Cloud-online proof.

## Repository inventory

Actual remote branch heads, not only cached tracking refs, were compared with
local HEADs. All eight dependencies below matched their tracked remote and
had no tracked source changes; the accepted workspace pins match them.

| Repository | Branch / remote | HEAD |
| --- | --- | --- |
| carla-ego-runtime | main / origin | `453b7948006d0264b0cede17816aaf551485b3cf` |
| aos-vehicle-platform | main / origin | `75503cdc2b9ab0ecb527db3bbf84e5380d6c42c7` |
| brake-health-service | main / origin | `4f75373123cbc00a5b7a3541b1d289cb07affd39` |
| tire-health-service | main / origin | `20e6a23dcb97c29a0315fedd2e720ab537f01ff8` |
| brake-health-cloud | main / origin | `42395715103d9f512c2586a2c9b98c3975c06ab7` |
| tire-health-cloud | main / origin | `47cfa632a80c89a7eaab0c501fe437c4ae2cb180` |
| CarlaSim/carla | macos-apple-silicon / personal | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| UnrealEngine5_carla | macos-xcode26-compat / personal | `9b705d6d2db5b769ab34edb04f3ca2bb8b960014` |

Only the solution repository required a push. Its configured GitHub repository
is public (`alexmaninblack/aosedge-sdv-demo`). No visibility change is needed.
The licensed Unreal dependency is not republished as a public project.

## Publication

The operator requested publication of the five outgoing commits and this
audit/documentation correction. The combined commit/push command was rejected
before execution by the automatic safety review: public disclosure of source,
internal paths, runtime metadata and architecture in this exact payload needs
separate explicit confirmation for `alexmaninblack/aosedge-sdv-demo`.
Local checkpointing proceeds independently; no successful push or remote
publication is claimed. Do not retry through a different transport or otherwise
bypass that boundary. No credentials, runtime data files or VM images enter Git;
non-secret environment details in source and this report are still a disclosure.

## Remaining qualification boundaries

Publication reconciliation, 23 September: actual GitHub `main` was read as
`eaf176465f9311ef9504b9543dd3be7df2309ddc`, which includes the UI amendment batch.
The rejection above records the earlier attempt, not a permanent unpublished
state. The later advisory readiness commit and current audit corrections are
separate work; this addendum does not claim their publication or green CI.

Preserve the open gates in the [timing report](presenter-ui-timing-e2e-2026-09-20.md#targeted-follow-up-after-the-completed-cycle):
real Manual/off-road/occupied-spawn and held-input recovery; deliberate live
macOS lock/unlock; the unexecuted live negative combinations; independent
D4-003 calibration; historical source-frame-gap root-cause proof; and separately
agreed guest-reboot engineering qualification. Native-wrapper reload and
native preflight-copy activation are not silently established by browser tests.
No new runtime defect is inferred from those not-yet-executed checks.
