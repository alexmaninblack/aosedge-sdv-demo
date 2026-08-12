# AOS-0: Boot Official ARM64 AosVM on Apple Silicon

## Objective

Boot the official AosVM 6.1.0 `qemuarm64` Main Node on the M5 Pro without
rebuilding Yocto, changing the upstream base image, or performing cloud
provisioning. Produce a repeatable macOS launcher and enough evidence to decide
whether this image is a sound base for the CARLA integration.

Provisioning and certificate enrollment are explicitly out of scope. They will
be performed in AOS-1 with the utilities supplied by the AosEdge SDK.

## Execution status

| Phase | Status | Result |
| --- | --- | --- |
| Phase 1: host baseline | Complete — 2026-08-12 | Pass |
| Phase 2: native QEMU qualification | Complete — 2026-08-12 | Pass |
| Phases 3–14 | Not started | — |

### Phase 1 observed baseline

| Field | Observed value |
| --- | --- |
| Host | Apple M5 Pro (`Mac17,8`) |
| Architecture | `arm64` |
| CPU | 18 physical / 18 logical cores |
| Memory | 51,539,607,552 bytes (48 GiB) |
| macOS | 26.5.2, build `25F84` |
| Hypervisor Framework | Available (`kern.hv_support=1`) |
| Free disk at repository | 392,364,826,624 bytes (365.42 GiB) |
| Planned SSH forward | `127.0.0.1:10022`, available at check time |
| Homebrew | Native prefix `/opt/homebrew` |
| QEMU | Not installed; expected input to Phase 2 |
| Repository branch | `feature/aos-0-arm64-vm` |
| Repository commit checked | `9168b64cb91983b78c10c9dc17184f0334c99bb8` |
| Check time | `2026-08-12T23:19:40+0200` (`CEST`) |

No serial number, hardware UUID, network address, credential, or account data
was collected. Phase 1 passes because the host is native ARM64, supports HVF,
has substantially more than the 20 GiB disk minimum and 2 GiB guest-memory
baseline, and has no listener occupying the planned loopback port.

### Phase 2 observed baseline

| Field | Qualified value |
| --- | --- |
| Package manager | Homebrew 6.0.17, native prefix `/opt/homebrew` |
| Package | `qemu` 11.0.3, Homebrew ARM64 bottle |
| System binary | `/opt/homebrew/bin/qemu-system-aarch64`, Mach-O ARM64 |
| Image binary | `/opt/homebrew/bin/qemu-img`, Mach-O ARM64 |
| Accelerator | `hvf` |
| Machine | `virt-11.0` |
| CPU | `host` |
| Initial topology | 2 vCPUs, 2 GiB RAM for AosVM |
| Storage controller | `virtio-scsi-pci` with `scsi-hd` |
| Network device | `virtio-net-pci` |
| User network | `10.0.0.0/24`, host `10.0.0.1`, DNS proxy `10.0.0.2` |
| Planned SSH forward | `127.0.0.1:10022` to `10.0.0.100:22` |
| Check completed | `2026-08-12T23:30:25+0200` (`CEST`) |

Qualification used empty, diskless probes only; no AosVM image or guest OS was
started. QEMU successfully created and ran two `host` vCPUs with HVF, created
the required virtio-SCSI and virtio network devices, accepted the planned user
network, and bound the SSH forward only to loopback. The probes exited cleanly,
leaving no QEMU process or listener on port 10022.

The installed binary also contains TCG, but the accepted launcher configuration
selects `virt-11.0,accel=hvf` explicitly and defines no accelerator fallback.
TCG does not satisfy the AOS-0 acceptance criteria.

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

Use `qemu-system-aarch64` for a complete virtual ARM64 machine with Apple
Hypervisor Framework (`hvf`) acceleration and the upstream `virt` machine
model. This is not QEMU user-mode execution: the official AosVM EFI, bootloader,
Linux kernel, initramfs, root filesystem, systemd, and AosCore processes all run
inside the guest. QEMU and HVF provide virtual CPUs, memory, interrupts, timers,
and devices; they do not replace the guest kernel.

