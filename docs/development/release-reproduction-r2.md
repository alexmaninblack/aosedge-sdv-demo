<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R2 Preparation and Build Tooling

- Status: In progress; complete ordered developer chain and unchanged-output repeat verified
- Date: 2026-10-09
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

The source-Factory campaign can acquire its binary inputs separately:

```sh
./lab inputs plan
./lab inputs prepare --storage /Volumes/BUILD/declared-inputs \
  --binding /private/path/developer-inputs.drive.json \
  --simulation-binding /private/path/simulation-inputs.drive.json \
  --account authorized-reader@example.com
./lab inputs verify --storage /Volumes/BUILD/declared-inputs
```

`prepare` reports `kitInputs`, `gatewaySdk` and `factoryInputs`. Use all three
reported paths with the frozen source-Factory build plan and its checkpoints;
the sparse result is not an installable kit or an input to the historical
default Factory selection. Initial uncached acquisition needs an authorized
Google CLI account. Prepared-output verification and repeat need no account.
The private binding files are delivered to approved readers outside Git. Their
file IDs select transport only; checked-in SHA-256 locks remain authoritative.
Host compiler/SDK and pinned build-tool prerequisites still apply.

Maintainers use `lab inputs export` with explicit retained `--kit-inputs` and
source `--factory-inputs`, review the generated lock, then `lab inputs upload`
with an explicit private folder and authorized account. These commands never
rebuild CARLA/Factory, change sharing or publish runtime packages to AosCloud.

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
fallback or a replacement for verified artifact acquisition.

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

For the independently pinned source-Factory campaign, add all four selections
to that invocation; do not replace the default historical checkpoint:

```sh
  --build-plan workspace/releases/1.2.0-rc.1-source-factory-build-chain.json \
  --factory-inputs /Volumes/BUILD/factory41-clean/factory-results \
  --input-checkpoint workspace/releases/1.2.0-rc.1-source-factory-packaging.json \
  --release-checkpoint workspace/releases/1.2.0-rc.1-source-factory-setup.json
```

These are additional arguments to the complete command above, not a standalone
shell command. They select the separately built image, group manifests and
Setup pin, while reusing unchanged CARLA and component results.

## Storage and recovery

### Device renumbering after reconnect

macOS can assign a new device number when the same external volume is remounted.
For completed manifest-backed input groups, an explicit recovery command is
available:

```sh
./lab revalidate --storage /Volumes/BUILD/workspace --target host-runtime
```

Supported targets are `host-runtime`, `preparation`, `vm-runtime` and
`backend-inputs`. The command checks the original volume UUID, permits only a
device-number change in recorded file metadata, rehashes affected payloads
against their existing manifests, and preserves the original receipts before
refreshing device stamps. A repeat on unchanged stamps hashes nothing. Changed
content, missing receipts or a different volume are not adopted or repaired.
This does not yet revalidate historical application/media receipts or extracted
simulation dependencies; it must not be described as recovery of every cache.

### Reusing a declared cache

Use a completed workspace's digest cache explicitly when preparing another
workspace on the same external volume:

```sh
./lab space --storage /Volumes/BUILD/new-workspace \
  --cache-from /Volumes/BUILD/existing-workspace
./lab cache --storage /Volumes/BUILD/new-workspace \
  --cache-from /Volumes/BUILD/existing-workspace
./lab prepare --storage /Volumes/BUILD/new-workspace --sources-only
```

`space` does not create the new directory. `cache` initializes only the ordinary
build-workspace binding and copies eligible complete cache objects through APFS
copy-on-write clones. It neither prepares sources nor downloads missing objects.
The source workspace remains unchanged. Each clone is hash-verified before
promotion; no full-copy fallback, hardlink or overwrite is permitted. An exact
prepared integration source supplies the selected wheel lock, including when
it is read from the explicitly declared donor. Arbitrary donor files and build
outputs do not become trusted cache entries.

The report separates file sizes from allocated-block observations and lists the
existing build guards. It does not add the Factory twice to its input group or
claim that APFS clones occupy the sum of their apparent sizes. Cache absence
does not imply a retained input is unavailable. In particular, historical DMG
and Factory bytes are not copied into the cache just to make its report green.
The 166 GiB single-step guard and 285 GiB sum of step reservations are not cold
peak measurements. Full-source and unreviewed-plan capacity remain gated.

