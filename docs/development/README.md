<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Development Map

This page helps a contributor decide where a change belongs before editing
code. The architectural component, lifecycle owner and repository boundary
must agree.

## Choose the Change Boundary

| If the change concerns | Primary repository | Lifecycle |
| --- | --- | --- |
| CARLA physics, maps, native simulator build | `CarlaSim` | vehicle simulation baseline |
| Vehicle control, CARLA sampling, VSS/VISS, engineering dashboard or deterministic scenario | `carla-ego-runtime` | Vehicle Gateway/demo tooling |
| Factory-image integration, provider runtime, KUKSA platform contract or Vehicle Data Platform Capability | `aos-vehicle-platform` | Platform Team / FOTA |
| Brake Health in-vehicle analytics | `brake-health-service` | Function Team 1 / SOTA |
| Tire Health condition estimation, bounded reporting and inspection advisory | future `tire-health-service` | Function Team 2 / independent SOTA |
| Software Delivery Dashboard, demo orchestration, cross-component contract or end-to-end qualification | `aosedge-sdv-demo` | solution integration |
| Unreal Engine compatibility required by CARLA | restricted Unreal fork | maintained Apple Silicon dependency branch |

Backends and function dashboards are separate from their in-vehicle SOTA
containers. Their final repository allocation is intentionally unresolved in
the current Component Register; do not place them in this repository merely
because it is convenient.

## Read Before Changing an Interface

1. Locate the component and interface ID in the
   [Component Register](../requirements/component-decomposition-and-interface-register.md).
2. Trace its parent obligations in
   [System Requirements](../requirements/system-requirements-and-traceability.md).
3. Check the relevant runtime and lifecycle sequence in
   [Architecture Flows](../architecture/demo-scenario-architecture-flows.md).
4. Confirm that the change still fits
   [High-Level Architecture 1.2](../architecture/high-level-architecture.md)
   and [Demo Scenario 1.2](../demo/staged-post-sop-brake-health-demo-scenarios.md).

If the proposed behavior does not fit, change and review the owning design
document first. A downstream implementation must not silently redefine an
upstream architectural decision.

## Implementation Rule

Keep source, tests and component-specific usage documentation in the owning
repository. Update this solution repository when a change affects:

- a cross-component contract or component state;
- the accepted workspace revision;
- the audience-visible demo flow;
- orchestration or operator instructions;
- qualification evidence or a known limitation.

The current branch policy and commit expectations are defined in the
[development workflow](../governance/development-workflow.md).

## Validation Rule

Validate at the narrowest useful boundary first, then at each affected
interface, and finally through the relevant end-to-end scenario. Record exact
versions and sanitized evidence. Never commit secrets, provisioned overlays,
raw Cloud logs, customer material or machine-specific absolute paths.

For a new audience-visible behavior, use
[Add or Change a Demo Scenario](add-demo-scenario.md).

Before commit, run the deterministic documentation and repository gates:

```sh
./scripts/docs-check
./scripts/qualify-repository-boundaries
```

The documentation gate checks navigation, anchors, stable identifiers,
canonical metadata, readable package traceability and stale artifacts. The
repository gate also checks workspace and confidentiality boundaries.
