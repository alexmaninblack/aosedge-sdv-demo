<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .39 — live ignition qualification

Status: focused raw reboot, graceful full process power-cycle recovery and
post-cycle functional checks **PASS**, with exclusions below. No baseline promotion.

Follow-up: [existing-installation external-OFF/ON qualification](factory-39-offline-2026-09-24.md)
passes a five-minute interval on the same Test, with readiness/feedback observations.

## Authorized boundary

The operator explicitly approved retirement of Test .38 Unit
`a6cf9e5f-5859-4302-9f8f-791d603e58a8`, its working VM and run backend data,
then creation of Test .39 in staging for ignition off/on. Factory artifacts,
published releases and Production are preserved. An initial tool rejection
occurred before execution; the exact-target approval then permitted one attempt.

- Retirement completed17:52:50UTC; native lifecycle reconciled Cloud absence
  before local cleanup. Production journal metadata unchanged.
- Fresh create17:53:38→17:54:49UTC, Factory `6.1.1-maninblack.39`.
  VM `48a0e19c-857f-44b8-9b68-38b585a8278f`.
- Provision17:59:33→18:00:05UTC,31.98s. Unit
  `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb`, Node
  `6318b28e-688d-47e3-a265-7753b9f31ef8`.
- Existing VDP117/V3, Brake92/V3 and Tire49/V1 were separately read READY.
  No new signing/upload. This is a focused retained-state test, **not** a fresh
  serial V1→V2→V3 publication qualification.
- CARLA/Driving Control start completed41.8s. Provision attached the protected
  Gateway without simulator recreation. Safe Stop18:08:27UTC confirmed0km/h,
  brake1.0. Cloud installed117 with no pending update by18:08:31.
- Service runtime inputs prepared5.25s, Brake/Tire assignment8.2/9.22s.
  Managers and VDP active, automatic restarts0, READY/LIVE, Enforcing, no core
  collector and no SEGV in the bounded health window. Existing SSH search AVC
  category remains explicitly excluded, not hidden as a clean all-domain audit.
- Real Brake/Tire maneuvers completed15.11/14.74s; backend/UI received results.
  Both end in Safe Stop. No Autopilot was enabled.

## Additional observations before reboot

1. Presenter shutdown owner check omitted the valid repository-relative
   `apps/demo-orchestrator/.venv/bin/democtl ui serve` spelling. Exact PID/cwd
   inspection and a failing mocked regression confirmed it. Recognize this
   spelling only with the exact repository cwd; foreign cwd remains refused.
   Stop tests7/7 and boot recovery17/17 pass. Updated Presenter is now running;
   no image rebuild is needed for this host-only change.
2. Fresh Test has no `runtime.externalConnectivity` record although the actual
   packet filter reportsON. The new worker consequently does not establish its
   boot observation until a normal idempotent ON action records it. At18:10:50
   the explicit command returnedON/noOp. This is a recorded **first-run host
   prerequisite defect**. Source correction now observes the actual guest gate
   once when the record is absent; it never toggles the network. ExistingOFF,
   UNCERTAIN and malformed/unknown records still defer. Negative control failed
   exactly the missing-record case; corrected boot suite20/20 passes. A real
   read-only .39 proof with the missing-field snapshot held only in RAM recorded
   ON/OBSERVED and idle repeat, zero guest mutations, unchanged live journal.
   This does not claim a second fresh provision without the ON action was run.
   Corrected Presenter was loaded before the full process power-cycle test.
3. Presenter correctly shows installed117 but says its functional profile is
   not confirmed after reuse of an earlier run's publication. No false absence
   or fabricated profile is displayed; separate package/profile binding follow-up.
4. Native-window inspection timed out in Computer Use; this does not establish
   a product UI freeze. CLI control and browser Presenter observation succeeded.

Compact exact-target intent/baseline/reboot/result evidence is retained under
the dated private proof root in `factory39-*` and `test39-*`. No diagnostic
binary, transient policy, credential or artificial telemetry is injected.

