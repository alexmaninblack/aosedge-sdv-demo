<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 live installed journey

- Date: 2026-10-03
- Updated: 2026-10-04
- Status: Kit 028 scripted installed sequence passed all 98 checks; native and release acceptance remain open. Earlier failures are retained below.
- Initial candidate: Runtime Kit 025, signed Setup 039, Factory .39
- Diagnostic candidate: Runtime Kit 026, signed Setup 040, Factory .40; installed and exercised, subsequently retired
- New installed E2E candidate: Runtime Kit 028, signed Setup 042, Factory .41; corrected VM/host binding and its own scripted sequence passed. Kit 027 installed but was rejected before Test creation.
- Host: dedicated M1 Pro, 16 GiB RAM, internal installation, macOS 27.0.1
- Scope: staging only, existing authorized OEM and SP accounts
- Parent: [Scripted journey](scripted-journey-2026-10-02.md)

## Access and execution boundary

The development SSD was reconnected and its recorded volume identity verified.
Pinned SSH, the M1 console session, installed selection, Docker API and staging
access were available. The journey uses the installed private Python, signed
Setup bridge and normal Demo Control owners. It does not patch installed
package bytes, inject telemetry or import development product modules on M1.
Docker Engine is reused and is not stopped during demo cleanup.

## Initial sequence and measurements

| Operation | Elapsed | Observed result |
| --- | --- | --- |
| Create Controller | 191.29 s | Completed, including native one-use VM access |
| Start controller | 5.81 s | Completed |
| Provision | 44.07 s | Test Online in staging |
| Start packaged CARLA | 102.64 s | Completed |
| Connect Test | 12.03 s | Completed |
| VDP 128 V1 prepare | 8.01 s | Prepared |
| VDP 128 V1 publish | 18.07 s | Accepted |
| VDP installed readiness | 14.89 s | Slot A, 128.0.0, LIVE, seven paths, zero restarts |
| Brake 104 V1 prepare | 6.01 s | Prepared |
| Brake 104 V1 publish | 20.13 s | Accepted; not yet proof of READY |

No Brake delivery or runtime pass is inferred from publication. Subsequent
read-only Cloud observation confirmed the exact Brake 104 deployment READY.

## Test tooling corrections

The initial runner exposed several ordering/evidence defects, not demonstrated
vehicle-service regressions:

- Wait for bounded background layout/recovery ownership after foreground
  connection, without redispatching the connection.
- Reconcile completed shutdown by reading processes, listeners and backend
  state; never repeat a stop merely because its final response was lost.
- Resolve the first service identity from publication, not preparation.
- Observe the exact Cloud publication READY before assignment or installed
  readiness. An accepted upload alone does not populate the publication
  observation required by the assignment owner.
- Carry terminal product error codes into sanitized test evidence.
- Select explicitly pinned, previously chosen Subject references before
  Create Controller. Cloud account readiness alone does not perform selection.

The old attempts remain append-only. Changes to the runner retain the source
revision warning; prior passes are not silently relabelled as a clean new run.

## Initial Test retirement

The initial Test was `452496f5-d284-4922-a765-7c5eba59bb58`, Cloud Unit
`d229013a-0419-48df-a434-d06baf4b4cd4`. Assignment reached the known
`SERVICE_SUBJECT_UNRECORDED_LABEL_COLLISION`: the new instance had no selected
reference for an existing unbound Subject. Its exact no-POST placeholder,
empty operation steps and complete empty Unit service inventory confirmed
that no service assignment occurred.

Normal installed Finish retired this Test. The first Finish stopped during
read-only Cloud inventory with `UNIT_CLOUD_UNAVAILABLE_URLError`. Its journal
had no deprovision intent, and fresh Cloud reads still showed provisioned/
Offline with no services. A bounded continuation completed retirement and
confirmed the automotive journal absent. The working VM and this run's backend
data were removed through their owners, not raw filesystem deletion. Factory,
published releases, credentials, Subject objects, sources and Production remain.

The replacement attempt explicitly pins the same public Subject references
already selected in the prior M1 instance. Fresh authority and zero-recipient
checks are still mandatory; there is no automatic adoption by label.

## Replacement sequence and confirmed guest defect

The replacement Test is `b90064dc-d20e-450c-a175-705d82d18d4d`. Explicit
Subject selection passed before Create Controller. The installed package,
Factory, credentials and service source bytes remain unchanged.

| Operation | Elapsed | Observed result |
| --- | --- | --- |
| Create Controller | 96.55 s | Completed |
| Start controller | 5.82 s | Completed |
| Provision | 36.01 s | Completed |
| Start packaged CARLA | 60.09 s | Completed |
| Connect Test | 10.03 s | Completed |
| VDP 129 V1 publish / readiness | 17.91 / 9.28 s | Installed and ready |
| Brake 105 V1 publish / assignment / readiness | 22.03 / 26.03 / 3.79 s | Running |
| Brake V1 maneuver / backend product | 28.67 / 0.81 s | New complete product received |
| VDP 130 V2 publish / readiness | 16.02 / 8.90 s | Installed and ready |
| Brake 106 V2 publish / Cloud READY | 22.05 / 9.36 s | Artifact accepted; runtime not proved |
| Brake V2 running gate | 182.78 s | Failed; instance network could not start |

The physical Safe Stop projection initially depended on a V2 model file even
while only V1 was installed. Source inspection confirmed V1 has events, not that
model. The read-only tooling now separates physical state from strict two-service
model collection; the latter remains mandatory for offline/ignition checks.
The combined journey, remote and installed-scenario suite passes 78 tests.

### AosCore VLAN allocation failure

At **10:39:25 UTC (12:39:25 Berlin)** CM allocated VLAN **4095** for the SP
network while replacing Brake 105 with 106. SM logged the same value, then
`failed to add link: Input data out of range (networkmanager.cpp:1963)`.
The failed runtime is `de48e899-3da2-3d1e-8bab-ce6079169fe1`. VDP 130, CM,
SM and IAM stayed active; no Brake process remained. This is a guest network
allocator defect, not slow Cloud convergence or a Brake algorithm failure.

Cloud still projected version 105 as installed and 106 as pending/installed,
with instance details UNKNOWN/NOT_REPORTED. Therefore a successful artifact
upload or an installed pending artifact cannot count as a running-service pass.
The lack of an actionable runtime error in this projection is a separate
observability gap; it has not been corrected by the allocator patch.

An isolated network namespace on the same guest accepted VLAN 4094 and rejected
4095 with `8021q: Invalid VLAN id`. It was deleted and no live interface changed.
Two preliminary proof commands were unsupported by this image (`unshare` absent,
dummy interface unavailable); those are tooling limitations, not extra product
faults. The successful proof used the already supported veth interface.

The retained production build source is exactly AosCore
`9d613a46df3c7f550062e2f19ae3406c57715694`. Its allocator permits values 0–4095;
its collision `continue` also skips only the inner loop. A private source copy,
using the original target toolchain and sysroot, reproduced four failing boundary/
collision tests. The candidate excludes reserved values and retries collisions:
**31/31 native CM network tests pass**, including the 27 pre-existing tests.
The ARM64 CM application also compiles. No live CM replacement or Factory rebuild
is implied by this result.

The source correction is recipe patch
`0008-allocate-valid-unused-vlan-ids.patch` in the vehicle-platform repository.
It prevents invalid new allocations; it deliberately does not rewrite existing
CM/SM database rows. The current failing Test and Factory .39 remain preserved.
The candidate binary is 5,664,496 bytes, SHA-256
`26d1c5aa48ea9986f6263bfaa448a5faf3bf532f15f4999aa1ab9cd76a074483`.
Private Builder evidence is `/home/yocto/r61-build/cm-vlan-proof-20261003`.

## Factory .40 corrective candidate

The failed Test was shut down through the installed owner at 11:10:38 UTC
(25.30 seconds); zero owned listeners/processes remained. Persistent failure
state and Docker Engine were preserved. No live CM substitution or database
rewrite was performed.

Platform source correction is committed locally at
`9adee816b4f942ceafb4d30da4adba318352bf59`. The clean isolated build-tool
checkpoint is `a57bb215fe6ef2ca2e62146327f0c3ee704bd8f8`; neither was pushed.
The ordinary guarded warm/offline owner built Factory .40 once after those
checkpoints. An earlier preflight refused uncommitted build tools before any
compilation; the gate was satisfied, not bypassed.

Mandatory native gates pass **466 tests**, with **2 skipped and 2 disabled**;
additional KAC/provider/verifier gates exit zero. Compile, package QA and image
QA pass. Three inherited build-path warnings remain; no QA bypass was added.
The six-partition raw image is 6,997,147,648 bytes, SHA-256
`13fc1b3c9893df80261228783d345ea830658d3b4822993b5ed5a7e5b3a2f30f`.
Host transfer matched and the Builder stopped cleanly.

The separate `workspace/checkpoints/factory-40-candidate.json` pins this
engineering candidate. Historical `demo-v1.1` and Factory .39 are unchanged.
Vehicle input manifest SHA-256 is
`4333858ca44528ff815227ed400cced091513e78ac6f85675deececd4b2a9360`.
Kit026 is assembled from these inputs and the unchanged, independently pinned
Kit025 host/VM/Cloud/backend groups. Its application manifest SHA-256 is
`f05444400262473e039197bb3b308f511e71604d2f96c402a55db4001db883ad`.
Candidate construction is not installed/native/live acceptance.

