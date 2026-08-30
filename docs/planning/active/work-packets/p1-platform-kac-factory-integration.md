<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KAC Factory Integration Work Packet

- ID: `WP-P1-PLATFORM-KAC-FACTORY-INTEGRATION-002`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-KAC-FACTORY-INTEGRATION`
- State: `COMPLETED IN PLATFORM TRAIN — FACTORY-QUALIFIED IN .21`
- Version: 0.9
- Prepared: 2026-08-29
- Product edit, offline package proof and one local Factory commit authorized:
  yes, inside the frozen boundary and consolidated Platform Train
  authorization recorded on 2026-08-29
- External network, image build, VM/Unit operation, provisioning, real
  PKCS#11 signing, FOTA, Cloud and live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Critical-path sequence:
  [Infrastructure-First Critical Path](../infrastructure-first-critical-path-proposal.md)
- Completed source input:
  [KAC compile integration](p1-platform-kac-compile-integration.md)
- Required predecessor:
  [KUKSA Row2 scope parser](p1-platform-kuksa-row2-scope-parser.md)
  (`WP-P1-PLATFORM-KUKSA-ROW2-SCOPE-001`) — completed and locally committed;
  exact source, test and `do_package` evidence frozen below
- Later fan-in: `WP-P1-PLATFORM-SUCCESSOR-FANIN-001` — authorized only as the
  subsequent umbrella Platform Train stage; not owned by this packet

## Completion Resolution

This source/package stage completed in the Platform train and was carried
through the successor fan-in and qualification fixes into accepted source
`667afb1512cf43ff27f1ab5327293208bf73045b`, image
`6.1.1-maninblack.21`. The original exclusions below remain the exact authority
boundary of this packet; later image, VM and Cloud qualification occurred only
under separate explicit authorization and grants no residual authority here.

## Outcome

Integrate the completed removable KAC package into the successor Factory
composition and add only the missing product-owned seams around it:

1. the native Aos named resource used by Brake and Tire Service bootstraps;
2. the dedicated `kuksa-jwt` certificate-module/token bootstrap and
   provisioning-state handoff;
3. fail-closed startup of the separately patched KUKSA 0.5.0 predecessor with
   the volatile Unit verifier;
4. one strictly separated one-shot fixed OEM Provider credential preparer
   delivered in the same temporary KAC compatibility package; and
5. deterministic image-package composition and configuration tests.

This packet owns no existing Service-facing KAC request/JWT business logic, no
Service bootstrap, no VDP data/advisory behavior and no Safe Stop Runtime
behavior. It produces a source/package checkpoint only. The controlled fan-in,
bootable image and disposable-VM qualification remain later packets.
It does not own the accepted KUKSA scope-parser correction; that is a separate
mandatory predecessor because the pinned upstream parser cannot represent the
already accepted FI-02 paths.

The former packet `...-001` is superseded. It incorrectly described the fixed
Provider signer as owned by the Service-facing KAC daemon/API. The accepted
replacement delivers Provider preparation in the same temporary
`aos-kuksa-auth-compat` deployable, but as a separate networkless executable,
unit, code path and authority boundary. No Provider operation enters the KAC
socket/API. The complete compatibility deployable and its wiring are removed
together when native EOS Core replaces both authorization paths.

## Frozen Inputs

| Input | Exact identity |
| --- | --- |
| Solution committed baseline | `aosedge-sdv-demo@4bede414b402c4b94bd45a9b4f4caac5992bb390`, tree `0c21b8e045474c75af024a0f7f6d41087446fbd3` |
| Product main ancestry | `aos-vehicle-platform@bdc72aba97a83c9868d454588189ef139710a6d7` |
| Completed KAC checkpoint | `aos-vehicle-platform@570d17821edfd85915e688f7239a04eb4fc1f535`, tree `6ebe07e7793f3dbbacc688fd8781d12c70b1f599` |
| Required Row2 result commit | `405546b9efa6d5acf6ced4bc14a5249860d448de`; single parent `570d17821edfd85915e688f7239a04eb4fc1f535` |
| Required Row2 result tree | `54676116a89dd929605173bef66868564e8c3aa6` |
| Required Row2 package identity | `PN=kuksa-databroker`, `PV=git`, `PR=r0`, `PACKAGE_ARCH=cortexa57`; installed package-split root `tmp/work/cortexa57-aos-linux/kuksa-databroker/git/packages-split/kuksa-databroker` |
| Row2 package-archive status | no patched RPM/archive filename or archive SHA exists: `do_package`/`do_package_qa` were authorized and completed, but `package_write_rpm` was neither authorized nor executed; distinct patched RPM count `0` |
| Required Row2 package proof | databroker binary SHA-256 `bea1717b593a9ab343a24948004075df0eb96c2a8b68baa247f620591c30af02`; normalized installed-package-content SHA-256 `7016769004ebd32459bbb797d1559da9402d3c7c213c039359e62ac72fc2de5b` |
| Required Row2 patch/source proof | patch SHA-256 `f48fd0493d11bf3a8157d8290c58494836e11de985733aaccf18a092efb36ba4`; patched `scope.rs` SHA-256 `8ed0ce84ff9fb4baac518e9aff299bb9f70f181f283ac546cc3b3064d5c75a1d` |
| Required Row2 closure evidence | no original aggregate evidence manifest was created (`count=0`); post-completion bounded read-only retrieval export `/private/tmp/kuksa-row2-evidence-export-20260829`, manifest `evidence-manifest.sha256`, manifest SHA-256 `228a9cffc6b290191159ac8e66ee654070bf5916dca51a48924df625cf8fc30e`, `22/22` entries independently verified; first/repeat ARM64 scoped Rust `17/17`, host suite `50/50` |
| Runtime checkpoint, later fan-in input only | `4d8800636ded58386e2872a7e415dc1cc322c92c`, tree `db3d316675a0cf0a60574c90634a75207a4a26c4` |
| VDP-family checkpoint, later fan-in input only | `67123333775a696a1143d0281013651b3736f0fd`, tree `5a81007a95932cf63f516304538484e3476f4649` |
| KAC requirement | `CR-KAC` 0.12, SHA-256 `ab0d6bf039d94d52b82ff77c6bcf74ffe397f9f2b6110f8be032ed07198c3e39` |
| Factory requirement | `CR-FACTORY` 0.5, SHA-256 `9c8e224c4e0ecdf366a7acb95f2fd310b23cf109dd33bd20232b1982ba361c2d` |
| VDP requirement | `CR-VDP` 0.9, SHA-256 `6650864fd83229a43fcb843c663558844d51e90d1f208c4131501bede9af5fee` |
| KAC executable contract | 1.7.0, SHA-256 `1ddd097976dc8606533307bf2f0f0619b166a295a38391e593340487b8d2931c` |
| VDP compatibility profile | 1.0.1, SHA-256 `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871` |
| QM advisory profile | 1.0.2, SHA-256 `f7ae78148fb3b3265c8b773117126665afb1edd97a73f59db5a1f3af7c223487` |
| Pinned metadata | `meta-aos@176da6346b1199f854106dede4cc49604174619c`; `meta-aos-vm@b13320898a2ed1cce504f90f70451638232d6a83` |
| Pinned Aos sources | `aos_core_cpp@9eecb80c4994937b5c8cbe0464970f81e8ad4c2d`; `aos_core_lib_cpp@60cb83535f773762c61ac5f544b31b7b88c502e3`; `aos_core_api@af3552a0a5eb0237eff7f5f183780ca46c339cd3` |
| Pinned KUKSA source | `kuksa-databroker@30e5c13abc496d0b39aaa6c25acebb088b9902e3`, tree `919f40c5f88ff0a74304c9e99a36b726462a2363` |
| Completed Gate 0 evidence export | `/private/tmp/kac-factory-gate0-evidence-20260829`; manifest SHA-256 `57ecc8a6f2147eeb9ec3b6cbfc39e05dd8602dc32e82b5bc79f915dbfc7b98f4`; matrix SHA-256 `6044ae1d112e3302adb337f8f395e6d18445d0672f2e36d5b02a3964b92cec09` |
| Target/toolchain | R6.1 `qemuarm64`, `aarch64-aos-linux`, GCC 13.4.0 |

The post-completion Row2 export is retrieval evidence, not a falsely
backdated build-time manifest. Its `row2-output-facts.txt`, raw
`kuksa-databroker.pkgdata`, `repeat-patched-package-inventory.txt` and
`manifest-cortexa57-kuksa-databroker.package` prove the exact package name,
`git-r0` version and `cortexa57` architecture. The nominal
`kuksa-databroker-git-r0.cortexa57.rpm` present in the older baseline build is
explicitly unpatched (SHA-256
`ffc140b3fbd4a34297b77398c049a72b4258220ad28d36a78599725996b64e3e`)
and is forbidden as a Row2 or Factory input. Gate 1 consumes the exact source
checkpoint; Gate 3 under the consolidated Platform Train authorization must
create and hash any deployable archive.

The completed KAC checkpoint fixes package/recipe
`aos-kuksa-auth-compat` 0.1.0. Its main package contains exactly
`/usr/libexec/aos-kuksa-auth-compat`,
`/usr/libexec/aos-kuksa-verifier-prepare`, the two matching systemd units and
one tmpfiles file. Its explicit runtime dependencies are `openssl`,
`pkcs11-provider` and `softhsm`; its systemd credential ID is
`kuksa-jwt-pin`, sourced only from `/var/aos/iam/.kuksa-jwt-pin`.

The current `.11` image is evidence only, not an implementation base. Read-only
byte inspection proves the pinned image uses:

- `/etc/aos/resources.cfg` as Service Manager's configured resource path;
  read-only byte inspection recovered no usable resource-definition fixture,
  so it is not accepted as schema evidence;
- `kuksa-databroker.service` with `/usr/bin/databroker $EXTRA_ARGS` and
  `/etc/default/kuksa-databroker`;
- the current fixed KUKSA arguments, including
  `--jwt-public-key /etc/kuksa-val/jwt.key.pub`; and
- the IAM certificate-module keys `id`, `plugin`, `algorithm`, `maxItems`,
  `selfSigned` and `params.{library,tokenLabel,userPinPath,modulePathInUrl}`.

The image evidence alone did not prove the upstream `ResourceInfo` shape,
recipe ownership or provisioning lifecycle. Completed Gate 0 pinned-source
evidence now proves those facts and is authoritative over the binary strings;
it also exposed the separate KUKSA Row 2 parser defect whose qualified closure
is recorded below.

## Repository and Isolation

| Item | Proposed frozen value after review |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| New branch | `codex/imp-03-kac-factory-integration` |
| New isolated worktree | `../aos-vehicle-platform-imp-03-kac-factory-integration` |
| Required initial HEAD | exact clean `405546b9efa6d5acf6ced4bc14a5249860d448de`, tree `54676116a89dd929605173bef66868564e8c3aa6` |
| Required ancestry | KAC checkpoint plus only the accepted parser predecessor; no Runtime/VDP merge |

The later fan-in imports Runtime, VDP, KAC and this checkpoint in the separately
reviewed order. This packet may not merge or rebase another implementation
branch. Generated output stays outside every Git repository.

## Accepted Required Predecessor — KUKSA scope parser

The bounded predecessor is
[`WP-P1-PLATFORM-KUKSA-ROW2-SCOPE-001`](p1-platform-kuksa-row2-scope-parser.md).
Its direction, separate execution and local checkpoint are complete. The clean
single-parent commit/tree, patch/patched-source hashes, first/repeat ARM64
`17/17`, host `50/50`, binary and normalized package-content hashes, pkgdata and
post-completion retrieval manifest are frozen above. The absence of a patched
RPM is factual and non-blocking for source Gate 1 because `package_write_rpm`
was outside Row2 authorization; no baseline RPM is substituted.

Gate 0 proved that pinned KUKSA 0.5.0 parses each VSS path segment with
`[A-Z][a-zA-Z0-1]*`. Eight accepted VDP-v3 paths contain segment `Row2`, for
example `provide:Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed`, so the exact
27-entry FI-02 Provider scope cannot be parsed. Renaming the VSS paths,
dropping Row 2 authority, adding wildcards or widening FI-02 is forbidden.

The operator accepted a separate bounded predecessor patch. It changes only
the KUKSA segment grammar needed to accept ASCII digits `0` through `9` after
the required leading uppercase letter, preserves all separators, operation
names and wildcard/invalid-character rejection, and adds exact positive Row 2
plus digit-leading/wildcard/invalid-character negatives. It must be reviewed,
tested, packaged and committed separately. This Factory packet consumes only
the exact qualified source checkpoint and may not implement, broaden or hide
the KUKSA patch. Those predecessor conditions are now satisfied; a deployable
archive remains a later package-write output, not a Gate 1 input.

## Accepted Design Decisions

### FI-01 — fixed Provider preparation ownership

**Status:** `ACCEPTED` — operator decision recorded 2026-08-29.

One temporary deployable package/recipe `aos-kuksa-auth-compat` owns two
strictly separated authorization paths:

1. the existing long-running Service-only KAC daemon and socket/API; and
2. one new root-owned networkless one-shot executable
   `/usr/libexec/aos-kuksa-provider-prepare` with its own
   `aos-kuksa-provider-prepare.service`.

The Provider executable may share the provisioned Unit's `kuksa-jwt` PKCS#11
trust root, the private systemd credential ID `kuksa-jwt-pin` and audited pure
signing/encoding primitives with the daemon package. It has no socket/API, no
IAM or Cloud call, no renewal loop, no caller-selected input and no runtime
dependency on the KAC daemon. The two executables have separate units,
filesystem access and SELinux domains; package co-location grants neither
process access to the other's runtime state.

Provider issuance is absent from the KAC socket protocol and Service daemon
dispatch. The complete compatibility package, its units, policies, runtime
paths and Factory wiring are removed together only after native EOS Core has
qualified replacements for both Service authorization and the fixed Provider
credential. Package removal must not guess whether the native replacement
adopts or replaces the existing per-Unit trust root.

### FI-02 — fixed Provider JWT claims

**Status:** `ACCEPTED` — operator decision recorded 2026-08-29. Gate 0 proved
the exact pinned serialization rules and exposed the separate Row 2 parser
defect; FI-02 itself is not weakened or renamed to work around that defect.

**Recommendation:** freeze one deterministic profile:

- header `alg=RS256`, `typ=JWT`;
- `sub=aos-vdp`, `iss=aosedge-vdp-provider`, `aud=[kuksa.val]`;
- `iat` from trusted UTC and `exp=iat+604800` seconds;
- one lexicographically sorted, single-space-delimited `scope` string; and
- no `jti`, Unit/Node/VIN, Cloud identity, role, arbitrary extension or caller
  input.

The fixed scope is `provide` on all 23 VDP-v3 telemetry paths and the two
Brake/Tire `GatewayStatus` paths, plus `read` on the two Brake/Tire advisory
`Request` paths. Wildcards, `create`, `actuate` and every other scope reject.
The seven-day lifetime intentionally exceeds one demo/qualification run and
avoids a presentation-time Provider renewal path. It is a current-demo
compatibility choice, not evidence of production-grade revocation or
continuous credential lifecycle.
The preparer writes only the compact JWT, atomically and as root-owned mode
`0600`, to
`/var/aos/workdirs/sm/runtimes/systemd-slot-component/credentials/kuksa-token`.
The already accepted Provider unit consumes that exact source only through
`LoadCredential=kuksa-token`.

### FI-03 — provisioning/reboot/deprovision handoff

**Status:** `ACCEPTED` — operator decision recorded 2026-08-29; the
pre-connection/established-session correction below supersedes the earlier
instant in-session expiry interpretation.

Unit provisioning remains authoritative. A downstream authorization failure
does not roll back or misreport an otherwise successful native AosCore
provisioning result. The accepted lifecycle uses product-owned systemd
integration, not a KAC lifecycle controller or Provider renewal daemon:

1. before `aos-iam.service`, a root networkless one-shot in its own
   `aos_kuksa_token_init_t` domain creates or validates the dedicated
   `aos-kuksa` SoftHSM token and mode-`0600`
   `/var/aos/iam/.kuksa-jwt-pin` in the writable Unit overlay; it uses the
   native PKCS#11 API and kernel randomness so no PIN appears in a command
   argument or environment, and it never creates the `kuksa-jwt` key itself;
2. native Aos provisioning creates the one RSA-2048 self-signed `kuksa-jwt`
   object through the added certificate module;
3. after provisioning, verifier preparation publishes only the tested public
   key; KUKSA depends on that verifier, the Service KAC daemon depends on the
   verifier and trusted time but not Provider output, and VDP additionally
   depends on a valid fixed Provider JWT;
4. on ordinary boot, the volatile verifier is reconstructed from the existing
   Unit key and the Provider JWT is checked before VDP connection. A valid
   existing token is reused. If it is missing or expired, the networkless
   Provider one-shot runs once after the key, verifier and trusted-time
   prerequisites and atomically writes a new token;
5. the boot/provisioning one-shot has one bounded systemd start activation and
   no polling or background renewal loop. A failed write exposes no partial
   token and preserves any previous still-valid token. Failure leaves the unit
   failed and its direct dependants factually `NOT_READY`;
6. no JWT parser or expiry timer is added to VDP. If the Provider JWT expires
   during an already established KUKSA session, the demo makes no exact
   in-session revocation claim. Expiry is detected and enforced on the next
   reconnect/authentication; failed reauthentication then makes VDP
   `NOT_READY` until an explicit controlled Provider one-shot and VDP
   service restart loads the replacement systemd credential. A reconnect by
   the unchanged process would reuse its old private snapshot. No hidden
   background renewal occurs; and
7. deprovision stops VDP, KAC and KUKSA, removes the Provider JWT plus volatile
   verifier/socket state and prevents further issuance. R0 overlay disposal
   remains the destruction proof for the per-Unit key and PIN.

The dependency/readiness result is fixed as follows:

| Condition | Direct result |
| --- | --- |
| Token/PIN initialization fails before provisioning | Provisioning does not start or report success; KUKSA, Provider, VDP and KAC remain unavailable. |
| Native provisioning succeeds and all prerequisites are ready | Verifier is reconstructed, KUKSA starts fail-closed with it, Provider JWT is reused or prepared, VDP becomes ready, and KAC independently serves Service authorization. |
| Valid Provider JWT exists on boot | Reuse it; do not sign a replacement merely because the Unit rebooted. |
| Provider JWT is missing or expired on boot | Run the Provider one-shot once; VDP waits for success, while KUKSA and KAC retain their independent readiness. |
| Provider preparation fails | Preserve any previous still-valid token; VDP is `NOT_READY` when no valid token remains. KUKSA and KAC are not blocked by this failure. |
| Common Unit key/PIN or verifier is missing/malformed | Provider cannot sign, KUKSA remains blocked and KAC cannot become technically ready; VDP and dependent functional Services are `NOT_READY`. |
| Trusted time is unavailable on cold boot | No new Provider or Service JWT is issued; KAC reports time-untrusted readiness and VDP remains `NOT_READY`; unrelated AosCore work and successful provisioning state remain intact. |
| Provider JWT expires while VDP is running | The established KUKSA session may continue; no exact instant-revocation claim is made. The next reconnect/authentication enforces expiry and then leaves VDP `NOT_READY` until explicit controlled re-preparation and VDP service restart. KAC remains independent. |
| Deprovision | Stop the three affected runtime paths, remove Provider/verifier/socket state and prevent issuance; R0 later destroys key/PIN state with the overlay. |

Gate 0 proved the native lifecycle seam, so the trigger is no longer open:
IAM service drop-ins pull a finite token-init prerequisite; successful native
provisioning restarts `aos.target`, which pulls the KUKSA substrate target; and
the product-owned override of the existing `aos-deprov` script invokes the
static cleanup unit after stopping the current `aos.target` wants and before
removing `/var/aos/.provisionstate`. No `.path` unit, watcher, lifecycle daemon
or ordinary-shutdown cleanup is introduced. In particular, the cleanup hook
does not run merely because the VM reboots, so a still-valid Provider JWT can
be reused on ordinary boot exactly as FI-03 requires.

## Fixed Native Named-Resource Semantics

The resource identity and effects are decided, and Gate 0 proved the pinned
top-level JSON-array schema and field set:

| Field | Fixed value |
| --- | --- |
| Name | `kuksa-auth-client` |
| Sharing | `sharedCount: 4` |
| Supplementary groups | exactly `aos-kuksa-clients` |
| Host socket directory | `/run/aos-kuksa-auth-compat` |
| Container socket directory | `/run/aosedge/platform/kuksa-auth` |
| Mount policy | bind, read-only; no caller-selected path |
| Private token tmpfs | `/run/aosedge/secrets/kuksa`, exactly 64 KiB, mode `0700`, `nosuid,nodev,noexec` |
| Authority content | none; no secret, token, permission, subject or path scope |

The existing upstream `kuksa` entry is copied byte-for-byte into the product
override and followed by exactly this second entry. The top-level value remains
one JSON array; the field name is `envs` if ever used, not `env`, although this
resource deliberately supplies no environment value:

```json
{
  "name": "kuksa-auth-client",
  "sharedCount": 4,
  "groups": [
    "aos-kuksa-clients"
  ],
  "mounts": [
    {
      "destination": "/run/aosedge/platform/kuksa-auth",
      "type": "bind",
      "source": "/run/aos-kuksa-auth-compat",
      "options": ["rbind", "ro", "nosuid", "nodev", "noexec"]
    },
    {
      "destination": "/run/aosedge/secrets/kuksa",
      "type": "tmpfs",
      "source": "tmpfs",
      "options": ["rw", "nosuid", "nodev", "noexec", "mode=0700", "size=65536"]
    }
  ]
}
```

Gate 2 must feed the complete two-entry file through the pinned Resource
Manager parser and prove the effective OCI mounts. If the pinned runtime does
not accept these exact bind/tmpfs options, stop and revise this packet; do not
silently drop an option, widen the mount or introduce a second resource owner.

Brake and Tire item metadata request this resource in their own SOTA packets.
This Factory packet defines only the native resource and validates exact
allocation/isolation behavior. It does not edit either Service artifact.

## Frozen Gate 1 Writable Boundary

After the frozen Row2 identities are re-read and Gate 1 is separately
authorized, the changed-path set must be a subset of the following exact list.
`**` below does not authorize an arbitrary file; it expands only to the
explicitly named children in that item.

### Same temporary KAC deployable

- modify `authorization/aos-kuksa-compat/CMakeLists.txt` only to move project
  version to `0.2.0`, add a Provider-only library/test target and install the
  third executable;
- modify `authorization/aos-kuksa-compat/README.md` only for the implemented
  separate-process Provider path and common removal boundary;
- add `authorization/aos-kuksa-compat/include/kac/provider.hpp`,
  `authorization/aos-kuksa-compat/src/provider.cpp`,
  `authorization/aos-kuksa-compat/src/provider_prepare.cpp` and
  `authorization/aos-kuksa-compat/tests/provider_tests.cpp`;
- reuse `src/pkcs11_signer.cpp` and the existing strict JSON/Base64 primitives
  as separately linked source inputs without editing them; the Provider target
  must not link `kac_proto`, gRPC or `grpc_iam_client.cpp`;
- replace recipe filename
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/aos-kuksa-auth-compat_0.1.0.bb`
  with the otherwise continuous
  `aos-kuksa-auth-compat_0.2.0.bb`, adding the executable/unit to the same
  `${PN}` and creating no subpackage; and
