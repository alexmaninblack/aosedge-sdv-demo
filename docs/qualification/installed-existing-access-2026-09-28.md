<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Existing-access Handover — 28 September 2026

## Scope

Continuation of the [Kit 008 native qualification](installed-first-use-2026-09-28.md)
under [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md).
The operator explicitly authorized using the existing staging OEM/SP pair in
the separate installed instance: references only and GET-only prerequisite
checks. The operator subsequently authorized stopping the developer demo to
free its processes/ports. Neither authorization means Finish, deletion,
provisioning, package publication, migration or a Production change.
`VDP-TIMEOUT-01` remains user-deferred and untouched.

## Preserved developer run

The idle Presenter and absence of pending Cloud component/service updates were
verified before the normal Test-only child operations. In order:

1. Simulation stop confirmed physical Safe Stop, detached the Test and stopped
   the owned CARLA/Gateway/Driving Control processes.
2. Graceful Test VM stop completed without forced power-off.
3. Both owned backend containers stopped with data preservation.
4. Owned Presenter windows and its verified idle server stopped.

Post-read confirmed the same Test/Production Unit/Node/system identities and both
overlay files remain. Test is locally STOPPED, source is STOPPED and no vehicle
is selected. No CARLA, Driving Control, QEMU, native Presenter or test-setup
process matched the final process check. The Production journal still contains
its pre-existing `RUNNING` field despite no QEMU process; this stale historical
field was preserved, not represented as a new observation or silently repaired.
No data was removed from either VM or backend and no Cloud object was deleted.

Test Unit remains `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb`, with Factory .39,
VDP 117/V3, Brake 92/V3 and Tire 49/V1 retained on its stopped disk. Production
Unit `d87ba9cb-b21f-45db-8773-553e52d0353e` and Factory .31 are preserved.
A fresh authoritative Cloud read confirmed that Test is still `provisioned`
and now `Offline`, with the same `system_uid`.

## Diagnostic-harness correction

The first shutdown preflight correctly failed closed with
`CLOUD_RUNTIME_UNDECLARED_FILE`. The earlier 13:52 diagnostic driver had run the
Cloud Python without `-B`, producing exactly 38 undeclared `.cpython-312.pyc`
files (1,023,824 bytes). These were not a Cloud or VDP product failure.
After exact inventory, owner/type/Python-magic checks and proof of no open
handles, only those files were moved to the recoverable evidence quarantine.
All originally declared Cloud-runtime files passed their unchanged manifest.
The subsequent read-only shutdown preflight passed. Diagnostic invocations now
use `-I -B`; no runtime manifest or security guard was relaxed.

## File-open localization

A same-volume clone of preview 007 was used for one synthetic-only native
inspection. Only that disposable copy added a fixed-stage wrapper around
`os.open`; it logs elapsed times and fixed labels, never paths, contents,
tokens or certificate data. It was ad-hoc signed locally, not published or
used with real credentials. The original preview and Kit 008 were unchanged.

The probe localized a **3.874-second** first `STORE_METADATA` open, followed by
sub-millisecond receipt, manifest and instance/package-lease opens. The second
read of the same store metadata was also sub-millisecond. Inspection succeeded.
This distinguishes the measured first metadata-open delay from a `flock`
deadlock; it does not prove the cause of the earlier approximately minute-long
wait. OS attribution and cold-start stability remain unqualified. No permissions,
trust checks, leases or endpoint protections were bypassed.

## Permanent installed instance

The unchanged preview 007 is now used with the existing Kit 008 store on Work
and a **fresh permanent internal** state path:
`~/SDV-Lab-InstallCheck`.
It does not inherit the synthetic certificates, artificial ledger/history,
developer journal, VM identity or backend data. Using an already installed
immutable package is not a second physical copy of the complete kit.

Native preflight, verified reuse of Kit 008 and separate local preparation all
completed. Selection revision is 1; private state is mode 0700 and configuration
0600. Native local inspection, explicit reference save and the real GET-only
Cloud check completed using the selected existing staging pair. An independent
local audit confirmed unchanged credential inode/size/mtime/mode, reference-only
configuration, and no synthetic ledger/history, current-run journal or VM.

Observed completion bounds (UI observation, not exact operation durations):

| Native action | Complete observed after |
| --- | ---: |
| Preflight | 28.7 s |
| Verified existing-package reuse | 158.3 s |
| Private local preparation | 131.6 s |
| Real certificate-pair inspection | 29.8 s |
| Reference save | 25.3 s |
| GET-only Cloud access check | 31.0 s |

## Real Cloud result and first-use correction

OEM, SP, their association, Default fleet, arm64, Factory model, node type and
VDP delivery permissions passed. Two independent blockers were observed:

1. `TEST_UNIT_SET_HAS_OTHER_UNITS`: the preserved old Unit still occupies the
   Test verification set. This is an expected ownership conflict, not an
   authentication failure. Stopping a VM is not Cloud unassignment. The native
   check must not remove, adopt or delete that member. A separate exact-target
   decision is required before freeing this membership for a new run.
2. `SP_PERMISSION_MISSING:service_providers_list`: a first-use checker defect.
   It reused the cross-role service-catalog display's permissions as an SP
   prerequisite. Provider discovery is an OEM operation already checked for
   the OEM/SP association; the SP catalog deliberately does not invoke it.

A synthetic-only reversible proof reproduced the false SP denial. Substituting
the actual SP checklist in memory removed that denial while preserving the OEM
association gate and all eight required SP-permission negatives. It also exposed
an omitted `deployment_bundles_list` prerequisite, already required by actual
publication/reconciliation. The monkeypatch was reverted at process exit; no
real account permission, key, trust or service behavior changed.

Source now uses an explicit SP delivery checklist in `cloud_setup.py`. The
cross-role catalog display is unchanged; required bundle reads are included.
Four regressions cover repeat checks without OEM-only SP permissions, the OEM
association deny, each required SP permission deny and the occupied Test set.
The contract records this role boundary. Results:

- Focused Cloud/setup/publication suite: 48 tests passed.
- Full Demo Control suite: 1,194 tests completed successfully, two intentional skips.
- Distribution suite: 206 tests completed successfully, one opt-in process test
  skipped in the default invocation; its 32-test version/lease suite then passed
  separately with that process guard enabled, with no skips.

The first focused invocation included one nonexistent test module name; the
48 real tests passed but the invocation failed on that collection error. The
corrected explicit module list passed. This was a test-driver issue, not a
product regression.

Do not infer runtime readiness or full first-launch completion from installation
or authenticated access. The secure enrollment/native first-launch gates remain
open. Kit 008 and the stopped developer run are not modified by this correction;
the subsequent native-preview proof is recorded separately below.

## Corrected native preview — real observation

Built **preview 008** on Work, using unchanged Kit 008 for the authenticated
bootstrap and installed SDK. Only the trusted setup/application helper closure
contains the SP-check correction; the selected immutable Kit 008 remains
unchanged. A future coherent runtime-kit refresh must carry the source change
as well; no in-place patch or completed runtime migration is implied.

Native protocol self-test, embedded bootstrap rejection probe and strict local
ad-hoc signature verification passed. Executable SHA-256:
`2818a732dd2b5412a374fb7f71d298ff523ad3f42ce59800f3d730088b068f29`.
This is not Developer ID/notarization or external distribution approval.
The source is `22ee79e0e21709de34803c6db20047847138eba0` plus the reviewed
working-tree delta; no new commit or push was requested in this step.

The previous idle preview was closed before opening this one. In the actual
native window, the same permanent instance and real pair were explicitly
selected, inspected and saved idempotently, then checked against staging.
Local inspection/save/Cloud completion was observed at **17.7/38.8/52.1 seconds**
respectively (observation bounds, not measured worker duration).

All nine non-membership checks, including **Brake and Tire delivery permissions**,
were Confirmed. Only **Test verification set: Conflict** remains. The window
correctly says the demo is not started. No Cloud writes, account permission
changes, new Unit, service publication, VM or Docker launch occurred. The same
reference-only credential configuration and selection revision remain intact.
The old Test's group membership is unchanged pending separate authorization.

The native first-use cold-start wait remains an unresolved qualification item;
this successful run does not establish its cause or close cold-start stability.
Secure new-user enrollment, guarded first launch, full wizard/DMG and clean-Mac
qualification also remain open. `VDP-TIMEOUT-01` was not investigated or changed.

## Evidence

Ignored local evidence: `CarlaSim/Build-distribution-stage2-20260926/`:
`installed-handover-*.json`, its single-use shutdown driver and
`cloud-runtime-pycache-quarantine-20260928/receipt.json`.
Real-access evidence: `installed-real-access-*.json`,
`installed-cloud-access-blockers.json`, `installed-real-cloud-blockers.png`,
`prove_sp_delivery_permissions.json`, `installed-cloud-fix-preservation.json`
and `installed-fixed-cloud-access.png`. Preview 008 and its compact
`build-receipt.json` remain under `SDV-Work/AosEdge-SDV/setup-preview-008-20260928/`.
The synthetic-only trace remains at
`/private/tmp/sdv8.k1qZuT/native-open-probe.jsonl`; the stopped diagnostic copy is
`SDV-Work/AosEdge-SDV/setup-open-probe-001-20260928/`.
No commit, push, large rebuild or broad cleanup is part of this step.
