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
for release.

### B1. Prepare tools, storage and access

Storage should be chosen by available capacity, whether on the Mac's internal
disk or an external disk. An external SSD is useful for additional capacity
and separating build data; it is not a platform requirement. Use a writable
local APFS volume and keep the workspace, its reusable inputs and short test
scratch directory on that volume. Docker may use a different local volume.

**Prepare the environment with one wizard.** No clone, Python or Homebrew is
needed to start. It checks all six preparation stages, reuses compatible tools,
shows what is missing and asks once before preparing it. Choose an existing
internal folder or mounted external disk when prompted. Xcode, Docker first-run
setup and account permissions may still require your interaction.

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

Have your Google account with access to the SDV Lab artifacts and your Apple
Development signing identity available. After Google authorization, the wizard
finds the small release catalog, selects compatible inputs and prepares their
references automatically. You do not need to find, create or enter JSON files.
It shows the selected release and checks access without downloading the large
CARLA/Factory archives. The wizard remembers selections; rerun the same command
after resolving a missing item.
It does not clone, build, sign anything or start the demo. It never restarts
Docker or moves its disk. See the optional
[preparation reference](docs/getting-started/macos-developer-tools.md) for
diagnostic mode, installation locations and recovery.

Only after **READY FOR SOURCE PREPARATION**, load the saved environment:

```sh
source "$HOME/Library/Application Support/AosEdge SDV Lab/Developer/environment.sh"
```

Expect `Developer environment loaded`. This supplies `SDV_ROOT`, `SDV_TMP` and
the explicit tool/access paths below, also after a Terminal restart. Stop if
the saved environment reports an error. Preparation is not a completed build
or a substitute for the build-space and exact-source checks in B3.

### B2. Clone the one entry repository

```sh
git clone --branch main https://github.com/alexmaninblack/aosedge-sdv-demo.git "$SDV_ROOT/source"
cd "$SDV_ROOT/source"
git rev-parse HEAD
"$SDV_PYTHON" -B scripts/developer_catalog.py --check-source "$SDV_PREPARED_SOURCE"
```

Expect `Source compatibility: PASS`. Stop on a mismatch: the cloned dependency
records/producer plan must match the prepared selection before any input
download or build. Rerun the current preparation script; if no compatible
release is available, contact the release owner rather than substituting inputs.

This walkthrough uses the current `main`, as selected for the development
exercise. Record the printed revision; it is not an immutable release tag.
The existing build plan still selects frozen candidate component/producer
revisions, not all component mains. Changing that plan is a separate reviewed
step; the wizard does not change those pins. For exact historical candidate
reproduction, use the checkpoint recorded in
[release selection](docs/getting-started/release-status.md). Do not clone
components manually.

### B3. Inspect the build before downloading inputs

**Source and release boundary:** current storage-aware scripts and their joint
walkthrough do not upgrade the historical build plan. That plan still uses
older, external-only build owners and requires Docker on that same external
volume. A reviewed successor must adopt new owners before the complete internal
or split-Docker route can be qualified. Do not edit historical pins or relocate
shared Docker to bypass this boundary. Compatibility is checked separately
from available space; a disconnected disk must never trigger a fallback.

Budget for source checkouts, downloads, unpacked inputs, caches, temporary files,
outputs and reserves on each actual disk, including Docker and, for route C,
the Factory Builder. The final DMG size is not a build-space estimate.

```sh
./lab plan --profile developer \
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json
./lab inputs plan
./lab space --storage "$SDV_ROOT/build" \
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json
```

Review the reported free space, missing cached inputs and build-stage space
guards for the selected release. The new tooling checks Docker separately and
counts shared APFS capacity only once; an incomplete storage check is not a
pass. These guards are not a measured cold-build
peak or a universal minimum for every release. Keep the required reserve and
resolve insufficient space or other blocking prerequisites before acquisition.
A plan with `qualified: false` does not fail merely because qualification is
still open; it does not mean that the build or release is qualified.

### B4. Prepare, build and locate the result

Continue directly at [developer guide step 3](docs/getting-started/reproduce-demo.md#3-prepare-sources-and-binary-inputs).
That is the single copy/paste recipe for the remaining commands:

1. Prepare and verify seven pinned source roles.
2. Acquire the five locked binary inputs using your two binding files.
3. Read the returned paths automatically; no manual path reconstruction.
4. Run the ordered 17-step build using the explicit tools/signing identity.
5. Expect `CHAIN_BUILT_NOT_QUALIFIED`; use its result/receipt path to find the
   DMG, then install it through route A with **its own** matching descriptor.

The guide includes failure recovery and cache reuse. A build never implicitly
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
