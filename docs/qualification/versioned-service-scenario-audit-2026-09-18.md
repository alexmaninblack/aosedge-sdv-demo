<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Versioned Brake/Tire scenario and Presenter audit

Date: 18 September 2026. Status: analysis with all six decisions 1A through 6A
accepted, including Return to road, the Aos Cloud summary-card revision,
color association and the AosCore/AosEdge platform presentation. The source-first
timing recommendation remains proposed. The operator subsequently authorized
implementation under the [work packet](../planning/active/work-packets/versioned-service-observability.md).
Its execution record, not the historical decision-capture notes below, tracks
current implementation. This audit is not a new live qualification result.

## 1. Scope and source precedence

**19 September lifecycle supersession:** the operator accepted
[ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md).
Park/Resume is removed from Studio and from mandatory demo qualification;
native CM shared-storage retention is known failing upstream. The remaining
matrix is exercised in a continuous clean run. SOTA/model/outbox continuity,
offline behavior, page/backend recovery and Finish are not waived.

The operator requested a comprehensive reconciliation of the original product
stories, the current single-Mac setup, version transitions, service behavior
and Presenter before further fixes. No executable source, accepted contract,
mockup, package, Cloud object or running process was changed for this audit.
No maneuver, reset, new publication, downgrade or E2E run was executed.

Use these sources together, not as competing requirements:

| Source | Authority used in this audit |
| --- | --- |
| [Scenario 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md), especially G2/G3/G4/T1 | Original product evolution and audience-visible proof. Its provisional G3 signal wish list is not the later frozen signal contract. |
| [Architecture Flows 2.1](../architecture/demo-scenario-architecture-flows.md), AF-G2-RT/OB, AF-G3-RT/OB, AF-G4 and AF-TIRE | Data directions, ownership, continuity, failure containment and correlation. |
| [D4 register](../requirements/d4-decision-register.md), D4-003/007/016/018/026 | Stimulus, compatibility, product/state/advisory and evidence decisions. |
| [VDP compatibility](../../contracts/vdp-compatibility-profile/README.md), [Brake window](../../contracts/brake-telemetry-window/README.md), [Brake model](../../contracts/brake-health-model/README.md), [Brake runtime](../../contracts/brake-health-runtime/README.md), [Brake advisory](../../contracts/brake-health-advisory-policy/README.md), [Tire product](../../contracts/tire-health-model/README.md) | Executable signal, model, freshness, persistence, compatibility and message semantics, including dated accepted amendments. |
| [UI-STUDIO-026](../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract) | Current Test-only flow, publication/assignment, native-left/Studio-right layout, summary/dialog navigation and evidence sources. Supersedes older Production/approval/terminal presentation provisions. |
| [Native service inputs](../architecture/demo-control-service-inputs.md) / ADR 0015 | Native instance identity, package release, public VDP metadata and private token placement. Supersedes the original mandatory service/model OCI-digest input. |
| [Readiness/reset packet](../planning/active/work-packets/advisory-readiness-and-demo-reset.md) | Accepted September native advisory labels, independent reset, offline renewal and no-restart post-Provision attachment. |
| [Factory .35 qualification](factory-35-e2e-2026-09-17.md), [pre-UI checkpoint](pre-ui-checkpoint-2026-09-17.md), [current chain audit](service-chain-audit-2026-09-18.md) | Dated evidence with different scopes; an earlier passing controlled maneuver is not proof that the latest releases or arbitrary Autopilot driving pass. |

The actual implementation is authoritative for what exists, not permission
to silently redefine the accepted product. Differences below are classified
as implementation gaps, document drift, evidence gaps or proposed changes.

## 2. Version vocabulary and current setup

Never conflate four different identities:

- Functional profile: VDP V1/V2/V3, Brake V1/V2/V3, Tire V1.
- Monotonic Cloud package release: currently VDP **79.0.0**, Brake **59.0.0**,
  Tire **34.0.0** in the preserved Test observed by the preceding audit.
- Model identity/configuration: Brake and Tire synthetic models remain their
  own versioned products; a new package does not imply a newly trained model.
- Compatibility-document identity: `aosedge-demo-vdp-compatibility` **1.0.1**
  describes the whole VDP family. It is not VDP functional V1, V2 or V3.

Current setup is Factory `.35`, one staging Test Domain Controller, one live
CARLA/Gateway, native Driving Control/Telemetry, two separately assigned
services and two Mac-hosted functional backends. Brake and Tire use separate
retained Group Subjects and SP publication contexts. Production is deferred.
The current graph is VDP V3 + Brake V3 + Tire V1: it cannot re-prove the earlier
V1/V2 chapters without a later clean cycle. Do not downgrade it for this audit.

The original Tire product is explicitly one mature **V1 with analytics and
advisory**, not an undisclosed V3. Subsequent Tire package releases repair or
extend that same functional profile unless a new product version is approved.

## 3. Accepted capability and product matrix

