<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R2 Preparation and Build Tooling

- Status: In progress; complete ordered developer chain and unchanged-output repeat verified
- Date: 2026-10-08
- Owner: Demo Solution Team
- Authority: [Work packet](../planning/active/work-packets/human-friendly-reproduction.md)
  and [reproduction contract](../../contracts/release-reproduction/README.md)

`lab` prepares pinned sources and builds the native/web UI, Cloud SDK, both
backend images, service profiles, Gateway and the OCI export on external storage.
It also assembles preparation, host, VM and backend inputs, the complete
application, signed Setup and media through explicit owner adapters. The base
definition remains Kit028 / Setup042 / Factory .41. Independently reviewed
successor checkpoints select new `1.2.0-rc.1` engineering inputs; historical
media, source locks and Setup's old pin are not renamed or overwritten.

## Exercised commands

Use Python 3.10 or newer. `plan` is portable and offline. Other commands require
macOS on Apple Silicon and an explicitly selected mounted external volume.
The workspace's parent must exist; the workspace must be empty or already owned
by this release/profile/volume binding. Replace the example path below:

```sh
./lab plan --profile developer
./lab prepare --profile developer --storage /Volumes/BUILD/workspace --sources-only
./lab status --storage /Volumes/BUILD/workspace
./lab verify --storage /Volumes/BUILD/workspace --sources-only
./lab build --storage /Volumes/BUILD/workspace --target presenter --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target presenter
./lab build --storage /Volumes/BUILD/workspace --target cloud-sdk \
  --kit-inputs /Volumes/BUILD/retained-kit --python /path/to/python3.12 \
  --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target brake-backend --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target tire-backend --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target backend-export
./lab build --storage /Volumes/BUILD/workspace --target brake-service \
  --functional-profile v1 --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target tire-service \
  --functional-profile v1 --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target gateway \
  --gateway-sdk /Volumes/BUILD/inputs/gateway-sdk \
  --test-tmp-parent /Volumes/BUILD/tmp --cmake /path/to/cmake
./lab build --storage /Volumes/BUILD/workspace --target preparation \
  --kit-inputs /Volumes/BUILD/retained-kit --python /path/to/python3.12 --prepare-dependencies
./lab build --storage /Volumes/BUILD/workspace --target host-runtime \
  --kit-inputs /Volumes/BUILD/retained-kit --gateway-sdk /Volumes/BUILD/inputs/gateway-sdk
./lab build --storage /Volumes/BUILD/workspace --target backend-inputs
./lab build --storage /Volumes/BUILD/workspace --target vm-runtime --kit-inputs /Volumes/BUILD/retained-kit
./lab build --storage /Volumes/BUILD/workspace --target application
./lab build --storage /Volumes/BUILD/workspace --target setup \
  --signing-identity <authorized-Apple-Development-fingerprint>
./lab build --storage /Volumes/BUILD/workspace --target dmg
```

The first build requires pinned Node 26.0.0/npm 11.12.1, Xcode's macOS SDK and
Swift compiler, and explicit dependency acquisition. `--node` and `--npm` can
select installed tools. The adapter calls the exact integration owner's
`scripts/distribution/ui_build.py` with its locked integration/Gateway sources.
npm acquisition disables lifecycle scripts. The owner denies network to build
subprocesses and performs local ad-hoc signing, not Developer ID signing.
No application is launched. Observed compiler/SDK identities enter the build
fingerprint; that does not qualify them for every release target.

The `cloud-sdk` developer target requires ARM64 Python 3.12 with `packaging`.
It preserves the selected virtual-environment entry point and calls the pinned
owner's `cloud_worker.py`. The explicit retained kit supplies only the isolated
Python base: the release pins the host manifest, which pins the Python manifest
and its files. The adapter checks both inventories, hashes and modes, and stages
only the declared base files. CARLA modules and other kit contents are excluded.
The kit must be on the selected external volume; it is not an implicit local
fallback or an alternative to the pending artifact delivery route.

First acquisition uses 41 hash-locked public PyPI wheels (24,581,670 bytes),
with bounded HTTPS requests and no ambient authorization/proxy configuration.
The existing digest cache supports exact range resume; the owner's wheel and
dependency validation remains authoritative. A repeat can reuse the completed
output without downloading or assembling again. This build makes no Cloud
connection, enrolls no identity and installs no host Python packages.

