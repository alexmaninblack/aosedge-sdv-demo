<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vehicle Hardware Capability Profile

This directory owns the cross-repository contract between the CARLA Vehicle
Simulation and the Vehicle Gateway. It does not define the narrower VSS/VISS or
KUKSA service contract.

- [`vehicle-hardware-capability-profile.v1.json`](vehicle-hardware-capability-profile.v1.json)
  is the accepted D4-002 profile for the selected virtual vehicle.
- [`vehicle-hardware-capability-profile.schema.json`](vehicle-hardware-capability-profile.schema.json)
  defines the stable version 1 shape.

The profile pins the selected CARLA source and ego blueprint, distinguishes
installed native or derived capabilities from optional CARLA facilities, and
allocates every capability to one explicit Gateway disposition. It also keeps
qualification-only simulator truth and demo-only visualization outside the
production vehicle-data interface.

The profile file is addressed externally by its SHA-256 digest; it does not
contain its own digest. This avoids a recursive self-digest. A release or
qualification record shall calculate the digest from the exact checked-in
bytes and shall bind that value to the Gateway coverage report.

The accepted static profile describes expected configuration. A qualified
Gateway startup must additionally reconcile the live CARLA revision,
blueprint, installed sensors and adapter coverage. A mismatch invalidates the
run; it is not converted into an apparently healthy profile.

Scenario/map calibration belongs to D4-003, drive-mode behavior belongs to
D4-004, exact VSS/VISS paths and freshness belong to D4-006, and typed
advisories belong to D4-008.
