<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Clean Application Installation — 28 September 2026

## Scope and authority

The operator explicitly authorized retiring the old Test and removing disposable
installation-test data, then testing a clean installation. This supersedes the
earlier data-preserving stop for that Test only. Preserve Production, original
Factory .39/.31, source, credentials, published releases and release continuity.
`VDP-TIMEOUT-01` remains deferred and unchanged. This is empty application state
on the existing Mac, **not** a clean macOS or redistribution qualification.

Parent: [Stage 3 plan](../planning/active/installable-distribution-and-reproducibility.md).
Previous evidence: [existing-access handover](installed-existing-access-2026-09-28.md).

## Exact old-Test retirement

Read-only preflight confirmed Test Unit
`5395f7d6-2ff3-4d10-9e7f-efa85e7994eb` was provisioned/Offline in the selected
staging tenant, with its owned VM stopped and source detached. The normal
`demo retire` path then completed its durable sequence, without a new guest
start: local stop, Subject reconciliation, deprovision, membership removal,
Unit deletion, scoped backend cleanup and owned Test overlay/access removal.
Result: `COMPLETED / RETIRED`. This deletion is irreversible.

A fresh post-read proved the Test Unit absent and its local overlay removed.
Production's local Unit/Node/system identity and disk inode/size/mtime were
unchanged. Its historical Unit `d87ba9cb-b21f-45db-8773-553e52d0353e` was already
absent from the selected staging tenant **before** this operation and remained
absent afterward; do not claim that it was deleted here or that a live Cloud
Production was verified. No Production operation was performed.

The preliminary diagnostic's `factoryPreserved: false` field tested a guessed
`factory.qcow2` path, not the actual factory reference. It is not a missing-image
finding. The product retirement validates the authoritative per-role factories,
preserves the Production base and removes only the disposable Test factory copy;
the original Factory .39 remains bound into the verified kit.

## Test-harness correction

The first preflight stopped before Cloud mutation because a previous unit-test
subprocess had created 22 undeclared Python bytecode files at 14:29:56. Exact
inventory/magic/owner/link/open-handle checks preceded moving those files to
recoverable quarantine. The unchanged Cloud-runtime manifest then verified.
Two test modules now launch their Python children with `-I -B`; their 46-test
suite passed, and runtime verification passed both before and after the suite.
This was a harness contamination issue, not a Cloud, VDP or installer failure.

## Fresh package and installation inputs

Kit 009 contains the role-correct SP first-use checklist in the actual immutable
application export as well as the trusted native helper. Only `cloud_setup.py`
changed from Kit 008; all five large input groups, including CARLA and Factory,
are unchanged. No guest/container/simulator rebuild or credential copy occurred.
All 17,682 files passed transfer verification; application export: 86 files.
Logical kit size: 35,114,354,960 bytes. APFS clones share unchanged physical blocks;
logical size is not newly allocated disk usage.

Manifest SHA-256:
`f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`.
Source checkpoint: `22ee79e0e21709de34803c6db20047847138eba0` plus the reviewed
working-tree changes; no commit or push is implied.

Native preview 009 is independently pinned to this kit. Compile, native protocol
self-test, embedded helper rejection probe and strict local ad-hoc signature
verification passed. Executable SHA-256:
`4e14ed860128c2488d1a9d28bcfeed90ce6d6bdbfa7bde41d1f5207e79104680`.
Developer ID signing/notarization, DMG and external distribution remain open.

The old never-launched `~/SDV-Lab-InstallCheck` was explicitly unselected. Its
five inventoried private-state files were deleted after quiescence checks.
An empty `artifacts` directory required a separate final `rmdir`; no recursive
cleanup or credential deletion occurred. Kit 008 and its store are retained
as the compatible predecessor, not used as the fresh target.

Before beginning the actual native flow, both new destinations were absent:

- Work: `AosEdge-SDV/install-tests/stage3-clean-store-001`.
- Internal private state: `~/SDV-Lab-Clean`.

