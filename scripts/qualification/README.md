<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Remote Mac qualification harness

This development-side tool records bounded checks and transfers one pinned
engineering kit to the dedicated M1. It is not an installer, runtime owner,
Cloud client or formal qualification dossier. Native Setup and Demo Control
remain the installation and lifecycle authorities. UI acceptance is performed
through Screen Sharing, not inferred from SSH output.

Native `Open demo` must be invoked in the signed Setup GUI. Launching its
Python helper through SSH can attribute Accessibility to `sshd-keygen-wrapper`,
not Setup. Do not grant SSH Accessibility to make this check pass. The journey
adapter blocks `setup/launch`; reconciliation of an earlier attempt only
verifies normal cleanup and records failed acceptance without replaying launch.

## Real browser UI pilot

### Visible M1 mode (default)

The default is now `--scenario installed --display m1`: the browser driver runs
on M1, visibly, against its installed Presenter server. CARLA and Driving Control
are started by their ordinary product owners. The browser window occupies the
canonical right-hand Presenter rectangle and is brought to the front for each
step so the operator sees dialogs and navigation, not a hidden second client.
Before business checks, and again before each subsequent stage/action, the
driver requires the native owner's settled window placement and verified
ordering, and checks that its own visible browser remains in its normal,
canonical rectangle. A missing/locked native placement receipt or a
minimized/displaced browser stops the check instead of switching to headless
execution. Human readability/visual review remains
separate from the native owner's geometry receipt. Startup naturally precedes
the point where all three windows exist; confirmed Stop deliberately removes
them.
This is the real Presenter web build in a signed Chrome app-mode window, **not**
the native WKWebView shell. Native-shell acceptance remains a separate gate.

```sh
python3 -B scripts/qualification/ui_pilot.py \
  --scenario installed --display m1 \
  --config PRIVATE_TRANSPORT_JSON --journey PRIVATE_JOURNEY_JSON \
  --test RETAINED_TEST_UUID --dmg VERIFIED_LOCAL_DMG \
  --remote-dmg VERIFIED_M1_DMG --records NEW_PRIVATE_RECORD_DIRECTORY \
  --workspace EXISTING_SCRATCH_WORKSPACE
```

The explicit qualification tools live outside the installed product, under the
M1 test user's `SDV-Qualification/ui-tools/`. The first run copies the development
Mac's Google-signed Chrome and existing Playwright packages, and downloads a
vendor-digest-pinned ARM64 Node runtime into the selected build workspace. Strict
signature verification of the copied browser precedes execution. Framework
symlinks are retained, but Finder/resource-fork attributes are not copied; the
original Chrome application is unchanged. Later runs reuse the same tools.
No package manager, additional SSH port, SSH Accessibility, credential transfer,
Docker restart, product install or DMG rebuild is involved. The browser sandbox
is enabled. Private read requests return only the existing fixed owner
projections. They cannot publish, control the car or replace UI clicks.

At completion the owned visible browser closes, its temporary profile is removed
only after process exit is observed, and ordinary demo shutdown closes the other
owners. Reusable test tools and compact evidence remain; Docker and Test data
are preserved. Use `--scenario release-story` for the additional serial releases
and witnessed native maneuvers below. The following development-side mode is
retained explicitly for diagnostics.

### Development-side background pilot (explicit opt-in)

`ui_pilot.py` automates one short browser journey on a retained, already
qualified M1 Test. Playwright runs on the development Mac; M1 needs no Node,
browser-testing package or development checkout. One pinned SSH forward exposes
M1's installed Presenter at the same loopback port, without weakening product
Host/Origin checks. The normal harness continues to disable forwarding.

The one-time SSH exception needs explicit approval before it is configured.
Both the existing key and the server restrict the destination to
`127.0.0.1:18080`; the server allows local forwarding only and rejects reverse
listeners. Source-host and other key restrictions remain in place. The
administrative helper is not part of Setup or the runtime. When using a bundled
immutable Python interpreter, invoke it with **`-I -B`**, preferably from a
verified shell wrapper: never let an administrative launch write bytecode
caches into the installed package. Do not give SSH Accessibility or broaden
forwarding to make the pilot pass.

