<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross Repository Change Journal

This maintainer journal records coordinated changes to the SDV Lab repositories.
The [distribution plan](active/installable-distribution-and-reproducibility.md)
controls delivery order; the [current baseline](../qualification/current-baseline.md)
identifies the implemented candidate. Component source, contracts and release
locks remain authoritative. This journal links them and does not duplicate them.

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
