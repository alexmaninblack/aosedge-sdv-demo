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
| Phase 3: pinned release download | Complete — 2026-08-12 | Pass |
| Phase 4: immutable inputs and overlay | Complete — 2026-08-13 | Pass |
| Phase 5: QEMU command assembly | Complete — 2026-08-13 | Pass |
| Phase 6: first serial boot | Complete — 2026-08-13 | Pass |
| Phase 7: guest identity and storage | Complete — 2026-08-13 | Pass |
| Phase 8: guest kernel capability gate | Complete — 2026-08-13 | Pass |
| Phase 9: local OCI runtime gate | Complete — 2026-08-13 | Pass |
| Phase 10: AosCore pre-provisioning state | Complete — 2026-08-13 | Pass with tracked ARM64 overlay fix |
| Phase 11: layered networking | Complete — 2026-08-13 | Pass with tracked loopback DNS bridge |
| Phase 12: owned VM lifecycle | Complete — 2026-08-13 | Pass |
| Phase 13: persistence and overlay reset | Complete — 2026-08-13 | Pass |
| Phase 14: accepted baseline | Complete — 2026-08-13 | Pass; go to AOS-1 with one qualified Main Node |

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

QEMU 11.1.0, the next Homebrew ARM64 bottle, was additionally qualified on
2026-08-13 against the same fixed `virt-11.0,accel=hvf` contract. An isolated
fresh overlay reached the real OpenSSH banner in 20 seconds, and its qcow2
integrity check passed after shutdown. The launcher accepts 11.0.3 and 11.1.0
only; later releases remain fail-closed until independently qualified.

The original 11.0.3 qualification used empty, diskless probes only; no AosVM
image or guest OS was started in that phase. QEMU successfully created and ran
two `host` vCPUs with HVF, created
the required virtio-SCSI and virtio network devices, accepted the planned user
network, and bound the SSH forward only to loopback. The probes exited cleanly,
leaving no QEMU process or listener on port 10022.

The installed binary also contains TCG, but the accepted launcher configuration
selects `virt-11.0,accel=hvf` explicitly and defines no accelerator fallback.
TCG does not satisfy the AOS-0 acceptance criteria.

### Phase 3 observed baseline

| Field | Verified value |
| --- | --- |
| Release | AosVM `v6.1.0` |
| Asset | `aos-vm-image-qemuarm64-6.1.0.tar.xz` |
| Download source | Official GitHub release over HTTPS |
| Effective asset host | `release-assets.githubusercontent.com` over HTTPS |
| Exact size | 381,515,220 bytes |
| SHA-256 | `db8fef0188f4ba0930aecafecdfe4ad063a3cf27a48e8649fc5050f9b3117e04` |
| Local cache | `.cache/aosvm/v6.1.0/qemuarm64/` |
| Check completed | `2026-08-12T23:37:41+0200` (`CEST`) |

The tracked `scripts/aosvm download` command uses a temporary `.partial` file,
HTTPS-only redirects, an allowlist for the effective GitHub asset host, retry
and resume support, exact size verification, SHA-256 verification, and an
atomic final rename. A complete cached file is reverified on every invocation.
The downloader rejects corrupt cached files, oversized partial files, and
symbolic links at either cache target.

The verified archive is ignored by Git. It has not been extracted, inspected,
mounted, or executed; those actions begin in Phase 4.

### Phase 4 observed baseline

The verified archive contains exactly three top-level regular files and no
directory, symbolic link, hard link, device node, or nested path:

| Artifact | File size | SHA-256 | Prepared mode |
| --- | ---: | --- | --- |
| `aos-vm-main-qemuarm64.qcow2` | 593,428,480 bytes | `8cbc4bd331650fbae7b54ad5b11b00e36e275cea00298327629e568422023fc4` | `0444` |
| `aos-vm-secondary-qemuarm64.qcow2` | 573,833,216 bytes | `c6b687c180bab7621d5680c6e44894b531edc8a64cd6851afd467cec2dc193f6` | `0444` |
| `QEMU_EFI.fd` | 2,097,152 bytes | `30f7042c23b81c28b8196a76f4af6bcf10046f08049c9d78b4387472c5bbcd10` | `0444` |

Both upstream disks are standalone qcow2 1.1 images with no backing file, a
virtual size of 6,997,147,648 bytes, a clean dirty flag, and `corrupt=false`.
QEMU 11.0.3 reported no errors for either image.

The active Main Node overlay is:

| Field | Prepared value |
| --- | --- |
| Path | `.local/aosvm-main-overlay.qcow2` |
| Format | qcow2 1.1 |
| Virtual size | 6,997,147,648 bytes (approximately 6.52 GiB) |
| Initial file size | 196,720 bytes |
| Initial allocated disk space | approximately 196 KiB |
| Mode | `0600` |
| Backing format | qcow2 |
| Backing file | Verified absolute path to the immutable Main Node image |
| Integrity | Clean; `qemu-img check` found no errors |
| Check completed | `2026-08-13T08:32:40+0200` (`CEST`) |

The absolute backing path deliberately prevents ambiguous resolution when QEMU
is launched from a different working directory. If the repository is moved,
the disposable overlay must be recreated by a lifecycle command rather than
edited by hand. The upstream base images remain valid and unchanged.

The tracked `scripts/aosvm prepare` command verifies the archive manifest before
extraction, extracts only the exact pinned manifest, verifies every file by
size and SHA-256, validates both qcow2 images, and creates the overlay through a
temporary path. It is idempotent and refuses an incomplete base set, a corrupt
existing overlay, an unexpected backing file, or a symbolic-link target.

All archive, base, firmware, and overlay files remain ignored by Git. The
Secondary Node is prepared for upstream-release completeness but is not attached
or used in AOS-0. No firmware, disk, or guest code has been executed yet.

