<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Tire Health In-Vehicle Product Contract — Accepted Contract

Implementation and qualification: [protocol status](../implementation-status.md).

- Decision: `D4-018`
- Lifecycle state: `ACCEPTED`
- Contract version: `1.1.2`

## Current product messages

New assessments and events use `schemaVersion: 2`, `contractVersion: "2.0.0"`
and [native product provenance](../service-runtime-inputs/product-message-migration.md):
the immutable package release and native service/Subject/instance identity,
without `serviceArtifactSha256`. Wire revision 2 is distinct from Tire's
functional V1 and this model-contract version. The model, state, advisory and
resource obligations below remain current, not legacy-only rules.

Use the current [assessment](tire-health-assessment.v2.schema.json) and
[event](tire-health-event.v2.schema.json) schemas for new products.

## Model and runtime obligations

Current packages request 600 DMIPS through signed native metadata. Full
resource acceptance and the fixed CPU-isolation demonstration remain separate
D4-023 obligations; a quota declaration or monitoring is not enforcement proof.
The synthetic model, 250-ms input freshness, other quotas, dynamics episode,
persistent hysteresis/idempotency, advisory, offline/readiness and isolation
requirements below retain their accepted meanings.

This package defines the accepted current-demo contract for the single
Tire Health Service v1.0. It consumes only the accepted VDP v3 native dynamics
subset. CARLA's selected `HEALTHY`/`PRE_AGED` profile and friction multiplier
are qualification truth and are forbidden from the Service, KUKSA, backend and
dashboard.

Service v1.0 is compatible only with VDP v3 and consumes the exact 15-path
subset frozen in the product profile. Under the [active-capability evidence contract](../service-runtime-inputs/active-vdp-capability-amendment.md),
Presenter establishes exact VDP compatibility from Cloud/artifact evidence.
The service validates real local inputs, remains waiting/not-ready on absent
or invalid data, and recovers automatically; absence alone must not be called
proven `INCOMPATIBLE_VDP`. It emits no fabricated condition result/advisory. The
Function Team view may direct the operator to the Platform Team, but the first
demo claims no native pre-transfer AosCloud dependency rejection.

`TIRE_DYNAMICS_EXERCISE_V1` is one bounded maneuver window measured from
vehicle-signal source timestamps. A 12-second maximum closes one uninterrupted
maneuver and suppresses immediate re-segmentation only until its clear
condition; it does not limit later maneuvers or the number of episodes in a
demo run. Scenario, Autopilot and Manual driving can all produce episodes, but
control mode is not a model input. Source-generation reset aborts the current
episode and re-arms collection for the next maneuver.

The synthetic estimator uses integer basis-point arithmetic and clamps each of
its four normalized feature values to `0..10000` before applying the accepted
30/30/20/20 weights. Identical input therefore produces identical load, score
and band without implementation-dependent floating-point behavior. Every
result is labelled `DEMO_SYNTHETIC`; it is not tread depth, remaining useful
life, a production diagnosis or a safety decision.

The first eligible episode establishes state. One worse episode applies
immediately; improvement requires three consecutive eligible episodes naming
the same better band. Invalid evidence mutates neither accepted state nor the
improvement counter. Every eligible episode is assessed locally, while
same-band Cloud assessments are rate-limited to one per 30 seconds and a band
change may emit immediately. Deterministic IDs/digests, a recent-source ledger
and journal/atomic-replace/commit-marker persistence ensure one source episode
advances state at most once across retries or restart.

D4-003 performs five calibration runs per hidden simulator profile before the
model configuration is frozen and digest-pinned. Qualification then uses ten
independent fresh-state runs per profile without tuning: all ten `HEALTHY`
runs must produce `GOOD` and all ten `PRE_AGED` runs must produce
`REPLACEMENT_RECOMMENDED`. Persistence/hysteresis are qualified separately.
These runs and their report precede the presentation; they are not repeated
inside the demo. Failure blocks artifact acceptance and never permits exposing
the simulator oracle to the Service.

Accepted inspection/replacement state writes only the typed Tire Request into
KUKSA; confirmed `GOOD` after hysteresis writes `CLEAR`. A 30-second lease is
refreshed every 20 seconds. Restart with persisted non-good state re-establishes
the lease from the last accepted assessment; stop/crash fabricates no clear and
the Gateway expires an unrefreshed lease. Only correlated Gateway Status—not a
successful KUKSA write—proves application. The entire path remains local when
external connectivity is absent and is presented only on the Engineering
Telematics Dashboard, not a demo driver cluster.

