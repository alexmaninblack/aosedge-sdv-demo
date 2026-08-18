<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Staged Post-SOP Brake and Tire Health Demo Scenarios

- Status: Review candidate incorporating the accepted manufacturing,
  provisioning, and demo-retirement model
- Version: 1.2
- Prepared: 2026-08-18
- Owner: Demo Architecture
- Previous accepted version: 1.0, accepted 2026-08-16
- Scope: manufacturing output, end-of-line provisioning, audience-visible
  capability evolution, release sequence, dashboards, observability, and
  end-of-demo retirement
- Architecture alignment: dynamic staged projection of High-Level Architecture
  1.2; detailed API and sequence mapping remains a later design gate
- Accepted architecture decision: [ADR 0009](../architecture/decisions/0009-separate-release-decision-from-cloud-execution.md)
- Implementation, build, signing, Cloud, or Unit mutation authorized: no

## Purpose

This document defines one connected demonstration lifecycle. It begins with
two newly manufactured virtual vehicle computers, provisions them into
AosCloud, evolves their software capabilities after SOP, and retires the
disposable demonstration identities and VM state at the end of the run.

The post-SOP portion deliberately starts with a working vehicle rather than a
broken or incomplete prototype. The vehicle drives, exposes telemetry through
its Vehicle Gateway, and contains an operational Domain Controller with the
AosEdge platform substrate. What is initially absent is the Vehicle Data
Platform Capability payload and all functional SOTA services.

This Scenario 1.2 review candidate defines what should happen and what an
audience should see. It is the dynamic, stage-by-stage projection of the
capability-superset model in High-Level Architecture 1.2. It does not yet
select exact APIs, define every detailed interaction, or authorize
implementation.

## Core Demonstration Claim

The vehicle software architecture is prepared for post-SOP evolution because
AosEdge and the OEM-integrated Vehicle Data Provider component runtime are
integrated into the vehicle platform before SOP. Produced vehicles therefore
contain the lifecycle and execution substrate required to receive the
provider payload later without another rootfs change.

Consequently, after end-of-line provisioning the OEM can deliver versioned
Vehicle Data Platform capabilities by FOTA and independently deliver
functional services by SOTA without reprovisioning the vehicle, changing its
identity, or redesigning the software architecture established for SOP.

Provisioning and identity creation occur once at the beginning of each
demonstration run. No reprovisioning or identity replacement occurs during the
accepted `G0 -> G1 -> G2 -> G3 -> G4` post-SOP progression. End-of-demo
retirement is an outer demonstration-lab lifecycle, not an OTA rollback of an
in-field vehicle.

The demonstration does not claim that no software ever changes after SOP. Its
claim is that post-SOP functionality is added through the extension and
lifecycle mechanisms intentionally built into the SOP platform.

## Alignment With High-Level Architecture 1.2

High-Level Architecture 1.2 shows every capability that the target logical
vehicle architecture can host. This scenario defines when those deployable
capabilities are absent or present during `M0`, `M1`, `G0–G4`, and `R0`.

The current `G0–G4` narrative exercises the shared Vehicle Data Platform
Capability and Function Team 1 / Service Provider 1 Brake Health lifecycle.
Function Team 2 / Service Provider 2 and its Tire Health product remain valid
parts of the target HLA but are intentionally not deployed in the current
`G0–G4` Brake Health sequence. Their condition model, existing-signal inputs,
bounded reports/events, advisory proof, backend and dashboard are an
independent SOTA 2 extension. This separation does not authorize a Function
Team 2 request for another platform capability in
the current demo.

The Validation Unit and Demonstration Unit are two instances of the same
logical Domain Controller architecture. The demo currently has one visible
CARLA/Vehicle Gateway/VISS source. Detailed design must define selection or
deterministic replay against the two Unit roles and must not imply two
simultaneous simulated vehicles unless that topology is later implemented.

## Demonstration Roles and Terms

