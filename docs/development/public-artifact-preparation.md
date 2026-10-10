<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Public Artifact Distribution Preparation

- Status: public test access active; redistribution review remains open
- Version: 1.3
- Prepared: 2026-10-10
- Owner: Demo Solution Team

The owner authorized preparing the materials needed to distribute the five
developer dependency archives anonymously. This follows the
[public-delivery contract](../../contracts/release-reproduction/README.md#anonymous-developer-input-delivery)
and the [activation preflight](../planning/repository-change-journal.md#2026-october-10-public-artifact-activation-preflight).
The owner subsequently confirmed public reading of the entire prepared eight-file
folder after the remaining licensing questions were disclosed. The current
launcher can use its inputs without Google authentication. This is not a new
installer, runtime release, license-clearance decision or clean-build qualification.

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
`release-index.json` are available in the separate
[AosEdge SDV Lab Public Artifacts folder](https://drive.google.com/drive/folders/1DJQkMfbLICXe4LhROdg6pcqUHzp8Tvp7).
Its eight files have read-only access for anyone with the link, with search
discovery disabled. These are the five dependency archives, the catalog, the
source/notice companion and its README. Historical private objects, permissions
and source locks are unchanged. The companion and copied README retain their
pre-activation review snapshot; this status supersedes their access statements,
not their unresolved review findings or draft terms.

Large files and private review evidence remain outside Git. After public access
and consumer verification, the owner authorized removing the temporary local
publication workspace on October 10. Its duplicate archives and extracted
payloads are deleted; compact review manifests, receipts and preparation tools
are retained in the existing ignored local evidence area. Published files and
their permissions are unchanged. Future preparation uses the selected
workspace's managed `.tmp` instead of a separate directory at the volume root. The
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
the exact archive supplied the content check; that verified copy was removed
with the temporary publication workspace. This was not a second download to
test the Drive storage provider.
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

The Apple binary terms, cooked-asset attribution and applicable Unreal
product-distribution conditions remain unresolved, as do the complete SDK
source/notice mapping and adopted end-user terms. The owner's explicit
test-access authorization supersedes the earlier activation hold, not these
findings. The full archive integrity and bounded content scan are complete;
the remaining questions are not a reason to repeat the 13.3 GB download or
request Factory build reports.

### Public test activation

On October 10 the owner explicitly confirmed public reading of this exact
eight-file folder after disclosure of the unresolved Unreal/Apple/SDK licensing
questions. The folder permission is `anyone:reader`, with
`allowFileDiscovery=false`; all eight files inherit it. An immediate child
permission check ran before propagation had completed. Authoritative readback
then confirmed every inherited permission, without repeating the sharing write.

All eight names, sizes, provider SHA-256 values and parent identities match the
prepared receipts. The original private root and five original archives remain
private and unchanged. The anonymous reader obtained the 3,481-byte catalog,
verified its pinned record and passed one-byte HTTP range probes for all five
dependency roles. No cookies, OAuth, Google CLI credentials or API keys were
used by that reader. No archive was downloaded back for this access check.

The source/notice companion is available beside the binaries and linked from
README B1 through the public folder. It is not automatically consumed by Setup
or the launcher; its completeness and recipient-terms integration remain open.
If review requires payload changes, create a new reviewed dependency generation
rather than overwriting existing archives or locks.

The new public record has ID `1.2.0-rc.1-source-factory-r1-public` and canonical
SHA-256 `74943dc852a160b4cfdcc6e17496a56e48ca3d644756145b7ce1cc63544c0450`.
The existing offline generator validated all five byte identities and source
pins against the historical receipt. It contains only the new delivery
locations. Its observed URL and hash are now active in `PUBLIC_PIN` and the
regenerated standalone launcher. Download a fresh launcher from README B1;
previously downloaded copies retain their inactive pins. The user's actual
walkthrough, archive-consumer checksum verification and build remain separate
evidence, not results of these bounded access probes.

## References and interpretation

The review uses the [Unreal Engine EULA](https://www.unrealengine.com/eula/unreal),
[CARLA license summary](https://github.com/carla-simulator/carla#license),
[QEMU GPLv2 text](https://www.qemu.org/license-gpl-2/) and
[Yocto license-maintenance guidance](https://docs.yoctoproject.org/dev-manual/licenses.html).
They identify release obligations; this preparation report is not a legal
opinion or evidence that the product already satisfies them.

No compiler, installer, simulator, VM or Docker workload was started. Only the
prepared distribution folder was opened publicly. Source artifacts and license
texts were read, acquired where necessary and checksummed; no downloaded code
was run.
