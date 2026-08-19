<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Documentation Map

This directory is the source of truth for documentation that spans the whole
AosEdge SDV demonstration. Component-specific design and usage documentation
stays with the component that owns it.

The canonical repository is `alexmaninblack/aosedge-sdv-demo`. It was renamed
from `carla-aosedge-integration` after the solution boundary was accepted in
ADR 0007. The repository name now reflects its ownership of the complete demo,
not only the CARLA-to-AosEdge transport bridge.

## Start Here

- [Choose a task](getting-started/README.md) — run AosVM, reproduce the current
  demo, understand the system, modify a component or add a scenario.
- [Reproduction guide and readiness matrix](getting-started/reproduce-demo.md)
  — what works today, required repositories and access, and what remains a
  target.

## Architecture

- [Architecture documentation index](architecture/README.md)
- [High-Level Architecture 1.4 — accepted architecture baseline](architecture/high-level-architecture.md)
  — accepted end-to-end system view with the Tire Health decision.
- [Demo Scenario Architecture Flows 1.5 — accepted architecture-flow baseline](architecture/demo-scenario-architecture-flows.md)
  — complete manufacturing, provisioning, post-SOP evolution, Function Team 2
  `T1` Tire Health stage, observability, offline, and retirement mapping.
- [Repository and component boundaries](architecture/repository-boundaries.md)
  — ownership across the participating repositories.
- [Architecture decisions](architecture/decisions/) — accepted decisions and
  their consequences.
- [Architecture diagrams](architecture/diagrams/) — accepted editable diagram
  sources and exports.

## Demo

- [Demo documentation index](demo/README.md)
- [Staged Post-SOP Brake and Tire Health Demo Scenarios 1.6](demo/staged-post-sop-brake-health-demo-scenarios.md)
  — accepted manufacturing-to-retirement audience-visible baseline.
- [Demo assets](demo/assets/) — original, license-cleared visual sources and
  exports. Storyboards and presenter materials will be added here only after
  review.

## Requirements

- [System Requirements and Traceability 0.8 — accepted system-requirements baseline](requirements/system-requirements-and-traceability.md)
  — system obligations, complete coverage of the twenty-one Architecture Flows
  gaps, verification intent, repository ownership and component allocation.
- [Component Decomposition and Interface Register 0.8 — accepted component baseline](requirements/component-decomposition-and-interface-register.md)
  — logical components, implementation state, lifecycle and repository
  boundaries, runtime and Cloud interfaces, and component-package allocation.
- [Component requirement packages and template](requirements/components/README.md)
  — ordered D3 work, human-readable component requirements, unit-test
  obligations and verification traceability.
- [Requirements documentation](requirements/README.md)

## Planning

- [Planning documentation index](planning/README.md)
- [Current design and delivery roadmap](planning/roadmap.md)
- [Repository inventory and migration plan](planning/repository-inventory-and-migration-plan.md)
  — completed workspace migration and cleanup record retained as historical
  evidence.

## Research

- [R9 Demo Foundation Research](research/demo-foundation/README.md) — completed
  read-only workstreams for the G0 runtime, AosCloud lifecycle, VM recovery,
  CARLA scenario, Brake Health model, advisory path, functional backend,
  logging, and demo dashboards.
- [Integrated research summary](research/demo-foundation/integration-summary.md)
  — cross-workstream decisions, contradictions, dependencies, risks, and the
  recommended review gates before implementation.
- [Automotive Orchestration Coverage Matrix](research/demo-foundation/automotive-orchestration-coverage-matrix.md)
  — sanitized dashboard proof catalogue derived from confidential OEM input;
  the source workbook remains outside Git.
- [Native CARLA telemetry and Function Team 2 evidence](research/demo-foundation/r10-carla-telemetry-and-function-team-2.md)
  — native vehicle state, Chaos telemetry, built-in sensors, simulator ground
  truth, explicit non-capabilities, the superseded low-friction candidate, and
  evidence constraining the accepted Tire Health design.

## Operations

- [Operations documentation index](operations/README.md)
- [Run AosVM on Apple Silicon](operations/aosvm-apple-silicon.md) — canonical
  install, lifecycle and guarded provisioning guide.

## Development

- [Development map](development/README.md) — choose the owning repository and
  trace a change through architecture, requirements and interfaces.
- [Add or change a demo scenario](development/add-demo-scenario.md)

## Qualification

- [Qualification documentation index](qualification/README.md)
- [Current accepted baseline](qualification/current-baseline.md)
- [CARLA VISS-to-KUKSA qualification](qualification/carla-viss-to-kuksa.md)
- [Exact component lock](qualification/component-lock.md)
- [Validation-set scope defect](qualification/r6-1-validation-set-scope-defect.md)
- [Repository-rename VM repair](qualification/repository-rename-vm-repair.md)
- [AOS-0 Apple Silicon qualification record](qualification/aosvm-apple-silicon-baseline.md)
- [AOS-1 single-Main-Node qualification record](qualification/aosvm-single-node-provisioning.md)

## Governance

- [Governance documentation index](governance/README.md)
- [Licensing and copyright policy](governance/licensing-and-copyright-policy.md)
- [Confidential source handling](governance/confidential-source-handling.md)
  — local-only input policy, sanitization rules, and Git safeguards.
- [Development workflow](governance/development-workflow.md) — direct-to-main
  policy for the current single-developer, single-agent phase.
- [Documentation and requirements management](governance/documentation-and-requirements-management.md)
  — human-readable traceability, stable identifiers, quality gates and the
  architecture-change cascade.

## Ownership Rule

This repository owns system-level architecture, demo experience, cross-project
planning, orchestration, operational setup, and end-to-end qualification. It
must not become the source repository for CARLA, Unreal Engine, the Vehicle
Gateway runtime, the Aos vehicle platform, or a functional SOTA service.

External reference material, private correspondence, proprietary screenshots,
credentials, VM disks, build output, and raw operational evidence remain
outside public Git. Obsolete documents are removed from the current tree;
their history remains available in Git.
