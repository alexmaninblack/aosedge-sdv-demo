<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-6 First Cloud Deployment

- Status: replacement rootfs installed on validation Unit only; provider deployment blocked by persistent-store SELinux boundary
- Date started: 2026-08-15
- Baseline: AosVM `6.1.0`, one Main Node
- Rootfs release: `6.1.1-maninblack.2` (`.1` retained as an invalid incident record)
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
separation. The demonstration VM is outside the software-mutation scope of
this stage. Its Cloud grouping may be changed only to enforce the accepted
separation between validation and release-candidate deployment, and that
grouping change must not install, remove, or restart software on the
demonstration Unit.

The bootstrap update is **rootfs-only**. The boot component remains at
`6.1.0`; the full rootfs component advances to `6.1.1-maninblack.2`. This is a
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

`6.1.1-maninblack.2` is a SemVer release greater than the installed `6.1.0`
without claiming to be the future upstream stable `6.1.1`. Its bytes and
metadata become immutable after local acceptance. A different rootfs requires
a different version.

The credential-free release manifest SHA-256 is
`592ea37f0472a21c960b2d23a0bb63aa31d3c9ad0150adb14f48c41be24476fb`.
The regenerated pinned Ninja graph SHA-256 is
`9f95805690e95a4f998997c3052ecde6eb065c5a24e75817fd988ea80d96a8ab`.

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
4. install and qualify rootfs `6.1.1-maninblack.2` on the validation Unit;
5. install and qualify provider `0.2.0` on the same Unit;
6. prove update, restart, failure handling, and rollback;
7. make a separate, explicit promotion decision before assigning any accepted
   release to the demonstration Unit.

### Validation and promotion sets

The two VMs have different Cloud lifecycle roles even though they belong to
the same Fleet:

| Unit Set | Verification Set | Member | Purpose |
| --- | --- | --- | --- |
| `R6.1 Vehicle Data Validation` | Yes | Validation Unit only | Receive unapproved updates for qualification |
| `Demo / Release Candidate` | No | Demonstration Unit only | Receive only an explicitly approved post-validation campaign |

There must be exactly one Verification Set participating in R6.1 validation.
The demonstration Unit must not belong to any Verification Set because such
membership makes every applicable unapproved update a validation target. A
successful validation does not directly promote software to the demonstration
Unit. Promotion is a separate campaign decision targeting the regular
`Demo / Release Candidate` set.

Changing a Unit Set from verification to regular does not necessarily cancel
a pending validation batch that Cloud already calculated. Therefore the live
API scope, not only current Unit Set membership, is an activation gate. Before
submitting or changing the architecture approval state, Cloud must show no
pending validation target for the demonstration Unit. If an old target remains,
the batch must be safely reconciled or replaced while the demonstration Unit
is prevented from applying it.

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
| Complete local raw image SHA-256 | `155db230d85824d835ddd76bcfb7a70eafeaf54b7cce1e9dff957be41cccabd2` |
| Rootfs-only `config.yaml` size | 608 bytes |
| Rootfs-only `config.yaml` SHA-256 | `46dcb33805b05eab248090eec5a4756496a5a3795f150cd60d910edf8e8416dc` |
| Full rootfs payload size | 128,372,736 bytes |
| Full rootfs payload SHA-256 | `59c575891a3a0429c2a54c0f8793b0f3fc05ff3856817d35ce4870f2dba28def` |
| Frozen candidate metadata size | 841 bytes |
| Frozen candidate metadata SHA-256 | `575802c79859aafe2e81eeb6da8fa742b72bcce6dfd92290e145aae3a80c1fcc` |
| Signed deployment bundle size | 127,428,809 bytes |
| Signed deployment bundle SHA-256 | `579bed02d03833a230f8c611bf223b37e7096bdad5e5887a838708f2b0e5a606` |
| Signature algorithm and verification | RS256; pass |
| Boot component marker | `6.1.0`; omitted from the FOTA release |
| Rootfs component marker | `6.1.1-maninblack.2` |

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
The Yocto builder, caches, build tree, accepted unsigned inputs, and signed
bundle remain retained.

The unsigned candidate is frozen outside Git under the ignored R6.1 artifact
root. Its mode-0600 `candidate.json` records only the accepted manifest, graph,
platform, configuration, rootfs, version, sizes, and digests. No certificate,
key, token, Unit identity, Cloud identifier, or user-specific path is stored
in the record. A dedicated post-signing verifier and negative RSA/payload tests
were prepared before credential access. Explicit approval was granted on
2026-08-15 to use the OEM identity only for local signing and verification of
this exact bootstrap candidate. It did not authorize upload, provisioning,
publication, assignment, or any Cloud or Unit mutation.

The official signer validated the configuration and image paths, then created
the signed deployment bundle. The guarded verifier proved that the outer and
inner archives contain exactly the accepted configuration and rootfs bytes,
that the signed SHA3-512 records match those bytes, and that the RS256
signature validates against the OEM certificate. No signing material or
certificate identity was copied into Git, the image, the builder, or retained
evidence.

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

- pin boot `6.1.0` and rootfs `6.1.1-maninblack.2` independently;
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

Result: pass. Explicit permission was received for this exact candidate. The
official signer created a 127,428,809-byte bundle, and the guarded verifier
proved the accepted configuration and rootfs digests, signed hashes, and RS256
signature. No upload or Cloud operation was performed.

