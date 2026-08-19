<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R9 Demo Foundation — Integrated Research Summary

> Status: completed research evidence. References to Scenario 1.0 and a
> `G4`-to-`G0` reset describe hypotheses evaluated by this research pass, not
> the current design. Current decisions are owned by High-Level Architecture
> 1.3, Demo Scenario 1.4, Architecture Flows 1.3 and the requirements set.

Status: **research checkpoint complete; decisions require review; implementation
not authorized**.

Date: 2026-08-16.

## Outcome

The staged post-SOP Brake Health story remains technically coherent, and most
of its visible behavior can be built from the current CARLA, Vehicle Gateway,
AosVM, KUKSA, AosCloud, and service scaffolds. Research found three foundation
issues that must be resolved before implementation resumes:

1. **G0 is not generic today.** Both Units contain a provider-specific runtime
   with empty stores. The later `.11` candidate hardens that runtime but does
   not turn it into the reusable post-SOP substrate claimed by Scenario 1.0.
2. **Cloud lifecycle has three gates.** Artifact Verification, Fleet
   Validation, and Campaign promotion are separate. Verification targets must
   be reconciled from pending Unit records because a stale batch previously
   retained an obsolete Unit target.
3. **G4-to-G0 reset is not proven.** SOTA removal is supported, but arbitrary
   post-Apply FOTA removal/downgrade is not. A forward reset component is the
   primary candidate; protected per-Unit golden G0 images are the fallback.

These do not invalidate the HLA. They change the implementation order and the
language used to describe current versus target capability.

The sanitized
[Automotive Orchestration Coverage Matrix](automotive-orchestration-coverage-matrix.md)
adds twenty-one automotive proof obligations to this implementation sequence
and provides the machine-readable input for the Software Delivery Dashboard.
Its confidential OEM source remains outside every Git repository.

## Workstream decisions

| ID | Accepted research direction | Main unresolved gate |
| --- | --- | --- |
| R1 | Separate current provider-specific runtime from the required generic G0 substrate; choose multi-type host or aggregate platform component before Yocto. | AosCore/Cloud multi-type routing and isolation |
| R2 | Show Verification, Fleet Validation, and Campaign separately; derive G0–G4 from accepted manifests plus actual state. | Post-Apply provider reset/removal and mixed-bundle behavior |
| R3 | Native/forward reset first; separate golden image per Unit as out-of-band fallback. | Cloud reconciliation and certificate/identity behavior after restore |
| R4 | Dedicated frame-driven scenario tick owner; Gateway remains observer; 20-run strict-reset qualification. | Calibrated obstacle, brake, and tolerance values |
| R5 | P1 four-signal subset; P2 wheel + simulated wear/energy/temperature; transparent equivalent-event projection; P3 adds a separate advisory capability. | Wheel calibration and model/threshold acceptance |
| R6 | KUKSA v1 target-value compatibility bridge for current VM; one allowlisted advisory; factual Gateway status; planned v2 migration; ADR 0010 keeps upstream KUKSA unchanged and allocates the thin native-IAM Credential Broker and provider identity integration to the VDP Component. | Broker/IAM/PKCS#11 qualification, provider identity binding, scoped authorization, stale/replay behavior, VISS Set handler |
| R7 | Separate lossy bounded S1 samples from durable S2/S3 events; persistent bounded queue; Function Backend never enters local decision path. | Egress policy, credentials, storage persistence, transport |
| R8 | AosEdge native system/service/crash-log request path is real; the demo uses it through the stateless Software Delivery Dashboard without a separate pipeline or store. | Log API permissions, request/result behavior, retention/deletion and offline qualification |
| R9 | Read-only localhost dashboard backend over public API; explicit target mismatch guard; all write actions deferred. | Least-privilege identity, latency, live field values |

## Integrated architecture refinements

### Runtime and release plane

```text
accepted G0 substrate
  -> FOTA P1/P2/P3 platform capability
  -> KUKSA/VSS versioned contract
  -> independently deployed SOTA S1/S2/S3

AosCloud lifecycle for each release
  -> Artifact Verification
  -> Validation Unit delivery
  -> Fleet Validation
  -> Campaign promotion to Demonstration Unit
```

No service is considered ready merely because the container runs. Each Sn must
fail closed until its required Pn contract is present and compatible. Until a
native Service-to-FOTA dependency is released and qualified, provider-first
ordering, runtime readiness and an exact accepted graph manifest form the
current dependency policy. They do not implement or simulate Cloud admission;
the negative rejection scenario remains deferred.

### Vehicle and functional data plane