- modify only
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/files/aos-kuksa-auth-compat.service`
  and
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/files/aos-kuksa-verifier-prepare.service`,
  and add only
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/files/aos-kuksa-provider-prepare.service`
  to implement the exact graph below. The existing
  `aos-kuksa-auth-compat.conf` tmpfiles fixture remains unchanged; no Provider
  state directory is added.

The existing Service daemon files `include/kac/core.hpp`, `src/core.cpp`,
`src/json.cpp`, `src/grpc_iam_client.cpp`, `src/pkcs11_signer.cpp`,
`src/main.cpp`, `src/server.cpp`, `src/verifier_prepare.cpp` and
`tests/kac_tests.cpp` are frozen. A need to edit any of them stops for a
separate reviewed correction. In particular, Provider preparation may not be
added to the Service protocol, dispatcher or socket.

### Factory integration implementation and units

- add exactly
  `authorization/aos-kuksa-factory-integration/CMakeLists.txt`,
  `authorization/aos-kuksa-factory-integration/include/factory/integration.hpp`,
  `authorization/aos-kuksa-factory-integration/src/token_init.cpp`,
  `authorization/aos-kuksa-factory-integration/src/runtime_cleanup.cpp` and
  `authorization/aos-kuksa-factory-integration/tests/factory_integration_tests.cpp`;
- add recipe
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-factory-integration/aos-kuksa-factory-integration_0.1.0.bb`;
- add only these recipe fixtures:
  `files/aos-kuksa-substrate.target`,
  `files/aos-kuksa-provision-reset.service`,
  `files/aos-kuksa-token-init.service`,
  `files/aos-kuksa-runtime-cleanup.service`,
  `files/aos-iam-prov.service.d/20-kuksa-token-init.conf`,
  `files/aos-iam.service.d/20-kuksa-token-init.conf`,
  `files/kuksa-databroker.service.d/20-kuksa-verifier.conf` and
  `files/aos-vehicle-data-provider.service.d/20-kuksa-provider.conf`;
