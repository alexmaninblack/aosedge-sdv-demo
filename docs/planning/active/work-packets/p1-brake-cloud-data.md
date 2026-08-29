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
   receipt separate from terminal-window state and withholding projection of
   later out-of-order chunks until authoritative window start is known;
5. persist and expose v2 assessments/events and v3 advisory facts while
   keeping event VDP provenance nullable/pending until exact assessment
   correlation;
6. expose the closed Query/SSE/Admin API 1.0.0 annex; and
7. preview and atomically delete records for exactly the current Test Vehicle
   and Production Vehicle Unit UIDs supplied through the injected closed
   `CurrentUnitContext` sourced from the provisioning journal.

The internal wire role `VALIDATION` maps to the user-facing label **Test
Vehicle**. This packet adds no Dashboard rendering, live adapter, deployment or
composed demo proof. Its exit would mean only that the isolated backend data
slice passes deterministic source tests.

## Frozen Repositories and Inputs

The proposed product branch must start from the exact isolated foundation
commit above, whose parent is governance base
`6da2926ba96df5e470bfbc3514e983f5d54c3975`. The documentation/contract
cascade was prepared from clean `aosedge-sdv-demo@d54fbc4ced3b1083dbf686d7aa559e009638d2f7`.

| Input | Frozen identity |
| --- | --- |
| `CR-BRAKE-CLOUD` | SHA-256 `3d57f85e7ca64d0d766061122756c5a93a3d4868d24a80698bcbbf91f03da624` |
| D4 Decision Register | SHA-256 `cd26226ce4a51cc2ab21bbee8c53157a48b38c518f9ee75bbe518791b067f488` |
| Foundation work packet | SHA-256 `27f1ebfea993ac9af6727296b63de4cabc0bcd55fa1fdc0f12f1fe4a25e0fd1f` |
| Brake Cloud API README | SHA-256 `41d5ced4bb51108c898e165fbe7b9a9f81d0024219fd28299e5bb705e7135a56` |
| Brake Cloud API profile 1.0.0 | SHA-256 `b539571d80d76fa11234f3e41b0646ff6d6c4235be5de933448ebc9fafeb3891` |
| Query/SSE/Admin API annex 1.0.0 | SHA-256 `2b04089106b8263ff1efd68240623168f4dcf9d1bf6d92748ed253a3ba8ad29c` |
| Current Unit context schema/fixture | SHA-256 `f5733d7750b2fbda863201f66503e40f97c146f426ff4ec290f195efdcca4681`, `c9b623b368dd17053a94fbc612375f8aae14d2e99026325a4ce9cb5c5742d022` |
| Durable ACK schema | SHA-256 `778f176d85ccdb7c177380c145783a4c0d2c26d1324759f972f02765cc3e68d9` |
| Advisory-fact schema | SHA-256 `41bf4de82143077fd6bb675abb63150ad5d886f9e5f4d3547585c50bfb79d67a` |
| Corrected advisory fixture | SHA-256 `a2dc0c016d5281c9accead1d6447600d4a2c3736acaef1f725a2831efe334cad` |
| Query page / error / SSE schemas | SHA-256 `17b13d55462e97ca2011391e1ce78e272124839b1851cfcf675ad9434d802c38`, `53ff0a6073f6d3eb51e67165d62bdc512bcd98c2d200690f8607ee146d4ea30b`, `7e8bccc76167722910e9c671f46223caf53708a29758587906a4afcac4356d1b` |
| Pending-VDP query fixture | SHA-256 `3056242db14d4c97a7cbf1e33fe6e388c8a6447b6bccb471407869db9d2b49b6` |
| Cleanup preview/request/execute/result schemas | SHA-256 `83f2db9864f75d8199d77a949d5af20800010ec2c3f9df2902082e9164990b93`, `161ed28ddbadd2c3c2938409cba46eafd8f7e26b99aa08f62dfeaf87d1fc67b3`, `067eedf0dfb568cb678c90492e4d0c47e598dbf97447887532c1de4e42668083`, `52bd4a7fc58954e314c440c8359a85c4b58cbf6f85e5bcedbea299555d788f30` |
| Cleanup preview/execute fixtures | SHA-256 `3fd5f314f523f72a1039026b18feab256762dd67af453b624db411105682b1f3`, `9758cef03207c09ae6b11754a6b729ce939da20964ddc737fa2aee264a9daebb` |
| RFC8785 edge-vector schema/fixture | SHA-256 `d07bae7bba564654b6054da4b5e2819940e30b9a1dede7f7a31bcf35d26ecd10`, `b00fb380b53d53ef2c9d3ced96497787426ba4ee14547937c36e57a04c0060c2` |
| v1 window contract README/chunk/completion | SHA-256 `c8abce17f99c33f10cf4e245b9e9139e94c35525414828f1402c7975d9a78dc8`, `6166d196b15017d0b6ddc6be7ba94548fff11cc2b260daafb804fe9c1a532b32`, `0dc9b3f89d1bf3a3c7c790aafd3f8972aed0f5b9e437a07bd19934ea194bac31` |
| v2 model README/assessment/event | SHA-256 `7b51ffb474c8271542d6aca3cd0b0a2473d9d6f48f0209625fcd77957c2e850c`, `0c47d793bb4e31852c0452b92c901514d582c16a479f7107d15e02f0d22dc1e9`, `d88bf8882f68b25980dc23987149d4f57c25eee7bed371af419998a053a55e66` |
| Immutable product migration `001_initialize.sql` | SHA-256 `367e6cf3f51ae0abf15cf4b9fbd5ff4923f69096fb58c4cd5dc7533df6def2dd` |
| Foundation migration runner | SHA-256 `7ca9c06822f68ff1d0126a3c4bff2634ca635c2639fcffc58aca86fa2f20b0d9` |
| Foundation Node type shims | SHA-256 `517098a91f197f62f0559974e6854cd7e8c8f5ca38027901c594f11033d83308` |
| Foundation lockfile | SHA-256 `26ef2251179f7cde0978ed8aeff3b1e6863bff7e9d1884d814951a9f1c72a7cc` |

