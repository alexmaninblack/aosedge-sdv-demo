<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio implementation checkpoint — 10 September 2026

Status: **partial implementation; not ready for final operator E2E**.
The [accepted P1–P8 plan](../planning/active/demo-studio-delivery-plan.md)
remains authoritative. No mockup flow or live Presenter composition was changed.

## <a id="resumed-execution"></a>Resumed execution — 10 September, supersedes the initial gates below

The user authorized scoped current-Test deprovision/delete, owned data/overlay
removal and a fresh Test from the same `.31` image. Existing Production and
shared dependencies are preserved. Source branch publication was separately
authorized to the existing Solution, Brake Cloud and Brake Service GitHub
repositories, with no force-push or main-branch changes. The Tire repository
was created at `alexmaninblack/tire-health-cloud` and verified **public** after
the user's public-only repository rule. Its source push was rejected by
execution review because repository creation did not explicitly authorize that
source export. No alternate export was attempted; local work is unaffected.

- Docker is now available. Real `democtl backend build/start` succeeded for
  both teams. Tire image: `sha256:8dac4d0e6a40090010a0242082e907931a01cd66937ed60a35aef6f09ea22895`
  from `565c3da`. The updated Brake image is
  `sha256:48eb81d1caec2b2fa51207e3a3405b5ba83210ed315ae7ef042909ce41fb7966`
  from `6a5889d`. Explicit Brake stop/activation/start passed without deleting
  its database. Process health is not product qualification.
- Fresh OEM/SP access reads passed. Both profiles are valid; the visible
  service catalog contains three existing non-demo services under the one
  configured SP, and no Brake or Tire service. This proves usable access, not
  an agreed independent Tire authority mapping or permission to create roles.
- Test was observed external-connectivity **OFF** through the existing owned
  fault control. Host DNS answered; SSH and all three Aos daemons worked.
  There is no evidence requiring another image rebuild for DNS.
- Test-only retirement/recreation leaves Production, shared DNS and factory
  identity unchanged in fixtures. Full-story Create, Park/Resume and scoped
  Retire now use the shared application boundary. Cloud-only inventory is
  consulted before shutdown; an uncompleted/unknown update refuses before
  automatic Safe Stop. Quick preparation also starts both prepared backends
  and permits a preserved Production peer without provisioning that peer.
- Combined Demo Control suite passed **395 tests** (63.460 seconds) before
  the final retirement/Quick-preparation additions. Subsequent focused suites
  passed: backend lifecycle/activation 19, Studio lifecycle 16, Quick
  preparation 7, source handover 15, simulation 24, Brake Cloud contract 17.
  Scoped cleanup tests and later full-suite results are recorded at the next
  integration checkpoint; these fixtures are not a live E2E claim.
- Final integration checkpoint: **425 Demo Control tests passed** in 55.154
  seconds; Brake Cloud contract tests passed 17/17. Documentation validation
  passed for 165 Markdown documents, 658 stable identifiers and 38 diagrams;
  `git diff --check` passed. No live VM/Cloud action is implied by these fixture
  suites, including their mocked Builder progress output.
- Brake backend source `6a5889d`: 39 tests, compile/typecheck and quality
  gates passed. Private Test-scoped cleanup preserves nonmatching records;
  whole-store emptiness requires schema/integrity proof, not a missing UID.
- Brake service source `6fb8e02`: bootstrap and domain/input tests passed
  (4 CTest targets plus two repository-boundary tests). The real gRPC adapter
  exists in source but is **not yet compiled or deployable**. Pinned Linux
  ARM64 dependency assembly and authoritative service-visible metadata/public
  KUKSA TLS leaf delivery remain real integration work. No insecure fallback,
  guessed UID, private-key exposure or Factory rebuild was performed.

The real scoped `democtl demo retire` reached confirmed Test deprovisioning,
graceful VM shutdown and deletion of the Test Unit and its Node. Cloud steps
are recorded complete and must not be replayed. Brake's exact-Test record
counts are zero; Tire's result is foundation-only, not a product-data claim.
Both backend containers are stopped, their storage retained. Local cleanup is
**PARTIAL** at `retire-test-data-and-overlay`: `CLEANUP_FILE_IN_USE` while
removing the old current-Test context. Its removal receipt is `REMOVE_PENDING`.
The context and old Test overlay have not been declared removed. Do not
delete them outside Demo Control or weaken the open-handle check. No retirement
process remains running; the journal is the recovery authority.

