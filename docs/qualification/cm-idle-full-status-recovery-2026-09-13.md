<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Test .32: idle full-status recovery experiment

Publication note: private evidence links, infrastructure identifiers and source
locations have been removed. The detailed working report is retained outside
Git under the confidential-input policy; timings and our own conclusions remain.

Status: **PASS for the authorized idle false-Offline recovery experiment.**
Historical snapshot: the transient CM was active on Test .32 at this checkpoint.
It was subsequently incorporated into .33 and the .32 Unit retired. See the
[current baseline](current-baseline.md); this experiment is not a Cloud fix.

## Purpose and authorized boundary

The original .31 control also suffered a stale Cloud connection event. It
recovered without a restart because its failed VDP update caused the native
update-completion path to send a new full UnitStatus. Stable .32 had no such
reason to send another full status and remained falsely Offline, despite its
live transport and acknowledged monitoring.

The user authorized a CM-only rebuild and one CM restart on the current .32
Test. This experiment periodically invokes the existing full-status producer;
it does not restart a connection to recover Online or change Cloud code.

- Factory: `6.1.1-maninblack.32`, image SHA-256
  `f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14`.
- Test Unit: `d90798f6-a32c-40cc-8129-26a0f1343a67`.
- System UID: `c7b8f9d868ea4b65b4448b01595eb110`.
- VM: `c7b8f9d8-68ea-4b65-b444-8b01595eb110`.
- Separate original .31 control and Production are excluded from mutations.
- No VM reboot, SM restart, provisioning, service reassignment, package
  publication, Factory image build or Cloud configuration change.

## Change under test

CM configuration gains `idleFullStatusInterval`, disabled by default (`0s`).
Only the transient Test configuration sets it to `60s`.

The existing DesiredStatus worker uses a timed condition-variable wait while
its update state is idle. A timeout requests a full status through the existing
UnitStatusHandler. No additional timer thread writes the snapshot; no synthetic
version, update, connectivity event or ACK is produced. The native delta path
is retained, and a pending delta takes priority over the idle refresh.

The full-status producer rejects overlapping full/delta collection and releases
its processing guard after a collection/send error. This permits a later
refresh instead of leaving status collection permanently suppressed.

Important limits:

- This is an **idle-state repair mechanism**, not a strict 60-second recovery
  guarantee during a long update. Active updates retain native completion
  status reporting. A pending delta can defer an idle refresh.
- It cannot prevent Cloud from applying a stale event. Cloud can temporarily
  display Offline/Connected until it processes a newer full report.
- It cannot repair a Cloud queue that is also unable to process UnitStatus.
- Original consumer stalls, stale-event rejection/session ordering and the
  production fix remain Cloud responsibilities.

## Reproducible source and build

Only the warm .32 CM target and status/configuration test targets were built.
No BitBake package/image task ran. Ten exact source/test files were transferred,
with their pre-edit warm bytes checked against the local Git bases.

| Input | Revision / artifact |
| --- | --- |
| Platform Factory source | `04fc8270c55ff5c35f1e98af534a5efccb035464` |
| Shared-library base | `0b82a6bfcb5296ae7cdc97fcd8e9ab58048c30ec` |
| Core application base | `da50b60b7d72208bf17ad51250d24dbc727bc679` |
| Shared-library delta | [Review patch](../../components/upstream-review/cm-idle-full-status-library.patch) |
| Application/configuration delta | [Review patch](../../components/upstream-review/cm-idle-full-status-app.patch) |
| Stock installed CM SHA-256 | `85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d` |
| Test proof CM SHA-256 | `e1f06ff8a2bce082a0825c5e4163ba7cedc14e7c0863e9c021fbe85455c1c9fd` |
| Proof size / architecture | 5,598,976 bytes / ELF64 AArch64 |

The binary and build manifest are local artifacts, not Git content:
`$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-idle-full-status-20260913/`.

Tests actually run:

- 11 native update-manager tests passed, including all existing tests and new
  default-disabled, periodic full, disconnect/reconnect, and collection-error
  recovery cases. Refresh does not invoke download or installation.
- 2 native CM configuration tests passed, including `60s` and absent/default
  `0s` configuration.
- 58 focused Demo Control tests passed, including CLI-only exposure, pinned
  Test/candidate guards, and completed/uncertain operation replay protection.
- `git diff --check` passed for the Solution changes.

Concurrent stress, send-error injection, full Factory/cold E2E and upstream
review are not claimed by these tests. The existing production warm source is
restored after the proof build. The warm compiled CM was subsequently rebuilt
from that original source and its ELF allocated sections verified equal to the
stock packaged binary. Builder is stopped. The first cache-restoration call
did not reach SSH authentication while Builder was booting; its remote build
never began. After reconciling that failure, restoration completed once.

## Activation and early evidence (UTC)

