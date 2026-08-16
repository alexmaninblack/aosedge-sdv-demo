<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R3 — VM Recovery, Checkpoints, and Unit Identity

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream evaluates whether protected VM checkpoints can support a
repeatable demonstration reset while preserving provisioned Unit identities,
and identifies the Cloud and external state that a disk restore cannot reset.

## Current evidence

Both Unit roles have private mode-`0600`, standalone, integrity-checked
pre-provision and post-provision checkpoints. Both lifecycle records verify and
report `provisioned`. Both active overlays are healthy qcow2 files with clean
dirty flags and the expected immutable upstream backing image.

The launcher intentionally has no command to restore a provisioned checkpoint
and rejects destructive reset for provisioned overlays. Checkpoint creation
requires a stopped VM and produces a standalone image. These safeguards are
correct because provisioning changes both guest disk state and AosCloud state.

## Findings

| Finding | Classification |
| --- | --- |
| Complete integrity-checked disk recovery assets exist separately for both Unit identities. | **PROVEN** |
| The checkpoints contain provisioned identity and credential state and must remain private. | **PROVEN** |
| Current tooling deliberately prevents treating these backups as ordinary demo reset points. | **PROVEN** |
| A restored disk cannot restore AosCloud desired state, batch history, backend data, ELK data, dashboard caches, or CARLA state. | **PROVEN** |
| On reconnect, AosCore reports actual state and reconciles toward the Cloud's complete current desired state. | **PROVEN** |
| If Cloud still desires G4, a disk restored to G0 may immediately start reconverging toward G4. | **INFERRED** |
| Existing post-provision checkpoints are recovery evidence, not proven G0 golden images. | **INFERRED** |
| Running two VM copies with the same provisioned identity is unsafe and must be prevented. | **INFERRED from uniqueness requirement; duplicate behavior is unqualified** |

## Why a checkpoint is not a rollback

```text
VM checkpoint contains
  guest filesystem + AosCore databases + Unit keys/certificates

VM checkpoint does not contain
  AosCloud desired graph + verification/campaign state
  Function Backend events
  ELK indices and downloaded archives
  dashboard caches
  CARLA scenario seed and actors
```

FOTA also has a transaction boundary: official AosCore documentation permits
`RevertUpdate` before `ApplyUpdate`; after Apply, that transaction is committed.
Restoring an older qcow2 file after that point is out-of-band recovery, not an
AosEdge FOTA rollback.

## Recommended two-layer reset strategy

### Primary — platform-native desired-state transition

Use normal Cloud desired-state removal or a forward reset release if R2 proves
the full dependency-safe G4-to-G0 sequence. This preserves identity, active
disk continuity, and Cloud audit history.

### Fallback — protected per-Unit golden G0

Maintain one immutable golden image for Validation and a different one for
Demonstration. Create them only after:

- the common G0 rootfs is accepted;
- Cloud desired and Unit actual state both equal the version-controlled G0
  manifest;
- no update is pending;
- certificates and identity continuity are healthy;
- all feature payload, service state, and generated demo data are absent.

Each golden manifest should record only sanitized metadata: Unit-role identity
hash, rootfs version, G0 graph digest, certificate generation/validity metadata,
checkpoint digest, and creation time. Golden images remain encrypted/private,
outside Git, and are never booted directly.

Restoration is permitted only when:

1. the previous child VM is cleanly stopped and made non-runnable;
2. Cloud desired state is already G0, or the restored VM remains network
   isolated;
3. a new disposable child is created for the same Unit role only;
4. no second copy of that identity can start;
5. external demo state is reset separately.

This mechanism belongs to a **Demo Recovery Controller** on the workstation,
outside the logical vehicle and outside the production HLA.

## Options and trade-offs

| Option | Benefit | Risk or limitation |
| --- | --- | --- |
| Native desired-state reset | Preserves identity and audit continuity | Applied component removal/downgrade remains unproven |
| Higher-version reset component | Compatible with monotonic versioning | Leaves reset history and does not clear service/backend data alone |
| Golden G0 per Unit | Fast and deterministic guest restoration | Cloud conflict, stale certificates, and duplicate identity risk |
| New Unit for every run | Clean state | Slow, changes identity, and weakens the lifecycle story |

## Required experiments

### E1 — offline checkpoint provenance

Use Validation only. Stop the original, verify hashes, make it non-runnable,
boot a restored copy with networking disabled, record sanitized state, stop and
verify it, then restore the unchanged original. Never run both copies.

### E2 — accepted G0 golden creation

After R1/R2 establish G0, reconcile Cloud and Unit to G0, verify certificate
health and no pending update, stop cleanly, create a standalone golden image
and sanitized manifest, then create a disposable child while archiving the
prior active disk as non-runnable.

### E3 — reconnect reconciliation

Boot the Validation child network-isolated, prove local G0, independently
confirm Cloud desires G0, then enable connectivity. Observe Unit status upload,
desired-state response, certificate behavior, unexpected deployments, pending
state, identity continuity, and time to Online/G0-ready.

### E4 — reset after a staged graph

Advance Validation through a harmless G1/G2 fixture. First test the R2 native
reset path, then the golden fallback. Compare reverse dependency order,
duration, determinism, logs, residual state, and identity/certificate behavior.
Do not involve Demonstration until accepted.

Duplicate identity guards must be tested with mock metadata or unprovisioned
VMs first, never by connecting two provisioned copies.

## Cross-system reset requirement

A complete demo reset includes all of the following:

- AosCloud target and pending lifecycle state;
- Validation and Demonstration VM actual state;
- Brake Health service persistent storage and pending functional events;
- Function Backend demo records;
- ELK demo indices or filters;
- dashboard caches and run selection;
- deterministic CARLA world, actor state, and scenario seed.

## Impact on planning

The scenario's reset outcome remains a requirement but is not demonstrated.
The implementation plan must treat native reset and golden restore as separate
qualification paths, require identity exclusivity and Cloud reconciliation,
and never describe snapshot replacement as production rollback.

## Sources

- [Single-node provisioning and checkpoint policy](../../operations/single-node-provisioning.md)
- [VM relocation and identity repair evidence](../../qualification/repository-rename-vm-repair.md)
- [AosCore Unit status reconciliation](https://docs.aosedge.tech/docs/aos-core/architecture/cm/unit-status-handler)
- [AosCore deployment flows](https://docs.aosedge.tech/docs/aos-core/deployment-flows)
- [AosCore Node identity](https://docs.aosedge.tech/docs/aos-core/architecture/identity-access-manager/node-identity)
- [QEMU disk image documentation](https://www.qemu.org/docs/master/tools/qemu-img.html)
