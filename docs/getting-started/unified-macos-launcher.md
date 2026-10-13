<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# macOS launcher routes and recovery

Start with the one download/run entry in [README](../../README.md#start-here).
The [launcher](../../scripts/aosedge-sdv-lab.sh) asks what you want to do before
checking route-specific tools. It works before Git, Python or Homebrew. Its
matching helpers are obtained automatically, not manually selected.

## Route results

| Route | Result | Not established by that result |
| --- | --- | --- |
| A | Approved DMG/Setup verified; normal macOS open requested | Completed installation, authenticated Cloud access, visible Setup or a running vehicle |
| B | Existing developer preparation/build completed, with its canonical receipt | Qualified release, bit-identical signing, installation or publication |
| C | Compatible specialist host tools observed/prepared | Complete source/assets/Builder closure, build capacity, compilation or full-source qualification |

A validates against the operator entry in the source-owned
[launcher catalog](../../workspace/launcher-catalog.json), projected from the
selected immutable delivery descriptor. It downloads the reviewed public
locator or reuses an approved local file. An arbitrary
same-named or developer-built DMG is not accepted automatically. The matching
Setup/kit must stay together; signed Setup remains the installation and
Cloud-access owner. Respect OS security warnings. Setup handoff deliberately
keeps its installer media mounted until the user quits Setup and ejects it.
On pre-handoff failure only a newly attached image is detached; an already
mounted image is not owned by the launcher.

An operator download locator must be separately published and source-reviewed
before anonymous delivery is enabled. The selected Dropbox link passed the real
M1 consumer check. Provider redirects are bounded and HTTPS-only; HTML warning
or sign-in pages cannot pass the DMG size/checksum gate. No credentials,
cross-provider fallback or private-download workaround is added. Google Drive
remains available for developer inputs and explicitly selected older deliveries.

B delegates to the unchanged standalone developer script. It retains the
[preparation reference](macos-developer-tools.md), fixed root revision on repeat,
pinned component inputs and explicit signing. The menu changes no producer
plan, recipe, artifact bytes or release qualification status.

C separates Factory and simulator tools. Factory uses the Builder's exact
QEMU/firmware identity and checks Homebrew's advertised version before a bottle
installation. An existing incompatible tool is preserved rather than upgraded.
Simulator uses its current CMake floor, native Python and compatible Xcode/Ninja.
Host preparation does not install Linux guest packages, acquire a Builder,
clone restricted Unreal or start a build. The
[full-source guide](full-source-build.md) retains these gates and hardware needs.

## Repeat and storage behavior

Rerun the same downloaded file after resolving a prerequisite. The menu offers
the last route; press Return to select it. C also remembers Factory/simulator.
Route B retains its finer-grained selections and verifies completed work.
The menu is not a green-readiness cache. A retains the approved DMG path and
C retains its workspace/volume identity. An unavailable saved disk/file stops
without choosing the internal disk; use an explicit option for a deliberate
new selection. The launcher does not update itself or pull new source
revisions automatically.

Small control data and verified helper caches are under
`~/Library/Application Support/AosEdge SDV Lab/Launcher`. The existing developer
state remains in its `Developer` sibling. Choices are plain data, not executed
shell code. A launcher lease spans helper preparation and delegated execution.
Do not run a legacy standalone build concurrently with specialist preparation
in the same workspace. Unsafe
directories, links, wrong ownership, changed helpers and unknown lease contents
stop rather than get overwritten. Changed helper pins require a new reviewed
launcher; cached verified generations remain reusable.

Bulk developer/specialist work uses the selected existing APFS parent and `sdv`
workspace, with `.tmp` cleanup and stable volume checks. Host applications and
Homebrew stay in their normal locations; choosing an external workspace does
not move them. The launcher never formats a disk or relocates shared Docker.
Only small installer/helper metadata uses private launcher scratch. Logs,
sources, verified caches and outputs are not scratch and are preserved.

Ctrl+C stops the current owned transfer/tool process group and removes its
owned scratch/lease. It does not erase a Test or stop shared Docker. Failed
or interrupted owner operations are not automatically retried. A lost response
is not permission to click/publish again; retain existing normal-owner receipts.

## Optional controls

These are diagnostic conveniences, not another sequence after README:

```sh
/bin/bash "$HOME/Downloads/aosedge-sdv-lab.sh" --help
```

`--route A`, `--route B` or `--route C --component factory|simulator` selects a
route without the menu. `--plan` describes it without host probes, downloads or
writes. `--check` performs only cached/local checks: absent verified helpers
produce an explicit unavailable result without downloading. Passing local
checks never proves installation, Cloud access or full-source readiness.

Use `--parent /absolute/existing/folder` for build/download workspace selection,
`--dmg /absolute/file.dmg` to avoid A's file picker, or `--xcode /path/to/Xcode.app`
for B/C session-only tool selection. `--prepare-only` belongs to B. Quote paths
with spaces in command arguments; file-picker answers need no quoting. Wrong
route/option combinations stop before installation or host preparation.

Exit 0 means the reported local check, handoff or developer operation completed,
not a release-qualified demo. Exit 2 means cancellation, missing prerequisites
or explicit partial preparation. Exit 1 means invalid input/integrity or an
operation failure. C's normal final `HOST TOOLS PREPARED — FULL SOURCE NOT READY`
is deliberately partial (exit 2). No heavy build is started on either result.

## Helper integrity and source maintenance

The downloaded script contains immutable Git blob locators and independently
checked SHA-256/size pins. Public
[GitHub raw blob reads](https://docs.github.com/en/rest/git/blobs#get-a-blob)
need no account for this public source. Helpers and metadata must pass every
pin before execution; mutable branch names are not helper authority. API denial
or rate limiting stops with the verified cache preserved, not an OAuth request
or automatic retry. No arbitrary executable URL is accepted.

Maintainers update the source catalog/helper code, then run the mechanical
`scripts/sync-launcher-pins --write` projection and its `--check` gate. Tests
compare operator fields to the existing delivery descriptor and Factory
tool/capacity fields to the canonical Builder. No release pin is rewritten to
make another artifact pass. Publish the complete helper graph and launcher in
the same source checkpoint before asking a user to download it.

Local fixture tests are distinct from the new real M1 first-use walkthrough.
Neither source publication nor a successfully opened installer closes that
walkthrough, full installer E2E or the specialist full-source gates.
