<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Cloud API — Accepted Contract

Implementation and qualification: [protocol status](../implementation-status.md).

- Decision: `D4-017`
- Lifecycle state: `ACCEPTED`
- Accepted contract version: `1.0.0`
- Additive Query/SSE/Admin profile: `1.1.0`
- Window detail decision: `BC-WINDOW-DETAIL-DEC-01`
- Subdecision state: transport, first-demo security boundary, idempotency,
  durable acknowledgement, persistence, Dashboard query/authority and exact
  current-run cleanup accepted 2026-08-23

## Current product messages

New products use `schemaVersion: 2`, `contractVersion: "2.0.0"` and
[native product provenance](../service-runtime-inputs/product-message-migration.md):
the immutable package release and native service/Subject/instance identity.
`serviceArtifactSha256` and `modelArtifactSha256` are absent and rejected in
new products. The current [advisory fact](brake-advisory-fact.v2.schema.json),
[query page](query-page.v2.schema.json) and [window detail](window-detail.v2.schema.json)
schemas distinguish native and retained legacy records explicitly. Stored v1
messages keep their original bytes; query envelopes do not upgrade them.
Function observations use their separate [v3 contract](../service-function-observation/v3-contract.md).

Wire revisions do not replace this API family's accepted version, durable ACK,
SSE, context or [current administration](current-admin-profile.v1.json).
The transport, storage, query and cleanup rules below remain current; only the
explicitly identified legacy formats have compatibility-only scope.

## Current context and lifecycle

Use one current Test UID in installed Studio; dual-role context is an explicit
engineering profile, not a hidden Production vehicle. The handlers reject
empty, duplicate, foreign and unrelated partial selectors. Keep the current UID
bound through scoped Finish cleanup, then clear it. Backend restart and ordinary
Stop preserve the database; Finish deletes only selected run records. Neither
ingestion health nor context readiness proves a live analytic result.

This package freezes the accepted current-demo transport boundary between the
Brake Health in-vehicle Service and the Mac-hosted Brake Health Cloud product.
It does not change the accepted logical Brake messages. Canonical message bytes
and their SHA-256 remain authoritative even when HTTP content encoding is used.

The first demo uses one logical message per HTTP request over an isolated local
QEMU-to-Mac route. An asynchronous sender reads the bounded persistent Service
outbox, so backend delivery, timeout and retry cannot block KUKSA consumption,
local analytics or advisory. Durable acknowledgement is returned only after a
transactional SQLite commit; transport success without that acknowledgement
never allows the Service to delete its local message.

No per-Unit backend client credential, certificate provisioning, rotation or
retirement belongs to this demo contract. Production backend authentication is
owned by Function Team 1 and is explicitly outside the first-demo claim. That
simplification does not create a public endpoint: D4-020 must qualify the
guest-visible route and prove that ingestion has no LAN or public-network
exposure.

The message `system_uid` remains useful for VU/PU correlation and exact reset,
but this local prototype does not present it as a cryptographically
authenticated backend identity. This simplification does not affect signed
SOTA delivery, OEM approval, Aos IAM/KUKSA authorization or Gateway policy.

