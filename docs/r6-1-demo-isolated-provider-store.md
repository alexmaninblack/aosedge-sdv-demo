<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-6.5a Demo Isolated Provider Store

- Status: `.11` unsigned rootfs-only candidate frozen; signing approval pending
- Date: 2026-08-15
- Platform baseline: validation Unit on rootfs `6.1.1-maninblack.2`
- Current local qualification candidate: `6.1.1-maninblack.11`
- Provider candidate: signed and locally verified `0.2.0`
- Cloud scope: isolated validation Unit only

## Accepted Decision

Accept a bounded demo storage backend that preserves the intended SELinux
boundary without changing the provisioned AosVM workdirs mount or waiting for
the final production storage architecture decision.

The proposed backend creates a fixed-size ext4 filesystem image inside the
existing encrypted workdirs volume and mounts that filesystem at the already
accepted component root with the dedicated
`vehicle_data_provider_store_t` context.

The plan was explicitly accepted on 2026-08-15. That acceptance authorizes the
local implementation, static tests, disposable fixtures, incremental build,
rootfs-only qualification, and freezing of one unsigned candidate. It does not
authorize OEM signing, upload, assignment, restart of a provisioned Unit, or
any Cloud mutation; those remain separate explicit gates.

## Motivation

Rootfs `6.1.1-maninblack.2` successfully installed the Service Manager
component runtime on the validation Unit. Provider deployment then stopped
because provisioned AosVM mounts all of `/var/aos/workdirs` with the fixed
SELinux context `aos_var_run_t`. The provider policy expects its persistent
subtree to use `vehicle_data_provider_store_t`, but a fixed-context mount
cannot carry a different label on one subtree.

The long-term choices remain:

- convert workdirs to per-inode SELinux labels through a controlled migration;
- introduce a dedicated production logical volume or partition; or
- select another platform storage abstraction with equivalent isolation.

Those choices require platform-architecture review. The demo still needs an
independent provider FOTA lifecycle, so R6.1-6.5a introduces a reversible,
bounded storage backend that does not weaken the existing SELinux policy and
does not relabel any existing AosCore data.

## Accepted Constraints

The demo solution must:

1. preserve Unit identity, provisioning state, certificates, and one-Main-Node
   topology;
2. leave the upstream `/var/aos/workdirs` mount options unchanged;
3. avoid recursive relabeling of existing AosCore workdirs;
4. avoid giving `vehicle_data_provider_t` general read, write, or execute
   access to `aos_var_run_t`;
5. preserve the existing provider component root and signed-provider absolute
   path contract;
6. keep provider state persistent across clean VM restarts and rootfs updates;
7. bound storage allocation and fail closed on corruption or insufficient
   capacity;
8. require a new immutable rootfs version rather than modify `.2`;
9. target only the validation Unit until a separate promotion decision; and
10. remain clearly classified as a demo backend, not an approved production
    vehicle storage design.

## Proposed Storage Architecture

The existing mount remains unchanged:

```text
/dev/aosvg/workdirs
    -> /var/aos/workdirs
    -> context=system_u:object_r:aos_var_run_t:s0
```

R6.1-6.5a adds one private backing file and one nested filesystem:

```text
/var/aos/workdirs
└── sm/runtimes/.vehicle-data-provider-store.ext4
        regular file, root:root, mode 0600, fixed allocation
                   │
                   │ loop device
                   ▼
/var/aos/workdirs/sm/runtimes/systemd-slot-component
        ext4
        context=system_u:object_r:vehicle_data_provider_store_t:s0
        nodev,nosuid,noatime,errors=remount-ro
```

The backing file remains visible only through the general Aos platform storage
domain. Its mounted filesystem becomes a distinct SELinux superblock and is
visible to the provider through the dedicated store type.

The mount point remains exactly:

```text
/var/aos/workdirs/sm/runtimes/systemd-slot-component
```

Keeping this path avoids changing the Service Manager runtime configuration,
provider launcher path allowlist, health contract, systemd environment paths,
and signed provider `0.2.0` path assumptions.

