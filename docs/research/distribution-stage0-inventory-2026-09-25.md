<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Distribution Stage 0 — release inputs and implementation boundaries

- Prepared: 2026-09-25
- Status: Inventory and work-packet gate complete; portability, licensing,
  clean-install qualification and hosted publication of the CI correction remain open.
- Owner: Demo Solution Team / release integration
- Plan: [Installable distribution and reproducibility](../planning/active/installable-distribution-and-reproducibility.md)
- Source milestone: [demo-v1.1 / Factory .39](../qualification/demo-v1.1-return-point.md)
- Machine-readable observations: [Stage 0 inventory](../../workspace/distribution-stage0-inventory.json)

This is a dated inventory, not a runnable installer manifest. Unknown package
sizes and unresolved distribution decisions are explicit, with an owner and a
closure gate below. Current-file checksums are not a claim of reproducible
binary provenance. No compilation, image creation, Cloud mutation, simulator
restart, cleanup or change to model behavior was performed in Stage 0.

## 1. Source and publication reconciliation

The immutable integration tag still peels locally and remotely to
`862d48b158e0f0980f80bb40eb0837453e21788e`. Integration `main` at entry and
remote `main` agree on `0d132125f8c88776b173060dc0cbc414332bcc45`.
The [workspace manifest](../../workspace/repositories.json) and CI checkout
pins continue to identify implementation inputs, not later documentation heads.

| Input | Implementation pin | Observed published HEAD | Difference |
| --- | --- | --- | --- |
| Integration | `862d48b158e0` | `0d132125f8c8` | Documentation only before this task |
| CARLA | `ac7d882cac49` | same | No tracked delta |
| Unreal | `9b705d6d2db5` | same | Clean restricted checkout |
| Gateway | `98b0b70a0c16` | `4e384798c952` | README only |
| Platform | `793b1fc035d2` | `a3eb9b63d960` | Seven Markdown files only |
| Brake service | `230cdd4515d1` | `a52f462c2efa` | Four Markdown files only |
| Brake backend | `42395715103d` | `7c64adf7b3d9` | README only |
| Tire service | `8639b57535e3` | `0ddaf76ecb712` | README only |
| Tire backend | `026018a47daa` | `ea2d6deec9b7` | README only |

Full revisions are in the return-point manifest and the
[documentation publication receipt](../qualification/documentation-implementation-audit-2026-09-24.md).
All nine observed branch heads matched their remotes. No fetch/reset/repin,
commit, push or tag movement was used to make the audit pass.

The workspace doctor is **not green**: its authorized, process-visible read
reported ten errors. These are the integration working documents, CARLA's
untracked media/private experiment scratch, six documentation-successor heads,
and two generated legacy launchers lacking the expected runtime-build reference.
All declared launcher dependency paths exist. The initial sandboxed doctor also
could not inspect processes; the bounded read with process access closed that
environmental check. Preserve scratch without copying it into release artifacts.
Do not reset documentation successors to hide these findings.

### Hosted CI discrepancy and bounded correction