The backend stores only current-demo functional records. It is not an
AosCloud mirror, lifecycle authority or long-term demo-run archive. The local
application receives a closed `CurrentUnitContext` containing the mandatory
current Test Vehicle and, for the dual-role engineering flow only, the optional
Production Vehicle `system_uid` and wire roles from
the provisioning journal. It is explicit injected input, not a backend Cloud
lookup, lifecycle/readiness assertion or inferred current Unit. Its live
context provider rereads a Demo Control-owned file without restarting the backend.
Process/storage readiness (`GET /health/ready`) is independent of current-Unit
query readiness (`GET /health/context`); Create may start the process before
Provision. Missing/invalid context returns 503, not an empty healthy dashboard.
The [context-readiness schema](current-unit-readiness.schema.json) defines the
closed response: 200 for ready current context, 503 otherwise. It asserts no
Cloud connection, installed service or functional result.
Retire retains the context through exact scoped cleanup. The accepted wire enum
`VALIDATION` and its provisioning identity map to the user-facing label **Test
Vehicle**; human-facing product text must use only that label.
Only a UID in that context may produce a query page or SSE stream. A matching
current UID with no rows truthfully returns an empty page with the context
role; a non-current UID is `404 UNIT_NOT_CURRENT`, and missing/invalid context
is `503 CURRENT_UNIT_CONTEXT_UNAVAILABLE` without a stream. The Demo
Orchestrator uses the same exact context for preview/confirm/execute reset.
The Studio cleanup selector is exactly the current Test UID. The engineering
operation also retains the exact sorted full-context selector; a Production-only
selector is not allowed. Neither selector contains
`demoRunId`, start time or end time. The admin endpoints use a separate
mode-`0600` Unix-domain HTTP composition root and are unavailable to the
browser, guest ingestion route and LAN. Wildcard, missing, empty, duplicate,
foreign or other partial-context selectors are rejected. An empty matching
dataset is a valid idempotent result; its accepted current-context identity
scope remains mandatory. Preview and execute additionally report ten explicit
`nonmatchingRecordCounts`, allowing a caller to distinguish removal of the
Test records from an entirely empty logical store. Other Units' rows are never
implied disposable. Whole-volume removal requires the separate private schema-
validated empty-store proof, stopped owners and exact resource ownership.

