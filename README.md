# CARLA–AosEdge Integration

This repository owns the reproducible integration between the native Apple
Silicon CARLA/VISS environment and AosEdge. It does not vendor CARLA, Unreal
Engine, AosCore, or AosVM images.

The first milestone boots the official AosVM 6.1.0 `qemuarm64` image on an
Apple Silicon Mac. Later milestones bridge the project's VISS 3.1 telemetry
into the in-VM KUKSA Databroker and deploy an AosEdge-managed service that
subscribes to the resulting VSS signals without depending on CARLA.

## Documents

- [Project roadmap](docs/roadmap.md)
- [AOS-0: boot official ARM64 AosVM on Apple Silicon](docs/aos-0-arm64-vm.md)
- [AOS-1: provision one Main Node](docs/aos-1-single-node-provisioning.md)
- [AOS-2: qualify the CARLA VISS-to-KUKSA provider](docs/aos-2-carla-kuksa-qualification.md)
- [R6.1: design a Cloud-visible provider FOTA component](docs/r6-1-vehicle-data-provider-fota-design.md)
- [R6.1-1: runtime-mechanism qualification record](docs/r6-1-runtime-mechanism-qualification.md)
- [R6.1-2: bootstrap-image qualification record](docs/r6-1-bootstrap-image-qualification.md)
- [R6.1-3: atomic lifecycle design](docs/r6-1-atomic-component-lifecycle.md)
- [R6.1-3: atomic lifecycle qualification record](docs/r6-1-atomic-component-lifecycle-qualification.md)
- [R6.1-3.1: real provider interface-closure plan](docs/r6-1-real-provider-interface-closure.md)
- [R6.1-5: offline provider qualification and signing gate](docs/r6-1-offline-provider-qualification.md)
- [R6.1-6: first isolated Cloud deployment](docs/r6-1-first-cloud-deployment.md)
- [Colleague setup: run and provision AosVM on an Apple Silicon Mac](docs/aosvm-macos-colleague-setup.md)
- [Reissue AosEdge user certificates on a new Mac](docs/aos-user-certificate-reissue-macos.md)
- [Licensing and copyright policy](docs/licensing-and-copyright-policy.md)
- [Repository separation implementation plan](docs/repository-separation-plan.md)
- [Exact component lock](docs/component-lock.md)
- [Repository and artifact boundaries](docs/decisions/0001-repository-and-artifact-boundaries.md)
- [QEMU system VM with HVF](docs/decisions/0002-qemu-system-hvf-for-aosvm.md)
- [Superseded two-Node topology decision](docs/decisions/0003-two-node-aos1-topology.md)
- [Single Main Node for AOS-1](docs/decisions/0004-single-main-node-for-aos1.md)
- [KUKSA vehicle-data boundary and authorization follow-up](docs/decisions/0005-kuksa-vehicle-data-boundary.md)
- [Lifecycle-based platform and service repository ownership](docs/decisions/0006-lifecycle-based-repository-ownership.md)

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
exposure. It follows macOS resolver changes after sleep or a Wi-Fi/network
transition without restarting the VM. Phase 12 adds an English-only,
ownership-checked lifecycle with
background and foreground start, serial console, status, smoke test, QMP-first
shutdown, and explicit overlay reset. Phase 13 proves persistence across a
clean restart, safe recreation of only the disposable overlay, unchanged
immutable inputs, complete stopped-state cleanup, and recovery of the tracked
ARM64 and DNS compatibility state. Phase 14 accepted-baseline recording is
complete: the final start/smoke/stop run passed, sanitized evidence is recorded,
and the VM is stopped. The current decision is **go to AOS-1** with only the
qualified Main Node. Official generic provisioning supports one Node; the
Secondary image and multi-Node work are deferred until a concrete use case
justifies them. AOS-1.1 through AOS-1.9 are complete. The official SDK
provisioned exactly one Main Node, AosCloud reports the Unit online, two normal
starts preserved its identity without exposing provisioning IAM, and verified
pre- and post-provision checkpoints protect its persistent disk. The VM is
running in normal mode with lifecycle `provisioned`. The schema-v2 official
Hello World sample is installed as one ARM64 `crun` workload and reports
`Active`. Its bounded English output was retrieved through the AosCloud log
API, and a cloud-driven removal and fresh start both passed. The repository
separation gate has completed R-0 through R-5: the platform and service
repositories, draft vehicle-data contract, diagnostic ARM64 service scaffold,
and exact component lock are public and validated. R-5 passed both fresh-clone
qualification and the independent GitHub Actions gate. The repository
separation gate is complete. R6/AOS-2 is also complete: the ARM64 platform
provider publishes the seven contract 0.1.1 signals from the host-only CARLA
VISS endpoint into the in-VM KUKSA Databroker at 20 Hz, marks them unavailable
on source loss, and survives a clean VM restart without changing the
provisioned cloud Unit. R6.1-1 is complete: an isolated ARM64 build proved the
custom Service Manager runtime through the local CM boundary, selected the
persistent component root, and confirmed that the existing Unit Model and Node
Type remain unchanged. R6.1-2 is complete: the unchanged and project bootstrap
images built, both disposable image gates passed, the project delta is exactly
one OEM platform package, and the unsigned boot plus full-rootfs FOTA output
passed structural and secret-exclusion checks. Both Moulin manifests are
pinned; the project manifest references the separately versioned OEM platform
layer and contains no upload credential. R6.1-3 is complete: the production
runtime implements restricted provider-archive handling, durable A/B apply,
rollback and restart recovery. Its exact ARM64 compile and 40 lifecycle tests,
corrected incremental Yocto image, disposable non-provisioned guest gate, and
regenerated unsigned bootstrap FOTA output all pass. R6.1-3.1 and R6.1-4 are
complete: the real Python provider conforms to the fixed launcher, health,
configuration, credential, trust, and packaging interfaces, and its
reproducible credential-free `0.2.0` candidate passes both local and official
unsigned validation. R6.1-5 is complete. A fresh
disposable ARM64 VM passed the runtime matrix, real install, live telemetry,
source-loss, update, downgrade, failed-candidate rollback, security, SELinux,
resource, and secret-exclusion gates. The exact unsigned layer, configuration,
and reproducibility envelope are frozen. Only that accepted candidate was
signed with the OEM identity and its RS256 signature, signed hashes, embedded
layer, and configuration passed the guarded local verifier. No Cloud or active
Unit mutation was performed or is authorized.
Bootstrap deployment, Cloud mutation,
deprovisioning, reprovisioning, and active-Unit changes remain separately
gated. R6.1-6 local preparation is complete: a dedicated validation VM profile
is isolated, boot remains `6.1.0`, and the rootfs-only
`6.1.1-maninblack.1` release passed its incremental build, structural checks,
two disposable boots, clean restart, and security gates. The unsigned rootfs
candidate was frozen and then signed under separate explicit approval. Its
embedded inputs, signed hashes, and RS256 signature passed the guarded local
verifier. Work is stopped before Cloud mutation approval; no upload,
provisioning, publication, assignment, or Unit change is authorized.