The backend targets call each component's pinned Dockerfile for `linux/arm64`.
They require an already-running local Docker Desktop whose active backing disk
is on the workspace's bound external volume. The adapter does not relocate or
start the Engine; an internal/default or remote engine is rejected. Its separate
SSD client configuration contains no registry credentials; client/build caches
also use the SSD. No image is published, tagged over an existing image, or run.

`backend-export` first verifies/reuses those images, saves their immutable IDs
without mutable tags, then calls the pinned owner's `backend_archive.py`.
That owner verifies OCI graph/blob/layer hashes, source labels, ARM64 and the
`node` runtime identity. The export contains image layers, not container/volume
data. Completed image/export receipts recover without rebuilding after an
interrupted outer state save; incomplete or corrupt results are preserved and
rejected. `status` verifies local receipts/archive; an explicit backend build
also checks the image still exists in the Engine. No clean-engine import or
runtime qualification is implied.

The service targets call the pinned Dockerfile's `export` stage, selecting
Brake `v1`, `v2` or `v3`, or Tire `v1`. First builds require
`--prepare-dependencies` for their pinned public dependencies. The adapters
verify the owner test report, native dependency identity, ELF payload and
complete export inventory. Repeating without that flag reuses a verified
export. Services are neither loaded as runtime containers nor signed, published
or installed. These builds share the external Docker/cache guard above.

Gateway requires the explicit SDK whose complete manifest is bound by
[`gateway-build-sdk.lock.json`](../../workspace/gateway-build-sdk.lock.json).
The SDK is a declared prebuilt input: accepted LibCarla artifacts plus selected
OpenSSL 3.6.3 headers/libraries and its license. No certificate store, private
configuration or host library search is copied into it. The freeze helper
records every selected file; it is not a clean source rebuild or a public
download route. SDK acquisition and redistribution remain separate gates.

The adapter enables CARLA, VISS and the owner's tests, targets ARM64/macOS 26.0,
and records CMake, compiler, SDK and Python versions. Configure/compile steps
deny network. Unit tests may bind local sockets; they do not start CARLA or a
demo. An existing short directory selected by `--test-tmp-parent` must be on
the same SSD and at most 29 UTF-8 bytes long. Its temporary child is private
and removed on exit. `CARLA_CACHE_DIR` is explicit inside the workspace, so
tests do not depend on the operator's home directory. Test loading explicitly
selects the declared SDK libraries. The output is still an unrelocated compiler
product, not a portable native runtime package.

`preparation` requires all four completed service builds and a clean committed
root checkout. That root revision owns the updated packaging recipe; the
component sources remain the exact prepared revisions. The adapter stages only
the selected Factory .41, firmware, unsigned VDP bases and service outputs on
the same SSD, then calls the existing vehicle-input assembler offline. It
preserves the Factory hash, checks VDP profiles and reviewed runtime, and does
not sign or publish anything. A new output has its own manifest and receipt;
it cannot replace the historical kit's independently pinned manifest. Repeats
reuse unchanged outputs; incomplete outputs remain available for diagnosis.
First preparation may acquire the exact pinned common-runtime Git object with
`--prepare-dependencies`; this leaves the prepared platform HEAD unchanged.

The successor packaging checkpoint explicitly selects new manifests without
rewriting Kit028's locks. The host target needs the declared SDK and retained
heavy inputs. It verifies native library ancestry, relocates/signs the closure,
and probes only version/help with network/Homebrew denied. The small backend
and VM targets prepare existing runtime input formats. VM assembly binds the
new host manifest, firmware and NIC ROM; it does not boot a guest. Complete
application export requires all five independently checkpointed group manifests.
Setup additionally requires the independent source-reviewed application digest
in `workspace/releases/1.2.0-rc.1-setup.json` and an explicit authorized stable
signer. The DMG target selects only the verified Setup for that application.
Their receipts record `BUILT_NOT_INSTALLED`: a successful build never implies
installer launch, native acceptance, notarization or publication. Swift compiler
scratch and media staging also use the selected SSD. Repeats verify file
identity and reuse completed output without signing or compression again.

