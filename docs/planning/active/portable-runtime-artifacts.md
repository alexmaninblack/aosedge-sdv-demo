<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable Runtime Artifact Work Packet

- Status: In progress; local engineering candidates only.
- Prepared: 2026-09-26.
- Owner: Integration, with existing component owners unchanged.
- Accepted parent: [Installable distribution plan, Stage 2](installable-distribution-and-reproducibility.md).
- Input: [Stage 0 inventory](../../research/distribution-stage0-inventory-2026-09-25.md)
  and [qualified simulator](../../qualification/standalone-carla-stage1-2026-09-25.md).

## Scope and change classification

The initial slices assemble private, non-installed native and Python runtime
candidates from explicit inputs and their dependency closure. The subsequent
packaged-preparation slice below adds an opt-in input selector to existing
Prepare operations; the host-launch slice selects prebuilt inputs for the
existing source/workspace owners. These slices do not change launch ownership, VM state, package
signing, service wire contracts or release-number allocation. The working demo
remained on its development inputs during isolated qualification. The ordinary
simulator/native-host selection has now been switched as recorded in the final
checkpoint below; complete VM/backend/Cloud-worker migration remains open.

Before changing operator Prepare, SourceDriver, VM selectors or first-use
behavior, update the relevant accepted contracts and tests as required by the
[documentation policy](../../governance/documentation-and-requirements-management.md).
This work packet is not a second orchestrator or final installer specification.

### Packaged preparation selector slice — 26 September

Change class B: realize Stage 2's source-independent Prepare using the existing
artifact catalogue, writer, allocator and signing/publication flows. The
[portable-input contract](../../../contracts/portable-preparation-inputs/README.md)
freezes the opt-in directory, independent release-source lock, fail-closed
selection, no developer fallback and pre-allocation integrity gate. This slice
does not yet switch native application, simulator, backend, VM or Cloud-worker
launch selectors. No new state root, launcher or installer is introduced.

Affected: VDP source/common-runtime readers, no-build service selection and
preparation tests. Revalidated unchanged: ADR 0016 signing/authority, operator
scenario/flows, orchestration requirements and existing version continuity.
Preserve the ordinary developer path when no packaged inputs are selected.
Qualify the real composition path against an isolated release-catalogue fixture;
never present the fixture as live Cloud evidence or consume the user's ledger.

### Packaged host launch selector slice — 26 September

Change class B, governed by the [host launch contract](../../../contracts/portable-host-launch/README.md).
The existing artifact catalogue selects a separately locked `host-runtime`
closure. SourceDriver, WorkspaceService, Presenter HTTP and strict local trust
consume prebuilt hosts/web assets, private Python/OpenSSL/Gateway and the
qualified standalone Game. No new process owner, port, state root or credentials
store is introduced. Absence retains the developer path; invalid presence
blocks. Full dependency inventories reject undeclared importable files and links
before execution, not just changes to known binaries. The unchanged caller
still supplies its existing operator server-TLS reference.

Required controls include no compiler/Editor fallback, unchanged ownership and
idle guards, first/repeated start, private callback entry, live detached local
telemetry, exact window layout/ordering and normal stop. This slice does not
qualify a packaged guest, Cloud enrollment or an installer. Preserve existing
Test/Production and their native Presenter while testing an isolated app tree.

## First slice: native dependency closure

### Complete application export — 26 September continuation

Live qualification exposed a corrective input defect: the historical native
inventory selected a pre-QM Gateway/client pair. Preserve that evidence, verify
the current warm build and six protocol/security suites, then replace only
those small native inputs and their manifests. Add a pre-advisory rejection
gate, preserving all existing trust roles and wire contracts. Rebind the small
VM manifest to the successor host pin; do not rebuild CARLA, Factory or services.
Use normal stopped-owner handoff and retain both previous artifacts and Unit
identities. Fresh local advisory/backend proof is required before closing this
packaging defect. No architecture, model or permission change is authorized.

The final HTTP restart exposed a separate response-cancellation defect:
client disconnection during monitoring output was caught as an observation
failure and caused a second response attempt. Prove it with a disconnected
writer fixture, then terminate only that response on BrokenPipe/ConnectionReset.
Preserve genuine observation errors, action execution, idle guards and all
status semantics. Re-export application source after the targeted regression;
no native host, guest, simulator or backend rebuild is part of this correction.

Build/evidence-only realization of the accepted Stage 2 assembly. Export the
current tracked orchestrator Python files plus the six explicitly reviewed
selector/entry modules, the runtime JSON contracts and five independent locks.
Include only the existing public launcher-path configuration and license; never
copy operator configuration, credentials, journals, overlays or ledgers. Reject
an unreviewed Python module or unresolved relative import instead of producing
an incomplete application. Record working-source byte hashes, not just HEAD.

Bind the five existing immutable input groups into a separate workspace using
the existing catalogue layout and APFS clones (no full-copy fallback). Verify
manifest pins, exact inventories and transferred bytes. Expose Factory .39
through the unchanged image catalogue using a read-only APFS clone. This extra
logical path shares image blocks; it is not a rebuild or a full physical copy.
No new launcher, state root, product interface, installation or credential store
is introduced. External prerequisites, TLS/first-use setup, redistribution and
clean-Mac qualification remain explicit open gates.

Use the existing private `host_entry.py` for relocated CLI/import/contract
checks with development-source reads denied. This isolated empty-state proof
is not a live run. After assembly, qualify packaged dependencies through the
existing live owners while retaining the current state root and Test/Production
identities. Do not copy a provisioned workspace into the distributable artifact
or label preserved-run qualification as a clean installation.

### Cloud/backend selectors — 26 September continuation

Class B, governed by the [portable Cloud/backend contract](../../../contracts/portable-cloud-backend-inputs/README.md).
Connect existing workers and backend candidate readers to independently locked
assembled inputs. Preserve configured developer behavior when absent, strict
failure when invalid, current backend records and all authority/lifecycle gates.
Do not implicitly load images or start Docker. Validate Cloud dependencies at
worker dispatch, not during UI configuration. Reuse the existing artifacts;
no operator credential, current runtime or Cloud object is part of these tests.
Complete application assembly and live qualification follow this source slice.

### VM/image/DNS input selector — 26 September continuation