| Installed functional graph | What the vehicle/service does | Backend evidence | Native advisory expectation |
| --- | --- | --- | --- |
| Empty Factory / no VDP | Local simulator/dashboard can run; no functional service data path | No product results | Not available |
| VDP V1, no Brake | Publishes seven base-dynamics paths into KUKSA | No invented function result | Both Not available |
| VDP V1 + Brake V1 | Brake reads six base paths, excluding steering; captures a bounded hard-braking window | Growing PRE/ACTIVE/POST window, ordered chunks, explicit completion or abort | Both Not available; Brake V1 has no advisory |
| VDP V2 + Brake V1 | Fifteen platform paths; Brake retains its original six-path behavior | Same V1 window product, not an assessment | Both Not available |
| VDP V2 + Brake V2 | Twelve-path local synthetic Brake model; one assessment per eligible completed episode, event only on band change | Score/band and derived features/events, not new normal V1 raw-window traffic | Both Not available |
| VDP V3 + Brake V2 | Twenty-three platform paths and both advisory transports; Brake remains V2 analytics | V2 assessment/event continues | Support exists, but both Waiting for service until a compatible producer appears |
| VDP V3 + Brake V3 | Same Brake model/state plus typed local advisory | Assessment/event and separately correlated advisory facts | Brake Monitoring or a valid confirmed recommendation; Tire Waiting for service if absent |
| VDP V3 + Brake V3 + Tire V1 | Independent Tire 15-path model, condition/hysteresis, reports and local advisory | Separate Tire assessment/event/status/advisory evidence; Brake unchanged | Each endpoint independently Monitoring, warning or Unavailable |

Compatibility: Brake V1 accepts VDP V1/V2/V3; Brake V2 accepts V2/V3; Brake
V3 and Tire V1 require V3. Early installation with missing capabilities must
not fabricate a healthy function. Do not describe a demo sequencing guard as
native Cloud dependency admission.

The frozen VDP progression is 7 → 15 → 23 inbound paths. V2 adds eight wheel
linear/angular speeds. V3 adds eight slip paths plus typed advisory support.
The provisional original examples of pressure, temperature, ABS and pad-wear
signals are not part of this accepted native input set.

## 4. Transition matrix for this setup

| Transition | Required continuity / action | What Presenter should communicate |
| --- | --- | --- |
| Create → local simulator → Provision | Boot controller; start/reuse local source without attachment; publish initial VDP; Provision/Online; attach existing source in stationary Manual; verification membership | Distinct local-running, Cloud-registered and attached facts; no second CARLA/control restart |
| VDP publication before Provision | Publication can finish without a recipient. Warehouse flow may start from a higher profile | Published / no eligible vehicle yet, not failed installation. Skipped chapters are not demonstrated |
| First VDP / VDP V1→V2 / V2→V3 | Delivery and application separate; explicit native Safe Stop for component application; old version remains active while waiting | Requested/published/pending/installed separately. After install, functional evidence separate from Cloud inventory |
| First Brake or Tire publication | SP publishes; OEM assigns only the service ID through that team's Subject to current Test | Publish then Deploy to Test; no service-version or instance-count assignment field |
| Brake V1→V2 | Later publication updates the existing service identity while moving; model starts from its accepted preconditioned state; retained V1 spool drains in background | Recorder → edge analytics. Late V1 records labelled historical; V2 is not blocked by an old spool |
| Brake V2→V3, prior MONITOR | Preserve model and producer state; enable advisory; next eligible episode can cross the threshold | Monitoring is available; a warning is not guaranteed merely by installation |
| Brake V2→V3, prior INSPECTION | Preserve exact model state; activate warning from the persisted assessment without creating another assessment/event | State carried from V2; new V3 advisory confirmation linked to its originating assessment. Do not wait for or invent a new assessment to explain activation |
| Same-profile repair release | Preserve model/outbox/epoch; continue sequence; old requests/records keep original provenance, new refreshes identify the current release | Release updated, state retained, awaiting current-release observation where necessary—not a new drive/reset |
| Tire first install / later repair | Tire first starts NOT_EVALUATED; later same-schema repair retains model/hysteresis and queue; Brake unaffected | Independent function/condition/report state; do not call V1 advisory unsupported |
| Backend Reset | Only Brake V3 or Tire V1; scoped model/capture reset and correlated Gateway CLEAR; history/outbox/sequence retained | Resetting → confirmed reset, or failure/expiry. No GOOD assessment, service update, physical repair or scene reset is implied |
| Vehicle external Offline | Local IAM/KAC/KUKSA, analytics and advisory continue; backend delivery queues; Cloud independently observes connectivity | Local function can work while right-side data is delayed. Last result is not a live condition report |
| Reconnect | Same identity; drain queues idempotently with original source time | Delayed receipt is history/synchronization, not a new maneuver or fresh old warning |
| CM/VM restart retention (engineering only; ADR 0017) | Known failing upstream shared-storage cleanup; not part of the mandatory continuous demo cycle | Park/Resume is absent; interrupted established runs offer confirmed Finish. Cloud Online does not establish retained state |
| Finish / next run | Dispose only owned Test and ordinary data; preserve .35, infrastructure and release continuity | Partial cleanup remains actionable; next run starts empty with newly allocated releases |

Service updates do not require Safe Stop. A controlled test maneuver may
itself begin with Safe Stop/scene reset; never confuse that harness preparation
with a SOTA installation prerequisite. VDP replacement can briefly interrupt
capture: a partially captured episode must have an honest aborted/incomplete
outcome, not be reconstructed as though no interruption happened.

## 5. What the physical drive proves

