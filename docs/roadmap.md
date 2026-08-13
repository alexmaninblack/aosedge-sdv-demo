# Roadmap

The milestones deliberately separate host virtualization, AosCloud lifecycle
management, vehicle-data transport, and AOS-native data abstraction. A failure
in one layer must not be hidden by work in another layer.

## AOS-0 — Boot the official ARM64 AosVM image on Apple Silicon

- Download and verify the pinned official AosVM `qemuarm64` release.
- Boot the complete Main Node system through a disposable qcow2 overlay,
  including the official EFI, guest kernel, initramfs, and root filesystem.
- Use QEMU system virtualization with Apple Hypervisor Framework acceleration.
- Establish serial console and loopback-only SSH access.
- Functionally validate the guest kernel facilities required by AosCore.
- Run a cloud-free local OCI probe through the image's `crun` runtime.
- Validate AosCore components and classify the expected unprovisioned state.
- Verify outbound HTTPS, DNS, clean shutdown, and restart persistence.
- Record the exact host, QEMU, image, firmware, and network configuration.

Exit criterion: the pinned Main Node boots reproducibly on the M5 Pro, is
reachable only through explicitly configured local forwards, reaches the
Internet, passes the kernel and local OCI gates, and survives a clean stop/start
without modifying the downloaded base image.

Current gate: AOS-0 passes all 14 phases. Addressing, routing,
outbound TCP, guest-to-host access, DNS, synchronized time, verified HTTPS, and
loopback-only SSH all pass tracked host and guest gates. A tracked macOS DNS
bridge binds only to `127.0.0.1`; the overlay-only guest helper routes the
image's existing dnsmasq through it without administrator-owned networking or
LAN exposure. The upstream ARM64 EFI loader correction from Phase 10 remains
stable. The tracked lifecycle now qualifies host readiness; starts and owns the
VM; attaches to its serial console; reports exact process, listener, and disk
state; waits for SSH readiness in its smoke test; and shuts down through QMP
before any bounded escalation. Stale or unrelated PID state is rejected.
A marker on the guest's writable `/home` partition persisted across a clean
restart and disappeared after explicit overlay recreation. Every stopped-state
gate found no owned process, listener, or runtime residue and reverified the
exact Main Node, Secondary Node, and EFI hashes. The tracked ARM64 and DNS
compatibility changes were restored on the fresh overlay, remained idempotent,
and passed the Phase 10 and complete Phase 11 regressions. The final accepted
start/smoke/stop run passed, the VM is stopped, and the sanitized baseline and
go decision are recorded in the runbook.

Phase 9 also passes the complete cloud-free `crun` qualification.
The probe ran an isolated ARM64 PID 1 with enforced CPU, memory, and PID
limits, a read-only rootfs, writable tmpfs, isolated networking, and clean
teardown. Phase 8 passes all 13 required capabilities. SquashFS and loop
are intentionally packaged in the boot initramfs, where the rootfs update path
uses them before `switch_root`; they are not required in the steady-state
rootfs.

Detailed plan: [AOS-0 runbook](aos-0-arm64-vm.md).

## AOS-1 — Register and provision the Unit

- Use the AosEdge-provided SDK and CLI utilities for registration,
  provisioning, and certificate installation.
- Extend the owned QEMU/HVF lifecycle and private networking to the released
  Secondary Node image.
- Use the accepted official two-Node topology, with both VMs on the same Mac.
- Confirm that the Unit appears online in hosted AosCloud.
- Deploy and observe the official Hello World service.

Exit criterion: AosCloud reports the Unit online and an official sample service
reaches `Active` state after a cloud-driven deployment.

No repository-managed script will reimplement the SDK provisioning protocol.

## AOS-2 — Connect the VM to the CARLA VISS endpoint

- Provide a host-only route from the guest to the macOS VISS endpoint.
- Preserve TLS verification and install only the required public trust anchor
  in the service package or its declared resource.
- Keep VISS unavailable from the external LAN and Internet.
- Verify VISS 3.1 `get`, `subscribe`, reconnect, and shutdown behavior from an
  ordinary process in the guest before containerizing the client.

Exit criterion: a guest-side probe continuously receives live CARLA speed,
acceleration, steering, throttle, and brake values over a verified TLS
connection.

## AOS-3 — Deploy the first telemetry consumer

- Package an ARM64 OCI service with explicit CPU, RAM, storage, and network
  limits.
- Subscribe directly to the CARLA VISS 3.1 endpoint.
- Produce structured English logs and basic connection health.
- Deploy, update, stop, and restart the service from AosCloud.

Exit criterion: the cloud-managed service receives live vehicle telemetry and
its state and logs are visible through AosCloud.

## AOS-4 — Add useful edge processing

- Calculate trip statistics and bounded driving events such as hard braking,
  hard acceleration, and steering activity.
- Persist only explicitly selected state across service updates.
- Define whether processed results remain local, appear in logs/alerts, or are
  sent to a separate backend.

Exit criterion: the service demonstrates a useful transformation of live
vehicle data and preserves its declared state across an update.

## AOS-5 — Evaluate and, if justified, add AOS VIS integration

- Pin the exact AOS VIS protocol and signal-tree version.
- Define a reviewed mapping from VSS 6.0/VISS 3.1 paths to the older
  `Signal.*` and `Attribute.*` AOS VIS namespace.
- Implement either a dedicated adapter or a narrowly scoped bridge.
- Apply AosEdge IAM service permissions to vehicle-data access.

Exit criterion: a second cloud-managed service consumes mapped vehicle data
through AOS VIS without knowing that CARLA is the original source.

This milestone is intentionally after the direct VISS consumer; it must solve a
concrete isolation or compatibility requirement rather than add an unnecessary
translation layer.

## Deferred decisions

- Self-hosted AosCloud versus the hosted platform.
- Additional AosVM Nodes beyond the accepted Main + Secondary provisioning
  topology.
- Cameras, LiDAR, radar, and ultrasonic data.
- ROS 2 integration.
- Upstream contributions to `AosEdge/meta-aos-vm` or `AosEdge/aos_vis`.
