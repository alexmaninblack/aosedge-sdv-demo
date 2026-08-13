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

Planning and Phases 1–6 are complete for AOS-0. The official AosVM 6.1.0 ARM64
Main Node boots natively accelerated by HVF on the Apple M5 Pro and reaches the
serial login prompt. The pinned archive, immutable base images, firmware, and
disposable overlay remain verified; the first shutdown was clean. Phase 7 will
validate the guest identity, boot state, and storage from inside the VM.

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

## Repository policy

This repository is intended to be public. Never commit credentials,
certificates containing private keys, SDK account data, downloaded VM images,
runtime disks, logs containing secrets, CARLA build output, or restricted
Unreal Engine material.
