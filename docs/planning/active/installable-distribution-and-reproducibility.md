<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installable Distribution and Reproducibility Plan

- Status: Accepted planning; implementation and qualification are not complete.
- Version: 1.7
- Prepared: 2026-09-25
- Updated: 2026-10-07
- Owner: Demo Solution Team
- Original source baseline: [demo-v1.1 / Factory .39](../../qualification/demo-v1.1-return-point.md)
- Current candidate: [Kit028 / Setup042 / Factory .41](../../qualification/current-baseline.md)
- Implementation input: [Current implemented architecture](../../architecture/current-implementation.md)
- Operational input: [Current operator workflow](../../operations/current-demo-workflow.md)
- Evidence input: [Documentation audit and open items](../../qualification/documentation-reconciliation-2026-10-07.md)

## Current execution route — updated 7 October 2026

The candidate source checkpoint was published on 5 October. Documentation was
reconciled on 7 October without rebuilding or altering the media. The 4 October
Test was subsequently retired and old M1 installations removed; the verified
DMG was delivered for the user's manual launch, which was not started in the
last recorded disposition. Do not follow retained-run instructions below as
if that Test still exists. Re-observe current state before any later test.

The four separate candidate gates remain native operator journey, moving SOTA,
secure native token entry and target-host installation interruption/repair.
The native Power on gap for a retained stopped controller remains explicit.
No additional live gate is closed by this documentation revision.

This section is the single current execution checklist. The numbered delivery
stages below retain their acceptance criteria. Dated kit/preview notes record
evidence, not separate projects, new approval gates or competing queues of
"next" actions. Do not restart completed work from an earlier checkpoint.

On 7 October the user requested detailed planning for a human-friendly source
and release entry point. The [repository reproduction packet](work-packets/human-friendly-reproduction.md)
expands Stage 4 and the relevant Stage 5/7 work into R1 release definition,
R2 build automation, R3 documentation routes and R4 reproduction proof. It is
subordinate to this plan, not a replacement installer plan or a claim that
those blocks are implemented. This documentation-only task does not reopen
completed runtime checks. The [cross-repository journal](../repository-change-journal.md)
records coordinated changes and publication state without duplicating source
locks or runtime authority.

