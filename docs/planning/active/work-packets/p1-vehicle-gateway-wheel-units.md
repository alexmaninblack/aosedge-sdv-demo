<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle/Gateway Wheel-Unit Implementation Work Packet

- ID: `WP-P1-VEH-001`
- Lane: `L-VEH`
- Increment: `IMP-02A`
- Review state: `ACCEPTED — AUTHORIZED`
- Version: 0.2
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded scope in this packet
- External operations authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-VEH-001 0.3](p0-vehicle-gateway-readiness.md),
  SHA-256
  `c82ac18a956b7680ac12ab2001d9ae6a17075a229b8a6567fff012532de5bf1a`

## Outcome

Correct the accepted VSS wheel angular-speed unit mismatch without changing
the CARLA physical model, normalized internal sample or any external system.
The Gateway shall project wheel angular speed in degrees per second, matching
the frozen VSS contract, while the internal sample remains radians per second.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `carla-ego-runtime` |
| Base revision | `22864c5bfd15f70827fdfc2a374686d00487481b` |
| Branch | `codex/imp-02-vehicle-gateway` |
| Isolated worktree | sibling path `../carla-ego-runtime-imp-02a-wheel-units` from the repository checkout |
| Dependency repositories | `CarlaSim` and `aosedge-sdv-demo`, read-only |

The isolated worktree must be clean. The generated file
`tools/__pycache__/external_control_protocol.cpython-312.pyc` in the existing
checkout is not product input, must not be copied or committed and does not
authorize cleanup of any unrelated local content.

## Exact Writable Files

Only these six files may change:

- `src/vss.cpp`;
- `tests/vss_projection_test.cpp`;
- `src/viss_client.cpp`;
- `tests/product_language_test.py`;
- `docs/telemetry-contract.md`; and
- `docs/brake-event-scenario.md`.

A need to change another file, dependency, contract or CARLA API stops the
packet and produces a bounded change request.

## Exact Change

1. Preserve the normalized wheel angular-speed value in radians per second.
2. Convert radians per second to degrees per second only when writing the four
   frozen VSS wheel angular-speed paths.
3. Protect the conversion with a deterministic projection test. The existing
   `20.0 rad/s` fixture shall project approximately
   `1145.9155902616465 deg/s` within an explicit floating-point tolerance.
4. Preserve the existing `23.76 km/h` derived linear-speed assertion.
5. Change the factual Engineering Telematics unit label from `rad/s` to
   `deg/s` and protect it with the product-language test.
6. Reconcile the two owned documentation pages with the same internal-versus-
   VSS-boundary distinction.

No new signal, actuator, threshold, Tire model or behavior is introduced.

## Required Verification

Build output uses a fresh temporary directory outside every repository:

```text
cmake -S <isolated-worktree> -B <temporary-build> -DCMAKE_BUILD_TYPE=Release
cmake --build <temporary-build>
ctest --test-dir <temporary-build> --output-on-failure
python3 -m unittest tests.test_viss_trust_telemetry_profile
```

The completion packet records the branch and commit, exact changed files,
conversion/tolerance evidence, full test counts, any sandbox-only socket
restriction, unchanged repository boundaries and confirmation that no
forbidden operation occurred.

## Explicit Exclusions

- no live CARLA/Unreal launch or actor/world mutation;
- no change to `CarlaSim`, shared contracts, requirements or other runtime
  behavior;
- no dependency installation, external download or network access;
- no typed advisory, mTLS, selected-Unit, Safe Stop, connectivity or Tire
  calibration work;
- no Cloud, VM, Unit, signing, publication or provisioning operation; and
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the exact base, six-file boundary, conversion semantics,
commands, tests and exclusions on 2026-08-28. The worker may create the named
branch/worktree and implement this packet. Any boundary expansion requires a
new review; successful implementation does not authorize push, merge or a live
integration operation.
