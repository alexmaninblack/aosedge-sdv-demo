<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# First-use OEM/SP configuration audit — 15 September 2026

- Status: Implemented; staging setup, provisioning and VDP passed; service delivery remains open
- Version: 1.3
- Prepared: 2026-09-15
- Owner: Demo Solution Team
- Context: [unsigned-package live checks](unsigned-package-signing-2026-09-15.md)
- Contract: [certificate-selected Test Cloud](../architecture/certificate-selected-cloud.md)

## Implementation and live qualification

### Later lifecycle disposition — 15 September, 14:38 UTC

The staging Units described below are dated observations. The later manual
unprovisioned Test completed Finish through Presenter in 2.70 seconds after
upload-receipt reconciliation was made independent of Unit provisioning.
There is no current Test to resume. See the [source checkpoint](staging-source-checkpoint-2026-09-15.md)
for current scope, regression results and unresolved publication/service-data
qualification. Factory `.33`, Cloud releases and version continuity remain.

### Post-reboot registration recovery — 15 September, 13:29 UTC

The selected staging domain and OEM certificate agreed. The exact current Test
was already `provisioned` / `Online`; its detail response returned
`unit_sets: null`. Demo Control incorrectly iterated that null, reporting
`UNIT_CLOUD_UNAVAILABLE_TypeError` before binding the local Unit/Node IDs.

The reader now normalizes explicit null memberships, and the Presenter exposes
**Continue registration** for an owned partial registration. Through that UI
action, registration completed in approximately seven seconds: existing source
bound, Test verification membership confirmed, and Presenter showed **ONLINE**.
No repeat SDK registration, VM restart, source reset or Production mutation
occurred. Unit remains `558cf923-9ccc-46ee-b3c8-ace1c05bdcbe`.

Targeted checks: 39 Unit tests, 11 Presenter tests, two browser registration
tests, and the Presenter production build passed. Browser tests use isolated
fixtures; the seven-second recovery above was the real staging run.
At this checkpoint, VDP `60.0.0` remains Cloud **PROCESSING**, with factory
`0.0.0` reported installed. Recovery does not establish publication or full E2E
completion; the previous-run results below are not claims for this new Unit.
The 13:30:49 UTC read confirmed the exact bundle remains `uploaded`,
`build_info: null`, `items: null`, and has no catalog version. Test has the
expected verification-set membership, no FOTA block, and no pending component.
Thus Safe Stop is not the current publication blocker. The reason Cloud has not
processed this accepted upload is not established; no replacement version or
repeat upload was submitted.

The approved first-use increment is implemented in Demo Control and Session.
`democtl cloud check` performs GET-only prerequisite discovery; `democtl cloud
prepare` explicitly creates only absent matching demo configuration. Test-only
provisioning no longer requires a Production set. Authenticated owner contexts
and publication paths distinguish tenant replacement from certificate renewal;
uncertain creation/publication receipts remain protected against blind replay.

### Actual staging run — 15 September

All lifecycle and assignment mutations used Demo Control. The retained .33 Test
was resumed rather than recreated. No image build, new release, repeated upload,
Production mutation or campaign change was performed by Demo Control.

| Check | Observed result |
| --- | --- |
| First preparation | Created `aos-vm;1.0.0` with the exact tracked single-node configuration and one Test Vehicles verification set in existing Default |
| Node registration | Model creation did not create a Node Type. Provisioning subsequently registered `aos-vm-main`. Check now reports `AFTER_PROVISION` only before a Test Unit exists, avoiding a first-use deadlock |
| Repeated preparation | `READY`, `noOp: true`, 1.48 seconds; no additional POST |
| Test provision | Completed in approximately 28 seconds; Cloud Online, one Main Node, Test verification membership confirmed |
| VDP 58.0.0 / functional v1 | Observed pending while driving; installed and active after native Safe Stop; active slot matches process, 7 read paths, LIVE data, zero VDP restarts |
| Brake 37.0.0 / Tire 25.0.0 | Existing SP bundles `done` / `Done`; exact versions `ready`; no republishing |
| Service assignment | Separate retained Group Subjects created and bound to current Test and the corresponding service IDs; both assignments confirmed by Cloud reads |
| Service delivery/runtime | **Not passed:** repeated Desired Status observations contain only VDP, no Brake/Tire service items; Cloud service runtime and native container lists are empty |
| UI | Session exposes explicit Check/Prepare, displays all prerequisite rows, and Vehicle shows installed VDP 58.0.0; no automatic provisioning/publication on opening Session |

