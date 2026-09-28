<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installable Distribution and Reproducibility Plan

- Status: Accepted planning; implementation and qualification are not complete.
- Version: 1.0
- Prepared: 2026-09-25
- Owner: Demo Solution Team
- Source baseline: [demo-v1.1 / Factory .39](../../qualification/demo-v1.1-return-point.md)
- Implementation input: [Current implemented architecture](../../architecture/current-implementation.md)
- Operational input: [Current operator workflow](../../operations/current-demo-workflow.md)
- Evidence input: [Documentation audit and open items](../../qualification/documentation-implementation-audit-2026-09-24.md)

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
Next is that secure OEM/SP enrollment adapter and guarded first-launch integration through
Demo Control, with retained-run ownership and all-instance retention gates
before live updates or destructive removal. Unselect is not uninstall. The
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

Use progressively stronger isolation:

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
baseline's remaining negative/recovery and host sleep/wake cases explicitly:
close what the proposed support claim requires or document a bounded exclusion.
Never silently turn an untested case into a passed one.

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
| Clean external boot disk and scheduled user setup window | Before Stage 6 native execution |
| Exact staging targets, release allocation and retirement authority | Before live mutation |

## Progress and immediate next work

### Current acceptance checkpoint — 28 September 2026

The operator accepted returning to stage exit criteria rather than starting
another independent installer increment. The historical slice notes below are
evidence, not a queue of simultaneous next actions.

| Stage | Current acceptance state | Next required result |
| --- | --- | --- |
| 0 — Inventory | Complete in its recorded scope | Preserve the input inventory |
| 1 — Standalone CARLA | Complete in its recorded scope | Reuse the qualified Game; no rebuild |
| 2 — Portable runtime | Open; independent empty-engine import passed | Finish Presenter visual acceptance and triage recorded native UI/advisory observations |
| 3 — Installation and first use | Partial | One installed-package path from setup through first launch; then lifecycle cases |
| 4 — Reproduction documentation | Partial supporting work | Coherent release-specific operator and developer routes |
| 5 — Verification | Source/fixture coverage exists | Repeatable installed-product and UI scenario evidence |
| 6 — Clean-system qualification | Not complete | Native clean-system installation and mandatory E2E |
| 7 — Publication | Not complete | Exact qualified release, artifacts, notices and supported scope |

The local source checkpoint is `70dac05`; existing `demo-v1.1` is unchanged.
Independent empty-engine import, repeated import and networkless backend startup
passed on 28 September. Native CARLA and Driving Control were observed directly;
Presenter review is still incomplete. These results are not clean-Mac proof.

Immediate order: finish Stage 2's operator-visible acceptance; then resume the
existing Stage 3 design as one first-use journey. Do not
add installer features, rebuild Factory/Game, change service models or start a
new demo scenario while that closure is pending. Existing-access verification
does not replace the accepted new-user registration/enrollment path. Source
test success and a retained Test run do not establish clean installation.

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
