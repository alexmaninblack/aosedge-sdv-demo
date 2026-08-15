<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Roadmap

The roadmap separates simulation, OEM platform/FOTA, Cloud service/SOTA, and
authorization lifecycles. A completed experiment is not a supported path; only
the current accepted baseline and the gates below remain active.

## Completed

### AOS-0 — Native Apple Silicon AosVM

The official AosVM 6.1.0 `qemuarm64` Main Node boots with QEMU system
virtualization and Apple Hypervisor Framework acceleration. Guest kernel,
storage, SELinux, OCI, networking, DNS mobility, clean shutdown, persistence,
and recovery gates pass.

### AOS-1 — One Persistent Main Node

The official SDK provisioned exactly one Main Node. Its identity persists on
the protected VM overlay, normal launches expose no provisioning listener, and
the official Hello World service completed install, log, removal, and restart
qualification.

### Repository Ownership Split

Platform, service, simulation, and integration code live in separate
repositories according to their release lifecycle. The versioned vehicle-data
contract belongs to `aos-vehicle-platform`; this repository pins and qualifies
the complete graph.

### AOS-2 — CARLA to KUKSA

The platform provider subscribes to the host-only CARLA VISS 3.1 endpoint and
publishes the seven accepted VSS signals to KUKSA. Live telemetry, stale and
source-loss behavior, TLS, credential isolation, restart continuity, and
Cloud-identity continuity pass.

### R6.1 Local Platform and Provider Qualification

The provider is now an independently versioned OEM FOTA component. Provider
`0.2.0` passed deterministic packaging, official unsigned validation, ARM64
lifecycle/recovery tests, live telemetry, rollback, SELinux, resource, and
secret-exclusion gates. Its accepted bytes were signed and independently
verified locally, but were not published or assigned.

The Service Manager component runtime, atomic A/B store, fixed `aos-vdp`
identity, systemd credential boundary, SELinux policy, DNS/TLS behavior, and
soft KUKSA dependency are integrated into rootfs candidate
`6.1.1-maninblack.11`. The candidate passed clean disposable boot and targeted
Enforcing qualification. Its rootfs-only unsigned FOTA output is frozen.

## Active R6.1 Gates

Each gate requires the previous result and a fresh explicit authorization for
any identity or Cloud mutation.

1. Reverify the frozen `.11` source, manifest, image, rootfs payload, and
   sanitized candidate metadata.
2. Sign only the accepted `.11` digest and independently verify the signed
   envelope. Signing does not unpack or mutate the already accepted payload.
3. Create or refresh a protected checkpoint of the validation Unit, then
   deploy `.11` only to that Unit.
4. Verify boot `6.1.0`, rootfs `.11`, the nested provider store, SELinux,
   Service Manager runtime, clean restart, and Cloud component reporting.
5. Publish and assign signed provider `0.2.0` only to the validation Unit.
6. Demonstrate CARLA telemetry through VISS, the provider, KUKSA, and the
   consumer; also prove source loss, recovery, restart, and provider rollback.
7. Decide separately whether to promote the accepted combination to the
   demonstration Unit. The validation-set scope defect must remain accounted
   for during every assignment decision.

Current stop point: `.11` is unsigned and local; the validation Unit remains on
`.2`, the demonstration Unit remains on `6.1.0`, and provider `0.2.0` remains
unpublished and unassigned.

## AOS-3 — First KUKSA Telemetry Service

Package the ARM64 telemetry consumer as an Aos SOTA service with explicit
resources and a compatible vehicle-data contract. Deploy, observe, update,
stop, restart, and roll it back through AosCloud without any CARLA dependency
inside the service.

Exit: a Cloud-managed service consumes live KUKSA telemetry and exposes useful
English health and data-age logs.

## AOS-4 — Useful Edge Processing

Add bounded trip statistics and driving-event detection, define exactly which
state persists across service updates, and prove update/rollback behavior.

## AOS-5 — Aos-to-KUKSA Authorization Adapter

Replace the temporary path-scoped KUKSA token fixture with a platform-owned
adapter that maps Aos service identity to short-lived least-privilege KUKSA
authorization. This is mandatory before third-party services, actuation, or
production credential handling.

## Optional AOS-6 — Legacy AOS VIS Compatibility

Add a legacy AOS VIS mapping only if a concrete compatibility requirement
justifies a second vehicle-data abstraction.

## Deferred

- production provider-store architecture and migration from the demo nested
  ext4 backend;
- Secondary or additional AosVM Nodes;
- cameras, LiDAR, radar, and ultrasonic data;
- ROS 2 integration;
- upstreaming CARLA, Unreal Engine, or AosEdge changes;
- self-hosted AosCloud.