The four unrelated campaign sets were preserved. Cloud automatically included
the new Test in two existing campaign sets (canary-small and blue/green-blue)
as well as the explicitly assigned Test verification set. This is an observed
Cloud-side membership effect, not a Demo Control assignment; no campaign policy
or membership was modified to try to force delivery.

### Bounded unresolved service-delivery evidence

- Cloud lists both Group Subjects under Test `assigned_subjects`, each with the
  correct service. `reported_subjects` is empty.
- Per-Subject resource-conflict lists and the OEM blacklist are empty.
- Both processed service versions report `min_num_instances=1`,
  `container_config_data=null`, and `layers=[]`. Those optional legacy fields
  alone do **not** prove a broken archive or a package-format defect.
- Node details report `cpus[].archInfo.architecture=arm64`; the separate
  `architecture` field is null. This is evidence, not a demonstrated cause.
- CM receives Desired Status and acknowledgements, remains active with zero
  restarts; VDP delivery succeeded. No SM service-install attempt can be claimed
  for services absent from Desired Status.
- The selected OEM receives HTTP 403 for `GET /fleet-validation-batch/`.
  This does not establish that approval is required; no approval mutation was
  attempted. The documented [verification-set service workflow](https://docs.aosedge.tech/docs/how-to/updates-and-campaigns/update-service)
  bypasses manual approval for the designated verification Units.

Next investigation is the selected staging Cloud's service eligibility /
Desired Status composition for these already Ready versions and assigned
Subjects. Preserve the failing Unit and receipts. Do not infer a new package,
Safe Stop, CM/SM patch, extra Subject activation or campaign mutation from these
observations. Service execution and synthetic backend ingestion remain open;
the first-use setup result must not be presented as a complete E2E pass.

Final local state: existing Test preserved Online, native vehicle stopped in
Safe Stop (0.0 km/h, brake 100%), VDP 58.0.0 active; presenter and runtimes remain
available for inspection. No retirement/reprovision loop was used.

### Regression evidence

- 227 targeted Python tests ran in 5.66 seconds: 226 passed, one existing skip, covering
  setup, denied/missing/conflicting reads, uncertain creation, repeat no-op,
  Test-only/dual-role boundaries, owner replacement and renewal, publication
  reconciliation, service assignment, lifecycle and presenter operations.
- All 127 Presenter UI unit tests passed (14 files); production UI build passed.
- Live Session Check and plain terminal `cloud check` displayed all eight current
  staging prerequisite results. The terminal formatter regression is covered.
- Documentation quality gate passed (196 Markdown documents); `git diff --check`
  passed. This is a working-tree verification, not a new commit/push receipt.
- Tests did not create another VM, allocate another version or mutate a tenant.

## Initial audit and live inventory (before implementation)

New catalogs work: staging accepted VDP 58.0.0, Brake 37.0.0 and Tire 25.0.0,
all Ready, using current OEM/SP certificates. The same unprovisioned .33 Test
is parked with these receipts retained. The missing capability is first-use
OEM configuration, not another rebuild.

Checks used the selected staging API v11, its live OpenAPI schema and existing
Cloud adapters. No Cloud mutation, Production API access or VM restart was
performed during this audit. Private account IDs and credentials are omitted.

| Item | Actual staging observation | First-use treatment |
| --- | --- | --- |
| OEM/SP authority | Valid certificates, matching roles, required model/set/Subject permissions present | Authenticate each role; certificate domain alone is insufficient |
| SDK | Installed 5.4.2; Cloud minimum 0.7; guard passes | No replacement needed |
| OEM architecture | Exactly arm64 | Matches existing packages |
| Fleet | Existing Default fleet | Reuse; another fleet is unnecessary |
| Unit Sets | Four unrelated campaign sets, all non-validation; neither demo role set exists | Preserve them; prepare a dedicated demo verification set |
| Unit Models | Empty | Establish the exact demo model/configuration |
| Node Types | Empty | Verify the type from Unit Configuration, not automatically a separate manual create |
| VDP | New component identity created by successful upload | No pre-created UUID or historical certificate needed |
| SP services | Both Ready and visible to OEM under current SP | No additional SP association is shown missing; installation not yet proven |
| Subjects | Empty | Expected before Deploy; democtl already creates them |

**Correction:** `Cloud.inventory()` filters by the two demo titles. Its earlier
`sets: []` meant no matching demo sets, not an empty OEM. Complete
`GET /unit-sets/` returned four unrelated campaign sets. Do not rename or
delete those sets to satisfy the demo naming convention.

## Platform contract versus our assumptions

Official [device integration documentation](https://docs.aosedge.tech/docs/how-to/register-your-device/with-your-HPC-device/)
allows automatic Target System registration during provisioning but describes
separate Unit Configuration registration. Node Types are listed from that
configuration. Empty model/type lists do not prove two independent manual
creation requirements.

Our tracked identity is `aos-vm;1.0.0`, one `aos-vm-main` Node. Use the
[single-node configuration](../../config/aosvm-single-node-unitconfig.json):
label `main`, priority 100. The parked guest identity was not reread in this
audit. Match the selected Factory contract, not the upstream two-node example.
The live API supports `POST /unit-models/` with `name`, `version`, `unit_config`.
An explicit preparation can ensure this configuration; it must never overwrite
an incompatible in-use model. The [Unit ontology](https://docs.aosedge.tech/docs/reference/ontology/unit)
places automatic Node Type registration at provisioning, not model creation.

Before this increment, `UnitService._bindings` required Test Vehicles (validation) and
Production Vehicles (non-validation) in the same fleet even for Test-only
provisioning. Opposite-role checks also assume both sets. The live provisioning
request has no Unit Set field: requiring the pair is our constraint, not an
Aos requirement to create Production before Test.

SDK registration does not select a fleet. Default receives new Units, whereas
`_bind_unit` requires the Unit fleet to match its role set. Reusing Default
is consistent; another fleet needs an explicit supported association.

## First publication and Subject setup already supported

Unsigned prepared content has no authoritative Cloud owner/service UUID.
Sign uses the current OEM or matching SP credential. Upload resolves the
current owner's catalog and supports authoritatively absent identities.

Presenter Deploy calls `service runtime-prepare test`, then
`service assign <service-id> --target test`. Assignment verifies current Test
and verification membership, then creates an owned Group Subject, binds Test
via `system_uids`, and assigns the service via `service_ids`.

There is one dedicated Subject per service: AosEdge SDV demo Brake and
AosEdge SDV demo Tire. An unrecorded same-label Subject is a conflict, not
silently adopted. Packages set `instances.minInstances: 1`, `offlineTTL: P7D`;
assignment has neither version nor instance count. This follows the
[Subject-based delivery workflow](https://docs.aosedge.tech/docs/quick-start/).

No validation-batch approval is added to the accepted verification story.
Components require Safe Stop; services do not. The deferred KUKSA permission
issue remains; services use explicit synthetic data, not vehicle telemetry.

## Approved implementation packet

1. One explicit first-use report in Session/democtl: both authorities,
   architecture, Default fleet, verification set and Factory model/config.
   Detect missing prerequisites together, before provisioning.
2. Explicit idempotent preparation through democtl after approval: create only
   absent demo-owned settings, re-read results, preserve unrelated objects.
   No mutations on page open/status refresh; denied reads and uncertain POSTs
   are not absence and never justify blind retries.
3. Prefer removing the mandatory Production-set dependency from Test
   provisioning/binding/retirement. Otherwise today's code requires an unused
   empty Production Vehicles set in staging. Preserve the existing dual-role CLI.
4. Distinguish tenant replacement from certificate renewal. Selection/journal
   scopes are principally domain-based; publication paths use domain plus
role. Owner guards prevented mismatched adoption, but switching to
another OEM/SP inside the same domain needed explicit tenant contexts. Contexts
   must include authenticated owner IDs without discarding uncertain receipts.
5. Preserve reusable model/set settings and release continuity across Finish;
   retire only the owned run. Never transplant another Cloud's IDs.

Minimum next work here: exact single-node model/config plus a dedicated
verification set in existing Default, and resolution of the dual-set code
dependency. Then use the three already Ready releases. Provisioning,
installation, runtime resources, backend service data and E2E remain separate
checks; this audit does not close them.

Execution order: amend the contract, implement `democtl cloud check` (GET-only)
and `democtl cloud prepare` (explicit create-if-absent), connect both to Session,
test missing/repeat/conflict/uncertain and tenant isolation, then prepare the
selected staging and resume the retained Test with its already Ready releases.
No Factory rebuild, new release allocation or unrelated campaign/Production
mutation belongs to this packet. Subjects remain lazy, per-service Deploy steps.

## Inspected implementation

`units.py` (_bindings/_bind_unit/_provision), `unit_cloud.py` (inventory),
`unit_sdk.py` (registration), `cloud_connection.py` and `package_artifacts.py`
(context keys), `services.py`, `service_cloud.py`, `service_publication.py`
(catalog/visibility), `service_assignment.py` (create/bind/assign), and live
OpenAPI v11 UnitSetInputSchema, UnitModelInput, UnitProvisioningCreateSchema,
Default fleet and Node Types routes.
