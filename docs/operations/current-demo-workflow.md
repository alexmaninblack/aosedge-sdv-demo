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

1. Select the intended Cloud instance, OEM and one associated SP configuration for both independent services.
   Check access and first-use tenant prerequisites before publication. Prepared
   packages are unsigned; sign with the selected instance's current certificate.
   Neither an old signature nor a previous tenant's identity is reusable authority.
2. Use **Create Controller** to create an empty ARM64 virtual controller from
   the selected **Factory image**, its clean Linux/AosEdge base. This Test run
   has its own VM, Cloud identity and data; VDP and services are installed later.
   Any retained Production identity/backing image is outside the Test workflow.
3. Start or reuse CARLA and native Driving Control / Telemetry in detached mode.
   A not-yet-provisioned controller is not a usable Gateway destination.
4. Prepare and publish VDP V1, provision the selected Test and observe Cloud
   Online. Attach the existing Gateway to that same Unit using strict mTLS.
   Attachment starts stationary in Manual; it must not reload the CARLA scene
   or create a second simulator/control panel.
5. Use explicit Safe Stop to permit VDP application. Upload accepted by Cloud,
   pending update, installed release and confirmed profile are separate states.
   Wait for the exact version and verify its function before advancing.
6. Publish and assign Brake V1. Exercise the native brake maneuver and verify
   a vehicle-derived capture at its backend. Autopilot stopping at an obstacle
   is not, by itself, proof that a complete qualifying brake event was captured.
7. Progress through the selected scenario: VDP V2 then Brake V2; VDP V3 then
   Brake V3; Tire V1 requires VDP V3 inputs. Publish each next version only
   after the preceding version has installed and passed its check. Publishing
   all versions at once can cause the Unit to receive only the latest version.
8. Check products, native advisory, independent Reset Driver Advisory and
   renewed results; use the dedicated Brake and Tire physical maneuvers.
   Do not substitute telemetry or lower model thresholds to obtain a warning.

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
