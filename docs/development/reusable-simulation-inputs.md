<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reusable CARLA build inputs

Normal [developer builds](../getting-started/reproduce-demo.md) automatically
obtain reviewed public dependencies and reuse the standalone CARLA simulator.
They compile project components and assemble the installer without rebuilding
Unreal, opening an Editor or recooking unchanged content. No Google login or
private binding file is a prerequisite for that route.

The independent dependency identity `carla-macos-arm64-r1` is not a CARLA
upstream version or a demo release. The
[dependency lock](../../workspace/dependencies/carla-macos-arm64-r1.lock.json)
owns archive bytes, source correspondence and compatibility. Its historical
status describes the original preparation, not the current public access route.

## Contents and boundaries

| Role | Retained contents | Consumer |
| --- | --- | --- |
| `carla-runtime` | Standalone simulator, cooked content, compatible Python API and isolated Python 3.12 | Host and Cloud SDK assembly |
| `host-support` | Native closure, QEMU, OpenSSL, notices and original host manifest | Host assembly; newly compiled Gateway outputs have separate ownership |
| `gateway-sdk` | Hash-bound LibCarla/OpenSSL headers, libraries, notices and SDK manifest | Offline Gateway compilation |

The lock binds macOS ARM64/Town10HD_Opt compatibility, source revisions,
manifests, archive digests and inventories. This is retained binary reuse,
not proof of a fresh full-source build. The public catalog and producer plan
also select the separate vehicle/Factory inputs needed for the complete demo.

Editor/source trees, intermediate objects, derived-data caches, Factory images,
UI programs, credentials, live Tests and run logs are not simulator dependency
content. Original manifests inside immutable archives may retain earlier build
paths; do not rewrite their bytes or copy those paths into public instructions.

## Automatic developer acquisition

Choose **2 / B** in the [README launcher](../../README.md#start-here).
It selects compatible sources/catalog records, obtains and verifies the
required archives, and reuses compatible caches. Internal or external local
APFS workspaces are supported; Docker capacity is checked separately.

Extraction checks the reviewed inventory, bytes and modes and rejects escaping,
linked, device, extra, missing or duplicate members. A failed or partial
directory is not accepted input. Checksums do not come from the newly
downloaded payload. Public access failure never falls back to publisher
credentials, arbitrary substitute archives or silent permission changes.

## Optional private maintainer adapter

The lower-level `lab dependencies` adapter remains for authorized maintainers
with an existing private binding and account. It is not another required
developer step or an automatic fallback from public download failure.
That retained adapter requires explicit external-SSD storage; this restriction
does not change the normal B route's internal/external storage choice.

```sh
./lab dependencies prepare \
  --storage /Volumes/BUILD/simulation-inputs \
  --binding /Volumes/BUILD/private-dependency-binding.json \
  --account YOUR_AUTHORIZED_GOOGLE_ACCOUNT
./lab dependencies verify --storage /Volumes/BUILD/simulation-inputs
```

Use the returned exact `kitInputs` and `gatewaySdk` with their consumers.
This sparse dependency set is not a complete kit and cannot alone satisfy
the full build. Complete compatible cache reuse can work offline. A changed
extracted file fails verification rather than being adopted or overwritten.

The adapter retains a 90 GiB reserve in addition to its declared byte demand.
That is not the measured cold full-build peak. Failed owned extraction can be
removed after inspection without erasing the verified download cache.

## Maintain a dependency version

Export only explicitly selected verified retained inputs:

```sh
./lab dependencies export \
  --storage /Volumes/BUILD/simulation-publication \
  --kit-inputs /Volumes/BUILD/retained-kit \
  --gateway-sdk /Volumes/BUILD/retained-gateway-sdk
```

The exporter preserves payload bytes/modes and proposes a new reviewed lock.
Publication requires the exact approved destination, account and matching lock;
ordinary preparation never uploads or widens access. Reconcile an existing
object rather than overwriting it or creating another same-name copy.

Maps, assets, engine patches, client ABI or native-dependency changes require
a new dependency identity, reviewed pins and affected qualification. UI,
service or installer changes do not themselves require a new CARLA package.
Keep reusable caches and immutable supported inputs; disposable preparation
work uses managed workspace scratch.

Mixed dependency licenses and unresolved redistribution obligations remain
separate from access and integrity. Follow the
[public artifact policy](public-artifact-preparation.md) and
[release campaign](release-campaign.md). Anonymous access or a successful
download is not a fresh-build, runtime or license-clearance verdict.
