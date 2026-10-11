<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter branch DMG and M1 qualification — 11 October 2026

Status: The clean successor contains the profile and stopped-window display
corrections. Its M1 API journey has 117 latest PASS results, with the explicit
qualification-source review caveat below. Visible UI checks on that exact
successor and new Test completed across a serial release story, an exact Tire
continuation and a separate moving-SOTA scenario. The release story retains its
native-witness timeout; the continuation and moving scenario passed.
Bounded native Setup/WKWebView checks and repeat launch without mounted media
also passed on 11–12 October; the remaining first-use gates are listed below.
Failed and passing experiments remain separate, never a synthetic uninterrupted
journey. Main and Production are unchanged; normal cleanup preserves Test data
and Docker. The historical candidate evidence below does not qualify the
successor. Current artifact pins and results are in the Clean M1 campaign section.

## Original review scope and candidate (historical)

Branch: `codex/presenter-human-friendly`. Presenter product source:
`d65c4f0af952253d64a65141fa4e25358c610000`. Main is unchanged at
`a4afa82e2dd2e6007102797cb785e5f004e46db6`.
The corrected Presenter source and journey expectations are committed at
`3863db63b2d04c8e5e43174c11f311e878ccbf44` on the same review branch.

Candidate output:
`/Volumes/SDV-Build/sdv/build/candidates/presenter-human-friendly-20261011-dmg`.
The complete DMG is named `AosEdge-SDV-Lab-Presenter-Review-20261011.dmg`.
Build only UI/native helpers and Setup; reuse reviewed Gateway, Factory `.41`,
CARLA, Python, QEMU and backend inputs. No simulator or Factory rebuild is
required for this Presenter change. Credentials and installed run state are
not part of the media. Existing Apple Development signing does not imply
Developer ID/notarization or public distribution approval.

## Build findings

Two local orchestration-input mistakes were corrected without weakening the
canonical checks or changing runtime behavior:

1. A previously repackaged host group cannot serve as the original SDK-origin
   input to the native assembler. The OpenSSL source-provenance guard rejected
   it. Reuse the original reviewed retained host input with manifest SHA-256
   `f6ae4b1222e55a0d15501176ca0ab91aaa29ce011817419c1e6b3443c5dacff2`.
2. The direct packaging orchestration omitted the existing workspace scratch
   root setting. Native signing left two empty-registry metadata files inside
   the host group. Exact inventory validation rejected those undeclared files.
   Use `SDV_SCRATCH_ROOT` on the selected SSD, as the ordinary reproduction
   worker environment already does. Remove only the owned, idle empty metadata
   directory; reuse completed verified UI/host/VM outputs. Do not add scratch
   files to the payload manifest or relax its equality check.

The native Setup protocol self-test passed. Final DMG image verification passed;
the build receipt records 14,160,513,657 bytes and SHA-256
`65cec3f47d3c5963843505d06de15b42e219a8124cf0ce51e732d53e04f17b26`.
The application manifest is
`6f9b0391d1c696c7bbe07c0b94ead485536b47956bb893c7b354d65bb15d10b5`;
the signed Setup executable is
`be5b586fb90858d45c4056a209211cf117446921b716cc34b04babd6bb2084a5`.
These pins bind the new M1 campaign and cannot inherit the old candidate's
passes. The media receipt explicitly reports `notarized: false` and no runtime
or Cloud launch during packaging. Owned full-size staging is cleaned on exit.
Compact private logs
are in `.local/presenter-human-friendly/`. Large outputs remain on the SSD.

## Fixed campaign and local evidence

The qualification harness suite passed 78 tests. The 117-step fixed journey
uses exact installed candidate/Test bindings, journaled request identities and
the existing signed Setup and product owners. It covers:

- Installation and backend preparation; current staging certificate pair.
- New Test, simulator, provisioning and attachment.
- Serial VDP V1→V2→V3 via Safe Stop and Brake V1→V2→V3, then Tire V1.
- Native maneuver commands, new product delivery and correlated advisories.
- Independent resets, return to road, 300-second offline operation/recovery.
- Ignition off/on, unchanged identity/models/history and new post-boot results.
- Stop demo/Start controller on the same Test, observed source/VM/backend stop,
  preserved Docker Engine, explicit simulator start/attachment and new results.
- Test-owned process/window shutdown with persistent state preserved.

Native window/layout and button acceptance remain separately observed; a
scripted operation is not a native click. New-account token entry, moving SOTA,
installation interruption/repair and external distribution are not silently
closed by this branch campaign. The deferred VDP timeout is not changed.

## M1 preparation boundary

The new DMG was delivered to
`SDV-Qualification/presenter-review-20261011/AosEdge-SDV-Lab-Presenter-Review-20261011.dmg`
under the authorized M1 test user's home directory.
The canonical media owner recorded transfer PASS (213.977 seconds, exact
consumer digest and unchanged file identity) and mount/signature/pin verification
PASS (71.485 seconds). Installation was deliberately not dispatched while the
existing-state gate is blocked. The private installation report correctly says
`installation: NOT_COMPLETE`, `nativeAcceptance: NOT_RUN` and
`fullE2E: NOT_COMPLETE`. Later continuation rechecks the same media identity;
it does not retransmit a verified large file merely for another status check.

M1 transport and unlocked Screen Sharing are available; the demo was quiescent
at preflight. The old default instance retains a provisioned Test. Installed
selection correctly blocks replacing that kit until normal retirement.

The exact old Test was `524ed2c5-23b6-4ec7-ab81-e8687f4be096`; its staging Unit
was `5c2e41b1-19cf-43c9-9428-89460015d243`. Tool review initially rejected the
retirement and scoped unused-copy deletion before execution and required exact
target approval. The operator then explicitly approved those objects. Normal
installed retirement confirmed `COMPLETED / RETIRED`, and the run journal is
absent. Retirement was not replayed during subsequent copy cleanup.

The two approved unused qualification DMGs and the unselected `1cb2628a…`
package were removed after exact target/usage checks. Approximately 159 GiB is
free on M1. The accepted `e296fd…` package, credentials, source and Production
are preserved. An overly broad local cleanup preflight checked preserved state
as well as the actual removed copies; it was narrowed to the deletion targets.
The separate product installation guard was not changed.

The installation guard reported `INSTALLED_NATIVE_CONSUMER_ACTIVE` while the
Docker Virtualization file-sharing cache held the retired instance; zero
containers were running. The operator explicitly approved one M1-only normal
Docker restart. That restart completed, preserved the Engine identity
`fa9259a6-f8b1-44e2-80ba-2ad68e9d00d6`, and the unmodified installed-state
quiescence check passed. Images and data were not removed. This is exceptional
host maintenance, never a routine Engine lifecycle test.

