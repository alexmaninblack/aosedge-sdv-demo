<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native service runtime inputs

Status: accepted input contract under
[ADR 0015](../../docs/architecture/decisions/0015-use-native-aos-service-runtime-inputs.md);
implementation and live qualification are separate.

- [Public metadata schema](public-metadata.schema.json): schemaVersion 2;
  Unit/role and committed VDP compatibility only.
- [Package release schema](service-release.schema.json): schemaVersion 1;
  the exact Demo Control release also used in publication metadata.
- [Credential placement profile](credential-placement.v1.json): private
  sessions using the unchanged native resource mount mechanism.
- [Placement and sequence](../../docs/architecture/demo-control-service-inputs.md).
- [Ordered migration](../../docs/planning/active/demo-studio-delivery-plan.md#native-service-input-migration).

The old seven-field schemaVersion 1 runtime input is not a fallback for new
readers. This does not remove the decoder for historical product messages.
Native instance identifiers come from Aos; package and public metadata cannot
override them. Release values are application-reported, never attestation.
