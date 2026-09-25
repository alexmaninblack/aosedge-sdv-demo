<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Bounded service function observation

Current implementation status (24 September 2026, demo-v1.1 / Factory .39):
see the [complete protocol map](../implementation-status.md) for this family's
implemented path, accepted amendments and remaining qualification or executable-
profile differences. Design lifecycle labels below are not deployment verdicts.
Historical golden schemas/digests are not rewritten as part of this audit.

Accepted semantics: decisions 1A and 2A, 18 September 2026. The
[v3 executable contract](v3-contract.md), closed schema, producers, backend
consumers and Presenter selectors are implemented and have scoped live
evidence. Remaining acceptance and freshness observations are recorded in the
[work packet](../../docs/planning/active/work-packets/versioned-service-observability.md).

## Authority and axes

Brake supplies bounded function/episode facts to its own backend; Tire
completes its existing status mechanism. Presenter reads the corresponding
backend, never a guest file or SSH probe. Native Aos Cloud owns installed
software, instances and resources. Native vehicle telemetry owns the current
in-vehicle advisory. A reset poll or receipt is not proof of telemetry input.

Keep these independent facts:

- Compatibility: required versus observed VDP profile/capabilities with an
  explicit evidence source. Presenter installed-profile evidence comes from
  native Cloud plus exact artifact metadata; service-local capability/input
  observations remain independent. Neither implies the other is current.
  The subsequent P2 option-A clarification assigns exact version/profile
  comparison to Cloud/package evidence in Presenter; services do not need a
  new local profile transport and must not infer incompatibility from absent
  samples. Legacy Tire `requiredVdpContractVersion: 3.0.0` is not comparable
  with the common family-document revision `1.0.1`; retain its historical
  decoder without carrying that ambiguity into the new observation revision.
  Distinguish unavailable evidence from a proved incompatible profile. The
  accepted [Cloud-first correction](../service-runtime-inputs/active-vdp-capability-amendment.md)
  introduces no guest timer or dependency of local operation on Cloud.
- Input: receiving current valid input, waiting, stale, disconnected, access
  denied or invalid; do not silently turn a rejected sample into zero.
- Activity: waiting for a qualifying episode, capturing, completed or skipped
  with a bounded reason. A skipped episode is not necessarily function failure.
- Product: latest valid assessment/window with original source and release
  provenance, or no result. Heartbeats are never substitute assessments.
- Delivery: last confirmed backend receipt and service-reported queue state,
  when available. External Cloud status is not a backend reachability probe.
- Advisory: request/application facts distinct from analytics and readiness;
  a retained V2 condition can activate a V3 advisory without a new assessment.

Routine credential renewal must remain distinguishable from lost source data.
Mandatory token replacement/reconnection and fail-closed expiry are unchanged.
An uncorrelated cached advisory ACK is not a current success and is not, by
itself, evidence of failed analytics. These distinctions must be frozen in
the bounded observation schema before the changed service producers ship.

No continuous raw-telemetry stream, new inbound guest listener, arbitrary
command or dependency of local analytics on backend connectivity is introduced.

## Boundedness and migration

Emit state-change observations and a bounded periodic freshness observation.
Specify maximum message size, rate, retained status history and offline
behavior before implementing the new wire revision. Reuse service delivery
workers; never block KUKSA consumption on HTTP. Late historical status cannot
replace newer function state merely because its receipt is later.

Use exact native Unit/service/Subject/instance and package-profile/release
provenance. If a separate status epoch/sequence is needed, define its lifecycle
explicitly rather than borrowing or advancing advisory-command sequence numbers.
Keep existing product receipt, canonical hash and exact-retry semantics.

Retain explicit Tire legacy status decoding and all stored records. New fields
must use a new wire discriminator, not loosen a closed legacy schema. Deploy
backend consumers before changed services and make Presenter distinguish
unreported status from reported unavailable state.

## Current result, reset and updates

One shared selector serves overview, dialog and chapter proof. Match the
current binding; separate source ordering, receipt history and current-release
acceptance. Old instances and offline-delayed records remain history.
Never infer a model reset from a package update or reset-command issue time.
Pending, failed, expired and confirmed-applied reset outcomes remain distinct;
partially applied/uncertain resets cannot be called successful or ignored.

Brake V1 displays bounded window acquisition and completion, not a model
score. V2 displays analytics without advisory. V3 preserves V2 model state
and adds separately confirmed advisory. Tire V1 already supports analytics
and advisory. Same-profile repairs preserve model and queue state.

Backend timestamps describe the last known observation during network loss;
they cannot establish current native advisory. Model thresholds and existing
local freshness/advisory/authentication policies are unchanged.
