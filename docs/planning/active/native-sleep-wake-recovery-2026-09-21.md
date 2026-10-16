<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native simulation recovery after host sleep

- Date: 21 September 2026
- Status: Accepted planning item; automatic recovery is **not implemented or qualified**.
- Current scope: deferred accepted planning only. Historical one-session restoration
  authority is not a standing permission to change a live environment.

## Failure boundary

Host sleep can terminate the CARLA source session while the simulator and VM
remain alive, leaving stale RUNNING state. Recovery must reconcile actual
owners and fresh data, not interpret an old journal as a live source.
Controller ignition is a separate implemented behavior.

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

The [original failure and one-session recovery](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/cc75541f255f3d2fb0fd670053687ebe406c37ee/docs/planning/active/native-sleep-wake-recovery-2026-09-21.md)
remain in Git. The old PIDs, session identities and manual outcome do not qualify
automatic recovery or create a standing permission.