```sh
python3 -B scripts/qualification/ui_pilot.py \
  --scenario pilot --display background \
  --config PRIVATE_TRANSPORT_JSON --journey PRIVATE_JOURNEY_JSON \
  --test RETAINED_TEST_UUID --dmg VERIFIED_LOCAL_DMG \
  --remote-dmg VERIFIED_M1_DMG --records NEW_PRIVATE_RECORD_DIRECTORY \
  --workspace EXISTING_SCRATCH_WORKSPACE --node DEVELOPMENT_NODE_EXECUTABLE
```

The private journey record binds the exact installed candidate and retained
Test. Expected card versions come from that Test's qualified VDP V3, Brake V3
and Tire V1 observations, not a guessed latest Cloud release. Matching signed
Setup media supplies the existing bootstrap/shutdown helper. A changed consumer
file identity requires one digest re-verification; unchanged media is not
retransferred or repeatedly hashed. No installation or DMG build is performed.
The optional `--media-records PRIVATE_PREVIOUS_RECORD_DIRECTORY` reuses an
earlier successful consumer verification only when its digest, byte count and
current remote file identity match. A receipt alone is not proof that a changed
consumer copy remains intact.

The script clicks Start controller, Start simulator and Connect in Manual,
opens the three installed-detail cards, cancels Stop, then confirms Stop. All
four scenario actions originate from actual buttons. A request guard permits
only those actions in that order, with the current session and unique request
IDs. Intent is flushed before forwarding, with no header/payload rewriting or
mock responses. Cancellation must send no mutation. Terminal failure stops the
scenario; an unknown outcome is observed, never blindly replayed.
Observe the actual submission acknowledgement before polling a job: HTTP
400/403/409 stops immediately as rejected; a lost or mismatched acknowledgement
is uncertain and prohibits replay. Wait at most 30 seconds for the complete
owner idle gate, including window-placement retries and source recovery, before
clicking. Do not confuse a recorded dispatch intent with an accepted operation.

Keep one-time host authorization outside the measured scenario. Stage timings
include real controller/backend or simulator startup when the pilot deliberately
starts those owners. A fast UI check on an already running environment is a
different scenario; do not skip Start/Stop acceptance while reporting it passed.

Independent read-only owner checks corroborate controller/backends, exact
Test/Unit/Node/system identity, stationary Manual attachment, preserved journal
and unchanged Docker Engine. Stage timings, bounded codes and screenshots with
input fields masked go into private records. Raw network traces, credentials,
product responses and exception text are not retained. Temporary browser
profiles use the selected workspace's owned `.tmp` and are removed on exit.

Final ordinary shutdown closes demo-owned applications and listeners. The
browser and tunnel close; only media mounted for the pilot is normally detached.
Docker remains running; Test disks, history, credentials and packages remain.
The report distinguishes browser-pilot acceptance from native Setup/WKWebView,
layout and full E2E acceptance. A browser pass does not close those native gates.
The browser runs headlessly on the development Mac, not in an M1 browser
window. This does not establish native window visibility or placement on M1.

Local guard tests do not start M1 or the demo:

```sh
node --test scripts/qualification/test_ui_pilot.mjs
PYTHONPATH=scripts/qualification python3 -B -m unittest scripts/qualification/test_ui_pilot.py
```

### Extended installed UI scenarios

The same entry point accepts `--scenario installed` or `--scenario release-story`.
Use the same candidate/Test/media arguments above and a new private record
directory for each diagnosed experiment. Never erase a failed attempt or reuse
its request IDs. The script does not change the DMG. Background mode requires no
M1 testing tools; visible mode uses the separate tools described above.

`installed` exercises Start controller, Start simulator, Connect in Manual,
all installed-detail cards, Platform/Brake/Tire perspectives, Cloud software and
resource views, both backend views, independent Brake/Tire Reset with correlated
CLEAR and preserved peer model/history, Activity, Stop cancellation and confirmed
Stop. Publication is not part of this scenario. Every mutation comes from an
actual browser click and must match the exact currently armed command. Unknown
responses stop the sequence; no direct mutation adapter or blind retry exists.