Any base or digest mismatch stops the future packet. The worker must not
reinterpret, regenerate or copy solution contracts into product history.

## Exact Future Writable Boundary

After explicit authorization, only these twenty-two product files may change or
be created:

1. `package-lock.json` — workspace-edge metadata only; no external package;
2. `apps/backend/package.json` — internal workspace dependencies only;
3. `apps/backend/tsconfig.build.json` — compile the accepted internal layers;
4. `apps/backend/src/index.ts`;
5. `apps/backend/src/main.ts`;
6. `apps/backend/src/migrations.ts`;
7. `apps/backend/src/node-shims.d.ts` — only the minimal Node built-in
   declarations required by this packet's accepted source;
8. `apps/backend/src/server.ts`;
9. `apps/backend/src/brake-data-contract.ts` — transport-independent parsing,
   canonical digest and closed error mapping;
10. `apps/backend/src/brake-data-domain.ts` — reconstruction/idempotency state;
11. `apps/backend/src/brake-data-store.ts` — SQLite transactions and queries;
12. `apps/backend/src/brake-data-http.ts` — ingestion, REST, SSE and admin
    composition without deployment configuration;
13. `apps/backend/test/backend.test.mjs`;
14. `apps/backend/test/brake-data.test.mjs` — new;
15. `migrations/002_brake_data.sql` — new;
16. `packages/contracts/src/index.ts`;
17. `packages/contracts/src/index.test.ts`;
18. `packages/domain/src/index.ts`;
19. `packages/domain/src/index.test.ts`;
20. `packages/test-support/src/index.ts`;
21. `packages/test-support/src/index.test.ts`; and
22. `tests/architecture.test.ts` — permit only the declared public internal
    backend edges and reject cross-layer relative imports.

