<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter status and release visibility on M1

The successor DMG is installed and selected on M1. VDP capability metadata and
all nine serial release-view checks passed, including both moving QM updates.
The latest uninterrupted campaign passed 30 stages but failed to confirm a new
Brake product after its post-SOTA maneuver: full E2E remains NOT_COMPLETE.
After connection, all 96 Cloud responses in that campaign were Online with
CURRENT profile evidence; the reported Offline fluctuation was not reproduced.
Original FAIL receipts, bounded diagnostics and final closure are retained below.

## VDP capability metadata

The installed package reports VDP `171.0.0` before consuming its asynchronous
publication response. In the first diagnostic sequence the initial profile was
unknown and V1 appeared about 13 seconds later. Two unit regressions reproduce
the retained-receipt first-read delay and a publication that completes while
inventory is loading.

The corrected reader consumes an already completed publication in the same
response and resolves the exact retained receipt from that response's installed
version. It starts at most one component-publication request per invocation;
slow publication does not block inventory. All owner/domain/Unit, version UUID,
upload, preparation/signing and inspected package checks remain mandatory.

A reversible M1 module loaded only in memory confirmed current V1 for the same
installed `171.0.0`, with the journal unchanged and no VM start or new
publication. Cold convergence took 5.025 seconds, including an explicit
read-only wait for the original publication future and the following inventory
read. This is not a first-frame or automatic UI latency guarantee. The tested
module and committed Presenter source have SHA-256
`c7888245dfe7852a8e6737878e78ee258da65719244dcec9185858993f40574c`.

When metadata really is unresolved, the card says `Profile not confirmed`
instead of presenting `Release` as a final capability label. The existing
visible observer uses its 2/4/8/10-second pending cadence for reconciliation,
then returns to idle cadence. It adds no timer, endpoint, persistent truth
store, profile inference or runtime-readiness claim.

## Offline observation

The `status-observation` scenario uses the same preserved Test and installed
package `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c`.
It starts normal visible owners, connects in Manual, alternates Vehicle and
Platform Team during a bounded observation window, and confirms final Stop
and shutdown. Production, Cloud identity, assignments, models and history
remain unchanged. Shared Docker stays running.

The passing run completed in 264.810 seconds, including cold startup and
cleanup. Its observation window lasted 64.533 seconds. Across the whole run,
26 Cloud responses contained three Offline observations before startup
converged and 23 Online observations. All 13 displayed samples after connection
were Online. The unit response, source change time, response completion time,
binding and local VM process were recorded as fixed fields without raw traces
or credentials. All owned processes, listeners, browser and media closed.

The preceding 236.571-second diagnostic failed inside the new browser observation
step; it is retained as FAIL, with successful cleanup. Its generic failure was
not sufficient to establish a product cause. The harness now distinguishes
fixed connection-reset/refusal, locator ambiguity, closed-target and timeout
categories without logging raw exceptions. The next independently bound
diagnostic passed. It does not erase the first failure.

No debounce, forced Online, freshness relaxation or inferred VM-to-Cloud status
was added. The reported one-second Offline fluctuation remains unclassified.
The same fixed status trace is collected by future publication campaigns so a
recurrence can be correlated with its actual Cloud response.

## Visible publication checks

After independent installation confirmation, each VDP release checks its
Platform Team candidate, Published and Installed stages and exact Cloud
installed version. Each QM release checks its own team candidate, Published,
Assigned and Running stages. The scenario then opens Vehicle, checks the exact
profile/version card and its details, and captures masked screenshots before
the next publication. Moving QM updates retain the independent unchanged-VDP
check. Publication and installation are not treated as the same event.

These checks use semantic names and current visible elements, not screen
coordinates, injected callbacks or manufactured state. Existing physical Safe
Stop, real instance/error, product-quality and independent owner gates remain.

## Source gates and package acceptance

Source gates passed: TypeScript, all 370 frontend unit tests, 62 Presenter
server unit tests and 23 JavaScript scenario guard tests. The 16 focused
profile/performance cases are included in the server count. Development-side
checks are unit-only; all live and visible checks execute on M1.

At the initial source-only checkpoint, updated installed-package and
per-publication UI gates were pending. Later sections record their actual M1
results. The existing full-E2E failures, including the incomplete
Brake input window, remain in the [earlier M1 report](m1-clean-install-e2e-2026-10-14.md).
VDP-TIMEOUT-01 is deferred and unchanged. No public catalog/tag or historical
immutable artifact is moved by this correction.

