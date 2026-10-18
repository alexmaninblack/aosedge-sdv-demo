<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service runtime inputs

- Status: Accepted contract; implementation evidence is separately scoped
- Version: 2.3; source-baseline correction, no schema change
- Owner: Demo Control / OEM Platform
- Decision: [ADR 0015](decisions/0015-use-native-aos-service-runtime-inputs.md)

## Purpose and authority

This contract separates package provenance, public Unit/VDP/trust inputs,
native workload identity and private short-lived credentials. None substitutes
for another. Current scoped proof is mapped by the
[implementation view](current-implementation.md) and
[baseline](../qualification/current-baseline.md).

The [active-capability contract](../../contracts/service-runtime-inputs/active-vdp-capability-amendment.md)
binds Presenter software state to native Cloud and the exact installed artifact's
verified functional profile. The strict public projection below does not
identify that active profile. Services evaluate actual local inputs without a
Cloud/Presenter dependency; missing samples do not prove profile incompatibility.
No new guest timer, polling interface or mandatory projection is prescribed.
Legacy input/product decoders preserve their original schema and provenance;
they are not competing current authoring instructions.

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
daemon, wrapper, fixed service UID, privileged chown or token-specific SM code
is introduced by this contract.

KAC request/response, IAM authority, 300-second TTL, renewal at 180 seconds,
expiry, denial, retry and redaction remain unchanged. Remove AOS_SECRET
before starting analytics. Persistent model/outbox data stay in native
`/storage`; credentials never enter `/storage` or `/state.dat`.

## Activation and recovery order

<a id="native-launch-boundary--confirmed-11-september-2026"></a>

### Native launch boundary

Container launch and retained-instance recovery remain native AosCore duties.
Do not add a launcher, container startup wrapper, token/identity SM patch or
replacement container lifecycle for these inputs. Demo Control prepares our
packages and public inputs; the Factory image carries the declared resource
configuration. Generic native lifecycle bug fixes are tracked separately.

The [controller image lock](../../workspace/inputs/controller-images.lock.json)
selects the immutable Platform source. Its
[Service Manager recipe](https://github.com/alexmaninblack/aos-vehicle-platform/blob/3fd1f8eb8e8d51c7e89c9f89f1646c7d4f55494f/meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/aos-servicemanager_git.bbappend)
and matching IAM/CM recipes pin this native source set:

| Source | Exact revision |
| --- | --- |
| AosCore applications | `9d613a46df3c7f550062e2f19ae3406c57715694` |
| AosCore library | `5560291ba6914e36a5b841ade4d8fc54134a9e91` |
| AosCore API | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` |

These pins describe the selected image, not unmodified upstream main or an
instruction to refresh build inputs. Native container setup owns environment,
resource mounts and instance recovery. Public-input projection uses the
Factory-packaged SM startup hook described below, not a per-container
`aos-service@.service` template or replacement container runner.

Cold preparation reconstructs volatile input files; it does not reimplement
native container recovery. A missing application input is not evidence that
AosCore cannot launch a container. The five-field schema, provenance authority
and read-only mount contract remain unchanged. Startup and KUKSA authorization
require their own evidence in the current baseline.

### Required sequence

1. Package preparation and publication may occur before a vehicle exists.
   They do not require runtime inputs or a final OCI manifest lookup.
2. Before launch, project native Unit/role, committed VDP and public trust.
   Reject missing/contradictory inputs instead of supplying placeholders.
3. Load the Factory-packaged native resource configuration at SM initialization,
   not via hot reload. Routine service deployment requires no runtime
   activation or SM restart. The explicit activation command is an
   engineering migration operation, not a normal preparation step.
4. Assign service IDs through the existing Subject operation. Native Aos
   determines the actual instance and version.
5. Bootstrap authenticates through KAC, establishes TLS/subscriptions and
   starts analytics. Cloud Running is not functional Ready.
6. Refresh public files only after committed slot/process agreement.
   Old windows/outbox records retain their original provenance and bytes.
7. Cold start restores the /run sources from verified committed state before
   automatic retained assignments launch, without requiring a running VDP.
   After native SM recovery, verify process/slot agreement. Warm refresh still
   requires that agreement. This split changes no SM code or container lifecycle.

No direct guest reads are added to the Presenter platform dashboard; Cloud
remains its platform-state source. Engineering input projection/inspection is
a Demo Control operation, separate from dashboard observation.

<a id="cold-start-ordering-conflict--11-september-2026"></a>

<a id="historical-cold-start-ordering-conflict--11-september-2026"></a>
### Cold and warm projection ordering

The existing platform `aos-vehicle-data-provider-bootstrap.service` runs the
store check before `aos-sm.service`; it does not start VDP. The VDP service is
explicitly not enabled independently: component runtime
`SystemdSlotComponentRuntime::Start()` calls `Recover()`, which validates the
committed slot and starts the provider. The warm projector requires a
running provider whose process matches that committed slot. Putting the warm
projector into the pre-SM store check would therefore prevent SM from reaching
the code that starts the provider. The negative fixture verifies that no
public input is published when the provider is absent.

The component/startup sources are in the owning platform repository:
`meta-aos-vehicle-platform/recipes-aos/aos-vehicle-data-provider-platform/files/`
(`aos-vehicle-data-provider-bootstrap.service`, `aos-vehicle-data-provider.service`)
and `recipes-aos/aos-servicemanager/files/systemd-slot-component/runtime.cpp`
under the same layer. The Factory-packaged
`40-aos-demo-service-inputs.conf` invokes the shared projector in SM
`ExecStartPre` (`cold`) and `ExecStartPost` (`verify`). This is component/startup
integration, not a missing native container capability or a per-container hook.

Prepare cold-start inputs from validated committed state, then verify the
process after SM recovers VDP. An interrupted transaction does not authorize
using an intermediate slot or claiming functional readiness. Native component
recovery remains responsible for that transaction; public projection must
withhold incomplete or contradictory data, not prevent SM from performing
its recovery. No new SM hook, daemon, independent VDP launcher, persistent
metadata authority or container startup retry is authorized by this split.

The current Test uses native IAM `fileidentifier`, with `systemIDPath` equal
to `/etc/machine-id`; its value matches the observed IAM v6 response and Test
provisioning context. Cold preparation may read this same native source,
without persisting a second identity. Other identifier plugins are unsupported,
not silently substituted. The
[shared projector](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/service_inputs_guest.py)
validates the configured plugin/path and reads this native file; initial
activation and warm observations reconcile its value with native IAM.

## Product compatibility and evidence

[Product-message compatibility](../../contracts/service-runtime-inputs/product-message-migration.md) must
cover the service digest **and** Brake's modelArtifactSha256 alias of it.
Retain modelConfigSha256 and the VDP compatibility digest. Do not invent a
replacement artifact hash. New messages use an explicit new schema version;
legacy queues and backend records remain readable and are never relabelled.

The current placement and native source set above govern implementation.
[ADR 0015](decisions/0015-use-native-aos-service-runtime-inputs.md#9-evidence-and-limitations)
owns the accepted provenance and credential boundary.
The [current baseline](../qualification/current-baseline.md) selects scoped
startup/reboot, native KAC/TLS/subscription renewal, private-session and
vehicle-derived product evidence. It is not blanket acceptance of every
restart/failure combination.
Exact profile comparison uses Cloud in Presenter; services validate local
inputs independently. Full negative-matrix acceptance remains separate.
