<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current Design and Delivery Roadmap

- Status: Working gate map
- Updated: 2026-08-19
- Accepted architecture baseline: High-Level Architecture 1.3
- Cloud or Unit mutation authorized: no

## Purpose

This roadmap identifies the current design baseline and the order in which the
demonstration may move from architecture into implementation. It replaces the
obsolete R6.1 plan that proposed a separate `vehicle-data-integration`
component, a generic component runtime, and a `G4`-to-`G0` reset on retained
Unit identities.

The current target uses:

- one OEM Factory Baseline Assembly that reproducibly produces the immutable
  OEM Demo Factory Image artifact;
- one provider-specific empty-slot runtime in the OEM Demo Factory Image;
- one independently versioned Vehicle Data Platform Component FOTA family;
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

1. [High-Level Architecture 1.3](../architecture/high-level-architecture.md)
   owns boundaries, authorities and invariants.
2. [Demo Scenario 1.4](../demo/staged-post-sop-brake-health-demo-scenarios.md)
   owns the audience-visible stage sequence.
3. [Architecture Flows 1.3](../architecture/demo-scenario-architecture-flows.md)
   owns lifecycle, runtime, observability and failure flows.
4. [System Requirements and Traceability 0.6](../requirements/system-requirements-and-traceability.md)
   owns `SYS-*` obligations and coverage of all twenty-one gaps.
5. [Component Decomposition and Interface Register 0.6](../requirements/component-decomposition-and-interface-register.md)
   owns component/interface IDs and provisional requirement-package
   allocation.

A downstream document may not silently redefine an upstream decision.

## Active Design Gates

### D0 — Component register review — completed 2026-08-18

Component names, responsibilities, current/target state, interfaces, owners,
lifecycles and repository candidates are accepted in Component Decomposition
and Interface Register 0.2. This includes the Vehicle Gateway and Tire Health
boundaries, one backend-plus-dashboard Cloud repository per Function Team,
stateless Software Delivery Dashboard and Demo Orchestrator boundaries, native
AosEdge logging ownership, and the ADR 0010 allocation of the thin Credential
Broker and provider platform-identity integration to `CMP-VDP`, while native
Aos IAM retains SOTA instance identity and permission ownership.

Exit evidence: Component Decomposition and Interface Register 0.3 closed D0;
the accepted register has since advanced to 0.4 through controlled downstream
refinement.

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

The completed gate also establishes stable identifier anchors,
human-readable package summaries, direct traceability links, the documented
architecture-change cascade, and the deterministic `docs-check` commit/CI
gate.

### D2 — Baseline acceptance — completed 2026-08-18

HLA 1.3, Scenario 1.4, Architecture Flows 1.3, System Requirements 0.6 and the
Component Register 0.6 form one consistent design baseline. Scenario 1.4 and
Flows 1.3 retain the accepted drive-mode/world-context transition contract;
Requirements and Register 0.4 allocate it to Vehicle Simulation, Vehicle
Gateway and the Engineering Dashboard. HLA 1.3 also corrects the native Aos
IAM credential authority and Factory/VDP security seam. Deferred platform capabilities and
open qualification or implementation gates remain explicit and are not
presented as current behavior.

Exit evidence: each baseline document records its accepted status and date,
and the documentation quality gate passes for the complete design chain.

### D3 — Component requirement packages

Create and review packages in this order:

1. [Vehicle simulation (`CR-VEHICLE-SIM`)](../requirements/component-decomposition-and-interface-register.md#cr-vehicle-sim)
   and [Vehicle Gateway (`CR-GATEWAY`)](../requirements/component-decomposition-and-interface-register.md#cr-gateway);
2. [Factory substrate (`CR-FACTORY`)](../requirements/component-decomposition-and-interface-register.md#cr-factory)
   and [Vehicle Data Platform (`CR-VDP`)](../requirements/component-decomposition-and-interface-register.md#cr-vdp);
3. [Aos lifecycle (`CR-AOS`)](../requirements/component-decomposition-and-interface-register.md#cr-aos);
4. [Brake Health service (`CR-BHS`)](../requirements/component-decomposition-and-interface-register.md#cr-bhs)
   and [Brake Health Cloud (`CR-BRAKE-CLOUD`)](../requirements/component-decomposition-and-interface-register.md#cr-brake-cloud);
5. [Tire Health service (`CR-TIRE`)](../requirements/component-decomposition-and-interface-register.md#cr-tire)
   and [Tire Health Cloud (`CR-TIRE-CLOUD`)](../requirements/component-decomposition-and-interface-register.md#cr-tire-cloud);
6. [Demo orchestration (`CR-DEMO`)](../requirements/component-decomposition-and-interface-register.md#cr-demo),
   [cross-cutting concerns (`CR-CROSS`)](../requirements/component-decomposition-and-interface-register.md#cr-cross)
   and [end-to-end acceptance (`CR-E2E`)](../requirements/component-decomposition-and-interface-register.md#cr-e2e).

Create every package from the
[component requirement package template](../requirements/components/template.md).
Every component requirement must cite its named parent `SYS-*` requirement,
relevant `AF-*` flow, component and interface definitions, verification levels
and required evidence. Owned executable logic must also define stable `UT-*`
unit-test obligations covering applicable normal, boundary, malformed,
unavailable and recovery behavior. External executables and packages with no
owned executable logic may record a reasoned unit-test exception and allocate
their proof to contract, integration, qualification or end-to-end verification.

Exit: every system obligation is allocated, every interface has an owner on
both sides, every component requirement has complete verification
traceability, and every owned unit of behavior has a unit-test obligation or a
reviewed exception.

### D4 — Interface contracts and acceptance tests

Freeze the versioned VISS, KUKSA, typed advisory, functional-report/event,
AosCloud, log and dashboard contracts. Define executable cases, fixtures,
suites and evidence locations for normal, unavailable, stale, malformed,
unauthorized, offline, retry, rollback and resource-bound behavior. D4 refines
how D3 obligations are proved; it does not silently change component behavior.

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
| `I1` Vehicle stimulus and Gateway | Qualify emergency-braking and explicit accelerated/pre-aged tire stimuli; add typed narrowly scoped advisory handling and dashboard status. |
| `I2` Factory and Vehicle Data Platform | Freeze the clean factory image with enabled stock IAM permission handling and a non-secret PKCS#11 seam; implement and qualify the accepted Component v1-v3 contract, thin Aos–KUKSA Credential Broker, provider platform identity and KUKSA trust configuration. |
| `I3` Brake Health product | Build the in-vehicle service, local model, bounded offline reporting, backend and function dashboard. |
| `I4` Tire Health product | Build the independent persistent condition estimator, bounded reporting, inspection advisory, backend and function dashboard. |
| `I5` Software delivery experience | Build the Software Delivery Dashboard over authoritative AosCloud APIs and the manufacturing/provisioning/promotion/retirement orchestration. |
| `I6` Security and operations | Qualify native Aos IAM instance/permission lifecycle, exact contract-bounded translation, short-lived JWT refresh/expiry, provider identity binding, per-Unit PKCS#11 signing, native AosCloud system/service/crash-log requests, retention/deletion, offline behavior and redaction. |
| `I7` End-to-end release proof | Execute `M0 -> M1 -> G0 -> G1 -> G2 -> G3 -> G4 -> T1 -> R0` on Validation and Demonstration Units with retained evidence. |

Each workstream requires the relevant component requirements and acceptance
tests before code or deployment work begins.

## Deferred Platform Capabilities

- Native AosCloud rejection of a SOTA request whose required Vehicle Data
  Platform Component version is absent or incompatible remains blocked on an
  implementing platform release. No project-side admission controller will be
  built as a substitute.
- Cloud-side pre-transfer rejection of a SOTA service whose requested KUKSA
  paths exceed an independent OEM upper bound remains future native platform
  behavior. The current broker validates native IAM identity and registered
  permissions against the installed VDP contract; it must not be presented as
  a second OEM-policy database or as Cloud admission.
- Production driver HMI, third-party Service Providers, Fleet Operators, a
  production fleet, and production vehicle-network/hardware selection remain
  outside the current demo.

## Current Stop Point

Documentation housekeeping gate D1, component-register gate D0, and joint
baseline gate D2 are complete. The current boundary is D3 component requirement
packages. Vehicle Simulation 0.4 and Vehicle Gateway 0.5 are draft packages;
Factory Substrate 0.2 and Vehicle Data Platform 0.1 are reviewed drafts. Their
`CURRENT` and `EVIDENCE` labels
describe verified implementation evidence and do not mean that the packages
are accepted. No new repository, component code, build, signature, Cloud
upload, assignment, approval, VM restart, provisioning, deprovisioning or Unit
mutation is authorized by this roadmap.
