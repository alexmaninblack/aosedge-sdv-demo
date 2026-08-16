<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Pre-Cleanup End-to-End Acceptance

- Accepted: 2026-08-16
- Purpose: protect the working demonstration before local artifact cleanup
- Cloud mutation: none
- Provisioning mutation: none
- Release upload, signing, assignment, or rollback: none

## Decision

The owner accepted `6.1.1-maninblack.1` as the current operational baseline of
the demonstration VM. This records the software state that is already booted
and working. It does not approve the stale Verification Batch that delivered
the candidate, convert `.1` into a rollout candidate, or supersede the plan for
a separately qualified successor.

## Source Baseline

| Repository role | Accepted revision |
| --- | --- |
| SDV demo solution | `d21004f4942f68adfc5f7e2b71481e1cd05b14e8` |
| Vehicle platform | `18a17bb53f141342b6b143395c8478fd6fc66d3d` |
| Brake Health service | `dfaff4af63b59d6eb4c7878f6d13ff67adf3fe98` |
| Vehicle Gateway | `3fcf1fac52151f30bf04bd3b5c5d67bfd8526aa1` |
| CARLA | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| Unreal Engine | `2583a3fd4110bc430416d14820c6df2894ccc619` |

The solution, platform, service, Vehicle Gateway, and CARLA working trees were
clean. Unreal Engine contained only the already classified generated
`Engine/Config/DefaultEngine.ini`, which is removed during the reviewed
housekeeping phase and is not accepted source.

## CARLA Acceptance

`CARLA Manual Drive.app` was started from a cold state with Town10HD. The city,
ego vehicle, live control window, and telemetry dashboard appeared correctly.

| Observation | Result |
| --- | --- |
| CARLA RPC ready | `32.18 s` |
| Vehicle ready | `33.11 s` |
| First VSS frame | `33.44 s` |
| Dashboard ready | `33.96 s` |
| Keyboard ready | `34.22 s` |
| Drive transitions | Safe Stop → Manual → Autopilot → Manual → Safe Stop |
| Maximum observed speed | `19.50 km/h` |
| Distance travelled | `166.56 m` |
| Simulation delivery | stable `30 Hz` |
| Dashboard delivery | stable `4 Hz` |
| Dashboard events | `576`, with no dropped events |
| Final state | vehicle stopped, control released, exit codes `0` |

The VISS end probe succeeded, the runtime destroyed its GNSS sensor and vehicle,
and CARLA restored Traffic Manager and world settings during shutdown.

## AosVM Acceptance

| Unit role | Rootfs | Identity SHA-256 | Result |
| --- | --- | --- | --- |
| validation | `6.1.1-maninblack.2` | `0df9a062ba9df85726b6aecf66cf960964d1bc922d8d3fb0b871100a66a8de86` | provisioned, Online, one primary Main Node |
| demonstration | `6.1.1-maninblack.1` | `55e05719489369c03a6ad7c4934d72611b30bcf0715b09a90a0543c9434b69fa` | provisioned, Online, one primary Main Node |

Both guests passed saved SSH host-key verification and the AosCore service
check. Both root filesystems were mounted read-only with SELinux labels. The
preserved incremental Yocto builder passed its AArch64 smoke test with ten CPUs
and an ext4 root filesystem.

## Repository Qualification

- workspace doctor: `0` errors and one expected pre-cleanup Unreal warning;
- vehicle-platform tests: `35` passed;
- Brake Health service tests: `4` passed;
- solution tests: `81` passed;
- both public component repositories passed their quality gates;
- component lock validation passed;
- REUSE: platform `78/78`, service `18/18`;
- cross-repository ownership and dependency qualification passed.

## Cleanup Gate

The pre-cleanup baseline is accepted. Housekeeping may now remove only the
reviewed obsolete artifacts listed in the repository migration plan. Active
CARLA dependencies, the two provisioned identity overlays and their recovery
backups, the official AosVM base, rootfs candidate `.11`, and the incremental
Yocto builder remain protected. A post-cleanup smoke regression is mandatory
before the new clean baseline is accepted.