- add
  `meta-aos-vehicle-platform/recipes-aos/aos-deprov/aos-deprov.bbappend`
  and
  `meta-aos-vehicle-platform/recipes-aos/aos-deprov/files/deprovision.sh` as an
  exact pinned-script override. The override
  preserves every existing command and adds only a bounded invocation of the
  static cleanup unit after async target-want stop and before provision-state
  removal, plus the same cleanup before the full clear path. The `aos-deprov`
  package remains the sole owner of `/opt/aos/deprovision.sh`;
- add
  `meta-aos-vehicle-platform/recipes-aos/aos-iamanager/aos-iamanager_git.bbappend`
  and
  `meta-aos-vehicle-platform/recipes-aos/aos-iamanager/files/aos-kuksa-iam-configure.py`
  only for a deterministic build-time
  transformation/validation of the installed `iam.cfg`. The transformer is
  not installed; the Factory-integration package above owns the two service
  drop-ins; and
- add the complete upstream `kuksa` fixture plus the exact second entry above
  only at
  `meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/resources.cfg`.
  Do not change the existing Service Manager bbappend or install that file
  from Factory integration.

The IAM transform preserves every current module and adds exactly one module:

```json
{
  "id": "kuksa-jwt",
  "plugin": "pkcs11",
  "algorithm": "rsa",
  "maxItems": 1,
  "selfSigned": true,
  "params": {
    "library": "/usr/lib/softhsm/libsofthsm2.so",
    "tokenLabel": "aos-kuksa",
    "userPinPath": "/var/aos/iam/.kuksa-jwt-pin",
    "modulePathInUrl": true
  }
}
```

