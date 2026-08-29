<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Cloud Data Implementation Work Packet

- ID: `WP-P1-BRAKE-CLOUD-DATA-001`
- Lane: `L-BRAKE-CLOUD`
- Increment: `IMP-04-BRAKE-CLOUD-DATA-001`
- State: `PROPOSED — REVIEW REQUIRED`
- Version: 0.1
- Prepared: 2026-08-29
- Implementation authorized: no
- Repository: `brake-health-cloud`
- Frozen base: `68fe61b292b0b9671b1af0dc1881fe37dc5f97de`
- Proposed branch: `codex/imp-04-brake-cloud-data`
- Proposed isolated worktree: `brake-health-cloud-imp-04-data`
- Integration owner: Demo Integration Coordinator
- Dependency retrieval, product edit, commit, push or merge authorized: no
- Cloud, helper, credential, container, VM, Unit, CARLA, signing, publication
  or live operation authorized: no
- Previous implemented slice:
  [WP-P1-BRAKE-CLOUD-FOUNDATION-001](p1-brake-cloud-foundation.md)

## Objective

On separate review and explicit implementation authorization, add the smallest
source-only Brake data backend over the completed foundation:

1. transactionally upgrade the immutable v1 foundation database to schema v2;
2. validate and durably ingest the five accepted Brake logical message kinds;
3. return the accepted idempotent durable acknowledgement and quarantine
   same-key/different-content conflicts;
4. reconstruct factual v1 projections while keeping a durable completion
   receipt separate from terminal-window state;
5. persist and expose v2 assessments/events and v3 advisory facts;
6. expose the closed Query/SSE/Admin API 1.0.0 annex; and
7. preview and atomically delete records for exactly the current Test Vehicle
   and Production Vehicle Unit UIDs.

The internal wire role `VALIDATION` maps to the user-facing label **Test
Vehicle**. This packet adds no Dashboard rendering, live adapter, deployment or
composed demo proof. Its exit would mean only that the isolated backend data
slice passes deterministic source tests.

## Frozen Repositories and Inputs

The proposed product branch must start from the exact isolated foundation
commit above, whose parent is governance base
`6da2926ba96df5e470bfbc3514e983f5d54c3975`. The documentation/contract
cascade was prepared from clean `aosedge-sdv-demo@b861cc97940b5d8445a6b237a9d26f1b609cd38a`.

