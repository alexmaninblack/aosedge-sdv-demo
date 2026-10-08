<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross Repository Change Journal

This maintainer journal records coordinated changes to the SDV Lab repositories.
The [distribution plan](active/installable-distribution-and-reproducibility.md)
controls delivery order; the [current baseline](../qualification/current-baseline.md)
identifies the implemented candidate. Component source, contracts and release
locks remain authoritative. This journal links them and does not duplicate them.

The latest [publication checkpoint](#2026-october-7-documentation-publication)
records the committed and remotely verified documentation baseline. Earlier
local-only entries below retain their original checkpoint state.

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
