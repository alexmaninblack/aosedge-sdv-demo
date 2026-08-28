<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosEdge Demo Walkthrough and Review Guide

- Status: colleague-review companion
- Version: 0.1
- Prepared: 2026-08-28
- Owner: Demo Solution Team
- Review artifact: [AosEdge Demo Interaction Mockup](mockups/aosedge-demo-interaction-mockup-2-4.html)
- Accepted interaction contract: [AosEdge Demo Interaction Specification 2.5](mockups/aosedge-demo-interaction-specification.md)
- Accepted scenario source: [Demo Scenarios 2.0](staged-post-sop-brake-health-demo-scenarios.md)
- Authority: explanatory only; this guide does not redefine product behavior,
  release authority, requirements or implementation

## Why This Guide Exists

This guide is the human-readable companion to the interactive mockup. It helps
a reviewer open the mockup, follow the intended demonstration story and give
feedback without first learning the internal AosEdge architecture or reading
the complete interaction specification.

The mockup shows how an OEM can continue evolving shared vehicle capabilities
and independently owned functional services after SOP. The guide explains:

- where to look on the screen;
- who is taking each decision;
- what the presenter does;
- what the audience should observe; and
- what platform capability that observation demonstrates.

The walkthrough order is the recommended audience narrative. It is not a
global workflow restriction: the Platform, Brake and Tire teams retain
independent release lifecycles, and the presenter may switch between them
without changing vehicle or software state.

## The Story in One Minute

Before SOP, the OEM integrates the AosEdge execution and lifecycle substrate
into the vehicle. The produced vehicle is already functional, but the later
Vehicle Data Platform releases and the Brake Health and Tire Health products
are not yet installed.

After SOP:

1. the OEM Platform Team adds versioned vehicle-data capabilities;
2. the Brake Function Team independently evolves its product from Cloud data
   collection to on-vehicle analysis and then driver indication;
3. the Tire Function Team independently releases a second product on the same
   vehicle platform;
4. every release is first validated on a Test Vehicle and then authorized for
   the Production Vehicle without rebuilding the artifact; and
5. the resulting services continue local operation during loss of vehicle
   external connectivity and remain isolated by platform-enforced quotas.

AosCloud records and executes authorized lifecycle operations. It does not
approve software by itself. Producer teams accept their Test results, while
OEM Release Authority independently authorizes exact vehicle deployments after
the required verification, validation, integration and applicable homologation
evidence has been reviewed.

## How to Read the Mockup

| Screen area | What it means | What does not happen there |
| --- | --- | --- |
| Shared header | Current Vehicle and the selectable Platform, Brake and Tire producer perspectives | Changing perspective does not deploy software or switch vehicles |
| `AosEdge Software Evolution Demo` title | Opens the global Demo Lifecycle page in the right workspace | It does not replace CARLA, the Controller or Engineering Telematics |
| CARLA | The currently selected Test or Production Vehicle driving in the simulated world | CARLA does not decide software lifecycle state |
| Vehicle Controller | Scenario, Autopilot and Manual driving, restart, Safe Stop and the single external-connectivity control | It does not approve or publish software |
| Engineering Telematics | Live vehicle signals, advisories and resource-isolation evidence from the current vehicle | It is not a second Cloud dashboard |
| Team workspace | The selected team's complete version story and current release actions | The vertical order does not disable versions or force a global sequence |
| OEM Release Authority card | Independent governance and deployment authorization | Release Authority is not a producer team and does not build the artifact |
| `Details` | Read-only explanation of the exact candidate, dependency, evidence, permissions or Service quota relevant to the selected stage | Opening or closing Details never changes lifecycle state |
| Function result panel | Brake or Tire backend result correlated with the current vehicle exercise | One Function Team never sees or owns the other team's backend data |

All three producer teams are internal OEM teams. OEM Release Authority is a
separate governance role outside those teams, not a fourth product team.

## The Reusable Release Loop

Every Platform, Brake or Tire release uses the same five audience-visible
stages. Learning this loop once makes every version card readable.

