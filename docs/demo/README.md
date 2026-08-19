<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Documentation

This directory owns audience-visible scenarios, storyboards, presenter flows,
and original demo visual assets. These documents describe what the audience
sees; they do not redefine the system architecture.

[Staged Post-SOP Brake and Tire Health Demo Scenarios 1.5](staged-post-sop-brake-health-demo-scenarios.md)
is the accepted demo-scenario baseline. It defines the canonical
`M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` presentation lifecycle,
including manufacturing, provisioning, Brake Health evolution, the independent
Tire Health stage, and end-of-demo retirement, without authorizing
implementation.

The corresponding
[Demo Scenario Architecture Flows 1.4](../architecture/demo-scenario-architecture-flows.md)
map Scenario 1.5 to High-Level Architecture 1.4, including lifecycle, runtime,
observability, failure and retirement flows. They do not authorize
implementation.

No storyboard or presenter flow is accepted yet. Those are separate next
steps after architecture mapping.
