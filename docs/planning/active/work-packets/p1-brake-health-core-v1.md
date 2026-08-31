<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Health v1 Domain Core Implementation Work Packet

- ID: `WP-P1-BHS-CORE-001`
- Lane: `L-BRAKE`
- Increment: `IMP-04-BHS-CORE-001`
- State: `IMPLEMENTED — ISOLATED V1 DOMAIN CORE COMPLETE`
- Accepted: 2026-08-28
- Repository: `brake-health-service`
- Frozen base: `04abe5bacc47e849c6a6fe4fccb64e8a15157d8f`
- Branch: `codex/imp-04-bhs-core-v1`
- Integration owner: Demo Integration Coordinator

## Outcome

Implement the dependency-free C++17 domain foundation for Brake Health v1:
the accepted six-signal input model, deterministic retained-cadence/window
state machine, bounded local event spool and contract-conforming canonical
chunk/completion messages. The packet produces a host-testable library and
tests only. It does not replace the current scaffold executable or produce an
Aos Service artifact.

## Frozen Inputs

| Input | Version or revision | SHA-256 |
| --- | --- | --- |
| `CR-BHS` | 0.8 | `b16f168631728e9d1267cada125f49bab96725064664ccfb38470698901ea6a3` |
| Brake Telemetry Window contract README | D4-016.1/.2 plus accepted D4-017 boundary | `c8abce17f99c33f10cf4e245b9e9139e94c35525414828f1402c7975d9a78dc8` |
| Window profile | 1.0.0 | `2cf82973051b37e92941fc67c0682d03782b9288dee017b5e6740266e54c20b9` |
| Chunk schema | 1.0.0 | `6166d196b15017d0b6ddc6be7ba94548fff11cc2b260daafb804fe9c1a532b32` |
| Completion schema | 1.0.0 | `0dc9b3f89d1bf3a3c7c790aafd3f8972aed0f5b9e437a07bd19934ea194bac31` |
| Golden chunk fixture | 1.0.0 | `b931ef9cbac717768a6db23992c70acebad74a5b1ccffdcfdd07c707ed4665f6` |
| Golden completion fixture | 1.0.0 | `6b359f78fb7c1c3dd8cd3ccf44901de7d71e3d0fdec926c480fe8854e9a3bbe8` |

All solution-repository inputs are read-only. A mismatch stops the packet; the
worker must not regenerate or reinterpret a contract locally.

## Repository and Isolation

1. Create a clean isolated worktree from the exact frozen base.
2. Use only branch `codex/imp-04-bhs-core-v1`.
3. Keep the existing `brake-health-service` checkout and its `main` unchanged.
4. Use a packet-local or temporary out-of-tree build directory.
5. Commit only the writable boundary below and report the exact commit SHA.

## Writable Boundary

The packet may create or change only:

- `CMakeLists.txt`;
- `include/brake_health/v1/**`;
- `src/v1/**`;
- `tests/cpp/v1/**`;
- `tests/test_v1_cpp.py`;
- `docs/architecture.md`;
- `packaging/aos/README.md`; and
- `README.md`.

The documentation edits are limited to the accepted one-product/v1-v3 model,
fixed-resource KAC boundary, C++17 domain-core status and an explicit statement
that the packaged scaffold executable remains unchanged. Packaging metadata,
the scaffold builder, current shell executable, compatibility data, licenses
and dependency manifest remain read-only.

## Exact Required Behavior

### Domain input and cadence

1. Represent one complete normalized frame containing speed,
   longitudinal/lateral/vertical acceleration, accelerator-pedal position,
   brake-pedal position, source timestamp, maximum source age and quality.
2. Accept no simulator truth, control mode or hidden condition input.
3. Retain every third complete valid source frame from the accepted 30 Hz
   source as the 10 Hz window stream. An incomplete, malformed, non-finite,
   out-of-range, future or older-than-250-ms frame is not valid evidence and
   cannot satisfy trigger/clear timing.
4. Use injected monotonic/source clocks and an injected UUIDv4 source. Tests
   must not sleep or depend on wall-clock time or randomness.

### Window state machine

1. Maintain a memory-only three-second PRE ring of at most 30 retained frames.
2. Start `HARD_BRAKING_EPISODE_V1` only after speed is at least 10 km/h and
   brake pedal is at least 50 percent continuously for 200 ms.
3. Treat longitudinal acceleration as evidence only, never as a trigger.
4. Clear ACTIVE after brake pedal below 10 percent or speed below 0.5 km/h
   continuously for 500 ms, then collect two seconds POST.
5. A valid trigger during POST returns the same event to ACTIVE. Maximum ACTIVE
   duration is ten seconds; maximum total is fifteen seconds/150 retained
   samples. A maximum-duration event suppresses retrigger until clear.
6. Produce only the accepted terminal states `COMPLETE`,
   `TRUNCATED_MAX_DURATION`, `INCOMPLETE_SOURCE_GAP`,
   `ABORTED_SERVICE_STOP` and `ABORTED_RESTART`.

### Logical messages and integrity

