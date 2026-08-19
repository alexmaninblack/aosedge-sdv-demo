<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# High-Level Architecture 1.4

- Status: Accepted architecture baseline
- Version: 1.4
- Prepared: 2026-08-19
- Accepted: 2026-08-19
- Owner: System Architecture
- Previous accepted version: 1.0, accepted 2026-08-16
- Accepted architecture decisions: [ADR 0008](decisions/0008-use-tire-health-for-function-team-2.md),
  [ADR 0009](decisions/0009-separate-release-decision-from-cloud-execution.md),
  [ADR 0010](decisions/0010-aos-kuksa-credential-broker.md),
  [ADR 0011](decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md)
- Scope: CARLA, Vehicle Gateway ECU, AosVM Domain Controller, AosCloud,
  shared Vehicle Data Platform Component, two independent OEM Service
  Providers, functional backends, and demonstration tooling
- Implementation status: target architecture; current and planned elements are
  distinguished below
- Cloud or Unit mutation authorized: no

## Visual Authoring Source

The reviewed visual source is preserved together with its matching export:

- [Draw.io source](diagrams/aosedge-demo-hla-authoring-reference.drawio);
- [PNG export](diagrams/aosedge-demo-hla-authoring-reference.png).

The Draw.io file is the primary visual architecture source. Its PNG export and
the Mermaid rendering below are reviewable derivatives and must be regenerated
or reconciled whenever the source changes.

The visual source defines the component boundaries and principal relationships
used by Architecture 1.4: two peer OEM Function Teams represented as
independent AosCloud Service Providers, the shared Vehicle Data Platform
Component, the Tire Health function, the Factory Baseline Assembly-to-Factory
Image artifact and factory-installed runtime boundaries,
the Software Delivery and log-observation surfaces, and the explicit typed
Brake Health and Tire Health advisory paths through KUKSA. It also distinguishes
team-owned release decisions from the OEM identity used to authorize Cloud
mutations and from AosCloud lifecycle state and execution. It also identifies
both functional services as QM-domain applications, the Gateway as the final
authoritative containment boundary, and OEM approval as an evidence-backed
final decision rather than a bare dashboard action. The diagram does not
introduce a production driver HMI; the advisory remains visible on the
Engineering Telematics Dashboard.

## Revision 1.4 Summary

Architecture 1.4 preserves the component and lifecycle topology of 1.3 and
adopts [ADR 0011](decisions/0011-qm-service-containment-and-evidence-backed-oem-approval.md):

1. Brake Health and Tire Health are QM-domain maintenance/inspection
   applications with no allocated safety goal or vehicle-motion authority;
2. the VDP outbound allowlist is defense in depth, while the Vehicle Gateway
   is the final authoritative boundary for the QM-origin channel and denies
   arbitrary VSS, motion and safety-critical operations;
3. an OEM deployment approval is the explicit conclusion of an engineering
   validation process, bound to the exact artifact and metadata digests,
   requested permissions, target, evidence and owning-team acceptance;
4. the Software Delivery Dashboard must show those prerequisites before its
   final approval control can be used; passing tests never auto-approve; and
5. the Dashboard remains stateless, while AosCloud records and executes the
   authorized decision.

## Revision 1.3 Summary

Architecture 1.3 preserves the component and lifecycle topology of 1.2 and
corrects the Aos-to-KUKSA credential authority as amended in
[ADR 0010](decisions/0010-aos-kuksa-credential-broker.md):

1. Aos Service Manager and IAM own per-instance `AOS_SECRET` creation,
   registration, lookup and invalidation;
2. the VDP-owned Credential Broker is only a fail-closed translator from
   currently registered IAM permissions to short-lived KUKSA JWTs;
3. no project-owned identity store or duplicate per-service OEM allowlist is
   added to the broker;
4. the Factory Image enables the stock Aos IAM permission handler and carries
   only the non-secret IAM/PKCS#11 integration seam for the broker signing
   key; per-Unit key material is established after manufacturing;
5. the privileged FOTA provider uses a separate short-lived platform
   credential, whose exact identity binding remains a qualification gate; and
6. native pre-transfer Cloud permission admission remains deferred until a
   released AosCloud capability is qualified.

## Revision 1.2 Summary

Architecture 1.2 retains the 1.1 platform and lifecycle model and replaces its
provisional Function Team 2 candidate, as accepted in
[ADR 0008](decisions/0008-use-tire-health-for-function-team-2.md):

1. defining Function Team 1 and Function Team 2 as independent peer OEM
   organizations and independent AosCloud Service Providers;
2. adding an independently delivered Tire Health SOTA service with its own
   backend and dashboard;
3. establishing the FOTA-owned Vehicle Data Platform Component as a shared
   vehicle integration layer used by multiple functional services;
4. separating continuous local condition estimation from bounded Tire Health
   summaries and threshold-event Cloud upload;
5. making each typed Brake Health or Tire Health advisory return explicitly
   pass through KUKSA, outbound validation, VISS Set, and the Vehicle Gateway;
6. limiting the current demo's platform feature-request flow to Function Team
   1, while Function Team 2 consumes the already available data contract;
7. distinguishing the build-time OEM Factory Baseline Assembly, its immutable
   pre-SOP OEM Demo Factory Image artifact, and the factory-installed runtime
   graph from the post-SOP FOTA capability payload;
8. adding the OEM Software Delivery Dashboard as the stateless engineering
   surface over authoritative AosCloud lifecycle state and native log APIs;
9. clarifying that the same logical Domain Controller architecture is
   instantiated separately as the Validation Unit and Demonstration Unit;
10. adopting [ADR 0009](decisions/0009-separate-release-decision-from-cloud-execution.md):
    each owning team makes its engineering release decision, an OEM identity
    authorizes deployment to OEM Units, and AosCloud remains the lifecycle
    system of record and execution control plane.