| Term | Meaning in this demonstration |
| --- | --- |
| Virtual Vehicle | CARLA vehicle dynamics, environment, sensors, and actuators |
| Vehicle Gateway | `carla-ego-runtime`, VSS normalization, VISS endpoint, and vehicle-side status |
| Domain Controller | QEMU plus AosVM representing a separate vehicle ECU |
| Official AosEdge release | Immutable upstream release from which the OEM platform image is reproducibly derived |
| OEM Demo Factory Image | Cloud-unprovisioned OEM image derived from the official AosEdge release; it contains the accepted component runtime but no provider payload, functional service, Unit registration, or Cloud-issued identity certificate |
| Platform substrate | AosCore, Service Manager, KUKSA, the accepted Vehicle Data Provider component runtime, security, and update support present from SOP |
| Vehicle Data Platform Capability | FOTA-owned provider payload and versioned contract that exposes an approved subset of vehicle data through KUKSA; stage names use the shorthand Provider v1–v3 |
| Brake Health Function Team | Function Team 1 / Service Provider 1: OEM functional vertical that owns the Brake Health service, model, backend, dashboard, and SOTA 1 lifecycle |
| Tire Health Function Team | Function Team 2 / Service Provider 2: independent peer OEM functional vertical that owns local tire-condition estimation, bounded Cloud reporting, inspection advisory, backend, dashboard, and SOTA 2 lifecycle |
| Service Provider identity | Function Team Cloud identity used to develop, sign, publish, version, and technically verify its own SOTA artifact; it does not authorize deployment to OEM Units |
| OEM authorization identity | Cloud identity used by the owning Platform or Function Team to record validation acceptance and deployment or promotion approval affecting OEM Units |
| AosCloud lifecycle control plane | Authoritative desired/reported actual state, batches, campaigns, recorded approvals, audit history, and update execution; it does not make an owning team's engineering release decision |
| Validation Unit | Freshly provisioned engineering AosVM for the current demo run, used for qualification and integration |
| Demonstration Unit | Freshly provisioned production-like AosVM for the current demo run, used as the promotion target after acceptance |
| Current demo session | Presentation-scoped association, not an Aos identity: session start time and local overlay roles before M1, then the Validation and Demonstration Unit IDs plus that time window |
| Demo retirement | Controlled Cloud deprovisioning and Unit deletion followed by disposal of the corresponding provisioned VM overlays |

The Demonstration Unit is not presented as a real production vehicle or fleet.
It is the controlled production-rollout proxy available in the demo
environment. Both Units are disposable simulation assets between complete
demo runs, but their identities remain stable throughout one `G0–G4` run.

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
5. the Engineering Telematics Dashboard simultaneously shows the brake request,
   speed reduction, and longitudinal deceleration;
6. the same stimulus can be replayed against different software graphs so that
   any changed Brake Health result comes from the deployed capability, not
   from a different driving event.

The CARLA scenario controller, vehicle controller, or accepted safety behavior
creates the braking stimulus. The Brake Health service only observes and
analyzes the resulting signals; it does not command the vehicle to brake or
create the obstacle.

### Engineering Telematics Dashboard

The existing engineering dashboard subscribes directly to the Vehicle Gateway
VISS endpoint. It initially proves that the physical simulation and Gateway
telemetry are working even when no data reaches the Domain Controller.

The dashboard shows existing vehicle telemetry such as speed, longitudinal
acceleration, pedals, and steering. In the target scenario set it is extended
to show typed Brake Health and Tire Health advisory requests and Vehicle
Gateway reception status.

It is an engineering demonstration tool, not an IVI, Instrument Cluster, or
production driver HMI.

### OEM Software Delivery Dashboard

A small purpose-built dashboard should present the OEM release lifecycle in a
form that is easier to understand than the complete AosCloud UI. It is a
presentation and orchestration view over real AosCloud state and APIs; it must
not invent or cache authoritative release state independently.

Its primary view should show:

- the current demo session and manufacturing/provisioning state;
- Validation and Demonstration Unit lanes;
- current and target platform and service versions;
- exact artifact identities and compact digest evidence;
- download, install, activation, readiness, validation, and promotion states;
- the effective target Units before an approval is accepted;
- `Waiting for validation`, approval, rejection, and accepted-release states;
- the owning Platform or Function Team, Service Provider publication identity,
  active OEM authorization role, and exact action awaiting confirmation;
- concise qualification results with optional technical drill-down;
- provider and service log availability.

The dashboard must distinguish active state from retained audit history. Before
provisioning, it identifies the current session by its start time and the two
local overlay roles. After M1, it binds that view to the Validation and
Demonstration Unit IDs and the same time window. Unit deprovisioning and
deletion do not imply erasure of Cloud audit records. No separate
architecture-level run identifier is required; an internal correlation UUID
remains an optional dashboard implementation detail.

