<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R1 Release Inventory and Reproduction Readiness

- Status: R1 complete; Google Drive and product version policy accepted
- Version: 1.3
- Prepared: 2026-10-07
- Owner: Demo Solution Team

Kit028 / Setup042 / Factory .41 now has one
[resolved release definition](../../workspace/releases/kit028-setup042.json)
and a [read-only validation contract](../../contracts/release-reproduction/README.md).
It identifies 21 dependency nodes, ten source roles and five portable input
groups. None of the three reproduction profiles is yet qualified. The running
product, retained media, old tags and component source pins are unchanged.

## Selected sources and separate roles

The [Kit028 source lock](../../workspace/checkpoints/installer-kit-028-source-lock.json)
owns the full commit values. The new definition repeats selected values only
under executable consistency checks, not as an independently maintained lock.

| Role | Source publication | Original build identity |
| --- | --- | --- |
| Integration application | `638fc8d18b1e` | `22ee79e0e217` plus recorded uncommitted input hashes |
| Factory build tools | `30ae66148255` | Separate exact tools role, not the application branch |
| Gateway and Driving Control | `2e3d1164d491` | `4e384798c952` plus source correspondence receipt |
| Vehicle platform | `92a213881398` | `3fd1f8eb8e8d` |
| Brake service | `5aa652fda603` | Same selected revision |
| Tire service | `f0a0f6edadb5` | Same selected revision |
| Brake backend | `7c64adf7b3d9` | `42395715103d` |
| Tire backend | `ea2d6deec9b7` | `47cfa632a80c` |
| CARLA | `eb09b8246407` | Standalone source and content-profile corrections |
| Unreal | `9b705d6d2db5` | Restricted Apple Silicon dependency |

The historical tag `candidate/kit028-setup042` selects `b6600cfeee29`.
The 7 October documentation publication is later and does not become an
input to an already-built artifact. R2 should prepare both integration roles
at their commits, not ask a user to find a branch. No merge is needed for R1.

## Resolved input inventory

All sizes below are bytes, not allocated disk space. The pinned manifests own
individual file hashes; they are not copied into another inventory. Sizes
are taken from the selected Kit028 metadata, not from old retained kits.

| Group or artifact | Contents and format | Recorded size |
| --- | --- | ---: |
| Complete DMG | Setup042 plus matching Runtime Kit | 14,150,764,550 |
| Host input group | 14,179 files: standalone Game, Python, native tools, UI | 21,132,496,858 |
| Preparation input group | 207 files: Factory and unsigned VDP/service exports | 7,121,339,444 |
| VM support group | Six files: firmware, ROM, notices and DNS helper | 2,291,482 |
| Cloud input group | Private Python and 41 pinned wheels, 3,204 files | 115,003,292 |
| Backend input group | OCI archive plus its manifest | 82,130,944 archive bytes |
| Factory image inside preparation | Raw arm64 `main-qemuarm64.img` | 6,997,147,648 |

The application receipt records 28,453,262,020 logical input bytes. Nested
figures overlap: do not add the Factory to preparation again, or the compressed
DMG to its installed payload as an installed-size claim. The five input totals
exclude application source and temporary installation/build space. Peak space,
download timing and supported builder requirements must be measured separately.
No extra archive, Factory, VM, engine build or kit copy was created for R1.

The host manifest includes 20,963,896,021 simulator bytes, 78,352,359 native
tool bytes, 79,117,634 Python bytes, 6,637,766 OpenSSL bytes and 4,493,078 UI
bytes. Operators and default developers reuse this heavy simulation input;
they do not need Unreal Editor or its build tree to run the demo.

## Owner and acquisition map