11. adopting [ADR 0010](decisions/0010-aos-kuksa-credential-broker.md):
    upstream Eclipse KUKSA remains unchanged, while the Vehicle Data Platform
    Component owns the thin Aos–KUKSA Credential Broker used to derive
    short-lived KUKSA JWTs from Aos IAM service-instance identity.

## Purpose

This document defines the high-level architecture for the AosEdge SDV
demonstration. It records the logical vehicle model, ECU and software
boundaries, OEM ownership and release lifecycles, runtime telemetry, event
upload and advisory paths, Cloud interactions, and engineering tooling.

The architecture demonstrates how an OEM can add a new vehicle-facing platform
capability through FOTA and then independently deliver multiple containerized
functional services through SOTA. The Brake Health service performs local
analysis and can return an advisory request to the Vehicle Gateway without a
Cloud round trip. Tire Health estimates condition locally and sends only
bounded summaries or threshold events to its functional backend; it can also
request a local inspection advisory without a Cloud round trip.

This is a logical automotive architecture. All elements currently run on one
Apple Silicon Mac for the demonstration, but process placement on the Mac must
not erase the logical separation between the simulated physical vehicle, the
Vehicle Gateway ECU, the Domain Controller ECU, the OEM Cloud, and engineering
tools.

## Architecture 1.4 Model

```mermaid
flowchart TB
    subgraph OEM["OEM"]
        direction LR

        subgraph PLATFORM_TEAM["Platform Team"]
            FACTORY_ASSEMBLY["OEM Factory Baseline Assembly<br/>compose · build · qualify · freeze"]
            PLATFORM_DEV["Development of Vehicle Data<br/>Platform Component"]
        end

        AOS_CLOUD(["AosCloud<br/>lifecycle system of record<br/>and execution control plane"])

        subgraph FUNCTION_TEAM_1["Function Team 1 / Service Provider 1 — SOTA"]
            BRAKE_DEV["Development of<br/>Brake Health Service"]
        end

        subgraph FUNCTION_TEAM_2["Function Team 2 / Service Provider 2 — SOTA"]
            TIRE_DEV["Development of<br/>Tire Health Service"]
        end

        BRAKE_BACKEND[("Service Provider 1<br/>Brake Health Backend")]
        BRAKE_DASHBOARD["Brake Health<br/>Function Dashboard"]
        TIRE_BACKEND[("Service Provider 2<br/>Tire Health Backend")]
        TIRE_DASHBOARD["Tire Health<br/>Function Dashboard"]

        BRAKE_DEV -. "Feature request:<br/>new or updated vehicle signals" .-> PLATFORM_DEV
        PLATFORM_DEV -- "OEM identity:<br/>publish + evidence-backed FOTA approval" --> AOS_CLOUD
        BRAKE_DEV -- "SP identity: publish SOTA 1<br/>OEM identity: evidence-backed approval" --> AOS_CLOUD
        TIRE_DEV -- "SP identity: publish SOTA 2<br/>OEM identity: evidence-backed approval" --> AOS_CLOUD
        BRAKE_BACKEND --> BRAKE_DASHBOARD
        TIRE_BACKEND --> TIRE_DASHBOARD
    end

    subgraph DEMO["Demo / Engineering Workstation — Mac host"]
        direction LR
        CONTROL_UI["Vehicle Control UI<br/>Manual · Autopilot · Safe Stop"]
        SOFTWARE_DASHBOARD["OEM Software Delivery Dashboard<br/>digest · permissions · target · validation evidence<br/>team acceptance · explicit final OEM approval"]
        TELEMETRY_DASHBOARD["Engineering Telematics Dashboard<br/>speed · acceleration · pedals · steering<br/>Brake + Tire Health advisory · gateway status"]
    end

    subgraph VEHICLE["Virtual Vehicle"]
        direction LR

        subgraph VIRTUAL_PLATFORM["Virtual Vehicle Platform — CARLA"]
            direction LR

            CARLA["CARLA Physical Vehicle<br/>dynamics · sensors · actuators"]

            subgraph GATEWAY["Vehicle Gateway ECU"]
                direction LR
                EGO_RUNTIME["carla-ego-runtime"]
                VSS_MODEL["Signal normalization<br/>and VSS data model"]
                VISS_SERVER["VISS 3.1 Server"]
                ADVISORY_HANDLER["Authoritative QM-channel handler<br/>typed non-safety advisory only<br/>deny motion and safety-critical operations"]

                EGO_RUNTIME --> VSS_MODEL --> VISS_SERVER
                VISS_SERVER -- "Set advisory target" --> ADVISORY_HANDLER
                ADVISORY_HANDLER -- "Publish received/status" --> VISS_SERVER
            end

            CARLA -- "Vehicle and sensor state" --> EGO_RUNTIME
            EGO_RUNTIME -- "Control commands" --> CARLA
        end

        NETWORK["Simulated In-Vehicle Network<br/>VSS semantics · VISS 3.1 · TLS/IP"]

        subgraph DOMAIN["Domain Controller ECU — QEMU + AosVM<br/>logical instance: Validation Unit or Demonstration Unit"]
            direction TB

            AOS_CORE["Factory-installed Domain Controller substrate<br/>AosCore · Service Manager · KUKSA<br/>security · update support"]
            COMPONENT_RUNTIME["Preinstalled component runtime<br/>provider-specific · empty slot"]

            subgraph DATA_PLATFORM["Vehicle Data Platform Component — FOTA payload and versioned contract"]
                direction TB

                subgraph INBOUND_PATH["Inbound vehicle-data path"]
                    direction LR
                    INBOUND["Vehicle Interface Provider<br/>VISS subscribe client"]
                    INBOUND_POLICY["Inbound validation<br/>normalization · signal selection"]
                    KUKSA_ACTUAL["KUKSA actual-value<br/>namespace"]
                    READ_API["Read / subscribe<br/>kuksa.val.v1"]

                    INBOUND --> INBOUND_POLICY
                    INBOUND_POLICY -- "Publish actual values" --> KUKSA_ACTUAL
                    KUKSA_ACTUAL --> READ_API
                end

                subgraph OUTBOUND_PATH["Outbound QM advisory path — defense in depth"]
                    direction RL
                    ACTUATE_API["Actuate / write target<br/>kuksa.val.v1"]
                    KUKSA_TARGET["KUKSA advisory-target<br/>namespace"]
                    OUTBOUND_POLICY["Outbound validation<br/>and allowlist"]
                    OUTBOUND["Outbound Vehicle Interface Provider<br/>VISS Set client"]

                    ACTUATE_API --> KUKSA_TARGET
                    KUKSA_TARGET --> OUTBOUND_POLICY
                    OUTBOUND_POLICY --> OUTBOUND
                end

                AUTH["Aos–KUKSA Credential Broker<br/>Aos IAM permissions → short-lived<br/>path-scoped KUKSA JWT"]
                CONTRACT["Versioned Vehicle Data Platform<br/>Component contract"]
                CONTRACT --- KUKSA_ACTUAL
                CONTRACT --- KUKSA_TARGET
                AUTH -. "authorizes" .-> READ_API
                AUTH -. "authorizes" .-> ACTUATE_API
            end

            subgraph TIRE_FUNCTION_SERVICE["QM OEM Functional Service — SOTA 2"]
                TIRE_SERVICE["Tire Health Service Container<br/>local condition estimation<br/>bounded summary + advisory decision"]
            end

            subgraph BRAKE_FUNCTION_SERVICE["QM OEM Functional Service — SOTA 1"]
                BRAKE_SERVICE["Brake Health Service Container<br/>local analytics and advisory decision"]
            end

            BRAKE_SERVICE -. "AOS_SECRET → short-lived JWT" .-> AUTH
            TIRE_SERVICE -. "AOS_SECRET → short-lived JWT" .-> AUTH
            AUTH -. "GetPermissions<br/>native IAM authority" .-> AOS_CORE

            READ_API -- "Read / subscribe" --> TIRE_SERVICE
            READ_API -- "Read / subscribe" --> BRAKE_SERVICE
            BRAKE_SERVICE -- "Brake Health advisory request" --> ACTUATE_API
            TIRE_SERVICE -- "Tire Health advisory request" --> ACTUATE_API
            TIRE_SERVICE -. "Requires compatible<br/>component contract" .-> CONTRACT
            BRAKE_SERVICE -. "Requires compatible<br/>component contract" .-> CONTRACT
        end

        VISS_SERVER -- "Telemetry and gateway status" --> NETWORK
        NETWORK -- "Telemetry and status subscription" --> INBOUND
        OUTBOUND -- "VISS Set request" --> NETWORK
        NETWORK -- "Advisory request" --> VISS_SERVER
    end

    CONTROL_UI -- "Separate authenticated<br/>control channel" --> EGO_RUNTIME
    NETWORK -- "Independent read-only<br/>VISS subscription" --> TELEMETRY_DASHBOARD
    SOFTWARE_DASHBOARD <-->|"authoritative API state + evidence<br/>explicit final OEM-authorized decision"| AOS_CLOUD

    AOS_CLOUD <-->|"Provisioning, deployment,<br/>lifecycle and status"| AOS_CORE
    AOS_CORE -. "Install / update<br/>FOTA artifact" .-> COMPONENT_RUNTIME
    COMPONENT_RUNTIME -. "Host provider payload" .-> DATA_PLATFORM
    AOS_CORE -. "Deploy / update<br/>SOTA 1" .-> BRAKE_SERVICE
    AOS_CORE -. "Deploy / update<br/>SOTA 2" .-> TIRE_SERVICE

    BRAKE_SERVICE -. "Brake Health report<br/>asynchronous" .-> BRAKE_BACKEND
    TIRE_SERVICE -. "Bounded condition summary<br/>or threshold event" .-> TIRE_BACKEND
```

