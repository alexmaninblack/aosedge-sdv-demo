<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current SDV Lab operator workflow

Use Presenter and Driving Control to operate **AosEdge Platform - SDV Lab**.
The sequence below takes a new controller through platform and service updates.

For a new installation, begin with the [operator guide](../getting-started/installed-preview-cloud-first-use.md)
and [release selection](../getting-started/release-status.md).
The Cloud environment follows the selected credentials; connecting to Production
Aos Cloud does not mean promoting a Test into the separate Production vehicle role.

## Preparation and version sequence

First complete **Setup → Connect to Aos Cloud** with one OEM and its associated
SP, then **Open SDV Lab**. You do not need another Cloud setup in Presenter.
Use the **Vehicle**, **Platform**, **Brake** and **Tire** views and the **Next
step** guide; **Activity** shows the current operation and its result.

### First drive: Full story

Leave **Advanced preparation → Preparation → Full story** selected. This is
the default and exposes each lifecycle step. Complete one row before the next:

| Where | Action | Expected result / next step |
| --- | --- | --- |
| Vehicle | Keep the supplied Factory firmware and choose **Create controller**; confirm and supply VM access if requested | A new Test controller is created from the clean Linux/AosEdge base. It has no installed VDP/services. Wait for completion and **Start simulator**. |
| Vehicle → Next step | Choose **Start simulator** | CARLA and native Driving Control / Telemetry appear. They can run before Cloud provisioning, without a controller data connection. Do not open another simulator manually. |
| Platform | Select **v1**, choose **Prepare v1**, then **Sign & publish** and confirm the selected Cloud/release | Wait for the publication to become ready. Uploaded/processing is not yet ready or installed. The Vehicle guide then offers **Provision to Test**. |
| Vehicle → Next step | Choose **Provision to Test** and confirm; use **Continue registration** only if the same attempt needs continuation | Demo Control registers this Test, observes Cloud Online and connects the existing simulator in stationary Manual. If offered, **Connect in Manual** completes that connection. No manual certificate or Gateway configuration is needed. |
| Native Driving Control | Drive using the displayed controls if desired, then choose **Safe Stop** | VDP FOTA may apply while stopped. In Platform, use **Refresh Cloud state** until the exact release is installed and its V1 profile is confirmed. No separate Apply button is needed. |
| Brake | Select **v1**, choose **Prepare v1**, then **Sign & publish**; after publication is ready, choose **Assign to Test** | Wait for the exact service release to be running. First assignment is explicit; subsequent updates keep this assignment. |
| Driving Control, then Brake | Choose **BRAKE MANEUVER**, wait for completion, then choose **Open Brake backend** or open the Brake backend card | A vehicle-derived capture appears. A running container alone is not proof of a captured event; simply stopping behind an obstacle may not produce one. |

If an action reports **Incomplete** or **Needs attention**, read its reason and
the Next step/Activity result before continuing. A displayed **Continue
preparation** resumes the recorded unfinished work; it is not an instruction
to delete the Test or submit the same publication again. See
[troubleshooting](../getting-started/troubleshooting.md).

### Evolve the platform and services

Repeat the same view/profile controls in this order:

| Next profile | View and controls | Completion before advancing |
| --- | --- | --- |
| VDP V2 | Platform → **v2 → Prepare v2 → Sign & publish** | Use native **Safe Stop** and confirm the exact installed V2 release. |
| Brake V2 | Brake → **v2 → Prepare v2 → Sign & publish** | Confirm the running release, use **BRAKE MANEUVER**, then observe a condition-analysis result at the backend. |
| VDP V3 | Platform → **v3 → Prepare v3 → Sign & publish** | Use native **Safe Stop** and confirm the exact installed V3 release. |
| Brake V3 | Brake → **v3 → Prepare v3 → Sign & publish** | Confirm the running release, then observe its advisory/readiness in Driving Control and results at the backend. |
| Tire V1 | Tire → **v1 → Prepare v1 → Sign & publish**, then **Assign to Test** after publication is ready | With VDP V3 installed, confirm the running Tire release, use **TIRE MANEUVER** and observe condition/advisory data. |

Use **Refresh publication** for a submitted service still processing, and
**Refresh Cloud state** for installed software observations. Switch back to
**Platform** after service publication when checking the shared VDP prerequisite;
the service and its required platform profile are separate observations.
Publish each next version only after the preceding version has installed and
passed its functional check. Publishing all versions at once can cause the
Unit to receive only the latest version. Demo Control signs unsigned prepared
content with the selected OEM for VDP and SP for services; no separate signing
CLI or old signature is needed.

### Optional Quick preparation

Before creating a Test, **Advanced preparation → Preparation → Quick
preparation → Prepare demo** composes controller/simulator startup, VDP V1
preparation/publication and Test registration/connection. It does **not**
install all future profiles or services. Wait for its completed result, use
native **Safe Stop** to permit VDP V1 installation, then join the Brake V1 row
above. Do not also repeat Full story's VDP publication or provisioning.

