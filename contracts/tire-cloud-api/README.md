<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Tire Health Cloud API — Accepted Contract

Implementation and qualification: [protocol status](../implementation-status.md).

## Effective installed profile

The backend supports one current Test and optional retained Production context;
Test-only cleanup rejects unrelated selectors and preserves peer records.
This document owns the current functional and [administrative protocol](#current-test-administrative-protocol).
The [retained compatibility inputs](#retained-compatibility-inputs) serve their
original validators, not a second current administrative specification.

## Contract and authority
- Decision: `D4-019`
- Lifecycle state: `ACCEPTED`
- Contract version: `1.0.0`
- Subdecision state: transport, first-demo security and independent tenant
  boundary, exact logical products and durable acknowledgement/SQLite storage
  plus Dashboard query/authority and exact current-run cleanup accepted
  2026-08-23

This package defines the accepted functional transport and dashboard-data
boundary for Function Team 2. It is deliberately separate from Brake Health:
its API namespace, database, volume, dashboard, publication profile and
failure boundary are not shared.

The first demo uses a local isolated QEMU-to-Mac HTTP route without per-Unit
backend certificates or credential lifecycle. Production backend
authentication belongs to Function Team 2 and is outside the first-demo
claim. The reported `system_uid` is correlation data rather than proof of an
authenticated backend client. Signed SOTA delivery and in-vehicle Aos
IAM/KUKSA authorization remain unchanged.

Delivery is one canonical logical message per HTTP 1.1 request and is
asynchronous from the bounded persistent Tire outbox, so backend timeout/retry
cannot block local assessment, state update or advisory. The unauthenticated
first-demo ingestion endpoint is available only on the isolated guest route;
LAN, public-network and browser ingestion are forbidden and D4-020 owns live
negative qualification.

The Tire product has its own API namespace, container, SQLite database, Docker
volume/network, Dashboard and `tire-sp2` publication profile. It shares neither
data nor failure boundary with Brake Cloud. Tire Cloud has no OEM lifecycle
authority: approval, targeting and promotion remain with the OEM Software
Delivery Dashboard and AosCloud.

The Service sends only bounded assessments, band-change events, advisory facts
and `TIRE_FUNCTION_STATUS`. The latter is a Function Team-reported diagnostic
fact—not AosCore lifecycle readiness. In the current implementation, exact
installed VDP profile/compatibility comes from Presenter Cloud/artifact binding;
services report real local input observations, not a profile inferred from
missing values. Closed v3 function observations now coexist with legacy status. It is emitted at start/change and as a
bounded heartbeat no more often than every 30 seconds. Continuous raw telemetry
and hidden CARLA qualification truth are prohibited. The backend acknowledges
only durable transactional storage; a matching acknowledgement is required
before local outbox deletion.

The closed ACK uses `messageKeySha256`, the SHA-256 of the RFC-8785 canonical
idempotency-key array, plus accepted content digest. New data is acknowledged
only after commit; an identical duplicate reuses the original receipt ID/time.
Same key with different content is `409`, quarantined and retained in the
Service outbox without automatic retry. ACK proves exact durable storage only.

SQLite runtime and forward-only migrations are packaged in the immutable Tire
backend image; `/data/tire-health.sqlite` lives in its dedicated external
Docker volume and is inaccessible to the Dashboard. One serialized WAL/FULL
transaction performs idempotency check, canonical insert, typed projection and
receipt. Unsupported newer schema is `NOT_READY`, never reset or downgraded.
Ordinary container/Docker restart or same-run replacement preserves data.
Database failure returns `503`, creates no ACK and leaves the Service outbox
authoritative. There is no historical archive or separate first-demo backup.

The Dashboard reads assessments, events, advisory facts and bounded Function
Team status only through exact-Unit, stably paginated REST queries. SSE is
change notification only; reconnect causes an authoritative REST re-read.
Backend health endpoints describe only this process/database. AosCloud/AosCore
remain authoritative for Unit and Service lifecycle/readiness in the Software
Delivery Dashboard. `TIRE_FUNCTION_STATUS` is labelled Function Team-reported;
after 90 seconds without heartbeat it becomes `FUNCTION_STATUS_STALE` while
retaining the last reason and making no process-state inference. An exact
`INCOMPATIBLE_VDP` view requires Cloud/profile evidence in Presenter; missing
local input alone cannot establish that verdict.

D4-023.3 designs one deliberately narrow, demo-only Tire CPU-isolation control.
**It is not implemented:** the endpoint returns `501 NOT_IMPLEMENTED`, and no
worker is enabled. The following describes the retained design, not a usable
action or observed enforcement proof.
The Dashboard sends only `START_FIXED_CPU_LOAD` or `STOP_FIXED_CPU_LOAD` to its
Mac-local backend. The Tire Service obtains the command over its existing
service-initiated outbound route; the backend binds current `system_uid`, Tire
version, artifact digest and fixed `TIRE_CPU_ISOLATION_PROOF_V1`. No caller can
choose shell text, workers, intensity or duration. One in-instance worker is
allowed, duplicate start is idempotent, backend-lease loss and the 180-second
ceiling stop it, and Service/VM restart returns it to `INACTIVE` without
resume. The action is disabled when the selected vehicle is externally
offline. Reported control state never proves AosCore quota enforcement.

## Current-Test administrative protocol

The [current admin profile](current-admin-profile.v1.json) binds endpoint-specific
definitions in [current-admin.schema.json](current-admin.schema.json) and
[synthetic fixtures](fixtures/current-admin.valid.json). Profile version 1.0.0
describes the implemented wire contract 1.0.0 and database schema 4; it does not
change a handler or frozen input. Current consumers use this profile, not the
retained two-UID/six-counter cleanup schema. Schema validity alone cannot prove
current-context authorization, opaque-token validity/expiry or transactional
peer preservation; the backend must still enforce those stateful checks.

The backend retains current-demo functional state, not a historical run
archive. Only local Demo Control may preview/execute cleanup. Browser, guest
ingestion and LAN cannot access this administrative interface. Model Reset is
a separate protocol and does not erase history. D4-021 owns R0 ordering;
cleanup must precede Tire-volume reset.

### Context and selectors

Context is a closed object with `schemaVersion: 1`, `contractVersion: "1.0.0"`,
`source: "CURRENT_RUN_PROVISIONING_JOURNAL"`, required `testUnit` and optional
`productionUnit`. Each Unit has exactly `systemUid`, `unitRole` and
`userFacingRole`. Internal roles are `VALIDATION` / `PRODUCTION`, display roles
`Test Vehicle` / `Production Vehicle`. Identities must be distinct; missing,
duplicate-key, malformed, oversized or unknown context is rejected.

Cleanup accepts exactly `[currentTestUid]` or all current context UIDs (one or
two). It rejects empty, duplicate, foreign and Production-only selectors.
The selector is checked against current context and sorted before use; valid
UID syntax alone grants no cleanup authority. Neither a `demoRunId` nor an
independent time-window selector is accepted.

### Transport and closed requests

Admin POSTs use a private mode-0600 Unix socket, not the guest-ingestion or
browser TCP route. Requests are limited to 4096 bytes and use strict JSON.

| Operation | Path suffix under `/api/v1/tire/admin/` | Exact request fields |
| --- | --- | --- |
| Preview | `current-run/cleanup-preview` | `schemaVersion`, `contractVersion`, `systemUids` |
| Execute | `current-run/cleanup` | Previous fields plus `confirmationToken` |
| Storage proof | `storage/empty-proof` | `schemaVersion`, `contractVersion` |

All three requests require schema 1 and contract `1.0.0`; extra fields fail.

### Response and transaction

Preview returns `schemaVersion: 1`, sorted `systemUids`, `recordCounts`,
`recordSetSha256`, `nonmatchingRecordCounts`, `nonmatchingRecordSetSha256`,
`confirmationToken` and `expiresAt`. Unlike the request, it has no
`contractVersion` field. Tokens last 60 seconds and at most 16 previews are
retained. Token contents are private and must not enter audit evidence.
The token is opaque random server-held state, not Brake's HMAC wire format.
Invalid, expired, wrong-selector, consumed or previous-process tokens yield
`409 INVALID_PREVIEW`; a backend restart requires a fresh preview.

Both count objects cover ten categories: `messages`, `assessments`, `events`,
`advisories`, `functionStatus`, `quarantine`, `resetProducers`, `resetCommands`,
`functionObservations`, `functionObservationConflicts`.

Execution revalidates context, exact selector/token/expiry and both matching
and nonmatching record-set digests. Changed data is `409 STALE_PREVIEW`; no blind
retry is valid. One SQLite transaction deletes selected rows, including reset
and observation records, proves zero selected rows and unchanged nonmatching
digest, then consumes the preview token. Uncertain response requires read-only
reconciliation, not repeated execution.
An empty exact match remains valid; a fresh preview/execute may report zero
selected rows. This does not permit replaying a consumed token.

Success returns schema 1, contract `1.0.0`, `state: "CLEANED"`, `systemUids`,
`deletedRecordCounts`, `remainingRecordCounts`, `nonmatchingRecordCounts`,
`nonmatchingRecordSetSha256` and `completedAt`. Storage proof separately
reports database schema 4 and `EMPTY` / `NONEMPTY`, counts and observation time.
Neither response retires Cloud identity, deletes VM files or touches Brake data.

Sources: [context validation](https://github.com/alexmaninblack/tire-health-cloud/blob/main/src/context.mjs),
[private HTTP handler](https://github.com/alexmaninblack/tire-health-cloud/blob/main/src/main.mjs),
[store/cleanup transaction](https://github.com/alexmaninblack/tire-health-cloud/blob/main/src/store.mjs) and
[product/selector tests](https://github.com/alexmaninblack/tire-health-cloud/blob/main/test/product.test.mjs).
These tests cover Test-only/dual context, selector rejection, stale preview,
peer preservation and empty-store behavior; scoped live proof belongs to the
[current baseline](../../docs/qualification/current-baseline.md).

## Retained compatibility inputs

The following frozen files remain dependencies of original validators and
persisted-message compatibility. They are not regenerated by a prose correction:

- [`tire-cloud-api-profile.v1.json`](tire-cloud-api-profile.v1.json) — accepted
  original machine profile; its two-UID cleanup selector is not the current
  Test-only administrative protocol above;
- [`tire-cloud-ack.schema.json`](tire-cloud-ack.schema.json) and
  [`tire-advisory-fact.schema.json`](tire-advisory-fact.schema.json),
  [`tire-function-status.schema.json`](tire-function-status.schema.json) and
  [`cleanup-preview.schema.json`](cleanup-preview.schema.json) — closed wire
  message/response schemas; the cleanup preview schema is legacy and does not
  validate the current one-Test/ten-counter response;
- [`fixtures/tire-cloud-ack.valid.json`](fixtures/tire-cloud-ack.valid.json) and
  [`fixtures/tire-advisory-fact.valid.json`](fixtures/tire-advisory-fact.valid.json),
  [`fixtures/tire-function-status.valid.json`](fixtures/tire-function-status.valid.json)
  and [`fixtures/cleanup-preview.valid.json`](fixtures/cleanup-preview.valid.json)
  — conformance fixtures.

This accepted design contract authorizes no repository creation, backend
implementation, signing, Cloud call, Unit mutation or deployment by itself.

<a id="native-product-provenance--2026-09-11"></a>
## Current and legacy product provenance

For new product messages, [ADR 0015's versioned migration](../service-runtime-inputs/product-message-migration.md)
defines revision 2 / 2.0.0 beside the retained legacy schemas in this package.
Use the immutable package release and native service/Subject/instance identity;
do not require service/model OCI digest fields or relabel old queued records.
Payload algorithms, model/VDP hashes, receipt keys and authorization remain
unchanged. Producer/input migration and backend consumers are implemented and
have scoped live Test evidence. Full current-image qualification remains
separate; see the protocol map above. Retained v1 schema files decode original
records; they do not reintroduce the digest dependency into new messages.
Administrative/cleanup protocols are unaffected by product-wire revision.