Free Autopilot/Manual driving is a valid live input, not a guaranteed test
stimulus. Brake needs speed >=10 km/h, pedal >=50% held 200 ms; V2/V3 also
needs at least five active and five near-straight qualified samples. Tire
needs a moving/turning episode (speed >=12, absolute steering >=3 degrees for
500 ms) with at least 20 valid active samples. The two products must not be
judged by the same trigger.

Brake begins at synthetic wear 54 / score 46 / MONITOR. Its accepted model
accumulates use; it does not report a new event on every assessment or clear
wear merely after gentle driving. Tire is different: first eligible evidence
sets a band, worsening applies immediately, improvement requires three
consecutive eligible episodes of the same better band. Same-band Tire reports
are limited to one per 30 seconds, though local evaluation continues.

The .35 record documents successful controlled Brake/Tire CLI maneuvers with
real KUKSA data and UI-observed results, including warning/reset/renewal. It
does not establish latest-release long-drive continuity, fully UI-only test
stimuli, or the original D4-003 20 Brake / 10+10 Tire calibration series.
D4-003 remains RESEARCHING in its owner register; this audit found no closure
of that gate in the inspected .35/readiness qualification records. Do not
promote a one-run inspection result into proof of healthy/pre-aged separation.

Recommendation: retain free driving and provide one clearly labelled,
repeatable demonstration maneuver per team through the existing single tick
owner. Native control already has a conditional scripted-scenario action;
Demo Control has `simulation exercise brake|tire`. Audit/reuse those actions,
not a new simulator controller. Exposing a team selector or new button is an
explicit UI action change, not assumed by this document. No oracle, invented
telemetry or model-threshold tuning is permitted to make a demonstration pass.

## 6. Gaps and proposed disposition

Priority P0 means resolve before another claimed full functional pass; P1
means close before accepting the complete versioned audience story. Source
findings below are not all reproduced live failures.

| ID / priority | Finding and evidence | Proposed change / owner / approval boundary |
| --- | --- | --- |
| VS-01 / P0 | Prior chain audit: intermittent missing Gateway point, VDP whole-set invalidation, Brake explicit missing inputs. Non-atomic steering reads are a strong candidate, not yet fully correlated. | Gateway/VDP: bounded structural correlation then smallest proved source correction. Preserve current model thresholds and capture rules. |
| VS-02 / P0 | Effective compatibility evidence is incomplete. `aos-demo-service-inputs.py:snapshot` projects the common document pair, not active profile/capabilities. Both services' `parse_metadata` validates shape, not profile range. KUKSA metadata checks see schema, not which publisher is active. | Platform + services: explicitly version the existing public-input projection to include validated active profile/capability identity and reevaluation boundary. No new identity service or SM patch. This changes an accepted input schema and needs approval. |
| VS-03 / P0 | Required versus actual VDP uses different dimensions: Tire function status says required `3.0.0`, while actual metadata denotes compatibility document `1.0.1`. Missing current values may be reported as generic data loss even when capability is absent. | Define required functional profile, actual profile/release, contract revision and transient input quality separately. Test early service install and automatic recovery after VDP update; do not silently fail open or infer profile from release major. |
| VS-04 / P1 | Brake V1 `WindowEngine` retains every third valid input frame. Current VISS profile requests 50 ms / nominal 20 Hz; at 20 valid frames/s this is about 6.7 retained samples/s, not the specified 10. V2/V3 already uses 100-ms source-time buckets; Tire uses elapsed source time. | Brake owner: reconcile original 30-Hz assumption with actual transport; use real source-time-based 10-Hz selection without interpolation. Update the acquisition contract/fixtures consistently. Current V1 retained rate was not remeasured in this V3 audit. |
| VS-05 / P1 | Complete-record counters replaced the V1 narrative. Brake backend only routes collection reads; the accepted bounded window-detail point read is absent. Demo Control/Presenter never fetch its samples or render PRE/ACTIVE/POST. | Implement accepted window-detail read, bounded adapter and phase-marked graph in the existing Brake dialog. Preserve max 150 stored samples and gaps; do not add raw streaming for V2/V3. |
| VS-06 / P1 | Brake has no backend function/episode-status product. V1/V2 do not run the V3 reset-control poll; Presenter derives service contact from that poll, so lack of reset contact cannot mean no V1/V2 telemetry. | Add a bounded, versioned Brake function/episode observation via its existing backend path. Separate telemetry, capture outcome, result, delivery and advisory. New wire product requires approval; no guest polling in Presenter. |
| VS-07 / P1 | Tire has a status product but watcher-driven disconnect only changes local state/log; it does not emit function status there. Delivery failures also do not invoke all available status reasons. A retained READY can persist until backend stale timeout. | Complete existing Tire status transitions and freshness tests. Preserve local estimation offline; avoid requiring network delivery to establish local readiness. |
| VS-08 / P1 | `backendProduct.ts:productRows` re-sorts by receipt time, and summaries choose the first matching result. Late old same-release records can replace newer source results. Selection does not enforce current native instance/epoch. Only ten rows/resource are fetched, with local pagination over that subset. | Separate receipt history from current model state, use source-owned ordering/provenance and explicit current binding; bounded backend cursor/detail reads when needed. Retain old records, never relabel them current. |
| VS-09 / P1 | Current-release assessment gating cannot explain persisted V2→V3 warning activation. `backendSummary` ignores advisory facts as product proof, correctly, but has no separate inherited-condition/advisory presentation. | Keep new-assessment proof separate. Show carried model condition and a correlated current V3 advisory fact with its original assessment provenance. Define chapter proofs per profile, not one generic latest-result gate. |
| VS-10 / P1 | Reset filtering uses any command's issue time, even pending/failed/expired commands. Modal evidence callback uses unfiltered retained records; summary proof filters after reset. Historical reset may belong to a replaced instance. | Distinguish pending reset, confirmed applied reset, failed-before-application and uncertain-after-application. Use one scoped selection rule; never hide valid results or reuse old reset authority just because a command was issued. Extend outcome evidence if application is ambiguous. |
| VS-11 / P1 | Brake diagnostic advisory readiness begins unproved and can call that Gateway unavailable; individual Tire status errors use a catch-all. Native Monitoring, persistent model warning, backend fact and process health have different meanings. | Keep accepted native labels; expose unproved/transport-failed separately in engineering/backend status. Correlate request/ack and readiness writes before changing lease behavior. Do not send a fake SET/CLEAR just to prove readiness. |
| VS-12 / P1 decision | Brake freshness is 5000 ms; Tire and VISS freshness remain 250 ms. Incomplete VDP frames invalidate all selected paths, even paths an older service does not consume. | First fix the source and measure. A Tire timing amendment or capability-group invalidation policy requires separate contract review; raising one timeout cannot repair explicit missing values. Safe Stop and auth/advisory leases remain separate. |
| VS-13 / P1 | No original calibration-closure evidence in the inspected current packet; .35 pass used approved CLI maneuvers and predates latest long-drive defects. | Separate source tests, preserved-Test proof, clean UI cycle and calibration claims. Qualify the chosen same-Mac demo stimulus before promising a predictable warning. |
| VS-14 / P1 | Polling waits five seconds after each completed read; Demo Control backend observation reads resources serially with per-request timeout. This is not a fixed five-second live update guarantee. | Measure scoped read/visible lag after functional fixes; reuse shared observers, bounded requests and per-resource freshness. Do not turn unavailable optional history into a misleading whole-function outage. |
| VS-15 / P2 | Generic summary labels V1 window data as a model estimate; title-case warning strings are tested with uppercase-only warning regexp in `StudioSummaryCards`. | Profile-specific copy and enum-based visual severity. V1 is a recorder, not an estimator: no model score for V1; no advisory/reset controls for V1/V2. V2 retains its model score. |
| VS-16 / P1 documentation | Several README/status sections still claim no Tire repository, Test-only migration pending or permissions blocked, while .35 evidence is later. Broad VDP NOT_READY/no-output wording also needs explicit alignment with the accepted Brake analytics/advisory axes. | Publish one applicability/closure map, preserve historical evidence, amend current owner documents after decisions. Do not reinstate old Production, approval or credential design. |