It also requires the existing top-level `enablePermissionsHandler` value to be
exactly `true`; false, absent, duplicate IDs, a changed existing module or a
second `kuksa-jwt` entry fails the build. The later fan-in, not this packet,
must reconcile the known shared-IAM-transform collision with the Permission
Handler branch without changing this resulting JSON.

### Composition, policy, tests and factual docs

- modify `meta-aos-vehicle-platform/recipes-core/images/aos-image-vm.bbappend`
  only to append `aos-kuksa-auth-compat` and
  `aos-kuksa-factory-integration` once;
- modify only
  `meta-aos-vehicle-platform/recipes-security/refpolicy/files/aos_kuksa_auth_compat.te`,
  `.fc` and `.if` for the new Provider domain; add only the matching
  `aos_kuksa_factory_integration.te`, `.fc` and `.if` in that same directory;
  and add only those three new policy files to
  `meta-aos-vehicle-platform/recipes-security/refpolicy/refpolicy-aos_git.bbappend`;
- add `tools/validate_kac_factory_integration.py` and
  `tests/test_kac_factory_integration.py`; and
- modify `meta-aos-vehicle-platform/README.md`, `docs/architecture.md` and
  `docs/contract-compatibility.md` only to record factual implemented bytes.

The Row2 `kuksa-databroker_git.bbappend` and patch are frozen predecessor
bytes. Factory integration configures the effective KUKSA command only through
its package-owned drop-in and never edits that bbappend, patch, `SRCREV`,
upstream source, package name or baked upstream fixture. Service Manager
remains the sole package owner of `/etc/aos/resources.cfg`; `aos-deprov`
remains sole owner of `/opt/aos/deprovision.sh`. Any ownership collision,
unlisted path or need for a wildcard stops before edit.

## Exact Package and systemd Contract

