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
