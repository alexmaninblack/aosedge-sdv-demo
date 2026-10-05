<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 installation qualification

- Status: Installed engineering functional sequence complete on Kit 024; Kit 025 selected and native Setup launch/layout verified; obsolete staging copies removed and owned runtime closed
- Updated: 2026-10-02
- Candidate: Kit 025 / Setup 038 host corrections; functional evidence below belongs to Kit 024 and is not relabeled as a new native E2E pass
- Scope: Current user on dedicated M1 Pro; internal disk; current staging accounts
- Plan: [Installable distribution](../planning/active/installable-distribution-and-reproducibility.md)

## Initial candidate and automation

The complete kit manifest is pinned to
`ba93d179e4bacd3b9d24ff26ebca551990f2983dda2995726a732e322e63e971`.
The original Setup 031 is pinned to
`fb4d36fee289cd25ef2fb1d9ccc53e36937e0b8d72c1431a77ff5da18162b899`.
Source verification passed for 17,686 files including Setup, totaling
35,153,663,807 bytes. No product rebuild was performed.

The [test-only helper](../../scripts/qualification/README.md) initially passed 14 unit and
local-fixture tests. The reused installation reader passed its 34-test suite.
Coverage includes target pinning, private single-writer checkpoints, interrupted
transfer handling, sanitized failures, exact destination digests/modes/inventory
and rejection of extra files, links or corruption. These are not M1 E2E results.

The private configuration and attempt history are in
`.local/remote-qualification/`; run `m1-20261001-001`. They do not contain tokens,
keys or certificate contents and are not product state or the formal D4 dossier.
The full configuration binds the candidate, target, run and source identity.

## Live preflight

At 10:11 UTC the first SSH preflight timed out. The direct cable retained a
1 Gbit/s full-duplex link and an Ethernet neighbor entry. Subsequent checks
reached SSH and Screen Sharing without a network/security configuration change.
The cause of the brief unavailability is not established; do not call it a
proved sleep/wake recovery test.

At 10:14:34 UTC the repeated preflight passed in 2.328 seconds:

- MacBookPro18,3, arm64, macOS 27.0.1 build 26A434.
- 16 GiB physical RAM; zero reported swap use at idle.
- Internal storage; 422,492,844 KiB available, approximately 403 GiB.
- Expected console user; no detected demo process or occupied demo port.
- Docker, Homebrew and Xcode absent from their declared standard locations.
- M1's unauthenticated staging HTTPS request returned 200.

This is a transport/entry check, not Cloud authorization or runtime readiness.
Absence at standard paths is not a forensic assertion that all development
software is absent from the computer. Shared/global state remains inventoried
as relevant dependencies are introduced.

## Native installation and next steps

Verified staging completed at 10:25:19 UTC in 612.164 seconds, including source
verification, transfer and complete destination verification. All 17,686 files
passed digest, size, mode, ownership, link and inventory checks in a new private
directory on the M1 internal disk. No previous VM, demo run, development checkout
or credentials are included. This duration is not pure network throughput.
Native installation and local preparation subsequently passed as recorded below.
The remaining gates are declared Docker dependency readiness, first-use Cloud
enrollment and the installed serial E2E sequence. Record genuine OS consent/terms handoffs without
turning routine staging actions into repeated approval questions.

Remote Screen Sharing reconnects and shows the desktop. Initial text entry
produced Cyrillic characters and automatic clipboard insertion timed out.
Synchronizing the connection's keyboard language and selecting the local Latin
input source restored key-by-key input: the official Docker installation address
was visually checked and loaded on M1. The shared-clipboard option was not enabled.
Docker's Apple silicon DMG was downloaded through the official page in M1 Safari;
Docker Desktop 4.93.0 was copied into Applications through Finder. The first
launch reached its Subscription Service Agreement and macOS Local Network
permission prompt. At the first checkpoint both awaited user confirmation; no
terms were accepted, permission granted or subscription purchased then. The
subsequent consent and engine-readiness result is recorded below.

Native Setup 031 opened directly from its transferred DMG. Its file chooser
opened but sidebar navigation did not complete through this Screen Sharing
session; this is an unclassified remote-interaction observation, not a proved
installer defect. Entering the kit path in Setup's ordinary text field worked.
The remote input source can resynchronize to Cyrillic when local focus changes;
visually verify Latin input before entering any path or identifier. No malformed
path was submitted to installation.

Setup's **Check installation** passed, reporting the 32.7 GiB package and the
90 GiB reserve. **Install package** was performed through UI at approximately
10:37 UTC. It visibly completed with **Package installed — demo not started**;
the canonical pinned installation receipt was written at **10:39:06 UTC**.
The installed store accounts for 34,331,992 KiB by `du`, approximately 32.7 GiB;
Docker.app accounts for 2,263,640 KiB, approximately 2.2 GiB. No Xcode/Homebrew
or undeclared build dependency was introduced.

**Prepare local data** was then invoked through Setup. The new instance marker
was written at 10:43:13 UTC, and the canonical version-selection record at
10:43:46 UTC. The UI subsequently reported **Local setup complete — Cloud setup
remains**. Read-only reconciliation confirmed selection revision 1 with the
pinned Kit 021 digest and private mode 0600. The immutable installation receipt
remains `INSTALLED_NOT_ACTIVATED`; selection is a separate state, not runtime
readiness. The native Cloud-access and enrollment windows opened, but no token
was submitted and no certificate or Cloud resource was created on this host.

Read-only storage inspection after local preparation reported 383,930,784 KiB
available, approximately 366 GiB. The source kit and installed copy remain
separate; this checkpoint does not authorize their deletion.

The helper's status initially said `native_installation_not_started` after
every successful transfer, even after native installation. This was a harness
reporting defect, not an installer failure. It now directs the operator to this
native receipt without inferring unobserved UI state. A regression assertion
covers that distinction. The updated 15-test harness suite and `git diff --check`
pass; no product kit change is required. The stop probe's label was also narrowed
to `NO_DETECTED_DEMO_PROCESS_OR_PORT`: it does not observe Docker's first-use
helpers or prove that installation has not started. Earlier attempt records
remain unchanged.

## First checkpoint shutdown

At this first checkpoint, Docker consent/readiness, fresh staging OEM/SP
enrollment, Open demo and the serial E2E sequence remained outstanding. No
consent acceptance, token submission, publication or provisioning had occurred.

Setup and Docker were closed through their native UI. At 10:56 UTC the bounded
probe reported zero detected demo processes and zero occupied demo ports. A
separate read-only check found Docker's `docker-agent` helper orphaned after
normal Quit, with parent PID 1, zero reported CPU and no TCP listener. For
end-of-check cleanup only, SSH sent SIGTERM to that exact PID after rechecking
its executable, current-user ownership and parent. This is an explicit cleanup
exception to the read-only SSH diagnostic path, not installation or runtime
acceptance through SSH. At **11:00:07 UTC** a post-read found zero matching
Setup, Docker/helper, CARLA, controller-VM or driving/gateway processes. No files
were removed; package, instance and evidence remain available for resumption.

## Resumed first use — 11:17 UTC

After explicit user confirmation, Docker's Subscription Service Agreement was
accepted through its native UI. Optional Docker-account sign-in was skipped;
no account or paid subscription was created. The dashboard displayed **Engine
running**. At **11:17:25 UTC**, a read-only check independently confirmed engine
29.8.1, Linux/aarch64, zero containers, zero images and 8,319,770,624 bytes of
engine memory capacity. This qualifies dependency startup, not backend
containers or full-load suitability. The Local Network prompt did not reappear;
no separate permission-grant action was observed in this resumed session.

