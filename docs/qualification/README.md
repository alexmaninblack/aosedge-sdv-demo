<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification Documentation

This directory records accepted baselines, exact component locks,
qualification procedures, and sanitized defect evidence.

- [Current working .33 baseline and acceptance limits](current-baseline.md)
- [Published .33 source checkpoint and branch cleanup](factory-33-source-checkpoint-2026-09-13.md)
  — seven public main branches and return-point tags; 18 local and 9 remote
  temporary branches removed with historical source preserved.
- [Factory .33 scoped E2E — 13 September](factory-33-e2e-2026-09-13.md)
  — VDP Safe Stop transitions; Brake/Tire updates while driving; synthetic
  backend retry; network and retained-identity cold recovery.
- [Consolidation audit and open-issue register — 13 September](factory-33-consolidation-audit-2026-09-13.md)
  — source/publication, artifact retention, permissions and Cloud workaround.
- [Completed artifact cleanup — 13 September](factory-33-cleanup-2026-09-13.md)
  — exact permanent removals, 15.84 GiB available-space increase, preserved inputs
  and post-cleanup Demo Control observations.
- [CM idle full-status recovery proof](cm-idle-full-status-recovery-2026-09-13.md)
  and [isolated original .31 control](factory-31-isolated-online-control-2026-09-13.md)
  — dated evidence behind the packaged .33 workaround, not a Cloud-side fix.
- [Historical .21 baseline — 30 August](factory-21-baseline-2026-08-30.md)
- [Explicit mocked service/backend integration](demo-mocked-backend-integration.md)
  — authorized synthetic-source boundary, separate queues/storage and real
  transport/receipt qualification; never a KUKSA authentication fallback.
- [AosCore service teardown and CM reconciliation proof](aoscore-service-update-teardown-2026-09-11.md)
  — 78 native tests and 25 Demo Control tests passed; Test recovered both
  services to 4, then Brake updated to 5/v2 and 6/v3 and Tire to 5/v1.
  Explicit no-telemetry mode: authenticated/functional qualification remains open.
- [Pre-Studio implementation source checkpoint](pre-studio-implementation-2026-09-09.md)
  — historical multi-repository return point before the subsequently authorized
  Studio implementation; not the current authorization or source state.
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
  — historical immutable Factory .31 Test checkpoint, operator-assisted VDP
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
- [Legacy component locks and current pin reconciliation](component-lock.md)
- [R6.1 isolated-provider-store qualification design](r6-1-demo-isolated-provider-store.md)
  — retained engineering evidence for local candidate `.11`, not an active
  architecture source.
- [Validation-set scope defect](r6-1-validation-set-scope-defect.md)