Continuation detected a changed media `ctime` after its first mount, with the
same device, inode, size, modification time and mode. The guard stopped before
installation. One full consumer digest verification confirmed the original DMG
bytes and recorded its current stable identity without another transfer. The
earlier blocked observation remains in the append-only evidence. Signed Setup
installation and backend preparation subsequently passed.
No journal alteration, forced selection or guard bypass was used.

## First installed journey and order correction

The first journey passed installed-package, Docker, backend-image, Cloud-pair,
Cloud-readiness, VM-access, service-subject, Presenter, Create, controller-start,
simulator and provisioning checks. The following redundant connection
confirmation stopped with `SOURCE_EXISTING_ASSIGNMENT_NOT_READY`. Provisioning
had already selected the Test in stationary Manual mode; this failure occurred
in the existing-assignment read branch, before a new source assignment. Normal
shutdown passed and confirmed zero owned processes and listeners.

Bounded diagnosis restored the same Test through its normal owners. An
unconfirmed VM response was reconciled by a read-only observation rather than
a second start. A later source connection checkpoint reached `RESET_CONFIRMED`.
The guest reported incoming VDP `143.0.0` waiting for Safe Stop, with a recorded
`safe_stop_timeout`. One exact checkpoint continuation stopped at
`SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE`, preserving its operation identity
and generation. No trust, TLS, freshness or transaction guard was weakened.

The harness now keeps simulator-before-provisioning and performs the first
physical Safe Stop and prior-update settlement before redundant connection
confirmation. The 117-step plan and all 78 qualification-harness tests pass.
This is a harness-order correction: the installed product and DMG are unchanged.
A suspected short frame-probe timing race was not established as the cause of
the original failure and is not presented as a product defect.

After classification, normal retirement removed only failed Test
`0c95b7b3-3ccb-4781-8092-4165be0171ad` and its staging Unit
`e87f478f-7359-4e8e-a5f6-2bec86d471c0`. Retirement completed, the run journal
was absent, and fresh host checks confirmed zero owned processes and listeners.
Published releases, credentials, Factory, installed packages and Production
were preserved. The failed campaign's compact evidence remains retained.

The corrected journey uses a separate append-only record directory with the
same installed candidate and authorized staging references. It does not resend
media, reinstall the package, rebuild Factory/CARLA or restart Docker again.

## Live release and recovery results

The corrected 117-step campaign recorded 110 PASS, one failed assertion and six
steps not run. Serial VDP V1–V3 and Brake V1–V3, Tire V1, new maneuver products,
advisories, independent resets, 300-second offline operation, queued delivery
after reconnection and ignition off/on all passed. New post-ignition products
were observed for both teams. Normal shutdown passed and preserved the Test.

Stop demo and Start controller, fresh stopped-owner observation, explicit
simulator restart, connection and VDP readiness also passed. The preservation
assertion failed only because it reused raw ignition's Safe Stop expectation
after the explicit `connect-test` action. Recorded telemetry was fresh, unheld
Manual, 0 km/h, 100% brake. The boot changed; Unit/Node/system identity, both
models and both product histories were preserved. This is a test expectation
defect, not lost state or a runtime crash.

The corrected `demo-restart` postcondition requires stationary Manual after
that deliberate action, while raw `ignition` still requires Safe Stop. Identity,
boot, model and history requirements remain unchanged. All 79 harness tests
pass, including rejection of moving, held, stale, Autopilot and state-loss cases.
The original failed assertion remains failed in its append-only campaign.

A separate follow-up repeats the complete continuous Stop/Start experiment on
retained Test `1f3cfbff-6323-4282-b3dd-f6a1705de60e`, staging Unit
`4f73881b-037c-4bf5-aafa-3c628cddb749`. It obtains a new before/after pair and new
post-restart products; it does not combine observations across the earlier
shutdown or republish the already verified releases. All 26 planned follow-up
steps passed. Fresh observations confirmed the same Unit/Node/system identity,
preserved models and product histories, the changed boot, stationary Manual
after deliberate connection, and new Brake/Tire products. Shutdown passed.
The original 117-step campaign remains 110 PASS, one failed assertion and six
not run; the follow-up is separately scoped evidence, not a retroactive rewrite.

## Native review and stopped controller correction

The signed Setup's native Cloud dialog connected the existing certificate pair
to staging. Continue installation reached Ready to open SDV Lab; its native
Open SDV Lab button opened Presenter. The stopped Test displayed the installed
VDP V3, Brake V3 and Tire V1. The ordinary interface exposed one Demo controls
entry, Runtime, Activity, separate installed-details/release-management actions,
and Cloud configuration under Advanced settings. OEM/SP file presence was
shown separately from authenticated access. No token/PIN input gate is claimed
from reusing this pair.

Native review found Continue preparation where a fully created but stopped
controller should offer Start controller. A read-only snapshot showed a
COMPLETED story Create, a stopped VM and `preparation: {}`. The empty object is
the read port's no-checkpoint sentinel; JavaScript truthiness incorrectly
classified it as an unfinished quick-preparation recipe. No incomplete
preparation action was submitted during diagnosis.

Presenter now treats only the empty object as absent. A nonempty partial
checkpoint still follows the guarded continuation path. New tests first
reproduced the defect, then passed after the correction. TypeScript passed;
the complete unit suite passed 361 tests across 34 files, and the browser suite
passed 142 tests with the live empty-checkpoint shape in its fixtures. An
earlier concurrent run recorded one unrelated asynchronous fixture timeout;
the isolated complete unit run passed. Both logs remain retained.

This correction changes UI interpretation only. No lifecycle journal, installed
selection, certificate authority, trust guard or vehicle state was rewritten.
One corrected complete DMG was assembled using the retained Factory/CARLA
inputs. The subsequent corrected-media campaign and native check below qualify
that candidate separately; fixture passes alone do not close native gates.

The corrected file is `AosEdge-SDV-Lab-Presenter-Review-Fixed-20261011.dmg` in
the sibling `presenter-human-friendly-20261011-corrected` SSD candidate directory.
Its completed image verification and Setup protocol self-test passed. The media
receipt records 14,150,132,370 bytes, SHA-256
`99ca5094746eb762f7ebd69904026f1de9ecb2f9cb89ccead76fdc5cd77b9f28`, application
manifest `fbdf35e18bc9553d665465aee69b6c2e63e248a272c96db39f37e4a88fb12720`,
and signed Setup executable
`301d8ba38fd098fdfa4cb215dee684b3a9f8fd1ebe4cbde1f72b25fcdaa73ead`.
It remains an Apple Development engineering preview, not notarized.

## Corrected candidate installation boundary

