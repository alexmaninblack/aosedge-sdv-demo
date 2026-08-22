<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# KUKSA JWT Current-Release Architecture and Delivery Change Plan

- Status: Active — execution approved
- Updated: 2026-08-22
- Change class: C — authority, trust boundary, component ownership and interfaces
- Protected baseline: Git commit `5542b47`, pushed to `origin/main`
- Working branch: `codex/kuksa-jwt-doc-cascade`
- Proposed authority: [ADR 0013](../../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md)
- Cloud or Unit mutation authorized: no
- Source implementation or image build authorized: no

## Purpose and Lifetime

This active plan controls promotion of the accepted KUKSA security direction
from local brainstorming into one internally consistent formal baseline and,
after a separate technical review, into implementation on the current AosCore
release.

The plan is intentionally temporary. It remains tracked while the change is
active so that scope, ordering, decisions and evidence are recoverable. At
closure, the active file is removed from the current documentation tree;
lasting rationale remains in ADR 0013, normative behavior remains in canonical
requirements and executable contracts, and the execution record remains in
Git history.

## Accepted Direction

The project owner confirmed the following on 2026-08-22:

1. treat the change as class C and use ADR 0013 to supersede ADR 0010;
2. represent the current helper as transitional `CMP-KAC` / `CR-KAC`, visually
   subordinate to the implementation-neutral permanent HLA;
3. retire materially changed identifiers rather than silently reusing them;
   and
4. do not define a future native AosCore interface until its released contract
   is inspected, while keeping the VDP Provider gate independent and open.

## Non-Negotiable Boundaries

- `CMP-KAC` is outside VDP, Brake Health and Tire Health payloads and business
  logic.
- Immutable Service metadata plus active Aos IAM state remain authoritative.
- The caller cannot select paths, operations, subject, audience, TTL, claims or
  signing payload.
- KUKSA remains unmodified and enforces supported JWT paths and operations.
- Services connect directly to KUKSA after credential preparation.
- The VDP Provider credential is a separate open design gate.
- No future native interface, path or rotation behavior is guessed.
- No real secret, JWT, private key or confidential Platform Team material may
  enter Git, logs, fixtures or dashboard evidence.

## Reserved Identifier Allocations

The following identifiers are reserved by the accepted cascade decision but
are not yet normative component or requirement definitions. Their anchors live
temporarily in this active plan so references remain deterministic during the
class-C transition. C3 moves each anchor and definition to its canonical owner
in the same change that removes it from this section.

| Reserved identifier | Planned canonical owner and meaning |
| --- | --- |
| <a id="cmp-kac"></a>`CMP-KAC` | Component register — transitional current-release KUKSA authorization compatibility helper |
| <a id="cr-kac"></a>`CR-KAC` | Component package index — helper requirements and verification package |
| Security successor after `SYS-SEC-006` | System requirements — current-release compatibility authority and lifecycle; its accepted successor ID is activated together with canonical allocation in C3 |
| <a id="if-auth-007"></a>`IF-AUTH-007` | Interface register — Service bootstrap to helper |
| <a id="if-auth-008"></a>`IF-AUTH-008` | Interface register — helper to Aos IAM `GetPermissions` |
| <a id="if-auth-009"></a>`IF-AUTH-009` | Interface register — helper rejection or Service-private JWT delivery |
| <a id="if-auth-010"></a>`IF-AUTH-010` | Interface register — current-release signer and verifier preparation |
| <a id="req-bhs-013"></a>`REQ-BHS-013` | Brake Health package — fixed-resource bootstrap and private JWT consumption |
| <a id="req-tire-013"></a>`REQ-TIRE-013` | Tire Health package — fixed-resource bootstrap and private JWT consumption |

## Phase Status

| Phase | Scope | State |
| --- | --- | --- |
| C0 | Protect baseline, classify change and establish branch | Complete |
| C1 | ADR, Draw.io, HLA and repository boundaries | Not started |
| C2 | Demo Scenario and Architecture Flows | Not started |
| C3 | System requirements, components, interfaces and CR packages | Not started |
| C4 | D4 decisions, executable contracts and acceptance | Not started |
| C5 | Reader navigation, tests, stale-reference audit and quality gates | Not started |
| C6 | Final review, ADR acceptance, merge and active-plan cleanup | Not started |
| T1 | Current-release detailed technical design | Blocked by accepted C1–C4 baseline |
| I1 | Source implementation and isolated unit tests | Not authorized |
| I2 | Factory integration and component/service integration | Not authorized |
| I3 | E2E qualification and demo acceptance | Not authorized |
| M1 | Future native AosCore contract assessment and migration | Deferred to released platform support |