The two preceding integration defects were corrected: the legacy journal's
known `workspace` field is preserved, and exact Docker Desktop `/host_mnt`
aliases are accepted for the owned read-only context bind on macOS only.
The cleanup regression suite passes 24 tests. These fixes do not override an
actual open handle or authorize removal of a foreign path.

Production's Unit identity, overlay and shared factory/DNS resources remain
outside the retirement target. Its current runtime/Cloud availability has not
been independently re-qualified by the cleanup result. No fresh Test was
created and no new VDP/service release was published in this resumed cycle.
P3–P8 and final visual acceptance are not complete.

### Current decisions needed for full service E2E

- Approve or supply the bounded platform-owned, read-only service metadata and
  public KUKSA TLS trust interface described in the delivery plan. Native
  service identity alone does not supply Unit role, artifact provenance or
  active VDP contract evidence. An exact proposal must identify the producer,
  fields, resource mapping and transient Test proof before any guest change;
  this is not permission for a Factory rebuild or broad service access.
- Establish the Tire publication binding: the accepted plan requires separate
  team-SP authority, but only one configured SP profile has been observed.
  Sharing that profile would amend the accepted authority model; no such
  amendment or credential creation is inferred.
- Explicit Tire source publication permission remains separate from creation
  of its public repository. The rejected source push was not retried.

ARM64 dependency assembly, service packaging, Brake/Tire product wiring and
the P4–P8 implementation remain engineering work even after these decisions.
There is no basis yet for promising a completed morning visual review.

The sections below preserve the initial checkpoint and its then-current
evidence; Docker, repository and cleanup-authority statements there are
historical, not current blockers.

## Return point and owned changes

The remote pre-implementation checkpoint remains
`pre-studio-implementation-2.8-2026-09-09`, Solution commit
`b997e6e6cffba02b61a588c40f14dba30942d17d`.
The implementation branch is `codex/demo-studio-implementation`; `main` was
not advanced. Source increments are isolated from Factory images and runtime data.

| Repository | Implemented source boundary | Local checkpoint |
| --- | --- | --- |
| `aosedge-sdv-demo` | Test-targeted preparation, initial Manual operation, release continuity, backend context/lifecycle primitives, Cloud-only reads, publication reconciliation, image support reader/producer | `619d107`, `755125d`, `f196a20`, `58a9116`, `eb25666`, `5b61970`, `bdee1b2`; later commits on the same branch contain metadata-only registration and this checkpoint |
| `brake-health-cloud` | Current Test context with optional Production, durable backend, private scoped cleanup, Docker recipe | `f55bd74` |
| `tire-health-cloud` | Independent process/SQLite/context foundation and Docker recipe, not product ingestion | `565c3da`; new local repository, no remote configured |
| `brake-health-service` | Host-tested Brake v1 composition and bounded transport primitives, not a deployable service executable | `dca3190` |
| `aos-vehicle-platform` | Unchanged | `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` |
| `carla-ego-runtime` | Unchanged | `f506e4b206725317c83346c4f46069235ca8f038` |

No image, bundle, executable, database, credential or temporary socket was
committed. No implementation branch was pushed: execution review denied the
push without explicit approval of the exact remote destination. No alternate
export route or force-push was attempted.

## Evidence actually obtained

- Full combined Demo Control suite with the metadata-only increment: **342 tests
  passed** in 57.910 seconds, using local fixtures, not a live VM/Cloud lifecycle.
  A final secondary-manifest conflict regression was subsequently added and the
  complete eight-test metadata suite passed again.
- Subsequent backend ownership/error tests: **10 passed**; context tests: **6
  passed**, including the non-secret read-only container export. Image/create/retire tests: **40 passed**, including the new
  declaration reader. Initial sandbox process-listing denials were resolved
  by running the same fixture suite with permitted process reads; product
  logic was not weakened.
- Eight Factory producer/migration tests and five unchanged runtime tests passed.
  The explicit metadata-only registration on .31 passed and an intentional
  repeat returned `noOp=true`. It registered 23 source-derived read paths,
  preserving image bytes, recorded SHA and qualification state; no Builder ran.
