<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P0 Platform Readiness Work Packet

- ID: `WP-P0-PLATFORM-001`
- Lane: `L-PLATFORM`
- Parent increment: `IMP-03`
- Review state: `COMPLETED — BASELINE_ACCEPTED`; P1 source packets accepted separately
- Version: 0.12
- Prepared: 2026-08-27
- Updated: 2026-08-28
- Accepted: 2026-08-28
- Execution authorized: yes — P0 read-only assessment and local tests only
- Authorized: 2026-08-28
- Product implementation, Yocto/image/component build, signing, Cloud, VM or
  Unit mutation authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Objective

Freeze the truthful Platform baseline and produce the exact future code-packet
decomposition for Factory Assembly, OEM Component Runtime, removable KUKSA
authorization compatibility helper and VDP v1-v3. P0 must not implement the
target or silently treat newer local documentation as an accepted product
revision.

## P0 Execution Result

- Completed: 2026-08-28
- Exit state: `BASELINE_ACCEPTED`
- `IMP-03` state at P0 exit: `BLOCKED`; three bounded P1 source packets were
  subsequently accepted on 2026-08-28

P0 first selected `5c2a7d0704fac93ba0a285cf533c17847d88633e` as the
source-evidence candidate because its delta from the previous accepted
revision was documentation-only. The accepted reconciliation then aligned the
Platform documentation to the current KAC, trusted Provider and Factory
boundaries and produced final baseline
`bdc72aba97a83c9868d454588189ef139710a6d7`. Platform `main` and `origin/main`
are equal at that revision, and the solution repository pin/evidence cascade
records it. The historical `.11` image and Provider `0.2.0` artifact pins
remain immutable and were not repinned to this documentation revision.

All P0-frozen requirement/contract digests and preserved `.11` artifact digests
matched during the read-only assessment. After package acceptance, the four
requirement files were deliberately repinned below. At the final Platform
baseline, 35 Python tests and the quality gate for 82 tracked files passed. No
product source, recipe, image, component, key, JWT, Cloud, VM or Unit operation
was performed.

Reusable current implementation evidence includes the provider-specific A/B
runtime, bounded 512 MiB ext4 runtime working storage, fixed `aos-vdp` identity, systemd/SELinux
boundaries and the seven-path inbound Provider. The following target behavior
is absent and must not be presented as implemented:

- factory configuration with `enablePermissionsHandler: true`;
- the removable `authorization/aos-kuksa-compat/` package and all KAC signer,
  verifier, permission-mapping and JWT-lifecycle behavior;
- OEM Component Runtime `WaitingForSafeStop` application gating;
- VDP v2/v3 capability increments, typed outbound advisory path and complete
  readiness/resource recovery; and
- exact selected-Unit mTLS and the smallest boot/provisioning-time
  materialization of the trusted OEM Provider's KUKSA credential.

The future Platform work remains decomposed into three independently reviewed
code packets: KAC, successor Factory/runtime and VDP v1-v3. `CR-FACTORY` 0.5,
`CR-KAC` 0.12, `CR-VDP` 0.9 and `CR-CROSS` 0.4 were accepted on 2026-08-28.
IAM ownership plus KAC package/process, signer/verifier, Service-bootstrap,
native-IAM loopback, minimum trustworthy-time, exact
filesystem/SELinux/PKCS#11 parameters and the OEM Component Runtime Safe Stop
adapter are now accepted. The absence of a second dynamic Provider-
authorization system is also accepted in `IMP-03-VDP-001`, and the exact
selected-Unit VISS mTLS enrollment and atomic handover boundary is accepted in
`IMP-03-VDP-002`. The minimum fixed Provider credential materialization is
accepted in `IMP-03-VDP-003`, and the immutable prebuilt VDP v1-v3 artifact
family is accepted in `IMP-03-VDP-004`. The subsequent Factory/runtime, KAC
and VDP P1 packets authorize only isolated source implementation. Their
interdependent merge plus every dependency download, artifact/image build and
live qualification remains separately gated.

## Accepted Implementation Parameters

### `IMP-03-IAM-001` — Product-owned Permission Handler enablement

- Decision state: `ACCEPTED` on 2026-08-28.
- Owner: OEM Factory Image assembly in `aos-vehicle-platform`.
- Upstream boundary: do not fork or patch AosCore source and do not introduce a
  second runtime configuration authority.
- Yocto mechanism: a tracked product-layer `aos-iamanager` bbappend shall apply
  one deterministic build-time transformation to the final product-specific
  `/etc/aos/iam.cfg`, after the upstream/AosVM configuration has been composed,
  setting only `enablePermissionsHandler` to Boolean `true`.
- Scope: the transformation applies to every applicable Node image and remains
  independent of provisioning state. It must preserve all other main/secondary
  product configuration differences.
- Negative boundary: the Factory Image still contains no Unit identity, Cloud
  credential, registered Service permission, `AOS_SECRET`, JWT, signing key or
  shared verifier.
