<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0011: Contain QM Services at the Gateway and Make OEM Approval Evidence-Backed

- Status: Accepted for architecture and requirements
- Date: 2026-08-19

## Context

Brake Health and Tire Health are post-SOP OEM functional services. In this
demonstration they provide maintenance and inspection recommendations; they do
not implement a safety function and must not become a route to vehicle-motion
or safety-critical actuation.

A Function Team publishes and technically verifies its service through its
Service Provider identity, while an authorized OEM identity approves a
deployment affecting OEM Units. A demo dashboard can make the final approval
look like one button press. Without an explicit evidence model, that visual
shortcut could falsely imply that approval is an arbitrary UI action rather
than the recorded conclusion of engineering validation and acceptance.

## Decision

1. Brake Health and Tire Health are **QM-domain applications** in this demo.
   No safety goal is allocated to them, and no safety claim may depend on their
   availability, timing, output or correctness.
2. Their outputs are typed maintenance or inspection advisories. They are not
   safety warnings, direct driver-HMI implementations, vehicle-motion
   commands, or arbitrary VSS writes.
3. Aos IAM permissions and short-lived KUKSA credentials provide
   cybersecurity least privilege within the QM domain. They do not constitute
   a functional-safety argument.
4. The Vehicle Data Platform Component validates the outbound advisory as
   defense in depth. The Vehicle Gateway is the final authoritative boundary
   because it knows that the channel originates from the QM Domain Controller.
5. The Gateway shall accept only Platform-Team-owned, typed non-safety
   advisory targets. It shall validate type, range, freshness, rate and
   correlation; publish factual accepted/rejected status; and deny arbitrary
   VSS writes and throttle, brake, steering, gear, vehicle-motion or other
   safety-critical operations.
6. A service candidate is published with an immutable artifact digest and
   service-metadata digest, including its requested permissions. The owning
   Function Team completes validation and integration testing and explicitly
   accepts the exact candidate and evidence.
7. Before an authorized OEM identity confirms deployment or promotion, the
   Software Delivery Dashboard shall present the exact artifact and metadata
   identities, requested permissions, target, required validation evidence,
   owning-team acceptance and active OEM role. Missing, stale, mismatched or
   failed prerequisites block the action.
8. The visible **Approve** action is the final explicit OEM decision. Passing
   tests never auto-approve. The dashboard records the decision through
   AosCloud and then re-reads authoritative Cloud state; it does not store
   lifecycle state, invent evidence or make the release decision itself.
   The approval records that the required release process was reviewed and
   accepted; it does not by itself make the software safe or constitute a
   functional-safety certification.
9. Future native AosCloud admission can add an earlier independent policy
   gate, but current safety containment does not depend on that roadmap
   feature.

## Consequences

- The demo can truthfully show an approval button while also showing the
  validation dossier that makes the decision reviewable and auditable.
- Function Teams retain engineering ownership of their candidates; the OEM
  role remains the authority for deployment to OEM Units; AosCloud remains the
  lifecycle system of record and execution control plane.
- The Dashboard requires an evidence/prerequisite view, not only action and
  progress controls.
- The Gateway contract and negative tests become the authoritative proof that
  the QM channel cannot reach vehicle-motion or safety-critical operations.
- If a future advisory is allocated a safety goal, relied upon for hazard
  mitigation, or connected to a safety-related actuator, this ADR no longer
  applies. That change requires a new safety architecture, classification,
  requirements, independence analysis and safety case before implementation.

## Rejected Alternatives

- Treating an OEM button press as sufficient evidence without showing the
  candidate, permissions and validation basis.
- Automatically approving a candidate because tests passed.
- Letting the Dashboard maintain a second desired-state or approval database.
- Treating KUKSA/Aos IAM authorization as a substitute for Gateway containment
  or for a functional-safety analysis.
- Giving QM services arbitrary VSS write access and relying on organizational
  process alone.

## Verification Implications

The accepted design requires:

- positive and negative Gateway contract tests for every typed advisory and
  every forbidden motion/safety operation;
- stale, replayed, malformed, excessive-rate and cross-service request tests;
- Dashboard tests proving evidence completeness, exact digest/target binding,
  role display, explicit confirmation, Cloud mutation and authoritative
  re-read;
- negative tests proving that passing evidence, a Function Team acceptance or
  a Service Provider publication alone cannot trigger OEM deployment.