VS-02/03 are a static assurance/diagnostic gap, not proof that the current
compatible V3 graph is unauthorized. The five-field public-input contract was
an approved simplification; correcting it requires coordinated schema and
producer/consumer changes, not silently adding fields to a strict reader.

## 7. Presenter model and fixed-layout proposal

Keep CARLA and native Driving Control/Telemetry on the left. Keep the Vehicle
architecture, B2 miniatures, service/component slots, connectors, three backend/
Cloud cards and existing detail dialogs on the right. Team release views
remain. No new page, Controller tab, direct VM read or embedded CARLA is needed.

The inline team card should answer three questions, using its backend only:

1. **Function:** receiving input / waiting for compatible VDP / data unavailable
   / last-known report. Until a function-status contract supplies the fact,
   show Not reported instead of guessing from installation or contact.
2. **Activity/result:** waiting for braking, recording PRE/ACTIVE/POST,
   episode skipped with reason, or last assessment with source age. State
   that Tire intentionally reports some same-band results less frequently.
3. **Delivery:** last confirmed receipt / delayed / synchronization pending,
   as supported by service/backend evidence. Cloud Offline alone does not
   prove the functional backend is unreachable.

| Dialog/profile | Primary content | Secondary evidence |
| --- | --- | --- |
| Brake V1 | One growing/complete bounded event graph: speed/deceleration and pedals, PRE/ACTIVE/POST bands, real sample gaps | Chunk/completion integrity, capture/abort reason, event time and receipt time; no model score |
| Brake V2 | Synthetic condition score/band, change from previous assessment, compact accepted feature values | Last episode outcome, model/config provenance, original V1 history visibly separated; no live advisory claim |
| Brake V3 | Same model view plus advisory request/application evidence; explicit inherited V2 assessment where relevant | Independent Reset, request/epoch/sequence and Gateway acknowledgement; native dashboard remains current vehicle display |
| Tire V1 | Synthetic condition score/band, confidence, latest exercise, report age | Hysteresis explanation, typed advisory history, independent Reset; no hidden friction/profile oracle |
| Aos Cloud | Actual Unit state, installed/pending releases, service instances and resources in DMIPS/bytes | Per-resource timestamps and partial/last-known status; no inference of product health |