The first packaging attempt rejected an obsolete development-side input
catalogue before creating output. The verified Kit025 groups matched all four
locks; no version/hash validation was relaxed. The journey explicitly accepts
only .39 and .40 selectors and still requires fresh candidate-bound evidence.
Its 49 unit tests pass.

Two offline boot observations report SELinux Enforcing, IAM-provision active,
CM/SM/IAM/VDP inactive as expected before provisioning, success results and zero
automatic restarts. Provision marker and private provisioning PIN are absent.
Boot IDs differ; CM bytes are stable at SHA-256
`107f9c6fe32517b492b3329da8acab94306cb97a912c605ba51e39953630f035`.
The disposable VM stopped cleanly. The initial evidence script assumed an
incorrect binary pathname; it failed after key enrollment and stopped the VM.
The corrected read resolves the actual unit ExecStart on the same overlay;
the image was not rebuilt and no guest runtime configuration changed.
This bounded smoke is not a blanket zero-AVC or full provisioned-runtime claim.

The exact failed Test `b90064dc-d20e-450c-a175-705d82d18d4d`, Cloud Unit
`2c5290e4-c129-4dbd-a90f-cc786147b268`, was then retired through the installed
normal Finish owner. All lifecycle steps completed and the automotive journal
is absent. Its working VM and backend run data are irrecoverably removed;
published releases, Factory images, private credentials and compact failure
evidence remain. No Production object was targeted.

The affected Factory, distribution, Setup and harness regression set passes
149 tests. Setup040 protocol self-test and stable Apple Development signing
pass; executable SHA-256 is
`562347904e16a8700b9bcabbdd5c2620508fece1ec8bda6fee7400b714251e5e`.
Old Kit025 media was ejected after verifying no Setup/runtime users; Docker
Engine remains running.

An exact Kit025/026 manifest comparison shows only three application export
changes: Factory build selection, mandatory gate definitions and the vehicle
input lock. Host-runtime, VM-runtime, Cloud-runtime and backend-input manifest
pins are identical. The diagnostic Test retirement took 55.49 seconds.

The complete Kit026/Setup040 DMG was built and passed `hdiutil verify`. It
contains 17,686 files and 35,456,327,298 logical bytes; the compressed image is
14,141,620,842 bytes, SHA-256
`5787a517df49fe39da5a7a89c4b7646fbf63df894c1832d8c9902935a6568b0b`.
The temporary media staging tree was removed after successful construction.
This is Apple Development-signed private engineering media, not a notarized
public release.

Pinned-SSH delivery of that single DMG to M1 took 121.48 seconds. Its destination
SHA-256 matches. New installation targets are the empty `AosEdge SDV Kit026`
package store and `SDV-Kit026` state directory on the M1 internal disk. Old
installation files remain unchanged. The existing Screen Sharing connection
showed a frozen lock-screen frame even though SSH remained available. Normal
disconnect/reconnect restored the current desktop without entering a macOS
password or changing authentication or lock-screen settings. The initial
request for operator unlock was no longer necessary.

Signed Setup completed preflight in 5.89 seconds, fresh installation in 123.47
seconds and selection/preparation in 36.22 seconds. No operator data was copied
into the new instance. Candidate-bound installed selection, existing Docker
Engine, both backend image identities, authorized Cloud certificate references,
staging account access and both explicitly selected Subject references pass.
The separate Presenter launch smoke passes in 13.94 seconds and its normal
cleanup passes in 10.71 seconds. These preparatory observations create no new
Test or published release. The full remaining journey then resumes.

## Factory 40 live progress

The fresh Test is `4f77ccb2-eb23-461b-88c8-15a1c277ac74`. Creation took
104.53 seconds, Start 5.80 seconds, Provision 42.00 seconds, packaged CARLA
startup 96.36 seconds and connection 9.98 seconds. The native VM dialog used
the authorized password once without storing it in Keychain.

| Installed release | Publish | Readiness | Functional result |
| --- | --- | --- | --- |
| VDP 131 V1 | 17.92 s | 8.35 s | Ready, correct slot, zero restarts |
| Brake 107 V1 | 21.95 s | 3.58 s after assignment | Complete new product after 26.36 s maneuver |
| VDP 132 V2 | 15.96 s | 9.66 s | Ready, correct slot, zero restarts |
| Brake 108 V2 | 19.98 s | 2.71 s | New product after 26.03 s maneuver |
| VDP 133 V3 | 17.98 s | 8.67 s | Ready, correct slot, zero restarts |
| Brake 109 V3 | 19.97 s | 3.67 s | New product after 26.33 s maneuver |

Versions were published serially; each VDP update followed observed physical
Safe Stop. Brake V2 now starts and delivers a new result, unlike the preserved
Factory .39 failure. This is a successful functional path, not a statistical
proof of every allocator outcome; boundary/collision tests provide that proof.

The Brake V3 advisory gate then timed out after 180.78 seconds. Diagnosis
classified this as a test criterion error: ten observed `APPLIED` facts from
Brake 109 referenced the valid persisted Brake 108 assessment. Accepted
D4-016.4 explicitly requires that activation and subsequent lease refresh
behavior. A separate new assessment from Brake 109 had already been received.
The old checker incorrectly demanded a decision for that new assessment.

Three regression tests reproduce the criterion/projection mismatch. The
corrected harness accepts only the pinned, valid V2 condition with correlated
`APPLIED` evidence from V3; unrelated, invalid and wrong-version evidence still
fails. All 52 journey unit tests pass. No service or immutable candidate bytes
changed, and passed publications are not replayed. The failed attempt and
source-revision review remain in the record. The first normal shutdown took
30.72 seconds and preserved the Test, Docker Engine and diagnostic state.

The corrected advisory gate passes in 0.88 seconds. Tire preparation and
publication complete in 7.95 and 20.15 seconds. Its subsequent read encountered
`CURRENT_RUN_BUSY` before acquiring the product journal lock. Source inspection
confirmed that `cloud_status` throws this before its network read; an optional
post-read receipt-cache collision is already handled by the product. The harness
now waits for idle ownership and retries only this known pre-read contention
within 20 seconds, preserving all other errors and identity checks. Tests cover
eventual success, deadline and immediate propagation of unrelated errors;
53 journey unit tests pass. Tire publication is not replayed.

The installed security projection at 12:33:49 UTC confirms Enforcing, active
IAM/CM/SM/VDP, zero automatic restarts, the pinned Factory40 CM binary and valid
VLAN 1443. The current-boot audit query returned 68 records without truncation:
11 denials in the previously classified auditctl/auditd socket, SSH directory
search and getty capability categories. No Aos-manager-specific denial appears
in that bounded observation. This is not an all-domain zero-AVC claim. See the
[original baseline comparison](factory-37-mainline-build-2026-09-23.md#classified-baseline-observations-not-a-zero-warning-claim).
The initial diagnostic used an unsupported/failing journal grep form; querying
the audit transport and filtering locally produced the evidence without changing
the guest or weakening policy.

Tire 54/V1 Cloud READY subsequently passes in 8.49 seconds, assignment in
26.02 seconds and runtime readiness in 3.79 seconds. Its real maneuver takes
29.09 seconds; a new `INSPECTION_RECOMMENDED` assessment is observed 0.78
seconds later, already accompanied by `APPLIED` evidence. The projection had
omitted Tire's contract-defined `content.assessmentId` (Brake uses
`content.decisionId`). The accepted v2 fixture reproduces that omission; the
minimal projection fix passes all 54 journey tests and the live read completes
without restarting services. Its 133.44-second measured gate includes diagnostic
and harness repair time; it is not Tire delivery latency. No advisory semantics,
telemetry or installed product bytes changed.

## Reset, offline recovery and ignition observations

Both independent Reset checks pass. Brake's request/confirmed clear took
3.92/8.31 seconds; Tire's took 3.90/8.37 seconds. The other service's model
projection and observed product history remained unchanged. Return to road
passes in 4.70 seconds.

External OFF took 4.31 seconds. Real Brake/Tire maneuvers while OFF took
26.19/28.81 seconds; both local models progressed while backend product IDs
stayed fixed. The 302.91-second sampled soak passes with the same boot and
identity, active managers and zero automatic restarts. Cloud OFFLINE is
observed. After ON (4.92 seconds), the delivery gate passes in 26.17 seconds:
queues are empty and all queued assessment IDs appear in their own backend.
Cloud ONLINE is then observed. This is bounded product-history evidence, not
an exhaustive database audit.

Ignition OFF completed in 4.20 seconds and ON in 36.05 seconds. VDP readiness
followed in 27.41 seconds. The boot ID changed while Unit/Node identity, both
models and prior result IDs survived; the controller returned to confirmed
stationary Safe Stop without automatic driving. Postboot security observations
again show Enforcing, the pinned CM binary, VLAN 1443, four active managers and
zero automatic restarts. The 48 audit denials in 95 audit-transport records
remain in the four previously classified baseline categories, predominantly
SSH directory search; there is no all-domain zero-AVC claim.

**Open functional failure:** the subsequent Brake maneuver completed in
26.25 seconds, but no new assessment arrived within the 180.78-second gate.
The model digest and product IDs remained unchanged and queues were empty;
advisory lease refreshes still reached the backend. Therefore ignition identity/
persistence recovery passes, but post-ignition Brake analytics does not yet pass.
Tire's post-ignition maneuver was not run. The runner closed owned processes
in 28.97 seconds and retained Test data and Docker Engine.

