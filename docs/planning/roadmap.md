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

The deployment plan now separates public vehicle-integration material from
the provider executable. The separate OEM FOTA component is provisionally
named `vehicle-data-integration`; it owns the model-level provider endpoint
configuration, VISS trust anchor, and KUKSA public verifier. It never owns the
KUKSA provider token or another secret. Provider successor `0.2.1` will name a
compatible integration-component version through the Aos FOTA
`runtimeDependencies` manifest field.

Frozen rootfs `.11` and signed provider `0.2.0` remain accepted local evidence.
They are not modified, re-signed under the same versions, published, assigned,
or selected for the revised deployment. The next rootfs candidate is
provisionally `.12`; its final version is fixed only when its inputs and output
are frozen.

Each implementation gate requires the previous result. Signing, Cloud
publication, assignment, VM mutation, and promotion each require fresh
explicit authorization.

1. Review and accept the integration-component architecture, file ownership,
   secret boundary, version compatibility, activation ordering, health,
   rollback, and recovery contracts. This is the current gate and changes
   documentation only.
2. Implement and host-test a second, independently reported component runtime
   for `vehicle-data-integration`. It must use a separate A/B store, validate
   the complete public payload before activation, switch atomically, and
   coordinate KUKSA and provider readiness without containing a credential.
3. Build deterministic unsigned `vehicle-data-integration` `0.1.0` packaging
   with the model-level external provider configuration, VISS CA, and KUKSA
   public verifier. Unit-specific settings remain outside the shared FOTA
   artifact.
4. Produce provider successor `0.2.1` without changing the accepted application
   behavior, and add a signed `runtimeDependencies` constraint on the
   compatible integration component. Keep signed `0.2.0` immutable.
5. Run the complete host-side matrix for both component runtimes, archive
   validation, compatibility, dependency absence, concurrent desired state,
   activation ordering, failed update, interrupted update, rollback, recovery,
   expired or missing token, and secret exclusion. Resolve the full matrix
   before starting another Yocto build.
6. Incrementally build the next rootfs candidate from the preserved builder
   and caches. Qualify clean AArch64 boot, read-only root, SELinux Enforcing,
   both reported component types, independent stores, KUKSA verifier
   activation, provider credential isolation, and unchanged Unit identity.
7. Freeze and independently reverify the new rootfs, integration component,
   and provider candidates. Record exact source revisions, sizes, digests,
   manifests, and sanitized evidence.
8. After explicit approval, sign and independently verify only the accepted
   digests. Signing does not authorize Cloud upload or Unit mutation.
9. After separate approval, checkpoint the validation Unit, deploy the new
   rootfs only to that Unit, and verify boot, storage, SELinux, runtimes,
   restart, and Cloud inventory.
10. Publish and assign the integration component and provider only to the
    validation Unit. Prove that an absent or incompatible integration component
    blocks provider installation, and that missing or invalid credentials
    prevent provider activation without entering a FOTA artifact.
11. Demonstrate CARLA telemetry through VISS, the provider, KUKSA, and the
    consumer; also prove source loss, recovery, restart, independent component
    update, compatible rollback, and dependency-safe rollback ordering.
12. Decide separately whether to promote the accepted combination to the
    demonstration Unit. The validation-set scope defect must remain accounted
    for during every assignment decision.

Current stop point: gate 1, documentation review. `.11` is unsigned and local;
provider `0.2.0` is signed locally but unpublished and unassigned; no
integration-component artifact exists. The validation Unit remains on `.2`.
The demonstration Unit activated the previously staged `.1` slot during the
guarded 2026-08-16 restart; acceptance or rollback of that observed state is
an explicit pre-cleanup gate.

The detailed design and qualification questions are in
[the R6.1 integration-component plan](r6-1-integration-component-plan.md).

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
