<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KAC Source, Recipe and Compile Integration Work Packet

- ID: `WP-P1-PLATFORM-KAC-COMPILE-INTEGRATION-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-KAC-COMPILE`
- State: `COMPLETED IN PLATFORM TRAIN — HISTORICAL PACKET / NO RESIDUAL AUTHORITY`
- Version: 0.1
- Prepared: 2026-08-29
- Product source, dependency compile, recipe/package tasks and commit
  authorized: no
- External network, image build, VM/Unit operation, provisioning, signing,
  FOTA, Cloud and live qualification authorized: no
- Parent source contract: [KAC implementation](p1-platform-kac.md)
- Completed dependency input:
  [KAC dependency acquisition](p1-platform-kac-dependency-acquisition.md)
- Later Factory composition:
  [KAC Factory integration](p1-platform-kac-factory-integration.md)
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)

## Completion Resolution

The accepted implementation was later integrated through product commit
`215bd29` and its successor Factory train, culminating in accepted source
`667afb1512cf43ff27f1ab5327293208bf73045b` and Factory image `.21`. The
authorization lines below describe this packet's original proposal boundary;
they grant no new product, Builder, VM or Cloud operation.

## Outcome

Implement the accepted removable KUKSA Authorization Compatibility helper,
its verifier-preparation executable and one separately installable Yocto
package, then compile, package and execute its bounded test suite against the
exact dependency set already frozen by Gate A and reproduced offline by Gate
B.

This packet closes only the KAC source, recipe, dependency-governance and
pinned compile/test gap. It does not add KAC to an image, define Aos named
resources, prepare the fixed OEM Provider credential, provision a Unit, test a
real PKCS#11 object or operate KUKSA/Aos IAM in a VM. Those remain later
Factory-image and disposable-VM/live qualification gates.

The packet is a proposal only. Its presence does not authorize a product edit,
Builder start, compile, package task, governance edit or commit.

## Frozen Inputs

| Input | Exact identity |
| --- | --- |
| Solution planning baseline | `aosedge-sdv-demo@bcc7975d4aa3e3ed3c6b617abcd47b6bb18c88fd` |
| Product base | `aos-vehicle-platform@bdc72aba97a83c9868d454588189ef139710a6d7` |
| Product base tree | clean `main == origin/main`; assessed 2026-08-29 |
| KAC requirements | `CR-KAC` 0.12, SHA-256 `ab0d6bf039d94d52b82ff77c6bcf74ffe397f9f2b6110f8be032ed07198c3e39` |
| Executable local protocol | `kuksa-auth-compat.v1.json` 1.7.0, SHA-256 `1ddd097976dc8606533307bf2f0f0619b166a295a38391e593340487b8d2931c` |
| Gate A provisional lock | SHA-256 `92714c3fb020c7e3975c54618887b35c82ce9b6d8bc55abd3148aa96aa5f06a4` |
| Gate B final report | SHA-256 `e4f692f9daa035123d92b6b488a1fb5730cbcd7656795e71f05d1370cbdbfb5d` |
| Gate B cache inventory | SHA-256 `06cd34677f999657129f6c8100533ff1ea583b04c5ea85a54d727b41e9832e16` |
| Gate B evidence manifest | SHA-256 `b3a56b470f0cd3a1e96ba6d1cbe5376cdbe59a67fb974c0e7eca25809bc63b72` |
| Builder image | Ubuntu 22.04 ARM64, SHA-256 `8f61e558498ba262da5b5d13f75b2921136b737a1492415150f33b3d0e46a281` |
| Target/toolchain | R6.1 `qemuarm64`, `aarch64-aos-linux`, GCC `13.4.0` |
| AosCore API | `af3552a0a5eb0237eff7f5f183780ca46c339cd3`, native IAM v6 and common v2 protos |
| AosCore C++ reference | `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d`, read-only reference only |
| AosCore C++ library reference | `60cb83535f773762c61ac5f544b31b7b88c502e3`, read-only reference only |

