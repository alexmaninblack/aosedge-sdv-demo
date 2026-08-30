<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Brake Health v2 Domain Core Implementation-Review Work Packet

- ID: `WP-P1-BHS-CORE-002`
- Lane: `L-BRAKE`
- Increment: `IMP-04-BHS-CORE-002`
- State: `DESIGN REVIEW COMPLETE / READY FOR IMPLEMENTATION REVIEW — IMPLEMENTATION NOT AUTHORIZED`
- Prepared: 2026-08-29
- Repository: `brake-health-service`
- Proposed frozen source base:
  `7c0a658ba2106a7274e61296746dcdd3008db26b`
- Proposed branch: `codex/imp-04-bhs-core-v2`
- Integration owner: Demo Integration Coordinator

## Outcome

After a separate explicit implementation authorization, implement the
dependency-free C++17 Brake Health v2 domain core over the source-complete v1
core. The bounded
increment owns a normalized completed-episode input, deterministic synthetic
feature/model execution, closed assessment and optional band-change-event
messages, crash-safe exactly-once model state and a bounded derived-message
outbox. It also proves that v2 analytics may start while the retained v1 spool
continues to exist for later adapter-owned draining.

This is a source-only implementation-review packet. It creates no executable
Service composition, KUKSA subscription, backend sender, Aos package or
vehicle artifact and grants no implementation authority by itself.

## Authorization Status and Accepted Review Decisions

This packet is ready for implementation review but is deliberately **not an
implementation authorization**. The accepted D4-016.3 package and its
2026-08-29 cascade now freeze the model identity, complete input, conversion,
arithmetic, eligibility, identity/provenance, timestamps, state/outbox behavior
and deterministic fixtures needed for independent implementations.

`BHS-V2-RD-01` through `BHS-V2-RD-10` were accepted by the decision owner on
2026-08-29. Their authoritative contract/fixture cascade is complete and the
frozen digests below are refreshed. Decision closure and implementation
authorization remain distinct; no branch or product edit may begin without a
separate operator authorization.

