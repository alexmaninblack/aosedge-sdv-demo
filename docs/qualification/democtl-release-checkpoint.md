<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control Source Checkpoint and Next Factory Release

- Status: Live .30 correction proved; demo environments retired; clean Factory .31 not built yet
- Version: 0.5
- Prepared: 2026-09-06
- Owner: Demo Solution Team
- Design: [Demo Control](../architecture/demo-control.md)
- Evidence: [VDP family checkpoint](democtl-vdp-family.md)

## What is demonstrated

### Authorized Factory .31 execution — 2026-09-06

Platform main `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` is committed and
pushed, containing the proven factory-placeholder correction and new offline
factory-31.conf. Platform source quality gate passed for 193 files. Demo Control
builds only this pinned revision, runs five native factory/profile regressions
before package/image QA, and retains the warm caches. No provisioned disk,
temporary SM executable or guest credential is an image input.

Agreed next sequence: build/freeze .31 once; fresh Test/Production overlays;
stage VDP 10/v1 before Test provisioning, then 11/v2 and 12/v3 with moving
negative/Safe Stop positive evidence. Operator visual acceptance and a repeat
from fresh overlays of the identical image SHA remain required. This entry is
execution intent, not a claim that .31 build or E2E has passed.

### Pre-.31 environment cleanup — 2026-09-06 06:17 UTC

The user authorized deletion of all current demo VM environments through
Demo Control, and explicitly authorized extending the existing environment
retire implementation for stopped telemetry source outputs/history.
No .31 build or provisioning has started.

`simulation stop` confirmed physical Safe Stop and stopped Controller,
Gateway, keyboard/dashboard group and CARLA. `unit deprovision` followed by
`unit delete` retired these exact identities, with Unit/Node absence and empty
role sets confirmed by authenticated Aos Cloud reads:

| Environment | Role | Deleted Cloud Unit |
| --- | --- | --- |
| isolated .30 | Test | d8aceca5-8044-4f57-8ca3-e8f6dd223a86 |
| isolated .29 | Test | 7cc3327d-b2e2-4db4-8f18-680990773f52 |
| canonical .28 | Test | 4279840f-d81f-410b-abf3-376e69719fc2 |
| canonical .28 | Production | 766f8fcc-e733-4d1c-a928-fb25176a2f4f |

The two older stopped Test VMs were briefly started through `vm start` solely
because the existing deprovision command requires a live guest to disconnect
CM. No new provisioning or update publication occurred. All four VMs and the
canonical owned DNS bridge were then stopped. The borrowed-DNS records in
isolated environments did not acquire or stop that external bridge.

`environment retire` removed four overlays, three local factory copies and
their manifests, four generated SSH access sets, thirteen stopped source-run
directories, empty control directories and the three current-run journals,
without backup. The earlier isolated .28 qualification returned
NO_CURRENT_ENVIRONMENT. Main status now reports Test/Production NOT_CREATED,
source NOT_PREPARED and NO_MANAGED_CURRENT_RUN; a scoped filesystem search
found no remaining current-run journal/overlay/factory-copy files in these
three roots. Final host free space was 284 GiB.

The retire extension uses the existing exact-file intent/recovery mechanism,
checks terminal run receipts and stopped owners, rejects unknown files and
symlinks, and never recursively deletes a source tree. Thirty-five environment
tests passed in 21.077 s; the subsequent borrowed-DNS and exact-retired-send
regressions passed in 1.256 s and 2.548 s. The isolated .29 journal contained
an old UNCERTAIN VDP 2 send to its own deleted Unit. Fresh absence of that exact
Unit allowed discarding the obsolete local send record; delivery was not
claimed and no send/publication was retried. Uncertain global publication
remains blocked. These cleanup source changes are pending, not committed.

Preserved: original immutable Factory artifacts (.28/.29/.30), published VDP
bundles and frozen functional profiles, Cloud release/audit history and Unit
Sets, source repositories/worktrees (including pending SM correction), compact
qualification evidence, credentials, Builder and caches. The prior transient
SM bind/proof on .30 no longer exists because that VM overlay was removed.
This is a clean VM/runtime starting point for .31, not deletion of the reusable
build inputs or of all workspace source copies.

### Moving Test VDP 8 → 9 with Safe Stop — 2026-09-06 05:52 UTC

The preserved .30 Test Unit `d8aceca5-8044-4f57-8ca3-e8f6dd223a86` completed
the next live update with the temporary factory-placeholder SM correction.
All component preparation, signing, publication, approval and guest/Cloud
observations used `democtl` from the isolated .30 demo-orchestrator directory.
The operator selected Autopilot and then Safe Stop in the existing Controller;
no new mode-control interface or standalone helper was introduced.

