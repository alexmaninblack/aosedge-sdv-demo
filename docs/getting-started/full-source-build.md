<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Full source build scope and prerequisites

Use this route when changing the simulation engine, native dependencies or
vehicle Factory image. For UI, Gateway, services and backends, use the
[developer route](reproduce-demo.md) and reuse heavy dependencies. Operators
use a [prebuilt DMG](installed-preview-cloud-first-use.md).

**Full-source preparation and reproduction are not yet qualified.** The
resolver describes the scope, but does not provide a completed end-to-end
full-source build for a new user.

## Inspect the declared scope

From the reviewed root checkout, run this read-only command:

```sh
./lab plan --profile full-source
```

Inspect gates, source roles and build order. A successful plan is not a build.
Missing licensed inputs and unsupported owners stay explicit; do not copy
unrecorded files from a maintainer's machine to clear them.

| Area | Existing route | Remaining condition |
| --- | --- | --- |
| Project components and packaging | Developer chain | Fresh-environment qualification of the documented chain |
| Factory .41 | Exact-source campaign in the SSD-backed ARM64 Builder with native/package/image gates | Independent packaging pins and live qualification for a new candidate |
| CARLA and Unreal | Maintained Apple Silicon forks and retained standalone dependency | Complete source/assets/toolchain closure, licensed access, capacity and reproduction proof |
| Native host support, SDK and unsigned vehicle bases | Pinned binary inputs in the developer route | Source/build closure for each full-source claim |

## Factory subroute

The Factory campaign rebuilt .41 using a separate exact-source directory in
the retained ARM64 Builder, with explicit download and shared-state cache
reuse. Builder base, writable disk, guest workspace and host outputs were on
the external SSD. This was not a cache-cold compiler run.

Use `./lab factory --help` for the owner adapter and the
[Factory procedure and evidence](../development/release-reproduction-r2.md#factory-source-build-on-external-storage)
for this specialist route. It is not a one-command clean-host guide. A new
Factory needs native/package/image gates, offline smoke and independently
reviewed group/Setup pins before inclusion in another installer. Do not replace
a backing image beneath a provisioned VM.

The Factory guard requires 40 GiB additional host headroom plus a 90 GiB
reserve, with a 60 GiB guest guard. These are admission checks, not measured
cold peaks. Full-source time and capacity remain unmeasured. An M1 runtime
test does not establish suitability as an Unreal/Yocto builder.

## Simulation and licensed inputs

The [product map](../architecture/product-map.md) identifies source owners.
Restricted Unreal access, compatible tools and licensed content are separate
prerequisites. Public source is not permission to redistribute all packaged
content. Use reviewed fork revisions, not upstream main.

Map, asset, physics, native ABI or relevant engine changes can require a new
simulator dependency. Presenter or advisory-service changes normally do not.
Keep `carla-macos-arm64-r1` for unchanged developer builds; do not compile
Unreal merely to assemble another DMG.

## Before claiming full source support

Resolve every input and entitlement, exercise all owner recipes in a declared
fresh environment, measure disk/time and verify the installed result. Record
unavoidable binary inputs explicitly. Until then, report only the developer or
Factory subroute actually exercised. Use [Contributing](../../CONTRIBUTING.md)
for candidate changes and [troubleshooting](troubleshooting.md) for failures.