- Required implementation evidence: build-time validation fails if the final
  value is absent, non-Boolean or false; package/image tests prove the value is
  true before provisioning and unchanged after reboot/provisioning; IAM starts
  with its native Permission Handler while the secret-negative Factory scans
  remain clean.

This decision closes only the IAM configuration-ownership parameter. It does
not authorize product code or an image build and does not close the remaining
KAC packaging/startup, signer/verifier, trusted Provider connection, Safe Stop
adapter or VDP artifact parameters.

### `IMP-03-KAC-001` — Separate helper package and process boundary

- Decision state: `ACCEPTED` on 2026-08-28.
- Source boundary: one C++ component under
  `authorization/aos-kuksa-compat/`, with its own CMake target and package-owned
  unit/contract/security tests.
- Yocto boundary: one independently removable
  `aos-kuksa-auth-compat` recipe/package and
  `aos-kuksa-auth-compat.service`; the package is installed in the successor
  Factory Image and is not part of VDP FOTA or either functional SOTA artifact.
- Runtime identity: dedicated unprivileged `aos-kac:aos-kac`, no root fallback,
  inbound TCP listener, ambient capability or VDP dependency. The sole
  `AF_INET` exception is the separately accepted fixed native-IAM loopback
  client in `IMP-03-KAC-004`.
- Startup boundary: the unit uses the native
  `ConditionPathExists=/var/aos/.provisionstate` gate, requires active
  `aos-iam.service` and successful `aos-kuksa-verifier-prepare.service`, and
  becomes ready through `Type=notify` only after its private Unix socket and
  trustworthy-time prerequisites are valid. KAC and unmodified KUKSA depend
  independently on verifier preparation; neither KAC nor KUKSA is ordered
  through VDP.
- IAM integration: call the pinned native v6
  `IAMPublicPermissionsService/GetPermissions` gRPC interface directly. Do not
  use the current AosCore `PublicPermissionsService` logging wrapper because
  it logs the presented Service secret at debug level; do not fork AosCore or
  create a parallel permission store or policy API.
- Readiness boundary: a KUKSA-consuming Service may remain functionally
  `NOT_READY` while KAC is unavailable, but KAC failure must not block Service
  Manager or unrelated Services.

This decision closes the helper source/package/process and native IAM-call
placement. It does not yet close protected signer/verifier preparation, local
socket/resource/bootstrap ownership, trustworthy-time implementation,
SELinux/PKCS#11 grants or exact build/image qualification parameters.

### `IMP-03-KAC-002` — Per-Unit protected signer and verifier preparation

- Decision state: `ACCEPTED` on 2026-08-28.
- Factory configuration: add one non-secret `kuksa-jwt` certificate module to
  the final product IAM configuration with `pkcs11module`, RSA,
  `maxItems: 1` and `selfSigned: true`. Use dedicated SoftHSM token label
  `aos-kuksa` and dedicated PIN path `/var/aos/iam/.kuksa-jwt-pin`; do not use
  the shared `aoscore` token or `/var/aos/iam/.usrpin`.
- Provisioning lifecycle: native AosCore `ProvisionManager` owns key creation.
  Each successful fresh Unit provisioning creates a new RSA key pair and
  self-signed certificate in the dedicated PKCS#11 token. The Factory Image
  contains only module/preparation wiring and no key or shared verifier.
- Preparation gate: `aos-kuksa-verifier-prepare.service` runs after provisioned
  `aos-iam.service`, locates the exact `kuksa-jwt` object, performs a protected
  sign/verify self-test and atomically publishes only the public key as
  root-owned mode-`0444`
  `/run/aos-kuksa-verifier/kuksa-jwt-public.pem`. Missing, ambiguous,
  malformed or unverifiable state publishes no verifier and blocks KUKSA and
  KAC without blocking unrelated AosCore services.
- Signing path: the unprivileged KAC process uses the pinned OpenSSL 3 PKCS#11
  provider and exact token/object selection for `RS256`; no file-key fallback
  or AosCore source patch is permitted. The dedicated PIN is delivered only as
  a systemd service credential rather than exposed through the Service API or
  broad file permissions.
- Restart and retirement: reboot reconstructs the volatile public verifier
  from the existing Unit key before KUKSA/KAC startup. A new key is created
  only by a fresh provisioning lifecycle; R0 retires it by discarding the
  reconciled provisioned VM overlay.
- Qualification boundary: the demo SoftHSM proves PKCS#11 API
  non-exportability, key/identity separation, verifier binding and negative
  access behavior. It does not claim the physical tamper resistance of a
  production automotive HSM.

This decision closes signer ownership, token/PIN separation, native
provisioning creation, public-verifier preparation and reboot/R0 behavior. It
does not yet close the exact Service bootstrap/named-resource wiring,
trustworthy-time implementation, residual filesystem/SELinux grants or final
image qualification commands.

### `IMP-03-KAC-003` — Named resource, socket and Service bootstrap ownership

