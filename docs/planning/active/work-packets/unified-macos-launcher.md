<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Unified macOS launcher implementation

- Date: 13 October 2026
- Status: Implemented; offline acceptance PASS; real first-use pending
- Owner: Integration tooling and documentation
- Branch: `codex/unified-launcher`, based on main
- Parent: [Human friendly reproduction](human-friendly-reproduction.md)

The operator approved one downloaded script with three routes and requested
implementation after resuming the parked session. Keep the current developer
workflow and normal signed Setup owners. README becomes a product explanation
and one download/run entry. This is a tooling change, not a new runtime,
installer, Cloud authority, release or full-source build recipe.

## Accepted route contract

| Choice | Executor and result | Explicit boundary |
| --- | --- | --- |
| A Install and run | Verify an approved complete DMG and hand off to its signed Setup | No source clone, compiler, signing key or Google login. Setup owns installation, Cloud access and permissions; opening it is not verified installation. |
| B Build demo and installer | Existing `prepare-macos.sh` and developer continuation, unchanged | Prebuilt CARLA/Factory, frozen source/input pins, capacity checks and candidate result remain authoritative. No implicit installation, runtime start or publication. |
| C Prepare Factory or simulator tools | Reuse host-tool helpers, then inspect the selected specialist prerequisites | Separate Factory and CARLA/Unreal. Prepare compatible host tools only; no Builder boot, engine/Factory compile or claim of clean full-source closure. |

Choose the route before route-specific prerequisites. A must not invoke the B
host preparation or require developer tools. B retains its original standalone
command and saved-state behavior. C does not require Cloud credentials, Docker,
Node or a signing key merely to prepare host tools. System first-run, Apple
licensing, administrator dialogs and licensed-source access stay explicit.

The approved operator DMG has no public download locator today. A offers an
already obtained matching file, without asking for JSON metadata. A future
reviewed locator may enable download, with its size and SHA-256 in the source
catalog. Never substitute another same-named candidate or change Drive sharing.
Factory host preparation requires the existing Builder's exact QEMU version;
install a Homebrew bottle only if its advertised version matches. Simulator
preparation requires the current native Python/CMake/Xcode tools, but cannot
manufacture Epic entitlement or missing source/assets. Missing full-source
conditions produce an explicit partial result, not BUILD READY.

## Bootstrap and integrity

One Bash 3.2 entry works before Git, Python or Homebrew. It shows the menu and
fetches only the selected route and its shared helper/metadata. Each helper is
addressed by its immutable Git blob ID and independently checked with a
compiled SHA-256 and bounded size before execution. Public read uses GitHub's
[raw blob endpoint](https://docs.github.com/en/rest/git/blobs#get-a-blob), without
OAuth or arbitrary executable URLs. Branch movement cannot change saved code.

Keep small private launcher state and verified helper caches in the user's
Application Support directory. Saved choices are data, never sourced as code.
Reject unowned/link/corrupt entries. Use exact leases and cleanup for helper
transfer scratch; large downloads and specialist work use the selected APFS
workspace and existing `.tmp` helpers, never the volume/home root. Resume the
same selection; a repeat rechecks actual state, not a remembered green flag.

Known downloads show names and byte progress; unmeasurable operations show
activity, not invented percentages. A failed download cannot replace a valid
file. Cancellation stops only owned transfer/tool children and preserves
verified caches, Test data, sources and shared Docker. Setup/media handoff has
an explicit owner and detachment instruction rather than silently ejecting an
image while its installer is running.

## Implementation and acceptance

1. Add the menu/dispatcher and content-pinned helper resolver.
2. Add approved-DMG handoff and specialist host preparation; reuse B.
3. Replace README's mandatory A/B command lists with one launcher entry;
   retain anchors and move detailed diagnosis to existing references.
4. Add offline first/repeat/cancellation, selection, checksum/path, route
   isolation, missing prerequisites and partial-result tests. Validate helper
   pin parity, Bash 3.2 syntax, docs, existing developer tests and secret gates.
5. Record exact passed gates and remaining real M1/manual walkthrough. Publish
   source independently of the Presenter review; do not merge that branch or
   change its immutable candidate. Current main remains the intended reader
   entry, subject to the source gates and normal publication policy.

No heavy build, DMG assembly, large download, installation or live demo test is
required by this source implementation. Only local unit/static checks execute
on the development Mac. Any real Setup/route acceptance uses M1; full-source
hardware, licensing and fresh-Builder gates remain separate. Preserve existing
release pins, artifact bytes, credentials, staging/Production resources, Docker
storage, Factory/CARLA and video.

## Offline implementation result

The menu, integrity-checked helper graph, normal approved-DMG Setup handoff and
specialist host preparation are implemented. The developer executor is unchanged.
The [offline receipt](../../../qualification/unified-macos-launcher-2026-10-13.md)
records passed regression gates, fixture scope and remaining real M1/public
operator-delivery/full-source acceptance. Preserve the separately published
Presenter review branch; this source change carries none of its payload edits.
