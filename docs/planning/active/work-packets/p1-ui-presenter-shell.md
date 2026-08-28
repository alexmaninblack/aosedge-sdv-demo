<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Presenter UI Implementation Work Packet

- ID: `WP-P1-UI-001`
- Lane: `L-UI`
- Increment: `IMP-01`
- Review state: `ACCEPTED — AUTHORIZED`
- Version: 0.2
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded scope in this packet
- Exact npm registry package installation authorized: yes
- Cloud, backend, helper, VM, Unit, CARLA, signing, push or merge authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-UI-001 0.3](p0-ui-readiness.md), SHA-256
  `d8ff0a65d450cd74e7dae5b838c14d66763d3cb7d3460ea804e52ae0fdac3234`

## Outcome

Implement the first fixture-only Presenter UI as a maintainable browser
application that reproduces the accepted interaction contract and visual
associations. This packet creates product code; it does not connect to
AosCloud, a native helper, CARLA, a backend, a VM or a Unit.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `aosedge-sdv-demo` |
| Base revision | `bedeb2f8e291eb5e6b20c3dbc2188fce5f7069c7` |
| Required base relationship | clean `main`, equal to `origin/main` at authorization |
| Branch | `codex/imp-01-presenter-shell` |
| Isolated worktree | sibling path `../aosedge-sdv-demo-imp-01-presenter-shell` from the repository checkout |
| Writable repository boundary | `apps/presenter-ui/**` only |

The worker must stop if the base, readiness digest or worktree cleanliness does
not match. It must not edit requirements, contracts, architecture, accepted
mockups, planning documents or another application boundary.

## Frozen Technology and Dependencies

- Node `26.0.0`, npm `11.12.1`, strict TypeScript and lockfile v3;
- React `19.2.8`, React DOM `19.2.8`;
- Vite `8.2.2`, `@vitejs/plugin-react` `6.1.1`, TypeScript `7.0.2`;
- Vitest `4.1.11`, jsdom `30.0.1`;
- Testing Library React `16.3.3`, DOM `10.4.1`, jest-dom `7.0.1` and
  user-event `14.6.6`;
- Playwright Test `1.62.1`, using the qualified locally installed Chrome
  channel; no Playwright browser-binary download; and
- `@types/react` `19.2.18` and `@types/react-dom` `19.2.5`.

After authorization, registry access is limited to installing exactly these
versions and their lockfile-resolved transitive dependencies. Direct
dependencies use exact versions with no caret or tilde. The worker commits one
`package-lock.json`, records its SHA-256 and uses `npm ci` for repeat checks.
No other package may be added without a bounded change request.

## Product Boundary

The application is one static modular-monolith bundle under
`apps/presenter-ui/` with these responsibility boundaries:

- `src/app/`: composition, shared header, dependency wiring and route/view
  selection;
- `src/domain/`: framework-independent read models, reducers and milestone
  derivation;
- `src/features/vehicle-context/`, `global-lifecycle/`, `platform-team/`,
  `brake-team/`, `tire-team/`, `release-authority/` and
  `evidence-overlays/`: separate public feature entry points;
- `src/adapters/fixtures/`: the only adapter implementation in `IMP-01`;
- `src/shared/`: small visual primitives, layout and project-owned design
  tokens; and
- `src/test-support/` plus `tests/`: fixture builders, architecture, component
  and browser tests.

The application layer composes producer-team features and Release Authority
side by side. Platform, Brake and Tire feature code must not import, contain or
act as Release Authority. Cross-feature internal imports, direct component-to-
adapter calls and browser-owned authoritative lifecycle state are rejected by
an automated architecture test.

## Required Behavior

1. Reproduce the accepted full-screen right-hand Presenter workspace and
   shared header from Interaction Specification 2.5 and the accepted review
   source, using repository-owned icons and wording.
2. Preserve independent Platform, Brake and Tire perspectives, independent
   release progress and return to the previously selected team/version
   position.
3. Render Test Vehicle and Production Vehicle representation, fixed team and
   Release Authority context, version-only scrolling and Details/Operational
   Logs overlays with correct focus return.
4. Provide deterministic fixture states for normal, blocked, unavailable,
   stale, submitting, uncertain/reconciling, failed, offline/reconnected,
   source-asset-failure, M0/M1/G0 and R0 presentations.
5. Present fixture facts with an explicit non-live source label. Action buttons
   change fixture presentation only and cannot invoke an external operation.
6. Reserve, but do not render, native CARLA, Vehicle Controller and Terminal
   Engineering Telematics surfaces. The browser must not embed their
   screenshots or attempt to control their windows.
7. Keep Platform Details free of Service quotas; show Service metadata and
   quotas only in Brake/Tire Details. Preserve the accepted Safe Stop,
   dependency-block and multi-tenant-isolation presentation semantics.

## Commands and Generated Output

The committed package scripts must expose equivalent deterministic commands:

```text
npm ci
npm run typecheck
npm run test:unit
npm run test:browser
npm run build
npm run dev -- --host 127.0.0.1 --port 18070
```

Generated output is limited to ignored paths inside `apps/presenter-ui/`:

```text
node_modules/
dist/
coverage/
test-results/
playwright-report/
.vite/
*.tsbuildinfo
```

Reviewed browser goldens, if created, live under
`apps/presenter-ui/tests/browser/golden/**` and are committed evidence rather
than generated output.

## Required Verification and Exit Evidence

- strict typecheck and production build pass;
- domain/reducer, fixture-schema, architecture and component suites pass;
- browser coverage passes against the local Chrome channel for every
  fixture-applicable `UI-AT-001` through `UI-AT-050` obligation;
- one reviewed full-screen human pass confirms hierarchy, scrolling, modal
  behavior, team independence, Test/Production wording and asset rendering;
- changed files remain entirely under `apps/presenter-ui/**`;
- the completion packet records branch/commit, exact changed files, lockfile
  digest, Node/npm versions, commands/results, unimplemented integrations and
  confirmation that no forbidden operation occurred.

Successful isolated checks change the increment to `IMPLEMENTED`, not
`QUALIFIED`. Native launcher composition, live data and external lifecycle
actions require later increments and separate evidence.

## Explicit Exclusions

- no Cloud/backend/helper/Gateway adapter or credential handling;
- no signing, publication, provisioning, VM, Unit, CARLA or network mutation;
- no native launcher/window-management implementation;
- no static-container/Compose packaging in this packet;
- no SSR, Electron, micro-frontends, Storybook, runtime plugins, global state
  framework, mobile/tablet layout or second authoritative state store;
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the exact base, writable boundary, dependency installation,
local Chrome use, commands, tests and exclusions on 2026-08-28. The worker may
create the named branch/worktree and implement this packet. Any boundary
expansion requires a new review; successful implementation does not authorize
push, merge or a live integration operation.
