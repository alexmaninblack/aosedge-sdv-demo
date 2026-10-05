<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Serial Functional Check — 29 September 2026

- Status: Serial profiles, functional results, independent resets, offline delivery and retained reboot recovery passed in the scope below; installation/release acceptance remains open
- Version: 1.3
- Prepared: 2026-09-29
- Updated: 2026-09-30
- Owner: Demo Solution Team
- Plan: [Consolidated installation route](../planning/active/installable-distribution-and-reproducibility.md)
- Previous evidence: [Installed first-use journey](cloud-first-use-implementation-2026-09-29.md)
- Operational contract: [Current workflow](../operations/current-demo-workflow.md)

## Candidate and authorized boundary

This continues the existing native Setup 024 / installed Kit 015 Test. It is
not another installation, clean-Mac result or new enrollment. The operator
explicitly confirmed the exact remaining release set, selected OEM/SP signing
and serial publication to `aws-stage.epmp-aos.projects.epam.com`, assigned only
to Unit `f26ecc96-6acd-461a-a4ad-1a1f55925165`. Ordinary UI actions then passed
the action-time review; no alternate upload path or approval bypass was used.

- Installed manifest: `8180428ce97e069a69f68a2960e376920e96c6fa969ec7eaa4354c4ce338966c`.
- Factory: `6.1.1-maninblack.39`.
- Local VM: `a3e24d29-19d6-4c8f-801c-4a72f3688583`.
- Node: `3fad0b63-2236-4bfe-95bc-13e872f3027a`.
- Final software: VDP 123/V3, Brake 99/V3, Tire 51/V1.
- Production, Factory/Game bytes, source trust and security policy unchanged.

Publication, assignment, Safe Stop, Autopilot, maneuvers, resets and external
network controls used the ordinary Presenter/native UI. Read-only CLI/SSH
observations corroborated Cloud, backend and guest evidence. Reboot was the
explicit engineering test described below, not an invented Presenter button.

## Serial release and function evidence

Every next publication followed installation and function observations of its
predecessor. VDP 121/V1 had been installed in the preceding first-use check.
Times below are UTC; receipt duration is not total click-to-vehicle readiness.

| Action | Receipt interval | Duration | Functional result before continuing |
| --- | --- | --- | --- |
| Publish Brake 97/V1 | 19:38:37.015–19:38:51.246 | 14.232 s | Assigned 19:39:46.069–19:40:10.837; active before source connection |
| Start retained simulator | 19:40:43.425–19:42:22.147 | 98.722 s | One owner; includes installed-input verification; not first cold launch |
| Connect in Manual | 19:42:43.905–19:42:52.188 | 8.283 s | Same Unit/Node, live native telemetry; no scene recreation |
| Publish VDP 122/V2 | 19:44:51.407–19:45:04.626 | 13.219 s | Pending while 121 remained installed during Autopilot; Safe Stop installed 122 at about 19:45:41; 15 READY/LIVE paths |
| Publish Brake 98/V2 | 19:46:48.472–19:47:06.338 | 17.866 s | Active by 19:47:20 while native Autopilot showed 19.3 km/h; no FOTA stop requirement applied to SOTA |
| Publish VDP 123/V3 | 19:49:17.931–19:49:30.097 | 12.166 s | Pending while 122 remained installed; Safe Stop then 123 at about 19:49:56; 23 READY/LIVE paths |
| Publish Brake 99/V3 | 19:50:39.469–19:50:55.959 | 16.489 s | Inherited V2 assessment and produced local advisory without a new maneuver |
| Publish Tire 51/V1 | 19:51:57.962–19:52:15.654 | 17.692 s | PROCESSING then READY on read-only refresh; no second publish |
| Assign Tire | 19:53:34.741–19:53:55.428 | 20.687 s | Active, initial Monitoring, then real Tire maneuver and received assessment |

Brake V1's first explicit maneuver produced window
`093b402e-365b-4c70-8dd2-d8d9f6bd9d76`: 76 samples, 8/8 chunks, COMPLETE,
durably received at 19:43:39.422. Two subsequent physical braking windows
were also retained; an ordinary stop is not assumed to be an eligible episode.

Brake V2's real maneuvers produced:

- `be15c54f-59f9-5c5c-8ddf-d7df136817e4`, received 19:47:44.851,
  MONITOR, score 40, wear 54→60.
- `f18b8cfe-8f19-5e87-8003-96738c908eea`, received 19:48:42.816,
  INSPECTION_RECOMMENDED, score 34, wear 60→66.

