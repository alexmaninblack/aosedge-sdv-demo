<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle/Gateway Safe Stop Projection Work Packet

- ID: `WP-P1-VEH-002`
- Lane: `L-VEH`
- Increment: `IMP-02B`
- State: `IMPLEMENTED — ISOLATED SOURCE PROJECTION COMPLETE`
- Version: 0.2
- Prepared: 2026-08-29
- Accepted: 2026-08-29
- Implementation authorized: yes — 2026-08-29, only the exact nine-file
  source boundary and deterministic tests in this packet
- Completed: 2026-08-29
- Live CARLA, external network, Cloud, VM, Unit, FOTA, signing, push, merge and
  live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Previous implemented slice:
  [WP-P1-VEH-001](p1-vehicle-gateway-wheel-units.md)

## Outcome

Add the transport-independent, frame-coherent VSS projection core for the six
control/reset facts still missing from the accepted ten-path Platform FOTA
Safe Stop evidence set:

- `Vehicle.CarlaSimulation.Control.ActiveMode`;
- `Vehicle.CarlaSimulation.Control.TransitionState`;
- `Vehicle.CarlaSimulation.Control.Generation`;
- `Vehicle.CarlaSimulation.Reset.Generation`;
- `Vehicle.CarlaSimulation.Reset.InProgress`; and
- `Vehicle.CarlaSimulation.Reset.Discontinuity`.

The existing projection already supplies `Vehicle.CarlaSimulation.FrameId`,
`Vehicle.Speed`, `Vehicle.Chassis.Accelerator.PedalPosition` and
`Vehicle.Chassis.Brake.PedalPosition`. The proposed slice combines the six new
facts with those four existing facts in one source-frame and source-timestamp
coherent VSS snapshot.

The Gateway projects vehicle facts only. It does not evaluate the Safe Stop
thresholds, authorize FOTA or infer motion state for AosCloud. A missing,
invalid or wrong-frame control/reset group remains atomically absent rather
than becoming a partial or fabricated normal state, so the OEM Component
Runtime continues to fail closed.

This packet is a projection-core increment only. It does not make
`IF-VEH-007` operational, complete `REQ-GATEWAY-013` or qualify Platform FOTA
Safe Stop.

## Frozen Repositories and Inputs