- Decision state: `ACCEPTED` on 2026-08-28.
- Native resource mechanism: the Factory Image shall extend the product-owned
  `/etc/aos/resources.cfg`; no AosCore source patch or parallel resource
  allocator is permitted.
- Resource definition: `kuksa-auth-client` has `sharedCount: 4`, adds only the
  `aos-kuksa-clients` supplementary group, read-only bind-mounts host
  `/run/aos-kuksa-auth-compat` at container
  `/run/aosedge/platform/kuksa-auth`, and creates a container-private 64-KiB
  tmpfs at `/run/aosedge/secrets/kuksa` with mode `0700` and
  `nosuid,nodev,noexec`. It contains no secret, token, permission, configurable
  host path or injected authority.
- Allocation boundary: each eligible Brake or Tire SOTA item explicitly
  requests `kuksa-auth-client` in its immutable item metadata. Resource
  allocation grants transport only; the active instance `AOS_SECRET` and
  native IAM `GetPermissions` result remain authoritative. Capacity four
  supports both tenants plus bounded old/new overlap and does not widen IAM
  authority.
- Host transport: the KAC package owns group `aos-kuksa-clients`, host runtime
  directory `/run/aos-kuksa-auth-compat` and Unix stream socket
  `request.sock`, owned `aos-kac:aos-kuksa-clients` and mode `0660`. The
  directory may exist before readiness; the socket is published only after
  signer/verifier/time preparation. No TCP listener exists.
- Bootstrap ownership: Brake and Tire each package a Service-local bootstrap
  in their own SOTA artifact; no additional shared deployable artifact or
  platform-owned analytics wrapper is introduced. Both implementations must
  conform to the same pinned machine-readable KAC contract and fixtures.
- Secret/child boundary: only the bootstrap reads the Service Manager-injected
  `AOS_SECRET`. It requests the implicit fixed `kuksa` resource, atomically
  maintains mode-`0400` `token.jwt` in the private tmpfs and starts the
  analytics child with only `KUKSA_TOKEN_FILE`, after removing `AOS_SECRET`
  from the child environment.
- Lifecycle boundary: the bootstrap owns renewal and mandatory KUKSA
  reconnect/subscription recreation. Terminal rejection or expiry removes the
  token and keeps analytics functionally `NOT_READY`; container stop,
  replacement, removal and VM reboot destroy the private tmpfs automatically.

This decision closes local transport placement, exact first-demo allocation
capacity, mount/group ownership and the Platform-versus-Function-Team
bootstrap boundary. It does not close residual SELinux/PKCS#11 grants or final
build/image qualification parameters.

### `IMP-03-KAC-004` — Native IAM loopback exception

- Decision state: `ACCEPTED` on 2026-08-28.
- Released interface: KAC calls only the pinned native v6
  `IAMPublicPermissionsService/GetPermissions` gRPC method at fixed
  `127.0.0.1:8090`; replacing the released TCP interface with a Unix socket is
  outside this work packet.
- Authentication: the client uses TLS, trusts the Aos CA and verifies expected
  certificate server name `main`.
- Address boundary: KAC may use `AF_UNIX` for its private Service-facing socket
  and `AF_INET` only for the fixed loopback IAM client. It exposes no TCP
  listener, performs no DNS lookup, accepts no caller-configurable endpoint and
  may not reach an external IP.
- Offline boundary: the loopback call remains inside the Unit and therefore is
  not removed by the demo's vehicle external-connectivity fault.
- Qualification: contract and package tests must reject wrong port, address,
  trust root or server name, DNS/external destinations and any KAC TCP
  listener, while proving successful native IAM lookup during targeted vehicle
  external-connectivity loss.

This decision corrects an unimplementable `AF_UNIX`-only sandbox assumption
found during pinned-source inspection. It changes no authority owner,
Service-facing contract, public interface or permanent architecture.

### `IMP-03-KAC-005` — Minimum current-release trustworthy time

- Decision state: `ACCEPTED` on 2026-08-28.
- Startup gate: once per VM boot, KAC waits for successful
  `systemd-timesyncd` synchronization and then observes a 10-second stable
  window before reporting ready or issuing a JWT.
- Clock use: JWT epoch claims use UTC `CLOCK_REALTIME`; renewal, retry and
  stable-window scheduling use `CLOCK_BOOTTIME`.
- Operation gate: immediately before every issue or renewal, KAC compares
  elapsed wall and boot clocks. More than five seconds of deviation in either
  direction returns retryable `TIME_UNTRUSTED` and issues no JWT.
- Recovery: issue/renew resumes only after synchronized time and another
  10-second stable window. Loss of external connectivity after the initial
  gate does not itself revoke time trust; cold offline boot remains
  authorization `NOT_READY` without blocking unrelated AosCore services.
- Deliberate temporary boundary: no separate time-guard service, anchor file,
  continuous monitoring loop, timerfd clock-jump detector, KUKSA stop/restart
  controller or instant token revocation is implemented. An already issued
  self-contained JWT may remain usable only until signed expiry.