Class B, specified by the [portable VM contract](../../../contracts/portable-vm-launch/README.md).
Reuse the existing host native/Python closure; assemble only firmware, the
unchanged DNS helper and its license in a separately locked small bundle.
EnvironmentService and VMService remain the owners. No guest/runtime behavior,
IDs, ports, model thresholds or security checks change. A packaged helper has
one interpreter-independent command; current legacy owners are not adopted.
Preserved-owner handoff and real lifecycle validation remain separate gates.

The operator explicitly deferred further live-screen checks until assembly is
complete. Continue unit/static/integrity gates, then remaining backend/Cloud
selectors and complete application assembly. Do not restart current Docker,
Test, CARLA or native panels to close interim screen symptoms. Current findings
remain in the [deferred validation record](../../qualification/distribution-deferred-live-checks-2026-09-26.md).

Inputs are existing arm64 QEMU 11.0.3 executables and Gateway/VISS-client
binaries from the frozen inventory. Resolve transitive libraries, copy only
the required files into an exclusive candidate, replace development-prefix
load commands with package-relative paths, and preserve existing entitlements.
Sign modified candidate bytes locally/ad-hoc, without changing original files.
Record source/output hashes, library graph, OS load paths and preserved rights.
Copy available dependency notices; unresolved redistribution/source-offer
review remains a blocking gate for external distribution.

Reject missing libraries, external/unresolved relative dependencies, non-arm64
inputs, name collisions, existing outputs and insufficient disk before copying.
An interrupted candidate is evidence, not a successful artifact; never overwrite
it or fall back silently to Homebrew. Full dynamic plugin/data closure is a
separate functional gate, not established solely by Mach-O inspection.

Verification order:

1. Deterministic builder unit tests, including negative cases.
2. Bounded assembly, with at least 90 GiB free and a 1 GiB input-copy budget.
3. Static dependency and signature verification of every copied Mach-O.
4. Rename into a separate path containing spaces; run with minimal environment
   and explicit denial of development/Homebrew file reads.
5. QEMU version, scratch-image create/check, and a diskless paused HVF/QMP
   start/normal quit on a private socket. No existing VM disk, network, Cloud
   identity or guest is used by this smoke test.
6. Gateway/client startup/help and source-prefix rejection. Real TLS/simulator
   behavior remains for the integrated packaged-runtime gate.

## Following slices and preserved boundary

Continue with private Python/API and helper closure, prebuilt native hosts/web
assets, immutable backend exports, pinned firmware/Factory and all unsigned
functional-profile inputs. Then connect artifact selectors to the existing
product path under the accepted contracts. Stage 2 is not complete until all
three logical groups and their separate-location tests pass.

Keep working Test/Production, Factory .39/.31, credentials, run/model data,
release ledgers, warm Yocto/Unreal/CARLA inputs and the video repository intact.
No credential or provisioned-state directory is copied. Do not rebuild the
Factory or recook CARLA for a host packaging issue. No installer, public upload,
Developer ID/notarization or clean-Mac qualification is claimed here.

### Native UI/helper slice boundary

Precompile the unchanged Presenter window host and Driving Control source,
build the existing Presenter web application, and assemble their tracked
Python helpers/configuration into an exclusive local candidate. Record exact
source hashes, build commands, platform/compiler identity and output hashes.
Use the existing keyboard application metadata and local ad-hoc signing;
do not add entitlements or claim Developer ID distribution readiness.

Only tracked source files, reviewed runtime-helper entries, compiled web assets
and explicit build outputs enter this slice. Do not copy `.local`, `.run`,
editable environments, credentials, source maps, node_modules or operator
configuration. All generation remains build-time; the proof must deny reads
from the development workspace, Homebrew and Xcode after relocation.

Tests cover helper imports/CLI parsing, native argument validation, read-only
display discovery, static-asset delivery and the existing HTTP security
boundaries using clearly identified disposable fixtures. No native layout
restoration, process takeover, control command, Cloud read or VM action is
part of these fixture checks. A fixture must never be presented as live demo
status. The native Presenter still uses its accepted fixed loopback endpoint;
do not change that interface merely to simplify this packaging proof.

At this initial helper checkpoint the operator path still invoked build-on-demand
and resolved source trees. The subsequent host-launch checkpoint below records
the separate contract-backed selector integration; startup/help checks alone
did not establish it.

## Checkpoint

