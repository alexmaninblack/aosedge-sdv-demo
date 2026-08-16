# ADR 0002: Run AosVM as a QEMU System VM with HVF

- Status: Accepted for AOS-0
- Date: 2026-08-12

## Context

AosCore depends on Linux kernel facilities such as cgroups, namespaces,
seccomp, overlayfs, nftables, traffic control, quotas, and SELinux. The target
host is an Apple Silicon Mac, whose host kernel is XNU rather than Linux.

The official AosVM 6.1.0 ARM64 release is distributed as QEMU qcow2 disks plus
ARM QEMU EFI firmware. The release also contains the Linux kernel, initramfs,
root filesystem, AosCore components, and `crun` runtime needed by the guest.

The terms "QEMU", "emulation", and "user networking" can be ambiguous:

- `qemu-system-aarch64` creates a complete virtual machine and boots a guest
  kernel;
- `qemu-aarch64` runs individual Linux user-space programs and is not suitable
  for AosVM;
- QEMU user networking is only a network backend for a system VM and does not
  replace or bypass the guest kernel.

VirtualBox can also create a full ARM64 VM, but the pinned official artifact and
upstream launch topology are QEMU-specific. Selecting VirtualBox would introduce
an image-conversion or separate SDK flow before the official QEMU path has been
tested.

## Decision

Use native `qemu-system-aarch64` with:

- Apple Hypervisor Framework (`hvf`) acceleration only;
- the QEMU ARM `virt` machine;
- the CPU model qualified for HVF on the host, preferably `host`;
- the upstream `QEMU_EFI.fd` firmware;
- the upstream Main Node qcow2 disk behind `virtio-scsi-pci` and `scsi-hd`;
- a qcow2 overlay as the only writable VM disk; it is disposable only while
  unprovisioned and becomes the permanent local Unit disk before provisioning;
- QEMU user networking and loopback-only host forwarding for the first spike;
- serial and QMP sockets owned by this repository.

The official guest kernel remains the authority for AosCore's Linux features.
The macOS host kernel is not expected to provide them. AOS-0 must functionally
test the required kernel features and run a local OCI bundle with `crun` before
the VM is accepted for provisioning.

Do not silently fall back to QEMU TCG. TCG may be used later for a narrowly
approved diagnostic, but it does not satisfy the M5 Pro native-virtualization
baseline.

## Consequences

### Positive

- Uses the upstream release in its native format and intended ARM machine
  family.
- Boots the official Linux kernel and preserves the Linux environment required
  by AosCore.
- Uses Apple hardware virtualization without requiring VirtualBox kernel
  extensions or a separate image-conversion workflow.
- Keeps base artifacts immutable and isolates local changes in one overlay.
  Before provisioning, the lifecycle protects that overlay from reset and
  creates an independent recovery checkpoint outside Git.
- Allows headless, scriptable startup, shutdown, serial logging, and health
  checks.

### Costs and constraints

- QEMU still supplies device emulation, firmware integration, networking, and
  lifecycle plumbing around HVF; HVF is not a complete VM product by itself.
- The released static guest network configuration may need a deterministic
  overlay-only DNS adjustment.
- macOS QEMU/HVF CPU compatibility must be probed rather than assuming that the
  upstream `cortex-a57` command line is correct for this host.
- Passing boot alone is insufficient; the guest-kernel and local OCI gates add
  explicit validation work.

## Alternatives considered

### VirtualBox ARM64

Technically capable of running a full guest kernel, but not selected for AOS-0
because the pinned artifact and upstream script target QEMU. Keep it as a
fallback if the QEMU networking design cannot meet the integration needs or an
official SDK-managed VirtualBox ARM64 flow is later required.

### QEMU TCG

Can emulate ARM CPUs without HVF and may help diagnose CPU-model compatibility,
but it is slower and does not prove the intended hardware-accelerated Mac path.
It is not an accepted production or demonstration baseline.

### QEMU user-mode execution

Rejected. It does not boot the official AosVM kernel and cannot provide the
complete system environment required by AosCore.

### Rebuild AosVM with Yocto immediately

Deferred. Rebuilding adds a large toolchain and creates a custom image before
the official release has been evaluated. It becomes relevant only if a required
kernel capability or non-local image constraint cannot be solved with the
official artifact.

## Revisit conditions

Revisit this decision if:

- the official image cannot boot with HVF;
- a mandatory guest-kernel capability is absent;
- `crun` cannot execute a local OCI bundle;
- safe host/guest networking cannot be achieved without invasive host changes;
- AosEdge publishes a better-supported Apple Silicon VM workflow.
