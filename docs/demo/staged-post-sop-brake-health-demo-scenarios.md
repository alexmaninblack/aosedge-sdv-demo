<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Staged Post-SOP Brake Health Demo Scenarios

- Status: Accepted demo scenario baseline
- Version: 1.0
- Accepted: 2026-08-16
- Scope: audience-visible capability evolution, release sequence, dashboards,
  observability, and reset behavior
- Architecture mapping: separate next gate; not part of scenario acceptance
- Implementation, build, signing, Cloud, or Unit mutation authorized: no

## Purpose

This document defines a short sequence of connected demonstration scenarios.
Together they show how a vehicle that was produced with an integrated AosEdge
platform can gain new vehicle-data and Brake Health capabilities after SOP.

The scenarios deliberately start with a working vehicle rather than a broken
or incomplete prototype. The vehicle drives, exposes telemetry through its
Vehicle Gateway, and contains an operational Domain Controller with the
AosEdge platform substrate. What is initially absent is the vehicle-specific
data capability and the functional service that will use it.

This accepted scenario baseline defines what should happen and what an audience
should see. It does not yet map every step to the accepted High-Level
Architecture, select exact APIs, or authorize implementation.

## Core Demonstration Claim

The vehicle software architecture is prepared for post-SOP evolution because
AosEdge is integrated into the vehicle platform before SOP and produced
vehicles already contain the required generic lifecycle and execution
substrate.

Consequently, the OEM can later deliver versioned platform capabilities by
FOTA and independently deliver functional services by SOTA without
reprovisioning the vehicle, changing its identity, or redesigning the software
architecture established for SOP.

The demonstration does not claim that no software ever changes after SOP. Its
claim is that post-SOP functionality is added through the extension and
lifecycle mechanisms intentionally built into the SOP platform.

## Demonstration Roles and Terms

| Term | Meaning in this demonstration |
| --- | --- |
| Virtual Vehicle | CARLA vehicle dynamics, environment, sensors, and actuators |
| Vehicle Gateway | `carla-ego-runtime`, VSS normalization, VISS endpoint, and vehicle-side status |
| Domain Controller | QEMU plus AosVM representing a separate vehicle ECU |
| Platform substrate | AosCore, Service Manager, KUKSA, generic component runtime, security, and update support present from SOP |
| Vehicle Data Provider | FOTA-owned platform component that exposes an approved subset of vehicle data to KUKSA |
| Brake Health Function Team | OEM functional vertical that owns the Brake Health service, model, backend, dashboard, and SOTA lifecycle |
| Validation Unit | Persistent engineering AosVM used for qualification and integration |
| Demonstration Unit | Persistent production-like AosVM used as the promotion target after acceptance |

The Demonstration Unit is not presented as a real production vehicle or fleet.
It is the controlled production-rollout proxy available in the demo
environment.

## Audience-Visible Surfaces

### CARLA Visual Vehicle Scene

CARLA is the primary visual anchor of the demonstration. The audience sees a
vehicle driving through a virtual city while the software graph changes across
the five stages. Release dashboards explain what software is being delivered;
CARLA proves that the story still concerns a live, operating vehicle.

The visual scene must include one short, repeatable emergency-braking
scenario:

1. the vehicle starts from a known location and follows a fixed route;
2. a controlled obstacle or stopped actor appears at a known point;
3. the vehicle performs a deterministic hard-braking maneuver without an
   unintended collision;
4. the audience sees the vehicle decelerate in the CARLA scene;
5. the Engineering Telemetry Dashboard simultaneously shows the brake request,
   speed reduction, and longitudinal deceleration;
6. the same stimulus can be replayed against different software graphs so that
   any changed Brake Health result comes from the deployed capability, not
   from a different driving event.

The CARLA scenario controller, vehicle controller, or accepted safety behavior
creates the braking stimulus. The Brake Health service only observes and
analyzes the resulting signals; it does not command the vehicle to brake or
create the obstacle.

### Engineering Telemetry Dashboard

The existing engineering dashboard subscribes directly to the Vehicle Gateway
VISS endpoint. It initially proves that the physical simulation and Gateway
telemetry are working even when no data reaches the Domain Controller.

