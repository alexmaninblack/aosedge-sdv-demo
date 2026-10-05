<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installer and launcher operator experience audit

- Date: 2026-10-02
- Status: Direction accepted on 2 October; implementation and qualification incomplete
- Scope: Delivery, first installation, Cloud access, first working demo and repeat launch
- Inspected baseline: Setup 038, Kit 025, current native Setup and Demo Control source

The installed functional demo has run on the clean target Mac. This proves that
the packaged system can work, not that a new operator can reach it unaided.
The current interface exposes internal transactions instead of guiding the
operator toward a running demonstration. Simplification needs to cover the
delivery artifact and the handoff to Presenter, not just the Setup window.

This audit uses source, contracts, the operator guide and existing native test
evidence. It is not a fresh usability study or another live qualification run.
No runtime or installation behavior was changed for the audit.

The user subsequently accepted this direction. The first execution milestone
is a complete single DMG, transfer to the dedicated M1 and installation from
that mounted media. Audit/cleanup of the development Mac precedes assembly.
This packaging milestone does not claim that the entire guided wizard and
automated demo journey are already implemented.

## Scope decision

The user excluded host Mac sleep and wake from the current qualification on
2 October. This is an exclusion, not a successful recovery test or support
claim. Controller ignition off and on remains a separate requirement with its
existing evidence. The audit discussion is complete and the accepted first
single-media milestone is executing; completed functional evidence remains
valid within its scope.

## Findings

| Area | Observed behavior | Effect on a new operator |
| --- | --- | --- |
| Delivery | The current DMG is about 39 MB and carries Setup and its bootstrap. The complete kit is separate; the guide describes approximately 32.7 GiB of logical runtime payload. | Receiving and opening the DMG alone is insufficient. The operator must obtain the matching kit and find its root directory. |
| Main screen | Three path fields and six peer actions. The three-step heading ends at Prepare local data, before backends, Cloud and launch. | The visible sequence does not describe the whole task or identify a single next action. |
| Action availability | Backend, Cloud and launch enablement starts from a nonempty state-path field. Deeper checks reject invalid state. | The UI invites actions which the selected instance cannot yet complete. Correct rejection is not good guidance. |
| Cloud access | Existing certificates require separate Inspect, Use and Check actions. New enrollment exposes domain, role, saved-attempt inspection, token entry and recovery controls. | Routine setup and exceptional recovery compete for attention. The operator must understand internal identity operations. |
| Shared Cloud objects | A separate dialog exposes exact Subject/service references and eligibility. | An infrastructure conflict becomes a normal-looking onboarding step. Ownership checks are necessary; UUID-driven navigation is not. |
| Dependencies and permissions | Docker installation/start is separate. Accessibility can block launch. Display constraints and VM bootstrap access introduce further operator work. | Requirements arrive across several applications rather than in one early readiness checklist. |
| Open demo | Opens Presenter, not a fully operational vehicle and services. The completion text acknowledges that distinction. | The button promises a broader result than the action delivers. More setup remains after the apparent finish. |
| Quick mode | DemoPreparation already groups VM/backend/simulator startup, VDP V1 preparation/publication and provisioning. Activation and product results remain separate; it does not deliver the full Brake/Tire evolution scenario. | Useful orchestration exists, but Quick mode is not yet the complete newcomer journey. |
| Return visit | Instructions tell the operator to reopen Setup and select an existing private-data folder. The main UI does not restore a validated last-instance selection automatically. | The user must remember implementation paths to launch an already installed product. This is a presentation issue, not loss of the durable backend records. |
| Feedback and documentation | Technical phases and diagnostic codes are prominent. The entry guide mixes current steps with historical candidate evidence and recovery caveats. | Users need engineering context to distinguish waiting, success, required input and failure. |

Evidence: [native UI](../../scripts/distribution/native/Setup.swift),
[Setup builder](../../scripts/distribution/setup_build.py),
[existing Quick preparation](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/demo_preparation.py),
[Presenter guide](../../apps/presenter-ui/src/app/StudioWorkspace.tsx),
[VM access](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/native_access.py),
[operator instructions](../getting-started/installed-preview-cloud-first-use.md),
and [M1 qualification](../qualification/m1-installation-2026-10-01.md).

## Proposed delivery

Deliver one versioned DMG with one obvious application entry, **AosEdge SDV Lab**,
and its complete verified runtime payload. The operator should not download a
second kit, choose a manifest or browse a payload folder. The mounted volume is
installation media, not the permanent runtime location. Do not rely on an
application automatically executing when a disk image mounts.

First launch installs the persistent application and runtime into supported
locations. After installation, launch the installed application; the DMG can be
ejected. Future launches use Applications. Keep the setup and launcher identity
stable rather than producing a new permission identity for each release.
The installed application runs onboarding when needed and otherwise offers
Start demo. The final application placement and identity migration must be
specified before implementation.

