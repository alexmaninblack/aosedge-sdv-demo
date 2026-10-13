<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosEdge Platform SDV Lab

AosEdge SDV Lab is a hands-on environment for exploring how to build and operate
a software-defined vehicle with a modular, orchestrated and updatable software
architecture. It demonstrates how the AosEdge platform manages the deployment,
execution and evolution of platform components and independently delivered
services—from establishing the vehicle’s software foundation to introducing
new capabilities throughout its lifecycle.

The lab combines a CARLA-simulated vehicle, an ARM64 virtual controller and the
real AosEdge platform on a Mac, connected to Aos Cloud. The vehicle and
controller hardware are simulated or virtualized; software deployment, runtime
management and updates use actual platform components.

## Start here

**Download one launcher, run it and choose what you want to do.** You do not need
to clone repositories, find JSON files or follow separate preparation commands
before starting. Matching helpers are obtained and checksum-verified
automatically. Requirements are checked for your selected route, not all routes.

These instructions target **macOS 26 or later on Apple Silicon**. Download the
script below. A failed or partial download does not replace the completed file:

```sh
curl --fail --location --proto '=https' --proto-redir '=https' \
  --output "$HOME/Downloads/aosedge-sdv-lab.sh.download" \
  https://raw.githubusercontent.com/alexmaninblack/aosedge-sdv-demo/main/scripts/aosedge-sdv-lab.sh && \
mv "$HOME/Downloads/aosedge-sdv-lab.sh.download" "$HOME/Downloads/aosedge-sdv-lab.sh"
```