The completed initial sequence has 93 latest PASS, one FAIL and two NOT_RUN
main steps. A later attempt to read the exact previous boot journal reports it
unavailable; the journal is not silently treated as empty evidence. A scoped
second ignition experiment captures bounded application-event diagnostics
immediately after each maneuver, before ordinary shutdown. It does not replay
successful publications or overwrite the failed first experiment.

The second ignition experiment passes both postboot product gates, 0.79/0.76
seconds after the maneuver/diagnostic sequence. Crucially, retained application
events show Brake starting at 13:03:53 UTC but accepting VDP inputs only at
13:05:18, during the Brake maneuver. Tire accepts its inputs at 13:05:22.
The test previously waited for VDP but not for each consumer's authorization
and input recovery. This proves a test sequencing race; it is the leading
explanation for the first missing result, not a direct diagnosis of its lost
boot journal. The passing repeat alone does not erase that earlier failure.

The corrected test waits for each service's fresh receiving-input observation,
with the exact version/native instance and a generation greater than before
ignition. Old preboot, stale, conflicting, wrong-version and wrong-instance
observations fail closed. The local journey suite passes 58 tests. A separately
recorded third cycle validates this strengthened order; product packages and
the strict new-assessment criterion are unchanged.

### Third ignition cycle and bounded Tire observation

The third cycle preserves the same identity and model state. Brake's fresh
postboot input gate takes 23.64 seconds and its new product gate passes in
0.84 seconds after the 26.30-second maneuver. Tire's input gate passes in
0.79 seconds and physical maneuver in 29.25 seconds, but no new Tire assessment
arrives within 180.80 seconds. At 13:16:40.918 UTC the actual Tire process logs
`EXERCISE_SKIPPED / ASSESSMENT_SKIPPED_INPUT_QUALITY`, not a delivery error.
The owned shutdown passes in 31.16 seconds. This is a remaining functional
failure, not a successful ignition cycle; an earlier commentary implying both
products succeeded was explicitly corrected.

A separate, bounded passive observation uses the existing Tire read authority
in the same Test. Tokens remain in guest process memory and are neither copied
out nor logged. No Set, model mutation, raw telemetry recording, service binary
replacement or permission change is performed. It observes 625 subscription
updates over 65.02 seconds: 610 coherent complete frames, 15 intermediate
incoherent updates, no stale/future/invalid values, and two source gaps above
250 ms (maximum 399 ms). Maximum coherent input age is 49 ms. The accepted
250 ms contract is unchanged.

The passive segmentation observer sees a COMPLETE episode of 58 retained
samples / 8.603 seconds. At that exact completion time, 13:34:47.923 UTC, the
actual Tire process again logs `ASSESSMENT_SKIPPED_INPUT_QUALITY`; product IDs
stay unchanged. The observer is not product execution and does not prove what
the Tire consumer retained. This narrows investigation to consumer capture,
segmentation or eligibility rather than backend delivery, but does not yet
prove a specific root cause. The fixed read ends at its gRPC deadline, not a
service crash. Normal shutdown passes in 29.64 seconds. No additional Factory
or diagnostic service release was built for this observation.

Evidence: private `...-tire-passive.json`, diagnostic receipts ending
`dc9bd376-d1cd-41dd-9777-23f806163cb4`,
`0a5c2692-7a2a-4595-8d55-4388f9d5fb0d`, and
`b3bf9ea7-1e43-443f-840c-5c3a0285a0c1`, plus append-only `ignition3-*`
and `capture4-*` attempts. Prior failures remain visible.

### Service resource observation

Read-only cgroup v2 observations confirm the installed limits: Tire
`cpu.max=1500 100000`, Brake `2500 100000`, and 16 MiB memory for each.
Both show CPU throttling; one post-update Brake observation has 1,121 throttled
periods out of 1,159. Memory/OOM event counters are zero in these observations.
These are possible timing contributors, not proof that a quota caused the Tire
episode rejection. No quota, freshness threshold, model rule, security policy
or installed service binary was changed to obtain a pass. Private diagnostic
receipts end in `4b5f472d-5fb0-4a16-872e-b5076552bd9f` and
`4c87f78f-8846-4c35-ac92-10b0122dc7a8`.

### Moving SOTA and native launch

The dedicated CARLA controller visibly entered Autopilot and actual motion.
Brake 110/V3 and Tire 55/V1 were prepared and published sequentially for this
same Test, with unchanged service content and new staging release numbers.
Brake publication / Cloud READY / installed readiness took
22.08 / 9.89 / 3.64 seconds; actual motion after its update was confirmed.
Tire's corresponding timings were 19.96 / 9.85 / 2.81 seconds. Both exact
release versions were observed installed.

The post-Tire continuous-motion gate failed after 63.07 seconds: the fresh
controller observation retained `AUTOPILOT`, `held=false`, but reported
speed zero and brake 1.0. This does not establish either continuous motion or
a SOTA-induced driving regression. A normal traffic stop is possible but not
proven. Preserve the failed gate; do not infer a cause from the speed alone.
This sequence stopped the owned demo in 28.96 seconds; no publication was
replayed. The new-release product checks are separate from installation.

An engineering call to Setup's launch helper through SSH opened Presenter but
could not confirm geometry and caused macOS to attribute Accessibility to
`sshd-keygen-wrapper`. No new permission was granted. The native-GUI check
must not use this caller identity. Normal shutdown completed in 11.45 seconds;
subsequent read-only reconciliation confirmed zero owned processes/listeners
and stopped backends, recording failed visual acceptance without replaying
launch. The adapter now blocks SSH GUI launch; its reconciliation is read-only.
All 60 journey regression tests pass, including the no-replay guard.

At approximately 14:02 UTC, Setup040 was opened through Finder from the pinned
DMG, the existing `SDV-Kit026` private-data folder was selected and **Open demo**
was clicked. Setup visibly reported **Presenter opened / Presenter windows
verified**, without an SSH permission prompt. Presenter showed the retained
Test switched off, Cloud offline, no current-release result, and disabled Reset
buttons with the controller-off explanation. This is successful returning-user
GUI launch, not full demo readiness or first-use installation acceptance.
The Presenter still displayed a generic partial-layout warning while CARLA
and Driving Control were stopped; its wording is more ambiguous than Setup's
specific Presenter-window confirmation and merits separate UI review.

## Final installed-release checks and visual review

The final observation restores the same Test with VDP 133/V3, Brake 110/V3
and Tire 55/V1. No publication or assignment is replayed. Before either
maneuver, its exact installed service must freshly report connected/receiving
inputs. These readiness gates pass, but they do not prove uninterrupted input
quality throughout the subsequent maneuver.

| Check | Elapsed | Result |
| --- | --- | --- |
| Brake 110 maneuver | 26.55 s | Completed |
| Brake 110 new backend product | 0.82 s after maneuver/diagnostic sequence | PASS |
| Tire 55 maneuver | 29.50 s | Completed |
| Tire 55 new backend product | 60.81 s observation | FAIL: no new assessment |
| Normal owned shutdown | 30.78 s | PASS; zero owned processes/listeners |

At **14:06:37.411 UTC (16:06:37 Berlin)** the actual Tire 55 process reports
`EXERCISE_SKIPPED / ASSESSMENT_SKIPPED_INPUT_QUALITY`, correlated with
source event `7ead287b-bd33-4d35-be21-e598926d542c`. This repeats the failure
after a service update; it is not merely delayed delivery of a created result.
Brake logs new assessment creation at 14:06:06.851 UTC and again during the
later physical maneuver at 14:06:40.754 UTC.

The final bounded journal also shows repeated short readiness changes:
Brake publishes NOT_READY then READY, and Tire reports
`KUKSA_DATA_UNAVAILABLE` then READY. Successful Brake product generation does
not close this readiness-stability concern. No specific source, CPU-quota,
consumer-lock or authorization root cause is established by this evidence.
The four managers remain active with zero automatic restarts, SELinux remains
Enforcing and VLAN 1443 is valid. The 56 audit denials in 112 bounded current-boot
records remain in the previously classified baseline categories; the query is
not truncated and this is not a zero-AVC claim.

Final visual observation at approximately 14:08 UTC confirms actual window
placement: CARLA upper left, Driving Control lower left, Presenter right.
The same Test is in Safe Stop, external network ON, Cloud Online, with three
components, two services and no pending update. Brake shows Result received /
Inspection recommended. The following UI findings remain open:

- Tire shows **Delivery blocked / No current-release result**, while the
  actual observed episode was rejected before result creation. Audit the
  status projection and wording; do not label this a proven transport fault.
- Tire Driver Advisory shows **Waiting for service** while the backend input
  projection shows RECEIVING. Correlate local readiness/advisory timestamps
  with the backend projection before deciding whether this is stale state or
  an ambiguous label for a different readiness condition.
- A prior **Restore window layout: PARTIAL** operation banner remains visible
  although the final windows are correctly placed. Keep operation history
  distinguishable from current layout state.

The append-only final records are `products5-*` and shutdown attempt 0216.
Diagnostic receipts end in `975d0de4-30bd-4fb8-8040-7dff12b154c7`,
`5956fd17-3c59-42e7-8e17-a5a75027ae70`, and
`8eef4cc9-6862-4330-92e9-6b43e6c47fd7`. The combined journey, remote and
installed-scenario regression set passes 90 tests; `git diff --check` passes.

Shutdown completed at **14:09:18 UTC** with zero owned demo processes and
listeners. Test identity, VM disk, models, journals and evidence are retained;
Finish was not executed. Docker Engine remains running. The remaining Setup
and test Finder windows were visibly closed at approximately 14:13 UTC.
The development SSD remains mounted; no eject was requested.

