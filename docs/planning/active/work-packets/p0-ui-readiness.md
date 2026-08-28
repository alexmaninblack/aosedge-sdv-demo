<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 UI Readiness Work Packet

- ID: `WP-P0-UI-001`
- Lane: `L-UI`
- Parent increment: `IMP-01`
- Review state: `COMPLETED — READY_FOR_CODE_PACKET`
- Version: 0.3
- Prepared: 2026-08-27
- Updated: 2026-08-28
- Accepted: 2026-08-28
- Execution authorized: yes — P0 read-only assessment only
- Authorized: 2026-08-28
- Product implementation, dependency installation, external download, build,
  signing, Cloud, VM, Unit or CARLA mutation authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Produce the exact implementation packet for the fixture-only presenter
application shell. This P0 packet performs assessment only. It must not turn
the accepted HTML review artifact into product code or select behavior that is
not already present in the accepted UI contract.

## P0 Execution Result

- Completed: 2026-08-28
- Exit state: `READY_FOR_CODE_PACKET`
- Product implementation authorized by this result: no

All frozen revisions and SHA-256 values matched. The repository remained clean
and the six frozen inputs were byte-identical between the read baseline and the
current accepted documentation state. The assessment confirmed that there is
no existing product application, package manifest or lockfile to preserve;
the accepted HTML remains a review artifact rather than product source.

The validated first implementation boundary is:

- one strict TypeScript/React/Vite modular-monolith browser application under
  `apps/presenter-ui/**`;
- Node `26.0.0`, npm `11.12.1`, one exact committed lockfile and loopback
  development endpoint `127.0.0.1:18070`;
- fixture-only typed read adapters in `IMP-01`, with no Cloud, helper, backend,
  credential or lifecycle-mutation capability;
- Vitest, React Testing Library and Playwright coverage plus the final human
  visual veto; and
- repository-owned icons reused as supplementary visuals, while CARLA,
  Controller and Terminal remain native external surfaces rather than browser
  screenshots or reimplementations.

Application composition shall place Platform, Brake and Tire producer features
and the independent OEM Release Authority feature side by side. A producer
feature must not import or contain Release Authority; the application layer
composes both public entry points. This preserves the accepted organizational
separation in code as well as in presentation.

Read-only verification passed:

- `./scripts/docs-check`: 115 Markdown documents, 658 stable identifiers and
  38 Mermaid diagrams;
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 284 tests passed.

The code branch base must be the exact current accepted `main` revision at the
time `IMP-01` is authorized. The older `bf231c3` revision remains the frozen
evidence-read baseline; it is not a reason to omit the accepted P0 records from
the future implementation branch. No source, dependency, generated bundle or
external state was changed during P0.

## Repository and Baseline

| Item | Frozen value |
| --- | --- |
| Repository | `aosedge-sdv-demo` |
| Read baseline | `bf231c350c17f8173bfd4da19bfa45932b45cc24` |
| Required branch state | clean `main`; unexpected files are reported, not removed |
| Future code branch | `codex/imp-01-presenter-shell` only after separate authorization |
| P0 writable paths | none |
| P0 build outputs | none |

Current assessment fact: the repository contains the accepted standalone HTML
mockup and its source, but no selected application framework, package manifest
or product application root. The working technology and componentization
baseline below closes the design direction; P0 must validate exact local
versions, commands and paths before `IMP-01` can be authorized.

## Frozen Inputs

The worker reads the following inputs at the frozen repository revision:

- [Surface Register 0.14](../../../demo/mockups/README.md);
- [Interaction Specification 2.5](../../../demo/mockups/aosedge-demo-interaction-specification.md);
- [UI Traceability Register 1.1](../../../demo/mockups/aosedge-demo-ui-traceability-register.md);
- [accepted review source](../../../demo/mockups/aosedge-demo-interaction-mockup-2-4.source.html);
- [Demo Run State v1](../../../../contracts/demo-run-state/demo-run-state-profile.v1.json);
- [local hosting profile v1](../../../../contracts/local-demo-hosting/local-demo-hosting-profile.v1.json); and
- `UI-AT-001` through `UI-AT-050` from the accepted UI traceability register.