`component prepare 9.0.0 --profile v3` reused frozen 3.0.0 functional content
with coherent release metadata and 23 read paths. `component sign 9.0.0`
verified RS256 against the configured OEM signing certificate. Signed bundle
SHA-256: `6fa0eec0ebfe2c902c06e98803daa215acc740443e1c4bef07a42c1ac706047f`
(6624628 bytes). Deployment `c08c4189-3bfd-42f8-b524-65b0d1a1551a` is done;
verification batch `9d8c8ecd-2678-4d6a-86ed-10f6bb62dda0` is Valid and approved.
The initial upload execution was rejected before process creation; read-only
confirmation of the Aos-only trust domain and official endpoint cleared that
review. Exactly one upload reached Cloud (HTTP 201).

Negative proof: desired VDP 9 reached CM at 05:50:52.847858 UTC. At
05:51:01.153090 SM was asked to stop VDP 8. A subsequent component observation
showed slot b/version 8/PID 2154 still READY with 15 paths and a remove
transaction in `waiting-for-safe-stop`. At 05:51:59.887 Controller still
reported AUTOPILOT, 19.1197 km/h, brake 0. Thus receiving/approving the update
did not replace the running provider while the vehicle was moving.

After the operator pressed Safe Stop, native events were:

- 05:52:23.307215 UTC: CM accepted VDP 8 inactive.
- 05:52:23.328107: SM called StartInstance for VDP 9.
- 05:52:23.677827: CM entered activating; the full node report kept factory
  VDP 0.0.0 inactive, not activating.
- 05:52:24.602177: CM received VDP 9 active.
- 05:52:24.602382: CM entered finalizing.
- 05:52:24.617942: CM entered none, with VDP 9 installed.

StartInstance-to-update-complete was 1.289835 seconds; activating lasted
0.924555 seconds. No ten-minute timeout occurred in this update. This does
not measure button-to-stop latency: the later Controller observation at
05:52:51.987 confirmed SAFE_STOP, speed 0 and brake 1 on the same run/ego/reset.

Final provider: slot a, version 9.0.0, PID 3255, 23 paths, READY/LIVE/NONE,
NRestarts 0; no transaction or last-failure file. Capability manifest SHA-256:
`21660641d8221329fbb43efc52911213156155703cc1cf6de582021154fc78ee`.
This is provider-reported telemetry readiness, not independent verification
of all 23 consumer values; v3 advisory remains deferred.

Final Cloud: Test Online, installed 9.0.0, pending component null;
component version ID `cc103d0e-ef7d-4b9a-9f2e-fd008ddd33a3`. Production remained
Online at factory 0.0.0, no pending update, unchanged memberships/settings.
SM stayed PID 2864 with NRestarts 0 and the same temporary binary hash below.
SM/CM/provider service results were success; SELinux remained Enforcing with
zero denials in the complete kernel window since SM start. No VM/SM restart,
reprovisioning, image rebuild, Production promotion or backup occurred.

The bounded log projection also contained CM `not found
(instancemanager.cpp:198)` while stopping 8, SM `Remove instance info from
storage failed`, and provider `pthread_getschedparam failed: 1`. These did not
prevent this observed transition but are retained as unclassified diagnostics;
this result is not a claim of error-free logs. No speculative fix was made.

This closes the targeted moving-to-Safe-Stop 8 → 9 proof. Consolidating the
pending correction into a new immutable Factory image and repeating from a
fresh overlay remain separate, uncompleted qualification steps.

### Factory-placeholder correction — 2026-09-06 05:33 UTC

The preserved .30 Test Unit `d8aceca5-8044-4f57-8ca3-e8f6dd223a86` had a stale
preinstalled VDP 0.0.0 instance in activating while the real VDP 8.0.0 was active.
CM WaitInstancesActive consequently timed out at desiredstatushandler.cpp:485.
The trigger was the first source-selection SM restart during VDP 7 installation.

The agreed correction handles the factory marker before transaction conflict
checking, retires it through inactive status when a real release is installed,
and returns failed status on early StartInstance rejection. Demo Control writes
the Test/Production role in vm start before provisioning; source configuration
no longer restarts SM. No CM timeout, Safe Stop policy or VDP payload changed.

