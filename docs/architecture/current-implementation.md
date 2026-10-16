<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Implemented architecture and traceability

- Status: as-built candidate view; not blanket requirements acceptance
- Version: 2.1
- Prepared: 2026-10-07
- Updated: 2026-10-15
- Owner: SDV Lab integration
- Current selection: [launcher catalog](../../workspace/launcher-catalog.json) and its immutable delivery descriptor
- Source inputs: [current source lock](../../workspace/inputs/sources.lock.json)

## Reading the design chain

The accepted chain remains HLA 1.8 → Scenario 2.1 → Flows 2.2 →
System Requirements 2.2 → Component Register 2.2 → component packages.
Stable IDs and unfulfilled obligations remain intact. Accepted later amendments
take precedence over original design examples; implementation is not authority
to invent a new requirement or mark an unexecuted test passed.

The [current baseline](../qualification/current-baseline.md) points to the
selected release and its exact evidence. The
[release report](../qualification/release-automation-2026-10-13.md#successor-published-on-15-october-120-rc2)
records current main/tag publication, M1 Production runtime checks, separate
native Setup first use and anonymous delivery. Kit028 / Setup042 and
demo-v1.1 / Factory .39 are historical; the
[Kit028 return point](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/cc75541f255f3d2fb0fd670053687ebe406c37ee/docs/qualification/kit028-setup042-source-publication-2026-10-05.md)
preserves its exact sources. The retained Factory .41
embeds mainline-derived AosCore with explicit retained patches, KUKSA and the
removable KAC helper. It is not unmodified current upstream mainline.

## Installed workstation

One complete DMG supplies signed Setup and a digest-bound Runtime Kit:
application/UI, prebuilt standalone CARLA/Driving Control/Gateway, QEMU and
the ARM64 controller base image (Factory), preparation inputs, Cloud SDK and backend image archive. No Unreal
Editor, source checkout or compiler is required on the operator Mac.
Docker Engine and access/permissions remain prerequisites.

The **Factory image** is a clean, unprovisioned Linux/AosEdge base used to
create the **ARM64 virtual controller**, a QEMU VM. VDP and the demo services
are delivered later. The Linux **Builder** that compiles this image is a
separate development tool, not part of the running vehicle. See the
[reader overview](../../README.md#how-the-lab-fits-together) and
[component map](product-map.md) for locations and responsibilities.

Setup wraps existing transaction, selection and Demo Control code; it does not
own a second vehicle lifecycle. Immutable program/input versions are separate
from a private instance containing credentials or their references, release
continuity, workspace metadata, run journal, VM and backend data. Opening windows
creates no vehicle journal; Create Controller does. Installer actions cannot
silently adopt a foreign instance or replace a live selected version.

The first-use topology is one OEM and one associated SP with independent Brake
and Tire identities. Cloud reads and backend-image preparation are explicit
steps. Open demo opens Presenter; it does not create or start a controller.
Integrated Install / Connect / Open is implemented; native issuance/connection
with existing accounts passed on M1 Production. Ordinary retained-Test
Stop/Start is implemented and passed the separate visible UI campaign.
New-account registration and broader interruption/recovery cases remain separate.
See the [native Setup contract](../../contracts/distribution-installation/native-setup.md).

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
| [Vehicle Gateway](../requirements/components/vehicle-gateway.md) | [runtime source](https://github.com/alexmaninblack/carla-ego-runtime/blob/main/src/runtime_carla.cpp), [tests](https://github.com/alexmaninblack/carla-ego-runtime/blob/main/tests/qm_advisory_test.cpp) | Sampling/units, bounded control handoff, strict selected-peer VISS, typed advisory and native telemetry implemented; complete hardware/actuator and dual-role matrix remain broader obligations |
| [Factory Substrate](../requirements/components/factory-substrate.md) | [platform layer](https://github.com/alexmaninblack/aos-vehicle-platform/tree/main/meta-aos-vehicle-platform) | Retained immutable .41 controller image with native managers, KUKSA/KAC, VLAN allocation and source-timestamp corrections; current installed runtime passed API/visible UI checks, not all Factory requirement cases |
| [KUKSA compatibility](../requirements/components/kuksa-authorization-compatibility.md) | [KAC source](https://github.com/alexmaninblack/aos-vehicle-platform/tree/main/authorization/aos-kuksa-compat) | Real IAM/TLS/token renewal and offline-local operation; removable compatibility layer, not future native API or hardware-HSM certification |
| [VDP](../requirements/components/vehicle-data-platform.md) | [provider](https://github.com/alexmaninblack/aos-vehicle-platform/tree/main/providers/carla-viss-kuksa), Demo Control component preparation | Common current runtime, profile-bound 7/15/23 telemetry paths, typed V3 output; current M1 runtime passed serial V1→V2→V3 Safe Stop FOTA and moving QM service updates; VDP-TIMEOUT-01 remains deferred |
| [Aos lifecycle](../requirements/components/aos-lifecycle.md) | Demo Control Unit, component/service publication and assignment modules; native AosCore/Cloud | Guarded Test provision/publish/assign/retire implemented; current Production-environment Test passed ignition/offline checks, not separate vehicle Production-role promotion or new native service-to-FOTA pre-transfer admission |
| [Brake service](../requirements/components/brake-health-service.md) | [service source](https://github.com/alexmaninblack/brake-health-service/blob/main/src/runtime/product.cpp), [runtime profiles](https://github.com/alexmaninblack/brake-health-service/blob/main/docs/runtime-profiles.md) | V1 captures, V2 analyzes, V3 preserves model and adds advisory; real inputs/delivery/reset; quota stress/calibration/crash matrix not all complete |
| [Brake Cloud](../requirements/components/brake-health-cloud.md) | [backend](https://github.com/alexmaninblack/brake-health-cloud/blob/main/README.md), Presenter | Durable ACK/idempotency, windows/details, products, function observation, Reset and exact cleanup implemented; production ingestion authentication and standalone live dashboard are not claimed |
| [Tire service](../requirements/components/tire-health-service.md) | [service source](https://github.com/alexmaninblack/tire-health-service/blob/main/src/runtime/application.cpp) | Functional V1 consumes 15 VDP V3 inputs, estimates, queues and publishes advisory; fixed CPU-load demonstration and complete calibration remain unimplemented/unqualified scope |
| [Tire Cloud](../requirements/components/tire-health-cloud.md) | [backend source](https://github.com/alexmaninblack/tire-health-cloud/blob/main/src/store.mjs), Presenter | Separate persistence/ACK/query/SSE/Reset/cleanup; fixed CPU qualification endpoint is not implemented; retained legacy cleanup schema differs from current Studio handler |
| [Demo orchestration](../requirements/components/demo-orchestration.md) | [orchestrator](../../apps/demo-orchestrator), [Presenter](../../apps/presenter-ui) | Shared guarded commands, bounded read paths, source attachment, layout, resources, Finish and boot recovery; host sleep/wake remains planning |
| [Cross-cutting](../requirements/components/cross-cutting.md) | Native policy/identity, contracts and repository/security gates | Enforcing/private credentials, separate teams, bounded transport and scoped negatives; no production safety/security certification inferred |
| [End-to-end acceptance](../requirements/components/end-to-end-acceptance.md) | [qualification receipts](../qualification/README.md) | Current runtime passed 118 API and 42 visible browser UI checks plus required native driving input; separate native Setup first use passed. New-account signup, full native return journey, full P8 dossier, long soak and nonempty-queue power loss are not closed |

## Protocol, compatibility and resource facts

VDP profiles expose seven base signals, fifteen with wheel inputs, then
twenty-three with slip inputs; only V3 enables typed outbound advisory.
Brake V1/V2/V3 consume their own six/twelve/twelve-signal processing subsets.
Tire V1 requires the fifteen-signal V3 dynamics subset. Presence of all catalog
entries alone is not a live publisher or fresh sample.

Current service packages request 1024 file descriptors; Brake has 24 PIDs and
Tire 16. Brake requests 250 DMIPS and Tire 600 DMIPS; the latter is the
authorized test envelope, not a completed isolation proof. Native AosCore enforces quotas. CPU graphs in DMIPS are not proof of
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

## Source time and continuity

Factory .41 preserves original source timestamps in KUKSA VAL v1 output.
Refreshing a cached value must not turn old data into fresh input. Current
Brake/Tire sources separate input acquisition from longer processing and
preserve subscription continuity across credential renewal; Tire also recovers
interrupted state writes. These corrections do not widen freshness tolerances.
Load-sensitive readiness and VDP-TIMEOUT-01 remain explicitly deferred.

## Qualification and residual mismatches

The [current baseline](../qualification/current-baseline.md) and selected release
report supply current acceptance boundaries. The
[7 October audit register](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/qualification/documentation-reconciliation-2026-10-07.md)
retains that review's dated findings. The
[protocol map](../../contracts/implementation-status.md) records legacy
machine-readable packages that need a separately versioned synchronization;
passing their old fixtures is not proof of current backend conformance.
Unchanged legacy digests are not silently relabeled as current runtime wire
contracts. Full production promotion, CPU stress proof and calibration stay
visible instead of being removed from requirements.
