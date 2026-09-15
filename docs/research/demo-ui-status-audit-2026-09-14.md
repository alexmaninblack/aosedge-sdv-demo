<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo UI: status, consistency and latency audit

Date: 14 September 2026. Status: **Audit complete; corrections not implemented.**

Historical audit snapshot. The subsequently authorized implementation and
verification are recorded separately in the
[correction receipt](../qualification/ui-status-corrections-2026-09-14.md);
the findings and measurements below describe the pre-correction state.

## Conclusion

The normal flow passes the existing tests, but the UI is not yet consistent in
all error, transition and recovery states. The most consequential problems are
version-unbound Running indicators, outdated details labelled as current,
hidden installation failures, and recovery paths that can leave Finish
unavailable. Populated backend records are clipped. An already-open ordinary
browser can also continue running an older frontend build without warning.

This is an audit of the actual Studio implementation, not another approval of
the mockup. No application source, factory image, VM, component, service,
Cloud configuration or deployment was changed. No new live demo cycle was
started. Session inspection performed its existing local read-only certificate
operation; it did not select a different certificate or Cloud.

## Evidence and limits

- Repository HEAD: `52dd2c0bedbad43944ee05e2569e51d7306d9774`, plus the existing
  uncommitted implementation. This is not a clean-commit qualification.
- Inspected the running Presenter on `http://127.0.0.1:18080/`, including Vehicle,
  Platform, Brake, Tire, backend, Software, Resources, Trace and Session.
- Test had already been retired. The real endpoint returned
  `UNAVAILABLE / TEST_CLOUD_BINDING_NOT_OBSERVED`, `bindingKey=none:none`.
  Native driving/telemetry were not restarted for this audit; Production was
  untouched. Their current-code review is distinguished from live visual proof.
- Existing frontend suite: **111 unit tests passed**, 1.87 seconds.
- Existing browser suite: **84 tests passed**, 24.7 seconds, isolated API
  fixtures on a separate development port. This includes three Studio layout
  sizes, service transitions, stale observations and retirement continuations.
  Some tests exercise retained legacy fixtures, not the live Studio renderer.
- Presenter backend suite: **33 tests passed**, 6.211 seconds, mocked operations
  and temporary local servers only.
- Additional diagnostic cases: **7 isolated reproductions passed**, plus
  **1 real-browser layout reproduction**. These tests assert the problematic
  current behaviour; their passing does not mean the defects are fixed.
- Temporary diagnostic files are outside the repository under
  `/private/tmp/demo-ui-status-audit*`. They are not production helpers.
- Initial test harness attempts hit sandbox/module-path/test-directory errors;
  corrected harness runs produced the results above. They were not application
  failures and did not initiate a live operation.
- Browser console: no warning/error entries during the inspected navigation.
- Full running native composition, live state-transition latency and fresh
  Cloud authentication latency were **not remeasured** in this retired state.
  The [preceding real cycle](../qualification/rabbitmq-full-cycle-2026-09-14.md)
  remains separate evidence, not a substitute for this audit's UI cases.

### Build identity

The already-open browser was executing `index-D7R602mT.js`; the current server
entry referenced `index-1o55Fq3H.js`. Both used `index-BsHhEtp2.css`.
The served local entry SHA-256 was
`6f34b9d5e669ea82868f66f0d9e64c8d216bd1372204a51342b7d47c61ede952`.
The newer built asset contains the current debug-only guest-configuration
wording, while the open page displayed its predecessor. This is a verified
loaded-page mismatch, not a claim that the current source was unbuilt.

## Surface coverage

