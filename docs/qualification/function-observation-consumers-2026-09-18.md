<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P3 function-observation consumers and Brake window detail

Date: 18 September 2026. Status: source and isolated-host verification.
Not deployed; not P7/P8 or a complete service-recovery claim.

## Implemented boundary

The new closed v3 function-observation contract separates connection, current
input, episode activity, delivery, advisory and a provenance-preserving last
result reference. Existing Tire status and Brake/Tire product messages are
unchanged. Services do not infer the active VDP profile from missing samples.

Both backend consumers implement strict ingestion, exact durable retry,
visible conflict, source generation/sequence ordering and one head per native
binding. Backend receive time cannot renew source freshness or choose the
current Cloud instance. Full observation payload retention is bounded at 1024
per binding; compact receipt/conflict identities remain until exact run cleanup.

Brake's accepted window-detail point read returns its existing summary and
up to 150 stored points in chunk/sample order. It preserves gaps, phases,
source times and provenance; no interpolation or model score is introduced.
Hidden pre-start chunks remain hidden. Corrupt stored content is a storage
error, never silently incomplete success.

Brake database migration 005 and Tire database migration 004 are additive.
Old canonical records, receipts, reset commands and model-product histories
are preserved. Both private cleanup/count/digest paths include the two new
tables. Demo Control recognizes the exact new proof shapes while retaining
old supported shapes during rollout. Unknown schemas and incomplete counts
still prevent whole-volume removal.

## Executed checks

- Shared reference decoder/store: 30 tests.
- Brake backend: TypeScript compile, 58 Node tests and 12 existing Vitest tests.
- Tire backend: 20 Node tests.
- Demo Control backend lifecycle/context/retirement: 75 Python tests.
- Packaged reference source copies are byte-identical in both backend repos.
- HTTP tests use service-like Node HTTP requests. An initial test used fetch,
  whose browser-style fetch metadata correctly triggered the existing guard;
  only the test client was corrected, not the network boundary.
- Exact cleanup client operations are preview/execute, not URL-tail names.
  The initial harness mismatch was corrected before claiming cleanup success.

New checks cover previous-schema migration and rollback, old bytes/receipts,
current-Unit and role scope, browser rejection, late older generations,
duplicates, conflicts, process reopen, source-stale/future reports, retention,
Test-only cleanup with peer preservation, zero-count proof completeness,
window completion-first/out-of-order/gap/legacy/native/150-point reads.

No additional JSON Schema engine was installed; the executable reference
validator and its negative tests were run. The JSON Schema remains the
published structural definition; digest, canonical-byte bound and semantic
checks are also enforced in the executable validator.

## Deployment and remaining gates

### First P4 source corrections

Tire's valid superseded/unrelated Gateway ACK is now ignored only after
strict own-endpoint envelope validation. It cannot mutate the model, input
readiness, current request or queued bytes. Malformed messages remain rejected
with an advisory-specific diagnostic. The old exception was reproduced before
the fix; the corrected regression and all four Tire CTest groups passed.

Brake and Tire classify token-only replacement separately from public-input
change, removal, unsafe token ownership/mode and RPC authentication refusal.
Reauthentication still cancels the old RPC, aborts interrupted acquisition and
creates a fresh authenticated subscription. Only this classified path skips
the former unconditional one-second error delay. Failure remains sticky within
a session; late file restoration cannot relabel a failed session as renewal.
Brake's advisory session retains its fresh request/reply requirement; a cached
ACK does not become a new confirmation.

Both actual ARM64 gRPC product executables and bootstraps compiled against
pinned gRPC 1.60.1, Protobuf 25.8.0 and KUKSA 0.5.0 schemas. All seven Brake and
four Tire CTest groups passed in isolated network-disabled containers, in
addition to their host tests and ten Python source guards.

An isolated TLS/VAL fixture ran four cases for each telemetry subscription:
token replacement and reconnect with the replacement, token deletion,
simultaneous CA/token change, and a new credential rejected by the RPC server.
All eight cases passed. The probe uses synthetic tokens and a temporary local
certificate, not IAM issuance or KUKSA's JWT verifier; it is not the live
180-second renewal/offline gate. Brake's separate advisory loop was compiled
but is not covered by this telemetry-only fixture.

Probe sources/builds are retained in
`/private/tmp/aos-service-p4.MutJS1`. Initial probe-only issues (generated
protobuf setter spelling and an absent default OpenSSL config in the pinned
dependency image) were corrected without changing product behavior. The
dependency stage was reused from the normal recipe cache; code compilation
and TLS probes ran with networking disabled and source read-only. No package
was exported to the catalog or published.

