<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native UI runner mechanical qualification

- Date: 12 October 2026
- Status: Mechanical pilot PASS; normal package installed; live vehicle gate pending Test replacement decision
- Review branch: `codex/presenter-human-friendly` in both source repositories
- Gateway source: `e67657033a81a390caf55ee30d5b98ff12cdf39c`
- Target: Dedicated Apple Silicon M1, macOS 27.0.1, internal storage

The signed local runner delivered real mouse input to all five semantic
Driving Control buttons before and after moving/resizing the window. Both
autonomous campaigns passed 21 stages in about five seconds. Invalid targets
were refused without input, and both owned apps closed normally. This proves
the input/layout mechanism, not vehicle motion, release delivery or full E2E.

The [research and authorized design](../planning/active/work-packets/native-ui-runner-pilot.md)
defines the semantic-ID contract and separate live gate. Main, the installed
immutable package, persistent Test, VM, credentials, shared Docker and heavy
CARLA/Factory inputs were not changed by these campaigns.

## Accepted execution

The fixture compiles the exact production `ControlView` prefix from
`carla-ego-runtime/tools/KeyboardControl.swift`. Its callbacks record
`fixture=true`, the action ID and `mouseDownObserved=true` only from the normal
production mouse dispatch. It has no simulator, VM or Cloud connection. The
runner cannot use a fixture callback as a real vehicle-result observation.

The executor resolves each unique Accessibility ID in the exact signed
fixture process, reads its current frame, requires enabled/foreground state,
checks system-wide hit-testing for obstruction and rechecks identity/geometry
before one Quartz mouse down/up. It records intent before dispatch and an
exclusive correlated receipt afterward. No AXPress, Gateway RPC or mutation
API substitutes for a mouse event in these tests.

The operator explicitly approved the new signed Native UI Runner Accessibility
client and completed macOS administrator authorization in the system dialog.
The repeat campaign used the same signed binaries without another permission
prompt. No SSH, Full Disk Access, screen-recording or other permission setting
was changed by the pilot.

## Results and measured durations

| Gate | First campaign | Final repeat |
| --- | ---: | ---: |
| Ordered mechanical stages | 21 PASS | 21 PASS |
| Complete worker duration, including fixture launch and closure | 5.075 s | 4.661 s |
| Measured mouse actions, five before and five after transformation | 10 | 10 |
| Median click stage, including receipt and callback observation | 108.5 ms | 106 ms |
| Click stage range | 53–168 ms | 55–113 ms |
| Fixture and runner closed | PASS | PASS |
| Owned pilot processes in final independent process inventory | 0 | 0 |

The 21 stages cover semantic inspection, the ten clicks, movement/resize,
disabled, missing, duplicate, obstructed and minimized targets, unsupported
action, wrong executable digest, wrong application process and repeated polling
of an already receipted request. Each negative case required both
`inputDispatched=false` and no new fixture callback.

An additional M1 check called the final worker with its already completed
campaign: it returned `CAMPAIGN_REPLAY_FORBIDDEN`, preserved the original report
byte-for-byte and left zero pilot processes. Unit tests additionally prohibit
writing a report outside a verified root and passing a blocked inspection or
unconfirmed mouse effect.

The final targeted build took 10.029 seconds across compilation, signing,
signature checks and the pure Swift request-parser test. Development-side
Gateway native unit coverage passed 10 tests in 22.228 seconds; qualification
guard coverage passed 7 tests. No development-Mac GUI/live acceptance occurred.

One-time permission handling, compilation, transfer, model/tool round trips
and human authorization are outside the worker durations. Callback observation
time is measured after receipt retrieval and is not event-to-callback latency.
The five-second mechanical campaign does not replace real controller/CARLA
startup, maneuver execution, installation settlement or independent physical
and backend-result checks. It cannot be compared as a full-E2E speedup against
the [original campaign totals](ui-qualification-timing-2026-10-12.md).

