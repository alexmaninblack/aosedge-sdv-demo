<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Post-SOP Emergency Braking and Predictive Brake Health Demo Scenario

- Status: Accepted baseline
- Version: 1.0
- Accepted: 2026-08-16
- Scope: audience-visible story, product behavior, dashboards and backend role
- Architecture: [Post-SOP SDV Feature Extension Architecture](../architecture/post-sop-sdv-feature-extension-architecture.md)
- Technical decomposition status: intentionally deferred
- Cloud or Unit mutation authorized: no

## Purpose

This document defines what the demonstration should communicate, what the
audience should see, and how the visible elements form one coherent story. It
does not select implementation technologies, APIs, packages, repositories,
builds, signing operations or Cloud mutations.

The scenario is derived as an original project narrative. External presentation
screenshots, commands, logs and proprietary artifacts are not copied into this
public repository.

## Scenario Statement

The selected scenario is:

> **Post-SOP Emergency Braking and Predictive Brake Health**

An already provisioned vehicle can initially detect and report an emergency
braking event using its accepted basic telemetry. After start of production,
the OEM adds a qualified brake-health platform capability and an OEM Service
Provider updates its in-vehicle service. The same vehicle can then perform
event-triggered brake-condition monitoring, analyze the condition locally,
decide locally whether a driver advisory is required, and display that warning
without contacting the Cloud. The vehicle synchronizes its incident report to
the OEM-SP backend asynchronously when connectivity is available. The feature
is validated first on a validation vehicle and then promoted without rebuilding
the accepted artifacts to a production-like demonstration vehicle.

The business claim is not merely that a new container runs. The audience must
see a useful vehicle behavior that did not exist before the post-SOP release.

## Two Different Stories That Must Not Be Mixed

The demonstration contains two connected but distinct stories.

### Release-time story

This explains how the feature is created and delivered:

```text
OEM-SP capability request
    -> Vehicle Platform Team FOTA qualification
        -> capability handoff
            -> OEM-SP SOTA integration
                -> formal acceptance
                    -> promotion to the demonstration vehicle
```

### Runtime story

This explains what the accepted feature does while the vehicle is operating:

```text
emergency braking event
    -> diagnostic monitoring session
        -> in-vehicle brake and wheel condition analysis
            -> in-vehicle advisory decision
                -> local IVI warning and inspection recommendation
                    -> asynchronous backend report when connected
```

FOTA or SOTA deployment must not occur in response to a live emergency braking
event. The service is already installed. The event changes its operational
state from normal monitoring to a bounded diagnostic investigation.

The Cloud is not part of the runtime decision path. Loss of connectivity must
not block event detection, diagnostic analysis, the local advisory decision or
the IVI warning. The report is retained locally and synchronized later.

## Participants

| Participant | Role in the story |
| --- | --- |
| Vehicle Platform Team | Delivers and qualifies vehicle-facing brake-health capabilities through the platform lifecycle |
| OEM Service Provider (OEM-SP) | Owns the Brake Health feature, its in-vehicle service, backend, product dashboard and SOTA lifecycle |
| OEM Release and Validation Authority | Accepts the combined feature graph and authorizes promotion |
| Validation Vehicle | Persistent AosVM used for platform qualification and OEM-SP feature integration |
| Production-like Vehicle | Persistent demonstration AosVM that receives only an accepted graph |
| Driver | Experiences the vehicle event and receives an IVI warning |

No external third-party Service Provider, Fleet Operator or real production
fleet participates in this demonstration.

## Demonstration Environment Roles

| Existing or planned element | Audience-facing meaning |
| --- | --- |
| CARLA and ego runtime | Physical vehicle, road, traffic and emergency braking event |
| VISS and vehicle-data providers | Vehicle-facing data source and platform capability boundary |
| KUKSA in AosVM | Stable vehicle-data contract used by the OEM-SP service |
| Validation VM | OEM engineering vehicle |
| Demonstration VM | Vehicle already operating with an accepted production-like baseline |
| OEM-SP in-vehicle service | Event detection, diagnostic-session logic and edge analysis |
| OEM-SP backend | Asynchronously synchronized incident state, short history, diagnostic report and after-sales workflow |
| Brake Health Operations Dashboard | Product and operational value visible outside the vehicle |
| IVI Display | Driver-facing state and warning |
| OEM Software Delivery Dashboard | Organizational and release lifecycle visible to the audience |
| AosCloud UI | Technical source-of-truth evidence used only for drill-down |
| Presenter Console | Hidden or secondary controls that make the live demonstration repeatable |

