<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Requirement Packages

- Status: Draft framework
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

| Order | Package | File | Requirement / unit-test prefix | State |
| --- | --- | --- | --- | --- |
| 1 | [`CR-VEHICLE-SIM`](../component-decomposition-and-interface-register.md#cr-vehicle-sim) | [Vehicle Simulation 0.8](vehicle-simulation.md) | `VEHICLE-SIM` | D3 design-reviewed; D4-002, D4-004 and D4-005 accepted, D4-003 working direction reviewed |
| 1 | [`CR-GATEWAY`](../component-decomposition-and-interface-register.md#cr-gateway) | [Vehicle Gateway 1.1](vehicle-gateway.md) | `GATEWAY` | D3 design-reviewed; D4-002, D4-004, D4-005, D4-006 and D4-008 contracts accepted |
| 2 | [`CR-FACTORY`](../component-decomposition-and-interface-register.md#cr-factory) | [Factory Substrate 0.5](factory-substrate.md) | `FACTORY` | D3 design-reviewed 2026-08-28; runtime A/B working-storage ownership and separately packaged `CMP-KAC` factory seam accepted; implementation and qualification open |
| 2 | [`CR-KAC`](../component-decomposition-and-interface-register.md#cr-kac) | [Current-Release KUKSA Authorization Compatibility 0.12](kuksa-authorization-compatibility.md) | `KAC` | D3 design-reviewed 2026-08-28; complete D4-027.1 through D4-027.8 helper contract plus exact current-demo filesystem, SELinux and PKCS#11 boundary accepted; unmeasured CPU/RAM ceilings removed while deterministic process bounds remain; implementation open |
| 2 | [`CR-VDP`](../component-decomposition-and-interface-register.md#cr-vdp) | [Vehicle Data Platform 0.9](vehicle-data-platform.md) | `VDP` | D3 design-reviewed 2026-08-28; trusted OEM Provider integration plus native logs/no-tenant-quota boundary accepted; implementation and qualification open |
| 3 | [`CR-AOS`](../component-decomposition-and-interface-register.md#cr-aos) | [Aos Lifecycle 0.4](aos-lifecycle.md) | `AOS` | D3 review candidate; D4-011 public role/action matrix and separate `oem-delivery` authority recorded |
| 4 | [`CR-BHS`](../component-decomposition-and-interface-register.md#cr-bhs) | [Brake Health Service 0.8](brake-health-service.md) | `BHS` | D4 design accepted; ready for bounded implementation work-packet decomposition |
| 4 | [`CR-BRAKE-CLOUD`](../component-decomposition-and-interface-register.md#cr-brake-cloud) | [Brake Health Cloud Product 0.5](brake-health-cloud.md) | `BRAKE-CLOUD` | D4 design accepted; repository-creation and implementation gates open |
| 5 | [`CR-TIRE`](../component-decomposition-and-interface-register.md#cr-tire) | [Tire Health Service 0.6](tire-health-service.md) | `TIRE` | D3 review candidate; exact D4-018 in-vehicle contract prepared for review |
| 5 | [`CR-TIRE-CLOUD`](../component-decomposition-and-interface-register.md#cr-tire-cloud) | [Tire Health Cloud Product 0.3](tire-health-cloud.md) | `TIRE-CLOUD` | D3 design-reviewed; D4-019 accepted, D4-020 review candidate prepared |
| 6 | [`CR-DEMO`](../component-decomposition-and-interface-register.md#cr-demo) | [Demo Orchestration 1.1](demo-orchestration.md) | `DEMO` | D3 design-reviewed; D4-026.19 fixed team context/version-only scrolling, D4-026.18 global lifecycle workspace, D4-026.17 workspace ownership and D4-021.2/.3 resource-scoped operation registry revalidated; implementation open |
| 6 | [`CR-CROSS`](../component-decomposition-and-interface-register.md#cr-cross) | [Cross-Cutting Security and Operations 0.4](cross-cutting.md) | `CROSS` | D3 design-reviewed 2026-08-28; KAC, trusted Provider and D4-010.3 publication boundaries accepted; implementation and qualification open |
| 6 | [`CR-E2E`](../component-decomposition-and-interface-register.md#cr-e2e) | [End-to-End Acceptance 0.8](end-to-end-acceptance.md) | `E2E` | D3 design-reviewed 2026-08-27; complete D4-026.1–.20 presentation, qualification and composed-workspace design accepted; implementation and live qualification open |

The files listed above are created only when work begins on the corresponding
package. Their absence therefore means “not started,” not a broken link.

`D3 design-reviewed` means that the component boundary, requirement
obligations, interface ownership, verification levels and stable unit-test
obligations are accepted as input to D4. It does not mean that target behavior
is implemented, qualified or authorized for deployment; each package keeps
those states and open gates explicit.

Shared D4 questions are consolidated in the
[D4 Interface and Qualification Decision Register](../d4-decision-register.md).
Package `Open D4 Gates` and `Open Issues` sections remain the requirement-owner
source, while one `D4-*` ID controls each cross-package decision.

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
