<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Presenter Launch — 28 September 2026

- Status: Source corrections and negative UI passed; final native success awaits OS consent
- Version: 1.1
- Prepared: 2026-09-28
- Owner: Demo Solution Team
- Contract: [native setup v1.3](../../contracts/distribution-installation/native-setup.md)
- Plan: [installation and reproducibility](../planning/active/installable-distribution-and-reproducibility.md)

## Scope and exact candidate

This resumes the [travel checkpoint](installed-pause-2026-09-28.md), after the
completed [installed functional E2E](installed-clean-e2e-2026-09-28.md). It tests
the separately authorized native **Open demo** action, not another serial
release/E2E cycle. No Finish, package selection, provisioning or driving action
was performed. `VDP-TIMEOUT-01` remains explicitly deferred.

- Source base: `22ee79e0e21709de34803c6db20047847138eba0`, with the recorded
  uncommitted installer source/tests and documentation; no commit or push here.
- Setup preview: `SDV-Work/AosEdge-SDV/setup-preview-010-20260928`.
  **Preview 010 is not Kit 010**; this installer still pins Kit 009.
- Native executable SHA-256:
  `160d9406b27a5fc3e1f4ff4a827299082155ce3c6904eefaa862cdb2533bcb45`.
- Selected Kit 009:
  `f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`.
- Existing instance: `~/SDV-Lab-Clean`,
  `191c70c8-6cb5-487d-9be0-3f06691c9812`; selection revision remains 1,
  previous version remains null.
- Work volume UUID rechecked:
  `591578E3-8196-4B44-A575-CEC76B406789`.

The build receipt beside the preview contains the exact source digests and
2,430 authenticated bootstrap files. Only the native setup target was compiled,
with the existing network-denied compiler guard. Ad-hoc local signing is not
Developer ID/notarization or redistribution acceptance. Factory, CARLA and
service packages were not rebuilt or modified.

## Source correction and automated proof

Before building, fixture tests reproduced permissive missing session fields
and acceptance of Presenter surfaces with mixed process owners. Minimal
transient replacements passed before source consolidation. The final source:

- requires explicit idle/uncertain/busy fields and one owned native host;
- holds the existing instance writer across the child socket-bind interval;
- waits for HTTP readiness by bounded reads, without another process start;
- refuses redirects, foreign/partial ports and changed owners/selections;
- submits one existing workspace-restore identity, reconciling response loss
  without POST replay; and
- preserves any opened server/windows on timeout, without claiming readiness.

Results:

| Gate | Observed result |
| --- | --- |
| Launch, native bridge, existing-access fixtures | 50 tests passed |
| Installation/version fixtures | 66 tests run, 65 passed and one explicit process-inspection test skipped by default |
| The skipped process-inspection test, explicitly enabled | Passed; detached consumer blocks while holding a temporary file, then clears after normal test-process termination |
| Compiled native protocol/deadline self-test | `SETUP_NATIVE_PROTOCOL_PASS` |
| Build signature/bootstrap checks | Passed in build receipt |

Final documentation validation passed for 310 Markdown documents, 662 stable
identifiers and 38 Mermaid diagrams. `git diff --check` passed.

An initial local test-runner invocation used the wrong import search path and
one incorrect module name; it ran no product test. The corrected private
Python 3.12 isolated invocation produced the results above. This harness error
did not trigger another build.

## Actual native-window checks

The source-kit field remained empty; returning to an existing installation
required only its private-data directory. All five action buttons fit and
remained responsive. Times below are UTC on 28 September; local time was UTC+2.

