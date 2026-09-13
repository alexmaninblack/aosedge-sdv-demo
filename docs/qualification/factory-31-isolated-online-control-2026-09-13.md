<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Original Factory .31: isolated Online control

Publication note: private evidence links, infrastructure identifiers and source
locations have been removed. The detailed working report is retained outside
Git under the confidential-input policy; timings and our own conclusions remain.

Status: **completed; stale Cloud connection-event defect reproduced on original
.31**. All times UTC.

Later disposition: this temporary comparison Unit was deprovisioned/deleted
before the [.33 run](factory-33-e2e-2026-09-13.md). Its historical boundaries
below are not current runtime instructions. Disk cleanup is tracked separately
in the [consolidation audit](factory-33-consolidation-audit-2026-09-13.md).
The existing Production .31 is a different VM and remains preserved.

The user authorized a separate temporary Test VM and its Cloud provisioning to
compare the original full Factory .31 against the false-Offline reproduction
on .32. Do not replace only one CM patch and call it a .31 comparison.

## Fixed boundaries

- Original image: `6.1.1-maninblack.31/main-qemuarm64`, SHA-256
  `a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4`.
- Separate root: `$WORKSPACE_ROOT/aosedge-sdv-demo-qual-31`.
- CLI context: `democtl --qualification factory31`; Test-only allowed actions.
- SSH port 11022; temporary provisioning forward 18093. Existing Test and
  Production retain ports 10022/10023 and their existing disks and identities.
- Reuse the canonical DNS bridge as an observed external dependency. Never stop
  it from the comparison environment. Credentials are referenced, not copied.
- Preserve .32 Unit `d90798f6-a32c-40cc-8129-26a0f1343a67` and Production Unit
  `d87ba9cb-b21f-45db-8773-553e52d0353e`; no assignments/releases/model changes.
- No manager binary replacement, new image build, service publication or
  permissions workaround. Existing shared service Subjects stay on .32.
- Leave CARLA on .32. This control compares Cloud connection-event handling,
  not service replacement, driving or advisory functionality; service workload
  is consequently not identical. State this limit in conclusions.

## Sequence

1. Create from the exact .31 image; boot and initialize its Test role through
   the normal CLI lifecycle, with no copied identity from another VM.
2. Provision once and add only the new UID to existing Test Vehicles. Native
   membership addition must not replace existing set members.
3. Observe original manager identities, Online and connection-event timestamps.
4. Run one owned guest external-link off/on cycle, preserving local SSH. Restore
   ON even if Cloud state is unexpected; do not mask a failure with a restart.
5. Observe more than 30 minutes after server-observed disconnect, with CM logs,
   Cloud WS, UMH and RabbitMQ evidence. Distinguish no reproduction in this
   bounded interval from proof that .31 cannot trigger the Cloud defect.

The CLI-only context reuses existing environment/VM/provisioning/filter code;
it is excluded from Presenter API and allows no cleanup or package mutation.
Original-context VM/connectivity/unit tests passed (55); focused isolation
tests passed (11, including inherited connectivity controls). No live operation
had occurred when those tests ran.

## Executed control

- Create completed from the original .31; boot/SSH/DNS took 62.47 seconds.
- Provisioning completed in 22.72 seconds, including Cloud Online and additive
  Test Vehicles membership, confirmed at 03:10:23.032125.
- Unit: `555290f6-0cd7-4eb0-bddc-8e5cfbed7ab6`.
- System UID: `2af4d5ce11244fc49bc03124acec8b65`.
- Node: `3ea1a555-edf1-4f9e-958d-27ddd9c40543`.
- Original CM: PID 1580, zero automatic restarts, SHA-256
  `8432c0ca62b3b7bebf0e20f3ae3f82d412429be44fadcd00d914dbf1170f48bc`.
- Original SM: PID 1803, zero automatic restarts, SHA-256
  `df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86`.
- Neither manager was replaced or restarted after provisioning.
- Source comparison: .31 `0bed8b3769b09fbe685ed599ca8d10e6594fbe53`
  versus .32 `04fc8270c55ff5c35f1e98af534a5efccb035464` confirms CM
  reconciliation patch 0002, SM service patches 0002–0004, packaged service-input
  hooks/resources and component-runtime changes are .32 additions/deltas.
  The preexisting CM stream-write serialization patch is already in .31.
  The Platform worktree remained clean during the experiment.

Two local harness conditions stopped before SDK registration: the default
single-member Test Set guard, and a chosen provisioning port already occupied
by the Brake Docker backend. The isolated context now tolerates only the exact
canonical Test ID/UID as a preserved peer and uses free port 18093; the backend
was not stopped. The normal guard remains unchanged. The provisioning SDK
itself ran once, successfully. Focused Unit tests passed: 28.
After the port/coexistence corrections, the combined qualification,
connectivity, VM and Unit suite passed **67 tests**; `git diff --check` passed.

### Connection-event timeline