CARLA is not an Aos Unit. It is the simulated vehicle and data stimulus. The two
AosVM instances remain distinct, persistently provisioned vehicles with their
own identities and release states.

## Product Baseline Before the Post-SOP Feature

Both vehicles begin from one accepted demonstration baseline containing the
generic platform substrate, KUKSA, the basic vehicle-data capability and the
first OEM-SP service behavior.

The existing basic telemetry is sufficient to observe:

- vehicle speed;
- brake-pedal position;
- longitudinal acceleration;
- other already accepted motion signals.

Before the new feature is delivered, the system can detect and report an
emergency braking event, but it cannot produce a detailed brake-health report.
The visible product state is:

```text
Emergency braking event: detected
Detailed brake diagnostics: unavailable
Driver warning: not issued
```

This is a legitimate accepted baseline, not an artificially broken system. The
new post-SOP release extends it with a capability that did not previously
exist.

## Target Product Experience After the Post-SOP Feature

The new platform capability is provisionally named:

```text
vehicle.brake.health.v1
```

The name is a scenario-level placeholder until the capability contract is
reviewed. It represents the minimum vehicle-facing information required to
evaluate a simulated brake-condition issue, such as per-wheel behavior and
selected brake-component health information.

After the accepted FOTA and SOTA graph is installed, the visible product state
becomes:

```text
Emergency braking event: detected
Diagnostic monitoring: active
Brake condition: simulated anomaly detected
Local advisory decision: inspection recommended
Driver warning: displayed without Cloud connectivity
Local response time: measured from event to advisory, no Cloud round trip
Diagnostic report: queued locally or synchronized to OEM-SP backend
Recommended action: vehicle inspection
```

The first version is advisory. It does not autonomously modify a brake ECU.

## End-to-End Storyboard

### Act 0 — Pre-show preparation

This act is not presented as product behavior.

- Both provisioned vehicles are healthy and have the agreed demonstration
  baseline.
- CARLA, dashboards and backend are ready.
- Release artifacts used during the presentation are already built and staged;
  live build output is not part of the story.
- Validation and demonstration targeting is checked before any release action.
- The presenter can restore the story to its starting state without
  reprovisioning either Unit.

### Act 1 — Vehicle operating before the update

**Narrative:** this is an already released vehicle with an accepted feature set.

**Audience sees:**

- CARLA vehicle driving normally;
- production-like vehicle shown as `Online` and `Accepted baseline`;
- basic live driving data in the Brake Health Operations Dashboard;
- IVI in its normal state;
- OEM Software Delivery Dashboard showing no brake-health capability and the baseline OEM-SP
  service version.

### Act 2 — Emergency braking exposes a product limitation

**Narrative:** the existing service recognizes the event but lacks detailed
brake-condition data.

**Audience sees:**

- a deterministic emergency braking event in CARLA;
- an emergency-braking incident created in the OEM-SP backend;
- the dashboard transition from `Normal` to `Emergency Braking Detected`;
- `Detailed brake diagnostics unavailable`;
- no misleading malfunction claim and no driver warning.

This act establishes the visible before-state and motivates the post-SOP
feature request.

### Act 3 — OEM platform capability development

**Narrative:** the OEM-SP requests detailed brake-health information. The
Vehicle Platform Team qualifies the missing capability independently of the
production OEM-SP service.

**Audience sees in the OEM Software Delivery Dashboard:**

- a versioned capability request owned by the OEM-SP;
- the production-like vehicle remaining on the accepted baseline;
- a new FOTA version targeting only the validation vehicle;
- platform conformance, security, recovery and regression gates;
- failed platform candidates, if shown, remaining immutable audit evidence;
- a qualified capability handoff containing contract version, provider version,
  digest, readiness and test evidence.