| Input | Frozen identity |
| --- | --- |
| `CR-BRAKE-CLOUD` | SHA-256 `92501070b4bf7a7a8a8a4cc790e6a42f2286fbc0bdb178d02646b0bbd023185f` |
| D4 Decision Register | SHA-256 `c1f0fd85ac756888ba2199f5d68d4475c1546fe3aaaf308f3cce0f9fb665a7e7` |
| Foundation work packet | SHA-256 `27f1ebfea993ac9af6727296b63de4cabc0bcd55fa1fdc0f12f1fe4a25e0fd1f` |
| Brake Cloud API README | SHA-256 `f87359c4d8af77a4cfd7f2b345e1df59e66b280359c43a1fc392cb039a5441cc` |
| Brake Cloud API profile 1.0.0 | SHA-256 `b48f9f2f74a702f0aadfd895d87fc680ea4726255e35931fe75bedff2f7a5877` |
| Query/SSE/Admin API annex 1.0.0 | SHA-256 `4b123874a3809659cd3a807b5032778210fa4ea425481b014334bbcfa40c0366` |
| Durable ACK schema | SHA-256 `778f176d85ccdb7c177380c145783a4c0d2c26d1324759f972f02765cc3e68d9` |
| Advisory-fact schema | SHA-256 `41bf4de82143077fd6bb675abb63150ad5d886f9e5f4d3547585c50bfb79d67a` |
| Corrected advisory fixture | SHA-256 `a2dc0c016d5281c9accead1d6447600d4a2c3736acaef1f725a2831efe334cad` |
| Query page / error / SSE schemas | SHA-256 `5e02e92273a05ea55d3b2829e3c37542a0a71b366440a48e7e0760328e66e36e`, `3abca7ea13db3582a18fa3871e26e31299a2abee3bd28c885cf607d82754ab2d`, `7e8bccc76167722910e9c671f46223caf53708a29758587906a4afcac4356d1b` |
| Cleanup preview/request/execute/result schemas | SHA-256 `99bb4e00c124687dfdd54df578f9b315e229f61ddcd78f087b0cd007f5c72310`, `161ed28ddbadd2c3c2938409cba46eafd8f7e26b99aa08f62dfeaf87d1fc67b3`, `eee8049f5e54f6cb9b74f6d43517803d6a789e8c4415c890296612209590c2c7`, `52bd4a7fc58954e314c440c8359a85c4b58cbf6f85e5bcedbea299555d788f30` |
| v1 window contract README/chunk/completion | SHA-256 `c8abce17f99c33f10cf4e245b9e9139e94c35525414828f1402c7975d9a78dc8`, `6166d196b15017d0b6ddc6be7ba94548fff11cc2b260daafb804fe9c1a532b32`, `0dc9b3f89d1bf3a3c7c790aafd3f8972aed0f5b9e437a07bd19934ea194bac31` |
| v2 model README/assessment/event | SHA-256 `7b51ffb474c8271542d6aca3cd0b0a2473d9d6f48f0209625fcd77957c2e850c`, `0c47d793bb4e31852c0452b92c901514d582c16a479f7107d15e02f0d22dc1e9`, `d88bf8882f68b25980dc23987149d4f57c25eee7bed371af419998a053a55e66` |
| Immutable product migration `001_initialize.sql` | SHA-256 `367e6cf3f51ae0abf15cf4b9fbd5ff4923f69096fb58c4cd5dc7533df6def2dd` |
| Foundation migration runner | SHA-256 `7ca9c06822f68ff1d0126a3c4bff2634ca635c2639fcffc58aca86fa2f20b0d9` |
| Foundation lockfile | SHA-256 `26ef2251179f7cde0978ed8aeff3b1e6863bff7e9d1884d814951a9f1c72a7cc` |

Any base or digest mismatch stops the future packet. The worker must not
reinterpret, regenerate or copy solution contracts into product history.

## Exact Future Writable Boundary

After explicit authorization, only these twenty-one product files may change or
be created:

1. `package-lock.json` — workspace-edge metadata only; no external package;
2. `apps/backend/package.json` — internal workspace dependencies only;
3. `apps/backend/tsconfig.build.json` — compile the accepted internal layers;
4. `apps/backend/src/index.ts`;
5. `apps/backend/src/main.ts`;
6. `apps/backend/src/migrations.ts`;
7. `apps/backend/src/server.ts`;
8. `apps/backend/src/brake-data-contract.ts` — transport-independent parsing,
   canonical digest and closed error mapping;
9. `apps/backend/src/brake-data-domain.ts` — reconstruction/idempotency state;
10. `apps/backend/src/brake-data-store.ts` — SQLite transactions and queries;
11. `apps/backend/src/brake-data-http.ts` — ingestion, REST, SSE and admin
    composition without deployment configuration;
12. `apps/backend/test/backend.test.mjs`;
13. `apps/backend/test/brake-data.test.mjs` — new;
14. `migrations/002_brake_data.sql` — new;
15. `packages/contracts/src/index.ts`;
16. `packages/contracts/src/index.test.ts`;
17. `packages/domain/src/index.ts`;
18. `packages/domain/src/index.test.ts`;
19. `packages/test-support/src/index.ts`; and
20. `packages/test-support/src/index.test.ts`; and
21. `tests/architecture.test.ts` — permit only the declared public internal
    backend edges and reject cross-layer relative imports.

The architecture-suite change is limited to the declared public internal
backend edges and a new rejection of cross-layer relative imports; every other
architecture rule remains unchanged. A need to change `001_initialize.sql`, a
Dashboard file, root dependency/version, quality tool, deployment path or any
twenty-second file stops execution and returns a bounded change request.

## Exact Migration v2

`001_initialize.sql` is immutable. It continues to create only historic table
`schema_migrations(version INTEGER PRIMARY KEY, name TEXT NOT NULL,
applied_at TEXT NOT NULL) STRICT`.