1. Emit ordered chunks of at most ten samples and exactly one completion.
2. Keep every canonical uncompressed JSON message at or below 64 KiB.
3. Implement a schema-specific serializer for these two closed message
   families. Do not create a general JSON framework or accept caller-defined
   fields.
4. Produce RFC-8785-compatible canonical bytes for the accepted bounded field
   types and lowercase SHA-256 digests. The packet may contain a small
   repository-owned SHA-256 module used only for unkeyed content integrity; it
   must pass standard known-answer vectors and must not be presented as a
   signer, credential primitive or general cryptographic library.
5. `windowSha256` is the SHA-256 of the raw ordered chunk-digest bytes exactly
   as frozen by the contract.

### Bounded POSIX spool

1. Persist events below the supplied spool root using the accepted per-event
   layout, mode-`0700` directories and mode-`0600` files.
2. Write same-directory temporary content, synchronize it, atomically rename
   it and synchronize the directory before marking a message transport
   eligible.
3. Admit at most eight unacknowledged windows and at most 4 MiB encoded bytes.
   Preserve retained events and reject a new event with
   `WINDOW_DROPPED_QUEUE_FULL`; never evict old evidence to admit new data.
4. Recover an incomplete `CAPTURING` event as `ABORTED_RESTART`; quarantine
   corrupt retained content. Expose deterministic inventory and state results.
5. An injected accepted durable-ack result may advance local state for unit
   testing, but no HTTP response parsing belongs here. Delete an event only
   after every chunk and its completion are marked durably acknowledged.

## Required Verification

The packet must add and pass deterministic tests for:

- clean C++17 configure/build through CMake and CTest;
- retained-cadence selection and incomplete/stale/non-finite input negatives;
- trigger and clear values immediately below, at and above every threshold;
- 200-ms/500-ms timing boundaries without sleeping;
- PRE, ACTIVE, POST, same-event POST retrigger and max-duration suppression;
- every accepted terminal state and the 150-sample bound;
- eight-window and 4-MiB admission boundaries without eviction;
- temporary-write, fsync, rename, directory-fsync and injected failure cases;
- restart recovery, corruption quarantine and full-ack-only deletion;
- golden chunk and completion fixtures, maximum-size rejection, deterministic
  canonical bytes and ordered window digest;
- SHA-256 known-answer vectors; and
- existing repository scaffold, boundary and quality-gate suites.

The Python wrapper may locate a local CMake/C++ toolchain and execute the
out-of-tree CTest suite. It must skip no owned test silently and must download
nothing.

## Explicit Exclusions

- no KAC process, `AOS_SECRET`, JWT or token-file implementation;
- no KUKSA, VISS, gRPC/protobuf or network client;
- no backend HTTP, retry/backoff or D4-017 acknowledgement parsing;
- no v2 model, v3 advisory or Gateway Status transport;
- no change to `src/usr/bin/brake-health-service`, `packaging/aos/config.yaml`,
  `config/compatibility.json` or `tools/build_scaffold.py`;
- no ARM64/Aos artifact or container build;
- no dependency download, package installation or contract modification;
- no signing, publication, AosCloud, VM, Unit, CARLA or live operation;
- no push, merge or `main` mutation.

## Completion Record

- Branch/worktree: `codex/imp-04-bhs-core-v1` at the isolated sibling
  `brake-health-service-imp-04-bhs-core-v1` worktree.
- Commit/parent: `7c0a658ba2106a7274e61296746dcdd3008db26b` over the exact
  frozen base `04abe5bacc47e849c6a6fe4fccb64e8a15157d8f`.
- Boundary: 16 changed files, all within the writable boundary. The existing
  scaffold executable, builder, packaging metadata, compatibility file,
  dependencies and licenses remained unchanged.
- Implemented: dependency-free C++17 six-signal validation/cadence, complete
  PRE/ACTIVE/POST v1 state machine, closed canonical chunk/completion messages,
  unkeyed SHA-256 integrity and bounded durable POSIX event spool.
- Verification: clean configure/build and CTest passed; all nine owned
  deterministic groups, five repository tests and the 34-file quality gate
  passed. Golden chunk/completion/window digests and SHA-256 known-answer
  vectors passed.
- Excluded as required: KAC/KUKSA/network/backend, v2/v3, packaging
  integration, ARM64 artifact and all live operations.
- No generated, credential, binary or downloaded material was committed. No
  download, push, merge, signing, Cloud, VM, Unit, CARLA or FOTA operation
  occurred. There are no open packet defects.

`IMPLEMENTED` means only that this isolated v1 domain packet passes. It does
not mean that Brake Service v1 is packaged or qualified.

Integration note, 2026-08-31: the exact accepted v1 commit
`7c0a658ba2106a7274e61296746dcdd3008db26b` is now the first product commit in
the five-commit v1/v2 train integrated through
`63b0c5fd43572ff96c508abc5e35818218d3500a` on product `main`/`origin/main`.
Combined verification preserved the accepted v1 digests exactly. Runtime
composition, packaging, deployment and live qualification remain open.

## Authorization Gate

This packet is accepted and authorizes only the isolated source work above.
Any writable-boundary expansion, dependency retrieval, artifact build,
packaging integration or external operation requires a new reviewed packet or
explicit operator authorization.
