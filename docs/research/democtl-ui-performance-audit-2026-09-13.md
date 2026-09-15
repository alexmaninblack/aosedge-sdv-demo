<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: UI command performance audit

Date: 13 September 2026. Scope: the implemented Studio command/read paths,
their Demo Control compositions, and native Driving Control integration.
This is a source audit plus isolated regression/timing evidence, not another
live E2E qualification. No VM, Cloud object, published release or factory image
was changed for the measurements. Production remains out of scope.

The subsequently authorized [live command performance run](../qualification/democtl-live-performance-2026-09-13.md)
records actual VM/Cloud execution separately; its results do not turn the
controlled fixture timings below into a live before/after comparison.

## Outcome

Five changes remove avoidable work without changing the accepted demo flow:

1. Platform refresh overlaps independent Unit inventory, pending VDP publication
   and pending service publication reads, with at most three workers. Previously
   their network latencies accumulated serially. Mutations remain serial.
2. Service publication observation/preflight overlaps Deployment Bundle discovery
   with the service catalog/version path. It still reads the same authoritative
   records and enforces exact ownership, version and recipient constraints.
   The shared 24-request budget is now protected against concurrent increments.
3. VDP Prepare inspects the signed baseline once and constructs/compresses the
   package once. Baseline signature verification remains mandatory. Rebuilding
   the same bytes a second time to prove determinism moved out of the operator
   path; existing deterministic replay tests and new exact-byte tests cover it.
4. Studio treats publication `ERROR` as terminal, like `READY`/`FAILED`, instead
   of querying the same failed bundle on every inventory refresh. Explicit
   publication refresh is still available. This cache does not cache Online or
   authorize a mutation, and is keyed by version plus Deployment Bundle ID.
5. Service publication observation releases the environment writer lock while
   waiting for Cloud. It briefly reacquires the lock to save its observation
   only if the package and receipt are unchanged. Busy cache writes are skipped;
   changed/deleted receipts are not overwritten/recreated. Symlink checks remain.

## Measured results and limits

Three repetitions per case; medians shown. Cloud fixtures impose **80 ms per
independent remote stage**, with identical request counts before/after. They
measure scheduling, not actual Aos Cloud response times, TLS or authentication.

| Isolated path | Before | After | Difference |
| --- | ---: | ---: | ---: |
| Platform: three independent Cloud reads | 265.2 ms | 86.9 ms | 67% lower latency |
| Service: catalog → versions, plus independent bundle read | 257.8 ms | 178.5 ms | 31% lower latency |
| VDP construction/compression, 8 MiB incompressible fixture | 401.5 ms | 198.6 ms | 51% lower latency |

The VDP measurement excludes signing and version allocation. Tests separately
confirm unchanged package bytes, one baseline inspection and one signature
verification. It is not a benchmark of a newly released component.

Read-only local observations with process visibility enabled, in a warm Python
process, Test retired and Production preserved:

| Local path | Three samples | Median |
| --- | --- | ---: |
| `status all`, without `--guest`/`--cloud` | 182.4 / 192.1 / 173.2 ms | 182.4 ms |
| `image list` | 6.3 / 1.2 / 1.1 ms | 1.2 ms |
| `service releases` | 16.2 / 5.4 / 5.3 ms | 5.4 ms |
| Presenter local snapshot | 178.0 / 180.4 / 182.7 ms | 180.4 ms |

These exclude fresh CLI interpreter startup. Earlier sandbox-only ~10 ms
snapshot samples lacked full process visibility and are not representative.
No live Cloud latency, provisioning, simulator startup or disk-copy benchmark
is claimed. A 90-second timeout is a maximum budget, not a fixed 90-second wait.

## Read paths

Commands below are CLI equivalents. The UI backend calls the same application
API in process; it does not spawn the CLI for each local observation.

