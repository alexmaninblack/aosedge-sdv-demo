<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Build the demo from pinned sources

This developer route builds project components and a matching installer using
verified standalone CARLA, native support and source-built Factory .41 inputs.
It does not compile Unreal/CARLA or require an old installed kit. To run
a prebuilt package, use the [installation guide](installed-preview-cloud-first-use.md).

The route targets the `1.2.0-rc.1` source-Factory candidate. Tooling and warm
builds have passed; fresh-clone reproduction of this guide remains an R4 gate.
Read [release selection](release-status.md) first. The historical source tag
does not include these newer commands; the candidate tag is not yet published.
The exact published root revision and its source branch are recorded in release
selection; private input bindings still come through the approved handoff.

## 1 Prepare the host and access

| Requirement | Purpose |
| --- | --- |
| Apple Silicon, macOS 26, Xcode macOS SDK and Swift | Native UI, Gateway and packaging |
| Python 3.10 or later for `lab`; ARM64 Python 3.12 with `packaging` for build owners | Resolver and isolated Cloud worker assembly |
| Node 26.0.0 and npm 11.12.1 | Pinned UI and backend tooling |
| CMake, Git, Docker CLI and running local Docker Desktop | Gateway and Linux ARM64 builds |
| Mounted external APFS SSD | Sources, caches, scratch, outputs and Docker's active backing disk |
| Authorized Google CLI account and two private input bindings | Initial acquisition of five locked archives |
| Authorized Apple Development signing identity in Keychain | Explicit Setup signing, not notarized distribution |

Host tools are prerequisites, not installed by `lab`. Declare their paths;
do not use the installed demo's private Python as a development interpreter.
Google login is separate from the build. Bindings contain file IDs, not
credentials; checked-in locks supply sizes and hashes. OEM/SP certificates are
needed later for the installed demo, not these builds.

Docker must already use the selected SSD. Do not relocate its disk or restart
it as a build side effect. No live Test, backend container, VM or simulator
is started by this route.

## 2 Select the root revision and storage

Clone only `https://github.com/alexmaninblack/aosedge-sdv-demo.git`, then select
the exact published root revision in [release selection](release-status.md).
Do not substitute the latest/default branch or manually collect component
repositories. Source and frozen producer revisions are published; a public
clone alone does not supply the private binary inputs or host tools.

Run from that clean root checkout. Replace the example mount with your SSD.
Create only the parent directories; `lab` creates and owns its workspaces.
The test path must be at most 29 UTF-8 bytes long.

```sh
SDV_ROOT="/Volumes/BUILD/sdv"
SDV_TMP="/Volumes/BUILD/tmp"
mkdir -p "$SDV_ROOT" "$SDV_TMP"
./lab plan --profile developer \
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json
./lab inputs plan
./lab space --storage "$SDV_ROOT/build" \
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json
```

Inspect gates before acquisition. `qualified: false` is intentional: planning
is not release acceptance. State binds the volume UUID; a missing/replaced SSD
causes failure, not fallback to the internal disk.

## 3 Prepare sources and binary inputs

```sh
./lab prepare --profile developer --storage "$SDV_ROOT/build" --sources-only
./lab verify --storage "$SDV_ROOT/build" --sources-only
./lab inputs prepare --storage "$SDV_ROOT/inputs" \
  --binding /private/path/developer-inputs.drive.json \
  --simulation-binding /private/path/simulation-inputs.drive.json \
  --account authorized-reader@example.com
./lab inputs verify --storage "$SDV_ROOT/inputs"
```

Replace both binding paths and the account with your approved handoff values.
Supply `--gcloud /path/to/gcloud` if needed. Never paste tokens into commands,
logs or source files. Repeats reuse verified inputs; after preparation no
Google access is needed for offline verification.

Expect seven source roles and `BUILD_INPUTS_READY_NOT_PROFILE_QUALIFIED`.
Input preparation reports `kitInputs`, `gatewaySdk` and `factoryInputs`.
Use those three returned paths, not guessed directories or an installed kit:

```sh
SDV_KIT_INPUTS="<returned kitInputs>"
SDV_GATEWAY_SDK="<returned gatewaySdk>"
SDV_FACTORY_INPUTS="<returned factoryInputs>"
```

The five archives contain CARLA/Python API, host support, Gateway SDK, unsigned
vehicle/VM bases, and the independently built Factory image. CARLA is reused
across demo releases while its inputs remain unchanged.

## 4 Build the complete candidate

Replace tool paths and the signing fingerprint with your declared host inputs.
This is one ordered command. The first run explicitly permits acquisition
of missing pinned build dependencies.

```sh
./lab build --target all --storage "$SDV_ROOT/build" \
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json \
  --kit-inputs "$SDV_KIT_INPUTS" \
  --gateway-sdk "$SDV_GATEWAY_SDK" \
  --factory-inputs "$SDV_FACTORY_INPUTS" \
  --input-checkpoint workspace/releases/1.2.0-rc.1-source-factory-packaging.json \
  --release-checkpoint workspace/releases/1.2.0-rc.1-source-factory-setup.json \
  --test-tmp-parent "$SDV_TMP" \
  --python /path/to/python3.12 --ui-python /usr/bin/python3 \
  --node /path/to/node --npm /path/to/npm --cmake /path/to/cmake \
  --docker /path/to/docker \
  --signing-identity YOUR_AUTHORIZED_CERTIFICATE_FINGERPRINT \
  --prepare-dependencies
```

The 17 steps build UI, Cloud worker, backend images, Brake V1/V2/V3, Tire V1
and Gateway, then assemble input groups, application, signed Setup and DMG.
VDP bases and Factory are pinned binary inputs here. Rebuilding Factory itself
is a separate [full-source subroute](full-source-build.md).

Success is `CHAIN_BUILT_NOT_QUALIFIED`. Use emitted result paths and receipts
to locate the DMG, not newest timestamps. Independent manifest and Setup pins
must match; never replace expected hashes with observed ones to clear a failure.

## 5 Repeat or continue after a failure

Repeat the same command to verify/reuse unchanged outputs and continue from
the failed step. Omit `--prepare-dependencies` when no acquisition is needed.
Preserve partial output and the first error. Incomplete native output requires
diagnosis, not blind retries; see [recovery](troubleshooting.md#build-and-acquisition).

`./lab status --storage "$SDV_ROOT/build"` inspects saved results. Source
readiness, built targets and qualification are distinct. Ordinary full-profile
`prepare`/`verify` can remain blocked even when the explicit source/input/chain
route above has passed. Do not erase those gates.

## Space and elapsed time

| Observation or guard | Value | Interpretation |
| --- | ---: | --- |
| Five compressed archives | 13.70 GB | Download once or reuse a verified cache |
| Extracted inputs | 28.34 GB | 31,491 files; not the complete footprint |
| Chain admission guard | 166 GiB free | 76 GiB allowance plus 90 GiB reserve, not a measured cold peak |
| Completed source-Factory chain | 17 min 2 sec | Recorded campaign run with reusable inputs, not a cold-host estimate |
| Unchanged chain repeat | 69 sec | Observed warm result, not a guarantee |
| Fresh-host build time and peak storage | Not yet measured | R4 must establish these on its declared host |

Large payloads, caches and temporary files stay on SSD. Routine delivery does
not download a just-uploaded DMG back to the maintainer. The real installation
consumer verifies its own download.

## Next steps

Installation is a separate action through the [operator guide](installed-preview-cloud-first-use.md).
A build does not launch the demo, create a Cloud Unit, publish a service,
notarize the app or prove clean-machine operation. For changes, follow
[Contributing](../../CONTRIBUTING.md); pins are not floating branches.
The [build reference](../development/release-reproduction-r2.md) retains
per-target options and evidence without making that history a prerequisite.