V2 correctly did not expose a local driver advisory. V3 subsequently used that
same retained second assessment: request
`78591cda-acd6-5cf1-97ea-4f123d0d9116` was issued 19:51:06.924, Gateway APPLIED
19:51:07.099 and backend-received 19:51:08.332. Native Inspection recommended
appeared without a fabricated new V3 assessment. Producer epoch was retained.

The dedicated Tire maneuver produced
`52cb7a17-34c1-5996-bbd9-cf9d3fd9b771`, received 19:54:30.274, score 67,
confidence 100%, 41 valid active samples and native Inspection recommended.
Its physical braking also legitimately produced Brake V3 assessment
`206bfc2d-90ca-5336-b757-3f47f9403225`, received 19:54:31.990, score 26,
wear 66→74. This is a different physical episode, not duplicate delivery.

## Independent resets and Return to road

The main-card resets dispatch directly. Their short UI operation receipt is
not the Gateway CLEAR acknowledgement; the Presenter kept those states separate.

| Reset | Command issued | Gateway CLEARED | End-to-end confirmation |
| --- | --- | --- | --- |
| Brake | 19:55:13.821 | 19:55:19.568 | 5.747 s; Brake Monitoring, Tire warning unchanged |
| Tire | 19:55:40.225 | 19:55:44.959 | 4.734 s; both Monitoring |

Brake reset ID `918d9138-97ec-422f-9198-67759081c392` and Tire reset ID
`c60ed6f4-133c-41cf-8cdb-622231c80d0e` remained distinct. Existing assessment
IDs and original receipt times remained visible. Reset did not clear history.
Return to road then completed at 0 km/h in Manual, retaining model/advisory
state and not enabling Autopilot.

## External network OFF → ON

External OFF was confirmed in native Driving Control. Two later backend reads
(19:58:33/39 and 20:02:36/37) retained exactly the previous assessment sets and
receipt times. Brake's last function receipt stayed 19:57:29.973; Tire's stayed
19:57:24.871. Their latest advisory receipts also stayed unchanged. Presenter
reported Cloud Offline and last-known backend observations, while native vehicle
telemetry continued LIVE.

Real Brake and Tire maneuvers were performed while OFF. Both local warnings
changed from Monitoring to Inspection recommended, not just a retained warning:

| Service | Offline product ID | Source assessment time | Backend receipt after ON |
| --- | --- | --- | --- |
| Brake | `355dc763-4f47-5197-8f6d-3350f886ee1c` | 19:59:08.455 | 20:03:30.494 |
| Brake | `afb12a92-e5ac-5f38-9022-ccf276566425` | 19:59:41.260 | 20:03:30.596 |
| Tire | `97402915-df0d-5535-bde9-7b5d4076262a` | source window ended 19:59:39.575 | 20:03:05.789 |

Read-only guest evidence found these products in local durable outboxes. Brake
model score/wear was 32/68; Tire score 66. Tire's persisted request matched its
new assessment and Gateway APPLIED while still OFF. The native panel showed both
new recommendations. No service/VDP restart or policy change was used.

ON was recorded at 20:03:03.832. Tire's assessment arrived about 1.96 s later;
Brake's two assessments arrived about 26.7 s later under normal retry/backoff.
Presenter showed Delivery pending during that wait, not false delivered success.
By 20:03:45 both current function reports showed RECEIVING and queue zero; the
20:04:04 direct guest inventory also found zero files across all three outboxes.
Old history remained, with 5 Brake and 2 Tire assessment IDs. This proves the
bounded offline products' delivery, not an exhaustive all-message audit or
arbitrary-duration offline/power-loss qualification.

## Retained controller reboot recovery

The normal `vm stop` guard refused a selected vehicle before mutation
(`CURRENT_VEHICLE_REQUIRES_PARK_OR_DETACH`). It was not weakened. The explicit
engineering reboot test instead exercised the already accepted guest-reboot
recovery contract via `systemctl reboot`, with physical Safe Stop, empty queues
and external ON. This is a guest reboot, **not** a full QEMU off/on or host
laptop sleep/wake test.

Boot ID changed from `13df8217-8779-425d-a18a-0913c083b44f` to
`0c25fcdd-1b95-49f5-990e-36216c3c5083`. The Presenter-owned worker automatically
restored the same attachment from 20:05:36.577 to 20:05:50.805 (14.227 s),
ending READY_SAFE_STOP. No manual Connect, provisioning, model Reset, new actor
or Autopilot command was issued. Unit, Node, source run and assignment generation
5 remained unchanged. Both persisted producer epochs and assessment IDs survived.

