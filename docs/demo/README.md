<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo scenarios and presentation

The live **AosEdge Platform - SDV Lab** demonstrates a modular, orchestrated
and updatable vehicle software foundation. Brake and Tire are illustrative QM
services, not production diagnostic algorithms or vehicle-control functions.

For the current experience, start with the
[root README](../../README.md), [Setup guide](../getting-started/installed-preview-cloud-first-use.md)
and [operator workflow](../operations/current-demo-workflow.md).
Presenter, CARLA and native Driving Control are actual running components;
an HTML mockup is not evidence of a live installation.

## Accepted design

- [Demo name and scope](demo-name.md).
- [Staged Scenarios 2.1](staged-post-sop-brake-health-demo-scenarios.md).
- [Architecture Flows 2.2](../architecture/demo-scenario-architecture-flows.md).
- [Interaction Specification 2.6](mockups/aosedge-demo-interaction-specification.md),
  including the accepted [Test-only Studio amendment](mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
- [UI traceability](mockups/aosedge-demo-ui-traceability-register.md).
- [Interface register](mockups/README.md).
- [Original visual assets](assets/README.md).

The accepted scenario/interaction documents contain expanded two-vehicle and
two-provider obligations. Later Test-only and one-associated-SP amendments
define the implemented first-demo scope. Neither a Production Cloud connection
nor a passed Test run proves Production vehicle-role promotion.

Older versioned HTML mockups remain only where active regression tests or
accepted design references require them. They are historical test/review
fixtures, not alternative operator instructions. The obsolete two-vehicle
walkthrough has been removed; the current workflow is the sole operation guide.