### Packages and installed ownership

1. `aos-kuksa-auth-compat` becomes version `0.2.0` but remains one
   independently removable `${PN}`. It contains exactly three executables —
   the existing Service daemon, existing verifier preparer and new Provider
   preparer — their three units and the existing tmpfiles fixture. No Provider
   subpackage, Provider API or second crypto stack is introduced. Its exact
   runtime dependencies remain `openssl pkcs11-provider softhsm`.
2. `aos-kuksa-factory-integration` version `0.1.0` contains the token-init and
   cleanup executables, substrate/reset/token-init/cleanup units, four drop-ins
   and no secret. Its exact runtime dependencies are
   `aos-deprov aos-iamanager aos-kuksa-auth-compat aos-servicemanager
   aos-vehicle-data-provider-platform kuksa-databroker softhsm`. Its build
   dependency is `softhsm`; adding another crypto/HSM implementation stops.
3. The existing `aos-servicemanager` package remains sole owner of
   `/etc/aos/resources.cfg`; `aos-deprov` remains sole owner of
   `/opt/aos/deprovision.sh`; the Factory package owns only its executable,
   units and drop-ins. Package manifests must show no duplicate installed path.
4. `aos-image-vm.bbappend` appends exactly
   `aos-kuksa-auth-compat aos-kuksa-factory-integration` once. KUKSA, IAM,
   deprovision, Service Manager and VDP platform packages arrive through their
   existing image/dependency graph. No KAC/Provider payload enters a VDP FOTA
   or Service SOTA artifact.

### Exact Provider JWT serialization

The compact UTF-8 header is exactly:

```json
{"alg":"RS256","typ":"JWT"}
```

The compact UTF-8 payload uses exactly this member order and no whitespace or
additional member:

```text
{"sub":"aos-vdp","iss":"aosedge-vdp-provider","aud":["kuksa.val"],"iat":<SIGNED_INTEGER_UTC_SECONDS>,"exp":<IAT_PLUS_604800>,"scope":"<EXACT_SCOPE_BELOW>"}
```

`Base64Url` uses the URL alphabet with no padding. The signed bytes are the
ASCII bytes `base64url(header) + "." + base64url(payload)`. The signature is
RSA-2048 PKCS#1 v1.5 with SHA-256 through the existing Unit-local
`pkcs11:token=aos-kuksa;object=kuksa-jwt;type=private` operation. The third JWT
segment is unpadded Base64URL. The complete JWT must be non-empty and at most
16 KiB.

The exact 27-entry, ASCII-lexicographically sorted, single-space-delimited
scope string is:

```text
provide:Vehicle.Acceleration.Lateral provide:Vehicle.Acceleration.Longitudinal provide:Vehicle.Acceleration.Vertical provide:Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LateralSlipAngle provide:Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LongitudinalSlip provide:Vehicle.CarlaSimulation.ChaosWheel.Row1.Right.LateralSlipAngle provide:Vehicle.CarlaSimulation.ChaosWheel.Row1.Right.LongitudinalSlip provide:Vehicle.CarlaSimulation.ChaosWheel.Row2.Left.LateralSlipAngle provide:Vehicle.CarlaSimulation.ChaosWheel.Row2.Left.LongitudinalSlip provide:Vehicle.CarlaSimulation.ChaosWheel.Row2.Right.LateralSlipAngle provide:Vehicle.CarlaSimulation.ChaosWheel.Row2.Right.LongitudinalSlip provide:Vehicle.Chassis.Accelerator.PedalPosition provide:Vehicle.Chassis.Axle.Row1.SteeringAngle provide:Vehicle.Chassis.Axle.Row1.Wheel.Left.AngularSpeed provide:Vehicle.Chassis.Axle.Row1.Wheel.Left.Speed provide:Vehicle.Chassis.Axle.Row1.Wheel.Right.AngularSpeed provide:Vehicle.Chassis.Axle.Row1.Wheel.Right.Speed provide:Vehicle.Chassis.Axle.Row2.Wheel.Left.AngularSpeed provide:Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed provide:Vehicle.Chassis.Axle.Row2.Wheel.Right.AngularSpeed provide:Vehicle.Chassis.Axle.Row2.Wheel.Right.Speed provide:Vehicle.Chassis.Brake.PedalPosition provide:Vehicle.OEM.BrakeHealth.Advisory.GatewayStatus provide:Vehicle.OEM.TireHealth.Advisory.GatewayStatus provide:Vehicle.Speed read:Vehicle.OEM.BrakeHealth.Advisory.Request read:Vehicle.OEM.TireHealth.Advisory.Request
```

The one-shot first validates the fixed source path without following a symlink.
A regular root-owned mode-`0600` token is reusable only when its signature,
exact header, exact payload-member set/order, fixed strings, 27-entry scope,
integer times, `exp == iat + 604800`, `iat <= trusted_now + 5` and
`exp > trusted_now` all pass. A missing file or an otherwise exact, correctly
signed expired token is replaced. Malformed encoding/JSON, wrong signature,
mode/owner, claim, order, scope, future `iat`, duration or extra member fails
closed and is not silently overwritten.

Creation uses the fixed parent directory already owned and prepared by the VDP
platform package. It opens that directory without following symlinks, writes
only `.kuksa-token.tmp` with `O_CREAT|O_EXCL|O_NOFOLLOW`, root ownership and
mode `0600`, syncs the complete bytes, atomically renames it to `kuksa-token`
and syncs the parent directory. A stale temporary path is removed only after
proving it is a root-owned regular file in that exact directory. Failure before
rename preserves the prior valid token and exposes no partial destination.

### Exact finite systemd graph

