<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reproduce the AosEdge SDV Demonstration

## Readiness at a Glance

Recorded 13 September 2026. Distinguish the working engineering workspace
from a fully published, fresh-checkout, visually accepted product demo.

| Path | Current status | What a newcomer can reproduce |
| --- | --- | --- |
| Standalone AosVM on Apple Silicon | Repeatable | Boot, persistent lifecycle, network mobility checks and guarded single-Main-Node provisioning |
| CARLA engineering demonstration | Repeatable on the qualified workspace | Native CARLA vehicle, manual/autopilot control, deterministic brake-event scenario and live Engineering Telematics Dashboard |
| CARLA VISS-to-KUKSA integration | Accepted qualification evidence | Vehicle telemetry crossing the Gateway boundary into KUKSA on the qualified VM baseline |
| Factory .33 Test lifecycle and FOTA/SOTA | Scoped E2E passed | Fresh Test provisioning; VDP V1/V2/V3 under Safe Stop; Brake/Tire replacement while driving; synthetic backend receipt/retry; network and retained-identity cold recovery |
| Real service telemetry and advisory | Blocked on Cloud permissions; not live-qualified | Normal packages retain native authorization; temporary demo packages use explicitly synthetic data, not KUKSA or real advisory |
| Full staged Studio story / fresh checkout | Partially implemented; acceptance remains open | Complete Presenter service actions, real product gates, published source/lock reconciliation and clean operator visual repeat remain |

Use the [current working baseline](../qualification/current-baseline.md),
[exact .33 E2E evidence](../qualification/factory-33-e2e-2026-09-13.md) and
[consolidation audit](../qualification/factory-33-consolidation-audit-2026-09-13.md)
for current pins and limitations. A synthetic backend receipt is real transport
evidence but is not proof of vehicle-derived analytics. The packaged CM idle
full-status setting is recovery around an unresolved Cloud ordering defect,
not a server fix.

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

Both service and backend repositories exist. Both backends accepted native
service-produced synthetic records in the .33 run; real KUKSA/product/advisory
qualification remains separate. Project-owned public remotes are under
`alexmaninblack`; Unreal Engine remains a restricted external dependency.

The machine-readable workspace contract is
[`workspace/repositories.json`](../../workspace/repositories.json), but its
accepted main-branch inputs predate the working Studio feature branches and
Tire repositories. Reconciliation is explicitly OPEN-05 in the audit; do not
interpret its older pins as the current build recipe. The read-only doctor
can expose that drift:

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

The current exact branches, source pins and remote-publication gaps are recorded
in the consolidation audit. Some working changes are uncommitted or ahead of
remote. The CARLA/Unreal compatibility branches and the project Studio branches
must not be replaced with `main` merely to satisfy an older workspace file.

## Use the current Demo Control workflow

Run the installed `democtl` from `apps/demo-orchestrator`, as described in its
[CLI guide](../../apps/demo-orchestrator/README.md). Use `democtl image list`
to discover the real catalog; .33 is current Test, while existing Production
still uses .31. Do not retire Production or use an obsolete image from an old
example. The [E2E report](../qualification/factory-33-e2e-2026-09-13.md)
records the commands and results of the current scoped cycle.

All lifecycle, package preparation/signing/publication, assignment and runtime
actions use the shared Demo Control implementation. A normal .33 start already
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

The accepted evidence and its limitations are recorded in
[CARLA VISS-to-KUKSA qualification](../qualification/carla-viss-to-kuksa.md).
The current .33 report additionally qualifies the VDP component release flow.
Neither report claims that the permission-free Brake/Tire services consume
live KUKSA data.

## What Must Be Built Before a One-Command Full Demo

The [active Studio plan](../planning/active/demo-studio-delivery-plan.md#current-delivery-position--13-september-2026)
owns the remaining work: finish consolidation/source publication, complete
Presenter actions/visual alignment, then qualify native permissions and real
service analytics/advisory after the platform fix, followed by the clean
CLI/visual repeat. Cloud ordering and the client workaround are tracked
independently. Do not list the already built .33, VDP family, orchestrator or
Tire repositories as missing implementation.

No new image is needed just to repeat this workflow; rebuild only for an
identified, approved guest change. Keep runtime observations distinct from
accepted design requirements and never conceal a blocked gate with synthetic
success or undocumented manual state changes.
