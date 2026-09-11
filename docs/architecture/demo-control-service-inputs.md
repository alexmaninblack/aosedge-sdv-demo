<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service runtime inputs

- Status: Accepted contract; implementation and live qualification tracked separately
- Version: 2.0
- Prepared: 2026-09-11
- Owner: Demo Control / OEM Platform
- Decision: [ADR 0015](decisions/0015-use-native-aos-service-runtime-inputs.md)

This is the replacement for the former seven-field input and SM token-owner
patch design. Historical observations remain in the dated qualification
checkpoints, not as competing instructions here.

## Package, public inputs and native identity

| Source | Fields / location | Lifecycle |
| --- | --- | --- |
| Immutable package | `/usr/share/aosedge/service-release.json`: schemaVersion 1, serviceVersion | Demo Control allocates one release and writes it to this file and publication metadata; root-owned read-only package data |
| Public Unit input | `/run/aosedge/platform/service-inputs/metadata.json`: schemaVersion 2, unitSystemUid, unitRole, vdpContractVersion, vdpContractSha256 | Prepared before service launch; refresh only on committed VDP change |
| Public KUKSA trust | `/run/aosedge/platform/service-inputs/kuksa-ca.pem` | Copy only the Unit public certificate, never a private key |
| Native instance identity | AOS_ITEM_ID, AOS_SUBJECT_ID, AOS_INSTANCE_INDEX, AOS_INSTANCE_ID | Supplied by native Aos; not substituted by caller labels or release metadata |
| Token path | KUKSA_TOKEN_FILE | Bootstrap-selected private session path; never a token value |

Both services use strict `X.Y.Z` release values, at most 32 characters,
without leading zeroes. Functional profiles remain separate from releases.
The package version is application-reported, not platform attestation.

Unit UID is native IAM `GetSystemInfo.system_id`, reconciled with successful
provisioning, not the Cloud Unit UUID. Test maps to wire role `validation`.
The VDP pair comes from `contracts.vdpCompatibility` in the verified,
committed active capability manifest; it is neither a functional profile,
Cloud release nor the whole capability-manifest digest.

The executable input schemas are in
[service runtime inputs](../../contracts/service-runtime-inputs/README.md).

## Filesystem resources

| Service | Resource | Host directory |
| --- | --- | --- |
| Brake | brake-runtime-inputs | /run/aos-demo-service-inputs/brake |
| Tire | tire-runtime-inputs | /run/aos-demo-service-inputs/tire |

Each resource binds only its own directory to
`/run/aosedge/platform/service-inputs` using
`bind,ro,nosuid,nodev,noexec`. Root owns directories (0755) and the two public
files (0444). Do not bind a shared parent or both resources into one instance.
Demo Control replaces individual files atomically inside the stable directory.

Public trust originates only at `/var/lib/aos-kuksa-tls/server.pem`.
The service validates TLS for `Server`; no TOFU, handshake-extracted trust,
private-key sibling, Provider token or private trust directory is exposed.

## Private token session

The existing `kuksa-auth-client` resource keeps its socket bind and
`aos-kuksa-clients` group. Its separate per-container 64-KiB tmpfs retains
`rw,nosuid,nodev,noexec`, with root mode **1777**, not an SM-generated UID/GID.
The bootstrap creates an unpredictable `session-<random>` directory (0700)
under `/run/aosedge/secrets/kuksa`, owned by its effective UID/GID.
Its token is a regular file `token.jwt` (0400); the child receives its exact
path through `KUKSA_TOKEN_FILE`.

Reject symlink traversal, wrong ownership/mode and pre-existing session
adoption. Bound crash-orphan accumulation; never delete an active peer
session. Normal shutdown removes only the bootstrap's own session. Restart
acquires new credentials; it does not recover a token from storage. No new
daemon, wrapper, fixed service UID, privileged chown or SM code is introduced.

KAC request/response, IAM authority, 300-second TTL, renewal at 180 seconds,
expiry, denial, retry and redaction remain unchanged. Remove AOS_SECRET
before starting analytics. Persistent model/outbox data stay in native
`/storage`; credentials never enter `/storage` or `/state.dat`.

## Activation and recovery order

1. Package preparation and publication may occur before a vehicle exists.
   They do not require runtime inputs or a final OCI manifest lookup.
2. Before launch, project native Unit/role, committed VDP and public trust.
   Reject missing/contradictory inputs instead of supplying placeholders.
3. Activate the native resource configuration through Demo Control. The
   pinned resource manager loads at initialization, not via hot reload.
   Preserve existing SM binary, settings, credentials and resources.
4. Assign service IDs through the existing Subject operation. Native Aos
   determines the actual instance and version.
5. Bootstrap authenticates through KAC, establishes TLS/subscriptions and
   starts analytics. Cloud Running is not functional Ready.
6. Refresh public files only after committed slot/process agreement.
   Old windows/outbox records retain their original provenance and bytes.
7. Cold start must restore the /run sources before automatic retained
   assignments launch. The exact existing platform/startup hook is a required
   implementation gate; a warm assignment does not prove this ordering.

No direct guest reads are added to the Presenter platform dashboard; Cloud
remains its platform-state source. Engineering input projection/inspection is
a Demo Control operation, separate from dashboard observation.

## Migration and remaining evidence

[The delivery plan](../planning/active/demo-studio-delivery-plan.md#native-service-input-migration)
owns the ordered work and its actual status. Product-message migration must
cover the service digest **and** Brake's modelArtifactSha256 alias of it.
Retain modelConfigSha256 and the VDP compatibility digest. Do not invent a
replacement artifact hash. New messages use an explicit new schema version;
legacy queues and backend records remain readable and are never relabelled.

Native environment/resource behavior was inspected at AosCore
`9eecb80c4994937b5c8cbe0464970f81e8ad4c2d`; evidence links and limitations
remain in [ADR 0015](decisions/0015-use-native-aos-service-runtime-inputs.md#9-evidence-and-limitations).
Native mount/SELinux, real KAC/TLS/renewal, backend ingestion and retained-
assignment cold start still require the focused live proof. Current Factory
image and Production are not modified by this document.