Before corrected installation, M1 had approximately 103.7 GiB free. Both
installed packages were about 33.1 GiB each, the retained Test state about
7.8 GiB, and the current review DMG about 13.2 GiB. The ordinary installer
required its 90 GiB reserve in addition
to the new payload. A separate complete installation could not fit without
cleanup; the existing instance also correctly rejected a replacement while its
run was retained. Neither check was weakened.

Auto-review rejected a proposed clean-cycle retirement and deletion of two
old installer files before execution because those specific preserved objects
were outside the earlier exact-target cleanup approval. A new explicit
confirmation was obtained for Test `1f3cfbff-6323-4282-b3dd-f6a1705de60e`, Unit
`4f73881b-037c-4bf5-aafa-3c628cddb749`, and the review/Kit028 DMG copies. The Test,
both installed packages, credentials and installer files remain unchanged by
that rejected attempt. The accepted rollback package is not a cleanup target.

After explicit confirmation, normal retirement reported COMPLETED / RETIRED
and observed the journal absent. The two approved unused M1 DMGs were removed,
freeing about 26.4 GiB of installer files in addition to retired run storage.
The original review master remains on the build SSD; both installed packages
and credentials remain on M1. No installed selection was forced and no journal
was deleted by the harness. Earlier preflight-only failures resulted from
harness assumptions about completed lifecycle receipts; the normal installed
retirement owner performed its full checks and cleanup.

The original native review ended with ordinary demo shutdown and Setup Quit.
A fresh host probe confirmed zero owned demo processes and zero occupied ports.
The original read-only review image was normally detached. Docker Engine was
preserved with its original identity and both demo backends stopped.

## Corrected media campaign results

The fresh corrected candidate passed **117 of 117** scripted steps in one
continuous journey, from 14:00:06 to 14:27:40 UTC on 11 October 2026 (about
27 minutes 35 seconds). Media delivery, verification, installation and backend
preparation have separate records and are outside that runtime interval.
There are no failed, blocked or uncertain campaign steps and no source-revision
review warning. No earlier candidate's result is inherited.

The retained Test is `918df550-d41a-4e06-8052-23df0f60a74f`, staging Unit
`7efa7804-1f71-46cb-9f38-38c9e31618b3`, Node
`2c89ef7b-6d5e-433f-8624-c6b7151cc69a`. Releases were published and verified
one at a time:

| Component | Demo version | Installed release |
| --- | --- | --- |
| VDP | V1 → V2 → V3 | 147.0.0 → 148.0.0 → 149.0.0 |
| Brake | V1 → V2 → V3 | 124.0.0 → 125.0.0 → 126.0.0 |
| Tire | V1 | 64.0.0 |

VDP application passed through physical Safe Stop. Maneuvers produced fresh
Brake/Tire results and correlated advisories. Independent resets preserved
history and the other service's state. Return to road, the full 300-second
offline interval, queued delivery after reconnection and ignition recovery all
passed. The separate same-Test Stop/Start experiment preserved identities,
models and histories and produced new results after deliberate simulator
attachment in stationary Manual. Its raw-ignition comparison still requires
Safe Stop. Campaign shutdown confirmed zero demo-owned processes/listeners.

Private records are under
`.local/remote-qualification/m1-presenter-20261011-fixed-journey/`, with
installation evidence in its `-installation` sibling. The machine report says
`scriptedSequence: PASS`; `nativeAcceptance: NOT_RUN` and
`fullE2E: NOT_COMPLETE` remain unchanged because this runner cannot certify
native interaction. VDP-TIMEOUT-01 remains deferred. Moving SOTA, secure token
entry, the complete native operator journey and installation interruption/repair
retain separate gates. Host sleep/wake and external SSD are excluded from this
M1 profile.

## Corrected native Start and Stop acceptance

Through unlocked Screen Sharing, the signed Setup connected the existing
OEM/SP pair to staging, reached Ready to open SDV Lab and opened Presenter
using its native button. No new token-entry gate is claimed. Presenter correctly
displayed Controller switched off / Start controller for the completed stopped
Test with `preparation: {}`.

One native Start click started that same controller and both backends. Fresh
owner observations confirmed RUNNING, unchanged Test/Unit/Node/system identity
and a preserved journal. Simulator startup remained a deliberate next step;
this check did not create, provision, publish or start Autopilot.

Cancel in the native Stop demo and keep data confirmation left the controller
and both backends RUNNING. Confirming Stop once then stopped the source,
controller and both backends. Presenter returned to Controller switched off /
Start controller. Independent reads confirmed STOPPED with the same identity
and retained data. These observations are in the private
`.local/presenter-human-friendly/native-fixed-*.json` records.

This is bounded native Start/Cancel/Stop acceptance, not the entire native
operator journey. With the simulator closed, Presenter reported that desktop
window layout could not be verified; a complete live window-layout pass is not
claimed from this check.

Final cleanup used ordinary shutdown and native Setup Quit. The immediate
shutdown observation was unavailable; a separate read-only reconciliation
confirmed completion without replaying shutdown. A fresh host probe confirmed
zero demo-owned processes/listeners, zero Setup processes and zero running
containers. Docker Engine remained running with identity
`fa9259a6-f8b1-44e2-80ba-2ad68e9d00d6`; it was not restarted in this corrected
cycle. The corrected image was normally detached without force. The new Test,
three installed candidate/rollback packages, credentials and reports remain.

## Automated browser pilot

The accepted pilot uses a real headless browser on the development Mac against
the installed M1 Presenter, over a pinned same-port loopback SSH forward. It
does not replace native Setup, window-layout or full operator acceptance. Its
four allowed mutations must originate from UI buttons, with independent owner
observations and retained Test identity. No Create, publication, Reset,
Autopilot, rebuild or installation is included.

The first attempt stopped before any UI mutation because SSH forwarding was
disabled. Ordinary shutdown passed. After explicit operator approval, the
existing key retained its source restriction and received only permission for
`127.0.0.1:18080`. The server separately requires local forwarding, permits
only that destination and disallows reverse listeners. The effective server
configuration was validated without restarting SSH.

An administrative helper was then incorrectly launched with the installed
Python interpreter without `-B`. It created 44 root-owned bytecode cache files
inside the immutable runtime. Inventory validation blocked bootstrap before
any UI action. This was a qualification-tool error, not a product defect. The
operator executed the exact verified cleanup wrapper; only those temporary
caches and their six empty directories were removed. Independent observation
confirmed zero undeclared Python files and preserved Test data. All further
installed-interpreter invocations require `-I -B`; inventory checks remain
unchanged. The earlier blocked attempt and its separate cleanup resolution are
retained, not rewritten as a pass.