## Built successor and installation boundary

One successor was packaged from integration commit
`c5e164d907006c0dc3839f978770132ba5afb6ca`, reusing CARLA, Factory and the
validated Gateway/SDK inputs. The UI target was built once. Two interrupted
private packaging attempts corrected input selection and an exact Gateway path;
the completed UI was reused and only inactive incomplete host outputs were
discarded. Source or dependency checks were not weakened.

| Artifact fact | Value |
| --- | --- |
| File | `AosEdge-SDV-Lab-Presenter-Status-20261014.dmg` |
| Manifest | `75ca0ca8e6a86f9aaa5c626d77e1292209322ea71777392cddc75bf705d9cc43` |
| SHA-256 | `cb31968751a534411b4a9db64a9de7c5e58c8fa0148b3f8937118f13daffe987` |
| Bytes | `14162413813` |
| Signing | Apple Development preview, not notarized |

The M1 consumer verified delivery and media, then installed the successor.
Selection stopped at `INSTALLED_CURRENT_RUN_RETAINED`: the installed-state
contract deliberately prohibits changing packages underneath a retained Test,
even when stopped. The 384.666-second attempt is retained as FAIL; it did not
start the UI campaign. An independent read confirmed the previous selection
and zero owned processes/listeners.

The authorized clean-test route then used normal Finish for Test
`50674c94-d590-437a-8d6c-acf4d0d341c9`, with its exact Unit/Node and staging scope
confirmed before mutation. Cloud absence, empty verification set and local
journal/overlay absence were independently checked. This permanently removed
that Test's runtime/model/history data; qualification reports, packages,
Factory, credentials and Production were retained. No journal was deleted to
bypass the package-selection guard.

Selection next stopped at `INSTALLED_NATIVE_CONSUMER_ACTIVE`. Both backend
containers were already absent, but Docker's Apple Virtualization process held
six stale backend-context handles under the instance root. Its open Docker.raw
proved Docker VM ownership. No program-store handle or active vehicle was
found. The 98.009-second fresh attempt closed all test owners and detached media;
no replacement Test had yet been created.

A one-time M1 Docker file-sharing recovery was explicitly authorized and passed
with zero containers, all images preserved, unchanged engine identity and no
Dashboard request. This is a separate infrastructure action, not a recurring
test step. Normal selection of the already delivered successor then passed.
Public delivery still points to the previous immutable candidate.

## Successor baseline and profile-navigation proof

Fresh normal preparation created Test
`7edaeca0-8823-4dd2-bd0e-8477b9e092f0` on the selected successor. Controller,
simulator, provisioning, stationary connection and the VDP `171.0.0`, Brake
`153.0.0` and Tire `76.0.0` baseline passed. One baseline shutdown observation
was uncertain; the same shutdown was reconciled to stopped without replay.

The following continuous UI attempt passed seven stages and then failed the
new VDP V1 view check. Its UI publication of VDP `172.0.0` was completed once;
independent installation and current V1 metadata were confirmed. The failure
screenshot showed Platform Team correctly suggesting V2 on navigation, while
the new harness assumed that reopening the team preserved V1 selection. This
was a harness selection error, not a failed component update or a reason to
republish that release. The 336.568-second campaign remains FAIL. Recovery,
selection, fresh baseline and that campaign together took 812.959 seconds.

All 21 Cloud responses in that attempt had CURRENT V1 profile evidence. Three
Offline observations preceded connection and 18 were Online. This is not a
proof that an after-connection fluctuation cannot recur.

A bounded view-only M1 proof then explicitly selected V1 by its semantic name.
The selected `172.0.0` candidate, complete Published/Installed stages, current
Cloud version, Vehicle card and V1 details all passed in 29.008 seconds. No VM
was started and no release was published. Its Presenter, browser and media
closed. A preceding local diagnostic-call signature error occurred before
action dispatch; it is recorded separately, not counted as a product failure.

The harness now explicitly selects the exact tested profile after opening its
team. Twenty-four JavaScript guards, including the next-profile navigation
regression, and 15 Python pilot/campaign guards passed. Product package bytes
remain unchanged. A new continuous campaign uses the preserved Test and exact
`172.0.0` / `153.0.0` / `76.0.0` baseline; it does not replay the completed
publication. Its final outcome is recorded below when available.

