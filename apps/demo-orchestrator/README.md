<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Orchestrator

### Cloud-only Test observations

`democtl unit cloud-status test` reads the current Test's Cloud-reported
components, Subjects, services and actual instances. `democtl unit monitoring test`
reads its latest resource samples separately. Neither command queries the VM,
changes Cloud, waits for an update or performs an environment audit. Missing,
empty and failed observations remain distinct; CPU is DMIPS, while unverified
RAM/disk/traffic scaling remains explicitly unknown. See the
[bounded read/result contract](../../docs/architecture/demo-control-cloud-observation.md).

Development update: the normal simulation now opens **Driving Control & Telemetry**
as one native window beneath the separate CARLA window. It consumes the existing
VISS client's JSON output; no Terminal dashboard opens. Use the same
`simulation start/stop`, `vehicle select test` and workspace commands. Older
Terminal-layout descriptions below record the published checkpoint; native
telemetry is currently under live visual review, not formally qualified.

### Vehicle external connectivity

The Driving Control button invokes the same commands available in the CLI:

```bash
democtl vehicle connectivity status
democtl vehicle connectivity off
democtl vehicle connectivity on
```

OFF affects only the currently selected VM's external connection: Aos Cloud
and functional backends. Local CARLA/Gateway/VISS, maintenance SSH, the Mac's
Internet connection and the other VM are preserved. ON removes that transient
filter without restarting or reprovisioning anything. ON/OFF is the observed
filter setting, not a claim about Cloud reachability; Cloud may report Offline
or Online later. The telemetry dashboard remains vehicle-data-only.

Restore connectivity before selecting another VM. If simulation was stopped
while the link was OFF, restore explicitly with
`democtl vehicle connectivity on --target test` (or `production`). Closing the
control window does not restore the link; a VM reboot clears the transient
filter. The native button checks the setting every five seconds without a
Cloud API call. An unavailable reading is UNKNOWN, never assumed ON.

