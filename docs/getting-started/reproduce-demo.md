<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reproduce the AosEdge SDV Demonstration

## Choose the operator or developer route

For the prebuilt **engineering preview**, start with
[Installed Preview: Cloud First Use](installed-preview-cloud-first-use.md).
That operator route uses the matching prebuilt kit and native Setup, without
reconstructing old experiments or compiling Unreal/CARLA. It is not yet a
notarized or clean-Mac-qualified public release.

The rest of this page is the **source/developer route for Kit028 / Setup042**. Its
workspace, Editor and build prerequisites are not prerequisites for using the
prebuilt preview. Do not mix its component launchers into an installed run.

## Readiness at a Glance

Updated 7 October 2026. The selected source return point is
`candidate/kit028-setup042`, with Factory .41. The complete DMG is an
engineering preview; the installed M1 scripted sequence passed 98 steps.
Full native UI, moving-SOTA, secure token entry and interruption/repair gates
remain open. No source checkout alone reproduces private artifact bytes,
Cloud identities, credentials or the release ledger.

Use the [current baseline](../qualification/current-baseline.md),
[source return point](../qualification/kit028-setup042-source-publication-2026-10-05.md)
and [implementation map](../architecture/current-implementation.md).
Historical .39/v1.1 instructions and earlier source builds remain historical,
not replacements for the current pinned package.

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
includes Tire and both backends. The candidate source lock records the exact
published source pins and their distinctions from the original built inputs. The read-only doctor checks actual checkout drift:

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
- configured OEM access for Unit/Subject operations and one associated SP
  for separate Brake and Tire service catalogs/publication; configured signing access for bundles;
- private credentials, native access and generated VM state only in their
  designated ignored/local stores; never stage credentials, VM disks, compiled
  bundles or private Cloud source in Git.

Exact revisions/branches are in the candidate source lock and workspace manifest.
CARLA/Unreal retain compatibility branches; the other six dependencies use their
recorded main revisions. Do not replace pinned inputs with arbitrary branches.

## Use the current Demo Control workflow

Run the installed `democtl` from `apps/demo-orchestrator`, as described in its
[CLI guide](../../apps/demo-orchestrator/README.md). Use `democtl image list`
to discover the real catalog; Kit028 selects .41. Do not retire any retained
Production or use an obsolete image from an old example. The [E2E report](../qualification/factory-36-e2e-2026-09-19.md)
records a dated scoped cycle, not a claim that a Test is running now.

All lifecycle, package preparation/signing/publication, assignment and runtime
actions use the shared Demo Control implementation. A normal .41 start already
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

The following historical component-level launchers and their prerequisites
are owned by the Vehicle Gateway repository. They are not the Kit028 installer:

- [native CARLA setup on macOS](../../../carla-ego-runtime/docs/carla-setup-macos.md);
- [macOS desktop launchers](../../../carla-ego-runtime/docs/macos-launchers.md);
- [deterministic brake-event scenario](../../../carla-ego-runtime/docs/brake-event-scenario.md).

That standalone launcher generator creates three developer applications:

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
[Kit028 installed journey](../qualification/m1-live-journey-2026-10-03.md) and
[candidate record](../../workspace/checkpoints/installer-kit-028-candidate.json).
Normal packages use native permissions; the explicit historical
permission-free lifecycle mode is never an authorization-failure fallback.

## Current package build boundary

The distribution tooling assembles locked application, host, VM, vehicle
preparation and Cloud/backend inputs. See the [portable artifact plan](../planning/active/portable-runtime-artifacts.md)
and [distribution contracts](../../contracts/distribution-installation/README.md).
Rebuild only the owner whose inputs change, then rebuild dependent manifests
and the matching Setup pin. Never modify an installed kit in place or combine
a new host manifest with a stale VM binding (the rejected Kit027 defect).

The Factory build-tool checkout is separately pinned in the source lock; it
is not a replacement for the application checkout. Unreal/CARLA compiler,
licensed content and cooked output are build-time concerns, not operator
prerequisites. Reproduce from the recorded pins, not today's upstream branches.

Use repository-only validation first. The [remote qualification harness](../../scripts/qualification/README.md)
drives the installed owners and records scripted evidence separately from
native UI acceptance. A source rebuild is not a new release qualification.
