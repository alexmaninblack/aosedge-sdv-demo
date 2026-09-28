<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Offline Setup — 27 September 2026

## Scope and verdict

Stage 3 local native setup increment, governed by the
[native setup contract](../../contracts/distribution-installation/native-setup.md),
ADR 0018 and REQ-DEMO-025 / UT-DEMO-025. This is a local engineering preview,
not a distributable DMG or a completed Cloud first-use wizard.

Verdict: **PASS for this bounded local setup increment**, including real native
UI installation/reuse and explicit local preparation. The remaining gates below
are not closed by this verdict.

The new AppKit window uses the existing installation/selection engines, its own
authenticated private Python, fixed trusted tooling and an independent release
pin. It installs immutable bytes and separately prepares/selects an internal
private instance. It never executes the selected source kit, launches the demo,
reads/enrolls credentials, starts Docker, provisions or contacts Cloud.

## Candidate identity

- Input: complete Kit 007, application-manifest SHA-256
  `f62e35f7b068c9d06b30d6536c4400790f0e53dbff50e6ed61682a98f5fcd0b3`.
- Final preview: `SDV-Work/AosEdge-SDV/setup-preview-002-20260927/`.
- App: `AosEdge SDV Lab Setup.app`; local version 0.1.0, build 1.
- Native executable SHA-256:
  `2b3f84204d5f4b8adeb3500ba1a00fe02533c255d2ce6758ff99d822c4dbeca1`.
- `build-receipt.json` binds all helper/native source digests and the release pin.
- Embedded bootstrap: 2,430 manifest-authenticated Python files; no developer
  Python, site-packages or environment override at execution time.
- Ad-hoc local code-sign verification passed. No Developer ID or notarization
  claim. The compiler ran with network denied; no Unreal/CARLA/VM rebuild.
- Output footprint: approximately 82 MiB per preview; 001 is superseded by 002.
  The existing 32.7 GiB logical Kit 007 is reused, not recopied for this UI proof.

## Deterministic and native checks

- Distribution suite: **201 tests PASS**, including 18 new setup/bootstrap
  tests and the opt-in real-process exclusion fixture; no skips.
- New proofs cover read-only preflight; exact bounded request keys; independent
  release pin; source/store/state separation; linked/noncanonical paths; internal
  state/Unix socket length; changed volume; corruption; foreign folders;
  prepare-before-install; missing receipts; stale revision; retained-run guard;
  first/repeat selection; progress bounds; secret-safe errors; authenticated
  bootstrap copying; absent/modified interpreter rejection without execution.
- Native protocol self-test passed: impossible progress, terminal ordering,
  missing result, wrong action and nonzero helper exit are not successes;
  verified-copy progress is capped below completion until the terminal result.
- The actual native window was inspected visually and through accessibility.
  Standard paste initially failed because the first preview lacked the macOS
  Edit menu. Reproduced before changing source; 002 adds the standard responder
  actions. Paste and Select All then worked in all three path fields.
- A real-kit preflight passed through the UI and correctly left installation
  and preparation as separate actions. While installation was busy, fields and
  repeat actions were disabled. Attempting to close displayed an explanatory
  sheet and left the transaction running; dismissing it resumed the same window.

Real-kit UI outcomes: **PASS**. The isolated Work store
`install-tests/stage3-store-001` returned a verified reused receipt for 17,682
files / 35,114,347,644 logical bytes, `INSTALLED_NOT_ACTIVATED`, no runtime or
Cloud effects. The separate **Prepare local data** button created
`/private/tmp/sdv-setup-check.RrkxmM/state` (test fixture, not an operator data
location), with owner-private directories and an authoritative revision-1
selection of Kit 007 on the original Work volume UUID. Final UI text was
**Local setup complete — Cloud setup remains**, **Version selected, not started**.
Docker was only reported as an application found, explicitly not engine-checked.
The helper exited; no VM, credentials, run journal or Cloud access was created
for the new instance. This actual UI run reused the already-installed package;
the prior transaction receipt covers real first-copy installation.

Observation bounds (not exact benchmark timings): install/reverification was
still busy at 58 seconds and observed complete at 130 seconds; local preparation
was busy at 68 seconds and observed complete at 119 seconds. Copy percentage was
not fabricated during indeterminate verification. Final screen layout was
visually inspected with the completion/checklist text visible and unclipped.

Orchestrator regression: **1,183 tests PASS, two explicit skips**. This does not
close native/live gates represented by skipped or separately qualified tests.

The first broad regression attempt was blocked by the execution sandbox for
local TCP/Unix test sockets and `ps` (32 errors, not functional assertions).
Those fixtures were rerun with the required local test/process permissions;
no production/runtime permission was widened to make a test pass.

## Preservation and next gates

The live QEMU, CARLA, Driving Control and Presenter owners were observed at
PIDs 18914 / 19988 / 20208 / 51041 before and after qualification. This work
does not stop, replace, relocate, update, provision or otherwise control them.
No Factory, service, model, backend, published release or video asset changed.
Existing dirty source work is retained; no commit, push, tag or cleanup is
implied by this increment.

Next: secure native OEM/SP enrollment and existing-access integration, explicit
dependency/Cloud preparation and guarded first launch through Demo Control.
The later [existing-access increment](native-cloud-access-2026-09-27.md) records
progress and its own native/helper/live boundaries; it does not turn this local
installation receipt into a complete Cloud-onboarding acceptance.
Official registration/email and OS/license acceptance remain operator steps.
DMG, signing/licensing/notarization, retained-run update ownership, uninstall,
volume reconnect, installed live E2E and a genuinely clean Mac remain open.
The current app explicitly reports selected/not started and Cloud setup pending;
it does not contain a fake ready/connected state or credential-entry placeholder.
