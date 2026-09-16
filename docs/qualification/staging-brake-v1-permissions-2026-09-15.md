<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Staging Brake V1 permissions trial — 15 September 2026

## Scope and result

Operator-authorized scope: Factory .33, current Test only, baseline VDP,
Brake functional V1 with native KUKSA permissions, and real backend/dashboard
evidence. All live lifecycle and publication actions used `democtl`.
Production and Tire deployment were not changed. The operator confirmed
Safe Stop in Driving Control.

**Initial trial:** publication and delivery passed; service launch and real data
did not. **Authorized follow-up:** the 256-byte IAM/SM/CM proof below now passes
native Brake launch. Real KAC/KUKSA data is still unqualified. The same Test and
Cloud identity remain; the VM was not rebooted or retired.

| Boundary | Observed result |
| --- | --- |
| Provision / selected staging Cloud | Test Online; provision completed in approximately 29 seconds. |
| VDP V1 / 66.0.0 | Cloud Ready, installed, active process, zero restarts, provider-reported live source, seven read paths. This alone is not independent consumer evidence. |
| Brake V1 / 41.0.0 | Normal package, six exact read permissions, no synthetic/lifecycle-only switches, `noFileLimit: 1024`; signed by current-session SP and uploaded once. |
| Cloud package processing | Ready, bundle `done`, build information `Done`. Staging accepted this actual permissions-bearing bundle. |
| Desired assignment | Dedicated Brake Subject created/bound to current Test; desired status contains Brake 41.0.0 with one instance. |
| Delivery | CM reported Brake 41.0.0 installed. |
| Launch | Failed before a native container was created: `permission key parsing error (itemconfig.cpp:300)`. |
| KUKSA / product dashboard | Not qualified. No Brake consumer process or real Brake event/window evidence. |

## Verified permission-key capacity failure

The documented [service configuration schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-service-config)
allows a nested permission map with `r`, `w` and `rw` values. The prepared
package uses that shape; the public schema does not specify a key-length limit.

The Core implementation used by this Factory has a separate native capacity:

- `aos_core_cpp/src/common/ocispec/itemconfig.cpp`,
  `FunctionServicePermissionsFromJSON`: assigns each key into `mFunction`;
  the following check emits the exact observed error at line 300.
- Pinned `aos_core_lib_cpp` revision
  `60cb83535f773762c61ac5f544b31b7b88c502e3`,
  `src/core/common/types/permissions.hpp`: `mFunction` is
  `StaticString<cFunctionLen>`.
- At that revision, `src/core/common/config.hpp` defaults
  `AOS_CONFIG_TYPES_FUNCTION_LEN` to **32**. The platform recipe does not
  override this setting. The underlying string/array assignment returns an
  error when the key exceeds capacity.

| Exact requested read path | Characters | Fits 32 |
| --- | ---: | --- |
| Vehicle.Speed | 13 | Yes |
| Vehicle.Acceleration.Lateral | 28 | Yes |
| Vehicle.Acceleration.Longitudinal | 33 | No |
| Vehicle.Acceleration.Vertical | 29 | Yes |
| Vehicle.Chassis.Accelerator.PedalPosition | 41 | No |
| Vehicle.Chassis.Brake.PedalPosition | 35 | No |

At 16:13:39 UTC, CM reported `Can't schedule instance` with this parsing
error, then an instance failure. Subsequent status retained the same error.
SM/CM/VDP stayed active with zero reported restarts. No speculative upload,
re-assignment, process restart, permissions removal or broad wildcard was used
to hide the failed launch.

Increasing native permission-key capacity requires an agreed Core build change.
Replacing exact paths with short permission identifiers would instead require
an explicit KAC mapping-contract change; silently shortening paths is invalid.
Neither option was implemented in this trial.

### Authorized follow-up: 256-byte key capacity

After checking fresh upstream main (`aos_core_lib_cpp` `5560291ba6914e36a5b841ade4d8fc54134a9e91`
and `aos_core_cpp` `9d613a46df3c7f550062e2f19ae3406c57715694`), the operator approved
capacity 256 in **all three** managers: IAM, SM and CM. Upstream still uses
`StaticString<cFunctionLen>` with a default of 32 and the same parser assignment.
The earlier source-only 128 proposal is superseded. No permission mapping,
wildcard, value length, count, issuer or authorization change is included.

