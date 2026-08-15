<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1 Persistent Store SELinux Architecture Review

- Status: discussion draft; no implementation decision
- Date: 2026-08-15
- Audience: AosEdge platform, security, storage, lifecycle, and vehicle-integration architects
- Affected stage: R6.1-6, before vehicle-data-provider `0.2.0` assignment
- Validated platform rootfs: `6.1.1-maninblack.2`

## Executive Summary

R6.1 adds an OEM platform runtime that allows Service Manager to install and
update the vehicle data provider as an independent FOTA component. The runtime,
stable launcher, systemd units, health adapter, and SELinux policy are delivered
by rootfs. The provider payload is delivered later and stored in a persistent
A/B component store.

The intended SELinux boundary assigns the provider store the dedicated type
`vehicle_data_provider_store_t`. Service Manager, running in `aos_t`, manages
that type; the provider payload runs in `vehicle_data_provider_t` and receives
only the minimum read and execute access required for its own files.

The first deployment to a provisioned validation Unit exposed an incompatible
storage contract. Upstream AosVM mounts the complete `/var/aos/workdirs` ext4
filesystem with the fixed mount option:

```text
context=system_u:object_r:aos_var_run_t:s0
```

A fixed SELinux mount context makes every inode visible as `aos_var_run_t` and
prevents a subtree from carrying `vehicle_data_provider_store_t`. The provider
policy is therefore correctly restrictive, but the provisioned filesystem
cannot represent the label required by that policy. Provider `0.2.0` has not
been assigned.

This document recommends an initial solution for R6.1: retain the existing
workdirs logical volume, remove its fixed mount-wide `context=`, enable normal
ext4 per-inode SELinux labels, and perform a controlled one-time relabel before
AosCore starts. A dedicated provider logical volume remains the stronger
production option when independent quota and filesystem-failure isolation are
required. This recommendation is not yet an implementation authorization.

## Scope

This review covers:

- persistent storage for the OEM vehicle-data-provider platform component;
- SELinux type enforcement across Service Manager, the provider, and other
  AosCore state;
- upgrade and rollback of an already provisioned Unit;
- implications for future OEM vehicle storage design.

It does not change:

- the CARLA-to-VISS-to-KUKSA data architecture;
- the independent SOTA lifecycle of telemetry-consuming services;
- Unit identity, Node topology, provisioning certificates, or Cloud grouping;
- the accepted A/B provider update state machine;
- the immutable `6.1.1-maninblack.2` release.

## Intended Platform and Component Boundary

The platform rootfs owns the stable integration contract:

- Service Manager runtime type `systemd-slot-component`;
- restricted provider archive validation and A/B apply/rollback;
- stable launcher, health adapter, systemd service, and self-test unit;
- provider configuration, trust, and credential paths;
- SELinux domain transition and file-type policy;
- persistent-store bootstrap and recovery rules.

The independently delivered provider owns only its versioned payload. It must
not install files into `/usr` or `/etc`, install policy, replace the stable
launcher, alter another component's data, or require a rootfs rebuild for each
provider update.

The current component root is:

```text
/var/aos/workdirs/sm/runtimes/systemd-slot-component
```

Its durable layout contains inactive and active payload slots, transaction
state, configuration, trust data, and credentials. Service Manager is the
writer and lifecycle owner. The provider is intentionally not a general writer
to this tree.

## Intended SELinux Model

The relevant types and ownership are:

| Object or process | SELinux type/domain | Intended access |
| --- | --- | --- |
| Service Manager and its component runtime | `aos_t` | Manage provider store and lifecycle |
| Stable provider launcher | `vehicle_data_provider_exec_t` | Transition payload into provider domain |
| Provider payload process | `vehicle_data_provider_t` | Read and execute only its accepted payload and inputs |
| Provider component store | `vehicle_data_provider_store_t` | Dedicated provider storage boundary |
| General Aos persistent data | `aos_var_run_t` | Existing AosCore shared data boundary |

The policy deliberately allows `aos_t` to manage
`vehicle_data_provider_store_t`, while `vehicle_data_provider_t` receives
limited list, read, map, and execute permissions. The systemd unit adds a
dynamic user, an empty capability set, `NoNewPrivileges`, read-only system
protection, namespace restrictions, and credential delivery through systemd.

These mechanisms are complementary. Unix modes and the systemd sandbox do not
replace SELinux type separation because they do not provide the same mandatory
boundary across all files carrying a shared type.

