<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness flicker during KUKSA token renewal

Status: approved correction implemented, published and live-qualified for
readiness renewal on the preserved Test, 20 September 2026. No clean full-story
or new warning/reset qualification is claimed by this report.
Initial diagnosis: Factory .36, VDP V3/97.0.0, Brake V3/77.0.0 and Tire V1/43.0.0.
Qualified successor: VDP V3/98.0.0, Brake V3/78.0.0 and Tire V1/44.0.0.
Only the existing Test in `aws-stage.epmp-aos.projects.epam.com` was updated;
Production and Factory are unchanged.

## Original diagnosis, before correction

The observed `Monitoring → Unavailable → Monitoring` is a real producer
readiness publication, not an invented dashboard state. During token renewal
the service reconnects to KUKSA and clears local readiness. Its newly started
readiness writer can publish `false` before fresh telemetry arrives. Although
input can recover in milliseconds, that value is retained until the next
five-second publication. VDP forwards readiness on a separate five-second
cadence. Native Driving Control then faithfully displays the retained false
value and its later recovery.

This is timing-dependent: a renewal whose first readiness publication is
already true does not produce the visible flicker. Normal token renewal is
not itself a failure of IAM, CM, SM, KUKSA authorization or Cloud connectivity.
The diagnosis concerns the service readiness/reconnection implementation and
its propagation timing. It does not justify disabling renewal or retaining
unauthorized subscriptions.

## Observation method and limits

- Native Driving Control screenshots were sampled approximately every
  0.35–0.50 seconds during bounded observation windows. Only changed images
  were inspected; no UI input was sent. There are gaps between windows.
- Guest journal records were reduced to fixed event/state/reason/time fields.
- After explicit operator approval, one temporary client used the existing
  VDP access to read **only** the Brake and Tire `Advisory.Readiness` targets
  every 200 ms for 250 seconds, 14:38:32.86–14:42:42.93 UTC. It made no writes.
- The first probe failed before connection because its Python dependency path
  omitted the installed component's `site-packages`. It was stopped; the
  installed launcher established the correct path. Those probe failures are
  not product failures. No credential content was output or copied.
- The existing `service runtime-inspect test` command supplied token-file
  modification times, process facts and bounded failure counts. It reads file
  metadata, not token contents, for this evidence.
- No extra VISS dashboard session was opened: its existing single-role
  connection remained untouched. The VDP → Gateway step is established by
  source and downstream UI correlation, not a separate packet trace.
- All times below are UTC; the desktop's local time is UTC+2. Sub-millisecond
  cross-host timing precision is not claimed.

## Brake: joined service, KUKSA and UI timeline

| UTC | Observed fact |
| --- | --- |
| 14:38:58.509 | Brake logs NOT_READY / KUKSA_REAUTHENTICATING. |
| 14:38:58.580 | Producer publishes readiness `false`; read back at 58.593. |
| 14:38:58.683 | Operational log becomes DEGRADED: analytics is ready again, 174 ms after NOT_READY. This is not a fresh advisory-application ACK. |
| 14:39:02.881 | Native screenshot changes to Brake `Unavailable`, Tire still `Monitoring`, telemetry LIVE. |
| 14:39:03.707 | Producer publishes readiness `true`; read back at 03.859. |
| 14:39:07.853 | Native screenshot changes back to Brake `Monitoring`. |

The negative producer value persisted for **5.127 seconds**, despite analytics
recovery after 174 ms. The two changed screenshot observations are 4.972 seconds
apart; the actual display-transition times are bounded by the screenshot sample
interval, not known to millisecond precision.

At the following renewal, 14:41:58.650, the operational log again briefly became
NOT_READY and recovered at 58.780. This time the new readiness publication at
14:41:59.180 was already `true`; the sampled UI did not change. This directly
supports the startup/publication race rather than a mandatory outage on every
token rotation. Earlier renewals were also logged before recording/editing work.

## Tire: same retained negative readiness, independent timing

