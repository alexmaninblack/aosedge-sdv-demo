<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 Vehicle and Gateway Readiness Work Packet

- ID: `WP-P0-VEH-001`
- Lane: `L-VEH`
- Parent increment: `IMP-02`
- Review state: `COMPLETED — READY_FOR_CODE_PACKET`
- Version: 0.3
- Prepared: 2026-08-27
- Updated: 2026-08-28
- Accepted: 2026-08-28
- Execution authorized: yes — P0 read-only assessment and local tests only
- Authorized: 2026-08-28
- Product implementation, live CARLA, network, Cloud, VM or Unit mutation
  authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Assess the accepted CARLA/Gateway implementation against the reviewed Vehicle
Simulation and Vehicle Gateway packages, then produce one exact first
`IMP-02` code packet. The P0 worker does not modify either repository and does
not launch CARLA.

## P0 Execution Result

- Completed: 2026-08-28
- Exit state: `READY_FOR_CODE_PACKET` for `IMP-02A`
- Product implementation authorized by this result: no

All three frozen revisions and every frozen contract digest matched. The
dependency-free build and all 16 CTest entries passed; the unchanged local
Unix-socket test required the already accepted local socket permission. All 47
selected shared-contract tests also passed. No live CARLA, Cloud, VM, Unit,
network or product mutation occurred.

The assessment found one smallest deterministic contract correction that can
be implemented wholly in `carla-ego-runtime` without live CARLA:

### `IMP-02A` — Frozen VSS wheel angular-speed semantics

The runtime samples wheel angular speed in radians per second but currently
projects the unchanged values into frozen VSS paths whose unit is degrees per
second. The Engineering Telematics output also labels the values as `rad/s`.
The reviewed slice converts only at the VSS boundary and keeps the normalized
internal sample in radians per second.

Exact future writable files:

- `src/vss.cpp`;
- `tests/vss_projection_test.cpp`;
- `src/viss_client.cpp`;
- `tests/product_language_test.py`;
- `docs/telemetry-contract.md`; and
- `docs/brake-event-scenario.md`.

The existing `20.0 rad/s` fixture shall produce approximately
`1145.9155902616465 deg/s` while preserving the existing `23.76 km/h` linear-
speed assertion. The slice uses branch `codex/imp-02-vehicle-gateway` from
`22864c5bfd15f70827fdfc2a374686d00487481b`, after the owning worktree is clean.

The current untracked `tools/__pycache__/external_control_protocol.cpython-312.pyc`
is classified as generated local output and must be removed or otherwise
explicitly dispositioned before the implementation branch starts; it is not
product input and shall not be committed.

Broader hardware coverage, transactional mode/context behavior, selected-Unit
mTLS/source evidence, typed advisories, Safe Stop facts, connectivity UI/wire
integration and live CARLA qualification remain later `IMP-02` slices. Tire
stimulus values remain gated by D4-003 empirical calibration and must not be
invented. `CarlaSim` needs no change unless later live evidence proves an
actual physical-model or API defect.

## Repositories and Baselines