## Released AosVM Persistent Storage Contract

The pinned upstream disk configuration creates four logical volumes during
provisioning:

| Logical volume | Allocation | Quota enabled |
| --- | ---: | --- |
| `downloads` | 40% of the volume group | No |
| `workdirs` | 30% of the volume group | No |
| `storages` | 20% of the volume group | Yes |
| `states` | 10% of the volume group | Yes |

The volume group is therefore fully allocated by the released configuration.
The Main Node mounts `/dev/aosvg/workdirs` as ext4 at `/var/aos/workdirs` and,
when SELinux is enabled, adds the fixed `aos_var_run_t` mount context.

The upstream Aos reference policy also maps `/var/aos(/.*)?` to
`aos_var_run_t`. The project policy adds a more specific mapping for the
component root to `vehicle_data_provider_store_t`. That specific path rule
works only when the filesystem supports and exposes per-inode SELinux labels.

## Observed Failure Mechanism

The provisioned validation Unit reported the workdirs mount with the fixed
`context=system_u:object_r:aos_var_run_t:s0` option. The component root and all
of its parents consequently appeared as `aos_var_run_t`.

The following mechanisms could not create the intended subtree label:

- the file-context rule was present but overridden by the mount context;
- the tmpfiles `Z` rule could create paths but could not change the visible
  mount-wide type;
- policy-driven `restorecon` could not establish a different subtree type;
- direct `chcon` returned `Operation not supported`, which is expected for a
  filesystem mounted with a fixed SELinux context.

The result is not an invalid policy or a failed rootfs update. It is a mismatch
between the provider isolation design and the provisioned storage mount
contract.

If the provider started in `vehicle_data_provider_t`, its active payload,
configuration, and trust files would still appear as `aos_var_run_t`. The
current least-privilege policy correctly denies that access, so the provider
cannot be safely assigned until the storage boundary is changed.

## Why Disposable Qualification Did Not Expose It

Before provisioning, `/dev/aosvg` and its four logical volumes do not exist.
The disposable image tests therefore exercised the rootfs directory and its
normal per-file labels. Provisioning later creates and mounts a new persistent
filesystem over that directory.

Rootfs FOTA replaces the rootfs but preserves the provisioned workdirs volume.
The successful disposable checks consequently proved the policy, runtime, and
fresh-image layout, but they did not reproduce the provisioned persistent
volume's fixed-context mount during a rootfs migration. Future qualification
must include both unprovisioned and provisioned storage states.

## Security and Lifecycle Requirements

Any accepted solution must satisfy all of the following:

1. Provider payloads remain independently updateable without rootfs rebuilds.
2. Provider data survives rootfs updates, clean reboots, and provider rollback.
3. `vehicle_data_provider_t` cannot read or execute unrelated AosCore workdirs.
4. `aos_t` can prepare, activate, roll back, recover, and garbage-collect the
   provider slots.
5. A failed storage migration prevents AosCore and provider startup rather than
   silently weakening policy.
6. Existing provisioned identity, certificates, and Cloud ownership remain
   unchanged.
7. Rollback to the previously installed rootfs remains understood and tested.
8. Provider storage has bounded usage and cannot exhaust critical platform
   storage without detection.
9. No solution depends on disabling SELinux or running the provider in `aos_t`.

## Option A: Per-Inode Labels on the Existing Workdirs Volume

Remove the fixed `context=` option from the workdirs mount and use the ext4
filesystem's normal `security.selinux` extended attributes. The generic
upstream file-context rule continues to label ordinary `/var/aos` content as
`aos_var_run_t`; the more specific project rule labels only the provider
component root as `vehicle_data_provider_store_t`.

### Advantages

- preserves the existing logical-volume and provisioning layout;
- does not require deprovisioning or a new Unit identity;
- preserves the selected Service Manager-owned component path;
- restores the intended SELinux type boundary;
- can be delivered by a replacement OEM platform rootfs;
- has the lowest implementation cost for the current validation VM.

### Limitations

- provider and Service Manager data still share filesystem capacity and a
  filesystem-failure boundary;
- workdirs has no quota enabled in the released disk configuration;
- the first boot requires a carefully ordered migration and recursive relabel;
- every existing AosCore path on the volume must receive a verified label;
- a boot-order defect could expose unlabeled data to a service before migration
  completes.