### Diagram interpretation

The diagram is a **capability-superset view** of one logical vehicle
architecture. A deployable FOTA or SOTA box indicates that the architecture can
host that element; it does not imply that every element is installed at every
demonstration stage. The manufacturing, provisioning, `G0–G4`, independent
`T1` Tire Health, and retirement sequence and the precise presence or absence of each deployable component are
owned by Demo Scenario 1.5 rather than by this static component diagram.

The logical Domain Controller architecture is instantiated twice for the
demonstration: once as the Validation Unit and once as the Demonstration Unit.
The diagram intentionally does not duplicate the full ECU graph. The current
demo has one visible CARLA/Vehicle Gateway/VISS environment; connection or
deterministic replay between that source and the selected Unit remains a
detailed demonstration-design decision.

## System Boundaries

### Virtual physical vehicle

CARLA represents the physical part of the vehicle: vehicle dynamics, the road
environment, sensors, and actuators. It is not an Aos Unit and it does not
expose the stable application-facing vehicle-data interface directly.

### Vehicle Gateway ECU

`carla-ego-runtime` represents a Vehicle Gateway ECU. It:

1. observes the CARLA vehicle and its sensors;
2. receives control commands over a separate control channel;
3. normalizes CARLA-specific data into the VSS model;
4. exposes that model through a TLS-protected VISS 3.1 endpoint;
5. in the target architecture, accepts a narrowly scoped advisory actuator
   request and publishes the Gateway reception status.

CARLA-specific APIs stop at this boundary. Neither the Domain Controller nor
the Brake Health service connects directly to CARLA.

### Simulated in-vehicle network

The VISS connection over TLS/IP represents the communication path between the
Vehicle Gateway ECU and the Domain Controller ECU. In a real vehicle the
underlying transport could be CAN, SOME/IP, DDS, TSN Ethernet, or an OEM-defined
interface. VSS provides the stable signal semantics while the provider hides
the transport-specific implementation.

### Domain Controller ECU

QEMU plus AosVM represents a Domain Controller ECU. It contains:

- the factory-installed substrate created from the OEM Demo Factory Image,
  including AosCore lifecycle,
  identity, security, desired-state management, Service Manager, KUKSA, and
  update support;