```text
macOS / Apple Silicon
  -> QEMU system VM + HVF
    -> ARM virt machine + virtio devices
      -> upstream QEMU_EFI.fd
        -> GRUB
          -> upstream AosVM kernel + Aos initramfs
            -> upstream AosVM root filesystem + systemd
              -> AosCore + crun
```

Store all persistent guest changes in a qcow2 overlay whose backing file is the
verified upstream Main Node image. The downloaded archive, extracted base disk,
and EFI firmware remain immutable.

The phrase **QEMU user networking** in this plan refers only to the emulated
network backend. It does not mean QEMU user-mode CPU emulation and has no effect
on which Linux kernel runs in the VM.

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

## Boot and storage invariants

The released image expects its boot disk to appear as `/dev/sda`. The launcher
must therefore preserve the upstream virtio-SCSI topology:

```text
qcow2 overlay -> virtio-scsi-pci -> scsi-hd -> /dev/sda
```

Switching to virtio-blk would normally rename the disk to `/dev/vda` and could
break the boot configuration, initramfs logic, and Aos partition handling.

Expected partitions after boot:

| Device | Expected role | AOS-0 check |
| --- | --- | --- |
| `/dev/sda1` | Boot A, including ARM64 kernel and EFI files | Present; not modified |
| `/dev/sda2` | Boot B for update rollback | Present; not modified |
| `/dev/sda3` | Root filesystem | Mounted read-only |
| `/dev/sda4` | Home data | Mounted read-write |
| `/dev/sda5` | Variable data | Mounted read-write |
| `/dev/sda6` | Encrypted Aos data area | Present; state recorded before provisioning |

The test must verify the observed layout rather than assume it. Any device-name
or partition-role mismatch is a stop condition until its cause is understood.

## Guest kernel contract

Booting to a login prompt is necessary but not sufficient. AosCore relies on
Linux facilities that must be supplied by the **guest kernel**, including:

- unified cgroups v2 and CPU/memory resource control;
- mount, PID, IPC, UTS, and network namespaces;
- seccomp;
- overlayfs and squashfs;
- veth, bridge, VLAN, VXLAN, and IFB networking;
- nftables, conntrack, and NAT;
- traffic control with TBF, ingress, mirred, and matchall support;
- filesystem quotas;
- SELinux policy support used by the AosVM build.

AOS-0 includes functional probes for these facilities and a local, cloud-free
OCI container run with `crun`. A kernel configuration listing alone is not
accepted as proof when a safe functional probe is possible.

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
  Brewfile
  README.md
  docs/
  scripts/aosvm             # one entry point with lifecycle subcommands
  scripts/lib/              # shared validation and QEMU command assembly
  config/
    aosvm.env.example
  tests/
    guest/                   # kernel and local OCI capability probes
    host/                    # launcher and listener checks
  .cache/              # ignored; archive and extracted immutable base image
  .local/              # ignored; qcow2 overlay and local configuration
  .run/                # ignored; PID, QMP socket, serial socket
  runs/                # ignored; local manifests and logs
