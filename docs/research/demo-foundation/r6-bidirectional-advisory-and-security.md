<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6 — Bidirectional Advisory Path and Security

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream determines how Brake Health Service v3 can request a bounded
inspection advisory through KUKSA and the Vehicle Gateway without exposing
vehicle-motion controls or turning the provider into an unrestricted tunnel.
It also identifies the compatibility consequence of the KUKSA version pinned
in the current AosVM.

## Evidence summary

| Finding | Classification |
| --- | --- |
| The accepted provider is inbound only: VISS actual values are validated and published into KUKSA. | **PROVEN** |
| The current Gateway VISS profile parses `set` but rejects every update with `400 invalid_data`; it also rejects any request carrying `authorization`. | **PROVEN** |
| COVESA VISS 3.1 permits Update only for actuator nodes and states that a successful Set response does not prove that physical actuation completed. | **PROVEN** |
| KUKSA 0.5.0 distinguishes data providers from actuation providers. An actuation provider subscribes to the desired value and tries to apply it to the vehicle. | **PROVEN** |
| The pinned `kuksa.val.v1` API uses the stored, subscribable `target_value` perspective. KUKSA already marks this perspective deprecated in favor of the non-stored v2 actuation perspective. | **PROVEN** |
| KUKSA JWT authorization supports separate path-scoped `read`, `actuate`, `provide`, and `create` permissions, RS256 verification, expiry, and audience `kuksa.val`. | **PROVEN** |
| The ADR 0010 thin Aos–KUKSA Credential Broker, protected signing integration and provider platform-identity binding are not implemented in this baseline; existing tokens are qualification fixtures. | **PROVEN** |
| A safe prototype can use a narrowly scoped v1 target channel while preserving a migration requirement to `kuksa.val.v2`. | **PROPOSED** |

## Current boundary

The present runtime is intentionally read-only:

```text
CARLA state
  -> carla-ego-runtime signal store
  -> TLS VISS 3.1 Get/Subscribe
  -> inbound provider
  -> KUKSA current values
```

`carla-ego-runtime` documents VISS as a telemetry boundary and keeps vehicle
control on a separate authenticated local channel. Its protocol tests prove
that Set on `Vehicle.Speed` is rejected, and its profile states that no client
authorization scheme is implemented. Therefore Architecture 1.0's return path
is a real target delta, not a hidden capability already present in the
baseline.

## Recommended prototype flow

```text
Brake Health Service v3
  -> set KUKSA v1 actuator_target on one allowlisted advisory path
  -> outbound actuation provider subscribes to that target
  -> validate path, enum, freshness, order and rate
  -> authorized TLS VISS Set
  -> Gateway advisory handler validates again and records factual result
  -> Gateway publishes actual advisory/status over VISS
  -> inbound provider publishes those actual values into KUKSA
  -> Engineering Dashboard observes the Gateway VISS result independently
```

The double validation is intentional. KUKSA authorization constrains which
application can request the value; the outbound provider and Gateway still
enforce the automotive actuation policy at their respective trust boundaries.

## Provisional signal contract

The lower-level VSS overlay should retain the Architecture 1.0 semantics while
adding enough correlation to reject stale or repeated work:

| Entry | VSS role | Bounded values or meaning |
| --- | --- | --- |
| `Vehicle.OEM.BrakeHealth.Advisory.Request` | actuator | `NONE`, `INSPECTION_RECOMMENDED`, `SERVICE_REQUIRED` |
| `Vehicle.OEM.BrakeHealth.Advisory.GatewayStatus` | sensor | `NOT_RECEIVED`, `RECEIVED`, `REJECTED`, `FAILED` |

The detailed contract must define how a request is correlated across the
KUKSA datapoint timestamp, VISS `requestId`, and Gateway result. A bounded
monotonic sequence entry may be added if timestamp plus transport request ID
cannot provide unambiguous restart behavior. Arbitrary display text, script
payloads, URLs, or generalized path/value forwarding are prohibited.

Gateway status is factual transport/application evidence. `RECEIVED` means the
Gateway accepted the request into its advisory handler; it does not mean an HMI
displayed it or a driver acknowledged it.

## KUKSA v1 compatibility decision

For the current AosVM, the least disruptive prototype is:

1. Service v3 writes `actuator_target` through `kuksa.val.v1`.
2. The outbound provider subscribes to that same target-value perspective.
3. The provider consumes only a fresh change and records the last processed
   target metadata so a reconnect does not repeat stale work silently.
4. Actual Gateway status returns through the ordinary current-value provider
   path.

This is a compatibility bridge, not the long-term API choice. The contract
must state that a future platform version migrates both producer and consumer
of the desired value together to `kuksa.val.v2` actuation semantics. Mixing a
v1 target writer with a v2 actuation subscriber does not work because KUKSA
treats those as separate channels.

## Least-privilege model