## Storage Size and Capacity Contract

The accepted demonstration filesystem size is 512 MiB. It is sized for the
qualified provider `0.2.0` candidate and one retained rollback generation; it
is not a production capacity commitment for every archive accepted by the
runtime's independent 512 MiB safety ceiling. Every installation still fails
before switching if the extracted active and candidate slots plus metadata do
not fit.

The production capacity decision must instead be calculated from:

- two maximum provider payload slots;
- staging and transaction overhead;
- rollback evidence;
- configuration, trust, credential, and state data;
- ext4 metadata and reserved space;
- a defined future provider growth margin.

The backing file must be fully allocated. A sparse file that can fail later
during provider update is not acceptable. Before creation, the preparation
service must prove both the requested allocation and a separate workdirs
reserve for AosCore.

The demonstration constants are explicit and tested:

```text
store image size: 512 MiB
minimum free space before creation: 1 GiB
minimum free space retained immediately after creation: 512 MiB
runtime archive safety ceiling: 512 MiB, not a store capacity guarantee
maximum extracted slot size: bounded by the remaining store capacity gate
maximum retained rollback generations: one
```

Changing any accepted constant after release requires a new platform version
and migration review.

## Rootfs `6.1.1-maninblack.10` Delta

The rootfs contains only the platform changes needed for this storage
backend. Boot remains at `6.1.0` and is not part of the update.

### Integrated Candidate Evidence

```text
version: 6.1.1-maninblack.10
platform revision: 12b09c6e447584f79d6627e83e59bb025bff00d6
raw image size: 6997147648 bytes
raw image SHA-256: a39d4c97b9a5e28e372b6b44ec654308b6b1d85a765be752deed1d47e57630c8
```

The retained incremental builder reused 99% of build state. Both clean
bootstrap boots passed with AArch64, read-only `/dev/sda3`, Enforcing SELinux,
and the exact `.10` version. A fresh integrated store then passed allocation,
loop attachment, fixed-context nested mounting, non-root provider execution,
store access, and sibling denial. A clean stop/start preserved and revalidated
the backing filesystem and fixture content. The recent provider AVC profile
contains only the deliberately exercised denial on the DAC-open sibling
`aos_var_run_t` secret; no procfs, userdb, or extra-capability access appears.

## Rootfs `6.1.1-maninblack.11` Runtime Dependency Closure

`.10` remained the disposable discovery base while the complete provider
lifecycle and dependency surface were reviewed before another image build.
The resulting `.11` delta is intentionally limited to the provider platform
boundary:

- read-only access to systemd's unit-private `LoadCredential` files;
- the pinned refpolicy DNS client interface for hostname-based VISS URIs;
- direct, unconditional read access to `/dev/urandom` for gRPC TLS while the
  AosVM `global_ssp` boolean remains off; and
- a soft, ordered KUKSA dependency so a Databroker restart does not stop the
  provider lifecycle.

The exact candidate evidence is:

```text
version: 6.1.1-maninblack.11
platform revision: a12c0aa7f8a680b35407776b12bcc025970abc73
manifest SHA-256: b9b49a575798f2bc4a532a794e77352ed21596677ef5aced4304db9e7a87f09e
build graph SHA-256: 08bb15d68e32cbfce1825563e8207e84c1e3b584d9a48c266338f2c242ca867e
raw image size: 6997147648 bytes
raw image SHA-256: 946a296b7200644bc529080f3512712d8b7ec97dedad520146a4f503cf4006a2
FOTA configuration SHA-256: 9bceee031f31e3c0ec3afe2453c51213282d96ca2ed3b2139965038d4a4506b3
FOTA rootfs size: 128528384 bytes
FOTA rootfs SHA-256: e30406f600ada77568d21178e656a34f444973bf121f5a0b537e24efde8ab9d7
candidate metadata SHA-256: 56c109c30ab1111ba23dffe45634dbd556298f55da79782d867c3ac6be911aa6
```

