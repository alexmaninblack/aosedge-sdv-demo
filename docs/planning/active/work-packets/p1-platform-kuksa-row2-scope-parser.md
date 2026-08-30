<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KUKSA Row2 Scope Parser Work Packet

- ID: `WP-P1-PLATFORM-KUKSA-ROW2-SCOPE-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-KUKSA-ROW2-SCOPE`
- State: `COMPLETED IN PLATFORM TRAIN — HISTORICAL PACKET / NO RESIDUAL AUTHORITY`
- Version: 0.1
- Prepared: 2026-08-29
- Direction to correct the pinned KUKSA 0.5.0 Row2 blocker: accepted
  2026-08-29
- Product edit, Builder task, package task and commit authorized: no
- Network, dependency acquisition, image/rootfs/SDK build, install, VM/Unit,
  provisioning, signing, FOTA, Cloud and live operation authorized: no
- Blocking parent:
  [KAC Factory integration](p1-platform-kac-factory-integration.md)

## Completion Resolution

The exact two-regex correction and its tests were implemented in product
commit `7824a82` and carried into accepted `.21` source
`667afb1512cf43ff27f1ab5327293208bf73045b`. The original authorization limits
below remain historical and grant no new product, Builder, VM or Cloud action.

## Outcome

Create the smallest OEM Yocto-layer correction that makes the pinned KUKSA
Databroker 0.5.0 JWT scope parser accept decimal digits `0` through `9` after
the required uppercase first character of every path component. The product
layer applies one patch to BitBake's disposable source work directory; no
upstream checkout is modified and no KUKSA version or `SRCREV` changes.

The only production-code change is two occurrences of the same character
class in one parser regex:

```text
[A-Z][a-zA-Z0-1]* -> [A-Z][a-zA-Z0-9]*
```

Both replacements are required: the first occurrence parses the first path
component and the second parses every dot-separated later component. The same
patch adds narrow table-driven Rust unit cases beside the pinned parser tests.
No action, wildcard, claim, permission, expiry or path-component-start
semantic changes.

Passing this packet produces a source-compiled, package-inspected prerequisite
checkpoint for Factory Gate 1. It does not add the package to an image, start
KUKSA, validate a JWT, exercise a lifecycle, or establish `QUALIFIED` target
behavior.

This file is a proposal. The accepted direction above does not itself
authorize the exact product edit, build or commit described below.

## Frozen Inputs and Evidence

| Input | Exact identity |
| --- | --- |
| Solution committed baseline | `aosedge-sdv-demo@4bede414b402c4b94bd45a9b4f4caac5992bb390`, tree `0c21b8e045474c75af024a0f7f6d41087446fbd3` |
| Product main ancestry | `aos-vehicle-platform@bdc72aba97a83c9868d454588189ef139710a6d7`, tree `8754a343dc57cacfbe85eb134f0c8c9b8e67b2c6` |
| Required product base | completed KAC checkpoint `570d17821edfd85915e688f7239a04eb4fc1f535`, tree `6ebe07e7793f3dbbacc688fd8781d12c70b1f599` |
| KUKSA source | tag `0.5.0`, commit `30e5c13abc496d0b39aaa6c25acebb088b9902e3`, tree `919f40c5f88ff0a74304c9e99a36b726462a2363` |
| Pinned recipe owner | `meta-aos@176da6346b1199f854106dede4cc49604174619c`, tree `b71ce05bc6727bf2c918a37b7dc675370f29d857` |
| Pinned recipe | `recipes-connectivity/kuksa-databroker/kuksa-databroker_git.bb`; Git blob `dbf6fefb62d4c423cbd6c258def1ac8a150caf0e`; SHA-256 `108bbf00b39ad4ba68968b56d64276a49630c7773ca0bcc9cbd274a8f319132a` |
| Pinned parser | `databroker/src/authorization/jwt/scope.rs`; Git blob `263b277d155cc2b642883724b3cd1f24abb9525d`; SHA-256 `d9abb22c118d63f728b12a1d06bc10c8e72848aaef07181dc5fbabf369a69e2b` |
| Gate 0 evidence manifest | SHA-256 `57ecc8a6f2147eeb9ec3b6cbfc39e05dd8602dc32e82b5bc79f915dbfc7b98f4` |
| G0-03 identity record | `precopy-sha256-and-identity.txt`, SHA-256 `3bddc1323f30e82fc3a73f9e06ad46979de16868015d7a465ff5a836626f26b1` |
| G0-03 source verification | `source-hash-verification.txt`, SHA-256 `5f89740f9d612c8bd4b489e82bfd3b99882f4e77f944dce31bed6e01d4c9a743` |
| G0-03 post-copy record | `postcopy-sha256.txt`, SHA-256 `c71e811437cbbafac67db17631e503f9a4c577a2c72e61db29ac950cadbf8ee7` |
| Gate 0 finding matrix | SHA-256 `6044ae1d112e3302adb337f8f395e6d18445d0672f2e36d5b02a3964b92cec09` |
| KAC requirement | `CR-KAC` 0.12, SHA-256 `ab0d6bf039d94d52b82ff77c6bcf74ffe397f9f2b6110f8be032ed07198c3e39` |
| Factory requirement | `CR-FACTORY` 0.5, SHA-256 `9c8e224c4e0ecdf366a7acb95f2fd310b23cf109dd33bd20232b1982ba361c2d` |
| VDP requirement | `CR-VDP` 0.9, SHA-256 `6650864fd83229a43fcb843c663558844d51e90d1f208c4131501bede9af5fee` |
| VDP compatibility profile | 1.0.1, SHA-256 `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871` |
| Builder image | Ubuntu 22.04 ARM64, SHA-256 `8f61e558498ba262da5b5d13f75b2921136b737a1492415150f33b3d0e46a281` |
| Target/toolchain | R6.1 `qemuarm64`, `aarch64-aos-linux`, GCC 13.4.0 |