| ID | Contract issue | Proposed or accepted closure |
| --- | --- | --- |
| `BHS-V2-RD-01` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | There is no complete 12-signal, 10 Hz normalized episode input fixture. The accepted assessment is an output fixture only; its 30 ACTIVE samples, three-second logical duration and 0.5-second stated source-window span cannot serve as one cadence-consistent input vector. | Add one closed complete synthetic 12-signal PRE/ACTIVE/POST golden input at 10 Hz plus invalid/boundary companions. Its 30 ACTIVE samples have logical duration `30 / 10 Hz = 3.0 s` and a first-to-last ACTIVE timestamp span of `2.9 s`; `sourceWindowStartTimestamp`/`EndTimestamp` cover the full retained PRE/ACTIVE/POST episode. Update the golden assessment/event timestamps, canonical content and digests to match while preserving normalized features `8000/6000/8000/5000/6000`, load `6750` and wear `54 -> 62`. |
| `BHS-V2-RD-02` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The five feature names and normalizers are accepted, but sample reduction is not exact. | Freeze the exact five formulas below over the reviewed fixed-point inputs and in the stated operation order. Use positive round-half-up for every division, clamp each normalized feature to `0..10000` before the weighted load, and use only integer/rational intermediates. The D4-003 scripted demo timeline qualification is at most 7 seconds nominal and at most 8 seconds in every 20/20 scripted run; this is a demo acceptance budget, not a production KPI. |
| `BHS-V2-RD-03` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | UUIDv5 name-field lists do not define byte concatenation. The existing fixtures can be reproduced by LF-joining the ordered values, but that rule is implicit. | Encode each ordered field as its exact UTF-8 bytes after rejecting any field containing CR (`0x0d`), LF (`0x0a`) or NUL (`0x00`); join fields with exactly one LF byte (`0x0a`) and no trailing LF, then apply RFC 4122 UUIDv5. Freeze the ordered field lists and both current resulting UUIDs in the contract. UUIDv5 is deterministic identification only, never authentication, integrity protection, signing or a credential. |
| `BHS-V2-RD-04` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The accepted transaction protocol does not define the almost-full-outbox case when an assessment and band-change event are created together. | Treat one assessment plus its optional band-change event as one atomic admission. Admit both messages or neither. If the pair would exceed either outbox item or byte limit, advance condition state and the recent-source-event ledger exactly once, enqueue neither message, return/log the typed `DERIVED_OUTBOX_FULL` outcome, never fabricate a later message for that already-applied source event and continue future local operation. |
| `BHS-V2-RD-05` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The exact internal journal/commit-marker file layout and recovery precedence are not frozen. | Use one immutable transaction journal per assessment below the accepted model-state root, containing canonical before/after state and a manifest binding their digests, the assessment, optional event and the `ADMIT` or `OVERFLOW_NOT_ENQUEUED` disposition. Synchronize the journal, atomically replace and synchronize `state.json`, and for `ADMIT` publish the assessment plus optional event as one staged bundle directory atomically renamed on the same outbox filesystem; synchronize its files, directories and final outbox parent. Then atomically create and synchronize the commit marker. Recovery may proceed only when current state exactly matches journal `before` (apply once) or journal `after` (complete publication/marker without reapplying); every other state/generation/digest combination is quarantined as `NOT_READY_STATE`. Remove a committed journal only after verifying its admitted bundle or overflow disposition. Never double-advance wear, duplicate an event or silently reset state. |
| `BHS-V2-RD-06` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | `ASSESSMENT_SKIPPED_INPUT_QUALITY` is an accepted outcome but has no functional wire schema or persistent-result schema. | Keep `ASSESSMENT_SKIPPED_INPUT_QUALITY` as a typed local, non-wire and non-persistent outcome with exactly one closed reason: `EPISODE_NOT_COMPLETE`, `MISSING_REQUIRED_SIGNAL`, `STALE_SAMPLE`, `NON_FINITE_VALUE`, `OUT_OF_RANGE_VALUE`, `NON_MONOTONIC_SOURCE_TIME`, `INSUFFICIENT_ACTIVE_SAMPLES` or `INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`. It produces no assessment/event and mutates no state, generation, band or recent-source-event ledger. Later structured-log and readiness projection remain adapter/runtime work; no new wire message or persistent result is invented. |
| `BHS-V2-RD-07` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The VDP paths are floating-point values, but their deterministic quantization before integer feature arithmetic is not frozen. | Perform exactly one adapter-owned conversion/quantization: apply the normative source-unit conversion before quantization, reject non-finite values, normalize negative zero to zero, scale and round an exact half away from zero, and reject accepted-path range or target-integer overflow. Supply the core only milli-km/h speed, milli-m/s² acceleration, milli-percent brake effort, milli-degree steering, milli-km/h wheel linear speed and milli-degree/s wheel angular speed; the core performs no second quantization. Freeze below/half/above vectors for every unit, including negative-capable units and range/overflow negatives. |
| `BHS-V2-RD-08` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The assessment requires both `modelArtifactSha256` and `modelConfigSha256`, but the accepted package identifies only the profile digest and defines no separate runtime model file. | Bind `modelArtifactSha256` to the immutable deployed Brake Health Service artifact digest that contains the compiled model, and bind `modelConfigSha256` to the exact accepted model-profile SHA-256. Inject both as distinct immutable deployment metadata; the core neither discovers nor hashes its installation. Do not invent a separate model file. A future separately packaged model requires a versioned contract change. |
| `BHS-V2-RD-09` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | `minimumQualifiedEpisodeLoadBps: 5000` is accepted for D4-003 live qualification, but the profile does not explicitly say whether lower load suppresses a locally valid assessment. | Treat 5000 only as the D4-003/demo qualification threshold, never as a runtime eligibility filter. Every otherwise eligible lower-load episode emits its deterministic assessment and advances deterministic state; a band-change event appears only on an actual band crossing. A scripted run below 5000 is a calibration failure, never a reason to suppress, alter or fabricate model output. |
| `BHS-V2-RD-10` — **ACCEPTED 2026-08-29; AUTHORITATIVE CASCADE COMPLETE** | The assessment timestamps do not state whether “window” means the full PRE/ACTIVE/POST episode or only ACTIVE, and the event's `effectiveAt` rule is implicit. | Supply the complete retained PRE/ACTIVE/POST episode to v2; features use only ACTIVE (wheel dispersion only its qualified near-straight subset). `sourceWindowStartTimestamp`/`EndTimestamp` are the first/last retained sample times, `assessedAt` is an injected processing time not earlier than the end and reused on retry/recovery, and band-change `effectiveAt` equals the source-window end rather than processing/persistence/transport/backend time. Freeze these relations in the consistent golden pair. |

