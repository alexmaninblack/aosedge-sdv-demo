<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter operator experience

- Status: Clean successor API, installed-browser, moving-SOTA and bounded native checks completed with recorded caveats; main integration pending
- Date: 2026-10-12
- Branch: `codex/presenter-human-friendly`
- Baseline: `a4afa82` on main
- Scope: Presenter UI and its fixed Test operation plans

The operator approved the Presenter audit and requested implementation on a
separate branch. Keep main and the accepted installed candidate unchanged.
The ordinary interface supports the demonstration; environment configuration
and engineering diagnostics are secondary. Project documents remain English.

## Accepted behavior

Keep Vehicle, Platform, Brake and Tire perspectives, serial release preparation
and publication, native maneuvers, independent backend evidence and per-service
Reset. Preserve exact ownership, scope, freshness, Safe Stop and at-most-once
submission checks.

- Provide one Demo controls entry. Default to the full story. Offer quick
  preparation under Advanced preparation before Create only; freeze that choice
  while a run exists. Show a single Factory image as information, not a choice.
- Keep installed details and release management as separate, labelled actions.
  Empty slots identify Brake/Tire and offer their release view explicitly.
- Make next-step guidance contextual. On the appropriate team screen, offer
  Prepare, Publish or first assignment rather than navigating to that same
  screen. Results guidance names the native Brake/Tire maneuver. Completion
  means observed software/results, not complete qualification, and does not
  promote destructive deletion as the normal next action.
- Routine local preparation, Create, simulator start, controller start and
  layout restoration use one deliberate click. Publication, first assignment,
  provisioning, quick preparation (which publishes), Cloud changes, shutdown
  and deletion retain short, effect-specific confirmations. Technical execution
  detail is expandable. Reset retains its accepted one-click contract.
- Stop demo and keep data composes the existing Test-scoped simulation stop,
  Test VM stop and owned Tire/Brake backend stop operations in that order.
  Do not retire a Unit, delete a disk, reset a model, stop Docker Engine or
  mutate Production. Stop on the first unconfirmed step; unknown results never
  authorize replay. Keep Presenter available to show the receipt.
- Start controller on a known stopped Test composes existing Test VM start and
  owned backend starts. Do not create/provision/publish again. Guide simulator
  start and attachment afterward through existing operations; do not start
  Autopilot. This is separate from automatic ignition attachment recovery.
- Rename destructive Finish to Delete Test & start over, preserving the exact
  retirement owner and confirmation. Closing Presenter keeps the demo running;
  it is not Stop or deletion. Legacy `reset` remains the wire action.
- Put Cloud/OEM/SP configuration diagnostics under Advanced settings. Explain
  that complete pair setup belongs in Setup, explicitly name OEM-only selection
  and show certificate presence separately from authenticated access. Preserve
  existing check/prepare operations; hide neither failures nor authority.
- Rename Trace to Activity. Keep scope-specific refresh actions and existing
  automated observation. Mock-history inspection is an engineering disclosure,
  not an ordinary result choice. Keep record filters, charts and pagination.

These fixed composition changes add no credential channel, lifecycle journal,
CLI interface, automatic retry, safety-policy change or new Cloud authority.

## Implementation and qualification

1. Amend the current interaction contract and fixed operation-plan tests.
2. Implement the UI and bounded native plan compositions on this branch.
3. Run TypeScript, Python owner-plan, UI unit and browser regression gates.
   Cover stopped/unknown/partial/uncertain states, first assignment, repeats,
   cancellation, single-click preparation and unchanged peer/Production scope.
4. Build only Presenter after local gates; use retained Factory/CARLA inputs.
   Keep any branch candidate separate from the accepted installed candidate.
5. Record evidence and push this branch, never merge it automatically. Native
   M1 and live stop/start acceptance remain separate from fixture test results.

## Completion criteria

The ordinary flow contains no duplicate controls entry, ambiguous destructive
Finish, self-navigation prompt or mandatory mock/certificate debugging step.
Known stopped controllers have an explicit power-on path. Publications remain
serial and separately confirmed; VDP application remains vehicle-owned Safe
Stop. Stop and deletion have different effects and receipts. Negative and
uncertain paths fail closed. Branch qualification is not main acceptance.

