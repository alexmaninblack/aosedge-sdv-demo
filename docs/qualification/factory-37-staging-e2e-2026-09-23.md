<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .37 clean staging E2E — 23 September 2026

Status: diagnostic/security stage closed for successor .38 candidate construction
on24September12:16UTC; .37 is **not a qualified baseline**. Preserve the Test and
evidence. The historical VDP109 native crash remains unexplained, not claimed fixed.

## Authorized scope and starting evidence

The operator confirmed retirement of the current Test and a clean end-to-end
run on Factory .37. Delete only the old owned Test Cloud Unit, working VM and
run-scoped backend records. Preserve Factory .36/.37, source, published releases,
release numbering and diagnostic evidence. Production and the video repository
are outside this operation.

Read-only preflight at `2026-09-23T20:48:43.813123Z` confirmed:

- Selected OEM and SP both use `aws-stage.epmp-aos.projects.epam.com`;
  authenticated access is current.
- Old Test Cloud Unit: `9dc8c120-7f20-45db-9655-d5585b57cc35`.
- Old local VM: `15a538bc-af0e-4972-8c5e-4beda4b90a83`, Factory .36.
- Old Test is Online/provisioned; IAM/SM/CM active, zero restarts.
- CARLA/source connected to Test; Production stopped.
- Planning a .37 Test correctly refuses the existing .36 environment.

Retirement must use the existing lifecycle with authoritative Cloud and backend
receipts. Unknown or partial outcomes are reconciled before any retry. No manual
filesystem deletion substitutes for lifecycle completion.

## Planned gates

1. Retire old Test; confirm scoped deletion and preserved factories.
2. Create fresh .37 through normal Demo Control; verify identity, time, DNS,
   manager health and UI observations.
3. Sequential VDP V1/V2/V3 and Brake V1/V2/V3, plus Tire V1. Publish each next
   version only after installation and verification of its predecessor.
4. VDP Safe Stop gate; QM updates while driving; persisted data, stable service
   UIDs/quotas and complete Cloud resource metrics across upgrades.
5. Real Brake/Tire maneuvers, local advisory, independent reset and return-to-road.
6. External network OFF at least five minutes: backend ingress stops while local
   processing/authorization/advisory continue. ON restores Online and delivery.
7. UI feedback and status consistency; exact owned-Test Finish gate at the end.

## Evidence log

- Preflight completed. One `demo.retire` completed with phase `RETIRED`:
  graceful VM shutdown, Cloud Offline, deprovisioned new/Offline confirmation,
  membership removal, authoritative Unit/Node absence, scoped backend cleanup
  and local overlay retirement. No manual deletion or repeated mutation.
  The removed run's working data is not recoverable through normal Demo Control.
- Clean .37 creation completed with `CONTROLLER_RUNNING`; local VM/run
  `621ad642-daad-483b-97cd-dd48297b5cd7`, QEMU PID88193. Existing native
  credential provider supplied first-SSH enrollment without a password prompt.
  Guest release .37, DNS resolved/bridge-port matching, unprovisioned IAM
  active and normal IAM/SM/CM inactive; all restart counts zero.
- Guest/host epoch both `1790197004` at20:56:44UTC. SELinux Enforcing,
  timesyncd active with zero restarts. `timedatectl show` is denied over D-Bus;
  this diagnostic does not prove an NTP failure and no security change was
  made. Known preprovisioning NFS failure and absent states/storages mounts
  match the documented .36/.37 offline baseline; check again after Provision.
- At21:01:18UTC, the existing timesync synchronization marker was present
  (epoch1790197137); all four manager units reported Result=success and zero
  restarts in their expected unprovisioned active/inactive states.
- Simulation startup completed, detached as designed: native panel shows
  Not assigned, Safe Stop,0km/h, both advisories Not available. Presenter shows
  .37/Not provisioned and advances to the Platform preparation action. No
  premature attachment, cloud-installed claim or reused backend result.
- Selected staging prerequisite check at20:59:58UTC is READY for OEM/SP,
  Default fleet, arm64, one-node model/config, node type, Test verification
  set and OEM/SP association. No Cloud setup mutation was needed.
- Local unsigned candidates prepared successfully: VDP109/110/111
  (V1/V2/V3), Brake87/88/89(V1/V2/V3), Tire48(V1). None signed/published.
  Exact selected-certificate, staging publication and new-Test Provision /
  assignment confirmation requested as one group. Execution remains sequential.
- Operator confirmed the exact seven-release set and new-Test Provision /
  assignment. Fresh preflight at21:11:01UTC confirms the same .37 Test,
  unprovisioned state, current OEM/SP access and selected staging domain.
  First external action is signing/publishing VDP109/V1 only. No later VDP or
  Brake profile may be uploaded until its predecessor's live gate passes.

## Provision and VDP V1

- VDP109 upload accepted once21:11:36UTC (deployment
  `f46024ac-aa3d-4268-874e-df0b8044ae9c`); authoritative READY/Done read at
  21:11:56UTC. Provision completed in32.27s, new Unit
  `2737ef63-4781-4ee6-a770-52e0a01e95e0`, Node
  `7219f742-7de1-42c0-8a2a-63798c5f0972`, same local VM/run.
- Post-Provision: .37 NORMAL, IAM/SM/CM active with zero restarts,
  authenticated staging Online/provisioned, Gateway CONNECTED/mTLS ACTIVE.
  Native UI transitioned from Not assigned to Test/stationary Manual. Explicit
  Autopilot then observed19.3km/h/MOVING.

### M4-status-01 — premature installed/active report (open)

Before an operator Safe Stop, Cloud reported VDP109 installed with no pending
version. Guest runtime contradicted that claim: provider inactive, no active
version, durable transaction `waiting-for-safe-stop` for109. Safe Stop itself
has not been bypassed.

Bounded current-boot evidence pinpoints the chain: SM image unpack was recorded
as installed; VDP returned an asynchronous activating status; immediately after
StartInstance returned, SM reported that instance active although the runtime
was still waiting. Mainline library `src/core/sm/launcher/launcher.cpp`,
`AddStartInstanceTask`, unconditionally calls
`SetInstanceState(...eActive)` on successful return. Our slot runtime returns
success once its Safe Stop worker has started, with an activating out-status.
This is an integration semantic mismatch, not proof of premature vehicle
activation. Runtime unit tests alone did not cover this launcher integration.

Preserved the contradictory Cloud/runtime/log observations before issuing
Safe Stop. No code, policy or manager restart is used to hide the result.
Continue only the independently observable functional checks, checking the
actual provider version/readiness before advancing releases. M4 cannot be
accepted while this status defect remains. A fix needs a launcher/runtime
integration regression and a live repeat; do not compensate in Presenter by
inventing an installed state from guest-only data.

After one explicit operator Safe Stop at21:16:02UTC, VDP109 activated in slot a:
provider PID2787, seven read paths, `REPORTED_READY`, zero restarts. This closes
the functional V1 activation prerequisite, not M4-status-01. No later VDP
version has been published.

Two new isolated ARM64 negative-control regressions reproduce the status defect
against the current migration candidate: an asynchronous component's activating
return is overwritten with active, and a later failed callback is forwarded
but does not update the launcher's cached full snapshot. Final result:0/2 pass,
with exactly those two assertion failures. Evidence:
`sm-async-negative-v2.xml` and `sm-async-negative-v2.log` in the host proof root.
Earlier harness-only dependency/assertion corrections are excluded. These tests
are currently only in the isolated proof source; no product fix or VM binary
replacement has occurred. The eventual fix must cover both initial and later
snapshots, including stale-version callbacks, rather than masking UI output.

### M4-container-02 — first Brake start blocked by new execution domain (open)

- Brake87/V1 was signed/uploaded once; HTTP201 at21:17:31UTC, deployment
  `c48090e8-217f-46d6-be13-90de2c55d669`, authoritative READY at21:17:40UTC.
- Service `cabba557-061d-4f44-9385-5b1b03e34186` was assigned once to the
  current Test through subject `78d05c9c-cdf6-45cc-ab28-df2a4d3ac0d7`.
  Unit/service binding succeeded; actual runtime failed. Presenter reports
  `Service runtime not confirmed`; assignment is not counted as functionality.
- The precise runtime failure at21:18:25.448511UTC is
  `cannot stat /run/aos-kuksa-auth-compat: Permission denied`. The generated
  OCI process has UID/GID5000 and supplementary group997, as intended.
  SM has no seccomp filter or capability restriction causing that stat failure.
- Upstream app commit `9c8a27ec168b6e0cab84b827a27dfedac359797b`
  changed in-process libcrun startup to executing `/usr/bin/crun`. The installed
  executable has type `container_engine_exec_t`; compiled policy transitions
  `initrc_t` to `container_engine_t`. Journald's inherited-stream identity alone
  is misleading here: it reports initrc_t and does not establish the child's
  post-exec domain.
- Compiled policy has `dontaudit container_engine_domain file_type:dir getattr`.
  Its generic non-security-file mount grant is conditional on
  `container_mounton_non_security`, which is **off**. It was not enabled.
  No active specific directory grant was found for this KAC runtime type.
- A single isolated reproduction used the same generated user/mount contract,
  but `/bin/true`, no application environment/hooks, no backend network, and
  no state/storage/credential mounts. It ran from a transient systemd unit
  under the same initrc_t starting context. `strace` captured successful
  supplementary-group setup and the exact failing `statx(...)=EACCES` before
  payload execution. The reproduction did not start Brake or request a token.
  This is a platform launch-policy integration failure, not a Brake model,
  certificate, publication or backend error.

The exact transient evidence is `/run/factory37-crun-probe-qb3xxd6u` on the
preserved Test and the host proof directory. No policy/boolean/rootfs change,
manager restart, reassignment or live retry was performed. The probe terminated;
its temporary source and inactive evidence are retained for the next bounded
proof. Do not grant broad file access or disable SELinux. A narrowly scoped,
automatically rolled-back policy proof requires confirmation before proceeding;
then verify the full KAC/service chain and negative access boundaries before
source consolidation. A stat-only success would not qualify the service.

Final read-only check confirms Enforcing, the broad boolean off, no remaining
probe container, and IAM/SM/CM/VDP still active with their unchanged PIDs and
zero restarts. The separate diagnostic Builder was stopped cleanly; its warm
disk/caches are retained.

#### Authorized directory-only proof — 24 September local time

The operator authorized the bounded directory-metadata proof, not a permanent
policy installation or additional credential/socket permissions. Compiled a
private policy store at `/run/factory37-crun-policy-proof-20260924`; full SETools
structural comparison found exactly one added rule and no other policy change:

```text
allow container_engine_t aos_kuksa_auth_runtime_t:dir { getattr search };
```