| Time | Evidence |
| --- | --- |
| Before activation | .32 was falsely Offline since 02:24:30 despite the live CM transport. |
| 04:44:04 | One authorized CM restart replaced PID 55106 with PID 80357. |
| 04:44:04.704 | Cloud UMH received the new V7 connect, embedded timestamp 1789274644.693789. |
| 04:44:04.892 | UMH started processing the new UnitStatus. |
| 04:44:05.018 | UMH explicitly logged setting this Unit Online. |
| 04:44:26.492615 | Authoritative API read: Online. |
| 04:45:14.024684 | First periodic full UnitStatus observed; `isDeltaInfo=false`. |
| 04:46:14.027305 | Next full report from the same process; Cloud returned desiredStatus. |
| 04:47–04:49 | Further full reports approximately 60 seconds apart, without restart. |
| 04:56:59.107798 | Authoritative API still Online; `last_online_changed_at=04:44:04`. |

Guest wire log records are size-truncated. Only the visible complete boolean
`isDeltaInfo` and fixed stages/timestamps are extracted; unavailable fields are
not reconstructed. Cloud log observations are independent of the guest send
attempt. `response: ack` in a sent header is a request, not proof of receipt.

Preservation evidence: SM PID 56660 remained active; VDP 18.0.0 remained active
with zero restarts, matching slot/process and 23 reported read paths. Native
Brake and Tire containers remained alive with their existing IDs
`7cf522e4-ff3f-3b8c-b02e-b09458403b5a` and
`b14e8bca-b1a3-30a0-b44c-d972263deee6`. Base CM configuration and committed VDP
records were unchanged. No claim of KUKSA permission recovery is made.

## Delayed false-Offline recovery: observed, not inferred

The same Cloud failure reproduced after the patch was already running. All
timestamps below are UTC on 13 September 2026.

| Time | Authoritative evidence |
| --- | --- |
| 04:44:03.956 | Cloud WS logged the old connection closing during the one authorized restart. |
| 05:14:02.452405 | Demo Control API read still Online. |
| 05:14:03.997747 | RabbitMQ consumer `CONSUMER_A`, channel 1277, queue `connection-event queue`, delivery tag 1 timed out after 1,800,000 ms. |
| 05:14:04.000 | UMH received `is_connected=false` with old event timestamp `1789274643.95922` (04:44:03.959220), over the newer active session. |
| 05:14:13.637444 | Demo Control API confirmed **Offline**, changed-at 05:14:04. |
| 05:14:14.135108 | Existing CM PID 80357 logged `Refresh idle full unit status`. |
| 05:14:14.139170 | Same CM sent UnitStatus with visible `isDeltaInfo=false`. |
| 05:14:14.180 | UMH began processing that UnitStatus. |
| 05:14:14.247 | UMH explicitly logged setting the exact Test Unit **Online**. |
| 05:14:15.113157 | Same CM received Cloud desiredStatus. |
| 05:14:23.682634 | Demo Control API confirmed **Online**. |
| 05:14:33.389806 / 05:14:45.794028 | Subsequent API reads remained Online. |

Cloud recovery followed the stale-event receipt by **10.247 seconds**. The
API sampled the actual Offline state before recovery; it is not merely an
absence-of-failure observation. `last_online_changed_at` remained 05:14:04
after recovery, so that field alone is not a complete status-transition history.

The post-window CM observation confirmed the exact candidate SHA, PID 80357,
`ActiveState=active`, `NRestarts=0`, **one** WebSocket connection, 31 periodic full
reports, and seven update-state transitions (unchanged from initial startup).
Thus the refresh did not recover by reconnecting or starting another software
update. No CM/SM/VM restart was performed after the initial activation.

Read-only Cloud evidence:

- UMH stale-event and recovery window (private evidence reference omitted).
- Matching consumer timeout (private evidence reference omitted).

## Retained transient state and exclusions

- Binary/configuration directory:
  `/run/democtl-cm-idle-full-status-20260913`.
- Drop-in:
  `/run/systemd/system/aos-cm.service.d/95-democtl-idle-full-status.conf`.
- The drop-in binds only the tested executable and a copy of `/etc/aos/cm.cfg`
  with the interval added. Original owners/modes and SELinux reference labels
  are retained; no permission or policy broadening was applied.
- Original executable and rootfs configuration are unchanged. Proof state is
  deliberately retained; a VM reboot removes `/run` and returns to stock CM.
- Removing the drop-in and restarting CM would restore stock at runtime, but
  another restart/rollback was **not performed** under the one-restart budget.
- Exact operation intent/result is recorded by Demo Control. Repeating apply
  returns the recorded result, not another restart. An uncertain result blocks
  a new apply and requires read-only reconciliation.

The specific idle false-Offline recovery case is now proven. It does not
establish strict recovery timing during active updates, a cold Factory boot,
power-loss recovery, or absence of future Cloud consumer faults. No new image
or additional network-off/on experiment was needed for this result.

This document and the source review patches are an experimental checkpoint,
not an approved new Factory Image or completion of the overall demo E2E plan.