## Local qualification evidence — 2026-10-11

The following gates passed against this branch, not the installed M1 kit:

| Gate | Result |
| --- | --- |
| Presenter TypeScript check | PASS |
| Presenter unit suite | 359 tests passed across 34 files |
| Presenter browser suite | 142 tests passed |
| Orchestrator Presenter family | 61 tests passed |
| Backend owner suite | 35 tests passed |
| Simulation owner suite | 37 tests passed |
| VM owner suite | 30 tests passed |
| Repository documentation and whitespace checks | PASS |

Browser coverage includes the ordinary service flow, first assignment,
publication cancellation, both supported operator window layouts, distinct
Stop/Delete actions, same-Test restart without Create or Cloud mutation, and
uncertain-result guards. Browser responses are fixtures; they do not prove
native or live Cloud execution. Owner tests verify the fixed stop/start plans,
partial-stop interruption and at-most-once submission.

At the initial local-gate checkpoint, only the Presenter web assets were built. The separate, mutable branch-review
output is at
`/Volumes/SDV-Build/sdv/build/candidates/presenter-human-friendly-20261011/presenter-ui`.
It is not a signed installer, a new release kit or an accepted installed demo.
Factory and CARLA were not rebuilt. Compact local logs are under
`.local/presenter-human-friendly/`; browser screenshots remain in the ignored
Presenter test-results directory. The test-owned browser server was stopped.

Main remains at `a4afa82e2dd2e6007102797cb785e5f004e46db6`. The installed M1
candidate, persistent Test data and shared Docker Engine were not changed by
this work. Publish only `codex/presenter-human-friendly` for review. Before any
main integration, review the branch UI and qualify the real existing-Test
stop/start sequence through its native owners.

## Requested DMG and M1 campaign — 2026-10-11

The operator subsequently requested a complete DMG with this Presenter and an
autonomous M1 end-to-end run, still on this branch. The candidate is assembled
on `SDV-Build` using the canonical packaging owners and retained Factory/CARLA
inputs. Neither heavy component is recompiled. Setup retains the authorized
Apple Development signature; this is an engineering preview, not a notarized
external release. Detailed evidence is recorded in the
[branch candidate qualification](../../../qualification/presenter-human-friendly-2026-10-11.md).

The scripted journey now has 117 fixed steps, including serial VDP/Brake
versions, Tire, maneuvers and product delivery, independent resets, offline
delivery, ignition, and the new same-Test Stop/Start plans. The qualification
harness suite passes 78 tests, including fresh stop-state observations,
unchanged identity/Docker Engine and interrupted-experiment guards. Fixture
results do not close native or live gates. The exact installed candidate binds
all subsequent evidence; no previous M1 candidate's passes are inherited.

M1 preparation retired the old Test through its normal lifecycle owner after
the tool-required exact-target approval. The agreed unused copies were removed;
the accepted package and credentials remain. Product installation was
blocked by an idle Docker file-sharing holder, with zero running containers.
The operator approved one M1-only Engine restart; it completed and the unchanged
product quiescence check passed, with images/data and Engine identity preserved.
This exceptional host maintenance is not part of the routine campaign.

The complete media was subsequently delivered and verified on M1. Transfer,
read-only mount and exact signed Setup/application pins passed. Installation
and live/native tests were not dispatched through the blocked state gate.
After that gate cleared, a changed media `ctime` caused another fail-closed
preflight. Full consumer digest re-verification confirmed unchanged bytes and
recorded the current stable identity without retransmission. Signed Setup
installation and backend preparation passed.

