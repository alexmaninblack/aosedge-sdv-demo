<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Setup — Installation and First-use Actions

- Status: Accepted bounded implementation detail of ADR 0018 / REQ-DEMO-025
- Version: 1.9
- Date: 2026-10-01
- Parent: [installation](README.md), [installed state](installed-state.md),
  [version selection](version-selection.md)

The native application wraps existing transaction, selection and Demo Control
engines; it is not a second runtime orchestrator. Its installation actions
provide folder choice, read-only preflight, verified copying and explicit
private-instance preparation/selection. Those actions remain offline: they
do not enroll, provision, read credentials or launch the runtime.

Setup042 also implements the separately accepted actions below: existing Cloud
access, enrollment/recovery, exact Subject selection, Prepare backends and
Open demo. None implicitly starts Docker or adopts the working developer
installation. Installation, selection, Cloud access, image availability and
Presenter launch must report their own outcomes, never a combined false Ready
state. Current evidence and remaining native gates are in the
[baseline](../../docs/qualification/current-baseline.md).

## Complete local media accepted on 2 October 2026

The first consolidated DMG contains the signed native Setup app, a fixed sibling
`Runtime Kit` directory and a short Start Here guide. Setup may prefill the kit
field only from that sibling of its own app bundle. It must not search other
volumes, the developer checkout or previous downloads. A missing sibling leaves
the ordinary explicit selection path available; it does not select another kit.
Discovery starts no helper, writes no user state and does not imply verification.
Existing source edits invalidate preflight and all trust/inventory checks remain.

The media builder verifies the independent pin, exact complete payload inventory
and copied file hashes/modes, plus the supplied Setup signature and its embedded
pin. Output must be new, outside the inputs, with sufficient space. Preserve
current and rollback kits. A failed assembly leaves identified scratch/evidence,
never a reported successful DMG. Qualification mounts the resulting image read
only, verifies its inventory and authenticates the transferred image before
native M1 installation. There is no secret, developer state, Cloud call or new
runtime owner in media assembly. This increment is not the complete future
wizard or persistent Applications launcher.

## Existing OEM/SP access increment

The accepted [Cloud first-use completion](cloud-first-use.md) extends this
existing-access path with explicit exact Subject references and secure token
enrollment. Its tests and live qualification remain separately recorded; the
historical local-only slice below must not imply those later actions are offline.

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
Permission checks follow the authenticated role: provider discovery is required
from the OEM for its association check, not from the SP. SP delivery requires
service catalog/detail/version/recipient reads, service creation and deployment
bundle creation/listing; bundle listing supports publication reconciliation.
The cross-role service-catalog display is not a permission checklist for the SP.
An occupied Test set remains a conflict even when both roles authenticate and
their delivery permissions pass; setup must not remove or adopt its members.
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
Local setup remains usable without Cloud access. The subsequent explicit token
and exact-reference source implementation follows the linked first-use contract;
registration remains an official Cloud/operator action. Real enrollment,
ordinary first-use integration and clean-Mac acceptance remain separate gates.

Qualification uses synthetic certificates and mocked authenticated API replies;
actual credential use requires a separately scoped live check. Test pair mismatch,
expiry, encrypted/unsafe files, retained runs, changed metadata/configuration,
repeat save, selection races, GET-only failure/missing/ready reports, redaction,
and native feedback without changing the working demo.

## Explicit backend preparation accepted on 1 October 2026

`prepare-backends` is a separate native Setup button, before Create Controller.
Its only input besides `action` is the existing private `state` path. It uses
the independent Setup pin, existing installed instance/package leases and
Demo Control writer. No selection, installation or vehicle journal is created.
A retained vehicle journal or pending write blocks this first-use operation.
The source kit is not needed again; consumed locks and backend inputs are
verified against the selected installed inventory before use.

Docker Desktop's engine must already be running and its current context must be
`desktop-linux`, pointing to the current user's local Docker Desktop socket.
Setup uses the fixed Docker application executable, a clean environment and
that explicit local endpoint. A missing engine, remote context, different
engine identity or non-Linux/arm64 engine blocks without changing settings.
Setup neither starts nor installs Docker or accepts its license. An already
running engine needs no dashboard opening/closing and is preserved after demo
shutdown; engine restart is not an ordinary qualification step.

Verify the pinned untagged archive, then inspect the two exact immutable image
IDs. If both are present with their pinned platform/source/team identities,
return a fresh observation without importing. Otherwise load the unchanged
archive once into that engine, with bounded execution, and re-inspect both IDs.
Do not pull, build, tag, remove images, start containers or access Cloud. Other
images, tags, containers, volumes, credentials and run data remain unchanged.

Before dispatch, atomically record only the selected manifest pin, engine ID,
archive digest and attempted state in the existing instance's private
`.local/demo-control/backend-preparation.json`, under its existing writer.
This is an attempt record, not a readiness authority. Unsafe, malformed or
pending records block. On response loss/reopen, inspect the same engine and
exact IDs first: both verified images reconcile the attempt; otherwise report
`SETUP_BACKENDS_IMPORT_UNCONFIRMED` without another load. Preserve partial
images and evidence for explicit diagnosis. A reconciled record does not
replace the next authoritative Docker check.

