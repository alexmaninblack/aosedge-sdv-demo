<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Cloud API — Accepted Contract

- Decision: `D4-017`
- Lifecycle state: `ACCEPTED`
- Contract version: `1.0.0`
- Subdecision state: transport, first-demo security boundary, idempotency,
  durable acknowledgement, persistence, Dashboard query/authority and exact
  current-run cleanup accepted 2026-08-23

This package freezes the proposed current-demo transport boundary between the
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
Demo Orchestrator obtains the exact current Validation and Production
`system_uid` values from the current-run provisioning journal and performs an
explicit preview/confirm/execute reset. The admin endpoints are unavailable to
the browser, guest ingestion route and LAN. Wildcard, missing or non-two-Unit
selectors are rejected. An empty matching dataset is a valid idempotent result,
but the two exact Unit identities are still mandatory.

The 60-second preview token binds the two sorted identities, record counts,
record-set digest and expiry. Execute is rejected when new records make the
preview stale. One SQLite transaction removes only matching Brake messages,
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

Files:

- [`brake-cloud-api-profile.v1.json`](brake-cloud-api-profile.v1.json) — exact
  review-candidate endpoint, scope, acknowledgement, persistence,
  retry, query and reset rules;
- [`brake-cloud-ack.schema.json`](brake-cloud-ack.schema.json) — closed durable
  acknowledgement schema;
- [`brake-advisory-fact.schema.json`](brake-advisory-fact.schema.json) — closed
  Service-to-backend fact combining the accepted request identity with factual
  Gateway Status;
- [`cleanup-preview.schema.json`](cleanup-preview.schema.json) — closed reset
  preview and confirmation-token schema;
- [`fixtures/brake-cloud-ack.valid.json`](fixtures/brake-cloud-ack.valid.json)
  [`fixtures/brake-advisory-fact.valid.json`](fixtures/brake-advisory-fact.valid.json)
  and [`fixtures/cleanup-preview.valid.json`](fixtures/cleanup-preview.valid.json)
  — conformance fixtures.

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

The Brake Dashboard obtains functional windows, assessments, events and
advisory facts only through bounded, stably ordered Brake backend REST queries
for the exact current Validation or Production Unit. Server-Sent Events are
change notifications only: after reconnect or any detected gap, the Dashboard
re-reads authoritative REST state. `/health/live` and `/health/ready` describe
the local backend process and database only. They are not Unit or Service
readiness. AosCloud/AosCore lifecycle and readiness remain authoritative and
are shown by the separate Software Delivery Dashboard. The UI labels these two
authorities explicitly and never derives AosCore readiness from functional
Brake records.

This accepted design contract authorizes no repository creation, backend
implementation, signing, Cloud call, Unit mutation or deployment by itself.