Keep immutable packages and private instance data separate internally. Hide
their folder choices behind Advanced settings with safe defaults. Do not
duplicate the full payload inside both the installed launcher and package store.
Report download size, installed size and peak free-space requirement separately;
32.7 GiB is not a measured compressed DMG size. Retain bounded current/rollback
storage and offer a supported way to remove obsolete installation media.

Include only components cleared for redistribution. Docker remains an explicitly
declared dependency with guided official installation and required user consent;
do not silently bundle it or accept its terms. Cloud access and any missing
dependency download still need internet. Never include developer credentials,
certificates, personal Cloud state or previous vehicle runs. Developer ID,
notarization and redistribution gates remain open, independent of this UX work.
A small network bootstrap installer is a possible later delivery mode, not a
second implementation track for this iteration.

## Proposed operator journey

1. **Set up SDV Lab.** Detect the supplied payload and existing installation.
   Check architecture, OS, disk, display and dependencies early. Show one
   primary action; combine the ordinary local check, install, selection and
   image-preparation sequence under its explicit intent. Preserve each
   transaction and its error handling internally.
2. **Connect to Aos Cloud.** Show the chosen environment clearly. Guide a new
   operator through official account/access prerequisites and role-labelled
   enrollment; offer existing certificates as an alternative. Perform safe
   inspection automatically and explain only the inputs currently needed.
   There is no implemented one-click Cloud login to assume. Existing-object
   conflicts still require verified ownership and explicit exact selection.
3. **Start guided demo.** Explain once that this starts an owned staging Test
   and publishes/installs its demo software. Use existing Demo Control owners
   to prepare the environment and conduct the baseline scenario. Show named
   chapters and actual progress in Presenter, with manual exploration optional.

On a return visit, the default journey is **open AosEdge SDV Lab → Start demo**,
with a separate state-aware option for an existing run. Do not promise recovery
of every interrupted run or host sleep. Reconcile state before offering a
continuation and never silently replace a retained Test.

The target is three main decisions on first use and one start action thereafter,
not a claim of three literal clicks on an unconfigured Mac. Account verification,
terms, macOS permissions and secure credential entry cannot be wished away.
The current VM bootstrap password prompt is an additional obstacle: disclose
and collect it coherently in the first iteration if still required. Eliminating
it through per-installation bootstrap credentials needs a separately specified
security contract; do not embed a shared secret to achieve a click target.

Keep the scenario meaningful. Publish VDP/Brake versions serially, observe
installation and real function before advancing, apply VDP in Safe Stop and
preserve the separate moving QM SOTA path. Automation must not install every
latest release in advance and erase the software-evolution story. A fully
guided sequence is a proposal, not a current Presenter capability.

## Feedback and recovery

Show one current phase, the achieved result and the next required input. Use
messages such as Installing simulator or Waiting for the controller to confirm
the update. Put UUIDs, locks, image IDs and detailed logs behind Details. Show
determinate progress only when measurable; distinguish file installation,
environment readiness and demonstrated product results.

Resume an interrupted workflow by reading durable state, not by repeating
Cloud writes. Uncertain certificate issuance must retain its key and attempt;
publication uncertainty must be reconciled before another mutation. Only
surface the recovery controls when that condition actually exists. Do not
disable integrity checks, leases, access checks or Safe Stop to simplify screens.

Make closing/stopping the lab an explicit, understandable lifecycle path and
keep irreversible Finish separate. Do not leave owned heavy runtime processes
behind after a completed test. Changes to stop/retain/reopen behavior require
the existing lifecycle contract to remain authoritative.

## Proposed implementation boundary

Agree this complete journey, including packaging and exceptional inputs, before
coding. Then update the affected requirements, ADR and contracts together:
[ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md),
[native Setup](../../contracts/distribution-installation/native-setup.md) and
[Cloud first use](../../contracts/distribution-installation/cloud-first-use.md).
Their current explicit action boundaries must not be silently replaced by
automatic behavior. Keep Demo Control as the single lifecycle owner.

Implement the delivery wrapper, onboarding and guided handoff as one coherent
change. Reuse existing verified installation and runtime operations; do not
rebuild Factory or CARLA unless a proven required change affects them. Validate
with focused source tests before assembling one candidate and running the
native newcomer journey on M1.

Acceptance must demonstrate first and repeat launch from the delivered artifact,
operation after ejecting the DMG, no development-tree fallback, honest statuses,
bounded recovery and shutdown. Record operator decisions, permission prompts,
active interaction time and unattended wait time separately. An engineer using
scripts to make the scenario work is not evidence that this journey is usable.
The beginner guide should contain only this release's ordinary path; move
engineering history and exceptional repair details out of that path.

## Qualification execution order

The user requested script-first qualification on 2 October. Exercise the signed
Setup worker and installed lifecycle owners remotely, with explicit expected
results, bounded deadlines, per-phase timings and resumable evidence. After a
fix, repeat affected checks rather than the whole installation. Keep the final
native operator journey as a separate acceptance pass once functionality is
stable. This accelerates engineering qualification without treating scripts as
proof of a usable installation experience or weakening permissions and trust.