## Remaining acceptance and next bounded correction

This section records the earlier Kit 026 checkpoint. The subsequent corrective
work and the 4 October Kit 028 result below supersede its next-action queue;
do not repeat the completed diagnosis or reopen deferred readiness tuning.

The Factory .39 replacement sequence stopped at actual Brake V2 startup.
Factory .40 has passed sequential VDP V1–V3 and Brake V1–V3 product checks,
including a later Brake 110 product. Tire's initial product, independent Reset,
Return to road, the five-minute offline interval and queued delivery recovery
pass. Ignition identity/persistence passes, but repeatable postboot/post-update
Tire analytics and steady readiness do not pass. The candidate is not accepted.

Next, preserve this Test and add only bounded, non-secret diagnostics at the
actual Tire consumer: episode terminal reason, retained sample count, maximum
source/processing gap and read-loop timing. Correlate these with readiness
changes and cgroup throttling to distinguish input discontinuity from local
processing or segmentation faults. Prove one hypothesis with a reversible,
scoped change before any service fix or new package. Do not relax the 250 ms
freshness rule, eligibility rules, quotas or security merely to obtain a pass.
Then repeat the failed post-ignition and post-SOTA product chain and its
negative checks before the final full regression.

Native returning-user Open demo is observed working. Full first-use visual
acceptance and the remaining installer exception branches are not claimed by
that result. Both service SOTA installations succeeded without a requested
Safe Stop, but continuous motion through Tire SOTA remains unproved after the
zero-speed gate failure. Correlate the controller/traffic state in the next
bounded moving-update check. Review the three UI findings above independently
of the Tire functional fix. Host sleep/wake and external working-storage tests
on M1 are excluded; `VDP-TIMEOUT-01` remains deferred.

Private append-only evidence is under
`.local/remote-qualification/m1-journey-025-20261002/` and
`.local/remote-qualification/m1-journey-025-20261003/` and
`.local/remote-qualification/m1-journey-026-20261003/`. These contain no reusable
credentials, passwords or token contents. No commit or push was requested.

## Service-instability investigation (same retained Test)

The subsequent correction session preserves the same Test, Cloud Unit, models
and histories. The findings below supersede the earlier undifferentiated
input-quality hypothesis; they do not supersede the failed acceptance gates.

### Tire interrupted durable transaction: proved and corrected in source

Tire 55's private state contained a valid durable transaction and an interrupted
outbox `.json.next` file. Replay attempted exclusive creation of that same file,
failed with `STATE_WRITE_FAILED`, and left the runtime without a usable store.
Input continued, but the old readiness/activity reports obscured the storage
failure as generic input quality. This was not a backend transport failure.

The reversible E proof recovered the exact retained state at 15:20:39 UTC,
connected to the backend, completed an exercise with 59 samples / 9012 ms, and
produced assessment `9c91352f-ef8a-524a-b270-03708018cce8`. The backend confirmed
the Tire 55 result and correlated `APPLIED` advisory; the outbox emptied. The
original service binary was restored without resetting the model. Canonical
Tire changes retain exclusive creation for ordinary writes, validate the durable
journal before replay, and permit only exact safe interrupted replay files:
regular, private, owned, single-link, non-symlink files with identity checked
before truncation. Symlink, hardlink, FIFO, wrong-mode and malformed-journal
negative cases remain fail-closed. This proof does **not** claim recovery from
every first-create or pre-journal crash cutpoint.

Canonical Tire compilation and all five test suites passed in the offline
service-runtime environment. A watchdog race was also corrected: accepted input
and expiry now share the runtime lock, so a delayed expiry decision cannot
discard a newer frame. Tests retain the exact 250/251 ms boundary. Storage
unavailability and source discontinuity now have distinct truthful activity
reasons. These source changes are not yet a published service release.

### KUKSA source timestamps: reproduced and corrected; Factory delivery pending

The pinned KUKSA 0.5.0 VAL v1 conversion stores incoming measurement timestamps
as `source_ts` but returns per-signal broker receipt time (`ts`). This violates
the demo's source-time-preservation requirement (`REQ-VDP-004`) and can make
signals from one frame appear incoherent at a millisecond boundary. In a
read-only 20.171 s sample, all 181 updates contained all 15 Tire signals, but
none retained identical microsecond timestamps; one batch crossed a millisecond
boundary. The maximum within-batch spread was 152 microseconds. This is not
evidence of partial batch publication. Earlier passive observations of loaded
maneuvers also contained incoherent batches and gaps beyond 250 ms.

The isolated target regression reproduces three failures in the original
conversion: preserving source timestamps, preserving one coherent batch across
receipt-time boundaries, and avoiding restamping old/future data as current.
Three unchanged-behavior controls pass. The proposed correction uses source
time when present, retaining receipt-time fallback only when source time is
absent. All six target regressions and 17 authorization-scope tests pass with
the correction. The broader Rust library suite reports 165 pass / 1 fail /
15 ignored: its fixed JWT fixture fails with `ExpiredSignature`. This is not
a green full-suite claim; no authentication clock or policy was changed.
Three bounded live observations with the corrected broker retained coherent
source timestamps. The last 65 s observation had 570 updates, 569 valid frames,
zero incoherent batches, zero source gaps, maximum interval 232 ms and one
stale update at 252 ms. A new actual Tire assessment
`3925a4dd-2dcf-58a8-bfd5-a50e64ae164c` reached the backend with correlated
`APPLIED` advisory and an empty outbox. One successful product is not stability
acceptance. The broker was restored to its original bytes after each proof.
No source-age tolerance, certificate policy or access rule is widened.
KUKSA is Factory-installed; this is not deliverable by a VDP-only FOTA release.

### Tire resource-burst qualification: authorized, not yet accepted

The original 150-DMIPS request is natively enforced as `cpu.max=1500 100000`
on this Node. During a 25.009 s observation, average CPU was 0.925% of one core
(231226 us), but 22 periods were throttled for a cumulative 1037207 us. Thus
average headroom does not exclude burst starvation. Bounded profiling found
44 durable commits costing about 1.76 ms CPU each, with a 422 ms maximum wall
time; input/status operations share that state lock. Removing an unnecessary
whole-state copy on idle 50 ms advisory checks reduced its CPU cost, but did
not remove all readiness transitions. Source/VM clock skew was measured using
a persistent round-trip probe: approximately 7.0–7.35 ms, not hundreds of ms.

The operator explicitly authorized measurement and CPU-budget requalification
through native signed staging releases. The initial candidate requests
300 DMIPS under the D4-023 amendment. All other quotas, the 250 ms input-age
limit, estimator, persistence, identities and AosCore authority remain unchanged.
No manual cgroup override was used. The SP catalog read confirms that this
Tire service is assigned only to the retained M1 Test. A separate development
artifact catalogue avoids modifying the installed Kit's pinned inputs.

Canonical Tire commit `d519729` includes transaction replay, watchdog ordering
and idle-copy corrections. All five C++ suites pass; 21 Solution contract tests
and 24 package tests pass (one package test skipped). The release observations
below do not advance the accepted installer/Factory baseline.

Publication-path correction: the developer host has no current Test journal;
its normal upload guard therefore returned `SERVICE_NON_TEST_ASSIGNMENT_PRESENT`
with `attempted=false`. It did not identify an extra recipient. Complete fresh
Cloud reads on both hosts confirmed one assignment, identical to M1's native
Test scope, and no version 56 before publication. The immutable prepared bytes
were transferred and hash-validated in M1's mutable catalogue; only the receipt's
local package path was relocated. Installed Kit bytes, credentials and journal
were not changed. M1's normal signing/publication owner then accepted Tire
56.0.0 at 17:34:22 UTC (deployment `132db143-e8ea-4265-be40-ff3ccca7c718`).
Its exact Cloud version became READY and installed input resumed. The observer
started before the blocked developer upload timed out; that record is a harness
ordering failure, not a version-56 installation failure. Subsequent publication
was not a blind retry: the no-POST result and target scope were reconciled first.

Two native Tire maneuvers and the intervening Brake control maneuver each
produced a new backend result. The retained model, Unit/Node identity and
all four managers were preserved with zero automatic restarts. The 300-DMIPS
post-renewal Tire maneuver also produced a new result. The 300.635 s soak
confirmed the same PID and native `cpu.max=3000 100000`, with 3067598 us CPU,
69 throttled periods and 4245785 us throttled time. Three input-readiness
NOT_READY transitions lasted approximately 1, 24 and 47 ms; readiness publication
also briefly changed during token renewal. Therefore 300 DMIPS is not accepted
as the completed stability fix. All four managers and KUKSA had zero automatic
restarts. The 86 audit denials during this bounded soak were solely diagnostic
`sshd_t -> aos_var_run_t:dir search`, not a service-policy denial; no policy was
widened. The next CPU candidate is 600 DMIPS in signed Tire 57 with the
identical binary, published serially only after the 56 checks. Platform source checkpoint for the broker fix
is `9169490`; it does not advance the accepted Factory/installer baseline.

Tire 57.0.0 was accepted at 17:45:51 UTC (deployment
`7dd02354-fe7c-4909-8824-bbaf07dee8be`) and became READY. Its executable is
identical to 56 (`18ad5a5e98cdf20951efc594ce8df72a753e5cd6d2800d0f063d1dc27c419036`);
only the requested CPU budget differs. The 450.890 s observation verified native
`cpu.max=6000 100000`, the same PID, 4465866 us CPU (about 0.99% of one core),
8 throttled periods and 241360 us throttled time. No input-readiness
`NOT_READY/KUKSA_DATA_UNAVAILABLE` transition occurred. Two brief advisory
readiness changes still coincided with token replacement. All managers and
KUKSA remained active with zero automatic restarts. The extended audit from
this window contains only diagnostic `sshd_t -> aos_var_run_t:dir search`
denials, not service-policy denials. No policy changed.

