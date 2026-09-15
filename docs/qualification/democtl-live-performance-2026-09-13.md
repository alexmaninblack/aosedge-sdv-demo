<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control live performance run — 13 September 2026

Status: **LIVE CYCLE COMPLETED WITH RECORDED LIMITATIONS; TEST RETIRED**.
User-authorized real Test-only lifecycle and command
timing after the performance increment. Production .31 is preserved. Start
state: Test absent; Production running; simulator stopped. Use the existing
immutable Factory .33, no image/product rebuild. Service inputs remain
explicitly synthetic while native Cloud permissions/KUKSA is blocked.

Source base: `52dd2c0bedbad43944ee05e2569e51d7306d9774`, with the current
uncommitted Studio fixes and performance increment. This is not a clean-tree
release qualification or human visual acceptance.

## Measurement method

Every command is run directly from `apps/demo-orchestrator` with
`/usr/bin/time -p .venv/bin/democtl ...`. Wall time includes Python startup,
checks, HTTP and command-owned waits. Tool dispatch/review delays and time
between commands are excluded. Native dialog/operator delays inside a command
are explicitly identified. No new execution wrapper or private Cloud mutation
path is used. CARLA driving buttons retain their native control path.

These are real single-run observations, not a statistically controlled
before/after benchmark. The earlier isolated benchmarks are documented in the
[performance audit](../research/democtl-ui-performance-audit-2026-09-13.md).

## Timed command results

| Command | Wall seconds | Result / scope |
| --- | ---: | --- |
| `image list` | 0.10 | .31/.33 catalog metadata available; no content rehash |
| `status all` | 0.24 | Test absent, Production running, simulator stopped |
| `demo create --image 6.1.1-maninblack.33/main-qemuarm64` | 281.27 | COMPLETED; fresh Test and both backends running. Includes native password-dialog handling and first console/SSH enrollment; not pure VM boot time |
| `component prepare --profile v1` | 2.59 | VDP28.0.0/V1 prepared from signed baseline; seven paths |
| `component sign 28.0.0` | 1.07 | Signature verified |
| `component upload 28.0.0` | 12.06 | One accepted HTTP201; bundle `1da43331-e2ab-48e2-8084-eb7ac040aaed`, 18:17:16.990221 UTC |
| `simulation start --target test` | 52.61 | CARLA, Controller/Gateway, native UI running |
| `vehicle initialize test` | 4.48 | Stationary Manual, Test selected |
| `unit provision test` | 31.80 | SDK + Online + Test Vehicles; internal Unit operation reports 29.75 s |
| `component cloud-status 28.0.0` | 1.41 | READY in Cloud; factory 0.0.0 with 28.0.0 pending |
| `component status test`, before Safe Stop | 2.29 | Candidate28, waiting-for-safe-stop, provider inactive |
| `component status test`, after Safe Stop | 1.94 | Active28, slot a, seven LIVE/READY paths, zero restarts |
| `service runtime-prepare test`, first | 5.08 | Public inputs created; no SM restart |
| `service prepare brake --profile v1 --without-permissions --demo-mocked-data` | 1.31 | Brake16/V1 prepared; existing ARM64 build reused |
| `service sign brake/16.0.0` | 3.26 | Verified signed bundle |
| `service upload brake/16.0.0` | 9.94 | HTTP201, bundle `bec88016-d15d-499d-ad0c-533c3b160823`, 18:24:21 UTC |
| `service cloud-status brake/16.0.0` | 0.87 | READY, 18:24:50 UTC |
| `unit monitoring test` | 1.13 | Real Cloud sample present; PARTIAL because usedDisk is NOT_REPORTED, not a transport timeout |

Live Presenter HTTP measurements (response bodies discarded, curl total time):
Platform200 **0.960875 s**; local snapshot200 **0.198185 s**. These exercise
the running optimized UI backend, with ordinary UI polling left enabled.

Current Test: Unit `ba3b6a9c-05c5-43b1-84a6-42c8871bb5ca`, system UID
`8ac950f979224400bc55891a7c7adceb`, Test Vehicles confirmed. Native Autopilot
showed 19.4 km/h before the first Safe Stop. Safe Stop was requested at
18:21:42.917 UTC and the provider's ActiveEnterTimestamp is 18:21:44 UTC:
approximately two seconds, subject to UI-dispatch and one-second guest timestamp
resolution. Cloud independently reported VDP28 installed at 18:24:30 UTC.

