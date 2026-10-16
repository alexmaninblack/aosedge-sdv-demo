<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Local hosting and controller routes

- Decision: `D4-020`; accepted hosting/containment obligations retained
- Contract version: 1.0.0; prose consolidation, no executable-profile change
- Implementation and evidence: [protocol map](../implementation-status.md)

## Installed topology

The Mac runs **two separate Linux/arm64 backend containers**, one for Brake and
one for Tire, with independent durable data. Demo Control/Presenter and native
CARLA/Driving Control run on the host, not a third dashboard container. The
ARM64 controller VM runs AosCore, KUKSA, VDP and service instances; Docker's
backend containers are not those in-vehicle services.

Setup imports the exact reviewed backend image archive into an available local
Engine. Runtime start reuses immutable identities: no build, pull, `latest`
selection, repackaging, automatic image activation or Engine lifecycle change.
Normal Stop closes owned containers and preserves data; confirmed Finish alone
cleans exact run-scoped records. Shared Docker and other projects are untouched.
See [backend ownership](../../docs/architecture/demo-control-backends.md).

Browser surfaces use loopback. The controller reaches each backend through the
accepted QEMU guest-visible host route (`10.0.0.1`); per-VM control sockets and
ports retain exact ownership. Product correlation uses native `system_uid`,
not source IP. An absent/invalid current-Test context is unavailable, not an
empty healthy product view. HTTP ACK proves durable ingestion, not analytics,
Cloud installation or vehicle advisory.

## Network and authority separation

Vehicle-data/control and external Cloud/backend connectivity use independent
VM network planes. One accepted external-offline action removes the selected
Unit's Cloud and both backend routes together while preserving in-vehicle and
presenter administrative access. Native Driving Control requests that owner
operation; it does not implement network policy itself.

Functional ingestion is an isolated local demonstration route, not a
production-authenticated backend. A reported `system_uid` supports correlation
and exact cleanup, not cryptographic client identity. Each Function Team owns
production backend authentication outside this scope. Separate endpoints,
schemas, containers and stores preserve product separation without claiming
per-Unit backend certificate issuance or rotation.

Cloud signing/administration remains in the protected host-side operation
boundary. Browsers and backend containers receive no private key, credential
path, arbitrary endpoint/command or lifecycle authority. Actual mutation is
journaled and independently reconciled in Aos Cloud; unknown outcomes are not
retried. See [publication](../artifact-publication-profile/README.md).

## Expanded design profile

The retained [machine profile](local-demo-hosting-profile.v1.json) and
[preflight fixture](fixtures/hosting-preflight.valid.json) describe the earlier
expanded three-container/dashboard-helper and dual-VM design. They are **not**
a complete generated deployment specification for the installed Studio.
Keep their frozen bytes and accepted security/qualification obligations; do not
invent a third container to satisfy an obsolete process-placement example.

Expanded Validation/Production VMs have independent QEMU user-network namespaces
and can use the same guest address. Exactly one owns the CARLA source at a
time; backend correlation remains by Unit identity. Dual-role routing, helper
capability isolation and LAN negatives require their own proof and are not
inferred from an installed single-Test run.

## Security and verification

Preserve loopback-only publication, separate Brake/Tire storage, digest pinning,
health checks and controlled owner shutdown. No privileged container, host
network, Docker socket, broad filesystem/PKCS#12 mount or credential embedded in
an image/frontend. Use non-root execution where supported by the selected
image. This is not a claim of production container RBAC, backend TLS, a secret
manager, hardware security or safety certification.

Host/tool compatibility comes from current manifests, not old observed Docker,
Compose or macOS versions. `QUALIFIED`, `COMPATIBLE_UNQUALIFIED` and
`INCOMPATIBLE` retain their evidence meanings; a new host combination is not
qualified by version similarity. Verify ordinary and partial startup,
stop/restart/persistence, owner loss, exact cleanup and released listeners.
Current candidate proof/exclusions belong to the integration baseline.
This contract authorizes no live start, signing, Cloud call or deletion.
