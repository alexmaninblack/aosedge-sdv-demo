<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter and native UI: displayed facts and evidence audit

Date: 19 September 2026. Status: historical audit baseline.

The operator subsequently authorized all listed corrections. Implementation,
tests and remaining live qualifications are tracked in the
[correction record](presenter-ui-truth-fixes-2026-09-19.md). The findings below
describe the pre-correction source, not the current fixed UI.

## Executive result

The principal authorities are separated correctly: Cloud installation,
service-reported function, durable backend products and Gateway-confirmed
vehicle advisory are not interchangeable. However, several displays lose that
distinction in their timestamps, last-known qualifiers or error details.

The first correction group should be **F1–F2** below. F3–F7 are bounded
information/presentation defects; L1–L2 are observation-path concerns requiring
targeted qualification before a change. Optional improvements are separated
from defects. No finding authorizes changing model thresholds, freshness
leases, Cloud behavior, assignment, service permissions or the accepted flow.

## Scope, baseline and limitations

- Inspected the reachable local Studio route, not the legacy fixture/demo
  screens that remain in the source tree but are not rendered by this route.
- Covered Vehicle cards/architecture, Platform/Brake/Tire authoring,
  Cloud Software/Resources, component/service/package details, backend
  Overview/Records/window details, Session, operation confirmations/Trace,
  native Driving Control and Dashboard/Vehicle/Data telemetry projections.
- Traced their selectors to Demo Control's normalized Cloud/backend readers
  and the Gateway monitor. Consulted the accepted
  [Cloud observation contract](../architecture/demo-control-cloud-observation.md),
  [function observation contract](../../contracts/service-function-observation/v3-contract.md),
  [active packet](../planning/active/work-packets/versioned-service-observability.md),
  [native control contract](../../../carla-ego-runtime/docs/external-control-contract.md)
  and the [previous correction record](factory-36-follow-up-fixes-2026-09-19.md).
- The .36 Test was already retired. The current browser confirms **No
  controller created**, not a running vehicle. No new Test or telemetry was
  manufactured for this audit. Active/failure transitions were examined in
  source and isolated synthetic fixtures, not claimed as fresh live events.
- The user's existing browser tab has an older loaded build and correctly
  offers **Reload UI**. It was not reloaded. A separate temporary tab loaded
  the current served assets and was used for read-only navigation.
- Native desktop inspection was unavailable because the Mac was locked.
  Native projections were inspected in source and the executable scene-mode
  regression was rerun; this is not live visual qualification of those windows.
- Opening Session → Cloud performed its normal read-only certificate
  inspection. Selected Cloud and certificate domain both resolved to
  `aws-stage.epmp-aos.projects.epam.com`. No credential contents were exposed,
  settings changed or Cloud setup/publication actions executed.
- Main repository HEAD: `d2298ba2f283896717c8cd8aa123fc1c76149782`, with substantial
  existing working-tree changes. This report audits those working sources,
  not HEAD alone. No commit, push, build, restart or deployment was performed.

Current served `dist/index.html` SHA-256:
`992970f3dec46ac73c5f0c027842050203f397101f6777409d409d1a3090c233`.

Source fingerprints at audit time:

| File | SHA-256 |
| --- | --- |
| `StudioWorkspace.tsx` | `d9ff312a274d1bf7c20e829704265231ac98f92e7af9acacec9d752718b0e0f8` |
| `useBackendObservation.ts` | `0552d29143f91636bfa40f2bfbccdaec834b7bf68f8fb192a0da417b84d8929b` |
| `StudioReadViews.tsx` | `f4304608387e84523ac507addc798bce428ce7d9e1ebfb213c8007d328cd0bb5` |

## Confirmed discrepancies — separate correction list

P1 means correct before relying on this presentation in the next operator
qualification. P2 means a bounded visibility/interpretation defect. These
priorities concern demo evidence, not a claim of physical-vehicle risk.

