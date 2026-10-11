<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Missing service provider access after controller creation

The manual M1 journey on 11 October 2026 reached a provisioned Test with VDP
V1 installed, but Brake V1 preparation could not proceed because no usable
service-provider certificate reference was saved. Returning to Setup and
choosing an SP file did not resolve it: pair inspection is first-use only and
rejects an instance with a retained vehicle run. This was an operator-flow
defect; it did not establish a certificate or Cloud authentication failure.
The source correction and bounded live proof are recorded below; native
candidate acceptance is separate.

## Observed sequence

1. The operator selected OEM access in Presenter, created the controller and
   provisioned the Test with VDP V1 release `140.0.0`.
2. Brake V1 Prepare returned `SERVICE_RELEASE_CATALOG_UNAVAILABLE`. The SP
   reader's underlying reason was `SERVICE_CREDENTIAL_MISSING_OR_UNSAFE`.
   Preparation stopped before release allocation, signing or publication.
3. The operator selected an SP certificate path in Setup and chose
   **Inspect locally**. Inspection returned
   `CLOUD_FIRST_USE_CURRENT_RUN_RETAINED`; the generic native status was
   **Cloud step stopped — no readiness confirmed**.

The active installation uses the Kit028 manifest
`1cb2628a3c358d685441644b500a94598c826f976b0bcff13ab5e7144754fbef`.
This manual observation is separate from the corrected r8 scripted journey.

## Cause and original boundary

`CloudConnection.inspect_pair()` calls `_pair_stamp()`, which calls
`first_use_guard()` before inspecting either certificate. A vehicle journal,
pending journal or retained overlay triggers the rejection. Choosing a file
only changes the native form; the rejected inspection does not save its path.
Presenter's existing single-certificate selection configures OEM access only.
There is no implemented native action for adding a missing SP reference to
this retained Test.

The restriction follows the accepted [native Setup](../../contracts/distribution-installation/native-setup.md)
and [Cloud first-use](../../contracts/distribution-installation/cloud-first-use.md)
contracts. Removing that guard, editing installed code, copying a private key
into a default path or manually editing configuration is not an approved
operator recovery. Advice to return to first-use Setup after controller
creation was incorrect for this state.

## Required correction

Define a bounded, explicit way to add missing SP access to a stable retained
Test without retiring it. Preserve the selected package, OEM identity, Cloud
domain, Unit, VDP, run journal, release ledger and backend history. Inspect
and explicitly save a private file reference through the existing writer;
verify the SP role and association with the existing OEM through authenticated
reads. Do not infer authority from a filename, replace an existing SP binding,
copy keys, publish a release or replay an uncertain operation implicitly.
This requires an accepted contract amendment before implementation.

Improve the native failure text to name the retained-run restriction and the
available recovery, rather than presenting it as an unspecified Cloud failure.
The initial operator flow must make the OEM/SP pair requirement clear before
the user starts the full service-delivery journey.

Acceptance must include adding a missing SP to a provisioned Test, repeated
selection, restart, wrong-domain/role/association rejection, changed-file and
pending-operation rejection, secret redaction and unchanged non-target state.

## Operator continuation before the correction

Closing the Cloud-access dialog preserves the existing Test, but retrying
Brake or Tire preparation cannot resolve the missing SP reference. VDP-only
work may continue with the existing OEM access.

The currently implemented route to the complete service demo is a fresh run:
explicitly finish the existing Test through its normal owner, then select and
save the OEM/SP pair in Setup before creating the replacement controller.
Finish is destructive and requires an explicit decision; this report does
not authorize or perform it. A new run also requires its ordinary VDP
publication/provisioning sequence. No current Test, credential or Cloud object
was changed to record this defect.

## Authorized correction and live proof

The integrated Setup scenario and amended Cloud first-use contract authorize
one authenticated Connect operation and a bounded same-OEM missing-SP repair.
The original first-use selector remains restricted. The repair adds file
references and authenticated owner IDs through the existing configuration
writer; it never writes the vehicle journal or calls fresh-instance preparation.

On 11 October, the reviewed source was executed transiently with the selected
Kit028 package and its existing SDK on the same M1 Test. The same preserved OEM
certificate and associated SP certificate were used in staging. Both roles,
their association, VDP delivery and Brake/Tire delivery permissions, model,
node type and Test verification set returned READY. The resulting bounded
reply was `CLOUD_CONNECTED_OBSERVED`, `cloudStage=READY`,
`runtimeChanged=false`, `journalPreserved=true`.

The complete journal was compared byte-for-byte before and after the operation.
The existing Test Unit, VDP V1 release `140.0.0`, publication records and service
history were therefore preserved. No Unit, release, prerequisite object or
container was created, deleted, published or restarted by this proof. Temporary
qualification sources were removed by the owned scratch context. No key or
token bytes were copied, printed or retained in evidence.

Automated negative and repeat tests cover domain/owner/association rejection,
changed files, pending or uncertain operations and unchanged journal data. A
known upload response with matching HTTP 201, deployment ID and ACCEPTED/READY
publication is stable configuration evidence, not a retirement receipt or proof
of delivery. The repair does not rewrite that response to CONFIRMED.

This is a source-worker live proof, not an installed native-UI acceptance. The
new signed candidate still needs the fresh and returning M1 user journeys.
