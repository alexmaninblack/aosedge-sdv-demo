<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Staging source checkpoint — 15 September 2026

- Status: Audited source checkpoint; known gaps retained before staging KUKSA work
- Version: 1.0
- Prepared: 2026-09-15
- Owner: Demo Solution Team

## Scope and authority

The operator requested an audit, commits and pushes of the current working
increment before a separate staging service-to-KUKSA phase. The operator reports
that staging is working. This checkpoint records that report separately from
the dated automated/live evidence; it is not a new full staging E2E run.

No provisioning, upload, service assignment, manager restart, image rebuild or
Production change is part of this source-publication task. The immutable Factory
`.33` remains unchanged. Source publication does not update an existing VM.

## Consolidated changes

| Boundary | Changes included |
| --- | --- |
| Cloud selection | OEM-certificate domain selection in Session/democtl; matching OEM/SP authority; transient Test endpoint/hosts projection; domain and tenant isolation |
| First-use setup | Explicit Check/Prepare for the matching model and Test verification set; no implicit provisioning; Test no longer depends on a Production set |
| Packages | Pinned unsigned VDP sources, current-session OEM/SP signing, immutable prepared content, signer-specific representations and owner-scoped publication receipts; no blind upload retry |
| VM and source | Reduced repeated guest checks; owned source recovery; abnormal Finish shuts down local runtimes before Cloud retirement |
| Service lifecycle | Dedicated retained Group Subjects, explicit assignment recovery, synthetic runtime-input preparation and backend-data cleanup |
| Presenter | Studio flow, protected service operations, exact-version status/details, bounded record lists, freshness/error handling, external-CLI refresh and client-build notice |
| Native controller | Consistent dark presentation, mode selection distinct from physical movement, network-display freshness and allowlisted vehicle advisory values |
| Documentation | HLA 1.7 / ADR 0016, run-state contract, active delivery plan and dated performance/live-cycle evidence |

All normal mutations still go through Demo Control. Platform/team monitoring
remains Aos Cloud sourced; native in-vehicle telemetry is not a Cloud status
display. Services remain explicitly synthetic and permission-free in Presenter.

## Latest lifecycle evidence

At 14:38:42–14:38:44 UTC, **Continue Finish** completed through the real Presenter
in 2.70 seconds. The current Test had never been provisioned, but had an accepted
VDP 61.0.0 upload. The missing reconciliation call, previously conditional on
having a Unit identity, is now made for that exact accepted upload independently
of provisioning. Cloud processing or installation is not a retirement gate.

UI returned to **No controller created / Create controller**. Test working data
was removed without backup; Factory originals, Cloud releases, automatic version
continuity and the existing Production peer were preserved. No Unit was claimed
deprovisioned or deleted in that run: those steps were no-ops because it had no
Unit identity. VDP 62.0.0 was only prepared/signed and was not uploaded by Finish.

Earlier records of a parked or Online staging Test are historical checkpoints,
not instructions to resume a currently retained Test. The current local journal
has no Test entry and records completed Test retirement.

## Audit findings and verification

- Updated stale Cloud-reader fixtures to use the real constructor/pool and
  route mock responses by operation rather than thread-dependent call order.
- Updated the QMP negative fixture: `quit` is explicitly allowed for terminal
  disposal under the accepted Finish contract; `system_reset` remains denied.
- Real signing tests require the installed Aos SDK Python. The dependency-free
  CLI environment now explicitly skips them; the SDK suite actually executes
  them with disposable keys, without operator credentials or Cloud calls.
- Synchronized the Factory copy of the public input projector with Demo Control:
  repeated no-op preparation avoids redundant fsync/post-write observation.
  First-write checks remain. This is source synchronization, not a new `.33`.
- Found a remaining Upload-to-Deploy receipt-path mismatch for new SP tenants:
  Upload uses the authenticated owner in its publication path, while assignment
  still searches the older domain/role-only path. A bounded correction was
  proposed to the operator; it does not require permissions or Cloud mutation.

| Verification | Result |
| --- | --- |
| Presenter unit tests | 127 passed |
| Presenter browser fixtures | 88 passed; isolated localhost fixture server, not a live Cloud E2E |
| Presenter TypeScript/build | Passed; generated output stays outside Git |
| Native runtime Python tests | 110 passed |
| Native Driving Control Swift typecheck | Passed; CARLA was not launched |
| Factory runtime-input tests | 11 passed |
| Projector equality and runtime/input regressions | 45 + 18 passed |
| Full SDK-backed Demo Control suite | 846 tests in 59.43 seconds: 845 passed, one existing skip; real signing fixtures executed |
| Documentation gate | Passed: 197 Markdown documents, 658 stable identifiers, 38 Mermaid diagrams |

