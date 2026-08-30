<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Gateway Controller-to-C++ Handoff Work Packet

- ID: `WP-P1-VEH-GATEWAY-CONTROLLER-CPP-001`
- Lane: `L-VEH`
- Increment: `IMP-02C`
- State: `IMPLEMENTATION CANDIDATE EXISTS — QUALIFICATION BLOCKED`
- Version: 0.3
- Prepared: 2026-08-29
- Design review completed: 2026-08-29
- Product edits within the exact fourteen-path boundary and one isolated local
  product commit authorized: yes, 2026-08-29
- Build, dependency retrieval, live CARLA/VM/Unit, Cloud, signing, FOTA, merge
  and push authorized: no
- Planning context: Infrastructure-First Critical Path proposal (not part of
  this Gateway-only documentation commit)
- Inputs: [WP-P1-VEH-002](p1-vehicle-gateway-safe-stop-projection.md),
  D4-004, `IF-VEH-007`, and Platform FOTA Safe Stop 1.1.1

## Outcome

Connect the Python process that exclusively owns CARLA control/ticks to the
C++ Gateway observer so the already implemented six control/reset paths join
the four physical paths as one complete frame-coherent VSS snapshot. The
Gateway publishes facts only. It does not calculate, retain or authorize Safe
Stop; the OEM Component Runtime remains the sole Safe Stop evaluator.

This packet replaces no lifecycle or status file. In particular, C++ shall
never poll `controller-status.json`; that file remains operator/run evidence,
not a vehicle-state transport.

## Frozen source and isolation

| Item | Exact value |
| --- | --- |
| Repository | `carla-ego-runtime` |
| Main/source ancestor | `d05ac2dbf89f341215e12770feab0ec23b3c2394` |
| Required integration base | `8af302dd11c872a564ea7542a126c9886daf2a5a` |
| Base content | wheel-unit correction plus accepted Safe Stop projection core |
| Proposed branch | `codex/imp-02c-controller-cpp-handoff` |
| Proposed worktree | `../carla-ego-runtime-imp-02c-controller-cpp-handoff` |

The worktree must be created at exact base `8af302d` and clean. The current
main checkout's untracked `tools/__pycache__/` is neither an input nor an
authorized deletion. Any base movement or unrelated dirty path stops work.

Synchronized solution source is
`aosedge-sdv-demo@ce829f0a7300e83ab222fda64defbaf56eccbf9c`; the reviewed
Gateway cascade is identified by the exact content digests below and must be
committed plus rechecked before any implementation authorization:

| Input | SHA-256 |
| --- | --- |
| Simulator Control and Context 1.1.0 | `f34073d5b8906c2588a02c074b538b526966fedd9291bfdc1d18f73a69797b91` |
| VISS Trust and Telemetry 1.1.0 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| Platform FOTA Safe Stop 1.1.1 | `5b7087748877295837eb16a8bac02742dbae7328e54ba0b852fed2f5de6d3be9` |
| Vehicle Gateway requirements | `88c008dcb1e452f5fa60152dbdc0dad9d70fbf801cc2b1083574257c38856415` |
| Vehicle Simulation requirements | `79050e0b86162d04ab2f670af1238e1b319ebb6b161bb7e54ea9a1745a5003da` |
| D4 Decision Register | `5ad2a0a922907962c0b0d4712194404696cdc15d15db3d41b82058a0eafcca68` |
| Component/interface register (`IF-VEH-007`) | `85b2c5c1c96007f532a23947c05eedaada32af5509095569f42ef526d965ea89` |

Every digest must be rechecked immediately before future authorization.

## Independent Candidate Qualification Result

The clean isolated candidate exists at
`d4a20c85196ef7df81c78f992f6237c5eca8ff6c`, parent `8af302d`, tree
`f232db0ed28c2a5dc12009aa5197beee646d8703`, and changes exactly the fourteen
allowed paths. Independent local qualification completed on 2026-08-30:

- 18/18 core, 20/20 VISS and 24/24 shared-contract tests passed;
- ASan+UBSan core tests passed;
- socket/loopback, malformed-input, capacity/expiry, reset/generation and
  no-last-known-reuse cases passed; and
