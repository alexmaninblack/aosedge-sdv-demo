<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Running service-chain audit — 18 September 2026

## Scope and evidence limits

The operator requested the complete picture before further fixes. This audit
is read-only: no process restart, drive/reset command, source correction,
publication, provisioning or model-threshold change was performed. Autopilot
and the existing staging Test were preserved. This document records findings;
it is not an implementation approval or an end-to-end pass.

Current releases: Factory `.35`, VDP functional V3 `79.0.0`, Brake functional
V3 `59.0.0`, Tire functional V1 `34.0.0`. Cloud:
`aws-stage.epmp-aos.projects.epam.com`. The VDP 79 update and duplicate-frame
fix preceded this audit; see [the preceding diagnosis](brake-driving-gap-2026-09-18.md).

Evidence combines local implementation/contracts, bounded guest journals from
07:15:08 UTC, sampled Gateway events through 07:31:17, backend observations at
approximately 07:33:41, and two bounded independent CARLA read-only probes.
Different observation windows must not be treated as one synchronized trace.
No raw telemetry, credentials or tokens are retained here. Journal counts are
bounded observations, not lifetime totals or statistically representative rates.

## Three distinct paths

1. **Product input and results:** CARLA → Gateway/VISS → VDP provider → KUKSA
   → Brake/Tire model → durable service outbox → corresponding backend →
   Presenter backend cards/dialogs.
2. **In-vehicle advisory:** service → KUKSA actuator/readiness → VDP advisory
   transport → Gateway validation/application → native telemetry dashboard.
   Gateway acknowledgements return through VDP/KUKSA to the service. Backend
   advisory facts are a separate record of that interaction.
3. **Management:** Aos Cloud → package delivery/service assignment; Cloud
   inventory and unit state → Presenter. Cloud Online/installed does not prove
   model input readiness or an applied in-vehicle advisory.

The Presenter must not replace backend evidence with guest reads. The native
dashboard must not infer advisory availability from Cloud package versions.

## Findings by boundary