| UI consumer / command | Work and scaling | Decision |
| --- | --- | --- |
| Local snapshot: `status all` | One host process snapshot plus local journal/configuration/file metadata; no SSH, DNS or Cloud authentication by default | Keep. Approximately 180 ms locally; not the source of multi-minute Cloud waits |
| Firmware picker: `image list` | Catalog metadata and file existence; proportional to catalog entries; no full image checksum | Keep metadata-only |
| Prepared service cards: `service releases` | Bounded local receipt enumeration, at most 256 entries per team; no payload hash or signature worker | Keep metadata-only |
| Platform: `unit cloud-status test` | Fresh scoped Cloud observation; authentication, exact Unit identity, components/nodes/layers and service inventory; Subject details are already bounded/parallel | Overlap with publication reads; retain authoritative Unit result independently of publication failure |
| Pending VDP: `component cloud-status <version>` | Component/version/bundle discovery and scoped Unit information; paginated GETs are bounded | Overlap with Unit/service reads; stop automatic terminal-error polling |
| Pending service: `service cloud-status <handle>` | SP authentication, exact service/version/bundle discovery; optional local observation receipt | Parallel independent GET paths; release global writer during HTTP |
| Resource dashboard: `unit monitoring test` | Authentication, exact Unit identity, latest monitoring sample; three dependent GETs in the ordinary path | Keep visible/on-demand and coalesced; retain identity check and DMIPS semantics |
| Brake/Tire dashboards: `backend inspect <team>` | Owned container inspection plus one product HTTP read; product HTTP timeout 3 seconds, Docker commands have separate budgets | Keep scoped to requested team. No service build, restart or KUKSA claim |
| Cloud access diagnostic: `status all --cloud` | Explicit authentication/authority diagnostics for configured profiles; materially more expensive than local status | Keep explicit, not part of ordinary local refresh |
| Component diagnostics: `component inspect/verify/cloud-status <version>` | Inspect/verify read archive bytes; verify uses official signature worker; Cloud status uses bounded remote reads | Keep explicit diagnostics, not repeated as local status checks |

Polling is already visibility-aware: local refresh is every 10 seconds while
visible; Platform polling backs off from 2 seconds to 10 seconds while pending,
and uses 10 seconds when idle. In-flight reads are coalesced. Platform's server
also coalesces nearby reads. This audit does not replace authoritative reads
with a stale status cache or introduce another background polling loop.

## Operator commands and compositions