| Case | Intent / authoritative operation | Result |
| --- | --- | --- |
| First native Open, previously stopped Presenter | Click 18:54:25.468; workspace restore 18:56:20.669–18:56:25.394 | Setup reached its 120-second deadline; reported attention, not success. Server/windows were preserved. Cold gate failed. |
| Explicit idempotent repeat after reconciliation | Click 19:00:50.802; restore 19:00:57.362–19:00:58.365 | Native UI reported **Presenter opened**; same server and host PIDs, no duplicate. Terminal UI observed by 19:01:26.759. |
| Missing private-data directory | One explicit Open | Safe error `SETUP_OPERATION_FAILED`; no directory or restore job created; existing Presenter unaffected. |
| Quit/reopen Setup, then select existing data | Click 19:03:09.237; restore 19:03:16.100–19:03:16.983 | Native UI again reported **Presenter opened**; no source-kit re-selection needed. Terminal UI observed by 19:03:32.264. |

The last-observed UI times are observation bounds, not measured helper
durations. Workspace operations reached PARTIAL because simulator/control
windows were intentionally stopped. Presenter geometry and ordering were
verified; setup correctly distinguished this from full demo readiness.

Exactly one HTTP/native server (PID 47891) and one Presenter host (PID 47978)
were preserved across repeat and Setup quit/reopen. The three explicit valid
Open intents produced exactly three workspace-restore jobs; there was no hidden
retry. Final operation state was idle, not uncertain or recovering.

The native Presenter is an unregistered standalone executable: direct CUA app
selection returned `Invalid app`. No second launch was attempted through that
route. Native geometry/owner verification came from the product observer;
content was additionally inspected through the existing Presenter browser tab.

## Open cold-start finding — SETUP-COLD-OPEN-01

At 18:55:57.519, about 92 seconds after helper creation, a bounded native stack
sample found Python `os_open` waiting in kernel `__open`, not `flock` or hashing.
The exact filename was not established. The server started at 18:56:17; native
windows followed at 18:56:20. Thus the delay preceded server/window startup and
consumed nearly all of the helper's two-minute budget. The restore completed
approximately at that deadline, so a final success could not be established.