| ID / priority | Where and what is displayed | What the implementation actually establishes | Evidence and correction direction |
| --- | --- | --- | --- |
| **F1 / P1** | Brake/Tire summary can show an old condition with **Result received · Observed 0s ago**. With a stale Cloud binding, the summary still lacks a result-level **last known** qualifier although the popup has one. | `recordsObservedAt` advances on a successful backend read even if no new product arrived. It is not result source time or receipt time. Product selection deliberately retains the latest matching historical result. A stale binding correctly removes story proof, but not the unqualified card title/status. | Reproduced with a 17 September result and a current read, for both current and non-current bindings. Keep the result, but separately label **Latest result**, its source/receipt age, **Backend checked**, and binding last-known state. Do not make old results disappear or invent a new result-expiry policy. [Summary](../../apps/presenter-ui/src/app/StudioSummaryCards.tsx), [selector/read stamp](../../apps/presenter-ui/src/features/service-team/useBackendObservation.ts), [popup](../../apps/presenter-ui/src/features/service-team/BackendEvidence.tsx). |
| **F2 / P1** | Cloud overview can show **1 pending / in progress**, while its component tile says **No pending release**. Details say **Pending release: None reported** alongside **Update state: downloading**. | A pending status can be present before the expanded pending-version object. The overview considers the status; the tile only tests `pending_component`. The Platform guidance also primarily uses `pendingVersion`. Missing version is not no pending update. | Reproduced a current `downloading` row with `pending_component: null`. Reuse one component-update interpretation; display **Update in progress · version not reported** and retain exact failure/status information. Do not infer a version. [Overview](../../apps/presenter-ui/src/domain/cloudSummary.ts), [component tile/Platform](../../apps/presenter-ui/src/app/StudioWorkspace.tsx), [details](../../apps/presenter-ui/src/app/StudioReadViews.tsx). |
| **F3 / P2** | Service details show an instance's `failed` state but can omit its actual numeric Aos/exit error. A generic service error is always labelled **Service update issue**, even when the available fields do not establish an update-specific cause. | The Cloud reader forwards per-instance `error_aos_code` and `error_exit_code`. The UI instance type/display only includes `error_message`; `serviceIssue()` checks aggregate fields, not instance numeric errors. | A failed instance with Aos code 42 / exit 137 and no message displayed neither code. A separate defensive fixture with `active` plus a numeric error also passed `serviceRunning()`; this conflicting source combination is **not claimed observed live**. Preserve codes and scope, and avoid labelling an unclassified runtime error as an update failure. [Cloud projection](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/cloud_observation.py), [type](../../apps/presenter-ui/src/domain/platformObservation.ts), [logic](../../apps/presenter-ui/src/domain/softwareObservation.ts), [rows](../../apps/presenter-ui/src/app/StudioReadViews.tsx). |
| **F4 / P2** | Service details label a timestamp **Cloud report**. A newly read, unchanged instance can therefore appear to have just reported from the vehicle. | `reportReadCompletedAt` is populated from the local API read completion, or the retained previous read completion. The native instance projection has `sourceTimestamp: null`; it does not supply the time of a new device report. | Source-traced: `StudioCloudReader` sets this field from section read times. Rename it **Cloud checked** / **Last successful Cloud read**, not device report time. The source report age must remain **not supplied** where unavailable. [Reader](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter.py), [display](../../apps/presenter-ui/src/app/StudioReadViews.tsx). |
| **F5 / P2** | Resources → Disk can display **NOT_REPORTED** although the observation contains disk samples. | The adapter supports both `usedDisk` and `disk`; its documented supplementary-absence policy accepts absent `usedDisk` when `disk` is current and non-null. UI buttons always select `usedDisk`; `disk` is never offered/rendered. | Reproduced with `usedDisk: UNKNOWN/null` and a current `disk` sample. Expose the supported disk representation with its actual parameter/partition and unverified units, rather than guessing equivalence or converting unitless values. [Monitoring](../../apps/presenter-ui/src/app/StudioReadViews.tsx), [adapter](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/cloud_observation.py), Cloud observation contract above. |
| **F6 / P2** | An open Brake window detail can continue showing **1/2 chunks** after delivery has reached 2/2. It offers no refresh or explicit snapshot-read time. | `BackendEvidence` holds the selected record object. `BrakeWindowDetail` reads once for that object/event; parent polling does not replace the selected object. Window delivery projections can change as late chunks arrive, even though previously retained bytes are immutable. | Reproduced changing the fixture response after the initial read: same selected row caused no second request, and no Refresh button exists. Either label the detail as a timestamped snapshot with explicit refresh, or reconcile this exact event through the bounded reader. Never replace it with another event/instance. [Selection](../../apps/presenter-ui/src/features/service-team/BackendEvidence.tsx), [window read](../../apps/presenter-ui/src/features/service-team/BrakeWindowDetail.tsx). |
| **F7 / P2** | Every real-data backend popup says **Demo model estimates**, including Brake V1 retained braking windows. | V1 acquires actual retained source samples; it does not calculate a condition estimate. The nested window correctly says **V1 acquires a window, not a condition score**. The common parent explanation is unconditional. | Source-confirmed contradiction between parent and V1 detail. Use profile/result-specific explanatory text: retained telemetry for V1, model estimate for health assessments. Keep real input provenance separate from model interpretation. [Backend explanation](../../apps/presenter-ui/src/features/service-team/BackendEvidence.tsx), [V1 detail](../../apps/presenter-ui/src/features/service-team/BrakeWindowDetail.tsx). |

