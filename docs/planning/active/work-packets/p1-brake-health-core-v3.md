<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Health v3 Advisory Core Work Packet

- ID: `WP-P1-BHS-CORE-003`
- Lane: `L-BHS`
- Parent increment: `IMP-04`
- Review state: `ACCEPTED — IMPLEMENTATION AUTHORIZED`
- Version: 1.0
- Prepared: 2026-08-31
- Product implementation authorization: yes — exact nine-path boundary only
- Network, live platform, packaging, signing, publication, merge or push
  authorization: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Add the dependency-free C++17 Brake Health v3 advisory domain core after the
accepted v1 and v2 cores. The bounded implementation builds the exact typed
Brake maintenance request, persists its request/epoch/sequence lifecycle,
accepts only a matching factual Gateway Status and creates the correlated
Brake advisory fact for the existing bounded functional outbox.

This packet adds no KUKSA, VISS, KAC, gRPC, backend, Aos packaging or live
runtime integration. The exact nine-path source-only implementation boundary
is accepted and authorized; every external operation and excluded path remains
unauthorized.

## Exact Frozen Entry Base

| Item | Exact value |
| --- | --- |
| Product repository | sibling `brake-health-service` repository |
| Product commit | `63b0c5fd43572ff96c508abc5e35818218d3500a` |
| Product parent | `c5544f5f6de37f35a7fe1b34a5a2e9e399c1ab53` |
| Product tree | `7c2803c806001ab8bfb7eae44fbf8489f95ccdd5` |
| Required product refs | clean `main == origin/main ==` product commit |
| Authoritative contract-cascade commit | `3f4635a6ec08f845e2a4bbdf4bf70f318cfa537b` |
| Contract-cascade tree | `56124314f268390e4789feb835315cc6025f0e6b` |

A worker must use a new isolated one-writer product worktree from the exact
product commit. Any different commit, tree, dirty base or pre-existing v3 path
is a stop condition.

## Accepted Requirement Decisions

| ID | Exact accepted decision |
| --- | --- |
| `BHS-V3-RD-01` | An ordinary process, container or VM restart preserves `producerEpoch` and continues from the persisted next sequence monotonically without reuse. Restart never rotates the epoch and never restarts sequence numbering. |
| `BHS-V3-RD-02` | Only an explicit producer replacement or new producer lifecycle rotates `producerEpoch`, exactly once, and starts its sequence at `1`. R0 destroys the old producer state. Late old-epoch evidence may remain historical evidence but can never change current state or advisory. |

The accepted v2-to-v3 transition is not an implicit producer replacement. It
reuses the exact v2 model state, producer epoch and next advisory sequence.
Changing either decision requires the decision owner to update this packet and
the authoritative contracts before implementation continues.

## Frozen Contract Inputs

All hashes are raw file SHA-256 at the authoritative contract-cascade commit.

