<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installer Consolidation Checkpoint — 29 September 2026

- Status: Kit 012 / Setup 020 native first, repeat and restart qualification passed; later first-use/distribution gates remain open
- Version: 1.5
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0`, with existing uncommitted changes preserved
- Plan: [Installable distribution and reproducibility](../planning/active/installable-distribution-and-reproducibility.md)
- Previous gate: [Native permission continuity](native-setup-signing-2026-09-29.md)

## Scope and preservation

The next accepted increment reconciles the already-proven service-Prepare
correction into a single immutable runtime kit. It does not replace or patch
the selected Kit 009 of the retained Test. Kit 010 already includes per-instance
Gateway trust initialization; the combined candidate must subsequently pass
installed-product checks in a separate empty instance.

`VDP-TIMEOUT-01` remains explicitly deferred. No Factory, CARLA or service
binary rebuild, Cloud mutation, provisioning, model reset or retained-Test
lifecycle operation was performed during this checkpoint. No signing key or
credential was used by the configuration-schema tests.

## Source-to-artifact reconciliation

Compared the current application export with Kit 010, manifest
`08b127ac9d9ba2836e2281d71006133dca418d25e988fda97a0276971c893cb0`.
Of 87 application files, exactly one differs:
`apps/demo-orchestrator/src/aosedge_demo_orchestrator/service_packages.py`.
No application file was removed; all five large input groups are unchanged.

The source correction accepts only the exact manifest-selected preparation
input root when loading service contracts. Foreign roots still fail closed.
The original defect and engineering continuation remain documented in the
[installed E2E report](installed-clean-e2e-2026-09-28.md); earlier successful
engineering preparation is not reclassified as native UI acceptance.

Prepared a bounded Kit 011 assembly helper under the ignored CarlaSim
qualification directory. It requires the exact Work-volume UUID, the existing
90 GiB internal reserve and 130 GiB Work reserve, an absent output directory,
and exactly the one expected source delta. It preserves large inputs and the
previous kit, then verifies the new transfer and complete inventory before
recording a new manifest pin. This was initially deferred for disk capacity;
the authorized storage work subsequently cleared that gate. The continuation
below supersedes that initial not-executed status.

### Kit 011 and Setup 019 continuation

Kit 011 assembly completed with manifest
`0ba77d7ee8775a6f9220ab98e82702af2361cc4275dc7b9977bc4f7a81e5c717`:
17,683 files, 35,114,362,428 logical bytes, 87 application files. Full transfer
and inventory verification took 118.05 seconds. The one-file delta above was
enforced before assembly; all five large input groups and Kit 010 remained
unchanged. APFS cloning reused the large inputs, with no Factory/Game rebuild.

The independently reviewed Setup release pin now selects Kit 011. Native
preview 019 was built and signed with the already-authorized Apple Development
identity and unchanged bundle identifier. Its designated requirement digest
is unchanged from previews 016/018:
`2cd6abe5ddd0ce9733dbcd1762af34ba64136679033c1cabd22d4482e16dd11c`.
Private bootstrap verification (2,430 files), native protocol self-test and
strict signature verification passed. This is local development signing,
not Developer ID/notarization or external redistribution qualification.

Actual native preflight passed for a new, separate package store
`SDV-Work/AosEdge-SDV/install-tests/stage3-kit011-store-001` and private state
`~/SDV-Lab-Kit011`. Native installation completed with `reused: false` and
`INSTALLED_NOT_ACTIVATED`; explicit preparation reached `SELECTED_NOT_STARTED`,
revision 1. No repeated removable-volume prompt was observed. The retained
Kit 009 selection was unchanged. Installation is not runtime readiness.

## Executed local gates

| Gate | Result |
| --- | --- |
| Distribution suite, process-ownership checks explicitly enabled | 258 passed, no skips; 7.617 s |
| Kit 011 continuation, before/after Setup release-pin update | 258 passed without skips in each run; 6.832 s / 8.954 s |
| Runtime paths, service packages, Factory/source, image/environment and local Gateway trust | 108 cases: 107 passed and one optional official-schema test initially skipped; 51.626 s |
| Initially skipped schema test, explicitly using the selected packaged Cloud Python | Passed; six service configurations; 6.817 s |

The schema validation used the official installed validator without signing,
uploading, or reading a private credential. These source/fixture results do not
qualify a new installed kit, Cloud first use, a cold simulator start or a clean
Mac.

The additional installed-Prepare/local-trust proof passed in 28.403 seconds,
using the candidate's private runtime and actual packaged Brake V1/V2/V3 and
Tire V1 products. Only the read-only Cloud release catalogue was a fixture;
product selection, ELF/license verification, configuration construction,
official schema validation, local version allocation and package receipts remain
real. Repeated preparation, prior-package preservation and foreign-root
rejection passed with OS denial of network, developer-tree reads and immutable
kit writes. Local Gateway trust first/repeat and new-process reads passed.
The retained Test journal/selection remained byte-identical during this proof.
This is offline installed-product evidence, not live Cloud/UI Prepare acceptance.

### Native repeat defect and approved correction

First Open Presenter passed with correct geometry/z-order. Repeating Open
failed before dispatch: the existing window owner had created a workspace-only
vehicle journal. The strict configuration reader correctly rejected it as
`Unsupported current journal`. The failed operation had no progress/results and
dispatch count zero; this was not a TCC, Cloud or layout failure. The incomplete
journal and request evidence were preserved. Only the empty probe's Presenter
was parked after read-only reconciliation; the retained Test's Presenter was
reopened through Setup 018. No VM, Cloud identity or service state was changed.

The user accepted separate window metadata in the existing workspace directory,
with Create Controller retaining journal initialization and no weakening of
validation. Twelve transient tests passed before source promotion. The source
fix changes only WorkspaceService and the simulator-start profile consumer.
It reads legacy workspace fields without rewriting their journal, rejects unsafe
or interrupted separate records, preserves run-ID recovery guards and keeps a
layout failure distinct from a successful simulator start. Requirements, HLA,
D4/interface clarification and both installation contracts were synchronized.

Targeted source regression passed 159 tests (5.537 seconds), including three
simulator-start consumer cases. Distribution regression passed 258 tests with
process guards enabled and no skips (7.586 seconds). The continuation below
records the resulting Kit 012 and actual native qualification, not a fixture
substitute for that gate.
Ignored evidence includes `kit-011-installed-proof-20260929.json`,
`kit-011-native-repeat-failure-20260929.json` and the bounded before-dispatch
reproduction. Do not repair or reuse the malformed Kit 011 probe as fresh state.

### Kit 012 / Setup 020 qualified continuation

Kit 012 manifest:
`6828c1dad9f3efd692bb7f052bc5f346a7d6d31ba997c45aa49268eca515892c`.
Full transfer/inventory verification passed: 17,683 files, 35,114,365,053 logical
bytes, 87 application files, 116.66 seconds. Exactly `workspace.py` and
`source.py` changed relative to Kit 011. All large inputs and the prior kit
were preserved. Setup 020 uses this independent release pin and the same
authorized Apple Development identity/designated requirement as Setup 018/019.
Its binary SHA-256 is
`b36eab989af1b79632d5758ae0387e7495336bbacd0e7d475c2ed1902860c43f`.
All 2,430 private bootstrap files, native protocol and strict signature checks
passed. No additional entitlement, TCC reset or new permission grant was used.

The actual native buttons installed the new store
`SDV-Work/AosEdge-SDV/install-tests/stage3-kit012-store-001`, then prepared
`~/SDV-Lab-Kit012`, revision 1. Installation was fresh (`reused: false`), not an
adoption of the Kit 011 failure. No repeated removable-volume permission prompt
was observed in this changed-build test. This does not extend the claim to a
new OS user, clean Mac, physical SSD reconnect or notarized distribution.

| Native scenario | Result | Workspace operation time |
| --- | --- | ---: |
| First Open on fresh private state | PASS; own windows/ports and verified z-order | 1.997 s |
| Repeat Open without stopping Presenter | PASS; same server, window host and session | 0.885 s |
| Quit/reopen Setup, only choose existing private folder | PASS; same Presenter, no source-kit selection required | 0.826 s |
| Ordinary Presenter close/server stop, then Open | PASS; new server/session/windows, persisted layout read | 1.509 s |

These times are the recorded workspace operation, **not** click-to-ready latency;
package verification and final UI observation add time. Each scenario left the
vehicle journal absent and kept separate window state owner-private (0600).
Operations ended `PARTIAL` only because CARLA/Controller were intentionally
absent; geometry and z-order were confirmed, and the native UI truthfully said
Presenter opened, not full demo ready. No uncertain operation or duplicate
Presenter appeared. The fresh browser showed `No controller created`, an enabled
Create Controller action, empty service slots and `Trace · 0` rather than the
previous configuration error. Create Controller was not pressed on the real kit.

The installed private interpreter also read configuration after Open with
network/developer reads/immutable writes denied by the OS. Missing Cloud
credentials correctly failed as `CLOUD_CREDENTIAL_MISSING_OR_UNSAFE`, without
inheriting credentials or failing on a bogus journal. Separately, all 44
image/environment tests passed (45.267 seconds), including real miniature-image
Create after window metadata: Create alone initialized the journal and preserved
the window record. No real Factory VM was created by that fixture.
The final distribution run after pinning passed 258 tests, no skips (9.514 seconds).
An additional 60 CLI/simulation/Gateway-trust cases passed (8.546 seconds).
Their initial run found two incomplete mocks without `environment.root`; the
fixtures were corrected to use their existing instance path, matching the real
EnvironmentService. No product guard or artifact bytes changed for those fixes.
Together with the 159 targeted cases, this slice has 521 passing source cases.

Compact native receipts are `kit-012-native-{first,repeat,setup-restart,server-restart}-20260929.json`
under the ignored CARLA evidence directory. The fresh probe was normally closed
after completion; its installation/window data and the failed Kit 011 probe were
preserved. A harness initially checked stopped-server sockets too early: ordinary
UI stop had succeeded but shutdown was asynchronous. A later read confirmed both
ports absent; no stop was replayed. The harness now waits boundedly for that
postcondition. This was not a second product defect or a reason to rebuild.

Documentation checks passed for 314 Markdown files, 662 stable identifiers and
38 diagrams. Internal free space remained about 164 GiB; Work about 484 GiB.
No additional cleanup, Git publication or VM/service build was performed.

At completion the retained Test's Presenter was reopened through its matching
Setup 018. Its Kit 009 selection/revision and VM/Unit/Node identities were
reconfirmed unchanged; source remains STOPPED and no vehicle start was requested.
Setup windows and the new empty probe are closed. Kit 012 is qualified separately,
not silently activated over that retained run. The installed read-only evidence
and `kit-012-retained-restored-20260929.json` preserve this distinction.

## Resource gate and cleanup disposition

Subsequent authorized [storage consolidation](storage-consolidation-2026-09-29.md)
restored internal headroom above the unchanged 90-GiB guard. Kit 011 assembly
and native Setup building subsequently completed. During native installation,
internal free space was 176,377,737,216 bytes and Work free space was
519,655,522,304 bytes. The measurements below describe the earlier blocked
checkpoint, not the current resource gate.

Internal free space measured approximately 88.8 GiB; Work approximately
560.8 GiB. The established 90 GiB internal reserve is not lowered merely because
large inputs can be cloned on the SSD. Large candidate assembly is paused at
that gate.

A bounded cleanup approval request covers only the three older complete test
kits `Runtime Kit`, `Runtime Kit 002` and `Runtime Kit 003` under
`/private/tmp/aosapp.dEU9Ge`. Before any removal, preserve their small manifests,
verify dependencies and stopped owners, and prove no open handles. Preserve
Kit 004, SSD packages, retained instances, Factory/VM data and warm build caches.
APFS sharing means their apparent aggregate size is not a promise of reclaimed
physical space. No cleanup had been performed or approved at that initial
checkpoint. The explicitly authorized continuation follows.

### Authorized cleanup result

The user subsequently approved deletion of those three exact old test kits.
The current runtime and distribution source contained no dependency on them;
the retained historical transfer helper refers to Kit 004, which is preserved.
An elevated exact-tree open-file check reported no holders or diagnostics.
The removal helper repeated that check immediately before deletion, verified
canonical owned directories with no symlinks, special files or nested volumes,
and confirmed each recorded source commit remained available in Git.

Before deletion, it copied and verified each application manifest, all five
input manifests, and the small manifest-listed public application source and
contracts to `Build-distribution-stage2-20260926/retired-kits-20260929` under the
ignored CarlaSim evidence directory. No credential or operator state was copied.
Per-target removal receipts and a final completion receipt are retained there.

All three exact targets were removed. Kit 004's directory identity and manifest
pin remained unchanged; `probe.py`, `offline.sb` and the parent directory remain.
No current SSD package, VM, Factory, warm cache or process was removed/stopped.
The obsolete binary copies are no longer recoverable in place; regeneration
requires the retained source/build inputs. Their manifests and public source
snapshots remain available.

| Measurement | Result |
| --- | ---: |
| Internal free bytes immediately before removal | 95,294,857,216 |
| Internal free bytes after removal | 95,324,172,288 |
| Observed free-space increase | 29,315,072 bytes / 27.96 MiB |
| Final internal free space | 88.78 GiB |
| Existing 90 GiB reserve | Not met; approximately 1.23 GiB still required |

The small observed increase is consistent with APFS shared extents. It is a
before/after free-space observation, not a measurement of exclusive reclaimed
extents; concurrent applications may also affect it. The earlier 98.22 GiB
directory-accounting total was never a physical recovery estimate. No further
cleanup target is implicitly authorized by this batch, and assembly has not
started or bypassed the reserve.

## Ordered continuation

1. Storage consolidation is complete and the unchanged reserve is satisfied.
   Preserve recovery copies, warm build inputs and the current Test.
2. Kit 011 verification and signed Setup 019 build are complete. Do not rebuild
   unchanged large components or reinterpret development signing as distribution.
3. Kit 012/Setup 020 independent-workspace qualification is complete in the
   recorded scope. Preserve its receipts, the Kit 011 failure and retained Test
   selection; do not infer live Cloud enrollment or full E2E from window tests.
4. Complete the accepted first-use contract for existing Subject references
   and secure new-account enrollment, then integrated installation lifecycle
   and cold-first-launch checks. Do not adopt Cloud Subjects merely by label.
5. Close release documentation/notices, external distribution signing and
   notarization, then clean-system installation and full E2E.

The installer is not yet a finished distributable, and clean-Mac testing is not
the only remaining gate. No commit, push, tag or external publication is claimed
for this checkpoint.
