<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Pre-UI source checkpoint and cleanup audit — 17 September 2026

Status: audit and seven-repository source publication complete. Remote commit
and annotated-tag equality verified on 17 September. No new Vehicle UI implementation.
Scope: seven custom repositories, documentation, reviewed proposal, source
tests and obsolete artifact cleanup. Running Test, simulator, Cloud records,
release ledger, credentials, Builder and native caches remain unchanged.

## Corrections made during the audit

1. Replace the stale .33 current-baseline summary with exact .35 provenance
   and dated qualification/limitations. Historical receipts remain historical.
2. Correct CLI and Presenter confirmation text still promising a simulator
   restart during Provision. Existing code already preserves the source;
   no new UI composition or runtime mutation is introduced.
3. Repair two unittest-discovery imports and test the historical capacity-only
   guard against its pinned .34 recipe inputs. The guard still rejects the
   unrelated .35 CM change; no safety check was relaxed to pass a test.
4. Preserve the visual proposal in the project as Mockup 2.9, including its
   popup/Finish interaction test. No older mockup is overwritten.
5. Reconcile workspace source pins and include both Tire repositories.
   Historical lock/build provenance is not rewritten.
6. Align the unused diagnostic Brake packaging scaffold with the already
   approved 1024 file-descriptor quota. Normal Demo Control packages already
   used 1024; no running service or package was replaced.
7. Fix the stale run-state contract test version (1.7.0 → actual 1.8.6), and
   constrain the layer-validator exception to the exact PEM delimiter-check
   expression. Negative tests still reject real PEM markers and other files.

## Evidence and remaining gates

| Area | Evidence / disposition |
| --- | --- |
| Factory .35 clean cycle | [Passed with explicit scope](factory-35-e2e-2026-09-17.md); predates no-restart Provision amendment |
| Attachment order | [Focused and preserved-run proof](source-attachment-order-2026-09-17.md); clean first-Provision repeat remains open |
| Native control/offline KUKSA | [Control/cache evidence](manual-control-and-map-cache-2026-09-17.md) and attachment receipt |
| Permissions | Staging real KUKSA passed; native upstream review and Production parity remain open |
| Cloud connection ordering | Guest workaround retained; no Cloud code change or RabbitMQ defect closure claimed |
| Visual proposal 2.9 | jsdom popup/records/reset/Finish checks; examples only, not a complete lifecycle simulator |
| Proposal discrepancy to correct before integration | Tire V1 is already advisory/reset capable, but 2.9 disables its Reset button with incompatible-service wording. Preserve the reviewed artwork now; align this preview with the existing independent Tire reset contract before implementation |
| New UI | Not implemented; viewport fit, keyboard behavior, data-age/version handling, modal polling and live flow remain gates |
| Reproducibility | Source pins are a checkout manifest, not fresh-clone or historical release-lock qualification |
| Legacy standalone launchers | Workspace doctor reports two old launchers still referencing removed `Build-ego-runtime-m4`; they are not the current democtl/Presenter path and were not silently repointed |

The new overview must reuse existing backend/Cloud read models and commands,
preserve versions/timestamps, distinguish missing/stale data from zero, and
never add guest reads. Backend records are not current native advisories.
Mockup metrics do not introduce model thresholds or new product contracts.

## Source return point

Published common annotated tag: `checkpoint/pre-ui-20260917` on `main` in:
`aosedge-sdv-demo`, `carla-ego-runtime`, `aos-vehicle-platform`,
`brake-health-service`, `tire-health-service`, `brake-health-cloud`,
`tire-health-cloud`. All seven remote repositories were verified public.
Unreal remains an existing licensed/private dependency, not a new project repo.

Every remote peeled tag and `main` matched the intended local commit at
publication. This subsequent receipt-only commit advances the solution `main`
without changing the frozen tag or implementation. Component pins are in
[`workspace/repositories.json`](../../workspace/repositories.json).
The solution tag resolves its own commit without a circular self-pin.

| Repository | Verified checkpoint commit |
| --- | --- |
| aosedge-sdv-demo | `08e508feeb5f283a0ba9f1efc0b62194974919a4` |
| carla-ego-runtime | `10e476d45c28d206d14ab0a3a5a7e1bfab85807f` |
| aos-vehicle-platform | `57243dc0a7c6d27bd4a7a10e6250b3d37dc53288` |
| brake-health-service | `057b444fa77960fa51ea61b47256339afe067216` |
| tire-health-service | `e113183feb1974511d7171a7630eac404165058e` |
| brake-health-cloud | `55bb8d820eb2d83a0bf7be9cf45aeca01a4d8924` |
| tire-health-cloud | `2ac7ccbf3d32ab3bf6e5967fb38d115f488974ad` |

