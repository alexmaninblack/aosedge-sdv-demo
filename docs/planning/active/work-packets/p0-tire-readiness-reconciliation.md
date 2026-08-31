<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 Tire Acceptance and Baseline Reconciliation Work Packet

- ID: `WP-P0-TIRE-001`
- Lane: `L-TIRE`
- Parent increment: `IMP-05`
- Review state: `COMPLETED — DESIGN_BASELINE_RECONCILED`
- Version: 1.0
- Prepared and authorized: 2026-08-31
- Execution authorization: solution-document reconciliation only
- Repository creation, product implementation, calibration, CARLA, network,
  signing, Cloud, VM or Unit action authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Reconcile the already accepted D4-018/D4-019 product contracts and accepted
D4-027 authorization boundary into the CR-TIRE and CR-TIRE-CLOUD requirement
baseline without changing any model value or converting empirical evidence
gates into documentation claims.

This packet closes only a stale lifecycle/status/version cascade. It does not
close D4-003, create either proposed Tire repository or authorize IMP-05
product work.

## Frozen Entry Baseline

- Solution repository commit:
  `42167067aaf0c7f86f085504bd2ec64eb9762827`
- Solution repository tree:
  `b844743cea923c1dbbaf00498ce7feada7bae607`
- Entry state: clean `main == origin/main`

| Frozen input | SHA-256 |
| --- | --- |
| Tire Health Service requirements 0.6 | `5f3c04d537b31a622b3b0f2259a51449a12dc42b1e2f0d79c75050d1a8114136` |
| Tire Health Cloud requirements | `622f83ba94b12daf5ef2775213a1c521c7bbd5712a0f90302bd4b60be735c471` |
| Component package index | `3edc266f2e2937a6ce6d27242faec2312bfebe48f5889af17b15cd9143d66942` |
| Component/interface register | `b37205720325f127b9d4a020e64c75f97af18ae58ee74c40abe9fc168c7d0dc3` |
| Tire Health product-contract README | `6188c82ae0ea1c75dac23d40013ee7999187e5bfbd4b005560ea27e2609f8461` |
| Demo implementation plan | `864942073e1ce853535207e202195ce2deb3e4488b57e7d1d848fc1f01b1ce5b` |
| Tire Health product profile, immutable negative control | `d72b16bc94b42b9ec435dbd9256428ee3bf94766b4d0209ba560ae05096e2615` |

## Accepted Reconciliation

1. `CR-TIRE` 0.6 is the accepted current design baseline. D4-018 fixes the
   in-vehicle product contract and D4-027 fixes its current-release
   authorization lifecycle; implementation and integration remain open.
2. `CR-TIRE-CLOUD` is Version 0.4 with fifteen requirements and eleven stable
   unit-test obligations. D4-018/D4-019 are accepted and D4-020 is
   design-reviewed; repository and runtime qualification remain open.
3. D4-003 blocks artifact/product acceptance, not the already accepted D4-018
   design contract. Its exact exercise values, pre-aged multiplier, bounds,
   feature-separation margins and calibration/qualification evidence remain
   absent and must not be invented.
4. The Tire estimator profile, schemas, fixtures and all numeric values remain
   byte-identical in this packet.
5. `IMP-05` remains blocked until D4-003 empirical values and explicit creation
   of both proposed product repositories are accepted.

## Exact Writable Boundary

Only these seven paths are writable:

1. `docs/requirements/components/tire-health-service.md`;
2. `docs/requirements/components/tire-health-cloud.md`;
3. `docs/requirements/components/README.md`;
4. `docs/requirements/component-decomposition-and-interface-register.md`;
5. `contracts/tire-health-model/README.md`;
6. `docs/planning/active/demo-implementation-plan.md`; and
7. `docs/planning/active/work-packets/p0-tire-readiness-reconciliation.md`.

## Required Gates

1. `./scripts/docs-check` passes.
2. Confidential-input guard passes for the changed documentation.
3. Tire model, Tire Cloud API and Service tenant quota contract tests pass.
4. `git diff --check` passes.
5. The changed-path set equals the exact seven-path boundary.
6. `contracts/tire-health-model/tire-health-product-profile.v1.json` retains
   its frozen SHA-256 and no schema/fixture/product source is changed.

## Explicit Exclusions

- no Tire repository creation or Git initialization;
- no Service, backend, Dashboard, container or publication-helper code;
- no estimator, threshold, normalization, quota, timing or payload change;
- no D4-003 stimulus implementation, calibration or qualification run;
- no CARLA, dependency retrieval, network, signing, Cloud, VM or Unit action;
  and
- no merge, push or `main` mutation.

## Exit

The packet exits `DESIGN_BASELINE_RECONCILED` when the seven-path documentation
delta is clean, all required gates pass, the estimator profile remains
byte-identical and IMP-05 remains explicitly blocked on empirical values and
repository creation. The next implementation-critical work belongs to a
separately reviewed D4-003 Vehicle stimulus/calibration packet; it is not
authorized here.
