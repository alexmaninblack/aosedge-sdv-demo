<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current-run state, overlays and retirement

- Decision: `D4-021`; accepted lifecycle and narrow cleanup exceptions retained
- Contract version: 1.8.6; matches the retained executable profile, no journal/schema change
- Implementation and proof: [protocol map](../implementation-status.md)

## Purpose and profiles

The current-run journal coordinates one owned demonstration; it is not a
history database, Cloud mirror or backend authority. Installed Studio uses one
Test. An explicitly retained Production peer remains outside Test operations.
The expanded two-role profile and its full acceptance matrix remain allocated,
not prerequisites for an ordinary single-Test installation.

The [machine profile](demo-run-state-profile.v1.json) retains its frozen design
fields. Apply this effective contract and the
[installed-state boundary](../distribution-installation/installed-state.md),
not its older two-overlay/credential-probe examples as current Studio commands.
The operator uses [the current workflow](../../docs/operations/current-demo-workflow.md).

## Factory, overlays and state roots

The qualified source Factory is immutable and identified by its manifest.
Current copies/overlays live in the selected instance's `.local/factory` and
`.local/demo-current`; bounded run state lives in `.run/demo-current`.
Preserve source format and bytes: raw copies use `oem-demo-factory.img`; qcow2
keeps its declared path. Record format/path/digest rather than converting it.
A provisioned overlay is never a manufacturing source or a next-run template.

The role overlays use `validation.qcow2` and, only when that profile is selected,
`production.qcow2`, mode 0600. Fresh manufacture generates distinct identity;
there is no hidden Production VM for Test-only use. Unknown files, corrupt
journals, unresolved operations or a conflicting existing run block creation.

Installed program/input roots are separate from private state and mutable
outputs. Window layout uses its own existing workspace record; opening or
restoring windows does not create/repair a vehicle journal. Create Controller
initializes that journal. No new cross-run state store is introduced.

## Journal and operation ownership

`journal.json` is a mode-0600, atomically replaced single-writer record in a
mode-0700 directory. Keep current stage/start time, Factory/manifest identity,
relative owned files, current Unit/Node/system UID and role references, source
binding, VISS fingerprint, bounded external-operation registry, conflict keys,
reconciliation state and sanitized last authoritative reads. Mac/Launcher
restart does not make nonterminal entries trustworthy: reread their owners.

Never store key/certificate/PKCS#12 contents, passwords, JWTs, session capability,
raw Cloud responses, telemetry/products/logs, VIN, personal paths, backend
confirmation tokens or previous-run history. Infrastructure OEM/SP credentials
remain external references, are not copied into overlays and survive Finish.
Unit/Node and vehicle credentials are disposable run identities; native service
credentials retain their separate Aos/KAC lifecycle.

Record exact team/candidate, authority, target, request fingerprint, resource
keys and known external IDs before a call (`SUBMITTING`). HTTP success means
`RECONCILING`, not completed work. Response loss/restart means `UNCERTAIN`.
Independently classify the observed effect as APPLIED, NOT_APPLIED,
CONTRADICTORY or UNOBSERVABLE. Only proved APPLIED can advance automatically;
NOT_APPLIED requires new explicit intent. No blind retry or queue submission.
An absence/404 is meaningful only with independently established visibility.

Same candidate/digest/profile, resulting Cloud object, Batch/Campaign or
Unit/Set are conflicting resources. Provisioning, retirement, live-source
handover/reset and cleanup are run-exclusive. Installed operator mutations are
serialized; expanded disjoint-resource concurrency does not weaken writer or
uncertainty guards. Read-only diagnosis remains available. Corrupt registry
blocks mutations; helper BUSY is not permission for automatic replay.

## Stop, Start and identity retirement

Stop closes exact owned VM/source/backend processes, preserves disks/models/
history/releases and releases shared DNS only when no managed VM still uses it.
Start restores that retained Test; it is not creation, provisioning or Finish.
Initial SSH access is explicit secure enrollment, never credential discovery.
Controller ignition, Studio Stop/Start and host sleep are distinct; no operator
Park/Resume or automatic host sleep/wake recovery is reinstated.

Provisioning records native system UID, Cloud Unit/Main Node, authenticated
owner and scoped role membership. Partial registration reconciles those exact
identities instead of starting another SDK attempt. Cloud owns Online and
identity revocation. Current retirement observes Offline, deprovisions once,
rereads authority, stops exact owners, removes only current membership and
deletes the Unit with Unit/Node absence proof. It does not reconnect old
credentials as a routine deletion prerequisite or claim TLS revocation proof.
The broader security-negative matrix remains a separate qualification duty.

