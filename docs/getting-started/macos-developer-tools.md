<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# macOS developer preparation reference

The normal route is **2 / B** in the
[single README launcher](../../README.md#start-here). It prepares the host
and continues through source checkout, verified inputs and the DMG build.
No Git checkout, Python or Homebrew is needed to start it. This page explains
the checks; it is not another mandatory command sequence.

The default public-input route needs no Google account or Google CLI.
The launcher selects compatible inputs automatically, without asking you
for JSON binding files. A download-access failure does not switch to a
private account.

<a id="1-select-the-mac-and-storage"></a>

## What the six stages do

| Stage | Reuse/check | If a prerequisite is missing or incompatible |
| --- | --- | --- |
| 1. Mac and storage | Native Apple Silicon, macOS 26+, existing writable local APFS, volume identity and free space | Explain the problem; never format a disk or choose another volume after disconnect |
| 2. Apple tools | Selected Xcode, completed first-run setup, macOS SDK 26+, Swift and Git | Ask you to install/open Xcode and complete Apple's prompts; preserve the global Xcode selection |
| 3. CMake and Python | CMake/CTest >=3.24; native Python 3.12; project environment with packaging | Install missing Homebrew bottles and reconcile the owned environment; do not automatically upgrade an incompatible formula |
| 4. Node and npm | Exact versions selected by the current source requirements | Install a checksum-verified ARM64 distribution inside the workspace, not over a global installation |
| 5. Docker and public inputs | Docker CLI/Engine, local Linux ARM64 context and anonymous input availability | Install Docker only if missing; leave first-run/start to you; no Google login |
| 6. Signing and inputs | Apple Development identity and compatible release from the pinned catalog | Select an identity by number; explain unavailable inputs; never create/export your key |

The launcher shows a plan before changes and asks for one workflow
confirmation, including the build/signing continuation unless you selected
`--prepare-only`. Xcode, Homebrew and Docker may require their own first-run,
license or system prompts.

Host applications and Homebrew retain their normal locations. Sources,
isolated Python/Node, downloads, caches and results use the selected workspace.
Preparation does not change shell profiles, upgrade unrelated tools, move
shared storage or restart Docker Engine.

<a id="apple-signing-access"></a>

## Apple signing access

Only the **B build** needs your own Apple Development signing identity; A uses
the package publisher's signature. Neither is an OEM/SP Cloud certificate.

1. Install compatible Xcode, open it and complete Apple's license/components.
2. In **Xcode → Settings → Accounts**, sign in with your own Apple Account and
   select the development team you are authorized to use.
3. Open **Manage Certificates…**. Reuse a usable **Apple Development** identity,
   or use **+ → Apple Development** if you need to create one and have that
   permission. If your organization manages signing, ask its administrator;
   do not revoke somebody else's certificate or import the publisher's key.
4. Rerun B and select the listed identity. Its private key must also be in this
   Mac's unlocked login Keychain; downloading a public certificate alone is
   insufficient. Review any normal Keychain signing prompt locally.

See Apple's [certificate types and account guidance](https://developer.apple.com/help/account/certificates/certificates-overview/).
The launcher neither creates this identity nor exports its key. An Apple
Development signature is for the engineering workflow; it does not make your
DMG a Developer ID/notarized public distribution.

## Storage and completion

A writable APFS parent may be on the internal disk or an external SSD.
Preparation requires a 90 GiB free-space reserve on the selected volume and
checks host-tool locations before installing there. This reserve is not the
complete build's size. After cloning, the build-space planner checks workspace
and Docker capacity against the selected build. Docker may use a separate
local volume; neither preparation nor the build relocates its data.

<a id="capacity-planning"></a>

### Capacity planning before a fresh build

| Resource | What to allow for |
| --- | --- |
| Selected APFS workspace | Verified compressed downloads, extracted inputs, pinned source/tool checkouts, intermediate components, packaging scratch and the final DMG, plus the reserve. Expect a several-hundred-GiB working budget for a fresh B run, not a 90 GiB total allowance. |
| Docker's backing disk | ARM64 backend/service build layers and exports. If it is on another disk, free space on the workspace does not solve a Docker-disk shortage. Unrelated projects also share its capacity. |
| Internal tool disk | Xcode, Homebrew and Docker applications keep their normal locations even with an external workspace. Allow their own installation/update space. |
| Memory | Ordinary installed-demo operation has a 16 GiB Apple Silicon reference configuration. B compilation has no established universal RAM minimum or measured clean-host peak; do not infer it from A. Avoid parallel builds and unrelated memory-heavy work. Full-source Factory has its separate 32 GiB host requirement. |

This is planning guidance, not a measured cold-build upper bound. The workflow
prints **Binary inputs: … to download if uncached; … unpacked** and performs
separate workspace/Docker checks before large stages. Those checks and each
owner's headroom guard remain authoritative; they cannot guarantee that other
applications will not consume space or memory later. No heavy build begins
just to measure capacity. If you only want to run the demo, choose A instead.

`READY FOR SOURCE PREPARATION` means the host checks completed. The default
route then checks out sources, downloads and fully verifies the archives,
and starts the ordered build. It does not install the DMG, publish services
or launch a controller or simulator.

`PREPARATION INCOMPLETE` or `ACTION REQUIRED` means resolve the listed
action and rerun the same downloaded launcher. To stop after preparation:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh" --route B --prepare-only
```

The complete B route ends with **BUILD COMPLETE** and a readable
`<workspace>/output/<name>.dmg` path. The file stays on the selected disk;
it is not uploaded automatically. `output` points to the exact build result,
without making another large copy. An existing unowned output is not overwritten.

## Progress, repeats and diagnostics

Large inputs show their names, downloaded/total bytes, percentage, transfer
rate and approximate remaining time. Verification and unpacking are separate
stages. Build progress counts completed steps, not elapsed-time percentage.
Operations without measurable progress show an activity indicator.

Disposable work uses `sdv/.tmp` and is removed after completion or normal
cancellation. Sources, verified caches, logs and final outputs are preserved.
After a crash, only idle owned temporary directories can be cleaned; unknown
or still-used files are left alone. Some Gateway tests need a shorter
same-volume temporary path; the launcher explains when that is required.

Small private control files are under
`~/Library/Application Support/AosEdge SDV Lab/Developer`. They record
selections and paths, not passwords, tokens or private keys. Each run
rediscovers tools and checks their versions. A saved handoff does not replace
these checks.

The launcher loads its generated `environment.sh` itself; you do not need
to source it for the normal route. The selected volume and root revision
are retained for continuation. Restarting does not follow an updated
`main`, overwrite local edits or adopt a foreign checkout. Do not start
parallel workflows in the same workspace.

Diagnostics are under `<workspace>/.developer-preparation`; the final message
identifies the failing stage and log. Keep the first error and resolve it
before rerunning. Do not edit `root-source.json` or `workflow.json` to
force progress.

For local-only checks, without downloading or starting the build:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh" --route B --check
```

Missing verified helpers are reported without fetching them. Use
`--parent /absolute/existing/folder` for a deliberate workspace selection
or `--xcode /path/to/Xcode.app` for a session-only Xcode selection.
Quote paths with spaces in commands; interactive path answers need no quotes.
See the [launcher reference](unified-macos-launcher.md) for all options.

## Automatic input selection

The wizard reads the hash-pinned source-owned `workspace/dependencies/catalog.json`
from GitHub and obtains all five archives from their reviewed public Dropbox links.
No Dropbox or Google account is required. Versions and dependency identities are inside JSON, not inferred
from filenames or timestamps. No compatible record, changed checksum or
denied access stops with a specific error instead of asking for a manual
JSON path or your publisher's credentials.

Preparation checks catalog integrity and archive availability. The acquisition
stage checks each complete archive's size and SHA-256 against the source lock
before using it. Interrupted downloads can continue from retained ranges,
and verified cached inputs are reused.

Sign-in pages, provider limits, foreign redirects, wrong ranges and changed
bytes stop the transfer. There is no automatic switch to Google Drive or a
request for publisher credentials. Resolve the reported access/connectivity
problem, then rerun the same downloaded launcher to reuse verified cache data
and resume a retained partial download.

For source changes or release-owner/private-input maintenance, use the
[development map](../development/README.md), not a separate preparation path.