The build uses the immutable .33 Platform revision
`f7922b02b15f6cf816f181e1bf97572b61859aea` plus the three reviewed recipe files.
Demo Control checks that their only executable delta is
`-DAOS_CONFIG_TYPES_FUNCTION_LEN=256`, compiles the three affected recipes
offline, checks application/library compile-flag parity, exports ARM64 binaries
and restores the Builder layer binding before stopping Builder. It does not
build an image. The current Test's original packaged binaries and durable
identity/component records are preserved; activation is a transient `/run`
bind override with ordered IAM/SM/CM startup and stock-binary rollback on error.

Engineering commands (current authorized Test only; not Presenter actions):

```text
democtl component core-permissions-build test
democtl component core-permissions-status test
democtl component core-permissions-apply test
```

Focused host checks passed: native string capacity 32 reproduces three rejected
Brake V1 paths; capacity 256 accepts all six. A 256-byte key round-trips exactly;
257 is rejected without truncating or replacing the previous key. Both tests
pass; permission value/count limits remain unchanged. Nine orchestration/path
regressions and the existing 45 runtime-operation tests also pass. This is not
yet evidence of live KUKSA readiness.

### Forward profile/path audit

Read-only evaluation used the actual `package_configuration` function for every
supported service profile and scanned canonical JSON contracts, including VDP
compatibility and Advisory. It created no release or package and did not stop
the ongoing manager build.

| Current service profile | Permission keys | Longest UTF-8 key, bytes |
| --- | ---: | ---: |
| Brake V1 | 6 | 41 |
| Brake V2 | 12 | 50 |
| Brake V3 including Advisory | 14 | 50 |
| Tire V1 including Advisory | 17 | 62 |

All 27 unique package permission keys fit 256. The 93 distinct path-shaped
strings found across canonical contracts also have a maximum of 62 bytes.
The longest paths are Tire slip telemetry, for example
`Vehicle.CarlaSimulation.ChaosWheel.Row1.Right.LongitudinalSlip` (62 bytes).
Brake Advisory request/status paths are 40/46 bytes; Tire's are 39/45.
Current paths are ASCII, so byte and character lengths agree.

Each service uses one `kuksa` permission group and at most 17 keys, below the
separate Core maximum of 32 functions per group. KAC's independent limits are
64 entries and 512-byte paths; that does not imply the whole native chain
supports 512-byte paths. With this proof its effective key limit is 256.
Tire has only the agreed V1 content profile; no Tire V2/V3 was invented for this
audit. No future arbitrary path-length guarantee or completed Advisory E2E is
claimed.

### Live follow-up outcome

All three offline recipe compiles succeeded: BitBake completed 1,734 tasks,
of which 1,718 were already current. Compile flags were verified across 48 IAM,
92 SM and 72 CM C++ targets. Builder was stopped cleanly after export and its
original layer binding restored. No image was constructed.

| Manager | Exported/running executable SHA-256 |
| --- | --- |
| IAM | `d788ffbe4b93cf8e9c526b72a4ebaac65f98615dc7933db925a9343dd471b0bc` |
| SM | `a5dc8a726fc7f670fc2adbf6b557ee7d726abb7cc37f025c0b64affcea14cf80` |
| CM | `717bd7c8f1ac8e4b8ae73fd819092dd89a963e9338da2aa4b8b9629d9e08780e` |

The apply transport lost its final acknowledgement. No second restart was
issued. An independent guest read proved all three running hashes, matching
transient binaries/drop-ins, active processes and the committed VDP66 record.
Demo Control reconciled that exact attempt as `APPLIED` at 17:03:55 UTC with
`noOp=true`; the same PIDs remained. A regression test covers this post-read
reconciliation without a guest mutation. The precise transport-loss cause was
not established and is not presented as a manager failure.

Observed results:

- IAM/CM started at 17:01:03 UTC and SM at 17:01:04; all active, Result success,
  NRestarts zero. Current-process permission-key/value parsing failures are zero.