### Existing workspace observations

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
metadata were checked. That initial probe changed no sharing and uploaded no
binary; the successor delivery proof below is a separate operation.
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

The original connected-tool probe did not qualify command-line acquisition.
On October 8, the owner separately authorized Google CLI login with its disclosed
Drive/Cloud scopes. The explicit Workspace account was authenticated, upload
capacity checked and a private successor release folder created. No access
grants or unrelated Cloud changes were made. Credentials remain in the Google
CLI store; connected-tool credentials were not extracted.

The new explicit maintainer transport uses the reviewed
[1.2.0-rc.1 descriptor](../../workspace/releases/1.2.0-rc.1-delivery.json), not the
historical Kit028 definition. It pins the existing 14,162,125,968-byte DMG and
its exact SHA-256, media producer, build key and application manifest. It does
not rebuild, sign, install or qualify the candidate. This is private engineering
delivery, not approval for public binary redistribution.

```sh
python3 -B scripts/drive-delivery upload \
  --descriptor workspace/releases/1.2.0-rc.1-delivery.json \
  --storage /Volumes/BUILD/private-delivery \
  --folder-id <authorized-private-release-folder> --account <authorized-account> \
  --source /Volumes/BUILD/output/AosEdge-SDV-Lab-1.2.0-rc.1.dmg
python3 -B scripts/drive-delivery download \
  --descriptor workspace/releases/1.2.0-rc.1-delivery.json \
  --storage /Volumes/BUILD/private-receiver \
  --folder-id <authorized-private-release-folder> --account <authorized-account> \
  --file-id <verified-file-id>
```

Supply `--gcloud` when the CLI is not on PATH. Login is a separate explicit
operation, never an automatic side effect. A new storage directory must have
an existing parent; the existing external-volume and 60 GiB reserve guards
apply. The uploader records a pre-generated file ID before starting, reconciles
acknowledged ranges after response loss and verifies remote metadata afterward.
Matching existing files are reused; conflicting same-name files fail without
overwrite or deletion. Session URLs remain in memory; after process loss an
absent completed file can require retransmission with the same reserved ID.
The downloader reuses the existing bounded range/SHA cache path and refreshes
its in-memory CLI token for new requests. Completed payloads are never adopted
as the historical Kit028 artifact or as a profile qualification receipt.

Twelve offline tests cover first/repeat, response-loss reconciliation, preserved
intent, cross-workspace reuse, name/content conflicts, malformed ranges,
credential endpoint guards and private-folder identity. The real large-file
upload, complete SHA-256-verified download, controlled interruption/resume and
idempotent repeats subsequently passed. Approved-reader access, public source
handoff and release qualification remain separate gates.

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

1. Private successor DMG upload, acquisition, file binding, capacity and repeats
   now pass. Complete build-input acquisition and approved-reader handoff
   separately; preserve supported inputs. Historical media remains unpublished.
2. Exact producer roles, dependency selection and whole-chain unchanged-output
   reuse now pass real verification. Cold profile reproduction and measured
   full-profile capacity remain open. Cross-workspace
   digest-cache reuse and read-only capacity accounting now pass local proof;
   neither establishes the cold-build peak. Preserve verified results.
   New packaging adapters use target-specific file fingerprints, with real Git
   change fixtures. Existing frozen producers keep their old keys; newer owner
   adoption requires a separately reviewed candidate and output checkpoints.
3. Close effective Factory configuration, native/simulation prerequisites and
   entitlement gaps before enabling full-source preparation/builds.
4. Finish release-level build evidence and handoff. CI now separately runs the
   root-only resolver and adapter fixtures; those are not native builds or live
   tests. R3 reader-facing routes and R4 fresh environment/native acceptance
   remain separate deliverables.

## Factory source build on external storage

The October 8 campaign includes rebuilding Factory .41 while retaining the
reviewed prebuilt CARLA dependency. The stopped Builder was copied to the
selected SSD with an SSD-local Ubuntu backing image. Base SHA-256, seed/trust
file equality, `qemu-img check`, complete virtual disk content comparison and
boot on the new disk passed. After the source build, repeat preparation and a
second clean disk check, the obsolete internal disk and Ubuntu base were removed.
The working Builder, downloads, sstate and original guest build remain on SSD.

