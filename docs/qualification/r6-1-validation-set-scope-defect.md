<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1 stale validation-scope defect

- Status: reproduced and contained
- Date: 2026-08-15
- Affected flow: component FOTA verification on `arm64`
- Installed rootfs before and after reproduction: `6.1.0`
- Candidate rootfs: `6.1.1-maninblack.1`

## Summary

A component Verification Batch retained a demonstration Unit as a validation
target after that Unit's set was changed from a Verification Set to a regular
release-candidate set. Approving the batch sent the rootfs desired status to
both the validation Unit and the demonstration Unit.

The batch was immediately disapproved. Both Units remained online on the
original rootfs and did not reboot. No private Cloud identifier, Unit identity,
certificate data, token, or raw log is retained in this record.

## Intended topology

| Unit Set | Verification Set | Member | Intended behavior |
| --- | --- | --- | --- |
| `R6.1 Vehicle Data Validation` | Yes | Validation Unit only | Receive the unapproved candidate |
| `Demo / Release Candidate` | No | Demonstration Unit only | Receive a later explicit campaign after validation |

Both Units were in the same Fleet. Each project-owned set contained exactly
one distinct Unit and had the role shown above before the reproduction began.

## Preconditions

1. A rootfs component version was uploaded while both Units still belonged to
   separate Verification Sets.
2. Cloud created one pending validation batch and associated it with both
   Units.
3. The demonstration set was renamed to `Demo / Release Candidate` and changed
   to `is_validation_set=false`.
4. The validation set remained `is_validation_set=true` with only the
   validation Unit as a member.
5. Read-only API checks confirmed both installed rootfs versions were `6.1.0`.

## Reproduction

1. Change the verification batch architecture state to `Disapproved`.
2. Observe that the batch becomes `Invalid`, but both Unit details retain the
   same pending validation target.
3. Change the architecture state to `Waiting` (`is_approved=null`).
4. Observe that the batch returns to `Waiting_validation`, but no delivery is
   started and the pending target is not recalculated.
5. Change the architecture state to `Verified` (`is_approved=true`).
6. Observe that both Units receive a desired status containing rootfs
   `6.1.1-maninblack.1`.
7. Observe download, install, and activation activity on both Units, including
   the regular demonstration Unit.
8. Immediately change the architecture state back to `Disapproved`.

## Expected result

Before accepting `Verified`, Cloud should do one of the following:

- recalculate the effective validation targets from current Unit Set roles and
  send the candidate only to the validation Unit;
- invalidate the stale batch and require creation of a new batch; or
- reject approval with an explicit warning that the recorded target snapshot
  no longer matches current Unit Set membership.

The demonstration Unit must not receive the candidate merely because it was a
Verification Set member when the batch was initially created.

## Actual result

- The current Unit Set roles were not reflected in the existing batch target.
- Both Units received the candidate desired status after `Verified`.
- Both Update Managers downloaded the rootfs and entered activation.
- Both rootfs instances remained on `6.1.0`; neither Unit rebooted.
- Disapproving the batch contained further progress but did not remove the
  pending references from Unit detail responses.

## Secondary observation

Both Update Managers reported a desired-status processing timeout while the
new rootfs instance was activating. This may be independent of the stale scope
problem and should be investigated separately after a safe single-target batch
is available. It is not used as evidence for the targeting defect.

## Questions for the platform team

1. Is Verification Batch target membership intentionally snapshotted when the
   batch is created?
2. What is the supported way to regenerate or reconcile a batch after
   Verification Set membership changes?
3. Should a Unit Set update automatically remove stale pending validation
   targets?
4. Can the API expose the effective target Units before an architecture is
   marked `Verified`?
5. Should approval be rejected when the current Verification Sets no longer
   match the batch's stored target snapshot?

## Current containment

- The architecture approval is `Disapproved` and the batch is `Invalid`.
- The demonstration Unit is online and reports rootfs
  `6.1.1-maninblack.1` after the 2026-08-16 controlled restart activated the
  stale staged slot. No new batch or Cloud mutation caused that activation.
  The owner subsequently accepted the working `.1` state as the current
  operational demonstration baseline; the stale batch remains invalid and is
  not approved by that acceptance.
- The demonstration Unit remains in the regular `Demo / Release Candidate`
  set.
- The validation Unit remains the only member of the project Verification Set.
- Public API v11 has no Verification Batch DELETE operation and no documented
  cancellation operation for the stale Unit pending reference. The component
  version also cannot be deleted while a Unit or Verification Batch references
  it, so `.1` remains an invalid audit record.

The follow-up activation is documented in the
[repository-rename repair record](repository-rename-vm-repair.md). It does not
change the original observation below: during the replacement `.2` batch, the
demonstration Unit remained on `6.1.0`.

## Replacement-batch result

A replacement `6.1.1-maninblack.2` batch was created only after the Unit Set
roles and membership were correct. Before approval, read-only Unit details
showed `.2` pending on the validation Unit and absent from the demonstration
Unit. Approval sent `.2` only to the validation Unit, which installed it and
returned online with no pending rootfs. The demonstration Unit remained on
`6.1.0` throughout.

This result narrows the defect to stale target retention in a batch created
before the topology change; it is not evidence that newly created Verification
Batches always ignore current Verification Set membership. Validation restart
also caused Image Manager to remove orphaned `.1` download blobs automatically.
No internal store was manually deleted. The stale `.1` Cloud reference on the
demonstration Unit remains for platform-team reconciliation.