The main dashboards do not show a new customer feature yet. A platform
capability is necessary infrastructure, not the finished product.

### Act 4 — OEM-SP feature integration

**Narrative:** after the capability handoff, the OEM-SP independently updates
its in-vehicle Brake Health service.

**Audience sees:**

- a new SOTA service version installed on the validation vehicle;
- the capability and service becoming `Ready` in dependency order;
- the production-like vehicle remaining on the previous accepted graph;
- the same emergency braking event repeated on the validation vehicle;
- diagnostic monitoring becoming active;
- brake-condition information appearing in the dashboard;
- the in-vehicle service detecting a simulated anomaly and making the advisory
  decision locally;
- an IVI warning appearing on the validation vehicle without waiting for the
  OEM-SP backend;
- the diagnostic report being queued locally while offline or synchronized
  asynchronously while connected.

A service defect creates a new SOTA version without a platform rebuild. A
confirmed platform defect returns to the Vehicle Platform Team and creates a
new FOTA version and capability handoff. An unchanged compatible SOTA artifact
is retested rather than rebuilt without reason.

### Act 5 — Formal feature acceptance

**Narrative:** the OEM accepts one exact combined graph, not merely the latest
version labels.

**Audience sees in the OEM Software Delivery Dashboard:**

- platform qualification passed;
- OEM-SP integration passed;
- runtime scenario passed;
- restart, source-loss, recovery and rollback checks passed;
- exact FOTA and SOTA versions and digests frozen;
- one accepted release identity eligible for promotion.

### Act 6 — Production-like promotion

**Narrative:** the accepted post-SOP feature is delivered to a vehicle already
in operation.

**Audience sees:**

- the demonstration vehicle still on the old graph before approval;
- the exact accepted FOTA items installed in dependency order;
- the exact accepted SOTA item installed only after capability readiness;
- no rebuild, repackaging, reprovisioning or Unit-identity change;
- the validation and demonstration vehicles reporting the same accepted graph.

### Act 7 — Emergency braking after the update

**Narrative:** the same operational event now produces a materially improved
outcome even when the vehicle has no Cloud connectivity.

**Audience sees:**

1. the Production-like Vehicle is deliberately shown as `Offline` in the
   Brake Health Operations Dashboard before the event;
2. the CARLA vehicle brakes sharply;
3. the in-vehicle service detects the event and starts diagnostic monitoring;
4. wheel and brake-condition information is analyzed locally;
5. a clearly labeled simulated anomaly is detected locally;
6. the in-vehicle service decides that inspection should be recommended;
7. the IVI displays the service-inspection warning without contacting the
   Cloud;
8. the audience can see the measured local elapsed time from the emergency
   braking event to the advisory and IVI warning;
9. the diagnostic report remains securely queued in the vehicle;
10. connectivity is restored;
11. the report synchronizes to the OEM-SP backend and the Brake Health
    Operations Dashboard opens the incident with its original event time;
12. existing basic telemetry and the accepted vehicle behavior remain healthy.

This is the final before-and-after proof of the demonstration.

### Optional Act 8 — Independent correction or rollback

This act is an engineering appendix rather than part of the shortest executive
story.

- Show a service-only correction that changes SOTA but leaves FOTA unchanged;
  or
- show a confirmed platform correction that changes FOTA and handoff while a
  compatible SOTA artifact remains unchanged; or
- roll back in reverse dependency order and prove that the original accepted
  vehicle behavior remains healthy.

Only one optional branch should be shown in a live presentation unless the
audience explicitly requests a technical deep dive.

## Runtime Incident State Model

The in-vehicle decision state is authoritative for the immediate driver
advisory:

```text
Normal
  -> Emergency Braking Detected
      -> Diagnostic Monitoring Active
          -> No Anomaly Detected -> Incident Closed
          -> Simulated Anomaly Detected
              -> Local Advisory Decision
                  -> IVI Warning Displayed
                      -> Vehicle Inspection Recommended
                          -> Report Queued for Synchronization
```

The out-of-vehicle state is eventually synchronized and must not control the
local decision:

