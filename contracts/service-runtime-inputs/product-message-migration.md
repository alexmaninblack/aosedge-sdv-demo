<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native product-message migration

- Authority: [ADR 0015](../../docs/architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
- Delivery step: N3, consumer compatibility before producer publication
- Wire revision: `schemaVersion: 2`, `contractVersion: "2.0.0"`

The nine `*.v2.schema.json` product schemas replace only application
provenance. The original `*.schema.json` files remain the strict legacy
decoders. Neither model state nor KAC, VSS, advisory request/status, receipt,
idempotency-key or content-hash protocols change.

| Family | Native schemas |
| --- | --- |
| Brake windows | [Chunk](../brake-telemetry-window/brake-telemetry-window-chunk.v2.schema.json), [completion](../brake-telemetry-window/brake-telemetry-window-completion.v2.schema.json) |
| Brake model | [Assessment](../brake-health-model/brake-health-assessment.v2.schema.json), [event](../brake-health-model/brake-health-event.v2.schema.json) |
| Brake advisory | [Fact](../brake-cloud-api/brake-advisory-fact.v2.schema.json) |
| Tire model | [Assessment](../tire-health-model/tire-health-assessment.v2.schema.json), [event](../tire-health-model/tire-health-event.v2.schema.json) |
| Tire advisory/status | [Fact](../tire-cloud-api/tire-advisory-fact.v2.schema.json), [function status](../tire-cloud-api/tire-function-status.v2.schema.json) |
| Brake queries | [Page](../brake-cloud-api/query-page.v2.schema.json), [detail](../brake-cloud-api/window-detail.v2.schema.json) |
| Tire queries | [Page](../tire-cloud-api/query-page.v2.schema.json) |

| New field | Exact source | Meaning |
| --- | --- | --- |
| `serviceVersion` | Immutable `/usr/share/aosedge/service-release.json` | Monotonic package release; not the compiled functional profile |
| `serviceInstance.serviceId` | `AOS_ITEM_ID` | Native service identity |
| `serviceInstance.subjectId` | `AOS_SUBJECT_ID` | Native Subject identity |
| `serviceInstance.instanceIndex` | `AOS_INSTANCE_INDEX` parsed as a nonnegative JSON-safe integer | Native instance index; no invented restart count |
| `serviceInstance.instanceId` | `AOS_INSTANCE_ID` | Native runtime instance identity; not a replacement for producer epoch |

The nested identity is closed and required. Identifiers use the bounded
ASCII identifier grammar in the schemas; the integer upper bound is JSON's
exact-integer bound, not a claim about Aos' internal integer width. Release
versions use the package's strict `X.Y.Z` grammar (maximum 32 characters,
no leading zeros, prerelease/build suffix or trailing whitespace).
The actual native values must be present; team labels and defaults are not
substitutes. All these values are application-reported correlation, not
authentication or runtime attestation. KAC continues to authorize using IAM.

`serviceArtifactSha256` and Brake's `modelArtifactSha256` are absent and
rejected in v2 product messages, including null/empty/zero substitutes.
`modelConfigSha256` and VDP compatibility hashes retain their meaning.
The thin Tire band-change event now carries role, package release and native
identity itself; its content and assessment reference are unchanged.

Brake's assessment, event and advisory decoders no longer infer a functional
profile from the release number. A v2 advisory from release `18.0.0` is valid
when its advisory payload satisfies the existing contract. Legacy v1 decoder
behavior remains unchanged. Message kind describes the logical product, not
a new configurable profile or authority.

## Queue, correlation and query compatibility

Queued messages are retried byte-for-byte with their original discriminator,
identity, version, timestamps, content and hashes. A new process must not
upgrade old records in its outbox. Same key/same canonical message returns the
original receipt; same key/different provenance is a retained conflict even
when the content hash is unchanged. Do not add schema or instance to existing
idempotency keys just to hide a collision.

Every chunk and completion in a window must have the same provenance:
schema revision, Unit role, package release, native identity (v2) or artifact
digest (legacy), and VDP contract pair. Mixed identities/revisions are
quarantined. Assessment/event correlation matches that version-aware identity
as well as the existing Unit, assessment/source IDs and model identity/config.
It must never join two different native instances merely because both lack
an OCI digest. Close an active window with its original metadata before a
committed VDP input change.

Brake collection/detail responses use the new `query-page.v2.schema.json`
and `window-detail.v2.schema.json` envelopes (2 / 2.0.0), containing explicitly
versioned stored v1 or v2 messages. A legacy window summary keeps its original
artifact field; a v2 window summary uses `messageSchemaVersion: 2` and
`serviceInstance` instead. Tire query envelopes likewise use 2 / 2.0.0 and
return the original stored messages. Receipts, errors, SSE change notices,
admin context and cleanup request contracts are unchanged.
This freezes the detail response contract only: the current backend branch
does not yet implement the accepted window-detail endpoint. That existing
endpoint gap remains in P7; a schema file is not evidence of a working route.

Brake database migration 003 preserves canonical messages, receipt IDs/times,
keys, content hashes and legacy projection values. Only legacy artifact
projection columns become nullable; v2 stores SQL NULL for an absent legacy
column, never a placeholder digest in a product record. A separate canonical
native-identity projection supports exact joins. Migration failure rolls back
the complete migration. Tire already stores the canonical envelope without
mandatory digest columns and needs no database migration.

## Persisted request provenance

Brake already persists metadata alongside each advisory request; its binding
decoder explicitly accepts old or native provenance. Tire now adds
`lastRequestMetadata` to its existing private wrapper state when creating a
request. The model's 13-field schema, producer epoch and sequence semantics do
not change. The reader accepts old wrapper records with no binding; it never
uses current metadata to manufacture a fact for an unbound legacy request.
Queued facts remain unchanged. Normal advisory refresh creates a new bound
request using the next sequence in the retained epoch. Backward execution by
an older binary against this extended wrapper state is not qualified here.

## Integration gate

Deploy neither producer nor backend during this source-only increment.
Consumer tests cover old/new ingestion, malformed identity/version, unchanged
receipts/history, cross-instance conflicts and query correlation. The N3 source producer gate now passes: both readers use the separate inputs,
and actual C++ output for all nine product kinds passes matching backend
validation/storage and exact-retry checks. This is not ARM64/live qualification. Demo Control's existing private
empty-store proof accepts Brake database 2/3 and Tire 2 without weakening its
ownership, selector or empty-state checks. Real query/readiness/evidence
consumers must use the new query envelopes before P7 acceptance/N6 evidence.
Tire load commands retain the accepted Unit/service/version/instance binding,
authorization, fixed profile, lease, idempotency and 180-second ceiling;
this migration does not invent its still-unimplemented transport or model.