## Corrected continuous attempt and bounded read diagnostic

The corrected campaign passed 27 visible stages, including all seven serial
capability releases, their Team/Vehicle/details checks, real maneuver results,
independent resets with history preserved, resource/backend views and actual
Autopilot movement. It stopped during `brake-moving-sota` with
`UI_READ_BROKER_UNAVAILABLE`. The 860.986-second campaign remains FAIL;
its later Tire-moving and Stop/Start business stages were not run. Mandatory
cleanup, media detachment and the temporary display assertion's closure passed.

| Confirmed UI release | Installed version |
| --- | --- |
| VDP V1 / V2 / V3 | `173.0.0` / `174.0.0` / `175.0.0` |
| Brake V1 / V2 / V3 | `154.0.0` / `155.0.0` / `156.0.0` |
| Tire V1 | `77.0.0` |

Brake `157.0.0` was prepared and published once during observed motion; its
publication operation completed before the read failure. The SSH read transport
was healthy: 105 commands and zero transport failures. The failure wrapper had
collapsed a non-PASS owner projection into `UI_OWNER_READ_UNAVAILABLE`, losing
the exact owner reason and query kind. This does not establish a failed update,
network outage, simulator crash or root cause of the original read refusal.

The harness now retains the worker's bounded fixed code and the allowed query
kind. It adds no automatic replay, cached success, deadline extension, false
Online result or relaxed freshness/quality criterion. Eighteen Python
pilot/campaign/build guards and 24 JavaScript guards passed. A small rebuilt,
signed native test client also passed its pure parser/scope checks; product DMG,
Factory, CARLA and controller payload bytes did not change. Its focused moving
profile permits only the two existing Autopilot/Safe Stop inputs.

A separate 227.181-second retained read diagnostic passed normal startup and
connection, confirmed current `175.0.0` / `157.0.0` / `77.0.0`, and passed nine
local/platform/service reads. It published nothing, reset nothing and closed
its owners and media. It established successful installation of `157.0.0`, but
did not reproduce or identify the earlier refusal and does not prove its exact
installation instant was during motion.

The corrected continuous attempt recorded 81 Cloud responses: five Offline and
76 Online, with 80 CURRENT profiles and one UNKNOWN profile. All 67 responses
after its completed Manual connection were Online with confirmed profiles.
No after-connection Offline fluctuation was reproduced.

A focused follow-up initially refused `QUALIFIED_TEST_BINDING_REQUIRED` before
any UI/product action. Current version-read receipts lacked a run-binding fact;
a genuine installed-Test binding observation was added through the normal read
adapter, without synthesizing a Create or successful UI receipt. That first
14.211-second attempt remains FAIL. The subsequent focused moving/restart
outcomes are recorded separately; they cannot convert either failed continuous
attempt into uninterrupted PASS.

## Separately completed moving and restart coverage

The bound remaining-tests entry passed in 861.878 seconds and confirmed final
closure of demo owners, native/browser clients, media and its temporary display
assertion. Shared Docker and Test data were preserved.

| Focused scenario | Visible stages | Pilot duration | Result |
| --- | --- | --- | --- |
| Moving QM SOTA | 12 | 408.419 s | PASS |
| Same-Test Stop/Start | 15 | 425.770 s | PASS |

Moving SOTA independently confirmed actual unheld Autopilot motion during both
Brake `158.0.0` and Tire `78.0.0` updates, unchanged VDP `175.0.0`, and each exact
Team/Vehicle/details view. Both inputs used the signed native runner and real
mouse events, not a vehicle RPC substitute. The scenario ended with Safe Stop
and confirmed Stop.

The restart scenario independently read its installed baseline, performed Stop
and Start, restored the same stationary Manual connection and layout, and
confirmed changed boot ID, retained vehicle identity, models/history and exact
installed versions, healthy platform services and final Stop. Neither scenario
reproduced the earlier read refusal. Their PASS results do not identify its
original cause or waive either earlier continuous FAIL.

A control uninterrupted campaign now uses the same installed DMG and preserved
`175.0.0` / `158.0.0` / `78.0.0` baseline, with the current signed test runner and
fixed read diagnostics. Its result is recorded separately after completion;
no public release promotion is inferred from these focused passes.

## Native target lookup control

