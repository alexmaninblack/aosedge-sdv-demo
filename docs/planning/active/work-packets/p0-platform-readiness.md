<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 Platform Readiness Work Packet

- ID: `WP-P0-PLATFORM-001`
- Lane: `L-PLATFORM`
- Parent increment: `IMP-03`
- Review state: `ACCEPTED`; code packet remains `BLOCKED`
- Version: 0.2
- Prepared: 2026-08-27
- Updated: 2026-08-28
- Accepted: 2026-08-28
- Execution authorized: no
- Product implementation, Yocto/image/component build, signing, Cloud, VM or
  Unit mutation authorized: no
- Parent plan: [Demo Implementation Plan 1.1](../demo-implementation-plan.md)

## Objective

Freeze the truthful Platform baseline and produce the exact future code-packet
decomposition for Factory Assembly, OEM Component Runtime, removable KUKSA
authorization compatibility helper and VDP v1-v3. P0 must not implement the
target or silently treat newer local documentation as an accepted product
revision.

## Repository and Baseline Gate

| Item | Value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Accepted workspace revision | `15b6abb7562b4d0fd4628817e1046ea95b047a0c` |
| Current clean local `main` | `5c2a7d0704fac93ba0a285cf533c17847d88633e` |
| Remote relationship | local `main` is three commits ahead of `origin/main` |
| Future branch | `codex/imp-03-platform-vdp`, only after package and base acceptance |
| P0 writable paths | none |

The three local commits are:

1. `51d3fce` — factory and rootfs artifact clarification;
2. `03c3065` — native Aos IAM credential-lifecycle documentation; and
3. `5c2a7d0` — QM Gateway boundary documentation.

The diff from the accepted revision changes only `README.md`,
`authorization/aos-kuksa/README.md`, `docs/aos2-provider-design.md`,
`docs/architecture.md` and `meta-aos-vehicle-platform/README.md`. P0 must still
decide explicitly whether `5c2a7d0` becomes the new accepted repository base
and identify the exact Level B pin/evidence updates. It must not push or update
the workspace lock.

`5c2a7d0` is the preferred baseline candidate because the repository is clean,
the delta is documentation-only and the current repository tests and quality
gate pass. P0 accepts it as the new evidence baseline only after independently
confirming those facts and producing the complete pin cascade. The Platform
`main`, remote and solution locks must then be reconciled through one reviewed
documentation change before a code branch is created. Any product-code delta
or evidence mismatch retains `15b6abb` and opens a bounded change request.

## Design Gates

The latest packages remain review candidates and therefore block a code
authorization:

- [Factory Substrate 0.4](../../../requirements/components/factory-substrate.md);
- [KUKSA Authorization Compatibility 0.8](../../../requirements/components/kuksa-authorization-compatibility.md);
- [Vehicle Data Platform 0.8](../../../requirements/components/vehicle-data-platform.md); and
- [Cross-Cutting 0.4](../../../requirements/components/cross-cutting.md).

P0 may identify exact parameters and inconsistencies but cannot declare these
packages accepted.

## Frozen Requirements and Contracts

- `REQ-FACTORY-001` through `011`, `UT-FACTORY-001` through `009`;
- `REQ-KAC-001` through `010`, `UT-KAC-001` through `010`;
- `REQ-VDP-001` through `011`, `UT-VDP-001` through `008`;
- `REQ-CROSS-001`, `002`, `004`, `010` and the applicable owner-package tests;
- `IF-AUTH-007` through `010`, `IF-VEH-005`, `IF-DATA-001`,
  `IF-ADV-001` through `005`, `IF-LC-001` and `IF-LC-006`.

| Frozen file/contract | SHA-256 |
| --- | --- |
| Factory Substrate requirements | `3e9459f1ccf30565ef043c929ab2348ccb725c01b2995d5873ee13a0da11d8a8` |
| KAC requirements | `6613bb1a70be031958244c0a8aa97789eced86d8bc90f4e5faaf43bf119541d2` |
| VDP requirements | `94a655608456c136e53cfc5631254b79f96798989bb5863f3b2caebf56587320` |
| Cross-Cutting requirements | `2ba07bef40674097410e1c601e34a67c7aa7b77fcda1c186bd4d9d29d54de403` |
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

Baseline evidence on 2026-08-27: 35 tests passed and the repository quality
gate passed for 81 tracked files at local `5c2a7d0`. These checks do not prove
the target Factory Image, KAC, Safe Stop runtime or VDP v1-v3, and no image or
component was built.

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

P0 exits `BASELINE_READY` when one repository revision and its pin cascade are
unambiguous. The expected result is accepted `5c2a7d0`, reconciled remote/main
state and updated solution pins; otherwise the packet retains `15b6abb` with a
change request. `IMP-03` remains `BLOCKED` until the latest Factory, KAC, VDP
and Cross-Cutting packages and each exact code packet are accepted. A code
delta between the two candidate revisions, missing immutable evidence,
contract conflict or any need to build/sign/use a VM is escalated to the
Platform owner and Integration Coordinator.
