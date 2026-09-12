<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore service replacement: SM/CM patches and live update proof

Date: 11 September 2026. Status: **native regressions and Test service
replacement passed in explicit no-telemetry mode**. Full authenticated
KUKSA, analytics and advisory qualification remains open.

## Current recovery follow-up — 12 September 2026

After an authorized .31 VM reboot lost the temporary manager/resource overrides,
the prior SM/CM fixes were restored. A further SM same-service preparation
retry defect was reproduced, patched and qualified: 77 native tests passed,
and the existing Brake 7.0.0 / Tire 6.0.0 packages now run and deliver isolated
mock records to their real backends. See the [complete recovery evidence and
remaining image gate](demo-mocked-backend-integration.md#runtime-recovery-2026-09-12).
This follow-up does not retroactively qualify cold boot of the immutable .31
image or authenticated KUKSA/advisory functionality.

## Service-update result — 11 September, 21:16 UTC

The user authorized continuation without parking, the additional CM patch,
and the service update scenarios. The original SM-only checkpoint below is
historical. At 21:08 UTC `democtl component cm-apply test` applied the qualified
CM executable with exactly one CM restart. SM PID 181284 and durable VDP18
records were preserved; CM PID became 183405. No VM restart, reset,
reprovisioning, native database deletion, assignment change or Production
mutation was required.

CM now retains unexpected old-version statuses in the observed node snapshot
for reconciliation, without attributing them to the desired version. Cross-node
snapshots are rejected before mutation; genuine known-instance/storage errors
still propagate. The existing native resend path issues stop-old/start-desired.
The patch does not introduce another scheduler or Cloud authority.

| Gate | Observed result |
| --- | --- |
| Targeted CM ARM64 compile | Passed; no package/image build |
| Native CM tests | 4 passed: existing service update/resend, old Active and Failed version reconciliation; cross-node and storage-error negatives included |
| Demo Control runtime tests | 25 passed, including one-CM-restart, no blind retry, repeat no-op and wrong-target/binary rejection |
| Both services 3.0.0 → 4.0.0 | Native stop-old/start-4 and Active observed; Cloud installed 4 with Active instance and no pending version |
| Brake 4.0.0/v1 → 5.0.0/v2 | Cloud installed 5, Active; Tire remained Active 4 |
| Brake 5.0.0/v2 → 6.0.0/v3 | Cloud installed 6, Active; Tire remained Active 4 |
| Tire 4.0.0 → 5.0.0 (v1 content) | Cloud installed 5, Active; Brake remained Active 6 |
| Final guest observation | Both native bootstrap processes alive; new six-argument command/1024-file-limit package configuration |

All successor operations used `democtl service build/prepare/sign/upload`.
Version allocation remained automatic. There was no second Deploy, Subject
reassignment, batch approval or manager restart between service releases.
The same two per-service Group Subjects and current Test Unit were retained.
No Tire v2/v3 profile is claimed: Tire's accepted product export is v1 only.
The v2/v3 Brake binaries were packaged, but no-telemetry mode does not execute
the analytic child, so this proves replacement, not those algorithms.

CM shared-library source checkpoint: `0b82a6bf` on top of SM `4b8d38ee`.
Platform CM recipe checkpoint: `1c901cf75fb834b5c93224d846660b91137dd126`.
It preserves the existing serialized SM-stream-write backport and adds the
CM reconciliation patch against pinned library/API sources. A fixture-only
access correction reused the compiled manager after exact production-source
comparison; the final native tests were rebuilt and passed.

CM artifact outside Git:
`demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-service-update-reconcile/`.
Executable SHA-256:
`1ee6ad0a821de89c40b4b108b25b89b8afe338fdced9b0cd6a678df0b9f93936`.
The binary and test manifest are deliberately retained; Builder stopped after
qualification. Runtime proof files are `/run/democtl-cm-service-update/aos_cm_app`
and `/run/systemd/system/aos-cm.service.d/93-democtl-service-reconcile.conf`.
They are transient and are not part of immutable Factory .31. SM proof paths
below remain active. No new factory image or reboot qualification is claimed.

Successor Deployment Bundles:

- Brake 5.0.0: `42ca2e46-78e9-4b99-875c-482a57130b5a`.
- Brake 6.0.0: `1945ce25-74ce-4b4b-b0d8-55f22debf9f4`.
- Tire 5.0.0: `c79222cf-64e7-48a6-9001-94e55956f22b`.

The user's next authorized increment is explicitly mocked data generated
inside services, sent to real team backends. That is a separate backend
integration proof and must not masquerade as KUKSA telemetry or close native
authentication, vehicle analytics or advisory acceptance.

Final manager/security observation: SM PID 181284 and CM PID 183405 remained
active/success with `NRestarts=0`. SELinux remained Enforcing. The complete
kernel audit window since SM start contained zero denied events (232 entries
scanned); no policy was relaxed. No demo/runtime cleanup was requested or done.

Upstream review is a separate remaining step: a fresh read of official main
found 9.1.2 with substantial container, launcher and network reconciliation
changes since the tested 9.1.0 pins, including related absent-process handling.
Do not submit this baseline-specific patch as if reproduced against current
main, or silently upgrade the working Test. First compare the remaining delta
against current upstream. No upstream PR or push was performed at this gate.

### Upstream source comparison — 12 September 2026

Compared the fetched official 9.1.2 snapshots (Core `a46d1cba`, shared library
`5560291b`) without modifying the tested pins or live VM:

| Tested failure boundary | Current upstream source | Disposition |
| --- | --- | --- |
| CM rejects old/unassigned Active status before resend | Shared-library `f95d155e` changes `UpdateStatus` to warn when the active/status entry is missing while still returning real update errors | The principal status-ingestion fix is already upstream; do not open a duplicate patch against main |
| crun missing process becomes fatal teardown | Core `34eb0acc` maps ESRCH to typed not-found; current launcher accepts runtime not-found | Related resolution already upstream; our narrower pinned implementation is not a direct main patch |
| Stop marks inactive before asynchronous task succeeds | Shared-library `9eb7d42e` moves status handling into the task and waits for the pool | Substantially refactored; baseline hunk is not applicable unchanged |
| Absent bridge interface and unmounted namespace placeholder | Current `BridgeNetwork::Detach` still propagates all delete errors; `DeleteNetworkNamespace` still fails on unsuccessful unmount | Residual source concern; reproduce against current upstream before proposing review changes |
| Retain failed teardown ownership/image references | Current stop/network/remove sequence differs from the pinned launcher | Requires current-main regression; not claimed fixed or reproduced by the .31 live proof |

This comparison does not qualify a 9.1.2 image and does not authorize replacing
the currently diagnosed VM. Keep the proven backports in the Platform source;
upstream review should contain only a reproduced residual delta, not the whole
baseline-specific patch or a claim that current main has the same failure.

## Historical SM-only checkpoint

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

## Historical next boundary at the SM-only checkpoint

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