| Frozen file | SHA-256 |
| --- | --- |
| Surface Register | `5feb4d39175ee8d1b1e8f30199b5cecb53e9d4a3c94c6f50d9a597946b80ed87` |
| Interaction Specification | `d6d71fa1f5981d109ae6354e945b47e50298c9095a6f9048fd3b088bd44973d0` |
| UI Traceability Register | `84cb86ba668b13fb979b1b1df219761a49ed410856629fde712051001cd63bd3` |
| accepted review source | `37cfebf43b0d2968d941139d4324caf5e956af93cb8c6b360aacf51634d45861` |
| Demo Run State v1 | `3cc284f15b0b81f2c145b64e813c6081e255cf74b883f8feb6111db4bf47dcf2` |
| local hosting profile v1 | `9f68013c18c8945777e9fc4b015036492226db6e1ac1ed3eae10703bc498e296` |

Any digest mismatch stops the packet and is reported to the Integration
Coordinator. The worker must not regenerate the digest against changed input.

## Working Technology Baseline

P0 validates the following preferred implementation baseline rather than
performing an open-ended technology search:

| Concern | Working decision |
| --- | --- |
| Application form | One browser-based modular monolith; no micro-frontends |
| Language | TypeScript in strict mode |
| View layer | React functional components |
| Development/build tool | Vite |
| Package discipline | `npm` with one committed lockfile after code authorization |
| Domain and component tests | Vitest plus React Testing Library |
| Browser and visual tests | Playwright at reviewed presenter-display profiles |
| Styling | Project-owned design tokens and locally scoped styles; no heavy external design system |
| Proposed application root | `apps/presenter-ui/` |
| Development runtime | Local browser development server on a reviewed loopback-only port |
| Demo runtime | Prebuilt static bundle in the `SOFTWARE_DELIVERY` ARM64 container at `127.0.0.1:18080` |
| Backend | None inside `IMP-01`; fixture reads only |
| Explicit exclusions | Electron, server-side rendering, micro-frontends, runtime plugin loading, Storybook and a global state framework are not first-increment dependencies |

The worker may reject one of these choices only through a bounded change
request that proves a conflict with an accepted requirement, the qualified
Apple Silicon host, deterministic testing or the later read-adapter boundary.
Personal preference is not a reason to reopen the choice.

## Componentization Model

The application is one deployable bundle but not one large component. It is
decomposed by product responsibility:

```text
apps/presenter-ui/src/
├── app/                         composition, routing and dependency wiring
├── domain/                      framework-independent types and reducers
├── features/
│   ├── vehicle-context/         selected vehicle, source and workspace status
│   ├── global-lifecycle/        qualification, M0/M1/current lifecycle and R0
│   ├── platform-team/           VDP releases and Safe Stop application evidence
│   ├── brake-team/              Brake releases, quotas and backend evidence
│   ├── tire-team/               Tire release, quotas and backend evidence
│   ├── release-authority/       independent OEM authorization context
│   └── evidence-overlays/       Details, logs and qualification evidence
├── adapters/
│   └── fixtures/                the only IMP-01 adapter implementations
├── shared/
│   ├── components/              small reusable visual primitives
│   ├── layout/                  fixed composition and scroll boundaries
│   └── design-tokens/           color, spacing, type and icon vocabulary
└── test-support/                builders, fixtures and browser helpers
```

`vehicle-context` does not render or reimplement CARLA, the native Controller
or the Terminal Engineering Telematics Dashboard. It projects only the
selected vehicle, live-source and workspace-completeness facts needed by the
shared header and right-hand context. The Presenter Launcher owns physical
native-window composition; the browser owns only its accepted right-hand
workspace plus the shared header/read model defined by the Interaction
Specification.

The application must not use one configuration-driven `TeamWorkspace` mega-
component. Shared release cards, timeline primitives, status presentation and
domain types may be reused, while Platform, Brake and Tire retain separate
feature compositions and tests. Platform-only Safe Stop behavior must not
leak into Service modules; Service-only quota presentation must not appear in
the Platform module.

A component is extracted when it has an independent responsibility, state,
reuse or test boundary. Splitting every label or button into a separate file
is not required.

## State and Adapter Boundaries

| State class | Owner and rule |
| --- | --- |
| Presentation state | Browser-local selected perspective, modal, focus and independent scroll position; never Cloud lifecycle authority |
| Observed state | Read-only projection with source, freshness, observation time and unavailable/stale/error state; AosEdge or the named backend remains authoritative |
| Action state | Request/submitting/uncertain/reconciling/failure presentation isolated from observed state; no optimistic lifecycle completion |
| Domain state | Framework-independent Platform, Brake, Tire, vehicle and global-lifecycle reducers; team release progress remains independent |

