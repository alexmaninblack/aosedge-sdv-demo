<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Protocol and executable-contract status — demo-v1.1

Reviewed against the published source checkpoint and Factory39 evidence on
24 September 2026. Contract versions, product wire versions, functional
profiles, allocated Cloud releases and the demo tag are different namespaces.
This map documents implemented behavior; it does not silently regenerate
digest-pinned historical profiles or claim every design fixture tests the live
implementation. See the [implemented architecture](../docs/architecture/current-implementation.md).

## Complete contract-family map

| Family | Current implementation / authority | Boundary or discrepancy |
| --- | --- | --- |
| [Artifact publication](artifact-publication-profile/README.md) | Demo Control unsigned preparation and selected OEM/SP signing/publication | ADR 0016 supersedes pre-signed reuse. Publication is not installation; non-exportable artifact signing remains future hardening |
| [Vehicle hardware](vehicle-hardware-profile/README.md) | Pinned simulator inventory and Gateway projection | Native physics is real simulation, not a production hardware certification or complete all-sensor acceptance |
| [Simulator control](simulator-control-context/README.md) | Controller/Gateway frame-coherent channel, modes and discontinuity; native Return to road | Return to road ends stationary Manual. Broader transition/cleanup matrix still needs its evidence |
| [Source assignment](exclusive-live-source-assignment/README.md) | Same-Unit exclusive source and strict Test trust | Old server-only local exception is historical. Test-only Studio does not imply completed dual-VU/PU promotion |
| [VISS trust](viss-trust-telemetry-profile/README.md) | Selected-Unit mTLS, distinct safety/runtime/read-only roles | Default current Test is not the earlier server-only exception; engineering exceptions are not strict-trust proof |
| [FOTA Safe Stop](platform-fota-safe-stop/README.md) | OEM runtime gate; native stop completion and retained component recovery | Standard profile versus explicit Test `demo-5s` remain different. SOTA is not gated by this policy |
| [VDP compatibility](vdp-compatibility-profile/README.md) | Common runtime with V1/V2/V3 capability selection | Presenter Cloud/artifact binding supplies exact profile. Services check local input, not Cloud or inferred version |
| [KUKSA authorization](kuksa-current-demo-authorization/README.md) | Fixed-resource Unix exchange, IAM TLS lookup, 300s JWT / renewal at 180s, private sessions | Native permission-key capacity and KAC wire maxima are distinct bounds; no caller-selected paths or Cloud renewal dependency |
| [Native runtime inputs](service-runtime-inputs/README.md) | Public metadata v2, immutable package release, native identity and private token path | Five-field metadata is not exact installed-profile evidence; old mandatory OCI-digest input is retired |
| [Brake windows](brake-telemetry-window/README.md) | V1 finite capture, persistent spool and canonical HTTP messages | Apply accepted 5s freshness and 100-ms source-bucket amendments; old golden baseline is not the current cadence |
| [Brake model](brake-health-model/README.md) | V2/V3 fixed-point model, persistent state and derived outbox | Synthetic demonstration model; frozen 20/20 stimulus/calibration acceptance is not proved by isolated successes |
| [Brake advisory](brake-health-advisory-policy/README.md) | V3 retained-model activation, typed request, lease and correlated Gateway fact | Reset is the accepted separate demo exception; a write/HTTP ACK is not Gateway application |
| [Brake runtime](brake-health-runtime/README.md) | Native quotas, independent input/analytics/delivery/advisory state | Ordinary packages: 1024 files and 24 PIDs. Declaration/monitoring is not a full quota stress proof |
| [Brake Cloud](brake-cloud-api/README.md) | Durable transaction/ACK, query/window detail, SSE notification, reset and scoped cleanup | Product v2 and observation v3 coexist with legacy decoders. Integrated Presenter is not the standalone fixture shell |
| [Tire model](tire-health-model/README.md) | Functional V1 with VDP V3 dynamics, bounded estimator/hysteresis, persistence, advisory | Missing samples do not prove `INCOMPATIBLE_VDP`; apply option A. Full healthy/pre-aged calibration remains separate |
| [Tire Cloud](tire-cloud-api/README.md) | Independent product delivery/query/SSE, reset, current-Test context/cleanup | **Legacy executable-profile drift:** two-UID cleanup/schema predates current one-Test handler and extra count/proof fields; use [current wire description](tire-cloud-api/studio-current-wire.md) |
| [QM advisory](qm-advisory-profile/README.md) | Typed JSON leaf request/status and readiness, exact endpoints, freshness/replay/lease | Brake V3 and Tire V1; package release remains unchanged in provenance. Short genuine readiness interruptions are not hidden |
| [Function observation](service-function-observation/README.md) | Closed v3 producer/backend/Presenter chain with epoch/sequence ordering | Deployed; legacy Tire status remains readable. Delayed status cannot replace newer source state |
| [Local hosting](local-demo-hosting/README.md) | Separate backend containers and stores; host Demo Control/Presenter and native panels | Original three-container dashboard/helper topology is not the current Studio implementation; local isolated HTTP is not production authentication |
| [Run state/cleanup](demo-run-state/README.md) | Bounded operation journal, fresh Test overlay, peer-preserving Finish | Apply Test-only and lifecycle amendments; no Studio Park/Resume. .39 ignition is separate, guarded and same-identity |
| [External connectivity](vehicle-external-connectivity/README.md) | Independent VM vehicle/external planes and explicit link state | .39 focused OFF/ON passed. Cloud Online, outbox drained and UI freshness are separate milestones; no SLA or dual-vehicle matrix inferred |
| [Tenant quota proof](service-tenant-quota-proof/README.md) | Native package quotas and real controller/instance resource observations | Fixed Tire CPU-load endpoint/worker demonstration is **not implemented**; do not render planned proof as PASS |
| [Shared evidence](shared-evidence-correlation/README.md) | Native identity, source/decision/receipt times, original retries and v3 ordering | Public/legacy digest wording is amended by ADR 0015; a reconnect timestamp is not a synchronization watermark or latency KPI |
| [Software dashboard](software-delivery-dashboard/README.md) | Cloud lifecycle/resource projections and integrated function views | Coverage catalogue and formal CPU verdict/dossier design are not proof that every coverage item has a live implementation |
| [E2E stage evidence](e2e-stage-evidence/README.md) | Atomic operations/reconciliation plus dated qualification receipts | Full composed two-cycle/human acceptance dossier not established for .39; legacy golden stage maps retain their design scope |

