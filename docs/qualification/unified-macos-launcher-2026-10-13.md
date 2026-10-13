<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Unified macOS launcher offline results

- Date: 13 October 2026
- Status: Offline implementation acceptance PASS; new real first-use walkthrough pending
- Source branch: `codex/unified-launcher`, independently based on main `a4afa82`
- Scope: README, launcher routing/helpers, source catalog, regression tests and CI

The new [README](../../README.md) has one download/run entry and explains A,
B and C. The [launcher](../../scripts/aosedge-sdv-lab.sh) selects a route before
its prerequisites, obtains content-pinned helpers and preserves repeat/cancel
behavior. Existing developer execution and its standalone command are unchanged.
No Presenter review commit, installed candidate or artifact pin was merged.

## Implemented behavior

| Route | Implemented | Remaining gate |
| --- | --- | --- |
| A | Local ARM64 Docker/host checks; approved DMG selection, consumer checksum reuse, signature/embedded release checks, normal Setup handoff | Complete operator DMG remains privately supplied; public delivery and actual new first-use/native installation are not qualified |
| B | Delegates to the existing full developer workflow with unchanged argument, source/input and candidate contracts | New menu's real walkthrough; no new build or release acceptance inherited from older evidence |
| C | Separate Factory/simulator tools, compatible reuse, Homebrew bottle/version checks, saved workspace/volume identity and explicit partial result | Fresh Builder/guest preparation, licensed engine source/assets, full-source recipe/capacity and compilation qualification |

Helpers use immutable Git blob locators plus independent size/SHA-256 pins.
Wrong or changed cached/downloaded code is never executed. Data-only saved
choices, owned leases and scratch isolate transfers and delegated execution.
Missing/replaced saved storage does not select an internal fallback. Native
installer handoff is distinct from verified installation; borrowed media is
not detached on failure. No credential/account data is placed in the helpers.

## Local gates

The final grouped regression run passed 116 tests in 90.956 seconds: new launcher
fixtures plus existing preparation, catalog, developer workflow/progress and
reader-route tests. The final targeted launcher suite passed 25 tests separately,
including exact-delegate cancellation and lease release. Tests mock downloads,
package managers, mounts, signatures, UI,
Cloud and build execution. Native-Mac metadata fixtures are explicitly skipped
on unsupported platforms; portable CLI/pin checks still run there.

Bash 3.2 syntax, compiled helper/canonical authority pin parity, whitespace and
documentation gates passed. Reader navigation passes from the root-only tree
without sibling checkouts. CI now checks the portable graph and separate macOS
fixtures; CI completion is not claimed from the local run. Source-pinned
catalog projections preserve the historical delivery descriptor and canonical
Builder QEMU/firmware/capacity requirements rather than changing them.

No real download, Homebrew installation, Docker action, DMG mount, simulator,
VM, native window, signing or Cloud mutation was performed in this exercise.
Only temporary fixture processes were started and closed. Small unit scratch
was cleaned; reusable source/artifacts/caches and the external SSD remain.
No new bulk build or artifact copy was created.

## Publication and next acceptance

Publish the complete source graph with the launcher so README's main download
has obtainable matching helpers. This independent change does not merge
`codex/presenter-human-friendly`; its UI results and main-integration gate remain
separate. Production, staged Tests, credentials, Docker storage/Engine, Factory,
CARLA, release tags and video are unchanged.

Next verify the downloaded public entry on M1, then the selected route through
its normal owner. A's local approved-package handoff and B's actual build remain
separate tests; C stays host preparation with explicit full-source gaps. Source
publication is not completed installer E2E, public binary redistribution or a
turnkey engine/Factory rebuild.
