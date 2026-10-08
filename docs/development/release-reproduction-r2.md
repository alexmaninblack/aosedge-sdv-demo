<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R2 Preparation and Build Tooling

- Status: In progress; five build targets and repeat proof complete
- Date: 2026-10-08
- Owner: Demo Solution Team
- Authority: [Work packet](../planning/active/work-packets/human-friendly-reproduction.md)
  and [reproduction contract](../../contracts/release-reproduction/README.md)

`lab` prepares pinned sources and builds the native/web UI, Cloud SDK, both
backend images and their OCI export on external storage. It does not yet
reproduce a complete installer. The selected
definition remains Kit028 / Setup042 / Factory .41; this tooling does not rename
that media to the future `1.2.0-rc.1` candidate.

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

| Operation | Exit | Meaning |
| --- | --- | --- |
| `plan` or `status` | 0 | Report produced; inspect gates and readiness |
| Successful source-only preparation/verification | 0 | Selected sources ready, not a complete profile |
| Successful explicit target build | 0 | Built/reused, not installed or runtime-qualified |
| Ordinary `prepare` or `verify` | 2 | Full profile remains blocked |
| Invalid input, collision, wrong pin, disk/access failure | 1 | No unsafe repair or fallback |
| Interrupted command | 130 | Owned command group stopped; partial work retained |

`--target all` and full-source preparation fail until their adapters/input
closure are implemented. Operator mode needs no source roles but is not yet
a complete acquisition route.

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
state save. An incomplete compile remains preserved for inspection; automatic
recovery of failed compilation is not yet supported.

## Google Drive binding

A separate private artifact root has been created and its unshared metadata
verified. It remains empty; no binary upload or sharing change was performed.
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

This adapter has offline fixture proof only. Actual CLI authorization, release
file binding, capacity, no-overwrite upload/retention enforcement and large-file
transfer remain unqualified. Folder creation does not approve redistribution.

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

## Remaining R2 work

1. Qualify authenticated Drive acquisition, release binding, capacity, approved
   access and retention. Keep old media unpublished until its gate closes.
2. Add remaining component adapters and pinned heavy input dependencies,
   cross-workspace cache reuse and full-profile capacity accounting.
3. Close effective Factory configuration, native/simulation prerequisites and
   entitlement gaps before enabling full-source preparation/builds.
4. Extend CI/build proof to those targets. R3 reader-facing routes and R4 fresh
   environment/native acceptance remain separate deliverables.