`release-story` additionally prepares and publishes VDP V1/V2/V3 and Brake
V1/V2/V3 serially, then Tire V1, on the retained Test. Release values are obtained
from preparation receipts. Each matching installation must be observed before
the next publication. Existing Subjects remain assigned; the scenario does not
create, provision, retire or reassign. It is a retained-Test release story, not
a clean first-user installation.

Native Safe Stop and maneuvers are not HTML buttons. This scenario writes a
bounded `native-ui-gate.json` and waits for supported CUA control of the named
visible Driving Control button. After the click, record its exact witness:

```sh
python3 -B scripts/qualification/ui_native_gate.py \
  --records PRIVATE_UI_RECORD_DIRECTORY --stage EXACT_WAITING_STAGE \
  --action 'EXACT_VISIBLE_NATIVE_ACTION' --witness-cua-click
```

The witness helper does not click, invoke driver RPC or prove the postcondition.
The browser runner independently confirms physical Safe Stop or a new matching
backend product after the click. Do not acknowledge a gate before a supported
CUA click. Wrong stages/actions/identities and repeated acknowledgements fail
closed. This is agent-assisted native UI execution, not a fully unattended
native test. An unexecuted gate times out, fails the scenario and triggers
ordinary shutdown. Native gates retain their failed evidence.

The initial desktop check requires an unlocked M1 before owners start. A lock
observed during placement stops instead of waiting minutes for a nonexistent
operation. Control evidence uses the native `MANUAL` mode and a brake fraction
of at least `0.99`, not display wording or a percentage. Input freshness,
ownership, stationary speed and at-most-once safeguards remain unchanged.

```sh
node --test scripts/qualification/test_ui_pilot.mjs scripts/qualification/test_ui_journey.mjs
PYTHONPATH=scripts/qualification python3 -B -m unittest scripts/qualification/test_ui_pilot.py
```

Reports distinguish these scenarios from native Setup/WKWebView/layout,
first assignment, moving SOTA, offline/ignition and clean installation/repair.
Those separate gates cannot be inferred from a browser pass; `fullE2E` remains
`NOT_COMPLETE`. Actual M1 outcomes are recorded in the
[branch qualification receipt](../../docs/qualification/presenter-human-friendly-2026-10-11.md).

### Targeted VDP profile transition diagnosis

`--scenario vdp-transition --display m1` starts the retained Test and its visible
native surfaces, connects in stationary Manual and requires a current same-Test
Cloud binding for installed VDP V1 with no pending component update. It selects
V2 and clicks Prepare once, guarded against any other request, then confirms
ordinary Stop. It does not sign, publish, install, assign, Reset or delete.
Historical installed-card expectations are not used to establish its baseline.

Snapshot request records contain only status, elapsed time and matching/missing
run classification. Rejected requests retain only the fixed guard code,
supported expected/actual profiles and session equality. Missing observations
and failed submissions remain terminal. This diagnostic cannot establish a
complete V1-to-V2 deployment, a new candidate's acceptance or full E2E.

## Record and acceptance rules

The private configuration and records live under `.local/remote-qualification/`,
outside product state and Git. Schema 1 binds a run ID, exact SSH target and
server fingerprint, source address, OS/model, internal destination, kit manifest
and Setup digest. Each attempt records its command, UTC start/end, duration,
harness digest, fixed outcome code and allowlisted observations. Outcomes are
`PASS`, `FAIL`, `BLOCKED` or `UNCERTAIN`; absent steps are `NOT_RUN`.
History is append-only at the attempt level. An unfinished intent is uncertain,
not success. A single local writer holds a file lock across each operation.

The initial preflight requires the pinned host, current console user, arm64,
expected model/OS, at least 16 GiB RAM, internal storage, idle demo ports and
processes, and enough space for two complete kit copies plus Setup and the
existing 90 GiB installation reserve. Dependencies are inventoried separately;
a missing Docker installation is a next step, not evidence of runtime readiness.
These are engineering entry conditions, not a published hardware minimum.

