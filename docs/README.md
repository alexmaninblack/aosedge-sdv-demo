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

## Architecture

- [High-Level Architecture 1.0](architecture/high-level-architecture.md) —
  normative end-to-end system view.
- [Post-SOP feature-extension architecture](architecture/post-sop-sdv-feature-extension-architecture.md)
  — lifecycle and platform-extension model.
- [Repository and component boundaries](architecture/repository-boundaries.md)
  — ownership across the participating repositories.
- [Architecture decisions](architecture/decisions/) — accepted decisions and
  their consequences.
- [Architecture diagrams](architecture/diagrams/) — accepted editable diagram
  sources and exports.

## Demo

- [Emergency Braking and Brake Health scenario](demo/post-sop-emergency-braking-demo-scenario.md)
  — the existing scenario baseline, to be realigned with HLA 1.0 in the next
  dedicated scenario iteration.
- [Demo assets](demo/assets/) — original, license-cleared visual sources and
  exports. Storyboards and presenter materials will be added here only after
  review.

## Planning

- [Roadmap and gates](planning/roadmap.md)
- [R6.1 vehicle-data integration component plan](planning/r6-1-integration-component-plan.md)

## Operations

- [Run AosVM on Apple Silicon](operations/aosvm-arm64-macos.md)
- [Provision one Main Node](operations/single-node-provisioning.md)
- [Colleague setup on macOS](operations/macos-colleague-setup.md)

## Qualification

- [Current accepted baseline](qualification/current-baseline.md)
- [CARLA VISS-to-KUKSA qualification](qualification/carla-viss-to-kuksa.md)
- [Exact component lock](qualification/component-lock.md)
- [Validation-set scope defect](qualification/r6-1-validation-set-scope-defect.md)

## Governance

- [Licensing and copyright policy](governance/licensing-and-copyright-policy.md)

## Ownership Rule

This repository owns system-level architecture, demo experience, cross-project
planning, orchestration, operational setup, and end-to-end qualification. It
must not become the source repository for CARLA, Unreal Engine, the Vehicle
Gateway runtime, the Aos vehicle platform, or a functional SOTA service.

External reference material, private correspondence, proprietary screenshots,
credentials, VM disks, build output, and raw operational evidence remain
outside public Git. Obsolete documents are removed from the current tree;
their history remains available in Git.