| Operation | Exit | Meaning |
| --- | --- | --- |
| `plan` or `status` | 0 | Report produced; inspect gates and readiness |
| Successful source-only preparation/verification | 0 | Selected sources ready, not a complete profile |
| Successful explicit target build | 0 | Built/reused, not installed or runtime-qualified |
| Ordinary `prepare` or `verify` | 2 | Full profile remains blocked |
| Invalid input, collision, wrong pin, disk/access failure | 1 | No unsafe repair or fallback |
| Interrupted command | 130 | Owned command group stopped; partial work retained |

`--target all` now uses an explicit frozen producer plan for the ordered
developer chain. Full-source preparation remains blocked on input closure.
Operator mode needs no source roles but is not yet a complete acquisition route.

### Ordered developer invocation

The chain uses the same 17 owner builds above, including all four service
profiles. It requires prepared component sources and these explicit inputs:

```sh
./lab build --target all --storage /Volumes/BUILD/workspace \
  --kit-inputs /Volumes/BUILD/retained-kit \
  --gateway-sdk /Volumes/BUILD/inputs/gateway-sdk \
  --test-tmp-parent /Volumes/BUILD/tmp \
  --python /path/to/python3.12 --ui-python /usr/bin/python3 \
  --node /path/to/node --npm /path/to/npm --cmake /path/to/cmake \
  --docker /path/to/docker \
  --signing-identity <authorized-Apple-Development-fingerprint>
```

Add `--prepare-dependencies` only when acquisition is required and authorized.
The [producer plan](../../workspace/releases/1.2.0-rc.1-build-chain.json)
binds five exact tool revisions to six roles; it retains the base release and
the independent successor manifest pins. A tool checkout is prepared once on
the SSD and verified on reuse. It is a build input, not a branch/worktree edit.
The root's current HEAD is not silently substituted for a frozen producer.

One workspace lock covers the entire chain. Each step sees its selected
dependencies, not unrelated previous applications or signers. Existing result
receipts remain intact. A failed step stops the chain while retaining completed
work; rerunning verifies/reuses those results before continuing. Incomplete
native output is not automatically promoted. The chain does not start the demo,
change Cloud state, publish artifacts or qualify a fresh installation.

Preflight requires the inputs on the bound SSD, available tools, explicit
signing identity and at least 166 GiB free under the existing conservative
76 GiB demand plus 90 GiB reserve. This is not measured cold-build capacity.
Real chain and repeat evidence is recorded separately from fixture results.

## Storage and recovery

State binds the definition digest, profile and volume UUID. A parent lock
prevents concurrent writers. Sources, digest cache, tool caches, temporary files
and outputs stay in the workspace. Disconnects, volume replacement, symlinks,
linked cache files, wrong remotes and dirty sources are rejected. No internal
fallback, checkout reset or implicit deletion is used.

The default reserve is 60 GiB plus acquisition demand; the existing UI owner's
90 GiB reserve is retained. These are guards, not measured full-profile peaks.
The source/UI proof occupied approximately 300 MiB including sources, npm
inputs/caches, Swift cache and outputs. The retained kit was not copied.
With Cloud inputs and output, the same workspace occupies approximately
501 MiB. The Cloud output is 115,003,292 payload bytes; the selected Python base
is 36,502,557 bytes plus its manifest. The wheelhouse stages about 24.6 MB from
the digest cache for the unchanged owner recipe; no second kit is created.
Including the backend export and client metadata, it occupies approximately
582 MiB, excluding the shared Docker disk. Container layers and BuildKit cache
are inside that external Docker disk, not the checkout or internal disk.
After all four service profiles, the declared Gateway SDK and Gateway build,
the same workspace occupies approximately 1.0 GiB. This includes 182,886,138
SDK payload bytes; it does not duplicate CARLA/Unreal or Factory. At this
checkpoint the external volume has approximately 269 GiB free and the internal
volume 130 GiB free. These are point-in-time observations, not install demands.

### Docker storage maintenance

The owner separately authorized relocation of the shared Docker Desktop disk.
The initial built-in copy terminated after five minutes. An offline sparse
copy and full logical comparison preserved all data; Docker's settings selected
the external location and its documented whole-VM restore procedure supplied
the verified disk. Inventory reconciliation preserved all 22 existing images,
five containers, three volumes and 314 build-cache records (11.92 GB).
Only the verified internal duplicate and empty intermediate disk were removed,
releasing approximately 15 GiB internally. New R2 images were built afterward.