You can inspect the downloaded script in a text editor. **Only after the
download succeeds**, run it as your ordinary user, without `sudo`:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh"
```

The menu offers:

```text
1. Install and run the demo
2. Build the demo and installer
3. Prepare Factory or simulator build tools
```

## Choose your route

| Choice | Use it when | What you receive |
| --- | --- | --- |
| **A / 1** | You want to use the demo without compiling | Verified approved DMG handed off to its signed Setup |
| **B / 2** | You want to change project components or build an installer | A new engineering DMG, using prebuilt CARLA and Factory |
| **C / 3** | You need to change Factory or the simulation engine | Selected specialist host tools prepared; full-source input/build gates remain separate |

The launcher shows the selected route and its plan. Existing compatible tools
and verified files are reused. Resolve a reported prerequisite, then rerun the
same downloaded file; it remembers your last route. It never silently updates
a retained checkout, formats storage, deletes your Test, moves Docker data or
publishes software to Cloud.

<a id="release-status"></a>

## Releases and access

See [release selection](docs/getting-started/release-status.md) for available
versions, validation status and access. Versions, checksums and artifact
identities belong to release records, not manually copied README constants.
An engineering candidate is not a qualified public release.

The developer route has owner-authorized public input downloads and needs no
Google login. Route A downloads the selected engineering DMG from its reviewed
public link, or reuses an approved local copy, and checks its exact identity.
It needs no Dropbox or Google login and does not ask for a release-index JSON
path. Public downloads do not grant Aos Cloud access or permission to
redistribute restricted content.

<a id="install-and-run"></a>
<a id="supported-route"></a>
<a id="a1-check-the-mac"></a>
<a id="a2-prepare-docker-once"></a>
<a id="a3-obtain-and-verify-the-complete-dmg"></a>
<a id="a4-install-through-setup"></a>
<a id="a5-connect-cloud-and-open-the-demo"></a>
<a id="a6-stop-without-deleting-your-test"></a>

## A — Install and run

Choose **1**. The script checks the Mac and existing local ARM64 Docker Engine,
verifies the selected complete DMG and signed Setup identity, then requests
opening Setup. No source checkout, Xcode, Python, Node or signing key is needed.
If Docker is missing, it explains how to install and initialize Docker Desktop.
It does not restart a running Engine or interfere with another project's data.

Installation, destination selection, Cloud access and macOS permission prompts
remain in **Setup**, their normal owner. Keep the matching Runtime Kit beside
Setup in the mounted image. Finish installation and Cloud access there, then
open SDV Lab. Opening Setup alone is not verified installation or a running
vehicle. Keep the image mounted until Setup quits; afterward you can eject it
and use the installed application.

This preview is not a notarized public distribution. Do not disable Gatekeeper
or bypass a macOS security refusal. The installer checks payload/storage needs
and a 90 GiB free-space reserve; the DMG size is not the installed footprint.
Your Cloud certificates and any new invitation remain personal inputs, never
included in the media or launcher cache.

Use the [installed first-use guide](docs/getting-started/installed-preview-cloud-first-use.md)
and [demo sequence](docs/operations/current-demo-workflow.md#preparation-and-version-sequence)
for actual vehicle operation. Publish one version at a time and verify it before
the next; VDP updates require Safe Stop. Stop normally and preserve Test data
and shared Docker when ending a session—deletion is a different operation.

<a id="developer-build"></a>
<a id="b1-prepare-tools-storage-and-access"></a>
<a id="b2-clone-the-one-entry-repository"></a>
<a id="b2-automatic-source-selection"></a>
<a id="b3-inspect-the-build-before-downloading-inputs"></a>
<a id="b3-automatic-checks-before-downloading-inputs"></a>
<a id="b4-prepare-build-and-locate-the-result"></a>
<a id="b4-automatic-build-and-result"></a>

## B — Build the demo and installer

Choose **2**. The existing developer workflow prepares tools, fixes the root
main revision once, obtains pinned component sources and verified inputs,
checks storage, then builds and signs the engineering DMG. No additional clone
or build commands need to be copied. Have compatible Xcode and your Apple
Development signing identity available; first-run/license/system prompts remain
explicit. The old standalone `prepare-macos.sh` command remains supported.

Choose an existing writable APFS parent folder on either the internal disk or
an external disk. An external SSD is useful, not mandatory. Capacity is checked
before downloads and large stages, including Docker's actual storage location.
A missing or replaced disk stops the run; it never falls back to another disk.
Shared Docker storage is not moved or restarted.

The workflow builds project components and packaging. It **reuses CARLA and
Factory**, rather than rebuilding them. Its result is a readable DMG path under
`<workspace>/output/`, labelled `BUILD COMPLETE / CHAIN_BUILT_NOT_QUALIFIED`.
It does not install, start or upload the resulting demo. Installation is a
separate deliberate route using that candidate's matching approved inputs.

Downloads show the artifact name and progress. Measurable work shows byte/step
progress; other long work shows activity without an invented ETA. Temporary
work stays in `sdv/.tmp` and is cleaned by its owner. Sources, verified caches,
results and compact diagnostic logs remain reusable after interruption.

See the optional [preparation reference](docs/getting-started/macos-developer-tools.md)
or [manual build reference](docs/getting-started/reproduce-demo.md) for diagnosis,
not another required checklist.

<a id="heavy-dependencies"></a>

## C — Prepare Factory or simulator tools

Choose **3**, then choose **Factory** or **CARLA / Unreal**. The script checks
compatible tools and offers preparation of missing host tools, reusing the
selected APFS workspace for Python, caches and scratch. Factory uses its
existing exact QEMU/firmware requirement. Simulator preparation checks Xcode,
Python, CMake and Ninja. Neither needs Cloud credentials, Node, Docker or a
signing key merely for this preparation.

**This route prepares host tools; it does not yet provide a turnkey full-source
build.** A retained exact-source Factory procedure exists, but fresh Builder
acquisition/guest preparation remains separate. CARLA/Unreal still needs
licensed source/assets and a complete reproducible macOS recipe. The script
lists those remaining conditions and exits with an explicit partial result;
it never launches a VM or an expensive engine build to make preparation look
complete. See the [specialist guide](docs/getting-started/full-source-build.md).

## Help and project information

- [Launcher behavior and recovery](docs/getting-started/unified-macos-launcher.md)
- [Troubleshooting](docs/getting-started/troubleshooting.md)
- [Documentation map](docs/README.md)
- [Implemented architecture](docs/architecture/current-implementation.md)
- [Qualification record](docs/qualification/current-baseline.md)
- [Contributing](CONTRIBUTING.md)

This repository owns integration, orchestration, contracts and system
documentation. Components retain their own repositories and lifecycles.
There are no Git submodules and no need to reconstruct earlier experiments.

## Security and license

Keep credentials, provisioned VM disks, operational data and compiled artifacts
out of Git. See [confidential source handling](docs/governance/confidential-source-handling.md).
Original integration work is MIT-licensed under `maninblack`; component and
third-party licenses remain separate. See [LICENSE](LICENSE) and
[third-party notices](THIRD_PARTY_NOTICES.md). Public source access does not
grant restricted engine access or binary redistribution rights.