The restored pilot completed in 348.725 seconds, including ordinary shutdown:

| Stage | Outcome | Seconds |
| --- | --- | --- |
| Presenter bootstrap | PASS | 14.128 |
| Open installed Presenter and verify stopped owners | PASS | 3.687 |
| Start controller and verify running owners | PASS | 49.238 |
| Start simulator | PASS | 67.150 |
| Connect in Manual | FAIL | 180 second operation deadline |
| Ordinary final shutdown | PASS | 27.241 |

The UI reported rejection, and no connection job was observed during the
bounded read. The original harness recorded dispatch intent but did not inspect
the POST acknowledgement; it consequently waited for a job that was absent.
The exact rejection cause is not established by this record. Installed-card,
Cancel and confirmed Stop checks were not reached in this pilot. Their earlier
bounded native evidence remains separately scoped.

The harness correction checks the actual POST acknowledgement: explicit
rejection fails immediately, while response loss or mismatched request identity
is uncertain and must not be replayed. It also checks all owner-busy conditions
before clicking, including workspace retries and unresolved source recovery.
Six JavaScript and four Python guard tests pass. These local tests do not pass
the failed M1 scenario; the corrected browser harness has not yet completed a
new live pilot. Cold owner startup and the avoidable three-minute wait are
reported separately rather than presented as UI-click execution time.

Private restored-pilot records and the masked failure screenshot are in
`.local/remote-qualification/m1-ui-pilot-20261011-restored/`. Final observations
confirmed zero demo-owned processes/listeners, preserved Test data and the same
running Docker Engine. The owned browser and tunnel closed, and the exact
owned media was normally detached. Main, the installed candidate and Production
remain unchanged. Browser-pilot acceptance is FAIL; full E2E remains
NOT_COMPLETE.

## Subsequent browser experiments and visible M1 requirement

Each attempt has a separate private evidence directory. No failed record is
rewritten as a pass. The installed candidate, Test and shared Docker Engine are
retained; browser-tool corrections below do not modify the DMG.

| Attempt | Result | Total seconds | Classification |
| --- | --- | --- | --- |
| Acknowledgement-aware pilot | FAIL | 280.367 | Manual connection completed; harness incorrectly expected a differently spelled mode and brake units |
| Extended installed UI, first attempt | FAIL | 101.532 | Completed controller start; harness rejected nullable optional receipt metadata |
| Extended installed UI, corrected receipts | PASS | 232.859 | All 16 stages and six real button-originated mutations passed, development-side headless browser only |
| Retained release story, background | INTERRUPTED | 269.183 | Stopped before first publication when the operator required visible M1 execution |
| First visible M1 installed UI | FAIL | 241.081 | 13 stages passed; Activity lost its current-run observation and displayed no current receipts |

The first two corrections use the actual stationary Manual contract
(`MANUAL`, fresh/unheld, brake fraction 0.99–1.0, speed at most 0.5) and accept
absent optional receipt fields without accepting malformed values. Neither
correction weakens product identity, freshness, at-most-once submission or
correlated Reset checks. The corrected installed scenario covered detail cards,
all team perspectives, Cloud resources, both backend views, independent Reset,
Activity, Stop cancellation and confirmed Stop. It is not a visible M1 pass.

The first visible attempt covered the same startup and connection, installed
details, team views, CPU/Disk/Inbound/Outbound resource navigation, backend
Records and Brake windows filtering, and both independent Resets. At Activity,
the UI reported that current controller state was unavailable and showed zero
current-run operations despite earlier completed receipts. The cause of that
read failure is not established. A bounded current-run observation gate and
fixed failure projection were added to the harness; this is not a product fix
or a passed Activity check. Normal shutdown was initially uncertain, then
read-only reconciliation confirmed completion without replaying shutdown.
Every completed attempt confirmed closed demo owners/listeners, preserved Test
data and Docker, and normal detachment of media owned by that attempt.

The visible driver runs on M1 in a signed Chrome app-mode window at the product's
canonical right-hand Presenter rectangle. Ordinary product buttons start CARLA
and Driving Control; browser actions are not sent to a hidden development-side
client. This verifies the real web build, not the native WKWebView shell. Tools
are stored separately under the M1 qualification directory, never in the
installed payload. Strict copied-browser signature verification passed after
preserving framework symlinks while omitting Finder/resource-fork metadata.
The development Mac's Chrome and its attributes remain unchanged. ARM64 Node
22.23.3 is vendor-digest pinned; existing Playwright modules are reused.

The first visible launch used Playwright's default sandbox-disabled setting.
The harness now explicitly enables Chromium sandboxing. No OS security policy,
SSH Accessibility or product trust setting is changed. A later release-story
preflight observed a locked desktop and stopped before starting any product
owner or publishing a release. It did not request or use a Mac login password.

The latest local checks passed 11 JavaScript guard tests, seven Python guard
tests, the documentation quality gate and whitespace checks. These local
results do not close live visible, native-shell or full E2E acceptance.

## Visible retained release story — bounded partial result

After the desktop was unlocked, the sandbox-enabled visible browser launched
successfully on M1. Screen Sharing confirmed the real CARLA window at upper
left, Driving Control/Telemetry at lower left and the automated Presenter at
right, all visible together. The native control window must be focused before
clicking a maneuver or mode button: the initial click on an inactive window
may only focus it. A CUA click witness never replaces the independent physical
or backend result postcondition.

The scenario took 583.120 seconds including ordinary final shutdown:

| Stage | Result | Seconds |
| --- | --- | --- |
| Open installed visible Presenter | PASS | 2.837 |
| Start controller | PASS | 49.660 |
| Start simulator | PASS | 68.937 |
| Connect in stationary Manual | PASS | 15.004 |
| VDP V1, witnessed Safe Stop, UI preparation/publication and matching installation | PASS | 187.324 |
| Brake V1, UI preparation/publication, matching installation and native maneuver's new backend product | PASS | 108.136 |
| VDP V2 | FAIL | Unexpected UI request rejected before forwarding to the product |
| Ordinary shutdown | PASS | 29.989 |

Allocated and installed versions were VDP `150.0.0` and Brake `127.0.0`.
Tire `64.0.0` was not changed. All seven browser mutations originated from the
visible UI. Publications were serial: the next component/service was not
submitted until the preceding installation had been independently confirmed.
No new Create, provisioning, assignment, reset or retirement was performed.