This is host maintenance, not a reproduction command or runtime change. Docker
now depends on the external disk. Ordinary test cleanup leaves shared Docker
running; a separately requested SSD disconnect requires stopping Docker and
checking open handles first. OS/application settings and small Docker host logs
retain their normal host locations; build payloads and caches are external.

Repeat preparation verifies sources without refetching. Incomplete marked
clones can resume before checkout when no user files could be overwritten.
`status` lists missing source roles. Verified unchanged build output is reused;
a completed owner receipt can be reconciled after interruption before the outer
state save. An incomplete compile remains preserved for inspection. Gateway
alone supports explicit `--resume` after diagnosis, only when its owned marker
and inputs match; it reuses compiler outputs and preserves the first stage
logs. There is no automatic blind retry or recovery of an unowned directory.

## Google Drive binding

A separate private artifact root has been created and its unshared metadata
verified. A 126-byte synthetic text probe was uploaded through the connected
Drive tool and read back with identical text; its parent, size and unshared
metadata were checked. No binary release upload or sharing change occurred.
Private account/folder identifiers stay outside public source documentation.
An administrative folder is not a release download locator.

The reader consumes a separate local non-secret binding:

```json
{
  "schemaVersion": 1,
  "releaseDigest": "<definitionDigest from lab plan>",
  "folderId": "<release folder ID>",
  "files": {"dmg": {"fileId": "<release file ID>"}}
}
```

Expected size/SHA-256 come from the release definition. Use `prepare` with
`--drive-binding <file>` and `--drive-token-fd <descriptor>` only with separately
authorized short-lived OAuth access via an inherited descriptor. Tokens must
never enter arguments, Git, receipts or reports. The connected app's Drive
access is not implicitly exported to this command-line reader.

New downloads check folder membership, download capability, size, digest and
version. Exact byte ranges permit resume; redirects cannot forward credentials.
Final size/digest and unchanged metadata are required before atomic promotion.
Cache reuse requires unchanged file identity or renewed digest verification.
Corrupt or interrupted payloads stay on the SSD and are never promoted.

The connected-tool probe does not qualify this command-line adapter, which
still has offline fixture proof only. Actual CLI authorization, release
file binding, capacity, no-overwrite upload/retention enforcement and large-file
transfer remain unqualified. Folder creation does not approve redistribution.
The local Google Cloud CLI has no credential database or application-default
credential file at its selected configuration location. No account was added
or token obtained. This is not evidence of a Drive permission failure. A
separately authorized CLI OAuth setup remains required; connected-tool
credentials must not be extracted or silently repurposed.

## Recorded proof

### Initial source and UI checkpoint

- 38 targeted tests passed, covering profiles/DAG invalidation, storage/state,
  first/repeat/resume, wrong pins/remotes, dirty inputs, corrupt downloads,
  byte ranges/access denial, secret-safe errors and owner build/reuse.
- Final integration suite: 845 tests in 47.405 seconds; 844 passed, one skipped.
- Documentation gate passed for 334 Markdown documents, 662 stable identifiers
  and 38 Mermaid diagrams. Public-source scanning included new files and passed.
- Seven public source roles remotely fetched at their exact pins; repeat
  preparation and verification passed without fetching again.
- Real Presenter, Driving Control and web build passed: 17 output files,
  2,850,432 bytes, ARM64 target macOS 26.0, source bytes unchanged. Host SDK
  was 27.0; external distribution approval remains false.
- Build fingerprint:
  `bcf927e9b787627665201c8735088df9ed0bacdaaaa6133706150d458ea0317f`.
  Repeat returned `BUILD_REUSED`, without dependency install or compilation.
- Build/test runners exited. No VM, simulator, Presenter, Setup, Docker Engine
  or demo container was started. Cloud/Production/video state was untouched.

### Cloud SDK continuation

- The real owner assembled 41 packages, 3,204 payload files and ten native
  modules from pinned sources and newly verified public downloads.
- Build host tools: Python 3.12.14 and packaging 26.3. No host runtime selector,
  installed application or Cloud identity changed.
- Build fingerprint:
  `38de3de0019d7ddfae2f9ad3889d0aa765de6ad285965bf6f35551cda31142d8`.
  Repeat returned `BUILD_REUSED` without network acquisition or owner assembly.
- This proof is `ASSEMBLED_NOT_INTEGRATED`, not an installer, native runtime
  qualification or redistribution approval. The earlier UI proof remains valid.

### Backend continuation

