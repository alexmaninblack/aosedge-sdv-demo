<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Documentation and Requirements Management

- Status: Accepted
- Version: 1.0
- Prepared: 2026-08-18
- Owner: System Architecture

## Purpose

This policy keeps the demonstration readable for people and traceable for
engineering as architecture, scenarios, requirements and implementation
evolve. Markdown remains the source of truth; no parallel requirements
database is introduced at the current project scale.

## Canonical Information Chain

| Information | Canonical owner |
| --- | --- |
| System boundaries, authorities and invariants | High-Level Architecture |
| Audience-visible lifecycle and proof | Demo Scenario |
| Runtime, lifecycle, observability and failure sequences | Architecture Flows |
| Cross-component normative obligations | System Requirements |
| Components, interfaces, lifecycle ownership and allocation | Component and Interface Register |
| Derived component obligations | The relevant Component Requirement package |
| Implemented and qualified state | Current Baseline and accepted evidence |

A downstream document may summarize an upstream decision, but it must link to
the canonical definition and must not reproduce a second normative copy.

## Human-Readable References

A cross-document identifier in reader-facing content must include a short
name and a direct link to its canonical definition:

```text
Exact source-to-Unit binding (SYS-SRC-001)
```

An unexplained `SYS-*`, `CMP-*`, `IF-*`, `AF-*`, `GAP-*`, `CR-*`, `REQ-*` or
`UT-*` token is allowed only in a definition table, detailed traceability
appendix, test or machine-readable report. Inclusive identifier ranges are
prohibited in the reader view because they hide the obligations they
represent.

Reader-view tables explain purpose, ownership and behavior. Detailed
traceability is kept in a separate section of the same document.

## Stable Paths, Versions and Identifiers

- A canonical document keeps one stable path. Its version changes in document
  metadata, not in the filename.
- Every stable engineering identifier has a permanent lowercase HTML anchor.
- An identifier is never reused for a different concept.
- Component requirements use `REQ-<PACKAGE>-NNN`; stable isolated unit-test
  obligations use `UT-<PACKAGE>-NNN`. Implementation-specific test names may
  change while their accepted obligation mapping remains stable.
- Editorial clarification that preserves semantics keeps the identifier.
- A material semantic replacement receives a new identifier. The old entry is
  marked `RETIRED`, records the replacement and remains resolvable while any
  accepted evidence refers to it.
- Git history and accepted checkpoint commits preserve prior document
  versions. Active directories do not retain parallel `old`, `final`, backup
  or version-suffixed copies.

## Canonical Document Metadata

Current design-chain documents carry, as applicable:

```text
Status: Draft | Review candidate | Accepted | Superseded
Version: major.minor
Prepared: YYYY-MM-DD
Owner: accountable architecture or product owner
Architecture input: linked HLA version
Scenario input: linked scenario version
Flow input: linked flow version
Accepted architecture changes: linked ADR identifiers
```

An input version describes the baseline actually used by the document. A
version mismatch is an explicit review condition, not an implicit assumption.

## Change Classification

| Level | Change | Required cascade |
| --- | --- | --- |
| `A` | Presentation order, wording or dashboard layout without behavior change | Scenario or presentation material only |
| `B` | New behavior using accepted boundaries, components and interfaces | Scenario, Flows, Requirements and affected packages |
| `C` | New or changed authority, trust boundary, component, interface, lifecycle or data direction | HLA followed by every affected downstream document |

The author records the classification before changing a canonical baseline.
The impact set is derived from direct references and the canonical chain; an
unaffected downstream document is not version-bumped merely because another
document changed. It is still reviewed against the new upstream baseline and
its input metadata advances to that baseline. This records that the document
was revalidated without falsely claiming a semantic revision.

### As-built discoveries

Implementation review can expose behavior that is useful and tested but has no
accepted parent requirement. That behavior is marked `UNALLOCATED` while the
team makes one explicit decision:

1. **adopt** it by adding a measurable parent requirement and allocating it to
   the affected packages;
2. **constrain** it to the narrower behavior actually intended by the accepted
   baseline; or
3. **remove** it when it is accidental, unsafe or outside scope.

