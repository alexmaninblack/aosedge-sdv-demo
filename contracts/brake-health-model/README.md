<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Synthetic Model Contract

- Decision: [`D4-016.3`](../../docs/requirements/d4-decision-register.md#d4-016)
- Contract version: 1.0.0 accepted 2026-08-23
- Model: `brake-condition-demo-v1`
- Profile: `DEMO_PRECONDITIONED`
- Provenance: `DEMO_SYNTHETIC`
- Accepted profile SHA-256:
  `5d7ca7ebf257a7a34014e70d1f041a624dbd65eac038a6762bdb21d6d38f6ad6`

This accepted contract defines the deterministic on-board Brake Health Service
v2 model used by the demonstration. It proves event analysis can move from
Cloud collection into the vehicle; it is not a production brake diagnostic,
remaining-useful-life estimate or safety function.

Files:

- [model profile](brake-health-model-profile.v1.json);
- [assessment schema](brake-health-assessment.schema.json);
- [band-change event schema](brake-health-event.schema.json);
- [persistent-state schema](brake-health-state.schema.json);
- [golden assessment](fixtures/brake-health-assessment.valid.json);
- [golden band-change event](fixtures/brake-health-event.valid.json); and
- [golden post-assessment state](fixtures/brake-health-state.valid.json).

## Deterministic arithmetic

All normalized features and the combined load use integer basis points
(`0..10000`) with positive round-half-up arithmetic. The accepted golden input
produces load `6750`, wear increment `8`, wear `54 -> 62`, condition score
`46 -> 38` and the transition `MONITOR -> INSPECTION_RECOMMENDED`.

The preconditioned wear value is visibly disclosed model configuration. It is
not obtained from hidden CARLA scenario state. D4-003 qualification must prove
that the frozen live braking scenario reaches the accepted minimum load on
every required repeat before the presentation claim is accepted.

## Exactly-once local state

The Service first writes a synchronized immutable transaction containing the
before/after generations and derived messages. It then atomically replaces
the state file and marks the transaction committed. Recovery completes either
the unapplied transaction or its commit marker; any generation/digest conflict
is quarantined and yields `NOT_READY_STATE`. A bounded recent-event ledger
prevents one source event from advancing wear twice.

Normal v2 operation emits no v1 telemetry-window chunks. Local transport and
durable backend acknowledgement remain D4-017; production backend
authentication is Function Team 1-owned and outside the first-demo scope.
