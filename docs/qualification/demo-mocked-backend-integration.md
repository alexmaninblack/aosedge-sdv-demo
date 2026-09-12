<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Explicit mocked service data and real backend integration

Status: implementation authorized by the user on 11 September 2026, after
the service replacement proof. This does not close authenticated KUKSA or
vehicle/advisory acceptance in the [delivery plan](../planning/active/demo-studio-delivery-plan.md).

- Existing `democtl service prepare` gains an explicit mocked-data mode,
  mutually exclusive with the inert no-telemetry mode and requiring the
  temporary permission-free package. Normal authentication remains unchanged.
- Only current Test is eligible. Native service identity and the allocated
  package version remain real; no invented Unit, Subject, token or Cloud state.
- Brake uses deterministic synthetic samples with its existing product engine;
  Tire uses explicitly synthetic normalized features while its production
  feature extraction is still unqualified. Neither opens KUKSA nor sends a
  Gateway advisory request or fabricates an applied advisory acknowledgement.
- Service mock state/outboxes use a dedicated `demo-mock` subdirectory under
  their owned storage. Normal queues and model state remain untouched.
- Real HTTP delivery uses `/api/v1/{team}/demo-mock/messages` and the explicit
  `X-Aos-Demo-Source: MOCK` marker. Existing payload validation, durable storage,
  content binding and retry acknowledgements remain in use.
- Backends keep mock records in a separate database inside their owned volume.
  Normal product queries never return them. Mock reads always identify
  `source: DEMO_MOCK` and `vehicleTelemetry: false`; access remains scoped to
  the current Test. Private cleanup must account for both owned databases.
- Build, activation, publication and observation are Demo Control operations.
  No external fixture uploader or alternate service launcher is introduced.

Required proof: two real service-to-backend deliveries, native identity/version
correlation, duplicate receipt stability, retry after temporary backend loss,
isolation from ordinary product records, and visibly synthetic presentation.
Mock generation is not evidence of sensor acquisition, KUKSA authorization,
production feature extraction or in-vehicle recommendations.

## Execution checkpoint — 11 September 2026, 22:08 UTC