The architecture-suite change is limited to the declared public internal
backend edges and a new rejection of cross-layer relative imports; every other
architecture rule remains unchanged. A need to change `001_initialize.sql`, a
Dashboard file, root dependency/version, quality tool, deployment path or any
twenty-third file stops execution and returns a bounded change request.

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
   inconsistent complete set is quarantined and remains non-terminal. A valid
   later out-of-order chunk is persisted and ACKed, but the window is withheld
   from Query/SSE projection until authoritative start is known from chunk 0
   first-sample time or completion `windowStartTimestamp`. When both exist they
   must match; a mismatch is quarantined and remains non-terminal.
5. Preserve immutable message source/local timestamps separately from
   `backendReceivedAt`. Record duplicate and out-of-order facts. Do not create
   `synchronizationCompletedAt`, an outbox-drained flag, retired-run rejection,
   source generation or a VU/PU comparative-success result.
6. Exact Unit identity prevents equal logical IDs on Test and Production Units
   from colliding. No record or table contains `demoRunId`.
7. Event query projection exposes `vdpProvenanceState`, nullable
   `vdpContractVersion` and nullable `vdpContractSha256`. The latter two remain
   null in `PENDING_ASSESSMENT_CORRELATION` and become non-null only after exact
   correlation to the assessment's Unit, assessment/source-event identity,
   service artifact and model/config provenance. No Unit, receipt, time or
   release-state inference is allowed.

## Exact Query, SSE and Cleanup Semantics

- Construction requires one schema-valid injected `CurrentUnitContext` with
  exactly the current Test Vehicle UID/`VALIDATION` role and Production Vehicle
  UID/`PRODUCTION` role, distinct UIDs and source
  `CURRENT_RUN_PROVISIONING_JOURNAL`. It contains no Cloud lifecycle/readiness
  state and triggers no Cloud lookup or inference. Live provisioning-journal
  adapter wiring is deferred to `BRAKE-CLOUD-INTEGRATION-001`. Missing or
  invalid context is `503 CURRENT_UNIT_CONTEXT_UNAVAILABLE` and starts no SSE
  stream.
- Implement the four GET collections and closed page schema exactly as the
  annex freezes them: resource-specific descending order, opaque keyset cursor,
  limits `1..100`, default 50, `nextCursor: null` at end and `400
  INVALID_CURSOR` for malformed or cross-Unit/resource cursors. A valid current
  Unit with no rows returns a truthful empty `200`; a Unit outside the injected
  context is `404 UNIT_NOT_CURRENT`. There is no snapshot/full-synchronization
  claim.
- Implement `/stream` as `text/event-stream` change notification only, with
  exact `systemUid`, named `brake-data-changed` events, closed JSON data and a
  monotonic unsigned decimal ID per process. No message or projection state is
  carried in SSE. Every notification/reconnect/gap/restart requires the client
  to re-read REST; backpressure closes the stream.
- Implement cleanup on a separate mode-`0600`
  `/run/brake-health-cloud/admin.sock` Unix-domain HTTP composition root. It is
  not mounted or exposed to browser, guest ingestion or LAN in this packet.
- Preview and execute accept exactly the same two-element selector containing
  current Test Vehicle and Production Vehicle `system_uid` values from the
  injected context, strictly sorted by UID with no positional role meaning.
  There is no `demoRunId` or time field. Preview includes `contractVersion:
  "1.0.0"`.
- `recordSetSha256` is SHA-256 of RFC-8785 canonical JSON whose top level is an
  array of `[tableName, rows]` pairs in exact order `messages`, `windows`,
  `assessments`, `events`, `advisories`, `quarantine`, including empty table
  blocks. Each row is a JSON array of the exact fields and order frozen in the
  annex; rows sort lexicographically by their canonical-row UTF-8 bytes.
  Duplicate JSON keys are rejected before canonicalization. The nonmatching
  digest uses the same shape for the exact complement.