`002_brake_data.sql` is one transaction under the runner's existing
`BEGIN IMMEDIATE` boundary and shall:

1. create strict `schema_version` with the same three columns;
2. copy the v1 row from `schema_migrations` and then drop only that legacy
   table;
3. create strict tables `messages`, `receipts`, `window_chunks`,
   `window_completions`, `windows`, `assessments`, `condition_events`,
   `advisory_facts` and `quarantine`;
4. use integer primary keys/FKs, exact `unit_system_uid`, closed `unit_role`
   and `message_type` checks, lowercase 64-hex digest length checks, canonical
   JSON text, immutable source time and `backend_received_at`;
5. make `(unit_system_uid, message_type, message_identity)` unique in
   `messages`, make each receipt one-to-one with its message, make
   `(unit_system_uid, event_id, chunk_index)` unique for chunks and every typed
   message identity unique within its Unit;
6. cascade typed rows and receipts only from their owning `messages` row;
7. index every exact-Unit resource ordering key and the quarantine Unit/key;
8. let the runner insert `(2, 'brake_data', appliedAt)` into
   `schema_version` and set `PRAGMA user_version = 2` before commit.

The runner shall discover `schema_version` when present and otherwise
`schema_migrations`. It records each migration in the ledger selected after
that migration SQL executes. Fresh v2, repeat v2 and v1-to-v2 upgrade must
produce the same two ledger rows. An injected failure after the legacy table
drop must roll back every v2 table, retain the v1 legacy ledger and retain
`user_version = 1`. Unknown version 3 remains `NOT_READY`; downgrade or reset
is forbidden.

## Exact Data and Receipt Semantics

1. Accept only `WINDOW_CHUNK`, `WINDOW_COMPLETION`,
   `BRAKE_HEALTH_ASSESSMENT`, `BRAKE_HEALTH_EVENT` and
   `BRAKE_ADVISORY_FACT` under their frozen schemas and size limits.
2. Verify RFC-8785 `contentSha256`; derive the exact accepted idempotency-key
   array and its SHA-256. Invalid data is `422`; oversized wire content is
   `413`; database unavailability is `503` without ACK.
3. One serialized transaction performs idempotency check, immutable message
   insert, typed row/projection update and receipt insert. New data returns
   `201 DURABLE_ACCEPTED`; an identical retry returns `200
   DUPLICATE_ACCEPTED` with the original receipt ID/time. Same key/different
   digest returns `409 CONTENT_CONFLICT`, records quarantine and never replaces
   the accepted row.
4. A schema-valid completion is inserted and ACKed even if chunks are missing.
   Its window projection remains `PARTIAL` and non-terminal. Only the complete
   ordered chunk index set with matching digests, sample/phase counts,
   terminal-state pairing and `windowSha256` creates `TERMINAL`. An
   inconsistent complete set is quarantined and remains non-terminal.
5. Preserve immutable message source/local timestamps separately from
   `backendReceivedAt`. Record duplicate and out-of-order facts. Do not create
   `synchronizationCompletedAt`, an outbox-drained flag, retired-run rejection,
   source generation or a VU/PU comparative-success result.
6. Exact Unit identity prevents equal logical IDs on Test and Production Units
   from colliding. No record or table contains `demoRunId`.

## Exact Query, SSE and Cleanup Semantics

- Implement the four GET collections and closed page schema exactly as the
  annex freezes them: resource-specific descending order, opaque keyset cursor,
  limits `1..100`, default 50, `nextCursor: null` at end and `400
  INVALID_CURSOR` for malformed or cross-Unit/resource cursors. There is no
  snapshot/full-synchronization claim.
- Implement `/stream` as `text/event-stream` change notification only, with
  exact `systemUid`, named `brake-data-changed` events, closed JSON data and a
  monotonic unsigned decimal ID per process. No message or projection state is
  carried in SSE. Every notification/reconnect/gap/restart requires the client
  to re-read REST; backpressure closes the stream.
- Implement cleanup on a separate mode-`0600`
  `/run/brake-health-cloud/admin.sock` Unix-domain HTTP composition root. It is
  not mounted or exposed to browser, guest ingestion or LAN in this packet.
