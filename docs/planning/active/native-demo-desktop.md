<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Demo Desktop Plan

- Status: Accepted direction; implementation not started
- Version: 1.0
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
  speed/pedals and existing signals. Keep diagnostic detail collapsible.
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

Production FOTA (platform delivery limitation), complete Driver Advisory,
external-connectivity toggle, CARLA video embedding/capture, image rebuilds,
fresh-overlay qualification and slide preparation are separate work. This
desktop plan does not silently authorize any of them or claim their completion.
