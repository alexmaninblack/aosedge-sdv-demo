<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .36: follow-up review before selecting fixes

Date: 19 September 2026. Status: R1–R5 SELECTED — local pass recorded; R2 and live qualification remain open.

The operator accepted R1–R5 on 19 September. R6–R9 remain unselected.
Run targeted regressions before any package/image work. R2 remains a
cause-first investigation; no speculative source correction is authorized.
No new Test, Cloud publication or Factory rebuild is part of this local pass.
See the [correction/test record](factory-36-follow-up-fixes-2026-09-19.md).

The operator approved final retirement, then requested all remarks before
choosing which to fix. The [diagnostic cycle](factory-36-e2e-2026-09-19.md)
ended with a successful 42.01-second Finish. There is no active Test. Preserve
Factory .35/.36, releases, release continuity, reports and Production.

This review consolidates observations from the completed .36 cycle and focused
source checks. It is not a new complete visual audit of every viewport, state
or historic mockup, and it does not reinstate already resolved old defects.
Keep the accepted layout, miniature icons, service colors, architecture links,
inline summaries and detail dialogs. No redesign, hidden state or new data
authority is proposed.

## Confirmed problems and bounded follow-ups

| ID | Observation and evidence | Proposed direction, subject to selection | Priority / scope |
| --- | --- | --- | --- |
| R1 | Brake displayed ACCESS_DENIED during about 19 seconds of initial credential issuance, then recovered to RECEIVING. Missing/not-yet-issued tokens and true authentication/permission failures share the same producer error path. The same mapping exists in Tire. | Distinguish initial authorization waiting, renewal and genuine denial at the producer/contract boundary; use consistent backend/Presenter labels. Do not hide actual denial or infer readiness from an active process. | High. Service/bootstrap observations and compatible readers; not merely a text replacement. |
| R2 | One ordinary-drive V1 window was incomplete when VDP rejected a nonmonotonic VISS source frame at 16:12:05.426. The bridge recovered after 0.5 seconds, and the next window was complete. All retained chunks reached the backend. The precise frame-order trigger is unresolved. | Investigate source/frame ordering with bounded evidence; prove the cause before proposing a correction. Preserve monotonicity checks, actual timestamps and missing-data semantics. Do not mask the fault by changing model thresholds or declaring it a backend upload failure. | High diagnostic priority. Source/Gateway/VDP chain; no speculative patch selected. |
| R3 | Brake window detail exposes INCOMPLETE_SOURCE_GAP directly. The operator asked what this meant. The 30 PRE / 0 ACTIVE / 0 POST example delivered 3/3 chunks, so acquisition completeness and delivery completeness differ. | Show a plain-language summary such as “Recording interrupted: source data gap”, retained phase/sample counts and delivery completeness separately. Retain the exact terminal code in details and history. | Medium. Presenter wording/presentation; independent of the R2 root cause. |
| R4 | Tire showed stale/source-gap input while the empty product section still instructed the operator to wait for a completed exercise. The empty-result text is unconditional on input state; Brake has an analogous fixed qualifying-episode message. | Use existing confirmed input/activity/delivery facts to distinguish waiting for eligible driving, missing/stale input, denied access and last-known offline evidence. Do not imply driving alone fixes an input fault. Preserve separate data authorities. | High UX correctness. Shared summary/detail selectors, including reset and release-change empty states. |
| R5 | After Return to road and the following Tire maneuver, the left Driving Control banner still read READY / select Manual or Autopilot while the telemetry panel reported SAFE STOP. The maneuver was physically stopped; a control failure is not established. | Reproduce the display transition in a targeted test, then reconcile banner and confirmed mode after scene actions. The scene completion branch currently updates sceneDetail without setting the mode except for Return to road. Do not fabricate a mode from button intent. | Medium. Native Driving Control status coherence, not CARLA rendering or physics. |

### Evidence anchors

- R1: [Brake token read](../../../brake-health-service/src/runtime/application.cpp),
  [Brake gRPC status mapping](../../../brake-health-service/src/runtime/grpc_main.cpp),
  [Tire gRPC mapping](../../../tire-health-service/src/runtime/grpc_main.cpp),
  [closed observation vocabulary](../../contracts/service-function-observation/function-observation.ts).
