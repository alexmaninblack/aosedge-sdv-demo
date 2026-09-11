<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio implementation checkpoint — 11 September 2026

Status: **partial implementation; not ready for full operator E2E**.
The [accepted P1–P8 plan](../planning/active/demo-studio-delivery-plan.md)
and [10 September evidence](demo-studio-implementation-progress-2026-09-10.md)
remain the baseline. This continuation does not change the approved story,
native left-hand composition, Production scope or service trust model.

## Explicit no-telemetry lifecycle experiment — 4.0.0

Latest follow-up: the subsequently authorized SM patch passed 74 native tests
and was applied once to Test at approximately 16:11 UTC. Live transition still
fails because CM rejects the old-version startup snapshot before scheduling
resend. See the [patch and reconciliation evidence](aoscore-service-update-teardown-2026-09-11.md).
Earlier observations below remain historical; no upstream PR is qualified.

<a id="no-telemetry-lifecycle-400"></a>

### Subsequently authorized single SM restart

The user approved one restart of the current Test SM to check already delivered
4.0.0. The existing `service runtime-activate` command now accepts an explicit
`--restart-sm` for its already-activated branch; ordinary repeats remain no-op.
The explicit branch writes no configuration, verifies the existing setup and
binary, and never retries on failure/response loss.

At 15:02:41–46 UTC, `democtl service runtime-activate test --restart-sm`
performed exactly one restart. SM PID changed from 137576 to 171280.
Its binary SHA-256 remained
`cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee`.
SM returned active/success; cold public-input preparation and post-start
verification both used committed VDP18.0.0. This proves the SM restart and
unchanged binary, **not service recovery**.

Post-restart logs explicitly show both saved service instances being started
as **3.0.0**, not 4.0.0. Their native OCI commands still have five arguments and
NOFILE limits 64/32. Both processes are absent at observation. Brake again
emits KUKSA_AUTH_UNAVAILABLE; Tire fails network-namespace cleanup with
`Invalid argument / failed to unmount namespace`. Native startup also logs
missing leftover container state and an unsuccessful unmount. Thus resetting
the SM process did not discard or correct the retained old instance state.

Cloud remains: Brake installed-version field 3.0.0, pending 4.0.0 with image
status installed; Tire pending 4.0.0 with image status installed and failed
instance. These are separate Cloud projections, not evidence of running 4.0.0.
SM/CM are active with zero automatic restarts; VDP18 remains active with its
pre-existing restart count one. No second SM restart, CM/VM restart,
reprovisioning, native-state deletion, new release or Production action occurred.
Retained-instance reconciliation remains the next unresolved boundary.

Targeted tests: 5 activation tests (including one-command/no-retry/binary-match
checks) and 14 input tests passed; the complete service suite passed 116 tests
with the installed official SDK/signer. The state below documents the preceding
pre-restart experiment chronologically.

The user subsequently approved explicit Test-only no-telemetry bootstraps, a
1024-file package limit in that mode, and launch/version-transition testing.
Normal authorization, SM, VM identity and Production remain unchanged.

- Brake source: `09358831a27330e9824cdea0cf6370506475e071`.
- Tire source: `4deb4e32220525665c011afd4e9433aa65033670`.
- Both host bootstrap/input targets compiled; process tests prove survival
  without tokens, SIGTERM/SIGINT shutdown, NOT_READY reporting and Production
  rejection. A Tire role-case mismatch was caught and fixed before publication.
- Through `democtl service build`: one warm ARM64 build per team; six Brake
  and three Tire CTest suites passed.
- All 114 Demo Control service tests passed with the installed official SDK
  and signer, including schema validation of both workaround configurations.
- `prepare --without-permissions --demo-no-telemetry` allocated 4.0.0 per
  team. Only that explicit mode adds the bootstrap flag and 1024-file limit.
  Both signatures verified against the configured SP certificate.

| Release | Deployment Bundle | Cloud version ID | Signed bundle SHA-256 |
| --- | --- | --- | --- |
| Brake 4.0.0 | c43f23e9-3a35-4b9c-a7f5-04c2da45c79e | e2f030af-11b7-47ab-b527-da5ac2110579 | 7f52b771bc27c168f1d2e95db1a70b012947a88c845f511d6eba5363e2f1a6ca |
| Tire 4.0.0 | 0d549d8f-208c-424d-8608-c90d0eb81fe8 | a5c0a409-2ec1-40c5-9714-c9443ccb1232 | 810f0cdc35c597120331bbe4cb82c7496380bee1c9d7802ef7246b22034f0958 |

Uploads returned HTTP 201 at 14:46:40/42 UTC. Both builds were Done/READY at
14:47:05. Native image-manager logs report both 4.0.0 images installed at
14:46:51. Existing separate Subjects delivered them without reassignment or
approval. These facts do not establish a running new instance.

**Launch/update proof failed at old-instance teardown**, before the new
configuration became effective:

| Old 3.0.0 instance | Stop failure at crunrunner.cpp:139 | Subsequent native observation |
| --- | --- | --- |
| Brake, 7cf522e4-ff3f-3b8c-b02e-b09458403b5a | No such process | Launcher starts 3.0.0 again; OCI still has five arguments and 64-file limit; process later absent |
| Tire, b14e8bca-b1a3-30a0-b44c-d972263deee6 | No such file or directory | Launcher starts 3.0.0 again; OCI still has five arguments and 32-file limit; repeats Too many open files at crunrunner.cpp:84 |

The pinned [native CRun runner](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/launcher/runtimes/container/crunrunner.cpp)
returns an error when `libcrun_container_kill(SIGKILL)` fails in StopContainer.
CM reports the new instances failed with activation timeout at launcher.cpp:392.
The new bootstrap/1024-file quota therefore has **not** received a live launch
proof. Host SIGTERM/SIGINT tests are application tests, not a claim that native
crun stops gracefully. The existing log command now retains only fixed errno
labels and source locations from redacted native errors.

SM/CM remain active with zero systemd restarts. VDP18 remains active with its
pre-existing restart count of one. No VM/SM restart, reprovision, runner patch,
cleanup or 5.0.0 publication was performed. Native-instance recovery is the
next separate step; then prove 4.0.0 Running before publishing its successor.
Telemetry/KAC/advisory and full N6 are intentionally not qualified by this mode.
Artifacts remain in the existing external service catalog, outside Git; old
packages, failing instances, source baselines and build caches are preserved.

## Follow-up diagnosis — native service launch

