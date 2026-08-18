<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0009: Separate Release Decision Ownership from Cloud Execution

- Status: Accepted
- Date: 2026-08-18
- Decision owner: System Architecture
- Cloud or Unit mutation authorized: no

## Context

The Platform Team and the two OEM Function Teams own independent FOTA and SOTA
release decisions. Function Team 1 and Function Team 2 are internal OEM
organizations represented in AosCloud as separate Service Providers. AosCloud
uses different identities for service artifact management and for authorizing
deployment to OEM Units.

Earlier architecture wording called AosCloud the lifecycle authority and used
generic `OEM Acceptance` actors in combined release flows. That wording mixed
three different responsibilities:

1. the engineering team that decides whether its release is acceptable;
2. the Cloud identity authorized to record an approval affecting OEM Units;
3. the control plane that stores lifecycle state and executes the transition.

It also left open whether the Software Delivery Dashboard or Demo Orchestrator
could become a second source of lifecycle truth.

## Decision

The architecture separates business decision ownership, authorization, and
lifecycle execution as follows:

1. The Platform Team owns engineering release decisions for the Vehicle Data
   Platform Component and its FOTA lifecycle.
2. Function Team 1 owns engineering release decisions for Brake Health SOTA 1.
   Function Team 2 independently owns the corresponding decisions for Tire
   Health SOTA 2.
3. A Function Team uses its Service Provider identity to develop, sign,
   publish, version, and technically verify its service artifact. That identity
   does not authorize deployment to OEM Units.
4. Validation acceptance and deployment or promotion approval affecting OEM
   Units are recorded through an authorized OEM identity. The organizational
   decision still belongs to the owning Platform or Function Team; the OEM
   identity is the Cloud authorization principal used to enact it.
5. AosCloud is the lifecycle system of record and execution control plane. It
   owns authoritative desired and reported actual state, batches, campaigns,
   recorded approvals, audit history, and delivery execution. It does not make
   the owning team's engineering release decision.
6. The OEM Software Delivery Dashboard and Demo Orchestrator are stateless with
   respect to authoritative lifecycle state. They may read and re-read
   AosCloud, present qualification evidence, and invoke an explicitly confirmed
   operation with the correct scoped identity. They must not infer approval from
   a passing test, auto-approve a candidate, impersonate a team, or maintain a
   parallel desired-state database.
7. A combined FOTA/SOTA graph requires separate owner decisions. The Platform
   Team accepts the platform candidate, the relevant Function Team accepts its
   service candidate and integration result, and promotion proceeds only when
   every required approval is recorded for the exact versions, digests, and
   targets. A generic anonymous `OEM Acceptance` does not replace those gates.

## Consequences

- Architecture and scenario flows name both the business decision owner and
  the OEM authorization identity used for the Cloud action.
- Service Provider publication or optional service verification is not
  presented as OEM deployment approval.
- The Software Delivery Dashboard must display the active team context,
  Cloud role, candidate identity, digest, effective targets, evidence, and the
  exact transition being confirmed.
- The Cloud audit record remains authoritative after the dashboard or
  orchestrator process exits.
- Current AosCloud API and RBAC operations must be qualified before the demo
  dashboard enables each mutation, but this qualification does not change the
  ownership model above.

## Rejected Alternatives

Treating AosCloud as the owner of engineering release decisions would erase
OEM accountability. Allowing a Service Provider identity to authorize its own
deployment to OEM Units would collapse the OEM trust boundary. Giving the
dashboard or orchestrator an independent lifecycle database or unattended
approval policy would create a second control plane and is also rejected.
