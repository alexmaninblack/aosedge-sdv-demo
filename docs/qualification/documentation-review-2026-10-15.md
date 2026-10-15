<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# README-linked documentation review — 15 October 2026

- Status: content reconciliation and retirement implemented; validation recorded below
- Prepared: 2026-10-15
- Owner: SDV Lab integration
- Change class: editorial/status reconciliation; no runtime or normative behavior change
- Baseline source: `84056efdf73c518d14929d66a772673212e8a2d9`

## Scope and method

The root README's complete recursive local Markdown graph contained **364
reachable documents**, within **365 scanned documents**. The unlinked file was
the repository's agent instruction file, not a user guide. The audit covered
navigation/indexes, actual selected release/producer records, Setup/Presenter
and CLI source, current qualification receipts, architecture/requirements
status, contract amendment precedence and incoming links in declared siblings.

External upstream documentation is not project-owned and was not rewritten or
deleted. Published revision-pinned references remain historical source
references; they do not imply the selected release uses that same component
revision. Network availability is a separate observation, not proof of the
upstream document's correctness or ongoing accessibility.

## Corrections

- Current entry pages now select the release through the catalog rather than
  Kit028, Factory39 or an old review branch.
- Production/Staging Cloud environments are distinguished from Test/Production
  vehicle roles; existing and newly issued certificates are separate paths.
- Current Setup issuance for existing accounts, public delivery and API/UI
  profiles are no longer falsely marked pending or merged into one proof.
- Source inspection confirmed **Start controller** and **Stop demo and keep
  data**. Guides that incorrectly claimed no retained-controller UI start were
  corrected. Ordinary tested Stop/Start is not host sleep/wake or all recovery.
- Factory means the clean Linux/AosEdge ARM64 controller image; Builder is a
  separate build VM. Normal B reuses these heavy inputs; C prepares tools only.
- Architecture and all component packages point to one current as-built/proof
  map, preserving stable obligations and explicit gaps.
- Closed plans and embedded prototype progress logs were consolidated into
  current references, not kept as competing instructions.
- Repository-boundary prose no longer calls accepted HLA 1.8 a proposal under
  HLA 1.4; the first-demo single-SP scope and documented KUKSA patches are explicit.
- Legacy executable-contract discrepancies remain explicit; no profile hash,
  protocol, quota, algorithm, security rule or acceptance gate was rewritten.

## Retirement and recovery

**212 documents** were retired from the working tree in the initial cleanup;
the obsolete UX discussion proposal was then also retired, for **213 total**.
This includes earlier checkpoint reports, closed implementation/migration
packets, superseded research/inventories, two superseded ADRs and obsolete user
journeys. Their exact paths, content hashes and reasons are in the
[retirement inventory](../../workspace/checkpoints/documentation-retirement-20261015.json).

Original content remains recoverable at the published baseline commit;
historical citations use immutable Git URLs. No new archive directory, copied
history or duplicate artifact collection was created. Active inbound sibling
links were repaired as part of the same documentation change.

Three historical Markdown files remain because the unchanged predecessor
release definition requires their paths: the R1 inventory, Kit028 M1 journey
and Kit028 source publication. They are labelled historical dependencies,
not current instructions. Accepted ADR rationale, stable requirement/contract
definitions, unfulfilled calibration/sleep-wake obligations and HTML/artwork
used by active regression tests are not disposable merely because they are old.

## Validation and exclusions

| Check | Result |
| --- | --- |
| Full documentation gate | PASS: 153 Markdown documents, 662 stable identifiers, 36 Mermaid diagrams |
| Recursive README reachability | PASS: 152 reachable documents; only the agent-instruction file is outside user navigation |
| Initial reader routes | PASS: 10 root-only entry documents, no sibling clone prerequisite |
| Frozen release definition | PASS: unchanged predecessor, 3 profiles and 21 components |
| Retirement integrity | PASS: all 213 original Git blobs/hash matches, absent working paths, 3 required historical dependencies retained |
| Offline regression suites | PASS: 19 documentation-check, 9 reader-route and 48 release-definition tests |
| Whitespace/source boundaries | PASS: documentation-only changes; no tracked runtime source or release lock changed |

