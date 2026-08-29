<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KAC Factory Integration Work Packet

- ID: `WP-P1-PLATFORM-KAC-FACTORY-INTEGRATION-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-KAC-FACTORY-INTEGRATION`
- Review state: `BLOCKED — EXACT PLATFORM INPUTS REQUIRED`
- Version: 0.1
- Prepared: 2026-08-29
- Implementation authorized: no
- Network/dependency acquisition, image build, VM, provisioning, signing,
  FOTA and live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Related source packet: [KAC implementation](p1-platform-kac.md)
- Related evidence packet: [KAC dependency acquisition](p1-platform-kac-dependency-acquisition.md)

## Outcome

Integrate the independently packaged removable KAC and the fixed OEM Provider
credential preparation into the successor Factory Image without inventing an
Aos resource schema, signer CLI, filesystem authority or package dependency.
This packet owns only final product-layer integration after its prerequisites
are frozen; it owns no KAC business logic and no Safe Stop runtime behavior.

## Exact Blocking Inputs

Implementation remains blocked until all of the following are available and
reviewed together:

1. the pinned AosCore release and exact product-owned source path/schema that
   generates effective `/etc/aos/resources.cfg`;
2. the exact `kuksa-auth-client` named-resource representation for shared
   count four, the one supplementary group, read-only KAC socket directory and
   container-private 64-KiB token tmpfs;
3. the accepted KAC package/recipe name and combined image dependency produced
   by `WP-P1-PLATFORM-KAC-001`;
4. the KAC-owned fixed-Provider PKCS#11 signer executable contract: installed
   path, command/IPC schema, fixed inputs, PKCS#11 Provider and token binding,
   systemd identity/credentials, atomic output contract and redacted failures;
5. the protected persistent credential-source path, owner/group/mode and
   `LoadCredential=kuksa-token` consumer wiring for exactly one seven-day
   Provider JWT containing only the accepted VDP v1-v3 Provider path union;
6. pinned AosCore/Yocto/OpenSSL/PKCS#11 build inputs and deterministic tests for
   the combined integration.

No placeholder schema, guessed executable, shell-expanded secret, file-key
fallback, static shared verifier or hand-written token is acceptable evidence.

## Future Writable Boundary

After separate authorization, the bounded packet may change only:

- the product-owned Aos resource configuration overlay and its validator;
- product-owned systemd/credential/SELinux integration for KAC and fixed
  Provider verifier preparation;
- successor-image package composition;
- package-owned Factory integration tests and validators; and
- factual integration documentation.

It may not patch upstream AosCore or KUKSA, change KAC request/JWT semantics,
change VDP payload behavior or broaden Service permissions.

## Required Verification Before Completion

- the effective named-resource configuration is generated and schema-valid;
- KAC remains separately removable and Services receive only the accepted
  private socket/token resources;
- fixed Provider preparation uses the protected per-Unit key without exporting
  key bytes, renews nothing and emits exactly one seven-day JWT;
- Factory image scans prove absence of Unit identity, key, token, Service
  permission, `AOS_SECRET` and shared static verifier;
- missing signer/resource/verifier state fails closed without blocking
  unrelated AosCore work;
- combined source, package and pinned C++/Yocto tests pass; and
- later disposable-VM and live FOTA qualification are reported separately.

## Exit Rule

This packet may move to `READY_FOR_REVIEW` only after the six blocking inputs
are frozen with exact revisions and interfaces. Until then, no source change,
dependency retrieval, build, signing or live operation is authorized.
