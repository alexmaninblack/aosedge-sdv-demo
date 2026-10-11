<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Integrated SDV Lab Setup plan

- Status: Implemented; native existing-access and scripted vehicle journey passed; new-access gates open
- Date: 2026-10-11
- Parent: [Installable distribution plan](../installable-distribution-and-reproducibility.md)
- Scope: Complete DMG, first installation, Cloud onboarding and repeat launch

Setup should guide an operator from one complete DMG to an installed lab with
verified OEM and SP access. Payload paths, package-store selection, instance
preparation, certificate inspection and backend-image import are internal
steps, not separate ordinary user decisions. Existing transaction, integrity,
permission and lifecycle owners remain authoritative.

## Baseline before this work

The [native application](../../../../scripts/distribution/native/Setup.swift)
already detects the fixed sibling Runtime Kit but still exposes three paths
and six peer actions. Backend, Cloud and launch buttons can be enabled by a
nonempty instance field before that instance is actually prepared. The Cloud
dialog requires separate Inspect, Use and Check actions and exposes exceptional
enrollment recovery alongside normal setup.

The installation worker already checks platform, storage and package identity,
copies verified files and prepares/selects the instance. The backend helper
already verifies/imports the two exact images. Cloud workers already support
certificate-domain inspection, authenticated OEM/SP role and association checks,
one-shot RSA enrollment from a token and uncertain-response recovery. Demo
Control can check and explicitly prepare the fixed model and Test-set objects;
native Setup currently exposes the check but not their preparation.

Open demo currently opens Presenter only. It neither creates a controller nor
starts CARLA. Repeat use requires the operator to remember a private-data path.
The [missing-SP defect](../../../qualification/sp-configuration-after-create-2026-10-11.md)
allows OEM-only progress to a provisioned Test but prevents the first-use pair
selector from configuring SP access afterward. These are operator-flow gaps,
not reasons to rebuild Factory or CARLA.

## Ordinary user journey

### Install SDV Lab

Open Setup from the complete DMG. Authenticate only its fixed sibling payload;
never search for another kit. A missing/mismatched payload produces a specific
media error rather than a normal folder-selection question.

Automatically check Apple silicon, supported macOS, available storage, write
access and Docker installation/engine/platform. Report the required and free
space before copying. A default installation needs no location question.
Advanced settings may offer one bulk-program location; keep private instance
data on the supported internal disk. Preserve program/state separation without
showing it as two choices. For the first increment, reuse existing validated
roots internally; any new layout must first satisfy ownership, overlap and
Unix-socket length constraints. Never relocate an existing instance silently.

If Docker is missing, show its official installation instructions and an
explicit recheck. If present but stopped, explain that the engine must be
started. Reuse an already running Engine without opening Dashboard, restarting
it, changing its storage or accepting its license. Docker is not in the DMG.

One Install action runs the existing check, copy, local preparation and backend
image preparation in order. Show named phases with real copy progress and
honest waiting states. Persist enough existing receipts to resume after an
interruption without another full copy or uncertain import replay.

### Connect to Aos Cloud

Offer two normal routes: **Use existing certificates** and **Set up new Cloud
access**. Keep exceptional recovery and diagnostic codes under Details.

For existing access, select one OEM and one associated SP file. Derive the
domain from each certificate's Organization attribute; reject mismatch and
unsupported signing keys. Display the actual environment and domain without
asking the operator to choose staging or production again. One Connect action
performs local inspection, explicit reference save and authenticated checks.
Do not infer roles/association from certificate filenames or domain alone.

For new access, ask first for **Staging** or **Production**, using a reviewed
endpoint mapping, then only the account fields required by that instance's
official registration flow. Guide both OEM and SP as one task, not two unrelated
technical dialogs. Generate private keys locally, enroll with the supported
Cloud issuance mechanism, verify the returned domain and use the same pair
validation as existing access. Existing-account certificate renewal and
first-account registration are distinct cases; do not recreate organizations
when the user only needs certificates.

