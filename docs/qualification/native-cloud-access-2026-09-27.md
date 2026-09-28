<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Existing Cloud Access — 27 September 2026

## Scope and verdict

Stage 3 existing-certificate increment of ADR 0018 / REQ-DEMO-025 /
UT-DEMO-025, under the [native setup contract](../../contracts/distribution-installation/native-setup.md).
One explicitly selected OEM and one associated SP for both independent services.

**Source/helper proofs and the bounded local native pair flow pass on preview
005; live Cloud qualification remains open.** Do not describe this as a finished
wizard, successful enrollment, Cloud connection or clean-Mac installation.

The native sheet separates local pair inspection, explicit atomic reference save
and an explicit GET-only prerequisite check. It shows certificate-derived domain
and validity, never key contents. Both profiles use existing Demo Control
configuration/locks and the selected installed SDK. No developer credential
defaults, copying of keys, alternate trust store, provisioning, publication,
Docker startup, runtime launch or Cloud-object creation.

## Implemented and tested boundaries

- Distinct, owner-private, unlinked, single-link PKCS#12 files; valid lifetime
  and matching domains. Encrypted certificates remain unsupported, not silently
  decrypted. Local validity is not proof of account roles.
- Fresh installed instance only. Retained run/overlays and interrupted writes
  block selection. Existing developer mode and active demo configuration are
  not adopted.
- Compare-and-swap covers certificate **filesystem metadata**, local config
  and package selection. No reusable certificate/key contents are hashed for
  display. Changed files/configuration invalidate the preview; both profile
  references are saved atomically. Exact repeat does not rewrite configuration.
- Existing authenticated Cloud checks read identities, OEM/SP association,
  arm64 architecture, Factory model and Test set. A first-use-only extension
  checks existing VDP/component and SP service-delivery permission names.
  It does not allocate Brake/Tire service identities or prove a later upload.
- Fixed projected labels/states; missing prerequisites are distinct from
  denied/conflicting ones. Successful checks do not mean the demo is started.
- Responsive native sheet, disabled duplicate controls, result/exit agreement,
  invalidation on path changes and no automatic retry. Two-minute Cloud helper
  deadline includes local work; it does not limit large installation operations.
  The helper owns a dedicated process group for bounded child-worker shutdown.

New deterministic coverage comprises seven orchestrator tests and four installer
protocol tests. Tests use generated synthetic certificates and authenticated-API
fixtures only. Source tests exercise mismatch, expiry, encrypted/unsafe files,
same-file pairing, retained/pending state, changed files/config/selection,
read-only checks, permission denial, repeat, public projection and no Cloud
prepare dispatch. Native protocol self-tests include deadline termination.

## Actual package and native evidence

Input remains complete Kit 007, manifest pin
`f62e35f7b068c9d06b30d6536c4400790f0e53dbff50e6ed61682a98f5fcd0b3`.
The existing `stage3-store-001` installation and isolated internal instance
`/private/tmp/sdv-setup-check.RrkxmM/state` are reused. The new bootstrap adds
reviewed Demo Control source closure, not another SDK/interpreter payload.
Each preview is approximately 83 MiB; no CARLA, Unreal, Factory or service build.

Preview 003 native executable:
`c0ef1b39b4466bb9004ad758935f77f5cf3c875f452d7f4c4c26d7b29a6110d8`.
Preview 004 native executable:
`3f6cc25bbc505c3a0f216d907f4ecbda67ec9d336f1d56cb5627f066e30d1430`.
They are local ad-hoc signed previews, not Developer ID/notarized distribution.
Build receipts bind exact source inventories. 003/004 are superseded diagnostic
candidates; neither is accepted as a completed native flow.

Current preview: `SDV-Work/AosEdge-SDV/setup-preview-005-20260927/`.
Native executable SHA-256:
`9058a0fafb84d20ee314792c496543cfcb803c43df924b4f81770d4206407bcf`.
All 94 source files match its build receipt. Native compilation, self-test,
ad-hoc signature and embedded bootstrap probe pass. The diagnostic group
shutdown and bounded stages are retained. Managed runtime use now opens an
existing instance lock without implicit creation; absent managed lock fails
closed, selection is checked again under the unchanged shared lease, and legacy
unmanaged behavior is preserved. A dedicated missing-lock test covers this.