- IAM and SM both logged registration of the instance without registration errors.
- Native Brake container `fd340aca-07b2-3c01-b107-61bb71561630` is alive, runs the
  normal bootstrap as UID/GID 5000, has the native identity/secret environment
  fields present (values not read), and retains declared quotas/rlimits.
- At 17:04:31 UTC the selected staging OEM API reported Test Online and Brake
  41.0.0 instance 0 active, with no instance error. No new upload, version,
  Subject assignment or provisioning was performed for the proof.
- VDP66 remains committed in slot a, process/slot agree, seven paths are
  provider-reported ready from the live source, with zero automatic restarts.
- SELinux remains Enforcing; the complete post-SM-start kernel window reports
  zero AVC denials.
- The KAC request socket is still absent, as it was before this change.
  Container Running does not establish successful token issuance, KUKSA reads
  or real backend/dashboard data. That is the next separate diagnostic boundary.

Artifacts remain outside Git under
`demo-artifacts/aosedge-sdv-demo/runtime-proofs/core-permission-keys-256/`.
The live proof deliberately retains `/run/democtl-core-permissions-256/` and
`/run/systemd/system/aos-{iam,sm,cm}.service.d/96-democtl-permission-capacity.conf`.
These overrides are volatile and disappear on VM reboot; original .33 packaged
binaries and the immutable Factory image are unchanged. No Production state,
credentials, caches or unrelated artifacts were removed.

## Additional open boundaries

- Read-only KAC startup diagnosis is recorded below. The absent request socket
  is a separate boundary, not the cause of CM's earlier configuration-parser
  failure. Successful token issuance and independent KUKSA reads remain unproven.
- The current Function backend Presenter adapter/view reads the isolated mock
  summary endpoint. Real Brake windows/events need their existing normal
  backend endpoints wired into the dashboard, with explicit provenance and
  current-Test/version checks. No synthetic record was presented as vehicle data.
- In the initial failure the OEM UI reported `installed` without a confirmed
  running instance. After the capacity proof Cloud now reports the active
  instance. Installed, Running and functional readiness remain separate.

### KAC startup diagnosis after the capacity proof

The existing `democtl service runtime-inspect test` now includes a bounded,
read-only authorization-startup projection. It reports fixed systemd properties,
file existence/ownership/modes and allowlisted journal stage codes, never PIN,
token, certificate contents or arbitrary journal payloads. Its 20 focused
service-input tests pass, including diagnostic redaction; `git diff --check`
passes. This diagnostic did not start or restart any guest service.

- KAC is `inactive/dead`, PID 0, zero restarts, `ConditionResult=no` and has
  never entered the active state in this boot. The journal explicitly records
  a condition-skipped start, not a process failure.
- Its last condition evaluation was at monotonic 9.348412 seconds after boot.
  Startup wall-clock timestamps predate guest clock synchronization and must
  not be treated as current UTC event times.
- The provision marker, signing-PIN file and public verifier currently exist;
  the request directory exists, but `request.sock` does not. Presence alone
  does not prove successful credential loading or signing.
- The verifier preparation unit and Databroker are now active. The verifier's
  latest successful activation was at monotonic 3791.612988 seconds; KAC's
  condition was not re-evaluated with that activation.

The checked platform unit requires the provision marker and public verifier.
The substrate target wants KAC, but the VDP/provider preparation dependency chain
does not pull KAC in. A skipped condition does not mark a unit failed and does
not cause `Restart=on-failure` to retry when files appear; conditions are tested
when a start job executes. See the official
[systemd unit condition documentation](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml).
This explains how provider telemetry can be live while service authorization is
unavailable. The captured projection does not identify which individual file
condition failed at boot; it does establish that KAC was skipped and never
subsequently started.

Next bounded proof: activate only KAC through Demo Control after its current
prerequisites are verified, then check socket creation, native Brake token
issuance, actual subscriptions and normal backend data. Do not restart the VM,
IAM/SM/CM or the entire substrate for this proof. If the proof passes, close
post-provision activation in the existing startup lifecycle; do not remove the
authorization conditions or introduce polling as a substitute. No runtime fix
or real-data qualification is claimed by this diagnostic.

## Changes and focused checks

### KAC-only recovery and remaining time-marker access gate

