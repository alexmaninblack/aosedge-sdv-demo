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

## Choose your route

- **I want to see the demo:** follow [A — install and run](#install-and-run).
  You need one approved DMG, not nine Git repositories.
- **I want to build the demo:** follow [B — developer build](#developer-build).
  Clone this repository only; `lab` obtains the pinned component sources.
- **I am changing the engine or Factory:** use [C — heavy dependencies](#heavy-dependencies).
  This is not a prerequisite for A or B.

These instructions target **macOS on Apple Silicon**. Run Terminal blocks one
at a time, in order. Stop at the first error; do not continue with an empty
variable or a different package. Developer preparation now has a standalone
wizard with offline regression checks; its real first-use walkthrough and the
subsequent build remain **awaiting joint step-by-step execution**.

<a id="release-status"></a>

## Releases

See the [release status page](docs/getting-started/release-status.md) for
available versions, validation status, known limitations and download access.

Select a specific release before installing or building. Each release identifies
its matching artifacts, source revisions and instructions. Preview candidates
are listed separately from validated releases.

<a id="install-and-run"></a>
<a id="supported-route"></a>

## A — Install and run (no source build)

### A1. Check the Mac

```sh
uname -m
sw_vers -productVersion
df -h "$HOME"
```

Expect `arm64` and macOS 26 or later. If Terminal reports `x86_64` on Apple
Silicon, reopen it without Rosetta. The recorded test host is an M1 with 16 GiB
RAM, not a universal performance minimum. Setup checks the complete installed
payload plus a **90 GiB free-space reserve**; the DMG size is not the installed
footprint. No Xcode, Python, Node, Unreal Editor or source checkout is needed.

### A2. Prepare Docker once

Install **Docker Desktop for Mac with Apple Silicon** using
[Docker's installation guide](https://docs.docker.com/desktop/setup/install/mac-install/).
Complete its first-run and license dialogs. If Docker is already running,
reuse it; do not quit/restart it or change another project's storage.

```sh
docker --context desktop-linux info --format '{{.OSType}}/{{.Architecture}}'
```

Expect `linux/aarch64` or `linux/arm64`. If `docker` is not found, finish Docker's
CLI installation before continuing. Setup does not install or start the engine.

### A3. Obtain and verify the complete DMG

Ask the release owner for the approved private Drive link, release index and
Cloud staging access described in [release selection](docs/getting-started/release-status.md).
There is no public binary download in this repository. Download the complete
DMG once; do not extract/copy individual kit files out of it.

Paste the **absolute path** of your downloaded DMG when prompted (without quotes):

```sh
printf 'Downloaded DMG path: '
read -r SDV_DMG
stat -f '%z bytes' "$SDV_DMG"
shasum -a 256 "$SDV_DMG"
```

For the selected source-Factory `1.2.0-rc.1` candidate, expect
**14,162,601,112 bytes** and
`f2b3d68d9dd4bd084d9fa199cc8053190a0466fb10ee3c5ecf024f877d4de82d`.
Two candidates have the same filename: a different checksum is not acceptable.
Only after both values match, open the verified file:

```sh
open "$SDV_DMG"
```

### A4. Install through Setup

In the mounted disk, open **AosEdge SDV Lab Setup**. Keep its matching Runtime
Kit beside it. Choose package storage and a separate short private-data path.
Then perform these actions in order, waiting for each result:

| Action | Expected result |
| --- | --- |
| **Check installation** | Host, storage and destination preflight succeeds |
| **Install package** | Verified version copied; `INSTALLED_NOT_ACTIVATED` |
| **Prepare local data** | Private instance selected; `SELECTED_NOT_STARTED` |
| **Prepare backends** | Required images available in the existing Docker engine |

These steps do not yet start a vehicle. Use ordinary macOS permission dialogs;
do not disable Gatekeeper. This preview is Apple Development signed, not a
notarized public-distribution package. If macOS refuses it, retain the exact
message and contact the release owner rather than bypassing the check.

### A5. Connect Cloud and open the demo

1. Choose **Set up Cloud access…**. Use the intended **staging** instance,
   one OEM and its associated SP, shared by the two independent services.
2. With existing certificates: select the OEM/SP files, then **1. Inspect
   locally**, **2. Use this pair**, **3. Check Cloud access**. With a new
   invitation, follow the [new-certificate route](docs/getting-started/installed-preview-cloud-first-use.md#set-up-cloud-access).
   Setup does not register Cloud accounts or read your mailbox.
3. Grant Accessibility to the signed Setup when requested for window layout.
   Full Disk Access and screen recording are not installation prerequisites.
4. Choose **Open demo**. Expected: Presenter opens. This action does not create
   a controller or start CARLA.
5. Follow the [numbered first-demo sequence](docs/operations/current-demo-workflow.md#preparation-and-version-sequence):
   Create Controller → simulator → VDP V1 / Provision → attachment / Safe Stop
   → Brake V1 → successive VDP/Brake versions → Tire V1.

Publish **one version at a time** and confirm installation/function before the
next. VDP FOTA requires Safe Stop; Brake/Tire QM services have their own SOTA
lifecycle. Enter the fresh VM password only in **VM access / Use once**, not
in shell commands or committed configuration.

### A6. Stop without deleting your Test

For a short pause, choose **Safe Stop** and leave the controller running.
The native menu **Close Presenter (keep demo running)** closes only the
Presenter windows, not the simulator, controller or backends. Full
non-destructive shutdown is still an engineering-owner procedure, not a
completed one-button operator workflow; arrange that handoff before ending a
retained Test session. Preserve Docker Engine and unrelated workloads.
**Finish demo is destructive**: it
retires the current Test and its data, not merely closes Presenter.
The current UI does not yet offer a complete cold return/power-on workflow.
Read [returning and stopping](docs/getting-started/installed-preview-cloud-first-use.md#returning-stopping-and-removing)
before shutdown; do not improvise a VM restart or delete retained state.

<a id="developer-build"></a>

## B — Build project components and the installer

This route builds the UI, Gateway, backends, services and installer. It reuses
the prebuilt CARLA simulator, native dependencies and base images selected by
the release, including the virtual controller's base image (Factory).
**It does not rebuild the simulator engine or Factory.** Exact versions and
checksums belong to the selected release's dependency records. A new signed
build is not automatically byte-identical to the delivered DMG or qualified
for release. The launcher verifies the selected sources and inputs, seals the
results of your build and embeds their exact checksums in the signed Setup.
Installation verifies those checksums; published releases keep their separate
release pins.

### B1. Prepare tools, storage and access

Storage should be chosen by available capacity, whether on the Mac's internal
disk or an external disk. An external SSD is useful for additional capacity
and separating build data; it is not a platform requirement. Use a writable
local APFS volume and keep the workspace, its reusable inputs and short test
scratch directory on that volume. Docker may use a different local volume.

Temporary build and packaging files stay in `sdv/.tmp` and are cleaned up
automatically. Verified downloads/caches, source checkouts, build results and
diagnostic reports are kept separately for reuse. A failed run does not erase
them. Very long workspace paths may require a shorter same-volume `.tmp` for
Gateway socket tests only; the launcher explains that exception when needed.

**Use one launcher from preparation to the developer DMG.** No clone, Python
or Homebrew is needed to start. It checks prerequisites, reuses compatible tools,
shows the plan and asks once before preparing and building. Choose an existing
internal folder or mounted external disk when prompted. Xcode, Docker first-run
setup and Apple account permissions may still require your interaction.

The ordinary input route uses public downloads, without Google login or Google
CLI. **Public inputs are available for the developer walkthrough.** The
[public artifact folder](https://drive.google.com/drive/folders/1DJQkMfbLICXe4LhROdg6pcqUHzp8Tvp7)
also provides the prepared source/notice companion. This is an owner-authorized
test distribution, not a qualified release or completed
[redistribution review](docs/development/public-artifact-preparation.md).
Download the current launcher below; older copies with an inactive public pin
still report `PUBLIC RELEASE NOT YET AVAILABLE`. The
[maintainer-only private route](docs/getting-started/macos-developer-tools.md#private-maintainer-route)
remains available for the existing authorized artifacts.

Download the current script from this repository. Continue only if download
succeeds; a partial download never replaces the completed script:

```sh
curl --fail --location --proto '=https' --proto-redir '=https' \
  --output "$HOME/Downloads/aosedge-prepare-macos.sh.download" \
  https://raw.githubusercontent.com/alexmaninblack/aosedge-sdv-demo/main/scripts/prepare-macos.sh && \
mv "$HOME/Downloads/aosedge-prepare-macos.sh.download" "$HOME/Downloads/aosedge-prepare-macos.sh"
```

You can open the downloaded file in a text editor before executing it. Run:

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh"
```

Have your Apple Development signing identity available. The wizard reads the
small public release catalog through its fixed link, verifies its pinned record,
selects compatible inputs and prepares their references automatically. You do
not need a Google account or any JSON file paths. It shows the selected release
and checks download availability with one-byte range requests, without
downloading the large CARLA/Factory archives. Complete archive integrity is
checked when the build consumer downloads them. The launcher remembers selections;
rerun the same command after resolving a missing item. It automatically continues
through the stages described below; **do not copy more commands or clone anything
manually**. It signs Setup with your selected identity, but never installs or
starts the demo, publishes services, restarts Docker or moves its disk. See the optional
[preparation reference](docs/getting-started/macos-developer-tools.md) for
diagnostic mode, installation locations and recovery.

`READY FOR SOURCE PREPARATION` is an intermediate milestone, not the final
result. The launcher passes its environment to the next phase itself. For
preparation without cloning/downloading/building, use the optional
`--prepare-only` mode; `--check` remains local read-only diagnosis.

<a id="b2-clone-the-one-entry-repository"></a>

### B2. Automatic source selection

No user action is needed here. The launcher selects the current root `main`
commit once, records it and clones `aosedge-sdv-demo` into the selected workspace.
It checks source/input compatibility before continuing. Repeats keep that exact
commit: no automatic pull, reset or replacement of your changes. A compatible
clean checkout from the earlier manual B2 can be reused. Foreign or dirty
checkouts produce a specific stop, not deletion.

Component repositories are then prepared automatically at the build plan's
pinned revisions, not at all component mains. The root development revision is
not an immutable qualified release tag. See
[release selection](docs/getting-started/release-status.md) for historical reproduction.

<a id="b3-inspect-the-build-before-downloading-inputs"></a>

### B3. Automatic checks before downloading inputs

The launcher selects reviewed, storage-aware build owners and checks their
compatibility with your chosen workspace and Docker locations. Docker can stay
on its existing local disk; the launcher does not move or restart it. Historical
release plans remain unchanged. Compatibility is checked separately from
available space; a disconnected disk must never trigger a fallback.

Budget for source checkouts, downloads, unpacked inputs, caches, temporary files,
outputs and reserves on each actual disk, including Docker and, for route C,
the Factory Builder. The final DMG size is not a build-space estimate.

These checks run automatically before acquisition, and again before large
stages. The launcher reports input sizes and stops on a failed capacity or
compatibility check. The tooling checks Docker separately and
counts shared APFS capacity only once; an incomplete storage check is not a
pass. These guards are not a measured cold-build
peak or a universal minimum for every release. Keep the required reserve and
resolve insufficient space or other blocking prerequisites before acquisition.
A plan with `qualified: false` does not fail merely because qualification is
still open; it does not mean that the build or release is qualified.

<a id="b4-prepare-build-and-locate-the-result"></a>

### B4. Automatic build and result

The launcher continues without another command:

1. Prepare and verify seven pinned source roles.
2. Acquire or reuse five locked binary inputs using automatically selected references.
3. Read the returned paths automatically; no manual path reconstruction.
4. Run the ordered 17-step build using the explicit tools/signing identity.
5. Print `BUILD COMPLETE` / `CHAIN_BUILT_NOT_QUALIFIED` and the exact DMG and
   build-receipt paths. Installation through route A is a separate action with
   the result's **own** matching descriptor.

The DMG stays on your selected build disk. The script does not upload it to
Google Drive or create a public release; publication is a separate release-owner
action. Google Drive supplies the verified build inputs, not an automatic
destination for each developer's output.

If interrupted, rerun the same downloaded launcher. Existing owners verify and
reuse completed work; progress flags alone never skip integrity checks.
Unexpected partial native output may require diagnosis; the launcher does not
delete it or retry blindly. Detailed logs live in the workspace's
`.developer-preparation` directory and the existing owner build logs.

The [manual developer reference](docs/getting-started/reproduce-demo.md) retains
individual commands for diagnosis, not another required checklist. A build never implicitly
provisions a Cloud Unit, publishes services or starts a simulator. Stop on a
failed step; do not turn retries into duplicate live actions.

<a id="heavy-dependencies"></a>

## C — Rebuild Factory or the simulator

Use the separate [full-source guide](docs/getting-started/full-source-build.md).
The selected Factory image has an exact-source retained-Builder procedure;
fresh Builder acquisition and full Unreal/CARLA source closure remain explicit gaps. Do not
use upstream Linux/Windows recipes as macOS instructions or claim an arbitrary
clean Mac can already perform this route unattended.

## More information

- [Troubleshooting](docs/getting-started/troubleshooting.md)
- [Documentation map](docs/README.md)
- [Implemented architecture](docs/architecture/current-implementation.md)
- [Qualification record](docs/qualification/current-baseline.md)

This repository owns integration, orchestration, contracts and system
documentation. Components retain their own repositories and lifecycles; the
build command prepares their pinned sources. There are no Git submodules and
no requirement to reconstruct old experiments.

## Security and license

Keep credentials, provisioned VM disks, operational data and compiled artifacts
out of Git. See [confidential source handling](docs/governance/confidential-source-handling.md).
Original integration work is MIT-licensed under `maninblack`; component and
third-party licenses remain separate. See [LICENSE](LICENSE) and
[third-party notices](THIRD_PARTY_NOTICES.md). Public source access does not
grant access to restricted engine source or permission to redistribute binaries.