- the preinstalled, provider-specific component runtime with an initially
  empty Vehicle Data Platform Component slot;
- the independently installed FOTA-owned Vehicle Data Platform Component
  payload and its versioned contract;
- KUKSA Databroker as the preinstalled stable VSS data boundary for services;
- independently deployed SOTA service containers;
- the Function Team 1 Brake Health service;
- the Function Team 2 Tire Health service.

The Domain Controller is not part of CARLA. Its VM boundary represents a
separate automotive computer even though both sides execute on the same Mac.

The OEM Factory Baseline Assembly is a build-time Platform Team responsibility,
not software running in the Domain Controller. It reproducibly composes,
builds, qualifies and freezes the immutable OEM Demo Factory Image artifact.
Fresh Validation and Demonstration Unit runtime deployments are created from
that artifact and run the installed component graph; they are not instances
of the assembly component.

The immutable OEM Factory Image contains no Vehicle Data Platform Component
payload, functional SOTA service, Cloud registration, Cloud-issued credential,
or reusable per-vehicle identity. The accepted component runtime is currently
specific to one provider type and one empty slot; Architecture 1.4 does not
claim a generic arbitrary-component runtime.

A pinned OEM build may emit both the complete bootable Factory Image and a
separate rootfs platform-update envelope from the same rootfs content. These
are different lifecycle artifacts. Fresh M0 deployments use the complete
unprovisioned Factory Image and already contain the empty-slot runtime before
M1 provisioning. The rootfs envelope uses the factory-installed AosVM rootfs
A/B mechanism only to retrofit or maintain an older provisioned Unit; it is
not required to introduce the initial runtime in the normal manufacturing
flow. The post-SOP Vehicle Data Platform Component remains a third, separately
versioned FOTA artifact installed through that runtime.

The Vehicle Data Platform Component payload is the shared
vehicle-integration layer. It owns the privileged connection to the Vehicle
Gateway, converts accepted VISS values into the stable KUKSA contract, and
enforces the narrowly scoped outbound advisory path. The KUKSA executable is
part of the SOP substrate, while the signal mappings, accepted namespaces, and
versioned contract exposed through it belong to the FOTA component.
Functional services consume that contract and do not contain vehicle-network
integration code.

### OEM systems

AosCloud is the lifecycle system of record and execution control plane for
provisioning and for the FOTA component and both SOTA services. It stores the
authoritative desired state, reported actual state, batches, campaigns,
recorded approvals, audit history, and delivery progress. It does not make an
owning team's engineering release decision, is not a functional telemetry
backend, and does not participate in either service's real-time decision path.

The OEM Software Delivery Dashboard is a stateless presentation and
workflow-facilitation view over authoritative AosCloud APIs. It can display
targets, exact artifact and service-metadata digests, requested permissions,
required qualification evidence, validation results, owning-team acceptance,
promotion, Unit status, the current team context, and the OEM role used for a
proposed action. Missing, stale, mismatched or failed prerequisites block the
action. The visible approval control is only the final explicit OEM decision
after that review; passing evidence never auto-approves. The Dashboard submits
the decision through the correct scoped OEM identity and re-reads AosCloud. It
must not make the engineering decision, impersonate an owner, invent evidence
or parallel desired state, or become a second lifecycle control plane.

AosEdge native logging is an existing platform capability. System, service
instance, and crash logs are collected by AosCore and delivered to AosCloud in
response to authorized log requests. The OEM Software Delivery Dashboard uses
supported AosCloud APIs to request and present that evidence without storing
its own log archive or introducing a separate collection, transport, or search
pipeline.

Function Team 1 owns a separate Brake Health Backend and Brake Health Function
Dashboard. Function Team 2 owns a separate Tire Health Backend and Tire Health
Function Dashboard. The two functional data planes are peers: neither backend is routed
through the other, and neither has authority to deploy software to the Unit.

### Demo and engineering workstation

The Vehicle Control UI, OEM Software Delivery Dashboard, and Engineering
Telematics Dashboard are demonstration tools on the Mac host. They are not
production vehicle ECUs and must be shown outside the logical vehicle boundary.

The existing telemetry dashboard is the `carla-viss-client --monitor` mode. It
connects directly to the Vehicle Gateway VISS endpoint as an independent,
read-only subscriber. It does not connect to CARLA RPC, KUKSA, AosVM, or the
Cloud backend.

No production driver HMI or Instrument Cluster is implemented in Architecture
1.3. The engineering dashboard may show that an advisory was requested and
received by the Vehicle Gateway, but the demonstration must not claim that the
warning was displayed to or acknowledged by a driver.

## OEM Ownership and Release Lifecycles

### Platform Team — Vehicle Data Platform Component, FOTA

The Platform Team owns the factory baseline and shared vehicle-facing platform
component:

- OEM Factory Baseline Assembly and Factory Image qualification, including
  the selected provider-specific component runtime, its empty-slot behavior,
  the enabled stock Aos IAM permission handler, and the non-secret
  IAM/PKCS#11 integration seam used by the future broker;
- inbound and outbound vehicle-interface providers;
- VSS mapping, filtering, and validation;
- KUKSA integration and stable signal contract;
- the thin Aos–KUKSA Credential Broker, KUKSA public-verifier configuration,
  and platform-protected signing-key integration;
- outbound actuator allowlists and enforcement;
- short-lived platform credentials and trust integration without embedding
  secrets in artifacts;
- platform qualification, compatibility, update, and rollback;
- the engineering decision to accept each platform candidate, recorded in
  AosCloud through an authorized OEM identity before deployment or promotion.

In the current demonstration, Function Team 1 may request a new or extended
vehicle-data capability. It does not gain permission to ship privileged
platform integration code. Function Team 2 consumes signals already present in
the accepted component contract; a Function Team 2 platform feature request
is possible in a production organization but is not part of this demo.

### Function Team 1 / Service Provider 1 — Brake Health, SOTA 1