| Action / command | Potential time-consuming work | Optimization / retained boundary |
| --- | --- | --- |
| Create: `demo create --image <id>` → environment creation + Test/backend startup | Copy selected immutable factory image, verify its checksum, create overlay, boot and establish guest access/role/DNS; start existing backend images | Factory copy is the accepted contract. No new build or backup; checksum belongs at image adoption, not every status read |
| Quick preparation: `demo prepare --image <id> --target test` | Existing lifecycle stages, simulator/backends, Cloud provisioning and final guest baseline observation | Keep resumable stage receipts and stop-on-error; no new parallel mutations. Final guest probe is engineering preparation, not the Platform dashboard's information source |
| Start/stop Test: `vm start test`, `vm stop test` | Guest/SSH readiness, factory-role/DNS setup; graceful shutdown and process exit | Already starts requested VMs concurrently for `all`, exits readiness polling promptly, polls at 250 ms. Retain exact process/overlay ownership and graceful-stop budget |
| Simulator: `simulation start/stop --target test` | CARLA launch/readiness, native control/telemetry windows, source selection and workspace placement | Explicit Test scope retained. Simulator startup is not a VM rebuild/provision. Do not replace readiness with an arbitrary sleep |
| Connect: `vehicle initialize test`; reconnect/switch: `vehicle select test` | Source gate, selected-role state, guest source configuration and CARLA readback; switching may reset world | Existing invocation-scoped connection reuse/no-op path retained. Do not remove source-role isolation or permit two VM consumers of CARLA |
| Provision: `unit provision test` | Official SDK once, exact Cloud identity lookup, Test Unit Set membership, Online observation | No blind SDK retry. Online wait is evidence, not artificial delay; worker wait budget defaults to 90 seconds, polling at 2 seconds |
| VDP authoring: `component prepare --profile <v1/v2/v3>` | Fresh release allocation, signed baseline inspection/verification, replay and compression | Removed duplicate inspection and duplicate complete construction/compression. Keep monotonic version allocation and exact content checks |
| VDP publishing: `component sign <version>` → `component upload <version>` | Signing/verifying package, OEM authority and recipient preflight, one Deployment Bundle upload | Keep signature and exact recipient checks at trust boundaries. No automatic VM build, approval or install wait |
| Service authoring: `service prepare <team> --profile <profile> --without-permissions --demo-mocked-data` | Validate committed ARM64 export, allocate release from fresh SP catalog/continuity ledger, create package and schema validation | No implicit Docker build. Keep synthetic-data/permissions flags and package integrity |
| Service publishing: `service sign <handle>` → `service upload <handle>` | SP identity/version/recipient preflight, signed content, one Deployment Bundle upload | Independent preflight GETs now overlap. All mutation checks and one-attempt accounting remain |
| First Deploy: `service runtime-prepare test` → `service assign <service-id> --target test` | Public input preparation, scoped Group Subject/service association and assignment to current Test | Keep ordered; assigning before inputs are ready reintroduces a demonstrated launch defect. No Safe Stop dependency for services |
| Backend stack start/stop, composed by lifecycle | Existing owned images/containers, health observation; Compose uses `--no-build --pull never --wait` | No implicit build/pull. 60-second health budget is not a mandatory delay. Team mutation order remains serial |
| Park/resume: `environment park/resume` | Selected source and simulator/VM/backend lifecycle with retained identity | Retain pending-operation/ownership checks. No deprovision/rebuild/copy on ordinary resume |
| Finish: `demo retire` | Scoped Test shutdown, authoritative Offline/deprovision/delete/absence, then owned local cleanup | Preserve ordering and Production exclusion. Do not fake Cloud Offline or delete while identity is unresolved |
| Internal lifecycle: `unit deprovision/delete`, `environment retire` variants | Authoritative mutation/readback and validated stopped-file cleanup | These are existing stages, not additional generic preflight wrappers |
| Native Driving Control: `vehicle connectivity status/off/on` | Selected-role/identity and network-filter readback; preserves management/local telemetry paths | Keep firewall/selection checks. No Cloud restart or reprovision as a connectivity command side effect |
| Host infrastructure: `ui serve/stop`, workspace restoration, native access | Session capability, idle-stop check, loopback server/native layout and first-use guest access | Keep small local checks. Do not restart a busy operation to apply an optimization |

Autopilot, Manual and Safe Stop buttons use the existing CARLA control path,
not repeated `democtl status`/Cloud calls. Native telemetry reads vehicle data;
Platform inventory continues to use Cloud only.

The protected bridge also accepts individual `component unpack/sign/upload`
and diagnostic actions. These are explicit engineering actions, not hidden
steps on every dashboard refresh. Unpack is proportional to archive size and
retains safe-path/integrity checks. Build, factory creation and other CLI-only
engineering workflows are not newly added to the normal demo path.

## Remaining costs, deliberately not hidden

- Each isolated Cloud worker establishes TLS credentials and verifies
  `users/me/` authority. Parallel reads reduce latency but do not reduce this
  authentication count. Longer-lived cross-request credential/role caching
  would change revocation and isolation behavior and is not introduced here.
- Network failure can consume a 12-second HTTP timeout per call. Higher-level
  worker budgets differ (for example service publication 90 seconds and Unit
  observation 60 seconds). The Platform browser request budget is 35 seconds,
  so prolonged remote failure can still show unavailable while a worker is
  finishing. There is no newly introduced retry; this remains a bounded
  failure-path/UI budget mismatch, not evidence of an intentional delay.
- Publication workers still perform their own exact identity reads. Further
  request consolidation should be an explicit combined observation boundary,
  not removal of checks or an invented Cloud endpoint.