## Current wire authorities and amendment precedence

- KAC: [strict request/response schemas](kuksa-current-demo-authorization/README.md)
  and platform helper; one LF-delimited request/response per Unix connection.
- Public inputs: [ADR 0015 migration](service-runtime-inputs/product-message-migration.md)
  and [private placement](service-runtime-inputs/credential-placement.v1.json).
- Products: explicit `.v2.schema.json` messages where defined; old v1 records
  keep original provenance. Current function observations use the separate
  [v3 contract](service-function-observation/v3-contract.md).
- Advisory: [QM profile](qm-advisory-profile/qm-advisory-profile.v1.json) and
  [readiness](qm-advisory-profile/advisory-readiness.v1.json). Authority and
  lease checks remain independent from telemetry source-age budgets.
- Reset: [accepted bounded protocol](../docs/planning/active/work-packets/advisory-readiness-and-demo-reset.md)
  implemented by each backend and service; only the selected current Test
  producer is affected, with durable command/application outcomes.
- Runtime compatibility: [accepted option A](service-runtime-inputs/active-vdp-capability-amendment.md)
  supersedes older instructions to infer an incompatible VDP from missing input.

## Contract-maintenance debt, not a product change

The retained Tire cleanup profile/schema and older design-stage hosting,
dual-role acceptance and compatibility descriptions must not be used as a
complete generated-client specification for the current Studio. Their current
differences are explicit above. Updating executable profile versions, hashes,
all copies and their negative fixtures is a separate controlled synchronization,
not an excuse to loosen production handlers or reinterpret old signed bundles.
The current audit updates prose/traceability and runs available conformance
tests; it does not change wire bytes, thresholds, quotas or security policy.
