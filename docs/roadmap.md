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
LAN exposure. The bridge refreshes the active macOS resolver set after host
sleep and ordinary Wi-Fi/network transitions while retaining last-known-good
resolvers during a transient empty configuration. The upstream ARM64 EFI
loader correction from Phase 10 remains
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
- Create and verify the OEM and SP account identities without storing their
  tokens or certificates in this repository.
- Provision only the qualified Main Node with
  `aos-prov provision --nodes 1`.
- Use a temporary loopback-only forwarding mode for the guest IAM provisioning
  port; remove that forward from normal post-provision launches.
- Register a single-Node Target System containing only `aos-vm-main`.
- Lock destructive overlay reset before provisioning, keep lifecycle metadata
  outside Git, and create independent pre- and post-provision qcow2 checkpoints.
- Treat the provisioned overlay as the permanent local disk of the cloud Unit;
  never run a restored copy concurrently with the active VM.
- Confirm that the Unit appears online in hosted AosCloud.
- Deploy and observe the official Hello World service.

Exit criterion: AosCloud reports the Unit online and an official sample service
reaches `Active` state after a cloud-driven deployment.

Current gate: AOS-1.1 through AOS-1.9 pass. The SDK provisioned exactly one
Main Node with protocol v6 and `--nodes 1`; AosCloud reports one online,
provisioned Unit with one provisioned `aos-vm-main` Node. Two accepted
normal-mode starts preserved private identity hashes and exposed no
provisioning listener. Local IAM, SM, CM, encrypted storage, NFS, SELinux,
time, DNS, TLS, and HTTPS gates pass. Independent pre- and post-provision
checkpoints are verified, destructive reset is locked, lifecycle is
`provisioned`, and the VM is running in normal mode. The schema-v2 official
Hello World package was validated and uploaded with `aos-signer` 2.0.1. One
dedicated Subject and one explicitly approved Verification Set bind the sample
to only this development Unit. The Service Manager installed it on the ARM64
Main Node through `crun`; it reached `Active`, produced bounded English output
that was retrieved through the cloud log API, stopped after cloud assignment
removal, and reached `Active` again after a fresh assignment. The final local,
network, cloud monitoring, checkpoint, and resource-conflict gates pass. The
Verification Set intentionally remains active for this development Unit, so
future SOTA/FOTA assigned to it bypass additional OEM approval. The released
image's redundant
`quotaon.service` reports `EEXIST` after mount-time quota activation; quotas
and all required Aos data paths are operational, so this is tracked as a
non-blocking upstream idempotency issue.

No repository-managed script will reimplement the SDK provisioning protocol.

Detailed plan: [AOS-1 single-Node runbook](aos-1-single-node-provisioning.md).

## Repository Separation Gate — Complete R-0 through R-5

Execution status: R-0 through R-5 are complete. The documentation and scope are
accepted, both public repositories and their governance are live, the platform
contract and ARM64 diagnostic service scaffold pass CI, the exact component
lock is accepted, and clean-clone plus GitHub Actions dependency-boundary
qualification passed. This gate unblocked the now-complete AOS-2 work.

- Accept ADR 0006 and the review-gated repository separation plan.
- Create public `aos-vehicle-platform` and `vehicle-telemetry-service`
  repositories only after final plan approval.
- Publish the initial versioned vehicle-data contract from the platform
  repository.
- Scaffold platform/FOTA and service/SOTA ownership without implementing AOS-2
  or AOS-3 behavior during the separation step.
- Add an exact component version and artifact-digest lock to this integration
  repository.
- Qualify dependency direction, licensing, public-source safety, credential
  exclusion, clean cloning, and static gates across all repositories.
- Apply Apache-2.0, the `maninblack` copyright holder, SPDX/REUSE metadata,
  minimal NOTICE files, DCO contribution terms, and reviewed third-party
  provenance to both new repositories.

Exit criterion: R-0 through R-5 of the separation plan pass, repository
ownership matches the vehicle-program platform and independently updated
service lifecycles, and an accepted lock identifies the exact components for
the first AOS-2 baseline.

The AOS-2 implementation started only after this gate passed.

Detailed plan: [repository separation plan](repository-separation-plan.md).
Decision: [ADR 0006](decisions/0006-lifecycle-based-repository-ownership.md).

## AOS-2 — Bridge CARLA telemetry into the in-VM KUKSA Databroker

- Provide a host-only route from the guest to the macOS VISS endpoint.
- Run a platform-owned `carla-kuksa-provider` inside AosVM; do not embed the
  provider in CARLA or in the cloud-managed telemetry service.
- Preserve TLS verification and install only the required public trust anchor
  in the provider's declared platform resource.