The current [source/evidence checkpoint](../../docs/qualification/democtl-release-checkpoint.md#desktop-preparation-checkpoint--2026-09-07)
and accepted [native desktop plan](../../docs/planning/active/native-demo-desktop.md)
are the starting point for this UI increment. Control and telemetry are now
combined; the one-click launcher is not implemented. CARLA remains separate.

### Local Presenter control

Operator workflow (same core in CLI and the UI's **Prepare demo** button):

```bash
democtl demo plan --image 6.1.1-maninblack.31/main-qemuarm64
democtl demo prepare --image 6.1.1-maninblack.31/main-qemuarm64
```

Plan is read-only. Prepare chooses/reuses the correct v1 release automatically,
creates or continues matching Test/Production VMs, publishes/approves baseline
v1, starts/provisions both roles, starts simulation and initially connects Test
in stationary Manual. Then the operator starts Autopilot and presses Safe Stop.
The component may already be downloaded; activation waits for actual Safe Stop.
Completed stages persist in the existing run journal, not in the browser.
Failures retain the exact stage; another call never blindly repeats a Cloud
mutation. Already-prepared calls do not reset or restart the vehicle.

UI and `demo prepare` use a visible macOS VM-access dialog or the fixed Keychain
item. To configure it separately: `democtl access setup`. **Save in Keychain**
is optional and explicit; **Use once** lasts only for that command. No hidden
terminal prompt, password in argv, or browser credential. Cancel stops the flow.

After building the existing `apps/presenter-ui` package, run `democtl ui serve`
from this directory. The foreground server exposes the UI at
`http://127.0.0.1:18080/`, local observations and explicitly confirmed operations.
Startup does not start VMs or call Cloud. Buttons invoke the same application
core as CLI. Cloud and guest reads are explicit, never background polling.
Private native port 18600 uses a temporary backend-only capability; enter the
first-SSH password in the native macOS dialog, never in the browser.
No caller-selected command, path, target, credential or Cloud endpoint is
accepted over HTTP. Fixed actions prepare both VMs; VDP delivery is Test-only.
One job runs at a time with immediate receipts and no automatic retries.
Ctrl+C while idle closes the UI session, preserving VMs and Units. Reset is a
separate confirmed action without backups. Native composition has been visually
accepted on the built-in display; complete fresh-environment UI E2E remains
unqualified. See the
[Presenter UI instructions](../presenter-ui/README.md).

### Built-in Mac display workspace

With the local Presenter server and simulation already running:

```bash
democtl workspace restore
democtl workspace status
democtl workspace close
```

`restore` places only the current demo's windows on the built-in display:
shared header, CARLA upper-left, Controller and native Terminal telematics
below it, and the Platform/Lifecycle panel on the right. The two Presenter
windows host the existing local UI, not a separate lifecycle implementation.
The compact profile aligns CARLA and the dashboard at their right edge,
narrows the Controller and expands the right panel (approximately 45/55).
The shared header and dashboard width are unchanged on the built-in display.
A black background in the same Presenter process fills the working area
behind the demo panels. It closes with Presenter and does not change macOS
wallpaper/settings. A changed native Presenter binary reloads only those UI
windows during restore, never the simulator or VMs.
`workspace close` gracefully closes only the owned native Presenter windows
and black background. The simulation, VMs, Cloud Units and local web server
remain running. Repeating close is a no-op; restore recreates the windows.
`status` only observes; neither command connects a VM, touches Cloud or
changes driving mode. A missing window or denied macOS Accessibility access
is reported as incomplete, not as a successful layout. The app/Terminal from
which `democtl` is invoked needs the relevant macOS Accessibility/Automation
permission; permission for an unrelated app is not sufficient.

After the first restore, a new `simulation start` restores this layout
automatically. Its existing single telemetry client renders in one native
Terminal, not an HTML copy or a log-following second client. Healthy repeated
starts do not restart the simulator. The controller is resizable. The operator
accepted the compact composition and black background; later layout changes
still require visual review. Interactive sessions now run until explicitly
stopped, without the old one-hour cap. Startup and safety timeouts remain.

### Cold start of the preserved environment

In one terminal, keep the local UI service running:

```bash
democtl ui serve
```

In another terminal in this package's activated virtual environment:

```bash
democtl vm start all
democtl simulation start
democtl vehicle select test
```

`simulation start` does not itself attach a VM. The last command is required
and leaves the car in Safe Stop; this is everyday restart, not the initial
stationary-Manual Prepare workflow. Existing Units, installed releases and
overlays are reused without provisioning or component publication.

### Factory .29 qualification additions

For repeated demos use the [monotonic release / frozen profile sequence](#component-artifacts-and-test-delivery)
below. The older reapproval/addressed-send commands in this section document
the prior investigation, not the current repeat-demo procedure; its one live
addressed 2.0.0 request was rejected by Cloud HTTP 400.

`democtl component send 2.0.0` explicitly requests delivery of the existing,
approved component to this environment's Test Unit. The same interface supports
3.0.0 when separately authorized. It does not upload/sign/rebuild, change Unit
Sets or approve fleet validation. It resolves the version ID from Cloud, records
one attempt, requires HTTP 201 and post-read reconciliation, and never blindly
resends after uncertainty. Repeated confirmed requests are read-only no-ops.
Acceptance is not installation: follow with `component status test` and
`component logs test`. Production, custom UUID/URL and arbitrary target options
are not accepted. `component cloud-status VERSION` also lists Test send requests.

`democtl component unapprove 2.0.0` (or `3.0.0`) temporarily removes approval
from the uniquely resolved existing verification batch. Restore sequentially
with `democtl component approve VERSION`. These commands do not upload another
bundle or approve fleet validation. Existing approval state is read first;
uncertain mutations require reconciliation and are not blindly repeated.

`democtl unit unassign test` removes only the stopped, detached Test Unit's
bound Test Vehicles membership. Its provisioned Unit, disk and all other
memberships remain. Production/all are rejected. This is distinct from
deprovision/delete and is intended for retaining the previous Factory baseline
while qualifying a successor. A single-Test qualification reads the existing
bound Production-set member as a Cloud guard; it does not acquire local
ownership of Production.

An isolated `aosedge-sdv-demo-qual-*` single-Test qualification reuses the
canonical runtime's DNS bridge only after its journal, exact command/PID and
script bytes match. The dependency is recorded as `EXTERNAL_DEPENDENCY`; its
stop operation cannot terminate that bridge. An unknown listener is still an
error, not a fallback. Keep the canonical Production owner running throughout
this qualification; do not stop/retire that owner while the Test depends on it.

`democtl` is the headless interface to the native Demo Orchestrator. The future
local API and Presenter UI use the same application core; they do not implement
VM or AosCloud lifecycle operations independently.

This package implements read-only status, image discovery and local environment
creation, local VM start/stop, OEM Unit provisioning/deprovisioning/deletion,
and cleanup of unprovisioned or explicitly Cloud-retired local output. No legacy
lifecycle workflow is called. After `simulation stop`, `unit deprovision` and
`unit delete`, `environment retire` also removes the stopped telemetry source's
owned runtime outputs and completed component-operation journal records. It
does not delete original images, published bundles, Cloud releases, Unit Sets,
source code or Builder caches, and adds no backups.

The [Demo Control design](../../docs/architecture/demo-control.md) records the
agreed direction, documentation audit and proposals still under review,
including implemented status observations and remaining lifecycle proposals.

## Current commands

### Role initialization and Cloud request economy — 2026-09-06

`vm start` stages the exact Test/Production role for the native SM start
sequence. On an unmounted store it reports `STAGED_BEFORE_SM`; it does not
write beneath a future mount. An owned `/run/systemd/system/aos-sm.service.d/20-democtl-role.conf`
`ExecStartPre` writes the role after SM's existing bootstrap/mount dependencies,
before SM reads its configuration. There is no extra SM start/restart, image
rebuild, copied image or separate persistent role store. A mounted valid role
is reused; a conflicting role fails. `unit provision` includes role readback
in its existing guest readiness read. `component sm-status test` reports the
role and mount observation. On reboot the role remains in the component store.

Cloud commands keep authenticated OEM/permission and exact-target checks,
one recorded mutation attempt and authoritative confirmation. Verification-Test
publication returns HTTP acceptance immediately; `component cloud-status VERSION`
separately observes processing, Ready or Error. It needs no batch approval or
Production VM. Explicit engineering approval still reads its known batch and
retains its historical Production guard. Known batch UUIDs use their detail endpoint.
The v11 deployment-bundle detail route supports DELETE only: read its collection
and select the exact recorded UUID; never issue GET to that detail route.
Approval does not reverify a local archive or require Test Online. Its post-read
must confirm the requested approval value. Upload still verifies signed bytes,
release ordering and compatibility; addressed-send and destructive cleanup
retain their separate scope checks.

Production FOTA is deferred pending a platform release. On 2026-09-06 the
operator reported confirmation from the Aos platform developers: the current
deployment delivers updates only to Units in verification sets. This is an
operator-reported platform limitation, not a conclusion from HTTP 403 or a
reason to change OEM permissions, Production membership or campaign settings.
`component cloud-status VERSION` reads the owned bundle, catalog version and
current Test Unit without querying verification batches, Production or campaigns.
Production remains a non-verification set. Its lifecycle
and source selection remain available, but Production FOTA is not qualified.

Unit lifecycle discovery reads only the two role sets, not other sets' members.
Online/membership/offline waiting uses one authenticated Cloud client for that
wait, resolves an unknown Unit UUID once, and reuses known Node identity. Each
subsequent poll reads the exact Unit; there is no repeated `users/me`, Unit
search or Nodes inventory per poll. Independent mutation stages still verify
their own OEM authority. No persistent credential/session cache is added.

Prepared v1/v2/v3 profile replays can be published before provisioning the
owned Test, including while connected/running in initial Manual. No hidden
Production VM is required. Before publication all verification-set membership
pages must prove that no other Unit can receive the update. After provisioning,
only the current Test may be a recipient; Offline is not a host-publication block.
Compatibility comes from the exact Factory copy receipt and a producer catalog
declaration, not guest SSH. Missing declaration is a blocker: the retained .31
artifact is not automatically grandfathered in by version number. See the
[publication contract](../../docs/architecture/demo-control-component-publication.md).
The operator confirmed the Test .31 sequence 10/v1 -> 11/v2 -> 12/v3 and visual
Safe Stop-gated replacements. The separate fresh-overlay repeat, full advisory
and independent-consumer qualification remain outstanding. See the
[current Test baseline](../../docs/qualification/democtl-release-checkpoint.md#current-test-baseline)
for exact artifacts, evidence and deferred scope. No new image is needed merely
to checkpoint these already exercised host-side corrections.

```text
democtl image list
democtl component list
democtl component inspect 1.0.16
democtl component unpack 1.0.16
democtl component verify 1.0.16
democtl component prepare --profile v1
democtl component sign VERSION
democtl component upload VERSION
democtl component cloud-status VERSION
democtl component status test
democtl component logs test
democtl component diagnose test
democtl component schema-apply test
democtl component schema-remove test
democtl environment create --image VERSION/ARCHITECTURE --target all
democtl environment create --image-path /absolute/catalog/image.img --target test
democtl environment retire
democtl status [test|production|all]
democtl status test --guest
democtl status --cloud
democtl status --guest --cloud
democtl --output json status --guest --cloud
democtl vm start <test|production|all> [--timeout 90]
democtl vm stop <test|production|all> [--timeout 90]
democtl unit provision <test|production|all>
democtl unit deprovision <test|production|all>
democtl unit delete <test|production|all>
democtl simulation start
democtl simulation stop
```

Status, image list, environment create, VM start/stop and unused/Cloud-retired CLI environment retire are
implemented, as are the three unit commands and local-profile environment
prepare/vehicle select. `environment park` / `environment resume` preserve the
owned Test disk and Cloud identity. They do not provision, publish, or touch
Production. Resume restores only the formerly running source/selection and
then reads Cloud once; a failed Cloud read can be repeated without replaying
startup. Pending/uncertain updates prevent Park before shutdown begins.

Repeated completed `demo create` and `demo prepare` perform one focused
readiness observation instead of trusting the recorded phase. Create reads
Test SSH/DNS and the two owned backend processes; Prepare also reads the local
controller/remembered selection and Cloud inventory. No hashes/extraction,
enrollment, factory-role writes, restart, provisioning or publication are
repeated. `readiness` carries timestamped observations and CURRENT/INCOMPLETE;
it is not product qualification or a newly proven guest-source connection.

### Component artifacts and Test delivery

`democtl component cloud-status` without a version reads a focused Cloud-only
Test overview (Unit status and VDP release catalog). The Platform UI uses this
same application operation on tab entry. It never probes the guest, scans all
Units or reads Production for this overview. A version argument retains the
existing detailed release observation. Cloud Installed is not evidence of a
running process, telemetry READY or the functional v1/v2/v3 content mapping.

Repeat a demo with new Cloud releases and explicit frozen content profiles:

```sh
democtl component prepare 4.0.0 --profile v1
democtl component sign 4.0.0
democtl component upload 4.0.0
democtl component cloud-status 4.0.0
democtl component status test
# After seven-signal READY, repeat for 5.0.0 --profile v2 (15 signals),
# then 6.0.0 --profile v3 (23 signals).
```

Profiles use pinned signed 1.0.16/2.0.0/3.0.0 contents. Cloud release numbers
are separate and must increase; later cycles can use 7/8/9 or higher. Only
seven allowlisted metadata files may differ. Application code/dependencies
remain unchanged except the selected profile's VERSION/MANIFEST_SHA256
constants and package version. Signed provenance records the content profile,
source-bundle SHA and current Factory identity. Candidates may be prepared and
signed locally in advance, but publication is sequential. Before Provision a
previous Ready publication may be superseded by the next profile; with a
provisioned Test, the previous version must be installed and no update pending
or failed. No deletion,
reprovisioning, old-version force-send or automatic Production promotion occurs.

Known .29 runtime defect observed on the first 4.0.0 replacement: the native
launcher immediately starts the successor while the custom runtime's stop
worker is still removing the predecessor. Start fails with
`a different component transaction is already active`; the stack automatically
retried about ten minutes later and 4.0.0 became READY. Do not equate Cloud
Installed with runtime readiness, manually resend, or report this delay as
normal CLI/API execution time. The [qualification record](../../docs/qualification/democtl-vdp-family.md)
preserves the timeline and remaining runtime defect.

Temporary v3 platform proof (operator-authorized 2026-09-06): while no vehicle
is selected, `component schema-apply test` adds only the eight accepted
ChaosWheel sensor leaves to a copy of the base KUKSA schema in
`/run/democtl-vss/vss.json`. An owned runtime drop-in at
`/run/systemd/system/kuksa-databroker.service.d/90-democtl-vss.conf` binds that
file read-only over the existing schema **inside KUKSA's mount namespace**.
One KUKSA restart loads it. The original schema, ExecStart, TLS/JWT inputs,
permissions, Factory image and Production are unchanged. Repeating a confirmed
application is a no-op. A failed application restores the base binding;
uncertain outcomes are recorded and require reconciliation, not blind retries.
`component schema-remove test` restores the base service and deletes only those
owned temporary files. Reboot also removes this `/run`-only configuration.
`component diagnose test` reads the running service's namespace and reports
the effective/base digests and missing leaves. This is a temporary Test proof,
not a repaired Factory image or full v3 advisory qualification.

`component list` lists VDP versions in
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/components/vehicle-data-provider`.
`inspect VERSION` reads the qualified producer's JSON-in-YAML deployment
envelope and payload, reports their digests and inner/outer/profile version
coherence, runtime binding, media type and capability digest. It is read-only:
signature presence is **not** cryptographic verification, and packaging
inspection is not runtime or Cloud qualification. Other YAML producers are
not silently interpreted as this producer's schema.

`unpack VERSION` extracts validated regular payload files into that exact
version's `unpacked` directory. Files are owner-only, non-executable inspection
copies. It rejects links, path traversal, oversized expansion, duplicate
members and an existing destination; it never overwrites a previous unpack or
creates a backup. The signed bundle remains unchanged. CLI and local API use
the same core; callers cannot choose arbitrary paths, credentials or URLs.

Without `--profile`, legacy `prepare VERSION` supports the original `2.0.0`
and `3.0.0` telemetry candidates; repeated demos use the explicit-profile form
above, with a new release number.
It composes the pinned Platform release source with ARM64 dependencies from the
cryptographically verified, qualified 1.0.16 bundle. It does not download wheels,
start a Builder or rebuild the VM. It checks 15/23 exact manifest paths, metadata
coherence and repeatable payload bytes, and refuses to overwrite a candidate.
`sign VERSION` uses the installed official Aos signer and configured OEM
credential; `verify VERSION` verifies RS256 plus all signed member hashes and
matching inner/outer config against that credential's certificate.

`upload VERSION` sends the signed archive to **deployment-bundles/upload/**,
not component upload. It checks the prepared profile, signed bytes, increasing
release, Factory receipt/catalog compatibility, OEM ownership and complete
verification-recipient coverage. No guest read is needed. New publication uses
explicitly prepared profile-replay releases (4.0.0 or higher); the frozen
2.0.0/3.0.0 artifacts remain replay inputs, not new release numbers.
HTTP 201 means `publication.stage=ACCEPTED`, not Ready. `cloud-status VERSION`
reads the exact recorded bundle through documented pagination and the matching
catalog version. Error preserves sanitized `build_info`; neither error nor
processing becomes a successful `noOp`. A repeated `upload VERSION` only
reconciles that exact response ID and never uploads again. Response loss without
a known ID blocks resubmission. `approve`/`unapprove` remain explicit engineering
operations for existing VDP/arm64 verification batches, not steps in the current
Test flow. None of these operations promotes to Production.

`component status <test|production>` reads the active slot, coherent installed
metadata, matching running process configuration, systemd result/restarts and
provider-reported data readiness over pinned SSH. The read-path count is the
active manifest count; READY means the provider reports a fresh complete frame
after publication to KUKSA, **not an independent KUKSA consumer-read proof**.
`component logs <test|production>` returns bounded, redacted per-service
SM/CM/provider/self-test events, including binary journal messages, with repeated
provider READY events aggregated. It does not return raw message bodies or secrets.
`component diagnose <test|production>` compares the fixed 23-path family contract
with the installed KUKSA schema, reporting present leaf types and missing names.
It changes no schema, credentials or permissions. Factory .28 currently lacks
the eight v3 ChaosWheel leaves, so v3 telemetry is not qualified on that image.

Move to the next content profile only after the preceding release is active
and ready. This run
qualifies telemetry only: v3 advisory and client-authenticated write roles remain
deferred; Gateway Set is still rejected. The current
[VDP family checkpoint](../../docs/qualification/democtl-vdp-family.md)
records actual results and exclusions. No standalone workflow scripts are used.

The agreed preparation interface keeps operated-on VMs separate from the one
live consumer:

```text
democtl environment prepare --target all --current test
democtl environment prepare --target all --current production
democtl vehicle select production
democtl vehicle select test
```

`--current` is explicit and never `all`; the selected role must be among the
prepared targets. Both VMs may remain Cloud Online, but only one receives live
CARLA/Gateway data. Switching requires Safe Stop, confirmed detach and scene
reset; selecting the already attached role is a confirmed no-op.

Selector validation is implemented in the CLI and shared application/API:
missing/plural current roles and target/current mismatches are rejected before
lifecycle actions. The existing Controller now provides the authorized
Safe Stop/reset interlock without taking the native keyboard session. Source
switches use that Controller, not a second CARLA controller. Public run-scoped
VM inputs and an exact guest VISS gate connect only one role; both Cloud
identities remain unchanged. A failed or uncertain switch retains its intent
and blocks further attachment pending reconciliation. See Demo Control for
the transport and separate live-acceptance record.

For this local demo the operator has
[deferred per-Unit VISS client mTLS](../../docs/architecture/demo-control.md#local-demo-amendment-defer-per-unit-viss-mtls).
The explicit `LOCAL_DEMO_SERVER_TLS` profile retains server TLS verification
and actual single-VM connectivity. It does not alter AosCloud provisioning or
claim strict mTLS qualification.

`simulation start` starts CARLA, Controller, Gateway and the associated UI,
without booting/provisioning VMs or selecting a vehicle. Existing VM source
paths are blocked before startup. A fully ready repeat is a no-op.
`simulation stop` performs Safe Stop, confirms detachment and gracefully stops
that owned group; VMs and Cloud identities are preserved. Repeated stop is a
no-op. If the Controller has already exited, physical stop is reported as not
observed rather than fabricated. No automatic forced kill or backup is used.

Use `vehicle select test|production` after startup. A missing simulator returns
`SIMULATION_NOT_RUNNING`; a not-ready Controller/Gateway returns
`SIMULATION_NOT_READY`, without implicit startup or startup waiting. Selection
uses provisioned local bindings, not a full Cloud inventory; `status --cloud`
provides live Cloud observations. `environment prepare` composes the same
primitives. Use simulation commands for operator and engineering startup/stop.

Current visual limitation: the runner's terminal telemetry dashboard is active
but its output goes to the private run log. Unlike the old desktop launcher,
this command does not yet open a visible dashboard Terminal window. CARLA and
the keyboard-control window do open; dashboard presentation remains unfinished.

Ordinary `democtl status` quickly shows `CARLA selected VM` and the timestamp
of its last connection confirmation, with fresh local Controller/runtime facts.
It makes no SSH or Cloud calls and does not claim the saved connection is live.
`status --guest` reads guest gates/VDP and verifies two advancing VISS frames
through the selected guest with server TLS under a bounded source read budget.
Blocked peers are checked by their gate, not an expected connection timeout.
`status --guest --cloud` additionally reports fresh Cloud state.
VDP process health and its reported data readiness are separate;
an inactive baseline provider is not reported as a running VDP data chain.
The [live source-selection record](../../docs/qualification/democtl-source-selection.md)
separates CLI observations, automated fixtures and deferred lifecycle checks.

Status returns timestamped `OBSERVED` or `PARTIAL` results, not the former
package-only `READY`. Neither result is a demo-readiness or qualification claim.

The audience-facing target `test` maps to the accepted technical role
`VALIDATION`; `production` maps to `PRODUCTION`. Local creation uses the accepted
.run/demo-current/journal.json contract; single-role use is engineering scope,
not complete-demo qualification.

## Image Discovery and Local Creation

~~~text
democtl image list
democtl environment create --image 6.1.1-maninblack.27/main-qemuarm64 --target all
democtl status
~~~

The selector comes from the existing demo-artifacts/aosedge-sdv-demo catalog
(or DEMO_ARTIFACT_ROOT). No manual YAML or image registration database is
required. Listing reads published metadata and file attributes, not image
contents. A selector never implicitly chooses latest. --image-path currently
accepts only an exact catalog image with published metadata; arbitrary external
paths are not yet supported. Missing/conflicting manifests block creation.

create makes ONE independent read-only copy in .local/factory. Raw keeps its
bytes and SHA at oem-demo-factory.img; qcow2 uses oem-demo-factory.qcow2. Both
requested overlays in .local/demo-current use this local copy, not the original
artifact-store file. Copying is not conversion or a VM rebuild. A same-digest
retained factory copy is verified and reused, never overwritten. Distinct local
VM identities and planned SSH endpoints (test 10022, production 10023) are
recorded; endpoint availability must be established by the later prepare step.

Prerequisite: qemu-img installed. The existing repository image-work guard
requires at least 60 GiB free before making a new factory copy. There is no
automatic disk cleanup or override. SHA verification occurs at this creation
trust boundary, not in image list or status.

COMPLETED means only that the requested disks were manufactured locally. It
does not mean booted, provisioned, Online, CARLA-connected or demo-qualified.
No Cloud identity is assigned; Current Vehicle remains unset. No backup is made.
The original image and existing experimental VMs/Cloud Units are untouched.

Existing run state or overlays block a second create. Partial results and
unfinished writes are retained as RECOVERY_REQUIRED; no automatic rollback,
deletion or blind retry occurs. Failed-create recovery and full Cloud retirement
are not yet implemented, so this increment is not a complete demo lifecycle.

Default status uses the newly created journal's exact disk bindings, with no
inherited legacy Unit IDs or SSH credentials. The old observation configuration
is preserved. Explicit status --config selects a separate diagnostic binding.
The transport-neutral API accepts catalog selectors, not caller-selected paths.

Create exits 0 on COMPLETED and 1 on BLOCKED; image list exits 0 for an observed
catalog or 1 for metadata-read issues. All results support global --output json.

## Start and Stop Created VMs

~~~text
democtl vm start test
democtl vm start all --timeout 90
democtl status --guest
democtl vm stop test
democtl vm stop all
~~~

These commands operate only on the overlays recorded by environment create.
They never create/rebuild an image, provision a Unit, call Cloud, launch CARLA,
change Current Vehicle, or make a backup. The selected image is inherited from
create, not supplied again. all means every role actually created.

The initial runtime profile is aos-main-qemuarm64-v1: macOS ARM64/HVF,
virt-11.0, two CPUs and 2 GiB per VM, QEMU 11.0.3 or 11.1.0, pinned firmware
from .cache/aosvm/v6.1.0/qemuarm64/QEMU_EFI.fd. Image versions are not hard-coded;
only the main-qemuarm64 variant is supported by this first profile. A compatible
profile is not a production-qualification claim for every image in the catalog.

start directly launches QEMU and one shared owned host DNS service on loopback
port 18053; it reuses matching running processes, never duplicates or adopts a
foreign one. SSH ports are 10022 (Test) and 10023 (Production). The guest image
must already contain its correct network/DNS configuration; start does not patch it.
It waits for QMP Running, authenticated SSH and guest DNS, with a default
90-second wait budget per VM (1–300). This is a ceiling, not a mandatory wait;
cold .27 boot plus initial SSH enrollment exceeded the former 60-second ceiling.
For all, both processes launch before readiness checks, so their boots overlap.
It reports each VM separately, with duration excluding interactive password entry. Running
without SSH/DNS readiness is PARTIAL, not COMPLETED or Cloud Online.

First SSH enrollment requires an interactive CLI terminal and an explicit
guest root password prompt. It creates a per-VM key, installs its public key
over the owned local serial console, and pins the guest's public host key from
that console. Host-key paths come from sshd's effective configuration, including
the -f option in /etc/default/ssh used by the readonly guest. No fixed /etc/ssh
host-key path is assumed. Before login, the console prompt is requested again
after boot if the initial Enter preceded getty readiness. Login/password are
never blindly resubmitted, and fixed progress stages identify any timeout.
The password exists in memory only, is never discovered from
legacy scripts, and is not accepted in command arguments, API requests or the
journal. Subsequent starts use the enrolled key without prompting. With no
interactive password and no enrollment, the VM can start but reports
SSH_ENROLLMENT_REQUIRES_INTERACTIVE_PASSWORD; rerun start from an interactive
terminal. Access files live in .run/demo-current/test-access or production-access.
Guest DNS uses the installed BusyBox nslookup with a two-second query bound;
getent is not present in this factory image. No DNS configuration is changed.
The CLI prints the exact SSH command after successful enrollment/readiness.

stop requests guest poweroff over SSH, or QMP system_powerdown if SSH is
unavailable. It waits for the owned QEMU process to exit and release its disk.
There is no automatic forced kill. Disks, keys and identities are retained;
stopping the last managed VM also stops its owned DNS service. An already
stopped VM is a no-op. A Current Vehicle must first be detached/parked through
the corresponding lifecycle operation; stop does not hide that transition.
Those higher-level operations remain unimplemented in this slice.

The current-run journal records process ownership and interrupted operations.
Explicit retries re-observe process ownership first. An unresolved operation
covering another role must be reconciled with the same targets or all before
starting an unrelated role. No background retry loop or automatic rollback runs.
Fixture tests are not live qualification. The separate
[operator-equivalent CLI acceptance record](../../docs/qualification/democtl-local-vm-lifecycle.md)
documents actual runs from this directory, including cold start, immediate
stop/start without a password, one-role stops and retirement/recreation.

## Provision and Retire Cloud Units

From this directory, with the virtual environment activated:

~~~text
democtl vm start all
democtl unit provision all
democtl status all --guest --cloud --profile oem-delivery --timeout 30
democtl unit deprovision all
democtl unit delete all
democtl status all --cloud --profile oem-delivery --timeout 30
~~~

Each unit command also accepts test or production. all operates on the created
roles in Test-then-Production order, with serialized SDK/identity mutations;
it does not mean concurrent provisioning. Each role has its own result and
duration. The CLI and local API use the same UnitService implementation.

- provision requires an already-running, SSH-enrolled, DNS-ready VM. It reads
  its actual system/model/Main Node identity, invokes the official protocol-v6
  SDK once, waits for Cloud Online and guest normal mode, then adds only that
  systemUID to the role set. Test Vehicles must be a verification set;
  Production Vehicles must not. Both must belong to the same fleet. The OEM
  owner and resolved set UUIDs are pinned in the current journal. Other Units
  in a selected role set block the command; they are never automatically removed.
  An already provisioned current Unit is observed/reused without another SDK attempt.
- deprovision stops the selected guest's CM, waits for authoritative Offline,
  performs Cloud deprovision once, reads new/Offline, then stops the exact VM.
  It does not restart CM with old credentials or test identity revocation;
  that is Cloud's responsibility. No certificate is extracted. The initial
  CM disconnect still observes its stock systemd stop limit when needed.
  There is no forced VM kill or systemd timeout change.
- delete requires that deprovision proof and a stopped, released overlay. It
  removes only the current systemUID from its exact role set, deletes the Unit,
  and confirms Unit/Node absence with independent authenticated inventory
  visibility. Persistent role sets and Cloud campaign definitions are retained.
- These commands retain local disks, the factory copy, access keys and journal.
  They do not launch CARLA, sign/upload VDP or rebuild an image. After deletion
  the retired overlay cannot be provisioned/started as a fresh Unit. Full
  scenario retirement remains a separate, unimplemented slice. For this
  CLI-only lifecycle, environment retire can now remove the retained local
  files after fresh Cloud-absence proof, as described below.

The host requires its existing oem-delivery PKCS#12 and Aos SDK environment.
No credential enrollment or permission modification happens automatically.
The pinned SDK 5.4.2 start/finish transition correction is reused as a library,
not by invoking the former VM/checkpoint/provisioning workflow. IAM forwarding
is temporary and loopback-only (Test 18089, Production 18090 to guest 8089).

Cloud mutation intent is recorded before submission. A lost response returns
PARTIAL; an explicit subsequent command reconciles the exact recorded identity
and resumes only a proven applied step. It never blindly resubmits an SDK or
destructive request. Completion is confirmed external state, not merely HTTP
success. Exit 0 means every selected role completed; exit 1 means blocked/partial.

See [Unit CLI acceptance](../../docs/qualification/democtl-unit-lifecycle.md)
for actual runs and their precise qualification limits.

## Clean Up an Unprovisioned Created Environment

~~~text
democtl environment retire
~~~

The same command also accepts an already Cloud-retired CLI-only run. First run
unit deprovision and unit delete for every provisioned role. retire does not
perform these Cloud mutations implicitly. It requires the recorded rejection
proof and new authenticated Unit/Node/systemUID absence and empty role-set reads,
including on an interrupted-cleanup continuation. Cloud unavailable/denied or
any remaining identity means no local file is removed. It then uses the same
owned-file cleanup below: overlay/access files, working factory copy/manifest,
journal last. The original artifact remains. This extension does not cover a
run that used future CARLA/scenario/backend operations or claim complete R0.
Its JSON scope is CLOUD_RETIRED_CLI_RUN, with cloudReadsPerformed=true and
cloudActions=false (no Cloud mutation). No backup is made.

For new verification-Test uploads left at RESPONDED/HTTP 201, retire reconciles
the owned deployment ID and matching Ready catalog version without a batch or
approval. Processing/error/missing proof remains unresolved. For historical
engineering uploads, retire can reconcile the exact recorded deployment and
confirmed verification batch through read-only Cloud
requests. It confirms the completed bundle's component/version and the batch's
OEM/component/architecture/version; it never uploads or approves again. Unknown
IDs, mismatched or unavailable proof and unresolved approvals still block local
deletion. This confirms publication only, not the former Production snapshot.

This implements the inverse of a successful local create, including a booted
but proven unprovisioned VM after democtl stop. It permanently removes the exact
role overlays and generated host access keys, then the local factory copy
and its manifest, empty owned directories, and finally the journal. There is no
backup. It preserves the original demo-artifacts image and published manifests,
legacy observation configuration and all unrelated VMs/files/Cloud objects.
The tiny writer.lock remains to keep concurrent-writer exclusion stable.

No target or force option is accepted: all roles present in this current
environment are retired together. A single-role create has only that role to
remove. Afterwards create can be run again: it makes a new factory copy from
the original artifact and generates fresh overlays and local identities.

For the unprovisioned path, cleanup requires a successful create, no Unit/Node/Unit Set identity, no
Current Vehicle and released files. Never-started overlays must have no
guest-owned extents. For a booted VM, stop must have observed provisioning mode,
absent provision-state/PIN files and inactive normal-mode Aos services immediately
before poweroff; it binds that observation to the stopped overlay's SHA-256.
retire requires that same digest. An unobserved/provisioned guest or an externally
modified stopped disk has no valid local deletion proof. No secret file is read.
The command does not boot/stop VMs, contact Cloud or run deprovisioning.
qemu-img and lsof are required. A running/open, unproven, symlinked, untracked,
or uncertain target blocks deletion. All remaining targets are checked before
the first deletion, including open handles on the factory copy and manifest.
The original artifact is never a deletion target. Factory metadata is checked;
the factory image is not recopied or rehashed by this local-only cleanup.
Only booted overlays with a stop proof are hashed to validate that proof.

Compatibility: when an older retire has already removed overlays and journal,
this command also removes its remaining factory copy/manifest, after verifying
the exact democtl producer manifest against the original catalog entry. It
records factory-only deletion intent in the same current journal; arbitrary
or unbound leftovers remain blocked. No recreate step is necessary.

No current environment or retained factory copy is a successful no-op. If deletion is interrupted,
the RETIRING_LOCAL journal records each exact file before unlink. A repeated
retire reconciles an already-absent file and continues with remaining files;
it never repeats a proven deletion. Corrupt or incomplete atomic journal
writes remain blocked for explicit recovery. Status shows interrupted cleanup
as requiring recovery. This is NOT full Cloud/scenario R0 or a READY_FOR_M0
qualification claim. Exit codes: 0 completed/no-op, 1 blocked.

## Status Options and Results

Without flags, status reads only local configuration, overlay presence, exact
matching QEMU processes/QMP and credential availability. Default target: all.

- --guest adds one non-interactive SSH read per running VM for release,
  configured Aos services/restart counts and guest DNS. It also queries the
  configured loopback DNS bridge. Stopped VMs skip SSH. Existing host keys are
  required; no key enrollment or host-key acceptance occurs.
  On managed VMs it also observes the provisioning-port connection-state names
  through read-only QMP; --details displays these without exposing the raw table.
- --cloud performs separate authenticated OEM/SP reads, including certificate
  validity, actual role, owner ID and effective permissions. Only the
  oem-delivery context reads exact configured Units and their memberships.
- --profile NAME --cloud selects one configured context from the local CLI.
- --details adds effective permission names and expanded Unit/service fields.
  JSON always contains the structured observations.
  CM diagnostics project bounded current-boot startup stages, existing journal
  backtrace symbols and fixed gRPC assertion codes. They do not read a core dump
  or export message/credential payloads. The running CM executable's supported
  --version output and executable digest are observed without restarting the
  service; unavailable fields remain empty, not a guessed version.
- --timeout SECONDS sets a per-probe budget (default 8; range 0.2–30).
  Each Cloud context shares its budget across authentication and Unit reads,
  with a 0.5-second exit allowance and up to 2 seconds for timeout cleanup.
  Independent guest/Cloud reads run concurrently. There are no retries.

Exit codes: 0 means observations completed, **not** “the demo is healthy”;
1 means partial/unavailable observations or invalid configuration; 2 means
invalid CLI usage or an unimplemented mutation. An observed stopped VM or
Offline Unit is not, by itself, an error.

### Local Observation Configuration

The default is .local/demo-control/status.json in the Solution checkout.
It is Git-excluded operator configuration, not a new journal or history store.
Status only reads it. --config PATH selects another local file; relative
artifact/access paths inside it resolve from the Solution checkout.

A local binding to the retained test .27 has been prepared on this development
host; Production is explicitly unconfigured. No overlay was moved or copied,
and .27 is not a code default. Example of the configuration shape:

~~~json
{
  "schemaVersion": 1,
  "vehicles": {
    "test": {
      "overlay": ".local/demo-current/validation.qcow2",
      "accessRoot": ".local/validation-host-access",
      "sshPort": 10022,
      "dnsPort": 18053,
      "cloudHost": "aoscloud.io"
    },
    "production": null
  }
}
~~~

Optional vehicle fields: imageVersion, imageSha256, unitId, unitSetId and
services (a bounded list of systemd service names). Image references are
labelled configured, not verified; no factory-image hashing occurs. Without
unitId the Unit read is explicitly skipped. Without unitSetId, memberships
are observed but an expected-membership match is not claimed.

Without a configuration file, the accepted canonical overlay paths are used;
SSH access and Cloud Unit identities are not guessed.

Default Cloud profiles are oem-delivery and service-provider, referencing
~/.aos/security/aos-user-oem.p12 and aos-user-sp.p12. Their actual API role
strings are "oem" and "service provider". Optional cloudProfiles replaces
this mapping: each named entry has credential, expectedRole and optionally
expectedOwnerId. Separate configured SP1/SP2 contexts can be added without
inventing an account or pooling its permissions with another context.

Cloud reads use the existing ~/.aos/venv/bin/python3 Aos SDK environment;
cloudPython may select another installed local environment. Nothing is
installed automatically. Only unencrypted, privately permissioned PKCS#12 files
are used. SDK temporary key/certificate files are deleted before network reads.
TLS uses the SDK root CA; redirects, proxy-environment routing and TLS bypass
are disabled. Raw responses, keys, certificate content and the users/me token
are never returned.

### Current Limits

Each observation carries source, readCompletedAt, sourceTimestamp when
available, read state, transport classification and a fixed error reason.
There is no persisted observation cache. Missing/denied reads do not prove
Cloud-object absence. The API adapter uses the same application core but is
not an HTTP server or an authenticated UI session implementation. It rejects
caller-selected paths, credentials and profiles.

Guest mode is inferred from the observed IAM/SM/CM service states. Active
services do not prove the AosCore-to-Cloud connection: that field remains
NOT_OBSERVED. The journal reader supports the implemented manufacture/VM/Unit slice,
not future full-scenario recovery schemas or a history store. This slice
derives neither overall demo readiness nor Cloud mutation authority.

## Installation

The existing editable installation picks up these source changes; reinstalling
is not necessary. For a new installation, follow the commands below.

From the Solution repository checkout, install into a local Python environment:

```bash
cd apps/demo-orchestrator
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --editable .
source .venv/bin/activate
democtl --help
democtl status
```

The installer reads `pyproject.toml`; that file is not an executable. Editable
installation uses the source files directly, so ordinary code edits do not
require reinstallation. The first installation downloads packaging tools.

In a new terminal, enter this directory and run `source .venv/bin/activate`
again. Alternatively, use `.venv/bin/democtl status` directly without activation.

## Development

### Factory .31 build

`democtl image build 6.1.1-maninblack.31` uses pinned Platform main
`0bed8b3769b09fbe685ed599ca8d10e6594fbe53` and the existing warm Builder.
It runs five ARM64 factory-placeholder/input/profile regressions before
SM package QA and image construction, reuses the existing Rouge layout, then
exports a new immutable catalog image and stops Builder. It does not publish
components, provision Units or modify Production. A completed build means
`BUILT_NOT_LIVE_QUALIFIED`, not E2E acceptance. Existing artifacts are never
overwritten by repeating this command. Downloads and shared-state caches are
retained; generated artifacts stay outside Git.

For an existing image, `democtl image build 6.1.1-maninblack.31 --metadata-only`
registers its source-derived VDP compatibility declaration in the producer
manifest. It requires the exact clean source revision and owned immutable
catalog binding. It never starts Builder, checks build disk space, rebuilds or
changes image bytes or qualification state. Missing artifacts or conflicting
metadata fail closed; an identical repeat is a noOp. This explicit migration is
not performed implicitly by `image list`, status or component upload.

Factory .31 retains .30's persistent public source-input configuration. `vm start`
initializes the explicit role before provisioning; source selection writes
public CA/bindings without restarting SM. The role stays in runtime data;
only Test selects `demo-5s`, and an empty Factory/Production uses `standard`.
No private keys, role assignment or captured vehicle data are baked into the
image. Existing .29 transient qualification commands remain separate.

### Test-only SM qualification

The 2026-09-06 local-demo exception is documented in the
[Safe Stop contract](../../contracts/platform-fota-safe-stop/README.md) and
[VDP checkpoint](../../docs/qualification/democtl-vdp-family.md). In the isolated
Test qualification environment, `component sm-build test` starts the existing
Builder on port 10024, compiles only SM, runs native timing, role-selection,
physical-gate, stop and queued cold-boot recovery regressions, exports the proof
artifact and stops Builder.
`component sm-test test` reruns those tests on the existing
compiled target without compiling again. Test failures retain their output.
`component sm-builder-stop test` is the explicit graceful stop.

The current authorized target is Test .31, local VM
`d53d05cd-4c46-49c9-a896-534b23b88273`, Unit
`2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, with the existing immutable .31 SHA.
Proof sources are pinned to Platform commit
`7f168e9bd5338dd9320ebbd6fe0f6043fcc1eb65` in a separate Builder source directory.
The artifact is `demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-queued-recovery`;
the earlier timing-only proof is retained separately.

`component sm-apply test` applies only that binary through a temporary systemd
mount and one stop/start, preserving the Factory configuration and public inputs;
`component sm-status
test` observes the effective binary and profile. These are bounded qualification
commands, pinned to the authorized Test .31, not general release deployment.
They do not modify the immutable Factory image, Cloud or Production; the
temporary substitution disappears at VM reboot. The normal default remains
250 ms. Test alone admits signed age ±5000 ms and a 1000-ms read deadline.
No VDP update is implied by SM application.

For this exact authorized Test recovery only, application validates the existing
17.0.0 slot-b installation, matching queued remove transaction, slot record and
capability digest before and after stopping SM. It restores a missing
`active -> slots/b` selector without overwriting another selection or rewriting
durable JSON. The corrected native runtime starts the saved provider and resumes
the existing transaction with fresh Safe Stop evidence. An intentionally stopped
predecessor, changed transaction or foreign selector is rejected. A repeated
application to the already active proof binary performs no restart. This is not
a general missing-selector repair policy, Cloud retry, or new VDP publication.

After Park/Resume of this same qualified Test, the same command may reapply the
previously confirmed proof to committed **18.0.0 / slot a**. It requires the
existing active selector, exact installed/slot metadata and capability digest,
with no transaction or intentionally stopped marker. It never repairs a missing
selector in this case. This is a separate explicit qualification operation,
not an automatic Resume step; a clean factory image still needs the source fix.

The package uses Python 3.9 and the standard library. Optional Cloud reads use
the separately installed Aos SDK environment. Fixture tests do not contact
Cloud or modify an existing VM. The QMP fixture binds a temporary Unix socket.
Creation integration tests use qemu-img and temporary 1 MiB raw images; these
tests are skipped when qemu-img is unavailable.

```text
PYTHONPATH=apps/demo-orchestrator/src \
  python3 -m aosedge_demo_orchestrator --help

PYTHONPATH=apps/demo-orchestrator/src \
  python3 -m unittest discover -s apps/demo-orchestrator/tests -p 'test_*.py'
```

Installing the package creates the `democtl` console command through the
`pyproject.toml` entry point.
