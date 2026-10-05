<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Stage 2 UI corrections — 28 September 2026

- Status: E2E findings 1–3 corrected and locally deployed; transport finding 4 is open and user-deferred as `VDP-TIMEOUT-01`.
- Parent: [retained-Test E2E](distribution-stage2-live-e2e-2026-09-28.md).
- Scope: the retained Factory .39 Test; no new Factory, service release, publication, provisioning or retirement.

## Corrected behavior

| Finding | Correction | Evidence |
| --- | --- | --- |
| Ignition off confused with Park/Resume and Finish | A present, stopped controller has a separate `controllerStopped` presentation. Both Reset controls explain that the controller is switched off. Preparation/publication stay disabled. | Red/green regression; actual Test power-off shows **Controller switched off**, with neither the legacy same-run prohibition nor an instruction to Finish. |
| Recovery and Session instructions | Recovery-in-progress has its own guide. Session distinguishes Safe Stop, controller ignition recovery, destructive Finish and unqualified laptop sleep/wake. | Busy-recovery and real-retirement precedence covered by unit tests; Session text inspected in the deployed UI. |
| Native caption overlaps the external-network button | Draw and clip the caption in the 12-point gap between the maneuver and network rows. | Native geometry tests and actual 914×502-point window inspection. |
| Return-to-road caption becomes false in Autopilot / Safe Stop | Caption describes the completed return action and retained model/advisory state, not the current driving mode. | Actual Return to road → explicit Autopilot → explicit Safe Stop. Autopilot mode was selected; the captured frame is stationary and is not new driving-performance evidence. |

Real partial Finish still takes precedence and retains Continue Finish protection.
No new power control, automatic Autopilot, credential path or lifecycle was added.
No model thresholds, Reset semantics, authentication or network policy changed.

## Build and regression

- Presenter: **331 tests passed**, including seven new power-state regressions;
  TypeScript type check passed.
- Native Controller: **7 tests passed**, including the compiled Swift caption
  geometry/state harness; no vehicle/window launched by those unit tests.
- Presenter stop / portable host / portable VM contracts: **34 tests passed**.
- Offline incremental build: Controller compilation 4.36 s, web build 0.44 s;
  signing and strict verification passed. The native Presenter executable was
  reused only after its digest matched the previous build.
- No CARLA cook, Factory build or service build was performed.

The initial test invocation for the Python contract suites lacked the package
import path and did not execute tests. The corrected invocation used the pinned
Python 3.12 with explicit source/test paths; all 34 passed.

## Controlled deployment and retained state

The generic UI assembler also collected newer orchestrator helper sources.
The exact-change guard rejected that broader candidate before installation.
A bounded UI-only payload instead retained the previous pinned helper closure
and changed only web output, the native Controller executable and UI metadata.
All **14,077 non-UI manifest rows** are unchanged. The obsolete hashed web asset
is retained with the original UI backup rather than irreversibly deleted.

Host/VM lock pins now reference the updated manifest chain. The VM manifest
change is its host-manifest reference, not a QEMU or Factory payload change.
A final promotion check encountered the expected pending-lock mismatch after
the payload copy. No mutation was replayed: pins were updated, then the entire
small UI payload, unchanged non-UI manifest rows and Test owner were independently
reconciled. QEMU PID 3525 remained uninterrupted during UI installation.

The owned Presenter had originally been launched with `--output json ui serve`;
the CLI's exact-owner stop check rejected that noncanonical command spelling.
The verified existing terminal session was stopped with Ctrl+C, and Presenter
was restarted with its canonical `ui serve` command. The owner guard was not
weakened. Supporting the alternate spelling remains a CLI compatibility note,
not a new passing stop-path claim.

Applying Controller required the normal local simulation stop/start. The old
scene was recreated, while the Test VM, Unit, Node, versions and backend/model
state were preserved. The replacement simulation run is
`6a61fef1-9892-41c2-b7aa-e1f8f9a80b8b`; actor 25, assignment generation 38.
Presenter's **Connect in Manual** restored the same provisioned Test. Window
placement and z-order were reported verified by the ordinary workspace path.

The retained target remains:

- VM: `48a0e19c-857f-44b8-9b68-38b585a8278f`;
- Unit: `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb`;
- Node: `6318b28e-688d-47e3-a265-7753b9f31ef8`;
- VDP 117/V3, Brake 92/V3, Tire 49/V1, Factory .39.

Production and its .31 backing remain unchanged. Internal available space was
approximately **91.24 GiB** after UI promotion, above the 90-GiB guard.

## Live ignition recheck

All times UTC. After Safe Stop and empty-queue checks, one graceful power-off
was accepted at **09:39:50.349**. The deployed UI showed the corrected off-state
guide and both disabled Reset explanations. Session's updated instructions were
also inspected. The busy-recovery guide is regression-tested; its short-lived
appearance was not captured separately in this live cycle.

