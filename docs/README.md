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

- [Kit028 / Setup042 source return point](qualification/kit028-setup042-source-publication-2026-10-05.md)
  — candidate tag, exact cross-repository source pins, unchanged DMG provenance
  and explicit remaining qualification gates.
- [Installed preview: Cloud first use](getting-started/installed-preview-cloud-first-use.md)
  — existing access, secure enrollment/recovery and exact Subject selection;
  [native first-use evidence](qualification/cloud-first-use-implementation-2026-09-29.md) and
  [serial E2E and installed-candidate qualification](qualification/installed-serial-e2e-2026-09-29.md).
- [Installer first-use continuation 30 September](qualification/installer-first-use-2026-09-30.md)
  — changing-display recovery, native password entry, private directory ordering
  and existing-account enrollment qualification.
- [M1 installation qualification](qualification/m1-installation-2026-10-01.md)
  — pinned clean-host candidate, automation, measured preflight and current
  native installation/E2E evidence; internal storage only.
- [Current implemented architecture and traceability](architecture/current-implementation.md)
  — requirements, owning code, accepted amendments and qualification limits.
- [All 25 protocol families: implementation status](../contracts/implementation-status.md)
  — current wire versions, authority and remaining contract drift.
- [Complete documentation audit](qualification/documentation-implementation-audit-2026-09-24.md)
  — discrepancies, corrections, tests and unclosed gates.
- [Current operator workflow](operations/current-demo-workflow.md)
  — Test-only lifecycle, serial updates, reset, offline and ignition.

- [Demo1.1 source return point](qualification/demo-v1.1-return-point.md)
  — exact dependency pins, Factory39 provenance, restoration and known limits.
- [Current .39 candidate and baseline history](qualification/current-baseline.md)
  — retained Test image, installed profiles, dated qualification and exclusions.
- [Factory .39 artifact cleanup](qualification/factory-39-cleanup-2026-09-24.md)
  — retired image/build inventory, preserved Production .31 and disk accounting.
- [17 September pre-UI checkpoint audit](qualification/pre-ui-checkpoint-2026-09-17.md)
  — historical source return point, evidence, cleanup and then-remaining gates.
- [13 September consolidation audit](qualification/factory-33-consolidation-audit-2026-09-13.md)
  — source/remote inventory, cleanup disposition, KUKSA permissions and Cloud
  recovery workaround, with exact remaining closure conditions.
- [Active Studio delivery plan](planning/active/demo-studio-delivery-plan.md)
  — current phase position and next work; dated execution history is separate.
- [Choose a task](getting-started/README.md) — run AosVM, reproduce the current
  demo, understand the system, modify a component or add a scenario.
- [Reproduction guide and readiness matrix](getting-started/reproduce-demo.md)
  — what works today, required repositories and access, and what remains a
  target.

## Architecture

- [Architecture documentation index](architecture/README.md)
- [High-Level Architecture 1.8 — accepted](architecture/high-level-architecture.md)
  — current end-to-end system view with the accepted authorization,
  Release Authority, Safe Stop and Tire Health decisions.
- [Demo Scenario Architecture Flows 2.2 — accepted](architecture/demo-scenario-architecture-flows.md)
  — complete manufacturing, provisioning, post-SOP evolution, Function Team 2
  `T1` Tire Health stage, observability, offline, and retirement mapping.
- [Repository and component boundaries](architecture/repository-boundaries.md)
  — ownership across the participating repositories.
- [Demo Control — implementation design and history](architecture/demo-control.md)
  — shared `democtl`/UI core; current workflow and dated implementation amendments.