One service-upload tool review initially rejected the unspecified destination;
read-only evidence established the public source/payload, exact existing Aos
Cloud SP and prior explicit upload authorization. The same direct command was
then authorized. This review/dispatch delay is not part of its 9.94-second
command execution and caused no extra upload attempt.

## Scope and outstanding stages

### Subsequent measured progression

| Command | Wall seconds | Observed result |
| --- | ---: | --- |
| `service runtime-prepare test`, unchanged repeat before Brake Deploy | 4.32 | COMPLETED, noOp=true |
| `service assign <brake-id> --target test` | 12.64 | Brake16/V1 assigned and already active in Cloud post-read |
| `component prepare --profile v2` | 2.05 | VDP29/V2 |
| `component sign 29.0.0` | 1.00 | Verified |
| `component upload 29.0.0` | 3.76 | HTTP201, 18:27:19.735715 UTC |
| `service prepare tire --profile v1 …` | 1.02 | Tire12/V1 |
| `service sign tire/12.0.0` | 3.00 | Verified |
| `service upload tire/12.0.0` | 5.17 | HTTP201, 18:27:27.929911 UTC |
| `service cloud-status tire/12.0.0` | 0.73 | READY |
| `component status test`, VDP29 pending | 2.28 | VDP28 active; removal/update transaction waiting for Safe Stop |
| `component cloud-status 29.0.0` | 0.97 | Installed28, pending29 |
| `service runtime-prepare test`, during VDP transaction | 4.91 | BLOCKED; see sequencing qualification below |
| `service assign <tire-id> --target test` | 9.67 | ASSIGNED, initially to be installed |
| `component status test`, after second Safe Stop | 2.71 | Active29/V2, slot b, 15 paths, zero restarts |
| `service runtime-prepare test`, after second Safe Stop | 4.39 | COMPLETED, unchanged inputs |
| `service prepare brake --profile v2 …` | 1.04 | Brake17/V2 |
| `service sign brake/17.0.0` | 3.08 | Verified |
| `service upload brake/17.0.0` | 5.18 | HTTP201, 18:31:56.193062 UTC |
| `service prepare tire --profile v1 …`, successor | 1.33 | Tire13/V1 |
| `service sign tire/13.0.0` | 3.04 | Verified |
| `service upload tire/13.0.0` | 4.91 | HTTP201, 18:34:01.988334 UTC |
| `service prepare brake --profile v3 …` | 1.16 | Brake18/V3 |
| `service sign brake/18.0.0` | 3.24 | Verified |
| `service upload brake/18.0.0` | 5.36 | HTTP201, 18:34:43.294260 UTC |
| `component prepare --profile v3` | 2.45 | VDP30/V3 |
| `component sign 30.0.0` | 0.94 | Verified |
| `component upload 30.0.0` | 4.07 | HTTP201, 18:35:50.415079 UTC |
| `component cloud-status 30.0.0` | 1.03 | Installed29, pending30, Online |
| `unit cloud-status test`, subsequent reads | 0.99 / 0.98 | Unit/services CURRENT; aggregate PARTIAL only for unreported optional fields |
| `backend inspect brake`, successful reads | 0.13 / 0.15 / 0.15 | Current Test synthetic receipts from Brake16, then17, then18 |
| `backend inspect tire`, successful reads | 0.13 / 0.14 / 0.14 | Empty before first launch; then Tire12 and successor13 |
| `backend inspect tire`, during service upload | 0.11 | BLOCKED; backend read still shares the environment writer with mutations |

Here `…` means the same explicit `--without-permissions --demo-mocked-data`
flags used for every service preparation, not an omitted execution helper.

- Second Safe Stop: requested18:30:37.743 UTC; VDP29 active18:30:40 UTC,
  approximately 2–3 seconds, 15 LIVE/READY paths, no restart loop.
- Backend read18:33:11 proves Brake17 and Tire12 receipts for this exact Test.
- Tire13 successor receipts observed18:35:14.703 UTC, while native Autopilot
  remained moving. No new Subject assignment or Safe Stop accompanied this update.
- Cloud18:35:15.691648 UTC independently reports Brake18 and Tire13 installed,
  one active instance each. Native Autopilot subsequently shows19.4 km/h.
