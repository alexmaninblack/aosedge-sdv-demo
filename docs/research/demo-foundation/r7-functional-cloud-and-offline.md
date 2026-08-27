<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R7 — Functional Cloud Contract and Offline Operation

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream defines what the Brake Health service sends to its Function
Team Backend, which information must survive loss of connectivity, and how the
Function Dashboard remains separate from AosCloud and the vehicle's local
decision path.

## Evidence summary

| Finding | Classification |
| --- | --- |
| The current Brake Health repository is a packaging scaffold only; it does not connect to KUKSA, persist data, run analysis, or contact a backend. | **PROVEN** |
| Its current package requests read-only KUKSA access, 8 MiB storage and 1 MiB state, and omits `offlineTTL`. | **PROVEN** |
| AosEdge documents `/state.dat` as persistent across restarts and updates of the same service version, and `/storage/` as persistent across service-version updates. | **PROVEN in current official documentation** |
| An absent service `offlineTTL` is documented as allowing the service to continue running indefinitely while the Unit is offline. | **PROVEN in schema; live Cloud defaults require confirmation** |
| AosEdge service networking is isolated and public egress is policy-controlled. The current service has no qualified backend network policy or credential path. | **PROVEN / unresolved integration** |
| A local inference path can be independent of Cloud while reporting asynchronously through a bounded persistent queue. | **PROPOSED** |

## Separation of responsibilities

| System | Owns | Must not own |
| --- | --- | --- |
| Brake Health service | Signal subscription, local feature calculation, local model inference, advisory decision, report queue | FOTA/SOTA authority, raw CARLA/VISS access, Cloud validation |
| Function Backend | Functional event ingestion, idempotency, long-term function data, dashboard API | Immediate advisory authorization, vehicle actuation, software delivery state |
| Function Dashboard | Brake Health data, model/service version, freshness, connectivity and sync state | AosCloud lifecycle truth, Gateway VISS truth |
| AosCloud | Unit identity, desired software state, validation/campaign lifecycle, operational monitoring/log requests | Functional telemetry storage or predictive decision |

## Recommended data products by stage

The service should not treat every 30 Hz input as one durable Cloud event.
Different stages need different products:

| Stage | Product | Delivery and retention |
| --- | --- | --- |
| S1 | Selected `TelemetrySample` for the Function Dashboard | Bounded latest-value stream, initially within 1–5 Hz with 5 Hz as a candidate; loss-tolerant and not replayed as a raw backlog |
| S2 | `BrakeHealthObservation` and `PredictionResult` around a deterministic braking event | Durable event report with original event time and model version |
| S3 | `AdvisoryEvent`, Gateway outcome, and offline/sync state | Durable, correlated report; immediate local advisory is independent of upload |

This preserves the Stage 3 story while avoiding a misleading architecture in
which the backend becomes a second vehicle-data broker.

## Versioned functional envelope

Every durable report should contain a small, transport-independent envelope:

```text
schema_version
event_id
run_id
unit_pseudonym
event_type
event_time
created_time
service_version
model_version
provider_contract_version
signal_quality_summary
simulated_or_estimated_inputs
severity
confidence
evidence_summary
advisory_request
gateway_status
connectivity_state_at_event
```

Rules:

- `event_id` is globally unique and is the backend idempotency key.
- `event_time` is the vehicle-side occurrence time and never changes on retry;
  backend receipt time is separate.
- `unit_pseudonym` is a demo-safe stable identifier, not a certificate subject,
  private key identity, or public VIN.
- Every simulated or estimated signal remains explicitly marked.
- `evidence_summary` is bounded and versioned; it is not an arbitrary log or a
  raw telemetry dump.
- The envelope schema evolves independently of the VSS/KUKSA signal contract.

## Offline queue design

The recommended first implementation uses a small transactional queue below
the Aos service `/storage/` mount because official AosCore documentation says
that storage persists across service-version updates. Exact persistence on the
pinned AosVM must still be qualified.

```text
local inference
  -> commit durable event with event_id
  -> local advisory continues immediately
  -> asynchronous uploader batches pending events
  -> local demo backend accepts and persists idempotently
  -> backend deduplicates by event_id
  -> local queue records acknowledgement and compacts safely
```

