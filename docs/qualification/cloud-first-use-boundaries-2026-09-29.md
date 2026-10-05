<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cloud First-use Boundary Proof — 29 September 2026

This is the historical pre-implementation checkpoint. The subsequent
[product implementation and candidate evidence](cloud-first-use-implementation-2026-09-29.md)
supersedes its unimplemented status, not its recorded observations or exclusions.

- Status: Read-only live observation and transient proofs passed; both design choices accepted; product integration remains unimplemented
- Version: 1.1
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0`, existing uncommitted work preserved
- Plan: [Installable distribution and reproducibility](../planning/active/installable-distribution-and-reproducibility.md)
- Previous gate: [Kit 012 / Setup 020 consolidation](installer-consolidation-2026-09-29.md)

## Scope

Continue Stage 3 after the independent workspace-metadata correction. Inspect
the two outstanding Cloud first-use boundaries before introducing another
installer build: secure new-certificate enrollment and explicit reuse of exact
existing service assignment Subjects. This is not completed onboarding, a
change to the accepted trust model, a new Test or clean-Mac qualification.

No installed application, selected version, run journal, credential reference,
VM, Cloud object or backend data was changed. No real token was requested,
received or submitted. No additional kit, Factory or simulator was built.
`VDP-TIMEOUT-01` remains deferred. The existing Kit 009 Test and the separate
empty Kit 012 instance remain distinct; window-state success did not authorize
switching a retained run to Kit 012.

## Enrollment transport finding and transient proof

The pinned `aos-keys 1.10.0` implementation calls its certificate-issuance POST
again after `SSLError`, omitting the explicit packaged CA on the second call.
A deterministic synthetic transport reproduced **two invocations with different
trust arguments**. This is a code-path proof, not evidence that a live token
was consumed twice. The CLI also has browser-install/version-check behavior,
so calling it unmodified is not the accepted native enrollment boundary.

A transient candidate uses the SDK's key/CSR and PKCS#12 conversion functions,
with a fixed, one-shot transport envelope. The experiment enforces packaged
CA trust, no redirects, no environment-derived proxies/trust, zero transport
retries, bounded response reads, input/domain checks and certificate/key/domain/
validity consistency. A pre-dispatch intent callback must succeed before the
single request. Errors expose fixed codes, not response bodies or tokens.
Certificate receipt is explicitly not proof of OEM/SP roles or association.

Ten tests pass, including SSL errors, timeouts, disconnects, redirects, HTTP
errors, malformed/duplicate/oversized JSON, expired/wrong-domain/wrong-key
certificates, failed intent and invalid inputs. The final execution denied
network access at the OS level. Keys, tokens and certificates were synthetic
and remained in memory; no secret material was placed in evidence.

This does **not** implement durable attempt/key storage, crash/restart recovery,
native secure input, token issuance, role authentication or live enrollment.
The candidate's transport bounds and accepted success statuses are experimental
implementation details, not a newly accepted executable product contract.
The inspected SDK exposes no request-ID-based reconciliation in this enrollment
function; this does not prove the Cloud server lacks another recovery API.

## Exact existing Subject references

The [earlier installed run](installed-clean-e2e-2026-09-28.md#existing-account-subject-reconciliation)
needed an explicit engineering reconciliation because the new instance had no
recorded Subject UUIDs. Existing-access setup currently checks identities,
association and delivery prerequisites, but does not resolve that later Deploy
collision. Never infer consent to adopt an existing object from its label.

A separate fixture prototype exercises exact supplied Subject/service/creator/
OEM/SP identities using existing authoritative readers and validators. It
requires the proper Subject type and priority, one expected service owned by
the selected SP, complete unambiguous inventory and **zero desired and reported
Unit recipients**, including service recipients through another Subject.
It performs no configuration write, adoption or Cloud mutation.

Eleven tests pass: first/repeat for both services, no label-only adoption,
changed owner/creator/identity, duplicate/absent labels, wrong type/protection,
desired/reported recipients, peer services, denied permissions, incomplete
pagination and fresh reread after a changed binding. The final execution denied
network access at the OS level. This is not an implemented reference-selection
UI or restart-safe local reference store.

## Current retained Test — actual read-only observation

Existing authorized OEM/SP references were used through the retained installed
Demo Control GET-only assignment observer. Selected manifest remained
`f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`.
Exact Test Unit: `ee0a8607-5359-47ee-b5a6-4f50568d2b3a`.

| Team | Exact Subject | Service release checked | Observation UTC | Observer duration |
| --- | --- | --- | --- | --- |
| Brake | `78d05c9c-cdf6-45cc-ab28-df2a4d3ac0d7` | 96.0.0 / V3 | 11:37:36.331897 | 3.305 s |
| Tire | `ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb` | 50.0.0 / V1 | 11:37:38.461297 | 2.208 s |

Both Subjects remain bound to this exact Test and their expected service;
both queried packages are Cloud-ready. These observations are not a live
advisory/telemetry test, because the vehicle runtime remains parked. They prove
the Subjects are **not free for another installation**. An offline VM is not
a retired Unit. The observer compared journal and selection bytes before/after
and proved both unchanged. There was no POST, unbind, deletion or provisioning.

## Verification and evidence

- Existing source regression: **96 tests passed**, no skips, in 0.604 s:
  `test_cloud_first_use`, `test_cloud_setup`, `test_cloud_connection`,
  `test_service_assignment`; network denied by the OS.
- Transient enrollment proof: **10 tests passed** in 0.013 s in the final
  network-denied execution (initial execution 0.024 s).
- Transient Subject proof: **11 tests passed** in 0.003 s in the final
  network-denied execution (initial execution 0.005 s).
- The first attempt to create a nested OS sandbox was rejected before the
  interpreter started. Rerunning with permission to install the same restrictive
  sandbox is a harness correction, not a product or Cloud retry.
- No product source was changed or promoted by this checkpoint. Prototype code
  is retained only in the ignored `CarlaSim/Build-distribution-stage2-20260926`
  evidence directory: `enrollment_transport_probe_20260929.py`,
  `subject_first_use_probe_20260929.py`, and
  `observe_retained_subjects_20260929.py`.
- Observed reserve: approximately 163 GiB internal and 483 GiB on SDV-Work.
  No large copy or cleanup was performed; warm caches, current images and video
  materials are unchanged.

<a id="accepted-decisions--29-september-2026"></a>
## Accepted decisions — 29 September 2026

The user explicitly accepted both proposed behaviors after reviewing this
checkpoint, and directed continuation under one end-to-end plan without routine
intermediate approval questions. The choices below are closed. This acceptance
does not retroactively turn the prototypes into product implementation or
authorize an unspecified live token request, resource retirement or publication.

1. **Explicit existing-object reuse:** offer a separate exact-reference selection
   and fresh validation step, not automatic discovery/adoption by label. Only
   unbound objects are eligible. Save only public references in the existing
   configuration authority; do not create a vehicle journal or import historical
   run state. Recheck under the existing writer before later consumption.
   The alternative of creating new objects for every installation was not
   selected. Never silently delete or replace same-labelled resources.
2. **Lost issuance response:** preserve the private attempt/key, block automatic
   replay and show an explicit access-recovery state. Obtain a replacement token
   through the official Cloud process only after the uncertain attempt is
   reconciled. A new token alone does not prove the earlier certificate was not
   issued or authorize discarding its key. Fully automatic Cloud reconciliation
   is not a prerequisite added to this release; any future implementation needs
   a separately supported server contract.

Next, freeze the bounded contract and corresponding
requirements before promoting code: local ownership, atomic private writes,
restart/repeat semantics, response-loss behavior, redaction and native feedback.
This is implementation work within the accepted choices, not another request
to approve them. Then run source/native gates and produce one small-input kit
update. New-account
live token use and retirement/replacement of the preserved Test are separate
exact-target actions, not implied by this read-only checkpoint. Continue to
keep lifecycle, cold first launch, distribution signing and clean-Mac gates open.
