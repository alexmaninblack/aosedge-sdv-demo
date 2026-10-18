<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Artifact Publication Credential Profile

Implementation and qualification: [protocol status](../implementation-status.md).

- Decision: [`D4-010.3`](../../docs/requirements/d4-decision-register.md#d4-010)
- Contract version: 1.0.0
- Accepted contract SHA-256: `52bafd7b1249ec8bc10265e913265cdc7c2975f5f56db7ff3cd5cdbad4001c39`
- Lifecycle state: accepted current-demo contract; protected publication is
  implemented with scoped live evidence in the [current baseline](../../docs/qualification/current-baseline.md);
  expanded cross-provider and full negative matrices remain separate gates

This contract freezes the three role-bound artifact-publication profiles used
by the first demo, their candidate-family boundaries, current `aos-signer`
compatibility limitation, native-helper isolation and publication state
machine.

- [JSON Schema](artifact-publication-profile.schema.json)
- [Accepted contract 1.0.0](artifact-publication-profile.v1.json)

The contract deliberately distinguishes technical signing/publication from
the later OEM-authorized Validation deployment or Production promotion.
It also records the current-release limitation honestly: installed
`aos-signer` 2.0.1 uses one passwordless PKCS#12 file per profile for both
bundle signing and mTLS upload and does not use macOS Keychain or PKCS#11 as a
private-key operation provider.

These are three logical profiles, not a requirement for three distinct
credential files. Installed use binds one OEM credential and one associated-SP
credential; `brake-sp1` and `tire-sp2` may reference the same SP PKCS#12 without
copying it. Expanded cross-provider qualification binds separate SP identities.
The credentials are private local prerequisites, not project artifacts or
bundled inputs. They remain outside Git and every dashboard/container, are selected
only from fixed helper configuration and are never accepted as a caller path.
Keychain/PKCS#11-backed non-exportable artifact signing remains a later
hardening migration behind the same helper contract.

Installed Prepare verifies prebuilt functional inputs and allocates a fresh
release number through the reviewed adapter. It may assemble version-bound
metadata/package, but never compile, train or accept arbitrary changed content.
The prepared digest becomes immutable before signing. Expanded frozen-catalogue
use prepares all such packages before presentation. A lost upload response with
no exact response ID stays uncertain: collection search cannot adopt a guessed
object or authorize resubmission. See the
[publication owner](../../docs/architecture/demo-control-component-publication.md).

The frozen JSON preserves original profile bindings and conformance fixtures;
these effective preparation/observation rules change no frozen schema, hash,
runtime handler or signing authority.
