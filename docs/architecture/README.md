<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture documentation

Start with the [component map](product-map.md) and
[README overview diagram](../../README.md#how-the-lab-fits-together).
They distinguish the simulated vehicle, real AosEdge software, ARM64 virtual
controller, Factory base image, local backends and remote Aos Cloud.

For implemented behavior and exact acceptance, use
[implemented architecture](current-implementation.md) and the
[current baseline](../qualification/current-baseline.md). They are separate
from expanded design obligations.

- [High-Level Architecture 1.8](high-level-architecture.md): accepted boundaries,
  authority and invariants, with later amendments taking precedence.
- [Architecture Flows 2.2](demo-scenario-architecture-flows.md): manufacturing,
  provisioning, component/service evolution, offline operation and retirement.
- [Repository boundaries](repository-boundaries.md): component ownership.
- [Demo Control](demo-control.md): current shared orchestration and state owners.
- [Native service inputs](demo-control-service-inputs.md): accepted public/private runtime contract.
- [Backend ownership](demo-control-backends.md): current container, context and cleanup boundaries.
- [Cloud observations](demo-control-cloud-observation.md): bounded authoritative software/resource reads.
- [Component publication](demo-control-component-publication.md): request, acceptance, processing and reconciliation stages.
- [Image compatibility](demo-control-image-compatibility.md): exact controller-image/profile guards.
- [Service observations](demo-control-service-observation.md): read-only owner-bound catalog/status projections.
- [Architecture decisions](decisions/README.md): current rationale and explicit supersession.
- [Editable diagrams and exports](diagrams/README.md): design diagrams, not a claim of full implementation.

A document version is not a demo release number. The launcher catalog and
immutable delivery descriptor select media; old Factory/Kit numbers never
override that selection.