Function Team 1 is an OEM functional vertical and an independent AosCloud
Service Provider. It owns:

- a QM-domain maintenance/inspection application with no allocated safety goal
  or vehicle-motion authority;
- the Brake Health service container;
- local emergency-braking detection, diagnostic analysis, and advisory
  decision logic;
- the required Vehicle Data Platform Component compatibility declaration;
- service configuration, state, tests, updates, and rollback;
- the engineering decision to accept each service candidate and integration
  result; service publication uses the Service Provider 1 identity, while
  deployment approval affecting OEM Units uses an authorized OEM identity;
- the Brake Health Backend and Brake Health Function Dashboard.

The service consumes the stable KUKSA/VSS contract. It does not depend on
CARLA, VISS, CAN, or another vehicle-network transport directly.

### Function Team 2 / Service Provider 2 — Tire Health, SOTA 2

Function Team 2 is a peer OEM functional vertical and a separate AosCloud
Service Provider. It owns:

- a QM-domain maintenance/inspection application with no allocated safety goal
  or vehicle-motion authority;
- the Tire Health service container;
- local processing of the vehicle-dynamics signals allowed by its KUKSA contract;
- a bounded, persistent and versioned tire-condition estimate;
- the decision to create a bounded summary or threshold event;
- the decision to request an allowlisted tire-inspection advisory;
- its required Vehicle Data Platform Component compatibility declaration;
- service configuration, state, tests, updates, and rollback;
- the engineering decision to accept each service candidate and integration
  result; service publication uses the Service Provider 2 identity, while
  deployment approval affecting OEM Units uses an authorized OEM identity;
- the Tire Health Backend and Tire Health Function Dashboard.

The service does not continuously stream raw sensor data to the Cloud. It
estimates tire condition locally and uploads deliberately bounded summaries or
threshold events to its own backend when connectivity is available. It reports
an estimated condition band and inspection recommendation, not an exact
measured tread depth. A clearly labelled accelerated-time or pre-aged tire
condition makes the transition observable in a short demo. Hidden deterministic
simulation truth may qualify the model but is not a production signal exposed
to the service or backend. The exact input subset, state model, persistence,
thresholds, payload and dashboard representation remain detailed-design items.

### Lifecycle independence, dependency, and promotion

The architecture has three independently owned release lifecycles:

1. the Platform Team publishes the Vehicle Data Platform Component through
   FOTA;
2. Service Provider 1 publishes the Brake Health service through SOTA 1;
3. Service Provider 2 publishes the Tire Health service through SOTA 2.

Each SOTA service declares its own dependency on a versioned Vehicle Data
Platform Component. The services do not depend on each other and can be
installed, updated, or rolled back independently, subject to their platform
contract. The platform is qualified through its FOTA lifecycle before a
dependent service is accepted against it. A service defect creates a new
version in that service provider's SOTA lifecycle; a platform defect creates a
new FOTA version. Promotion freezes the exact compatible graph and artifact
digests accepted on the validation Unit before rollout to the demonstration
Unit.

Release ownership, Cloud authorization, and execution are deliberately
separate. A Function Team uses its Service Provider identity to develop, sign,
publish, version, and technically verify its service artifact. The same
organizational team records validation acceptance and deployment or promotion
approval through an authorized OEM identity. The Platform Team records its
FOTA acceptance through an OEM identity. Before final approval, the review
binds the exact artifact and metadata digests, requested permissions, target,
required validation evidence and owning-team acceptance. AosCloud persists
those decisions and executes the resulting lifecycle transition. A passing
test or completed batch never performs this decision automatically.
The recorded approval means that the required release evidence was reviewed
and accepted; it is not, by itself, a functional-safety certification or proof
that software is safe.

A combined platform-and-service graph has no anonymous single acceptance
owner. The Platform Team accepts the exact platform candidate, the relevant
Function Team accepts its exact service candidate and integration result, and
AosCloud may promote the graph only after every required owner approval is
recorded for the exact versions, digests, and targets.

The target architecture requires **native AosCloud pre-deployment
enforcement** of each SOTA-to-FOTA compatibility range. If the intended Unit
does not yet contain a compatible Vehicle Data Platform Component, AosCloud
rejects the SOTA request before it creates a rollout or sends update content to
the Unit. The current released Cloud/API does not yet expose this cross-type
dependency. On 2026-08-18 the AosEdge Platform Team identified it as a roadmap
feature, without committing a release or date. The corresponding negative-path
demo is therefore deferred until an implementing release is available and
qualified. No temporary admission controller is added to this architecture.

Service-side compatibility metadata and fail-closed startup/readiness remain
required defense in depth; they do not substitute for the future native Cloud
gate.

## Runtime Flows

### 1. Shared vehicle telemetry

```text
CARLA vehicle state
  -> carla-ego-runtime
  -> normalized VSS model
  -> Vehicle Gateway VISS 3.1 server
  -> simulated in-vehicle network
  -> inbound VISS provider in AosVM
  -> validation, normalization and signal selection
  -> KUKSA publish of actual values
  +-> Brake Health service read/subscribe
  `-> Tire Health service read/subscribe
```

The platform provider publishes actual sensor values into KUKSA once. Each
functional service reads only the paths in its own contract or subscribes to
their changes. The services do not receive raw values from one another.

### 2. Vehicle control

```text
Vehicle Control UI
  -> separate authenticated local control channel
  -> carla-ego-runtime
  -> CARLA vehicle controls
```

The control path is deliberately separate from VISS telemetry and KUKSA. Loss
of the control client selects the existing safe-stop behavior. The Brake Health
service and Tire Health service are QM-domain applications and do not control
vehicle motion in Architecture 1.4.

### 3. Local Brake Health analysis

```text
KUKSA sensor subscription
  -> emergency-braking/event detection
  -> bounded diagnostic monitoring
  -> local brake-health analysis
  -> local advisory decision