The user requested diagnosis only. No new release, assignment, restart, quota
change, authentication bypass or SM/product patch was performed. Current Test
and its failing native runtime state are preserved. Only existing Demo Control
read-only diagnostics were extended; the Presenter remains Cloud-only.

`service runtime-inspect test` now projects the two bootstraps' actual native
OCI limits, UID/GID, argument count, process existence and **presence only** of
the five native Aos variables. It never exports environment values, arbitrary
arguments, tokens or credential contents. `component logs test` now retains the
fixed `KUKSA_AUTH_UNAVAILABLE` structured event previously dropped because it
had no free-text `message` field. Targeted tests: 17 runtime + 23 delivery tests
passed (40 total; mocked lifecycle tests made no live mutations).

Observed facts:

| Boundary | Brake 3.0.0 | Tire 3.0.0 |
| --- | --- | --- |
| Image-manager installation | installed | installed |
| Native OCI executable | `/usr/bin/brake-health-bootstrap`, five arguments | `/usr/bin/tire-health-bootstrap`, five arguments |
| Native UID/GID | 5000/5000, supplementary 997 | 5001/5001, supplementary 997 |
| Actual `RLIMIT_NOFILE` soft/hard | 64/64 | 32/32 |
| Actual process/task limit | 16 | 8 |
| Actual memory limit | 16 MiB | 16 MiB |
| `AOS_SECRET` in native OCI environment | absent | absent |
| Other four native Aos identity variables | present | present |
| Launch | Native `Start instance ... state=active, error=none` at 14:05:29.399Z, then inactive | Fails before bootstrap with `openat2 sys/fs/cgroup [Too many open files]` |

SM itself remains PID 137576, active, with 28 open descriptors in the observed
snapshot. Its systemd soft/hard limits are 1024/524288. The service's much lower
32-file limit is not the SM service's systemd limit and does not indicate disk
space exhaustion. Both limits originate in **our** executable product contracts:
`brake-health-runtime-profile.v1.json` (64) and
`tire-health-product-profile.v1.json` (32), passed unchanged by Demo Control.

