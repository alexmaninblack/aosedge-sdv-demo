<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# SDV Lab product and component map

SDV Lab combines a simulated vehicle with real AosEdge software delivery and
runtime components. It demonstrates platform capability; Brake and Tire are
illustrative QM advisory services, not production diagnostics or vehicle control.

The **Factory image** is the prepared, unprovisioned Linux/AosEdge base used
to create the **ARM64 virtual controller**. VDP and the Brake/Tire services are
delivered afterward. A **Builder** is a separate build VM used to produce that
image, not a second controller in the demo. The
[README overview diagram](../../README.md#how-the-lab-fits-together) shows these roles.

## What runs where

| Part | Location | Role |
| --- | --- | --- |
| CARLA and Vehicle Gateway | macOS | Simulated vehicle motion/measurements, driving controls and VISS transport |
| AosCore, KUKSA and vehicle platform | ARM64 virtual controller (QEMU VM) | Real platform runtime, identity, data contract and software installation |
| Brake and Tire services | Separate containers in that controller | Independent local analytics and typed advisory, using authorized KUKSA data |
| Brake and Tire backends | Separate Docker containers on macOS in this lab | Receive products, retain history and answer Presenter queries |
| Aos Cloud | Remote Cloud; intended Production or Staging environment | Real provisioning, software delivery and authoritative Unit/software observations |
| Presenter and Demo Control | macOS | One operator workflow across these owners; not a replacement Cloud or service runtime |

The virtual controller represents a vehicle computer, not a simulation of the
Aos runtime. Real vehicle networks would replace the CARLA-specific input side.
The lab does not prove production vehicle safety certification.

## Two update lifecycles

The vehicle baseline integrates the platform before SOP. The Vehicle Data
Platform component later evolves through OEM FOTA, gated by Safe Stop. Brake
and Tire evolve independently through SOTA, within the platform contract.
Neither advisory service controls braking or steering. Local operation and
backend delivery remain distinct when the external network is unavailable.

## Source ownership

The launcher prepares the integration checkout and exact component source roles
for developer builds; there is no requirement to manually assemble this hierarchy.
The links below open each component's maintained documentation on `main`.
They explain ownership and component development, not the source identity of
an already built package. Exact build inputs remain separately pinned.

| Product area | Repository and current documentation | Owner responsibility |
| --- | --- | --- |
| Integration | [This repository](../../README.md) | Presenter, Setup, Demo Control, contracts, release locks and qualification |
| Vehicle platform | [aos-vehicle-platform](https://github.com/alexmaninblack/aos-vehicle-platform/blob/main/README.md) | Factory integration, VDP and OEM platform lifecycle |
| Brake | [brake-health-service](https://github.com/alexmaninblack/brake-health-service/blob/main/README.md) and [brake-health-cloud](https://github.com/alexmaninblack/brake-health-cloud/blob/main/README.md) | Independent in-vehicle service and its backend |
| Tire | [tire-health-service](https://github.com/alexmaninblack/tire-health-service/blob/main/README.md) and [tire-health-cloud](https://github.com/alexmaninblack/tire-health-cloud/blob/main/README.md) | Independent in-vehicle service and its backend |
| Simulation gateway | [carla-ego-runtime](https://github.com/alexmaninblack/carla-ego-runtime/blob/main/README.md) | CARLA control, VISS and native Driving Control/Telemetry integration |
| Simulator dependency | [CARLA fork](https://github.com/alexmaninblack/carla/blob/eb09b82464076596ee47e42b3f5f9b48f9ff5b30/README.md) | Maintained simulator and content compatibility; Unreal source has separate restricted access |

The two functions can belong to independent teams while sharing the one
associated SP account selected for this first-demo topology. Accounts,
repository ownership and service identities are different concepts.

Component code stays with its owner. The [workspace manifest](../../workspace/repositories.json)
records source references; release definitions and producer plans distinguish
component code from packaging tools. Documentation-only commits do not
silently advance a built artifact's source pin.
The [selected release](../getting-started/release-status.md) and current developer
build plan identify exact artifact/producer sources; current documentation
does not change those immutable selections.

## Read deeper when needed

- [Implemented architecture](current-implementation.md)
- [High-Level Architecture 1.8](high-level-architecture.md)
- [Interface contracts](../../contracts/README.md)
- [Developer build](../getting-started/reproduce-demo.md)
- [Contributing](../../CONTRIBUTING.md)

The initial operator/developer guides and this map work from the root repository
alone. Use the component references above when changing an individual component.