The UI displayed unavailable local/controller state during this stage, then
reported an unknown submission after the browser guard rejected a request
that did not match its armed command. No VDP V2 preparation/publication was
forwarded to the product. The record does not establish which request field
differed; the subsequently added fixed diagnostic reports only the bounded
guard code, supported profile values and session equality, not raw payloads.
At failure, fixed
read-only diagnostics confirmed the expected run and session, the recorded
current job, no active or uncertain operation, and placed native workspace.
This does not establish the cause of the UI read failure, nor justify replaying
an operation or overriding a disabled control. The complete browser release
story remains FAIL / full E2E NOT_COMPLETE. Its private evidence directory is
`.local/remote-qualification/m1-ui-visible-releases-20261011/`.

Shutdown confirmed zero owned processes/listeners, retained Test data and the
unchanged running Docker Engine. The owned browser/profile closed and only the
scenario-owned mounted DMG was normally detached. Production is unchanged.

The harness was subsequently tightened to require the native owner's settled
placement/ordering receipt before business stages and actions, and to check
that its browser remains normal and at the canonical rectangle. This new
explicit composition gate has local guard coverage; a new live scenario using
that stricter gate has not yet been run. The prior Screen Sharing observation
is actual visual evidence for the completed attempt, not a fabricated pass of
the subsequently amended script. Native-shell acceptance remains separate.

## Targeted VDP profile recovery diagnosis

The targeted diagnosis confirmed a Presenter source defect independently of
the earlier live failure: when a local read becomes unavailable, `runId`
disappears and the original effect resets the operator's selected VDP/Brake
profile to V1. Two new unit regressions failed before correction. The minimal
correction preserves only that selection through unknown reads; preparation
remains disabled until current controller facts return. A confirmed different
run or confirmed empty-controller state still resets the profiles. It does not
retain stale readiness, receipts or installation facts.

The corrected source passed TypeScript, all 363 unit tests in 34 files and all
144 browser tests. The two new browser fixtures exercise actual refresh,
unavailable state, disabled preparation, recovery and exactly one matching V2
request for Platform and Brake. Qualification guards passed 13 JavaScript and
seven Python tests; documentation, whitespace and confidential-input checks
also passed. Only the affected Presenter assets were built on SSD, under
`build/candidates/presenter-profile-recovery-20261011/presenter-ui`. Factory,
CARLA, the DMG and the installed M1 payload were not rebuilt or replaced.

The visible M1 experiment used the retained installed candidate and Test,
confirmed the current V1 baseline rather than historical campaign cards,
selected V2 and prepared it once. Signing, publication, installation,
assignment, Reset and deletion were excluded. The installed versions remained
VDP `150.0.0`, Brake `127.0.0` and Tire `64.0.0`.

The first attempt stopped at `VISIBLE_WORKSPACE_OWNER_BUSY` before any V2
preparation request. Current V1 and idle component state had already passed.
The strict visibility gate rejected a transient busy owner immediately. That
attempt did not record which busy field was set; its 242.096-second failed
result and normal 29.597-second shutdown are retained separately.

The corrected harness waits at most 30 seconds for the same session to settle,
retaining all uncertainty, ownership, native placement and browser-geometry
guards. It does not retry a mutation. The subsequent attempt directly observed
`sourceRecoveryBusy: true`, with no active operation, workspace busy flag,
retry or uncertainty, then observed settlement before clicking Prepare V2.
This identifies that attempt's temporary busy owner; it does not prove the
unrecorded field in the preceding attempt.

The corrected targeted scenario passed in 246.011 seconds:

| Stage | Result | Seconds |
| --- | --- | --- |
| Open visible installed Presenter | PASS | 2.381 |
| Start controller | PASS | 50.389 |
| Start simulator | PASS | 70.085 |
| Connect in stationary Manual | PASS | 12.327 |
| Verify native workspace and browser placement | PASS | 0.052 |
| Confirm current VDP V1 without pending update | PASS | 6.185 |
| Select and prepare VDP V2 once | PASS | 7.720 |
| Confirm ordinary Stop | PASS | 16.085 |

The exact UI request was `prepare` with profile `v2`, acknowledged with HTTP
202. Its correlated owner receipt completed with version `151.0.0`. No signing
or publication request was dispatched. All recorded UI snapshot responses in
this attempt returned HTTP 200 with the matching run; most took 139–625 ms,
with slower reads of 1.465 and 4.180 seconds. The original unavailable-read
incident did not recur, so its underlying read failure remains unlocalized.
The profile-reset defect is proven, but cannot retrospectively identify the
unrecorded request mismatch in the earlier full release story.

The screenshot taken immediately after the independent preparation receipt
still shows the UI's preceding candidate and in-progress poll. It confirms V2
selection, not a settled on-screen `151.0.0` receipt. The completed preparation
is established by the correlated owner record; visual receipt settlement
requires a separate current UI observation before acceptance of a new candidate.

Normal cleanup confirmed zero demo-owned processes/listeners, preserved Test
data, the unchanged running Docker Engine, closed browser/profile and tunnel,
and normal detachment of the scenario-owned DMG. Private evidence is retained
separately in `.local/remote-qualification/m1-ui-vdp-transition-20261011/` and
`.local/remote-qualification/m1-ui-vdp-transition-settled-20261011/`.

Targeted installed-browser preparation is PASS; live acceptance of the source
profile-recovery correction requires a separately built and installed candidate.
The full release story remains NOT_COMPLETE, native-shell acceptance is separate,
and main and Production are unchanged.

## Remaining release and recovery checks

The operator requested the remaining checks before putting the profile correction
into another DMG. The retained installed candidate and Test remain unchanged.
The continuation binds the completed, unpublished VDP V2 `151.0.0` preparation,
freshly requires installed V1, and checks the matching on-screen candidate
before publication. It skips the already completed V1 publications.

The first continuation failed in 364.599 seconds at the native Safe Stop witness
wait, before any preparation or publication request. The recorded three actions
were controller start, simulator start and connection. The failed witness was
not accepted, and the 120-second native gate expired. Normal shutdown closed
the owned runtime, browser and media, preserving Docker and Test data.
Evidence remains under
`.local/remote-qualification/m1-ui-release-continuation-20261011/`.

Diagnosis reproduced a qualification-driver defect: its synchronous stdin read
blocked the Node event loop while awaiting a native witness, preventing normal
Playwright routing and browser polling. An isolated delayed-reply experiment
confirmed that the heartbeat ran only after the synchronous read returned.
The native wait now reads asynchronously. Regression tests require polling to
run before the witness arrives and reject failed or mismatched replies. This
changes the test driver, not installed Presenter behavior or native controls.
It does not retrospectively establish the cause of earlier unavailable reads.

The corrected continuation and subsequent recovery experiment retain separate
records and candidate-bound release receipts. The recovery experiment uses the
existing fixed offline, ignition and same-Test Stop/Start plans with fresh
baselines; it cannot inherit historical runtime readiness or mark engineering
actions as UI clicks. A separate read-only visible browser shows the installed
Presenter during those operations and closes with the other test owners.

