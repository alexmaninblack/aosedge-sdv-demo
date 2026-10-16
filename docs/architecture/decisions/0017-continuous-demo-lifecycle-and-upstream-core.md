<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0017: Continuous Demo Lifecycle and Upstream Core

- Status: Accepted by the operator, including storage/ignition and Stop/Start amendments
- Owner: Demo Solution Team / Platform Team
- Scope: Test lifecycle and retained native storage; editorial consolidation only

## Context

Native CM version cleanup could delete storage still owned by another version
of the same service instance. Hiding a UI action cannot fix that defect.
Controller power cycling, stopping a local demonstration, destructive retirement
and host sleep are separate operations and require separate contracts/proof.

## Decision

1. Preserve storage while another version of the same instance owns it; retain
   final-owner cleanup. The authorized minimal native storage/cold-component
   corrections belong in pinned source and the qualified Factory, not an
   ad-hoc guest patch. Existing images and proof are not relabelled stock
   upstream mainline. Local regression is not live restart qualification.
2. Do not expose Studio Park/Resume. Reject old-browser requests at the command
   boundary; retained CLI primitives are engineering-only and warn about their
   storage-retention boundary. Historical receipts remain readable.
3. Safe Stop pauses motion with the controller running. Ordinary Stop demo
   closes owned runtime but retains the same Test, identity, disks, models,
   histories and release continuity. Start restores that Test under current
   guards; it is neither new provisioning nor reuse of a retired overlay.
4. Controller ignition off/on can restore the existing provisioned connection
   with the same Unit/Node/certificates and service state, stationary and without
   Autopilot. Require a new boot, same source identity, external network ON and
   no conflicting/uncertain operation. Never override an explicit block,
   reprovision or blindly retry. Scoped ignition evidence is in the baseline;
   cold externalOFF and nonempty-outbox power loss remain separate gates.
5. Finish is explicit destructive retirement with ownership, confirmation and
   uncertainty guards. Page entry deletes nothing. Preserve Factory,
   infrastructure, published releases and release-number continuity. A failed
   or interrupted Test is reconciled; it is not silently reset or replaced.
6. External network off/on, service upgrades, independent model Reset and Return
   to road are separate actions. None implies VM restart, model reset, relaxed
   conflicts or fabricated observation generations.
7. Host sleep/wake tolerance remains the separate
   [accepted plan](../../planning/active/native-sleep-wake-recovery-2026-09-21.md),
   not an implemented recovery claim or authorization for automatic CM/VM
   restart. A parked work session still uses verified end-of-check shutdown.

## Qualification boundary

The continuous demonstration verifies empty Factory → detached source → initial
VDP publication → provision/Online → stationary attachment → Safe Stop FOTA,
serial VDP V1/V2/V3 and Brake V1/V2/V3 plus Tire V1 and same-profile replacement.
Prove actual products, continuity and provenance, not upload alone. QM SOTA
does not inherit platform Safe Stop.

Verify advisory, independent Reset/CLEAR/renewed warnings, Manual/Return to road,
source interruption, offline-local authorization/analytics, stopped backend
ingress and exact queued delivery after reconnect. Explicit Finish returns to
empty Create state. Stop/Start, ignition, page/Presenter/backend recovery and
negative/partial outcomes retain their own cases. Scoped proof does not close
the entire crash/nonempty-outbox/long-retention matrix. Any unexpected storage
loss fails the cycle and preserves evidence; never conceal it with retry or
ledger editing.

Build a successor Factory only for a proved factory-owned delta after its gates.
UI/backend/service edits alone do not justify rebuilding. The
[implementation map](../current-implementation.md) and
[baseline](../../qualification/current-baseline.md) own current evidence.

## Provenance

The superseded no-patch/fresh-controller-only instructions and defect
investigation are preserved in
[Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/1a0d66f4b340bfc7b487062f7bb316623ad86af8/docs/architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md),
not alternative current lifecycle instructions. Stable UI/requirement IDs and
the unclosed acceptance matrix are unchanged.