The dashboard and orchestrator do not store authoritative lifecycle state and
do not turn passing qualification evidence into approval. Every mutation
affecting an OEM Unit requires an explicit confirmation from the owning team
and is submitted through an authorized OEM identity; the resulting AosCloud
record remains authoritative after the local tools exit.

The normal presentation uses this dashboard. The original AosCloud UI remains
available for technical source-of-truth drill-down.

### Brake Health Function Dashboard

This dashboard belongs to the Brake Health Function Team. It receives data
from the team's backend, not directly from CARLA, VISS, KUKSA, or AosCloud.

Across the scenarios it evolves from no available vehicle data, to selected
telemetry, to richer Brake Health inputs and prediction results. Backend data
is not part of the time-critical local advisory path.

### Tire Health Function Dashboard — Independent SOTA 2 Extension

High-Level Architecture 1.2 assigns a separate backend and dashboard to
Function Team 2 / Service Provider 2. They are not audience-visible surfaces
in the current `G0–G4` Brake Health sequence. The independent Tire Health
extension will show an estimated condition band, threshold event, service and
platform versions, Unit role, and online/offline delivery state. It must not
display hidden simulation truth as a measured production vehicle value or
couple its data plane to the Brake Health backend.

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

| Stage | Accepted state after the stage | New capability |
| --- | --- | --- |
| M0 | `F0 = OEM Demo Factory Image` | Two fresh unprovisioned Domain Controller VM overlays exist; no Cloud Units or credentials exist |
| M1 | `G0 onboarding complete` | Validation and Demonstration Units have unique identities, certificates, roles, and Cloud connectivity |
| 1 | `G0 = platform substrate` | Working vehicle and update-ready Domain Controller, but no vehicle provider or Brake Health service |
| 2 | `G1 = Provider v1` | First read-only subset of vehicle telemetry becomes available in KUKSA |
| 3 | `G2 = Provider v1 + Service v1` | Selected data reaches the Brake Health Function Backend and Dashboard |
| 4 | `G3 = Provider v2 + Service v2` | Additional signals support a richer Brake Health model and prediction output |
| 5 | `G4 = Provider v3 + Service v3` | Local inference can return an allowlisted advisory request to the Vehicle Gateway |
| R0 | `Retired demo run` | Cloud identities are retired and provisioned overlays are discarded; the immutable factory image remains |

Every graph is composed of immutable, versioned artifacts. Promotion uses the
same accepted bytes and digests that passed validation; it does not rebuild or
repackage them during the presentation.

The graph table describes the Function Team 1 Brake Health progression.
Function Team 2's Tire Health service, backend, and dashboard remain absent
throughout the `G0–G4` sequence and receive a separate SOTA 2 extension flow.

One additional negative-path scenario is part of the target demo but deferred
from the current executable baseline: native AosCloud rejection of a SOTA
service whose required Vehicle Data Platform Capability version is absent.
When enabled, it runs at the beginning of Stage 4 while the Unit still has the
`G2` graph; it does not add another persistent graph state.

The audience-visible lifecycle moves forward only. Recovery and rollback may
be qualified before the presentation as engineering evidence, but the normal
demo does not move backward between `G0–G4` stages.

## M0 — Manufacturing Output

The immutable official AosEdge release is an upstream input, not the complete
vehicle-computer image manufactured by the OEM. Before SOP, the OEM integrates
and qualifies its platform layer to create the immutable **OEM Demo Factory
Image**.

The logical **OEM Factory Baseline Assembly** capability owns this build-time
composition, qualification and freeze process. Its output is the Factory Image
artifact; it does not run in the resulting Domain Controller.

That factory image contains:

- the official AosCore baseline;
- Service Manager, KUKSA, security, and update support;
- the accepted `systemd-slot-component` runtime for the Vehicle Data Provider;
- its launcher, health, systemd, storage, and SELinux integration;
- an empty provider component store.

It intentionally contains no:

- Vehicle Data Provider executable payload;
- functional SOTA service;
- Cloud Unit registration or Cloud-issued Node credentials;
- Unit certificate, KUKSA service token, or other per-vehicle secret;
- vehicle-specific mutable runtime state.

At the beginning of a demo run, two new copy-on-write VM overlays are created
from this immutable image. One represents the Validation vehicle computer and
one represents the Demonstration vehicle computer. The factory image itself
remains read-only and is never provisioned or modified.

