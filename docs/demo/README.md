<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Documentation

This directory owns audience-visible scenarios, storyboards, presenter flows,
and original demo visual assets. These documents describe what the audience
sees; they do not redefine the system architecture.

Start a colleague or stakeholder review with the
[AosEdge Demo Walkthrough and Review Guide](aosedge-demo-walkthrough.md) and the
[clickable interaction mockup](mockups/aosedge-demo-interaction-mockup-2-4.html).
The guide explains where to look, what action occurs, what the audience should
observe and what each chapter demonstrates without requiring the reader to
first study the technical specifications below.

[Staged Post-SOP Brake and Tire Health Demo Scenarios 2.0](staged-post-sop-brake-health-demo-scenarios.md)
is the accepted demo-scenario baseline. It defines the canonical
`M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` presentation lifecycle,
including manufacturing, provisioning, Brake Health evolution, the independent
Tire Health stage, and end-of-demo retirement, without authorizing
implementation.

The corresponding
[Demo Scenario Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
map Scenario 2.0 to High-Level Architecture 1.5, including lifecycle, runtime,
observability, failure and retirement flows. They do not authorize
implementation.

The [AosEdge Demo Interaction Specification 2.5](mockups/aosedge-demo-interaction-specification.md)
is the accepted presenter-interaction contract. It fixes the composed
workspace, team perspectives, current-vehicle handover, release stories,
Details, action/authority semantics, failure/recovery states and UI acceptance
cases, including the title-selected right-hand global Demo Lifecycle page and
bounded Qualification Status, fixed team context and version-only release
scrolling. Its [UI Traceability Register 1.1](mockups/aosedge-demo-ui-traceability-register.md)
links every stable interaction rule to its owner, surface and acceptance case.
The accepted clickable HTML is a derived review artifact; it may not replace
or redefine the accepted scenario, architecture, requirements or contracts.

The current I0 register is the
[Audience-Visible Interface Register and Mockup Gate](mockups/README.md). It
records the accepted surface inventory, navigation/authority split and required
visible states while implementation and presenter-Mac qualification remain
open.
