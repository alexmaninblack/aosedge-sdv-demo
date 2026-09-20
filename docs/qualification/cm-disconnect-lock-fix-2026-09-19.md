<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# CM disconnect lock correction: native and live qualification

Date: 19 September 2026. Status: isolated tests, production-target compile and
two live external OFF/ON cycles passed for the CM lock correction. Full service
continuity failed on the independent Brake storage cleanup defect. No Factory
successor or completed P8. Earlier exclusions describe the isolated stage.

## Authority and preserved boundary

After the [live diagnosis and negative native proof](cm-monitoring-disconnect-deadlock-2026-09-19.md),
the operator explicitly requested a fix and verification. This authorizes the
bounded Communication lock-order correction and its local tests. It does not
reverse the [ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md)
decision against another native **storage** patch or restore operator Park/Resume.

The running Test, CM process, VM overlay, service/model/outbox data, CARLA,
Driving Control and staging Cloud objects were not changed by this correction.
No credential, production endpoint or runtime volume entered the test container.
Existing unrelated working-tree changes were preserved. Factory `.35` remains
the installed baseline; it does not contain this new fix.

## Correction

The pending upstream candidate is stored in the Platform repository as
`meta-aos-vehicle-platform/recipes-aos/aos-communicationmanager/files/0006-notify-outside-transport-lock.patch`.
The existing CM recipe includes it once. Only native
`src/cm/communication/communication.cpp` and `.hpp` change:

1. Close/reset transport while holding its mutex, then release that mutex
   **before** notifying Monitoring, Alerts or other connection subscribers.
   Apply this to both Disconnect and Stop; CloseConnection no longer notifies.
2. Serialize Connect/Disconnect/Stop transitions and their notifications with
   a separate connection mutex. Message enqueue does not acquire this mutex.
   Release the connection guard before Stop joins the receive worker, which
   may still need to execute Disconnect.
3. Preserve the existing subscriber mutex and listener-lifetime fencing. Use
   an atomic connection state for callback-safe queries and suppress repeated
   same-state notifications.
4. Notify disconnection even if socket shutdown returns an error or the socket
   is already absent. Disconnect still returns the native shutdown error.
   Stop retains its pre-existing return policy.
5. Reject ConnectToCloud after running state has been cleared, so a late
   connection attempt cannot notify Online after a completed Stop transition.

This removes the observed transport-mutex / Monitoring-or-Alerts-mutex cycle;
it is not a claim to eliminate every possible native concurrency defect.
Monitoring/Alerts analytics, storage, token/permission handling, Cloud protocol,
model thresholds, retry intervals and dependency pins are unchanged. No
watchdog, automatic restart or synthetic Online status was added.

## Source identity and environment

The isolated candidate was exported from CPP
`da50b60b7d72208bf17ad51250d24dbc727bc679`; the original checkout was not patched.
The cached library checkout is `0b82a6bfcb5296ae7cdc97fcd8e9ab58048c30ec`.
The relevant Monitoring/Alerts sources match the baseline recorded in the
incident report; this does not describe the full workspace as clean upstream.
The Platform recipe keeps its existing service-update library pin
`60cb83535f773762c61ac5f544b31b7b88c502e3` and prior accepted patches.

The [test target](../../tests/upstream/cm-lock-harness/CMakeLists.txt) compiles
actual native Communication, Monitoring, Alerts and supporting sources. The
[fixture](../../tests/upstream/cm-lock-harness/probe.cpp) uses test-only private
access for scheduling, not replacement implementations of the lock paths.
Linux ARM64 / GCC 12.2 / CMake 3.25 / Poco 1.11.0 / OpenSSL 3.0.20 were used in
`democtl/cm-lock-test:20260919`, with `--network none` and synthetic local data.
These are not a byte-identical production image or its dependency qualification.

Native ConnectToCloud opens a real local WebSocket. A test certificate provider
returns NotFound; the real CryptoHelper uses a fallback URL and a fixture-cached
discovery response. TLS and HTTP discovery are excluded. In worker cases the
real connection/receive worker observes a peer close while a real Monitoring
or Alerts send holds its own mutex. It must disconnect, reconnect automatically
and send two binary frames through native HandleSendQueue: the pending message
and a subsequent message. No external Cloud or ACK/NACK handling is simulated
as a passed full-system result.