```

Scripts, examples, tests, and documentation are tracked. Downloaded upstream
artifacts and all mutable runtime state are not tracked.

The public repository must contain no upstream VM image, Unreal Engine content,
CARLA packaged content, certificate, token, password, private key, raw cloud
configuration, or log containing credentials.

## Work products

AOS-0 is complete only when it produces all of the following:

1. a repeatable `scripts/aosvm` command with `host-check`, `download`,
   `prepare`, `start`, `console`, `status`, `smoke-test`, `stop`, and
   `reset-overlay` subcommands;
2. an English-only example configuration with no secrets;
3. automated host, boot, guest-kernel, networking, and local OCI checks;
4. an ignored per-run evidence manifest and serial log;
5. a sanitized accepted-baseline section committed to this document;
6. a clear go/no-go decision for provisioning in AOS-1.

## Execution plan

### Phase 0: Freeze scope and safety boundaries

Before touching the host:

- work on `feature/aos-0-arm64-vm`;
- confirm the repository working tree and current commit;
- confirm that `.cache/`, `.local/`, `.run/`, `runs/`, and common secret formats
  are ignored;
- keep all host forwards bound to `127.0.0.1`;
- do not use `sudo` on macOS, macOS bridging, packet-filter changes, or external
  LAN listeners in the baseline;
- do not provision, enroll certificates, or supply cloud credentials;
- do not execute upstream helper scripts merely because they are in the release
  archive; use them as implementation references only;
- never silently fall back from HVF to TCG.

**Pass:** the branch, ignore rules, and ownership boundaries are unambiguous.

**Stop:** any required artifact or configuration would need to be committed
despite containing private or upstream-distribution-controlled data.

### Phase 1: Record and validate the host baseline

Capture without secrets:

- Mac model and CPU architecture;
- macOS version and build;
- available RAM and free disk space;
- Hypervisor Framework availability;
- currently installed QEMU version and supported AArch64 accelerators, if any;
- availability of the planned loopback SSH port;
- repository commit;
- date and timezone.

Initial default sizing for the Main Node is 2 vCPUs, 2 GiB RAM, and at least
20 GiB of free host disk for the release, extraction, overlay, and logs. Sizing
is recorded in configuration and can be raised after measurement.

Representative checks:

```sh
uname -m
sw_vers
sysctl -n kern.hv_support
```

**Pass:** the host is Apple Silicon, `kern.hv_support` reports hardware
virtualization support, resources are available, and the chosen loopback port
is free.

**Stop:** an x86-only QEMU binary, unavailable HVF, insufficient resources, or
an ambiguous port owner.

**Evidence:** `host` section in an ignored per-run manifest.

### Phase 2: Install and qualify native QEMU

Install native ARM64 QEMU through the selected macOS package manager. Do not
install a full Yocto build environment.

Validate:

- `qemu-system-aarch64` and `qemu-img` are available;
- the binaries are native ARM64;
- `hvf` appears in the supported accelerator list;
- the `virt` machine and virtio-SCSI/virtio-network devices are available;
- the CPU model accepted by HVF is determined explicitly;
- the QEMU version is recorded.

Representative qualification commands:

```sh
file "$(command -v qemu-system-aarch64)"
qemu-system-aarch64 --version
qemu-system-aarch64 -accel help
qemu-system-aarch64 -machine help
qemu-system-aarch64 -cpu help
qemu-img --version
```

Use `-cpu host` when QEMU/HVF accepts it. If it does not, select a supported
HVF CPU model based on a recorded probe. Do not quietly copy the upstream
`cortex-a57` setting if that setting forces software emulation on macOS.

**Pass:** a native QEMU build can create an AArch64 `virt` VM with `hvf`.

**Stop:** QEMU initializes only TCG, or the required disk/network device model
is unavailable.

**Evidence:** exact QEMU paths, versions, accelerator list, and selected CPU
model in the manifest. Add QEMU to a tracked `Brewfile` after validation.

### Phase 3: Download and verify the pinned release

The download script must:

- use the pinned URL;
- save to an ignored cache directory;
- support retry/resume where the available transfer tool permits it;
- verify byte size and SHA-256 before extraction;
- refuse to use a mismatched artifact;
- record the upstream release metadata.

Never run code from an unverified archive.

Verification order:

1. download into a temporary file under `.cache/`;
2. verify exact byte count;
3. verify SHA-256;
4. atomically rename it to the final cached name;
5. write no success marker until all checks pass.

**Pass:** the cached archive is exactly 381,515,220 bytes and its SHA-256 is
`db8fef0188f4ba0930aecafecdfe4ad063a3cf27a48e8649fc5050f9b3117e04`.

**Stop:** any digest, size, TLS, or final-URL mismatch.

**Evidence:** URL, size, digest, and verification timestamp in the manifest.

### Phase 4: Inspect the archive and prepare immutable inputs

- List archive members before extraction and reject unsafe paths.
- Reject absolute paths, `..` traversal, device nodes, and unexpected archive
  members before extraction.
- Extract into `.cache/aosvm/v6.1.0/qemuarm64/`.
- Identify exactly one Main Node qcow2 disk, one Secondary Node disk, and
  `QEMU_EFI.fd`; record their final names and hashes.
- Inspect both disks with `qemu-img info --output=json`.
- Reject an unexpected format, damaged qcow2 metadata, or an unplanned backing
  chain.
- Mark extracted inputs read-only where practical.
- Create `.local/aosvm-main-overlay.qcow2` with the verified Main Node disk as
  its backing file.
- Keep the Secondary Node disk cached but unused in AOS-0.

Re-running prepare must be idempotent. A reset removes only the explicitly
resolved overlay, never the cache root or repository.

**Pass:** base inputs are verified and immutable, and the new overlay has the
expected backing file.

**Stop:** ambiguous Main/Secondary identification, unsafe archive content,
qcow2 errors, or an external backing file.

**Evidence:** archive member manifest, input hashes, `qemu-img` metadata, and
overlay/backing relationship.

### Phase 5: Assemble and inspect the QEMU command

The launcher will construct a command equivalent to this design skeleton; the
actual paths and the CPU selected in Phase 2 are generated, not copied by hand:

```sh
qemu-system-aarch64 \
  -name aosvm-main \
  -machine virt,accel=hvf \
  -cpu host \
  -smp 2 \
  -m 2048 \
  -bios QEMU_EFI.fd \
  -drive file=aosvm-main-overlay.qcow2,if=none,id=aos-image,format=qcow2 \
  -device virtio-scsi-pci,id=scsi \
  -device scsi-hd,drive=aos-image \
  -netdev user,id=aosnet,net=10.0.0.0/24,host=10.0.0.1,dns=10.0.0.2,hostfwd=tcp:127.0.0.1:10022-10.0.0.100:22 \
  -device virtio-net-pci,netdev=aosnet,mac=52:54:00:41:4f:53 \
  -qmp unix:.run/aosvm-main.qmp,server=on,wait=off \
  -pidfile .run/aosvm-main.pid