Native **Open demo** at approximately 11:18 UTC stopped before launch with
**Accessibility permission needed** for the signed Setup application. No
Presenter, VM or simulator was started. This is an expected macOS first-use
consent boundary, not a proved installer failure. Exact permission confirmation
was requested for window placement/inspection on this M1; Full Disk Access and
screen recording were not requested.

Independent native Cloud-form inspection used the exact staging domain and OEM
role. **Inspect saved attempt** completed with **No attempt recorded — ready for
an explicit token submission**, and the main window reported **Enrollment state
inspected — demo unchanged**. No token, certificate, Unit or service was created.
This proves the empty-state UI path only, not authentication or enrollment.

The bounded collection at **11:19:57–11:19:58 UTC** reported one Setup process,
zero occupied demo ports, approximately 365.5 GiB free, Docker present,
Homebrew/Xcode absent at their declared locations, 1.75 MiB swap and staging
HTTPS 200. No product rebuild or additional kit transfer was required.

Setup, Docker and the test Finder window were then closed through native UI.
At **11:27:10 UTC**, a separate process read found no Setup, Docker/helper,
CARLA, controller-VM or driving/control processes. The **11:27:28 UTC** stop
probe also confirmed zero demo processes and zero busy demo ports. This second
shutdown needed no helper termination exception. Installed files, data and
evidence were preserved.

## Native launch and remote display

At approximately 11:32 UTC, the specifically authorized Accessibility permission
was enabled for the signed Setup application on M1. On this macOS version the
control is under Privacy & Security, Device Control and Data Access. No Full
Disk Access or screen-recording permission was added. At approximately 11:54 UTC,
the matching System Events automation request for window layout was allowed.

The first launch encountered `WORKSPACE_BUILTIN_DISPLAY_UNAVAILABLE`: Screen
Sharing was using a high-performance virtual display rather than the physical
built-in screen. Switching the disconnected connection profile to Standard
restored observation of the physical display. Its default 1512-by-982 logical
resolution still failed the existing 1440-by-900 usable-workspace guard after
menu-bar/Dock exclusion. Selecting More Space, 1800-by-1169 logical pixels,
through M1 Displays settings resolved that condition. No product guard or
geometry tolerance was changed.

At approximately 11:54 UTC, native Open demo reported **Presenter opened**.
The empty instance intentionally had no CARLA or Driving Control window; their
absence was not treated as full-demo readiness. The generic Setup launch error
had obscured the more specific display cause in the operation record. Record
this as a diagnostic UX issue, not a reason to weaken display requirements.

## Fresh staging certificates and native access check

The user explicitly authorized obtaining one-time tokens with the existing
staging OEM/SP identities and sending them over the pinned SSH connection to
the unchanged signed Setup helper on M1. The official current-user operation
is `POST /api/v11/users/new-token/`. It requires neither a new email nor a new
account. Each token remained in memory and private standard input; no token or
private key was printed, copied into evidence or placed in Git. Development
private keys were not transferred to M1.

Setup generated each new RSA private key locally and completed exactly one
issuance per role. Authoritative reconciliation found the certificate count
increase from three to four for each role, with the prior authenticated identity
and authority unchanged. Inspect/recovery repeats issued nothing. The private
attempt records retain reconciliation evidence without token/key contents.

At 12:14–12:17 UTC the native UI inspected both saved attempts, inspected the
auto-populated pair locally, saved it through **Use this pair**, and ran
**Check Cloud access**. The final visible result was **Cloud prerequisites
observed — demo not started**. OEM access, default fleet, arm64, Factory model,
node type, Test verification set, SP access, OEM/SP association and VDP/Brake/Tire
delivery permissions were all confirmed. Both certificates were valid, with
expiry in September 2036. The main window then reported **Cloud access step
completed — demo not started**.

Issuance used the explicitly approved engineering standard-input interface of
the unmodified signed Setup helper, not manual entry into its secure UI field.
Native secure-field token-entry acceptance therefore remains **not exercised**.
The subsequent inspect/save/access-check actions did use the ordinary native UI.
Neither enrollment nor these access checks provisioned a Unit or published a
service. Kit 021 / Setup 031 remained unchanged.

## First Create on the clean Docker engine

Docker was reopened through native UI. Its engine reported running; a bounded
read independently confirmed version 29.8.1, Linux/aarch64, zero containers and
zero images. At approximately 12:22 UTC, **Create controller** and its exact Test
confirmation were selected once in Presenter. The operation stopped immediately
with `BACKEND_COMMAND_FAILED`; no VM-password prompt or controller startup occurred.

Read-only reconciliation confirmed no active or uncertain operation, no vehicle
journal and zero Docker images. Source inspection identifies the exact boundary:
`DemoLifecycle.create` checks both immutable backend images before environment
creation, while the installed package only contains their verified OCI archive.
No Setup action imports that archive into an empty engine. The existing
[backend contract](../../contracts/portable-cloud-backend-inputs/README.md)
explicitly prohibits loading during ordinary start/navigation and leaves a
separate explicit setup import open. Earlier same-Mac tests had available images;
they did not close this clean-engine integration gate.

**M1-FIRST-USE-01:** implement the missing explicit first-use backend import,
not an implicit load during Create or a manual engineering preload disguised
as installation success. The recommended bounded refinement is a separate
Setup dependency-preparation action: verify the pinned archive; use the declared
already-running Docker engine; reconcile the two exact immutable image IDs;
import only when missing; re-read IDs/architecture afterwards. Preserve unrelated
images, containers, tags and data. Do not build, pull, start Docker, create a VM,
contact Cloud or replay an uncertain import. Freeze this action's contract before
implementation and qualify empty-engine, repeat, interrupted-response and negative
cases. No import or product-source change was performed at this checkpoint.

## Shutdown after first Create diagnosis

Presenter and Docker Desktop were closed through their native menus. The idle
Presenter HTTP service was then stopped through the installed CLI's existing
`ui stop`, which validates the exact current-user owner and absence of active
or uncertain work. This SSH cleanup exception is not a substitute for native
installation acceptance. At **12:31:45 UTC** the harness recorded zero detected
demo processes and zero occupied demo ports; available internal storage was
382,667,048 KiB, approximately 365 GiB. A separate process-name-only read then
confirmed zero Docker/helper, Setup and native-runtime processes. No files,
certificates, Cloud objects or persistent state were deleted. The 15-test
qualification-harness suite and `git diff --check` pass.

## Historical checkpoint before Kit 022

This checkpoint is superseded by the Kit 022 results and current resume point
at the end of this document. It preserves the original diagnosis, not a current
instruction to rebuild.

**Setup 033** reconciled the exact images imported by Setup 032 without another
load. Same-window and reopened repeats pass, and ordinary native Create
Controller completed in 99 seconds. This is not full E2E completion or a
fresh-empty-engine import with Setup 033: the original load was performed by
Setup 032, whose result reconciliation failed as described below.

The next blocker is **M1-STATUS-01**: Kit 021 falsely reports the running
controller as switched off when the installed executable path contains spaces.
The minimal source correction and read-only live proof pass; it is not yet in
an immutable installed successor. Package the host correction without rebuilding
CARLA, Factory or services, verify the installed UI result, then resume the fixed
serial E2E sequence. Preserve the retained Test and fresh staging pair; do not
delete a journal or mutate a package to bypass selection guards. Any necessary
exact-Test replacement uses the existing authorized lifecycle. Docker terms and
the observed native permissions are complete. Do not repeat credential enrollment.