- Migration gate: the future released native AosCore contract must be
  requalified for trustworthy time, bounded credential invalidation and
  recovery before KAC is removed; this packet does not invent its mechanism.

This is the minimum correctness guard needed for VM-based JWT operation. It
avoids building production-strength clock lifecycle machinery into the
deliberately removable compatibility helper.

### <a id="imp-03-kac-006"></a>`IMP-03-KAC-006` — Exact filesystem, SELinux and PKCS#11 boundary

- Decision state: `ACCEPTED` on 2026-08-28.
- PIN source: `/var/aos/iam/.kuksa-jwt-pin`, `root:root`, mode `0600`, separate
  from `/var/aos/iam/.usrpin`. KAC and verifier preparation receive the PIN
  only through private systemd `LoadCredential`; direct source-file access and
  PIN placement in a PKCS#11 URI, environment, process argument or log are
  forbidden.
- Signer: module ID `kuksa-jwt`, SoftHSM token label `aos-kuksa`, RSA-2048,
  `maxItems: 1`, `selfSigned: true`, library
  `/usr/lib/softhsm/libsofthsm2.so` and OpenSSL provider
  `/usr/lib/ossl-modules/pkcs11.so`. Exact token/object selection is required;
  no file-key fallback exists.
- Verifier filesystem: `/run/aos-kuksa-verifier` is `root:root` mode `0755`;
  the preparation unit atomically replaces only root-owned mode-`0444`
  `kuksa-jwt-public.pem`.
- Helper filesystem: `/run/aos-kuksa-auth-compat` is
  `aos-kac:aos-kuksa-clients` mode `0750`; `request.sock` has the same owner
  and group with mode `0660`. KAC writes only to that runtime directory, has no
  persistent state directory and cannot read Service-private token tmpfs.
- SELinux: the unprivileged main process uses
  `aos_kuksa_auth_compat_t`; the short root-owned networkless preparation unit
  uses `aos_kuksa_verifier_prepare_t`. KAC receives only its socket/runtime
  files, private systemd credential, CA/public-verifier reads, pinned
  PKCS#11 signing, fixed TLS loopback IAM access, initial time-sync evidence
  and fixed redacted journald output. Capabilities, shell execution, arbitrary
  `/var/aos`, DNS/external network, shared `.usrpin`, Service tmpfs,
  public-verifier modification and systemd-unit management are denied.
- SoftHSM backend: initial permission is read/open/lock only; create, delete or
  rename is not granted. If the pinned implementation proves that any broader
  access is required, work stops for a separate decision; policy is never
  automatically widened from `audit2allow` output.
- Deliberate current-demo boundary: direct KAC-to-SoftHSM signing avoids a
  second temporary signer daemon. SoftHSM is not hardware-HSM isolation and no
  production non-extractability claim is made.

This closes the KAC integration-parameter gate without expanding the helper
into a permanent security service. Source implementation remains unauthorized
until the exact P1 package is accepted.

### <a id="imp-03-runtime-001"></a>`IMP-03-RUNTIME-001` — Safe Stop runtime adapter and waiting execution

- Decision state: `ACCEPTED` on 2026-08-28.
- Trust role: VISS profile 1.1.0 adds one purpose-bound
  `PLATFORM_UPDATE_RUNTIME` peer for each selected Unit. It uses a credential
  distinct from the VDP peer, permits one connection and only
  `GET`/`SUBSCRIBE`/`UNSUBSCRIBE`, and is bound to the same Unit ID, Node ID,
  certificate fingerprint and assignment generation.
- Credential lifecycle: create it only after Unit/Node identity is known,
  store it as a protected root-owned Unit credential, deliver it through
  systemd `LoadCredential`, exclude it from Factory/FOTA/Git/logs/dashboards
  and retire it at R0.
- Exact read boundary: the role may read only the ten Safe Stop paths in
  contract 1.1.1. `Vehicle.CarlaSimulation.FrameId` is mandatory so the
  twelve-sample gate counts distinct monotonic CARLA frames rather than repeat
  reads of one cached value. Each sample is fresh when acquired; the retained
  history proves stability only, and the latest complete sample is rechecked
  for 250-ms freshness at every destructive gate.
- Runtime structure: a transport-only VISS 3.1 mTLS adapter implements
  `VehicleStateProviderItf`; a pure Safe Stop evaluator owns the accepted
  policy and is testable with a fake provider. Neither VDP, KUKSA, AosCloud nor
  the Demo UI enters the physical-state authority path.
- Waiting execution: after candidate preparation and durable transaction
  metadata, one bounded asynchronous worker reports native `Activating` while
  waiting. It does not hold the runtime mutex across the wait; runtime stop
  performs bounded cancel-and-join.
- Persistence: only transaction metadata is durable. Safe Stop samples are
  never persisted or reused after runtime/VM restart; a fresh complete frame
  sequence is mandatory.
- Availability: first install exposes no active VDP while waiting;
  replacement and removal leave the current healthy release active until Safe
  Stop is proven. No destructive stop or activation begins early, and driving
  resumes only through an explicit presenter action after readiness.