```text
Vehicle Offline / Report Pending
    -> Connectivity Restored
        -> Report Synchronized
            -> Backend Incident Created or Updated
                -> Vehicle Health Operations Specialist Notified
```

Every state transition must have one visible timestamp and one source. The
backend must preserve the original in-vehicle event time rather than replace it
with the later synchronization time. Raw container logs may support drill-down
but are not the primary proof.

## Visible Surfaces

### CARLA Vehicle View

Purpose: make the trigger physically understandable.

Must show:

- normal driving before the event;
- a repeatable emergency braking event;
- continued operation after the event;
- which logical vehicle is currently connected to the scenario.

It does not need camera, LiDAR or media streaming.

### Brake Health Operations Dashboard

Purpose: show the OEM-SP product value and the out-of-vehicle incident view.

Minimum visible information:

- vehicle role: `Validation Vehicle` or `Production-like Vehicle`;
- connectivity and data freshness;
- current incident state;
- event timeline;
- speed, brake request and longitudinal deceleration around the event;
- diagnostic monitoring status;
- available wheel and brake-condition information;
- clearly labeled simulated anomaly result;
- measured local event-to-advisory time, derived from in-vehicle timestamps;
- report synchronization state and original in-vehicle event time;
- locally decided driver-notification state as reported by the vehicle;
- recommended next action;
- active OEM-SP feature version.

The default view should explain the scenario without requiring a log terminal.
When the vehicle is disconnected, it must show `Offline` and the last known
state; it must not fabricate the locally pending incident before synchronization.

### In-Vehicle IVI Display

Purpose: show the driver-visible outcome.

Required states:

- normal;
- emergency braking acknowledged, if a transient indication is useful;
- brake inspection warning;
- warning cleared or acknowledged.

The warning must be factual and non-alarming. It must identify the issue as a
simulated brake-condition finding and recommend inspection rather than claim an
unverified real-world failure. It is driven by the in-vehicle OEM-SP service
through an accepted local interface and must not wait for a Cloud round trip.

### OEM Software Delivery Dashboard

Purpose: show the independent internal OEM lifecycles without exposing the
audience to implementation commands.

Minimum visible information:

- Validation Vehicle and Production-like Vehicle as separate lanes;
- accepted baseline on both vehicles;
- OEM-SP capability request;
- Vehicle Platform Team FOTA qualification state;
- capability handoff identity and readiness;
- OEM-SP SOTA integration state;
- formal acceptance gate;
- exact accepted release identity;
- production-like promotion state;
- proof that the demonstration vehicle does not change before promotion.

Artifact digests, Cloud object identifiers and detailed test evidence belong in
expandable drill-down, not the primary presentation surface.

### Presenter Console

Purpose: make the demonstration safe and repeatable.

Potential controls, subject to later design:

- select the validation or demonstration vehicle;
- start or stop the scenario environment;
- put the CARLA vehicle in the required driving mode;
- trigger the deterministic emergency-braking setup;
- disconnect and restore vehicle Cloud connectivity without stopping local
  vehicle processing;
- advance an already authorized release step;
- inject an approved source-loss or network-loss condition;
- return to the known pre-show state.

This is not an OEM product dashboard and should normally remain hidden or
secondary.

### AosCloud UI

Purpose: provide technical source-of-truth evidence at selected moments.

It may be opened to confirm Unit identity, installed component or service
version, update state and reported health. It should not be the main narrative
surface because the audience should not need to interpret low-level platform
objects to understand the feature.

## OEM-SP Backend Role

The backend is part of the OEM-SP product, not an external third party. It
should make the out-of-vehicle value visible while preserving the in-vehicle
service boundary.

It should conceptually:

1. receive already timestamped emergency-braking events, diagnostic results and
   bounded aggregates from the in-vehicle service when connected;
2. create or update a brake incident without changing the original event time;
3. retain a short, audience-visible incident history;
4. support after-sales or vehicle-health follow-up after the local advisory;
5. expose synchronized incident state to the Brake Health Operations Dashboard;
6. distinguish `Live`, `Delayed`, `Offline` and `Report Pending` states where
   those states are known;
7. tolerate duplicate delivery when the vehicle retries synchronization.