`component sm-build test` compiled only SM (1716 tasks, 1708 reused), executed
three ARM64 regressions successfully in 43 ms and stopped Builder. The transient
binary SHA-256 is `a9da669ace53e21a798bf9a9d3fe8988936ae924c7ed9513dd97520a1ae194d7`;
its manifest and tests are under
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/runtime-proofs/sm-factory-placeholder`.
Source is the pending runtime delta on Platform `c3e0858`, not a new Factory image.

One `component sm-apply test` replaced only the binary via
`/run/democtl-sm-factory-placeholder/aos_sm_app` and
`/run/systemd/system/aos-sm.service.d/91-democtl-sm-factory-placeholder.conf`.
The Factory config and persistent public inputs were unchanged. These exact
temporary proof files remain intentionally installed and disappear at VM reboot.

At 05:33:22.742104 UTC CM accepted factory VDP 0.0.0 inactive; at
05:33:22.742111 it entered finalizing; at 05:33:22.828634 it entered none.
The blocked native update finalized in 86.530 ms, without another upload,
provisioning, CM restart or ten-minute wait. VDP 8 remained in slot b, PID 2154,
with its 15-path profile and zero restarts. A later observation reported
NOT_READY/TELEMETRY_DISCONNECTED when the separate Controller session completed
at 05:34:34.915 UTC (configured maximum session duration 3600 seconds).
`simulation stop`, `simulation start`, and `vehicle select test` restored the
source as run `e1e178ac-1975-4eb2-94bf-64bc9f595069`, assignment generation 1.
At 05:41:25 UTC verified VISS frames advanced 1571 to 1573; the following VDP
read confirmed READY/LIVE/NONE, same PID 2154 and zero restarts. Reconnecting
the source preserved SM PID 2864, proving no second SM restart. SM has zero
automatic restarts,
SELinux Enforcing, complete fresh kernel window and zero AVC denials.
Final Cloud read: Test Online/8.0.0 installed, pending component null;
Production Online/factory 0.0.0 with no pending update or membership changes.

The host role fixture and four CLI/API boundary tests pass. The subsequent
moving-to-Safe-Stop update is recorded above. Clean Factory rebuild,
fresh-overlay repeat and full operator E2E remain outstanding; this transient
proof is not Factory qualification. No
Production mutation, source commit/push, image build, cleanup or backup was
performed for this correction.

### Earlier checkpoints

Latest confirmed increment: Test VDP 7.0.0 (v1 content) is READY/LIVE/NONE,
Cloud installed=7.0.0, pending=null. Native Stop returned at
03:48:35.001468 UTC and Start was called at 03:48:35.747153 UTC; the new
installation was committed at 03:48:36.825068 UTC. The native stop-completion
fix is committed in Platform `e5e9ffd`, with seven targeted regressions passing.
The Gateway Traffic Manager port delta is consolidated in main `93459ee`.
These close the earlier Stop/Start and source-consolidation issues below.

Factory .30 source `c3e0858` packages persistent public source inputs and
role selection, with missing/Production role retaining standard freshness.
The new host-side packaging fixture, source fixture, CLI/API boundary tests
and 15 source-operation tests pass. The ARM64 configuration tests pass 2/2
in 2 ms. SM compile passed 1716 tasks (1706 reused); package QA/build passed
6367 tasks (6332 reused); image QA/build passed 7547 tasks (7532 reused).
`democtl image build 6.1.1-maninblack.30` assembled and exported the immutable
6997147648-byte image with SHA-256
`b33165364be8798c05762a5f2523a350167c0865b77ed25e655c65b58cc3791a`.
Transfer digest matched and Builder stopped cleanly. Artifact directory:
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/factory-images/6.1.1-maninblack.30`.

Solution checkpoint `6c831e9` owns the release command, durable source input
integration and associated documentation. An isolated terminal-equivalent
Test environment was created at
`$WORKSPACE_ROOT/aosedge-sdv-demo-qual-30.G9eUof`; it contains a factory copy
and fresh overlay, not the .29 provisioning/SSH state. Local create/start
completed; first boot/enrollment took 60.37 seconds, SSH/DNS are ready and
the unprovisioned state was confirmed. New local Test VM ID is
`7a2d4419-5a37-4838-ab5c-ed0d2792b9e8`. Provisioning and live component E2E
remain in progress; these are not yet operator acceptance results.

The previous .29 Test VM was stopped through Demo Control in 3.99 seconds,
then removed only from Test Vehicles (10.33 seconds). Its disk and Cloud Unit
are retained; other memberships are unchanged. Its expired Controller was
already absent, so simulation stop records physical stop `NOT_OBSERVED`, not
a new successful Safe Stop test. Production remains outside these mutations.

The recorded 2026-09-06 03:05 UTC observation is Test VDP 6.0.0 active,
23-path READY/LIVE/NONE, Cloud installed=6.0.0 and pending=null. Production
was unchanged. This proves the narrowed telemetry update, not complete v3
advisory, mTLS or a clean Factory release. Earlier functional v1/v2 releases
4.0.0 and 5.0.0 reported 7 and 15 paths respectively.

Factory .29 already exists and remains immutable, with SHA-256
`fb6f77cb280b0836ba0979373260af50a9b30cdb1bf9b3365fb6b2f775b2cf6a`.
Its SM is not the temporary demo-5s SM used for the successful latest update.
The next changed Factory image must therefore be .30, not an overwritten .29.

