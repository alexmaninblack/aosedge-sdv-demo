<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0015: Use Native Aos Facilities for Service Identity, Data and Tokens

- Status: Accepted — documentation migration and implementation authorized
- Version: 1.0
- Prepared: 2026-09-11
- Accepted: 2026-09-11, explicit user approval
- Owner: Demo Solution Team and OEM Platform Team
- Change class: C — application provenance contract and credential-file boundary
- Architecture input: [High-Level Architecture 1.6](../high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Delivery context: [Demo Studio delivery plan](../../planning/active/demo-studio-delivery-plan.md)

## 1. Accepted decision

Use the existing Aos container lifecycle, instance identity, permissions,
resource mounts and storage. Adapt our Brake/Tire applications and protocols
instead of extending Service Manager (SM) to supply application metadata or
special-case ownership of a KUKSA token directory.

The user approved this document and authorized the documentation cascade and
implementation on 11 September 2026. Acceptance defines the target; it does
not mean that executable contracts, applications or the VM already implement
it. The delivery plan records the ordered migration and its actual evidence.

For this scope:

- Do not add service-version or manifest-digest environment variables to SM.
- Retire the prepared SM token-mount UID/GID patch and its recipe integration
  before a build. Implement private sessions in the existing bootstraps.
- Use the same input and credential model for Brake and Tire, with separate
  service identities, instances, permissions and data.
- Retain the existing KUKSA authorization compatibility layer. It is our
  current-release integration, not a native Aos JWT-delivery feature.
- Make operational changes only through existing or agreed `democtl`
  commands. Add no separate operational wrapper or background helper.

"No SM changes" means no new SM code changes for the two issues covered here.
It does not claim that all earlier platform/runtime corrections have been
removed, authorize their removal, or qualify an unchanged Factory image.

## 2. Native facilities and our responsibilities

| Concern | Native Aos responsibility | Our application/integration responsibility |
| --- | --- | --- |
| Delivery and execution | Process the package, verify image contents, establish an instance, launch it and report lifecycle state | Prepare a consistent package and request deployment through the normal Cloud/Subject flow |
| Instance identity | Supply `AOS_ITEM_ID`, `AOS_SUBJECT_ID`, `AOS_INSTANCE_INDEX`, `AOS_INSTANCE_ID` | Use those identifiers without replacing them with team names, labels or operator choices |
| KUKSA authorization | Register instance permissions in IAM and supply `AOS_SECRET` | Existing KAC exchange converts authenticated IAM permissions to a short-lived KUKSA JWT |
| Application version | Record the published version and report the actual instance version | Include the same release value inside the application package; identify it as application-reported |
| Filesystem access | Apply named-resource mounts, instance UID/GID and supported quotas | Declare narrow resources; create private application-owned subdirectories |
| Persistent data | Provide `/storage` and, when requested, `/state.dat` | Keep outbox/model semantics explicit; never store JWTs in persistent or Cloud-synchronized state |
| Observability | Report actual service state and resource usage through Aos Cloud | Keep Cloud observations distinct from analytics/readiness messages |

The documented standard environment does not include the service version or
selected OCI manifest digest. The inspected IAM v6 permission response returns
the instance identity and permissions, not those two values. SM internally
knows the version and manifest digest; that does not establish an application
API for reading them. See the [native sources](#9-evidence-and-limitations).

## 3. Change the application provenance contract

### Version and identity

`democtl` assigns the release version once during package preparation and uses
that exact value both in publication metadata and a configuration file inside
the service package. The operator does not enter a second version. Brake and
Tire use the same semantic-version validation rules.

`serviceVersion` in a product message is application-reported provenance, not
runtime attestation. Native identifiers identify the Aos service/Subject/
instance; the current Unit system UID remains distinct from its Cloud UUID.
Do not assume that `AOS_INSTANCE_ID` changes on every process restart or
replace the existing advisory producer epoch with it.

### Remove the mandatory OCI digest dependency

The new product-message contracts do not require `serviceArtifactSha256`.
Service startup, analytics, backend ingestion and demo readiness must not wait
for the final ARM64 OCI manifest digest. Do not insert an empty, zero, archive,
binary, layer or index hash to satisfy an old validator.

This deliberately removes exact-OCI-manifest attribution from every product
message. Aos image verification remains in place. Engineering evidence may
retain an exact observed artifact digest separately, with its source and
meaning; it must not be fabricated or silently relabelled.

KAC authorization continues to rely on Aos IAM, not on any service-reported
version, digest or identity field. This changes application provenance, not
the authority model in [ADR 0013](0013-current-release-kuksa-authorization-compatibility.md).

### Retained public runtime inputs

| Input | Source and lifecycle |
| --- | --- |
| `unitSystemUid` | Native IAM system identity, reconciled with the current provisioning context; not the Cloud Unit UUID |
| `unitRole` | The initialized demo role; Test maps to the agreed validation wire role |
| `vdpContractVersion` | The committed active VDP compatibility contract, not the VDP functional profile or Cloud release number |
| `vdpContractSha256` | Digest of that compatibility contract; retained unchanged in meaning |
| Public KUKSA TLS certificate | The existing Unit-local public trust source; never its private-key sibling |

The public runtime metadata retains its schema discriminator but no longer
supplies `serviceVersion` or `serviceArtifactSha256`. Application version
comes from the package; native instance identifiers come from Aos.

Close an in-progress analytics window with its original provenance before a
VDP contract change. Already queued records retain their original version,
contract, event time and producer identity; never relabel them as current.

Update service producers, backend validators, correlation, advisory evidence,
readiness and Tire load-command binding together. Load commands target the
current Unit, service, version and instance rather than requiring an OCI
digest; fixed load profile, command idempotency, lease and stop bounds remain.
This identity tuple does not grant new authority or replace existing command
authorization and stale-command checks.

Publish new versions of the affected wire schemas. Existing persisted records
remain explicit legacy records; if old queued messages can still arrive,
retain their decoder until they drain. Do not delete history or rewrite
records merely to make a new schema pass. Exact schema versions and field
names are finalized in the contract migration, before producers change.

## 4. File placement

| Data | Container location | Access and owner |
| --- | --- | --- |
| Release version and fixed application configuration | Files inside the service package | Prepared with the package; no Unit-specific secrets or runtime identity baked in |
| Public metadata and KUKSA TLS trust | `/run/aosedge/platform/service-inputs/metadata.json` and `kuksa-ca.pem` | Root-owned public files, read-only to the service |
| KAC request socket | Existing `/run/aosedge/platform/kuksa-auth/request.sock` resource | Existing group/socket authorization unchanged |
| Short-lived JWT | `/run/aosedge/secrets/kuksa/session-<random>/token.jwt` | Private service-owned directory and file inside per-container tmpfs |
| Durable local outbox and working data | `/storage/<service-owned-subdirectory>` | Native instance-owned writable storage, with the declared quota |
| Intentionally Cloud-synchronized state | `/state.dat`, only when the application explicitly uses it | Separate native state facility; never credentials |

Use the existing public-input resource declarations:

| Service | Named resource | Host source directory |
| --- | --- | --- |
| Brake | `brake-runtime-inputs` | `/run/aos-demo-service-inputs/brake` |
| Tire | `tire-runtime-inputs` | `/run/aos-demo-service-inputs/tire` |

Both map into the same container destination because they belong to different
containers. A package requests only its own resource. Directory mode is 0755,
public files are 0444, and the bind retains `ro,nosuid,nodev,noexec`. Neither
the shared host parent nor a directory containing private keys is exposed.

Demo Control owns public-input preparation and refresh. It atomically replaces
files inside a stable source directory; replacing that directory itself would
leave a live bind attached to the old directory. Refresh VDP inputs only after
the component transaction commits, not at an intermediate slot switch.

Do not move model state or outboxes between native storage facilities as an
incidental part of this change. Their existing restart/update guarantees must
be preserved and verified against the pinned runtime. `/state.dat` has Cloud
synchronization semantics and is not a generic private local file.

## 5. Token ownership without an SM patch

### Root mount and private directory are different objects

The current resource mounts tmpfs with root mode 0700 but no instance owner.
Our bootstrap requires that same directory to belong to its non-root UID.
Native SM copies mount options; it does not resolve that conflict for us.

Change our resource declaration, not SM: keep the existing per-container
tmpfs destination and 64-KiB limit; retain `rw,nosuid,nodev,noexec`; change only
the tmpfs root mode to 1777. This is a change to the container resource,
not a `chmod` of a shared host directory.

The existing service bootstrap then:

1. Creates a fresh unpredictable private subdirectory using `mkdtemp` under
   that fixed mount. Mode is 0700; ownership is its actual effective UID/GID.
   Do not adopt a pre-existing or symlink-substituted session directory.
2. Supplies its exact token-file path to the analytics child through
   `KUKSA_TOKEN_FILE`. This carries a path, never the JWT itself.
3. Writes/replaces the token atomically as a regular mode-0400 file owned by
   the service. Readers validate ownership, mode and file type and reject
   symlink traversal. Both bootstrap and analytics stop assuming a fixed leaf
   at the root of the mount.
4. Removes the token on expiry/terminal denial and removes only its own
   session on normal shutdown. A new bootstrap never reuses an old token;
   container destruction removes the tmpfs. Crashes must not cause token
   adoption or an unbounded directory leak on in-container relaunch.

The root's 1777 mode permits directory creation and uses the sticky bit.
The token remains under a 0700 private directory, not directly in that root.
Separate containers receive separate tmpfs instances; no shared token volume,
fixed service UID, root service or privileged `chown` is introduced.

The source-confirmed alternative is `/tmp`: native SM creates a bounded tmpfs
there when `tmpLimit` is present. We prefer the existing named resource because
the pinned `/tmp` mount does not include all of our resource's `nodev,noexec`
flags, and the dedicated 64-KiB token space stays separate from working files.
No fallback to `/storage`, `/state.dat` or an arbitrary host directory is allowed.

Tmpfs is volatile storage, not a claim of hardware-backed secrecy or guaranteed
absence from swap. Do not claim a no-swap property without separate evidence.

### Authorization behavior stays unchanged

The existing [KAC contract](../../../contracts/kuksa-current-demo-authorization/README.md)
still owns issuance, exact scopes, renewal, expiry, trusted-time handling and
redaction. The bootstrap alone consumes `AOS_SECRET` and removes it from the
analytics child's environment. KAC still checks native IAM permissions and
keeps its signing key outside both services; it gains no access to their token
directories. Successful renewal reconnects/re-subscribes with the new token.
No Cloud dependency is added to local renewal or analytics.

## 6. Startup, update and recovery sequence

1. **Prepare public inputs.** Resolve the current Unit/role and committed VDP
   contract, project the public trust file and ensure source directories exist.
2. **Load resources.** Use standard Aos resource configuration. The pinned
   resource manager reads it at initialization; do not assume hot reload.
   Any required controlled SM restart is a configuration activation, not an
   SM code change, and remains an explicit `democtl` operation.
3. **Prepare and publish the service.** Use one package release value; sign
   and upload through Demo Control's normal Aos path. No final-manifest lookup
   is a prerequisite for creating its runtime metadata.
4. **Assign through the existing Subject flow.** Aos performs delivery and
   launch with the service's native permissions, UID/GID and resources.
5. **Bootstrap and run.** Create the private token session, complete the KAC
   exchange, verify KUKSA TLS and establish permitted subscriptions. Missing
   authorization or incompatible VDP data is not fabricated as readiness.
6. **Observe independently.** Obtain process/version/resource facts through
   Aos Cloud. Obtain analytics outcomes through the corresponding backend.
   Cloud processing Ready, process Running and functional Ready are different.
7. **Recover.** Acquire a new token session on launch. Preserve valid outbox,
   model and producer state; refresh public VDP inputs only on committed change.

Package preparation/publication may occur before a vehicle exists or is
provisioned, as already agreed for the demo story. Steps 1 and 2 gate service
launch, not publication. Cloud observation does not gate local analytics when
external connectivity is absent.

### Boot-ordering boundary that the mount alone does not solve

The selected host input directories are under `/run` and disappear on reboot.
An already assigned service may be restarted automatically by Aos. Therefore
calling a projector after that automatic launch is insufficient.

Before implementation is declared cold-start ready, the existing platform/
Demo Control startup path must establish public inputs before the relevant SM
launch, including retained assignments. Record the exact existing hook and
ordering during implementation review; this document does not invent a new
daemon, silently persist `/run` data or claim that a hook is already wired.
Warm assignment alone is not evidence that this boundary is closed.

## 7. Authorized coordinated change set

| Owner | Required change |
| --- | --- |
| Solution architecture/contracts | Reconcile HLA/flows, affected requirements and D4 profiles; version product messages, evidence and load-command bindings; replace the seven-field runtime-input contract |
| Demo Control | Prepare one coherent release, project public inputs, activate resource configuration, preserve startup ordering and use Cloud-reported lifecycle facts |
| Brake and Tire service repositories | Split package/runtime inputs, remove the required OCI digest, use equivalent identity/version validation, implement private token sessions and update readers |
| Brake and Tire backends | Migrate schemas/correlation/readiness and legacy ingestion without treating application provenance as platform attestation |
| Vehicle platform | Adjust named-resource configuration, retain KAC/socket/trust separation, remove only the unneeded token-owner SM patch and recipe wiring |
| Presenter UI | Retain Cloud-only platform monitoring and separate product/backend readiness; change no agreed demo flow |

Affected contract families include
[Brake windows](../../../contracts/brake-telemetry-window/README.md),
[Brake assessments](../../../contracts/brake-health-model/README.md),
[Tire assessments/status](../../../contracts/tire-health-model/README.md),
[Brake backend API](../../../contracts/brake-cloud-api/README.md),
[Tire backend API](../../../contracts/tire-cloud-api/README.md),
[shared evidence](../../../contracts/shared-evidence-correlation/README.md),
[advisory](../../../contracts/qm-advisory-profile/README.md),
[quota proof](../../../contracts/service-tenant-quota-proof/README.md) and
[KAC credential delivery](../../../contracts/kuksa-current-demo-authorization/README.md).
Only affected semantics advance; unrelated algorithms, quotas, Safe Stop,
production deployment, signing authority and token lifetimes do not change.

## 8. Focused acceptance, not a new broad qualification cycle

After document approval, use targeted contract/bootstrap tests, then one
bounded Test integration through `democtl`:

- Package version equals publication version; no mandatory manifest-digest
  lookup, fabricated hash or runtime metadata substitution remains.
- Both services launch under native non-root identities; private token paths
  have the intended ownership/modes and are isolated from the peer container.
- Token issue, replacement/re-subscription, expiry, denial and restart behave
  as before; secrets do not enter logs, artifacts or Cloud state.
- Public inputs are readable but not writable; VDP refresh keeps historical
  events intact. Missing/invalid trust or identity fails truthfully.
- Actual subscriptions and backend records work; Cloud independently reports
  the running version. Local operation survives the agreed external disconnect.
- Cold start with retained assignments restores inputs before launch; storage,
  producer epochs and queued records obey their existing contracts.
- Effective mounts and fresh scoped SELinux evidence confirm access under the
  real service identity. Do not broaden policy merely to make a check pass.

Document approval authorizes the scoped documentation/source migration and
targeted tests. It does not independently authorize a Factory rebuild,
cleanup or provisioning cycle. Live actions use the existing bounded Test
authorization and Demo Control; no Production mutation is included.

## 9. Evidence and limitations

Read-only inspection on 11 September 2026 used AosCore revision
`9eecb80c4994937b5c8cbe0464970f81e8ad4c2d`, the local IAM v6 descriptors,
our Brake/Tire bootstrap sources and resource templates. It established the
available mechanisms, not a completed live service deployment.

| Source | What it supports |
| --- | --- |
| [Aos Launcher](https://docs.aosedge.tech/docs/aos-core/architecture/service-manager/launcher) | Native container setup, environment and lifecycle |
| [Aos IAM](https://docs.aosedge.tech/docs/aos-core/architecture/identity-access-manager/) | Native identity and permission responsibilities |
| [Package processing](https://docs.aosedge.tech/docs/how-to/run-your-application/run-qm-service) | Package files/configuration and Cloud generation of OCI artifacts |
| [Image deployment pipeline](https://docs.aosedge.tech/docs/aos-core/service-lifecycle/image-deployment-pipeline) | Native image verification, assembly and launch |
| [Service configuration schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-service-config) | Temporary/storage/state quotas and requested resources |
| [Storage/state](https://docs.aosedge.tech/docs/aos-core/service-lifecycle/storage-state) | Instance-owned storage and Cloud synchronization of state |
| [Pinned container runtime](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/launcher/runtimes/container/instance.cpp) | `CreateAosEnvVars`, `ApplyItemConfig`, `AddResources`, `PrepareStateStorage`; no special token-owner mapping required by native API |
| [Linux tmpfs](https://docs.kernel.org/filesystems/tmpfs.html) | Mount-root mode/ownership, size, volatile lifetime and swap caveat |

The published storage documentation contains differing statements about
preservation across a version update. Do not resolve that by selecting the
most convenient sentence: retain our accepted data-preservation obligation and
verify the actual same-instance update path. The sources also do not establish
a public pre-assignment API for the final ARM64 manifest digest; this decision
removes that dependency rather than claiming such an API exists.

### Review relationship to earlier records

The [service-input contract](../demo-control-service-inputs.md) is the current
implementation mapping. This ADR replaces its former seven-field input,
manifest-before-assignment requirement and token-owner patch proposal only;
the valid read-only trust/resource findings remain applicable. The
[11 September checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-11.md)
remains historical evidence of what was actually built, committed or tested.

The accepted provenance tradeoff, token root/private-directory distinction
and boot-ordering gate apply to the coordinated implementation. P5/P7/E2E
remain open until their actual exit evidence exists; old checkpoint records
are historical and are not rewritten as evidence of the new design.
