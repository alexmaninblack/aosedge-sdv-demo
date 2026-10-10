<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Public Artifact Distribution Preparation

- Status: review candidate; public activation is not complete
- Version: 1.0
- Prepared: 2026-10-10
- Owner: Demo Solution Team

The owner authorized preparing the materials needed to distribute the five
developer dependency archives anonymously. This follows the
[public-delivery contract](../../contracts/release-reproduction/README.md#anonymous-developer-input-delivery)
and the [activation preflight](../planning/repository-change-journal.md#2026-october-10-public-artifact-activation-preflight).
It is not a new installer, runtime release or clean-build qualification.

## Prepared materials

A private SSD review bundle, `distribution-materials`, contains:

- 29 original installed Homebrew recipes, selected by the dependency versions
  recorded in the hash-pinned runtime manifests;
- 39 upstream source inputs: 29 primary archives and ten additional recipe
  resources/patches, all checked against the SHA-256 in those recipes;
- original retained notices from host support, gateway SDK, VDP and Python;
- supplementary CARLA code and asset notices, and selected Unreal third-party
  dependency notices from the pinned source revision;
- original license texts extracted from the checked source archives, with
  archive/member provenance;
- machine-readable acquisition results, explicit unresolved inputs, a review
  checklist and a file checksum inventory.

The 39 source inputs are a **partial corresponding-source preparation**, not
a declaration of complete license compliance. A matching upstream version is
not sufficient when patches, bundled subdependencies, firmware sources or
binary relocation/build scripts are missing. Supplemental notices must be
matched to the actual shipped components before distribution.

The [sanitized checkpoint](../../workspace/checkpoints/public-materials-preparation-20261010.json)
pins the prepared bundle's file manifest: 339 files, including 263 notice files;
the directory including its manifest/checksums occupies 321,162,679 bytes.

Large files and private review evidence remain outside Git. The private
checkpoint stores the exact workspace location and preparation tools. The
repository stores this sanitized status and the release boundaries. No access
token, certificate, password value/hash, private Drive locator, Unreal source
tree or Factory filesystem is included in the documentation.

## Content review performed

| Artifact role | Verified evidence | Limit of this review |
| --- | --- | --- |
| `host-support` | Full archive and all 92 payload hashes checked; original notices retained | Complete source/patch/firmware correspondence still open |
| `gateway-sdk` | Full archive and all 17,398 payload hashes checked; original notices retained | License coverage of the complete SDK still requires reconciliation |
| `vehicle-bases` | Full archive and all 12 payload hashes checked; VDP V1/V2/V3 inner inventories reviewed | Metadata includes build/CI dependencies as well as runtime dependencies; these must not be misreported as all bundled |
| `factory-image` | Full archive and both payload hashes checked; read-only rootfs/home/var inventory | No full Yocto package/license manifest found in the image; boot partitions, unused space and complete source closure not qualified |
| `carla-runtime` | Previously pinned inventory; 22 Python notice/metadata files checked against their individual hashes using a bounded archive prefix | The complete 13.3 GB archive was not downloaded or content-scanned in this preparation |

VDP inner archives contain 247, 247 and 248 regular files respectively. The
targeted scan found no private-key markers or credential-like filenames in
those inner files. Factory inventory covered 15,895 rootfs, three home and
1,657 var entries, without mounting filesystems, replaying journals or starting
a guest. The targeted Factory scan found no private-key markers in the selected
candidate files; it was **not** an exhaustive secret audit of the disk image.

The Factory root account setting was compared in memory with the pinned public
upstream image recipe. It matches an upstream default rather than establishing
an operator-secret leak. No value or hash was logged or retained. Default
credentials still require an explicit first-use/security review; this check
does not change or approve the authentication contract.

## Remaining release gates

### Factory build records and corresponding sources

Retrieve the preserved Factory .41 build results from the original build SSD.
The currently attached preparation SSD is not that build workspace. Required
inputs are the **selected image's** package manifest, deployed license/SPDX
records, exact recipes/layers/configuration, patches and corresponding sources.
Use the retained Yocto builder/downloads only for the selected packages; do not
publish the entire download cache or unrelated build history. No rebuild was
started as a substitute for the missing records.

If the records were not retained, record that fact and use the existing owner
workflow to agree the smallest source-closure recovery. Do not relabel a newer
build's license report as evidence for this immutable Factory image.

### Host and Python source closure

Two installed recipes reference external patch files that are not stored next
to the recipes:

- GLib 2.88.3: `Patches/glib/hardcoded-paths.diff`;
- Python 3.12.14: `Patches/python/3.11-sysconfig.diff`.

A bounded upstream-history lookup did not recover a byte-identical recipe
revision. The current Homebrew cache describes newer versions and is not used
as a substitute. Preserve this gap until the exact inputs are recovered.
The other downloaded external patches/resources passed their recipe hashes.
The libpng PNG fixture is Linux-only and was not acquired for this macOS set;
the Snappy inline patch remains in its original recipe.

Also reconcile actual firmware and wheel-bundled libraries (including GEOS in
Shapely) with their source/notice obligations and retain the exact native/Python
exporter transformations and build instructions. An upstream source URL alone
does not close a source-delivery obligation.

### Simulator and asset distribution

CARLA code is identified by the MIT notice at the pinned CARLA revision. The
retained asset tree has a CC-BY-4.0 notice. Keep these distinct from Unreal's
terms and record exact cooked-asset attribution, provenance and modifications.
The local asset license file alone does not establish attribution for every
asset in the packaged simulator.

Selected TBB, Ogg, Vorbis, EOS SDK and Metal Shader Converter notices were
retained from the pinned Unreal tree. The Apple notice was found under
`include`; do not assume that an include-file license establishes the terms of
the binary library. Resolve the actual ONNX/runtime dependency versions and
applicable Epic/EOS/binary terms. Do not publish Unreal source to anonymous
readers. Editor/Developer descriptors are not by themselves evidence of
distributable or prohibited Engine Tools; classify the actual packaged files.

Before activation, finish the simulator content review and the product's
end-user notices/terms, including the applicable Unreal product-distribution
conditions. The collected notices are review inputs, not an accepted end-user
license or legal approval.

### Package delivery and activation

1. Close the content, notice, source and terms gaps above for the exact selected
   bytes. Keep a reviewed component-to-material mapping.
2. Make notices and matching required sources available with the binary
   distribution, including a usable retrieval route for recipients. This
   preparation bundle is not automatically consumed by Setup or the developer
   launcher; that delivery integration must be checked before activation.
3. Preserve old private archives/locks. If payload changes are required, create
   and adopt a new reviewed dependency generation, never overwrite the old one.
4. Publish only the approved set to a separate public folder. Verify remote
   identity, size, checksum, parent and read-only sharing; do not download large
   unchanged archives back merely to test the storage provider.
5. Generate the distinct public catalog record, check bounded anonymous access,
   activate its observed URL/hash and regenerate the standalone launcher.
   Then perform the jointly planned user walkthrough.

`PUBLIC_PIN` remains inactive. Historical private Drive sharing is unchanged.
The existing authorization covers routine publication of the reviewed public
set; these technical/content gaps are not a request to approve the same sharing
operation again.

## References and interpretation

The review uses the [Unreal Engine EULA](https://www.unrealengine.com/eula/unreal),
[CARLA license summary](https://github.com/carla-simulator/carla#license),
[QEMU GPLv2 text](https://www.qemu.org/license-gpl-2/) and
[Yocto license-maintenance guidance](https://docs.yoctoproject.org/dev-manual/licenses.html).
They identify release obligations; this preparation report is not a legal
opinion or evidence that the product already satisfies them.

No compiler, installer, simulator, VM, Docker workload, public upload or sharing
change was used for this preparation. Source artifacts and license texts were
read, downloaded where necessary and checksummed; no downloaded code was run.
