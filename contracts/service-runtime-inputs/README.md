<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native service runtime inputs

Current implementation status (24 September 2026, demo-v1.1 / Factory .39):
see the [complete protocol map](../implementation-status.md) for this family's
implemented path, accepted amendments and remaining qualification or executable-
profile differences. Design lifecycle labels below are not deployment verdicts.
Historical golden schemas/digests are not rewritten as part of this audit.

Status: accepted input contract under
[ADR 0015](../../docs/architecture/decisions/0015-use-native-aos-service-runtime-inputs.md);
implementation and live qualification are separate.

18 September accepted amendment: [active VDP capability evidence](active-vdp-capability-amendment.md)
defines profile/release/capability observation, corrected to use native Cloud
for Presenter inventory and verified artifact/profile binding. The strict v2
schema below remains unchanged. No guest timer or mandatory new input revision
is prescribed; service-local compatibility/recovery still requires proof.

- [Public metadata schema](public-metadata.schema.json): schemaVersion 2;
  Unit/role and committed VDP compatibility only.
- [Package release schema](service-release.schema.json): schemaVersion 1;
  the exact Demo Control release also used in publication metadata.
- [Product-message migration](product-message-migration.md): explicit v2
  provenance, strict legacy decoding and consumer-first rollout.
- [Credential placement profile](credential-placement.v1.json): private
  sessions using the unchanged native resource mount mechanism.
- [Placement and sequence](../../docs/architecture/demo-control-service-inputs.md).
- [Ordered migration](../../docs/planning/active/demo-studio-delivery-plan.md#native-service-input-migration).

The old seven-field schemaVersion 1 runtime input is not a fallback for new
readers. This does not remove the decoder for historical product messages.
Native instance identifiers come from Aos; package and public metadata cannot
override them. Release values are application-reported, never attestation.