The operator approved the bounded recovery plan. The existing CLI now supports
`democtl service runtime-activate test --kac-only`. This mode validates the
bound native Test identity and existing prerequisites, journals its single
attempt, and starts only the unchanged KAC unit. It neither activates SM
resources nor restarts managers, the VM, VDP or containers. Combining it with
`--restart-sm` is rejected; it is not exposed as a Presenter API action.

The live start succeeded: KAC PID **18373**, `active/running`, condition true,
zero restarts. Its Unix socket exists as UID 999 / GID 997, mode 0660. The
Databroker retained PID 10129 and SM PID 10104; the same Brake container stayed
alive. The existing post-SM-start audit window is complete and reports zero
AVCs with SELinux Enforcing. Socket existence proves transport availability,
not token issuance.

The credential-free KAC status operation repeatedly returns
`TIME_UNTRUSTED`, retryable. Brake reports authorization `NOT_READY` and has
no token file. Read-only checks established:

- `systemd-timesyncd` is active and its synchronization marker exists both on
  the guest host and in KAC's mount namespace, with file mode 0644 and parent
  directories 0755.
- Both the marker and its immediate directory have type `ntpd_pid_t`; KAC runs
  in `aos_kuksa_auth_compat_t`. The effective policy query
  `sesearch -A -s aos_kuksa_auth_compat_t -t ntpd_pid_t` succeeds and returns
  no allow rules. Absence of an AVC does not prove access is allowed.
- KAC's pinned `SystemClock::SynchronizedThisBoot()` opens that exact marker.
  A failed open is reported through the time gate rather than a separate
  access-error code. The missing SELinux read/search grant therefore explains
  the observed boundary; the causal live policy proof is not yet performed.
- Descriptor usage is 9 of 128. Two guest clock samples 44.91656 seconds apart
  advance by the same interval (within a millisecond); this is bounded evidence,
  not a general clock-stability qualification.

The initial safety review required explicit approval. The operator subsequently
approved the exact temporary grant: KAC directory search/getattr and file
open/read/getattr for `ntpd_pid_t`, with Enforcing retained, automatic rollback,
and no canonical policy-store mutation. That bounded proof has now **passed**.

The candidate was built in `/run/democtl-kac-time-read-proof` and reused after
tooling-only preparation failures. The alternate store path and its file labels
were corrected before compilation; a full `sediff` process later exited with
signal 9 before any policy load. Its cause was not independently established.
The final comparison used native SETools statements without expanding attribute
rule products, including type membership, permissive flags, conditional rules,
other declarations/rules and policy properties. It verified exactly two added
allow rules, zero removed rules, and no other changed categories:

```text
allow aos_kuksa_auth_compat_t ntpd_pid_t:dir { getattr search };
allow aos_kuksa_auth_compat_t ntpd_pid_t:file { getattr open read };
```

No clock marker was created or modified; no time gate was disabled. An unchanged
stock reload first verified the loader context. A forked rollback guard inherited
that context and restores stock on parent loss or its 75-second deadline; the
normal `finally` path restored it and verified the original active-policy hash.
The canonical policy store and Factory image were not modified.

Live results:

- KAC moved from `TIME_UNTRUSTED` to `ready` at the next 12-second sample and
  remained ready at the following sample. PID 18373 and restart count 0 were
  unchanged throughout; no VM/manager/VDP/container restart occurred.
- The existing native Brake41 bootstrap obtained a token at
  **2026-09-15 19:06:43 UTC**, owned by UID 5000 with mode 0400, and emitted
  `KUKSA_AUTH_CHANGED: READY`. Token bytes were not read into evidence.
- The original active-policy SHA-256 was restored and separately rechecked:
  `057a7caaa4c7387715af978df163bbc9551bb63033518b0e1265df17c7d61af9`.
  The isolated candidate SHA-256 is
  `bafa843730051d517a53c2d67b4a39a87ecebeba10b77fed7eff63b28a3143c7`.
- After rollback KAC correctly returned `TIME_UNTRUSTED`. After the issued
  lease expired, Brake removed its token and returned to `NOT_READY`. The proof
  is not a persistent repair and does not leave authorization enabled.