| Role | Repository | Frozen revision | P0 access |
| --- | --- | --- | --- |
| Primary | `carla-ego-runtime` | `22864c5bfd15f70827fdfc2a374686d00487481b` | read-only |
| Hardware dependency | `CarlaSim` | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` | read-only source evidence |
| Shared contracts | `aosedge-sdv-demo` | `bf231c350c17f8173bfd4da19bfa45932b45cc24` | read-only |

The primary repository must be clean. Existing untracked `.codex-build/` and
`.tmp/` content in the current `CarlaSim` checkout is outside this packet: it
must not be inspected as product input, removed, committed or absorbed. Read
accepted CARLA content by revision or from an isolated read-only worktree.

The future code branch is `codex/imp-02-vehicle-gateway`, created only after an
exact code packet is separately authorized. P0 has no writable repository
paths.

## Frozen Requirements and Interfaces

- [Vehicle Simulation 0.8](../../../requirements/components/vehicle-simulation.md):
  `REQ-VEHICLE-SIM-001` through `010`, `UT-VEHICLE-SIM-001` through `010`;
- [Vehicle Gateway 1.1](../../../requirements/components/vehicle-gateway.md):
  `REQ-GATEWAY-001` through `015`, `UT-GATEWAY-001` through `015`;
- `IF-VEH-001`, `IF-VEH-002`, `IF-VEH-003`, `IF-VEH-004`, `IF-VEH-005`,
  `IF-VEH-006`, `IF-ADV-003`, `IF-ADV-004` and `IF-ADV-005` from the
  [Component Register](../../../requirements/component-decomposition-and-interface-register.md);
- accepted D4-003 boundary: empirical Tire stimulus values remain
  `RESEARCHING` and must not be invented by this packet.

| Frozen file/contract | SHA-256 |
| --- | --- |
| Vehicle Simulation requirements | `fdae4928e99c361b6682d49cd90674584eb5634147fbd9ccca5134588595b5c4` |
| Vehicle Gateway requirements | `670828913038514773de4f03145b6a9e68476bade38e8e27b91430b875b3f56e` |
| Simulator Control Context v1 | `7517d811c04c89ee5b502a9716a8f664ce5c2290abe9ffde6fa1351d9ba9c938` |
| Exclusive Live Source v1 | `9434ec3a8abb6a9ef3e283b4d0a505f7dbb4f848b37232df83d8e21a899d4ce2` |
| Vehicle External Connectivity v1 | `50caf96fdc847e24ac48e13686f38e8b56cdef24c8b701879566627150a83911` |
| Vehicle Hardware Capability v1 | `ac0ba26464219482dcb41e56ebbc1538489e13bd6c84725dbc124e59514cb7e5` |
| VISS Trust and Telemetry v1 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| QM Advisory v1 | `f7ae78148fb3b3265c8b773117126665afb1edd97a73f59db5a1f3af7c223487` |
| Platform FOTA Safe Stop v1 | `b92cd31c9b5066ca5b79c526134c3a059fcda0738cd668f3c96c6b51a0396c66` |

## Exact P0 Tasks

1. Confirm all three revisions, repository cleanliness and frozen digests.
2. Inventory the current `carla-ego-runtime` source, configuration, tests and
   launch tooling. Map each requirement/test ID to `CURRENT`, `PARTIAL`,
   `MISSING` or `EMPIRICAL-GATE` with exact file evidence.
3. Reconcile the selected CARLA hardware profile with current sampled signals,
   normalized VSS paths, declared actuators and applied-control feedback.
   Identify every silent omission or qualification-only value.
4. Assess the full scripted/manual/autopilot/safe-stop transition matrix,
   obstacle lifecycle, reverse/recovery behavior, owned-actor cleanup and one
   honest selected vehicle source.
5. Assess the typed Brake/Tire advisory path and factual status surface,
   engineering-dashboard evidence, one atomic vehicle-external-connectivity
   control and fresh Safe Stop evidence required by the OEM Component Runtime.
6. Freeze the external-connectivity ownership boundary: `carla-ego-runtime`
   owns the native Controller button, typed request/status interface and local
   factual presentation, while `aosedge-sdv-demo`/`IMP-07` owns the actual
   selected-VM QMP/network mutation. The operation disconnects the selected
   vehicle from AosCloud and both Function backends while preserving the local
   CARLA/Gateway plane, the other VM and browser-to-AosCloud connectivity.
7. Separate work that belongs in `carla-ego-runtime` from any genuine physical
   model change that would require `CarlaSim`. Do not allocate work to
   `CarlaSim` merely because it supplies the dependency.
8. Propose one smallest coherent first `IMP-02` code slice with exact writable
   files, tests, fixtures and exit evidence. It must not depend on unfrozen
   D4-003 calibration values.

## Baseline Checks

Run the dependency-free suite with build output outside the repository:

```text
cmake -S . -B <temporary-build> -DCMAKE_BUILD_TYPE=Release
cmake --build <temporary-build>
ctest --test-dir <temporary-build> --output-on-failure
```

Baseline evidence on 2026-08-27: all fifteen non-socket CTest entries passed
in the restricted environment; the one local Unix-socket protocol entry was
blocked only by sandbox socket policy and passed unchanged when rerun with
local socket permission. This is baseline evidence, not live CARLA
qualification.

## Forbidden Work

- no source, configuration, contract or requirement edits;
- no live CARLA/Unreal launch or actor/world mutation;
- no write to the current dirty `CarlaSim` checkout;
- no invented Tire thresholds, degradation curve or production claim;
- no VM, Unit, AosCloud, signing, publication or network operation; and
- no QMP/network implementation in `carla-ego-runtime`; and
- no combining Test and Production Vehicle into simultaneous views of one
  CARLA source.

## Completion Packet

The worker returns:

1. verified baselines and digests;
2. requirement/test-to-file delta matrix;
3. exact repository ownership for every missing behavior;
4. baseline test commands and results, including environment restrictions;
5. recommended first code slice, branch, isolated worktree, writable paths,
   fixtures, tests and local resources;
6. explicit deferred slices and D4-003 empirical work;
7. change requests or blockers; and
8. confirmation that no forbidden operation occurred.

## Exit and Escalation

P0 exits `READY_FOR_CODE_PACKET` when the first slice can be implemented only
inside one reviewed repository boundary and has deterministic tests. A need to
change the CARLA physical model, a contract conflict, missing safety boundary,
or a slice that requires live CARLA or unfrozen Tire values is escalated to the
Gateway owner and Integration Coordinator and leaves only the affected slice
`BLOCKED`.