## Prepare backends implementation and candidate

The user approved the explicit Setup action on 1 October. The requirement,
ADR 0018, native setup contract and first-use guide now describe the same
boundary: selected pinned archive, already-running local Docker Desktop,
exact image inspection, one load when missing and durable attempt reconciliation.
No runtime auto-import, build, pull, tagging, deletion, container start, Cloud
request or fresh credential enrollment was added.

The transient isolated prototype passed four first/repeat/failure proofs before
source integration. The consolidated Setup suites pass **102 tests**, including
18 new backend-preparation tests. The existing backend-input and installed-Docker
suites pass another **9 + 4 tests**. Swift type checking and the compiled native
protocol self-test pass, including incomplete-image result rejection. An initial
type-check invocation hit a compiler-cache sandbox restriction; the explicit
temporary cache passed. An initial standalone Python test invocation omitted
the declared source import path; the corrected invocation passed. Neither was
a product or candidate failure. Standalone execution of the new test module
also exposed a fixture import-order dependency; importing its request-validator
dependency explicitly removed that dependency without changing product sources.

**Setup 032** was built against unchanged Kit 021 and signed with the existing
authorized Apple Development identity. Strict signature verification and the
embedded trusted-helper probe pass. Its designated-requirement digest remains
`2cd6abe5ddd0ce9733dbcd1762af34ba64136679033c1cabd22d4482e16dd11c`.
There is no Developer ID or notarization claim. CARLA, Factory, backend images
and the 32.7 GiB kit were not rebuilt or recopied.

- Artifact: `setup-preview-032-20261001.dmg`
- Bytes: `41283837`
- SHA-256: `e1740587aaa7bfaf046981aafd72a71604d05195b0564cec1e463a91a5b4eb33`
- Runtime pin: unchanged `ba93d179e4bacd3b9d24ff26ebca551990f2983dda2995726a732e322e63e971`
- Remote successor: `m1-20261001-001/setup032.dmg`; original `setup.dmg` and
  historical candidate identity remain untouched.

SSH transfer and the M1 digest/size check passed. A first transfer invocation
had a harness argument-assembly error; the remote target was proven absent
before the corrected transfer. Host-key verification was never disabled.

At approximately **12:59 UTC**, Screen Sharing showed M1's ordinary lock screen.
The user was asked only to unlock the existing session; no security setting or
new permission was requested. The new Setup has **not yet been opened** on M1,
Docker remains stopped, and no import has occurred. Native empty-engine,
same-window repeat, quit/reopen repeat and ordinary Create Controller gates
therefore remain **not run**, not passed. Source tests are not a substitute.

After unlock, open `setup032.dmg` in Finder, use the existing private-data
folder, first verify the stopped-engine explanation, then open Docker Desktop
and choose **Prepare backends**. Record timings, exact two images/platforms,
zero created containers/journal, repeat and reopened result before Create.
On import uncertainty, preserve its exact attempt and inspect; do not preload
or erase the attempt to force another load. The later fixed E2E order is unchanged.

At **13:05:20 UTC**, the end-of-check read confirmed zero Docker/Setup/native
runtime processes, zero demo listeners and no vehicle journal on M1. The remote
viewer was closed afterwards. The two transient local proof source files were
removed after their regression cases were retained in the repository; no runtime
or credential data was deleted. The final Setup regression rerun passed all
102 tests and `git diff --check` passed. Git commit/push was not part of this step.

External SSD checks are excluded. The three same-Mac deferred checks and
`VDP-TIMEOUT-01` remain open; recurrence on M1 is a new current failure.
Developer ID, notarization and redistribution gates are unchanged. No public
release, full-load 16 GiB suitability or clean-install success is claimed.

## Prepare backends live checks after unlock

At 13:13:09 UTC, native Setup correctly refused the stopped Docker engine with
`SETUP_BACKENDS_ENGINE_UNAVAILABLE`. No preparation attempt, vehicle journal or
container was created. The result was observed within 31 seconds; this is a
tool-observation upper bound, not an instrumented UI latency.

Docker was then opened normally. At 13:13:52 UTC its local engine reported Linux
aarch64 with zero images and zero containers. One **Prepare backends** action in
Setup 032 imported the pinned archive at 13:14:42 UTC. The result was
`SETUP_BACKENDS_IMPORT_UNCONFIRMED`, observed within eight seconds. Read-only
inspection found both exact images and no containers. Docker's default image
listing omitted the deliberately untagged imported images; `image ls --all`
and exact inspection found them. The import itself had succeeded.

The source correction adds `--all` to that inventory read, retaining exact
ID, Linux/arm64, service label and source-revision validation. No tag, pull,
second load or attempt deletion was used to conceal the failure. The Setup
regression passes **103 tests**, including an explicit untagged-inventory test.
The native protocol self-test and signature checks pass.

Setup 033 was built and signed with the same authorized Apple Development
identity. Kit 021 and all large payloads remain unchanged:

- Artifact: `setup-preview-033-20261001.dmg`, 40,247,491 bytes.
- DMG SHA-256: `ac8732db0e921436347b63bfbcf45a079c3f4bca2cc18b991dc2b7a89d805199`.
- Native executable SHA-256: `123c67bde73c3fb6c5149c9813a39de4c1f576a12baf13299e741b30770df9d0`.
- M1 copy: `m1-20261001-001/setup033.dmg`; transfer identity was verified.

At 13:25:48 UTC, the native action in Setup 033 reconciled the preserved attempt.
The UI reported **Backend images available — demo not started** and explicitly
said no import was needed. The private preparation record became `RECONCILED`
at 13:25:49 UTC, mode 0600, 260 bytes. A same-window repeat and a quit/reopen
repeat returned the same result, observed within nine and eleven seconds
respectively. The record's timestamp and size were unchanged after both repeats.
There were still no containers or vehicle journal before Create.

The exact imported image IDs are:

- Brake: `sha256:48f633748d225b27079e69a439e875745067a5248a7006c3b9685dc8a5e2baf1`.
- Tire: `sha256:5dddd12060c3e65f928e844a65f92ae8826d1e8e52dce66329f86682934c3326`.

**Open demo** opened Presenter. The ordinary native **Create Controller** action
completed at 13:36:16 UTC, with a 99-second duration shown in Trace. Subsequent
read-only reconciliation confirmed the manufactured Factory .39 Test, its
running QEMU process and two healthy backend containers. No Cloud Unit or
service release was created in this continuation; CARLA and Driving Control
were not started. Production was untouched.

## Installed controller status defect

Despite successful Create, Presenter displayed **Controller switched off** and
blocked progression. QMP confirmed the controller was running. The read-only
status probe shell-split the unquoted process listing before identifying the
executable. The ordinary installation directory `AosEdge SDV Packages` therefore
made the QEMU executable name appear to be a different path, excluding the VM.
The lifecycle owner's exact command check correctly recognized the same process.

The source fix reads the full executable separately, joins the two observations
by PID and then parses options. Missing, duplicate or changed process evidence
remains unknown, not a fabricated stopped result. The existing exact overlay
ownership check is retained. Five new regression methods cover spaced paths,
ordinary paths, unrelated processes, inconsistent reads and failed reads.