| Input | Version or role | SHA-256 |
| --- | --- | --- |
| `CR-BHS` | current accepted requirements | `46e2e5302fa8a265a45217e4ebf092b34ca900eaac3c1564a574e6604f9cc7f2` |
| D4 decision register | accepted D4-016.4/.5 plus RD-01/RD-02 cascade | `e2c731ff99e7be8099b58b13ee9e372b8688863ade42c744bc3eadb859e78c08` |
| Brake advisory-policy README | accepted lifecycle interpretation | `f6234b2502e374037629bd190536d46ab10f6411bb433877731e28b3021f7af2` |
| Brake advisory policy | 1.0.1, byte-identical accepted policy | `13216b51647525d48b83eb79bd47444ccb392d1a51a7ffd18b593d4c91f52467` |
| Brake advisory request fixture | canonical valid `SET` | `a38378564e442a0d7ecd9b203ee0416aa89c4159f691c1f616d27ecfcbc59068` |
| Typed QM advisory profile | 1.0.2 | `f7ae78148fb3b3265c8b773117126665afb1edd97a73f59db5a1f3af7c223487` |
| Typed QM Request schema | closed schema v1 | `f2102fd948734a714160efb8ee09885107d58da1daabd95771dce56785149910` |
| Typed QM Gateway Status schema | closed schema v1 | `1e0ecb28cc7548c65f1352b4c8b5874871400b8a83050a1b527c5f58f8493661` |
| Brake runtime README | D4-016.5 / lifecycle 1.1.0 | `066d23506302fc094385b666081385b2cef8fc8c8fbabbf313a50020dcefea65` |
| Brake runtime profile | 1.1.0 | `cc90a091e044995a49ad886ae6a5f000c579c8a43a84dbaab8a6edf2a8c492c4` |
| Shared evidence profile | 1.1.0 | `657c4d0dc83fd2a98b2a827172f1cb408965105865903397fc7ba07564f5c0d2` |
| Brake model profile | 1.0.0 | `7749dff2dd340f05ae5f3c90912d65007ad48c52a5136ab0e165a83109d55f53` |
| Brake model persistent-state schema | 1.0.0 | `350a38547490547f3bf963971fb9a2f5e0cc7c4c4ea4d96b746b392779fc7f79` |
| Brake model state fixture | 1.0.0 | `5a9b64c8f4fe8295e018c484b925f79f221659fb8106cfea87968b6cb0ad9240` |
| Brake advisory-fact schema | 1.0.0 | `41bf4de82143077fd6bb675abb63150ad5d886f9e5f4d3547585c50bfb79d67a` |
| Brake advisory-fact fixture | 1.0.0 | `a2dc0c016d5281c9accead1d6447600d4a2c3736acaef1f725a2831efe334cad` |
| Brake Cloud API profile | 1.0.0 | `b539571d80d76fa11234f3e41b0646ff6d6c4235be5de933448ebc9fafeb3891` |
| VDP compatibility profile | 1.0.1 | `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871` |
| VISS trust/telemetry profile | 1.1.0 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |

The policy JSON remains byte-identical while the accepted lifecycle meaning is
made explicit in D4, CR-BHS, the policy README, runtime profile and shared
evidence profile. A worker may not reinterpret persistence from only one of
those inputs.

## Product-Base Compatibility Digests

| Product-base file at `63b0c5f` | SHA-256 |
| --- | --- |
| `CMakeLists.txt` | `0ab6067578de68e1fb71bb5a5838b10df044e215b6653f66ab4d45e06c39636e` |
| `include/brake_health/v2/model.hpp` | `3b42fc5507f85c6d22f2bba2ef837b35c7036d5fd6bbbc5014d5dcfd7f7b3068` |
| `include/brake_health/v2/messages.hpp` | `fc2556892c29654b19222289d4036d67f83bc29b44db3d75aee45b990a15f633` |
| `include/brake_health/v2/state_store.hpp` | `92fec9e98c47f097013f43d3f7e44695d966209588d17bc6f19f794dbcc0d048` |
| `src/v2/messages.cpp` | `a334718d4afe1becd7ea1aeaa802f3e7cd8d3e0817b11e0c6f913270bbf1ed13` |
| `src/v2/state_store.cpp` | `0d2f1646e7f6ad5d7c869f9d324436f4791eace0f6c873124e15ef355a655c4b` |
| `tests/cpp/v2/v2_tests.cpp` | `0cbdbc708b23199e655cc87a1a59d41f0e05130df26501fb9b0aa438447b6148` |
| `tests/test_v2_cpp.py` | `44ac35888b1d0c4fd2e09a95126df661c6ee0b623e93ca0ce02f0b55d75f4e6e` |

Every v1 and v2 source/test byte is immutable in this packet. The v3 core may
call their public interfaces but may not copy, patch or bypass their accepted
behavior.

## Exact Nine-Path Writable Boundary

Only these product-repository paths may change under this implementation
authorization:

1. `CMakeLists.txt`;
2. `include/brake_health/v3/advisory.hpp`;
3. `include/brake_health/v3/messages.hpp`;
4. `include/brake_health/v3/state_store.hpp`;
5. `src/v3/advisory.cpp`;
6. `src/v3/messages.cpp`;
7. `src/v3/state_store.cpp`;
8. `tests/cpp/v3/v3_tests.cpp`; and
9. `tests/test_v3_cpp.py`.

All other product paths are read-only. In particular, `v1/**`, `v2/**`, the
packaged scaffold, compatibility metadata, dependency inventory, repository
documentation and Aos packaging are outside this packet.

## Exact Proposed Core Behavior

### v2-to-v3 activation and persistent advisory state

