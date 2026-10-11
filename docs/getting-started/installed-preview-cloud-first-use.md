<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Install the demo and connect Cloud access

- Status: current engineering-preview instructions; complete native acceptance open
- Version: 3.0
- Prepared: 2026-10-11
- Owner: Demo Solution Team
- Implementation: Kit028 / Setup042 / Factory .41

First [select the exact release and obtain access](release-status.md), then
use its complete approved DMG. The new source-Factory `1.2.0-rc.1` candidate
awaits fresh installation/live qualification; earlier Kit028 / Setup042 results
remain in the [qualification baseline](../qualification/current-baseline.md).
The integrated Setup source follows the [authorized scenario](../planning/active/work-packets/integrated-setup-scenario.md).
Its new candidate must pass the recorded native gates before release acceptance.
For older Setup042 media use its original guide rather than expecting the new UI.
No source checkout,
Unreal Editor or local compilation is required.

## Before opening Setup

Complete [README A1–A3](../../README.md#a1-check-the-mac) first: host checks,
Docker's separate first-run setup, exact private DMG acquisition, size/checksum
comparison and opening the verified file. No source clone is needed for this
route. Then follow the numbered actions below in order and wait for each result.
This revised walkthrough awaits joint execution; documentation review alone
does not close an installation or runtime qualification gate.

Use Apple silicon with macOS 26 or later. The recorded clean-host campaign
used an M1 with 16 GiB RAM and an internal disk; it does not establish a
universal performance minimum. Preflight checks a complete payload copy plus
a **90 GiB engineering free-space reserve**. Let Setup report the selected
kit's logical size; a compressed DMG's size is not its installed footprint.

Install Docker Desktop separately and complete its first-run/license prompts.
The local Linux/arm64 engine must be available through `desktop-linux`.
If it is already running, leave it running: opening/closing its dashboard is
not preparation, and restarting the engine is not a normal demo step.
Setup does not install, launch or stop Docker Engine.

Prepare access to the intended **Aos Cloud staging** instance: one OEM and
one associated SP, with Brake and Tire remaining separate services. No working
credentials, account sessions, provisioned VM or private run state are included
in the media. Production is outside this qualification route.

The application is locally Apple Development signed. It is not notarized or
approved for public distribution. Follow ordinary macOS security/consent;
do not disable Gatekeeper or grant broad disk permissions as a workaround.

## Install and select local data

1. Mount the complete DMG and open **AosEdge SDV Lab Setup**. Its fixed sibling
   Runtime Kit is the only source; Setup never searches for a substitute.
2. Choose **Install SDV Lab**. No kit, package-store or private-data questions
   are required. Defaults are `~/AosEdge SDV Packages` and `~/SDV-Lab-Data`.
   Advanced settings can change program storage, not silently move existing data.
3. Wait for the named checks, verified copy, local selection, backend-image
   preparation and signed launcher installation. Copy progress measures actual
   verified bytes; other phases show an indeterminate indicator. Missing Docker
   or insufficient space stops before copying and gives a specific next action.
4. Continue to **Connect to Aos Cloud**. Installed files and imported images
   are not a created vehicle, running backend or provisioned Unit.

Do not edit installed program files, add Python caches or use the private
runtime interpreter as a development environment. Version selection, runtime
leases and inventory checks protect the immutable package. A failed or
interrupted operation preserves existing data and evidence; it is not
permission to delete an unknown folder or lower verification requirements.

## Set up Cloud access

Choose **Connect to Aos Cloud…** after local preparation. Two routes exist:

- **Existing certificates:** select the intended OEM and associated SP PKCS#12
  files, then **Connect**. Setup authenticates both roles, their association and
  delivery permissions before storing references. It stores no copy of the working
  private keys. Files must satisfy the private ownership/permissions contract.
- **New certificates:** choose **Get new certificates…**, select Staging or
  Production, use the official registration/sign-in flow and enter the OEM and
  associated SP tokens in secure fields. Choose **Get certificates** to receive
  both and connect them. New enrollment uses the package-signing-compatible
  RSA path. Register accounts/obtain invitations through the official Cloud
  process; Setup is not an automatic account-registration or mailbox client.

For response loss, use **Details and enrollment recovery…** and the supported
**Inspect saved attempt** / recovery
path. An uncertain token submission is not replayed automatically. Keep tokens,
passwords and private keys out of screenshots, logs and reports. Never replace
working access merely to repeat a first-use test.

A successful Connect establishes the observed role/domain/association and
required permissions/prerequisites. Missing objects and an occupied Test set
are not authentication failures. Connect can explicitly prepare only the fixed
absent model and Test set through the existing owner. It never provisions a Unit,
publishes a package or deletes a conflicting object. Reopening checks are read-only.

For a retained Test missing SP access, keep the same OEM reference and select
the associated SP, then Connect. The bounded repair preserves the Unit, VDP,
journal, history and ledger; it cannot change the OEM or Cloud environment.

For diagnostic reference reuse, expand **Details and existing references…**,
inspect/save the pair through the low-level controls, then choose **Review existing
Brake / Tire assignments…**, **Read existing objects**, and the exact intended
reference. Do not pick by a similar display name. Missing objects are handled
by the ordinary explicit Demo Control preparation flow, not guessed or silently
created by the read-only selector.

## Open Presenter and create the Test

Authorize the signed Setup application for **Accessibility** when needed for
window placement/inspection. A removable-volume consent is a separate macOS
permission; it is not needed for the internal-disk campaign. Neither Full Disk
Access nor screen recording is a prerequisite for installation/placement.
An older app's permission entry may not authorize this executable.

Choose **Open SDV Lab**. It rechecks local installation/backend images and saved
Cloud access, then opens the selected instance's Presenter through the
existing Demo Control owner. It does not start Docker, create/power on a VM,
start CARLA, provision, publish, reset models or enable Autopilot. A successful
Open is Presenter availability, not full demo readiness.

Continue with the [current operator workflow](../operations/current-demo-workflow.md):
Create Controller → detached simulator → VDP V1 publication/provisioning →
same-Unit attachment → Safe Stop FOTA → serial service/profile evolution.
Use the ordinary secure **VM access / Use once** dialog when Create requests
the fresh VM's password. Do not embed that password in a configuration or guide.

The linked workflow is the next part of this operator route, not a requirement
to read the architecture or engineering history. Start with its numbered
sequence and keep each version's installation/check ahead of the next upload.
If a step stops, use [troubleshooting](troubleshooting.md).

Use a display configuration that fits all three windows. The M1 campaign
observed the correct Presenter/CARLA/Driving Control layout; this does not
qualify every display scale, monitor topology or lock/unlock transition.

## Returning, stopping and removing

Open **AosEdge SDV Lab** from your user Applications folder and choose
**Open SDV Lab**; the DMG/source kit is not needed. The installed selection and
saved access are revalidated, not inferred from a cached Ready indicator.
Do not repeat installation or reselect a version over a retained vehicle run.
Opening Presenter does **not** power on a stopped retained controller:
the current UI has no native Power on action. Engineering restoration observed
during qualification is not a completed returning-user workflow.

When a check ends, stop the demo-owned runtime through its normal owners and
close the windows. Verify no owned processes/listeners remain. Preserve Docker
Engine and unrelated processes. A stop preserves Test identity/state;
**Finish demo** is the distinct destructive retirement of the exact Test and
its run data. Package removal is not vehicle retirement or Cloud rollback.

In particular, **Close Presenter (keep demo running)** means exactly that:
closing its native window/menu is not a full runtime stop. A complete
non-destructive operator shutdown/return journey is not yet available as one
Setup action. For a retained Test, use the documented engineering owner with
the release maintainer rather than assuming the disappearance of windows
means storage is safe to eject.

For external storage, only disconnect after owned consumers are stopped and
the volume is safely ejected. External-SSD and host sleep/wake qualification
are not part of the current M1 internal-disk campaign.

## What is still being qualified

The [candidate record](../../workspace/checkpoints/installer-kit-028-candidate.json)
separates 98 passed installed scripted steps from open moving-SOTA, secure
native token entry, full native journey and interruption/repair gates.
The integrated candidate still requires its own native acceptance. It does not
close cold controller resume,
Developer ID/notarization or public-distribution work.

See the [native Setup contract](../../contracts/distribution-installation/native-setup.md)
for action boundaries and the [active plan](../planning/active/installable-distribution-and-reproducibility.md)
for outstanding work. Earlier Kit/Setup reports retain their original dates
and are not instructions to reinstall retired candidates.