### Phase 5 observed baseline

`scripts/aosvm start --dry-run` revalidates the prepared artifacts, exact file
modes, qcow2 backing chain, native QEMU binary, QEMU version, HVF availability,
machine, CPU model, required devices, runtime paths, and loopback port before it
prints the shell-quoted argument vector. It does not start a VM.

The accepted Phase 6 command contract is:

| Field | Qualified value |
| --- | --- |
| QEMU | `/opt/homebrew/bin/qemu-system-aarch64` 11.0.3, native ARM64 |
| VM name | `aosvm-main` |
| Machine | `virt-11.0,accel=hvf` with no accelerator fallback |
| CPU and memory | `host`, 2 vCPUs, 2,048 MiB RAM |
| Defaults | `-nodefaults` |
| Firmware | Verified immutable `QEMU_EFI.fd` |
| Writable disk | `.local/aosvm-main-overlay.qcow2` only |
| Disk topology | `virtio-scsi-pci` -> `scsi-hd` -> `aos-image` |
| User network | `10.0.0.0/24`, host `10.0.0.1`, DNS proxy `10.0.0.2` |
| SSH forward | `127.0.0.1:10022` -> `10.0.0.100:22` |
| NIC | `virtio-net-pci`, MAC `52:54:00:41:4f:53` |
| Serial | Repository-owned Unix socket with append-only timestamped local log |
| Control | Repository-owned QMP Unix socket; HMP monitor disabled |
| Display | Disabled |
| PID | Repository-owned PID file |
| Runtime directory modes | `0700` |
| Check completed | `2026-08-13T08:47:14+0200` (`CEST`) |

The command does not contain TCG, KVM, `qemu-aarch64` user-mode execution,
`-daemonize`, `-nographic`, a graphical display, a non-loopback host forward,
the Secondary Node disk, or the immutable Main Node base disk as a QEMU drive.
The absolute base path appears only inside the overlay metadata validated by
`qemu-img`; QEMU receives the overlay path.

Dry-run rejects an unqualified QEMU version or architecture, unavailable HVF or
devices, changed input hash/mode/backing chain, privileged or invalid SSH port,
occupied SSH port, symbolic-link runtime/log paths, unsafe Unix socket length,
and any pre-existing PID or control socket. Contract tests confirmed that no
QEMU process, port listener, PID, socket, or serial log remains after dry-run.

Phase 5 did not boot EFI or execute guest code. The first real QEMU start and
serial boot checkpoints belong exclusively to Phase 6.

### Phase 6 observed baseline

The first real start used `scripts/aosvm start --foreground` and exactly the
Phase 5 argument contract. QEMU 11.0.3 remained alive with
`virt-11.0,accel=hvf` and `-cpu host`; no fallback accelerator was configured.
The VM ran without a graphical window, and QMP reported `status: running`.

| Checkpoint | Observed result |
| --- | --- |
| Start | `2026-08-13T08:56:51.190008+0200` (`CEST`) |
| EFI | Upstream EDK II firmware selected the virtio-SCSI QEMU hard disk |
| GRUB | GRUB 2.12 selected the fallback `boot` entry after a 5-second timeout |
| Kernel | Linux `6.6.123-yocto-standard`, compiled for AArch64 |
| Disk | 6.52 GiB SCSI disk as `/dev/sda`, partitions `sda1` through `sda6` |
| Root | `/dev/sda3` mounted as read-only ext4 by the initramfs |
| Guest identity | systemd detected `qemu` virtualization and `arm64` architecture |
| Operational target | Multi-User System queued; serial getty reached a stable prompt |
| Prompt | `AosCore 6.1.0 main ttyAMA0` followed by `main login:` |
| First prompt time | 67.307 seconds after initial EFI output |
| SSH forward | Guest SSH accepted TCP connections through `127.0.0.1:10022` |
| Graceful stop | QMP ACPI power-down; guest powered off in approximately 14.6 seconds |
| Disk integrity | Post-shutdown `qemu-img check` reported no errors |
| Check completed | `2026-08-13T09:00:00+0200` (`CEST`) |

The initial start performed one clean automatic reboot before presenting the
prompt. Before that reboot, SELinux rejected access to an unlabeled writable
partition and `rpcbind` and the persistent journal could not start. systemd
then synchronized and unmounted every filesystem and rebooted normally. On the
second boot, `rpcbind` and the journal started successfully and the login
prompt appeared. Phase 7 confirmed that the upstream SELinux autorelabel unit
performs a full relabel and explicitly reboots when `/var/aos/.autorelabel` is
present. The marker is removed after that one-time initialization.

Known upstream boot warnings are:

- GRUB could not load its first attempted `EFI/BOOT/grub.cfg` path, then used
  the visible fallback `boot` entry and successfully loaded the kernel;
- GRUB reported that serial port `com0` was not present, while Linux and the
  serial getty correctly used the ARM PL011 console exposed as `ttyAMA0`;
- the initramfs reported that the Aos update workdirs device did not exist,
  which is expected before the later provisioning and storage-validation
  phases.

None of these warnings caused a kernel panic, illegal instruction, missing
root disk, repeated initramfs failure, or accelerator fallback. The QEMU
process accepted an ACPI power-down through its private QMP socket; the guest
cleanly unmounted `sda4` and `sda5`, synchronized the SCSI disk, and powered
off. QEMU removed its PID and socket files on exit.

The writable overlay grew from 196,720 bytes to approximately 38.4 MB. It has a
clean dirty flag, `corrupt=false`, and the expected immutable backing file. The
upstream Main Node image and EFI firmware still match their pinned SHA-256
values.

### Phase 7 observed baseline

