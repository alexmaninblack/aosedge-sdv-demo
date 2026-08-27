<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Add or Change a Demo Scenario

Use this sequence for a new scenario or a material change to an existing one.
It prevents an attractive visual idea from bypassing platform lifecycle,
security or component ownership.

## 1. Define the Audience-Visible Story

Describe the initial state, the actor making each decision, the visible
action, the expected result and the reset/end state. Keep implementation names
out of the first draft unless the audience must see them.

## 2. Check the High-Level Architecture

Map the story to existing system boundaries, authorities and directions. If a
new component, authority or trust boundary is required, revise and review the
High-Level Architecture before continuing.

Classify the change using
[Documentation and Requirements Management](../governance/documentation-and-requirements-management.md):
level A changes presentation only, level B changes behavior within accepted
boundaries, and level C changes architecture. Level C starts as a proposed ADR
and uses a short-lived architecture branch for the complete document cascade.

## 3. Add Architecture Flows

Describe normal, validation, promotion, unavailable, offline, failure and
cleanup paths. Separate Validation and Production Units and preserve the
independence of Platform/FOTA and each Function Team/SOTA lifecycle.

## 4. Derive System Requirements and Gaps

Create traceable `SYS-*` requirements for every observable outcome and safety
constraint. Record missing capabilities as explicit gaps; do not hide them in
manual presenter actions.

## 5. Allocate Components and Interfaces

Update the Component Register with stable component and interface IDs,
ownership, lifecycle, authoritative data source and implementation state.
Choose the repository only after that allocation is clear.

## 6. Define Deterministic Stimulus and Evidence

When CARLA supplies the stimulus, provide a bounded, repeatable scenario with
manual takeover, safe stop and owned-actor cleanup. Define the signals or
events visible at every interface and the dashboard evidence the audience
will see. Engineering dashboards remain read-only views over authoritative
sources.

## 7. Freeze Contracts Before Implementation

Version the relevant VISS, KUKSA, Cloud, report, event, log and dashboard
contracts. Specify unavailable, stale, malformed, unauthorized, offline and
retry behavior before implementing either side.

## 8. Review Audience-Visible UI Mockups

Inventory the launcher/controller, engineering dashboard, OEM delivery views,
Function Team views and every other interface the presenter or audience can
see. Before implementing a new view or changing an existing one, review a
low-fidelity mockup and state flow that identify:

- the audience and actor using the surface;
- the authoritative source of every displayed fact;
- the owner and confirmation boundary of every action;
- the relevant component, interface and requirement IDs; and
- normal plus applicable blocked, submitting, uncertain/reconciling, failed,
  incomplete, stale, offline and redacted states.

Unchanged parts of an existing interface may be reused by reference. The
mockups define presentation and interaction intent; accepted architecture,
requirements and versioned contracts remain authoritative for behavior. Do
not start the affected UI implementation until this review gate is accepted.

## 9. Implement in the Owning Repositories

Build and test each component independently, then qualify its interfaces.
Promote the same accepted artifact bytes and digest from the Validation Unit
to the Production Unit. Do not rebuild a release for promotion.

## 10. Add Reproduction and Acceptance Material

Update operator instructions, workspace locks, component state, sanitized
evidence and the reset procedure. A scenario is complete only when another
person can identify its prerequisites, run it, understand its visible result
and return the environment to the declared state.

## Authorization Boundary

An accepted scenario document or implementation plan does not authorize
signing, Cloud upload, assignment, validation approval, provisioning,
deprovisioning, VM reset or deletion. Those remain explicit operational gates.
