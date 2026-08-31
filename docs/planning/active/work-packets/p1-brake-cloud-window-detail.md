<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Cloud Window Detail Work Packet

- ID: `WP-P1-BRAKE-CLOUD-WINDOW-DETAIL-001`
- Lane: `L-BRAKE-CLOUD`
- Parent increment: `IMP-04`
- Review state: `ACCEPTED — IMPLEMENTATION AUTHORIZED`
- Version: 1.1
- Prepared: 2026-08-31
- Independently reviewed and accepted: 2026-08-31
- Product implementation authorization: yes, only for the exact local
  source-only five-path boundary below
- Network, dependency retrieval, container, VM, Cloud, signing, publication,
  merge or push authorization: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Add the smallest source-only Brake Backend point read needed by the Vehicle
Data detail view:

```text
GET /api/v1/brake/units/{systemUid}/windows/{eventId}
```

The response returns the existing factual window summary and zero through 150
already accepted samples from the current SQLite data model. The packet adds
no database migration and changes no collection, SSE, Current Unit, paging,
listener, security or first-demo authority behavior.

This packet is independently accepted and authorizes only the exact local
source-only five-path implementation below. It authorizes no packaging,
network, live, merge or push action.

## Exact Frozen Entry Base

| Item | Exact value |
| --- | --- |
| Product repository | sibling `brake-health-cloud` repository |
| Product commit | `1320dde24ae0f72771ea9320c2bd2212c20726ba` |
| Product parent | `a4b5b33f53a0931ae115f0790216e40b445499d6` |
| Product tree | `e13fe62e0e2e5a9702f98e2170a32fde9cc4083e` |
| Required product refs | clean `main == origin/main ==` product commit |
| Reviewed contract-cascade commit | `f7c701dc9c0b4052dfff6a0c8de138eef5094600` |
| Reviewed contract-cascade tree | `2b3fe064b7c5f05eafea2e4519585aa23acaeb14` |

A future worker must create one isolated product worktree from the exact
product commit. A different commit/tree, dirty base, changed frozen input or
pre-existing implementation outside the declared boundary stops execution.

## Frozen Contract Inputs

All hashes are raw file SHA-256 at the contract-cascade commit.

| Input | Role | SHA-256 |
| --- | --- | --- |
| D4 decision register | accepted D4-017 additive amendment | `e90bcd7b9a3bf12c3ff0f2e7f002b1294f6e65d2c5815a05e8e187fe712172d7` |
| `CR-BRAKE-CLOUD` | accepted requirement/test cascade | `6b72dee873760cff4f2642498626ec5bbf8ebb4b14eab8d657f11819985e53e9` |
| Brake Cloud API README | accepted 1.0.0 plus detail closure | `4e9fc900c1de737983aff3486b8ae98c65de42e468e6995d6ae7dfbf975ffade` |
| Query/SSE/Admin profile | accepted 1.1.0 | `5a07981c6ca7c9747c9d7925c03d8c73b5a3b0852a29e36c952b0cad06d682b3` |
| Window-detail schema | closed response 1.0.0 | `ac3b34589a5d5084b5b2eac229bf1b5467fdf6006b079d8cf9cbd29d5db9a99e` |
| Window-detail fixture | growing two-sample valid response | `89f10a95af5f579f96db0cedd977d61a63f007f4a2efce4f752e1dd85a91eda9` |
| Query-page schema | immutable collection/window-item input | `17b13d55462e97ca2011391e1ce78e272124839b1851cfcf675ad9434d802c38` |
| Current Unit context schema | immutable Unit scope | `f5733d7750b2fbda863201f66503e40f97c146f426ff4ec290f195efdcca4681` |
| Error-response schema | immutable error body | `53ff0a6073f6d3eb51e67165d62bdc512bcd98c2d200690f8607ee146d4ea30b` |
| SSE schema | immutable notification-only body | `7e8bccc76167722910e9c671f46223caf53708a29758587906a4afcac4356d1b` |
| Window-chunk schema | exact stored sample definition | `6166d196b15017d0b6ddc6be7ba94548fff11cc2b260daafb804fe9c1a532b32` |
| Window-chunk fixture | source of the detail fixture samples | `b931ef9cbac717768a6db23992c70acebad74a5b1ccffdcfdd07c707ed4665f6` |