F1 does not mean the stored product is false, and F4 does not mean the Cloud
read did not happen. The error is how scope/freshness is communicated. No audit
probe established data fabrication, cross-Unit leakage or an unintended write.

## Latency and partial-observation concerns

| ID | Source-confirmed mechanism | Risk / next bounded check |
| --- | --- | --- |
| **L1 / P2** | Each team's backend inspector performs nine sequential HTTP reads with a three-second socket timeout. The browser's aggregate backend request expires after 15 seconds. The next refresh waits another five seconds after completion/failure. | Several slow subresources can outlive the browser request, losing useful partial observations and creating apparent lag. Nine near-timeout reads already imply about 27 seconds of waiting in that scenario; socket timeouts are not a guaranteed overall deadline. This is a **budget mismatch**, not a measured 27-second stall in the retired run. Inject selective slow endpoints, measure complete request latency and cancellation, then align bounded server/client budgets or resource scheduling without weakening validity. |
| **L2 / P2** | Real backend availability is combined across product/history/reset resources. One failed required resource sets `model.error`; `backendSummary()` then downgrades even an independently valid fresh function resource to unavailable/last-known. Conversely, the function resource is not itself in the product-completeness list. | Conservative behavior avoids false green, but hides which boundary failed and can make a valid input observation disappear because a history/reset endpoint failed. Preserve independent resource outcomes and show **partial read**, not a guessed service/input failure. Any refinement must retain exact scope, conflict and reset gates. |

Sources: [backend inspector](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/backends.py),
[browser deadlines](../../apps/presenter-ui/src/adapters/local/LocalPresenterReadAdapter.ts),
[availability projection](../../apps/presenter-ui/src/features/service-team/useBackendObservation.ts).

Existing timing behavior is intentional unless qualified otherwise:

| Boundary | Current timing / meaning |
| --- | --- |
| Local controller/assignment snapshot | Ten seconds after a completed read; focus/visibility return and explicit refresh also reconcile. Eight-second request timeout. It is not a guest-health probe. |
| Cloud software | Single flight; pending interval 2/4/8/10 seconds, idle ten seconds after completion. A slow current read becomes STALE after 15 seconds; browser timeout is 65 seconds. No offline state is invented from timeout. |
| Backend cards/dialogs | Shared per-team observer; five seconds after a completed attempt, 15-second aggregate timeout. Backend reachability is not vehicle ingress. See L1. |
| Function report | Producer change coalescing at minimum five seconds, unchanged heartbeat 30 seconds, source freshness at most 90 seconds. This is a recent service observation, not instantaneous vehicle telemetry. |
| Cloud resources | Ten seconds after a completed read while the Resources dialog is visible; 65-second request timeout. Sample time and API read time are displayed separately. |
| Operation receipts | Session poll every second while active, otherwise five seconds. Completion is an operation receipt, not a product/qualification result. |
| Native telemetry | Gateway monitor output every 500 ms; advancing-frame freshness and native reader expiry protect against frozen data. The native view expires after five seconds without reader output. |

Thus **Backend Input: Receiving** and **native advisory: Unavailable** can
temporarily coexist legitimately: they have different producers, evidence and
freshness rules. Making every surface green at the same time is not an
acceptable fix. F1/F4 improve the explanation without changing these rules.

## Optional presentation improvements — separate from defects

