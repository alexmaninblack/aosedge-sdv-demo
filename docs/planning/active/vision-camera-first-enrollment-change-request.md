<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vision First Enrollment and Queued Camera Installation

- Status: Accepted on 2026-11-01; transient first-enrollment/activation/restart proof passed, signed consumer proof pending
- Prepared: 2026-11-01
- Owner: SDV Lab Source lifecycle and OEM platform
- Parent: [Vision implementation packet](vision-pilot-single-node.md#current-signed-bootstrap-and-native-camera-access-packet)
- Requirements: [Camera Access](../../requirements/components/camera-access.md), especially `REQ-CAM-005` and `REQ-CAM-006`

## Proven boundary

The independent Camera backend and signed bootstrap 0.2.0 are built on SSD.
The successor passed normal manufacture/OEM provisioning on the M4 in
`signed-bootstrap-02`; its own Cloud Unit and verification set are retained.
Main, engineering Vision and the previous failed native Unit remain unchanged.

The `native-camera-06` scenario revalidated the exact published Camera 0.1.0
and completed Source/CARLA startup. Before the explicit native send, Cloud had
already queued a Camera first install through automatic verification delivery.
The native transaction is schema 2, `install-or-replace`,
`waiting-for-safe-stop`, `hasPrevious=false`, with no installed record or active
slot. The independent store's immutable verifier passes. Source onboarding is
`PENDING`; runtime enrollment/binding and its SM credential declaration are
absent. Source's existing guard refuses any credential projection while that
transaction exists. Native FOTA requires those credentials to prove Safe Stop.
Repeated publication, provisioning or image construction cannot solve this cycle.

The initial connection also reached a physically stationary, braked, held
`MANUAL_READY` controller phase. Its unfinished Source journal is retained.
The current cancellation path requires the same operation in `SAFE_STOP`;
repeating that operation's Safe Stop request does not change its completed
Manual-ready phase. Do not forge a completed Source stop or discard this intent.

Native Camera activation, Aos reader, revocation and cold restart remain
unqualified. A scoped Camera-domain certificate-directory search denial was
also observed during startup; its exact executable/purpose and necessity remain
to be classified before any policy change. It is not a passed native AVC gate.

The failed native receipt remains unchanged. Independent stop reconciliation
confirms that the exact Source/Controller/CARLA processes and native VM are
off, their listeners released and the owned DNS helper closed. The unfinished
Source journal is deliberately retained, not relabelled as a completed Source
stop. An intermediate receipt-collection error was reconciled by read, without
replaying VM or Source actions. The SSD Builder and its DNS helper are stopped.
Private evidence is `native-camera-06/enrollment-boundary-stop-reconciled.json`.

The accepted correction passed `native-camera-08` using hash-pinned targeted
Source tooling and the same VM/Unit/image/Camera publication. Normal Source
authentication completed in 6.69 seconds; real physical Safe Stop was observed,
native Camera activation committed and a normal daemon restart established a
fresh epoch, rejected the old epoch and remained nonroot/capability-empty in
Enforcing. The 94.01-second scenario closed its Source/CARLA/VM owners and
verified three retained journals unchanged. This is a transient tooling proof,
not signed Source, Aos-reader, revocation or full Vision E2E acceptance.

## Accepted minimal correction

Extend only the fresh Vision first-enrollment case, not general transaction
reconfiguration or credential rotation:

1. Bind the same fresh Vision Unit, hardware identity, selected Source,
   assignment generation and existing Source-owned certificate pair.
2. Require a valid first-install transaction waiting for Safe Stop, no previous
   deployment, no active/installed component, and no existing runtime enrollment.
   Reject destructive phases, foreign identity, malformed state or partial/
   conflicting enrollment. No data migration or transaction cancellation.
3. Normally quiesce the sole native SM writer and verify that the complete
   transaction/candidate/selector state remains unchanged. Project the initial
   Source-owned runtime identity only through its existing fixed-path owner.
4. Restore the ordinary native SM owner. It alone resumes the same transaction,
   proves real Safe Stop and commits activation; retain all normal security and
   A/B validation. Source does not write slots or fabricate a safe-stop frame.
5. Define deterministic cancellation/recovery for this exact held, stationary
   first connection, including `MANUAL_READY`, without discarding an unknown
   intent or claiming it was a completed Safe Stop. Keep the simulated actor
   termination and journal reconciliation independently evidenced.

This is the accepted narrow exception to the no-projection-during-transaction
rule, not permission for general reconfiguration. An alternative would be an
explicit native bootstrap admission gate that prevents all first deliveries
until Source enrollment and Unit-set isolation finish; that is a broader new
startup gate and is not silently substituted here.

## Required proof and preserved boundary

Prove the exact case reversibly on the retained successor, with intent before
each action and rollback of any transient implementation. Add negative tests
for previous deployment, destructive phase, different Unit/key, partial state
and changing transaction. Verify first-create/idempotence, process/VM restart,
ordinary cancellation and failed-enrollment recovery. Then close the native
Camera daemon, actual Aos read-resource, denial/revocation and scoped AVC gates.

Do not rebuild CARLA, erase any transaction, remount rootfs, grant broad policy,
copy another Unit's keys, alter Main/VDP/Brake/Tire, create another Test to retry,
republish Camera 0.1.0, merge Main or publicly upload this engineering bootstrap.
The same image can be reused for a Source-tooling-only successor if the exact
runtime proof establishes that no image delta is required.
