<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Offline Setup — Local Preparation Slice

- Status: Accepted bounded implementation detail of ADR 0018 / REQ-DEMO-025
- Version: 1.1
- Date: 2026-09-27
- Parent: [installation](README.md), [installed state](installed-state.md),
  [version selection](version-selection.md)

The native application wraps the existing transaction and selection engines;
it is not a second runtime orchestrator. This increment provides folder choice,
read-only preflight, verified installation with progress, and a separate explicit
local-data preparation/selection operation. It neither launches the demo nor
enrolls, provisions, contacts Cloud, reads credentials, starts Docker, or changes
the working developer installation. Cloud enrollment and native launch remain
separate open gates. A first-use checklist must say so, without a false Ready state.
The following separately authorized existing-access increment extends that
local-only slice; the original installation actions remain network-free.

## Existing OEM/SP access increment

For a selected, fresh installed instance only, the native window accepts two
explicit external PKCS#12 references. No developer defaults, key copying, tokens,
browser storage or new credential format. Files must be canonical, unlinked,
owner-private, single-link regular files. Local inspection checks certificate
validity and a common certificate-derived domain, not account roles. Preview
and save are separate operations; a metadata/configuration compare-and-swap
token rejects a changed file, configuration or selected package. Both profiles
are saved in the existing Demo Control configuration in one atomic write under
its existing writer. Interrupted writes and retained runs fail closed.

A third explicit action revalidates the saved pair and calls the existing
GET-only Cloud setup check: OEM/SP identities, association, arm64 support,
Factory model, Test set and required component/service delivery permissions.
Missing prerequisites are not authentication failures and are not created here.
The check does not publish, provision, start Docker or launch a runtime. Its
result is an observation, not a persistent Ready flag. A failure or changed
selection clears the prior visible result; no blind retry or TLS fallback.
The native Cloud helper has a two-minute deadline, including local verification.
It uses its own process group so a deadline cannot orphan a Cloud worker.
Termination is not success; completed local saves remain, pending writes require
reconciliation. This deadline does not apply to large offline installations.

Trusted setup sources include the reviewed Demo Control Python closure. They
run through its installed-instance context with the selected package leases;
the existing Cloud worker launcher verifies the pinned installed SDK before
execution. The installer does not import arbitrary selected-kit Python code.
Managed runtime use requires its already-created instance lock; it does not
silently recreate missing ownership metadata. Matching selection is checked
again under the lease, and exclusive/shared locking semantics are unchanged.
The native bootstrap remains small and contains no duplicate Cloud interpreter.
Local setup remains usable without Cloud access. New-account registration,
secure SDK enrollment, Cloud preparation and first launch remain open gates.

Qualification uses synthetic certificates and mocked authenticated API replies;
actual credential use requires a separately scoped live check. Test pair mismatch,
expiry, encrypted/unsafe files, retained runs, changed metadata/configuration,
repeat save, selection races, GET-only failure/missing/ready reports, redaction,
and native feedback without changing the working demo.

## Bootstrap and request boundary

The installer carries its own private Python, trusted helper sources and a
release pin reviewed independently of the chosen kit. It never executes code
from that kit. The builder authenticates the bootstrap Python files against the
pinned kit inventory before and after copying. Local ad-hoc signing is only an
engineering check, not Developer ID/notarization or redistribution approval.

The native window invokes a fixed embedded executable and helper without a
shell, with an isolated Python interpreter and a minimal environment. One
bounded JSON request on stdin selects `preflight`, `install` or `prepare`.
Unknown keys/actions, relative/linked paths, overlapping source/store/state,
unsupported platform, missing parents and foreign state directories fail closed.
No credentials or arbitrary command arguments belong in this protocol. Output
contains bounded progress and fixed diagnostics, not source paths or tracebacks.

Preflight validates arm64/macOS 26+, complete pinned inventory, disk reserve,
ownership/volume identity and an internal private-state destination compatible
with the Unix socket path budget. It does not hash every payload or write state.
Any source/store/state edit invalidates preflight. Installation consumes its
observed volume UUID and revalidates it. Preparation separately creates or
recognizes the private instance and selects the verified installed version with
the observed selection revision (compare-and-swap). Retained runs, busy owners,
changed revisions and incompatible state retain their existing blocking behavior.
No automatic repair, fallback disk, destructive cleanup or blind retry.

## Native lifecycle and truthful feedback

Only one operation runs in a window. Filesystem work and helper output handling
stay off the main UI thread. Inputs are frozen during an operation, stale replies
cannot update a later operation, and success requires both a valid terminal
result and a zero helper exit. Copy progress never means the version is ready;
verification/reused installation can remain indeterminate. Closing or quitting
during an operation is refused with an explanation rather than killing a writer.
After an OS/process interruption, a fresh explicit check/retry uses the existing
transaction reconciliation, not a remembered visual progress counter.

Installation ends at `INSTALLED_NOT_ACTIVATED`. Explicit local preparation ends
at `SELECTED_NOT_STARTED`. Docker application presence is not engine readiness;
OEM and one associated SP access, secure enrollment, dependency preparation and
first launch remain unverified. Two services keep separate identities/history.
No Ready/Connected/Running label may be inferred from successful local setup.

## Qualification

Test malformed requests, unsupported hosts, path/volume/state conflicts,
read-only preflight, corruption, revision races, repeat, process failure,
progress bounds, and absence of source execution/credential/runtime effects.
Compile only the new native target, exercise its protocol model, then inspect
the actual window and perform a bounded local setup against an isolated store.
Record separate evidence for source tests, native UI, real kit verification and
unchanged live owners. DMG, secure enrollment, retained-run updates, uninstall,
notarization, installed live E2E and a genuinely clean Mac are not closed here.
