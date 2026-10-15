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
- [Specialist build inspection and image prerequisites](release-reproduction-r2.md).
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

## Retained product inputs

The source tree is not a release-attempt archive. Current selection comes from
the [launcher catalog](../../workspace/launcher-catalog.json) for installation
and the [developer selector](../../workspace/current-developer-build.json) for
the reviewed build chain. A version or date in an input filename is not a
request to use that older installer.

| Retained source records | Current consumer / reason |
| --- | --- |
| `releases/1.2.0-rc.2-presenter-preview-dropbox-delivery.json` | Option A's selected DMG identity and provenance |
| `releases/1.2.0-rc.1-public-build-chain-r7.json` | The developer selector's hash-pinned producer plan |
| `releases/kit028-setup042.json` and `release.schema.json` | Immutable base definition validated by the current build/catalog tooling |
| `releases/1.2.0-rc.1-source-factory-build-chain.json` and `1.2.0-rc.1-source-factory-delivery.json` | Public input catalog's exact source requirements and independent capacity checks |
| `releases/1.2.0-rc.1-build-chain.json`, `1.2.0-rc.1-packaging.json` and `1.2.0-rc.1-setup.json` | Existing lower-level chain/packaging/media adapter inputs; not the current option A selector |
| `checkpoints/installer-kit-028-candidate.json` and `installer-kit-028-source-lock.json` | Byte-pinned authorities of the unchanged base definition |
| `checkpoints/factory-41-candidate.json` and `factory-41-source-20261008.json` | Reviewed retained-image and source-Factory preparation identities |
| `checkpoints/reproduction-services-20261008.json` | Reviewed service-export identities used by preparation |
| `checkpoints/demo-v1.1.json` | The portable vehicle-input exporter's explicit baseline guard; the current Factory path passes its separate checkpoint |

Paths in this table are relative to `workspace/`. These are executable inputs,
not a collection of obsolete DMGs. Do not rename or rewrite frozen records to
make filenames look current: the public catalog and producer definitions pin
their bytes. Documentary references inside immutable records (such as the
predecessor of Kit028) are historical provenance, not recursively required
build files; recover them from the record's original Git revision.

Prototype-only HTML, artwork alternatives, prototype tests and unused
release/checkpoint reports belong in Git history. The current UI keeps its
own implementation, assets and tests. Accepted interaction requirements and
stable traceability identifiers remain maintained even where their original
directory name contains `mockups`.