- R2: the source-order episode and exact timestamps in the
  [.36 run](factory-36-e2e-2026-09-19.md#observed-incomplete-window-source-frame-order).
- R3: [BrakeWindowDetail](../../apps/presenter-ui/src/features/service-team/BrakeWindowDetail.tsx)
  renders the terminal state directly before sample counts.
- R4: [BackendEvidence](../../apps/presenter-ui/src/features/service-team/BackendEvidence.tsx)
  chooses the no-result instruction by team, not input/activity state.
- R5: [KeyboardControl.swift](../../../carla-ego-runtime/tools/KeyboardControl.swift),
  `setMode`, `requestScene` completion and `consumeBridgeOutput`; live observations
  around 17:19–17:20 after Return to road.

## Optional presentation improvements — not functional failures

| ID | Observed behavior | Possible improvement without changing flows |
| --- | --- | --- |
| R6 | The global Demo Story action on the Tire page offered Open Brake backend. Source confirms the guide selects the next missing global proof, not necessarily the currently selected team. A wrong backend route is not established. | Explicitly label it “Next in the demo: Brake result” so cross-team guidance is understandable. Retain the global story sequence. |
| R7 | After Finish and its automatic session reset, the screen shows No controller created and Trace 0; the earlier operation receipt is no longer in the new session. This follows the cleanup/no-run-dossier design. | Consider a short completion acknowledgement listing stopped/deprovisioned/removed outcomes before it disappears. Do not retain previous telemetry, create a new permanent history store or weaken the accepted cleanup rule. |
| R8 | In the genuinely empty post-Finish state, cards repeat Waiting for service / Not reported / Not confirmed although the higher-level state already proves that no controller exists. | Use a concise not-yet-created empty state and reserve Unknown/Not confirmed for an existing but unobservable target. Keep the architecture slots visible and empty. |
| R9 | The real-data Tire popup visually says Demo model estimates, but its condition-score accessibility label is “Synthetic condition score”. This concerns the model score, not evidence of synthetic telemetry. | Align accessible and visible wording, for example “Demo model condition score”, to avoid confusing estimated health with fabricated input data. |

R6 is grounded in [StudioWorkspace](../../apps/presenter-ui/src/app/StudioWorkspace.tsx)
global guide selection. R8 is visible in the post-Finish Vehicle screen and the
[summary selectors](../../apps/presenter-ui/src/features/service-team/useBackendObservation.ts).
R9 is the `meter` label in BackendEvidence. These are proposals for operator
selection, not claims that existing data flow or calculation is wrong.

## Separate engineering/qualification items

These must not be silently converted into a Presenter fix or a mandatory demo
stage:

- Bare guest reboot does not restore all host-managed runtime dependencies.
  The exact failure and bounded same-Test recovery are in the
  [separate engineering record](factory-36-guest-reboot-2026-09-19.md).
  Storage survived; autonomous complete reboot recovery did not pass.
  The operator explicitly separated this from the continuous demo.
- The full transition/negative matrix is not complete. This cycle covered
  MONITOR V2 -> V3 inheritance, later warnings, same-profile Tire replacement,
  stationary Manual Return to road and offline delivery. INSPECTION V2 -> V3
  inheritance and actual Manual off-road/negative geometry cases need explicit
  coverage; missing evidence is not itself a demonstrated software bug.
- Early boot/general audit denials were recorded. A later bounded kernel
  window was empty, not proof of a universally complete zero-AVC audit.
- The .36 cycle was interrupted by the separated reboot test and recovered.
  Do not call it an uninterrupted clean-run proof or promote full qualification
  solely from the passing final Finish.

## What passed and should not be redesigned from these remarks

- Real KUKSA input, Brake V1/V2/V3 and Tire V1 products and native advisories.
- Component Safe Stop gating and service-update independence.
- Model/producer/queued-byte retention in the observed version/CM-cleanup cases.
- Independent Reset -> CLEAR -> renewed local warnings, with history retained.
- Offline local computation while both backends stopped receiving new data;
  all 32 captured messages later arrived with matching bytes and no duplicates.
- Cloud OFFLINE -> ONLINE recovery and pending Tire installation without a
  manager/VM restart; no thirty-minute wait.
- Final Finish and scoped cleanup in 42.01 seconds.

## Recommended selection for discussion

1. Select R1–R5 as the first correction/diagnosis group. R2 starts with bounded
   investigation; it is not permission for a speculative source change.
2. Decide separately whether to include optional R6–R9 in the same UI pass.
3. Keep guest-reboot engineering separate. After selected corrections, run
   targeted regressions first and agree the remaining clean qualification
   matrix before creating another Test.

This review records the selected scope, not completion evidence. Corrections
and test outcomes will be recorded separately. Model thresholds, certificates
and Factory images are outside this local pass.
