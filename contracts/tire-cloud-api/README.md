<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

## Studio Test contract migration — implemented state, 24 September 2026

The backend supports one current Test and optional retained Production context;
Test-only cleanup rejects unrelated selectors and preserves peer records.
The old two-UID JSON profile/schema below has **not** been synchronized with
this implementation. Its green legacy fixtures do not prove current wire
conformance. Use the [as-implemented administrative protocol](studio-current-wire.md)
for exact requests, responses, counts and guards. No handler or frozen digest
is changed by this documentation correction.

# Tire Health Cloud API — Accepted Contract

Current implementation status (24 September 2026, demo-v1.1 / Factory .39):
see the [complete protocol map](../implementation-status.md) for this family's
implemented path, accepted amendments and remaining qualification or executable-
profile differences. Design lifecycle labels below are not deployment verdicts.
Historical golden schemas/digests are not rewritten as part of this audit.

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

The backend retains current-demo functional state, not a historical run
archive. The implemented cleanup uses current Test alone or all bound context
UIDs, preserving nonselected records. See the [current wire](studio-current-wire.md).
The two-UID description below records the legacy executable profile, whose
schema/fixtures still require controlled synchronization. AosCloud lifecycle and audit records are
outside this product and remain untouched.

Only the local Demo Orchestrator can preview/execute cleanup. It obtains the
exact current VU/PU identities from the provisioning journal; browser, guest
ingestion and LAN cannot access these endpoints. A 60-second token binds the
two identities, counts and record-set digest. Any intervening data change makes
the preview stale. One transaction removes matching Tire messages,
assessments, events, advisory facts, function-status facts and quarantine; an
empty exact match is idempotent. Success proves zero selected rows and unchanged
nonmatching digest. Uncertain response is reconciled by re-read. Brake data,
AosCloud audit/Units/Nodes and VM/overlay state are untouched; D4-021 owns R0
ordering and cleanup must precede Tire-volume reset.

Files:

- [`tire-cloud-api-profile.v1.json`](tire-cloud-api-profile.v1.json) — exact
  review-candidate transport, message, persistence, UI and cleanup profile;
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

## Native product provenance — 2026-09-11

For new product messages, [ADR 0015's versioned migration](../service-runtime-inputs/product-message-migration.md)
defines revision 2 / 2.0.0 beside the retained legacy schemas in this package.
Use the immutable package release and native service/Subject/instance identity;
do not require service/model OCI digest fields or relabel old queued records.
Payload algorithms, model/VDP hashes, receipt keys and authorization remain
unchanged. Producer/input migration and backend consumers are implemented and
have scoped live Test evidence. Full current-image qualification remains
separate; see the protocol map above. Earlier sections and v1 schema
files remain legacy evidence, not an instruction to reintroduce the digest
dependency into new messages. Administrative/cleanup protocols are unaffected.
