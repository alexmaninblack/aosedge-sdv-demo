<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Preview: Cloud First Use

- Status: Engineering preview instructions; not a clean-Mac release claim
- Version: 1.10
- Prepared: 2026-09-29
- Updated: 2026-10-01
- Owner: Demo Solution Team
- Installed evidence: Kit 015 / Setup 024 (seeded first-create and scoped serial functional checks passed)
- Successor evidence: Kit 020 / Setup 030 passes actual fresh-RSA publication, installed function, offline delivery, full power cycle and ordinary Finish. Kit 021 / Setup 031 contains the proved preprovisioning host correction and passes native installation, first/repeat Presenter launch and installed-code regression; remaining first-use and release limits are tracked in the latest receipt below.
- Evidence: [Implementation and qualification](../qualification/cloud-first-use-implementation-2026-09-29.md)

## Install the engineering preview

The [latest qualification receipt](../qualification/installer-first-use-2026-09-30.md)
distinguishes the retained installed Test from the independently installed successor. A
successful build is not installed acceptance. The first selection slice refuses
switching around a retained vehicle run; do not delete its journal or rebase its
VM to force a version change. Exact-Test Finish is a separate destructive action.
Installing a verified package for a separate empty private instance is supported
and does not require deleting that retained Test. Do not copy its journal,
credentials, VM or backend data into the new instance.

After Finish, a version change can still report an active native consumer when
Docker Desktop retains old context-directory handles. Do not erase metadata,
relax the usage check or restart shared Docker while unrelated containers are
running. Preserve the current selection and arrange an explicit maintenance
window for that shared-engine dependency. A separate empty instance is a
supported installation test, not proof that the original update succeeded.

This route uses prebuilt runtime files. It does not require compiling Unreal,
CARLA, the host applications or Factory on the operator's Mac. It currently
targets Apple silicon and macOS 26 or later; this is a tested engineering
target, not a finalized public minimum-hardware specification. Use the matching
Setup application and complete kit supplied by the project, not an arbitrary
folder or a development checkout. Developer ID/notarization and redistribution
approval are not yet closed: this guide is not authorization to bypass macOS
security or distribute the preview externally.

The selected external beta channel is a Developer ID Application-signed,
Apple-notarized DMG, not TestFlight. The current engineering preview is not that
release. A local Apple Development identity cannot replace Developer ID; the
account holder supplies the appropriate certificate/private-key access and
notarization access through Apple's supported process. Neither an installer
checksum nor an ordinary development signature means Apple has notarized it.

1. Open Setup. Select the **Complete offline kit** and **Package storage**.
   An existing supported external disk is allowed; do not create a missing
   mount path or substitute a same-named disk. The kit has approximately
   32.7 GiB logical payload. Preflight requires room for a full copy plus the
   current 90 GiB engineering reserve; do not assume APFS sharing saves space.
2. Choose a short **Private demo data** folder on the internal disk. Keep it
   separate from immutable program storage and any retained vehicle run.
3. Choose **Check installation**, then **Install package**. Preflight is not
   a full content verification; installation verifies the complete payload.
   Wait for the completed result. A stopped or interrupted operation is not
   success; retain its files for the ordinary guarded recovery path.
4. Choose **Prepare local data** explicitly. Installed and selected are not
   running or demo-ready states.
5. Open the separately installed Docker Desktop and wait for its local engine.
   In Setup 033 or later choose **Prepare backends**. It verifies and loads the
   packaged Brake/Tire images without a download or container start. Wait for
   **Backend images available — demo not started**, then continue to Cloud
   access below. Reopening Setup needs only the existing private-data folder;
   there is no need to reinstall the kit or re-enroll certificates.

Setup does not install/start Docker or create Cloud prerequisites during file
installation. Docker application presence alone is not an engine-readiness
check; Prepare backends observes images, while runtime checks remain in Demo
Control. Review macOS folder or
Accessibility requests when actually required. Full Disk Access and screen
recording are not installer prerequisites.

Install Docker Desktop in its standard Applications location and start its
engine before Create Controller. Installed backend commands locate that declared
application directly; changing a shell PATH is neither required nor a remedy.
An unavailable executable or engine blocks creation and remains visible in
Presenter progress/Trace even before the first vehicle journal exists.

Setup 031 did not import the packaged images into an empty engine; the first M1
Create stopped before making a VM. Setup 032 added the explicit action, but
misclassified successfully imported untagged images as missing. Setup 033 fixes
that observation and can reconcile the preserved attempt without loading again.
Kit 021 remains unchanged. Native repeats and Create have passed; an installed
controller-status defect and full E2E remain open. Use the
[M1 qualification receipt](../qualification/m1-installation-2026-10-01.md) for the
actual scope. Do not preload manually and report UI first use passed.

Use Docker Desktop's local `desktop-linux` context. A remote engine or changed
engine identity is refused. If an import becomes uncertain, keep its saved
attempt and partial images: another Prepare checks the same engine first and
does not repeat an unresolved load. Do not erase the attempt to force a retry.
The step changes no Cloud objects, credentials, tags or existing containers.

## Before connecting