```text
deterministic CARLA stimulus
  -> Vehicle Gateway VSS actual values
  -> inbound provider
  -> KUKSA current values
  -> Brake Health local processing
       -> bounded asynchronous functional report
       -> one local advisory request at S3
  -> outbound advisory provider
  -> authorized VISS Set
  -> Gateway factual status
  -> Engineering Dashboard
```

The Function Backend and AosCloud remain separate systems. AosCloud manages
software; the Function Backend owns functional Brake Health data. Neither
authorizes the immediate local advisory.

### Common correlation contract

The following identifiers should join the otherwise independent surfaces:

| Identifier | Purpose |
| --- | --- |
| `run_id` | One presentation/qualification run across all surfaces |
| `scenario_id`, `scenario_version`, `configuration_digest` | Exact CARLA stimulus and vehicle-condition profile |
| `event_id` | Durable Brake Health event and backend idempotency key |
| platform graph manifest/digest | Exact G-stage component/service contract |
| provider contract version | P1/P2 data semantics |
| service/model version and digest | Exact inference behavior |
| Unit-role alias | `Validation` or `Demonstration` without exposing credentials/identity |

Logs, dashboards, result manifests, and backend reports should use these
identifiers without copying secrets, certificate subjects, or raw high-rate
telemetry.

## Dependency graph

```text
R1 generic G0 choice ----+----> one accepted G0 rootfs
                         |
R2 Cloud/reset proof ----+----> R3 golden/reset qualification
                         |
                         +----> P1/P2/P3 FOTA lifecycle

R4 deterministic scene -------> R5 signal/model calibration
                                      |
                                      +----> S1/S2 service fixtures
                                      +----> R7 backend envelope/queue
                                      +----> R6 advisory contract

R2 API map -------------------> R9 Software Delivery Dashboard
R8 native log path -----------> R9 Software Delivery Dashboard log view
```

This reveals work that can proceed without waiting for a VM build:

- generic runtime source-level experiments;
- scenario state-machine unit tests and offline trace fixtures;
- P1/P2 schema and model replay design;
- S1/S2 service logic against fixtures;
- read-only dashboard backend using mock/sanitized API responses;
- log normalization and redaction design;
- backend envelope, queue, and idempotency tests.

## Recommended implementation gates

This is sequencing advice for review, not authorization to execute.

### Gate 0 — correct and accept the design baseline

1. Update Scenario 1.0 and architecture flows to distinguish current
   `SM-VPD` from target `SM-GEN`.
2. Replace the single validation box with Artifact Verification, Fleet
   Validation, and Campaign.
3. Mark G4-to-G0 provider removal as required but unproven.
4. Accept the P1/P2/P3 and S1/S2/S3 contract split.
5. Accept the honest model wording and no-driver-HMI boundary.

### Gate 1 — cheap repository-only proofs

1. Test multi-type generic runtime behavior against pinned source without
   Yocto or a provisioned VM.
2. Unit-test the scenario state machine and result manifest.
3. Build replay fixtures for P1/P2 and deterministic S2 output.
4. Test offline queue/idempotency logic with a fake backend.
5. Prototype the read-only Software Delivery data model and target guard with
   sanitized responses.

### Gate 2 — disposable environment proofs

1. Prove the selected generic component mapping on an unprovisioned disposable
   VM.
2. Calibrate CARLA obstacle/braking/wheel telemetry and complete the 20-run
   repeatability gate.
3. Qualify the VDP-owned thin Aos–KUKSA Credential Broker against native IAM
   permissions, per-Unit PKCS#11 signing, separately bound provider credential,
   short-lived read/actuate JWTs, and v1 target subscribe/restart behavior in
   isolation.
4. Qualify Aos service storage persistence and network policy without Cloud
   promotion.

### Gate 3 — build G0 once

Only after Gates 0–2, build one common G0 rootfs, install it on Validation,
qualify its empty state and generic extension isolation, and create a new
protected Validation G0 golden image. Do not rebuild Yocto separately for each
provider feature.

### Gate 4 — staged feature integration

1. P1 on Validation, platform qualification, then S1 and backend integration.
2. P2 backward-compatible update, S2 model integration, exact graph
   acceptance.
3. P3 outbound capability, S3 local advisory, online/offline and fail-closed
   tests.
4. At each stage use the same deterministic scenario digest and promote only
   through the complete Cloud gate sequence.

### Gate 5 — reset and Demonstration promotion

Prove forward/native reset and the golden fallback on Validation. Reset must
cover Cloud, VM, CARLA, service storage, Function Backend, bounded Cloud log
request artifacts, and transient dashboard state. Only then create the
Demonstration golden image and exercise Campaign promotion and reset on that
Unit.

