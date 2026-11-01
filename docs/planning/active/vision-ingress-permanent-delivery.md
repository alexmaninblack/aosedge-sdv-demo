<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Permanent Vision Ingress Delivery — Bounded Change Request

- Status: Accepted fresh .5 packet; diagnostic successor delta proposed below
- Version: 0.9
- Prepared: 2026-11-01
- Owner: SDV Lab integration and OEM platform
- Parent: [Vision implementation plan](vision-pilot-single-node.md#current-packet-authenticated-gateway-camera-ingress)
- Invariants: [accepted ingress contract](../../../contracts/vision-vm/camera-ingress.v1.json),
  [ADR 0019](../../architecture/decisions/0019-vision-pilot-single-node-lab.md),
  `REQ-CAM-001`–`REQ-CAM-006` and `D4-030`

## Purpose and current boundary

The operator accepted a **fresh development environment** after rejection of
`.4` failed to clear its assignment. This explicitly supersedes the earlier
preserve-current-Vision-VM restriction below, but only for current Unit
`4374bcb2-0613-419c-8ac9-e8458358c91c`, node
`d22dca91-5746-4218-ac1a-cc9bd489023c` and
`SDV-Vision-Camera-Image-Lab-Data` on M4. Retire that Unit through normal owners,
confirm its absence, remove its owned disks/checkpoints and disposable instance
state, and create a new Unit/VM from a corrected `.5` manufacturing image.
Preserve the four other instance roots, Main/VDP/Brake/Tire, selected shared
OEM/SP credentials, source, current DMG, Builder and caches. Keep compact failure
evidence. No unproven restore of the old disk or manual pending-state edit.

The fresh route is: exact retirement and empty-recipient preflight → source/unit
gates → warm `.5` Vision image plus matching rootfs artifact on SSD → signed
bootstrap and `.5` OEM publication while verification sets are empty → normal
fresh manufacture/provision → Source enrollment and initial Camera activation
→ Camera `0.1.1` upgrade → native read/revoke `0.1.4`/`0.1.5` and permanent ingress
acceptance. Existing owned model/set/service definitions may be reused after
proving no old Unit binding; they are not stale VM state. Do not publish a new
candidate until account-level recipient isolation is proven. CARLA, Main
Factory, Core/kernel revisions and unrelated services are not rebuilt.

The historical preservation-bound route below records the failed attempt and
its evidence; it is not authority to reuse or recover the disposable old VM.

### Fresh execution checkpoint

The old disposable Unit is deprovisioned/deleted and its child disks, backing
image and instance root removed (`vision-fresh-retire-02`, 10.96 s). Shared
credentials and all four retained journals are unchanged. Empty-recipient
preflight passed; `.5` was built on the SSD with warm caches (264.06 s), signed
and published once before fresh provisioning (`vision-fresh-oem-02`, 55.81 s).
The signed bootstrap manufactured/provisioned the new Unit normally
(`signed-bootstrap-04`, 187.43 s including transfer). Main and CARLA were not
rebuilt. This is not yet permanent-ingress acceptance.

The first Source connection passed but the scenario omitted physical Safe Stop
after stationary Manual, so native Camera activation correctly stayed pending.
The scenario now uses the existing control owner to prove real Safe Stop before
activation checks; no synthetic update permission is injected. Its observer also
normalizes native ComponentInfo's capitalized metadata fields without editing
the native journal.

Cold boot exposed a Source restore defect while that exact first install was
pending: persistent enrollment survived, but the volatile `/run` SM binding did
not. `vision-first-restore-proof-01` proves restoring only that binding, with the
same native transaction/candidate, unchanged persistent enrollment, Enforcing
and no immutable guest writes. The source correction follows the closed
[first-enrollment contract](../../../contracts/vision-vm/first-enrollment.v1.json).
No new VM, reset, re-enrollment, component publication or credential rotation is
needed for this correction. The remaining named scenario owns Camera `0.1.1`,
native read/revoke, media denial/staleness, restart/cold-boot and shutdown gates.

`vision-fresh-accept-06` then proved the complementary pending-first-install
reconnect path (131.97 s): normal Source advanced its assignment generation,
the exact old identities/material and native candidate remained unchanged,
only public binding generations and the volatile SM projection were refreshed
under a stopped writer, and real Safe Stop completed native Camera `0.1.0`
activation. This was explicitly a transient projection proof, not permanent
ingress acceptance. VM/Unit and all retained journals are unchanged; owned
runtimes stopped. The source function matches the live-proven candidate in
the regression gate. No immutable guest file or native transaction was edited.

### Permanent delivery result and remaining boundary

`vision-fresh-accept-07` proves native Camera `0.1.0` → `0.1.1` OEM delivery,
same store UUID, Cloud/native version agreement, permanent nonroot ingress,
idempotent start, empty ingress capabilities, read-only credential projection,
and wrong-role/anonymous/second-media-session denial. The new diagnostic Subject
binding targets only the fresh Unit; its service definition is reused. Read
probe `0.1.4` was published once. It becomes failed when it receives a pair,
so actual native JPEG-pair acceptance is **not complete**.

`vision-fresh-accept-08` reconciles and reuses the exact Camera and reader
publications without another upload/send/bind. It reproduces the reader failure
while Camera/ingress remain healthy and Enforcing. Before Source start, kernel
observations confirm UID 5000, reader group, read-only mount, no credential
mount, no active capabilities and the expected binary. It is not an observer
permission failure. Both attempts end with stopped owned runtimes, unchanged
fresh identity and unchanged retained journals.

The synthetic-only `vision-reader-diagnostic-02` reproduces the failure with a
14-byte SOF test envelope, excluding CARLA throughput/JPEG size as its cause.
This is fault isolation, not a valid live-image or pixel-decode claim.
`vision-reader-diagnostic-03` proves that the same native parser unit passes in
the full guest filesystem, segfaults (`-11`) in the actual container filesystem
view with automatic OpenSSL configuration, and passes there with that config
load disabled. The view-only unit runs as the diagnostic parent, not as the
Aos service identity; it does not replace native-Aos acceptance.

The hash-only fixture now explicitly initializes OpenSSL with
`OPENSSL_INIT_NO_LOAD_CONFIG` before SHA-256 and checks the digest API result.
It has no TLS/key/provider configuration contract. This changes neither system
OpenSSL settings nor Camera/Core policy, limits, credentials or signing tools.
Only the two fixture targets were compiled on the SSD (`fresh-reader-03`);
the Builder was stopped. `vision-reader-diagnostic-04` proves both default-env
and no-config parser units pass in the same container filesystem view. No
synthetic frames were sent in that final check. Scratch and owned VM stopped;
all retained journals match. Corrected bytes are **not published**.

#### Proposed bounded delta D1 — immutable diagnostic successors

Status: **requires operator acceptance; not publication authority**.

Replace the remaining diagnostic read/revoke pair with `0.1.6` read followed by
`0.1.7` revoke for the same `vision-camera-image-probe`, fresh Unit and existing
Subject only. Leave `0.1.4` immutable and `0.1.5` unused; no version overwrite,
new Unit/Subject, expanded resource, global crypto change or image rebuild.
Keep the existing configured OEM/SP owners and normal signer/deployer.
The executable publisher remains limited to the already accepted versions
until this delta is accepted.

After acceptance, reconcile the existing `.5`/Camera `0.1.1`/reader `0.1.4`
receipts; publish the fixed read/revoke successors serially and run the remaining
named native pair, network/credential denial, stale/disconnect, component
restart, retained cold boot, detach, revocation, AVC and shutdown gates. Preserve
the current VM, Unit, data, Main, CARLA, dependencies and caches. No Main merge,
push, public distribution or Perception/Assessment acceptance is included.

The reversible Gateway → Camera Access → native Aos reader proof passed.
Permanent ingress still needs the labelled launcher, systemd unit, narrow
SELinux policy, updated Camera payload and signed host Gateway/Source tooling.
The current Camera component archive cannot install those rootfs-owned files.
Do not retain the temporary policy loader, boot a diagnostic drop-in forever,
remount rootfs manually, rebase its overlay or manufacture a replacement VM.

The completed transient diagnostic authority covered only service versions
`0.1.2` and `0.1.3`; the latter has its read resource revoked. The operator
subsequently accepted this entire permanent-delivery packet, explicitly requiring
recovery first, preservation of the Vision VM/data and VDP/Brake/Tire, SSD builds,
no CARLA rebuild and no routine intermediate confirmations. Additional authority
is limited to the exact targets and gates below, not inferred from the old proof.

## Read-only inventory completed

`ingress-delivery-02` passed in 43.61 seconds on the current M4 Vision VM:

- Rootfs version is `6.1.1-vision-camera.3`; `/` is read-only ext4 on `/dev/sda3`.
- The SM declares native component runtimes
  `aos-vision-vm-1.0.0-main-qemuarm64-rootfs` and
  `aos-vision-vm-1.0.0-main-qemuarm64-boot`.
- Boot has `boot_a` and `boot_b`. There is **one** rootfs partition, not a
  proven dual-rootfs scheme. Do not infer atomic OS rollback from boot A/B.
- The rootfs runtime's declared health services are CM, IAM and SM; their
  presence does not prove Camera/ingress compatibility or completed recovery.
- Camera is installed and has no pending native component transaction.
- Enforcing remains enabled. No update, Source/CARLA launch, signing or Cloud
  mutation was attempted. The VM was stopped and four retained journals match.

`ingress-delivery-01` is a failed evidence-tool attempt (`KeyError`, before the
guest inventory ran), with stopped VM and unchanged retained journals. Its
failure is retained, not relabelled as success.

The pinned [SM rootfs implementation](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/src/sm/launcher/runtimes/rootfs/rootfs.cpp)
stages a rootfs layer, records pending state, requests a reboot, and runs a
health/confirmation cycle. This supports investigating the existing native
owner, not bypassing it. The upstream
[initramfs update helper](https://github.com/aosedge/meta-aos/blob/176da6346b1199f854106dede4cc49604174619c/recipes-core/initrdscripts/initramfs-framework/aosupdate)
uses trial mounting and a later in-place apply. Its installed revision was
subsequently checked as described below; it does not provide atomic rootfs
recovery from power loss.

## Accepted route

Use a separate Vision-only **native rootfs FOTA**, then the normal Camera OEM
component update. Keep the same logical VM, overlay/backing image, hardware ID,
Unit/node, Subject memberships, store UUID, credentials and application data.
The provisioning/manufacturing receipt stays frozen at its original baseline;
the observed updated rootfs version is a separate lifecycle fact.

| Stage | Exact boundary and completion gate |
| --- | --- |
| Freeze delivery and recovery | Inspect the installed initramfs/update-state/SSH and IAM persistence contracts. Prove a compatible stopped-VM checkpoint and bounded recovery/reconciliation procedure before publication. Do not promise atomic rootfs rollback or replay an uncertain update. |
| Prepare platform source | Package only the proven ingress launcher/unit/policy and existing native resource/store profile. Preserve static UID/GID, base Core/kernel, core IPC, compatibility and Main recipes. Keep ingress disabled until valid Source enrollment. |
| Prepare host source | Extend the existing signed Vision bootstrap/catalog for its exact sealed Gateway/Source resources; normal Source remains the lifecycle owner. No proof monkeypatch, arbitrary binary path, second trust owner or Main/package replacement. Keep the current DMG and manufacture image. Freeze this closed resource binding before signing. |
| Build on SSD | Run source/unit/targeted policy gates, then one warm Vision rootfs update artifact and package QA. Do not rebuild CARLA, Unreal, the Main Factory, model binaries or unrelated services. Separate rootfs-update bytes from a fresh manufacturing image. |
| Native OS delivery | Sign/publish the frozen Vision rootfs candidate through the configured OEM and native SM runtime, only to the current Vision Unit's exact verification recipient. Let the native owner perform trial/apply/reboots. No agent-side rootfs writes or pending-state edits. Reconcile before any resume. |
| Camera and reader delivery | Update Camera through its existing OEM A/B transaction owner, preserving rollback/data and real Safe Stop. Publish read/revoke diagnostic versions serially only to the existing Vision Subject; never change its members. |
| Acceptance and shutdown | One named scenario owns first start, repeat, actual native pair hashes, wrong-role/generation/network/credential denial, disconnect/stale clearing, component restart, retained cold boot, revocation, scoped AVCs, recovery and verified cleanup. Preserve evidence and stop only owned processes. |

## Exact additional authority

Subject to all preceding gates, authorize one closed delivery campaign:

- Current `SDV-Vision-Camera-Image-Lab-Data` only; no fresh VM or provisioning.
- Vision rootfs successor `6.1.1-vision-camera.5`, targeting only the existing
  Vision `rootfs` runtime. No boot component update or host-Mac OS update. If
  compatibility requires a boot update, report a separate bounded delta first.
- Camera Access `0.1.1` through the existing Vision Camera OEM component target.
- Existing `vision-camera-image-probe`: `0.1.4` read, then `0.1.5` revoke.
- One engineering-signed Vision bootstrap/tooling successor with the already
  selected Apple owner and exact base-program binding. No public distribution,
  Main merge/push, option A update or replacement of the current DMG.
- Normal guest reboots, a private stopped-VM recovery checkpoint and its
  ownership-checked use only under the accepted recovery/reconciliation plan.

Before mutation, re-read the exact Unit, node, runtime/component type, existing
versions and verification recipients. Refuse collision, another recipient,
changed identity, incompatible archive or an uncertain existing intent. Do not
edit shared Cloud models, adopt another verification set, rotate keys or use
staging/main-account assumptions in place of the selected certificate domain.

If the installed native update/recovery path cannot preserve the declared
state, stop at that exact boundary with evidence. Do not substitute a replacement
VM, manual disk surgery or a permanent diagnostic loader.

Perception/Assessment and their final result/display contracts remain the next
service packet, after permanent ingress acceptance. This request does not
authorize new motion authority, model deployment or performance claims.

## Execution checkpoint — 2026-11-01

Evidence below is retained in the private `vision-vm-m4` qualification records,
not embedded in the public source tree. The two flag-only Cloud changes below
are complete. The `.4` rootfs publication and native trial failed and were
recovered as recorded below; permanent ingress acceptance is not complete.

| Gate | Observed result |
| --- | --- |
| `ingress-recovery-01` | PASS, 131.15 s. Stopped APFS-cloned overlay was compared byte-for-byte and checked. After an owned marker was written through the normal running guest, the checkpoint was restored by an atomic same-directory swap and the same VM booted again. Marker absent; machine/provisioning identity, rootfs, Camera store UUID and SSH continuity retained. Both recovery and pre-restore disks are preserved privately on M4. |
| `ingress-boot-01` / `native-primitives-01` | Installed initramfs matches the cached archive and exact `meta-aos` revision `176da6346b1199f854106dede4cc49604174619c`; all four installed helper hashes match that source. No boot update is required by the inspected route. The permanent SELinux module and launcher compiled on SSD. No rootfs/image assembly was run. |
| `ingress-native-source-01` | PASS, 134.06 s. Exact permanent policy reads the sealed Camera-store payload, with nonroot transport, credential isolation, destination-drop and listener-denial proofs, disconnect/restart and fresh epochs. Stock policy and native store restored. No diagnostic publication; resource remains revoked at `0.1.3`. |
| `ingress-cloud-01` | BLOCKED, 48.42 s. Current Unit/node scope is valid and online, candidate versions/bundles do not exist, no pending rootfs/Camera transaction or send request exists. The account-level recipient guard found two additional verification Units. Vision was normally stopped and all four retained journals are unchanged. |

Rootfs trial/apply is owned by the native runtime and installed initramfs, not
the host scenario. The pinned helper mounts persistent `/var` outside the trial
root until its final mount move; root SSH home is on a separate `/home` mount.
The checkpoint remains mandatory because final rootfs apply is in-place, not
dual-rootfs atomic replacement. After any future publication, reconcile Cloud
desired state before booting a restored checkpoint; an unknown result is not
permission to replay the update or automatically boot an old disk.

### Account-level blocker and proposed bounded delta

The only selected recipient is Unit
`4374bcb2-0613-419c-8ac9-e8458358c91c` in
`SDV Vision Camera Image Verification`. Other verification memberships are:

| Verification set | Set ID | Other retained Unit |
| --- | --- | --- |
| SDV Vision Camera Verification | `55e87ad2-9c8c-4e0f-ad3c-02bbd362acd9` | `5abf6a2b-ae53-4995-a58a-91d9253057f7` |
| SDV Vision Verification | `581d4776-9679-4c48-8021-194539f2a5d3` | `2ac4b71a-2d06-4dd5-904f-7d2c24109f39` |

The existing `component_publication.recipients` guard correctly rejects these
additional recipients. Do not weaken it, infer isolation from offline guests,
or upload first and attempt to change recipients afterward.

The [Cloud deployment lifecycle](https://docs.aosedge.tech/docs/aos-cloud/entities/deployable_item)
documents automatic delivery to verification sets when the batch enters
verification. The [public v11 OpenAPI](https://api.aoscloud.io/api/v11/openapi.json),
version `6.1.97` checked on 2026-11-01, declares only the multipart `file` field
for bundle upload, with no upload-level recipient selector or skip-verification
parameter. A later explicit send request therefore does not establish that the
initial upload was isolated. No undocumented control was attempted.

**Accepted by the operator on 2026-11-01:** change only `is_validation_set` to
`false` on those two older Vision sets, keeping the sets, all Unit memberships,
Subjects, VMs, credentials and data. Keep the current selected verification set
unchanged. Re-read definitions/members before each exact mutation, record intent,
apply once, reconcile and rerun the account gate before build/publication.
This is the only exception to the current packet's prohibition on editing
shared sets. Do not automatically restore verification
eligibility after publication: that can reintroduce delivery to the old Units.
Main/VDP/Brake/Tire and `Test Vehicles` remain excluded.

This boundary is now closed by `ingress-verification-05` (49.93 s): only the
current Vision Unit remains an occupied verification recipient; both older sets
and their Units/memberships remain present. The first flag operation was
authoritatively reconciled from attempt 04 without replay. That older observer
did not retain a full definition preimage and initially misclassified the
expected nested flag projection in Unit membership data. The corrected observer
records the preimage; the second operation proves every other definition field
and membership unchanged. No Subject or Unit write endpoint was invoked.

The SSD Builder was expanded monotonically from 220 to 320 GiB after a private
stopped-disk checkpoint; native filesystem UUID and caches are retained. The
minimum 60-GiB build reserve is unchanged. Only a checksum-verified redundant
Builder copy of the `.3` manufacturing image was removed; the host input and
M4 backing image are preserved.

Native module packaging requires the refpolicy summary header for its generated
module selection. The source correction adds that header, not permissions.
`native-primitives-03` proves policy and launcher binaries identical to the
previously live-proven ones. Package QA now requires `camera_ingress.pp` before
rootfs work. The original manufacturing profile remains unchanged.

The signed host-tooling successor uses the optional, closed extension in
[bootstrap v1](../../../contracts/vision-vm/bootstrap.v1.json). It seals the
fixed Gateway/runner and portable libraries with the existing Apple owner;
the normal Source selects them without proof callbacks. The Factory `.3` image
and its platform provenance stay frozen, while the update platform/Gateway
revisions are bound separately. Only the fixed Gateway Mach-O has a 32-MiB
resource ceiling; other and total resource limits are unchanged.

### Rootfs trial, recovery and accepted successor

`rootfs-fota-07` produced the immutable `.4` artifact; `permanent-rootfs-01`
signed and uploaded it once to the isolated verification recipient. The native
trial did **not** commit. Its producer had depended on `do_rootfs`, omitting
`IMAGE_PREPROCESS_COMMAND` (systemd presets and final SELinux labels). Networking
did not start, so Core initialization could not confirm the trial. This is a
producer defect, not a reason to weaken health confirmation or retry the upload.

`ingress-native-revert-02` passed in 53.01 s. With CM/SM held stopped through
their normal service owners, transient network/SSH starts proved the diagnosis
without enabling units or writing rootfs. One normal guest reboot let the pinned
initramfs revert the unconfirmed trial to `.3`; no checkpoint disk was restored.
Machine/Unit/node identity, Camera store, component bytes, provisioning and SSH
continuity were retained. Native transaction flags cleared, Enforcing remained
enabled, Camera was healthy, and Vision/Source stopped. Four retained journals
are unchanged. The earlier `ingress-native-revert-01` interpreter import failure
occurred before a recovery mutation and is not acceptance evidence.

Platform `1f317ac7a70ae029f409a1e9a8d5c103f0224e05` now exports the fully
preprocessed Vision tree through a dedicated FOTA-only build task. It does not
depend on the shared link from an old manufacturing run or invoke filesystem,
boot, WIC or RW-partition assembly. `vision-image-preprocess-03` passed first and
idempotent-repeat gates in 42.07 s, with network/SSH presets and offline guards,
and restored Main build configuration. A Python 3.10 literal-glob diagnostic bug
was fixed separately: absolute guest symlinks must be enumerated without
resolving them against the Builder host. No corrected `.4` artifact was published.

The stopped VM is on `.3`; the final read-only Cloud observation still reports
`.4` pending and its batch `96a16904-0cfa-484c-ac70-0601ff90048d` in
`Waiting_validation`. The batch matches the exact OEM/component identity,
codename, version and ARM64 architecture; this API response does not expose an
`update_bundle_id`, so an upload-to-batch ID equality was not proven or assumed.
No rejection, approval, pending-state edit or replay is inferred from native
rollback.

**Additional operator authority accepted on 2026-11-01:** reject only that
exact failed `.4` batch through the documented verification approval endpoint,
authoritatively reconcile Cloud state, then sign/publish/deliver immutable
`6.1.1-vision-camera.5` to the same retained Vision VM and continue this packet.
Preserve `.4` and its evidence; never overwrite its bytes or reuse its version.
Re-read the exact batch/Unit and record intent before rejection. If rejection
does not close the pending state, stop and reconcile rather than manually
editing guest or Cloud state. Update the closed signed host descriptor to the
successor version without rewriting the earlier frozen bootstrap manifest.

`ingress-reject-01` subsequently passed in 7.02 s: one exact rejection changed
that batch to `Invalid` with ARM64 `is_approved=false`. Vision/Source stayed
stopped, their journal and all retained journals were unchanged. No Unit,
Subject, member, payload or version was deleted. The fresh account/guest gate
must still pass before the `.5` build and upload; rejection alone is not proof
that native and Cloud pending state have converged.

Subsequent `ingress-cloud-02` could not finish startup. Read-only
`ingress-startup-02` proved another `.4` squashfs trial with only
`do_update`/`updated`, no final apply, and inactive networkd. Rejecting the batch
did not clear the Unit assignment. The ordinary owner stopped the VM, retained
journals are unchanged, and no owned QEMU process/open overlay handle remains.
No `.5` build/publication had started at the reset decision. The accepted fresh
route above replaces further attempts to preserve this looping environment.

Camera `0.1.1`, probe `0.1.4`/`0.1.5`, permanent Source ingress and the final
security/restart acceptance remain **NOT_RUN**. The existing signed bootstrap
`0.4.0` is a prepared, uninstalled candidate, not a qualified deployment.
Preserve checkpoints, source, dependencies and caches. Builder and M4 Vision
were stopped after diagnosis; resume only through the named campaign.