| Surface | Authority / expected meaning | Audit coverage and result |
|---|---|---|
| Shared header | Accepted local vehicle assignment, not Cloud connectivity | Live unassigned state and existing selection tests pass; separate native webviews can observe changes at different times. |
| Vehicle architecture | Factory selection/local lifecycle; installed slots from Cloud | Live empty state and populated fixtures checked; empty/unavailable copy is ambiguous; details can fall behind cards. |
| Platform | Prepared, published, pending and Cloud-installed VDP, never inferred process readiness | Entry refresh and publication separation work; failure reasons and guide selection need correction. |
| Brake and Tire | SP publication, first Subject assignment, subsequent release replacement and instance runtime | Normal fixtures pass; Running is not bound to the exact instance version, and several Cloud error fields are dropped by presentation. |
| Product backends | Real backend receipts from synthetic service inputs, scoped to Test | Explicit synthetic labelling and identity validation work; fallback to old release data, partial-read wording and populated lists need correction. |
| Cloud Software | Components/services/instances; missing is not absent | Normal inventory works; component absence/error explanations and section-level freshness are incomplete. |
| Cloud Resources | Cloud samples, CPU in DMIPS; sample time distinct from read time | Zero and unknown units preserved; top-level monitoring failure can look like an empty successful read. |
| Details | Current selected entity or explicitly dated snapshot | Reproduced old values remaining in an open modal while the main card changes. |
| Session / Cloud | Selected Cloud and local OEM certificate; explicit change | Local read works; ordinary browser build mismatch observed; job-derived selected-domain precedence and missing SP access explanation remain. |
| Progress / Trace / confirmations | Actual command outcome, exact current run, no replay | Duplicate-submission protection works; current-run trace can show a prior run, and recovery/receipt-limit paths are incomplete. |
| Finish / Park / Resume | Distinct destructive retirement versus retained local state | Ordinary/partial retirement fixtures pass; uncertainty and session-capacity guards still have no operator-only exit. |
| Native control / telemetry | Driving mode/vehicle measurements/local external link, no Cloud inference | Source and preceding-cycle evidence only; stale/action wording concerns below. No new live native fault injection. |

## Findings

P1 means correct before relying on the affected transition/recovery in another
operator-only demo. P2 means a presentation, diagnosability or latency issue.
“Reproduced” uses the actual renderer with controlled data unless explicitly
marked “live”. Source-only risks are not claimed to have occurred in this run.

### F01 — P1: Running can refer to the wrong instance version

**Reproduced.** The service candidate and installed version were `7.0.0`, but
the only active instance was `6.0.0`. The release ribbon still marked Running
complete. `countInstances` filters `run_state=active` but does not compare the
instance version or require a current instance section. Failed/stopped instances
are already excluded; the problem is narrower than counting all instances.

Source: [StudioWorkspace](../../apps/presenter-ui/src/app/StudioWorkspace.tsx),
lines 157 and 183–187. Fix direction: derive version-specific runtime evidence
once and reuse it for ribbon, card and details; distinguish unknown, starting,
active and failed without adding guest reads.

### F02 — P1: open details can show outdated values as current

**Reproduced.** With details open at VDP `1.0.0`, a refresh changed the map to
`2.0.0`, but the modal retained `1.0.0` without a last-known label. Selection
stores the whole row; freshness comes from the newer global observation.
Service and package details use the same captured-row pattern. A modal can
also outlive a run/binding change because selection is not keyed to that identity.

Source: StudioWorkspace lines 48, 175–178 and 222–225; [StudioReadViews](../../apps/presenter-ui/src/app/StudioReadViews.tsx)
lines 26–30. Store a stable entity/binding identity and resolve the latest row,
or explicitly freeze and date the entire snapshot. Clear it when scope changes.

### F03 — P1: VDP failures can be presented as a Safe Stop wait

**Reproduced omission; guide branch confirmed in source.** Cloud projection
preserves `pending_component_error`, but even component details omit it. The
main guide checks only whether a pending version exists and recommends Safe
Stop; a failed update with that version takes the same branch. Platform copy
also calls a failed publication “Cloud processing” followed by its error stage.

Sources: [cloud_observation](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/cloud_observation.py)
lines 99–108; StudioWorkspace lines 125, 191–193; StudioReadViews lines 26–30.
Display the reported failure separately from Pending and do not prescribe
Safe Stop as a remedy for a certificate/download/installation error. Retain
Finish and bounded diagnosis; do not invent an automatic retry.

### F04 — P1: service pending/error information is incomplete

