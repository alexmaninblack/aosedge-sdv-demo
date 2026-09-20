<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current working baseline

Updated: **20 September 2026**. Retained Factory: **.35**; clean-cycle image
**.36**, both immutable and preserved. Vehicle overview integration and latest
Presenter corrections are activated. The corrected continuous UI cycle has
completed; broader qualification exclusions remain explicit. See the
[active packet](../planning/active/work-packets/versioned-service-observability.md).
The former UI hold and .33 current status are historical, not active blockers.

## Current qualification limitation

Latest targeted checkpoint: **20 September09:02UTC**, the same .36 Test is retained
in staging, Online and Safe Stop with external network ON. The operator approved
VDP97/V3, Brake77/V3 and Tire43/V1; all are installed and real products and both
native warnings were observed. Moving/double-click Return to road and exact
offline delivery of54 captured messages passed. Subsequent live Reset checks
covered a concurrent-action rejection, an accepted command expiring offline,
reload without resubmission, no late application after reconnect, an explicit
new successful Brake Reset and a stale Tire confirmation rejected without a
command. Brake then produced a new Monitor40 result; native Brake is Monitoring
and Tire retains Inspection recommended. T15 corrects misleading pending/expired
Reset copy; its rebuilt UI is verified in the browser, not a separately reloaded
native Presenter wrapper. This is a targeted follow-up,
not another full version progression or a completed Finish. T13 Presenter copy
is active; T14 native preflight copy is source-tested, not yet activated in the
running Driving Control. Remaining gates are listed in the
[single timing report](presenter-ui-timing-e2e-2026-09-20.md#targeted-follow-up-after-the-completed-cycle).

Previous full completion: **20 September06:46UTC**, then no active Test. The full recorded
UI-only operator cycle after T10 reached VDP94/95/96, Brake73/74/75 then76,
Tire42, real products, inherited and new advisories, independent resets,
five-minute OFF/local operation, reconnect/backlog and confirmed Finish.
The initial UI returned within58s of the Finish click. Latest build includes
T11 product-history/advisory explanation and T12 empty-lifecycle layout copy.
See the [single timing report](presenter-ui-timing-e2e-2026-09-20.md) for gates,
upper-bound timing methodology and unexecuted branches. The .36 manifest is not
silently promoted to fully qualified; guest reboot and broader negative matrix
remain separate. Production, images and release continuity are preserved.

## Historical qualification checkpoints through 19 September

Latest UI follow-up: the operator approved U1–U5 from the repeat flow/status
audit. The [correction record](presenter-ui-reaudit-fixes-2026-09-19.md) records
implementation, local gates and Presenter activation separately from live demo
qualification. The retired Test remains absent; no image or service package is
changed by these UI/read-path fixes.

Latest local work: all UI truth-audit corrections were selected, including
previously optional presentation items. See the
[correction record](presenter-ui-truth-fixes-2026-09-19.md) for tests, deployment
status and exclusions. This supersedes the earlier request to select remaining
UI follow-ups; it does not qualify new service packages or a fresh P8 cycle.

Latest completion, 19 September 17:29:30 UTC: the .36 Test was retired after
exact approval. Finish completed in 42.01 seconds; Cloud absence, local overlay
removal and the empty Presenter state were verified. No active Test remains.
Both .35 and .36 originals are preserved; .36 is not promoted to full clean
qualification while its recorded defects and unexecuted branches remain.
The next step is [review and selection of follow-ups](factory-36-follow-up-review-2026-09-19.md),
not a source change or another run without that selection.

Latest live checkpoint, 19 September 17:23 UTC: Factory .36 is running the
current staging Test with VDP85/V3, Brake66/V3 and Tire39/V1. The
[.36 run](factory-36-e2e-2026-09-19.md) passed the observed version progression,
real products, independent Reset/CLEAR, model/pending-byte retention through
replacement and CM cleanup, network OFF/ON without manager restart, exact
backlog delivery and stationary Return to road. Final retirement is awaiting
an exact tool-safety confirmation. Source-gap/UI follow-ups and unexecuted
matrix branches remain open; .36 is not promoted to fully qualified. The .35
immutable artifact is retained for rollback. Bare guest reboot and its
engineering recovery are a [separate check](factory-36-guest-reboot-2026-09-19.md).
The earlier limitation descriptions below are historical context.

An earlier retained Test had VDP79/V3, Brake60/V3 and Tire35/V1. Targeted real products,
reset/CLEAR and offline queued delivery passed before Park/Resume exposed
native CM shared-storage loss. Earlier `.35` startup/Online checks did not
compare that model/producer continuity and cannot close it. See the
[live evidence](preserved-test-function-observation-2026-09-19.md).

[ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md)
removes operator Park/Resume. The subsequent
[continuous clean cycle](continuous-factory-35-e2e-2026-09-19.md) reached all
software profiles but exposed a separate CM connection deadlock. The bounded
connection correction passed live OFF/ON; its restart reproduced storage loss.
The operator then authorized a storage fix. Its
[local tests and new Factory .36 build](cm-shared-storage-fix-2026-09-19.md)
passed. The .36 artifact manifest remains **BUILT_NOT_LIVE_QUALIFIED** pending
complete acceptance; its later live evidence is summarized above. Existing
`.35` native patches remain inventoried; neither image is stock mainline.
Complete P8 acceptance remains open.

## Immutable Factory

| Item | Value |
| --- | --- |
| Selector | `6.1.1-maninblack.35/main-qemuarm64` |
| Artifact relative to workspace | `demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.35/main-qemuarm64.img` |
| SHA-256 | `668690a922d62f158c60769cab673ca9cac1ccb7fde7dee2c7cd22dd9952a458` |
| Image size | 6,997,147,648 bytes |
| Platform build source | `bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74` |

This digest/build source is immutable. Later source, documentation, host and
service-package commits do not retroactively alter the Factory image.

## Qualified behavior and later corrections

The [clean .35 staging cycle](factory-35-e2e-2026-09-17.md) passed by 05:32 UTC:
VDP74/V1 → 75/V2 → 76/V3, Brake53/V1 → 54/V2 → 55/V3, Tire32/V1, actual KUKSA
reads, real backend results, both native warnings and independent reset/CLEAR/
renewed-warning chains. Cloud Offline/Online, first-attempt packaged Park/Resume
and final Finish/deprovision/delete passed. CLI maneuvers supplied physical
stimuli; lifecycle, publication and observation used Presenter/native UI.
This is not UI-only test stimuli or complete visual acceptance.

The subsequent preserved Test uses .35 with VDP78/V3, Brake58/V3 and Tire34/V1
in the dated [attachment-order evidence](source-attachment-order-2026-09-17.md).
Brake V3 and Tire V1 are compatible advisory producers; there is no Tire V3
requirement. Both services use the native gRPC hosts resolver to keep local
KUKSA reconnect independent of external-network availability.

The [manual-control/cache evidence](manual-control-and-map-cache-2026-09-17.md)
records bounded first-command handling, bridge recovery and explicit Unreal
map-cache preparation. Native caches are preserved. No simulator texture cache
or compiled shader rebuild is required on each normal start.

The latest attachment order is Create/boot → start local simulation detached →
publish → Provision/Cloud Online → authenticate and attach the same Gateway in
stationary Manual → operator Safe Stop. Focused tests and preserved-run reuse
passed; the20September UI cycle now also passed the clean first-Provision order
without restarting the already-running simulator. The earlier.35 cycle is not
used as evidence for that later amendment.

## Current boundaries

- Native telemetry reads Gateway/VISS only; backend and Unit reports are
  distinct evidence, not a substitute for a confirmed vehicle advisory.
- Component application requires Safe Stop. Service installation does not.
- Staging permissions/real KUKSA work with the qualified 256-character CM/SM/IAM
  capacity and IAM response correction. Production Cloud parity and upstream
  acceptance remain separate; no production platform fix is claimed.
- CM idle full-status recovery is a guest workaround, not a Cloud queue fix.
- Production stays excluded. Its dormant .31 backing is a separately recorded
  cleanup dependency, not an available Test catalog baseline.
- The [pre-UI checkpoint audit](pre-ui-checkpoint-2026-09-17.md) records source
  publication, housekeeping, test results and remaining gates.

Git restores source, not Cloud identity, VM contents, credentials or release
allocation. Never restore an old release ledger to replay this source.

The [20 September source checkpoint and cleanup receipt](source-checkpoint-and-cleanup-2026-09-20.md)
pins the published integration and its dependency revisions. These source pins
do not change immutable Factory provenance or promote broader qualification.