```

This path executes entirely inside the Domain Controller. It must continue to
work without Cloud connectivity and its decision latency must not contain a
Cloud round trip.

### 4. Local Tire Health estimation and bounded reporting

```text
KUKSA sensor subscription
  -> local vehicle-dynamics processing
  -> bounded persistent tire-condition model
  -> estimated condition band and threshold decision
  -> bounded summary/event to the Tire Health Backend when connected
  -> Tire Health Function Dashboard
```

Condition estimation and the inspection recommendation run inside the Domain
Controller and do not require a Cloud round trip. The service sends bounded
summaries and threshold events; it does not use the functional backend as a
continuous raw-sensor processor. Connectivity loss may delay upload, but it
must not prevent local estimation or advisory generation. State persistence,
retention, retry behavior and the exact payload are lower-level decisions.

For the current demo, this service must use vehicle data already present in the
accepted Vehicle Data Platform Component. It combines native dynamics
evidence with an explicit simulation-only degradation stimulus. That hidden
qualification truth must not be published as if it were a production vehicle
measurement.

### 5. Typed advisory return to the Vehicle Gateway

```text
Brake Health service or Tire Health service
  -> KUKSA actuate
  -> actuator target
  -> outbound actuation policy and allowlist
  -> outbound VISS provider
  -> VISS Set over the simulated in-vehicle network
  -> Vehicle Gateway advisory handler
  -> Gateway reception/status signal
```

The service does not send a message directly to the dashboard. The engineering
dashboard observes the Gateway-side advisory and status over VISS. This proves
that the request completed the round trip back to the simulated vehicle side.

Architecture 1.4 defines the following semantics:

| Operation | Meaning |
| --- | --- |
| KUKSA `publish` | Platform provider supplies an actual sensor or status value |
| KUKSA `read` / `subscribe` | Service or observer consumes actual values and changes |
| KUKSA `actuate` | Service requests a desired value for an allowed actuator |
| KUKSA actuator target | Desired value consumed by the outbound provider |
| VISS `Set` | Target transport operation used to deliver the allowed request to the Gateway |

The final VSS overlay is a lower-level design deliverable. The architecture
uses these provisional semantic entries:

```text
Vehicle.OEM.BrakeHealth.Advisory.Request       actuator
Vehicle.OEM.BrakeHealth.Advisory.GatewayStatus sensor
Vehicle.OEM.TireHealth.Advisory.Request        actuator
Vehicle.OEM.TireHealth.Advisory.GatewayStatus  sensor
```

The request should be a bounded enum such as `NONE`,
`INSPECTION_RECOMMENDED`, or `SERVICE_REQUIRED`; it must not carry arbitrary
display text. Gateway status should describe only facts the demonstration can
prove, such as `NOT_RECEIVED`, `RECEIVED`, `REJECTED`, or `FAILED`. It must not
use `DISPLAYED` or `ACKNOWLEDGED` because no driver HMI exists in this scope.

These are QM maintenance/inspection advisories, not safety warnings or safety
commands. The VDP validates them as defense in depth. The Vehicle Gateway is
the final authoritative boundary for this QM-origin channel: it validates the
typed target, value, freshness, rate and correlation and denies throttle,
brake, steering, gear, vehicle-motion, safety-critical and arbitrary VSS write
operations.

### 6. Engineering observation

```text
Vehicle Gateway VISS server
  -> independent read-only VISS subscription
  -> Engineering Telematics Dashboard
```

The dashboard continues to show the already implemented vehicle signals:

- speed and longitudinal acceleration;
- accelerator and brake-pedal positions;
- steering angle;
- gear and engine speed;
- GNSS and simulation health information.

The target extension adds typed Brake Health and Tire Health advisory requests
and Gateway statuses to the same engineering view. The dashboard is an observer and does not
participate in the decision or actuation path.

### 7. Brake Health functional reporting

```text
Brake Health service
  -> locally retained derived health event/report
  -> Function Team Backend when connectivity is available
  -> Brake Health Function Dashboard