| Observation | Original .31 control |
| --- | --- |
| First WS connection | **03:10:18.253**, establishment/publish path finished **03:10:18.265**; trace `2c1515c117d6795f9b028ac9ec0b7081`. Its initial true-event receipt was not found in the first bounded UMH event query. |
| External-link OFF command | Completed around 03:10:42; only the isolated VM filter changed. |
| Cloud disconnect timestamp | `1789269078.356562` = **03:11:18.356562**. |
| UMH false-event receipt | **03:11:18.366**: approximately **9.4 ms** after event creation. |
| Cloud API while OFF | At 03:11:25.917192: **Offline**, last change **03:11:18**. |
| External-link ON command | Confirmed **03:11:51.190544**; no CM/SM/VM restart. |
| Cloud reconnect timestamp | `1789269117.078594` = **03:11:57.078594**. |
| UMH true-event receipt | **03:11:57.089**: approximately **10.4 ms** after event creation. |
| Cloud API after ON | At 03:13:27.388262: **Online**, last change **03:11:57**. |
| Handler pod | `CLOUD_INSTANCE_A`, also involved in the .32 investigation. |

Both connection events reached the handler promptly, unlike the queued stale
disconnects in the .32 reproduction. This is an observed difference, not proof
that a VM patch causes the consumer failure. There is a different Unit identity,
different service workload, different execution time, and potentially different
consumer selection inside the same pod. At this early checkpoint the .31
window beyond 30 minutes was still in progress; the result below supersedes
any early impression of a clean run.

The initial connection is a separate unresolved event: WS confirms it at
03:10:18, but the first UMH `is_connected` query returned only the later
disconnect and reconnect. Absence from this bounded query is not yet proof of
a queued delivery. If that initial true event arrives late, the same handler
can demote Online to Connected; therefore prompt handling of the link cycle
alone must not be reported as a clean .31 result.

Connection-event evidence (private evidence reference omitted).

## Decisive result at 03:40:18 UTC

The previously missing initial connect was delivered **30 minutes late**.
This closes the earlier query-absence uncertainty; it was not merely a missing
display row. No guest, manager, filter or Cloud mutation occurred at this time.

| Boundary | Evidence |
| --- | --- |
| RabbitMQ ACK timeout | **03:40:18.293758**, queue `connection-event queue`, consumer `CONSUMER_A`, channel **1275**, delivery tag **1**, timeout **1800000 ms**. Same consumer tag as .32, different recovered channel. |
| Delayed UMH receipt | **03:40:18.295**, `is_connected=true`, protocol 7, UID `2af4d5ce11244fc49bc03124acec8b65`, embedded timestamp **1789269018.25377** = **03:10:18.253770**. |
| Event age | **1800.041 s**, matching the initial WS connection, not the newer 03:11:57 session. |
| Authoritative Cloud API | **03:40:44.340257**: **Connected**, `last_online_changed_at=03:40:18`; previously Online since 03:11:57. |
| Original guest CM | PID **1580**, unchanged factory SHA, zero automatic restarts after the demotion. |
| Preserved .32 | Read at **03:43:04.467246**: still Offline since **02:24:30**, same Unit ID; not restarted to hide the failure. |

This reproduces the **same stale-event delivery and status-overwrite mechanism**
without the latest .32 CM/SM service-update patches. The exact visible symptom
differs: .32 received old `false` events and became Offline; .31 received an old
`true` event and was demoted from Online to Connected. Do not claim that the
exact Offline symptom was reproduced by the .31 link-off event: that false
event was processed promptly.

The latest service-update patches are **not necessary** for this Cloud failure
to occur. This does not prove that every historical guest change is harmless,
or identify why the Cloud consumer originally stopped acknowledging deliveries.
Both images exercise the existing defective consumer/ordering path. Rebuilding
or removing the latest patches is not an evidence-based fix for that path.

### Automatic recovery and closure

No recovery command was issued. The original CM sent UnitStatus at
**03:44:03.377996**; UMH began processing it at **03:44:03.407**. CM received
and handled desiredStatus at **03:44:04.313247/.313303**. Cloud also processed
fresh monitoring at **03:44:17.885** and **03:45:17.876**. This is bidirectional
transport evidence after the incorrect Connected state, not only a live PID.

At **03:45:00.976891** the API again reported **Online**, without an operator
restart, reprovision or status write. `last_online_changed_at` remained
**03:40:18** even after this recovery; that field alone is not a complete
Online-state-transition history. The control therefore shows a transient
Online -> Connected -> Online degradation, not a permanent Offline on .31.
Final API read **03:47:03.139619**: Online, more than **35 minutes 44 seconds**
after the server-observed disconnect. Final filter read **03:47:11.566717**:
ON, with no selected CARLA vehicle in the isolated context.

The comparison VM, factory copy, overlay and Cloud identity are deliberately
retained for diagnosis. Its external link is ON; CARLA, both .32 service
Subjects and Production stay in their original contexts. No cleanup, package
upload, image build, Cloud platform/code/config change, commit or push was
performed. The CLI isolation changes and this record remain uncommitted in
the existing dirty Solution worktree; unrelated prior changes are preserved.

The whole-image experiment does not qualify service updates, KUKSA, advisory,
or equal application workloads. VDP 18 was selected automatically by existing
Test-set policy; no new release or Subject assignment was made. Without CARLA
on this comparison VM, its component readiness is not this experiment's gate.

Post-degradation live messages (private evidence reference omitted).

- Broker timeout for .31 (private evidence reference omitted).
- Delayed initial connect (private evidence reference omitted).
