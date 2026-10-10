<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross Repository Change Journal

This maintainer journal records coordinated changes to the SDV Lab repositories.
The [distribution plan](active/installable-distribution-and-reproducibility.md)
controls delivery order; the [current baseline](../qualification/current-baseline.md)
identifies the implemented candidate. Component source, contracts and release
locks remain authoritative. This journal links them and does not duplicate them.

The latest [publication checkpoint](#2026-october-10-one-run-launcher-source-handoff)
records the owner-authorized README and one-run launcher source handoff. Earlier
local-only entries below retain their original checkpoint state; source
publication does not constitute retroactive build or test evidence.

### 2026 October 10 Public artifact activation preflight

The owner authorized activating anonymous artifact access. The separate-public-
folder design remains applicable; this does not authorize sharing the historical
private artifact root. No Drive write or sharing change was performed because
the existing content/redistribution gate is not yet closed. `PUBLIC_PIN` remains
inactive; this entry does not claim a usable anonymous release.

Read-only checks covered the five exact archives selected by the published
launcher. All provider-reported names, sizes and SHA-256 values matched the
existing locks. Each archive's initial 1 MiB HTTP range supplied its complete
inventory, verified against its pinned manifest SHA-256: **31,491 files** across
the five inventories, **5 MiB** transferred in total. No complete archive was
downloaded, extracted, rebuilt or executed. This verifies inventory identity,
not every file's contents, embedded filesystem or absence of secrets.

Concrete publication gaps:

- The simulator subtree has no separately inventoried CARLA/Unreal license,
  attribution or end-user terms file. The CARLA Python wheel has its own MIT
  license, but that is not evidence for the entire simulator and its assets.
  Editor/Developer plugin descriptors and resource files occur in the inventory;
  no source/object/library files were identified under those two directory names.
  Those names alone do **not** prove that prohibited Engine Tools are shipped.
  Review the exact packaged product and asset terms before deciding that point.
- QEMU and other host libraries have bundled license notices, but no matching
  downloadable corresponding-source package or source-offer arrangement was
  identified in the reviewed archive inventories, artifact folders or release
  documents. Binary hash correspondence is not source-distribution compliance.
- The Factory archive contains its image and manifest, while the vehicle bases
  contain nested VDP packages. Their nested contents have not received a public
  content/notice review in this check; a top-level filename scan cannot close it.

The release preparation follow-up is to assemble a version-matched third-party
notice/source-delivery set, resolve the simulator distribution terms and review
the nested image/package contents. Preserve historical archives and locks. If
payload changes are necessary, adopt a new reviewed dependency generation rather
than overwrite the old one. Then copy only the approved public set, verify remote
identity and anonymous bounded access, and activate the observed catalog URL and
record hash. No additional routine sharing approval is needed inside the owner's
authorized public set; unresolved license terms are not resolved by that approval.

Reference checks on October 10 used the primary
[Unreal Engine EULA](https://www.unrealengine.com/eula/unreal), especially product
distribution and Engine Tools restrictions, the
[QEMU GPLv2 text](https://www.qemu.org/license-gpl-2/) on binary/source delivery,
and [CARLA's license summary](https://github.com/carla-simulator/carla#license).
These identify review obligations, not a legal conclusion about this build.
No installer, simulator, VM, container or background worker was started. Only
small private inventory evidence remains outside Git; credentials and private
Drive locators are excluded from this entry.

### 2026 October 10 One-run launcher source handoff

The owner authorized committing and pushing the current README, anonymous input
transport, one-run launcher, contracts, guides and regression fixtures together
to `main`. This source checkpoint follows `ffebae0`; Git identifies its exact
revision. Normal confidential-input and documentation hooks remain enabled.
The commit uses `[skip ci]` to preserve the agreed no-build boundary; the 228
offline tests recorded below are the implementation evidence, not a live build.

This handoff publishes source only. It neither makes the private Drive files
public nor activates the empty public-catalog pin. The default launcher still
reports `PUBLIC RELEASE NOT YET AVAILABLE` before making changes. A real public
walkthrough requires reviewed artifact publication/activation and a compatible
producer/storage plan. No installation, signing, runtime or Cloud action is
part of this Git handoff. Remote commit equality is checked after pushing.

### 2026 October 10 One-run developer preparation and DMG workflow

The owner approved replacing manual B1–B4 handoffs with a single downloaded
launcher and then doing the real walkthrough together. The default launcher
now shows one combined preparation/build plan, prepares the host, fixes the
root main revision, obtains the matching checkout and delegates to the existing
`lab` source/input/build owners. `--prepare-only` retains the previous boundary;
`--check` remains non-mutating. README requires only download and run commands;
individual build commands remain in the optional engineering reference.

The embedded bootstrap records the selected commit before fetching. Repeat and
interrupted acquisition retain that commit even if main advances. Existing
clean matching manual checkouts may be reused; dirty/foreign/linked/changed
checkouts and replacement volumes are preserved and rejected. Preparation and
workspace locks prevent overlapping owners. Continuation checks compatibility
and capacity before acquisition, forwards explicit tools/input/signing choices,
and invokes the canonical ordered build without changing its pins. Result paths
come from that exact chain/media receipt, not a newest-file search. Workflow
progress is diagnostic only; canonical owners verify reusable results on repeat.

Offline coverage: **228 tests passed**, including new local-Git first/repeat,
moving-main, interrupted-fetch, manual-checkout adoption, local-change/foreign
remote/volume/pin rejection, concurrent-lock and shell-to-repository handoff
fixtures. Continuation fixtures cover phase order, early capacity stops, private
versus public arguments, failure/cancellation and exact DMG receipt selection.
No compiler, real clone, installer, archive transfer, signing or runtime was
started. Synthetic repositories and test processes are disposed of by fixtures.
Shell syntax, embedded-helper parity, documentation and public-source scanning
(including untracked new source files) pass. This source remains local and
uncommitted; no push or release qualification is implied.

Remaining before a public joint end-to-end walkthrough: publish the reviewed
source, activate the reviewed public catalog/dependencies, and adopt a successor
producer plan where the selected internal/split-Docker layout is incompatible
with historical frozen owners. The launcher preserves those failures instead
of moving Docker storage, editing old pins or silently using private access.
The user requested no real build/installation in this implementation turn.

### 2026 October 9 Automatic pre-clone release catalog

The owner accepted replacing ordinary JSON-path questions with automatic
authenticated discovery, and keeping all format/release version fields inside
a stable `release-index.json`. This Class B developer-preparation amendment is
implemented in the existing integration repository and documented in the
[preparation contract](../../contracts/release-reproduction/README.md#pre-clone-release-catalog).
No runtime interface, frozen source pin or historical artifact is changed.

The one-file wizard now discovers the authorized artifact folder/catalog,
verifies a source-pinned immutable release record, checks all five archive
metadata records and generates both private bindings atomically. Manual paths
are available only through explicit `--advanced-inputs`, never as a fallback.
README B2 checks the saved preparation requirements against the cloned main
before downloads/builds; changed dependency requirements fail closed. The
canonical helper is embedded mechanically and tested for exact parity.

A new private 3,265-byte catalog was published in the existing artifact folder.
Its initial SHA-256 is
`432de15e36b6f82ecd7bffcd782212dc35610d077d6cdaded6999d2517c3c269`;
the selected immutable record's canonical SHA-256 is
`c4c5639edc09ddc363784b8fcf3c97fb5b5ff99b4815e8421bb2858b657d0da5`.
The record identifies the existing `1.2.0-rc.1-source-factory-r1` input set,
not a new or newly qualified release. Historical `release-index-v1.json`
receipts, archives and private sharing remain unchanged; object IDs stay out
of public Git.

First and repeated real catalog discovery passed with the existing authorized
Google account. Both runs transferred only the small catalog and checked
input names, parents, permissions, sizes and hashes through metadata. The
generated local selection passed the offline check and the current checkout's
source-compatibility guard. No login, archive transfer, installation, build,
signing operation, Cloud mutation or demo launch was performed. This targeted
proof is not the owner's complete six-stage preparation or R4 qualification.

Targeted coverage comprises 12 catalog tests, 26 wizard tests and nine reader
tests: compatible selection rather than latest, missing/duplicate/unsupported
catalogs, tampering, concurrent remote change, atomic failure/repeat, preserved
local edits, source drift, immutable catalog append, legacy-path migration,
secret redaction and existing wizard lifecycle. Bash syntax, embedded-helper
parity, documentation and reader-route gates pass. Disposable private catalog
and generated-selection files are removed after the checks; no helper remains
running. Source publication uses the ordinary guards with build CI skipped.

### 2026 October 9 Developer walkthrough parked for travel

The published wizard checkpoint is `f884bd86acce497c7b356f4118a094c5d90e55a3`
on `main`. The owner's live walkthrough reached the Google account and private
binding-file questions; full preparation is not yet qualified. The owner found
the `developer-inputs.drive.json` prompt unsuitable for a first-time reader.

The next proposed UX change is to remove both manual JSON-path questions from
the ordinary route, resolving compatible private bindings through an
authenticated release catalog instead. Manual paths would remain an advanced
route. Before implementation, review the existing private release index and
define its discovery and trust contract: source compatibility and trusted
checksums must be explicit, duplicate names must not select an arbitrary or
blindly latest release, private Drive IDs stay outside public Git, and catalog
discovery must not download large artifacts. This remains a proposal, not an
implemented or qualified behavior.

The owner requested parking before travel. No active preparation/build/demo
process or open handle on the selected SSD was found. `SDV-Build` was normally
ejected and its mount path was verified absent. Unrelated applications and
shared infrastructure were preserved. Resume the UX work after reconnecting
the same volume; do not restart cloning or builds. This handoff is saved locally
on the internal disk; no new implementation, release or publication occurred
during parking.

### 2026 October 9 Standalone developer preparation wizard

The owner accepted and requested implementation of one downloadable wizard
covering all six pre-clone macOS preparation stages. Class B host-tool/UX change;
the [work packet](active/work-packets/human-friendly-reproduction.md#block-r3-provide-the-human-documentation-routes)
and [preparation contract](../../contracts/release-reproduction/README.md#standalone-macos-developer-preparation)
record the accepted boundaries. README B1 now contains short download, launch
and saved-environment commands; the former large guide becomes optional
reference material. Root cloning uses current main as previously requested;
frozen component/producer pins and release artifacts remain unchanged.

The wizard discovers compatible tools, plans missing prerequisites, preserves
global/shared installations, checks explicit storage, provides resumable owned
Python/Node setup and private non-secret selection/environment files, and
separates human Xcode/Docker/Google actions from unattended checks. Google
metadata probes never transfer archives or expose tokens. No actual installer,
login, Docker operation, build, signing, source acquisition or demo process was
started during implementation. Offline fixtures exercise first/repeat/resume,
decline/check-only, invalid versions/paths/archives, lock/volume handling,
credential redaction and metadata-only access. Actual first-use qualification
remains the owner's next walkthrough, not a claimed result of these fixtures.

Validation of this source checkpoint: 25 targeted offline wizard/interactive
reader tests pass, Bash syntax passes, the documentation gate passes (341
documents), and the independent reader-route gate passes. The cancellation
fixture verifies its owned child exits; disposable fixture directories are
removed. No test helper or demo runtime is retained. Publication uses the
ordinary confidential-input/documentation hooks and skips build CI to preserve
the agreed no-install/no-build walkthrough boundary.

### 2026 October 9 Guided storage preflight presentation

The owner completed the first macOS preparation block on the new APFS SSD,
then requested a concise, automatically checked result instead of the full
device report. Class A documentation/UX correction within the accepted host
and storage requirements. Only the first block and its explanation change;
the source-selection and later build steps are not executed by this edit.

The block uses built-in macOS tools, checks native Apple Silicon/macOS 26,
an existing writable directory, a local writable APFS volume and a real mount
for a `/Volumes` path. It reports path, volume name, location, access and
free GiB, or an explicit `STOP` reason. No temporary file, formatter, installer,
permission change or source clone is invoked. Success is format/access only,
not a claim that a complete build fits; existing capacity guards remain intact.
The selected parent variable is cleared before a retry and assigned only on
success. Commands remain in the guide, not in parallel chat instructions.

The revised block awaits the owner's walkthrough. The earlier successful
device dump is not evidence that the revised block has been executed.
Static checks cover shell syntax in `sh` and `zsh`, documentation references
and Git whitespace; no preflight, installer, build or regression suite is run.

The owner's subsequent paste exposed `zsh: event not found: 0`: the numeric
negation glob triggered interactive history expansion before the function
could be defined. Static `sh -n`/`zsh -n` checks did not exercise that reader.
The corrected guide uses a quoted numeric regular expression, not a history
option change. The exact original error was reproduced in an isolated
interactive zsh; the corrected bracketed paste successfully checked the new
SSD read-only and rejected a nonexistent path. A narrowly scoped regression
fixture defines, but does not run, the guide function in interactive zsh with
history expansion enabled and includes an unsafe positive control. No build,
installer, source preparation or broad regression campaign is part of this fix.

### 2026 October 9 README and build-storage source publication

The owner explicitly requested committing and pushing all pending README,
documentation, script and regression-fixture changes across the nine maintained
repositories. All use `main`; no new branch, release tag, binary publication or
immutable source/producer pin change is part of this handoff. The video
repository remains outside scope.

The eight component README commits were pushed before this integration
checkpoint: CARLA `d5adb807f`, restricted Unreal `d800754d1`, vehicle platform
`5ba2b74`, Gateway `26a593a`, Brake service `b3f7955`, Brake backend `9bc8be8`,
Tire service `ebb0ded` and Tire backend `0ce41f2`. The containing integration
commit carries the root guides, new macOS preparation guide, accepted explicit
APFS/split-Docker storage policy, adapters and their unexecuted regression cases.

This authorization preserves the no-build/no-test boundary: all publication
commits use `[skip ci]`; normal confidentiality and static documentation hooks
remain enabled. Python syntax and Git whitespace checks do not execute product
code or fixtures. No installer, simulator, VM, backend, signing, Cloud operation
or artifact transfer is started. Published source is not a qualified release.

Next: perform the agreed joint command walkthrough and regression execution,
then select reviewed successor producer revisions if the new storage layout is
to be adopted. Existing candidate pins and qualification remain unchanged.

### 2026 October 9 Explicit build-storage choice — local implementation

The owner accepted internal or external APFS workspace selection and then
explicitly requested the corresponding script changes. Class B: build-tool
storage policy only; runtime, Cloud, release authority and frozen pins are
unchanged. The owning [reproduction contract](../../contracts/release-reproduction/README.md#explicit-build-storage)
and existing reproduction work packet record the scope.

The new probe resolves the actual Data volume for macOS firmlink paths, retains
UUID/device/ownership guards and rejects a missing `/Volumes` mount rather
than creating an internal fallback. Inputs and clone caches stay on the selected
volume. Docker may use another local disk: read-only discovery verifies its
active backing file, guards its capacity separately and combines reservations
when it shares the workspace's APFS capacity pool. No Engine lifecycle or
storage migration is introduced. The bound Factory Builder uses the same probe
and retains its host/guest guards.

Capacity inspection now works before wheel-source preparation, marks that
cache scope incomplete, supports both reviewed frozen plans and reports exact
producer storage compatibility without executing their code. Old producers
remain external-only; a successor pinned plan must explicitly adopt the new
tooling. No immutable descriptor, artifact, signature or candidate was changed.

Regression cases have been added/updated but **not run** under the owner's
continuing no-test/no-build instruction. Source/static checks are separate from
qualification. Python AST parsing, the revised guide's shell syntax and Git
whitespace checks pass; no project code was imported or executed by those
checks. Read-only macOS volume metadata confirmed the Data firmlink and APFS
pool fields used by the probe. Frozen workspace/component metadata has no diff.
No installer, simulator, VM, Docker build or Cloud operation was
started. Publication and the joint command walkthrough remain pending.

### 2026 October 9 Step-by-step README revision — local draft

Class A documentation/presentation change, authorized by the owner after the
main-branch review. Scope: nine top-level READMEs, root getting-started guides,
navigation, troubleshooting and the existing reproduction work packet.
New human routes explain macOS prerequisites, explicit clone commands, exact
Node/npm versions, private input acquisition, returned paths, expected results
and stopping boundaries. Existing implementation detail and upstream notices
are preserved as reference; no canonical contract or requirement was retired.

The owner explicitly requested no builds of any size and a later joint
step-by-step walkthrough. No installation, documented build/check command,
project test suite, simulator, VM, Docker or Cloud operation was run for this
revision. Source inspection and static Markdown/shell-shape review are not
runtime proof. This draft is not yet committed/pushed; publication is deferred
so it does not trigger build/test CI before the agreed walkthrough boundary.
The older passed checks below belong to their original checkpoints.

Static review of 14 first-use documents found no missing local targets or
anchors among 89 inspected links. All 68 shell blocks parsed with `sh -n`;
their commands were not executed. Git whitespace review is clean. The final
working set is 17 Markdown files across nine repositories and contains no
code, manifest, lock or binary edits. Repository test/quality suites remain
deliberately unrun, not reported as passed. No runtime/helper was started, so
this documentation task leaves no test-owned process to stop.

Frozen release/source pins, existing candidate bytes, signatures, access,
runtime behavior and the video repository remain unchanged. Full-source
acquisition and native retained-Test shutdown/return gaps are disclosed rather
than solved by invented instructions. The next activity is the owner's guided
walkthrough, not an autonomous build or a renewed installer campaign.

### 2026 October 9 Main consolidation

The owner required all current demo work on `main`, with other branches retained
as history. The root advances the old `main` by the 51 accepted integration
commits through `1e73ae5`. Merge `003cded` also includes Factory-tool head
`30ae661`; its file tree is identical to its first parent because those changes
were already present with newer SSD/configuration guards. Two historical merge
conflicts were resolved without removing those guards or their tests.

The current branch policy and reader guides now point to `main`. All nine
maintained repositories use it as their development and GitHub default branch.
CARLA `eb09b82` and private Unreal `9b705d6` retain identical source trees on
new `main` refs; their old compatibility refs remain. The other six component
`main` heads are unchanged from the publication checkpoint below. Upstream
repositories, historical tags and branches, video, binaries and release source
pins were not rewritten, deleted or republished.

The initial branch-metadata edit correctly failed the release authority digest
gate. It was withdrawn rather than resealing the frozen Kit028 definition.
The workspace doctor now accepts current `main` alongside historical branch
names; exact revision, remote and dirty-tree checks remain intact. Historical
manifests and Factory/build-owner source compare byte-for-byte with `1e73ae5`.

Local checks pass: 27 Factory build-gate tests, 215 offline reproduction fixtures,
8 reader-route tests, 8 workspace-doctor tests, the release-definition gate,
and the complete documentation gate (340 documents, 662 identifiers, 38 diagrams).
The existing confidentiality hooks remain enabled. GitHub CI results are
separate from local tests and Git publication; the preceding `1e73ae5` already
had a failing Repository boundaries workflow and a passing Reproduction offline
workflow. This consolidation is not a new binary release or R4 qualification.

Investigation of that pre-existing CI failure identified two portable-source
defects: a disk-probe fixture required macOS-only `/private/tmp` on the Linux
runner, and an audit linked to an ignored maintainer-local CARLA report that
does not exist in a public clone. The fixture now owns a portable temporary
directory; the audit identifies its local-only evidence without a broken public
link. Runtime disk validation and documentation-link validation are unchanged.
All 20 isolated Setup bridge tests and 19 documentation regression tests pass;
the read-only source gate resolves all ten pinned roles, 28 recipe files and
the original baseline tag. GitHub API readback confirms matching local/remote
`main` heads in all nine repositories and the current root README on the default
branch. No local tracked changes remain outside the publication commits.

No build, installer, VM, simulator, Cloud operation or large artifact transfer
was needed. Shared Docker and unrelated workloads remain untouched. Next work
is the already planned R4 clean-SSD campaign after settling the declared Builder
cache/acquisition and shared Docker storage-isolation boundaries.

### 2026 October 9 R2 and R3 source publication

At the owner's request, all pending work in the seven project repositories was
pushed before the proposed R4 clean-SSD campaign. Root `dbfd542` (42 commits)
is on `codex/installable-demo-stage3`, not merged into `main`. Component `main`
heads are Gateway `1279f4b`, platform `9a7238a`, Brake service `8e21ab0`, Brake
backend `3edc01e`, Tire service `9cb361e` and Tire backend `0ac481d`. Remote
heads match local commits and all seven worktrees are clean. Existing tags,
source locks, binary artifacts and the video repository are unchanged.

Pre-push history guards passed for all seven repositories. The integration,
platform and Brake public-source scans, source-license boundary checks,
documentation and release-definition gates passed. The existing component
REUSE gates passed for platform and Brake. An additional integration-wide
REUSE probe did not pass: that repository has pre-existing JSON/asset/license
annotation gaps and is not claimed REUSE-compliant. The committed CI applies
REUSE lint to platform and Brake, not integration; no gate was relaxed.
Remote CI completion is separate from verified Git publication.

The owner proposes a new empty 1-TB SSD for a fresh build including Factory
.41 and retaining the Drive-hosted CARLA dependency. Discussion identified
two preparation boundaries: the Factory adapter currently uses the retained
Builder's Git/download/sstate inputs, and the Docker adapter requires its
active backing disk on the selected build volume. A blank-Builder acquisition
route, declared cache policy and safe Docker storage isolation must be settled
before claiming a clean run. No disk was formatted, Builder copied, Docker
storage changed or R4 build started during this discussion. Publishing this
snapshot does not qualify the candidate or create a release tag.

### 2026 October 9 R3 human documentation routes

The authorized R3 block is complete locally. The
[product entry](../../README.md) offers Run, Build, Understand and Contribute;
the [reader index](../getting-started/README.md) leads to separate operator,
developer and full-source guides, a release selector, product map and recovery
instructions. These are English reader routes, not another copy of component
manuals. Canonical contracts, stable IDs, ADRs and dated evidence remain intact.

The new source-Factory candidate is explicitly not the older qualified kit.
Its exact delivery identity, unpublished source handoff, measured warm results
and still-unknown cold capacity are disclosed. No source pin, binary, old tag
or readiness flag was changed to make the instructions appear complete.
The full-source guide records the remaining engine/access/capacity gates.

Six component entry updates were committed locally without changing code:
Gateway `1279f4b`, platform `9a7238a`, Brake service `8e21ab0`, Brake backend
`3edc01e`, Tire service `9cb361e` and Tire backend `0ac481d`. Each adds its role,
owned documentation, local checks and a link to the complete Lab. This is a
Class A documentation/navigation change. The small accompanying documentation
checker change allows only manifest-pinned hosted Markdown references; it
continues to reject mutable/wrong-pin URLs and broken targets. Reader-only
checking is explicitly separate from the full design/traceability gate.

Evidence: ten root-only entry documents and seven live pinned GitHub references
pass; 8 new reader tests and 19 existing documentation tests pass. The full
gate checks 340 Markdown documents, 662 stable identifiers and 38 diagrams.
All six component entry checks and the platform/Brake existing quality gates
pass. Shell syntax, documented option names and checkpoint paths are validated
without compiling. A network-disabled local browser render of the landing,
operator and developer pages found no horizontal overflow; the landing page
was also visually inspected and the browser closed. Scratch was on Work SSD.

R4 remains the next block: reviewed source publication, fresh-environment
execution, candidate-bound installation/live checks and the matching release
handoff. No Git push/tag, build, large transfer, credential use or Cloud/runtime
mutation was performed in R3. No owned helper remains running; shared Docker
and unrelated workloads were left untouched.

### 2026 October 9 Artifact transfer economy

The owner accepted one upload plus exact remote metadata/checksum verification
for routine artifacts, with byte verification on the actual installation/build
consumer. A separate maintainer loopback download is no longer a per-candidate
step. Dedicated round trips require a changed transfer/recovery implementation
or provider integration, or a concrete integrity incident; completed evidence
and verified caches are reused. The
[operating policy](../governance/rapid-development-and-debugging.md#artifact-transfer-economy),
repository instructions and release reproduction contract now agree. This is
a workflow change; upload/download remain separate existing commands. No new
large transfer, build, credential change or sharing change was needed.

### 2026 October 9 R2 private delivery and tooling acceptance

The owner restored Google CLI authorization and retained the existing OAuth
scheme. Both new vehicle/Factory archives passed private upload, actual download,
metadata/digest verification and no-duplicate repeat. A separate receiver restores
31,491 files from five pinned archives; the three unchanged simulation archives
are explicitly verified cache reuse, not another network-transfer claim.
Offline repeat took 4.892 seconds. All 17 frozen steps accepted the received
inputs with old maintainer/restoration directories denied by the OS, retaining
every build key in 78.240 seconds. All 215 reproduction fixtures and three profile
plans also passed from a root-only export without siblings.

The source-Factory DMG subsequently passed full private upload/download and
repeat checks. A transient Google rate limit stopped the first upload near
completion; reconciliation and one same-ID restart succeeded without another
login, changed permissions or duplicate media. The private release index binds
all five inputs, exact DMG and locally committed code checkpoint `91fd485`;
its upload and raw readback passed. See the
[delivery result](../development/release-reproduction-r2.md#source-factory-media-delivery-on-october-9).

The [original R2 tooling criteria](../development/release-reproduction-r2.md#r2-acceptance-and-remaining-release-work)
are closed for the accepted developer plus source-Factory route. This is not
release qualification: source push/tagging, a different approved reader, cold
capacity/fresh-clone proof, full-source closure and native/live/signing/licensing
gates remain explicit. R3 human documentation is next; R4 keeps its original
qualification responsibilities. No historical manifest or readiness flag changed.

Only documentation changed in this closure turn. Large files remained on SSD;
the temporary source export was removed, all owned check/transfer processes are
finished and no new runtime or media mount remains. Shared Docker and five Watt
containers were preserved. Approximately 402 GB / 374.4 GiB remained free on Work.
Private bindings, receipts and logs stay outside Git; no push or new tag was made.

### 2026 October 9 Source Factory integration through complete media

After Work/Clean consolidation removed the capacity blocker, the independent
source Factory .41 passed an offline boot and clean shutdown. New committed
image/group/application checkpoints and the producer plan at `01936d0` now
select that image without changing historical/default pins. The complete
17-step chain produced a separate 14.16-GB engineering DMG; every unchanged
step reused its output on a 69.22-second repeat. Mounted inventory, Factory
digest and Setup signature checks passed, followed by media detachment.

An actual macOS device-number change after SSD remount exposed an input-receipt
reuse defect. Explicit volume/content revalidation now restores the affected
manifest-backed input stamps while preserving original receipts and all payload
bytes. Recovery of other historical media/dependency receipt types remains
outside that implementation. Full regression ran 1,028 tests (one skipped);
203 reproduction fixtures also passed from a root-only export without siblings.

Integration sources/checkpoints are committed locally; no push, tag, new Drive
upload, public release, installation or Cloud mutation is part of this block.
The new candidate remains Apple Development signed and not notarized or live
qualified. The temporary source export was removed after checks; owned VMs,
workers and the media mount are closed. Shared Docker/Watt is preserved.
Approximately 474 GB / 442 GiB is free on the external SSD.

See the [campaign evidence and exact artifact identity](../development/release-reproduction-r2.md#source-factory-downstream-packaging-on-october-9).
R2 remains open for complete build-input acquisition, capacity and reader handoff;
R3/R4 remain separate. Continue with the missing input acquisition rather than
rebuilding the completed Factory or retained CARLA.

### 2026 October 8 Factory source rebuild on the external SSD

The owner included Factory .41 in the clean build and required the QEMU Builder
disk and build storage on the external SSD. The relocated disk passed base
identity, structure, complete virtual-content comparison and boot verification.
The new build-only `lab factory` route prepares nine exact source checkouts and
a clean Moulin configuration; it reuses downloads/sstate explicitly but no old
`tmp`, image or warm `auto.conf`. The historical .11 recipe, Factory .41 image,
CARLA dependency and frozen installer chain remain unchanged.

Corrective build-tool changes bind the Builder volume UUID, use the selected
SSH trust path and repository-local lifecycle owner, and check the effective
Factory version/architecture and KUKSA source before compiling. Initial real
preparation passed. Offline regression: 1,014 tests, 1,013 passed and one skipped;
25 Factory build-tool tests, historical definition and documentation gates pass.
The source checkpoint `78f837a` subsequently completed compilation, native tests,
package/image QA and verified transfer of a new .41 image. Its SHA-256 is
`e7c9e3b20c08a91f9072014ece0861d8ae34787ef14d4ef9b50693c062439d57`.
Post-build exact layer restoration/preparation reuse and disk checks passed.
Follow-up adapter fixes suppress macOS archive metadata and restore only the
owner's exact layer change. Their regression passed 1,015 root tests (one
skipped) and 27 Factory build-tool tests. Two verified obsolete internal Builder
files were removed, recovering approximately 85 GiB; all working data and
caches remain on SSD. Owned Builder/DNS processes are stopped. See the
[Factory build route](../development/release-reproduction-r2.md#factory-source-build-on-external-storage).
Cold acquisition and live qualification are not claimed. The frozen installer
chain and historical Factory remain unchanged. Downstream image binding and
external capacity reconciliation remain: approximately 106 GiB is free versus
the frozen chain's 166-GiB admission guard. No guard or storage boundary changed.

## Recording convention

Use one dated entry per meaningful cross-repository work block, not per command.
Record purpose, affected repositories, outcome, validation, commit/publication
state, remaining blocker and next action. Use exact commit/tag and evidence
references once they exist; distinguish local edits, committed sources, pushed
sources, built artifacts and qualified releases. Later work gets a new dated
entry so earlier outcomes remain understandable in their original scope.

Keep records sanitized and compact. Credentials, private file contents, raw
operational logs, VM images, caches and video material stay outside this journal.
Do not make the journal required reading for installing or rebuilding the demo.

## 2026 October 7 Documentation reconciliation

- Purpose: reconcile documentation with Kit028 / Setup042 / Factory .41 rather
  than presenting historical demo-v1.1 as the current installer.
- Repositories: `aosedge-sdv-demo`, `aos-vehicle-platform`, `carla-ego-runtime`,
  both Health service repositories and both Health backend repositories.
- Outcome: 87 Markdown documents revised/added in the recorded audit; source,
  media, profiles and published tags unchanged. These counts describe that
  audit, not subsequent planning edits.
- Evidence: [reconciliation report](../qualification/documentation-reconciliation-2026-10-07.md)
  and [inventory snapshot](../../workspace/checkpoints/documentation-inventory-2026-10-07.json).
- Recorded validation: documentation gate passed; 759 source tests ran,
  758 passed and one skipped. These are not new native/live qualification.
- Publication state at this checkpoint: documentation edits remain local and
  uncommitted; no new push or artifact build.

## 2026 October 7 Human friendly reproduction planning

- Purpose: expand the agreed four-block repository/reproduction direction into
  inputs, owners, deliverables, dependencies and acceptance criteria.
- Repository changed: `aosedge-sdv-demo`, documentation only. Existing pending
  documentation work is preserved; component source and video remain untouched.
- Outcome: [detailed work packet](active/work-packets/human-friendly-reproduction.md)
  added and linked from the parent plan and planning index. R1 to R4 remain
  planned. The recommended maintainer home is this repository; no separate
  repository has been created and no source layout has moved.
- Validation: documentation gate passed with 331 scanned Markdown documents,
  662 stable identifiers and 38 Mermaid diagrams; tracked/new-file whitespace
  checks passed. No runtime test was needed for this documentation-only step.
- Publication state: local documentation only; no commit, push, tag, build or
  live test is performed by this planning step.
- Next action: review the detailed specification, then begin R1 release and
  dependency definition when implementation is requested. Do not start a
  new native E2E campaign merely because this planning packet was added.

## 2026 October 7 Documentation publication

The user authorized committing and pushing the documentation reconciliation
and reproduction plan before beginning repository reorganization. The following
seven commits were pushed and their exact branch heads verified by remote read:

- Integration, `codex/installable-demo-stage3`:
  [b8e78c2](https://github.com/alexmaninblack/aosedge-sdv-demo/commit/b8e78c2743386d407237301f795ccc715e8869be).
- [Vehicle platform](../../../aos-vehicle-platform/README.md), `main`:
  `b4fe9b7e441843f7cd75071ef96aaf25b2f469f9`.
- [Gateway and Driving Control](../../../carla-ego-runtime/README.md), `main`:
  `a64b9950fc0ea6cf4eaf0cf3ac162e8b810b09e4`.
- [Brake service](../../../brake-health-service/README.md), `main`:
  `abda6c566cb77a8f75df91224d4460531c60bc43`.
- [Tire service](../../../tire-health-service/README.md), `main`:
  `41248034c282407ff4e693fe4b61d2f2ad75203a`.
- [Brake backend](../../../brake-health-cloud/README.md), `main`:
  `614f1c1abd75bf369bbacb791dbd8e0074d8dcfb`.
- [Tire backend](../../../tire-health-cloud/README.md), `main`:
  `fc1f6a8d0e015d583a0abb7b412d2e3733e2cd5b`.

The scope is 90 documentation/inventory files across seven repositories. This
receipt is a subsequent journal-only commit. The integration branch is not
merged into `main`; component source/build pins, existing release tags and
immutable media remain unchanged. These documentation commits are not new
Kit028 build inputs or evidence of a new runtime qualification. The video
repository and simulation forks are untouched.

Before publication, `docs-check` passed with 331 scanned Markdown documents,
662 stable identifiers and 38 Mermaid diagrams; component lock validation and
whitespace checks passed. The repeated integration suite ran 759 tests in
38.513 seconds, with 758 passing and one skipped. The integration confidential
input guards passed during commit and push.

The public-source scanner passed for integration, platform, Gateway, Brake
service and both backends. Applying that scanner beyond its ordinary repository
set to Tire service flagged an unchanged private VM bridge URL example in its
README. The same example exists in the parent commit; the documentation delta
adds no such URL or credential. No scanner exception or runtime change was
introduced to hide this pre-existing scope difference.

Next work remains R1 release/dependency definition under the detailed packet.
This publication does not start implementation, rebuild an installer, change
Cloud objects or close any outstanding native acceptance gate.

## 2026 October 7 R1 implementation and parked handoff

The user authorized starting R1, then requested parking the work to close the
computer and disconnect the external SSD. All R1 changes are saved locally in
the integration checkout on `codex/installable-demo-stage3`, based on
`f65e2df28b1757bc0b37bfa4c99dfe0a6bb8c11c`. They are not yet committed or pushed.
Preserve the modified and untracked files; do not reset or clean this checkout.

Completed local work:

- Added [resolved Kit028 definition](../../workspace/releases/kit028-setup042.json),
  its [schema](../../workspace/releases/release.schema.json),
  [contract](../../contracts/release-reproduction/README.md) and
  [inventory](../development/release-reproduction-r1.md).
- Recorded 21 dependency nodes, ten exact source roles, five input groups,
  three explicitly unqualified reproduction profiles and original artifact
  identities. Application source and Factory tools remain separate pinned roles.
- Added read-only `scripts/validate-release-definition`, 41 offline tests and
  a CI definition gate; updated navigation and the existing R1 work packet.
- Verified all referenced recipe paths at their selected local Git revisions.
  Six small manifests from retained Kit028 match, including VM-to-host binding.
  The original media and payloads were neither copied nor rebuilt/rehashed.

Validation before parking:

- Full integration suite: **800 tests in 38.640 seconds, 799 passed and one
  skipped**. The runner completed and exited; no test process remains active.
- Dedicated R1 suite: 41 passed. Missing/changed inputs, profile errors, CI pin
  drift, cycles, provenance changes and access-boundary changes are rejected.
- Documentation gate: PASS, 333 Markdown documents, 662 stable identifiers,
  38 Mermaid diagrams. Whitespace and public-source checks passed, including
  new untracked R1 files.
- An additional whole-integration `reuse lint` audit did not pass: existing
  root licensing metadata lacks `LICENSES/MIT.txt`, and the repository's JSON
  comment convention is not parsed as SPDX by that tool. This is not an existing
  integration CI gate (REUSE runs on platform/service there). R1 JSON follows
  that same convention; do not claim whole-repository REUSE compliance or
  silently expand R1 into a repository-wide licensing rewrite.

R1 is **not fully closed**. Artifact hosting/access/retention and the proposed
future product version policy remain release-owner decisions. Effective
Factory41 configuration and heavy/native/container build-input closure remain
explicit gates; the old pinned template alone still contains older values.
No profile claims reproduction readiness. R2 build automation and R4 fresh
environment/native qualification have not been started by this work.

Resume from this checkpoint: inspect the preserved diff, finish the R1 review
and resolve those specific acquisition/closure decisions. Do not repeat large
artifact hashing, restart a demo, regenerate a kit or move an existing tag.
The component and private video repositories are unchanged. No simulator, VM,
Presenter, Docker Engine or container was started during R1; unrelated user
processes must be preserved when ejecting the SSD.

Parking completed: the normal eject was initially held by an idle Terminal
tab whose working directory was on the SSD. Its exact TTY was verified idle
with no child process, then its directory was changed to an internal workspace;
the tab and unrelated processes were preserved. Normal physical-disk eject
succeeded for both Work/Clean volumes. Presenter had no listener. No force
unmount, deletion or data cleanup was used. Reconnect the SSD before an optional
real-kit metadata recheck; the saved R1 code, documents and tests are internal.

## 2026 October 7 R1 resumed review and local verification

The user reconnected the external storage and authorized continuing R1. The
preserved checkout and retained Kit028 were reused without a new kit, image,
cache copy or payload rehash. Changes remain local on the existing integration
branch; no commit, push, tag or artifact publication was performed in this step.

The source review corrected the preliminary inventory: Brake/Tire services
and both backends are Apache-2.0 projects and already pin their container base
digests. Service builds also pin dated Debian repositories and native dependency
revisions. Those inputs are no longer described as missing. Acquisition,
redistribution review and fresh-build proof remain separate requirements.

The Factory gap is confirmed in both the pinned template and guest build
driver: they still select/check rootfs .11 and the older platform revision,
whereas the retained receipt identifies Factory .41. The effective generated
configuration and aligned driver belong in a new source revision during R2;
the historical tools commit and retained Factory were not modified.

Added optional `--source-workspace` verification to the existing definition
gate. It inspects local pinned Git objects, not the current branch or HEAD,
and never fetches, checks out or executes build recipes. Inherited Git
repository overrides, lazy fetching and terminal credential prompts are
disabled; failures do not echo raw Git responses.

Completed checks:

- Full integration suite: **807 tests in 39.245 seconds, 806 passed and one
  skipped**. The runner completed and exited.
- Dedicated R1 suite: **48 passed**, including missing objects, wrong tag/root,
  non-file recipes, Git environment isolation, timeout and error redaction.
- Actual local source inspection: **10 source roles, 28 unique recipe files
  and the original baseline tag target matched**.
- Existing Kit028 metadata: **six manifest identities matched**, including the
  application/input and VM/host bindings; payloads and runtime were not retested.
- Documentation gate: **PASS**, 333 Markdown documents, 662 stable identifiers
  and 38 Mermaid diagrams. Whitespace and public-source checks passed, including
  the new R1 files.

The delivery/version proposal is recorded in the
[R1 inventory](../development/release-reproduction-r1.md#selected-delivery-route):
public Git metadata, private S3 delivery to approved testers, and a proposed
next new candidate `1.2.0-rc.1`. The single existing DMG exceeds GitHub's
per-asset release limit. The release-owner choice was requested and remains
pending; no AWS account, bucket, budget or credentials are assumed. The current
definition stays unpublished with a null product version and download locator.

R1's inventory, specification and local gates are implemented. R1 overall
remains open only for its release-owner acquisition/version decisions; the
recorded build-input gaps feed R2 and reproduction proof belongs to R4. Do not
restart the inventory, alter old tags or treat this result as a clean build or
native E2E pass. No demo, VM, simulator, Docker Engine or UI was started. The
external disk remains connected for the resumed work; no eject was requested.

## 2026 October 7 Google Drive delivery decision

The release owner selected Google Drive in the existing Google Workspace
account instead of the earlier S3 proposal. The current R1 contract, inventory,
plan and candidate gate explanations now reflect that decision. Source and
release metadata remain in public Git; approved testers receive read/download
access to separate release files. Preserve supported release inputs and do not
overwrite published bytes. Actual file access and content must be verified
before a candidate is described as obtainable.

R1's remaining owner decision is the proposed product version and tag policy
(`1.2.0-rc.1`, then `1.2.0`; tags `sdv-lab-v<version>`). Acceptance of Google
Drive does not approve those numbers. Final reconciliation and Git handoff
follow the decision. Folder/account binding, authorized API setup and upload/
download verification are R2 implementation work, not new R1 prerequisites.
The source/build closure and native qualification gates retain their R2/R4
owners. No Drive resource, sharing permission, upload, credential, release tag
or old artifact was changed by this documentation update.

Decision-update validation passed: 48 targeted R1 tests in 0.179 seconds,
the resolved-definition gate, documentation checks (333 documents, 662 stable
identifiers, 38 Mermaid diagrams) and whitespace checks. The earlier 807-test
suite remains the code validation receipt; only decision text and explanatory
manifest fields changed in this step.

## 2026 October 7 R1 completion

The release owner accepted the remaining numbering decision: product versions
use `MAJOR.MINOR.PATCH`, candidate suffixes `-rc.N`, and tags
`sdv-lab-v<version>`. The next new candidate is `1.2.0-rc.1`; `1.2.0` is the
stable target after qualification. Google Drive in the existing Workspace
account is the selected delivery route. These decisions complete R1 together
with the resolved definition, dependency inventory, schema, validation script,
tests and CI gate.

The contract, inventory and plan now show R1 as complete. Historical Kit028
retains its null product version, source pins and artifact identities;
`demo-v1.1` and `candidate/kit028-setup042` are unchanged. No new product tag,
release binary, cloud resource or runtime qualification is created by this
source/documentation handoff. The existing integration branch is retained;
this completion does not merge it into `main` or modify component/video repos.

Next is R2 preparation/build automation, including actual Drive folder/API
binding and verified downloads. Effective Factory configuration and other
explicit source-input gaps stay with their R2 owners; fresh reproduction and
native acceptance remain R4. Do not restart R1's inventory or treat its closure
as a claim that the new product candidate has been built or qualified.

Final local validation for the R1 completion commit: 807 integration tests in
37.826 seconds (806 passed, one skipped); definition/source inspection passed
for ten roles, 28 recipe files and the baseline tag. Documentation checks passed
for 333 documents, 662 stable identifiers and 38 Mermaid diagrams; public-source
scanning included new files and passed. The test runner exited normally. No
demo, VM, simulator, Docker Engine or UI was started for this completion.

## 2026 October 8 R2 source and UI proof

The user authorized R2 on external SSD storage and requested a separate Google
Drive directory for artifacts. The private artifact root was created and its
unshared metadata verified; it remains empty. Private folder/account identifiers
are not recorded in public Git. Supported commands, proof and remaining gates
are in [R2 commands and evidence](../development/release-reproduction-r2.md).

Only the integration repository changed: a build-only `lab` entry point,
SSD-bound state/source preparation, a fixture-tested resumable Drive reader,
the existing UI owner adapter, tests and a CI planning gate. Seven developer
source roles were prepared at exact remote pins. Native Presenter, Driving
Control and web UI built successfully; repeats reused sources and outputs.
The retained workspace occupies about 300 MiB on the external volume, without
duplicating the retained kit.

Validation: 38 targeted tests passed; full suite 845 tests, 844 passed and one
skipped. This is source/UI proof, not complete R2, new installer qualification
or release publication. This checkpoint is local; no remote push is performed.
Existing tags, component repositories and video are unchanged. Runners exited;
no demo or shared Docker infrastructure was started or stopped.

Next: actual authorized Drive acquisition/binding and remaining component
adapters. Keep R2 in progress; do not repeat its completed source/UI proof or
treat the empty Drive folder as a released product.

## 2026 October 8 R2 Cloud and backend build proof

Continued the authorized R2 packet without changing the retained release pins.
The integration tooling now delegates to the existing owners for Cloud SDK
assembly, Brake and Tire backend Dockerfile builds, and backend OCI export.
Together with the earlier UI target, five targets have real first-build and
no-rebuild repeat proof. Sources, public wheel downloads, build caches,
temporary files and outputs use the bound external SSD. The reproduction
workspace occupies approximately 582 MiB, excluding the shared Docker disk.

The Cloud adapter derives only the manifest-bound isolated Python base from
the explicitly selected retained kit and verifies 41 public wheels. It does
not copy the whole kit, contact Cloud, enroll identities or install packages
into host Python. Backend adapters require an already-running local Engine
whose actual backing disk is on the same external volume. They build immutable
image IDs without running containers, replacing tags or publishing images.
The canonical export verifier accepted the 82,129,920-byte archive. Exact
fingerprints and scope are in the [R2 evidence](../development/release-reproduction-r2.md).

The user separately authorized shared Docker storage relocation. A stopped
sparse copy was compared against the entire original logical disk, restored
at the location selected by Docker's settings, and reconciled against all
22 prior images, five containers, three volumes and 314 cache records. Only
the verified internal duplicate and empty migration intermediate were removed;
approximately 15 GiB was released internally. This host-maintenance operation
does not become part of R2 build lifecycle. Docker now requires the SSD; stop
it and verify released handles before a separately requested SSD disconnect.
Ordinary end-of-test cleanup must still preserve the shared Engine and
unrelated running workloads.

Validation: 59 targeted reproduction tests passed. The complete integration
suite ran 866 tests in 82.275 seconds: 865 passed and one skipped. No new demo
container, VM, simulator, Presenter or Setup was launched. Build/test runners
exited and Docker Dashboard was closed; the shared Engine remains running.
Documentation checks passed for 334 Markdown documents, 662 stable identifiers
and 38 Mermaid diagrams; whitespace and public-source checks, including new
adapter files, also passed.
Cloud, Production, existing tags, component sources and private video are
unchanged. This is a local source checkpoint, not a remote push, new installer,
release publication or runtime qualification.

R2 remains in progress. Continue with authenticated Drive input binding and
the remaining component adapters. Gateway/native SDK, VDP/service product
recipes, full package assembly and effective Factory/full-source input closure
remain required; R3 reader-facing documentation and R4 fresh reproduction/native
acceptance are separate. Reuse the verified five-target outputs and shared
caches rather than repeating builds or copying the retained kit.

## 2026 October 8 R2 service and Gateway build proof

Added the pinned owner adapters for Brake V1/V2/V3, Tire V1 and Gateway.
All four service exports passed the existing product and test validators
(eight tests per Brake profile, five for Tire); repeat commands reused the
verified exports. Gateway compiled with an explicit hash-bound prebuilt SDK
on SSD. Two test-environment assumptions caused four initial failures: the
Unix socket path limit and LibCarla's cache initializer in a scrubbed
environment. A short same-SSD temporary directory and explicit CARLA cache
made the four tests pass without changing or rebuilding Gateway binaries.
The corrected adapter resumed the warm build; all 30 owner tests passed,
and the repeat reused the result. First failure logs are preserved on SSD.

The connected Google Drive tool uploaded and read back a 126-byte synthetic
text probe in the private artifact root, with identical text and unshared
metadata. This is not CLI OAuth, binary delivery, large-file integrity proof
or redistribution approval. No source-public folder/file identifiers or
credentials were added. No release binary was uploaded.

Validation: 78 reproduction tests passed; full integration regression ran
885 tests in 54.515 seconds (884 passed, one skipped). Eight target types now
have ten build receipts. All new build payloads, temporary data and caches
use external storage; the workspace is approximately 1.0 GiB excluding the
shared Docker disk. No CARLA/Unreal/Factory rebuild or duplicate kit was made.
The external volume has approximately 269 GiB free; internal free space is
approximately 130 GiB. Detailed keys and commands are in the
[R2 evidence](../development/release-reproduction-r2.md).

R2 remains in progress. The next packaging gate is the preparation owner's
historical Stage 0 service inventory, which does not match the selected
current service source revisions. Reconcile that owner through a new reviewed
recipe/input record and candidate definition; preserve historical manifests,
pins and source checkouts. VDP/preparation, native relocation, complete-package
assembly, authenticated Drive delivery and effective full-source closure
remain open. This local checkpoint changes only integration tooling and docs;
it does not publish a product, tag, installer or Cloud update.

## 2026 October 8 R2 preparation owner correction

Corrected the build-only vehicle-input producer to accept an explicit reviewed
service checkpoint, following the existing explicit Factory-checkpoint model.
The new checkpoint selects the four verified R2 service products. The default
historical inventory and old portable manifest lock are unchanged. Explicit
choices fail closed on invalid schema/identity, missing or duplicate profiles,
mixed Brake revisions, unsafe paths, links and executable digest mismatch.
The product reader and Factory/VDP checks remain authoritative; no runtime,
signing, credential or Cloud interface changed.

All four real exports passed the canonical input reader with 46 files each.
The temporary APFS clones on SSD were removed; no Factory or complete kit was
copied. This is partial input composition proof, not complete-package assembly.
The new producer source/checkpoint still must be frozen in the future candidate
definition; the pinned historical checkout was not patched.

Validation: 25 vehicle-input tests passed; full regression 892 tests in
45.571 seconds, 891 passed and one skipped. The historical release definition
still passes, and status verified all ten retained R2 build results.
Build/test runners exited; no demo, VM, simulator or new runtime container
remains. The shared Docker Engine was not stopped. The Google Drive CLI access
gate remains open: connected-tool upload/readback is proven, but a CLI
credential setup was not available and no account/token was created or extracted.

Next: select the corrected producer in the future candidate and complete
VDP/preparation and native/application packaging adapters. Keep actual Drive
CLI acquisition, full-source closure and R4 qualification separately gated.
Preserve the current warm results; do not restart completed builds to resume.

## 2026 October 8 R2 successor packaging and media proof

Continued the accepted external-SSD build packet through preparation, portable
host closure, backend/VM inputs, complete application, stable-signed Setup and
DMG. Canonical owners and strict validators remain authoritative. Two separate
source-reviewed successor checkpoints bind group manifests and the application
digest. Historical Kit028/Setup042 locks, Factory .41, component pins and tags
were not overwritten. These are new local engineering outputs, not promotion
of the historical media or a qualified release.

The preparation run fetched one exact reviewed VDP history object, preserving
the source HEAD. Host corrections addressed nested sandbox execution and
incidental Finder metadata in blanket copies, not runtime behavior. All four
native help/version probes passed with network and Homebrew reads denied.
Setup's compiler temporary directory now follows the selected SSD. Its native
self-test, embedded bootstrap protocol and Apple Development signature passed.
Signing keys were not exported or added to evidence.

Complete media: `AosEdge-SDV-Lab-1.2.0-rc.1.dmg`, 14,162,125,968 bytes,
SHA-256 `7bac892b2398e38fe511de738838c23dd02e5ec26d2578afd3f6f932868cc755`.
First builds and immediate no-rebuild repeats passed. The archive was verified;
its read-only mount passed canonical inventory and Setup signature/pin checks,
then detached normally. No Setup window, demo, simulator, guest or new container
was launched. No Cloud state, Production or video repository changed; the
shared Docker Engine remains running. Two unreferenced failed host copies and
the completed root-only test export were removed, preserving compact evidence,
successful outputs and historical inputs.

Validation: 932 integration tests, 931 passing and one skipped; all 109
reproduction tests also passed in a separate root-only Git export. A dedicated
CI job now exercises the same resolver and offline fixtures, with no native or
remote-CI success claim. Documentation, historical release-definition and
public-source gates passed. Build keys and precise scope are in the
[R2 evidence record](../development/release-reproduction-r2.md).

Source changes are committed locally on the existing integration branch:
preparation/host implementations through `ecb3894`, successor owner bindings
`15c75ad` and `f13a186`, media adapters `2597959`, independent Setup pin and
compiler scratch fix `ad6b338`, root-only CI `7ac3c85`. No new tag, push or
binary upload was performed by this block.

R2 remains in progress. Next: complete the single-command dependency chain
with exact producer-role selection, narrow invalidation and shared-cache/space
accounting; qualify authenticated Drive input delivery and close full-source
prerequisites. R3 human-facing instructions and R4 fresh/native installation
remain separate. The signed DMG alone does not close those criteria.

## 2026 October 8 R2 ordered developer chain

Implemented `lab build --target all` at `1f95e9d`, retaining exact source owners,
canonical adapters and independent successor input/Setup pins. A source-reviewed
17-step plan prepares five immutable build-tool checkouts on external storage.
The existing workspace lock covers worker invocations. Exact dependency views
exclude unrelated old candidate/signing results without deleting them; owner
saves cannot change source/artifact/storage bindings or existing receipts.

Two real whole-chain runs passed, reusing the same 17 verified outputs. The
repeat took 80.09 seconds, with no compilation, signing, recompression, runtime
launch, Cloud change or upload. The output remains the earlier engineering
`1.2.0-rc.1` DMG, not a new or qualified release. Historical media and the video
repository are unchanged. Tests at this checkpoint: 946 integration tests,
945 passing and one skipped; 123 reproduction fixtures passed again in a
separate root-only source export. The temporary export was removed; retained
producer inputs occupy approximately 306 MiB on the SSD. Shared Docker and
unrelated containers remain untouched.

Follow-up hardening rejects malformed worker completion records and retains
the first failure log through a subsequent successful continuation. No artifact
or trust pin changes. Precise evidence and outstanding R2 criteria are in the
[R2 record](../development/release-reproduction-r2.md#ordered-chain-proof-on-october-8).
Narrow recipe invalidation, shared-cache/capacity accounting, authenticated
artifact delivery and full-source closure remain open; R3/R4 are not closed by
warm-chain success. No push, release tag or binary publication in this block.

## 2026 October 8 R2 cache reuse and capacity reporting

Added `lab cache --cache-from` and read-only `lab space` inside the accepted
build-only packet. Only release-declared complete digest objects and wheels
from the selected exact source lock are eligible. Both workspaces use the same
external volume. Direct APFS `clonefile` shares data without mutable hardlinks,
overwrites or full-copy fallback. A transfer verifies SHA-256 before promotion;
the donor is not modified and no source/build/qualification receipts are adopted.

Real proof: 41 wheel objects, 24,581,670 logical bytes, zero network bytes.
The repeat imported zero objects and reused all 41; the frozen `ad6b338` owner
accepted them. The two absent historical DMG/Factory cache entries remained
explicit rather than triggering unnecessary copies of their retained inputs.
The disposable receiver was removed after a no-open-handle/dependency check.
Original caches, accepted artifacts, Factory, runtime and video are unchanged.

The workspace report took 3.53 seconds. It distinguishes logical sizes, file
block counts, cache availability and recipe guards. The 166 GiB largest-step
guard and 285 GiB reservation sum are not cold-build peaks or claims about
unique APFS allocation. Actual cold peak, shared Docker growth and full-source
capacity remain open. Full regression: 968 tests, 967 passed and one skipped;
documentation, historical-definition and public-source gates passed.

Next R2 work remains narrow recipe invalidation, measured cold capacity,
authenticated artifact delivery and full-source closure. These cache/reporting
results do not close R3/R4 or promote the candidate. No push, tag or upload.

## 2026 October 8 R2 packaging recipe dependencies

Replaced the current direct packaging adapters' shared whole-directory identity
with target-specific source-file closures. Static import selection includes
deferred imports and package initializers without executing code. Exported data,
Python modules, native Setup source and shared validation helpers remain explicit
inputs with blob and executable-mode identities. Added the previously omitted
VM DNS helper, application configuration and repository manifest dependencies.

Eight targeted fixtures passed, including real committed changes in a disposable
SSD Git repository: README changes affect no recipe, native Setup affects Setup,
VM DNS affects VM inputs, and the shared native validator affects all seven
packaging targets. Existing upstream result keys propagate output changes.
Owner constants have drift tests for copied data and shipped helper files.
Full regression: 976 tests, 975 passed and one skipped; documentation and
historical release-definition checks passed.

The frozen 17-step producer plan, old receipts, accepted DMG, Factory and caches
are unchanged. No native rebuild, signing, runtime start or publication occurred.
New producer adoption still needs source-reviewed independent manifest pins.
Remaining R2 gates are authenticated artifact delivery, measured cold capacity
and full-source input closure; R3/R4 remain separate.

## 2026 October 8 Private Drive delivery

The user selected delivery before discussing cold builds and separately approved
Google CLI authorization. Added the explicit maintainer transport and a reviewed
descriptor for the existing `1.2.0-rc.1` DMG. The root `lab` build commands do not
publish artifacts or acquire credentials. Historical Kit028 and build receipts
remain unchanged; component and video repositories were not modified.

The complete 14.16 GB DMG passed private upload metadata/SHA-256 verification,
full independent download and digest verification, controlled 32 MiB download
interruption/range resume, no-duplicate upload repeat and cached download repeat.
A private release index binds source revision, build provenance and object IDs;
its bytes were read back and verified. No sharing permissions were expanded.
The disposable downloaded copy was removed, preserving source, original media,
Drive contents and compact receipts. No demo runtime was started.

Tooling checkpoint: local commit `de109aa`. Tests: 12 targeted transport fixtures;
988 integration tests with 987 passes and one skip. Documentation, historical
definition and public-source checks passed. See the
[delivery evidence](../development/release-reproduction-r2.md#private-drive-delivery-proof-on-october-8).
No push, tag, cold build, public distribution or completed R2/R4 claim.

Next discussion: distinguish a fresh developer build with declared prebuilt
heavy dependencies from a full-source CARLA/Factory/native build, then select
the exact cold-build inputs and capacity proof. The verified DMG route does not
by itself supply or qualify all build prerequisites or another user's access.

## 2026 October 8 Reusable CARLA dependency delivery

At the owner's request, preserved the existing standalone simulation as
`carla-macos-arm64-r1`, independently of demo release media. Three private
archives contain CARLA/Python, native host support and the pinned Gateway SDK.
The [Git lock and usage route](../development/reusable-simulation-inputs.md)
preserve byte identities, source correspondence and existing manifest ancestry.
New `lab dependencies` commands export, explicitly publish, acquire and verify
them; no engine build, live demo or cold build is started implicitly.

All 13.36 GB passed private Drive upload and independent full download. All
31,477 extracted files passed content/mode checks. Upload repeats reused the
same IDs; local preparation repeated with network denied and no Google CLI or
account. The frozen `ecb3894` consumer accepted the inputs. Four native probes,
Python 3.12.14/CARLA import with the declared SSD cache, and deep/strict simulator
signature verification passed. The bounded HTTP 403/reconciliation event and
initial missing-cache diagnostic mistake are recorded in the
[R2 evidence](../development/release-reproduction-r2.md#reusable-simulation-dependencies-on-october-8).

Tooling checkpoint `8b7b245`: 1,008 local tests (1,007 passed, one skipped),
185 passing reproduction fixtures from a root-only source export, documentation,
historical definition and public-source gates. Temporary source-test files and
the three duplicate publication archives were removed after open-handle and
recovery checks. Verified SSD cache/working inputs, private Drive files, original
kit, Factory, accepted DMG, receipts and video remain intact. No runtime process,
VM or demo container was started; shared Docker was not changed.

This closes the reusable simulation input delivery step, not full R2/R4 or
public distribution. No source push, tag, signing or permission expansion.
Next: discuss a clean developer build that reuses these declared dependencies,
separately from a full-source engine/Factory rebuild.

## 2026 October 10 Anonymous preparation reader implementation

The owner approved implementing the tested anonymous Drive reader, with the
actual first-use walkthrough to follow together. Changes are confined to the
entry repository on `main`, based on `ffebae05165a57c7e69c044991158de0230e4e3e`.
No component, video, frozen artifact, Factory, account or Drive permission was
changed during implementation. This is an uncommitted local source checkpoint,
not a published release or completed user walkthrough.

Preparation v3 defaults to a source-pinned public catalog, without Google CLI
discovery/installation, account questions or OAuth. The standard-library
anonymous transport handles bounded same-file redirects, the expected large-
file confirmation, one-byte availability probes and sanitized failures. Public
schema-2 input selections flow into both dependency consumers; complete archive
hashes, safe extraction, existing cache receipts and range-resume checks remain
authoritative. Explicit `--private-inputs` preserves the authenticated route;
there is no implicit fallback. The offline catalog generator can create a
distinct public record from reviewed links without publishing anything.

Evidence: 205 targeted offline fixtures passed across transport, catalog,
wizard, both input consumers, existing private delivery/reproduction and reader
navigation. This includes real small fixture downloads/extraction through the
consumer with mocked HTTP, interruption/resume, cached no-network repeat,
wrong bytes/ranges, HTML/access/quota failure, no credential lookup and state
preservation. One pre-existing test expected the obsolete wording "selected
external"; only that assertion was updated to the accepted "selected volume"
message, retaining the cross-volume rejection check. Documentation quality,
standalone embedding parity, Bash syntax and tracked/new public-source scans
passed. No real installation, product build, large transfer or demo launch ran.

The preceding disposable Drive proof verified anonymous 1 MiB full/range
downloads, 128 MiB bounded range reads after the normal large-file confirmation,
stable index update and read-only sharing. Its public permission was revoked;
synthetic Drive files were trashed and local payloads removed. This proves a
transport mechanism, not the availability/licensing of real 13–14 GB archives.

Public activation remains deliberately unset in `PUBLIC_PIN`: the real inputs
are still private. A release-owner content/redistribution review, separate
read-only public publication and source review of its stable catalog URL/record
pin are needed before the joint ordinary-user walkthrough. Until activation,
the default wizard exits before storage prompts/installations and explains the
publication gap without asking the user for credentials or JSON paths. Existing
private catalog state and the explicit maintainer route remain available.

No commit, push, tag, runtime process, test VM or demo container was created.
Fixture directories/processes were cleaned by their test owners; shared Docker
and working caches were not changed.
