<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Distribution Stage 2 — Retained-Test Live E2E, 28 September 2026

- Status: Functional checks passed in the scope below; UI findings remain open.
- Owner: Demo Solution Team.
- Source checkpoint: `22ee79e` on `codex/installable-demo-stage3`; no product source or packaged binary changed during this run.
- Scope: UI-led operation of the retained Factory .39 Test with the selected packaged runtime, supported by read-only guest, backend and AosCloud evidence.
- Parent: [Stage 2 closure checklist](distribution-stage2-closure-2026-09-28.md).

Follow-up: [same-day UI corrections and recheck](distribution-stage2-ui-corrections-2026-09-28.md)
close findings 1–3 below. This report preserves the original pre-fix observations;
finding 4 (transport causality) remains open.

## Result and limits

The real CARLA → Gateway → VDP/KUKSA → Brake/Tire → backend → local driver
advisory chain passed online, during an external-network outage, after
reconnection, and after one graceful controller power-off/power-on cycle.
Twenty-three recorded-state assertions passed. This is not a fresh installation,
new-user enrollment, all-version update run, power-loss durability test, or
unconditional Stage 2 acceptance.

No Factory/Game/service rebuild, signing, publication, provisioning, Finish,
retirement, Production mutation or disk cleanup occurred. In particular, the
previous V1/V2 evolution evidence is not relabelled as newly executed here.
Product defects were recorded, not silently fixed during qualification.

The active plan still requires explicit disposition of the UI and advisory
observations before new Stage 3 work. A clean all-version run would separately
need an exact authorized Test retirement/new target and release set, publishing
each successive version only after the previous version is installed and
verified; VDP installation remains gated by Safe Stop.

## Exact retained target

| Item | Observed value |
| --- | --- |
| Environment | `aws-stage.epmp-aos.projects.epam.com`, Test only |
| Factory | `6.1.1-maninblack.39` |
| VM | `48a0e19c-857f-44b8-9b68-38b585a8278f` |
| Unit | `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb` |
| Node | `6318b28e-688d-47e3-a265-7753b9f31ef8` |
| Installed profiles | VDP V3 / 117.0.0; Brake V3 / 92.0.0; Tire V1 / 49.0.0 |
| Simulation run | `3b9a419d-909e-4723-b554-d4bb499ed88f`, actor 25 |
| Final state | ONLINE; both Cloud service instances active; no pending component or service error; network ON; Safe Stop, 0 km/h |

Production remained stopped with its original Factory .31 backing. Existing
backend histories, identities, source, credentials, warm caches and video assets
were preserved. The two intentional advisory resets changed current model state,
not backend assessment/event history. Maneuvers and Return to road changed the
simulated vehicle state through their normal UI controls.

## Execution matrix

| Check | Result | Evidence and qualification limit |
| --- | --- | --- |
| Main cards and installed software | PASS | Correct functional profiles and release numbers, .39 firmware, no pending update; current input observation distinguished from old result |
| Brake backend popup | PASS in observed scope | Overview, Records, pagination and braking-recording filter; no V1 recording in this V3 run, so no fresh V1 chart proof |
| Tire backend popup | PASS | Overview, latest-result detail and nested-dialog close behavior |
| Cloud monitoring popup | PASS | Software, CPU/memory for controller and service instances, disks and traffic labels inspected |
| Online Brake maneuver | PASS | Native completion, new backend assessment and local advisory evidence |
| Online Tire maneuver | PASS | New Tire assessment; its final braking also produced a Brake assessment |
| Independent advisory resets | PASS | Matching Gateway CLEAR; Brake reset left Tire unchanged, then Tire reset left Brake unchanged; assessment/event history retained |
| External network OFF | PASS | Settled backend records/receipt times stopped changing while local models processed both real maneuvers and produced inspection recommendations |
| Offline Return to road, Autopilot, Safe Stop | PASS | Stationary placement first, explicit Autopilot then driving at about 19.4 km/h, explicit Safe Stop to 0; no automatic drive on return |
| External network ON and queued delivery | PASS | All 39 captured queued identities received exactly once; both outboxes empty afterwards |
| Ignition off/on | Functional PASS; UI FAIL | Different guest boot, same Unit/Node/run/actor, preserved storage/model/versions and recovery in Safe Stop; misleading interruption/Finish text |
| Post-ignition maneuvers | PASS | New model inputs and assessments on both services, fresh APPLIED advisory facts, empty queues, no extra guest boot or automatic manager restart |
| Team and Session views | Partial PASS | Installed service state and disabled unpublished-candidate actions inspected without preparing/publishing; Session contains obsolete shutdown instructions |
| Clean creation, serial V1→V2→V3 updates, Finish | NOT RUN | Retained-Test scope; exact destructive/publication boundary not crossed |
| Clean Mac / installed first-use journey | NOT RUN | Separate accepted distribution gates |

