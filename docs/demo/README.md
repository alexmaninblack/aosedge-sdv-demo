<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Documentation

This directory owns audience-visible scenarios, storyboards, presenter flows,
and original demo visual assets. These documents describe what the audience
sees; they do not redefine the system architecture.

Accepted audience-facing name: **AosEdge Platform - SDV Lab**. See the
[naming decision](demo-name.md) for spelling and scope, including the planned
demo video. This decision does not itself rename the running UI.

For the **current implemented Test-only Studio**, start with the
[operator workflow](../operations/current-demo-workflow.md),
[current implementation](../architecture/current-implementation.md) and
[UI-STUDIO-026](mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
The [20 September UI timing and repair report](../qualification/presenter-ui-timing-e2e-2026-09-20.md)
records the observed version/offline cycle, Presenter corrections and required
engineering preflight for compiled Brake V1/V2/V3 and Tire V1 products. UI
Prepare consumes those products; it does not build uncommitted service source.
The earlier two-vehicle walkthrough below is historical narrative, not today's
operator procedure or authorization to alter Production.

Start a colleague or stakeholder review with the
[AosEdge Demo Walkthrough and Review Guide](aosedge-demo-walkthrough.md) and the
[retained review mockup](mockups/aosedge-demo-interaction-mockup-2-10.html).
The mockup simulates facts and predates later accepted amendments; use the
real Presenter for current status and operator behavior.
The guide explains where to look, what action occurs, what the audience should
observe and what each chapter demonstrates without requiring the reader to
first study the technical specifications below.

The accepted [Native Demo Desktop Plan](../planning/active/native-demo-desktop.md)
keeps this composition while combining control/telemetry, retaining CARLA as a
separate window and adding one-click startup. The
[source checkpoint](../qualification/demo-v1.1-return-point.md) separates
implemented Test/advisory behavior from broader Production qualification.

[Staged Post-SOP Brake and Tire Health Demo Scenarios 2.0](staged-post-sop-brake-health-demo-scenarios.md)
is the accepted demo-scenario baseline. It defines the canonical
`M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` presentation lifecycle,
including manufacturing, provisioning, Brake Health evolution, the independent
Tire Health stage, and end-of-demo retirement, without authorizing
implementation.

The corresponding
[Demo Scenario Architecture Flows 2.1](../architecture/demo-scenario-architecture-flows.md)
map Scenario 2.0 to High-Level Architecture 1.7, including lifecycle, runtime,
observability, failure and retirement flows. They do not authorize
implementation.

The [AosEdge Demo Interaction Specification 2.6](mockups/aosedge-demo-interaction-specification.md)
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
visible states. Later implemented amendments and the remaining presenter/host
recovery qualification boundaries are identified at the top of that register.
