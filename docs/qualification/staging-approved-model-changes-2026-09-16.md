<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Approved model changes: preserved Test qualification, 16 September 2026

Status: partial functional qualification, not a complete pre-Factory gate.
Target: the existing Factory .33 Test on staging. Production is excluded.

## Current result: Brake48 quota and live advisory passed

Brake **48.0.0 / functional V3** is active on the preserved Test with native
package `pids.limit: 24` and `RLIMIT_NPROC: 24`. Before, during and after the
real maneuver, sampled usage was **one bootstrap + 16 product threads = 17**,
leaving **7 tasks (29% of the limit)**. The bounded current-instance journal
reported no thread/allocation failures. This is measured sampled headroom,
not a guaranteed peak or a completed cgroup isolation/stress qualification;
the cgroup counter projection was unavailable. Tire remains at 16; all other
quotas and all model thresholds are unchanged.

- Metadata source: `b88ba79aace431a6555ab21dedc7061abee42ee7` (local commit).
  The warm Brake-only build produced identical service/bootstrap binaries to
  Brake47; no VM image build occurred.
- One selected staging SP upload: HTTP 201 at 07:09:25 UTC, deployment
  `6b0a41c0-205b-473e-ab92-a3aafc695de2`; Ready at 07:09:39 UTC, version UUID
  `92d1c521-20cc-4211-81f8-1df80facb2dc`.
- Signed bundle SHA-256:
  `032569eee3f8e1aba7f3ed160613444c27d1a1718a6f192c861d74c3c314afd7`.
- Backend durably received real-input Brake48 assessments at 07:17:58.212
  and 07:21:27.699 UTC. Both contained 26 active samples, 13 straight eligible
  samples and 50% brake effort. Scores progressed **40/MONITOR →
  34/INSPECTION_RECOMMENDED**, preserving prior model state. The estimator
  truthfully retains `DEMO_SYNTHETIC` provenance; the telemetry is real CARLA,
  not injected assessments or substituted sensor values.
- The second assessment was `e4e4aea9-cbcc-5cb2-89b6-e9c59d797d53`.
  Its first request `217bce46-f60e-544d-a158-6b8e8a4d1dbb`, sequence 1,
  reached **Gateway APPLIED** at 07:21:27.845 UTC; the backend durably received
  the correlated fact at 07:21:27.943 UTC. Sequence 2 renewed it and was also
  APPLIED. Service readiness reached OPERATIONAL at least once.
- Native Driving Control & Telemetry was visually inspected: Test selected,
  LIVE, Safe Stop / STOPPED at 0.0 km/h, Brake **Inspection recommended**.
  Tire showed its own recommendation too; this observation does not replace
  the independent Tire backend/lease/replay qualification.
- The first 50% maneuver was rejected by the model after an input-gap episode
  and insufficient eligible samples. Subsequent valid episodes passed without
  any model change. Intermittent `KUKSA_DATA_UNAVAILABLE` transitions remain
  recorded; successful episodes do not qualify continuous-input stability.
- A separate reset/start harness race was reproduced: an initial stationary
  respawn frame precedes settling onto the road. `democtl` now requires 0.5 s
  of fresh advancing stopped frames (bounded by 5 s) before starting motion;
  the controller's physical-stop gate is unchanged. Fresh operation
  `27c70ec7-aa01-438d-b816-0f96b465993c` completed without a rejection/retry,
  13.35 s, 267 frames, 30.579 km/h maximum, final physical Safe Stop confirmed.
- Fixed a diagnostic-only Python name collision that shadowed the network
  probe. `component diagnose` now runs and confirms all telemetry/four advisory
  schema leaves. Its legacy Safe Stop binding comparisons still do not model
  the selected-Unit mTLS layout; they are not evidence that the working update
  runtime lost its authenticated binding. The diagnostic journal window now
  retains 600 bounded VDP records instead of 80, with existing redaction.
- Focused CLI exercise/schema/package tests: **41 run, one skipped, no
  failures** with the repository test import path. Quota contract tests:
  **10 passed**. An earlier direct unittest module invocation lacked the
  fixture import path; it was corrected, not treated as a product failure.

Cloud remains Online since 06:47:47 UTC. VM/Unit/Subject identities, VDP69,
CM/SM and the diagnostic proofs are preserved; Production is unchanged.
Full UI-driven replay, independent Tire round trip, original Brake V2 gate,
continuous-input stability and transient-security/Factory closure remain.
No new push, full E2E acceptance or clean Factory qualification is claimed.

