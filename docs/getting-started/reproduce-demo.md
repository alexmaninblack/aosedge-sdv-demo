<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Build the demo and installer

Use **2 / B** in the [single README launcher](../../README.md#developer-build).
The script prepares the host, obtains the sources and dependencies, checks
storage, and builds a signed DMG. You do not need to run another set of clone
or build commands afterward.

This route builds the demo's project components and installer. It reuses the
prebuilt CARLA simulator, native support and **Factory image**, the clean
Linux/AosEdge base for the ARM64 virtual controller. It does not rebuild
Unreal/CARLA or the controller image. For those tools, see the
[specialist route](full-source-build.md). To run the demo without compiling,
use [route A](installed-preview-cloud-first-use.md).

## 1 Prepare the host and access

Have these prerequisites available; the launcher checks versions and explains
any required action before continuing:

| Requirement | Purpose |
| --- | --- |
| Apple Silicon, macOS 26+, Xcode with macOS SDK and Swift | Native applications, Gateway and packaging |
| Git, CMake/CTest and native Python 3.12 | Source checkout and build tools |
| Node and npm versions selected by the launcher | UI and backend tooling; installed in the workspace when needed |
| Docker CLI and a running local Linux ARM64 Docker Engine | Backend images and service builds |
| Existing writable local APFS parent folder | Sources, downloads, caches, temporary work and results |
| Authorized Apple Development identity in Keychain | Signing the Setup application |

The parent folder may be on the internal disk or an external SSD. Leave room
for the complete build, not just the downloaded archives: the launcher checks
the workspace and Docker's actual backing storage separately before large
stages. It does not move Docker storage or restart a running Engine.

No Google account, input-binding JSON files, Cloud certificates or old
installed kit are needed for this build. Xcode, Homebrew and Docker may
require their own first-run, license or system prompts. Do not use the
installed demo's private Python interpreter for development.

For checks and recovery details, use the
[macOS preparation reference](macos-developer-tools.md).

## 2 Select the root revision and storage

Choose **Build the demo and installer**, select an existing APFS parent and
follow the preparation prompts. Confirm the workflow and signing identity.

The launcher records the integration repository's `main` revision at the
start and obtains the component revisions from its selected build plan.
It checks the compatible public dependency catalog automatically; do not
collect the component repositories or select input JSON files by hand.

The selected volume and root revision are retained for continuation. A
missing/replaced volume stops the run rather than switching to another disk.
Existing unowned directories and local source edits are preserved and reported.

## 3 Prepare sources and binary inputs

The launcher checks source and producer compatibility, then downloads and
verifies the pinned inputs. Large downloads show the artifact name and
progress. Compatible verified downloads and caches are reused.

The inputs include CARLA and its Python API, host support, Gateway SDK,
unsigned vehicle/VM bases and the Factory image. These reusable dependencies
are not rebuilt just because Presenter or a service changed.

A failed checksum or access check stops the affected stage. Keep the reported
error and resolve it before rerunning the same launcher; do not supply a new
expected hash from the download itself.

## 4 Build the complete candidate

The ordered build compiles UI, Cloud worker, backend images, Brake profiles,
Tire and Gateway, then assembles the runtime package, signed Setup and DMG.
The progress display counts completed steps; it does not predict build time.

On success, the launcher prints **BUILD COMPLETE** and a readable path under
`<workspace>/output/`. The machine-readable result is
`CHAIN_BUILT_NOT_QUALIFIED`: the package was built, but this command does not
install or publish it. Use the reported path rather than searching for the
newest DMG by timestamp.

## 5 Repeat or continue after a failure

Resolve the first reported error, then rerun the same downloaded launcher
and choose **2 / B**. It verifies and reuses completed work before continuing.
It does not silently update the retained root checkout to a newer `main`.
Sources, verified caches and completed outputs stay available after an
interruption; owned temporary files are cleaned separately.

Do not start another build in the same workspace while one is active.
For a deliberate new source selection or a storage change, use the
[launcher reference](unified-macos-launcher.md) rather than editing saved state.

## Next steps

Install the resulting DMG through its matching Setup application using the
[installation guide](installed-preview-cloud-first-use.md). Building does not
create a Cloud Unit, publish services, launch the simulator or upload the DMG.
For source changes and release publication, see [Contributing](../../CONTRIBUTING.md).