- Both Dockerfile builds passed and immediate repeats returned `BUILD_REUSED`.
  Source/ARM64/`node` labels were verified by image ID. No new container ran.
- Build keys: Brake
  `26386d18959b31651be84bb9e4df5abcbd68c1010755612e063a9b0e5b4d7cce`;
  Tire `bef2f165d6ee00cc5494470ec0f25ee1d4b48439ac5a0087ad0bc7f944aacc6a`.
- OCI export: 82,129,920 bytes, 25 blobs and 14 unique runtime layers;
  SHA-256 `80ab22f44058c85e9b9118911f7f04ac3ab96bba931e391ec46bae7423034cad`.
  Build key `6f29a016a631be06b5f60d7069751f018e01bb39544c3668cee386390ef438fb`.
  Repeat reused the archive without another save or validator invocation.
- Targeted R2 suite: 59 passed, including public-wheel resume, declared Python
  entry point, isolation, corruption, Docker storage guards, owner delegation
  and interrupted-receipt recovery. These do not close R4 clean-runtime gates.
- Complete integration regression after all five adapters: 866 tests in
  82.275 seconds, 865 passed and one skipped. The runner exited normally.

### Service and Gateway continuation

- All four unsigned service exports passed their exact owner checks: eight
  tests for each Brake profile and five for Tire. Each export contains 46
  files. Immediate repeats returned `BUILD_REUSED`, with no compilation or
  repeat owner invocation. Selected component sources remain unchanged.
- Build keys: Brake V1
  `1700cc0883f01d131ddae246d5cc9b6572fc01471969f75bd4463bcbb6063367`,
  V2 `63a87292a9f507df94f3dc978fe73ff4f17a327d1277b4d1903a7164ae77b966`,
  V3 `1a6293312dcdd1c62d9cda3de57c2c3a61fceefb393d6c5af8381739485e5f9a`;
  Tire V1 `0d67377410478408dcc6b88173c681ef65a980b0b0700fbb5668b3c15be912ef`.
- The explicit SDK has 17,397 files and manifest SHA-256
  `977f67ad9f67e003e78aee619ff262138d5fb49a7bda5d3e1c18fc16f55ebeca`.
  Accepted LibCarla anchor hashes were checked before freezing it on SSD.
- Gateway compiled successfully. Its initial test run found two harness
  assumptions: long temporary paths exceeded Unix socket limits, and
  LibCarla's static cache initializer required an explicit cache path when
  the scrubbed environment had no home directory. The four affected tests
  passed on the same binaries after the transient environment correction.
  The adapter then resumed the warm build and all 30 owner tests passed.
- Gateway key
  `f96c3b15d11cef62270750bc23d4dd15a9345a35b35eb97484518cce0b6d8636`;
  both binaries are ARM64. Repeat returned `BUILD_REUSED`. No Gateway runtime
  source, simulator, installed demo or operating-system home setting changed.
- 78 targeted reproduction tests passed. The full integration suite ran
  885 tests in 54.515 seconds: 884 passed, one skipped. The workspace now has
  ten verified build results across eight target types; it is not a complete
  developer profile or an installed-system qualification.

### Preparation input reconciliation

The selected Brake and Tire source revisions are `5aa652fda603` and
`f0a0f6edadb5`. The pinned integration owner's `vehicle_inputs.py` still reads
`serviceExports` from the historical Stage 0 inventory, which points to older
sources and binary hashes. That inventory is not authority for these fresh
outputs. The current build-only owner now accepts `--service-checkpoint`, a
reviewed source-tree file selecting all four service revisions and executable
digests. Its default still selects the historical inventory. Explicit choices
reject missing profiles, duplicate or mixed Brake revisions, wrong architecture,
invalid hashes, unknown fields and unsafe paths without fallback. Existing
product/test, Factory and VDP checks remain unchanged.

The [new checkpoint](../../workspace/checkpoints/reproduction-services-20261008.json)
was checked against all four real exports through the canonical input reader:
46 files each, with totals of 25,830,068 / 25,830,069 / 25,830,068 bytes for
Brake V1/V2/V3 and 24,611,237 bytes for Tire V1. Temporary same-SSD APFS clones
were removed afterward; Factory was not copied. This proves service input
composition, not a complete preparation bundle or new installer.