Latest result: the [Factory .32 integration test](#factory-32-integration-test)
below supersedes the older pending/recovery observations for the current Test.

| Boundary | Evidence | Result |
| --- | --- | --- |
| Brake product | Source `438cac887b7ef248f81b4dbf69285c89d903101d`; actual ARM64 v3 export and seven native tests | Passed |
| Tire product | Source `fc81a37dbb68425bf659f7bbd683898d64966792`; actual ARM64 v1 export and four native tests | Passed |
| Brake backend | Source `da7ee6b12fbc7c4a85fcd0c3d75566982e7f8f34`; 48 backend tests | Passed; new image activated through Demo Control, existing volume retained |
| Tire backend | Source `76a5cd2e8f40da842f16d6ad6c955b5472f4594b`; 14 backend tests | Passed; new image activated through Demo Control, existing volume retained |
| Product-equivalent HTTP fixtures | Actual native C++ output → real backend HTTP → durable SQLite; duplicate returns the same receipt after backend restart; ordinary queries exclude mock records; exact private cleanup | Passed for both teams in isolated fixtures, not the live VM |
| Brake publication | 7.0.0 / v3; Deployment Bundle `bb56e411-90fc-4a47-a5a1-dd142f90a040` | Accepted once; Cloud READY |
| Tire publication | 6.0.0 / v1; Deployment Bundle `c2767b6d-b1ee-4436-b9fa-d3e0cc78d944` | Accepted once; Cloud READY |
| Current native service delivery | Test Cloud Unit `2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, system UID `d53d05cd4c4649c9a896534b23b88273` | Brake 6.0.0 Active / 7.0.0 pending; Tire 5.0.0 Active / 6.0.0 pending |
| Live backend records | Both owned backends are ready, with current Test context | Zero mock records; real VM delivery is **not yet proven** |

The later Brake commit `76d80e9` changes only its Python export-test fixture
to expect the seventh native test; it does not alter the published binary.

### Cloud observation contradiction

The exact Unit API reports Offline since `2026-09-11T21:17:11+00:00`, while
native CM continues exchanging websocket traffic, acknowledging messages and
sending monitoring. Cloud's monitoring API returned an exact-Test sample at
`2026-09-11T22:07:29.661650+00:00` (17 DMIPS, RAM 349839360 bytes).
Guest/host DNS resolve, the explicit connectivity filter is ON, and both
native managers remain active with unchanged PIDs and no additional restart.

This proves a disagreement between Cloud's Unit/connectivity view and its
accepted telemetry transport. It does **not** identify the internal dispatcher
fault. No forced Online state, repeat upload, Subject reassignment, VM/manager
restart, reprovisioning or Production change is used to conceal the disagreement.
Retain the exact packages and diagnostic VM until authoritative reconciliation.
Bounded CM diagnostics expose allowlisted stage labels, not message payloads.

### Remaining live gate and next steps

1. Observe the existing publications reaching the exact native versions; do
   not prepare more releases merely to retry delivery.
2. Through `democtl backend inspect`, correlate real receipts with Test UID,
   service ID, retained Subject, native instance and installed package version.
3. Exercise one scoped backend outage/recovery and durable retry, preserving
   the peer backend and both service identities. Do not equate local fixture
   restart evidence with this VM proof.
4. Confirm the visible team dashboard labels synthetic evidence and separates
   Cloud runtime, backend readiness and records.
5. Continue the accepted P5–P7 service/UI work; leave KUKSA, actual vehicle data,
   Tire production feature extraction and advisory acceptance explicitly open.
   No Factory rebuild or full cleanup before these gates are resolved.

## Pending-delivery investigation — 12 September 2026, 01:07 UTC

The failure is localized **before a new desired state is accepted by CM**, not
inside an ongoing SM replacement. Its internal Cloud cause remains unproven.
All times below are UTC. Read-only observations used the existing Demo Control
commands `unit cloud-status test`, `unit monitoring test`, `component logs test`
and `component cm-status test`; the latter gained bounded diagnostic fields.

| Evidence | Observation |
| --- | --- |
| CM process | PID 183405, active/success, zero restarts; journal begins at its initialization at 2026-09-11 21:08:42.358910 |
| Journal coverage | 6,598 records through 2026-09-12 01:03:43.206145; 30,000-record cap not reached |
| Last outgoing `unitStatus` log | 2026-09-11 21:15:36.770213 |
| Last incoming `desiredStatus` log | 2026-09-11 21:15:37.591460; eight received and eight handler entries since current CM initialization, none logged after this point |
| Persisted CM database | `updatemanager.updateState = none`; desired items Tire 5.0.0, Brake 6.0.0 and VDP 18.0.0; each service requests one instance |
| Last CM message-handling error in this process | 2026-09-11 21:09:12.439064, before subsequent successful service replacements; not evidence of rejection of the later mock releases |
| Cloud Unit state | Provisioned, Offline since 2026-09-11 21:17:11; exact Unit/UID unchanged |
| New release publication | Brake 7.0.0 at 21:52:48; Tire 6.0.0 at 21:53:21, both later than the last logged desired status |
| Exact service assignments | Existing respective Subjects retained; Cloud reports ready package versions and `pending_service_version_status = to be installed`; installed versions remain Brake 6.0.0 and Tire 5.0.0 |
| Current connection | CM continues receiving WebSocket frames, replying with PONG, sending monitoring and receiving ACK; no reconnect event after initial establishment in the captured process history |
| Independent Cloud receipt | API sample for this exact system UID at 2026-09-12 01:06:35.019592: CPU 28 DMIPS, RAM 365072384 bytes, while Unit API still says Offline |

### Meaning and limits of the evidence

- The Cloud API's `to be installed` is not proof that CM reached its local
  `Pending` phase. The stored phase is `none`, with the old service versions.
  The documented update lifecycle begins with delivery of a desired state;
  no accepted target containing Brake 7 / Tire 6 is present here.
- Full wire bodies cannot be reconstructed from this journal. The pinned native
  logger has a default 512-character line buffer; longer protocol entries are
  truncated. The diagnostics retain the visible message type and timestamp and
  explicitly mark the body incomplete. This is a logging limit, not proof that
  malformed JSON was transmitted. Existing `cloudMessageLog` is disabled and
  was not enabled as part of the diagnosis.
- The running source copies received PING payloads into PONG frames. The
  continued ACKs and Cloud's new monitoring sample rule out a completely dead
  transport; ACK alone is not proof of successful desired-state dispatch.
- In the pinned `UnitStatusHandler`, full status is sent on connection/update
  completion; changed status starts a one-shot coalescing timer. Its timeout
  is not a periodic Online heartbeat. No published requirement found in the
  inspected documentation establishes a mandatory 90-second UnitStatus
  heartbeat. The roughly 94-second gap between the last status and Offline is
  a correlation for server-side investigation, **not a proven timeout cause**.
- Nothing here justifies another service package, Subject reassignment, Safe
  Stop, or an SM restart to resolve the missing new desired state. These checks
  do not identify which Cloud service or session-state transition is faulty.

### Exact server-side trace needed

For Unit `2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, system UID
`d53d05cd4c4649c9a896534b23b88273`, reconcile:

1. Why did connectivity transition to Offline at 21:17:11 while this session
   continued to send acknowledged traffic and accepted monitoring?
2. Did the dispatcher generate a new desired state after the existing ready
   versions were assigned? If not, record its actual eligibility/block reason.
3. If generated, identify its transaction/session route, send attempt and
   disposition; compare it with the CM receive journal after 21:15:37.
4. Check whether a stale disconnect/session event or a status-consumer failure
   overwrote the current connection record. These are candidates to verify,
   not established defects.

Use deployment IDs `bb56e411-90fc-4a47-a5a1-dd142f90a040` (Brake) and
`c2767b6d-b1ee-4436-b9fa-d3e0cc78d944` (Tire), and service version IDs
`49dbaddb-1df5-443f-b6a1-c1074fd9015a` / `4421337f-1862-41cd-9631-0d120974887f`.
The OEM read endpoints and guest logs available here do not expose the Cloud
dispatcher/session-manager server logs. No forced reconnect, VM restart,
new release, assignment change or Production operation was performed.

Diagnostic verification: 27 component-delivery tests passed, including
read-only database access, truncated-message handling, secret redaction and
no guest command for a stopped CM. This is not a successful mock-release E2E.

References checked:

- [Update flow and persisted desired state](https://docs.aosedge.tech/docs/aos-core/deployment-flows/update-flow-overview).
- [Cloud communication, ACK and optional wire logging](https://docs.aosedge.tech/docs/aos-core/architecture/communication-manager/cloud-communication).
- [Documented Unit connectivity states](https://docs.aosedge.tech/docs/how-to/advanced-device-operation/monitor-device).
- Pinned Core `da50b60b7d72208bf17ad51250d24dbc727bc679`,
  `src/cm/communication/communication.cpp` (`ReceiveFrames`, `HandleReceivedMessage`)
  and `src/cm/database/database.cpp` (`GetDesiredStatus`, `GetUpdateState`).
- Pinned CM shared-library source `0b82a6bf`,
  `src/core/cm/updatemanager/unitstatushandler.cpp` (`OnConnect`, `StartTimer`),
  and `src/core/common/tools/config.hpp` (`AOS_CONFIG_LOG_LINE_LEN`).

## User-authorized VM restart — 12 September 2026, 01:26 UTC

The user explicitly requested one VM restart to test Cloud Online recovery.
`vm stop test` initially returned `CURRENT_VEHICLE_REQUIRES_PARK_OR_DETACH`
without stopping the VM. `simulation stop --target test` then detached the
selected role (Controller absent; physical stop not observed), followed by
`vm stop test` and `vm start test`. Graceful shutdown took 3.97 seconds;
startup took 25.95 seconds and confirmed guest SSH/DNS and the initialized
Test role. The same overlay, Unit UUID and system UID were retained; Production
was not changed. The simulator remains stopped/detached.

- Cloud changed to **Online at 01:24:46** and remained Online at the final
  read, **01:26:35.616323**.
- CM received the existing Brake **7.0.0** / Tire **6.0.0** desired state,
  persisted it, and completed its update state machine. No upload or Subject
  reassignment was necessary to resume delivery.
- Cloud changed `pending_service_version_status` to `installed`, although the
  installed-version fields still show 6.0.0 / 5.0.0 and instance detail is
  unavailable. This does not prove application startup.
- Native logs report **both new service instances failed** with
  `no nodes with with service resources (balancer.cpp:176)`. Native container
  inspection returns an empty list. The effective resource configuration is
  again `/etc/aos/resources.cfg`, with only `kuksa` / `kuksa-auth-client` among
  the inspected declarations; Brake/Tire public metadata files are absent.
- As warned before reboot, `/run` activation state did not survive. CM is now
  `/usr/bin/aos_cm_app`, SHA
  `8432c0ca62b3b7bebf0e20f3ae3f82d412429be44fadcd00d914dbf1170f48bc`,
  PID 1018; SM PID 1077. The previous transient corrected managers and runtime
  resource activation were **not reapplied** by this restart experiment.
- Six `systemID mismatch` message-handling errors and two exhausted-message
  retry records also appear in the new CM journal. They are recorded, not
  conflated with proof of the earlier missing desired-state cause.

Conclusion: reconnecting through a full VM restart restored Online and new
desired-state delivery. It does not isolate the original Cloud/session failure,
and the post-reboot service startup is not a test of the previous corrected
runtime. Resume service/backend E2E only after the accepted runtime activation
is restored through its explicitly authorized Demo Control operations. Do not
run the backend outage proof while no new service instance is running.

## Presenter and adapter verification — 12 September 2026

The existing Studio build now presents Cloud-installed service versions on
the architecture map and reads per-Subject instance details. Entering either
team view refreshes Cloud state and its own backend observation; a missing
detail is incomplete evidence, not an absent service. Backend transport stays
inside the fixed same-origin read adapter. The current live read showed both
backends Ready and zero isolated mock records; no fixture was injected into
the live stores.

Verification: 99 UI unit tests, four isolated browser scenarios, production UI
build, 64 backend/retirement adapter tests, 20 package tests (one optional SDK
test skipped), nine Presenter HTTP tests, six Cloud-reader tests and 25 bounded
component-diagnostic tests passed. Both backend suites were rerun successfully
(Brake 48, Tire 14); documentation navigation passed. Browser scenarios prove
clickable synthetic record details and no guest/mutation calls, not VM delivery.

Only the idle Presenter process was refreshed with `democtl ui stop/serve`.
VM, CM, SM, Cloud assignments and backend processes were not restarted by this
UI refresh. UI is available on the established loopback port 18080. The native
left-hand workspace was not restyled or automatically restarted. Service
publication/assignment controls in Studio and the full operator E2E remain
later plan gates; this increment exposes backend observations, not simulated
success or a completed service workflow.

## Authorized runtime restoration — 12 September 2026

The user authorized restoring the proven transient runtime, debugging remaining
failures and evaluating a new immutable image with the qualified CM/SM changes.
The same .31 Test Unit, overlay, service assignments and VDP 18.0.0 were retained.
Production was untouched. No new service release was uploaded.

1. `component sm-apply test` restored the qualified teardown SM directly over
   the exact rebooted factory binary; `component cm-apply test` restored CM.
2. `service runtime-activate test` restored both team resource declarations and
   cold/warm public-input hooks. The VM reboot qualification remains open.
3. CM had already processed the desired services while their resources were
   absent. A single explicit `component cm-apply test --restart-cm` after input
   activation placed Tire 6.0.0 and attempted Brake 7.0.0.
4. Tire became Cloud/native **active** and delivered real VM-originated records
   to the isolated mock endpoint. At 01:45:14 UTC the backend had two function
   statuses, two assessments and one band-change record, correlated with native
   instance `b14e8bca-b1a3-30a0-b44c-d972263deee6`, the existing Tire Subject,
   service 6.0.0 and the exact Test system UID. `source=DEMO_MOCK`,
   `vehicleTelemetry=false`; this is not a KUKSA or driver-advisory proof.
5. Brake's first preparation failed to find an image/config blob
   (`imagemanager.cpp:304`). Its next same-version request attempted runtime
   start without creating a network and failed at `networkmanager.cpp:252`.
   The journal shows Tire network creation but no Brake network creation
   between these two Brake failures.
6. One `service runtime-activate test --restart-sm` re-entered native preparation.
   Brake then failed allocation with `network stub not available
   (smclient.cpp:350)` during SM startup, before the network subscription was
   ready. Tire retained its allocation and restarted successfully. No further
   restart-only loop, database edit or assignment reset was used.

The pinned SM `Launcher::PrepareInstances` retains `InstanceData` after a config
or network preparation failure, but its existing-instance branch resets the
state and skips preparation on the next identical request. This explains why a
temporary prerequisite failure becomes a persistent missing-network failure.
The fix candidate retries preparation for a **failed same-identity service**;
it preserves component behavior and the prior different-version failed-teardown
guard. Tests cover missing config, temporary network allocation failure and a
persistent allocation failure that must never launch a runtime.

Platform candidate source: `f4ba4a8903f179461a6d8e831c33168fff1dc352`.
Qualification uses `democtl component sm-build test` and a separate
`runtime-proofs/sm-service-prepare-recovery` artifact; prior qualified artifacts
are not overwritten. Compilation, live application and final recovery results
must be recorded below before this candidate is described as qualified.

Image decision: a new immutable image must include the accepted manager fixes,
runtime resource declarations and public-input cold-start ordering together.
A manager-only rebuild would still lose the transient resources. Do not build
or qualify that image until the current failed-service recovery is demonstrated.

<a id="runtime-recovery-2026-09-12"></a>

### Recovery result — 12 September 2026, 02:05 UTC

The corrected test fixture targets the config read after the separate TTL
lookup. Production SM source was unchanged after its successful compile;
`component sm-test test` verified byte identity before rebuilding tests only.
All 23 launcher, 13 container, 12 bridge/namespace and 29 VDP/Safe Stop tests
passed. Final source is `b66ab25979e53b997005c0519eda9c869b111d8b` and SM SHA-256
is `ae36ada2815700d751549404d5fb93f5a9e1f22890507c14da7f2df1a0c30299`.
Builder stopped cleanly after qualification.

`component sm-apply test` applied the fix once, retaining resource hooks and
VDP records. After startup initially lacked the CM network stub, one explicit
`component cm-apply test --restart-cm` obtained the **same** existing desired
state while SM remained running. This time native SM completed Brake's failed
preparation instead of skipping it. No package, version, Subject assignment,
native database or VM identity was changed.

- Cloud Unit is **Online**. Brake **7.0.0** and Tire **6.0.0** both have
  installed-version fields and native instance `run_state=active`, no pending
  version and no instance error.
- Guest inspection independently confirms both bootstrap processes alive,
  with native runtime IDs `7cf522e4-ff3f-3b8c-b02e-b09458403b5a` (Brake) and
  `b14e8bca-b1a3-30a0-b44c-d972263deee6` (Tire).
- Brake backend received its first VM-originated event and assessment at
  **02:03:56 UTC**, package 7.0.0, matching its exact native service/Subject/
  instance and Test system UID. Tire continued delivery at **02:04:49 UTC**;
  its observed counts were 42 function statuses, 40 assessments and one band
  change. These are isolated synthetic product inputs over the real delivery
  path, never vehicle telemetry or driver advisory.
- VDP **18.0.0** remains active with slot/process agreement and zero reported
  automatic restarts. SM PID 2326 and CM PID 2469 are active with zero reported
  automatic restarts. Explicit proof restarts above are recorded separately.
- 78 targeted Demo Control tests passed. Production was not changed; the
  simulator remains stopped/detached following the earlier requested reboot.
- Repeating `component sm-apply test` returned `noOp=true` with unchanged
  PID 2326. SELinux remained enforcing; the complete kernel audit window since
  this SM start contained zero AVC denials (78 journal entries scanned).

The VM-to-backend mock-delivery boundary is now proven for both services.
Backend outage/retry and complete operator E2E are still separate pending
gates. The original Cloud Offline/dispatcher incident is not root-caused by
this local SM fix. A clean image/reboot remains unqualified; do not claim that
transient runtime restoration makes .31 a corrected factory image.

<a id="factory-32-integration-test"></a>

## Factory .32 integration test — 12 September 2026, 05:02 UTC

The user authorized preparing and assigning both retained services to the new
Test, then verifying native containers and real mock-backend delivery. Source
baseline: Solution `e3ad83f`; immutable Platform source `04fc8270c55ff5c35f1e98af534a5efccb035464`.
Current Test Unit is `923b9820-999b-41bb-91db-b2a2c469e743`, system UID
`5aa1f8e4a1114467a6ccfb269c62a7a8`. The preceding unchanged-CM delivery control
had already restored VDP 18.0.0; this run performs no additional manager restart.

The exact Demo Control sequence was:

1. `service runtime-prepare test`: created the two public metadata/trust inputs
   from native identity and committed VDP 18.0.0; process verification passed.
   Native resource declarations were already packaged in .32. No activation,
   SM restart or alternative container launcher was needed.
2. `service assign 3bc71fa0-aae5-4363-8298-8d06501c3132 --target test`:
   reused Brake Subject `ede5ae8b-9796-4bea-88d1-d2dfcab24725` and its existing
   service membership; bound the current Test. Brake 7.0.0 became Active.
3. `service assign d98957a1-83c2-4d14-a6fb-4e6a6ad27c77 --target test`:
   reused Tire Subject `e6699b5d-b243-4bfe-8e0c-b905fcfa14df` and its existing
   service membership; bound the current Test. Tire 6.0.0 became Active.
4. `service runtime-inspect test`, `unit cloud-status test`, both
   `backend inspect` commands and component/SM status reads established the
   results below. One backend observation attempted while assignment held the
   writer lock returned `CURRENT_RUN_BUSY` before observation; it was read
   after assignment completed. No assignment was replayed.

| Boundary | Observed result |
| --- | --- |
| Cloud, 05:00:41 UTC | Test Online; Brake 7.0.0 and Tire 6.0.0 each have one Active instance, installed status, no pending successor and no reported instance error |
| Native containers | Both bootstrap processes alive; Brake runtime `7cf522e4-ff3f-3b8c-b02e-b09458403b5a`, Tire runtime `b14e8bca-b1a3-30a0-b44c-d972263deee6`; native item/Subject/index/instance inputs present |
| Brake backend | First current-Test event/assessment received at 04:59:47 UTC; by 05:01:54 UTC, five assessments and one event; latest receipt 05:01:47.700 UTC |
| Tire backend | First current-Test status/assessment/event received at 05:00:19 UTC; by 05:01:54 UTC, four statuses, four assessments and one band-change event; latest receipt 05:01:50.135 UTC |
| Identity correlation | Both real HTTP backend records match the current Test UID, respective retained Subject, service UUID/version and observed native instance ID |
| Unchanged runtime | SM PID 1875, active/success, zero automatic restarts; VDP 18.0.0 PID 6899, slot a/process agreement, READY/LIVE, 23 read paths, zero restarts |
| Security observation | SELinux enforcing; complete available kernel window since SM startup: 402 entries, zero AVC denials |

All backend records are `DEMO_MOCK` with `vehicleTelemetry=false`. Tire's
`SERVICE_ACCESS_DENIED` function status is the expected permission-free mode,
not evidence that this service failed to start. Native KUKSA authorization,
actual vehicle telemetry and advisory functionality remain unqualified.

This proves fresh service assignment, native launch and continuing delivery
to both real backends on the immutable .32 runtime **after explicit warm input
preparation**. It is not proof of automatic input refresh, retained-assignment
reboot recovery, version replacement on .32 or backend outage/retry. Those
remain separate gates. No build, upload, validation approval, VM/CM/SM/backend
restart, cleanup, private-data export or Production mutation occurred in this
integration run. Existing runtime and backend storage are preserved. No source
code changed, so no additional compile/unit suite was run for this live test.