| UTC | Observed fact |
| --- | --- |
| 14:39:38.972 | Tire publishes readiness `false`; Brake remains true. |
| 14:39:44.106 | Tire publishes true again: **5.134 seconds** later. The UI transition for this occurrence fell between observation windows. |
| 14:42:39 (one-second resolution) | Native runtime inspection reports the current Tire token file was modified. |
| 14:42:39.418 | Tire again publishes false, coincident with renewal. |
| 14:42:44.771 | First screenshot in the next observation window shows Tire `Unavailable`, Brake `Monitoring`, telemetry LIVE. |
| 14:42:48.941 | Tire returns to `Monitoring` in the native UI. |

The last Tire UI outage was present across at least the 4.17 seconds between
those screenshots; its onset was in a screenshot gap, so its full duration
must not be stated as precisely measured. The KUKSA observer ended at
14:42:42.93, before that occurrence's true publication; the earlier occurrence
provides the complete false-to-true KUKSA interval.

Tire's repeating connection events are deduplicated in its existing log. The
renewal correlation uses the standard token-file modification metadata and the
source's reconnect behavior; it is not a new token-content inspection. Separate
very brief Tire input NOT_READY/READY events also occurred at 14:32:12 and
14:33:38. They were not observed to change the native label in the sampled
windows and are not asserted to share this precise cause.

## Source mechanism

- Brake `src/runtime/application.cpp:17` distinguishes token replacement from
  missing credentials or other changed public inputs. The subscription
  watcher cancels the old session; `src/runtime/grpc_main.cpp:339` disconnects
  analytics before recreating the authenticated stream.
- Brake `src/runtime/product.cpp:123` clears readiness on disconnect;
  `:216` uses actual model/input readiness and five-second input freshness.
  `src/runtime/grpc_main.cpp:478` publishes readiness, then sets the next
  publication five seconds later, regardless of an earlier readiness change.
- Tire `src/runtime.cpp:55` clears its telemetry timestamp on disconnect.
  `src/runtime/grpc_main.cpp:218` starts the readiness worker **before** the
  telemetry subscription loop receives its first valid sample. The first
  write is immediate; `:242` then waits five seconds. `src/runtime.cpp:218`
  evaluates readiness from the restored telemetry timestamp and store.
- VDP `providers/carla-viss-kuksa/src/carla_viss_kuksa_provider/advisory_transport.py:150`
  adds the independent five-second availability-publication cadence.
- Gateway/native `src/viss_client.cpp:447` maps supported, previously ready,
  currently false readiness to `Unavailable`; true maps to `Monitoring`.
  Cloud/backend connectivity is not consulted for this label.

Inspected source HEADs: Brake `4f75373123cbc00a5b7a3541b1d289cb07affd39`,
Tire `20e6a23dcb97c29a0315fedd2e720ab537f01ff8`, platform
`75503cdc2b9ab0ecb527db3bbf84e5380d6c42c7`, Gateway/native UI
`453b7948006d0264b0cede17816aaf551485b3cf`.
No new byte-for-byte deployment attestation was performed in this investigation.

## Correction proposed at the diagnosis checkpoint

1. In both services, publish a readiness transition promptly when fresh input
   restores or removes readiness; preserve the periodic heartbeat as well.
   Confirm readiness Set results instead of ignoring failures.
2. Propagate a changed producer readiness promptly through VDP, retaining
   freshness/expiry, bounded traffic and the periodic support heartbeat.
3. Add bounded non-secret transition and token-renewal diagnostics, so a
   future incident has a joined timeline without a special credential probe.
4. Test reconnect ordering before/after the first valid sample, normal token
   renewal, missing/invalid credentials, real input loss, independent teams,
   external network off, and a still-valid Gateway-confirmed warning.

Do not simply keep the UI green, relax authentication or fabricate continuity
of a capture interrupted by reconnect. Prompt propagation removes the observed
five-second stale-status amplification; it does not promise that every genuine
short interruption will become invisible. Any debounce/grace-state product
choice must be explicitly agreed rather than hidden in a UI patch.

## Preservation at the diagnosis checkpoint

VDP was active with NRestarts=0. Both analytics processes remained present;
bounded resource-failure counts were zero. Both advisories returned to
Monitoring, LIVE telemetry, Safe Stop / 0.0 km/h. No VM, service, CARLA or native
UI restart, reset, deployment, Cloud mutation, policy or model change occurred.
The 250-second KUKSA observer and bounded journal follower both exited; their
temporary scripts reside only under `/private/tmp`, with no credentials or
runtime modifications. No build, functional fix, E2E rerun, commit or push is
claimed. Existing unrelated working-tree edits were preserved.

