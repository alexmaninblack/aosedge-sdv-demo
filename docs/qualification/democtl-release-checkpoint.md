<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control Source Checkpoint and Next Factory Release

- Status: authorized Factory .30 build in progress; operator E2E not yet ready
- Version: 0.2
- Prepared: 2026-09-06
- Owner: Demo Solution Team
- Design: [Demo Control](../architecture/demo-control.md)
- Evidence: [VDP family checkpoint](democtl-vdp-family.md)

## What is demonstrated

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
and 15 source-operation tests pass. ARM64 configuration tests, package/image
build and clean-VM E2E are still running or pending; no clean-release success
is claimed. The build is invoked with `democtl image build 6.1.1-maninblack.30`.

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
