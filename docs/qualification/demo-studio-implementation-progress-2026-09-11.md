<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio implementation checkpoint — 11 September 2026

Status: **partial implementation; not ready for full operator E2E**.
The [accepted P1–P8 plan](../planning/active/demo-studio-delivery-plan.md)
and [10 September evidence](demo-studio-implementation-progress-2026-09-10.md)
remain the baseline. This continuation does not change the approved story,
native left-hand composition, Production scope or service trust model.

## Outcome by phase

| Phase | Current result | Still required |
| --- | --- | --- |
| P1 | Shared Test lifecycle source, current-state reentry and backend ownership/cleanup adapters | Complete scoped retire/fresh-run integration, including future service bindings |
| P2 | Normalized Cloud-only inventory, publication receipts, visible observer and resource view | Service-instance integration and observed metric coverage in the actual tenant |
| P3 | Previously recorded VDP18 and retained-Test Park/Resume proof preserved | Final fresh CLI story with the complete service-capable baseline |
| P4 | Initial Studio B2 workspace connected to existing lifecycle/VDP operations | Complete live UI repeat and operator visual approval; team product panels not connected |
| P5 | Brake native product source and ARM64 build; read-only service-input resource template | Token-directory ownership, pre-assignment manifest identity, SOTA tooling and real Brake ingestion chain |
| P6 | Brake v2/v3 profile implementation and focused source tests | Live assessment/advisory and independent consumer evidence |
| P7 | Independent Tire source and product backend; schema-aware cleanup integration | Raw-feature contract closure, ARM64 runtime integration and complete live/offline proof |
| P8 | Checkpoint/source consolidation in progress | Full clean-image and visual repeat; success-gated final cleanup |

## Presenter and Demo Control changes

- Approved automotive B2 assets are reused from mockup 2.8. Mockup files and
  native CARLA/Driving Control are unchanged.
- Page opening and navigation do not mutate the environment. Full story and
  Quick preparation remain explicit protected operations. Create starts Test;
  first simulator connection is stationary Manual. Provisioning can resume its
  unfinished membership stage even when Cloud already says provisioned.
- Park, Resume and Finish use shared Demo Control operations scoped to Test.
  Production remains excluded. Automatic release allocation is not an operator
  input. Existing native password/Keychain and confirmation boundaries remain.
- Current-run prepared/signed/submitted receipts survive page/server reentry.
  Previous-run jobs cannot select a candidate. Each profile retains its exact
  Cloud publication result when another profile is selected or published.
- Upload acceptance, Cloud publication and installed version are distinct.
  There is no required batch-approval button and no simulated successful update.
- Architecture, Platform and monitoring use normalized Aos Cloud reads, never
  guest diagnostics. Installed does not mean Running. Missing service data is
  not an empty inventory; absent metrics are not zero. A genuine zero DMIPS
  sample is retained. Stale data is marked and cannot cross Unit bindings.
- Monitoring is visible-only and has an explicit return to the vehicle map.
  Brake/Tire panels disclose that product integration is not yet connected.
- `democtl ui stop` stops only the identified idle Presenter process; it does
  not stop VMs, simulation or Cloud Units. It refuses uncertain/busy sessions.
- `democtl service runtime-inspect test` is an explicit engineering-only,
  read-only guest observation. It reports native ABI, selected declared mounts
  and public-input ownership/modes, never credential contents. It is not an
  HTTP/Presenter capability.

## Owned source revisions and product artifacts

| Repository | Revision | Scope |
| --- | --- | --- |
| aos-vehicle-platform | `161108b6e96ff1f43ecccc776f28a7792f4c73ee` | Opt-in per-service public metadata/CA resource template; no active recipe or VM change |
| brake-health-service | `8bae83066df071f5cb3bf7791ab6dedc00843d3d` | v1/v2/v3 product profiles, bootstrap, real KUKSA transport, durable recovery and capability readiness |
| tire-health-cloud | `c3b2d2aedffbf94e78c9a38bae45d5ba753e3765` | Independent product ingestion, query/storage and exact scoped cleanup |
| tire-health-service | `cb1bfca2180a747128ab65d24951d6d5d63ea1d8` | Independent runtime source with strict provenance and durable delivery; not live-qualified |