```

The final launcher also attaches the serial console to a repository-owned Unix
socket and log. First boot stays attached to the terminal; background startup
is added only after the foreground path is proven.

Command inspection must confirm:

- `qemu-system-aarch64`, not `qemu-aarch64`;
- `accel=hvf` with no fallback accelerator;
- upstream EFI firmware;
- virtio-SCSI, preserving `/dev/sda`;
- qcow2 overlay, never the base disk, as the writable drive;
- stable locally administered MAC address;
- only loopback host forwarding;
- PID, QMP, serial socket, and logs under this repository's ignored paths.

**Pass:** a dry-run printout has no mutable base disk, broad listener, secret,
or unowned runtime path.

**Stop:** direct base-disk writes, a non-loopback forward, or a command that can
fall back to TCG.

### Phase 6: Perform the first serial boot

Start the Main Node in the foreground with:

- AArch64 `virt` machine;
- HVF acceleration;
- host CPU model if supported, otherwise the exact HVF CPU model qualified in
  Phase 2;
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

Explicit boot checkpoints:

1. QEMU reports HVF initialization without fallback;
2. upstream EFI starts;
3. GRUB selects an ARM64 kernel;
4. the kernel identifies the expected `virt` platform and virtio devices;
5. initramfs finds `/dev/sda` and the expected root partition;
6. the root filesystem mounts;
7. systemd reaches a login-capable target;
8. the serial console reaches a prompt.

Development-image console access uses the documented `root` account. Any
published default password is development-only and must never be reused as a
project secret or exposed beyond a loopback forward.

**Pass:** all eight checkpoints succeed under HVF and the prompt is stable.

**Stop:** kernel panic, illegal instruction, missing root disk, unexpected
`/dev/vda` dependency, repeated initramfs failure, or QEMU accelerator fallback.

**Evidence:** timestamped serial log and boot-duration fields in the manifest.

### Phase 7: Validate guest identity, boot state, and storage

From the serial console or loopback SSH:

- confirm `aarch64`/`arm64` architecture;
- record kernel and OS release;
- record the kernel command line and cgroup mode;
- inspect memory and the full block-device layout;
- confirm root is read-only and `/home` and `/var` have the intended writable
  behavior;
- record `/dev/sda6` state without provisioning or formatting it;
- record failed systemd units;

Representative observations:

```sh
uname -a
uname -m
cat /etc/os-release
cat /proc/cmdline
lsblk -o NAME,SIZE,FSTYPE,RO,MOUNTPOINTS
findmnt
systemctl is-system-running
systemctl --failed
```

**Pass:** the guest is ARM64, uses its own expected kernel, has the expected
partition roles, and has no unexplained boot-critical failure.

**Stop:** host architecture leakage, wrong disk topology, writable root without
an upstream explanation, corrupted filesystems, or a boot-critical failed unit.

### Phase 8: Run the guest kernel capability gate

Run non-destructive, self-cleaning functional probes from writable temporary
storage. Every created namespace, link, nftables table, traffic-control object,
mount, directory, and cgroup must have a unique `aos0-probe-*` name and a cleanup
trap.

| Capability | Required proof |
| --- | --- |
| cgroups v2 | Unified hierarchy plus a temporary unit/cgroup with an enforced resource limit |
| Namespaces | A child process successfully enters new mount, PID, IPC, UTS, and network namespaces |
| Seccomp | Kernel seccomp actions are present and `crun` reports seccomp support |
| Overlayfs | Create lower/upper/work/merged directories, mount, write, read, and unmount |
| Squashfs | Load/detect filesystem support; mount a generated fixture if tooling exists |
| veth and bridge | Create a network namespace, veth pair, and bridge; move/link interfaces; clean up |
| VLAN and VXLAN | Create and delete temporary VLAN and VXLAN links |
| IFB | Create and delete an IFB device |
| nftables/NAT | Add, list, and remove an isolated table and NAT rule set |
| Traffic control | Add and remove TBF, ingress, matchall, and mirred objects on test links |
| Quotas | Verify kernel/filesystem quota support on the partition used by AosCore |
| SELinux | Record policy presence and enforcing/permissive state; explain any deviation from upstream configuration |

Configuration evidence from `/proc/config.gz` or the installed kernel config is
recorded when available, but a successful functional probe is stronger. A
missing diagnostic utility is not automatically interpreted as a missing
kernel capability; the smoke test must distinguish those cases.

**Pass:** every mandatory feature either passes a functional probe or has
equivalent unambiguous evidence, and cleanup leaves no probe state behind.

**Stop:** a required kernel feature is unavailable, cannot be loaded, or fails
when exercised. Do not proceed to cloud provisioning hoping that it will repair
a guest-kernel deficiency.

**Evidence:** one result per capability with `pass`, `fail`, or
`not-tested-with-reason`; mandatory `not-tested` entries prevent final
acceptance.

### Phase 9: Prove the local OCI runtime without AosCloud

This gate verifies that the kernel facilities work together under the same OCI
runtime selected by AosVM:

1. record `crun` version and feature output;
2. construct an ephemeral minimal root filesystem from guest binaries and their
   runtime libraries under `/var/tmp/aos0-oci-probe`;
3. use a tracked, non-networked OCI test configuration with a memory limit and
   isolated PID, mount, IPC, UTS, and network namespaces;
4. run it directly with `crun`;
5. require a fixed English success marker and exit status 0;
6. verify that the container, cgroup, mounts, and temporary root filesystem are
   gone after cleanup.

This is deliberately a **local OCI probe**, not an Aos service deployment. The
full AosCloud desired-state -> Communication Manager -> Service Manager ->
`crun` lifecycle belongs to AOS-1 after provisioning.

**Pass:** a real isolated ARM64 process starts and exits through `crun`, with
the configured resource boundary and no residual runtime state.

**Stop:** `crun` is absent, cannot create namespaces/cgroups/mounts, or leaves
uncontrolled state.

### Phase 10: Classify AosCore's pre-provisioning state

Confirm installation and inspect the current status and logs for:

- `aos-iamanager` / `aos-iam.service`;
- `aos-servicemanager` / `aos-sm.service`;
- `aos-communicationmanager` / `aos-cm.service`;
- the configured `crun` runtime and AosCore storage paths.

Use the unit and binary names actually present in the release when they differ
from these expected names.

Cloud connection is not an acceptance requirement before provisioning. An
unprovisioned or certificate-related AosCore state is expected and must be
distinguished from a runtime failure.

Expected pre-provisioning conditions can include missing enrollment identity,
certificate, cloud authorization, or cloud connection. Blocking conditions
include a binary crash, missing library/kernel capability, unusable Aos storage,
OCI runtime registration failure, or unexplained SELinux denial.

**Pass:** all failures are classified, and only provisioning/cloud-dependent
failures remain.

**Stop:** any local AosCore component cannot initialize for a host, kernel,
storage, runtime, or policy reason.

### Phase 11: Validate networking as independent layers

Validate separately:

1. guest interface and static address `10.0.0.100/24`;
2. default route through `10.0.0.1`;
3. guest-to-host connection to the guest-visible host address;
4. outbound TCP by IP, without depending on ICMP;
5. DNS resolution;
6. outbound HTTPS with certificate validation;
7. host-to-guest SSH through `127.0.0.1:10022`;
8. macOS listener scope, proving the forward is not exposed on the LAN.

Do not use ping failure alone as evidence that QEMU user networking is broken;
the SLIRP backend can treat ICMP differently from TCP/UDP.

The image expects gateway and DNS at the same address, while QEMU user
networking normally separates them. If routing succeeds and DNS alone fails:

1. capture the failure before changing anything;
2. make a deterministic DNS override only in the disposable overlay;
3. relabel the changed file if SELinux requires it;
4. reboot and rerun the complete network test;
5. record the override in the manifest and automate it in `prepare`;
6. prove that recreating the overlay removes the override.

If that controlled overlay change is not reliable, evaluate QEMU `vmnet` next.
VirtualBox and a custom Yocto image remain later fallbacks. No fallback may
silently widen listener scope or require persistent host packet-filter changes.

**Pass:** outbound DNS/HTTPS and loopback SSH work, the host is reachable from
the guest for the later VISS path, and no service is exposed externally.

**Stop:** basic connectivity needs an undocumented image mutation, external LAN
exposure, or administrator-owned network configuration.

### Phase 12: Automate the owned VM lifecycle

Implement English-only commands for:

- `host-check` — validate architecture, HVF, QEMU, resources, and port scope;
- `download` — fetch and verify pinned inputs;
- `prepare` — extract and create the overlay;
- `start` — start only this repository's VM and write PID/QMP state;
- `console` — attach to the owned serial socket without starting another VM;
- `status` — report process, serial, SSH, and disk state;
- `stop` — request a clean guest shutdown through QMP, then use a bounded
  escalation only for the owned QEMU PID;
- `reset-overlay` — recreate only the named disposable overlay after explicit
  confirmation;
- `smoke-test` — perform non-destructive health checks and write a local run
  manifest.

The scripts must reject stale or ambiguous PID files and must never match or
terminate unrelated QEMU processes by name.

Lifecycle rules:

- acquire a per-VM lock before changing state;
- validate that a PID belongs to the expected QEMU binary and command before
  signaling it;
- request guest shutdown through QMP first;
- wait for a bounded interval while reporting progress;
- send a normal termination signal only to the verified owned PID if the guest
  does not exit;
- never use `killall`, broad process matching, or an unresolved path;
- remove stale PID/socket files only after proving that no owned process uses
  them;
- make `start`, `stop`, and `status` idempotent.

**Pass:** start/status/console/stop can be repeated and affect only this VM.

**Stop:** any lifecycle action relies on process names, broad deletion, or
ambiguous state.

### Phase 13: Prove restart, persistence, and reset behavior

- Cleanly shut down the guest.
- Start it again from the same overlay.
- Confirm the guest boots and retains an intentionally created harmless marker.
- Stop it again.
- Recreate the overlay and confirm the marker disappears while the verified
  base remains unchanged.

Also verify after each stop:

- no owned QEMU process remains;
- no unexpected TCP listener remains;
- no stale QMP or serial socket is treated as a running VM;
- the pristine base disk and firmware hashes are unchanged.

**Pass:** two normal boot/shutdown cycles succeed, intended overlay persistence
works, reset removes it, and the base remains identical.

**Stop:** base-image drift, leaked process/listener state, or a reset that can
target more than the named overlay.

### Phase 14: Record and commit the accepted baseline

Update this document with:

- exact QEMU package and version;
- final launch parameters;
- boot and shutdown timing;
- chosen network backend and DNS solution;
- AosCore component status before provisioning;
- kernel capability matrix and local OCI result;
- known warnings;
- smoke-test result;
- whether AOS-1 should use one or two Nodes.

Commit only scripts, examples, tests, and sanitized documentation. Keep raw
serial logs and manifests ignored unless a specific sanitized fixture is
required for a test.

Before committing:

- run secret and large-file checks;
- inspect all new tracked files;
- confirm no absolute user-specific paths are embedded in examples;
- confirm all user-visible program text is English;
- confirm the working tree contains only intended AOS-0 changes.

**Pass:** the accepted baseline is reproducible from a fresh overlay, the
sanitized evidence is committed, and the working tree is clean.

## Acceptance checklist

- [ ] Official archive matches the pinned SHA-256.
- [ ] Base image remains unchanged after every test.
- [ ] Native ARM64 QEMU starts the Main Node with HVF and no TCG fallback.
- [ ] EFI, GRUB, the upstream AosVM kernel, initramfs, and root filesystem boot.
- [ ] Serial console reaches a login prompt.
- [ ] Guest reports ARM64 architecture.
- [ ] Guest disk is `/dev/sda` with the expected partition and mount roles.
- [ ] The mandatory guest-kernel capability matrix passes.
- [ ] A local OCI bundle runs successfully with `crun` and leaves no residue.
- [ ] No unexplained local AosCore component failure exists.
- [ ] Outbound HTTPS and DNS work.
- [ ] The guest can reach the macOS host for the later VISS path.
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
limited to the expected unprovisioned state. This means AOS-1 can focus on SDK
provisioning, certificates, and the first cloud-managed service instead of
debugging the VM foundation.

Stop and reconsider the VM base if HVF cannot boot the image, a mandatory guest
kernel capability or local `crun` execution fails, the released disk requires
an invasive persistent patch, or network access requires exposing host services
to the external LAN.

## Failure routing

| Symptom | First investigation | Decision boundary |
| --- | --- | --- |
| HVF initialization fails | Native QEMU build, macOS support, selected CPU model | No TCG acceptance |
| EFI does not find a boot target | Firmware path, qcow2 selection, `virt` machine | Do not edit base disk |
| Kernel cannot find root | virtio-SCSI topology and `/dev/sda` assumptions | Do not switch devices casually |
| Kernel boots but capability gate fails | Release kernel config/modules and functional probe log | No provisioning until resolved |
| Only DNS fails | QEMU DNS address versus image static DNS | Overlay-only deterministic override |
| `crun` probe fails | cgroups, namespaces, seccomp, mounts, SELinux | No AOS-1 service deployment |
| AosCore reports no identity/certificate/cloud | Confirm it is strictly provisioning-dependent | Expected in AOS-0 |
| AosCore binary crashes or cannot initialize storage/runtime | Local journal, policy, filesystem, kernel | Blocking local defect |

## Upstream references

- [AosVM v6.1.0 release](https://github.com/AosEdge/meta-aos-vm/releases/tag/v6.1.0)
- [AosVM upstream QEMU launcher](https://github.com/AosEdge/meta-aos-vm/blob/v6.1.0/scripts/aos_vm.sh)
- [AosVM common kernel configuration](https://github.com/AosEdge/meta-aos-vm/blob/v6.1.0/meta-aos-vm-common/recipes-kernel/linux/files/common_node.cfg)
- [AosCore integration requirements](https://github.com/AosEdge/meta-aos/blob/v9.1.0/doc/integration.md)
- [QEMU system emulation](https://www.qemu.org/docs/master/system/index.html)
- [QEMU ARM `virt` platform](https://www.qemu.org/docs/master/system/arm/virt.html)