All 25 vehicle-input tests passed. The final integration regression ran 892
tests in 45.571 seconds: 891 passed, one skipped. The historical release
definition still validates, and `lab status` verifies all ten retained builds.
The new root-owned adapter freezes its committed producer, explicit checkpoint,
component inputs and toolchain in a separate build receipt. Complete installer
assembly still requires a new candidate selecting these new output manifests.
Do not edit the historical inventory, old release lock or prepared source
checkout, or fall back to stale products to bypass the mismatch.

### Successor preparation, host and application proof

The root-owned preparation recipe assembled Factory .41, all four newly built
service exports and VDP profiles with 7/15/23 read paths. It preserved the
Factory digest and verified common runtime commit `1fe5649f860f62573b313e1f38e5ec0f4ca1b519`.
The shallow platform clone originally lacked that historical object; explicit
dependency acquisition fetched only its reviewed commit and checked its tree
without changing the prepared platform HEAD. A path-validator shadowing bug
was also corrected before the successful preparation run.

Host assembly retained the declared standalone simulator, Python and QEMU
inputs and selected freshly compiled UI/Gateway products. Exact SDK library
ancestry was checked before native relocation and signing. Initial host trials
found two packaging-harness issues: nested macOS sandbox setup was rejected,
and a blanket clone imported incidental Finder metadata. Native help/version
probes now run in a separate network/Homebrew-denied sandbox; transfer selects
only manifest members. All four native probes passed without starting a
simulator, VM or listener. The source kit and runtime code were not altered.

The small VM package binds the new host manifest. The backend package reuses
the verified untagged OCI archive. Complete application assembly then passed
the canonical strict inventory reader, including all five manifest pins and
the VM-to-host binding. Each target's immediate repeat reused its completed
result; no heavy compilation or Factory rebuild was performed.

| Target | Verified build key |
| --- | --- |
| Preparation | `998d0d70b8a27bbf8e292cf858792dfffaaf6deef02e7d55d4bef930a97a6f0a` |
| Host runtime | `e345486fc3a9861c4ce379b1acee117b77af0126832e2f94484a6bb831683a4c` |
| Backend inputs | `490c2b29446d8ed78b3d39db5e29d6acaeab36ce459df1229f4ccb751bc427f4` |
| VM runtime | `57997265dd6d0760abdce34a5835fdcac06ae01d066829c8f0159914f15c8c09` |
| Application | `48bece9229758e9018f220b8c7eeeffe8457b78e2c08ac53dca60fd610492abf` |
| Signed Setup | `a1c53895cdde873e90c2b3c6a6770be9856fbe9a1b026f69ab8b9c0e83fd46da` |
| Complete DMG | `98ba1c5048376b7e12aa597fa42d52d3098972347259162835a9a103a99369fb` |

The [group checkpoint](../../workspace/releases/1.2.0-rc.1-packaging.json)
records the five new input manifests. The 19,767-byte application manifest has
SHA-256 `60d258db46f2277af185fd794cafb9d3928aa4b361cc56b05d64df81d281d39a`
and source revision `2597959d3070644dddc83bc5fc51e4658acf3b4a`.
It selects 28,453,306,428 logical input bytes and 89 application source files.
The separate [Setup pin](../../workspace/releases/1.2.0-rc.1-setup.json) was
committed before signing; it was not adopted from untrusted media at runtime.

Setup compiled, passed its native self-test and isolated bootstrap protocol
probe, and verified its stable Apple Development signature. It contains
2,430 Python bootstrap files. Its executable SHA-256 is
`c3a196d8ad10aaf7ed00f50bf313520569e50d8cdf8de576a8278aff479aea9e`.
A repeat reused the signature and output. This is local engineering signing,
not Developer ID, notarization, installation or distribution approval.

The complete `AosEdge-SDV-Lab-1.2.0-rc.1.dmg` was created and passed the media
owner's archive verification. It is 14,162,125,968 bytes; SHA-256 is
`7bac892b2398e38fe511de738838c23dd02e5ec26d2578afd3f6f932868cc755`.
The media receipt contains 17,697 runtime-kit files and 35,456,467,266 logical
bytes. This larger logical count includes the existing cloned Factory
catalogue as well as the preparation input; it is not another Factory build
or a measure of additional physical SSD use.