The proposed 1.1.0 profile is additive. Collection response bodies and the new
detail response both retain body `contractVersion: 1.0.0`. A worker may not
reinterpret the profile version as permission to alter an accepted collection
payload.

## Product-Base Compatibility Digests

| Product-base file at `1320dde` | SHA-256 |
| --- | --- |
| `apps/backend/src/brake-data-domain.ts` | `09b482151def9c2cb708e27e50ec8149385fd5c65e6e0cf3b1349542d0d72930` |
| `apps/backend/src/brake-data-store.ts` | `54162cd7d1b0c21139b63ab6fb1fabef06a9f939bc0f3ae0ce080f5df6d1d48c` |
| `apps/backend/src/brake-data-http.ts` | `47de9d6dd2b51a310693f5e8471c1483a5e7e6f31ff6dd4f0f431e77ac5414d0` |
| `apps/backend/test/brake-data.test.mjs` | `12f29ae8f0dcb7e87257721314fb9d6b22a9d9b111dce79ca374da55f60e8b78` |
| `apps/backend/test/backend.test.mjs` | `21da4b15dcf52f455b7a59f4a0ddd0f1349c52d583b361d3294d2b6a78a71312` |
| immutable `migrations/002_brake_data.sql` | `bfc0d901968d0b22a39e712cd900751f222546c93a8d05f0f120729d0f468d94` |
| immutable `package-lock.json` | `26ef2251179f7cde0978ed8aeff3b1e6863bff7e9d1884d814951a9f1c72a7cc` |

## Exact Five-Path Future Writable Boundary

Only these product paths may change after separate implementation
authorization:

1. `apps/backend/src/brake-data-domain.ts`;
2. `apps/backend/src/brake-data-store.ts`;
3. `apps/backend/src/brake-data-http.ts`;
4. `apps/backend/test/brake-data.test.mjs`; and
5. `apps/backend/test/backend.test.mjs`.

Every migration, package/lock file, public export, Dashboard file, SSE schema,
deployment path and any sixth product file is read-only. A need to change one
stops execution and returns a bounded change request.

## Exact Proposed Behavior

### Route, scope and errors

1. Add only `GET /api/v1/brake/units/{systemUid}/windows/{eventId}` on the
   existing loopback public composition root. Every other method or route keeps
   the existing closed behavior.
2. Authorize decoded `systemUid` against the injected closed
   `CurrentUnitContext` before any event lookup. A missing/invalid context is
   `503 CURRENT_UNIT_CONTEXT_UNAVAILABLE`; a non-current Unit is `404
   UNIT_NOT_CURRENT` without confirming whether the event exists.
3. Accept only a lowercase UUIDv4 `eventId`. Invalid path encoding, event ID or
   any query key—including `limit` and `cursor`—is `400 INVALID_REQUEST`.
4. A valid current Unit with no query-visible exact event returns `404
   NOT_FOUND`. A later chunk stored before chunk 0/completion remains hidden and
   therefore also returns `404 NOT_FOUND`.
5. Existing closed error bodies and `cache-control: no-store` apply. No new
   error code, authentication claim, listener or Cloud lookup is added.

### Factual response and ordering

1. Return the closed `window-detail.schema.json` body: exact request Unit/role,
   the same factual window item as the collection projection and an array of
   zero through 150 accepted stored samples.
2. Read chunk content for the exact Unit/event in ascending `chunk_index` and
   append each stored sample array without changing its order. Preserve every
   sample index, PRE/ACTIVE/POST phase, quality, source time, source-age and
   signal value. Do not interpolate, infer, phase-sort, deduplicate or fabricate
   data.
3. Zero samples is valid when a completion created a visible `PARTIAL` window
   before any chunk arrived. `GROWING`, `PARTIAL`, `TERMINAL` and
   `QUARANTINED` return only the exact current projection and accepted stored
   samples. Attempted conflicting quarantine content is never returned as an
   accepted sample.
