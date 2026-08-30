<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current Accepted Baseline

- Recorded: 2026-08-30
- Factory baseline: `6.1.1-maninblack.21`
- Scope: immutable OEM Demo Factory Image, one qualified Test Vehicle Unit,
  pinned demo Cloud topology and VDP source/artifact boundary
- Cloud mutation status: `.21` is assigned to the Test Vehicles Unit Set;
  the Production Vehicles Unit Set is intentionally empty

## Accepted OEM Demo Factory Image `.21`

| Item | Accepted value |
| --- | --- |
| Platform source revision | `667afb1512cf43ff27f1ab5327293208bf73045b` |
| Platform source tree | `164f907bf041dbc99df24d2ebe7b0e5d2bbaeab0` |
| Image version | `6.1.1-maninblack.21` |
| Raw image size | `6,997,147,648` bytes |
| Raw image SHA-256 | `80e0c0dc4f7f9c51a25d3461047e2e3d85bf540059c7052af3944ce8650e19e1` |
| Frozen rootfs SHA-256 | `32290e8f45632b3993ef0dc61b23be8a508bfd4d94f97f6ab65c80cbbad8d00b` |
| Factory payload state | Provider-specific runtime present; VDP slot empty |

`.21` is the current accepted Factory baseline for fresh read-only backing
images and new copy-on-write overlays. It supersedes `.11` as the current
candidate. It does not turn a provisioned overlay or Cloud Unit into a
manufacturing source.

The accepted evidence includes an offline Enforcing boot with restricted QEMU
networking, correct unprovisioned lifecycle gating, no VDP payload, no scoped
AVCs and clean shutdown. The single official SDK provisioning attempt then
succeeded. In normal mode IAM, CM, SM, TLS preparation, KUKSA verifier,
Provider credential preparation, authorization helper and broker all reached
the expected successful state with zero restarts. Provider credential
first-create and idempotent reuse both completed with clean teardown, the
strict TLS/JWT KUKSA read returned `Vehicle.Speed: NotAvailable`, and the final
scoped AVC set was empty. `NotAvailable` is the required Factory result because
no VDP component is installed to publish a value.

The retained local Builder, package manifest, candidate/rootfs digests,
offline evidence, provisioning checkpoints and online evidence remain outside
Git. A controlled same-source reproducibility rebuild remains a separate
D4-001 dossier obligation; it does not change which immutable image is the
accepted working Factory baseline.

## Qualified Test Vehicle Unit

| Cloud identity | Accepted value |
| --- | --- |
| Unit UUID | `ba74a1e6-5496-496b-8e4b-e8beb0af27ad` |
| `system_uid` / native Node ID | `7cec239e6ab348b4b1c7961186cfd978` |
| Primary Main Node UUID | `4f3be6c7-d50e-4c60-ab39-db25a6614358` |
| Unit state at acceptance | `provisioned` / `Online` |
| Node state at acceptance | `provisioned`, primary `aos-vm-main` |
| Demo role | Test Vehicle |

This Unit is qualification evidence for `.21` and the current Test Vehicle
lane. It is not the Factory Image itself and is not a Production Vehicle.

## Persistent Demo Cloud Topology

These objects were created once through the OEM/AosCloud administrative
bootstrap and authoritatively validated on 2026-08-30. Their identifiers are
pinned configuration, not values inferred from titles. The documentation
provenance checkpoint that first recorded the live identifiers is `661868c`.

| Cloud object | Exact title | UUID | Invariant |
| --- | --- | --- | --- |
| Fleet | `AosEdge SDV Demo Fleet` | `52cadaf9-5294-4d32-937f-16e3f441b81b` | Persistent demo Fleet |
| Test role Unit Set | `AosEdge SDV Demo / Test Vehicles` | `a3399102-3b62-4874-89a4-f2a0206b9ea7` | `is_validation_set=true`; contains the current `.21` Test Unit |
| Production role Unit Set | `AosEdge SDV Demo / Production Vehicles` | `a8bfc280-1146-4b99-90cf-3058a5e21730` | `is_validation_set=false`; currently empty |

The Demo Orchestrator verifies these three persistent objects and manages only
run-scoped Unit membership. It never creates, renames, reconfigures, moves or
deletes the Fleet or Unit Set definitions.

## VDP Source and Artifact Boundary

The VDP v1-v3 source family is implemented and integrated into the accepted
`.21` platform source history:

| Item | Current state |
| --- | --- |
| Source-complete checkpoint | `67123333775a696a1143d0281013651b3736f0fd` |
| Integrated platform commit | `f565251` (`Implement immutable VDP v1-v3 source family`) |
| Accepted containing source | `667afb1512cf43ff27f1ab5327293208bf73045b` |
| v1/v2/v3 prepared component artifacts | Absent |
| Signed/published AosCloud component artifacts | Absent |
| Installed VDP in Factory baseline or Test Unit | Absent |

Source integration is therefore complete, but artifact production is not.
No VDP v1/v2/v3 ARM64 candidate, canonical artifact/metadata digest,
signature, publication identity or FOTA installation may be claimed yet.
Artifact build, qualification, signing, publication and Test-to-Production
promotion remain later explicit lifecycle steps. The Factory image must keep
the VDP slot empty.

## Superseded and Historical Evidence

`.1`, `.2`, `.11`, provider `0.2.0` and the intermediate `.17`-`.20` images
remain historical engineering and debugging evidence only. In particular,
`.11` is not the current Factory candidate or baseline. Its qualification
records may retain exact historical version, digest and behavior statements;
they shall not be used as current M0 input or Cloud deployment authority.

The legacy and intermediate Cloud Units and their large local IMG/QCOW2
artifacts were retired under explicit authorization. Git history, compact
logs, manifests and the warm Builder/caches were preserved.

## Next Authorized Boundary

The next Platform step is to build and qualify the already integrated VDP
source as three immutable post-SOP component FOTA candidates. This baseline
record does not authorize signing, Cloud publication, deployment, Production
membership or rollout. Those actions remain governed by the accepted
Platform, Demo Orchestration and release-lifecycle gates.