At 13:49:35 UTC a temporary read-only diagnostic process on M1 executed the
corrected function: the old function returned zero QEMU processes; the corrected
function found exactly one, matching the observed Test PID. It did not replace
the installed module or modify the running VM. **38 status tests and 57 Presenter
tests pass.** An earlier sandboxed test invocation could not bind local sockets;
the appropriately permitted rerun passed. That restriction is not a product
failure. Installed UI verification remains open until the fix is packaged.

During shutdown, the immutable-runtime guard detected 36 Python bytecode cache
files generated by earlier diagnostic invocations between 13:38:39 and
13:41:13 UTC. This was a diagnostic side effect, not a Setup/runtime defect.
Only those validated unlisted cache files were moved to a recoverable private
qualification directory. All declared payloads were preserved; subsequent
diagnostics use isolated Python with bytecode writes disabled. The ordinary
idle UI stop then succeeded without relaxing its ownership or integrity checks.

## Shutdown after backend preparation checks

The installed owner's ordinary VM and backend stop commands completed; the
journal was reconciled to `LOCAL_STOPPED` with a stopped Test, no PID and an
unprovisioned guest shutdown proof. The native Presenter and Setup windows were
closed, the idle UI service stopped, and Docker Desktop was quit through its
native menu. The engineering shutdown commands are cleanup evidence, not native
E2E acceptance.

At 13:59:44 UTC, harness attempt 11 recorded zero demo processes and zero busy
demo ports, with 373,798,884 KiB free internally (approximately 356.5 GiB). At
14:01:23 UTC a separate process-name read confirmed no Docker/helper, Setup,
Presenter, CARLA, Driving Control or QEMU process. The Test overlay, journal,
fresh staging certificates, backend data/images and preparation record remain
preserved. No Cloud object, release or retained Test was deleted. The final
Setup and harness reruns pass 103 and 15 tests respectively; `git diff --check`
passes. No Git commit or push was requested in this step.

## Efficiency refinement — installed scenarios and Kit 022

The authorized refinement extends the existing test harness, not the product
lifecycle or delivery plan. Private target records bind the exact installed
manifest, package path, instance and Test identity. Read-only checks now cover
installed selection, controller/QMP agreement, both backend health observations,
Presenter/process agreement and stopped state. Bounded `local-start` and
`local-stop` sequences call the installed owners, observe before acting, skip
already achieved states and reconcile uncertain actions without replay.
Candidate/source changes invalidate carried-forward pass claims. Each attempt
records separate operation/observation durations, sanitized facts and the
explicit `ENGINEERING` / native `NOT_RUN` distinction. Serial Cloud deployment
and native UI acceptance are not inferred from these checks.

The original harness and installed-scenario suites pass **15 tests each**.
Application export tests pass **14**, Setup tests **103**, and the earlier
status/Presenter gates remain **38/57**. No Factory, CARLA or service rebuild was
needed. The small host application correction was assembled with the existing
five payload groups into one new candidate:

- Kit 022 manifest: `36b8fbac7ede65d24f904d7780969a84a766726b5403bf4fbca72b4bd9223a15`.
- Setup 034 DMG: `7e2bdcc5bb38a3d6940e7b2f3cbf1d54dacdb6b4d4f9d93c9cfd32e2f5bf7fc5`.
- Native executable: `2583877a094b42c98ae96c25683c00b09f0d303ad4971c8d81b7335020ec1ae1`.
- Signing remains the authorized Apple Development identity; native protocol
  self-tests and strict signature verification passed. This is not Developer ID
  or notarization acceptance.

Private run `m1-20261001-002` transferred and verified the candidate from
14:40:25 to 14:42:58 UTC: **152.696 seconds**, versus **612.164 seconds** for the
original transfer/verification. Reusing an APFS clone of the verified predecessor
and transferring the delta avoided copying unchanged large inputs; all 17,686
destination files still passed the complete check. These are end-to-end staging
durations, not network throughput measurements.

Setup 034's signed embedded helper installed Kit 022 and selected revision 2.
These are engineering installation/selection results, not native button-test
claims. The previously owned, unprovisioned Test was retired after exact identity
and ownership checks; its working overlay/backend run data were deleted. Factory,
installation inputs, credentials and Production were preserved. No Cloud Unit
or published release was deleted or created.

### Native launch and controller preparation

An engineering Setup launch started the server but returned
`PRESENTER_NEEDS_ATTENTION`; Presenter later became visible. Create then stopped
before guest boot with `VM_KEYCHAIN_ACCESS_DENIED` at 14:58:00 UTC. The partial
Test was retained, and its idle Presenter was closed through its owners. No
credential/Keychain policy was changed and no password was placed in a command.

Setup 034 was subsequently opened through Finder. **Open demo** visibly reported
**Presenter opened**. **Continue preparation** resumed the same partial Test:
native Create ran from **15:09:04.720 to 15:10:20.115 UTC**, approximately
**75.4 seconds**, and completed. The Keychain failure did not recur in this
native launch context; this is evidence of launch-context sensitivity, not a
proved general Keychain root cause or permission fix.

At 15:10:03 UTC the installed status observer reported `RUNNING` and independent
QMP reported `running=true`. At 15:11:24 UTC the Presenter API agreed with both.
The full local baseline also found both backend containers healthy. This closes
the packaged observer regression that had reported the running VM as stopped
under an installation path containing spaces. Cloud readiness, installed vehicle
services and full-load behavior are separate, still-unpassed gates.

### Bounded scenario results

The native Presenter now progresses to **Start the local vehicle / Start
simulator**, rather than falsely reporting a switched-off controller. CARLA and
Driving Control were not started in this refinement; the full demo remains the
next qualification sequence, not a result inferred from controller readiness.

Private run `m1-20261001-002` records the following engineering sequences:

| Sequence | Duration | Result |
| --- | ---: | --- |
| Local stop, attempts 8–12 | 11.23 s | Controller and both backends stopped; Test retained |
| Local start, attempts 13–21 | 46.94 s | Controller/QMP agree; both backends healthy |
| Repeat local start, attempts 22–27 | 4.63 s | Six fresh reads; zero actions attempted |
| Presenter agreement, attempt 28 | 0.89 s | Presenter, status observer and QMP agree |
| Final local stop, attempts 29–33 | 10.80 s | Controller and both backends stopped; Test retained |

Within local start, VM start plus observation took 28.50 s, Brake backend start
6.94 s and Tire backend start 6.91 s. These are measured samples, not guaranteed
budgets. Expected pre-action reads can record `POSTCONDITION_NOT_MET` when the
requested target state has not yet been reached; the subsequent owner action
and final verification determine the sequence result. They are not newly found
product regressions. All attempts remain preserved rather than erased on pass.

After final stop, installed `workspace.close` and idle `ui.stop` both returned
success. Setup and Docker Desktop were quit through their native menus. At
15:20:55 UTC, attempt 34 confirmed **zero demo processes and zero busy demo
ports**, with 373,029,364 KiB free internally (approximately 355.7 GiB). The
independent process-name check also found no Docker/helper, Setup, Presenter,
CARLA, Driving Control or QEMU process. The
current Test overlay, journals, backend data/images and fresh certificates remain
intact. No Cloud publication or provisioning was performed in this refinement.

Both harness suites pass again: **15 original tests and 15 installed-scenario
tests**. This closes the bounded automation refinement and packaged status
regression, not Stage 6 or full installer acceptance. Remaining gates include
the native simulator/vehicle journey, serial VDP/Brake/Tire deployment and
updates, 16 GiB full-load behavior, offline recovery and ignition. The separate
fresh-empty-engine backend preparation and secure UI token-entry checks also
remain open. Resume from the retained installed candidate and Test; do not
restart the installation history or rebuild unchanged large inputs.