Registration integration is a feasibility gate, not a promised implementation.
The official [account procedure](https://docs.aosedge.tech/docs/how-to/register-your-users/create-first-account)
uses signup and two welcome emails. The public
[v11 schema](https://api.aoscloud.io/api/v11/openapi.json), read on 11 October,
includes tenant registration for a signed-up user and authenticated token
issuance. Separate SP organization creation requires Admin authority. These
definitions do not establish a complete anonymous signup flow on staging or
production. Verify the actual bootstrap authentication, email confirmation,
terms, account association and permission requirements for each target before
choosing native forms or an official browser-authentication return flow.

Prefer supported API operations inside Setup. Where Cloud requires an official
login, verification or terms page, use that explicit flow and return to Setup;
do not embed administrator credentials or promise zero human intervention.
If email tokens remain necessary, collect them securely in Setup, never ask
the user to run email commands. Preserve uncertain issuance and reconcile it
instead of requesting another certificate automatically.

Connect may explicitly prepare only the agreed absent demo model and Test-set
objects through the existing owner, following an understandable summary and
the operator's Connect intent. Do not create a Unit, publish packages, alter
permissions, resolve foreign conflicts by deletion or adopt Subjects by name.
Conflicts must name the problem and offer the bounded authorized resolution.

### Open the installed lab

Install a persistent, consistently signed launcher at
`~/Applications/AosEdge SDV Lab.app` so later use does not need the DMG. The
launcher uses the default private instance `~/SDV-Lab-Data`; an advanced
location is an advisory preference and must pass the same installed-selection
checks. Neither the preference nor the launcher is runtime readiness authority.
The runtime must work after media ejection and without a development checkout.

The default path reaches **Ready to open** only after local installation,
backend images and complete OEM/SP access are independently confirmed. Offer
**Open SDV Lab**, explicitly meaning Presenter, not a running simulated vehicle.
Create Controller and the serial release demonstration remain in Presenter;
do not preinstall latest versions and erase the evolution story. If local-only
exploration is offered, label its missing Cloud capabilities clearly and block
the full delivery flow until access is configured.

Reopening discovers only the validated installed selection and offers Open or
the next incomplete setup phase. Preserve retained runs. Define a same-domain,
same-OEM missing-SP repair through the existing writer with authenticated
association checks; an environment/owner switch must not repoint a provisioned
Test. The first-use guard must not simply be removed. Returning stopped
controllers still require a defined native power-on path; opening Presenter
alone is not cold-resume acceptance.

## Delivery sequence

1. **Freeze the complete contract packet.** Define screen states, default and
   advanced storage, persistent launcher, registration feasibility, Cloud
   environment selection, missing-SP repair and continuation/stop behavior.
   Amend ADR 0018, native Setup and first-use contracts and the operator guide
   together. Keep one OEM and one associated SP for both independent services.
2. **Implement automatic local setup.** Reuse the current engines beneath one
   ordinary action; remove redundant fields/buttons and expose only actionable
   prerequisite failures. Add state-based continuation and accurate progress.
3. **Implement complete Cloud onboarding.** Unify pair validation/save/check,
   agreed prerequisite preparation and retained-Test repair. Add registration
   only after the feasibility gate; do not claim the token-enrollment path is
   complete new-account onboarding.
4. **Implement persistent launch and recovery.** Open the correct installed
   instance after DMG ejection, resume incomplete setup and preserve stopped or
   active runs. Provide clear non-destructive stop versus destructive Finish.
5. **Qualify and deliver one candidate.** Run focused automated worker/owner
   tests first, assemble one signed matching DMG using retained heavy inputs,
   then execute the native newcomer journey on M1. Update instructions to the
   actual UI and publish source separately from release acceptance.

Execute the agreed packet without routine micro-approval checkpoints. Stop
only at an actual design, authentication, OS-consent or external-authority
boundary. All live implementation qualification remains staging-only; production
support must not authorize testing against existing production resources.

## Completion criteria

- First install needs no kit, package-store or private-data path question in
  the default route and no source clone or compilation.
- Missing/stopped/wrong Docker, insufficient space and invalid media each
  produce one clear explanation and a supported next action.
- Both existing certificates and the agreed new-access route complete without
  terminal commands; incompatible domains, roles and associations are rejected.
- A missing SP can be repaired on the same provisioned Test without deleting
  its Unit, VDP, journal, history or release ledger; wrong authority is blocked.
- Reopen, interruption, repeat actions and media ejection preserve selection
  and do not replay uncertain Cloud writes, enrollment or image imports.
- Native first use and returning use pass on M1 without engineering repair.
  Scripted PASS is not native UI acceptance. Record operator inputs and prompts
  separately from unattended waiting time.
- No key/token/password disclosure, silent production mutation, destructive
  replacement or unneeded Docker restart occurs. Normal demo shutdown verifies
  owned consumers stopped while preserving shared Docker Engine and run data.

The [complete user scenario](integrated-setup-scenario.md) specifies the screens,
continuation rules and acceptance cases. Signing/notarization and the previously
open runtime gates remain separate from Setup usability acceptance.

Implementation tests, candidate identity and separately observed native outcomes
are recorded in the [11 October qualification record](../../../qualification/integrated-setup-2026-10-11.md).
