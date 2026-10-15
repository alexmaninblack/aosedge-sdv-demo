<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Documentation map

Start with the [root README](../README.md): one downloadable launcher offers
installation, developer builds and specialist build-tool preparation. No
engineering history or sibling checkout is needed to choose a route.

## Use, build or change the lab

| Goal | Current guide |
| --- | --- |
| Install the selected demo | [Release/access selection](getting-started/release-status.md), then [Setup and Cloud access](getting-started/installed-preview-cloud-first-use.md) |
| Operate the vehicle demonstration | [Current operator sequence](operations/current-demo-workflow.md) |
| Build project components and the installer | [Developer build reference](getting-started/reproduce-demo.md) and [preparation/recovery reference](getting-started/macos-developer-tools.md) |
| Prepare tools to rebuild the controller image or simulator | [Specialist preparation and remaining full-source gates](getting-started/full-source-build.md) |
| Understand the real and simulated parts | [Component map](architecture/product-map.md), [implemented architecture](architecture/current-implementation.md) |
| Change a component or add a scenario | [Contributing](../CONTRIBUTING.md), [development map](development/README.md), [scenario changes](development/add-demo-scenario.md) |
| Resolve a failure | [Troubleshooting](getting-started/troubleshooting.md), [launcher recovery](getting-started/unified-macos-launcher.md) |

The **Factory image** is the clean Linux/AosEdge base for the **ARM64 virtual
controller**. Its Linux **Builder** is a separate build VM. Operator and normal
developer routes reuse the prepared controller image and CARLA simulator.

## Current release and actual proof

The [launcher catalog](../workspace/launcher-catalog.json) selects option A.
The [current baseline](qualification/current-baseline.md) separates selected
media, exact runtime/native/public-consumer evidence and remaining exclusions.
Use the [qualification index](qualification/README.md), not an old kit number
or a report's historical next-step instruction.

The operator media is an Apple Development engineering preview, not a
notarized general-public release. Aos Cloud Production and Staging are separate
environments; neither is the same concept as the Test/Production vehicle role.

## Accepted design and contracts

These are normative obligations, not claims that every case is implemented:

1. [High-Level Architecture 1.8](architecture/high-level-architecture.md).
2. [Demo Scenarios 2.1](demo/staged-post-sop-brake-health-demo-scenarios.md).
3. [Architecture Flows 2.2](architecture/demo-scenario-architecture-flows.md).
4. [System Requirements 2.2](requirements/system-requirements-and-traceability.md).
5. [Component and Interface Register 2.2](requirements/component-decomposition-and-interface-register.md).
6. [Component requirements](requirements/components/README.md) and
   [D4 decision register](requirements/d4-decision-register.md).
7. [Executable contracts](../contracts/README.md) and
   [implemented protocol/amendment status](../contracts/implementation-status.md).

Later accepted amendments take precedence over original expanded two-vehicle,
two-provider and lifecycle examples. Stable requirement IDs remain in their
canonical documents. [Architecture decisions](architecture/decisions/README.md)
retain current rationale; explicitly superseded decisions are Git references.

## Navigation by responsibility

- [Getting started](getting-started/README.md)
- [Architecture](architecture/README.md), [editable diagrams](architecture/diagrams/README.md)
- [Demo scenarios and interaction contracts](demo/README.md)
- [Automotive orchestration coverage](research/demo-foundation/automotive-orchestration-coverage-matrix.md): accepted coverage input, not blanket implementation proof
- [Requirements](requirements/README.md)
- [Operations](operations/README.md)
- [Development and release tooling](development/README.md)
- [Remaining work and reproduction gates](planning/README.md)
- [Governance](governance/README.md)

## Documentation maintenance

[Review and retirement](governance/documentation-and-requirements-management.md)
separates current instructions, normative obligations and evidence.
The [15 October documentation review](qualification/documentation-review-2026-10-15.md)
records this complete README-link audit and the
[retirement inventory](../workspace/checkpoints/documentation-retirement-20261015.json).
Obsolete instructions, completed execution packets and superseded reports have
been removed from the working tree; original evidence is recoverable through
immutable Git links, not a second active archive directory.