Changing any accepted closure above requires the decision owner to update this
packet and the authoritative contract together.
A worker may not choose an alternate formula, fixture, UUID encoding or
persistence behavior locally.

### Accepted arithmetic and fixed-point boundary for `BHS-V2-RD-02`/`07`

Let `RHU(n/d)` mean positive integer division rounded half up, and clamp every
normalized feature result to `0..10000` before weighted-load evaluation. All
inputs below are the reviewed fixed-point integers, the operations execute in
the listed order and no binary floating-point value enters the decision path.
The adapter first performs the normative source-unit conversion, rejects a
non-finite result, normalizes negative zero to zero, scales to the target milli
unit, rounds an exact half away from zero and rejects accepted-path range or
target-integer overflow. This is the only conversion/quantization boundary;
the core consumes the resulting integers without a second quantization.

1. `peakDecelerationMilliMps2 = max(0, max(-longAccelMilliMps2))` over all
   ACTIVE samples; `peakDecelerationBps = RHU(peak * 10000 / 8000)`.
2. `activeDurationMilliseconds = activeSampleCount * 100`; its basis points
   are `RHU(durationMs * 10000 / 5000)`.
3. `speedReductionMilliKph = max(0, firstActiveSpeed - lastActiveSpeed)`;
   its basis points are `RHU(reduction * 10000 / 40000)`.
4. `meanBrakeMilliPercent = RHU(sum(activeBrakeMilliPercent) /
   activeSampleCount)`; its basis points are
   `RHU(max(0, meanBrake - 50000) * 10000 / 50000)`.
5. For each qualified near-straight ACTIVE sample, linear dispersion is
   `RHU((maxLinear-minLinear) * 10000 / max(maxLinear, 5000))`. Angular
   dispersion first takes each wheel's absolute milli-degree/s value, then is
   `RHU((maxAngular-minAngular) * 10000 / max(maxAngular, 30000))`. Episode
   wheel dispersion is the maximum linear or angular sample result. The raw
   output ratio is that accepted basis-point result divided by 10000, and its
   normalized feature is `RHU(wheelDispersionBps * 10000 / 1500)`.
6. `episodeLoadBps = RHU((30*peak + 20*duration + 15*reduction +
   15*brake + 20*wheel) / 100)`. Eligibility is independent of the accepted
   5000 load qualification threshold; an otherwise eligible lower-load episode
   still produces its deterministic assessment and advances state, with a band
   event only on an actual crossing. D4-003 separately proves the live
   presenter stimulus reaches at least 5000 on every required repeat. A
   below-5000 scripted run fails calibration; it never changes model output.

The authoritative golden input must exercise these equations and reproduce
raw features `6.4`, `3`, `32`, `75`, `0.09`, normalized features
`8000/6000/8000/5000/6000`, load `6750`, wear increment `8`, wear `54 -> 62`
and `MONITOR -> INSPECTION_RECOMMENDED`.

The D4-003 scripted demo qualification must observe this v2 assessment and
band change within at most 7 seconds nominally and within at most 8 seconds in
all 20 of 20 scripted runs. This bound is a controlled demo acceptance budget;
it is not a production latency, reliability, safety or network KPI.

## Exact Proposed Source Base

