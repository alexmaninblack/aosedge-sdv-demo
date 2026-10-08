<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release Definition and Reproduction Contract

- Status: R1 complete; delivery and version policy accepted; acquisition and reproduction unqualified
- Version: 1.9
- Prepared: 2026-10-08
- Owner: Demo Solution Team
- Scope: [R1 work packet](../../docs/planning/active/work-packets/human-friendly-reproduction.md)

One release definition selects the source roles, portable input manifests,
artifact identities and profile boundaries. A consistent definition is not a
downloadable, reproducible or qualified release. The current definition resolves
Kit028 / Setup042 / Factory .41 without asking the reader to follow older kits.

## Authority and immutable inputs

The [resolved candidate](../../workspace/releases/kit028-setup042.json) follows
the [schema](../../workspace/releases/release.schema.json). It binds existing
authority files by SHA-256 and cross-checks their selected values. It does not
replace the component manifests or retroactively edit original build receipts.
The integration tag selects a commit; the definition never hashes its own
commit. A later signed external receipt must bind released outputs to that
commit and its complete input set.

Source roles are exact commits, not branch requirements. In this candidate the
application source publication and Factory build tools are two explicit roles
of the same repository. R2 must resolve them automatically as separate clean
checkouts. Consolidation, branch merging and worktree removal are not required.
Published source, original build revision and current documentation revision
are distinct. The original Kit028 build contained uncommitted inputs; source
hash correspondence is not a clean or byte-identical rebuild claim.

`workspace/repositories.json`, the Kit028 source lock, five portable locks,
Setup's application pin and CI checkout pins must agree. The old
`components/baseline.lock.json` and `components/r6-1-source.lock.json` describe
earlier work, not replacement inputs for this candidate. The Stage 0 inventory
supplies historical observations only, not current toolchain qualification.

## Profiles and dependency closure

Each component records its owner, source roles, input groups, dependencies,
recipe locations, output format, access/license constraints and action for
each profile. Dependencies form an acyclic graph. All transitive inputs remain
visible even when a profile consumes them inside a prebuilt package.

| Profile | Builds or assembles | Reuses or obtains externally |
| --- | --- | --- |
| Operator | Nothing | Complete matching DMG, host prerequisites and user Cloud access |
| Developer | Integration, Presenter, Gateway, VDP, services, backends and packaging | Standalone CARLA/Unreal/content, Factory, native host/VM support and private Python |
| Full source | Developer outputs plus heavy native, simulation and Factory builds | Explicit licensed assets, pinned wheels, OS SDKs and any declared binary-only input |

These are target build scopes, not working end-user build commands. R1 adds only
a read-only definition validator. R2 owns preparation, download/cache handling
and build adapters; R4 owns fresh-environment proof. Full source does not mean
every upstream binary, OS SDK or licensed asset is available as public source.
Unknown source inputs must remain an explicit gate.

## Validation and failure behavior

From the integration checkout:

```sh
python3 -B scripts/validate-release-definition
python3 -B scripts/validate-release-definition --profile developer
python3 -B scripts/validate-release-definition --kit-root /path/to/existing-kit
python3 -B scripts/validate-release-definition --source-workspace /path/to/existing-workspace
```

Exit `0` means `DEFINITION_VALID` and, if requested, six small matching kit
manifests. It does not verify the payload files or claim successful installation.
Exit `1` rejects malformed definitions, unknown fields/profiles, changed pins,
missing authorities, escaping paths, duplicate records, dependency cycles,
missing metadata or mismatched manifests. Exit `2` means the requested profile
is structurally valid but blocked; the output identifies the remaining gates.
Unsupported profiles are invalid, not an implicit default. Optional source
inspection checks ten local Git commit objects, the baseline tag's exact target
and the 28 unique recipe files at their declared revisions. It does not require
the current branch or HEAD to equal those revisions, change a checkout, fetch
missing objects or run a recipe. Lazy fetching and terminal credential prompts
are disabled. Missing objects fail explicitly; preparation remains R2 work.

The gate uses Python 3.10 or newer, the standard library and a deliberately
bounded JSON Schema subset; unsupported schema keywords fail closed. It works
without sibling checkouts, the SSD, network, Docker, credentials or a running
demo. Optional kit checking reads at most 8 MiB per metadata file and never
imports kit code. Full payload verification remains with the existing
[installation owner](../distribution-installation/README.md).

Schema version 1 intentionally represents engineering candidates only. It
cannot advertise an approved download or a qualified profile by deleting a
blocker or toggling a flag. A future release-state extension requires reviewed
acquisition and qualification evidence; R1 is not that promotion mechanism.