| Input | Frozen identity |
| --- | --- |
| Product repository | `carla-ego-runtime@d05ac2dbf89f341215e12770feab0ec23b3c2394` |
| Shared solution repository | `aosedge-sdv-demo@a366e1ef3d1fc2470a916421157a0b9a016d26ce` |
| Vehicle Simulation requirements | SHA-256 `fdae4928e99c361b6682d49cd90674584eb5634147fbd9ccca5134588595b5c4` |
| Vehicle Gateway requirements | SHA-256 `4efa9ad6d583d4fcb1b8543dda9bb28769b8032ad54925830498e0437ad43fd5` |
| Component and Interface Register | SHA-256 `d8af5f69fcca00542196e5ff4bd73e21e6f5aaa79c67126a27656d5860d4456b` |
| D4 Decision Register | SHA-256 `9cf1eda4abb7ea141928b5d21dc7a67294a5ebaa89ab3d0e5356056c50c9b2e7` |
| Simulator Control and Context 1.0.0 | SHA-256 `7517d811c04c89ee5b502a9716a8f664ce5c2290abe9ffde6fa1351d9ba9c938` |
| VISS Trust and Telemetry 1.1.0 | SHA-256 `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| Platform FOTA Safe Stop 1.1.1 / `D4-028` | SHA-256 `5b7087748877295837eb16a8bac02742dbae7328e54ba0b852fed2f5de6d3be9` |

The frozen requirement/interface scope is `REQ-GATEWAY-003`,
`REQ-GATEWAY-004`, `REQ-GATEWAY-013`, `UT-GATEWAY-003`,
`UT-GATEWAY-004`, `UT-GATEWAY-013`, `IF-VEH-004`, `IF-VEH-006` and
`IF-VEH-007`. The proposed implementation would produce partial evidence for
these obligations; it would not change their accepted meaning or completion
state by itself.

The product base contains the accepted wheel angular-speed correction from
`WP-P1-VEH-001`. The existing untracked `tools/__pycache__/` in the ordinary
checkout is generated local output, is not a frozen input and shall not be
copied, deleted, modified or committed by this packet. Any later implementation
shall use a clean isolated worktree from the exact product revision above.

## Exact Future Writable Boundary

After separate review and explicit implementation authorization, only these
nine `carla-ego-runtime` files may change:

1. `include/carla_ego_runtime/simulator_control_facts.hpp` — new typed,
   transport-independent source-frame and six-fact input;
2. `include/carla_ego_runtime/vss.hpp` — optional facts input and boolean VSS
   value support;
3. `src/vss.cpp` — all-or-none same-frame projection;
4. `src/viss_protocol.cpp` — canonical VISS boolean value formatting as
   `true`/`false`, never `1`/`0`;
5. `tests/vss_projection_test.cpp`;
6. `tests/viss_protocol_test.cpp`;
7. `vss/Vehicle.CarlaSimulation.vspec`;
8. `cmake/ValidateVssOverlay.cmake`; and
9. `docs/telemetry-contract.md`.

No `CMakeLists.txt` change is required when the new facts type remains
header-only. A need to change any other source, configuration, shared contract
or requirement stops the proposed packet and returns it for review.

## Proposed Source Semantics

1. The input type uses closed typed values for `SAFE_STOP`, `SCENARIO`,
   `MANUAL`, `AUTOPILOT` and `STABLE`, `PREPARING`, `FAILED`; arbitrary strings
   cannot enter the projection.
2. The input carries its attributable source frame. The six paths are emitted
   together only when that frame equals the physical vehicle snapshot frame.
3. Missing or frame-mismatched context omits the entire six-path group while
   leaving truthful physical telemetry available. It never publishes part of
   the group, copies a previous group forward or substitutes defaults.
4. Every emitted path uses the current complete vehicle snapshot's source UTC
   timestamp. Existing `FrameId`, speed, throttle and brake meanings remain
   unchanged.
5. `Reset.InProgress` and `Reset.Discontinuity` remain typed booleans through
   the in-memory VSS value and serialize through VISS as the strings `true` or
   `false` required by the existing VISS datapoint representation.
6. The projection contains no threshold, observation window, FOTA state or
   deployment decision. `D4-028` freshness and stability policy remains owned
   by the OEM Component Runtime.

## Required Deterministic Verification

The future implementation packet shall use fresh temporary build directories
outside every repository and prove:

1. a positive fixture exposes all ten Safe Stop paths with one frame and one
   source timestamp, exact types and accepted uppercase enum values;
2. absent context and a context/vehicle frame mismatch omit all six new paths
   atomically while preserving existing factual physical telemetry;
3. no fixture can emit a partial control/reset group or an arbitrary enum;
4. VISS `Get` and `Subscribe` serialize both boolean values as `true`/`false`
   and never as numeric booleans;
5. the VSS overlay contains the exact six paths, branch hierarchy, data types
   and read-only sensor semantics; and
6. all unchanged source-only regression tests still pass.

The minimum checks are:

```text
cmake -S <isolated-worktree> -B <temporary-core-build> -DCMAKE_BUILD_TYPE=Release
cmake --build <temporary-core-build>
ctest --test-dir <temporary-core-build> --output-on-failure

cmake -S <isolated-worktree> -B <temporary-viss-build> \
  -DCMAKE_BUILD_TYPE=Release \
  -DCARLA_EGO_WITH_VISS=ON \
  -DCARLA_EGO_BOOST_INCLUDE_DIR=<pinned-Boost-1.82-include>
cmake --build <temporary-viss-build>
ctest --test-dir <temporary-viss-build> --output-on-failure

python3 -m unittest \
  tests.test_simulator_control_context \
  tests.test_viss_trust_telemetry_profile \
  tests.test_platform_fota_safe_stop_contract
