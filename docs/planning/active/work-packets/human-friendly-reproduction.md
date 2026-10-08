<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Human Friendly Repository and Release Reproduction Plan

- Status: R1 complete; R2 implementation in progress; R3 and R4 planned
- Version: 0.10
- Prepared: 2026-10-08
- Owner: Demo Solution Team
- Parent: [Installable distribution and reproducibility](../installable-distribution-and-reproducibility.md)
- Baseline: [Kit028 / Setup042 / Factory .41](../../../qualification/current-baseline.md)
- Tracking: [Cross repository change journal](../../repository-change-journal.md)

## Purpose and completion promise

A new developer receives one repository URL, one immutable release tag and one
guide. From those inputs, the developer obtains the exact required sources and
dependencies, builds the selected profile, and verifies the result without the
maintainer's checkout, private working files or conversation history.

An operator receives one complete DMG and follows the installation and demo
guide without cloning source or compiling Unreal. These are separate promises.
The release declares which build profiles and runtime scenarios were actually
qualified. Reproducing a tested configuration does not imply byte-identical
signed output, safety certification or access to restricted dependencies.

This packet refines Stage 4, Stage 5 build verification and Stage 7 release
materials. It does not replace the parent execution plan or close its remaining
native installer and runtime gates. The initial request authorized planning and
documentation. On 7 October the user authorized starting R1. Its definition and
read-only validator are now implemented; no repository move, binary build or
binary publication is performed by R1. Its source and documents use the
existing integration branch for the Git handoff.

## Scope and preserved boundaries

Use `aosedge-sdv-demo` as the product entry repository. Retain the component
repositories and their independent lifecycles. Keep simulation forks and their
restricted dependencies separate. Do not introduce a monorepo, Git submodules,
a second runtime controller, or a documentation-only repository for this work.
This follows [ADR 0006](../../../architecture/decisions/0006-lifecycle-based-repository-ownership.md)
and [ADR 0007](../../../architecture/decisions/0007-solution-documentation-home.md).

Preserve existing tags, original build provenance, credentials, release-number
ledgers, Production, retained tests and required build inputs. Do not rebuild
CARLA or Factory merely to reorganize documentation. The private video
repository is outside scope. Source-tree layout changes require a dependency
and documentation-link check before migration; automatic checkout preparation
can initially retain the supported sibling layout.

## Starting gaps

| Observed input | Gap to close | Work block |
| --- | --- | --- |
| [Workspace manifest](../../../../workspace/repositories.json) and [doctor](../../../../scripts/workspace-doctor) | Exact pins exist, but preparation is manual; branch-name checks reject detached exact-revision checkouts; legacy Editor launch paths are mixed into the workspace check | R1 and R2 |
| [Kit028 source lock](../../../../workspace/checkpoints/installer-kit-028-source-lock.json) | Application and Factory tools use different revisions of the integration repository; built inputs and later source publication have distinct provenance | R1 |
| [Candidate record](../../../../workspace/checkpoints/installer-kit-028-candidate.json) | Useful historical inheritance does not provide a single resolved release bill of materials or a complete artifact acquisition route | R1 |
| [Source reproduction guide](../../../getting-started/reproduce-demo.md) | Reader must assemble component instructions and know the development environment | R2 and R3 |
| [Documentation map](../../../README.md) | Current routes exist, but many historical and specialist entries compete for attention | R3 |
| [Current qualification](../../../qualification/current-baseline.md) | Installed scripted proof is not fresh-clone source reproduction or complete native release qualification | R4 |

## Three supported routes

| Route | Inputs and work | Intended result |
| --- | --- | --- |
| Operator | Complete pinned DMG, declared host prerequisites and the user's Cloud access | Installed demo; no compiler or source checkout |
| Developer | Root tag, pinned project sources, declared toolchain and verified prebuilt heavy dependencies | Build and modify project code and assemble a matching installer without rebuilding the simulation engine or Factory by default |
| Full source | Root tag, all declared source revisions and assets, toolchains, restricted-source entitlements and build capacity | Rebuild CARLA, Factory and project components from the declared inputs; identify any unavoidable binary or licensed inputs explicitly |

R1 must enumerate exactly which components are built or reused by each profile.
"Full source" must not hide an undocumented prebuilt VDP base, SDK, native
helper, container image or host package. Its scope and remaining external
inputs belong in the release record. Cloud access and signing are not required
for every offline source check; report their absence only for operations that
actually need them.