## Resume on 2 October 2026

The retained candidate is Kit 022 / Setup 034. Continue with the same installed
Test and issued staging certificates. Controller creation and the bounded local
start/stop checks have already passed. The next unpassed functional step is
native simulator startup, followed by the agreed serial platform/service
deployment sequence. Do not reinstall, recreate the Test or re-enroll credentials
merely to resume after the overnight shutdown.

At 06:17 UTC, attempts 36–37 confirmed M1 connectivity over the direct cable,
the same hardware/OS, the selected installed candidate and preserved Test
binding. No demo processes or occupied demo ports were detected. Available
internal storage was 372,158,812 KiB, approximately 355 GiB; SDV-Work was mounted
on the development Mac with approximately 485 GiB free. There were no unresolved
automation actions.

The initial network check could not reach staging. Wi-Fi was powered on but
had no association/default internet route, and DNS resolution failed. The
remote desktop subsequently showed the guest-network registration form; the
operator was asked to complete network access without changing the direct
Ethernet link. No Cloud mutation or credential operation was attempted. This is
a host-connectivity prerequisite, not evidence of a demo or certificate defect.

### Restored network and native simulator failure

After the operator restored internet, attempt 38 confirmed staging HTTP 200 at
06:21 UTC. The existing installed owner's local-start sequence, attempts
39–47, completed in **47.75 seconds**: controller start and observation took
29.55 seconds, Brake backend 6.43 seconds and Tire backend 6.84 seconds. Final
controller/QMP and backend health observations passed. These are engineering
resume results, not repeated native installation acceptance.

Native Setup **Open demo** reported **Presenter opened**. Workspace restore ran
from 06:26:17.771 to 06:26:19.356 UTC and was partial because CARLA and Driving
Control had not yet started. The Presenter then offered **Start simulator**.
The native start was attempted once, from **06:28:17.815 to 06:29:23.997 UTC**,
approximately **66.2 seconds**, and finished blocked with
`SOURCE_SIMULATOR_EXITED`. This duration includes the visible macOS first-use
verification of CarlaUnreal; it is not a measured healthy simulator startup.

The authoritative engine log identifies the cause: the installed Game requests
Metal SM6, the M1 rejects that graphics profile, and the engine falls back to
SM5. The package contains no cooked `SF_METAL_SM5` shaders, so the engine shows
**Shader Platform Unavailable** and requests exit. No matching crash report was
found. Available memory before exit was approximately 53 percent, with 3 MiB
swap in use; the evidence does not identify an out-of-memory failure. This is
`M1-GRAPHICS-01`, a simulator/package compatibility defect, not a Cloud,
certificate, network or controller failure.

The pinned engine's `MetalRHI.cpp` explicitly excludes adapter names containing
`M1` from SM6, with a comment that 64-bit atomics arrived on M2 devices. The
CARLA Mac target configuration instead removes SM5 and includes SM6 alone to
support its road materials. Its comment that Apple Silicon supports SM6 is
too broad for the observed M1 target. Do not override the engine's hardware
check or call an OS update a solution to this package mismatch.

### Bounded SM5 material proofs

Before any full rebuild, two isolated single-package cook probes used the
existing pinned engine and warm build, with a command-line-only SM5 override.
Canonical configuration/content, the accepted SM6 cooked output, installed kit
and Factory were not changed. Network-denied execution, a 15-minute deadline,
18 GiB owned-memory guard and 90 GiB free-space guards bounded each probe.

| Probe | Duration | Peak owned footprint | Result |
| --- | ---: | ---: | --- |
| Road master default permutations | 51.63 s | 3.35 GiB | Compile passed; 54 shaders, no material replacement reported |
| Five actual road material instances | 107.30 s | 4.10 GiB | Compatibility failed: three instances exceed SM5's 16-sampler limit |

The failing instances are `MI_Road_Asphalt_B`,
`MI_Road_Asphalt_B_LaneMarkingWhite` and
`MI_Road_Asphalt_B_LaneMarkingYellow`. Their compiler diagnostics report
17–19 samplers and **Default Material will be used in game**. Although the
cook process returns exit code zero and reports zero errors, its shader
warnings make this a failed compatibility gate. Merely adding SM5 to the
package would silently degrade road appearance; the isolated master-material
success cannot override the actual instance failures. No full cook or new kit
was started after this failed gate.

Compact proof logs and resource receipts are retained in the development
CARLA build's `evidence/sm5-road-material-20261002.*` and
`evidence/sm5-road-instances-20261002.*`. Isolated outputs are retained on
SDV-Work under `AosEdge-SDV/build-data/standalone-20260925/` in
`sm5-material-probe-20261002` and `sm5-instances-probe-20261002`. The
diagnostic helper is `Build-distribution-stage1-20260925/probe_sm5_material.py`;
it is not a shipped runtime or a product fix.

### Preserved shutdown and next boundary

The existing owner's local-stop sequence, attempts 48–52, completed in
**12.16 seconds**. Installed workspace close and idle UI stop succeeded. Setup
and Docker Desktop were quit through their native menus. At **06:44:28 UTC**,
attempt 53 verified **zero demo processes and zero busy demo ports**, staging
HTTP 200 and approximately **354.1 GiB** free internally. An independent
process-name check found no Setup, Docker/helper, Presenter, CARLA, Driving
Control or QEMU process. Both diagnostic cooks exited and left no engine or
shader-worker processes on the development Mac.

The same unprovisioned Test, overlay, certificates, journals and backend data
remain preserved. No Cloud provisioning, publication or deletion occurred in
this resumed check. Stage 6 remains incomplete at native simulator startup;
serial deployment, maneuvers, offline/online, ignition and full-load M1 behavior
have not been exercised.

The next decision is the graphics compatibility boundary, not another installer
retry. Recommended: retain M1 as the target and investigate an isolated SM5
material adaptation, preserving road markings, geometry, vehicle physics and
sensor semantics. Require shader success without default-material replacement
and visual equivalence before a warm cook/package and native M1 retry. If that
cannot preserve the intended scene, agree the visual compromise or a different
test-machine requirement explicitly. Keeping the SM6-only candidate and moving
qualification to M2-or-later hardware is an alternative, not demonstrated
support for all such machines. The current acceptance criteria are not silently
weakened, and no material or supported-hardware change has yet been applied.

### Accepted M1 graphics correction

On 2 October the user accepted adapting the graphics for M1, preserving road
markings, vehicle physics and sensor behavior. This closes the choice recorded
above; it does not authorize a reduced visual scene or establish hardware
qualification before the native tests pass.

A read-only Unreal inventory showed that six direct road-master sample nodes
could use shared-wrap samplers with matching wrap addressing, default filtering
and World texture group. Their effective texture overrides across all five
cooked road instances were checked too. Virtual textures and the normal-map
sample were excluded. Isolated copies of the master and five instances retained
their parent hierarchy and texture parameters. Their SM5 cook completed in
**103.13 seconds**, peak owned footprint **4.08 GiB**, with no material compile
failure, sampler-limit error or default-material replacement.