| Item | Exact value |
| --- | --- |
| Product commit | `7c0a658ba2106a7274e61296746dcdd3008db26b` |
| Product parent | `04abe5bacc47e849c6a6fe4fccb64e8a15157d8f` |
| Product tree | `0b2c25d5b47d683420539d9f4fde6c12a292b4e9` |
| Solution baseline used for this proposal | `bcc7975d4aa3e3ed3c6b617abcd47b6bb18c88fd` |

The proposed product base is the isolated, source-complete
`WP-P1-BHS-CORE-001` commit. Product `main` need not move before this packet,
but the v2 worker must branch from the exact commit above in a separate clean
worktree. A different commit or dirty base stops work and requires review.

## Frozen Contract Inputs

| Input | Version or revision | SHA-256 |
| --- | --- | --- |
| `CR-BHS` | 0.9 | `c0199dd5b08d89ad8aa98ad131351463070d2a6641a1be0ed9dcdf6492f72a26` |
| D4 decision register | accepted D4-016.3 byte/arithmetic closure, D4-016.5 and D4-017 | `d4e95f59d7b5e5189d215af7dc1db2363efd94200f7736d2845207d9c5023503` |
| Brake model README | 1.0.0 / closure 2026-08-29 | `477c9630b893f4fca42dcd286bc23c7b8737ce3418d2da80f54f3239fe98f11f` |
| Brake model profile | 1.0.0 | `7749dff2dd340f05ae5f3c90912d65007ad48c52a5136ab0e165a83109d55f53` |
| Completed-episode input schema | 1.0.0 | `72913fbfee22d81a09106a80c7354d8f03f38600e1d9ada8ea56a8a6156118c5` |
| Complete 80-sample golden input | 1.0.0 | `a989204bb82d48e512d8771f8e36102a3f9a8db59a26b6209d2943ec246e170d` |
| Invalid-input cases | 1.0.0 | `d63d80b2e8f8d5e02ddaa24ecbb1532aea80694ed5a552b7c3329a26a36ac222` |
| Conversion/quantization cases | 1.0.0 | `deb8d15e0bad1ddec562d3b5a6fcaf1121cec41f467c4e040924d1efc4572fa7` |
| Assessment schema | 1.0.0 | `0c47d793bb4e31852c0452b92c901514d582c16a479f7107d15e02f0d22dc1e9` |
| Band-change event schema | 1.0.0 | `d88bf8882f68b25980dc23987149d4f57c25eee7bed371af419998a053a55e66` |
| Persistent-state schema | 1.0.0 | `350a38547490547f3bf963971fb9a2f5e0cc7c4c4ea4d96b746b392779fc7f79` |
| Golden assessment fixture | 1.0.0 | `84c7deaea38a0ed4c8f95a9aabda1dd7d89ab96d76cd09298f11f27e52b8301d` |
| Golden event fixture | 1.0.0 | `4abcf514a6d454e7216325a62a2aee3416e1ef07636f318ed5315b67fd723578` |
| Golden state fixture | 1.0.0 | `5a9b64c8f4fe8295e018c484b925f79f221659fb8106cfea87968b6cb0ad9240` |
| Brake runtime README | D4-016.5 / 1.0.0 | `fc9ec25744fb11648b0cace9e9ca80477f49f3d76b27c03a8d9970f4daa405fd` |
| Brake runtime profile | 1.0.0 | `1c2816a83c0f64f7f02f1656a73580871c3c45e108a78e5791d9d6462963a17c` |
| VDP compatibility profile | 1.0.1 | `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871` |
| VISS trust/telemetry profile | 1.1.0 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| v1 window profile | 1.0.0 | `2cf82973051b37e92941fc67c0682d03782b9288dee017b5e6740266e54c20b9` |
| Brake Cloud durable ACK schema | 1.0.0 | `778f176d85ccdb7c177380c145783a4c0d2c26d1324759f972f02765cc3e68d9` |
| Brake Cloud API profile | 1.0.0 | `b539571d80d76fa11234f3e41b0646ff6d6c4235be5de933448ebc9fafeb3891` |

The accepted `BHS-V2-RD-01` through `BHS-V2-RD-10` cascade is represented by
the exact authoritative digests above. This closes design review but is not a
start permission; any later byte change requires a reviewed digest refresh.