**Reproduced.** A service-level `error_message` and a pending-version ID/status
without an expanded version object were absent from the UI. Projection already
retains those fields, plus error codes. Presentation only recognises a nested
pending-version object and instance error text. This also affects pending
polling detection and button gating.

Sources: cloud_observation lines 138–151; [platformObservation](../../apps/presenter-ui/src/domain/platformObservation.ts);
StudioReadViews lines 10–23; StudioWorkspace lines 95 and 195–202;
[visibleCloudObserver](../../apps/presenter-ui/src/domain/visibleCloudObserver.ts).
Use the existing normalised fields for “Pending, version not yet reported”,
failure reason and exact installed/runtime state. Do not treat an unexpanded
pending object as proof that no update exists.

### F05 — P2: empty environment is described like an observation failure

**Live.** With no current Test, the header says “Cloud not current”, Platform
says “Not reported · last known”, the backend says “Stored mock messages ·
last known / Not observed”, and Software has a blank Components section.
The endpoint explicitly identifies the missing binding. Refreshing these
screens cannot create the missing controller or make historical data current.

Sources: StudioWorkspace lines 161, 193, 209 and 214; StudioReadViews;
[BackendEvidence](../../apps/presenter-ui/src/features/service-team/BackendEvidence.tsx).
Separate Not created, Not provisioned, Not yet reported, Last known and Read
failed. Reserve “last known” for data that actually exists. Preserve the
accepted header's assignment-only wording; put explanations inside panels.

### F06 — P2: failed monitoring read can look like a successful empty result

**Reproduced.** HTTP 200 containing the same Unit ID and
`monitoring={state:UNKNOWN, reason:HTTP_403, value:null}` produced a read time
and “No sample reported for this scope”, with no failure explanation. The
renderer checks transport/Unit identity but not the outer monitoring state.
Per-metric reasons work only when a metric object exists.

Source: StudioReadViews lines 34–70. Preserve the last successful samples and
their timestamps separately from the latest read failure; show the supplied
section reason instead of interpreting it as an empty dataset. Do not convert
an unavailable sample into zero or invented units.

### F07 — P2: backend result fallback hides the expected-release gap

**Reproduced.** With expected release `8.0.0` and only `7.0.0` records, Overview
showed the old result as the latest result without stating that `8.0.0` had
not reported. The displayed release number remains truthful, but its mismatch
with the service just installed is unexplained. The guide's proof callback
does require the expected version, so this is not evidence that it falsely
accepted the new release.

Separately, a structurally valid backend `PARTIAL` response can still show
“Observed <time>” rather than explaining failed readiness/mock-data sections.
The server preserves section state/HTTP status; the panel loses this context.

Sources: BackendEvidence lines 35–70; [backends](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/backends.py)
lines 24–55. Show current expected release and its result availability;
previous records belong to clearly labelled history. Preserve explicit
synthetic provenance and the separation from vehicle advisory.

### F08 — P2: freshness is not consistently attached to the displayed fact

**Reproduced/source.** During a hung refresh, an older observation remains
`CURRENT` while `loading=true`; footer text changes but green/current values
can remain. The isolated case held this state for 44 seconds from the first
read, with the second read still unresolved. Real browser timeout limits this
case; it is not a claim of an unlimited real fetch.

The UI also uses a single top-level read time even when software/resource
subsections retained older values. Instance lines lack their own last-known
qualifier. `stamp()` displays only time-of-day, making yesterday's value hard
to distinguish from today's. Cloud “last report” and live process health must
not be conflated, even when the API read itself succeeded.

Sources: visibleCloudObserver; [LocalPresenterReadAdapter](../../apps/presenter-ui/src/adapters/local/LocalPresenterReadAdapter.ts);
StudioReadViews lines 7, 16–20, 56–68. Use a common observation envelope with
source, binding, last-success time and latest read outcome; show age on the
relevant section. A modest demo-appropriate freshness policy is sufficient;
this is not a request for real-time scheduling or shorter safety windows.

### F09 — P2: refresh latency is composed from independent polling budgets