Before the image build, the side-loaded candidate passed in global SELinux
`Enforcing` mode with no permissive domains and a read-only root. Positive DNS
resolution delivered live VISS telemetry; KUKSA stop/start preserved the same
provider PID and automatically recovered live values; invalid credentials
failed closed; `SIGKILL` recovered in four seconds; and DNS/TLS failures
remained fail-safe. The one incremental `.11` image then passed a clean
disposable AArch64 boot with direct compiled-policy gates for credentials,
DNS, and `urandom`.

The regenerated FOTA output contains exactly one full rootfs SquashFS. Boot
and incremental-rootfs components are absent. The frozen `128,528,384`-byte
payload is therefore the actual unsigned update candidate; the
`6,997,147,648`-byte raw image is only the complete local VM disk used for
clean-boot qualification and is not transferred as the FOTA payload.

No signing identity, provisioned Unit, Cloud assignment, validation Unit, or
demonstration Unit was accessed or changed.

### Steady-State Loop Support

The exact loop module already built for the accepted AosVM kernel is used by
the update initramfs but is not installed in the released steady-state rootfs.
`.10` includes the matching loop module and the minimum required userspace
tools for loop setup, ext4 creation, identity inspection, mounting, and
filesystem checking.

The build must prove that:

- the module matches the running kernel release and vermagic;
- no new kernel or boot image is required;
- no unrelated update-only kernel module is added to rootfs;
- the rootfs-only FOTA bundle still contains no boot component.

### Store Preparation and Loop Attachment

A root-owned platform service with an empty capability set prepares and
validates the backing filesystem. It must:

1. start only after the real workdirs mount is active;
2. verify the exact mount point, source family, filesystem type, and fixed
   `aos_var_run_t` context;
3. verify that the component mount point is not already controlled by an
   unexpected mount or link;
4. reject a symbolic link, special file, unexpected owner, unsafe mode, or
   unexpected existing backing-file size;
5. check the accepted workdirs reserve before first allocation;
6. fully allocate a mode-0600 root-owned temporary file;
7. create ext4 with an accepted label and filesystem UUID policy;
8. atomically install the backing file only after format and identity checks;
9. never reformat, truncate, replace, or automatically recreate an existing
   backing file;
10. run bounded non-destructive filesystem recovery on later boots;
11. record a non-secret format schema marker outside the provider slots; and
12. fail closed on every ambiguous condition.

The service must not contain a general disk formatting interface. Its source,
target path, size, mode, filesystem type, and accepted identities are fixed by
the platform package.

A separate oneshot attachment service executes only the fixed native loop
helper. The helper accepts `attach` or `detach`, but no caller-controlled path,
size, device, or mount point. It validates the immutable backing-file contract,
selects at most one bounded `/dev/loopN`, and atomically publishes the selected
device through `/run/aos-vehicle-data-provider-store/loop`. Only this service
has `CAP_SYS_ADMIN`; the preparation shell, filesystem tools, mount process,
Service Manager, and provider do not inherit that capability.

The attachment helper enters
`vehicle_data_provider_store_admin_t`. Its private runtime directory and loop
identity use `vehicle_data_provider_store_runtime_t`. The generic mount domain
may traverse that directory and read that one link, but it receives no access
to the backing file or general Aos workdirs.

The immutable preparation entrypoint enters the separate
`vehicle_data_provider_store_prepare_t` domain. It has no capabilities and may
execute the required filesystem tools without transitioning into generic
`fsadm_t`. Its filesystem writes remain limited by both SELinux and the
systemd `ReadWritePaths=/var/aos/workdirs/sm/runtimes` namespace. Standard
shell plumbing is limited to its own FIFO, the inherited init-script stream
socket, and read-only generic `/proc` system state.

### Mount Unit

The dedicated mount unit must:

- require successful store preparation, loop attachment, and the workdirs
  mount;
- use the fixed runtime loop identity and exact accepted mount point;
- mount ext4 with `nodev`, `nosuid`, `noatime`,
  `errors=remount-ro`, and the fixed
  `vehicle_data_provider_store_t` context;