## C0 — Protected Starting Point

- [x] Run the documentation quality gate.
- [x] Run all repository unit and contract tests.
- [x] Confirm that confidential inputs and `Brainstorming` remain outside Git.
- [x] Commit the preceding formal baseline as `5542b47`.
- [x] Push the protected baseline to `origin/main`.
- [x] Create branch `codex/kuksa-jwt-doc-cascade`.
- [x] Create proposed ADR 0013 and this active plan.
- [x] Review ADR 0013 and this active plan with the project owner.

Exit: the proposed authority and execution plan are accepted before canonical
HLA or requirement changes begin.

## C1 — Architecture Authority

1. Update the Draw.io authoring source before its generated PNG.
2. Remove the permanent Credential Broker from the VDP boundary.
3. Show the permanent implementation-neutral platform credential boundary.
4. Show `CMP-KAC` only as a dashed/current-release compatibility overlay.
5. Preserve unmodified KUKSA and the separate open VDP Provider lane.
6. Update HLA, repository boundaries and architecture navigation.
7. Mark ADR 0010 superseded only after ADR 0013 and the cascade are accepted.

Exit: no active target-architecture text assigns Service JWT issuance to VDP.

## C2 — Audience and Runtime Behavior

1. Update the Demo Scenario glossary and affected stages without making the
   helper part of the audience-facing product value.
2. Replace the `VDP Broker` authorization actor with `CMP-KAC`.
3. Show Service bootstrap, fixed-resource request, IAM lookup, volatile JWT
   delivery and direct Service-to-KUKSA access.
4. Add renewal, IAM/helper failure, restart, reboot, offline, stop,
   unregistration and removal flows.
5. Revalidate unaffected lifecycle and data flows without artificial semantic
   version bumps.

Exit: HLA, scenario and sequence diagrams describe one runtime model.

## C3 — Normative Allocation

### Stable identifier transitions

| Retire | Successor or disposition |
| --- | --- |
| `SYS-SEC-006` | A new canonically allocated security requirement for current-release compatibility authority and lifecycle |
| `IF-AUTH-001` | `IF-AUTH-007` — Service bootstrap to `CMP-KAC` |
| `IF-AUTH-002` | `IF-AUTH-008` — `CMP-KAC` to Aos IAM `GetPermissions` |
| `IF-AUTH-003` | `IF-AUTH-009` — helper rejection or Service-private JWT delivery |
| `IF-AUTH-004` | Covered by direct Service-to-KUKSA access plus `IF-AUTH-009/010` |
| `IF-AUTH-005` | `IF-AUTH-010` — temporary signer and verifier preparation |
| `REQ-VDP-006` | Remove Service JWT responsibility from `CR-VDP`; allocate it to `CR-KAC` |
| `REQ-BHS-003` | `REQ-BHS-013` — fixed-resource bootstrap and private credential consumption |
| `REQ-TIRE-003` | `REQ-TIRE-013` — fixed-resource bootstrap and private credential consumption |

Retain `SYS-SEC-004` with current-release scope, `SYS-SEC-005` and
`IF-AUTH-006` as the independent Provider gate, and the accepted QM/OEM policy
requirements.

### Package changes

- add transitional component `CMP-KAC` and component package `CR-KAC`;
- remove IAM lookup and Service JWT issuance from `CR-VDP`;
- narrow Brake/Tire credential integration so applications do not choose
  authority or construct claims;
- update `CR-FACTORY` for current-release helper packaging, clean reboot and
  later removal;
- preserve evidence-backed native `AOS_SECRET`/`GetPermissions` behavior in
  `CR-AOS` without adding upstream AosCore unit tests;
- update `CR-CROSS` isolation, lifetime, logging and fail-closed obligations;
  and
- update `CR-E2E` authorization, reboot, offline, removal and negative proof.

Exit: each new obligation has one component owner and verification allocation.

## C4 — D4 Contracts and Acceptance

1. Preserve `D4-009` as superseded history and introduce `D4-027` for the
   current-release compatibility contract.
2. Add deferred `D4-X04` for the future native AosCore JWT delivery assessment.
3. Keep `D4-010.2` open for VDP Provider authority and clarify the temporary
   current-release scope of signer/verifier decisions.