`stage-kit` verifies the source with the existing complete-kit reader, transfers
without deletion, and rechecks every destination file's SHA-256, size and mode,
inventory, ownership and absence of links. The remote directory is newly created
for this run and marked with the exact run and candidate pins. It cannot adopt
an unrelated directory. A failed or interrupted transfer is never blindly
replayed: use read-only `reconcile-stage` first. An incomplete transfer remains
blocked for explicit investigation. No staging command opens or executes the kit.

## Commands

Run with development Python 3.9 or later:

```
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG status
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG preflight
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG stage-kit
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG reconcile-stage
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG collect
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG stop
python3 scripts/qualification/remote_harness.py --config PRIVATE_CONFIG report
```

`status` and `report` are local reads and start nothing. `collect` captures only
bounded system counters, dependency presence and conflicts. No keys, tokens,
arbitrary command lines, screenshots or application logs enter these records.
SSH agent/port forwarding and implicit user configuration are disabled.
Any separate diagnostic using the installed private Python must invoke it with
`-I -B`: isolate its import environment and prohibit bytecode writes into the
immutable package. Do not run it as an ordinary development interpreter or
relax inventory checks to accept diagnostic cache files.
After verified staging, status directs the operator to the dated native
qualification receipt: this helper does not observe Setup and cannot infer that
installation has not started merely because it has no native-action record.

Before an installed instance exists, `stop` verifies absence of demo processes
and ports; it does not kill unidentified processes or stop shared Docker.
If anything is active, it reports `BLOCKED`. Once installation begins, use the
installed owner's ordinary shutdown through UI, then run this verification.
The installed scenario extension below is engineering evidence, not native UI
acceptance. It reuses product owners; it does not change their lifecycle rules.

## Installed scenario checks

The 1 October efficiency refinement adds a private target record containing the
installed package digest, package path, instance path and exact existing Test
VM identity. It is separate from the immutable original transfer configuration.
Every attempt records that target identity and the current harness source digest.
Candidate changes never carry a previous candidate's pass forward.

The target JSON has exactly `schemaVersion: 1`, `packageRoot`, `instanceRoot`,
`manifestSha256` and `localVmId`; the last four values are strings. Resolve them
from the verified installed selection and retained Test, not a guessed default.
Keep this file mode 0600 under the existing private qualification directory.

```
python3 -B scripts/qualification/remote_harness.py --config PRIVATE_CONFIG --target PRIVATE_TARGET status
python3 -B scripts/qualification/remote_harness.py --config PRIVATE_CONFIG --target PRIVATE_TARGET run local-start
python3 -B scripts/qualification/remote_harness.py --config PRIVATE_CONFIG --target PRIVATE_TARGET verify presenter-consistency
python3 -B scripts/qualification/remote_harness.py --config PRIVATE_CONFIG --target PRIVATE_TARGET run local-stop
python3 -B scripts/qualification/remote_harness.py --config PRIVATE_CONFIG --target PRIVATE_TARGET report
```

`local-start` checks the bound instance, starts the controller and both backends
through their owners, and checks controller and backend observations. `local-stop`
stops that controller and both backends without retirement or data deletion.
Each action first gets a fresh postcondition read: an already achieved state is
not re-executed. Unknown reads block. A resumed sequence reconciles an uncertain
action first, then follows the same read-before-action rule. It does not use
historical pass flags as current runtime authority.

`verify installed`, `verify controller-running`, `verify backends-running`,
`verify presenter-consistency` and `verify stopped` read the installed product
and compare explicit expectations. `verify local-baseline` runs the first three
checks in order and stops at the first failure. A pass is an observation at its
recorded time, not permanent readiness. Repeating a read is safe and obtains
fresh evidence; a failed attempt is never overwritten by a later pass.

The engineering `action` command has only five fixed adapters: `vm-start`,
`vm-stop`, `brake-start`, `tire-start` and `backends-stop`. They invoke the
installed Demo Control owner once for the bound Test. No arbitrary command,
shell fragment, Cloud mutation, dependency installation or implicit Docker start
is accepted. The target, staging domain, absent Production and absence of an
active/uncertain Presenter operation are checked before an adapter executes.
An incomplete or uncertain action blocks another action. `reconcile` observes
the relevant postcondition and records a separate resolution; it never replays
the mutation. A failed or unreachable read cannot resolve an uncertain action.