The successful three-stage control, using inherited systemd journal descriptors
like `CRunRunner::StartContainer` / `ExecDetachedCommand`, produced:

| Stage | Result |
| --- | --- |
| Stock before | KAC directory `statx` returns EACCES; payload not started |
| Temporary candidate | `statx` and bind mount succeed; `/bin/true` exits0 under UID/GID5000, supplementary group997 |
| Stock restored | The original `statx` EACCES is reproduced |

The test retained the generated user/capability/NoNewPrivileges contract and
the KAC directory mount, but used a read-only rootfs, an isolated network
namespace, no application environment/hooks, no state/storage mounts and no
credential requests. It is a mount/start proof, **not** a complete application,
quota, service-network or KUKSA functional proof. No real Brake instance was
started and no published release was retried.

The policy rollback guard was armed for240seconds and disarmed only after
verified stock restoration. Final active policy matches the original digest;
canonical policy stores are unchanged; SELinux remains Enforcing and
`container_mounton_non_security` remains off. IAM1795, SM2187, CM1831 and
VDP2787 remain active with unchanged PIDs and zero restarts. No probe PID or
real Brake crun state remains. Fresh scoped crun AVCs for the successful
three-stage test are empty.

Earlier harness-only failures are excluded from product findings:

- `systemd-run --pipe` could not pass a Python-created unconfined FIFO through
  D-Bus; this failed before loading a policy. Switched to native journal output.
- The first reduced OCI spec omitted the normal `/dev` tmpfs, causing read-only
  `/dev/null` creation after the mount had already succeeded. Restored only the
  existing generated `/dev` tmpfs mount in the isolated test.
- Python output capture created an initrc_t FIFO; crun then failed `fchown` on
  stdout. The actual SM startup explicitly inherits its real descriptors.
  Matching that behavior resolved the harness failure with **no additional
  FIFO, D-Bus or device permission grant**.

Final receipt: `receipt-native-stdio.json` in the private guest proof root.
Compact control logs are `stock-before-native-stdio.log`,
`candidate-native-stdio.log` and `stock-after-native-stdio.log`. The successful
probe bundle is `/run/factory37-crun-probe-ifrobfdg`; evidence is deliberately
retained inactive along with the host proof harness. Product source and Factory
bytes are unchanged; no new build, commit or push was performed.

Read-only follow-up found no explicit process SELinux label in the generated
Brake OCI configuration. The new container-engine domain has neither
`aos_kuksa_auth_runtime_t:sock_file write` nor
`aos_kuksa_auth_compat_t:unix_stream_socket connectto`; the previous initrc_t
context has those accesses through its existing unconfined attributes. This is
a likely **next** integration boundary, not an observed live Brake denial or
permission to add broad rules. The directory-only proof does not authorize
socket permissions. A separately bounded functional/security proof is required
before consolidating a source policy change or advancing the E2E releases.

#### Authorized socket proof and upgrade causality — 24 September

The operator separately authorized the exact socket-access proof with a
240second automatic stock-policy rollback, no key access and no change to
signal permissions. It passed after correcting the test harness and respecting
the existing KAC rate limit. This closes the **socket-access hypothesis**, not
the whole application E2E gate.

The candidate differs structurally from stock by exactly these three rules:

```text
allow container_engine_t aos_kuksa_auth_runtime_t:dir { getattr search };
allow container_engine_t aos_kuksa_auth_runtime_t:sock_file write;
allow container_engine_t aos_kuksa_auth_compat_t:unix_stream_socket connectto;
```

The first rule is the previously proved mount prerequisite. The other two
permit addressing the exact socket type and connecting to the KAC server
domain. They add no regular-file/key permission, type membership, permissive
domain, boolean change, IAM authorization or VSS scope.

The client uses the generated UID/GID5000, supplementary group997,
capabilities and NoNewPrivileges contract. It starts through the installed
crun from initrc_t, with inherited journal output, a disposable minimal rootfs,
private network namespace and only the KAC, `/dev` and `/proc` mounts. It
reports its actual payload context as `container_engine_t`. Each positive
run sends two fixed credential-free status requests and one deliberately
invalid protocol/status request. It neither starts Brake, requests a token,
reads application data nor accesses an external backend.

| Final control | Observed result |
| --- | --- |
| Stock before | Directory stat denied; payload does not run |
| Directory rule only | Payload UID5000/container_engine_t runs; socket connect fails EACCES; exact sock_file/write AVC |
| Three-rule candidate, first run | Two ready responses, invalid request rejected, exit0, zero scoped AVCs |
| Three-rule candidate, repeat | Same successful result after respecting native rate limit |
| Socket rules removed, directory rule retained | Socket connect again fails EACCES with the same exact AVC |
| Full stock restored | Original directory stat denial returns |

Final receipt is `receipt-v5.json` under
`/run/factory37-crun-socket-proof-20260924`. The corresponding `*-v5.json`
stage records and compact earlier receipts were copied to
`/private/tmp/aos-mainline-migration-20260923.A2qEwO/socket-proof-evidence`.
Diagnostic source/binaries and inactive guest bundles remain preserved for
review, not installed as product files. The final client binary is ARM64,
statically linked, SHA256
`3864e9f6e429163d6309f6345b45af944cf999fff60b013efe316297aa004bbd`.

Original active policy hash and canonical store were restored/unchanged.
Enforcing stayed on, the broad mount boolean stayed off, the rollback child
exited, and no diagnostic PID/host mount or real Brake crun state remains.
IAM1795, SM2187, CM1831, KAC2232 and VDP52444 stayed active without any PID or
restart-counter change during this test. VDP's counter was already1 before
the test; see the separate stability finding below. No Cloud mutation,
publication, assignment, manager restart or Factory rebuild occurred.

Excluded intermediate results:

- The first harness attempted a bind mount over `/bin/true`; stock policy
  correctly denied mounton for bin_t. Replaced that harness-only technique
  with a minimal temporary rootfs, without granting a mount permission.
- Payload journal records lose the originating transient unit identifier when
  OCI changes cgroups. Scope collection by traced exact PID and fixed safe
  diagnostic prefixes instead. The original PID-scoped trace/AVC already
  showed the expected connection denial; no missing output was called success.
- An initial connection succeeded but returned an unexpected non-ready status;
  its body was deliberately not recorded, so the cause remains unclassified.
  Added only a whitelist of non-secret rejection codes to the client.
- A rapid repeat subsequently returned BUSY. Source confirms a per-UID burst
  capacity of4 and refill12/minute. This is expected protection, not a policy
  fault. Final proof waited21seconds for initial refill and16seconds between
  three-request runs; no rate limit or time-trust check was changed.