| Stage | Actor and action | What the audience sees | Meaning |
| --- | --- | --- | --- |
| Publish candidate | Owning Platform, Brake or Tire team opens `Details`, then signs and submits an already prepared artifact | Exact candidate and Cloud publication state | Publication makes the candidate available; it is not deployment approval |
| Authorize Test deployment | OEM Release Authority reviews the exact artifact, effective Test target and required pre-deployment evidence | Explicit Test authorization followed by AosCloud delivery state | An independent governance decision controls deployment |
| Validate and accept on Test Vehicle | Owning producer team runs the accepted vehicle exercise and then explicitly accepts the result | CARLA, Engineering Telematics and matching Platform or Function evidence | Passing evidence does not auto-accept a release |
| Authorize Production rollout | Presenter hands the live source to the Production Vehicle; OEM Release Authority reviews the accepted Test result and unchanged artifact | Explicit Production authorization | Test acceptance and Production authorization are separate decisions |
| Show released operation | AosCloud delivers the identical artifact; the presenter drives the Production Vehicle and shows the released behavior | Live vehicle, signals and matching Function result | Production is normal operation, not a second product-validation lane |

For a later version, use `Continue testing on Test Vehicle` to return to the
Test Vehicle. The handover changes only the current live vehicle evidence
context. It does not roll back, reinstall or reset the software already present
on either vehicle.

Platform FOTA has one additional visible vehicle rule: the OEM Component
Runtime applies the component only after fresh vehicle facts prove Safe Stop.
The presenter therefore stops the vehicle before application and keeps it
stopped until readiness is confirmed. Brake and Tire are non-safety QM Service
SOTA in this demo and may be updated while the vehicle moves, subject to all
other release gates.

## Recommended Walkthrough

### Chapter 1 — Prepare the Demo Vehicles

**Purpose:** establish that the audience is seeing newly produced vehicles,
not previously prepared Cloud identities.

1. Select the `AosEdge Software Evolution Demo` title to open Demo Lifecycle.
2. Review the environment and qualification summary.
3. Use `Create new Test and Production Vehicles`.
4. Observe two manufactured vehicles awaiting provisioning. At this point
   there is no Current Vehicle, Unit identity, Cloud credential, VDP or
   functional Service.
5. Use `Provision vehicles`.
6. Observe both vehicles Online, assigned to their separate Test and Production
   target groups. The Test Vehicle becomes Current Vehicle.
7. Confirm the resulting baseline: the vehicle drives and produces engineering
   telemetry, but VDP and both functional products are absent.

**Audience takeaway:** the SOP vehicle already contains the AosEdge lifecycle
and execution substrate. New post-SOP products do not require the vehicle to be
reprovisioned or its base architecture to be redesigned.

### Chapter 2 — Platform v1 Enables the First Vehicle-Data Capability

**Purpose:** show the first post-SOP evolution of the shared vehicle platform.

1. Select `Platform Team` and locate `Vehicle Data Platform Component v1`.
2. Open `Details` to inspect its prepared purpose and capability contract.
3. Follow the reusable release loop: publish, authorize Test deployment, enter
   Safe Stop, apply, run Test validation and accept the Test result.
4. Continue with the Production Vehicle.
5. Authorize the unchanged v1 artifact for Production, enter Safe Stop and wait
   for the vehicle runtime to apply it.
6. Resume driving and show that the baseline braking-related vehicle signals
   are available through the platform.

**Audience takeaway:** the Platform Team can extend a shared vehicle-data
contract after SOP. The Cloud carries the authorized update, while the
in-vehicle runtime enforces the Safe Stop application condition.

### Chapter 3 — Brake v1 Collects Bounded Training Data

**Purpose:** show an independent Function Team shipping its first product on
top of VDP v1.

1. Return to the Test Vehicle and select `Brake Team`.
2. Open Brake v1 `Details`. The Service reads the approved braking signals and
   has its own Service quotas and backend; it is not part of VDP.
