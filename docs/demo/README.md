<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo scenarios and presentation

The live **AosEdge Platform - SDV Lab** demonstrates a modular, orchestrated
and updatable vehicle software foundation. Brake and Tire are illustrative QM
services, not production diagnostic algorithms or vehicle-control functions.

For the current experience, start with the
[root README](../../README.md), [Setup guide](../getting-started/installed-preview-cloud-first-use.md)
and [operator workflow](../operations/current-demo-workflow.md).
Presenter, CARLA and native Driving Control run as separate applications.

## Design references for contributors

- [Staged Scenarios 2.3](staged-post-sop-brake-health-demo-scenarios.md).
- [Architecture Flows 2.4](../architecture/demo-scenario-architecture-flows.md).
- [Interaction Specification 2.7](mockups/aosedge-demo-interaction-specification.md),
  including the [installed Test interaction profile](mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
- [UI traceability](mockups/aosedge-demo-ui-traceability-register.md).
- [Interface register](mockups/README.md).

The accepted scenario/interaction documents contain expanded two-vehicle and
two-provider obligations, explicitly separated from the installed Test and
one-associated-SP scope. A Production Cloud connection is not
the same as promoting a Test to the separate Production vehicle role.

The interface register and interaction specification are maintained contracts.
Standalone HTML prototypes and their tests have been retired to Git history;
the current implementation and tests belong to Presenter and Demo Control.

## Name and scope

Use **AosEdge Platform - SDV Lab** for the overall demonstration and new
presentation/video materials, not only for its Brake/Tire examples. This naming
rule does not rename repositories, packages, Cloud objects or application titles.