- The actual analytics process changed from `KUKSA_AUTH_UNAVAILABLE` to
  `KUKSA_DATA_UNAVAILABLE` during the token window. Its existing journal also
  contains `VDP_CONTRACT_ACCEPTED: READY`: the real service completed its KUKSA
  metadata RPC and validated the six required signal definitions. No operational analytics
  result or real backend record was established. A credential-free TCP/TLS
  probe from the container's network namespace subsequently succeeded with
  the declared trust and hostname; it is not a service-identity RPC proof.
- The final complete post-SM-start kernel audit window reports zero denied
  AVCs, with SELinux Enforcing. This does not replace application-level proof.
- The existing backend inspection reports no current mock records and still
  exposes the explicit mock-data adapter. It is not relabelled as real data.

The temporary copied policy store is preserved at the exact `/run` path for
review, inactive; no policy module is installed in the canonical store and no
rollback process remains after normal completion. No build cache or evidence
was deleted. The completed Demo Control proof receipt is a no-op on repetition,
not an assertion of current readiness.

Next: localize the real subscription/data-quality boundary, then consolidate
the proven marker-access rule and post-provision KAC activation in source.
The Brake V1 data validator still rejects samples older than 250 ms or ahead
of guest wall time, and requires one common source timestamp across all six
values. These are source facts, **not yet a proven cause** of this data failure;
no freshness requirement was changed during the policy proof.
The backend/dashboard migration and first functional real-data result remain
open. No new image or release was produced by this proof.

Focused service-input tests: 28 passed, including CLI selector rejection,
single-unit activation, idempotent reuse, missing-prerequisite rejection and
status-only protocol/secret-redaction checks, structural policy-delta rejection,
and rollback on parent EOF, deadline and explicit disarm, plus no reapplication
of a completed proof. The adjacent runtime suites also
passed: service activation 7/7, manager runtime 45/45, service identity 3 passed
with 4 existing skips. No live restart was performed by these fixture tests.

- Normal Brake/Tire package contracts and quota proof now declare
  `noFileLimit: 1024`; other quotas are unchanged.
- Presenter prepares normal native-permissions packages. Explicit synthetic
  CLI modes remain available, but are not automatic fallbacks.
- Package data-mode labels use prepared evidence rather than always saying
  synthetic. The mock-only Function backend view is not relabelled as real.
- Deploy's catalog scan no longer lets unrelated unscoped history hide an
  independently validated current-owner publication. Legacy-only results,
  unsafe paths and mismatching receipts remain blocked. No history was deleted.

Verification in this increment:

- Service packaging / Presenter operations / unsigned signing: 51 tests,
  50 passed and one existing skip.
- Assignment regression: failure reproduced first, then all 47 assignment
  tests passed after the scan correction.
- UI state-model tests: four passed.
- TypeScript and production UI build: passed, including the final normal-data
  text changes.

These are focused checks, not a completed permissions E2E or a new full-suite
qualification. Service upgrades, Tire, Advisory and a new Factory build remain
outside this trial.

## Five-second freshness and first real Brake window — 15 September, 19:46 UTC

The operator authorized widening the demo's timing window and continuing until
the service receives, processes and sends real telemetry. Brake V1 now accepts
source age and stream idle up to 5000 ms. The matching backend and both raw-window
provenance schemas use the same upper bound. Missing/future/mixed timestamps,
invalid values, trigger hold, capture duration, token lifetime and model/advisory
timing are not relaxed. No source values or timestamps were fabricated.

Two bounded hypotheses were tested, with distinct preserved receipts:

1. **Brake42, freshness only:** native authorization and metadata RPC succeeded,
   but the new bounded diagnostic reported `MISSING_VALUE`; the real backend
   had no windows. This disproved freshness as the only blocker.