The dashboard shows existing vehicle telemetry such as speed, longitudinal
acceleration, pedals, and steering. In the final scenario it is extended to
show the Brake Health advisory request and the Vehicle Gateway reception
status.

It is an engineering demonstration tool, not an IVI, Instrument Cluster, or
production driver HMI.

### OEM Software Delivery Dashboard

A small purpose-built dashboard should present the OEM release lifecycle in a
form that is easier to understand than the complete AosCloud UI. It is a
presentation and orchestration view over real AosCloud state and APIs; it must
not invent or cache authoritative release state independently.

Its primary view should show:

- Validation and Demonstration Unit lanes;
- current and target platform and service versions;
- exact artifact identities and compact digest evidence;
- download, install, activation, readiness, validation, and promotion states;
- the effective target Units before an approval is accepted;
- `Waiting for validation`, approval, rejection, and accepted-release states;
- concise qualification results with optional technical drill-down;
- provider and service log availability.

The normal presentation uses this dashboard. The original AosCloud UI remains
available for technical source-of-truth drill-down.

### Brake Health Function Dashboard

This dashboard belongs to the Brake Health Function Team. It receives data
from the team's backend, not directly from CARLA, VISS, KUKSA, or AosCloud.

Across the scenarios it evolves from no available vehicle data, to selected
telemetry, to richer Brake Health inputs and prediction results. Backend data
is not part of the time-critical local advisory path.

### Vehicle and Service Log View

AosEdge provides system and service log collection and Cloud transmission
mechanisms. The demonstration should expose selected structured provider and
service logs through the configured Cloud-to-ELK integration.

`ELK` is the traditional name for the log-analysis stack composed of:

- **Elasticsearch** — stores and indexes log records for search;
- **Logstash** — optionally receives, transforms, and forwards log records;
- **Kibana** — provides the web interface for searching and visualizing the
  indexed logs.

Modern installations may use Elastic Agent, Beats, or another collector
instead of Logstash, but `ELK` remains a commonly used shorthand for the
centralized Elastic logging and visualization environment.

The ELK view should be filtered by Unit, component or service identity,
version, severity, and timestamp. It should show useful lifecycle and runtime
events without turning raw logs into the main proof of correct behavior.

ELK contains operational evidence such as provider startup, service readiness,
errors, and processing decisions. It is not the transport or source of vehicle
telemetry, and it is not the Brake Health Function Backend.

Direct ELK delivery is treated as a deployment integration of the available
AosEdge logging pipeline, not as an unverified claim that every AosEdge
deployment includes an identical ELK backend. Offline retention and retry
semantics must be verified before the demo claims them.

## Release Graph Overview

| Stage | Accepted graph after the stage | New capability |
| --- | --- | --- |
| 1 | `G0 = platform substrate` | Working vehicle and update-ready Domain Controller, but no vehicle provider or Brake Health service |
| 2 | `G1 = Provider v1` | First read-only subset of vehicle telemetry becomes available in KUKSA |
| 3 | `G2 = Provider v1 + Service v1` | Selected data reaches the Brake Health Function Backend and Dashboard |
| 4 | `G3 = Provider v2 + Service v2` | Additional signals support a richer Brake Health model and prediction output |
| 5 | `G4 = Provider v3 + Service v3` | Local inference can return an allowlisted advisory request to the Vehicle Gateway |

Every graph is composed of immutable, versioned artifacts. Promotion uses the
same accepted bytes and digests that passed validation; it does not rebuild or
repackage them during the presentation.

## Stage 1 — SOP-Ready Vehicle Without Feature Components

### Starting state

The complete demonstration environment is running:

- CARLA drives the virtual vehicle through the city;
- the Vehicle Control UI can use manual or autopilot mode;
- the Vehicle Gateway publishes live VISS telemetry;
- the Engineering Telemetry Dashboard displays that telemetry;
- the Validation and Demonstration Units retain their provisioned identities;
- the Domain Controller contains AosCore, Service Manager, KUKSA, the generic
  component runtime, security integration, and update support.

The following feature-specific elements are absent:

- no Vehicle Data Provider is installed;
- no live vehicle values are published into KUKSA;
- no Brake Health service is installed;
- no vehicle data reaches the Brake Health Function Backend.

### Audience-visible proof

```text
CARLA -> Vehicle Gateway -> VISS -> Engineering Telemetry Dashboard
                                  X
                                  no provider path to KUKSA
```

The audience sees a fully operational vehicle and an online, update-ready
Domain Controller. The absence of the new capability is explicit and is not
presented as a platform failure.

## Stage 2 — Platform Team Delivers Provider v1

### Capability

Provider v1 exposes a small, read-only subset of already available vehicle
telemetry to KUKSA. The provisional subset is:

- vehicle speed;
- longitudinal acceleration;
- brake-pedal position;
- accelerator-pedal position.

The exact contract is a later design decision.

### Release flow

1. The Platform Team publishes immutable Provider v1 through the FOTA
   lifecycle.
2. A new verification batch targets only the Validation Unit.
3. The OEM Software Delivery Dashboard shows the effective target Unit before
   approval.
4. Provider v1 is installed and activated on the Validation Unit.
5. Platform qualification verifies signal mapping, filtering, KUKSA
   publication, security, restart, source loss, recovery, and rollback.
6. Selected provider lifecycle and runtime logs become available through the
   AosEdge logging pipeline and the configured ELK view.
7. Validation is explicitly approved.
8. The same Provider v1 artifact is promoted to the Demonstration Unit.

### Audience-visible proof

- Provider v1 is absent from the Demonstration Unit during validation.
- The Validation Unit reports Provider v1 as ready.
- KUKSA receives only the approved v1 signal subset.
- No functional service consumes the data yet.
- The Demonstration Unit receives the exact accepted artifact only after
  approval.

Provider v1 is a platform capability, not a finished customer feature.

## Stage 3 — Function Team Delivers Service v1

### Capability

Service v1 is a deliberately simple KUKSA consumer. It reads the Provider v1
subset and sends a bounded, demo-appropriate stream to the Brake Health
Function Backend. The Function Dashboard visualizes the received data and its
freshness.

This version performs no predictive diagnostics and does not request an
advisory.

### Release flow

1. The Brake Health Function Team publishes immutable Service v1 through the
   SOTA lifecycle.
2. Service v1 declares a dependency on the Provider v1 capability.
3. Service v1 is installed first on the Validation Unit.
4. Integration validation proves the KUKSA-to-service-to-backend path.
5. Service logs become available through the configured AosEdge log pipeline
   and ELK view.
6. The exact accepted Service v1 artifact is promoted to the Demonstration
   Unit.

### Audience-visible proof

- AosCloud remains the software lifecycle system.
- The Brake Health Function Backend is a separate functional data system.
- The Function Dashboard receives data only through the deployed service.
- Removing or stopping Service v1 does not remove Provider v1 or the existing
  Engineering Telemetry Dashboard path.

## Stage 4 — Expanded Inputs and Predictive Service v2

### Feature request

After working with the initial data, the Brake Health Function Team determines
that a richer model needs additional vehicle information that exists on the
vehicle side but is not part of Provider v1.

The Function Team sends the Platform Team a versioned capability request with
the required signals, quality constraints, timing expectations, and acceptance
criteria.

### Candidate input expansion

The provisional Provider v2 inputs may include:

- per-wheel speed and wheel-speed asymmetry;
- brake demand or simulated brake pressure;
- measured deceleration relative to brake demand;
- emergency-braking or ABS activation state;
- estimated brake temperature;
- cumulative braking-energy or pad-wear proxy.

Signals not produced by CARLA as real sensors must be clearly labelled as
simulated or estimated. The demo must not imply production diagnostic accuracy.

### Release flow

1. The Platform Team develops Provider v2 as a backward-compatible superset of
   Provider v1.
2. Provider v2 is installed on the Validation Unit through FOTA.
3. The Platform Team independently completes platform qualification.
4. The Brake Health Function Team installs Service v2 through SOTA on the same
   Validation Unit.