## Results

| Check | Result |
| --- | --- |
| Original native eight-case matrix, baseline | Historical 12 PASS / 12 FAIL over three repeats; all overlaps reproduced the native deadlock. |
| Same eight-case matrix, corrected source | 24/24 PASS over three repeats. |
| Final expanded suite: 17 cases, five consecutive repeats each | **85/85 PASS**, CTest exit 0. |
| Expanded native worker cases against unchanged baseline | Monitoring and Alerts both TIMEOUT at 15 seconds, CTest exit 8; regression remains capable of detecting the old defect. |
| Final Python report check, eight cases | 8/8 PASS; all four overlaps confirm gates executed and transport mutex was not held during callbacks. |
| Platform patch/recipe regression | 3/3 PASS; scope, existing pin/capacity, clean patch application and resulting source invariants. |
| Existing related packaging gates | Idle-status 1/1 and permission-key-capacity 3/3 PASS; no failures or skips. |
| Documentation and whitespace | Documentation gate PASS (231 Markdown documents, 658 stable identifiers, 38 Mermaid diagrams); both repositories pass diff whitespace checks. |

The 17 cases cover Monitoring/Alerts × Disconnect/Stop × serial/overlap (8),
duplicate events, Disconnect close error, callback send/query reentry,
concurrent unsubscribe, concurrent Stop/Disconnect, Connect/Stop ordering,
Monitoring worker recovery, Alerts worker recovery and Stop close error (9).

The final CTest JUnit has 17 entries (the last execution of each case); its
LastTest log records all 85 successful executions. A preceding expanded run
found a fixture expectation error: a second native Stop returns WrongState,
not success. The fixture was corrected to assert that contract; product source
was not changed to make the assertion pass. A concurrent Connect/Stop check
uses ordered callback counts and final state, not a racy intermediate read.

### Reproducibility fingerprints

| Artifact | SHA-256 |
| --- | --- |
| Pending Platform patch | `fb5ad21ac1a6e91efcc6f9496e72d786c5cf7b756a07f4eaa8875c76546d4aba` |
| Corrected communication.cpp | `80cc3d3410bae5628a2cdd98f4804c92fde3526294d779503f48f0d12e14139a` |
| Corrected communication.hpp | `8b2afc97162487700dcbc2d62548e09c1e2f07d95216d702f13b62c7cce0b03d` |
| Final native probe executable | `3f49238827245963a61f88c47c2d1d861eebcfb45d3d3592ec9c36dc76f83cb3` |

Disposable candidate/build/evidence are deliberately retained at
`/private/tmp/aos-cm-lock-fix.WfcfVL`: `candidate`, `build`, `baseline-build`,
`final-junit.xml`, `baseline-worker-junit.xml` and `final-matrix/results.json`.
They contain synthetic test data, not guest storage or secrets. Test containers
are removed on exit; no container from this test image remained running at the
final check. This isolated proof directory occupies approximately 156 MiB.
Existing Builder/download/shared-state caches are preserved.
No source commit, push, upstream submission or large image artifact was made.

## Open deployment gate

Local evidence establishes correction of the reproduced lock cycle, **not**
that the currently running Test has recovered. It cannot receive this code
without replacing/restarting CM. Its independently proven shared-storage
cleanup defect still makes an unplanned restart unsafe for service continuity.
Do not restart the retained CM implicitly or call the original run passed.

The next bounded live step needs an explicit choice of how to handle that
retained state, followed by the affected production-target compile/package
gates and an exact reversible deployment. Then verify real external OFF/ON,
Cloud Online, pending SOTA, local function continuity, backend backlog and fresh
security/restart observations. A fresh image/clean cycle remains separate.

Not covered here: production TLS/discovery, ACK/NACK and retry-worker semantics,
sustained backpressure, arbitrary subscriber destruction, callback lifecycle or
subscription reentrancy, Stop during a stalled external handshake, production
SELinux/systemd permissions, or service storage retention across CM restart.
The existing blocking retry/backoff was not redesigned. P8 stays open.