1. The core accepts an already validated v2 `ModelState` plus injected Unit,
   service, VDP and clock metadata. It implements no telemetry subscription or
   model evaluation.
2. First v3 activation copies the exact persisted v2 `producerEpoch` and
   `nextAdvisorySequence` into a private v3 advisory-state root. It never
   changes the accepted v2 model-state bytes or v2 identity ledger.
3. When the persisted accepted band is `INSPECTION_RECOMMENDED`, and no request
   binding exists for the exact `lastAssessmentId`, activation emits exactly
   one request using that assessment as `decisionId`. It creates no assessment
   or band-change event. Reopen/retry returns the already persisted request
   bytes rather than allocating another sequence.
4. A later accepted new transition into `INSPECTION_RECOMMENDED` uses the new
   assessment ID exactly once. A same-decision duplicate reuses the committed
   request identity and bytes. A same identity with conflicting content or
   metadata quarantines v3 state as `NOT_READY_STATE`.
5. The private state root is injected in tests and maps later to
   `/storage/brake-health/advisory-state/v1`. Directories are `0700`, files are
   `0600`; state and pending action use same-directory temporary write, file
   synchronization, atomic rename and directory synchronization. Unknown,
   malformed, oversized or digest-conflicting state is quarantined without
   silent reset.

### Request identity, lease and refresh

1. Emit only the closed D4-008 `SET` Request to
   `Vehicle.OEM.BrakeHealth.Advisory.Request` with recommendation
   `INSPECTION_RECOMMENDED`, reason `PREDICTED_BRAKE_DEGRADATION`, service
   version `3.0.0` and model version `brake-condition-demo-v1`.
2. Request UUIDv5 uses namespace
   `894e102e-5380-5c9d-a6f7-46f00b234725` and exact LF-joined fields
   `producerEpoch`, decimal `sequence`, `operation`, `decisionId`. The core
   reuses the existing tested v2 UUIDv5/SHA implementations without changing
   v2 sources.
3. Persist the complete canonical request, identity binding and incremented
   next sequence before returning a write action. An ambiguous adapter result
   can only retry the identical canonical bytes.
4. Lease duration is exactly 30 seconds. While the same valid condition is
   active, refresh eligibility begins at 20 seconds using an injected clock;
   each refresh allocates one new sequence and request ID and is persisted
   before action. Tests never sleep.
5. The current monotonic model creates no `CLEAR`. Stop, crash, restart,
   unavailable Gateway or lost KUKSA never fabricates clear. Future explicit
   clear support is outside this packet.

### Owner-approved producer lifecycle

1. Reopening the same state after an ordinary process, container or VM restart
   preserves the exact epoch and continues from the persisted next sequence.
   No sequence can be reused or reset by a retry or ordinary restart.
2. An explicit replacement/new-producer entry point requires a caller-supplied
   new UUIDv4 epoch and an explicit lifecycle operation. It rotates once,
   starts at sequence `1` and persists that lifecycle before any request.
   Reopening the replacement state is ordinary restart and cannot rotate again.
3. Reusing the current or any retired epoch for explicit replacement is
   rejected. Late Request/Status/fact evidence from a retired epoch is never
   allowed to update the current binding, Gateway state, refresh state or
   outbox fact.
4. R0 is not simulated by a reset API. Destruction of the disposable Unit
   overlay removes the v3 root. The core has no hidden fallback file, retained
   epoch database or migration from retired R0 state.

### Gateway Status and advisory fact

1. The core consumes a caller-supplied, schema-validated Gateway Status. This
   packet implements no KUKSA/VISS reader. Status is actionable only when
   `requestId`, `producerEpoch` and `sequence` all match one exact committed
   Request.
2. Only matching `APPLIED` or `CLEARED` is application evidence. `RECEIVED` is
   factual non-terminal evidence; `REJECTED`, `EXPIRED` and `FAILED` are
   factual terminal outcomes. No state falls back to another target, command
   or motion path, and a single failure does not silently redefine process
   health.
3. Every newly accepted exact status creates at most one canonical
   `BRAKE_ADVISORY_FACT` with the frozen Brake Cloud schema, original Request
   fields, injected `recordedAt`, Gateway fields and exact canonical content
   SHA-256. Duplicate status reuses the committed fact; conflicting status for
   the same identity quarantines the advisory state.