| Boundary | Observed evidence | Conclusion and limitation |
| --- | --- | --- |
| CARLA → Gateway | Among 647 sampled Gateway events after activation, 642 contain 41 points and five contain 40. | Some snapshots are incomplete before VDP. Event sampling does not identify the missing path or total loss rate. |
| CARLA sampling | Gateway combines a world snapshot with separate telemetry, left-wheel and right-wheel RPCs. A 45-second independent probe observed 20 frame advances during 222 reads and one opposite-sign steering pair. A second 60-second probe observed one opposite-sign pair among 582 reads; it crossed observed frames and both magnitudes were below 0.01 degrees. | Source sampling is not atomic. Steering rejection is a reproduced candidate mechanism, but these independent reads are not a timestamp-correlated capture of a failing Gateway frame. |
| Gateway normalization | Opposite-sign front-wheel angles cause `EquivalentFrontAxleAngleDegrees` to return no value. VSS then omits front-axle steering angle. | Code confirms a route from contradictory steering reads to one missing VSS point. It does not yet prove that this explains every observed 40-point frame. |
| VISS → VDP 79 | One connection establishment; no non-monotonic, stale-timeout or reconnect warning in the bounded post-update journal. Repeated READY transitions remain. | The previous duplicate-frame reconnect defect is no longer observed. Remaining interruptions have a different path. |
| VDP → KUKSA | In complete-frame mode, any incomplete selected frame publishes unavailable values for all 23 selected paths. Missing paths do not get a dedicated named-path log. | A single missing input can invalidate the entire selected data set. This is existing fail-closed behavior, not proof that all physical inputs failed. |
| KUKSA/access layer | Databroker and auth-compat service active, successful result, zero restarts. No permission-denied, unauthenticated, expired, panic or resource-exhaustion marker in their bounded journals. Both deployed services process real episodes. | No evidence of a general permissions, token or broker outage in this window. Absence of log markers alone is not a complete authorization proof. |
| KUKSA → Brake | Missing-value summaries report mask 4095: all twelve required values unavailable together. The bounded post-update sample contains 87 NOT_READY entries and 42 aggregate records reporting 80 rejected inputs. No watchdog expiry was observed. | Brake sees explicit missing values, not merely old values. Its 5000 ms freshness allowance does not override explicit invalidation. Different counters have different scopes and are not expected to be equal. |
| Brake model | Four captures completed, each skipped with `INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`; zero `ASSESSMENT_CREATED`. | No new Brake assessment existed to deliver in this window. The skip reason does not by itself identify which individual speed/steering/sample-count condition failed. |
| Tire model | 21 completed exercises in the bounded post-update journal and fresh release 34 backend assessments. | Tire's product path works. This does not establish uninterrupted input or close every advisory edge case. |
| Service → backend | Tire records at 07:31:48, 07:32:25 and 07:33:37 were durably accepted. Brake backend still has retained release 58 assessments, not a release 59 result. Current backend control contact exists for both. | There is no evidence of a common delivery outage. Brake's missing current result agrees with its local model outcome. Control contact is not telemetry readiness. |
| Durable queues | A later read-only process-root inspection found zero entries, including directories, in Brake `v2/outbox` and `v3/outbox`; Tire `outbox/v1` contained zero files. | No queued Brake assessment/advisory or Tire message was waiting at those inspection instants. Empty queues do not alone prove delivery; they are consistent with the model logs and backend evidence above. |
| Service → advisory | Brake readiness changes with input validity. Service readiness and VDP availability are each published on periodic intervals; native availability expires separately. | A short input failure can be visible longer in the native availability label. Exact phase/cause of each visible transition has not been jointly captured. |
| Presenter | Backend observations are polled after a 5-second interval when visible. Current result selection is scoped to Cloud-observed release and source-event time after reset. | Old release 58 results are correctly excluded from the current release 59 result. Presenter has no Brake backend message explaining skipped captures or current input readiness. |

## Why Brake and Tire behave differently

Brake explicitly reacts to invalid required values by marking analytics not
ready and aborting an active capture. Tire skips incomplete frames and can
continue an episode if a valid frame returns within its 250 ms gap allowance.
Its 250 ms source-age contract also differs from Brake's approved 5000 ms
profile. Neither service interpolates missing measurements.

Brake triggers on speed at least 10 km/h with brake effort at least 50% held
for 200 ms. Its derived assessment requires at least five active samples and
at least five qualified active samples with speed at least 10 km/h, absolute
steering no greater than five degrees, and permitted source age. A natural
Autopilot stop does not guarantee these conditions. Four completed captures
after VDP 79 were rejected on the qualified-sample count; this is separate
from the missing-input defect.

Tire's maneuver qualification is different: turns while moving can naturally
produce eligible exercises. Its success therefore cannot establish that a
Brake capture should also succeed.

Brake V2/V3 sends derived assessments/events/advisory facts, not a continuous
raw driving telemetry stream. Under the current contract, a skipped assessment
is logged locally but does not become a backend product assessment. Consequently
"the car is driving" and "no new Brake backend result" can both be true.

## Advisory and UI meaning gaps

- Brake's diagnostic `DEGRADED / VISS_OR_GATEWAY_UNAVAILABLE` also occurs when
  no current-session request/acknowledgement has yet proved the advisory
  round trip. It must not be read as confirmed Gateway disconnection.
- Native `Monitoring` follows fresh service availability received through
  telemetry. An applied warning follows its own validity and expiry. Neither
  is the same as the latest backend condition assessment.
- Service readiness publication is periodic (5 seconds), VDP availability
  publication is periodic (5 seconds), and readiness expiry is 15 seconds.
  These independent clocks can prolong a sampled transient; this is a
  source-based mechanism, not a measured latency bound for every transition.