For either mode, use the dedicated Brake and Tire physical maneuvers to obtain
real products and advisory observations. **Reset Driver Advisory** on a service's
backend card affects that service only and preserves history. Do not substitute
telemetry or lower model thresholds to force a warning. Any retained Production
identity/backing image is outside this Test workflow.

VDP is an OEM platform component delivered by FOTA and gated by Safe Stop.
Brake and Tire are independently delivered QM SOTA containers: their updates
do not require Safe Stop and may be installed while moving.
These condition/advisory services do not control braking or steering.

Functional profiles (V1/V2/V3) and allocated Cloud release numbers are different.
Demo Control allocates new release numbers automatically. Do not restore an
old release ledger to reuse an already published number.

## Read the UI by authority, not by appearance

| Display | What it establishes | What it does not establish |
| --- | --- | --- |
| Aos Cloud Unit, software and instance status | Cloud-reported identity, installed/pending release and runtime state | A successful analytic result or a driver-visible warning |
| Brake/Tire backend card and detail popup | Received function observations, products, history and freshness | Current in-vehicle operation while the backend is disconnected |
| Native Driver Advisory | Actual local delivery/readiness and advisory observation | That Cloud or the backend has already received the same result |
| Platform/profile compatibility | Presenter mapping of the exact Cloud installation to a known profile | Services discovering a VDP version from missing local input |

Backend health, input readiness, complete products, advisory publication and
Gateway application are distinct. Missing data is not proof of incompatible
VDP. Services validate their actual inputs locally and do not need Cloud to
continue authorized local operation. VDP V3 enables the advisory interface;
it does not alone guarantee a capable service, fresh input or a warning.

Brake V1 captures events; V2 adds condition analysis; V3 adds driver advisory.
Tire has one functional profile, V1, with condition analysis and advisory.
There is no Tire V3 requirement. Monitoring is not an instruction to generate
an inspection warning on every drive.

Reset Driver Advisory is on each service's main backend card. It sends a
command for that selected service, clears its model/advisory state when applied,
and retains prior result history and delivery records. Accepted/pending is not
applied. Offline expiry does not authorize delayed execution after reconnect.
The other service must remain unaffected; this is not a whole-demo reset.

## Cloud resources and freshness

The Aos Cloud popup separates software from resources. CPU and memory history
can be scoped to the controller or an exact Brake/Tire service instance.
CPU is DMIPS, not a percentage of host CPU. Memory and disk are bytes rendered
in readable binary units; disk rows are reported partitions, not necessarily
three physical disks. Inbound/outbound are byte accounting values, not an
inferred bit/s rate. Private backend traffic can be excluded by native traffic
accounting, so zero does not prove that no application traffic occurred.

The implemented Cloud path uses bounded REST reads and visible-panel refresh,
not a Cloud subscription. Backend SSE notifications are a different interface.
Missing, stale, ambiguous and unavailable samples must remain distinct from zero;
source timestamps are not replaced by the time the UI refreshed. Slow Cloud
reads must not block independent backend/control actions.

## Pause, offline operation and recovery

- For a normal pause, use Safe Stop and leave the controller running.
- Return to road places the car at a validated road location, stationary in
  Manual. It neither launches Autopilot nor resets service models.
- External network OFF tests loss of backend/Cloud delivery while the local
  Gateway–KUKSA–service chain continues. Verify unchanged backend receipts,
  new local products and queued messages; after ON verify their delivery and
  restored freshness separately from Unit Online.
- After controller ignition off/on, Presenter can restore the same provisioned
  Unit/Node attachment after a new boot, with external network ON, unchanged
  identities and no conflicting
  operation. It does not provision again or start Autopilot; it ends Safe Stop.
  It will not override an explicit blocked gate or blindly retry uncertainty.
- Stop the demo before putting the host Mac to sleep; host sleep/wake recovery
  is not automatic. Keep the external network ON for controller restart.
  Do not substitute a raw VM stop or forced power loss for an operator pause.

## Stop or delete the Test

**Delete Test & start over** requires confirmation of the exact current Test.
It retires its Cloud identity, working VM and run-scoped backend data;
uncertainty must be reconciled
before retry or deletion. It preserves Production, Factory images, published
releases and release-number continuity.

For a non-destructive session stop, choose **Demo controls → Runtime → Stop demo
and keep data**. Opening Presenter later does not automatically power on the
stopped Test: choose **Start controller**, then follow simulator/connection
readiness. Do not use Create or reprovision merely to resume the retained Test.

At the end of a session, use the normal stop action and close the windows.
Keep Docker Engine and unrelated workloads running. Stopping preserves data;
deleting the Test does not.