This resembles the earlier [native file-open delay](installed-first-use-2026-09-28.md#native-cold-start-delay-remains-open),
but an identical root cause is not proven. A bounded TCC log query for the two
exact process IDs returned no entries; it neither establishes nor excludes a
permission/OS-service cause. No lock deletion, permission bypass, broader file
access or arbitrary deadline increase was used. Warm/reopened success does not
close this finding.

The next diagnostic at that checkpoint was to add only fixed non-secret boundary markers around metadata
open/volume/lease verification in a separately identified diagnostic candidate;
capture one native first-use attempt and distinguish the precise open boundary
from OS attribution before selecting a fix. Do not edit the retained immutable
kit or recreate its Test to investigate this.

Two presentation follow-ups were recorded: missing-instance failure used a
generic diagnostic, and the existing workspace panel can show automatic
layout retry wording while the simulator is intentionally stopped. Neither is
evidence of a running vehicle or completed simulator readiness.

## Same-day continuation: removable-volume consent and final observation

The diagnostic-only preview 011 added fixed file/volume/lease boundary names,
duration and errno, without filenames or contents. It deliberately stopped
before server reuse/start, so it could not submit a workspace or Cloud action.
The immutable installed Kit 009 was not patched.

At 19:16:29.578 UTC the diagnostic native intent began. The initial store metadata
open took **4.230228 seconds**; subsequent volume discovery took approximately
0.128 seconds and leases completed in microseconds. The read-only diagnostic
finished at 12.316 seconds. Informative TCC events showed the corresponding
removable-volume prompt at 21:16:30.301594 local and response at
21:16:34.494697 local: **4.193 seconds**, overlapping that exact open. This
establishes OS consent as the cause of this observed wait, not a slow SSD read
or a writer-lock wait. It does not retrospectively prove every earlier long open
had the same cause. The earlier empty log query omitted informative/debug events;
its negative result must not be treated as evidence against TCC involvement.

Apple documents that first access to removable media can require consent, with
the app's [removable-volume usage description](https://developer.apple.com/documentation/bundleresources/information-property-list/nsremovablevolumesusagedescription)
explaining the purpose. The source now supplies that description and separates
private-instance verification, external-storage access and program verification
in the native UI. Missing-instance and denied-file-access errors now have
actionable, redacted explanations. No permission is granted by code, no TCC
database or security setting is changed, and the overall 120-second deadline
is unchanged. Four red/green regression tests plus the native protocol self-test
cover the correction; the targeted setup suite passed 54 tests.

Preview 012 (executable SHA-256
`71979fef0250a92fa044e086e014d09919f97d871b2b1c260c85639ae0ca94c0`)
showed the explicit SSD-consent guidance. Its first Open began at
19:24:42.197 UTC; TCC recorded a pending removable-volume prompt. The operator
confirmed granting it. The preserved server completed one restore at
19:26:36.014–19:26:38.659, but setup reached its overall deadline during final
qualification. The native attention state correctly preserved the existing
Presenter. No automatic launch or POST replay occurred.

### Final observation race — SETUP-LAUNCH-OBSERVATION-01

After authoritative reconciliation, one explicit preview 012 repeat began at
19:30:29.558 UTC. Its restore completed at 19:30:53.296–19:30:56.466, then the
helper returned `CURRENT_RUN_BUSY` while performing its final status check.
The automatic workspace-recovery worker was still completing the accepted
layout request; its journal reached attempt 3 / `retryPending: false` at
19:31:05.495. CARLA and control were intentionally stopped. Thus a successful
restore did not imply that the shared writer was immediately available for the
separate observation. This was not a stuck VM or another operator mutation.

A transient in-memory replacement passed the exact race, deadline, changed
session/owner, competing operation and non-retryable error fixtures before source
consolidation. Final surface observation now waits at most 20 seconds inside the
unchanged overall deadline, rechecking process/session and operation interlocks.
Only read-only observations repeat. Restore, process start and lifecycle actions
are never replayed; no lock is removed or bypassed. Four new regression tests
cover this boundary. All **242 distribution tests passed**, including the
explicit local process-inspection proof with no skips. An earlier broad-suite
invocation used host-runtime Python, which lacks the test-only `packaging`
dependency; the corrected invocation used the existing packaged Cloud Python.
Nothing was installed into either immutable interpreter.

Preview 013 carries both corrections and still pins Kit 009. Executable SHA-256:
`7323281fc0eb23380316caabee66ab2c54e28e3e1865fb69fab6df3fb08bb831`.
The native protocol self-test, authenticated 2,430-file Python bootstrap,
embedded-helper startup and ad-hoc signature checks passed. Only the small
setup app was rebuilt. Live outcome is recorded below after reconciliation.

Preview 013 began Open at 19:35:50.341 UTC. Its one restore completed at
19:36:06.185–19:36:08.517; the busy-lock error did not recur. The first final
surface observation returned attention. Later authoritative geometry/ordering
was correct; a fresh installed CLI read confirmed it without moving windows.
Scoped TCC evidence confirmed Accessibility access was allowed. The exact
contents of the first transient surface snapshot were not captured, so they
must not be invented or described as a proven permission denial. Inspection
found that observation still returned its first incomplete snapshot immediately,
even with time remaining. A deterministic incomplete-to-valid fixture reproduced
that early exit; the transient replacement passed before source consolidation.
The same bounded observation window now waits for verified Presenter surfaces,
or returns the last unconfirmed observation as attention at its deadline.
Persistent wrong geometry never becomes success. This does not replay a restore
or increase the overall native deadline.

An actual missing-folder negative also exposed an incomplete earlier test double:
local preflight permits a missing folder for installation, whereas Open must
reject it. The launch-only existence guard and a real temporary-directory test
now cover that path before runtime execution. The first correction's mocked
FileNotFoundError test alone did not establish this behavior.

Final preview 015 (preview 014 was built but not used for native acceptance)
contains these source corrections, still against unchanged Kit 009. Executable
SHA-256: `66e781e744d2c89dfa27a353f00c8e20164c3ff0e1882f804dd3847e683b2411`.
All **245 distribution tests passed with no skips**, including the opt-in local
process-ownership proof. Targeted native compile/protocol, authenticated bootstrap,
signature and embedded-helper checks passed again.

### Final-candidate UI checkpoint

- Preview 015 first Open intent: **19:44:11.965 UTC**. TCC recorded the new
  removable-volume prompt at **21:44:12.857345 local**. The native UI explicitly
  showed external-storage consent waiting. The 120-second deadline then returned
  attention and preserved the existing demo. No helper remained and no new
  workspace job was submitted: the count stayed at six prior valid intents.
- A subsequent missing-folder negative on this exact preview passed visibly:
  `SETUP_INSTANCE_NOT_FOUND`, with instructions to select existing private data
  or prepare a new installation. The absent target remained absent, and no
  process or workspace action was created. The form was returned to the retained
  instance without resubmitting Open.
- Final live successful Open/repeat/reopened-setup acceptance of preview 015
  remains pending the operator's new macOS consent response. Previous preview
  successes and the 245 passing tests do not substitute for that gate. The
  second consent request is explicitly recorded, not silently bypassed or
  treated as consent for every rebuilt ad-hoc application.
- Presenter server/host remain PIDs **47891 / 47978**, operation state is idle
  and not uncertain/recovering. The Test VM, simulator, services and immutable
  package selection are unchanged by these launch checks. No VDP-timeout work,
  Cloud mutation, model reset, commit, push or release publication occurred.

Evidence in the ignored CARLA build directory includes
`native-open-boundaries-20260928.jsonl`, the transient observation proof and
`setup12-*`, `setup13-*`, `setup15-*` screenshots. The separate 64-MiB targeted
compile scratch was removed after proving zero open handles; source/proof and
candidate build receipts remain. Diagnostic preview 011 is stopped and retained
as a labelled non-product artifact. Previews 012–015 are separate small local
engineering candidates; none modifies the immutable installed kit. Large-build
work remains blocked by the existing internal reserve guard (approximately
86 GiB available versus 90 GiB required); Work still has approximately 561 GiB.

Next after native acceptance: integrate the already-tested service-Prepare
correction into one coherent candidate, close explicit existing-account Subject
reconciliation UX without label-only adoption, then continue first-use/enrollment
and installed lifecycle gates in the accepted plan. New-account enrollment,
clean-Mac and signed distribution remain unqualified.

## Preserved state and remaining acceptance

The Presenter visibly shows **Controller switched off**, Cloud Offline, and the
retained releases VDP 120/V3, Brake 96/V3, Tire 50/V1. Current vehicle remains
unassigned. Source and both backends remain STOPPED from the travel pause;
VM/simulator were not started by Open demo. Test Unit
`ee0a8607-5359-47ee-b5a6-4f50568d2b3a` and Node
`50d8b2c5-4e10-46c2-9335-b5b8598a2aff` remain in the same retained journal.
No model Reset, history cleanup, credential copy, Cloud mutation or Production
change was requested or performed. Presenter reads are not an offline promise.

Small build/test scratch was removed by normal temporary-directory cleanup.
Compact logs and screenshots remain in ignored
`CarlaSim/Build-distribution-stage2-20260926/` (`native-launch-*`). No broad disk
cleanup occurred. Final available space was approximately 86 GiB internal and
561 GiB on Work; the 90-GiB guard still blocks large artifact work.

The warm native entry point is usable, but Stage 3 is **not fully qualified**:
first-use delay, previously disclosed preparation/subject reconciliation, cold
CARLA start, new-user enrollment, signed distribution and clean-Mac acceptance
remain separate gates. Existing E2E results stand with their documented
engineering corrections; they are not automatic clean-install acceptance.
