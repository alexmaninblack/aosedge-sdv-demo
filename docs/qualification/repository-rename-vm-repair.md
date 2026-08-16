<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Repository-Rename VM Repair

- Executed: 2026-08-16
- Scope: host paths, VM lifecycle metadata, and DNS bridge ownership
- Provisioning, deprovisioning, signing, upload, assignment, and rollback: not performed

## Result

The solution checkout was renamed from `carla-aosedge-integration` to
`aosedge-sdv-demo` while the Main, validation, and Yocto-builder VMs were
running. Open file handles kept the processes alive, but their qcow2 backing
metadata and process ownership checks still referenced the obsolete path.

The validation and Main VMs were repaired one at a time. Each provisioned
overlay received a private APFS-clone checkpoint before an offline
metadata-only rebase to the same immutable AosVM base bytes. Provisioning
guards and private lifecycle metadata were updated in the same boundary.
`qemu-img check` passed before each restart.

After restart:

- both saved SSH host keys matched;
- both machine identities matched their pre-repair values;
- both guests retained a read-only root filesystem and SELinux enforcement;
- both AosCloud Units were `provisioned` and Online with one primary Main Node;
- the known `quotaon.service` exception remained the only failed unit;
- the validation Unit remained on `6.1.1-maninblack.2`;
- the existing local DNS-forwarder compatibility correction was reapplied to
  both installed rootfs slots;
- the Yocto builder retained its 220 GiB sparse disk, downloads, sstate, and
  workdirs and passed its AArch64 smoke test after restart;
- all three host DNS bridges now run from the `aosedge-sdv-demo` checkout.

Private VM checkpoints, machine identifiers, certificates, and raw logs stay
outside Git.

## Deferred `.1` Activation on the Demonstration Unit

The Main demonstration Unit booted `6.1.1-maninblack.1` after its controlled
restart. The preceding serial record showed `6.1.0`, so the restart activated
the stale `.1` update that had already been staged by the earlier Verification
Set scope defect. The repository rename did not deliver a new update and no
Cloud mutation was performed during this repair.

The Unit identity and registration remain intact, and the Unit is Online. The
`.1` software state is an observed current state, not a newly accepted release
decision. Automatic rollback is intentionally prohibited. Pre-cleanup
end-to-end acceptance must explicitly decide whether to accept `.1` as the
demonstration baseline or authorize a separate rollback plan.