The prior effective path combined a generated .11 configuration, a warm .27
`auto.conf` and the final .41 qualification override. The new adapter renders
.41 from the immutable template and checkpoint, creates nine independent exact
source checkouts, and executes the pinned Moulin configuration generator in
a separate empty build directory. It does not copy the warm configuration,
native objects or Factory image. Downloads and sstate are explicitly reused.
The real source build at tool checkpoint `78f837a` passed on the relocated
Builder. Its new read-only image is 6,997,147,648 bytes, with SHA-256
`e7c9e3b20c08a91f9072014ece0861d8ae34787ef14d4ef9b50693c062439d57`.
The historical image and its checkpoint remain unchanged. Evidence is retained
in the external `factory41-clean/factory-results/` directory; the producer
manifest records exact source/tool revisions, effective configuration and tests.

The effective Factory version is .41, architecture ARM64, and KUKSA revision
`30e5c13abc496d0b39aaa6c25acebb088b9902e3`. The existing manager triplet passed
effective-pin and actual-source verification. Qualification before image
construction included 466 native GTest/lock passes (two skipped and two disabled
cases remain explicit), successful KAC/Provider/verifier suites, five Factory
configuration regressions, and 167 KUKSA test passes with 15 ignored cases.
Package QA, image QA, six-partition assembly and the guest-to-host transfer
digest passed. Known build-path warnings remained; no QA bypass was added.
This proves source construction with retained caches, not a cache-cold build,
blank-Builder acquisition, byte identity with the earlier image or live E2E.

Two host-adapter defects were isolated without rebuilding the finished image:

- Initial macOS transfer added four AppleDouble sidecars while every source
  digest remained correct. The sidecars were quarantined as evidence. Transfers
  now disable both extended attributes and macOS copyfile metadata; a real
  metadata-bearing fixture rejects recurrence.
- The existing Factory owner temporarily changes the Platform layer path to
  its committed export. The clean-build adapter now requests exact restoration
  before shutdown, preserving the preparation hashes. Unexpected concurrent
  changes are rejected, not overwritten. Exact restoration and subsequent
  preparation reuse passed on the actual Builder after the first completed run.

After these corrections, the root offline suite ran 1,015 tests: 1,014 passed
and one skipped. The separate Factory build-tool suite passed all 27 tests.
Historical release-definition and documentation checks passed. The Builder and
its DNS helper were cleanly stopped and their process/listener exit verified.

```sh
./lab factory plan
./lab factory prepare --storage /Volumes/BUILD/factory41-clean \
  --builder-root /Volumes/BUILD/yocto-builder \
  --platform-source /path/to/aos-vehicle-platform
./lab factory build --storage /Volumes/BUILD/factory41-clean \
  --builder-root /Volumes/BUILD/yocto-builder \
  --platform-source /path/to/aos-vehicle-platform
```

The Builder must already be prepared on that SSD. Source acquisition currently
uses the explicitly selected platform repository and the retained Builder's
Git object cache; fresh independent checkouts verify exact commits. This is
not proof of downloading every prerequisite onto a blank Builder. Source fixes
do not automatically change frozen developer-chain producers or installer pins.
After transfer/build checks, remove only verified obsolete internal copies,
preserving source, keys, the historical Factory and required cache inputs.

The cleanup removed only the old internal `local/r61-yocto-builder.qcow2` and
`cache/ubuntu-22.04-server-cloudimg-arm64.img` below the previous Builder root.
Exact identity, stopped owners, zero open handles, matching base bytes and the
SSD-only backing chain were checked first. Measured internal free-space growth
was 91,266,564,096 bytes, approximately 85 GiB; about 220 GiB remained free.
The replacement is retained on SSD, not in Trash. Small old logs, seed/trust
metadata, Production's .31 dependency, historical Factory images, source/assets
and private video material were preserved. No shared Docker lifecycle changed.

External free space after the new build was approximately 106 GiB. That is above
the image campaign's 90-GiB reserve but below the frozen developer chain's
166-GiB admission guard. Downstream packaging must resolve this capacity gap and
independently bind the new image; it must not silently reuse the historical
Factory, lower the guard or write build data back to the internal disk.

### SSD capacity audit on October 9

The connected 1,000.2-GB Samsung T5 has two separate GPT partitions and APFS
containers, not two volumes sharing capacity. Work is limited to 650.0 GB:
535.2 GB is physically allocated, including container overhead, and 114.8 GB
is free. Clean reserves the other 350.0 GB and contains only Finder, Spotlight
and filesystem-event metadata, less than 1 MB of volume data. Neither volume
has APFS snapshots. Reclaiming the empty trailing Clean partition would allow
Work to grow to approximately 1 TB, with approximately 465 GB free before
subsequent writes. Consolidation was initially deferred for the filesystem
warning below. After the separate cleanup and the operator's renewed explicit
instruction, standard in-place expansion completed as recorded below.