- the synthetic trace proved all ten VSS paths and atomic omission of the six
  controller paths when the handoff is missing.

The candidate is not merge-ready. The accepted deployment runs CARLA and the
Gateway on macOS, but the implementation uses a Linux-only Unix datagram peer-
credential path and throws on every non-Linux platform. `run_m6.py` enables
that path unconditionally, so the target Mac fails its startup gate. Darwin
documents reliable `LOCAL_PEERCRED`/`getpeereid` only for connected Unix
`SOCK_STREAM`, while this packet froze `SOCK_DGRAM`; changing the transport
requires a bounded D4-004/IF-VEH-007 correction before product edits.

The changed `runtime_carla.cpp` also lacks a full `CARLA_EGO_WITH_CARLA=ON`
compile proof because the pinned LibCarla CMake package is not currently
materialized and dependency retrieval was excluded. The candidate remains
preserved and clean. No merge or push is authorized until both blockers close,
the corrected target tests pass and this completion record is updated.

## Reviewed exact writable boundary

Only these fourteen paths may change or be created:

1. `CMakeLists.txt`;
2. `include/carla_ego_runtime/runtime_options.hpp`;
3. `src/runtime_options.cpp`;
4. `include/carla_ego_runtime/simulator_control_channel.hpp` — new;
5. `src/simulator_control_channel.cpp` — new;
6. `src/runtime_carla.cpp`;
7. `tools/external_control_protocol.py`;
8. `tools/external_control_controller.py`;
9. `tools/run_m6.py`;
10. `tests/external_control_protocol_test.py`;
11. `tests/m6_tools_test.py`;
12. `tests/simulator_control_channel_test.cpp` — new;
13. `docs/external-control-contract.md`; and
14. `docs/telemetry-contract.md`.

The implemented projection files at `8af302d`, VSS overlay, VISS server,
CARLA physical normalization and all launcher/UI/solution files are frozen.
A need for another product file returns a bounded change request.

## Exact handoff

1. `run_m6.py` creates one short per-run owner-only runtime directory and
   passes an explicit control-facts Unix socket path to both processes. No
   global, predictable or durable socket is allowed.
2. C++ binds one `AF_UNIX` `SOCK_DGRAM` receiver before the startup gate;
   directory mode is `0700`, socket mode `0600`, Linux peer credentials are
   verified, the maximum datagram is 4096 bytes and exactly one local
   controller is the producer. `recvmsg` truncation or oversize is rejected
   before JSON processing. No network listener is added.
3. After applying control and completing each successful `world.tick`, Python
   emits one versioned, closed JSON datagram containing run/ego identity,
   returned CARLA `frameId`, CARLA `simulationTime`, applied mode,
   transition state, control generation, reset generation, reset-in-progress
   and first-post-reset discontinuity. It contains no command token, session,
   operator identity or Safe Stop conclusion.
4. The controller state machine, not `controller-status.json`, owns the
   applied values. Generations are unsigned monotonic within the run. A
   requested mode is never reported as active until application succeeds.
   Preparation reports `PREPARING`; a failed transition reports `FAILED` and
   remains/applies `SAFE_STOP` as required by D4-004.
5. A last real completed pre-reset frame may report `PREPARING`,
   `Reset.InProgress=true` and the current generations. A blocking reset emits
   no fabricated frame. Canonical reset increments `Reset.Generation` only
   after success; the first real complete post-reset frame carries that
   generation, a new control generation where applicable,
   `Reset.InProgress=false` and `Reset.Discontinuity=true`. The next real frame
   clears discontinuity. Failed reset with no completed frame publishes no
   success evidence; UI operation progress is separate.
6. C++ validates schema/version, exact keys/types/enums/bounds, run/ego,
   strictly increasing frame and non-regressing generations. It holds at most
   four unmatched physical plus four unmatched control records, each for 250
   ms host-monotonic residence from first receipt, never a last-known-good
   substitute. Exact match removes both records immediately.