Initial-input handling is now implemented in both bootstraps. Native package/
instance identity and the existing secret boundary are validated first.
Missing initial public metadata or trust makes the existing process wait with
a single fixed diagnostic; valid arrival starts the real child without another
Deploy. Empty/oversized/non-regular/symlink inputs and malformed metadata are
errors, not permissive defaults. TLS/KAC still authenticate normally.

The subsequent incremental ARM64 rebuild and all eleven CTest groups passed.
Five isolated real-bootstrap process tests per service passed: wait for both
inputs and automatic child startup, missing native identity, invalid metadata,
empty trust, and clean termination while waiting. The test's child has no KAC
and obtains no token; startup is not confused with authorization success.
These ten process tests are not a live early-SOTA/FOTA acceptance.

The live backend containers, databases, Test VM, Cloud identity, CARLA,
Driving Control and current packages were not changed. No signing/upload,
Factory build, model Reset, Finish or production operation occurred.

The P4 source increment below now implements producers. Activate the compatible
cleanup adapter and backend consumers before publishing those producers. New
Presenter data reads and shared current-result/reset selectors remain P6.

Reset outcome review found that a legacy REJECTED result after package-binding
change can follow local model application; FAILED/EXPIRED also do not prove
that nothing was applied. Do not classify these legacy outcomes as
failed-before-application or use command issue time as a model boundary.
Only correlated successful CLEAR plus the exact binding establishes completion.
Explicit application-stage evidence, conservative uncertain-state handling
and cross-version/reset tests remain open for P3/P4/P6 reconciliation.

### P4 producer, reset persistence and Brake V1 cadence follow-up

Both C++ products now emit the closed v3 observation through their existing
delivery worker and fixed Mac-hosted team endpoint. There is no extra thread,
destination or credential. The observations use a separate 64-record allocation
in native storage, independent of product outboxes, models and advisory epochs.
Generation reservation, directory lock, owner/mode checks, bounded reads,
atomic fsync/rename, poison-on-uncertain-write and exact attempted-message
preservation are implemented. Overflow coalesces only unsent observations.
Native instance replacement inside the same Unit/service/Subject/index storage
allocation preserves old queued provenance and monotonically reserves another
generation; foreign allocation reuse is rejected.

Snapshots separate real validated input, capture phase/outcome, product receipt,
advisory request/ACK and actual last-result provenance. Delivery failure does
not become input failure; an observation receipt does not confirm product
delivery. Invalid/renewal/source-gap evidence remains separate. A telemetry
subscription alone does not establish RECEIVING. No active VDP profile is
invented. An emitter/storage failure disables reporting, not local analytics.

Tire's pending-Reset SOTA regression initially reproduced NOT_READY_STATE: the
runtime persisted REJECTED but its validator accepted only CLEARED/FAILED.
The validator now accepts REJECTED only with null clear request/Gateway state
and its original exact binding. Restart and duplicate-old-command tests pass;
old queued bytes are unchanged. This does not mean a rejected Reset applied
nothing locally, and does not close the conservative Presenter outcome gate.

Brake V1 now retains the first valid real frame per 100-ms source-time bucket,
instead of every third ingress frame. Tests first reproduced the 20-Hz defect,
then proved 100 retained samples in ten seconds at both 20 and 30 Hz, no filled
gaps and unchanged source timestamps. The explicit source-time amendment
supersedes only the historical cadence selection; old wire/golden records,
trigger/clear thresholds, window caps and durability rules remain unchanged.
Delivery fixtures now assert the resulting exact PRE/ACTIVE sample counts.

Latest checks: eight Brake and five Tire CTest groups pass with actual ARM64
gRPC executables. Shared producer persistence tests cover generation/restart,
minimum/unchanged cadence, exact receipts/retry, overflow, SOTA/foreign scope,
locking, symlinks/corruption and injected write/rename/directory-fsync failures.
C++ envelopes for Brake V1/V2/V3 and Tire V1 pass the TypeScript reference
decoder/store's canonical bytes, receipt and source-order checks. The 30
reference tests and eight window-contract Python tests pass.

The updated TLS telemetry probes again pass all eight cases. An added Brake
advisory-stream closure fixture reproduced a stale observation on normal RPC
termination; the fixed loop marks advisory UNAVAILABLE without changing input.
That ninth TLS case now passes. This is not live IAM/KUKSA renewal proof. A
probe invocation initially missed its container-local Server hostname mapping;
the command was corrected, with no product/network-policy change.

Still unexecuted: backend activation, service package publication, real early
install/FOTA/180-second renewal/offline and Reset qualification, P5/P6 completion,
preserved-Test P7 and Factory/clean UI P8. All running demo state is preserved.
