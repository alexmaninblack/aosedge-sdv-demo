<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 Platform Readiness Work Packet

- ID: `WP-P0-PLATFORM-001`
- Lane: `L-PLATFORM`
- Parent increment: `IMP-03`
- Review state: `COMPLETED — BASELINE_ACCEPTED`; code packets remain `BLOCKED`
- Version: 0.4
- Prepared: 2026-08-27
- Updated: 2026-08-28
- Accepted: 2026-08-28
- Execution authorized: yes — P0 read-only assessment and local tests only
- Authorized: 2026-08-28
- Product implementation, Yocto/image/component build, signing, Cloud, VM or
  Unit mutation authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Freeze the truthful Platform baseline and produce the exact future code-packet
decomposition for Factory Assembly, OEM Component Runtime, removable KUKSA
authorization compatibility helper and VDP v1-v3. P0 must not implement the
target or silently treat newer local documentation as an accepted product
revision.

## P0 Execution Result

- Completed: 2026-08-28
- Exit state: `BASELINE_ACCEPTED`
- `IMP-03` implementation state: `BLOCKED`

P0 first selected `5c2a7d0704fac93ba0a285cf533c17847d88633e` as the
source-evidence candidate because its delta from the previous accepted
revision was documentation-only. The accepted reconciliation then aligned the
Platform documentation to the current KAC, trusted Provider and Factory
boundaries and produced final baseline
`bdc72aba97a83c9868d454588189ef139710a6d7`. Platform `main` and `origin/main`
are equal at that revision, and the solution repository pin/evidence cascade
records it. The historical `.11` image and Provider `0.2.0` artifact pins
remain immutable and were not repinned to this documentation revision.

All P0-frozen requirement/contract digests and preserved `.11` artifact digests
matched during the read-only assessment. After package acceptance, the four
requirement files were deliberately repinned below. At the final Platform
baseline, 35 Python tests and the quality gate for 82 tracked files passed. No
product source, recipe, image, component, key, JWT, Cloud, VM or Unit operation
was performed.

Reusable current implementation evidence includes the provider-specific A/B
runtime, bounded 512 MiB ext4 store, fixed `aos-vdp` identity, systemd/SELinux
boundaries and the seven-path inbound Provider. The following target behavior
is absent and must not be presented as implemented:

- factory configuration with `enablePermissionsHandler: true`;
- the removable `authorization/aos-kuksa-compat/` package and all KAC signer,
  verifier, permission-mapping and JWT-lifecycle behavior;
- OEM Component Runtime `WaitingForSafeStop` application gating;
- VDP v2/v3 capability increments, typed outbound advisory path and complete
  readiness/resource recovery; and
- exact selected-Unit mTLS and trusted OEM Provider integration.

The future Platform work remains decomposed into three independently reviewed
code packets: KAC, successor Factory/runtime and VDP v1-v3. `CR-FACTORY` 0.4,
`CR-KAC` 0.8, `CR-VDP` 0.8 and `CR-CROSS` 0.4 were accepted on 2026-08-28.
Implementation remains blocked until the exact IAM ownership, KUKSA/Provider
connection, selected-Unit credential, Safe Stop adapter, packaging and
artifact parameters are accepted. Platform/VDP design review may continue in
parallel with any separately authorized UI and Vehicle/Gateway implementation
lanes.

## Repository and Baseline Gate

| Item | Value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Accepted workspace revision | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Current clean local `main` | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Remote relationship | `main` equals `origin/main` |
| Future branch | `codex/imp-03-platform-vdp`, only after package and base acceptance |
| P0 writable paths | none |

The original three candidate commits were:

1. `51d3fce` — factory and rootfs artifact clarification;
2. `03c3065` — native Aos IAM credential-lifecycle documentation; and
3. `5c2a7d0` — QM Gateway boundary documentation.

The accepted reconciliation commit `bdc72ab` updates those five documentation
files and adds the planned `authorization/aos-kuksa-compat/README.md` boundary.
It contains no product-code, recipe, configuration or artifact delta. The
repository remote and solution lock are reconciled; a future code packet may
use the accepted revision only after its remaining implementation parameters
are frozen.

## Design Gates

The latest packages were design-reviewed on 2026-08-28:

- [Factory Substrate 0.4](../../../requirements/components/factory-substrate.md);
- [KUKSA Authorization Compatibility 0.8](../../../requirements/components/kuksa-authorization-compatibility.md);
- [Vehicle Data Platform 0.8](../../../requirements/components/vehicle-data-platform.md); and
- [Cross-Cutting 0.4](../../../requirements/components/cross-cutting.md).

Their acceptance freezes architectural requirements but does not authorize
implementation. Exact package-owned implementation parameters remain the
`IMP-03` gate.

## Frozen Requirements and Contracts