All seven primary working trees were clean after checkpoint commits. Fast-forward
atomic pushes published each `main` with its tag; no history was rewritten.
Running Test QEMU and CARLA retained the same process IDs throughout the audit.

To inspect source safely, fetch the tag in each repository and create a separate
checkout (choose a different destination per repository):

```text
git fetch origin tag checkpoint/pre-ui-20260917
git worktree add --detach ../pre-ui-review checkpoint/pre-ui-20260917
```

Never reset the running checkout or reuse a live overlay. Source rollback
does not undo Cloud, versions, credentials or guest state. Preserve the current
release-continuity ledger and choose a fresh owned run when appropriate.

## Cleanup

Removed `.33/main-qemuarm64.img` and `.34/main-qemuarm64.img` from the artifact
catalog after inspecting every project overlay backing chain, QEMU ownership
and open handles: 13,994,295,296 logical bytes. Kept .35 and local backing
dependencies. Old manifests and compact logs remain for provenance, not as
selectable images. Deleted images are not in Trash; recovery requires a rebuild.

Dormant Production still depends on `.local/factory/oem-demo-factory.img`
(.31). Deleting it independently would break that VM. The earlier Production
exclusion remains until its retirement is explicitly authorized. This is the
only pre-.35 image dependency identified in the project workspace.

Five clean, stopped experimental worktrees were removed, with each exact HEAD
verified against a remote annotated archive tag before removal:

| Removed workspace-relative directory | Retained archive tag suffix under `archive/20260913/` |
| --- | --- |
| `aosedge-sdv-demo-bhs-v2-packet-digest-correction` | `bhs-v2-packet-digest-correction` |
| `aosedge-sdv-demo-studio-cloud` | `studio-cloud-observation` |
| `aosedge-sdv-demo-studio-test-retirement` | `studio-bind-release` |
| `CarlaSim/.worktrees/carla-tm-order` | `ltvp-traffic-manager-order` |
| `CarlaSim/brake-health-cloud-window-detail` | `imp-04-brake-cloud-window-detail` |

Source recovery is by those tags. No force removal was used. Remaining small
experimental directories contain unique uncommitted source, credential-bearing
diagnostics or compact provenance; they were not blindly removed. Historical
VDP inputs and package catalogs remain because current composition/re-signing
can depend on them. Builder/download/shared-state and Unreal DDC caches remain.

## Audit test receipt

| Gate | Result |
| --- | --- |
| Full SDK-backed Demo Control suite | 969 tests, 968 pass and one existing skip; 137.64 s |
| Opt-in official service configuration test | Separately executed the skipped test with the installed signer interpreter: pass across all six ordinary/no-telemetry configurations, no credentials or Cloud access |
| Solution contract suite | 351 pass; 28.01 s |
| Presenter unit suite | 143 pass; typecheck pass |
| Gateway Python suite | 132 pass; 2.16 s |
| Native Driving Control Swift | Typecheck pass |
| Platform Python/layer suite | 165 pass; 3.30 s |
| Brake service fixture suite | 14 pass; 50.79 s, includes compiled V2 native contract |
| Tire service fixture suite | 18 pass |
| Brake backend | 51 Node tests and 12 Vitest tests pass |
| Tire backend | 18 Node tests pass |
| Mockup 2.9 | Local interaction/embedded-artwork/no-network assertions pass |
| Retained Mockup 2.8 | 43 pass, two opt-in browser cases skipped; earlier browser evidence is unchanged |
| Documentation | Navigation, SPDX, stable identifiers and Mermaid gate pass |
| Publication hygiene | Outgoing Git blobs checked for private-key/token patterns and oversized artifacts; no findings; confidential-input guard pass |

Workspace doctor confirmed the revised source pins and repositories, but is
**not globally green**: two legacy launcher-path errors remain, plus the CARLA
checkout's retained untracked experiments. Current Demo Control uses its owned
runtime build and does not use those legacy shell launchers. No broad ignore
exception or replacement launcher was introduced to hide the findings.

Host free space rose from approximately 266 GiB to 274 GiB at the audit samples.
This is a net APFS observation during a running demo, not a claim that logical
file bytes equal physically reclaimed bytes.

Initial suite failures were retained in temporary audit logs and corrected as
listed above; no initial failed result is presented as a pass. The diagnostic
Brake quota-only scaffold correction is additionally covered by the final
solution quota-contract suite. No Factory rebuild, release publication, live
restart, deprovisioning or full new E2E took place during this audit.