Power-on started at **09:40:39.016** and returned at **09:41:16.324**. Automatic
recovery completed at **09:41:42.712** in `READY_SAFE_STOP` (63.70 s after power-on
intent; recovery operation itself 9.87 s). The boot changed from
`a3484eea-7b3f-4dbd-aee5-c2868a82292d` to
`b2b794b5-b803-408f-8939-0bb5aebde1ff`, without replacing the Unit/Node or changing
installed versions. No automatic Autopilot was started.

By the 09:42:29 read, VDP was READY/LIVE and both services had fresh backend
APPLIED facts. Native telemetry subsequently showed both inspection
recommendations at Safe Stop / 0 km/h. The stored models and prior assessment
history remained present. The UI test's preceding local operation produced one
additional Tire assessment; this is not a claim that all counters were frozen.
No advisory Reset was submitted in this correction run.

IAM/SM/CM/KUKSA-auth-compat/VDP were active with `NRestarts=0`. SELinux remained
Enforcing. The startup window includes the known sshd directory-search AVC
class and two getty `checkpoint_restore` capability AVCs; it is not an assertion
of zero system-wide AVCs. No policy was widened. Core collection stayed disabled.

## Transport investigation — not closed by the UI fix

A corrected, fixed-field projection recovered **96 old-boot transport records**
between 07:58 and 08:05. They include 20 timeout records from **08:01:59.925** to
**08:04:48.322** in that bounded window. These are not unique request counts:
the existing logger deduplicates endpoint/result transitions and does not retain
per-request arrival/consumption timing. An earlier JSON-only extractor returned
zero because transport messages are fixed-format text, not JSON; that was an
evidence-tool limitation, not proof that the journal was empty.

A deterministic local probe exercises the actual VDP runtime loop and advisory
transport with a fake socket/clock and controlled telemetry work:

- At 50 ms local processing, two already-queued Set replies are accepted.
- At 2.1 s local processing, the next `tick` expires both before `recv` consumes
  them. Both replies are then read but no longer match pending entries.

This establishes a possible consumer-delay mechanism, **not the historical
incident's cause**. It does not distinguish a delayed peer/network from local
KUKSA work or an earlier receive backlog in the old run. Gateway APPLIED is a
separate subscription fact, so it can coexist with a lost Set acknowledgement.

Next transport gate: correlate bounded request send, reply arrival/consumption,
main-loop delay and KUKSA publication duration on a reproduced case. Preserve
strict validation, bounded queues and the current failure semantics while
selecting a fix. No timeout increase, telemetry dropping, VDP source patch,
guest instrumentation, service restart workaround or new VDP publication was
introduced by this UI correction.

Final read at **09:48:59 UTC**: the same recovered boot and versions, ONLINE,
Safe Stop at 0 km/h, fresh backend observations and empty outboxes. The last
six-minute journal window contained 36 forwarding and 36 Set-accepted records,
no Set timeout or SEGV, and all five monitored services still had `NRestarts=0`.
This bounded success does not close the earlier timeout cause.

### User disposition — deferred follow-up

On 28 September the user explicitly requested recording this VDP timeout and
returning to it later, while resuming the main distribution plan.

- Tracking ID: **VDP-TIMEOUT-01**.
- State: **OPEN / USER-DEFERRED**, not fixed, disproved or accepted as harmless.
- Owner: VDP transport, with Gateway correlation owned by integration.
- Preserved evidence: the old-boot fixed-field projection, local receive-order
  probe and the exact retained Test referenced above.
- Resume with: per-request timing correlation before choosing a transport fix;
  then a regression reproducing the proven cause and a bounded live recheck.
- Immediate scope: no further timeout investigation or VDP changes in the
  current packaging work; Stage 3 may continue with this explicit limitation.
- Acceptance limit: this deferral is not unconditional Stage 2 acceptance or
  permission to claim interruption-free advisory transport. Reassess it before
  external distribution/support acceptance, or if it becomes a blocker during
  the installed-product checks.

Clean installation, fresh serial V1→V2→V3 updates and clean-Mac acceptance are
not claimed here. The deferral changes work order, not those qualification facts.

## Evidence

Ignored local directory: `CarlaSim/Build-distribution-stage2-20260926/`.

- `ui-inputs-005`, `ui-fix-payload-005`: bounded build/assembly receipts;
- `ui-fix-originals-20260928`, `ui-fix-promotion-20260928.json`: recoverable prior UI and reconciliation;
- `e2e-ui-fix-before.json`, `e2e-ui-fix-after.json`, `e2e-ui-fix-final.json`,
  `packaged-live-ui-fix-recovery-final.json`, `ui-fix-ignition/`: live snapshots and single-use power receipts;
- `ui-fix-ignition-off.png`, `ui-fix-session.png`,
  `ui-fix-native-autopilot.png`, `ui-fix-native-final.png`,
  `ui-fix-presenter-final.png`: visual proof;
- `vdp-startup-transport-20260928.json`, `vdp-receive-order-proof.json`:
  redacted old-boot facts and explicitly synthetic mechanism probe.