React components do not call fixtures, future APIs or helpers directly. They
consume typed domain interfaces supplied by application composition. `IMP-01`
implements only fixture read adapters. Future AosEdge, Brake backend, Tire
backend and protected-action adapters are named design seams, not empty or
partially functioning implementations in the first increment.

There is no global browser operation lock. Future protected operations use
the accepted resource-conflict model; unrelated team workflows remain
independently viewable and actionable.

## Test Architecture

1. Pure TypeScript unit tests prove domain reducers, lifecycle transitions,
   source/freshness handling and team independence without React.
2. React component tests prove each feature through its public inputs and
   visible outcomes without reading another feature's internals.
3. Contract/fixture tests prove every fixture satisfies the same typed read
   interface expected from future adapters and contains no credential or
   privileged helper capability.
4. Playwright browser tests prove the accepted right-workspace navigation,
   modal/focus, version-only scrolling, fixed context, asset failure and
   reserved browser geometry. Presenter Launcher integration and human review,
   not Playwright alone, prove the complete native-left/browser-right physical
   composition. Human review remains the final visual veto.

Tests may import public feature entry points and shared primitives. Cross-
feature imports into another feature's internal files fail the repository
architecture gate.

## Exact P0 Tasks

1. Confirm the repository and input digests match this packet and record any
   pre-existing dirty state without changing it.
2. Inventory the current UI-related source, assets, tests and local-hosting
   support. Explicitly distinguish review-only HTML from reusable product
   assets.
3. Validate the working TypeScript/React/Vite modular-monolith baseline,
   `apps/presenter-ui/` root, container target and four-level test strategy
   against the accepted host and local-hosting contract. Raise a change
   request rather than silently substituting another stack.
4. Freeze the exact future writable paths, generated/ignored paths, Node/npm
   versions, loopback development port, local run command, production build
   command, test commands and dependency-lock strategy. No package is
   installed during P0.
5. Freeze public feature entry points, allowed dependency directions and one
   typed fixture/read-adapter seam. Fixture adapters may supply all current
   state in `IMP-01`; future Cloud, helper, backend and Gateway adapter
   implementations must remain absent and impossible to invoke.
6. Define the architecture test that rejects cross-feature internal imports,
   direct component-to-adapter calls and any browser-owned authoritative
   lifecycle store.
7. Map `UI-AT-001` through `UI-AT-050` to named automated tests or explicit
   human visual checks and their actual owner. Include Presenter Launcher and
   human coverage for fixed left vehicle surfaces; browser coverage for
   independent team perspectives, the right-hand global view, fixed context,
   version-only scrolling, Details modal behavior, Test/Production wording,
   Release Authority separation, asset failure and redaction states.
8. Produce one exact `IMP-01` code packet with files, tests, fixtures, commands,
   exit evidence and explicit exclusions. Do not implement it.

## Required Read-Only Checks

```text
./scripts/docs-check
python3 -m unittest discover -s tests -p 'test_*.py'
```

These checks validate the current design baseline only. They do not qualify a
future UI stack. The worker records the commands and results without editing
generated output into the repository.

## Forbidden Work

- no edits to the mockup, contracts, requirements or architecture;
- no application code, package manifest, lockfile or generated scaffold;
- no dependency install or network download;
- no AosCloud credentials, helper invocation or backend implementation;
- no signing, publishing, provisioning, VM, Unit or CARLA operation; and
- no claim that a fixture represents live authoritative AosEdge state.

## Completion Packet

The worker returns one report containing:

1. confirmed baseline and input digests;
2. current UI inventory and reusable versus review-only assets;
3. validated technology/componentization baseline or one bounded change
   request with evidence;
4. exact future branch, worktree, writable and generated paths;
5. exact module dependency graph and public feature entry points;
6. exact run, build, domain, component, contract and browser-test commands;
7. the `UI-AT-001` through `UI-AT-050` coverage map;
8. the proposed `IMP-01` code packet;
9. open gaps or change requests; and
10. confirmation that no forbidden operation occurred.

## Exit and Escalation

P0 exits `READY_FOR_CODE_PACKET` only when every item above is exact and no
accepted UI behavior needs reinterpretation. A contract mismatch, missing
asset, required external service, inability to keep adapters read-only, or a
technology/module choice that changes visible behavior, creates a second state
authority or couples independent team workflows is escalated to the Demo
Solution owner and leaves this packet `BLOCKED`.
