<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Platform FOTA Safe Stop Contract

- Architecture decision: [ADR 0014](../../docs/architecture/decisions/0014-enforce-platform-fota-safe-stop-in-oem-component-runtime.md)
- Contract version: 1.0.1
- Lifecycle state: design accepted; implementation and live qualification are open

This contract fixes the Safe Stop evidence, policy, lifecycle gate and recovery
behavior used by the factory-installed OEM Component Runtime before applying a
Vehicle Data Platform Component FOTA.

It consumes the read-only control-state projection already defined by the
[Simulator Control and Context Contract](../simulator-control-context/simulator-control-context.v1.json).
It does not make AosCloud, the Demo UI, KUKSA or the VDP being updated a source
of physical-motion authority.

- [JSON Schema](platform-fota-safe-stop-profile.schema.json)
- [Accepted profile 1.0.1](platform-fota-safe-stop-profile.v1.json)

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