- retain executable files because the provider payload runs from its active
  slot;
- reject a read-only or incorrectly labelled result during normal startup;
- stop before workdirs is unmounted; and
- make failure visible through systemd and the R6.1 health gate.

The component archive validator continues to reject device nodes, setuid or
setgid modes, Linux capabilities, unsafe links, special files, and paths outside
the accepted payload layout. The executable mount does not relax those archive
rules.

### Boot Ordering

The required order is:

```text
var-aos-workdirs.mount
    -> vehicle-provider-store-layout.service
    -> vehicle-provider-store-prepare.service
    -> vehicle-provider-store-attach.service
    -> component-store.mount (path-derived systemd unit name)
    -> aos-vehicle-data-provider-bootstrap.service
    -> aos-sm.service
```

Service Manager must not accept a provider installation or start the provider
until the mounted store passes its source, type, mode, capacity, and SELinux
checks. A mount or preparation failure must make the component runtime fail
closed and must not fall back to the underlying generic-labelled directory.

## SELinux Contract

The mounted filesystem uses a fixed context intentionally because every object
on that filesystem belongs to the one provider-store trust boundary.

The existing permissions remain:

- `aos_t` manages directories, files, links, A/B state, and lifecycle;
- `vehicle_data_provider_t` receives only the accepted read, map, list, link,
  and execute permissions for `vehicle_data_provider_store_t`;
- the provider receives no general read, write, or execute permission for
  `aos_var_run_t`.

The provider needs only the minimum directory-search permission required to
reach the dedicated child mount through its generic-labelled parent path. That
permission must be demonstrated not to allow listing, reading, mapping,
executing, or modifying sibling AosCore workdirs.

The health helper remains outside the provider payload domain. Credentials
continue to be delivered through systemd `LoadCredential`; provider code must
not open the credential source directly.

The provider unit enters `vehicle_data_provider_t` through the immutable
launcher before enabling `no_new_privs`. The launcher alone temporarily uses
`CAP_SETGID` and `CAP_SETUID`, clears all supplementary groups, drops every
real, effective, and saved UID/GID to the image-owned non-login `aos-vdp`
account, verifies an empty capability set, and only then executes the selected
payload without another domain transition.

The final provider-domain allowance set is deliberately bounded to:

- `setgid` and `setuid` for the pre-payload identity drop;
- `getcap` for the launcher's fail-closed post-drop verification;
- self-owned FIFO access and the inherited init stream used for ordinary
  payload pipes and systemd stdout/stderr;
- read, map, list, link, and execute access to the dedicated store;
- client-side TCP, systemd readiness notification, runtime credentials, and
  public certificate reads required by the VISS-to-KUKSA bridge.

The policy does not grant provider access to sibling `aos_var_run_t` files,
arbitrary procfs or sysctl inspection, systemd-userdb, listening or raw
sockets, store writes, or any capability other than the two transient identity
drop capabilities. The isolated store is no longer managed by global
`systemd-tmpfiles`, so that management interface is not part of the accepted
policy.

## Provider `0.2.0` Compatibility

The signed provider candidate contains an exact entrypoint and an internal
path allowlist for the existing A/B slot locations. R6.1-6.5a preserves those
locations, so the candidate is expected to remain compatible.

Before Cloud upload, the guarded verifier must nevertheless prove again that:

- the bundle, configuration, layer, and signed hashes still match the accepted
  provider evidence;
- the entrypoint resolves only inside slot `a` or `b` below the mounted store;
- no provider artifact expects the backing-file path or loop device;
- the new platform runtime reports the same provider component type; and
- no provider re-signing is needed.

If any signed assumption changes, provider `0.2.0` must not be reused under the
same version.

## Rootfs Update and Cloud Scope

`.11` is the current local rootfs payload. `.2` remains immutable and installed
evidence; the rejected `.3` through `.9` development images remain local
evidence only, and `.10` is retained as the runtime-discovery base.
The accepted flow is:

1. build and qualify `.11` locally using retained Yocto sources and caches;
2. freeze a rootfs-only candidate with new exact digests;
3. stop for explicit signing approval;
4. sign and independently verify only the accepted `.11` candidate;
5. stop for explicit Cloud mutation approval;
6. upload `.11` only after the validation and demonstration Unit Sets are
   rechecked;
7. prove through Unit details that `.11` is pending only on the validation Unit;
8. approve only the intended architecture;
9. monitor download, install, activation, reboot, and final online state; and
10. leave the demonstration Unit unchanged.

The previous stale-scope incident makes pending Unit details, not Unit Set
membership alone, the final approval gate.

## Qualification Plan

### R6.1-6.5a.1 — Static Design and Negative Tests

- pin all paths, sizes, mount options, unit names, ordering, and policy types;
- test rejection of unsafe backing files, links, devices, modes, sizes, UUIDs,
  filesystem types, and mount sources;
- test that no command accepts an arbitrary destructive target;
- test archive and source-lock regressions;
- make the implementation idempotent and fail closed.

Status: complete. The exact platform paths, constants, mount options, identity
transaction, non-destructive recovery rules, isolated tmpfiles boundary,
minimal parent traversal permission, and negative source tests are enforced by
the repository gates. No provisioned VM or Cloud object was changed.

### R6.1-6.5a.2 — Disposable Provisioned-Storage Fixture

- create an isolated ARM64 fixture that reproduces a parent ext4 mount with the
  fixed `aos_var_run_t` context;
- prove that direct subtree relabel remains impossible;
- create and mount the nested store through the production units;
- prove the exact mount source, context, options, capacity, and parent label;
- run positive and negative SELinux access tests;
- perform two clean boot/shutdown cycles.

Exit: no provisioned Unit or Cloud mutation.

Status: in progress. The fixture owns a separate 2 GiB QEMU disk with a fixed
serial and refuses formatting until device, size, serial, root-device, and
blank-filesystem checks pass. The same disk is retained across two clean boot
cycles.

### Rejected local boot candidate

The first unsigned `.3` image, SHA-256 prefix `e605be1f`, was rejected during
its first disposable boot. Its store preparation service participated in the
local-files transaction with normal service default dependencies, creating an
ordering cycle that caused systemd to remove `selinux-autorelabel` from the
second boot transaction. Writable partitions consequently remained
`unlabeled_t`, SSH correctly failed closed, and the image was never accepted,
signed, uploaded, or run on a provisioned Unit.

The raw image, overlay, serial log, and boot evidence are retained locally
under an explicit `rejected-ordering-cycle-e605` name. After the bounded ACPI
shutdown did not complete, only that rejected disposable QEMU was terminated.
Corrective platform revision
`1385b3b0f5f72a9381d65ea77458619314ba3607` added an early-boot dependency
contract with `DefaultDependencies=no` and the narrow pinned-refpolicy
interface needed by steady-state module loading. Its image, SHA-256 prefix
`6ace89d4`, proved that autorelabel and SSH enrollment were restored, but found
a smaller remaining cycle: `PrivateTmp=yes` implicitly ordered preparation
after `systemd-tmpfiles-setup`, which itself follows `local-fs.target`. That
image was stopped cleanly and retained locally under the explicit
`rejected-private-tmp-cycle-6ace` name; it was never signed or uploaded.

Revision `8b18bbcf940032159af3c6fce933f7b04226ece8` removes that unused
`PrivateTmp` dependency and adds a regression guard. Before booting its build,
the mount transaction was tightened further: native mount units otherwise
participate in `local-fs.target` even when the provider runtime is not needed.
Current revision `54c09911341b2bf8fde369f3ce116c91361cfe4a` therefore makes the
nested mount on-demand with `DefaultDependencies=no`, while explicitly
conflicting with and stopping before `umount.target`. The intermediate
`8b18bbc` bytes were not fetched or booted. The next candidate must prove that
no ordering cycle exists, autorelabel completes, SSH enrollment works, and
current-boot AVCs are clean before fixture testing continues.