## Implemented correction and source identity

The operator approved the correction and then explicitly approved signing,
publication and installation of these three exact releases on the current Test.

| Owner | Source commit | Release |
| --- | --- | --- |
| Brake service | `a7f7b0b5021c271c51a2196b620f2631fd788edc` | 78.0.0 / V3 |
| Tire service | `fed2161a9c77703cef04d3df4d4dae2cbdca3f0d` | 44.0.0 / V1 |
| VDP/platform | `1fe5649f860f62573b313e1f38e5ec0f4ca1b519` | 98.0.0 / V3 |

Both service writers now check actual readiness each worker iteration and
publish a changed boolean without waiting for the five-second heartbeat.
They validate both RPC and KUKSA entry results. VDP similarly propagates
changes with one in-flight write per path and only treats an accepted VISS
response as confirmation. Minimum attempt spacing is 100 ms; failures retry
the current state after one second. This is bounded traffic, **not** a promise
of a 100 ms maximum latency: worker scheduling, RPC deadlines and transport
remain relevant. A successful unchanged value is still refreshed every five
seconds. No old-state transition queue is replayed.

Authentication/session replacement, freshness expiry, permissions, schemas,
warning semantics, reset scope, models and UI mapping remain unchanged.
Bounded fixed-field diagnostics distinguish readiness publication from a
warning-application ACK. The solution pin retains all previous runtime pins
and the correct 1.2.0 contract for the preceding retained runtime. The new pin
also includes the already committed bridge diagnostic distinction between
changed equal-time data and time regression; it changes no telemetry decision.

### Local and package gates

- Minimal transient scheduler proof passed before the source correction.
- Brake C++ Debug tests: 8/8. Tire C++ Debug tests: 5/5.
- Production ARM64 builds and their export gates passed for both services;
  the real gRPC runtime was compiled, not only a scheduler fixture.
- Platform Python suite: 188 passed, including ten new transition tests.
  Three selected new regression tests fail against the old transport and
  pass against the corrected transport.
- Brake Python suite: 23 run, five skipped. Tire: 26 run, five skipped.
- Solution component tests: 161 run, three skipped; service-input tests: 37
  passed; advisory tests: 16 passed. These cover redacted diagnostic output
  and retained-release compatibility as well as transition behavior.
- Brake repository quality gate passed. All changed platform files passed
  the targeted source/license/secret checks. The **full platform quality gate
  remains non-clean**: 19 pre-existing findings in 11 unchanged files (SPDX
  metadata and a test-fixture credential-pattern match). Each flagged file
  was compared with the pre-fix HEAD. No Factory/image build was attempted or
  qualified, and those findings were not silently repaired in this packet.

### Publication and installation

Each upload was attempted once through Demo Control with the selected role's
certificate. HTTP 201 was reconciled against the Cloud objects, not treated
alone as installation proof. Brake uploaded at 15:07:26 UTC, Tire at 15:08:38,
VDP at 15:09:29. VDP installation used the existing Safe Stop authorization.
No Subject, assignment, Unit identity, VM or simulator replacement was made.

At 15:22:48 UTC, the authoritative Cloud observation reported Test Online,
VDP 98.0.0 installed with no pending component, and active installed Brake
78.0.0 / Tire 44.0.0 instances with no pending versions or reported errors.

| Artifact | SHA-256 |
| --- | --- |
| Signed Brake 78 bundle | `b14255be70afeee1bfa103f5fbbceac4825ac37f4b7739c6cb646abf1c5b325c` |
| Signed Tire 44 bundle | `cba7b3e7727e8c8a8988f57a47211ce9fce32aeb502d8120f40dc3823a23ff24` |
| Signed VDP 98 bundle | `0063d9807d5bcd770a7ea559602a3ebb9fe74deaf392ef54f5d409b9099a2afd` |
| Running Brake ELF, matching build output | `bf4dd56b0b1327a4d8043866eb3f3187fbc715aa1a6d107444fa704cf7700bfb` |
| Running Tire ELF, matching build output | `e3b271769c212c42c400d0317015288803c541e48f8d51958970fa306c86ba46` |

### Live timing and offline proof

