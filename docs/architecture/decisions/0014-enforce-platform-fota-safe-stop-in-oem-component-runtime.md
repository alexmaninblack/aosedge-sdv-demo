<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0014: Enforce Platform FOTA Safe Stop in the OEM Component Runtime

- Status: Accepted
- Date: 2026-08-26
- Change class: C — trusted vehicle-state interface and Platform FOTA enforcement boundary

## Context

Vehicle Data Platform Component FOTA is authorized through the normal OEM
release process and delivered through AosCloud/AosCore. Authorization does not
mean that the vehicle is physically safe for application. AosCloud does not
observe vehicle motion and the Demo UI must not become an alternative update
authority.

The current factory-installed `systemd-slot-component` runtime validates and
prepares an accepted component candidate and then immediately activates it. It
has no vehicle-state input, Safe Stop policy or durable waiting state. A simple
wait added only to `StartInstance` is also insufficient: when an installed
component is replaced, Service Manager calls `StopInstance` for the current
version before it calls `StartInstance` for the replacement.

The accepted Simulator Control and Context Contract already defines the
project-owned read-only control-state projection, including
`Vehicle.CarlaSimulation.Control.ActiveMode` and `TransitionState`. Its
implementation and the Platform FOTA policy that consumes it remain open.

## Decision

### Keep authorization and physical application separate

OEM Release Authority may authorize Platform FOTA while the selected vehicle
is moving. AosCloud remains authoritative for desired and actual lifecycle
state, but it is not a source of physical-motion truth and does not approve a
Safe Stop condition.

The factory-installed OEM Component Runtime inside AosCore Service Manager
shall be the Platform FOTA application enforcement point. The runtime shall
not activate, replace or remove its Vehicle Data Platform Component unless it
has fresh, stable and complete Safe Stop evidence from the Vehicle Gateway.

### Use a platform-owned vehicle-state boundary

The Vehicle Gateway shall expose the accepted read-only control-state
projection and factual vehicle values. A distinct purpose-bound per-Unit
`PLATFORM_UPDATE_RUNTIME` mTLS role shall permit one connection and only the
ten Safe Stop paths, using a credential separate from the VDP peer and bound
to the same selected Unit and assignment generation. A runtime-internal
`VehicleStateProviderItf` with a VISS 3.1 transport adapter shall isolate
transport and demo-specific integration from the pure lifecycle policy. The
runtime shall not depend on the VDP
being updated, KUKSA, either functional Service, AosCloud motion inference or
the Demo UI for this evidence.

The runtime-owned Safe Stop policy shall require, at minimum:

- applied control mode `SAFE_STOP`;
- transition state `STABLE`;
- fresh factual speed at or below the accepted threshold;
- zero throttle and applied brake hold;
- the complete condition for the accepted consecutive-sample window using
  distinct monotonic `FrameId` values rather than repeated cached reads; and
- no stale, missing, contradictory or reset-discontinuous evidence.

The versioned Platform FOTA Safe Stop contract owns the exact thresholds,
freshness, stability window, timeout and reason vocabulary. A stopped vehicle
in another control mode, including a temporary traffic stop, is not Safe Stop.

### Gate every destructive component transition

For replacement or removal, `StopInstance` shall wait before marking the
current provider unavailable or stopping it. For first installation and the
subsequent start of a replacement, `StartInstance` shall prepare the candidate
and revalidate Safe Stop before activation. Safe Stop shall remain valid
through every destructive activation phase; loss or uncertainty blocks or
fails the transition. A first-install slot remains empty; a replacement
preserves or restores the previous healthy release; a removal preserves or
restores the current healthy release.

The gate shall be bounded below the current AosCore node-status timeout. It
shall fail closed rather than waiting indefinitely or treating a missing
vehicle-state source as stopped.

### Persist and recover the waiting state

The runtime transaction state machine shall add a durable
`WaitingForSafeStop` phase between candidate preparation and destructive
activation. Only transaction metadata is durable; Safe Stop samples are never
persisted. One bounded asynchronous worker shall return native `Activating`
after the durable wait is established, shall not hold the runtime's main mutex
while waiting and shall be cancelled and joined within a bound during runtime
stop. After VM or runtime restart, old evidence is never reused as
current. Where a prior healthy provider exists, the runtime shall restore it;
for a first install, the slot shall remain empty. The runtime then reconstructs
the pending transaction, obtains fresh evidence and either resumes the same
candidate idempotently or fails it without activating.

A repeated request for the same candidate may reattach to the transaction. A
different candidate while a transition is active shall be rejected. No reboot
may turn a previously observed Safe Stop into implicit authorization.

### Expose standard lifecycle state plus structured reason evidence

AosCore/AosCloud continue to expose their native component lifecycle states,
including `Activating`, `Active` and `Failed`. The OEM runtime shall emit
bounded structured reasons such as `waiting_for_safe_stop`,
`vehicle_state_stale`, `safe_stop_lost_during_apply` and
`safe_stop_timeout` through the native Aos logging path. The Demo UI may
present native lifecycle and Gateway facts and may request those runtime
reasons through the accepted on-demand log flow. Its bounded `Waiting for Safe
Stop before application` wording is a derived audience interpretation, not a
native Cloud state. The UI shall not issue a substitute apply mutation or claim
to enforce the condition.

Driving resumes only through an explicit presenter action after exact
component readiness. Platform FOTA does not automatically leave Safe Stop.

## Consequences

- The OEM Component Runtime and its fixed trust/configuration are part of the
  pre-SOP OEM Demo Factory Image; this policy is not carried by a VDP FOTA
  payload.
- The accepted Gateway control-state projection must be implemented and made
  available through a separately bounded platform-runtime read role.
- The runtime gains a vehicle-state provider abstraction, Safe Stop policy,
  bounded gate, durable waiting phase and restart/cancellation tests.
- First install, replacement, removal, timeout, stale evidence, Safe Stop loss
  and restart while waiting require explicit qualification.
- No upstream AosCore fork, Cloud-side motion rule, KUKSA dependency or
  UI-owned enforcement is introduced for the current demo.
- A future native AosCore update-scheduler contract may replace this current
  integration only after its released implementation and migration behavior
  are inspected and qualified.

## Rejected Alternatives

- Require the presenter to stop the vehicle before OEM authorization.
- Let the Demo UI decide that the vehicle is safe and then call an apply API.
- Treat zero speed alone as Safe Stop.
- Read Safe Stop through the VDP or KUKSA path being updated.
- Add a wait only to `StartInstance` and ignore Service Manager stop ordering.
- Wait indefinitely inside the runtime.
- Claim that the current public `READY_TO_UPDATE` protocol artifact proves a
  scheduler implementation in the pinned AosVM release.

## Acceptance Conditions

- The Gateway publishes the accepted control-state projection and factual
  stop evidence with freshness and discontinuity semantics.
- Unit tests prove policy truth tables, stale and contradictory input,
  bounded waiting, cancellation, first install, replacement and removal.
- Runtime restart while waiting never activates without fresh evidence, never
  populates a first-install slot early and never loses an applicable previous
  or current healthy release.
- VM integration proves a moving Platform FOTA waits, explicit Safe Stop
  releases it, application stays stopped and readiness precedes explicit
  driving resume on both Test and Production Vehicles.
- Native Aos logs and the Demo UI distinguish Cloud authorization, runtime
  waiting, application and readiness without presenting AosCloud or the UI as
  the physical enforcement point.

Acceptance of this ADR records the design and documentation cascade. It does
not by itself authorize an image build, artifact signing, provisioning,
deprovisioning or Cloud mutation.