Later candidates passed those early-boot gates and exposed progressively
narrower runtime-policy defects. The `.3` image with SHA-256 prefix `af7cc`
proved store allocation, then failed because preparation and loop attachment
shared one privileged service and the mount process could not resolve a
generic-labelled runtime link. Revision `15d0a3c` separated an unprivileged
preparation service from a fixed native loop helper with only
`CAP_SYS_ADMIN`, and gave the loop identity a dedicated runtime type.

The `.4` image `a777f710…` passed two complete bootstrap boots with read-only
rootfs and enforcing SELinux. Its clean store fixture reached `mkfs.ext4` and
was rejected because the generic `fsadm_t` transition could not access the
fixed-context backing file. Revision `dd6717b` introduced a dedicated,
capability-free preparation domain instead of broadening `fsadm_t`.

The `.5` image `eab0e8c9…` also passed two complete bootstrap boots. Its store
fixture proved that the dedicated domain was entered, then failed before
allocation because the new shell domain lacked only the standard inherited
init-script socket, self-FIFO, and read-only `/proc` plumbing permissions.
Revision `74d0407` adds exactly those permissions. The rejected overlays,
secondary disks, access records, serial logs, and boot evidence are preserved
locally under explicit `rejected-*` names; none of these images was signed,
uploaded, or installed on a provisioned Unit.

The `.6` image `d02b52a6…` passed two complete bootstrap boots. Its enforcing
store fixture progressed to the capacity check and exposed one missing
read-only filesystem `getattr`. A separately labelled disposable diagnostic
run temporarily changed only runtime enforcement, completed the exact fixed
production chain, immediately restored global Enforcing, and collected the
remaining AVCs in one pass. It showed that preparation needed only read-only
sysfs and loop inspection, the fixed loop helper needed its inherited service
socket and filesystem `getattr`, and the mount needed one dedicated-filesystem
`relabelfrom`. It also exposed an avoidable generic `fsadm_t` read caused by
post-mount `blkid` on the backing file. Revision `72babce` moves that identity
check to the mounted `/dev/loopN` and adds only the observed fixed-domain
permissions. The diagnostic overlay and data disk are archived separately
under `store-diagnostic-permissive-d02b`; they are not qualification evidence.

The `.7` image `35e22dc3…` passed two complete bootstrap boots and then passed
preparation, loop attachment, and nested mounting in Enforcing. Its
post-mount check was rejected because one remaining `losetup -j` still
transitioned into generic `fsadm_t` and attempted to inspect the backing file.
The replacement check was side-loaded only into that disposable VM and passed
against the mounted store, proving the logic without turning the VM into
qualification evidence. Revision `5133933` removes that scan and verifies the
actual mount source against the dedicated runtime loop identity created by the
fixed native helper.

The `.8` image
`2de2e47b37ace5601ce2e86e6ddbc40faa976da2b2c7920115277728a24e7c5c`
passed two complete bootstrap boots and the clean
Enforcing store path through preparation, loop attachment, nested mount, and
post-mount validation. The original fixture then produced a false negative by
calling the launcher directly from an SSH shell, which correctly remained
`unconfined_t`. After the fixture was corrected to use the production systemd
self-test unit, the payload remained in the generic `initrc_t` domain and could
read a DAC-open sibling workdir. The compiled policy contained the intended
transition, but this AosVM baseline suppresses it after systemd applies
`DynamicUser` or `NoNewPrivileges`. `.8` is therefore rejected as provider
domain-isolation evidence even though its store implementation is sound.
Platform revision `083997d` introduced a fixed non-login `aos-vdp` account and
a bounded native launcher. Only that launcher receives `CAP_SETUID` and
`CAP_SETGID`; after entering `vehicle_data_provider_t` it enables
`no_new_privs`, irreversibly drops UID/GID, verifies empty runtime capability
sets, and only then executes the payload. Rootfs `.9`
(`533c3c2e297da0af7b8d39b91a559a21416989f30f69765d3f01dc48bb285ced`)
passed both clean
bootstrap boots and the complete store path, but the first production-unit
self-test stopped when SELinux denied the launcher's post-drop `capget`
verification. It is therefore rejected rather than incrementally patched.

