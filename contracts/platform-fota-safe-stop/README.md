<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Platform FOTA Safe Stop Contract

- Architecture decision: [ADR 0014](../../docs/architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Contract version: 1.1.1
- Lifecycle state: design accepted; implementation and live qualification are open

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

Waiting is a single asynchronous bounded runtime transaction. The durable
record contains transaction metadata, never Safe Stop samples; the runtime
does not hold its main mutex while waiting, and shutdown performs bounded
cancel-and-join. The current healthy VDP remains active during replacement or
removal waiting, while first install exposes no active capability.

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

## Local Test clock-age exception — 2026-09-06

The operator explicitly authorized `safeStopFreshnessProfile: "demo-5s"` in
the Test .29 SM bootstrap runtime configuration to continue the local CARLA
demo despite approximately 2.016 seconds of Mac/VM clock skew. This is a
separate demonstration exception, not compliance with the unchanged 1.1.1
250-ms profile. It admits up to 5000 ms source age both at acquisition and
at each destructive gate, including genuinely delayed data within that bound.
It is not a symmetric clock-skew allowance: future timestamps remain rejected.

Omitting the setting retains `standard` (250 ms); other values are rejected.
The twelve distinct advancing frames, mode/transition, motion/brake/throttle,
generation/reset, completeness, transport identity, bounded waits and rollback
conditions are unchanged. Production and signed VDP profile hashes are not
modified. The initial proof uses a temporary Test-only SM binary/config mount;
it does not qualify or alter the immutable Factory .29 image. The independent
asynchronous StopInstance/StartInstance transaction race remains open.