- Preview token TTL is 60 seconds and binds the sorted UIDs, exact six record
  counts, record-set digest and expiry in the annex's canonical payload. The
  HMAC-SHA-256 key is random, process-local, not persisted, logged or returned;
  comparison is constant-time and the token maximum is 1024 characters.
  Malformed, bad-MAC, expired and previous-process/restart tokens all return
  `409 PREVIEW_TOKEN_EXPIRED` and require a new preview. Only a structurally
  valid, valid-MAC token whose bound current row set has changed returns `409
  PREVIEW_STALE`. Both failures delete nothing. One transaction deletes
  matching messages and cascading projections/receipts/quarantine, proves all
  six matching counts are zero and returns the unchanged nonmatching digest. An
  uncertain response is reconciled by preview/re-read, never blind repeat.

## Required Deterministic Verification

The future implementation must use temporary databases/socket paths and pass:

1. fresh v2, repeat v2, exact v1-to-v2 ledger transition, injected post-drop
   rollback and unknown-v3 refusal;
2. closed validation and exact RFC-8785 digest checks for all five messages,
   including the corrected advisory fixture; plus Unicode UTF-16 property
   ordering, ECMAScript numeric serialization and duplicate-key rejection edge
   vectors;
3. new/duplicate/conflict behavior, original receipt reuse, transaction failure,
   busy/full/unavailable behavior and restart persistence;
4. ordered/reordered/missing/conflicting chunks, completion-before-chunks,
   later-chunk durable ACK with no projection before authoritative start,
   chunk-0/completion start agreement, partial/terminal/quarantine projection
   and exact Unit isolation;
5. v2 assessment/event and v3 advisory persistence with immutable
   source/local/receipt time separation, pending/null then exact-correlated VDP
   provenance and no inferred or forbidden sync/run fields;
6. every query route/order/limit/cursor edge, empty exact Unit, cross-scope
   cursor, injected-context validation, truthful current-Unit empty page,
   non-current Unit and closed error/status mapping;
7. SSE exact wire event, monotonic ID, no state payload, gap/reconnect/restart
   REST-reread rule and deterministic backpressure closure;
8. admin socket path/mode/composition isolation; sorted exact two-UID preview,
   wildcard/empty/one/three/unsorted/duplicate negatives, no run/time fields,
   `contractVersion`, exact six-table/field/order RFC-8785 digest, duplicate-key
   rejection, token lengths 1024/1025, malformed/bad-MAC/expired/previous-process
   mapping to `409 PREVIEW_TOKEN_EXPIRED`, valid-MAC changed-row-set mapping to
   `409 PREVIEW_STALE`, atomic delete, zero matching rows and unchanged
   nonmatching digest;
9. strict typecheck, all Node/Vitest/architecture regressions, production build,
   lockfile/direct-dependency and repository quality gates; and
10. a boundary scan proving that only the twenty-two files changed and no
    generated output, dependency cache or credential entered the commit.

The minimum commands after authorization are:

```text
npm run typecheck
npm run test
npm run build
npm run quality
git diff --check
```

After explicit packet authorization, exactly one dependency materialization is
allowed only from a verified content-addressed npm cache outside the repository
against the frozen lock, with scripts, audit, funding and network disabled:

```text
npm_config_offline=true npm ci --offline --ignore-scripts --no-audit --no-fund
```

A cache miss, any attempted registry/network access, lifecycle script, package
or version change, or lockfile change beyond the declared internal workspace
metadata stops the packet. The ignored materialized `node_modules/` tree is a
transient test prerequisite, not product source or a twenty-third writable
file; it must not enter the commit and is removed with the isolated worktree.
No dependency download is authorized.

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
- no new npm dependency, network/dependency download, lifecycle script,
  generated build output in the commit or copied solution contract; the one
  exact offline frozen-lock materialization above is the only dependency
  operation eligible for later authorization;
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
must explicitly accept the exact objective, frozen inputs, twenty-two-file
boundary, v2 ledger transition, query/SSE/admin annex, tests, exclusions and partial-exit
meaning before implementation begins. Any change outside them returns a
bounded change request rather than being absorbed into the packet.
