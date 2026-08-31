<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Gateway Controller Handoff macOS Correction Review Packet

- ID: `WP-P1-VEH-GATEWAY-CONTROLLER-MACOS-001`
- Lane: `L-VEH`
- Increment: bounded correction to `IMP-02C`
- State: `IMPLEMENTED — INTEGRATED TO MAIN`
- Version: 0.3
- Prepared: 2026-08-30
- Accepted and authorized: 2026-08-30
- Completed and integrated: 2026-08-31
- Repository: `carla-ego-runtime`
- Preserved candidate: `d4a20c85196ef7df81c78f992f6237c5eca8ff6c`
- Initial correction authorization: product edits and owned offline/local tests
  inside the retained fourteen-file boundary after the synchronized contract
  checkpoint. Dependency retrieval, live CARLA, VM and Cloud remained excluded;
  later bounded build and integration evidence is recorded below.

## Proven Blocker

The candidate passes its Linux core, VISS, shared-contract and sanitizer
tests, but the accepted runtime placement starts CARLA/controller/Gateway on
macOS. The implementation unconditionally enables a Linux-only
`AF_UNIX/SOCK_DGRAM` credential path and throws on non-Linux platforms.

Darwin's installed SDK documents reliable `LOCAL_PEERCRED` and `getpeereid`
only for a connected Unix `SOCK_STREAM`. Therefore the exact D4-004 statement
that simultaneously requires the macOS runtime and Linux-peer-credential-
verified `SOCK_DGRAM` is not implementable as written. Weakening peer
verification, trusting a path/source address or moving the Gateway to another
runtime is not accepted.

## Recommended Bounded Correction

Amend D4-004, Simulator Control and Context 1.1.1 and `IF-VEH-007` together to
use one owner-only connected `AF_UNIX/SOCK_STREAM` per run:

1. the C++ Gateway creates one mode-`0600` socket under the existing random
   owner-only mode-`0700` run directory and listens before the startup gate;
2. the Python controller creates exactly one connection for that run;
3. both endpoints verify the peer effective UID: Darwin uses
   `getpeereid`/`LOCAL_PEERCRED`, Linux uses `SO_PEERCRED`; wrong UID fails
   closed before any record is accepted;
4. each record retains the exact closed JSON schema and maximum 4096-byte body,
   preceded by one unsigned big-endian 32-bit body length;
5. the receiver accepts only complete frames, rejects zero/oversize/invalid
   lengths and truncated JSON, and keeps at most one partial bounded frame;
6. producer I/O is non-blocking. Backpressure, partial-write timeout, EOF or
   disconnect makes the channel unavailable and omits the complete six-path
   controller fact group; it never blocks CARLA ticks, reuses last-known data
   or invents a frame;
7. there is no reconnect, replay or history protocol inside one run. A broken
   channel requires the existing bounded run restart/reconciliation path; and
8. the exact frame/time join, four-record/250-ms bounds, reset semantics and
   all ten projected VSS paths remain unchanged.

This changes only the local transport required for target-platform peer
authentication. It changes no authority, data field, producer, consumer,
freshness, lifecycle or Safe Stop behavior.

## Implemented Source Boundary

Retain the original fourteen-file packet boundary. Only the channel/protocol,
controller and their existing tests/docs may need edits; no fifteenth product
path is introduced. Add target-conditional tests that execute the real Darwin
stream and peer-credential path on macOS and the Linux peer path on Linux,
including wrong UID where a bounded subprocess fixture can prove it.

The corrected candidate must pass all existing 18 core, 20 VISS, 24 shared-
contract and sanitizer tests plus stream framing, partial frame, EOF,
backpressure, wrong-peer, oversize/truncation, restart and no-last-known-reuse
negatives. It also requires one incremental build of only the changed
Gateway/runtime target with `CARLA_EGO_WITH_CARLA=ON`, using the already
working pinned local LibCarla from the accepted `Build-macos-client-v3`/
`Build-ego-runtime-m4` configuration. Rebuilding CARLA or Unreal, downloading
dependencies or creating a new LibCarla build is neither required nor
authorized. The entry gate first resolves and verifies the exact existing
headers, libraries and CMake settings used by the working launcher; a missing
or mismatched local input stops rather than expanding the build.

## Completion Record

The operator accepted the recommended transport correction on 2026-08-30.
Commit `a8d27194fa74d29f1fc45b7b849ddb727fed9fe6` implemented it over preserved
candidate `d4a20c85196ef7df81c78f992f6237c5eca8ff6c`; follow-up
`162eaa3c65ed1c4e9a981b4efd133a9287e8ebe2` invalidates all buffered control
facts on channel loss before a waiter can consume them. Both commits remain
inside the original fourteen-file boundary and are integrated on product
`main`/`origin/main`.

Normal and sanitizer CTest each passed 18/18, Python/M6 verification passed
85/85, and the targeted arm64 `CARLA_EGO_WITH_CARLA=ON` target compiled and
linked against the accepted installed LibCarla prefix. No CARLA/Unreal/
LibCarla rebuild, dependency retrieval or live run occurred. Native wrong-UID
macOS execution remains documented rather than replaced by a fabricated
privileged test. Selected-Unit mTLS and live CARLA/Safe Stop qualification are
separate open gates.