The first installed journey stopped at redundant connection confirmation after
provisioning. Diagnosis found an incoming VDP transaction waiting for Safe Stop;
the existing-assignment and trust guards remained unchanged. The harness now
observes physical Safe Stop and settlement of that incoming update before
confirming the connection. All 78 harness tests pass; the DMG needs no rebuild.
Normal retirement removed only that failed disposable Test after diagnosis.
The corrected clean journey reused the same verified installed package. Serial
releases, products, resets, offline operation and ignition passed. Its final
same-Test preservation assertion revealed a harness expectation defect:
explicit connection selects stationary Manual, unlike raw ignition's Safe Stop.
The assertion was corrected without relaxing freshness, identity or history
requirements; all 79 harness tests pass. The campaign remains 110 PASS, one
failed assertion and six not run. A separate fresh 26-step Stop/Start experiment
passed completely, including new results and ordinary shutdown.

Native Setup Cloud connection and Open SDV Lab were observed. Review exposed
a real stopped-controller UI defect: an empty `preparation` object was treated
as an unfinished quick recipe and hid Start controller. The source correction
keeps nonempty partial checkpoints guarded. TypeScript, 361 unit tests and
142 browser tests passed; a corrected complete DMG was assembled with
retained heavy inputs. No prior candidate's passes are transferred to it.

Before corrected installation, the ordinary installer required its 90 GiB
reserve and the current instance retained the tested run.
Auto-review rejected proposed retirement/media cleanup before execution.
The operator then approved the specific completed Test/Unit and two old DMGs.
Normal retirement confirmed COMPLETED / RETIRED and an absent journal; only
the named unused media copies were deleted. Both installed packages, rollback,
credentials and compact evidence remain intact. A fresh 117-step campaign is
bound to the corrected media manifest, without inherited candidate results.
The preceding native review runtime and Setup were closed, the review media
detached, and a fresh host probe confirmed zero owned processes/listeners.
Shared Docker remains running; it was not restarted for this new cycle.

The corrected campaign subsequently passed all 117 steps on new Test
`918df550-d41a-4e06-8052-23df0f60a74f`, including serial VDP 147/148/149,
Brake 124/125/126 and Tire 64, real products/advisories, independent resets,
300-second offline processing/recovery, ignition and same-Test Stop/Start with
preserved models/history and new results. No failed or uncertain campaign steps
or source-revision warnings remain. Source correction is committed at
`3863db63b2d04c8e5e43174c11f311e878ccbf44`.

The corrected signed Setup also passed native existing-pair Cloud connection,
Continue installation and Open SDV Lab. Presenter offered Start controller,
started that same Test, left it running after Stop cancellation, and stopped
it with data preserved after one confirmed Stop. Fresh normal-owner reads
corroborated each transition. This closes the stopped-controller button check,
not full native layout, token-entry or operator-journey acceptance.

Final ordinary shutdown and Setup Quit were verified by read-only reconciliation
and a host probe: zero demo processes/listeners, zero Setup processes and zero
running containers. Docker retains its original running identity. The corrected
media was normally detached; Test, packages, credentials and evidence remain.
The branch is ready for operator review. Main stays unchanged; moving SOTA,
complete native acceptance and installation interruption/repair retain their
separate gates, and VDP-TIMEOUT-01 stays deferred.

## Accepted automated browser pilot

On 11 October the operator approved a short real-UI automation pilot on the
retained M1 Test: Start controller, Start simulator, Connect in Manual, inspect
installed cards, cancel Stop, then confirm Stop. Extend only qualification
scripts on this branch. Do not change product behavior or rebuild the DMG.

Use working-Mac Playwright against the installed M1 web assets over one pinned
SSH loopback forward. Keep the original Host/Origin checks intact. Bootstrap
and final shutdown use existing installed owners; all four scenario mutations
must originate from browser clicks, not direct API/CLI calls. Additional owner
reads confirm the exact candidate, Test/Unit/Node/system identity, running or
stopped owners and stationary Manual attachment. Preserve Docker and Test data.

The pilot allows only start-demo, start-simulation, connect-test and stop-demo,
in that order, once each. Record request identity before forwarding an action.
Cancellation must dispatch no mutation. Unknown outcomes prohibit a new action
and require read-only reconciliation. Do not publish, provision, Reset, delete,
start Autopilot or replay an uncertain click. Reuse verified installed media;
record bounded timings and masked screenshots, not raw network traces or logs.

