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
| 1 | [`CR-VEHICLE-SIM`](../component-decomposition-and-interface-register.md#cr-vehicle-sim) | [Vehicle Simulation 0.4](vehicle-simulation.md) | `VEHICLE-SIM` | D3 design-reviewed |
| 1 | [`CR-GATEWAY`](../component-decomposition-and-interface-register.md#cr-gateway) | [Vehicle Gateway 0.6](vehicle-gateway.md) | `GATEWAY` | D3 design-reviewed |
| 2 | [`CR-FACTORY`](../component-decomposition-and-interface-register.md#cr-factory) | [Factory Substrate 0.2](factory-substrate.md) | `FACTORY` | D3 design-reviewed |
| 2 | [`CR-VDP`](../component-decomposition-and-interface-register.md#cr-vdp) | [Vehicle Data Platform 0.3](vehicle-data-platform.md) | `VDP` | D3 design-reviewed |
| 3 | [`CR-AOS`](../component-decomposition-and-interface-register.md#cr-aos) | `aos-lifecycle.md` | `AOS` | Not started |
| 4 | [`CR-BHS`](../component-decomposition-and-interface-register.md#cr-bhs) | `brake-health-service.md` | `BHS` | Not started |
| 4 | [`CR-BRAKE-CLOUD`](../component-decomposition-and-interface-register.md#cr-brake-cloud) | `brake-health-cloud.md` | `BRAKE-CLOUD` | Not started |
| 5 | [`CR-TIRE`](../component-decomposition-and-interface-register.md#cr-tire) | `tire-health-service.md` | `TIRE` | Not started |
| 5 | [`CR-TIRE-CLOUD`](../component-decomposition-and-interface-register.md#cr-tire-cloud) | `tire-health-cloud.md` | `TIRE-CLOUD` | Not started |
| 6 | [`CR-DEMO`](../component-decomposition-and-interface-register.md#cr-demo) | `demo-orchestration.md` | `DEMO` | Not started |
| 6 | [`CR-CROSS`](../component-decomposition-and-interface-register.md#cr-cross) | `cross-cutting.md` | `CROSS` | Not started |
| 6 | [`CR-E2E`](../component-decomposition-and-interface-register.md#cr-e2e) | `end-to-end-acceptance.md` | `E2E` | Not started |

The files listed above are created only when work begins on the corresponding
package. Their absence therefore means “not started,” not a broken link.

`D3 design-reviewed` means that the component boundary, requirement
obligations, interface ownership, verification levels and stable unit-test
obligations are accepted as input to D4. It does not mean that target behavior
is implemented, qualified or authorized for deployment; each package keeps
those states and open gates explicit.

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