During recovery VDP honestly reported NOT_READY / absent mTLS projection. Its
same process subsequently became READY/LIVE. Native advisory was still
Unavailable at the 20:06:03 observation, then both recommendations returned;
route-restoration completion is not conflated with complete advisory readiness.
CM had one controlled endpoint-restoration restart (PID 1065→1364), not a crash
restart; SM 1127 and VDP 1154 retained their first-boot PIDs. All NRestarts were 0.

A further real Tire maneuver proved post-recovery function, producing Tire
`238bc975-f799-58df-9005-178ad0631356` at backend 20:06:54.769 and Brake
`913962db-7706-5903-867e-c109cca43d48` at 20:06:56.592. By 20:07:06 both
inputs were RECEIVING, advisory CONFIRMED and delivery IDLE with zero queues.
History now contained 6/3 unique assessments. Native showed Safe Stop, 0 km/h,
LIVE and both recommendations.

Enforcing remained enabled. The bounded post-boot error scan found the existing
getty checkpoint, audit socket and sshd search AVC categories, not a clean
all-domain audit. No VDP/KUKSA-specific denial or SEGV was observed in that scan.

## UI correction, regression and closure

Class A wording correction: Tire's active panel incorrectly described the
brake-event state machine, and the request caption kept saying Preparing / models
unchanged while real maneuvers could update models. A transient stream compile
passed with generic **ACTIVE TEST MANEUVER** and **Real … maneuver · no model
Reset**. Only these two strings changed in the owning native source; existing
caption-layout changes were preserved. Eight native regressions and targeted
arm64 compilation passed. This is not yet a correction to installed Kit 015.

The source/host/simulation/workspace/boot suite passed 119 cases. Distribution
regression passed 267 cases with the explicit process-owner guard enabled and
no skips. Initial harness invocations either lacked the package import path,
omitted the opt-in process case, or selected a venv without `packaging`; these
were corrected without changing the product or weakening a test. The installed
runtime did not use any test-harness environment.

End-of-check closure used ordinary ownership-checked shutdown: physical stop
confirmed, simulator/control/Gateway detached and exited, Test shut down in
4.43 s, both backends stopped with data preserved, workspace closed 20:08:22.845,
then idle UI stop, temporary tab closure and Setup exit. A process/listener
inspection found no owned demo runtime and no listeners at 18080/18600/10022/2000.
Five unrelated Watt containers remained untouched. The Test disk, Cloud identity,
models, histories and release ledgers remain available. No Finish was performed.

## Batched successor: Kit 016 / Setup 025

The two proved host corrections are now packaged together, not installed over
the retained Test. Kit 016 verified all 17,685 files / 35,114,393,996 logical
bytes in 99.27 seconds. Independent manifest:
`d5e14055ae0fb2d5693909ce0059eca17a26fc8bb542038eef314d2406bb296d`.
Only `source.py`, the native Controller caption binary and their enclosing
manifest pins changed. Factory, Game, service payloads and immutable Kit 015
remained unchanged. APFS cloning was used; logical size is not newly allocated
physical disk space. No credentials or runtime state entered the new package.

The Controller's arm64 build completed in 6.352 seconds and passed local
signature/dependency verification. Its caption regression is also registered
with the permanent CMake test set. Small canonical build inputs were aligned
after full candidate verification, with predecessor copies retained in ignored
engineering evidence; installed package bytes were not edited.

Setup 025 passed its native protocol and embedded-bootstrap checks with the
previously authorized stable Apple Development identity. Binary SHA-256:
`cc638805e078b422b5d97d5a68ba95a9391f6c6afc34a8d33b8d8931e4da68d5`.
This is a local development-signed preview, not Developer ID/notarized
distribution. The following continuation records its subsequent native checks;
the build result alone did not establish installation or cold-start acceptance.
The 267-case distribution gate was rerun against the final pins without skips.
Documentation/whitespace checks pass (319 Markdown documents, 662 stable
identifiers, 38 diagrams).

The normal retained-run selection guard is not a defect or permission to remove
state. Installation into the package store and selection for a separate empty
instance do not require Finish of the retained Test. The earlier suggested
dependency on Finish was unnecessarily restrictive; use these already accepted
independent operations for unaffected qualification. Do not silently rebase the
retained VM, edit its selection or treat Kit 015's live result as proof that Kit
016 has run. Published software versions remain reusable; these host-only
corrections do not require another service/Factory/Game build.

