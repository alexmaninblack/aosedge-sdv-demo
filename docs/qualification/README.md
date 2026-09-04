<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification Documentation

This directory records accepted baselines, exact component locks,
qualification procedures, and sanitized defect evidence.

- [Current accepted baseline](current-baseline.md)
- [AOS-0 Apple Silicon qualification record](aosvm-apple-silicon-baseline.md)
- [AOS-1 single-Main-Node qualification record](aosvm-single-node-provisioning.md)
- [Pre-cleanup end-to-end acceptance](pre-cleanup-e2e-acceptance.md)
- [Post-cleanup acceptance](post-cleanup-acceptance.md)
- [CARLA VISS-to-KUKSA qualification](carla-viss-to-kuksa.md)
- [LTVP VDP update specification-to-implementation record](ltvp-vdp-update-as-built.md)
  — `.26` engineering findings and the runtime/visual `.27`/VDP
  `1.0.15`–`1.0.16` result; restart-evidence and publication closeout remain
  open.
- [LTVP `.27` closeout inventory](../../manifests/r6-1/ltvp-27-closeout-inventory.v1.json)
  — exact retained artifact/evidence hashes and explicit remaining gates; it
  is not the full Demo Baseline Qualification Dossier.
- [LTVP `.27` clean-build record](ltvp-27-clean-build.md)
  — pinned Platform and AosCore inputs, offline clean Yocto result and the
  boundary between the canonical E2E image and same-source rebuild candidate.
- [LTVP `.27` branch reconciliation](ltvp-27-branch-reconciliation.md)
  — reviewed disposition of unique and dirty experiment branches before the
  gated post-publication cleanup.
- [D4-003 Brake and Tire stimulus calibration plan](d4-003-stimulus-calibration-plan.md)
  — approved pre-demonstration calibration and independent-repeat plan; exact
  Tire parameters and numeric tolerances remain open until live calibration.
- [Exact component lock](component-lock.md)
- [R6.1 isolated-provider-store qualification design](r6-1-demo-isolated-provider-store.md)
  — retained engineering evidence for local candidate `.11`, not an active
  architecture source.
- [Validation-set scope defect](r6-1-validation-set-scope-defect.md)
