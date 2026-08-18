<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reproduce the AosEdge SDV Demonstration

## Readiness at a Glance

The project currently has two different meanings of “run the demo.” They must
not be confused.

| Path | Current status | What a newcomer can reproduce |
| --- | --- | --- |
| Standalone AosVM on Apple Silicon | Repeatable | Boot, persistent lifecycle, network mobility checks and guarded single-Main-Node provisioning |
| CARLA engineering demonstration | Repeatable on the qualified workspace | Native CARLA vehicle, manual/autopilot control, deterministic brake-event scenario and live Engineering Telematics Dashboard |
| CARLA VISS-to-KUKSA integration | Accepted qualification evidence | Vehicle telemetry crossing the Gateway boundary into KUKSA on the qualified VM baseline |
| Full staged SDV story | Design and implementation target | Manufacturing, fresh Unit provisioning, versioned FOTA/SOTA stages, two functional backends and dashboards, advisory return, retirement and reset are not yet one fresh-checkout launcher |

The last row is the destination described by the architecture and scenario
documents. This repository does not claim that it can already be reproduced
end to end.

## Workspace Shape

Keep participating repositories as siblings under one private workspace
directory. Do not move CARLA or Unreal Engine into this solution repository.

```text
workspace/
├── aosedge-sdv-demo/          system integration and documentation
├── CarlaSim/                  virtual physical vehicle
├── UnrealEngine5_carla/       restricted CARLA build dependency
├── carla-ego-runtime/         Vehicle Gateway and engineering demo tools
├── aos-vehicle-platform/      Domain Controller platform/FOTA source
└── brake-health-service/      Function Team 1 in-vehicle SOTA source
```

The planned `tire-health-service` checkout is intentionally not shown because
its name and in-vehicle SOTA boundary are accepted, but the repository has not
yet been created and qualified. Functional Cloud product repositories are
also not shown because their allocation remains an open design decision.

The machine-readable workspace contract is
[`workspace/repositories.json`](../../workspace/repositories.json). From the
solution repository, check the workspace without changing it:

```sh
./scripts/workspace-doctor
```

The doctor reports missing, divergent or dirty repositories and stale
generated launchers. It never clones, updates or cleans another repository.

Documentation links into participating repositories use this sibling layout.
For seamless navigation in a Markdown knowledge-base application, open the
workspace parent directory—not only this repository—as the documentation
workspace or vault.

## Prerequisites and Access

- Apple Silicon Mac with sufficient disk space for Unreal Engine, CARLA and
  persistent VM overlays;
- public access to the solution, CARLA fork, Vehicle Gateway, Vehicle Platform
  and Brake Health repositories;
- Epic Games-linked GitHub access to the restricted Unreal Engine source and
  access to the qualified fork used by this workspace;
- an OEM certificate only if a new AosVM Unit will be provisioned;
- no customer workbook, private certificate, Unit identity or VM disk inside
  any Git checkout.

The exact repository URLs, branches and accepted revisions are recorded in
the workspace contract. The CARLA and Unreal Engine ports deliberately remain
on maintained Apple Silicon compatibility branches; custom project
repositories use `main`.

## Reproduce AosVM First

Follow [Run AosVM on an Apple Silicon Mac](../operations/aosvm-apple-silicon.md).
Stop after local setup if Cloud registration is not part of the exercise.
Provisioning is a separate, explicit operation and creates a persistent Unit
identity.

## Reproduce the CARLA Engineering Demonstration

The operator-facing launcher and its exact prerequisites are owned by the
Vehicle Gateway repository:

- [native CARLA setup on macOS](../../../carla-ego-runtime/docs/carla-setup-macos.md);
- [macOS desktop launchers](../../../carla-ego-runtime/docs/macos-launchers.md);
- [deterministic brake-event scenario](../../../carla-ego-runtime/docs/brake-event-scenario.md).

The installer creates three operator applications:

- `CARLA Simulator.app` for the fixed route and live telemetry;
- `CARLA Manual Drive.app` for manual/autopilot handover;
- `CARLA Brake Event.app` for the persistent obstacle/braking scenario with
  manual takeover and the Engineering Telematics Dashboard.

Closing the controller or pressing Escape in the accepted desktop workflow
requests orderly cleanup of launcher-owned actors, telemetry resources and
the CARLA editor. A reused editor that was not adopted by the launcher is not
terminated blindly.

## Verify the Cross-VM Telemetry Boundary

The accepted evidence and its limitations are recorded in
[CARLA VISS-to-KUKSA qualification](../qualification/carla-viss-to-kuksa.md).
This is currently a qualified integration path, not yet the complete staged
Vehicle Data Platform Capability release flow.

## What Must Be Built Before a One-Command Full Demo

The active gaps and component states are authoritative in the
[Component Register](../requirements/component-decomposition-and-interface-register.md)
and [roadmap](../planning/roadmap.md). Major missing pieces include the clean
factory baseline, accepted Vehicle Data Platform v1-v3 artifacts, both
functional Cloud products, Tire Health service, Software Delivery
Dashboard, unified orchestrator, outbound advisory path and end-to-end reset.

Do not conceal those gaps with manual state changes or undocumented local
files. Each completed component should add a reproducible launcher or test,
sanitized evidence, an updated component state and an accepted workspace lock.