**Measured locally; slow-path risk confirmed in source.** See the timing table
below. Ordinary polling adds up to 10 seconds before a changed state is read.
Platform fetch times out at 35 seconds while the Unit worker can take 60 and
publication workers longer. The server waits for all selected readers before
returning the combined result. A slow SP/publication read can therefore delay
otherwise available Unit status. A returned publication failure does not
itself overwrite Online; the concern is latency, not state mapping.

The one-second server coalescing cache can also satisfy an immediate refresh
with the just-completed observation, including after an operation. Independent
header/right-panel webviews and ordinary tabs have separate local observers;
temporary disagreement is possible. No new live delay was injected.

Sources: LocalPresenterReadAdapter; visibleCloudObserver;
[PresenterControls](../../apps/presenter-ui/src/app/state/PresenterControls.tsx)
lines 40–67; [presenter.py](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter.py)
lines 98–119 and 232–252; [units.py](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/units.py)
line 72. Prefer post-action invalidation and independently deliverable
observations, with consistent deadlines, over extra VM checks or faster
unconditional polling of all endpoints.

### F10 — P1: uncertain outcomes have no complete operator-only recovery path

**Source-confirmed, not induced live.** `session.uncertain` or a lost submission
whose request ID cannot be reconciled blocks every command through the shared
controls, including Finish. Text says to reconcile native state, but no UI
action completes that reconciliation. Cloud GET refresh remains available;
it does not clear the operation uncertainty. Even native read commands that
the server permits under uncertainty are blocked by the common UI predicate.

Sources: PresenterControls lines 50–68 and 94–99; StudioWorkspace line 221;
[presenter_operations](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter_operations.py)
lines 192–195 and 275–284. Keep the no-replay guard. Provide a bounded
authoritative reconcile/resume path, or an explicit operator handoff explaining
what remains unresolved. Do not simply enable destructive action when its
previous outcome is unknown.

### F11 — P1: lifetime receipt limit can reject Finish after repeated demos

**Source-confirmed, not filled live.** The native session rejects every new
request after 128 receipts. No pruning/reset is applied on successful Test
retirement. Opening Session also creates a certificate-inspection receipt.
The UI counts only current-run jobs, so it can show Trace 0 while the lifetime
limit is approaching. Rejection becomes the generic “operation rejected or
another operation is running” message rather than the actual limit reason.

Sources: presenter_operations lines 180–210; CloudConnectionPanel lines 8–13;
LocalPresenterCommandAdapter lines 12–19. Compact only completed, reconciled
history; retain uncertain/idempotency evidence and capacity for recovery.
Expose a reason-specific error. Do not require an unexplained Presenter restart.

### F12 — P2: Current run Trace can display a previous run's last operation

**Live.** Trace 0 opened “Current run activity” containing “Finish demo ·
COMPLETED” from an earlier run. The list is run-filtered but its embedded
OperationProgress uses the last job of the entire native session. The same
unscoped last job may appear outside Trace if it was blocked/failed.

Sources: StudioWorkspace lines 72, 214–216; PresenterControls lines 120–130.
Give progress an explicit job/run scope. Historical session operations can
remain inspectable, but must not masquerade as activity of the current run.

### F13 — P2: browser tabs can silently remain on an obsolete UI build

**Live; asset IDs recorded above.** The ordinary browser has no client-state
build check. Native Presenter does have a guarded five-second paired-window
reload mechanism. This accounts for different wording between the open page
and the already-built current implementation.

Source: [PresenterWorkspace.swift](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/native/PresenterWorkspace.swift)
lines 70, 110–141; no matching browser-side client-state consumer.
Offer an idle-only “new UI version available” refresh in ordinary browsers,
preserving confirmations and uncertain submissions. This is not a Cloud retry.

### F14 — P1: populated backend Records are inaccessible below the fixed area

**Real-browser reproduction.** At 1512×982, with 20 valid scoped records,
`.studio-body` had 661 px available and 2069 px content height. Its overflow is
hidden, there is no paginated record control, and the last record extends
below the visible panel. The ordinary empty/profile viewport tests passed
because they do not populate this Records view.