## Artifact delivery boundary

The release owner selected Google Drive in the existing Google Workspace
account, with public Git source/metadata and read/download access for approved
testers. Published artifacts are separate files, never overwritten; inputs of
supported releases are retained. The schema does not itself provision hosting
or grant access. Local SSD paths and Git source URLs are not binary download
routes. Until the actual delivery binding is verified, the candidate retains
a null locator and `unpublished` access.

For an eventual authorized delivery, bind each Drive file identifier, size and
digest to the root commit in an authenticated release index. Use HTTPS transport
and integrity verification at creation and transfer. File identity is not
content immutability; changed bytes must fail verification. Cache keys use the
content digest, not a transient download URL.
Restricted inputs remain behind their own entitlement boundary. Short-lived
authorization is supplied separately and never committed in URLs, cache keys,
logs or manifests. Retention must preserve all inputs of supported releases;
do not silently replace an object at the same identity.

R2 owns folder/account binding, capacity/sharing checks, authorized API access
and verified acquisition. It must reject a missing locator for acquisition.
Neither provider selection, a source push nor a successful local metadata
check closes the actual delivery gate.

## Version policy

The release owner accepted product numbering `MAJOR.MINOR.PATCH`, candidate
suffixes `-rc.N`, and tags `sdv-lab-v<version>`. The next new candidate is
`1.2.0-rc.1`; its completed release target is `1.2.0` after the required
qualification. The corresponding tags are `sdv-lab-v1.2.0-rc.1` and
`sdv-lab-v1.2.0`. Acceptance of these names does not create a tag or promote
an artifact. A candidate tag belongs to its frozen source and build record;
a stable tag requires the completed release evidence.

Kit, Setup, Factory and Cloud release numbers remain independent traceable
fields. Historical Kit028 retains `productVersion: null`; it is not renamed
to the future product version. `demo-v1.1` and `candidate/kit028-setup042`
remain unchanged.

Changing this definition creates a new Git revision. Changing any deployed
artifact requires a new candidate identity and corresponding qualification;
it must not relabel the retained bytes as rebuilt or fully tested.

See the [R1 inventory and remaining gates](../../docs/development/release-reproduction-r1.md).

## R2 build tooling boundary

The build-only [lab](../../lab) entry point implements `plan`, `prepare`, `status`,
`verify` and `build`. An explicit external storage root holds state, exact
detached source checkouts, a digest-keyed artifact cache, temporary files and
outputs. It binds the volume UUID, selected profile and complete definition
digest; changing any binding requires a different preparation directory, not
an implicit reset. Existing unrelated or dirty directories are rejected.

Source preparation is independently resumable. `prepare --sources-only` may
succeed while artifact/build gates remain open. Ordinary `prepare` must not
report complete without the profile's required verified inputs. `status` and
`plan` distinguish source readiness, artifact readiness, supported target builds
and full-profile qualification. They never start or install the demo.

Google Drive acquisition consumes a separate non-secret binding of release
digest, artifact name and file ID. Expected size/digest come from the release,
not the binding. A short-lived authorized OAuth token may be supplied through
an inherited file descriptor; it is not a command argument, logged value or
stored receipt. Downloads enforce byte ranges, metadata consistency and final
SHA-256 before atomic promotion. Partial files stay on the SSD for resume.
An absent binding or credentials is an explicit acquisition failure.

Build adapters use exact source roles and existing recipes, with explicit
toolchain identity, SSD caches/temp/output and recorded input fingerprints.
Verified unchanged outputs may be reused; changing an upstream input changes
its downstream build key. A supported target build is not a completed profile,
signed installer, publication or native acceptance. Unresolved Factory/native
source inputs remain gated rather than being taken from undeclared warm state.