The same six-property correction was then applied to source `M_RoadMaster`.
All **519 graph expressions** remain. First application took **10.37 seconds**;
an **8.33-second** repeat reported `ALREADY_APPLIED` with zero changed nodes.
The original asset is retained as a compact rollback input. Its SHA-256 is
`d390ee3290c276ad3fdebe8f578a3788393157e9ad2e08d51c4efa2d088b6b0b`;
the corrected asset is
`d28fd9eb7431e85dfcf07a808827ff246c36d18dad6c5ba6442fb99149e31cbe`.
Source helper `Util/BuildTools/road_sampler_profile.py` reproduces and validates
the edit. The focused BuildTools suite passes **8 tests**, including incompatible
texture rejection and narrow-profile checks.

Canonical and warm-snapshot Mac configuration now request **SM6 and SM5**,
preserving the former capable-Mac profile while adding M1's required profile.
At approximately 07:00 UTC a guarded full Town10 cook started against an
isolated APFS clone on SDV-Work, reusing the retained file cache and engine.
The profile change correctly invalidates previous cooked packages in that
clone; the original completed cook and installed Kit 022 remain untouched.
The full dual-profile cook completed successfully in **3,295.21 seconds**
(54 minutes 55 seconds), with **18.43 GiB** peak owned footprint and at least
**143.2 GiB** free on the internal disk. Both SM5 and SM6 global shader caches
exist; the log contains no material compilation failure, sampler-limit error
or default-material substitution. Existing historical soft-asset warnings remain
recorded, not silently reclassified as new regressions. No C++ engine, Factory
or service rebuild was performed. Focused source regression totals **156 passed,
one skipped**; corrected test import-path invocations are recorded separately.

The packaging stage exposed a build-only relocation defect: Xcode resolved the
entitlements and Info.plist input paths relative to the SSD-backed Intermediate
directory. The initial UAT process returned zero despite nested Xcode failure;
it was not accepted as a pass. Supplying both verified absolute resource paths
completed the same stage in **227.86 seconds**, with explicit `BUILD SUCCEEDED`.
No shader recook or security-permission change was required. Package integrity,
actual M1 rendering and live behavior remain pending here.

The retained Test is unprovisioned and stopped. A candidate change cannot reuse
it in place: the existing selector deliberately rejects a retained run. After
the successor has been verified, retire that exact owned Test through Demo
Control under the standing authorization, then select the successor and create
a new Test. Preserve certificates, Factory, the prior kit and evidence. Do not
delete its journal manually or weaken the selection guard.

### Pinned graphics successor

Kit 023 / Setup 035 was assembled on 2 October. The application export changes
only the host and VM manifest locks; VM payload bytes are unchanged, and the VM
manifest only binds the new host. All 36 file-backed Mach-O sections of the Game
remain unchanged after re-signing. The same four sandbox/network/debug
entitlements, strict deep signature verification, 34-prop catalogue and all
non-simulator host inventory entries pass. Diagnostic material copies are absent.

- Kit manifest: `f3530694325cc887b8ff7061cf8c122bc12b50bf57a36710a7da99a3b6c74560`.
- Host manifest: `38c9a0fcbed3be42a71f2fa3c8cc81a82c499e50bc40ef5fda19d7899cd7adf0`.
- Setup DMG: `c684a1e10d6595672494e4bd1ea4d10f7eac6c4577c5ffc4253373aee01c0372`.
- Setup executable: `a72d812e2b33be654252e24ace367149d50c29ad7819f47cca1f108e392b6369`.

Host assembly/verification took **221.73 seconds**, full kit assembly
**129.47 seconds**, and native Setup build/DMG creation **30.30 seconds**.
The Setup protocol test passes; the authorized Apple Development team and
designated requirement match Setup 034. Developer ID/notarization is not claimed.
Private harness run `m1-20261002-001` binds this candidate for transfer and native
retest. These build results do not qualify M1 rendering or the full E2E.

### Graphics transfer and early failure cleanup

Kit 023 / Setup 035 was transferred and fully verified on M1 from 08:18:59
to 08:28:29 UTC on 2 October: **570.908 seconds**, **17,687 files**. It was
staged, not selected or launched. The installed Kit 022 Test remained stopped.

The exact unprovisioned Test `68aa1250-f0b6-4bf2-a677-092fb22c767b` was then
retired through Demo Control under the standing authorization. The first attempt
took **21.46 seconds** and returned partial. Backend cleanup completed, but the
VM overlay and run journal were retained. The source directory contained only
`input.json` and `simulator.log`: CARLA had exited before the runner could start
and produce its terminal `manifest.json`. Local cleanup incorrectly required
that nonexistent runner receipt even for this exact stopped, never-assigned run.
This is a separate cleanup defect, not a second graphics or Cloud failure.

A read-only transient proof planned only eight owned files and four directories,
left the journal unchanged and passed ownership/open-handle checks. The source
correction accepts only the exact current pre-runner case defined in the
[run-state contract](../../contracts/demo-run-state/README.md). Historical
unreceipted fragments, unknown or runner output, wrong bindings, live owners and
unsafe files still block cleanup. No fake completion receipt is introduced.
Regression passes **51 environment/image tests** and **147 adjacent lifecycle,
retirement and source tests**. The initial sandboxed invocation could not inspect
processes; the same tests passed with diagnostic access, without weakening gates.

At **08:55:58 UTC**, one bounded recovery resumed the existing retirement
checkpoint through Demo Control with that same tested method loaded transiently
in the recovery process. It completed in **5.42 seconds**. The exact Test overlay,
current source outputs and journal are absent; installed package source was not
changed and the transient method was restored before process exit. The Test had
no Cloud Unit, so no Cloud deletion occurred. Factory source, certificates,
package versions and non-target resources remain. This is engineering recovery,
not native acceptance of the repaired installer.

Kit 024 contains the permanent correction. Its only application-file difference
from Kit 023 is `environment.py`; all five payload groups, the dual-profile CARLA,
Factory and service bytes are reused unchanged. Assembly took **134.31 seconds**.
Its manifest is `21952bba1fa1e4dc44638534abffaf03453ba7bb47407b11f1c4416b9d4f5813`.
Native installation, rendering and full E2E remain pending. The separate accepted
TODO is to unmount obsolete M1 Setup images and retire unused installed/staged
copies after successor verification, preserving required rollback and evidence.

### Kit 024 installed continuation

Kit 024 was staged using the already verified predecessor as a local APFS clone
plus its exact changed files. All 17,687 entries passed destination verification
in 247.705 seconds; network transfer was 41,533,771 bytes rather than another
complete payload. Setup 036 retains the authorized signing team and independent
Kit 024 pin.

The user requested larger automated batches with minimal intermediate waits.
The unchanged signed Setup protocol completed preflight in 4.52 seconds,
installation in 92.26 seconds and selection in 35.13 seconds. Revision 3 selects
Kit 024 and retains Kit 022 as predecessor. These are engineering API results,
not native button acceptance. Existing credentials were retained.

Prepare Backends then exposed `SETUP_BACKENDS_RECORD_INVALID`: the completed
import receipt from an earlier kit still references its old manifest, although
the archive and exact installed images are unchanged. A local transient proof
reproduced the failure and passed with the narrow completed-predecessor rule.
The source correction passes 106 Setup tests, including predecessor reuse,
uncertain attempts, changed archive, changed engine and malformed pin negatives.
Setup-only rebuilding is sufficient; Kit 024 and simulator bytes are unchanged.
Native regression of that correction is still pending.