### Required Migration Design

A new immutable platform rootfs, provisionally named
`6.1.1-maninblack.3`, would:

1. remove fixed `context=` only from the workdirs fstab entry;
2. retain the upstream generic and project-specific file-context rules;
3. add an idempotent, versioned workdirs-label migration service;
4. order that service after `var-aos-workdirs.mount` and before every AosCore
   consumer of workdirs, including Service Manager and the provider bootstrap;
5. verify the exact block device, filesystem, mount point, and absence of a
   fixed context before relabeling;
6. relabel the complete workdirs tree using the installed accepted policy;
7. reject `unlabeled_t`, `default_t`, or an unexpected type anywhere in the
   protected scope;
8. verify generic AosCore paths and the dedicated provider subtree separately;
9. create a versioned migration marker only after all checks pass;
10. fail closed and keep AosCore stopped on any mismatch.

The provider store should be created or relabeled after the filesystem
migration and before Service Manager accepts a provider component. The
migration must be tested against a copy of the real provisioned overlay before
Cloud deployment.

### Rollback Considerations

A rollback from `.3` to `.2` would restore the previous fstab and again mount
workdirs with the fixed `aos_var_run_t` context. The per-inode labels would
remain on disk but be hidden by the mount-wide context. This is expected to
preserve existing AosCore behavior, but it must be qualified rather than
assumed.

Reapplying `.3` must be idempotent: it should expose the retained per-inode
labels, validate them, repair only policy-defined mismatches, and avoid
destroying component state.

## Option B: Dedicated Provider Logical Volume or Filesystem

Create an independently mounted persistent filesystem for the provider, for
example:

```text
/dev/aosvg/vehicle-provider
    -> /var/aos/components/vehicle-data-provider
    -> vehicle_data_provider_store_t
```

### Advantages

- strongest SELinux and filesystem ownership boundary;
- independent size, quota, mount options, and failure containment;
- easier capacity accounting and denial-of-service analysis;
- clean product-level separation between AosCore workdirs and an OEM platform
  component.

### Limitations

- the released volume group already allocates 100% of its capacity;
- an existing Unit would require volume resizing, an additional disk, or an
  offline storage migration;
- provisioning and disk-layout contracts must change for newly produced Units;
- rollback and recovery are materially more complex;
- introducing a QEMU-only extra disk would not by itself prove the intended
  production ECU design.

This is the preferred production-hardening direction when storage quota and
filesystem-failure isolation are explicit vehicle requirements. It is not the
lowest-risk correction for the already provisioned validation VM.

## Alternatives Not Accepted as Automatic Fixes

### Grant `vehicle_data_provider_t` access to `aos_var_run_t`

This would make the provider subtree accessible but would also make SELinux
unable to distinguish it from unrelated AosCore workdirs carrying the same
type. Directory modes provide partial discretionary protection, not an
equivalent mandatory boundary. This option is rejected unless a security
review explicitly accepts the broader trust relationship.

### Run the provider in `aos_t`

This collapses the component/platform boundary and gives updateable provider
code the privileges of AosCore. It is rejected.

### Disable or relax SELinux enforcement

Permissive mode would hide the integration defect instead of solving it and is
incompatible with the accepted platform security baseline. It is rejected.

### Store the payload in rootfs

Rootfs is read-only and replaced by FOTA. Coupling each provider release to a
new rootfs defeats the independent component lifecycle. It is rejected.

### Bind mount the subtree with a different context

The interaction between bind mounts, superblock security options, remount
restrictions, and the existing fixed-context ext4 mount requires a dedicated
kernel-level qualification. It must not be treated as a safe design shortcut.

### Store an additional filesystem image inside workdirs

A nested filesystem could create a separate label boundary, but it adds loop
device, image sizing, corruption, mount-order, recovery, and footprint
complexity. The released runtime rootfs also does not currently provide the
same loop-module environment used by the update initramfs. This option offers
few advantages over a properly designed dedicated logical volume.

## Recommended Decision

For the current R6.1 validation path:

1. select Option A as the proposed implementation;
2. insert a dedicated work package between rootfs validation and provider
   assignment;
3. build a new immutable rootfs instead of modifying `.2`;
4. qualify the migration on a copied provisioned overlay;
5. deploy the new rootfs only to the validation Unit;
6. assign provider `0.2.0` only after the complete SELinux gate passes;
7. keep the demonstration Unit unchanged until a separate promotion decision.