Authorized obsolete-build cleanup is [recorded separately](../../research/distribution-stage1-retention-audit-2026-09-26.md#authorized-cleanup).
The native closure builder is implemented in `scripts/distribution/native_bundle.py`.
It supports explicitly located native extension files as well as executables;
neither discovery nor copying includes arbitrary user-data directories.

First native candidate: four executables plus 29 dependency libraries, 77,527,152
source bytes (about 74 MiB; installed accounting about 75 MiB with notices).
All 33 Mach-O signatures/dependency paths pass, with unchanged source hashes.
QEMU retains its existing hypervisor entitlement; no new entitlement is added.
Available notices for 25 dependency formulae are included, but source-offer and
redistribution review remain open.

The same candidate was renamed into a separate temporary path containing spaces.
With Homebrew/workspace file reads denied and a minimal environment, nine scoped
smoke checks pass: denial control, both QEMU version commands, Gateway and client
help, scratch-image create/check/info, and a 128 MiB diskless paused HVF/QMP
start/normal quit. Dynamic library traces contain no Homebrew/workspace load.
No existing VM, disk, network or Cloud object was used. This is not a guest boot,
real Gateway TLS/CARLA proof, dynamic-plugin/data closure or clean-OS acceptance.

Local engineering evidence is in the ignored CARLA workspace
`Build-distribution-stage2-20260926/native-smoke-001.json`; the relocated payload
is `/private/tmp/aosedge-stage2-native.cir6B1/Portable Native Candidate`.

### Private interpreter and matching simulator API

`scripts/distribution/private_python.py` now assembles a private Python 3.12.14
interpreter, standard library and relocated native modules. The builder does
not copy the developer's site-packages, user/custom distribution startup hooks
or caches. Its 1 GiB input-copy budget and 90 GiB free-space reserve include
the standard library as well as the native dependency closure.

An initial site-enabled proof caught a real packaging defect: Homebrew's
`sitecustomize.py` resides in the standard-library directory and adds its
global site-packages path even in isolated mode. The earlier `-S` proof did
not exercise that hook. Both `sitecustomize` and `usercustomize` files/packages
are now excluded, with regression coverage; the failed receipt is retained.
The revised proof runs with site enabled and asserts every interpreter search
path remains inside the relocated candidate. Homebrew, Xcode and workspace
reads and all network access are denied during the offline checks.

The matching CARLA extension was rebuilt for CPython 3.12, not relabelled from
the Stage 1 CPython 3.9 wheel. It reuses the qualified LibCarla client and
Boost 1.90 source, recompiling only Boost.Python and the Python API. Neither
Game/content nor Factory was rebuilt. Build evidence records 18.51 seconds
for Boost.Python and 43.12 seconds for the API, with peak owned physical
footprints of approximately 0.37 and 1.86 GiB respectively.

An offline wheelhouse contains CARLA 0.10.0 (local arm64/cp312 build), NumPy
2.0.2, NetworkX 3.2.1 and Shapely 2.0.7 (pinned public binary wheels), totalling
10,727,530 bytes. Every wheel has an input hash; generated developer-shebang
scripts are excluded from the runtime. The combined relocated candidate has
2,429 recorded files and 78,652,266 payload bytes, excluding its own manifest.
No developer environment or credentials are copied.

Passed offline checks: standard-library imports and SQLite/compression use,
Demo Control CLI import/help, CARLA value objects and wheel-angle API presence,
navigation-agent imports, NumPy arithmetic, NetworkX routing and Shapely
geometry. Loaded-library traces show no development-prefix dependency.
This is not yet an ordinary operator launch, Cloud-worker proof, native UI
integration, clean-Mac qualification or external redistribution approval.

Evidence in `Build-distribution-stage2-20260926`:

- `python-smoke-002.json`: revised site-enabled interpreter and CLI proof.
- `simulator-wheels.json`: pinned wheel sizes/hashes and build provenance.
- `simulator-python-smoke-001.json`: retained failed hook/path check.
- `simulator-python-smoke-002.json`: corrected offline imports/value proof.
- `api312-live-002.json`: matching private-client/standalone-Game physical proof.

Current candidate: `/private/tmp/aosedge-stage2-native.cir6B1/Simulator Python Candidate 002`.
The first candidates remain explicitly superseded engineering evidence; do
not select them for delivery.

### Live matching-client checkpoint

The corrected private interpreter/client connected to the retained qualified
Game on private test ports 2100/2101/2102, with Traffic Manager on 19000. Client
and server both report 0.10.0. RPC readiness took 10.162 seconds. The unchanged
Stage 1 physical probe passed real motion/RPM/wheel rotation, braking to stop,
finite four-wheel angles including near-zero steering, 15.93 metres of
Autopilot motion and 560 GNSS frames. It removed its actors, restored world
settings and left no vehicles; the owned Game exited zero without forced stop.
No working Test, Cloud identity, Gateway or ordinary runtime journal was used.

The client was run with developer workspace/Homebrew/Xcode reads denied and a
minimal environment; its loaded-library trace contains no development prefix.
The Game kept its previously qualified App Sandbox, without an additional
seatbelt wrapper or entitlement change. This proves the private API against
the qualified simulator, not a full UI session, whole-package network
isolation or clean-host acceptance.

Two harness issues were reconciled before this pass: an initial runner command
placed options after its remainder argument and launched no process; the first
actual invocation inherited a 14 GiB build default and was stopped at 16.52 GiB
during Game startup, before a completed client proof. Its process tree was
confirmed gone. Comparison with Stage 1 showed the qualified Game tests used
a 24 GiB ceiling. The repeat used that existing ceiling, retained the 90 GiB
disk reserve and critical-pressure stop, and completed in 32.96 seconds with
14.12 GiB peak owned footprint and 103.88 GiB minimum free space. This is not
evidence of a simulator defect or a reason to remove resource guards.
Guard records remain in Stage 1 `evidence/stage2-api312-live*.json`; interrupted
and prelaunch attempts are not presented as successful product tests.

The native/Python builder unit suite passes 28 cases; `docs-check` and
`git diff --check` pass. No operator runtime selectors have changed.

### Next bounded action

The native UI/helper, Cloud-worker, backend export and vehicle-input slices
are assembled and pass the scoped checks below. The first integrated selector,
for packaged VDP/service preparation, now passes the real offline Prepare proof
recorded in the final checkpoint below. Next, define and qualify native UI,
standalone simulator and private interpreter/helper selection as the next
bounded operator-launch slice, preserving session ownership and layout.
QEMU/firmware and backend-image selection, fresh Docker engine import, the full
native graphical session and remaining Stage 2 exit gates remain open. Do not
switch the working demo or copy user/run state. Later stages are not started.

### Native UI/helper artifact checkpoint

Two reproducible build-time tools are now in the integration repository:

- `scripts/distribution/ui_build.py` compiles Presenter and Driving Control,
  type-checks and builds the existing web UI, and records tracked source,
  compiler and output identities. Every build subprocess has network access
  denied; prepared dependencies are required, not downloaded automatically.
- `scripts/distribution/ui_helpers.py` assembles only reviewed source helpers,
  built native/web files and repository notices. It rejects symlinks, changed
  or incomplete build receipts, untracked Gateway helper inputs, source maps,
  unexpected native files, non-system native dependencies, added entitlements,
  existing output directories and insufficient disk space.

Source baseline: integration `0d132125f8c88776b173060dc0cbc414332bcc45` and
Gateway `4e384798c95298a706709775c6fb33367edd00c6`. Their runtime UI/helper
sources were unchanged; the new packaging tools/tests and this checkpoint
are working-tree additions. The build records hashes for tracked web inputs,
both Swift sources and keyboard metadata, rather than claiming a commit ID
alone proves reproducibility.

The transient recipe first passed, then the saved recipe was exercised once.
The saved build completed in 10.31 seconds, with 218,990,080 bytes peak sampled
owned footprint and no resource-guard stop. This is an arm64/macOS 26.0
engineering target, not a newly qualified minimum OS requirement. Its copied
keyboard plist minimum is normalized to 26.0 to match the compiler target;
the installed application's original metadata is unchanged. Both native
binaries load only system macOS libraries; ad-hoc signatures verify and no
entitlements were added. Developer ID/notarization remains unqualified.

Current relocated candidate:
`/private/tmp/aosedge-stage2-native.cir6B1/UI Helper Candidate 002`.
It has **92 payload files, 4,380,820 bytes**, excluding its manifest and the
separately qualified private Python runtime. It contains the prebuilt Presenter
host, Driving Control application, compiled web UI, tracked orchestrator Python
sources, nine Gateway runtime helpers, the unchanged base configuration template
and two repository licenses. The base configuration is not a newly accepted
packaged launch profile; its map/spawn/port overrides remain an integration gate.
No Swift source, node_modules, developer environment, certificate, user/run
state or operator configuration is packaged.

The same payload was moved, not rebuilt, to the separate path containing spaces.
Its eight scoped entry-point/check groups pass with workspace/Homebrew/Xcode
reads denied: native invalid-argument handling, native read-only display
discovery, malformed telemetry-argument rejection, three helper CLI imports,
and the combined helper/HTTP proof. That proof also verifies the denial itself,
private CARLA API/helper imports, a disposable local control-protocol exchange,
two HTTP server start/stop cycles, delivery of every built web asset, stable
client build identity, no mutation endpoint, no private-file/path traversal
access, and rejection of foreign Host/Origin. Non-loopback TCP is denied and
checked with a negative control. All 92 payload hashes are unchanged afterward.

The first combined fixture attempt exposed a test-profile issue: a broad local
endpoint allow rule did not enforce the intended outbound denial. It was
replaced with separate bind/inbound and outbound loopback rules, then the same
payload passed without rebuilding. This was a harness correction, not a product
network-policy change. The failed receipt remains distinguishable from the two
successful proofs. Fixtures are explicitly labelled non-live; no real Cloud,
VM, simulator, native layout or protected operation was used by this slice.

Validation: **324 Presenter unit tests** and **45 distribution-tool unit tests**
pass; web type-check/build, native compile/signature checks, documentation and
whitespace gates pass. The original Test QEMU process remained PID 37277 with
its 24 September 20:20:06 start time. No working selectors or installed apps
were replaced, and no permanent test server is left running.

Local evidence in `Build-distribution-stage2-20260926`:

- `ui-inputs-002/build-receipt.json`: saved recipe's successful build and hashes.
- `ui-helper-smoke-001.json`: retained failed fixture network-denial control.
- `ui-helper-smoke-002.json`: first artifact's corrected scoped proof.
- `ui-helper-smoke-003.json`: saved recipe/current candidate's passing proof.

The guard receipt is Stage 1 `evidence/stage2-ui-recipe.json`. Build logs and
the two bounded Swift build caches are retained for diagnosis/reuse (about
139 MiB for both input directories, plus approximately 9 MiB for both small
UI payloads). Free disk after this slice is approximately 103.6 GiB. No
Unreal/CARLA/Factory rebuild or additional cleanup was performed.

This checkpoint does **not** qualify a complete native graphical drive session,
automatic operator startup without source paths, Cloud-worker execution,
backend/image delivery, an installer or installation on a clean Mac. These
remain explicit later gates, not inferred from CLI/display/fixture success.

### Cloud-worker artifact checkpoint

The build-only boundary above also applies to this slice: no operator lookup,
credential enrollment, Cloud authority, trust policy or lifecycle behavior is
changed. The existing SDK transition correction remains source-locked and
unmodified, as required by the [Unit lifecycle architecture](../../architecture/demo-control.md#unit-lifecycle-authorized-increment).

The complete runtime dependency closure of the observed Cloud environment is
**41 packages**, excluding its developer installer (`pip`). All 41 exact versions
were available as public PyPI wheels. Each downloaded wheel's SHA-256 was checked
against the corresponding public PyPI release JSON. Immutable URLs, sizes,
versions and hashes are now saved in
[the Cloud wheel lock](../../../workspace/cloud-worker-wheels.lock.json).
The three SDK roots remain `aos-keys` 1.10.0, `aos-prov` 5.4.2 and `aos-signer`
2.0.1. No opportunistic library upgrade or copy of the installed venv is used.

The new [offline assembler](../../../scripts/distribution/cloud_worker.py) takes
the qualified private Python base, an exact wheelhouse, that lock, the integration
adapter source and a new output path. It verifies both outer wheel hashes and
every wheel's RECORD, package identities/compatibility, transitive dependency
constraints, absence of unrelated packages, base-file receipts, safe paths,
absence of startup hooks/symlinks/private-key containers, output exclusivity,
the 512 MiB expansion/copy budget and the 90 GiB disk reserve. It never downloads,
executes an installation script or produces developer-path console launchers.
The build/test environment needs `packaging` 26.3; CI now explicitly pins this
build dependency. End users do not need this developer environment.

The source-locked runner, its guard and its five-file source lock are copied to
`demo/scripts/host`, the relative destination expected alongside the packaged
orchestrator. This prepares artifacts only; merging selectors into the ordinary
operator path is still a later gate. Public CA resources shipped by the official
wheels and dependency notices are retained. No operator certificate, token,
Keychain item, private settings, run journal or release ledger was copied.

Current relocated candidate:
`/private/tmp/aosedge-stage2-native.cir6B1/Cloud Python Candidate 001`.
It contains **3,204 payload files and 115,003,292 bytes** (about 109.7 MiB), plus
its manifest. The wheelhouse is 24,581,670 bytes (about 23.4 MiB). All ten native
extension modules contain arm64; six retain the vendor's universal2 bytes rather
than being rebuilt or thinned. Their arm64 load dependencies are OS libraries
only, with no developer rpaths. Own Mach-O install IDs are distinguished from
loaded dependencies. Native wheel bytes, package metadata and RECORDs remain
unchanged. External redistribution/licensing and final signing/notarization
are not approved by this local test.

After moving the candidate to a path containing spaces, tests run with an empty
HOME, minimal PATH, Python isolated mode, workspace/Homebrew/Xcode/operator-Aos
and Keychain file reads denied, and external network denied. Negative controls
confirm the source/private-directory and outbound-network denials. The three
official CLI help paths, exact dependency set, SDK/signer imports, source guard
and correction loading pass. In-memory synthetic fixtures exercise the official
PKCS12 conversion helpers, RSA/JWT verification, Ed25519 and bcrypt. Packaged
trust resources and schema libraries load successfully. The actual native gRPC
extension exchanges official IAM protobuf messages with a disposable fixture
over a private Unix socket. No fixture certificate or key is exported to a file.
All 3,204 recorded hashes remain unchanged, and no test server remains running.

The first prototype passed CLI checks but its TCP fixture failed because the
test sandbox denied gRPC's IPv4-mapped IPv6 bind. The harness switched this
offline serialization/native-extension proof to a private Unix socket; the
same prototype then passed. This is **not** a product-network correction or a
successful guest TCP/provisioning test. No production sandbox was weakened.

Evidence under `Build-distribution-stage2-20260926`:

- `cloud-observed-packages.json` and `cloud-pins.txt`: metadata-only inventory.
- `cloud-wheels.lock.json`: upstream-hash-checked input record (also saved in Git).
- `cloud-smoke-prototype-001.json`: retained failed TCP fixture attempt.
- `cloud-smoke-prototype-002.json`: corrected prototype's passing proof.
- `cloud-smoke-001.json`: saved assembler's passing relocated proof.
- `cloud-smoke-002.json`: repeat with the diagnostic script outside the artifact.

The distribution-tool suite now passes **63 tests**, including 18 Cloud builder
cases. Test VM PID 37277 retains its original 24 September start time; no working
selector, VM, simulator or user account was changed. Retained new wheel/prototype/
candidate storage is approximately 259 MiB allocated; free disk is about 102.7 GiB.
This scoped checkpoint does not prove Cloud TLS/authentication, actual upload or
provisioning, OS trust enrollment, ordinary packaged worker launch, a complete
installer or a clean Mac. Continue with backend/platform inputs before the
contract-backed runtime-selector integration and full native UI gate.

### Backend export and vehicle-input checkpoint

The unchanged Stage 0 backend images are exported by immutable image ID, not
mutable tags, into one **82,130,944-byte** Docker OCI archive. Its SHA-256 is
`c15c6f69eddec6d9bc0552215414c9b0b8186fe9524392c4c9cb4f1d3b607a28`.
The archive contains the pinned Brake/Tire Linux/arm64 images and their build
attestations. It contains no container volumes or copied operator databases.
No image was rebuilt, pulled or pushed. Loading it back into the existing
engine preserved both image identities; because they were already present,
this is an **idempotent import**, not a clean-engine installation proof.

Both image entry points pass a disposable startup proof with no external
network, published ports, host bind mounts or named volumes. They run as their
existing `node` identity with read-only rootfs, all capabilities dropped,
no-new-privileges, 256 MiB memory, 64 PIDs and private bounded tmpfs directories.
Each creates its empty database, becomes ready, creates the private control
socket and rejects missing vehicle context with HTTP 503. Test containers are
removed afterward. This does not prove actual telemetry ingestion, advisory
reset or persistent database restart under the future packaged operator.

The first startup harness mounted over all of `/tmp`, hiding the socket parent
directory created in the image. The backend exited before the probe completed.
The corrected harness mounts only `/tmp/demo-backend`; the unchanged images
then pass. No product permission, memory quota or image content was changed.
The failed receipt remains separate from the successful one.

Starting Docker Desktop automatically started seven pre-existing containers
under their saved restart policies. Their identities and volumes were preserved;
after export and proof Docker Desktop was stopped successfully, restoring its
initial stopped state. No test container remains. Future installer checks must
account for this engine-wide startup side effect rather than claim Docker
startup affects only the two demo containers.

The [offline archive validator](../../../scripts/distribution/backend_archive.py)
checks a bounded, non-extracted archive: safe unique regular members, the exact
two OCI root identities, every referenced blob's size/hash, complete reference
closure, Linux/arm64 configs and source labels, decompressed layer hashes and
Docker/OCI compatibility. It rejects mutable tags and unreferenced blobs.
The 25 blobs contain 14 unique runtime layers, totalling 267,603,968 expanded
bytes. Docker's OCI image ID is the root index digest, not the config digest.
One validator attempt rejected the valid empty config in the build attestation;
support for that observed OCI descriptor and its embedded-data digest check
was added to the test fixture. The archive was reused without re-export.

The [vehicle-input assembler](../../../scripts/distribution/vehicle_inputs.py)
copies only explicitly pinned preparation inputs:

- Clean immutable Factory .39 and matching QEMU firmware, with the original
  Factory provenance/qualification state preserved.
- Three reviewed **unsigned** VDP profiles with 7/15/23 read paths, plus the five
  current source-pinned runtime modules. V1/V2 retain their feature profiles,
  not their old transport implementation; V3 includes advisory code.
- Prebuilt Brake V1/V2/V3 and Tire V1 Linux/arm64 exports, their public licenses,
  binary/source receipts and matching successful CTest reports.
- Six accepted VDP/service configuration contracts and repository notices.

It rejects changed profile/binary/firmware receipts, incomplete inventories,
mutable Factory inputs, unsafe paths/links, insufficient disk and existing
outputs. Build-time Git access exports only the already reviewed runtime commit,
never the Platform working tree. No old signed package, certificate, private
key, run/model data, release ledger or VM overlay is selected. The delivered
inputs are explicitly **not upload-ready**; operator preparation will still
need a new release number, selected destination identity and authorized signing.

The candidate has **207 files and 7,121,327,470 logical payload bytes**, excluding
its manifest. Of these, 6,997,147,648 bytes are the unchanged Factory .39.
The Factory transfer uses an APFS clone and verifies the complete target SHA-256
once against `demo-v1.1`; it does not rebuild, boot, rebase or provision the image.
APFS shares the original data blocks until writes occur, so `du`'s roughly
6.6 GiB for the whole candidate is not incremental physical disk consumption.
The other inputs total 124,179,822 bytes (about 118.4 MiB). There is no silent
full-copy fallback when clone support is unavailable. Free disk after this
slice is approximately **102 GiB**, above the 90 GiB reserve. No cleanup or
Unreal/Factory/service compilation was performed in this slice.

Both candidates reside at separate paths containing spaces:

- `/private/tmp/aosedge-stage2-native.cir6B1/Backend Images Candidate 001`.
- `/private/tmp/aosedge-stage2-native.cir6B1/Vehicle Inputs Candidate 001`.

With workspace/Homebrew/Xcode/Keychain reads and all network access denied,
the private interpreter verifies the backend archive and all 206 smaller
vehicle-input file hashes. The Factory's transfer hash is reused, with size,
read-only mode and private-QEMU raw-format checks, rather than rescanning it
for status. In an explicitly labelled temporary fixture, the existing VDP
composition/inspection functions consume the packaged reviewed modules and
produce valid V1/V2/V3 envelopes with 7/15/23 read paths and the intended
advisory distinction. The fixture substitutes only the source-reader callback;
it is **not** an integrated operator selector. Temporary fixture version
999.0.0 is neither allocated in a release ledger nor signed/published, and its
temporary packages are removed when the fixture exits. All four service exports
also pass the existing product reader and exact configuration generation, with
6/12/15 Brake and 18 Tire KUKSA permissions respectively.

Validation: **92 distribution-tool tests** pass, including 29 new archive/input
tests. Documentation and whitespace checks pass. Test QEMU remains PID 37277,
started on 24 September at 20:20:06; this is a process-preservation check, not
a new Cloud-online claim. No current runtime selector or Cloud object changed.

Compact evidence in `Build-distribution-stage2-20260926`:

- `backend-smoke-001.json`: failed socket-directory harness attempt.
- `backend-smoke-002.json`: passing disposable image startup proof.
- `backend-integrity-001.json`: complete offline OCI integrity receipt.
- `vehicle-backend-relocated-001.json`: source-denied archive, composition,
  service-input and Factory-format checks.

The payload manifests remain beside each candidate. These build-only tools do
not constitute an installer or distribution approval. Fresh-engine import,
ordinary operator selectors, packaged guest boot and native UI/E2E, dependency
redistribution/source-offer review, signing/notarization and clean-Mac acceptance
remain open. Factory .31/Production, Factory .39/Test, warm caches, credentials
and the video repository remain outside the changed boundary.

### Packaged preparation integration checkpoint

The first source-path selector is implemented, behind the fixed opt-in
`preparation-inputs` directory in the existing artifact catalogue. Its source
lock pins candidate manifest SHA-256
`ea3e4f67661b9aa5f73f52786e1d0e13b44ba87a6fc2688dc82479dbdcbaff51`.
VDP Prepare consumes unsigned profiles and the reviewed runtime without Git;
service Prepare consumes prebuilt products without invoking Git, Docker or a
compiler. Missing/invalid selected inputs fail closed before the Cloud release
catalogue or allocator. Absence of a selection preserves developer behavior.
The new catalogue may initially have no generated component directory; VDP
Prepare now creates that output directory only after validating the inputs.

The existing Prepare operations were exercised in an isolated path containing
spaces, using relocated Python and SDK candidates. Workspace, Homebrew, Xcode,
Keychain and network reads/connections were denied with negative controls.
Only the external release catalogue and private SDK interpreter configuration
were substituted; input selection, composition, product validation, official
service schema validation and the temporary release ledger were real. A
Factory binding in the temporary journal was explicitly a fixture, not a VM.

| Profile | Read paths / permissions | Preparation time in offline fixture |
| --- | --- | --- |
| VDP V1 | 7 read paths, no advisory | 1.244 s |
| VDP V2 | 15 read paths, no advisory | 1.232 s |
| VDP V3 | 23 read paths, advisory | 1.235 s |
| Brake V1 | 6 permissions | 0.876 s |
| Brake V2 | 12 permissions | 0.615 s |
| Brake V3 | 15 permissions | 0.608 s |
| Tire V1 | 18 permissions | 0.609 s |

These are local preparation timings, not live Cloud latency or UI benchmarks.
All VDP outputs pass envelope inspection with current common-module digests.
All four service outputs pass the unchanged official SDK schema validator;
their model, permission, descriptor and quota contracts remain unchanged.
The temporary allocator preserves monotonic VDP/Brake/Tire versions. Repeating
an explicit VDP destination rejects overwrite; repeating Brake preparation
allocates the next fixture version and preserves the previous payload. No
package is signed/published and no real release number is consumed.

Eight real-input corruption checks cover the unsigned VDP, runtime module,
compatibility/advisory contracts, Brake binary, Tire receipt and both product
configuration contracts. Each rejects before the Cloud fixture is called and
leaves the temporary ledger byte-identical. A separate 14-case deterministic
unit suite covers absence/developer fallback, independent manifest trust,
missing/changed files, links, writable modes, unsafe/duplicate paths, size limits,
and no-build versus explicit developer-build routing.

Evidence under `Build-distribution-stage2-20260926` in the CARLA workspace:

- `preparation-selector-001.json`: test-harness-only failure. The fixture journal
  directory had the wrong mode; the writer rejected it before allocation.
- `preparation-selector-002.json`: successful continuation using the same COW
  input copy, with the corrected fixture permissions; no artifact rebuild.
- `probe_preparation_selector.py` and `run_preparation_selector.py`: retained
  scoped reproducer and exported source-file identities in the result receipt.

The accepted input artifact and original UI-helper candidate remain unchanged.
The updated Python source was exported into a separate test-only app tree; it
has not yet been rolled into the ordinary UI/helper distribution artifact.
The Factory test copy is an APFS clone, SHA-verified once at that transfer.
Free space after the proof is 101.84 GiB, above the 90 GiB reserve.

Regression gates: the full orchestrator suite passes **1,092 cases with 15
explicit skips** (1,077 executed), including the 14 new selection tests;
all **92 distribution-tool tests** pass. The initial restricted run could not
bind local test sockets; rerunning the same suite with that test permission
passes in 103.355 seconds. This is a harness-permission limitation, not a
product fix. Documentation validation passes for 276 Markdown documents,
658 stable identifiers and 38 Mermaid diagrams; `git diff --check` passes.

Remaining developer dependencies were inventoried: SourceDriver's Editor,
Gateway and interpreter paths; native app build-on-launch paths; QEMU/firmware
lookup; backend developer builds; default Cloud-worker interpreter; and writable
state tied to the current project root. Those need their own contract-backed
selectors and acceptance; this checkpoint does not qualify an installer,
full packaged launch, actual Cloud credentials, VM boot or a clean Mac.

### Packaged host launch checkpoint — functional proof, layout gate open

The existing host launch path now selects a fixed, independently locked
`host-runtime` closure: prebuilt native Presenter/Driving Control, web assets,
Gateway helpers/binaries, private Python 3.12/CARLA API, OpenSSL and the qualified
standalone Game. Manifest SHA-256 is
`b4b12c59a3193fc942fbb3a0e4024b7b533f4749105b5207e21cd49e21cf9e4b`.
The APFS-cloned candidate contains 14,170 regular files / 20,790,352,384 logical
bytes. No Game/Factory/native-UI rebuild was needed. The new OpenSSL closure
contains three native files and a public minimal request configuration, not
operator TLS keys. Updated application Python was exported into isolated app
trees; the original UI-helper payload is not presented as a newly released app.

Implemented boundaries:

- Invalid/modified/linked/undeclared selected inputs block; absent selection
  preserves development behavior. Hashes are cached only against unchanged
  in-process file identities; full dependency directory inventories are checked
  before execution. Neither status nor polling repeatedly hashes Game data.
- Existing SourceDriver/WorkspaceService own the same journal, fixed ports,
  strict Gateway assignment and native Quit. Packaged start skips Swift/CMake
  and Editor launch. Callbacks use the private interpreter and fixed app entry.
- Missing operator server TLS is explicit. A synthetic, private local fixture
  proves local CA/dashboard creation and stable repeat without any guest/Cloud
  authority. Private OpenSSL/Python work with network, workspace, Homebrew,
  Xcode and Keychain reads denied.
- A readiness subprocess timeout is now an unsuccessful observation within
  the existing 120-second overall window, not an abort or a second simulator
  launch. A stopped source can use updated display geometry; recoverable live
  startup still requires the exact recorded simulator command, before replacing
  its journal record.

Observed functional results use the actual SourceDriver, not a second launcher:
fresh local frames, one engineering-dashboard TLS role, zero attached guest
roles, idempotent Start with unchanged simulator/runner PIDs, and clean normal
Quit with no retained source ports/control socket. Three completed functional
starts took 25.02, 27.56 and 28.84 seconds on this warm development Mac; these
include integrity validation and are not clean-machine latency claims.
The native UI visibly showed LIVE, Autopilot at 19.5 km/h and then Safe Stop at
0.0 km/h / 100% brake. Advisory remained unavailable as expected without a
selected VM. The actual packaged `ui serve` delivered the exact pinned HTML
and created its protected session; ordinary `ui stop` verified its own exact
private invocation and idle state, then exited cleanly.

Do not mark native layout acceptance complete. Initial geometry matched every
expected surface and background ordering was VERIFIED. Later observations
reported the built-in visible height changing from 1,224 to 1,220 points, with
unchanged 2x scale. Browser/backdrop then differed by four points. Explicit
Restore did not close this: the Game became 910x611 versus requested 914x612;
browser/backdrop retained their earlier sizes. Source PIDs stayed unchanged,
telemetry remained fresh and z-order stayed VERIFIED. The complete reason for
the native resizing behavior is not yet proven. Keep the existing three-point
geometry tolerance and fail/incomplete result; do not rebuild Unreal or modify
the working desktop to hide this discrepancy. During the interactive screenshot
proof an additional CARLA AX window was also observed; this did not recur in
the no-capture proof and is not yet attributed to a product or capture cause.

Evidence and harness classifications:

- `Build-distribution-stage2-20260926/host-launch-assembly-001.json` and
  `host-launch-checkpoint-001.json` record the candidate and compact results.
- Stage 1 guard evidence `stage2-host-launch-001` records the initial probe
  timeout; `002` records a harness physical-footprint read error, not a claimed
  service crash. The guard now boundedly re-observes transient process reads,
  never treats a still-live unreadable owner as zero, and keeps the 24 GiB / 90
  GiB limits. `003` contains functional/UI proof but a late layout discrepancy;
  `004` and `005` explicitly fail the stronger end-layout assertion. All
  surviving proof processes were reconciled and closed; do not count attempts
  as passing whole-session qualification.
- Isolated `app7-presenter-entry.json` passes real HTTP/owned-stop acceptance.
  Earlier `presenter-entry-001` / `app6` checks could not invoke macOS's setuid
  `/bin/ps` inside the extra test seatbelt. The successful UI remains
  source/non-loopback-denied while its ordinary owner-inspecting stop runs
  outside that additional test policy. No product ownership guard was relaxed.
- `app8-offline-proof.json` covers the final dependency-inventory implementation;
  `app8-live-proof.json` preserves both functional success and layout failure.
  Isolated app reports live under the receipt's `/private/tmp/aoshl.*` fixture,
  not the current demo state. Synthetic private keys are not copied into reports.

Regression: **1,104 orchestrator cases, 15 explicit skips** (1,089 executed),
plus **92 distribution-tool tests**, pass. The 11 new host tests cover integrity,
extra importable files, routing, no builds, callback paths, explicit TLS inputs,
readiness timeout/repeat behavior and rejection before enrollment/spawn. The
Presenter stop suite additionally checks exact packaged ownership and unchanged
busy/recovery refusal. Documentation and whitespace gates pass. No source commit,
push, Cloud mutation, installation or working runtime selection was performed.

**Immediate next gate:** diagnose and prove the native display-settling/resize
case against exact owned windows, then rerun the scoped end-layout assertion.
Only afterward close this host slice and proceed with QEMU/firmware, backend and
Cloud-worker selectors, full packaged guest/UI E2E and later installer stages.
Working Factory .39/Test, Factory .31/Production, their identities/data, the
original native Presenter and the video repository remain outside the changes.

### Native resize correction and ordinary host handoff — 26 September

The preceding layout-open checkpoint is historical. The scoped resize proof
now passes; see the [detailed execution report](../../qualification/standalone-host-handoff-2026-09-26.md).
Independent experiments identified stale Accessibility geometry in borderless
Presenter windows and the Game's default aspect-ratio-preserving resize. Source
now posts native moved/resized notifications and supplies the existing Game
setting `bShouldWindowPreserveAspectRatio=False`. Restore observes frames after
the exact native acknowledgement. Ownership, layout and the three-point
tolerance are unchanged. A later desktop-height change can require explicit
Restore; continuous automatic adaptation was not added.

Only Presenter was incrementally compiled; Controller/web and all large Game,
cook, Factory and guest inputs were reused. The locked successor manifest is
`de160d783708b649bb60da979e2b66e4d1e7679b72fd50d0324716f135733d98`
(14,170 payload files / 20,790,358,693 logical bytes). Final isolated startup,
fresh frames, repeated Start/Restore, native ordering and normal Quit pass.
The orchestrator suite reports 1,106 tests with 16 explicit skips, OK; all 92
distribution tests pass. Generated test bytecode was rejected by the immutable
inventory, reconciled by exact identity, and prevented in later test children;
no relaxed integrity rule was introduced.

After preserving the prior candidate, the successor was moved into the default
catalogue without copying its multi-GiB payload. The ordinary demo now runs
standalone Game and prebuilt native hosts, with private Presenter HTTP/Python.
The pre-existing DNS failure was recovered by the existing owned helper restart;
the same Test .39 is Online, attached through mTLS, with VDP READY and the car
in Safe Stop. QEMU and CM/IAM/SM were not restarted. No Cloud mutation, model
reset or further large-artifact deletion occurred; about 103 GiB remains free.

**Next bounded gate:** finish VM/DNS ownership and runtime selection before
claiming the private UI can perform the whole lifecycle. Read-only inspection
confirmed that private Python rejects the still-development-owned DNS helper
with `VM_PROCESS_OWNER_CONTRADICTORY`; the old CLI recognizes it and DNS works.
Preserve strict owner checks and current Test. Do not silently adopt an arbitrary
process or use a port-based kill. QEMU/firmware, backend, Cloud-worker selectors
and complete app assembly still follow. Local browser visual review was blocked
by tool policy, so native geometry/CLI evidence is not labelled web UI acceptance.
Installer, clean-Mac and full E2E gates remain open. B/C/D retention batches
remain unchanged; warm build/repackage dependencies must be verified before
any further cleanup.

### Presenter late-server recovery — 26 September follow-up

Operator visual feedback exposed a remaining blank-page defect after the
initial host handoff: native windows had opened before HTTP, and the existing
reload attempted to reload a document that never committed. A synthetic native
WebKit baseline reproduces this; the corrected host passes delayed startup,
dialog/submission/server-idle guards, stable repeat and failed-refresh recovery.
The current source lock now pins manifest
`da72bce6d1785424b93564d280f9ae7786f8795437fd9019e89a1082b1db1634`.
Only Presenter and matching small metadata were replaced, preserving the
identities of the other 14,168 runtime files and all CARLA/Controller/VM processes.
HTTP-first reopening produced successful WebKit commit/finish for both actual
panels. Native load evidence and operator visual review remain separate.
See the [follow-up receipt](../../qualification/standalone-host-handoff-2026-09-26.md#blank-page-follow-up-and-presenter-only-repair).
This repair does not close the independent VM/DNS-owner or full Stage 2 gates.

### Portable VM input assembly — 26 September continuation

The [VM input checkpoint](../../qualification/portable-vm-inputs-2026-09-26.md)
records the next bounded slice: existing image/VM owners select packaged QEMU,
firmware and a private-interpreter DNS helper. Only 2,111,657 payload bytes were
assembled; QEMU/Python are reused from the existing host closure. No Game,
Factory, service or native host rebuild was needed. The independently locked
small manifest is `b8222b9bb8de59af834252d3b53817f6045945544f895d5bfd4bf5788591c5dd`.

Current owners remain untouched and exact matching still blocks implicit
legacy adoption. New helper commands are independent of the caller interpreter;
actual legacy handoff is not yet qualified. The operator deferred further live
checks until full assembly; the candidate is not promoted into the current
catalogue. Next are backend and Cloud-worker selection, complete application
assembly and then the preserved-owner/live qualification gates. No observed
backend/advisory symptom is considered fixed by this packaging checkpoint.

### Cloud/backend selector integration — 26 September continuation

The [source/integrity checkpoint](../../qualification/portable-cloud-backend-inputs-2026-09-26.md)
records completed fixed-worker and backend-candidate selection. Existing Cloud
workers consume the verified private SDK, retaining requests, roles and
deadlines; the pinned provisioning adapter verifies its executing interpreter.
UI configuration parsing does not perform the full SDK scan. Local failures
are not mislabeled as permission/Cloud failures and cannot start the worker.

Backend candidate selection consumes the pinned exported image identities and
cleanup protocols. Existing run records remain authoritative; activation still
requires the owned stopped-container gate. No image import, engine startup,
build, current-runtime handoff or Cloud call was performed. Both candidates are
reused at their existing locations without copying or rebuilding their payloads.
The complete source regression passes 1,155 cases with 17 explicit skips.

Next is the complete current application export, including every new selector
module, independent lock and required configuration/contract file. Bind the
already assembled artifact groups without importing developer state. Only after
that assembly proceed to the preserved-owner handoff and integrated live gates.
Current Test/Production, Docker, simulator, credentials, ledgers and the separate
video repository remain unchanged; no commit, push or tag change is claimed.

### Complete export and integrated preserved-run checkpoint — 26 September

The [application qualification record](../../qualification/portable-application-2026-09-26.md)
contains the completed 83-file export, five-group COW composition, isolated
source/network-denied proof and corrected immutable pins. The ordinary run now
uses the packaged VM/DNS, Cloud worker and backend selections as well as host
inputs. Same Test .39 boots and reattaches; real Brake/Tire work, fresh APPLIED
facts, backend delivery and external OFF/ON recovery pass. No guest/Factory/Game
rebuild, Cloud publication, model reset or identity retirement was performed.

The live run exposed three packaging boundaries missed by static closure:
QEMU's NIC ROM, admission's hidden developer-client reference, and a historical
pre-QM Gateway/client pair. Corrections and regression gates are recorded with
their transient/local proof, not attributed to AosCore or the service algorithms.
Full regression passes 1,163 cases with 17 explicit skips and 118 build-tool
tests. Native visual review, fresh-engine import and fresh serial-version E2E
remain separate gates; first-use/installer design is not silently invented.
The final raw guest reboot also passes automatic retained attachment recovery
in about 42.10s, with unchanged QEMU/simulator identity and no manual reattach.
Cloud subsequently reports ONLINE, 117/92/49 active/installed and no pending
updates. This does not qualify cold externalOFF boot or abrupt power loss.
Previous candidates and compact rollback evidence are retained; disk reserve
remains above 90 GiB and no additional cleanup was performed.