- Brake18 backend receipts observed18:36:23.946908 UTC. Services have separate
  retained Group Subjects; no Production assignment was performed.

### Sequencing limitation exposed during this run

The first Tire Deploy was attempted while VDP29 was waiting for Safe Stop.
The runtime-input command returned BLOCKED. The source guard in
`service_inputs_guest.py` rejects an active component transaction before
projecting public inputs. The diagnostic output filter unfortunately omitted
the returned reason string; the active transaction is independently observed.
The batch used a newline rather than `&&`, so it proceeded to Tire assignment
despite that failure. This is a **test-driver sequencing error**, not a passed
execution of the protected UI plan: the real UI stops on a blocked prerequisite.
Both teams' inputs had already been prepared successfully against committed
VDP28 before any assignment, so no unvalidated input was manufactured as a
workaround. No manager restart or manual journal edit was performed.

VDP29 was then completed through native Safe Stop and the existing input
preparation command succeeded. Tire12 subsequently ran and produced backend
data, but its first launch is not counted as an independent while-moving proof.
The separate Tire12→13 publication-only update, with no pending FOTA, supplies
that replacement proof. The deployment guard interaction remains an operator
flow/efficiency observation; it was not silently removed during measurement.

The backend inspection attempted during Brake18 upload was blocked immediately.
Source inspection confirms `BackendService.execute` takes the global writer
even for inspect/status. Successful reads after upload take ~0.14 seconds.
This is a remaining concurrency limitation, not slow backend HTTP, and no
source change was made midway through this performance run.

### Final software and recovery measurements

| Command | Wall seconds | Result |
| --- | ---: | --- |
| `component status test`, final VDP | 2.28 | Active30/V3, slot a, 23 LIVE/READY paths, zero restarts |
| `service runtime-prepare test`, final VDP | 4.57 | COMPLETED, unchanged inputs |
| `backend stop brake` | 0.49 | STOPPED, storage preserved |
| `backend inspect tire`, while Brake stopped | 0.15 | Tire receipts increased; ready |
| `backend start brake` | 6.04 | RUNNING, no build/pull |
| `backend stop tire` | 0.39 | STOPPED, storage preserved |
| `backend inspect brake`, after restoration | 0.15 | Assessment count increased to13 |
| `backend start tire` | 5.97 | RUNNING, no build/pull |
| `vehicle connectivity off --target test` | 1.81 | OFF; native telemetry still LIVE |
| `vehicle connectivity status --target test` | 2.23 | OFF filter confirmed |
| `vehicle connectivity on --target test` | 2.14 | ON filter confirmed |
| `vm start test`, already running | 5.46 | No new VM; SSH/DNS/role reconfirmed; inner duration5.07 s |
| `simulation start --target test`, already running | 0.32 | Unchanged simulator, no duplicate process |
| `vehicle select test`, already current | 2.60 | Current Vehicle unchanged; Test data ready, Production source blocked |
| `unit cloud-status test`, after network restore | 1.31 | Same Unit Online; Brake18/Tire13 active |
| `backend inspect tire`, after restoration | 0.16 | Assessment count21, function-status22 |

Third Safe Stop was requested18:36:56.023 UTC; VDP30 active18:36:58 UTC,
approximately two seconds. No provider restart loop occurred. The existing CM
readout confirms active process, NRestarts0, a disconnect followed by a second
established connection, and continued full status/ACK activity. Cloud observation
18:42:26.206642 UTC confirms the same Unit Online with both services active.
There was no manual CM/SM restart or transient manager modification.

Brake outage was observed independently while Tire remained available. The
later Tire outage overlapped the external-network OFF test; its restoration and
continued ingestion passed, but this is not a fully isolated Tire-only outage
experiment. Cloud Offline during network OFF was not measured: the packet
filter/native telemetry proof does not establish server-side connectivity state.

### Retained-identity cold recovery

| Command | Wall seconds | Result |
| --- | ---: | --- |
| `environment park` | 14.64 | PARKED; entire Test stopped, backend storage/identity/disks preserved |
| `environment resume` | 82.50 | RESUMED; same Test, existing images, no provisioning |
| `component status test`, post-Resume | 2.29 | Active30/V3, 23 LIVE/READY paths, zero restarts |
| `unit cloud-status test`, post-Resume | 1.01 | Same Unit Online, Brake18 and Tire13 active |
| `backend inspect brake`, post-Resume | 0.12 | Brake18 receipts continue; assessment count22 |
| `backend inspect tire`, post-Resume | 0.11 | Tire13 receipts continue; assessment count26 |

