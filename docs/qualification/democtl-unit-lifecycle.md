<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# democtl Unit Lifecycle — Terminal Acceptance

Current outcome: **Factory .28 completed its bounded VM/Cloud lifecycle cycle**:
provisioning, idempotent reuse, combined and individual restarts, deprovision,
Unit/Node deletion and local environment retirement. Before retirement both were
Online with correct memberships, IAM/SM/CM NRestarts=0 and zero current-boot
kernel AVC denials under SELinux Enforcing. Original .28 is preserved.
The operator subsequently removed the unnecessary old-identity reconnect test
from future CLI runs; that source-only change is noted below. Subsequent explicit
cleanup removed all three remaining .27 Cloud Units and five local .27 disks.
This is not full CARLA/VDP scenario qualification.
Historical disposition sections below are dated checkpoints, not current state.

- Date: 2026-09-05
- Source: main working tree based on fe35641; not a commit/push receipt
- Scope: current-run Test/Production Cloud lifecycle, not complete-demo R0
- Design: [Demo Control](../architecture/demo-control.md), Unit Lifecycle — Authorized Increment
- Commands: [Demo Orchestrator](../../apps/demo-orchestrator/README.md#provision-and-retire-cloud-units)

## Boundary

Live checks used democtl from apps/demo-orchestrator with its virtual environment
activated. No direct SDK/SSH/QMP call or former lifecycle wrapper replaced CLI
acceptance. The one-time authorized removal of the retained baseline Unit's
Test-set membership was a separate exact API operation; its Unit, provisioning,
nodes and local VM/disks were preserved.

Both current overlays derive from the same unchanged raw factory artifact
6.1.1-maninblack.27/main-qemuarm64, 6,997,147,648 bytes, SHA-256
dbc018cf31dc83accbca82cf26df0b3ca69c66d1135100db8d05552fd2744c56.
Existing per-VM SSH enrollment and existing OEM credentials were reused; no
password, PIN, key/certificate content or raw Cloud/guest log is in this record.

The public Cloud OpenAPI read during implementation was version 6.1.26:
[API v11 schema](https://api.aoscloud.io/api/v11/openapi.json).
Its deprovision operation requires Offline; role membership uses scoped
system_uids operations. SDK provisioning used the official v6 flow with the
previously qualified narrow 5.4.2 start/finish transition correction as a library.

## Initial Diagnostic Coverage

| Command / condition | Observed result |
| --- | --- |
| vm start all, existing enrolled factory-derived guests | COMPLETED; Test ready at 24.85 s, both at 27.56 s |
| unit provision all, first SDK attempt for each role | Both SDK attempts succeeded; initial command PARTIAL because a QEMU successful-forward-removal message was misclassified |
| unit provision all, authoritative continuation | Both Online and in their correct role sets; no second SDK invocation; role durations 22.12 s and 21.59 s |
| unit provision production; unit provision test, already provisioned | Idempotent, same UUIDs, correct memberships; 14.88 s / 14.78 s |
| status all --guest --cloud | Both normal mode; IAM/SM/CM active, NRestarts=0; SSH/DNS and Cloud Online observed |
| unit delete all, before deprovision | Both BLOCKED UNIT_DEPROVISION_REQUIRED; no deletion |
| unit deprovision test, then continuation | Cloud deprovision applied once; initial 8-second CM stop observation timed out; reconciliation proved old-identity rejection and completed graceful stop without repeating Cloud deprovision |
| unit delete test | COMPLETED; Unit/Node absence and empty Test set; disk retained; 24.06 s |
| status production --guest --cloud after Test deletion | Production remained Online, healthy core services and zero restarts (06:11:32 UTC) |
| unit deprovision all, Test already deleted | Test no-op; Production became new/Offline once, but first command PARTIAL because rejection evidence arrived after the probe read window |
| unit delete all at that boundary | Test absence re-confirmed; Production correctly blocked pending retirement proof |
| unit deprovision production, authoritative continuation | Same-attempt late rejection reconciled; graceful stop completed; no second Cloud deprovision; 21.09 s |
| unit delete test; unit delete production | Test idempotent absence; Production deleted with Unit/Node and role-set proofs; 10.18 s / 24.31 s |
| status all --cloud --profile oem-delivery --timeout 30 | OBSERVED at 06:21:51 UTC; both VMs STOPPED, both Units deleted, OEM authority current |
| unit delete all, both already deleted | COMPLETED for both; authoritative absence re-confirmed; cloudMutationsStarted=false; 10.46 s / 10.20 s |
| vm start all, retired overlays | BLOCKED RETIRED_VM_REQUIRES_FRESH_FACTORY_OVERLAY; no VM started |

Timings are host observations, not guarantees. A continuation passing does not
retroactively turn the first PARTIAL invocation into a clean first-pass result.

## Corrections and Qualification Limits

1. The QEMU monitor's nonempty successful removal reply is no longer treated as
   an error. The actual forwarding table proves the resulting state.
2. CM stop now waits on its real state instead of an eight-second synchronous
   SSH budget. Its stock systemd stop limit is 90 seconds, unchanged by democtl.
3. After a bounded old-identity attempt, the same journal cursor is re-read once
   CM finishes stopping. This captures a handshake that completes during drain,
   without another reconnect. A deterministic late-evidence regression passed;
   the final combined first-pass path still needs a fresh live cycle.
4. Status for deleted Units now combines exact 404 with authenticated inventory
   absence. The error-code match and a Python local-import shadowing defect were
   fixed; the final live status above passed.

Discovery with the old identity succeeded, then the server rejected WebSocket
upgrade while the Unit remained new/Offline. The CM logger truncated the HTTP
reason. Evidence proves failure to return Online, **not** certificate revocation
or a guessed HTTP status. Guest logs were classified in memory; no raw transcript
was retained. No product/rootfs, DNS configuration or security policy was patched.

Package regression gate: 86 isolated tests and 11 run-state contract tests passed.
Documentation/link and whitespace gates passed. This is not a substitute for
fresh live acceptance. The supported-SDK preflight was added after the successful
SDK attempts and also needs that next fresh-path exercise.

At this initial checkpoint, still unqualified: fresh individual provision in reverse order; a clean first
invocation of all three operations after the final fixes; all retirement with
both roles initially live; provisioned-guest reboot recovery; crash/lost-response
injection, fresh AVC qualification, full R0, CARLA/VDP and arbitrary image versions.
Fresh cycles require fresh factory-derived overlays. These two retired disks
were explicitly retained; they were not silently replaced to extend testing.

## Initial Checkpoint Disposition

- Test Unit b55cdb27-a3a9-428f-8cb3-a1f7a0e94ec7 and Production Unit
  1c95c7fa-8815-42ad-8350-d25385e9c79c were deleted (Cloud deletion is not undone
  by the retained local disk). Their Unit-owned Nodes were inaccessible.
- Persistent Test Vehicles and Production Vehicles sets remain and were proven
  empty. Their UUIDs are respectively f83dee0e-d93c-4dd2-905f-a3b4f8dc9878 and
  1823b4a8-27b8-4f21-aa87-0438294cc2e8. No role/fleet/permission was created.
- Pre-existing Cloud Campaign sets were not created or explicitly assigned by
  democtl and were not deleted. Their automatic memberships are not role binding.
- Both exact managed VMs and shared owned DNS stopped. The local factory copy,
  validation/production overlays and .run/demo-current journal/access files remain.
  No backup, disk cleanup, Builder run, image build, VDP upload, CARLA action,
  commit or push occurred in this slice.
- Retained baseline Unit 70e48e60-de2b-444b-a961-258683f324c4 remains provisioned;
  only its separately authorized Test membership was removed. The ignored
  .local/demo-control/baseline-membership.json receipt records this narrow action.

## Follow-up: Authorized Fresh Cycles

The operator subsequently authorized extending environment retire to remove
the two proven Cloud-retired overlays, tracked run-access files and journal,
and explicitly also the local working factory copy/generated manifest. Original
artifact, published manifests and retained baseline VM remain excluded.
The new cleanup gate performs fresh authenticated Unit/Node/systemUID absence
and empty role-set reads before local deletion, including after interruption.
Isolated fixtures cover denial, incomplete Cloud retirement, successful cleanup/
recreate and interrupted unlink followed by a newly denied Cloud read.

### Cycle A: Fresh all, Remaining Forwarding Defect

Initial cleanup and fresh create both completed. First SSH enrollment used only
interactive hidden prompts. Fresh vm start all passed: Test 61.22 s, both ready
by 74.31 s. Each SDK attempt succeeded, including the supported-SDK preflight,
but both commands reported PROVISIONING_FORWARD_POSTCONDITION_FAILED.

The endpoint-only table check counted non-listener TCP entries. libslirp marks
the actual listening rule HOST_FORWARD separately from accepted/draining
connections at the same endpoint, as shown in its
[connection-info implementation](https://qemu.googlesource.com/qemu/+/dfacac4c819f57f3a3e11ef2114a86a5d68fb648/slirp/src/misc.c).
Subsequent read-only democtl status observed both forwarding ports absent and
both guests in normal mode. The check now selects HOST_FORWARD specifically;
fixtures reject a remaining listener but permit CLOSE_WAIT/TIME_WAIT/ESTABLISHED
connection rows. Status can expose only fixed connection-state names, not the
raw forwarding table. Payload-bearing CM log lines are excluded completely.

An explicit continuation read and bound the existing Cloud identities without
another SDK call, then assigned the exact role sets. Test Unit was
ba446c3a-dbcd-4a97-98e1-7dbd39d36faa; Production was
a30ea8a2-5fa4-46ab-a84c-f5f28a878d4d. Status at 07:06:41 UTC observed both
Online, normal core services, zero restarts, working SSH and DNS.

Starting with both Units live, unit deprovision all completed on its first
invocation: Test 116.44 s and Production 115.78 s, including old-identity
rejection and graceful shutdown. unit delete all completed (26.49 / 25.11 s),
proving Unit/Node absence and empty persistent role sets. environment retire
then removed exact local overlays/access, working factory copy/manifest and
journal without backup. The original artifact was preserved. This validates
the combined retirement path, but the initial provisioning PARTIAL remains a
failed first-pass result; later fresh cycles must qualify its correction.

### Cycle B: Fresh Production Then Test, Reboot Failure Preserved

Fresh create completed from the same original .27. Individual first starts
passed (Production 60.28 s, Test 60.07 s). Individual first provisioning passed
without continuation or SDK retry: Production 49.13 s, Test 48.31 s. The live
forwarding observations explicitly showed TIME_WAIT entries after listener
removal, confirming the endpoint-only-check defect and its correction.

| Role | System UID | Unit UUID | Main Node UUID |
| --- | --- | --- | --- |
| Production | 06032ca018b047339a8d2bce1b02195a | 47930d0c-839f-495a-a687-758d23e9543b | aeaaab67-c973-4206-8a36-97a4f0da8f82 |
| Test | 033fb7cd169f405580c03ff4961a156d | 1d2deb63-7981-4cc7-86de-6c06a2a8b108 | d31c3608-8a37-4a8a-bb51-598eaa0a1824 |

At 07:18:49 UTC both were Online, in their correct role sets, with authenticated
SSH, working DNS, normal IAM/SM/CM and NRestarts=0. vm stop all then completed
(3.81 / 4.95 s); vm start all completed without password (24.54 / 25.89 s).
Idempotent unit provision all reused exactly the same four Cloud UUIDs and two
systemUIDs, with no SDK invocation (15.58 / 16.40 s).

The next status at 07:20:08 UTC confirmed both Online, but Production CM had
NRestarts=1. This fails the zero-restart stability criterion. The shell acceptance
sequence had already advanced to Production deprovision because status exit 0
means observations obtained, not health accepted. It was interrupted as soon as
that result was inspected. Future acceptance must inspect status fields before
advancing to destructive steps; shell set -e alone is not a health gate.

Production Cloud deprovision had applied once before interruption; its Unit
remains new/Offline and is **not deleted**. The interruption occurred during the
old-identity probe; its finally block stopped CM normally. The VM remains running
for diagnosis, with IAM/SM active and SSH/DNS available. Test was not retired and
remains provisioned. No local Cycle B file was deleted. Both overlays, the working
factory copy, access files and journal remain in their canonical current-run paths.

Read-only democtl diagnostics of the current boot confirmed a systemd exit of
code=dumped, status=6/ABRT and result core-dump. A runtime-termination signature
is present, but no usable exception/assertion expression or stack was recovered.
coredumpctl is unavailable in this image. Raw core memory was neither read nor
exported; raw guest logs were classified in memory, not saved in the dossier.
The later CM stop resets NRestarts to zero; that does not erase the earlier
observed abort. Its root cause is **not established**, and is not attributed to
DNS, QEMU, a particular AosCore function or democtl without evidence.

Bounded boot-failure/exit/core-metadata observations were added to status details.
The CLI now handles Ctrl-C with exit 130 and an explicit retained-state message,
instead of a traceback; it does not perform a new mutation or discard recovery
state. The real interruption above occurred before that presentation fix.

### Remaining Gate and Current Disposition

Final source gates: 93 package tests and 12 run-state contract tests passed;
documentation/link and whitespace checks passed. These gates do not waive the
observed guest-runtime failure or qualify the unrun combinations below.

- Do not delete/rebuild/reprovision Cycle B to conceal the abort. Its current
  journal is .run/demo-current/journal.json, its overlays are
  .local/demo-current/validation.qcow2 and production.qcow2, and the working
  factory copy remains .local/factory/oem-demo-factory.img.
- Diagnose the CM abort and agree any cross-component/image change before
  claiming reboot stability. No guest binary, rootfs, security policy or original
  image has been changed by this investigation.
- Fresh combined provisioning after the final forwarding fix (Cycle C), reverse
  peer-retirement completion and the remainder of Cycle B cleanup remain unrun.
  Combined retirement starting with both live Units did pass in Cycle A.
- Full scenario R0, CARLA/VDP, Mac crash/sleep recovery and arbitrary image
  qualification remain outside this slice. No commit or push was performed.

### Operator-Requested Repeat: Retained Test Stop/Start

On 2026-09-05 the operator requested a repeat check. The initial read at
07:46:24 UTC confirmed Test Online and Production new/Offline with CM stopped.
Production's same-boot record still contained the previously observed 6/ABRT;
this was not a new crash. Its unfinished deprovision lifecycle was retained.
The run had no outstanding operation-lock entry, so a separate Test VM operation
could proceed without reconciling or changing Production.

From apps/demo-orchestrator with the virtual environment activated, separate
democtl vm stop test and democtl vm start test invocations completed in 4.31 s
and 23.36 s. No password, SDK provisioning, Cloud mutation, fresh overlay or
image change was needed. Each result was inspected before the next command.

The read at 07:48:45 UTC confirmed Test Online/provisioned, the same Unit UUID
1d2deb63-7981-4cc7-86de-6c06a2a8b108 and systemUID, and its expected Test Vehicles
membership. IAM, SM and CM were active/running with successful results and
NRestarts=0. Authenticated SSH and guest DNS passed; the bounded current-boot CM
failure observation contained no service exit or runtime-termination signature.
Production remained running locally, new/Offline in Cloud and CM inactive;
its original diagnostic boot and files were not changed.

A second read at 07:50:07 UTC, 82 seconds after the first post-start observation,
again confirmed Test Online, unchanged identity/membership, working SSH/DNS and
IAM/SM/CM active with NRestarts=0. The bounded CM boot-failure observation again
contained no service exit or runtime-termination signature. Both VMs and the
shared DNS service were deliberately left running. The documentation quality
gate and git diff --check passed for this evidence-only update.

This is a single-role restart proof, not a repetition of the former simultaneous
two-VM restart: Production is no longer provisioned. It neither establishes the
cause of its original abort nor closes the blocked combined-restart acceptance.
No lifecycle implementation change, package/image build, deletion, commit or
push was performed for this repeat. Existing package-test results above were
not rerun or represented as new tests.

## Full Two-Role Repeat — Operator Authorization

The operator explicitly requested deprovision/delete of both current Units,
removal of their local environment and a complete fresh Test/Production CLI
cycle. This supersedes the previous instruction to retain Cycle B's diagnostic
runtime. Its compact sanitized evidence above is retained; no disk backup is
created. Only current journal-owned targets are in scope, including the working
factory copy and generated manifest. The original .27 artifact, retained baseline
VM/Unit, persistent role sets, Campaign definitions, Builder/caches and unrelated
files/Cloud Units are excluded.

Execution uses individual democtl invocations from apps/demo-orchestrator, with
each outcome inspected before advancing. Planned coverage: initial retirement
and fresh create; combined start/provision; authoritative Online and exact role
membership; idempotent role commands; isolated and combined VM stop/start with
service-restart inspection; Production retirement while Test stays Online;
Test retirement; final local cleanup and repeated empty cleanup. This is the
complete implemented VM/Unit CLI lifecycle, not CARLA/VDP or full scenario R0.

### Cycle C Execution and Reproduced Failure

The initial unit deprovision all completed: Test 115.00 s; Production 22.30 s,
reconciling its earlier Cloud deprovision and existing rejection evidence without
a second destructive Cloud request. Both old identities were rejected and both
VMs stopped. unit delete all completed (25.32 / 25.57 s), confirming Unit/Node
absence and empty persistent role sets. environment retire then removed both
Cycle B overlays, tracked SSH access files, working factory image/generated
manifest and journal, without backup. The original .27 artifact was preserved.
Old diagnostic guest journals are no longer available after this authorized
removal; their compact observations above remain, not a claim of recoverability.

Fresh environment create --image 6.1.1-maninblack.27/main-qemuarm64 --target all
completed from the same immutable original. New identities were:

| Role | System UID | Unit UUID | Main Node UUID |
| --- | --- | --- | --- |
| Test | e2e824a126c8491882c22f3670be4c23 | 27e0a9cc-453d-416a-a284-bb1306ebff11 | 885636be-3f50-404d-9b8d-77b9501e7eff |
| Production | 3f3952c22fa54e9e933ee5590ff60ba3 | b5f8465b-1efe-412a-8384-f0a5dc7cd53c | ba4dcb8d-852c-42b6-a7cb-0d2cb1db445e |

| CLI step | Actual result |
| --- | --- |
| vm start all, fresh initial enrollment | COMPLETED; Test 61.86 s, both ready by 74.40 s; SSH/DNS passed |
| unit provision all, fresh first invocation | COMPLETED without continuation; Test 49.65 s, Production 49.06 s; one SDK attempt each, correct role sets |
| status all at 08:06:40 UTC | Both Online/provisioned, normal IAM/SM/CM, NRestarts=0, SSH/DNS passed |
| unit provision production, already provisioned | COMPLETED 14.56 s; same Unit/Node/systemUID, cloudMutationsStarted=false |
| unit provision test, already provisioned | COMPLETED 15.25 s; same Unit/Node/systemUID, cloudMutationsStarted=false |
| vm stop production | COMPLETED 5.05 s |
| status all at 08:08:56 UTC | Production stopped/Offline but still provisioned; Test remained Online, normal core services, NRestarts=0, SSH/DNS passed |
| vm start production | COMPLETED 24.01 s; enrolled access reused, no password or SDK |
| status all at 08:09:56 UTC | Both Online, same identities/memberships; IAM/SM/CM active, NRestarts=0; Production bounded CM boot-failure observation had no service exit |
| vm stop all | COMPLETED; Test 4.52 s, Production 4.69 s; shared DNS stopped with last VM |
| vm start all | COMPLETED; Test 24.63 s, both ready by 26.47 s; SSH/DNS passed |
| status all at 08:11:29 UTC | Both Online, but Production CM NRestarts=1 and boot evidence code=dumped, status=6/ABRT, result core-dump; Test core NRestarts=0 |

Initial factory-boot logs included a CM dependency-job failure on both roles;
by the first post-provision observation all normal core services were active and
had zero restarts. That historical job result is distinct from the actual
Production process abort observed after the later combined restart. The bounded
logs also recorded automatic existing VDP 1.0.16 delivery on Test; no VDP was
uploaded, approved or functionally qualified by this lifecycle test.

Unlike the earlier Cycle B harness sequence, the combined-restart status fields
were inspected before any new retirement command. No Cycle C deprovision,
delete or environment retire followed the failed stability gate. Both fresh
Units remain provisioned/Online with their expected role memberships, both
guests and shared DNS remain running, and their overlay/access/journal files
remain in the canonical current-run paths. Original artifact/baseline and all
unrelated resources were unchanged. No forced kill or guest/image/security
change was used.

This reproduces the failure on new identities and fresh disks. The isolated
Production restart passed whereas the subsequent combined restart failed;
that is an observed distinction, not proof that concurrency, shared DNS or a
particular source function caused the abort. Root cause remains unestablished.
Online after automatic restart does not satisfy the zero-restart criterion.

Final read at 08:13:37 UTC (128 seconds after the failed gate) again showed both
Units Online/provisioned with expected memberships and both guests SSH/DNS-ready.
Production CM remained active with NRestarts=1 and the same 6/ABRT record;
Test core services remained active with NRestarts=0. No further CM restart was
observed in that interval. No mutation followed the failed gate.

93 isolated package tests and 12 contract tests passed in this turn. An initial
sandboxed package invocation had four PermissionError failures on fixture Unix
socket bind; rerunning with local socket permission passed all 93, with no
source change. These fixture results do not override the reproduced live failure.
No lifecycle source was edited, no build was performed and nothing was committed
or pushed. New-cycle reverse peer retirement, final cleanup and empty-cleanup
repeat remain unrun because the failing runtime is preserved. Therefore this
is not a completed end-to-end qualification or a claim that the old CM defect
has been fixed.

Documentation quality and whitespace gates passed after this record update.

## Cycle C Root-Cause Analysis — Concurrent CM Stream Writes

Read-only democtl observations at 08:42:34 and 08:45:55 UTC recovered the exact
gRPC error GRPC_CALL_ERROR_TOO_MANY_OPERATIONS, followed by assertion failed:
false at call_op_set.h:977 (API-misuse report at line 975). The existing journal
backtrace, not a core-memory extraction, contained this causal call path:

Communication::ConnectToCloud -> NotifyConnectionEstablished ->
SMController::OnConnect -> SMHandler::SendCloudConnectionStatus ->
SMHandler::SendMessage -> gRPC assertion -> abort.

Immediately preceding it, the same boot logged Get node configuration status
at 13.863573 s and Send cloud status at 13.863605 s. The 32-microsecond spacing
is log timing, not a measured duration of either Write. The call stack proves
the aborting writer was the Cloud-status notification inside the CM process.
This is not two different VMs sharing one gRPC stream.

Both guest executables reported Aos CM v9.1.0-1-g9eec and the same executable
SHA-256 e55f0c8a506587bc9ba1772f721887d7ba73e56bb026af35035a8d98cc833f21.
The [pinned meta-aos CM recipe](https://github.com/AosEdge/meta-aos/blob/176da6346b1199f854106dede4cc49604174619c/recipes-aos/aos-communicationmanager/aos-communicationmanager_git.bb)
selects AosCore 9eecb80c4994937b5c8cbe0464970f81e8ad4c2d. Its stock executable
is aos_cm_app; this is CM provenance, not an inferred Service Manager version.
The Platform source tree recorded for .27 has no CM recipe override; its
systemd-slot patch belongs to SM. The original .27 build-log limitation recorded
above remains; it is not retroactively replaced with a binary reproducibility claim.

In the [pinned SMHandler](https://github.com/AosEdge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/cm/smcontroller/smhandler.cpp),
SendMessage protects mStream->Write with SMHandler::mMutex. GetNodeConfigStatus
instead calls [SyncMessageSender::SendSync](https://github.com/AosEdge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/common/utils/syncmessagesender.hpp),
which writes to the same stream under a different, private mutex. No common
write lock serializes these two paths. The
[gRPC 1.60.1 check](https://github.com/grpc/grpc/blob/e5ae3b6b44bf3b64d24bfb4b4f82556239b986db/include/grpcpp/impl/call_op_set.h#L971)
explicitly treats overlapping writes on the same RPC as API misuse and aborts.
The observed code, stack, adjacent request and pinned source therefore identify
the concurrent-write defect; DNS or Cloud provisioning repair is not the fix.

Upstream already has the exact correction:
[6e0b1980e71ea6ee9979292a8aa336574d317f09](https://github.com/AosEdge/aos_core_cpp/commit/6e0b1980e71ea6ee9979292a8aa336574d317f09),
with the same change also recorded as cf75a8f783f3962fff86667ed162ee5742cb105d.
It introduces one shared write mutex for SMHandler and SyncMessageSender while
keeping response bookkeeping/wait synchronization separate. The fix is absent
from pinned 9eecb80. This supports a bounded CM backport; it is not a justification
to update all AosCore components or insert host startup sleeps.

Combined VM launch changes scheduling and plausibly exposes this race; the
precise host timing trigger has not been isolated. The same defect can occur
in a single VM whenever the two CM writers overlap. A successful isolated start
does not prove immunity, and automatic recovery does not prove the fix works.

Only the host-side read-only status projection and its regression tests were
extended. No CM/SM, guest configuration, security policy or lifecycle source was
changed; no VM restart, SDK action, Cloud mutation, Builder start or image build
occurred during this analysis. Both Units remained Online with correct role
membership at 08:45:55 UTC; Production CM NRestarts=1 and Test NRestarts=0.
No raw journal payload/core memory or credential content was retained. The
temporary official-source checkout at /private/tmp/aos-cm-source.Cyb8Bj (8.2 MiB)
is deliberately retained for the proposed bounded follow-up. No commit/push.

Next, subject to the CM/Platform change boundary: backport the reviewed upstream
write-serialization fix, compile only CM, run focused concurrent-writer tests,
then prove it on the disposable target before a formal image build. The actual
fix and live post-fix qualification have **not** been performed in this diagnosis.

## Authorized CM fix and factory successor — 2026-09-05

The subsequent user authorization covered taking the exact upstream fix,
testing it, and building a new Factory Image after the proof passed. A later
authorization permits .27 cleanup only after .28 has passed acceptance.

The concurrent-writer regression reproduced the original abort on its first
execution (exit 134, GRPC_CALL_ERROR_TOO_MANY_OPERATIONS at call_op_set.h:975/977).
After the unchanged upstream backport, the same test passed 100 repetitions;
all 20 SMController tests passed. That native test cache uses gRPC 1.54.3.
The separate production-compatible Yocto CM build uses gRPC 1.60.1 and passed
the target-only compile gate without an image build.

Both existing Cycle C VMs then ran the hash-verified CM through a temporary
/run ExecStart override, with unchanged flags, owner/mode, bin_t exec label
and SELinux Enforcing. Both completed the CM/SM node-configuration handshake
and Cloud connection with no fresh AVC or gRPC assertion. At 09:27:51 UTC,
democtl status reported both original Units Online, correct role membership,
CM active/running, Result=success and NRestarts=0. No Cloud mutation or
reprovisioning was used. The one-time binary deployment was a direct SSH
debug action, not a new democtl feature; acceptance observations used democtl.

Source checkpoint: aos-vehicle-platform e0a0d101a58a9aaec5123ff9eda4e0459f5db62d,
tree 5525a8f4639a293dbc68ffe9ec3a49562dffa65b, based exactly on .27 source
72c0224ba65537bed41a6ca12a7bf3a9c07da194. Its only product change is a CM
recipe append applying upstream 6e0b1980; accompanying files document and test
the regression. The 21 existing R6.1 layer tests and layer validator passed.
Commit is local; no source push or binary publication to Git occurred.

Factory .28 package QA and image QA passed using the retained offline Builder,
download and sstate caches. Package build: 6223 tasks, 6140 reused (its dependency
graph also built initramfs/kernel outputs). Image build: 7549 tasks, 7533 reused.
The resulting six-partition disk is 6997147648 bytes, SHA-256
5154a312598e3712666e27573adee149a730c1816d712f6cdb77bddb3f54da01. Its os-release
reports 6.1.1-maninblack.28. Host transfer SHA matched; artifact and manifest are
under demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.28.

Packaged CM SHA is b287d4c30fd2c7b8c5aea240e86f90c1534f37e6d5e02c2042b058f748aecab1;
its .text and .rodata match the live-proof binary exactly. Different packaging
debug metadata means its whole-file SHA differs from the transient binary
a376b824444a282baa1bbd2dbc0ade42eb055b7335467860ffd84970c83f74cd.
The selected AosCore API v9.1.0/v9.1.1 tags have identical source trees
0bf4d8957355f2f0f33844452afbbdc3612ac19a; the build introduces no API source update.

Cycle C .27 VMs were stopped through democtl (Test 4.41 s, Production 5.27 s).
Their /run-only overrides disappeared with shutdown; original on-disk CM,
overlays and Cloud identities remain. Builder is stopped after artifact transfer.

Fresh .28 qualification runs the exact same CLI source bytes in the isolated
directory $WORKSPACE_ROOT/aosedge-sdv-demo-qual-28.752zc1. It uses the
existing installed Python environment and a PYTHONPATH pointing to that source
copy, from its apps/demo-orchestrator directory. No lifecycle implementation,
credential copy or journal migration was introduced. This preserves .27 until
.28 acceptance. No .27 artifact or Unit has been deleted.

Fresh create passed; first `democtl vm start all` passed with SSH and DNS ready:
Test 58.4 s, both roles 73.42 s. The subsequent `democtl unit provision all`
returned ROLE_UNIT_SET_HAS_OTHER_UNITS before any SDK or Cloud mutation attempt.
Test Vehicles still contains Cycle C Unit 27e0a9cc-453d-416a-a284-bb1306ebff11;
Production Vehicles contains b5f8465b-1efe-412a-8384-f0a5dc7cd53c. The .28 journal
still has only its successful LOCAL_CREATE operation, with no Unit/Node/Cloud
identity. This is the CLI's exclusive-role-set guard, not a failure of the new CM.

The new instruction to retain .27 until .28 works prevents silently retiring
those old Units now. The next bounded choice is to temporarily remove only
these two old role-set memberships, retaining their Cloud Units, original image
and disks until .28 acceptance. This administrative change needs explicit
agreement; no guard bypass, extra Unit Set, membership mutation or retry was
performed. Both .28 VMs remain running, unprovisioned and ready; .27 VMs and
Builder are stopped. Cloud/restart/full-cycle acceptance and .27 cleanup remain
open and are not claimed as passed.

## Factory .28 Live Qualification — 2026-09-05

The operator authorized removing only the two old Cycle C role memberships.
Both removals returned HTTP 204 and were independently re-read: the old .27
Units stayed provisioned/Offline, other memberships stayed unchanged, and the
two role sets became empty. This was a separate administrative API action,
not a democtl guard bypass or old Unit deletion.

The isolated CLI copy initially omitted scripts/host/aos-prov-5.4.2-source-lock.json.
The SDK guard therefore
raised FileNotFoundError before run_provision_v6, while democtl had already
journaled its mutation intent. Restoring the exact existing source-lock file
required no image rebuild or SDK change. After fresh authenticated inventory
absence, both guests still unprovisioned/DNS-ready, and separate explicit user
confirmation, attempt 76c22e23-c8da-44ba-9f89-dccf9fb98d57 was classified
NOT_APPLIED and released under the run writer lock. Its compact reconciliation
record is retained outside the current-run journal. No SDK retry was attempted
while the old outcome remained uncertain. This was a one-time authorized
journal recovery, not a new public CLI repair command.

Subsequent live lifecycle operations used democtl from the isolated
apps/demo-orchestrator directory:

| Check | Observed result |
| --- | --- |
| unit provision all | One SDK call per role; Test final inventory read returned HTTP 503 after successful assignment (42.75 s); Production completed in 49.45 s |
| status all at 10:30:49 UTC | Both Online, correct role memberships, normal IAM/SM/CM, zero restarts; packaged CM SHA matches .28 manifest |
| unit provision all, explicit continuation/idempotence | Both COMPLETED, same Unit/Node/systemUID, cloudMutationsStarted=false; Test 14.77 s, Production 14.49 s |
| vm stop all | Both COMPLETED; Test 3.82 s, Production 4.63 s |
| vm start all | Both COMPLETED; Test 24.87 s, both ready by 26.16 s; existing SSH enrollment/DNS reused |
| status all at 10:41:15 UTC | Both Online, same role memberships, CM zero restarts, no local abort/gRPC assertion, SELinux Enforcing, kernel AVC=0 |
| vm stop production; status all | Stop 4.12 s; Production Offline/stopped, Test remained Online with CM zero restarts |
| vm start production; status all | Start 23.22 s; both Online at 10:43:45 UTC, IAM/SM/CM zero restarts, kernel AVC=0 |
| vm stop test; status all | Stop 4.14 s; Test Offline/stopped, Production remained Online with CM zero restarts |
| vm start test; status all | Start 23.77 s; both Online at 10:45:21 UTC, IAM/SM/CM zero restarts, kernel AVC=0 |

Test Unit: dac767d5-5fc6-45bb-b20d-b08669a71da7; Main Node:
676aeda1-26ce-4b46-ad49-d8d74a3120fb; systemUID:
86bdffdabe7a432292b18e7ed3013784. Production Unit:
ce482c27-e957-4fca-9c2d-552839652a51; Main Node:
c6784e13-f785-4ab4-9682-7fa8ffd49549; systemUID:
9a05abd5a59648d6a713f74c68208bf6.

One host-diagnostic defect was localized without changing or restarting CM:
the classifier initially counted two strings Main process exited/6/ABRT inside
payload-bearing CM messages as local service exits. Both records were proved
embeddedPayload=true and systemdCmExitLine=false. Payload records are now
excluded before every failure/signature classification, not just redacted
excerpts; fixtures still require genuine systemd exits and gRPC assertions to
be reported. This does not reinterpret the earlier .27 failure, which had a
real restart and independently proven source/stack/regression evidence.

Status also projects only SELinux mode, kernel-journal query result, record
count and AVC-denial count for the current boot. Missing evidence is not zero
denials; raw kernel records are never returned. These read-only host changes
are identical in the main CLI and qualification source copies. All 98 package
tests passed, including payload false-positive and secret-redaction regressions.
No guest/image/security policy or lifecycle implementation was changed.

This is VM/Cloud lifecycle qualification, not CARLA/VDP functional or complete
scenario R0 acceptance. Existing VDP 1.0.16 was automatically delivered to Test;
no new bundle was signed/uploaded/approved. The Cloud 503 continuation is
recorded as such and is not called a clean first-pass provisioning result.
Combined unit deprovision all then passed: Test 115.48 s, Production 118.36 s,
both new/Offline and both VMs stopped. This run still included the old-identity
probe, before its removal below. unit delete all passed (26.20 / 26.21 s), with
both Units/Nodes absent and role sets empty. environment retire passed: the two
qualification overlays, access material, working factory copy/manifest and run
journal were deleted without backup; the immutable original .28 was preserved.
No .27 Unit, image or overlay was deleted in this cycle.

### Operator Amendment: No Old-Identity Probe in Future CLI Runs

The operator explicitly requested removing this redundant Cloud-feature test.
The implementation now stops after authoritative Cloud new/Offline and normal
VM shutdown, without restarting CM or reading rejection logs. Delete and local
retire no longer require the oldIdentityRejected flag. Existing historical
probe fields cannot trigger a reconnect. The current contract is 1.6.0.
Fixtures cover deprovision without reconnect/log queries, deletion without the
flag, cleanup without the flag, and unchanged authoritative-absence/ownership
guards. No new VM or Cloud cycle was launched merely to test this removal;
the timings above describe the former probe-enabled path, not the new path.

### Subsequent Authorized .27 Cleanup

The operator then explicitly requested deletion of the remaining .27 copies,
including Cloud. All three old Units were already Offline, so no VM was started.
Direct authenticated OEM API calls deprovisioned and deleted each exact Unit
once (HTTP 204 each), followed by Unit/Node absence and inventory reconciliation:
27e0a9cc-453d-416a-a284-bb1306ebff11,
b5f8465b-1efe-412a-8384-f0a5dc7cd53c and
70e48e60-de2b-444b-a961-258683f324c4. The final Unit inventory was empty;
components, bundles, persistent Unit Sets and Campaign definitions were not
mutation targets. No old-identity probe was performed.

After stopped-owner and unheld-file proof, cleanup removed the two Cycle C
overlays, the earlier accepted-demo overlay, the working .27 factory copy and
the original .27 image, children before backing images. Allocated disk bytes
removed: 16490954752 (15.36 GiB). Their per-run access/runtime material, obsolete
observation profile, current journal and stale PID were removed without backup.
The current-run writer-lock inode remains available for future CLI use.
The .28 image identity was unchanged, and image list now shows only .28.

No Git history or source branch was deleted: both ltvp-finalize-27 source branches
still contain VDP/qualification changes absent from main. Their source worktrees
and compact qualification evidence are retained; they are not runnable .27 VM
copies. Builder/download/sstate caches, VDP artifacts and the .28 CM-fix source
were preserved. The compact cleanup receipt lives beside the .28 artifact as
retired-27.json. This administrative cleanup was not an extra CLI qualification
cycle and did not create a replacement live environment.