## Reboot and full ignition results

| Gate | Raw guest reboot | Full VM process power cycle |
| --- | --- | --- |
| Initiation UTC |18:13:53.501|OFF18:19:19.862; ON18:20:05.192|
| Real shutdown |kernel boot ID changed|QEMU absent18:19:51.292; disk unheld before ON|
| Normal VM-start completion |not manually invoked|33.27s|
| Automatic source restoration |18:14:32.021→18:14:37.800|18:20:48.330→18:20:54.283|
| Restoration step duration |5.78s|5.95s|
| Start command to route ready |~44.3s|~49.1s|
| Final state |READY_SAFE_STOP; VDP READY/LIVE|READY_SAFE_STOP; VDP READY/LIVE|

Both cycles retain exact Unit/Node/VM/system identity, run
`72d823c5-181d-475b-91c1-1c4def2db4bf`, assignment29 and strict mTLS enrollment.
No provisioning, reset, scene recreation or Autopilot command occurs. Physical
speed0km/h, brake1.0, no lingering control hold. Cloud returns ONLINE with
117/92/49, active services and no pending update/error.

Post-boot VDP is initially NOT_READY while the host reconstructs the retained
route/credentials; it then becomes READY without restarting. SM/VDP retain their
first boot PIDs, NRestarts0. CM has one normal controlled restart when Demo
Control restores the staging discovery endpoint (`cloud_guest.py`); it is not
an automatic crash restart. Do not call all managers continuously running.

The observed boot IDs are distinct: original52dd4a01…, reboot3fee6df3…,
power cycle2d803274…. After the second cycle IAM1051/SM1139/CM1318/VDP1165
are active/success/NRestarts0. Enforcing and disabled core capture remain in
place. Only the recorded audit/getty/SSH baseline AVC categories appear;
no VDP/KAC-specific denial or SEGV appears in the captured windows.

Storage/UID comparison passes for both cycles: BrakeUID5000, storage inode15,
state inode32388; TireUID5001, storage inode35, state inode64772. Numeric quotas
remain Brake8192/1024KiB and Tire4096/2048KiB. Brake generation2/recent2 and
Tire recent1/assessment remain; both retain INSPECTION_RECOMMENDED. Backend
assessment counts stay2/1 and original timestamps/IDs remain unique. New
function observations and Gateway APPLIED confirmations arrive after recovery.
Advisory sequence numbers advance normally, not reset or byte-identical state.
Outboxes were empty before and after: **nonempty queue durability through
power loss is not claimed** by these two cycles.

Post-cycle real maneuvers passed: Brake18:22:05→18:22:21 (15.16s),
Tire18:23:18→18:23:33 (14.79s). At18:24:16UTC the backend confirms new
assessments, Brake2→4 and Tire1→2, all assessment IDs unique, old history
retained. Both function inputs report RECEIVING, delivery queues0, advisory
CONFIRMED with fresh Gateway APPLIED. At18:24:19 the actual controller is
fresh/unheld, SAFE_STOP, speed0 and brake1.0; no Autopilot is enabled. Presenter
shows both recommendations, Online, exact installed117/92/49 and no pending
updates. No transient product mutation or policy rollback was needed.

## Local regression / remaining boundaries

Boot recovery20/20 and Presenter41/41 pass (61 total); socket tests ran with
the needed local permission. Documentation navigation check passes261 Markdown
documents; tracked confidential-input guard passes. A first docs check exposed
only a missing navigation link, then corrected; one confidential-check command
omitted its required mode and was corrected to `--tracked`.

These host fixes require no Factory rebuild. The image is not promoted to the
accepted baseline by a narrow ignition pass. Fresh serial all-version E2E,
externalOFF soak beyond the linked five-minute check, cold boot while explicitly
externalOFF and nonempty queue persistence are separate gates. Historical
VDP109 crash attribution remains unchanged. The reused-release Presenter
profile binding observation remains open; no unrelated UI behavior was changed.
