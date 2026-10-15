<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Development map

Start with the [developer route](../getting-started/reproduce-demo.md) or
[Contributing](../../CONTRIBUTING.md). The launcher prepares tools, pinned
sources/inputs and the engineering installer. Public developer inputs need no
Google login; fresh-host source reproduction remains a separate gate.

## Choose the owner

| Change | Owning repository / boundary |
| --- | --- |
| CARLA physics, maps or simulator build | Maintained CARLA/Unreal sources; licensed dependency lifecycle |
| Vehicle Gateway, VISS, native Driving Control and maneuvers | carla-ego-runtime |
| ARM64 controller image (Factory), KUKSA/IAM integration and VDP | aos-vehicle-platform; platform/FOTA lifecycle |
| Brake analytics / backend | brake-health-service / brake-health-cloud |
| Tire analytics / backend | tire-health-service / tire-health-cloud |
| Setup, Presenter, Demo Control and cross-component contracts | aosedge-sdv-demo |

See the [component map](../architecture/product-map.md) and
[repository boundaries](../architecture/repository-boundaries.md) for exact
responsibilities. A UI or service change normally reuses the prebuilt CARLA
simulator and controller image; it is not a reason to rebuild Unreal or Yocto.

## Current references

- [Add or change a scenario](add-demo-scenario.md).
- [Release campaign and publication](release-campaign.md).
- [M1 qualification scenario runner](../../scripts/qualification/README.md).
- [Native upstream concurrency regression fixture](../../tests/upstream/cm-lock-harness/README.md).
- [Reusable simulator dependency](reusable-simulation-inputs.md).
- [Public artifacts, notices and remaining redistribution review](public-artifact-preparation.md).
- [Retained specialist commands and measured build evidence](release-reproduction-r2.md).
- [Implemented architecture](../architecture/current-implementation.md) and
  [protocol status](../../contracts/implementation-status.md).
- [Requirements](../requirements/README.md) and [executable contracts](../../contracts/README.md).

The earlier [R1 definition inventory](release-reproduction-r1.md) remains only
because the immutable predecessor release definition requires that path.
It is explicitly historical, not another current build guide.

Use the contribution guide's offline checks for source/document changes.
Builds, signatures, live M1 scenarios and public promotion require their own
scope. No development reference implicitly starts a simulator, modifies Cloud
or grants new access.
