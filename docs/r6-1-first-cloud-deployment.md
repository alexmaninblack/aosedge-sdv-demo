<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-6 First Cloud Deployment

- Status: local release preparation in progress; stopped before signing or mutation
- Date started: 2026-08-15
- Baseline: AosVM `6.1.0`, one Main Node
- Rootfs release: `6.1.1-maninblack.1`
- Provider release: signed and locally verified `0.2.0`

## Decision

R6.1-6 uses a new, independently provisioned validation Unit. It must never
reuse an existing `new`, offline, or otherwise unowned Cloud Unit, and it must
never clone the demonstration Unit's overlay, checkpoints, System ID, Unit
identity, Node identity, certificates, or provisioned state.

The validation VM starts from the same immutable official AosVM 6.1.0 base
image but uses a new qcow2 overlay, host-access key, known-host record,
lifecycle guard, checkpoints, provisioning-attempt record, MAC address, and
loopback ports. The tracked `scripts/r6-1-validation-vm` profile owns that
separation. The demonstration VM may remain online and is outside the mutation
scope of this stage.

The bootstrap update is **rootfs-only**. The boot component remains at
`6.1.0`; the full rootfs component advances to `6.1.1-maninblack.1`. This is a
full rootfs image, not an incremental rootfs image, but its deployment bundle
contains no boot component. The pinned AosVM FOTA implementation explicitly
supports selecting components with their `enabled` fields.

This choice is required because the qualified project delta is one rootfs
package and the upstream and project initramfs package manifests are
byte-identical. No kernel, initramfs, bootloader, or boot configuration change
is part of the vehicle-data-provider runtime. Sending or updating the boot
component would add approximately 65.2 MB and an unnecessary boot-slot risk.
The expected unsigned payload is therefore approximately 128.4 MB rather than
193.6 MB, before Cloud cryptographic metadata and transport encryption.

`6.1.1-maninblack.1` is a SemVer release greater than the installed `6.1.0`
without claiming to be the future upstream stable `6.1.1`. Its bytes and
metadata become immutable after local acceptance. A different rootfs requires
a different version.

The credential-free release manifest SHA-256 is
`f7909fd95c93ac5a3821c921e3371778d489787c8d2cb8444d93ae273cfb1912`.
The regenerated pinned Ninja graph SHA-256 is
`d2916a739c6b702aa9218e5496b25a88f834c1bc9374f86297c7075174167650`.

## Isolation Profile

| Boundary | Demonstration Unit | R6.1 validation Unit |
| --- | --- | --- |
| Local lifecycle | Existing protected `aosvm-main` | New `aosvm-r6-1-validation` |
| Disk | Existing provisioned overlay | New overlay from official base |
| Cloud identity | Preserved and untouched | Newly issued during provisioning |
| Node topology | One Main Node | One Main Node |
| SSH | `127.0.0.1:10022` | `127.0.0.1:10024` |
| DNS bridge | `127.0.0.1:18053` | `127.0.0.1:18055` |
| Provisioning IAM | Not exposed | `127.0.0.1:18091` only during provisioning |
| MAC | Existing fixed development MAC | Dedicated validation MAC |
| Checkpoints | Existing protected pair | Separate pre/post-provision pair |

The OEM currently contains multiple existing Units, including Units that are
offline or incomplete. Their ownership is not inferred and none is eligible
for this work. The new validation Unit is identified only by the System ID
read from the new local VM and accepted only if Cloud reports exactly that new
identity with one primary `aos-vm-main` Node.

## Execution Gates

### R6.1-6.1 — Prepare the isolated local profile

- add instance-aware VM paths and an allowlisted validation instance;
- reserve distinct loopback ports and MAC address;
- keep the official base image shared and read-only;
- test that default demonstration paths are unchanged;
- do not create or provision a Cloud Unit.

Exit: the validation profile passes static and dry-run isolation tests.

### R6.1-6.2 — Build and freeze the rootfs release

- pin boot `6.1.0` and rootfs `6.1.1-maninblack.1` independently;
- disable boot and incremental-rootfs output;
- regenerate and pin the Moulin graph;
- run the incremental Yocto image build using the retained download, sstate,
  source, and build caches;
- boot the complete image in a disposable, externally restricted VM;
- repeat the platform, lifecycle, version, empty-store, SELinux, storage,
  secret-exclusion, and restart gates;
- generate a clean rootfs-only FOTA output;
- freeze its exact configuration, payload size, and digests.

Exit: one unsigned, locally accepted rootfs-only release is ready for a
separate signing decision.

### R6.1-6.3 — Bootstrap signing approval gate

Stop for explicit permission to access the OEM identity for this exact rootfs
candidate. After approval, sign and locally verify only the accepted bytes.
Do not upload.

### R6.1-6.4 — Validation Unit and Cloud mutation approval gate

Stop for explicit permission covering exactly:

- creation and provisioning of one new validation Unit;
- creation of an isolated validation Unit Set or Verification Set if required;
- upload/publication of the accepted bootstrap and provider releases;
- assignments only to the new validation Unit.

No permission in this gate applies to the demonstration Unit or any preexisting
Unit, Subject, Unit Set, Verification Set, component version, or assignment.

### R6.1-6.5 — Provision and bootstrap the validation Unit

- create a new overlay from the official base and prove a distinct System ID;
- create and verify a standalone pre-provision checkpoint;
- provision exactly one Main Node with the existing accepted Unit Model;
- seal a distinct post-provision checkpoint and verify restart persistence;
- run a read-only API preflight against the exact new System ID;
- upload and assign the signed rootfs only to that Unit;
- verify `6.1.1-maninblack.1`, runtime-type reporting, an empty provider store,
  core health, logs, and restart persistence.

### R6.1-6.6 — Publish and assign provider `0.2.0`

- reverify the accepted signed provider bundle before upload;
- publish and assign it only to the validation Unit;
- verify component discovery, progress, final installed version, Components
  visibility, provider health, and empty-source KUKSA behavior;
- retain only sanitized evidence.

## Stop Conditions

Stop without automatic retry if account capacity blocks a new Unit, the new
System ID is not unique, Cloud selects an existing Unit, more than one Node is
created, a target scope contains any other Unit, rootfs or boot versions do not
match the decision, the boot component appears in the release, signing inputs
change, rollback is unclear, or any action would touch the demonstration Unit.

## Exit

R6.1-6 is complete only when AosCloud shows provider `0.2.0` as an independent
component installed on the separately provisioned validation Unit running
rootfs `6.1.1-maninblack.1`, while the demonstration Unit and all unrelated
Cloud objects remain unchanged.