### Planned credential replacement aborts a valid Tire episode

The first Tire maneuver and Brake control maneuver under 600 DMIPS produced new
backend results. The next Tire maneuver completed physically but produced no new
Tire product within the 50.619 s observation deadline. A parallel passive
120.021 s input observation recorded 1067 valid coherent frames, no stale or
future values and no source gaps (maximum interval 187 ms, maximum age 216 ms).
It recognized a complete 58-sample, 8469 ms episode at 17:49:04.396 UTC.

Tire replaced its token at 17:49:00.974 UTC, inside that episode. Source inspection
found unconditional `Runtime::disconnect()` calls both before identifying a
planned replacement and in its exception handler. They discard the active
episode even when the authenticated reconnect receives continuous fresh source
data. This is separate from CPU starvation; raising the quota cannot fix it.

An isolated candidate preserves only in-memory episode continuity during planned
replacement. Fresh IAM lookup, a new authenticated KUKSA subscription, metadata
checks, token expiry and the 250 ms source/monotonic guards remain mandatory.
Actual disconnect, authorization failure, changed metadata or missing input
still aborts. All five C++ suites pass, including continuity, real 251 ms gap,
monotonic expiry and disconnect cases. Live renewal-aligned proof is in progress;
the initial candidate was not yet canonical or a signed release at that point.
The diagnostic overlay had a ten-minute rollback and did not change the native
600-DMIPS quota. Subsequent evidence and its limitations follow below.

### Tire 58 and diagnostic rollback ownership (18:22–18:48 UTC)

The bounded Tire continuity proof ran for 420.681 s with the same process,
4140472 us CPU, six throttled periods / 146902 us throttled time, and no input
or advisory NOT_READY transition. Two maneuvers produced backend results.
One was scheduled to overlap renewal, but the passive observer started after
that maneuver and the repeated renewal event was log-coalesced. Therefore it
does not independently prove the exact episode/renewal overlap.

The tested Tire delta was consolidated as `6a29f5a2456193ac5b42f4ef36cd2ab4dff94ea6`.
Five C++ suites and five subscription-contract tests passed. Native Tire 58/V1
was signed and accepted in staging at 18:27:22.624 UTC, deployment
`25889182-a807-4dae-ae6b-9695976e3770`; Cloud READY followed at 18:28:09.490.
Its executable SHA-256 is
`90616a665b6f854ec6348ccfe30d316ca6063ca597f7a961790369e87ce260d2`.
Native `cpu.max=6000 100000` and the unchanged 16-MiB memory cap were verified.

The first Tire 58 maneuver completed physically but no new product arrived.
This is **not a valid test of Tire 58 plus corrected KUKSA**: at 18:22:28.942
an older CPU300 proof's rollback removed the shared broker drop-in used by a
newer proof. The broker had already reverted to its original executable before
58 was installed. The 450.769 s observation under that original broker recorded
15 input NOT_READY transitions, seven advisory NOT_READY transitions and no
process replacement. Preserve this failure as evidence; do not report it as a
successful soak or attribute it to the new Tire delta alone.

The harness defect was use of one shared drop-in path across generations and
failure to cancel an old timer on manual restoration. Proof24 uses its own
drop-in, checks its exact contents before rollback, cancels its own timer during
restoration and has a 30-minute ceiling. Old active timers were reconciled to
none before applying it. The actual running broker digest is checked rather
than inferred from a prior receipt. No authorization or freshness limit changed.

With corrected KUKSA restored at 18:45:33 UTC and stock Brake 110 unchanged,
the native Tire → Brake → Tire functional series passed: each maneuver produced
a new backend result. The 450.838 s follow-up verified the same Tire and corrected
broker processes/digests throughout, 4620084 us CPU (1.025% of one core), four
throttled periods / 117354 us throttled time, and zero input/advisory readiness
transitions. Three Tire exercises completed, including the renewal-aligned one.
A separate Tire input-quality skip occurred during the Brake control maneuver;
it is not counted as a failed requested Tire maneuver. All platform services
remained active with zero automatic restarts. All 133 AVC denials were the
diagnostic `sshd_t -> aos_var_run_t:dir search` class; no service permission was
widened.

For `tire58-renewal25`, the token file's replacement time was observed as
18:51:31.740 UTC without exporting its contents. The passive observer saw a
complete 59-sample / 8509 ms episode ending at 18:51:35.693 UTC, spanning that
replacement. Native Tire produced assessment `cd71359f-43a6-5e73-9059-1eb3c281c3f6`
and logged completion at 18:51:35.703. The 177.256 s passive observation contained
1555 coherent valid frames, zero source gaps/stale/future/incoherent frames,
maximum interval 203 ms and maximum age 235 ms. The product process remained
unchanged. This closes this bounded native-release continuity reproduction,
not the entire quota-isolation, restart, Factory or installed-kit acceptance.

An analogous Brake renewal fix remains isolated scratch work. Eight C++ suites
and seven subscription-contract tests pass, but live attempts were not accepted:
the first used Debug optimization, and the later Release attempt ran while
KUKSA had reverted. Both were restored to native Brake 110. Heavy CPU throttling
in those attempts requires a controlled follow-up, not an unmeasured quota
increase or an immediate source/Factory promotion.

### Brake hot-path validation cost (18:54–19:04 UTC)

A controlled repeat with corrected KUKSA and the native Release/static C++
link flags still saturated Brake's unchanged `cpu.max=2500 100000`: 300 of 300
periods were throttled in 30.017 s. Restoration of the original Brake 110 then
reproduced the same condition (740374 us CPU, 300/300 throttled periods in
30.015 s, stale-input and advisory-readiness transitions). Therefore this is
not attributed to the planned-renewal delta or a proposed new quota.

Bounded fixed-stage profiling localized the work: in a 30.040 s sample,
`reset_pending()` inside ingest consumed 391273 us across 176 slow calls;
whole ingest consumed 424350 us and next-request preparation consumed
184016 us. Reset-state checking repeatedly read, parsed, canonicalized and
validated the same complete advisory history for every incoming frame.
Maximum observed reset-check wall time was 306 ms; lock wait at input expiry
reached 1.348 s despite only 125 us maximum thread CPU in that section.

The isolated correction memoizes only the parsed validation result for an
exact byte string. Every call still reads the authoritative bounded state
file and compares every byte. Changed bytes undergo the complete original
validator; missing or malformed files fail closed with no cached fallback.
Idle next-request checks avoid copying the whole tree before determining that
no write is due. The persistence protocol, journal, reset semantics, quotas,
freshness and model remain unchanged. Eight C++ suites pass, including a new
same-size/same-mtime corruption, repeated failure, repair, missing-file,
monotonic-request and restart test. Profiling-only code was removed before
the functional candidate was built. Candidate digest:
`0cd3bb0e8489cfdd0861751f25f7f9412e1a43db0e280ecfad252b081d841d46`.
It is undergoing bounded live functional/renewal/soak checks; canonical Brake
source and the installed release have not yet been promoted.

Proof29 completed Brake → Tire → Brake with new results, followed by a Brake
episode starting at 19:11:13.253 UTC, token replacement at 19:11:15.574 and
episode/assessment completion at 19:11:19.137. Its 420.396 s sample measured
8180825 us CPU (1.946% of one core), 893/4201 throttled periods, the same process,
no source-stale input rejection and zero platform automatic restarts. However,
six 102–204 ms advisory readiness dips remained, so this was not accepted as
the final stability fix. Planned reauthentication connection statuses remain
distinct from local advisory validity.

### Readiness wall-clock sampling race (19:17–19:19 UTC)

The readiness caller sampled wall time before waiting for Product's mutex.
Meanwhile ingest could accept a newer frame and advance `telemetry_at_`.
After acquiring the mutex, readiness compared the old caller time to the newer
local receive time and incorrectly classified that fresh state as future data.
Bounded diagnostics confirmed three NOT_READY publications with otherwise-ready
state and computed ages of **-307, -200 and -404 ms**. This is not actual source
clock skew and does not justify removing the backward-clock guard.

The isolated correction supplies a clock function to readiness and samples it
only after acquiring the same mutex as ingest. Scalar-time fixture support is
retained. The original future/5000-ms guards and observedAt semantics are
unchanged. Tire has the same pre-lock sampling pattern, so the same narrowly
scoped correction is being verified there. Brake's eight C++ suites and eight
static subscription tests pass; Tire's five C++ suites and six static tests pass.
The native 250/600-DMIPS quotas remain unchanged. Full candidate live-soak and
delivery evidence follow separately; diagnostic counters are not in these
candidates (`b4ad8ecb…` Brake and `769dbced…` Tire).

### Verified corrections and native service delivery

Brake's final transient candidate completed a 420.509 s observation with the
same process, three new braking products, no telemetry-expiry transition and
no local advisory NOT_READY publication. CPU use was 7,882,215 us (about 1.87%
of one core) under the unchanged 250-DMIPS signed limit. Throttling still
occurred in 824 of 4202 periods; functional success is not an absence-of-load
claim. The fix is committed at `5aa652fda603e7621043961331e58236b19204e9`.
Eight native C++ suites and eight subscription/static checks pass. Every
state-file read still compares authoritative bytes; missing/corrupt data
fails closed. No freshness, model, persistence or AosCore limit was relaxed.