The private `POST /api/v1/brake/admin/storage/empty-proof` takes the
[current proof request](current-admin.schema.json#/$defs/proofRequest) and returns
the [current closed storage proof](current-admin.schema.json#/$defs/proof). It is read-only and
does not require a Unit context, so an interrupted Create before Provision can
be retired without inventing a Unit UID. The backend verifies its packaged
database schema, migration ledger, integrity and foreign keys before counting
all ten current record categories in one read transaction. Unknown tables,
schema or unavailable storage are errors, never `EMPTY`. It is not a public/guest route,
does not expose records and does not itself authorize a volume deletion.

The 60-second preview token binds the selected accepted identities, record counts,
record-set digest and expiry. The digest is SHA-256 of one RFC8785 canonical
array containing ten logical table blocks in fixed order: `messages`,
`windows`, `assessments`, `events`, `advisories`, `quarantine`, `resetProducers`,
`resetCommands`, `functionObservations`, `functionObservationConflicts`, including
empty blocks and rows sorted by their canonical UTF-8 bytes. The current store
owns the exact field lists; the original six-block fixtures remain compatibility
inputs. The nonmatching digest uses the same representation over complement
rows. Duplicate JSON object keys are rejected before canonicalization.
The token is a versioned RFC8785 payload plus HMAC-SHA256, bounded to 1024
characters, under a random 256-bit process-local key that is never persisted,
logged or returned. A malformed token, bad MAC, expired token or token from a
previous process/restart returns `409 PREVIEW_TOKEN_EXPIRED` and requires a new
preview. Only a structurally valid, valid-MAC token whose bound current row set
has changed returns `409 PREVIEW_STALE`. Both failures delete nothing. One SQLite
transaction removes only matching Brake messages,
windows, assessments, events, advisory facts, quarantine, reset producer/command
and function-observation/conflict records. Success proves zero matching rows
and an unchanged nonmatching-data digest across the deletion transaction. Brake
binds selected rows in the HMAC preview; unlike Tire it does not bind a preview-
time complement digest. It proves complement preservation within execution.
If the response is lost, the Orchestrator reconciles by authoritative re-read instead
of blind repetition. Cleanup neither deletes Tire data, VM/overlay state,
AosCloud Units/Nodes nor AosCloud audit. It must complete before the Brake
volume reset; D4-021 owns the overall R0 ordering.

These are **data cleanup** operations, not the separate history-preserving
model Reset. Tire has its own opaque-token admin protocol and error names;
Brake's HMAC encoding must not be imposed on Tire.

Read-only source authorities:
[selector/token handler](https://github.com/alexmaninblack/brake-health-cloud/blob/main/apps/backend/src/brake-data-http.ts),
[record-set/delete transaction](https://github.com/alexmaninblack/brake-health-cloud/blob/main/apps/backend/src/brake-data-store.ts).
The [current admin profile](current-admin-profile.v1.json) selects endpoint
request/response definitions in [current-admin.schema.json](current-admin.schema.json)
and [synthetic fixtures](fixtures/current-admin.valid.json). Profile version
1.0.0 describes the existing wire contract 1.0.0, ten counters and database
schema 5; it is not a new wire deployment. Closed-schema validation does not
prove current-context authorization, HMAC validity/expiry or transactional
peer preservation: those remain mandatory owner checks. The source-only
conformance suite is `tests/test_current_admin_contracts.py` in the integration
repository. It changes no handler, signed input or recorded artifact hash.

The original `cleanup-*.schema.json`, `storage-empty-proof.schema.json` and
six-counter fixtures remain immutable compatibility inputs, not validators
for the current administrative responses. Consumers of current admin data
must select the new profile rather than generate a client from those files.

SQLite runtime and forward-only transactional migrations are packaged in the
immutable Brake backend image. The database file lives only in a dedicated
external Docker persistent volume mounted at `/data`; the Dashboard has no
direct database access. One serialized writer transaction performs the
idempotency check, immutable message insert, typed projection and durable
receipt before ACK. WAL, `synchronous=FULL`, foreign keys, bounded checkpoint
and a five-second busy timeout apply. Unsupported newer schema is `NOT_READY`
and is never destructively reset or downgraded. Ordinary container/Docker
restart or same-run image replacement preserves data. Database unavailable,
full, locked beyond timeout or migration failure returns `503`, creates no ACK
and leaves the Service outbox authoritative. No historical run archive or
separate backup belongs to the first demo.

Foundation migration `001_initialize.sql` is immutable and retains its
historic `schema_migrations` ledger. Data migration `002_brake_data.sql`
performs the complete ledger transition and Brake data schema creation in one
transaction: create `schema_version`, copy the v1 ledger row, drop
`schema_migrations`, create the data tables and indexes, insert the v2 ledger
row, and set `PRAGMA user_version = 2`. The runner selects `schema_version`
when it exists and otherwise the legacy ledger, so a v1 database upgrades
without rewriting history and any v2 failure rolls back to the intact v1
ledger and `user_version = 1`.

Files:

- [`brake-cloud-api-profile.v1.json`](brake-cloud-api-profile.v1.json) — exact
  original endpoint, scope, acknowledgement, persistence, retry, query and
  cleanup profile; older two-UID examples retain compatibility scope;
- [`brake-cloud-ack.schema.json`](brake-cloud-ack.schema.json) — closed durable
  acknowledgement schema;
- [`brake-advisory-fact.v2.schema.json`](brake-advisory-fact.v2.schema.json) — current closed
  Service-to-backend fact combining the accepted request identity with factual
  Gateway Status;
- [`cleanup-preview.schema.json`](cleanup-preview.schema.json) — retained
  six-category cleanup preview/token schema, not a complete validator for the
  current ten-counter administrative response;
- [`current-unit-context.schema.json`](current-unit-context.schema.json) —
  closed injected current Test and optional Production identity/role context;
- [`brake-cloud-query-admin-profile.v1.json`](brake-cloud-query-admin-profile.v1.json)
  — exact bounded REST pagination, closed error mapping, notification-only SSE
  and separate local-admin transport;
- [`query-page.v2.schema.json`](query-page.v2.schema.json),
  [`window-detail.v2.schema.json`](window-detail.v2.schema.json),
  [`error-response.schema.json`](error-response.schema.json) and
  [`sse-change-notification.schema.json`](sse-change-notification.schema.json)
  — current closed browser-query responses; page/detail envelopes use wire
  revision 2, while error and SSE bodies retain their own unchanged versions;
- [`cleanup-preview-request.schema.json`](cleanup-preview-request.schema.json),
  [`cleanup-execute-request.schema.json`](cleanup-execute-request.schema.json)
  and [`cleanup-result.schema.json`](cleanup-result.schema.json) — closed
  one-or-two-UID admin requests and original six-counter result with no run
  identifier or time range; current ten-counter results extend that retained
  fixture scope and require the current handler contract above;
- [`rfc8785-edge-vectors.schema.json`](rfc8785-edge-vectors.schema.json) —
  closed Unicode ordering, number serialization and duplicate-key edge-vector
  package;
- [`fixtures/brake-cloud-ack.valid.json`](fixtures/brake-cloud-ack.valid.json)
  and [`fixtures/brake-advisory-fact.v2.valid.json`](fixtures/brake-advisory-fact.v2.valid.json)
  — current ACK and native-product conformance fixtures;
- [`fixtures/cleanup-preview.valid.json`](fixtures/cleanup-preview.valid.json)
  — retained six-counter preview compatibility fixture;
- the query page, closed error, SSE notification, cleanup preview request,
  cleanup execute request, cleanup result, Current Unit context, pending VDP
  provenance and RFC8785 edge files under `fixtures/`
  — Query/SSE/Admin 1.0.0 annex conformance fixtures; and
- [`fixtures/window-detail.valid.json`](fixtures/window-detail.valid.json) —
  the exact Unit/window point-read fixture with stored PRE/ACTIVE
  samples and no paging fields.

Backend idempotency is namespaced by the correlation-only `unitSystemUid` and
the exact canonical `messageType` before its message-specific identity. A
Brake band change therefore uses `messageType: BRAKE_HEALTH_EVENT` plus
`content.eventType: BRAKE_CONDITION_BAND_CHANGED`; the event type is not used
as a substitute message type. The advisory fact key is Unit, message type,
request ID and factual Gateway state. Same key/same canonical digest is a
durable duplicate; same key/different digest is `409`, quarantined and not
automatically retried or locally deleted.

The closed acknowledgement echoes the SHA-256 of the RFC-8785 canonical
idempotency-key array and the accepted content digest. A duplicate returns the
original stored receipt ID and receive time. A v1 window remains in the local
Service spool until every expected chunk and its single completion have a
matching durable acknowledgement. `409` leaves the source in
`DELIVERY_CONFLICT`, stops automatic retries and deletes nothing. An accepted
receipt proves durable storage of exact logical content only; it proves no
Gateway application, driver receipt or OEM acceptance.

A schema-valid completion is itself durably stored and acknowledged even when
some declared chunks have not arrived. That receipt does not make the window
terminal: its projection remains `PARTIAL` until every declared chunk index is
present and the ordered chunk digests, sample and phase counts, terminal state
and `windowSha256` all validate. Any inconsistent combined set is quarantined
and remains non-terminal. Durable message receipt and terminal window
projection are therefore separate factual states.

An out-of-order chunk with index greater than zero is also durably persisted
and ACKed, but it does not create or expose a window query projection. A
window becomes query-visible only after an authoritative start exists from
chunk 0's first sample timestamp or the completion's
`windowStartTimestamp`. When both arrive, they must match; mismatch is
quarantined and non-terminal. No window-change SSE notification is emitted for
a still-hidden later chunk.

<a id="accepted-window-detail-amendment"></a>
## Window detail contract

The point-read route retains the logical bounds of the accepted 1.1.0
Query/SSE/Admin profile. Current page/detail responses use the explicit
revision-2 envelopes above; the original revision-1 bodies remain compatibility
formats, not a second current query specification:

```text
GET /api/v1/brake/units/{systemUid}/windows/{eventId}
```

The backend authorizes the exact Unit through the injected
`CurrentUnitContext` before looking up the lowercase UUIDv4 event ID. The
closed revision-2 detail body contains the version-aware query-window summary and zero
through 150 samples read from already validated canonical chunk content in
ascending chunk-index and stored-array order. A completion-first partial
window may therefore return zero samples. Every stored phase, value, quality,
source timestamp and source-age field remains unchanged; the point read never
fabricates or interpolates data and never reorders it by phase.

The detail route accepts no query parameters and has no limit, cursor,
pagination or snapshot/freshness claim. A non-current Unit is `404
UNIT_NOT_CURRENT`, malformed identity or query syntax is `400 INVALID_REQUEST`,
and a current Unit without a visible matching projection is `404 NOT_FOUND`.
Existing growing, partial, terminal and quarantined projection states remain
factual. Corrupt stored content is a retryable `503`, not a partial response.
The existing collection, SSE, cache, Current Unit, first-demo network and
security boundaries remain unchanged.

The point-read contract needs no database migration. Existing migration 002
already retains canonical validated chunk content and the exact
Unit/event/chunk index. The point read is implemented and used by Presenter;
its implementation/qualification status is recorded with the current protocol baseline.

The Brake Dashboard obtains functional windows, assessments, events and
advisory facts only through bounded keyset-paginated revision-2
REST queries for the exact current Test or Production Unit. `VALIDATION` is
the wire identity for the Test Vehicle; the Dashboard label remains **Test
Vehicle**. Server-Sent Events contain change notifications only. After every
notification, every reconnect, any detected gap or backend restart, the
Dashboard re-reads authoritative REST state; no SSE ID or payload is state
authority. `/health/live` and `/health/ready` describe
the local backend process and database only. They are not Unit or Service
readiness. AosCloud/AosCore lifecycle and readiness remain authoritative and
are shown by the separate Software Delivery Dashboard. The UI labels these two
authorities explicitly and never derives AosCore readiness from functional
Brake records.

`BrakeHealthEvent` does not carry VDP contract fields. Its query projection
therefore exposes `null` version/digest with
`PENDING_ASSESSMENT_CORRELATION` until the exact assessment matches Unit,
assessment/source IDs, package release, version-aware service identity and model
identity/config. Service identity means native instance for v2 and the original
artifact digest for legacy v1; absence of an OCI digest never joins two native
instances.
Only then may the projection copy the assessment's exact VDP version/digest
and become `CORRELATED_ASSESSMENT`; Service-version or nearby-record inference
is forbidden.

This accepted design contract authorizes no repository creation, backend
implementation, signing, Cloud call, Unit mutation or deployment by itself.

<a id="accepted-fixture-erratum--2026-08-29"></a>
## Retained fixture interpretation

The originally accepted
`fixtures/brake-advisory-fact.valid.json` contained a placeholder
`contentSha256` of 64 `3` characters. The schema and wire contract are
unchanged. RFC-8785 canonicalization of the fixture's existing `content`
object yields the corrected SHA-256
`56500a4db40505e7a1c03ba37830f03b9a406cb54db8e1a81790f907431e703a`.
With only that value corrected and the file's existing formatting preserved,
the complete fixture SHA-256 is
`a2dc0c016d5281c9accead1d6447600d4a2c3736acaef1f725a2831efe334cad`.
This is an accepted fixture erratum, not a Brake Cloud API version change.

<a id="native-product-provenance--2026-09-11"></a>
## Current and legacy product provenance

Only the original wire-provenance/query formats and their message fixtures
have legacy compatibility scope: [advisory fact](brake-advisory-fact.schema.json),
[query page](query-page.schema.json), [window detail](window-detail.schema.json)
and [original advisory fixture](fixtures/brake-advisory-fact.valid.json).
Retain the original discriminator, provenance, queued bytes and stored records;
do not reintroduce artifact-digest fields into new v2 messages. The fixture
interpretation above applies only to that original advisory fixture.

Current transport, storage, context, query, hashing and authorization rules
remain normative. Administration is independently defined by the current
ten-category profile; its legacy six-counter fixtures are separately bounded
above. Scoped live evidence and the remaining full acceptance matrix follow
the protocol map, not a blanket legacy label or a compatibility fixture pass.
