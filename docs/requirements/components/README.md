<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Requirement Packages

- Status: Accepted requirement packages; implementation inventory reviewed 2026-09-24
- Prepared: 2026-08-18
- Owner: System Architecture

This directory contains the D3 component-level requirements derived from the
accepted system design. Each package owns one readable component boundary and
connects that boundary to stable system requirements, architecture flows,
interfaces and verification obligations.

Use the [component requirement package template](template.md) for every new
package. The template deliberately keeps the requirement statement beside its
short name and verification intent so a reader does not have to decode a table
of unexplained identifiers.

## Planned Packages and Order

All thirteen packages exist. The order below is the original decomposition order;
the final column is the current **implementation scope**, not blanket acceptance
of every requirement. See the [current implementation matrix](../../architecture/current-implementation.md)
for owning source and dated evidence, and each package's current baseline/gates.

| Order | Package | File | Requirement / unit-test prefix | Current scope — demo-v1.1 / Factory .39 |
| --- | --- | --- | --- | --- |
| 1 | [`CR-VEHICLE-SIM`](../component-decomposition-and-interface-register.md#cr-vehicle-sim) | [Vehicle Simulation](vehicle-simulation.md) | `VEHICLE-SIM` | Native physics, control and real maneuvers implemented; formal repeatability/calibration and full hardware coverage remain open |
| 2 | [`CR-GATEWAY`](../component-decomposition-and-interface-register.md#cr-gateway) | [Vehicle Gateway](vehicle-gateway.md) | `GATEWAY` | Strict selected-peer VISS, telemetry, typed advisory and native control implemented; broader negative/dual-role matrix remains |
| 3 | [`CR-FACTORY`](../component-decomposition-and-interface-register.md#cr-factory) | [Factory Substrate](factory-substrate.md) | `FACTORY` | Factory .39 built and focused ignition/offline proof recorded; complete fresh serial qualification remains open |
| 4 | [`CR-KAC`](../component-decomposition-and-interface-register.md#cr-kac) | [KUKSA Authorization Compatibility](kuksa-authorization-compatibility.md) | `KAC` | Native IAM mapping, private JWT lifecycle and Factory integration implemented; scoped local/offline proof |
| 5 | [`CR-VDP`](../component-decomposition-and-interface-register.md#cr-vdp) | [Vehicle Data Platform](vehicle-data-platform.md) | `VDP` | V1/V2/V3 common-runtime artifacts, Safe Stop FOTA and V3 advisory implemented; full fresh .39 progression remains open |
| 6 | [`CR-AOS`](../component-decomposition-and-interface-register.md#cr-aos) | [Aos Lifecycle](aos-lifecycle.md) | `AOS` | Selected staging Test provisioning, serial publication/assignment, observation and retirement implemented; native dependency admission remains deferred |
| 7 | [`CR-BHS`](../component-decomposition-and-interface-register.md#cr-bhs) | [Brake Health Service](brake-health-service.md) | `BHS` | V1 windows, V2 model and V3 advisory implemented; independent calibration and full fault/resource matrix remain open |
| 8 | [`CR-BRAKE-CLOUD`](../component-decomposition-and-interface-register.md#cr-brake-cloud) | [Brake Health Cloud Product](brake-health-cloud.md) | `BRAKE-CLOUD` | Real ingest/query/reset/cleanup implemented; integrated Presenter is live, standalone Dashboard remains fixtures |
| 9 | [`CR-TIRE`](../component-decomposition-and-interface-register.md#cr-tire) | [Tire Health Service](tire-health-service.md) | `TIRE` | Real V1 model, advisory and durable delivery implemented; formal calibration and CPU worker remain open |
| 10 | [`CR-TIRE-CLOUD`](../component-decomposition-and-interface-register.md#cr-tire-cloud) | [Tire Health Cloud Product](tire-health-cloud.md) | `TIRE-CLOUD` | Real API, SQLite, Test-scoped cleanup and observation implemented; legacy cleanup schema drift and CPU control remain open |
| 11 | [`CR-DEMO`](../component-decomposition-and-interface-register.md#cr-demo) | [Demo Orchestration](demo-orchestration.md) | `DEMO` | Presenter, CLI, lifecycle, monitoring, Reset and guarded ignition recovery implemented; host sleep/wake remains planned |
| 12 | [`CR-CROSS`](../component-decomposition-and-interface-register.md#cr-cross) | [Cross-Cutting Security and Operations](cross-cutting.md) | `CROSS` | Native trust, isolation and scoped offline/recovery proof; complete security/resource qualification not claimed |
| 13 | [`CR-E2E`](../component-decomposition-and-interface-register.md#cr-e2e) | [End-to-End Acceptance](end-to-end-acceptance.md) | `E2E` | Dated receipts and source gates exist; full .39 all-version/Finish and remaining negative matrix are not complete |

D3 review dates and requirement/verification obligations remain preserved.
Design approval is not implementation or deployment authorization. Historical
design-review status annotations inside a requirement do not override the
current baseline and qualification gates.

Shared decisions remain in the [D4 register](../d4-decision-register.md).
Implementation discrepancies are tracked in the [documentation audit](../../qualification/documentation-implementation-audit-2026-09-24.md),
including executable-contract drift; they are not silently accepted as a new
protocol.

## Stable Identifier Rules

- Component requirements use `REQ-<PACKAGE>-NNN` and a matching lowercase
  permanent anchor. Example shape: `REQ-<PACKAGE>-NNN`.
- Required isolated unit-test obligations use `UT-<PACKAGE>-NNN` and a matching
  lowercase permanent anchor. Example shape: `UT-<PACKAGE>-NNN`.
- `<PACKAGE>` is the exact prefix in the table above. Identifiers are never
  renumbered or reused after review.
- A requirement links to named parent `SYS-*`, `AF-*`, `CMP-*`, `IF-*` and
  `CR-*` definitions. A bare identifier list is not an adequate reader view.
- A test result references the stable requirement and test-obligation IDs; an
  implementation-specific function name may change without breaking design
  traceability.

## D3 and D4 Boundary

D3 defines component behavior, acceptance criteria, required verification
levels, testability and unit-test obligations. It answers **what must be
proved** without freezing an implementation.

D4 freezes executable interface contracts, fixtures, test cases, suites and
retained-evidence formats. It answers **exactly how the cross-component and
end-to-end proof is executed**. D4 may refine a test procedure but must not
silently change a D3 requirement.

Unit tests are not required for an unchanged external executable or a package
that contains no independently executable logic. Such a package records a
reasoned `Not applicable` decision and assigns the proof to contract,
integration, qualification or end-to-end verification instead.