A completed predecessor-kit record may accompany a compatible selection change
when its archive digest is unchanged. Validate its schema and pin, require
`RECONCILED`, verify the pinned archive and the same engine, and re-inspect both
exact images before advancing the record to the selected pin. A different
archive, malformed pin, different engine or unresolved cross-kit attempt still
blocks. This is not permission to skip image verification or replay an uncertain
load; the record remains an attempt receipt rather than readiness authority.

Success is `BACKEND_IMAGES_AVAILABLE`, with `demoReady: false`,
`runtimeChanged: false`, `cloudAccessed: false`, `dockerEngineChecked: true`,
`imagesVerified: 2` and a separate `importAttempted` boolean. It means only
that backend images were observed, not that a controller or service is running.
Use bounded fixed progress/error messages, no raw Docker output. Qualify empty
engine, repeat, reopened Setup, corrupted inputs, wrong engine/platform,
interruption/reconciliation and unchanged non-targets; native UI and the next
ordinary Create Controller are independent live gates. Only Setup needs a new
build when the existing pinned kit already supplies the verified archive.

## Explicit Presenter launch increment

After the installed E2E, the separately authorized `launch` action opens the
selected instance through existing Demo Control. Its only request field besides
`action` is the private `state` path. Re-read that instance's selection, require
the installer's independent pin, validate the mounted volume and acquire the
existing shared package/instance leases. Verify the installed application closure
and consumed private Python/UI inputs before executing the fixed installed CLI.
Do not select, repair or upgrade a version as a side effect of opening it.

The fixed HTTP/native ports must both belong to the exact same current-user,
selected-instance `ui serve` command, or both be free. Partial, foreign or
unobservable ownership blocks. Use the existing instance writer around the
check/start boundary; never stop or replace a listener. Start HTTP before native
windows. A launched server owns its own normal runtime leases after the setup
helper exits. On readiness timeout it is preserved for reconciliation, not
killed or relaunched automatically.

For a healthy idle session, submit exactly one existing `workspace-restore`
operation using its current session and a unique request identity. This preserves
the ordinary action interlocks, window ownership, layout and z-order. Poll that
identity, never replay a POST after a lost response. A busy/uncertain session or
changed owner/session blocks without lifecycle actions. Final observation must
establish the owned Presenter surfaces and ordering; absent simulator/control
windows in an empty instance do not mean the Presenter failed, but must not be
reported as full demo readiness. With no simulator source, those expected
absences must not schedule layout recovery; actual Presenter readiness and
ordering failures keep their existing bounded recovery and strict failure rules.
After applying native windows, re-observe the usable display area: registering
an application can change it. A changed area keeps the applied geometry evidence
and requests only the existing bounded workspace recovery. It must not widen
geometry tolerance, replay the launch operation or report stale placement as
confirmed. Final status remains read-only and checks the current display.
The native helper is bounded to two minutes;
timeout preserves any already opened server/windows for observation.

Launch does not start Docker, create/start a VM or CARLA, provision, publish,
reset models, alter connectivity or start driving. Opening the existing Presenter
retains its ordinary read/explicitly accepted recovery behavior; it is not an
offline operation or a promise that its normal Cloud readers make no requests.
The helper itself neither reads credentials nor calls Cloud. A retained run is
permitted only with its unchanged selected version, not through version selection.

The native button is separate from installation, preparation and Cloud access.
It works after reopening setup by selecting the existing private-data folder;
the original source kit is not required again. Success says Presenter opened,
with simulator readiness still owned by Demo Control. OS permission/lock errors
and incomplete geometry get explicit attention states. No automatic retry,
privilege grant or security bypass. Test first/repeat/restarted setup, foreign
ports, changed selection, missing disk, concurrent/busy operations, redaction,
bounded response loss and preservation of the existing live run.

Before invoking the launch helper, the native Open action reads its current
Accessibility trust with `AXIsProcessTrusted()`. If absent, report the exact
Accessibility prerequisite immediately and start no helper/server/restore.
An enabled settings entry for an old ad-hoc preview is not evidence that the
current signed executable is trusted. This is a read-only prerequisite check,
not a grant or automatic system prompt. It does not gate offline installation
or Cloud access, request Full Disk Access/recording, or alter existing owners.
After an operator grants the OS permission, a new explicit Open rechecks it.

<a id="independent-window-metadata--accepted-29-september-2026"></a>
### Independent window metadata — accepted 29 September 2026

Opening/restoring/closing Presenter must not create a vehicle-run journal.
Create Controller remains the vehicle-journal initialization boundary. The
existing WorkspaceService owns an owner-private `state.json` in its existing
`.local/demo-control/workspace` directory, under the existing instance writer.
Its envelope is `schemaVersion: 1`, `kind: democtl.workspace`, and `workspace`.
Only window profile, Presenter command/build, ordering generation, restore time
and placement evidence belong here; no Unit, VM, Cloud or release state.