5. Service v2 declares a dependency on the Provider v2 capability.
6. Both teams perform joint integration and scenario validation.
7. The OEM accepts one exact `Provider v2 + Service v2` graph.
8. Provider v2 is promoted to the Demonstration Unit first; Service v1 remains
   operational against the backward-compatible v1 subset.
9. After Provider v2 reports ready, Service v2 is promoted to the
   Demonstration Unit.

### Model lifecycle

Data gathered during earlier work may be used by the Function Team to develop
and validate its model outside the live vehicle demonstration. The resulting
model is versioned and packaged with Service v2.

The live presentation demonstrates deterministic inference. It does not claim
that a useful predictive model was trained during the presentation.

### Audience-visible proof

- Provider v2 and Service v2 iterate independently before combined acceptance.
- Existing v1 behavior remains available while Provider v2 is installed.
- New Function Dashboard information appears only after both Provider v2 and
  Service v2 are ready.
- The dashboard identifies simulated signals and model output clearly.
- Provider and service logs can be inspected without relying on terminal
  output as the main narrative.

## Stage 5 — Bidirectional Advisory Capability

### Feature request

After validating the predictive behavior, the Brake Health Function Team asks
for a bounded vehicle-facing capability that can return an inspection advisory
request to the Vehicle Gateway.

The Platform Team produces Vehicle Data Platform Capability v3. At the
scenario level this is called Provider v3; its lower-level implementation may
use separate inbound and outbound providers.

### Release flow

1. Provider v3 adds a strictly allowlisted advisory actuator path and Gateway
   status feedback while preserving all accepted v1 and v2 inputs.
2. Provider v3 is installed and platform-qualified on the Validation Unit.
3. Service v3, containing the accepted local inference model, is installed on
   the Validation Unit.
4. Joint validation proves online, offline, failure, restart, and rollback
   behavior.
5. The exact `Provider v3 + Service v3` graph is accepted.
6. Provider v3 and then Service v3 are promoted in dependency order to the
   Demonstration Unit.

### Runtime flow

```text
vehicle signals
  -> KUKSA
  -> Brake Health Service v3
  -> local inference
  -> KUKSA advisory actuator target
  -> outbound platform provider
  -> Vehicle Gateway
  -> Gateway reception/status
  -> Engineering Telemetry Dashboard
```

The advisory is intended for a future driver-facing vehicle function, but the
demonstration implements no IVI or Instrument Cluster. It proves only that the
request reaches the Vehicle Gateway and that the Gateway publishes a factual
reception status.

### Offline proof

1. The Demonstration Unit loses Cloud connectivity while local vehicle
   processing remains active.
2. A deterministic CARLA braking scenario produces the required signal
   sequence.
3. Service v3 performs local inference without a Cloud request.
4. The advisory reaches the Vehicle Gateway.
5. The Engineering Telemetry Dashboard shows the advisory and Gateway status.
6. The functional report remains pending locally if the backend is
   unavailable.
7. After connectivity returns, the report synchronizes to the Function
   Backend and appears in the Function Dashboard with its original event time.

The demo does not claim `displayed to driver` or `driver acknowledged`.

## Deterministic CARLA Visual Scenario

The runtime demonstration requires a repeatable visual and physical stimulus
rather than random traffic behavior. A later design should select one
controlled scenario, for example:

1. the vehicle follows a known route at a bounded speed;
2. a scripted obstacle or stopped actor appears at a known location;
3. the vehicle performs a deterministic hard-braking maneuver;
4. the Gateway publishes the resulting brake request, speed, deceleration,
   wheel, and simulated brake-health signals;
5. the CARLA scene and Engineering Telemetry Dashboard make the maneuver
   visible at the same time;
6. the same scenario can be replayed before and after a software graph change.

The Brake Health service observes and analyzes the event. It does not control
vehicle motion or create the emergency-braking stimulus.

The scene must have a deterministic reset, bounded duration, fixed actor
placement, and a safe failure mode if the expected braking trigger does not
occur. Random city traffic may remain visible outside the controlled segment
only if it cannot change the event timing or outcome.

## Prebuilt Demo and Runtime Duration