4. Verify parsed stored canonical content against the joined accepted message
   Unit/event/chunk identity and `content_sha256` before response. Malformed,
   noncanonical, digest-mismatched or otherwise corrupt stored content fails
   closed as retryable `503 TEMPORARILY_UNAVAILABLE`; no partial detail body is
   emitted.
5. The point read has no page, limit, cursor, history, snapshot-isolation,
   freshness or synchronization-complete semantics. `backendReceivedAt` remains
   the existing projection receipt time, not a claim that vehicle data is now
   fresh.

### Preserved behavior and persistence

1. The four collection routes, response schema/body version 1.0.0, ordering,
   keyset paging, empty-page behavior and all existing tests remain unchanged.
2. SSE remains change notification only and carries no detail payload. Clients
   still authoritatively re-read REST after notification/reconnect/gap/restart.
3. SQLite `BUSY`/`LOCKED` remains a retryable `503` without permanently
   latching the backend unavailable. Closed/corrupt storage remains fail
   closed under the accepted data-service behavior.
4. Migration 002 already stores canonical validated `content_json` and has the
   exact Unit/event/chunk index. No migration, table, column or index change is
   needed or permitted.

## Required Deterministic Verification

Targeted tests must prove:

1. exact terminal detail at the 150-sample bound and the 151st sample is
   impossible under accepted storage/schema bounds;
2. completion-first visible `PARTIAL` detail with zero samples;
3. `GROWING` and gapped/out-of-order `PARTIAL` details return only accepted
   samples in exact chunk/stored-array order;
4. `QUARANTINED`/`CONFLICT` returns its exact factual projection and accepted
   samples without false terminal or attempted-conflict content;
5. a later-chunk-only hidden event returns `404 NOT_FOUND` and no SSE/detail
   projection;
6. Test/Production equal event IDs remain isolated; wrong Unit returns
   `UNIT_NOT_CURRENT` before event existence, missing context is 503 and a
   missing exact current-Unit event is `NOT_FOUND`;
7. malformed UUID/path encoding, every query parameter and repeated parameter
   return `INVALID_REQUEST`; there is no limit/cursor/next-cursor field;
8. source values, phase, index, timestamp, quality and age are byte/value
   equivalent to stored accepted content;
9. malformed/noncanonical/digest- or identity-mismatched stored content returns
   503 without a partial response; SQLite busy is retryable and does not latch;
10. the existing collection golden response, all cursor/order tests, SSE wire
    body and migration 002 SHA-256 remain unchanged.

After targeted tests, the future worker must run offline from already
materialized dependencies:

```text
npm_config_offline=true npm run typecheck
npm_config_offline=true npm run test
npm_config_offline=true npm run build
npm_config_offline=true npm run quality
git diff --check
```

The final gate proves only the five declared paths changed; every migration,
lockfile, collection fixture, generated output, dependency cache and credential
remains outside the commit. Any cache miss or attempted dependency retrieval
stops execution; this packet grants no `npm ci` or registry access.

## Explicit Exclusions

- no Dashboard rendering, chart, browser adapter or UI route;
- no collection, paging, SSE, CurrentUnitContext, cleanup or ingestion change;
- no schema migration, repair, history/snapshot store or backup;
- no production backend authentication or `system_uid` identity claim;
- no D4-024 run/source-generation or comparative-success binding;
- no Docker/ARM64 packaging, QEMU route, Service sender or live integration;
- no dependency, lockfile, build-tool or public-package change;
- no signing, publication, Cloud, VM, Unit, CARLA, container or external
  network operation; and
- no merge, push or mutation of any main branch.

## Exit and Handoff

After separate authorization, exit requires one clean local product commit
over exact `1320dde`, the five-path boundary, all targeted/full offline gates,
unchanged migration/lock/collection/SSE bytes and an independent source review.
It proves only the isolated backend detail read. Dashboard use, container/live
integration and qualification remain owned by later packets.
