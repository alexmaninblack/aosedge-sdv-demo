<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Implemented architecture and traceability — demo-v1.1

Reviewed 24 September 2026 against `demo-v1.1`, Factory .39 and its retained
qualification receipts. This is the current implementation view of the accepted
design, not HLA version 1.8 and not a new wire-protocol version. The operator
confirmed that this is the intended version for the documentation audit.

## Reading the design chain

HLA 1.7, Scenario 2.0, Flows 2.1 and System/Component Register 2.1 retain their
stable identities. Their dated D3 allocation states describe the design review,
not current delivery. Apply accepted amendments in date order; use this view
for current implementation and the [audit](../qualification/documentation-implementation-audit-2026-09-24.md)
for unresolved discrepancies. A local or contract test does not prove a full
requirement's live acceptance. No requirement is removed merely because its
implementation is missing.

The [source return point](../qualification/demo-v1.1-return-point.md) binds exact
repository revisions. Factory39 embeds mainline-derived AosCore with retained
explicit patches, KUKSA and the removable KAC helper. FOTA/SOTA releases are
independent of that source tag. Only .39 is retained for new Test creation;
Production and its .31 backing image are preserved and not a prerequisite for
this milestone's Test-only flow.

## Runtime and authority

```text
Mac: CARLA physics → Vehicle Gateway/VISS ⇄ native Driving Control/Telemetry
                          ⇅ selected-Unit mTLS; vehicle network
VM:              OEM VDP provider ⇄ KUKSA ⇄ Brake / Tire SOTA
                          ↑                    ↓ asynchronous outboxes
                 OEM component runtime    Mac-local team backends
                          ↑                    ↓ factual results/history
                 AosCore ⇄ Aos Cloud      integrated Presenter
                              ↓                 ↑
                         lifecycle/resources ───┘
```

The simulator supplies physical observations, not model results. Gateway
remains the final authority for the two typed QM advisory targets and for
motion control. Brake/Tire cannot steer or brake. The read-only engineering
observer, selected platform peer and purpose-bound FOTA safety peer have
different roles; a successful KUKSA write is not Gateway application or driver
acknowledgement. Advisory request/status and readiness are separate signals.

KAC obtains exact native IAM permissions locally and issues bounded KUKSA
credentials; it has no Cloud dependency. The service bootstrap owns the secret
exchange and private token session; the analytics child receives the token
path, not the Aos secret. Provider authority is separately packaged and is not
issued by a service or by its backend. No browser gains VM, signing or QMP
credentials. See the [protocol status map](../../contracts/implementation-status.md).

## Accepted amendments that supersede older wording

| Earlier design wording | Current interpretation and source |
| --- | --- |
| Two fresh VU/PU overlays and mandatory production promotion in every demo | UI-STUDIO-026 scopes this milestone to one Test; Production is preserved, dual-role promotion remains separate scope |
| Pre-signed reusable bundles tied to old certificates | ADR 0016: immutable unsigned prepared content; destination/session-selected OEM or SP signing; exact publication reconciliation |
| Application requires final service OCI digest or a fixed shared token leaf | ADR 0015: immutable package release, native instance identity, strict public metadata v2 and private volatile credential sessions; legacy product decoders retained |
| Service proves exact active VDP version from local metadata/catalog | Accepted 18 September option A: Presenter uses Cloud plus exact artifact/profile binding; services validate actual inputs locally and never infer incompatibility from missing samples |
| Package major number equals functional version | Functional VDP V1/V2/V3, Brake V1/V2/V3 and Tire V1 are independent of monotonically allocated release numbers |
| Old 30-Hz/every-third-frame Brake acquisition | Accepted source-time retention amendment selects the first valid complete frame per 100-ms bucket, with gaps retained |
| Every timing budget is 250 ms | Separate budgets: Brake V1 accepted 5s freshness, Test FOTA `demo-5s`, fixed local control join and advisory lease/future bounds. Never substitute one for another |
| Operator Park/Resume is the pause/restart flow | ADR 0017: Safe Stop pause, no Studio Park/Resume; accepted .39 controller ignition restores the same identity/attachment in Safe Stop under guarded conditions |
| Restart storage loss is a universal current condition | Retained native storage/cold-component corrections have scoped .39 reboot/power-cycle evidence; nonempty-outbox power loss remains unqualified |
| Backend Reset means delete history or repair vehicle | Reset Driver Advisory resets the selected service model/advisory through command/application acknowledgement, retaining history/queues; Finish is separate destructive run cleanup |
| Separate dashboards own every audience view | Integrated Presenter cards/popups use team APIs and native Cloud reads; standalone backend fixture shells are not the integrated live UI |

## Component requirements → implementation → evidence

Each row covers its package's current implemented boundary, not an automatic
PASS for every `REQ-*` / `UT-*` in that package. Full calibration, negative
cases and final acceptance remain as stated below and in the dated receipts.