Presenter and native controls were used for popups, maneuvers, resets, network
switching, road return and driving. Ignition had no native power button: after
Safe Stop and empty-queue guards, the existing SSH path requested one graceful
guest power-off; the canonical Demo Control VM-start path then started the same
overlay. No direct product-state injection, fake telemetry, model-threshold
change, service restart workaround or security relaxation was used.

## Timing and state transitions

Times below are UTC; the desktop displayed Europe/Berlin (UTC+2). Measurements
from discrete UI observations are upper bounds, not exact server latencies.

| Action / milestone | Measurement |
| --- | --- |
| Brake / Cloud popup first observed open | 284 / 292 ms |
| Brake / Tire reset first UI feedback | 159 / 89 ms |
| Brake reset submitted / Gateway CLEAR shown | 08:53:28.016 / approximately 08:53:29 |
| Tire reset submitted / Gateway CLEAR shown | 08:53:55.284 / approximately 08:54:00 |
| Network OFF first feedback | 735 ms |
| OFF click / ON click | 08:54:34.807 / 09:00:17.517; 342.71 seconds between clicks |
| Network ON first feedback | 744 ms |
| First / last captured Brake queued receipt after ON | 5.63 / 7.93 seconds |
| First / last captured Tire queued receipt after ON | 35.15 / 37.76 seconds |
| Cloud ONLINE first UI observation after ON | At most 28.42 seconds |
| Both backend input cards observed fresh after ON | At most 136.30 seconds; coarse observation, not a measured polling SLA |
| Power-off accepted / QEMU absence observed | 09:03:05.788 / 09:03:40.612 |
| Power-on intent / VM-start receipt | 09:04:07.626 / 09:04:44.339; 36.71 seconds |
| Boot recovery READY_SAFE_STOP | 09:05:01.299; 53.67 seconds after power-on intent |
| Boot-recovery operation itself | 6.42 seconds |

Cloud ONLINE preceded Tire queue drainage. Presenter showed the intermediate
delivery-pending/last-known state instead of fabricating fresh telemetry.
Returning from a team perspective briefly displayed cached backend observations
as Last known, then refreshed them to RECEIVING/WAITING; historical result
timestamps also caught up. No unlabelled old/new-state oscillation was confirmed
in this bounded run. It is not a continuous frame-by-frame flicker test.

## Offline delivery and independent reset proof

Settled offline snapshots at approximately 08:55:16 and before reconnect have
identical backend assessment, event and advisory rows and identical current
function-observation receipt times. Local recommendations became active during
the outage. The final captured outboxes contained:

| Service | Captured messages | Delivered exactly once |
| --- | --- | --- |
| Brake | 2 assessments, 1 event, 11 advisory facts | 14 / 14 |
| Tire | 3 assessments, 1 band-change event, 11 advisory facts, 10 function statuses | 25 / 25 |

Identity comparison uses assessment/event/status IDs and advisory epoch,
sequence, request and Gateway state. Additional messages produced after the
last offline snapshot are outside the 39-message set. Backend reads are bounded
to the latest 100 rows per collection; this is not an assertion about all
historical pages. The captured set fits that bound and both final outboxes are
empty.

Reset comparison preserves assessment/event history and verifies team
independence. The immediate button feedback is not treated as completion:
matching Gateway CLEAR and the independent local recommendation are required.

## Ignition persistence and post-boot operation

The guest boot ID changed from `5689a62d-150e-40c7-8921-1f4185c37b65` to
`a3484eea-7b3f-4dbd-aee5-c2868a82292d`. The storage inode/ownership and service UID
comparisons matched before/after. Model condition, generation, recent-input
count and assessment-presence fields survived unchanged. Cloud versions and
simulation run/actor/reset generation were unchanged across the power cycle.

