<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Demo Desktop Plan

- Status: Accepted; step 0 published, step 1 development/live review in progress
- Version: 1.3
- Prepared: 2026-09-07
- Owner: Demo Solution Team with Vehicle/Gateway runtime owner
- Design: [Demo Control](../../architecture/demo-control.md#native-demo-desktop--accepted-direction-2026-09-07)
- Starting evidence: [Source checkpoint](../../qualification/democtl-release-checkpoint.md#desktop-preparation-checkpoint--2026-09-07)

## Agreed result

Keep CARLA/Unreal as a separate native window. Combine Driving Control and
Engineering Telematics into one native application window beneath CARLA:
controls on the left, telemetry on the right. Preserve the accepted composed
workspace, shared header, right-hand Presenter panel and black background.
Do not embed, capture, stream or reparent CARLA into the control application.
Avoiding video integration avoids its additional implementation and runtime
cost; no measured performance loss from embedding is claimed.

An `AosEdge Demo.app` launcher will start the existing demo through Demo
Control and restore its windows. It will not become a second orchestrator.
A dedicated ordinary macOS Desktop/Space will be configured once; automatic
Space creation, private APIs and arbitrary cross-application window migration
are not part of this plan.

## Development trial — 2026-09-07

After the source checkpoint was published, the operator explicitly authorized
step 1 implementation and immediate live review, deferring broad formal checks
until the working UI is visually accepted. Step 2/3 have not started.

The first native control/telemetry window is implemented. The existing VISS
client supplies bounded JSON snapshots to a single child owned by the native
Control app; normal simulation startup no longer launches a Terminal. Existing
terminal monitor mode and cleanup of a previous owned Terminal are retained.
The existing controller occupies the left 44% of the combined window; telemetry
occupies the right. The operator subsequently accepted fixed Dashboard / Vehicle /
Data pages instead of expanding engineering details; CARLA remains separate.

The fixed-page revision keeps vehicle identity, freshness, speed and driving
state visible above every page. Dashboard contains pedals and advisory; Vehicle
contains steering/gear/RPM and a four-wheel schematic; Data contains stream
metrics, coordinates and session/timestamp fields. No scrolling, window growth,
Cloud state or duplicate advisory footnotes are introduced. Native screen-point
typography replaces scaling the telemetry canvas; the current workspace geometry
is preserved. This revision is a native UI change, not a VM or VDP rebuild.

Only the Swift window and VISS client were compiled. Thirteen workspace and
27 runtime-tool tests plus the native dashboard JSON/freshness test passed.
`democtl simulation stop/start`, `vehicle select test` and `workspace status`
completed; VMs and Cloud identities were not restarted or recreated. Native
visual inspection showed LIVE Test telemetry at 19.4 km/h in Autopilot. Clicking
the same window's Safe Stop resulted in 0.0 km/h, 0% accelerator, 100% brake and
STOPPED (Gateway observation). The live demo remains open in Safe Stop for
operator review. Full regression, telemetry-child failure/reconnect lifecycle,
further native accessibility/layout refinement and source publication are not
claimed by this development trial. Advisory remains unavailable.

### Selected-vehicle connectivity — authorized development increment

The operator subsequently requested the planned disconnect/reconnect button.
Driving Control now uses `democtl vehicle connectivity status|off|on`, without
moving Aos/network concepts into the telemetry dashboard. It faults only the
selected VM's external uplink, retaining local VISS and maintenance SSH.
Implementation and recovery are described in
[Demo Control](../../architecture/demo-control.md#vehicle-external-connectivity-development-increment--2026-09-07).

The focused CLI live trial observed the same Test Unit change to Cloud Offline
while VDP 15.0.0 remained READY with 23 signals, PID 1833 and unchanged restart
count 1. ON removed only the owned transient filter. This is a development
proof, not full advisory/backend replay or Production qualification. No image,
component, Unit identity, existing firewall table or Mac network was changed.

The installed native button was then exercised OFF/ON. While OFF, the live
Dashboard showed Autopilot, MOVING, 19.4 km/h and LIVE telemetry; guest VDP
remained READY with the same PID/restart count. Reconnect returned the button
and actual filter to ON; the CLI trial also confirmed that the same Cloud Unit
returned Online. Simulation stop/start and Test selection used democtl to load
the new native binary; neither VM was restarted. Targeted checks passed:
14 connectivity tests, 13 source-selection tests, 8 runtime-tool tests and
Swift compilation. Full formal regression/publication remain deferred.

## Order and exit criteria

### 0. Freeze the working baseline before implementation

Record and commit the current Solution and Runtime source, tests and evidence;
push the exact normal branches without force. Include the existing native
Presenter, initial stationary-Manual preparation, Cloud-only Platform status,
current-vehicle projection, dashboard additions and interactive duration fix.
Do not rebuild Factory, VDP, Unreal or the installed runtime for bookkeeping.

Run bounded local regressions and source/document hygiene checks. Record
operator-confirmed live results separately from fixtures and unqualified scope.
Images, compiled binaries, signed bundles, credentials, journals and captured
telemetry stay outside Git. Keep immutable Factory .31, active overlays,
frozen VDP profile inputs, published releases, Builder and useful build caches.

Inventory cleanup candidates and remove only proven disposable, inactive
scratch. Preserve branches/worktrees still referenced by build/runtime inputs,
unique source work and historical diagnostic state with unresolved ownership.
Record retained items instead of broad cleanup or unrequested lifecycle calls.

This user request authorizes documentation, source commits/pushes and bounded
housekeeping only. Subsequent implementation starts after this checkpoint is
handed off; no new UI or launcher code is part of step 0.

### 1. Combine Driving Control and telemetry

Owner: `carla-ego-runtime` for the native Swift/AppKit window and the existing
VISS client; `aosedge-sdv-demo` for launch/layout integration and documentation.

- Retain the existing command bridge, keyboard behavior and explicit Safe Stop.
- Reuse the VISS client and its validated data/freshness rules. Define its
  bounded machine-readable live output before implementation, rather than
  parsing ANSI terminal text or adding an independent telemetry helper.
- Keep control and telemetry processing separate so a stalled data stream does
  not block commands. Preserve manual focus-loss safety and stationary
  `manual_ready` behavior when interacting with the combined window.
- Display selected-vehicle context, drive mode, physical stop observation,
  speed/pedals and existing signals. Use the accepted fixed Dashboard / Vehicle /
  Data pages; diagnostics must not expand the window or require scrolling.
- Show missing/stale/disconnected data explicitly. Driver Advisory remains
  unavailable until the separate real Brake/Tire advisory chain is connected.
- Engineering telemetry comes from Gateway/VISS, not from invented Cloud
  telemetry or a VM SSH probe. Platform Team remains Aos Cloud-only; Cloud
  Installed is not proof of running VDP, fresh data or Safe Stop authorization.
- Keep terminal monitor mode available for engineering CLI use, but remove its
  separate Terminal window from the normal demo startup path. Migrate the
  existing runner's Terminal dependency too; adding a second subscriber does
  not constitute replacing the old dashboard.
- Launch/stop through `democtl simulation start/stop`; update
  `democtl workspace restore/status/close` only within their existing ownership
  and lifecycle boundaries. Closing Presenter alone still does not stop VMs.

Exit: targeted native/client/protocol tests; one live democtl-driven start,
drive/Safe Stop, telemetry-loss presentation and stop/restart; operator visual
acceptance on the built-in display. Compare responsiveness with the preserved
baseline. No Factory/VDP release or Cloud identity reset is required.

### 2. Add the native launcher

Owner: Solution application layer, reusing the existing native Presenter where
appropriate. The exact package layout is an implementation detail to record
before adding code; do not fork orchestration logic into the runtime repo.

- Opening the application starts the normal existing-environment workflow:
  owned UI service, VMs, simulation, Test selection and workspace restoration.
  Reuse already-running owned instances; do not reset a healthy connection or
  create duplicate applications/jobs. Show actual stages and blockers.
- VM enrollment uses the existing visible native access dialog or explicitly
  saved Keychain item, never an invisible terminal prompt or browser password.
- First-time environment creation/provisioning remains an explicit Prepare
  action using the existing Demo Control workflow. Opening the launcher does
  not silently create identities, publish a component or reprovision Units.
- Stop Demo uses Demo Control to stop simulation and VMs and close owned UI
  processes safely; it does not deprovision/delete Units or remove disks.
- Restore Layout does not restart the simulation or VMs.
- Add any missing owned-service lifecycle operation to Demo Control itself,
  exposed to CLI as well as launcher. Do not introduce launcher-only shell
  workarounds, blind retries, backup workflows or repeated full-system audits.
- Preserve the existing single active operation and uncertain-result handling;
  UI service termination must not abandon an in-flight operation.

Exit: one-click cold start of a preserved environment, duplicate-open reuse,
visible failure/input, Stop Demo, and repeated start with operator visual
control. One click reduces operator work, not CARLA's actual loading time.

### 3. Configure the dedicated macOS Space

Create one ordinary Desktop manually and document the one-time supported app
assignment. The combined native control/telemetry app removes the need to bind
the user's general Terminal application to the demo Desktop. Keep CARLA in its
own window, visually aligned with the native panels.

Test launch, existing-window reuse, Space switching and layout restoration.
Do not confuse window geometry on a display with membership in a Space.
If macOS app assignment cannot meet a specific relocation case, report that
limitation rather than add private APIs or keyboard-driven Mission Control.

## Explicitly deferred

Production FOTA (platform delivery limitation), complete Driver Advisory and
offline backend replay, CARLA video embedding/capture, image rebuilds,
fresh-overlay qualification and slide preparation are separate work. This
desktop plan does not silently authorize any of them or claim their completion.
