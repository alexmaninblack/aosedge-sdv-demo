<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current Design and Delivery Roadmap

- Status: Working gate map
- Updated: 2026-08-18
- Architecture baseline under review: High-Level Architecture 1.1
- Cloud or Unit mutation authorized: no

## Purpose

This roadmap identifies the current design baseline and the order in which the
demonstration may move from architecture into implementation. It replaces the
obsolete R6.1 plan that proposed a separate `vehicle-data-integration`
component, a generic component runtime, and a `G4`-to-`G0` reset on retained
Unit identities.

The current target uses:

- one provider-specific empty-slot runtime in the OEM Demo Factory Image;
- one independently versioned Vehicle Data Platform Capability FOTA family;
- two peer OEM functional services with independent SOTA lifecycles;
- fresh Validation and Demonstration Unit identities per demo run;
- controlled retirement and disposable-overlay replacement for the normal
  next-run reset.

## Completed Engineering Foundations

The following achievements are retained as engineering evidence. They do not
by themselves prove the final manufacturing-to-retirement demonstration:

1. native CARLA and Unreal Engine operation on Apple Silicon;
2. Vehicle Gateway control, VSS normalization, TLS VISS 3.1 read/subscription,
   and the Engineering Telematics Dashboard;
3. deterministic emergency-braking scenario, manual takeover, safe stop and
   actor cleanup;
4. official AArch64 AosVM boot under QEMU/HVF;
5. single-Main-Node provisioning, persistent identity, DNS mobility and
   lifecycle safety tooling;
6. live CARLA/VISS-to-KUKSA provider qualification evidence;
7. provider-specific empty-slot runtime, isolated store and SELinux evidence
   in local rootfs candidate `.11`;
8. immutable local provider `0.2.0` evidence;
9. repository ownership split, workspace contract and post-cleanup acceptance.

Exact retained versions and limitations remain recorded in the
[current accepted engineering baseline](../qualification/current-baseline.md).

## Current Documentation Baseline

The following documents form one ordered design chain:

1. [High-Level Architecture 1.1](../architecture/high-level-architecture.md)
   owns boundaries, authorities and invariants.
2. [Demo Scenario 1.1](../demo/staged-post-sop-brake-health-demo-scenarios.md)
   owns the audience-visible stage sequence.
3. [Architecture Flows 1.0](../architecture/demo-scenario-architecture-flows.md)
   owns lifecycle, runtime, observability and failure flows.
4. [System Requirements and Traceability 0.1](../requirements/system-requirements-and-traceability.md)
   owns `SYS-*` obligations and coverage of all twenty gaps.
5. [Component Decomposition and Interface Register 0.1](../requirements/component-decomposition-and-interface-register.md)
   owns component/interface IDs and provisional requirement-package
   allocation.

A downstream document may not silently redefine an upstream decision.

## Active Design Gates

### D0 — Component register review — in review

Confirm component names, responsibilities, current/target state, interfaces,
owners, lifecycles and repository candidates. In particular, review the new
Cloud backends and dashboards, Function Team 2 service boundary, Software
Delivery Dashboard, Demo Orchestrator and logging integration.

Exit: Component Decomposition and Interface Register 0.1 is accepted or
returned with explicit corrections.

### D1 — Documentation housekeeping — completed 2026-08-18

Remove superseded active design documents and unreferenced generated files;
retain ADRs, research evidence, qualification records and operations manuals
with clear authority labels. Provide task-oriented entry paths for running
AosVM, reproducing the current demonstration, understanding the system,
modifying components and adding scenarios. Keep the current repeatable
engineering paths visibly separate from the unfinished full staged demo.
Validate indexes, internal links and source precedence.

Exit: the documentation tree presents one current design chain without broken
links or competing active plans.

### D2 — Baseline acceptance

Review HLA 1.1, Scenario 1.1, Architecture Flows 1.0, System Requirements 0.1
and the Component Register together. Resolve any remaining terminology or
boundary inconsistency before deriving component requirements.

Exit: accepted documentation versions and unresolved deferred features are
explicitly recorded.

### D3 — Component requirement packages

Create and review packages in this order:

1. `CR-VEHICLE-SIM` and `CR-GATEWAY`;
2. `CR-FACTORY` and `CR-VDP`;
3. `CR-AOS`;
4. `CR-BHS` and `CR-BRAKE-CLOUD`;
5. `CR-EVT` and `CR-EVENT-CLOUD`;
6. `CR-DEMO`, `CR-CROSS` and `CR-E2E`.

Every component requirement must cite its parent `SYS-*` requirement, relevant
`AF-*` flow, interface ID, verification method and required evidence.

Exit: every system obligation is allocated and every interface has an owner on
both sides.

### D4 — Interface contracts and acceptance tests

Freeze the versioned VISS, KUKSA, advisory, functional-report, event-package,
AosCloud, log and dashboard contracts. Define normal, unavailable, stale,
malformed, unauthorized, offline, retry, rollback and resource-bound behavior.

Exit: tests can be written without inventing missing architecture decisions.

### D5 — Implementation plan

Build a new implementation plan from the accepted component packages. Reuse
existing qualified code and artifacts only where their exact contracts match
the accepted design. Do not revive the superseded R6.1 two-component plan.

Exit: independently reviewable implementation increments, repository changes,
build boundaries and authorization gates are defined.

## Future Implementation Workstreams

These workstreams are sequencing guidance, not authorization to implement:

| Workstream | Main outcome |
| --- | --- |
| `I1` Vehicle stimulus and Gateway | Qualify emergency-braking and low-friction stimuli; add narrowly scoped advisory handling and dashboard status. |
| `I2` Factory and Vehicle Data Platform | Freeze the clean factory image and empty slot; implement and qualify the accepted Provider v1-v3 contract. |
| `I3` Brake Health product | Build the in-vehicle service, local model, bounded offline reporting, backend and function dashboard. |
| `I4` Vehicle Stability product | Build the independent low-friction detector, bounded event upload, backend and event dashboard. |
| `I5` Software delivery experience | Build the Software Delivery Dashboard over authoritative AosCloud APIs and the manufacturing/provisioning/promotion/retirement orchestration. |
| `I6` Security and operations | Qualify least privilege, secret delivery, operational logs, ELK route, retention and redaction. |
| `I7` End-to-end release proof | Execute `M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> R0` on Validation and Demonstration Units with retained evidence. |

Each workstream requires the relevant component requirements and acceptance
tests before code or deployment work begins.

## Deferred Platform Capabilities

- Native AosCloud rejection of a SOTA request whose required Vehicle Data
  Platform Capability version is absent or incompatible remains blocked on an
  implementing platform release. No project-side admission controller will be
  built as a substitute.
- The Aos-to-KUKSA Authorization Adapter remains explicit production
  hardening. Prototype path-scoped tokens are temporary demo fixtures and must
  not be confused with the target security architecture.
- Production driver HMI, third-party Service Providers, Fleet Operators, a
  production fleet, and production vehicle-network/hardware selection remain
  outside the current demo.

## Current Stop Point

Documentation housekeeping gate D1 is complete. The current boundary is D0
component-register review followed by D2 joint baseline acceptance. No new
repository, component code, build, signature, Cloud upload, assignment,
approval, VM restart, provisioning, deprovisioning or Unit mutation is
authorized by this roadmap.
