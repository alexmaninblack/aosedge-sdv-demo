<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native simulation recovery after host sleep

- Date: 21 September 2026
- Status: Accepted planning item; automatic recovery is **not implemented or qualified**.
- Immediate authorization: restore the current local simulation and Driving Control;
  preserve the Test VM, Cloud identity, installed releases and service data. Then
  return to the separately maintained private video project.

## Observed failure

The Mac entered clamshell sleep at 05:29:03 UTC. At 05:39:04.980 UTC the
controller reported `std::exception` at its CARLA `world.tick` call. Its cleanup
destroyed the vehicle and sensors. The runner then closed Driving Control at
05:39:06.123 UTC. Unreal and the Test VM remained running. The source journal's
older RUNNING value did not represent a live controller. This is an actual
process/session failure, not merely a hidden window. The precise lower-level
CARLA exception is not available; the timing correlates with host sleep/wake.

## Accepted direction

1. Keep Driving Control visible through a transient disconnect. Show
   `Reconnecting…`, invalidate stale live values, and clear held keys and old
   queued commands. Do not display old telemetry as fresh.
2. Keep democtl as the recovery owner. Reuse healthy local processes. If the
   source session has ended, recover only the local CARLA/controller/Gateway
   session with a new, truthful source identity/generation. Do not replay an old
   source connection or create a competing orchestrator.
3. Preserve Test VM/Cloud identity, installed releases, model storage and backend
   history. This plan does not require AosCore/CM/SM/Cloud changes, a Factory
   rebuild, a VM reboot or re-provisioning.
4. Declare readiness only after fresh, advancing, correctly assigned telemetry.
   Recovery ends stationary in Manual; Autopilot remains an explicit operator
   action. Waking the host does not grant the Safe Stop component-update gate.
5. Interrupt unfinished maneuvers/windows across a source gap. Never join
   pre-sleep and post-wake samples into a fabricated valid measurement. Preserve
   historical results and distinguish them from current observations.
6. Bound automatic attempts. On failure keep the panel available with an honest
   error and an explicit `Restore simulation` action. Do not restart indefinitely.
7. Preserve the external-network toggle, including OFF. Local recovery must not
   depend on a Cloud response. Restore the established layout and z-order without
   stealing control continuously.

This is host sleep/wake tolerance, **not** restoration of the removed VM
Park/Resume operator workflow. It is a scoped future amendment to
[ADR 0017](../../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md).
Until it is implemented and qualified, normal sleep recovery is an explicit
engineering operation, not a supported automatic behavior.

## Implementation and qualification order

1. Specify the existing runner/panel/source lifecycle failure boundaries and
   reconcile stale RUNNING state without bypassing ownership or guest gates.
2. Implement panel survival and bounded local recovery; preserve commands,
   source generation, authentication and one-writer invariants.
3. Test short and long sleep in Manual and Autopilot; also sleep during Brake
   and Tire maneuvers and with External Network OFF.
4. Verify unchanged Test identity, VM lifetime, installed versions/model data,
   no duplicate processes/commands, no spontaneous motion, no false advisory or
   fresh-data claim, and correct window layout/z-order.
5. Only then mark the feature implemented and run the existing continuous-demo
   regression. Do not claim that the one-off recovery qualifies this feature.

## Immediate recovery completed — 21 September, 06:46 UTC

The normal `simulation stop --target test` reconciled the absent controller;
it honestly reported physical stop NOT_OBSERVED. `simulation start --target test`
created a new source run, then `vehicle initialize test` attached the preserved
Test in stationary Manual using its existing mTLS identities.

- New source run: `4ae4afe0-3313-47df-a099-610298b3ec92`, assignment generation 22.
- Test VM process remained PID 25577; its local identity and Cloud Unit were
  unchanged. No provisioning, release publication, model Reset or VM restart.
- Guest reported `VDP data READY; source LIVE; reason NONE`, active VDP and
  zero VDP restarts; the Gateway admitted the selected Unit through mTLS.
- The native panel was visually checked: Test LIVE, Manual, STOPPED, 0.0 km/h,
  Brake 100%, Brake/Tire Monitoring. CARLA visibly showed the vehicle on the road.
- External Network remained ON, confirmed by the existing connectivity status
  command. This is packet-filter evidence, not a claim about Cloud status.
- Existing workspace restoration reported expected window bounds and VERIFIED
  z-order. No automatic sleep/wake logic was changed or qualified.

The operator may explicitly select Manual or Autopilot to continue. Historical
recordings and service data were not reset or deleted during this recovery.