The read-only Gate 0 export is currently outside the repositories at
`/private/tmp/kac-factory-gate0-evidence-20260829/`. Its manifest and the
individual hashes above are evidence inputs, not a writable implementation
location. If those bytes are unavailable or any hash differs, stop; do not
recreate or substitute evidence from the network.

The pinned parser proves the defect at source lines 43 and 50 of the exported
file. Both positions use `[A-Z][a-zA-Z0-1]*`. Therefore an exact accepted scope
such as
`provide:Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed` fails before permission
construction, while the frozen VDP profile requires multiple `Row2` paths.
The recipe fixes `SRCREV` to the KUKSA commit above and owns package
`kuksa-databroker`; no source upgrade is required or permitted.

## Repository, Isolation and Fan-In Ownership

| Item | Frozen proposed value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Branch | `codex/imp-03-kuksa-row2-scope-parser` |
| Isolated worktree | `../aos-vehicle-platform-imp-03-kuksa-row2-scope-parser` |
| Required initial HEAD | clean `570d17821edfd85915e688f7239a04eb4fc1f535` |
| Required ancestry | single parent chain from `bdc72aba97a83c9868d454588189ef139710a6d7`; no Runtime or VDP merge |

The Platform owner owns this packet and its checkpoint. After completion, the
Coordinator must update `WP-P1-PLATFORM-KAC-FACTORY-INTEGRATION-002` so its
required initial HEAD is the exact resulting parser checkpoint, not
`570d178...`. Factory Gate 1 may then add only its separately authorized
Factory changes on top. The later successor fan-in owns Runtime/VDP/KAC/Factory
ordering and collisions; this packet may not merge, rebase or resolve them.

No implementation commit from this packet may be cherry-picked directly onto
`main` or an image branch. The dependency sequence is:

```text
570d178 KAC checkpoint
  -> this Row2 parser checkpoint
    -> KAC Factory integration Gate 1 checkpoint
      -> separately reviewed successor fan-in
```

## Exact Writable Boundary

After separate exact authorization, only these new product paths may change:

1. `meta-aos-vehicle-platform/recipes-connectivity/kuksa-databroker/kuksa-databroker_git.bbappend`
   to prepend only its sibling `files` directory, append only the patch below,
   and, if required by the frozen cargo recipe interface, compile the scoped
   Rust tests without packaging them;
2. `meta-aos-vehicle-platform/recipes-connectivity/kuksa-databroker/files/0002-authorization-accept-decimal-digits-in-scope-path.patch`
   to modify only
   `databroker/src/authorization/jwt/scope.rs` in BitBake's source workdir; and
3. `tests/test_kuksa_databroker_scope_patch.py` for product-owned static
   wiring, exact-delta, source-identity and forbidden-change checks.

The patch is also the only writable source of the Rust behavior tests. It may
add tests only inside the existing `#[cfg(test)]` module in
`databroker/src/authorization/jwt/scope.rs`. That upstream-relative path is a
patch target in generated BitBake work output, not a repository writable path.

No README, dependency lock, `DEPENDENCIES.json`, image bbappend, packagegroup,
service/default file, KAC source/recipe, SELinux policy or other test/tool path
may change. If the exact three-path boundary is insufficient, stop and revise
this packet before editing.

## Exact Patch and Test Contract

### Production delta

The patch must contain exactly two production-token replacements, both in the
single raw regex literal of `parse_whitespace_separated`:

```text
[a-zA-Z0-1]* -> [a-zA-Z0-9]*
```

It must preserve the required leading `[A-Z]`, anchors, captures, dot
separation, action matching, whitespace splitting and every other byte of
production logic. Patch application must be exact with zero fuzz/offset and
must fail if the preimage parser SHA-256 is not the frozen value.

