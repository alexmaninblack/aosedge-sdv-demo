<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Install the demo and connect Cloud access

- Status: current user guide
- Version: 3.3
- Prepared: 2026-10-11
- Updated: 2026-10-15
- Owner: Demo Solution Team

Use the [launcher in README](../../README.md#install-and-run) to obtain and
open the complete DMG, then follow the steps below. No source checkout,
Unreal Editor or local compilation is required.

## Before opening Setup

Use Apple silicon with macOS 26 or later. Setup checks the space needed for
the complete payload plus a **90 GiB free-space reserve**. A compressed DMG's
size is not its installed footprint.

Install Docker Desktop separately and complete its first-run/license prompts.
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

## Install and select local data

1. Mount the complete DMG and open **AosEdge SDV Lab Setup**. Keep its matching
   Runtime Kit beside Setup in the mounted image.
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
- **New certificates:** choose **Get new certificates…**, select Production or
  Staging, follow the official registration/sign-in flow and enter the OEM
  and associated SP issuance tokens in the secure fields. Choose
  **Get certificates** to receive and connect the pair. Account registration
  and invitations use the official Cloud process; Setup does not register
  accounts or read your mailbox automatically.

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
Create Controller → simulator → VDP V1 publication and provisioning →
connection to the same Unit → Safe Stop FOTA → service evolution.
**Create Controller** uses the prepared Linux/AosEdge base (**Factory image**)
to create the ARM64 virtual controller. A **Test** is this demo run and its
associated Cloud identity, VM and data, not another simulator.

If Create requests VM access, enter the VM password in the secure
**VM access / Use once** dialog. Use a display configuration that fits
Presenter, CARLA and Driving Control. If a step stops, follow its message
and [troubleshooting](troubleshooting.md).

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