## Authorized production-target rebuild and Test activation

The operator accepted the explicit CM-replacement/restart risk and requested
the rebuild and verification. Scope: current Test only; no fresh identity,
VM/CARLA restart, SM/IAM replacement, storage fix or Cloud-code change.

The retained Yocto Builder was started with its existing caches. Free space
was 262 GiB on the host and 110 GiB on the Builder. The affected `aos_cm_app`
target was compiled with the existing Factory .35 production compiler,
sysroot, dependency pins and accepted prior patches. Only the new connection
patch was added transiently; original warm source and baseline build were
restored after copying the result. Build and restoration both succeeded.

- Builder artifact: `/home/yocto/r61-build/project/yocto/cm-disconnect-lock-proof-2h6mnr/aos_cm_app`.
- Host artifact: `/private/tmp/aos-cm-lock-fix.WfcfVL/aos_cm_app`.
- ARM64 ELF, stripped, 5,598,976 bytes; interpreter `/usr/lib/ld-linux-aarch64.so.1`.
- SHA-256 at creation and host transfer: `b94bef9d976ad7fc56f45b795d033246afdda5a4b1af5df26a2123c0c9034ad7`.
- Original installed CM: `a9768c64bf91c6d9894cc8b2f4af64c3ddd493c5e2d96f275a1749abc667b406`.

At 13:13:08 UTC before activation: CM 1588, SM 1947, IAM 1559 and VDP 5008;
all active with zero systemd restarts. Test external network was ON while Cloud
remained Offline. Brake63 and Tire36 stores existed, with no pending files in
their outbox/pending directories. Brake model generation 6 and function
generation 3/sequence 543; Tire function generation 1/sequence 734. The bounded
pre-state record is `live-before.json` in the host proof directory. Hashes and
continuity fields are retained, not raw model/telemetry payloads or credentials.

Activation uses `/run/aos-cm-disconnect-lock-20260919/aos_cm_app`, root:root 0755,
the installed binary's SELinux label, and one ExecStart-only drop-in at
`/run/systemd/system/aos-cm.service.d/90-disconnect-lock-proof.conf`. The installed
binary and immutable .35 image remain unchanged. Runtime proof and disposition
are pending; neither this compile nor restart intent closes live OFF/ON or P8.

### First live result: connection recovery passes, storage failure recurs

The initial activation preflight stopped before any mutation because the guest
has no `ldd`; the native dynamic loader successfully validated dependencies.
The reconciled second invocation submitted the **first and only** restart at
13:16:05 UTC. The already deadlocked original CM could not complete SIGTERM;
systemd's existing 90-second stop timeout preceded the new process, PID 29178.
SM 1947, IAM 1559 and VDP 5008 were unchanged. The running executable resolves
to the transient candidate; SELinux remains Enforcing, with no new AVC denies.

At 13:17:35 the new CM connected; peer close frames at 13:17:35 and 13:17:45
were followed by native disconnect/reconnect, not a blocked callback. By the
13:18:13 authoritative read, the same Unit was ONLINE (Cloud transition
13:18:05) and Tire37 was installed/active, replacing the already pending Tire36
without another upload, assignment or restart. Brake63 remained Cloud-active.

However, the 13:18:20 local read found **Brake's persistent root absent**.
Its last backend advisory/function receipts stop at 13:17:21 / 13:17:25.
This is not service continuity success. The known independent native storage
cleanup risk has recurred after restart; it is not masked by Cloud's active
instance state. No storage restoration, new model, Reset or service restart
was attempted. Tire's producer epoch persisted across its update; its function
generation advanced to 2. Full model inheritance is not established by those
metadata alone. The remaining CM OFF/ON proof is recorded separately from the
blocked full service scenario.

First external OFF completed at 13:19:10.112. Cloud transition to Offline is
13:19:45. By 13:20:59 the Tire backend still had the pre-OFF function receipt
13:18:51.773 / sequence 6, now stale. Local Tire at 13:20:53 had sequence 11,
five pending function reports and nine pending/outbox files; native CM/SM/IAM/
VDP PIDs and restart counters were unchanged.

