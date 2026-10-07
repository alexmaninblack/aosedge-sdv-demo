<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Offline Distribution Installation — Transaction Slice

The [native setup wrapper](native-setup.md) adds explicit local installation and
private-instance preparation, with separate explicit Cloud access/enrollment,
backend-image preparation and Presenter launch actions. The offline transaction
specified here still performs none of those later actions.

- Status: Implemented offline transaction; full native journey remains open
- Version: 1.0
- Prepared: 2026-09-27
- Owner: Demo Solution Team / integration distribution tooling
- Decision: [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)
- Parent: [Stage 3](../../docs/planning/active/installable-distribution-and-reproducibility.md#stage-3-implement-installation-and-first-use-setup)

## Authority and trust

This slice installs an explicitly selected complete local kit only. It has no
network, credential, Docker, process-control or runtime activation operations.
It never imports or executes code from the supplied kit. The expected
application-manifest SHA-256 is an independently supplied release pin; reading
a hash from the same untrusted folder is not authentication. The current
signed Setup supplies this pin. The engineering CLI requires it explicitly.

The pinned application manifest binds every exported application file and all
five input manifests. Their source locks must match the declared input pins;
each manifest binds its bounded inventory. Include the existing Factory
catalogue mirror and verify its equality to the declared preparation input.
All five groups are mandatory, even if a developer selector permits absence.
Reject duplicate JSON keys, traversal, absolute/noncanonical paths, case-fold
collisions, links, hard links, special files, unsafe modes, undeclared files,
oversized metadata, inventory budgets and changed sources. Preserve recorded
file modes and verify copied bytes before promotion. Reconcile verified file
identities and the final inventory before accepting the transaction. No
developer fallback.

## Private package-store layout

An explicitly selected store is either new or already carries a valid owned
installation marker. Never adopt a nonempty unrecognized directory. Its parent
must exist; never create a missing mount path. Resolve and validate the volume
UUID and ownership enforcement before mutation and before promotion. Bind the
marker to that UUID; a same-named replacement disk is not the same store.

The first transaction slice uses `store.json`, `writer.lock`, `staging`, `versions`
and `receipts`. The subsequent [selection/recovery contract](version-selection.md)
also permits private `quarantine` and package-use locks under `receipts`.
Its root and administrative directories are owner-private; payload
directories inherit that access boundary. Each version directory contains
the unchanged complete kit, identified by its full application-manifest digest.
A sibling receipt records the verified digest, counts and non-activation status.
No current-version pointer or writable application state belongs in this store;
the later managed selection record belongs to the private instance.

Use one exclusive nonblocking writer lock. Staging is addressed by the same
digest, contains a fixed transaction identity and a `bundle` child. Copy each
file into one fixed private temporary file, flush it, verify digest/mode and
rename it into place. Resume checks completed bytes; it does not blindly trust
a progress counter. An interrupted partial file is replaced only in this owned
transaction. Changed input, another digest or unknown entries block reuse.

On complete verification, atomically rename the staged bundle into `versions`
on the same volume. Write the verified receipt atomically. If receipt writing
is interrupted after promotion, an explicit repeat verifies the promoted kit
and completes the receipt. A corrupt existing promoted version is not repaired
in place or deleted by this slice. No active version can be overwritten.

Require enough free space for a full copy plus the existing 90 GiB engineering
reserve; do not assume APFS sharing saves physical space. A same-volume clone
may be used per file, with an explicit ordinary-copy fallback if unsupported;
both paths must pass the same digest checks. Recheck the reserve during copy.
The 90 GiB value is an engineering guard, not a published end-user requirement.

## Operations and evidence

`plan` is read-only and reports manifest/inventory/space eligibility, never demo
readiness or full payload verification (`payloadDigestsVerified: false`).
`install` creates or resumes one owned transaction. `verify` hashes an installed
version on explicit request. A repeated successful install returns reuse only
after verification. Fixed progress stages carry counts and byte totals, not
source paths, secrets or external responses. Status is
`INSTALLED_NOT_ACTIVATED`; all runtime/Cloud effects are explicitly false.

Source, user data and existing installations are preserved on failure. Do not
recursively clean up unknown paths. Automatic retention, repair of promoted
versions, active switching, rollback and removal are separate contracts. The
[engineering selection/recovery extension](version-selection.md) defines the
first three, without native activation or destructive removal. This
slice's resumable staging is not proof of those later operations.

## Deterministic acceptance matrix

| Obligation | Required isolated proof |
| --- | --- |
| Complete trusted inputs | Correct kit; wrong root pin; changed application/lock/input; absent group; extra file; missing Factory mirror |
| Filesystem safety | Traversal, duplicate JSON/path, case collision, symlink/hardlink, unsafe mode, unrelated destination and overlapping source/store rejected |
| Transaction integrity | New install, verified repeat, interruption/resume, partial-file recovery, post-promotion receipt recovery; one writer |
| Preservation | Original bytes/modes unchanged; foreign state untouched; no partial version reported installed; corrupt promoted version blocks |
| Storage binding | Insufficient space, absent/wrong volume, changed volume mid-operation and missing parent block |
| Runtime separation | No imported payload code, network/Docker/Cloud/VM action or developer fallback; installed is not ready |

Actual Kit 004 transfer/installation proof is required after deterministic tests,
using an exclusive disposable SSD store and preserving all live owners. Keep
compact receipts and distinguish clone allocation from logical byte count.

The [27 September qualification receipt](../../docs/qualification/offline-installation-2026-09-27.md)
records the passed first-install/repeat proof and explicit remaining gates.