## Follow-up: office network and Brake47/V3

- Cloud went Offline at 05:49:49 UTC during the host move. Test QEMU and CM
  remained running, the demo external-connectivity filter was ON, and local
  VDP/CARLA telemetry remained live. Guest DNS failed while the office
  resolver answered direct UDP/TCP requests in 23–28 ms. The bridge's TCP
  path answered; its UDP receive queue was congested by repeated queries
  from QEMU-owned sockets. Bounded instrumentation showed 20–30-ms upstream
  responses, excluding an upstream timeout as the steady-state bottleneck.
- One unchanged host-bridge restart did not help. A subsequent instrumented
  bridge restart classified the repeated-query congestion, also without
  resolving it. `democtl vm refresh-dns test --restart-guest-resolver` then
  restarted Test dnsmasq (694 → 135438) and the owned bridge. DNS passed at
  06:47:46 UTC; the same Cloud Unit became Online at 06:47:47 UTC. CM remained
  PID 10061, `NRestarts=0`, with the same binary SHA. No VM/CM/SM/VDP or
  container restart, reprovisioning, clock override or hosts-file change
  was performed. The initial trigger inside dnsmasq/QEMU is not fully isolated.
- Brake47 functional V3: source `16b54a403c5ff9cc3769a4b4c8ba7fd88a535024`;
  selected staging SP signing; upload HTTP 201 at 06:50:19 UTC; deployment
  `1a5c546d-53aa-478b-af56-d55931c32130`; service version
  `85bcd5be-5579-4d54-96b9-bf53648744f7`. At 06:50:59 Cloud reported Ready,
  Installed and active on the preserved Test / Brake Subject.
- A real Brake maneuver completed and confirmed physical Safe Stop, but its
  initial 25% brake did not meet the existing 50% capture threshold. It is
  invalid as model/advisory qualification. The harness now uses 50%; model
  thresholds are unchanged. Brake V3 also has observed `pthread_create failed`
  with bootstrap 1 + product 15 threads at native limit 16. The operator
  subsequently approved Brake-only `pidsLimit: 24` and a headroom check.
  Source metadata commit `b88ba79aace431a6555ab21dedc7061abee42ee7`
  builds identical bootstrap/service binaries. Brake48/V3 is prepared;
  live installation and headroom are not yet qualified in this checkpoint.
- Provider diagnostic collection no longer depends on optional journalctl
  `--grep` support. Bounded JSON projection now observes real Tire request
  forwarding and VISS acceptance; these are not Gateway application or
  dashboard advisory proof. The exact cause of the old grep return code 1
  was not established. Service diagnostics now separate capture, rejected
  input and advisory events; unavailable cgroup evidence is not zero usage.
- Focused recovery/CLI tests: 29 passed; DNS bridge tests: 6 passed;
  advisory/runtime/input/authentication tests: 51 passed. Corrected maneuver
  tests: 3 passed, existing braking-scenario tests: 5 passed.

The historical checkpoints below are retained as prior observations, not
claims that Brake V3 is still unpublished.

## Accepted changes and source checkpoints

| Change | Implementation | Proof boundary |
| --- | --- | --- |
| Tire task capacity | `pidsLimit: 16`, previously 8; all other quotas unchanged | Tire29 installed with native limit 16; bootstrap 1 thread plus product 14 threads; no observed thread/allocation errors in the bounded current-instance journal |
| Brake V2/V3 timing | 5000-ms delivery/source-age and input-gap budget; separate 100-ms maximum measurement skew; original timestamps retained, no interpolation | Brake46/V2 accepts live input, observed skew 0–10 ms; an accepted model assessment is still missing |
| Tire raw features | Per-frame `(maxWheel-minWheel)/max(maxWheel,5 km/h)`, maximum over the episode; persistence counts each valid sample once when any wheel reaches either absolute threshold, longitudinal 0.08 or lateral 4 degrees, inclusive | Three real-input Tire assessments durably accepted by the real backend; the approved profile digest is present |

Tire source: `715a5a0eda1b217b78ab8fb75e513f234fd23554`.
Brake model/timing source: `cb4e22ab038f4d119580e00bf3050ff60064bf6a`.
Brake diagnostic follow-up: `16b54a403c5ff9cc3769a4b4c8ba7fd88a535024`.
The latter limits timing diagnostics to newly observed maximum buckets so
ordinary jitter does not exhaust the model-event log budget. It is built for
V3 but not installed in this checkpoint. Source commits are local; no new push
is claimed by this receipt.

