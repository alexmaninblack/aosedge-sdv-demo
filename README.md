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
- [Repository and artifact boundaries](docs/decisions/0001-repository-and-artifact-boundaries.md)
- [QEMU system VM with HVF](docs/decisions/0002-qemu-system-hvf-for-aosvm.md)

## Current status

Planning and Phases 1–8 are complete for AOS-0. The official AosVM 6.1.0 ARM64
Main Node boots natively accelerated by HVF on the Apple M5 Pro. Its guest
identity, own kernel, unified cgroups v2, memory, partition layout, read-only
root, writable data mounts, SELinux state, and pre-provisioning services are
validated by automated guest gates. Phase 8 passes all 13 capability probes,
including the initramfs-scoped SquashFS and loop update path. Phase 9 is the
next gate: a complete local OCI run through `crun` without AosCloud.

## Commands

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

Start the Main Node in the foreground with a timestamped serial log and private
QMP and serial sockets:

```sh
./scripts/aosvm start --foreground
```

Foreground start is the validated Phase 6 path. Interactive console, status,
and lifecycle commands are added in later phases.

The read-only Phase 7 guest gate is tracked at
`tests/guest/aosvm-phase7-test`. It is intended to run as root inside the
unprovisioned Main Node and contains no credential or provisioning action.

The self-cleaning Phase 8 capability gate is tracked at
`tests/guest/aosvm-phase8-test`. It is also intended to run as root inside the
unprovisioned Main Node. It exercises temporary kernel objects and therefore
must only be run on an otherwise idle development VM.

## Repository policy

This repository is intended to be public. Never commit credentials,
certificates containing private keys, SDK account data, downloaded VM images,
runtime disks, logs containing secrets, CARLA build output, or restricted
Unreal Engine material.