4. The v3 store exposes a bounded pending-fact inventory and exact durable-ACK
   deletion hook for later adapter composition. Combined v2/v3 functional
   outbox limits remain 64 messages and 1 MiB; admission failure reports
   `DERIVED_OUTBOX_FULL` but does not erase the current local assessment or
   valid active advisory state. This packet performs no HTTP delivery.

## Required Deterministic Verification

An authorized implementation must add and pass tests for:

- clean offline C++17 configure/build and CTest for v1, v2 and v3;
- canonical bytes matching the frozen valid `SET` fixture and UUIDv5 known
  answer, plus wrong field order/delimiter, metadata and schema negatives;
- first v3 activation in persisted `INSPECTION_RECOMMENDED`, exact one-time
  request, reuse of last assessment ID and absence of synthetic assessment or
  event;
- non-inspection activation, new transition, same-decision duplicate and
  conflicting-decision/digest behavior;
- exact 30-second lease, 20-second refresh boundary, new refresh sequence and
  ID, and identical-byte ambiguous retry;
- process, container and VM restart fixtures proving the same epoch and
  strictly continued sequence;
- explicit replacement proving one rotation and sequence `1`, repeated reopen
  without another rotation, rejected current/retired epoch and R0 fresh-state
  behavior;
- delayed old-epoch Request, Status and fact inputs proving no current-state,
  advisory or outbox mutation;
- exact Gateway Status correlation and all six states, including mismatched
  request/epoch/sequence, duplicate and conflict;
- canonical advisory fact and content digest matching the frozen fixture,
  duplicate suppression and exact ACK-only deletion;
- 64-message and 1-MiB boundaries, exact-byte edge, overflow without local
  advisory loss and malformed inventory quarantine;
- interruption at every state, request, lifecycle and fact write stage,
  followed by deterministic recovery or explicit `NOT_READY_STATE`;
- unknown schema, malformed/oversized state, digest conflict, sequence
  rollback and missing persistent input negatives;
- unchanged full v1 and v2 suites, byte-identical v1/v2 tracked inputs,
  repository-boundary tests and quality gate;
- compiler warnings as errors and Address/UndefinedBehavior sanitizer runs
  over the owned v3 suite when supported by the existing toolchain; and
- exact changed-path equality with the nine-path writable boundary.

Tests inject epochs, clocks, roots, write faults and metadata. They do not
sleep, use uncontrolled randomness, access a network, retrieve dependencies or
silently skip an owned assertion.

## Explicit Exclusions

- no v1 or v2 source/test change and no model, episode or assessment change;
- no KUKSA/VISS/gRPC/protobuf transport or resource discovery;
- no KAC, `AOS_SECRET`, JWT, token file, IAM or permissions implementation;
- no backend HTTP client, retry scheduler, SSE, Dashboard or Cloud operation;
- no arbitrary text, Tire target, arbitrary VSS write, motion or safety action;
- no service executable composition, health endpoint or structured-log sink;
- no compatibility, Aos metadata, permission, quota or packaging change;
- no new dependency, downloaded JSON/crypto framework or package install;
- no ARM64 artifact, Builder, image, CARLA, VM, Unit, signing, publication,
  FOTA or SOTA action; and
- no merge, push or product `main` mutation.

## Stop Conditions

Stop and return for review if:

1. the exact product base/tree, contract-cascade commit/tree or any frozen
   digest differs;
2. a v1/v2 file or path outside the nine-path boundary must change;
3. v2-to-v3 activation cannot reuse the exact persisted epoch/next sequence
   without changing v2 state bytes;
4. atomic request/lifecycle/fact recovery requires a database or new
   dependency;
5. a caller-selected target, path, recommendation, reason, namespace, lease or
   refresh value would be required;
6. Gateway Status cannot be correlated by the exact request/epoch/sequence;
7. explicit replacement cannot be distinguished from ordinary restart or R0;
8. a late old-epoch input can affect current state under any tested path; or
9. any owned, inherited, sanitizer, quality or boundary gate fails.

## Authorization Record

Accepted and implementation-authorized on 2026-08-31 after independent packet
review and direct owner approval. Authorization is limited to the exact
nine-path product boundary above. Product implementation has not yet started;
all network, live platform, packaging, signing, publication, merge and push
operations remain separately gated.