The installed Create path independently verified the existing backend images.
The first engineering call created the Test but lacked a native password
provider; it stopped at `SSH_ENROLLMENT_REQUIRES_INTERACTIVE_PASSWORD`, not a
guest crash. Native Setup Open Demo succeeded, and Presenter Continue preparation
used the existing native credential access. At 09:34:48 UTC the exact Test
`72a7ab99-9b4f-489f-aa78-4bd305e76455` reached `CONTROLLER_RUNNING`, with both
backend processes started. Native continuation took 19.81 seconds. The earlier
layout observation is incomplete because simulator/control windows did not yet
exist; it does not qualify the final layout.

Temporary qualification batches call the same installed Presenter operations,
bind this exact run and staging domain, record each request ID before dispatch,
poll the existing operation to its terminal result and stop on uncertainty.
They do not change product ownership or count as native visual acceptance.
Simulation, serial release delivery and full-load E2E remain in progress.

### First component delivery and first use ordering

On 2 October, the packaged CARLA start completed in 102.49 seconds. Native
Screen Sharing showed the rendered Town10 road and car using `SF_METAL_SM5`,
with Driving Control present. This closes the previously blank graphics
observation, not the complete motion or layout gate. Driving Control overlaps
the Presenter and its bottom buttons are partly obscured by the Dock; the
workspace observation reports differing controller geometry. Layout remains open.

VDP 125.0.0 / V1 was prepared in 4.03 seconds, signed and published in 12.07
seconds, then observed READY in staging. Provisioning the exact Test took
44.24 seconds; the repeat connection check took 4.03 seconds without changing
the driving mode. Native Space selected Safe Stop. The guest then reported
active slot A, version 125.0.0, seven read paths, `REPORTED_READY`, source LIVE,
matching process slot and zero VDP restarts. Advisory is correctly not
applicable to this V1 profile. No later VDP version was published.

Brake 101.0.0 / V1 preparation took 6.05 seconds, publication 16.11 seconds,
and the focused READY observation 6.13 seconds. Assignment stopped at
`SERVICE_SUBJECT_UNRECORDED_LABEL_COLLISION`, before any Cloud create, bind or
assign POST. The new M1 installation had not selected the existing unbound
Subject references before Create Controller. Cloud access READY had not
established this separate first-use requirement. This ordering omission must
not be reported as service delivery or a Brake runtime defect.

The failed preflight also exposed a cleanup defect: its identity-free local
placeholder and empty operation steps blocked normal Test retirement. A
transient local proof reproduced this and demonstrated that only the exact
no-POST collision can be excluded from retained Cloud Subjects. Source
regression passes 79 assignment, single-Test retirement and first-use tests.
Unknown create outcomes, recorded identities, attempted steps, foreign Test/
owner bindings and unexpected fields remain blocked. The private receipt is
not cleared or rewritten to claim success. An initial broader sandboxed test
invocation could not run process inspection; it was not a product regression.

Authenticated read-only checks found exactly the eligible Brake Subject
`78d05c9c-cdf6-45cc-ab28-df2a4d3ac0d7` and Tire Subject
`ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb`, each with the expected SP service and
zero recipients. The scoped Test `72a7ab99-9b4f-489f-aa78-4bd305e76455` and
Cloud Unit `2a4a5a25-0c3d-4833-9766-49700351f2bf` were retired through Demo
Control in 56.08 seconds, using the tested cleanup function only in the
recovery process. The immutable installation was unchanged, and the function
was restored before exit. This is engineering recovery, not installed native
acceptance of the source correction. Factory, credentials, published versions,
Cloud Subject/service objects and non-target resources were preserved.

Both exact Subject references were subsequently saved through the installed
first-use owner, with fresh authority and zero-recipient checks. No credentials
were copied and no Cloud object was mutated by saving these references.

### Setup 037 backend regression

Only the 40,377,451-byte Setup update was transferred, not another runtime kit.
Destination DMG SHA-256 is
`015e2833d977e0134f5ff913885c4d8a072a66408c220d7926feb8c57fb11187`;
the executable and strict signature verification passed. Through this signed
Setup's unchanged bridge, Prepare Backends completed in 5.38 seconds and its
repeat in 4.06 seconds: both exact images verified, no import attempted,
no runtime or Cloud change. This qualifies completed-predecessor receipt
reconciliation on M1, not a fresh-empty-engine import or native button click.

The replacement Test `23068fcc-f5f7-4d07-916e-123e5fcc7d6e`, Cloud Unit
`6d49490c-5dfc-4c60-bebc-e8ee75d731fe`, was created in 78.45 seconds. Warm
CARLA start took 46.25 seconds and provisioning 44.23 seconds. VDP125/V1 was
reused without republishing. Brake101/V1 assignment completed in 24.15 seconds
after the exact Subject references were selected; the earlier collision did
not recur. One follow-up connection request was not dispatched while source
recovery was busy; provisioning had completed. No mutation was replayed.

### Serial installed function results on 2 October

The fixed sequence was executed through the installed Presenter and Demo Control
engineering interfaces, with exact Test/staging pins and durable request IDs.
The next profile was not published until the preceding installation/function
gate passed. Real CARLA physics generated the inputs; model configuration and
thresholds were unchanged. Engineering success is not native button acceptance.

| Installed profile | Release | Functional observation |
| --- | --- | --- |
| VDP V1 | 125.0.0 | Seven inputs, READY/LIVE, zero automatic restarts |
| Brake V1 | 101.0.0 | Complete window: 78 samples, all eight chunks durably received |
| VDP V2 | 126.0.0 | Fifteen inputs, READY/LIVE, zero automatic restarts |
| Brake V2 | 102.0.0 | New condition assessment after the dedicated physical maneuver |
| VDP V3 | 127.0.0 | Twenty-three inputs, READY/LIVE, zero automatic restarts |
| Brake V3 | 103.0.0 | New assessment and Gateway APPLIED advisory fact |
| Tire V1 | 53.0.0 | New assessment, INSPECTION_RECOMMENDED and Gateway APPLIED fact |

The automated continuation from the Brake V2 maneuver through Tire's functional
result ran from approximately 10:22:50 to 10:26:18 UTC without an operator
checkpoint. VDP V2/V3 publication took 14.13/16.17 seconds, Brake V2/V3
publication 20.19/20.19 seconds, and Tire publication 16.13 seconds. Tire
assignment took 22.18 seconds. The dedicated maneuvers took 23.23–24.54 seconds
wall time, including physical stop and placement; their simulated motion was
13.0–13.4 seconds. These are observations on this M1, not service-level promises.

Both Reset Driver Advisory commands reached matching Gateway CLEARED results.
The unselected model remained unchanged and previous assessment history was
retained. Return to road completed in 2.77 seconds, stationary in Manual with
Autopilot false. A qualification receipt filename collision interrupted result
recording after the first successful reset; the exact command was reconciled
and not resent. This was a test-helper failure, not a second product reset.

### Focused offline recovery

External OFF and ON used the normal selected-Test connectivity owner. Brake and
Tire each performed a real maneuver while OFF. Between the settled OFF snapshot
at 10:35:32 UTC and final OFF snapshot at 10:36:37 UTC, backend assessment counts
remained 3 and 1. Local model state advanced and the captured product queues
contained two Brake and five Tire messages. VDP remained READY/LIVE and Cloud
reported OFFLINE. This short interval is not the historical five-minute soak.

After ON, captured queues were empty at the bounded read 8.79 seconds into the
drain check. The exact queued assessment IDs appeared at their backends; counts
advanced to 4 and 2, and Cloud returned ONLINE. Boot identity was unchanged.
The local projection reads fixed model/outbox facts through the existing pinned
guest access; it neither reads credential files nor injects telemetry. It does
not qualify every message category, uninterrupted UI freshness or token-cycle
soak. Private evidence is in `Build-distribution-stage1-20260925/evidence/` on the
development host, with `m1-024-` serial and `recovery1` receipts.