| Dependency | Owner and canonical recipe | Acquisition and remaining boundary |
| --- | --- | --- |
| Presenter and native host UI | Integration `scripts/distribution/ui_build.py`; npm lock | Public pinned source; Node 26.0.0 and npm 11.12.1 are pinned; exact native compiler/SDK closure still required |
| Gateway and Driving Control | Gateway `CMakeLists.txt`, `tools/KeyboardControl.swift` | Public source; linked native dependencies need a reproducible build closure |
| CARLA and Unreal | Simulation forks; CARLA content/road-sampler profile recipes | Exact Git revisions recorded; Unreal entitlement, assets and complete cook provenance required for full source |
| Native host and Python | Integration native bundle and private-Python exporters | Prebuilt relocation is implemented; exact upstream source recipes are not equivalent to those exporters |
| VM support | Integration `scripts/distribution/vm_inputs.py` | Firmware/ROM hashes in VM manifest; upstream build closure still required |
| Factory, AosCore, KUKSA | Platform Yocto layer plus separate integration Factory tools | Public source pins and patches; resolved Factory .41 configuration must be frozen |
| VDP | Platform runtime plus integration vehicle-input export | Three unsigned functional profiles; future Cloud versions allocated per run, never reused from a prior Test |
| Brake and Tire containers | Each service's Dockerfile and product build tool | Apache-2.0 project source; base digest, dated Debian snapshot and native dependency commits already pinned; acquisition and clean-build proof remain open |
| Brake and Tire backends | Each backend's Dockerfile; integration OCI archive exporter | Apache-2.0 project source; Node base digest and build inputs pinned; hosted archive and fresh-build proof remain open |
| Cloud tools | Integration cloud-worker exporter and wheel lock | 41 public PyPI wheels with URLs/hashes; review each license, preserve adapter source lock, no account secrets in kit |
| Setup and DMG | Integration setup builder and complete-DMG assembler | Existing local Apple Development output; no public delivery/notarization claim |

Every recipe path is recorded with its owning source role in the manifest and
is checked by the optional source-workspace gate at that exact local Git object.
The current candidate has 28 unique recipe paths. This proves a recipe
location, not that an exporter is a complete source compiler or that an external
user has all inputs. Component licenses remain with their owners; the table is
an access inventory, not a redistribution approval.

## Factory and preparation details

Factory .41 metadata selects platform `3fd1f8eb8e8d`, AosCore application
`9d613a46df3c7f550062e2f19ae3406c57715694`, library
`5560291ba6914e36a5b841ade4d8fc54134a9e91` and API
`af3552a0a5eb0237eff7f5f183780ca46c339cd3`. KUKSA authorization and source-time
patches remain in the pinned platform layer; they are not substituted by a
different upstream baseline. The full Yocto recipe/download closure, including
the effective KUKSA recipe revision, must be captured before full-source proof.

The Factory-tools template and `scripts/guest/r6-1-yocto-build` at
`30ae66148255` still contain rootfs `.11` and platform `a12c0aa7f8a6`.
The guest driver explicitly checks those old values. These files alone are not
the final .41 recipe.
The actual build receipt identifies .41 and platform `3fd1f8eb8e8d`; using the
template unchanged would select a different build. Keep an explicit
`factory-config` gate until resolved generated configuration and overrides are
captured and the driver is aligned in a new source revision. Do not edit the
historical tools commit or call it the current recipe merely because it is pinned.

The builder script already pins an Ubuntu ARM64 base image and several tools.
Its guards require 32 GiB host memory, 260 GiB initial host free space and
60 GiB operational free space. These are existing builder guards, not measured
end-user requirements. The 16 GiB M1 runtime test does not qualify this builder.
Remaining environment/dependency closure is not solved by preserving a warm VM.

Preparation binds VDP V1/V2/V3 source versions `1.0.16`, `2.0.0`, `3.0.0`,
with 7/15/23 read paths. Their common runtime revision is
`1fe5649f860f62573b313e1f38e5ec0f4ca1b519` and tree
`cfc2e0c790c179ddc10f734f0def0361535154c0`. The preparation manifest records
per-module and per-service export hashes. Brake has three profiles; Tire has
one. Signing/enrollment uses private local state later and is not a build input.

## Container source inputs already pinned

Both service Dockerfiles select the same Debian ARM64 image digest,
`6bd27d44e6c32a66bbd72d7cb2b76a8ae3497ec2e5274a81abd1b37f6013fa1f`,
and the Debian/debian-security snapshots at `20260901T000000Z`. The package
list is in each Dockerfile; this is not a floating current Apt repository.
They also pin Abseil `54fac219c4ef0bc379dfffb0b8098725d77ac81b`,
Protobuf `a4cbdd3ed0042e8f9b9c30e8b0634096d9532809`,
gRPC `e5ae3b6b44bf3b64d24bfb4b4f82556239b986db` and KUKSA client source
`30e5c13abc496d0b39aaa6c25acebb088b9902e3`. Selected gRPC submodules are
gitlink-pinned by that parent commit. OpenSSL 3.2.6 is archive-hash pinned.