Seventy non-recovery external destinations were probed with bounded HEAD
requests. Sixty-seven responded successfully. Google Help returned misleading
404 to HEAD but 200 to bounded GET without a body read; its unsupported hosting
recommendation was replaced by the verified official troubleshooting reference.
The genuinely missing staging frontend JavaScript chunk returned 404 to both
methods and was replaced by an immutable observation citation. The
[Unreal EULA](https://www.unrealengine.com/eula/unreal) denied CLI probes with
403 but was readable through the official web page; it was not deleted or
replaced with an older agreement. No access restriction was bypassed.
Git recovery references were verified against the already published baseline
objects instead of repeatedly downloading each historical document.

No build, signing, DMG assembly, installation, live demo, Cloud mutation or
payload transfer is part of this documentation-only work.
The [current baseline](current-baseline.md) retains release exclusions;
documentation cleanup does not qualify a new product.

## Follow-up: separate user guidance from internal status

The operator identified an incomplete part of the initial review: the Setup
guide still contained **What is still being qualified**, and several user
routes repeated campaign history or internal acceptance exclusions. The
follow-up reviewed the documentation by audience, not just by link validity
or document age.

- Removed that section and embedded test counts, older kit/release examples,
  dated campaign claims, internal deferred-defect references and backlog links
  from getting-started and operator instructions.
- Replaced the developer guide's historical manual candidate walkthrough with
  the current automatic route B, its results and continuation steps.
- Moved private-input/catalog maintenance to the existing development reference.
  The documentation map explicitly separates engineering records and plans.
- Kept user-impacting restrictions: Apple Development signing/notarization,
  Docker and Cloud prerequisites, space checks, limited route C tooling scope,
  Safe Stop, retained-Test operations and safe shutdown/storage handling.
- Corrected stale troubleshooting advice: public inputs need no Google login
  or manual bindings, and a local internal Docker disk is not itself a failure.
- Removed stale installed-step counts and branch-era prose from the Presenter
  component README. Current test results remain in their canonical baseline.

The documentation policy now defines this audience boundary. Both the full
gate and reader-route gate reject known internal-status sections/narratives
and direct test/backlog links in user guides, including Git-hosted copies.
New getting-started pages are checked without a new allowlist entry. Tests
also require practical restrictions and separate engineering reports to remain
allowed; the policy is not a blanket ban on documenting limitations.

Follow-up validation: **153 Markdown documents, 662 stable identifiers,
36 Mermaid diagrams and 14 root-only reader routes** pass. All **80 offline
regression tests** pass: 19 documentation-check, 13 reader-route and
48 release-definition tests. The frozen release definition remains valid.
No runtime source, launcher behavior, release lock, artifact, test result or
acceptance status was changed. No build or live demo was started.

## Follow-up: source-tree retirement and current developer selection

The automatic Dropbox publisher was integrated into main at
`3804cfbff4d3ca3f3825bfd67d20667e894a594a`. The same checkpoint corrects the
capacity review's rejection of the independently pinned current r7 producer
plan. Publisher verification used offline fixtures, not a live upload.

The next cleanup retires **36 integration files** and **11 platform historical
documents**. The separate `sourceCleanup` section in the existing retirement
inventory records their published baselines and content hashes. It does not
rebind the earlier documentation inventory to a different source checkpoint.
Superseded build plans, old bootstrap-only validators and their own tests,
orphan mockups, duplicate upstream review patches and obsolete checkpoints are
not current build dependencies. Six component README files retain their
first-use commands and current technical references instead of dated diaries.

Current tooling requires the source-owned developer selector rather than
silently choosing a removed plan. Capacity review retains the frozen base and
source-Factory definitions plus the validated current selection. Selected
option A, r7, all five public input source files, Factory configuration
inheritance and locked namespace files remain unchanged. No product runtime,
protocol, security policy, release allocation or packaged artifact is changed.

Validation before source publication:

- Full integration unit discovery: **1,335 tests**, one platform-dependent
  skip. The process-cancellation fixture requires host process-list access;
  its isolated rerun with that access passed after the sandbox denied `pgrep`.
- Documentation: **155 Markdown documents, 662 stable identifiers and 36
  Mermaid diagrams** pass, now including test/component reference READMEs.
  A negative regression rejects broken links in the upstream fixture README.
- Platform and Brake source-policy gates, component README local references,
  launcher/helper pins, confidential-input guard and frozen release definition
  pass. All 47 additional retirement hashes match their original Git blobs.
- No build, signing, DMG assembly, installation, simulator, Docker or Cloud
  operation was run. Fresh-clone checks and local-data relocation are separate
  maintenance operations, not new live-product acceptance.

## Follow-up: ignored history is not source isolation

Fresh main clones passed the source gates, but copying ignored local trees back
also restored obsolete artifacts, trial scripts and run records. That migration
was not proof of a history-free working environment. The operating policy now
requires selective preservation rather than wholesale ignored-tree restoration.

The additional source retirement removes the closed original-Test CM comparison
host adapter/CLI and eight superseded Factory configurations. The existing
inventory's `localHistoryFollowup` records their published Git baselines and
hashes. Guest fail-closed decoding, retained-journal handling and redaction tests
remain. Factory .31/.33 helper inputs and .39/.40/.41 inheritance are retained;
neither frozen source pins nor the selected packaged artifact is rewritten.

The qualification guide now documents the current M1 campaign entries instead
of dated pilot walkthroughs and development-Mac live browser instructions.
Gateway's roadmap describes current scope and remaining boundaries instead of
the completed M0-M6 diary. Old evidence citations in the still-used Factory39
checkpoint resolve to immutable Git, not absent local files.

Validation: **1,335 integration unit tests** (one skip), **116 affected
orchestrator fixtures**, and **233 platform tests** (two skips) pass. Reader
routes, documentation, source policy, pinned helper/catalog inputs and the
frozen release definition pass. These are source-only checks; no build,
installation, signing, simulator, VM, Docker or Cloud operation was run.

Explicit maintenance refreshes the prepared root-source selection separately
from old completed workflow/media receipts. It retains input/build/tool caches
and does not claim that an existing DMG was rebuilt from the new source commit.
Private local-retirement and source-refresh results are retained in the SSD's
maintenance records; they are not public release acceptance.
