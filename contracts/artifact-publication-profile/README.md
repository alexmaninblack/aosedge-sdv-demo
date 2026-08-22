<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Artifact Publication Credential Profile

- Decision: [`D4-010.3`](../../docs/requirements/d4-decision-register.md#d4-010)
- Contract version: 1.0.0
- Accepted contract SHA-256: `52bafd7b1249ec8bc10265e913265cdc7c2975f5f56db7ff3cd5cdbad4001c39`
- Lifecycle state: accepted current-demo contract; implementation and live
  qualification remain open

This contract freezes the three role-bound artifact-publication profiles used
by the first demo, their candidate-family boundaries, current `aos-signer`
compatibility limitation, native-helper isolation and publication state
machine.

- [JSON Schema](artifact-publication-profile.schema.json)
- [Accepted contract 1.0.0](artifact-publication-profile.v1.json)

The contract deliberately distinguishes technical signing/publication from
the later OEM-authorized Validation deployment or Demonstration promotion.
It also records the current-release limitation honestly: installed
`aos-signer` 2.0.1 uses one passwordless PKCS#12 file per profile for both
bundle signing and mTLS upload and does not use macOS Keychain or PKCS#11 as a
private-key operation provider.

The three credential files are local demo prerequisites, not project
artifacts. They remain outside Git and every dashboard/container, are selected
only from fixed helper configuration and are never accepted as a caller path.
Keychain/PKCS#11-backed non-exportable artifact signing remains a later
hardening migration behind the same helper contract.