The initialized overlay completed the next start in one boot with no automatic
reboot. Upstream EFI output began at `2026-08-13T09:22:15.810785+0200` and the
serial login prompt appeared 47.887 seconds later. systemd recorded 5.955
seconds in the kernel and 30.439 seconds in userspace, or 36.394 seconds to its
operational target after the kernel clock started.

| Field | Observed value |
| --- | --- |
| Architecture | `aarch64`, two virtual CPUs |
| OS | AosCore `6.1.0 (scarthgap)` |
| Kernel | `6.6.123-yocto-standard`, AArch64, SMP PREEMPT |
| Memory | 1,962,964 KiB total, no swap |
| Cgroups | Unified cgroups v2; `cpuset cpu io memory pids` controllers |
| Security | SELinux enabled with the `aos` policy in Enforcing mode |
| Kernel root argument | `root=/dev/sda3 rootwait ro rootfstype=ext4` |
| Operational targets | `multi-user`, `getty`, and `network-online` active |
| Pre-provisioning service | `aos-iam-prov.service` active and running |
| Provisioning state | IAM reports the node as `unprovisioned` |
| Automated guest gate | `tests/guest/aosvm-phase7-test`, exit status 0 |
| Clean shutdown | Guest `systemctl poweroff`; all filesystems unmounted |
| Post-shutdown disk check | No qcow2 errors; immutable hashes unchanged |
| Check completed | `2026-08-13T09:40:52+0200` (`CEST`) |

The complete upstream disk layout is:

| Device | Size | Filesystem | Observed role |
| --- | ---: | --- | --- |
| `/dev/sda1` | 256 MiB | FAT | `boot_a`, not mounted at runtime |
| `/dev/sda2` | 256 MiB | FAT | `boot_b`, not mounted at runtime |
| `/dev/sda3` | 1 GiB | ext4 | `/`, mounted read-only |
| `/dev/sda4` | 512 MiB | ext4 | `/home`, mounted read-write with `noatime` |
| `/dev/sda5` | 512 MiB | ext4 | `/var`, mounted read-write; also backs `/etc/machine-id` |
| `/dev/sda6` | 4 GiB | No signature | Aos data partition, unopened and unmounted |

`/dev/sda6` has no filesystem signature, `/dev/aosvg` does not exist, and the
planned `downloads`, `states`, `storages`, and `workdirs` logical volumes and
mounts are absent. This is the correct non-destructive state before SDK
provisioning. Phase 7 did not format, mount, unlock, or otherwise initialize the
partition.

systemd reports `degraded` because `nfs-server.service` is the sole failed
unit. Its `exportfs -r` precondition references `/var/aos/states` and
`/var/aos/storages`, which do not exist until the Aos data partition is opened.
The failure does not block the operational targets or provisioning IAM. The
normal IAM, Communication Manager, and Service Manager units are conditionally
inactive while the node is unprovisioned. This is a fully explained
pre-provisioning condition, not a boot-critical failure.

The first-boot reboot is now confirmed as intentional. The upstream
`selinux-autorelabel.service` checks for `/var/aos/.autorelabel`, performs a
forced filesystem relabel, removes the marker, and invokes `/sbin/reboot`.
Afterwards the writable paths carry their intended SELinux types, the marker is
absent, and subsequent starts do not repeat the reboot.

One issue remains outside the Phase 7 acceptance gate: the guest clock stayed
at the image's 2025 timestamp even though `systemd-timesyncd` was active. This
must be resolved and tested with DNS/outbound connectivity before any TLS,
certificate enrollment, or cloud provisioning. No clock or network setting was
changed in Phase 7.

The serial log is mode `0600`, ignored by Git, and remains local because an
interactive development login was used. No credential, device identifier, raw
journal, or serial transcript is stored in tracked files. The reusable guest
test contains only read-only validation commands and no access credential.

### Phase 8 observed baseline

The tracked `tests/guest/aosvm-phase8-test` ran as root inside the initialized,
unprovisioned Main Node. It creates every object under a unique
`aos0-probe-*` name, records one result per required capability, and removes its
temporary cgroup, OCI bundle, mounts, network namespace, links, nftables table,
traffic-control objects, RAM-disk filesystem, and loaded probe modules. It does
not access the cloud or initialize `/dev/sda6`.

| Capability | Result | Functional evidence |
| --- | --- | --- |
| cgroups v2 | Pass | A transient systemd cgroup enforced `memory.max=16777216`, `pids.max=8`, and `cpu.max=50000 100000` |
| Mount, PID, IPC, UTS, and network namespaces | Pass | `crun` started PID 1 with a probe hostname and five namespace inode values distinct from the parent |
| Seccomp | Pass | Kernel actions include kill, trap, errno, notification, trace, log, and allow; `crun` applied `SCMP_ACT_ERRNO` to `getcwd` |
| Overlayfs | Pass | A temporary overlay mount read its lower layer and stored a write in its upper layer |
| SquashFS and loop | Pass | The boot initramfs contains matching `squashfs.ko` and `loop.ko`; its update script mounts `*.squashfs` through loop before `switch_root` |
| veth and bridge | Pass | A veth peer was moved into a new network namespace and its host peer attached to a temporary bridge |
| VLAN and VXLAN | Pass | VLAN ID 100 and VXLAN ID 4242 links were created, inspected, and deleted |
| IFB | Pass | A temporary IFB link was created, inspected, and deleted |
| nftables/NAT | Pass | An isolated IPv4 table, NAT postrouting chain, and masquerade rule were added, listed, and removed |
| Traffic control | Pass | TBF, ingress, matchall, and mirred-to-IFB objects were applied to temporary links |
| Quotas | Pass | An ext4 filesystem created on volatile `/dev/ram15` enforced a 64 KiB user hard limit |
| SELinux | Pass | Kernel support is built in; policy `aos` is loaded and enforcing |
| Probe cleanup | Pass | No probe mounts, namespaces, links, nftables tables, or cgroups remained |