### Completed releases and installed browser checks

The asynchronous driver completed these serial release stages on the retained
Test, checking each installation before the next publication. Service stages
also required a new backend product from the exact installed version after a
real CUA maneuver click.

| Stage | Release | Result | Seconds |
| --- | --- | --- | --- |
| VDP V2 through physical Safe Stop | 151.0.0 | PASS | 89.111 |
| Brake V2 and new product | 128.0.0 | PASS | 123.392 |
| VDP V3 through physical Safe Stop | 152.0.0 | PASS | 115.148 |
| Brake V3 and new product | 129.0.0 | PASS | 107.327 |
| Tire V1 and new product | 65.0.0 | PASS | 155.458 |

The later Return to road gate expired while awaiting the operator witness.
The attempt remains FAIL with `NATIVE_UI_BROKER_UNAVAILABLE`; no native click
or postcondition is inferred after that deadline. Normal cleanup again closed
all owned runtime and browser processes and detached owned media. This witness
timeout is not evidence of a Presenter or vehicle failure. The interrupted
attempt is retained in
`.local/remote-qualification/m1-ui-release-continuation-async-20261011/`.

A separate installed-browser continuation passed all 17 stages in 264.679
seconds against the completed release receipts, without preparing or publishing
again. It verified current version labels and detail dialogs, all three team
views, Cloud resource-tab navigation, both backend dashboards and record tabs,
independent Brake and Tire resets with peer model/history preservation,
Activity, Stop cancellation and confirmed Stop. Resource-tab navigation does
not establish fresh numerical metric samples. Its only mutations were Start,
simulator Start, Manual connection, the two resets and Stop. Evidence is in
`.local/remote-qualification/m1-ui-post-release-checks-20261011/`.

The continuation confirmed zero owned demo processes/listeners, preserved Test
data and the same running Docker Engine, closed its browser and tunnel, and
normally detached the owned DMG. The failed release-story attempt and the
passing installed continuation remain separate results, not a synthetic full
journey pass. Recovery is bound to both receipts and must establish fresh
runtime postconditions for VDP 152, Brake 129 and Tire 65.

### Fresh recovery results

All 53 engineering steps passed with no failed, uncertain, stale or unrun
steps, no unresolved actions and no source-review warning. Recorded step
durations total 964.284 seconds; this is not a split between product work and
transport overhead. The offline soak itself lasted 303.099 seconds.

- Both offline maneuvers advanced their local models and queued results without
  changing backend history. Services remained active with zero restarts during
  the complete five-minute interval; Cloud reported OFFLINE.
- Reconnection drained both queues and delivered every queued assessment.
  Delivery confirmation took 15.930 seconds, followed by Cloud ONLINE.
- Ignition produced a new boot with the same Test/Unit/Node identity, protected
  Safe Stop and preserved models/history. VDP readiness and fresh consumer
  generations were re-established; both maneuvers produced new matching results.
- Ordinary Stop closed the retained controller, source and backends without
  changing Docker. Start restored stationary Manual, identity, models/history
  and fresh consumer generations; both services delivered new matching results.

Final read-only reconciliation confirmed zero owned demo processes/listeners,
preserved Test data and the unchanged running Docker Engine. The read-only
visible browser and its profile closed, and the owned DMG detached normally.
Evidence is retained in
`.local/remote-qualification/m1-recovery-after-ui-20261011/`.

These are engineering recovery results, not UI button acceptance. They do not
qualify the source-only profile correction or close moving SOTA, complete
native-shell/token-entry acceptance, or installation interruption/repair.
VDP-TIMEOUT-01 remains deferred and unchanged.

### Native Return to road recheck

The bounded visible recheck passed all eight stages in 253.257 seconds. It
restored the retained owners, independently confirmed VDP 152, Brake 129 and
Tire 65, witnessed the real CUA Return to road click and confirmed fresh,
unheld, stationary Manual with full braking. It then confirmed Stop and normal
cleanup. No preparation, publication, assignment, Reset or deletion was
dispatched. The original witness timeout remains in its failed record.

Final reconciliation again confirmed zero owned demo processes/listeners,
preserved Test data and the unchanged Docker Engine, closed browser/profile
and tunnel, and normally detached owned media. Evidence is in
`.local/remote-qualification/m1-ui-road-return-20261011/`.

Local gates passed: 12 qualification-script guards, 15 Node guards, 79 journey
tests, 15 remote-qualification tests and 19 documentation tests. Documentation
navigation/traceability, syntax, whitespace and confidential-input checks passed.
These fixture/source gates are separate from the M1 observations above. Final
visual review found the additional product defect below; the earlier completed
operation receipts do not establish correct rendering of every status message.

### Stopped vehicle windows incorrectly reported as a layout fault

The retained Return to road experiment's `stopped.png` shows both the correct
Controller switched off guidance and an incorrect Desktop window layout
warning saying that the demo may still be running. The ordinary Stop receipt
and independent owner reconciliation confirm that the Test VM, simulator and
backends are stopped. This is a Presenter classification defect, not a failed
shutdown or evidence that Docker Engine should stop.

Two regression cases reproduced the warning for a confirmed stopped controller
with a STOPPED or NOT_PREPARED source and an old INCOMPLETE placement receipt.
The minimal correction classifies those closed windows as expected, just as it
already does before simulator startup. Advanced settings still describes the
closed windows. Unknown or running source observations, incomplete Create,
legacy interruption, retirement and an actual layout restore retain their
existing warnings and guards. No lifecycle action, receipt, identity, authority
or layout operation changes.

TypeScript and all 368 unit tests passed, including five new positive/negative
Stop-state regressions. The focused lifecycle browser suite passed all 23 tests,
including four new cases for confirmed, unknown and running source states;
the full browser suite then passed all 148 tests. Documentation and whitespace
checks passed, and the owned local browser server exited.
This correction and the profile recovery correction remain source-only;
new-candidate installed acceptance is still required. The DMG is unchanged.

### Moving service updates on M1

The retained candidate passed all 11 visible moving-SOTA stages in 440.564
seconds. The real native Autopilot button started driving. Presenter then
prepared and published Brake 130.0.0/V3 followed by Tire 66.0.0/V1, observing
fresh, unheld motion before publication and at each installed confirmation.
The Test identity and boot stayed unchanged, and VDP 152.0.0/V3 was not updated.
Brake and Tire installation stages took 60.754 and 57.393 seconds respectively.
This establishes moving service installation, not uninterrupted motion at
millisecond resolution. A witnessed Safe Stop preceded ordinary Stop.

