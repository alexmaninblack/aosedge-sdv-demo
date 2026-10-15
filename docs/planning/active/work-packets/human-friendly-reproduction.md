<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Human-friendly reproduction: current scope and R4 gate

- Status: R1–R3 implemented for the engineering developer route; R4 fresh-host proof remains open
- Updated: 2026-10-15
- Owner: SDV Lab integration
- Authority: this plan grants no build, signing, publication or runtime mutation

## Current entry and exact inputs

The [README launcher](../../../../README.md#start-here) offers:

1. Install and run the selected prebuilt demo through Setup.
2. Prepare tools, resolve exact source/producer/input revisions and build the
   demo/installer using the prebuilt simulator and ARM64 controller image.
3. Prepare host tools to rebuild the controller image (Factory) or simulator;
   full-source Builder/licensed-input/build gates remain separate.

The [launcher catalog](../../../../workspace/launcher-catalog.json) selects
operator delivery. [Current developer selection](../../../../workspace/current-developer-build.json)
binds B's reviewed producer plan independently. Older input definitions may be
reused without implying that every product component is rebuilt from current main.

## R1 — Release definition

Implemented: exact source roles, immutable manifests and producer definitions,
validator/inspection tooling, product-versus-functional-version separation and
public dependency catalog. Google Drive holds reviewed developer inputs; the
selected operator DMG uses its explicit delivery locator. These are separate
from Cloud credentials and redistribution rights.

## R2 — Automated engineering build

Implemented: tool/version/storage/access preparation; source-role resolution;
verified acquisition/cache reuse; ordered component and installer assembly;
named progress; managed scratch and readable output. Normal builds reuse
CARLA/Unreal and the Factory image. A finished build is
CHAIN_BUILT_NOT_QUALIFIED, not installed or published automatically.

The current route supports internal or external local APFS workspaces.
Frozen historical producer plans retain their original policies. Docker
storage is checked independently and never silently moved or restarted.

## R3 — Human entry routes

Implemented: one script and route-specific prerequisites, automatic B
continuation, clear C partial result, current Setup/operation guides, a
component overview and consistent controller-image terminology. Root-only
reader checks and full documentation checks are distinct from actual builds.

## R4 — Independent reproduction and release handoff

Still required: declare a fresh host/workspace; obtain only published inputs
and authorized tools/keys; execute the documented B chain; record exact source
and artifact identities, cache/binary reuse, elapsed time and peak disk demand.
Exercise the resulting candidate's applicable installation/runtime profiles;
do not transfer another DMG's passes to it.

A successful M1 operator installation/API/UI journey is not a fresh developer
or full-source build. The specialist C route is not a promise of a turnkey
fresh Yocto/CARLA/Unreal compilation.

## Preserved boundaries

No provisioned VM, working credentials, old release ledger or hidden maintainer
directory is a required build input. No private-key export, Engine relocation,
security bypass or automatic publication is introduced. Retain exact receipt,
dependency, signing and release-promotion gates.

See [current baseline](../../../qualification/current-baseline.md),
[developer guide](../../../getting-started/reproduce-demo.md),
[release campaign](../../../development/release-campaign.md) and
[remaining delivery plan](../installable-distribution-and-reproducibility.md).
The [original R1–R4 packet](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/planning/active/work-packets/human-friendly-reproduction.md)
preserves detailed historical allocations and acceptance criteria.