Acceptance requires the complete sequence, independent owner observations,
unchanged software cards and identity, no request on cancellation, normal final
shutdown, zero demo processes/listeners, unchanged running Docker and closed
browser/tunnel/owned media. This is browser UI acceptance of one installed
scenario, not native Setup/WKWebView/layout or full release acceptance.

The first real-browser pilot on restored installed media passed Start controller
and Start simulator but failed at Connect in Manual. The whole run took
348.725 seconds, including a wrongly awaited rejected submission. The harness
now checks the actual acknowledgement and fails immediately on rejection,
preserving uncertainty/no-replay and all owner-busy gates. Ten local guard tests
pass; no new live pass is claimed. Final shutdown, browser/tunnel close and
normal media detach were verified, with Test data and running Docker preserved.
The [qualification receipt](../../../qualification/presenter-human-friendly-2026-10-11.md)
records the separate one-time SSH configuration, exact temporary-cache cleanup,
actual timings and remaining connection investigation. No product or DMG
change was made for this pilot. Main integration is still pending.

## Authorized UI automation extension

The operator requested completion of the automation scripts and live execution
on 11 October after the pilot failure. Extend the branch qualification boundary,
not the product interface. Keep the retained Test and installed candidate.

The installed scenario adds all four perspectives, installed-detail dialogs,
Cloud software/resources, both functional backends, independent correlated
Brake/Tire Reset, Activity, Stop cancellation and confirmed Stop. Each mutation
must match the exact command armed immediately before its UI click; no arbitrary
mutation endpoint or input is accepted. Read-only owner evidence remains separate.

The retained release-story scenario prepares and publishes VDP V1/V2/V3 and
Brake V1/V2/V3 serially, then Tire V1. Bind allocated versions and service handles
to the returned preparation receipts, verify each installation before advancing,
and preserve the existing assignments. Native Safe Stop and maneuvers are
explicit gates for supported CUA clicks, with independent physical/result
postconditions. No driver RPC or direct action adapter can satisfy a UI gate.
The native witness helper records an already performed CUA click; it cannot
perform a click or prove success on its own. This scenario is agent-assisted,
not fully unattended native automation.

### Visible M1 amendment — 11 October 2026

The operator now requires Presenter, CARLA and Driving Control to be visible on
M1 throughout the live UI experiment. The hidden development-side browser is
not sufficient for this requirement. Stop its current retained release story
before publication; retain the interrupted attempt and ordinary shutdown.

Run the browser executor visibly on M1 against the same installed Presenter
server. Keep it in the canonical right-hand Presenter rectangle, alongside the
ordinary CARLA and Driving Control owners. A separate signed Chrome app-mode
window is browser acceptance, not acceptance of the native WKWebView shell.
Reuse the development Mac's verified Google-signed browser, existing Playwright
packages and a vendor-digest-pinned ARM64 Node executable, stored only under the
private M1 qualification tools directory. This explicit testing dependency is
not shipped in the DMG or installed into the product/system. No additional SSH
port, Accessibility grant, Cloud credential, Docker restart or product rebuild
is needed. Transport only fixed read queries and witnessed native clicks through
the existing pinned SSH connection. Close the owned browser and remove its
temporary profile at the end; retain compact evidence and reusable testing tools.

Keep uncertainty terminal and retain failed attempts. A completed scenario closes
the browser, tunnel, owned media and ordinary demo owners, preserving Docker,
Test data and Production. Report installed-browser acceptance and retained
release-story acceptance separately from clean installation, native Setup,
moving SOTA, offline/ignition and full E2E acceptance. Do not infer those separate
gates from script implementation or local guard tests.

## Profile recovery diagnosis

The operator requested a targeted investigation of the V1-to-V2 failure. Two
new regression tests reproduce a real Presenter defect: an unavailable local
read removes `runId` and resets selected VDP/Brake authoring profiles to V1.
The minimal UI correction retains the selection during unknown reads and resets
it only for a confirmed different run or confirmed empty-controller state.
Controller facts, mutation guards, release receipts and history remain scoped
to current observations; no last-known green state is substituted.