Free space was 98.34 GiB internal / 561.63 GiB Work. The fresh store must report
`reused: false`; retained local configuration or developer state must not be
adopted. Existing certificate references will be selected explicitly only after
local installation/selection. Registration of a new account is not simulated.

## Observed native flow

All three local actions were performed in native preview 009. Preflight passed;
the complete 17,682-file installation completed with `reused: false` and
`INSTALLED_NOT_ACTIVATED`. The private state destination was still absent after
installation, proving that file installation did not implicitly prepare a run.
Separate **Prepare local data** completed with selection revision 1 and private
directory mode `0700`. No developer configuration, release ledger, run journal,
VM directory or certificate copy was inherited.

Existing access was selected explicitly in the native window. Local inspection
passed, then **Use this pair** atomically saved the two external references in
a mode-`0600` configuration. Certificate inode/size/mtime/mode/owner metadata
remained equal to the pre-handover baseline. The subsequent real GET-only check
displayed **Cloud prerequisites observed — demo not started**, with all ten
checks confirmed: OEM, default fleet, arm64, Factory model, node type, empty Test
verification set, SP, OEM/SP association, VDP permissions and Brake/Tire
permissions. No Unit creation, provisioning, publication or deployment occurred.

Observed elapsed times are upper bounds from click to the first successful UI
observation, not instrumented operation durations: preflight 91.732 seconds,
installation 413.244 seconds, preparation 105.486 seconds, local inspection
17.138 seconds, reference save 27.082 seconds and Cloud check 27.752 seconds.
The native window remained responsive and showed progress during verification.
These observations do not close the historical cold-start file-open wait.

Free space after installation and preparation was approximately 98.24 GiB
internal / 561.62 GiB Work. The 32.7-GiB logical installed payload shared existing
APFS blocks; this measurement is not a guarantee for ordinary-copy destinations.

## Installed Presenter smoke

With the old listeners and vehicle processes absent, the existing canonical
installed CLI launched `ui serve` under this new instance. The executable and
`host_entry.py` both came from the installed manifest directory, with isolated,
no-bytecode Python; no developer entry point or build was used. PID 96566 owned
both loopback listeners, 18080 and 18600. The server reported successful startup.

After a fresh browser reload the actual UI showed **No controller created**,
**No Cloud Unit yet**, empty Brake/Tire slots, disabled advisory resets, Factory
`.39` and **Create controller**; Trace remained 0. A filesystem post-read still
found no managed run journal or VM data. This proves the installed Presenter can
start against clean state, not that a new VM, simulator or end-to-end run passed.
The installed Presenter remains running for the next step.

The native setup app has no launch action yet: using the accepted engineering
CLI does **not** close the discoverable native-first-launch exit gate. Before
provisioning, the empty Cloud card also renders `unit not verified` and empty
0–1 resource scales. This is placeholder presentation, not observed usage or a
Cloud access failure; retain it as a non-blocking first-use UX observation.

## Remaining gates

The subsequent [installed clean-state E2E](installed-clean-e2e-2026-09-28.md)
created the new Test and backend resources, but simulator startup exposed the
missing first-use Gateway server-TLS prerequisite. Its report supersedes the
empty-state smoke only for those explicitly observed steps; full E2E and native
launch remain open.

Secure new-user enrollment, guarded native first-launch UX, interrupted/retained
update cases, the previous cold-start wait and genuinely clean-host acceptance
are not closed by an installed-package command or a screenshot.

## Evidence

Ignored local evidence is under `CarlaSim/Build-distribution-stage2-20260926/`:
`clean-install-retire-*.json`, `cloud-runtime-test-pycache-quarantine-20260928/`,
`remove-empty-installcheck-completed.json`, `kit-009-refresh-20260928.json`,
`clean-install-native-{installed,prepared,cloud}.json`,
`clean-install-observed-timings.json`, `clean-install-files-success.png`,
`clean-install-cloud-success.png`, `clean-install-presenter-empty.png` and the
bounded single-use drivers. The `native-cloud` local audit proves reference-only
storage/preservation; the native Cloud result screenshot is the actual access
observation. Native artifacts and their build receipt are
under Work `AosEdge-SDV/setup-preview-009-20260928/`.