An immediate repeat returned `BUILD_REUSED` without compression or signing.
The unchanged, already archive-verified image was then mounted read-only,
without opening Finder, Setup or payload code. The canonical bundle reader
validated all 17,697 file entries and independent manifest pin. Setup's strict
signature, executable digest, bundle identifier and embedded release pin
matched. The normal detach succeeded and the private test mount was removed.
No installation, provisioning, publication or live runtime test was performed.
The workspace now holds 17 verified results across 15 target types. The final
observed free space was approximately 256 GiB externally and 132 GiB internally;
these are observations, not full-profile peak-space requirements.

Full local regression ran 932 tests in 78.072 seconds: 931 passed and one was
skipped. A separate source-only Git export on SSD, with no sibling checkouts,
passed all 109 reproduction tests in 6.388 seconds. The new root-only CI job
uses the same profile resolver and fixture suite; remote CI execution has not
been claimed. These checks do not execute a complete fresh developer build.

Two failed intermediate host output directories were removed after checking
their ownership, zero open handles and absence from completed build dependency
records. Their compact sibling logs, markers and receipts remain for diagnosis.
The temporary root-only test export was also removed. Accepted outputs and
historical media remain intact. These were APFS clones; their apparent sizes
must not be presented as physical disk space recovered.

## Remaining R2 work

1. Qualify authenticated Drive acquisition, release binding, capacity, approved
   access and retention. Keep old media unpublished until its gate closes.
2. Exact producer roles, dependency selection and whole-chain unchanged-output
   reuse now pass real verification. Cold profile reproduction, narrow recipe
   invalidation, cross-workspace cache reuse and
   full-profile capacity accounting remain open. Preserve verified results.
   Current conservative whole-tool-tree fingerprints still require refinement
   before claiming narrow invalidation for recipe changes.
3. Close effective Factory configuration, native/simulation prerequisites and
   entitlement gaps before enabling full-source preparation/builds.
4. Finish release-level build evidence and handoff. CI now separately runs the
   root-only resolver and adapter fixtures; those are not native builds or live
   tests. R3 reader-facing routes and R4 fresh environment/native acceptance
   remain separate deliverables.

## Ordered chain proof on October 8

Source checkpoint `1f95e9d` added the complete ordered developer invocation.
The source-reviewed plan selected five exact tool commits, prepared as clean
independent detached inputs on the bound SSD. No network source acquisition was
needed for these already available exact objects. Neither application generation
nor Setup's later independent pin used the current root HEAD implicitly.

Both whole-chain invocations completed all 17 steps, preserving the existing
17 build keys. Every step reported reuse. No compiler, signer, DMG compressor,
installer, simulator, VM or demo container was started by these invocations.
The second invocation took **80.09 seconds** wall clock, including source,
dependency and output validation. This is warm verification time, not a cold
build estimate. Result:

- Chain key: `a9452e449ee997e01c7536311dbe5ee726566db3dd4fe48255db08dce847e66b`.
- Final DMG key: `98ba1c5048376b7e12aa597fa42d52d3098972347259162835a9a103a99369fb`.
- Verdict: `CHAIN_BUILT_NOT_QUALIFIED`; no profile promotion or publication.

The full suite at that checkpoint ran 946 tests in 62.627 seconds, with 945
passing and one skipped. An isolated root-only Git export, without sibling
repositories, passed all 123 reproduction fixtures in 9.051 seconds. These
fixtures include ordered first/repeat execution, failure/resume, preserved
unselected results, exact detached source preparation, collision/dirty-source
rejection, volume/tool/signing preflight and separate interpreter selection.
Subsequent hardening adds malformed/empty worker-result rejection and retains
the first failed-step log across recovery; it changes no payload or input pin.
After that hardening, all 124 reproduction fixtures passed in 9.405 seconds,
and the full suite ran 947 tests in 53.878 seconds: 946 passed, one skipped.
The final source checkpoint `f2e22b6` also passed all 124 reproduction fixtures
in a new root-only export in 10.676 seconds; that temporary export was removed.

The five producer checkouts occupy approximately 306 MiB according to `du`;
existing workspace caches occupy 56 MiB. They are retained build inputs, not
extra runtime kits. The temporary root-only source export was removed after
successful tests and a zero-open-handle check; it can be recreated from Git.
No unnecessary build worker or demo process remains. Shared Docker and unrelated
containers are unchanged. Observed free space after checks was approximately
255 GiB externally and 129 GiB internally; concurrent host activity prevents
attributing the host's free-space change to this build-only check.