- Tire logged two `GATEWAY_STATUS_INVALID` occurrences while continuing to
  generate results. The catch-all includes uncorrelated request/status,
  validation and persistence errors. Existing logs cannot distinguish them;
  stale acknowledgement is a hypothesis, not a confirmed cause.
- Readiness writes do not expose their Set result sufficiently for this audit
  to attribute an individual failed native update. This is an observability
  gap, not evidence that a write failed.
- Presenter now distinguishes "Waiting for braking result", "No new result
  after reset" and recent service contact. It still cannot distinguish
  receiving valid inputs, waiting for a qualifying maneuver, and a rejected
  maneuver using the current Brake backend contract. UI wording alone cannot
  supply missing service evidence.

## Confirmed versus still open

**Confirmed:** occasional upstream snapshot incompleteness; VDP's whole-set
invalidation policy; explicit missing inputs at Brake; completed but ineligible
Brake captures; functioning Tire result delivery; multiple different readiness
meanings that are not exposed coherently to the operator.

**Strong candidate, not yet fully correlated:** separate CARLA steering RPCs
straddle a simulation frame near straight-ahead, normalization rejects the
opposite-sign pair, steering disappears, and VDP clears the complete set.
Other missing-path/invalid-frame causes have not been excluded.

**Not demonstrated:** a general Cloud delivery failure, lack of permissions,
dead service process, broker restart, or a lost release 59 Brake assessment
that was successfully created but never reached the backend.

## Proposed investigation/fix order — not executed by this audit

1. Close the missing-path attribution with bounded structural diagnostics:
   source frame identity, required-path presence/invalid mask and transition
   timestamp, not telemetry values. Correlate Gateway, VDP and service events.
2. Prove the smallest correction at the confirmed source boundary. Do not
   substitute steering values, silently retain stale data, loosen model
   thresholds or weaken VDP completeness merely to hide the symptom.
3. Recheck continuous input on the same running scene, then run an explicitly
   controlled qualifying Brake maneuver and trace one assessment through
   durable outbox, backend receipt and Presenter. Do not call ordinary
   Autopilot an assessment acceptance test.
4. Trace readiness and a warning request/acknowledgement separately. Classify
   the Tire catch-all and distinguish advisory not-yet-proven from transport
   failed before altering availability semantics.
5. Agree a minimal backend-visible Brake function/episode status if needed,
   reusing the accepted delivery pattern. Only then make Presenter display
   receiving input, awaiting maneuver, skipped reason, result and advisory as
   distinct states. No guest-read shortcut or new interface is assumed here.

## Implementation references

- Gateway: `carla-ego-runtime/src/runtime_carla.cpp` (`CollectSample`),
  `src/vehicle_state.cpp` (`EquivalentFrontAxleAngleDegrees`), `src/vss.cpp`.
- CARLA: `LibCarla/source/carla/client/Vehicle.cpp` and
  `client/detail/Client.cpp`: telemetry and wheel-angle reads use distinct
  synchronous RPCs.
- VDP: `providers/carla-viss-kuksa/src/carla_viss_kuksa_provider/bridge.py`,
  `runtime.py`, `readiness.py`, `advisory_transport.py` in `aos-vehicle-platform`.
- Brake: `src/runtime/grpc_main.cpp`, `product.cpp`, `model_capture.cpp`,
  `src/v2/model.cpp` in `brake-health-service`.
- Tire: `src/runtime/grpc_main.cpp`, `protocol.cpp`, `src/runtime.cpp`,
  `src/model.cpp` in `tire-health-service`.
- Presenter: `apps/presenter-ui/src/features/service-team/useBackendObservation.ts`,
  `backendProduct.ts`, `BackendEvidence.tsx`.
- Accepted inputs: `contracts/brake-health-model`,
  `contracts/brake-health-runtime`, `contracts/tire-health-model`,
  `contracts/viss-trust-telemetry-profile`, and
  `docs/planning/active/work-packets/advisory-readiness-and-demo-reset.md`.