The [pinned native Instance source](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/launcher/runtimes/container/instance.cpp)
maps `quotas.noFileLimit` to `RLIMIT_NOFILE`. The
[native CRun runner](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/launcher/runtimes/container/crunrunner.cpp)
uses libcrun directly inside the SM process, not a clean external launcher.
AosCore declares crun 1.14.3 in its Conan recipe; that library's
[Linux setup](https://github.com/containers/crun/blob/1.14.3/src/libcrun/linux.c)
applies the service rlimit before namespace/mount setup, while
[container entrypoint setup](https://github.com/containers/crun/blob/1.14.3/src/libcrun/container.c)
closes unnecessary inherited descriptors later. These sources explain why the
32-file quota can fail during container construction, before Tire opens any
telemetry connections. The generated OCI limit plus the actual EMFILE error
localize the failure; a larger-limit live proof was not authorized/executed in
this diagnosis. The exact guest libcrun package version was not independently
read; Conan source evidence is not relabelled as guest package attestation.

Brake has a different failure boundary. Native Instance only registers IAM
permissions and injects `AOS_SECRET` when the permissions map is nonempty.
Both of our bootstraps explicitly throw on missing/empty `AOS_SECRET`, before
forking analytics, and their catch block emits `KUKSA_AUTH_UNAVAILABLE` then
returns 2. The existing journal contains that fixed event at
14:05:31.596982Z following the Brake relaunch. Journald attributes the inherited
stream to SM, not independently to the bootstrap executable; the projection
therefore leaves `team=null` rather than fabricating attribution. The generic
catch event does not distinguish earlier metadata errors, but the observed
missing secret is independently a deterministic fatal bootstrap condition.

Consequently, removing `permissions` is sufficient for Cloud build/delivery but
**not** for these unmodified services to remain Running without telemetry.
The earlier blanket description of both failures as unrelated to missing KUKSA
authorization was inaccurate. Tire hits resource setup first; Brake reaches a
bootstrap that intentionally requires authorization. There is no evidence here
that SM needs replacement or that provisioning/Subject association must repeat.

Proposed next decision, not implemented: increase the package descriptor budget
(for example a bounded 1024 for this demo), then either retain intentional
bootstrap failure for delivery/version-only testing, or explicitly approve a
separate no-telemetry demo mode which remains alive without contacting KUKSA.
Normal authorization must stay fail-closed; never fabricate `AOS_SECRET` or use
the Provider's token. A successful Running/version-transition claim still needs
the separately agreed live proof.

## Permission-free delivery experiment

The user reported the platform team's diagnosis: a service `permissions`
section triggers a Cloud build failure. The user authorized omitting it for
both services to test delivery/version handling without KUKSA telemetry.
Demo Control now exposes explicit `service prepare <team> --profile v1
--without-permissions`; the normal default still includes native permissions.
No authentication bypass, SM change, VM restart, image/product build, Production
change, cleanup or backup occurred in this experiment.

Both packages reuse the exact existing ARM64 v1 executables from the previous
2.0.0 attempt. Only the allocated version and permissions omission changed.
Preparation records `DELIVERY_ONLY_NO_KUKSA_AUTH`. The official signer confirmed
RS256 and prepared-payload equality. All preparation, signing, upload, assignment
and live observations were executed through `democtl`.

| Service release | SP Deployment Bundle ID | Cloud version ID | Cloud build result |
| --- | --- | --- | --- |
| Brake 3.0.0 | 407ea227-0f42-4445-9bfe-93f35c00bb82 | 5ef448a5-cc6a-4b1b-9750-107a8a432089 | HTTP 201; Done / ready at 14:04:05Z |
| Tire 3.0.0 | 0c12036b-30f7-4e31-b4fe-782b8f520841 | 5f20d8d1-86b9-4f32-b56c-f0141f6fb3e2 | HTTP 201; Done / ready at 14:04:06Z |

Signing SHA-256: Brake
`ca95d357426012b68780af60f6d8fa9bb3a06168d1bc25fac9d92b710fa14c77`;
Tire `cc0ae563b92362c40699b4ed00c8f859f9256e4d313e6fb10f66a73b7368f60e`.
Artifacts remain outside Git in the catalog's `services/<team>/releases/3.0.0`.

The two retained per-service Subjects below were reused. After exact absence
reconciliation against the newer READY release, one explicit new service
association attempt per team succeeded. No Subject was recreated or rebound.
Old 2.0.0 attempts remain in the journal. Same-release uncertain attempts still
cannot be replayed; creation/binding never receive this newer-release exception.

Post-read exposed two Demo Control interpretation defects, corrected against
the [public OpenAPI](https://api.aoscloud.io/api/v11/openapi.json):

- A service's Unit recipient row lists all Subjects attached to that Unit, not
  the Subjects assigning that particular service. Scope now uses actual
  `(Subject, service)` relations from the Unit service list; peer/default Unit
  membership is allowed, but a service assigned through an unrelated Subject
  still blocks.
- Unit service list rows use a Subject UUID; detail rows use a Subject object.
  Both normalize to the same validated ID before projection/pagination.

At 14:10:55Z / 14:10:59Z, repeat assignment commands reconciled with `noOp=true`,
`unitBound=true`, `serviceBound=true`, and no further POST:

| Service | Cloud observation | Native evidence from existing `component logs test` |
| --- | --- | --- |
| Brake 3.0.0 | Installed version 3.0.0; instance 0 inactive | Download/install completed; CRun launch attempted; native restarts exhausted |
| Tire 3.0.0 | Pending status `installed`, installed version null; instance 0 version 3.0.0 failed | Image manager marked 3.0.0 installed; launch failed with `openat2 sys/fs/cgroup [Too many open files] (crunrunner.cpp:84` |

Guest image-manager events at 14:05:29Z explicitly mark **both** packages
installed with no install error. This establishes delivery and package
installation, not healthy execution. Tire's conflicting Cloud version/status
fields are retained rather than normalized into a successful runtime. The native
launch failure is distinct from the intentionally missing KUKSA permission; the
underlying descriptor/limit cause is not yet established. No fabricated KAC
error or successful product bootstrap is claimed. No 4.0.0 update was published
to mask the unresolved runtime boundary; version-transition proof remains open.

Additional observation for later reconciliation: Cloud Subject reads report
`is_group=true` for the two retained Subjects, while CM desired-status log lines
render their type as `user`. No type mutation or inferred cause was introduced.
SM and CM remain active, with `NRestarts=0`; VDP remains active (its existing
provider reconnect/restart observations are not service functionality proof).

Targeted regression evidence: 113 service-family tests with the official signer,
25 Cloud observation tests and 6 CLI tests passed (144 total). Coverage includes
normal permissions retained, omission-only package difference, API/CLI flag
validation, Finder `.DS_Store` ignored as metadata rather than a release, real
Subject list/detail shapes, unrelated assignment rejection and no POST replay.
Finder metadata is preserved; no release directory is removed.

## Earlier continuation — separate service Subjects, Test only

The user approved replacing the shared Subject with separate retained OEM Group
Subjects for the logical Brake and Tire services. Both remain current-Test-only;
release updates reuse their identity. `democtl service assign <service-id>
--target test` now implements this model and reports package readiness separately
from desired association. It requires the exact accepted publication receipt and
matching service/SP/version identity, but no longer invents a local READY gate.

The authorized calls created and bound these objects to current Test
`2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, native UID
`d53d05cd4c4649c9a896534b23b88273`:

| Logical service | Group Subject label | Recorded Subject ID | Confirmed result |
| --- | --- | --- | --- |
| Brake | AosEdge SDV demo Brake | ede5ae8b-9796-4bea-88d1-d2dfcab24725 | Create 201; Test binding 201 and authoritative read |
| Tire | AosEdge SDV demo Tire | e6699b5d-b243-4bfe-8e0c-b905fcfa14df | Create 201; Test binding 201 and authoritative read |

Each service association was attempted once, but the post-read remained empty.
At 13:01:36Z and 13:01:38Z, explicit CLI reconciliation returned `noOp=true`,
`unitBound=true`, `serviceBound=false`, `serviceIds=[]`, and package version
2.0.0 `uploaded` / `ready=false`. No POST was replayed. Assignment remains
`UNCERTAIN`, not ASSIGNED/installed/Running. The earlier failed Cloud bundle build
remains unresolved; these observations do not establish why association failed.

The original assignment exception was reduced to a generic reason. A targeted
worker test reproduced duplicate `CloudFailure` classes when launched by filename
versus imported by an adapter. The worker now shares its canonical module identity;
assignment preserves fixed HTTP codes while still redacting response bodies.
This fixes future diagnostics, not the lost original response. No response was
invented and no retry was issued merely to recover that diagnostic.

Cloud-only Unit observation at 13:01:00Z confirmed Online, VDP 18.0.0 installed,
the two new Group Subjects plus the unchanged protected default Subject, and
zero reported services. Production, Unit Sets, VM/SM, firmware, product data and
existing packages were not changed. No new bundle, image, backup or cleanup was
performed. Current transient runtime inputs and all diagnostic state are retained.

Validation: 107 service-family tests (24 assignment tests, including real
filename-worker exception identity), 27 Unit tests and 20 lifecycle tests passed:
154 total. Cases include both assignment orders, Tire-only, non-ready packages,
exact ownership/current-Test checks, no peer contamination, default preservation,
idempotent repeats, response loss, no blind replay, legacy-shared-record refusal,
and retirement guard preservation of the new records. Subject cleanup integration,
native service launch and N6 functional proof remain open. No full VM reboot or
Factory build is claimed. Source/doc checkpoint only; no artifact/secret enters Git.

## Earlier publication check — OEM arm64 only, releases 2.0.0

The user removed `arm` from the OEM architecture list. A subsequent
`democtl service list --profile oem-delivery` confirmed exactly `[arm64]` at
2026-09-11T11:47:14Z. Existing 1.0.0 bundles remained in their terminal Error
state; changing the OEM did not restart their processing.

The user then explicitly authorized signing/uploading Brake and Tire 2.0.0
to `SP alex_agizim`, owner `fa2c914f-dfc8-48e8-9888-1671c2c9c8c4`.
Both packages reuse their existing verified ARM64 binaries and functional v1
content; only the allocated release value changed. No product rebuild, OEM
mutation by Demo Control, VM restart or Subject assignment occurred.

| Team | Bundle ID (one accepted HTTP 201 upload) | Created service ID | Created version ID |
| --- | --- | --- | --- |
| Brake | 7a93da7b-f318-442b-95b9-75378fa575f6 | 3bc71fa0-aae5-4363-8298-8d06501c3132 | 7f58a43b-ba00-4ebc-aa8f-994f62763b82 |
| Tire | 7c4c069e-c7cd-4b42-88c4-e64b280c0861 | d98957a1-83c2-4d14-a6fb-4e6a6ad27c77 | e0ac84ae-fcbb-4621-bd64-42a1c028594c |

The official signer verified RS256 and prepared-payload equality. Signed bundle
SHA-256: Brake `b3293da19f1f9de1f89b5db2036268492e51662348e6b37d0d4e85a96c397f21`;
Tire `0d4935049b946141dc03b0a4957123ed2ed2ca1a67ed4600ee410822d113bdf8`.

Both new bundles failed with `Error: Failed to build deployment bundle.`
The previous missing-`arm` message did not recur and Cloud now created both
service identities and versions, but this is not a successful container build.
Exact-version reads at 11:53:49Z / 11:53:53Z reported `container_state=uploaded`,
`container_build_info=null`, `container_config_data=null`, `min_num_instances=1`
and priority 10. Both service recipient lists were empty. No READY, installation
or execution is claimed. An internal Cloud build diagnostic is required to
classify this new failure; do not infer a package fix from the generic message.

`service inspect` now exposes the documented `container_build_info` through
the existing bounded/redacting text projection, without additional API calls
or raw configuration output. Its focused tests pass (18 tests). The earlier
OEM architecture hypothesis and first-upload evidence below remain historical;
the current blocker is the generic Cloud bundle build failure.

## Earlier continuation — startup configuration and first native service publication

The user accepted the cold/warm input split. `democtl service runtime-activate
test` succeeded on the retained Test with one controlled SM restart:

- Native IAM fileidentifier `/etc/machine-id`, IAM TLS `GetSystemInfo` and the
  provisioning context agree on the Test system UID.
- Pre-SM stage `PREPARED`, `processVerified=false`, VDP 18.0.0,
  monotonic observation 54035618206063; post-SM stage `VERIFIED`,
  `processVerified=true`, same VDP, monotonic observation 54035937140619.
- SM active/success, PID 137576, `NRestarts=0`, unchanged binary SHA-256
  `cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee`.
- Read-only follow-up confirmed both team input resources, root-owned 0444
  metadata and the native private token tmpfs with 1777 root, 64-KiB limit and
  retained `rw,nosuid,nodev,noexec` flags.
- The subsequent unchanged `runtime-activate test` returned `noOp=true` and
  `currentProcessVerified=true`; SM PID remained 137576 with `NRestarts=0`.
- This is configuration under `/run`, with `transient=true` and
  `rebootQualified=false`. The immutable rootfs and existing temporary SM fix
  were preserved. No full VM reboot, new Factory image, retained service
  recovery or native service execution is claimed.

Both migrated backends were built/activated/started through Demo Control;
health is healthy and existing data preserved. Brake source `d7626b7c` produced
image `sha256:6d8f561051461eef40176031cee5416a1521e5c3a59caceddf9445e63303a99e`;
Tire source `b383c02a` produced image
`sha256:f9a25be0f82d05ddeb26da7ffdd474bb77fe5c6912cfec9bfb0ab72b14c150d3`.
Backend process health alone is not product ingestion readiness.

Brake ARM64 source `bc0ed655d87297746955307695c3102881049316` was built
successfully through `service build`; Tire reused its completed `1698ee4`
export. Each prepared v1 package received `1.0.0`. The official signer verified
RS256 and byte-for-byte equality with the prepared payload before upload.

| Team | Exact accepted deployment | Upload result | Subsequent processing |
| --- | --- | --- | --- |
| Brake | ff672a59-9566-4db7-a205-1b5e15961a57 | 201, 2026-09-11T11:14:07Z | Error: service does not support architectures `{'arm'}` |
| Tire | 44f09c7d-c049-4f4b-ad5c-da54bef76358 | 201, 2026-09-11T11:14:55Z | Same architecture error |

Signed digests are Brake
`e0925b80835cb65d9c26dfb11c2371a070fad7ebf0a0897bc2ceb8ae62cceb53`
and Tire `7127eaf89df262415fc32e960e230ada85c56a0bc74b621533e4503b23fdb094`.
Artifacts and receipts remain outside Git in the existing service release
catalog. Failed versions remain consumed; no bundle was overwritten/retried.

Both exact configurations contain only `images[].archInfo.architecture=arm64`.
At 11:20:18Z, `service list --profile oem-delivery` read native API architecture
lists: available includes `arm64`; assigned to OEM
`60266780-a6e3-4998-a7b1-b39f246cf81d` is `[arm, arm64]`.
The absent `arm` matches Cloud's error. This strongly indicates an OEM/package
architecture requirement, but public OpenAPI does not expose the bundle
builder's validation algorithm. Do not claim internal causal proof or silently
change tenant-wide settings. The SP catalog still contains no Brake/Tire
service identity; no Subject/assignment POST or batch approval was performed.

The initial `service assign <catalog-service-UUID> --target test` source was
implemented and isolated-tested with one dedicated retained Group Subject, exact
native Test UID, service IDs only, peer/default preservation and durable
uncertainty handling and a local READY gate. Both the allocation and that gate
are superseded by the latest continuation above. The observer
now recognizes actual bundle state `building` as PROCESSING. No UI capability,
new SM code, deprovisioning, cleanup or Production change was introduced.

Final focused regression: 100 service-family tests (including installed official
signer), 6 CLI, 27 Unit, 21 source and 80 component tests passed: 234 total,
no skips. The documentation gate passed for 170 Markdown documents, 658 stable
identifiers and 38 Mermaid diagrams. These fixture/source checks do not replace
the blocked native service execution or retained-assignment cold-start proof.

Remaining boundary: separately authorize any OEM-wide architecture adjustment
(or resolve the platform's requirement), then prepare the next allocated
releases, sign/upload and prove native launch/KAC/ingestion. Full retained-
assignment VM reboot still needs persistent startup integration in a later
authorized image packet. N4/N5/N6 are not reported fully closed.

## Earlier continuation — native inputs and real Tire product build

The latest changes preserve native AosCore container preparation, launch and
retained-instance recovery. No SM code/configuration change, restart, Factory
build, provisioning cycle, Cloud mutation or Production change occurred in
this continuation.

- Tire source checkpoints `e3bdfa7` and `1698ee4` add the pinned real ARM64
  product export and a formatting-only GCC warning correction. The first build
  failed on `-Werror=misleading-indentation`; existing BuildKit history located
  the exact source errors without repeating the failed build. The corrected
  revision completed through `democtl service build tire --content-profile v1`
  at 10:27:10 UTC. A subsequent invocation returned `noOp=true` and reused the
  same receipt. No source push occurred.
- Exported bootstrap SHA-256:
  `b63c27cba9736b6387dfc0e29ad7d343956c99556edd1c099d5d3a41e43844f5`;
  service SHA-256:
  `d87451dde73ecf4dcd57145cd4133b7f328fc9c893bf6e86fcb2d4b5af95ff0b`.
  Product outputs remain outside Git under the artifact catalog. Compilation,
  product tests and declared dependency closure do not prove live analytics.
- `democtl service runtime-prepare test` successfully reconciled native IAM
  v6 identity over authenticated TLS, validated committed VDP 18.0.0 / active
  slot a and projected compatibility 1.0.1 plus the public KUKSA certificate.
  A repeat returned `changed=[]`, `noOp=true`. Read-only inspection confirmed
  both public metadata files owned by root with mode 0444. Source directories
  remain `/run/aos-demo-service-inputs/brake` and `tire`; they are intentionally
  retained for the next bounded integration step, not copied into an image.
- Native IAM requires TLS on 8090 with server name `main`; the initial
  plaintext diagnostic failed before projection. The implementation uses the
  official SDK trust root and a temporary pinned SSH Unix-socket forward to
  Unit-local 127.0.0.1:8090. No DNS change, guest SDK, persisted identity,
  Cloud login or credential-content output is involved.
- Focused Solution tests: 74 service tests, including the installed official
  signer, native TLS transport, public trust parsing, projection/refresh,
  negatives, idempotence and build-history reconciliation; all passed without
  skips. Six CLI, 80 component and 21 source regression tests also passed
  (181 test executions in the focused groups); the 10 public-input tests also
  passed under the CLI Python environment. The documentation gate passed
  (170 Markdown documents, 658 stable identifiers, 38 Mermaid diagrams).
  These are source/fixture proofs except for
  the explicit live build/projection results above.

N4 native resource activation is still pending. Current Test retains the
existing SM PID 1458 and its existing resources (old 0700 token tmpfs and no
team-specific input mounts); this continuation did not activate the migration.
No native Brake/Tire container launch, KAC renewal, real backend ingestion or
retained-assignment reboot is claimed.
The final read-only `component status test` still reported VDP 18.0.0, slot a,
PID 44297, process/slot agreement and 23 read paths. Its restart counter remained
1 from the earlier run; this continuation caused no provider restart and does
not report a zero-restart qualification.

N5 has a concrete [cold-start ordering conflict](../architecture/demo-control-service-inputs.md#cold-start-ordering-conflict--11-september-2026):
the existing pre-SM bootstrap cannot satisfy a running-VDP prerequisite when
SM component recovery is what starts VDP. The missing-provider fixture fails
without fabricating public readiness. Resolving the cold versus warm input
gate requires an explicit contract decision; no launcher, daemon or SM hook
was added to conceal this. The latest N4/N5 state supersedes the earlier dated
source-only observations below, not the accepted phase definitions.

## Earlier outcome by phase

| Phase | Current result | Still required |
| --- | --- | --- |
| P1 | Shared Test lifecycle source, current-state reentry and backend ownership/cleanup adapters | Complete scoped retire/fresh-run integration, including future service bindings |
| P2 | Normalized Cloud-only inventory, publication receipts, visible observer and resource view | Service-instance integration and observed metric coverage in the actual tenant |
| P3 | Previously recorded VDP18 and retained-Test Park/Resume proof preserved | Final fresh CLI story with the complete service-capable baseline |
| P4 | Initial Studio B2 workspace connected to existing lifecycle/VDP operations | Complete live UI repeat and operator visual approval; team product panels not connected |
| P5 | Brake profiles; native token/input/provenance source migration and producer/backend conformance | N4 package/public projection, N5 boot ordering, current-source ARM64 build and N6 real ingestion chain; former token-owner/manifest gates retired by ADR 0015 |
| P6 | Brake v2/v3 profile implementation and focused source tests | Live assessment/advisory and independent consumer evidence |
| P7 | Independent Tire source/backend, native provenance, retained request binding and schema-aware cleanup | Raw-feature/load-worker contract closure, real query consumers, ARM64 runtime integration and complete live/offline proof |
| P8 | Checkpoint/source consolidation in progress | Full clean-image and visual repeat; success-gated final cleanup |

## Presenter and Demo Control changes

- Approved automotive B2 assets are reused from mockup 2.8. Mockup files and
  native CARLA/Driving Control are unchanged.
- Page opening and navigation do not mutate the environment. Full story and
  Quick preparation remain explicit protected operations. Create starts Test;
  first simulator connection is stationary Manual. Provisioning can resume its
  unfinished membership stage even when Cloud already says provisioned.
- Park, Resume and Finish use shared Demo Control operations scoped to Test.
  Production remains excluded. Automatic release allocation is not an operator
  input. Existing native password/Keychain and confirmation boundaries remain.
- Current-run prepared/signed/submitted receipts survive page/server reentry.
  Previous-run jobs cannot select a candidate. Each profile retains its exact
  Cloud publication result when another profile is selected or published.
- Upload acceptance, Cloud publication and installed version are distinct.
  There is no required batch-approval button and no simulated successful update.
- Architecture, Platform and monitoring use normalized Aos Cloud reads, never
  guest diagnostics. Installed does not mean Running. Missing service data is
  not an empty inventory; absent metrics are not zero. A genuine zero DMIPS
  sample is retained. Stale data is marked and cannot cross Unit bindings.
- Monitoring is visible-only and has an explicit return to the vehicle map.
  Brake/Tire panels disclose that product integration is not yet connected.
- `democtl ui stop` stops only the identified idle Presenter process; it does
  not stop VMs, simulation or Cloud Units. It refuses uncertain/busy sessions.
- `democtl service runtime-inspect test` is an explicit engineering-only,
  read-only guest observation. It reports native ABI, selected declared mounts
  and public-input ownership/modes, never credential contents. It is not an
  HTTP/Presenter capability.

## Owned source revisions and product artifacts

| Repository | Revision | Scope |
| --- | --- | --- |
| aos-vehicle-platform | `161108b6e96ff1f43ecccc776f28a7792f4c73ee` | Opt-in per-service public metadata/CA resource template; no active recipe or VM change |
| brake-health-service | `8bae83066df071f5cb3bf7791ab6dedc00843d3d` | v1/v2/v3 product profiles, bootstrap, real KUKSA transport, durable recovery and capability readiness |
| tire-health-cloud | `c3b2d2aedffbf94e78c9a38bae45d5ba753e3765` | Independent product ingestion, query/storage and exact scoped cleanup |
| tire-health-service | `cb1bfca2180a747128ab65d24951d6d5d63ea1d8` | Independent runtime source with strict provenance and durable delivery; not live-qualified |

Platform, Brake and Tire backend revisions above were pushed to their existing
`alexmaninblack` working branches, without changing main or forcing history.
The canonical [Tire source repository](https://github.com/alexmaninblack/tire-health-service)
is public under **alexmaninblack**. On 11 September, the user authorized a new
repository in that account instead of transferring the earlier copy. The
existing source history was pushed unchanged; GitHub confirms that
`codex/studio-tire-runtime` points to the revision above, and local `origin`
now uses the canonical URL. The earlier repository under **AlexAgizim** was
left untouched for the user to remove separately; it is not an active project
remote. No account transfer or history rewrite was performed.

All three Brake ARM64 profiles were built successfully through
`democtl service build brake --content-profile v1|v2|v3`.
Each profile has a separate source-bound artifact path under
`demo-artifacts/aosedge-sdv-demo/services/brake/builds/<source-revision>/<profile>`.
ELF architecture and product test manifest are verified at this build boundary;
no image, binary or build output is committed to Git. The actual guest is
AArch64 with glibc 2.39, compatible with the built Brake binary's glibc 2.36
minimum. This ABI check is not evidence of successful service startup.

Executable message schemas accept canonical monotonic release numbers rather
than one hard-coded service version. They retain model/policy/profile semantics;
changing a Cloud release number does not redefine the functional contract.

## Tire backend integration

The new backend image is
`sha256:479c0dfe9c30bfc812995a86d8f6097ae22164364883e504cb26b69491e21685`.
It was built, explicitly stopped/activated/started through Demo Control, with
the existing volume and context preserved. Process startup succeeded; real Tire
service ingestion has not been demonstrated.

The immutable build/runtime record selects private cleanup protocol
`tire-product-v1`. Scoped preview/execute checks all six product record counts,
the exact retiring UID and nonmatching hash preservation. Single-Test volume
removal still needs schema-aware whole-store emptiness. Legacy foundation
records retain their foundation-only proof rather than claiming product
emptiness. Tests use disposable fixture stores; no live product data was
deleted in this continuation.

## Concrete P5 gates — no further bundle guessing

1. The existing KAC token-directory tmpfs requests mode 0700 without per-instance
   ownership. Native CM assigns a non-root service UID; native SM copies the
   resource mount options. The bootstrap requires its token directory to be
   owned by its effective UID. These inputs do not establish a usable private
   directory. No root service, guessed UID, broad chmod or SELinux relaxation
   was used. Close the exact native ownership mechanism before live assignment.
2. `serviceArtifactSha256` is the selected ARM64 OCI manifest digest, not the
   bundle, OCI index, layer or executable digest. The audited Cloud service
   version schema does not explicitly provide that value before assignment.
   Inspect the actual published artifact/response through a supported path;
   if it cannot supply the authoritative value, resolve this bounded ordering
   contract before implementing a fallback.

Details and pinned source evidence are recorded with the
[temporary service-input contract](../architecture/demo-control-service-inputs.md).
No new service identity, Subject binding or service publication was applied.

## Tire limits that must not be guessed

The accepted raw-to-normalized wheel-dispersion definition and slip-persistence
comparison boundary are not closed by the current source contracts. Tire
explicitly reports `MODEL_CONTRACT_UNRESOLVED` instead of inventing a result.
CPU-load-control wire/lease behavior, the complete recovery/overflow matrix,
live calibration, quotas and offline E2E remain unqualified. Existing fixture
success is not a complete P7 claim.

## Verification and preserved live state

- Demo Control: 500 tests passed in 77 seconds. Added publication-history and
  CLI-capability regressions subsequently passed in the focused 12-test suite.
- Presenter: 94 unit tests and production build passed. Browser tests cover
  exact profile receipts, registration continuation, Quick image reuse,
  zero-DMIPS monitoring, navigation, stale Cloud observations and protected
  prepare/sign/upload order. All three Studio cases pass after the preparation
  selector's accessible name was made explicit; the Cloud-observer case also
  passes. Browser fixtures do not operate real VMs/Cloud.
- Backend/retirement: the scoped Tire product and legacy cleanup fixtures pass,
  including nonmatching preservation and invalid/uncertain outcomes.
- Owning repository checks: Platform 47 tests, Brake four CTest targets,
  Tire native scoped tests and backend 11-test suite passed. These remain
  narrower than full functional/runtime/security qualification.

The last Cloud read at **01:04 UTC on 11 September** reports the same Test Unit
`2a29c145-bbd1-4494-a0e5-d4b79e6a9db5` Online with VDP **18.0.0 installed**,
no pending component and no services. The preceding independent guest evidence
in the 10 September checkpoint proves VDP18 running with 23 read paths; this
later Cloud observation is not a fresh process observation.

Factory `.31` and the Production peer are unchanged. The earlier qualified SM
override under `/run/democtl-sm-queued-recovery` remains intentionally retained;
a VM reboot removes it. Builder was not started. No Factory image, overlay,
Cloud release or historical source was deleted. Final destructive housekeeping
is deferred until the required complete successor passes.

Next: close the exact P5 native ownership and artifact-identity gates, complete
SOTA tooling and one real Brake chain, then the dependent advisory/Tire work.
Do not claim a morning-ready complete demo from these source checkpoints.

## Final source checkpoint and live UI read

Solution implementation commit `648082b88b58ed5df9b5a0a12f6d9aacf2cde485`
was pushed to `codex/demo-studio-implementation`. It includes source, English
documentation, tests and approved design assets, not compiled artifacts or
runtime/credential data. The documentation and confidential-input gates passed.
The pre-implementation return point remains unchanged.

The UI-only restart exposed the documented relative terminal invocation
`.venv/bin/democtl ui serve`. The stop guard now verifies the process's exact
canonical working directory before accepting this relative form. Four focused
tests cover it, a foreign directory/user, a busy session and the absolute form;
the nine-test stop/Cloud-reader suite passed. No broad process matching or
port-only signal was introduced.

The updated server started and `workspace restore` placed the owned windows;
VM, Cloud, CARLA and driving state were not restarted. The live page then
reported Test Online, VDP18 installed, three named components and empty service
inventory. At **01:34:58 UTC** its Cloud-only monitor returned a CPU sample of
**684 DMIPS** dated **01:34:18 UTC**. Memory/traffic retained their raw values
with units explicitly unverified; disk remained Not reported. A functioning
resource read is demonstrated, not complete metric-unit or product readiness.

## Source-publication correction and next P5 increment

The canonical Tire source is now public under `alexmaninblack`, with unchanged
source history and the same `cb1bfca...` commit. Local `origin` follows that
repository. The user requested leaving the earlier AlexAgizim copy untouched;
no transfer or deletion was performed.

The existing SP profile was re-read through Demo Control and has usable
catalog/version access. The previously accepted temporary use of this SP for
distinct Brake/Tire identities remains authorized; it is not another open
permission question. No new service, SP, Subject or assignment was created.

P5 gained the explicit engineering-only `service inspect SERVICE_UUID
VERSION_UUID --profile PROFILE` command. It checks parent ownership and exact
version binding, exposes only bounded fields and metadata field names/types,
and never claims manifest verification. The 23 focused service tests pass;
its real existing-version read completed in under one second. It is not a
Presenter capability and does not add polling, retries or guest access.

The token-owner source correction and nine focused Platform tests are recorded
in the [service-input contract](../architecture/demo-control-service-inputs.md).
The native SM patch applies to its pinned source, but has not been built into
a complete SM binary or installed. The metadata source/order remains the
specific integration decision in that document; P5 is still incomplete.
No VM, SM, CARLA, backend, Factory image, Cloud release or Production state was
modified during this increment.

## Accepted native-input migration: documentation and private sessions

The user approved [ADR 0015](../architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
and authorized the documentation cascade and implementation. The earlier
token-owner SM candidate and final-manifest-before-assignment design above
are historical, not the current target.

- HLA 1.6, flows/system/interface register 2.1 and affected component packages
  now link the accepted replacement. Unaffected packages changed input metadata
  only. Input schemas freeze package release, five-field public metadata and
  private credential placement. Product wire migration is explicitly N3.
- Brake `8d19381` and Tire `47ab08d` implement private 0700 sessions in
  native per-container 1777 tmpfs, dynamic path-only token delivery, secure
  parent/leaf reads, atomic renewal, own-session cleanup and bounded orphans.
- Platform `205f89d` removes the unshipped token-owner patch, header, recipe
  wiring and old tests, and changes only the token mount root mode. These
  deleted source files remain recoverable from Git. Other SM fixes stay intact.
- Brake 5/5 and Tire 2/2 host CTest targets pass; both bootstraps compile.
  Platform 8 resource tests and its repository gate pass. Solution 36
  input/KAC/document-checker tests and docs-check pass. The stale-version
  checker test now changes the actual metadata rather than hardcoding HLA 1.5.
- These are local source commits, not pushes or release publications.
  No ARM64/gRPC rebuild, VM/SM restart, Cloud/Subject/service mutation,
  backend change, Factory rebuild or Production action was performed.

Next is the coordinated package/provenance and backend migration, including
the modelArtifactSha256 alias, explicit legacy decoding and unchanged retained
state. Then implement public-input projection/boot ordering and perform the
bounded Test integration through Demo Control. Do not publish this intermediate
runtime or claim full P5/P7 readiness from host token tests.

## N3 consumer compatibility checkpoint

The next authorized increment continues P5/P7 and ADR 0015. Product revision
2 / 2.0.0 is frozen separately from retained legacy revision 1. Nine schemas
and corresponding fixtures use the package release and native service,
Subject, index and runtime-instance identity without service/model OCI digest
fields. Model configuration, VDP hashes, content payloads, receipt keys and
authorization are unchanged. The accepted package/public/environment readers
and actual service producers have **not yet migrated** to this revision.

Brake consumer source supports both revisions, removes the functional-profile
restriction from native package releases, and correlates native instances
exactly. New migration 003 updates only typed projections and retains all
legacy columns/values, canonical messages and original receipts. Unknown
legacy schema is rejected before a table rebuild, and an injected mid-migration
failure rolls back to intact database schema 2. The final migration includes
every legacy digest column; the populated-database test caught and corrected
an initial copy-column omission before any live use.

Tire uses separate packaged old/new validators. Its canonical envelope store
requires no database migration. Both backends return explicit revision-2
query envelopes and retain the actual revision on every stored message;
ACK/admin/error/SSE contracts stay unchanged. Existing Demo Control empty-store
validation accepts Brake database 2/3 and Tire 2 only. No cleanup, deployment
or runtime operation was executed to test this adapter.

Completed local evidence:

- Brake TypeScript backend compilation and full typecheck passed; 44 backend
  tests passed, including native HTTP ingestion/query, invalid identity/release,
  legacy strict decoding, exact duplicates, mixed-instance conflicts,
  cross-instance event/assessment joins and populated migration/rollback.
- Brake source/licensing/dependency/artifact quality gate passed.
- Tire 13 backend tests passed, including both wire revisions, unchanged
  history/receipts across database reopen, conflicts, scoped cleanup and HTTP.
- Solution 4 new schema-invariant and 4 existing runtime-input tests passed.
  Documentation checks passed (170 Markdown files, 658 stable identifiers,
  38 Mermaid diagrams). The existing Demo Control
  retirement suites passed: 29 Brake-suite and 36 Tire-suite test executions
  (the latter also imports the shared Brake fixture suite).
- Tests use temporary SQLite files/in-memory databases and loopback test
  sockets. Initial sandbox socket/write denials were harness restrictions;
  reviewed local test execution passed. No checks ran against the demo database.

Remaining: migrate the two service input readers and serializers, bind real
query/readiness/evidence consumers, complete N4 package/public projection and
N5 boot ordering, then N6 current-Test SOTA evidence through Demo Control.
The accepted Brake window-detail contract has no handler on the active backend
branch; the v2 schema does not close that P7 endpoint gap. Tire model/CPU-worker
work remains separate. No Factory build, VM/SM restart, Cloud publication,
Subject/assignment change or Production mutation occurred. No E2E completion
or actual product data is claimed by these synthetic fixtures.

Local source checkpoints: Brake Cloud `d7626b7`, Tire Cloud `b383c02`.
The Solution checkpoint containing this section freezes the contract snapshots,
adapter compatibility and execution position. Nothing was pushed or published
in this increment; the repositories remain on their existing `codex/` branches.

## N3 producer and native-reader source checkpoint

Both Brake and Tire now read the immutable package release and four native
Aos identity variables at startup, independently of the five-field public
Unit/VDP input. New public readers reject legacy metadata and all identity/
version overrides. The existing private token-session boundary is unchanged.

All nine product message kinds emit revision 2 / 2.0.0 with a complete native
`serviceInstance`, and no service/model OCI artifact fields. Content payloads,
hashes, idempotency keys, QM request/status and ACK schemas remain unchanged.
Retained legacy queues and journal recovery keep exact old bytes and provenance.

Brake's persisted advisory binding supports both revisions. Tire saves the
original request metadata in its existing private state wrapper; the actual
model state, producer epoch and sequence rules do not change. An old unbound
request is retained but cannot generate a newly misattributed fact. Normal
refresh creates a bound request using the retained epoch and next sequence.
No old-binary rollback compatibility for the extended wrapper is claimed.

Local evidence:

- Brake: all six CTest targets passed, including new closed-input tests,
  native product/restart/journal tests and legacy-to-native recovery.
- Tire: all three CTest targets passed, including separate-input negatives,
  native/legacy queues, retained request provenance, unbound legacy recovery
  and monotonic advisory sequence checks.
- Actual C++ producers emitted five Brake and four Tire message kinds.
  Both matching backend implementations accepted and stored them in memory;
  exact retries retained their receipts, and queries exposed revision 2.
  These are real serializers with synthetic inputs, not live vehicle records.
- Brake product-export validation now requires all six CTest suites rather
  than the stale four-suite list. A missing/failed/skipped suite still blocks
  export; no package was built in this increment.

This closes the N3 producer/input **source** gate. N4 Demo Control package
assembly/public projection, N5 boot ordering and N6 actual Test integration
are next. The gRPC main call sites are migrated, but this host build excludes
the pinned gRPC/ARM64 target. No package signing/upload, service assignment,
backend activation, VM/SM restart, Factory build or Production change occurred.
Team dashboards, Brake detail handler and Tire model/load-worker gaps remain
as previously recorded. Existing local branches are retained.

Source checkpoints: Brake `bc0ed65`, Tire `a0c58b8`; local only, not pushed.
The four focused Brake export tests and repository quality gate also passed.
Solution docs-check passed with 170 Markdown documents, 658 stable identifiers
and 38 Mermaid diagrams. The Solution commit containing this record preserves
the exact source-gate position; it does not mark the full migration complete.

## N4 service package preparation source increment

Demo Control now owns `service prepare <team> --profile <content>`. It reads
the existing real product export without invoking Docker or requiring a Unit.
Brake supports its existing v1/v2/v3 exports; Tire still has no real build
adapter and fails explicitly rather than packaging a scaffold.

The authenticated SP worker reads only the owned catalog and matching service
versions. No manifest or Unit inventory is needed. Complete absence of the
codename and read failure remain distinct. All published version states feed
the existing continuity ledger; the package and publication metadata receive
one allocated value. Version bounds now match the native readers (32-character
strict SemVer). A failed preparation consumes its number without committing
partial output. An explicit subsequent preparation preserves the prior package.

Prepared packages contain the two verified ARM64 executables, exported public
licenses and immutable release metadata. Public Unit/VDP/trust input is not
packaged, and native Aos identity remains runtime supplied. Source configuration
requests minInstances 1, offlineTTL P7D, accepted quotas and exact team-scoped
resources/KUKSA permissions. Outbound rules name only the fixed KUKSA and own
backend endpoints; schema acceptance does not prove native routing/enforcement.

Evidence: 38 focused service build/catalog/package tests, six CLI tests and four release
continuity tests passed. Four configurations were checked using the installed
official Aos signer in temporary directories, through the same private adapter
used by Demo Control; no signing credential was read. Fixture ARM64 bytes are
used only for package tests and are not a real product build or published
artifact. Tests cover version equality, same-content repeat, failure retention,
no-vehicle preparation, changed executables, links/unexpected files, complete
catalog coverage, caller umask, catalog redirection and no browser publication
authority. Documentation quality checks passed (170 Markdown documents,
658 stable identifiers, 38 Mermaid diagrams).

Remaining N4: real Tire build adapter, handle-based signing/publication,
public-input projection and native resource activation. N5 existing cold-start
hook/order remains unimplemented. N6 must still prove the actual container
loader/glibc boundary, mounted inputs, native identity/KAC/TLS/permissions,
backend ingestion and retained assignment recovery. No actual product package
was prepared, signed or published during this source increment; no Cloud,
VM, backend, SM, Factory or Production state was changed.

## N4 signing/publication source increment

The next increment implements `service sign <handle>`, `service upload <handle>`
and `service cloud-status <handle>` behind the common application boundary.
Prepared metadata binds team, SP and release; these commands cannot change
those selectors, allocate another release, build or assign a service.

The official signer signs an isolated exact copy. RS256 verification and
byte-for-byte signed/prepared payload comparison precede the output receipt.
Repeat and interrupted-receipt recovery verify the existing signed output
instead of resigning. Package path/content/mode and native-version invariants
are checked at signing/publication, not repeated during Cloud-only status.

The shared fixed multipart upload route is unchanged for FOTA. SOTA uses the
bound SP and one session containing preflight plus one POST. A prepared
release must be unused/newer; assignments to any Unit other than the current
owned Test block. Empty assignments permit publication before a vehicle
exists. No OEM permissions, Unit Set/Subject mutation, approve/send, runtime
restart or fixed delay is introduced.

`201` is recorded as ACCEPTED immediately. Explicit status requires the exact
recorded bundle ID, correct service/codename/version and ready catalog entry
before READY. Missing/processing/error/unknown remain distinct. A lost upload
response remains UNCERTAIN; no speculative bundle adoption or repeat POST.
An explicit preflight failure is distinguishable from an attempted upload.
The existing artifact directory retains the intent and sanitized receipt;
no token, certificate content or new Unit authority is stored there.

Evidence: 55 focused service tests (including real official signing with an
ephemeral self-signed fixture key), 24 existing FOTA-publication tests,
eight existing component-package tests, six CLI tests and four continuity
tests passed. The public v11 OpenAPI was read to verify the upload response,
bundle-list fields and service-version fields. Native account authentication
is stubbed only in the offline signature test; no real Cloud key or endpoint
was used by these tests. HTTP transport tests use an in-memory opener.

No live product was built, signed, uploaded, assigned or started. The current
VM/SM override, Factory, Production and backend data remain unchanged. Actual
Tire building, native public-input projection/activation, N5 boot restoration
and N6 backend/service integration remain pending. This is a local source
checkpoint, not an E2E or UI-completion claim.
