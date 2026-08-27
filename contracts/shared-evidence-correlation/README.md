<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Shared Evidence, Correlation and Chronology — Design Reviewed

- Decision: `D4-024`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.0.0`
- Accepted subdecisions: D4-024.1 canonical correlation context, D4-024.2
  timestamp semantics/causal order, D4-024.3 structured evidence/redaction and
  D4-024.4 duplicate/out-of-order/clock behavior and D4-024.5 conformance and
  qualification, 2026-08-23

D4-024.1 introduces no global or audience-visible `demoRunId` and no
historical demo-run database. Before provisioning, the current run is bounded
by its start time, overlay role and Factory/overlay digests. After
provisioning, operational evidence binds the exact Validation or Production
role, current `system_uid`, AosCloud Unit UUID, main Node UUID, source
generation/frame or event range and the same bounded current-session window.

Function messages carry only their own correlation context: `unitSystemUid`,
`unitRole`, Service version/digest, VDP contract version/digest, source
exercise/generation/event identity and the domain `eventId`, `assessmentId` or
`requestId`. They do not receive Cloud Unit/Node UUIDs or a local run
identifier. Demo surfaces join `system_uid` to current authoritative AosCloud
state when Cloud identity is required.

Collision scope is Function Team + Unit `system_uid` + message type + domain
identifier. JSON/HTTP contracts use camelCase; AosCloud snake_case or other
native names are adapter-local mappings, not a second public schema. VIN,
credentials, JWTs, private certificates/keys and raw Cloud responses never
become correlation fields.

Missing, stale, contradictory or cross-run binding produces `UNKNOWN` or
`BLOCKED`, never success. Successful R0 removes demo-owned current-run
correlation while leaving AosCloud-owned audit history intact.

Five timestamp roles remain separate: Gateway-owned `sourceEventTime`,
Service-owned local decision time (`assessedAt`, `effectiveAt` or `issuedAt`),
Gateway-owned `gatewayObservedAt`, backend-owned first durable
`backendReceivedAt`, and backend-owned `synchronizationCompletedAt`. The last
value requires a Service outbox-drain watermark bound to producer epoch and
highest acknowledged sequence; reconnect time alone cannot prove
synchronization. Retries preserve all upstream times and duplicates reuse the
original receipt time.

Causal order is proven by domain identifiers, producer epoch/sequence, source
generation/frame and explicit state transitions, never by comparing clocks on
the Mac, VM and backend. Dashboards label vehicle event, local decision,
Gateway action, Cloud receipt and synchronization independently and calculate
no latency KPI.

This demonstrates causal linkage, local-decision separation and delayed
delivery/reconnect behavior in the demo only. It does not prove production
clock synchronization, worst-case or end-to-end latency, real-time deadlines,
production network behavior or automotive safety suitability.

The shared structured record is a sanitized current-state Dashboard projection,
not a new system of record, AosCloud-log replacement or evidence archive. It
contains a typed record/owner/source, one source-owned observation time,
correlation fingerprints, fixed event/state/reason codes, a bounded detail
object, source fingerprint/freshness and content digest. Free-form log text and
unknown fields are not evidence and are not displayed automatically.

Exact Unit/Node binding is checked before the audience projection. The browser
receives vehicle aliases and fingerprints rather than full private Cloud IDs.
Secrets, JWTs, authorization headers, private keys/certificates, VIN, raw Cloud
responses and unrestricted raw telemetry are removed before data enters UI
state. Missing, rejected or redacted evidence remains visibly
`INCOMPLETE`/`REDACTED`/`UNKNOWN`; silent omission is forbidden.

At the Representation Layer, the stable internal `Validation Vehicle` evidence
alias is rendered as `Test Vehicle`. Exact Cloud binding and technical evidence
retain `Validation Unit`, `VU` and `Verification Unit Set` semantics.

R0 deletes demo-owned current records. It creates no historical archive; the
only retained exception is one separately governed sanitized, baseline-bound
qualification dossier where its owner contract requires it.

An exact duplicate has the same idempotency key and content digest. It reuses
the original receipt/result and creates neither a second action nor a second
Dashboard row. Reusing a key with different content is an explicit
`IDEMPOTENCY_CONFLICT` and cannot replace accepted evidence.

State-changing order is defined by producer epoch and sequence, not backend
receipt time. Service restart creates a new epoch. Delayed evidence from an old
epoch may remain visible in the current run but cannot mutate current state or
advisory. Reconnect retries only unacknowledged messages without changing IDs,
content or source times; synchronization completes only after every sequence
through the declared watermark is acknowledged.

Out-of-order evidence is labelled rather than silently discarded and never
rolls back the current Dashboard state. Invalid RFC 3339 UTC or impossible
owner-local chronology is rejected. Cross-clock differences are shown as
`CLOCK_UNVERIFIED`/`CLOCK_ANOMALY` and never determine causal order. The UI
shows an ignored-duplicate count and explicit conflicts without duplicating
normal rows. These rules remain demo guarantees only.

Qualification starts with static closed-schema, naming, namespace and
forbidden-field tests, followed by owner-component tests for Gateway binding,
Service retry/epoch behavior, backend ordering/idempotency, pre-browser
redaction and acknowledged synchronization watermarks. Controlled negatives
cover wrong Unit/role, unknown generation, retired-run input, digest conflict,
sequence rollback, late old epoch, invalid/owner-impossible time, missing
watermark and forbidden/unknown UI fields. Clock anomalies use fixtures and do
not change Mac or VM clocks.

Validation Unit integration proves normal Brake/Tire chains, restart/new epoch,
atomic external-connectivity loss, local offline decision, immutable reconnect
retry and acknowledged synchronization without duplicate rows or state
rollback. Production Unit rehearsal runs one normal and one offline/reconnect
chain with the same reviewed contracts and prepared artifacts.

`PASS` requires exact Unit/role/source/team binding, valid causal linkage, the
complete idempotency/ordering matrix, no forbidden browser-state data, R0
current-record cleanup and no historical demo database. Evidence feeds the
future common D4-025 acceptance dossier; D4-024 creates no separate archive.

The design is closed. Implementation and live qualification remain open. This
review authorizes no implementation, publication, Cloud mutation or VM change.
