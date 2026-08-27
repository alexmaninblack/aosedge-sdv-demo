<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service Tenant Quota Proof — Design Reviewed

- Decision: `D4-023`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.0.0`
- Accepted subdecisions: D4-023.1 metadata/authority, D4-023.2 exact requested
  envelopes/native mapping design, D4-023.3 fixed Tire CPU-load control and
  D4-023.4 authoritative evidence split, D4-023.5 sample-driven verdict and
  D4-023.6 qualification matrix, 2026-08-23

Each Function Team requests its Service quotas in the SOTA candidate's
`configuration.quotas` metadata. OEM approval confirms the exact Service
version/digest and requested metadata after the required validation evidence.
AosCore/Service Manager is the sole in-vehicle enforcement authority. The
Software Delivery Dashboard and Demo Orchestrator only present evidence and
must never set, override, emulate or enforce the quotas. No project resource
manager is permitted.

The current `aos-signer` 2.0.1 input field family is `cpuLimit`, `ramLimit`,
`storageLimit`, `stateLimit`, `tmpLimit`, `noFileLimit` and `pidsLimit`.
`cpuLimit` is DMIPS and becomes native `cpuDmipsLimit`; size fields normalize
to bytes. It is never labelled as CPU percent. The signed native config and
the resulting OCI/cgroup/resource mounts must be inspected after deployment;
an unsupported or unobserved field is not presented as enforced.

The accepted requested envelopes are:

| Quota | Brake Health | Tire Health |
| --- | ---: | ---: |
| CPU | 250 DMIPS | 150 DMIPS |
| RAM | 16 MiB | 16 MiB |
| Storage | 8 MiB | 4 MiB |
| State | 1 MiB | 2 MiB |
| Temporary storage | 8 MiB | 2 MiB |
| Open files | 64 | 32 |
| PIDs | 16 | 8 |

Tire storage owns its persistent outbox/supporting database metadata, state
owns the versioned estimator state and tmp owns temporary computation only.
No network quota is requested. Insufficient implementation headroom requires
a reviewed, measured envelope change; silent inflation is forbidden.

The first audience proof intentionally saturates only CPU inside the actual
Tire Health Service instance while Brake Health is the unaffected control
tenant. Other approved metadata remains visible but memory, storage, file and
PID exhaustion are not first-demo claims.

The Tire Function Dashboard exposes one `Start CPU Isolation Proof` action.
It asks the Mac-local Tire backend for one fixed, identity-bound command; the
actual Tire Service obtains it through its existing service-initiated outbound
backend route. The command is bound to the exact current `system_uid`, Tire
Service version and artifact digest, and fixed
`TIRE_CPU_ISOLATION_PROOF_V1` profile. Only idempotent start and stop are
supported. The caller cannot supply shell text, worker count, intensity or
duration.

The prepared worker executes inside the real Tire Service process boundary
and the same Aos-managed cgroup. It is not another Service, load container,
resource manager or administrative side channel. At most one worker exists;
a duplicate start returns its current state. A bounded renewable lease stops
the load if the Dashboard/backend path is lost, and an unconditional 180-second
ceiling prevents an orphan load. Service or VM restart always returns the
control to `INACTIVE` without persistence or automatic resume. The action is
disabled while the selected vehicle has no external connectivity.

`INACTIVE`, `STARTING`, `ACTIVE`, `STOPPING`, `AUTO_STOPPED` and `FAILED` are
Function Team control states only. They do not prove quota enforcement. That
claim requires the authoritative evidence below.

The audience view obtains the approved quota, current exact Tire instance,
per-instance CPU usage in DMIPS, source time/freshness and instance state from
fresh AosCloud reads. It uses the current Unit monitoring, monitoring-dashboard
and alerts API surfaces. An instance-quota alert is supplementary: correct
throttling may prevent an over-quota alert, so absence of that alert is not a
failure and its presence alone is not success.

The current public Cloud surface does not expose raw `cpu.max` or `cpu.stat`
throttling counters. Final technical acceptance therefore also requires one
sanitized read-only qualification record proving the exact Tire-instance
cgroup binding, its v2 CPU cap, an increase in throttle counters under load and
no instance restart/replacement. That record is bound to the Factory Image,
AosCore release, Tire artifact, signed Service configuration and Node DMIPS
capacity. It need not be recollected during every audience demonstration, but
any bound-baseline change makes it stale.

Cloud facts and qualification evidence remain visibly distinct. Missing,
stale, ambiguous or identity-mismatched evidence produces `UNKNOWN` and blocks
`PASS`. Tire Service/backend control status is never enforcement evidence.
D4-023.5 makes the proof sample-driven rather than a wall-clock performance
test. It requires three consecutive fresh Cloud samples for pre-load baseline,
saturation and post-stop recovery. Freshness, saturation/recovery DMIPS bands
and cgroup mapping tolerance are measured once during live characterization
and frozen in a profile bound to the exact Factory Image, AosCore release,
Tire artifact/configuration and Node DMIPS capacity. No arbitrary percentage
tolerance is accepted.

`PASS` requires the exact Tire instance and 150-DMIPS approval, three samples
in the qualified saturation band, bound cgroup cap/throttle evidence, no Tire
restart/replacement, one completed deterministic Brake event with Brake and
the platform graph healthy, and three post-stop recovery samples without
reinstall/restart. Brake uses the existing scenario completion timeout; no new
latency KPI is introduced.

A cap/mapping violation, restart, peer/platform degradation or failed recovery
is `FAIL`. Missing/stale samples, ambiguous identity, incomplete evidence or an
early lease/ceiling auto-stop is `INCONCLUSIVE`. Offline Unit, wrong/unknown
Tire version or stale/missing qualification profile is `NOT_READY`. A quota
alert never determines the verdict by itself.

Qualification begins with static signer/configuration, no-quota-mutation,
fixed-command negative and verdict-state tests. The Validation Unit then runs
three complete characterization cycles; each contains three baseline samples,
fixed Tire load, three saturation samples, cgroup cap/throttle evidence, one
concurrent deterministic Brake event, stop and three recovery samples. The
resulting freshness/bands/tolerance profile is frozen before qualification.

Two further independent Validation Unit cycles must both pass without profile
adjustment. A `FAIL` blocks qualification and `INCONCLUSIVE` is never counted
as success. Live VU fault cases cover duplicate commands, lease loss, the
180-second ceiling, Service/VM restart, stale monitoring, identity/profile
mismatch and an externally offline Unit. One Production Unit rehearsal must
then pass with the same signed Tire artifact and frozen profile.

Exactly one sanitized qualification dossier is retained. It binds baseline
digests and Node DMIPS to approved quotas, normalized Cloud samples/timestamps,
cgroup cap/counters, Tire continuity, Brake correlation, shared-platform health
and per-cycle/overall verdicts. It contains no credential, private key, full
private Cloud identifier, raw vehicle telemetry or ordinary demo-run history.

Factory Image, AosCore, runtime/cgroup mapping, Tire artifact/load worker,
signed quota/configuration, Node DMIPS or monitoring API/cadence change requires
requalification. Fresh provisioning identity alone does not invalidate the
technical profile when every bound baseline remains identical.

The design is closed. Implementation and live qualification remain required;
this contract authorizes no Service build, publication, Cloud mutation, VM
change or resource-load execution.
