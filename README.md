# CARLA–AosEdge Integration

This repository owns the reproducible integration between the native Apple
Silicon CARLA/VISS environment and AosEdge. It does not vendor CARLA, Unreal
Engine, AosCore, or AosVM images.

The first milestone boots the official AosVM 6.1.0 `qemuarm64` image on an
Apple Silicon Mac. Later milestones will deploy an AosEdge-managed service that
consumes the project's VISS 3.1 telemetry and, if justified, add an adapter to
the legacy AOS Vehicle Information Service interface.

## Documents

- [Project roadmap](docs/roadmap.md)
- [AOS-0: boot official ARM64 AosVM on Apple Silicon](docs/aos-0-arm64-vm.md)
- [AOS-1: provision one Main Node](docs/aos-1-single-node-provisioning.md)
- [Colleague setup: run and provision AosVM on an Apple Silicon Mac](docs/aosvm-macos-colleague-setup.md)
- [Reissue AosEdge user certificates on a new Mac](docs/aos-user-certificate-reissue-macos.md)
- [Repository and artifact boundaries](docs/decisions/0001-repository-and-artifact-boundaries.md)
- [QEMU system VM with HVF](docs/decisions/0002-qemu-system-hvf-for-aosvm.md)
- [Superseded two-Node topology decision](docs/decisions/0003-two-node-aos1-topology.md)
- [Single Main Node for AOS-1](docs/decisions/0004-single-main-node-for-aos1.md)

## Current status

Planning and Phases 1–14 are complete for AOS-0. The official AosVM 6.1.0 ARM64
Main Node boots natively accelerated by HVF on the Apple M5 Pro. Its guest
identity, own kernel, unified cgroups v2, memory, partition layout, read-only
root, writable data mounts, SELinux state, and pre-provisioning services are
validated by automated guest gates. Phase 8 passes all 13 capability probes,
including the initramfs-scoped SquashFS and loop update path. Phase 9 passes a
complete local ARM64 OCI run through `crun`, including namespace isolation,
resource limits, read-only rootfs, isolated networking, and clean teardown.
Phase 10 classifies the installed AosCore components as locally healthy and
intentionally unprovisioned. It also applies a tracked ARM64 compatibility fix
to the disposable overlay because the upstream Service Manager configuration
names the x86 EFI loader. Phase 11 passes layered address, route, TCP, DNS,
time, verified HTTPS, guest-to-host, loopback SSH, exposure, reboot, and cleanup
gates. A tracked loopback-only macOS DNS bridge supplies bounded resolver
failover without TAP, packet-filter changes, administrator privilege, or LAN
exposure. Phase 12 adds an English-only, ownership-checked lifecycle with
background and foreground start, serial console, status, smoke test, QMP-first
shutdown, and explicit overlay reset. Phase 13 proves persistence across a
clean restart, safe recreation of only the disposable overlay, unchanged
immutable inputs, complete stopped-state cleanup, and recovery of the tracked
ARM64 and DNS compatibility state. Phase 14 accepted-baseline recording is
complete: the final start/smoke/stop run passed, sanitized evidence is recorded,
and the VM is stopped. The current decision is **go to AOS-1** with only the
qualified Main Node. Official generic provisioning supports one Node; the
Secondary image and multi-Node work are deferred until a concrete use case
justifies them. AOS-1.1 through AOS-1.8 are now complete. The official SDK
provisioned exactly one Main Node, AosCloud reports the Unit online, two normal
starts preserved its identity without exposing provisioning IAM, and verified
pre- and post-provision checkpoints protect its persistent disk. The VM is
stopped with lifecycle `provisioned`. Deploying the official Hello World
service is the remaining AOS-1 phase.

## Commands

For a new Apple Silicon Mac, use the guarded onboarding entry point. It keeps
local VM setup separate from the explicit cloud-provisioning step:

```sh
./scripts/aosvm-macos-onboard doctor
./scripts/aosvm-macos-onboard bootstrap
./scripts/aosvm-macos-onboard setup
```

See the colleague setup guide before running `provision --confirm`.

Qualify the Apple Silicon host, HVF, QEMU baseline, resources, and planned
loopback listeners:

```sh
./scripts/aosvm host-check
```

Download or reverify the pinned official release archive:

```sh
./scripts/aosvm download
```

Prepare or reverify immutable release inputs and the writable Main Node overlay:

```sh
./scripts/aosvm prepare
```

Validate and print the exact QEMU command without starting the VM:

```sh
./scripts/aosvm start --dry-run
```