Independent final reconciliation confirmed zero owned demo processes and
listeners, preserved Test data and the same running Docker Engine. The browser,
profile and tunnel closed, and owned media detached. Evidence is retained in
`.local/remote-qualification/m1-ui-moving-sota-20261011/`. This pass remains
separate from native WKWebView, token-entry and installation-repair acceptance.
Only unit tests may run on the development Mac; all subsequent installation,
recovery and live UI checks use the dedicated M1 internal disk.

## Clean successor campaign

The operator requested removal of owned M1 experiments, fresh installation,
then the full API campaign followed by UI checks. The previous Test
`918df550-d41a-4e06-8052-23df0f60a74f` and staging Unit
`7efa7804-1f71-46cb-9f38-38c9e31618b3` were retired through the normal owner.
COMPLETED / RETIRED and an absent run journal were independently observed.

After the operator's exact-target approval, the old current `fbdf35e…`, rollback
`6f9b039…` and unselected `e296fd…` package installations, old run-data directory
and Presenter-Review-Fixed DMG were removed. Credentials and compact reports
remain outside those targets. Cleanup recovered 113.234 GiB; M1 had 203.339 GiB
free afterward. An idle Docker file-sharing holder required one maintenance
restart before deletion. Zero containers and the unchanged Engine identity
were confirmed; this is not a routine campaign step or a Docker test.

The successor was assembled on the development SSD from the corrected review
branch at `aab218e`, retaining Factory 41 and CARLA without rebuilding either.
Only unit tests ran on the development Mac: 368 Presenter tests, 16 Node
qualification guards and 11 Python UI guards passed. The additional Python
guard binds a subsequent moving-SOTA check to a completely passed, same-candidate
release story without replaying its publications.

| Successor artifact | Binding |
| --- | --- |
| DMG | `AosEdge-SDV-Lab-Clean-M1-20261011.dmg` |
| Application manifest | `862bf19b8f345718b986c9a779b95583091ae6d373c13e3966ce715da95315e9` |
| Setup binary | `3f305be50c311a2400f9505da8e894cba01ab8f998e68df2f67241044178904c` |
| DMG digest | `5700df588b64c95e275dc32f58b1212ac93be477d9b6a740135cce3965c88753` |
| DMG bytes | 14,161,403,156 |
| Payload | 17,699 files / 35,456,536,149 logical bytes |
| Signature | Authorized Apple Development; not notarized |

The canonical media build and image verification passed. The actual M1
consumer transfer/digest check passed without a Drive round trip. Fresh
signed Setup installation and backend preparation passed on M1. API/UI
acceptance are separate gates and are not inferred
from the preceding candidate's successful experiments. Private receipts use
`.local/remote-qualification/m1-clean-20261011-api-installation/` and
`.local/remote-qualification/m1-clean-20261011-api/`. Main remains unchanged.

The fresh API Test is `b86da97e-f54c-43ed-b97a-dade76dd81a9`, with staging Unit
`20174976-c230-4e70-a7c5-8133a840f262`. Create, controller/simulator start,
provisioning, physical Safe Stop, attachment and VDP 153.0.0/V1 passed.
Brake 131.0.0/V1 publication reached READY. Assignment stopped at a final Cloud
GET returning HTTP 503 after the Unit bind returned 201 and both assignment
steps were confirmed. The uncertain attempt and normal shutdown are retained.

Fresh authoritative reads confirmed the exact Unit, retained Subject and
published service. The ordinary assignment owner reconciled its local record
to ASSIGNED using a Cloud adapter that permits observation only; no publication,
Subject creation, binding or assignment POST was repeated. The qualification
adapter now supports this confirmed-terminal reconciliation after the original
Presenter session closes. Exact Test/version guards, no-op verification and
negative mutation guards passed in the 95-test Python qualification suite.
The installed product and DMG did not change. Earlier API evidence retains its
original qualification-source digest; the resumed report flags that source
revision for review rather than rewriting old passes.

A subsequent campaign media recheck stopped on a changed consumer file identity.
The completed installation remains intact. Continuation uses the installed
journey directly; a UI campaign must re-verify the existing media digest before
use, without retransmission or reinstallation.

### Successor API sequence completed

The installed successor completed all 117 API journey steps on the new Test:
117 latest PASS, zero FAIL/BLOCKED/UNCERTAIN/STALE/NOT_RUN and no unresolved
effects. It installed VDP 153/154/155 (V1/V2/V3), Brake 131/132/133 (V1/V2/V3)
and Tire 67 (V1) serially. Matching maneuver products/advisories, independent
resets, an actual 302.92-second offline soak, queued delivery and Cloud
Offline/Online passed. Ignition and ordinary same-Test Stop/Start preserved
identity, models and history; both services produced new results afterward.

Normal final shutdown confirmed zero owned demo processes and listeners,
preserved persistent state and preserved Docker Engine. The original Cloud
503 attempt and media-identity guard failure remain in their records. The
aggregate report conservatively retains `sourceReviewRequired: true` and
`scriptedSequence: NOT_COMPLETE` because the qualification adapter changed
during reconciliation. The reviewed change is the read-only, exact-assignment
recovery described above; neither the installed product nor DMG changed.
This is not a claim of an uninterrupted single-source API run or UI acceptance.

The full visible M1 release-story UI sequence was dispatched immediately after
API shutdown, using the same candidate and Test. Its results are recorded
separately; API actions cannot satisfy browser or native-click gates.

The first successor UI attempt passed controller start, simulator start and
Manual attachment, then failed `VISIBLE_WORKSPACE_NOT_PLACED` in 228.227 seconds
including confirmed cleanup. It dispatched no release preparation or publication.
Diagnosis identified a harness omission: API shutdown deliberately closes the
workspace; starting its browser and runtime does not request native placement.
The driver now clicks the existing Restore window layout action once through
Demo controls / Advanced settings before requiring the unchanged geometry and
ordering receipt. All 17 Node guards pass, including exact single-dispatch
layout-command identity and rejection of extra fields. No product/DMG change
or weakened layout criterion was made. The original failed record remains in
`m1-clean-20261011-ui-story`; continuation uses a separate record directory.

Two further pre-publication attempts exposed additional driver assumptions:
Advanced settings starts one read-only `cloud-inspect` on mount, and the window
owner may initially return PARTIAL / WAITING_FOR_WINDOWS while its existing
bounded recovery completes. Their failed records (189.735 and 188.313 seconds,
including confirmed cleanup) remain intact. The driver now arms exactly that
inspection before the tab click and observes the original layout request until
strict placement, ordering and owner quiescence are confirmed. It never
rewrites a PARTIAL receipt as COMPLETED or permits another partial operation,
locked desktop, uncertain session, unsupported layout state or a repeated POST.
All 19 Node guards pass. No product/DMG change or release publication occurred
in these attempts.

