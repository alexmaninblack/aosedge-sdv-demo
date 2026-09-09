<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio B: action, transition and integration audit

Review package: [Mockup 2.6](../demo/mockups/aosedge-demo-interaction-mockup-2-6.html),
[experience proposal](../demo/mockups/demo-experience-proposal.md) and
[proposed delivery plan](../planning/active/demo-studio-delivery-plan.md).

Audit date: 8 September 2026. English translation: 9 September 2026. Status: **audit for agreement, not a record of completed implementation**. Working documents are maintained in English regardless of the discussion language.

Scope: the [accepted interactive mockup](../demo/mockups/aosedge-demo-interaction-mockup-2-6.html), its [transition logic][mock], the actual Demo Control / Presenter / Native Driving Control working code, and the public [Aos Cloud OpenAPI][openapi], `info.version = 6.1.53`.

This audit did not start, build, publish or change anything in the VMs, Cloud or applications. It inspected source code and the public API schema. Live responses from our tenant, its current user permissions and its deployed API version **were not checked**. Public schema version 6.1.53 does not prove that the tenant is running that release.

<a id="current-re-audit--9-september-2026"></a>

## Current re-audit — 9 September 2026

### Final disposition after Subject/package acceptance

**Design review complete for the bounded Test Studio milestone.** No further
operator/product choice remains open in this review. Implementation and live
qualification are not complete or authorized by the audit. The 28 integration
gaps below are work items, not 28 questions to reopen or a reason to rebuild
the VM. Previously passed infrastructure checks must not be repeated at every
release.

Final verification on 9 September 2026:

- **27/27 mockup regressions passed again**, including the standalone browser
  sequence using actual buttons for all VDP/Brake/Tire profiles, Offline,
  Park/Resume and Retire. Browser requests were intercepted; no live tenant,
  demo process or existing browser profile was used.
- All **78 action IDs** and **28 gap IDs** are unique and accounted for. Removed
  2.5-only controls retain explicit retired rows. The current source and
  standalone contain the same state machine.
- Public OpenAPI **6.1.53** was re-read: Subject creation has `is_group`;
  assignment accepts `service_ids`, attachment accepts `system_uids`. No
  service-version or instance-count selector is accepted by those payloads.
  The tenant's actual capability/permissions remain one bounded integration
  check, not an unverified claim in this report.
- Re-read the description tables for service configuration and state management:
  minimum instances/lifetime belong to service configuration; Group Subjects do
  not synchronize vehicle-modified service state back to Cloud. P7D does not
  replace durable product queues or scoped record cleanup.
- Rechecked current Demo Control source: dual-role preparation/guards,
  approval-dependent recovery and missing service/backend lifecycle integration
  still match the recorded implementation gaps. The existing writer supports
  same-thread composed calls and rejects competing writers without waiting;
  a new lock or another orchestration wrapper is not required.

| Boundary reviewed | Final contract / first implementation responsibility |
|---|---|
| Create → backend context → Provision | P1 starts backend processes/storage without a Unit context. Context-dependent queries remain explicitly unavailable until provisioning returns the exact Test UID. Health does not claim query readiness. No need to provision before backend process startup. |
| Backend context → Retire | Preserve the retiring UID selector until owned record cleanup succeeds, including after Cloud Unit deletion. Then clear context and stop backends. Migrate the two-role JSON profiles and handlers/tests together in P1. |
| Initial Manual connection → Provision | P1 narrows only the provisioning source guard. Preserve the separate deprovision/delete detach rule. No artificial stop/restart or reconnect to publish. |
| Publication → delivery → terminal observation | P2 separates bundle processing from Unit outcome, needs no batch approval for verification Test, and accepts terminal expected state without a missed Pending sample. No second service Deploy for an already assigned identity. |
| Repeat → retained Subject/catalog → fresh releases | P1 ledger survives cleanup; P3 resets owned Subject assignments before the next first Deploy. The default Full story publishes fresh v1 content; the optional warehouse variation may publish higher content before Provision. |
| Package request → actual instance | P5 applies the accepted one-instance/P7D configuration through the real package adapter, then observes expected version and instance runtime. A setting or successful assignment is not runtime proof. |
| Cloud monitoring → native telemetry → backend results | Keep all three evidence sources separate. CPU is DMIPS. Unknown and stale are not successful; VDP Installed does not establish process health. |
| Failed update / shutdown | Basic truthful refusal and known-operation recovery remain required. Terminal failed-install intervention, expanded diagnostics and parallel mutation remain explicitly deferred; no automatic campaign-stop or cancellation claim. |

**Change record:** class B acceptance/contract clarification within existing
actors and authority. Owning source: UI-STUDIO-026. Updated affected interaction,
action audit, delivery plan, Demo Control design, mockup register and traceability.
Revalidated unchanged: mockup source/standalone, tests, current lifecycle/package
source and executable backend profiles. No application/package/schema change,
live action, Git checkpoint or deletion was performed. Existing stable anchors
are preserved. The next authorized work starts at Studio P1; this final audit
does not start it automatically.