The exact layer revisions remain the completed dependency packet and accepted
R6.1 source lock. No branch, tag-only, host-library, Python gRPC/Protobuf or
newer recipe substitution is permitted.

### Frozen KAC dependency selection

| Selection | Version / revision | Canonical fetched payload SHA-256 | Recipe license |
| --- | --- | --- | --- |
| `grpc` / `grpc-native` | `1.60.1`, `e5ae3b6b44bf3b64d24bfb4b4f82556239b986db` | `cf83d37590a24bbc3439df4cb9ca1b2b84bcf3cb5941407cbc84a3a0de978432` | `Apache-2.0 & BSD-3-Clause & MPL-2.0` |
| `protobuf` / `protobuf-native` | `4.25.8`, `a4cbdd3ed0042e8f9b9c30e8b0634096d9532809` | `6ac659ddfda20f72c337f57de7d262bdda52808388ac155f917c42b1d64d29b9` | `BSD-3-Clause` |
| `openssl` | `3.2.6` | `89681a9ddaa9ed7cf25ea8ef61338db805200bae47d00510490623547380c148` | `Apache-2.0` |
| `softhsm` | `2.6.1` | `61249473054bcd1811519ef9a989a880a7bdcc36d317c9c25457fc614df475f2` | `BSD-2-Clause & ISC` |
| `pkcs11-provider` | recipe 1.0, `8f6b94409d4872265076df310492da1e5f6abdf7` | `a542545e196e60e466aefb0a45a3822e54c29210ab86808bc208d9d84968476f` | `Apache-2.0` |

The selected target composition owns
`/usr/lib/ossl-modules/pkcs11.so` and
`/usr/lib/softhsm/libsofthsm2.so`. The KAC signer must use token label
`aos-kuksa`, object `kuksa-jwt` and the distinct credential source
`/var/aos/iam/.kuksa-jwt-pin`; it must never use the AosCore `.usrpin`.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Branch | `codex/imp-03-kac` |
| Isolated worktree | `../aos-vehicle-platform-imp-03-kac` |
| Required initial HEAD | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Assessed state | clean, no KAC implementation commit |
| Dependency cache | `/home/yocto/.dependency-cache/wp-p1-platform-kac-001` |
| Proposed compile root | `/home/yocto/kac-compile-bdc72ab-e4f692f9` |

The worker must stop if the product branch is dirty, its initial HEAD differs,
or `main` and `origin/main` no longer equal the frozen base. It must not rebase
or merge the independent Factory/runtime or VDP branches. Their later fan-in
is owned by a separate integration gate.

Generated build output remains outside every Git repository. The compile root
may receive a verified copy of the Gate B downloads and metadata sources; it
must not modify the completed Gate A/B evidence directory.

## Proposed Writable Boundary

After separate acceptance, only these product paths may change:

- `authorization/aos-kuksa-compat/**` for C++17 source, private interfaces,
  pinned-protocol fixtures, CMake build files and package-owned unit tests;