One complete review replaced the earlier denial-by-denial loop. Platform
revision `12b09c6` clears supplementary groups without NSS or systemd-userdb,
adds only self-`getcap`, self-FIFO, and the inherited init stream, and removes
the obsolete global-tmpfiles store-management interface. A package-only build
passed before any image rebuild. The complete domain-scoped permissive
discovery run on the disposable `.9` base produced only the deliberately
exercised sibling `aos_var_run_t` denial. After restoring the provider domain
to Enforcing and cleanly restarting the same persistent store, the lifecycle
passed with that sibling read denied and no procfs, userdb, or additional
capability access. Rootfs `.10` then became the disposable discovery base for
the consolidated credential, DNS, random-device, and KUKSA lifecycle review.
Rootfs `.11` is the single current integrated candidate for the next unsigned
rootfs-only FOTA gate. That gate has now passed and the exact candidate is
frozen; signing remains unauthorized pending explicit approval.

### R6.1-6.5a.3 — Lifecycle and Failure Matrix

- install the real provider into an inactive slot;
- activate, update, roll back, and recover through the production runtime;
- inject interrupted allocation, invalid image identity, filesystem damage,
  failed fsck, insufficient reserve, missing loop support, mount failure,
  read-only remount, and unclean shutdown;
- prove that an existing invalid store is never reformatted automatically;
- prove that the active and rollback slots survive restart;
- prove that unrelated workdirs remain unchanged.

Exit: complete local provider lifecycle passes on the nested filesystem.

### R6.1-6.5a.4 — Build and Rootfs Qualification

- create rootfs `6.1.1-maninblack.11` without a boot update;
- use the retained incremental Yocto builder and preserve all caches;
- run structural, secret-exclusion, version, kernel-module, mount, systemd,
  SELinux, capacity, restart, and fatal-log gates;
- freeze exact configuration, rootfs size, and digests.

Exit: one unsigned, locally accepted rootfs candidate; no signing or Cloud
mutation.

### R6.1-6.5a.5 — Signing Gate

- request explicit permission for the exact frozen `.11` candidate;
- reverify all accepted bytes before identity access;
- sign only the rootfs candidate;
- independently verify embedded bytes, signed hashes, and RS256;
- retain sanitized evidence only.

Exit: one signed, locally verified `.11` bundle; no Cloud mutation.

### R6.1-6.5a.6 — Validation Unit Deployment

- request explicit permission for the exact Cloud mutation;
- recheck Unit Set roles, membership, installed versions, and pending versions;
- upload `.11` and prove validation-only pending scope before approval;
- install `.11` only on the validation Unit;
- verify online state, boot `6.1.0`, rootfs `.11`, nested store mount, SELinux,
  empty slots, service health, clean logs, and restart persistence.

Exit: validation Unit is ready for provider assignment; demonstration Unit is
unchanged.

### R6.1-6.5a.7 — Provider Deployment and Demo Gate

- reverify signed provider `0.2.0` and its platform compatibility;
- publish and assign it only to the validation Unit;
- verify component discovery, progress, install, active version, and rollback
  state;
- connect CARLA VISS input and KUKSA output;
- demonstrate live telemetry, source loss, recovery, clean VM restart, and one
  provider update or rollback cycle;
- retain sanitized Cloud and guest evidence.

Exit: the isolated validation Unit demonstrates the intended independent
provider FOTA lifecycle and telemetry path.

## Rootfs Rollback Limitation

Rootfs `.2` does not contain the steady-state loop support or nested-store
mount units. If rootfs is rolled back after provider installation, the backing
file remains intact but is not mounted, and the underlying empty component
directory becomes visible.

Therefore `.11 -> .2` is not a transparent provider-preserving rollback. The
accepted rollback procedure must either:

- remove or suspend the provider assignment before rootfs rollback and report
  the provider unavailable on `.2`; or
