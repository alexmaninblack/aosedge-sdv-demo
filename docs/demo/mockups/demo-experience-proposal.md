<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

Review package: [Mockup 2.6 — agreed Studio B flow](aosedge-demo-interaction-mockup-2-6.html),
[action audit](../../research/demo-studio-action-audit.md) and
[proposed delivery plan](../../planning/active/demo-studio-delivery-plan.md).

# AosEdge: from an operations panel to a demonstration of vehicle evolution

Discussion proposal · 8 September 2026. Decision and mockup review update ·
9 September 2026. This is a working UX proposal, not a new normative
specification. Q01–Q14 and M01–M08 are accepted in the
[delivery plan](../../planning/active/demo-studio-delivery-plan.md); Mockup 2.6
now simulates those decisions for user review. Statements below about unchanged
mockup HTML describe the earlier questionnaire phase. Current authorization is
mockup-only: no application implementation or live operation. Visual approval
of 2.6 comes before the comprehensive integration audit and implementation.

## Current authority

This proposal records design exploration. For current Test behavior, its older
recommendations are superseded where conflicting by [UI-STUDIO-026](aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract)
and the reconciled delivery plan. Warehouse publication before Provision is
allowed; foreground operations may serialize; expanded logs/errors are deferred.

## 1. What the demo demonstrates

The central subject is a vehicle whose architecture supports new capabilities after manufacture, rather than a sequence of update commands. Factory firmware and vehicle identity persist while the Platform, Brake and Tire teams release their software independently. Aos Cloud executes authorized operations. Behavior is demonstrated in the vehicle and in the corresponding backend.

Native Driving Control + Telemetry improves the target UX; it is not a deviation to reverse. CARLA remains a separate native window. Production is a required part of the target story. It follows completion of Test integration and remains in the design.

