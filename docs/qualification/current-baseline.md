<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current Accepted Baseline

- Recorded: 2026-08-16
- Scope: running Units, local rootfs candidate, and accepted provider component
- Cloud mutation status: none for candidate `.11` or provider `0.2.0`

## Running Units

| Unit role | Boot | Rootfs | Provider assignment |
| --- | --- | --- | --- |
| validation | `6.1.0` | `6.1.1-maninblack.2` | none |
| demonstration | `6.1.0` | `6.1.1-maninblack.1` | accepted operational baseline; no provider assigned |

Both Units retain their existing provisioned identities. No deprovisioning or
reprovisioning is required. The demonstration Unit activated a previously
staged `.1` slot during the guarded repository-rename restart. End-to-end
acceptance confirmed it as the current operational demonstration baseline. The
decision does not approve the stale Verification Batch, make `.1` a rollout
candidate, or change the qualification requirements for its successor. See the
[acceptance record](pre-cleanup-e2e-acceptance.md) and
[repair record](repository-rename-vm-repair.md).

### Host lifecycle-control caveat recorded 2026-08-18

Both Unit QEMU processes and their loopback DNS bridges remain running, but
their repository-local `.run` PID and QMP/serial socket paths were removed
while the processes were alive. The overlays and provisioning locks remain
present and must not be reset, copied or reprovisioned. The lifecycle helper
now rejects this state instead of reporting the VM as stopped.

Recovery requires a controlled maintenance window: verify the exact QEMU,
overlay, Unit identity and Cloud state; request a clean shutdown inside each
guest; prove the old processes exited and the overlays are consistent; then
start each VM through its normal lifecycle helper and rerun status, smoke and
Cloud-online checks. This is a host control-state repair, not deprovisioning or
identity replacement. Until that window is explicitly authorized, both VMs
remain online and no lifecycle mutation is permitted.

## Rootfs Candidate `.11`

| Item | Accepted value |
| --- | --- |
| Platform build revision | `a12c0aa7f8a680b35407776b12bcc025970abc73` |
| Raw image size | `6,997,147,648` bytes |
| Raw image SHA-256 | `946a296b7200644bc529080f3512712d8b7ec97dedad520146a4f503cf4006a2` |
| FOTA manifest SHA-256 | `b9b49a575798f2bc4a532a794e77352ed21596677ef5aced4304db9e7a87f09e` |
| Moulin graph SHA-256 | `08bb15d68e32cbfce1825563e8207e84c1e3b584d9a48c266338f2c242ca867e` |
| FOTA config SHA-256 | `9bceee031f31e3c0ec3afe2453c51213282d96ca2ed3b2139965038d4a4506b3` |
| Rootfs payload size | `128,528,384` bytes |
| Rootfs payload SHA-256 | `e30406f600ada77568d21178e656a34f444973bf121f5a0b537e24efde8ab9d7` |
| Candidate metadata SHA-256 | `56c109c30ab1111ba23dffe45634dbd556298f55da79782d867c3ac6be911aa6` |

The candidate contains only the full rootfs payload. Boot and incremental
rootfs artifacts are absent. The accepted payload is frozen, unsigned, and has
not been uploaded, assigned, or installed.

## Provider `0.2.0`

| Item | Accepted value |
| --- | --- |
| Source revision | `e972d2bd7f14e27646bb5d7c10c7186ecdecfa9f` |
| Layer SHA-256 | `baf1c29c9264b8f2422dc155540c3b22716bb43d5f80c1cfeb3cc9529f0bf3cb` |
| Signed bundle size | `6,599,930` bytes |
| Signed bundle SHA-256 | `30802d1bcb88a5954cf1e9c6c17573b527efe4f2a62ca3c0c83459f8a2fe35db` |

The exact provider candidate is signed and locally verified. It has not been
published to the component catalog or assigned to a Unit.

## Qualified Behavior

Candidate `.11` passed clean AArch64 boot, read-only root, SELinux Enforcing,
component runtime, nested-store, fixed non-root identity, empty capability,
systemd credential, hostname DNS, gRPC random-device, soft KUKSA dependency,
process recovery, invalid-credential fail-closed, DNS/TLS fail-safe, and
secret-exclusion gates.

The 512 MiB nested ext4 store is a bounded demonstration backend inside the
encrypted Aos workdirs volume. It preserves the provider SELinux boundary but
does not select the production vehicle storage architecture.

## Preserved Local Build State

The isolated Yocto builder disk and caches remain outside Git and should be
kept for incremental follow-up builds. VM images, overlays, signed artifacts,
certificates, Unit identities, and raw logs must never be committed.

The reviewed local artifact cleanup recovered approximately `27 GiB` while
preserving every active dependency and incremental build cache. CARLA, both
AosVM roles, the builder, all repository gates, and all license gates passed
the required regression. See the
[post-cleanup acceptance record](post-cleanup-acceptance.md).

## Next Authorized Boundary

Documentation cleanup and repository-only validation do not authorize
signing, Cloud upload, assignment, VM restart, or provisioned-Unit mutation.
The revised plan preserves `.11` and provider `0.2.0` as accepted local
evidence but does not select them for Cloud deployment. The current boundary
is review of the HLA 1.2 design chain, including the
[Component Decomposition and Interface Register](../requirements/component-decomposition-and-interface-register.md),
followed by component requirements and a replacement implementation plan.
Those actions follow the explicit gates in the
[current roadmap](../planning/roadmap.md).