- `vm stop` hashes an overlay only when the guest reports unprovisioned, to
  bind a stopped-unprovisioned cleanup proof to its bytes. Local retirement
  rechecks that proof when no authoritative Cloud-retirement proof exists.
  Cloud-retired cleanup has a separate branch. This can cost disk time for a
  large overlay; it was not removed because it authorizes irreversible deletion.
- Factory adoption copies/hashes the chosen image. Local catalog/status reads
  do not. Removing the accepted copy or weakening cleanup identity is not a
  performance fix in this increment.
- Service/VDP uploads may legitimately leave Cloud processing or the component
  pending Safe Stop. Services do not require Safe Stop. These external/runtime
  states are not converted into success or retried merely to shorten a command.

## Verification and source map

Focused regression set: **310 tests; 304 passed, six skipped**, in 7.55 seconds,
across component, service, Presenter and Cloud observation families. Skips require
the optional official SDK/signer or certificate-parser test runtime; no dependency
installation/build was added to this increment. Tests use temporary packages/journals, mocked SDK/Cloud/guest calls
and temporary localhost servers; they do not execute a live lifecycle.

New proofs cover concurrent read barriers with unchanged call counts, terminal
publication errors, independent Unit Online evidence, deterministic VDP bytes,
failed baseline signature rejection, non-blocking service observations and
concurrent/removed/symlinked receipt protection. The mutation request budget,
ownership/pagination/recipient tests remain in the suite.

- [UI action plans](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter_operations.py)
- [Presenter observations](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter.py)
- [VDP preparation](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/components.py)
- [Shared bounded Cloud reads](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/component_publication.py)
- [Service publication](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/service_publication.py)
- [Service package/receipt operations](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/service_packages.py)
- [Cloud transport and lifecycle worker](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/unit_cloud.py)
- [VM lifecycle](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/vm.py)
- [Cleanup proof](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/environment.py)
- [Accepted demo-control contract](../architecture/demo-control.md)
- [Current delivery plan](../planning/active/demo-studio-delivery-plan.md)

This increment does not close the remaining clean operator/visual acceptance,
real permission-backed KUKSA/advisory, or upstream Cloud ordering items.

## Follow-up: repeated guest checks

Implemented after the live performance run, under the operator's separate
optimization request. No VM, Cloud identity, release or deployed manager was
changed. These source changes do not retroactively alter the measured results.

| Path | Before | After | Retained boundary |
| --- | --- | --- | --- |
| `vm start`, first/repeat | Separate readiness SSH and role SSH, plus role-session teardown | One guest call runs readiness then existing role reconciliation | Fresh DNS, pinned host key, exact role; ambiguous completion fails without blind retry |
| `service runtime-prepare test` | Full engineering runtime/container/process inventory before native identity reconciliation | Identity-only guest projection; fresh official IAM RPC unchanged | Exact native/provisioned identity; activation and explicit inspection keep the full view |
| Unchanged public service inputs | Three slot/process snapshots and two directory syncs despite no file replacement | Two snapshots; no post-write check or directory sync when nothing changed | Source-race, transaction, role, slot/process, trust and path/mode guards |
| `backend inspect/status` during upload | Read-only observation takes global writer and can return busy | No writer acquisition; validate current binding across observation | Owned container and Test scope; changed binding rejected; mutations remain serialized |

Regression result: **333 tests, 327 passed, six skipped, 25.641 seconds**.
The affected VM/access, service/backend, source, simulation/lifecycle and
Presenter families run against temporary files, protocol fixtures and test
doubles. Skips need optional official SDK/signer or certificate-parser runtimes.
Additional proofs execute the combined shell with simulated DNS success/failure,
count one guest call per role on first/repeat start, reject uncertain role
completion, preserve active-transaction and source-race failures on unchanged
inputs, omit container forensics for preparation, retain full activation
inspection, and read a running backend under another thread's writer lock.
`git diff --check` passes. The idle UI server is reloaded through `democtl` only.

There is no new live before/after timing claim: the benchmark's Test environment
was already retired, and Production was not used to measure the optimization.
The next authorized Test cycle can measure the resulting wall-clock improvement.