Do not create a single green badge that means all of installed, receiving,
qualified, delivered and advisory applied. Native labels stay Not available /
Waiting for service / Monitoring / confirmed warning / Unavailable under the
accepted telemetry-only contract. An unexpired confirmed warning retains its
own priority; lack of a new assessment or loss of backend connectivity is not
an instruction to clear it.

Overview and dialog must use the same result selector. Current model condition,
new-release acceptance proof, after-reset drive outcome and delivery history
are distinct views of the same sourced records, not duplicate local truths.
Use existing run/action evidence for chapter history; do not add another
independent lifecycle database or claim skipped chapters passed.

## 8. Decisions and approval record

| Question | A — recommended | B — alternative |
| --- | --- | --- |
| Repeatable audience drive — A accepted with Return to road, 18 September 2026 | Keep free driving; reuse/expose explicit prepared Brake/Tire maneuvers for predictable product proof. Scene action is visibly separate from model Reset and SOTA | Free driving only; explicitly accept unpredictable time to a qualifying result/warning |
| Function observability — A accepted, 18 September 2026 | Add minimal Brake status/episode facts; complete Tire's existing status; read both through their own backends | Native Cloud logs on demand only; less code but the live cards cannot explain why a running service has no result |
| Compatibility identity — A accepted, 18 September 2026 | Version the existing public-input contract with actual VDP functional capability evidence; keep native Aos identities and resources | Keep five fields and report compatibility as unconfirmed. This cannot close the original runtime compatibility requirement |
| Aos Cloud summary — A accepted, 18 September 2026 | Show Unit state, installed component/service counts, update state and observation freshness; keep resource metrics in the monitoring dialog | Retain CPU and memory on the summary card with compact formatting and secondary visual emphasis |
| Service/backend color association — A accepted, 18 September 2026 | Repeat stable Brake purple, Tire teal and platform blue accents across the relevant cards, service/backend connectors and dialog headings; status colors remain independent | Limit group colors to card headings and keep connectors and other elements neutral |
| AosCore and AosEdge platform presentation — A accepted, 18 September 2026 | Show AosCore with a distinct B2-style software miniature inside Factory firmware; label its role and Aos Cloud's role and give both shared AosEdge platform branding | Add only `includes AosCore` to the Factory firmware label, without a miniature or shared platform branding |
| Timing/completeness | Correct source sampling first, retain thresholds, then decide any measured Tire freshness adjustment separately | Broaden Tire freshness now with coordinated contract/validator changes; does not solve explicit VDP invalidation and risks obscuring diagnosis |

The accepted A choices, plus the proposed source-first timing approach, form
the bounded package. No new CM/SM/IAM behavior, Cloud code change, safety authority,
production rollout or model algorithm is proposed. Any later finding requiring
such scope must return for a separate decision.

### Decision 1A — function observability (accepted)

The operator explicitly accepted option A on 18 September 2026:

- Brake will send bounded function/episode observations to its own backend;
  Tire will complete its existing equivalent status mechanism.
- Presenter will obtain these observations only through the corresponding
  backend, never through direct guest access. Native in-vehicle advisory
  continues to depend on vehicle telemetry, not backend availability.
- Input availability, capture activity/outcome, the last assessment and
  delivery freshness remain separate facts. Waiting for a qualifying brake
  episode must not imply that telemetry is absent or erase a prior result.
- Emit observations on state changes and at a bounded periodic interval for
  freshness. This does not authorize continuous raw-telemetry upload.
- Preserve source/receipt age and show last-known or unavailable information
  honestly when communication is lost. Detailed rejection reasons belong in
  the dialog; no new assessment is fabricated to explain activity.
- Model algorithms, thresholds and local advisory behavior are unchanged.

The exact wire schema, bounded cadence and freshness policy will be specified
in the coordinated contract update before implementation. This acceptance
does not itself authorize the other proposed design changes or start the
implementation phase.

### Decision 2A — active VDP capability identity (accepted)

The operator explicitly accepted option A on 18 September 2026:

- Extend the existing versioned local public-input contract with the active
  VDP functional profile, actual component release and provided capabilities.
  Keep compatibility-document revision separate from these identities.
- Evidence must describe the installed, running VDP, not a Cloud publication,
  desired release or pending installation. Missing or invalid evidence must
  not imply that the required capabilities are available.
- Services will distinguish an absent/incompatible active VDP from a
  compatible VDP whose current telemetry has not arrived or is unavailable.
  Receiving data requires actual current input, not inventory alone.
- Services will automatically reevaluate compatibility and readiness after
  VDP activation, without another Deploy action. Specify and test the update
  propagation boundary in the coordinated producer/consumer contract.
- Presenter obtains the service's explanation through its backend; this
  introduces no direct guest reads by Presenter. Native in-vehicle advisory
  remains governed by its existing telemetry-only contract.
- Reuse native Aos identities and resources and the existing input-projection
  mechanism. No CM, SM or IAM behavioral changes are approved by this choice.

The exact additive schema revision, active-evidence validation and refresh
mechanism must be reconciled with strict consumers before implementation.
This approval does not change model thresholds, service delivery semantics or
the component Safe Stop requirement, and does not start implementation yet.

### Decision 3A — repeatable maneuvers and Return to road (accepted)

The operator explicitly accepted option A on 18 September 2026 and requested
a separate Driving Control button to return the vehicle to a suitable road
position so that Autopilot can be started again, especially after manual driving.