Initial advisory Unavailable during startup was followed by readiness READY
and fresh APPLIED facts. Native inspection recommendations were observed again
by 09:06:18. The car did not start driving automatically.

Post-boot Brake and Tire maneuvers started at 09:10:32.225 and 09:11:00.271.
By 09:12:02, Brake assessment count increased from 16 to 18 and Tire from 11 to
12; local recent-input counts matched. Both current advisory facts were APPLIED
and both queues empty. IAM/SM/CM/KUKSA-auth-compat/VDP stayed active with
`NRestarts=0`; the boot ID did not change again. Final native state was LIVE,
Safe Stop / STOPPED, both Inspection recommended, network ON.

## Findings requiring disposition

1. **Ignition is misclassified as retirement/interruption in Presenter.**
   While the guest was off, the guide claimed “Same-run restart is not supported”
   and directed the operator to Finish and create a new controller. Both Reset
   captions said “Reset unavailable during Finish” despite no Finish operation.
   Session/Lifecycle also instructs “Finish before shutting down. Start a fresh
   run next time.” Actual same-identity recovery passed. Read-only source
   inspection finds stopped-present controllers classified as `interruptedRun`
   in `StudioWorkspace.tsx`; that is merged into `lifecycleRestricted` and passed
   to `ResetScenario` as `retiring`. The existing no-revive protection for a real
   partial Finish must be preserved when correcting the ignition presentation.
2. **Native caption overlaps the network button.** The already recorded
   inter-row geometry defect is visible for Return-to-road and maneuver
   preparation/completion captions at 914×503 points. Primary controls remain
   usable. It still needs a bounded layout correction and native recheck.
3. **Return-to-road action text is stale after subsequent driving actions.**
   “On road · stationary Manual · select Autopilot when ready” remained after
   explicit Autopilot and then Safe Stop. The authoritative mode/speed were
   correct; the action caption was not a current-state description. Separate
   historical completion feedback from current driving status or expire it.
4. **Prior Set-response timeout cause remains open.** Overlapping bounded
   journal windows in this E2E continuation showed no `VISS_RESPONSE_TIMEOUT`
   or VDP SEGV, with fresh APPLIED receipts and stable processes. That does not
   explain or close the earlier startup/session timeouts documented in the
   parent report. Correlate actual Set request/reply consumption timing before
   changing deadlines or transport behavior.

The narrow in-app browser reserves space for the native workspace and wraps
the three cards heavily; the lower controller section is reachable by scrolling.
This was not classified as hidden data or a desktop-layout regression. Review
readability at the intended presentation size as part of UI acceptance.

Some pointer-based in-app browser actions did not activate controls. State
inspection confirmed no reset submission before using the same visible button
with Enter. Keyboard activation succeeded without duplicate requests. This is
recorded as an automation/input limitation, not an established product defect.
Trace's count of two was the two completed reset receipts, not two errors.

## Security, resources and retained evidence

SELinux remained Enforcing and core-dump collection remained disabled
(`|/bin/false`). Sampled logs had no new VDP/KUKSA/service AVC class. They did
contain the previously recorded `sshd_t → aos_var_run_t:dir search` category
(106 records in the final six-minute window). This is not a clean-all-AVCs
claim and no permission was broadened to suppress it.

Internal available space at the final resource observation was 95,984,592 KiB
(approximately 91.54 GiB), above the accepted 90-GiB live guard. Work SSD had
589,507,096 KiB available. No large copies, images, build caches or runtime
inputs were removed or created.

Compact non-secret evidence is deliberately retained under the ignored CARLA
workspace directory `Build-distribution-stage2-20260926/`:

- `e2e-*.json`: bounded snapshots, timings, ignition receipts and the 23-check analysis;
- `e2e-ui-offline.png`, `e2e-ui-reconnected.png`, `e2e-ui-ignition-off.png`,
  `e2e-ui-session-lifecycle.png`, `e2e-ui-final.png`;
- `e2e-native-offline-advisories.png`, `e2e-native-final.png`;
- `e2e_read_20260928.py`, `e2e_power_20260928.py`, `e2e_analyze_20260928.py`:
  exact-Test harnesses, not shipped product or replacements for UI evidence.

No guest diagnostic client, systemd override, new credential or policy module
was installed. Retain the current Test for the bounded UI/transport follow-up;
do not delete it to make an incomplete qualification appear clean.
