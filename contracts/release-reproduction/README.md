<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release Definition and Reproduction Contract

- Status: R1 complete; delivery and version policy accepted; acquisition and reproduction unqualified
- Version: 1.23
- Prepared: 2026-10-09
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

The private publication/receipt contract below remains valid for historical
artifacts and explicit maintainer operations. The October 10 owner-authorized
[anonymous reader extension](#anonymous-developer-input-delivery) is a separate
transport for reviewed public inputs; it does not automatically publish any
existing file or change its permissions.

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

The explicit maintainer command `python3 -B scripts/drive-delivery` transfers
the separately reviewed [successor DMG descriptor](../../workspace/releases/1.2.0-rc.1-delivery.json).
It is not called by `lab`, Setup or any build. The historical release definition
and its `unpublished` locator remain unchanged. A private transfer of this new
engineering candidate does not qualify its installation or any build profile.

The command takes an explicit Google CLI account, private release folder and
explicit workspace. Existing authorized CLI credentials remain in Google's
credential store; access tokens and resumable session URLs stay in memory, not
arguments, receipts or logs. It never initiates login, changes sharing, replaces
a remote file or deletes an artifact. Source size and SHA-256 must match the
reviewed descriptor before upload. A pre-generated file ID and non-secret intent
prevent duplicate creation on repeat. Lost chunk responses are reconciled using
the server's acknowledged range before retransmission. A process restart keeps
the ID but not the session capability; absent completed metadata may require
restarting the upload, never creating a second file ID.

Readback checks the exact parent, private state, download permission, size,
provider-reported digest and version. For routine delivery, this readback after
the verified upload is sufficient; do not perform a separate maintainer
empty-cache download for every candidate. The actual installation/build
consumer verifies all downloaded bytes and unchanged remote metadata before
atomic promotion. A repeat may reuse the digest cache; it is not another
network-transfer proof. A dedicated complete round trip is reserved for changes
to transfer/recovery code or the provider integration, or a concrete integrity
incident, preferably using the actual consumer download. Missing or conflicting
metadata still fails verification. See the accepted
[transfer economy rule](../../docs/governance/rapid-development-and-debugging.md#artifact-transfer-economy).
The authenticated
release index records the definition revision and file identity separately
from build provenance. Source publication and access by another approved user
remain distinct gates; this command grants no new readers automatically.

## Reusable simulation inputs

On 8 October the owner approved extracting the retained, already built macOS
ARM64 CARLA into independently versioned private Drive dependencies. Normal
developer assembly reuses these bytes; it does not rebuild Unreal or CARLA.
Three archives separate the simulator and compatible Python API, small native
host support, and the existing Gateway SDK. The retained host and SDK manifests
remain authoritative. Original binaries, signatures and historical release
definitions are not rewritten. No Editor, engine source, build cache, Factory,
credentials or installed demo state is added to these archives.

A separately reviewed dependency lock binds package bytes, SHA-256, selected
manifest ancestry and compatibility. A separate Drive binding supplies file
identifiers only. Export validates every selected source member. Acquisition
uses the existing bounded, resumable digest cache, rejects unsafe/extra archive
members, verifies payload hashes and modes, and publishes extracted inputs only
after the entire set passes. Repeats validate recorded file identities; changed
files fail rather than being silently overwritten. Everything large stays on
the explicitly bound workspace volume, with a 90 GiB reserve for extraction/export.

The restored layout feeds existing `--kit-inputs` for host/Cloud assembly and
`--gateway-sdk` for Gateway, without adopting new producer revisions or creating
a second build implementation. It is a sparse build-input directory, not a
complete kit: Factory and preparation inputs remain separately required. A
verified transfer and consumer-input check do not claim a fresh build, runtime
qualification, public redistribution approval or complete R2 acceptance.

## Declared developer inputs with source Factory

The source-Factory campaign acquires the remaining binary inputs through
`lab inputs`, without requiring an installed kit or the maintainer's retained
directory. A separate reviewed `developer-factory41-r1` lock binds the release
definition, existing simulation lock, source-Factory checkpoint and original
vehicle/VM manifests. It adds only two archives: unsigned VDP bases with firmware
and the retained VM support files; and the independently built Factory .41 image
with its manifest. The original Factory image, services, operator state and
credentials are excluded. Existing CARLA, host-support and SDK packages do not
change. Export snapshots mutable, small Factory metadata into an immutable
checked copy without modifying its producer.

The five archives restore a sparse `kit-inputs` directory, `gateway-sdk` and
`factory-inputs`. They feed the existing frozen build owners through their
explicit paths. Preparation must select the source-Factory checkpoint, rather
than interpreting the sparse directory as a complete historical kit. Exact
member sets, modes, digest checks, selected-volume binding, 90 GiB reserve and
fail-closed partial-output handling follow the simulation acquisition contract.
Private Drive bindings contain transport identifiers, not artifact authority.
An unchanged prepared result works without Google access. Changed prepared
files are not adopted or automatically repaired.

This closes a build-input delivery boundary only after its real transfer and
consumer checks pass. It does not supply undeclared host toolchains, qualify a
cold build, change installer/runtime trust, or imply public distribution rights.

## Version policy

The October 8 clean-build campaign additionally selects a source rebuild of
Factory .41 while reusing `carla-macos-arm64-r1`. This explicit combination does
not change the default developer profile or enable the still-gated full-source
profile. The old Factory checkpoint and recipe remain historical authorities.
`lab factory plan` renders the successor Moulin input by binding that template
to the checkpoint's exact .41 platform revision/version. `factory prepare`
creates independent pinned source checkouts and a fresh configuration inside
the explicitly selected SSD-backed Builder. It reuses declared downloads and
sstate, not old `tmp`, `auto.conf` or image outputs. The original guest driver
remains the historical .11 route; the new adapter uses the pinned Moulin
configuration generator instead of changing that old driver in place.

`factory build` uses the existing Factory owner and native/package/image gates,
with new source/project/output paths. Its tools must be committed. Effective
image version, architecture and KUKSA source identity are checked before
compilation and retained with manager pins in the output manifest. The campaign
requires 40 GiB additional host headroom plus a 90 GiB reserve before compilation,
checks that reserve between stages, and retains the guest 60 GiB guard. These
are guards, not measured cold peak requirements. The adapter stops its Builder
after completion/failure and never starts a live demo or changes Cloud state.
The clean-build route restores the owner's temporary Platform-layer binding
before shutdown so preparation hashes remain valid on repeat. Restoration
compares the exact expected content and refuses unrelated changes. Source
archives omit macOS extended attributes and AppleDouble sidecars; unexpected
input members or digest changes remain errors, not ignored exceptions.
Fresh Factory outputs require new evidence and independently reviewed downstream
packaging identities. Preparation alone does not prove a completed image build.

`build --target preparation --factory-inputs <result-root>` explicitly selects
the [October 8 source image checkpoint](../../workspace/checkpoints/factory-41-source-20261008.json).
The result directory must be on the bound volume. Its independently pinned
manifest, exact source/tool revisions, native/package/image results and immutable
image size are verified; the canonical assembler hashes the image at transfer.
Retained firmware and unsigned VDP bases keep their historical manifest checks.
Without this option the historical Factory selection is unchanged. Source-built
Factory selection changes the preparation key and requires independent downstream
group and Setup pins. It does not qualify a live guest or replace historical media.

Downstream `vm-runtime` and `application` accept an explicit `--input-checkpoint`
relative to their committed producer. Setup and DMG additionally require the
independent `--release-checkpoint`; selecting only one is rejected. Both files
enter the recipe fingerprint. Matching upstream manifests are selected by their
reviewed hashes, not by latest timestamp, while older results stay intact.
The ordered chain forwards these explicit selections only to the affected
owners and keeps a separate invocation identity. A frozen old owner is not
implicitly upgraded; a new chain must pin owners supporting these options.

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

## One-run macOS developer workflow

The October 10 owner-approved amendment makes the downloaded wizard the single
entry for preparation, root checkout, source/input acquisition and the existing
developer DMG chain. One displayed plan and confirmation covers this build-only
route, including signing with the selected identity. `--prepare-only` retains
the old preparation boundary; `--check` remains non-mutating local diagnosis.
System permissions remain explicit. No installation, runtime launch, Cloud
mutation, Docker restart/storage migration or public publication is implied.

The bootstrap records the selected root `main` commit before acquisition and
never pulls or changes it on resume. Owned incomplete clones may resume at that
same commit. Existing clean canonical checkouts may be adopted explicitly by
location; dirty, foreign, linked or changed checkouts are preserved and rejected.
The prepared release requirements must match before repository code is used.
The preparation lock covers the whole workflow; existing build/input owners
retain their own locks and receipts. Workflow progress is diagnostic, not an
alternative readiness authority. Repeats call the canonical idempotent owners,
not a skip list based on previous green progress flags.

The repository continuation checks plans, source preparation, exact producer
storage compatibility and capacity before large input downloads. It forwards
explicit paths/tool/signing selections to the existing `lab` commands. The
single-script public route remains gated on actual public input publication;
the historical producer/storage boundary is unchanged. No pin adoption or
automatic native-partial recovery is added. Success is only
`CHAIN_BUILT_NOT_QUALIFIED` with the DMG selected from the exact chain receipt,
never the newest file. Offline fixtures are not a completed real walkthrough.

## Standalone macOS developer preparation

The October 9 owner-approved wizard replaces the six manual prerequisite
blocks. [prepare-macos.sh](../../scripts/prepare-macos.sh) is a single downloadable
Bash 3.2 file, runnable before a source checkout, Python or Homebrew exists.
Its preparation phase is a host-preparation owner, not a new builder or runtime
controller; the default continuation calls the existing repository builder.

It inspects first, shows one plan and requests one preparation confirmation.
Compatible installed tools are reused; mismatched project Node/npm are isolated
inside the selected workspace. Missing Homebrew tools use binary bottles/casks;
an incompatible already-installed formula is reported without a global upgrade.
Xcode installation/license and Docker first-run/start remain explicit
user/system boundaries. Google consent exists only in the explicit private
maintainer mode. Global Xcode selection, shell profiles,
shared Docker storage and Engine lifecycle are not changed. No source clone,
heavy input transfer, compile, signing operation, Cloud enrollment or demo launch
is part of preparation.

The six checks cover host/storage, Xcode/SDK/Swift/Git, CMake/Python, exact
Node/npm, local Docker/public input availability, and existing signing/input selections.
Bootstrap version values are exposed by `--requirements` and tested against
the source-owned UI engines and simulation Python compatibility. Existing
build owners retain their own authoritative version/input checks; frozen
release pins and historical evidence are not edited by preparation.

Saved selections are private data, never evaluated shell code. A private,
atomic shell environment handoff is generated only after all six checks pass;
a failed new preparation invalidates the previous handoff before mutation.
The handoff rejects a missing/replaced selected volume. Repeats re-probe tools,
reconcile owned partial Python/Node work and reuse verified downloads. They
preserve unexpected files and incompatible/unowned destinations. A lock
prevents overlapping preparations; confirmed dead owners may be recovered.

Default public mode does not discover/install Google CLI, ask for a Google
account, or access credentials. It fetches one bounded catalog and checks one
byte per declared archive. Only the later build consumer acquires full archives.
In the explicit private maintainer mode, Google credentials stay in their existing store. Access tokens are obtained
only inside a bounded helper and never printed, placed in shell variables,
logs or state. This private route downloads only the bounded catalog and checks
input metadata, never archives. Local bindings are produced automatically from
the trusted release record; archive verification remains with `lab inputs prepare`.
Missing/expired authorization or missing Drive scope
may request one login; ordinary permission denial must not create a login loop.

`--check` is local diagnosis without installation, persisted state, login or
Drive requests. Exit 0 means local checks passed, not complete access readiness;
exit 2 means an incomplete preparation/user action, and exit 1 rejects fatal
host/storage, ownership, integrity or installer errors. Full preparation alone
can publish `READY FOR SOURCE PREPARATION`. This is neither a build-capacity
guarantee nor fresh-machine/build/runtime qualification. The 90 GiB preparation
reserve does not replace per-stage capacity checks or exact-producer storage
compatibility. UI/output and recovery are described in the
[preparation reference](../../docs/getting-started/macos-developer-tools.md).

### Pre-clone release catalog

This subsection records the October 9 private catalog compatibility contract.
It now requires `--private-inputs` (or `--advanced-inputs`); the ordinary route
uses the October 10 anonymous extension below. Old records and source pins are
preserved, not reinterpreted as public permissions.

The October 9 owner-approved amendment replaces ordinary manual binding-path
questions. The stable filename is `release-index.json` in the authorized
`AosEdge SDV Lab Artifacts` folder. Versioning is internal: integer
`schemaVersion` for format, positive `catalogRevision` for catalog updates,
and immutable release records with unique `id` and `productVersion`.
The product marker is `aosedge-sdv-lab`. Old version-suffixed historical receipts
remain unchanged; this new discovery catalog is not a rename or promotion.

Discovery is bounded to exact folder/file names through the authenticated API.
Names are locators, not authorities. Missing/duplicate matches, incomplete
searches, unsupported format and oversized content fail explicitly. Only a
1 MiB maximum JSON catalog may be transferred. Its remote size/checksum and
unchanged post-read identity/version are checked. Duplicate JSON keys and
duplicate release IDs are rejected.

The reviewed bootstrap pin contains the exact release record's canonical JSON
SHA-256, release ID, dependency lock digests and source-file hashes, but no
account or private Drive IDs. The canonical encoding is UTF-8 Python JSON with
sorted keys and compact separators (ASCII escaping). Catalog entries cannot
self-authorize by supplying their own checksum. The reader selects exactly its
pinned compatible record; it never falls forward to a newer release or decides
compatibility from current timestamps. Other new entries do not invalidate an
older compatible pinned record. An altered selected record is rejected.

Each record binds source definition, build plan, delivery descriptor and both
dependency locks to the private bindings and all five objects' names, sizes
and hashes. Read-only object checks verify identity, parent, download access,
size and hash before saving anything. Authentication failure/scope renewal
remain distinct from ordinary 403/404 access denial; no login loop is added.
No sharing change, public artifact ID, new server or archive transfer is needed.

The reader generates both existing binding formats and a source selection in
a private, generation-specific directory under the existing preparation state.
Promotion is atomic; repeat compares rather than overwrites. The shell handoff
exports `SDV_BUILD_BINDING`, `SDV_SIM_BINDING` and `SDV_PREPARED_SOURCE`.
The explicit post-clone `developer_catalog.py --check-source` guard compares the
selection and local source authorities before acquisition/build. A moving main
with different input requirements fails rather than mixing versions. Existing
`lab inputs prepare` remains authoritative for archive bytes and consumers.

`--advanced-inputs` is the only manual binding-path route and checks the same
lock digests. It is never an automatic fallback after discovery fails. `--check`
only validates existing local selection data and contacts no Drive endpoint.
Source helper `scripts/developer_catalog.py` is embedded verbatim into the one
downloadable shell script by `scripts/sync-preparation-catalog`; parity is an
offline test, not a runtime network dependency.

Maintainers create the initial catalog or append a reviewed record with
`scripts/preparation-catalog`, supplying the existing private historical index
and optional previous catalog. It checks source/receipt correspondence and
refuses to alter an existing record ID. The private result is published to the
existing authorized folder; only the public trust pin enters Git. Future
producer/input adoption still requires its normal review and a new record;
catalog discovery does not move any historical pin or qualify a release.

### Anonymous developer input delivery

On October 10 the owner approved implementing the tested public-reader route
before a joint walkthrough. Default preparation is anonymous; explicit private
mode remains available for maintainers. Public-read failure must never trigger
OAuth, Google CLI installation, account questions or a private transport fallback.

The public distribution folder is separate from historical/private artifacts.
Publication requires explicit owner authorization, read-only link sharing and
a reviewed persistent `release-index.json` locator. On October 10 the owner
explicitly authorized public reading of the prepared eight-file folder for the
launcher walkthrough, after disclosure that the Unreal/Apple/SDK redistribution
review remains unresolved. This bounded test-publication amendment activates
`PUBLIC_PIN`; it does not declare license clearance, adopt draft terms or qualify
a release. The original private folder and immutable source/byte pins remain
unchanged. The [preparation record](../../docs/development/public-artifact-preparation.md)
retains the review gaps and the omitted Factory audit separately.

An absent public URL or record pin still makes the ordinary wizard exit 2 before
prompts, state changes or tool installation; it is not an invitation for the
reader to supply credentials. Implementation alone does not authorize or
complete a new publication.

The existing catalog envelope/versioning is retained. Public records have
distinct immutable IDs and canonical record SHA-256 pins. A selected record
must match `PUBLIC_PIN`, the same dependency-lock digests and source-file pins.
Its schema-2 bindings contain exactly `schemaVersion`, `transport` equal to
`google-drive-public`, `lockDigest` and a role-to-public-download-URL `files`
mapping. No private folder IDs, OAuth fields, API keys or expected-byte overrides
are accepted. Source locks, not URLs or response headers, authenticate archives.

The standard-library transport is `scripts/public_drive.py`, embedded with the
catalog helper by `scripts/sync-preparation-catalog`. It uses HTTPS only, bounded
same-file redirects between the two observed Google download endpoints, and no
ambient proxy authentication, cookies, OAuth or API key. Resource keys remain
part of the approved public locator. The reader does not search Drive.
Only Google's expected bounded same-file "cannot scan for viruses" confirmation
form is followed, once. Unexpected forms, login redirects, malware/abuse
warnings, foreign hosts and quota errors fail closed with sanitized messages.
There is no alternate-copy or quota-bypass operation.

Preparation limits the JSON catalog to 1 MiB, rejects duplicate keys/IDs and
selects only the pinned record. Each dependency probe requires HTTP 206 with
the exact `bytes 0-0/<pinned-size>` range and reads at most two bytes to check
that the response contains exactly one. This is an availability/length check,
not full integrity or a claim of remotely verified parent/version metadata.
Public state uses its own digest-keyed `public` generation, atomic promotion
and private modes; existing private/manual generations remain intact.

After cloning, source compatibility is checked before `lab inputs prepare` or
`lab dependencies prepare`. Both consumers accept explicitly supplied schema-2
bindings, preserve the existing verified SHA-256 cache/resume mechanism, and
check complete size and source-pinned hash before promotion/extraction. Wrong
ranges, ignored resume, changed bytes, unsafe archives and altered receipts
remain failures. Public acquisition does not fake private API metadata checks;
the authenticated schema-1 route retains those checks unchanged. A verified
cache repeat requires no network client or credentials.

The offline maintainer generator accepts `--public-links` with reviewed URLs,
preserves byte/source identities and creates a distinct `-public` record. It
does not upload, change sharing, approve redistribution or edit old records.
After public publication the owner must review the stable URL and record pin
into source and regenerate the standalone script. Real archive delivery and
the user's first-use walkthrough remain separate qualification evidence.

## Explicit build storage

The October 9 owner amendment permits an explicitly selected writable local
APFS workspace on an internal or external disk. This is a build-tool policy
change, not a release promotion. Earlier external-only campaign evidence and
frozen producer commits retain their original meaning. The new implementation
and regression fixtures await execution; no internal-disk build is qualified.

Resolve the actual filesystem device before probing volume metadata: macOS
`/Users` firmlinks do not identify the writable Data mount through lexical
parent traversal. Bind workspace state to the volume UUID, profile and release
as before; recheck mount/device/path ownership during operations. Reject read-
only/non-APFS/network storage, linked paths, volume roots and stale `/Volumes`
paths. A missing or replaced volume never selects another disk automatically.

Source preparation, downloads, extraction, caches, temporary files and outputs
use the explicit workspace. Retained inputs, clone donors, Gateway scratch and
the selected Factory Builder stay on its bound volume; same-volume clone
restrictions are not relaxed. Factory keeps its independent guest-space guard.

Docker is the declared exception: its already-running local Desktop Engine may
use another internal or external APFS volume. Verify the configured disk, actual
open backing file and local socket without creating containers or moving data.
Before Docker operations, reject a changed backing-file identity/configuration
and check both workspace and Docker capacity. No Engine start/stop, shared
storage migration, remote daemon or Docker credential inheritance is introduced.

Report free and required bytes per actual APFS capacity pool. Sum additional
workspace/Docker allowances that share a pool, retain its largest reserve and
never sum the same pool's free space across volumes. Use the most restrictive
reported available capacity for volumes sharing a pool, retaining volume-quota
limits. Separate pools have separate guards. Existing owner reserves remain;
the Docker layer allowance is not a measured upper bound or guest-disk guarantee.
Failure identifies the affected paths and available/required GiB before work.

`space` is read-only even for an unprepared workspace. Missing prepared source
marks the wheel-cache scope incomplete, not zero required dependencies. It
reports `capacityPools`, `dockerStorage`, `storagePreflightComplete` and
`producerStorageCompatibility`; insufficient checked capacity or an incomplete
storage preflight returns exit 2. Non-Docker direct targets do not require an
Engine. A capacity report remains neither a cold-peak measurement nor readiness.

For an ordered chain, read storage capabilities from the exact producer's Git
blob without importing code or editing its checkout. Producers without a
capability declaration retain external-only/same-Docker-volume semantics.
Unavailable policy fails closed. The chain rejects an incompatible layout
before preparing producer checkouts or starting any build step. A successor
source-reviewed plan must adopt new committed owners; historical plans and
checksums are never resealed to bypass the boundary.

## R2 build tooling boundary

The build-only [lab](../../lab) entry point implements `plan`, `prepare`, `status`,
`verify`, `build`, `cache` and `space`. An explicit selected storage root holds state, exact
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
SHA-256 before atomic promotion. Partial files stay on the selected volume for resume.
An absent binding or credentials is an explicit acquisition failure.

Build adapters use exact source roles and existing recipes, with explicit
toolchain identity, workspace caches/temp/output and recorded input fingerprints.
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
the bound volume. The release-to-host-to-Python manifest chain and payload hashes
are checked; other kit files are not copied. Public wheel acquisition shares
the bounded digest cache and resume checks, without Drive credentials. The
worker is assembled offline and does not enroll identities or contact Cloud.
The current backend adapters require an already-running local Docker Desktop
with its active disk checked under the explicit build-storage policy above.
Frozen older adapters retain their original same-external-volume requirement.
They call the pinned component Dockerfiles and
existing OCI export verifier; they do not start/stop the Engine, run containers,
overwrite tags, publish images or reuse undeclared registry credentials.
Build layers stay on Docker's selected disk; client caches stay in the workspace. Image receipts bind
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
an existing directory on the same verified volume, with a path no longer than
29 UTF-8 bytes. Only the invocation's private child directory is removed after
testing. CARLA's test cache is explicitly inside the workspace. An inspected
incomplete Gateway build may resume only with `--resume` and matching inputs;
the first stage logs are retained. Raw outputs still require native packaging
and library relocation before they can be treated as portable runtime files.

The preparation adapter uses the clean, committed root checkout as its explicit
build-tool owner. Its receipt records that revision and hashes the relevant
source files, checkpoints and toolchain. It selects the reviewed four-profile
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
volume. A signed engineering candidate is not notarized distribution
or installation qualification.
See [R2 commands and evidence](../../docs/development/release-reproduction-r2.md)
for the exercised scope, exit codes and remaining gates.

### Ordered developer chain

`build --target all` invokes the 17 developer steps from the source-reviewed
[ordered producer plan](../../workspace/releases/1.2.0-rc.1-build-chain.json).
This plan extends the accepted separate build-tools roles: it binds the base
definition, exact integration-repository commits and dependency order. It does
not modify component pins, input manifests, the independent Setup pin or trust
policy. `plan` exposes these selections before execution.

Each producer is an independent clean detached checkout on the bound volume.
An exact object already in the explicitly selected root repository can be
prepared without network; fetching a missing object requires
`--prepare-dependencies`. Wrong remotes, revisions, dirty checkouts and unowned
paths fail without reset. Each worker imports only its selected frozen adapter.
This separates application generation from the later source-reviewed Setup pin
without a circular source-to-manifest hash or implicit current-HEAD selection.

The parent holds the existing workspace lock. Workers receive only the exact
selected dependency results and their own target cache. Saved state retains
all older valid results; workers cannot replace an existing build receipt or
change source, artifact or storage bindings. Repeats run owner verification and
reuse unchanged results. A failure preserves completed work and compact logs;
an unverified partial native output still requires the owner's inspection and
resume procedure. No automatic retry or pin adoption is introduced.

The complete chain requires explicit retained kit/SDK inputs on the bound volume,
declared build tools, a short same-volume test directory and an authorized signing
fingerprint. It retains the per-owner guards and preflights 76 GiB additional
space plus a 90 GiB reserve. This is a conservative guard, not a measured cold
peak. UI and build Python entry points are selected separately; virtual
environment paths are not resolved to a different interpreter.

Success reports `CHAIN_BUILT_NOT_QUALIFIED`, never profile readiness,
installation or publication. Frozen owner selection avoids invalidation from
unrelated current-root changes. Historical producers retain their original
fingerprints; they are not silently replaced by newer adapter code. Cold
reproduction, artifact delivery and full-source closure retain separate gates.

### Packaging recipe invalidation

New direct packaging builds select file-level recipe inputs for preparation,
host assembly, backend inputs, VM inputs, application, Setup and DMG. Static
Python imports, including deferred imports and package initializers, select
the conservative local module closure without executing it. Explicit data,
exported Python modules, native Setup source, source-reviewed checkpoints and
shared verification helpers complete the selection. Each input records its Git
blob and executable mode; the actual producer revision remains in the receipt.
Dirty roots, missing/untracked inputs and linked recipe files fail closed.

Setup native-source edits no longer invalidate preparation or host recipes.
The VM DNS helper and application configuration are explicit dependencies;
they cannot change without changing the relevant key. Documentation and
unrelated diagnostic tools are excluded. Shared validators and the full
checkpoint validations remain conservative dependencies, not function-level
reachability claims. Existing upstream result keys carry changes downstream.
Tests compare copied-data lists with canonical owner constants to detect drift.

This new fingerprint format does not adopt old receipts or rewrite a frozen
producer plan. Selecting a new producer for an actual candidate remains an
explicit source-reviewed change, with independently pinned output manifests
and Setup identity. The existing warm candidate stays on its original owners.

### Cross workspace cache reuse and capacity

`revalidate --storage <workspace> --target <input-target>` explicitly recovers
completed host, preparation, VM or backend-input receipts after macOS renumbers
the same mounted volume. The existing workspace UUID binding is mandatory.
Only the device-number field may differ; inode, size, times, mode and inventory
must remain unchanged. Every affected payload is hashed against its existing
manifest before the original owner validates the proposed receipt. Original
receipts and verification evidence are preserved before atomic stamp refresh.
No payload, build key or source/manifest pin changes. Wrong volume, any other
metadata change, missing receipt or content mismatch fails without resealing.
This is explicit recovery, not an implicit status repair or a new build.

`cache --storage <destination> --cache-from <existing-workspace>` reuses only
declared complete digest-cache objects. Both workspaces must be separate,
ownership-marked and on the same bound volume. Expected sizes and
hashes come from the selected release; developer wheels additionally require
the clean exact integration source and its wheel lock in either the destination
or the explicitly selected source workspace. A donor cannot supply new pins.
Unlisted cache files, build results, credentials and runtime state are excluded.

The existing destination lock covers transfers. The source remains read-only.
The macOS `clonefile` call shares file data blocks while creating independent
file identities; it never overwrites an existing file or falls back to a full
copy. Each transferred object is SHA-256 verified before atomic promotion to
the existing cache layout. Links, corruption, changed source identity, foreign
volume binding and unowned partials fail without deletion. Owned complete
partial clones may resume verification. No shared mutable hardlinks or new
cache daemon are introduced; existing frozen consumers use the resulting
cache without changes. Normal disk reserves remain in force.

This is local cache reuse, not artifact acquisition or profile completion.
Missing objects remain explicit (`CACHE_REUSE_PARTIAL`); the command downloads
nothing and does not set artifact/source/build readiness receipts. Existing
verified objects are reused on repeat. Full-source cache closure remains gated.

`space` is read-only and does not initialize a workspace. It reports declared
cache objects present locally, available from the optional explicit donor, or
absent from both. Absence from a cache does not mean an explicitly retained kit
or Factory input is missing. Workspace logical bytes and file-reported blocks
are separate; neither measures unique APFS clone extents. Symlinks are counted
but not followed, and hardlinked files are counted once within each section.

For the reviewed developer chains the report exposes the existing per-owner
workspace guards, the largest single-step requirement and the sum of additional
step reservations plus one largest reserve. These workspace-only summaries do
not include the separate Docker allowance in `capacityPools`; use the pool
verdict for admission. The sum is not a measured peak, an upper bound, or a new
build gate. Shared Docker growth, cold acquisition and unique physical extent
usage remain unmeasured. A recorded candidate is not verified reuse; `space`
does not substitute for owner validation. It refuses capacity claims for a
different unreviewed producer plan or full-source profile.