## Cross-cutting invariants

1. Exactly one CARLA tick owner and one active copy of each provisioned Unit
   identity.
2. The Brake Health service talks only to KUKSA, never CARLA or VISS directly.
3. Vehicle motion control stays on the existing separate channel.
4. Local S2/S3 inference and S3 advisory never require Cloud connectivity.
5. The outbound path allows exactly one bounded advisory and no arbitrary
   payload or motion control.
6. Simulated/estimated signals and `demoOnly` model output are always visible
   as such.
7. P2 remains backward compatible with P1; P3 does not silently redefine the
   telemetry schema.
8. Dashboard state is observational; it cannot become desired-state authority.
9. Native AosEdge logs contain operational evidence, not vehicle telemetry or
   functional model truth, and the dashboard stores no independent archive.
10. Every external write, deployment, approval, VM replacement, or Yocto build
    remains a separately reviewed action.

## Contradictions requiring later document cleanup

| Current statement | Required correction |
| --- | --- |
| Generic runtime exists only in `.11` | Provider-specific runtime exists in installed `.1/.2`; no generic runtime exists yet |
| Produced baseline already has generic post-SOP substrate | Retain as target SOP premise, label current demo implementation gap |
| One generic validation approval | Show Artifact Verification, Fleet Validation, and Campaign separately |
| Verification Batch target follows current Unit Set | Compare actual pending recipients; stale batches can retain obsolete targets |
| Reverse provider rollback/remove returns G4 to G0 | Required outcome, mechanism unproven; test forward reset and snapshot fallback |
| A custom log pipeline and store are required for the demo | AosEdge native log collection, Cloud delivery and downloadable results are the accepted path; the Software Delivery Dashboard is a stateless API view |
| Service dependency on provider is Cloud-enforced | Current release has no documented Service-to-FOTA dependency. Platform Team reports it as roadmap work; defer the native rejection demo, use provider-first ordering and fail-closed service readiness, and add no custom admission gate |
| Service artifact digest is always available | Component SHA-256 is public; service OCI digest needs live confirmation |
| Any large brake command can populate ABS/EBA/driver-emergency paths | Preserve standard semantics; derive demo event or use explicit overlay |

## Principal risks

| Risk | Mitigation |
| --- | --- |
| Another 10-hour rootfs iteration loop | Resolve generic runtime source-level and disposable-VM design before one G0 build |
| Wrong Unit receives verification update | New batch only; pending-recipient comparison and dashboard block |
| Reset immediately reconverges to G4 | Reconcile Cloud desired state before VM restore; network isolation guard |
| Stale KUKSA v1 target replays | Freshness/order/idempotency state, restart tests, factual Gateway feedback |
| Demo model sounds scientifically stronger than it is | Transparent equations, versioned constants, simulated provenance, `demoOnly` |
| Scenario varies run to run | One tick owner, fixed timestep/seed, strict reload, 20-run gate |
| Backend outage blocks advisory | Transactional bounded queue and asynchronous uploader |
| Logs become a telemetry leak | Event allowlist, redaction, bounded archives, short retention |

## Review decisions required before implementation

1. Select independently visible multi-type runtime versus aggregate
   `vehicle-data-platform` host.
2. Accept forward reset as primary and golden G0 restore as fallback.
3. Accept the exact P1 subset and P2 simulated/estimated signal categories.
4. Accept the equivalent-severe-braking-event demo model and wording.
5. Accept the pinned KUKSA v1 compatibility bridge plus mandatory v2 migration
   requirement.
6. Select the first Function Backend transport after egress/credential tests.
7. Qualify native AosCloud log request permissions, latency, result retrieval,
   retention/deletion and offline behavior for the Software Delivery Dashboard.

## Research documents

- [R1 — G0 platform baseline](r1-g0-platform-baseline.md)
- [R2 — AosCloud lifecycle](r2-aoscloud-lifecycle.md)
- [R3 — VM recovery and identity](r3-vm-recovery-and-identity.md)
- [R4 — CARLA scenario](r4-carla-scenario-and-signals.md)
- [R5 — Brake Health data and model](r5-brake-health-data-and-model.md)
- [R6 — Advisory and security](r6-bidirectional-advisory-and-security.md)
- [R7 — Functional Cloud and offline](r7-functional-cloud-and-offline.md)
- [R8 — AosEdge native logging](r8-aosedge-native-logging.md)
- [R9 — Dashboards and APIs](r9-demo-dashboards-and-apis.md)