Current review artifact: [Mockup 2.6](../demo/mockups/aosedge-demo-interaction-mockup-2-6.html).
The 78 action IDs and G01–G28 are retained for traceability; they are not 78
implemented commands. The [UI-STUDIO-026 contract](../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract)
and [reconciled phase order](../planning/active/demo-studio-delivery-plan.md#current-reconciled-sequence)
replace the earlier Test/Production, approval and phase-order assumptions.
No live tenant calls, guest changes, packaging or application implementation
were performed by this corrective review.

### Mockup defects, resolution and coverage

| Finding | Correction in 2.6 | Isolated regression evidence |
|---|---|---|
| Guide returned to older profiles after they had been replaced | Retain observed completed chapters per run; a newer observed profile may skip an older chapter without claiming it was demonstrated | Full profile story terminates; terminal observation without Pending |
| Reload during Park could offer factory startup and reset installed VDP | Save completed operation stages; resume remaining Park steps; startup never overwrites installed software | Partial Park/Resume and repeated interruption preserve VDP |
| Reconcile could turn Processing into Published | Separate persisted simulated server outcome/deadline from client observation; reconcile same deployment ID | Processing stays Processing; lost response uses one bundle; rejected Quick does not provision |
| Service Starting could remain unfinished after reload | Resume the recorded startup observation rather than replaying installation or claiming immediate Running | Starting → Running after reload |
| Online outbox receipt could be lost on page reload | Resume outstanding delivery on entry; retain event IDs and deduplicate durable receipt | Online reload and offline/reconnect exactly-once receipt |
| Old live advisory survived service/source changes and never expired | Clear by version/generation/restart and enforce the 30-second QM lease ceiling; backend history is separate | Expiry, changed profile/generation and Resume |
| Provision could report Online while external link was off | Registration, Online and membership remain separate; recover incomplete registration on the same identity | Disconnected Provision and membership recovery |
| CPU displayed fabricated percentages | Use explicitly simulated DMIPS; remove ungrounded capacity-percent bar | Standalone rendering inspection |
| Warehouse variant was not represented by the guide prerequisite | Any published eligible VDP can permit Provision; default Full story still introduces v1 | Publish v2 before Provision and install v2 without a false v1 completion |

Result: **27/27 tests passed**, including the opt-in standalone browser full-story case. Documentation quality gate and whitespace check passed.

Reproducible isolated state tests:
`node --test tests/mockups/mockup-2-6.test.cjs`.
These tests operate on the actual mockup logic with an isolated clock/storage;
they do not invoke democtl or any external service. Browser checks additionally
exercise the standalone document's DOM/rendering. Existing browser run data is
not deleted. Old 2.4/2.5 artifacts are preserved.

**Remaining scope boundary:** terminal failed installation may leave Park/Retire
blocked until engineering intervention. The user explicitly deferred complex
failure handling; the mockup must not pretend such a failure was cancelled,
rolled back or recovered. Expanded logs/errors and concurrent foreground team
mutations are later work, not current release gates. Basic processing rejection,
response-loss recovery and prompt truthful refusal remain covered.

<a id="subject-and-package-proposal"></a>

### Accepted Subject and package settings

The user explicitly **accepted** the retained Group Subject and both package
settings on 9 September 2026. The canonical decision is in
[UI-STUDIO-026](../demo/mockups/aosedge-demo-interaction-specification.md#accepted-subject-and-service-package-settings--9-september-2026).
The earlier proposal anchor is retained for stable links. Acceptance is a
design decision, not an assertion that Cloud or packages have been changed.

| Item | Accepted setting / integration rule | Evidence and consequence |
|---|---|---|
| Subject type | Dedicated reusable **Group Subject**, `is_group: true`, limited by our tooling to the single current Test | Group has no Unit-to-Cloud service-state synchronization; non-group supports transferable user state. This demo is vehicle-scoped, not a roaming-user session. [State Management](https://docs.aosedge.tech/docs/aos-cloud/components-view/state-management%20component) |
| Existing Subject | Read exact retained UUID/type/ownership once at authorized setup; reuse only a matching dedicated object | Never convert/delete a factory NodeType Subject or guess ownership by its title. A mismatch is reported for decision, not silently changed. [Unit ontology](https://docs.aosedge.tech/docs/reference/ontology/unit) |
| Service assignment | OEM binds exact `system_uids:[UID]`, then adds only requested `service_ids:[S]`; verify both bindings and instances | Service UUID, not version UUID or `numInstances`; preserve peer Brake/Tire assignment. Public OpenAPI 6.1.53 |
| Instances | Both packages: `instances.minInstances: 1`; expected one main-node instance on this single-node Test | Instance demand belongs in the service configuration. Confirm actual instance IDs/run state from Cloud, not a hardcoded zero. [Service configuration](https://docs.aosedge.tech/docs/reference/file-formats/service-config) |
| Offline lifetime | Both packages: explicit `offlineTTL: P7D` | Seven-day offline lifetime, not infinite retention or a platform default. Short offline episodes and overnight Park are within the chosen limit; do not promise preservation across a longer offline period. |
| Runtime/package | arm64; real executable `configuration.cmd`; only required runtime layers and node labels; declared KUKSA/resource permissions | The Brake scaffold currently prints a placeholder; metadata alone cannot make a product service run. Validate against selected image capabilities before packaging. |
| Resources | Reuse measured/declared package requirements and verify quotas; express CPU demand/limit in DMIPS | Do not invent quotas to obtain a green UI. Brake scaffold's current quotas are not qualification of future algorithms. |
| Product state | Local durable queue/storage, event identity and backend records; no dependency on user-Subject migration | Preserve across Park/service update as required; clear owned ordinary run data at Retire. Confirm actual image/runtime storage behavior in P5. |

If cross-vehicle user-state migration becomes a requirement, reconsider a
non-group Subject explicitly. It is not needed for the current demo. Neither
Group semantics nor an offline TTL replaces backend persistence/cleanup.

### Integration gaps remaining after correction

| Gap group | Current disposition / exact next work |
|---|---|
| G01–G04, G21 | P1/P3: Test-only preparation; running pre-provision upload; preserve initial Manual connection; remove mandatory verification approval; current-read rather than stale READY no-op |
| G05, G07, G11–G12, G14 | P2: component Installed is distinct from runtime; service list **and detail** with actual instance version/run_state; paginated bundle processing; DMIPS/freshness/shared observer. Public schema does not establish VDP process health. |
| G06, G28 | P1/P2: recipient scope and host access independent of vehicle Online; trusted OEM monitoring projection with SP-scoped views; tenant permissions/version still require one authorized integration read |
| G08–G10, G25 | P1/P5: durable per-identity automatic release ledger; coherent profile metadata; actual SOTA package/commands and Subject bindings. Group type, minimum instances and TTL are accepted; implementation/qualification remain open. |
| G15–G17, G22, G27 | P1/P3: shared Park/Resume/Retire, exact owned cleanup, resumable journal; one unfinished update per identity; no duplicate upload or forced cancellation |
| G18–G20, G26 | P1 backend lifecycle/context/storage first; P5–P7 real product runtime/records/advisory/offline. Backend HTTP profiles currently require two roles: migrate contracts and handlers together before the Test-only path depends on them. |
| G13 | Expanded Cloud log request/list/download UI deferred; preserve raw errors and uncertainty for core actions now |
| G23–G24 | P8 qualification and scoped observation cadence. No mock-only pass closes real E2E or authorizes a VM rebuild. |

Current call order: Create+boot+backend preparation → initial Manual connect →
VDP Prepare/Sign/Publish (v1 normal, newer profile permitted) → official
Provision → Online → verification membership → delivery/vehicle Safe Stop.
First service Publish → exact Test Subject binding → service identity assignment
→ installed expected version and instance Running → independent product result.
Later Publish update has no version-specific Deploy or batch approval gate.
Retire first quiesces producers, retains VM availability for deprovision, observes
Offline/revocation, stops VM, clears owned Set/Subject bindings and deletes Unit,
then clears backend records, stops backends and removes working files. The
backend context survives until scoped record cleanup; release continuity survives
the whole Retire. These are target shared operations, not existing capabilities.

## 1. Conclusion

Connecting the mockup to the current backend requires more than replacing timers with calls.

Operations already exist for images, VMs, provisioning/deprovisioning/deletion, the simulator, vehicle selection, external connectivity and VDP. However, the accepted scenario conflicts with current restrictions: one Test vehicle versus several requirements for two VMs; immediate boot during Create versus pre-provision upload restricted to a stopped environment; and unnecessary approval in automatic preparation. Service operations, full Cloud monitoring and product backend screens are not fully integrated.

The essential status distinction is: **Cloud accepted the file ≠ bundle processed ≠ assigned to the Unit ≠ installed ≠ process running ≠ function produced a result**. The mockup simulates every transition, but real sources do not provide equal coverage.

### Legend

| Label | Meaning |
|---|---|
| Exists | The corresponding operation exists in the current code. This audit is not a new live qualification. |
| Partial | The command exists, but its preconditions, result or UI access do not fully match the mockup. |
| API available | The public schema confirms the method, but the required Demo Control/Presenter integration is missing. |
| Gap | No confirmed implementation or contract supports the promised transition. |
| UI only | Navigation/display; no system mutation is needed. |

`G01…G28` refer to the issue register in section 10. The same issue is not counted again for each click.

## 2. Call boundaries, results and identifiers

### Which part calls which source

| Area | Source / call mechanism | Boundary to preserve |
|---|---|---|
| Left-side Driving Control and telemetry | Existing native application, CARLA/Gateway/VISS; external connectivity changes through Demo Control | Do not derive Aos status from local motion or make the vehicle dashboard depend on Cloud awareness. |
| Right-side architecture, Unit monitoring, Platform and service runtime status | Aos Cloud through a trusted backend; the local journal selects the exact Unit only | These panels must not SSH into a VM. `component status/logs/diagnose test` are not substitutes for Cloud observation. |
| VM, environment and publication actions | One Demo Control implementation. CLI and native/Presenter share its application API | Do not create a second set of shell helpers or bypass existing operations with browser-issued commands. |
| Brake/Tire functional results | The respective product backend API | Cloud inventory or Running does not establish an assessment/advisory. These records are not in Aos Cloud REST inventory. |
| Credentials | Native/backend: OEM for Units/components, the respective team's SP for services | VM passwords, PKCS12 and OEM authority must not reach the browser or another SP. |

The current Presenter **does not launch the shell CLI**. It calls the same `execute_operation` used by `democtl`. CLI examples below identify that shared operation, not a proposed subprocess wrapper. This is the existing architecture. [Source][operations]

All CLI examples assume the common prefix `democtl --output json`. Below, `democtl …` or the remaining command is used for brevity. The global `--output json` goes **before** the command domain.

| Boundary | Current result | Interpretation |
|---|---|---|
| Demo Control | `{operation,state,message,target?,data?,status?}`. `state`: `READY`, `OBSERVED`, `COMPLETED`, `PARTIAL`, `BLOCKED`, `NOT_IMPLEMENTED` | Exit 0 for the first three; exit 1 for `PARTIAL/BLOCKED`; exit 2 for `NOT_IMPLEMENTED` or a CLI error. Progress is separate on stderr. `COMPLETED upload` does not mean Installed. |
| Presenter mutation | `POST /api/presenter/operations`, `{requestId,sessionId,action,…}` → HTTP 202 receipt. Subsequent operations reads return job state, progress and results/facts | One active job. An identical requestId/payload returns the existing job. Changed payload, stale session or busy state is rejected. A lost response may produce `UNCERTAIN`; it does not justify automatic POST replay. |
| Presenter read | `/api/presenter/snapshot` is the local projection; `/api/presenter/platform` is the VDP Cloud projection | These are separate sources. Snapshot does not establish Cloud Online. Platform is not yet a complete Unit dashboard. |
| Cloud mutation | HTTP 201/204/200, depending on the method | Confirms that mutation, not completion of subsequent delivery/startup. |
| Cloud list | Usually `{items,total}`; some monitoring/log methods return arrays | Handle pagination. Do not choose the first similar-looking Unit/bundle/service. |

Common Cloud failures: HTTP 400 invalid request; 401 authentication; 403 permissions; 404 object missing **or inaccessible**; 422 schema validation; transport/TLS/timeout is a separate class. The adapter currently often reduces HTTP errors to `CLOUD_HTTP_<code>`, losing useful response details. After a write timeout, first read the result using known identifiers; do not blindly repeat upload/provision/assignment. [Transport][unit-cloud], [UI receipts][operations]

### Keep identifiers distinct

| Value | Source / purpose |
|---|---|
| Image selector + SHA256 | `image list`; selector for create, SHA to bind the exact factory image. `.31` is a version, not a universal ID. |
| `test` / `production` | Local Demo Control role, not a Cloud UUID or Fleet name. |
| Unit UUID | Returned by Cloud provisioning/read and stored in the current journal; used in `/units/{id}/`. |
| `system_uid` | Device identity from IAM/Cloud; used in Unit Set/Subject membership and product queries. Do not substitute the Unit UUID. |
| Node UUID | Cloud node identity; distinct from the hardware node ID inside IAM. |
| Unit Set UUID | From Cloud binding; `Test Vehicles` must be a verification set. Production rollout is outside this stage. |
| VDP Component identity UUID | Currently `c33bc994-460b-476f-8000-934b55a70455`; codename `aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider`. |
| Update component/version UUID | The specific Cloud version object, not Component identity; used, for example, by `components/send-requests`. |
| Deployment bundle UUID / verification batch UUID | Distinct publication-processing results, not interchangeable IDs. |
| Service UUID / service-version UUID | SOTA service identity and a separate version. Subject assignment accepts **service UUID**, not version UUID. |
| Subject UUID | Independent service-to-Unit binding object, not inherently a run-owned resource. Group/non-group semantics, factory origin and lifetime must be distinguished; see the review below. |
| VDP profile / release version | `v1/v2/v3` are content profiles with 7/15/23 read paths. `16.0.0` and similar values are monotonic publication versions. Do not infer the profile from the major version. |

### <a id="subject-lifecycle-review"></a>Subject lifecycle review — 9 September 2026

The user challenged the proposed per-run Subject deletion. This review
withdraws that recommendation as the default. Subject retention was
subsequently accepted below, followed by Q13a's common scoped Retire policy.
Q13b subsequently accepts scoped run-data deletion while preserving release
numbering; actual Subject/type/state mapping is still audit work.

| Documented fact | Consequence for the pending decision |
|---|---|
| The [Subject guide](https://docs.aosedge.tech/docs/how-to/tutorials/service-managment/subject/) defines a grouping/binding object. Group Subjects support multiple Units; non-group Subjects can move after detachment from the current Unit. | Neither kind is inherently tied to one VM or one demo run. Q09b's one-current-Test scope is our targeting policy, not a reason to destroy the Subject. |
| [Aos Unit ontology](https://docs.aosedge.tech/docs/reference/ontology/unit) describes provisioning-created NodeType Group Subjects and additional Subjects. | Distinguish factory/platform Subjects from any separately managed demo Subject; do not treat a factory Subject as disposable. Actual tenant objects were not inspected in this documentation review. |
| [State Management](https://docs.aosedge.tech/docs/aos-cloud/components-view/state-management%20component) differentiates non-group state migration/synchronization from group behavior. | Selecting `is_group` is not just a one-versus-many UI choice. Check service state requirements; do not equate Cloud service state with product-backend records. |
| Audited OpenAPI 6.1.53 separately exposes Subject deletion and Unit/Subject unbinding. It does not establish a required deletion on Unit retirement. | Deletion capability does not justify a per-run deletion policy or prove cascading effects. |

The user subsequently **accepted retaining a dedicated reusable demo Subject**
and separately managing its Unit/service bindings; see the
[Q13a accepted cleanup policy](../planning/active/demo-studio-delivery-plan.md#q13-clean-cycle-cleanup-proposal).
Reattaching
a new Unit while old Brake/Tire assignments remain can bypass the agreed
independent first-deployment story. Binding reset, Subject type/state semantics
and factory-versus-demo identity therefore remain Q13a/G09 audit work; do not
silently adopt a new configuration or perform cleanup.

## 3. Opening, navigation and cards

| ID / mockup action | Call sequence | Returned fact / transition | Errors and gaps |
|---|---|---|---|
| A01. Open page / restore view | GET `/api/presenter/snapshot`; GET current operations; if a Unit is known, GET `/api/presenter/platform`. Do not automatically launch `demo prepare` on opening | Local environment, catalog, current vehicle and unfinished job; separate Cloud observation | Partial. Browser reload is not reset. Session receipts do not fully restore a workflow after native restart. G21, G22. |
| A02. Select factory firmware | `democtl image list` → select an already returned selector. The picker itself creates nothing | Available image catalog; version, identity/SHA and suitability come from that catalog | The current mockup offers only illustrative factory .31; bind real choices to the actual image catalog. Other firmware availability is not asserted. Pre-provision code is still pinned to .31. G02. |
| A03. Select Test for provisioning | Local role selection; Unit Set binding is read/checked inside `unit provision test` | `Test Vehicles`, a verification set, not a new Fleet | Partial: CLI accepts test, but existing UI `create/provision` use all and auto-prepare requires two VMs. Do not silently create Production as a workaround. G01. |
| A04. Open Platform / release studio | GET `/api/presenter/platform`; `component list` for local releases. For the selected prepared release: `component inspect <V>` | Cloud installed/pending/catalog and a separate local candidate | Partial. `component list` lacks full profile/signing details. Use stored metadata/inspect, not repeated unpacking of all files on every tab switch. G14, G25. |
| A05. Select a VDP/Brake/Tire candidate | Local selection; VDP `component inspect <V>` for details only. SOTA requires a future service catalog plus Cloud service versions | Changes the selected artifact, not its Unit assignment | VDP partial; `democtl service …` **does not exist**. The mockup service list is still simulated. G08, G10. |
| A06. Open release Details | VDP `component inspect <V>`; for a separate signature check, `component verify <V>`; Cloud catalog metadata if needed | Type, codename, version, profile, architecture, digest, provenance and file; “signed” only with evidence | Current 2.6 uses deployment-bundle naming. Signing/profile inspection remains an integration boundary, not repeated extraction on navigation. G25. |
| A07. Click VDP/rootfs/boot in the architecture | GET `/units/{U}/`; matching `unit_update_components`; follow version references to Component catalog details | Installed/pending versions; distinguish missing information from a missing component. [Q05](../planning/active/demo-studio-delivery-plan.md#q05-accepted-factory-slots-and-versions) accepts Factory baseline / profile-first labels with exact release secondary and raw technical values in Details | API available. Current `unit_view` selects VDP only. The mockup hardcodes rootfs/boot and their versions. Pre-provision image configuration must not masquerade as Cloud observation. G05, G12, G25 remain implementation gaps. |
| A08. Click a Brake/Tire service in the architecture | GET `/units/{U}/subjects-services/`; service UUID detail if needed | Versions, instances, run state and errors; Open releases is navigation only | API available, adapter missing. An empty slot is valid only after a successful complete read, not after 403/timeout. G11, G12. |
| A09. Click Aos Cloud / Brake backend / Tire backend | Cloud → C01–C04; backend → B01–B04. Back to map, Close, Escape and team/workspace changes perform no mutations | Screen navigation and refresh of its read model only | No repeated upload/assign/start during navigation. G14, G18. |
| A10. Next / Open required VDP / See backend result | Navigate to the appropriate card; read its API on entry | Advance the story using confirmed facts | 2.6 now retains confirmed completed chapters and accepts terminal expected state without a seen Pending; VDP runtime remains Not reported. Real Cloud-backed guide integration remains G05/G14. |
| A11. Session, confirmation, Close | Open/close dialog locally; invoke the system only after Confirm for the selected action | Cancelling the dialog makes no new call | Closing an already started operation does not cancel it. Current jobs have no general cancellation API. G22. |

Sources: [Mock handlers][mock-handlers], [CLI][cli], [Presenter][presenter], [ComponentService][components], [Image catalog][images].

## 4. Create → initial Manual connection → publication → provisioning

| ID / action or transition | Call sequence | Result required for the next transition | Errors and gaps |
|---|---|---|---|
| L01. Create vehicle | Mockup semantics: `environment create --image <I> --target test` → `vm start test`. **This exact sequence followed by pre-provision upload cannot currently run without changing restrictions** | Create: factory copy + overlay, stage `MANUFACTURED`; start: running process, SSH/DNS/role readiness | Commands exist, composition differs. Create does not boot the VM. Errors: existing current run, foreign/busy files, insufficient space; create currently requires 60 GiB free for the factory copy. Boot changes stage to `LOCAL_ACTIVE`, rejected by pre-provision upload. G01, G02. |
| L02. Request access to a new VM | Native `NativeVMAccess`: Keychain or macOS dialog; then continue `vm start` | Secret stays native; SSH enrollment completed; `guestReady`, `guestDnsReady`, `factoryRole` | `VM_ACCESS_DIALOG_TIMED_OUT` (code: 185 s), `VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`, invalid input. Do not wait for a terminal password in the browser. Wrong password/readiness timeout means blocked/partial, not ready. |
| L03. Stage fresh VDP v1 before provisioning | `demo plan --image <I>` chooses the next V; `component prepare <V> --profile v1` → `component sign <V>` → `component upload <V>` → confirm bundle/catalog processing | New monotonic v1 release ready; without a Unit it is not installed | Partial. `demo plan` reads the Cloud catalog; the version is not a locally timed counter. Pre-provision upload requires both pristine VMs, `.31`, MANUFACTURED/LOCAL_STOPPED and empty role sets/the bound scope. G01, G02, G07. |
| L04. Provision to Test | `unit provision test`. Internally: role binding + live VM/IAM/DNS → official SDK `run_provision_v6` → Cloud registration/certificate exchange → wait for provisioned **Online** → POST Unit Set membership → read membership | `unitId`, `nodeId`, `systemUid`, lifecycle `PROVISIONED`, Online and correct set | 2.6 now matches Online before membership and preserves incomplete registration. Current CLI still rejects a selected source; DNS/IAM/SDK/Online/membership failures remain distinct. G01/G03/G24. |
| L05. Update assigned automatically after membership | UI issues no FOTA assign command. Read Unit/version; Cloud selects an appropriate component for the compatible model/architecture and verification set | `pending_component` and its version/ID/status; later installed | Cloud behavior, not `component approve` or a timer. Model/codename/architecture/set must match. Do not PATCH Unit Model with `formatVersion/vendorVersion` from the old example. G04, G23. |
| L06. Connect simulator / initial vehicle source | `simulation start` → first-run presentation needs existing internal `vehicle.initialize test` (stationary Manual). Ordinary CLI `vehicle select test` is **a different transition**, using Safe Stop/reset | Simulator/Gateway/native control ready; one current vehicle; source bound and VISS telemetry confirmed | Start/select exist; initial initialize exists inside the application but has no public CLI command or standalone UI action. Ordinary select may immediately open the FOTA gate and install the baseline before driving. G03. |
| L07. Prepare Test demo · one action | Current `demo prepare --image <I>`: create **all** → prepare/sign/upload/**approve** v1 → start **all** → provision **all** → simulation start → internal initialize test → guest component observation | Recorded completedSteps, version/profile, `READY_TO_DRIVE`; baseline not yet activated | Partial, not equivalent to the accepted path. [Q04b](../planning/active/demo-studio-delivery-plan.md#q04b-accepted-preparation-modes) accepts explicit Full story / Quick preparation using shared operations, not this old order. No test target; approval unnecessary; the internal SSH probe cannot become a right-panel Cloud fact. Repeating with recorded READY_TO_DRIVE may return noOp without current readiness. G01, G03, G04, G21, G22. |
| L08. Repeat click / partially completed preparation | Reuse the existing job/journal; continue only confirmed unfinished stages. Do not create/provision/upload again because the UI timed out | noOp or the exact next stage; an uncertain result remains uncertain until read | Idempotency exists at several levels, but unified recovery for the new Studio workflow is not defined. `CURRENT_RUN_EXISTS_RECOVERY_OR_RETIREMENT_REQUIRED`, image/SHA mismatch, UNCERTAIN. G21, G22. |

Sources: [Environment create][environment], [VM start/stop][vm], [Unit lifecycle][units], [SDK adapter][unit-sdk], [Demo preparation][prepare], [Native password][native-access], [Source switching][source].

## 5. VDP: preparation, publication and automatic transitions

These rows apply to all three profiles and subsequent cycles: v1 → v2 → v3, each with a new monotonic release version. The mockup uses 16/17/18 and then 19/20/21. Actual versions come from the catalog, not fixed numbers in this document.

| ID / action or transition | Call sequence | Returned fact / display | Errors and gaps |
|---|---|---|---|
| V01. Prepare a missing candidate | `component prepare <V> --profile <P>`, where P is v1, v2 or v3; for separate extraction, existing `component unpack <V>` | `prepared.json`, contentProfile, digest/provenance, consistent internal/external versions, payload/bundle | Exists. Do not rebuild the factory image for every VDP version. Do not repeat prepare/unpack on each tab switch. Existing output or an incompatible profile/base/digest is an error, not a silent overwrite. |
| V02. Sign | `component sign <V>`: current official Aos signer through the private adapter; OEM credential; verification of signed output | Signed deployment bundle, SHA256 and verified signature; an unchanged repeat may be noOp | Exists. Credential/access errors, metadata/hash/signature mismatch, or an existing incompatible output. Local “signed” is not Cloud acceptance. |
| V03. Sign & upload | V02 if not already signed → `component upload <V>`; internally multipart `POST /deployment-bundles/upload/`, field `file` | HTTP 201: deploymentId/state; initially show “Cloud accepted the file” | Partial. The call performs local checks, Cloud scope/Production guards and, for provisioned Test, SSH schema diagnosis. These are actual command stages, not one short HTTP call. Offline Test blocks upload. G06, G07. |
| V04. Cloud processing → Published | Paginated GET `/deployment-bundles/`, locate the known deploymentId; then Component versions. No deployment-bundle detail GET exists | Bundle state/build_info and the discovered version; only successful processing means Published | Currently `upload` returns COMPLETED after list registration, not necessarily `done`. Projection loses build_info; repeated upload can return noOp even for a discovered error bundle. `payload must be a file…` is a processing error. G07. |
| V05. Published → pending on matching Test | Read `/units/{U}/`; no additional approve/send in the normal path | Version in pending_component; Cloud status without guessing the internal VM stage | A verification set receives SOTA/FOTA without approval. `component approve/unapprove/send` exist but are **not required stages of this demo**. Unapprove is not rollback/cancel. G04. |
| V06. Pending → downloading / verifying / Waiting for Safe Stop | Observe Cloud Unit; use Cloud logs C05–C07 for diagnosis | Show only the returned pending status/error. Local telemetry Safe Stop may appear separately on the left | The API does not guarantee download percentage, verification phase or explicit FOTA gate. The current adapter does not provide these facts. Timed 25/50/75/100% and definite Waiting for Safe Stop are simulation, not ready integration. G05. |
| V07. Safe Stop pressed → installation | Native control N03; then read Cloud Unit until the installed version changes. UI does not call `install`, `restart` or `component send` on Safe Stop | Installation authorization belongs to the current runtime/VDP gate; Cloud installed version confirms installation | Button event ≠ stationary vehicle ≠ gate accepted by core. Installation failure, old installed version and pending error remain visible. UI cannot declare success from elapsed time. G05. |
| V08. Installed → Starting → Running VDP | Installed: Cloud component row. Running requires separate confirmed **Cloud-accessible** runtime evidence, absent from the current adapter | Today: “Installed <V>; runtime not reported by Cloud” | Critical gap. A FOTA component is not a SOTA service instance; do not automatically apply service run_state to VDP. SSH `component status test` exists for engineers, not as the right-panel source. G05. |
| V09. Next profile, new cycle, no downgrade | Select profile → new V above published versions → V01–V08. Retire preserves the same factory image and existing Cloud releases | Explicit contentProfile ↔ release version ↔ digest binding; old candidate unavailable for a new upload | 2.6 maintains a per-identity high-water ledger across Retire and consults its simulated catalog. Real durable allocation across local cleanup and external publications remains G25; operator never supplies release numbers. |
| V10. New upload while previous release is pending | Publish through V03; observe actual Unit pending/installed. Do not delete the previous component | What Cloud actually selected / what the Unit actually installed | 2.6 blocks Publish for an already unfinished identity; Prepare/Sign remain available. This is a demo workflow restriction, not proof of Cloud supersession semantics. G27. |
| V11. Leave Safe Stop during Installing | Native mode command; read the real outcome. Do not invent a Cloud cancel call | Actual runtime defer/cancel/finish, if observable through Cloud | 2.6 no longer invents cancellation/restored old runtime when leaving Safe Stop during apply. Real in-flight policy remains source-backed and separately qualified; no cancel command is implied. G27. |

Sources: [Component pipeline][components], [Signer][signer], [Cloud projection/guards][component-cloud], [Verification-set semantics][verification-doc], [Update tutorial][update-doc], [Public schema][openapi].

## 6. Brake/Tire: service publication and assignment

The table below contains **no invented `democtl service …` commands**. Existing APIs are specified, but integrating them into shared Demo Control remains a gap. Direct UI curl calls are not proposed as a substitute.

| ID / action or transition | Call sequence | Returned fact / transition | Errors and gaps |
|---|---|---|---|
| S01. Select Brake v1/v2/v3 or Tire v1 | Local catalog/provenance of prepared service bundles + GET `/services/{S}/service-versions/` | Confirmed candidate/profile/version/architecture/owner | Gap. VDP ComponentService is specialized. The canonical Brake repository contains foundation/domain code, not a fully qualified runtime for all three profiles. No Tire implementation was found in the inspected workspace. G08. |
| S02. Sign & upload service | Prepared SOTA bundle → official signer with the respective **SP** credential → POST `/deployment-bundles/upload/` → GET bundles + service versions/detail | Bundle accepted, then service version ready, owned by that SP | API available; no democtl commands or Brake/Tire SP publication bindings. Do not submit SOTA as VDP FOTA using OEM identity. Package/container build, layer dependency and owner/permission errors. G08. |
| S03. First Deploy to Test | After SP Publish service and confirmed processing/ready state, use OEM authority: resolve the dedicated demo Subject Q; POST `/subjects/{Q}/units/` `{system_uids:[UID]}` only if the exact Test binding is absent; then POST `/subjects/{Q}/services/` `{service_ids:[S]}` for the requested missing binding; read both bindings and Unit subjects-services | Subject actually contains the requested service identity and only the current Test Unit; desired assignment, not yet Running | Q09a/M05 and Q09b option A accepted: two explicit actions through Demo Control; one Subject shared by independently assigned Brake/Tire identities, without altering the peer binding or SP ownership. Create only when needed and authorized, not per click. Reconcile uncertain mutations. Existing Test membership means adding a service may start delivery immediately. G09/G21 integration remains open. |
| S04. Publish Brake v2/v3 update after the previous version | Read the existing Subject/service binding; publish under the owning SP through Demo Control and observe processing and Unit versions/runtime. A new ready version may deliver automatically; repeating assignment does not select a version | Update of the actually assigned service identity | Implemented in 2.6 simulation as Publish update, no second Deploy. Actual service publication/runtime integration remains G08/G09/G11. |
| S05. Assigned → installed → Running | GET `/units/{U}/subjects-services/` and `/{S}/`; inspect installed/pending versions, `num_instance`, `pending_num_instance`, instances/version/run_state/errors for the intended Test/Subject/service binding | Q09c option A: expected version installed and required instances of that version running completes the technical update and releases the per-identity publication guard; not functional/E2E acceptance | API available, integration pending. Assignment does not set an explicit numInstances in its payload. Zero instances, old running versions, stale/missing evidence or unresolved errors do not qualify. Accepted minimum-instance metadata and exact observation mapping remain G11 work. |
| S06. Service “Waiting for VDP” | Cloud confirms the process/errors; capability readiness must come from service logic and accessible functional status/logs | Q09c option A: function readiness/results are separate from technical completion; an awaiting-capabilities/data function does not keep a confirmed installed/running update open | No confirmed native Service→FOTA dependency field. Mockup `vdp.profile >= service.requires` is a demo model, not a Cloud admission rule. Do not fabricate functional reasons/readiness from an inventory comparison. Function and advisory proofs remain mandatory for their E2E scenarios. G11, G19. |
| S07. VDP update temporarily interrupts a function, then restores it | V01–V08 + service runtime/functional status reads | Actual function transition and data availability, not forced states for every service | 2.6 preserves service runtime separately from capability availability. Real function interruption/readiness must come from its own status; do not infer it from component inventory. G05, G11. |
| S08. Repeat the full service cycle after retire | New Unit + reconciled dedicated Subject binding; repeat profiles with new monotonically increasing releases on the same service identity and owning SP | Q09c retains each service identity and independent release sequence: new v1 content release, then higher releases for later profiles | 2.6 allocates separate monotonically increasing releases for VDP, Brake and Tire. Durable real tooling still needs implementation. Do not attach a fresh Unit to stale assignments and accidentally deliver the previous later profile. Subject retention and owned-binding cleanup are accepted Q13a/Q13b. G10. |
| S09. Remove/cancel service assignment (not a separate current mockup button) | If needed later: DELETE `/subjects/{Q}/services/{S}/`; then observe the Unit | Desired binding removed; instance stop/removal confirmed separately | This is neither FOTA-component deletion nor version rollback. Q09b fixes one dedicated Test Subject and independent bindings, not authorization to remove them. Owned binding removal is accepted only within Q13 Retire; do not include removal implicitly in Publish or navigation. Preserve the peer binding. G09. |

Sources: [OpenAPI][openapi], [Official service flow][service-doc], [Lifecycle research: no native FOTA dependency][lifecycle-research], [Brake service source][brake-service].

## 7. Native Driving Control, connectivity and telemetry

| ID / action or transition | Actual call | Returned fact / transition | Errors and gaps |
|---|---|---|---|
| N01. Autopilot / A key | Existing native bridge: `{"action":"set_mode","mode":"autopilot"}`; neither Cloud API nor a new democtl command | Controller mode acknowledgement, followed by actual speed/data from Gateway | Exists. Accepted command does not mean the vehicle is already moving. Detached source, stopped simulator, rejection or no reply must remain visible. |
| N02. Manual / M key / arrow keys | Native `set_mode: manual`; existing driving-control inputs throttle/brake/steer | Mode, actual applied controls and telemetry | Exists. Arrow keys are not Cloud actions. The browser mockup must not become a second uncoordinated control channel. Focus loss/key release follow native controller behavior, not indefinite retention of the last throttle. |
| N03. Safe Stop / Space | Native `set_mode: safe_stop`; telemetry shows braking → stationary | Separate Request accepted, actual braking and stopped states. V07 then observes FOTA through Cloud | Exists. UI does not call Cloud install. Safe Stop can authorize an already pending update, including during completion/parking. G05, G16. |
| N04. External network OFF | `vehicle connectivity off --target test`; the current native button already calls democtl | Filter read-back, target and OFF state; local CARLA/VISS/SSH remain available | Exists. Disables VM external traffic, not Mac Wi-Fi or Gateway attachment. Requires a running/current VM; `EXTERNAL_LINK_CURRENT_VEHICLE_REQUIRED`, `…RUNNING_VM_REQUIRED`, UNCERTAIN. G06. |
| N05. OFF → Cloud Offline / backend queue | Right panel reads Cloud Unit; product functions continue locally and establish outbox state separately | Cloud Offline only when Cloud actually reports it; last-known inventory with age | 2.6 has a separate delayed simulated Cloud observation. Production adapter must read actual Cloud, never infer Offline from the native toggle. Product outbox is not Cloud inventory. G20. |
| N06. External network ON → reconnect | `vehicle connectivity on --target test`; independent reads of Cloud Online and backend delivery | ON confirms filter removal; Online/ack appear later | Partial. Removing the filter does not guarantee DNS/TLS/CM reconnect. Do not announce instant drain of all records or repeat upload. G20. |
| N07. Telemetry tabs Dashboard / Vehicle / Data | Local native UI navigation only; existing Gateway/VISS data stream | Speed, controls, wheel/GNSS, freshness and advisory from telemetry | Exists. No Cloud GET on native tab changes. Missing/stale/unsupported data is neither zero nor “healthy.” |
| N08. Driver advisory appears/disappears | Service → VDP request path → Gateway validation/status → native telemetry | Confirmed in-vehicle advisory, availability/status and clearing under the actual contract | 2.6 independently simulates vehicle advisory receipt and lease/version/generation clearing; backend receipt is not vehicle receipt. Complete real service → VDP → Gateway → telemetry evidence remains G19/G20. |
| N09. Switch current vehicle | `vehicle select <role>`, role = test or production: source Safe Stop → block old path → reset → allow new path → VISS read-back | Exactly one current vehicle and generation; source switching, not Cloud Unit assignment | Command exists; Production rollout is currently out of scope. Restore the offline filter before switching; initial Manual differs from ordinary select. G03. |

Sources: [Native controls][native-control], [Source lifecycle][source], [External network][connectivity], [Gateway packet-filter integration][source-guest].

## 8. Cloud monitoring, logs, backend dashboards and trace

### Cloud Unit monitoring: the same source for architecture and teams

| ID / action or transition | Call sequence | Result / display | Errors and gaps |
|---|---|---|---|
| C01. Open Cloud / Refresh inventory | GET `/units/{U}/`; separate subjects-services reads if required. For the existing VDP projection: `component cloud-status` **without a version** | Unit identity/lifecycle/online, rootfs/boot/VDP components, pending, services/instances and installed config | API available; current `/api/presenter/platform` returns only a VDP subset plus Online/lifecycle. Do not call expensive versioned cloud-status for every general refresh. G12. |
| C02. Cloud ↔ controller connection line | Use `online_status` from C01 plus read success/time | Distinguish Online, Connected and Offline; separately show Cloud-read unavailable/stale | Do not derive Online from a local process or network toggle. Inability to read Cloud does not mean Unit Offline. Current selected vehicle is a separate local fact. G14. |
| C03. CPU / RAM / disk / traffic | GET `/units/{U}/monitoring/` with selected node/time/measurements; `/monitoring/dashboard/` for history if required | Timestamped samples scoped to node/service/subject/instance; show null/missing samples explicitly | CPU is documented in DMIPS and 2.6 now labels its illustrative values accordingly. Actual adapter, node/sample units and null semantics remain P2/G12 work; no fabricated percent denominator. |
| C04. Open a team dashboard | Cloud inventory/runtime projection C01–C03 with permitted scope; functional data separately through B01/B02 | Team observes its service state; OEM monitors the controller as a whole | Public monitoring schema permits OEM/FleetOwner, not any SP. Server-side projection authorization is required. Do not hand an OEM credential to Brake/Tire to make the dashboard work. G28. |
| C05. VDP/unit logs: open existing logs | GET `/unit-logs/?unit=<U>…` → GET `/unit-logs/{L}/` → download only when ready | Request list, state/error, available log with time/source | API available, integration missing. `component logs test` uses SSH and is unsuitable for this panel. Merely opening a card must not POST a new log collection request. G13. |
| C06. Request fresh unit logs | Explicit action: POST `/unit-logs/` `{unit:U,node_ids:[N],date_from:…,date_till:…}`; then read every returned request ID | POST 201 returns an **array** of log requests; waiting-unit/receiving/done/error/empty | Separate Cloud mutation, not instant tail. Requires OEM permission. Timeout, offline Unit, empty logs and request error are distinct outcomes. Bound time range/volume and avoid exposing secrets in UI. G13. |
| C07. Brake/Tire service logs | GET `/service-logs/`; for a separate Request action, POST `{unit,service,subject,request_type:"log" or "crash_log",date_from,…}` → follow IDs → download | Logs for the exact service/subject/instance belonging to that team; POST also returns an array | API available; SP service_logs permissions are not automatically OEM unit_logs scope. Possible no instances, missing subject, forbidden, empty/crash-log unavailable. G13. |
| C08. Automatic updates after publication / while panel remains open | Initial read + bounded repeat reads during pending/job; stop or slow down after terminal state. This is **proposed integration**, not an existing command | One consistent read model with observedAt, age and previous snapshot on failure | Current Presenter refresh is a single fetch. A stale marker after 60 s is not Cloud polling. Fetch failure clears value while the mockup retains last-known data. No guaranteed new Unit-report time. G14. |
| C09. Presenter Cloud access unavailable / restored | Actual source is read/auth/TLS/timeout outcome; after restoration, GET without replaying mutations | Unavailable + last-known, then fresh observation | Toggle simulated Cloud access in Session is mock fault injection only. It must not change real OEM/SP rights or disable VM networking. G28. |

### Product backends: separate from Aos Cloud monitoring

| ID / action or transition | Call sequence | Result / display | Errors and gaps |
|---|---|---|---|
| B01. Open Brake backend | `GET /api/v1/brake/units/{UID}/windows`, `/assessments`, `/events`, `/advisories`; selected window: `/windows/{eventId}` | Q10b overview first: service state from Cloud/C04, latest persisted product result and backend-recorded advisory; compact history/details with event provenance | Q10b presentation accepted, integration missing. HTTP handlers exist, but democtl lifecycle/Presenter proxy/currentUnitContext are not connected. Default main supplies no context; queries can return 503 `CURRENT_UNIT_CONTEXT_UNAVAILABLE` even when health is ready. Backend receipt does not prove vehicle advisory display. G18/G19. |
| B02. Open Tire backend | Contract: GET `/api/v1/tire/units/{UID}/assessments`, `/events`, `/advisories`, `/function-status` | Q10b uses the same overview-first composition with Tire's independent results/advisory and Cloud service state; readiness/freshness differs from Running | Presentation accepted, but contract existence does not prove an implemented endpoint. Implementation/startup adapter was not found in the inspected workspace; retain unavailable/unknown states rather than fabricated healthy results. G18. |
| B03. Drive → Safe Stop → Brake result | Actual sample stream → service domain algorithm → POST `/api/v1/brake/messages` → backend persistence; UI reads B01 | v1 window, v2 assessment, v3 advisory according to implemented profile, inputs and contract | 2.6 uses a qualifying simulated moving/stopping episode and measured mock sample count. Its illustrative result is not an algorithm or a guarantee that every Safe Stop yields an advisory. G19. |
| B04. Drive → Tire result | Actual samples/quality/window → service → POST `/api/v1/tire/messages` → B02 | Confirmed result or explicit not-ready/deferred/insufficient-data | 2.6 uses a simulated driving episode and capability prerequisites. This is not a real collection-window/algorithm timing guarantee. Actual Tire runtime and quality handling remain G18/G19. |
| B05. Backend live updates | Brake SSE `/api/v1/brake/stream?systemUid=<UID>`: notification → reread REST. Tire stream is analogous in the contract | Event announces a change; read the result from the persisted backend API | Brake stream handler exists, UI binding does not; Tire is unconfirmed. Reconnect requires refetch. SSE does not replace an authoritative record. G18. |
| B06. Inspect received records / pagination | REST collections with next cursor; window detail by eventId. Q10b places compact history below the overview and opens record details on selection | Records for the exact current system_uid/run, eventId, available input data, service/VDP provenance and captured/received timestamps where present in schema | Q10b presentation accepted; integration remains open. Do not substitute Cloud Unit UUID for system_uid. 404 `UNIT_NOT_CURRENT`, 400 invalid query/cursor, 503 no context. Distinguish empty/stale/read-error and use event-time versions, not today's inventory. No retention policy is implied. G19, G25. |
| B07. Offline → local result/advisory → delayed delivery | Q11 option A: after installed local functions are established, Native N04 → real offline stimulus/local operation → N06 → service retry/backend durable ack → reread correlated records; no new release required in this chapter | Independently observed filter state, Cloud connectivity, native advisory and backend receipt, with original event times; no invented queue size or local record in a disconnected backend | Q11 story accepted, implementation remains open. Tire contract requires persisted outbox and bounded retry/backoff. Prove the fault blocks vehicle-to-backend traffic while preserving local telemetry/operator access. Networking ON does not prove drain; backend ack ≠ Gateway advisory ack ≠ driver ack. G20. |
| B08. Backend context/start/stop during a demo session | Q10a option A: prepare/reuse both product backends through shared Demo Control during composed Create or Quick preparation; bind current Test context when known. Opening a dashboard is read-only. Exact CLI integration is still missing | Distinct application availability, current Unit query binding, guest route and persistence; no service publication/deployment implied | Brake main defaults to a temp DB and receives no currentUnitContext. Current-unit query contract expects two roles, conflicting with accepted Test-only scope. Do not start Production, reuse an old Unit context or fabricate empty/successful results on read failure. Q12/Q13 still own stop/resume/retention. G01/G18 integration remains open. |
| B09. Records after Retire / new Unit | Use the accepted scoped Retire through backend admin cleanup while retaining exact current-run UID context until deletion completes | Current session is not mixed with an old UID; preservation/deletion is explicit | Q13b accepted scoped ordinary-record deletion at Retire; 2.6 clears records/outbox/context. Real environment retire still lacks backend cleanup. Migrate current-role selectors in P1; G26. |

### Trace and mockup-only tools

| ID / action | Actual equivalent | Result / gap |
|---|---|---|
| T01. Trace, Newer/Older | Read already received operation receipts, journal/public facts and Cloud observations; pagination is UI-only | Trace must identify Command / Cloud / Native / Product backend sources. Current native receipts are ephemeral, limited to 128 jobs. Mock trace with 120 timer events is not a real backend audit log. G21, G22. |
| T02. Overall progress bar | Demo Control stage progress and Cloud state; indeterminate where no percentage is measurable | Do not report 65% Installing/88% Starting from timers. Upload percentage requires actual byte progress, absent from the current response. G05, G24. |
| T03. Retired 2.5 fixture entry selector | No live or 2.6 control; retained ID for traceability | Replaced by actual simulated Create/Quick preparation, not a jump to installed software. |
| T04. Retired 2.5 pace selector | No live or 2.6 control; retained ID for traceability | Simulation timers do not specify actual timeout/retry/gating intervals. |

Sources: [OpenAPI][openapi], [Platform read model][platform-model], [Presenter provider][presenter-provider], [Brake HTTP implementation][brake-http], [Brake main][brake-main], [Brake query contract][brake-contract], [Tire contract][tire-contract].

## 9. Park, Resume, Deprovision, Delete and Retire

The mockup timer order cannot be copied literally here. Current `unit deprovision` uses the still-running VM to stop CM normally, wait for Offline and revoke provisioning. Only then does the command stop the VM.

| ID / action or transition | Call sequence | What remains / returned result | Errors and gaps |
|---|---|---|---|
| R01. Park demo · preserve environment | Q12b first rejects conflicting unfinished/uncertain changes promptly with their reason, without stopping or queuing Park. Otherwise Q12a composes graceful stop of owned VM, CARLA/Gateway, native surfaces and backends through shared Demo Control | Retained disks/content, Cloud identity/assignments, product records and operation state; owned local runtimes stopped only after successful Park. No warm Pause | Park remains NOT_IMPLEMENTED. No deprovision/delete/history clearing/backups or forced update interruption. Status reads alone do not block Park. Exact conflict sources, pending-FOTA interaction and shutdown ordering remain final-audit work. G15/G16. |
| R02. Resume parked demo | Q12a: start the retained environment through shared Demo Control, restore applicable connections and read actual state; reuse recorded identities/working disks instead of replaying preparation | Same environment and existing identity; fresh observed readiness/Online, or truthful partial/unprovisioned state | `environment resume` is NOT_IMPLEMENTED. No Create/provision/sign/upload replay. VM start does not prove VDP Running. Ordinary prepare is not Resume. Retained content does not freeze Cloud desired-state reconciliation. Exact source mode/recovery sequencing remains audit work. G03/G05/G15/G22. |
| R03. Deprovision only | simulation stop/detach → if VM is already stopped, `vm start test` for the current contract → `unit deprovision test`. Internally: stop CM → Cloud Offline → DELETE `/units/{U}/deprovision/` → GET new/Offline → VM stop | Cloud Unit remains, provisioning revoked; VM off; overlay retained but retired for reprovisioning | 2.6 retains/restores VM availability through deprovision and stops it afterwards. CLI exists, shared Presenter composition remains partial. Offline/CM/permission/timeout failures never mean successful revocation. G16/G17/G21. |
| R04. Delete deprovisioned Unit | `unit delete test`: require deprovisioned/new and stopped → remove exact role-set membership → DELETE `/units/{U}/` → confirm Unit/Node absence and empty set | `unitAbsent`, `nodeAbsent`, `roleSetEmpty`, `localDiskRetained`; Cloud Unit deleted | Exists. No separate Node DELETE is required. Working overlay still exists. Foreign Units/Sets remain untouched; do not delete every similarly named Unit. G21. |
| R05. Retire · identity + working copy | Q13a/Q13b: shared scoped retirement for Finish demo and incomplete cleanup before New cycle. Compose existing deprovision/delete/local disposal with owned Subject-binding reset, temporary-setting restoration and scoped product-record deletion. Keep VM/backend APIs alive until their required actions finish | No leftover owned run or ordinary product history; preserve Subject, source image/catalog, published releases, permanent infrastructure/credentials and cross-run release numbering. New cycle starts only after confirmed cleanup; Park remains separate | Accepted policy, not completed integration. `environment retire` itself only disposes local resources after Cloud absence proof. Preserve journal/selectors until external outcomes reconcile; no blind repeats or cleanup on page open. Exact ordering, Test-only/parked/partial cases, numbering retention and integration remain G01/G09/G10/G16/G21/G22/G26. |
| R06. Retire after a lost upload response | Read Cloud/journal for reconciliation; then ordinary R05, without new upload/approval | Retain knowledge of whether the external action occurred | The special current cleanup recovery for upload state RESPONDED depends on confirmed approve/batchId; normal CONFIRMED upload does not. When removing unnecessary approval, also resolve this recovery path. G04, G22. |
| R07. Fresh run after Delete | Complete Q13a cleanup if needed → Create/start fresh overlay from catalog image → connect locally, stationary Manual → publish a new VDP v1-profile release → Provision, per Q01–Q03 | Fresh clean overlay/new Unit; source image is not rebuilt. No stale Brake/Tire assignment bypasses independent first Deploy | Q13a accepts common cleanup-before-new-cycle. Do not reprovision the retired overlay or delete published releases to force v1. Preserve the same image SHA for the agreed repeat qualification. Integration remains G17/G21. |
| R08. Retire while Installing / unknown state | Mockup blocks during install. Live UI lacks a reliable Cloud FOTA Installing gate; define behavior for unknown/in-flight state before the destructive path | Explicit blocked outcome or an agreed normal completion path, not a promise of atomic cancellation | 2.6 refuses unfinished/uncertain changes without queuing shutdown. Terminal failed-install intervention is explicitly deferred; do not promise cancel/rollback or erase uncertain ownership. Real observed guard remains G05/G27. |

Sources: [UnitService deprovision/delete/confirm_retired][units], [Environment retire][environment-retire], [Presenter reset plan][operations], [CLI park/resume][cli].

## 10. Consolidated issue and decision register before connecting the mockup

“Resolve” below means agree the behavior and then implement/confirm it in a separate stage. This document does not authorize those changes.

| Gap | Finding and affected behavior | Decision / subsequent correction required |
|---|---|---|
| G01 — Test-only | Auto-prepare/UI lifecycle use all; pre-provision VDP requires two pristine VMs; versioned upload without local Production still requires a Production member; Brake query context expects two roles | [Q04a/M01 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q04a-accepted-test-scope-and-production-presentation): one Test VM; Production visible but disabled with Deferred; retain CLI production/all. Align lifecycle, publication guards and backend context without a hidden Production VM. Preserve existing Production resources and genuine recipient/ownership checks. Implementation/verification remain open. |
| G02 — Create / image | Mock Create boots the VM; pre-provision upload allows MANUFACTURED/LOCAL_STOPPED, not LOCAL_ACTIVE; factory guard pins .31 | Decision accepted on 9 September 2026: [M02 Create B / Platform Team A](../planning/active/demo-studio-delivery-plan.md#m02-accepted-create-and-platform-publication). Create includes boot; show v1 preparation/publication before Provision. Revise the pre-provision contract, with no stop/start workaround. Implementation and image compatibility validation remain open; decision acceptance does not close the gap. |
| G03 — Initial connection | `vehicle select` uses Safe Stop/reset; internal initialize provides stationary Manual but is not a standalone CLI/UI action; the shared Unit lifecycle guard rejects provisioning with a selected source | [Q03 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q03-accepted-initial-vehicle-connection): connect after Create, before Provision; stationary Manual without automatic Safe Stop. Expose initial connection and revise only the affected provisioning guard so it preserves the connection. No detach/reconnect workaround or broad removal of retirement safeguards. Implementation/qualification remain open. |
| G04 — Approval | Auto-prepare still calls approve; some docs treat it as a gate; one cleanup recovery path depends on it | Remove approval from the required Test verification-set path. Retain a separate explicit approval operation if needed for future rollout. Update associated recovery/docs only; do not replace deployment-bundle upload with the direct-components endpoint. |
| G05 — FOTA evidence | Current Cloud component projection confirms installed, but not VDP process, Safe Stop gate, download percentage or functional startup | [Q06 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q06-accepted-cloud-runtime-evidence): investigate supported Cloud runtime sources first; if none is confirmed, allow Installed / runtime Not reported for the first UI milestone. The adapter limitation is not a proven platform limitation. Actual runtime/E2E proof through engineering democtl remains mandatory and separate from the Cloud-only panel. G05 implementation and the remaining gate/progress evidence are not closed. |
| G06 — Offline publication | Cloud upload API does not require an Online Unit, but democtl `guard` requires Online Test; pre-provisioning is a separate exception | [Q08a accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q08a-accepted-offline-publication): allow publication while a provisioned Test is Offline, provided host Cloud access and compatibility/identity/recipient-scope safeguards hold. Show publication, connectivity and observed delivery/install separately; no immediate-delivery promise or automatic republish on reconnect. Implementation remains open. |
| G07 — Upload results/errors | 201 and bundle list presence complete the command; build_info/pending errors are lost; noOp does not distinguish an error bundle | [Q07b accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q07b-accepted-cloud-logs-and-progress): confirmed stage plus elapsed time, measured percentages only; no timer-driven success or invented Pending reason. Separate accepted/processing/published/error and preserve deploymentId/build_info/pending errors. No successful Publish from 201 alone. Implementation remains open. |
| G08 — SOTA tooling/artifacts | No service command family or team SP publication adapters; complete Brake profiles/Tire runtime are unconfirmed | Before connecting SOTA buttons, define actual artifacts, identity, profile/version, owner and shared Demo Control path. Mockup cards do not make services ready. |
| G09 — Subject / version selection | Actual assignment uses Subject + service identity + system_uid; POST has no version field. Group type and state semantics are accepted; the actual tenant UUID/ownership still needs a scoped integration read | Q09a–Q09c retain independent publication/assignment, one current Test and monotonic release semantics. [Q13a Subject retention is accepted](../planning/active/demo-studio-delivery-plan.md#q13a-accepted-subject-retention); no routine per-run Subject deletion. Implement the accepted binding reset/Group policy; actual object identity and integration/qualification remain open. |
| G10 — Repeated SOTA cycle | Mockup 2.6 now increments all three identities; real allocator integration remains missing. Current VDP preparation requires an explicit version, checks local version directories, and upload checks the Cloud maximum; neither provides cleanup-independent automatic allocation for all products | [Q09c](../planning/active/demo-studio-delivery-plan.md#q09c-accepted-service-update-completion) and [Q13b](../planning/active/demo-studio-delivery-plan.md#q13b-accepted-clean-run-release-continuity) accepted: Demo Control automatically assigns independent monotonic releases for VDP/Brake/Tire in CLI and UI. The operator chooses the profile, never a release number. Allocate once before packaging/signing; reuse it for publication/recovery and show it read-only. Preserve used numbers/profile bindings through Retire. Define minimal durable allocation, scoped Cloud reconciliation and uncertain/reserved-number handling in the existing shared core. No ordinary run archive; implementation/interface mapping and fresh-Unit sequencing remain open. |
| G11 — Instances / dependency | Assignment ≠ instances >0 ≠ running ≠ capability readiness; native FOTA dependency is unconfirmed | [Q09c accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q09c-accepted-service-update-completion): Cloud-confirmed expected installed version and required running instances complete the technical update; function readiness/results remain separate and mandatory for E2E. No success for zero/old instances, stale/missing evidence or unresolved errors. Minimum one instance and P7D are accepted; package mapping, runtime observation and functional proof remain integration work. |
| G12 — Full Cloud dashboard | Existing adapter selects VDP only. APIs expose services/nodes/components/monitoring, but presentation and metric normalization are missing | [Q07a accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q07a-accepted-cloud-observation-refresh): one shared map/monitoring read model without duplicate card/tab requests; resource metrics only while their monitor is visible. Integration, complete identity/error/freshness, known units and nullable values remain implementation work. |
| G13 — Cloud logs | SSH component logs exist; asynchronous Cloud log lifecycle is not integrated | [Q07b accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q07b-accepted-cloud-logs-and-progress): complete list/request/observe/view/download workflow in UI and shared democtl commands. Opening Logs reads existing records, not a new collection. Handle arrays of request IDs, team/Unit scope, bounded time range, waiting/offline/empty/error and safe text delivery. Expanded log UX is deferred by the latest user amendment; basic action errors/uncertainty remain required now. |
| G14 — Freshness | Mock observe is instant; actual Platform fetch is one-shot; the 60 s stale timer is not refresh; failures clear value | [Q07a accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q07a-accepted-cloud-observation-refresh): entry/post-action reads, pending 2s backing off to 10s, visible idle 10s; shared snapshot and last-known data with stale/source-unavailable on error. Hidden views add no polling, active operations are not cancelled, and fetch time is not device report time. Decision accepted; implementation remains open. |
| G15 — Park/Resume | CLI parser exists, implementation is NOT_IMPLEMENTED | [Q12a](../planning/active/demo-studio-delivery-plan.md#q12a-accepted-full-park-resume) accepts full-stop/preserve/resume without preparation replay. [Q12b](../planning/active/demo-studio-delivery-plan.md#q12b-accepted-prompt-park-refusal) accepts prompt refusal for conflicting active/uncertain changes, no queued Park or forced cancellation, and actual-outcome reconciliation. Exact ordering/source mapping and implementation/qualification remain open. |
| G16 — Shutdown order | 2.6 corrected: VM remains available until CM Offline and deprovision; current command uses this ordering | Implement the shared composition and partial recovery. Stopping simulation can trigger Safe Stop; respect unfinished-update refusal. No extra identity-rejection test. |
| G17 — Fresh overlay after retirement | Retired local disk remains after delete, but reprovisioning it is forbidden | [Q13a accepted](../planning/active/demo-studio-delivery-plan.md#q13-clean-cycle-cleanup-proposal): Finish demo uses scoped Retire; New cycle completes the same cleanup before fresh Create. Preserve the source image, permanent Cloud objects and published releases; reset owned bindings. Implementation and final call/error/order mapping remain open. |
| G18 — Product backend integration | Brake handlers exist; default main has no currentUnitContext and uses temp DB; democtl lifecycle/route/proxy missing; Tire implementation not found | [Q10a accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q10a-accepted-backend-preparation): prepare/reuse both backends with composed Create or Quick preparation through shared Demo Control, with current Test binding when known; opening dashboards is read-only and vehicle deployment remains separate. Persisted storage, query context/readiness, guest routing and partial-operation handling remain implementation/audit work. Simple health is not functional readiness. |
| G19 — Functional evidence | 2.6 uses qualified simulated driving episodes and separates product/native receipts; its algorithms and outputs remain illustrative, not real product proof | [Q10b accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q10b-accepted-overview-first-backend-dashboards): overview-first team dashboards show authoritative backend results/recorded advisory and compact event history, with service state separately from Cloud. Native vehicle advisory display remains separate from backend receipt. Preserve available event-time provenance, quality and empty/stale/error distinctions; no generated result. Field mapping, implementation and functional proof remain open. |
| G20 — Offline/advisory delivery | 2.6 separates delayed Cloud observation, queued backend receipts and expiring vehicle advisory; real external-uplink coverage and durable product behavior remain unqualified | [Q11 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q11-accepted-standalone-offline-episode): separate offline chapter on installed versions, preserving local vehicle operation and operator access; observe reconnection and correlated delayed backend receipts independently. No new release is required, but Q08a publication remains allowed. Prove actual backend-uplink fault coverage, local continuity, persistence/retry/acknowledgements and no duplicate functional events. No invented queue count or fixed recovery latency. Integration/E2E remain open. |
| G21 — UI action/result surface | Allowlist lacks individual deprovision/delete/park/resume, SOTA, metrics/logs; create/provision use all; public_result drops IDs/details | Extend shared API explicitly, without granting the browser arbitrary commands/paths/credentials. Receipts need safe IDs and actual scope. |
| G22 — Recovery | Native receipts are ephemeral, capped at 128; no general cancel; prepare READY noOp lacks readiness recheck; special upload recovery | [Q12b accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q12b-accepted-prompt-park-refusal): recover the existing journal and reconcile authoritative outcomes for recorded identities after interruption. Do not blindly replay publication/provisioning, invent cancellation or queue Park. Unknown outcomes remain explicit; show the next action. Durable integration, response-loss cases and qualification remain open. |
| G23 — Documentation | Earlier research/requirements contain mandatory approval, old upload paths/Fleet/campaign assumptions and deferred old-identity tests | Current Test amendment, replacement map and phase order are reconciled. P1 executable backend contract migration is tracked explicitly. Do not restore cancelled checks. |
| G24 — Timing/progress | Mock uses 2–4 s. Actual defaults/budgets include VM 90 s, SDK worker up to195 s, Cloud wait up to90 s, CM stop up to100 s; roles are partly sequential | These are upper budgets, not artificial delay on every call. Show current stage and measured elapsed time. This audit does not prescribe additional checks; remove duplication after defining the contract. |
| G25 — Identity/provenance | Mock hardcodes IDs/filenames/profile/version/rootfs values; local list is not a complete release catalog; manifest acceptedRevision trails working trees | [Q05/M04 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q05-accepted-factory-slots-and-versions): meaning/profile first, exact release secondary, raw placeholder/IDs in Details; empty differs from Unknown. Typed real IDs/versions/files/hashes and explicit verified profile-release binding still require implementation. Distinguish pre-provision Factory configuration from Cloud observations; use actual working-tree provenance until the next checkpoint. |
| G26 — Ordinary run cleanup | Q13b accepted owned backend-record deletion, no archives, retained release continuity; 2.6 now follows it | P1 context/selector migration and P3 shared Retire remain required; Park preserves records. No retention question remains open. |
| G27 — Supersession/cancel | 2.6 guards one unfinished update per identity and does not invent cancellation; REST schema does not define native cancellation/supersession | [Q08b/M07 accepted on 9 September 2026](../planning/active/demo-studio-delivery-plan.md#q08b-accepted-one-outstanding-update): one outstanding update per identity in the shared demo workflow; preparing/signing successors remains allowed, team state/authority stays separate while foreground mutations may serialize, and no hidden queue is introduced. For VDP, expected Cloud Installed closes this publication guard without requiring unavailable Running evidence. Confirm native edge semantics separately; no cancellation/rollback/supersession claim from the UI. Implementation/verification remain open. |
| G28 — Tenant/role/API capability | Public schema 6.1.53 does not prove tenant rollout; OEM/SP rights have not been checked live; SP is not a universal Unit-monitor reader | Before future live integration, perform one scoped read of current API/role capability and preserve explicit access status. Do not add blanket OEM rights or return Production rollout to scope. |

## 11. API contract for implementation after agreement

Paths below are relative to `/api/v11`. The working host comes from the appropriate credential profile. The current client uses `https://<cloud_url>:10000/api/v11/`, SDK/PKCS12 mTLS, TLS verification and an Aos host allowlist. Public `api.aoscloud.io` is the schema source here, not an instruction to change the tenant endpoint.

| Operation / authorization in public schema | Request | Successful response and important restrictions |
|---|---|---|
| Check own identity | GET `/users/me/` | Detailed user/owner/role/effective permissions; establishes access, not readiness of all services. |
| Provision, OEM | POST `/units/provisioning/` through official SDK | 201; do not construct CSR/node/certificate exchange manually in UI. |
| Unit read | GET `/units/{U}/` | `status`: new/provisioned; `online_status`: Offline/Connected/Online; components/config/nodes/subjects and update information. |
| Unit Set membership, OEM | POST `/unit-sets/{Q}/units/` `{system_uids:[UID]}`; DELETE `/unit-sets/{Q}/units/remove/` with the same shape | 201 / 204; verify membership by read, not an expectation that response proves runtime readiness. |
| Deprovision/delete, OEM | DELETE `/units/{U}/deprovision/`; DELETE `/units/{U}/` | 204; deprovision requires Offline. Current democtl additionally defines its local/guest ordering. |
| Bundle upload, OEM or SP, `deployment_bundles_create` | POST `/deployment-bundles/upload/`, multipart `file` | 201: id, state, items, build_info, file_size. HTTP code does not guarantee Ready/Installed. |
| Bundle processing, `deployment_bundles_list` | GET `/deployment-bundles/` | Page with state filter and pagination. **GET `/deployment-bundles/{id}/` is absent from the schema**. DELETE by ID exists but is unnecessary for normal observation. |
| Component version catalog | GET `/components/{C}/versions/`, GET `/components/{C}/versions/{CV}/` | Version/reported_version/is_fake/metadata/state; fake 0.0.0 is not a published working bundle. |
| Verification batch | GET `/verification-batch/` and `/{B}/`; for separate approval, PATCH `/{B}/` `[{architecture:"arm64",is_approved:true}]` | Read/200 PATCH; **not a mandatory Test verification-set gate** and not cancellation of installation. |
| Explicit send component (not the normal Test path) | POST `/units/{U}/components/send-requests/` `{update_component_ids:[CV]}` | 201 request array; requires version UUID. Current `component send` has approval/Online guards. Do not use it as a silent fallback after ordinary upload. |
| Service version read, SP owner / associated OEM | GET `/services/{S}/service-versions/`; GET `/services/versions/{SV}/` | Version/container state/build_info, min_num_instances, layers/config/quotas. Ready container is not a running instance. |
| Subject service assignment, OEM `subjects_services_create` | POST `/subjects/{Q}/services/` `{service_ids:[S]}` | 201 `{subject_id,service_ids}`. No version or numInstances field in the request body. |
| Subject Unit binding, OEM `subjects_units_create` | POST `/subjects/{Q}/units/` `{system_uids:[UID]}` | 201 SubjectUnitCreateInfo; binding to a specific system_uid. |
| Subject deletion, OEM `subjects_delete` — excluded from routine Retire by accepted Q13a | DELETE `/subjects/{Q}/` | Reference only; the dedicated demo Subject is retained across runs. OpenAPI 6.1.53 has a misleading summary, “Delete the specified service provider.” Its detailed description, operationId `subjects_delete`, tag and UUID parameter identify a Subject. Do not target an SP or infer cascade behavior from that summary. Any separately authorized Subject deletion would require exact scope, ordering and tenant qualification; 204 must be followed by scoped reconciliation. |
| Service runtime observation | GET `/units/{U}/subjects-services/`; GET `/units/{U}/subjects-services/{S}/` | **Both return pages**. Versions/instances, run_state, pending/installed status, error codes/messages. Service detail is not a single instance; multiple subjects are possible. |
| Monitoring, OEM/FleetOwner | GET `/units/{U}/monitoring/` with filters; `/monitoring/dashboard/` with not_older_than | Arrays. Nullable samples with time/node/service/subject/instance; units/normalization need clarification. |
| Unit logs, OEM `unit_logs_*` | GET/POST `/unit-logs/`; GET `/{L}/`; GET `/{L}/download-log-file/` | POST201 **array**; asynchronous states; OpenAPI does not detail the download body. |
| Service logs, SP `service_logs_*` | GET/POST `/service-logs/`; GET `/{L}/`; GET `/{L}/download-log-file/` | POST201 **array**; required unit/service/subject/request_type/date_from. Scope must belong to the team. |

Important: `pending_component_status` is a free string in the schema, not a guaranteed enum of mockup stages. Component artifact state and service container state use different value sets. Do not apply one universal Ready/Running mapping to every entity.

## 12. A coherent target sequence

This is a record of the accepted target based on the final audit, **not an instruction to execute now**. The order below incorporates the accepted [M02 Create/publication decision](../planning/active/demo-studio-delivery-plan.md#m02-accepted-create-and-platform-publication) and [Q03 initial connection decision](../planning/active/demo-studio-delivery-plan.md#q03-accepted-initial-vehicle-connection), dated 9 September 2026; design choices are closed; actual implementation/qualification findings remain distinct.

| Stage | Target sequence | Current blockers |
|---|---|---|
| 1. Open | Read local session/image catalog, existing operations and Cloud observation; offer explicitly selected Full story or Quick preparation under [accepted Q04b](../planning/active/demo-studio-delivery-plan.md#q04b-accepted-preparation-modes). Page opening and mode selection do not initiate mutations | Recovery/freshness, G14/G22. Quick preparation uses the same ordered operations as the visible chapters, shows completed work honestly and stops before driving/Safe Stop. |
| 2. Create / Connect / Platform / Provision | Selected image → fresh Test overlay and boot/DNS/role → simulator/Gateway and initial stationary Manual connection → visible Platform Team preparation/signing/publication of new VDP v1 → provision the running, locally connected controller → Online → Test verification membership | G01/G02/G03/G04. M02/Q03 order accepted; publication and provisioning guards still need implementation. No automatic Safe Stop, stop/start or detach/reconnect workaround. Do not hide the first publication in preparation. |
| 3. First VDP | Autopilot → Safe Stop → Cloud Installed; show Runtime only from available Cloud evidence | G05. No additional approve/install click. |
| 4. Brake v1 | SP publish → OEM Subject assignment → instances/runtime → driving event → backend result | G08/G09/G11/G18/G19. |
| 5. VDP v2 / Brake v2 | New VDP profile-v2 release → Safe Stop update; service-v2 publish with agreed assignment semantics → functional assessment | G05/G09; do not promise a separate Deploy version operation absent from the API. |
| 6. VDP v3 / Brake v3 / Tire | Corresponding VDP transition → service releases → real backend records/advisory | G08/G11/G18/G19/G20. |
| 7. Offline segment | Q11: installed versions → vehicle external OFF → local function/advisory with suitable inputs → ON → independently observed Cloud reconnect and correlated durable product receipts | G06/G20 implementation and replay qualification remain open. [Q08a](../planning/active/demo-studio-delivery-plan.md#q08a-accepted-offline-publication) still permits scoped Offline publication; [Q11](../planning/active/demo-studio-delivery-plan.md#q11-accepted-standalone-offline-episode) does not require publishing an update in this standalone chapter. No automatic republish, VM restart or instant-drain claim. |
| 8. Completion/repeat | Park/Resume or Deprovision → Delete → local Retire → fresh overlay with the same image SHA; new monotonic release versions for **all repeated profiles** | G10/G15/G16/G17/G26. |

### Accepted decisions and implementation conditions

1. **Accepted on 9 September 2026:** [Q04a/M01](../planning/active/demo-studio-delivery-plan.md#q04a-accepted-test-scope-and-production-presentation) uses one Test VM, with Production visible but disabled as Deferred and CLI production/all retained. Align existing guards and backend context; do not create a hidden Production VM. Implementation remains pending.
2. **Accepted on 9 September 2026:** Create includes boot; Platform Team visibly prepares/signs/publishes fresh VDP v1 before Provision. The earlier disk-only recommendation is superseded by [M02](../planning/active/demo-studio-delivery-plan.md#m02-accepted-create-and-platform-publication). The democtl contract change and its verification remain pending.
3. **Accepted on 9 September 2026:** [Q06](../planning/active/demo-studio-delivery-plan.md#q06-accepted-cloud-runtime-evidence) allows Cloud Installed with runtime Not reported for the first UI milestone if the final audit confirms no supported runtime source. Actual engineering/E2E runtime qualification remains required; the panel never substitutes direct VM reads. Gate/progress details remain distinct from this decision.
4. For an already assigned service, Publish update may be the operator's final action; Deploy applies only to first assignment of the service identity. If manual rollout of every version is required, first confirm a platform-supported mechanism.
5. **Accepted Q13b:** Retire deletes owned ordinary run records without backups/archives, preserving release-number continuity; Park retains the current run. Implement scoped cleanup, not a new retention decision.

The remaining register items are specific integration work, not reasons to rebuild the VM or create another experimental VDP release.

## 13. Audit basis and reproducibility

This audit inspected the **current working tree**, including uncommitted changes, not only HEAD. It does not claim those changes have already been committed or released.

| Repository | HEAD at inspection | State relevant to the audit |
|---|---|---|
| aosedge-sdv-demo | `dfd958bb57e08fc7d23216124685872af293fe67` | Dirty Demo Control/Presenter/source/workspace/docs, including untracked connectivity implementation/tests. |
| carla-ego-runtime | `a3e22ae1067a3cdcada191dc683380fcd386368a` | Dirty native Driving Control/VISS/runtime tool and associated docs/tests. |
| brake-health-cloud | `1320dde24ae0f72771ea9320c2bd2212c20726ba` | Clean; HTTP query implementation exists, but startup integration is insufficient. |
| brake-health-service | `63b0c5fd43572ff96c508abc5e35818218d3500a` | Canonical source inspected; the complete claimed SOTA flow is unconfirmed. |

The table IDs cover the earlier and current interactions; retired 2.5-only controls are explicitly marked. Current logic uses operation, createSteps, publishSteps, provisionSteps, pump, emitResult, flushResults, park/resume, reconcile and retire. Hidden fault injection remains mock-only.

### Local sources

- [Mockup transitions][mock], [mockup event handlers][mock-handlers].
- [CLI parser][cli], [result model][models], [application dispatch][application], [Presenter operation mapping/receipts][operations], [Presenter HTTP layer][presenter].
- [Image catalog][images], [Environment create][environment], [Environment retire][environment-retire], [VM lifecycle][vm], [Unit lifecycle][units], [official provisioning SDK adapter][unit-sdk], [Cloud transport][unit-cloud].
- [Demo preparation][prepare], [native access/password][native-access], [simulation/vehicle source][source], [external connectivity][connectivity], [guest/source integration][source-guest], [native driving controller][native-control].
- [VDP local/build/sign/publication operations][components], [official signer adapter][signer], [Cloud reads/guards][component-cloud], [VDP profile contract][vdp-contract].
- [Current demo-control architecture][control-doc], [historical lifecycle research][lifecycle-research], [earlier decision register][decisions], [earlier orchestration requirements][orchestration], [original interaction specification][interaction].
- [Platform Cloud projection][platform-model], [Presenter refresh/freshness][presenter-provider].
- [Brake service repository][brake-service], [Brake HTTP implementation][brake-http], [Brake backend main][brake-main], [Brake backend server defaults][brake-server], [Brake query/admin contract][brake-contract], [Tire API contract][tire-contract].

### Public sources

- [Aos Cloud OpenAPI JSON, inspected `info.version=6.1.53`][openapi].
- [Verification Unit Set description: updates without additional approval][verification-doc].
- [Service updates: verification-set behavior and version increments][update-doc].
- [Official service flow: SP publication and Subject assignment][service-doc].

[mock]: ../demo/mockups/aosedge-demo-interaction-mockup-2-6.source.html
[mock-handlers]: ../demo/mockups/aosedge-demo-interaction-mockup-2-6.source.html
[cli]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/cli.py "Audit source line 29"
[models]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/models.py
[application]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/application.py
[operations]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter_operations.py "Audit source line 35"
[presenter]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/presenter.py
[images]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/images.py
[environment]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/environment.py "Audit source line 207"
[environment-retire]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/environment.py "Audit source line 505"
[vm]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/vm.py
[units]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/units.py "Audit source line 78"
[unit-sdk]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/unit_sdk.py
[unit-cloud]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/unit_cloud.py
[prepare]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/demo_preparation.py "Audit source line 21"
[native-access]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/native_access.py "Audit source line 57"
[source]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/source.py
[connectivity]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/connectivity.py
[source-guest]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/source_guest.py
[native-control]: ../../../carla-ego-runtime/tools/KeyboardControl.swift "Audit source line 980"
[components]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/components.py "Audit source line 95"
[signer]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/component_worker.py "Audit source line 46"
[component-cloud]: ../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/component_cloud.py "Audit source line 21"
[vdp-contract]: ../../contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json
[control-doc]: ../architecture/demo-control.md
[lifecycle-research]: demo-foundation/r2-aoscloud-lifecycle.md
[decisions]: ../requirements/d4-decision-register.md
[orchestration]: ../requirements/components/demo-orchestration.md
[interaction]: ../demo/mockups/aosedge-demo-interaction-specification.md
[platform-model]: ../../apps/presenter-ui/src/domain/platformObservation.ts
[presenter-provider]: ../../apps/presenter-ui/src/app/state/PresenterReadModelProvider.tsx
[brake-service]: ../../../brake-health-service/README.md
[brake-http]: ../../../brake-health-cloud/apps/backend/src/brake-data-http.ts
[brake-main]: ../../../brake-health-cloud/apps/backend/src/main.ts
[brake-server]: ../../../brake-health-cloud/apps/backend/src/server.ts
[brake-contract]: ../../contracts/brake-cloud-api/brake-cloud-query-admin-profile.v1.json
[tire-contract]: ../../contracts/tire-cloud-api/tire-cloud-api-profile.v1.json
[openapi]: https://api.aoscloud.io/api/v11/openapi.json
[verification-doc]: https://docs.aosedge.tech/docs/quick-start/create-unit-set
[update-doc]: https://docs.aosedge.tech/docs/how-to/updates-and-campaigns/update-service
[service-doc]: https://docs.aosedge.tech/docs/how-to/run-your-application/run-qm-service