The corrected final run completed with **13 passes and no failures**. The
original SquashFS check incorrectly attempted `modprobe squashfs` after
`switch_root`, where the module is intentionally absent. The released boot
partition contains a separate initramfs with `squashfs.ko`, `loop.ko`, and
`overlay.ko`, all built for `6.6.123-yocto-standard`. Its `95-aosupdate` script
mounts the rootfs update image using `mount -t squashfs -o loop` before
`99-finish` switches to the steady-state ext4 rootfs.

This split is deliberate. The pinned `meta-aos` recipes recommend SquashFS,
loop, and overlay for the initramfs update module, while the Service Manager
runtime recommends overlay and the networking modules but not SquashFS or
loop. Omitting the two update-only modules from the steady-state rootfs reduces
its footprint without removing the capability from the execution environment
that uses it. No AosVM rebuild or rootfs patch is required.

The guest was then powered off through systemd. It unmounted all filesystems,
synchronized the SCSI disk, and powered down; no QEMU process, listener, PID
file, or runtime socket remained. `qemu-img check` reported no overlay errors,
and the immutable Main Node, Secondary Node, and firmware SHA-256 values still
matched the pinned release.

The full serial output remains local and ignored. The reusable test and this
sanitized result contain no credential, certificate, device identifier, or
cloud account data.

### Phase 9 observed baseline

The tracked `tests/guest/aosvm-phase9-test` and
`tests/guest/aosvm-phase9-config.json` ran as root inside the same initialized,
unprovisioned Main Node. The gate used the image's own `crun` runtime directly;
it did not invoke AosCore, contact AosCloud, or initialize `/dev/sda6`.

| Check | Result | Functional evidence |
| --- | --- | --- |
| Runtime identity | Pass | `crun 1.14.3.0.0.0.8-89d44-dirty`, commit `89d44467e3b410b73f2065756a12789be45b855b`, OCI spec 1.0.0 |
| Runtime features | Pass | `crun features` reports OCI 1.0.0–1.1.0+dev, cgroups v2, systemd cgroups, and seccomp enabled |
| ARM64 process | Pass | The container ran the guest BusyBox as AArch64 PID 1 and emitted the fixed `AOSVM_PHASE9_OCI_OK` marker once before exiting 0 |
| Namespace isolation | Pass | Mount, PID, IPC, UTS, network, and cgroup namespace inode values differed from the parent |
| Filesystem boundary | Pass | The OCI rootfs rejected a write while a 1 MiB `/tmp` tmpfs accepted and returned probe data |
| Network boundary | Pass | A fresh network namespace had no externally usable interface; only loopback and the kernel-created down `sit0` device were present |
| Resource boundary | Pass | The live container cgroup enforced `memory.max=33554432`, `pids.max=16`, and `cpu.max=50000 100000` |
| Privilege boundary | Pass | The OCI process had `noNewPrivileges` and empty bounding, effective, inheritable, permitted, and ambient capability sets |
| Cleanup | Pass | The container, cgroup, probe mounts, lock, bundle, and ephemeral rootfs were absent after exit |

The minimal rootfs was constructed from the guest's own AArch64 BusyBox,
runtime linker, and libraries under volatile `/var/tmp/aos0-oci-probe`. The
tracked OCI configuration made the rootfs read-only, mounted separate `/proc`,
`/sys`, `/dev`, and `/tmp` filesystems, and declared all resource and namespace
constraints. This is a complete local OCI acceptance result, not a substitute
for the cloud-driven Service Manager lifecycle that begins after provisioning
in AOS-1.

### Phase 10 observed baseline

The tracked `tests/guest/aosvm-phase10-test` classified the installed AosCore
components without provisioning the Unit, starting condition-gated services,
contacting AosCloud, or initializing `/dev/sda6`.

| Check | Result | Classification |
| --- | --- | --- |
| Component installation | Pass | AArch64 `aos_iam_app`, `aos_sm_app`, and `aos_cm_app` all load and report `v9.1.0-1-g9eec`; the core library reports the same release |
| Provisioning IAM | Pass | `aos-iam-prov.service` is active with zero restarts and runs IAM in provisioning mode; its journal reports `state=unprovisioned` and no owned PKCS#11 token |
| Runtime services | Pass | `aos-iam.service`, `aos-sm.service`, `aos-cm.service`, and `aos-provfirewall.service` are inactive because their explicit `/var/aos/.provisionstate` condition is false, not because their binaries crashed |
| OCI registration | Pass | Service Manager selects the `crun` container runtime with `/var/aos/states` and `/var/aos/storages`; `crun` reports cgroups v2 and seccomp support |
| Aos data storage | Pass | `/dev/sda6` remains unsigned and unmounted; `/dev/aosvg` and the four generated Aos mount sources are absent; their unit conditions are false as expected |
| NFS failure | Pass, classified | `nfs-server.service` is the only failed unit because `/var/aos/states` and `/var/aos/storages` do not exist until provisioning opens the Aos data partition |
| Certificates and identity | Pass, classified | The trusted Aos root CA and SoftHSM library are installed; the provisioning marker, PKCS#11 user PIN, subjects, and owned tokens are intentionally absent |
| Policy and stability | Pass | SELinux is enforcing, no current-boot AVC denial is present, and no AosCore crash, panic, illegal instruction, core dump, or OOM evidence exists |
| ARM64 boot runtime | Pass after overlay fix | Both boot partitions contain `/EFI/BOOT/bootaa64.efi`, and Service Manager now names that loader while managing partitions 1 and 2 |
| Restart persistence | Pass | A clean reboot preserved the compatibility correction and the full Phase 10 gate passed again |