Brake profile digest:
`ea74cda63116d1f9fc969ec292aedb7cd0935ae899775bd8bcd73c230190e028`.
The known previous profile digest remains readable for retained model state
and pending messages. A successful new assessment atomically advances model
provenance without resetting wear, epoch, sequence or historical outbox bytes.
Unknown profile hashes remain rejected.

Tire profile digest:
`ba7f37351ac7297a3e61042dc2842e0f1d28e748757b38cde6fe7b8572712fd7`.
Tire delivery timing was not silently changed to the Brake policy. Its
existing 250-ms/exact-timestamp acceptance remains a separate implementation
fact, not a new approved timing contract.

## Live sequence and evidence

All package builds, preparation, signing, uploads, schema operations and
VM/Cloud observations used `democtl`. Native Driving Control supplied
Autopilot and Safe Stop; no synthetic assessment, advisory or telemetry was
injected. The same VM, Unit, separate Subjects, native service instances and
persisted model/outbox data were retained. No Factory image was built.

1. Renewed the existing bounded KAC time-marker access proof after its previous
   deadline. The replacement deadline is epoch `1789549400`; the proof remains
   transient and requires explicit security closure, not Factory acceptance.
2. Built, prepared, signed and published Tire29/V1 and Brake46/V2 using the
   current staging credentials. Cloud publication reached Ready and existing
   assignments delivered the releases without Subject reassignment.
3. Brake consumed real VDP67/V2 input. The observed completed braking episode
   was rejected as `INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`. Do not lower model
   eligibility or treat process readiness as an accepted assessment.
4. Published VDP68/V3 and observed installation in Safe Stop, Cloud Online,
   active slot `a`, all 23 telemetry paths, and zero provider restarts.
5. Tire still reported `VDP_INCOMPATIBLE`. `component diagnose test` proved
   all four D4-008 advisory schema leaves absent in the running broker's mount
   namespace. Tire checks these as well as its fifteen telemetry inputs.
6. Stopped only the Test simulation group, applied the exact temporary schema
   through `component schema-apply test`, and repeated it as a confirmed no-op.
   This adds the four fixed string leaves, preserves the base file and existing
   telemetry, and restarts only KUKSA. No permission/credential changes occur.
   Restored the simulator group and selected the same Test through `democtl`.
7. Tire29 automatically accepted the compatible schema and consumed real
   vehicle data, without a Tire reinstall or restart. Autopilot exercises
   produced the records below.

| Backend received UTC | Assessment | Samples | Score / band | Result |
| --- | --- | --- | --- | --- |
| 03:43:57.943 | `535134c0-5582-5276-bf69-4bc2bb5b6f4a` | 96 | 93 / GOOD | DURABLE_ACCEPTED |
| 03:45:09.026 | `8d6869b9-f099-5000-a802-23a11a056388` | 96 | 93 / GOOD | DURABLE_ACCEPTED |
| 03:46:19.824 | `b65d0c31-6896-5d51-92f4-3fea7139891b` | 97 | 91 / GOOD | DURABLE_ACCEPTED |

The initial NOT_EVALUATED → GOOD event
`0831be66-9744-5529-8ed2-1d0f075d6ff7` was also durably accepted. At 03:46:40,
the backend had a fresh Tire OPERATIONAL/READY function report. These are
real-input results of a **DEMO_SYNTHETIC estimator**, not a production tire
diagnosis. Backend advisory facts remained empty.

## Temporary schema inventory

- Schema: `/run/democtl-vss/vss.json`.
- Drop-in: `/run/systemd/system/kuksa-databroker.service.d/90-democtl-vss.conf`.
- Base SHA: `357e5af4e1ee6fa881c6a0ddf55e87320bedc966dd4faf7c70e14e57ba0fa73d`.
- Effective proof SHA: `78ef8f9c27beba748c489956770f610e7655bb2b04956f9e453ec2d37adcdff8`.
- Scope: the existing eight slip leaves plus Brake/Tire `Advisory.Request`
  string actuators and `Advisory.GatewayStatus` string sensors only.
- Undo: stop the Test simulator selection, run `component schema-remove test`,
  then restore the simulation connection. Reboot removes the runtime override.