Read legacy journal workspace metadata only when the separate record is absent;
never migrate, overwrite or repair that journal through a window operation.
Malformed/unsafe/oversized/newer records and interrupted `.pending` writes block
instead of falling back. Require a canonical, owner-private, single-link regular
file and atomic replacement. Existing vehicle-journal validation stays strict.
The simulator-start consumer reads this same window profile. Layout failure
reports incomplete workspace without relabelling a successful simulator start.

Qualify empty-instance first Open, idempotent repeat, Setup restart and continued
configuration/status reads without any vehicle journal. Preserve legacy journal
bytes and current Test identity; prove invalid journals still fail and changed
vehicle run IDs never restore stale windows. Native positive results do not
qualify controller creation, Cloud enrollment or full E2E by themselves.

## Bootstrap and request boundary

The installer carries its own private Python, trusted helper sources and a
release pin reviewed independently of the chosen kit. Installation never executes
unverified kit code; explicit launch uses the verified selected CLI above.
The builder authenticates the bootstrap Python files against the
pinned kit inventory before and after copying. Local ad-hoc signing is only an
engineering check, not Developer ID/notarization or redistribution approval.

### Local signing and permission continuity

The local builder requires an explicit signing mode before copying or compiling.
Normal development uses an exact valid Apple Development identity from the
operator's Keychain, never a name-prefix match or automatically selected key.
Missing, expired, wrong-type or failed signing blocks; no ad-hoc fallback.
An explicit `--ad-hoc` remains an engineering-only exception and cannot qualify
permission continuity. Actual private-key use requires operator authorization;
no key export, account enrollment or trust-store change is part of building.

Keep the Setup bundle identifier constant. Use Apple's generated designated
requirement, not a permissive custom requirement. Verify the resulting signature,
identifier, development authority, TeamIdentifier and absence of a build-specific
`cdhash` requirement. Record non-secret requirement digest and signing mode in the
build receipt. Local signing has no network timestamp request, additional
entitlements or notarization claim; Developer ID distribution remains a gate.

Stable signing is necessary for this continuity fix but is not proof of TCC
permission reuse. Qualify one ordinary removable-volume consent, same-build
repeat, Setup quit/reopen, a changed signed build and SSD reconnect separately.
Do not reset TCC, request Full Disk Access, disable Gatekeeper or promise that all
other permission categories/apps share this one consent. The first transition
from an ad-hoc preview to the stable signer can legitimately require consent.

### Direct distribution signing — accepted 29 September 2026

The [accepted channel](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)
is Developer ID Application and Apple notarization, not TestFlight. Preserve
the explicit Apple Development/ad-hoc engineering modes. Distribution requires
its own explicit exact-identity argument, rejects a development/other identity
before copying or compiling, and never falls back to a weaker signature.

For the Setup bundle, sign the verified embedded Python native files first,
then the outer app, without `--deep` signing or extra entitlements. Distribution
requires hardened runtime, a secure timestamp and post-signature inspection of
every nested native file and the outer app for the expected authority and same
team. An explicit development hardening proof uses the existing development
identity with no timestamp network request and is still not distribution.
Ad-hoc signing cannot satisfy this hardening proof.

Keep the unchanged bundle identifier and Apple's designated requirement. No
custom permissive requirement, key export, TCC reset or Gatekeeper change.
The build receipt distinguishes local preview from distribution-signed but
unnotarized output. The builder does not submit to Apple, mark notarization as
passed or authorize redistribution. The separately supplied runtime kit needs
its own executable-closure signing and renewed integrity pins; a signed Setup
does not qualify that kit. Actual Developer ID and notarization remain live
gates even when the development hardening proof and isolated tests pass.

The native window invokes a fixed embedded executable and helper without a
shell, with an isolated Python interpreter and a minimal environment. One
bounded JSON request on stdin selects `preflight`, `install` or `prepare`.
Unknown keys/actions, relative/linked paths, overlapping source/store/state,
unsupported platform, missing parents and foreign state directories fail closed.
The original installation actions contain no credentials or arbitrary commands.
The separate enrollment submission accepts its one-time token only in bounded
stdin; it is never included in arguments, environment, progress or diagnostics.
Output
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

Fresh private-instance preparation creates the shared `.local/demo-control`
parent with owner-only directory permissions before any window or Cloud action.
Opening Presenter before Cloud setup must not make later enrollment fail because
of default intermediate-directory modes. This creates no credential or vehicle
journal; existing unsafe directories are not silently adopted or repaired, and
enrollment's strict ownership/mode checks remain unchanged.

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
unchanged live owners. These original slice tests do not close every later gate.
Complete DMG and
installed scripted M1 evidence now exist; full native UI, moving SOTA, secure
native token entry and target-host interruption/repair remain open. Retained-run
updates, public distribution/notarization and broader acceptance are not implied.
