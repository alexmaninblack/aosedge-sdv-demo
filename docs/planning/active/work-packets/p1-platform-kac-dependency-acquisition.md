<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KAC Dependency Acquisition Work Packet

- ID: `WP-DEP-P1-PLATFORM-KAC-001`
- Lane: `L-PLATFORM-DEPENDENCIES`
- Increment: `IMP-03-KAC-DEPENDENCIES`
- State: `GATE A COMPLETED — GATE B REVIEW REQUIRED`
- Prepared: 2026-08-28
- Gate A accepted and completed: 2026-08-29
- Product repositories: read-only
- Product implementation, compile, image build and live operation authorized:
  no

## Outcome

Resolve and freeze the exact Yocto-native and target dependency set required
to compile `WP-P1-PLATFORM-KAC-001`. The acquisition is evidence-only: it may
fetch exact source metadata and license material into a private local cache,
but it may not edit product repositories, compile KAC, install host packages
or build an image.

The packet exists because the accepted KAC source packet correctly excludes
dependency download, while the present workspace has no complete pinned C++
gRPC/Protobuf, SoftHSM and OpenSSL PKCS#11-provider build set.

## Validated API Baseline

| Input | Exact identity |
| --- | --- |
| AosCore API | `AosEdge/aos_core_api@af3552a0a5eb0237eff7f5f183780ca46c339cd3` (`v9.1.0`) |
| IAM protocol | `proto/iamanager/v6/iamanager.proto` |
| Common protocol | `proto/common/v2/common.proto` |
| Server reference | `AosEdge/aos_core_cpp@9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` |
| Library reference | `AosEdge/aos_core_lib_cpp@60cb83535f773762c61ac5f544b31b7b88c502e3` |
| Required RPC | `/iamanager.v6.IAMPublicPermissionsService/GetPermissions` |
| Fixed request resource | `functional_server_id = "kuksa"` |

The native v6 namespace is the IAM protocol version; it must not be presented
as the AosCore release number. KAC generates C++/gRPC sources from the pinned
proto inputs using matching Yocto `protobuf-native` and `grpc-native`. It does
not link AosCore C++, use Python gRPC/Protobuf or reuse the Aos secret-logging
wrapper.

## Frozen Metadata Sources