One upstream image defect was found and corrected only in the disposable
overlay. The pinned `AosEdge/meta-aos-vm` `v6.1.0` source commit
`b13320898a2ed1cce504f90f70451638232d6a83` supplies the same Main Node
`sm.cfg` to `qemuarm64` and hard-codes `/EFI/BOOT/bootx64.efi`. The released
ARM64 boot partitions instead contain `/EFI/BOOT/bootaa64.efi` and no x86
loader. This is functionally significant: the installed Aos core v9.1.0 source
commit `4475d18f9e5e311b9b7e003a34c5ba8907ce596e` passes the configured loader
path to `efi_generate_file_device_path_from_esp` when Service Manager creates a
missing EFI Boot entry.

The tracked `scripts/guest/aosvm-apply-arm64-compat` helper verifies both boot
partitions read-only, accepts only the exact known old or corrected value,
changes `sm.cfg` atomically, preserves its mode, owner, and SELinux context,
syncs the overlay, and returns `/dev/sda3` to read-only. Repeated execution is a
no-op. The upstream base qcow2 remains unchanged. The preferred long-term fix
is an architecture-specific loader value in `meta-aos-vm`; the local helper
must be removed once a pinned official release contains that correction.

Phase 10 passes because all present failures are either explicit
pre-provisioning conditions or the resolved ARM64 configuration mismatch. No
remaining local host, kernel, runtime, storage, binary, or policy defect blocks
Phase 11. This result does not claim that runtime IAM, SM, or CM have completed
their post-provisioning startup; that acceptance belongs to AOS-1.

### Phase 11 observed baseline

The unchanged guest baseline had the correct `10.0.0.100/24` address and
default route through `10.0.0.1`. Outbound TCP by IP and a guest-to-host TCP
probe also passed. DNS failed because the image named the gateway and its own
local forwarder as upstreams, while QEMU presents its virtual DNS service at
`10.0.0.2`. Pointing the guest at that address exposed a second host-specific
problem: libslirp selected the first DNS server reported by macOS, which was
unreachable in the active corporate network configuration even though later
macOS resolvers worked.

The accepted design preserves QEMU user networking and adds no TAP device,
bridge, packet-filter rule, administrator privilege, or external listener:

```text
guest applications -> 10.0.0.100:53 (image dnsmasq)
                   -> 10.0.0.1:18053 (QEMU host mapping)
                   -> 127.0.0.1:18053 (tracked macOS DNS bridge)
                   -> active macOS resolvers with bounded failover
```

The launcher now starts `scripts/host/aosvm-dns-bridge` before QEMU. The bridge
supports UDP and TCP DNS, accepts only DNS queries, binds both sockets only to
`127.0.0.1`, reads the current macOS resolver set through `scutil --dns`, and
fails over between upstreams. It re-reads that set every five seconds, forces
an immediate refresh after a host scheduling gap or when all current
upstreams fail, and retries a failed query once with the refreshed set. During
the brief interval in which macOS publishes no resolver while changing
networks, it retains the last known set and keeps checking for recovery. The
listener PID therefore remains stable across Mac sleep, Wi-Fi roaming, and
ordinary network changes. It and QEMU are cleaned up together; the timestamped
bridge log and PID remain ignored local runtime state.

A post-provision mobility regression on 2026-08-14 confirmed the need for the
refresh contract. The Mac slept on one network and woke on another; QEMU and
all guest core services remained active, but the original bridge process still
held the previous resolver set. Guest Communication Manager then reported
temporary DNS failures and the cloud Unit became offline. The revised bridge
passed resolver-transition unit tests and a live loopback query on an isolated
test port. After one clean persistent-VM restart, `dns-check`, guest DNS, guest
time, and the post-provision core gate passed. AosCloud again reported the
single target Unit online with monitoring present, and the installed Hello
World instance returned to `active` without a new deployment or any identity
change.

The idempotent `scripts/guest/aosvm-apply-qemu-network-compat` helper changes
only the disposable overlay. It configures `systemd-resolved` to use the
image's existing `dnsmasq` on `10.0.0.100` and configures that forwarder with
`server=10.0.0.1#18053`. The helper accepts only the known released,
intermediate, or final states, installs both files atomically, preserves owner,
mode, and SELinux context, syncs storage, and returns `/dev/sda3` to read-only.
Recreating the overlay restores the released files and therefore removes this
guest-side compatibility adjustment; the immutable base is never changed.

The tracked host and guest gates passed before and after a clean reboot:

| Layer | Result | Functional evidence |
| --- | --- | --- |
| Guest interface | Pass | `enp0s2`, MAC `52:54:00:41:4f:53`, and `10.0.0.100/24` matched the contract |
| Default route | Pass | `10.0.0.1` remained the static gateway |
| Outbound TCP by IP | Pass | TCP port 443 was reachable without DNS or ICMP dependency |
| Guest-to-host | Pass | The guest received a fixed marker from a temporary loopback-only Mac TCP service through `10.0.0.1` |
| DNS | Pass | Both `systemd-resolved` and ordinary libc/BusyBox resolution succeeded through guest dnsmasq and the Mac bridge |
| Time | Pass | `systemd-timesyncd` contacted `time3.google.com`, reached stratum 1, and retained a synchronized 2026 clock after reboot |
| HTTPS | Pass | `docs.aosedge.tech` completed an HTTPS request and OpenSSL returned certificate verification code 0 |
| Host-to-guest SSH | Pass | `127.0.0.1:10022` returned the guest OpenSSH banner |
| Exposure | Pass | SSH and both DNS sockets were bound only to loopback and were unreachable on the Mac LAN address |
| Restart and cleanup | Pass | The complete host and guest gates passed after reboot; clean poweroff left no QEMU/DNS process, listener, or owned runtime PID/socket |

