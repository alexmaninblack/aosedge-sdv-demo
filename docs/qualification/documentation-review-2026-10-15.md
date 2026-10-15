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
