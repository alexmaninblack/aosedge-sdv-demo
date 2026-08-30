<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Gateway Controller-to-C++ Handoff Work Packet

- ID: `WP-P1-VEH-GATEWAY-CONTROLLER-CPP-001`
- Lane: `L-VEH`
- Increment: `IMP-02C`
- State: `BOUNDED MACOS CORRECTION AUTHORIZED — NOT STARTED`
- Version: 0.4
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

Committed solution readiness parent is
`aosedge-sdv-demo@107031a353308fc670d4a477e302e7a6bd278e55`; the accepted
Gateway correction cascade is identified by the exact content digests below
and must be committed plus rechecked before correction implementation:

| Input | SHA-256 |
| --- | --- |
| Simulator Control and Context 1.1.1 | `34e0912a0cd30ff04365468b4944a81ef6e7655e019c2539de915b66e0c120e4` |
| VISS Trust and Telemetry 1.1.0 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| Platform FOTA Safe Stop 1.1.1 | `5b7087748877295837eb16a8bac02742dbae7328e54ba0b852fed2f5de6d3be9` |
| Vehicle Gateway requirements | `39aaf18675a8b4160f734c075ca411919d99a90071afb19ab9c070e2eeaa2d8e` |
| Vehicle Simulation requirements | `75c2ba5936afaeb517e754ca5e424adf8f470b08031ec0af1f67b786a3a24fd0` |
| D4 Decision Register | `91842de2ec12a8f802a9bc2ae402e2db77af76ccf9d248ca1a44463a3943e556` |
| Component/interface register (`IF-VEH-007`) | `1bb198f8a63074bd2c133b439abd918b6730278fd553339145f1956d53cafb61` |

Every digest must be rechecked immediately before correction implementation.

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
`SOCK_STREAM`. The operator accepted the bounded D4-004/IF-VEH-007 correction
on 2026-08-30; it is now the sole authorized delta over `d4a20c`.

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
2. C++ binds and listens on one `AF_UNIX` `SOCK_STREAM` endpoint before the
   startup gate; directory mode is `0700`, socket mode `0600`, exactly one
   connection is accepted per run and the peer effective UID is verified with
   `getpeereid`/`LOCAL_PEERCRED` on Darwin or `SO_PEERCRED` on Linux. No
   network listener is added.
3. After applying control and completing each successful `world.tick`, Python
   emits one versioned, closed UTF-8 JSON body preceded by one unsigned
   big-endian 32-bit body length. The body contains run/ego identity,
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
8. Stream I/O is non-blocking and cannot block CARLA ticks. The body maximum is
   4096 bytes and the receiver retains at most one bounded partial frame. Zero,
   oversize, truncated or invalid lengths are rejected before JSON. Partial-
   write timeout, backpressure, EOF or disconnect makes the channel unavailable
   and omits the complete six-path group. There is no reconnect or
   history/replay protocol within one run. A process restart creates a new
   per-run socket/run boundary and accepts only new frames. Shutdown removes
   only owned socket state.

## Tests and evidence

- Python state-machine tests cover every mode transition, idempotent request,
  failed preparation, monotonic control/reset generation and exactly-one-frame
  reset discontinuity.
- Codec tests cover canonical valid frames and unknown/missing/wrong-type,
  oversize, malformed JSON, invalid UTF-8, enum, range and identity failures.
- C++ channel tests cover permissions, Darwin/Linux peer credentials, one
  producer, partial/coalesced frames, invalid length, reordered/dropped/
  duplicated/conflicting records, bounded queue/backpressure, EOF, restart and
  cleanup.
- Integration tests drive synthetic physical snapshots and control records
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

Superseding correction accepted on 2026-08-30: the local handoff uses one
connected `AF_UNIX` `SOCK_STREAM` per run with one unsigned-big-endian-32-
length-framed UTF-8 JSON body per completed CARLA frame and non-blocking I/O.
The socket is restricted by filesystem permissions and both peers verify the
effective UID using the accepted Darwin/Linux mechanism. Only an exact frame
ID plus simulation-time match may join the record to the physical snapshot.
Missing, dropped, duplicate or out-of-order input makes the complete
control/reset fact group absent for that frame. The transport adds no
reconnect or history/replay mechanism within a run.

Accepted correction on 2026-08-30: the maximum JSON body is 4096 bytes; zero,
oversize, truncated or invalid length and body input is rejected before JSON
processing, with at most one bounded partial frame retained. Backpressure,
partial-write timeout, EOF or disconnect makes the channel unavailable. The join
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