The provisioning-only dry run adds a single loopback forward for IAM. A real
provisioning start is rejected until the pre-provision checkpoint has locked
the lifecycle:

```sh
./scripts/aosvm start-provisioning --dry-run
./scripts/aosvm checkpoint-pre-provision
./scripts/aosvm start-provisioning
```

Provisioning mode adds only
`127.0.0.1:18089 -> 10.0.0.100:8089`; normal `start` never exposes IAM.

Start the Main Node as an owned background VM:

```sh
./scripts/aosvm start
```

The start command reports QEMU readiness. The guest can take longer to reach
its login prompt and SSH readiness. Use the bounded smoke test when guest
readiness is required:

```sh
./scripts/aosvm status
./scripts/aosvm smoke-test
```

Attach to the existing VM serial console, or start it in the foreground when
direct process ownership is preferable:

```sh
./scripts/aosvm console
./scripts/aosvm start --foreground
```

Request a clean guest shutdown through QMP. Repeating `start`, `status`, or
`stop` is safe and idempotent:

```sh
./scripts/aosvm stop
```

`reset-overlay` recreates only an unprovisioned Main Node overlay and requires
explicit confirmation. It is permanently blocked after the pre-provision
lifecycle checkpoint is created:

```sh
./scripts/aosvm reset-overlay --confirm
```

Immediately before provisioning, stop the VM and create a standalone recovery
checkpoint. This also locks destructive reset:

```sh
./scripts/aosvm checkpoint-pre-provision
./scripts/aosvm lifecycle-status
```

After successful provisioning, two clean restart/identity checks, and cloud
acceptance, stop the VM and seal its persistent identity with a second
standalone checkpoint:

```sh
./scripts/aosvm seal-provisioned
./scripts/aosvm lifecycle-status
```

These checkpoints and their lifecycle metadata live outside the checkout at
`~/Library/Application Support/CarlaAosEdge/AosVM/backups` by default and must
remain private. A matching reset guard beside the active overlay makes missing
or inconsistent lifecycle metadata fail safe. Never start a restored
checkpoint while the active Unit still exists; both disks contain the same
cloud identity.

Optional non-secret environment overrides are documented in
`config/aosvm.env.example`.

The read-only Phase 7 guest gate is tracked at
`tests/guest/aosvm-phase7-test`. It is intended to run as root inside the
unprovisioned Main Node and contains no credential or provisioning action.

The self-cleaning Phase 8 capability gate is tracked at
`tests/guest/aosvm-phase8-test`. It is also intended to run as root inside the
unprovisioned Main Node. It exercises temporary kernel objects and therefore
must only be run on an otherwise idle development VM.

The Phase 9 local OCI gate and its tracked runtime configuration are
`tests/guest/aosvm-phase9-test` and
`tests/guest/aosvm-phase9-config.json`. Run them from the same directory as
root inside an idle, unprovisioned Main Node. The gate constructs its rootfs in
volatile `/var/tmp`, does not contact AosCloud, and removes all probe state.

The read-only Phase 10 classification gate is
`tests/guest/aosvm-phase10-test`. Before running it on the pinned `qemuarm64`
image, apply `scripts/guest/aosvm-apply-arm64-compat` once inside the guest. The
helper changes only the disposable overlay, is idempotent, preserves the
read-only root and SELinux context, and corrects the Service Manager boot
runtime from `bootx64.efi` to the ARM64 `bootaa64.efi` present on both boot
partitions.

Before the first Phase 11 run on the pinned image, also apply
`scripts/guest/aosvm-apply-qemu-network-compat` inside the guest and reboot.
It configures the image's existing dnsmasq to reach the tracked macOS DNS
bridge started automatically by either start mode. The helper is
idempotent, changes only the disposable overlay, preserves SELinux labels and
the read-only root contract, and contains no credential. The repeatable live
gates are `tests/guest/aosvm-phase11-test` and
`tests/host/aosvm-phase11-host-gate`.

Phase 13 persistence and stopped-state gates are
`tests/guest/aosvm-phase13-test` and
`tests/host/aosvm-phase13-stopped-gate`. The guest gate writes only one
explicit marker on the writable `/home` partition. The host gate is read-only
and verifies cleanup, listener absence, qcow2 integrity, and exact immutable
input hashes after each stop.

## Repository policy

This repository is intended to be public. Never commit credentials,
certificates containing private keys, SDK account data, downloaded VM images,
runtime disks, logs containing secrets, CARLA build output, or restricted
Unreal Engine material.
