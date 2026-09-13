<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Test .32 CM Online controlled comparison — 12 September 2026

Status: A/B/A experiment completed; original CM restored. The tested patch was
not isolated as the cause. No product fix or general regression clearance.

Later observation: restored A was reported Offline again at **10:36:04 UTC**
while its connection and Cloud monitoring continued. See the
[startup and delayed-recurrence investigation](cm-startup-and-online-recurrence-2026-09-12.md).
The five-minute results below are bounded observations, not sustained Online
qualification; B was not tested over the later approximately nineteen-minute
interval to recurrence.

## Question and authorized boundary

Does the recent CM stale-instance reconciliation patch cause the observed
loss of Cloud Online after VM startup? The user authorized an A/B/A comparison.
This is a warm CM restart experiment, **not** a cold-VM-start comparison.

- Exact Test VM: `5aa1f8e4-a111-4467-a6cc-fb269c62a7a8`.
- Exact Cloud Unit: `923b9820-999b-41bb-91db-b2a2c469e743`.
- Factory .32 source: `04fc8270c55ff5c35f1e98af534a5efccb035464`.
- SM remains PID `1120`; VDP remains PID `1142`, version `18.0.0`.
- Brake `8.0.0` and Tire `7.0.0`, assignments, Subjects, credentials, identity,
  network configuration, SM, VDP and the running VM are not changed.
- Production is outside the experiment. No provisioning, deployment, upload,
  Cloud mutation, image build or offline-button fault is performed.

## Exact independent variable

A is the installed .32 CM:
`85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d`.

B removes only `0002-reconcile-stale-instance-snapshot.patch` runtime changes
from `src/core/cm/launcher/instancemanager.cpp`. The shared gRPC write-lock
backport and all other compilation inputs remain unchanged. B SHA:
`b57ce3b757ef3fbc1d32bdcf22be8d32d72d779d7d59acf03b67211af93aa9de`.

The warm, unstripped CM SHA was
`1ee6ad0a821de89c40b4b108b25b89b8afe338fdced9b0cd6a678df0b9f93936`.
All allocated ELF sections of that binary matched the installed packaged A
before compilation. Only target `aos_cm_app` was compiled using its saved Yocto
environment. After exporting B, the original source was restored and the same
target recompiled; its allocated sections again matched packaged A. No package,
image, configuration, layer-selection or fetch task was run. Builder was stopped
immediately after transfer. The comparison artifact is outside Git under
`demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-comparison-20260912`.

B runs through an exact `/run` bind-mount drop-in, not a rootfs modification.
An eight-minute systemd timer independently restores A if host control is lost.
Explicit restoration stops that timer and removes the owned binary and drop-in.

## Execution and observations

All live actions and observations use `democtl`. Fixed, Test-only engineering
phases were added to Demo Control; they are explicitly rejected by the
presentation API. Each mutation phase journals intent and result; completed
repeats do not restart CM, and uncertain attempts require reconciliation.

| Phase | CM process start, UTC | PID | Observed result |
| --- | --- | --- | --- |
| Failing preserved baseline | 05:12:13 | 1057 | Cloud Offline since 05:15:09, still Offline immediately before the control; WebSocket Pong and monitoring ACKs continued |
| A: unchanged installed CM restart | 10:06:04.978 | 41710 | Cloud Online since 10:06:05; still Online immediately before B at 10:11:29 (more than five minutes) |
| B: same build without reconciliation patch | 10:11:29.496 | 42647 | Online since 10:11:29; still Online at 10:16:46.098 (5 minutes 17 seconds), immediately before restoration |
| A: restore installed CM | 10:16:50.781 | 43568 | Online since 10:16:51; still Online at 10:22:10.715 (5 minutes 20 seconds after process start) |

B monitoring read at `10:14:16Z` returned an exact-Test sample timestamped
`10:13:07.065060Z`, including the node and both service/Subject identities.
CM logs show regular Pong and monitoring ACKs, not just a successful TCP
connection. The phase window must exceed the earlier approximately 175-second
startup-to-Offline interval; the target is at least five minutes per leg.

The final Cloud monitoring read at `10:21:52.868567Z` returned a fresh exact-Test
sample timestamped `10:21:17.078534Z` for the node and both services. Restored A
has one connection-establishment event, two sent UnitStatus entries, five sent
monitoring entries, 17 received ACKs and `NRestarts=0` over its final window;
B had the same counts at the end of its window. Existing log-line truncation
means this is a message-count/shape comparison, not full wire-body equality.

One Cloud read at `10:20:39.238Z` yielded no Unit value. It is recorded as an
unavailable observation, not Offline. Reads at `10:20:58.289Z`, `10:21:49.138Z`
and `10:22:10.715Z` all reported Online with the unchanged transition timestamp
`10:16:51Z`; the reduced first output did not retain the read failure reason.

The eight initial `systemId mismatch` failures are not by themselves proof of
this regression: they were also present with the older CM and appeared in the
successful unchanged-binary control. Both warm legs resend initial UnitStatus
and receive desiredStatus without a service release or assignment change.

## Limits and decision

The failing baseline recovered after restarting **unchanged** A. Therefore,
successful B alone cannot prove that removing the patch fixes the failure.
The CM process/session/startup timing changed in every restarted leg. This
experiment cannot exclude cold-start ordering, SM startup effects, a timing-
dependent interaction or Cloud-side state. No one of those is established as
the cause here. Service-update reconciliation itself is not requalified by a
steady-state connectivity experiment, and B is not a replacement release.

Decision: retain the installed patched CM. Both patched controls and the
unpatched leg passed this bounded warm-restart observation. This does not prove
the recent SM/CM changes regression-free and does not identify a Cloud defect.
The original cold/resume-start failure remains open. Any next comparison that
restarts the VM or changes SM must be scoped separately; neither was performed
here. No automatic reconnect workaround is added to normal demo lifecycle.

Local focused tests: 44 passed (`test_component_runtime`, `test_cm_comparison`).
No new VM image, service release, broad formal E2E or Production test was run.
Explicit rollback completed at `10:16:50.827948Z`. The effective CM hash equals
the original installed hash. The transient drop-in and binary were removed,
the rollback timer was stopped, and neither SM nor VDP restarted. The later
SM read reports PID `1120`, `NRestarts=0`, SELinux Enforcing and zero denied
entries in its available complete kernel-journal window. Both native service
containers are still alive. VDP remains `18.0.0`, slot `a`, PID `1142`,
READY/LIVE with the same service start time `05:12:14Z`.

The small comparison binary, manifest and compile logs are deliberately retained
outside Git as evidence; no image/cache/history cleanup was performed. Platform
source is unchanged. The Demo Control engineering commands/tests and this report
are local changes, not a new CM fix or a published release.