## Evidence and source pins

Compact private reports are retained under
`.local/remote-qualification/m1-native-ui-pilot-20261012/` and
`.local/remote-qualification/m1-native-ui-pilot-20261012-repeat/`.
The candidate is the small `native-ui-pilot-20261012-r2` build; it is not a DMG
or an installed product release. Both campaigns verified signatures and exact
executable digests on M1 before execution.

| Input or executable | SHA-256 |
| --- | --- |
| Production KeyboardControl.swift | `1917a15524badeb292016086c7a79200c4575b392ba4b1aca786d90c0cb37028` |
| ControlFixture.swift | `3d41b18bef435499c7c73eb5a8a99e380354ae885fe4c111f0846653e4d1f6a1` |
| NativeUIRunner.swift | `3f62ac43587a021dec1131d970f6091723bf618e98441b2fd0de8cdede42b48d` |
| Signed ControlFixture executable | `1411f304191e5fdd45950cf3f3d05856ca64f1494dfd0c01a35568e18ea9be09` |
| Signed NativeUIRunner executable | `eca28dbc3db9cb518826d7abd7817b6bb3eb4980d7deb623816cf89ebf687399` |
| Final repeat worker | `da6e14f743ed78f12c8705983010a3d810ad6b5989a098269672eb48b2f27bc2` |

No reusable credentials, raw product responses or browser profiles enter this
receipt. Permission state is not inferred from an old report: the repeat
client freshly reported READY before execution.

## Live integration checkpoint

The live connection is implemented on the review branch, with the bounded
`native-controls` scenario, signed executor profile and distinct mouse receipts.
Production window identity is included in Gateway commit
`b4c505561f9d2bcdf75ee322f973c85d4b18380d`. The normal product package records
integration source `3f1fdbe6576a821f0cd045353fde75ff13829fc3`; later qualification
adapter changes are outside its product payload. Native controls, source journal
and backend evidence remain separate authorities. A backend product alone is
insufficient: require a new same-source completed maneuver receipt as well.

| Artifact / gate | Observed result |
| --- | --- |
| Normal package SHA-256 | `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c` |
| Complete DMG SHA-256 | `5e0dbf77f6b48e9efcaee8a38b85157dd691c0bb11369f316e5919fe5fa6f719` |
| DMG size | 14,165,529,112 bytes |
| Driving Control compilation | PASS, 3.037 s |
| M1 media transfer/consumer verification | PASS, 219.082 s |
| M1 signed media mount | PASS, 72.451 s |
| Normal package installation | PASS |
| Retained-run selection | Refused by existing contract; no migration attempted |
| Separate private instance selection | PASS |
| Existing Docker image availability / certificate references | PASS |
| Initial M1 Cloud access gate | BLOCKED; staging timeout and public-internet DNS failure |
| Cloud check after network recovery | OEM/SP and association READY; Test verification set CONFLICT |
| New vehicle / new releases / live native input | NOT CREATED / NOT PUBLISHED / NOT DISPATCHED |

Installation initially refused an 8,196-byte Finder `.DS_Store` entry in the
package-store root. Read-only checks proved no successor installation/staging
had started. Preserve that metadata outside the store, retain the refusal and
perform a new journalled normal install. This is qualification housekeeping,
not a fix or relaxation of the installer's unknown-entry guard. Human-friendly
Finder-metadata handling remains a separate installer issue.

The earlier Test, VM, Unit and history remain unchanged. Installed initialization
and selection both forbid retained automotive runs. The successor uses a new
private M1 instance, not a moved/deleted journal or an unqualified upgrade. Cloud
access failed before creating a new Test. Private receipts retain the failed
attempts, preserving observed facts rather than relabelling them PASS.