| ID | Observation | Direction / boundary |
| --- | --- | --- |
| O1 / previous R6 | The global Demo Story may ask to open Brake backend while on the Tire page. | Label **Next in the demo: Brake result**. Routing is intentional global sequencing, not a wrong backend. |
| O2 / previous R7 | Finish returns to No controller / Trace 0 after session cleanup. | A short completion acknowledgement would reassure the operator. Do not retain deleted telemetry or create a new permanent run dossier. |
| O3 / previous R8 | The confirmed no-controller state contains repeated Waiting for service / Not reported / Not confirmed; popup subtitle still says Current Test · observed data. | Distinguish **not created yet** from an existing target whose observations failed. Architecture slots should stay visible. Live browser confirmed this state. |
| O4 / previous R9 | The score meter accessibility label is **Synthetic condition score** while visible text says Demo model estimates from vehicle data. | Use a consistent model-estimate label. This is not evidence that synthetic input was actually used. |
| O5 | Resource samples remain separated internally by node/service/Subject/index/partition, but service-instance cards omit Subject and usually node from visible identity. | Multi-Subject/node rows can look identical. Show enough exact scope to distinguish them; do not sum them or elect a current instance. Current one-Subject-per-team demo does not itself prove this ambiguity live. |
| O6 | Assessment/advisory record detail mainly shows message type, quality/confidence and provenance; the actual band/score/recommendation often requires expanding raw JSON. | Add result-type-specific human-readable detail using existing fields, without computing a new diagnosis. |
| O7 | Native KUKSA / real service → real backend explanatory text appears even before a candidate or Test exists. | Label this as the configured data path, not evidence of a connection. Actual Input/Activity must continue to require observations. |

The existing browser correctly announces that a newer UI build is available.
Old-tab text must not be reported as a regression in the rebuilt source.
Factory .35 being the initial selector in a fresh tab, while another tab had
selected .36, is local selection state; it is not proof of a wrong installed
image. Neither selection establishes live qualification.

## Surface-to-authority coverage

| Surface | Actual authority and audit conclusion |
| --- | --- |
| Current vehicle header | Accepted source assignment; does not claim Internet/Cloud Online. Read failure becomes unavailable. No incorrect connectivity inference found. |
| Vehicle / Aos Cloud status | Exact scoped Cloud Unit connectivity; CONNECTED, ONLINE, OFFLINE remain distinct. HTTP failure retains stale evidence instead of manufacturing Offline. |
| Installed software counts | Cloud installed rows, not prepared/pending candidates; service IDs deduplicated across Subjects. Missing/partial inventory cannot establish no updates. F2 concerns the inconsistent component subview. |
| Architecture service/VDP slots | Installed release comes from Cloud. VDP profile requires exact package/installation evidence; unknown profile is not inferred from release number. Empty vs unobserved remains distinct. |
| Architecture wires/colors | Structural association and Cloud connectivity, not measured packet flow. No service-wire traffic claim or live-ingress animation found. |
| AosCore / Factory | Image/architecture explanation, not a live process-health claim. Factory selection is disabled when a controller exists. |
| Platform authoring | Preparation/publication receipts are separate from Cloud installation. READY publication before Provision is allowed. Safe Stop guidance does not claim automatic installation success. F2 remains. |
| Brake/Tire authoring | Candidate profile and release differ from installed/running reports. First Deploy assigns a Subject; later versions need no extra Deploy or Safe Stop. Runtime details have F3/F4. |
| Package details | Authoring metadata, not installed evidence. ARM64, minInstances 1 and P7D are displayed package conventions; no resource-use/runtime proof is claimed. |
| Cloud component details | Installed/pending/update facts; process explicitly not reported by Cloud. Error text retained. Pending version absence needs F2. |
| Cloud service details | Exact installed/pending releases and per-instance reported state, with stale qualification. Numeric error omission and report-time wording need F3/F4. |
| Compatibility | Brake V1/V2/V3 require corresponding-or-later VDP; Tire V1 requires VDP V3. This is software compatibility, not input readiness. |
| Resources | CPU DMIPS, zero preserved, missing values not zero, unverified units not silently converted, controller/instance samples not summed. F5 and O5 remain. |
| Backend Overview | Exact Unit/service/Subject/index/release binding; current function and product result are distinct. F1/F7 and L2 remain. |
| Backend Records | Bounded retained receipt history, including earlier releases; not an all-time record count and not current-release proof. Explicit mock-history switch stays separate. |
| Brake V1 window | Actual retained samples/phases; recording completeness and durable chunk delivery are separated. No invented score/interpolation. F6 remains. |
| Function conflict / ambiguity | Wrong scope, malformed report, conflict, future/old source time and ambiguous native instances cannot establish fresh green. |
| Backend Reset | PENDING is not success; matched Gateway CLEAR establishes completion. Failure/expiry remains uncertain, history survives, historical reset from another release does not reset the current release. |
| Advisory | Brake V3 and Tire V1 support advisory. Backend result or service ACK is not the current driver warning; native Gateway lease/status remains authoritative. |
| Demo Story | Uses installed profiles, active-instance reports and exact-release backend proof. Software story complete explicitly asks to verify native advisory separately; it is not full E2E qualification. O1 remains. |
| Session | Continuous lifecycle: Safe Stop for pause; Finish before shutdown. Park/Resume not offered. Cloud selection is a separate explicit operation; certificate read is not API/SP access proof. |
| Confirmation / Trace | Named operation, actor/target and actual receipts; lost submission is reconciled rather than retried. Uncertain overlap blocks mutation. O2 concerns the post-cleanup acknowledgement, not missing retirement execution. |
| Native control / Return to road | Mode acknowledgement and physical telemetry are separate. Current source reconciles confirmed terminal maneuver receipts; uncertain output cannot claim a successful placement/mode. Native live UI not requalified here. |
| Native Dashboard/Vehicle/Data | Existing VISS/Gateway signals only; stale input dims values and invalidates motion/advisory claims. STOPPED is physical motion, not component-update authorization. |
| External network switch | Owned filter ON/OFF, with its own stale/unknown handling. It is not Aos Cloud connectivity. Cloud Offline may be observed later. |