- Keep VISS unavailable from the external LAN and Internet.
- Verify VISS 3.1 `get`, `subscribe`, reconnect, and shutdown behavior from an
  ordinary process in the guest.
- Map the approved VSS 6.0 telemetry paths to the compatible VSS 5.0 paths and
  publish them to the local KUKSA Databroker with a path-scoped provider JWT.

Exit criterion: KUKSA continuously receives live CARLA speed, acceleration,
steering, throttle, and brake values through the platform provider; loss of
CARLA produces an explicit stale state rather than fabricated zero values.

Current gate: R6/AOS-2 passes. The normalized ARM64 bundle is reproducible and
contains five exact hash-locked wheels. Inside the provisioned AosVM, KUKSA
uses a project-owned verifier and the DynamicUser provider receives only a
seven-path `provide` token through systemd credentials. Verified TLS and
`VISSv3` connect to the macOS loopback-only endpoint through the guest host
gateway. Forty-one consecutive atomic seven-path KUKSA batches measured
20.16 Hz. A separate read-only JWT retrieved the live values and source
timestamps. CARLA loss made every path unavailable immediately; reconnect is
bounded and never fabricates zero. After a clean VM restart, KUKSA and the
provider were active with zero restarts, root remained read-only, SELinux was
enforcing without a provider-related denial, AosCore remained healthy, and
AosCloud reported the same Online Unit with one primary Main Node. The future
Authorization Adapter remains explicitly deferred to AOS-5.

Detailed boundary decision: [ADR 0005](decisions/0005-kuksa-vehicle-data-boundary.md).
Qualification record: [AOS-2 runbook](aos-2-carla-kuksa-qualification.md).

## AOS-3 — Deploy the first KUKSA telemetry consumer

- Package an ARM64 OCI service with explicit CPU, RAM, storage, and network
  limits.
- Request the Aos `kuksa` resource and a compatible ARM64 `kuksa-client` layer.
- Subscribe to the approved VSS paths through the KUKSA streaming API; keep all
  CARLA endpoints and protocol handling outside the service.
- Use a path-scoped read-only KUKSA JWT until AOS-5 provides Aos IAM-integrated
  authorization.
- Produce structured English logs, data-age reporting, and connection health.
- Deploy, update, stop, and restart the service from AosCloud.

Exit criterion: the cloud-managed service receives live vehicle telemetry and
its state and logs are visible through AosCloud; the same service can consume a
non-CARLA provider without a code or configuration change.

## AOS-4 — Add useful edge processing

- Calculate trip statistics and bounded driving events such as hard braking,
  hard acceleration, and steering activity.
- Persist only explicitly selected state across service updates.
- Define whether processed results remain local, appear in logs/alerts, or are
  sent to a separate backend.

Exit criterion: the service demonstrates a useful transformation of live
vehicle data and preserves its declared state across an update.

## AOS-5 — Integrate Aos service identity with KUKSA authorization

- Return to the currently unavailable Aos-to-KUKSA Authorization Adapter after
  the end-to-end prototype and initial edge processing work.
- Bind the Aos-managed service identity or `AOS_SECRET` flow to short-lived,
  least-privilege KUKSA authorization.
- Preserve per-path separation between provider, consumer, and any future
  actuation permissions.
- Remove static KUKSA JWTs from service images and deployment artifacts.
- Define token renewal, revocation, offline operation, and failure behavior.

Exit criterion: Aos-managed service identity authorizes a consumer for only its
declared VSS paths without a static KUKSA token in the service artifact.

This milestone does not block AOS-2 through AOS-4, but it is mandatory before
third-party services, actuation, or production credential handling.

## AOS-6 — Evaluate and, if justified, add legacy AOS VIS integration

- Pin the exact AOS VIS protocol and signal-tree version.
- Define a reviewed mapping from VSS 6.0/VISS 3.1 paths to the older
  `Signal.*` and `Attribute.*` AOS VIS namespace.
- Implement either a dedicated adapter or a narrowly scoped bridge.
- Apply AosEdge IAM service permissions to vehicle-data access.

Exit criterion: a second cloud-managed service consumes mapped vehicle data
through AOS VIS without knowing that CARLA is the original source.

This optional milestone is intentionally after the KUKSA-based consumer. It
must solve a concrete compatibility requirement rather than add an unnecessary
second vehicle-data abstraction.

## Deferred decisions

- Self-hosted AosCloud versus the hosted platform.
- Secondary and additional AosVM Nodes, inter-Node networking, Dynamic
  Rebalance, and migration from a provisioned single-Node Unit.
- Cameras, LiDAR, radar, and ultrasonic data.
- ROS 2 integration.
- Upstream contributions to `AosEdge/meta-aos-vm` or `AosEdge/aos_vis`.
