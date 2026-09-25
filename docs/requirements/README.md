<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Requirements Documentation

The [current implementation matrix](../architecture/current-implementation.md) and [protocol audit](../../contracts/implementation-status.md) cover the implemented demo-v1.1 / Factory .39. Normative requirements remain obligations, not assertions that every qualification case has passed.

- [System Requirements and Traceability 2.1 — accepted](system-requirements-and-traceability.md)
  — system obligations, coverage of all Architecture Flows gaps, verification
  intent, repository ownership and allocation to the thirteen component requirement
  packages.
- [Component Decomposition and Interface Register 2.1 — accepted](component-decomposition-and-interface-register.md)
  — stable logical-component and interface identifiers, current/target state,
  lifecycle ownership, implemented repositories and requirement allocation.
- [Component requirement packages](components/README.md)
  — D3 package order, stable component-requirement and unit-test-obligation
  identifiers, reusable package template and the D3/D4 verification boundary.
- [D4 Interface and Qualification Decision Register 1.0](d4-decision-register.md)
  — consolidated shared contract, API, security, hosting, resilience and
  acceptance decisions with stable IDs, owners, order and closure rules;
  includes accepted Factory and Vehicle Hardware Capability decisions.
- [Vehicle Hardware Capability Profile 1.0.0](../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.v1.json)
  and its [schema](../../contracts/vehicle-hardware-profile/vehicle-hardware-capability-profile.schema.json)
  — digest-addressed CARLA physical-capability and Simulator–Gateway accounting
  contract accepted by `D4-002`.