```

The backend receives derived health events, diagnostic evidence, and advisory
state rather than being required to process every raw signal. Loss of Cloud
connectivity may delay synchronization but must not block local analysis or the
Gateway advisory request.

### 8. Independent software lifecycle delivery

```text
Platform Team -> FOTA artifact + OEM-authorized approval -> AosCloud -> AosCore -> preinstalled component runtime -> Vehicle Data Platform Component
Function Team 1 -> SP identity publishes SOTA 1 + OEM identity approves -> AosCloud -> AosCore -> Brake Health service
Function Team 2 -> SP identity publishes SOTA 2 + OEM identity approves -> AosCloud -> AosCore -> Tire Health service
```

AosCloud records and executes all three lifecycles, but it does not merge
their ownership or make their engineering release decisions. A service can be changed without
rebuilding the other service, and either service can be changed without a new
FOTA when the installed platform contract already satisfies its declared
dependency.

## Security and Trust Boundaries

- The Vehicle Gateway VISS endpoint uses TLS and a private route intended for
  the simulated in-vehicle connection.
- Unit identity, private keys, certificates, provider credentials, and service
  tokens never enter Git or deployable public artifacts.
- The immutable OEM Factory Image contains no Cloud registration, Cloud-issued
  credential, reusable per-vehicle secret, or fixed identity that would be
  duplicated across Unit instances.
- The inbound provider has permission to publish only its accepted sensor and
  status paths.
- Each functional service receives read access only to its required KUKSA
  sensor paths.
- Each service receives actuation access only to its own typed advisory target.
- Brake Health and Tire Health are QM-domain applications. No safety goal is
  allocated to them and no safety claim depends on their timing or output.
- The Tire Health service has no vehicle-motion permission. Its external
  egress is limited to its own backend and bounded functional payloads.
- The outbound provider accepts only an explicit actuator allowlist, validates
  type and enum bounds, and fails closed.
- VDP outbound validation is defense in depth. The Vehicle Gateway is the
  final authoritative enforcement point for the QM-origin channel and denies
  arbitrary VSS writes and every vehicle-motion or safety-critical operation.
- An advisory request cannot become an unrestricted transport tunnel from a
  service container to the Vehicle Gateway.
- Upstream Eclipse KUKSA Databroker remains unchanged and trusts only the
  public verifier configured by the Platform Team.
- The Vehicle Data Platform Component's Aos–KUKSA Credential Broker validates
  a running service's `AOS_SECRET` through Aos IAM and translates only the
  currently registered path/mode set into a short-lived KUKSA JWT. It rejects
  invalid, stale, malformed or contract-incompatible permissions and never
  widens the IAM result.
- Aos IAM and Service Manager remain authoritative for SOTA instance identity,
  secret registration and permission invalidation. The broker stores neither
  service identities nor a duplicate per-service OEM policy database.
- Functional services never receive KUKSA `provide` or `create` authority.
  The Vehicle Data Provider uses a separate short-lived platform credential;
  its exact FOTA-component identity binding remains a qualification gate.
- Broker signing material is protected through the Aos IAM/certificate-module
  and PKCS#11 integration. It, `AOS_SECRET`, and issued JWTs never enter Git,
  Factory Images, FOTA/SOTA payloads, command lines, or logs. Example/static
  tokens are qualification history, not the target architecture.
- Vehicle control remains on its separate authenticated channel and is not
  exposed to either functional service.
- Functional backends have no AosCore lifecycle authority and cannot act as a
  substitute path into CARLA, VISS, or KUKSA.
- The two Service Providers have separate identities, credentials, artifacts,
  configuration, and Cloud-side functional endpoints.
- Service Provider identities publish and technically verify service artifacts;
  they do not authorize deployment to OEM Units. Validation acceptance and
  deployment or promotion actions use authorized OEM identities.
- The OEM Software Delivery Dashboard uses scoped AosCloud authentication,
  displays the exact artifact and metadata digests, requested permissions,
  target, required evidence, owning-team acceptance and active OEM role, and
  exposes only the final explicitly confirmed mutation action when all
  prerequisites match. It stores no authoritative lifecycle state and passing
  evidence never grants or implies approval.
- KUKSA/Aos IAM authorization is a cybersecurity least-privilege control
  within the QM domain; it is not a functional-safety case.
- AosCloud log requests and results use scoped authentication; emitted service
  and platform logs must not disclose Unit secrets, service tokens, or
  unrestricted vehicle data.

## Current Baseline and Target Delta

| Area | Current accepted behavior | Architecture 1.4 target |
| --- | --- | --- |
| CARLA and ego runtime | Vehicle state, control, VSS normalization | Preserve unchanged behavior |
| VISS server | TLS VISS 3.1 Get and Subscribe; write rejected | Add a narrowly scoped QM advisory Set path and Gateway status; Gateway remains the authoritative deny-by-default boundary for motion and safety-critical operations |
| Engineering dashboard | Independent VISS subscriber for live telemetry | Add advisory request and Gateway reception status |
| Vehicle Data Platform Component | Inbound VISS-to-KUKSA implementation and qualification evidence exist; the thin Credential Broker and provider platform-identity binding are not yet implemented in the clean demo baseline | Provide one shared, versioned FOTA component with inbound telemetry, separately governed outbound advisory directions, and short-lived KUKSA credentials derived from Aos IAM without a parallel identity or per-service policy store |
| Factory Baseline Assembly, OEM Demo Factory Image and Domain Controller substrate | The current build evidence and runtime are provider-specific; the live `.1`/`.2` IAM configuration does not enable the permissions handler, installed systems prove an empty provider slot, and the hardened candidate is not yet an accepted clean factory artifact | Qualify the reproducible assembly process and freeze its immutable, unprovisioned OEM image containing AosCore, KUKSA, security/update support, enabled stock IAM permission handling, a non-secret IAM/PKCS#11 signing-key seam, and the selected empty-slot runtime, but no provider payload, functional service, reusable identity or key |
| KUKSA contract | Readable telemetry signals | Serve both services and add the versioned advisory actuator and status sensor |
| Brake Health service | Not yet the accepted final service | Subscribe, analyze locally, actuate advisory, report asynchronously |
| Tire Health service | Not implemented | Estimate tire condition locally, send bounded summaries/events and request a typed inspection advisory |
| Service Provider separation | AosCloud lifecycle mechanisms exist; the two target services are not yet accepted as independent deployments | Independent Service Provider identities for publication, team-owned engineering decisions, OEM-authorized deployment approvals, artifacts, dependencies, updates, and rollback |
| Cross-lifecycle dependency admission | Service-to-layer and component-to-component dependencies exist, but the current released Cloud/API does not expose a Service-to-FOTA-component admission rule | Natively reject an incompatible SOTA request in AosCloud before rollout creation or Unit transfer; deferred until the roadmap feature ships and is qualified |
| OEM Software Delivery Dashboard | Not implemented; the AosCloud UI and APIs remain authoritative | Provide a stateless view of exact artifact/metadata digests, requested permissions, actual targets, evidence, owning-team acceptance, active OEM role, validation, promotion and Unit state; expose explicit final OEM approval only after prerequisites match, without a parallel state store or automatic approval policy |
| Native operational logs | AosEdge supports Cloud-requested system, service-instance and crash logs | Present selected, access-controlled request status and log evidence in the stateless Software Delivery Dashboard through supported AosCloud APIs |
| Validation and Demonstration instances | Separate VM roles exist, while the demo has one visible CARLA/Vehicle Gateway/VISS source | Instantiate the same logical Domain Controller architecture twice and define deterministic selection or replay without claiming two simultaneous vehicles |
| Driver HMI | Not implemented | Remains out of scope |
| Functional backends | Scenario-level targets | Two separate backends receive derived Brake Health and Tire Health data without entering local decisions or software lifecycle control |

The target writable VISS path must not weaken the current read-only guarantee
for any other signal. A request outside the explicit typed advisory
contract remains rejected.

## Architectural Invariants

Architecture 1.4 is aligned only while all of the following remain true:

1. CARLA represents the physical vehicle; `carla-ego-runtime` represents the
   Vehicle Gateway ECU; AosVM represents a separate Domain Controller ECU.
2. Both functional services talk to KUKSA, never directly to CARLA or VISS.
3. Function Team 1 and Function Team 2 are peer OEM organizations and separate
   AosCloud Service Providers.
4. Only Function Team 1 requests a Vehicle Data Platform Component extension
   in the current demo; Function Team 2 uses the already available contract.
5. Tire Health estimates condition locally and sends only bounded summaries or
   threshold events; it does not continuously stream raw sensor data to the Cloud.
6. Brake Health local analysis and advisory generation do not require Cloud
   connectivity.
7. Tire Health estimation and advisory generation do not require Cloud
   connectivity; its backend synchronization is asynchronous.
8. AosCloud lifecycle control, Brake Health functional data, and Tire Health
   functional data are three distinct Cloud concerns.
9. The Engineering Telematics Dashboard talks to the Gateway VISS endpoint,
   never directly to KUKSA or either functional service.
10. Vehicle control and VISS vehicle-data exchange remain separate channels.
11. The platform FOTA, Brake Health SOTA 1, and Tire Health SOTA 2
    retain independent ownership, versioning, qualification, update, and
    rollback lifecycles.
12. The two services do not depend on each other; each is gated only by its
    declared Vehicle Data Platform Component contract. Native AosCloud
    pre-deployment enforcement is a deferred target capability and must not be
    claimed against the current release.
13. Each Brake Health or Tire Health advisory passes through KUKSA, the
    outbound allowlist, VISS Set, and the Vehicle Gateway before the engineering
    dashboard observes it.
14. The demonstration proves Gateway receipt, not display or acknowledgment by
    a driver.
15. No secret, Unit identity, or private credential is embedded in a FOTA or
    SOTA payload.
16. The static diagram is a target capability superset; Demo Scenario 1.6 owns
    component presence and absence at each manufacturing, provisioning,
    `G0–G4`, `T1`, and retirement stage.
17. Validation and Demonstration Units are separate instances of the same
    logical Domain Controller architecture; the diagram does not imply two
    simultaneous CARLA vehicles.
18. The Platform Team and each Function Team own their engineering release
    decisions. Function Teams publish through their Service Provider identities,
    while every approval affecting OEM Unit deployment is recorded through an
    authorized OEM identity.
19. AosCloud is the lifecycle system of record and execution control plane;
    neither the Software Delivery Dashboard nor the Demo Orchestrator stores
    authoritative lifecycle state, auto-approves evidence, or replaces an
    owning team's decision.
20. A combined FOTA/SOTA graph is promoted only after the Platform Team and the
    relevant Function Team have separately accepted their exact artifacts and
    the integration result.
21. Aos Service Manager and IAM own each SOTA instance's identity,
    `AOS_SECRET` and registered permissions. The VDP Credential Broker only
    performs contract-bounded translation to a short-lived KUKSA JWT and owns
    no parallel identity or per-service policy database.
22. The Factory Image contains the enabled stock IAM permission handler and
    non-secret IAM/PKCS#11 integration seam, but no per-Unit signing key or
    static provider/service token. The FOTA provider uses a separately bound
    short-lived platform credential.
23. Brake Health and Tire Health remain QM-domain maintenance/inspection
    applications with no allocated safety goal, direct driver-HMI claim,
    vehicle-motion authority or safety-critical actuator access.
24. The VDP outbound allowlist is defense in depth; the Vehicle Gateway is the
    final authoritative boundary for the QM-origin channel and denies any
    operation outside the typed non-safety advisory contract.
25. OEM approval is the explicit final decision after review of exact artifact
    and metadata identities, permissions, target, validation evidence and
    owning-team acceptance. Passing evidence never auto-approves, and the
    Dashboard owns neither the decision nor lifecycle state.

## Out of Scope

- a production IVI, Instrument Cluster, or driver-facing HMI;
- claims that a warning was displayed or acknowledged by a driver;
- autonomous modification of brake ECU calibration or vehicle motion;
- any functional-safety claim for Brake Health or Tire Health, or reliance on
  their advisory for hazard mitigation;
- third-party Service Providers or Fleet Operators;
- a Function Team 2 request for a new Vehicle Data Platform Component in the
  current demo;
- continuous raw-sensor streaming to the Tire Health Backend;
- presentation of simulated tire degradation truth as a measured production
  vehicle signal;
- an exact tread-depth claim without a corresponding sensor;
- a real production fleet campaign;
- selection of CAN, SOME/IP, DDS, TSN, or production ECU hardware;
- Cloud-side pre-transfer admission against an independent OEM KUKSA
  permission upper bound; the current runtime uses Service Manager/IAM
  registration and contract-bounded broker translation without a duplicate
  policy database;
- exact VSS overlay paths, enum values, timing budgets, and retry policy;
- Cloud or Unit mutation merely by accepting this document.

## Acceptance Record and Downstream Ownership

High-Level Architecture 1.4 was accepted as the architecture baseline on
2026-08-19 after the ADR 0011 QM-containment and evidence-backed approval
decision. Its downstream
current downstream review projections are:

1. Demo Scenario 1.6 for audience-visible stage order and component presence;
2. Architecture Flows 1.5 for detailed lifecycle, runtime, observability, and
   failure mapping;
3. System Requirements and Traceability 0.8 for normative system obligations
   and gap coverage;
4. Component Decomposition and Interface Register 0.8 for component ownership,
   interface identifiers, repository allocation, and provisional requirement
   packages.

Revision 1.4 keeps the 1.3 credential model unchanged. It classifies the two
functional services as QM, makes Gateway containment authoritative, and makes
the evidence behind the final OEM approval visible and testable.

The next roadmap boundary is D3 component requirement packages. Acceptance of
this architecture does not authorize implementation, building, signing, Cloud
publication, assignment, provisioning, deprovisioning, or Unit mutation.