## Execution order and ownership

| Block | Responsible owner | Dependencies | Completion evidence | Current state |
| --- | --- | --- | --- | --- |
| R1 Define the release and dependency closure | Demo Solution Team with component build owners | Current locks, recipes and source publication evidence | Validated release specification, ownership map and delivery design with explicit unresolved gates | Complete; Google Drive and version policy accepted |
| R2 Automate preparation and builds | Integration build tooling; component owners retain their build logic | R1 schema, profile and dependency decisions | Repeatable commands, deterministic validation, resume and negative tests | In progress; external SSD required for this development campaign |
| R3 Provide the human documentation routes | Integration documentation; component maintainers | R1 terminology and R2 public command contract | One release landing page, three usable guides and working navigation | Planned |
| R4 Prove reproduction and prepare release handoff | Integration qualification and release owners | R1 to R3 candidate | Fresh environment reproduction evidence, preserved runtime gate results and obtainable matching artifacts | Planned |

Execute R1 before fixing the command contract in R2. Draft R3 alongside R2,
then validate its actual commands in R4. Finish a block through its relevant
tests and corrections without making every internal action a new approval
checkpoint. Escalate only a real unresolved design, access or authorization
boundary; retain the parent plan's scope and safety constraints.

## Block R1 Define the release and dependency closure

### Current result

The [resolved Kit028 definition](../../../../workspace/releases/kit028-setup042.json),
[schema and contract](../../../../contracts/release-reproduction/README.md),
[inventory](../../../development/release-reproduction-r1.md) and read-only
`scripts/validate-release-definition` are implemented. They retain original
source/build provenance, pin the two integration roles separately, check CI
consistency and expose three blocked profiles. No automatic downloader or
builder has been added.

The optional local source gate additionally checks ten commit objects, the
baseline tag target and 28 recipe files without fetching or changing checkouts.
Service/backend Docker base digests and service native-dependency pins are
already present; the inventory preserves them and records Apache-2.0 project
licensing rather than treating those bases as unpinned.