- No new Factory schema source delta is qualified by this temporary proof.

## Tests

- Brake host CTest: 7/7 passed, including timing boundary and retained-state /
  historical outbox compatibility cases. Brake subscription/diagnostic source
  guards: 3/3 passed.
- Tire host CTest: 4/4 passed, including raw extraction boundaries and actual
  runtime assessment/outbox generation.
- ARM64 `democtl service build`: Tire V1, Brake V2 and Brake V3 succeeded with
  product-build test receipts. V3 is built, not published or live-qualified.
- Solution model/quota contracts: Brake 11, Tire 11, quota 10 passed.
- Temporary schema tests: 8 passed, including exact leaf/type constraints,
  first apply, no-op repeat, rollback, legacy-proof removal and foreign-target
  rejection. Service package tests: 25 run, 1 skipped; delivery tests: 27 passed.

## Remaining gates and accepted contract clarification

- Brake V2 still needs a real eligible episode and accepted backend assessment.
  V3 installation and real advisory cannot substitute for that gate.
- The frozen VDP V3 payload is telemetry-only. Its `advisory_enabled` flag is
  populated, but `AdvisoryPolicy` is not wired to the running KUKSA/VISS bridge.
  No Gateway acknowledgement or visible native indication has been proven.
- The previous advisory contract literally pinned service versions Brake3.0.0
  and Tire1.0.0, while service messages correctly carry allocated package
  versions. A direct local policy check of Tire29 returns
  `UNAUTHORIZED_SOURCE` before forwarding. The policy is not active in the
  live bridge yet; this is a proven prospective blocker, not a fabricated
  explanation for a live Gateway error.
- Operator-approved clarification, 16 September: express functional
  compatibility separately from package release numbers. Keep actual release
  provenance in each request; retain exact IAM/KUKSA path authorization,
  service isolation, schema/rate/replay/lease restrictions and no motion writes.
  Do not hardcode each new package number or bypass authentication.
- QM profile 1.1.0 and the VDP policy now implement this clarification.
  Focused tests: 8 QM contract, 7 Brake advisory contract, 32 VDP family tests
  passed, including new release provenance and cross-profile/path/replay denies.
  Existing frozen packages are unchanged; no new live advisory result follows
  from these source tests.
- Complete both advisory round trips, UI replay, KAC/transient security closure
  and consolidated Factory clean UI qualification only after these gates pass.

## Advisory transport follow-up — 16 September

Platform checkpoint `05cbff85c52eb0fe09641e177f1b3089a1df5b1f` passes
12 new transport tests, 32 VDP family tests and 14 provider tests. The new
transport has two bounded current-target entries, a single selected VISS
session, exact-path status publication and no new credential authority.
Identical request IDs across Brake/Tire remain independent; APPLIED remains
correlatable until the Gateway's EXPIRED status. Set success is never promoted
to application success. V1/V2 and frozen V3 profiles do not enable this new
runtime; a newly prepared profile must explicitly bind QM1.1.0.

Live preflight found the existing explicit `LOCAL_DEMO_SERVER_TLS` exception,
not selected-Unit mutual TLS. Demo Control starts Gateway with
`--viss-development` and supplies `LTVP_VISS_SERVER_AUTH_TEST_ONLY` guest
bindings. This is consistent with the 5 September local-demo decision but
insufficient for the accepted advisory writer authority. The source remains
fail-closed, and no new component upload/application or Gateway restart was
attempted. The operator has been asked whether to implement the previously
deferred mutual-TLS onboarding/client-integration slice. No legacy permission
is silently broadened to obtain a demonstration result.

Gateway source checkpoint `41d5e7103750311d0dc41f030bd0589cf6b2ecb9` passes
five targeted host CTests (advisory, dashboard, protocol, access and real local
mutual-TLS network), three native source regressions and Swift typechecking.
These cover authenticated application and read-only dashboard behavior;
whole-process restart reconciliation remains open. Source checkpoints are
local and have not been pushed as part of this follow-up.
Demo Control's new composition passed an offline real frozen-dependency/import
proof and explicit rejection of the current server-auth-only route before any
connection/publication. Its new-release selection remains disabled until the
mutual-TLS prerequisite is implemented and qualified; existing UI V3 preparation
continues to use the frozen telemetry-only profile. This is a source release
gate, not an authentication fallback or a claim that advisory works locally.
The current runtime remains VDP68 with 23 LIVE paths and zero provider restarts.