The equivalent Tire clock fix alone did not close stability: a 360 s sample
still contained two input expiries, 25 and 56 ms beyond the freshness boundary,
and one 109 ms advisory interruption around planned token renewal. Reusing the
existing TLS channel across that planned renewal removed repeated connection
setup. Each RPC still receives a new context and current token; metadata is
read again, a changed CA recreates the channel, and unplanned failures discard
the transport. The correction does not persist a bearer on the channel.

The final transient Tire sample lasted 420.613 s with the same process, zero
input-expiry or advisory NOT_READY transitions and 4,107,571 us CPU (about
0.98% of one core). Nine CPU periods were throttled under the native
600-DMIPS candidate limit. A completed episode crossed natural token renewal
at 19:41:05.257 UTC and produced its result at 19:41:09.504 UTC. Five C++ suites
and seven subscription/static checks pass. Canonical source is
`f0a0f6edadb51aa338775d157aa3bde28f5b76f4`. All temporary service replacements
were removed before native publication.

These observations retain SELinux Enforcing and zero automatic platform
restarts. They are not a blanket zero-AVC statement: the Tire sample contains
121 SSH diagnostic `sshd_t -> aos_var_run_t:dir search` denials, retained as
separate evidence rather than attributed to the service or hidden by a grant.
Planned REAUTHENTICATING connection status is distinct from local advisory
validity and must not be relabelled as a demonstrated local outage.

Brake 111/V3 and Tire 59/V1 were built from these exact clean source commits,
signed through the installed selected SP context and published only to the
retained Test in staging. Brake 111 installation, input reception and a new
braking result passed. Tire 59 publication started only after Autopilot motion
was observed. Cloud publication and installed READY passed; motion was
observed again after installation, followed by Safe Stop and renewed input
reception. This proves motion before/after the update, not uninterrupted motion
at every instant of transfer. The earlier motion precondition timeout occurred
before publication because the first remote click had focused the window
without activating the mode; its failed record remains intact.

The native Tire 59 -> Brake 111 -> Tire 59 maneuver sequence produced three
new backend results and passed the combined observation. The subsequent native
soak is recorded below; restart/recovery and successor-kit gates remain separate. The 600-DMIPS envelope
is still a staging requalification candidate, not a completed D4-023 CPU
isolation demonstration; its fixed-load worker remains unimplemented.

Private evidence includes `m1-brake-proof33-monitor-20261003.json`,
`m1-tire-clock34-monitor-20261003.json`,
`m1-tire-transport35-monitor-20261003.json` and the append-only
`brake111-proof37-*`, `tire59-moving39-*` and `native40-maneuvers-*` records.

### Factory 41 build checkpoint

Platform `3fd1f8eb8e8d51c7e89c9f89f1646c7d4f55494f` carries the already-proven
KUKSA source-timestamp conversion and a test-only JWT fixture repair. The old
fixed token is now explicitly tested as expired; a newly signed short-lived
fixture exercises success, expiration and wrong audience with the unchanged
production validator. No production credential is used. The complete Rust
library suite passes 167 tests with 15 pre-existing ignored tests; the scope
and source-timestamp regression gates remain mandatory before image creation.

Clean integration build tooling `30ae66148255830b7e29cc82e2cd251d065bb894`
retains the Factory 40 CM/SM/IAM/VDP test matrix and adds KUKSA compile/package
QA before image construction. Factory .41 built successfully offline from the
warm Builder. Its raw image is 6,997,147,648 bytes, SHA-256
`361c187374469f4a97b3b9c74cb755ce432bc5287fb19ccd2f6bfb9c3eb46769`.
Compile, package QA, image QA and host transfer validation passed. An inherited
forced-unpack warning is recorded; no test or QA rule was disabled. The earlier
attempt failed before compilation because the diagnostic Builder was listening
on a different SSH port; normal shutdown reconciled it before the real build.

The candidate remains BUILT_NOT_LIVE_QUALIFIED. The historical return point and
Factory .40 are unchanged. Offline first and repeat boot passed on disposable
Factory .41 overlays: SELinux Enforcing, provisioning IAM active, normal
CM/SM/IAM/VDP inactive before provisioning, no provisioning marker/PIN and no
automatic restarts. Both boots ended through normal shutdown. New media and
installed M1 acceptance must bind this exact image before promotion.

### Native soak and operator disposition

The 480.061-second native sample started at 20:06:21.954 UTC. Brake 111 and
Tire 59 retained their process IDs; IAM, CM, SM, VDP and KUKSA were active with
zero automatic restarts. Brake used about 1.91% and Tire about 0.99% of one
CPU core over this interval. Tire's native limit was 600 DMIPS; Brake remained
at 250 DMIPS.

Three short Tire input-expiry transitions remained, lasting approximately
3 ms, less than 1 ms and 48 ms. Brake connection/combined readiness changed
during planned reauthentication, without a logged local advisory NOT_READY
publication. Neither service logged such an advisory publication in this
sample. Tire completed three episodes and skipped one on input quality; Brake
completed four windows and assessments. A further maneuver crossed Tire's
natural renewal at 20:13:21.595 UTC and produced a new backend result at
20:13:27.227 UTC. These bounded observations are not a zero-gap guarantee.

SELinux remained Enforcing. The 138 fresh AVCs were the already-separated SSH
diagnostic directory-search class, not evidence of zero AVCs. Evidence is
`m1-native-services40-monitor-20261003.json` and the `tire59-renewal41-*`
append-only journey records.

The operator explicitly deferred further tuning of load-sensitive readiness
transitions and requested release packaging and a new installed E2E run. Treat
this as an accepted limitation for that next test, not a passed strict
zero-interruption criterion. Freshness limits, fail-closed behavior, algorithm
and security permissions are unchanged. VDP-TIMEOUT-01 remains deferred.

The last temporary KUKSA replacement was restored at 20:15:37 UTC; no temporary
service replacement or diagnostic policy enters the new Factory or installer.
Journey shutdown attempt 387 passed at 20:18:07 UTC: zero owned demo processes
and listeners, persistent Test preserved, no Finish, Docker Engine preserved.

### Kit 027 media and clean replacement

The corrected sources are consolidated into Kit 027 with Factory .41, native
Brake V1/V2/V3 and Tire V1 preparation inputs. Tire uses the explicitly approved
600-DMIPS candidate envelope. Game, Python and Gateway inputs are reused from
Kit 026; no unrelated engine rebuild or copied diagnostic state is included.
The application manifest is
`d4caa56bf25aa15428ec5bbba37c1915c96e3d65a3d27e871344e78d56c4b893`.

Setup 041 retains the existing Apple Development identity and designated
requirement. Its binary SHA-256 is
`e1efd310fe4904b57724ff4bee36783b6e6cd8b212d43fb667c2c499e214cfac`.
Native protocol self-test, embedded Python probe and strict signature
verification passed. The complete DMG is 14,160,036,368 bytes, SHA-256
`b546a460e05ec3530a0ad1f8ef0d32036a04fd99ff2526ce7837f5fa3bd9bba1`;
image verification passed. This is local engineering media, not a notarized or
publicly distributable release.

Pre-installation source gates passed: distribution 300 tests (one skipped),
UI 336 tests in 33 files, journey 60 tests, application 14 tests and vehicle
inputs 18 tests. UI type checking/build and native compilation also passed.
An early preparation-input mode mismatch was corrected in the candidate
producer before media creation; Factory bytes and product validation were
unchanged. No later gate inherited a failed candidate result.

Normal Finish then retired Kit 026 Test `4f77ccb2-eb23-461b-88c8-15a1c277ac74`
and its staging Unit `d61e7036-aeb0-4495-b906-a4e6da558fcc`. The working VM
and run-specific backend data were deleted; published releases, credentials,
reports, rollback media and Production were preserved. Post-read confirmed
the automotive journal absent and no owned demo process/container. Docker
Engine remained running. New installation and journey records bind only Kit
027 and Factory .41; historical test passes do not establish their acceptance.

The verified full DMG transferred to M1 in 121.92 seconds. A new empty internal
store and private-data directory were used: installation took 123.02 seconds,
local preparation 35.04 seconds, with no copied operator state. The receipt is
`full-media-m1-027-20261003.json`; the new append-only journey binding is
`m1-journey-027-20261003.json` under the private qualification directory.

The first journey passed installed selection, Docker and backend-image checks,
then stopped at local certificate inspection with `CLOUD_CERTIFICATE_UNAVAILABLE`.
No certificate selection or Cloud mutation had started; normal shutdown passed.
Both retained enrollment files still had their expected owner and mode 0600.
A bounded isolated inspection using the installed runtime completed in 0.355 s;
the unchanged signed Setup's ordinary two-certificate inspection then passed in
3.342 s for staging. No credentials, configuration, timeout or protection was
changed. The original transient failure is retained and its precise cause is
unproven, not labelled as fixed or attributed to cleanup. With confirmed absence
of a prior save, the journey resumed: normal credential-reference save, Cloud
readiness and exact Subject reference selection all passed.

Create Controller then correctly blocked with `VM_RUNTIME_HOST_PIN_MISMATCH`.
Kit 027 had updated its UI/host manifest but reused a VM manifest bound to the
previous host. Individual input integrity tests had not checked this dependency
at assembly or installation. The runner conservatively recorded the operation
as uncertain and stopped normally. A separate authoritative read confirmed no
automotive journal, VM disk, demo process or listener; no Test or Unit had been
created. The original attempt record is unchanged. Kit 027 is rejected, not a
qualified replacement.

