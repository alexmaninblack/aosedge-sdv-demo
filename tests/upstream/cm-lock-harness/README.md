<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native CM disconnect lock regression

Test-only proof authorized on 19 September 2026. See the
[incident and execution record](../../../docs/qualification/cm-monitoring-disconnect-deadlock-2026-09-19.md).
This harness does not patch, deploy, restart or repair native CM.
The subsequent [correction record](../../../docs/qualification/cm-disconnect-lock-fix-2026-09-19.md)
separates the expanded fixed-source proof from the original negative execution.

## What runs

[CMakeLists.txt](CMakeLists.txt) compiles the actual Communication, Monitoring,
Alerts and their supporting source into one Linux test executable. Source
checkouts can be mounted read-only. No copied two-mutex model substitutes for
these implementations. [probe.cpp](probe.cpp) uses GCC's test-only
`-fno-access-control` to initialize minimal state and invoke private timer/
disconnect entry points; production source and headers are not edited.

A real plaintext WebSocket handshake runs on container loopback with an
ephemeral port through native `ConnectToCloud`. The real CryptoHelper uses a
test certificate provider returning NotFound and a configured fallback URL;
the fixture supplies the cached discovery response. No TLS credentials,
provisioning, HTTP discovery, Cloud connection, VM or service model data are
used. The fixture bypasses full application startup and timer scheduling,
calling the real timer callback body directly. The two worker cases also run
native `HandleConnection`, `ReceiveFrames` and `HandleSendQueue`.

Eight cases cover Monitoring/Alerts × Disconnect/Stop × serial/overlap:

1. Cache one synthetic node sample or system alert through the real receiver.
2. Serial control: enqueue the sample, disconnect/stop, open another local
   WebSocket through native ConnectToCloud, enqueue a second
   sample and verify queue counts and connected/disconnected state.
3. Overlap: the UUID test dependency pauses an actual native send **after**
   its running-state check and before acquiring Communication's queue mutex.
   Monitoring/Alerts still owns its own mutex at this point. Pausing here also
   prevents Stop's early running-state rejection from masking the lock cycle.
4. Another thread invokes the real Disconnect or Stop. A forwarding subscriber
   signals entry and immediately calls the real Monitoring/Alerts OnDisconnect.
   Its signal mutex is released before that call. Listener lifetime spans all
   test threads. The separate lifecycle case tests concurrent unsubscribe.
5. At this rendezvous the coordinator probes both native mutexes, releases the
   UUID gate, then requires both operations to finish. The gate is released
   before failure detection; the resulting wait cannot be blamed on an
   unreleased fixture gate.
6. If both complete, the same reconnect/queue control follows. A known-bad
   candidate cannot reach this stage.

The coordinator records whether Communication's mutex is held, rather than
requiring that bad scope forever. It currently requires the sender's mutex at
the rendezvous. A future sender-side snapshot redesign would need a separately
reviewed equivalent scheduling hook; do not silently weaken the test.

Nine additional CTest cases cover duplicate notification suppression, socket
shutdown errors in both Disconnect and Stop, callback send/query reentry,
concurrent unsubscribe, concurrent Stop/Disconnect, Connect/Stop ordering, and
Monitoring/Alerts receive-worker disconnect and reconnect. In the worker cases
the peer sends a close frame during the gated native send; a replacement local
connection must deliver both the queued and subsequent message as binary
frames. This tests local wire delivery, not remote ACK/NACK handling.

## Run

Dependencies used for the recorded run: Linux ARM64, GCC 12.2, CMake 3.25,
Python 3, Debian Poco 1.11.0, OpenSSL 3.0.20 and GDB 13.1. The actual deployment
may use different dependency versions. This is a native source-level lock
regression, not a byte-identical Factory binary qualification.

```sh
cmake -S /path/to/cm-lock-harness -B /path/to/proof-build \
  -DCPP=/path/to/aos_core_cpp -DCORE=/path/to/aos_core_lib_cpp \
  -DCMAKE_BUILD_TYPE=Debug
cmake --build /path/to/proof-build --target cm_lock_probe -j4
ctest --test-dir /path/to/proof-build --repeat until-fail:5 --output-on-failure
python3 /path/to/cm-lock-harness/run.py \
  /path/to/proof-build/cm_lock_probe /path/to/test-results --repeat 3
```

[run.py](run.py) bounds each child, captures function-only stacks on timeout,
then kills and reaps only that child. In a disposable Docker container, grant
`SYS_PTRACE` for those test children only; no host PID namespace, privileged
container, Docker socket, credentials or runtime mounts are needed. Use
`--network none`: only loopback is required. No core dump is needed.

Results distinguish rendezvous confirmation and native wait-cycle stack
confirmation from a generic timeout or harness error. The runner exits **1**
if any regression fails. Known deadlocks remain FAIL; they are not converted
into passing expected failures. The output directory contains JSON, bounded
stage logs and synthetic-process stack files. Never point it at runtime data.

CTest registers all 17 cases with ten- or fifteen-second timeouts. It does not
capture stacks. The Python runner covers the original eight-case matrix and
can capture stacks on failures. Rendezvous confirmation means that the gates
were exercised, on both failing and passing candidates; the transport-lock
field separately identifies whether the callback still holds that mutex.
Serial controls have no rendezvous and report a null transport-lock field.

## Qualification limits

- The serial proof checks native enqueue and notification recovery. Worker
  cases extend this to automatic local reconnect and wire delivery, not a full
  Cloud reconnect, ACK/NACK or retry worker.
- The two-second completion check is a deadlock-test watchdog, not a new demo
  real-time requirement. Deterministic gates establish the overlap first.
- The test excludes TLS/HTTP discovery, arbitrary listener destruction,
  callback lifecycle/subscribe/unsubscribe reentrancy and sustained traffic or
  backpressure. The unsubscribe case retains the object until unsubscribe and
  the active callback both complete; it does not establish a new ownership
  contract. Stop during a stalled external handshake and production dependency
  versions need separate qualification. Live OFF/ON acceptance remains open.
- Repeated forced failures demonstrate a reachable, reproducible wait cycle;
  they do not measure its probability under natural traffic or establish that
  a particular demo patch caused the live occurrence.
- Failed children are intentionally terminated. The separate live failing
  Test and its evidence remain untouched.
