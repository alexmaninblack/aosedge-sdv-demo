<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Specialist build and reproduction reference

The ordinary developer route is [README option 2](../../README.md#developer-build).
It prepares tools, fixes the source selection, obtains verified inputs and runs
the reviewed engineering build chain. Do not run a parallel manual workflow
against the same workspace.

## Current selectors and ownership

- [Current developer selection](../../workspace/current-developer-build.json)
  binds the reviewed build/producer plan.
- [Launcher catalog](../../workspace/launcher-catalog.json) independently selects
  operator delivery; a B build is not automatically the current A release.
- [Reproduction contract](../../contracts/release-reproduction/README.md)
  defines immutable inputs, provenance, candidate results and storage.
- [Developer guide](../getting-started/reproduce-demo.md) explains automatic B
  continuation and the separate installation/publication steps.
- [Reusable simulation inputs](reusable-simulation-inputs.md) describes retained
  CARLA dependencies; no engine rebuild is needed for an unchanged dependency.

Sources, verified caches, scratch and results use the selected declared
workspace. Current B accepts internal or external local APFS storage and
checks Docker's actual backing disk separately. Frozen predecessor plans keep
their original storage policy and source identities. Do not mutate those plans
to make another environment pass.

The current B plan selects the current product's application and Setup owners,
including retained-Test package updates and pending-FOTA trust recovery. It
retains unchanged UI and CARLA/Factory input pins. Source alignment is not a
completed rebuild or qualification, and independently signed B media must not
overwrite the published A DMG even when its product-version label matches.

Installer DMGs are outputs, not build inputs. B acquires five independently
locked dependency archives and assembles new media; it needs no preceding DMG.
Launcher A owns the separately selected delivery and its download cache. The
obsolete `lab prepare --drive-binding/--drive-token-fd` media path and operator
use of `lab cache` are rejected before preparation or credential access.

## Read-only specialist inspection

From the selected integration checkout:

```sh
./lab --help
./lab plan --profile developer
./lab plan --profile full-source
./lab factory --help
```

These commands inspect declared interfaces and gates; they are not builds or
evidence of complete reproduction. Full-source readiness remains explicitly
incomplete.

<a id="factory-source-build-on-external-storage"></a>

## ARM64 controller image (Factory)

The Factory image is the clean Linux/AosEdge base for the virtual controller.
The separate ARM64 Linux Builder compiles it. Preparing macOS QEMU/Python tools
does not acquire or prepare that Builder.

The [recorded exact-source Factory procedure](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/development/release-reproduction-r2.md#factory-source-build-on-external-storage)
documents the retained warm Builder and its native/package/image gates.
It is valid only for its declared source/base/cache/layout; it is not a
turnkey fresh-host bootstrap. Use the existing Factory owner adapter, preserve
offline/disk guards and obtain independently reviewed packaging pins for a new
image. Never replace a backing image underneath a provisioned VM.

The [specialist guide](../getting-started/full-source-build.md) distinguishes
fresh Builder requirements, retained-adapter guards and unmeasured cold peaks.
CARLA/Unreal source/licensing/build closure is a separate gate.

## Builds, evidence and delivery

The automatic developer chain returns a receipt and
CHAIN_BUILT_NOT_QUALIFIED, with a readable output path. Its result is not an
installed demo, Cloud publication, notarized app or qualified release.
The [release campaign](release-campaign.md) owns promotion after exact source,
artifact and target-consumer evidence.

<a id="current-independent-workspace-proof"></a>

## Reproduction evidence

The [independent developer reproduction record](../qualification/developer-reproduction.md)
owns exact media identities, M1 results, timings and retained failures. It
proves a fresh source workspace with verified binary-cache reuse on an existing
developer host, not a fresh-macOS or cold-cache build. Its rebuilt package is
separate from public option A. Use that record for evidence, not as another
manual build procedure.

## Earlier measured procedure

The [original R2 execution and timing record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/development/release-reproduction-r2.md)
preserves earlier warm measurements, input counts, failed attempts and staging
notes. They are evidence, not current inventory or another required checklist.