Kit 028 rebinds the same six VM payload files to the independently reviewed host
manifest. Factory, CARLA, services, runtime authority and protection are unchanged.
Assembly and installation now both reject the stale cross-binding before copying;
302 distribution tests passed (one skipped). The new reader rejects the actual
Kit 027 with `VM_HOST_MANIFEST_MISMATCH` and accepts all 17,694 Kit 028 entries.
Setup 042's native protocol, embedded Python and signature checks passed with
the unchanged designated requirement. Its binary SHA-256 is
`4eb4e060d5e7306b402aa03a4282ea00ea4e3e7f9f968e152c19e5b824277fd5`;
Kit 028 is `1cb2628a3c358d685441644b500a94598c826f976b0bcff13ab5e7144754fbef`.
Native and installed E2E acceptance require this new candidate's own evidence.

The verified Kit 028 / Setup 042 DMG is 14,150,764,550 bytes, SHA-256
`27c4dbcac02c5cefcd3f20c75d7e51e3d54ec9f631bbc48e8d58839ea8e67236`.
M1 transfer took 121.73 s and the destination hash matched. Fresh installation
took 124.89 s and local preparation 35.69 s; both passed using a new empty
internal store and state directory, without copied operator state. The separate
`m1-journey-028-20261003` sequence began after those gates passed. This is a
clean installed candidate, not yet completed E2E or native UI acceptance.

The first seven Kit 028 journey gates passed: installed selection, Docker,
backend images, Cloud certificate pair, Cloud readiness, exact Subject reference
selection and Presenter readiness. Create Controller recorded its local Test
`f0dbfedf-4c9c-4444-a0c9-1619ebf0bef7`, but its native VM password request
expired without input. The product job ended `PARTIAL` at 21:53:00 UTC with
`VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`. The screen had been showing the
remote screen saver; waking it afterward showed the desktop without the expired
dialog. That observation does not prove whether the dialog was displayed behind
the screen saver or could not be displayed. No readiness threshold was changed.

Read-only reconciliation confirmed that the exact product job was terminal,
with no active or uncertain product operation, a matching Test journal, no Cloud
Unit and a stopped VM. No second Create or provisioning request was issued. The
runner's initial shutdown could not adopt the partial Test identity, so the
separate closure bound that exact identity for shutdown only and used the normal
installed owners. Shutdown passed with zero owned processes and listeners;
persistent Test files, receipts and Docker Engine were retained. The original
uncertain journey attempt remains unchanged and is not counted as passed.
The private closure receipt is `kit028-partial-create-closure-20261003.json`.
Kit 028 full E2E remains incomplete at first VM access, not accepted or rejected
on an inferred runtime failure.

### Source cadence and diagnostic-method failure

A passive post-recovery CARLA sample observed 272 frames over 29.796 s: mean
interval 109.95 ms, maximum 215 ms, no interval above 250 ms. This is a bounded
sample, not a continuous-load guarantee. Controller sampling shows significant
time in Traffic Manager's settings RPC and the controller's pacing sleep;
no timing contract or controller pacing change has been made on that basis.

At 15:37:59 UTC the controller exited after a diagnostic rendering-settings
change. CARLA `World::ApplySettings` internally ticks a synchronous world;
calling it while Driving Control owns ticks introduced a second tick owner.
This is classified as an investigation-method error, not a product regression.
Normal source stop/start and connection recovery completed on the retained
Test at approximately 15:50–15:53 UTC. No provisioning or model reset occurred.
Future passive diagnostics must not call `ApplySettings` while that tick owner
is running. All transient Tire overlays were rolled back before continuing.

Private compact evidence: `m1-tire-state-diagnostic-20261003.json`,
`m1-tire-recovery-proof-20261003.json`, `m1-tire-watchdog-proof-20261003.json`,
`m1-kuksa-epoch-audit-20261003.json`, `m1-source-ticks-20261003.json`,
`m1-controller-sample-20261003.json`, and the append-only `recovery9-*`,
`diagnostic10-*`, `source13-*` journey records. The failed harness starts before
the Rust target specification / loader were restored are not product test
results; their logs are retained separately from the actual RED/GREEN proof.

## Kit 028 installed sequence completed on 4 October

The exact retained, unprovisioned Test from the password-interrupted creation
was reconciled again before resumption: terminal partial Create, no Cloud Unit,
stopped VM, no active product operation and no owned listeners. The ordinary
idempotent Create path resumed that same Test, not a replacement. The native
one-use password dialog accepted the previously authorized VM password; no
password was saved. The original failed attempt and its separate reconciliation
remain in the append-only record.

All **98 scripted sequence checks pass** on the installed Kit 028 / Setup 042 /
Factory .41 candidate. The final report has no unresolved operation, stale step,
source-review warning or supporting-check failure. No product bytes, freshness
thresholds, resource limits or security policy were changed during this run.
This closes the scripted functional sequence, not the separate native operator
and release gates.

The retained Test is `f0dbfedf-4c9c-4444-a0c9-1619ebf0bef7`, staging Unit
`7330baea-92a1-41dc-b450-481b491277be`, Node
`c9326fd7-e5c3-4ff5-845c-19a71907d402`. Serial publication and installation
passed for VDP **134/V1, 135/V2, 136/V3**, Brake **112/V1, 113/V2, 114/V3**
and Tire **60/V1**. Each next version was published only after the previous
version's required checks. Every VDP update had an observed physical Safe Stop.
All Brake profiles and Tire produced new backend results from actual CARLA
maneuvers; Brake V3 and Tire Driver Advisory application checks passed.

| Observed operation | Elapsed | Result |
| --- | --- | --- |
| Resume retained Create, including native VM access | 88.38 s | PASS |
| Provision | 39.98 s | PASS |
| First packaged CARLA startup | 100.39 s | PASS; macOS verification was visible |
| Connect Test | 11.93 s | PASS |
| VDP V1 / V2 / V3 publication | 15.87 / 15.94 / 15.93 s | PASS |
| VDP installed-readiness observation after publication | 9.32 / 8.69 / 8.29 s | PASS |
| Brake V1 / V2 / V3 publication | 21.94 / 19.95 / 19.98 s | PASS |
| Tire publication | 22.00 s | PASS |
| Return to road | 4.71 s | PASS |
| External-OFF soak | 302.81 s | PASS; complete 300-second interval sampled |
| Queued delivery observation after ON | 27.97 s | PASS |
| Ignition ON | 35.91 s | PASS |
| Post-ignition VDP readiness observation | 28.16 s | PASS |
| Post-ignition Brake / Tire input observation | 57.54 / 0.76 s | PASS |
| Normal shutdown | 30.60 s | PASS |

These are individual operation or observation durations, not interchangeable
end-to-end UI latencies. In particular, Tire's input observation starts after
the Brake input and maneuver checks; 0.76 s is not its total boot recovery time.
The 57.54-second Brake observation does not by itself locate when local
subscription recovered relative to backend status publication.

Independent Brake and Tire Reset checks passed. Each selected model reset was
acknowledged, the other model remained unchanged and the observed backend
history was preserved. Return to road completed without starting Autopilot.

During external OFF, both local models progressed while backend product counts
remained at four Brake and one Tire result. The final disconnected observation
had three Brake queued messages, containing two assessment IDs, and thirty Tire
queued messages, containing one assessment ID. CM, IAM, SM and VDP remained
active with successful results and zero automatic restarts in the sampled
observations. Cloud OFFLINE was confirmed. After ON, both queues emptied and
the exact queued assessment IDs appeared in backend history: six Brake and two
Tire products. Cloud ONLINE was confirmed separately.

Ignition changed the VM boot identity while retaining Unit, Node, system UID,
both models and observed history. The controller returned to physical Safe Stop
with zero speed, full brake and no held operation. No provisioning or Autopilot
start was issued. Fresh postboot receiving-input observations from the same
native service instances had increased producer generations. Both subsequent
maneuvers produced new results: seven Brake and three Tire products were present
at the final respective reads. Core manager restart counters remained zero in
the postboot observation. This is bounded functional evidence, not a claim of
uninterrupted readiness under every host load or a new security/AVC audit.

At **05:13:56 UTC (07:13:56 Berlin)** normal shutdown confirmed zero owned demo
processes and listeners. Persistent Test, Cloud identity, disks, models, history
and receipts are retained. Finish was not executed; Docker Engine was preserved.

The screen-control tool reported a locked Mac and required manual unlock, so the
final native visual review could not proceed. It is **not passed** by the script
or by earlier candidates' screenshots. The separate current-candidate gates for
moving SOTA, native secure token entry, native operator flow and installation
interruption/repair remain explicitly open. Host sleep/wake and M1 external SSD
tests remain excluded; short load-sensitive readiness tuning and VDP-TIMEOUT-01
remain deferred. Public distribution/notarization is not established.

Private evidence is the existing `m1-journey-028-20261003/` append-only record
and its `report.json`: 109 total attempts, including the preserved previous
failure and supporting checks, with all 98 current main steps passing. The
one-shot resumption records `TERMINAL_PARTIAL_CREATE_RECONCILED` before the
successful Create. No rebuild, Git commit or push was needed for this test.

### Native UI continuation on 4 October

The M1 screen became accessible and the matching signed Setup 042 was opened
from the mounted Kit 028 DMG through Finder. Its main window and native folder
chooser rendered correctly. The retained `~/SDV-Kit028` private
data directory was selected through the chooser and its exact path was visible
in Setup. Neither Install nor Open demo was submitted.