| Unit/drop-in | Frozen behavior and ordering |
| --- | --- |
| `aos-kuksa-provision-reset.service` | Static root/networkless oneshot, `ConditionPathExists=!/var/aos/.provisionstate`; executes the existing full `/opt/aos/deprovision.sh` before token init, exactly replacing the upstream provisioning IAM `ExecStartPre` placement without changing its behavior. |
| `aos-kuksa-token-init.service` | Static root/networkless oneshot, required by both IAM modes; `Requires/After=aos-kuksa-provision-reset.service`, `Before=aos-iam-prov.service aos-iam.service`, `TimeoutStartSec=10s`, `RemainAfterExit=yes`. It validates an existing unique `aos-kuksa` token plus private mode-`0600` PIN or, only when both are absent after the reset prerequisite, creates them through native PKCS#11 and kernel randomness. Any absent/present mismatch, duplicate/ambiguous token, wrong owner/mode or failed initialization stops; it never repairs by deleting live state. |
| `aos-iam-prov.service.d/20-kuksa-token-init.conf` | Clears the original `ExecStartPre` list, requires/starts after reset and token init, and leaves the original `ExecStart`, condition, restart and provisioning result semantics unchanged. |
| `aos-iam.service.d/20-kuksa-token-init.conf` | Requires/starts after token init and otherwise leaves the normal IAM unit unchanged. A downstream KUKSA failure never rolls back successful provisioning. |
| `aos-kuksa-substrate.target` | Enabled only as `WantedBy=aos.target`; wants verifier, KUKSA, Provider and Service KAC. It contains no executable logic. Consumers use `PartOf=` so an explicit substrate/`aos.target` stop stops them, while ordinary shutdown does not invoke persistent cleanup. |
| `aos-kuksa-verifier-prepare.service` | Moves from `multi-user.target` to the substrate target; `PartOf` substrate, `Requires/After=aos-iam.service`, `Before` KUKSA/Provider/KAC, and conditions on provision state and the PIN. Existing root/networkless process, credential ID, atomic verifier and sandbox remain unchanged. |
| `kuksa-databroker.service.d/20-kuksa-verifier.conf` | `PartOf` substrate; `Requires/After` verifier; conditions on provision state and the exact verifier. Clears the inherited `EnvironmentFile`, then sets only `EXTRA_ARGS=--vss /usr/share/vss/vss.json --tls-cert /etc/kuksa-val/Server.pem --tls-private-key /etc/kuksa-val/Server.key --jwt-public-key=/run/aos-kuksa-verifier/kuksa-jwt-public.pem --address=0.0.0.0`. The inherited `ExecStart=/usr/bin/databroker $EXTRA_ARGS` and restart policy remain. The baked `/etc/kuksa-val/jwt.key.pub` is absent from the effective command. |
| `aos-kuksa-provider-prepare.service` | Wanted by/`PartOf` substrate; `Requires/After` verifier and VDP store bootstrap; `Wants/After=systemd-time-wait-sync.service`; conditions on provision state, PIN, verifier and mounted credential directory; `Before=aos-vehicle-data-provider.service`; root, `Type=oneshot`, `RemainAfterExit=yes`, `Restart=no`, `JobTimeoutSec=45s`, `TimeoutStartSec=15s`, `LoadCredential=kuksa-jwt-pin:/var/aos/iam/.kuksa-jwt-pin`, `UMask=0077`, no IP access and write access only to the exact credential directory. It runs once per boot/target activation and does not poll. |
| `aos-kuksa-auth-compat.service` | Moves from `multi-user.target` to substrate; `PartOf` substrate; keeps the existing Service-only process/API/sandbox, verifier dependency and `After=systemd-time-wait-sync.service`, and adds only the provision-state condition. It does not pull a new time-wait job and retains the existing in-process `TIME_UNTRUSTED` readiness result; it has no Provider dependency. |
| `aos-vehicle-data-provider.service.d/20-kuksa-provider.conf` | `PartOf` substrate; adds `Requires/After=aos-kuksa-provider-prepare.service kuksa-databroker.service` and a condition on the exact token source. It does not enable VDP; Service Manager retains activation ownership. |
| `aos-kuksa-runtime-cleanup.service` | Static root/networkless oneshot invoked only by the accepted deprovision override, never by ordinary shutdown/reboot. After consumers stop it removes only the fixed Provider JWT, `.kuksa-token.tmp`, volatile verifier and KAC socket/runtime paths, then syncs persistent token-directory metadata. It never removes the PIN, PKCS#11 token/key, VDP component slots/configuration/trust/state or any Service data. |

An existing valid token is therefore reused on ordinary reboot. Missing or
expired token causes the boot one-shot to prepare one before VDP connects. If
expiry occurs after an established connection, there is no in-process VDP
timer or instant-revocation claim: the next authenticated operation/reconnect
is rejected by KUKSA. Recovery is an explicit controlled restart of
`aos-kuksa-provider-prepare.service`, followed by a restart of
`aos-vehicle-data-provider.service` so systemd supplies a new private
credential snapshot. No automatic restart loop, renewal daemon or polling
path may perform this recovery.

### SELinux domains and filesystem authority

- extend the existing module with new networkless
  `aos_kuksa_provider_prepare_t` entered only by
  `/usr/libexec/aos-kuksa-provider-prepare`;
- add separate networkless `aos_kuksa_token_init_t` and
  `aos_kuksa_runtime_cleanup_t` domains for their exact executables;
- label the exact PIN, Provider credential and Provider temporary file with
  dedicated types. Provider may read/lock the existing PKCS#11 store and its
  private systemd credential and create/replace only the two fixed credential
  filenames. It cannot connect to IAM/KAC/Cloud, manage the KAC socket, read
  Service tmpfs or create/delete/rename PKCS#11 objects;
- token init alone may initialize the fixed SoftHSM token and create/validate
  the exact PIN. It has no KAC socket, IAM network, Provider-token or Service
  tmpfs access; and
- cleanup may unlink only the exact Provider/verifier/socket runtime labels.
  It has no PKCS#11/PIN read or write authority.

Gate 1 must resolve the already-installed parent-directory type names from the
pinned policy before writing the `.te` rules. The three new process domains,
path labels and allowlist above are frozen; a missing parent-type interface or
policy compile error stops rather than granting a generic `var_t`, broad
`vehicle_data_provider_store_t`, network, `dac_override`, `sys_admin` or
`audit2allow`-generated permission.

Failure remains dependency-local: verifier failure blocks KUKSA and both JWT
consumers; Provider failure blocks VDP only; KAC failure blocks new/renewed
Service credentials only. Unrelated AosCore and non-KUKSA Services remain
operable.

## Collision and Fan-In Contract

| Shared surface | Gate 1 rule | Later fan-in rule |
| --- | --- | --- |
| Row2 KUKSA bbappend/patch | Read-only predecessor bytes; no Factory edit. | Preserve the qualified patch, package identity and digest. |
| `/etc/aos/resources.cfg` | One product override under the existing Service Manager recipe; no Factory-package copy. | Keep Service Manager as sole owner and merge only complete JSON entries. |
| IAM `iam.cfg` | Deterministic transform preserves all input modules and asserts exact resulting `kuksa-jwt` plus `enablePermissionsHandler: true`. | Re-run the transform after the Permission Handler branch is combined; byte-order differences are allowed only if semantic canonical validation is identical. |
| `aos-image-vm.bbappend` | Append only the two package names. | Fan-in deduplicates whitespace/list entries and proves each exact package once. |
| refpolicy bbappend | Add only named module files. | Fan-in compiles the union; never replace a domain with broader shared allow rules. |
| VDP package/service | Factory owns only a separately named drop-in and dependency; no VDP source/recipe/service-file edit. | Preserve Service Manager activation and the VDP checkpoint; effective-unit inspection must include the drop-in. |
| deprovision script | `aos-deprov` owner override adds only fixed cleanup invocations and pins the upstream preimage hash. | Any other script edit requires an explicit three-way semantic review; no last-writer-wins copy. |
| Runtime/Safe Stop, Brake, Tire, UI | No changed path. | Imported only by their owning later checkpoints. |

At Gate 1 start and Gate 4 handoff, the changed-path audit, `oe-pkgdata-util`
ownership result and effective systemd/IAM/resource hashes are recorded. A
collision is a stop condition, not permission to modify another packet.

## Execution Gates

### Gate 0 — completed pinned-source evidence assessment

**Result:** `PROVED — G0-03 CLOSED BY EXACT QUALIFIED ROW2 PREDECESSOR`.

The read-only export is
`/private/tmp/kac-factory-gate0-evidence-20260829`; its manifest SHA-256 is
`57ecc8a6f2147eeb9ec3b6cbfc39e05dd8602dc32e82b5bc79f915dbfc7b98f4`
and its proven/unresolved matrix SHA-256 is
`6044ae1d112e3302adb337f8f395e6d18445d0672f2e36d5b02a3964b92cec09`.
All pinned revisions/trees match the Frozen Inputs. The assessment performed no
product/solution/source mutation, network access, build, compile, install,
signing, Cloud or live-VM operation; its disposable Builder COW used explicit
read-only originals/backings. The secret scan found no key, PIN, JWT,
certificate, credential assignment or signing material.