The following uninterrupted control passed 11 stages and failed before VDP V3
preparation/publication. Its VDP V1/V2 were `176.0.0` / `177.0.0` and Brake
V1/V2 were `159.0.0` / `160.0.0`. The native receipt, not a guessed network
cause, established `BLOCKED`, `TARGET_PROCESS_MISSING` for pinned Driving
Control PID `78757`, with `inputDispatched: false`. No Safe Stop click or VDP
V3 publication was replayed. This 548.348-second control remains FAIL.

No matching KeyboardControl crash report was found. The retained source journal
recorded ready at 12:12:13.613 UTC and normal UI closure at 12:17:26.674 UTC,
after the 12:17:07 UTC failure; its source timeline recorded exit code 0 during
cleanup. These are logged observations, not proof that the process was alive
at the failing lookup or proof of a particular macOS root cause. The initial
registration/cache hypothesis remains an inference. Shutdown's first uncertain
response was reconciled to stopped without sending another Stop; all owners,
media and the display assertion closed.

The test-only native resolver now tries the existing macOS running-applications
list only when the direct application lookup is absent, and selects only that
same pinned PID. Wrong PID, bundle ID, executable path, digest, window, button,
foreground and hit-test checks still refuse input. It neither discovers a new
target process nor follows an implicit restart. Pure same-PID selection tests
reject mismatches and prove that an available primary result does not trigger
the second lookup. Native receipts also retain fixed lookup/kernel-presence
booleans for a recurrence. No product package, timeout, privilege or freshness
criterion changed.

The separately bound registration control starts from the exact preserved
`177.0.0` / `160.0.0` / `78.0.0` baseline. Its final result remains distinct from
the preceding controls; future passes do not identify their original causes.

## Exact service-read failure and pending-observation correction

The registration control passed the earlier native VDP V3 boundary and then
failed at moving Brake again. Its 874.336-second result remains FAIL, with all
owners closed. This time the retained read diagnostic identified the exact
cause: a `service` query returned `PLATFORM_NOT_CURRENT` immediately after
publication. The published moving Brake was `164.0.0`; VDP `180.0.0` and Tire
`79.0.0` remained its current confirmed baseline. This identifies the later
failure, not every earlier failure retrospectively.

The read-only service projection had thrown on a known temporary non-current
Cloud response. The caller already had a bounded installation wait, but the
exception closed its read broker before that wait could obtain a current
response. The corrected test projection explicitly reports STALE, UNAVAILABLE
or INCOMPLETE and withholds instances. Both API and UI installation predicates
require CURRENT; current service inventory, exact Subject detail and instance
observations are mandatory. Retained last-known instances cannot pass.

No observation is manufactured, no missing service is inferred, and no input,
publication or failed command is retried. The original installation deadline,
active-instance/version/error checks, physical motion and unchanged-VDP checks
remain. A malformed platform observation still fails. Eighty-seven Python
journey/pilot/campaign/build tests and all 24 JavaScript guards passed, including
non-current and incomplete-slice regressions.

A new uninterrupted observation control uses the same immutable installed DMG
and preserved Test from `180.0.0` / `164.0.0` / `79.0.0`. Its final outcome is
recorded separately below; no repeated media transfer or product rebuild is
needed for these test-harness corrections.

## Current-view settlement, not last-known acceptance

The observation control passed 11 stages before its VDP V3 detail assertion
failed; its 587.621-second result remains FAIL. VDP `183.0.0` had been published
once and independently installed. The browser recorded CURRENT V3 immediately
before a failed Cloud read, and its retained screenshot then showed
`V3 · last known` in the dialog. The exact `V3` assertion correctly refused to
accept that stale value, but used Playwright's implicit 5-second wait instead
of the surrounding release views' explicit 65-second UI budget. Neither a
failed installation nor an Offline controller follows from that screenshot.

The harness now uses that same explicit 65-second UI settlement budget for
exact Cloud-installed text and the VDP detail profile. It still requires the
unannotated current value, not the last-known suffix. Installation budgets,
source freshness and overall campaign deadline are unchanged. The fixed
timeout classifier now also recognizes Playwright's capitalized `Timed out`.

