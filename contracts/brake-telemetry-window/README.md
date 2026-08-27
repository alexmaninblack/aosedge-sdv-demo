<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Telemetry Window Contract

- Decision: [`D4-016`](../../docs/requirements/d4-decision-register.md#d4-016)
- Accepted subdecisions: D4-016.1 and D4-016.2
- Contract version: 1.0.0
- Lifecycle state: acquisition, logical message and local spool contract accepted;
  the D4-017 local transport/backend acknowledgement contract is a prepared
  review candidate; production backend authentication is out of scope

This cross-repository contract joins Brake Health Service v1 with the Brake
Health Backend. D4-017 now proposes the exact transport and durable
acknowledgement contract for review; this package defines the
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
An event is deleted only after an acknowledgement conforming to the D4-017
review candidate proves durable backend storage of all chunks and completion.
R0 removes remaining spool state with its disposable Unit overlay.

No SQLite, external database or additional persistence runtime is required by
this contract.