Each new instance must establish distinct local system, Node, SSH, and network
identity before Cloud registration. The factory artifact must therefore retain
the qualified first-boot identity-generation mechanism rather than embedding a
fixed identity that would be duplicated by every overlay.

The current `.1` and `.2` installed rootfs versions prove that this runtime can
exist with an empty provider slot. Candidate `.11` adds the most complete
local hardening, but it is not yet the accepted factory image. A clean,
unprovisioned factory artifact must be frozen and qualified separately; no
provisioned VM snapshot may be used as its source.

The currently implemented runtime is specific to one Vehicle Data Provider
component type. This demo may claim independent versioning of that shared
Vehicle Data Platform Capability, but it must not claim support for arbitrary
new provider types without another platform/rootfs release until a generic
multi-type runtime is implemented and qualified.

### Audience-visible proof

- two newly manufactured Domain Controller instances exist locally;
- neither instance is registered as an AosCloud Unit;
- no Cloud registration, Cloud-issued certificate, provider payload, or
  functional service exists;
- the Software Delivery Dashboard identifies both instances as
  `Manufactured / Awaiting provisioning`.

## M1 — End-of-Line Provisioning

The manufacturing station provisions each fresh VM exactly once with the
official Aos provisioning SDK. Provisioning creates the Unit and Main Node,
registers the instance's unique identity, generates its certificates, and
enables secure Cloud connectivity. After both Units are Online:

1. one Unit is assigned to the Validation lane and its dedicated Unit Set;
2. one Unit is assigned to the Demonstration lane and its dedicated Unit Set;
3. the dashboard verifies the exact Unit identities and target membership;
4. both Units report the accepted platform/runtime inventory;
5. both provider stores remain empty and no functional service is assigned.

Provisioning must fail closed after the SDK begins: an uncertain partial
result is preserved for reconciliation and is never retried automatically.
Two factory overlays must be proven to generate different system, Node, SSH,
and certificate identities before live use.

### Audience-visible proof

- each vehicle computer changes from `Awaiting provisioning` to `Online`;
- the two Units have different identities and explicit roles;
- the Validation and Demonstration lanes are visibly separated;
- `G0` is reached with the runtime ready but provider and services absent.

## Stage 1 — SOP-Ready Vehicle Without Feature Components

### Starting state

The complete demonstration environment is running:

- CARLA drives the virtual vehicle through the city;
- the Vehicle Control UI can use manual or autopilot mode;
- the Vehicle Gateway publishes live VISS telemetry;
- the Engineering Telematics Dashboard displays that telemetry;
- the Validation and Demonstration Units have the fresh provisioned identities
  created during M1 and retain them throughout `G0–G4`;
- the Domain Controller contains AosCore, Service Manager, KUKSA, the accepted
  Vehicle Data Provider runtime, security integration, and update support.

The following feature-specific elements are absent:

- no Vehicle Data Platform Capability payload is installed;
- no live vehicle values are published into KUKSA;
- no Brake Health service is installed;
- no vehicle data reaches the Brake Health Function Backend;
- no Tire Health service is installed and no Tire Health result reaches the
  Function Team 2 backend.

### Audience-visible proof

