<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Install the demo and connect Cloud access

- Status: current user guide
- Version: 3.4
- Prepared: 2026-10-11
- Updated: 2026-10-18
- Owner: Demo Solution Team

Use the [launcher in README](../../README.md#install-and-run) to obtain and
open the complete DMG, then follow the steps below. If you have just built
your own DMG with route B, use [install your build](reproduce-demo.md#install-your-build)
instead of downloading route A's package, then join at **Install and select
local data** below. No source checkout, Unreal Editor or local compilation
is required for installation.

## Before opening Setup

Use Apple silicon with macOS 26 or later. Setup checks the space needed for
the complete payload plus a **90 GiB free-space reserve**. A compressed DMG's
size is not its installed footprint.

For planning, a 16 GiB Apple Silicon Mac is the ordinary-demo reference
configuration, not a certified universal memory minimum. Allow memory for
CARLA, the controller VM, Docker and macOS together; close unrelated heavy
workloads. This does not describe full-source builds. Keep space for the
downloaded DMG **as well as** the installed payload, growing VM/backend data
and the reserve. Setup reports the selected payload's logical size before
copying; do not treat 90 GiB free by itself as enough. Internet is needed for
the initial download, Cloud connection and software publication.

Install [Docker Desktop for Apple Silicon](https://docs.docker.com/desktop/setup/install/mac-install/)
separately and complete its first-run/license prompts.
The local Linux/arm64 engine must be available through `desktop-linux`.
If it is already running, leave it running: you do not need to open its dashboard
or restart it. Setup does not install, launch or stop Docker Engine.

Prepare access to the intended **Aos Cloud environment**: one vehicle
manufacturer (**OEM**) and one associated **Service Provider (SP)**, used for
the separate Brake and Tire services. Setup supports **Production**
(`aoscloud.io`) and **Staging** (`aws-stage.epmp-aos.projects.epam.com`).
Existing certificates determine the environment; for new certificates, select
it before requesting issuance. Credentials are not included in the DMG.
See [release and access information](release-status.md).

The application is Apple Development signed, not notarized. Follow normal
macOS security prompts; do not disable Gatekeeper or grant broad disk
permissions to bypass a refusal.

<a id="file-locations"></a>

## File locations

In A, **Existing download workspace parent folder** means an existing APFS
folder for retaining the DMG. Press Return to use the shown home-folder default,
or enter an existing absolute folder on your internal/external disk without
shell quotes. This choice does not relocate the installed program or Docker.

| Files | Default / selected location | Purpose |
| --- | --- | --- |
| Downloaded DMG | `<download-parent>/sdv/cache/` | Verified reusable installation media; this is not a source build or the running demo. |
| Installed programs | `~/AosEdge SDV Packages` | Versioned program payload selected by Setup. |
| Private demo data | `~/SDV-Lab-Data` | Controller disk, run state and local data retained across normal Stop/Start. |

Setup confirms its program/data paths separately. The small launcher selections
live in your Library Application Support, not inside the installed program.
For an interrupted download, follow
[download recovery](unified-macos-launcher.md#operator-download-recovery), not
Test deletion or a new Cloud registration.

## Install and select local data

1. If the launcher already opened **AosEdge SDV Lab Setup**, continue there.
   Otherwise mount the complete DMG and open Setup. Keep its matching
   Runtime Kit beside it in the mounted image; do not launch a second copy.
2. Choose **Install SDV Lab**. Defaults are `~/AosEdge SDV Packages` for
   programs and `~/SDV-Lab-Data` for private demo data. No separate kit or
   package-store selection is required. Advanced settings can change program
   storage; they do not move existing data.
3. Wait for the checks, verified copy, backend-image preparation and launcher
   installation. Missing Docker or insufficient space stops before copying
   and gives a next action.
4. Continue to **Connect to Aos Cloud**.

Installed programs and imported images do not yet create a controller or a
Cloud Unit. Do not modify installed program files or use their private Python
interpreter for development. If an operation fails, keep its message and
existing data and use [troubleshooting](troubleshooting.md).

## Set up Cloud access

Choose **Connect to Aos Cloud…** after installation:

- **Existing certificates:** select the OEM and its associated SP PKCS#12
  files, then choose **Connect**. Setup checks both roles, their association
  and delivery permissions. It saves file references, not copies of your
  existing private keys. Keep those files in an owner-only private location.
  If access permissions need correction, use Finder **Get Info → Sharing &
  Permissions** on those specific files: your user may read/write; other
  users/groups must have no access. Do not change permissions on your whole
  home folder or share the files to resolve this error.
  Both must be valid, distinct, unencrypted `.p12` files with their private
  keys, RSA package-signing capability and the same Cloud environment.
  Password-protected files and authentication-only EC keys are not supported
  by this package-signing path. Do not upload keys to an online converter or
  replace working credentials just to pass a check; obtain a suitable pair
  through the Cloud account owner or the new-certificate path below.
- **New certificates:** choose **Get new certificates…**, select Production or
  Staging, follow the official registration/sign-in flow and enter the OEM
  and associated SP issuance tokens in the secure fields. Choose
  **Get certificates** to receive and connect the pair. Account registration
  and invitations use the official Cloud process; Setup does not register
  accounts or read your mailbox automatically.

<a id="new-cloud-access"></a>

### If you have no Aos Cloud accounts or certificates

1. Choose the intended environment in Setup. Open its official portal:
   [Production](https://aoscloud.io/) or
   [Staging](https://aws-stage.epmp-aos.projects.epam.com/).
   Use **Sign Up** and complete the registration and any email confirmation.
   Use your own accessible email; you do not need the demo publisher's account.
2. The standard first-account flow provides **two welcome emails**, one for
   OEM and one for its SP. Keep them as a pair for the same registration and
   environment; Brake and Tire share this one SP. For an existing company's
   account, ask its Aos Cloud administrator for invitations for both associated
   roles rather than creating an unrelated SP.
3. Each welcome/invitation message contains a certificate-generation command
   with a role-specific user token, the value after `-t` / `--token`. Copy
   **only that token** into the matching **OEM issuance token** or
   **Service Provider issuance token** field in Setup. Do not run the email's
   CLI command as well: Setup performs issuance and creates the local keys.
4. Choose **Get certificates** once. After both roles and their association
   are confirmed, Setup connects the pair. If only one role is complete or
   the outcome is uncertain, keep the saved attempt and use recovery below;
   do not request or submit another pair blindly.

The upstream [first-account walkthrough](https://docs.aosedge.tech/docs/how-to/register-your-users/create-first-account)
and [access guide](https://docs.aosedge.tech/docs/quick-start/get-access/)
explain registration and the two role emails. Their CLI installation steps
are replaced by Setup here. A user token is not your email password, an Apple
signing identity or a reusable API key. If an email/token is missing, expired
or already used, resolve it with that environment's account administrator;
do not borrow another person's credentials. Setup can issue certificates,
but cannot approve your registration or grant account permissions.

If the response to a certificate request is lost, open
**Details and enrollment recovery… → Inspect saved attempt**. Do not submit
the same one-time token again without inspecting the saved attempt. Keep
tokens, passwords and private keys out of screenshots and logs.

Connect checks access and prerequisites. Missing Cloud objects and an occupied
Test are different from authentication failure. Connect can prepare the fixed
missing model and Test set, but does not provision a Unit, publish software
or delete conflicting objects. Reopening performs read-only access checks.

If a retained Test lacks SP access, keep its OEM selection, choose the
associated SP and Connect. This preserves the Test, its controller and data;
it does not switch the Test to another OEM or Cloud environment.

Use **Details and existing references…** only when you need to inspect or
reuse existing Cloud objects. Under **Review existing Brake / Tire
assignments…**, read the objects and choose the exact intended reference,
not just a similar display name.

<a id="open-presenter-and-create-the-test"></a>

## Open Presenter and create the virtual controller

Allow **Accessibility** for the signed Setup application when requested for
window placement. Using removable storage may require separate volume access;
an internal-disk installation does not need that permission. Installation and
window placement do not require Full Disk Access or screen recording.

Choose **Open SDV Lab**. It checks the installed files, backend images and saved
Cloud access, then opens **Presenter**, the operator interface. This does not
start Docker, create or power on a controller, start CARLA or publish software.

Continue with the [operator workflow](../operations/current-demo-workflow.md):
Create controller → simulator → VDP V1 publication and provisioning →
connection to the same Unit → Safe Stop FOTA → service evolution.
**Create controller** uses the prepared Linux/AosEdge base (**Factory image**)
to create the ARM64 virtual controller. A **Test** is this demo run and its
associated Cloud identity, VM and data, not another simulator.

If Create requests **Demo Control — VM access**, use the current development
Factory image's public test password, `Password1` (capital P), in the secure
dialog and choose **Use once**, or **Save in Keychain** to remember it locally.
This is the VM's development login, **not your Mac, Apple or Aos Cloud password**.
It is already part of this project's development-image helper, not a personal
credential. It is not suitable for a real vehicle or an exposed SSH endpoint.
If you deliberately selected a different/custom image, use the password set
by its image owner; this default is not a recovery method for another image.
Do not pass passwords on a command line or place personal passwords in reports.
Use a display configuration that fits
Presenter, CARLA and Driving Control. If a step stops, follow its message
and [troubleshooting](troubleshooting.md).

Keep **Full story**, the default preparation mode, for the step-by-step
demonstration. **Advanced preparation → Quick preparation** also publishes
VDP V1 and registers the Test, but does not install future profiles. Follow
the displayed **Next step**, rather than repeating those completed actions.
The [operator workflow](../operations/current-demo-workflow.md#preparation-and-version-sequence)
lists the actual controls and expected results.

## Returning, stopping and removing

Open **AosEdge SDV Lab** from your user Applications folder and choose
**Open SDV Lab**. The DMG is no longer needed. Do not reinstall over a retained
Test just to resume it.

Opening Presenter does not power on a stopped controller. In
**Demo controls → Runtime**, choose **Start controller**, then follow the
simulator and connection prompts. This resumes the existing Test without
creating or provisioning it again; Autopilot stays off.

Use **Demo controls → Runtime → Stop demo and keep data** to stop the
simulator, controller and backends while preserving the Test. Leave Docker
Engine and unrelated workloads running. **Close Presenter (keep demo running)**
closes only its window, not the demo.

**Delete Test & start over** is a separate destructive action: it removes the
selected Test's Cloud identity, working VM and run data. Removing a program
package is not the same as deleting its Test.

If using external storage, stop all consumers and safely eject the volume
before disconnecting it. Stop the demo before putting the host Mac to sleep;
do not rely on automatic host sleep/wake recovery.