The next visible story passed all six serial VDP/Brake stages: VDP 156/157/158
(V1/V2/V3) and Brake 134/135/136 (V1/V2/V3), including each real Safe Stop or
Brake maneuver and independent installation/product observations. Tire 68/V1
preparation and publication completed and its active instance was observed.
The agent's native click witness was not supplied within the 120-second gate;
the story therefore remains FAIL (`NATIVE_UI_BROKER_UNAVAILABLE`, 1,132.407
seconds including confirmed cleanup). This is a qualification interruption,
not a failed publication or evidence of a runtime crash. No repeated signing,
publication or assignment is used to continue it.

A separate `tire-review` uses those exact completed receipts, freshly checks
current installations and performs a new witnessed Tire maneuver and Return
to road before the remaining installed-browser stages. The original story's
failure is preserved. Twelve Python UI guards include negative cases for
another candidate/Test, incomplete stages, missing/duplicate receipts and an
unrelated failure. Nineteen Node guards and the 95-test API qualification suite
also pass. The continuation changes qualification scripts only, not the DMG.

### Completed successor browser continuation and moving SOTA

The separately bound Tire review passed all 21 stages in 376.667 seconds,
including cleanup. It freshly confirmed VDP 158/V3, Brake 136/V3 and Tire 68/V1,
then required an actual native Tire maneuver and a new matching product
(43.722 seconds). Actual Return to road and stationary Manual passed in
46.438 seconds. Installed details, all team perspectives, Cloud software and
CPU/Disk/Inbound/Outbound resources, both backend dashboards and records,
independent correlated Reset, Activity, Stop cancellation and confirmed Stop
passed. Each Reset preserved the peer model and both product histories.
No release was prepared, published or assigned in this continuation.

A separate moving-SOTA scenario passed all 12 stages in 426.581 seconds,
including cleanup. A real native Autopilot click started driving. Presenter
prepared and published Brake 137/V3 and then Tire 69/V1, with fresh, unheld
motion observed before publication and at matching installation confirmation.
Those update stages took 54.582 and 50.527 seconds. The same Test identity and
boot were retained, and VDP 158/V3 did not change. This verifies moving QM
service installation, not continuous motion at millisecond resolution.
A real native Safe Stop preceded the confirmed ordinary Stop.

Each scenario's initial cleanup response was UNCERTAIN because its worker
observation was unavailable. A subsequent read-only reconciliation confirmed
zero owned demo processes/listeners, preserved Test data and the unchanged
running Docker Engine. Shutdown was not dispatched again. Browser/profile and
tunnel closure and normal owned-media detachment were confirmed. Private
evidence is retained separately in
`.local/remote-qualification/m1-clean-20261011-ui-tire-review/` and
`.local/remote-qualification/m1-clean-20261011-ui-moving/`.

These passes close the listed installed-browser and moving-SOTA checks for
the successor. They do not rewrite the failed release story, constitute one
uninterrupted UI pass, or claim native Setup/token entry or installation repair.

### Native workspace and repeat launch on 12 October

The correct signed Setup from the successor DMG completed Continue installation,
revalidated the retained staging pair and opened the native WKWebView Presenter.
Actual native clicks started the existing controller and simulator, then
connected deliberately in Manual. Independent observations confirmed the exact
successor and Test/Unit/Node/system identities, both backends RUNNING, fresh
unheld telemetry, zero speed and full braking. No Create, provisioning,
publication or Autopilot action was part of this bounded native check.

Restore window layout completed through Demo controls / Advanced settings.
Its native dialog reported verified positions and ordering; Screen Sharing
showed CARLA in the upper left, Driving Control in the lower left and Presenter
on the right. Both services received data, and installed cards showed VDP
158/V3, Brake 137/V3 and Tire 69/V1. Native Cancel left the controller and
backends running. A single confirmed Stop closed the source, VM and backends;
Presenter offered Start controller without the incorrect stopped-window warning.
Read-only observations corroborated both transitions and preserved the journal.

The initial persistent application still pinned the earlier `fbdf35e…` candidate,
while the low-level API installation had selected `862bf19…`. It correctly
stopped with `SETUP_LOCAL_PREPARATION_REQUIRED`. This was a qualification-plan
omission, not a product failure: runtime installation alone does not execute
the existing persistent-launcher installation phase. Native Continue installation
refreshed that signed application through the ordinary Setup owner. The media
and product source were unchanged.

The qualification plan now explicitly includes `install-launcher` after backend
preparation and before Cloud setup. It verifies the selected signed Setup and
requires fresh runtime, backend and launcher observations. Lost-response
reconciliation observes status only and never repeats installation. Two new
unit tests cover ordering, strict booleans, private-path exclusion and no replay.
Future complete plans have 118 steps; the historical 117-step report and its
source-review caveat remain unchanged. This added script phase has local unit
coverage and native owner evidence, not a new complete 118-step campaign pass.

After native Setup Quit and normal owner shutdown, the DMG had no open handles
and detached normally. Finder then opened the installed application from the
M1 user Applications folder. It reached Ready to open SDV Lab with the existing
staging access, without recopying the runtime, mounting media or entering
credentials. Its actual Open SDV Lab button opened the same stopped Test with
Start controller and current installed-version cards. Independent reads
confirmed unchanged identity, STOPPED source/controller/backends and preserved
data. This closes repeat native launch without the DMG.

Private observations use `.local/presenter-human-friendly/clean-native-*.json`;
the live three-window screenshot and repeat-Setup screenshot are retained
separately. The first normal cleanup response was UNCERTAIN; read-only
reconciliation confirmed zero demo-owned processes/listeners without replaying
the stop request. Final normal shutdown of the repeat-open check passed directly.
Independent final reads confirmed zero owned demo processes/listeners, zero
Setup processes and zero running containers, with the same running Docker
Engine and preserved Test journal. The installer image remains detached.

Final local unit gates passed: 82 journey/campaign tests, 15 remote-harness
tests, 15 qualification-script tests, 19 Node UI guards and 19 documentation
tests. The documentation check passed for 350 Markdown files, 662 stable IDs
and 38 Mermaid diagrams; whitespace validation also passed. These are source
gates, not additional live or native acceptance. Only unit tests ran on the
development Mac; all live and UI checks used the M1 internal disk.

The bounded native route does not establish new-account/token entry, first-time
OS permissions or installation interruption/repair. External notarized
distribution and main integration remain separate gates. Host sleep/wake and
external SSD checks are excluded from this M1 internal-storage profile, and
VDP-TIMEOUT-01 remains deferred. Full E2E is not certified by combining separate
passing experiments with the interrupted release story.
