<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Rebuild the controller image or simulator: scope and prerequisites

Use this route when changing the vehicle simulator, its native dependencies
or the **ARM64 virtual controller image (Factory)**. The Factory image is the
clean Linux/AosEdge base from which a controller VM is created, not a running
or provisioned vehicle.

For UI, Gateway, services and backends, use the [developer route](reproduce-demo.md)
and reuse those heavy dependencies. To run a prebuilt package, use
[installation](installed-preview-cloud-first-use.md).

## What option C prepares

Choose **3 / C — Prepare tools to rebuild the controller image or simulator**
in the [README launcher](../../README.md#start-here), then choose:

- **ARM64 virtual controller image (Factory)**; or
- **Vehicle simulator (CARLA / Unreal)**.

The launcher checks compatible macOS tools and offers to prepare missing ones.
It does not create a Linux Builder, acquire restricted source/assets, or
compile either component. The message
`HOST TOOLS PREPARED — FULL SOURCE NOT READY` means you must supply the
component-specific prerequisites below before building. See the
[launcher reference](unified-macos-launcher.md) for repeats and optional controls.

## Inspect the declared scope

From an integration source checkout, this read-only command shows source roles,
prerequisites and build order; it does not start a build:

```sh
./lab plan --profile full-source
```

<a id="factory-subroute"></a>

## Controller image (Factory) subroute

The **Builder** is a separate ARM64 Linux build VM used to compile the
controller image. It is not the vehicle controller. Preparing macOS tools
does not create or configure this Builder.

A fresh Builder requires 32 GiB host RAM, 260 GiB initial host free space and
180 GiB guest free space, as checked by `scripts/r6-1-builder`.
For an existing prepared Builder, the Factory adapter checks 40 GiB additional
host headroom plus a 90 GiB reserve, and 60 GiB guest free space. These are
different entry conditions, not estimates of the final build size.

Use `./lab factory --help` for the build adapter and the
[specialist Factory reference](../development/release-reproduction-r2.md#factory-source-build-on-external-storage)
for its Builder, source and cache setup. There is no turnkey clean-host
controller-image build in the downloaded launcher.

Build a new image separately from a provisioned controller. Do not replace
a backing image beneath an existing VM. Including a new image in an installer
requires matching reviewed packaging inputs; an image file alone is not a
replacement for the selected package.

## Simulation and licensed inputs

Simulator builds require compatible Xcode/CMake/Ninja/Python, access to the
maintained CARLA and restricted Unreal source revisions, and the corresponding
licensed content. The [component map](../architecture/product-map.md) identifies
the repositories. Public source access does not grant rights to redistribute
all packaged content.

Map, asset, physics, native ABI or engine changes can require a new simulator
dependency. Presenter and advisory-service changes normally do not. Use the
selected prebuilt simulator for unchanged developer builds rather than
compiling Unreal merely to assemble another DMG.

The launcher prepares host tools only; it does not provide an end-to-end
macOS simulator source-build recipe. For component changes, start with
[Contributing](../../CONTRIBUTING.md). For missing tools or inputs, use
[troubleshooting](troubleshooting.md).
