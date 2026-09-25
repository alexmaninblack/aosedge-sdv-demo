<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture Documentation

For `demo-v1.1 / Factory .39`, start with the [implemented architecture and traceability](current-implementation.md). It maps the accepted design and later amendments to source, contracts and dated proof; it does not promote untested requirements.

[High-Level Architecture 1.7](high-level-architecture.md) is the accepted
current architecture. It incorporates the accepted authorization compatibility
boundary, independent OEM Release Authority and Platform FOTA Safe Stop
boundary; High-Level Architecture 1.4 remains historical traceability only.

- [High-Level Architecture 1.7 — accepted](high-level-architecture.md)
- [Demo Scenario Architecture Flows 2.1 — accepted](demo-scenario-architecture-flows.md)
  — complete `M0 -> M1 -> G0–G4 -> T1 -> R0` mapping of Scenario 2.0 to
  High-Level Architecture 1.7, including the independent Tire Health stage.
- [Repository and component boundaries](repository-boundaries.md)
- [Demo Control — implementation design and history](demo-control.md)
  — shared CLI/UI orchestration, current Test workflow and dated status/lifecycle amendments.
- [Service identity, data and tokens using native Aos facilities — accepted](decisions/0015-use-native-aos-service-runtime-inputs.md)
  — approved Brake/Tire protocol and file placement without new SM code;
  implementation status is tracked in the delivery plan.
- [Architecture decisions](decisions/)
- [Diagram sources and exports](diagrams/)
