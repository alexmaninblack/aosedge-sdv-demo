<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter status and release visibility on M1

The retained M1 Test reproduces delayed VDP capability metadata. A short visible
status scenario passed, but did not reproduce a brief Offline report after the
controller was connected. The source correction preserves Cloud installation
authority and adds visible checks after every serial publication. Updated DMG
and release-campaign acceptance are recorded separately below.

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

The updated installed-package and per-publication UI gates remain pending at
this source checkpoint. The existing full-E2E failures, including the incomplete
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