A journal-only observer ran from 15:11:52.249 to 15:22:23.207 UTC and exited
normally. It used no KUKSA credentials. The earlier authorized KUKSA client was
not left running or reused. Measurements below are journal acknowledgement /
forwarding event intervals; they are not new direct KUKSA packet timestamps.

| Event (UTC) | Producer NOT_READY -> READY | VDP NOT_READY -> READY |
| --- | --- | --- |
| Brake renewal, 15:13:36 | 200.887 ms | 255.836 ms |
| Tire renewal, 15:14:46, external network off | 101.694 ms | No negative transition observed in the bounded log |
| Tire renewal, 15:17:45, external network off | 101.535 ms | 258.822 ms |
| Tire renewal, 15:20:45, network restored | 101.300 ms | 431.808 ms |

At the first Brake event, VDP's READY observation followed the service's
successful READY publication by 48.879 ms. Brake also reauthenticated at
15:16:35 and 15:19:35; analytics recovered in approximately 141 and 99 ms,
without a new false publication. These are timing-dependent observations,
not a requirement to publish every intermediate local state. Cross-thread
journal order is not precise send-order evidence.

The component update itself supplied a genuine negative case: input loss at
15:09:33 made both producers publish NOT_READY. After actual input recovered,
Brake published READY about 31 ms later and Tire about 47 ms later. Recovery
was not inferred from installed versions or Cloud Online status.

External networking was disabled at approximately 15:13:50 and restored at
approximately 15:20:30 UTC. Backend receipts remained at Brake 15:13:44.190 /
Tire 15:13:49.538 during the checked offline interval and became stale.
Local LIVE telemetry and readiness survived subsequent token renewals.
After reconnection, both backends again reported CONNECTED, RECEIVING, fresh
observations of the new versions and empty delivery queues. Cloud recorded
its Online transition at 15:20:36 UTC. No exact Cloud-offline transition-time
measurement is claimed by this readiness test.

Native screenshots before, around and after the offline Brake renewal and
after reconnection showed both advisories Monitoring and telemetry LIVE.
Screenshots are sampled, not continuous frame-by-frame proof. Byte inequality
of screenshots was not treated as an advisory state change: the native image
capture changed even while visible labels did not. Brief genuine negative
states remain possible and may be visible; this correction removes the
observed five-second stale-status amplification, not truthful unavailability.

### Final preservation and limitations

The original VM host PID 76491 remained running. Service PIDs 64436 / 64633
matched the verified new binaries. VDP, CM and SM were active, successful,
with NRestarts=0; CM/SM binaries were not changed. The expected component
update restarted only VDP. Bounded runtime inspection reported zero service
resource failures, no watchdog events and no provider denials. This is not a
new exhaustive SELinux audit or a reboot qualification. One final process-list
command was unsupported by guest BusyBox; the preceding hashes and systemd
checks succeeded and no build or deployment was repeated for that harness error.

The demo is left with external networking ON, Test Online, Safe Stop / 0 km/h,
LIVE telemetry and both advisories Monitoring. Temporary host-only proof and
journal scripts are retained under `/private/tmp/sdv-readiness-fix.TRLYrl`;
they contain no credentials and install no persistent guest diagnostic state.
No Factory image, build cache, user data or unrelated edit was deleted.
No new maneuver, warning/reset round trip, clean E2E cycle or push is claimed.

### Presenter handoff

The final UI inspection correctly showed the installed service versions but
initially could not bind VDP 98 to its functional profile. Its long-running
Python server still held the pre-change permitted source pins. A fresh CLI
inspection of the same immutable package reported V3 with no problems, while
the old server returned `INSTALLED_PROFILE_ARTIFACT_NOT_CONFIRMED`.
Only the idle Presenter server was restarted to load the source-pin change.
The standard stop guard rejected an equivalent relative invocation; exact PID,
owner, working directory and idle/no-uncertain-operation status were verified
before sending SIGINT to that one process. The successor was launched with the
canonical absolute command so the normal guard recognizes it in future.
After startup and read reconciliation, Presenter reported installed profile
CURRENT / v3 / 98.0.0 with publication READY. Native Driving Control remained
LIVE, Safe Stop, network ON and both advisories Monitoring throughout the
checked handoff. No UI truth rule was weakened to force a profile label.