## Complete single-Test Finish

1. Freeze mutations and retain exact identities/receipts; stop/detach the owned
   simulation, VM and backend consumers through their normal owners. Reconcile
   uncertain effects before any new destructive intent.
2. Retire the exact Test identity and reconcile exact Subject/Set bindings.
   Fresh authorized reads must prove Unit/Node absence and empty desired and
   reported recipients. Do not invent a Production peer or delete permanent
   Subjects, services, releases, Fleet/Unit Sets or Cloud audit history.
3. Clean exact old-Test backend data/context through each product's accepted
   preview/confirm/delete/prove-empty path. Keep confirmation tokens in memory;
   repeat preview after interruption, never retain the token in the journal.
   Preserve peer/unrelated records. Backend callbacks must return literal True
   and persist completed stages; identity cannot be discarded first.
4. Validate terminal receipts, exact released file identity, backing binding,
   stopped owners and zero open handles. Journal per-file unlink intent, then
   remove only owned overlay/access/working-source files. Unknown content blocks.
   Recheck Cloud absence and backend proof before interrupted unlink continues.
5. Dispose of the completed single-Test journal last. Keep configuration,
   external credentials, release-number continuity, original Factory/artifacts,
   source, maps and scenarios. Next first use explicitly selects exact unbound
   Cloud references; it does not auto-adopt discoverable objects.

The single-Test compositor removes backend ownership/path references only after
their cleanup is proved. Its lifecycle receipt remains until remaining stages
finish. The exact old runner/source binding is needed even when creation or
installation failed; a fresh empty workspace is not proof of successful Finish.

### Narrow local cleanup cases

- **Identity-free collision placeholder:** an exact owner/label record with no
  create identity/receipt or attempted step is not an owned Cloud Subject.
  Retire local Test state without adopting/deleting that colliding object.
  An attempted or unknown external outcome is not this exception.
- **Unprovisioned local create:** require no Cloud/current-vehicle identity,
  successful manufacture and no handles. A never-booted overlay has no guest
  extents; a booted one requires the stopped provisioning-mode/no-local-provision
  proof bound to its unchanged overlay digest. Missing journal IDs alone prove
  neither. Remove exact overlay/access, owned working copy/manifest, journal last;
  preserve the original source artifact. This is not full provisioned R0.
- **Source failed before runner startup:** no synthetic terminal receipt. Allow
  only the exact stopped, never-assigned source whose journal-bound command
  identifies its same input/run directory, containing only owned JSON input and
  optional simulator log. Runner logs, unknown fragments or conflicting binding
  block this case; normal identity/link/handle/per-file guards still apply.
- **DNS bridge log:** remove fixed `dns-bridge.log` only for the journal's stopped
  owned bridge with no remaining process carrying that owner ID. A retained
  Production peer keeps shared DNS and its log.

## Retained Production and expanded retirement

Test retirement preserves the peer's overlay, PID, Cloud identity, DNS, shared
Factory and journal references. Its callback receives the full journal so
publication reconciliation cannot discard Production. Exact Test files and
terminal Test receipts alone are disposable; peer-targeted/unknown receipts
block. New Test creation may append a fresh overlay to that retained journal
with the same Factory identity, never truncate a peer or inherit Unit credentials.

The expanded R0 sequence retires Validation then Production, verifies exact
empty role membership and owner absence, cleans both products and all owned
sources/files, and preserves permanent infrastructure. Full dual-role, security,
partial-failure and two-consecutive-cycle proof remains separately required.
Do not interpret old profile examples as authority to delete a retained peer
or a successful single-Test cycle as proof of that whole expanded matrix.

## Completion and verification

READY_FOR_M0 requires matching authoritative Cloud/local evidence: retired
identities absent, applicable role/context bindings clean, owned processes,
listeners, files, source assignments and actors released, unchanged source
Factory/manifests and prebuilt catalog preserved. Missing proof is BLOCKED.
Cleanup is identity retirement/new manufacture, not FOTA/SOTA rollback.

Test lost responses, owner/Launcher/Mac interruption and destructive boundaries
with exact resumption rather than repeated effects. Scenario cleanup owns only
its actors, state and safe shutdown; it cannot force-kill unrelated processes or
invent stopped-frame evidence. Retain a formal sanitized dossier only for its
designated qualification run, not every ordinary demonstration.
Earlier version-by-version implementation diaries remain in
[Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/a6c095f12f77a947357f504811577ac37784fde0/contracts/demo-run-state/README.md).
This contract itself authorizes no live mutation, start or deletion.
