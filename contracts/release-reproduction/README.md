<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release Definition and Reproduction Contract

- Status: current definition v3; engineering build/delivery implemented; fresh reproduction remains unqualified
- Version: 1.36
- Prepared: 2026-10-09
- Owner: Demo Solution Team
- Scope: engineering build/delivery and [independent reproduction](../../docs/planning/roadmap.md#fresh-developer-reproduction)

The [current build definition](../../workspace/build-definition.json), schema 3,
is standalone. It binds source/input locks, the component policy, maintained
instructions and independent build/delivery selections. A consistent definition
is not a qualified release and does not advance any artifact pin.

## Reading this contract

Start with the [developer guide](../../docs/getting-started/reproduce-demo.md)
to build the demo and installer. This is the implementation reference, not a
second prerequisite checklist.

| Task | Relevant section |
| --- | --- |
| Understand selected sources, dependencies and reuse | [Authority and immutable inputs](#authority-and-immutable-inputs), [profiles](#profiles-and-dependency-closure) |
| Follow the downloaded developer launcher | [One-run workflow](#one-run-macos-developer-workflow), [host preparation](#standalone-macos-developer-preparation), [storage](#explicit-build-storage) |
| Understand public downloads and publication | [Artifact delivery](#artifact-delivery-boundary), [anonymous inputs](#anonymous-developer-input-delivery), [Dropbox publication](#dropbox-dependency-publication) |
| Rebuild the controller image instead of reusing it | [Source-built controller input](#source-built-controller-input) |
| Maintain compatibility with an explicitly selected private catalog | [Private catalog](#pre-clone-release-catalog); not required for public downloads |
| Inspect build recipes, result seals and cache keys | [Build tooling](#build-tooling-boundary) |

## Current selection and compatibility identity

Default validation needs no old release file, obsolete report, Git history or
network. Exact Git source/build revisions, access boundaries, runtime manifest
hashes, CI pins, toolchains and the complete acyclic component graph remain
checked. Unknown, missing, changed, linked and unsafe inputs fail closed.

The [cache compatibility record](../../workspace/inputs/cache-compatibility.json)
retains the original cache/prepared-storage namespace and controller export
provenance for unchanged material inputs. It is not product versioning, current
qualification or permission to alter an old receipt. Its complete input closure
must match; automatic semantic rebinding is forbidden. Frozen producer checkouts
keep their original source and receipts; current maintenance does not edit them.

Operator DMGs are delivery outputs, not entries in the runtime build-input
lock or its schema. The namespace remains bound to the unchanged material
inputs: source revisions, retained manifests, controller identity and the five
dependency archives. Removing the obsolete delivery-output entry explicitly
preserves that namespace after comparison of those inputs; the current file
closure is still checked in full. Projection tools do not infer compatibility,
ignore mismatches or rewrite existing prepared state and completed receipts.

## Authority and immutable inputs

The [source lock](../../workspace/inputs/sources.lock.json) binds exact component
source and build revisions. [Runtime inputs](../../workspace/inputs/runtime-inputs.lock.json)
bind retained dependency-group manifests, not a preceding complete application.
Archive identities and original receipts remain unchanged; current application
and Setup results have independent source and integrity evidence.
[Controller image identities](../../workspace/inputs/controller-images.lock.json)
separate prebuilt and independently rebuilt images. [Service inputs](../../workspace/inputs/service-inputs.lock.json)
retain all four exact binary profile identities.

The [workspace map](../../workspace/README.md) lists these roles and projections.
The public catalog now describes dependency packages independently from old DMG
and full-build receipts. Actual archive names, bytes, manifests and hashes stay
unchanged. Current filenames describe roles; revisions and versions live inside
records. Source-only validation is not new runtime or rebuild acceptance.

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

These are build scopes. The [developer guide](../../docs/getting-started/reproduce-demo.md)
owns the working entry; the tooling below implements preparation, acquisition
and build adapters. [Independent reproduction](../../docs/planning/roadmap.md#fresh-developer-reproduction)
still requires fresh-environment proof. Full source does not mean
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

Exit `0` means `DEFINITION_VALID` and, if requested, five small matching retained
dependency-group manifests, including their VM-to-host binding. No preceding
application manifest is required. This is not a current candidate/installer gate:
the existing package/installation owners still verify the complete current
application, group bindings, payload sizes and hashes before use.
Exit `1` rejects malformed definitions, unknown fields/profiles, changed pins,
missing authorities, escaping paths, duplicate records, dependency cycles,
missing metadata or mismatched manifests. Exit `2` means the requested profile
is structurally valid but blocked; the output identifies the remaining gates.
Unsupported profiles are invalid, not an implicit default. Optional source
inspection checks ten local Git commit objects, the baseline tag's exact target
and the 28 unique recipe files at their declared revisions. It does not require
the current branch or HEAD to equal those revisions, change a checkout, fetch
missing objects or run a recipe. Lazy fetching and terminal credential prompts
are disabled. Missing objects fail explicitly; source preparation is a separate explicit action.

The gate uses Python 3.10 or newer, the standard library and a deliberately
bounded JSON Schema subset; unsupported schema keywords fail closed. It works
without sibling checkouts, the SSD, network, Docker, credentials or a running
demo. Optional kit checking reads at most 8 MiB per metadata file and never
imports kit code. Full payload verification remains with the existing
[installation owner](../distribution-installation/README.md).

Definition validity does not advertise a qualified profile by deleting a blocker
or toggling a flag. [Release promotion](../../docs/development/release-campaign.md)
requires independently reviewed acquisition and candidate qualification evidence.
The current operator catalog is separate from this build definition.

## Artifact delivery boundary

The private publication/receipt contract below remains valid for historical
artifacts and explicit maintainer operations. The
[anonymous reader extension](#anonymous-developer-input-delivery) is a separate
transport for reviewed public inputs; it does not automatically publish any
existing file or change its permissions.

The current public DMG and all five developer dependency archives use Dropbox;
their source-owned catalogs and byte locks remain in GitHub. The following
authenticated Google Drive contract is retained for explicit private maintenance
and already-pinned consumers, not the current public route.
Published artifacts are separate files, never overwritten; inputs of
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
the separately reviewed DMG descriptor selected by the
[launcher catalog](../../workspace/launcher-catalog.json).
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

### Resumable operator DMG acquisition

Route A retains its automatic download selection separately from an explicitly
supplied local DMG. Private metadata binds the approved package size/SHA-256,
canonical destination and selected volume UUID. A missing finished file may
resume only this exact download; an unrecorded missing local file remains a
missing-input condition, never an automatic new download or disk fallback.
An explicit `--parent` selects a new cache and preserves previous payloads.

Owned `.part` receipts bind the private regular single-link payload's identity
to that selection. Unknown, replaced, linked, oversized or differently bound
partials fail without adoption. HTTP resume requires exact 206 start/end/total
and, when provided, remaining Content-Length; encoded or ambiguous responses
are rejected. An invalid response rolls back only the new suffix through the
same checked file descriptor. A valid interrupted transfer retains received
bytes, but no prefix is trusted as media until the full pinned SHA-256 passes.
Destination collisions do not overwrite a completed file.

Connection and stalled-transfer deadlines bound unavailable networking; there
is no short total deadline for an advancing multi-gigabyte transfer. No automatic
retry, account login, provider fallback, signature bypass, installation or Cloud
action is added. Existing checksum, signed Setup identity and matching kit gates
still precede handoff. Unmarked predecessor partials are preserved; a current
launcher can explicitly select a new cache or a complete matching local file.

## Reusable simulation inputs

The retained, already built macOS ARM64 CARLA is an independently versioned,
source-locked dependency, delivered through the current Dropbox catalog. Normal
developer assembly reuses these bytes; it does not rebuild Unreal or CARLA.
Three archives separate the simulator and compatible Python API, small native
host support, and the existing Gateway SDK. The retained host and SDK manifests
remain authoritative. Original binaries, signatures and historical release
definitions are not rewritten. No Editor, engine source, build cache, Factory,
credentials or installed demo state is added to these archives.

A separately reviewed dependency lock binds package bytes, SHA-256, selected
manifest ancestry and compatibility. A separate transport binding supplies locators only. Export validates every selected source member. Acquisition
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
Transport bindings contain locators, not artifact authority.
An unchanged verified prepared result needs no provider access. Changed prepared
files are not adopted or automatically repaired.

This closes a build-input delivery boundary only after its real transfer and
consumer checks pass. It does not supply undeclared host toolchains, qualify a
cold build, change installer/runtime trust, or imply public distribution rights.

## Source-built controller input

The declared source-build input selects a rebuild of the locked controller
image while reusing `carla-macos-arm64-r1`. This explicit combination does
not change the default developer profile or enable the still-gated full-source
profile. Original input records and recipes remain immutable provenance.
`lab factory plan` renders the successor Moulin input by binding that template
to the controller lock's exact platform revision/version. `factory prepare`
creates independent pinned source checkouts and a fresh configuration inside
the explicitly selected SSD-backed Builder. It reuses declared downloads and
sstate, not old `tmp`, `auto.conf` or image outputs. The original guest driver
remains a legacy compatibility route; the source-build adapter uses the pinned Moulin
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
the [source-built controller identity](../../workspace/inputs/controller-images.lock.json).
The result directory must be on the bound volume. Its independently pinned
manifest, exact source/tool revisions, native/package/image results and immutable
image size are verified; the canonical assembler hashes the image at transfer.
Retained firmware and unsigned VDP bases keep their historical manifest checks.
Without this option the default prebuilt controller selection is unchanged. Source-built
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

## Version policy

Product numbering is `MAJOR.MINOR.PATCH`, candidates use `-rc.N`, and tags use
`sdv-lab-v<version>`. The [operator catalog](../../workspace/launcher-catalog.json)
selects the current package; this contract does not predict the next number.
A candidate tag belongs to its frozen source/build record; a stable tag requires
completed release evidence. Naming alone neither creates a tag nor promotes media.

Installer, Factory and Cloud release numbers remain independent traceable fields.
Do not rename historical tags, null-version records or retained artifact identities.

Changing this definition creates a new Git revision. Changing any deployed
artifact requires a new candidate identity and corresponding qualification;
it must not relabel the retained bytes as rebuilt or fully tested.

See the [current build inputs and remaining gates](../../docs/development/release-reproduction-r2.md).

## One-run macOS developer workflow

The downloaded wizard is the single
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
public route checks input availability and exact source pins before acquisition;
the selected producer/storage boundary remains enforced. No pin adoption or
automatic native-partial recovery is added. Success is only
`CHAIN_BUILT_NOT_QUALIFIED` with the DMG selected from the exact chain receipt,
never the newest file. Offline fixtures are not a completed real walkthrough.

### Human progress and result presentation

The launcher provides in-place terminal progress
without changing acquisition, validation, build or release authority. Input
events carry only source-locked artifact role/name, byte totals and observed
byte counts. Transfer, digest verification and extraction are separate phases.
The transfer ETA uses bytes received in this invocation, excluding an existing
partial file; when data stops arriving it reports waiting rather than a stale
estimate. Completion still requires all existing integrity/receipt checks, not
a full bar. The ordered build bar counts verified steps, not weighted time.
Unknown-duration work uses an activity indicator. Non-terminal output stays
bounded and plain. Full diagnostics remain in the existing logs; paths appear
on error and in the final build-details reference, not in recurring heartbeats.

Only after exact-chain media verification may the launcher expose
`<workspace>/output` as a relative directory symlink to that immutable result
under `build/builds/dmg`. This presentation-only link is not consumed by build
owners, does not weaken their no-symlink rules and allocates no second DMG copy.
Private ownership/intent metadata allows atomic advance and interrupted-update
reconciliation. Foreign output files/directories/links or changed metadata fail
without overwrite. Earlier results and receipts remain intact. The workflow
record retains canonical and displayed paths; display state cannot skip any
owner verification on repeat. This presentation changes no frozen producer plan
or source/input pin and requires no product rebuild for its offline UX tests.

## Standalone macOS developer preparation

[prepare-macos.sh](../../scripts/prepare-macos.sh) is a single downloadable
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

This private catalog compatibility route requires `--private-inputs` (or
`--advanced-inputs`); the ordinary route uses anonymous delivery below.
Old records and source pins are
preserved, not reinterpreted as public permissions.

For optional private-input maintenance the stable filename is `release-index.json` in the authorized
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

Default preparation is anonymous; explicit private mode remains available for
maintainers. Public-read failure must never trigger OAuth, Google CLI
installation, account questions or a private transport fallback.

The source-owned `workspace/dependencies/catalog.json` selects reviewed public
file locators independently from private maintenance bindings. Publication
requires explicit authorization, read-only access and a reviewed `PUBLIC_PIN`;
reader discovery never searches an artifact folder. Existing engineering-preview
public access does not establish Unreal/Apple/SDK redistribution clearance,
accept draft terms or qualify a release. The [artifact preparation reference](../../docs/development/public-artifact-preparation.md)
retains the remaining redistribution/source-notice boundaries. Immutable source
and byte pins do not change when a transport locator changes.

An absent public URL or record pin still makes the ordinary wizard exit 2 before
prompts, state changes or tool installation; it is not an invitation for the
reader to supply credentials. Implementation alone does not authorize or
complete a new publication.

The existing catalog envelope/versioning is retained. Public records have
distinct immutable IDs and canonical record SHA-256 pins. A selected record
must match `PUBLIC_PIN`, the same dependency-lock digests and source-file pins.
Its schema-2 bindings contain exactly `schemaVersion`, `transport` equal to
`dropbox-public` for current inputs (`google-drive-public` for legacy pinned
inputs), `lockDigest` and a role-to-public-download-URL `files`
mapping. No private folder IDs, OAuth fields, API keys or expected-byte overrides
are accepted. Source locks, not URLs or response headers, authenticate archives.

The standard-library transport keeps its compatibility name
`scripts/public_drive.py`, embedded with the
catalog helper by `scripts/sync-preparation-catalog`. It uses HTTPS only, bounded
provider-specific redirects, and no
ambient proxy authentication, cookies, OAuth or API key. Resource keys remain
part of the approved public locator. The reader does not search Drive.
Dropbox bindings accept only reviewed archive file links and observed Dropbox
content endpoints. They preserve Range across redirects and reject HTML/login,
foreign hosts, provider switching, altered encodings and unsupported queries.
Only the legacy Google adapter's expected bounded same-file "cannot scan for viruses" confirmation
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
preserves byte/source identities and creates a distinct `-dropbox` record
(`-public` for explicit legacy Drive maintenance). It
does not upload, change sharing, approve redistribution or edit old records.
After public publication the owner must review the stable URL and record pin
into source and regenerate the standalone script. Real archive delivery and
the user's first-use walkthrough remain separate qualification evidence.

### Dropbox dependency publication

Dropbox delivery binds transport locators for the five source-locked archives;
changing transport never changes their accepted bytes. `scripts/publish-dependency-inputs`
uses the existing authorized app-folder publisher and explicit cache/records
paths. Its fixed `/dependencies` destination is separate from operator releases.
Archive upload is an explicit kind; the default DMG publisher/parser continues
to reject dependency archives. No new credential scope or arbitrary-file
publication is introduced.

Before publication, local size and SHA-256 must match the lock. Upload uses the
existing private cursor journal, strict no-overwrite commit, chunk content hashes
and interruption reconciliation. Readback verifies remote identity, revision,
size and Dropbox block-content hash, then a bounded anonymous one-byte range
probe checks access. Routine verification never downloads the entire archive
back. A completed no-upload repeat reuses the same immutable destination.
Only a complete five-package report can supply the successor source catalog;
partial publication does not change reader selection.

A changed catalog record needs a distinct immutable ID and canonical pin;
old launcher pins remain unchanged in their original sources. Obsolete Drive
indexes are not a supported current public fallback: use the current launcher.
Preserve source/notice companions, supported DMGs, input identities and verified
caches. Public readers never fall back to private Google credentials or another
provider. Delivery proof is not a fresh build, installation, license clearance
or product-version promotion.

## Explicit build storage

The launcher accepts an explicitly selected writable local
APFS workspace on an internal or external disk. This is a build-tool policy
change, not a release promotion. Earlier external-only campaign evidence and
frozen producer commits retain their original meaning. Storage-policy checks do not establish a completed internal-disk build;
independent fresh-host reproduction remains unqualified.

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

Disposable build/compiler,
packaging and media staging live under the selected workspace's `.tmp`. The launcher
binds `SDV_SCRATCH_ROOT` to that directory. Direct build commands without the
launcher use their explicit workspace/output parent's `.tmp` on the same volume.
Each operation owns a private marked child and a lease. Successful, failed and
normally cancelled operations remove their disposable child; reports, verified
caches, resumable downloads, source trees and partial/final build outputs remain
outside it. DMG failure retains a bounded failure record and any partial DMG,
not a second full-size staging copy. Partial outputs are not promoted or retried
automatically.

The next invocation checks crash leftovers. Only a valid private marked run
with a dead owner, obtainable lease and no open handles can be removed. Foreign
or busy data and changed/missing volumes are preserved, never silently adopted.
The pre-Python launcher uses a private bootstrap child with a PID and its existing
exclusive preparation lock. Node archives are reusable cache entries; Node
extraction is disposable bootstrap scratch. Atomic metadata writes and security-
sensitive runtime/guest temporary files retain their existing boundaries.

Docker is the declared exception: its already-running local Desktop Engine may
use another internal or external APFS volume. An explicit `DataFolder` selects
its exact `Docker.raw`; only an omitted key selects Docker's documented macOS
default under `~/Library/Containers/com.docker.docker/Data/vms/0/data`.
Invalid explicit settings or a missing/linked disk never select another path.
Verify the regular single-link file, actual open backing file and local socket
without creating containers or moving data. Cached `info` is not activity proof.
If no open handle is visible, a bounded read-only `system df` query to that
exact checked local endpoint may wake Docker's Resource Saver VM. Check Docker
headroom before that query, then require an open handle on the same configured
device/inode; a failed query, changed disk or still-inactive disk fails closed.
No Desktop settings or idle timer are changed, and no helper container is used.
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

The source-owned `workspace/current-developer-build.json` selects the reviewed
developer plan by path and independent SHA-256. Capacity checks verify that
selection before admitting its exact producer plan; an arbitrary structurally
valid plan cannot reuse the guards. The retained base and source-Factory input
definitions remain separate authorities. Superseded public build attempts are
retained through Git history, not a growing hard-coded runtime allowlist.
The seventeen-step dependency order, producer storage checks, owner reserves
and separately sealed developer output policy remain unchanged.

<a id="r2-build-tooling-boundary"></a>
## Build tooling boundary

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

The default Dropbox acquisition follows the anonymous contract above. Private
dependency maintenance remains available through `lab inputs` and
`lab dependencies` with their explicit bindings and authenticated owners.
The obsolete `lab prepare --drive-binding/--drive-token-fd` DMG path is rejected
before source preparation or token access. Operator downloads and their
resumable caches belong to launcher A and its selected delivery descriptor;
`lab cache --profile operator` cannot import an installer into build storage.
No public/private transport fallback or new credential authority is introduced.

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
New backend producers export only the pinned Git tree into an owned disposable
build context. Public regular files use 0644, executable files and child
directories use 0755; the scratch root remains private. The launcher umask,
original checkout, credentials and runtime state are unchanged. Links, escaping
paths, duplicate members and an altered exported Dockerfile fail closed. The
context policy enters the backend build key so earlier mode-dependent images
cannot be reused as corrected outputs. Scratch is removed on success or failure.
This corrects non-root access to public source/SQL files, not runtime privileges
or readiness criteria. Frozen producer plans retain their original behavior.
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
an existing `.tmp` directory on the same verified volume, with a path no longer than
29 UTF-8 bytes. Only the invocation's private child directory is removed after
testing. The shared scratch owner keeps the original nine-byte socket child
suffix, allowing the launcher's ordinary workspace `.tmp` when it fits. A
longer workspace uses the launcher's automatic same-volume selection of a
shorter socket-only `.tmp`. It checks a valid saved location, then private
per-user candidates on the selected mount or the same writable Data device.
Selection itself is read-only; marked private creation occurs only after the
normal workflow confirmation. Linked, foreign, unavailable or other-device
paths are rejected, with no manual path prompt, symlink or disk fallback.
Direct specialist tools retain explicit `--test-tmp-parent` selection. This
does not move compiler or media scratch. CARLA's test cache is explicitly inside the workspace. An inspected
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

This produces new preparation inputs, not the bytes of an existing kit. Complete
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

The current ordered build seals independently verified upstream group manifests
and the application digest for that invocation. Low-level packaging can also
accept explicit source-reviewed checkpoints; it has no hidden old-checkpoint
default. All contract fields and VM-to-host bindings remain enforced. Missing,
changed or incomplete pins cannot produce a complete application. Low-level
media requires either verified developer results or both explicit group and
Setup pins. No command silently adopts an adjacent result.
Direct Setup and DMG builders also require explicit source-reviewed checkpoints
or the typed developer seal passed by the ordered chain. No fixed release JSON
is shipped in the source tree. Setup generates its signed embedded release record
from that validated input; missing selection fails before host/signing, copy or
compression work. Runtime still reads only that embedded record, never a mutable
source catalog or an adjacent kit's self-reported hash.
`setup` requires an explicitly selected authorized signing identity; it has no
automatic ad-hoc fallback. `dmg` reuses the verified Setup built for that same
application and independent source pin. Neither target launches Setup or the
demo. Compiler scratch, assembly and media staging remain on the selected
volume. A signed engineering candidate is not notarized distribution
or installation qualification.
See [specialist commands and scope](../../docs/development/release-reproduction-r2.md)
for the exercised scope, exit codes and remaining gates.

### Ordered developer chain

#### Developer result sealing

A source-reviewed schema-2 producer plan may select
`resultPolicy: seal-developer-results-v1`. This build-only policy validates the
same pinned sources, acquired input archives and exact upstream owner receipts,
then seals the resulting group manifests and application digest for that build.
Seals are immutable, digest-addressed records on the selected build volume,
binding the base definition, source selections and upstream result keys. Workers
require the independently passed seal digest and preserve all payload validators.
They reject changed, linked, incomplete or mixed historical/developer inputs.

The chain forwards its exact `productVersion` to downstream result sealing.
Group/application seals, Setup's developer label and the DMG filename use that
selected version; no fixed candidate number is substituted. Different versions
have different seal/build identities. Separately built reproduction media may
have different signed bytes and does not overwrite the public delivery with
the same product-version label. Reviewed-checkpoint operations cannot accept a
developer version override, and frozen predecessor owners are unchanged.

Setup embeds the sealed group locks and application digest before signing.
Installation still requires exact manifests and payload hashes; it has no
developer trust fallback. A developer result is not a published or qualified
release. Explicit source-reviewed checkpoint arguments remain supported; old automatic
plan and output defaults are not shipped in the current tree. Historical pins and frozen producer sources are not
rewritten. Repeats verify and reuse exact results without acquiring inputs again.

The current `build --target all` route invokes 17 developer steps from the source-reviewed
[ordered producer plan](../../workspace/releases/build-plan.json).
This plan extends the accepted separate build-tools roles: it binds the base
definition, exact integration-repository commits and dependency order. It does
not modify component pins, input manifests, the independent Setup pin or trust
policy. `plan` exposes these selections before execution.

Each producer is an independent clean detached checkout on the bound volume.
An exact object already in the explicitly selected root repository can be
prepared without network; fetching a missing object requires
`--prepare-dependencies`. Wrong remotes, revisions, dirty checkouts and unowned
paths fail without reset. Each worker imports only its selected frozen adapter.
Native/UI source acquisition follows the same rule: a shallow producer does
not imply that the selected application commit is present locally. With explicit
acquisition enabled, a missing exact object comes from its declared origin;
an available object may be reused from the verified producer repository.
This separates application generation from the later source-reviewed Setup pin
without a circular source-to-manifest hash or implicit current-HEAD selection.

The parent holds the existing workspace lock. Workers receive only the exact
selected dependency results and their own target cache. Saved state retains
all older valid results; workers cannot replace an existing build receipt or
change source, artifact or storage bindings. Repeats run owner verification and
reuse unchanged results. A failure preserves completed work and compact logs;
an unverified partial native output still requires the owner's inspection and
resume procedure. No automatic retry or pin adoption is introduced.

The public launcher selects the schema-2 successor plan described above instead
of the historical output-pin route. Both routes keep the same owner ordering,
source isolation, result verification and failure preservation rules.

The [current developer selection](../../workspace/current-developer-build.json)
binds the reviewed plan and its exact producer roles. Scratch/context fixes are
effective only in those selected committed owners, not merely in the launcher's
working tree. Previous plan revisions retain their original inputs and receipts;
they are not competing current defaults or silently upgraded producers.

Current-product maintenance advances only the reviewed application and media
owners needed for that product. Unchanged native/UI and heavy component inputs
retain their exact pins. A source commit is frozen before a successor plan
selects it; no moving HEAD, self-reference or receipt rewrite is permitted.
The current B selection targets the same product version as the selected A
delivery, but newly signed B results are independent media and cannot replace
or inherit acceptance from A. Local source checks are not a completed B build.
Before binary-input acquisition, launcher B compares the declared application
and media owners' Git blobs/modes with the current file-level packaging recipe
closure. A stale owner, missing local object or changed relevant input stops
without fetching or executing an owner. Documentation-only changes do not
change that closure. This check never adopts a newer producer or rewrites a
receipt; explicit source/plan maintenance owns the successor selection.
The current developer selector and its selected plan are control records, not
payload equivalence inputs: their path and complete digest are checked separately
to avoid a source-commit/selector self-reference. They remain in normal recipe
fingerprints and cache keys. No other recipe input is excluded from comparison.

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
declared complete build-input digest-cache objects, never operator DMGs.
The current inventory consists of the five acquired dependency archives and
the selected wheel lock. Original raw Factory provenance is not a missing B
download; prebuilt/rebuilt controller identities remain independently checked
by their normal consumers.
Both workspaces must be separate,
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