2. **Brake43, explicit subscription field:** inspection of the exact pinned
   [KUKSA Subscribe source](https://github.com/eclipse-kuksa/kuksa-databroker/blob/30e5c13abc496d0b39aaa6c25acebb088b9902e3/databroker/src/grpc/kuksa_val_v1/val.rs)
   showed that Subscribe reads `entry.fields` and does not expand `entry.view`
   as Get does. Our request set only `VIEW_CURRENT_VALUE`. Adding `FIELD_VALUE`
   for the unchanged exact telemetry paths restored actual data ingestion.

The native Driving Control was used for Autopilot (approximately 19 km/h) and
Safe Stop. The service journal then reported, in order, `WINDOW_TRIGGERED`,
`BACKEND_SYNC_CHANGED: CONNECTED`, `READINESS_CHANGED: OPERATIONAL`, and
`WINDOW_COMPLETED: COMPLETED`. The backend's real `/windows` collection, read
through `democtl backend inspect brake`, independently reported:

| Field | Observed result |
| --- | --- |
| Event | `6cf15587-d0fa-43cb-8982-6b1c0fbf7455` |
| Test system UID | `6fcf5a740b744ef0a05d44bad598ab94` |
| Service version | `43.0.0`, native Brake service/Subject/instance provenance |
| Backend receipt | `2026-09-15T19:45:49.395Z` |
| Delivery / terminal state | `DURABLY_RECEIVED` / `COMPLETE` |
| Chunks | 4 received of 4 expected |
| Samples | 40: PRE 20, ACTIVE 7, POST 13 |
| Window SHA-256 | `4e6e05f37b8af33818c81c1043fb21d3d9da2755f1e1a6ed5589d91f048bca36` |

The explicit mock collection remained empty. The new engineering backend
projection keeps real `productData` separate from `mockData`; it does not
silently relabel the existing mock-only Presenter Function view as real data.

### Source, builds and publication

- Brake freshness source: `3a6696c80e1fc0f112ab32ee22071c46ae3a172c`.
- Brake subscription correction: `e1c30821abacbd1f71312c55649d53d0c64b9964`.
- Backend freshness source: `8060ea38fff5ddeb1a32f39f1ae8e76a5543c610`.
- Brake43 service ELF SHA-256:
  `39536bcb4ba96ff5e48fc4b5cf8b256c7caabee107ae63004f71b2ba0b46f588`.
- Brake43 signed bundle SHA-256:
  `15c6eef21ecd69ebdf96d4e089d86330d8966dcdeb55a94d40679049d81f017a`.
- Staging deployment `83c9c4ed-f15c-46bc-b1f7-2d400ca24c48` reached Ready;
  OEM observation independently showed native instance version43 active and
  Test Online. Existing Subject association was reused, not reassigned.
- Backend was rebuilt and stopped/activated/started through Demo Control;
  owned data volume/context were preserved. Docker Desktop and Tire were not
  restarted. All build/prepare/sign/upload/runtime operations used Demo Control.

Both ARM64 service builds passed their seven CTests. The explicit Subscribe
source guard passed. Backend TypeScript compilation and focused source-age
boundary tests passed. Demo Control service-input tests 30/30, backend tests
31/31, and Solution raw-window contract tests 7/7 passed. These are not a
full-suite, restart, later-profile or load qualification. The three new source
commits are local; no push or bulk Solution commit was performed in this trial.

### Rollback and remaining work

Both trials reused the exact two-rule candidate and full structural-diff gate.
They retained Enforcing and the forked rollback guard. The original active
policy hash was restored after each trial; the canonical policy store was not
changed. KAC stayed PID18373 / NRestarts0; the VM and managers were not restarted.
The final complete post-SM-start audit scanned 319 kernel records with zero
denied AVCs; Enforcing remained true. SM stayed PID10104 / NRestarts0.
The inactive copied policy store under `/run/democtl-kac-time-read-proof`,
256-byte manager overrides, receipts and build caches are deliberately retained.

This establishes the first complete **real data → native Brake processing →
durable backend result**, not durable unattended operation. After policy rollback
KAC cannot renew tokens; the existing short lease expires normally. The proven
marker-access rule and post-provision KAC activation still need consolidation
in platform source and a separately scoped persistent-runtime verification.
During driving, some frames were rejected as missing or mixed timestamps;
continuous-source quality remains an explicit follow-up, not hidden by the
successful event. The real backend window still needs Presenter/dashboard
integration. Tire, V2/V3, advisory, restart qualification and a new Factory image
remain deferred. The separate advisory subscription has the same view-only
request pattern and must be corrected/verified before its later V3 trial.
