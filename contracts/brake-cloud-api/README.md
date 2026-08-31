<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Cloud API — Accepted Contract and Proposed Window Detail

- Decision: `D4-017`
- Lifecycle state: `ACCEPTED`
- Accepted contract version: `1.0.0`
- Proposed additive Query/SSE/Admin profile: `1.1.0`
- Proposed amendment: `BC-WINDOW-DETAIL-DEC-01`; independent review required
- Subdecision state: transport, first-demo security boundary, idempotency,
  durable acknowledgement, persistence, Dashboard query/authority and exact
  current-run cleanup accepted 2026-08-23

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
application receives a closed `CurrentUnitContext` containing exactly the
current Test Vehicle and Production Vehicle `system_uid` and wire roles from
the provisioning journal. It is explicit injected input, not a backend Cloud
lookup, lifecycle/readiness assertion or inferred current Unit. Its live
provisioning-journal adapter remains deferred to
`BRAKE-CLOUD-INTEGRATION-001`. The accepted wire enum
`VALIDATION` and its provisioning identity map to the user-facing label **Test
Vehicle**; human-facing product text must use only that label.
Only a UID in that context may produce a query page or SSE stream. A matching
current UID with no rows truthfully returns an empty page with the context
role; a non-current UID is `404 UNIT_NOT_CURRENT`, and missing/invalid context
is `503 CURRENT_UNIT_CONTEXT_UNAVAILABLE` without a stream. The Demo
Orchestrator uses the same exact context for preview/confirm/execute reset.
The cleanup selector is exactly those two sorted Unit UIDs and contains no
`demoRunId`, start time or end time. The admin endpoints use a separate
mode-`0600` Unix-domain HTTP composition root and are unavailable to the
browser, guest ingestion route and LAN. Wildcard, missing or non-two-Unit
selectors are rejected. An empty matching dataset is a valid idempotent
result, but the two exact Unit identities are still mandatory.

The 60-second preview token binds the two sorted identities, record counts,
record-set digest and expiry. The digest is SHA-256 of one RFC8785 canonical
array containing all six logical table blocks in fixed order—messages,
windows, assessments, events, advisories and quarantine—including empty
blocks, the annex's exact row fields and rows sorted by their canonical UTF-8
bytes. The nonmatching digest uses the same representation over complement
rows. Duplicate JSON object keys are rejected before canonicalization.
The token is a versioned RFC8785 payload plus HMAC-SHA256, bounded to 1024
characters, under a random 256-bit process-local key that is never persisted,
logged or returned. A malformed token, bad MAC, expired token or token from a
previous process/restart returns `409 PREVIEW_TOKEN_EXPIRED` and requires a new
preview. Only a structurally valid, valid-MAC token whose bound current row set
has changed returns `409 PREVIEW_STALE`. Both failures delete nothing. One SQLite
transaction removes only matching Brake messages,
windows, assessments, events, advisory facts and quarantine records. Success
proves zero matching rows and an unchanged nonmatching-data digest. If the
response is lost, the Orchestrator reconciles by authoritative re-read instead
of blind repetition. Cleanup neither deletes Tire data, VM/overlay state,
AosCloud Units/Nodes nor AosCloud audit. It must complete before the Brake
volume reset; D4-021 owns the overall R0 ordering.

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
  accepted endpoint, scope, acknowledgement, persistence,
  retry, query and reset rules;
- [`brake-cloud-ack.schema.json`](brake-cloud-ack.schema.json) — closed durable
  acknowledgement schema;
- [`brake-advisory-fact.schema.json`](brake-advisory-fact.schema.json) — closed
  Service-to-backend fact combining the accepted request identity with factual
  Gateway Status;
- [`cleanup-preview.schema.json`](cleanup-preview.schema.json) — closed reset
  preview and confirmation-token schema;
- [`current-unit-context.schema.json`](current-unit-context.schema.json) —
  closed injected current Test/Production Unit identity and role context;
- [`brake-cloud-query-admin-profile.v1.json`](brake-cloud-query-admin-profile.v1.json)
  — exact bounded REST pagination, closed error mapping, notification-only SSE
  and separate local-admin transport;
- [`query-page.schema.json`](query-page.schema.json),
  [`window-detail.schema.json`](window-detail.schema.json),
  [`error-response.schema.json`](error-response.schema.json) and
  [`sse-change-notification.schema.json`](sse-change-notification.schema.json)
  — closed browser-query responses; the window-detail schema belongs only to
  the proposed additive 1.1.0 profile;
- [`cleanup-preview-request.schema.json`](cleanup-preview-request.schema.json),
  [`cleanup-execute-request.schema.json`](cleanup-execute-request.schema.json)
  and [`cleanup-result.schema.json`](cleanup-result.schema.json) — closed
  two-UID admin request/result messages with no run identifier or time range;
- [`rfc8785-edge-vectors.schema.json`](rfc8785-edge-vectors.schema.json) —
  closed Unicode ordering, number serialization and duplicate-key edge-vector
  package;
- [`fixtures/brake-cloud-ack.valid.json`](fixtures/brake-cloud-ack.valid.json)
  [`fixtures/brake-advisory-fact.valid.json`](fixtures/brake-advisory-fact.valid.json)
  and [`fixtures/cleanup-preview.valid.json`](fixtures/cleanup-preview.valid.json)
  — ingestion/preview conformance fixtures; and
- the query page, closed error, SSE notification, cleanup preview request,
  cleanup execute request, cleanup result, Current Unit context, pending VDP
  provenance and RFC8785 edge files under `fixtures/`
  — Query/SSE/Admin 1.0.0 annex conformance fixtures; and
- [`fixtures/window-detail.valid.json`](fixtures/window-detail.valid.json) —
  the proposed exact Unit/window point-read fixture with stored PRE/ACTIVE
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

## Proposed Window Detail Amendment

The proposed 1.1.0 Query/SSE/Admin profile adds one point read without changing
the four accepted 1.0.0 collection bodies:

```text
GET /api/v1/brake/units/{systemUid}/windows/{eventId}
```

The backend authorizes the exact Unit through the injected
`CurrentUnitContext` before looking up the lowercase UUIDv4 event ID. The
closed 1.0.0 detail body contains the existing query-window summary and zero
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

No database migration belongs to this amendment. Existing migration 002
already retains canonical validated chunk content and the exact
Unit/event/chunk index. This proposal authorizes no backend change until the
contract cascade and its source-only work packet are independently accepted.

The Brake Dashboard obtains functional windows, assessments, events and
advisory facts only through the accepted 1.0.0 annex's bounded keyset-paginated
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
assessment/source IDs, Service version/artifact and model identity/config.
Only then may the projection copy the assessment's exact VDP version/digest
and become `CORRELATED_ASSESSMENT`; Service-version or nearby-record inference
is forbidden.

This accepted design contract authorizes no repository creation, backend
implementation, signing, Cloud call, Unit mutation or deployment by itself.

## Accepted Fixture Erratum — 2026-08-29

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
