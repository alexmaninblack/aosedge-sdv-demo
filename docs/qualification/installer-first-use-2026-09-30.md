<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installer First Use Qualification 30 September 2026

- Status: Recorded first-use results retained; three remaining same-Mac checks user-deferred for clean-system qualification
- Version: 1.1
- Prepared: 2026-09-30
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0` plus preserved working changes
- Plan: [Accepted execution route](../planning/active/installable-distribution-and-reproducibility.md)
- Prior evidence: [Installed serial E2E](installed-serial-e2e-2026-09-29.md)

This continuation closes concrete installer defects without changing the plan
or rebuilding Factory, CARLA or services. Initial checks preserved the retained
Test; the later authorized replacement is recorded separately below. Evidence
below distinguishes an installed native result from fixture tests and from the
still-required clean-system and distribution qualification.

## Current conclusion

Kit 020 completed real fresh-RSA signing/publication, installed VDP/Brake/Tire
function, independent Reset, Return to road, external-network interruption,
queued delivery, full controller poweroff/on, post-cycle maneuvers and ordinary
Finish. Its Test was retired and all owned demo runtime was closed. The dated
sections below retain earlier failed/interrupted checkpoints as evidence, not
as current pending publication approvals.

Kit 021 / Setup 031 consolidates the single proved preprovisioning `vm.py`
correction. Native installation, separate empty-instance selection, first/repeat
Presenter launch and 77 installed-code VM/trust regressions passed. Blocks A/B are
not fully closed: native console-entry ambiguity, shared-Docker retained-handle
selection and automatic incomplete-start cleanup still lack their specific
acceptance evidence. The user subsequently deferred these three checks on
30 September and authorized moving to clean-system qualification; see the
[accepted deferral](../planning/active/installable-distribution-and-reproducibility.md#accepted-deferral-and-move-to-clean-system-on-30-september-2026).
They are no longer prerequisites to that next test block, not passed checks.
Ordinary first-use access and Create Controller must still succeed on the clean
system. Clean native macOS and distribution signing/notarization remain release
gates. VDP-TIMEOUT-01 stays explicitly deferred.

## Presenter display change

The cold failure was reproduced on Setup 027 with no second launch. Before
native application registration the usable display height was 1220 points;
after registration it was 1225. The placement record at 08:49:20 UTC correctly
recorded its applied 1220-point geometry, attempt zero and verified z-order.
The later reader compared that geometry with the changed display, producing
the false-looking final attention state. Application registration changing the
usable frame is demonstrated; the Dock alone is not established as its cause.

An in-memory source substitution proved that a post-apply display observation
can request the existing bounded recovery and settle on attempt one. Source
now does that without widening geometry tolerance, changing the layout,
replaying the launch POST or making final status mutating. Repeated changes
remain bounded and failed screen observation is not success.

Kit 018 contains only this `workspace.py` change relative to Kit 017. Its full
17,685-file verification passed in 118.21 seconds, with all large components
unchanged. Manifest SHA-256:
`7cf7eb39a94e4e5f092162867d894ef815b8bcc8ed9dc33c8803c7b051baee75`.
Setup 028 and its read-only DMG passed native protocol, bootstrap and strict/deep
signature checks using the authorized stable Apple Development identity.

The normal native Install and Prepare actions selected Kit 018 at revision 3
for the separate empty instance. First Open reported **Presenter opened**.
The subsequent read-only observation showed all three Presenter surfaces at
exact current geometry, a 1225-point display and verified z-order. Missing
simulator/control surfaces remained honestly incomplete, not demo-ready.
Repeated Open retained the same server and window owners. Setup quit/reopen
with only the private-data folder selected passed, as did another Open after
normal workspace/server shutdown. No vehicle journal was created. Both runtime
owners and Setup were closed and the DMG detached after these checks.

## Native VM access entry

On the empty instance, the installed `access setup` path displayed the real
native password dialog. The operator entered the password; no engineering
Keychain seed was performed. The operation completed without a VM or Cloud
action. A non-secret existence check confirmed the exact per-instance Keychain
entry; a second access setup completed without another prompt. This proves
actual entry and reuse, not a fresh Create Controller integration, cancellation
on a clean Mac or permission inheritance between private instances. The password
was not printed, written into evidence or copied between instances.

## First Open before enrollment

An actual enrollment-status check failed before token generation or certificate
issuance. The private worker correctly rejected `CLOUD_ENROLLMENT_DIRECTORY_UNSAFE`.
Presenter had created the shared `.local/demo-control` parent as mode 0755:
Python's recursive directory creation applies its requested mode only to the
last path component. The enclosing instance was private, but enrollment still
requires every owned directory to satisfy its stricter private-mode contract.

A transient proof reproduced old failure and corrected success with umask 022,
the ordinary workspace build/save sequence and read-only enrollment status.
Fresh instance preparation now creates that shared parent as 0700 before any
consumer uses it. It creates no key, credential or vehicle journal. Existing
unsafe directories are preserved and rejected rather than silently repaired;
the already-used diagnostic instance was not chmod-repaired to claim acceptance.

The focused runtime-path/workspace/enrollment suite passed 53 tests. The first
full suite exposed five TLS fixture assumptions that the shared parent did not
yet exist. Those fixtures now use the private parent, while the hostile-link
test explicitly replaces only its empty temporary fixture parent. All 16 TLS
cases plus both written-overlay tests passed (18 total, 13.667 seconds). The
final full regression passed 1,339 cases in 226.351 seconds, with the same two
written-overlay cases skipped in that broad runner and passed explicitly in
the 18-case invocation above. The final-pin distribution suite passed 268 cases
without skips in 10.301 seconds. Fixture adjustments did not require another
runtime rebuild. Native qualification remains separate from those tests.

Kit 019 changes only `runtime_paths.py` relative to Kit 018. Verification passed
for 17,685 files / 35,114,395,227 logical bytes in 118.71 seconds. Manifest:
`caae9f8da91a38b15879d9459fc60da1e01e88f5ecab77f5c91afef62682bac0`.
Setup 029 binary SHA-256:
`f1e68cea5269dcbc0470c8094e793998004f5373370e51a03e384c9f072523af`.
The designated requirement remains unchanged; no new entitlements or permission
reset was introduced. Read-only DMG SHA-256:
`3faadb28fea6b915cbc4858963c3f95484741f0a4599beef3ff89457480b7509`.
Image verification and mounted strict/deep signature validation passed. This is
an engineering development signature, not Developer ID/notarization.

## Existing account enrollment route

A new email, user or invitation is not required for an existing OEM/SP account.
Official [existing-user instructions](https://docs.aosedge.tech/docs/how-to/tutorials/user-and-certificates/issue-new-user-certificate)
describe generating a new token from the user's profile. The current staging
OpenAPI and frontend expose `POST users/new-token/` for the authenticated current
user, followed by the existing CSR `POST user-certificates/` endpoint. Lost
certificate email recovery is a different workflow.

Authenticated preflight used the existing certificate-derived staging endpoint
and packaged trust. Both current accounts had token-generation permission, no
current token and one certificate record. No raw user response, email, token,
key or certificate was emitted. The initial qualification attempts stopped at
the local status failure above, before a token-generation intent or Cloud write.
The subsequent real issuance passed for both existing accounts.

The issuance check uses a durable non-secret token-dispatch intent, no blind
retry, and the unmodified signed Setup adapter over private stdin. It must
confirm that old certificates still authenticate and remain unchanged, that
new certificates have the same user/role/owner/permissions, and that restart,
local recovery and repeated completion create no additional certificate.
API acquisition does not by itself qualify manual secure-field interaction.

At 09:34:27 UTC the OEM check completed, followed by SP at 09:34:37 UTC. Each
account went from one active certificate to two. Original certificate records,
validity and revocation state were unchanged, their local files were unchanged,
and they still authenticated after issuance. Each new private certificate
authenticated as the same user, role and owner with the same permission set.
No user, invitation, association, Unit or service was created or changed.

The official current-user API supplied each token in memory. The signed Setup
029 helper, not a replacement transport or SDK CLI, submitted the CSR through
its ordinary bounded stdin/worker path. Private output belongs only to the new
instance's per-role enrollment directory. Three separate helper invocations
then checked status, recovered the completed local result, and submitted the
already-completed operation with a synthetic sentinel token. All reused the
same attempt without network access; authoritative inventories still contained
exactly the same two certificates. There was no blind retry or secret in
arguments, environment, output, report or Git. The native secure text field was
not used to enter the real tokens; that distinction remains explicit.

## Fresh Kit 019 native sequence

The normal Install action completed with a committed, non-reused receipt for
all 17,685 files. Prepare created a genuinely fresh private instance and selected
Kit 019 at revision one. Observed completion bounds were 370 seconds from Install
and 132 seconds from Prepare, including polling intervals; these are not precise
performance benchmarks. Neither action copied credentials or vehicle state.

Native Open preceded Cloud setup, reproducing the formerly failing order. It
reported Presenter opened within a 33-second observation bound. Independent
status confirmed exact 1225-point display geometry and verified z-order, while
correctly retaining the expected missing simulator/control findings. The shared
parent was 0700 without manual repair. A concurrent status attempt during the
Cloud writer's ownership correctly reported busy and made no changes; the
later idle read succeeded.

Before enrollment, the installed read-only isolation check passed with developer
tree and Homebrew reads denied, network denied, and immutable package writes
denied. It selected its private Python/QEMU/Factory .39 inputs, had no credentials
or vehicle journal, and neither imported nor modified the retained Test. The
retained-run selection guard still rejected an attempted version switch.

The native enrollment window subsequently displayed both real saved attempts
and filled their private file references back into the certificate-pair window.
Its token field remained empty. Native local inspection, explicit pair save and
GET-only Cloud check passed for OEM/SP identities, their association, fleet,
architecture, Factory, Node type and both delivery permission sets. The existing
occupied Test set correctly reported Conflict, not an authentication failure or
false demo readiness. No adoption, deletion or provisioning followed the check.

An authoritative read confirmed the retained Unit
`f26ecc96-6acd-461a-a4ad-1a1f55925165` still provisioned and Offline with the same
Node and system identity. Finishing/replacing that exact Test was requested as
one explicit destructive boundary for the remaining ordinary first-Create and
installed runtime checks. The user subsequently authorized the whole ongoing
staging test cycle, including retirement of previous owned Tests, replacement
creation and test signing/publication. The earlier approval wait is resolved;
occupancy and version-selection guards remain intact. The immediate continuation
reuses published VDP 123/V3, Brake 99/V3 and Tire 51/V1; already-qualified serial
transitions need not be repeated for these host-only changes.

## Repeat, restart and session shutdown

After saving the new certificate pair, another native Open reused the existing
Presenter server and native window process. Setup was then quit and reopened
from the same verified DMG. Selecting only the existing private-data folder,
without reselecting the kit or package store, successfully opened the Presenter
again. It correctly retained the incomplete simulator/controller finding; this
does not claim that cold CARLA or first Create Controller was exercised.

At 09:47 UTC, the normal workspace close completed with no lifecycle change,
followed by the installed UI stop. Independent process and listener checks found
no remaining Setup, Presenter, CARLA or QEMU owners from the check and no
listeners on 18080 or 18600. The Setup 029 DMG was detached normally. External
work volumes remain mounted; no unrelated application or container was stopped.
The retained Test installation record and run journal still matched their
pre-check hashes. New enrollment files and qualification evidence were preserved.

## Preservation and remaining acceptance

### Authorized prior Test retirement

The user's standing staging authorization closed the approval wait. Preflight
confirmed the exact old Unit provisioned/Offline, Test VM stopped, source stopped
and no Production role in this private instance. Normal installed Finish then
confirmed Unit/Node absence and removed exact Brake/Tire data and owned Docker
resources. It stopped at local cleanup because a prior failed CARLA start had
only `input.json` and `simulator.log`, without a terminal manifest. A read-only
probe localized the underlying `FileNotFoundError`; no Cloud deletion was replayed.

The two-file fragment (16,231 bytes) was preserved in private ignored engineering
evidence after proving stopped owners, no open handles, single-link private
files, and byte-identical input to the completed run. The move changed neither
the journal nor product cleanup guards. This is an engineering recovery of an
old incomplete start, not qualification of automatic interrupted-start cleanup.
That remaining product limitation must not be hidden by this recovery.

Normal Finish resumed only the remaining local step with fresh absence checks
and completed. Old working overlay, local Factory copy and run journal are
absent; the original immutable Factory, configuration, credentials and published
release ledger remain. A repeated Finish returned `NO_CURRENT_TEST` with no-op
completion. No owned backend containers remain; unrelated Docker containers
were unchanged. Internal free space after cleanup was approximately 162 GiB.

### New instance after retirement

The native Kit 019 Cloud check then confirmed every prerequisite, including
the now-empty Test verification set. Through the ordinary native reference UI,
the exact eligible Brake Subject `78d05c9c-cdf6-45cc-ab28-df2a4d3ac0d7` and Tire
Subject `ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb` were individually inspected and
saved after fresh recipient/owner checks. No Cloud binding changed. Native Open
again verified Presenter windows and correctly reported that the simulator and
controller were not yet ready.

The browser automation tool subsequently rejected access to the local Presenter
URL. No alternative browser, direct action request or CLI Create was used to
circumvent that tool denial. Manual operator input was requested for Create
Controller; no successful creation is claimed on the basis of opening Presenter.
This is a tooling block, not an ungranted staging mutation permission.

No manual Create was observed before session closure. At 10:05 UTC the normal
workspace close and UI stop completed; independent checks found no owned runtime
processes or listeners and no vehicle journal in the new instance. Setup was
quit and its DMG detached. The selected installation, new certificates and both
explicit Subject references remain intact for the next ordinary launch.

Before the replacement continuation, the retained Kit 015 Test, Cloud Unit,
VM, histories, models and release ledger were unchanged. The new standing
staging authorization permits retirement through the normal Finish lifecycle,
not adoption of occupied Subjects or switching around its retained journal.
Published releases and their ledger remain protected.
`VDP-TIMEOUT-01` remains deferred. Internal free space was about 155 GiB and the
Work volume about 482 GiB; no warm cache or previous evidence was deleted.

## Browser recovery and ordinary first Create

The apparent HTTP policy denial was localized to a retained browser error
document. Desktop logs record connection refusal and a generated `data:` error
page at 05:03:52 UTC; the browser tab inventory still exposed that document
despite the displayed loopback address. A later navigation while Presenter was
stopped failed similarly. No evidence established a policy prohibition on the
Presenter HTTP origin. No browser permission, protocol rule or security control
was changed.

The normal native Setup 029 Open path restarted the selected Kit 019 Presenter.
Both loopback listeners were present and its three native surfaces had exact
geometry and verified z-order. The operator manually refreshed the error tab;
the regular browser tool then read the actual Presenter successfully. Pointer
actions were unreliable in this browser session, while ordinary keyboard
activation opened Session and the Create confirmation. No direct operation
request or alternate transport substituted for the UI.

The first ordinary Create Controller completed in 111 seconds, with journal
start at 10:32:46.142520 UTC and lifecycle completion at 10:34:37.637793 UTC.
It booted Test VM `fa8511d0-8ff2-4e7f-bb56-847d7304b235` from Factory .39 and
started the owned Brake/Tire backends. The previously entered per-instance
VM access was reused without a new password prompt or engineering credential
seeding. The journal contains only Test, selected staging, and no Cloud Unit
or Node yet. This closes the ordinary first-Create integration check, not
provisioning, cold simulator or complete installed acceptance.

At 10:35:23 UTC the ordinary Start simulator confirmation initiated one
packaged CARLA launch. The UI reported input verification and then the bounded
map-readiness wait; no Editor/build or second launch was requested. It completed
at 10:38:53 UTC (209 seconds reported by UI), after about 63 seconds verifying
inputs and then map loading. One CARLA process was observed throughout. Read-only
workspace status reported exact CARLA/Driving Control/Presenter geometry, no
geometry problems and verified z-order. Native Driving Control showed live
simulation, stationary Safe Stop and no assigned vehicle, as expected before
provisioning. This closes the cold-start check, not installed service function.
During Create, a window-layout warning appeared while
simulator/control surfaces were still absent; retain this UI observation for
classification rather than treating it as a failed Create.

## New-certificate package-signing compatibility

The fresh UI has no ordinary path to select historical publications without
local preparation records. Instead of importing the previous run, Prepare V3
allocated VDP `124.0.0`. Ordinary Sign & publish stopped locally in three seconds
with `COMPONENT_ADAPTER_FAILED_InvalidKeyError`. Only the completed prepare record
and unsigned files exist; no sign or upload intent/receipt exists. The fixed
operation plan stops on failed signing before its upload step. No publication
retry, Unit provisioning or service assignment was performed.

Both freshly enrolled credentials contain EC P-256 keys. The pinned SDK's
`generate_pair()` defaults to EC, but its official package signer hardcodes
RS256, as does demo package verification. Thus successful Cloud authentication
did not establish signing compatibility. VDP, Brake and Tire share this issue.
An offline proof with synthetic credentials and network connections forbidden
reproduced `InvalidKeyError` with EC and verified RS256 with explicit SDK RSA.

The minimal source correction explicitly requests SDK RSA-2048 for new
enrollments. Local certificate-pair inspection and signing-context validation
now reject non-RSA keys before save/readiness or packing, with a specific native
explanation. No SDK, Cloud endpoint, trust anchor, accepted signature algorithm,
permission or existing private key is changed. Completed EC attempts remain
readable/replayable without issuance; they are not labeled signing-qualified.

The initial focused suite passed 48 cases, including real official signing for
both enrolled roles, RSA VDP/Brake/Tire packaging and preservation of legacy EC
attempts. Final expanded regression and immutable successor qualification are
recorded below when complete. A full run under the restricted command sandbox
was not a pass: 39 cases could not inspect processes or bind local fixture
sockets. Those gates require the ordinary local test permissions, not weaker
product checks; the corrected invocation is separate evidence.

At this checkpoint fresh RSA enrollment and installed signing still required
qualification. Enrollment is now closed by the following receipt. Overall
closure still needs installed signing, full-power-cycle evidence;
new-candidate Finish and interrupted-start cleanup; clean native macOS;
whole-runtime distribution signing and
notarization; and redistribution/corresponding-source closure. Previously passed
eligible exact-Subject selection and serial functional tests are not reopened.

## Corrected enrollment and native installation

The final broad regression passed 1,343 cases in 219.199 seconds. Its two
duplicated written-overlay cases were skipped in that runner; the actual
`qemu-io` modified-overlay case then passed explicitly. The final-pin
distribution suite passed all 268 cases with the installed process guard
enabled and no skips. The restricted-sandbox failure above was not reported
as a product pass or worked around by weakening a check.

Kit 020 changes only `cloud_enrollment.py`, `cloud_connection.py` and
`component_worker.py` relative to Kit 019. All 17,685 files and 35,114,395,873
logical bytes passed verification in 114.8 seconds. Manifest SHA-256:
`83f5c9101a1bc955f18aa970865b5a8cde6ed8614ad191d95fbb38df30a2fbc9`.
Factory, CARLA, services and the native runtime remain byte-identical.
Setup 030 adds the specific RSA requirement explanation. Native protocol,
embedded bootstrap and strict/deep signature verification passed. Binary:
`665314456db31c518b04da1a3efccc79d90d599eb8a862632896278492b73280`.
Read-only DMG:
`e6e9279447699350c3ac532c16afa5e6b8a10d220088acc658bdd24b9c37ba23`.
The designated requirement is unchanged; this remains Apple Development
signing, not Developer ID or notarization.

Ordinary native Install and Prepare completed for a separate empty instance.
At 11:18 UTC the signed Setup helper issued one RSA certificate for each
existing staging account through the current-user token API. Each account's
certificate inventory changed from two to three, preserving its original and
Kit 019 EC certificates. The new certificates authenticated as the same users,
owners, roles and permission sets. No email, invitation, registration, Unit or
vehicle journal was created. Tokens travelled only through bounded private
stdin; this live API/helper proof does not claim manual secure-field entry.
Status, local recovery and completed-attempt replay reused each receipt without
Cloud access or another issuance, confirmed by unchanged inventories.

The actual native pair window rejected the old EC pair before saving it, with
`CLOUD_PACKAGE_SIGNING_RSA_KEY_REQUIRED` and a clear explanation. Selecting
the newly issued RSA pair passed local inspection, explicit reference save
and the read-only staging prerequisite check, including both delivery roles.
No key was copied or automatically replaced.

The stopped, never-provisioned Test
`fa8511d0-8ff2-4e7f-bb56-847d7304b235` was then retired through normal installed
Finish under the standing authorization. At 11:20:27 UTC cleanup completed
without a Cloud mutation. Its working VM, temporary Factory copy and terminal
source files were removed; immutable Factory, credentials, VDP 124 artifacts
and release continuity remain. This terminal-run cleanup passed without the
historical interrupted-start fragment exception. Selection of Kit 020 for this
now-retired instance remained blocked by `INSTALLED_NATIVE_CONSUMER_ACTIVE`.
Read-only open-file inspection identified Docker's virtualization process still
holding five empty old backend/context directories. No old demo process was
running. The guard was not weakened and no journal was erased. Restarting the
shared Docker engine would affect five unrelated Watt containers, so that
recovery was not performed; post-Finish version selection is not a pass.

The already prepared separate Kit 020 instance instead completed its ordinary
native Open, with Presenter windows verified and an honest incomplete
simulator/controller state. The original browser tab reloaded successfully and
showed no controller, no Cloud Unit and empty software slots. Its private state
and RSA credentials were created by this installer, not copied from the old run.

The installed official signer also signed an offline fixture using each actual
new OEM/SP certificate; both RS256 signatures verified against their certificate
public keys. Network connections were forbidden, credential file identities
remained unchanged and temporary signature files were removed. This proves
real-key compatibility, not an actual component upload or Unit installation.

The native exact-reference workflow saved both still-unbound Brake/Tire Subjects
for the fresh instance after new inventory checks. Ordinary UI Create then
started Test `b1eaeeb9-f7d5-4890-bfca-baaf19e6473f` from unchanged Factory .39.
It displayed the native VM access wait, but ended PARTIAL after 96 seconds at
`start-test` with `GUEST_CONSOLE_AUTHENTICATION_FAILED`. No provisioning or
publication started. This error identifies the serial authentication boundary;
it does not by itself establish a mistyped password versus a console-prompt
handling problem. The UI tool did not expose the system dialog, and the
operator was asked whether they had entered it. A metadata-only Keychain check
found no saved VM password for this new instance. No password was printed,
copied from another instance or supplied through an engineering substitute.

No blind Create retry followed. Normal VM stop completed in 1.04 seconds,
preserving the overlay and partial lifecycle receipt for diagnosis. Installed
publication/function and full power-cycle remain unqualified on Kit 020;
the successful real RSA proof does not close those gates. The VDP timeout
exception remains deferred.

At 11:37 UTC, normal workspace close and idle UI stop completed. Independent
process/listener checks found no Setup, Presenter, CARLA, Driving Control,
QEMU or installed Python owners and no listeners on 18080/18600. Docker retained
only the five unrelated Watt containers. Setup was quit; the current Test disk,
RSA/EC credentials, selected kit and compact evidence remain available. This
is a stopped diagnostic handoff, not Finish of the new Test or completed A/B.

## Console access diagnosis and retained run continuation

The operator subsequently confirmed manual password entry during the failed
Create. That confirmation does not identify the value received by the guest.
The original error and available bounded authentication-journal observations
do not distinguish rejected input from a console-prompt handling fault. The
cause remains unconfirmed; no claim of operator error or corrected parser is
made.

One diagnostic start reused the exact stopped Test and unchanged Kit 020.
The ordinary installed interactive CLI received the previously user-supplied
factory password through its hidden prompt. A temporary observer emitted only
fixed serial event categories and elapsed times, never console payloads or
credentials. It observed one login prompt, one password prompt and a shell
3.112 seconds after password submission. SSH key installation and host-key
pinning completed, followed by authenticated guest and DNS readiness. The
VM operation completed in 46.96 seconds, preserving its UUID and disk. No
credential was saved to Keychain, no Cloud action occurred and no installed
code or Factory bytes were changed. This is diagnostic recovery, not a fresh
native password-entry acceptance result.

All 13 existing guest-access protocol tests and three native-access tests passed,
including refusal to retry a rejected password and no hidden terminal fallback
after native cancellation. The original failure was not reproduced by the live
diagnostic start; this does not establish that intermittent failures are fixed.

Setup 030 then opened the same installed instance normally. Before continuing
the partial Create, an independent journal read confirmed the exact original
Test, running VM, completed SSH setup, no Cloud Unit and no unresolved VM
operation. The installed lifecycle implementation resumes existing readiness
and backend steps instead of allocating another VM. The UI continuation
completed and advanced to Start simulator.

The single packaged simulator start completed at 12:09:29 UTC, approximately
209 seconds after dispatch. The native Session panel subsequently reported
verified window geometry and z-order. Before simulation was started, its absent
windows were correctly reported as incomplete; that earlier observation is not
a failed final layout. No Editor, build, duplicate CARLA or VM owner was used.

Ordinary UI Prepare produced VDP 124/V3, Brake 100/V3 and Tire 52/V1 in this
instance. VDP's deterministic unsigned digest is
`42bc590a6a015d3ec763f53c01b58ebc1d28fb7def483fe9612a02cbed0e1e0b`.
It matches the preserved Kit 019 unsigned candidate because payload inputs are
unchanged; no old run, artifact directory, credential or receipt was copied.
The defect addressed by Kit 020 is signing-key compatibility, not VDP payload
content. The old failed sign attempt never uploaded that release.

The UI tool's action-time safety review refused the Sign and publish action
before execution and required exact-payload confirmation despite the standing
staging authorization. The action was not retried through another interface.
One consolidated request named these three releases, the selected newly
enrolled RSA identities, the staging domain and current Test. The operator
subsequently reaffirmed authorization for this exact ongoing staging cycle.
No additional routine confirmation is outstanding. At this earlier checkpoint,
the journal contained only VDP's completed prepare record, no sign/upload
intent or receipt, and no service publication operation.

At 12:15:01 UTC the normal engineering `environment park` operation completed
Safe Stop, simulator/control shutdown, VM poweroff and backend stop. This is
resource-preserving test-session cleanup, not a supported Demo Studio pause
feature or a passed post-installation ignition test. The same Test, SSH pin,
RSA credentials, selected package, release reservations and unsigned candidates
remain. Continue with its existing guarded engineering resume after exact
publication authorization; do not recreate the Test or erase the journal.

Workspace close and idle UI stop then completed; Setup exited and its DMG was
detached. Independent process/listener observations found no owned CARLA,
Driving Control, Presenter, QEMU, Setup or installed Python process, and no
listeners on 10022, 18080 or 18600. Only the five unrelated Watt containers
remained running. No source implementation, Factory or installed-kit change,
commit, push, provisioning or Cloud publication occurred in that continuation.

## Preprovisioning resume correction

The next guarded engineering resume failed at 12:56:50 UTC with
`SOURCE_TRUST_BOOTSTRAP_BINDING_UNCONFIRMED`. The existing VM was running,
but guest readiness had not been attempted. The retained journal had no
Unit/Node, no Cloud identity and no assignment; it contained only the local
dashboard trust created by Start simulator. VM start incorrectly treated any
enabled source trust as completed Unit onboarding and required a Cloud binding.
This contradicts the accepted local-first Gateway initialization sequence.

A process-local proof reproduced the old refusal, then allowed only the exact
dashboard-only, detached, never-onboarded state to use ordinary guest readiness.
First start, repeat and stop/start passed, while 13 partial or contradictory
binding cases still refused before guest access. The existing bound-Test
restore and Production-isolation test also passed. A single live execution on
the same VM completed VM readiness, backend start and simulation start at
13:05:51 UTC. No certificate, identity, immutable package or Factory was
replaced; the same working overlay was preserved and continued normal runtime
writes. The temporary method replacement ended with that process.

The minimal correction is now in `vm.py`, with regression coverage for the
normal lifecycle and 16 rejected partial/contradictory cases. It remains a
source correction, not a deployed Kit 020 fix. The initial broader test command
used a Python environment without the crypto test dependency and lacked local
socket permission. Those are test-harness failures, not product failures;
the corrected environment passed 76 cases, and the single remaining crypto
case passed with the already packaged Cloud crypto dependency. All 77 cases
therefore passed; no tests were skipped or product checks weakened.

After the completed resume reached Presenter, its ordinary controls became
available. The action-time UI review accepted the user's renewed staging
authorization. VDP 124 signed successfully with the newly enrolled OEM RSA
credential and received HTTP 201 (`uploaded`) from staging. Upload started at
13:07:24 UTC; the signed bundle digest is
`220b7506df907bf137a74b234606655fb740cd112160043e355646be0debc6ed`.
The publication preflight observed no recipient Units. Ordinary UI Provision
then registered this Test, reached Online and attached the unchanged simulator
in stationary Manual. The UI correctly showed 124 pending over Factory 0.0.0;
native Safe Stop was explicitly requested before installation.

## Installed signing and functional sequence

The same Test received VDP 124/V3, Brake 100/V3 and Tire 52/V1 using its new
RSA credentials and ordinary Presenter controls. VDP installation was observed
at 13:10:33 UTC after native Safe Stop. Brake publication completed at 13:11:21,
assignment at 13:12:27 and active installation was observed at 13:12:51. Tire
publication completed at 13:14:39, assignment at 13:15:55 and active installation
was observed at 13:17:31. These observation bounds include polling time, not
only execution latency. No Production recipient was assigned.

The native Brake maneuver produced a backend assessment at 13:13:44 UTC and
local Monitoring. The native Tire maneuver produced a Tire assessment at
13:18:02 and local Inspection recommended; its braking also produced a second
Brake assessment. Presenter, backend receipts and actual native advisory were
checked separately. Installed versions and profiles matched Cloud with no
pending component or service error. The prior serial V1/V2/V3 matrix remains
valid for unchanged payloads; this run qualifies actual fresh-RSA signing and
delivery rather than claiming another complete serial matrix.

Brake Reset completed at 13:18:59 with a matching Gateway CLEAR. Brake changed
to Monitoring while Tire retained Inspection recommended. Tire Reset at
13:19:47 reached Gateway CLEAR at 13:19:51 without changing Brake. Both backend
assessment histories remained intact. Return to road finished stationary in
Manual with the same actor and preserved model state; it did not start Autopilot.

## External network interruption and queued delivery

With external network OFF, the settled 13:21:53 snapshot and the 13:23:40
snapshot had identical backend message IDs and receipt times. New native Brake
and Tire maneuvers nevertheless produced local assessments and Inspection
recommended. The VM contained five queued Brake and ten queued Tire messages.
Presenter eventually labeled backend input Last known rather than current;
the initial freshness grace period was observed separately.

External network ON was observed at 13:24:15.704916 UTC. The offline Brake
assessments arrived 7.042 and 7.154 seconds later, and Tire arrived after
21.474 seconds. By 13:24:58 both queues were empty. Each of the 15 captured
messages occurred exactly once in the bounded backend inventories. The same
guest boot and manager PIDs persisted, with every checked manager active,
successful and NRestarts zero. The receipt comparison passed 37 assertions.
No VDP timeout was observed in these bounded windows; VDP-TIMEOUT-01 remains
deferred and is not declared fixed.

## Full controller power cycle

Authenticated guest poweroff began at 13:26:15 UTC in physical Safe Stop with
empty queues and external network ON. QEMU absence was independently verified.
Presenter showed Controller switched off, Last known backend input and disabled
Reset controls. This was a full stopped-process interval, not only guest reboot.

The unchanged installed VM start began at 13:30:54 and completed at 13:31:32
(37.3 seconds). Automatic Presenter recovery completed at 13:31:48 in
READY_SAFE_STOP. No selection, provisioning, manual reconnect or Autopilot
action was used. Unit, Node, source run, assignment generation and CARLA actor
were unchanged; the guest boot ID changed. Cloud subsequently reported the
same active releases. Storage inodes, service UIDs, directory ownership,
assessment history and model event counts survived. Seventeen preservation
assertions passed with zero manager restarts and SELinux Enforcing.

Local advisory was temporarily Not available/Unavailable during startup and
input revalidation, not immediately operational when the VM start returned.
Tire readiness reached READY at 13:32:24; Brake reached OPERATIONAL at
13:32:26. Both native advisories then showed the retained Inspection recommended
without intervention. This is approximately 36–38 seconds after route recovery,
not evidence of zero-latency restoration. During early boot, the story footer
briefly used retained Software story complete before reporting Service runtime
not confirmed; preserve that presentation observation for follow-up, not as a
claim of current service readiness. Known sshd directory-search and early getty
checkpoint_restore denials were recorded; no all-domain clean-AVC claim is made.

New native maneuvers after ignition produced two further Brake assessments
and one Tire assessment. By 13:35:05 both services were active, all checked
managers still had zero restarts, VISS acceptance/forwarding counters advanced,
and both outboxes were empty. This closes the full-power-cycle preservation
and post-cycle functional checks for this installed Test, with the startup
latency described above.

## Normal Finish and process shutdown

The exact-ownership staging preflight confirmed Test Unit
`9f56845a-4a1e-4cfb-aa75-aebaa13ee41f`, its matching VM/system identity,
stationary Safe Stop and no Production role in this instance. Ordinary UI
Finish started around 13:37 UTC and returned Demo finished by 13:38:18.
There was no engineering cleanup, interrupted-fragment workaround or replay.
Authoritative post-read confirmed Unit absence; the working overlay and run
journal were absent. Private credential file identities, sizes, modification
times and modes remained unchanged. The independent release ledger still
held VDP 124, Brake 100 and Tire 52; the immutable Factory and kit remained.
Removed working run data has no normal recovery flow; retained compact test
receipts do not constitute a model/history backup.

The normal workspace close and idle Presenter stop completed. Independent
process and listener checks found no owned Setup, Presenter, Driving Control,
CARLA or QEMU process, and no listeners on 18080, 18600 or 10022. Setup 030
was quit and its DMG detached. Docker retained only the five unrelated Watt
containers. Internal free space was about 156 GiB; the Work volume had 482 GiB.

## Consolidated host correction candidate

Kit 021 incorporates only the proved `vm.py` preprovisioning correction.
All 17,685 files / 35,114,396,835 logical bytes passed verification in 110.68
seconds. APFS cloning preserved the prior kit; Factory, CARLA, service and
native-runtime bytes are unchanged. Manifest SHA-256:
`ba93d179e4bacd3b9d24ff26ebca551990f2983dda2995726a732e322e63e971`.
No credentials entered the package. This freeze is not an installed or
clean-Mac acceptance claim. The final-pin distribution suite passed 268 tests,
including the real process-usage guard, with no skips. Its initial harness
invocation lacked the already packaged `packaging` dependency; the corrected
test environment passed without a product change.

Setup 031 passed native protocol, embedded-bootstrap and strict/deep signature
checks. Its binary SHA-256 is
`6707ff7dd23bde3fc56031ad441881432de853358ae2cc7ead98ca12b63c12fd`;
the verified read-only DMG SHA-256 is
`fb4d36fee289cd25ef2fb1d9ccc53e36937e0b8d72c1431a77ff5da18162b899`.
The Apple Development designated requirement is unchanged from Setup 030.
This is not a Developer ID or notarization receipt. The ordinary native
Install action then completed for Kit 021 in the existing package store,
reporting Package installed — demo not started. Prepare/selection and launch
remain separate operations, not consequences inferred from that result.

The normal Prepare action selected Kit 021 at revision one for a separate empty
private instance. First Open and repeat Open both reported Presenter opened;
independent status observed exact geometry for its three native surfaces and
verified z-order. The same server and native window PIDs were retained by repeat
Open. No vehicle journal or credential directory was created. Missing simulator
and controller surfaces correctly remained incomplete, not full demo readiness.
No additional macOS permission prompt was observed during these operations.

All 77 VM/trust regression cases also passed against the actual installed Kit
021 modules with no skips. That runner used isolated fixtures, including the
exact dashboard-only first/repeat/restart and contradictory-binding cases; it
did not create a live VM or repeat Cloud publication. Do not equate this with a
fresh live native console-entry proof. Setup and Presenter were subsequently
closed through their ordinary paths and their processes were checked separately.

Remaining acceptance is specific: ordinary native access after the unclassified
Kit 020 console-authentication failure; retained-instance version selection
while shared Docker holds old directories; automatic incomplete-start cleanup;
clean native macOS E2E; and
whole-runtime distribution signing/notarization and redistribution obligations.
These gaps do not reopen successful serial transitions, real RSA enrollment,
publication, offline operation, power-cycle function or normal terminal Finish.

After the Kit 021 checks, ordinary workspace close and UI stop completed,
Setup exited and its read-only DMG was detached. Final process/listener checks
must be read with this later shutdown, not with the earlier Kit 020 state.

## Superseded kit and installer retirement

After deferring the three remaining same-Mac checks, the user explicitly asked
to remove obsolete kits. The scoped cleanup retired 16 source exports (Kit 004
through 019), 30 old Setup preview/diagnostic directories and five old Setup
DMGs. Kit 020/021 and Setup 030/031, including both retained DMGs, remain.
The source-export directory now contains only the current candidate and its
immediate predecessor. No installer, simulator or VM was launched for cleanup.

Before deletion, the audit checked the exact Work volume identity, path/inode
ownership, absence of links or nested devices, open-file owners and mounted
images. Each old kit's application source, manifest and input manifests were
preserved as compact evidence; existing Git source revisions were verified.
Setup receipts and operator notes were retained. Current Kit 021 application
exports and all five input-group inventories match the source locks. The
verified build-input record now points to Kit 021; the earlier Kit 010-based
recipe is historical and its removed paths must not be used for new builds.

Deletion stopped after nine complete exports when an immutable 0555 source
directory in Kit 013 rejected unlink. The existing removal receipts and exact
partial target inode were reconciled. Only owner-write permission on directories
inside the remaining authorized deletion roots was added before continuing;
no runtime or installation permission/guard was relaxed. All 51 targets were
then confirmed absent and the preserved package identities were rechecked.

Observed free capacity on Work increased from 517,190,914,048 to 520,024,678,400
bytes: **2,833,764,352 bytes, about 2.64 GiB / 2.83 GB**. APFS clones account for
the much larger aggregate directory sizes; those sums are not exclusive disk
usage. The measurement includes normal concurrent filesystem activity. No
internal payload was deleted in this batch; internal free space afterward was
167,588,102,144 bytes, about 156.1 GiB.

All 18 installed package versions, eight inspected instance selections,
credentials, ledgers, run evidence, Factory/build inputs, warm caches and the
separate video materials were preserved. Program-store pruning is distinct
from retiring immutable source exports and intersects the deferred retained
selection/all-instance retention gate; this cleanup does not claim that gate
passed or leave a selected instance with a missing program. Shared Docker and
unrelated workloads were not restarted or pruned. SDV-Clean was not modified.

Exact intent, target inventory, per-target completion receipts, preserved small
sources and the current build-input record are under
`SDV-Work/AosEdge-SDV/reports/kit-retirement-20260930`. Removed binaries were not
moved to Trash. Their small source/manifests and some installed equivalents
remain, but complete byte-identical restoration of every historical installer
is not guaranteed.