```text
CARLA -> Vehicle Gateway -> VISS -> Engineering Telematics Dashboard
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
2. A fresh verification batch is created for the Validation lane; stale
   batches are never reused after Unit Set membership changes.
3. Immediately before approval, the OEM Software Delivery Dashboard derives
   the effective target from current Unit state and proves that only the
   Validation Unit references the pending batch. Any unexpected Unit blocks
   approval.
4. The Platform Team explicitly authorizes the Validation Unit deployment
   through its OEM identity; the dashboard and orchestrator cannot infer this
   approval from target checks.
5. Provider v1 is installed and activated on the Validation Unit.
6. Platform qualification verifies signal mapping, filtering, KUKSA
   publication, security, restart, source loss, and recovery.
7. Selected provider lifecycle and runtime logs become available through the
   AosEdge logging pipeline and the configured ELK view.
8. The Platform Team accepts the exact Provider v1 version, digest,
   qualification evidence, and target, and records promotion approval through
   its OEM identity.
9. AosCloud promotes the same Provider v1 artifact to the Demonstration Unit.

### Audience-visible proof

- Provider v1 is absent from the Demonstration Unit during validation.
- The Validation Unit reports Provider v1 as ready.
- KUKSA receives only the approved v1 signal subset.
- No functional service consumes the data yet.
- The Demonstration Unit receives the exact accepted artifact only after
  approval.

Provider v1 is a platform capability, not a finished customer feature.

## Stage 3 — Function Team 1 Delivers Brake Health Service v1

### Capability

Service v1 is a deliberately simple KUKSA consumer. It reads the Provider v1
subset and converts it into a bounded, low-rate functional report for the
Brake Health Function Backend. The report may contain selected samples and/or
aggregates, but it is not an unrestricted continuous raw-sensor stream. The
Function Dashboard visualizes the received data and its freshness.

This version performs no predictive diagnostics and does not request an
advisory.

### Release flow

1. The Brake Health Function Team publishes immutable Service v1 through its
   Service Provider 1 identity in the SOTA 1 lifecycle.
2. Service v1 declares a dependency on the Provider v1 capability.
3. The Function Team explicitly authorizes deployment to the Validation Unit
   through an OEM identity.
4. Service v1 is installed first on the Validation Unit.
5. Integration validation proves the KUKSA-to-service-to-backend path.
6. Service logs become available through the configured AosEdge log pipeline
   and ELK view.
7. Function Team 1 accepts the exact Service v1 artifact and integration
   result and records promotion approval through an OEM identity.
8. AosCloud promotes the exact accepted Service v1 artifact to the
   Demonstration Unit.

### Audience-visible proof

- AosCloud remains the software lifecycle system.
- The Brake Health Function Backend is a separate functional data system.
- The Function Dashboard receives data only through the deployed service.
- Removing or stopping Service v1 does not remove Provider v1 or the existing
  Engineering Telematics Dashboard path.

## Stage 4 — Expanded Inputs and Predictive Service v2

### Deferred native dependency-rejection prelude

This prelude is a planned part of the target demonstration, but it is not
executed with the current AosCloud release.

Starting from `G2`, the Validation Unit has Provider v1 and Service v1.
Function Team 1 submits the already prepared Service v2 candidate, which
declares that it requires Vehicle Data Platform Capability v2. The target
native behavior is:

1. AosCloud resolves the candidate's required capability range against the
   authoritative actual component state of the intended Validation Unit.
2. AosCloud observes Provider v1 rather than the required Provider v2.
3. AosCloud rejects the SOTA request before changing Subject-service desired
   state, creating a validation batch or campaign, or transferring update
   content to the Unit.
4. The OEM Software Delivery Dashboard shows the authoritative Cloud rejection
   reason, required range, actual version, service identity and target Unit.
5. The Validation Unit remains on the unchanged `Provider v1 + Service v1`
   graph.
6. The Platform Team then follows the normal Provider v2 FOTA flow below.
7. The identical Service v2 candidate is resubmitted after Provider v2 reports
   ready; the dependency check succeeds and Stage 4 continues normally.

The scenario is activated only after an official AosEdge release exposes the
Service-to-FOTA-component dependency in its supported Cloud API and signed
service metadata, and a disposable qualification proves all rejection
boundaries above. The project does not implement a temporary admission gate in
the Software Delivery Dashboard.

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
4. The Brake Health Function Team installs Service v2 through SOTA 1 on the
   same Validation Unit.
5. Service v2 declares a dependency on the Provider v2 capability.
6. Both teams perform joint integration and scenario validation.
7. The Platform Team accepts the exact Provider v2 artifact and qualification
   through an OEM identity. Function Team 1 separately accepts the exact
   Service v2 artifact, model, and joint integration result through an OEM
   identity.
8. AosCloud permits promotion only after both owner decisions are recorded for
   the same graph, digests, and targets.
9. Provider v2 is promoted to the Demonstration Unit first; Service v1 remains
   operational against the backward-compatible v1 subset.
10. After Provider v2 reports ready, Service v2 is promoted to the
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
3. Service v3, containing the accepted local inference model, is installed
   through SOTA 1 on the Validation Unit.
4. Joint validation proves online, offline, failure, restart, and recovery
   behavior.
5. The Platform Team accepts the exact Provider v3 artifact through an OEM
   identity, and Function Team 1 separately accepts the exact Service v3
   artifact and joint integration result through an OEM identity.
6. AosCloud permits promotion only after both decisions are recorded for the
   exact graph, digests, and targets.
7. Provider v3 and then Service v3 are promoted in dependency order to the
   Demonstration Unit.

### Runtime flow

```text
vehicle signals
  -> inbound Vehicle Interface Provider
  -> KUKSA actual-value namespace
  -> read / subscribe
  -> Brake Health Service v3
  -> local inference
  -> Brake Health advisory request through actuate / write target
  -> KUKSA advisory-target namespace
  -> outbound validation and allowlist
  -> outbound Vehicle Interface Provider
  -> VISS Set over the simulated in-vehicle network
  -> Vehicle Gateway advisory handler
  -> Gateway reception/status
  -> Engineering Telematics Dashboard
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
5. The Engineering Telematics Dashboard shows the advisory and Gateway status.
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
5. the CARLA scene and Engineering Telematics Dashboard make the maneuver
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
uploads occur before the presentation. The OEM Demo Factory Image and all
post-SOP artifacts are frozen before the presentation. The live demo performs
only:

- creation of two fresh overlays from the immutable factory image;
- controlled provisioning and assignment of the two new Units;
- selection of the already staged immutable artifact;
- deployment to the intended Unit;
- visible validation and approval;
- promotion of the accepted artifact graph;
- deterministic runtime execution;
- optional connectivity loss and recovery;
- retirement of the current demo run and reset of external demo data.

The final storyboard should define executive and technical variants with
explicit duration budgets. Long builds and raw terminal output are never part
of the normal audience flow.

## R0 — End-of-Demo Retirement and Next-Run Reset

The complete demo does not reverse the accepted software graph from `G4` to
`G0`. No artificial provider or rootfs rollback is part of the normal
presentation. Instead, the two simulated Domain Controller Unit instances
created for the current run are retired, and the next run represents two newly
manufactured vehicle computers.

The controlled retirement sequence is:

1. close, stop, or detach current-run assignments and campaigns as required by
   the accepted Cloud procedure;
2. stop both VM instances cleanly and prove that no QEMU process holds either
   overlay;
3. wait until AosCloud reports both Units as `Offline`;
4. invoke the accepted Cloud-side Unit deprovisioning operation;
5. prove that the retired identities and certificates cannot reconnect;
6. delete the corresponding Unit records through AosCloud; Nodes are treated
   as Unit-owned resources unless the qualified API flow explicitly requires
   a separate operation;
7. discard the two provisioned overlays and their run-specific host access
   state without modifying the immutable OEM Demo Factory Image;
8. clear or archive functional backend and dashboard data associated with the
   retired Validation and Demonstration Unit IDs and the current session time
   window, while retaining the authoritative Cloud audit history;
9. reset the CARLA scenario, actors, route, and deterministic seed;
10. begin the next run by creating two new overlays from the same accepted
    factory image and provisioning two new identities.

This is a demonstration-lab retirement workflow, not a production OTA factory
reset or a normal in-field vehicle rollback. The exact deprovision/delete
ordering, certificate invalidation behavior, Unit-owned Node cleanup, audit
retention, and failure recovery must be qualified first on disposable Units.
The existing Validation and Demonstration identities must not be used for that
destructive experiment.

## Consistency Decisions Already Accepted

1. The official AosEdge release is an upstream input; manufacturing uses a
   reproducibly derived OEM Demo Factory Image.
2. The factory image contains the accepted Vehicle Data Provider runtime but
   no provider payload, functional service, Cloud registration, Cloud-issued
   credential, or embedded reusable per-vehicle secret.
3. The current runtime supports one independently versioned Vehicle Data
   Platform Capability; arbitrary new provider types are not claimed.
4. `Validation Unit` and `Demonstration Unit` are used instead of claiming a
   real production vehicle or fleet.
5. Provider v2 is backward compatible with the Provider v1 contract.
6. Every service version is validated on the Validation Unit before promotion.
7. Joint validation completes before either side of a new combined graph is
   promoted to the Demonstration Unit.
8. A prepared model is delivered with the service; live operation performs
   local inference rather than presentation-time training.
9. The final Brake Health advisory is visible only as a request and Gateway
   status in the Engineering Telematics Dashboard; no driver HMI is
   implemented.
10. All factory and update artifacts are built and staged before the
    presentation.
11. Unit identities remain stable throughout `G0–G4`; the complete next-run
    reset retires those identities and creates new ones from fresh overlays.
12. High-Level Architecture 1.2 is a capability superset; the `G0–G4` sequence
    exercises Function Team 1 while Function Team 2 is added only through its
    independent Tire Health SOTA 2 extension.