- `REQ-FACTORY-001` through `011`, `UT-FACTORY-001` through `009`;
- `REQ-KAC-001` through `010`, `UT-KAC-001` through `010`;
- `REQ-VDP-001` through `011`, `UT-VDP-001` through `008`;
- `REQ-CROSS-001`, `002`, `004`, `010` and the applicable owner-package tests;
- `IF-AUTH-007` through `010`, `IF-VEH-005`, `IF-DATA-001`,
  `IF-ADV-001` through `005`, `IF-LC-001` and `IF-LC-006`.

| Frozen file/contract | SHA-256 |
| --- | --- |
| Factory Substrate requirements | `168bbcc075baee6ace66fa2468cfc7f0953efe31a2baa8437bcd259e12602cef` |
| KAC requirements | `9cc4f459caeba4724bf7217c8cdb113190e216ea8d977e429ae296f2007e42ae` |
| VDP requirements | `c6ab37f26d188ca6f887e3f9c8325bb72511a4047cbcbca844fce9ba7719c959` |
| Cross-Cutting requirements | `419c4ea1c75c08c553565c3ad168bf6ff167ac439db1709d288572caee650175` |
| KUKSA current-demo authorization v1 | `0b1d407a40208aa7135f45d0ba83ce9064cde321d652e1b6ebdf1a1f5b175972` |
| VDP Compatibility v1 | `4c00a3848eb2c961b048e74d3d1253bdc43e47c1467f64e62653046ba39ba12c` |
| VISS Trust and Telemetry v1 | `24484919d916ade153111fd6075d06cecdf77d0bed7cfd016c0a4163e1b8fd53` |
| QM Advisory v1 | `5f50d5f27693d31a9726e78d52b5a039a43f9fa4e0368cac2fc7571508487614` |
| Platform FOTA Safe Stop v1 | `b2a84027ab0465b034c236a8ecbf7cd50edbb1851453c8f0b1066be9af2a69b8` |

## Exact P0 Tasks

1. Confirm repository cleanliness, both revisions, the five-file docs-only
   delta and every frozen digest.
2. Compare the accepted revision with current `main`; recommend one exact base
   and list every workspace lock, component evidence and documentation pin
   that would need an accepted update. Do not make that update.
3. Inventory current Factory/runtime/provider/KUKSA integration source and
   tests at the recommended base. Distinguish reusable evidence from target
   behavior that does not exist.
4. Prove whether the current factory inputs already contain
   `enablePermissionsHandler: true`, the provider-specific empty-slot A/B
   runtime, bounded store, systemd/SELinux boundaries and no provisioned
   identity or pre-populated Service authority.
5. Inventory the planned removable `authorization/aos-kuksa-compat/` boundary,
   per-Unit signer/verifier preparation and JWT lifecycle. Record missing
   source explicitly; do not reuse the historical `authorization/aos-kuksa/`
   notes as an implementation.
6. Map VDP v1-v3, trusted Provider integration, typed outbound QM advisory and
   fresh Safe Stop application gate to exact source/test deltas.
7. Decompose `IMP-03` into smallest repository-owned code packets with exact
   paths and tests. At minimum separate successor Factory/runtime, KAC and VDP
   work where their package/lifecycle identities differ.
8. Return the unresolved package decisions and exact acceptance needed before
   each code packet may change from `BLOCKED` to `READY_FOR_REVIEW`.

## Baseline Checks

```text
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/quality_gate.py
```

Baseline evidence on 2026-08-28: 35 tests passed and the repository quality
gate passed for 82 tracked files at accepted `bdc72ab`. These checks do not
prove the target Factory Image, KAC, Safe Stop runtime or VDP v1-v3, and no
image or component was built.

## Forbidden Work

- no source, recipe, configuration, requirement, contract or lock update;
- no branch push or assumption that local-ahead commits are remotely accepted;
- no Yocto, VM image, provider component or FOTA build;
- no signing, upload, AosCloud, Unit, VM, provisioning or live qualification;
- no generated key, JWT, shared verifier, identity or secret; and
- no OEM Component Runtime behavior implemented before the package gates close.

## Completion Packet

The worker returns:

1. exact base recommendation and complete pin-update impact;
2. confirmed baselines, digests and repository status;
3. requirement/test-to-source delta matrices for Factory/runtime, KAC and VDP;
4. current reusable evidence and explicit missing target behavior;
5. exact proposed code packets, branches, worktrees, writable paths, tests and
   build-output boundaries;
6. package decisions still required before authorization;
7. baseline test results and environment limitations;
8. change requests or blockers; and
9. confirmation that no forbidden operation occurred.

## Exit and Escalation

P0 exited `BASELINE_ACCEPTED` at
`bdc72aba97a83c9868d454588189ef139710a6d7` with reconciled remote/main state
and updated solution pins. `IMP-03` remains `BLOCKED` until each exact KAC,
Factory/runtime and VDP code packet is accepted. Any product-code delta,
missing immutable evidence, contract conflict or need to build, sign or use a
VM before its separate gate is escalated to the Platform owner and Integration
Coordinator.