Directory figures are allocated-block accounting, **not mutually exclusive
physical usage or guaranteed cleanup recovery**. APFS clones explain why these
figures together exceed physical allocation:

| Retained area | Approximate GiB | Interpretation |
| --- | ---: | --- |
| Standalone CARLA build/cook/DDC and Metal-profile outputs | 128.7 | Warm inputs and several related output copies; dependency review required before cleanup |
| Yocto Builder including its base and caches | 110.5 | Relocated from internal storage and enlarged by the new Factory source build; retain |
| CARLA LFS objects | 40.4 | Relocated source-asset store; retain |
| Runtime/preparation build inputs | 26.4 | Retained producer dependencies, not another running instance |
| Docker data | 15.0 | Shared infrastructure, including unrelated Watt data; no prune |
| Installed test stores | 196.4 | Old registrations and cloned payloads; owner/selection/dependency closure required |
| R2 reproduction workspaces | 113.0 | Includes new Factory, verified outputs and compressed/unpacked simulation dependency |
| Kit026 and Kit028 directories | 66.1 | Rollback and accepted media inputs; clone-shared |
| Two retained full DMGs | 26.4 | Kit026/Setup040 and Kit028/Setup042 |
| Private retained media | 24.8 | Protected recovery material |
| Staging | 9.4 | Requires producer/consumer reconciliation before retirement |

The separate Quant Trading Lab directory accounts for 69.6 GiB by the same
directory method; its contents were not inspected or changed. OllamaModels
has no allocated payload. Docker.raw advertises approximately 994.6 GB of
virtual capacity but allocates only approximately 16.1 GB (15.0 GiB); it does
not consume the entire SSD. Moving retained build inputs off the internal disk
transfers their storage cost to this SSD rather than eliminating that cost.
The audit does not establish an exact exclusive-byte attribution of historical
growth. Protected macOS metadata directories were not traversed.

The partition map verifies successfully. However, Work's APFS check repeatedly
reports `Resource Fork xattr is missing or empty for compressed file` for inode
2291193. A standard unmounted First Aid repair was performed once. It exited
zero and reported success, but the following verification reproduced the same
warning and intermediate corruption message. Therefore the final success line
is not treated as evidence that this defect was resolved. The object was not
located in accessible directory traversal; file-ID access returned permission
denied. No permission bypass, attribute deletion, formatting or blind repair
loop was attempted.

