<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Active VDP capability evidence — accepted semantic amendment

Accepted: 18 September 2026, decision 2A, subsequently corrected by the
operator-approved Cloud-first approach on the same date. A mandatory new guest
evidence file/timer is superseded; compatibility outcomes remain required.
Implementation and any necessary executable schema revision follow the
[work packet](../../docs/planning/active/work-packets/versioned-service-observability.md).

## P2 boundary clarification — option A accepted, 18 September 2026

After executable proof that legacy metadata and the preloaded KUKSA catalog
cannot identify the active profile, the operator selected A:

- Exact installed VDP profile/release and version-matrix compatibility are
  Presenter observations from native Aos Cloud plus exact package binding.
- Services use actual local input/capability observations, retain state, and
  recover automatically without Cloud or Presenter access. A missing value
  is not evidence of a proved incompatible profile.
- No new local active-profile file, schema, timer or transport is introduced.
  The previous requirement that a service distinguish an unsuitable profile
  from a suitable but silent publisher using its own evidence is superseded.
- Preserve the strict five-field public metadata and family-document identity.
  Missing initial inputs must be handled by the authorized service recovery
  work, not by fabricated metadata, widened trust or a Cloud dependency.

See the [proof and decision](../../docs/qualification/service-renewal-and-local-capability-2026-09-18.md).
This clarification selects the mechanism; it does not claim early-install,
FOTA or reconnect implementation/qualification is complete.

## Distinct identities

The VDP family document remains version 1.0.1 with its existing digest. Its
component profiles are VDP_V1, VDP_V2 and VDP_V3, while the component release
is a separately allocated X.Y.Z value. Never derive a profile from its release
major or compare the family-document version with a minimum profile version.

For Presenter, bind the Cloud-confirmed installed artifact to its verified
functional profile and declared capabilities in the package description.
Preserve exact Cloud/Unit/artifact scope and the meaning of the compatibility
document and manifest digest. Unknown bindings remain unknown, not an inferred
newer compatible profile. Available Cloud metadata fields must be verified
against our real packages and allowlisted before use; their existence is not
proof that our profile is present there.

## Truth and refresh boundary

Native Aos Cloud is the Presenter authority for installed/pending software,
service-instance runtime state, update errors and resources. A local slot or
process probe is not a prerequisite for displaying Cloud-confirmed installation.
Prepared, signed, uploaded or pending packages are not installed evidence.
Cloud installation is not a claim of continuously healthy component processing.

Absence, transition, invalid evidence and unavailable provider must be
representable without a fabricated active profile. Services wait truthfully,
keep their process alive where possible, and reevaluate after recovery instead
of requiring another Deploy. Compatible identity alone does not prove fresh
telemetry, authorization, model output or advisory application.

Service-local compatibility/input checks must recover automatically after
successful activation, including with no Presenter or external connection.
Prove the existing native-input/KUKSA path before proposing another transport.
KUKSA catalog presence alone cannot establish the active publisher or valid
samples. Neither a Cloud read nor a stale legacy metadata file is a substitute
for this functional proof. The accepted local integration uses these existing
inputs, not an additional active-profile projection. Recovery implementation
and qualification remain required.

Do not add the rejected guest timer or fifteen-second evidence expiry, make
analytics depend on Cloud access, or wait synchronously for component commit
inside a provider startup step that the commit itself is waiting on.

Keep source directories stable, root-owned and read-only to containers; replace
individual files atomically. The service may read only its existing native
resource. Neither service gains write access to platform evidence or peer data.

## Consumer-first migration

The current five-field metadata.json and public-metadata.schema.json remain
strict schemaVersion 2. Do not add fields to that file while old V1/V2/V3
packages remain valid recipients. No new guest projection is prescribed by
this correction. If proof establishes a necessary input change, define and
approve its versioned contract and negative fixtures before producer changes.
Old readers keep their input; the legacy pair is not functional-profile proof.

Current identity and persisted historical provenance are separate decoding
paths. Close an interrupted capture under its original provenance. Preserve
queued records and model/epoch/sequence state across updates; do not inject
new fields into old messages or rebind a saved advisory to the new release.

## Compatibility outcomes

| Consumer | Accepted active profiles |
| --- | --- |
| Brake functional V1 | VDP_V1, VDP_V2, VDP_V3 |
| Brake functional V2 | VDP_V2, VDP_V3 |
| Brake functional V3 | VDP_V3 |
| Tire functional V1 | VDP_V3 |

Presenter compares Cloud-confirmed installed profiles against this matrix,
separately from backend-reported waiting for input or a qualifying episode.
Do not require the service backend to invent an actual local profile from
missing data. Unknown/stale Cloud evidence remains unknown/last known, not
current compatibility. Cloud installation still follows native Aos behavior:
this is not new pre-transfer admission. Presenter does not probe the VM.

Safe Stop, KAC leases, native permissions and existing telemetry freshness
budgets are unchanged. This correction introduces no new evidence expiry.
