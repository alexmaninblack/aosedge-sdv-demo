<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Cloud Foundation Implementation Work Packet

- ID: `WP-P1-BRAKE-CLOUD-FOUNDATION-001`
- Lane: `L-BRAKE-CLOUD`
- Increment: `IMP-04-BRAKE-CLOUD-FOUNDATION-001`
- State: `IMPLEMENTED — ISOLATED SOURCE FOUNDATION COMPLETE`
- Accepted: 2026-08-28
- Repository: `brake-health-cloud`
- Frozen base: `6da2926ba96df5e470bfbc3514e983f5d54c3975`
- Branch: `codex/imp-04-brake-cloud-foundation`
- Integration owner: Demo Integration Coordinator
- Exact npm registry package installation authorized: yes, only the frozen
  direct versions and their lockfile-resolved transitive dependencies
- Cloud, helper, credential, VM, Unit, CARLA, container, push or merge
  authorized: no

## Outcome

Create the maintainable product foundation for the Brake Health backend and
Function Dashboard. The packet establishes one npm workspace, strict
TypeScript boundaries, a deterministic SQLite migration seam, a loopback-only
backend health surface and a fixture-only Dashboard shell with the accepted
`Release Candidates`, `Vehicle Data` and `Service Logs` views.

The packet does not ingest real Brake messages, publish a Service candidate,
call AosCloud, package a container or claim an operational backend.

## Frozen Inputs

| Input | Version or revision | SHA-256 |
| --- | --- | --- |
| `CR-BRAKE-CLOUD` | 0.5 plus accepted technology decomposition | `d378a97ec84e2a8ba2d279f4e87a92ba62a44928ae7dfd2d66e3fc26cf307376` |
| Brake Cloud API profile | D4-017 / 1.0.0 | `292d720aa99478cd6da7f6fc7a0a2e127012affe6d9519e0f08c76752ba14773` |
| Local Demo Hosting profile | 1.0.0 | `9f68013c18c8945777e9fc4b015036492226db6e1ac1ed3eae10703bc498e296` |
| Artifact Publication profile | 1.0.0 | `52bafd7b1249ec8bc10265e913265cdc7c2975f5f56db7ff3cd5cdbad4001c39` |
| Presenter Interaction Specification | 2.5 | `626fa2a9283225d0bba2dd4d2c33bf16b5e118b1010a983ec4ad18673bea7a2b` |
| UI traceability register | 1.2 | `84cb86ba668b13fb979b1b1df219761a49ed410856629fde712051001cd63bd3` |

All solution-repository inputs are read-only. A digest mismatch stops the
packet; the worker must not reinterpret or regenerate an accepted contract.

## Repository and Isolation

1. Create a clean isolated worktree from the exact frozen base.
2. Use only branch `codex/imp-04-brake-cloud-foundation`.
3. Keep the existing `brake-health-cloud` checkout and its `main` unchanged.
4. Keep dependency caches and generated test/build output outside committed
   product paths.
5. Commit only the writable boundary and report the exact commit SHA.

## Frozen Technology and Dependencies

- Node `26.0.0`, npm `11.12.1`, strict TypeScript and lockfile v3;
- React `19.2.8`, React DOM `19.2.8`;
- Vite `8.2.2`, `@vitejs/plugin-react` `6.1.1`, TypeScript `7.0.2`;
- Vitest `4.1.11`, jsdom `30.0.1`;
- Testing Library React `16.3.3`, DOM `10.4.1`, jest-dom `7.0.1` and
  user-event `14.6.6`; and
- `@types/react` `19.2.18` and `@types/react-dom` `19.2.5`.

The backend foundation uses only built-in `node:http`, `node:sqlite` and
`node:test`. It introduces no web framework, ORM, query builder, state
framework or authentication library. Direct dependencies use exact versions
with no caret or tilde. The worker commits one `package-lock.json`, records its
SHA-256 and uses `npm ci` for repeat verification. Any additional package is a
boundary expansion and must stop the packet.

## Writable Boundary

The packet may create or change only:

- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `NOTICE`,
  `THIRD_PARTY_NOTICES.md`, `REUSE.toml` and `LICENSES/**`;
- `.gitignore`, `.npmrc`, `package.json`, `package-lock.json` and
  `tsconfig*.json`;
- `apps/backend/**` and `apps/dashboard/**`;
- `packages/domain/**`, `packages/contracts/**` and
  `packages/test-support/**`;
- `migrations/**`, `tools/**` and `tests/**`.

The existing Apache-2.0 `LICENSE` remains read-only. No `deploy/**` file is
created in this packet because container and Compose work belongs to
`BRAKE-CLOUD-INTEGRATION-001`.

## Product Boundaries

- `apps/backend` owns the loopback HTTP composition root, readiness/liveness
  presentation and SQLite adapter wiring. It must not contain domain rules.
- `apps/dashboard` owns the Brake Function Team browser composition and three
  accepted views. It must not contain an OEM Release Authority or AosCloud
  client.
- `packages/domain` owns framework-independent state and projections.
- `packages/contracts` owns closed Brake Cloud types and validators derived
  from, but not copied over or changed from, the frozen solution contracts.
- `packages/test-support` owns deterministic clocks, IDs and fixture builders.
- `migrations` contains numbered forward-only SQL migrations; application
  startup applies them transactionally and refuses an unknown newer schema.