The user accepted both outstanding Cloud first-use choices on 29 September:
explicit verified exact-object reuse and preserved uncertain enrollment without
automatic replay. The user also reaffirmed end-to-end planning and autonomous
execution inside the approved scope, rather than asking to continue after every
test or internal design detail. Their
[recorded disposition](../../qualification/cloud-first-use-boundaries-2026-09-29.md#accepted-decisions--29-september-2026)
is authoritative; those questions are closed.

On 2 October, the user excluded host Mac sleep/wake (test 6) from the current
qualification scope and requested an installer/launcher usability audit before
further tests. The completed audit covers the delivered DMG and the path to a
working demo; see the
[operator experience proposal](../../research/installer-operator-experience-audit-2026-10-02.md).
The user subsequently accepted the direction and selected this execution order:
audit and clean development-host storage, relocate verified reusable large data
to SDV-Work, assemble a complete single DMG, transfer it to the dedicated M1,
and qualify installation from that media. The single-DMG milestone precedes
the remaining guided-wizard work; it must not be reported as its completion.
Preserve completed evidence and the other remaining gates; controller ignition
remains a separate requirement.

The development disk cleanup and single-media build are complete. Kit 025 /
Setup 039 was transferred to M1 and installed into a new empty store; its signed
Setup worker passed preflight, installation and private-instance preparation.
This is engineering installation evidence, not a passed native operator journey
or a new Cloud E2E result. See the
[complete-media qualification](../../qualification/m1-complete-media-2026-10-02.md).

On 3 October, Kit 026 exposed and helped prove additional guest and service
corrections. Factory .41 and the corrected Brake and Tire sources are now
assembled into Kit 028 / signed Setup 042 for a new installed run. Kit 027
installed but failed before controller creation because its VM manifest still
bound the previous host manifest. Kit 028 corrects that metadata dependency;
assembly and installer preflight now reject it before copying. The operator
explicitly deferred further tuning of short load-sensitive readiness
transitions; no freshness or fail-closed rule changes accompany that decision.
Kit 026's exact owned Test was retired through normal Finish before the clean
replacement. Its reports, credentials and published releases remain, together
with the rollback media. After clean installation, Kit 028's initial Create
stopped at an expired native VM password request before boot or Cloud creation.
On 4 October the reconciled same Test resumed through the ordinary idempotent
Create path and native one-use VM access. All 98 installed scripted checks now
pass: serial versions, actual products/advisories, independent Reset/history,
Return to road, five-minute external OFF and queued delivery after ON, and
same-identity stationary ignition with new products from both services afterward.
Normal shutdown verified zero owned processes/listeners and preserved Test data
and Docker Engine. Native Open demo and simulator-start submissions were
observed; starts completed in 66.17, 63.85 and 63.29 seconds. The latest
continuation also verified the final three-window layout, native Connect in
Manual (7.01 seconds), both services receiving input and displaying retained
advisories, and native Autopilot with observed movement at about 19.5 km/h.
Subsequent computer-use access failed again: read-only OS flags showed the
development host locked at 10:44:05 CEST while M1 remained unlocked. Earlier
tool errors are not proof of M1 lock. Shutdown at 10:46:25 CEST again verified
zero owned processes/listeners and preserved the Test. The remaining native
maneuver, Reset and offline review is incomplete. The returning stopped
Test also has no native power-on action under the current Studio lifecycle;
engineering restoration is recorded separately, not as UI acceptance. Moving
SOTA, secure UI token entry, native operator flow and interruption/repair
remain separate open gates. This is not complete native E2E or release acceptance.
Kit 028 uses its own evidence, not earlier candidates' passes. See
the [current live record](../../qualification/m1-live-journey-2026-10-03.md)
and [candidate checkpoint](../../../workspace/checkpoints/installer-kit-028-candidate.json).

### Where the project actually stands

| Deliverable | Current state | Remaining result |
| --- | --- | --- |
| Stage 0 inventory | Complete in recorded scope | Maintain pins and unresolved release constraints |
| Stage 1 standalone CARLA | Qualified on the development host; M1 rendering, actual maneuvers and corrected native layout observed at Stage 6 | Preserve the accepted Game/API; no further Factory or engine rebuild for the completed host checks |
| Stage 2 portable runtime | Functional evidence exists; VDP timeout explicitly deferred | Preserve the exception; do not restart this workstream |
| Stage 3 installer and first use | Recorded installed results retained; three remaining same-Mac checks explicitly deferred by the user on 30 September | Preserve the open native-access, interrupted-start cleanup and retained-instance selection cases; proceed to clean-system qualification without claiming A/B complete |
| Stages 4–5 reproduction docs and verification | Operator/developer docs, requirements/implementation map and contract status reconciled to Kit028 on 7 October; scripted harness implemented; R1–R4 reproduction packet defined | Implement the release resolver/build entry and prove fresh-clone reproduction; maintain candidate-bound evidence. Documentation does not close native usability/release acceptance |
| Stage 6 clean-system qualification | Kit 028 / Setup 042 / Factory .41 passed all 98 installed scripted checks on 4 October, including serial updates, both services' products, Reset/history, OFF/ON delivery and post-ignition products. Earlier Kit 024/026 evidence is retained; Kit 026 Test is retired and Kit 027 rejected. | Close separate native operator, secure UI token entry, moving SOTA and interruption/repair gates. Restore native access on the development host; M1 itself was observed unlocked. Do not rerun the completed serial sequence merely for UI review. Short load-sensitive readiness tuning and VDP timeout remain deferred. Preserve rollback and evidence; see the [current live record](../../qualification/m1-live-journey-2026-10-03.md). SSD and host sleep/wake checks are excluded |
| Stage 7 release | Not complete | Reconcile deferred cases and distribution gates before an authorized distributable release |

### One route to completion

| Order | Integrated work block | Exit evidence |
| --- | --- | --- |
| A — Finish first use | Complete the accepted contract cascade and implementation for existing OEM/SP access, explicit exact Subject reuse, official registration guidance, secure token enrollment and uncertain-attempt recovery. Integrate dependency/permission checks, Cloud preparation and the existing guarded Presenter/start path. Keep one OEM/one SP, fixed trust and separate installation/access/runtime states. | Complete ordinary operator paths and their negative/restart cases; no developer credential/state inheritance, no hidden replay, no false readiness. No more routine approval stops between contract, proof, source and native checks. |
| B — Qualify installed operation on this Mac | Assemble the corrected small inputs into one candidate, then test actual native first/repeat/cold launch, permissions, layout, selection and lifecycle. Exercise install interruption, corrupt/missing inputs, wrong/missing SSD, repair, update/rollback compatibility, retained-run protection and data-preserving removal. Run the installed functional UI scenario without engineering substitutions. | Source, native and live outcomes kept separate; exact candidate, UI timings, no stale-state oscillation, preserved identities/history/ledger and no duplicate owners. A blocked retained-run update is not reported as a successful update. |
| C — Finish release materials and packaging | Complete the DMG/application, integrity/source manifest, dependency notices and corresponding-source obligations. Confirm redistribution constraints and the available Developer ID/notarization route. Write the operator quick start and separate developer build/reproduction route from the same candidate. This work can proceed while another test runs, without another runtime owner. | One coherent candidate and guide; no chat/history dependency, undeclared runtime, secret, personal path or security-bypass instruction. Development signing is not distribution qualification. |
| D — Clean native installation and E2E | Proceed under the explicit 30 September deferral below using the agreed clean-system route. Install only declared dependencies and execute installation through the full demo with serial version progression, actual maneuvers, offline/online, ignition and scoped Finish. | Exact hardware/OS/artifact identity and complete native evidence; no internal development-tree fallback. Same-Mac isolation and fixture results do not substitute for this gate. |
| E — Release closure | Reconcile code, documentation, test evidence, open exclusions, source pins and artifact inventory. Perform the specifically authorized Git/artifact publication and handoff, preserving demo-v1.1 and necessary rollback inputs. | The obtainable release is exactly the tested one; unsupported/unverified cases are explicit. Do not call the installer finished before mandatory gates pass. |

The installed functional sequence is fixed: Create Controller, start/connect
the simulator, prepare and publish VDP/Brake profiles **one version at a time**
with installation and function checks before the next publication, then Tire V1.
VDP FOTA uses Safe Stop; QM service SOTA does not inherit that restriction.
Verify both backend products and local advisory, independent Reset/history,
Return to road, externalOFF local operation/queued delivery after ON, and
same-identity stationary ignition recovery. Finish is a separately scoped
destructive endpoint, never an implicit installation/uninstall side effect.
Do not repeat completed tests unless changed code or missing acceptance evidence
requires it. Host sleep/wake is excluded from the current qualification by the
2 October user decision; do not report it as passed or supported.

### Execution discipline and intervention boundary

The user's 30 September standing authorization covers this entire staging
test cycle: retire previous owned Tests and their run data, create replacements,
build/sign/publish test releases with the authorized identities, install and
verify them. It includes the retained Kit 015 Test replacement. Do not request
routine confirmation for each test, UUID or release. Resolve exact targets and
apply the [standing staging safeguards](../../governance/rapid-development-and-debugging.md#standing-staging-qualification-authorization)
without weakening product guards or mandatory tool controls. Production,
credentials, source, current Factory and required build/rollback inputs remain
protected. Public distribution is outside this permission.

- Finish each block through diagnosis, transient proof, affected-source tests,
  correction and its acceptance evidence; do not return a routine "continue?"
  question between these internal steps. Update contracts/tests within the
  accepted decisions without requesting the same product choice again.
- Report meaningful progress and failures, not an approval request for each
  helper, test suite, kit number or build. One evidence result does not become
  a new delivery stage.
- Batch known host fixes before a kit build. Rebuild Factory/Game/services only
  if a proven change affects those components. Preserve warm caches and the
  current disk guards; no cleanup merely to produce a new checkpoint.
- If a failure is within the accepted behavior, investigate and fix it. If it
  truly changes scope, authority, trust or lifecycle, present one consolidated
  change request with the alternatives and downstream effects. Do not invent
  permission, silently weaken a contract or treat an implementation detail as
  a new product decision.
- Before live mutation, resolve exact targets and existing authorization. If
  absent, batch the required staging releases, intended Test replacement and
  destructive endpoints into a bounded request at that boundary. Continue
  unaffected local work; do not seek repeated approval for the same authorized
  target/effect or assume generic permission covers a different one.
- Known external interventions are: official registration/email and unavailable
  one-time tokens; macOS-owned consent/authentication; clean-system boot/setup;
  unavailable distribution signing/notarization credentials or unresolved
  redistribution approval; and exact live/destructive/publication authority
  not already granted. These are not ordinary engineering checkpoints.
- Preserve the current retained Test identified in the latest qualification
  receipt until a separately authorized lifecycle transition. Its Brake/Tire
  Subjects remain bound; do not silently adopt, detach or delete them to pass
  installation. Earlier Kit 009 retirement is historical completed evidence.
- Keep `VDP-TIMEOUT-01` deferred and visible. Do not reopen it now or silently
  convert the exception into a passed release criterion.

The current next block is **D**, under the user's 30 September deferral below.
Do not restart same-Mac A/B checks as a prerequisite to this move. Preserve their
open status and the remaining C/E release gates; human interventions above are
requested only when their exact boundary is reached.

### Accepted two Mac qualification and automation approach

On 1 October the user accepted the development Mac as the control/build host
and the separate M1 Pro as the native qualification target. The user also
accepted a small resumable automation harness to reduce repeated diagnostics
and dependence on conversation history. This is supporting work within Stage 5
and block D, not a new delivery stage or completion of earlier open gates.
The [harness](../../../scripts/qualification/README.md) is implemented and tested,
including bounded installed-owner scenarios added after the timing audit. The
[dated M1 receipt](../../qualification/m1-installation-2026-10-01.md) records
execution separately from this accepted approach. Native installation,
dependency setup, credential issuance and E2E require their own evidence.

The observed target has an Apple M1 Pro, 16 GiB RAM, a nominal 512 GB internal
disk and macOS 27.0.1. Recheck the environment at preflight; these observations
are not a supported-hardware claim. The direct Ethernet connection separates
management traffic from each Mac's Wi-Fi internet connection. SSH uses the
dedicated source-restricted key and verified server identity. Screen Sharing
has demonstrated remote mouse/keyboard input using a disposable Calculator
check; that application and the sharing session were closed afterwards.
Successful access does not prove unattended login, installation or operation
under full demo load. Respect the active keyboard layout during text input.

Keep source fixes, builds and the canonical run record on the development
side. Install only the declared demo prerequisites and explicitly inventoried
test tooling on M1. Do not transfer development trees, provisioned VMs, prior
run data or implicit credentials. Inventory shared/global software as well as
the selected user's state: a new local user alone does not prove a clean host.

The [10 October autonomous qualification work packet](autonomous-m1-qualification.md)
extends the existing runner with one media-to-journey command, an explicit
instance/Factory-bound test password profile, partial-Create identity recovery
for cleanup, bounded failure diagnostics and timing. It preserves this delivery
plan and separate native acceptance. Source tests are not installed-candidate
evidence; the older r5 media does not contain these changes.

On 2 October, the user requested script-first qualification and a final UI pass
after functional checks succeed. Use SSH for verified media transfer, mounting,
the signed Setup worker protocol, bounded installed-owner scenarios, diagnostics
and evidence collection. Reuse existing distribution checks, Demo Control owners
and documented lifecycle paths; do not introduce a second installer or runtime
orchestrator. Scripts must not supply hidden dependencies or prepare state that
the ordinary operator journey cannot create.

Complete functional checks and fixes first. Reconcile an interrupted operation
before resuming, then repeat only affected checks unless the change invalidates
broader evidence. Record per-phase duration, outcome and exact candidate in a
resumable checkpoint; do not spend UI time repeating unchanged functional work.
Use Screen Sharing at the final acceptance boundary for the actual operator
journey, permissions, messages, layout and visual feedback. The user may inspect
the screen beforehand. Keep engineering and native results separate: successful
scripts do not prove that the UI is usable, nor do they waive the native gate.

The interface below is the accepted target. The helper implements local
status/report, preflight, verified staging/reconciliation and bounded collection.
Its installed extension binds the exact candidate and Test, observes before
acting, and supports `run local-start`, `run local-stop`, fixed-owner `action`
and read-only `reconcile`. Live stop/start/repeat checks pass on Kit 022. The
original `stop` remains a no-process/no-listener verifier; the installed
`local-stop` stops the controller and backends, not all desktop applications.
Presenter and Setup still require ordinary owner shutdown followed by exit
verification. The user clarified on 2 October that Docker Engine is background
infrastructure: reuse it without Dashboard and stop only demo containers, not
the Engine, at test completion. Engineering adapters do not count as native UI
acceptance.

The `journey.py` runner consolidates the serial scenario into one resumable
command, with fixed product-owner adapters, timing, uncertain-action
reconciliation and automatic demo-only shutdown. Local regression and the
installed host smoke have evidence in the
[runner record](../../qualification/scripted-journey-2026-10-02.md). Subsequent
installed runs and corrective proofs are recorded in the
[3 October live record](../../qualification/m1-live-journey-2026-10-03.md).
The current candidate is Kit 028 / Setup 042 / Factory .41, with fresh records
for installation and the serial deployment/recovery sequence. Historical
functional results remain evidence for their exact candidates, not a new
runner or native acceptance pass. Moving SOTA, secure native entry and the
final UI journey remain explicit separate gates.

| Command | Responsibility |
| --- | --- |
| `status` | Report exact candidate, completed checks, unresolved operations and next step without starting anything |
| `preflight` | Verify target identity, OS, storage, memory, declared dependencies, connectivity and conflicting owners/ports |
| `stage-kit` | Transfer one immutable candidate into a scoped staging location and verify integrity; do not activate it |
| `verify <scenario>` | Run the agreed check through existing owners with explicit expected results and bounded deadlines |
| `collect` | Capture minimal sanitized diagnostics and resource/timing evidence |
| `stop` | Reconcile active operations, stop only test-owned processes through normal lifecycle paths and verify exit |
| `report` | Produce a compact machine-readable checkpoint and a human-readable result summary |

Start with `status`, `preflight`, `stage-kit`, `collect` and `stop`; add scenario
wrappers as the real installed journey proceeds. Define the small test-only
record schema and tests before implementation, outside product state stores.
Each run records its ID, host/OS and kit identity, harness revision, baseline,
step outcomes, start/end times, evidence references, unresolved effects and
resumption instructions. Distinguish pass, fail, not run, blocked and deferred;
preserve failed attempts when a later retest passes. No run record may become
an alternative authority for installed or Cloud state.

Before repeating an interrupted mutation, reconcile authoritative state; never
blindly replay publication, provisioning, enrollment or Finish. Resolve exact
test ownership and staging targets, preserve Production and release continuity,
publish profiles serially and apply VDP only through Safe Stop. Never put
passwords, private keys or tokens in arguments, reports, recordings or Git.
Capture only relevant UI evidence, excluding unrelated personal windows.
Retain bounded logs and a current/compatible predecessor kit; retirement must
first account for active dependencies, unresolved failures and rollback inputs.

#### M1 installation cleanup TODO

- [x] After Kit 025 native host verification, unmount obsolete Setup images and
  remove the three superseded staged kit copies and their five obsolete DMGs.
  Nine old attachments and the final Setup 038 attachment were unmounted.
  Preserve Kit 025, rollback Kit 024, compact manifests/evidence, Factory and
  credentials. The measured final removal freed approximately 201 MiB because
  large inputs shared APFS blocks; approximately 318 GiB remains free.
- [ ] Retire the two older installed versions through a supported version-store
  removal operation. No such operation currently exists; do not delete installed
  versions manually or claim this part is complete. Selection/current/previous
  records and all installed versions remain unchanged by staging cleanup.

The fix loop remains: preserve failure evidence on M1, diagnose and prove the
cause, fix source on the development Mac, run affected regression, produce one
identified candidate and retest on M1. An explicit transient diagnostic change
must be recorded and restored; it cannot count as an installer fix. Qualify
fresh installation separately from updating an existing instance. Measure
operator feedback, readiness, Cloud convergence and backend receipt separately,
including memory pressure and responsiveness on the 16 GiB target. Freeze
scenario assertions and existing time/resource budgets before each run; do not
relax them after a failure to obtain a pass.

At completion or pause, close owned test UI/processes and verify shutdown,
preserving identities/data unless a scoped Finish is intended. On interruption,
record whether offline restoration and shutdown completed or still need
reconciliation. Do not promise recovery while a host is asleep or disconnected.
OS-owned consent, authentication and mandatory safety controls remain genuine
human-intervention boundaries, not recurring routine approval checkpoints.

#### M1 qualification profile

On 1 October the user selected internal M1 storage, explicitly excluded external
SSD checks from this qualification scope, and confirmed the existing staging
accounts. The user said a separate local user is not critical because M1 is a
test computer. The working choice is therefore to retain the current local
account and verified access, rather than create another account as a prerequisite.
This choice was stated to the user; no account was created or changed. Preserve
personal applications/data and inventory both user and global dependencies.

| Choice | Selected starting profile | Boundary |
| --- | --- | --- |
| Local user | Current account on the dedicated test Mac; no additional account required | Use a separate demo instance/data directory; do not claim fresh-user onboarding or absence of dependencies without preflight evidence |
| Storage | Internal M1 storage for the package store and working data, subject to measured space guards | External storage, disconnect/reconnect and external-boot tests are excluded, not deferred prerequisites or passed checks |
| First Cloud path | Existing staging OEM/SP accounts, retaining the proposed supported first-use issuance of test certificates | No new email or organization required; do not copy working private keys or interpret this as authorization to change account permissions |

The staging endpoint remains `aws-stage.epmp-aos.projects.epam.com`; Production
resources remain protected even in staging. New organization registration and
existing-certificate import are distinct coverage items, not implied successes
of this run. Excluding external storage on M1 does not remove product guards or
invalidate previously recorded SSD evidence. It also does not retire or relocate
the development Mac's SSD artifacts. No external-storage support claim may be
derived from the internal-only M1 result.

Kit 021 / Setup 031 was the initial controlled candidate. Kit 024 completed the
functional engineering run; Kit 025 / Setup 038 is the host-correction candidate,
with selection and supersession recorded in the dated receipt. Further
candidate changes require explicit immutable pins and evidence of a relevant
blocker; do not build a successor merely to add
harness evidence. Developer ID/notarization and redistribution remain separate
release gates. The three deferred same-Mac checks and `VDP-TIMEOUT-01` remain
deferred, not passed. If a deferred failure recurs on M1, record it as a current
failure. No full clean-Mac or public-distribution completion is claimed.

Block A implementation now has [Kit 013 / Setup 022 source and native evidence](../../qualification/cloud-first-use-implementation-2026-09-29.md):
552 passing Python cases, native protocol/compile, durable one-shot enrollment
and explicit exact-reference selection/consumption. Native installation,
private preparation, existing staging access, occupied Brake/Tire rejection and
repeat/reopen checks passed. A reproduced parent-window feedback defect was
fixed and verified in Setup 022 without rebuilding Kit 013. At that checkpoint,
real new-token and eligible-unbound-object proofs remained open. Kit 014 later
passed eligible exact-reference saves and consumption; that historical item is
not a current gap. Continue independent B/C work;
do not reopen accepted choices, redo the installer build, or confuse local
proof with real token or clean-Mac acceptance.

The user subsequently accepted the existing Block C direct-distribution route:
Developer ID Application plus Apple notarization, not TestFlight. The local
development identity is not a substitute. First/repeat Presenter launch and a
cold launch from the read-only Setup 022 DMG now pass on the fresh Kit 013
instance, with no vehicle journal or inherited Test. The installed Presenter
also confirms the retained Test-set conflict through its ordinary GET-only UI
check. This closes those particular launch checks, not Blocks A/B as a whole.
The retained-Test transition was requested once at that concrete boundary;
independent packaging checks continue while it is unresolved.

The operator subsequently granted that exact replacement and full staging-only
sequence. The first guarded Finish on Kit 009 stopped before Cloud mutation at
`SERVICE_SUBJECT_SINGLE_ROLE_RETENTION_REQUIRED`; preserve its partial receipt
and fix the single-Test Subject-retention lifecycle before resuming. Do not ask
for the same replacement approval again. Staging token-acquisition authority
and connected mailbox access have now been inspected; mailbox selection and
actual invitation/enrollment remain distinct from local fixture evidence. See
the latest continuation in the same Cloud first-use receipt above. Blocks A/B
remain open, with all demo processes stopped.

That single-Test Finish defect is now corrected and the authorized old Test
has been retired, including exact backend data and local working files. The
normal absence/ownership gates remained active; an unreceipted historical
startup fragment was preserved separately, not silently deleted. An idempotent
repeat passed, and 84 affected single/dual-role lifecycle tests passed after
the final fixed DNS-log correction. Package the three corrected host modules
once as Kit 014, then continue the already authorized native first-use and
serial staging E2E. Old-Test engineering recovery does not close A/B or replace
new-kit acceptance; keep the new credential/mailbox branch separate.

Kit 014 / Setup 023 subsequently passed native installation and selection,
existing staging access, explicit eligible Brake/Tire reference saves and
native Presenter launch with window verification. The next unchanged step is
the fresh installed serial E2E. On reconnect, a fresh normal HTTP tab restored
approved browser control without accessing the old denied error page. The first
Create then exposed a real native Docker executable-discovery defect before
creating state, plus a hidden pre-run terminal receipt in the UI. Both minimal
corrections have transient proof; consolidate them into one small-input package
and continue the same authorized first-use/serial E2E. No new Unit/release was
created at that first failure, and the VDP timeout remains deferred. Details are
in the linked receipt.

Kit 015 / Setup 024 now passes the actual seeded-Keychain Create continuation,
backend launch, warm simulator start, selected staging Provision and VDP 121/V1
installation after native Safe Stop. The first cold CARLA start exceeded its
readiness budget; the separate packaged-only bounded-wait source correction
passes 115 affected tests and awaits packaging/live cold qualification. Preserve
the current Test while checking the remaining software sequence. An action-time
safety review requires an exact remaining-payload publication confirmation;
unsigned local preparation is independent. These are bounded open acceptance
items within A/B, not a new plan or a claim that first use is complete.

The exact remaining release authorization subsequently passed. The same Kit 015
Test now has [serial functional evidence](../../qualification/installed-serial-e2e-2026-09-29.md)
for Brake 97/98/99, VDP 122/123 and Tire 51, independent Reset/history, Return
to road, offline local function/queued delivery and retained guest reboot
recovery. All owned demo processes are stopped; the Test is preserved. The two
proved small host changes (cold launch wait and native maneuver wording) are now
batched into verified Kit 016 / Setup 025. Its native installation and empty-instance
first/repeat launch subsequently passed without retiring the Test. A separate
empty instance is an accepted installation path, so Finish was not a prerequisite;
the retained-run selection guard remains unchanged. This closes those particular functional checks,
not genuine new enrollment, cold native qualification, full power-cycle,
scoped Finish, clean macOS or distribution release. No repeated publication
approval or full service rebuild is required for these host-only corrections.

The 30 September continuation in the same receipt reconciles an unrelated
ChatGPT process interruption: Setup completed its installation independently.
Kit 017 / Setup 027 is now installed and selected for the empty instance, without
changing the retained Test. Its actual cold Open still needs attention: the
unnecessary empty-instance retries are gone, but consecutive observations use
display heights differing by 5 pixels. Preserve this evidence and diagnose that
boundary before any further package build. All test-owned runtime processes
and Setup are stopped; this is neither a new plan nor completed A/B acceptance.

Block C now also has an isolated hardened-Setup proof and source build support
for an explicit Developer ID identity (267 passing distribution tests). The
required distribution certificate is not locally available. The entire runtime
code closure must still be prepared and qualified before Apple submission;
do not confuse the successful 109-file Setup proof with whole-kit readiness.
No CARLA/Factory rebuild, Test deletion or external submission is implied.

The [30 September first-use continuation](../../qualification/installer-first-use-2026-09-30.md)
supersedes historical mailbox and cold-Presenter gaps above. Existing accounts
need no new email or invitation: actual current-user token issuance and new
certificate authentication passed for both roles, preserving old credentials.
Native password entry and reuse were also proved without engineering seeding.
Kit 019/Setup 029 closes the separate first-Open/private-directory defect and
passes new-instance installation, Presenter launch and native Cloud pair checks.
The standing staging authorization subsequently covered exact Test retirement.
Kit 019 passed ordinary Create and cold CARLA, then exposed fresh EC credentials
that authenticated but could not sign RS256 packages. Kit 020 corrects new
enrollment to RSA; real OEM/SP issuance, restart/repeat without reissuance and
native inspect/save/check now pass, preserving every old credential. The empty
Kit 019 Test completed normal Finish before selection of the corrected package.
Installed publication/function and the remaining power-cycle/Finish checks
continue under the same authorization. Blocks A/B are not declared complete
from narrower results; clean-system and release gates are unchanged.

The same receipt now records actual VDP 124/Brake 100/Tire 52 RSA publication,
installation and native function, independent Reset/history, Return to road,
externalOFF queued delivery, a full guest poweroff/on with automatic stationary
same-identity recovery, post-ignition maneuvers and ordinary UI Finish. The
current Test is retired and its owned processes are closed; credentials,
Factory and release continuity remain. Do not repeat these passed checks merely
to produce another kit number. Kit 021 batches only the separately proved
preprovisioning VM-start correction. Its native install/selection, first/repeat
Presenter launch and installed-code regression passed. The receipt lists the
exact remaining native access, incomplete-start and retained-selection
gaps. Clean macOS and distribution release remain separate gates, not an
alternative description of this Mac's engineering evidence.

### Accepted deferral and move to clean system on 30 September 2026

The user explicitly deferred the three remaining checks at the current stage
and requested progression to clean-Mac qualification:

1. Classifying and repeating the intermittent native VM console-entry failure.
2. Automatic cleanup after an incomplete simulator/start transaction.
3. Retained-instance version selection while shared Docker holds old instance
   directories after their owned containers have exited.

These checks are **deferred, not passed or fixed**. They no longer block entry
to block D, but remain open for later disposition before the supported release
claim. Do not weaken occupancy, authentication or cleanup guards, restart
unrelated Docker workloads, or rebuild the candidate merely for this deferral.
VDP-TIMEOUT-01 remains a separate previously accepted exception.

Use the existing Kit 021 / Setup 031 candidate for controlled qualification,
not as a publicly distributable release. The then-agreed one-Mac route was a
native boot of clean macOS on the separate SDV-Clean APFS container; the accepted
1 October two-Mac route above supersedes it for current execution. Read-only preflight
on 30 September confirmed its recorded volume UUID
`870130E1-51A1-4ED8-841E-DB84B7941376`, external 1 TB physical parent,
350 GB container and approximately 349.8 GB free. macOS is not installed.
Preserve SDV-Work and the internal system; this move does not authorize erasing
the whole external disk. Re-resolve the exact target before OS installation.

No Migration Assistant, developer-tool/settings inheritance or internal source
fallback is permitted. Record declared runtime prerequisites and test tooling
separately. Ordinary first-use password entry and successful Create Controller
remain required in the clean run: deferring the old reproduction does not make
a new authentication failure acceptable. Capture a recurring deferred defect
as a current failure rather than suppressing it or calling the run complete.
Record OS-owned permissions, cold/repeat launches, serial releases, functional
maneuvers, offline recovery, ignition and scoped Finish from this candidate.

The user must participate in the scheduled native reboot, initial OS setup and
security consents. Preserve a handoff checkpoint; the current desktop session
does not continue controlling the Mac across boot. Clean native results on this
Mac do not qualify another hardware model. Development signing, notarization
and redistribution obligations remain separate release gates.

The subsequent authorized artifact revision retired source Kit 004–019 and
obsolete Setup previews/DMGs, retaining source Kit 020/021 and Setup 030/031.
Installed stores and instance selections remain unchanged. Current build inputs
have been verified against Kit 021; use the updated record in
`SDV-Work/AosEdge-SDV/reports/kit-retirement-20260930/current-build-inputs.json`,
not the historical recipe pointing at source Kit 010. The
[retirement receipt](../../qualification/installer-first-use-2026-09-30.md#superseded-kit-and-installer-retirement)
records the exact scope, preserved evidence and 2.64 GiB observed recovery.

## Purpose and acceptance boundary

Deliver **AosEdge Platform - SDV Lab** to a new Apple Silicon Mac user without
requiring that user to reconstruct the project's development history or compile
Unreal Engine, CARLA, the host applications or the vehicle software.

There are two linked deliverables:

1. An installable runtime distribution with first-use setup, diagnostics and
   an operator walkthrough.
2. A release-oriented repository entry point with exact source and artifact
   versions, installation instructions, verification and a separate developer
   build path for the same release.

This document records the user-accepted delivery sequence. It does not claim
that an installer, standalone simulator or autonomous clean-install test suite
already exists. It does not authorize unspecified Cloud mutations, signatures,
publication, operating-system installation or deletion. Exact live targets and
effects remain subject to the
[execution policy](../../governance/rapid-development-and-debugging.md).

This is a delivery-planning addition, not a change to the canonical vehicle
architecture, service contracts or qualification verdicts. Before implementation
introduces new installer, update or recovery behavior, classify the change and
update the affected canonical requirements, contracts and tests under the
[documentation policy](../../governance/documentation-and-requirements-management.md).
This plan must not become a competing runtime specification.

## Starting point and preserved scope

- Preserve the immutable `demo-v1.1` source checkpoint. Use a separately
  identified distribution candidate; do not move that tag or reuse its name
  to imply clean-install qualification.
- Start from retained Factory .39. Its focused ignition and offline evidence
  does not close the fresh serial all-version/Finish acceptance gate. See the
  [current baseline](../../qualification/current-baseline.md).
- Rebuild the Factory only when a proven guest change requires it. Host
  packaging or documentation changes alone do not justify an image rebuild.
- Preserve the existing working demo, Production and its dependent Factory .31,
  active diagnostic state, build caches and the separate video repository.
- Preserve component ownership and Git history. The integration repository
  remains the main entry point; it does not absorb the component repositories,
  Unreal source, compiled artifacts or provisioned VM disks.
- Current CARLA operation depends on the development environment. An existing
  packaging target is a starting point, not proof of a portable Mac build.
- Automatic laptop sleep/wake recovery remains a
  [separate accepted plan](native-sleep-wake-recovery-2026-09-21.md).
  Controller ignition evidence must not be used as host sleep/wake evidence.

## Delivery sequence

Repository navigation and test documentation are maintained alongside the
packaging work. The numbered stages define acceptance gates, not a requirement
to defer every documentation improvement until all binaries exist.

### Stage 0 — Freeze the distribution inventory

Inventory all runtime and build inputs: CARLA and its content, matching Python
API, Presenter, Demo Control, Gateway, native Driving Control / Telemetry,
Brake/Tire backends, QEMU and firmware, Factory, unsigned version-profile
inputs, Cloud tools, libraries and container runtime.

For each input record:

- owner, exact source revision and retained patches;
- artifact version, architecture, provenance and integrity information;
- download, installed and temporary-build space requirements;
- whether it is needed at runtime, only for development, or supplied by the user;
- licensing, attribution, source-offer and redistribution review status;
- dependencies on local paths, toolchains, stores and configuration.

Reconcile source status, workspace pins, documentation links and hosted CI.
Do not interpret an unavailable remote check as a successful one. Define the
initial macOS/hardware test target; publish minimum requirements only after
measurement, not by copying the development machine's specifications.

**Deliverable:** release-input inventory, preservation list, risk register and
bounded implementation work packets with owning repositories and tests.

**Exit gate:** every runtime dependency and unresolved distribution decision
has an owner; no undocumented local input is assumed.

### Stage 1 — Prove standalone CARLA portability

Build the simulator with only the maps, vehicles and other content needed by
the accepted demo. Preserve the qualified CARLA/Unreal corrections and build
the matching Python API. The target is a runtime package, not a copied Editor
installation or a requirement to install Unreal sources on the user's Mac.

Verify outside the development tree:

- simulator startup and connection to Gateway and Driving Control;
- Manual and Autopilot operation, Brake and Tire maneuvers, Return to road;
- actual telemetry, including steering and wheel-angle behavior;
- cold and warm startup, graphics/cache preparation, stability and memory;
- absence of runtime reads from the Editor, build directories or source tree.

Do not promise zero first-run graphics preparation; measure and explain it.

**Deliverable:** portable simulator proof, dependency report and measured size.

**Exit gate:** required simulation and signal behavior works without the
development installation. Stop and resolve a failure here before investing in
the final installer interface.

### Stage 2 — Assemble portable demo runtime artifacts

Prebuild the host applications and package or explicitly declare their runtime
dependencies. Remove assumptions about a particular home directory, Xcode's
Python, a developer virtual environment or Homebrew library paths. Freeze
backend image versions/digests and the supported container-runtime setup.

Prepare three logical groups, without prematurely freezing their file format:

- **Simulator:** standalone CARLA, required content and matching runtime/API.
- **Demo runtime:** Presenter, shared Demo Control, Gateway, native control,
  backends and supporting tools/libraries.
- **Vehicle:** clean Factory, compatible QEMU/firmware and unsigned preparation
  inputs for VDP V1/V2/V3, Brake V1/V2/V3 and Tire V1.

The ordinary operator preparation path must not depend on historical Git
checkouts or undocumented build exports. Preserve existing preparation inputs
until their packaged successors have passed verification.

Exclude credentials, provisioned identities, model data and previous run state.
Use the selected Cloud instance's authorized credentials when signing packages.
Do not distribute pre-signed packages bound to this development environment.
Protect release-number continuity during installation, update and recovery.

**Deliverable:** immutable candidate artifacts with provenance and integrity data.

**Exit gate:** artifacts run from a separate location with explicit
dependencies; no manual copying from the development environment is needed.

### Stage 3 — Implement installation and first-use setup

The user approved implementation of [ADR 0018](../../architecture/decisions/0018-installable-demo-and-first-use.md)
on 27 September: a DMG/application and first-use wizard, beginning with a complete
local kit. Versioned downloads remain a follow-up; no hosting service or purchase
is selected. One OEM and one SP suffice for the two independent services.

Implementation order:

1. Offline package transaction: independent pins, complete-inventory validation,
   explicit-volume store, verified copy, repeat and interrupted-copy recovery.
   The [frozen contract](../../../contracts/distribution-installation/README.md)
   deliberately has no runtime activation operation.
2. Complete the canonical installed-state/first-use cascade; separate immutable
   input selection from durable operator state through existing Demo Control.
   Test update/repair/rollback compatibility and data-preserving removal.
3. Native wizard/DMG: existing access or official registration, secure SDK
   enrollment, one OEM/one SP checks, explicit dependency and Cloud preparation.
4. Signing/redistribution gates and clean-system qualification, with operator
   participation for platform/OS authorization. Do not claim autonomous account
   creation or external distribution before those gates close.

The first offline transaction slice is implemented and passed the source
tests plus complete Kit 004 installation and verified repeat on Work; see the
[offline installation receipt](../../qualification/offline-installation-2026-09-27.md).
Its successful state is installed but not activated. The canonical installed-state
cascade and explicit runtime path separation now also pass source and isolated
Kit 005 execution checks; see the [installed-state evidence](../../qualification/installed-state-2026-09-27.md).
The [version-selection/recovery detail](../../../contracts/distribution-installation/version-selection.md)
now implements compatible engineering selection, leased runtime use and
state-preserving rollback/program repair. Source gates and final Kit 007
isolated installation/selection/CLI/unselect checks pass; the
[dated receipt](../../qualification/installed-versions-2026-09-27.md) also records
the reproduced and corrected early repair-record interruption.
The first [native local-setup slice](../../../contracts/distribution-installation/native-setup.md)
now exposes folder choice, read-only preflight, verified installation and a
separate private-instance preparation/selection action. Its
[dated receipt](../../qualification/native-setup-2026-09-27.md) distinguishes
source tests, actual native UI and real-kit outcomes. This app has a trusted
private bootstrap and does not execute an unverified user-selected kit.
The [existing-access increment](../../qualification/native-cloud-access-2026-09-27.md)
adds explicit native OEM/SP file choice, local inspection, atomic pair selection
and a separate read-only Cloud prerequisite check. It does not enroll new users
or launch the demo. Native/live evidence is tracked separately from fixture tests.
Inspection of pinned `aos-keys 1.10.0` found that token enrollment retries its
certificate POST with system CA trust after an SSL failure. Do not wire this
CLI blindly: a one-shot, strict-trust enrollment adapter and uncertain-response
reconciliation require their own bounded proof before exposing token entry.
The one-shot adapter and guarded first-launch integration are now implemented;
the current execution route and linked 29 September evidence supersede that
earlier implementation checkpoint. Genuine issuance, retained-run ownership
and all-instance retention gates still precede live updates or destructive
removal. Unselect is not uninstall. The
complete wizard/DMG and overall installation exit gate remain open; the working
demo has not been migrated into the isolated instance.

Installation and setup cover:

1. Architecture/macOS, disk-space, dependency, permission and port preflight.
2. Verified downloads, clear progress and safe recovery from interruption.
3. Application installation and a discoverable launch entry point.
4. User-selected Cloud/OEM/SP configuration and private credential handling.
5. First-run diagnostics with actionable failures rather than false readiness.
6. Repeat installation, update, interrupted-update recovery and removal.

#### Accepted first-release Cloud account scope — 27 September 2026

The user confirmed that the current demo uses two services within **one Service
Provider**, and accepted retaining that topology for the first installable
release. Onboarding requires one OEM context and one associated SP context;
Brake Health and Tire Health are separate services owned by that same SP.
Do not require a second SP organization, a second SP certificate or an
administrator/support request solely to separate the two demo services.

Their service identities, release sequences, backend data and independent
Driver Advisory Reset operations remain separate. Sharing an SP does not merge
the services, relax their permissions or combine the OEM and SP roles. First-use
checks must verify the selected OEM/SP relationship and authority for both
services. Distinct service providers may be a later explicit scenario; this
first-release setup must not be described as proof of cross-provider isolation.

This records the accepted onboarding scope, not a change to running Cloud
accounts, credentials or assignments. The earlier two-provider scenario is not
a first-install prerequisite. Detailed first-use contracts and their canonical
documentation reconciliation still precede implementation; this decision alone
does not approve the remaining installer, credential-storage or rollback choices.

Document and test rollback compatibility rather than assuming an old binary
can safely read newer state. Application removal must not silently perform
Finish, delete a Cloud Unit, erase run data or roll back the release ledger.
Separate disposable package/cache cleanup from user-data retention.

Resolve distribution licensing and macOS application-signing/notarization
requirements before handing the package to other users. Do not make disabling
operating-system security the installation procedure.

**Deliverable:** installer candidate and first-use workflow.

**Exit gate:** install, repeat, repair, update and removal have tested outcomes
and preserve unrelated applications, identities and data.

### Stage 4 — Organize the repository for reproduction

The [human-friendly reproduction packet](work-packets/human-friendly-reproduction.md)
defines the concrete R1–R4 deliverables and acceptance checks. Its developer
route distinguishes builds using pinned heavy artifacts from a separately
qualified full-source rebuild. Future command examples are not current tools.

Use the existing integration repository as the release landing page. Retain
component ownership and source history; do not create a monorepo or rewrite
history to make the first-time experience simpler.

Provide two explicit documentation routes:

| Operator route | Developer route |
| --- | --- |
| Download the qualified distribution | Obtain the exact source revisions |
| Install and configure access | Prepare the separate build environment |
| Follow the demo scenario | Build affected components and the distribution |
| Diagnose common failures | Run tests, qualify and contribute changes |

The landing page names the current distribution, tested configuration,
prerequisites, downloads and startup procedure. Historical research stays
accessible but is not required reading for a new operator. Preserve stable
document paths/anchors or provide reviewed replacements when reorganizing.

Keep large binaries in suitable artifact storage, not Git. Use a versioned
release manifest to bind source pins, artifacts, integrity data, instructions
and qualification evidence. Access to restricted dependencies must follow
their distribution conditions; a public source repository does not make every
dependency publicly redistributable.

**Deliverable:** operator quick start, developer build guide, diagnostics,
release manifest and a coherent documentation entry point.

**Exit gate:** a reader can identify one reproducible release without relying
on the chat, local development history or conflicting historical instructions.

### Stage 5 — Automate verification and the fix loop

Build on existing Demo Control ownership and test suites. Do not introduce a
second independent orchestrator or substitute screenshots for authoritative
state. Define exact expected results and evidence before running the tests.

Cover three groups:

- **Installation:** empty environment, repeat, interruption, corrupt download,
  insufficient space, missing dependencies/access, upgrade and removal.
- **Function:** creation, provisioning, sequential version progression,
  real vehicle-derived products/advisory, independent Reset, offline/online,
  ignition recovery and separately authorized Finish.
- **Presentation:** actual operator UI paths, status/source agreement,
  response latency, stale-state transitions, layout and z-order.

Keep UI actions through the shared product path; use authenticated read-only
Cloud observations and local/backend evidence to verify their effect. Record
which steps used UI and which used engineering controls. Measure action
feedback, Cloud convergence, backend receipt and local readiness separately.

On failure preserve the target and bounded sanitized evidence, establish the
cause, prove a minimal fix, add regression coverage, rebuild only affected
artifacts, and retest. A missing library manually installed on the test machine
does not close an installer defect. An interrupted Cloud action must be
reconciled before any retry. Keep secrets out of logs, recordings and reports.

**Deliverable:** reproducible tests, bounded evidence and resumable run records.

**Exit gate:** failures are distinguishable from missing evidence, actionable
and repeatable; source checks are not presented as clean-install/live proof.

### Stage 6 — Qualify installation on a clean system

The accepted current target is the separate M1 Pro, controlled from the
development Mac as described above. A fresh dependency/state inventory and
native installed E2E are mandatory. This run uses M1 internal storage; external
SSD checks are explicitly excluded. The earlier external-boot route below is
historical context, not a queued fallback, prerequisite or authorization to
install another OS now. The following isolation levels describe the strength
of earlier proposed approaches:

1. Separate installation on the current Mac. A new user still shares global
   software and therefore does not prove a clean-host installation.
2. Disposable clean macOS VM for supported installer tests. Verify graphics
   and nested-virtualization constraints; do not treat this as native CARLA,
   container and controller-VM acceptance automatically.
3. Clean compatible macOS on an external SSD, booted on the existing Mac,
   without migration of development tools or settings. Back up first and
   identify the exact installation disk before any destructive operation.
4. Repeat from the frozen release candidate using only the operator guide and
   declared dependencies; ensure the test cannot silently use the internal
   development installation.

Run the [current operator sequence](../../operations/current-demo-workflow.md)
from an empty Test through Finish. Publish each VDP/Brake version only after
installation and verification of the previous version. VDP FOTA requires Safe
Stop; the independent QM service SOTA path does not inherit that gate. Tire V1
is the existing advisory-capable profile; do not invent a Tire V3 requirement.

Verify actual Brake/Tire maneuvers and backend products, native advisories,
independent Reset/history preservation, externalOFF local operation and queued
delivery after ON, and same-identity stationary ignition recovery. Track the
baseline's remaining negative/recovery cases explicitly:
close what the proposed support claim requires or document a bounded exclusion.
Host sleep/wake is excluded from this qualification by the 2 October user
decision. Never silently turn an untested case into a passed one.

**Deliverable:** clean-system installation and E2E report with exact package,
hardware/OS identity, measurements, exclusions and reproduction instructions.

**Exit gate:** complete mandatory scenario and installation checks pass for
the declared target. One Mac model does not qualify every Apple Silicon Mac.

### Stage 7 — Publish a reproducible release

Prepare an explicitly labelled distribution preview for controlled validation,
then a qualified release only after its mandatory acceptance gates pass.
Publish authorized source commits/tags and artifacts without moving `demo-v1.1`.

The release contains the installer, manifest, source/build instructions,
operator walkthrough, troubleshooting, required notices, integrity information,
test report, supported configuration and known limitations. Reconcile download
links and actual published artifacts with the manifest.

**Exit gate:** another authorized user can obtain exactly the tested artifacts
and follow the instructions. A new-machine pilot broadens the support evidence;
it is not assumed completed by a same-Mac external-SSD test.

## Minimal-human execution on one Mac

This is a historical alternative, outside the selected M1/internal-storage
qualification scope. The accepted two-Mac route above avoids switching the
development host between operating systems.

Perform most diagnosis, source fixes and packaging iterations in the working
system before the clean native session. Preserve useful build caches within
the disk budget. In the clean system install only the declared runtime and
explicitly recorded test tools; the agent is not a demo dependency and must
not supply undeclared runtimes that mask packaging defects.

Booting the external system stops the original local agent session. A user
must complete OS setup/login and the new session's authentication and native
permissions before agent-driven UI work can continue. Preserve the work plan
and run checkpoint in files; do not assume uninterrupted control across reboot.

On one physical Mac, a heavy Unreal/CARLA rebuild may require returning to the
development boot and then back to the clean system. A separate build host can
reduce that later but is not assumed available or authorized by this plan.
Batch proven changes to minimize those switches.

Routine diagnosis and in-scope regression run without repeated design questions.
Human participation remains for OS/security dialogs, inaccessible credentials,
unresolved product decisions, exact external/destructive actions not previously
authorized, and final usability review. Do not disable FileVault or other
security controls to claim unattended operation. UI tests require an available
desktop, power and agent connectivity. Test externalOFF at the demo boundary,
not by disconnecting the entire Mac from the agent.

## Decisions to close before their implementation gates

| Decision | Closure point |
| --- | --- |
| Supported macOS/hardware, disk and memory envelope | Measured in Stages 0–2, confirmed in Stage 6 |
| Standalone CARLA feasibility and minimal required content | Stage 1 |
| Dependency redistribution, notices and restricted access | Before artifact distribution |
| Container runtime installation/licensing and backend image source | Stages 0–2 |
| Installer format, artifact storage and download authorization | Before Stage 3 implementation |
| macOS signing identity and distribution requirements | Before external-user preview |
| Credential setup, state retention, update/rollback contracts | Before Stage 3 implementation |
| Which remaining baseline gaps block the support claim | Freeze before Stage 6 execution |
| Clean target account, storage and Cloud first-use profile | Current test-Mac account, internal storage only and existing staging accounts are recorded above; verify actual baseline at preflight, without reopening these setup choices |
| Exact staging targets, release allocation and retirement authority | Before live mutation |

## Dated progress and evidence history

This history preserves earlier conclusions and then-current next actions.
Follow the consolidated execution route at the top for current work ordering.

### Acceptance checkpoint — 28 September 2026

The operator accepted returning to stage exit criteria rather than starting
another independent installer increment. The historical slice notes below are
evidence, not a queue of simultaneous next actions.

| Stage | Current acceptance state | Next required result |
| --- | --- | --- |
| 0 — Inventory | Complete in its recorded scope | Preserve the input inventory |
| 1 — Standalone CARLA | Complete in its recorded scope | Reuse the qualified Game; no rebuild |
| 2 — Portable runtime | Functional E2E and UI corrections passed; `VDP-TIMEOUT-01` explicitly user-deferred | Preserve the exception and evidence; Stage 3 continuation allowed, not unconditional release qualification |
| 3 — Installation and first use | Partial | One installed-package path from setup through first launch; then lifecycle cases |
| 4 — Reproduction documentation | Partial supporting work | Coherent release-specific operator and developer routes |
| 5 — Verification | Source/fixture coverage exists | Repeatable installed-product and UI scenario evidence |
| 6 — Clean-system qualification | Not complete | Native clean-system installation and mandatory E2E |
| 7 — Publication | Not complete | Exact qualified release, artifacts, notices and supported scope |

The local source checkpoint is `70dac05`; existing `demo-v1.1` is unchanged.
Independent empty-engine import, repeated import and networkless backend startup
passed on 28 September. Native CARLA, Driving Control and Presenter were observed
directly. The [retained-Test live E2E](../../qualification/distribution-stage2-live-e2e-2026-09-28.md)
passed its functional checks, including offline delivery and ignition recovery,
exposed contradictory shutdown/Finish guidance and retained native caption
defects; the [same-day UI correction](../../qualification/distribution-stage2-ui-corrections-2026-09-28.md)
subsequently fixed and rechecked them. Prior advisory timeout causality remains open. These results are not
clean-Mac or fresh serial-release proof.

**Work-order decision, 28 September:** the user deferred `VDP-TIMEOUT-01`
([record and resumption criteria](../../qualification/distribution-stage2-ui-corrections-2026-09-28.md#user-disposition-deferred-follow-up)).
Do not continue that investigation now or report the defect fixed.

Immediate order: resume the existing Stage 3 design as one first-use journey.
First reconcile the corrected small UI/program inputs into the candidate kit,
then qualify the existing installation/instance-selection and native Cloud-access
path from that kit. Close the previously recorded native file-open wait and
real GET-only access evidence gaps rather than assuming fixture success proves
them. Complete the accepted strict-trust OEM/SP enrollment and guarded first-launch
integration where still missing. Keep installation, access readiness and runtime
launch as distinct explicit actions. Do not add unrelated installer features,
rebuild Factory/Game, change service models or repeat completed Stage 2 scenarios.
Existing-access verification
does not replace the accepted new-user registration/enrollment path. Source
test success and a retained Test run do not establish clean installation.

Kit 008 now reconciles the current application export and the qualified Stage 2
UI payload. Its transfer and source gates pass; the native installed first-use
journey now passes fresh installation, separate instance selection, installed
isolation and synthetic certificate-pair inspection/save/recovery in a separate
fresh instance. Preview 007 corrects the reproduced certificate-error guidance.
The intermittent native cold-start file-open wait remains open; warm success
does not explain it. The operator subsequently authorized real GET-only staging
access and stopping the developer demo while preserving its Unit, disks and data.
The [existing-access handover](../../qualification/installed-existing-access-2026-09-28.md)
records the completed data-preserving stop, actual native installation/selection,
reference-only real pair save and GET-only staging observation in the permanent
instance. Authentication and OEM/SP association passed. The observed SP delivery
false denial was traced to an OEM-only catalog permission in the SP checklist;
the role-scoped source correction and its regression tests passed. Native preview
008 then confirmed actual OEM/SP and all delivery permissions with the same pair;
its trusted helper contains the fix while immutable Kit 008 is preserved. The
operator then explicitly authorized old-Test retirement for a clean installation.
The normal Test-only Finish completed and preserved Production's local disk and
published releases; the membership conflict was resolved by explicit retirement,
not by the wizard adopting or deleting another run. Kit 009 now carries the same
SP correction in its immutable program and trusted native preview. The
[clean-installation receipt](../../qualification/clean-installation-2026-09-28.md)
now records successful fresh native installation (`reused: false`), separate
empty-state preparation, reference-only credential selection, all ten real
GET-only Cloud checks and an installed-CLI Presenter smoke with no inherited
run. It does not close the still-missing native launch/enrollment or fresh
VM/simulator/E2E gates. The
[28 September Stage 3 receipt](../../qualification/installed-first-use-2026-09-28.md)
records the exact candidate and remaining gates. No active demo migration,
Factory/Game rebuild or VDP timeout correction is implied.

The subsequent [installed clean-state E2E](../../qualification/installed-clean-e2e-2026-09-28.md)
created Test `.39` and healthy new-owner backends after explicitly cleaning the
empty previous owner's conflicting Docker volumes/networks. Unsigned VDP V1
`118.0.0` preparation passed. The operator accepted per-instance local Gateway
server trust, now implemented and exported as Kit 010. Its
[qualification receipt](../../qualification/installed-gateway-trust-2026-09-28.md)
separates source tests, explicit Kit 009 rapid initialization and immutable
candidate checks. No old key was copied or TLS bypass added. The preserved Test
now has the same running simulator/dashboard attached to the new Cloud Unit,
with sequential VDP118/119/120 and Brake94/95/96 plus Tire50 installed and
functionally checked. VDP updates used explicit Safe Stop; Brake upgrades did
not require another Deploy. Both local advisories, separate resets/history and
Return to road passed. Five-minute external-OFF/ON, exact-once backlog delivery,
full ignition OFF/ON and fresh post-ignition Brake/Tire results also passed;
all 24 final evidence predicates are true. That E2E ended online and stationary;
the later [travel pause](../../qualification/installed-pause-2026-09-28.md)
gracefully stopped and preserved the same Test.
Brake preparation exposed
`INSTALLED-SERVICE-PREPARE-01`: a selected input root was incorrectly checked
as a private state root. Four-profile transient proof and 75 source tests passed;
Service preparation used a labelled engineering continuation, not an in-place
patch or completed native UI acceptance. Existing-account Subject references
also required explicit exact-identity reconciliation; first-use UX coverage
remains open and must not be replaced by label-only adoption. Cold launch exposed
`CARLA-FIRST-START-01` (OS scan outlasted native
readiness); one classified warm retry completed. Preserve the Test and both
outcomes; the warm result does not close cold first-use qualification.
The functional E2E is complete after the explicitly recorded engineering
first-use corrections; it is not automatic clean-Mac acceptance. The next
authorized increment is native launch under the updated native-setup contract.
The [native launch checkpoint](../../qualification/native-presenter-launch-2026-09-28.md)
now records preview 010 against unchanged Kit 009: automated ownership/protocol
checks, explicit repeat and Setup quit/reopen passed without duplicate owners
or lifecycle effects. First native Open exceeded its two-minute deadline while
waiting inside a file open before server startup. `SETUP-COLD-OPEN-01` remains
open; warm success is not first-use qualification. Its same-day continuation
now localizes one exact store-open wait to macOS removable-volume consent,
with aligned file-boundary/TCC timings and the operator's confirmation.
Preview 015 adds explicit storage-access feedback, actionable missing-instance
and denied-access errors, and bounded read-only final window observation that
does not replay the accepted restore. The source gate passes 245 distribution
tests without skips. Native final-candidate acceptance is recorded in that same
receipt; OS permission is an operator prerequisite, not a deadline to extend or
a security control to bypass. Earlier untraced long opens are not retroactively
declared identical or fixed. Presenter is open, while the same retained
controller/simulator/backends remain stopped. Next: close the exact candidate's
native first/repeat/negative checks, then package existing service-Prepare
corrections and resolve the bounded exact-identity Subject first-use contract.
No new Test or repeated functional E2E is needed for this native-launch slice.

The [29 September signing checkpoint](../../qualification/native-setup-signing-2026-09-29.md)
supersedes the desktop state above: vehicle runtime remains parked after SSD
reconnect, with the same selected instance; Presenter was opened for Setup QA. Ad-hoc preview
identities change between builds, so native permission-continuity qualification
now first requires explicit stable local signing. The builder rejects missing
signers before copying/compilation and never silently falls back to ad-hoc.
The existing Apple Development identity was explicitly authorized and previews
016/018 signed successfully; changed copy 017 preserved the same designated
requirement. SSD reads needed no further prompt on this host. A separate actual
Accessibility denial (-25211) remained despite an On checkbox for the old app.
Preview 018 now reports that prerequisite before any helper/restore starts.
Rebinding alone initially failed despite the visible switch. The operator then
explicitly authorized a one-time Setup-only Accessibility reset and re-add of
018 through System Settings. Actual native first/repeat Open, Setup quit/reopen,
different signed binaries (018 → 016 → 018), and a normal Work-volume
unmount/remount with stopped-server startup now pass without repeated prompts.
The installer itself never resets or grants permissions. Retained Test and
package selection are unchanged; Presenter is open, vehicle runtime is parked.
Physical disconnect, OS restart and clean-host consent remain separate gates.
The exact same-host results and remaining exclusions are in that
receipt; a signature or warm SSD read alone does not close them.
Do not rebuild the VM or create another Test for this correction.

The [installer consolidation checkpoint](../../qualification/installer-consolidation-2026-09-29.md)
records the next bounded slice: current source differs from Kit 010 in only the
service-Prepare correction; large inputs remain unchanged. Distribution and
targeted source/schema gates pass. The initial three-kit cleanup recovered only
27.96 MiB because directory accounting included shared APFS data and did not
clear the reserve. Subsequent authorized
[storage consolidation](../../qualification/storage-consolidation-2026-09-29.md)
restored approximately 164.5 GiB of internal free space. Kit 011 then passed
complete 17,683-file verification, the Setup release pin was advanced, and
preview 019 was built with the same authorized stable development identity.
Separate native installation and installed Prepare/local-trust proof passed.
Repeated Open exposed a workspace-only vehicle journal created by first Open;
the strict reader rejected it before dispatch. The user accepted independent
window metadata in the existing workspace directory, preserving old journals
and Create Controller initialization. The bounded two-file fix passed 521 source
cases, fresh native Kit 012 installation, first/repeat Open, Setup restart and
Presenter-server restart without creating a vehicle journal. The installed
configuration reader and missing-credential guard also passed with developer
reads/network denied. This completes only the bounded Kit 012/Setup 020 gate. Preserve
the Kit 011 failure evidence; no retained-Test switch or clean-Mac acceptance
is implied. Keep the remaining Subject/enrollment,
lifecycle, cold-first-use and distribution gates distinct from this slice.

The [Cloud first-use boundary proof](../../qualification/cloud-first-use-boundaries-2026-09-29.md)
now records 96 passing existing source regressions, 10 transient enrollment
transport tests and 11 transient exact-Subject tests. GET-only observation
confirms both existing Subjects remain bound to the preserved Test; they are
not available for automatic reuse by the empty installed instance. No product
source, kit, journal or Cloud object changed. Explicit reference reuse and
lost-enrollment-response recovery were submitted as bounded design choices;
do not promote the prototypes or create a replacement Test before those
choices and the relevant live authority are closed. The user subsequently
accepted both choices; see the consolidated execution route above. Exact live
target authority and actual onboarding qualification remain distinct from that
design acceptance.

The [28 September closure record](../../qualification/distribution-stage2-closure-2026-09-28.md)
is the current execution checklist. Large artifact work and the guarded live
qualification must retain their existing resource limits; reconnecting the SSD
does not make internal disk space available. No global Docker reset or removal
of unrelated containers is part of fresh-engine verification.

The [external SSD deployment plan](external-ssd-deployment.md) records the
27 September preparation of a separate 1 TB T5: 650 GB Work and about 350 GB
Clean in separate verified APFS containers. It defines candidate transfer and
future clean-system gates; no installer, OS install or runtime migration is
claimed. File-ownership enforcement on Work has now been enabled through native
administrator authorization. After the operator created the user-owned project
directory, Kit 004 passed its full transfer verification and external-only
[isolated proof](../../qualification/external-ssd-package-2026-09-27.md).
Its follow-up also passed 27 native checks and 12 invalid-input rejection cases
on the SSD, with 62 targeted source regression tests. The disposable clone was
removed after preserving evidence; no live runtime handoff was performed.
The internal original and all live owners are preserved; installer and clean-OS
acceptance remain separate gates.

Stage 0 inventory and ownership gate is **COMPLETE** as recorded in the
[25 September input audit](../../research/distribution-stage0-inventory-2026-09-25.md).
It freezes observed inputs, preservation, unknown size/licensing decisions and
owning implementation packets. A hosted documentation-checkout defect was
identified and corrected locally; publication and a fresh hosted result remain
open. This does not qualify a portable artifact or erase workspace-doctor drift.

Stage 1 is **COMPLETE** for the scoped simulator feasibility proof on 25 September:
the bounded standalone CARLA proof uses an isolated source/build candidate,
local dependency inputs and separate test ports, preserving the live demo.
Its [execution record](../../qualification/standalone-carla-stage1-2026-09-25.md)
separates preparation/build progress from runtime qualification. The relocated
single-map Game now passes real physics, native integration, Manual bridge
control, Autopilot, Brake/Tire/Return-to-road, fresh-profile/warm startup and
repeated clean shutdown. The final session lasted 863 seconds; peak owned
physical footprint was 13.80 GiB and free space stayed above 97 GiB. Residual
content findings are recorded, not silently suppressed. The requested current
window geometry/z-order handoff also passes: correcting the isolated launcher's
client height for the measured 32-point title bar gives exact native rectangles,
idempotent placement and background-below-demo ordering. A subsequent native
Autopilot/Safe Stop/session-close check passes without rebuilding the Game.
The matching wheel imports outside the development tree in Python isolated
mode with site packages disabled. No held-arrow-key, all-focus-transition or
clean-OS UI qualification is claimed. The preserved Test VM's DNS/Cloud-offline
condition is tracked separately from the isolated simulator proof. Stage 2 must
package the declared host interpreter/helpers and integrate standalone-launch
ownership into the ordinary operator path; this proof does not replace that work.
Stage 2 is **IN PROGRESS**, starting with the build-tool-only
[portable runtime artifact packet](portable-runtime-artifacts.md).
Relocated QEMU/Gateway smoke checks and a private Python 3.12/matching CARLA API
candidate now pass scoped tests with development-path reads denied. The private
client also passes the existing physical simulator probe and clean shutdown.
Prebuilt Presenter/Driving Control, web assets and the reviewed helper payload
also pass relocated entry-point and disposable HTTP/control-protocol checks.
Their later host-selector integration is recorded below; these initial fixture
checks alone did not qualify ordinary native launch or the complete UI story.
The separate Cloud Python candidate also passes a relocated offline proof:
41 hash-locked public wheels, the unchanged source-locked provisioning adapter,
native crypto/gRPC libraries and CLI entry points, without operator credentials.
Real Cloud enrollment/upload/provisioning remains unqualified for this candidate.
Pinned backend images are now exported and pass networkless disposable startup,
idempotent import and offline OCI integrity checks. The unsigned vehicle-input
candidate includes Factory .39/firmware, current reviewed VDP runtime with all
three profiles, four prebuilt service profiles and their contracts/notices.
Its separate-location, source-denied fixture checks pass without a rebuild,
new release allocation or Cloud signing/publication. The Factory uses a
hash-verified APFS clone; about 102 GiB remains free. The distribution-tool
suite now passes 92 tests. Fresh-engine import and ordinary operator integration
are not inferred from these scoped artifact proofs.
The first opt-in operator input selector is now implemented: existing VDP and
service Prepare can consume the independently locked portable input bundle.
All seven profiles pass real preparation with workspace/network access denied,
using a temporary release-catalogue fixture and isolated ledger; eight corrupt
input checks block before catalogue access/allocation. This is not signing,
publication or live installation. That preparation checkpoint did not switch
the working runtime; the later host handoff below now selects standalone CARLA.
The next [host-launch contract](../../../contracts/portable-host-launch/README.md)
now connects prebuilt Presenter/Driving Control, private Python/Gateway/OpenSSL
and the standalone Game to existing source/workspace owners. Isolated actual
source startup, repeated Start, secure local telemetry, native controls and
normal stop have been exercised without Test/Cloud attachment. A bounded
readiness-probe timeout no longer aborts the overall startup observation.
The real packaged Presenter HTTP entry and exact-owner idle stop also pass,
with its web server denied development paths and non-loopback connections.
The later [host handoff](../../qualification/standalone-host-handoff-2026-09-26.md)
proves native resize corrections without relaxing the geometry threshold or
rebuilding Unreal. Only Presenter was compiled. The accepted local successor
was moved into the ordinary catalogue without another large payload copy;
the ordinary simulator is now standalone, with the same Test .39 Online and
stationary through the existing mTLS selection path. No VM/manager restart,
Cloud mutation or further large cleanup occurred. The mixed-interpreter DNS
helper ownership transition remains an explicit next gate: connectivity works,
but private-UI helper lifecycle operations are not yet qualified. Browser visual
review was blocked by tool policy; CLI/native observations do not replace it.
The next [VM input slice](../../qualification/portable-vm-inputs-2026-09-26.md)
now assembles only about 2 MiB of firmware/helper inputs, reusing packaged
QEMU/Python through the existing lifecycle owners. Its source tests and actual
artifact integrity pass; it is not selected for the current run. The operator
requested complete assembly before further live-screen checks. Current legacy
owner handoff and guest/UI acceptance remain deferred, not waived.
The [Cloud/backend selector checkpoint](../../qualification/portable-cloud-backend-inputs-2026-09-26.md)
now connects the existing fixed workers and backend candidate readers to the
independently locked SDK/image artifacts. Source and actual input integrity
checks pass; current selections/owners are unchanged. No image import, Docker
startup, Cloud request or large artifact rebuild was needed.
The later [complete application and live checkpoint](../../qualification/portable-application-2026-09-26.md)
supersedes those historical unselected/deferred observations. All five groups
are assembled and selected; the separate complete export passes source/network-
denied verification. Packaged Test boot, strict reattachment, real maneuvers,
fresh backend/advisory results and external OFF/ON recovery pass. Missing QEMU
NIC data and stale pre-QM Gateway/client input selection were corrected without
rebuilding CARLA, Factory or services. Histories and Test/Production identities
remain intact; no clean install or serial-release cycle is claimed.

Stage 2's operator visual acceptance and fresh-engine import remain open;
Stage 3 is now authorized and starts with the non-activating offline transaction
slice under ADR 0018. Stages 4–7 and the remaining Stage 3 slices are not complete.
Download-host authorization, release signing identity and external distribution
review remain open; the accepted storage/lifecycle direction must be reflected
in executable contracts before runtime activation. See the packet checkpoints
for each boundary.
Track source changes, builds, artifact checks
and live qualification separately. At each gate record completed evidence,
open decisions, disk impact and the next bounded action. Do not undertake
unrelated UI redesign, model-threshold changes, video editing or cleanup.
