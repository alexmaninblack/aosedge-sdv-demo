<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Install the demo and connect Cloud access

- Status: current engineering-preview instructions; complete native acceptance open
- Version: 2.2
- Prepared: 2026-10-09
- Owner: Demo Solution Team
- Implementation: Kit028 / Setup042 / Factory .41

First [select the exact release and obtain access](release-status.md), then
use its complete approved DMG. The new source-Factory `1.2.0-rc.1` candidate
awaits fresh installation/live qualification; earlier Kit028 / Setup042 results
remain in the [qualification baseline](../qualification/current-baseline.md).
This guide describes the implemented Setup actions, not the proposed simplified
wizard or a claim of native acceptance for new media. No source checkout,
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

1. Mount the DMG and open **AosEdge SDV Lab Setup**. The matching sibling
   **Runtime Kit** is discovered automatically; if absent, select the exact
   matching kit explicitly. Do not combine a Setup with another kit.
2. Choose package storage and a separate private-data folder. For the M1
   campaign both are on the internal disk. Keep the private instance path short
   enough for local Unix sockets. A foreign nonempty folder is not adopted.
3. Choose **Check installation**. This checks platform, pins, inventory,
   storage/volume and destinations. It is not complete payload verification.
4. Choose **Install package**. Setup copies/verifies the immutable version and
   records `INSTALLED_NOT_ACTIVATED`; this does not mean a vehicle is running.
5. Choose **Prepare local data**. Setup creates or validates the private
   instance and selects the verified version: `SELECTED_NOT_STARTED`.
   It does not create a vehicle journal, provision or replace a retained run.
6. Choose **Prepare backends**. It verifies the pinned archive and exact images
   in the existing Docker engine, importing once if necessary. Success means
   images available, not running backend containers. Uncertain imports require
   reconciliation; do not repeat them blindly.

Do not edit installed program files, add Python caches or use the private
runtime interpreter as a development environment. Version selection, runtime
leases and inventory checks protect the immutable package. A failed or
interrupted operation preserves existing data and evidence; it is not
permission to delete an unknown folder or lower verification requirements.

## Set up Cloud access

Choose **Set up Cloud access…** after local preparation. Two routes exist:

- **Existing certificates:** select the intended OEM and associated SP PKCS#12
  files, then **1. Inspect locally**, **2. Use this pair**, and
  **3. Check Cloud access**. Setup stores references, not a copy of the working
  private keys. Files must satisfy the private ownership/permissions contract.
- **New certificate:** choose **Need a new certificate? Enroll with a Cloud
  token…**, select the role and submit its one-time token through
  **Receive certificate**. New enrollment uses the package-signing-compatible
  RSA path. Register accounts/obtain invitations through the official Cloud
  process; Setup is not an automatic account-registration or mailbox client.

For response loss, use **Inspect saved attempt** and the supported recovery
path. An uncertain token submission is not replayed automatically. Keep tokens,
passwords and private keys out of screenshots, logs and reports. Never replace
working access merely to repeat a first-use test.

A successful Cloud check establishes the observed role/domain/association and
required permissions/prerequisites. Missing objects and an occupied Test set
are not authentication failures. The read-only check does not create them,
provision a Unit or publish a package.

When reusing existing unbound Brake/Tire objects, choose **Review existing
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

Choose **Open demo**. It opens the selected instance's Presenter through the
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

Reopen the matching Setup, choose the existing private-data folder and
**Open demo**; the original source kit is not needed for that action.
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
The newer complete DMG does not close the simplified-wizard, returning-user,
Developer ID/notarization or public-distribution work.

See the [native Setup contract](../../contracts/distribution-installation/native-setup.md)
for action boundaries and the [active plan](../planning/active/installable-distribution-and-reproducibility.md)
for outstanding work. Earlier Kit/Setup reports retain their original dates
and are not instructions to reinstall retired candidates.