## Product-Base Compatibility Digests

| Product-base file at `7c0a658` | SHA-256 |
| --- | --- |
| `CMakeLists.txt` | `0110fd460030d3f19b7397231c761eb1e4aa8e7b98e528463752fca4711057dc` |
| `include/brake_health/v1/model.hpp` | `bd2fa01599259645c42c64a7ed157875e531fffc884ebcfa1fb094fa444094bd` |
| `include/brake_health/v1/window.hpp` | `e1da3cdceaf0364fd872129369cc9569e161bf029bd6db7c1877c27d43ff5ccb` |
| `include/brake_health/v1/messages.hpp` | `f607dea325e17f0f321b6b6acff12fad3a2fa002ddb9382f6112485113eeda4c` |
| `include/brake_health/v1/sha256.hpp` | `46e09b45f5fe26f912c1894bcd5398312bfa300b26a697ca778a68ce8ecc4e1f` |
| `include/brake_health/v1/spool.hpp` | `a0a4b9dac501c5069ad5c8d44cc8b9642a98c3d2d5d344e770a7cdc4f5d654eb` |
| `src/v1/sha256.cpp` | `2ff9c5d4e53311293cdde1acd5a668b8ac5d5899402b96fa47c48cb633107f2f` |

No v1 source file is writable in this packet. Any need to change the accepted
v1 behavior or public types is a stop condition and a separately reviewed
compatibility change.

## Proposed Writable Boundary

Only the following product-repository paths may change after authorization:

- `CMakeLists.txt`;
- `include/brake_health/v2/episode.hpp`;
- `include/brake_health/v2/model.hpp`;
- `include/brake_health/v2/messages.hpp`;
- `include/brake_health/v2/state_store.hpp`;
- `src/v2/model.cpp`;
- `src/v2/messages.cpp`;
- `src/v2/state_store.cpp`;
- `tests/cpp/v2/v2_tests.cpp`;
- `tests/test_v2_cpp.py`;
- `README.md`; and
- `docs/architecture.md`.

The documentation changes may describe only source-complete v2 domain status,
the unchanged scaffold executable and the remaining adapter/packaging/live
qualification gates. No `v1/**`, executable scaffold, packaging metadata,
compatibility metadata, builder, dependency manifest or license file is
writable.

## Exact Behavior Proposed for Separately Authorized Implementation

### Completed v2 episode boundary

1. Accept a caller-supplied, already completed D4-016.1 episode with one UUIDv4
   source event, terminal state and retained 10 Hz PRE/ACTIVE/POST samples. The
   core derives source-window timestamps under the reviewed `BHS-V2-RD-10`
   rule; it does not subscribe to KUKSA or own the 30-to-10 Hz adapter.
2. Each v2 sample contains exactly the 12 accepted model inputs in the reviewed
   fixed-point units, source time, source age, phase and complete/fresh quality.
   Lateral/vertical acceleration, accelerator pedal, hidden CARLA truth and any
   health label are absent.
3. Only `COMPLETE` is assessable. At least five ACTIVE samples and five
   near-straight ACTIVE samples at speed at least 10 km/h, absolute steering
   at most 5 degrees and age at most 250 ms are required.
4. A duplicate source event found in the recent ledger returns the already
   committed result identity without advancing wear or creating new bytes.
   Same identity with incompatible committed digests quarantines state.

### Synthetic feature and condition model

1. Implement only `brake-condition-demo-v1`, model version `1.0.0`, profile
   `DEMO_PRECONDITIONED` and provenance `DEMO_SYNTHETIC`.
2. Use the reviewed one-time fixed-point normalization and integer/rational
   intermediate arithmetic for basis-point conversion and
   positive round-half-up. No floating-point comparison may decide a threshold
   or band. Raw feature values in output use a single deterministic canonical
   representation.
3. Compute the five features and 30/20/15/15/20 weighted episode load exactly
   as accepted through `BHS-V2-RD-02`. Reject any configuration digest or model
   identity different from the frozen candidate.
