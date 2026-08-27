<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Run State, Overlays and Cleanup — Design Reviewed

- Decision: `D4-021`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.1.0`
- Accepted subdecisions: D4-021.1 Factory Image and overlay layout, D4-021.2
  minimal current-run journal, D4-021.3 interrupted-operation recovery and
  D4-021.4 complete R0 ordering plus D4-021.5 functional/simulator cleanup,
  and D4-021.6 next-run readiness proof, 2026-08-23
- Revalidated behavior: D4-021.2 bounded per-operation recovery registry and
  D4-021.3 resource-scoped conflict coordination, 2026-08-25

The local demo keeps one qualified read-only Factory Image under
`.local/factory` and exactly two current-run copy-on-write overlays under
`.local/demo-current`. The overlays are named `validation.qcow2` and
`production.qcow2`, have mode `0600`, and both bind the exact Factory Image
digest recorded by its manifest.

The Factory Image is a qualified local copy of the CMP Factory output, not a
symlink or hard link to a mutable build result. M0 and R0 verify its digest;
the demo never modifies or removes it. A provisioned overlay is never copied
or reused as a next-run source.

No historical ordinary-run directory exists. `.local/demo-current` and
`.run/demo-current` represent the only current run. If they describe an
incomplete or uncertain run, M0 is blocked until reconciliation or successful
retirement. Successful R0 removes both overlays and current-run state while
retaining the unchanged Factory Image and manifest.

`.run/demo-current/journal.json` is a mode-`0600`, single-writer, atomically
replaced recovery record in a mode-`0700` project directory. It persists across
Launcher and Mac restart, but is neither a history database nor an
authoritative Cloud/backend store. It records only the current stage, bounded
start time, factory/manifest digests, relative overlay roles, exact current
VU/PU identity references, VISS certificate fingerprint, selected live source,
one bounded registry of current external operations, per-operation
resource-conflict keys, reconciliation state and sanitized last authoritative
re-read. Restart always causes new authoritative external reads for every
non-terminal operation.

The journal contains no key/certificate/PKCS#12 content, password, JWT, helper
capability, raw Cloud response, telemetry, functional payload, raw log, VIN,
personal absolute path, backend confirmation token or previous-run history.
`UNCERTAIN` forbids blind retry. A missing/corrupt journal beside current
overlays blocks M0. Successful R0 deletes it; incomplete R0 retains it until
reconciliation. No audience-visible Demo Run ID is introduced.

Per D4-026.2, the once-issued OEM, SP1 and SP2 Cloud certificates are stable
control-plane infrastructure outside this run-state tree. They are not copied
into an overlay or journal and R0 never deletes or rotates them. The Unit/Node/
`system_uid` and vehicle credentials referenced by the journal are disposable
current-run identities; Aos IAM Service-instance identity and short-lived
KUKSA JWT follow their separate runtime-derived lifecycle.

Platform, Brake and Tire operations may be in flight independently when their
exact resource-conflict key sets are disjoint. Before every call, one bounded
registry entry records the owning team, operation/candidate identity,
authority context, exact target, request fingerprint, resource keys, known
external IDs and `SUBMITTING`. An HTTP success moves that entry to
`RECONCILING`, never directly to `COMPLETED`; response loss or process/Mac
restart moves it to `UNCERTAIN`.

The same candidate/digest/publication profile or resulting Cloud object, the
same Batch/Campaign, and the same Unit/Unit Set are conflicting resources.
Provisioning, identity retirement, live-source handover/reset and R0
freeze/cleanup are run-exclusive operations. A conflict blocks only the
overlapping mutation; read-only navigation and fresh reads remain available.
A helper-capacity `BUSY` result leaves only the affected request `WAITING` and
requires a new explicit action rather than automatic queue submission.

Restart acquires only the journal-writer lock, validates the complete registry,
factory and overlays, and performs authoritative reads for every non-terminal
entry before any mutation. Each result is classified independently as
`APPLIED`, `NOT_APPLIED`, `CONTRADICTORY` or `UNOBSERVABLE`. Only proven
`APPLIED` advances its exact operation automatically. Proven `NOT_APPLIED`
still requires new explicit confirmation; the latter two outcomes keep only
overlapping scopes blocked. A corrupt registry blocks all mutations for
recovery but keeps diagnosis available. A `404` proves absence only with
independently known visibility.

Partial provisioning reconciles both roles before retry, disposal or a new
M0. Partial R0 resumes at the first unproven step and never repeats a proven
destructive action. Overlays remain until Cloud identity retirement and
backend cleanup are proven. Corrupt state is `RECOVERY_REQUIRED`; automatic
rollback and just-in-case deletion are forbidden. Qualification interrupts
lost responses, Helper, Launcher and Mac and every destructive R0 boundary.

R0 freezes new actions, captures final identities and detaches the live source,
then retires Validation followed by Production. Each Unit is made
authoritatively offline, deprovisioned and re-read; its old credential is
proved unable to restore `Online`; its stopped VM releases the overlay; exact
current-run log requests are deleted; its `system_uid` is removed from its one
role Unit Set and re-read; and the Unit is deleted with Unit/Node absence proof.
The persistent Unit Set objects and AosCloud audit/Batch/Campaign history are
never deleted.

Only after both identities are retired does R0 clean exact Brake then Tire
data, stop their local backends and reset the empty owned volumes, reset and
stop CARLA/controller/Gateway, destroy run-specific VISS/host material and
delete the two released overlays. It deletes current-operation receipts,
re-verifies the Factory Image/manifest and deletes the journal last. Any
uncertain step halts, retains recovery material and blocks M0. This is Unit
retirement and new manufacture, not FOTA/SOTA rollback.

Only the Demo Orchestrator cleans functional data. It selects exact current
VU/PU `system_uid` values verified by final Cloud evidence, executes Brake then
Tire preview/confirm/delete/prove-empty flows, keeps each short-lived
confirmation token in memory only and repeats preview after restart. Cross-
Function deletion is forbidden; backend containers stop and empty volumes
reset only after both products prove clean.

Simulator cleanup applies `SAFE_STOP`, aborts the active scenario and
Autopilot/Traffic Manager, performs the accepted D4-004 canonical free-drive
reset, removes the scenario obstacle, proves reset generation and detaches the
live source. One unified shutdown then owns Control UI, controller, Gateway and
CARLA. `ESC` and R0 use that same path. A bounded graceful wait may escalate
only to exact Launcher-owned PIDs/process group; broad process killing is
forbidden. No CARLA window/process, listener/socket, source assignment, run
actor or run state may remain. Installation, maps, assets, source and prepared
scenarios are preserved. Failure blocks overlay deletion and M0.

After R0, the Orchestrator exposes local `READY_FOR_M0` only when exact Cloud
and local checks match: retired Units/Nodes are absent, persistent role sets
exist empty, old credentials fail, Cloud history remains, the Factory Image
matches its manifest, all current-run files/identities/processes/listeners/data/
sources/actors are absent and the prebuilt artifact catalogue remains. A
missing proof is `BLOCKED`, not a warning. M0 creates overlays but no Cloud
identity; the next M1 proves fresh Unit/Node/system/VISS identities. Two
consecutive complete cycles qualify repeatability without retaining ordinary
run history; only a specifically designated formal run may retain the accepted
sanitized dossier.

Files:

- [`demo-run-state-profile.v1.json`](demo-run-state-profile.v1.json) — accepted
  D4-021.1–.6 design-reviewed contract.

This design-reviewed contract authorizes no overlay creation/deletion, VM operation,
Cloud mutation or reset.
