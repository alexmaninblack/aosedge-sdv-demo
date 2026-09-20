<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Continuous lifecycle: Presenter verification

Date: 19 September 2026. Scope: accepted [ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md).
This is UI/command-boundary verification, not a completed clean E2E cycle.

## Implementation

- Session no longer offers Park or Resume. The pause instruction uses native
  Safe Stop and keeps the controller running; Finish precedes shutdown.
- Historical Park, partial Resume and an established stopped controller offer
  confirmed Finish. Publication/assignment/reset actions are unavailable while
  that interrupted run must be retired. Partial Create retains its legitimate
  preparation continuation. Historical completed Resume with a running VM is
  readable and is not relabelled as a new interruption.
- The fixed Presenter command dispatcher rejects both retired action names.
  An older browser cannot invoke the privileged worker through that endpoint.
- CLI environment Park/Resume primitives remain engineering-only. Parent and
  action-specific help warn about the known AosCore storage-retention defect.
- No native CM/SM/IAM code, Factory image or model/conflict policy changed.

## Executed gates

| Gate | Result |
| --- | --- |
| Presenter UI unit suite | 224 passed |
| TypeScript and production Vite build | Passed |
| Browser suite, including four historical interruption cases | 112 passed |
| Presenter operation tests, including retired HTTP actions never forwarded | 17 passed |
| Demo lifecycle unit tests | 35 passed |
| Presenter HTTP reader tests | 12 passed |
| CLI tests | 7 passed |
| Documentation quality / whitespace checks | Passed |

The initial HTTP reader attempt could not bind its isolated loopback port
inside the sandbox; rerunning with that local test capability passed all
12 cases. This was a test-environment refusal before application execution,
not a repaired application failure.

## Activation and live read-only check

At approximately 08:13 UTC, the existing idle Presenter was stopped through
its ownership/active-operation guarded `ui stop` and started once with the
new code/assets. Only the Presenter server changed. VM, CARLA, native controls,
backend containers, Cloud identity and service processes were not restarted.
The open browser's Reload UI action loaded the new build.

The live Session contains the new pause instruction and Finish, with no
Park/Resume controls. Opening Finish displayed the exact cleanup scope and
permanent/no-backup warning; Cancel returned to Vehicle without an operation.
The operations reader reported no active or uncertain action. The same run
`ac456637-7e30-474f-be40-5716f944a21b` remained, Test VM RUNNING; Cloud displayed
Online with VDP79, Brake60 and Tire35 and no pending updates. Production stayed
stopped/excluded. This is preserved-state verification, not proof of repaired
service model/function state after the earlier native CM data loss.

## Upstream reproduction and remaining gate

The [handoff](aoscore-shared-storage-handoff-2026-09-19.md) and test-only patch
are retained in the project. Patch reverse-check against the proof checkout
passed. The relocatable checked-in CMake harness was configured, built and run
again in a network-disabled Linux ARM64 container: 17 original cases passed;
both added retention assertions failed as expected. CTest's failing exit is
the reproduced product defect, not a claim that all upstream tests passed.
No native fix was built or deployed and no report was posted upstream.

The current damaged Test is preserved pending explicit scoped Finish approval.
Its Unit, Subject bindings, local VM working files and backend run data have
not been deleted. Clean Create/profile transitions/manual-off-road/offline/
Finish acceptance remains open. The existing `.35` and release continuity
remain preserved; no successor Factory is justified by these UI-only changes.
