<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Gateway Controller Handoff macOS Correction Review Packet

- ID: `WP-P1-VEH-GATEWAY-CONTROLLER-MACOS-001`
- Lane: `L-VEH`
- Increment: bounded correction to `IMP-02C`
- State: `REVIEW CANDIDATE — NOT AUTHORIZED`
- Version: 0.1
- Prepared: 2026-08-30
- Repository: `carla-ego-runtime`
- Preserved candidate: `d4a20c85196ef7df81c78f992f6237c5eca8ff6c`
- Product edits, dependency retrieval, build, live CARLA, VM, Cloud, merge and
  push authorized: no

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

Amend D4-004, Simulator Control and Context 1.1.0 and `IF-VEH-007` together to
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

## Proposed Source Boundary After Design Acceptance

Retain the original fourteen-file packet boundary. Only the channel/protocol,
controller and their existing tests/docs may need edits; no fifteenth product
path is introduced. Add target-conditional tests that execute the real Darwin
stream and peer-credential path on macOS and the Linux peer path on Linux,
including wrong UID where a bounded subprocess fixture can prove it.

The corrected candidate must pass all existing 18 core, 20 VISS, 24 shared-
contract and sanitizer tests plus stream framing, partial frame, EOF,
backpressure, wrong-peer, oversize/truncation, restart and no-last-known-reuse
negatives. It also requires a full pinned `CARLA_EGO_WITH_CARLA=ON` compile;
materializing LibCarla remains a separate dependency gate and no download is
authorized here.

## Authorization Gate

The operator must explicitly accept the recommended transport correction
before the normative D4/contract/interface cascade or any candidate source
edit. If the stream boundary is rejected, `d4a20c` remains quarantined and the
Demo Interface Train remains blocked. No fallback transport is inferred.