The final guest clock was `2026-08-13T12:11:25Z`, with three NTP packets,
approximately 17.8 ms delay, and sub-millisecond offset. Post-shutdown
`qemu-img check` reported no overlay errors. The immutable Main Node, Secondary
Node, and firmware SHA-256 values remained exactly pinned. No provisioning,
certificate enrollment, AosCloud connection, credential capture, or LAN
exposure occurred.

### Phase 12 observed baseline

The tracked `scripts/aosvm` entry point now owns the complete host lifecycle.
All user-visible launcher and test text is English. The implementation uses a
private per-VM lock, exact PID files, QMP and serial Unix sockets, and a small
allowlisted QMP client. It validates the QEMU executable and complete owned
command, links QEMU and the DNS bridge to the recorded supervisor through
their parent PIDs, and rejects stale, unrelated, symbolic-link, or ambiguous
runtime state.

The qualified command behavior is:

| Command | Qualified result |
| --- | --- |
| `host-check` | Passed macOS ARM64, HVF, 48 GiB memory, disk minimum, QEMU 11.0.3, and loopback-port checks |
| `start` | Started a detached supervisor, DNS bridge, and QEMU; remained running after an explicit `SIGHUP` |
| repeated `start` | Reported the already-running owned VM without starting a second process |
| `status` | Verified exact supervisor/QEMU/DNS ownership, QMP running state, loopback SSH/DNS listeners, serial socket, and overlay |
| `console` | Attached only to the owned serial socket and displayed `main login:`; `Ctrl-C` detached without stopping the VM |
| `smoke-test` | Waited up to a bounded guest-readiness timeout, verified the OpenSSH banner, QMP, and shared read-only qcow2 integrity, then wrote a mode-0600 ignored JSON manifest |
| `dns-check` | Performed a bounded public A-record lookup through the owned loopback bridge without exposing the returned address or changing VM state |
| `stop` | Requested `system_powerdown` through QMP, waited for guest exit, removed owned runtime state, and passed exclusive `qemu-img check` |
| repeated `stop` and stopped `status` | Reported the already-stopped state without error or broad cleanup |
| `reset-overlay --confirm` | Rejected missing confirmation and passed atomic recreation and metadata checks against an isolated disposable test overlay |

The start gate deliberately means **QEMU is running**, not that all guest
services are ready. The smoke test owns the separate readiness contract and
waits up to 90 seconds for the guest SSH banner. The first observed boot
reached QEMU running state in roughly 10 seconds and the serial login prompt in
roughly 37 seconds. Shutdown is bounded: QMP is tried for up to 90 seconds,
then `TERM` may be sent only after revalidating the exact owned QEMU PID.

No command uses `killall`, broad process-name matching, administrator
privilege, LAN listeners, or an unverified PID. Static safety gates also prove
that an unrelated live PID remains alive, a nonexistent PID is rejected, a
concurrent lifecycle lock blocks mutation, and stopped smoke testing fails
closed. A stopped `dns-check` also fails closed before making a network query.
Phase 13 subsequently qualified persistence and destructive reset on the real
working overlay.

### Phase 13 observed baseline

The tracked `tests/guest/aosvm-phase13-test` placed one harmless mode-0600,
root-owned marker on `/home`, which is the writable `/dev/sda4` partition. A
clean QMP shutdown, exclusive qcow2 check, and second full boot preserved the
marker exactly. Volatile `/tmp` did not survive the reboot, proving the result
did not depend on temporary guest state.

After a second clean shutdown, `scripts/aosvm reset-overlay --confirm`
atomically recreated only `.local/aosvm-main-overlay.qcow2` from the verified
Main Node backing image. The next boot proved all three expected reset effects:

- the `/home` marker was absent;
- the Service Manager loader returned to the released x86 path;
- network DNS and dnsmasq configuration returned to their released values.

The released configuration observations matter because they prove that reset
replaced the complete overlay instead of merely deleting the test marker. The
tracked ARM64 loader and QEMU DNS compatibility helpers were then transferred
to guest `/tmp`, matched against their repository SHA-256 values, applied, and
run a second time to prove idempotency. After another clean reboot, the Phase
10 pre-provisioning gate and both Phase 11 host and guest gates passed again,
including verified HTTPS, guest-to-host access, DNS failover, loopback-only
SSH/DNS listeners, and LAN isolation.

Reset also regenerated the guest SSH host key. Strict host-key checking
rejected the stale local key. The new ED25519 fingerprint was independently
read from `/var/ssh/ssh_host_ed25519_key.pub` through the serial console and
from the owned loopback SSH forward; only the exact matching public key was
then written to ignored `.run/aosvm-known-hosts`.

The tracked `tests/host/aosvm-phase13-stopped-gate` passed before testing,
after both persistence stops, immediately after reset, after compatibility
recovery, and at final shutdown. Every pass proved:

- no owned QEMU or DNS bridge process remained;
- ports `10022` and `18053` had no remaining listener;
- no owned PID, QMP socket, serial socket, or lifecycle lock remained;
- the overlay was a healthy mode-0600 qcow2 with the exact backing file;
- Main Node, Secondary Node, and EFI size, mode, and SHA-256 stayed pinned.

The VM is stopped. The active overlay contains no Phase 13 marker and retains
the qualified ARM64 and DNS compatibility state. No provisioning, certificate
enrollment, cloud connection, external listener, or administrator privilege
was introduced.

### Phase 14 accepted baseline

The accepted AOS-0 baseline is the official AosVM `v6.1.0` Main Node running as
a complete ARM64 system VM on the Apple M5 Pro. The host package is Homebrew
`qemu` 11.0.3 from the native ARM64 bottle. The launcher resolves
`/opt/homebrew/bin/qemu-system-aarch64`, requires the exact qualified version,
and selects Apple Hypervisor Framework explicitly; it has no TCG fallback.