Two operator-experience observations remain separate from runtime acceptance:

- The returning-user screen required manual selection of the retained private
  data folder rather than showing that instance automatically. This is a UX
  observation, not yet an established violation of the accepted contract.
- Screen Sharing text injection dropped alphabetic characters in path fields.
  Native folder selection worked for the private-data path. No operation was
  submitted with the malformed text. This is a remote-input limitation, not
  evidence that ordinary local typing or the installer filesystem logic fails.

At approximately 09:36 Berlin time the screen-control tool reported that the
Mac was locked and required manual unlock, while the package-storage folder
chooser was still open. UI execution stopped at that boundary; no alternate
SSH launch was used. A separate read confirmed the same Test and staging Unit,
one Setup process and no listeners on the owned demo ports. Thus returning-user
launch, native runtime controls and moving SOTA have not passed in this attempt.
The 98-check scripted result is unchanged and is not counted as native evidence.

At this blocked boundary the exact owned Setup executable was closed with
SIGTERM after process-path verification. Exit and absence of owned demo-port
listeners were confirmed; no forced termination, Test deletion or Docker Engine
stop occurred. The unsent folder-selection attempt did not launch the runtime.

### Native launch and simulator continuation after reported unlock

After the operator reported that the screens were unlocked, the same Setup 042 was launched through
Finder and the retained private-data folder was selected using the native folder
chooser. A single **Open demo** submission opened the installed Presenter without
reinstalling or replacing the Test. Progress was observed within 12.512 seconds
and the native Presenter was visible within 30.947 seconds. These are upper
observation bounds, not instrumented first-paint measurements.

The cards displayed VDP V3/136.0.0, Brake V3/114.0.0, Tire V1/60.0.0 and
Factory .41. The stopped controller was labelled **Controller switched off**;
Reset was disabled with an explanation. No false running/ready claim was observed.
Session Lifecycle and Test setup dialogs were inspected. Setup was subsequently
closed through its normal window control while Presenter remained open.

The returning-user path exposed an operator-experience gap: Setup says to open
the existing instance and continue in Demo Control, but a retained stopped
controller offers only **Refresh state**, not a power-on action. Source inspection
confirms that this is intentional current Studio behavior: ADR 0017 removed
Park/Resume; the legacy `LocalLifecyclePage` containing engineering Start controls
is not rendered by `PresenterApp`. This observation does not justify silently
reintroducing that retired lifecycle or count as a failed VM boot. The returning
stopped-instance user experience needs an explicit product decision.

To continue independent native checks, the existing qualification adapter used
normal product owners to restore only the two backends and the same Test VM.
Brake and Tire took 8.02 and 7.95 seconds; the VM took 38.90 seconds. This is
engineering setup, **not** evidence of UI power-on. No Test/Cloud identity, service
version, model, credential or production target was replaced.

The Presenter then offered **Start simulator**. Its confirmation dialog named
the current Test and unchanged Production scope. One native click submitted
operation `c921513f-a0ad-43cc-bd9a-c3d6ac5f6446`; the returned frame showed
**Operation in progress / ACCEPTED** without another submission. The operation
completed from 08:01:18.652 to 08:02:24.818 UTC, **66.17 seconds**. A read-only
reconciliation confirmed no active/uncertain operation and source
`RUNNING_UNASSIGNED`; connection and Autopilot had not been submitted.

The next screen observation was blocked again by the computer-use tool's manual
unlock requirement. Simulator rendering, final layout, native connection,
maneuvers and moving SOTA therefore remain unverified in this attempt. The
earlier layout warning while simulator/panels were stopped is not proof of a
misplaced running layout. Scripted startup success does not replace the missing
visual observation. No candidate rebuild or source behavior change was made.

At **08:06:03 UTC (10:06:03 Berlin)** normal ownership-checked shutdown
completed in 24.38 seconds and confirmed zero owned demo processes/listeners.
The Test and its persistent data were retained; Finish was not executed and
Docker Engine remained untouched. This attempt did not establish which host
caused the tool's lock error. No rebuild or repeat of the 98 scripted checks is
needed when native access is restored.

### Local host and remote M1 lock state distinguished

The operator disputed the lock diagnosis. A fresh Screen Sharing observation
showed the M1 desktop and Setup; no M1 lock screen was observed. Native folder
selection and Open demo worked again. Remote shortcut/paste injection did not:
the paste tool timed out and literal shortcut characters appeared in the path
field. The path was corrected using the native chooser before Open demo. This
is a remote-input limitation, not an installer path-validation result.

The same Test and both backends were restored through their normal owners as
engineering setup (Brake 7.39 s, Tire 8.28 s, VM 39.60 s). This does not qualify
the missing native power-on path. Setup was closed through its window control.
One native Start simulator confirmation submitted operation
`b1958d09-22b2-4444-ba11-5c6ada54d6fa`. The UI immediately showed ACCEPTED,
then RUNNING and map-readiness progress; the CARLA city rendered in the left
window. Completion was reconciled at 08:23:31.454919 UTC, **63.85 seconds**
after submission. No active or uncertain operation remained; source state was
RUNNING_UNASSIGNED. Connection and Autopilot were not submitted.

The next screen read returned the tool's locked-Mac/manual-unlock error. This
time independent read-only OS flags distinguished the two hosts:

- M1 test host: `IOConsoleLocked = No`.
- Development host running Codex and Screen Sharing: `IOConsoleLocked = Yes`,
  with `CGSSessionScreenIsLocked = Yes` and lock timestamp **10:23:49 CEST**
  (08:23:49 UTC).

These flags explain why an unlocked M1 does not establish that the local
computer-use session is available. They do not establish why the development
host locked, whether the physical screen matched the flag, or why automatic
unlock failed. Earlier tool errors must not be described as proven M1 locks.
No lock, permission, sleep or security setting was changed, and no alternative
UI-control path was used to bypass the tool restriction. Official
[Computer Use documentation](https://learn.chatgpt.com/docs/computer-use#locked-use)
describes a bounded automatic-unlock path and manual-unlock fallback, but does
not diagnose this particular event.

Final running layout, native connection and the remaining native gates are
still unverified. Product bytes, installed versions, credentials and the
98-check scripted result remain unchanged.

At **08:26:56 UTC (10:26:56 Berlin)** normal shutdown completed in 22.54 seconds
and verified zero owned demo processes/listeners. Test identity, disks and model
data were preserved; Finish was not executed and Docker Engine was not stopped.

### Native layout connection and driving observed

The next continuation used the same Kit 028, Setup 042 and retained Test. The
development host was observed unlocked before native work. Finder launch, private
folder selection, Open demo and closing Setup all worked through Screen Sharing.
The two backends and stopped VM were restored through normal product owners in
6.44, 6.98 and 38.77 seconds respectively. This remains engineering preparation,
not evidence that the missing native power-on path has been closed.

One native Start simulator confirmation submitted operation
`a2656c18-4055-4bfd-8998-19c76004788a`. ACCEPTED appeared in the returned frame;
map-readiness progress followed. The operation completed from
08:40:26.767264 to 08:41:30.058587 UTC, **63.291 seconds**. After completion,
CARLA occupied the upper left, Driving Control the lower left, and Presenter
the right side. All three were visible without manually raising or repositioning
the demo windows. Intermediate startup window positions were not treated as the
final layout.

The native **Connect in Manual** confirmation submitted operation
`2775b92c-4fb8-4803-b145-026579252a22`. It completed from
08:42:24.753118 to 08:42:31.759389 UTC, **7.006 seconds**. Subsequent native
observation showed Test Vehicle selected in both Presenter and Driving Control,
stationary Manual, external network ON, both backend inputs RECEIVING and both
persisted Inspection recommended advisories displayed in the vehicle panel.

Autopilot was selected through the native Driving Control button. Later frames
showed the car travelling through the city, AUTOPILOT / MOVING and **19.5 and
19.4 km/h**. Selecting the Brake team tab left both simulator and Driving Control
visible and the car moving. The page correctly distinguished the selected old
V1/112.0.0 candidate from the installed active 114.0.0 service; its Sign & publish
button was disabled for that already-submitted candidate. These are observations
of existing state, not a newly published release or a moving-SOTA pass.

The next attempted profile-selection click failed with the computer-use tool's
locked-Mac/manual-unlock error. Independent OS reads again reported the development
host locked and M1 unlocked. The development-host lock timestamp was
**10:44:05 CEST (08:44:05 UTC)**. Its cause and automatic-unlock failure remain
unestablished. No security setting was changed or alternate UI-control mechanism
used. No service preparation, signing or publication was submitted in this
continuation, and no ambiguous release operation was left to retry.

A bounded read before shutdown found VDP 136.0.0 active in its matching slot,
23 read paths and REPORTED_READY / source LIVE. IAM, CM, SM and VDP were active
with successful results and zero restarts. A later controller sample was fresh
and still in AUTOPILOT but stationary; the earlier observed movement is not
misrepresented as uninterrupted movement throughout the session.

At **08:46:25 UTC (10:46:25 Berlin)** normal shutdown completed in **26.74
seconds**, with zero owned demo processes/listeners. Test identity and persistent
data were preserved, Finish was not executed, and Docker Engine was untouched.
No source, installed candidate or release bytes changed. Native layout,
connection and Autopilot are now observed; native maneuvers/Reset/offline review,
moving SOTA, secure UI token entry and installation interruption/repair remain
open. The 98 passed scripted checks are retained, not rerun or promoted into a
complete native E2E claim.