For the production vehicle architecture, retain Option B as a separate storage
architecture decision driven by capacity, quota, functional-safety, security,
and recovery requirements.

## Proposed Qualification Matrix

| Gate | Required evidence |
| --- | --- |
| Mount contract | Exact ext4 source; no fixed `context=`; expected safe options |
| Migration order | No AosCore workdirs consumer starts before migration passes |
| Generic labels | Existing AosCore workdirs retain `aos_var_run_t` |
| Provider label | Only the component subtree uses `vehicle_data_provider_store_t` |
| Negative access | Provider domain cannot read or execute sibling AosCore data |
| Positive access | Provider starts and reads its accepted payload and inputs |
| Lifecycle ownership | `aos_t` completes install, update, rollback, and recovery |
| Persistence | Labels, active slot, and state survive clean reboot |
| Rootfs rollback | `.3 -> .2 -> .3` behavior is understood and repeatable |
| Capacity | Reserve and maximum payload checks prevent workdirs exhaustion |
| Failure injection | Interrupted relabel or invalid type fails closed and recovers |
| Audit | No unexplained AVC denial, secret disclosure, or identity change |
| Cloud scope | Only the isolated validation Unit receives the replacement rootfs |

## Questions for Platform Architects

1. Is the fixed `aos_var_run_t` context an intentional security contract or a
   provisioning convenience for freshly created Aos volumes?
2. Does AosEdge intend to support independently typed platform-component
   subtrees inside `/var/aos/workdirs`?
3. Would upstream accept per-inode labels on the workdirs ext4 filesystem while
   retaining fixed contexts on downloads, storages, and states?
4. Which services can access workdirs before `aos.target`, and what ordering is
   required for a safe first-boot relabel?
5. Is a supported Aos utility available for labeling newly provisioned
   persistent volumes before core services start?
6. What is the expected rollback behavior when moving between a fixed-context
   rootfs and a per-inode-label rootfs?
7. Should OEM platform components receive a dedicated volume class in the
   standard disk configuration?
8. Are filesystem quota and independent failure containment mandatory for this
   provider, or are bounded checks within shared workdirs sufficient?
9. Should Service Manager expose a first-class persistent component-store
   abstraction instead of each runtime selecting a filesystem path?
10. Which part of this correction belongs upstream in AosEdge and which part
    remains an OEM vehicle-platform integration responsibility?

## Decision Gates

Implementation must not begin until the architecture review confirms:

- shared per-inode-labeled workdirs or a dedicated filesystem;
- ownership of the mount and migration changes;
- required capacity and quota isolation;
- safe ordering and rollback behavior;
- the exact validation matrix;
- whether the correction is OEM-only or an upstream candidate.

Provider assignment remains blocked until the chosen storage design is built,
deployed to the validation Unit, and passes the qualification matrix.

## References

- [R6.1 vehicle-data-provider FOTA design](r6-1-vehicle-data-provider-fota-design.md)
- [R6.1 first Cloud deployment](r6-1-first-cloud-deployment.md)
- [R6.1 runtime mechanism qualification](r6-1-runtime-mechanism-qualification.md)
- [OEM vehicle platform SELinux policy](https://github.com/alexmaninblack/aos-vehicle-platform/tree/feature/r6-1-fota-runtime/meta-aos-vehicle-platform/recipes-security/refpolicy/files)
- [Pinned upstream Aos disk configuration](https://github.com/AosEdge/meta-aos/blob/176da6346b1199f854106dede4cc49604174619c/recipes-aos/aos-setupdisk/files/aosdisk_main.cfg)
- [Pinned upstream Aos fstab recipe](https://github.com/AosEdge/meta-aos/blob/176da6346b1199f854106dede4cc49604174619c/recipes-core/base-files/base-files_%25.bbappend)
- [Pinned upstream Aos SELinux path rules](https://github.com/AosEdge/refpolicy/blob/c8be82c7e62f69cb6530de8cc1da3beb389a6681/policy/modules/system/aos.fc)
- [SELinux fixed-context mount behavior](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/sect-security-enhanced_linux-working_with_selinux-mounting_file_systems)
- [Linux mount SELinux options](https://man7.org/linux/man-pages/man8/mount.8.html)
- [systemd-tmpfiles label operations](https://www.freedesktop.org/software/systemd/man/systemd-tmpfiles.html)
