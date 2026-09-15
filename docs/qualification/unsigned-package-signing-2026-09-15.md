<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Unsigned package and session signing verification — 15 September 2026

- Status: Dated offline/live publication evidence; subsequent setup, delivery
  and retirement are recorded in the first-use and source checkpoints
- Scope: [ADR 0016](../architecture/decisions/0016-unsigned-packages-and-session-scoped-signing.md)
- Branch: `codex/unsigned-package-signing`
- Initial implementation boundary: existing Test remained parked; no Cloud
  mutation, guest restart, provisioning, live signing or release allocation
  was performed until the separately authorized live follow-up below

## Implemented behavior

Canonical VDP source profiles are unsigned and pinned independently of the
destination certificate. VDP and service prepared content remains immutable.
Sign creates/reuses a context-specific representation using the currently
selected OEM or matching SP certificate. Same-path certificate rotation and
Cloud changes require a new signature, not a new payload or release number.

Service destination owner/catalog IDs are resolved at publication rather than
inherited from old prepared metadata. Attempt receipts are scoped to Cloud
and role and survive signer rotation; accepted/uncertain requests are not
resent. Unscoped legacy service attempts require reconciliation. UI Signed
state is invalidated by credential changes, and foreign-Cloud publication/job
facts cannot establish current publication readiness.

## Verification performed

| Check | Result |
| --- | --- |
| Targeted Python suite: source migration, VDP replay/signing/publication, service signing/publication/assignment, selected Cloud, Presenter operations/performance and status | 253 tests run, one existing skip, remaining tests passed; 18.8 seconds |
| Installed official Aos signer with disposable credentials | Real VDP, Brake and Tire signatures verified; repeated signing is idempotent; same-path rotation and another Cloud produce new representations |
| Unsigned/prepared integrity | Tampered pinned source and changed signed/prepared payload rejected; original prepared bytes and fixture release ledger unchanged |
| Publication routing | Legacy prepared service IDs not used for the target; exact current owner/service binding passed; signature rotation after acceptance only observes the recorded attempt |
| Worker consistency | Temporary private credential snapshot remains stable if the original file changes; removed after normal completion |
| UI | Typecheck and production build passed; 126 unit tests passed, including stale Signed and foreign-Cloud publication regression |
| Documentation | Navigation/version/traceability gate passed; HLA 1.7 and ADR 0016 links cascaded |
| Real source migration via democtl | `component unpack` for 1.0.16, 2.0.0 and 3.0.0 completed; repeat completed without overwrite; `component verify` reported `VERIFIED_PINNED_DIGESTS`, no structural problems and unsigned envelopes |
| Session preservation | Same unprovisioned Test, lifecycle `PARKED`; journal and release ledger byte-identical before/after migration |
| Presenter handoff | Idle server stopped and started through `democtl ui stop` / `democtl ui serve`; new client bundle served, no active/uncertain operation; local snapshot still reports the same parked Test |

The three actual source hashes are the accepted values in ADR 0016. Old
archives were retained. No VM image, manager binary or functional VDP/service
binary was rebuilt or altered. Actual release high-water marks remained VDP
57.0.0, Brake 36.0.0 and Tire 24.0.0; these are evidence, not operator inputs.

## Full-suite audit limitations

A broader discovery run executed 819 tests and was **not green**. It exposed
two generic Unpack fixtures using reserved source selector 2.0.0; those fixtures
now use an ordinary non-source selector and pass in the targeted gate.
The remaining findings are outside this package/signing increment:

- Five `test_studio_cloud_reader` cases construct the reader with `__new__`
  but omit its existing pool/publication state; they need alignment with the
  already implemented concurrent reader. The owned Presenter tests above pass.
- One QMP test still expects `quit` to be prohibited, although the previously
  accepted abnormal-Finish path permits a scoped force power-off.
- The sibling Platform copy of `aos-demo-service-inputs.py` differs from the
  current Demo Control source at the earlier conditional directory-fsync
  change. Source parity was not repaired by rebuilding or modifying Factory
  as part of this task.

These findings are recorded, not suppressed and not presented as a fully green
repository or a newly qualified Factory image. No broader gate is closed by
this targeted receipt.

## Operator continuation

