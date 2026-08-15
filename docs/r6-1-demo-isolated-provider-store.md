<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1 Demo Isolated Provider Store

- Status: implemented and qualified in unsigned rootfs candidate `.11`
- Provider: signed and locally verified `0.2.0`, not published or assigned
- Validation Unit: rootfs `.2`
- Demonstration Unit: rootfs `6.1.0`

## Decision

Use a bounded nested ext4 filesystem for the demonstration provider component
store. It preserves the accepted SELinux boundary without relabelling the
existing AosCore workdirs filesystem or waiting for the production storage
architecture decision.

The implementation is part of the rootfs platform lifecycle. It is not part
of the provider payload and is not a generic AosCore feature.

## Why It Is Needed

Provisioned AosVM mounts `/var/aos/workdirs` with the fixed SELinux context
`aos_var_run_t`. A fixed-context mount cannot give only the provider subtree
the required `vehicle_data_provider_store_t` type. Granting the provider broad
access to `aos_var_run_t` would weaken isolation and was rejected.

The demonstration backend creates a separate filesystem and therefore a
separate SELinux superblock at the unchanged runtime path:

```text
/var/aos/workdirs
└── sm/runtimes/.vehicle-data-provider-store.ext4
        root:root, mode 0600, fully allocated, 512 MiB
                    |
                    | loop attachment owned by the platform
                    v
/var/aos/workdirs/sm/runtimes/systemd-slot-component
        ext4
        context=system_u:object_r:vehicle_data_provider_store_t:s0
        nodev,nosuid,noatime,errors=remount-ro
```

The logical component root and signed provider path contract do not change.

## Fixed Contract

- fully allocated store image: 512 MiB;
- one recorded filesystem UUID and fixed label;
- one active provider and one rollback slot;
- at least 1 GiB free before first creation and 512 MiB retained afterward;
- only bounded non-destructive `e2fsck -p` recovery;
- never reformat an existing unknown or damaged store automatically;
- provider sees only its mounted store and directory-search permission through
  the generic parents;
- no provider access to sibling AosCore workdirs;
- fixed non-login `aos-vdp` account and empty capability set;
- SELinux Enforcing at every accepted gate.

Store allocation, identity, mount, size, label, UUID, capacity, and policy
mismatches fail closed before the provider becomes active.

## Rootfs Candidate `.11`

Candidate `.11` integrates:

- steady-state loop support and confined store preparation;
- the Service Manager `systemd-slot-component` runtime;
- durable A/B prepare, apply, revert, rollback, and restart recovery;
- fixed launcher, health, reload, and systemd credential boundaries;
- provider DNS, TLS, KUKSA, random-device, and soft-dependency policy;
- the complete normalized ARM64 provider runtime dependency closure.

The targeted Enforcing matrix passed live telemetry, KUKSA restart recovery
without a provider PID change, invalid-credential fail-closed, process restart,
and DNS/TLS fail-safe behavior. A clean disposable `.11` boot passed the root,
component, policy, store, service-order, and secret-exclusion gates.

Exact candidate hashes are recorded in [the current baseline](current-baseline.md).

## Rollback Limitation

Installed rootfs `.2` does not contain the nested-store mount support. The
backing file would survive a `.11 -> .2` rollback, but it would not be mounted.
The provider assignment must therefore be removed or suspended before that
rootfs rollback. Transparent cross-backend rollback is not claimed.

## Production Limitation

This backend is suitable for the demonstration, not yet an OEM production
storage decision. Production integration must separately select and qualify a
dedicated logical volume, a controlled per-inode-label migration, or an
equivalent platform storage abstraction. That decision may replace the
backend without changing the Service Manager or provider component contract.

## Deployment Gates

1. Reverify and sign only frozen candidate `.11` under explicit approval.
2. Protect the validation Unit with a fresh offline checkpoint.
3. Deploy `.11` only to the validation Unit and qualify a clean restart.
4. Publish and assign provider `0.2.0` only to the validation Unit.
5. Demonstrate telemetry, source loss, recovery, provider update/rollback, and
   Cloud reporting.
6. Promote to the demonstration Unit only under a separate decision.

No step may clone a provisioned disk, expose credentials, target the
demonstration Unit implicitly, or rely on Verification Set membership as a
substitute for explicit target validation.

## Stop Conditions

Stop without automatic repair if the filesystem identity or capacity changes,
the nested mount or SELinux type is wrong, sibling workdirs become accessible,
an unexplained AVC or fatal service error appears, the accepted provider bytes
change, or Cloud scope includes an unintended Unit.

The historical rejected `.3` through `.10` experiments and their one-shot
diagnostic helpers are retained in Git history, not the supported source tree.