```

The final two local transport tests require permission to bind an ephemeral
Unix socket and an ephemeral loopback TLS listener. If the execution sandbox
denies only that bind, the completion record shall identify the restriction
and rerun the unchanged tests only under separately permitted local-test
conditions. No external network connection is required or allowed.

## Explicit Exclusions

- no Python controller, Scenario Controller or control-state-machine change;
- no polling or promotion of `controller-status.json` into a product contract;
- no controller-to-C++ transport, live producer feed, monotonic generation
  enforcement or reset-discontinuity lifetime implementation;
- no mTLS client CA, peer certificate fingerprint, selected-Unit binding,
  assignment generation, role connection cap or credential lifecycle;
- no OEM Component Runtime policy, threshold, observation history, waiting,
  activation, rollback or removal change;
- no typed advisory `Set`, advisory status, source-state, hardware-superset,
  actuator, vehicle-external-connectivity or Tire stimulus/calibration work;
- no `CarlaSim`, shared contract, requirement, implementation-plan or other
  repository edit;
- no live CARLA/Unreal, Cloud, VM, Unit, FOTA, signing, provisioning,
  publication, credential or external-network operation; and
- no push, merge or direct mutation of `main`.

## Future Blockers Outside This Packet

### 1. Frame-coherent controller-to-Gateway state handoff

Full D4-004 and `IF-VEH-007` operation still requires a frozen internal handoff
from the Python external-control tick owner to the C++ Gateway. It must bind
applied mode, transition and reset facts to the exact CARLA frame without
blocking frame processing. The current `controller-status.json` is run
evidence updated at event or coarse motion cadence and lacks the complete
`TransitionState`, Reset generation/frame and discontinuity contract. It
cannot be treated as 50-ms Safe Stop evidence. The handoff and producer state
machine require their own reviewed packet.

### 2. Selected-Unit mTLS assignment and role configuration

Full D4-006 enforcement still requires an exact runtime configuration and
onboarding handoff that maps `UnitId`, `NodeId`, client-certificate fingerprint
and assignment generation to the selected Platform Unit and its distinct
`PLATFORM_UPDATE_RUNTIME` role. The current VISS server implements
server-authenticated TLS with generic clients; it has no client CA, role
selection or selected-Unit manifest. That trust/assignment slice requires its
own reviewed packet and per-Unit credential qualification.

Neither blocker authorizes a placeholder file, guessed IPC, static shared
client identity or weakened authentication. They do not block review of this
projection-core proposal, but they prevent it from being presented as an
operational or qualified Safe Stop path.

## Baseline Assessment Evidence

- The dependency-free Release build succeeded. Fifteen of sixteen CTest
  entries passed in the restricted assessment sandbox; the unchanged local
  Unix-socket test was denied only at socket bind. Its sixteen pure
  `ExternalControlStateTests` passed.
- The VISS-enabled Release build succeeded with the locally available pinned
  Boost 1.82 headers and OpenSSL 3.6.3. `vss_projection`, `viss_protocol` and
  `vss_overlay` passed; the unchanged `viss_network` test was denied only at
  loopback-listener bind.
- The current Simulator Control, VISS Trust and Platform FOTA Safe Stop
  contract suites passed all 21 tests.
- No product or shared-document file was changed and no live or external
  operation was performed during the assessment.

## Completion Record

- Repository: `carla-ego-runtime`
- Isolated branch: `codex/imp-02b-safe-stop-projection`
- Frozen base: `d05ac2dbf89f341215e12770feab0ec23b3c2394`
- Initial implementation commit: `64d200ab93a62dce0df0c230fa3dd687cdb60c03`
- Final corrective commit: `8af302dd11c872a564ea7542a126c9886daf2a5a`
- Cumulative boundary: exactly the nine authorized files; worktree clean
- Core Release verification: 16 of 16 CTest cases passed
- VISS Release verification: 18 of 18 CTest cases passed
- Frozen shared contract verification: 21 of 21 cases passed
- Independent review: initial default-construction and validator/test-strength
  findings were corrected in `8af302d`; final re-review found no open issue

The final source makes `SimulatorControlFacts` non-default-constructible,
requires every fact explicitly, projects the six-path group atomically only on
the matching physical frame, validates each overlay path against its own exact
datatype and `sensor` type, and tests every accepted and invalid enum mapping.
No generated artifact or out-of-boundary path was committed.

## Remaining Gate

`IMPLEMENTED` means only that the isolated projection core is complete. It does
not make `IF-VEH-007` operational or qualified. The frame-coherent live
controller handoff, selected-Unit mTLS identity/role assignment, live CARLA
qualification, push and merge remain separately reviewed future work.