The latest integration
[Repository boundaries run 36104970839](https://github.com/alexmaninblack/aosedge-sdv-demo/actions/runs/36104970839)
**failed**, despite the earlier tagged run being green. Its logs identify six
missing documentation-link targets in the Brake/Tire backend repositories.
The job did not check out those repositories; this is not evidence of a runtime
or Factory regression. Local documentation checks had both siblings available.

Stage 0 adds those two checkouts to the
[workflow](../../.github/workflows/repository-boundaries.yml), at the existing
workspace pins, and a regression test requiring all six owned dependency
checkouts to match that manifest. No dependency revision or runtime changes.
The correction is local until published; the failed hosted result is not
relabeled PASS. Release integration owns the fresh hosted gate after publication.

Platform run `36104846520` and Brake service run `36104846318` passed on their
documentation heads. CARLA's `31718550311` is a Dependency Graph success, not a
Mac packaging test. No exact-HEAD hosted run was returned for Unreal, Gateway,
either backend or Tire service. Absence of a run is not a failed or passed test.

## 2. Complete runtime input categories

`R` means required by the current operator path; `B` means build/development
only; `U` means user or operating-system supplied. These are current facts and
packaging assignments, not a promise to redistribute every dependency.

| Input / owner | Exact baseline and observed artifact | Role / unresolved portability work |
| --- | --- | --- |
| CARLA simulator / Vehicle Simulation | CARLA `ac7d882…`, runtime version 0.10.0; Unreal 5.5.4 at `9b705d6…` | R: currently Editor plus `.uproject`; B: engine/compiler/source. Stage 1 must produce the standalone game and preserve wheel telemetry fixes |
| CARLA assets / Vehicle Simulation | Separate content repository `639d6eff5aae672da4219e9ace4a2ee891367548` | R: cooked map, vehicle, sensors, materials and referenced assets; B: full content Git history. This additional input was not pinned by the eight-repository workspace manifest |
| CARLA Python client and helpers / Vehicle Simulation + Gateway | Installed `carla==0.10.0`, CPython 3.9 Darwin extension; checksum in inventory; agent helpers read from `PythonAPI/carla` | R: matching native extension and Python helper modules, NumPy 2.0.2, NetworkX 3.2.1, Shapely 2.0.7 observed. No distributable wheel found at `PythonAPI/carla/dist`; package ABI and complete used-module closure in Stage 1 |
| Gateway + VISS client / Gateway | Source `98b0b70…`, CMake 0.9.2; native arm64 executables, 13,906,320 and 2,233,344 bytes | R: LibCarla-connected runtime and VISS client, scripts/config and TLS setup. Direct Homebrew OpenSSL references must be removed or explicitly supported in Stage 2 |
| Driving Control / Telemetry / Gateway | `tools/KeyboardControl.swift`; installed arm64 AppKit app, 297,760-byte executable | R: same native UI and control owner. Currently ad-hoc signed and built on demand when source is newer; prebuild for distribution |
| Presenter / Integration | React UI 0.1.0 plus 178,784-byte arm64 Swift AppKit/WebKit host | R: built web assets and native host; B: Node 26.0.0, npm 11.12.1, TypeScript/Vite. Current host is ad-hoc signed, no TeamIdentifier; final app signing not done |
| Demo Control and host helpers / Integration | Python project 0.1.0 at tagged implementation; Python 3.9.6 currently linked to Xcode | R: shared orchestration, HTTP server, DNS bridge, SSH/serial/QMP adapters, native access and lifecycle. Empty Python `dependencies` does not describe the separate Cloud worker environment |
| Brake/Tire backends / Function Teams + Integration hosting | Two Linux arm64 local images; exact IDs below, Node base digest pinned in Dockerfiles | R: images, SQLite storage/migrations, private admin sockets, projected context and network setup; B: build tools. No verified downloadable distribution images yet |
| Container engine / Release integration + operator | Docker Desktop 4.89.0, Engine 29.7.2, Compose 5.5.0 observed | R/U: supported Docker-compatible host runtime. Desktop terms/installation must be addressed; no automatic assumption of free commercial entitlement |
| QEMU and UEFI / Integration VM owner | QEMU 11.0.3; `virt-11.0,accel=hvf`; fixed 2-MiB firmware SHA in inventory | R: arm64 emulator, `qemu-img`, firmware and complete dependent-library closure. Homebrew formula size is not a portable package size |
| Clean Factory / Platform | .39, 6,997,147,648 bytes; digest and native AosCore triplet in checkpoint | R: unprovisioned image, manifest and compatible overlay handling. No new image needed for the inventory; qualification remains scoped, not full E2E |
| VDP family preparation / Platform + Integration | Three unsigned source archives, verified exact digests; profile source `0a2c824…`, common/advisory runtime `1fe5649…` | R: immutable input for V1/V2/V3 preparation, selected-instance signing later. Current `git show` and historical archive dependency must become explicit packaged inputs, not a requirement for old full checkouts |
| Brake/Tire preparation / Function Teams + Integration | Brake V1/V2/V3 at `230cdd4…`; Tire V1 at `8639b57…`; eight executable hashes verified | R: four prebuilt Linux arm64 exports plus license/provenance files. B: Docker/C++ dependency builds. Current HEAD-keyed lookup can require a new build even after documentation-only commits |
| Aos provisioning/signing worker / Integration + Aos tooling owner | Separate Python 3.12.14 environment; `aos-prov` 5.4.2, `aos-keys` 1.10.0, `aos-signer` 2.0.1 | R: tools and transitive Python/native dependencies; source-locked provisioning adapter. Package/hash-lock separately from operator credentials |
| User configuration and host privileges / Operator + Integration | Selected Cloud endpoint, OEM/SP access, local trust, SSH enrollment, Keychain/native permissions | U: never clone the developer's identities, certificates, token files or run state. Installation must explain required access and permissions; not ship a provisioned VM |

The native host files' new hashes freeze only the inspected file identities.
Creation-time compiler/source receipts and complete dylib closure are still a
Stage 1/2 deliverable. Factory integrity is taken from its existing
creation/transfer manifest; the unchanged multi-gigabyte image was not rehashed.

### Backend identity reconciliation

The inspected local images are:

- Brake: `sha256:48f633748d225b27079e69a439e875745067a5248a7006c3b9685dc8a5e2baf1`,
  source tag `42395715103d9f512c2586a2c9b98c3975c06ab7`.
- Tire: `sha256:5dddd12060c3e65f928e844a65f92ae8826d1e8e52dce66329f86682934c3326`,
  source tag `47cfa632a80c89a7eaab0c501fe437c4ae2cb180`.

Tire's image source predates the workspace pin `026018a…`; their diff changes
only README.md, not executable behavior. Preserve that truthful build identity
instead of retagging it as if rebuilt. Docker's local ID/RepoDigest observation
does not prove an accessible remote registry artifact. Both Dockerfiles pin
`node:26.0.0-bookworm-slim` at
`sha256:34881fd97f67bed28bbfe3614a219e7d793e2b7554de33eaf71797d9dc8a35cc`.

### Transitive dependency authorities

- Presenter: [package lock](../../apps/presenter-ui/package-lock.json).
- Native platform and service dependencies: their committed `DEPENDENCIES.json`,
  recipes, Dockerfiles and product-build receipts. Retained native patches are
  detailed in the [Platform mainline record](../../../aos-vehicle-platform/docs/aoscore-mainline-migration-2026-09-23.md)
  and [.39 build](../qualification/factory-39-build-2026-09-24.md), including
  CM cold-component reconciliation, systemd-slot/runtime security and native
  permission compatibility. This is not stock unpatched mainline.
- Gateway directly links Homebrew OpenSSL 3.6.3. QEMU also links Homebrew
  Capstone, GnuTLS, Pixman, libpng, JPEG, Snappy, LZO, DTC, GLib, Zstandard,
  libslirp, VDE, ncurses and libusb, plus OS frameworks. This is an observed
  first-level list, not a recursive portable-library manifest.
- The installed CARLA extension links system libc++/libSystem; Python and its
  NumPy/Shapely native dependencies remain separate packaging inputs.
- Cloud worker's observed application dependency set is recorded below. This is
  an installed-version observation, not yet a hash-locked wheelhouse. Release
  integration owns resolution, wheel origin, native closure and license checks.

```text
aos-keys 1.10.0; aos-prov 5.4.2; aos-signer 2.0.1
annotated-types 0.8.0; appdirs 1.4.4; arrow 1.4.0; attrs 26.1.0
bcrypt 5.0.0; certifi 2026.7.22; cffi 2.1.1; charset-normalizer 3.5.0
cryptography 50.0.0; grpcio 1.83.0; idna 3.18; invoke 3.0.3
isoduration 20.11.0; jsonschema 4.26.0; jsonschema-specifications 2025.9.1
markdown-it-py 4.2.0; mdurl 0.1.2; packaging 26.3; paramiko 5.0.0
protobuf 6.33.6; pycparser 3.0; pydantic 2.12.4; pydantic_core 2.41.5
Pygments 2.20.0; PyJWT 2.13.0; PyNaCl 1.6.2; python-dateutil 2.9.0.post0
referencing 0.37.0; requests 2.34.2; rich 15.0.0; rpds-py 2026.6.3
ruamel.yaml 0.19.1; semver 3.0.4; six 1.17.0; typing_extensions 4.16.0
typing-inspection 0.4.4; tzdata 2026.3; urllib3 2.7.0
```

Developer-only tools include Xcode/Swift/Clang/Metal tools, CMake/Ninja,
Unreal build/cook tools, full content/source Git, Python build tools, Node/npm,
Docker Buildx, source/licensing gates and the isolated Yocto Builder with
downloads/sstate. These must not silently become end-user prerequisites.

## 3. Local assumptions that must not escape into the installer

1. `workspace/repositories.json` resolves sibling source/build paths, Xcode's
   `.venv-m5`, the Editor and a home-directory native app. `SourceDriver.assets`
   requires these files; a standalone `.app` cannot simply be substituted
   without adapting and testing this existing owner.
2. Presenter/Control can invoke `xcrun swiftc` at runtime, while Presenter
   process recognition expects the development virtual-environment path.
3. Trust setup and native binaries use `/opt/homebrew` OpenSSL. Copying just
   the executable loses those libraries. QEMU has a broader dylib dependency tree.
4. The Cloud worker uses a separate home-directory Python environment;
   provisioning has an exact source-locked correction. Git, SSH, shell,
   `osascript`, Keychain and OS frameworks have runtime uses beyond compilation.
5. Component preparation reads fixed historical Git blobs. Service preparation
   looks for build exports under the current service HEAD. Preserve present
   exports, but select release artifacts by immutable manifest in the planned
   implementation rather than requiring a compiler after a README update.
6. Private state is spread across ignored `.local`, `.run`, artifact roots,
   local Aos security configuration and Keychain. Split immutable installation
   inputs from private per-user state; never copy these directories wholesale.
7. Current paths have socket-length and unsupported-character guards. Test
   spaces, a different username/root and a long path rather than assuming that
   changing a single root variable makes the application portable.
8. Preflight must include Presenter 18080/18600, CARLA 2000 and associated
   streaming ports, Traffic Manager 18000, VISS 6443/16443, DNS 18053, backend
   18091/18092 and selected VM SSH/QMP sockets. These are owned existing paths,
   not permission to bind unrestricted interfaces or terminate unrelated users.

## 4. Initial test target and space measurements

First native target: Apple Silicon **M5 Pro, Mac17,8**, 18 CPU / 20 GPU cores,
48 GiB unified memory, macOS **26.6.2 (25G83)**. Development uses Xcode 27.0
(27A266a); Unreal is 5.5.4 with the pinned compatibility and steering corrections.
The layout code currently requires at least 1440×900 logical display space.
This identifies the first test environment, **not** a minimum supported Mac.

| Input | Measured local footprint | Download / final installation / build peak |
| --- | ---: | --- |
| Unreal development tree | 99.65 GiB in the same-day disk audit | Not shipped as source/Editor; standalone runtime size and cook peak TBD, Vehicle Simulation Stage 1 |
| CARLA content checkout | 80.90 GiB including 40.43 GiB content Git | Cooked required content TBD, Vehicle Simulation Stage 1; do not add this to the parent CARLA total |
| Gateway build tree | 129.47 MiB; principal runtime/client 15.39 MiB | Runtime libraries/scripts add to this; compressed download and peak TBD, Gateway Stage 2 |
| CARLA Python environment | 54.18 MiB, interpreter external | Full private Python/client distribution TBD, Vehicle Simulation Stage 1/2 |
| Presenter web output | 2.27 MiB plus native host 0.17 MiB | Final app/runtime/dependencies TBD, Integration Stage 2 |
| Demo Control virtual environment | 9.16 MiB, interpreter external | Full private interpreter and package closure TBD, Integration Stage 2 |
| Cloud Python environment | 111.76 MiB | Wheelhouse/private interpreter/download/peak TBD, Integration Stage 2 |
| QEMU Homebrew formula | 680.88 MiB, excludes dependency formulae | All-machine formula is not minimal runtime; final closure TBD, VM owner Stage 2 |
| Firmware | 2 MiB | Existing exact binary; origin/notices still reviewed by VM owner |
| Factory .39 | 6.52 GiB logical raw image | Compression, sparse copy and installation peak unmeasured; VM owner Stage 2 |
| VDP unsigned profiles | 18.95 MiB allocated total | Existing archives about 6.61 MB each; final package includes explicit source/provenance inputs, Platform Stage 2 |
| Four service build exports | 97.76 MiB allocated total | Existing ARM64 exports; final archive/download/peak TBD, Function Teams Stage 2 |
| Backend images | Docker reports 82,063,389 / 82,044,422 bytes | Shared layers/storage accounting differs; portable archive/registry transfer size TBD, hosting owner Stage 2 |
| Warm Yocto Builder | 78.38 GiB allocated host overlay after cleanup | B only, not a user installation dependency; preserved for affected guest rebuilds |

These numbers are allocated/local observations, not additive installer sizing.
No download or peak-temporary-space minimum is invented. Measure candidate
archive → expanded inputs → installed runtime → first-run caches → active
overlay/outbox growth; separately measure update staging/rollback duplication.
Release integration owns the combined requirement after those measurements.
About 189 GiB was available during Stage 0, after the
[authorized cleanup](disk-usage-retention-audit-2026-09-25.md).
Keep the existing 60-GiB build reserve; Stage 1 must add its bounded cook/output
budget before starting, not assume the entire remaining disk is disposable.

## 5. Licensing, attribution and delivery review

This is an engineering review checklist, not legal approval. The release owner
must obtain the applicable organization's licensing review before distribution.

| Input | Observed terms / primary reference | Owner and remaining gate |
| --- | --- | --- |
| Integration, Gateway, CARLA source | Local MIT license texts | Respective owner: carry notices and review embedded third-party components |
| Platform, Brake/Tire services and backends | Apache-2.0 project notices; dependency inventories separately | Component owners: ship required notices and generated binary dependency/license inventory |
| CARLA content | Local content LICENSE says CC BY 4.0; [attribution obligations](https://creativecommons.org/licenses/by/4.0/) | Vehicle Simulation: attribution/change records, asset-level provenance and any separate branding/asset conditions |
| Unreal code/runtime/tools | [Epic EULA](https://www.unrealengine.com/eula/unreal) distinguishes packaged object-code products from Engine/source/tools distribution | Release owner + Vehicle Simulation: confirm intended distribution, applicable seats/terms and notices; no public Editor/source bundle |
| QEMU | [QEMU license](https://www.qemu.org/docs/master/about/license.html): GPLv2, with component-specific terms | VM packaging owner: corresponding source/build information and dependency/firmware notices for selected binaries |
| Factory Linux/Yocto/KUKSA/AosCore | Mixed licenses, not a single Apache license for the image | Platform owner: export image package/license manifest, notices and applicable corresponding-source material before external delivery |
| Python, OpenSSL, Node and transitive packages | Separate runtime/package licenses | Integration + component owners: recursive native/Python/JS inventory and redistribution checks; current top-level notices are insufficient |
| Docker Desktop | [Docker terms](https://docs.docker.com/subscription-billing/desktop-license/) distinguish free eligible use from paid professional use | Release owner + operator: supported runtime and entitlement/setup decision; do not bundle Desktop or accept its terms automatically |
| macOS native applications | Current host/control signatures are ad-hoc; no release team identity | Release owner: Developer ID, entitlements and distribution/notarization path; no bypass of Gatekeeper as an install instruction |
| OEM/SP Cloud and signing access | User-supplied authorization, not a redistributed demo identity | Operator / Cloud administrator: access prerequisites and private setup; do not redistribute personal credentials |

## 6. Preservation and exclusions

Preserve immutable source/tag/pins, current working Test and all its private
state, Production plus its .31 backing, Factory .39/catalog/provenance, release
continuity, selected unsigned VDP archives and service build exports. Preserve
warm Builder/downloads/sstate, CARLA/Unreal source/content, compiled/shader caches,
all compact evidence, unrelated Docker resources and the separate video project.

Exclude from distribution: provisioned overlays, certificate/key/token contents,
Keychain entries, backend databases, service models/queues, run journals,
recordings/private media, scratch experiments, diagnostic core dumps and the
developer's generated launchers. Clean Factory is distinct from a Test disk.
No store was copied or credential opened for this inventory.

## 7. Risk register and bounded work packets

All packets below have a repository owner and an acceptance boundary. They do
not authorize unrelated UI changes, cloud publication or new identities.

| Risk / next packet | Owner and repositories | Required evidence / stop condition |
| --- | --- | --- |
| Standalone simulator feasibility and hidden Editor reads | Vehicle Simulation: CARLA; restricted Unreal only for a proved engine blocker; Gateway for launch adaptation | One bounded Town10HD_Opt candidate with all referenced maneuver assets; matching API; separate-location startup, telemetry/angles, Manual/Autopilot, both maneuvers, Return to road, cold/warm metrics and no source-tree reads. Stop if content/ABI/library closure fails |
| Native/application portability and on-demand compilation | Integration + Gateway | Prebuilt signed candidate hosts, private runtimes/library closure, stable existing orchestration API. Test a new path/user, no Xcode/Homebrew fallback, missing-dependency messages, layout/z-order and control ownership; no independent orchestrator |
| Reusable unsigned VDP and four service inputs | Platform + both services; Integration selects artifacts | Manifest-selected immutable inputs, no source-HEAD/old-checkout build requirement at operator Prepare; validate all functional profiles and provenance. Instance-specific signing remains separate. Update accepted packaging contracts before changing lookup semantics |
| Backend/container delivery and isolation | Both backends + Integration hosting | Immutable downloadable/exported images; clean import/start and health, storage/migrations, private sockets, existing-app preservation. Resolve Desktop licensing/runtime choice before first-use implementation |
| QEMU/firmware/Factory portability | Integration VM owner + Platform | Relocatable emulator/firmware closure and source/notices; clean .39 creation, unchanged machine type/security/overlay semantics. No guest rebuild absent a proved guest delta |
| Source/CI coherence | Integration | Added backend checkouts + pin regression pass locally; publish and observe a fresh hosted result later. Resolve legacy launcher assumptions without rewriting history. Preserve doc-successor distinction |
| Artifact provenance, redistribution and notices | Release owner with every component owner | Creation-time hashes/manifests, content pin, SBOM/license/source-offer review, authorized artifact storage and download integrity before external preview |
| First use, credentials, update/removal | Integration; operator for account/OS choices | Accepted state/credential/rollback contract, bounded install/repair/update/remove tests, no silent Finish/Cloud cleanup/release-number rollback. No copied developer secrets |
| Incomplete current behavioral qualification | Integration + Platform + Function Teams | Fresh serial .39 family cycle and Finish, readiness/profile observations, agreed negative/soak/recovery scope; no upgrade of focused receipts to full PASS |
| One-Mac clean testing and sleep/wake boundary | Release integration + operator | Separate-path checks first; later clean external boot with exact disk authorization and user setup. Host sleep/wake remains its own accepted packet, not proved by controller ignition |

### Immediate Stage 1 boundary

Start with the existing CARLA `carla-unreal-package-shipping` mechanism,
`CARLA_MAPS_TO_COOK` override and matching Python API build. Inspect the generated
UAT commands and dependency closure before execution. Preserve the qualified
steering fixes (`385927b6…` CARLA, `9b705d6…` Unreal), current running scene and
warm build directories. The main scene is Town10HD_Opt and ego Lincoln MKZ;
include actually referenced sensors/obstacles and map dependencies, not an
unproved single-asset whitelist. DefaultGame.ini currently lists five maps;
the override is available but a portable result has not been demonstrated.

Use a separate candidate output root, retain original runtime binaries and
observe free-space/memory limits. A live launch must not compete for the current
CARLA ports or tick/control ownership. If a switch is needed, preserve the
current run and schedule that bounded switch explicitly. Do not start a fresh
Unreal source rebuild or Factory build merely to begin this packet.

## 8. Completion evidence and remaining decisions

Stage 0 is complete **as an inventory and ownership gate**: runtime/build/user
inputs, exact known source/artifact identities, preservation, measured local
sizes, unknown download/peak sizes and distribution decisions have named owners.
The packaging gate is not complete. Stage 1 onward remain unexecuted.

Local verification completed:

- Documentation gate: PASS, 272 Markdown files, 658 stable IDs and 38 Mermaid
  blocks checked. An initially invalid report anchor was corrected and retested.
- Workspace/CI pin regression: 7 tests PASS.
- Documentation-check regression: 19 tests PASS.
- Inventory JSON parse and Git whitespace check: PASS.
- Confidential-input guard on tracked Git objects: PASS. All eight changed or
  untracked working files also pass the known confidential-input checks and a
  bounded common credential-marker scan; this is not a comprehensive secret audit.

No full source rebuild or hosted rerun is implied. The observed hosted
integration failure remains open until the local correction is published and
passes there. The workspace-doctor findings remain explicit, not suppressed.

Decisions not needed to start the local Stage 1 proof, but required later:
supported container runtime and entitlement; final installer/artifact-hosting
format; organizational redistribution review; application signing identity;
measured support envelope; state/update/rollback contract; exact external SSD
and clean-session window. No subscription purchase, EULA acceptance, disk erase
or public artifact release is assumed from this inventory.
