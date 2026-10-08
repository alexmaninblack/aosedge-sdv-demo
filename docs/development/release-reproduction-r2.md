<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R2 Preparation and Build Tooling

- Status: In progress; source and UI target proof complete
- Date: 2026-10-08
- Owner: Demo Solution Team
- Authority: [Work packet](../planning/active/work-packets/human-friendly-reproduction.md)
  and [reproduction contract](../../contracts/release-reproduction/README.md)

`lab` prepares pinned sources and builds the existing native/web UI target on
external storage. It does not yet reproduce a complete installer. The selected
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
```

The first build requires pinned Node 26.0.0/npm 11.12.1, Xcode's macOS SDK and
Swift compiler, and explicit dependency acquisition. `--node` and `--npm` can
select installed tools. The adapter calls the exact integration owner's
`scripts/distribution/ui_build.py` with its locked integration/Gateway sources.
npm acquisition disables lifecycle scripts. The owner denies network to build
subprocesses and performs local ad-hoc signing, not Developer ID signing.
No application is launched. Observed compiler/SDK identities enter the build
fingerprint; that does not qualify them for every release target.

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

## Remaining R2 work

1. Qualify authenticated Drive acquisition, release binding, capacity, approved
   access and retention. Keep old media unpublished until its gate closes.
2. Add remaining component adapters and pinned heavy input dependencies,
   cross-workspace cache reuse and full-profile capacity accounting.
3. Close effective Factory configuration, native/simulation prerequisites and
   entitlement gaps before enabling full-source preparation/builds.
4. Extend CI/build proof to those targets. R3 reader-facing routes and R4 fresh
   environment/native acceptance remain separate deliverables.