Post-Resume Cloud/backend observations are timestamped18:46:32 UTC. Native UI
returned in stationary Manual, Test selected, telemetry LIVE, external network
ON. A subsequent Presenter Platform request returned200 in0.000810 s from
coalesced/cached observation: **not a fresh Cloud read**. Local snapshot200 took
0.168969 s. The direct CLI inventory1.01 s above is a fresh scoped Cloud command.

## Retirement and final state

| Command | Wall seconds | Result |
| --- | ---: | --- |
| `demo retire` | 36.06 | RETIRED: stopped Test/simulator, Cloud Offline, deprovision/delete, Unit/Node absence, scoped local cleanup |
| `status all`, final | 0.24 | Test not configured; simulator stopped; Production still running |
| `image list`, final | 0.07 | Immutable .31/.33 catalog entries preserved |

Retirement completed before18:48:36 UTC. This run did **not** reproduce the
earlier prolonged Cloud Offline delay. The36.06 seconds include all cleanup
stages; no exact substage duration is inferred from untimestamped progress text.
Final status is timestamped18:49:18.111845 UTC. Test's disposable overlay,
local factory copy and owned runtime/data were removed through the existing
retirement workflow without backup; these disposable contents are not
recoverable. Immutable factory originals, Production, retained Subjects,
published software and monotonic version continuity remain. No reclaimed-byte
total was measured. No broad filesystem deletion was used.

## Conclusions and follow-up

- Real Cloud observation commands normally took0.73–1.41 seconds in these
  samples. Live uploads, including preflight, took3.76–12.06 seconds.
  Preparation was1.02–2.59 seconds; signing0.94–3.26 seconds.
- The largest command times were first Create281.27 seconds (including native
  access interaction and first enrollment), cold Resume82.50 seconds and first
  simulator launch52.61 seconds. These are not equivalent to simple API calls.
  Native access dispatch/dialog handling was an agent/operator pause; it is not
  a controlled measure of VM boot or Cloud performance. Compound commands do
  not yet expose enough internal timestamps to separate every substage exactly.
- Unchanged `vm start`5.46 seconds and unchanged input preparation4.32–4.57
  seconds still contain repeated guest checks. These and backend read/writer
  contention are concrete candidates for a subsequent optimization, not changes
  silently made during the benchmark.
- VDP28/V1→29/V2→30/V3, Brake16/V1→17/V2→18/V3 and Tire12/V1→13/V1
  were observed working with the stated qualifications. Three FOTA transitions
  waited for native Safe Stop; post-Safe-Stop startup was approximately2–3
  seconds. Service successor replacement worked while driving, without another
  assignment. Same-identity cold recovery and final cleanup completed.
- This is **not an unassisted clean UI pass**: first Tire assignment continued
  after the runtime-input guard refused a concurrent FOTA transaction, as
  disclosed above. The independent Tire successor and recovery results do not
  erase that test-driver sequencing error. A future exact UI repeat must retain
  stop-on-failed-prerequisite sequencing and not overlap first Deploy with FOTA.
- Tire outage was not isolated from the network outage; server Offline during
  the filter-OFF interval was not sampled. Backend restoration/receipt recovery,
  actual network filter readback, local telemetry preservation and later Cloud
  Online were observed. No claim of fixing Cloud event ordering is made.
- Real permission-backed KUKSA, vehicle analytics/advisory and human visual
  acceptance remain excluded. Synthetic service/backend data is explicitly
  labelled. No product/manager source, image, access policy or Production
  deployment was changed during this run; no build, commit or push was performed.

Execution ran from the initial timed status18:10:15 UTC through final
status18:49:18 UTC. The overall session includes tool reviews, native access/UI
interaction, observations, documentation and time between commands. It must
not be presented as39 minutes spent inside Cloud APIs or as the sum of the
individual command wall times. These are single-run observations, not a live
before/after speedup experiment.

Subsequent source-only optimization of repeated guest checks and backend
read/writer contention is recorded in the
[performance follow-up](../research/democtl-ui-performance-audit-2026-09-13.md#follow-up-repeated-guest-checks).
The timings and qualification exclusions in this report remain unchanged.