This resolves the previous mismatch between the Safe Stop contract's runtime
read role and the three-role VISS profile. It refines the implementation seam;
the already accepted Safe Stop thresholds, bounded timeout and rollback policy
do not change.

### <a id="imp-03-vdp-001"></a>`IMP-03-VDP-001` — Trusted Provider boundary without a second authorization system

- Decision state: `ACCEPTED` on 2026-08-28.
- Native trust boundary: the VDP is an OEM-qualified platform component. OEM
  approval, signed FOTA delivery through AosCore and the dedicated
  `systemd-slot-component` runtime establish which exact artifact may execute
  as `aos-vdp`; the first demo adds no separate Provider identity database,
  dynamic Provider IAM exchange, per-component attestation or malicious-
  Provider containment claim.
- AosCore boundary: the native Permission Handler remains authoritative only
  for active SOTA Service instances. It registers immutable Service metadata,
  returns each instance's `AOS_SECRET` and does not authenticate the FOTA VDP
  as a KUKSA Provider.
- KUKSA boundary: unmodified KUKSA remains authorization enforcement for its
  API actions and paths. The trusted VDP receives only the fixed Provider-side
  access required by the accepted VDP data/advisory contract. Brake and Tire
  credentials are derived through KAC and can never contain or obtain KUKSA
  `provide` or `create` authority.
- Existing implementation seam: retain the dedicated `aos-vdp` identity,
  systemd/SELinux isolation and private `LoadCredential=kuksa-token` path.
  SOTA containers may neither read nor reuse that credential. Missing,
  inconsistent or out-of-contract Provider configuration keeps VDP unready.
- Deliberate scope boundary: no 72-hour Provider-JWT profile, automatic
  Provider renewal/rotation loop, Provider call to `GetPermissions`, use of
  `AOS_SECRET`, KAC Service-facing exchange or second signer/key architecture
  is introduced by this decision.
- Qualification: prove exact signed VDP artifact/configuration identity on
  both Unit roles, successful bounded Provider operations, rejection of
  Service `provide`/`create`, credential-path isolation and fail-closed
  missing/inconsistent Provider connection.

This closes the question of whether a separate dynamic Provider-authorization
mechanism is required. It is not. The smallest boot/provisioning-time
materialization of the already required KUKSA-compatible platform credential
remains a separate implementation parameter; selected-Unit VISS mTLS is also
independent of this decision.

### <a id="imp-03-vdp-002"></a>`IMP-03-VDP-002` — Selected-Unit VISS mTLS enrollment and atomic handover

- Decision state: `ACCEPTED` on 2026-08-28.
- Boundary: this is transport identity and live-source selection between the
  Vehicle Gateway and the two provisioned Unit roles. It neither replaces nor
  extends AosCloud IAM, AosCore Permission Handler or KUKSA authorization.
- Per-Unit onboarding: after provisioning has established the current Unit ID
  and Node ID, the host-side onboarding helper creates distinct purpose-bound
  client identities for `SELECTED_PLATFORM_UNIT` and
  `PLATFORM_UPDATE_RUNTIME`. Certificate identity binds its Unit ID, Node ID
  and role; the Gateway records the exact certificate fingerprint.
- Credential placement: each fresh Unit receives only its own client material
  in the root-owned persistent VM overlay, outside Factory Image, FOTA
  artifacts and Git. The relevant systemd unit receives it through
  `LoadCredential`; R0 removal destroys the per-Unit material.
- Local trust anchor: one protected demo VISS CA is created during local setup
  and retained outside Git and the Unit VMs. It is demo transport
  infrastructure, not an AosCloud OEM or Service Provider credential. CA trust
  alone is insufficient: the Gateway also requires explicit Unit, role and
  fingerprint enrollment.
- Simultaneous Units: Test Vehicle and Production Vehicle may both be online,
  but the Gateway accepts the two selected-bound roles only from the current
  vehicle. A wrong Unit, wrong role, stale, expired, revoked, unknown or
  additional selected-bound session fails closed. The Engineering Dashboard
  retains its independent read-only connection.
- Atomic handover: a selection request supplies the expected previous
  `assignmentGeneration`. The Gateway atomically advances the generation and
  selected Unit, closes the previous Unit's VDP and update-runtime sessions,
  and permits only the newly selected Unit's enrolled role fingerprints.
- Readiness: after handover the new VDP remains `NOT_READY` until it has
  reconnected and produced the first complete, fresh, contract-valid snapshot.
  No data or Safe Stop evidence from the previous Unit or generation is reused.
- Generation boundary: `assignmentGeneration` is mutable selection state and
  is deliberately not encoded into the per-Unit certificate; otherwise every
  Test/Production switch would require certificate reissuance.
- Qualification: prove Test-to-Production and Production-to-Test handover,
  stale-generation rejection, old-session closure, wrong-Unit/role/fingerprint
  rejection, independent Dashboard continuity and R0 credential retirement.