## Commands

For a new Apple Silicon Mac, use the guarded onboarding entry point. It keeps
local VM setup separate from the explicit cloud-provisioning step:

```sh
./scripts/aosvm-macos-onboard doctor
./scripts/aosvm-macos-onboard bootstrap
./scripts/aosvm-macos-onboard setup
```

Validate the non-secret integration baseline lock with:

```sh
./scripts/validate-component-lock
```

Validate the separate R6.1 source and ARM64 builder candidate before creating
or using the isolated Yocto builder:

```sh
./scripts/validate-r6-1-source-lock
./scripts/validate-r6-1-manifest
python3 -m unittest tests.test_r6_1_source_lock
```

This candidate records exact upstream commits, the Service Manager recipe
`SRCREV`, relevant source-file digests, and the pinned Ubuntu ARM64 builder
image. It contains no checkout path, Aos Unit identity, Cloud credential, or
OEM signing material.

Manage the isolated builder separately from the provisioned AosVM:

```sh
./scripts/r6-1-builder host-check
./scripts/r6-1-builder download
./scripts/r6-1-builder prepare
./scripts/r6-1-builder start --dry-run
./scripts/r6-1-builder start
./scripts/r6-1-builder wait
./scripts/r6-1-builder smoke-test
./scripts/r6-1-builder bootstrap-tools
./scripts/r6-1-builder pin-moulin-tools
./scripts/r6-1-builder copy PATH /home/yocto/DESTINATION
./scripts/r6-1-builder fetch /home/yocto/r61-build/VARIANT/IMAGE artifacts/r6-1/VARIANT/IMAGE
./scripts/r6-1-builder stop
```

The builder uses a private sparse disk outside Git, key-only SSH on
`127.0.0.1:10023`, and a dynamic macOS resolver bridge on
`127.0.0.1:18054`. The DNS listener follows macOS resolver changes but is
never exposed to the LAN. `stop` cleanly stops both QEMU and the DNS bridge.
`bootstrap-tools` installs the qualification build dependencies and pins Conan
and CMake inside the non-provisioned builder; it never installs Aos identity
or signing material.
`pin-moulin-tools` installs Moulin from the already verified local v0.21
checkout and replaces its unbounded `gpt-image` dependency with the compatible
0.8.1 wheel after verifying the wheel's official PyPI SHA-256. It also installs
the exact, hash-verified Pydantic 2 wheel set required by the released Aos FOTA
metadata builder into the same isolated pipx environment.
`copy` accepts only an explicit local source and a destination below the
unprivileged builder user's home directory.
`fetch` accepts only regular R6.1 image artifacts, writes below the ignored
`artifacts/r6-1` directory, refuses overwrites, preserves a 20 GiB host-space
reserve, and verifies the guest and host SHA-256 digests before publishing the
read-only local artifact.

When the project repositories are sibling checkouts, also verify their exact
commits and locked files without recording those local paths:

```sh
./scripts/validate-component-lock --workspace-root ..
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
./scripts/aosvm dns-check
./scripts/aosvm-macos-onboard verify-online
```

`dns-check` performs a bounded query through the same loopback bridge used by
the guest. It is useful after waking the Mac or moving between networks; a
successful check does not require a VM restart.

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