An automated architecture test must reject cross-layer imports that bypass
these public boundaries. The Dashboard may reuse the accepted visual language
and exact dependency versions, but it must not import Presenter UI source.

## Exact Required Behavior

### Workspace and commands

1. One root npm workspace owns all applications and packages and one exact
   lockfile.
2. Repository scripts expose deterministic equivalents of:

```text
npm ci
npm run typecheck
npm run test
npm run build
npm run dev -- --host 127.0.0.1
```

3. The default development listeners bind only to `127.0.0.1`; no LAN or
   wildcard listener is permitted.

### Backend foundation

1. Expose separate `/health/live` and `/health/ready` endpoints through
   `node:http` with closed JSON response shapes.
2. Liveness reports process health only. Readiness is true only after the
   configured SQLite database is open and all known migrations are applied.
3. The default test database is temporary; repository-relative runtime data
   is neither required nor committed.
4. Startup and shutdown are explicit and testable. Tests do not sleep, bind a
   public interface or depend on wall-clock time.
5. No D4 ingestion, acknowledgement, query/SSE or cleanup API is implemented
   yet. Unknown routes return a closed not-found response.

### SQLite migration seam

1. Create the smallest schema required to record migration state and prove
   transactional forward-only migration behavior. Do not pre-implement the
   Brake event model owned by `BRAKE-CLOUD-DATA-001`.
2. A fresh database reaches the expected schema version deterministically.
3. Reopening the same database is idempotent; a migration failure rolls back;
   an unknown newer schema blocks readiness with a factual reason.

### Fixture-only Dashboard shell

1. Provide navigable `Release Candidates`, `Vehicle Data` and `Service Logs`
   views using deterministic fixture adapters only.
2. Clearly label fixture state as non-live. Buttons must not call a helper,
   backend mutation or AosCloud.
3. Release Candidates demonstrates the prepared v1-v3 catalogue shape,
   Service metadata, VDP compatibility, permissions and Service quotas without
   signing or publication behavior.
4. Vehicle Data demonstrates empty, disconnected and representative v1/v2/v3
   projection shells without implying persisted operational evidence.
5. Service Logs demonstrates unavailable/empty fixture states only and must
   not present local process logs as authoritative AosEdge/AosCloud logs.

## Required Verification

The packet must add and pass deterministic verification for:

- exact Node/npm version and lockfile/direct-dependency checks;
- strict typechecking, production frontend build and backend compilation;
- architecture/import-boundary rules;
- fresh, repeat, failed and newer-schema SQLite migration cases;
- loopback-only listener configuration, live/ready transitions, closed JSON
  responses and unknown-route behavior;
- clean backend shutdown and temporary-database cleanup;
- all three Dashboard views, non-live source labeling, navigation and basic
  keyboard/focus behavior;
- absence of real network adapters, credential material, container/deployment
  files and generated output from the commit; and
- repository license, secret-negative and quality checks.

## Explicit Exclusions

- no real D4-017 ingestion, durable acknowledgement, reconstruction, query,
  SSE, retention or cleanup behavior;
- no KAC, KUKSA, Gateway, Brake Service, AosCloud or publication helper
  adapter;
- no certificate, key, token, secret, credential loading or authentication;
- no Dockerfile, Compose, ARM64 image, `/data` production volume or QEMU
  route;
- no Playwright/browser binary download and no screenshot-golden obligation;
- no signing, publication, Cloud, VM, Unit, CARLA or live operation;
- no push, merge or mutation of `main`.

## Completion Record

- Branch/worktree: `codex/imp-04-brake-cloud-foundation` at the isolated
  sibling `brake-health-cloud-imp-04-foundation` worktree.
- Commit/parent: `68fe61b292b0b9671b1af0dc1881fe37dc5f97de` over the exact
  frozen base `6da2926ba96df5e470bfbc3514e983f5d54c3975`.
- Boundary: 43 changed files, all within the writable boundary; the existing
  Apache-2.0 `LICENSE` remained unchanged.
- Dependencies: the exact frozen React/Vite/TypeScript test set only; one
  lockfile v3 with SHA-256
  `26ef2251179f7cde0978ed8aeff3b1e6863bff7e9d1884d814951a9f1c72a7cc`.
- Verification: strict typecheck and production build passed; five built-in
  Node tests, ten Vitest tests and four architecture tests passed; repeat
  `npm ci` and repository quality gate passed.
- Implemented: loopback-only health foundation, explicit lifecycle,
  transactional forward-only SQLite migration seam, closed public/domain
  contracts and the fixture-only three-view Dashboard shell.
- Excluded as required: D4 data behavior, real adapters, credentials,
  publication, Docker/Compose, ARM64/QEMU and all live operations.
- No generated output, credential, downloaded binary or deployment file was
  committed. No push, merge, signing, Cloud, VM, Unit, CARLA or container
  operation occurred. There are no open packet defects.

`IMPLEMENTED` means only that the isolated foundation passes. It does not mean
that Brake Cloud data handling, UI behavior, packaging or live integration is
implemented or qualified.

## Authorization Gate

The user accepted the repository, exact technology baseline, decomposition and
this bounded first implementation step on 2026-08-28. This packet authorizes
only the isolated source implementation and exact registry dependency
retrieval above. Any writable-boundary expansion, container build, external
adapter or live operation requires a later reviewed packet or explicit
operator authorization.