The final QEMU argument contract is shown below with repository-local paths
sanitized. `scripts/aosvm start --dry-run` validates and prints the concrete
absolute paths before every launch.

```text
qemu-system-aarch64
  -name aosvm-main
  -machine virt-11.0,accel=hvf
  -cpu host -smp 2 -m 2048 -nodefaults
  -bios <cache>/QEMU_EFI.fd
  -drive file=<local>/aosvm-main-overlay.qcow2,if=none,id=aos-image,format=qcow2,cache=writeback
  -device virtio-scsi-pci,id=scsi
  -device scsi-hd,drive=aos-image,bootindex=0
  -netdev user,id=aosnet,net=10.0.0.0/24,host=10.0.0.1,dns=10.0.0.2,restrict=off,hostfwd=tcp:127.0.0.1:10022-10.0.0.100:22
  -device virtio-net-pci,netdev=aosnet,mac=52:54:00:41:4f:53
  -chardev socket,id=serial0,path=<run>/aosvm-main.serial,server=on,wait=off,logfile=<runs>/aosvm-main-serial.log,logappend=on,logtimestamp=on
  -serial chardev:serial0
  -qmp unix:<run>/aosvm-main.qmp,server=on,wait=off
  -pidfile <run>/aosvm-main.pid
  -monitor none -display none
```

The accepted network backend is QEMU user networking. SSH is forwarded only
from `127.0.0.1:10022`; the guest-visible host and gateway are `10.0.0.1`, and
the guest remains `10.0.0.100/24`. DNS uses the image's local dnsmasq and the
tracked overlay-only forwarding adjustment, then crosses QEMU to the tracked
macOS DNS bridge on `127.0.0.1:18053`. Both TCP and UDP DNS listeners are
loopback-only. No TAP device, macOS bridge, packet-filter change,
administrator privilege, or LAN listener is part of this baseline.

Observed timing is recorded as evidence, not as a performance guarantee:

| Readiness point | Observed result |
| --- | --- |
| Completely fresh overlay | First serial prompt 67.307 seconds after initial EFI output, including the intentional one-time SELinux relabel and reboot |
| Initialized overlay, serial | Stable prompt 47.887 seconds after EFI output in the Phase 7 measurement |
| Final launcher run, QEMU | `start` reported the owned QEMU process running after 8 seconds |
| Final launcher run, guest | `smoke-test` confirmed QMP and loopback SSH 26 seconds after the start invocation |
| Final launcher run, shutdown | Clean QMP-requested guest poweroff and exclusive overlay check completed in 2 seconds |

The launcher retains conservative bounds of 30 seconds for QEMU start, 90
seconds for SSH smoke readiness, 90 seconds for clean shutdown, and 15 seconds
for a verified process-specific `TERM` only if clean shutdown times out.

All required guest-kernel capabilities passed: cgroups v2; mount, PID, IPC,
UTS, and network namespaces; seccomp; overlayfs; initramfs-scoped SquashFS and
loop; veth, bridge, VLAN, VXLAN, and IFB; nftables/NAT; traffic control; quotas;
and enforcing SELinux. The separate local OCI gate used the image's AArch64
`crun` 1.14.3 build to start an isolated ARM64 PID 1 with enforced CPU, memory,
and PID limits, a read-only rootfs, a writable bounded tmpfs, no usable external
network interface, empty capabilities, `noNewPrivileges`, and complete cleanup.

Before provisioning, `aos_iam_app`, `aos_sm_app`, and `aos_cm_app` are native
AArch64 binaries at `v9.1.0-1-g9eec`. Provisioning IAM is active and reports
`unprovisioned`; runtime IAM, Service Manager, Communication Manager, and the
provisioning firewall are condition-gated on `/var/aos/.provisionstate`.
`/dev/sda6` is intentionally unopened, the generated Aos data mounts are
absent, and the dependent NFS unit is therefore the single classified failed
unit. No binary crash, kernel failure, SELinux denial, certificate, owned
PKCS#11 token, or unexplained local defect remains.

Known warnings and operational constraints are:

- a completely fresh overlay performs one intentional SELinux autorelabel and
  reboot before becoming ready;
- the released ARM64 image names `bootx64.efi` in Service Manager configuration
  even though it contains `bootaa64.efi`; the tracked idempotent helper corrects
  only the disposable overlay;
- the released static DNS assumptions do not work reliably with QEMU/libslirp
  and the active macOS resolver set; the tracked loopback bridge and
  overlay-only guest adjustment are required;
- GRUB emits non-fatal fallback-path and missing `com0` warnings before Linux
  uses the working PL011 `ttyAMA0` console;
- systemd is expected to report `degraded` before provisioning because the Aos
  data partition and NFS export paths have not yet been initialized;
- overlay reset deliberately removes both compatibility adjustments and
  regenerates the guest SSH host key, so the helpers and strict serial-verified
  host-key enrollment must be repeated before network gates pass;
- the smoke manifest and raw serial, DNS, and supervisor logs are mode-0600
  local evidence and remain ignored by Git.

The final smoke manifest at `2026-08-13T14:02:00Z` recorded `pass`, QMP
`running`, loopback-only SSH and DNS, a qcow2 overlay, and the exact pinned Main
Node base SHA-256. Clean stop then passed the complete Phase 13 stopped gate:
no owned process, listener, PID, socket, lock, corrupt overlay, or immutable
input drift remained. The VM is stopped.