The backend must not bypass the architecture by reading CARLA, VISS or KUKSA
directly. Vehicle data reaches it through the deployed OEM-SP service. Its own
cloud deployment lifecycle may be represented later, but it is not the focus
of the first vehicle OTA demonstration.

The backend is explicitly not responsible for:

- detecting the emergency braking event in real time;
- starting the local diagnostic analysis;
- deciding whether the driver should be warned;
- sending a time-critical command back to the vehicle;
- keeping the local feature operational while connectivity is absent.

Those responsibilities stay inside the vehicle. The backend adds history,
cross-session analysis and operational follow-up without becoming a runtime
availability dependency.

## Safety and Actuation Boundary

The first scenario version ends with a diagnostic report, driver warning and
inspection recommendation.

It does not:

- automatically change brake ECU parameters;
- actuate braking, steering or acceleration from the backend;
- depend on a Cloud response before showing the local advisory;
- claim production diagnostic accuracy;
- present simulated component data as real measured hardware data;
- broaden service permissions dynamically to make the scenario pass.

A future extension may show a **simulated corrective calibration proposal** in
state `Awaiting OEM approval`. Applying it even to a virtual ECU requires a
separate actuation contract, authorization model, validation, rollback design
and explicit scenario approval.

## Audience-Visible Success Criteria

The scenario is successful only when the audience can observe that:

1. the vehicle is already operational before the update;
2. the baseline detects emergency braking but cannot perform detailed brake
   diagnostics;
3. the validation vehicle receives the platform capability before the OEM-SP
   service update;
4. the production-like vehicle remains unchanged during validation;
5. the accepted graph is promoted without rebuilding or reprovisioning;
6. the same emergency event after promotion starts diagnostic monitoring;
7. local analysis and the IVI inspection warning complete while the vehicle is
   disconnected from the Cloud;
8. the local event-to-advisory time is observable and does not include a Cloud
   request or response;
9. a clearly labeled simulated anomaly is retained as a local report;
10. the report synchronizes to the OEM-SP backend after connectivity returns
   while preserving its original event time;
11. existing telemetry and local vehicle behavior remain available;
12. the story can be understood without reading raw logs.

## Scenario Decisions Still Open

These are product and presentation decisions, not yet technical tasks:

1. What deterministic CARLA event creates emergency braking: an obstacle,
   controlled traffic interaction, or presenter-triggered event?
2. Which simulated brake-condition anomaly is easiest to understand without
   making a false safety claim?
3. Which minimum wheel and brake information should be visible to the audience?
4. What exact driver-warning wording and acknowledgment behavior are used?
5. Who is the primary user of the Brake Health Operations Dashboard: OEM
   engineering, warranty/after-sales, or a connected-services operations team?
6. Should the shortest story include the `No Anomaly Detected` branch?
7. Which one correction or rollback branch, if any, belongs in the live demo?
8. What is the target duration for executive and technical versions of the
   presentation?
9. Which release steps are performed live and which are pre-staged while still
   being backed by real accepted artifacts and state?
10. Is a simulated corrective-calibration proposal useful, or should all
    actuation remain completely outside the current demonstration?
11. What audience-visible local response-time expectation demonstrates the
    advantage of in-vehicle analysis without prematurely selecting a technical
    latency SLO?
12. How should the dashboard distinguish original event time, local decision
    time and later backend synchronization time?

## Deferred Technical Decomposition

Only after the scenario, visible states, dashboards and open product decisions
are reviewed should the team decompose the work into:

- CARLA changes and deterministic scenario control;
- vehicle signal and capability contracts;
- platform providers and FOTA components;
- OEM-SP in-vehicle service and SOTA package;
- OEM-SP backend and dashboard;
- IVI display integration;
- OEM Software Delivery Dashboard and presenter controls;
- Cloud objects, release orchestration and acceptance automation;
- tests, evidence, repositories and milestones.

No item in this section is authorized for implementation by this document.

## Current Stop Point

The scenario is ready for product and presentation review. The next work is to
resolve its visible steps, dashboard content, warning language, simulated
anomaly and live presentation boundaries. Technical decomposition and changes
to the implementation roadmap remain deferred until that review is explicitly
accepted.