### R6.1-6.4 — Validation Unit and Cloud mutation approval gate

Result: pass. Explicit permission covers exactly:

- creation and provisioning of one new validation Unit;
- creation of an isolated validation Unit Set or Verification Set if required;
- upload/publication of the accepted bootstrap and provider releases;
- assignments only to the new validation Unit.

The later architecture review additionally authorized reclassifying the
demonstration Unit's existing development set from a Verification Set to the
regular `Demo / Release Candidate` set. This is a Cloud grouping change only;
it does not authorize a software update, restart, deprovisioning, or identity
change on the demonstration Unit.

### R6.1-6.5 — Provision and bootstrap the validation Unit

- create a new overlay from the official base and prove a distinct System ID;
- create and verify a standalone pre-provision checkpoint;
- provision exactly one Main Node with the existing accepted Unit Model;
- seal a distinct post-provision checkpoint and verify restart persistence;
- run a read-only API preflight against the exact new System ID;
- upload and assign the signed rootfs only to that Unit;
- verify `6.1.1-maninblack.2`, runtime-type reporting, an empty provider store,
  core health, logs, and restart persistence.

Current result: the new Unit was provisioned with exactly one Main Node and
reconnected from its sealed persistent overlay. The original `.1` batch was
created before the Unit Set role correction. It retained both Units as targets
through disapprove, waiting, and verify transitions, so the safety monitor
returned it to `Invalid`. This is recorded as a reproducible stale
validation-scope defect. See
[R6.1 stale validation-scope defect](r6-1-validation-set-scope-defect.md).

The replacement `6.1.1-maninblack.2` rootfs was rebuilt rather than relabelled
as metadata: Service Manager reads the active version from `/etc/aos/version`,
so the Cloud version and payload-internal version must agree. The retained
Yocto caches produced a new rootfs-only candidate. Two isolated local ARM64
boots, exact unsigned validation, frozen metadata, official signing, embedded
payload verification, signed-hash verification, and RS256 verification passed.

The `.2` upload created a new `Waiting_validation` batch after the Unit Set
topology was already correct. Before approval, the API showed `.2` pending on
the validation Unit only and absent from the demonstration Unit. The guarded
approval changed only the `arm64` architecture to verified. The validation VM
then downloaded, installed, activated, and rebooted into `.2`; AosCloud reports
it `Online`, installed on `6.1.1-maninblack.2`, with no pending rootfs. The
demonstration VM remained `Online` and installed on `6.1.0`; `.2` never became
its pending or installed version.

The old batch cannot be deleted through public API v11: its collection offers
GET, and its item endpoint offers GET and PATCH but no DELETE. The old
component version also cannot be deleted while a Unit or Verification Batch
references it. It therefore remains an `Invalid` audit record. On validation
restart, Image Manager automatically removed the old orphaned downloaded
blobs before fetching `.2`; no internal AosCore store was manually deleted.

### Persistent-store SELinux stop condition

The post-update gate found a separate platform-integration issue after the
successful rootfs deployment. On the provisioned release image,
`/var/aos/workdirs` is mounted with the fixed option
`context=system_u:object_r:aos_var_run_t:s0`. The provider design expects the
subtree `/var/aos/workdirs/sm/runtimes/systemd-slot-component` to use
`vehicle_data_provider_store_t`, but a fixed-context mount cannot hold a
different per-file SELinux label. Both policy-driven `restorecon` and direct
`chcon` are unsupported on that mount, and the current tmpfiles `Z` rule cannot
change the result.

This is not a batch-targeting or `.2` installation failure. It is an
incompatibility between the proposed provider isolation policy and the
provisioned AosVM persistent-storage mount contract. Provider `0.2.0` must not
be assigned until an accepted design supplies a real storage boundary, such as
an independently labelled persistent mount, or another policy model that does
not grant the provider broad access to all `aos_var_run_t` data. The builder,
caches, `.1` incident artifacts, `.2` accepted artifacts, and both persistent
VM overlays remain retained.

The evidence, alternatives, migration requirements, and questions for platform
architects are recorded in
[R6.1 Persistent Store SELinux Architecture Review](r6-1-selinux-persistent-store-architecture.md).

### R6.1-6.6 — Publish and assign provider `0.2.0`

- reverify the accepted signed provider bundle before upload;
- publish and assign it only to the validation Unit;
- verify component discovery, progress, final installed version, Components
  visibility, provider health, and empty-source KUKSA behavior;
- retain only sanitized evidence.

Result: not started. The persistent-store SELinux stop condition above must be
resolved and qualified in a replacement platform rootfs before provider
assignment.

## Stop Conditions

Stop without automatic retry if account capacity blocks a new Unit, the new
System ID is not unique, Cloud selects an existing Unit, more than one Node is
created, a target scope contains any other Unit, rootfs or boot versions do not
match the decision, the boot component appears in the release, signing inputs
change, rollback is unclear, or any action would touch the demonstration Unit.
Current Unit Set membership alone is insufficient evidence of safe scope; an
already-created pending validation target is also a stop condition.

## Exit

R6.1-6 is complete only when AosCloud shows provider `0.2.0` as an independent
component installed on the separately provisioned validation Unit running
rootfs `6.1.1-maninblack.2`, while the demonstration Unit and all unrelated
Cloud objects remain unchanged. The current persistent-store SELinux boundary
finding prevents that exit condition from being claimed.