- Preview and execute accept exactly the same two-element selector containing
  the current Test Vehicle and Production Vehicle `system_uid` values from the
  Orchestrator provisioning journal, strictly sorted by UID with no positional
  role meaning. There is no `demoRunId` or time field.
- Preview token TTL is 60 seconds and binds the sorted UIDs, exact six record
  counts, record-set digest and expiry. Execute with a stale/expired token is a
  closed `409` and deletes nothing. One transaction deletes matching messages
  and cascading projections/receipts/quarantine, proves all six matching counts
  are zero and returns the unchanged nonmatching digest. An uncertain response
  is reconciled by preview/re-read, never blind repeat.

## Required Deterministic Verification

The future implementation must use temporary databases/socket paths and pass:

1. fresh v2, repeat v2, exact v1-to-v2 ledger transition, injected post-drop
   rollback and unknown-v3 refusal;
2. closed validation and exact RFC-8785 digest checks for all five messages,
   including the corrected advisory fixture;
3. new/duplicate/conflict behavior, original receipt reuse, transaction failure,
   busy/full/unavailable behavior and restart persistence;
4. ordered/reordered/missing/conflicting chunks, completion-before-chunks,
   partial/terminal/quarantine projection and exact Unit isolation;
5. v2 assessment/event and v3 advisory persistence with immutable
   source/local/receipt time separation and no forbidden sync/run fields;
6. every query route/order/limit/cursor edge, empty exact Unit, cross-scope
   cursor and closed error/status mapping;
7. SSE exact wire event, monotonic ID, no state payload, gap/reconnect/restart
   REST-reread rule and deterministic backpressure closure;
8. admin socket path/mode/composition isolation; sorted exact two-UID preview,
   wildcard/empty/one/three/unsorted/duplicate negatives, no run/time fields,
   stale/expired token, atomic delete, zero matching rows and unchanged
   nonmatching digest;
9. strict typecheck, all Node/Vitest/architecture regressions, production build,
   lockfile/direct-dependency and repository quality gates; and
10. a boundary scan proving that only the twenty-one files changed and no
    generated output, dependency cache or credential entered the commit.

The minimum commands after authorization are:

```text
npm run typecheck
npm run test
npm run build
npm run quality
git diff --check
```

No dependency installation or retrieval is part of this packet. The exact
foundation dependency tree must already be available. Missing dependencies
stop the packet rather than authorizing network access.

## Explicit Exclusions and Deferred Proof

- no Dashboard UI behavior, `EventSource` browser adapter, chart, catalogue,
  release helper or Service Logs implementation;
- no D4-024 watermark, `synchronizationCompletedAt`, outbox-drain proof,
  retired-run rejection, run/source-generation binding, live source ownership
  or Test/Production comparative-success claim;
- no HTTP client/backend authentication, KAC, KUKSA, Gateway, Brake Service,
  AosCloud or publication-helper adapter;
- no retention scheduler, historic archive, backup or query snapshot claim;
- no Dockerfile, Compose, ARM64 image, persistent-volume deployment or QEMU
  route;
- no new npm dependency, dependency download, generated build output or copied
  solution contract;
- no credential, key, certificate, token provisioning or personal path;
- no signing, publication, Cloud, VM, Unit, CARLA, FOTA, container, external
  network or live operation; and
- no push, merge or mutation of any main branch.

`REQ-BRAKE-CLOUD-010` is covered only for deterministic delayed/out-of-order
data facts; reconnect/outbox convergence remains integration work.
`REQ-BRAKE-CLOUD-011` is covered only for exact Unit isolation.
`REQ-BRAKE-CLOUD-012`, D4-024 run/source-generation binding and the composed
success claim are wholly deferred.

## Authorization Gate

This document is a proposed packet only. It does not authorize creation of the
branch/worktree, product edits, tests, dependency access or a commit. Reviewers
must explicitly accept the exact objective, frozen inputs, twenty-one-file
boundary, v2 ledger transition, query/SSE/admin annex, tests, exclusions and partial-exit
meaning before implementation begins. Any change outside them returns a
bounded change request rather than being absorbed into the packet.