13. Function Team 1 and Function Team 2 remain independent AosCloud Service
    Providers. Function Team 2 consumes the existing platform contract and
    does not request another capability in the current demo.
14. The current demo session is associated through the two Unit IDs and a time
    window after M1; no additional architecture identity is mandatory.
15. Native Cloud rejection of a SOTA service whose required FOTA capability is
    absent is a target demo scenario deferred until the AosEdge roadmap feature
    ships and is qualified. No project-specific admission controller is used.
16. The owning Platform or Function Team makes each engineering release
    decision. Function Teams publish through Service Provider identities, all
    approvals affecting OEM Units use authorized OEM identities, and AosCloud
    stores and executes the resulting lifecycle transition. The dashboard and
    orchestrator own neither approval nor lifecycle state.

## Items Requiring Resolution Before Detailed Flow Mapping

1. Freeze and qualify the Function Team 2 Tire Health scenario required by
   High-Level Architecture 1.2, including its existing signal subset,
   accelerated/pre-aged degradation model, persistent state, condition bands,
   bounded backend payload, advisory, hidden qualification truth, and dashboard
   proof.
2. Define how the single visible CARLA/VISS environment is connected or
   deterministically replayed for the Validation and Demonstration Units; do
   not imply two simultaneous simulated vehicles unless that is implemented.
3. Confirm the exact Provider v1 and Provider v2 signal subsets.
4. Select the simulated brake degradation or anomaly and define how CARLA or
   the Vehicle Gateway generates its source values.
5. Define the exact bounded Service v1 report contract: selected low-rate
   samples, aggregates, or both. Continuous unrestricted raw streaming is
   excluded.
6. Confirm the AosEdge-to-ELK integration available in the current Cloud
   environment, including access control, retention, and offline behavior.
7. Define the minimum OEM Software Delivery Dashboard views, explicit
   confirmation interaction, team-owner and active-role presentation, and the
   exact OEM-authorized actions that may be invoked without introducing local
   lifecycle state or automatic approval.
8. Define the versioned model identity and prediction result shown by Service
   v2 before advisory actuation is introduced.
9. Prove that a fresh verification batch shows only its intended Validation
   Unit before approval; never reuse a stale batch after Unit Set changes.
10. Freeze and qualify a clean, unprovisioned OEM Demo Factory Image with an
    empty provider store, no Cloud registration or credential, and no fixed
    identity that would be duplicated across instances.
11. Prove that two fresh overlays create different system, Node, SSH, and
    certificate identities.
12. Qualify Cloud deprovision, Unit deletion, old-certificate rejection, Node
    cleanup, retained audit history, and partial-failure recovery on disposable
    Units.
13. Measure sequential and, if later required, parallel provisioning enough
    times to define an honest audience-visible duration and timeout.
14. Define current-session naming, binding to the two Unit IDs and time window,
    Unit Set assignment, and external data-retention rules. An internal UUID is
    optional and is not an architecture identity.
15. Define the target duration for each stage and for the complete executive
    and technical flows.
16. When an implementing AosEdge release becomes available, qualify native
    Service-to-FOTA-component dependency declaration and rejection before any
    Subject-service desired-state change, validation batch, campaign, or Unit
    download, then enable the deferred Stage 4 prelude.

No contradiction with High-Level Architecture 1.2 remains after this alignment
review. The open items above constrain implementation and audience-visible
claims. They preserve the inner `G0 -> G1 -> G2 -> G3 -> G4` progression and
the outer `M0 -> M1` onboarding and `R0` retirement lifecycle.

## Reference Basis

- [High-Level Architecture 1.2](../architecture/high-level-architecture.md)
  defines the current capability-superset architecture review candidate; this
  scenario defines its staged component presence and lifecycle, while detailed
  API and interaction mapping remains a later deliverable.
- [AosEdge overview](https://docs.aosedge.tech/docs/aos-edge/) describes the
  Cloud-to-edge lifecycle and operational visibility model.
- [Monitor a Service](https://docs.aosedge.tech/docs/how-to/advanced-service-operation/monitor-service)
  documents Cloud-requested service and crash logs.
- [AosCore common infrastructure](https://docs.aosedge.tech/docs/aos-core/architecture/common-infrastructure/)
  documents log archiving, compression, and Cloud transmission support.