- Preserve free Manual driving and Autopilot. Reuse the existing prepared
  Brake/Tire maneuvers through the single simulator control owner and expose
  an understandable selection in native Driving Control.
- Use real CARLA physics and the normal telemetry path. Do not synthesize
  measurements or results or change model thresholds to obtain a warning.
  A suitable maneuver produces an opportunity for evaluation, not a promise
  of an advisory regardless of the retained model condition.
- Keep maneuver launch, model/advisory Reset, software update and vehicle
  repositioning as separate actions. Any scene preparation required by a
  maneuver must be visible rather than a hidden model or lifecycle reset.

Return to road UX and implementation acceptance criteria:

1. Provide a separate **Return to road** button in native Driving Control.
   Reuse the existing scene recovery/control path; do not create a second
   CARLA tick owner or restart CARLA, the VM, Gateway or service processes.
2. Stop autonomous/manual motion before repositioning, clear held manual
   commands, and place the car at a validated drivable location aligned with
   the lane. A documented known-good spawn is acceptable; nearest-road
   recovery is not required. Do not report success for a blocked/invalid
   placement or before the car has settled and control is available.
3. The intended final state is stationary Manual, ready for the operator to
   explicitly select Autopilot. Do not automatically resume the old motion
   command. Verify the handover against the existing control/stop contract.
4. Preserve the current Test assignment, software versions, service model
   state, advisory state and backend history. This action is not a new run,
   model Reset, service restart or Cloud operation.
5. Mark the physical repositioning as a scene discontinuity using the
   existing control facts. An interrupted capture must not become a fabricated
   braking/cornering result, nor may teleportation be evaluated as wear.
6. Show in-progress, confirmed completion or a bounded failure; prevent
   competing control operations and duplicate recovery requests. An uncertain
   response requires reconciliation, not a blind repeated scene reset.

Exact button placement, command wiring and the stationary Manual handover
will be specified and verified in the implementation packet. The existing
exercise helper uses a stopped/reset/settled sequence, but this audit does not
claim that the requested native recovery button is already implemented.

### Decision 4A — Aos Cloud summary and resource detail (accepted)

The operator explicitly accepted option A on 18 September 2026:

- Replace CPU and memory on the main Aos Cloud card with the Cloud-reported
  Unit state, installed component/service counts, update state and observation
  freshness. Keep Online, Connected and Offline distinct; do not reinterpret
  Cloud connectivity as proof of service input, analytics or advisory health.
- Use confirmed, appropriately scoped inventory for counts. Do not count a
  prepared/published candidate as installed or confuse service identities with
  running-instance counts. Example counts in the design are illustrative.
- Distinguish pending/in-progress updates and reported failures. Show
  `No pending updates` only when the required current observations support it;
  it must not conceal a failed update or an unavailable/partial read. It is
  not a claim that every published release is installed or every function works.
- Retain source/observation freshness and explicit last-known/unavailable
  labels. Resource-read success must not refresh the apparent age of unrelated
  inventory or Unit-state evidence.
- Clicking the card continues to open the existing monitoring dialog with
  detailed software inventory, CPU, memory, disk and other reported resources.
  Format verified byte-valued memory compactly as MiB/GiB, retaining exact
  values where useful in details; do not guess missing source units. CPU
  remains in DMIPS, not a fabricated utilization percentage.
- Preserve the fixed composition and Cloud-only observation path. This
  agreement does not approve a new page or changes to lifecycle actions.

Color association and the AosCore/Factory firmware presentation are separate
decisions; see decisions 5A and 6A below. No executable UI
code or running state was changed when recording this acceptance.

### Decision 5A — stable service/backend color association (accepted)

The operator explicitly accepted option A on 18 September 2026:

- Assign stable visual identity accents: **Brake purple**, **Tire teal** and
  the **existing platform blue**. Exact accessible design-token shades will
  be selected during visual implementation; these are not status values.
- Repeat each Brake/Tire accent on its backend card, connecting line,
  installed-service card inside the Domain Controller and corresponding
  detail-dialog heading. Use restrained accent strips, outlines and light
  tints rather than saturated full-card backgrounds.
- Keep the B2 miniatures in their natural appearance and the main background
  predominantly light. Retain the existing layout and fixed viewport budget.
- Group identity remains unchanged for healthy, waiting, stale, advisory and
  error states. Show semantic status independently with text and an icon or
  badge using the appropriate status color; do not make a team permanently
  red or green to imply an operational state.
- Keep names and miniature/icon cues so the association does not depend on
  color perception alone. Validate label, focus and status contrast.
- A colored connector conveys association, not confirmed delivery, current
  telemetry or an active instance. Preserve empty/unobserved service-slot
  semantics and the existing Cloud connection-state meaning separately from
  the platform's blue identity accent.

This is visual-design approval only. It does not change data authority,
connectivity logic or state transitions. The AosCore presentation is covered
separately by decision 6A. No UI implementation or running-state change was
made at agreement.

### Decision 6A — AosCore and the AosEdge platform relationship (accepted)

The operator explicitly accepted option A on 18 September 2026:

- Retain the Factory firmware area at the base of the Domain Controller.
  Show **AosCore**, a small distinct B2-style system-software miniature and
  the role label **In-vehicle runtime** within that area. Preserve the
  existing Factory image selector and its lifecycle-dependent availability.
- The composition must communicate that AosCore is integrated into the
  Factory firmware and already present at controller creation. VDP and the
  Brake/Tire service slots remain separate subsequently installed products;
  their empty-state behavior is unchanged.
- Add the role label **Cloud management** to the Aos Cloud card. Give the
  AosCore area and Aos Cloud card the same platform-blue identity accent and
  small **AosEdge platform** label so they read as the vehicle and Cloud parts
  of one platform. Group branding is not evidence of a live connection.
- Use a system-software miniature consistent with the accepted B2 art style,
  distinguishable from both the physical Domain Controller miniature and
  the VDP component icon. Do not introduce a competing product logo or imply
  that AosCore is a second hardware controller.
- Do not expand the primary architecture into CM/SM/IAM internals, add pages,
  replace the current decomposition or consume the native-left screen area.
  Keep labels legible within the fixed right-hand viewport without scrolling.
- Preserve the distinction between the Factory image identifier and any
  actual AosCore version: do not infer a Core version or health status from
  the image name, the shared blue accent or the Cloud connection status.

This acceptance authorizes the visual direction, not a new AosCore capability,
runtime state source or extra lifecycle action. No miniature was generated
and no mockup, UI code, process or Cloud object was changed while recording it.

### Decision 2A correction — native Cloud authority (accepted)

After the initial implementation inspection, the operator rejected a proposed
guest evidence timer and accepted the Cloud-first correction on 18 September.
This entry supersedes earlier prescriptions of a mandatory new active-evidence
projection, including VS-02's proposed mechanism, not the compatibility matrix.

- Presenter software inventory, instance state, update errors and resources
  come from native Aos Cloud, with no duplicate guest monitor.
- Bind the exact Cloud-confirmed installed artifact to its verified functional
  profile. Release major and the family document version are not that profile.
  Public API metadata_info exists, but our actual package contents remain to
  be verified; do not assume a usable profile field or forward arbitrary data.
- Service input, episode, product and delivery facts come from the corresponding
  backend. Cloud Running/Installed does not prove telemetry or model output.
- Local compatibility recovery, analytics and advisory must work without Cloud
  or Presenter access. Prove existing native input paths before proposing any
  genuinely necessary new interface. No guest timer or new evidence expiry.

The [work packet](../planning/active/work-packets/versioned-service-observability.md)
records the revised sequence and remaining proofs. This acceptance changes
the plan, not the running Test or the status of unexecuted qualification gates.

### Discussion progress

Subsequent P2 clarification, accepted 18 September: after the
[local-input proof](service-renewal-and-local-capability-2026-09-18.md), the
operator selected option A. Exact installed profile and version compatibility
are Cloud/package-derived Presenter observations; services use actual local
input/capability readiness without Cloud dependence. Missing data does not
prove an incompatible profile. No new local active-profile transport is added.
This supersedes the earlier exact service-local discrimination requirement,
not the compatibility matrix, strict legacy readers or automatic recovery.
Implementation and full live qualification are still separate gates.

Checklist, in the order presented to the operator:

1. Function observability and display — **A accepted**.
2. Active VDP capability identity — **A accepted**.
3. Repeatable demonstration maneuvers — **A accepted**, with the separate
   **Return to road** action in native Driving Control.
4. Aos Cloud card content — **A accepted**; resource metrics remain in its
   monitoring dialog.
5. Color association between services and backends — **A accepted**.
6. AosCore in Factory firmware and the AosEdge platform relationship —
   **A accepted**.

The source-first timing recommendation remains proposed; no Tire freshness or
whole-frame invalidation policy change has been accepted by decisions 1A–6A.

## 9. Ordered delivery and verification after approval

1. **Contract reconciliation:** freeze profile matrix, reset/result chronology,
   status vocabulary and additive input/message revisions. Update owner docs
   and mockup expectations without replacing retained artifacts.
2. **Telemetry and compatibility:** close missing-path attribution; targeted
   source correction; Brake V1 cadence; active VDP identity/reevaluation.
   Prove with duplicate/missing/mixed/future/stale and wrong-profile negatives.
3. **Service/backend behavior:** retain state/outbox across updates; complete
   status transitions, inherited condition, reset outcome and chronological
   read models. Add accepted V1 window detail. Keep old wire records readable.
4. **Presenter and Driving Control:** profile-specific summary/dialog content;
   shared selectors, freshness, current-instance binding, maneuver selection
   and the separate Return to road action within the same fixed layout. Revise
   the Aos Cloud summary per decision 4A and format resources in its dialog.
   Apply decision 5A identity accents without conflating them with status.
   Show AosCore in Factory firmware and the shared AosEdge platform identity
   per decision 6A, preserving the image selector and empty software slots.
   Test fixture sequences without confusing them with live proof.
5. **Preserved Test:** prove source continuity on VDP79/Brake59/Tire34 or their
   explicitly published successors; one real result/ack per service, independent
   reset/renewed warning, offline continuation and no peer restart. No downgrade.