The supported developer build targets are `presenter`, `cloud-sdk`,
`brake-backend`, `tire-backend`, `backend-export`, `brake-service`,
`tire-service`, `gateway`, `preparation`, `host-runtime`, `backend-inputs`,
`vm-runtime`, `application`, `setup` and `dmg`.
`presenter` uses the pinned owner's native
Presenter, Driving Control and web UI recipe. It performs local ad-hoc signing
required by that recipe, not Developer ID signing, notarization or publication.
`cloud-sdk` uses the pinned Cloud worker assembly recipe, hash-locked public
wheels and the isolated Python base selected from an explicit retained kit on
the bound SSD. The release-to-host-to-Python manifest chain and payload hashes
are checked; other kit files are not copied. Public wheel acquisition shares
the bounded digest cache and resume checks, without Drive credentials. The
worker is assembled offline and does not enroll identities or contact Cloud.
The backend adapters require an already-running local Docker Desktop with its
active disk on the bound SSD. They call the pinned component Dockerfiles and
existing OCI export verifier; they do not start/stop the Engine, run containers,
overwrite tags, publish images or reuse undeclared registry credentials.
Build layers and client caches stay on external storage. Image receipts bind
source/platform/runtime identity; export receipts bind the complete archive.
Status-only receipt checks and live Engine image checks are distinguished.
The service adapters require an explicit functional profile: Brake V1/V2/V3
or Tire V1. They export unsigned ARM64 products through the pinned Dockerfiles
and use the source owners' test, dependency and payload validators. They never
sign, publish, install or run these products. Each profile has a separate input
fingerprint and verified repeat receipt.

Gateway uses the pinned CMake recipe and an explicit external SDK bound by
[`gateway-build-sdk.lock.json`](../../workspace/gateway-build-sdk.lock.json).
This is a declared prebuilt LibCarla/OpenSSL input, not full-source closure or
redistribution approval. Compile steps deny network. The unchanged owner's
socket tests need a short temporary directory; `--test-tmp-parent` must select
an existing directory on the same verified SSD, with a path no longer than
29 UTF-8 bytes. Only the invocation's private child directory is removed after
testing. CARLA's test cache is explicitly inside the workspace. An inspected
incomplete Gateway build may resume only with `--resume` and matching inputs;
the first stage logs are retained. Raw outputs still require native packaging
and library relocation before they can be treated as portable runtime files.

The preparation adapter uses the clean, committed root checkout as its explicit
build-tool owner. Its receipt records that revision and hashes the relevant
source trees, checkpoints and toolchain. It selects the reviewed four-profile
service checkpoint and Factory .41; retained unsigned VDP bases and firmware
are selected through the historical manifest chain. The existing owner validates
the products, tests, VDP profiles and reviewed runtime, and hashes the Factory
at transfer. Same-volume APFS clones do not silently fall back to full copies.
Repeat verification checks the unchanged output identities without repeatedly
hashing the large Factory. A partial owner result without the verified outer
receipt is preserved and rejected, not silently promoted.

This produces new preparation inputs, not historical Kit028 bytes. Complete
packaging must explicitly select the new group manifests in a new candidate;
its input-lock and Setup pin checks cannot be bypassed. Neither historical
manifests nor pinned source checkouts may be edited to make a new package
appear to match the old kit. Full-profile and runtime qualification stay gated.

The host adapter combines verified compiled UI/Gateway outputs with explicitly
retained simulator, Python, QEMU and OpenSSL inputs. It copies only manifest
members, ignoring incidental source-folder metadata rather than importing it.
OpenSSL reuse requires the exact original SDK library hashes, not a version
string alone. The native closure owner preserves entitlements, relocates loads,
removes build rpaths and verifies local signatures. Separate version/help-only
probes deny network and Homebrew reads; they start no simulator, VM or listener.

A new source-reviewed
[packaging checkpoint](../../workspace/releases/1.2.0-rc.1-packaging.json)
selects successor group manifests. It preserves the historical definition and
five source locks. Build-time `--input-checkpoint` selects this file explicitly;
there is no runtime pin adoption. Export retains every contract/protocol field
and substitutes only those independently reviewed manifest pins. VM assembly
requires both host/preparation pins; application assembly requires all five,
including the VM-to-host binding. An incomplete checkpoint cannot produce a
complete application. Adapter evidence stays outside installed payloads.
Backend assembly reuses the verified untagged OCI export without an Engine call.
Setup must subsequently bind the new application digest independently; none of
these commands creates a release tag, installs, provisions or publishes.
For successor Setup builds, both the reviewed group checkpoint and a separate
source-reviewed application release pin are required. Embedded contract pins
must equal those in the selected verified kit. Only the embedded build copy of
`setup_release.json` changes; the historical source pin stays intact. Complete
media assembly checks that same independent source pin against the signed Setup.
Omitting the explicit successor parameters retains the historical build behavior.
`setup` requires an explicitly selected authorized signing identity; it has no
automatic ad-hoc fallback. `dmg` reuses the verified Setup built for that same
application and independent source pin. Neither target launches Setup or the
demo. Compiler scratch, assembly and media staging remain on the selected
external volume. A signed engineering candidate is not notarized distribution
or installation qualification.
See [R2 commands and evidence](../../docs/development/release-reproduction-r2.md)
for the exercised scope, exit codes and remaining gates.