The per-attempt record separates operation duration from subsequent observation
time and states `ENGINEERING` with native acceptance `NOT_RUN`. Raw product
responses, process arguments, credentials and exception text are not retained.
Remote diagnostics use only the installed private Python with `-I -B`, never
write into the package and do not copy development dependencies to M1.

These initial scenarios cover local diagnosis and exact-owner actions. The
journey runner below adds the serial deployment and recovery sequence. Neither
tool can mark native UI acceptance from engineering observations.

`verify stopped` covers the bound controller and backend processes while Docker
is available. It does not claim that Presenter, CARLA or Driving Control has
exited. Close those through their owners at session completion and verify exit.
Docker Engine/Desktop remains running in the background: it is infrastructure,
not a test-owned application to quit. Do not open Dashboard for ordinary tests.
Do not run `local-stop` between successive steps that still need the same active
test environment. Run it at a deliberate pause or the end of the local sequence.

Actual live coverage is recorded in the dated qualification receipts, not
inferred from an implemented adapter. External SSD and host sleep/wake cases
are excluded from the current M1 profile. Deferred defects remain deferred;
any recurrence is a current failure. Every pause must close the demo-owned
applications and verify exit; never infer shutdown after a lost connection.

## Resumable installed journey

`journey.py` runs one fixed staging sequence through the installed product. It
does not rebuild or patch the package, inject telemetry, replace the installer,
or create its own Cloud or VM lifecycle. Use it after verified installation and
selection; media transfer, installation/repair and initial macOS consent remain
separate evidence. The `campaign.py` entry below joins those engineering steps
without turning them into native acceptance. Matching signed Setup media remains available while
the runner uses its embedded worker and launch validation.

The sequence covers dependency readiness, signed Setup backend preparation,
existing OEM/SP reference selection and Cloud access, controller creation,
CARLA startup, provisioning and connection, sequential VDP V1/V2/V3 and Brake V1/V2/V3,
Tire V1, real maneuvers and fresh backend/advisory observations. It then checks
independent Reset with observed history preservation, Return to road, five
minutes of external-OFF local processing and queued recovery after ON,
same-identity stationary ignition, and demo shutdown. Version numbers are
allocated by the installed product; the runner never guesses or pre-publishes
all versions. VDP publication requires physical Safe Stop.

Start CARLA before provisioning: the product establishes the protected source
connection before assigning Test-set membership, which may immediately offer
an existing Cloud component. Provisioning first can start FOTA before its
Gateway credentials exist. Never bypass the active-transaction credential guard
to compensate for a reversed test sequence.
Provision already connects the first Test in stationary Manual. After the first
physical Safe Stop, observe that any already-offered component update has
settled in Cloud before the redundant `connect-test` confirmation and before
preparing/publishing VDP V1. Confirming the empty Factory connection first can
race that update; stopping after a failed confirmation can leave its incoming
transaction waiting for Safe Stop. This is a bounded read of the existing update,
not another deployment or a relaxed release gate.

Raw ignition recovery must remain in Safe Stop. The deliberate Stop/Start
sequence instead starts the simulator and invokes `connect-test`, whose contract
is stationary Manual. Its preservation check requires fresh, unheld Manual
telemetry, speed at most 0.5 km/h and at least 99% brake, alongside a new boot and
unchanged identity, models and history. Do not reuse the raw-ignition mode
expectation or weaken that expectation to accommodate an explicit Manual action.

Brake V3 advisory correlation also accepts its documented first-activation
decision from the exact pinned V2 release, when that assessment is still present
and reports a valid synthetic `INSPECTION_RECOMMENDED` condition. D4-016.4
requires refreshing that same decision while the condition remains active;
it does not require a new decision for every later maneuver. The separate new
V3 product gate remains mandatory. An old advisory producer version, unknown
assessment, invalid condition or transport receipt alone cannot pass. Tire
retains its new-assessment correlation rule.