| Item | Completed result | Factual packet consequence |
| --- | --- | --- |
| `G0-01` named-resource schema | `PROVED` | `ResourceInfo` consumes a top-level JSON array. Field matching covers case-insensitive `name`, `sharedCount`, `groups`, `mounts`, `envs`, `hosts` and `devices`; pinned parser/types/tests and an accepted fixture are hash-matched. |
| `G0-02` resource ownership | `PROVED — BOUNDARY CORRECTED` | `meta-aos-vm-common/recipes-aos/aos-servicemanager/aos-servicemanager_git.bbappend` owns installation of `/etc/aos/resources.cfg`. The product's existing `meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/aos-servicemanager_git.bbappend` already prepends `files/`; therefore only its new `files/resources.cfg` override may extend the resource. Factory integration must never introduce a second owner. |
| `G0-03` KUKSA package/JWT parser | `PROVED BY PREDECESSOR` | Baseline package/unit ownership, `RS256`, array `aud`, required `kuksa.val`, whitespace-delimited scope and expiry validation remain unchanged. Exact commit `405546b...` changes only the accepted digit class and focused tests: first/repeat ARM64 `17/17`, host `50/50`; patched source, binary and normalized package-content hashes are frozen above. `PN/PV/PR/PACKAGE_ARCH` remain `kuksa-databroker/git/r0/cortexa57`. |
| `G0-04` one-package seam | `CURRENT SEAM PROVED; GATE 1 ADDITION` | The existing KAC source/recipe/executables/units and hashes are proved. The Provider executable/unit do not yet exist; their strict additive same-package implementation and no-KAC-API negatives are Gate 1/Gate 2 requirements, not pre-existing Gate 0 facts. |
| `G0-05` token/key bootstrap | `PROVED` | Pinned certificate-module plus SoftHSM/PKCS#11 seams support a distinct token, generated mode-`0600` PIN file, RSA/EC creation/lookup and object clearing without exposing private-key bytes. |
| `G0-06` native lifecycle hook | `PROVED` | `FinishProvisioning` invokes `/opt/aos/provfinish.sh`, persists `/var/aos/.provisionstate` and restarts `aos.target`. Async deprovision stops current target wants, removes provision state and restarts the target; it does not clear IAM/HSM storage, so full deprovision and R0 remain distinct. |
| `G0-07` systemd/readiness graph | `CURRENT SEAMS PROVED; GATE 1/2 REQUIREMENT` | Existing verifier/KAC units, KUKSA unit/defaults, VDP credential consumption, pre-operation authentication, reconnect behavior, finite VDP startup timeout and absence of a VDP JWT parser/timer are proved. Token-init, Provider, cleanup and KUKSA-verifier drop-in units do not exist yet; their exact finite graph is implemented in Gate 1 and qualified in Gate 2, not falsely source-proved at Gate 0. |
| `G0-08` credential ownership/teardown | `CURRENT CONSUMERS PROVED; GATE 1/2 REQUIREMENT` | KAC/verifier consume `kuksa-jwt-pin` from `/var/aos/iam/.kuksa-jwt-pin`; verifier atomically publishes `/run/aos-kuksa-verifier/kuksa-jwt-public.pem` mode `0444`; VDP consumes `kuksa-token` from `/var/aos/workdirs/sm/runtimes/systemd-slot-component/credentials/kuksa-token`. The PIN/JWT producers and immediate cleanup unit do not exist yet and must be implemented/tested in Gate 1/2. |
| `G0-09` collision audit | `DESIGN BOUNDARY FIXED; REPEAT AFTER GATE 1` | Service Manager remains the sole `resources.cfg` owner; KAC Provider additions remain additive; IAM transformation collision with Permission Handler stays deferred to successor fan-in. Exact changed-path/package/policy collision checks repeat on implemented bytes. |

In particular, the authorized checkpoint still starts KUKSA with the baked
verifier path, and the current KAC/verifier units are
`WantedBy=multi-user.target`. No token-init, Provider, immediate-cleanup or
KUKSA-verifier drop-in unit exists. These are implementation gaps, not missing
Gate 0 source evidence, and may be closed only inside the later authorized
Gate 1 boundary.

The FI-03 expiry correction is source-compatible: VDP reads its private systemd
credential when opening the KUKSA client, KUKSA validates JWT metadata on
authenticated operations, and no VDP JWT parser/timer is required. There is no
instant in-session revocation claim. After controlled Provider re-preparation,
VDP must restart, not merely reconnect, because systemd credentials are a
per-service-start private snapshot.

Gate 0 no longer requires hashes for not-yet-created token-init, Provider or
cleanup units. Their required behavior is the accepted design input to Gate 1,
and their installed/effective graph, ownership and teardown are Gate 2 plus
later disposable-VM evidence.

The prior G0-03 blocker is closed. The exact Row2 commit/tree, unchanged
package identity/architecture, grammar, all 27 FI-02 entries, negatives and
first/repeat installed-content proof are frozen. `package_write_rpm` was not
performed, so no patched archive is claimed or required as a source Gate 1
input. G0-01, G0-02, G0-05 and G0-06 remain valid because all other pinned
identities are unchanged. Gate 0 proof authorizes no Factory product edit,
build, signing or live action by itself.

### Gate 1 — bounded implementation

Before the first edit, independently re-read the frozen Row2 commit/tree and
post-completion evidence manifest, prove the isolated Factory worktree starts
clean at that exact HEAD, and reject the unpatched baseline RPM. Then implement
only the frozen path list and
exact contracts above. A patched archive is intentionally not a Gate 1 input;
it is created only by Gate 3 under the consolidated Platform Train
authorization.

The first implementation step creates pure fakes for clock, signer, PKCS#11
slot/token operations and fixed-root filesystem access. No product-local test
may invoke a real Unit key, real HSM token, real PIN/token, live systemd, VM,
network or Cloud. Provider construction, existing-token classification,
atomic replacement, token-init state machine and cleanup path selection must
be independently testable before unit/recipe wiring is added.

The implementation must keep three process entry points and three authority
boundaries explicit in source and package inventories: Service KAC, Provider
preparer and Factory token-init/cleanup. No reusable general JWT CLI,
caller-supplied claim/path/time/output parameter, environment override or
configuration file is added.

### Gate 2 — product-local and contract gates

Required passes:

- **Provider source tests:** exact compact header/payload/member order, all 27
  entries, exact `sub`/`iss`/array `aud`, integer `iat`, seven-day duration,
  RS256 signing input and output; valid reuse; missing/expired replacement;
  future time, extra/missing/reordered claim, wrong key/signature, malformed
  Base64URL/JSON, wildcard, `create`, `actuate`, duplicate, unsorted scope,
  size, owner/mode, symlink, non-regular destination, stale-temp and every
  write/sync/rename failure negative; old valid destination remains byte-exact
  on pre-rename failure;
- **same-package separation:** installed inventory has three executables but
  one `${PN}`; Provider dynamic-link/import/callgraph and socket-protocol tests
  prove no gRPC/IAM/KAC server/dispatch surface, no caller input and no network
  listener; existing KAC tests pass unchanged;