An unallocated behavior cannot be silently accepted merely because code and
tests already exist. A corrective requirement version may be used when the
accepted HLA, scenario and flows already require the behavior and no authority,
boundary, lifecycle or data direction changes. The correction records its
source, updates every affected package and revalidates unaffected canonical
documents without artificial semantic version bumps.

### Change impact record

Every normative change records the following compact review block in the
commit, pull request or working review note. The block is evidence for the
cascade; it is not a new permanent design document.

```text
Change: <one-sentence behavior or baseline correction>
Class: <A, B, C, or corrective baseline>
Owning source: <canonical document and stable ID>
Affected: <documents, packages, contracts and tests changed>
Revalidated: <canonical documents checked with no semantic change>
Retired: <obsolete IDs/files, or none>
Evidence: <checks and review results>
```

The same stable requirement ID is retained for a wording clarification that
does not change observable behavior. A changed obligation receives a new
version of its owning document; a removed obligation remains resolvable through
an explicit retirement mapping rather than disappearing from active links.

## Architecture Change Workflow

Level-C work starts as one Architecture Decision Record with status
`Proposed`. The record states the problem, audience scenario, proposed
boundary change, security and lifecycle consequences, affected documents and
open decisions. The same record becomes `Accepted` or `Rejected`; a separate
proposal document is not created.

An accepted Level-C change is implemented on a short-lived architecture
branch. `main` retains the previous internally consistent baseline until the
complete affected cascade passes review and `docs-check`. The stable canonical
paths are updated together when the branch is merged.

The checker compares every canonical input-link label with the version in its
target document. An HLA version change therefore exposes every stale
downstream input declaration immediately. The reviewer either updates the
affected content and its version or records a no-impact revalidation by
advancing only the input metadata.

## Quality Gate

Run the deterministic local gate with:

```sh
./scripts/docs-check
```

It validates local files and anchors, identifier definitions and references,
requirement allocation, interface rows, canonical metadata, documentation-map
reachability, Mermaid fence/compatibility rules, SPDX headers, stale paths and
personal absolute paths. It does not mutate documents or external systems.

External HTTP links are intentionally separated from the commit gate:

```sh
./scripts/docs-check --external
```

Network failures must not make the deterministic repository gate flaky.

### Component verification policy

The reusable
[component requirement package template](../requirements/components/template.md)
separates unit, component, contract, integration and end-to-end verification.
D3 states which levels and stable unit-test obligations are required. D4
freezes executable contracts, cases, fixtures, suites and evidence locations.

Owned executable decisions, transformations, validators and state transitions
require deterministic unit-test obligations. Those tests isolate external
systems and do not start Unreal Engine, CARLA, QEMU, AosCloud or a real KUKSA
Databroker. An unchanged external executable or a no-code package may record a
reasoned unit-test exception and prove its obligation at another verification
level. Neither an integration test nor a code-coverage percentage silently
replaces required isolated behavioral proof.

### Workspace and external link policy

- Links to files owned by a repository declared in
  [`workspace/repositories.json`](../../workspace/repositories.json) use a
  relative filesystem path to that sibling checkout. The local gate verifies
  that the checkout and target exist and rejects a GitHub web link to the same
  owned repository.
- HTTPS links remain appropriate for genuine external or upstream sources
  that are not part of the workspace contract.
- A repository clone URL in an installation procedure remains HTTPS because
  its purpose is to create the checkout before local links can work.

Cross-repository links assume the accepted sibling workspace layout. A reader
using Obsidian or a similar knowledge-base application should open the
workspace parent directory as the vault so those links remain navigable.

## Review and Retirement

Before accepting a documentation change:

1. update the owning source first;
2. update only the impacted downstream summaries and traceability;
3. run `docs-check` and the repository tests;
4. inspect the reader view, not only the source diff;
5. remove superseded drafts, generated duplicates, backups and obsolete local
   artifacts after proving that no active link or launcher depends on them;
6. retain historical rationale in ADRs, accepted evidence and Git history,
   not in competing active documents.

Documentation acceptance never authorizes a build, signature, Cloud mutation,
assignment, VM reset, provisioning, deprovisioning or deletion.