At the end of the read-only audit both partitions, Work's UUID and all payloads
remained; no capacity gain was claimed. The separately authorized cleanup below
subsequently removed obsolete payloads without changing partition boundaries.
The initial recommendation was to confirm backup coverage and resolve or
reassess this warning before changing partition boundaries. Apple's
[First Aid guidance](https://support.apple.com/en-ie/102611) recommends a current
backup before disk repairs. Builder, simulator and Docker remain stopped;
the idle Docker network helper holds no files on the SSD. The subsequent
consolidation closes the capacity gap, not the compressed-file warning.

### Authorized Work cleanup on October 9

The operator approved the first cleanup batch. Seven exact obsolete targets
were removed, after preserving application/input manifests and receipts:

- The unused Editor-era `staging/zen-retention-20260928.KutobN` cache.
- `AosEdge-SDV-Lab-Kit026-Setup040.dmg`; the unpacked Kit026 rollback remains.
- One payload in `install-tests/stage3-clean-store-001/versions` and four in
  `install-tests/stage3-kit012-store-001/versions`. The four owning registrations
  were normally unselected with revision checks before deletion. Their private
  state, history and registration metadata remain; restoring a removed version
  requires reinstalling its payload rather than simply selecting it.

The first apply attempt stopped at strict store validation before any selection
or payload mutation. Finder had added `.DS_Store` to each of the two old store
roots. Both exact metadata files were verified, preserved outside the stores
and removed from their original locations. Product validation was not weakened;
the subsequent normal unselect and cleanup passed. Store/state/payload leases,
zero-consumer and mounted-image checks protected the deletion window.

| Removed category | Observed free-space gain in bytes | Approximate decimal GB |
| --- | ---: | ---: |
| Old Editor Zen cache | 10,045,407,232 | 10.045 |
| Kit026 full DMG | 14,141,624,320 | 14.142 |
| Five old installed payloads together | 43,040,768 | 0.043 |
| Total | 24,230,072,320 | 24.230 |

Free space increased from **114,761,785,344** to **138,991,857,664 bytes**,
approximately **139.0 GB / 129.4 GiB**. The large old-installation directory
totals were clone-shared, not physical recovery. The developer-chain admission
threshold remains 166 GiB: approximately **39.25 GB / 36.6 GiB** is still missing.
No build guard was lowered and no new build was started.

Kit011 and its retained run, Kit026 rollback, Kit028 and its full DMG, both
historical and newly built Factory inputs, the Builder/base/caches, CARLA warm
and staged outputs, simulation download archives, source/Git, credentials,
private video, Docker and unrelated projects remain. Protected artifact
identities were unchanged. No runtime was started, no Cloud object changed and
the Work/Clean partitions were not modified. The earlier APFS warning was not
retested or claimed repaired by this cleanup.

Removed payloads are not in Trash. Zen can be regenerated; old software can be
reconstructed from retained sources/manifests, and Kit026's unpacked rollback
remains available. Exact target paths, original identities, metadata copies,
normal unselect results and per-target/free-space receipts are retained under
`CarlaSim/Build-distribution-stage2-20260926/cleanup-20261009-work/`.

### Work and Clean consolidation on October 9

After the unresolved warning and cleanup results were disclosed, the operator
explicitly requested proceeding with one Work volume. The exact external T5,
both volume UUIDs, physical-store order, empty Clean contents, absent Clean
snapshots and zero open consumers were rechecked. No independent backup was
claimed. A helper's initial preflight used an incorrect plist key and stopped
before any disk mutation; the observed key was corrected before execution.

Standard `diskutil apfs deleteContainer` removed only the empty trailing Clean
container/partition. Standard `diskutil apfs resizeContainer` then expanded the
existing Work container to fill the space. Its built-in storage check repeated
the compressed-file warning, also reporting a flag-clear warning and an
orphan/invalid `com.apple.decmpfs` attribute for the same object. The native
check exited zero and permitted growth. No force, check bypass, direct metadata
edit, full-disk erase or repeated mutation was used.

Final state:

- One user data volume, `SDV-Work`, plus the unchanged EFI system partition.
- Work container capacity: **999,995,129,856 bytes**, approximately 1 TB.
- Free space: **488,943,783,936 bytes**, approximately **489 GB / 455.4 GiB**.
- Original Work UUID `591578E3-8196-4B44-A575-CEC76B406789`, mount path, ownership
  enforcement and read/write access preserved.
- Protected Kit026/Kit028, new Factory, Builder/base and Kit011 artifact
  identities unchanged; final partition-map verification passed.

Clean's empty filesystem metadata was removed, not placed in Trash. It contained
no user payload. No Work payload was deleted by consolidation. The 166-GiB
downstream admission requirement is now satisfied; runtime/build qualification
and new Factory packaging remain separate. The metadata warning is **not claimed
repaired**. No demo, Docker or Builder process was started. Compact before/after
identity records and native command logs are retained under
`CarlaSim/Build-distribution-stage2-20260926/merge-work-clean-20261009/`.

## Source Factory downstream packaging on October 9

The independent source-image checkpoint binds the new .41 image and its
native/package/image evidence without changing the historical Factory checkpoint.
Preparation accepts an explicit external `--factory-inputs` result directory;
firmware and unsigned VDP inputs retain the original manifest checks. The owner
verifies the image digest at transfer and records a separate preparation key.

Downstream adapters accept committed `--input-checkpoint` and, for signed media,
`--release-checkpoint` files. Matching upstream manifests are selected by exact
hash, not the newest result, while prior build receipts stay intact. These
checkpoints are included in the producer fingerprint. Default historical build
selection is preserved. Fixture coverage includes first/repeat behavior,
independent candidate selection, wrong volume, writable image, altered manifest,
failed Factory gates, missing Setup selection and changed application digest.

Preparation completed with key
`1c1ba22a1c1d6db947da0f8c4c02a493eedae3a48ddfc987d977708269c96171`;
its 51,158-byte manifest SHA-256 is
`613413e6ba0563fe3cafbc17e9145d04cb86fd6a8956f4815d7c4b6cdfe063c3`.
The independent source-Factory packaging checkpoint selects it while retaining
the unchanged host, Cloud, VM and backend input pins. No image was rebuilt.
The root regression ran 1,023 tests: 1,022 passed and one skipped.

The existing disposable VM owner booted the source image through a new SSD-local
overlay with external networking restricted. It reached `main login:` and
completed ACPI shutdown with the process gone. This is an offline boot smoke,
not installed service, Cloud or full E2E qualification. The first harness attempt
failed before overlay/process creation because the SSD root was not writable;
using the existing user-owned SSD directory fixed that test-path issue without
changing filesystem permissions or the image.

Downstream reuse exposed a separate reproducibility defect: macOS remounting
changed `st_dev` from 16777243 to 16777241 while the external volume UUID, file
inodes, sizes, times and modes remained unchanged. Legacy output stamps treated
that as payload change. Explicit `lab revalidate` now checks the original volume
binding, rejects changes beyond the device number, hashes every affected payload
against its existing manifest, preserves the original receipt and refreshes only
the device stamps. It neither recompiles nor adopts a new artifact identity.
Negative fixtures cover wrong volume, changed payload, wrong digest, extra files
and missing receipts. Real content revalidation precedes downstream continuation.

Actual revalidation passed for 14,182 host files, six VM inputs and the backend
archive; the repeated host check refreshed zero receipts and hashed zero files.
The new application manifest is
`d4c35a96b053ea021103a40269cebf119279f4d5236d887914964724302b840a`.
The source-Factory producer plan, committed at `01936d0`, binds preparation to
`b7e0643`, application/VM inputs to `f20489e` and signed media to `609fcae`;
unchanged native/component owners retain their prior commits.

After the recovery fix, the full offline regression ran 1,028 tests in
98.595 seconds: 1,027 passed and one skipped. This is source/tooling regression,
not live or fresh-machine qualification.
An independent root-only export of `01936d0`, without sibling repositories,
passed all 203 reproduction fixtures in 52.614 seconds. That 44-MiB temporary
export was removed after a zero-open-handle check; committed sources and its
compact test log remain available.

The complete ordered source-Factory chain finished all 17 steps in **1,021.92
seconds** (17 minutes 1.92 seconds), reusing earlier component builds and creating
the new application selection, signed Setup and compressed DMG. This is the
downstream packaging time, not a cold build or the Factory compilation time.

- Chain key: `bb2848aa17e0bd7b2863c9cf3856f39c5d1b48fa0bb735ea1a25d81b2207809d`.
- Application key: `9f65e4a7321b4cd21dfa5a7b0499e76c2cd980d5963ae7b729beb572036432a5`.
- Setup key: `5d0e8bfd5077c44e0819131d2b23ae8b777ba6091466968b2a954fdb03e32713`.
- DMG key: `c6a65fa4c7fa75f86cf4c042fc6aa2b8ee479b44ce997027792b92a67c2e7a42`.
- DMG: **14,162,601,112 bytes**, SHA-256
  `f2b3d68d9dd4bd084d9fa199cc8053190a0466fb10ee3c5ecf024f877d4de82d`.

The canonical media owner verified every copied payload hash and the disk-image
container. A separate read-only mount verified the inventory of 17,697 files,
the new Factory image hash, the embedded application pin and the deep/strict
Setup signature. It then detached the media. No Setup, demo, Cloud connection
or live installation was started. The
[independent delivery descriptor](../../workspace/releases/1.2.0-rc.1-source-factory-delivery.json)
records these exact bytes without replacing the earlier candidate or its private
Drive object. Signing remains Apple Development, with no notarization, profile
qualification, source push, tag or public release.

The unchanged whole-chain repeat completed in **69.22 seconds**. Its completed
record and all 17 build keys equal the preserved first-run record. Every step
reported reuse; the 19 reuse events include two backend-image dependencies
inside export and do not mean 19 chain steps. No compiler, signer or compressor
was invoked by the repeat. First-run logs remain separately preserved.

Final checks found no owned chain worker, media worker or QEMU process and no
open handle to the DMG. The temporary read-only mount and media staging were
released. Shared Docker remains running with unrelated Watt containers; it was
not stopped as test cleanup. Approximately **474 GB / 442 GiB** was free on the
SSD afterward. Historical images, media, Builder/caches, source, credentials and
video were preserved. All new build/test payloads used the external volume.

This closes the source-Factory-to-DMG integration segment, not all of R2.
The next R2 work is complete acquisition of the remaining declared build inputs
without requiring the maintainer's retained kit, followed by release-level
handoff/capacity evidence. Independent approved-reader access and full-source
closure remain explicit; R3 human guides and R4 installation/live qualification
are not replaced by these build results.

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

## Cache reuse and capacity proof on October 8

A disposable empty SSD workspace received all 41 declared wheel objects from
the existing workspace by direct APFS `clonefile`: **24,581,670 logical bytes**,
zero downloaded bytes. The repeat imported zero objects and reused all 41.
The frozen `ad6b338` owner consumed every resulting cache entry without changes
or network access. The historical DMG and Factory were absent from these caches
and correctly reported as two missing cache objects; their retained inputs
remain untouched. No new kit, image, compilation or signing was involved.

The read-only report for the established workspace completed in **3.53 seconds**.
It observed about 255 GiB free on the SSD and 41 local wheel entries. Its section
sizes are logical, not additional unique physical allocation:

| Section | Logical bytes |
| --- | ---: |
| Prepared sources and build owners | 494,804,839 |
| Digest and tool caches | 57,633,028 |
| Declared SDK and staged inputs | 247,906,004 |
| Builds and retained receipts | 78,578,063,629 |
| Temporary owner files | 2,429,848 |

The report does not traverse the 11 source-tree symlinks or inspect unrelated
directories. Existing outputs include APFS clones; their apparent totals are
not a disk-cleanup recommendation. The shared Docker disk is not attributed
to this one workspace. Available space satisfies the existing 166 GiB largest
step guard, but not the 285 GiB reservation sum. Neither comparison promises
that a cold build fits or invalidates the completed warm build.

Full regression after the cache/capacity changes ran 968 tests in 56.017
seconds: 967 passed, one skipped. The new fixtures cover corruption, forged
donor receipts, source changes, interruption/resume, links, wrong volumes,
missing objects, cloning failure, insufficient space and read-only reporting.
Guard-drift tests check the report against the existing recipes, and a different
unreviewed producer plan cannot inherit the capacity claim. Documentation,
release-definition and source-publication gates passed.

The committed source checkpoint `8e25dcd` also passed all 145 reproduction
fixtures in **7.832 seconds** from a new root-only Git export on the bound SSD,
without sibling repositories. That disposable export was removed after a
zero-open-handle check; the source remains reproducible from Git.

The disposable receiver workspace was removed after verifying no open handles
and no source, build or runtime dependencies. Its wheel contents remain in the
original cache and are recoverable through the same command. No Factory, DMG,
accepted output, shared Docker state or user file was removed. Byte-size sums
are not reported as recovered physical space for these APFS clones.

## Packaging recipe dependency checks on October 8

The shared whole-directory producer fingerprint had two defects: unrelated
distribution or contract-document edits could invalidate all packaging owners,
while `scripts/host/aosvm-dns-bridge`, `workspace/repositories.json` and the
application unit configuration were absent. New direct packaging builds use
target-specific file closures with Git blob and executable-mode identities.
Static import inspection executes no source code. Application/Setup exports,
native Setup source, data contracts, checkpoints and shared validators are
included explicitly; fixtures guard their correspondence with owner constants.

Eight focused tests passed, including a disposable real Git repository on the
SSD. Its committed changes confirmed this direct recipe effect:

| Source change | Direct recipe keys changed |
| --- | --- |
| README only | None |
| Native Setup source | Setup |
| VM DNS helper | VM inputs |
| Shared native validator | All seven packaging targets |

Existing upstream keys still propagate a changed output to consumers. This is
file/module-level selection, not function-level analysis: shared validation
code and checkpoint guards deliberately remain dependencies. No compiler,
signer, media assembly, installer or runtime was launched by these fixtures.

The accepted 17-step chain still selects its original frozen producers and
verified outputs. No receipt was relabelled, manifest pin adopted or new DMG
created. New producer adoption belongs to a source-reviewed candidate with
independent output checkpoints; fixture success is not a fresh native build.

Full regression after this change ran **976 tests in 64.704 seconds**: 975
passed and one skipped. Documentation and historical release-definition gates
also passed. All fixture scratch used the external SSD and was automatically
removed; accepted outputs and the shared Docker Engine were untouched.

Committed checkpoint `ed48b74` then passed all **153 reproduction fixtures in
26.530 seconds** in a separate root-only Git export on the SSD, without sibling
repositories. The public-source scan also passed. After test completion and
zero-open-handle verification, the temporary export was removed; no build
worker or owned test process remained.

## Private Drive delivery proof on October 8

The subsequent [reusable CARLA input route](reusable-simulation-inputs.md)
separates retained simulation dependencies from complete installer releases.
Its transfer and consumer checks are recorded independently below.

The existing `1.2.0-rc.1` engineering DMG was uploaded to a separate private
release folder, without rebuilding or changing any existing artifact. Its
14,162,125,968 bytes and SHA-256
`7bac892b2398e38fe511de738838c23dd02e5ec26d2578afd3f6f932868cc755`
matched the source-reviewed delivery descriptor and Drive metadata. The folder
and artifact remained unshared; authorized owner access and capacity passed.

The real reader started with an empty SSD cache. A controlled client-side
interruption after 33,554,432 bytes left only a partial object. The ordinary
download command resumed at that exact offset, retrieved the remaining bytes,
verified the complete SHA-256 and unchanged remote metadata, then promoted the
cache object. Repeating the download reused that verified cache. Repeating
upload reused the same Drive ID without another upload; a folder read showed
one DMG, not a duplicate. This is a controlled interruption proof, not a claim
that the actual network failed during transfer.

An immutable `release-index-v1.json` was uploaded beside the DMG and read back
with matching size and SHA-256. It binds definition/tooling revision `de109aa`,
the descriptor digest, original media producer `ad6b338`, build key, application
manifest, Drive object identity/version and the exercised checks. It explicitly
records local-only source publication, Apple Development signing, no notarization
and no release/profile qualification. Private account and object IDs stay in
the authenticated index and external receipts, not public Git documentation.

The disposable full download was removed after successful verification/reuse
and a zero-open-handle check. Small receipts and the index remain on the SSD;
the original compiled DMG and its Drive object are preserved. The removed
14.16 GB test copy can be reacquired through the same reader. No installer,
simulator, VM or demo container was started; the shared Docker Engine was not
changed. The temporary Google login listener exited normally.

The delivery tooling has 12 targeted offline tests. Full integration regression
ran 988 tests: 987 passed and one skipped; documentation, historical-definition
and public-source gates passed. This verifies private transport of one complete
installer, not delivery of every dependency needed for source rebuilding.
Build-input acquisition, another approved reader, distribution entitlements,
signing/notarization and native release acceptance keep their separate gates.
No source push, new tag, public sharing or cold build was performed.

## Reusable simulation dependencies on October 8

Following the owner's approval, the retained CARLA was extracted into three
independent private archives: simulator/Python, native host support and Gateway
SDK. The [input route and verification record](reusable-simulation-inputs.md)
and [Git lock](../../workspace/dependencies/carla-macos-arm64-r1.lock.json)
bind exact bytes and original manifest ancestry. `lab dependencies` prepares
these inputs without compiling, installing or launching the demo. Neither the
old release definition nor the frozen 17-step producer plan was changed.

All 13.36 GB of archive bytes passed private Drive upload and independent
empty-cache download verification. All 31,477 extracted files passed payload
and mode checks. A network-denied repeat needed neither an account nor a working
Google CLI. Repeated upload reused all three IDs and created no duplicates.
The original `ecb3894` build consumer accepted the restored host/Python/SDK
inputs. Native version/help probes, isolated Python/CARLA import with the
declared cache environment, and deep/strict simulator signature checks passed.

Two diagnostic events were classified rather than hidden. Initial upload
initiation returned HTTP 403; no remote object existed on read reconciliation,
and one exact-ID repeat succeeded without a permission change. Its initial API
reason was not retained, so the cause remains unproven; future diagnostics now
expose only bounded non-secret API reason codes. The first Python probe omitted
`CARLA_CACHE_DIR` from its sanitized environment and crashed; restoring the
existing native owner's SSD cache setting made the same bytes pass. No product
runtime, engine, authentication scope or sandbox policy was changed.

Tooling commit `8b7b245` passed 1,008 local fixtures, with one skip, and all 185
reproduction fixtures from a root-only source export on SSD. The source export
was removed after verifying zero open handles. Large inputs and outputs used
external storage; Factory, original Kit028, the accepted DMG, video and shared
Docker were not changed. This completes the retained simulation package route,
not the complete R2 input closure, a fresh developer build, full-source build
or native runtime qualification. Clean-build scope remains the next discussion.