7. For each observed CARLA snapshot, C++ publishes the six control/reset facts
   only when an exact record with the same frame and simulation time is
   present. It attaches the physical snapshot's existing UTC source timestamp
   to the entire VSS snapshot. Either side may arrive first within the bound;
   malformed, duplicate, out-of-order, wrong-run, wrong-ego or wrong-time
   input is discarded. Missing/dropped/rejected input, or oldest-record
   eviction on capacity/expiry, makes the whole six-fact group absent for that
   frame and increments only a bounded diagnostic counter.
8. Datagram send is bounded and cannot block CARLA ticks. Backpressure or a
   disconnected receiver is explicit telemetry loss, not controller failure
   and never cached Safe Stop evidence. The handoff defines no stream,
   reconnect or history/replay protocol. A process restart creates a new
   per-run socket/run boundary and accepts only new frames. Shutdown removes
   only owned socket state.

## Tests and evidence

- Python state-machine tests cover every mode transition, idempotent request,
  failed preparation, monotonic control/reset generation and exactly-one-frame
  reset discontinuity.
- Codec tests cover canonical valid frames and unknown/missing/wrong-type,
  oversize, malformed JSON, invalid UTF-8, enum, range and identity failures.
- C++ channel tests cover permissions, one producer, reordered/dropped/
  duplicated/conflicting datagrams, bounded queue/backpressure, restart and
  cleanup.
- Integration tests drive synthetic physical snapshots and control datagrams
  in both arrival orders and prove all ten required paths share exact frame and
  source timestamp; no partial six-path group or prior-frame reuse appears.
- Existing runtime-option, projection, VISS protocol/network, Python tool and
  architecture tests remain green. Boundary scan, formatting, static compile,
  sanitizers where already available and `git diff --check` are required.

Exit evidence is a clean isolated commit, file-boundary report, exact test
commands/results, malformed-input matrix and a trace from controller tick to
the ten-path VSS snapshot. It authorizes neither mTLS nor live qualification.

## Exclusions and stop conditions

Excluded: Safe Stop thresholds/history/gate evaluation; Runtime changes;
selected-Unit/mTLS/trust; VDP/KUKSA; advisory writes; Dashboard/UI; Cloud;
scenario redesign; actor/tick ownership changes; dependencies; live CARLA,
VM or Unit use. Stop on contract ambiguity, need to poll a file, inability to
attribute a record to the exact frame/time/run/ego, need for blocking tick
I/O, generation wrap/regression, widened file boundary, dependency retrieval,
or any live/external action.

## Accepted review decisions

Accepted on 2026-08-29: the local handoff uses `AF_UNIX` `SOCK_DGRAM`, with
exactly one atomic record per completed CARLA frame and a non-blocking
controller send. The socket is restricted by filesystem permissions and the
C++ receiver verifies Linux peer credentials. Only an exact frame ID plus
simulation-time match may join the record to the physical snapshot. Missing,
dropped, duplicate or out-of-order input makes the complete control/reset fact
group absent for that frame. The transport adds no stream, reconnect protocol
or history/replay mechanism.

Accepted on 2026-08-29: the maximum datagram is 4096 bytes; `recvmsg`
`MSG_TRUNC` and oversize input are rejected before JSON processing. The join
may hold at most four unmatched physical snapshots plus four unmatched control
records, each for no more than 250 ms of host-monotonic residence from first
receipt. An exact match removes both records immediately. Malformed, duplicate
or out-of-order input is discarded. Capacity overflow or expiry evicts the
oldest unmatched record, leaves all six control/reset facts absent for that
frame and increments only a bounded diagnostic counter; it never reuses a
last-known value. These bounds are local transport tolerance, not OEM Runtime
Safe Stop freshness policy.

Accepted on 2026-08-29: only real completed CARLA frames may carry reset facts.
The last real pre-reset frame may show `PREPARING`, reset in progress and the
current generations; no record is invented while reset blocks. The first real
successful post-reset frame carries the incremented reset generation, a new
control generation where applicable, reset not in progress and one-frame
discontinuity; the next real frame clears it. Failure with no completed frame
creates no reset-success evidence. UI operation progress remains separate.

All three design choices are closed. The user explicitly authorized the exact
fourteen-path product implementation on 2026-08-29. That authorization becomes
effective only after this Gateway-only cascade is committed, every digest and
both source bases are rechecked, and the isolated product worktree is confirmed
clean. It does not authorize any excluded or live/external action.