| Source | Revision |
| --- | --- |
| Poky | `7d50718f90c51fb7f650c9db59b28c6e0194e5d2` |
| meta-openembedded | `ec0469748be4159fb83fb0fa0148d786484c88cf` |
| meta-virtualization | `3dd635f613f7299d986a8ab6bc9f584370f8ed1d` |
| meta-security | `97e482b71688b62ac1109d16e89368122f039cbf` |
| meta-selinux | `536df5a4fbce3c9fd63f51580f43d248a0d1b0ef` |
| meta-arm | `c4fd56386ee30f8b46f8e4eb1220edaf510d2ac0` |
| meta-aos | `176da6346b1199f854106dede4cc49604174619c` |
| meta-aos-vm | `b13320898a2ed1cce504f90f70451638232d6a83` |
| aos_core_api | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` |
| aos_core_cpp | `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` |
| aos_core_lib_cpp | `60cb83535f773762c61ac5f544b31b7b88c502e3` |
| AosEdge refpolicy | `c8be82c7e62f69cb6530de8cc1da3beb389a6681` |

## Private Local Boundary

If accepted, the packet may write only below:

```text
/home/yocto/.dependency-cache/wp-p1-platform-kac-001/
```

with separate `src`, `yocto/downloads`, `yocto/sstate-cache`, `yocto/tmp` and
`evidence` directories, mode-protected for the current user. The cache is not
Git-managed and must contain no key, PIN, certificate, token or Unit identity.
All source and product repositories remain read-only.

## Gate A — Metadata Resolution and Provisional Lock

1. Inspect the existing pinned Builder cache offline first. Reuse an existing
   input only after proving its exact identity against this packet; never treat
   cache presence as revision or license evidence.
2. Materialize each metadata source at the exact revision above into the new
   empty private `src` path, preferring a verified local source and using the
   network only for an exact missing revision. Verify every resulting `HEAD`.
3. Resolve the exact BitBake selections for `grpc`, `grpc-native`, `protobuf`,
   `protobuf-native`, `openssl`, `softhsm` and `pkcs11-provider` without
   overriding layer priority or recipe selection.
4. Record recipe file, effective layer priority, `PV`, `PR`, `SRC_URI`,
   `SRCREV`, every source checksum, `LICENSE`, `LIC_FILES_CHKSUM`, package
   splits, target/compiler tuple, generator identity and native/target pairing.
5. Prove from the selected metadata and source-install contract that the
   target packages own `/usr/lib/ossl-modules/pkcs11.so` and
   `/usr/lib/softhsm/libsofthsm2.so`, or stop.
6. Produce a provisional dependency lock and stop for separate review. Gate A
   does not authorize recipe payload fetch beyond the exact metadata needed to
   create that lock.

## Gate B — Exact Fetch and Offline Evidence

Gate B begins only after the Gate A provisional lock has been reviewed and
explicitly accepted.

1. Fetch exactly the source and license payloads enumerated by the accepted
   lock into the dedicated `yocto/downloads` path.
2. Verify every source identity, archive checksum and license checksum against
   the accepted lock.
3. Repeat the exact fetch task with `BB_NO_NETWORK=1`; any missing or changed
   input fails the gate.
4. Produce an evidence report, cache inventory and proposed governance delta
   for `DEPENDENCIES.json` and `THIRD_PARTY_NOTICES.md`; do not apply that delta
   in this packet.

Neither gate authorizes KAC or dependency compilation, host or target package
installation, product-repository edits, artifact or image construction, or any
VM, Unit, provisioning, signing, FOTA or live operation beyond the separately
accepted isolated Builder execution needed for this evidence-only packet.

## Stop Conditions

Stop without substituting or guessing if:

- a recipe is missing, ambiguous, `AUTOREV`/`AUTOINC`, or lacks source/license
  verification;
- native and target Protobuf/gRPC selections are incompatible;
- the PKCS#11 implementation is not the official OpenSSL
  `pkcs11-provider`, or its exact source/version/license cannot be proved;
- either accepted target module path cannot be established;
- a product repository edit, compile, package install or wider network source
  is required; or
- any credential or secret is encountered.

## Gate A Completion Record

- Dedicated cache:
  `/home/yocto/.dependency-cache/wp-p1-platform-kac-001`
- Provisional lock:
  `evidence/provisional-dependency-lock.json`
- Provisional lock SHA-256:
  `92714c3fb020c7e3975c54618887b35c82ce9b6d8bc55abd3148aa96aa5f06a4`
- Evidence summary SHA-256:
  `e759ce570d79215573e93c44ede61fc0248be55d8d1ea9811057c86c55dffa80`
- Evidence manifest SHA-256:
  `be84c425488eb3852688cfe7d0a8d11fef3369fbeb1b99ec06038d2dba7259d1`

Gate A resolved the exact native/target recipe selections under
`BB_NO_NETWORK=1`: gRPC 1.60.1, Protobuf 4.25.8, OpenSSL 3.2.6, SoftHSM 2.6.1
and the official `pkcs11-provider` 1.0. The frozen lock includes their exact
Git/archive identities, submodule closures, recipe metadata and hashes. It
proves ownership of `/usr/lib/ossl-modules/pkcs11.so` and
`/usr/lib/softhsm/libsofthsm2.so` for the selected target composition.

The only network metadata acquisitions were the two exact frozen revisions
`aos_core_api@af3552a0a5eb0237eff7f5f183780ca46c339cd3` and
`aos_core_lib_cpp@60cb83535f773762c61ac5f544b31b7b88c502e3`. Every other
input came from a verified local checkout or cache. Dedicated Gate B downloads
and sstate remain empty. The Builder and its DNS bridge were stopped cleanly.
No compile, install, product or documentation edit, artifact/image build or
live operation occurred.

The completion record for the whole packet still requires Gate B exact
source/license payload verification, offline refetch evidence, cache inventory
and proposed governance entries. Gate A completion authorizes neither KAC
compilation nor dependency inclusion in a Factory Image.

## Authorization Gate

The operator accepted Gate A on 2026-08-29, and it completed with the evidence
above. Gate B exact payload fetch still requires separate acceptance of the
provisional lock. No later compile, install, product edit, artifact/image build
or live operation is authorized by that acceptance.