After ignition, VDP readiness is followed by a separate input gate for each
service. It requires a non-stale, conflict-free function observation from the
same native instance and exact release, with generation greater than before
ignition and locally validated `CONNECTED` / `RECEIVING` inputs. A retained
green preboot observation, a merely active container, or ready VDP alone cannot
start the functional maneuver. Fresh product IDs are still checked afterwards.

For existing accounts, pin the previously explicitly selected public
`subjectReferences` in the private journey configuration. The Setup gate runs
before Create Controller, freshly verifies each exact reference, and saves it
through the signed Setup owner. It never chooses an eligible item by label.
If Cloud has existing candidates but no matching explicit selection, the gate
blocks before creating a Test. Preserve the returned metadata token after each
save. Service publication has its own exact READY observation before assignment;
an accepted upload is not sufficient.

```
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY plan
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY status
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY verify-host
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY run
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY report
python3 -B scripts/qualification/journey.py --config PRIVATE_CONFIG --journey PRIVATE_JOURNEY stop
```

`run` normally executes the entire remaining sequence, not one command per
phase. `--until STEP` is for a deliberate checkpoint or harness diagnosis; it
does not skip prerequisites and still closes the demo at the boundary.
`verify-host` is a small, fresh installation/Docker/Presenter smoke that creates
no controller or Cloud Unit and publishes nothing. It closes Presenter and
preserves Docker. `status`, `plan` and `report` start nothing.

Docker readiness is checked through the local Engine API. An available Engine
is reused. If its API is unavailable but its backend exists, the adapter waits
within the fixed budget rather than launching another application. Only a
confirmed absent backend is started through Docker CLI. There is no Engine
stop/restart/quit command in the journey, including its error cleanup. Demo
containers are stopped through Demo Control, with their persistent data kept.

### Candidate and access binding

The original private transport configuration supplies only pinned SSH identity,
host and source address. Its older artifact fields do not establish the current
candidate. The separate mode-0600 journey JSON has exactly these fields:

- `schemaVersion`: `1`.
- `manifestSha256`, `setupSha256`: independently verified candidate identities.
- `packageRoot`, `instanceRoot`, `storeRoot`: exact installed package and state;
  `packageRoot` must be `storeRoot/versions/manifestSha256`.
- `setupApp`, `sourceRoot`: the matching `AosEdge SDV Lab Setup.app` and sibling
  `Runtime Kit` on the verified media.
- `image`: the explicitly bound Factory `.39`, `.40` or corrected `.41` candidate
  catalog selector. A new Factory/kit requires a new record binding; it cannot
  inherit a previous candidate's passes.
- `oemCertificate`, `spCertificate`: authorized existing credential file
  references on M1, never copied private-key contents or command-line tokens.
- `records`: private development-side path under `.local/remote-qualification/`.

All paths are absolute. Package and instance directories must not overlap.
The binding is immutable once evidence exists. Only the dedicated Test in
`aws-stage.epmp-aos.projects.epam.com` is allowed; any Production entry or
changed Test/candidate blocks the operation. A new Test identity is adopted after
its own Create job agrees with the product journal. A terminal partial Create
binds identity for cleanup and diagnosis, not a passing Create or permission to
provision. It must be the exact unprovisioned Test-only staging run.

### Continuation and evidence

The runner journals intent and request/session identity before dispatch. A lost
response is `UNCERTAIN`, not a retry invitation: the next run reconciles that
same identity before other mutations. A changed Presenter session or missing
authoritative result remains unresolved. Do not delete evidence to bypass it.

Completed publications, assignments and resets are not replayed. Before an
ordinary continuation, current installation and infrastructure are re-observed;
previously reached runtime owners are restored through their normal paths when
they are confirmed stopped. Historical `PASS` is not current runtime readiness.
If shutdown interrupted a Reset, offline, ignition or same-Test Stop/Start comparison, the runner
blocks that experiment with `EXPERIMENT_INTERRUPTED_REBASE_REQUIRED`. It never
combines readings from incompatible boots or sessions. Diagnose and establish a
new scoped experimental baseline; do not silently replay the interrupted reset.

