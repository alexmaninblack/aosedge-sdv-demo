# AOS-0: Boot Official ARM64 AosVM on Apple Silicon

## Objective

Boot the official AosVM 6.1.0 `qemuarm64` Main Node on the M5 Pro without
rebuilding Yocto, changing the upstream base image, or performing cloud
provisioning. Produce a repeatable macOS launcher and enough evidence to decide
whether this image is a sound base for the CARLA integration.

Provisioning and certificate enrollment are explicitly out of scope. They will
be performed in AOS-1 with the utilities supplied by the AosEdge SDK.

## Pinned upstream input

| Field | Value |
| --- | --- |
| Repository | `AosEdge/meta-aos-vm` |
| Release | `v6.1.0` |
| Asset | `aos-vm-image-qemuarm64-6.1.0.tar.xz` |
| Published | 2026-06-07 |
| Size | 381,515,220 bytes |
| SHA-256 | `db8fef0188f4ba0930aecafecdfe4ad063a3cf27a48e8649fc5050f9b3117e04` |
| URL | `https://github.com/aosedge/meta-aos-vm/releases/download/v6.1.0/aos-vm-image-qemuarm64-6.1.0.tar.xz` |

The release archive contains both Main and Secondary Node disks plus the ARM
QEMU EFI firmware. AOS-0 boots the Main Node only. The pristine archive and
extracted base disks are immutable local inputs and are excluded from Git.

## Selected design

Use QEMU system emulation for AArch64 with Apple Hypervisor Framework (`hvf`)
acceleration and the upstream `virt` machine model. Store all persistent guest
changes in a qcow2 overlay whose backing file is the verified upstream Main
Node image.

The initial network backend is QEMU user-mode networking because it:

- requires no root privileges, TAP device, macOS bridge, or packet-filter
  changes;
- provides outbound TCP/UDP access;
- can expose SSH on a loopback-only host port;
- gives the guest a stable, guest-visible host address that can later be used
  for the VISS path.

VirtualBox is not the baseline because the current ARM64 release is packaged as
QEMU qcow2 plus QEMU EFI, while the official VirtualBox automation is a
different SDK-managed flow. A macOS `vmnet` or VirtualBox configuration remains
a fallback only if QEMU user networking cannot satisfy the image's fixed
network assumptions.

## Known network constraint

The released Main Node is configured for:

- address `10.0.0.100/24`;
- gateway `10.0.0.1`;
- DNS `10.0.0.1`.

QEMU user networking can present `10.0.0.1` as the host/gateway, but its DNS
proxy normally needs a different guest-visible address. The first boot must
therefore test routing and name resolution separately.

Preferred resolution if routing works but DNS does not:

1. keep the upstream base image read-only;
2. change only the disposable overlay's DNS setting to the QEMU DNS proxy;
3. automate that local development adjustment and record it in the run
   manifest;
4. reset by deleting and recreating the overlay.

Fallback order:

1. QEMU user networking with an overlay-only DNS adjustment;
2. QEMU `vmnet` networking with an explicit macOS host-only/NAT design;
3. an SDK-managed ARM64 VirtualBox path, if the installed SDK proves that it
   supports the release on Apple Silicon;
4. build a DHCP-enabled `qemuarm64` image only if none of the released-image
   options works.

## Planned repository layout

```text
carla-aosedge-integration/
  README.md
  docs/
  scripts/
    aosvm-download
    aosvm-prepare
    aosvm-start
    aosvm-stop
    aosvm-status
    aosvm-smoke-test
  config/
    aosvm.env.example
  tests/
  .cache/              # ignored; archive and extracted immutable base image
  .local/              # ignored; qcow2 overlay and local configuration
  .run/                # ignored; PID, QMP socket, serial socket
  runs/                # ignored; local manifests and logs
```

Scripts, examples, tests, and documentation are tracked. Downloaded upstream
artifacts and all mutable runtime state are not tracked.

## Execution plan

### 0. Record the host baseline

Capture without secrets:

- Mac model and CPU architecture;
- macOS version and build;
- available RAM and free disk space;
- QEMU version and supported AArch64 accelerators;
- repository commit;
- date and timezone.

Result: `aosvm-smoke-test` can place this information in an ignored per-run
manifest.

### 1. Install and validate the minimum host dependency

Install native ARM64 QEMU through the selected macOS package manager. Do not
install a full Yocto build environment.

Validate:

- `qemu-system-aarch64` and `qemu-img` are available;
- the binaries are native ARM64;
- `hvf` appears in the supported accelerator list;
- the QEMU version is recorded.

Stop condition: do not continue with TCG-only emulation unless a short
diagnostic boot is explicitly approved, because it would not represent the
intended M5 Pro execution path.

### 2. Download and verify the release

The download script must:

- use the pinned URL;
- save to an ignored cache directory;
- support retry/resume where the available transfer tool permits it;
- verify byte size and SHA-256 before extraction;
- refuse to use a mismatched artifact;
- record the upstream release metadata.

Never run code from an unverified archive.

### 3. Inspect and prepare immutable inputs

- List archive members before extraction and reject unsafe paths.
- Extract into a versioned ignored directory.
- Identify the Main Node qcow2 disk and `QEMU_EFI.fd` by exact expected names.
- Inspect disk metadata with `qemu-img info`.
- Mark the base disk read-only where practical.
- Create a new qcow2 overlay that references the base disk.

Re-running prepare must be idempotent. A reset removes only the explicitly
resolved overlay, never the cache root or repository.

### 4. Perform the first serial boot

Start the Main Node in the foreground with:

- AArch64 `virt` machine;
- HVF acceleration;
- host CPU model if supported, otherwise the closest supported virtual ARM CPU;
- 2 virtual CPUs and 2 GiB RAM initially;
- virtio SCSI disk;
- upstream QEMU EFI firmware;
- virtio network adapter;
- user-mode network `10.0.0.0/24`;
- loopback-only SSH forwarding;
- serial console and QMP control socket;
- no graphical window.

Observe and record:

- EFI and kernel boot;
- root filesystem mount;
- systemd reaching its operational target;
- absence of architecture or illegal-instruction failures;
- final login prompt;
- boot duration.

Development-image console access uses the documented `root` account. Any
published default password is development-only and must never be reused as a
project secret or exposed beyond a loopback forward.

### 5. Validate the guest

From the serial console or loopback SSH:

- confirm `aarch64`/`arm64` architecture;
- record kernel and OS release;
- inspect disk and memory;
- confirm `aos_iamanager`, `aos_servicemanager`, and
  `aos_communicationmanager` installation and current status;
- record failed systemd units;
- verify the configured IP, route, and DNS;
- test outbound IP connectivity and HTTPS/DNS separately;
- confirm the host is reachable through the guest-visible host address;
- confirm that no management port was accidentally exposed on a non-loopback
  macOS interface.

Cloud connection is not an acceptance requirement before provisioning. An
unprovisioned or certificate-related AosCore state is expected and must be
distinguished from a runtime failure.

### 6. Automate lifecycle commands

Implement English-only commands for:

- `download` — fetch and verify pinned inputs;
- `prepare` — extract and create the overlay;
- `start` — start only this repository's VM and write PID/QMP state;
- `status` — report process, serial, SSH, and disk state;
- `stop` — request a clean guest shutdown through QMP, then use a bounded
  escalation only for the owned QEMU PID;
- `reset-overlay` — recreate only the named disposable overlay after explicit
  confirmation;
- `smoke-test` — perform non-destructive health checks and write a local run
  manifest.

The scripts must reject stale or ambiguous PID files and must never match or
terminate unrelated QEMU processes by name.

### 7. Prove restart and persistence behavior

- Cleanly shut down the guest.
- Start it again from the same overlay.
- Confirm the guest boots and retains an intentionally created harmless marker.
- Stop it again.
- Recreate the overlay and confirm the marker disappears while the verified
  base remains unchanged.

### 8. Record the accepted baseline

Update this document with:

- exact QEMU package and version;
- final launch parameters;
- boot and shutdown timing;
- chosen network backend and DNS solution;
- AosCore component status before provisioning;
- known warnings;
- smoke-test result;
- whether AOS-1 should use one or two Nodes.

Commit only scripts, examples, tests, and sanitized documentation. Keep raw
serial logs and manifests ignored unless a specific sanitized fixture is
required for a test.

## Acceptance checklist

- [ ] Official archive matches the pinned SHA-256.
- [ ] Base image remains unchanged after every test.
- [ ] Main Node boots with HVF acceleration.
- [ ] Serial console reaches a login prompt.
- [ ] Guest reports ARM64 architecture.
- [ ] No unexplained failed core component exists.
- [ ] Outbound HTTPS and DNS work.
- [ ] SSH is reachable only through a loopback host forward.
- [ ] Clean shutdown and second boot succeed.
- [ ] Overlay reset is safe and reproducible.
- [ ] The launcher does not require administrator privileges.
- [ ] A sanitized baseline is committed and the working tree is clean.

## Explicit non-goals

- AosCloud registration or provisioning.
- Certificate generation or storage.
- Deployment of an application service.
- CARLA or VISS network changes.
- Multi-node routing.
- Rebuilding AosVM with Yocto.
- Modifying or redistributing the upstream VM image.

## Go/no-go decision for AOS-1

Proceed when the acceptance checklist passes and the remaining warnings are
limited to the expected unprovisioned state. Stop and reconsider the VM base if
HVF cannot boot the image, the released disk requires an invasive persistent
patch, or network access requires exposing host services to the external LAN.