The targeted M1 scenario prepares V2 once on the retained V1 Test without signing
or publishing. It keeps the installed candidate and distinguishes its result
from the source correction's local tests. Main remains unchanged. The correction
requires a separately built and installed candidate before live acceptance.

The source correction passed TypeScript, 363 unit tests and 144 browser tests;
only the affected Presenter assets were built on SSD. The retained M1 candidate
passed the targeted visible preparation in 246.011 seconds, allocating VDP
`151.0.0`/V2 without signing or publishing it. The harness now waits boundedly
for owner settlement; the successful attempt recorded temporary source-recovery
activity before the click. All owned runtime processes, windows, browser,
tunnel and mounted media closed normally, with Test data and Docker preserved.
The [qualification receipt](../../../qualification/presenter-human-friendly-2026-10-11.md)
retains the preceding failure and separates completed owner preparation from
the immediate screenshot's still-updating UI. New-candidate live recovery,
settled visual receipts and the complete release story remain open.

## Continued release and recovery qualification

The operator requested all remaining checks before another DMG includes the
profile correction. Keep the installed candidate and retained Test; do not
rebuild, replace media, merge main or republish completed releases.

The asynchronous native-witness reader corrects a reproduced test-driver
event-loop blockage. It leaves browser routing and ordinary polling responsive
while preserving real CUA clicks, exact witness identity and independent
postconditions. This is qualification infrastructure, not a product fix.

Serial VDP V2 151, Brake V2 128, VDP V3 152, Brake V3 129 and Tire V1 65 all
passed installation checks. Service stages produced new matching results after
real native maneuvers. The later Return to road witness expired, so the complete
release-story attempt remains FAIL. Its ordinary shutdown passed.

A separate visible installed-browser continuation passed all 17 stages in
264.679 seconds on those exact completed release receipts. Current version
cards/detail dialogs, team views, Cloud resource navigation, backend dashboards
and records, independent resets with preserved peer models/history, Activity,
Stop cancellation and confirmed Stop passed. It published nothing. All owned
processes/listeners and browser/profile closed; data and Docker were preserved,
and owned media detached.

Fresh recovery uses both evidence sets, current VDP/consumer inputs and the
original offline/ignition/Stop-Start contracts. A read-only visible browser
accompanies engineering actions; it cannot turn them into UI acceptance.
Interrupted and passing experiments remain separately recorded in the
[qualification receipt](../../../qualification/presenter-human-friendly-2026-10-11.md).
Moving SOTA, complete native acceptance and installation interruption/repair
remain separate gates. VDP-TIMEOUT-01 remains deferred.

The fresh recovery experiment completed all 53 steps with no failed/uncertain
steps or source-review warning. It confirmed offline model progress, an actual
303.099-second soak, complete queued delivery, Cloud Offline/Online, ignition
identity/model/history preservation, fresh consumer generations and new results,
then the same preservation and result checks after ordinary Stop/Start.
Final cleanup closed all owned runtime and the read-only browser/profile,
normally detached owned media, and retained the Test and unchanged Docker Engine.

The separate visible Return to road recheck then passed all eight stages in
253.257 seconds. It freshly confirmed the three current installed versions,
recorded a real CUA click and stationary Manual postcondition, and confirmed
Stop/owner closure without publication or Reset. The earlier interrupted
release-story record remains FAIL. Final visual review then identified the
additional Stop-display defect below; main and the DMG remain unchanged. Local qualification,
journey, remote, Node and documentation gates passed. Remaining separate gates
are not inferred from these results.

### Expected closed windows after ordinary Stop

The final M1 screenshot shows Controller switched off together with an
incorrect layout warning. Independent reconciliation confirms all owned demo
processes and listeners closed. The Presenter did not include a known stopped
controller in its expected-absence classification for source windows.

Two failing unit regressions established that mismatch. The minimal source
correction adds confirmed normal controller Stop to the existing classification,
only when the source is confirmed STOPPED or NOT_PREPARED and not connected or
running. Unknown source, incomplete Create, interrupted/retiring lifecycle and
an active restore keep their existing behavior. The main screen no longer
offers layout recovery for intentionally closed windows; Advanced settings
retains their factual description. No native owner or lifecycle contract changes.