**Decision: go to AOS-1 with one Main Node.** The initial Phase 14 review
selected the official two-Node AosVM demonstration topology. A subsequent
review confirmed that the AosEdge architecture supports a Unit with one Node,
the released Main image contains IAM, SM, and CM without a dependency on a
Secondary, and the official generic provisioning path explicitly supports
`aos-prov provision --nodes 1`. ADR 0003 retains the initial rationale and is
superseded by ADR 0004. The accepted AOS-0 evidence remains unchanged because
it qualified exactly this Main Node. The Secondary image remains verified,
immutable, and unused.

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

QEMU user networking presents `10.0.0.1` as the host/gateway and `10.0.0.2` as
its virtual DNS proxy. On macOS the proxy can inherit an unusable first system
resolver without trying later resolvers. Phase 11 therefore keeps the upstream
base read-only, routes the released guest dnsmasq through a tracked
loopback-only macOS DNS bridge, and stores the two guest configuration changes
only in the disposable overlay. Deleting and recreating the overlay restores
the released DNS configuration.

Fallback order:

1. QEMU user networking with the qualified loopback DNS bridge and
   overlay-only adjustment;
2. QEMU `vmnet` networking with an explicit macOS host-only/NAT design;
3. an SDK-managed ARM64 VirtualBox path, if the installed SDK proves that it
   supports the release on Apple Silicon;
4. build a DHCP-enabled `qemuarm64` image only if none of the released-image
   options works.

## Planned repository layout

```text
aosedge-sdv-demo/
  Brewfile
  README.md
  docs/
  scripts/aosvm             # one entry point with lifecycle subcommands
  scripts/host/             # constrained host helpers such as QMP and DNS
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

**Evidence:** timestamped ignored serial log and the sanitized observed
baseline recorded above. A structured per-run manifest remains a later
lifecycle deliverable.

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
| Squashfs and loop | Verify matching modules and the SquashFS-through-loop update path in the boot initramfs; do not require update-only modules after `switch_root` |
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

For the pinned `qemuarm64` release, also verify that the Service Manager boot
runtime names the AArch64 EFI loader present on both managed boot partitions.
An x86 loader path is a local update-path defect even when ordinary boot still
works through a pre-existing firmware entry.

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
5. track the helper and host bridge in this repository;
6. rely on the already qualified overlay recreation path to remove the
   override, and exercise the destructive reset workflow in Phase 13.

If that controlled overlay change is not reliable, evaluate QEMU `vmnet` next.
VirtualBox and a custom Yocto image remain later fallbacks. No fallback may
silently widen listener scope or require persistent host packet-filter changes.

**Pass:** outbound DNS/HTTPS and loopback SSH work, the host is reachable from
the guest for the later VISS path, and no service is exposed externally.

**Observed:** pass. `tests/guest/aosvm-phase11-test` and
`tests/host/aosvm-phase11-host-gate` passed twice, including after a clean
reboot. Phase 12 lifecycle automation and the Phase 13 reset regression also
pass.

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

**Observed:** pass. Real foreground and background runs exercised console,
status, immediate repeated start, bounded smoke readiness, QMP powerdown,
exclusive post-stop disk validation, repeated stop, and stopped status. An
explicit `SIGHUP` did not terminate the detached supervisor or its children.
The safety tests reject stale, unrelated, locked, and ambiguous runtime state.

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

**Observed:** pass. The `/dev/sda4` marker survived a clean stop/start and was
absent after explicit overlay recreation. Released EFI and DNS values returned,
both tracked compatibility helpers were restored and proved idempotent, and
Phase 10 plus complete Phase 11 regressions passed after reboot. All stopped
gates found no process, listener, or runtime leak and exact immutable hashes.

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

**Observed:** pass. Phase 13 recreated the overlay, restored both tracked
compatibility adjustments, and repeated the Phase 10 and Phase 11 gates. The
final Phase 14 start/smoke/stop run passed and left the VM stopped. This
document contains the sanitized accepted result; local manifests and raw logs
remain ignored.

## Acceptance checklist

- [x] Official archive matches the pinned SHA-256.
- [x] Base image remains unchanged after every completed test.
- [x] Native ARM64 QEMU starts the Main Node with HVF and no TCG fallback.
- [x] EFI, GRUB, the upstream AosVM kernel, initramfs, and root filesystem boot.
- [x] Serial console reaches a login prompt.
- [x] Guest reports ARM64 architecture.
- [x] Guest disk is `/dev/sda` with the expected partition and mount roles.
- [x] The mandatory guest-kernel capability matrix passes.
- [x] A local OCI bundle runs successfully with `crun` and leaves no residue.
- [x] No unexplained local AosCore component failure exists.
- [x] Outbound HTTPS and DNS work.
- [x] The guest can reach the macOS host for the later VISS path.
- [x] SSH is reachable only through a loopback host forward.
- [x] Clean shutdown and second boot succeed.
- [x] Overlay reset is safe and reproducible.
- [x] The launcher does not require administrator privileges.
- [x] A sanitized baseline is committed and the working tree is clean.

## Explicit non-goals

- AosCloud registration or provisioning.
- Certificate generation or storage.
- Deployment of an application service.
- CARLA or VISS network changes.
- Multi-node routing.
- Rebuilding AosVM with Yocto.
- Modifying or redistributing the upstream VM image.

## Go/no-go decision for AOS-1

**Go.** The Main Node foundation satisfies every AOS-0 acceptance item and the
remaining warnings are understood pre-provisioning or overlay-only
compatibility conditions. AOS-1 uses one `aos-vm-main` Node and the official
generic SDK path with an explicit `--nodes 1`. The tracked cloud Unit
Configuration must likewise contain only `aos-vm-main`.

AOS-1 begins with account and role verification, isolated CLI installation,
OEM/SP user certificates, and a temporary loopback-only provisioning forward.
It then provisions the Main Node, verifies the post-provision core state, and
deploys the official Hello World service. ADR 0004 and the AOS-1 runbook record
the detailed decision, safety boundaries, and execution phases.

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