## Non-destructive same-host continuation

The operator reaffirmed autonomous execution of the accepted route. Setup 025
was opened directly and its ordinary Check / Install actions used the existing
volume-bound store and a separate empty private-data destination. The retained
Kit 015 Test was not selected, started, provisioned or removed.

Full native installation completed at 20:43:12 UTC, with an observed upper bound
of 347 seconds from the click (including observation intervals). The committed
receipt reports `reused: false`, 17,685 verified files, 35,114,393,996 logical
bytes, `INSTALLED_NOT_ACTIVATED`, no copied operator data, no Cloud access and
no runtime/selection changes. Its staging transaction was removed normally.
Closing the window during copying produced an explicit wait warning; dismissing
that warning continued the same transaction, without duplicate execution.

Private preparation selected Kit 016 at 20:45:14 UTC in a separate empty
instance, with an observed upper bound of 143.569 seconds. First Open through
Setup 025 passed in at most 23.843 seconds; repeat Open retained the same server
and native window owners. Neither action created a vehicle journal or inherited
credentials, a Unit, VM, backend results or model state. Installed read-only
isolation checks passed with network, developer-tree and Homebrew reads denied
and installed-package writes denied. The retained Test's journal and selection
hashes remained unchanged, and its normal selection check still rejected
`INSTALLED_CURRENT_RUN_RETAINED`.

The native repeat exposed stale completed-step advice saying the window could
close while Open was busy. A transient native compile/protocol proof passed;
the minimal source fix hides completed-step advice for the busy interval, without
changing the close guard. Setup 026's real busy state verified the correction.
The distribution suite then passed 268 cases with no skips.

Setup 026 cold launch from its verified read-only DMG opened one Presenter but
reported `PRESENTER_NEEDS_ATTENTION`. A subsequent read-only layout observation
confirmed all three owned Presenter surfaces and verified z-order. An explicit
idempotent repeat passed with the same server/window PIDs, without a new consent
or permission change. That repeat does not retroactively pass the cold attempt.

The preserved empty-instance window record showed three recovery attempts even
though only the not-yet-created simulator/control surfaces were absent. A
deterministic in-memory proof reproduced this unnecessary retry condition. The
minimal correction retains those absence findings and incomplete full-workspace
status, but retries only actual Presenter problems until a simulator source
exists. Missing Presenter windows still retry within the existing bound;
permission/ambiguity failures, owner/generation checks and z-order remain strict.
Source first/repeat/restart and negative tests passed: 42 workspace cases. This
proves the unnecessary recovery defect, not by itself the full cause of the
native cold observation warning; installed cold qualification remains required.

The completed Kit 016 checks were closed normally, including Setup exit,
workspace close at 21:03:45 UTC and idle server stop. Both owners exited and
the Setup 026 DMG was detached. No retained-Test lifecycle action occurred.

### Corrected empty-Presenter candidate

Kit 017 changes only `workspace.py` relative to Kit 016. Full transfer
verification passed for 17,685 files / 35,114,394,248 logical bytes in 114.72 s.
Manifest: `97b29b3792bd9a05a51f735ec05f7100c19290f4ce19d763daee5d16204108e7`.
APFS cloning retained all predecessor bytes; Factory, Game, services and native
binaries are unchanged. No runtime credentials or state were copied.

The initial broad-suite invocation used system Python and the tool sandbox;
missing optional SDK imports and denied local socket/process fixtures made that
run invalid as a product gate. Repeating with the project's packaged Cloud
Python and normal local fixture access passed 1,335 cases in 189.285 s, with
two `qemu-io` cases skipped. Both were then explicitly run using the existing
test tool and passed in 5.742 s; this does not add Homebrew to the installed
runtime. The final-pin distribution gate passed 268 cases with no skips in
7.413 s. These are source/fixture checks, not a fresh vehicle E2E.

Setup 027 uses the same authorized Apple Development designated requirement.
Its executable SHA-256 is
`6987cdba2099c7e7f9d676b40324c6b9e6f4235f9b185d61c460978196a6b328`.
Native protocol, embedded bootstrap and mounted strict/deep signature checks
passed. The read-only DMG includes an English standalone quick-start companion;
SHA-256 `944893105cbffc2fee8f073fd3acff4fd9929f3c320a2240cf78159172ef7ed0`.
No notarization or external distribution claim follows from this local build.

### Host-app interruption and authoritative reconciliation — 30 September