This freezes the identity, storage and handover model required by the already
accepted VISS trust and exclusive-live-source contracts. Exact certificate
field encoding and implementation paths belong to the future smallest code
packet and may not weaken these semantics.

### <a id="imp-03-vdp-003"></a>`IMP-03-VDP-003` — Minimum fixed KUKSA Provider credential materialization

- Decision state: `ACCEPTED` on 2026-08-28.
- Purpose: satisfy the mandatory JWT enforcement of the pinned unmodified
  KUKSA Databroker for the trusted OEM VDP without introducing a second
  Provider-authorization architecture.
- Single Unit trust root: reuse the one Unit-specific protected `kuksa-jwt`
  signing key created through the accepted native Aos IAM certificate-module
  provisioning lifecycle. KUKSA receives its one public verifier. No second
  Provider key, verifier, identity database or trust chain is added.
- Separation from Service authorization: KAC may use the same Unit trust root
  for Service JWTs but its Service-facing socket can never issue a Provider
  token or map `provide`/`create`. VDP never calls KAC, `GetPermissions` or
  Aos IAM and receives no authority from `AOS_SECRET`.
- One-shot preparation: after successful fresh Unit provisioning, a
  platform-owned local preparation step signs exactly one fixed Provider JWT.
  It is not a runtime issuance endpoint and performs no automatic renewal,
  rotation or Cloud lookup.
- Exact bounded authority: the JWT contains the explicit union required by
  the accepted VDP v1-v3 graph: `provide` for the twenty-three telemetry paths
  and two Gateway Status paths, plus `read` for the two typed advisory request
  paths. Wildcards, `create`, `actuate` and every path outside the accepted
  contracts are forbidden. The complete non-secret VSS/OEM overlay is present
  in the qualified Factory KUKSA tree, so VDP never requires `create`.
- Version boundary: the fixed union credential is intentionally stable across
  VDP v1-v3 FOTA. Each signed VDP artifact remains constrained and qualified
  to its own version-specific subset; the first-demo trusted-Provider
  assumption does not claim containment of a malicious substituted VDP.
- Lifetime: issue the token for seven days from the successful preparation
  time. The supported demo run is shorter than this bound. There is no silent
  renewal; expiry makes VDP `NOT_READY` and requires an explicit fresh demo
  provisioning lifecycle rather than authorization fallback.
- Storage and restart: atomically write the token as root-owned mode `0600` in
  the persistent provisioned VM overlay at the source of the existing
  `LoadCredential=kuksa-token` boundary. Only systemd exposes the private
  runtime copy to `aos-vdp`. An ordinary VM reboot reuses the still-valid token
  after verifier reconstruction; R0 overlay retirement removes the Unit key
  and token.
- Failure and evidence: missing, malformed, expired, incorrectly signed,
  wrong-Unit or out-of-contract credential keeps VDP unready with redacted
  reason evidence. No token, private key or claim body is placed in Git,
  Factory/FOTA/SOTA payloads, command lines, logs or dashboards.

This closes the current-demo Provider credential ownership, authority,
lifetime, storage, reboot and retirement parameters. It deliberately does not
turn trusted Provider integration into a permanent dynamic IAM subsystem.

### <a id="imp-03-vdp-004"></a>`IMP-03-VDP-004` — Immutable VDP v1-v3 artifact family and prebuild boundary

- Decision state: `ACCEPTED` on 2026-08-28.
- Artifact identity: publish three independent immutable Platform FOTA
  candidates with semantic versions `1.0.0`, `2.0.0` and `3.0.0`. They retain
  the one accepted vehicle-data-provider component type and
  `systemd-slot-component` runtime; each candidate has distinct content and
  metadata digests.
- Historical evidence: Provider `0.2.0` and its accepted bytes remain
  immutable qualification evidence. They are neither relabelled as VDP v1 nor
  modified by the new release family.
- Capability graph: v1 exposes exactly the seven base-dynamics paths; v2 is
  the strict v1 superset adding four wheel-speed and four wheel-angular-speed
  paths; v3 is the strict v2 superset adding four longitudinal-slip and four
  lateral-slip paths plus the two typed Brake/Tire advisory request/status
  flows.
- Build composition: implementations may share reviewed source modules, but
  the deterministic builder includes only the release profile, capability
  manifest and runtime modules required by the selected version. An ordinary
  runtime switch may not unlock a later version's dormant capability in an
  earlier signed artifact.
- Payload contents: each candidate includes its executable/runtime files,
  immutable capability manifest, contract identities and digests,
  provenance, dependency lock, SPDX SBOM, licenses and notices. VISS/KUKSA
  endpoint ownership and systemd `LoadCredential` wiring remain in the
  Factory/runtime integration.
- Payload exclusions: no private key, token, Provider JWT, VISS client
  credential, Unit ID, Node ID, selected-vehicle assignment, Cloud target,
  signing credential or Service quota belongs in any VDP FOTA payload.
