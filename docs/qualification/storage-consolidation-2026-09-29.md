<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Authorized Storage Consolidation — 29 September 2026

- Status: Authorized migration, runtime consolidation and preservation checks complete
- Version: 1.1
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0`; existing dirty work preserved
- Input: [disk growth audit](../research/disk-growth-audit-2026-09-29.md)
- Installer continuation: [consolidation checkpoint](installer-consolidation-2026-09-29.md)

## Authorized boundary

The operator accepted the capacity plan after the read-only audit. This work
moves verified retained data to Work and retires exact internal duplicates.
It does not prune shared Docker/Yocto caches, modify source functionality,
rebuild a Factory, change service versions, install another kit, or touch Cloud.
The current Test, selected Kit 009, Production .31, Factory .39, source/Git,
video originals and current edits remain protected. `VDP-TIMEOUT-01` is deferred.

Work volume UUID is `591578E3-8196-4B44-A575-CEC76B406789`. UUID, external USB/APFS
identity, ownership, free space and absence of open source handles were checked.
The Clean volume was not used. Both partitions share one physical SSD; they
are not independent backups. The SSD is not encrypted.

## Completed recovery-archive relocation

The private video project's 26,668,154,880-byte v21 recovery archive was copied
to an owner-only directory on Work. Its full destination readback matched the
hash from the prior full restore test. Copy plus readback took 123.414 seconds.
A new full extraction was not necessary or performed. The private project's
current-location record and recovery instructions were updated before deleting
the exact internal original; historical receipts and recipes were unchanged.

Internal free space immediately around deletion increased from 95,286,542,336
to 121,961,103,360 bytes: approximately **24.84 GiB** observed recovery. Small
concurrent system writes explain any difference from the archive's exact size.
The archive remains recoverable from SSD; original footage, editable baseline,
current film, voice data and models were not deleted or published.

## Completed warm CARLA data migration

Development root: `CarlaSim/Build-distribution-stage1-20260925`.

| Previous development path, relative to that root | External destination under `SDV-Work/AosEdge-SDV/build-data/standalone-20260925` |
| --- | --- |
| `source/Unreal/CarlaUnreal/Intermediate` | `Intermediate` |
| `cooked` | `cooked` |
| `filesystem-ddc` | `filesystem-ddc` |

Transferred **54,507,488,642 logical bytes**. All regular-file hashes, inventories,
modes and modification times matched; source identities stayed unchanged during
copy. The transfer/readback phase took 338.69 seconds. The DDC alone contains
138,624 entries. No warm data was discarded or regenerated.

Unreal's response files contain absolute paths. Three exact **development-only**
directory aliases preserve those paths. The existing build-only UAT cook alias
still resolves to the same content. This is not an installed-runtime alias or
a relaxation of the installer's no-symlink contract. Source, engine and built
Game remain at their original locations.

Before switching, originals were renamed to exact `.pre-ssd-20260929` siblings
for rollback. They were deleted only after the following acceptance passed:

| Check | Result |
| --- | --- |
| UBT outdated-action plan before / after | Both succeeded: 6.27 / 6.33 seconds |
| Compile / link actions | Zero before and after |
| Other actions | Same two pre-existing `CreateAppBundle` / `WriteMetadata` actions |
| Action comparison | Identical after normalizing only UBT's per-invocation tracing UUID |
| Cook-input alias and required map/shader/registry | Present at qualified external location |
| Guard rejects absent/wrong volume, wrong mount, read-only volume, low free space | Five injected-information negative cases passed; no physical unplug |

The engineering runner now validates the exact external UUID, three aliases,
ownership and the existing 90-GiB Work reserve before launching a build. It also
retains the internal 90-GiB guard. If SSD is absent, stop; never create a local
replacement directory under `/Volumes`. Run future build/cook helpers through
this guarded runner. Do not disconnect Work during a build or while the installed
demo is using it. This change does not qualify external-drive compile speed,
a complete fresh cook, or a clean Mac.

The first dry-run wrapper attempt failed on argument ordering **before UBT
launched**. Its empty log was preserved; the corrected, separately named run
passed. No compiler attempt was silently repeated.

Deleting the internal original trees increased free space from 121,791,860,736
to 176,575,590,400 bytes: approximately **51.02 GiB** observed recovery. The
data remains on SSD. This is actual free-space measurement, not summed clone
directory sizes.

## Runtime-family consolidation

The maintained `scripts/distribution/application.py` accepts five explicit
input-group roots. Its current source export and all five source-pinned input
groups were checked against retained external Kit 010. All 87 application
files are present; the only known pending source delta is the already-qualified
`service_packages.py` correction. No legacy temporary path is required by this
current assembly route. This gate validates input closure; it is not a new kit
assembly or installation claim.

Five exact historical payload roots were fully compared with their external
recovery locations, then retired from the internal disk. Each regular file's
bytes and mode matched; source identities stayed unchanged. The copy/verification
phase took 484.97 seconds. Small differing files were copied over external APFS
clones of the current retained input, avoiding independent full payload copies.

| Removed internal payload | Retained recovery location on Work |
| --- | --- |
| `/private/tmp/aosapp.dEU9Ge/Runtime Kit 004` | Existing `AosEdge-SDV/packages/runtime-kit-004-20260927` |
| `/private/tmp/aoshl.yj7380eu/artifacts/aosedge-sdv-demo/host-runtime` | `retired-build-inputs/20260929/host-launch-original` |
| `/private/tmp/aosedge-stage2-native.cir6B1/Host Advisory Correction 001` | `retired-build-inputs/20260929/host-advisory-original` |
| `/private/tmp/aosedge-stage1-fixed.w9IUrj/content-profile.a38_dfdp/CarlaUnreal.app` | `retired-build-inputs/20260929/standalone-relocated/CarlaUnreal.app` |
| `/private/tmp/aosedge-stage2-native.cir6B1/Preparation Selector Proof 001/catalog` | `retired-build-inputs/20260929/preparation-selector-catalog` |

The last four destinations are below `SDV-Work/AosEdge-SDV`. Complete recovery
maps, per-file verification and retirement receipts are also verified beside
them in `retired-build-inputs/20260929/recovery-receipts`. Recover into an explicit
new engineering workspace, adapting copies of historical helpers as needed;
never substitute a different-version input while claiming historical proof.

Mixed parent directories, small source scripts, manifests, local proof fixtures
and logs remain on the internal disk. Historical one-shot helpers are evidence,
not current build commands. Their old paths intentionally remain in dated logs.
The verified current assembly command and all five external group roots are
recorded in `recipe-closure-v2.json`. Its actual CLI help/import check passed.
An earlier receipt's example invocation used Python isolation that would omit
trusted sibling imports; that example was corrected before any assembly or
retirement. Its successful input checks are preserved, not overwritten.

This batch increased internal free space from 176,366,972,928 to 176,639,967,232
bytes: **approximately 260.35 MiB**, not the apparent sum of all runtime sizes.
APFS shared blocks explain the small recovery. Both the current selection and
retained Test identity were checked again before and after deletion. No source
or active deployment consumed those temporary payload paths.

## Final capacity and preservation checkpoint

At 09:51:43 UTC, after flush and external receipt verification:

| Volume | Free bytes | Approximate free capacity |
| --- | ---: | ---: |
| Internal APFS | 176,635,273,216 | 164.5 GiB / 176.6 GB |
| SDV-Work | 519,874,031,616 | 484.2 GiB / 519.9 GB |
| SDV-Clean | 349,847,244,800 | 325.8 GiB / 349.8 GB |

Compared with the 95,280,955,392-byte start measurement, the net internal increase
is **approximately 75.8 GiB / 81.4 GB**. Per-batch observations sum slightly
differently because ordinary system activity and retained verification metadata
continue to consume space. Neither clone directory totals nor nominal disk-image
capacity are reported as physical recovery.

The Stage 1 internal directory now accounts for about 21.16 GiB rather than
72.13 GiB, excluding the three relocated trees. It still contains the built
Game and source/evidence. The engine, current artifact catalogue, warm Yocto
Builder, Docker data, personal files and original video media remain retained.
The goal was meaningful headroom with rebuild capability, not removing every
file until an old round-number free-space reading was reproduced.

Retained selection: Kit 009, revision 1, no previous selection. The same Test
VM/Unit/Node remains parked, with no vehicle runtime owner. Setup and Presenter
processes remain running from their original external paths; no second CARLA
or VM was launched. The post-retirement external build guard passed again.

## Evidence and remaining gates

Ignored local evidence is under `CarlaSim/Build-distribution-stage2-20260926`:
archive transfer/retirement receipts, `warm-build-relocation-20260929/`, and
`runtime-consolidation-20260929/`. The original Stage 1 `evidence/` retains both
UBT plans and logs. Migration guards/helpers are local engineering tools; no
product security contract was weakened.

The measured capacity blocker for Kit 011 assembly is cleared. This storage
task has not executed that assembly, changed Setup's release pin, signed a
new installer, committed/pushed, or completed clean-Mac qualification.

Documentation validation passed with 314 Markdown documents, 662 stable
identifiers and 38 Mermaid diagrams. All removal was scoped to verified copies;
the removed data is recoverable from the recorded SSD locations, not from Trash.