- [Native Aos service identity, data and tokens — accepted](architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
  — approved Brake/Tire metadata, private token sessions and native startup;
  documentation cascade and implementation authorized.
- [Architecture decisions](architecture/decisions/) — accepted and proposed
  decisions and their consequences.
- [Architecture diagrams](architecture/diagrams/) — editable diagram sources
  and matching review exports.

## Demo

- [Demo documentation index](demo/README.md)
- [AosEdge Demo Walkthrough and Review Guide](demo/aosedge-demo-walkthrough.md)
  — human-readable companion for following the clickable mockup chapter by
  chapter and collecting colleague feedback.
- [Staged Post-SOP Brake and Tire Health Demo Scenarios 2.1](demo/staged-post-sop-brake-health-demo-scenarios.md)
  — accepted baseline combining Brake Health v1-v3 evolution with one mature
  independent Tire Health v1.0 product on VDP v3.
- [Demo assets](demo/assets/) — original, license-cleared visual sources and
  exports. Storyboards and presenter materials will be added here only after
  review.

## Requirements

- [System Requirements and Traceability 2.2 — accepted](requirements/system-requirements-and-traceability.md)
  — system obligations, complete coverage of the twenty-two Architecture Flows
  gaps, verification intent, repository ownership and component allocation.
- [Component Decomposition and Interface Register 2.2 — accepted](requirements/component-decomposition-and-interface-register.md)
  — logical components, implementation state, lifecycle and repository
  boundaries, runtime and Cloud interfaces, and component-package allocation.
- [Component requirement packages and template](requirements/components/README.md)
  — ordered D3 work, human-readable component requirements, unit-test
  obligations and verification traceability.
- [D4 Interface and Qualification Decision Register 1.0](requirements/d4-decision-register.md)
  — one consolidated route through shared D4 decisions without duplicating
  component requirements or ownership.
- [Requirements documentation](requirements/README.md)

## Planning

- [Installable distribution and reproducibility](planning/active/installable-distribution-and-reproducibility.md)
  — accepted packaging, repository-entry-point and clean-Mac qualification plan;
  engineering previews do not constitute a clean-Mac-qualified release.
- [External SSD deployment plan](planning/active/external-ssd-deployment.md)
  — prepared 1 TB disk, package retention and isolated/clean-system test sequence;
  macOS installation and runtime migration have not been performed.
- [AosCore mainline migration — 23 September](planning/active/aoscore-mainline-migration-2026-09-23.md)
  — authorized sequence, native proof, pinned candidate and remaining Factory/E2E gates.
- [Planning documentation index](planning/README.md)
- [Current design and delivery roadmap](planning/roadmap.md)
- [Repository inventory and migration plan](planning/repository-inventory-and-migration-plan.md)
  — completed workspace migration and cleanup record retained as historical
  evidence.

## Research

- [Native Setup permission continuity — 29 September](qualification/native-setup-signing-2026-09-29.md)
  — explicit stable signing, preserved travel state and remaining native checks.
- [Installed first-use reconciliation — 28 September](qualification/installed-first-use-2026-09-28.md)
- [Installed existing-access handover — 28 September](qualification/installed-existing-access-2026-09-28.md)
- [Clean application installation — 28 September](qualification/clean-installation-2026-09-28.md)
  — current Kit 009, native setup and isolated installation evidence; explicit
  remaining onboarding and launch gates.
- [Installed clean-state E2E — 28 September](qualification/installed-clean-e2e-2026-09-28.md)
  — serial upgrades, independent resets/history, offline backlog delivery and
  ignition recovery; explicit first-use engineering corrections retained.
- [Installed travel pause and resume point — 28 September](qualification/installed-pause-2026-09-28.md)
  — data-preserving stop and SSD ejection, followed by the next launch checkpoint.
- [Native Presenter launch — 28 September](qualification/native-presenter-launch-2026-09-28.md)
  — warm/reopened native entry, ownership and preservation passed; initial
  file-open delay remains an explicit first-use gate.
- [Installed Gateway trust — 28 September](qualification/installed-gateway-trust-2026-09-28.md)
  — accepted per-instance server identity, source/security tests, live TLS proof
  and Kit 010 installation boundary; cold first-use remains separately tracked.
- [Retained-Test distribution E2E — 28 September](qualification/distribution-stage2-live-e2e-2026-09-28.md)
  — UI, real maneuvers, independent resets, offline delivery, ignition recovery,
  timings and unresolved presentation/transport findings; not clean installation.
- [Stage 2 UI corrections and recheck — 28 September](qualification/distribution-stage2-ui-corrections-2026-09-28.md)
  — deployed ignition/Finish separation, native caption fixes and the still-open
  transport investigation; includes bounded synthetic receive-delay evidence.
- [Internal disk growth audit — 29 September](research/disk-growth-audit-2026-09-29.md)
- [Authorized storage consolidation — 29 September](qualification/storage-consolidation-2026-09-29.md)
  — reconciles the earlier 200+ GB free-space observation with retained standalone
  build inputs, cloned runtime/video copies, system data and SSD capacity; no cleanup.
- [Post-assembly disk retention audit — 27 September](research/distribution-stage2-retention-audit-2026-09-27.md)
  — obsolete runtime kits, old Zen cache, updated Docker accounting and
  recipe-gated consolidation; inspection only, no deletion.
- [Distribution Stage 0 input inventory](research/distribution-stage0-inventory-2026-09-25.md)
  — observed source/artifact pins, dependency and licensing owners, portability
  risks and next bounded packets; not an installer release.
- [Disk usage and warm-build retention audit — 25 September](research/disk-usage-retention-audit-2026-09-25.md)
  — measured Builder/Docker candidates, hard-link accounting and protected
  current build inputs; authorized Builder cleanup recovered about 28 GiB,
  while Docker and other candidate pools remain untouched.
- [Unsigned-package and session-signing change audit](architecture/decisions/0016-unsigned-packages-and-session-scoped-signing.md)
  — source-certificate failure, per-Cloud signing/publication gaps, bounded
  migration, service parity and preservation of the current parked Test.

- [Demo Control UI command performance audit](research/democtl-ui-performance-audit-2026-09-13.md)
  — used command paths, implemented latency reductions, isolated measurements
  and retained identity/readiness/cleanup checks; not live E2E qualification.
- [Demo Studio action and integration audit](research/demo-studio-action-audit.md)
  — Studio B mockup actions mapped to current Demo Control and Cloud APIs,
  with observed gaps and proposed integration boundaries; not live qualification.
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

- [Cloud first-use boundary proof — 29 September](qualification/cloud-first-use-boundaries-2026-09-29.md)
  — isolated certificate-transport and exact-Subject tests, retained-Test
  GET-only observation, and the two remaining onboarding design choices.
- [Demo v1.0 sequential UI E2E — 23 September](qualification/demo-v1.0-ui-e2e-2026-09-23.md)
  — observed run, resource-metric diagnosis and evidence prompting the mainline migration.
- [Qualification documentation index](qualification/README.md)
- [Current working baseline and acceptance limits](qualification/current-baseline.md)
- [CARLA VISS-to-KUKSA qualification](qualification/carla-viss-to-kuksa.md)
- [Legacy component locks and current pin reconciliation](qualification/component-lock.md)
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