- Demo boundary: all three unsigned candidates are reproducibly built,
  validated and digest-frozen before an audience session. The Platform Team
  signs and submits the selected prepared candidate during the demo; no source
  edit, compilation, dependency download or package build occurs on stage.
- Promotion: after Test Vehicle qualification and Release Authority approval,
  the exact same signed artifact bytes are assigned to Production Vehicle.
  Promotion performs no rebuild, content mutation or second signature.
- Fail-closed version proof: package and contract tests prove exact manifests,
  deterministic double-build bytes, architecture/runtime identity and secret
  absence. They also prove that v1 cannot expose v2/v3 paths or advisory
  behavior, v2 cannot expose v3 behavior and an unknown, missing or mismatched
  manifest/version/digest keeps VDP `NOT_READY`.

This freezes the number, identity, capability delta, payload boundary,
prebuild rule and Test-to-Production byte identity of the first-demo VDP
release family. The future P1 VDP packet may generalize the existing builder
without mutating the immutable Provider `0.2.0` path.

### <a id="imp-03-vdp-005"></a>`IMP-03-VDP-005` — Native platform logs and OEM Runtime A/B storage ownership

- Decision state: `ACCEPTED` on 2026-08-28.
- No tenant quota: VDP is a trusted OEM platform component, not an Aos SOTA
  tenant. The first demo adds no VDP CPU/RAM quota, substitute resource manager
  or component-resource table. Service quota and isolation claims remain
  limited to Brake and Tire instances enforced by AosCore.
- Operational boundedness: VDP keeps only current validated state, uses fixed
  connection and endpoint topology, bounded retry/backoff and no unbounded
  telemetry, advisory, thread, file or in-memory history. Qualification checks
  for leaks or unbounded growth; it does not present those observations as a
  runtime quota.
- Native logging: VDP writes only allowlisted factual diagnostics to standard
  output/error under its systemd unit. The local system journal is the native
  source; authorized remote viewing uses the existing AosEdge/AosCloud log
  request and delivery path. VDP owns no log file, log database, archive or
  retention policy, and the Demo UI retains no second copy.
- Log disclosure: raw/high-rate telemetry, protocol frames, JWTs, credentials,
  certificates, VIN and unrestricted payloads are never logged or displayed.
  The Platform perspective labels the action `Platform Logs` and discloses its
  native Unit/system/VDP scope.
- No VDP application store: VDP persists no telemetry history, analytics model
  or application state. Restart reconstructs current truth from VISS/KUKSA and
  the accepted readiness contracts.
- Runtime storage ownership: the real persistent
  `systemd-slot-component/{slots,state,credentials}` tree belongs to the OEM
  Component Runtime. It is A/B working storage for payload installation,
  transaction recovery and private systemd credential sources, not a logical
  `VDP Component Store` or audience-visible VDP capability.
- Current demo backend: the existing 512-MiB nested ext4 implementation remains
  a demo-only OEM Runtime A/B working-storage backend. Production backend
  selection stays deferred; terminology and evidence may not imply a VDP-owned
  data store.
- Empty-state wording: M0/G0 evidence says `empty VDP component slot` and may
  additionally prove that Runtime A/B working storage contains no installed VDP
  payload. It no longer claims an `empty provider store`.

This replaces the rejected VDP quota proposal and removes the false VDP-owned
store/logging model without changing the accepted A/B runtime, native platform
log delivery or Service-tenant isolation requirements.

## Repository and Baseline Gate

| Item | Value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Accepted workspace revision | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Current clean local `main` | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Remote relationship | `main` equals `origin/main` |
| Future branch | `codex/imp-03-platform-vdp`, only after package and base acceptance |
| P0 writable paths | none |

The original three candidate commits were:

1. `51d3fce` — factory and rootfs artifact clarification;
2. `03c3065` — native Aos IAM credential-lifecycle documentation; and
3. `5c2a7d0` — QM Gateway boundary documentation.

The accepted reconciliation commit `bdc72ab` updates those five documentation
files and adds the planned `authorization/aos-kuksa-compat/README.md` boundary.
It contains no product-code, recipe, configuration or artifact delta. The
repository remote and solution lock are reconciled; a future code packet may
use the accepted revision only after its remaining implementation parameters
are frozen.

## Design Gates

The latest packages were design-reviewed on 2026-08-28:

- [Factory Substrate 0.5](../../../requirements/components/factory-substrate.md);
- [KUKSA Authorization Compatibility 0.12](../../../requirements/components/kuksa-authorization-compatibility.md);
- [Vehicle Data Platform 0.9](../../../requirements/components/vehicle-data-platform.md); and
- [Cross-Cutting 0.4](../../../requirements/components/cross-cutting.md).

Their acceptance freezes architectural requirements but does not authorize
implementation. Exact package-owned implementation parameters remain the
`IMP-03` gate.

## Frozen Requirements and Contracts