Install the matching complete kit, then choose **Prepare local data** for a fresh
private instance on the internal disk. Package storage may use the explicitly
selected supported external disk. Do not select a retained vehicle run as a new
installation. The existing runtime, Factory and Cloud remain unchanged.

Choose **Set up Cloud access**. The demo uses one OEM and one associated Service
Provider for both Brake and Tire, with distinct service identities. Installation,
certificate receipt, Cloud access and demo readiness are different states.

## Existing certificates

Choose your two distinct owner-private, valid, unencrypted PKCS#12 files.
They must contain RSA keys compatible with the pinned official RS256 package
signer. Authentication-only EC credentials cannot sign this demo's packages.
Choose **Inspect locally**, **Use this pair**, then **Check Cloud access**.
The first action does not authenticate account roles. The final action reads
roles, association and prerequisites. Missing prerequisites are not created by
this check; continue through the existing Presenter Cloud-preparation workflow.
Never substitute developer files or change file permissions to hide a failure.

## New certificate

For an existing OEM or associated SP account, no new email, invitation or user
is required. Use the official Cloud profile's **Generate new token** action for
that same account, then enroll below. Authorized API clients can use the same
current-user token operation; Setup itself accepts the token and does not
register or invite another user. See the official
[existing-user certificate instructions](https://docs.aosedge.tech/docs/how-to/tutorials/user-and-certificates/issue-new-user-certificate).

Only if you do not yet have the required account, register and confirm it through
the official Aos Cloud portal or your Cloud administrator. Review the platform's
terms yourself. Obtain a token for the intended role; do not paste an email
command into Setup. Lost-certificate email recovery is a separate operation.

Choose **Need a new certificate? Enroll with a Cloud token**. Enter the exact
Cloud domain without a scheme/port, choose the role and **Inspect saved attempt**.
Enter the one-time token in the secure field and choose **Receive certificate**.
Setup saves the private key/CSR and attempt before sending one request. It never
retries that token automatically. On receipt, the corresponding file reference
is filled in the pair window. Repeat for the other role, then explicitly
inspect, save and check the pair.

The corrected enrollment path explicitly creates RSA keys. Earlier Kit 019
enrollment used the SDK's EC default; do not delete or overwrite those completed
attempts to retry. They remain valid authentication credentials but fail package
signing. Preserve them and use an explicitly selected authorized RSA pair, or
qualify fresh enrollment in a separate empty instance with the corrected kit.

If the result is uncertain, inspect the same role/domain again. Do not delete
the attempt/key or repeatedly submit. **Recover saved certificate** only completes
an already valid local result without a network request. Otherwise reconcile the
exact attempt with Cloud, obtain a replacement token through its official process,
and confirm the displayed attempt before submitting that replacement. A new
token alone is not reconciliation. Partial/unsafe local files need investigation;
Setup preserves them rather than silently replacing an identity.

## Existing Brake or Tire objects

After saving the pair, **Review existing Brake / Tire assignments** is optional.
Read the inventory, deliberately choose an eligible exact Subject and inspect
its Subject/service/OEM/SP/creator identifiers. Then choose **Use selected exact
reference**. Nothing is preselected and no Cloud object is bound or changed here.

Objects with desired or reported Unit recipients, ambiguous names, unexpected
services or incomplete ownership/read evidence are blocked. A parked/offline Test
still occupies its objects. Do not remove that Test simply to pass installation.

A saved reference is checked again at the first subsequent service assignment.
If there is no existing Subject, normal Demo Control assignment creates its own
under its usual safeguards. Saving a reference neither imports an old run nor
starts a vehicle.

## Continue to the demo

Close the Cloud window and choose **Open demo**. Presenter opening is not full
demo readiness. The existing Demo Control owns dependency checks, Cloud
preparation, Create Controller, provisioning, serial VDP/service progression,
driving and Finish. Do not batch-publish all versions: verify each installed
profile before the next; VDP updates still require Safe Stop.

For remote Mac qualification, use Screen Sharing's **Standard** connection to
the physical built-in display, not a high-performance virtual display. The
existing layout requires at least 1440 by 900 usable logical pixels after the
menu bar and Dock are excluded. On the tested M1, the default resolution was
too small; **More Space**, 1800 by 1169, passed. This is the measured test-host
configuration, not a new universal hardware-support claim. Grant the matching
signed Setup's ordinary Accessibility/System Events requests when needed for
window placement; do not add Full Disk Access or disable security controls.

On a later visit, choose the same private-data folder and **Open demo**; do not
reinstall or prepare a different instance merely to reopen it. If another
instance owns the demo ports, Setup preserves it and refuses to start a second
Presenter. An occupied Cloud Test is also a real conflict, not a reason to erase
the old run from disk. Use its normal guarded lifecycle before starting another
Test. Updates around a retained run, full native removal and clean-host behavior
remain separate unqualified gates; deleting the app is not Finish demo.

Existing-account token issuance and new OEM/SP role checks now have real staging
evidence, not only synthetic tests. New-account registration/email, remaining
OS/first-Create integration and clean-Mac acceptance are separate gates. See the
evidence document for the exact qualified boundary and remaining release gates.