TypeScript, all 368 unit tests, the focused 23-test lifecycle browser suite and
the full 148-test browser suite passed. Documentation and whitespace checks
passed; the local test browser server exited. The profile and Stop-display corrections both still require installed
acceptance in a later candidate. Do not rebuild the DMG or merge main as part
of this retained-candidate continuation.

## Remaining gate execution

The operator requested completion of the remaining tests. Extend qualification
scripts only for the current retained candidate first. The moving-SOTA scenario
explicitly selects Autopilot through the visible native control, prepares and
publishes one new Brake V3 release and then one Tire V1 release through Presenter,
and checks fresh unheld Autopilot motion before publication and at installed
confirmation. Exact Test identity, boot and unchanged VDP remain mandatory.
Traffic stops are not Safe Stop; unknown/stale control evidence fails closed.
Finish with witnessed Safe Stop and ordinary Stop, preserving Test and Docker.
This does not claim continuous millisecond-level vehicle motion during download.

Installation interruption/repair uses a separate disposable package store,
never damage to the retained selected program or vehicle data. Exercise the
canonical transaction checkpoints, verification and explicit repair owners.
The operator clarified that only unit tests may run on the development Mac;
all installation/recovery and UI/live checks belong on M1's internal storage.
Development-side orchestration is not a development-side acceptance test.
Keep source and UI results distinct; native Setup and WKWebView acceptance
requires actual CUA actions and visible postconditions, not browser-driver or
SSH action results. Keep the DMG and main unchanged during these checks.

## Clean M1 campaign

The operator subsequently authorized removal of owned M1 experiments followed
by a fresh DMG installation, a complete API campaign and then the UI campaign.
Retire the exact previous staging Test through its normal owner before removing
its local installation or run data. Preserve credentials, compact evidence,
shared Docker and unrelated files. Reuse verified Factory and CARLA inputs.
Assemble one successor containing the source-tested profile and stopped-window
corrections; keep it on the review branch, with main unchanged. Bind all new
installation, API and UI evidence to that successor and new Test. API results
must not count as UI acceptance. Only unit tests may run on the development Mac;
all installation and live checks execute on the M1 internal disk.

The follow-up moving-SOTA experiment may consume either the existing exact
native-witness-interrupted continuation receipt or a fully passed release-story
receipt. The latter must bind the same candidate and Test, contain every serial
release stage, Return to road and confirmed Stop, record closed owners, and
identify exactly one completed preparation receipt for each current version.
It authorizes no replay of the preceding publications. Negative unit cases cover
another candidate/Test, failed or incomplete stages and missing/duplicate release
receipts. This qualification-only binding does not change the product or DMG.

Confirmed assignment recovery after a final Cloud HTTP 503 uses the existing
assignment owner, with a Cloud adapter restricted to authoritative reads.
Require both recorded assignment steps CONFIRMED, the exact current Test,
matching publication and fresh Unit/Subject/service relations. The owner must
return ASSIGNED and no-op; no publication or assignment mutation is replayed.
This handles loss of the original Presenter session after ordinary cleanup,
retains the uncertain attempt and does not turn runtime readiness into an
assignment fact. The installed candidate remains unchanged. Negative unit gates
cover changed Test, service, steps and resolution, plus attempted Cloud mutation.

After a clean API shutdown, the visible browser driver must explicitly click
the existing Restore window layout action through Demo controls / Advanced
settings before requiring native placement and ordering. Browser/runtime start
does not constitute that request. Submit once with exact session/request
binding; retain strict placement verification, uncertainty guards and failed
attempts. This test-driver correction adds no product behavior or authority.

A native Tire witness timeout after the six serial VDP/Brake stages may bind a
separate Tire review without republishing. Require the same candidate/Test,
closed owners, exactly that single witness failure, completed current-version
preparation receipts, completed Tire publication and its reached native gate.
The new visible review freshly checks all installed versions, clicks Tire
maneuver and Return to road, requires a new matching Tire product and executes
the remaining installed-browser checks. Keep the original failure unchanged;
this is not a passed uninterrupted release story. Moving SOTA may use those
settled release bindings but independently rechecks current installations.

