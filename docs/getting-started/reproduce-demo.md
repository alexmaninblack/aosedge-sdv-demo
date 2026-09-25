<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reproduce the AosEdge SDV Demonstration

## Readiness at a Glance

Updated 24 September 2026: **demo-v1.1 / Factory .39**.

| Path | Implemented / proven scope | Remaining boundary |
| --- | --- | --- |
| Native simulation/control | CARLA, Gateway, combined control/telemetry, Brake/Tire maneuvers and Return to road | Full calibration/repetition and automatic host sleep/wake not closed |
| Platform and services | Selected-Unit trust, KAC/KUKSA, VDP V1–V3, Brake V1–V3, Tire V1, real products/advisory | Production calibration and complete negative matrix are separate |
| Current .39 | Build/smoke; same-identity ignition and five-minute offline checks with VDP117/Brake92/Tire49 | Not a fresh serial all-version/Finish cycle or full P8 |
| Earlier serial UI cycles | Dated .36/.38 evidence retained | Their removed binaries and earlier results do not qualify .39 automatically |
| Source checkpoint | v1.1 dependencies, integration and tag published; hosted checks passed | Git does not restore images, credentials, release ledger or live state |

See the [baseline](../qualification/current-baseline.md),
[v1.1 return point](../qualification/demo-v1.1-return-point.md),
[implemented architecture](../architecture/current-implementation.md) and
[audit/open items](../qualification/documentation-implementation-audit-2026-09-24.md).
Historical synthetic receipts are not vehicle-derived analytic proof.

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
├── brake-health-service/      Function Team 1 in-vehicle SOTA source
├── brake-health-cloud/        Function Team 1 backend/dashboard
├── tire-health-service/       Function Team 2 in-vehicle SOTA source
├── tire-health-cloud/         Function Team 2 backend/dashboard
└── demo-artifacts/            local immutable images and prepared build outputs; outside Git
```

Both service and backend repositories exist. Real KUKSA/product/advisory
operation has the scoped evidence linked above; historical synthetic .33
receipts are not its substitute. Project-owned public remotes are under
`alexmaninblack`; Unreal Engine remains a restricted external dependency.

The machine-readable workspace contract is
[`workspace/repositories.json`](../../workspace/repositories.json), but its
accepted main-branch pins must match the selected published checkpoint. It
includes Tire and both backends. The v1.1 publication reconciled all eight
dependency pins and hosted CI. The read-only doctor checks actual checkout drift:

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
  and both service/backend repositories;
- Epic Games-linked GitHub access to the restricted Unreal Engine source and
  access to the qualified fork used by this workspace;
- configured OEM access for Unit/Subject operations and each team's SP access
  for its own service catalog/publication; configured signing access for bundles;
- private credentials, native access and generated VM state only in their
  designated ignored/local stores; never stage credentials, VM disks, compiled
  bundles or private Cloud source in Git.

Exact revisions/branches are in the v1.1 return point and workspace manifest.
CARLA/Unreal retain compatibility branches; the other six dependencies use their
recorded main revisions. Do not replace pinned inputs with arbitrary branches.

## Use the current Demo Control workflow

Run the installed `democtl` from `apps/demo-orchestrator`, as described in its
[CLI guide](../../apps/demo-orchestrator/README.md). Use `democtl image list`
to discover the real catalog; .39 is retained for new Tests, while existing Production
still uses .31. Do not retire Production or use an obsolete image from an old
example. The [E2E report](../qualification/factory-36-e2e-2026-09-19.md)
records a dated scoped cycle, not a claim that a Test is running now.

All lifecycle, package preparation/signing/publication, assignment and runtime
actions use the shared Demo Control implementation. A normal .39 start already
contains the accepted CM/SM/resource/input fixes; do not reapply old runtime
activation or restart recipes. The release allocator owns version numbers and
must retain its continuity ledger. VDP profile bases and current service build
exports are required preparation inputs, not disposable cache history.

The following standalone CARLA/AosVM guides describe component-level or legacy
entry points. They are useful background, not parallel launchers to run over
an active Demo Control-owned environment.

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

The initial [VISS-to-KUKSA proof](../qualification/carla-viss-to-kuksa.md)
is historical evidence. Current real-data proof is in the
[.39 ignition](../qualification/factory-39-ignition-2026-09-24.md) and
[offline](../qualification/factory-39-offline-2026-09-24.md) receipts.
Normal packages use native permissions; the explicit historical
permission-free lifecycle mode is never an authorization-failure fallback.

## What Must Be Built Before a One-Command Full Demo

Use the [current audit](../qualification/documentation-implementation-audit-2026-09-24.md)
for remaining work, not earlier lists of missing repositories or permissions
that are now implemented. Complete the fresh .39 serial sequence and remaining
recovery/negative/calibration gates. Source tests are not live/human acceptance.

The [Studio plan](../planning/active/demo-studio-delivery-plan.md) retains
chronology. Rebuild only for a proved, approved guest delta; documentation or
host UI changes alone do not require a new image. Never conceal a blocked gate
with synthetic success or undocumented manual state.
