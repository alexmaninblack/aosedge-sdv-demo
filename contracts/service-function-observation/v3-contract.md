<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service function observation v3 — executable contract

Frozen for consumer-first P3 implementation on 18 September 2026, under
accepted decisions 1A and P2 option A. This is a new message discriminator,
not an expansion of Tire's legacy FUNCTION_STATUS v1/v2 or product records.
[Schema](function-observation.v3.schema.json) and the reference
[validator/store](function-observation.ts) precede new producers.

## Wire and meaning

- POST through the existing team's /api/v1/{team}/messages endpoint.
- messageType is BRAKE_FUNCTION_OBSERVATION or TIRE_FUNCTION_OBSERVATION;
  schemaVersion 3, contractVersion 3.0.0. Closed objects throughout.
- Native Unit/service/Subject/index/instance, immutable package release and
  functional profile are application-reported provenance, not authorization.
- The six content axes are connection, input, activity, delivery, advisory,
  and the optional lastResult reference. No raw samples, scores, tokens,
  arbitrary text, error payloads, actual VDP profile or Cloud facts enter it.
- RECEIVING/NONE means locally validated inputs, not merely a subscription.
  REAUTHENTICATING distinguishes planned credential replacement. Captures
  interrupted by a real gap remain skipped/aborted, never repaired by fiction.
- Missing token bytes in the validated private token directory are not proof
  of rejected authorization: use STARTING / WAITING / AWAITING_INPUT until
  access and valid samples are observed. This may also occur while recovering;
  it does not prove first boot or planned renewal. Unsafe token files and
  actual RPC authentication/permission failures stay fail-closed. The local
  diagnostic KUKSA_AUTH_PENDING is not a new wire enum or permission grant.
- Activity reasons explain waiting, acquisition or skipped/completed episodes.
  The last result reference preserves its originating release and source time;
  it does not constitute a new assessment or an applied reset.
- Delivery is the service's own queue/receipt observation. The status POST's
  receipt is independent; it does not self-confirm product delivery.
- Advisory CONFIRMED requires a correlated current requestId. This reports
  the producer's observation, not perpetual native advisory validity. Legacy
  product/advisory records remain authoritative for their complete facts.
  Brake V1/V2 must report NOT_SUPPORTED; Brake V3 and Tire V1 support advisory.
- Required profile compatibility remains the Presenter Cloud/package matrix.
  No local missing-input state is named INCOMPATIBLE_VDP.

## Ordering and boundedness

A separate positive generation is atomically reserved in existing native
service storage before each producer process starts emitting observations.
It belongs to the native binding, survives restart/repair/model Reset, and
does not reuse or advance advisory epochs/sequences. Per-generation sequence
starts at 1 and strictly increases. A failed reservation disables observation
emission with an explicit diagnostic, never fabricates an ordering identity.
The storage counter may advance across native instance replacement within the
same Unit/service/Subject/index allocation. Gaps are valid; counters never go
backwards for a surviving binding. Old queued envelopes retain their original
instance and release byte-for-byte. A different Unit/service/Subject/index
cannot inherit that ledger. This does not elect a current instance; Cloud
matching remains mandatory at read time.
Existing model/outbox formats and retained messages must remain readable;
P4 must prove the producer persistence implementation before publication.

Idempotency key: SHA256(canonical JSON of
[unitSystemUid,messageType,serviceInstance,generation,sequence]).
Content SHA256 and full-envelope digest use the existing canonical JSON rules.
Exact retries preserve original bytes, receipt ID and receipt time. A changed
envelope at the same key is a conflict; no last-write-wins replacement.

The sender coalesces changes with a minimum five-second emission interval;
unchanged state is observed every 30 seconds while running. This is not a
promise that every intermediate transition reaches the backend. The backend
marks source observations older than 90 seconds or future-dated as last-known;
it never refreshes source freshness from a delayed receipt. These are new
observation bounds only, not changed telemetry/authentication/advisory leases.

Maximum canonical message: 8192 bytes. Per binding the backend retains the
newest 1024 full payloads by generation/sequence, while compact receipts and
conflict digests remain until owned-run cleanup to preserve exact retries.
No automatic model, assessment, window or advisory-history deletion.
P4 uses a separate bounded observation allocation inside existing delivery
storage (at most 64 pending records); it cannot evict product messages.
On overflow, coalesce an unsent observation without changing any attempted
message bytes. Analytics must never block on delivery.

## Read and migration boundary

GET /api/v1/{team}/units/{uid}/function-observations?limit=10 returns
schemaVersion 3, contractVersion 3.0.0, resourceType FUNCTION_OBSERVATION,
unitSystemUid, items and truncated. Limit is 1–100. One source-ordered head
is returned per native binding. Do not elect a current instance by receipt time.
Each item contains message, backendReceivedAt, authority, stale, clockSkew
and deliveryState. A conflict stays visible rather than falling back to an
older green observation. A truncated set is incomplete.

Presenter must match the native Cloud service instance/current release before
claiming a current function observation. History, source ordering and current
release acceptance remain distinct. No known match means unreported, not
failed. Backend getters remain current-Unit scoped; ingestion uses the same
owned-run Unit/role guard. This does not add new credential authority.

Two additive tables live in each backend's existing SQLite database.
Schema/cleanup proofs must include receipts and conflicts; exact Test cleanup
preserves other Units. Old wire readers and stored canonical bytes are retained.
Consumers and cleanup adapters deploy before changed producers. The old
Presenter remains usable because this new GET is not substituted for legacy
status/product routes. P6 adopts it only after producer qualification.

## Gates

Validate closed fields, safe integer bounds, timestamps, size, digest, native
scope, profile-specific advisory and semantic consistency. Prove mixed legacy/
new ingestion, exact duplicate/conflict, late older delivery, restart ordering,
future/source-stale reports, storage rollback, retention/retry, current-Unit
read guards and peer-preserving cleanup. No schema fixture is live proof.