Platform, Brake and Tire backend revisions above were pushed to their existing
`alexmaninblack` working branches, without changing main or forcing history.
The new [Tire source repository](https://github.com/AlexAgizim/tire-health-service)
was published through the already authenticated GitHub Desktop account,
**AlexAgizim**, not alexmaninblack. An unauthenticated GitHub API read confirms
`private: false`; its remote `codex/studio-tire-runtime` matches the source
revision above. No account transfer, new credential or visibility change was
performed. The namespace difference is explicitly retained for owner review;
it must not be hidden by an incorrect repository link.

All three Brake ARM64 profiles were built successfully through
`democtl service build brake --content-profile v1|v2|v3`.
Each profile has a separate source-bound artifact path under
`demo-artifacts/aosedge-sdv-demo/services/brake/builds/<source-revision>/<profile>`.
ELF architecture and product test manifest are verified at this build boundary;
no image, binary or build output is committed to Git. The actual guest is
AArch64 with glibc 2.39, compatible with the built Brake binary's glibc 2.36
minimum. This ABI check is not evidence of successful service startup.

Executable message schemas accept canonical monotonic release numbers rather
than one hard-coded service version. They retain model/policy/profile semantics;
changing a Cloud release number does not redefine the functional contract.

## Tire backend integration

The new backend image is
`sha256:479c0dfe9c30bfc812995a86d8f6097ae22164364883e504cb26b69491e21685`.
It was built, explicitly stopped/activated/started through Demo Control, with
the existing volume and context preserved. Process startup succeeded; real Tire
service ingestion has not been demonstrated.

The immutable build/runtime record selects private cleanup protocol
`tire-product-v1`. Scoped preview/execute checks all six product record counts,
the exact retiring UID and nonmatching hash preservation. Single-Test volume
removal still needs schema-aware whole-store emptiness. Legacy foundation
records retain their foundation-only proof rather than claiming product
emptiness. Tests use disposable fixture stores; no live product data was
deleted in this continuation.

## Concrete P5 gates — no further bundle guessing

1. The existing KAC token-directory tmpfs requests mode 0700 without per-instance
   ownership. Native CM assigns a non-root service UID; native SM copies the
   resource mount options. The bootstrap requires its token directory to be
   owned by its effective UID. These inputs do not establish a usable private
   directory. No root service, guessed UID, broad chmod or SELinux relaxation
   was used. Close the exact native ownership mechanism before live assignment.
2. `serviceArtifactSha256` is the selected ARM64 OCI manifest digest, not the
   bundle, OCI index, layer or executable digest. The audited Cloud service
   version schema does not explicitly provide that value before assignment.
   Inspect the actual published artifact/response through a supported path;
   if it cannot supply the authoritative value, resolve this bounded ordering
   contract before implementing a fallback.

Details and pinned source evidence are recorded with the
[temporary service-input contract](../architecture/demo-control-service-inputs.md).
No new service identity, Subject binding or service publication was applied.

## Tire limits that must not be guessed

The accepted raw-to-normalized wheel-dispersion definition and slip-persistence
comparison boundary are not closed by the current source contracts. Tire
explicitly reports `MODEL_CONTRACT_UNRESOLVED` instead of inventing a result.
CPU-load-control wire/lease behavior, the complete recovery/overflow matrix,
live calibration, quotas and offline E2E remain unqualified. Existing fixture
success is not a complete P7 claim.

## Verification and preserved live state

- Demo Control: 500 tests passed in 77 seconds. Added publication-history and
  CLI-capability regressions subsequently passed in the focused 12-test suite.
- Presenter: 94 unit tests and production build passed. Browser tests cover
  exact profile receipts, registration continuation, Quick image reuse,
  zero-DMIPS monitoring, navigation, stale Cloud observations and protected
  prepare/sign/upload order. All three Studio cases pass after the preparation
  selector's accessible name was made explicit; the Cloud-observer case also
  passes. Browser fixtures do not operate real VMs/Cloud.
- Backend/retirement: the scoped Tire product and legacy cleanup fixtures pass,
  including nonmatching preservation and invalid/uncertain outcomes.
- Owning repository checks: Platform 47 tests, Brake four CTest targets,
  Tire native scoped tests and backend 11-test suite passed. These remain
  narrower than full functional/runtime/security qualification.

The last Cloud read at **01:04 UTC on 11 September** reports the same Test Unit
`2a29c145-bbd1-4494-a0e5-d4b79e6a9db5` Online with VDP **18.0.0 installed**,
no pending component and no services. The preceding independent guest evidence
in the 10 September checkpoint proves VDP18 running with 23 read paths; this
later Cloud observation is not a fresh process observation.

Factory `.31` and the Production peer are unchanged. The earlier qualified SM
override under `/run/democtl-sm-queued-recovery` remains intentionally retained;
a VM reboot removes it. Builder was not started. No Factory image, overlay,
Cloud release or historical source was deleted. Final destructive housekeeping
is deferred until the required complete successor passes.

Next: close the exact P5 native ownership and artifact-identity gates, complete
SOTA tooling and one real Brake chain, then the dependent advisory/Tire work.
Do not claim a morning-ready complete demo from these source checkpoints.

## Final source checkpoint and live UI read

Solution implementation commit `648082b88b58ed5df9b5a0a12f6d9aacf2cde485`
was pushed to `codex/demo-studio-implementation`. It includes source, English
documentation, tests and approved design assets, not compiled artifacts or
runtime/credential data. The documentation and confidential-input gates passed.
The pre-implementation return point remains unchanged.

The UI-only restart exposed the documented relative terminal invocation
`.venv/bin/democtl ui serve`. The stop guard now verifies the process's exact
canonical working directory before accepting this relative form. Four focused
tests cover it, a foreign directory/user, a busy session and the absolute form;
the nine-test stop/Cloud-reader suite passed. No broad process matching or
port-only signal was introduced.

The updated server started and `workspace restore` placed the owned windows;
VM, Cloud, CARLA and driving state were not restarted. The live page then
reported Test Online, VDP18 installed, three named components and empty service
inventory. At **01:34:58 UTC** its Cloud-only monitor returned a CPU sample of
**684 DMIPS** dated **01:34:18 UTC**. Memory/traffic retained their raw values
with units explicitly unverified; disk remained Not reported. A functioning
resource read is demonstrated, not complete metric-unit or product readiness.
