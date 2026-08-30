<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Synthetic Model Contract

- Decision: [`D4-016.3`](../../docs/requirements/d4-decision-register.md#d4-016)
- Contract version: 1.0.0 accepted 2026-08-23; byte/arithmetic closure
  accepted 2026-08-29
- Model: `brake-condition-demo-v1`
- Profile: `DEMO_PRECONDITIONED`
- Provenance: `DEMO_SYNTHETIC`
- Accepted profile SHA-256:
  `7749dff2dd340f05ae5f3c90912d65007ad48c52a5136ab0e165a83109d55f53`

This accepted contract defines the deterministic on-board Brake Health Service
v2 model used by the demonstration. It proves event analysis can move from
Cloud collection into the vehicle; it is not a production brake diagnostic,
remaining-useful-life estimate or safety function.

Files:

- [model profile](brake-health-model-profile.v1.json);
- [completed-episode input schema](brake-health-model-input.schema.json);
- [assessment schema](brake-health-assessment.schema.json);
- [band-change event schema](brake-health-event.schema.json);
- [persistent-state schema](brake-health-state.schema.json);
- [complete golden model input](fixtures/brake-health-model-input.valid.json);
- [closed invalid-input cases](fixtures/brake-health-model-input-quality-cases.v1.json);
- [closed conversion/quantization cases](fixtures/brake-health-model-quantization-cases.v1.json);
- [golden assessment](fixtures/brake-health-assessment.valid.json);
- [golden band-change event](fixtures/brake-health-event.valid.json); and
- [golden post-assessment state](fixtures/brake-health-state.valid.json).

## Complete input and one-time conversion

The complete golden episode contains exactly 80 retained samples at 10 Hz:
30 PRE, 30 ACTIVE and 20 POST. Every sample has the exact twelve accepted VDP
v2/v3 model paths. The ACTIVE samples have a three-second logical duration and
a first-to-last source-timestamp span of 2.9 seconds. The full retained episode
runs from `2026-08-22T12:00:00.000Z` through
`2026-08-22T12:00:07.900Z`.

The adapter performs the normative source-unit conversion exactly once before
quantization. It rejects non-finite input, normalizes negative zero to zero,
scales into the accepted milli-unit, rounds an exact half away from zero and
rejects the accepted VDP path range or target-integer overflow. The core
receives only milli-km/h, milli-m/s², milli-percent, milli-degree,
milli-km/h wheel-linear and milli-degree/s wheel-angular values and never
quantizes them again. The conversion fixture freezes below-half, exact-half
and above-half values for every unit, negative-capable quantities, negative
zero, non-finite values, path range and integer overflow.

## Deterministic arithmetic

All normalized features and the combined load use integer basis points
(`0..10000`). Positive division rounds half up and every normalized feature is
clamped before the 30/20/15/15/20 weighted load.

1. Peak deceleration is `max(0, -minimum longitudinal acceleration)` over
   ACTIVE samples and is normalized by 8 m/s².
2. Duration is `ACTIVE sample count / 10 Hz` and is normalized by five
   seconds.
3. Speed reduction is
   `max(0, first ACTIVE speed - last ACTIVE speed)` and is normalized by
   40 km/h.
4. Brake effort is the positive-round-half-up mean of ACTIVE brake-pedal
   milli-percent. The amount above 50 percent is normalized over the remaining
   50-percent span.
5. Wheel dispersion is the maximum across qualified near-straight ACTIVE
   samples of the four-wheel linear ratio and absolute-angular ratio. Each is
   `(max-min)/max(max, accepted denominator)`, with 5 km/h and 30 degrees/s
   denominators respectively, and the episode maximum is normalized by 0.15.

The golden input produces raw features `6.4`, `3`, `32`, `75`, `0.09`,
normalized features `8000/6000/8000/5000/6000`, load `6750`, wear increment
`8`, wear `54 -> 62`, score `46 -> 38` and
`MONITOR -> INSPECTION_RECOMMENDED`.

The 5000-load value is only a D4-003 scripted-demo qualification threshold. It
is never runtime eligibility. Every otherwise eligible lower-load episode
produces its assessment and advances deterministic state, with an event only
on an actual band crossing. A below-5000 scripted run is a calibration
failure; output may not be suppressed, changed or fabricated.

The controlled demo acceptance budget is at most seven seconds nominal and at
most eight seconds in all 20 of 20 scripted runs. This is not a production,
network, reliability, real-time or safety KPI.

## Invalid-input outcome

Rejected input produces only local, non-wire, non-persistent
`ASSESSMENT_SKIPPED_INPUT_QUALITY` with exactly one ordered reason:
`EPISODE_NOT_COMPLETE`, `MISSING_REQUIRED_SIGNAL`, `STALE_SAMPLE`,
`NON_FINITE_VALUE`, `OUT_OF_RANGE_VALUE`, `NON_MONOTONIC_SOURCE_TIME`,
`INSUFFICIENT_ACTIVE_SAMPLES` or
`INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`. It emits no assessment/event and
mutates no state, generation, band or recent-source-event ledger. Later
structured-log and readiness projection belongs to the adapter/runtime.

## Message identity, provenance and time

UUIDv5 names encode each ordered field as its exact UTF-8 bytes, reject CR,
LF or NUL in any field, join fields with one LF byte and append no trailing
LF. UUIDv5 is deterministic identification only; it is not authentication,
integrity protection, signing or a credential.

`modelArtifactSha256` is the immutable deployed Brake Health Service artifact
digest containing the compiled model. `modelConfigSha256` is the exact
accepted model-profile file SHA-256 above. Both are distinct injected immutable
deployment metadata; the core does not discover or hash its installation and
no fake separate model file is introduced. A future separately packaged model
requires a versioned contract change.

The source window spans the full retained PRE/ACTIVE/POST episode. Its start
and end are the first and last retained source timestamps. Model features use
ACTIVE only, with wheel dispersion further restricted to qualified
near-straight ACTIVE samples. `assessedAt` is one injected local processing
timestamp not earlier than the window end. Retry and recovery reuse the
committed value. A band event's `effectiveAt` equals the source-window end,
never processing, persistence, transport or backend time.

## Exactly-once local state and derived admission

One assessment plus its optional band-change event is an atomic admission.
Both are published or neither is. If the pair would exceed the 64-message or
1 MiB outbox limit, state and recent-event ledger still advance exactly once,
neither message is enqueued, `DERIVED_OUTBOX_FULL` is returned/logged, no later
message is fabricated for that source event and future local operation
continues.

Each assessment uses one immutable transaction journal holding canonical
before/after state, assessment, optional event and a digest-binding manifest
with disposition `ADMIT` or `OVERFLOW_NOT_ENQUEUED`. The journal is
synchronized; state is atomically replaced and synchronized; an admitted pair
is written as one same-filesystem staged bundle directory, synchronized and
atomically renamed into the outbox; then the commit marker is atomically
created and synchronized. Recovery proceeds only when current state exactly
matches journal `before` or `after`. Every other state/generation/digest
combination is quarantined as `NOT_READY_STATE`; there is no double wear,
duplicate event or silent reset. A journal is removed only after its admitted
bundle or overflow disposition is verified.

Normal v2 emits no v1 telemetry-window chunks. Local transport and durable
backend acknowledgement remain D4-017; production backend authentication is
Function Team 1-owned and outside the first-demo scope.

This accepted contract authorizes no product implementation, artifact build,
publication, Cloud/VM/Unit operation, push or merge by itself.