Reload the Presenter after its idle server reload. The persisted lifecycle
must still show Parked. Use **Session → Resume**, then continue Prepare VDP V1
and Sign & publish with the selected staging context. Resume itself performs
no provisioning or publication. The controller allocates the next release;
the operator does not supply its number.

Real staging acceptance, provisioning, Safe Stop installation and service
deployment remain manual/live checks. Synthetic service data and the existing
KUKSA permission limitation are unchanged. No new live result is implied by
successful offline signature verification.

## Authorized live follow-up — 10:30–10:41 UTC

After the implementation handoff, the user asked the agent to perform the
checks independently. This superseded the earlier parked-only test boundary
for this run. All lifecycle, packaging, signing and publication operations
used the existing `democtl` commands in `apps/demo-orchestrator`. Autopilot
and Safe Stop used the native Driving Control buttons. One additional
read-only call through the existing Unit Cloud inventory adapter diagnosed
the provisioning preflight failure; no separate helper or mutation path was
introduced.

The selected staging OEM and Service Provider authenticated with matching
roles and valid current certificates. Production, the selected domain,
certificate files, Factory image and manager binaries were unchanged.

| Check | Observed result |
| --- | --- |
| Resume the same unprovisioned .33 Test | Completed at 10:32:15 UTC; Test, prepared backends, CARLA/Gateway and native controller started; Test connection restored in stationary Manual |
| VDP V1 Prepare | Allocated 58.0.0 from the pinned unsigned 1.0.16 source; seven read paths; historical certificate/signature failure did not recur |
| VDP Sign | Current OEM signature verified with RS256; repeated Sign returned `noOp: true` and the same signed digest |
| VDP Upload | One HTTP 201 response; Cloud processing completed with `Done`, publication `READY`, version `Ready`; repeated Upload reconciled the same deployment with `noOp: true` |
| Brake V1 | Prepared brake/37.0.0 from its existing build; current SP signature verified and payload matched prepared content; one upload accepted, then Cloud `READY`; repeated Upload observed the same deployment without resubmission |
| Tire V1 | Prepared tire/25.0.0 from its existing build; current SP signature verified and payload matched prepared content; repeated Sign reused it; one upload accepted, then Cloud `READY` |
| Native driving | Autopilot visibly moving at 19.3 km/h; Safe Stop visibly stopped at 0.0 km/h with brake 100% |
| Guest observation | Gate `OPEN`, no active VDP version, provider inactive; this is not an installation success and is consistent with an unprovisioned Test |
| Presenter after reload | Current vehicle Test; not provisioned; VDP 58.0.0 already submitted with Publish disabled; Brake/Tire show their new candidates and Cloud `READY`; Deploy disabled because registration is incomplete |
| Return to Park | Completed at 10:41:17 UTC: simulation, Test VM and both backends stopped; same overlay/connection context and published packages retained |

Exact deployment/version/service identifiers remain in the destination-scoped
local artifact receipts, not copied into public documentation. Automatic
release continuity now includes VDP 58.0.0, Brake 37.0.0 and Tire 25.0.0.
No certificate rotation or destination switch was performed during live
testing; those negative/cross-context cases retain their isolated test proof.

### Current blocker and explicit limits

`democtl unit provision test` stopped with
`ROLE_UNIT_SET_MISSING_OR_AMBIGUOUS:test` before any provisioning mutation.
The role-filtered inventory returned `sets: []`: no matching demo role sets,
not duplicate names. A subsequent full audit found four unrelated campaign
sets, all non-validation; the earlier claim that the entire OEM had no sets
was incorrect. The current provisioning contract requires
Test Vehicles (validation set) and Production Vehicles (non-validation set)
in the same fleet. The accepted Cloud-selection contract does not create
these objects automatically. No sets, fleets or Units were created to bypass
that boundary. Other staging provisioning prerequisites are not yet qualified.

Therefore guest delivery, installed/running VDP, service assignment/runtime,
backend service data and the complete E2E cycle remain **not verified** in
this staging run. Native Safe Stop alone cannot deliver software to a Unit
that has not been provisioned. Resume the preserved Test only after agreeing
the missing staging configuration; use the already published releases rather
than preparing replacement versions merely to retry provisioning.

The already-open Presenter retained its old Parked view after external CLI
operations until a page reload. After reload its local state and package
facts were correct. This CLI-to-open-page freshness limitation is recorded,
not claimed as a live auto-refresh success or fixed by this test-only turn.