A separate view-only M1 proof confirmed the existing V3/`183.0.0` candidate,
Published/Installed stages, current Cloud version, Vehicle card and exact V3
detail in 30.245 seconds. It started no VM, published nothing and closed all
owners/media. The following source gates passed: 122 Python qualification
tests and 31 JavaScript scenario/broker guards. Three local Unix-socket unit
fixtures initially hit the development sandbox and passed with only that
fixture access; no development-side live demo was run.

The next uninterrupted settlement control uses the same immutable candidate
and preserved Test, bound to `183.0.0` / `166.0.0` / `79.0.0`. Its actual outcome
is recorded below, without changing any earlier FAIL receipt or public release.

## Latest uninterrupted result and preserved functional evidence

The settlement control passed **30 visible stages** in one runtime sequence,
then failed `campaign-brake-moving-maneuver` with
`NATIVE_UI_POSTCONDITION_FAILED`. Total campaign time including closure was
1155.491 seconds (19 min 15 s). Full E2E remains NOT_COMPLETE. Later Tire
post-update maneuver and Stop/Start business stages were not run in that
campaign; the earlier independent moving/restart passes remain separate.

All nine exact Team/Vehicle/details gates passed before the next publication:

| Profile or update | Confirmed release |
| --- | --- |
| VDP V1 / V2 / V3 | `184.0.0` / `185.0.0` / `186.0.0` |
| Brake V1 / V2 / V3 | `167.0.0` / `168.0.0` / `169.0.0` |
| Tire V1 | `80.0.0` |
| Brake moving QM update | `170.0.0` |
| Tire moving QM update | `81.0.0` |

The capability-story maneuvers, independent advisory resets/history, backend
and resource views, actual Autopilot motion, unchanged VDP across both QM
updates and subsequent Safe Stop passed. Moving Tire took 132.575 seconds;
no installation or freshness limit was raised. All 96 Cloud responses after
Manual connection were Online with CURRENT profile evidence. The reported
brief Offline fluctuation remains unclassified, not declared fixed.

The failing Brake input had a signed real mouse receipt. Its normal owner
recorded new exercise `708a8aea-edeb-4483-b8bf-b07f34ee5fe9`, RELEASED/COMPLETED,
matching run/operation, physical Stop confirmed and noOp false. Numeric motion
metrics show maximum speed 30.564 km/h, 31 braking frames above 10 km/h and
13.35 seconds duration. This was not a missing click or no-op.

Two short backend-only diagnostics (40.455 and 41.742 seconds) read preserved
data without starting VM/CARLA, another maneuver, publication or Reset. They
found valid assessment `5a6b8653-e369-55b4-8b9a-55de6ed0b187` for `170.0.0`,
with quality VALID_DEMO_SYNTHETIC and INSPECTION_RECOMMENDED. Its assessedAt is
13:33:28.357 UTC, with source window 13:33:19.920–13:33:28.033 UTC. The tested
post-update maneuver began at 13:33:29.955 UTC, and its mouse receipt was logged
at 13:33:38.870 UTC. Therefore that existing assessment cannot qualify the
required new result for this maneuver. No later qualifying result was confirmed
through the scenario's deadline. Model, input-window, delivery and observation
coverage causes remain open; no algorithm or VDP defect is inferred from this
bounded evidence.

A VM-only historical quality diagnostic first stopped at a local script
generation error before dispatch. After correcting generation it did not retain
usable quality evidence: its shutdown confirmation failed
`QUALITY_VM_STOP_UNCONFIRMED`. The exact emulator later exited. Normal
alreadyStopped reconciliation finalized the journal without a new guest signal
or forced termination; a follow-up read confirmed absent PID, STOPPED journal,
zero owned demo processes/listeners and the numeric motion metrics above. The
diagnostic failure is retained and is not a passing quality investigation.

Final state: current Test, VM disk, models, history, credentials and installed
`186.0.0` / `170.0.0` / `81.0.0` are preserved; all test-owned UI, servers,
simulator, VM, native/browser helpers, media and display assertions are closed.
Shared Docker is preserved. VDP-TIMEOUT-01, source-quality thresholds, service
algorithms, Factory, CARLA, Gateway and public delivery/tag are unchanged.

The next functional investigation must use one bounded post-SOTA Brake
scenario on this preserved baseline, retain before/after product IDs and
source/window/model/delivery correlation before cleanup, and require an actual
new same-version assessment. Do not replay the whole release story to diagnose
that boundary or weaken product quality to obtain PASS. The original three
visibility concerns are tracked separately from this remaining functional gate.