4. Create `contracts/kuksa-current-demo-authorization/` with:

   - request, response and error schemas;
   - the pinned KUKSA JWT profile;
   - Brake and Tire permission fixtures;
   - malformed, broadened and unsupported negative fixtures;
   - TTL, renewal, restart, stop and removal behavior; and
   - credential-location and logging/redaction rules.

5. Update active machine-readable references to D4-009 without changing
   unrelated QM advisory semantics.

Exit: executable contracts and negative fixtures exist before source coding.

## C5 — Reader and Quality Gate

1. Update README indexes and human-readable local cross-references.
2. Add compact supersession notes to historical material that could otherwise
   be mistaken for current authority; do not rewrite historical evidence.
3. Update documentation tests for versions, IDs and retirement mappings.
4. Add contract validation tests.
5. Search for stale active references to the obsolete permanent broker label,
   VDP-owned JWT issuance, active D4-009, retired interfaces and guessed native
   APIs.
6. Run `./scripts/docs-check` and all repository tests.
7. Inspect Markdown/Mermaid reader views and compare Draw.io with its PNG.

Exit: gates pass and no active document presents the retired model as current.

## C6 — Formal Acceptance and Cleanup

1. Review the complete class-C cascade as one baseline.
2. Change ADR 0013 from `Proposed` to `Accepted` and ADR 0010 to `Superseded`.
3. Record the governance change-impact block.
4. Merge the internally consistent branch to `main` and push it.
5. Remove obsolete active drafts, generated duplicates and superseded local
   brainstorming artifacts only after proving no active reference depends on
   them.
6. Remove this active plan from the current tree after closure; Git history
   remains the execution record.

Exit: `main` contains one accepted baseline with no competing active model.

## T1 — Current-Release Technical Design

After the architecture and normative boundaries are accepted, freeze a
separate executable technical design covering:

- helper process owner, packaging and startup ordering;
- local transport and peer isolation;
- exact request/response/error formats;
- permission translation and supported KUKSA claims;
- signer/verifier preparation, TTL, renewal margin and trustworthy time;
- Service-private volatile credential path and file permissions;
- restart, reboot, stop, removal and offline behavior;
- network allowlists and rate/queue bounds;
- safe logging and diagnostics; and
- deletion seams for migration to native AosCore support.

The accepted technical decisions move into `CR-KAC`, the D4 register and
`contracts/kuksa-current-demo-authorization/`; they do not remain as a second
permanent design plan.

## Implementation and Migration Gates

Implementation begins only after T1 review. The current-release sequence is:

1. implement and isolate-test `CMP-KAC`;
2. implement shared Brake/Tire compatibility bootstrap code outside analytics;
3. integrate helper packaging into the OEM Demo Factory Image;
4. close the independent VDP Provider credential gate;
5. integrate Services with unmodified KUKSA; and
6. run contract, integration, security-negative and E2E acceptance.

Future native migration begins only after a released AosCore contract is
available. It assesses the real interface, adapts Service integration, reruns
the same acceptance suite, removes compatibility packages and deletes the HLA
overlay. No drop-in migration is promised.

## Change Impact Record

```text
Change: Separate current-release KUKSA JWT compatibility from VDP and preserve
        an implementation-neutral native AosCore target.
Class: C
Owning source: ADR 0013 (Proposed)
Affected: HLA/Draw.io, repository boundaries, Demo Scenario, Architecture
          Flows, system requirements, component/interface register, CR-VDP,
          CR-KAC, CR-BHS, CR-TIRE, CR-FACTORY, CR-AOS, CR-CROSS, CR-E2E,
          D4 register, authorization contracts, indexes and tests.
Revalidated: ADR 0012, KUKSA boundary, lifecycle ownership, QM containment,
             Cloud/dashboard packages, Vehicle Gateway and Vehicle Simulation.
Retired: ADR 0010 on acceptance; SYS-SEC-006; IF-AUTH-001..005;
         REQ-VDP-006; REQ-BHS-003; REQ-TIRE-003; D4-009.
Evidence: protected baseline 5542b47; documentation and repository test gates;
          reader-view and Draw.io/PNG review; contract and E2E evidence later.
```

## Review Gate

Review of this file and proposed ADR 0013 is required before C1 changes to the
canonical HLA, scenario, requirements or component packages begin. Review does
not authorize implementation, builds, signatures or external-state mutation.
