<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# macOS launcher routes and recovery

Start with the one download/run entry in [README](../../README.md#start-here).
The [launcher](../../scripts/aosedge-sdv-lab.sh) asks what you want to do before
checking route-specific tools. It works before Git, Python or Homebrew;
matching helpers are downloaded and verified automatically.

## Route results

| Route | What completes | What you do next |
| --- | --- | --- |
| A / 1 | Download or reuse the selected DMG, verify it and request macOS to open Setup | Follow Setup to install, connect Cloud access and open Presenter |
| B / 2 | Prepare tools and sources, obtain inputs and build the signed DMG | Use the reported output path to install the package separately |
| C / 3 | Check or prepare host tools for the controller image or simulator | Supply the component's source, assets and Builder prerequisites before building |

A follows the selected [launcher catalog](../../workspace/launcher-catalog.json).
Only a matching approved file is reused. A same-named or developer-built DMG
is not accepted automatically. Keep Setup and Runtime Kit together. The image
stays mounted for Setup; quit Setup before ejecting it. If handoff fails, the
launcher detaches only an image it mounted itself.

To install your own B result, open its reported DMG and its matching Setup
directly: see [install your build](reproduce-demo.md#install-your-build).
`--dmg` is only a way to supply the selected A package locally; it does not
switch the approved release or authorize arbitrary developer output.

A's public download requires no storage-provider login. Unexpected sign-in or
warning pages, incorrect sizes and checksum mismatches stop the download;
there is no automatic private-download or alternate-provider fallback.

<a id="operator-download-recovery"></a>

### Operator download recovery

An owned incomplete A download retains a `.part` payload, a private package/file
binding and its selected parent/volume identity. Resolve the reported network
issue and rerun the same current launcher with **A / 1**. It uses the original
disk and resumes from the retained byte count; a missing finished DMG is not
mistaken for a missing disk. A replaced volume, foreign/linked partial or
changed package binding stops without adoption or deletion.

The transfer has a connection deadline and a 90-second stalled/near-zero-data
limit, not a 25-minute total download limit. An advancing slow transfer can
continue. No automatic request retry or storage/provider fallback is added.
Resume requires an exact server byte-range response. Unexpected ranges/pages
discard only that request's appended suffix and preserve the earlier prefix.
Every completed file still needs the full selected SHA-256 and Setup identity
checks before mounting/opening; retained bytes are not proof of integrity.

If you need to restart in another location, pass **A with `--parent`** and an
existing new parent. This explicitly chooses a new download cache and leaves
the previous files untouched. `--dmg` instead selects a complete existing copy
of the approved package, not a partial file or arbitrary B build.
If a provider refuses ranges, use a new cache only as an explicit restart,
not an automatic fallback.

For an interrupted attempt made by an **older launcher without download
receipts**, first download the current launcher from README. Unmarked old
partials cannot be adopted safely: select a new parent explicitly with
`--route A --parent /absolute/existing/new-parent`, or supply a complete matching
file with `--dmg`. Do not delete or edit private selection/receipt files to force
recovery. An already selected local file that disappeared still requires its
original disk/file or a deliberate new selection.

B uses the [developer workflow](reproduce-demo.md). It retains the selected root
revision on repeat, checks pinned inputs and asks for a signing identity.

C offers **ARM64 virtual controller image (Factory)** and **Vehicle simulator
(CARLA / Unreal)**. Factory is the clean Linux/AosEdge controller base;
its **Builder** is a separate Linux build VM. This route prepares compatible
macOS tools, not Linux guest packages, a Builder or restricted source.
See [specialist prerequisites](full-source-build.md).

## Repeat and storage behavior

Rerun the same downloaded file after resolving a prerequisite. The menu offers
the last route; press Return to select it. C remembers the component and B
retains its detailed selections. Each run checks the actual prerequisites,
rather than trusting a saved success flag.

The launcher retains the selected DMG path or workspace and volume identity.
An unavailable saved disk/file stops the run without choosing another disk.
Use an explicit option below when you intend a new selection. The launcher
does not update itself or pull a new source revision automatically.

Small control files and verified helpers are under
`~/Library/Application Support/AosEdge SDV Lab/Launcher`; developer control
files are in its `Developer` sibling. Unsafe directories, changed helpers
and active workspace owners are reported, not overwritten.

Build work uses the selected existing APFS parent and `sdv` workspace.
Temporary files use `.tmp` and are cleaned separately from sources, verified
caches, logs and results. Host applications and Homebrew stay in their normal
locations. Selecting an external workspace does not move those tools or
shared Docker storage.

<a id="start-a-new-build-selection"></a>

### Start a new build selection

Resuming and updating are different actions. To select current `main` again,
finish or cancel the active build, download the launcher again using README,
then create a **new empty parent folder** in Finder on your chosen APFS disk.
Run the launcher and pass that folder with `--parent`. A saved B selection is
reused without a new storage prompt; the interactive choice is for first use
only. It must be a different parent, not the existing `sdv` child:
the workflow creates a new `<parent>/sdv` and records a new root revision.

For example, with your actual existing new folder substituted for the path:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh" --route B --parent "/absolute/existing/new-parent"
```

Keep the prior workspace, caches and outputs intact; this procedure does not
erase or move them. The new selection still uses the reviewed component/producer
plan in that root, not every component's latest branch. To include your own
source commits, follow [the contributor path](../../CONTRIBUTING.md#from-a-source-change-to-your-own-installer).
Do not edit `root-source.json`, ownership markers or completed build receipts,
and do not pull inside a frozen prepared checkout to force an update.

If the workspace's ordinary `.tmp` path is too long for Gateway socket tests,
B selects/reuses a private short `.tmp` on the **same volume** automatically.
Only socket-test scratch uses it; compilers, caches and packaging retain the
selected workspace. Selection is read-only until workflow confirmation, and
unknown/busy scratch is never removed to make room. An unsuitable mount/path
or ownership conflict stops with a reason instead of asking you to invent a
path, creating a symlink or using a different disk.

Ctrl+C stops the current owned transfer/tool process and removes its temporary
files and lock. It does not erase a Test or stop Docker Engine. Keep the first
error and resolve it before rerunning. If an external action's response is
uncertain, inspect its saved result before submitting it again.

## Optional controls

These are conveniences, not another required checklist:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh" --help
```

- `--route A`, `--route B` or `--route C --component factory|simulator`
  selects a route without the menu.
- `--plan` describes the route without host probes, downloads or writes.
- `--check` performs cached/local checks only. If a verified helper is missing,
  it reports that fact without downloading it.
- `--parent /absolute/existing/folder` selects the build/download parent.
- `--dmg /absolute/file.dmg` selects an existing route A file.
- `--xcode /path/to/Xcode.app` selects Xcode for this B/C session.
- `--prepare-only` stops B after host preparation, before cloning or building.

Quote command arguments that contain spaces; do not add shell quotes to
interactive file-picker/path answers. Incompatible route/options stop before
installation or tool preparation.

Exit 0 means the reported local action completed. Exit 2 means cancellation,
a missing prerequisite or partial preparation. Exit 1 means invalid input,
integrity failure or an operation error. C ends with
`HOST TOOLS PREPARED — FULL SOURCE NOT READY` and exit 2 because component
source/Builder preparation is still required; no heavy build starts.

## Download integrity

The launcher checks its helpers against fixed source identities, sizes and
SHA-256 values before execution. It does not accept an arbitrary executable
URL. A helper download failure preserves the verified cache and reports the
problem; it does not ask for OAuth or retry indefinitely.

For package, Docker or Cloud errors, use [troubleshooting](troubleshooting.md).
For changes to the launcher itself, use the
[development map](../development/README.md).