### Clean successor results and persistent launch

The successor API sequence has 117 latest PASS results. Its original Cloud 503
and read-only assignment reconciliation remain separately recorded, with the
qualification-source review flag retained. The visible serial release story
passed all six VDP/Brake stages and completed Tire publication, but expired at
the agent's native Tire witness gate. A separately bound Tire/installed review
passed all 21 stages; moving SOTA then passed all 12 stages, keeping Test identity
and VDP unchanged. Neither pass rewrites the interrupted story.

Native signed Setup and WKWebView checks on 11–12 October confirmed the same
Test's Start controller, simulator startup, deliberate Manual attachment,
verified live window placement/ordering, Stop cancellation and confirmed Stop.
After the DMG was detached, the installed application reached Ready to open
SDV Lab and opened the stopped Test again without installation or provisioning.
These bounded native checks do not qualify new-account/token-entry flow,
first-time OS permissions or installation interruption/repair.

The low-level qualification plan had omitted the existing Setup
`install-launcher` phase, leaving the previous signed application pin in the
user Applications folder. Its refusal to open the different selected runtime
was correct. Native Continue installation completed that phase and refreshed
the application without changing the DMG. Future plans now include the pinned
launcher phase after backend preparation and before Cloud setup: 118 steps.
Fresh status must observe runtime, backends and launcher; reconciliation is
read-only. The completed historical 117-step report is not retroactively
expanded or passed as that new plan. Detailed results and remaining acceptance
boundaries are in the linked qualification receipt.

Final closure confirmed zero demo processes/listeners, Setup processes and
running containers, with the installer media detached. Persistent Test data
and the same running Docker Engine remain. Final source gates passed 97
journey/campaign/remote tests, 15 qualification-script tests, 19 Node UI guards
and 19 documentation tests, plus documentation and whitespace validation.
These source gates do not promote the separate live experiments into one
uninterrupted full-E2E pass. Main integration remains explicitly pending.

## Recorded UI timing optimization follow-up

On 12 October the operator requested that the UI timing analysis and agreed
optimization direction be saved on this branch. The
[M1 timing analysis and ordered plan](../../../qualification/ui-qualification-timing-2026-10-12.md)
records measured attempt/stage durations, the hybrid Playwright/CUA execution
model and the remaining measurement gaps. The six visible attempts consumed
42:22 of measured runner time, including 10:06 in three early harness failures.

Follow the recorded order: split timing instrumentation, supported native UI
execution without conversational click scheduling, one healthy continuous
campaign, asynchronous/bounded read reuse, then comparative M1 acceptance.
The native execution mechanism and any change to the current CUA witness
contract must be defined before implementation. Recording the plan does not
select a framework, grant permissions, change product authority, launch a live
test or merge main. Preserve serial publication, VDP Safe Stop, fresh independent
proofs, explicit lifecycle tests, uncertainty/no-replay and final owner closure.
The original campaign measurements remain intact. The isolated native
mechanical pilot below is now implemented; optimized live-E2E results are not
yet claimed.

### Authorized native runner pilot

On 12 October the operator approved the research direction and requested its
pilot implementation on this review branch. The
[native runner packet](native-ui-runner-pilot.md) records the public-framework
comparison, semantic identifiers, exact mouse-input/uncertainty contract and
source ownership. Gateway changes use its same-named review branch, not main.
First validate actual `ControlView` mouse dispatch in an isolated signed M1
fixture; its callback is not real vehicle-result evidence. Preserve the installed
immutable candidate/Test. Normal-package/live integration remains a separate
gate after that mechanical pilot; no heavy CARLA/Factory rebuild is implied.

The first M1 campaign passed 21 mechanical stages in 5.075 seconds, with
genuine mouse delivery before/after movement and resize, negative refusals,
at-most-once polling and normal closure. See the
[native pilot receipt](../../../qualification/native-ui-runner-pilot-2026-10-12.md).
This closes only the input/layout pilot, not full vehicle-result acceptance or
the existing native Setup/WKWebView and first-user gates.
