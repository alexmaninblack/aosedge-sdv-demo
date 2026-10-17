<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosEdge Demo Interaction Specification

- Status: Accepted interaction contract; effective installed/expanded profiles stated below
- Version: 2.6
- Owner: Demo Solution Team with Platform Team and Function Teams 1 and 2
- Architecture input: [High-Level Architecture 1.8](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.1](../staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.2](../../architecture/demo-scenario-architecture-flows.md)
- Interaction decision: [D4-026.7 Linear Audience Interaction Model](../../requirements/d4-decision-register.md#d4-026-7)
- Global lifecycle decision: [D4-026.15 M0/M1/G0/R0 Interaction Model](../../requirements/d4-decision-register.md#d4-026-15)
- Fleet and Unit Set identity decision: [D4-012.1 Dedicated Demo Fleet and Unit Set Identity](../../requirements/d4-decision-register.md#d4-012-1)
- Capability-milestone decision: [D4-026.16 Independent Releases and Derived G3/G4 Milestones](../../requirements/d4-decision-register.md#d4-026-16)
- Workspace-ownership decision: [D4-026.17 Workspace Composition and Shared Header Ownership](../../requirements/d4-decision-register.md#d4-026-17)
- Global-workspace decision: [D4-026.18 Global Lifecycle Workspace and Qualification Status](../../requirements/d4-decision-register.md#d4-026-18)
- Team-context decision: [D4-026.19 Fixed Team Context and Version-Only Scrolling](../../requirements/d4-decision-register.md#d4-026-19)
- Icon/terminal boundary decision: [D4-026.20 Icon Vocabulary and Native Terminal Boundary](../../requirements/d4-decision-register.md#d4-026-20)
- Platform FOTA enforcement decision: [ADR 0014](../../architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Platform FOTA Safe Stop contract: [1.1.1](../../../contracts/platform-fota-safe-stop/README.md)
- Surface register: [I0 Audience-Visible Interface Register](README.md)
- UI traceability: [AosEdge Demo UI Traceability Register](aosedge-demo-ui-traceability-register.md)
- Maintained UI implementation: [Presenter](../../../apps/presenter-ui/README.md)
- Current implementation/proof: [baseline](../../qualification/current-baseline.md)
- Editorial consolidation: 2026-10-17; accepted behavior and stable IDs preserved

## Purpose and authority

This specification defines visible interaction and factual state presentation,
not vehicle behavior, Cloud authority, service protocols or a second state
store. Upstream contracts win. The maintained Presenter and native Driving
Control are the implementation; retired HTML simulations are not test evidence.

<a id="ui-studio-026--current-test-studio-contract"></a>
## UI-STUDIO-026 — Installed Test interaction contract

The installed profile uses one Test, one OEM and one associated SP with separate
Brake/Tire service identities. Presenter, CARLA and native Driving Control/
Telemetry remain visibly composed. Backend/Cloud summaries and details are
integrated cards/dialogs; Platform, Brake and Tire retain contextual release
actions. Ordinary Stop/Start is non-destructive; Delete/Finish names the Test
and consequence. No hidden Production VM, Fleet creation or automatic approval.

### Interaction profiles

The numbered rules below state their effective installed behavior directly.
An explicitly marked expanded rule retains separate Production promotion,
two-provider isolation or full qualification obligations. It is not an
installed feature claim. Shared security, evidence, Safe Stop, motion-control
and no-blind-retry rules apply to both profiles. UI IDs remain stable.

Installed navigation uses integrated actor/component cards and contextual
dialogs/actions, not a mandatory five-stage release-card layout. Protected
operator mutations are serialized. Logical producer independence does not
require multiple simultaneous writers. Native Driving Control includes its
read-only telemetry; a separate Terminal dashboard is not required.

### Observation and resource facts

Disk is verified used bytes, formatted B/KiB/MiB/GiB with all controller
partitions and separate instance scope. Network is accumulated daily byte
volume, not rate; preserve source day and explain exclusion of local/private
traffic. Local backend delivery may coexist with zero metered traffic. Public
backend network proof remains deferred. Unknown units, missing samples,
measured zero and conflicting aliases stay distinct; no guest collector is added.

- Conflicted product content is explicitly untrusted on the backend card and
  Overview. Keep the conflicting head inspectable in Records; neither a normal
  condition score nor an older healthy fallback may stand in for it.
- An assigned service pending installation offers Cloud observation, not
  Prepare/publish again. No Safe Stop is required for services.
- Selected Cloud comes from current session configuration independently of
  certificate inspection success. Old operation receipts cannot override it.
- Status-only component updates use the same pending interpretation for
  display and the existing bounded 2/4/8/10-second observer.
- Read-only backend inspection has one ten-second deadline including Docker
  ownership preflight and HTTP. Exact-window detail uses six seconds total,
  within its eight-second browser limit. Each HTTP exchange/body remains capped
  at three seconds or the remaining budget, whichever is smaller. No ownership
  guard is removed and no request is retried.

- Retained results keep their source and receipt dates. Backend/Cloud checked
  time is separately labelled; it never means a new vehicle event. A stale
  native binding qualifies the same result as last known on card and dialog.
- Component update status establishes pending activity even before a version
  is supplied. Cards, details and Platform guidance share this interpretation.
  Preserve errors and unknown versions; do not infer a release.
- Show aggregate and instance numeric errors without guessing an update cause.
  A conflicting instance error cannot establish Running. Cloud API completion
  is labelled Cloud checked, not device report time.
- Resource detail exposes available `disk` as well as `usedDisk`, preserving
  parameter, node, Subject, instance, partition and unknown units.
- Brake window detail is an explicitly timestamped snapshot with Refresh for
  that exact event and native identity. V1 recordings are not model estimates.
- Independently valid function reports survive history/reset read failures.
  Partial product history retains labelled records but cannot qualify story
  completion; reset evidence remains required. Scope/shape conflicts still fail
  closed. No freshness, reset, model or advisory policy changes.
- A completed `demo.retire` receipt can produce a dismissible, at-most-one-minute
  in-memory acknowledgement in the empty workspace. Empty state alone cannot
  establish success. No additional run dossier or persistent history is added.
- Explain global next-story routing, known not-created state and configured
  input paths. Show existing band/score/recommendation fields without raw-JSON
  navigation. Visible and accessible score labels both describe model estimates.

<a id="versioned-service-and-platform-clarity--18-september-2026"></a>
### Versions, readiness and vehicle evidence

- Backend cards/dialogs distinguish input, episode activity, last product
  result and delivery freshness through their own backend's facts. Unknown
  is not healthy; installed and reset-poll contact are not telemetry proof.
- Presenter obtains installed/pending software,
  runtime observations and resources from native Aos Cloud. Bind the exact
  installed artifact to its verified functional profile, not its release major.
  Service input/episode/results come from their backends; Cloud Running is not
  telemetry proof. No new guest timer or mandatory public-input revision is
  prescribed. Prove service-local compatibility/recovery using existing inputs
  without making analytics depend on Cloud or Presenter availability.
- Exact version/profile compatibility is
  a Cloud/package-derived Presenter fact. Services report actual local input
  and capability readiness; missing telemetry is not a proved incompatible
  profile. No local active-profile interface is added. Keep Cloud compatibility,
  backend input/episode state and native advisory separate, including during
  token renewal, offline operation and late advisory acknowledgements.
- Native Driving Control keeps Manual/Autopilot and exposes prepared Brake/
  Tire maneuvers plus separate Return to road. Repositioning preserves model
  and advisory state, marks scene discontinuity and finishes stationary Manual;
  Autopilot is explicitly started afterward. No second simulator tick owner.
- Aos Cloud card shows actual Unit state, installed software counts, update
  state and observation age. Resource values move to its existing dialog:
  verified byte memory is compact MiB/GiB and CPU remains DMIPS. Missing or
  stale reads cannot become `No pending updates`.
- Brake uses purple and Tire teal consistently across backend/service cards,
  their association lines and dialog headings. Platform identity stays blue.
  Status remains independently labelled with text/icon/color; B2 miniatures
  remain natural. Empty slots and Cloud connection-state semantics remain.
- Factory firmware contains an AosCore system-software miniature and
  `In-vehicle runtime`; its image selector stays unchanged. Aos Cloud carries
  `Cloud management`. Both show small `AosEdge platform` labels and common
  blue identity accents. Do not infer Core version or health from an image name.
- Keep the fixed native-left/Studio-right composition, existing dialogs and
  lifecycle actions. A warning is not guaranteed merely by launching a maneuver.

### State and action contract

Release-profile selection is operator input, not an observation of controller
readiness. A temporary unavailable local read must not reset that selection;
mutations still require current owner facts. Reset authoring selections only
after a confirmed different run or a confirmed empty-controller state, not
because an unavailable read omits the run identity.

1. **Create** composes creation of a disposable working copy from the catalog's
   immutable factory image, boot with role/DNS initialized, and preparation of
   both product backends. It does not provision or deploy a service. Empty
   service slots remain empty; factory VDP metadata is not a Cloud observation.
2. **Start simulator** starts/reuses CARLA, strict Gateway and native surfaces.
   The local dashboard works, but no Domain Controller is attached yet.
   Presenter simulation Start/Stop explicitly use `--target test`, preserving
   any existing Production source gate.
3. **Full story** shows Platform Prepare → Sign → Publish v1 before Provision.
   **Warehouse variant** may publish a higher VDP profile before Provision;
   the eligible latest release may arrive first. Do not force v1, downgrade,
   or claim skipped profile chapters were demonstrated. **Quick preparation**
   explicitly composes the ordinary sequence and stops in Manual.
4. **Provision** preserves the running controller and simulator: official
   provisioning → observe Online → enroll the real Unit/Main Node in the existing
   Gateway → confirm stationary Manual → add Test verification membership → observe
   delivery. If registration succeeded but Online/membership did not, resume
   those remaining stages against the same identity. Local connectivity alone
   never establishes Cloud Online. No CARLA, Gateway, native-window or scene
   restart occurs. First connection retains the actor and reset generation;
   it requires a fresh confirmed stopped frame and a native operator session.
   The guest gate remains closed until Manual is confirmed, so internal stop
   does not authorize FOTA. Connect before first VDP installation: the factory
   update-runtime needs the operator's subsequent Safe Stop. External network
   loss after enrollment does not remove the local assignment.
5. **VDP update** distinguishes accepted bundle, server processing, Published,
   Unit Pending and Installed. Apply is owned by the vehicle's Safe Stop policy,
   not a Cloud panel button. The Cloud component inventory has no VDP-process
   run-state field: display runtime Not reported, with functional proof separate.
6. **Service** first Publish uses its team's SP. Deploy to Test first composes
   the existing `service runtime-prepare test` operation; preparation failure
   prevents assignment and unchanged inputs are reused without restarting SM.
   It then uses OEM: resolve
   the retained dedicated Subject, bind the exact current Test `system_uid`,
   add only the requested `service_ids:[service UUID]`, preserve its peer, then
   read assignment and expected service version/instance runtime. The payload
   contains neither version nor instance count. Later higher-version publication
   uses the same service identity and no second Deploy. SOTA does not inherit
   our component-specific Safe Stop gate.
7. **Observation** reads Aos Cloud for right-side inventory/runtime/resources,
   the product backend for results/receipt, and vehicle telemetry for native
   advisory. CPU is DMIPS. Unknown/missing/stale are not zero/absent/Offline.
   Terminal observation can advance the guide without seeing Pending. Remember
   already observed chapters within the run; never return to an old chapter
   merely because its version was replaced.
8. **Product results** require suitable input and the corresponding real
   service/VDP capabilities in implementation. Running alone proves no result.
   Backend receipt and vehicle advisory visibility are separate. Live advisory
   expires/clears under the QM lease and cannot survive a different service
   version or vehicle-source generation as if fresh; backend history may remain.
9. **Offline** affects vehicle external access only. Local driving/telemetry and
   eligible local functions remain independent; durable queued product records
   upload once after reconnect. Host publication access is separately checked.
10. **Stop/Start and Finish**: Safe Stop pauses motion with the controller
    running. Stop demo closes owned runtime without deleting the same Test,
    credentials, models, history or release continuity; Start restores it under
    current guards. Park/Resume remains rejected, including old-browser input.
    Controller ignition recovery is separately guarded and stationary; host
    sleep/wake is not implied. Finish is explicit destructive Test retirement:
    quiesce producers, revoke/delete the exact Unit, clear owned Subject/Set
    bindings and product records, stop backends and remove working files.
    Preserve Factory, permanent infrastructure, Subjects, published releases and
    release continuity. A retired overlay is never reused.
    **Abnormal Finish:** Finish
    destroys Test without waiting for successful VDP/service installation,
    publication, CM readiness or a Safe Stop observation. Stop the local
    simulator, VM and backends before Cloud retirement. A stalled guest may
    be powered off through its exact owned QMP endpoint, only for Finish.
    Retained Brake/Tire Subjects may be unused in a new run: their exact
    identities and absence of assigned/reported Units are verified after local
    shutdown, without inventing service assignments. Existing incomplete or
    uncertain assignments still block. Finish retains the actual failing step
    and reason; **Continue Finish** resumes remaining work. Cloud Offline is
    awaited only where required by Unit deprovisioning, not by unrelated local
    cleanup or after confirmed Unit deletion.
11. **Interrupted action** preserves recorded identity, bundle result and
    completed stages. Reconcile observes first and resumes only remaining work;
    it cannot turn Processing into Published or replay an uncertain upload.
    A confirmed publication rejection offers a corrected new release. An
    unresolved installation failure requires engineering intervention to repair
    the update; it does not prevent the explicitly confirmed, owned-Test Finish
    described in item 10. General campaign recovery and replay of an uncertain
    external operation are not implemented by this scoped destructive exit.
12. **Versions** are allocated by Demo Control, not entered by the operator.
    Persist reservations/used numbers and verified profile bindings across
    ordinary cleanup. Number allocation details do not appear as audience copy.

<a id="accepted-subject-and-service-package-settings--9-september-2026"></a>
### Subject and service package settings

Use two retained Group Subjects, `is_group: true`, one for Brake and one for Tire,
both bound only to the current Test and containing only their own service.
Releases reuse service identities. Finish clears owned bindings, not Subjects.
Never reuse a factory/NodeType Subject. User-state migration between vehicles
is outside this demo; local product storage/queues remain separate obligations.

Both services require `instances.minInstances: 1` and `offlineTTL: P7D` in
their service configuration. For the existing schemaVersion-2 bundle authoring
shape, these belong under `items[].configuration.instances.minInstances` and
`items[].configuration.offlineTTL`, not in the assignment request. The package
adapter must validate the resulting signed metadata at the packaging boundary.
Seven days is an explicit offline lifetime, not infinite retention or a default.

OEM assignment passes `service_ids:[service UUID]` only; Unit attachment passes
`system_uids:[current Test UID]`. Neither payload selects a service version or
number of instances. Observe the actual expected version/instance in Cloud;
the requested minimum does not itself prove a running process.

### Verification boundary

Real API, visible UI and native first-use evidence is linked from the current
baseline. Mockup tests cannot qualify Cloud, VM or algorithms. Unknown or
unexecuted cases remain explicit. Prior prototype/audit chronology is available
in [Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/1a0d66f4b340bfc7b487062f7bb316623ad86af8/docs/demo/mockups/aosedge-demo-interaction-specification.md),
not as an additional implementation plan.

## Stable common and expanded-profile interaction rules

Apply the profile mapping above to the following stable definitions. In
particular a Production-role acceptance case is not proof from a Test hosted
on the Production Cloud environment.

## 1. Screen Composition and Global Interaction Invariants


### 1.1 Presentation environment

The installed profile targets the known presenter-operated Apple Silicon
Mac and one physical display in full-screen presentation mode. The exact
qualification viewport is measured from that Mac during implementation; this
specification deliberately does not invent a pixel resolution before that
measurement. Mobile, tablet and multi-display responsive layouts are outside
the installed profile.

The audience core flow shall not require switching browser tabs, changing
macOS Spaces or manually rearranging windows. `CMP-ORCH` and its trusted
Presenter Launcher own the physical composition of existing native windows,
one reserved shared-header strip and one browser window on the measured
presenter display. They do not own the content or authoritative state rendered
inside those surfaces. CARLA and the native Controller remain native surfaces;
the installed profile shall not embed, stream or screen-capture them into
the browser.

### <a id="ui-int-001"></a>UI-INT-001 — Visible workspace composition

Keep the live CARLA vehicle and native Driving Control/Telemetry visible
beside the integrated Presenter. Layout restoration is host-window composition,
not a Cloud or vehicle lifecycle mutation. The measured display profile must
keep required controls readable without horizontal page scrolling, overlapping
critical controls or manual rearrangement during the core story. CARLA and
Driving Control remain native windows, not browser streams or screen captures.
Mobile/tablet and unqualified multi-display layouts are outside this profile.

### <a id="ui-int-002"></a>UI-INT-002 — Shared title and vehicle context

The shared title identifies SDV Lab and its selected Test context. Detailed
Cloud/software/backend facts belong to their owning cards/dialogs, not a
header probe or combined healthy indicator. Vehicle selection is restored
from the accepted source assignment, never inferred from Internet or Cloud
Online state. Before assignment, show no assigned vehicle; expanded handover
distinguishes Test and Production explicitly. Do not expose Unit/Node UUIDs,
run IDs, guest attachment plumbing, a global step counter or automatic approval.
Use audience-facing Test terminology while technical details retain the exact
Validation Unit/Verification Set concepts.

### <a id="ui-int-003"></a>UI-INT-003 — Native vehicle evidence workspace

CARLA shows the selected physical actor. The existing native Driving Control
combines driving actions with read-only Gateway/VISS telemetry and separate
Brake/Tire advisory rows. Manual/Autopilot, prepared maneuvers, Safe Stop,
Return to road and vehicle external connectivity stay with their existing
owners. A model Reset is not Return to road. No publication, provisioning,
approval or deployment action belongs in the vehicle-control surface.
Telemetry freshness, unavailable input and advisory readiness remain visible;
decorative icons cannot change their meaning or synthesize values.

### <a id="ui-int-004"></a>UI-INT-004 — Contextual team and release navigation

The right-hand integrated Presenter shows persistent architecture actors,
their current facts and contextual release/result dialogs. Platform, Brake
and Tire retain independent meaning without requiring separate browser tabs,
a five-stage card stack or a second Controller/Architecture tab. Preserve the
selected actor/profile and disposable view context across read-only refreshes;
temporary unavailable reads do not reset authoring selections. A confirmed
different run or confirmed empty-controller state may reset that context.
Expanded audience governance may expose its additional lifecycle stages, but
cannot hide native evidence, add horizontal page scrolling or imply authority
from navigation.

### <a id="ui-int-005"></a>UI-INT-005 — Details overlay

`Details` is always a secondary action. It opens a modal overlay without
navigating away, changing team, changing current vehicle or advancing release
state. Closing it by its explicit close action or `Escape` returns to the exact
prior scroll position and focus context.

The installed profile confines the modal to the right browser
workspace so that CARLA, the Vehicle Controller and Engineering Telematics
remain visible. Section 6 defines its exact content, focus, disclosure and
redaction rules.

### <a id="ui-int-006"></a>UI-INT-006 — Global interaction invariants

The following rules hold across every team and release version:

1. **One current vehicle in stable state:** exactly one logical vehicle is
   audience-current; both Cloud Units may still be Online. During a bounded
   handover or failed reconciliation, the header instead shows the honest
   transition/unavailable state and never labels both vehicles current.
2. **One visible browser view:** the presenter may change among the three team
   perspectives or the global lifecycle page at any time; all such changes are
   navigation, not lifecycle actions.
3. **Independent team state:** switching teams does not reset, advance or
   reinterpret another team's observed state.
4. **No narrative gating:** visual order alone never disables a component or
   Service version.
5. **Authoritative action gating:** protected actions use fresh accepted
   prerequisites and show a factual blocking reason; the UI does not invent a
   Cloud success, dependency enforcement or approval.
6. **No hidden success:** `SUBMITTING`, `WAITING`, `UNCERTAIN`, `RECONCILING`,
   `OFFLINE` and stale state are never rendered as completed.
7. **Stable evidence layout:** state changes and modals do not resize, replace
   or scroll the fixed vehicle-evidence workspace.
8. **One primary action per actionable stage:** explanatory `Details` remains
   secondary; there is no generic `Next` button.
9. **No secret disclosure:** credentials, JWTs, private keys, protected local
   paths and unrestricted raw Cloud responses never appear.
10. **No source-of-truth transfer:** shared composition does not make the Demo
    UI authoritative for AosCloud, Gateway, CARLA or either Function backend.

### <a id="ui-int-078"></a>UI-INT-078 — Workspace and content ownership

The existing Demo Control/launcher owns measured native/browser window
placement and layout restoration. Presenter owns title, actor navigation and
factual content over its owning sources. Opening/restoring windows writes only
workspace metadata; Create initializes the vehicle journal. No second header
controller, lifecycle database, guest probe or browser credential boundary is
introduced by composition. CARLA and Driving Control own their content.

### <a id="ui-int-079"></a>UI-INT-079 — Global demo controls

Installed Demo controls exposes the existing runtime, non-destructive Stop/
Start, guarded recovery and exact Test deletion actions. Navigation itself has
no effect. Cloud inventory, local process state, missing prerequisites and
last-known facts remain separate. Expanded qualification/preparation/retirement
views may aggregate their additional evidence, but are not a second current
controller or another lifecycle owner. They cannot hide failure, initiate
provisioning on entry or make an unavailable dossier look qualified.

### 1.2 Composition acceptance criteria

Verify one full-screen single-display workspace, approximately equal left/right
regions, CARLA above native controls/telemetry on the left and readable browser
details on the right. Shared indicators name the demo, current vehicle and team
perspective. Exact placement follows the measured current layout contract,
not prototype coordinates.

## 2. Team Perspectives and Independent State Preservation


### 2.1 Internal OEM producer teams

The shared header exposes exactly three selectable producer-team perspectives:

1. `Platform Team` — Vehicle Data Platform Component evolution;
2. `Brake Team` — Brake Health Service releases and functional results; and
3. `Tire Team` — Tire Health Service release and functional results.

All three are internal OEM engineering teams. They own their product decisions,
prepared candidates and technical publication actions. The visual composition
may frame their product views inside one browser workspace, but it does not
merge repository ownership, backend data, credentials or release state.

### <a id="ui-int-007"></a>UI-INT-007 — Independent producer contexts

Platform, Brake and Tire are three producer contexts, not three Cloud accounts.
They own independent platform/service releases and results. Installed use maps
Brake and Tire to one associated SP while preserving separate service IDs,
permissions, histories, Reset operations and backend storage. Expanded use
adds distinct SP organizations. OEM deployment authority is a different role,
not a fourth producer or a permission inferred from the selected perspective.

### <a id="ui-int-008"></a>UI-INT-008 — OEM deployment authority

The UI identifies OEM deployment authority separately from producer acceptance
and technical publication. Installed Test verification recipients use native
delivery: no fictional per-version approval button is required. Expanded
Production rollout requires the exact independent OEM authorization and its
evidence/recipient preflight. Passing a test never auto-approves, and a browser
never obtains signing keys or independent Cloud authority.

### <a id="ui-int-009"></a>UI-INT-009 — Perspective switching is navigation only

The presenter may switch among the three producer-team perspectives at any
lifecycle stage, including while another team's external operation is
`SUBMITTING`, `WAITING`, `UNCERTAIN` or `RECONCILING`. A perspective switch
shall not:

- call AosCloud or either Function backend;
- sign, publish, approve, deploy, promote, remove or retry anything;
- change the current Test/Production Vehicle;
- start, stop or reset CARLA;
- change drive mode or vehicle external connectivity; or
- dismiss, reinterpret or mark another team's operation successful.

An open modal confirmation or `Details` overlay retains focus until explicitly
closed or cancelled. After that local overlay is closed, perspective switching
is immediately available even if the underlying external operation continues.

### <a id="ui-int-010"></a>UI-INT-010 — Retained view context

Changing actor context is navigation only. Preserve its selected profile,
inspected result, open/closed detail and applicable scroll anchor without
changing vehicle binding or lifecycle. On reentry reread the owning source;
view state cannot turn an old observation into current evidence or silently
select a different release after an unavailable response.

### <a id="ui-int-011"></a>UI-INT-011 — Actor-scoped status summaries

Summaries remain on their owning actor/card and distinguish uncertainty,
failure/staleness, pending work, blockers and observed results. They never
declare a whole team healthy from one completed action or hide a conflicting
error. Keep the shared header compact; do not duplicate connection diagnostics
or team-status summaries there. Detail retains exact source/time/scope.

### <a id="ui-int-012"></a>UI-INT-012 — Hidden-surface observation

Visible surfaces use the shared bounded observers. Leaving a panel or hiding
the document suspends scheduling; an already in-flight read or operation may
finish without opening a dialog, switching context or stealing focus. Reentry
coalesces the required fresh read and preserves disposable context. Late or
failed reads retain labelled last-known facts, not invented Offline/empty
inventory. A retained snapshot is never a current vehicle report.

### <a id="ui-int-013"></a>UI-INT-013 — Independent ownership and mutation conflicts

Installed operator mutations are serialized by the existing owner/writer.
Read-only navigation and independent observations remain available. Each
operation retains exact team, candidate, profile, external-object and resource
identity; uncertainty blocks conflicting effects and never queues blind replay.

The expanded concurrent profile allows disjoint producer operations only when
candidate/digest/profile, resulting Cloud object, Batch/Campaign, Unit and Set
scopes do not overlap. Provisioning, identity retirement, source handover/reset
and Finish are run-exclusive in either profile. Helper BUSY/WAITING describes
local capacity, not an invented Aos Cloud lifecycle restriction.

### <a id="ui-int-014"></a>UI-INT-014 — Perspective-local source failure

Failure or staleness of one team-owned backend is shown in that team's selector
and release story without marking the other teams or AosCloud offline. A shared
AosCloud read failure may affect multiple release cards, but it still does not
change CARLA/Gateway evidence or vehicle external-connectivity state. Section 7
defines the exact visible failure vocabulary and recovery actions.

### 2.2 Section 2 acceptance criteria

The interaction requires: exactly three producer perspectives;
OEM Release Authority as a persistent non-selectable governance role outside
the teams; per-team focus/scroll preservation; independent operations with
exact resource-scoped conflicts; the deterministic compact-summary priority;
and silent hidden-team refresh limited to the header summary. No additional producer, automatic global step or interrupting success popup is introduced.

## 3. Current Vehicle and Test-to-Production Handover


### 3.1 Audience vehicle terminology and global state

The audience UI and dedicated Cloud cohort use `Test Vehicle` for the technical
Validation Unit (`VU`) assigned to the validation-enabled Unit Set titled
`AosEdge SDV Demo / Test Vehicles`. It uses `Production Vehicle` for the
technical Production Unit (`PU`) assigned to the non-validation Unit Set titled
`AosEdge SDV Demo / Production Vehicles`. Both belong to the one-time
`AosEdge SDV Demo Fleet`. The
technical terms remain available in Details and evidence where exact Cloud
objects are relevant, but they are not the primary audience labels.

### <a id="ui-int-015"></a>UI-INT-015 — One selected vehicle binding

Installed use has exactly one owned Test and one selected live CARLA/Gateway
binding. Header, release actions and product evidence refer to that same
binding; actor navigation cannot change it. Before attachment or during
uncertainty, display not assigned/changing/unavailable truthfully. Expanded
use adds a Production role but still permits only one source owner at a time.
Neither retained identity nor Cloud Online proves live attachment.

### <a id="ui-int-016"></a>UI-INT-016 — Expanded-profile vehicle handover

Scope: expanded Validation/Production use. Handover explicitly detaches the
old Unit, proves release of its source, performs the canonical reset/new
generation and then assigns the same source exclusively to the other Unit.
Bind exact authenticated peer, contract, generation, time and frame range.
Uncertain detach/reset or overlapping evidence blocks the next assignment.
The sequence is repeatable in both directions and never changes software
versions, provisions again, mixes event histories or claims two CARLA vehicles.
The installed single-Test flow exposes no fictitious Production continuation.

### <a id="ui-int-017"></a>UI-INT-017 — Honest transition and failure state

The header changes to `Changing vehicle...` while handover is in progress. It
shows the new Current Vehicle only after the source gate, Gateway session and
first post-reset evidence are all proven. If the outcome is failed, uncertain
or unreconciled, the header shows `Current Vehicle unavailable` with a factual
reason and recovery action. It never guesses the result, labels both vehicles
current or silently falls back to the previous vehicle.

### 3.2 Vehicle-state policy for software updates

The demo deliberately distinguishes a vehicle-critical Platform FOTA update
from QM Service SOTA updates. This is an audience-visible policy distinction,
not a project-side replacement for AosEdge lifecycle enforcement.

### <a id="ui-int-018"></a>UI-INT-018 — Platform FOTA requires Safe Stop

Every Vehicle Data Platform Component release card shows:

> Vehicle state required: Safe Stop

OEM Release Authority may authorize delivery of that Platform FOTA to the
current Test or Production Vehicle while it moves. After delivery begins, the
card shows native `AosEdge Platform: ACTIVATING`, the factual Gateway condition
`Vehicle Gateway: Safe Stop not established`, and the clearly derived audience
explanation `Waiting for Safe Stop before application`. On a first install the
empty VDP slot remains empty; on a replacement the previous healthy release
remains active. The fixed Vehicle Controller offers `Enter Safe Stop`. The
application remains blocked until current Gateway evidence confirms the exact
stable Safe Stop condition.

AosCloud remains authoritative for the authorized desired update and delivery
records; it is not claimed to know whether the physical vehicle is moving.
The factory-installed OEM Component Runtime inside AosCore Service Manager is
the current-demo enforcement point: it gates destructive stop/removal and
activation on the accepted policy through a separate read-only Gateway/VISS
vehicle-state provider. The Demo UI presents native lifecycle state and
factual Gateway state, and may derive the bounded human-readable waiting
explanation from those two fresh facts. That explanation is not an AosCloud or
AosCore lifecycle state. Native runtime reason codes are available only through
the accepted on-demand native-log flow; the UI does not invent a continuously
available runtime-status interface, implement or emulate the gate.

The vehicle remains in Safe Stop throughout Platform FOTA application and
readiness confirmation. Success does not automatically resume driving. A
failed or uncertain update also leaves the vehicle stopped until the operator
selects an explicit, permitted recovery action.

### <a id="ui-int-019"></a>UI-INT-019 — Service SOTA may be applied in motion

Brake Health and Tire Health are QM services. Their release cards show:

> Vehicle state: In-motion update allowed

Their protected SOTA actions do not require Safe Stop solely because the
vehicle is moving. All other authority, dependency, recipient, evidence and
readiness gates remain unchanged. The UI never generalizes this QM demo claim
to arbitrary services or automotive software.

### <a id="ui-int-020"></a>UI-INT-020 — Expanded-profile Production rollout order

Scope: expanded release governance. Show owning-team acceptance and exact OEM
authorization before Production rollout. Apply the accepted VDP before a
dependent service and independently observe readiness. G3/G4 remain derived
capability milestones, not combined releases/Campaigns or automatic approval.
Production demonstrates released behavior with the same accepted bytes, not
a second product-validation lane.

### 3.3 Section 3 acceptance criteria

Verify one exact selected vehicle/source independent of actor navigation,
truthful transition/failure state and the motion-policy split: native OEM
Safe Stop gates Platform FOTA; accepted QM SOTA may apply while moving.
Expanded use additionally proves repeatable exclusive Test/Production handover.
No UI safety duplicate or Cloud physical-motion inference is allowed.

## 4. Platform, Brake and Tire Linear Release Stories


### 4.1 Common audience release story

Installed use shows actor-scoped prepare/sign/publish, first service assignment
and exact installation/result observations through contextual controls.
Functional V1/V2/V3 and allocated Cloud release numbers remain distinct. The
UI does not force all versions into five-stage cards or invent missing Pending
transitions. Expanded governance adds its exact acceptance/authorization steps
without changing product ownership, native lifecycle or motion policy.

### <a id="ui-int-021"></a>UI-INT-021 — Distinct release facts

Keep preparation, signing, publication, assignment/delivery, installed state
and functional evidence distinct. The installed Presenter uses contextual
actions and observations, not mandatory five-stage cards. First service
deployment assigns its identity once; later versions reuse it. A missed
intermediate Pending state may be replaced by an authoritative terminal read,
never by fabricated historical transitions. Expanded governance additionally
records Test acceptance and Production authorization without merging them.

### <a id="ui-int-022"></a>UI-INT-022 — Test validation and acceptance

Test is the validation role. A qualifying test binds exact artifact/profile,
Unit/native instance, source interval and result; Cloud Running or a completed
button request is insufficient. Owning-team acceptance is a separate explicit
engineering decision. Expanded Production promotion requires that accepted
evidence. An ordinary installed demonstration is not a complete qualification
dossier or permission to promote.

### <a id="ui-int-023"></a>UI-INT-023 — Expanded-profile released operation

Scope: expanded Production operation. Deliver the identical Test-accepted
artifact without rebuild, re-sign or re-upload. Independently confirm native
delivery/readiness and show live released behavior. Do not call this a second
product test, substitute replay or present one vehicle rehearsal as fleet-scale
or hardware-safety qualification.

### <a id="ui-int-024"></a>UI-INT-024 — Platform component release story

Platform release actions use the selected OEM context and verified unsigned
prepared VDP content. The full story publishes V1 before provisioning; a
deliberately selected warehouse variant may publish a higher profile and must
not claim skipped chapters. Reconcile publication, exact installation/profile
and real functional behavior separately. Native component application waits
for Safe Stop; Cloud inventory has no VDP process-health field. Publish each
next version only after the preceding one is installed and checked. Expanded
Production authorization uses the accepted governance path, not another
Platform authority or a combined G3/G4 release.

### <a id="ui-int-025"></a>UI-INT-025 — Brake service release story

Brake V1 captures bounded vehicle-derived windows, V2 adds local condition
analysis, and V3 preserves that model and adds typed advisory. Publish with
the associated SP; assign the exact Brake identity to Test through OEM once,
preserving Tire. Later higher versions reuse that identity. Installation,
input/episode readiness, backend receipt and Gateway application are different
facts. QM service updates may occur while moving; Reset affects only Brake
model/advisory and preserves history/queues. Expanded promotion retains its
independent acceptance and same-byte rollout obligations.

### <a id="ui-int-026"></a>UI-INT-026 — Independent Tire service story

Tire has one functional V1 profile consuming the VDP V3 dynamics contract.
It estimates locally, retains bounded state/outbox, delivers to its own backend
and requests its own typed inspection advisory. It neither depends on Brake
service state nor requests another platform capability. Sharing the installed
SP does not merge product storage or authority. Reset is Tire-only. The fixed
CPU-load/isolation experiment is a retained qualification obligation, not an
implemented action or an inference from a CPU graph.

### <a id="ui-int-027"></a>UI-INT-027 — Dependencies and independent evolution

Every Service card shows its required VDP version and the actual version on the
intended vehicle. A release remains visible and inspectable when compatibility
is absent. Until native AosCloud SOTA-to-VDP admission is available and
qualified, the UI shall not implement a substitute admission controller or
claim Cloud-native rejection. Provider-first ordering, evidence-backed OEM
authorization and fail-closed Service readiness remain the current behavior;
an installed Service without its required telemetry reports `Platform update
required` rather than a fabricated healthy result.

Switching Platform, Brake or Tire perspective never changes Current Vehicle or
another team's release state. Disjoint operations may progress independently;
visual order does not disable a version and one team's completion does not
advance another team automatically.

### <a id="ui-int-077"></a>UI-INT-077 — G3 and G4 are derived capability milestones, not release groups

`G3` and `G4` summarize audience capability without creating a deployable
Cloud object, combined approval or atomic multi-artifact transaction:

| Milestone | Derived completion condition |
| --- | --- |
| `G3 · Edge brake assessment` | Exact VDP v2 and Brake v2 are independently accepted, separately OEM-authorized, actually ready on the Production Vehicle and the released v2 behavior is observed |
| `G4 · Brake advisory` | Exact VDP v3 and Brake v3 meet the same independent lifecycle conditions and the released advisory round trip is observed |

Each VDP and Brake release retains its own candidate identity, publication,
Verification Batch, Test authorization, owning-team acceptance, Fleet
Validation state, OEM Production authorization, Campaign/per-Unit result and
readiness. OEM Release Authority authorizes one exact artifact at a time. The
UI shall expose no `Approve G3`, `Approve G4`, `Deploy group` or inferred atomic
rollback action.

Production ordering is provider-first for each dependent pair. The VDP release
is authorized and becomes actually ready first, including Safe Stop for FOTA;
the previous backward-compatible Brake Service remains operational. Only then
may the dependent Brake Production action proceed. Failure or delay of Brake
does not roll back the accepted VDP release, and failure of either release
leaves the derived milestone incomplete without changing the other team's
lifecycle state.

The main view may show a derived summary such as `G3 capability · 1 of 2
releases ready`. Platform cards use `Enables Brake v2/v3`, while Brake cards use
`Requires VDP v2/v3`. The summary is calculated from fresh authoritative
AosCloud/AosCore state plus the accepted Function evidence; it is not written
back as Cloud lifecycle state.

### 4.2 Section 4 acceptance criteria

Verify independent Platform/Brake/Tire purposes, profile prerequisites, serial
version publication, actual installation and corresponding live results.
G3/G4 derive from the compatible installed graph and behavior, not a combined
Cloud release group or approval. Expanded governance additionally requires
one-time publication, Test validation/producer acceptance, separate exact OEM
Production authorization and identical-artifact released operation, not a
second product test.

## 5. Action, Authority and Authoritative-Result Contract


Section 5 defines the contract behind a visible button. It does not define
modal layout or error styling, which belong to Sections 6 and 7. A button is
never the authority by itself: it presents an explicit human decision to the
accepted execution surface, then waits for the authoritative owner of the
result.

### 5.1 Action classes and organizational actors

### <a id="ui-int-028"></a>UI-INT-028 — Every action declares its class and actor

Every visible action belongs to exactly one of these classes:

| Action class | Meaning | Possible organizational actor |
| --- | --- | --- |
| Local navigation | Change team perspective, scroll position or open/close read-only Details | Presenter |
| Authoritative read | Refresh current Cloud, vehicle, backend or run-state facts without changing them | Presenter through the Demo UI |
| Producer publication | Sign and submit one frozen producer-owned candidate | Platform, Brake or Tire Team |
| Producer acceptance | Accept the exact Test Vehicle validation result for one candidate | Owning Platform, Brake or Tire Team |
| OEM deployment authorization | Authorize one exact Test deployment or Production rollout | Independent OEM Release Authority |
| Shared vehicle operation | Select the current vehicle, enter/resume Safe Stop, select drive mode or change vehicle external connectivity | Presenter through the accepted Orchestrator or Vehicle Controller surface |
| Function proof operation | Run the fixed Tire CPU-isolation proof and observe its result | Tire Team |
| Run-exclusive environment or lifecycle operation | Start or restore the local environment, provision fresh Units, perform exclusive live-source handover/reset or execute R0 retirement/reset | Demo Solution operator through the Demo Orchestrator |

`OEM Release Authority` is never shown as a producer team or selectable team
perspective. Producer acceptance is not OEM deployment authorization. The same
human presenter may exercise both decisions. Platform Team operations and OEM
Release Authority operations use one OEM Cloud user certificate in the first
demo, but the UI and native helper bind them to different organizational
actors, decision purposes, operation allowlists and lifecycle objects. This is
an organizational and application-level separation, not a claim of two OEM
certificate identities or Cloud-enforced separation of duties.

### <a id="ui-int-029"></a>UI-INT-029 — Local actions and protected actions

Local navigation and read-only refresh execute immediately and never open a
mutation confirmation. Every publication, Cloud lifecycle mutation,
producer-acceptance mutation, Unit Set change, provisioning, retirement,
functional proof command or destructive cleanup is a protected action.

`backend-reset` executes with one
explicit click on the named Brake/Tire backend card's **Reset Driver Advisory**
button. It still uses protected session/request-ID/serialization and uncertain
outcome reconciliation; it is not a read. The detail popup retains outcome
and history but no duplicate reset action. Only a correlated Gateway CLEAR
establishes completion. All other protected actions retain confirmation.
Use **Resetting driver advisory…** during
submission/waiting and **Driver advisory reset** after that confirmation;
the native `backend-reset` / `reset-scenario` commands and behavior are unchanged.

A protected action otherwise requires an explicit verb-specific confirmation. The
confirmation shall identify:

- the organizational actor and active authority context;
- the exact action and whether it is publication, acceptance, authorization,
  vehicle operation, proof or cleanup;
- the candidate, version and available digest identity;
- the exact Test or Production target and effective recipients, when relevant;
- required permissions, dependencies and current evidence status;
- whether the operation is reversible, forward-repair-only or destructive;
  and
- the current factual reason for every blocked prerequisite.

`Cancel` has no external side effect. Generic labels such as `Approve`, `Run`
or `Continue` are insufficient where the actor or target would be ambiguous.
The primary confirmation uses the explicit action, for example `Publish Brake
Health v2`, `Authorize Test deployment`, `Accept Test result` or `Authorize
Production rollout`.

### <a id="ui-int-030"></a>UI-INT-030 — Browser and credential boundary

The demo has no Cloud account, certificate or generic `demo credential` of its
own. The browser also receives no OEM, Service Provider, Unit, backend or
signing credential. It sends only a bounded action identifier and reviewed
parameters to an authenticated Mac-local application surface. That surface
delegates to the fixed native helper, Demo Orchestrator, Vehicle Controller or
matching Function backend adapter.

Installed first use needs one OEM certificate and one associated SP certificate.
Platform publication/delivery profiles share the OEM identity but remain
non-interchangeable allowlists. Brake and Tire have independent service,
publication and backend identities even when both profiles use the same SP.
The expanded two-provider profile additionally requires independent SP owner
domains/certificates and proof of cross-provider isolation; one shared SP is
not that proof.

The browser receives no certificate, secret, path, arbitrary URL/profile or
artifact selector. The native helper binds each action to its fixed configured
credential/profile. Setup's native certificate selection is a separate local
configuration boundary, not a credential input to the Presenter browser.
Credentials remain outside containers, VM overlays, journals and Git. Admin
credentials are never a fallback. Keep actor/release authority distinct from
certificate identity; these local profiles do not create cryptographic
separation between two actors sharing one OEM certificate.

### 5.2 Fresh prerequisites and authoritative completion

### <a id="ui-int-031"></a>UI-INT-031 — Fresh preflight at confirmation time

An enabled button is a presentation hint, not permission to use stale data.
Immediately before confirmation and again before the protected call, the
application re-reads every prerequisite owned outside the UI. A changed
candidate, role, permission, target, Unit Set membership, pending recipient,
dependency, evidence result, current vehicle or vehicle state cancels the
prepared intent and returns it to `BLOCKED` with a factual reason.

For installed Test deployment, fresh proof binds the exact configured
verification Set/current Test and effective pending recipients. Expanded
deployment additionally proves Verification Unit Set=`{VU}`, Production
Unit Set=`{PU}` and no matching Production pending reference. Expanded
Production rollout requires the accepted Fleet Validation Batch, unchanged
artifact identity, expected Fleet, sole Production Unit Set target and current
membership=`{PU}`.

Platform FOTA authorization does not require the vehicle to be stopped.
Before destructive OEM-runtime application, however, fresh factual Gateway
state shall satisfy the accepted Safe Stop policy. The Demo UI does not issue
a substitute `Apply` mutation or claim that AosCloud checks motion: it observes
the authorized delivery, shows native `ACTIVATING`, shows fresh Gateway state
and derives the bounded audience waiting explanation when necessary. Native
runtime reason codes remain available through the explicit on-demand log flow.
The UI advances only after actual/readiness state confirms application.

### <a id="ui-int-032"></a>UI-INT-032 — Authoritative source by result type

The UI uses the following result owners and never substitutes a local visual
state for them:

| Result | Authoritative source |
| --- | --- |
| Prepared candidate identity and digest chain | Producer manifest, pinned Demo Release Set and helper verification receipt |
| Published Component/Service Version, Verification Batch, Fleet Validation Batch and Campaign | Fresh AosCloud API read |
| Unit, Node, Unit Set membership, desired/actual software and readiness | Fresh AosCloud API read |
| Producer Test acceptance | Explicit owning-team decision bound to the exact Test evidence and corresponding Fleet Validation operation; it is never inferred from a passing test |
| OEM Test or Production authorization | Explicit `oem-delivery` operation and subsequent AosCloud re-read |
| Current Test/Production Vehicle and source handover | Demo Orchestrator exclusive-live-source contract |
| Motion, Safe Stop, drive mode and vehicle external connectivity | Vehicle Controller/Gateway/CARLA state, with Engineering Telematics as independent visible evidence |
| Brake or Tire functional result | Matching Function backend, correlated to current Unit, software and vehicle event |
| In-vehicle advisory | KUKSA/Gateway path as shown by Engineering Telematics |
| Tire quota enforcement result | Fresh AosCloud service usage/state plus the accepted baseline-bound qualification evidence; the Tire control response alone is not proof |
| Qualification Status | Current bounded local qualification status derived from the sealed dossier and exact baseline comparison; it is not Cloud lifecycle state or deployment authority |
| Platform FOTA waiting explanation | Derived Representation Layer interpretation of fresh native `ACTIVATING` plus fresh Gateway `Safe Stop not established`; native reason codes remain available through explicit on-demand logs |
| Run readiness, interruption recovery and R0 completion | Demo Orchestrator reconciliation against Cloud, backend, VM and local-resource owners |

An HTTP success, helper exit code, animated progress indicator, CARLA event or
passing local check alone never advances a Cloud lifecycle stage.

### <a id="ui-int-033"></a>UI-INT-033 — Operation-state progression

Protected external operations use the accepted current-run registry and the
following visible progression:

```text
READY or BLOCKED
  -> explicit confirmation
  -> SUBMITTING
  -> WAITING, RECONCILING, or UNCERTAIN
  -> authoritative classification
  -> COMPLETED, READY for a new confirmed attempt, or RECOVERY REQUIRED
```

The application records the exact intent before the call. A successful HTTP
response enters `RECONCILING`, not `COMPLETED`. Response loss, process loss or
an ambiguous helper outcome enters `UNCERTAIN`. Fresh authoritative reads
classify the external effect as `APPLIED`, `NOT_APPLIED`, `CONTRADICTORY` or
`UNOBSERVABLE`:

- only `APPLIED` may complete and advance that exact action;
- `NOT_APPLIED` may return to an actionable state only after presenting the
  result and obtaining a new confirmation;
- `CONTRADICTORY` and `UNOBSERVABLE` require recovery and keep overlapping
  actions blocked; and
- no state is translated into an invented AosCloud lifecycle label.

Section 7 defines the exact wording and visual treatment of these states.

### <a id="ui-int-034"></a>UI-INT-034 — Serialization and expanded concurrency

Installed protected mutations share one existing writer. Conflicting or
uncertain operations block another effect while read-only views remain usable.
For expanded disjoint-resource concurrency apply the exact conflict scopes in
UI-INT-013; never infer permission from different tabs/directories. No automatic
cross-team queue, broad global status failure or silent mutation replay is
introduced. Run-exclusive identity/source/cleanup operations remain exclusive.

### <a id="ui-int-035"></a>UI-INT-035 — Explicit composition and no blind retry

Only the accepted composed actions may execute their declared bounded steps:
Create prepares the owned controller/backends; Provision connects the same
Unit/source; Finish retires the exact Test. Their progress exposes distinct
owner results and persists intent before external effects. A response loss
requires authoritative reconciliation, not another create/upload/provision.
No action silently advances another release, accepts evidence, approves
Production or starts the next run. Expanded multi-call Campaign authorization
retains per-call journal and reconciliation boundaries.

### 5.3 Visible action matrix

### <a id="ui-int-036"></a>UI-INT-036 — Action-to-authority matrix

| Visible action | Actor and owner | Required independently observed result |
| --- | --- | --- |
| Select actor / open or close detail | Presenter, read-only view | Same run/vehicle/profile context; fresh scoped facts, no mutation |
| Restore workspace layout | Existing host composition owner | Native/browser windows restored; no vehicle journal or Cloud action |
| Create Controller | Existing run-exclusive Demo Control | Fresh identity-free Test and owned local preparation, not a Cloud Unit |
| Start simulator | Existing simulation owner | One CARLA/Gateway/native session; detached until Unit attachment |
| Prepare / sign / publish | Selected producer OEM/SP through native owner | Exact unsigned/signed/Cloud identity chain; known uncertainty is reconciled |
| Provision Test | Official SDK and Demo Control | Exact same Unit/Node, Online/membership and stationary source attachment |
| Deploy service to Test | OEM Subject owner | Exact service identity assigned once, peer preserved; actual version/instance reread |
| Enter Safe Stop / drive / prepared maneuver / Return to road | Native Driving Control | Physical frame confirms state; Return to road preserves models and ends stationary Manual |
| Reset Driver Advisory | Selected service/backend | One-click protected submission; pending versus correlated applied outcome; history and peer preserved |
| External network OFF/ON | Existing selected-Unit connectivity owner | Cloud and both backend routes change atomically; in-vehicle/admin paths remain |
| Start controller / Stop demo and keep data | Existing runtime owner | Same Test retained; no provisioning, deletion or automatic Autopilot |
| Delete Test / Continue Finish | Existing exact-target retirement owner | Reconciled owned Cloud/backend/file cleanup; no automatic next run |
| Close Presenter (keep demo running) | Presenter window owner | Window closes without claiming runtime stop |

Expanded governance additionally requires separate Test-validation acceptance,
exact OEM Production authorization, exclusive Test/Production source handover
and same-byte released-operation proof. Role-scoped native logs and the fixed
Tire isolation control retain their allocated requirements; unimplemented or
unqualified actions are not presented as available or PASS. No action gains
credentials, arbitrary command selection, a second scheduler or Cloud authority.

### <a id="ui-int-073"></a>UI-INT-073 — Lifecycle-aware infrastructure preflight

Validate the selected installed package, private instance, saved access,
backend images and exact owned resources before an action. Open SDV Lab opens
Presenter only. Start controller restores the same retained Test; it does not
create/provision again or resume Autopilot. Missing Docker requires an operator
prerequisite action; normal preflight never opens its Dashboard, restarts the
shared Engine or adopts another project's containers. An incomplete journal
enters explicit recovery, not new manufacture. Host sleep/wake recovery is
outside the current profile.

### <a id="ui-int-074"></a>UI-INT-074 — Profile-bound manufacture

Create Controller explicitly makes one fresh identity-free Test from the
selected immutable Factory, with no VDP/service or Cloud Unit. It may compose
owned boot/backend preparation but never provisions automatically. Show local
manufacture separately from Cloud Online and installed software. Expanded
manufacture additionally requires a distinct Production overlay and evidence
of non-shared system/Node/SSH/certificate identity. Never clone a provisioned
overlay or modify the backing image.

### <a id="ui-int-075"></a>UI-INT-075 — Provisioning establishes the Test substrate

Provision uses the official SDK once for the already created Test, reconciles
its exact native system UID and Cloud Unit/Main Node, observes Online and
verification membership, then attaches the same live source in stationary
Manual. Preserve actor and generation; no duplicate simulator/control panel.
Partial registration resumes against the same identity, never another SDK
attempt. Safe Stop for VDP application remains a subsequent explicit vehicle
action. Expanded use independently provisions its Production role.

### <a id="ui-int-076"></a>UI-INT-076 — Finish retires the owned run

Finish is a confirmed destructive action naming the exact Test. Quiesce owned
source/VM/backends, reconcile identity and Subject/Set effects, prove Unit/Node
absence and exact backend cleanup, dispose of owned working files and journal
last. Preserve unrelated/Production state, credentials, permanent Subjects/Sets,
Factory, published releases and release continuity. Continue Finish resumes
reconciled remaining stages, not repeated effects. Expanded R0 additionally
retires its explicitly owned Production role. No next Create/Provision starts
automatically; ordinary Stop/Start instead retains the same run.

### 5.4 Section 5 acceptance criteria

#### Control-plane credential topology — expanded profile

The accepted contract is that neither the Demo UI nor the demo solution owns a Cloud
identity. One OEM user certificate supports the fixed `platform-oem` and
`oem-delivery` operation profiles, while Brake and Tire use two different
Service Provider owner domains and two separate SP certificates. The UI actor
model remains distinct from certificate identity. This records no claim of
cryptographic separation between Platform Team and OEM Release Authority in
the first demo, and the Admin certificate is never part of the flow.

#### Production authorization per exact release — expanded profile

The accepted contract exposes one audience-visible `Authorize Production rollout`
decision for each exact release card. Its protected confirmation exposes the exact accepted artifact,
Fleet Validation Batch, Production Unit Set and bounded technical sequence.
The backend may then execute Campaign create, authoritative read, target
verification, approval and final reconciliation without additional audience
buttons.

This is one organizational Release Authority decision for one artifact, not a claim of one
atomic AosCloud transaction. Every external mutation has its own journal entry
and reconciliation boundary. A mismatch, timeout or uncertain outcome stops
the sequence; no Campaign is blindly recreated or approved, and no later call
executes until the previous effect is authoritatively known.

G3/G4 expose no combined authorization. Their VDP and Brake Production
decisions remain separate, and provider readiness is freshly proved before the
dependent Service action becomes eligible.

#### Application, lifecycle and optional operational actions

There is no audience Apply update button: AosCore applies the authorized
component under its Safe Stop policy. Driving Control owns physical stop and
explicit driving resumption. Service SOTA does not wait for Safe Stop.
UI-INT-073 through UI-INT-076 define preflight, manufacture, provisioning and
retirement at their exact profile scopes. Recheck is read-only; native logs
remain optional and role-scoped; a drive restart preserves vehicle identity
and software lifecycle. Recovery cannot introduce another product decision.

<a id="accepted-during-section-5-review--no-audience-apply-update-action"></a>
<a id="accepted-during-section-5-review--global-demo-lifecycle-chapters"></a>
<a id="accepted-during-section-5-review--complete-first-demo-action-inventory"></a>

## 6. Details Modal and Disclosed Information


### 6.1 Purpose and interaction boundary

`Details` explains what one release is, what it changes, what it requires and
why the currently selected lifecycle action is or is not ready. It is a
read-only audience explanation of already prepared or authoritatively observed
facts. It is not an artifact editor, approval form, Cloud console, raw evidence
viewer or alternate lifecycle path.

### <a id="ui-int-037"></a>UI-INT-037 — One read-only modal in the right workspace

Selecting `Details` for a release stage opens one modal confined to the right
browser workspace. The shared header and complete left vehicle-evidence
workspace remain visible and do not move, resize or scroll. The release story
behind the modal keeps its exact team, release, lifecycle stage, Current
Vehicle and scroll position.

The modal:

- identifies the selected product, version, owning producer team and lifecycle
  stage in its header;
- scrolls internally when its content exceeds the available height;
- has a stable header and footer with only `Close` as its footer action;
- closes through the explicit close icon, `Close` or `Escape`;
- returns focus to the exact `Details` control that opened it; and
- performs no read, refresh, mutation, navigation or state transition merely
  because it was opened or closed.

Keyboard focus remains inside the modal until it is closed. Clicking outside
the modal does not silently dismiss it. Nested modals are forbidden. A
protected-action confirmation and `Details` are never open at the same time;
the presenter closes one before opening the other. No publish, authorization,
acceptance, deployment, vehicle or recovery primary action appears inside
`Details`.

### 6.2 Human-first information hierarchy

### <a id="ui-int-038"></a>UI-INT-038 — Summary first, technical drill-down second

The first viewport answers five audience questions in plain language:

1. **What is this?** — product, release and owning OEM producer team.
2. **Why does it exist?** — one concise purpose statement and the user or OEM
   value delivered by this version.
3. **What changes?** — the bounded capability delta from the previous version.
4. **What does it need?** — vehicle/platform compatibility, access and resource
   summary.
5. **Where is it now?** — selected lifecycle stage, intended/current vehicle
   and authoritative readiness or blocking reason.

The modal then provides a collapsed `Technical details` disclosure for exact
non-secret contract and evidence values. The disclosure is closed by default
each time a different release-stage `Details` control is opened. It is not raw
JSON and does not repeat fields that have no meaning for the selected product
or stage.

The audience summary uses `Test Vehicle` and `Production Vehicle`. Exact
AosCloud titles `AosEdge SDV Demo Fleet`, `AosEdge SDV Demo / Test Vehicles`
and `AosEdge SDV Demo / Production Vehicles`, plus technical terms such as
Verification Batch, Validation Unit, Fleet Validation Batch and Campaign,
appear only where they explain a real lifecycle decision or inside the
technical disclosure.

### <a id="ui-int-039"></a>UI-INT-039 — Common Details content model

Every release-stage modal uses the following ordered groups:

| Group | Audience summary | Technical disclosure where applicable |
| --- | --- | --- |
| Release | Product, semantic version, owning OEM team, purpose and capability delta | Candidate ID, artifact kind, target architecture, immutable prepared-content state and producer-manifest reference |
| Vehicle compatibility | Required vehicle/platform capability, current installed capability, compatible/not-ready result and motion policy | Exact required/actual VDP or Factory Image compatibility, component runtime baseline and FOTA versus QM Service SOTA classification |
| Data contract and Service quotas | Plain-language signals/advisory access; for Brake and Tire Services, the approved Service-quota summary | Exact KUKSA/VSS paths and read/write modes; for Services only, signed requested and OEM-approved quota values with units |
| Lifecycle and target | Current stage, responsible actor, Test or Production target and factual readiness/blocking reason | Sanitized Cloud-object fingerprints, intended/effective recipient proof and current desired/actual/readiness state |
| Evidence and authority | Required evidence categories, freshness and whether the owning team or Release Authority has made the relevant decision | Sanitized evidence references, source fingerprints, observation times and exact decision/result codes |
| Integrity | Human-readable statement that the same frozen candidate is being followed | Prepared, manifest, signed/uploaded and Cloud-observed digests, with their verified mapping and observation status |

Static release-contract values come from the pinned producer manifest and Demo
Release Set. Dynamic lifecycle, target, vehicle, backend and readiness values
come from the authoritative sources accepted in Section 5. The UI does not
combine them into an invented state.

### 6.3 Stage-specific explanation

### <a id="ui-int-040"></a>UI-INT-040 — Details follows the selected release stage

`Details` belongs to a specific visible stage, not only to the release card as
a whole. The common groups remain recognizable while the lifecycle and
evidence emphasis changes as follows:

| Selected stage | Details must emphasize | It must not imply |
| --- | --- | --- |
| Producer Team publishes candidate | Candidate is already built and content-frozen; purpose, delta, artifact/manifest integrity, publication owner/profile and pre-publication evidence | That opening Details signs, rebuilds, qualifies, publishes or authorizes the candidate |
| OEM Release Authority authorizes Test deployment | Exact candidate, Test Vehicle target, effective `{VU}` recipients, required permissions/dependencies, pre-deployment evidence and independent authority context | That publication itself approved deployment, or that the browser/OEM authority changes the artifact |
| Test Vehicle validation and Producer Team acceptance | Test delivery/actual/readiness, selected Test scenario and integration evidence, observed functional result, evidence freshness and separate pending/completed producer acceptance | That a passing check automatically accepts the release, or that Production has been validated |
| OEM Release Authority authorizes Production rollout | Accepted Test result, unchanged artifact/digest chain, Fleet Validation state, sole Production Unit Set target, effective `{PU}` recipients and applicable verification/validation/integration/homologation evidence | That the Release Authority developed the release, that a new build exists or that Production rollout is already complete |
| Production rollout and live operation | Campaign/per-Unit result, Production desired/actual/readiness, released behavior and current Function-backend/in-vehicle outcome | That Production is a second product-validation lane or that CARLA behavior alone proves Cloud delivery |

For Platform FOTA, both Test and Production Details show the current Gateway
vehicle facts and the explicit rule `The in-vehicle OEM Component Runtime
applies this Platform update only after Safe Stop is proven`. Authorization may
already be complete while native state is `ACTIVATING`; the UI labels its
fresh-Gateway-based audience explanation `Waiting for Safe Stop before
application` as derived rather than as a Cloud state.
Brake and Tire QM Service Details instead
state that motion alone does not block SOTA application.

### 6.4 Freshness and incomplete information

### <a id="ui-int-041"></a>UI-INT-041 — Every dynamic fact exposes source and freshness

Each dynamic group shows its authoritative source class and observation time
or age. One group-level source/freshness line is sufficient when all rows came
from the same atomic read; mixed-source rows identify their source separately.
The accepted visible conditions are:

- `CURRENT` — observed within the accepted freshness rule;
- `STALE` — a prior value is visible but may no longer support a decision;
- `UNKNOWN` — the source cannot currently establish the value;
- `INCOMPLETE` — one or more mandatory facts or evidence references are
  missing;
- `REDACTED` — a known field is intentionally unavailable to the audience
  projection; and
- `NOT APPLICABLE` — the contract does not define that value for this release
  or stage.

A missing or stale row remains visible with its factual reason; it is never
silently omitted, rendered green or replaced by a cached success. Opening
`Details` does not refresh it. The separate read-only `Recheck current state`
action performs a fresh read and updates both the release card and any Details
modal opened afterward.

### 6.5 Identifiers, integrity, dependencies and resource limits

### <a id="ui-int-042"></a>UI-INT-042 — Exact integrity without private identity disclosure

Candidate IDs, semantic versions and SHA digests are non-secret release facts.
The summary uses a short digest fingerprint for readability; the technical
disclosure makes the complete digest available and allows an explicit
`Copy digest` action. Prepared, manifest, signed/uploaded and Cloud-observed
digests remain separately labelled and are never collapsed into one value
until their mapping has been verified.

The application binds exact Unit, Node, `system_uid`, Batch, Campaign and other
Cloud-object identities behind the Representation Layer. The browser receives
only `Test Vehicle` or `Production Vehicle` plus stable sanitized fingerprints.
The fingerprint is shown consistently in Details, protected confirmation and
result evidence so the audience can see that the same object is being used,
but the full private identifier is never disclosed or copied.

### <a id="ui-int-043"></a>UI-INT-043 — Access, dependency and quota presentation

The audience summary describes intent first: for example, `reads braking
telemetry`, `publishes a maintenance advisory` or `requires Vehicle Data
Platform Component v3`. Technical details may then show the exact reviewed
KUKSA/VSS paths, operation modes and contract version. They never show a JWT,
secret, token-exchange material or an authorization header.

Every Service release shows required and actual VDP versions for the selected
vehicle and one of `COMPATIBLE`, `PLATFORM UPDATE REQUIRED`, `UNKNOWN` or
`NOT INSTALLED`. Until native AosCloud dependency admission is available and
qualified, this is an evidence/readiness statement and OEM authorization gate,
not a claim that AosCloud rejected the Service candidate.

Brake and Tire Details show the signed requested and OEM-approved Service quota
values with their native units. Current utilization is shown only when freshly
read from the accepted AosCloud source and remains a separate observed fact.
Tire CPU-proof status is labelled as a demo proof control, not quota-
enforcement evidence. Vehicle Data Platform Component Details contain no
Service-quota or substitute component-resource table; they explain the data
contract, compatibility, Safe Stop policy, lifecycle and integrity instead.
They also contain no VDP application-store view: the persistent
slots/state/credentials tree belongs to OEM Component Runtime A/B working
storage and stores no VDP telemetry history or log archive.
Unsupported or unobserved Service limits remain `UNKNOWN`, never `enforced`.

### 6.6 Runtime-isolation evidence

### <a id="ui-int-044"></a>UI-INT-044 — Live isolation proof is separate from Details and telematics

Service quota definition belongs in Brake or Tire Service Details, but the
live Tire CPU-isolation exercise does not. When the Tire Team starts the fixed
proof from its Production live-operation stage, one compact sticky `Runtime
Isolation Evidence` panel appears in the right team workspace while the fixed
left vehicle-evidence workspace remains visible.

The panel is not embedded in the Engineering Telematics Dashboard. That
Dashboard retains its Gateway/KUKSA role and continues to show vehicle signals
and advisories. The isolation panel labels its different authoritative sources
and shows together:

- the exact approved Tire CPU quota, fresh observed Tire CPU usage and factual
  at-limit/throttling state;
- continuity of the same running Tire instance without restart or replacement;
- fresh Brake usage and health plus one successfully processed deterministic
  Brake event while Tire is loaded;
- AosCore, KUKSA, Gateway and Unit health; and
- post-stop Tire recovery without Service reinstall or restart.

The Tire load-control response is never presented as enforcement proof. The
verdict combines fresh AosCloud usage/instance state, the accepted baseline-
bound cgroup qualification evidence and concurrent Brake/platform functional
continuity. The UI states explicitly that this demonstrates isolation on the
qualified VM demo baseline and is not a real-hardware performance or automotive
safety claim.

### 6.7 Disclosure, redaction and team boundaries

### <a id="ui-int-045"></a>UI-INT-045 — Allowlisted browser disclosure

Details may disclose only reviewed release metadata, capability descriptions,
KUKSA/VSS contract paths, quota/resource values, digest values, vehicle aliases,
sanitized identity/evidence fingerprints, fixed status/reason codes and bounded
human-readable explanations.

The following are forbidden before data enters browser state:

- passwords, reusable credentials, JWTs, secrets, authorization headers,
  private keys, PKCS#12 content and private certificate material;
- credential/profile paths, protected local paths and personal absolute paths;
- VIN and full Unit, Node, `system_uid` or private Cloud-object identifiers;
- raw Cloud/helper/backend responses, unrestricted raw telemetry, unknown
  response fields and arbitrary free-form log text; and
- backend cleanup tokens, unredacted failure payloads or another producer
  team's private backend data.

Redaction is performed by the owning adapter before the browser projection.
The modal does not attempt to hide secrets with CSS or redact them after they
arrive in JavaScript state. A required redacted field remains visibly
`REDACTED` with a bounded reason rather than disappearing.

### <a id="ui-int-046"></a>UI-INT-046 — Perspective and evidence isolation

Platform Details may show Platform/Unit/system/VDP release evidence within the
accepted OEM scope. Brake Details may show only Brake candidate, Service and
backend evidence. Tire Details may show only Tire candidate, Service, backend
and Tire-proof evidence. The OEM Release Authority view embedded in a stage
shows the cross-domain decision summary necessary to authorize that exact
deployment, but it does not expose another team's raw backend payload or
credential boundary.

Changing producer perspective requires closing the modal first, as accepted in
Section 2. Reopening Details in the new perspective performs normal rendering
from that team's sanitized projection; modal state is not shared across teams.

### <a id="ui-int-047"></a>UI-INT-047 — Copy boundary

The installed profile provides no `Export all`, raw JSON, evidence-bundle
download or unrestricted copy action in Details. It may copy only an
allowlisted candidate ID, semantic version, full release digest, sanitized
evidence reference or sanitized object fingerprint. Copying uses the value
already present in the browser projection and never requests a more privileged
form from the helper.

The separately governed qualification dossier is not browsed or downloaded
through release Details.

### 6.8 Operational logs

### <a id="ui-int-048"></a>UI-INT-048 — Context-bound Operational Logs overlay

Native operational logs use a separate secondary action labelled `Platform
Logs` for Platform scope and `Operational Logs` for Brake/Tire Service scope,
not Details, Engineering Telematics, Function-backend evidence or a browser
tab. The action appears only for an installed/running release in the `Test
Vehicle validation` or `Production rollout and live operation` stage. It opens
one overlay confined to the right workspace while CARLA, Controller and
Engineering Telematics remain visible.

The originating release stage fixes and displays the vehicle alias, producer
owner, product/version and allowed log scope. The presenter cannot enter an
arbitrary Unit ID, Service, path, query, credential or Cloud endpoint. Platform
uses only accepted Unit/system/VDP scope; Brake uses only Brake Service scope;
Tire uses only Tire Service scope. No team can inspect another Function Team's
Service logs.

VDP diagnostics are standard output/error records captured by the native
systemd journal. VDP owns no log file, database, archive or retention policy.
The overlay delegates the fixed Platform request to the accepted
AosEdge/AosCloud delivery path and retains no second copy after the bounded
view is closed or deleted.

The overlay owns this bounded workflow:

1. `Request current logs` opens a verb-specific protected confirmation and
   delegates the fixed scope to the accepted native-log adapter.
2. The overlay shows the native AosCloud request state verbatim, its source and
   freshness. A separate audience explanation may identify missing vehicle
   external connectivity, but it never invents a Cloud lifecycle state.
3. `Recheck log status` performs only a fresh read and never resubmits the
   request.
4. When the native result is available, the overlay shows a bounded sanitized
   summary and scrollable redacted fragment; unrestricted raw output never
   enters browser state.
5. `Delete log request` is a protected deletion of the exact current request.
   R0 removes any current-run request/result not already deleted.

The overlay may expose only `Request current logs`, `Recheck log status`,
`Delete log request` and `Close` when each is applicable. It creates no ELK
path, second log archive or demo-run history. Closing it restores the exact
release-stage focus and scroll context. Details may at most show a sanitized
log-request reference relevant to the stage; it never requests, downloads,
renders or retains log content.

### 6.9 Reference content example

For `Brake Health v3` at `OEM Release Authority authorizes Production
rollout`, the first viewport would read approximately:

| Field | Audience value |
| --- | --- |
| What this release does | Adds an in-vehicle brake-maintenance advisory while keeping derived health results in the Brake backend |
| Owner | OEM Brake Function Team |
| Requires | Vehicle Data Platform Component v3 — compatible on Production Vehicle |
| Data access | Reads approved brake-health inputs and writes the approved maintenance-advisory path |
| Resource limits | Brake Service quota profile — approved; current usage observed separately |
| Test result | Accepted by Brake Team for this exact frozen release |
| Production decision | Awaiting independent OEM Release Authority authorization |
| Target | Production Vehicle / sole Production Unit Set recipient |
| Integrity | Candidate digest unchanged from the accepted Test release |
| Freshness | AosCloud and evidence projection observed at the displayed time; any stale source is called out individually |

`Technical details` would add exact non-secret paths, quota values, complete
digests and sanitized object/evidence fingerprints. It would not show Unit
UUIDs, certificates, tokens, raw Cloud responses or Brake backend payloads.

### 6.10 Section 6 acceptance criteria

Verify the accepted behavior:

1. one read-only right-workspace Details modal with a human-first summary,
   collapsed technical disclosure and no lifecycle action;
2. stage-specific content, explicit source/freshness, full non-secret release
   digests and fingerprint-only private vehicle/Cloud identities;
3. KUKSA/VSS access and approved quota disclosure for Brake/Tire Services,
   with no Service quota or substitute resource table for VDP Components;
4. one separate sticky Runtime Isolation Evidence panel during the Tire proof,
   leaving Engineering Telematics limited to Gateway/KUKSA vehicle evidence;
5. one separate context-bound, role-scoped logs overlay labelled `Platform
   Logs` for Platform scope and `Operational Logs` for Brake/Tire scope at Test
   validation and Production live-operation stages, using native AosCloud log
   delivery without ELK, a second archive or unrestricted raw output; and
6. the accepted allowlist, redaction, team-isolation and bounded-copy policy.

This acceptance authorizes no UI implementation, log request, CPU load,
Cloud operation or vehicle action. Section 7 defines the failure and recovery
presentation for these accepted surfaces, but it may not broaden
their authority, sources, scopes or disclosed data without reopening Section
6.

## 7. Failure, Offline and Recovery States


### 7.1 State layers and scope

### <a id="ui-int-049"></a>UI-INT-049 — Do not flatten three different state layers

Every release and protected operation preserves three separately labelled
state layers:

| Layer | Examples | Meaning |
| --- | --- | --- |
| Authoritative source state | Native AosCloud Batch/Campaign/Unit/Service value, AosCore readiness, Gateway motion/connectivity, Function-backend result | What the owning external source currently reports |
| Demo orchestration state | `READY`, `BLOCKED`, `SUBMITTING`, `WAITING`, `UNCERTAIN`, `RECONCILING`, `RECOVERY REQUIRED` | Whether one bounded local action may start or continue |
| Evidence or acceptance result | `NOT EVALUATED`, `PASSED`, `FAILED`, `ABORTED`; proof-specific `NOT READY`, `INCONCLUSIVE`, `PASS`, `FAIL` | The result derived from the accepted evidence rule |

The UI never relabels a local orchestration state as an AosCloud state or
turns one native Cloud word into a complete acceptance result. The release card
shows the concise audience interpretation; Details exposes the separate source,
observation time and fixed reason/result code.

For software lifecycle, deployment and managed runtime state, the audience-
visible authoritative source is always labelled `AosEdge Platform`. This label
is prominent on the release card or corresponding live panel and is never
replaced by `Demo UI`, `Dashboard` or `Orchestrator`. The compact source line
uses the form:

```text
Source: AosEdge Platform · observed HH:MM:SS · CURRENT
```

Technical Details identify the exact owning surface without changing the
audience-level source:

- AosCloud owns Batch, Campaign, Unit Set, desired state, Unit Online,
  delivery and native log-request state;
- AosCore state reported through AosCloud owns installed/actual software,
  readiness, managed Service instance state and observed resource usage; and
- accepted AosCore qualification evidence supports the separate resource-
  enforcement claim.

The source rule is not broadened to facts that AosEdge does not own. Motion,
Safe Stop and vehicle external connectivity remain Vehicle Gateway/CARLA facts;
Brake/Tire domain results remain matching Function-backend facts; and an in-
vehicle advisory is shown from the KUKSA/Gateway path. Every such fact retains
its own visible source and freshness.

The `AosEdge Platform` source line is required on every release card, compact
team summary, Runtime Isolation Evidence panel, Operational Logs overlay,
protected confirmation and authoritative post-action result. When a current
Platform read cannot be established, the last observation may remain visible
only as `STALE` with its timestamp and the message `Current state cannot be
confirmed`; it never remains a current success.

### <a id="ui-int-050"></a>UI-INT-050 — Failure presentation is scoped to its owner

A condition appears at the narrowest scope that it actually affects:

- an unmet candidate prerequisite or ambiguous mutation appears on that exact
  action and release;
- a Brake or Tire backend failure appears only in that team perspective and
  corresponding header summary;
- an overlapping operation blocks only its exact conflict-key scope;
- a shared AosCloud read failure may affect several cards but does not mark
  CARLA, Gateway or the vehicle external-connectivity control offline; and
- a global banner is reserved for run-exclusive provisioning, current-vehicle
  handover, identity retirement/R0, corrupt recovery state or loss of the
  shared presenter control plane.

Hidden-team failures update only their compact header summary and do not
auto-switch perspective or open an interrupting popup. Read-only navigation
continues unless the browser session itself is unavailable.

### 7.2 Visible state vocabulary and next actions

### <a id="ui-int-051"></a>UI-INT-051 — Fixed audience vocabulary

| Visible state | Factual meaning | Primary-action behavior |
| --- | --- | --- |
| `READY` | Fresh prerequisites permit a new explicitly confirmed action | Exact protected action enabled |
| `BLOCKED` | A known prerequisite is unmet; no mutation was submitted | Mutation disabled; factual reason and applicable non-mutating navigation/read available |
| `SUBMITTING` | The exact intent is journaled and the bounded request is being delegated | Duplicate action disabled |
| `WAITING` | A known operation or external condition is progressing but has not reached its exit gate | No resubmit; fresh status read remains available |
| `UNCERTAIN` | The external effect is unknown after timeout, response loss or interruption | Overlapping mutations blocked; no retry |
| `RECONCILING` | Fresh authoritative reads are classifying an uncertain or interrupted effect | Overlapping mutations blocked; no retry |
| `RECOVERY REQUIRED` | The effect is contradictory, unobservable or cannot be safely classified | Exact affected scope remains blocked; diagnosis and reviewed recovery only |
| `COMPLETED` | The accepted authoritative post-read and exit rule passed | No repeated action; next independent decision remains explicit |
| `STALE` | A previously observed value exceeds its freshness or baseline binding | It cannot satisfy a current gate |
| `OFFLINE` / `SOURCE UNAVAILABLE` | The named source or vehicle path cannot currently communicate | Only actions whose accepted preconditions remain provable are available |
| `WORKSPACE INCOMPLETE` | One or more required presentation surfaces or their accepted visibility, non-overlap or readability cannot be proved | Lifecycle meaning is unchanged; only local diagnosis and `Restore workspace layout` are offered |

`FAILED` is shown only when the authoritative source actually reports failure
or the accepted evidence rule assigns a failed result. It is not a synonym for
timeout, unknown outcome, offline state or a blocked action. Every state uses
explicit text and never relies on color alone. Browser-based Demo UI states
also use an icon. Native text-only surfaces may use restrained ANSI color but
have no bitmap-icon requirement.

### <a id="ui-int-052"></a>UI-INT-052 — One factual reason and one safe next step

A non-ready action shows directly beneath its stage:

1. a short factual headline;
2. the affected release, vehicle and operation;
3. source and freshness;
4. the exact unmet or ambiguous condition; and
5. at most one recommended safe next step.

The next step may be `Recheck current state`, `Enter Safe Stop`, `Restore
vehicle connectivity`, select the Platform perspective or follow an explicit
operator recovery instruction. A generic `Retry`, `Force`, `Ignore`, `Mark
successful`, `Rollback` or `Continue anyway` control is forbidden. The original
protected action becomes available again only after authoritative evidence
proves `NOT_APPLIED` and the presenter supplies a new confirmation.

### 7.3 Expected waiting and dependency conditions

### <a id="ui-int-053"></a>UI-INT-053 — Waiting for Safe Stop is an expected derived condition

After Platform Test or Production authorization, a moving vehicle may show:

> Authorized for this vehicle — the in-vehicle OEM runtime is waiting for Safe
> Stop before it applies the Vehicle Data Platform update.

This is neither an OEM-approval failure nor an AosCloud motion check. The stage
keeps Cloud delivery, current desired/actual/readiness and fresh Gateway facts
visible, labels the waiting phrase as a Representation Layer interpretation,
and points to the existing
Vehicle Controller `Enter Safe Stop` action. No UI `Apply update` or automatic
stop is introduced. The runtime gates both destructive replacement/removal and
activation, fails closed on stale/reset-discontinuous evidence and rechecks
fresh state after restart. Once AosCore readiness proves application while
stopped, the presenter explicitly resumes driving.

### <a id="ui-int-054"></a>UI-INT-054 — Missing Service dependency is an explicit bounded blocker

Brake and Tire cards always show required and actual VDP versions. When the
selected vehicle lacks the required capability, the card remains visible and
Details remains available, but deployment authorization/readiness is shown as:

> Platform update required — this Service requires Vehicle Data Platform
> Component vN; the selected vehicle currently provides vM.

The team selector allows the presenter to navigate to Platform Team without
changing any lifecycle state. The UI does not claim native AosCloud rejection
until D4-X01 is implemented and qualified. If a Service is nevertheless
installed without its telemetry contract, its Function surface reports
`PLATFORM UPDATE REQUIRED`/`NOT READY`, sends no fabricated healthy result and
directs the audience to the Platform Team.

### <a id="ui-int-055"></a>UI-INT-055 — Known external progress remains visible

Cloud delivery, native log collection, helper capacity and other known pending
conditions retain their native source state, observation time and affected
object fingerprint. `WAITING` never means success and never starts another
action automatically. Read-only recheck is available; an accepted subscription
may update the same card silently. A helper-capacity `BUSY` condition remains a
local request-capacity fact, creates no automatic queue and is never presented
as an AosCloud lifecycle restriction.

### 7.4 Vehicle external connectivity

### <a id="ui-int-056"></a>UI-INT-056 — Planned vehicle external-connectivity loss

The one Controller action means `the Current Vehicle loses the external
world`. It atomically removes the selected vehicle's AosCloud path and every
installed Service-to-Function-backend path while preserving CARLA, Controller,
Gateway, KUKSA and local Service execution. The non-current VM and the Demo
UI-to-AosCloud path are not faulted.

During the accepted Production demonstration:

- the shared header and Controller show `Production Vehicle — external
  connectivity off`;
- AosCloud-derived Unit/Service observations may become stale or offline and
  are labelled with their source time;
- Function backends show `No new cloud events` rather than a Service failure;
- Brake/Tire local analysis and advisories continue through KUKSA/Gateway and
  remain visible in Engineering Telematics; and
- no audience lifecycle mutation is deliberately started as part of the
  connectivity proof.

After `Restore connectivity`, the same Unit and Service instances reconnect.
Immutable buffered messages retry through the accepted owner contracts,
duplicate rows are suppressed and backend synchronization completes only at
the acknowledged watermark. The UI distinguishes local decision time, first
durable backend receipt and synchronization completion and calculates no
latency KPI.

### <a id="ui-int-057"></a>UI-INT-057 — Presenter-to-AosCloud failure is not the demo feature

If the Demo UI or native helper cannot reach AosCloud, it shows `AosCloud
source unavailable` at the affected shared-source scope and disables protected
Cloud actions whose current prerequisites cannot be proven. It does not label
the vehicle externally offline, operate the Controller connectivity switch or
claim offline-Service continuity. CARLA and locally observable vehicle behavior
may remain visible, but they cannot substitute for missing Cloud authority.

### 7.5 Uncertain operations and recovery

### <a id="ui-int-058"></a>UI-INT-058 — Reconciliation after interruption or unknown outcome

Before any protected external call, the current-operation registry contains
the exact intent and conflict keys. Response loss, process/Mac restart or an
ambiguous helper result enters `UNCERTAIN`. Restart validates the registry and
re-reads every non-terminal external operation before allowing any overlapping
mutation.

The result is shown separately as:

- `APPLIED` — the exact action may complete and its card advances;
- `NOT APPLIED` — the action may return to `READY`, but only a new explicit
  confirmation can submit it again;
- `CONTRADICTORY` — `RECOVERY REQUIRED`; or
- `UNOBSERVABLE` — `RECOVERY REQUIRED`.

Another team may continue disjoint work throughout this process. A corrupt
registry blocks all mutations and shows one global recovery banner, but keeps
read-only diagnosis available. No UI cleanup discards the journal before the
external effect is known.

### <a id="ui-int-059"></a>UI-INT-059 — Run-exclusive recovery remains global

Interrupted provisioning, identity retirement, current-vehicle handover and R0
are global because partial completion can invalidate both vehicle roles or the
single live source. The shared header shows `Current Vehicle unavailable —
reconciling` during an unresolved handover and never labels both vehicles
current. All conflicting mutations remain blocked until the accepted
authoritative proof is restored. R0 resumes from the first unproven step and
never repeats a proven destructive action or presents cleanup as OTA rollback.

### 7.6 Accepted auxiliary-surface states

### <a id="ui-int-060"></a>UI-INT-060 — Details, logs and isolation panels fail honestly

- Details retains visible `STALE`, `UNKNOWN`, `INCOMPLETE` and `REDACTED` rows;
  opening it does not refresh or repair them.
- Operational Logs shows native request state plus source/freshness. Vehicle
  external-connectivity loss may explain why no fresh result arrives, but the
  overlay does not invent a Cloud state or resubmit automatically.
- Runtime Isolation Evidence uses only `NOT READY`, `INCONCLUSIVE`, `FAIL` and
  `PASS` from its accepted proof rule. Missing/stale cgroup evidence or early
  load auto-stop is `INCONCLUSIVE`; externally offline Unit, wrong Tire version
  or stale profile is `NOT READY`; Brake/platform degradation or restart is
  `FAIL`.
- A Function-backend source failure remains local to its team. It never makes
  CARLA, Engineering Telematics, AosCloud or another team appear failed.

### 7.7 Message and layout rules

### <a id="ui-int-061"></a>UI-INT-061 — Stable, accessible and non-alarming presentation

Blocked, waiting and recovery information stays inside the corresponding card,
panel or scoped banner rather than appearing only as a transient toast. It does
not resize or scroll the fixed left workspace. Human wording leads; fixed
technical reason codes and fingerprints remain in Details. Status is never
communicated by color alone, and progress animation never implies success.

The UI avoids blame-oriented text such as `team error` where the fact is a
missing dependency, stale source or unavailable vehicle path. It names the
source and condition: for example `Brake backend source unavailable`, `VDP v3
required`, `Waiting for Safe Stop` or `Publication result uncertain`.

### 7.8 Reference examples

| Situation | Visible interpretation | Available next action |
| --- | --- | --- |
| VDP v2 authorized while vehicle moves | `Waiting for Safe Stop`; Cloud authorization remains visible | `Enter Safe Stop` in Controller |
| Tire v1 selected on VDP v2 | `Platform update required — needs VDP v3` | Select Platform Team or inspect Details; no deployment authorization |
| Brake publication response is lost | `Publication result uncertain`; same release scope blocked | `Recheck current state`; no retry |
| Production Vehicle external connectivity is off | Local Services continue; no new backend events; Cloud observations may be stale | `Restore connectivity` in Controller |
| Tire CPU proof lacks current cgroup qualification evidence | `INCONCLUSIVE`, never `PASS` | Restore required evidence and start a newly confirmed proof |
| Tire backend is unavailable | Tire perspective/source unavailable only | Recheck Tire source; Platform and Brake remain independently actionable |

### 7.9 Section 7 acceptance criteria

Verify the accepted behavior:

1. three separately labelled authoritative-source, local-orchestration and
   evidence/acceptance state layers;
2. `AosEdge Platform` as the prominent source for current software lifecycle,
   deployment and managed runtime state, with vehicle and Function facts still
   attributed to their actual owners;
3. the fixed recovery-safe state vocabulary with no generic retry, force,
   ignore or continue-anyway action;
4. `Waiting for Safe Stop before application` as an expected derived
   post-authorization Platform FOTA condition, based on native AosCore
   `ACTIVATING` plus fresh Gateway state and never presented as a Cloud state;
5. current-release Service compatibility presentation with OEM evidence
   gating, process-healthy/functional-`NOT_READY` runtime defense and no
   simulated native Cloud rejection;
6. one Current Vehicle external-connectivity fault that preserves Demo UI-to-
   AosCloud access and all accepted local in-vehicle behavior;
7. resource-scoped uncertainty/reconciliation, with global mutation blocking
   only for run-exclusive environment/lifecycle work and corrupt recovery
   state; and
8. the exact Operational Logs and Runtime Isolation state/verdict boundaries
   defined in this section.

This acceptance authorizes no UI implementation, retry, recovery mutation,
connectivity fault, CPU proof, log request or Cloud action. Section 8 may define
how already accepted live evidence is correlated across visible surfaces, but
it may not change these state, authority or recovery semantics without
reopening Section 7.

## 8. Vehicle and Function-Backend Correlation


### 8.1 One audience evidence context

### <a id="ui-int-062"></a>UI-INT-062 — One Current Vehicle, release and live exercise

Every live Test-validation or Production-operation view binds one audience
evidence context:

- `Test Vehicle` or `Production Vehicle`;
- selected Platform, Brake or Tire release and exact version;
- current installed VDP/Service graph as reported by AosEdge Platform;
- current CARLA drive mode and live exercise/generation; and
- current vehicle external-connectivity state.

The audience header uses human labels. Technical Details add only sanitized
vehicle, artifact, Service-instance, source-generation and event fingerprints.
There is no audience-visible demo-run ID and no inference across two vehicles,
two CARLA actors or an unproven source generation.

The evidence context remains stable while the presenter changes team
perspective. A perspective change selects a different product interpretation
of the same Current Vehicle; it does not restart CARLA, select another Unit or
reuse another team's backend result.

### <a id="ui-int-063"></a>UI-INT-063 — Sequential live exercises, not replay

The installed Test uses one live CARLA/Gateway source and fresh live exercises.
In the expanded profile, Test and Production evidence comes from separate
fresh live exercises after the explicit
Current Vehicle handover. It does not record one drive and replay its telemetry
into another Unit.

Test acceptance uses the exact previously qualified deterministic Brake or Tire
stimulus. Production operation normally uses Autopilot, or Manual when the
presenter chooses it, to show the released software processing continuous live
vehicle telemetry during ordinary driving, turning, braking and stopping. The
presenter may explicitly run the accepted deterministic stimulus on Production
when a guaranteed audience event is needed, but that run demonstrates released
behavior and does not revalidate or reaccept the release.

Autopilot continuously produces the accepted motion, pedal, steering, wheel and
slip signal families. A naturally occurring Autopilot or Manual episode becomes
valid Function evidence only when it satisfies that Service version's exact
event contract. Free driving alone does not guarantee a qualifying Brake event
and does not replace the accepted `PRE_AGED` Tire stimulus. Until an event is
actually detected, the UI reports live telemetry plus factual `Waiting for
event`; it never implies a result merely because the vehicle drove or stopped.

Every `Start/restart scripted scenario` creates a new bounded source exercise
and generation while preserving Current Vehicle and software lifecycle state.
The presenter may repeat it any number of times within the demo run. Manual and
Autopilot may also produce observable live events, but only the accepted
deterministic exercise and exact validation entry/exit contract can satisfy
Test acceptance.
Starting a new drive clears only transient current-exercise presentation; it
does not remove previously accepted Test evidence or advance a release stage.

### 8.2 Human-readable causal chain

### <a id="ui-int-064"></a>UI-INT-064 — Four visible links explain one event

During Test validation or Production live operation, the selected release
stage exposes one compact `Live Vehicle and Function Evidence` panel in the
right workspace. It remains visible together with the fixed left surfaces and
uses this human-first chain:

```text
Vehicle event
  -> vehicle signals available
  -> on-vehicle Service behavior
  -> driver indication and/or Function backend result
```

The actual evidence is split without duplicating authority:

| Visible link | Surface | Authoritative source |
| --- | --- | --- |
| Vehicle is driving, braking or under the accepted Tire stimulus | CARLA and Vehicle Controller | CARLA/Controller |
| Required signals and applied advisory status | Engineering Telematics | Gateway/KUKSA path |
| Installed graph, Service state and readiness | Release/evidence panel | AosEdge Platform |
| Brake/Tire assessment, event or delayed receipt | Selected Function result panel | Matching Function backend |

The right panel does not replace CARLA or Engineering Telematics and does not
embed a second simulator. It summarizes the currently selected team's live
result. Platform uses a `Vehicle capability evidence` variant with no invented
Function backend. Brake and Tire use their own isolated Function result views.

### <a id="ui-int-065"></a>UI-INT-065 — Release-specific evidence story

| Release | Vehicle/Engineering evidence | Right-side result evidence |
| --- | --- | --- |
| VDP v1 | Base-dynamics/braking signals become available through KUKSA | Exact v1 contract availability/readiness; no Function result |
| Brake v1 | Deterministic brake episode and its pre/active/post signals | One bounded braking-window receipt in Brake backend |
| VDP v2 | Backward-compatible wheel speed/angular-speed additions | Exact additive v2 capability/readiness; no Function result |
| Brake v2 | Same braking episode while local Service analysis runs | Bounded derived assessment/event rather than normal v1 high-detail stream |
| VDP v3 | Tire slip inputs and controlled advisory paths become available | Exact additive v3 capability/readiness; no Function result |
| Brake v3 | Brake episode plus applied Brake advisory in Engineering Telematics | Derived Brake state/advisory fact in Brake backend |
| Tire v1 | Accepted accelerated/pre-aged Tire stimulus plus applied Tire advisory | Tire condition assessment/event in independent Tire backend |

The panels explain platform-enabled product evolution; they do not claim that
the synthetic Brake/Tire algorithms are production predictive-maintenance
models or that the CARLA stimulus proves real-hardware performance.

For Test, the Brake and Tire rows use their accepted deterministic stimuli. For
Production, the same evidence chain may be populated by a naturally occurring
Autopilot/Manual event or by an explicitly selected deterministic stimulus; the
UI labels which source produced the current event and never treats normal free
driving as a guaranteed Function result.

### 8.3 Correlation and time semantics

### <a id="ui-int-066"></a>UI-INT-066 — Same-event fingerprints without private identifiers

The Representation Layer verifies exact internal Unit/Node/`system_uid`,
software digest, VDP contract, source generation and domain-message binding
before projection. The browser receives only:

- Current Vehicle alias and sanitized vehicle fingerprint;
- product version and release digest fingerprint;
- live exercise/generation and vehicle-event fingerprint;
- Service assessment/event/advisory fingerprint where applicable; and
- source-owned observation times and freshness.

The same short fingerprints appear on the relevant Engineering, release and
Function evidence so technical viewers can confirm that the panels describe
one causal chain. Full private Cloud/vehicle identities and unrestricted raw
telemetry remain outside browser state. Function wire messages retain their
accepted exact internal correlation contract; the audience projection does
not add Cloud Unit/Node IDs to them.

### <a id="ui-int-067"></a>UI-INT-067 — Causality is not a latency benchmark

Where applicable, the UI labels these times separately:

1. vehicle/source event time;
2. local Service decision time;
3. Gateway advisory observation/application time;
4. Function backend first durable receipt time; and
5. backend synchronization-complete time after reconnect.

Domain identifiers, producer epoch/sequence, source generation and state
transitions establish causal order. The UI does not subtract wall clocks from
different owners, report end-to-end latency, imply synchronized automotive
clocks or turn Cloud wait time into a vehicle KPI. An invalid or owner-
impossible timestamp is rejected; a cross-clock anomaly is labelled and cannot
reorder current state.

### <a id="ui-int-068"></a>UI-INT-068 — Duplicate, ordering and restart behavior

An identical Function-message retry reuses its accepted identity and produces
no second audience row. A conflicting duplicate is visibly quarantined and
cannot replace current state. Sequence/epoch, not receipt order, controls state
progression. An ordinary process, container or VM restart preserves the
producer epoch and continues from the persisted next sequence without reuse.
Only an explicit producer replacement or new producer lifecycle rotates the
epoch once and starts sequence `1`; R0 destroys producer state. Delayed
evidence from an old epoch may remain visible for diagnosis but cannot roll
back the current assessment or advisory.

The audience view de-duplicates normal retry traffic while retaining a bounded
ignored-duplicate/conflict indicator in Technical Details. It does not hide a
correlation conflict as a successful current event.

### 8.4 Connectivity and vehicle handover

### <a id="ui-int-069"></a>UI-INT-069 — Offline view proves local behavior and delayed delivery

During selected-Test external-connectivity loss (or the expanded Production
Vehicle exercise), the native
surfaces continue to show the live CARLA stimulus, local signals and local
advisory. The selected Function backend panel shows `No new cloud events` and
its last durable receipt time. It does not pretend to observe the Service's
current local decision through the disconnected backend path.

The Demo UI also cannot observe current Service queue occupancy, current
Service storage use or an overflow fact while the vehicle is externally
offline. It shows `Local delivery queue — not observable while vehicle is
offline`. Technical Details may show the configured bounded queue and
AosCore-enforced storage quota from accepted release metadata, plus the last
observed state and its timestamp, but never relabel those facts as current
usage. No special out-of-band monitoring path is introduced to bypass the
vehicle connectivity fault.

After reconnection, immutable queued Function messages arrive without duplicate
rows. The panel distinguishes delayed first durable receipt from acknowledged
synchronization completion and shows the exact accepted watermark fingerprint.
Only after the matching Service/backend synchronization summary or overflow
fact is durably received may the UI show delivered, still-pending or dropped
message counts. Absence of that summary remains `UNKNOWN`; it is not interpreted
as zero loss. This demonstrates local continuity plus delayed Cloud delivery;
it does not claim continuous backend operation or externally observed queue
state while the vehicle was offline.

### <a id="ui-int-070"></a>UI-INT-070 — Handover never mixes Test and Production live evidence

Before a Current Vehicle handover, the old source is detached and its current
live-exercise panel stops updating. After canonical reset/new generation and
exclusive binding, the live panel changes to the new vehicle alias/fingerprint
only when the handover is proven. During transition it shows `Current Vehicle
unavailable — reconciling`.

Accepted Test evidence remains a sealed release-decision reference for the
Production authorization stage, but it is visually labelled `Accepted Test
evidence`; it is never presented as a current Production event. Production
live evidence starts from a fresh exercise/generation and confirms released
operation rather than repeating product validation.

The same rule applies in reverse when a later Platform, Brake or Tire release
needs another Test cycle. While Production is current, candidate preparation,
signing, publication and disjoint Cloud work may continue. The owning release
card presents `Continue testing on Test Vehicle` before its next live Test
deployment/validation step. The accepted handover safe-stops and detaches the
Production source, performs a canonical reset/new generation with no Unit
attached, binds the Test Unit exclusively and waits for its first fresh frame
before changing the header.

This `Production -> Test` transition changes only Current Vehicle/live-source
assignment. It does not publish, deploy, roll back, remove or reset either
Unit's installed software graph. The Production Unit retains its released
versions while Test is current, and the Test Unit retains its previously
accepted graph for the next incremental release. After new Test evidence and
owning-team acceptance, the same proven handover returns to Production for a
separate Release Authority rollout and fresh Production live operation. Full
software/identity reset occurs only in R0 at the end of the demo run.

### 8.5 Presenter behavior and source failures

### <a id="ui-int-071"></a>UI-INT-071 — Live evidence never advances lifecycle by itself

`Run Test validation` binds the accepted deterministic exercise and evaluates
its evidence, but a passing live chain does not accept the release. The owning
team still selects `Accept validation result`. `Show released behavior` starts
or observes a Production live exercise but creates no Production acceptance
result. Repeated Scenario, Manual or Autopilot driving changes neither current
software lifecycle state nor another team's release state.

Switching team perspective changes only the right-side product/function
interpretation. CARLA, Controller, Engineering Telematics and Current Vehicle
remain continuous. A Platform view shows capability evidence; a Brake/Tire
view shows only its matching backend. No cross-team backend data is merged.

### <a id="ui-int-072"></a>UI-INT-072 — Missing one link yields incomplete correlation

No surface may infer another surface's fact. For example, a CARLA braking event
does not prove Service execution, KUKSA write success does not prove Gateway
application, and a backend receipt does not prove current vehicle readiness.
If any mandatory link is missing, stale, wrong-vehicle, wrong-version,
out-of-generation or contradictory, the live chain is `INCOMPLETE` or
`UNKNOWN`, never green.

Section 7 source-local failure behavior applies: one Function backend failure
does not mark AosEdge Platform, CARLA, Engineering Telematics or another team
failed. `Recheck current state` refreshes accepted owners but never reruns the
vehicle exercise or resubmits a Function message.

### 8.6 Correlation acceptance criteria

Verify one current vehicle/release/exercise context, a readable four-link causal
chain and release-specific Platform/Brake/Tire evidence. Keep sanitized event
fingerprints and source timestamps separate from receipt time; introduce no
latency KPI or fake run identity. Offline displays distinguish local results,
absent backend delivery and delayed synchronization. In the expanded profile,
Test/Production handover never mixes live evidence; deterministic exercises
remain repeatable without replay, with Manual/Autopilot normal driving separate.

## 9. Traceability and UI Acceptance Cases


### 9.1 Stable traceability model

### <a id="ui-trc-001"></a>UI-TRC-001 — Every interaction rule is covered without copied requirements

The [UI Traceability Register](aosedge-demo-ui-traceability-register.md)
contains one traceability row for every stable `UI-INT-*` rule in this
specification:

| Field | Meaning |
| --- | --- |
| UI rule | Exact stable `UI-INT-*` anchor |
| Upstream source | Linked architecture decision, system/component requirement or accepted D4 contract that owns the behavior |
| Surface | Audience-visible surface or shared workspace region under test |
| Acceptance cases | One or more stable `UI-AT-*` cases that verify the observable behavior |
| Status | `DESIGNED`, `IMPLEMENTED` or `QUALIFIED` without inferring a later state |

The register supports both directions: every `UI-INT-*` rule has at least one
case, and every `UI-AT-*` case links at least one interaction rule and its
actual upstream owner. It links rather than copying parent requirement prose.
Automated documentation checks reject missing anchors, orphan rules, orphan
cases, duplicate stable IDs and invalid local links.

An acceptance case verifies only observable interaction behavior and source
attribution. It never becomes a second definition of Cloud lifecycle, vehicle
physics, Service logic, security policy or evidence semantics. Each case uses
the human-readable structure `Precondition -> source event or presenter action
-> expected visible result -> forbidden visible result -> authoritative
evidence`.

For example, the reverse-vehicle case links `UI-INT-016`, D4-005 and
`REQ-DEMO-010`. It proves `Changing vehicle...`, a header change only after the
new exclusive binding, a new source generation in Details and unchanged Unit
software graphs. It forbids two Current Vehicles, cross-role telemetry,
presentation of handover as deployment and automatic continuation after an
uncertain detach/reset.

### 9.2 Acceptance-case format

### <a id="ui-trc-002"></a>UI-TRC-002 — One readable case format at three verification levels

Every stable `UI-AT-*` case uses one primary presenter action or source event
and the following fields:

1. stable case ID and human-readable title;
2. covered `UI-INT-*` rules and linked upstream owners;
3. affected surfaces;
4. mandatory verification levels and priority;
5. preconditions expressed as source facts rather than a click path;
6. one trigger;
7. expected visible results;
8. explicitly forbidden visible results;
9. authoritative evidence; and
10. postcondition/cleanup where the case mutates state.

The three verification levels are:

| Level | Boundary |
| --- | --- |
| `FIXTURE` | Automated browser/component behavior against deterministic accepted adapter states with no external mutation |
| `INTEGRATED` | Behavior against real accepted adapters and authoritative sources in the disposable demo environment |
| `HUMAN` | Visual and presenter-operability acceptance on the qualified Mac and measured full-screen viewport |

A machine/source failure cannot be overridden by a human decision. A human
reviewer may reject presentation quality even when automated checks pass. A
case is `PASSED` only when every mandatory level passes. Execution verdicts
reuse D4-025 `PASSED`, `FAILED`, `BLOCKED`, `ABORTED` and `NOT_EVALUATED`.

Screenshots may support human review but are not authoritative lifecycle or
functional proof. Cases link Service, Cloud, CARLA and security contracts
rather than redefining them. Cleanup is mandatory only when the case changes
state, and `Details` assertions remain bound to the same release/stage context.

### 9.3 Global workspace and navigation cases

The following cases apply to the named installed or expanded profile:

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-001"></a>`UI-AT-001` — Qualified full-screen composition | `UI-INT-001` | `FIXTURE`, `HUMAN` | One measured presenter display, approximately equal regions, readable real surfaces and no tab/Space/horizontal-scroll dependency |
| <a id="ui-at-002"></a>`UI-AT-002` — Stable native evidence and selected context | `UI-INT-003`, `UI-INT-004` | `FIXTURE`, `HUMAN` | At the qualified presenter viewport, visible CARLA, combined native Driving Control/Telemetry and Presenter remain readable; integrated cards/dialogs preserve selected team, component, focus and relevant scroll without a mandatory text-only Terminal or five-stage layout |
| <a id="ui-at-003"></a>`UI-AT-003` — Shared header and audience terminology | `UI-INT-002`, `UI-INT-006` | `FIXTURE`, `HUMAN` | Exact title, one Current Vehicle and three producer selectors with `Test Vehicle` normalization and no technical/global-step clutter |
| <a id="ui-at-004"></a>`UI-AT-004` — Independent team-perspective navigation | `UI-INT-007`, `UI-INT-009`–`UI-INT-012` | `FIXTURE`, `INTEGRATED` | Navigation restores each team's independent release/version scroll and focus with fresh fixed-context state and causes no external, vehicle or lifecycle action |
| <a id="ui-at-005"></a>`UI-AT-005` — Release Authority remains separate | `UI-INT-008` | `FIXTURE`, `HUMAN` | Compact fixed neutral non-selectable governance line outside all producer teams, no redundant decorative authority badge, and explicit actor identity on its stages |
| <a id="ui-at-006"></a>`UI-AT-006` — Mutation serialization and expanded scoped conflicts | `UI-INT-013`, `UI-INT-014` | `FIXTURE`, `INTEGRATED` | Installed protected mutations are serialized without blocking read-only diagnosis/navigation; expanded disjoint-operation qualification additionally proves exact conflict scopes and owner-local failures |
| <a id="ui-at-007"></a>`UI-AT-007` — Details overlay preserves context | `UI-INT-005` | `FIXTURE`, `HUMAN` | Right-side read-only modal preserves vehicle/team/release/scroll/focus and fixed evidence, then closes without an external side effect |

The mandatory negatives cover horizontal page scroll, a scrolling or clipped
team-context region at the qualified viewport, hidden version tabs, generic
`Next`, restored scroll from the wrong team, decorative labels that displace
the accepted context, two Current Vehicles, internal Validation-role labels, a
fourth team, navigation-triggered mutations, interrupting hidden-team success
popups, over-broad operation locking, cross-owner failure colouring and any
Details action that changes lifecycle state.

### 9.4 Current Vehicle and release-lifecycle cases

The following mandatory cases cover the shared lifecycle once and use stable
parameterized instances where releases or actions repeat the same contract:

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-008"></a>`UI-AT-008` — Global Current Vehicle | `UI-INT-015` | `FIXTURE`, `INTEGRATED` | One Current Vehicle shared across perspectives while both Cloud Units may remain Online |
| <a id="ui-at-009"></a>`UI-AT-009` — Test-to-Production handover | `UI-INT-016`, `UI-INT-017`, `UI-INT-070` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Honest changing state followed by Production only after exclusive detach/reset/attach and first fresh evidence |
| <a id="ui-at-010"></a>`UI-AT-010` — Production-to-Test handover | `UI-INT-016`, `UI-INT-017`, `UI-INT-070` | `FIXTURE`, `INTEGRATED`, `HUMAN` | The next release returns to Test through the same proven protocol without changing either Unit's software graph |
| <a id="ui-at-011"></a>`UI-AT-011` — Failed or uncertain handover | `UI-INT-017`, `UI-INT-070` | `FIXTURE`, `INTEGRATED` | No new Current Vehicle, cross-role evidence or automatic lifecycle continuation after uncertain detach/reset/attach |
| <a id="ui-at-012"></a>`UI-AT-012` — Platform FOTA and Safe Stop | `UI-INT-018`, `UI-INT-020` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Authorization may precede stop, AosCore owns apply enforcement, readiness precedes explicit resumed driving |
| <a id="ui-at-013"></a>`UI-AT-013` — Service SOTA while driving | `UI-INT-019` | `FIXTURE`, `INTEGRATED` | QM Service update is not motion-gated, vehicle evidence remains continuous and no motion authority is gained |
| <a id="ui-at-014"></a>`UI-AT-014` — Common release evidence and authority | `UI-INT-021`–`023` | `FIXTURE`, `HUMAN` | Prepared identity, authorized Test assignment, actual installation/readiness and owner evidence remain distinct; expanded Test acceptance, Production authorization and Production live operation add their own separate decisions, not a required five-card layout |
| <a id="ui-at-015"></a>`UI-AT-015` — VDP v1-v3 story | `UI-INT-024` | `FIXTURE`, `INTEGRATED` | Parameterized `VDP-v1`, `VDP-v2`, `VDP-v3` instances prove additive capability and Platform ownership |
| <a id="ui-at-016"></a>`UI-AT-016` — Brake v1-v3 story | `UI-INT-025` | `FIXTURE`, `INTEGRATED` | Parameterized `Brake-v1`, `Brake-v2`, `Brake-v3` instances prove one independent Service's product evolution |
| <a id="ui-at-017"></a>`UI-AT-017` — Tire v1 story | `UI-INT-026` | `FIXTURE`, `INTEGRATED` | One independent `Tire-v1` release shows the second tenant and distinct lifecycle/result |
| <a id="ui-at-018"></a>`UI-AT-018` — Dependencies and independent evolution | `UI-INT-027` | `FIXTURE`, `INTEGRATED` | Visible versions, factual current-release compatibility/readiness and automatic re-evaluation without simulated native admission |
| <a id="ui-at-019"></a>`UI-AT-019` — Protected action and credential boundary | `UI-INT-028`–`UI-INT-031`, `UI-INT-036` | `FIXTURE`, `INTEGRATED` | Per-action instances prove organizational actor, credential profile, fresh confirmation and browser/helper separation |
| <a id="ui-at-020"></a>`UI-AT-020` — Authoritative result, concurrency and reconciliation | `UI-INT-032`–`UI-INT-035` | `FIXTURE`, `INTEGRATED` | Authoritative post-read, scoped conflicts, honest uncertainty, no blind retry and no hidden cross-team chaining |

`UI-AT-014` is instantiated for all seven release instances without copying
the common contract. `UI-AT-015` through `017` retain individual version keys
and verdicts. `UI-AT-019` is instantiated for each accepted action-matrix row
that crosses a protected boundary. One instance still contains one primary
action and one independently evaluated verdict.

Mandatory negatives include perspective-driven vehicle changes, handover as
deployment, software-graph reset during handover, two current vehicles,
Production product validation, motion-gated QM SOTA, UI-owned Safe Stop
enforcement, hidden/disabled versions, local simulated Cloud admission,
credential delivery to the browser, HTTP-success-as-completion, broad
cross-team locking, hidden chaining and blind retry after uncertainty.

### 9.5 Details, disclosure, logs and isolation cases

The following seven mandatory cases cover the secondary explanation and
diagnostic surfaces without turning them into alternate lifecycle paths:

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-021"></a>`UI-AT-021` — Details content and stage binding | `UI-INT-037`–`UI-INT-040` | `FIXTURE`, `HUMAN` | Human-first, stage-specific read-only content with internal scrolling and unchanged release context |
| <a id="ui-at-022"></a>`UI-AT-022` — Source, freshness and integrity | `UI-INT-041`, `UI-INT-042` | `FIXTURE`, `INTEGRATED` | Explicit source/freshness states, separately labelled digest chain and fingerprint-only private identities |
| <a id="ui-at-023"></a>`UI-AT-023` — Access, dependency and quota presentation | `UI-INT-043` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Intent-first access, exact technical paths, Service-only approved quotas and factual compatibility without simulated admission |
| <a id="ui-at-024"></a>`UI-AT-024` — Disclosure, redaction and copy boundary | `UI-INT-045`, `UI-INT-047` | `FIXTURE`, `INTEGRATED` | Pre-browser allowlisting/redaction and copy of only reviewed non-secret identifiers/digests/fingerprints |
| <a id="ui-at-025"></a>`UI-AT-025` — Perspective and evidence isolation | `UI-INT-046` | `FIXTURE`, `INTEGRATED` | Platform, Brake and Tire projections remain disjoint; Release Authority receives only its bounded decision summary |
| <a id="ui-at-026"></a>`UI-AT-026` — Runtime Isolation Evidence | `UI-INT-044` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Separate sticky Tire-proof panel combines platform enforcement evidence, same-instance continuity, Brake control and recovery |
| <a id="ui-at-027"></a>`UI-AT-027` — Platform/Operational Logs workflow | `UI-INT-048` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Parameterized Platform/Brake/Tire fixed-scope request, status re-read, bounded sanitized result and exact deletion |

Mandatory negatives cover modal lifecycle actions, opening-as-refresh, cached
green state, collapsed unverified digests, browser-held private identities or
credentials, raw response/log/telemetry disclosure, unrestricted copy/export,
Service-quota presentation on VDP, Service-reported quota enforcement,
cross-team evidence, arbitrary log selectors, ELK/second archive and log-request
resubmission by a read-only status action. Failure and offline states for the
same surfaces are allocated in the next group rather than duplicated here.

### 9.6 Failure, offline and recovery cases

The following nine cases are mandatory. Existing `UI-AT-012` additionally
covers `UI-INT-053` expected Safe Stop waiting, and `UI-AT-018` additionally
covers `UI-INT-054` bounded Service dependency blocking.

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-028"></a>`UI-AT-028` — Separate state layers and source attribution | `UI-INT-049` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Keep authoritative source, local orchestration and evidence verdict separate; label each actual owner |
| <a id="ui-at-029"></a>`UI-AT-029` — Scoped vocabulary and safe next action | `UI-INT-050`–`UI-INT-052` | `FIXTURE`, `HUMAN` | Parameterized state instances remain narrowly scoped with one factual reason and at most one safe next step |
| <a id="ui-at-030"></a>`UI-AT-030` — Known progress without resubmission | `UI-INT-055` | `FIXTURE`, `INTEGRATED` | Waiting/subscription/helper-capacity facts remain honest and never trigger a mutation or next action |
| <a id="ui-at-031"></a>`UI-AT-031` — Vehicle offline and reconnect | `UI-INT-056`, `UI-INT-069` | `FIXTURE`, `INTEGRATED`, `HUMAN` | One external fault preserves local operation, stops backend events, exposes no live queue count and converges after acknowledged reconnect |
| <a id="ui-at-032"></a>`UI-AT-032` — Presenter-to-AosCloud failure | `UI-INT-057` | `FIXTURE`, `INTEGRATED` | A control-plane source outage blocks affected Cloud work without pretending that the vehicle is externally offline |
| <a id="ui-at-033"></a>`UI-AT-033` — Uncertain-operation reconciliation | `UI-INT-058` | `FIXTURE`, `INTEGRATED` | Lost outcome becomes uncertain and resolves only through authoritative `APPLIED`/`NOT APPLIED`/contradictory/unobservable classification |
| <a id="ui-at-034"></a>`UI-AT-034` — Run-exclusive recovery | `UI-INT-059` | `FIXTURE`, `INTEGRATED` | Provisioning, handover, retirement and R0 recovery remain global and resume from the first unproven step without repeating proven destruction |
| <a id="ui-at-035"></a>`UI-AT-035` — Auxiliary-surface failure states | `UI-INT-060` | `FIXTURE`, `INTEGRATED` | Details, Logs and Isolation panels retain their accepted source-local states and never infer success from missing evidence |
| <a id="ui-at-036"></a>`UI-AT-036` — Stable accessible failure presentation | `UI-INT-061` | `FIXTURE`, `HUMAN` | Persistent scoped wording, text/icon/color semantics and no fixed-workspace movement or blame-oriented message |

`UI-AT-029` has one case instance per fixed visible state and affected owner.
`UI-AT-031` requires `Connected -> external connectivity off -> local
continuity/no backend event -> restore -> synchronizing -> acknowledged
synchronized`, while current Service queue occupancy remains `not observable`
until a post-reconnect owner summary arrives. Configured bounds and
last-observed timestamps may remain visible but no out-of-band monitoring path
or zero-loss inference is allowed.

Mandatory negatives cover flattened Cloud/orchestration/verdict state,
cross-owner failure spread, generic retry/force/ignore/continue controls,
waiting-as-success, helper busy as Cloud restriction, vehicle/control-plane
outage confusion, current offline queue counts, blind retry, repeated proven
destructive steps, missing-evidence isolation `PASS`, transient-toast-only
failure and color-only status.

### 9.7 Live evidence and Function-backend correlation cases

The final seven mandatory cases cover the live causal chain. `UI-AT-031`
already covers `UI-INT-069` offline queue/synchronization presentation, while
`UI-AT-009` through `011` share `UI-INT-070` handover mechanics with the
evidence-separation case below.

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-037"></a>`UI-AT-037` — One evidence context and four-link chain | `UI-INT-062`, `UI-INT-064` | `FIXTURE`, `INTEGRATED`, `HUMAN` | One Current Vehicle/release/exercise context links event, signals, on-vehicle behavior and matching driver/backend result without merging owners |
| <a id="ui-at-038"></a>`UI-AT-038` — Test/Production exercise modes and no replay | `UI-INT-063`, `UI-INT-071` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Parameterized deterministic Test, normal Production Autopilot/Manual and optional guaranteed Production stimulus never replay or advance lifecycle automatically |
| <a id="ui-at-039"></a>`UI-AT-039` — Release-specific live evidence | `UI-INT-065` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Seven VDP/Brake/Tire instances show the exact accepted capability, window, derived result or advisory story |
| <a id="ui-at-040"></a>`UI-AT-040` — Fingerprints and source-owned time | `UI-INT-066`, `UI-INT-067` | `FIXTURE`, `INTEGRATED` | Sanitized same-event binding and separate owner times without private IDs, demo-run ID or cross-clock latency KPI |
| <a id="ui-at-041"></a>`UI-AT-041` — Duplicate, ordering and Service restart | `UI-INT-068` | `FIXTURE`, `INTEGRATED` | Idempotent retry suppression, digest-conflict quarantine and sequence/epoch ordering prevent duplicate rows or current-state rollback |
| <a id="ui-at-042"></a>`UI-AT-042` — Test reference versus current Production evidence | `UI-INT-070` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Accepted Test evidence remains sealed while every Production or later Test live panel starts from a fresh exclusive generation |
| <a id="ui-at-043"></a>`UI-AT-043` — Incomplete or contradictory evidence chain | `UI-INT-072` | `FIXTURE`, `INTEGRATED` | Any missing, stale, wrong-vehicle/version/generation or contradictory mandatory link remains incomplete/unknown and source-scoped |

`UI-AT-038` has distinct instances for deterministic Brake Test, deterministic
`PRE_AGED` Tire Test, Production Autopilot, Production Manual and explicit
deterministic Production exercise. Free driving remains `Waiting for event`
until the exact Function contract is met. `UI-AT-039` has `VDP-v1`,
`Brake-v1`, `VDP-v2`, `Brake-v2`, `VDP-v3`, `Brake-v3` and `Tire-v1`
instances; VDP instances have no invented Function backend.

Mandatory negatives cover cross-vehicle/release/generation evidence,
Test-telemetry replay, natural-driving-as-guaranteed-event, Production
revalidation, a demo-run ID, private identifiers, cross-clock latency claims,
receipt-order state rollback, duplicate audience rows, stale Test evidence as
current Production behavior, backend receipt as proof of vehicle readiness and
green correlation with any missing mandatory link.

### 9.8 Global preparation and reset cases

The following four mandatory positive cases close the boundary between local
environment startup, manufacturing, provisioning and run retirement:

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-044"></a>`UI-AT-044` — Lifecycle-aware environment preflight | `UI-INT-073` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Environment preflight restores only required owned surfaces and the same current Test when present; it does not create/provision a controller, advance a stage, initialize a run journal from layout or require nonexistent Units. Expanded use checks both owned roles |
| <a id="ui-at-045"></a>`UI-AT-045` — M0 manufacturing output | `UI-INT-002`, `UI-INT-074` | `FIXTURE`, `INTEGRATED`, `HUMAN` | An explicit Create Controller/M0 verifies the selected immutable Factory and one fresh unprovisioned Test overlay; expanded use adds an independent Production overlay. Each is manufactured and awaiting provisioning, with no assigned source or auto-M1 |
| <a id="ui-at-046"></a>`UI-AT-046` — M1 provisioning establishes G0 | `UI-INT-002`, `UI-INT-075` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Separate Provision reconciles exact Unit/Node/system UID, configured membership and fresh Online/source evidence, with VDP/Services absent; expanded use additionally verifies both disjoint role Sets |
| <a id="ui-at-047"></a>`UI-AT-047` — R0 terminal reset and recovery | `UI-INT-035`, `UI-INT-059`, `UI-INT-076` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Completed, failed and aborted run instances may reset; success ends at `READY_FOR_M0` with no Current Vehicle and no automatic M0/M1, while any unproven cleanup remains `Reset incomplete · Recovery required` |

Mandatory negatives cover requiring nonexistent Units at `READY_FOR_M0`,
restoring a different overlay, creating or provisioning from the environment
preflight, collapsing M0 and M1 into one result, showing Cloud identity during
M0, crossed/stale Unit Set membership, entering G0 without a fresh Test source,
requiring qualification before cleanup and automatically creating or
provisioning the next vehicle pair after R0.

### 9.9 Independent-release milestone case

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-048"></a>`UI-AT-048` — Independent VDP/Brake releases and derived milestones | `UI-INT-027`, `UI-INT-035`, `UI-INT-077` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Parameterized G3 and G4 instances keep two exact approvals/Campaigns/results, apply VDP provider-first, preserve the previous compatible Service, and complete only a read-only `0/2`, `1/2`, `2/2` capability summary |

Mandatory negatives cover a combined Cloud object, `Approve G3/G4`, one team
accepting the other team's artifact, hidden automatic Service rollout after
VDP readiness, Service-first Production application, rollback of a healthy VDP
after dependent-Service failure and writing the derived milestone back as
authoritative Cloud lifecycle state.

### 9.10 Composed-workspace ownership case

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-049"></a>`UI-AT-049` — Composed workspace ownership and local restoration | `UI-INT-001`–`UI-INT-006`, `UI-INT-051`, `UI-INT-078` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Presenter Launcher owns measured physical header/native/browser composition and recovery, the stateless Representation Layer owns shared-header meaning/navigation from the same browser read model, surface owners retain content, and local restoration changes no lifecycle state |

Mandatory positive instances cover clean startup, restart of each required
surface, a presenter-Mac application restart and one explicit local layout
restore. Mandatory negatives cover browser ownership of native geometry,
launcher ownership of surface content or Cloud truth, a second header state
store/read path, duplicated/missing/off-screen/overlapped/unreadable surfaces
reported as ready, layout recovery that mutates vehicle or release lifecycle,
and CARLA/Controller embedding, streaming or screen capture into the browser.
The integrated mechanism and its window selectors are qualified on the actual
presenter Mac; fixture success alone proves no portability to another host.

### 9.11 Global lifecycle workspace case

| Case | Main coverage | Required levels | Accepted purpose |
| --- | --- | --- | --- |
| <a id="ui-at-050"></a>`UI-AT-050` — Global Demo Lifecycle page and Qualification Status | `UI-INT-002`, `UI-INT-004`, `UI-INT-006`, `UI-INT-073`–`UI-INT-076`, `UI-INT-079` | `FIXTURE`, `INTEGRATED`, `HUMAN` | Selecting the shared title changes only the right region, keeps all fixed evidence surfaces visible, presents Qualification/Prepare/current lifecycle/R0/recovery from their accepted sources, preserves independent team state and does not duplicate native launcher actions |

Mandatory positives cover all five qualification states, M0/M1/G0, active and
recovery lifecycle states, R0 success/incomplete recovery, title-to-global and
global-to-team navigation with preserved team scroll/focus. Mandatory
negatives cover a fourth producer identity, full-screen replacement, hidden
left surfaces, browser duplication of launcher preflight/layout restoration,
manual qualification override and qualification treated as Cloud or release
authority.

### 9.12 Section 9 acceptance criteria

Verify the accepted behavior:

1. one bidirectional traceability row for every `UI-INT-001` through
   `UI-INT-079`, linked to actual upstream ownership and one or more cases;
2. a readable one-trigger case format with `FIXTURE`, `INTEGRATED` and `HUMAN`
   verification levels and D4-025-compatible verdicts;
3. 50 stable mandatory cases, using parameterized instances instead of copied
   release, action or visible-state prose;
4. machine/source failure as non-overridable and human presentation review as
   an additional required veto/pass gate where allocated;
5. screenshots as supporting presentation evidence only, never authoritative
   lifecycle or functional proof; and
6. automated rejection of missing/duplicate/orphan IDs, invalid local links or
   uncovered interaction rules.

The case definitions retain stable IDs and upstream authority. Current Test
scope and native rendering follow UI-STUDIO-026 above; expanded promotion and
resource proofs retain their separate acceptance boundary. Current implementation
and executed cases are recorded by the baseline, not a retired clickable mockup.
This specification itself authorizes no Cloud/helper mutation or vehicle action.