4. Start missing v2 state at generation zero, wear 54, score 46 and `MONITOR`.
   An eligible episode increments wear by
   `4 + round_half_up(6 * loadBps / 10000)`, capped at 100; score is
   `100 - wear`; bands remain `GOOD=70..100`, `MONITOR=40..69` and
   `INSPECTION_RECOMMENDED=0..39`.
5. A rejected episode produces only the typed local, non-wire and
   non-persistent `ASSESSMENT_SKIPPED_INPUT_QUALITY` outcome with exactly one
   accepted `BHS-V2-RD-06` reason. It creates no assessment or event and
   mutates no state, generation, band or recent-source-event ledger. Later
   logging/readiness projection is adapter/runtime-owned.
6. There is no live training, mutable/downloaded model, network inference,
   Cloud decision, production diagnostic, remaining-useful-life or safety
   claim.

### Closed derived messages

1. Emit exactly one schema-valid `BrakeHealthAssessment` for each newly
   eligible source event and an additional `BrakeHealthEvent` only when the
   accepted condition band changes.
2. Bind all metadata and provenance exactly to the accepted schema. Inject
   Unit/service/VDP artifact identities and deterministic assessed time; bind
   the compiled-model artifact/config identities through the reviewed
   `BHS-V2-RD-08` rule. The core neither discovers installed components nor
   hashes an artifact outside its supplied immutable metadata.
3. Create assessment and event UUIDv5 values from the accepted namespaces and
   the reviewed exact LF-joined name encoding. Implement only the minimal unkeyed
   SHA-1 operation required by RFC 4122 UUIDv5 and prove standard known-answer
   vectors. Do not present it as a credential, signer or general security API.
4. Serialize the two closed message families only, in RFC-8785-compatible key
   order and number/string form. Reuse the already tested v1 unkeyed SHA-256
   implementation without changing v1 sources. Maximum canonical message size
   is 16 KiB.
5. Normal v2 never creates or enqueues a v1 window chunk/completion. Retained
   v1 spool content remains separate and unchanged for later adapter-owned
   draining.

### Crash-safe state and bounded outbox

1. Persist accepted schema-v1 model state below
   `/storage/brake-health/model-state/v1` and derived messages below
   `/storage/brake-health/v2/outbox`, with injected temporary roots in tests.
2. Enforce state at most 64 KiB, at most 64 recent source IDs, at most 64
   unacknowledged messages and at most 1 MiB canonical outbox bytes. Use mode
   `0700` directories and mode `0600` files and require same-directory
   temporary write, file synchronization, atomic rename and directory
   synchronization.
3. Apply the reviewed journal/state/commit-marker protocol. A transaction
   either makes its state and all admitted derived messages recoverable or is
   explicitly quarantined; restart cannot count one event twice.
4. When a derived pair cannot fit, apply the reviewed
   `DERIVED_OUTBOX_FULL` semantics without stopping future local assessments.
5. Expose inventory and an injected durable-ACK transition for tests. No HTTP
   parsing, retry scheduler or backend connectivity is implemented. Delete a
   local derived message only after an exact injected ACK matches its accepted
   canonical idempotency-key digest and content digest; conflict retains and
   quarantines it.
   Assessment keys are RFC-8785 arrays of
   `[unitSystemUid, "BRAKE_HEALTH_ASSESSMENT", assessmentId]`; event keys are
   `[unitSystemUid, "BRAKE_HEALTH_EVENT", eventId]`.
6. Unknown state schema, model identity/config digest mismatch, malformed
   state or generation/digest conflict is quarantined as `NOT_READY_STATE`.
   Silent reset, downgrade or arbitrary previous-version selection is
   forbidden.

### v1-to-v2 transition

1. Missing v2 state creates the disclosed preconditioned v2 state and permits
   v2 analytics immediately; it does not wait for the v1 spool.
2. Existing v1 event directories remain byte-for-byte untouched. This packet
   neither migrates them into the v2 outbox nor deletes them.
3. Later adapter composition must keep the v1 sender available to drain those
   events and delete them only after accepted D4-017 durable acknowledgements
   or R0. This packet proves only coexistence and non-gating, not transport.
