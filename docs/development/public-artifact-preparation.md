<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Public Artifact Distribution Preparation

- Status: review candidate; public activation is not complete
- Version: 1.2
- Prepared: 2026-10-10
- Owner: Demo Solution Team

The owner authorized preparing the materials needed to distribute the five
developer dependency archives anonymously. This follows the
[public-delivery contract](../../contracts/release-reproduction/README.md#anonymous-developer-input-delivery)
and the [activation preflight](../planning/repository-change-journal.md#2026-october-10-public-artifact-activation-preflight).
It is not a new installer, runtime release or clean-build qualification.

## Prepared materials

The original private SSD review bundle, `distribution-materials`, contains:

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

A separate `public-companion-r2` now adds the recovered GLib/Python patches,
GEOS 3.11.4 and Shapely 2.0.7 sources, the published integration/exporter source,
ONNX Runtime 1.17.1 notices, Apple header acknowledgements, five retained SDK
notices, source-build guidance and a simulator terms draft. Its 356-file
manifest includes 274 notice files. The compressed companion is 324,263,318
bytes. Its digest and manifest digest are recorded in the checkpoint. The
original sealed bundle has not been modified.

Five exact server-side Drive copies and a distinct public-format
`release-index.json` have been prepared in the separate **AosEdge SDV Lab Public
Artifacts** folder. Despite its intended purpose, that folder and its files
remain private. No recipient can yet use the ordinary anonymous preparation
route. Historical private objects, permissions and source locks are unchanged.

Large files and private review evidence remain outside Git. The private
checkpoint stores the exact workspace location and preparation tools. The
repository stores this sanitized status and the release boundaries. No access
token, certificate, password value/hash, private Drive locator, Unreal source
tree or Factory filesystem is included in the documentation.

## Content review performed

| Artifact role | Verified evidence | Limit of this review |
| --- | --- | --- |
| `host-support` | Full archive and all 92 payload hashes checked; recipes, external patches, sources and notices retained | Not a fresh build or a blanket license-compliance verdict |
| `gateway-sdk` | Full archive and all 17,398 payload hashes checked; original notices retained | License coverage of the complete SDK still requires reconciliation |
| `vehicle-bases` | Full archive and all 12 payload hashes checked; VDP V1/V2/V3 inner inventories reviewed | Metadata includes build/CI dependencies as well as runtime dependencies; these must not be misreported as all bundled |
| `factory-image` | Full archive and both payload hashes checked; read-only rootfs/home/var inventory | No full Yocto package/license manifest found in the image; boot partitions, unused space and complete source closure not qualified |
| `carla-runtime` | Complete 13,302,049,728-byte archive and all 13,987 regular-file hashes checked; private-key marker/path and bounded configuration scans found no candidates | Not a semantic inspection of cooked assets or proof of redistribution rights |

The retained local simulator differed from the pinned archive in 1,048 file
entries (519 different hashes, 528 different sizes and one missing file), so it
could not stand in for the selected archive. One authenticated acquisition of
the exact archive supplied the content check; that verified copy is cached on
the SSD. This was not a second download to test the Drive storage provider.
No simulator code was executed. The inventory contains no `Engine/Source`
files or executables named Unreal Editor, UnrealPak or ShaderCompileWorker;
that filename check alone does not classify statically linked Engine Tools.

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

## Factory scope decision

On October 10 the owner removed the separate Factory license/source-record
audit from this preparation, relying on the known upstream AosCore/Linux
licensing. Do not request the original SSD, retrieve Yocto reports, copy build
caches or rebuild Factory for that audit. It is no longer an active preparation
task or a dependency on the owner's connecting another disk.

Record this as `OMITTED_BY_OWNER`, not a passed audit or a finding that every
distribution obligation has been verified. Preserve the existing upstream
license notices, source references, image hashes and content-review evidence.
Integrity and credential-protection checks are unaffected. The original sealed
bundle remains historical evidence; the checkpoint's scope decision supersedes
its Factory-audit/resume instruction without changing any archived bytes.

## Remaining release gates

### Recovered source inputs

Both previously missing Homebrew external patches have been recovered:

- GLib 2.88.3: `Patches/glib/hardcoded-paths.diff`;
- Python 3.12.14: `Patches/python/3.11-sysconfig.diff`.

Removing only the upstream formula's bottle metadata produces the exact
installed recipe; the arm64 Tahoe bottle digest also matches the installed
SBOM. This establishes the patch correspondence without using newer formulae.
The remaining external recipe resources already passed their recipe hashes.
The libpng PNG fixture is Linux-only and was not acquired; the Snappy inline
patch remains in its original recipe.

The companion now contains GEOS/Shapely source archives and native/Python
exporter transformations with build guidance. Shapely's source hash was checked
against PyPI metadata. GEOS was obtained from the official release archive and
its acquired hash recorded; no independent upstream checksum is claimed.
No extra QEMU firmware files occur in the selected host-support archive. This
does not audit firmware inside Factory, whose separate audit remains omitted.
Complete SDK/source correspondence still requires reconciliation; the retained
SDK notices and matching OpenSSL 3.6.3 headers do not prove every static
library's provenance.

### Simulator and asset distribution

CARLA code is identified by the MIT notice at the pinned CARLA revision. The
retained asset tree has a CC-BY-4.0 notice. Keep these distinct from Unreal's
terms and record exact cooked-asset attribution, provenance and modifications.
The local asset license file alone does not establish attribution for every
asset in the packaged simulator.

Selected TBB, Ogg, Vorbis, EOS SDK and Metal Shader Converter notices were
retained from the pinned Unreal tree. ONNX Runtime 1.17.1 is identified in the
exact archive and its upstream license/third-party notices were added. The
Apple license and acknowledgements were found under `include`; the applicable
agreement for `libmetalirconverter.dylib` has not been recovered. Do not treat
the header license, or another project's redistribution of the library, as
confirmation of the binary terms. Do not publish Unreal source anonymously.
Editor/Developer descriptors alone do not classify Engine Tools; the actual
packaged and linked modules remain the relevant scope.

The retained CARLA asset checkout is at
`639d6eff5aae672da4219e9ace4a2ee891367548` with a modified road material. This is
a provenance lead, not a demonstrated correspondence to every cooked asset in
the selected archive. The terms draft includes CARLA attribution and the
Unreal product-use/disclaimer boundary, but is not an adopted end-user agreement.

Before activation, resolve the Apple binary terms, cooked-asset attribution
and applicable Unreal product-distribution conditions; reconcile the remaining
SDK source/notice mapping and adopt/deliver the end-user terms. The full archive
integrity/content scan is complete; these are separate redistribution questions,
not a reason to repeat that 13.3 GB download or request Factory build reports.

### Package delivery and activation

1. Close the remaining in-scope content, notice, source and terms gaps above
   for the exact selected bytes, respecting the Factory scope decision. Keep a
   reviewed component-to-material mapping; do not report the omitted audit as
   completed.
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

The new public record has ID `1.2.0-rc.1-source-factory-r1-public` and canonical
SHA-256 `74943dc852a160b4cfdcc6e17496a56e48ca3d644756145b7ce1cc63544c0450`.
The existing offline generator validated all five byte identities and source
pins against the historical receipt. It contains only the new delivery
locations; this is not an anonymous-access test.

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

No compiler, installer, simulator, VM or Docker workload was started. Drive
copies and uploads are private preparation only; no public sharing was granted.
Source artifacts and license texts were read, acquired where necessary and
checksummed; no downloaded code was run.