Both backends select Node 26.0.0 at image digest
`34881fd97f67bed28bbfe3614a219e7d793e2b7554de33eaf71797d9dc8a35cc`.
Brake uses the repository npm lock and npm 11.12.1; Tire copies its native Node
application without an npm installation step. These existing pins narrow the
remaining work to acquiring declared inputs, checking redistribution and
proving clean builds. Do not replace them merely because a preliminary R1
inventory called their base images unresolved.

These are service build dependencies, not the selected Factory KUKSA or host
OpenSSL identity. Those owners and artifacts retain separate pins.

## Selected delivery route

The release owner selected Google Drive in the existing Google Workspace
account instead of Amazon S3. Source tags, release metadata and instructions
remain in the existing public Git repository. The complete DMG and approved
heavy dependency bundles use a dedicated Drive release folder. Approved testers
receive read/download access; restricted engine source, credentials and private
runtime state do not enter this distribution route.

GitHub release assets must each be smaller than 2 GiB. The current single DMG
is 14,150,764,550 bytes, so GitHub Releases cannot directly deliver that same
one-file installer. Splitting it would add a reassembly step to the agreed
operator experience. See [GitHub release limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

Each released artifact uses a separate file, with its Drive identifier, byte
count and SHA-256 bound to the release record. Published bytes must not be
replaced in place. A file identifier alone is not an integrity guarantee;
verification rejects changed content. Preserve every input of supported
releases; no automatic expiry or deletion is introduced by this decision.

Operators download one DMG through the shared Drive page. R2 automation uses
the authorized Drive API, with resumable downloads and the existing integrity
boundary, rather than scraping browser download pages. OAuth credentials stay
outside Git, reports and cache keys. The installed demo does not depend on
Drive after acquisition. See [Drive downloads](https://developers.google.com/workspace/drive/api/guides/manage-downloads).

R2 must bind the actual folder/account, verify capacity and Workspace external
sharing policy, configure the authorized API access, and test acquisition.
These are delivery implementation checks, not a reason to repeat R1's source
inventory. Selection does not create a folder, grant anyone access, upload a
file or waive binary redistribution review. The current candidate remains
unpublished with a null download locator; its concrete retention configuration
is not yet provisioned.

The release owner also accepted `MAJOR.MINOR.PATCH`, candidate suffix `-rc.N`,
and tags `sdv-lab-v<version>`. The first new candidate is `1.2.0-rc.1`, followed
by `1.2.0` after qualification. Neither is a retrospective rename of Kit028 or
`demo-v1.1`. The [version policy](../../contracts/release-reproduction/README.md#version-policy)
separates accepted names from actual artifact/tag publication.

## Readiness and next work

The new gate checks schema, source/CI consistency, artifact identities, complete
profiles, references and graph cycles. Optional existing-kit validation binds
the application and five input manifests, including VM-to-host consistency.
It does not rehash 28 GB of payload or rerun an installed demo.

| Remaining gate | Owner and next action |
| --- | --- |
| Artifact delivery implementation | Google Drive selected; R2 binds the folder, verifies account access/capacity and downloads, and enforces the no-overwrite and supported-release retention rules |
| Candidate and release publication | Apply the accepted version policy to new source/build records only; historical Kit028 productVersion stays null |
| Clean source and build automation | R2 creates resolver/adapters and new clean build receipts; old Kit028 bytes remain unchanged |
| Native toolchain and container proof | Close compiler/SDK/native inputs; retain existing container base pins and prove their acquisition/builds |
| Full source dependencies | Close effective Factory recipe, cooked assets, native library/firmware source closure and entitlement checks |
| Reproduction and release qualification | R4 proves each claimed profile; current native and distribution gates remain as recorded in the baseline |

**R1 is complete:** its inventory, specification and validator are implemented,
and the delivery and version policies are accepted. The definition records
unresolved build inputs explicitly instead of treating them as available.
Implementing their adapters, actual Drive acquisition and reproduction proof
remain R2/R4 work. No profile reports reproducible, and native E2E acceptance
is not being reclassified as an R1 definition test.

The next block is R2: a product-facing entry point for exact source preparation,
profile preflight, verified artifact acquisition and existing build adapters.
No runtime, installed media or historical source pin changes merely because
R1 is complete.