The operator-authorized demo-reset exception clears the current indication
without fabricating a GOOD assessment. It resets model/capture to NOT_EVALUATED,
retains sequence, epoch, history and outbox, and requires a correlated Gateway
CLEARED acknowledgement. This is demo control, not a repair claim. The closed
[reset protocol](../qm-advisory-profile/readiness-and-reset.md)
defines current-Test scope and bounded execution.

Model state and the derived-message outbox survive ordinary Service and VM
restart and are removed only with the disposable Unit overlay at R0. The
outbox holds at most 256 derived messages or 2 MiB, never raw telemetry. At
capacity it preserves accepted records, rejects the new Cloud message with
`TIRE_OUTBOX_FULL`, and continues local estimation/advisory. External loss is
`DEGRADED`, not local `NOT_READY`; reconnect delivery is idempotent and keeps
original event time. Unknown state is quarantined without silent reset.

Ordinary process, container and VM restarts also preserve the advisory
producer epoch and continue from the persisted next sequence without reuse.
Only an explicit producer replacement or new producer lifecycle rotates the
epoch, exactly once, and starts its sequence at `1`. R0 destroys that producer
state; late old-epoch evidence can never change the current Tire state or
advisory.

The accepted resource values are requested, not yet qualified. AosCore is the
only resource authority and D4-023 remains the measurement gate. The first
demo intentionally saturates CPU only inside Tire Health: AosCore throttles the
same instance without stop/restart/redeployment, Brake Health remains the
healthy control tenant, and Tire returns to normal after load stops. No common
runtime claim is made for deliberately exhausting other quota types.

Operational output is bounded allowlisted JSON on stdout/stderr, aggregated to
at most 60 records/minute and 2048 bytes/record. Per-sample/per-message-success
logging, credentials, raw telemetry and simulator oracle data are forbidden.
The native AosCore/AosCloud D4-014 path is authoritative; no separate Service
log archive or first-demo latency benchmark is introduced. Tire crash, CPU
throttling, backend failure, outbox overflow or invalid input remains contained
from Brake Health and the vehicle platform; restart either recovers valid state
or reports explicit quarantined `NOT_READY_STATE`.

The accepted outbox additionally carries bounded `TIRE_FUNCTION_STATUS` at
Service start, functional-status change and no more than one 30-second
heartbeat. This is the Function Team's diagnostic fact for VDP compatibility,
telemetry/access/state or backend-sync condition; it is explicitly not AosCore
process/lifecycle readiness. It contains no raw telemetry or simulator oracle.

The estimator is deliberately synthetic and deterministic. It demonstrates
local computation, independent Function Team 2 lifecycle, bounded offline
state, typed advisory and tenant isolation; it is not a production tread-depth,
remaining-life, safety or diagnostic model. Exact numeric separation is a
D4-003 calibration gate: the artifact/product is not accepted until the frozen
live exercise proves the required healthy/pre-aged bands repeatedly.

Files for current products and model verification:

- [`tire-health-product-profile.v1.json`](tire-health-product-profile.v1.json)
  — input, episode, estimator, hysteresis, advisory, persistence, runtime and
  evidence rules;
- [`tire-health-assessment.v2.schema.json`](tire-health-assessment.v2.schema.json),
  [`tire-health-event.v2.schema.json`](tire-health-event.v2.schema.json) and
  [`tire-health-state.schema.json`](tire-health-state.schema.json) — closed
  logical schemas;
- [`fixtures/tire-health-assessment.v2.valid.json`](fixtures/tire-health-assessment.v2.valid.json),
  [`fixtures/tire-health-event.v2.valid.json`](fixtures/tire-health-event.v2.valid.json)
  and [`fixtures/tire-health-state.valid.json`](fixtures/tire-health-state.valid.json)
  — deterministic review fixtures.

This accepted design contract authorizes no implementation, repository
creation, artifact publication, Cloud mutation or Unit deployment by itself.

<a id="native-product-provenance--2026-09-11"></a>
## Current and legacy product provenance

Only the original wire-provenance schemas and their message fixtures are
legacy compatibility inputs: [assessment](tire-health-assessment.schema.json),
[event](tire-health-event.schema.json), [assessment fixture](fixtures/tire-health-assessment.valid.json)
and [event fixture](fixtures/tire-health-event.valid.json). Retain their original
discriminator, artifact provenance and queued bytes; do not add that digest
dependency to new v2 messages or rebind an old advisory to a new release.

The product profile, model/state schema, algorithms, VDP hashes, receipt keys,
authorization and resource obligations remain current under their own versions.
Administrative/cleanup protocols are unaffected. Scoped live evidence and the
remaining full acceptance matrix follow the protocol map above; retained
compatibility fixtures do not close calibration or resource qualification.