### Positive Rust cases

One table-driven positive test must prove at least these exact cases and exact
returned action/path values:

- `provide:Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed`;
- `read:Vehicle.Test.Row9.Value`;
- `actuate:Vehicle.Test.Row2030.Value`;
- `read:Vehicle.Test.Row0.Value read:Vehicle.Test.Row1.Value`, preserving
  whitespace-delimited multi-scope behavior; and
- the existing no-digit and whole-segment-wildcard tests remain passing.

`Row2` is the product blocker; `Row9` proves the full upper end of the new
class; `Row2030` proves repeated decimal digits rather than a special-case
single digit.

### Negative Rust cases

One table-driven negative test must prove `Error::ParseError` for at least:

- component beginning with a digit:
  `provide:Vehicle.Chassis.Axle.2Row.Wheel.Left.Speed`;
- empty component: `provide:Vehicle.Chassis..Row2.Speed`;
- punctuation: `provide:Vehicle.Chassis.Row2-Wheel.Speed`;
- embedded/suffixed wildcard: `provide:Vehicle.Chassis.Row2*.Speed`;
- prefixed wildcard: `provide:Vehicle.Chassis.*Row2.Speed`;
- unknown action: `write:Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed`; and
- empty path: `provide:`.

Pinned KUKSA intentionally accepts a complete path component `*`, as proved by
the existing positive tests and regex alternatives. This packet does not
change that behavior. The fixed Factory Provider scope and KAC inputs continue
to reject every wildcard before issuance. If the operator instead requires
KUKSA itself to reject a complete `*` component, stop: that is a separate
authorization-model patch, conflicts with the two-token delta, and is not
authorized here.

### Product-owned static test

`tests/test_kuksa_databroker_scope_patch.py` must fail unless all of the
following are true:

- the bbappend selects exactly the named patch and does not change `SRCREV`,
  `PV`, `BRANCH`, dependencies, package contents or service configuration;
- the patch preimage identifies the frozen source path and contains exactly
  two `[a-zA-Z0-1]*` removals and two `[a-zA-Z0-9]*` additions in production
  context;
- the patch touches no upstream file other than `scope.rs`;
- every required positive and negative string is present in the Rust tests;
- no added production line contains a wildcard-policy, action, permission,
  claim, expiry, decoder or service change; and
- the repository changed-path set is a subset of the exact three-path
  boundary.

Static inspection is a boundary gate, not a substitute for executing the
patched Rust tests.

## Execution Gates

### Gate 0 — identity and offline-input revalidation

Before any edit, prove the solution requirement hashes, product base/tree,
`meta-aos` commit/tree, recipe blob/SHA-256, KUKSA commit/tree/tag and parser
blob/SHA-256 above. Prove the isolated worktree is clean and the verified
Builder/cache contains the complete pinned KUKSA Cargo/BitBake closure.

Gate 0 performs no edit, fetch, unpack, patch or compile. Any missing or
mismatched input stops for review; no network acquisition or substitute
revision is allowed.

### Gate 1 — bounded source implementation

Create only the three writable paths. Before staging, prove from the patch
that the production delta is exactly the two character-class replacements and
the rest is test code/wiring. `git apply --check` or BitBake patch dry-run must
report exact context with no fuzz or offset against the frozen source.

### Gate 2 — product-local source gates

Run from the isolated product worktree:

- `python3 -m unittest -v tests.test_kuksa_databroker_scope_patch`;
- the existing complete Python unit suite if its discovery writes only caches
  outside the repository;
- `python3 tools/quality_gate.py` with bytecode/cache output redirected outside
  the repository;
- REUSE/SPDX and secret-negative checks;
- `git diff --check`; and
- an exact changed-path audit against the three-path boundary.

No gate may rewrite formatting, dependency metadata, lockfiles or unrelated
worktree files. A test that requires a repository write must use a disposable
copy outside every Git repository or stop.

### Gate 3 — pinned offline BitBake and Rust package proof

Only after separate package-task authorization, use the frozen Builder and its
already verified cache with `BB_NO_NETWORK=1`. Generated output is limited to
one dedicated root outside every Git repository,
`/home/yocto/build/wp-p1-platform-kuksa-row2-scope-001/`, including its
`TMPDIR`, logs, patched `${S}`, test binaries and packages.

Permitted BitBake work is limited to `kuksa-databroker` dependency sysroots and
the exact recipe tasks `do_fetch`, `do_unpack`, `do_patch`, `do_configure`,
`do_compile`, the scoped Rust test build/execution, `do_install`, `do_package`
and `do_package_qa`. Required proof:

1. `do_fetch` succeeds from the verified local cache with
   `BB_NO_NETWORK=1`; the unpacked commit/tree and pre-patch `scope.rs` hash
   match the frozen inputs.