- Brake Cloud: 34 backend tests, four architecture groups, typecheck and
  source gates passed. Tire: four lifecycle groups passed. Brake service:
  three CTest targets (domain v1/v2 and seven runtime groups) passed.
- Confidential-input and documentation-quality gates passed at local commits.
- Actual `democtl unit cloud-status test` and `unit monitoring test` performed
  only bounded Cloud reads. At 2026-09-09 15:32 UTC, Cloud reported the current
  Test Offline, VDP **15.0.0 installed**, no service rows, and no resource
  samples. Missing samples remain unknown. This does not assert VDP Running.
- Actual `democtl component cloud-status 15.0.0` reconciled the recorded bundle
  as `done`, its exact catalog version as `Ready`, and publication as `READY`
  at 2026-09-09 16:07 UTC. The Unit remained Offline; no publication was replayed.
- Actual `democtl backend build brake` and `... tire` stopped before
  compilation. A subsequent `backend status brake` confirmed
  `BACKEND_DOCKER_ENGINE_UNAVAILABLE`; no container, volume or new image was
  created. Docker build/start/restart and guest-routing tests are not passed.
- Actual `democtl demo plan --image 6.1.1-maninblack.31/main-qemuarm64 --target
  test` returned the expected existing-role conflict. The old two-role run
  was not silently converted or destroyed.

## Live state deliberately preserved

The existing Test/Production run, Cloud identities, selected Test, simulator
assignment, overlay disks, factory copy and immutable source image remain.
No provisioning/deprovisioning/delete, source switch, Cloud upload, validation
approval, service assignment, VM restart or backend start was performed.

Factory `.31` remains SHA256
`a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4`.
Only its producer compatibility metadata was added through Demo Control;
`BUILT_NOT_LIVE_QUALIFIED` and the original image binding were retained.
No broad disk cleanup was performed. Existing Builder/cache and unrelated
CarlaSim scratch directories were preserved. Isolated source worktrees are
retained until their changes are integrated and qualified.

## Work that remains, not completion claims

| Phase | Current boundary |
| --- | --- |
| P1 | Source primitives and image registration implemented/tested; complete composed lifecycle, exact backend R0 and Docker live proof remain |
| P2 | Cloud inventory/monitoring and publication reconciliation integrated/fixture-tested; actual inventory and historical bundle reads passed; new live publication and Presenter observer remain |
| P3 | Not qualified: fresh Test CLI lifecycle, v1/v2/v3 transitions, Park/Resume and Retire still required |
| P4 | Not started: no new UI bound before P3 passes |
| P5 | Not deployable: Brake product process/bootstrap, KUKSA adapter and authoritative runtime bindings are incomplete |
| P6–P7 | Product advisory chain and real Tire algorithm/service/backend remain unimplemented |
| P8 | Not started: no full fresh-run/repeat/visual acceptance or final housekeeping claim |

## Bounded decisions before the next live stage

1. **Make Docker engine available.** The accepted startup preflight fails
   closed; this increment does not silently start Docker Desktop or substitute
   native backend processes.
2. **Resolve the pre-existing two-role run.** The new Test-only default cannot
   assume permission to delete the preserved Production VM/Unit. Select an
   explicitly authorized migration/retirement scope before the fresh P3 run.
3. **Close service runtime bindings.** Native IAM provides Unit system identity,
   but `.31` has no accepted service-visible combination of role, service
   artifact provenance, active VDP contract/digest and KUKSA public TLS trust.
   See the evidence table in the delivery plan. A read-only, platform-owned
   metadata/trust resource is a proposed bounded interface change, not an
   implemented or approved fallback. Do not bake a current Unit UID into a
   reusable package, substitute expected VDP metadata for active state, disable
   TLS, expose private keys or rebuild the Factory image implicitly.
4. **Bind Tire SP authority.** Only one configured SP credential/profile was
   observed. Independent Tire publication authority is not established; no
   credential/role creation or Brake-profile reuse has been assumed.
5. **Approve exact remote publication destinations when resuming push.** Local
   source commits exist, but sending repository contents remains blocked by
   execution review; the new Tire repository also needs an approved remote.

These are separate from ordinary remaining source tasks. Docker availability
alone would not make the unfinished product stages or full demo qualified.