The transient Test SM uses runtime mounts and systemd LoadCredential for the
public CA/binding. It is not reboot-persistent Factory integration. The
demo-5s profile is an explicit Test demo exception; the standard 250 ms
default and Production policy remain unchanged.

## Source boundaries to preserve

- Solution main: Demo Control CLI/API, lifecycle/component operations, tests,
  contracts, documentation and DNS ownership integration.
- Gateway main: Controller orchestration, physical Safe Stop correction and
  UTC acquisition semantics with associated tests and contracts.
- Gateway `codex/ltvp-traffic-manager-order`: actual live native Gateway build
  source, including UTC acquisition changes. This branch explicitly selects
  the Traffic Manager port; canonical main is not yet an exact replacement
  for this build. Consolidate the existing branch delta before claiming a
  reproducible canonical Gateway release.
- Platform `codex/factory-29-vss`: explicit demo-5s configuration/evaluator,
  targeted tests and transient-proof record. This checkpoint does not alter
  the published .29 image and does not fix the Stop/Start lifecycle conflict.

Local source checkpoint commits: Platform `70f91f4`, actual Gateway build
branch `d1838ab`, canonical Gateway/Controller `bbff7f0`. The Solution commit
containing this record captures Demo Control and its associated documentation.
These are engineering checkpoints, not clean-build acceptance tags; no push
was performed.

The earlier recorded test evidence is retained: SM 59 pass / 2 explicit
provider skips, Demo Control 183 local tests pass with a subsequent 41-test
component rerun, and three native Gateway UTC tests pass. These results are
not a claim that every later checkpoint file was independently requalified,
or that the complete combined source has passed a new clean-build E2E.

Generated images, compiled executables, bundles, credentials, runtime journals
and local artifact stores are excluded from source commits. Existing published
bundle identities and immutable artifact hashes are not rewritten.

## Why the update took roughly ten minutes

The observed failed StartInstance at 02:52:17.610 UTC returned
`a different component transaction is already active`. StopInstance had
started an asynchronous remove transaction and returned before it completed;
the native launcher proceeded to StartInstance while that transaction was
still active. The automatic second launch at 03:02:18.272 UTC succeeded.

Pinned AosCore library revision
`60cb83535f773762c61ac5f544b31b7b88c502e3` contains two relevant CM waits:

- `src/core/cm/updatemanager/desiredstatushandler.hpp`: cWaitActiveTimeout,
  ten minutes; WaitInstancesActive waits while an instance is Activating.
- `src/core/cm/launcher/nodemanager.hpp`: cStatusUpdateTimeout, ten minutes;
  scheduled/resend operations wait for node instance statuses.

The source and timestamps establish a native lifecycle/status recovery issue,
not an intentional ten-minute democtl delay or a demonstrated Cloud timer.
They do not uniquely identify which wait was responsible for this particular
retry. Node status notification is attempted even when updating the instance
manager returns an error; do not infer its absence solely from a not-found log.
Do not shorten unrelated timeouts as a substitute for fixing the known
StopInstance/StartInstance transaction contract.

## Authorized next release gates

1. Preserve these source checkpoints and existing proof. Do not rerun already
   passed tests merely to repeat evidence during bookkeeping.
2. Resolve the known StopInstance/StartInstance conflict with one targeted
   asynchronous stop-then-start regression test. Consolidate the Gateway
   build-source delta and durable public CA/binding lifecycle. Do not broaden
   Production access or silently apply the Test-only freshness exception.
3. Build Factory .30 from pinned, committed sources, using retained offline
   build caches. Publish one immutable image and its source/artifact hashes;
   never package a provisioned overlay or copy transient /run state.
4. Engineer E2E exclusively through democtl: fresh environment, provision,
   correct role sets, Online, CARLA/Gateway selection, physical Safe Stop,
   functional v1/v2/v3 delivery and startup, then lifecycle teardown.
   Check the demo profile and public inputs survive the intended VM lifecycle.
5. Operator repeats E2E through documented democtl commands using a fresh
   overlay from the same .30 image SHA, without rebuilding the image.

Proposed component versions are 7.0.0/8.0.0/9.0.0 for engineer v1/v2/v3 and
10.0.0/11.0.0/12.0.0 for the operator repeat, subject to the existing Cloud
release state when the agreed cycle starts. Version progression is monotonic;
functional content is reused. Stage and approve the next v1-content release
before a fresh Unit joins the delivery set, so Cloud's latest release does not
skip the initial v1 stage. All preparation/signing/upload/approval uses democtl.

The operator authorized the above release plan and the StopInstance contract
correction. Continue the remaining build/E2E gates through Demo Control. No
Production mutation or push is implied by this checkpoint.
