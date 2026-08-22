<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cross-Component Contracts

- [Vehicle Hardware Capability Profile](vehicle-hardware-profile/README.md)
  — selected CARLA hardware-equivalent capabilities and complete
  Simulator–Gateway accounting.
- [Simulator Control and Context Contract](simulator-control-context/README.md)
  — accepted drive-mode/world-context transitions, reset/discontinuity
  semantics and engineering VSS projection.
- [Exclusive Live-Source Assignment Contract](exclusive-live-source-assignment/README.md)
  — audience model for Validation/Demonstration Vehicles and the host-side
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
- [Software Delivery Dashboard Contracts](software-delivery-dashboard/README.md)
  — sanitized coverage catalogue and evidence-state schema.

Component-private schemas and fixtures remain in their owning repositories.
This directory contains only contracts that span repository boundaries.