The owner selected Google Drive in the existing Workspace account instead of
S3. The [delivery design](../../../development/release-reproduction-r1.md#selected-delivery-route)
keeps public Git metadata and separate, non-overwritten release files with
read/download access for approved testers. Supported release inputs are retained.
The owner accepted the product numbering/tag policy: next new candidate
`1.2.0-rc.1`, stable target `1.2.0` after qualification, and tags
`sdv-lab-v<version>`. **R1 is complete.** The accepted policy does not create
a cloud resource, upload, release tag or replacement for the historical kit.
Actual folder/API setup and verified downloads belong to R2, not R1 acceptance.
Effective Factory41 configuration and native/simulation dependency closure
remain explicit inputs for R2; clean-build/native qualification belongs to R4.
Neither local media nor the older Factory template/guest driver is presented
as a complete clean-reproduction recipe.

### Work

1. Produce a profile-specific dependency inventory covering the integration
   app, Gateway, platform/VDP, both services and backends, CARLA, Unreal,
   Factory/AosCore/KUKSA recipes and patches, host runtimes, Cloud SDK and
   preparation exports. Record owner, source pin, license/access conditions,
   build recipe, artifact format, size and acquisition method for each input.
2. Specify one root release manifest and schema. Reuse component manifests
   by reference and digest rather than duplicating their authority. Resolve
   inherited checkpoint data into a complete selected release view; a user
   must not need to interpret earlier kit history.
3. Define fields for product version and release status, profile coverage,
   source commits, toolchain pins, artifact identifiers/digests/download
   locations, platform constraints, build dependencies, document versions,
   test evidence and known limitations. Git branches are development metadata,
   not a requirement for reproducing an exact commit. Avoid circular hashes:
   the tag selects the root commit; external receipts bind the final outputs.
4. Reconcile the two integration checkout roles. Bring the required Factory
   build tools into the canonical release source after review and parity tests,
   or explicitly lock and automatically resolve a separate build-tools input
   if consolidation is not yet safe. Do not require a human to select a second
   branch; do not delete the old worktree or move a published tag as a shortcut.
5. Define an immutable artifact delivery route with authenticated provenance
   and integrity checks. A local SSD path is not a delivery route. Select
   hosting, access and retention before publishing; separate public source
   from restricted or not-yet-approved binary redistribution.
6. Define a product version scheme for future releases and candidates. Keep
   Kit, Setup, Factory and Cloud package versions as traceable internal fields.
   Preserve `demo-v1.1` and `candidate/kit028-setup042` unchanged. A source-only
   or partially qualified candidate must not be labelled a completed release.

### Deliverables and acceptance

- A reviewed release schema, profile matrix, dependency/build graph and one
  resolved candidate definition, with current manifests mapped to their roles.
- Every required input has a retrievable immutable identity, a build recipe or
  an explicit unresolved access/redistribution gate. Missing inputs prevent a
  profile from being marked reproducible, not independent work on other profiles.
- Root/component pins and CI are read from the same source of truth or checked
  for consistency; no manually maintained competing pin set.
- Tests reject unresolved inputs, mismatched component manifests, unavailable
  required artifacts and unsupported profiles with actionable messages.
- Original Kit028 media and build records remain intact. New builds use clean,
  committed inputs; old source-to-artifact correspondence is not retroactively
  described as a clean or byte-identical rebuild.

## Block R2 Automate preparation and builds

### Storage and execution boundary

On 8 October the owner required external SSD storage for R2. Sources and small
project documents may stay in the integration checkout. Prepared checkouts,
downloads, caches, temporary build/test directories and outputs must use the
explicit external storage root. Verify its mounted external volume identity,
bind that identity to preparation state, and fail closed on disconnect or
replacement; never fall back to the internal disk. Reuse retained inputs
without copying a kit merely for status checks. Preserve the existing build
space guards and show additional space demand before acquisition/build.

The build-only entry point stores no live Test, enrollment or runtime state.
Its local preparation receipt binds the release definition, profile and SSD.
Exact source preparation and verified artifact acquisition are separate stages;
source-only success is not complete preparation. Initial target adapters must
call the existing owner scripts, and unsupported/unresolved targets must fail
with their actual gates rather than claim a full build. The separate private
Drive artifact root is created. Authenticated CLI acquisition and per-release
file bindings are not yet configured; folder creation does not publish a release.

### Implementation checkpoint

The [R2 command and evidence record](../../../development/release-reproduction-r2.md)
contains exact build keys, first/repeat results and preserved failure diagnoses.
Seven public source roles were remotely prepared at fixed commits. Real owner
builds passed for Presenter/Driving Control/web UI, the Cloud SDK, both backend
images and OCI export, Brake V1/V2/V3, Tire V1 and Gateway. Their unchanged
outputs are reusable; the Gateway SDK is an explicit hash-bound input, not an
undeclared host library or full-source qualification.

Preparation now selects the reviewed service exports and common VDP runtime,
while retaining Factory .41. Host assembly verifies native ancestry and
relocation, then probes help/version without network or Homebrew. Backend and
VM inputs, complete application assembly and stable-signed Setup also pass
first/repeat proof. Independent source checkpoints select their new manifests
and application digest; historical locks and media stay unchanged. Complete
DMG creation, unchanged-output reuse and read-only mounted inventory/signature
checks also passed. The workspace contains 17 verified results across 15 target
types. The test image was detached; no installer or demo was launched.

Full local regression ran 932 tests: 931 passed and one skipped. A separate
root-only source export passed all 109 reproduction fixture tests. CI now has
a clearly labelled root-only resolver/adapter job; these fixtures do not prove
a complete native build, installation or live operation.

The separately authorized Docker disk migration preserved existing data;
R2 itself does not manage Engine lifecycle. The private Drive root passed
metadata and small synthetic upload/readback checks. CLI OAuth, release file
binding, capacity and release-sized transfer remain open.

R2 remains **in progress**. The ordered `--target all` chain and explicit frozen
producer selection passed two real 17-step unchanged-output runs; the repeat
took 80.09 seconds. Offline first/repeat/failure fixtures also pass.
Narrow recipe invalidation and shared-cache capacity
accounting, authenticated artifact delivery and full-source input closure
remain open. Chain implementation does not qualify a fresh-clone profile.
R3 human routes and R4 acceptance
remain separate. Reuse completed results; do not rebuild heavy inputs merely
to resume this packet.

### Work

1. Provide one small product-facing entry command over the existing build and
   validation tools. It prepares/builds/verifies inputs; it does not duplicate
   Demo Control, start a demo implicitly, enroll users or publish to Cloud.
2. Prepare exact source revisions automatically into a declared workspace.
   Accept a detached checkout at the correct pin. Keep maintenance branch
   policy separate from release validation. Reject collisions, wrong remotes,
   dirty user checkouts and escaping paths without reset, overwrite or deletion.
3. Separate profile-specific preflight from legacy Editor launcher checks.
   Check host/architecture, toolchains, entitlements and disk demand before
   large downloads. Do not require Unreal source for the operator/developer
   profiles when it is not a selected build input.
4. Resolve and verify artifacts through the R1 manifest. Use a shared cache
   keyed by immutable identity, resume interrupted preparation safely, and
   report progress and reuse. Retain the existing disk guards; derive peak
   space from the selected build graph rather than allocating duplicate kits.
5. Encode dependency ordering and invalidation: rebuild changed owners and
   downstream manifests/Setup only. Make requested outputs and reused inputs
   visible before expensive work. Keep canonical Factory/CARLA recipes with
   their owners and retain warm caches.
6. Separate offline checks, builds, installation and live qualification.
   Credential acquisition, release signing and staging deployment use the
   established explicit owners and authorization; no secret or enrollment
   state enters a source tree, cache key, argument log or receipt.
7. Add regression coverage for first/repeated preparation, interruption and
   resume, corrupt/missing artifacts, unavailable access, insufficient space,
   wrong pins, unsupported OS/architecture and a dirty pre-existing checkout.

### Command interface

The implemented interface requires an explicit external workspace. These
examples prepare and verify sources only, not the complete profile:

```sh
./lab plan --profile developer
./lab prepare --profile developer --storage /Volumes/BUILD/workspace --sources-only
./lab verify --storage /Volumes/BUILD/workspace --sources-only
```

The entry point plans `full-source` explicitly; its preparation/build remains
blocked on declared missing inputs. The prepared profile and
release are recorded so a later command cannot silently switch them. A status
operation explains completed work, reusable results, missing prerequisites and
the next operation. A failed command exits nonzero and reports a bounded cause.
Any supported target-specific build options are defined and tested in R2,
not guessed by users from internal scripts.

### Deliverables and acceptance

- One documented executable entry point, release resolver and build adapters,
  reusing existing owners instead of reimplementing their business logic.
- In an empty declared workspace, preparation obtains the selected inputs;
  a repeat does not duplicate them or alter user state. A warm build reuses
  valid outputs and invalidates only the affected dependency closure.
- CI consumes the same resolver/commands. Source-only CI, native build tests
  and live qualification remain separately labelled.
- No developer username, SSD mount name, inherited environment or hidden
  sibling checkout is required. Declared, pinned caches may be reused but must
  not supply unlisted inputs.
- No implicit runtime start, signing, Cloud publication, provisioning or Finish.

## Block R3 Provide the human documentation routes

### Work

1. Make the root README a short product landing page: purpose, supported
   configuration, selected release/status and four entries: Run the demo,
   Build from source, Understand the architecture, Contribute.
2. Write one linear operator guide and separate developer/full-source build
   guides. Show prerequisites, access, commands, expected results, measured
   build/storage needs and recovery from common failures. Keep unresolved
   measurements explicit until R4 supplies them; do not invent durations.
3. Present a product map grouping platform, Brake, Tire and simulation under
   SDV Lab. Explain independent Git ownership without requiring manual clones.
   Standardize component READMEs with role, local checks, component docs and
   a link back to the complete demo entry point.
4. Separate current instructions from specialist design and dated evidence.
   Preserve canonical requirements, contracts, ADRs, stable IDs and qualified
   release reports. Remove obsolete instructions from the normal route only
   after checking references; Git history retains superseded work. Do not
   create another archive of binary experiments or copied component manuals.
5. Publish or generate a coherent documentation view from pinned sources if
   needed. Keep each source document with its owner; test navigation in the
   root-only checkout and on the hosted repository, not just a sibling vault.
6. Add a short contribution guide for choosing an owner, changing a shared
   contract, running checks, updating source pins and preparing a release.
   Keep maintainer planning/journal links out of the operator's required path.

### Deliverables and acceptance

- Landing page, operator/developer/full-source guides, component map,
  troubleshooting and contribution route, all in English.
- A new reader can select the right route without understanding Kit/Setup
  numbering, old worktrees, the chat or past experiments.
- Commands are exercised in R4; historical examples are not represented as
  current copy-and-run instructions. Relative links work in their declared
  viewing context or resolve to pinned hosted component documentation.
- `docs-check` and component documentation gates pass; stable contract and
  requirement references remain valid.

## Block R4 Prove reproduction and prepare release handoff

### Work

1. Freeze a candidate from committed reviewed sources. Record the selected
   root revision and dependency closure; do not silently retag an older kit.
2. Run offline resolver/build tests first, then exercise the documented fresh
   clone and developer build on the dedicated M1 or an equivalently isolated
   declared environment. Do not use the maintainer's checkout, credentials or
   warm outputs as undeclared dependencies. Declared credentials must be
   obtained/configured through the supported route.
3. Qualify full-source rebuilding separately on hardware with the measured
   disk/memory capacity. M1 runtime qualification does not prove that this M1
   can efficiently build Unreal/Yocto. If that profile remains unverified,
   disclose it; do not let a developer-profile pass imply full-source success.
4. Install the resulting matching DMG through the normal path and verify the
   intended demo. Reuse existing valid candidate-bound evidence where inputs
   are unchanged; new or affected artifacts require corresponding tests.
   Preserve the parent's open native operator, moving SOTA, secure token entry
   and interruption/repair gates until their own evidence closes them.
5. Verify authorized staging progression one version at a time, Safe Stop for
   VDP, independent QM services, offline local operation/queued recovery,
   resets/history and ignition as applicable to the release scope. Keep native
   UI and scripted results distinct. Shut down owned test processes afterward;
   preserve the shared Docker Engine and persistent data unless retirement is
   separately in scope.
6. Produce a release report identifying source/profile/artifacts, actual
   environment, timings/storage, passes, failures, exclusions and remaining
   gates. Complete license/notices and signing/notarization requirements for
   the intended distribution channel before an authorized publication.
7. Verify that another authorized user can obtain the matching published
   sources, artifacts and instructions. A pushed tag without obtainable
   dependencies is not a reproducible release.

### Deliverables and acceptance

- Fresh-clone command transcript with sanitized evidence, build receipts,
  installed test results, supported configurations and explicit exclusions.
- No manual repair from the maintainer's environment is needed; discovered
  prerequisites/fixes enter source and are rechecked through the same route.
- Functional reproducibility and source correspondence are demonstrated for
  each claimed profile. Bit-identical signed binaries are a separate claim.
- Candidate publication and completed-release publication have distinct
  verdicts; no mandatory installer/runtime/signing gate is hidden by this plan.

## Maintainer records and the service repository question

Recommendation for this work: keep the plan and a short cross-repository
change journal in the existing integration repository. No additional service
repository is needed now. A second repository would introduce another access,
version and synchronization dependency without a separate owner or lifecycle.
The journal is a maintainer view, not another architecture authority or source
lock. Git records file changes; the journal records purpose, affected owners,
outcome and links to commits, evidence and the next unresolved block.

Consider a separate restricted operations repository only if work later spans
several independent products or requires a genuinely different audience/access
policy. Such a repository must not contain the sole reproducible release
definition or mandatory build instructions. Repository creation, visibility
and ownership would be a separate explicit decision. Private repositories are
not stores for secrets or confidential third-party source.

For every completed cross-repository block, update the owning documents, record
actual source/evidence references and leave one next action. For partial work,
record the exact blocker and preserve completed results. Do not copy raw logs,
chat transcripts, credentials or large artifacts into the journal. Do not mark
work done merely because a plan, a commit or an intermediate kit exists.

## Accepted decisions and remaining release boundaries

| Choice | Treatment | Status or required before |
| --- | --- | --- |
| Future product version and tag syntax | `1.2.0-rc.1` then qualified `1.2.0`; `sdv-lab-v<version>` tags; preserve old tags and independent internal numbers | Accepted; no new tag created by R1 |
| Artifact host and access | Google Drive in the existing Workspace account; separate non-overwritten files, approved readers and retained supported-release inputs | Accepted design; actual binding and download checks in R2 |
| Full source support envelope | Declare licensed/binary inputs and measure a suitable builder; report this profile separately | R2 full-source preflight and R4 claim |
| Distribution signing availability | Use the accepted Developer ID and notarization channel when its actual prerequisites are available | External distributable release |

The R1 choices are recorded in the owning release contract. Remaining build
and external-release conditions do not block independent offline work. Any
change to runtime, trust or repository ownership still follows the existing
architecture-change procedure.
