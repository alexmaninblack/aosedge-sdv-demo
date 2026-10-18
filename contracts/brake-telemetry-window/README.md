<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Telemetry Window Contract

Implementation and qualification: [protocol status](../implementation-status.md).

## Acquisition and freshness

At qualified 20/30-Hz input, retain the first complete valid frame in each
100-ms source-time bucket, at most 10 Hz. An empty bucket remains a gap; no
interpolation, duplicate filling or timestamp rewriting. The
[executable cadence record](source-time-retention-amendment.v1.json) declares
this selection; retained base/golden files preserve their exact fixture bytes,
not an alternative every-third-frame runtime algorithm.

The accepted single-Mac Brake V1 input source-age/stream-idle limit is 5000 ms
through service ingress, raw-window messages (both provenance revisions) and
backend validation. Missing, future, mixed-time or physically invalid samples
remain invalid. PRE/ACTIVE/POST durations, trigger hold/clear rules, resource
bounds, authorization lease, V2/V3 model timing and advisory expiry are
independent and unchanged. This is a validation budget, not a new payload shape.

<a id="authorized-source-cadence-amendment--18-september-2026"></a>
<a id="authorized-demo-freshness-amendment--15-september-2026"></a>

- Decision: [`D4-016`](../../docs/requirements/d4-decision-register.md#d4-016)
- Accepted subdecisions: D4-016.1 and D4-016.2
- Contract version: 1.0.0
- Lifecycle state: acquisition, logical message, local spool and D4-017 local
  transport/backend acknowledgement contracts accepted; production backend
  authentication is out of scope

This cross-repository contract joins Brake Health Service v1 with the Brake
Health Backend. D4-017 freezes the exact transport and durable acknowledgement
contract; this package defines the
six-signal acquisition subset, hard-braking trigger, bounded event window,
logical chunk/completion messages, canonical hashing and service-local durable
spool behavior.

## Current product messages

New chunks and completions use `schemaVersion: 2`, `contractVersion: "2.0.0"`
and [native product provenance](../service-runtime-inputs/product-message-migration.md):
the immutable package release and native service/Subject/instance identity,
without `serviceArtifactSha256`. Wire revision 2 is not the Brake functional
profile. Acquisition, content hashes, receipt keys and spool rules remain
current; only retained v1 wire provenance has compatibility-only scope.

Files for current products and acquisition verification:

- [profile](brake-telemetry-window-profile.v1.json);
- [profile schema](brake-telemetry-window-profile.schema.json);
- [chunk schema](brake-telemetry-window-chunk.v2.schema.json);
- [completion schema](brake-telemetry-window-completion.v2.schema.json);
- [golden chunk](fixtures/brake-telemetry-window-chunk.v2.valid.json); and
- [golden completion](fixtures/brake-telemetry-window-completion.v2.valid.json).

## Hashing

`contentSha256` is the lowercase SHA-256 of the RFC 8785 canonical JSON bytes
of the message's `content` object. `windowSha256` is the lowercase SHA-256 of
the concatenation, in `chunkIndex` order, of the raw 32-byte values represented
by the chunk `contentSha256` hex strings. Transport compression, framing and
authentication do not change either digest.

## Idempotency

- Chunk key: `(eventId, chunkIndex)`.
- Completion key: `(eventId, WINDOW_COMPLETION)`.
- An identical key and digest is a retry of the same logical message.
- An identical key with a different digest is a conflict and is never silently
  accepted.

## Persistent spool

The service stores each triggered event under
`/storage/brake-health/v1/events/<eventId>/`. Canonical message files are
written to a same-directory temporary file, synchronized, atomically renamed
and followed by directory synchronization before they are eligible for
transport. The spool uses `0700` directories and `0600` files.

The PRE ring remains memory-only until trigger. After trigger, no chunk is sent
before durable storage. A recovered `CAPTURING` event without completion is
closed as `ABORTED_RESTART`; corrupt retained content becomes `QUARANTINED`.
An event is deleted only after an acknowledgement conforming to accepted
D4-017 proves durable backend storage of all chunks and completion.
R0 removes remaining spool state with its disposable Unit overlay.

No SQLite, external database or additional persistence runtime is required by
this contract.

<a id="native-product-provenance--2026-09-11"></a>
## Current and legacy product provenance

Only the original wire-provenance schemas and their message fixtures are
legacy compatibility inputs: [chunk](brake-telemetry-window-chunk.schema.json),
[completion](brake-telemetry-window-completion.schema.json),
[chunk fixture](fixtures/window-chunk.valid.json) and
[completion fixture](fixtures/window-completion.valid.json). Retain their
original discriminator, artifact provenance and queued bytes. Do not introduce
that artifact-digest dependency into new v2 messages or mix provenance within
one window.

The profile, acquisition, hashing, idempotency and spool rules above remain
current; their versioned fixture bytes are not a competing runtime algorithm.
Administrative/cleanup protocols are unaffected. Scoped live evidence and the
complete negative/recovery acceptance matrix remain separate, as stated in
the protocol map above.