- `REQ-FACTORY-001` through `011`, `UT-FACTORY-001` through `009`;
- `REQ-KAC-001` through `010`, `UT-KAC-001` through `010`;
- `REQ-VDP-001` through `011`, `UT-VDP-001` through `008`;
- `REQ-CROSS-001`, `002`, `004`, `010` and the applicable owner-package tests;
- `IF-AUTH-007` through `010`, `IF-VEH-005`, `IF-DATA-001`,
  `IF-ADV-001` through `005`, `IF-LC-001` and `IF-LC-006`.

| Frozen file/contract | SHA-256 |
| --- | --- |
| Factory Substrate requirements | `fa450e7847beb7cfb5b5f09dea35a4e9bbf99412031336abafb4500a879ffc66` |
| KAC requirements | `ab0d6bf039d94d52b82ff77c6bcf74ffe397f9f2b6110f8be032ed07198c3e39` |
| VDP requirements | `acc1692c8147ef9a5236a29c01ae311afb4df6290d71b804611cf468423518a9` |
| Cross-Cutting requirements | `c8d2d15c4a1806511a99408dc341eb785c748109e7c4c9ebd9ad8ae1f9811f59` |
| KUKSA current-demo authorization v1 | `1ddd097976dc8606533307bf2f0f0619b166a295a38391e593340487b8d2931c` |
| VDP Compatibility v1 | `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871` |
| VISS Trust and Telemetry v1 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| QM Advisory v1 | `f7ae78148fb3b3265c8b773117126665afb1edd97a73f59db5a1f3af7c223487` |
| Platform FOTA Safe Stop v1 | `b92cd31c9b5066ca5b79c526134c3a059fcda0738cd668f3c96c6b51a0396c66` |

This table is the immutable digest record of the P0 input that was actually
assessed. The Safe Stop input was subsequently superseded by accepted
[`D4-028`](../../../requirements/d4-decision-register.md#d4-028) and contract
1.1.1; its current digest is intentionally not substituted into this
historical P0 evidence.

## Exact P0 Tasks

1. Confirm repository cleanliness, both revisions, the five-file docs-only
   delta and every frozen digest.
2. Compare the accepted revision with current `main`; recommend one exact base
   and list every workspace lock, component evidence and documentation pin
   that would need an accepted update. Do not make that update.
3. Inventory current Factory/runtime/provider/KUKSA integration source and
   tests at the recommended base. Distinguish reusable evidence from target
   behavior that does not exist.
4. Prove whether the current factory inputs already contain
   `enablePermissionsHandler: true`, the provider-specific empty-slot A/B
   runtime, bounded store, systemd/SELinux boundaries and no provisioned
   identity or pre-populated Service authority.
5. Inventory the planned removable `authorization/aos-kuksa-compat/` boundary,
   per-Unit signer/verifier preparation and JWT lifecycle. Record missing
   source explicitly; do not reuse the historical `authorization/aos-kuksa/`
   notes as an implementation.
6. Map VDP v1-v3, trusted Provider integration, typed outbound QM advisory and
   fresh Safe Stop application gate to exact source/test deltas.
7. Decompose `IMP-03` into smallest repository-owned code packets with exact
   paths and tests. At minimum separate successor Factory/runtime, KAC and VDP
   work where their package/lifecycle identities differ.
8. Return the unresolved package decisions and exact acceptance needed before
   each code packet may change from `BLOCKED` to `READY_FOR_REVIEW`.

## Baseline Checks

```text
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/quality_gate.py
```

Baseline evidence on 2026-08-28: 35 tests passed and the repository quality
gate passed for 82 tracked files at accepted `bdc72ab`. These checks do not
prove the target Factory Image, KAC, Safe Stop runtime or VDP v1-v3, and no
image or component was built.

## Forbidden Work

- no source, recipe, configuration, requirement, contract or lock update;
- no branch push or assumption that local-ahead commits are remotely accepted;
- no Yocto, VM image, provider component or FOTA build;
- no signing, upload, AosCloud, Unit, VM, provisioning or live qualification;
- no generated key, JWT, shared verifier, identity or secret; and
- no OEM Component Runtime behavior implemented before the package gates close.

## Completion Packet

The worker returns:

1. exact base recommendation and complete pin-update impact;
2. confirmed baselines, digests and repository status;
3. requirement/test-to-source delta matrices for Factory/runtime, KAC and VDP;
4. current reusable evidence and explicit missing target behavior;
5. exact proposed code packets, branches, worktrees, writable paths, tests and
   build-output boundaries;
6. package decisions still required before authorization;
7. baseline test results and environment limitations;
8. change requests or blockers; and
9. confirmation that no forbidden operation occurred.

## Exit and Escalation

P0 exited `BASELINE_ACCEPTED` at
`bdc72aba97a83c9868d454588189ef139710a6d7` with reconciled remote/main state
and updated solution pins. The exact Factory/runtime, KAC and VDP source
packets were subsequently accepted; they do not retroactively expand P0 or
authorize their combined merge, dependency retrieval, build, signing or VM
qualification. Any boundary expansion, missing immutable evidence, contract
conflict or external operation is escalated to the Platform owner and
Integration Coordinator.