3. Publish and authorize the Service for the Test Vehicle.
4. Run the deterministic braking scenario. Watch one causal chain:

   `vehicle braking -> signals -> Brake Service -> bounded backend window`.

5. Accept the Test result, continue with the Production Vehicle and authorize
   the unchanged Service artifact.
6. Drive the Production Vehicle and observe a bounded pre-braking, active and
   post-braking telemetry window arrive in the Brake backend.

**Audience takeaway:** a Function Team owns and updates its product
independently. The first version supports data exploration without streaming
all vehicle telemetry continuously.

### Chapter 4 — VDP v2 and Brake v2 Move Analysis into the Vehicle

**Purpose:** show platform and product evolution as two separate releases that
together create a new business capability.

1. Return to the Test Vehicle and select `Platform Team`.
2. Release VDP v2 through its complete independent loop. It adds the
   backward-compatible inputs required by local brake analysis.
3. After v2 is ready on Production, return to the Test Vehicle and select
   `Brake Team`.
4. Release Brake v2 through its own independent loop.
5. Run the same braking exercise and compare the result with Brake v1: the
   Service now performs local synthetic assessment and normally sends a bounded
   derived result rather than the high-detail v1 telemetry window.

The mockup may summarize this as the derived `G3 · Edge brake assessment`
milestone, but there is no combined G3 artifact or one-click group approval.

**Audience takeaway:** Platform and Function teams can evolve independently,
while an explicit versioned contract connects their work. Moving analysis into
the vehicle reduces Cloud traffic and preserves local functionality.

### Chapter 5 — VDP v3 and Brake v3 Close the Driver-Value Loop

**Purpose:** show the evolution from observing the vehicle to giving the
driver a useful local maintenance indication.

1. Release VDP v3 first. It adds tire-related inputs and the controlled
   bidirectional advisory path.
2. Release Brake v3 as a separate Service lifecycle.
3. Run the braking exercise on the Test Vehicle and accept the result only
   after the complete evidence chain is visible.
4. Roll out the unchanged artifacts to Production in provider-first order.
5. Drive the Production Vehicle and observe:
   - the vehicle event in CARLA;
   - required signals in Engineering Telematics;
   - the Brake advisory through the accepted in-vehicle path; and
   - the derived state and advisory fact in the Brake backend.

The mockup may summarize this as `G4 · Brake advisory`; it remains a derived
capability milestone, not a combined deployment object.

**Audience takeaway:** the OEM can close a predictive-maintenance loop after
SOP without replacing the vehicle platform or coupling the functional product
to a proprietary integration path.

### Chapter 6 — Tire Health Demonstrates a Second Independent Team

**Purpose:** demonstrate multi-tenancy and independent functional lifecycles
without repeating the three-version Brake story.

1. Select `Tire Team` and inspect its one mature Tire Health v1 release.
2. Observe that it requires VDP v3 but does not depend on Brake Health.
3. Follow the same Test validation, producer acceptance and Production
   authorization loop.
4. Run the accepted tire stimulus and observe:
   - tire-related signals;
   - local condition analysis;
   - a maintenance advisory in the vehicle; and
   - a bounded result in the independent Tire backend.

**Audience takeaway:** two internal OEM Function Teams can own different
products, credentials, backends, quotas and release timing while sharing the
same governed vehicle platform.

### Chapter 7 — Vehicle Offline, Local Products Continue

**Purpose:** show why on-vehicle analytics is valuable beyond Cloud-traffic
reduction.

1. Keep the Production Vehicle driving with Brake v3 and Tire v1 installed.
2. Use the single Vehicle Controller action that disconnects the vehicle from
   the external world.
3. Observe that CARLA, local vehicle signals, Service processing and driver
   indications continue.
4. Observe that the Function backend receives no new events and shows its last
   durable receipt. The UI must not claim it can see current on-vehicle queue
   occupancy while the vehicle is offline.
5. Restore connectivity and observe delayed, de-duplicated delivery and the
   synchronization result.

**Audience takeaway:** the local product does not stop when vehicle-to-Cloud
connectivity disappears. The demo does not bypass the connectivity loss with a
hidden monitoring channel.