**Exact source-level cause:** the old application pin
`9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` (v9.1.0) calls
`libcrun_container_run` inside SM. The upgraded pin
`9d613a46df3c7f550062e2f19ae3406c57715694` includes
[9c8a27ec](https://github.com/aosedge/aos_core_cpp/commit/9c8a27ec168b6e0cab84b827a27dfedac359797b),
committed18August2026: `run containers via crun CLI`. Its stated purpose is
preserving long-lived container stdout/stderr through `ExecDetachedCommand`
and `crun run -d`. This is a real upstream change, not an invented demo wrapper.

Executing the installed container_engine_exec_t binary triggers the compiled
initrc_t → container_engine_t transition. The generated OCI has no explicit
process selinuxLabel; crun's `libcrun_set_selinux_label` does nothing when that
field is absent. The live test confirms that the payload retains the new
context. The previous initrc_t policy has the relevant accesses through its
unconfined attributes; the new engine domain does not. Comparing Platform
`.36` source `a0f88d8f` with `.37` source `77d99770` shows **no changes** to
the KAC implementation, its SELinux policy directory or the service-resource
mount declaration. Thus our integration retained the old domain assumption
while adopting the new launcher.

This is a demonstrated **AosCore upgrade / Factory security-policy integration
regression**, not evidence that Brake analytics, selected certificates,
Cloud upload or KAC's authorization decisions are defective. The intended fix
belongs to the platform-owned SELinux integration, preserving mainline's
launcher and existing IAM/signal authorization. Source consolidation still
requires the real application/token/telemetry functional chain and its negative
security gates; these isolated status proofs do not qualify that chain.

### M4-stability-03 — pre-existing VDP crash observed (open, causality unknown)

Before any socket proof, VDP had PID52444/NRestarts1 instead of the prior
PID2787/NRestarts0. Bounded systemd-only journal confirms `status=11/SEGV` at
03:43:10UTC on24September and automatic recovery at03:43:12UTC. KAC and the
three managers remain at their original PIDs with zero restarts. No restart
was issued by this investigation. The crash predates the socket tests by
about three hours and is not attributed to their policy changes. Its cause
and relationship to the upgrade are unproved; preserve the current evidence
and investigate separately before accepting .37 stability. Do not export a
raw memory dump as ordinary evidence because it can contain credentials.

#### Correlation with the operator's morning lid-close — 24 September

Read-only correlation rules out the reported morning lid-close as the timing
of this VDP crash. All local times below are Europe/Berlin, CEST/UTC+02:00.

| Event | Local time | Evidence |
| --- | --- | --- |
| VDP main process exits with SIGSEGV/core-dump | 05:43:10.554094 | Guest systemd journal, 03:43:10.554094UTC |
| VDP automatically started again | 05:43:12.984175 | Guest systemd Started event; NRestarts1 |
| Mac enters Clamshell Sleep | 07:19:46 | Host pmset power log |
| Mac reaches FullWake for user activity | 08:31:28 | Host pmset; earlier USB/notification wake began08:30:53 |

The crash therefore precedes the recorded lid-close by approximately1h36m35s.
No host sleep/wake event was logged around05:43. Host boot time remains
15September14:23:16; QEMU PID88193 has run since23September22:54:14. This was
Mac sleep rather than a Mac shutdown/reboot or a newly created QEMU process.
Guest boot ID remains `39a55812-b255-4219-9913-3f7199089ba6` and IAM/SM/CM
retain their21:12UTC start times and zero restarts. Current VDP is active with
PID52444 and the same single automatic restart. No lifecycle mutation occurred
during this correlation.

Clock validation is important here: after the host resumed, guest realtime
advanced by4149.271seconds relative to its monotonic clock. The journal records
the correction from05:26:45.743003UTC to06:35:55.057218UTC while monotonic time
advances only0.043122seconds. This is a later resume-period correction, not the
crash's timestamp. At the crash, monotonic time is24518.024761seconds; at the
subsequent correction it is30733.256792seconds. In the03:40–03:46UTC crash
window, realtime-minus-monotonic is stable to about31microseconds and matches
the pre-sleep offset. Thus neither a UTC/local conversion nor the later clock
correction moves this crash to the morning lid-close.

Classification remains a genuine process-level SIGSEGV followed by automatic
recovery, not a graceful VM/service stop caused by closing the laptop. Its
software/root cause and any relationship to the AosCore migration remain
unproved. No core memory was read or exported. Only lifecycle records, clock
metadata and host power events were inspected.

#### Crash-path investigation — 24 September, follow-up

Read-only recheck found a second genuine SIGSEGV at
07:04:03.085007UTC / 09:04:03.085007CEST (monotonic32421.284581seconds).
Automatic restart completed at07:04:05.435587UTC; VDP is now PID71204 with
NRestarts2. IAM1795, SM2187 and CM1831 retain NRestarts0 and the same guest
boot. This supersedes the earlier single-restart observation, not its timing.

Both crashes follow the same application boundary:

| Episode | Last relevant VDP event, UTC | SIGSEGV, UTC | Interval |
| --- | --- | --- | --- |
| First, PID2787 | 03:43:10.045575: non-monotonic VISS frame; reconnect in0.5s | 03:43:10.554094 | 0.508519s |
| Second, PID52444 | 07:04:02.578775: same category; reconnect in0.5s | 07:04:03.085007 | 0.506232s |

The second episode had a previous non-monotonic warning at07:04:01.192963,
followed by successful VISS and KUKSA reconnect logs. These are correlated
precursors, **not a native stack trace or proof of the faulting library**.

The process is `/usr/bin/python3.12`, not a crashing CM/SM/IAM process.
Installed dependencies are grpcio1.75.0, kuksa_client0.5.0,
protobuf5.29.6, typing_extensions4.15.0 and websockets15.0.1.
Although LimitCORE is unlimited, `kernel.core_pattern=|/bin/false` discards
core output. The core directory is empty and coredumpctl is absent. Thus
systemd's `code=dumped` does not establish that a recoverable dump exists.
No live memory/core, private credential or raw telemetry was exported.

An additional packaging gap is proved independently of the SIGSEGV:

- Installed109/V1 `runtime.py` SHA256 is
  `7cdcb989c5e16410f8b7615def40e4e88338e470882a22594c8c4c2280a8cbdd`,
  identical to the retained1.0.16 baseline, not current Platform runtime
  `7261e09690795a7f8b89981179f4c296e5f60f6c6522c0c8dcfb18c93fc506da`.
- `components.py` selects the reviewed source overlay only for V3. V1/V2
  use metadata-only replay;109's prepared receipt explicitly lists only
  metadata/profile/version changes. New common runtime/bridge fixes therefore
  do not automatically reach V1/V2.
- A synthetic identical-frame negative test against the installed-baseline
  bridge raises an exception and clears data, leading the runtime to reconnect.
  Current source ignores that duplicate without renewing freshness; its stale
  timer still clears data. It does not accept changed/backward frames.
- The old runtime also logs "Selected vehicle data is ready" on every valid
  frame. The inspected windows contain319 and431 such events respectively;
  these counts are log events, not distinct recoveries. The current runtime
  already limits this message to a readiness transition.

Do not call this an AosCore-caused VDP crash: the exact old payload, reconnect
precursor, and missing common fixes are established, but the native cause and
an old/new Factory A/B result are still absent. Unifying reviewed common
runtime fixes across V1/V2/V3 must preserve7/15/23 read-path profiles and
V3-only advisory, frozen historical inspection, strict freshness, TLS and
Safe Stop. Do not silently rewrite already published109 or later reserved
releases.

Isolated native probes used only temporary localhost TLS/gRPC fixtures and
synthetic data under `/run/factory37-vdp-*`. They did not connect to real
CARLA/KUKSA, use selected-Test credentials, mutate product bytes, restart a
service, or change SELinux. GDB disabled argument printing and auto-load;
no raw dump was created. Completed observations:

- Initial single-frame probe stopped on a TLS handshake timeout: excluded as
  a SIGSEGV reproduction, not reported as a product pass.
- Bounded repeated single-frame test stopped at its third timeout, cycle274.
- Streaming close/reconnect:1036 iterations, three handshake timeouts,
  normal process exit, no SIGSEGV.
- Full gRPC object-release variation reached beyond100 iterations, then a
  handled Python SSL `UNEXPECTED_MESSAGE`/ConnectionClosed exception ended
  the harness; not a SIGSEGV or proof of the live cause.
- TLS/WebSocket-only isolation:3390 iterations, five handshake timeouts and
  one InvalidMessage exception, normal process exit, no SIGSEGV.
- Installed `runtime.run()` with synthetic VAL/VISS servers: the first fixture
  reused one timestamp across connections and therefore reconnected KUKSA only
  once. Its969 VISS reconnects do not qualify repeated KUKSA reconstruction.
  Correct the fixture, not the product.
- Corrected full-runtime fixture advances time on each connection, then repeats
  that frame. Over80seconds it records876 KUKSA and876 VISS connections,
  875 non-monotonic failures,879 reconnect warnings; normal exit, no SIGSEGV.
- Mutual-TLS variant additionally requires a synthetic client certificate,
  retaining verified TLS on both paths:875 KUKSA and875 VISS connections,
  875 non-monotonic failures,878 reconnect warnings over80seconds; normal exit,
  no SIGSEGV. Test-only readiness notification is disabled in these isolated
  runs; the real source checker and SDK/transport are unchanged. This is not
  a deployed-identity/SELinux or real-service acceptance test.
- Current-source signal-quality/readiness unit tests:15 passed. The separate
  installed-baseline/current-source identical-frame test demonstrates the
  version gap. Neither result closes native crash causality.

Synthetic fixtures were terminated and their temporary directories removed
automatically. Compact scripts and copied public installed Python source are
retained in the existing host proof directory. Stock active SELinux policy
still hashes to `0974d04f730ed91042963e504031dd152efe6067eb3e2925d70585c5781c4faf`,
Enforcing remains1. No accepted source fix or stability qualification follows
from these probes.

Upstream research found a superficially similar synchronous-WebSocket
[SIGSEGV report](https://github.com/python-websockets/websockets/issues/1389),
closed without a reproducible cause, not a matching confirmed fix. The
[WebSocket changelog](https://websockets.readthedocs.io/en/stable/project/changelog.html)
describes a later connection-close race/exception correction, but does not
establish equivalence to this live SIGSEGV. Do not update dependencies merely
because another issue mentions a crash.

Next diagnostic boundary: obtain an actual failure stack, with arguments,
locals, tokens and memory dumps excluded. Existing live Python was started
with `-I`; simply setting `PYTHONFAULTHANDLER` is not an effective solution
because isolated mode ignores Python environment options. A bounded transient
diagnostic launch must preserve the existing launcher, UID, SELinux domain,
credentials and sandbox, explicitly enable `-X faulthandler`, and reconcile
restart counts/rollback. No such live change or diagnostic restart has yet
been made. Until this is obtained, report **root cause unresolved**, not a
proved OpenSSL/gRPC/AosCore regression or a repaired crash.

Final read-only postcheck: CPython3.12.12 and OpenSSL3.2.6; VDP71204 active,
NRestarts2; IAM1795/SM2187/CM1831 active with NRestarts0. Guest boot and stock
Enforcing policy are unchanged, core output remains disabled, and no synthetic
fixture directories remain under `/run`. A local option-only check confirms
that `-I` ignores the environment-only faulthandler request, while explicit
`-I -X faulthandler` enables it. This check did not execute the real provider.

### Authorized VDP core capture and current common runtime — 24 September

The operator authorized temporary VDP core collection, explicitly requiring
removal after diagnosis, and correction of V1/V2 stale runtime packaging.
The earlier no-dump/no-live-change observations above describe the preceding
investigation, not the current diagnostic configuration.

- A guest-only receiver is armed at `/run/factory37-vdp-core/collector.py`.
  `core_pattern` points to it; `core_pipe_limit=1` retains the crashed process
  long enough to validate its identity. It accepts only UID998, Python3.12,
  exact `aos-vehicle-data-provider.service` cgroup and `vehicle_data_provider_t`,
  with SIGABRT/SIGSEGV. No other process is retained. Receiver lifetime20s;
  one core attempt, maximum256MiB raw/64MiB compressed;256MiB free-space guard.
- Directory0700 and output0600, root-owned. Memory stays inside this Test's
  `/run`; no core/credentials/telemetry exported to the Mac, Git or report.
  Success/failure of capture restores `|/bin/false` and pipe limit0. A transient
  `factory37-vdp-core-expiry.timer` restores those settings after24hours;
  reboot clears the transient setup. There is no Factory, `/etc`, launcher,
  SELinux policy or service sandbox change and no VDP diagnostic restart.
- Synthetic UID998 process aborted in a dedicated self-test unit: a valid ELF
  core of5,439,488bytes compressed to754,262bytes, correct0700/0600 permissions,
  and automatic self-disable. Wrong-UID/cgroup negatives wrote no dump. This
  proves kernel collection, not a crash of the real VDP nor capture from its
  confined domain. Real provider PID71204/NRestarts2 was unchanged. The exact
  synthetic dump and receipt were removed; no real crash dump exists yet.
- Explicit removal checklist is in the migration plan. Guest rollback command:
  `python3 -I /run/factory37-vdp-core/collector.py disable`. After diagnosis,
  verify both original sysctls, remove exact diagnostic dump/helper/timer, and
  confirm no diagnostic option entered a published payload or Factory image.
  If a core is captured, inspect only locally with auto-load and arguments
  disabled; disclose function/line-only evidence, never locals/environment.
  [Linux core documentation](https://man7.org/linux/man-pages/man5/core.5.html)
  explains why a pipe receiver needs its own size bound rather than relying
  on RLIMIT_CORE.
  Post-update size-only mapping check:96.65MiB readable anonymous virtual
  mappings versus the256MiB raw limit (full reserved virtual size709MiB);
  default core filter0x33 retained. No process memory content was read.

Common-runtime packaging correction is in Solution `component_build.py` and
`components.py`. New V1/V2 overlay only reviewed `runtime.py`, `bridge.py` and
`manifest.py` from Platform1fe5649, the same immutable checkpoint as V3.
Their frozen dependency binaries, launcher, profile selection,7/15 paths and
advisory-disabled semantics are preserved. Historical replay and V3 inspection
remain supported; source/hash/provenance mismatches fail closed before signing.
No old artifact is rewritten. Current Platform HEAD has no later provider
source delta beyond that reviewed checkpoint.

Tests and exclusions:

- Component regression:165 cases,162 passed,3 crypto-environment skips.
  New regression covers explicit Prepare/inspect/idempotent rejection for
  both profiles, immutable pin required before allocation/Cloud, deterministic
  output, real baseline imports, no advisory, and tamper rejection. Initial
  new-fixture factory metadata omissions were corrected; not product failures.
- Platform family37, frame-order diagnostics2, readiness10 all passed.
- Real unsigned112/V1 payload on the guest's installed ARM64 Python/SSL/SDK:
  80.011s,194 KUKSA and194 mutual-TLS VISS connections,194 deliberate reconnects,
  normal exit, no SEGV and no duplicate-frame/non-monotonic warning. Test uses
  temporary synthetic loopback servers/certificates, accelerated timing and
  disabled readiness notification; it does not qualify real service identity,
  long-duration stability or explain the earlier native SIGSEGV.
- VDP112/V1 prepared locally:7paths/no advisory, new current-runtime hashes,
  packaging inspection problems=[]; unsigned SHA
  `a6181f7be3b9e605286846795b827406824ea93bab2a47bd47aa2bb0f1f6dcd3`.
  Operator separately authorized this exact release's selected-OEM signing,
  staging publication and Safe Stop installation on this Test. RS256 verified;
  signed SHA `eff8a8c60eb70936526ce7ff73602bdcc9f661ddaf8fffd21e8bc05ab825c7d4`.
  Release109 and reserved110/111 bytes remain unchanged.
- Before publication: CloudOnline/current109/no pending, actual slot a/109/
  READY, PID71204/NRestarts2. Native Driving Control displays live Test,
  SAFE STOP/STOPPED/0km/h, accelerator0%, brake100%, external networkON.
  The crash cause remains unresolved; updated common code is not called a
  demonstrated native crash fix.

Live112 result: one upload accepted HTTP201 at08:08:57.915UTC, deployment
`8f4f99cf-5296-4a83-928c-bc6a2619ada5`. Authoritative publication READY/Done,
version UUID `4405ab4c-10f7-4d92-a51d-dea9dc0dc22a`; TestOnline/installed112,
no pending component. Actual provider started08:09:03UTC, slot b/112,
PID142419, NRestarts0, `READY/LIVE/NONE`,7paths, installed runtime hash matches
the reviewed source. No manual provider/manager start, forced send or validation
approval was needed. The existing Safe Stop allowed normal FOTA activation.
Automatic core receiver remains armed for the service, including its new PID.
IAM1795/SM2187/CM1831 remain active with0 restarts; stock Enforcing policy hash
is unchanged. No real core has been captured.

Native Autopilot was then activated through Driving Control; observed19.3km/h,
MOVING, live selected Test. A subsequent guest read again reports112,
READY/LIVE and0 restarts. Both driver advisories remain Not available as expected
for this V1 profile; this is not Brake/Tire functionality proof. Brake87 still
reports the previously diagnosed crun failure. The update re-attempted its
existing desired state automatically; no new Brake upload/assignment occurred.
Presenter's Platform card also shows selected/Cloud-installed112. Its hidden
browser observer correctly labels the cached report `Last known`, not a live
claim; no refresh or UI semantics workaround was used for acceptance.

At08:15:13UTC,6m10s after112 activation: samePID142419,READY/LIVE,NRestarts0;
exact runtime/bridge/manifest hashes match1fe5649. The bounded provider window
contains one ready transition, zero reconnect/non-monotonic/SEGV events;
zero fresh VDP-scoped AVCs. Core capture remains armed, no real core yet.
CARLA is intentionally left in Autopilot for further testing. This short
observation is not a long-duration stability qualification.

Full local orchestrator regression:1039 cases,1023 passed,16 skipped,
133.938seconds. Documentation gate passes257 documents/658 IDs/38 diagrams;
`git diff --check` passes. No Factory rebuild or source push is part of this
diagnostic increment.

### Brake native-start and functional proof — 24 September,08:30–08:40UTC

Preserved the same .37 Test, Cloud assignment, installed Brake87 and VDP112.
The exact already-proved three-rule KAC policy was loaded only temporarily,
with a210-second automatic rollback. A preflight checked that CM has no
restart propagation to SM/VDP. One native CM restart (1831→145206) caused SM2187
to start the existing Brake container, PID145278. IAM1795, KAC2232 and VDP142419
were unchanged, with no automatic restarts. Seventy-five seconds of native
container observations stayed running; no scoped AVC appeared in that phase.

An earlier evidence-only attempt compared a compiled policy file's checksum
with the kernel's reserialized policy. That check stopped before CM restart;
stock was restored and all PIDs were unchanged. The corrected proof compares
the complete parsed policy structure and verifies exactly the same three added
rules. The receipts distinguish this harness failure from the real attempt.

Brake then reported `INITIAL_PUBLIC_INPUTS_MISSING`. Its public metadata was
absent, not a new authorization denial or failed model. Standard
`democtl service runtime-prepare test` projected the four public metadata/CA
files from native IAM identity and committed VDP112, with no container/SM
restart. This is the existing pre-assignment preparation step in the Presenter
flow, not a new fallback or service source change. Why the automatic projection
was absent in this preserved migration run still needs a lifecycle check.

The next150-second temporary-policy proof reused the same running container
and restarted nothing. Observed fixed service stages:

- KUKSA_AUTH_CHANGED READY; VDP_CONTRACT_ACCEPTED READY.
- Backend reports Brake87/V1, CONNECTED, input RECEIVING/reasonNONE.
- WINDOW_TRIGGERED→WINDOW_COMPLETED twice; readiness OPERATIONAL.
- Backend window count0→1→2, last delivery receipt08:38:14.682UTC,
  queuedMessages0, deliveryIDLE. No V2 assessment or V3 advisory is expected.
- The standard CARLA Brake exercise completed, operation
  `a6117e67-d615-41d6-a104-78717589e923`:13.3seconds,266frames,
  31braking frames above10km/h, physical final stop confirmed. Backend output
  was checked separately; maneuver completion alone was not acceptance.

No Brake/container_engine/KAC denial occurred during the functional phase.
There were separate VDP-domain `self:process getsched` denials from
`grpc_global_tim` and `event_engine`; preserve this as an open observation, not
permission to grant scheduling changes or suppress logs. Some mixed-timestamp
inputs were correctly rejected; both windows completed. Quantify that timing
behavior before calling the whole source chain clean. VDP112 still hadPID142419,
READY/LIVE and0 restarts at08:41:03UTC, about32minutes after installation;
no core/reconnect/SEGV was observed. The earlier `journalctl -k` AVC summary
misses audit-transport entries, so the evidence helper now searches the full
bounded journal. Do not use the kernel-only zero count as security acceptance.
The corrected read at08:43:18UTC counts60 VDP-scoped AVC records since112
activation; exact distribution/impact still needs analysis. VDP remains
READY/LIVE,PID142419,NRestarts0 with no core, reconnect or SEGV event.

Both policy proof receipts verify stock policy hash and canonical store restored,
Enforcing retained, broad mount boolean off. Source consolidation adds exactly
the three proved rules in platform KAC policy1.1.4 plus negative static checks:
26 targeted tests pass; platform suite198 pass/2 skipped. No image rebuild,
new publication, model/threshold change or permanent guest policy edit occurred.
Because stock policy is restored, subsequent KAC reconnect/renewal can again be
denied until the corrected policy is deployed; running is not durable recovery.
CARLA is left at the maneuver's confirmed Safe Stop; no Autopilot resume was
issued during the policy rollback. Factory/source publication is unchanged.

Evidence: host proof root `run_brake_native_proof.py`, guest private
`/run/factory37-crun-socket-proof-20260924/native-brake-proof-1.json`,
`native-brake-proof-2.json`, `native-brake-functional-1.json` and sanitized backend
counts. These contain no raw credential, token or signal payload.

### UI finding: pending counter combines waiting and failure

The operator saw one pending update. Fresh Cloud inventory08:32:15UTC and the
Presenter Vehicle view08:32:41UTC both showed no pending updates: VDP112 installed,
Brake87 installed/active, pending version fields null. No new version was uploaded
to clear that counter. The earlier unsuccessful Brake startup is the matching
unresolved operation; its exact earlier UI snapshot was not captured.

Source `cloudSummary.ts`/`softwareObservation.ts` counts nonterminal-looking
status strings, including failed/error, as pending. Thus `Software issue · 1 pending`
can mean a failed operation rather than a queued release. Separate failed and
waiting/in-progress counts in a subsequent UI fix; keep Cloud inventory as the
authority and stale-report marking. No UI behavior was changed for this finding.

### Async SM status correction — isolated proof,24 September

Expanded the two original negative controls to five regression cases: initial
activating status; later failure; repeated failure with changed error details and
recovery; callback during StartInstance; stale version/runtime/digest callbacks.
On the original launcher all five cases fail. Besides premature Active, an old
component Inactive callback can remove the current durable record. The type is
part of InstanceIdent; a different type is not treated as the same instance.

The isolated correction preserves the runtime's start snapshot, updates cached
status on matching callbacks, rejects superseded callbacks before storage or
notification, and uses a callback revision to prevent the start return from
overwriting a newer notification. The runtime receives a private status copy,
not the shared cache. A failed start now retains its returned error; one existing
test had expected the old lost-error behavior and was corrected explicitly.

Full ARM64 launcher regression: **32/32 pass**, including existing replacement,
failed teardown, preparation retry, preinstalled-component and listener cases.
This is not a live SM replacement or Safe Stop/Cloud acceptance. Proof files in
the host proof root: `sm-async-expanded-negative-v3.xml`,
`sm-async-candidate-v2.xml`, their logs and `recipe-proof-async-v1/`.

Consolidated as SM recipe patch `0004-preserve-async-instance-status.patch`.
The coordinated source gate applies CM4/SM4/IAM2 patches to their exact pinned
baselines and verifies final changed-file bytes against the tested sources.
The verifier now compares after the complete patch series, with a regression
for two ordered patches touching one file. Platform suite:199pass/2skipped
(201total); mainline-verifier cases4/4. No Factory build or guest replacement.

Harness exclusions: the older temporary GoogleTest fixture had empty file
directories. Restored official GoogleTest v1.14.0 at
`f8d7d77c06936315286eb55f8de22cd23c188571` and built offline in the existing pinned
ARM64 image. A fatal negative assertion skipped shutdown; only that identified
disposable test container was stopped. Corrected cleanup and a warnings-as-errors
brace diagnostic before the completed negative run; neither is product evidence.

### Public-input lifecycle and VDP security follow-up

At08:54:30UTC, the packaged projector exactly matches current source
SHA256`13eaf424af56a2d172714c5aff7d1122b7e8824b755a634c1d3054d17a335203`.
Cold/verify startup receipts remain DEFERRED/SERVICE_INPUT_STARTUP_UNAVAILABLE
from early boot. Current Brake/Tire public metadata files were written by the
explicit preparation at08:35:32UTC. The preserved assignment receipt records
the low-level `service.assign` operation, which does not itself prepare inputs.
Presenter's composed service-assign plan does run runtime-prepare before Cloud
assignment and stops on failure or unknown outcome. Its17/17 operation tests
pass, including that ordering and no-replay cases; the initial sandbox denied
two fixture loopback binds, and the same suite passes with those binds allowed.

Do not infer an automatic projector failure on later VDP commits from these
early-boot receipts, or add a launcher/restart fallback. The future sequential
CLI flow must explicitly retain the existing preparation step. Cold recovery
and the next real version transition still require live observation.

At08:50:02UTC the VDP journal contains68 denial records:4directory getattr,
4credential-file ioctl,1sysfs read,1proc read,1node_bind,57self-process getsched.
Only getsched repeats after startup (event_engine/grpc_global_tim). By08:57UTC
the total is70; provider remains PID142419, READY/LIVE, NRestarts0, with one ready
transition and no reconnect, stale, SEGV or captured core. These are denial
records, not necessarily unique syscalls. A subsequent read could not correlate
audit serial/syscall records; exact call sites and effect remain unproved.
No scheduling permission, broad read/bind access or dontaudit was added.

Final read09:07:27UTC:112 remains READY/LIVE with the same PID142419 and0restarts,
58minutes24seconds after activation. No reconnect, stale, SEGV or core; capture
remains armed. The cumulative VDP denial-record count is78, so the security gate
is still open. No guest mutation, runtime restart, publication or simulation
command was performed during this follow-up. Documentation gate passes257documents,
658stable IDs and38diagrams; platform source/license/credential gate passes242files.

### SM production-toolchain target and isolated AVC proof —24 September09:37UTC

Started only the dedicated Builder (SSH10024; preserved warm disk/cache). In a
fresh private proof directory compiled the SM application and launcher tests
against the actual .37 recipe toolchain/sysroot. Applied only patch0004 to a
private dependency copy; source and regression hashes match the earlier proof.
All32 target launcher tests pass. Stripped AArch64 PIE candidate5,599,048bytes,
SHA256`3a7f15f32250b3f9d4568b16d2ea9792dde5246b2bb3fc4d58032646b67e57e9`.
Host evidence: `sm-async-builder/receipt.json`, `launcher.xml`, `elf.log` in the
preserved proof root. Builder evidence: `/home/yocto/r61-build/sm-async-live-proof`.

The initial configure failed before compilation because the standalone harness
omitted Yocto's `PKG_CONFIG_*` exports. Reused the reconciled private tree with
those original exports; no patch replay or product modification was necessary.
No formal image/package task ran. The candidate was copied only to
`/run/factory37-sm-async-proof/aos_sm_app`; no ExecStart drop-in exists and stock
SM remainsPID2187. Execution review rejected the proposed live replacement and
temporary KAC-policy/restart proof before script creation/execution. Exact
operator confirmation was requested. No service or policy mutation followed
that rejection; do not report live acceptance from the native test result.

Isolated gRPC diagnosis used installed grpcio1.75.0 but no real configuration,
credential or telemetry. The first diagnostic executable in `/run` did not enter
the VDP domain because of nosuid_transition; it was stopped and is excluded from
product-equivalent evidence. Corrected the harness using the unchanged installed
VDP launcher and a read-only diagnostic payload bind in its own systemd unit's
private mount namespace. Verified UID998/GID996, sole supplementary996, empty
capability sets, NNP1 and `vehicle_data_provider_t`; all existing sandbox options
were retained. Working VDP PID142419 and policy remained unchanged.

| Probe | Result |
| --- | --- |
| Closed local endpoint, three bounded connect attempts | Expected timeouts, clean close;113 getsched,2read,1node_bind denials |
| Independent synthetic loopback server,10 unary calls |10/10 success and clean close;3getsched,2read,1node_bind denials |
| Filtered child-only syscall trace | sched_getaffinity, sched_getparam, sched_getscheduler and bind returnEACCES |
| Rollback/isolation | Diagnostic units stopped; server stopped; stock policy and live VDP unchanged |

The getsched operations are scheduler inspection, not priority changes. Successful
RPCs prove those reproduced denials are not independently fatal to this exchange;
they do not identify the old SEGV cause, qualify production token renewal or prove
all startup denials harmless. No permission grant or dontaudit was introduced.
Sanitized receipts are in `vdp-avc-evidence/receipt*.json`; raw cores/credentials
were not collected. The audit journal supplies AVC envelopes but no correlated
SYSCALL records for these events, so missing joins are not evidence of no denial.

After same-domain probes, cumulative domain-wide AVC counts include deliberate
diagnostic denials. At09:37:20UTC there are237 domain records but114 for the real
VDP PID; the helper now reports them separately. VDP112 is READY/LIVE after
88minutes17seconds,0restarts, one readiness transition and no reconnect, stale,
SEGV or core. Core capture remains armed under the previously recorded expiry.

Fresh authoritative Cloud read09:35:42UTC: UnitOnline, VDP112 installed,
Brake87 active, no pending component/service version. Hidden in-app Presenter
properly marks reports last-known with OBSERVER_HIDDEN; this is not evidence
that the Unit is offline. Native Driving Control visually confirms LIVE,
SafeStop,0km/h and100%brake; advisory Not available is expected for this V1 setup.
Backend09:36:24UTC retains both V1 windows, no assessment/advisory, queue0;
current connection STARTING/inputWAITING is observed with stock KAC policy
restored. Do not claim the earlier transient access fix is permanently deployed.

Documentation gate passes257documents/658IDs/38diagrams; current targeted
mainline/KAC Python tests16/16 and both Git whitespace checks pass. The dedicated
Builder was stopped cleanly after compilation, preserving disk/cache/evidence;
the adapter confirms no demo-VM or Cloud mutation. Temporary SM candidate and
sanitized diagnostic receipts remain inactive on Test for the pending live gate.

### Authorized SM live proof and rollback —24 September09:44UTC

The operator explicitly approved the previously rejected bounded action. One
journaled proof began09:44:35UTC on the same .37 Test and guest boot, with CARLA
confirmed SAFE_STOP. Only SM ExecStart was temporarily redirected to the
hash-verified production-toolchain candidate. The active policy added exactly
the three previously proved KAC rules; Enforcing, labels, identities, group
checks and the canonical policy store were unchanged. A210second independent
watchdog restored the original SM/policy on loss of the controller or deadline.

| Check | Observed result |
| --- | --- |
| Candidate first start | SM PID155182, active, NRestarts0; stable at10/20/30seconds |
| Explicit repeat restart | Candidate SM PID155351, active, NRestarts0 |
| Preserved managers/provider | VDP142419, IAM1795, CM145206, KAC2232 unchanged |
| Functional read during candidate | Brake87 CONNECTED/RECEIVING, reasonNONE; backend retained two V1 windows |
| Cloud read09:45:16UTC | Online, VDP112 installed, Brake87 active, no pending/error;0.791s read |
| Rollback | Stock SM PID155513; original binary and canonical store unchanged; active stock policy restored; ExecStart override removed |
| Watchdog/evidence | Exit0, receiptCOMPLETE; guest `/run/factory37-sm-async-proof/receipt.json`, host `sm-async-builder/live-receipt.json` |

The live candidate is the previously compiled SHA256
`3a7f15f32250b3f9d4568b16d2ea9792dde5246b2bb3fc4d58032646b67e57e9`.
Restored stock SM SHA256
`a21038c77ce19c55de7cf261c7f288f9105b30dfd14a0b8125b8b78800153fc2`.
No new Factory, guest reboot, Cloud assignment or CARLA restart occurred.
Inactive candidate/evidence remain in `/run`; no debug content was installed
into immutable rootfs. The Builder remains stopped with its caches preserved.

All three SM starts caused the ordinary Brake process restart. Fixed events
show expected AUTH_PENDING then KAC READY; mixed-timestamp rejection remains
fail-closed rather than being masked. Backend generation3 was observed during
the candidate repeat; IDLE/queue0/lastReceiptAtnull refers to that new generation,
not loss of the two existing V1 windows. WAITING/NOT_QUALIFIED is expected while
stationary without a new qualifying braking episode. No assessment/advisory is
expected from V1. No KAC/container/VDP denial occurred in this proof's fresh
audit window; two generator and eleven SSH denials are separately recorded and
not resolved by new permissions. Do not call the entire audit clean.

Warm public-input recovery is now proved: cold PREPARED and verify VERIFIED
hooks completed at09:44:38,09:45:10 and09:45:27UTC. Brake/Tire public metadata
mtime remained08:35:32.424469UTC; projector bytes match the recorded source.
No fallback or repeated overwrite was added. Cold boot and next-version
projection remain separate unexecuted gates.

Post-rollback Cloud read09:48:54UTC took0.704seconds and retained Online /
112 installed /87 active /no pending versions. VDP read09:48:56UTC: READY/LIVE,
same PID142419,0restarts,99minutes53seconds continuous, no reconnect, stale,
SEGV or core. Real-provider AVC count124 is distinct from247 domain-wide
records including deliberate probes. Crash capture is still armed; its explicit
removal gate and prior24hour expiry remain required. Stock-policy restoration
means future KAC reconnect can still encounter the known access defect.

This proves candidate startup, warm restart, function and rollback, not yet the
real next-version asynchronous/Safe Stop transition or long-run token renewal.
Those live gates remain additional to the32/32 production-toolchain tests.

### Current-runtime next candidates and resource baseline

Prepared each profile once locally, without signing/upload or live installation.
Native package inspection reported no problems and verified the common/advisory
runtime modules against reviewed tree`cfc2e0c790c179ddc10f734f0def0361535154c0`.
Historical110/111 and all published bytes remain unchanged.

| Version | Profile | Read paths / advisory endpoints | Unsigned bundle SHA256 |
| --- | --- | --- | --- |
|113.0.0|V2|15 /0|`6bfe87c298bcc95df73ec63ced9ce2b093147617ddf1dbfbb950a9dfe4eb06d3`|
|114.0.0|V3|23 /2|`6c4029451fccc4dfc2c575fcb9a15e8df62a96bf9ecb365e87ddba3f228aca44`|

Both identify immutable Factory .37 and have matching outer, inner, provider and
capability versions. V2 is COMMON_RUNTIME_IMPLEMENTED_NOT_LIVE_QUALIFIED; V3 is
ADVISORY_RUNTIME_IMPLEMENTED_NOT_LIVE_QUALIFIED. Packaging inspection is not a
signature, installed-runtime or Cloud qualification.

Baseline read09:55:44UTC: running Brake87 PID155564 retains UID/GID5000.
State file is0600/inode64772; storage directory0755/inode15. Numeric user-quota
rows exist on both configured filesystems: storage28KiB used/8192KiB hard limit;
state0KiB used/1024KiB hard limit. Both reads exit0, neither reports`none`.
The first diagnostic used a singular storage path and returned exit2; corrected
the harness to read the actual SM storageDir (`/var/aos/storages`). This was not
a product quota failure, no quota was changed, and no mutation was retried.

Authoritative Cloud monitoring read09:54:57UTC took0.728seconds; samples at
09:54:47.807821UTC include Brake CPU6DMIPS, RAM2408448bytes, storage28672bytes,
state0bytes, inbound/outbound0bytes. Controller resource rows are also present.
The separate usedDisk field is NOT_REPORTED; the disk partition rows are real
and complete. Local-private traffic zero remains the previously documented
accounting behavior, not evidence of no service/backend communication.
Retain this pre-update baseline for the real stable-UID/quota88/89 comparison.

Final read10:00:12UTC: VDP112 remains PID142419, READY/LIVE, NRestarts0,
111minutes9seconds since activation; no captured core, collector still armed.
Real-provider AVC count134 remains separate from257 including diagnostic probes.
Targeted mainline/KAC regressions16/16 and common-runtime regressions4/4 pass.
Documentation gate passes257documents/658stable IDs/38diagrams; both repositories'
Git whitespace checks pass. No commit/push, new package/image build or further
external mutation was performed in this continuation.

### Historical stop gate at10:00UTC

The new Test and its diagnostic state remain preserved; VDP112/V1 is really
active with the reviewed current runtime. Brake87's native start and two delivered
V1 windows are proved under the narrow transient candidate; stock policy is
restored and permanent deployment is not yet qualified. The bounded SM first/
repeat start passed and stock SM is restored too. VDP113/114, Brake88/89 and
Tire48 remain local unsigned candidates; superseded110/111 must not be used.
Exact authorization was requested for113/114 signing/publication to selected
staging and Safe Stop installation on this Test only, plus at most90minutes of
the proved transient SM/three-rule policy with automatic rollback for the next
sequential run. Earlier Brake88/89/Tire48 approval remains unchanged. No such
next-stage external attempt has started. UID/quota/resource-metric upgrades, Tire maneuvers,
network OFF/ON, persistence and final Finish are still **not executed** for .37.
The candidate is not live-qualified; .36 remains the preserved baseline.

### Authorized sequential runtime proof —24September10:06UTC onward

Exact operator approval opened the113/114 publication gate and a maximum90minute
temporary SM/KAC proof on the preserved Test. An independent guest watchdog
started10:06:22UTC, deadline11:36:22UTC, and restores stock SM/policy on an
explicit finish marker, a captured VDP core, or the deadline. The original
binary and canonical policy store are not edited. Only the three previously
proved KAC rules and the hash-verified SM candidate are active during this proof.
All times below are UTC; observed UI times are bounds, not continuous latency
measurements. Published historical110/111 remain unchanged and unused.

| Release | Upload accepted | Deployment ID | Authoritative/live result |
| --- | --- | --- | --- |
| VDP113/V2 |10:07:16.107|`aaaa1319-c3de-4805-abbc-dfccd9575f4f`|Installed slot a at10:07:21, PID158624,15paths/0advisory endpoints; Presenter observed113 at10:07:48 |
| Brake88/V2 |10:09:38.408|`4e90167d-21df-4e59-aae3-a1c2e2121942`|Cloud active at10:10:22; real V2 assessment received10:11:14.211 |
| VDP114/V3 |10:12:40.832|`8cd50522-28be-4b55-9f31-ad50eb8bd542`|Installed slot b at10:13:26 only after Safe Stop; PID159575,23paths/2advisory endpoints |
| Brake89/V3 |10:14:31.349|`7ff3b8aa-bc4d-49a1-9340-dcddd1e32b3d`|Cloud active10:15:14; real assessment10:17:15.767, Gateway APPLIED10:17:15.951 |
| Tire48/V1 |10:15:41.035|`f71334e1-d0a0-4bb4-8425-642634889d49`|READY10:16:02; dedicated assignment complete10:16:27; Cloud active10:16:44; real assessment10:18:08.223 |

Each next release was published only after its predecessor was installed and
checked. No bulk latest-version upload was used. Tire's service UUID is
`b845eef2-bf81-4035-895f-4a013d6b956f`, version UUID
`ccba3f92-9066-49ed-bb8e-d14c73065438`, dedicated subject
`ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb`. All writes target this staging Test only.

Signed immutable bundle SHA256:

| Release | SHA256 |
| --- | --- |
|113.0.0|`0ab1110836b2e9ffa2a1e2acbc6307b61c250ce5231a6e41e04dcd6e219be5c7`|
|88.0.0|`ea8e1437d2e4cbdf4432d3d7dadeeb647bb1ee305bcf6713254b445e3bc02513`|
|114.0.0|`425febece9cd9be0faa5c737a08374b395254a16057e9bad998f3fabef8b1454`|
|89.0.0|`bc454ea18bb6b2beecd9d8a30a840c4e64b65300f679fcd1dbc3db1c0a429442`|
|48.0.0|`5e99867aac21ffae93e56fed5a46c5c0ea253a61a43604b9709a822b521c0a7d`|

#### Safe Stop, public inputs and UI truth

At10:12:56, Cloud still reported113 installed and114 pending; the live runtime
was waiting-for-safe-stop. At10:13:00 native Driving Control showed Autopilot
moving19.4km/h. Presenter explicitly requested Safe Stop and did not replace
the installed version prematurely. Native Space then produced Safe Stop;
114 installed10:13:26, Cloud confirmed114/no pending10:13:42.97, and Presenter
showed that result10:14:03.69. This is a real asynchronous negative/positive
proof for the SM candidate, not just its earlier same-version restart test.
Brake updates were requested while Autopilot was selected; traffic stops
occurred, so continuous physical motion throughout installation is not claimed.

After both113 and114, standard `service runtime-prepare test` returned no-op
with current-version verification. Existing public metadata remained valid.
Brake89 initially displayed “Waiting for braking result” / “No current-release
result” while retaining the previous88 assessment in history. Native Brake
showed Monitoring; Tire showed Waiting for service until assignment. Both
showed Inspection recommended after their real applied advisory.

#### Stable UID, persistence and resource observations

| Check | Result |
| --- | --- |
| Brake87→88→89 UID/GID |5000 throughout |
| Brake state/storage |Same inodes64772/15; no cleanup loss |
| Brake quotas |State1024KiB / storage8192KiB hard limits remain numeric |
| Brake storage used |28KiB baseline →56KiB after88 →76KiB after89 →92KiB after maneuvers |
| Tire identity/storage |UID/GID5001; state inode32388, storage inode32;2048/4096KiB hard limits;48KiB storage used |
| Cloud metrics |Fresh CPU/RAM/storage rows after both Brake upgrades; example88 sample10:10:29.546769:26DMIPS,2850816B RAM,57344B storage |
| Retained functional history |V1 windows survived88; V2 assessment survived89;89 added new assessments |

This closes the observed clean-upgrade UID/quota/metric path, not repair of
legacy mismatched records or persistence through a new VM boot. No quotas or
model thresholds were manually changed. Inbound/outbound zero on private demo
routes remains the documented accounting boundary, not absence of traffic.

#### Independent UI Reset and Return to road

After exact operator confirmation, clicked each card's Reset Driver Advisory
once. Brake showed ACCEPTED / waiting for Gateway CLEAR, then confirmed CLEAR
at10:25:48. Native Brake changed to Monitoring while Tire stayed Inspection
recommended. Tire then confirmed CLEAR at10:26:31 and changed to Monitoring;
Brake remained Monitoring. Presenter correctly said “No new result after reset”
instead of treating historical assessments as a new healthy result.

At10:27:10 both backends still held all prior assessments/events: Brake3/1,
Tire2/1. Their advisory histories also remained (Brake26, Tire29), including
historical SET records; latest history is not current advisory state. Input
remained CONNECTED/RECEIVING, queue0, same generations7/1. These are Reset
receipts, not vehicle-repair or new-assessment claims.

Clicked native Return to road once. UI reported “On road · stationary Manual”;
local status confirmed fresh, held=false, phaseRELEASED, MANUAL, moving=false,
physicalStop=true. Both advisories remained Monitoring. The subsequent native
Autopilot action was blocked by safety review before execution and separately
requested; therefore post-return driving is not yet passed.

#### Exceptions and remaining proof boundaries

- A Brake maneuver attempted while Tire assignment still held the writer lock
  returned CURRENT_RUN_BUSY before starting. After assignment completed and
  the lock was authoritatively RELEASED, one allowed maneuver completed. This
  is harness serialization, not a failed service or concurrent mutation proof.
- Network OFF was rejected by execution review before the command started.
  Exact OFF for five minutes → local maneuvers → ON confirmation is pending;
  no offline behavior, queue growth or reconnect pass is claimed for this run.
-10:21:25 health read: SM158393, CM145206, IAM1795, KAC2232 and VDP159575
  active with0automatic restarts; no core/SEGV. Brake/Tire bootstrap PIDs
  159811/160096. VDP READY/LIVE. Fixed90second logs include a Brake
  KUKSA_REAUTHENTICATING readiness transition and subsequent OPERATIONAL,
  and NOT_READY/READY publications. Do not claim uninterrupted readiness or
  token-renewal UI stability from occasional screenshots.
- Same interval had20VDP getsched and20SSH search denials; no container/KAC
  denials. These separate security observations are not suppressed or solved.
- UI candidate for later review:10:14:08 displayed CPU1802DMIPS while the
  graph scale label rounded to0–1800DMIPS. No formatter source fix or continuous
  latency/status-flip audit has yet been performed for that observation.
- Crash capture remains armed, guest-local and bounded, with its earlier
  24hour expiry. No dump has been captured; historical109 SEGV is not solved.
- No Factory rebuild, guest reboot, Production change, Finish/delete, commit,
  push or cleanup was performed. .36 remains the accepted immutable baseline.
  Rollback of the temporary SM/policy is mandatory before handing off this run;
  its final verification follows.

#### Final rollback and handoff state —10:31–10:32UTC

Explicit finish marker triggered the existing independent watchdog at10:31:12;
verification completed10:31:15.802. Guest receipt
`/run/factory37-e2e-lease/rollback.json` reports RESTORED / REQUESTED. All four
checks passed: active stock policy restored, original SM binary unchanged,
canonical policy store unchanged, ExecStart drop-in removed. SELinux remains
Enforcing. Stock SM PID162197 is active with0automatic restarts; VDP159575,
CM145206, IAM1795 and KAC2232 are unchanged. No VDP core was captured.

The ordinary SM restart restarted both service containers (Brake162247,
Tire162244; generations8/2), not the VM or VDP. At10:31:57 both backends still
reported CONNECTED/RECEIVING with queues0 and the same retained history counts.
Tire's function-observation advisory axis was UNAVAILABLE/requestIdnull after
the restart, while native availability remained Monitoring: command/advisory
history and readiness are separate axes, not interchangeable evidence.
At10:32 native UI showed LIVE, stationary Manual, external networkON and both
advisories Monitoring. No new recommendation or assessment was invented.

Cloud read10:31:54.835 took0.835s: UnitONLINE, VDP114 installed, Brake89/Tire48
active, no pending versions/errors. Restoring the stock KAC policy restores its
known access restriction for later renewals/start paths; this is intentionally
not presented as a permanent deployed fix. Core capture remains armed under
its prior bounded expiry/removal gate. Network OFF/ON and post-return driving
remain blocked before execution pending their exact user confirmations.

Documentation quality gate passes257Markdown documents/658stable identifiers/
38Mermaid diagrams; Git whitespace checks pass for both edited repositories.
Only evidence/planning documents changed in this continuation; earlier source
changes remain intact. Full migration acceptance is still open.

### Continuation: driving and stock-policy network control —24September10:35UTC

The operator requested continuation after the exact driving/network gates were
reported. Native Autopilot was selected once; source status10:36:01 confirmed
fresh AUTOPILOT, moving=true, physicalStop=false. Native dashboard showed
19.2km/h and MOVING. Native Space then returned Safe Stop;10:36:53.682 source
read confirmed SAFE_STOP, moving=false, physicalStop=true. This closes the
post-Return-to-road driving check without a simulator or VM restart.

The stock-policy baseline exposed the expected KAC access regression after
the temporary proof ended. Fixed-field journal correlation proves ordering:

| UTC | Observation |
| --- | --- |
|10:31:14|Both bootstrap processes obtained KAC access during stock-SM restart, before policy rollback finished |
|10:34:14.615 / .619|First renewed directory-search denials for Brake/Tire bootstrap respectively: container_engine_t → aos_kuksa_auth_runtime_t |
|10:36:14.014 / .068|Both reported KUKSA_AUTH_UNAVAILABLE; analytics became KUKSA_AUTH_PENDING by10:36:15 |
|10:36:46 / .48|Final pre-OFF backend observations already STARTING/inputWAITING |
|By10:37:14|One normal `vehicle connectivity off --target test` completed |
|10:37:48.400|Authoritative Cloud read reported OFFLINE, same identities and114/89/48 |

Thus the native Unavailable labels are not evidence that network OFF caused
the local input failure: that failure preceded OFF. No maneuver is counted as
an offline analytics proof with this invalid baseline. SM/CM/IAM/KAC/VDP and
both service PIDs are unchanged and VDP remains READY/LIVE with0restarts/no core.
At10:37:47 and10:40:08 backend heads/sequences and history counts were unchanged;
Brake retained3assessments/1event and Tire3/2. The additional Tire GOOD result
was received at10:36:06 during the preceding Autopilot run, not during OFF.
Tire had2queued outbox files at10:37:47; their payload was not read.

Presenter's hidden in-app tab first showed OBSERVER_HIDDEN/last-known. Once
shown through its ordinary visibility control, fresh Cloud observation showed
Offline while old CPU/RAM samples remained Last known. Later input expired to
Last known/Not confirmed; old Tire GOOD retained its explicit received age.
This is not an observed stale-Online failure. Native driving telemetry remained
LIVE and responsive while the two local advisories were Unavailable.

Requested a separate maximum20minute, automatically rolled-back window with
only the previously proved three KAC rules, without replacing SM or restarting
any workload. That activation is pending explicit confirmation. Targeted
mainline/KAC regressions pass16/16. Network restore/recovery is recorded below
after the five-minute observation completes; no full offline-service pass yet.

#### Five-minute OFF/ON result —10:42UTC

OFF was confirmed by10:37:14. The one explicit ON invocation began10:42:25
after more than five minutes and completed successfully. Tire's backend
connection event returned CONNECTED at10:42:32.952; Cloud authoritatively
reported ONLINE at10:42:51.094 (read finished10:42:52.049,1.419s). Presenter
visibly showed Online on the10:42:59 snapshot. These are observation bounds,
not exact first-transition latency or a30minute RabbitMQ timeout qualification.

At10:42:54, all five manager/provider PIDs and both service PIDs matched the
pre-OFF baseline, with0automatic manager/provider restarts and no core.
Tire's outbox returned from2files to0. New function-observation receipts arrived
for Brake at10:42:42.170 and Tire at10:42:53.066; histories were preserved.
The known KAC failure remained STARTING/inputWAITING, so resumed backend
transport is not resumed analytics or a local offline-inference pass.

Native UI remains LIVE, Safe Stop, external networkON, both advisories
Unavailable. The network-control/Cloud-reconnection subset passes: no manual
CM restart, reinstall, reprovision or identity change was needed. Local
offline analytics, new advisory and full queued-result replay require the
separately requested three-rule KAC window and a valid pre-OFF baseline.
No policy was re-enabled in this continuation and no temporary SM remains.

Connectivity unit regressions14/14 and mainline/KAC regressions16/16 pass;
documentation and both Git whitespace gates pass. An initial test command
selected unavailable pytest and ran no tests; the project's unittest runner
then executed the14cases. No package installation or product change was needed.

### KAC-only local offline and queued-delivery proof —24September10:51–11:03UTC

The operator explicitly authorized the previously requested maximum20minute
KAC-only window. This closes the local-offline gap in the preceding stock-policy
control test; it does not replace or relabel that invalid-baseline result.
No SM replacement, workload restart, new release or model/reset change occurred.

#### Guard and pre-OFF baseline

Activation10:51:31.123UTC armed an independent guest watchdog with deadline
11:11:31.123 and explicit-finish/core/deadline rollback. Guest metadata is
restricted to `/run/factory37-network-kac-lease` (0700 directory/0600 files).
Structural comparison accepted exactly these three added rules and no others:

```text
allow container_engine_t aos_kuksa_auth_runtime_t:dir { getattr search };
allow container_engine_t aos_kuksa_auth_runtime_t:sock_file write;
allow container_engine_t aos_kuksa_auth_compat_t:unix_stream_socket connectto;
```

The active stock policy hash was
`0974d04f730ed91042963e504031dd152efe6067eb3e2925d70585c5781c4faf`;
candidate file SHA256
`082434ed661d8b3129a6063703c286ec6c322bd6940b7e5836094d5cd3ee0ffd`.
Canonical policy store and stock SM binary were unchanged; no ExecStart
override remained. Enforcing and the disabled broad mount boolean were retained.
SM162197, CM145206, IAM1795, KAC2232, VDP159575, Brake bootstrap162247/inner162248
and Tire bootstrap162244/inner162251 were unchanged through the entire cycle.

Tire reached READY10:51:47.404; Brake regained KAC at10:51:58.121 and backend
CONNECTED/inputRECEIVING by10:52:29.453. Native advisories showed Monitoring.
Pre-OFF heads were Brake generation8/sequence43 and Tire generation2/sequence51,
queues empty, histories Brake3assessments/1event/26advisories and Tire3/2/30.
Thus this cycle began with valid local input and authorization, unlike10:37.

#### Real processing while external network was OFF

One standard `vehicle connectivity off --target test` completed by10:52:40.
Authoritative Cloud read10:53:12.646 reported OFFLINE with the same Unit and
installed114/89/48, no pending version. Native controls remained LIVE.

- Clicked native Brake Maneuver once. It completed in Safe Stop; a real Brake
  window produced an assessment at10:53:07.203 (journal completion10:53:07.225).
  A completed window is not necessarily a new warning. Tire rejected that
  brake-only episode on input quality; it is not counted as its maneuver.
- Clicked native Tire Maneuver once. Its dedicated exercise produced an
  assessment at10:54:09.301 and Gateway APPLIED at10:54:09.460. Brake independently
  produced a second assessment10:54:10.954 and APPLIED10:54:11.294.
  Native UI visibly showed both Inspection recommended while networkOFF.
- Token replacement/reauthentication was observed offline at10:54:46.234 for
  Tire and10:54:58.382 for Brake, followed by recovered readiness. No Cloud or
  service restart was needed. Brief NOT_READY/READY publications remain present;
  do not claim uninterrupted availability or suppression of real reauthentication.
- Backend heads/sequences/counts were unchanged on10:53:47 and10:55:56 reads,
  eventually marked stale. At10:55:53, Brake had11queued files (5in V2outbox,
  6in V3outbox) and Tire15. Only counts/metadata were inspected, not payloads.

#### ON, receipt timing and UI reconciliation

With local Safe Stop verified, ON was invoked once at10:57:57UTC, after more
than five minutes OFF. Tire transport became CONNECTED10:58:07.867 and Brake
backend sync CONNECTED10:58:24.073. Cloud reported ONLINE at10:58:42.045
(read finished10:58:42.403,0.801s), with114/89/48 and no pending version.
These are sampled transition bounds, not exact first-Online latency.

| Offline fact | Original source time UTC | Backend receipt UTC | Source-to-receipt delay |
| --- | --- | --- | --- |
| Brake assessment1 |10:53:07.203|10:58:24.069|316.866s|
| Brake assessment2 |10:54:10.954|10:58:24.035|253.081s|
| Brake warning event |10:54:10.903|10:58:24.170|253.267s|
| Brake first APPLIED |10:54:11.294|10:58:24.048|252.754s|
| Tire assessment |10:54:09.301|10:58:08.578|239.277s|
| Tire warning event |10:54:09.301|10:58:07.882|238.581s|
| Tire first APPLIED |10:54:09.460|10:58:08.092|238.632s|

All these results were produced locally during OFF and received only after ON.
Source ordering and delivery ordering differ; both timestamps are retained,
not rewritten to make a queued old result appear newly measured. At10:58:44
both outboxes contained0files and all manager/provider/service PIDs were unchanged.
No automatic manager/provider restart, core or SEGV was recorded.

Brake assessment/event counts grew3/1→5/2; Tire3/2→4/3. Metadata reread at
11:03:55 retained those counts, every record identified and IDs unique, with
no next page. Advisory history increased with normal renewal records, each
unique by producer epoch/sequence; growing advisory count alone is not duplicate
delivery. This bounded record check is not a general exactly-once guarantee.

At11:02, Presenter showed Online, Result received / Inspection recommended for
Brake and Inspection recommended for Tire; native panel agreed on both warnings,
LIVE telemetry, networkON and Safe Stop/0km/h. Old Reset receipts stayed explicitly
labelled with their earlier release/time and were not treated as current advisory
state. No new UI contradiction was found in these snapshots; they do not replace
a continuous latency/readiness-flip audit.

#### Verified rollback and exclusions

Explicit finish ended the lease at11:03:10.917UTC; receipt verified11:03:11.964:
RESTORED/REQUESTED, stockPolicyRestored, stockBinaryUnchanged,
canonicalStoreUnchanged, enforcing and managerPidsUnchanged all true. Stock
SM remains162197; other managers and VDP unchanged. The new20minute lease is
distinct from the already-restored90minute `/run/factory37-e2e-lease`.

Fixed-field journal from activation through11:02:41 contains no KAC denials.
Separate getsched AVCs from VDP and search AVCs from SSH persist; they are not
included in this policy grant or hidden. Tire briefly reports KUKSA_DATA_UNAVAILABLE
then READY at10:59:25 and11:00:46; Brake reauthentication/readiness publications
also remain visible. Successful offline inference/replay does not close those
transient-readiness observations or the historical109 SEGV investigation.

This passes the bounded local-offline/authorization/advisory, backend-isolation,
queue-drain and Cloud-reconnection gate with the minimal integration correction.
It does not qualify a30minute RabbitMQ timeout, cold persistence, crash/security
closure or permanent image integration. Restoring stock policy restores the known
KAC restriction, so later token renewals can again fail on this diagnostic Test.
The source fix is not yet deployed permanently in Factory .37.

Final read11:07:03 confirms the rollback-negative result: Tire is again
KUKSA_AUTH_PENDING from11:05:47.085 and Brake from11:05:59.089, after their
existing tokens expire; fresh container_engine_t search denials recur. All
manager/provider/service PIDs remain unchanged, VDP READY/LIVE, no core/SEGV,
and all outboxes are empty. Cloud still reports ONLINE at11:07:00.427 with
114/89/48 and no pending version. Thus current local analytics are unavailable
again even though Cloud/transport is healthy; do not hand off the earlier
temporary-policy success as the present permanent runtime condition.

VDP core capture remains intentionally armed under its earlier24hour expiry and
mandatory removal checklist; no core exists. Network isON and the vehicle was
left in Safe Stop. Preserve the current Test, .36/.37, Builder/caches and evidence;
no Finish/delete, reboot, Factory build, upload, Production change or cleanup.
Only these three evidence/planning documents changed in this continuation;
earlier source changes are preserved. No commit/push was performed.

Re-ran KAC12/12 and mainline4/4 unit regressions. Documentation gate passes
257Markdown documents/658stable identifiers/38Mermaid diagrams; both repository
Git whitespace checks pass. Solution HEAD remains
`f0420e393ad6a90cccd49d79083a64e0dc6ca04f`; platform HEAD remains
`77d99770a3d9476736da55c3e2196396899bc563`, with the previously documented
uncommitted source corrections preserved. No package/native rebuild was needed
for this metadata-only continuation of the already compiled policy proof.

### Regression origin compared with .36 —24September11:24UTC

The operator requested the cause of regression before continuing the remaining
crash/security and successor-image gates. Immutable .36 sourcea0f88d8f and
.37 source77d99770 comparisons confirm distinct upgrade integration defects:

| Boundary | Before | After | Classification |
| --- | --- | --- | --- |
| KAC access | App9eecb80c runs libcrun inside SM with effective initrc_t access | App9c8a27ec executes crun; the Factory transition produces container_engine_t, without the retained KAC directory/socket access | Platform security integration missed a changed upstream launcher/domain contract; affects both Brake and Tire |
| VDP activation status | Lib60cb8353 preserves status returned by the runtime | Lib9eb7d42e writes Active after successful StartInstance, even when the asynchronous runtime is still waiting for Safe Stop | SM launcher status regression; actual Safe Stop was not bypassed |
| V1/V2 runtime freshness | Old immutable payload code replayed with new metadata | Reviewed common source overlay selected only for V3 | Solution packaging gap predating migration, not a proved AosCore defect |
| VDP SIGSEGV | No comparative old/new native failure stack | Two109/V1 crashes follow reconnect warnings | Cause and relationship to migration remain unproved |

The exact app change is
[9c8a27ec168b6e0cab84b827a27dfedac359797b](https://github.com/aosedge/aos_core_cpp/commit/9c8a27ec168b6e0cab84b827a27dfedac359797b),
committed18August2026, replacing libcrun_container_run with
ExecDetachedCommand/crun run -d to preserve container stdout/stderr. KAC's
implementation/recipe, the complete refpolicy-files directory and demo resource
mount declaration are unchanged between .36/.37. Keeping that integration
unchanged while adopting the new runner was our migration compatibility omission;
native IAM rights, certificates and service models did not need to change.

The status change is traced independently to
[9eb7d42edab6b28f12f14e02df037bf8f2f7846e](https://github.com/aosedge/aos_core_lib_cpp/commit/9eb7d42edab6b28f12f14e02df037bf8f2f7846e),
also committed18August2026. AddStartInstanceTask adds an unconditional eActive
write after success; previous StartInstanceTask delegated the output status.
Inspected upstream launcher tests mostly mock immediate Active and contain no
eActivating case. Our five negative controls,32-case candidate suite and live
moving→Safe Stop check above cover the previously missed asynchronous contract.

The424 native cases and initial unprovisioned boot/repeat did not run a real
Brake/Tire bootstrap through the new compiled SELinux domain and token renewal.
They were never sufficient for live .37 acceptance. Future migration gates must
pair the runner with its effective identity/policy, exercise accepted asynchronous
return states, and check common runtime code in every prepared profile.

Read-only `regression_origin_audit.py` in the proof directory passed11:23:41:
immutable launcher comparisons, unchanged KAC/policy/mount assertions and policy
negative controls. The new minimal-policy validator rejects both historical
policies for the *new* runner contract and accepts the corrected working tree.
This does not call .36 defective under its old launcher. No live mutation.

V3-only reviewed-source selection already exists in solutionf21476f,
20September, before migration. The new common-runtime packaging tests prevent
that omission without rewriting historical releases. It explains missing common
fixes in109, not the native crash itself.

Fresh VDP read11:23:48:114/V3 PID159575, READY/LIVE,0restarts,70m21s continuous;
one ready transition since10:13:26, no matched stale/reconnect/non-monotonic/SEGV
event and no captured core. Restricted capture remains armed, expiry in74036s,
with its explicit removal gate. A quiet window is not a diagnosed crash fix.

Platform201cases:199passed/2skipped; component157cases:154passed/3skipped.
Printed restart messages in component tests are mocked operations, not real
SM/CM restarts. Platform source/license/secret gate passes242tracked files.
No source implementation, policy load, restart, upload, Factory build, commit,
push or cleanup in this audit. Earlier source corrections remain uncommitted.
Current Test retains stock policy and its known KAC restriction. Native crash
localization and scoped security classification remain before a successor build.

### UI finding: initial layout measurement

After startup, current display height was1225logical pixels while the retained
Presenter backdrop/browser rectangles were5pixels shorter; `workspace.status`
correctly reported INCOMPLETE, although z-order was VERIFIED. One normal
`workspace restore` updated the rectangles, preserved Presenter PID84088 and
the running simulation/VM, returned no problems and VERIFIED z-order. This is
recorded as a transient layout observation, not a Factory runtime defect or a
claim of permanent correction. Native controls are visually readable.
- Build/native/offline evidence is recorded separately in
  [the Factory .37 build report](factory-37-mainline-build-2026-09-23.md).

## Diagnostic/security closure — 24 September12:16UTC

The operator requested closure of the diagnostic stage, remaining security
checks and progression to a new Factory and fresh E2E. The earlier crash/security
items are now classified: proven SM/KAC migration defects enter source;
optional VDP probes remain denied with seven exact tested audit exclusions;
old-runtime109 SIGSEGV remains **unresolved/not reproduced**, not a diagnosed
fix. This residual must stay visible in the .38 qualification; stop on recurrence.

The installed114/V3 runtime was exercised in a separate unit with production
UID998/GID996, vehicle_data_provider_t, empty capabilities, NoNewPrivs and the
normal systemd sandbox. Synthetic loopback mTLS VISS/TLS gRPC fixtures caused
duplicate/out-of-order/stale/disconnected inputs. Two80second runs completed
312 and290 reconnect cycles,625 and581 authenticated sets, exit0, no SIGSEGV.
Wrong CA, wrong hostname, missing client certificate and invalid gRPC token
were rejected. This fixture disabled advisory and accelerated timing only in
its private process: it is not additional live advisory or long-soak qualification.

Early-import and actual-entrypoint self-tests reproduced the remaining parent
metadata and glibc2.39 overcommit probes. Exact seven-rule candidate proof at
12:05:34–12:05:50 retains EACCES for all denied syscalls with an empty scoped
VDP AVC set. It grants no access. Two policy leases restored stock policy,
unchanged canonical store, Enforcing and unchanged live PIDs; final restoration
12:05:50.513UTC. Unrelated SSH/host denials remain outside that scoped result.
Detailed security decisions and primary-source links are in Platform
`docs/vdp-security-closure-2026-09-24.md`.

VDP114 remained PID159575, READY/LIVE and NRestarts0 throughout the proofs.
At11:54 it had100m34s continuous operation without a stale/reconnect/SEGV event;
it remained active without restart through cleanup12:16. No real dump was
captured. At12:16:25.340UTC explicit cleanup verified original
`core_pattern=|/bin/false`, `core_pipe_limit=0`, inactive/absent expiry timer and
service, zero collector open handles, then removed exactly `collector.py`,
`config.json` and `lock` plus their empty `/run/factory37-vdp-core` directory.
The closure receipt remains `/run/factory37-diagnostic-closure.json`.
No memory/credential dump exists to analyze or publish. The source helper can
recreate diagnostic tooling, but no removed runtime state is needed for rollback.

One cleanup command stopped at systemd's missing transient service: capture had
already been disabled and the timer stopped. Read-only reconciliation confirmed
both units not-found/inactive before completing file removal. The11:44 synthetic
key/LoadCredential harness mistake and a host quoting error are excluded, not
counted as product defects or successful tests.

Stock SM162197, CM145206, IAM1795, KAC2232 and VDP159575 stayed active with zero
restarts during closure. Thus the preserved Test still has the stock KAC
restriction; source corrections are **not permanently deployed** there.
Production, Cloud objects, CARLA and service histories were not changed.

Results: Platform202cases/200passed/2skipped; targeted VDP policy suite25/25;
component157cases/154passed/3skipped; production-toolchain KAC10/10 plus provider
and verifier programs exit0. Compact sanitized receipts are in the private proof
root's `security-evidence`; no keys, tokens, telemetry or cores enter Git.

Next gate: pinned .38 source checkpoint, mandatory native/package/QA before one
warm image build, then clean offline boot/repeat. Fresh staging sequential
publication and current-Test retirement retain their exact authorization gates.
Full fresh E2E, cold persistence, thirty-minute RabbitMQ qualification and final
Finish are not claimed by this diagnostic closure.
