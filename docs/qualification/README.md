<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification Documentation

This directory records accepted baselines, exact component locks,
qualification procedures, and sanitized defect evidence.

- [Current accepted baseline](current-baseline.md)
- [democtl local VM terminal acceptance](democtl-local-vm-lifecycle.md)
  — live create/start/stop/retire checks on .27, separate from Cloud/demo qualification.
- [democtl Unit terminal acceptance](democtl-unit-lifecycle.md)
  — actual provisioning/Online/role-set/retirement results and remaining fresh-cycle gates.
- [democtl local source selection](democtl-source-selection.md)
  — .28 Test/Production handover, actual status, no-op and local TLS evidence.
- [democtl VDP family checkpoint](democtl-vdp-family.md)
  — Test VDP 6.0.0 active with 23 telemetry paths under transient SM demo-5s;
  the Stop/Start race and clean Factory qualification remain open.
- [Source checkpoint and next Factory release](democtl-release-checkpoint.md)
  — current immutable Factory .31 Test checkpoint, operator-assisted VDP
  13.0.1/v1 -> 14/v2 -> 15/v3 replay and native desktop preparation;
  earlier Factory investigations remain timestamped historical evidence.
- [AOS-0 Apple Silicon qualification record](aosvm-apple-silicon-baseline.md)
- [AOS-1 single-Main-Node qualification record](aosvm-single-node-provisioning.md)
- [Pre-cleanup end-to-end acceptance](pre-cleanup-e2e-acceptance.md)
- [Post-cleanup acceptance](post-cleanup-acceptance.md)
- [CARLA VISS-to-KUKSA qualification](carla-viss-to-kuksa.md)
- [D4-003 Brake and Tire stimulus calibration plan](d4-003-stimulus-calibration-plan.md)
  — approved pre-demonstration calibration and independent-repeat plan; exact
  Tire parameters and numeric tolerances remain open until live calibration.
- [Exact component lock](component-lock.md)
- [R6.1 isolated-provider-store qualification design](r6-1-demo-isolated-provider-store.md)
  — retained engineering evidence for local candidate `.11`, not an active
  architecture source.
- [Validation-set scope defect](r6-1-validation-set-scope-defect.md)
