<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Autonomous M1 qualification

Accepted by the operator on 10 October 2026. This work packet refines the
script-first M1 checks in the [distribution plan](installable-distribution-and-reproducibility.md),
not the delivery stages or the vehicle lifecycle.

## Scope and ownership

Extend the existing qualification scripts in this repository. One command binds
the exact DMG, pinned SSH target, installed instance and evidence directory;
delivers and installs through signed Setup; runs the installed journey; collects
bounded diagnostics on failure; and normally stops owned demo processes.
Setup and Demo Control remain the authorities. Preserve shared Docker Engine,
Production, credentials, current diagnostic state and immutable candidate pins.
Do not silently replace an occupied installation or retire a Test to make a
selection succeed. No automatic rebuild, publication replay or full native
acceptance claim follows from engineering success.

## Explicit unattended test access

The operator also authorized reuse of the development Factory password for
automated Test enrollment. A locally supplied test credential may be provisioned
once into an owner-private installed-instance qualification profile, bound to
the instance UUID, staging domain and exact Factory SHA-256. The value is not
shipped in the DMG, committed, displayed, passed in argv/environment or copied
into qualification reports. This is an explicit test configuration, never an
implicit developer-Keychain fallback or access to Production. An invalid profile
fails closed instead of opening a dialog. An absent profile preserves ordinary
native first-use behavior; the unattended runner requires it before Create.
The ordinary console login, per-VM SSH key and pinned host-key exchange remain
mandatory. Known-host reuse after enrollment does not require the password.

This accepted test-only exception refines the interactive first-SSH rule in
[Demo Control](../../architecture/demo-control.md). It does not test native
password entry and must be reported as engineering access preparation.

## Execution and recovery

Check access and installed candidate before runtime mutations. Journal intent
and exact request/session identity before dispatch. A partial Create may bind
the same unprovisioned Test for diagnosis and shutdown only after its terminal
job and validated vehicle journal agree; it never becomes a passed Create.
Unknown outcomes remain uncertain and are reconciled, not retried. A terminal
failed mutation is not automatically replayed either.

Capture expected stage, fixed reason codes, bounded job-result and lifecycle
projections before cleanup. Do not persist raw logs, exception text, passwords,
Cloud tokens or certificate contents. Report operation/poll/soak timing and
human-input prerequisites without inventing a time split or ETA. Repeat only
affected checks after review; changed candidates use new evidence bindings.

Native consent, first-user input and layout remain a final distinct UI gate.
Local deterministic tests precede one incremental candidate build where product
code changed. Installed results must identify that new candidate; tests of
source or the older r5 DMG cannot qualify the new code.