Suggested demo bounds are a maximum byte budget plus a maximum record count,
for example 4 MiB or 2,000 small event reports, whichever is reached first.
The final values require measurement. The uploader uses exponential backoff
with jitter, a request timeout, and a circuit-open interval; it never blocks
KUKSA subscription or local inference.

If the pending-only queue reaches its hard bound, the service must preserve
local operation, increment a visible loss counter, emit one rate-limited
operational error, and apply a documented eviction policy. Silent unbounded
growth and blocking the advisory decision are both unacceptable.

The S1 dashboard sample stream uses latest-value semantics rather than filling
this durable queue. When disconnected, the Function Dashboard shows the last
received sample and age; reconnect resumes current samples instead of replaying
hours of stale points.

## Transport and trust recommendation

Use a versioned application contract independent of a particular transport.
For the first demo, HTTPS batch ingestion is the simplest candidate because it
supports bounded request/response acknowledgement and backend idempotency with
minimal infrastructure. MQTT remains a valid later option if the OEM Function
Team already owns a broker and topic-security model.

This transport choice is **PROPOSED**, not yet accepted. The implementation
must first prove:

- Aos service public egress policy and DNS behavior on the pinned Unit;
- a backend hostname allowlist rather than unrestricted public access;
- TLS server verification and an approved per-Unit or per-service
  authentication mechanism;
- credential delivery and rotation without embedding secrets in the image;
- upload/download quotas sufficient for the bounded data products.

Aos Unit credentials and `AOS_SECRET` must not be repurposed as an application
backend bearer token without an explicit platform security design.

## Connectivity state

The service should derive functional-backend connectivity from its own
successful acknowledgements and timeout state, not from whether AosCloud is
online. The two connections can fail independently. The Function Dashboard
therefore distinguishes:

- vehicle Unit online to AosCloud;
- service running on the Unit;
- Function Backend reachable from the service;
- pending durable event count and oldest age;
- timestamp of the last acknowledged report.

## Restart and update behavior

- A process restart reopens and validates the queue before resuming uploads.
- An SOTA update must preserve the queue or migrate it transactionally.
- Removal/reassignment or forward-repair recovery must be able to read the
  previous state or leave a versioned spool for a compatible recovery tool.
- A corrupt record is quarantined within the byte limit and does not prevent
  later valid records from syncing.
- Clock discontinuities are recorded; ordering relies on event identity and a
  monotonic local sequence where needed, not wall-clock time alone.
- Removing the service must have an explicit policy for its persistent storage
  and pending reports; it must not be assumed to erase them automatically.

## Required experiments

1. Confirm generated `offlineTTL` and public-connection policy for the actual
   service version returned by AosCloud.
2. Prove `/storage/` contents survive service restart, S1→S2 update,
   removal/reassignment recovery, Unit reboot, and temporary Cloud loss on the
   pinned AosVM.
3. Measure a realistic event envelope and select queue byte/record limits.
4. Prove backend idempotency under duplicate, timeout-after-commit, reordered,
   and partial-batch cases.
5. Prove that a blocked or unreachable backend does not change local inference
   or advisory latency.
6. Prove service egress allowlisting, DNS recovery after Mac network changes,
   TLS verification, credential rotation, and quota accounting.
7. Define removal/reset behavior for pending functional data.
8. Verify the Function Dashboard labels last-received time, original event
   time, backlog state, and simulated inputs honestly.

## Impact on Architecture 1.0

The asynchronous Function Backend arrow remains correct. The detailed design
should split lossy S1 dashboard samples from durable S2/S3 health events and
make backend reachability independent of AosCloud connectivity. `/storage/`
persistence and no-offline-TTL behavior are promising platform capabilities,
but remain release-qualification gates on the pinned VM.

## Sources

- [`brake-health-service` architecture](../../../../brake-health-service/docs/architecture.md)
- [AosEdge Service Manager launcher and persistence](https://docs.aosedge.tech/docs/aos-core/architecture/service-manager/launcher)
- [AosEdge Service configuration schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-service-config)
- [AosEdge Network Manager](https://docs.aosedge.tech/docs/aos-core/architecture/service-manager/network-manager)
- [Current High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- [Current Demo Scenario 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