## Normal differences that must not be “fixed” into false agreement

- A service can be installed/running without receiving valid KUKSA input.
- Input can arrive while Brake waits for a qualifying braking episode.
- V1 can produce an incomplete recording and deliver every retained chunk.
- A backend can remain reachable and return history while external vehicle
  networking is off. That does not prove continued vehicle ingress.
- V2→V3 can preserve model state and produce a valid local advisory before
  a new current-release assessment is received by the backend.
- Backend assessment, producer-observed advisory ACK and active driver warning
  are different facts. Reset CLEAR is not a healthy-vehicle assessment.
- Source time, backend receipt time, Cloud API read time and operator action
  completion time must stay distinct.

## Verification performed in this audit

| Gate | Result and interpretation |
| --- | --- |
| Existing Presenter unit suite | **244/244 pass**, 23 files. Passing existing tests does not cover the new findings. |
| Presenter TypeScript check | Pass. |
| Additional isolated characterization | **6/6 pass**: pending-without-version, per-instance error-code omission, retained-result card with current binding, the same with stale binding, missing usedDisk/current disk, one-shot window detail. These tests assert/reproduce the present discrepancy; they are **not acceptance tests proving it fixed**. Temporary harness only, outside the repository. |
| Native confirmed-scene-mode projection | **1/1 pass**, executes the production pure Swift projection without launching CARLA/native UI. |
| Current-build browser read-only checks | Vehicle, Platform, Brake, Tire, backend empty detail, Cloud Software/Resources, Session Lifecycle/Cloud/Test setup. No preparation/publication/reset/Finish action executed. |
| Live active-vehicle transitions | Not executed: no active Test. Prior .36 evidence is historical and explicitly distinguished. |
| Browser responsive/layout regression | Not rerun in this audit. The prior correction record has 21 fixture-browser cases; no new claim of full visual/viewport acceptance is made. |

The earlier R1 and R3–R5 source fixes remain locally tested, not newly deployed
by this audit. R2's historical source-order root cause is still unresolved;
new diagnostic categories are not a proven root-cause fix. Bare guest reboot
remains a separate engineering check, not an added demo lifecycle requirement.

## Recommended next order — requires selection

1. Correct F1/F2 with paired card/dialog regressions for stale binding,
   unchanged history, delayed receipt, status-only pending and failure states.
2. Correct F3–F7 using the existing evidence fields/read endpoints. Add exact
   scope labels where needed; retain the accepted layout and flow.
3. Qualify L1/L2 with selective endpoint delay/failure tests before changing
   scheduling or independent-resource presentation. Do not loosen validation.
4. Select O1–O7 separately; previous R6–R9 are not silently included.
5. Then qualify the same labels in a real version/reset/offline cycle and in
   the native windows. New service/VDP releases and any necessary image work
   follow their existing approval and qualification sequence.

Only this audit document was added to the project in this pass. Existing dirty
changes, runtime state, Factory artifacts and the user's loaded tab were preserved.
