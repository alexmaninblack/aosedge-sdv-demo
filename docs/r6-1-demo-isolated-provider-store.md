<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-6.5a Demo Isolated Provider Store

- Status: proposed implementation plan; review required
- Date: 2026-08-15
- Platform baseline: validation Unit on rootfs `6.1.1-maninblack.2`
- Proposed replacement rootfs: `6.1.1-maninblack.3`
- Provider candidate: signed and locally verified `0.2.0`
- Cloud scope: isolated validation Unit only

## Decision Requested

Accept a bounded demo storage backend that preserves the intended SELinux
boundary without changing the provisioned AosVM workdirs mount or waiting for
the final production storage architecture decision.

The proposed backend creates a fixed-size ext4 filesystem image inside the
existing encrypted workdirs volume and mounts that filesystem at the already
accepted component root with the dedicated
`vehicle_data_provider_store_t` context.

This document authorizes no implementation, signing, upload, assignment, Unit
restart, or Cloud mutation. Work may begin only after review and explicit
acceptance of this plan.

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

The initial proposed filesystem size is 512 MiB. Final acceptance requires a
calculation from:

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

The first accepted constants must be explicit and tested:

```text
store image size
minimum free space before creation
minimum free space retained after creation
maximum provider archive size
maximum extracted slot size
maximum retained rollback generations
```

Changing any accepted constant after release requires a new platform version
and migration review.

## Rootfs `6.1.1-maninblack.3` Delta

The proposed rootfs contains only the platform changes needed for this storage
backend. Boot remains at `6.1.0` and is not part of the update.

### Steady-State Loop Support

The exact loop module already built for the accepted AosVM kernel is used by
the update initramfs but is not installed in the steady-state rootfs. `.3`
must include the matching loop module and the minimum required userspace tools
for loop setup, ext4 creation, identity inspection, mounting, and filesystem
checking.

The build must prove that:

- the module matches the running kernel release and vermagic;
- no new kernel or boot image is required;
- no unrelated update-only kernel module is added to rootfs;
- the rootfs-only FOTA bundle still contains no boot component.

### Store Preparation Service

A root-owned platform service prepares and validates the backing filesystem.
It must:

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

### Mount Unit

The dedicated mount unit must:

- require successful store preparation and the workdirs mount;
- use the exact accepted backing file and mount point;
- mount ext4 with `loop`, `nodev`, `nosuid`, `noatime`,
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
    -> vehicle-provider-store-prepare.service
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

`.3` is a new rootfs payload. `.2` remains immutable and installed evidence.
The accepted flow is:

1. build and qualify `.3` locally using retained Yocto sources and caches;
2. freeze a rootfs-only candidate with new exact digests;
3. stop for explicit signing approval;
4. sign and independently verify only the accepted `.3` candidate;
5. stop for explicit Cloud mutation approval;
6. upload `.3` only after the validation and demonstration Unit Sets are
   rechecked;
7. prove through Unit details that `.3` is pending only on the validation Unit;
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

Exit: repository gates pass; no VM or Cloud mutation.

### R6.1-6.5a.2 — Disposable Provisioned-Storage Fixture

- create an isolated ARM64 fixture that reproduces a parent ext4 mount with the
  fixed `aos_var_run_t` context;
- prove that direct subtree relabel remains impossible;
- create and mount the nested store through the production units;
- prove the exact mount source, context, options, capacity, and parent label;
- run positive and negative SELinux access tests;
- perform two clean boot/shutdown cycles.

Exit: no provisioned Unit or Cloud mutation.

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

- create rootfs `6.1.1-maninblack.3` without a boot update;
- use the retained incremental Yocto builder and preserve all caches;
- run structural, secret-exclusion, version, kernel-module, mount, systemd,
  SELinux, capacity, restart, and fatal-log gates;
- freeze exact configuration, rootfs size, and digests.

Exit: one unsigned, locally accepted rootfs candidate; no signing or Cloud
mutation.

### R6.1-6.5a.5 — Signing Gate

- request explicit permission for the exact frozen `.3` candidate;
- reverify all accepted bytes before identity access;
- sign only the rootfs candidate;
- independently verify embedded bytes, signed hashes, and RS256;
- retain sanitized evidence only.

Exit: one signed, locally verified `.3` bundle; no Cloud mutation.

### R6.1-6.5a.6 — Validation Unit Deployment

- request explicit permission for the exact Cloud mutation;
- recheck Unit Set roles, membership, installed versions, and pending versions;
- upload `.3` and prove validation-only pending scope before approval;
- install `.3` only on the validation Unit;
- verify online state, boot `6.1.0`, rootfs `.3`, nested store mount, SELinux,
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

Therefore `.3 -> .2` is not a transparent provider-preserving rollback. The
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
- Cloud shows `.3` or provider `0.2.0` pending on any Unit other than the
  validation Unit;
- a rootfs rollback would leave Cloud component state ambiguous; or
- any action would modify the demonstration Unit without separate approval.

## Exit Criteria

R6.1-6.5a is complete only when:

- `.3` is installed only on the validation Unit;
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

## Review Questions

1. Is a fixed 512 MiB store sufficient, and what AosCore reserve must remain?
2. Is minimum `search` permission on generic parent directories acceptable?
3. Should the backing file live below `sm/runtimes`, or in a separate
   root-owned workdirs platform directory?
4. Which exact ext4 recovery mode is acceptable for unattended boot?
5. Must the demo store use a fixed filesystem UUID, or a recorded UUID created
   once on the Unit?
6. Is provider removal before `.3 -> .2` rollback acceptable for the demo?
7. Which measurements and failure injections are required before Cloud upload?
8. Should this backend be retained as a supported development configuration or
   removed after the production storage decision?

## References

- [R6.1 Persistent Store SELinux Architecture Review](r6-1-selinux-persistent-store-architecture.md)
- [R6.1 vehicle-data-provider FOTA design](r6-1-vehicle-data-provider-fota-design.md)
- [R6.1 first Cloud deployment](r6-1-first-cloud-deployment.md)
- [R6.1 offline provider qualification](r6-1-offline-provider-qualification.md)
- [R6.1 stale validation-scope defect](r6-1-validation-set-scope-defect.md)
