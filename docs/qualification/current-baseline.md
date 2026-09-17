<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current working baseline

Updated: **17 September 2026**. Retained Factory: **.35**. New Vehicle overview
UI integration is on hold until the audit checkpoint is complete and the operator
authorizes that work. This supersedes the former .33 current status; historical
receipts and the previous page remain in Git history.

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
passed; **a clean first-Provision run of this latest amendment is still open**.
The earlier .35 cycle must not be used as evidence that it passed the new order.

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
