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