- **token-init/cleanup tests:** absent/absent creation, present/present exact
  validation, idempotent reboot, absent/present mismatch, duplicate/ambiguous
  token, wrong PIN/mode/owner, PKCS#11 partial/failure and kernel-random failure
  all fail closed without broad deletion; cleanup exact-positive and traversal,
  symlink, alternate-root, key/PIN/slot/config/state deletion negatives;
- **resource tests:** parse the complete two-entry JSON with pinned AosCore;
  prove exact count/name/share/group/source/destination/options and effective
  read-only bind plus 64-KiB private tmpfs for four isolated consumers; reject
  changed host path, writable bind, missing security option, environment,
  secret, fifth allocation, cross-container visibility and a second package
  owner;
- **IAM tests:** preserve every input byte semantically, require handler true,
  add exactly the frozen module and reject false/absent handler, duplicate ID,
  wrong RSA/token/PIN/library/maxItems/selfSigned/member or changed existing
  module; prove no PIN/key/JWT is in the output;
- **systemd tests:** `systemd-analyze verify` the staged root and inspect the
  effective graph for unprovisioned reset -> token-init -> provisioning IAM,
  provisioned normal IAM -> verifier -> KUKSA plus independent Provider/KAC,
  VDP wait, valid reboot reuse, missing/expired boot preparation, Provider-only
  failure, common verifier failure, explicit re-preparation + VDP restart and
  async deprovision cleanup. Prove no `.path`, timer, watcher, renewal/restart
  loop or cleanup-on-ordinary-shutdown; every one-shot timeout is finite;
- **deprovision/reboot tests:** preimage-hash and exact-delta check the owner
  override, prove cleanup executes after consumer stop and before state removal
  for async deprovision and before full clear, while an ordinary reboot never
  invokes the persistent cleanup path and therefore reuses an unexpired JWT;
- **KUKSA/Row2 tests:** execute the predecessor's focused Rust tests and parse
  the exact 27 scopes; prove the effective KUKSA command contains the volatile
  verifier exactly once, contains no baked verifier, and authorization cannot
  start with missing/malformed verifier;
- **SELinux tests:** compile both modules and use `sesearch`/negative fixtures
  to prove the three separate process domains, exact entry transitions and
  file types; Provider has no network/IAM/KAC-socket/PKCS11-object-management
  permission, token init has no network/Provider/KAC access, and cleanup has no
  PIN/key/store access. No generic store/`var_t`, capability or automatic
  `audit2allow` widening passes;
- **package/composition tests:** exact `RDEPENDS`, files/users/groups/modes,
  static/enablement state, two image additions, one owner for each shared path,
  no Provider subpackage, no secret and no payload in VDP FOTA/Service SOTA;
  inspect dependency graphs without building an image; and
- complete existing KAC, R6.1 layer and dependency-inventory suites plus
  `tools/quality_gate.py`, REUSE/SPDX, secret-negative scan, changed-path
  audit and `git diff --check`.

### Gate 3 — pinned offline package proof; no image

Under the consolidated Platform Train authorization, use the existing verified
Builder/cache with `BB_NO_NETWORK=1` to compile/test/package the updated KAC
compatibility package, the new Factory-integration package and exact affected
`aos-iamanager`, `aos-servicemanager`, `aos-deprov` and `refpolicy-aos`
recipes. Run `do_package_qa`,
inspect files/modes/users/groups/dependencies/systemd/SELinux and repeat a
forced-clean cycle. `bitbake -e`/dependency-graph inspection may prove image
selection, but `aos-image-vm`, any rootfs/image task and every VM operation are
forbidden.

Real PKCS#11 creation/signing, real provisioning triggers, KUKSA loading,
cross-Unit rejection, reboot/deprovision and VDP readiness belong to the later
disposable-VM qualification packet.

### Gate 4 — reviewable checkpoint

After every gate passes, create one local Factory commit on the isolated
branch with the exact source tree, package inventories,
dependency/configuration hashes,
test counts and all deferred real-Unit cases. Push, merge, rebase and `main`
mutation remain forbidden.

## Stop Conditions

Stop without broadening or patching if:

- FI-01, FI-02 or FI-03 is not accepted;
- the separate KUKSA parser predecessor is absent, differs from its bounded
  accepted grammar/test scope or lacks a committed/qualified identity and
  focused G0-03 proof;
- product or solution inputs differ from the frozen identities;
- pinned source does not prove the exact resource/provisioning/KUKSA seam;
- this Factory implementation would modify KAC business logic, upstream
  AosCore/KUKSA, Runtime Safe Stop, VDP source/recipe/owned service file or
  either Service artifact; the separately owned VDP drop-in above is the only
  permitted VDP dependency wiring, and the accepted KUKSA parser change belongs
  only to its separate predecessor;
- implementation would add a VDP JWT parser/expiry timer or present
  next-reconnect expiry enforcement as exact in-session or production-grade
  revocation;
- a file ownership collision, unknown package name or guessed JSON/systemd/CLI
  contract remains;
- token initialization requires shared `.usrpin`, a baked/default PIN,
  command-line/environment PIN delivery, create/delete/rename authority in the
  KAC or Provider domains, or authority broader than the separately reviewed
  one-shot `aos_kuksa_token_init_t` boundary;
- Provider issuance requires IAM, Cloud, KAC socket, caller input, a polling or
  background renewal daemon, wildcard, `create` or `actuate` authority;
- ordinary reboot would invoke persistent cleanup, a deprovision hook could
  remove the PIN/key, or expired-token recovery could occur without an
  explicit Provider-one-shot plus VDP restart;
- a real private key, PIN, JWT, certificate, Unit identity or secret is read,
  generated, copied or printed;
- work requires network, image/rootfs build, VM/Unit, provisioning, signing,
  FOTA, Cloud, live qualification, push or merge; or
- any gate fails or the frozen writable boundary is insufficient.

## Review Result Required

FI-01 through FI-03 are accepted and Gate 0 is proved, including G0-03 through
the exact qualified Row2 predecessor. G0-07 and G0-08 are not false
pre-implementation proof requirements: their missing producers/units/cleanup
are explicit Gate 1 deliverables and Gate 2 qualification targets.

The architecture and Gate 1/Gate 2 contract are now implementation-review
ready. There is no additional open user design decision beyond the already
accepted FI-01 through FI-03. Resolving pinned SELinux parent type names and
checking the exact deprovision preimage are implementation verifications with
stop-on-mismatch behavior, not choices to broaden authority.

This packet is `AUTHORIZED AS PLATFORM TRAIN STAGE — IN PROGRESS`. The exact
Row2 commit/tree, package name/version/architecture, patched source, binary and
normalized installed-package-content hashes, test counts and independently
verified post-completion retrieval manifest are frozen. The absence of a
patched RPM is explicit; the unpatched baseline RPM is forbidden and no
filename/hash is invented.

There is no remaining architecture/user decision in this packet. The operator
authorized Gate 1, the exact offline package proof and one local Factory
checkpoint on 2026-08-29 as part of the consolidated Platform Train. Image,
VM, provisioning and the narrowly bounded AosCloud-online confirmation are
owned only by later umbrella stages; they are not actions of this Factory
packet. Real PKCS#11 signing, dependency acquisition, unrelated network or
Cloud access, push, merge and `main` mutation remain forbidden here.