The actual sheet is readable, selects the isolated instance and accepts test
paths. Live local inspection repeatedly waits at the installed-package lease
boundary. A one-second stack of the 003 helper showed `os.open` / kernel
`__open`; no Cloud call had occurred. The exact read-only helper was terminated
after collecting evidence. 004 displays the precise stage, automatically ends
the attempt at the two-minute limit, clears readiness and re-enables controls.
Selecting the same instance through the system folder picker did not remove
the wait. No trust, permissions or locks were weakened to pass the check.
**The precise cause of the earlier GUI-versus-command wait is not established.**
Initial observation of 005 still showed a busy package boundary; a later terminal
observation confirmed success before its deadline. A brief source revert based
on that intermediate observation was undone after the actual terminal result;
final sources match 005. Do not mistake an intermediate busy state for failure.

On 005 the native window confirms local inspection, both public validity dates,
reference save and repeat. Editing SP invalidates the displayed result and
disables the Cloud check immediately. A synthetic certificate for a different
domain produces `CLOUD_OEM_SP_DOMAIN_MISMATCH`, no save and no readiness. Restoring
the matching pair then passes inspection/save again. Repeat preserved the config
mtime (`1790526268`), size (332 bytes) and mode (0600). This is bounded positive,
negative and recovery UI evidence, not proof of real Cloud access. Track the
earlier delay as a stability follow-up until cross-launch/cold-start evidence
explains it; no OS/security policy was weakened.

A further UI test selected a new valid synthetic SP file and explicitly saved
it. This was a real atomic configuration change, not just a no-op repeat:
mtime advanced to `1790527338`, size to 336 bytes, mode remained 0600, and the
window showed **References saved — Cloud access not yet checked**. Its helper
exited normally. The completed test window was then closed. No diagnostic
helper was deliberately left running; the four live demo owners were unchanged.

With network denied, the embedded 004 helper and real installed SDK successfully
performed synthetic inspect/save/repeat in the same isolated instance: cumulative
times 5.58 / 12.33 / 18.99 seconds (approximately 5.58 / 6.75 / 6.66 per step).
Both saved references target synthetic files under a private temporary fixture;
they grant no real Cloud access. Repeat preserved config modification time, no
run journal was created, and all receipts reported no network/runtime effects.
This is a separate helper proof, not a substitute for native UI or live Cloud
qualification. The native Check Cloud access button was not used against fake domains or
real developer certificates.

## Enrollment finding and next actions

The bundled SDK is `aos-keys 1.10.0`. Its
`aos_keys.cloud_api.receive_certificate_by_token` first posts with the packaged
CA, then retries the certificate POST with default system trust on `SSLError`.
The default CLI also checks versions and may install a certificate into browsers.
Do not expose this unadapted call as secure native enrollment. The next enrollment
packet needs a reviewed one-shot strict-trust adapter, private output lifecycle,
explicit role/domain, redaction and uncertain-response reconciliation. No token
has been collected or request sent in this increment.

Before accepting complete onboarding: explain/qualify the earlier file-open wait
across native cold starts and qualify GET-only access with an explicitly selected
real pair. Secure enrollment,
explicit Cloud preparation, first launch, DMG, redistribution/signing,
retained-run update/uninstall and a genuinely clean Mac remain separate gates.

## Regression and preservation

Final orchestrator regression: **1,190 tests pass, two explicit skips**.
Final distribution regression: **206 tests pass**, including the real-process
exclusion fixture and the additional missing managed-lock negative.
Documentation gate: **299 Markdown files, 662 stable IDs, 38 Mermaid diagrams**;
`git diff --check` passes. The separate final Swift compile/protocol/deadline
self-test also passes; no additional large kit was built.

A timing-sensitive progress test initially counted wall-clock emissions, and
two older tiny-fixture tests depended on the host having 90 GiB free. As host
free space crossed that boundary, their intended assertions were masked by the
real disk guard. Their clocks/free-space inputs are now controlled in fixtures;
the separate low-space negatives and all product disk guards remain unchanged.
No large build was allowed past a failed space guard.

Live QEMU/CARLA/Driving Control/Presenter owners were preserved at
18914 / 19988 / 20208 / 51041. Only completed/diagnostic setup preview processes
were closed. No VM, service, Factory, backend, Cloud Unit, Production or video
asset was modified. No commit/push/tag or broad cleanup is implied.