2. `do_patch` applies only the named OEM patch with zero fuzz/offset. The
   patched source diff contains exactly the two production replacements plus
   the accepted tests.
3. The Databroker compiles for the frozen target. The scoped
   `authorization::jwt::scope` Rust tests compile and all execute through the
   Yocto target loader/recipe sysroot on the ARM64 Builder; no test is skipped.
   Test execution may not start the Databroker or open a socket.
4. `do_install`, `do_package` and `do_package_qa` pass. Package name, file
   inventory, service/default bytes, dependencies, users/groups, modes and
   dynamic linkage are byte-for-byte or normalized-manifest equivalent to the
   unpatched baseline except for the Databroker executable and normal package
   metadata/digests caused by that executable.
5. Repeat the scoped test and compile/package/QA sequence from a newly cleared
   dedicated `TMPDIR`, still offline. Do not clear or modify the shared
   verified download/evidence cache.
6. Record pre/post source hashes, exact patch hash, BitBake environment hash,
   test names/count/result hash, Databroker binary/package hashes, normalized
   package delta and build-root inventory.

No rootfs/image/packagegroup/SDK task, host installation or target execution
outside the scoped test binary is allowed.

### Gate 4 — reviewable checkpoint

After Gates 0 through 3 pass, re-run the exact boundary and dirty-state checks.
One local commit containing only the three paths may then be proposed if the
separate execution authorization explicitly permitted commit creation. Report
commit/tree, parent, patch SHA-256, all test/gate results, normalized package
delta and later target cases. Push, merge, rebase, tag and `main` mutation are
forbidden.

## Stop Conditions

Stop without editing further, widening, upgrading or substituting if:

- the packet has not received exact implementation authorization naming its
  base, three writable paths, offline Builder/cache tasks and exclusions;
- any frozen commit, tree, blob, SHA-256, tag, requirement or Builder identity
  differs;
- the isolated worktree is dirty or does not start at `570d178...`;
- either proven `[a-zA-Z0-1]*` occurrence is absent, moved, already changed or
  more than two production occurrences require correction;
- the patch applies with fuzz/offset, touches another upstream file or changes
  anything beyond the two production tokens and scoped tests;
- correct `Row2` behavior requires an action, wildcard, permission, claim,
  decoder, expiry, service, recipe-version or dependency change;
- the requirement is reinterpreted to reject complete `*` components inside
  KUKSA rather than only malformed partial wildcards;
- any required positive or negative case fails or a pre-existing upstream
  parser test regresses;
- the target Rust tests cannot be executed offline through the frozen Yocto
  loader/sysroot without adding recipe/package files or dependencies;
- baseline and patched normalized package inventories differ outside the
  Databroker executable and inevitable package metadata/digests;
- any cache input is absent, network access is attempted, or the build would
  write outside the dedicated output root/shared cache contract;
- implementation overlaps Runtime, VDP, KAC/Provider, BHS/Tire, UI,
  lifecycle, image, service, SELinux, dependency or lockfile work; or
- any image/rootfs/SDK build, install, Databroker start, JWT/key generation,
  signing, FOTA, VM/Unit/Cloud/live operation, push, merge or `main` mutation
  would be required.

## Explicit Exclusions

- no KUKSA version, `SRCREV`, branch, recipe or dependency upgrade;
- no mutation or commit in a KUKSA or `meta-aos` checkout;
- no broader regex cleanup, lowercase component start, Unicode digit, hyphen,
  underscore, wildcard or action-policy change;
- no KAC claim/scope generator, fixed Provider profile, JWT decoder,
  permission matcher, VDP, Runtime, Factory, Brake/Tire, UI or contract edit;
- no `aos-image-vm.bbappend`, packagegroup, rootfs, image, SDK, FOTA or SOTA;
- no key, PIN, JWT, certificate, secret, Unit identity, provisioning or
  signing operation;
- no Databroker process, socket, VM, Unit, Cloud, CARLA or live operation;
- no dependency download, network, push, merge, rebase, tag or direct `main`
  change; and
- no claim of target qualification from source/package proof.

## Completion and Authorization Rule

Completion may establish only that the frozen KUKSA 0.5.0 source accepts the
required decimal path components, the OEM patch is reproducible offline, and
the package delta is bounded. Installed-image, real-JWT, KUKSA process,
Provider, Service, reboot/deprovision and cross-Unit behavior remain owned by
the later Factory image and disposable-VM qualification packets.

This proposal requires explicit operator acceptance before any product edit,
Builder/BitBake/Rust task or commit. Acceptance must name the exact base,
writable paths, verified offline cache, permitted recipe tasks, test-loader
execution and exclusions. The already accepted recommendation to fix the
blocker authorizes this planning proposal only.
