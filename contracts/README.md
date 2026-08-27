<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross-Component Contracts

- [Vehicle Hardware Capability Profile](vehicle-hardware-profile/README.md)
  — selected CARLA hardware-equivalent capabilities and complete
  Simulator–Gateway accounting.
- [Simulator Control and Context Contract](simulator-control-context/README.md)
  — accepted drive-mode/world-context transitions, reset/discontinuity
  semantics and engineering VSS projection.
- [Platform FOTA Safe Stop Contract](platform-fota-safe-stop/README.md)
  — accepted Gateway evidence, OEM Component Runtime gate, durable waiting,
  recovery and qualification rules for Vehicle Data Platform Component FOTA.
- [Exclusive Live-Source Assignment Contract](exclusive-live-source-assignment/README.md)
  — audience model for Validation/Production Vehicles and the host-side
  one-source sequential-assignment proof.
- [VISS Trust and Telemetry Profile](viss-trust-telemetry-profile/README.md)
  — private peer roles, mTLS, selected-Unit gate, timing, failure semantics and
  complete engineering VISS-path accounting.
- [VDP Compatibility Profile](vdp-compatibility-profile/README.md)
  — additive VDP v1-v3 path sets, service compatibility, installed identity,
  fail-closed readiness and factual dashboard guidance.
- [Typed QM Advisory Profile](qm-advisory-profile/README.md)
  — exact Brake/Tire Request and Gateway Status paths, schema-bound envelopes,
  freshness, replay/rate limits, clear/expiry and final Gateway authority.
- [Current-Demo KUKSA Authorization Exchange](kuksa-current-demo-authorization/README.md)
  — strict current-release Service-bootstrap to compatibility-helper local
  request, readiness, issuance and rejection protocol.
- [Artifact Publication Credential Profile](artifact-publication-profile/README.md)
  — role-bound Platform OEM, Brake SP1 and Tire SP2 signing/publication
  profiles, current `aos-signer` compatibility limits and helper isolation.
- [Software Delivery Dashboard Contracts](software-delivery-dashboard/README.md)
  — sanitized coverage catalogue and evidence-state schema.
- [Brake Telemetry Window Contract](brake-telemetry-window/README.md)
  — Brake Health v1 acquisition, bounded event-window messages, canonical
  hashes, idempotency and durable service-local spool behavior.
- [Brake Health Synthetic Model Contract](brake-health-model/README.md)
  — accepted D4-016.3 contract for exact v2 inputs, deterministic condition
  arithmetic, assessment/event messages and crash-safe local state; D4-003
  calibration remains an implementation-acceptance gate.
- [Brake Health v3 Advisory Policy](brake-health-advisory-policy/README.md)
  — accepted D4-016.4 policy binding a new or persisted active synthetic
  assessment to the existing typed QM advisory and authoritative Gateway
  Status.
- [Brake Health Runtime and Evidence Profile](brake-health-runtime/README.md)
  — accepted D4-016.5 readiness axes, requested Aos quotas, cross-version state,
  CPU-throttling isolation boundary and bounded native-log evidence.
- [Brake Health Cloud API](brake-cloud-api/README.md)
  — D4-017 review candidate for isolated local-demo delivery, transactional
  durable acknowledgement, SQLite persistence, factual UI queries and exact
  reset; production backend authentication is Function Team-owned and out of
  scope.
- [Tire Health In-Vehicle Product Contract](tire-health-model/README.md)
  — accepted D4-018 contract for VDP v3 input, synthetic local estimation,
  hysteresis, derived messages, advisory, bounded state and runtime evidence.
- [Tire Health Cloud API](tire-cloud-api/README.md)
  — accepted D4-019 contract for the isolated Function Team 2 backend,
  idempotent derived-result ingestion, UI queries and exact reset.
- [Local Demo Hosting and VM Route](local-demo-hosting/README.md)
  — D4-020 review candidate for exact ARM64 containers, ports, volumes,
  loopback/publication-helper sessions and isolated QEMU guest-to-host routes.
- [Service Tenant Quota Proof](service-tenant-quota-proof/README.md)
  — D4-023 design-reviewed contract for Function Team-requested/OEM-approved Service
  metadata, AosCore-only enforcement and the read-only demo evidence boundary.
- [Shared Evidence, Correlation and Chronology](shared-evidence-correlation/README.md)
  — D4-024 design-reviewed correlation, chronology, sanitized projection,
  idempotency/ordering and qualification contract.
- [Demo Run State, Overlays and Cleanup](demo-run-state/README.md)
  — D4-021 design-reviewed Factory/overlay layout, bounded per-operation
  recovery registry, resource-scoped conflicts and ordered R0 cleanup.
- [End-to-End Stage Evidence](e2e-stage-evidence/README.md)
  — D4-025 review-in-progress contract for atomic stage assertions, evidence
  composition and the formal acceptance dossier.

Component-private schemas and fixtures remain in their owning repositories.
This directory contains only contracts that span repository boundaries.