First ON completed at 13:21:58.846; Cloud Online transition is 13:22:00 and
was confirmed by a read at 13:22:37. CM remained PID 29178, NRestarts=0.
Tire resumed CONNECTED/RECEIVING, with fresh backend sequence 18 received at
13:22:29.631; local function pending count and outbox/pending-file count were
both zero at 13:22:42. SM/IAM/VDP PIDs were unchanged. This proves bounded
recovery/drain, not exact-once payload matching or Brake recovery.

### Repeated live OFF/ON and final state

| Cycle | External OFF completed | Cloud Offline transition | External ON completed | Cloud Online transition |
| --- | --- | --- | --- | --- |
| 1 | 13:19:10.112 | 13:19:45 | 13:21:58.846 | 13:22:00 |
| 2 | 13:23:00.842 | 13:23:40 | 13:25:31.301 | 13:25:35 |

Times are UTC on 19 September. Cloud transitions are the authoritative
`last_online_changed_at`; these are not request-response duration benchmarks.
Both recoveries occurred with the same CM PID 29178 and no additional restart.
The second OFF left Tire's backend function receipt at 13:22:49.770 / sequence
19; it became stale. After ON it advanced to sequence 30 at 13:25:57.065 and
38 at 13:27:29.178. Tire's local function pending count and outbox/pending-file
count were both zero at 13:27:15. Native node/service monitoring also resumed:
Cloud source sample times advanced from 13:22:25 to 13:25:20 (offline backlog)
and then to the post-recovery sample **13:27:05**. Thus Online was not the only
recovery signal.

At 13:27:10, native logs contain seven connection-established events and six
peer close/disconnection events, with subsequent reconnection and desired
status processing. There is one connection-worker start. CM NRestarts=0 means
no automatic restart after the one explicitly requested replacement, not zero
restarts over the entire experiment. SM/IAM/VDP retained their original PIDs,
and no fresh kernel AVC denies were found. No service model Reset, threshold
change, re-upload, Subject mutation or Cloud-code workaround participated.

Sanitized startup events also directly identify Brake's instance/storage
removal at **13:17:35.358–13:17:35.368**, before the first new connection was
established. Two logical removal calls each log both storage removal and
removal-from-system. Combined with the before/after root check, this confirms
native startup cleanup, not an external-network rule, deleted Brake's data.
The compact log extraction does not recover semantic old release numbers;
the prior source-level shared-storage diagnosis remains the explanation, not
a claim that this extraction decoded those missing versions.

Final authoritative read at 13:27:43: the same Test is ONLINE, Tire37 active,
Brake63 Cloud-active but functionally stale, and no pending service version.
Brake's root is still absent and its latest backend function receipt remains
13:17:25.065. Cloud instance Active is not proof of working product storage.
External network ON was confirmed separately at 13:27:45.

### Disposition and remaining gates

- Leave the verified transient CM active for diagnosis. The original installed
  executable and Factory .35 remain untouched. VM, CARLA, SM/IAM/VDP were not
  restarted. The observed native Brake cleanup is not described as successful
  data preservation.
- Deliberately retain the exact `/tmp` transfer files and `/run` executable/
  drop-in listed above. The `/run` fix is **not persistent across reboot**.
  Removing that drop-in, daemon-reloading and restarting CM would restore the
  original installed executable, but is not performed automatically: it brings
  back the deadlock risk and incurs another storage-risking restart.
- Builder was shut down cleanly after use, returning it to its initial state;
  build/download/shared-state caches and compact proof artifacts are retained.
- Production target and all seven scoped Platform tests passed. Documentation
  and whitespace checks passed. No formal package/image build, commit/push or
  upstream submission was performed in this turn.
- Stop before Factory/image/clean acceptance: independent storage loss prevents
  a green full-service run. Resolve that separate native defect or an explicitly
  accepted qualification strategy before restarting/recreating service state.
  The connection correction does not authorize a storage patch.