| Requirement package | Implemented owner / source | Current proof and remaining boundary |
| --- | --- | --- |
| [Vehicle Simulation](../requirements/components/vehicle-simulation.md) | `CarlaSim`; Gateway scenario/controller tooling | Native physics, scripted Brake/Tire maneuvers and road recovery; full frozen healthy/pre-aged repeat matrix is not established by a few successful maneuvers |
| [Vehicle Gateway](../requirements/components/vehicle-gateway.md) | [runtime source](../../../carla-ego-runtime/src/runtime_carla.cpp), [tests](../../../carla-ego-runtime/tests/qm_advisory_test.cpp) | Sampling/units, bounded control handoff, strict selected-peer VISS, typed advisory and native telemetry implemented; complete hardware/actuator and dual-role matrix remain broader obligations |
| [Factory Substrate](../requirements/components/factory-substrate.md) | [platform layer](../../../aos-vehicle-platform/meta-aos-vehicle-platform) | Empty immutable .39, native managers, runtime/KUKSA/KAC and scoped boot/security proofs; manifest not promoted to full live qualification |
| [KUKSA compatibility](../requirements/components/kuksa-authorization-compatibility.md) | [KAC source](../../../aos-vehicle-platform/authorization/aos-kuksa-compat) | Real IAM/TLS/token renewal and offline-local operation; removable compatibility layer, not future native API or hardware-HSM certification |
| [VDP](../requirements/components/vehicle-data-platform.md) | [provider](../../../aos-vehicle-platform/providers/carla-viss-kuksa), Demo Control component preparation | Common current runtime, profile-bound 7/15/23 telemetry paths, typed V3 output; Safe Stop FOTA and restored retained .39 V3 demonstrated; full fresh .39 serial family cycle still open |
| [Aos lifecycle](../requirements/components/aos-lifecycle.md) | Demo Control Unit, component/service publication and assignment modules; native AosCore/Cloud | Guarded Test provision/publish/assign/retire implemented; .39 ignition/offline proof, no new native service-to-FOTA pre-transfer admission or full production-promotion qualification |
| [Brake service](../requirements/components/brake-health-service.md) | [service source](../../../brake-health-service/src/runtime/product.cpp), [runtime profiles](../../../brake-health-service/docs/runtime-profiles.md) | V1 captures, V2 analyzes, V3 preserves model and adds advisory; real inputs/delivery/reset; quota stress/calibration/crash matrix not all complete |
| [Brake Cloud](../requirements/components/brake-health-cloud.md) | [backend](../../../brake-health-cloud/README.md), Presenter | Durable ACK/idempotency, windows/details, products, function observation, Reset and exact cleanup implemented; production ingestion authentication and standalone live dashboard are not claimed |
| [Tire service](../requirements/components/tire-health-service.md) | [service source](../../../tire-health-service/src/runtime/application.cpp) | Functional V1 consumes 15 VDP V3 inputs, estimates, queues and publishes advisory; fixed CPU-load demonstration and complete calibration remain unimplemented/unqualified scope |
| [Tire Cloud](../requirements/components/tire-health-cloud.md) | [backend source](../../../tire-health-cloud/src/store.mjs), Presenter | Separate persistence/ACK/query/SSE/Reset/cleanup; fixed CPU qualification endpoint is not implemented; retained legacy cleanup schema differs from current Studio handler |
| [Demo orchestration](../requirements/components/demo-orchestration.md) | [orchestrator](../../apps/demo-orchestrator), [Presenter](../../apps/presenter-ui) | Shared guarded commands, bounded read paths, source attachment, layout, resources, Finish and boot recovery; host sleep/wake remains planning |
| [Cross-cutting](../requirements/components/cross-cutting.md) | Native policy/identity, contracts and repository/security gates | Enforcing/private credentials, separate teams, bounded transport and scoped negatives; no production safety/security certification inferred |
| [End-to-end acceptance](../requirements/components/end-to-end-acceptance.md) | [qualification receipts](../qualification/README.md) | Earlier serial cycles and current .39 focused proof are distinct; no complete .39 P8 dossier, long soak or nonempty-queue power-loss PASS |

## Protocol, compatibility and resource facts

VDP profiles expose seven base signals, fifteen with wheel inputs, then
twenty-three with slip inputs; only V3 enables typed outbound advisory.
Brake V1/V2/V3 consume their own six/twelve/twelve-signal processing subsets.
Tire V1 requires the fifteen-signal V3 dynamics subset. Presence of all catalog
entries alone is not a live publisher or fresh sample.

Current service packages request 1024 file descriptors; Brake has 24 PIDs and
Tire 16. Native AosCore enforces quotas. CPU graphs in DMIPS are not proof of
the planned fixed-load isolation experiment. That experiment must not be
described as available merely because its design profile exists.

Raw window/derived product wire revision 2 removes the old mandatory service
OCI-digest provenance; old queued records retain their own schema and bytes.
Function observation revision 3 is separate from both product revisions and
functional V3. HTTP durable ACK, SSE notification, local KUKSA readiness,
advisory Gateway Status and Cloud lifecycle each establish different facts.

## Lifecycle implementation

Use the [operator workflow](../operations/current-demo-workflow.md). The normal
order is empty controller → detached simulator → VDP publication → provisioning
and Online → same-source attachment → Safe Stop FOTA → successive SOTA/FOTA
checks → offline/recovery → confirmed Finish. Publish versions individually.

The [boot recovery worker](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/source_boot_recovery.py)
is Presenter-owned, not a new guest agent. It runs bounded checks for the
same Test, Unit/Node/source identity, fresh boot, externalON and no conflicting
operation. It never opens an explicitly blocked gate, creates a new identity,
rebuilds CARLA or resumes Autopilot. Uncertain/failed attempts require
reconciliation. Laptop sleep/wake is not this controller-ignition feature.

## Qualification and residual mismatches

The [audit register](../qualification/documentation-implementation-audit-2026-09-24.md)
is the current consolidated list. The
[protocol map](../../contracts/implementation-status.md) records legacy
machine-readable packages that need a separately versioned synchronization;
passing their old fixtures is not proof of current backend conformance.
Unchanged legacy digests are not silently relabeled as current runtime wire
contracts. Full production promotion, CPU stress proof and calibration stay
visible instead of being removed from requirements.