The initial complete CLI-environment run exposed outdated fixtures and missing
optional signing dependencies; it was not a passing gate. The SDK rerun closed
those failures and isolated the projector-copy discrepancy, which is corrected
and covered by the exact-equality regression. The final complete SDK-backed
rerun passed as recorded above.

## Source and artifact inventory

| Repository | Source checkpoint |
| --- | --- |
| aosedge-sdv-demo | Source return point: `checkpoint/staging-20260915`; exact peeled commit is available from the Git tag |
| carla-ego-runtime | `da5038d` on public main |
| aos-vehicle-platform | `ecf926f` on public main; `.33` image still uses its original build source |
| brake-health-service | `76d80e9`, clean and equal to origin/main |
| tire-health-service | `fc81a37`, clean and equal to origin/main |
| brake-health-cloud | `da7ee6b`, clean and equal to origin/main |
| tire-health-cloud | `76a5cd2`, clean and equal to origin/main |

Return-point tag for the changed repositories: `checkpoint/staging-20260915`.
Only reviewed source, tests and English documentation are included. No images,
overlays, compiled executables, deployment bundles, certificate/key material,
runtime journals, local account configuration or generated test reports enter Git.

The main CARLA/Unreal source trees have no tracked changes for this increment.
Unreal is a licensed upstream dependency, not a newly created public demo repo.
Historical scratch/build folders and old worktrees are excluded and not deleted.
In particular, the old `brake-health-service-imp-04-bhs-core-v3` worktree has six
untracked experimental V3 files differing from current main; they are not part
of the active build and are not silently promoted over the qualified service.
The old `aos-vehicle-platform-stage-a-runtime-credential-template` directory has
invalid worktree metadata; it is not an active source checkout. These require a
separate scoped housekeeping decision, not a broad `git add` or deletion.
Historical workspace/lock pins remain a separately documented reconciliation
gap; this checkpoint does not claim fresh-clone reproducibility from those pins.

## Open boundaries and next phase

1. **Staging KUKSA permissions:** the operator reports the platform fix may be
   available there. Actual upload with permissions, workload authorization,
   telemetry reads and advisory writes have not been qualified. Production
   remains excluded. Do not relabel synthetic backend data as vehicle telemetry.
2. **Publication processing:** VDP58 previously reached Ready/installed on staging.
   Later VDP59–61 were observed accepted/processing without parsed items. The
   Cloud UI's empty-bundle message alone did not establish archive corruption.
   Prior archive/signature comparison found no demonstrated packaging defect;
   the Cloud processing cause remains unproven at the latest captured read.
   The operator's present working-state report is not invented worker-log proof.
3. **Service delivery:** the earlier first-use receipt records Ready versions and
   assigned Subjects without service items in Desired Status. The next real
   service run must confirm delivery and execution rather than reuse that old
   receipt as a pass.
4. **CM/Cloud recovery:** `.33` retains the documented idle full-status workaround.
   Successful Offline/retirement cycles do not prove a permanent Cloud-side fix.
5. **UI follow-ups:** native CARLA window placement after the host reboot remains
   deferred; the initial active-operation Trace gap has dated evidence but no
   claimed fix in this checkpoint. CARLA rendering itself is unchanged.

After source publication, the next bounded work is to verify the staging
permissions contract, agree the explicit real-data profile in CLI and Presenter,
then qualify Brake followed by Tire using native Aos workload authorization and
the existing input/token placement. Preserve dedicated Subjects, SP publication,
automatic releases, service updates without Safe Stop and VDP updates with Safe
Stop. No speculative SM/CM modification, shared token or authentication bypass
is implied. This document does not start that implementation or allocate releases.

Related: [delivery plan](../planning/active/demo-studio-delivery-plan.md),
[current Factory baseline](current-baseline.md),
[first-use staging receipt](first-use-cloud-configuration-audit-2026-09-15.md),
[unsigned-package receipt](unsigned-package-signing-2026-09-15.md),
[native Aos service-input decision](../architecture/decisions/0015-use-native-aos-service-runtime-inputs.md).