| Principal | Minimum logical rights |
| --- | --- |
| Inbound provider | `provide` only on accepted sensor and Gateway-status paths |
| Brake Health Service v3 | `read` only on required inputs; `actuate` only on the advisory request |
| Outbound provider | subscribe to the advisory target using the minimum permission proven by the pinned API; no other KUKSA path access |
| Gateway VISS client identity | Set only the advisory actuator; no motion-control or general VSS write permission |
| Engineering Dashboard | read/subscribe only |

The exact permission needed by a v1 target subscriber must be confirmed against
the running verifier; it must not be widened to `actuate:*` or `read:*` merely
to make the prototype work. The service and both provider directions should
use separate credentials so that one compromise does not combine sensor
publication, advisory request, and Gateway delivery privileges.

ADR 0010 now fixes the target credential architecture. Upstream Eclipse KUKSA
is not modified. Aos Service Manager and IAM own each SOTA instance's
`AOS_SECRET` and registered permissions. The Vehicle Data Platform Component's
thin broker calls `GetPermissions` for the `kuksa` functional-server ID and
maps only the current, VDP-contract-compatible result into a short-lived JWT;
it has no parallel service identity or per-service policy store. The provider
uses a separately bound short-lived platform credential for its accepted
`provide`/`create` paths. Its exact FOTA identity binding and the per-Unit
IAM/PKCS#11 signing-key integration remain qualification gates. Cloud-side
pre-transfer permission admission remains a future AosCloud feature and is not
claimed by the current design.

## Failure and safety rules

- Reject every Set path except the exact advisory actuator.
- Validate type and enum before any network operation and again at the Gateway.
- Reject expired, excessively future-dated, reordered, duplicated, or
  rate-violating requests.
- Fail closed on missing authorization, source loss, reconnect ambiguity, or
  malformed data.
- Never map the advisory channel to throttle, brake, steering, gear, or
  autopilot control.
- Do not persist KUKSA or VISS credentials in Git, the service image, a FOTA
  bundle, or demo evidence.
- Log identifiers and outcomes, not bearer tokens, certificate subjects,
  unrestricted payloads, or raw sensitive telemetry.
- Local advisory processing must not wait for AosCloud or the Function
  Backend.

## Options rejected for the baseline

| Option | Reason |
| --- | --- |
| Service calls Gateway VISS directly | Breaks the KUKSA application boundary and grants the SOTA service a vehicle-network interface. |
| Reuse the vehicle-control channel | Mixes diagnostic advisory semantics with safety-relevant motion ownership. |
| General KUKSA-to-VISS write bridge | Creates an unrestricted actuation tunnel and makes future signals writable by accident. |
| Report only to the Function Dashboard | Does not prove the required local round trip to the vehicle side and fails offline. |
| Claim v2 semantics on the current VM | The pinned runtime and existing service contract use `kuksa.val.v1`. |

## Required experiments

1. Add the two provisional entries to a scratch VSS overlay and prove the
   pinned Databroker exposes the actuator target and current status correctly.
2. Implement the ADR 0010 credential exchange and prove valid/invalid
   `AOS_SECRET`, allowed/excess path and mode requests, complete-request
   rejection, expiry, refresh, service removal, and restart behavior.
3. Determine the minimum permission for the outbound target subscription.
4. Prototype Set authorization and client authentication on a private Gateway
   route; prove every other path remains read-only.
5. Exercise fresh, stale, duplicated, reordered, invalid-enum, unauthorized,
   reconnect, and restart cases.
6. Measure event-to-Gateway-status latency with Cloud connectivity present and
   absent.
7. Prove service/provider rollback does not replay a previously stored v1
   target.
8. Design and qualify the `kuksa.val.v2` migration before treating v1 target
   semantics as a production pattern.

## Impact on Architecture 1.0

The high-level flow remains valid. The detailed design must explicitly state
that the first implementation uses the pinned v1 target-value compatibility
path, that VISS Set success is not final actuation evidence, and that the
Gateway status feedback is mandatory. The target delta includes both VISS
authorization and a Gateway advisory handler; TLS alone is not sufficient.
Credential issuance follows ADR 0010 and is part of the Vehicle Data Platform
Component, not a standalone adapter or a modification to Eclipse KUKSA.

## Sources

- [`carla-ego-runtime` VISS compatibility profile](../../../../carla-ego-runtime/docs/viss-profile.md)
- [COVESA VISS 3.1 specification](https://github.com/COVESA/vehicle-information-service-specification/tree/v3.1)
- [Eclipse KUKSA Databroker 0.5.0](https://github.com/eclipse-kuksa/kuksa-databroker/tree/0.5.0)
- [`aos-vehicle-platform` provider architecture](../../../../aos-vehicle-platform/docs/architecture.md)
- [Current High-Level Architecture 1.4](../../architecture/high-level-architecture.md)
- [ADR 0010: Aos–KUKSA Credential Broker](../../architecture/decisions/0010-aos-kuksa-credential-broker.md)
