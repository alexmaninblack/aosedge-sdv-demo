<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native UI runner pilot

- Date: 12 October 2026
- Status: Mechanical pilot passed; live package installed; retained Test conflicts with fresh-instance Cloud setup
- Integration branch: `codex/presenter-human-friendly`
- Gateway branch: `codex/presenter-human-friendly`
- Scope: Five Driving Control buttons and a separate signed M1 qualification tool

The operator authorized recording the research and implementing a pilot on the
current review branch. Stable semantic UI identifiers replace stored screen
coordinates. Retain Playwright for Presenter and use a narrow Swift executor
over public macOS Accessibility and Quartz APIs for the native surface. Main,
Production, Factory, Unreal/CARLA heavy inputs and the video repository remain
unchanged. The [timing baseline](../../../qualification/ui-qualification-timing-2026-10-12.md)
is the comparison checkpoint, not acceptance of this implementation.

## Research and selected approach

Apple recommends static, unique, nonlocalized identifiers for UI automation.
They remain separate from user-facing labels and layout. See
[Apple UI automation](https://developer.apple.com/videos/play/wwdc2025/344/).
Playwright provides the equivalent explicit test-ID contract and page objects
that centralize navigation rather than copying selectors into every scenario:
[locators](https://playwright.dev/docs/locators#locate-by-test-id) and
[page objects](https://playwright.dev/docs/pom).

Driving Control currently draws its buttons inside one AppKit `ControlView`.
Its hit-testing dispatches mouse input; the drawn controls have no separate
Accessibility elements. Add virtual `NSAccessibilityElement` button children,
as described in Apple's
[custom-control guide](https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/ImplementingAccessibilityforCustomControls.html),
without replacing the visual design or creating a test-only vehicle command.
Frame queries derive from the current view/window transform, not a stored
desktop point. Expose enabled state and route Accessibility activation through
the same guarded UI dispatch as the mouse.

Appium Mac2 is the established alternative over XCTest. It supports semantic
identifiers and retained-app attachment, but requires Xcode on the test host:
[requirements](https://appium.github.io/appium-mac2-driver/latest/getting-started/)
and [capabilities](https://appium.github.io/appium-mac2-driver/latest/reference/capabilities/).
Adding those development tools could mask undeclared clean-install dependencies.
The selected pilot therefore builds a small signed executor on the development
Mac/SSD and runs it on M1 without installing Xcode or Appium there.

## UI identity and execution contract

| Native action | Stable identifier |
| --- | --- |
| Safe Stop | `driving.safe-stop` |
| Autopilot | `driving.autopilot` |
| Brake maneuver | `driving.brake-maneuver` |
| Tire maneuver | `driving.tire-maneuver` |
| Return to road | `driving.return-to-road` |

Identifiers describe meaning, not caption, locale, version or position. A
duplicate/missing identifier is an explicit failure, never a request to pick
the first similar button. Cosmetic changes preserve IDs. Navigation changes
update one adapter; changed semantics require a changed scenario/contract.

The qualification executor targets an exact process, signed application and
binary digest. It accepts only the fixed five action IDs, bounded inspection
and fixture-only layout/negative operations. Communication stays in private
local qualification files; no listening port, credential channel, shell
command or arbitrary application/action is added. It runs as its own signed
GUI-session application, not as an Accessibility grant to SSH.

For mouse acceptance, resolve the current Accessibility element/frame,
require enabled state and the foreground target window, use system-wide
Accessibility hit-testing to reject an overlapping window, recheck the target,
then emit one mouse down/up. Apple's
[hit-testing API](https://developer.apple.com/documentation/applicationservices/1462077-axuielementcopyelementatposition)
and [Quartz events](https://developer.apple.com/documentation/coregraphics/cgevent)
provide these primitives. Successful event submission is not proof of the
button effect. Accessibility `AXPress` is a separate activation path and cannot
silently satisfy a mouse-click gate.

Record intent before input and a correlated receipt afterward. A request ID
cannot be executed twice. Lost responses remain uncertain: inspect evidence
and state without clicking again. Report permission refusal, hidden/minimized
or obstructed windows, invalid target and disabled buttons as bounded codes.
Do not use OCR/AI guessing, direct driver RPC or a mutation API as a fallback.

## Pilot stages and limits

1. Add the semantic Accessibility representation and unit tests for IDs,
   enabled-state guards, unchanged mouse dispatch and unsupported actions.
   Build only the affected native sources, with scratch/module caches on SSD.
2. Build a separate signed M1 fixture from the actual production `ControlView`
   source. Its callbacks write test-only action receipts; it has no simulator,
   VM, Cloud or vehicle-control connection. Keep the installed immutable
   candidate and persistent Test unchanged.
3. Run the executor on M1. Require genuine mouse delivery to each of the five
   controls and correlate the fixture callback. Repeat after moving/resizing
   the window and test disabled, missing, duplicate and obstructed targets,
   wrong process/digest and request replay. Preserve the preceding failure
   rather than retrying unknown input.
4. Record timings for resolution, preflight, input and effect observation.
   Close both pilot applications and verify zero pilot processes. Keep only
   small apps, source pins and compact evidence; do not stop shared Docker.
5. Integrate with a new immutable normal package only after the mechanical
   pilot passes. A changed Driving Control payload requires reassembly/signing,
   not in-place replacement of the installed package. Live vehicle/result
   acceptance remains a separate gate on M1 through the normal owners.

The fixture is a UI-input/layout test, not an E2E vehicle test. A fixture callback
does not prove Safe Stop physics, a real maneuver or product delivery. Report
the two gates separately. Unit/fixture results cannot close the existing full
UI, native Setup/WKWebView, first-use, repair or full-E2E acceptance boundaries.

The pilot introduces its own Accessibility client identity. Any required OS
permission is explicit and limited to that signed qualification app; do not
grant Full Disk Access, change TCC databases or disable automation protections.
If permission is unavailable, finish independent source gates and report the
specific OS boundary without fabricating native results.

## Source ownership and fan in

`carla-ego-runtime` owns the production `ControlView`, its Accessibility IDs
and shared input dispatch. `aosedge-sdv-demo` owns the qualification executor,
fixture build/orchestration and records. Both use the same review branch name.
Publish the Gateway source first, then the integration references/evidence.
Do not merge either main automatically. Qualification-only software remains
separate from the installer/runtime payload.

## Authorized live connection

The operator authorized Stage 5 on 12 October, after the mechanical campaign.
Preserve the retained M1 Test and reuse published VDP/Brake/Tire releases. Reuse
CARLA and Factory; publish no new vehicle component or service.
Reassemble the changed native UI through the normal immutable package and Setup
selection owners. Do not patch the installed package or reinterpret the earlier
candidate's receipts as qualification of its successor.

Observed contract constraint: both instance initialization and version selection
refuse a retained vehicle journal. A stopped Test is not permission to migrate
it. The normal successor therefore uses a separate private M1 instance and Test;
the earlier instance, VM, Unit and history remain paused and unchanged. This is
an isolated qualification deployment, not proof of retained-run upgrades.

The network checkpoint was resolved on 12 October. OEM and SP authentication,
association, architecture, model and delivery permissions now pass. The normal
Cloud preflight instead reports `TEST_UNIT_SET_HAS_OTHER_UNITS`: the shared Test
verification set contains the retained Test's Unit. A separate local instance
does not isolate this account-level set. No new Test or native input was created.

Preserving the retained Test and creating another independent Test with the same
accounts cannot both satisfy the existing first-use contract. A plan decision is
pending: retain the previous Test and defer live qualification, or replace it
through the normal Finish lifecycle before creating the successor. Do not move
the journal, edit set membership directly, bypass occupancy guards or modify the
installed immutable payload. Existing package/media and completed preparation
receipts are reusable; no new heavy build or publication is needed.

The hierarchy is:

```text
carla-ego-runtime/tools/KeyboardControl.swift     product controls and semantic IDs
aosedge-sdv-demo/scripts/qualification/native/    separate signed native executor
aosedge-sdv-demo/scripts/qualification/           browser/native scenario adapters
aosedge-sdv-demo/docs/qualification/              accepted, compact evidence
```

The live adapter binds each request to the current installed candidate, Test,
Presenter session, fixed scenario stage, native PID and executable digest. Obtain
the PID from the normal source journal's keyboard command and control directory;
do not select a similarly named application. Before input, require the same idle
Presenter session, connected Test and current source owner. The executor permits
only the five semantic actions, inspection and normal self-closure; fixture
layout/negative operations are forbidden in live mode.

Use a distinct native mouse-input receipt, never `CLICKED_THROUGH_CUA`. Event
submission remains `INPUT_DISPATCHED`, not a successful vehicle outcome. The
scenario separately requires actual Autopilot motion, Safe Stop physics, fresh
same-version Brake/Tire backend products and stationary Manual return. Retain
one input intent per stage and do not replay an uncertain click. Run visibly on
M1, then close normal demo owners, browser and executor; preserve Test data and
the shared Docker Engine. This closes only the live five-control boundary, not
the installer/WKWebView or full-E2E acceptance scope.

## Autonomous campaign entry

On 12 October the operator authorized converting the current check into one
scripted scenario and recording this execution rule for future tests. The
[campaign entry](../../../../scripts/qualification/native_controls_campaign.py)
and [run contract](../../../qualification/native-controls-campaign.md) own
preflight, normal preparation, unattended visible UI execution and final cleanup.
The agent no longer schedules normal test stages. No product payload, new
publication, retirement or permission grant is added by this amendment.

Keep the retained-Test decision above unchanged. Fresh preflight checks shared
Cloud occupancy before expensive media work and reports its exact fixed blocker.
Do not use a blocked preflight or source unit tests as live-control acceptance.
The declared profile includes API baseline preparation and subsequent cold UI
startup; those costs must not be presented as a warm-only control benchmark.

## Mechanical acceptance

The first authorized M1 campaign passed 21 stages in 5.075 seconds, including
normal fixture startup and final closure. Ten measured mouse actions covered
the five controls before and after movement/resize; each was corroborated by
the production mouse-handler callback. Negative targets emitted no input.
The same recorded request remained present through repeated polling without
being executed again. Both application processes were absent after cleanup.

The [qualification receipt](../../../qualification/native-ui-runner-pilot-2026-10-12.md)
records the measured boundaries and remaining live gate. This result closes
stages 1–4 of this packet only; Stage 5 remains pending.