The ChatGPT desktop log ended at 21:19:24 UTC on 29 September. macOS recorded
its process connections disappearing at approximately 21:19:26 UTC (23:19:26
Europe/Berlin). Repeated `ResizeObserver` interface errors preceded that point,
but no fatal exception, exit reason or fresh matching crash report was found in
the bounded logs inspected. The cause is unresolved; these errors do not prove
causation. The host did not reboot. The new ChatGPT process started at 05:03:39
UTC on 30 September; its subsequent update download cannot explain the earlier
interruption.

Native Setup survived independently. Kit 017's committed installation receipt
is dated 21:25:49 UTC on 29 September: 17,685 files, 35,114,394,248 logical bytes,
`INSTALLED_NOT_ACTIVATED`, no Cloud access, copied operator data, runtime change
or version selection. The resumed UI confirmed completion; installation was
not retried. Prepare then selected Kit 017 for the existing empty instance at
revision 2, retaining Kit 016 as previous and preserving the instance identity.
No vehicle journal was created. The retained Kit 015 Test's selection and
journal hashes remained unchanged.

The first native Open of Kit 017 created one server and one Presenter but still
returned `PRESENTER_NEEDS_ATTENTION`; this is not a passed cold launch. The
persisted placement at 05:12:30 UTC has attempt 0, `retryPending: false`, all
three Presenter surfaces at their requested geometry and verified z-order.
Only expected absent simulator/control/dashboard findings remain in that
placement. Thus the unnecessary empty-instance recovery was removed.

A subsequent read-only observation at 05:12:53 UTC saw the available display
height change from 1220 to 1225 pixels. Backdrop and browser remained at their
previous requested heights, producing exact 5-pixel geometry discrepancies;
the header and z-order still passed. This identifies a separate changing-display
observation boundary, not a proved cause of ChatGPT termination. No tolerance,
permission or security check was loosened, and no blind Open retry was made.
The remaining cold-launch issue is preserved for targeted diagnosis.

Workspace close completed at 05:13:52 UTC, followed by idle-server stop and
Setup exit. Process inspection confirmed that both runtime owners and Setup
exited. No VM, simulator, backend or Cloud lifecycle action was performed.

### Packaging and documentation observations

The same unchanged Setup 025 app and build receipt were packaged into a local
read-only DMG: 40,092,896 bytes, SHA-256
`ff2799f158ecb508c8abf0c32bb17716c228c57ee86a4dbb70a762055189c245`.
Image verification and mounted strict/deep signature verification passed;
the mounted executable hash matches the Setup 025 hash above. The 32.7 GiB
runtime remains a separate input, not duplicated in the small image. The
operator guide remains a separately maintained release companion. This is
engineering packaging, not notarization or external distribution approval.

The current package's own dependency records identify missing notice entries
for `dtc-1.8.1`, `glib-2.88.3` and `sqlite-3.53.4`. Host native/OpenSSL/Cloud
native records still explicitly mark corresponding-source review required.
Host build provenance contains local builder paths; the application source
base is recorded with per-file bytes, but the cumulative changes are not yet
a published reproducible source checkpoint. These are concrete Block C/E
release-material gaps, not runtime dependencies on those paths and not legal
approval. Preserve immutable candidate bytes and resolve these together before
the distribution artifact/signing gate; do not trigger another runtime build
for an evidence-only observation.

The old Kit 007 operator page is now explicitly historical and points to the
current first-use guide. This is an editorial correction, not an installation
contract change or a new delivery plan.

## Explicit remaining gates

- The [30 September continuation](installer-first-use-2026-09-30.md) closes the
  changing-display Presenter defect and actual current-account enrollment on
  Kit 019 / Setup 029. The packaged CARLA cold-start wait and complete ordinary
  first Create still await live qualification; do not treat the older Kit 017
  failure as the current candidate's result.
- The retained-run selection guard remains authoritative; packaging is not
  permission to erase this Test or call a blocked update successful.
- A new email is unnecessary for existing accounts. Actual OEM/SP certificate
  issuance, native password entry and reuse passed in the continuation; complete
  ordinary first-Create integration, clean native macOS, whole-runtime
  distribution signing/notarization and redistribution remain open gates.
- VDP-TIMEOUT-01 remains deferred. No claim of zero status flicker from continuous
  frame capture, arbitrary offline duration, cold-offline boot or nonempty-queue
  power-loss durability is made.
- Finish for this exact Unit needs its separately scoped action-time approval.
  This receipt closes the listed functional checks, not stages A–E or release.