4. Persist `producerEpoch` and `nextAdvisorySequence` in schema-valid v2 state
   without using them for a v2 advisory. They are preserved for the separately
   reviewed v2-to-v3 packet.

## Required Deterministic Verification

An authorized implementation must add and pass tests for:

- clean C++17 configure/build and CTest without download;
- exact eligible, insufficient, stale, malformed, reordered, terminal-state,
  speed/steering/sample-count and threshold boundary fixtures;
- the authoritative 80-sample 12-signal input fixture and exact five features, load,
  wear, score, band and output bytes;
- positive round-half-up at every half/below/above boundary and saturation at
  `0`, `10000` and wear `100`;
- deterministic UUIDv5 known-answer vectors and field-order/delimiter
  negatives;
- assessment-only and atomic assessment-plus-event paths, no-event same-band
  behavior and normal absence of all v1 messages;
- schema fixtures, exact content digests, message limit and invalid metadata;
- first-start state, restart, duplicate event, 64-entry ledger rollover,
  interrupted journal/state/marker at every write stage, corruption and
  generation/config conflict quarantine;
- outbox item/byte bounds, the one-slot pair boundary, explicit overflow,
  injected ACK match/conflict/duplicate and delete-after-ACK only;
- v1 spool presence while v2 initializes and assesses, with no v1 file
  mutation or v2 readiness gate;
- v2 state preservation fields required by the later v3 migration; and
- all existing v1, scaffold, repository-boundary and quality-gate tests.

Tests use injected UUIDs, timestamps, monotonic time, roots and fault stages.
They must not sleep, use randomness without injection, reach a network, install
packages or silently skip owned assertions.

## Explicit Exclusions

- no KUKSA/VISS/gRPC/protobuf adapter or 30 Hz subscription;
- no KAC, `AOS_SECRET`, JWT, token file or permissions implementation;
- no service main/process composition or capability/readiness endpoint;
- no HTTP backend sender, retry/backoff, SSE, Dashboard or Cloud code;
- no production backend authentication;
- no v3 advisory, Gateway Status or arbitrary KUKSA write;
- no modification or deletion of v1 spool content;
- no scaffold executable, Aos metadata, compatibility manifest or packaging
  integration;
- no ARM64/Aos artifact or container/image build;
- no D4-003 live calibration or D4-023 quota qualification;
- no dependency retrieval, package installation or contract reinterpretation;
- no signing, publication, AosCloud, VM, Unit, CARLA, FOTA or SOTA operation;
- no commit, push, merge or `main` mutation under this proposed packet.

## Stop Conditions

Stop and return for review if:

1. any frozen base, tree, file or contract digest differs;
2. any authoritative `BHS-V2-RD-*` closure or frozen digest is missing;
3. the authoritative input fixtures do not reproduce the accepted output
   arithmetic and identities;
4. implementation requires changing a v1 file or any path outside the exact
   writable boundary;
5. a new dependency, general JSON/crypto framework or network access appears
   necessary;
6. the derived pair cannot be made atomic under the accepted state/outbox
   semantics;
7. legacy v1 spool draining would require this source-core packet to own
   transport; or
8. build, owned tests, inherited v1/scaffold tests or boundary checks fail.

## Completion Evidence Required Later

An authorized worker must report the isolated branch/worktree, exact commit
and parent, changed-file list, boundary check, deterministic test commands and
results, contract fixture/digest comparison, dependency and secret-negative
scan and explicit confirmation that no excluded operation occurred.

Source completion would prove only the v2 domain core. It would not mean that
Brake Service v2 is composed, packaged, deployed, calibrated or qualified.

## Authorization Gate

`DESIGN REVIEW COMPLETE / READY FOR IMPLEMENTATION REVIEW`. This packet
authorizes no branch creation, product edit, dependency operation, build,
commit or external action. `BHS-V2-RD-01` through `BHS-V2-RD-10` are accepted
and the authoritative contract/fixture digests are refreshed; implementation
may start only after the writable boundary is reviewed and the operator grants
a separate explicit implementation authorization.
