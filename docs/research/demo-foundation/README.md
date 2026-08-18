<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R9 Demo Foundation Research

Status: **research pass complete; review required before implementation**.

This checkpoint records the read-only research required before implementation
planning for the staged post-SOP Brake Health demonstration. It does not
authorize deployments, builds, VM mutation, Cloud mutation, or product-code
changes.

## Evidence language

- **PROVEN** — directly supported by repository state, the pinned runtime, an
  official specification, or a prior captured acceptance result.
- **INFERRED** — strongly indicated by evidence but not exercised end to end.
- **PROPOSED** — a design recommendation for later review.
- **REQUIRES EXPERIMENT** — cannot be accepted without a controlled test.

## Workstreams

| ID | Topic | Document |
| --- | --- | --- |
| R1 | G0 platform baseline and generic runtime | [R1](r1-g0-platform-baseline.md) |
| R2 | AosCloud lifecycle, targeting, and reset semantics | [R2](r2-aoscloud-lifecycle.md) |
| R3 | VM recovery, checkpoints, and Unit identity | [R3](r3-vm-recovery-and-identity.md) |
| R4 | Deterministic CARLA scenario and signal production | [R4](r4-carla-scenario-and-signals.md) |
| R5 | Brake Health data contract and staged model | [R5](r5-brake-health-data-and-model.md) |
| R6 | Bidirectional advisory path and security | [R6](r6-bidirectional-advisory-and-security.md) |
| R7 | Functional Cloud contract and offline operation | [R7](r7-functional-cloud-and-offline.md) |
| R8 | AosEdge native logging and dashboard presentation | [R8](r8-aosedge-native-logging.md) |
| R9 | Demo dashboards and AosCloud API feasibility | [R9](r9-demo-dashboards-and-apis.md) |
| R10 | Native CARLA telemetry inventory and Tire Health design evidence | [R10](r10-carla-telemetry-and-function-team-2.md) |

The sanitized
[Automotive Orchestration Coverage Matrix](automotive-orchestration-coverage-matrix.md)
maps twenty-one automotive concerns to the `G0–G4` stages, dashboard evidence,
acceptance criteria, and explicit claim boundaries. The confidential OEM
source is not part of this repository.

The cross-workstream conclusions, dependencies, contradictions, and recommended
experiment order are consolidated in the [integration summary](integration-summary.md).

## Overnight boundary

This research pass may read local repositories, sanitized VM artifacts,
official documentation, and read-only AosCloud API data. It must not deploy,
assign, approve, delete, restart, reprovision, rebuild, replace checkpoints,
change product code, push Git history, or otherwise mutate the running demo.