The normal `vm.stop` correctly rejected the still-selected controller with
`CURRENT_VEHICLE_REQUIRES_PARK_OR_DETACH` before shutdown. The separately accepted
engineering ignition check therefore uses graceful guest poweroff after fresh
physical Safe Stop verification, then normal VM start and automatic restoration.
No guard, source selection or journal is altered to force that test to pass.
### Ignition and completed functional sequence

Graceful guest poweroff reached STOPPED in 4.48 seconds. Normal VM start took
34.22 seconds; VDP127 READY was observed 15.51 seconds into its subsequent
readiness check at 10:40:07 UTC. The boot identity changed from
`242ae187-c7e3-46af-a0cc-a3e22282f719` to
`91965ab3-7d14-416c-90e3-222ffa974647`. The same Unit/Node, model projections,
producer epochs and backend histories were preserved. Automatic reconnection
returned fresh, unheld Safe Stop at zero speed and full brake, without another
provision or Autopilot start. Both postboot physical maneuvers produced new
assessment IDs. This closes the separate engineering ignition test, not host
sleep/wake or power loss with queued data.

At 10:46 UTC, native Screen Sharing showed both backend cards and Driving
Control agree on Inspection recommended, with Cloud Online and Safe Stop.
The controller overlap remained visible and was not reported as a layout pass.
Continuous frame-by-frame UI timing and SOTA while moving were not qualified.

Normal installed Finish completed in 60.45 seconds at 10:49:40 UTC for Test
`23068fcc-f5f7-4d07-916e-123e5fcc7d6e` and Unit
`6d49490c-5dfc-4c60-bebc-e8ee75d731fe`. Its owner confirmed Unit/Node absence,
retired local Test state and run-scoped backend data, and preserved Factory,
credentials, published releases and release continuity. No transient cleanup
function was used for this final Test. At 11:00 UTC, the remaining Presenter
server/windows were closed; the backend containers were absent or stopped,
and the checked simulator, VM, native runtime processes and test listeners were
absent. A shutdown helper initially attempted a backend operation after Finish
had removed its journal; reconciliation established the completed cleanup and
did not replay Finish.

### Batched host corrections

The layout failure was caused by requesting a combined window smaller than
AppKit's actual 900 × 502-point minimum. A transient pure-geometry proof
reproduced overlap after clamping; budgeting those minimums preserves the
three-region composition and the exact 2056 × 1224 reference layout. The source
correction passed all 28 workspace tests. Native visual qualification of the
corrected M1 layout passed in the focused closure below; this is not a
font-scaling or Dock workaround.

Kit 025 packages that correction together with the already-tested narrow
no-POST assignment cleanup fix. Its manifest is
`cdc976a372b5294984769c4dbb1dbbe1c527baeeb6883c36a12469933641380c`.
Only `workspace.py` and `service_assignment.py` changed in the application;
all five large input groups are unchanged APFS clones. Setup 038 contains the
completed-predecessor backend receipt correction. Its DMG SHA-256 is
`1ecb9b49d3842b263659915269053fe19f89407f75431854373cd075c2271b2e`.
Signing remains Apple Development, not notarized distribution.

The kit was transferred as three changed files and the small Setup DMG, without
retransmitting large runtime inputs. Installation passed in 89.07 seconds.
Selection initially refused the qualification adapter itself because it was
using Python from the old installed package. The refusal correctly preserved
the active selection; the adapter was moved to Setup's private Python and only
selection/preparation was resumed. This does not require a new kit or a weaker
consumer-ownership check. Native acceptance and remaining first-use cases stay
separate from these engineering results. `VDP-TIMEOUT-01` remains deferred.

### Native host closure and cleanup

Kit 025 selection completed in 34.20 seconds with revision 4, current Kit 025
and previous Kit 024. Prepare Backends completed in 6.14 seconds. At approximately
11:19 UTC the native **Prepare backends** button independently reported that
both exact images were available and verified, with no import needed. At
approximately 11:20 UTC native **Open demo** opened Presenter and verified its
windows. These are native acceptance results for those paths, not a fresh
empty-Docker import or another full installation.

A single automated window-check sequence created the local unprovisioned Test
`e0fc04a9-9cee-4a28-92cc-2493401f8717` in 84.38 seconds and started CARLA in
100.41 seconds. No Cloud Unit or new service release was created. The display
changed while the native applications registered, and the existing bounded
workspace recovery settled automatically at 11:24:59 UTC with no problems,
no pending retry and verified z-order. A redundant explicit restore met an
HTTP refusal during this recovery; the successful lifecycle actions were not
replayed. The qualification helper now waits for workspace recovery as well as
other owners before dispatching a subsequent operation.

At 11:27 UTC Screen Sharing showed CARLA above Driving Control/Telemetry on the
left, Presenter on the right, and the common header above them. Neither the
900-point-wide controller nor its controls overlapped Presenter or the Dock.
The car remained in Safe Stop. This closes the native minimum-size layout
correction; it does not relabel the earlier engineering service run as native
UI E2E. One earlier helper request omitted the required image identifier and
was rejected before creation; this was a harness schema error, not a product
failure or a reason to rebuild.

Normal Finish retired the local window-check Test in 26.18 seconds. Runtime
shutdown then confirmed no owned Presenter, simulator, controller/gateway or
VM process and no test listeners. Setup and Docker were closed through their
native UI. At 11:37 UTC the final shutdown receipt also confirmed their absence
and no remaining qualification disk-image mount. Packages, Factory, credentials,
published releases and rollback inputs were retained.

Cleanup unmounted nine obsolete Setup attachments, including duplicate mounts,
then removed the staged `kit` directories for `m1-20261001-001`,
`m1-20261001-002` and `m1-20261002-001`, plus their five obsolete Setup DMGs.
Candidate markers, small manifests and diagnostic evidence were retained.
The current `m1-20261002-003` and rollback `m1-20261002-002` staged candidates
were preserved. Setup 038 was also unmounted after exit, without deleting it.
The obsolete copies were permanently removed; reconstruction requires their
build inputs, not Trash recovery.

The measured final removal increased free space by 210,554,880 bytes, about
201 MiB, leaving approximately 318 GiB free. Large staged copies shared APFS
blocks, so their apparent directory sizes are not additive reclaimable space.
The cleanup adapter had to distinguish mounted-image backing handles from
application handles and account for read-only staging directories and retained
manifests. These adapter corrections did not change the installed package.

Two older installed versions remain in the version store, separate from the
staged copies: the current product has no supported version-removal operation.
They were not deleted manually or reported as cleaned. Current/previous
selection remained unchanged. A supported removal path is an explicit open
cleanup item, not an installation or functional-test failure.

### Remaining qualification boundaries

The measured installed engineering scenario is complete. Native Setup backend
preparation, Open demo, rendering and corrected window layout are also observed.
A continuously observed native operator E2E, secure token-field entry, and
fresh-empty-engine preparation with the final Setup are not established by these
results. SOTA while moving and the historical five-minute offline soak were not
qualified in this run. On 2 October the user excluded host Mac sleep/wake from
the current qualification scope; this is not a passed test or a support claim.
Controller ignition evidence remains separate. The explicitly deferred same-Mac
cases, redistribution and notarization gates remain separate. Do not rerun completed
functional gates merely because the host-only candidate number changed.