### Chapter 8 — Service Quotas Preserve Tenant Isolation

**Purpose:** show that one functional tenant cannot consume another tenant's
allocated resources.

1. Keep both Brake and Tire Services active on the Production Vehicle.
2. From the Tire perspective, start the fixed CPU-isolation proof against the
   real Tire Service instance.
3. Observe Tire reaching its configured quota and being throttled rather than
   terminated.
4. Observe Brake and the shared platform remaining healthy and responsive.
5. Stop the proof and confirm recovery.

**Audience takeaway:** AosCore enforces each Service's resource envelope. The
demo is not acting as its own resource manager, and the synthetic VM result is
not presented as a real-hardware performance benchmark.

### Chapter 9 — End and Reset the Demo

**Purpose:** finish the disposable laboratory lifecycle without pretending to
roll an in-field vehicle back to SOP.

1. Open Demo Lifecycle and select `End and Reset Demo`.
2. Observe lifecycle freeze, deprovisioning, Unit and Node removal, Unit Set
   cleanup, local Function-data cleanup, vehicle-source reset and overlay
   disposal.
3. Confirm that the immutable Factory Image remains unchanged.
4. Stop at `READY_FOR_M0`. The UI does not automatically manufacture or
   provision the next pair of vehicles.

**Audience takeaway:** each complete demo run receives fresh identities and
disposable provisioned state. R0 is a demo-lab reset, not an OTA rollback claim
for a customer vehicle.

## Independent Navigation and Alternative Review Paths

The recommended walkthrough is intentionally easy to present, but the mockup
must also make these independence properties clear:

- switching Platform, Brake and Tire perspective is navigation only;
- Current Vehicle remains global while perspectives change;
- each team keeps its own version focus, scroll position and lifecycle state;
- versions are never disabled merely because the presenter did not click an
  earlier version first;
- disjoint publication and Cloud operations may progress independently;
- only overlapping exact artifacts, Cloud objects or vehicle targets may
  temporarily conflict;
- while Production is Current Vehicle, a team may prepare and publish a later
  candidate before returning to the Test Vehicle for live validation; and
- completing one team's release never automatically advances another team.

Dependencies remain explicit. Brake v1 requires VDP v1, Brake v2 requires VDP
v2, and Brake v3 and Tire v1 require VDP v3. A missing dependency remains
visible and inspectable. The current demo must not pretend that a project-side
UI check is native AosCloud dependency admission; that native feature remains
deferred until a supporting platform release is qualified.

## What Reviewers Should Comment On

While following the mockup, please consider:

1. Is the business story understandable without prior AosEdge knowledge?
2. Is it clear that all producer teams are inside the OEM?
3. Is OEM Release Authority visibly independent from those producer teams?
4. Is it clear that the OEM authorizes and AosCloud executes the decision?
5. Is the difference between Test Vehicle validation and Production Vehicle
   live operation obvious?
6. Does the repeated five-stage release loop become understandable after the
   first release?
7. Are Platform, Brake and Tire dependencies visible without making the teams
   appear artificially coupled?
8. Can the reviewer correlate CARLA, Engineering Telematics and the selected
   Function result without changing browser tabs?
9. Are Safe Stop, vehicle-offline behavior and quota isolation explained at
   the right level of detail?
10. Which actions, labels or Details views remain unclear or unnecessarily
    technical?

## Technical Reference Map

This walkthrough deliberately avoids requirement and API detail. When deeper
review is needed, use:

- [Demo Scenarios 2.0](staged-post-sop-brake-health-demo-scenarios.md) for the
  accepted product and vehicle lifecycle;
- [Interaction Specification 2.5](mockups/aosedge-demo-interaction-specification.md)
  for exact UI behavior, actions and state semantics;
- [UI Traceability Register](mockups/aosedge-demo-ui-traceability-register.md)
  for requirement and acceptance-case coverage; and
- [Demo Scenario Architecture Flows 2.0](../architecture/demo-scenario-architecture-flows.md)
  for detailed component and interface sequences.