Sources: BackendEvidence Records loop; [studio.css](../../apps/presenter-ui/src/shared/design-tokens/studio.css)
lines 35 and 67. Use fixed-height pagination or a compact drillable summary,
not whole-page scrolling. Extend the same bounded-content check to resource
groups, multiple instances and long errors; clipping of those other cases is
a coverage risk, not separately reproduced here.

### F15 — P2: disabled actions and wait messages do not explain the actual gate

**Live/source.** Several Prepare/Publish/Deploy/Park buttons have no adjacent
reason for being disabled. During an operation, the guide becomes generic
“Working…”; detailed native password prompts and Cloud waits live in Trace
or another window. Progress has no visible elapsed/phase budget; its last
intermediate progress line can remain under a terminal outcome.

Sources: StudioWorkspace lines 154, 190–203 and 218–221; PresenterControls
lines 120–130. Use one derived reason per action and concise stage-owned
messages, such as “Waiting for VM password in macOS” or “Waiting for Cloud
Offline”. Show elapsed time, not a fabricated percentage or completion ETA.
Opening Session need not masquerade as a demo mutation while its local
certificate read is in progress.

### F16 — P2: native control state and observation age need clearer semantics

**Source review only.** The external-link button displays its last ON/OFF value
without applying the 15-second age check used by its click handler. A click
on an old “Disconnect” label may merely refresh status. Polling is every five
seconds with a 15-second process budget. Bridge mode can also continue to say
“AUTOPILOT — VEHICLE DRIVING” while physical telemetry reports stopped; mode
selection is not proof of movement. Process termination is handled, but a
live stalled bridge has no equivalent displayed age check.

Sources: `carla-ego-runtime/tools/KeyboardControl.swift`, lines 116–119,
409–420 and 775–844. Show Active mode separately from physical movement and
make stale link readback visible before deciding the next button action.
Do not label the local packet filter as Cloud Online/Offline.

Positive boundary: native telemetry uses a monotonic five-second stale check,
the VISS producer checks both reception and advancing frames, and motion/
advisory cease to be current when data is stale. The native renderer does not
use the legacy `NOT ESTABLISHED`/Gateway stop string as its movement label.

### F17 — P2: Session's selected-domain display is based on historical jobs

**Source-confirmed risk.** A previous successful cloud-select result has
precedence over the selected domain returned by a newer certificate inspection.
If configuration changes through CLI while Presenter stays open, the UI can
continue showing the older selection. Current live inspection agreed on
`aoscloud.io`; no domain was changed to reproduce the risk.

Source: [CloudConnectionPanel](../../apps/presenter-ui/src/app/CloudConnectionPanel.tsx),
lines 14–22. Render selected configuration from its current read, not a
historical mutation receipt. Distinguish certificate inspection from API access
and show the relevant OEM/SP mismatch when known; successful local certificate
parsing does not itself establish Service Provider access.

### F18 — P2: acceptance documentation and test coverage can overstate consistency

**Document/source review.** The traceability register still says “Implementation
authorized: no”, with several current paths “implementation open”, while the
delivery plan and implementation receipts record authorization and execution.
The retained old UI fixtures also account for a substantial part of the green
browser suite. They do not cover every real Studio branch above. The current
specification's abnormal-Finish amendment permits destructive retirement after
failed installation, while a later paragraph still broadly says forced cleanup
is not implemented; distinguish scoped Finish from campaign recovery.

