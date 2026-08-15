<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-6 First Cloud Deployment

- Status: unsigned bootstrap accepted; stopped before bootstrap signing approval
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

## Validation Unit Concept

The validation Unit is a normal, independently provisioned AosCloud Unit that
is assigned a validation role in this project. It is not a special AosVM type,
a second Node inside the demonstration Unit, or a return to a multi-Node
topology. On the development Mac it is a second single-Main-Node VM with its
own persistent overlay, System ID, certificates, checkpoints, and Cloud
identity.

Disposable local VMs prove that an image boots and satisfies local platform,
security, persistence, and failure-injection gates. They cannot prove the
Cloud update path. The validation Unit provides an isolated end-to-end target
for publication, assignment, download, signature verification, installation,
restart, status reporting, Components visibility, and rollback without
changing the protected demonstration Unit.

The accepted promotion flow is:

1. build, qualify, freeze, sign, and locally verify immutable release bytes;
2. provision one new validation Unit from a clean official base;
3. target only that Unit through an isolated Unit Set or Verification Set when
   required by the Cloud workflow;
4. install and qualify rootfs `6.1.1-maninblack.1` on the validation Unit;
5. install and qualify provider `0.2.0` on the same Unit;
6. prove update, restart, failure handling, and rollback;
7. make a separate, explicit promotion decision before assigning any accepted
   release to the demonstration Unit.

The validation Unit is intended to remain a reusable staging target. Stopping
its VM makes the Unit offline in AosCloud but must not remove or regenerate its
identity; restarting the same protected overlay must reconnect the same Unit.
Every future release should pass this validation path before promotion when
the target and account capacity permit it.

## Local Qualification Result

R6.1-6.1 and R6.1-6.2 are complete. The incremental Yocto build reused the
retained source, download, shared-state, and build caches. The previous
`6.1.0` boot-plus-rootfs regression output was preserved separately inside the
builder before generating a clean release directory.

| Evidence | Accepted value |
| --- | --- |
| Integration build checkpoint | `df600fa3fa547a29e4e3970e38e84853cd24847a` |
| Complete local raw image size; not an OTA payload | 6,997,147,648 bytes |
| Complete local raw image SHA-256 | `28cc99b8b22f6e77cf6a5f2c7de6ec772eec4a1c8f8eb3ae4aa3b6dbfde5c6e2` |
| Rootfs-only `config.yaml` size | 608 bytes |
| Rootfs-only `config.yaml` SHA-256 | `7e46cc3b6ae1b1e279c5a460456802a48be7dce282736023d9265f8656f9ef6e` |
| Full rootfs payload size | 128,372,736 bytes |
| Full rootfs payload SHA-256 | `9152f59b052e9779eb89b43d8a52fba6eaa31fe56b4b4507fec8faa16d6e9232` |
| Frozen candidate metadata size | 841 bytes |
| Frozen candidate metadata SHA-256 | `7a969e57c53eaae266b97b3db555eb5d7aeea3afa2e9629b8b5bf3f634afa04a` |
| Boot component marker | `6.1.0`; omitted from the FOTA release |
| Rootfs component marker | `6.1.1-maninblack.1` |

The release output contains exactly `config.yaml` and one full rootfs
SquashFS. The structural validator rejected boot, incremental, stale,
unexpected, unsafe-path, symlink, credential, and publication inputs. The
complete raw image then passed two disposable, externally restricted ARM64
boots separated by a clean QMP/ACPI shutdown. Both guest gates passed the
rootfs version marker, read-only root, writable persistent partitions,
SELinux, cgroups, namespaces, one component runtime, empty provider store,
fail-safe launcher and health behavior, secret exclusion, and fatal-log gates.

The restart qualification also closed an evidence-lifecycle defect: disposable
boot logs and evidence are now rotated by generation instead of being
overwritten or blocking a second boot. The final disposable VM is stopped.
The Yocto builder, caches, build tree, and unsigned artifacts remain retained.

The unsigned candidate is frozen outside Git under the ignored R6.1 artifact
root. Its mode-0600 `candidate.json` records only the accepted manifest, graph,
platform, configuration, rootfs, version, sizes, and digests. No certificate,
key, token, Unit identity, Cloud identifier, or user-specific path is stored
in the record. A dedicated post-signing verifier and negative RSA/payload tests
are prepared, but no bootstrap signing identity has been accessed.

## Isolation Profile

| Boundary | Demonstration Unit | R6.1 validation Unit |
| --- | --- | --- |
| Local lifecycle | Existing protected `aosvm-main` | New `aosvm-r6-1-validation` |
| Disk | Existing provisioned overlay | New overlay from official base |
| Cloud identity | Preserved and untouched | Newly issued during provisioning |
| Node topology | One Main Node | One Main Node |
| SSH | `127.0.0.1:10022` | `127.0.0.1:10028` |
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

Result: pass. The validation profile passes static and dry-run isolation tests;
the demonstration profile still resolves to its running protected VM, while
the validation profile remains stopped and unprotected with no Cloud identity.

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

Result: pass. One unsigned, locally accepted rootfs-only release is frozen and
ready for a separate signing decision.

### R6.1-6.3 — Bootstrap signing approval gate

Current gate: stopped for explicit permission to access the OEM identity for
this exact rootfs candidate. After approval, sign and locally verify only the
accepted bytes. Do not upload.

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