- add a separately reviewed compatibility mechanism that safely mounts the
  same store on the rollback rootfs.

R6.1-6.5a proposes the first behavior. Automatic rootfs rollback with an active
provider is a stop condition until its Cloud and Service Manager status
semantics are tested and documented.

## Recovery and Backup

Before the first validation-Unit deployment:

- stop the validation VM cleanly;
- verify qcow2 integrity;
- create a new standalone checkpoint of the complete provisioned overlay;
- record only sanitized checkpoint metadata;
- restart the same protected overlay and identity.

The nested store backing file is part of that overlay and therefore part of
future offline checkpoints. It must never be copied independently into another
provisioned Unit, because a disk checkpoint is tied to the owning Unit's
identity and persistent state.

An invalid store image is preserved for diagnosis. Automated recovery may run
only bounded, non-destructive filesystem checks. Reformatting or replacing an
existing store always requires an explicit destructive recovery decision.

## Stop Conditions

Stop without automatic retry if:

- the loop module does not exactly match the running kernel;
- the required userspace tooling is absent or unexpectedly privileged;
- the workdirs mount source, filesystem, context, or capacity differs;
- the backing path is a link, device, unexpected file, or wrong size;
- the accepted free-space reserve cannot be maintained;
- an existing store has an unknown UUID, label, filesystem type, or corruption;
- the nested mount does not have the exact source, options, and SELinux type;
- any provider access to sibling `aos_var_run_t` data succeeds;
- any unexplained AVC, fatal process failure, or read-only remount appears;
- the provider signed bytes or absolute path assumptions change;
- Cloud shows `.11` or provider `0.2.0` pending on any Unit other than the
  validation Unit;
- a rootfs rollback would leave Cloud component state ambiguous; or
- any action would modify the demonstration Unit without separate approval.

## Exit Criteria

R6.1-6.5a is complete only when:

- `.11` is installed only on the validation Unit;
- boot remains `6.1.0`;
- the nested provider store is persistent, bounded, correctly labelled, and
  fail-closed;
- provider `0.2.0` is visible as an independent Aos component;
- provider install, start, update or rollback, and restart recovery pass;
- CARLA telemetry reaches KUKSA through the provider;
- the provider cannot access unrelated AosCore workdirs;
- the demonstration Unit remains unchanged; and
- all retained evidence contains no credential, identity, token, private Cloud
  identifier, or user-specific path.

Completion proves a demo-compatible isolated store backend. It does not select
the final production vehicle storage architecture.

## Resolved Review Questions

1. Fixed 512 MiB is accepted only for the qualified `0.2.0` demonstration; at
   least 512 MiB must remain in workdirs immediately after first allocation.
2. Directory `search` on `aos_var_run_t` parents is accepted; no sibling list,
   read, map, execute, create, write, or mutation permission is added.
3. The backing file remains below the fixed `sm/runtimes` platform path.
4. Unattended boot may run `e2fsck -p`; only status 0 or 1 is accepted.
5. A random filesystem UUID is created once, recorded atomically, and required
   on every later boot. A committed store is never reformatted automatically.
6. Provider assignment must be suspended or removed before `.11 -> .2`
   rollback; transparent rollback across those storage backends is not claimed.
7. The static, fixture, lifecycle/failure, build, SELinux, capacity, restart,
   fatal-log, and secret-exclusion gates in this document are all required.
8. The backend remains a development/demo configuration until the production
   storage decision explicitly accepts, replaces, or retires it.

## References

- [R6.1 Persistent Store SELinux Architecture Review](r6-1-selinux-persistent-store-architecture.md)
- [R6.1 vehicle-data-provider FOTA design](r6-1-vehicle-data-provider-fota-design.md)
- [R6.1 first Cloud deployment](r6-1-first-cloud-deployment.md)
- [R6.1 offline provider qualification](r6-1-offline-provider-qualification.md)
- [R6.1 stale validation-scope defect](r6-1-validation-set-scope-defect.md)
