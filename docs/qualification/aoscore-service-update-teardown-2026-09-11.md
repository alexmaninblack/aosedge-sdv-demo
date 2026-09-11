<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore service replacement: SM patch and remaining CM blocker

Date: 11 September 2026. Status: **native regressions passed; live 3.0.0 to
4.0.0 transition not qualified; upstream publication withheld**.

## Authorized scope

The user authorized the proposed SM/runtime patch, targeted compilation and
verification on the existing Test, followed by upstream review only if it
works. This is a bounded exception to the earlier unchanged-SM diagnostic
boundary, not a new Factory image or general runtime architecture change.
Production, Cloud assignments, service packages, Subjects, VM identity and
native persistent databases remain unchanged. No successor service release
or VM/CM restart was performed.

## Local source checkpoints

| Repository | Base | Local patch commit |
| --- | --- | --- |
| aos_core_cpp | 9eecb80c4994937b5c8cbe0464970f81e8ad4c2d | da50b60b7d72208bf17ad51250d24dbc727bc679 |
| aos_core_lib_cpp | 60cb83535f773762c61ac5f544b31b7b88c502e3 | 4b8d38eedb3521fe03883666aa61ffab3f71a072 |
| aos-vehicle-platform | 205f89d4a60965d962552abe3812c7ff8d527655 | 1243780d292eacf463f6a8c79075915565b51927 |

Both native repositories use local `codex/service-update-teardown` branches
under the ignored Platform `build/` directory. Nothing was pushed and no PR
was created. The Platform recipe carries the two patches against the pinned
native and shared-library sources; it does not modify the accepted .31 image.

Changes:

- Native crun cleanup classifies ESRCH on stop as already absent, and ENOENT
  only when the exact container state directory is absent. Delete still runs;
  access, I/O and invalid-argument failures are not globally suppressed.
- Bridge detach accepts the interface adapter's typed not-found result.
  Namespace cleanup accepts EINVAL only for an empty, regular, unmounted
  placeholder outside the namespace filesystem; real mount errors remain.
- Shared SM launcher marks service removal inactive only after successful
  teardown, retains failures, does not restart a retained old identity for a
  different desired version, and preserves images referenced by survivors.
- Demo Control's existing SM build/test/apply commands carry this exact proof.
  Apply validates the original Test/binary, preserves durable VDP state, and
  performs one stop/start without blind retry or database deletion.

## Executed gates

| Gate | Result |
| --- | --- |
| SM recipe compile, ARM64 | Passed; no package/image construction |
| Shared launcher suite | 20 passed, including successful replacement, stop failure and network failure |
| Native container suite | 13 passed, including absent process/state and preserved real errors |
| Bridge/namespace suite | 12 passed, including a real test namespace mount/unmount on the isolated Builder |
| Existing VDP/Safe Stop regressions | 29 passed |
| Demo Control SM tests | 21 passed |

No selected native test was skipped. Initial build/test-integration failures
were corrected before live application: a field name, test link dependency,
external-library test discovery, build-tool selection and target-loader
discovery. The standalone library test configure initially fetched its default
MbedTLS test dependency; final qualification disables unused crypto and uses
`FETCHCONTENT_FULLY_DISCONNECTED=ON`. The SM recipe itself remained offline.
No credentials or generated fixture material entered Git.

The immutable proof artifact is outside Git at
`demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-service-update-teardown/`.
It contains the executable, manifest and test log. Executable SHA-256:
`3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21`.
The manifest's `guestApplied: false` describes export time; the authoritative
live application receipt is `smServiceUpdateProof` in the environment journal.
Builder was stopped after each attempt and is stopped at this checkpoint.

## Live evidence

`democtl component sm-apply test` completed at approximately 16:11 UTC:

- Test VM `d53d05cd-4c46-49c9-a896-534b23b88273`, Cloud Unit
  `2a29c145-bbd1-4494-a0e5-d4b79e6a9db5` unchanged.
- SM PID changed from 171280 to 181284; the effective binary matches the
  qualified SHA above. Active/success, zero automatic restarts.
- VDP18.0.0 remains active in slot A with its pre-existing restart count one.
- CM remains active with zero automatic restarts.
- SELinux remains Enforcing; the complete kernel audit window since this SM
  start contains zero denied events.

The transient binary is deliberately retained at
`/run/democtl-sm-service-update/aos_sm_app`. The existing owned
`/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf`
now bind-mounts it over the service's executable path. The prior proof binary
and immutable rootfs remain available. No rollback or reboot was attempted.

**Service transition did not occur.** Startup restores saved Brake/Tire 3.0.0
records. Brake briefly starts then exits in the known unauthorized bootstrap
mode. Tire proceeds past the earlier namespace EINVAL but still uses its old
32-file quota and fails at `crunrunner.cpp:86` with Too many open files.
Observation shows both old five-argument OCI configurations and no live
bootstrap processes. These are not 4.0.0 runtime results.

Cloud still projects Brake installed 3.0.0 / pending 4.0.0 and Tire pending
4.0.0 with a failed instance. Image-installed and instance-version projections
are not evidence that the new bootstrap ran.

## Source-confirmed reconciliation blocker

At 16:11:06.905 UTC, CM receives the five-item node status snapshot, including
Brake active 3.0.0 and Tire failed 3.0.0. It then logs:

`Failed to process message ... not found (instancemanager.cpp:198)`

The pinned shared-library code explains the failure without assuming a Cloud
delivery problem:

1. `InstanceManager::UpdateStatus` looks up active instances by identity **and
   version**. An old active/failed 3.0.0 report has no matching desired 4.0.0
   entry and returns not-found; only inactive unmatched reports are ignored.
2. `UpdateRunningInstances` first records the received running snapshot, then
   propagates the first `UpdateStatus` error.
3. `Launcher::OnNodeInstancesStatusesReceived` returns on that error before
   updating projected statuses, enqueueing the node in `mUpdatedNodes`, and
   notifying the resend worker.
4. `Node::ResendInstances` already compares versions and can produce the
   stop-old/start-desired request, but the failed callback does not reach that
   scheduling path. No new 4.0.0 update request was observed after replacement.

Thus the SM replacement patch has passed its native tests but has not yet
received a live 3-to-4 request with which to qualify the end-to-end fix.

## Next boundary, not implemented

A bounded CM fix should treat an unexpected version in a valid full node
snapshot as reconciliation input, not a fatal status-ingestion error. Keep
desired version/Subject authority unchanged, do not label old 3.0.0 as 4.0.0,
and retain real snapshot/storage errors. Add a CM regression with desired 4
and reported old active/failed 3, proving exactly one stop-old/start-4 request.
Then compile/apply only the affected CM target and repeat the existing-release
Test observation. This additional CM patch/restart requires agreement beyond
the proposed SM-only proof; it has not been performed.

Do not publish the current patch as an E2E-qualified upstream fix. Full N6
authenticated KUKSA/telemetry/advisory remains separately excluded by the
agreed permission-free, no-telemetry service experiment.