Sources: [traceability register](../demo/mockups/aosedge-demo-ui-traceability-register.md),
[delivery plan](../planning/active/demo-studio-delivery-plan.md),
[UI-STUDIO-026](../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
Update status/evidence links without claiming real KUKSA/advisory or Production
qualification. Add real-renderer regressions for the eight reproduced cases.

## Latency: measured response time versus observation cadence

Three sequential local GET samples, current retired environment; HTTP 200 in
all cases. These are response times, not fresh active-Unit Cloud timings.

| Endpoint | Samples, milliseconds | Interpretation |
|---|---|---|
| snapshot | 193.232 / 198.660 / 210.876 | Local status/catalog/receipts; median 198.660 ms. |
| platform | 14.726 / 0.741 / 0.894 | No Test binding; subsequent calls may reuse the one-second coalescing result. Not a network-Cloud benchmark. |
| monitoring | 0.963 / 0.845 / 0.872 | No Test binding; no remote resource inventory measured. |
| operations | 2.221 / 2.051 / 3.018 | Local protected session read; median 2.221 ms. |
| client-state | 2.328 / 2.377 / 2.054 | Local build/session identity; median 2.328 ms. |

| Consumer | Current scheduling / deadline | Potential visible lag |
|---|---|---|
| Header/local lifecycle | 10 s after read completion, visible only; focus and post-action refresh; 8 s request budget | External changes can wait almost a poll interval plus response time. |
| Cloud inventory/platform | Entry/action refresh; pending 2→4→8→10 s, idle 10 s; 35 s fetch budget | Not instantaneous; stalled read can consume its budget while old facts remain visible. |
| Operations/progress | 5 s idle, 1 s active, measured after completion; 6 s GET budget | Initial job progress and terminal UI transition have their own polling delay. |
| Resources | Follows Cloud observer refresh generation; 65 s request budget, in-flight sharing | Separate slow observation can lag inventory; sample age may be much older than read age. |
| Product backend | 10 s after read, visible only; 15 s fetch budget | Separate from Cloud publication/runtime and vehicle telemetry. |
| Native network readback | 5 s poll, 15 s command budget | Local ON/OFF is not the timestamp of Cloud's state transition. |
| Native telemetry | Producer default 250 ms subscription, 500 ms display-state timer; 5 s stale floor | Modest freshness policy already exists; not a hard real-time guarantee. |

There is no discovered intentional UI wait of five, ten or thirty minutes.
In the preceding live run the Cloud changed to Offline roughly 34 seconds
after the packet drop, while the corresponding backend connection-event
receipt delay was about 9 ms. That transport/cloud detection interval must be
kept separate from the UI's next poll. A whole-VM shutdown and packet DROP
can legitimately produce different detection times. The earlier RabbitMQ
timeout was not reproduced in that bounded run; this audit does not declare
the platform issue permanently fixed.

## What is already correct and should be preserved

- Right-side component/service inventory comes from Cloud, not SSH guesses.
- Cloud-installed VDP is not presented as proof of VDP process/data readiness.
- Cloud Connected is not collapsed into Online; local external-link OFF does
  not itself set Cloud Offline.
- First service deployment is distinct from publication. Higher versions use
  the existing assignment; services do not inherit the component Safe Stop gate.
- No validation-batch approval is required by the current verification-set flow.
- Backend proof is visibly synthetic and current-Test scoped; it does not turn
  into a vehicle driver advisory. KUKSA permissions remain an explicit exclusion.
- Missing values remain different from zero. CPU is DMIPS; unknown resource
  units are not silently converted to percentages or bytes.
- Failed Cloud observations retain last-known data instead of inventing
  removal, and binding changes are checked in the normal observer path.
- Ordinary current-run cleanup and partial-Finish continuation regressions pass.
- Normal fixed-layout views show no measured overflow at the tested sizes;
  B2 icons and the left-native/right-Studio composition remain intact.
- Normal requests are deduplicated; a lost mutation response is not replayed.

## Proposed correction order — not implementation approval

1. **Truth of status:** F01–F04, F06–F08. One version/binding-aware read model for
   cards, ribbons, details and messages, using existing Cloud fields.
2. **Operator recovery:** F10–F12 and F15. Preserve uncertainty protection;
   expose reconciliation, correct receipt scope/capacity and actionable waits.
3. **Refresh consistency:** F09, F13 and F17. Fresh selected configuration,
   coordinated post-action refresh, compatible budgets and safe browser build
   adoption; no new guest polling or blanket removal of checks.
4. **Bounded presentation:** F05, F14 and F16. Clear empty states, fixed-size
   pagination, truthful native labels. No CARLA visual redesign.
5. **Evidence:** F18, then targeted real-renderer regressions and one agreed
   operator-visible cycle. Keep live timing, fixture correctness and excluded
   KUKSA/Production functionality explicitly separate.

No fixes, commits, pushes or demo restarts were performed by this audit.