After the operator restored internet, a journalled Cloud check completed in
11.962 seconds and stopped at `CLOUD_PREREQUISITES_NOT_READY`. The signed Setup's
read-only projection confirmed both roles authenticated and all other checks
READY. The conflicting verification set is
`3e2d6c28-7112-421a-912a-06b440470df6`; its sole member is the retained Test's Unit
`20174976-c230-4e70-a7c5-8133a840f262`. This is the expected account-level occupancy
guard, not a network, certificate or native-runner defect. The isolated local
instance plan did not account for that shared Cloud boundary.

The retained Test `b86da97e-f54c-43ed-b97a-dade76dd81a9` and its earlier package
selection were freshly confirmed unchanged. No new Test was created, no releases
were published and no live native mouse input was submitted. Final observation
confirmed zero owned demo processes/listeners and zero running containers, the
same Docker Engine, detached owned media and a closed temporary display assertion.
The fixed Cloud/check/cleanup projections remain in the private baseline records.

Current local source gates passed: 10 Gateway native tests, 10 qualification
native tests, 13 Python UI guards, 14 JavaScript scenario guards, 69 journey
tests, 13 campaign tests and 5 UI build tests. The new signed executor's pure
request assertions and normal native/web/Setup builds passed. These do not
qualify live input on the installed successor.

The owned DMG was detached and temporary display assertion closed. Final M1
observation found zero owned demo processes/listeners, preserved Test data and
the unchanged shared Docker Engine. SSD build scratch was cleaned by its normal
contexts; retain the immutable package, DMG, small executors and compact private
records. Main, Production and the video repository remain unchanged.

## Autonomous scenario checkpoint

The operator authorized a single-entry native-controls campaign and the general
scenario-first execution rule on 12 October. The
[campaign contract](native-controls-campaign.md) records its private input,
normal-owner preparation, semantic browser/native actions, result checks and
mandatory finalization. The current rule is also in the shared development
instructions, repository `AGENTS.md` and operating policy version 1.6.

The first real M1 campaign stopped in 4.883 seconds at desktop readiness. After
the report was corrected to retain partial observations and collect independent
Cloud prerequisites in the same read, a new bound campaign stopped in 9.885
seconds. It freshly reported desktop `LOCKED` and
`TEST_UNIT_SET_HAS_OTHER_UNITS`; both OEM/SP roles and the other Cloud checks were
READY. This is a negative preflight proof, not a passing live-control campaign
or a full-E2E speed benchmark.

Both runs used the installed successor, existing verified media and published
releases. No media mount/transfer, vehicle preparation, publication, retirement,
native permission client or live UI input was attempted. The final report marks
preparation and native UI NOT_RUN, native controls NOT_QUALIFIED and full E2E
NOT_COMPLETE. The M1 read found zero owned demo processes/listeners and the same
shared Docker Engine. The retained Test remains unchanged.

Private reports are retained under the `m1-native-controls-campaign-20261012`
and `m1-native-controls-campaign-20261012-r2` record directories. The earlier
failed report and plan were preserved; the corrected read-only proof used a new
campaign identity rather than replaying an uncertain action. Current unit gates
passed 26 native/campaign tests, 13 Python UI guards and 15 JavaScript scenario
guards; documentation validation passed with 354 Markdown documents. The
permission-only client and complete positive live path remain unqualified until
the real prerequisites permit them to run.

## Remaining integration gate

Stages 1–4 remain complete and network access is restored. The live gate requires
a decision about replacing the retained Test: the same OEM verification set
cannot accept the proposed independent first-use instance while that Unit remains
present. If replacement is selected, use normal Finish, confirm retirement, resume
the existing fresh-instance API baseline with published releases, then execute
the visible `native-controls` scenario. Otherwise retain the previous Test and
defer the live gate. Exact installed-payload/Test/session/action binding and
independent physical/product postconditions are implemented but not yet
live-qualified. No CARLA, Unreal or Factory rebuild is needed.

Until that separate M1 gate passes, the existing live scenarios retain their
CUA-only native witness requirement. Native Setup/WKWebView, first-user input,
repair, release qualification and complete live E2E remain separately scoped.