- new
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/**` for the
  `aos-kuksa-auth-compat_0.1.0.bb` recipe, systemd units, tmpfiles and package
  files;
- KAC-only
  `meta-aos-vehicle-platform/recipes-security/refpolicy/files/aos_kuksa_auth_compat.fc`,
  `aos_kuksa_auth_compat.if` and `aos_kuksa_auth_compat.te`, plus only the
  corresponding source/install entries in
  `meta-aos-vehicle-platform/recipes-security/refpolicy/refpolicy-aos_git.bbappend`;
- new `tools/validate_kac.py` and `tests/test_kac.py`;
- `DEPENDENCIES.json` and `THIRD_PARTY_NOTICES.md` only for the reviewed Gate B
  dependency entries;
- `tools/quality_gate.py` plus a new `tests/test_dependency_inventory.py` only
  for the narrow dependency-schema corrections below; and
- `authorization/aos-kuksa-compat/README.md`,
  `meta-aos-vehicle-platform/README.md`, `docs/architecture.md` and
  `docs/contract-compatibility.md` only for factual implemented behavior.

Allowing `tools/quality_gate.py` is an explicit proposed expansion over the
earlier source packet. It is required because the current validator accepts
only one SPDX license identifier and a 40-hex Git revision, while the frozen
inputs include conjunction licenses and checksum-pinned source archives. No
other generic quality, provider, VDP, Runtime, image or packaging boundary may
change.

## Exact Source and Package Contract

### Product source

1. Implement one executable `/usr/libexec/aos-kuksa-auth-compat` and one short
   root executable `/usr/libexec/aos-kuksa-verifier-prepare` behind injectable
   IAM, signer and clock interfaces.
2. Generate only the required IAM v6/common v2 C++ and gRPC sources from
   `aos_core_api@af3552a0...` using the matched `protobuf-native` and
   `grpc-native` tools. Do not link AosCore C++, copy generated files into Git
   or use host/Python generators.
3. Implement the exact accepted request framing, native-IAM call, permission
   mapping, RS256 claims, time gates, operational limits, retry mapping and
   redacted diagnostics. Fixed resource `kuksa` and IAM loopback
   `127.0.0.1:8090` are not configurable by callers.
4. Keep the Provider credential, Service bootstrap, telemetry and KUKSA data
   path outside the source tree.

### Recipe and package

1. Create exactly recipe/package `aos-kuksa-auth-compat` version `0.1.0`.
   The main package contains both executables, their two systemd units and one
   tmpfiles file; no test binary, private header, source, key, PIN, token,
   certificate or generated verifier is packaged.
2. Compile repository-owned source through an explicit product-layer
   `FILESEXTRAPATHS` path rather than maintaining a duplicate recipe copy.
3. Fetch `aos_core_api` in the recipe at exact `SRCREV
   af3552a0a5eb0237eff7f5f183780ca46c339cd3`. Before the offline compile,
   materialize its verified Gate A checkout into the private compile
   download-cache as a canonical BitBake Git mirror and record its digest. No
   network access is permitted.
4. Declare target build dependencies `grpc protobuf openssl` and native build
   dependencies `grpc-native protobuf-native`. Declare exact runtime
   dependencies `openssl pkcs11-provider softhsm`; do not link SoftHSM
   directly or invent a second PKCS#11 provider.
5. Create dedicated `aos-kac` user/group and shared
   `aos-kuksa-clients` group through the recipe. KAC runs non-root; verifier
   preparation alone runs root and has no network.
6. Ship exactly:
   - `aos-kuksa-auth-compat.service`;
   - `aos-kuksa-verifier-prepare.service`;
   - `/usr/lib/tmpfiles.d/aos-kuksa-auth-compat.conf`;
   - runtime directory `/run/aos-kuksa-auth-compat` mode `0750`, owner
     `aos-kac:aos-kuksa-clients`;
   - socket `/run/aos-kuksa-auth-compat/request.sock` mode `0660`, same owner;
   - verifier directory `/run/aos-kuksa-verifier` mode `0755`, root-owned; and
   - volatile verifier `/run/aos-kuksa-verifier/kuksa-jwt-public.pem` mode
     `0444`, root-owned, created only at runtime after protected verification.
7. Both signer consumers receive credential ID `kuksa-jwt-pin` only through
   systemd `LoadCredential` from the accepted root-owned mode-`0600` source.
   The PIN may not enter a URI, environment, argument, journal or package.
8. Package the separate SELinux domains
   `aos_kuksa_auth_compat_t` and `aos_kuksa_verifier_prepare_t`. Initial
   SoftHSM backend access is read/open/lock only; create/delete/rename stops
   execution for review.

The recipe/package identity above may satisfy only blocking input 3 of the
later Factory-integration packet after this packet completes. It does not
authorize image inclusion or silently close the other Factory inputs.

## Dependency Governance Change

The Gate B proposals are inputs, not an automatically applicable patch. After
acceptance, the worker may add the five target dependencies, matched two
native generator entries and the two missing build-metadata sources recorded
by Gate B only after the following validator behavior is implemented and
tested:

1. `revision` remains a 40-lowercase-hex Git commit by default. A source
   archive may instead use exact form `archive-sha256:<64 lowercase hex>` only
   when `artifactSha256` exists and equals the same digest.
2. `license` may contain only identifiers already in the approved allowlist,
   optionally joined by the exact conjunction ` & `. Parentheses, `OR`,
   `WITH`, unknown identifiers and empty terms reject.
3. Existing dependency entries and semantics remain valid without rewriting.
4. Tests cover valid Git/archive pins, both accepted conjunction expressions,
   mismatched archive/artifact hashes, malformed pins and unknown licenses.
5. The third-party notice delta remains factual and distinguishes target
   runtime dependencies from build-only native generators.

No downloaded source, license text, mirror tarball or build artifact is
committed to the product repository.

## Proposed Execution Gates

### Gate 0 — Revalidation and private build preparation

1. Reprove product base/branch cleanliness and every frozen documentation,
   lock, report and cache hash above.
2. Prove the Builder image, metadata `HEAD`s, target tuple, compiler and all
   selected recipes still match Gate A/B.
3. Copy only verified payloads into the new private compile root. Resolve the
   full build-task dependency closure offline, including CMake, Ninja/GNU Make
   and GTest. If any required payload is absent or its exact identity is not
   already proven by the pinned R6.1 cache, stop for a separate dependency
   acquisition review.
4. Record initial `local.conf`, `bblayers.conf`, source tree and cache hashes.

Gate 0 performs no product edit or compile. It must finish before Gate 1.
Immediately before the first compile, revalidate the same frozen inputs and
cache without repeating network acquisition.

### Gate 1 — Bounded source and recipe implementation

1. Implement only the writable paths and exact package contract above.
2. Add fake-IAM, fake-signer and controlled-clock tests for all
   `UT-KAC-001` through `UT-KAC-010` obligations that are unit/component
   testable without a live Unit.
3. Add deterministic validators for recipe, systemd, tmpfiles, SELinux,
   dependency inventory and secret-negative package content.
4. Stop before any compile if a source change requires an upstream patch,
   unreviewed filesystem authority, Provider signer behavior, named resource,
   image bbappend or another repository.

### Gate 2 — Product-local source gates

Run only repository-owned tests and inspections:

- KAC Python validators/tests and dependency-inventory tests;
- existing repository Python suite;
- `tools/validate_kac.py` and existing R6.1 layer validator;
- `tools/quality_gate.py`, REUSE/SPDX checks and `git diff --check`;
- strict standalone compile of pure parsers/mappers/time/rate-limit logic when
  it requires no host replacement for recipe-selected libraries; and
- changed-path audit against this packet.

Failure stops the packet. It does not authorize a corrective expansion.

### Gate 3 — Pinned offline Yocto compile and package proof

Only after separate acceptance of this packet may the dedicated Builder run
with `BB_NO_NETWORK=1`. Permitted BitBake work is limited to dependency
sysroots and the KAC recipe tasks `do_fetch`, `do_unpack`, `do_patch`,
`do_configure`, `do_compile`, recipe-local `do_install`, `do_package`,
`do_package_qa` and the exact test target. Recipe-local `do_install` writes
only `${D}`; it is not a host, VM or image install.

Required proof:

1. Generate IAM C++/gRPC code with the frozen native generators and compile
   target code with the frozen target libraries and GCC tuple.
2. Execute the complete target test binary with the Yocto target loader and
   recipe sysroot. No case may be silently skipped except separately listed
   real-IAM, real-PKCS#11 and image/boot cases explicitly owned by the later
   qualification packet.
3. Repeat a forced clean KAC compile/test/package cycle with
   `BB_NO_NETWORK=1` against the same verified cache.
4. Inspect package paths, modes, users/groups, dynamic linkage, systemd
   sandbox, SELinux installation, main-package dependency closure and
   removability.
5. Scan source, logs, generated code, workdir and packages for secret, PIN,
   private key, JWT, Unit identity, certificate, static verifier and forbidden
   high-cardinality diagnostics.
6. Record exact source tree, configurations, compiler/generator identities,
   binaries/packages and test-result hashes.

Gate 3 may compile locked dependencies as required by the exact recipe
dependency graph. It may not build `aos-image-vm`, create an SDK, install a
host package or populate/boot any VM.

### Gate 4 — Reviewable completion checkpoint

After every gate passes, the worker may propose one bounded commit in
`codex/imp-03-kac`. Commit creation still requires the execution authorization
for this packet; push, merge, rebase and `main` mutation remain prohibited.
The completion record must include the full changed-path list, source tree,
dependency/cache/configuration hashes, test counts, package inventory and
every skipped later-level case.

## Stop Conditions

Stop without guessing, widening or substituting if:

- a frozen revision, source/archive/license hash or Gate A/B evidence hash
  differs;
- the KAC worktree is dirty or no longer starts at the frozen base;
- any build input is missing from the verified offline cache;
- native/target gRPC or Protobuf versions differ, host tools/libraries enter
  the build, or `AUTOREV`/`AUTOINC` appears;
- compilation or tests require an upstream AosCore, KUKSA, OpenSSL, SoftHSM or
  PKCS#11-provider patch;
- implementation needs SoftHSM create/delete/rename authority, a file-key
  fallback, shared `.usrpin`, PIN in URI/environment/arguments, or another
  signer process;
- the exact package cannot remain separately removable;
- a real named resource, Provider signer, image composition, Unit credential
  or live IAM/KUKSA instance is required;
- any test, package QA, redaction, secret scan or changed-path audit fails; or
- a network request, image task, VM/Unit/Cloud/signing/FOTA/live action or
  writable-boundary expansion becomes necessary.

## Explicit Exclusions

- no Aos named-resource or Service-container bootstrap implementation;
- no fixed OEM Provider JWT/signer preparation or Provider authority;
- no VDP, Brake/Tire, Gateway, Safe Stop Runtime or Demo UI change;
- no `aos-image-vm.bbappend`, packagegroup or successor-image composition;
- no upstream source patch and no second policy/permission database;
- no real key/token creation, verifier publication or provisioning overlay;
- no external network acquisition;
- no bootable image, SDK, VM, Unit, Cloud, signing, FOTA, CARLA or live
  qualification operation; and
- no push, merge, rebase or direct `main` change.

## Completion and Follow-On Rule

Passing this packet may establish `aos-kuksa-auth-compat` as a source-complete,
offline-compiled and package-inspected removable component. It cannot claim
`QUALIFIED`, cannot authorize Factory Image inclusion and cannot demonstrate
real IAM, PKCS#11, KUKSA, cross-Service/cross-Unit, reboot, offline-vehicle or
R0 behavior.

After completion, the Coordinator reviews which exact blocking inputs of
`WP-P1-PLATFORM-KAC-FACTORY-INTEGRATION-002` are truly closed. A separate
combined-branch integration packet must then define merge order and resolve
overlapping product-layer files. Image construction and disposable-VM/live
qualification remain later independent authorizations.

## Authorization Gate

This proposal requires explicit operator review and acceptance before any
product edit, Builder start, dependency compile, recipe/package task,
governance application or commit. Acceptance must name the frozen product
base, writable boundary, offline cache, allowed BitBake tasks and exclusions.