Attempts retain duration, candidate, source digest and fixed non-secret facts.
`report.json` separates main steps, supporting checks, unresolved operations and
source-revision review. A changed step definition cannot inherit a previous
pass. A source-revision warning calls for review of affected evidence, not blind
republication. The offline soak samples through the end of its actual 300-second
interval. Backend checks use the observed bounded product history; they do not
claim an exhaustive database integrity audit.

The fixed journey also exercises the Presenter `stop-demo` and `start-demo`
plans after ignition. Fresh observations must confirm the Test VM, source and
both owned backends stopped, unchanged Unit/Node identity and the same running
Docker Engine. Restart explicitly starts the simulator and attaches the same
Test; it must preserve models and product history, confirm fresh stationary
Manual after that explicit connection, and produce new Brake/Tire results from
fresh post-restart inputs. Raw ignition remains subject to its separate Safe Stop
requirement. It does not create,
provision, publish or assign again. This is live engineering coverage of normal
product plans, not native-button acceptance or destructive retirement.

Native operator flow, secure token entry, service update while moving, and
installation interruption/repair retain separate acceptance gates. Finish is
not part of automatic cleanup. The current implementation has no automatic
Finish wrapper or moving-SOTA adapter. Full E2E stays `NOT_COMPLETE` regardless
of successful scripted steps until the separate acceptance evidence is closed.
See the [runner qualification record](../../docs/qualification/scripted-journey-2026-10-02.md)
for actual unit and M1 execution results.

## One command engineering campaign

The [10 October work packet](../../docs/planning/active/autonomous-m1-qualification.md)
joins pinned media delivery, signed Setup installation/preparation, the serial
journey, failure diagnosis and ordinary demo-only shutdown. It never rebuilds
the candidate or replaces a retained installation to force selection.

```
python3 -B scripts/qualification/campaign.py \
  --config PRIVATE_SSH_CONFIG --journey PRIVATE_JOURNEY_CONFIG \
  --dmg /absolute/path/to/Lab.dmg \
  --remote-dmg /Users/tester/SDV-Qualification/candidate/Lab.dmg
```

The DMG's sibling `.receipt.json` must match the journey's manifest pin and
the transfer bytes/digest. Setup has its own executable pin. The target must
be the pinned M1 and the ordinary internal installation path. No old-image
unmount, retained-Test retirement, SSH Accessibility grant, hidden dependency
installation or Docker restart occurs. An occupied mount fails instead of being
detached. Verified unchanged media is reused. Interrupted transfer, install or
selection requires exact read-only reconciliation; incomplete media is never
overwritten. Installation attempts are in a sibling
`<journey records>-installation` folder; runtime attempts and `report.json`
stay in the existing journey folder.

Unattended runs require explicit Test access before Create. Optionally add
`vmPasswordFile` to the private journey JSON: an absolute path on M1 to an
owner-private, single-link, mode-0600 JSON file with exactly one `password`
field. This is the existing development Factory password, not a new password
or a Cloud credential. Prepare the file once outside the package and evidence
directories; never paste its contents into a command or report. The installed
owner validates it and stores an equally private qualification profile bound
to the instance, staging and Factory digest. Later runs need no dialog.
No password is guessed, extracted from legacy tools or shipped as a default.

An absent file/profile is a fast `QUALIFICATION_ACCESS_INPUT_REQUIRED` stop,
before creating/starting a VM. An invalid profile never falls back to prompting.
Ordinary installations without the explicit profile still use native secure
input/Keychain. Automated access does not pass that separate native UI gate.

On a terminal failed mutation the runner stops with projected diagnosis before
cleanup. Re-running does not replay the mutation. After a diagnosed correction,
`--resume-partial-create` explicitly continues only the same bound partial
Create through Demo Control's idempotent path. It cannot replay a publication,
provisioning, assignment or reset. Candidate changes use new bindings and cannot
inherit previous passes.

Attempts record remote-call time, explicit postcondition-wait time and diagnostic
time. Remote time includes product execution and its internal waits; it is not
presented as pure CPU work. Long calls have a local elapsed-time heartbeat
without extra network probes or invented ETA. Bounded failure projections omit
free-text logs, arbitrary exception messages and credentials.
