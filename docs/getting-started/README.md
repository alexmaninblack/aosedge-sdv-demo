<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Getting Started

Use this page as the entry point to the AosEdge SDV demonstration. Choose the
path that matches the job you want to do; the documents are not intended to be
read in directory order.

## I Want to Run AosVM on an Apple Silicon Mac

Follow [Run AosVM on an Apple Silicon Mac](../operations/aosvm-apple-silicon.md).
It is the canonical standalone guide for installing, booting, operating and,
when explicitly authorized, provisioning one persistent AosVM Main Node.

CARLA, Unreal Engine and the functional-service repositories are not required
for this path.

## I Want to Reproduce the Demonstration

Start with the [reproduction guide and readiness matrix](reproduce-demo.md).
It separates the already repeatable engineering demonstration from the full
staged SDV story that is still under design and implementation. This prevents
a newcomer from interpreting a target architecture as a finished launcher.

## I Want to Understand the System

Read the accepted design chain in this order:

1. [High-Level Architecture 1.5](../architecture/high-level-architecture.md)
2. [Demo Scenario 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md)
3. [Demo Scenario Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
4. [System Requirements and Traceability 2.0](../requirements/system-requirements-and-traceability.md)
5. [Component Decomposition and Interface Register 2.0](../requirements/component-decomposition-and-interface-register.md)

The [current baseline](../qualification/current-baseline.md) states which
parts have accepted implementation evidence and which remain targets.

## I Want to Modify the Demonstration

Read the [development map](../development/README.md) before choosing a
repository. Source code stays with the component owner; this solution
repository owns cross-component contracts, orchestration, system
documentation and end-to-end evidence.

For the current single-writer branch policy, see the
[development workflow](../governance/development-workflow.md).

## I Want to Add a Demo Scenario

Follow [Add or Change a Demo Scenario](../development/add-demo-scenario.md).
The workflow starts with the audience-visible story, traces it through the
architecture and requirements, and only then allocates implementation to
component repositories.

## Safety Boundary

Reading documentation and running repository-only validation does not
authorize signing, Cloud upload, assignment, provisioning, deprovisioning,
Unit mutation, VM reset or deletion. Those operations remain explicit gates
in their relevant procedures.
