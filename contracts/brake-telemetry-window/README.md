<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Telemetry Window Contract

Current implementation status (24 September 2026, demo-v1.1 / Factory .39):
see the [complete protocol map](../implementation-status.md) for this family's
implemented path, accepted amendments and remaining qualification or executable-
profile differences. Design lifecycle labels below are not deployment verdicts.
Historical golden schemas/digests are not rewritten as part of this audit.

## Authorized source-cadence amendment — 18 September 2026

The accepted versioned-service work packet supersedes the historical 30-Hz /
every-third-valid-frame assumption with the first actual complete valid frame
in each 100-ms source-time bucket (`floor(sourceEpochMs / 100)`). At both
20-Hz and 30-Hz input this retains 10 samples per second. Validation happens
before selection; invalid, duplicate or reordered inputs cannot fill buckets.
An empty bucket stays a gap. No interpolation or timestamp rewriting occurs.
Trigger/clear timing, 3/10/2-second windows, 150 samples, spool/receipt bounds
and legacy/native logical message schemas are unchanged. The explicit
[machine-readable amendment](source-time-retention-amendment.v1.json) overrides
only `input.sourceCadenceHz` and `input.selection` in the retained base profile;
the original profile and golden message files are preserved as baseline evidence.


## Authorized demo freshness amendment — 15 September 2026

For the single-Mac Brake V1 real-data trial, source age and stream idle use
5000 ms, replacing the earlier 250-ms budget. Service ingress, V1 validation,
raw-window schemas (both provenance revisions) and backend validation use
the same bound. Missing, future, mixed-timestamp and physically invalid data
remain invalid; no values/timestamps are synthesized. Capture hold/durations,
authorization lease, V2/V3 model timing and advisory expiry are unchanged.
This is a validation-budget change, not a payload-shape/version change.

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

Files:

- [profile](brake-telemetry-window-profile.v1.json);
- [profile schema](brake-telemetry-window-profile.schema.json);
- [chunk schema](brake-telemetry-window-chunk.schema.json);
- [completion schema](brake-telemetry-window-completion.schema.json);
- [golden chunk](fixtures/window-chunk.valid.json); and
- [golden completion](fixtures/window-completion.valid.json).

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
