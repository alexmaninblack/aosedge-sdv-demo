<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# SDV Lab product and component map

SDV Lab combines a simulated vehicle with real AosEdge software delivery and
runtime components. It demonstrates platform capability; Brake and Tire are
illustrative QM advisory services, not production diagnostics or vehicle control.

## What runs where

| Part | Location | Role |
| --- | --- | --- |
| CARLA and Vehicle Gateway | macOS | Simulated vehicle motion/measurements, driving controls and VISS transport |
| AosCore, KUKSA and vehicle platform | ARM64 AosVM controller | Real platform runtime, identity, data contract and software installation |
| Brake and Tire services | Separate containers in that controller | Independent local analytics and typed advisory, using authorized KUKSA data |
| Brake and Tire backends | Separate Docker containers on macOS in this lab | Receive products, retain history and answer Presenter queries |
| Aos Cloud staging | Remote Cloud | Real provisioning, software delivery and authoritative Unit/software observations |
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

You clone the integration repository once. The developer build prepares exact
source roles; there is no requirement to manually assemble this hierarchy.
Links below select the existing workspace source pins, not floating branches.
They are component references, not promises that each README is an installer guide.

| Product area | Repository and pinned reference | Owner responsibility |
| --- | --- | --- |
| Integration | [This repository](../../README.md) | Presenter, Setup, Demo Control, contracts, release locks and qualification |
| Vehicle platform | [aos-vehicle-platform](https://github.com/alexmaninblack/aos-vehicle-platform/blob/92a2138813983cb1c029fd3e61bd90b68241af63/README.md) | Factory integration, VDP and OEM platform lifecycle |
| Brake | [brake-health-service](https://github.com/alexmaninblack/brake-health-service/blob/5aa652fda603e7621043961331e58236b19204e9/README.md) and [brake-health-cloud](https://github.com/alexmaninblack/brake-health-cloud/blob/7c64adf7b3d99535ecc7c8cbe468bc527cbcdc12/README.md) | Independent in-vehicle service and its backend |
| Tire | [tire-health-service](https://github.com/alexmaninblack/tire-health-service/blob/f0a0f6edadb51aa338775d157aa3bde28f5b76f4/README.md) and [tire-health-cloud](https://github.com/alexmaninblack/tire-health-cloud/blob/ea2d6deec9b704cb866d362eaefc9d87356ddeb5/README.md) | Independent in-vehicle service and its backend |
| Simulation gateway | [carla-ego-runtime](https://github.com/alexmaninblack/carla-ego-runtime/blob/2e3d1164d491dac25e212f59315057deca0bf3d8/README.md) | CARLA control, VISS and native Driving Control/Telemetry integration |
| Simulator dependency | [CARLA fork](https://github.com/alexmaninblack/carla/blob/eb09b82464076596ee47e42b3f5f9b48f9ff5b30/README.md) | Maintained simulator and content compatibility; Unreal source has separate restricted access |

The two functions can belong to independent teams while sharing the one
associated SP account selected for this first-demo topology. Accounts,
repository ownership and service identities are different concepts.

Component code stays with its owner. The [workspace manifest](../../workspace/repositories.json)
records source references; release definitions and producer plans distinguish
component code from packaging tools. Documentation-only commits do not
silently advance a built artifact's source pin.

## Read deeper when needed

- [Implemented architecture and evidence](current-implementation.md)
- [High-Level Architecture 1.8](high-level-architecture.md)
- [Interface contracts](../../contracts/README.md)
- [Developer build](../getting-started/reproduce-demo.md)
- [Contributing](../../CONTRIBUTING.md)

Specialist design documents may use the maintainer's sibling-workspace links.
The initial operator/developer routes and this map work from the root repository
alone. Historical research and dated tests remain evidence, not setup steps.