6. **Clean staged UI cycle:** use .35 if no factory-owned change is needed;
   build one successor only if a proven change must be baked into its projector/
   runtime resources. Execute the full sequence below with actual visible
   results, offline/reconnect and retirement. Per ADR 0017, do not include a
   same-run CM/VM restart or rebuild merely for UI edits.

### Required transition tests

- VDP V1 + Brake V1: actual retained cadence; PRE then live ACTIVE/POST; window
  detail, gap/abort and durable completion; no assessment/advisory.
- VDP V1→V2 while retaining Brake V1: FOTA holds outside Safe Stop; old service
  resumes its six-path product after the transition without reinstall.
- Brake V1→V2 while moving: retained legacy queue drains unchanged; one new
  V2 assessment and no new normal V1 window generation.
- VDP V2→V3 while retaining Brake V2: analytics continues after recovery;
  native advisory support waits for compatible producers, not inferred V3 Brake.
- Brake V2→V3: test both MONITOR and persisted INSPECTION; latter generates
  a current advisory confirmation without another assessment or band event.
- Tire V1: current V3 graph, independent assessment/inspection; later package
  replacement retains model and queue and leaves Brake untouched.
- Early/missing/unsupported VDP: distinguish capability absent from transient
  data loss; automatic reevaluation without service reinstall. No native Cloud
  pre-transfer-rejection claim and no arbitrary downgrade campaign.
- Reset versus SOTA/restart: old bound commands cannot act on a new instance;
  failed/expired/partially applied outcomes remain honest; peer/history retained.
- Offline with V1 backlog, V2/V3 results and Tire reports: bounded queues,
  local advisory, renewal, reconnect and out-of-order receipts; no current-state
  rollback, no fabricated all-results-delivered claim after overflow.
- Native warning expiry/refresh/CLEAR and stale producer status: backend
  history never overrides the native display; readiness is not a warning ACK.
- Return to road after manual off-road/collision and from Autopilot: validated
  lane position, correct heading, stationary confirmed handover, then explicit
  successful Autopilot start; no stack restart or model/advisory reset. Test
  scene-discontinuity handling, occupied placement, busy/double-click and
  uncertain-response cases without fabricated model results.
- Page reload, backend restart and partial API failure: retain appropriate
  state, source timestamps and scope; no duplicate operation. CM/VM restart
  storage retention is a separate known failing upstream test under ADR 0017,
  not a passed or mandatory operator Park/Resume case.
- Aos Cloud summary: Online/Connected/Offline, partial/stale inventory,
  pending/failed updates and confirmed absence of pending updates remain
  distinct. Resource values are absent from the overview but available in
  the dialog with verified units, compact memory formatting and DMIPS CPU.
- Group colors: Brake/Tire association remains consistent across cards,
  connectors and dialogs in empty, active, stale and warning states; status
  remains distinguishable by text/icons without relying on color alone.
- Platform presentation: AosCore is visible in the Factory base independently
  of VDP/service installation and Cloud registration; its identity is distinct
  from hardware and VDP. Shared AosEdge branding does not imply connectivity.
  The image selector retains its behavior and the fixed layout remains legible.
- Finish from successful and abnormal states: exact owned cleanup and next
  run's release continuity; Production and .35 original preserved.

## 10. Concrete implementation anchors

Paths below are relative to the named sibling repository, except Presenter /
Demo Control paths which are in this repository.

| Area | Inspected implementation |
| --- | --- |
| Source completeness | `carla-ego-runtime/src/runtime_carla.cpp:CollectSample`, `src/vehicle_state.cpp:EquivalentFrontAxleAngleDegrees`, `src/vss.cpp` |
| VDP invalidation | `aos-vehicle-platform/providers/carla-viss-kuksa/src/carla_viss_kuksa_provider/bridge.py:BridgeState` |
| Public VDP evidence | `aos-vehicle-platform/meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/aos-demo-service-inputs.py:snapshot`; both services' `src/runtime/application.cpp:parse_metadata` |
| Brake capture/state/update | `brake-health-service/src/v1/window.cpp:WindowEngine::ingest`, `src/runtime/product.cpp`, `model_capture.cpp`, `advisory_runtime.cpp`; `tests/cpp/runtime/product_tests.cpp:product_upgrade_and_delivery` |
| Tire capture/status | `tire-health-service/src/model.cpp:EpisodeEngine`, `src/runtime.cpp:function_status`, `src/runtime/grpc_main.cpp:subscribe` |
| Backend detail gap | `brake-health-cloud/apps/backend/src/brake-data-http.ts`: collection route only; README explicitly marks window detail unimplemented |
| Demo Control reads/actions | `apps/demo-orchestrator/src/aosedge_demo_orchestrator/backends.py`, `presenter_operations.py`, `source_exercise.py` |
| Native scenario control | `carla-ego-runtime/tools/KeyboardControl.swift`: conditional scripted-scenario button |
| Presenter chronology/proof | `apps/presenter-ui/src/features/service-team/backendProduct.ts`, `useBackendObservation.ts`, `BackendEvidence.tsx`; `src/app/StudioWorkspace.tsx` |
| Version-specific rendering | `apps/presenter-ui/src/app/StudioSummaryCards.tsx` |

Verification performed for this audit: document/source cross-reference and
static path/selector review. Earlier live observations remain linked with
their exact scope. No source tests, new builds, live transition tests, runtime
changes, commits or pushes are claimed by this audit.
