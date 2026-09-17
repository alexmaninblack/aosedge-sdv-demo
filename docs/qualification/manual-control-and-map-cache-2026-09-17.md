<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Manual first-command handling and first-drive cache preparation

Date: 17 September 2026. Scope: preserved staging Test, native simulator and
control only. No Factory/VM/service/Cloud changes or new releases.

## Observed failure

During the operator drive on run `f5e1bca5-3d16-4ae5-852c-ad9810b38df4`:

- At 13:21:20.913 UTC Manual was selected. At 13:21:20.929 the controller
  reported `command_timeout`, although its configured budget is 250 ms.
- At 13:22:33–41 Unreal built 4K textures for the scene. Its own log reported
  a 7.75-second tick delay; the normal 30-frame log interval stretched from
  about 1.5 seconds to 9.579 seconds. Native telemetry went STALE at
  13:22:39.444 and LIVE at 13:22:41.945.
- Control disconnects, ownership timeouts and rejected messages remained zero.
  The logs do not independently prove a blocked AppKit event loop.

## Correction

Manual selection holds full brake and starts the existing first-command
deadline at selection. No immediate timeout is inferred from the absence of
that first command. The bridge preserves selected Manual during the bounded
`awaiting_command` state; true timeout, operator stop and orchestration hold
still take priority. Explicit Manual selection after a timeout re-arms the
wait without replaying previous pedals. Established-command expiry remains
250 ms; heartbeats cannot extend it.

`democtl simulation prepare-cache` runs the native map-scoped Unreal DDC
commandlet with a resolved map filename. It refuses a running simulator,
preserves caches/project assets/graphics settings, checks disk capacity and
checks that the requested map was actually processed. It is explicit setup,
not a new build on every start. Native fatal errors/timeouts fail the command.

The initial commandlet proof exposed two invocation issues: disabling shader
compilation prevents creation of required default materials, and this engine's
`-Map` argument requires a filesystem filename, not the launcher's `/Game`
identifier. Both were corrected; failed/interrupted preparation is not
acceptance. Retained operation logs are under `.local/simulator-cache/`.

## Verification so far

- Control protocol: 30 tests passed, including first-command hold/deadline,
  actual expiry, explicit recovery and existing session safeguards.
- Bridge: 6 tests passed, including socket input/heartbeat/Safe Stop with no
  simulation ticks for over a second, and existing rejection recovery.
- Orchestration: 19 tests passed; native status semantics: 3 passed.
- Solution simulation lifecycle: 37 passed; source: 18 passed;
  map-cache adapter: 4 passed, including native failure and missing map.
- Live `democtl simulation stop --target test` confirmed physical stop and
  completed. Test VM and all installed releases were retained.

Cache completion and a restarted native driving check are recorded below
when observed. No hitch-free rendering or live-first-drive success is claimed
from unit tests alone.

## Native cache result and retained-Test restart

`simulation prepare-cache` completed at 14:31 UTC in 1141.34 seconds. Unreal's
own summary was `Success - 0 error(s), 152 warning(s)`; map processing is
explicitly present in the log. Warnings include pre-existing missing optional
asset references and project setting priority notices; this is not a clean
content audit. Evidence:
`.local/simulator-cache/3cef0a92-1bc7-4a14-b0b3-6f7bf6c30ca3/unreal.log`.
The cache is retained and no automatic per-start preparation was added.

`simulation start --target test` completed and placed the native windows.
`vehicle initialize test` reattached the same Unit/Main Node with live VDP
data and `vdpRestarts=0`. New local run:
`38423d6e-9b17-4046-bae0-0cace30799eb`. First attachment preserved actor 25 and
reset generation 0. VDP78/V3, Brake58/V3 and Tire34/V1 remain installed.

Native UI Manual, Safe Stop -> Manual and brief arrow input passed. At the
first check after those actions, 633 commands were accepted with zero command
timeouts, ownership disconnects or rejected messages. Brake still displayed
Inspection recommended and Tire Monitoring; neither model was reset.

Autopilot then covered about 160 m and reached 19.5 km/h. Across 66 consecutive
30-frame VSS log intervals after startup, the largest interval was 1.584 s
(nominal 1.5 s). No STALE/display-loss/bridge failure was recorded in that
window, and no texture-building message was logged in the new simulator run.
The native Safe Stop button responded; the final state was operator Stop,
zero speed, 761 accepted commands and zero timeouts/disconnects/rejections.
This is a short live smoke, not a repeat of the operator's complete manual
route. The native windows remain open for that visual check. No commits or
pushes were performed in this correction.
