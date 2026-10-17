<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Platform FOTA Safe Stop Contract

Implementation and qualification: [protocol status](../implementation-status.md).

- Architecture decision: [ADR 0014](../../docs/architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Contract version: 1.1.1
- Lifecycle state: accepted policy; implemented scoped FOTA proof follows the current baseline

This contract fixes the Safe Stop evidence, policy, lifecycle gate and recovery
behavior used by the factory-installed OEM Component Runtime before applying a
Vehicle Data Platform Component FOTA.

It consumes the read-only control-state projection already defined by the
[Simulator Control and Context Contract](../simulator-control-context/simulator-control-context.v1.json).
It does not make AosCloud, the Demo UI, KUKSA or the VDP being updated a source
of physical-motion authority.

- [JSON Schema](platform-fota-safe-stop-profile.schema.json)
- [Accepted profile 1.1.1](platform-fota-safe-stop-profile.v1.json)

The runtime uses a purpose-bound per-Unit `PLATFORM_UPDATE_RUNTIME` mTLS
identity, distinct from the VDP's selected-Unit identity. A transport-only
VISS adapter implements `VehicleStateProviderItf`; the Safe Stop evaluator
remains a pure policy component. `FrameId` is part of every accepted snapshot,
so the twelve-sample window requires twelve distinct monotonic CARLA frames
rather than repeated reads of one cached state.

The six controller/reset paths are a single frame-coherent Gateway fact group
under the
[Simulator Control and Context Contract](../simulator-control-context/simulator-control-context.v1.json).
If the local controller record cannot be joined to the physical snapshot by
exact frame ID and simulation time, the whole group is absent. Such a snapshot
is incomplete and therefore follows the profile's existing
`missingOrContradictoryEvidence = NOT_SAFE` rule. The local 250-ms join bound is
not the OEM Runtime's Safe Stop freshness limit and cannot authorize an update.

Version 1.1.1 clarifies the accepted freshness semantics. Every admitted
sample must carry source time and be no older than 250 ms when it is acquired.
The twelve-sample history proves only consecutive stability; it is not reused
as current vehicle state. The newest complete sample must again be no older
than 250 ms when the gate opens and immediately before every destructive
runtime operation. This deliberately permits a twelve-sample window to span
more than 250 ms while preventing buffered history from authorizing a current
transition.

Waiting uses a single bounded runtime worker. The durable
record contains transaction metadata, never Safe Stop samples; the runtime
does not hold its main mutex while waiting, and shutdown performs bounded
cancel-and-join. The current healthy VDP remains active during replacement or
removal waiting, while first install exposes no active capability.

<a id="native-stop-completion"></a>

<a id="native-stop-completion-correction--accepted-2026-09-06"></a>
### Native stop-completion boundary

The operator approved correcting the mismatch with the pinned AosCore launch
pool: `StopInstance` must not return success until the provider is actually
stopped. It waits for its worker without holding the runtime's main mutex and
returns `Inactive` only after durable stop completion. Cancellation or failure
returns an error, never a successful asynchronous stop. The completion bound
is 590 seconds plus the existing two-second cancellation bound, below CM's
600-second node-status timeout; successful completion returns immediately,
not after that limit. The Safe Stop collection deadline remains 480 seconds.

`StartInstance` retains its asynchronous `Activating` contract. A completed
stop retains a private `stopped.json` predecessor record and its existing A/B
slot for version checks and rollback. It is not an active installation and is
not automatically started by reboot. A subsequent candidate uses the other
slot; successful replacement clears the stopped record, while failed
replacement restores the predecessor. No Safe Stop evidence is persisted.
This supersedes the earlier implication that StopInstance could return while
its remove worker was still active. No upstream launcher fork is introduced.

While Safe Stop is not yet established, AosCore's native lifecycle state is
`ACTIVATING`. A first install leaves the empty VDP slot empty; a replacement
keeps the previous healthy release active; a removal keeps the current healthy
release active. The audience phrase `Waiting for Safe Stop before application`
is a bounded Representation Layer interpretation of that native state plus a
fresh Gateway `Safe Stop not established` fact. It is not a native AosCloud or
AosCore state. Native runtime reason codes remain available through explicit
on-demand Aos log requests.

The profile is specific to the first demonstration qualification. A production
vehicle may use a different Vehicle State Manager and different homologated
thresholds behind the same runtime-owned policy boundary.

## Effective timing profiles

| Vehicle role | Source-age interval at acquisition and each destructive gate | Read deadline |
| --- | --- | --- |
| Standard / Production role / missing role | 0 through 250 ms; future values rejected | 250 ms |
| Explicit Test role, `demo-5s` | -5000 through +5000 ms, inclusive | 1000 ms maximum, not a fixed wait |

<a id="local-test-timing-2026-09-10"></a>
The Test allowance handles the single-Mac demonstration's clock skew and
delayed data; it is not compliance with the unchanged standard profile or
proof of synchronization/real-time behavior. Cloud environment does not select
this policy: a Test on Production Cloud is still the vehicle Test role.
The immutable bootstrap field and standard signed profile remain 250 ms.
Only the explicit persistent role selects the effective demo allowance;
unknown profile values are rejected.

Both profiles require twelve distinct coherent advancing frames, actual
SAFE_STOP/STABLE, physical thresholds, generation/reset checks, strict transport
identity, cancellation and transaction deadlines. Every destructive operation
revalidates fresh evidence; no cached frame or durable sample creates authority.
The earlier temporary `.29`/`.31` probes and asymmetric exception are Git
history, not another active timing profile.

<a id="queued-cold-boot-recovery-correction--accepted-2026-09-10"></a>
## Queued cold-boot recovery boundary

For a waiting transaction with a validated committed predecessor, recovery
checks provider health and, when inactive, starts and rechecks that provider
before resuming the wait. A start or health-recheck failure preserves the valid
active selector and durable waiting intent. This applies to queued replacement
and removal, matching the existing ordinary-installed recovery behavior.
The intentionally stopped predecessor and empty first-install branches are
unchanged; all resumed destructive steps reconstruct fresh Safe Stop evidence.

The runtime never invents a missing active selector. Recovery failure retains
diagnostic/transaction state for exact reconciliation; a one-off historical
selector repair is not a normal boot or installation instruction.

## Durable local-demo input integration

The Factory opts into `demoLocalSourceInputs`; without it the native credential
paths and default profile are unchanged. Public CA, source binding, selected
VDP source and a fixed `test`/`production` role live under the existing runtime
data directory's `demo-inputs`. No private credential or vehicle sample is
stored there. The image contains no live input or role. Missing role selects
`standard`; only explicit `test` selects `demo-5s`. Production remains standard.

Demo Control writes these public inputs during source configuration. The first
role assignment restarts SM once so its initialization reads the role. Later
source generations update the binding without another role restart. Packaged
VDP `LoadCredential` entries read the public input files from persistent data.
Reboot retains configuration, not authorization from old Safe Stop samples:
every destructive operation still requires fresh live evidence. The existing
source-selection operation owns reconnecting the local CARLA transport.
The [current baseline](../../docs/qualification/current-baseline.md) maps the
selected image to scoped FOTA/ignition proof and the remaining negative matrix.