[Q04a/M01 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q04a-accepted-test-scope-and-production-presentation): the current run creates only one Test VM. Production remains visible in the target selection, disabled and labelled **Deferred**; it does not cause another VM to be created or started. Existing Production resources remain untouched and CLI production/all capabilities remain available for separately scoped work. [Q04b](../../planning/active/demo-studio-delivery-plan.md#q04b-accepted-preparation-modes) separately accepts the two explicit preparation modes below.

## 2. Findings in the project

| Observation | Implication for the new UX |
| --- | --- |
| Mockup 2.4 shows three VDP cards with five expanded stages each, repeating Current Vehicle, product state, roles and explanations. | The audience struggles to connect an action with a change in the vehicle. Compress the repeated process without removing its meaning. |
| LocalLifecyclePage combines Prepare demo, two-VM state, engineering steps, access, stop and reset. | Separate audience and operator concerns. Do not require the audience to understand SSH, DNS, overlays and access setup. |
| LocalPlatformControls contains prepare / inspect / unpack / sign / verify / upload / cloud-status / approve. | This is an engineering toolbox, not a mandatory sequence. A matching Unit in a validation set receives delivery after upload without batch approval, as clarified by the user after discussion with the Platform Team on 2026-09-08. On stage, retain publication and delivery observation. |
| Interaction Specification 2.5 still describes Terminal, separate lower windows and old subtitles. | Incorporate the accepted native improvements and simplified header into the current interaction contract. |
| current-baseline.md and the M0 scenario section still refer to `.21`, while a newer release checkpoint describes `.31` and Test transitions through `15.0.0/v3`. | Do not use the old baseline page as the current UI source. Distinguish target design, current checkpoint and historical evidence. |
| The native plan and checkpoint explicitly leave advisory, independent consumer proof and Production FOTA unfinished. | Do not show successful advisory merely because v3 is installed, or present target chapters as available live capabilities. |

Basis: the supplied [mockup](aosedge-demo-interaction-mockup-2-4.html), [walkthrough](../aosedge-demo-walkthrough.md), [interaction specification](aosedge-demo-interaction-specification.md), [LocalLifecyclePage](../../../apps/presenter-ui/src/features/global-lifecycle/LocalLifecyclePage.tsx), [LocalPlatformControls](../../../apps/presenter-ui/src/features/platform-team/LocalPlatformControls.tsx), [native plan](../../planning/active/native-demo-desktop.md), and [current checkpoint](../../qualification/democtl-release-checkpoint.md).

## 3. Proposed screen: one scene with different areas of focus

Real CARLA and the native driving/telemetry application stay on the left. The right side shows vehicle architecture, the current release and one primary action. This is a composition of separate windows, not a CARLA video stream embedded in the browser.

The map has fixed participants: Car / Sensors → Vehicle Gateway → Domain Controller, with Aos Cloud and the corresponding function backends above the vehicle. The Domain Controller contains Factory Firmware, a VDP slot and planned Brake/Tire slots. There is no separate Local Vehicle Data object. An empty slot means “not installed,” not “broken.”

For the full scenario, all participants are present from the start. Later steps change states, outlines and connections. Platform/Brake/Tire switch focus and actions, but neither create new architectural entities nor change Current Vehicle. If a shorter presentation is needed, its scope is selected before the start rather than expanding unexpectedly during the demo.

Capability names should take precedence over technical release numbers:

- VDP v1: basic braking signals.
- VDP v2: additional inputs for local analytics.
- VDP v3: tire data and the advisory contract.

Show the Cloud release number as secondary detail. The mapping from v1/v2/v3 profile to exact version must come from the prepared manifest, not a guess based on SemVer. Counts of 7/15/23 can describe the declared contract, but do not automatically prove data availability to a consumer.

I recommend a compact version selector and one expanded action context instead of three long vertical checklists. Every version remains inspectable; narrative order does not become an artificial prohibition on operations. This is a deliberate change to UI-INT-004/021 and requires agreement.

## 4. Two modes of the same tool

### Backstage: Operator

Factory image selection, restoration of an existing environment or creation of a new one, access setup, prepared releases, technical results and recovery of interrupted operations. Password entry is native/Keychain only. Reopening the UI observes the existing operation instead of starting another one.

Accepted [Q04b preparation modes](../../planning/active/demo-studio-delivery-plan.md#q04b-accepted-preparation-modes): **Full story** presents Create → local connection → Platform v1 preparation/publication → Provision as operator-led chapters; **Quick preparation** composes the same operations from one explicit operator start, reaching a provisioned/Online Test with its local connection, stationary in Manual before the first drive and Safe Stop. It labels completed chapters as completed and shows the actual VDP state, not a fabricated installation result. Neither opening the page nor selecting a mode starts work. Both modes use the same Demo Control core.

[Q10a accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q10a-accepted-backend-preparation) extends the shared preparation: composed Create in Full story and Quick preparation prepare/reuse both independent Brake and Tire backend applications through Demo Control. Bind queries to the current Test identity once known; before that, show unavailable vehicle context rather than an old Unit's data. Backend views are accessible before vehicle service deployment, with source-backed no-service/no-results states. Opening a view is read-only. Backend startup neither publishes nor deploys services, and does not change the low-level disk-only create command. Q10b below settles dashboard presentation; stop/resume/retention remain Q12/Q13. Implementation is pending.

Session completion has two modes:

- **Park demo** — [Q12a accepted, option A](../../planning/active/demo-studio-delivery-plan.md#q12a-accepted-full-park-resume): gracefully stop owned VM, CARLA/Gateway, native surfaces and backend applications; retain working disks, Cloud identity/assignments, product records and operation state. No deprovision/delete, history clearing, backups or separate warm Pause/Continue. **Resume** starts that same environment, restores applicable connections and observes actual state without Create/provision/publication replay. Q12b below settles conflict/recovery policy; integration remains pending.
- **Finish demo / Retire** — [Q13a accepted, option A](../../planning/active/demo-studio-delivery-plan.md#q13-clean-cycle-cleanup-proposal): use shared Demo Control to deprovision/delete the owned Test Unit and clean its working environment, reset owned demo bindings and restore only recorded temporary Cloud-setting changes. Keep the dedicated Subject, source image, published releases and permanent infrastructure. **New cycle** offers/completes this same cleanup if needed before fresh Create. Park remains the separate preserve/resume choice. [Q13b accepted](../../planning/active/demo-studio-delivery-plan.md#q13b-accepted-clean-run-release-continuity): remove owned ordinary product/run history without archives or automatic reports, but retain release-number continuity separately for VDP, Brake and Tire. No cleanup on page open; implementation is pending.

Completion does not start the next run. Both modes use Demo Control; no second set of UI scripts is introduced.

**Automatic release numbering — accepted Q13b clarification:** in both CLI and UI, the operator chooses the product and content profile (v1/v2/v3). Shared Demo Control assigns and preserves the actual release number, independently for VDP, Brake and Tire. The number is read-only operator information, not an input. Preparation reserves it before packaging/signing; publication and recovery reuse it. Refreshing a view does not consume a number or publish anything. The current explicit-version CLI needs adaptation; no implementation or mockup HTML is changed by this decision.

[Q12b accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q12b-accepted-prompt-park-refusal): if relevant unfinished or uncertain changes conflict with Park, return the actual reason promptly without stopping resources or queuing a future Park. The operator requests Park again after resolution. Background status reads alone are not a conflict. No forced installation interruption, automatic Safe Stop or invented cancellation. After unexpected interruption, reconcile the existing journal and authoritative outcomes before any repeat; do not replay completed publication/provisioning or replace identities. Source/race/partial-outcome mappings remain audit work, not implementation already completed.

The [Q13a documentation review](../../planning/active/demo-studio-delivery-plan.md#q13a-subject-documentation-review) led to accepted Subject retention and the [accepted common cleanup policy](../../planning/active/demo-studio-delivery-plan.md#q13-clean-cycle-cleanup-proposal). Keep the dedicated Subject across runs while resetting owned run bindings, without touching factory/platform Subjects. Q13b retains only release continuity from ordinary completed runs, not product history: the next v1 profile receives a new higher release, independently for each software identity. The exact numbering store, uncertain-upload recovery, identity/type/state and API ordering still require the final audit. No live cleanup or implementation is authorized by these review decisions.

### On stage: show the action and its result

[Q14 accepted, option A](../../planning/active/demo-studio-delivery-plan.md#q14-accepted-cli-then-visual-ui-repeat): after the comprehensive pre-implementation audit and authorized implementation, run the full story through `democtl`, retire that run, then repeat through UI with the user's visual control. Both cycles use the same immutable factory image/SHA and automatically assigned new releases. This is the verification plan, not authorization to execute live actions during review.

| Chapter | Presenter action | Audience takeaway |
| --- | --- | --- |
| Create | Select prepared firmware, create and start the controller. | The vehicle leaves manufacturing with its base firmware already running. |
| Initial local connection | After Create and before Provision, connect CARLA/Gateway; begin stationary in Manual without automatic Safe Stop. | The vehicle is locally connected to its factory controller before Cloud registration. |
| Platform v1 publication | Visibly prepare, sign and upload a fresh release carrying VDP v1 before Provision. | The Platform Team prepares software independently while the vehicle is manufactured. |
| Provision | Register the vehicle and select Test Fleet. | The same vehicle gains a managed Cloud identity. |
| First VDP | Show assigned v1, driving, Safe Stop and the installation result. | A capability is added without replacing firmware or vehicle identity. |
| VDP v2/v3 | Publish a prepared candidate, observe automatic delivery to the matching Test Unit in a validation set, perform Safe Stop and check the result. Batch approval is not a delivery prerequisite. | An independent release extends the platform; Cloud does not control braking. |
| Brake | Capture a bounded window → local analysis → advisory. | The function team creates driver value on top of the platform. |
| Tire | Release a separate service with its own backend. | A shared platform does not imply a combined product or shared lifecycle. |
| Production | After accepting the Test result, switch the vehicle and separately authorize rollout of the same artifact. | A verified release reaches operation without rebuilding; Production is not a second Test. |
| Offline / isolation | Disconnect external connectivity or run an agreed quota proof. | Local behavior and isolation are confirmed by their own evidence sources. |

The Production pass repeats within the relevant independent release loops. It must not become one shared “release everything to Production” button. A combined capability milestone is acceptable; an atomic group release is not.

## 5. Important correction to the first cycle

In the current [DemoPreparation](../../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/demo_preparation.py), a fresh v1 is prepared, signed, uploaded and approved **before provisioning**. This prevents a new run from beginning with the previous v3. Preparation currently creates both VM roles even when only Test is demonstrated.

The earlier recommendation to always stage v1 invisibly is superseded by the [accepted M02 decision](../../planning/active/demo-studio-delivery-plan.md#m02-accepted-create-and-platform-publication) for **Full story**. Create starts the factory controller; [Q03](../../planning/active/demo-studio-delivery-plan.md#q03-accepted-initial-vehicle-connection) establishes the CARLA/Gateway connection with the vehicle stationary in Manual, without automatic Safe Stop; the Platform Team visibly prepares, signs and publishes fresh VDP v1; then the running, locally connected controller is provisioned and receives the eligible update. Explicitly selected **Quick preparation** may compose those same stages under [Q04b](../../planning/active/demo-studio-delivery-plan.md#q04b-accepted-preparation-modes), honestly showing their completion. Provisioning must not introduce an artificial detach/reconnect. Keep receipt separate from Safe Stop installation. Repeat the visible publication/delivery/install story with v2 and v3. Validation batch approval is not a Test-delivery gate. An already completed publication must not be reenacted as a new action.

User clarification dated 2026-09-08, confirmed by the user with the Platform Team: if a Unit belongs to a validation set and matches the update, Cloud can start delivery immediately after upload without validation batch approval. Publication can therefore already affect Test; it is not a harmless intermediate stage awaiting approval. This does not establish Production rules or make batches irrelevant to other tasks. The older interactive sketch `demo-experience-scene.html`, which requires Authorize Test deployment, is outdated in this respect. This document records the corrected flow. This discussion has not changed working commands or the accepted project specification.

Our earlier “after Provision the slot must be empty and nothing assigned” sketch was too categorical: Cloud may already assign staged v1. Show installed and pending separately. If the product goal specifically requires an empty G0 with no assigned update, first agree on a supported Cloud-targeting mode; UI alone cannot provide it.

Test Fleet / Production Fleet are audience-friendly role names, not an instruction to create new Cloud Fleets. Details must retain exact bindings to existing Unit Sets. The picker does not imply arbitrary role changes on an already created VM; the current role is initialized before provisioning.

[Q09a/M05 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q09a-accepted-service-publication-and-assignment): first assignment of a Brake/Tire service to the current vehicle uses explicit **Publish service** under its owning SP, then **Deploy to Test** under OEM authority, through shared Demo Control. For an already assigned service identity, use **Publish update** and observe delivery/runtime; no second version-specific Deploy or validation-batch approval gate. Assignment selects a service identity, not a version. Subject scope is settled by Q09b below; completion/readiness is settled by Q09c. Mockup and implementation changes have not been made.

[Q09b accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q09b-accepted-shared-test-subject): use one dedicated demo Subject for the current Test vehicle, with independent Brake and Tire assignments managed by OEM through Demo Control. Each team retains its own SP publication identity; deploying one service neither deploys nor alters the other. The Subject remains in technical Details, not a new actor on the main scene. Do not reuse unrelated/shared Subjects or include Production. Cross-run retention/deletion remains Q13; no live objects or permissions have changed.

[Q09c accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q09c-accepted-service-update-completion): repeating a service profile retains its identity/SP and uses a new monotonically increasing release, independently for Brake and Tire. Cloud confirmation of the expected version installed with its required instances running completes the technical update and permits the next release. Functional readiness, a persisted product result and applicable advisory delivery are separate observations and remain required for E2E. A service may run while awaiting capabilities/data; no result is fabricated and no update operation waits for a future braking event after technical completion. Missing/stale runtime evidence, zero/old instances or unresolved errors do not qualify as completion. Q10b below settles overview-first presentation; concrete functional mappings and integration remain pending.

### Accepted team-dashboard presentation

[Q10b accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q10b-accepted-overview-first-backend-dashboards): keep the existing backend-card navigation and right-hand panel. Each team dashboard begins with the Cloud-reported service version/state, its latest persisted product result and its backend-recorded advisory. A compact history below opens available inputs, event correlation, event-time software provenance and capture/receipt times on selection. Whole-controller monitoring remains available through the shared Cloud view. Do not treat a read error or stale/missing data as an empty or healthy result, infer versions from current inventory, or fabricate a product outcome after a timer/Safe Stop.

A backend advisory record does not prove delivery to the vehicle or acknowledgement by the driver. Actual in-car advisory display remains in native telemetry on the left. This accepts the overview-first presentation, not a new data path, implementation completion or retention policy. Q11 below settles the offline episode; cleanup remains Q13. Applications and mockup HTML remain unchanged.

### Accepted standalone offline episode

[Q11 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q11-accepted-standalone-offline-episode): after establishing the installed local functions, disable only the Test vehicle's external connectivity, demonstrate actual local operation/advisory with suitable inputs, restore connectivity and observe delayed product delivery. Keep CARLA/Gateway telemetry and the operator's Cloud/backend access available. Show the control outcome, Cloud Offline/Online and backend receipts as independently observed facts; preserve original event times and provenance. Do not create backend results, queue counts or immediate-drain success from the network toggle. Backend receipt, vehicle advisory display and driver acknowledgement remain distinct.

No new software release is required inside this main-story chapter. Q08a still permits publication while Offline; this narrative choice does not disable that capability or change native update behavior. Reconnect does not automatically republish, restart a VM or trigger Safe Stop. Fault coverage, local continuity and durable replay remain implementation/E2E work. No live state or mockup HTML changes at this review stage.

## 6. Status: less text without losing meaning

- [Q05/M04 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q05-accepted-factory-slots-and-versions): show selected Factory Firmware, VDP **Factory baseline** before OTA, and installed **VDP v1/v2/v3** with exact release secondary afterwards. Raw placeholder **0.0.0** and IDs belong in Details. Keep confirmed-absent Brake/Tire positions empty, but show **Unknown** for missing observations. Before Provision, image-described **Factory configuration** is not a Cloud observation; after registration, installed state comes from Cloud. Capability profiles require a verified release binding, not a guess from SemVer.
- No Cloud line means the vehicle is not provisioned yet. A solid line remains after provisioning: green + Online, red + Offline. Unknown is neutral, not a false Offline.
- A Presenter-side Cloud read failure is a separate source state. It does not switch the vehicle's external network or mark local telemetry Offline.
- [Q08a accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q08a-accepted-offline-publication): a provisioned vehicle being Offline does not block Platform publication when the operator has Cloud access and the agreed recipient/identity safeguards hold. Publication is not a Unit-addressed send. Keep publication result, connectivity and delivery/install observations separate; observe the outcome after reconnect without promising immediate delivery or automatically uploading again. The democtl guard change remains pending.
- VDP shows both the previous installed version and its assigned successor. Upload, assignment and delivery do not themselves change the displayed installed version; installation must be observed.
- [Q08b/M07 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q08b-accepted-one-outstanding-update): one outstanding update per software identity in the demo workflow. Preparing/signing the successor stays available; Publish waits for confirmed completion or resolution of the current error by returning a clear unavailable state, not by queuing a command. Independent Platform/Brake/Tire releases remain independent. For VDP, confirmed expected Cloud Installed closes this publication guard without a new Running-field requirement. This is a demo-tool policy, not a Cloud limitation or a promise of native cancellation/rollback. Implementation remains pending.
- [Q06 accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q06-accepted-cloud-runtime-evidence): investigate supported Cloud runtime sources first. If none is confirmed, Cloud **Installed** with runtime **Not reported** is acceptable for the first UI milestone. Not reported is missing evidence, not a failure or success assertion. Actual VDP operation still requires engineering democtl/E2E proof, kept separate from the Cloud-only panel. Installed does not imply Running/Ready, and native Gateway telemetry does not prove the VDP consumer path; no hidden SSH from the panel.
- “FOTA is applied in Safe Stop” is a rule. The more specific claim “the runtime is currently waiting for Safe Stop” requires evidence of that reason. Otherwise, show Cloud Pending and prompt the presenter to use Safe Stop on the left.
- Show one short status and the nearest relevant action. Observation time, native status, batch ID, reasons and technical details are secondary.
- [Q07b accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q07b-accepted-cloud-logs-and-progress): provide the full Cloud-log workflow through UI and the same democtl operations. Logs lists existing records; a separate Request logs selects Unit/service and time range, followed by observed request status, viewing and download. Opening the panel does not start collection. Operation progress shows the confirmed stage and elapsed time; percentages require measured data. No timer-derived success or invented Pending reason. Implementation remains pending.

Platform currently reads Cloud on entry/re-entry and manually, without background Cloud polling. [Q07a accepted on 9 September 2026](../../planning/active/demo-studio-delivery-plan.md#q07a-accepted-cloud-observation-refresh) adds one shared bounded visible-panel observer through the existing democtl Cloud adapter: entry/post-action reads, pending delivery at 2 seconds backing off to 10, visible idle inventory at 10 seconds, and resource metrics only while the monitor is visible. Hidden tabs add no requests; navigating away does not cancel active work. Keep last-known data marked stale/source-unavailable on error, not false Offline/zero values. These are observation intervals, not command delays or device sampling guarantees. Implementation remains pending; no repeated full audits, VM reads, unpacking or hashing belong in this observer.

## 7. What stays and what needs agreement before implementation

Preserve control through democtl, team independence, separate OEM Release Authority, one Current Vehicle, Safe Stop in the vehicle runtime, an unchanged Test → Production artifact, boundaries between Cloud/Gateway/function backends, and confirmation of external and destructive actions.

Items for agreement: a persistent map instead of lists, compact version selection, the operator panel, an honest staged-v1 narrative, audience-friendly Fleet names, a shared Cloud observer, and temporarily unavailable Product/Production chapters while preserving the full target scenario.

After selecting the UX, record changes in the existing interaction specification, update the walkthrough, add acceptance cases to the UI traceability register and synchronize the Demo Control/native desktop plan. Do not create a parallel “authoritative specification.”

The immediate implementation sequence is the map and lifecycle, then the new Platform UX over existing actions, followed by the complete Brake/advisory/Tire chain on Test. Production, offline backend replay and isolation follow with agreed evidence. Do not revert native telemetry or rebuild the Factory image just to redesign the UX.