All source changes, builds, model training, tests, artifact signing, and Cloud
uploads occur before the presentation. The live demo performs only:

- selection of the already staged immutable artifact;
- deployment to the intended Unit;
- visible validation and approval;
- promotion of the accepted artifact graph;
- deterministic runtime execution;
- optional connectivity loss and recovery;
- reset to the starting graph.

The final storyboard should define executive and technical variants with
explicit duration budgets. Long builds and raw terminal output are never part
of the normal audience flow.

## Reset to Initial State

The demonstration must have a repeatable reset to `G0` without Unit
reprovisioning:

1. remove or roll back functional services in reverse dependency order;
2. remove or roll back feature-specific platform providers;
3. retain AosCore, KUKSA, the generic runtime, Unit identity, certificates, and
   provisioning state;
4. clear only demo-generated functional backend incidents and dashboard state;
5. reset the deterministic CARLA scenario and its seed;
6. verify that the Engineering Telemetry Dashboard still shows base VISS
   telemetry while KUKSA has no live vehicle provider and no Brake Health
   service is running.

The supported Cloud mechanism for representing and restoring the component-
absent `G0` desired state must be proven before the scenario is accepted for a
live presentation.

## Consistency Decisions Already Accepted

1. The SOP vehicle contains the generic AosEdge platform substrate but no
   feature-specific provider or Brake Health service in `G0`.
2. `Validation Unit` and `Demonstration Unit` are used instead of claiming a
   real production vehicle or fleet.
3. Provider v2 is backward compatible with the Provider v1 contract.
4. Every service version is validated on the Validation Unit before promotion.
5. Joint validation completes before either side of a new combined graph is
   promoted to the Demonstration Unit.
6. A prepared model is delivered with the service; live operation performs
   local inference rather than presentation-time training.
7. The final advisory is visible only as a request and Gateway status in the
   Engineering Telemetry Dashboard; no driver HMI is implemented.
8. All artifacts are built and staged before the presentation.
9. Reset preserves the provisioned Unit identities and SOP platform substrate.

## Items Requiring Review Before Architecture Mapping

1. Confirm the exact Provider v1 and Provider v2 signal subsets.
2. Select the simulated brake degradation or anomaly and define how CARLA or
   the Vehicle Gateway generates its source values.
3. Decide whether Service v1 sends sampled raw values, bounded aggregates, or
   both to the Function Backend.
4. Confirm the AosEdge-to-ELK integration available in the current Cloud
   environment, including access control, retention, and offline behavior.
5. Define the minimum OEM Software Delivery Dashboard views and which approval
   actions may be initiated from it.
6. Define the versioned model identity and prediction result shown by Service
   v2 before advisory actuation is introduced.
7. Prove that a fresh verification batch shows only its intended Validation
   Unit before approval; never reuse a stale batch after Unit Set changes.
8. Prove that the demonstration can restore `G0` without deprovisioning either
   Unit.
9. Define the target duration for each stage and for the complete executive
   and technical flows.

No contradiction currently blocks the five-stage narrative. The open items
above constrain its implementation and its audience-visible claims; they do
not require changing the core `G0 -> G1 -> G2 -> G3 -> G4` progression.

## Reference Basis

- [High-Level Architecture 1.0](../architecture/high-level-architecture.md)
  defines the accepted system boundaries but is not yet mapped step by step in
  this draft.
- [AosEdge overview](https://docs.aosedge.tech/docs/aos-edge/) describes the
  Cloud-to-edge lifecycle and operational visibility model.
- [Monitor a Service](https://docs.aosedge.tech/docs/how-to/advanced-service-operation/monitor-service)
  documents Cloud-requested service and crash logs.
- [AosCore common infrastructure](https://docs.aosedge.tech/docs/aos-core/architecture/common-infrastructure/)
  documents log archiving, compression, and Cloud transmission support.

The superseded
[Post-SOP Emergency Braking and Predictive Brake Health scenario](post-sop-emergency-braking-demo-scenario.md)
is retained temporarily for traceability. It must not be treated as the current
scenario or implementation plan where it conflicts with Demo Scenario 1.0 or
accepted HLA 1.0 decisions.
