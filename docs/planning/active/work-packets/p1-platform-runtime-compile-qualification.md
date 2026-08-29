<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform Runtime Compile Qualification Work Packet

- ID: `WP-QUAL-P1-PLATFORM-RUNTIME-001`
- Lane: `L-PLATFORM-QUALIFICATION`
- Increment: `IMP-03-RUNTIME-COMPILE`
- State: `COMPLETED — PINNED OFFLINE COMPILE/TEST PASSED`
- Prepared: 2026-08-29
- Completed: 2026-08-29
- Product source changes authorized: only the exact bounded compile/test defect
  corrections explicitly accepted during qualification
- Dedicated Yocto Builder VM and pinned dependency materialization authorized:
  yes — 2026-08-29
- External network, bootable image build, demo/disposable VM, provisioning,
  signing, FOTA and live operation authorized: no
- Source checkpoint:
  `aos-vehicle-platform@4d8800636ded58386e2872a7e415dc1cc322c92c`
- Parent packet: [Factory and Runtime](p1-platform-factory-runtime.md)

## Outcome

Compile and execute the integrated OEM Component Runtime Safe Stop suite
against the exact AosEdge R6.1 source and Yocto dependency baseline. This is a
qualification-only packet: it may materialize pinned build inputs in a private
cache and build the bounded test target. Exact product-owned compile/test
defects may be corrected only after the active attempt stops and the operator
explicitly accepts the correction; the packet may not build a bootable image
or operate a demo VM or Unit.

The packet was created because the source checkpoint passed every locally
available gate, including a strict standalone compile of the pure policy
evaluator, but the pinned AosCore, Poco and GTest inputs were not materialized
in the current workspace. The completion record below closes that compile/test
gap without claiming image or live qualification.

## Frozen Inputs

| Input | Exact identity |
| --- | --- |
| Platform source checkpoint | `aos-vehicle-platform@4d8800636ded58386e2872a7e415dc1cc322c92c` |
| `meta-aos` | `176da6346b1199f854106dede4cc49604174619c` |
| `meta-aos-vm` | `b13320898a2ed1cce504f90f70451638232d6a83` |
| `aos_core_cpp` | `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` |
| `aos_core_lib_cpp` | `60cb83535f773762c61ac5f544b31b7b88c502e3` |
| `aos_core_api` | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` |
| Poky | `7d50718f90c51fb7f650c9db59b28c6e0194e5d2` |
| meta-openembedded | `ec0469748be4159fb83fb0fa0148d786484c88cf` |
| Safe Stop profile | `1.1.1`, SHA-256 `5b7087748877295837eb16a8bac02742dbae7328e54ba0b852fed2f5de6d3be9` |
| Target | AosVM R6.1 `qemuarm64`, `aos-servicemanager` bounded component-runtime tests |

The complete layer/source selection remains the accepted
`components/r6-1-source.lock.json` and project pinned Moulin manifest. No
floating branch, tag-only substitution or host-library replacement is allowed.

## Private Build Boundary

After explicit authorization, generated material may exist only below one
private, non-Git cache directory dedicated to this packet. The cache must
contain no key, certificate, token, PIN, Unit identity or generated
credential. Product changes were limited to exact compile/test defects in the
already accepted Runtime boundary and were checkpointed only in the isolated
implementation branch.

The packet may reuse an already materialized cache only after proving every
repository `HEAD`, recipe selection, compiler tuple and source checksum against
the frozen inputs. Otherwise it stops or requests exact-source acquisition;
it never silently falls back to host headers or libraries.

## Exact Work

1. Materialize or verify the frozen R6.1 metadata and source set without
   changing any product repository.
2. Resolve the exact BitBake selections for the Service Manager test build,
   including Poco, GTest, compiler/sysroot and transitive AosCore libraries.
3. Build only the bounded `systemd-slot-component` and its test target through
   the accepted Service Manager recipe/toolchain seam.
4. Execute the complete Safe Stop evaluator, VISS adapter and Runtime suite.
5. Repeat the compile/test with network disabled using the same cache.
6. Record compiler identity, effective recipe versions, invoked target, test
   list/results, source/cache digests and boundary audit.

## Required Cases

The integrated suite must cover the accepted first-install, replacement,
removal, timeout, cancellation, same-candidate reattach, different-candidate
rejection, restart-while-waiting, Safe Stop loss and rollback behavior. It must
also cover threshold boundaries, missing/stale/contradictory evidence,
repeated/non-monotonic frames and the 1.1.1 freshness rule: each sample is
fresh when acquired, accumulated history proves stability only, and the latest
complete sample is fresh again at every destructive gate.

## Stop Conditions

Stop without patching or substituting if:

- any frozen revision or content digest differs;
- the exact recipe-selected Poco/GTest/AosCore inputs cannot be established;
- compilation requires a product source change, an upstream patch or a host
  dependency not selected by the pinned build;
- a test failure reveals an implementation or contract defect;
- the work requires an image build, VM, Cloud, signing or live operation; or
- any credential or secret is encountered.

## Completion Rule

Completion records either a passing pinned compile/test result or the exact
blocking defect. A passing result permits
`WP-P1-PLATFORM-FACTORY-RUNTIME-001` to move from source draft to
`IMPLEMENTED`; it does not qualify a Factory Image, authorize integration to
`main`, or authorize a disposable-VM/live FOTA run.

## Completion Record

The operator authorized the dedicated Yocto Builder VM, pinned dependency
materialization and bounded source corrections on 2026-08-29. Qualification
used the existing R6.1 ARM64 Builder image with SHA-256
`8f61e558498ba262da5b5d13f75b2921136b737a1492415150f33b3d0e46a281`
and the private build root `/home/yocto/runtime-qual-458cd95`. No bootable image,
demo VM, Unit, Cloud, provisioning, signing or FOTA operation was performed.

The first pinned compile exposed only product-owned defects inside the accepted
Runtime boundary. Each defect stopped the current attempt and was corrected
after explicit operator authorization:

- `091cf35251a0b761f6f920ced95f4b3d826751c0` declares the recipe-selected
  Poco NetSSL target used by the accepted WSS/mTLS transport;
- `f27a3d4d9dcb43e853615900e269c376c02159da` configures the TLS peer name on
  Poco 1.12.5's `SecureStreamSocket` while retaining the fixed numeric endpoint;
- `e6e2c31e0ce0f7c60354019d393908e8e8b53e31` keeps the bounded 64-KiB VISS
  receive buffer off the restricted thread stack;
- `c92be9b8bcc5de6ef579388ff24d46ccff6c0b92` transfers the large AosCore
  transaction state through heap ownership rather than thread stacks; and
- `4d8800636ded58386e2872a7e415dc1cc322c92c` closes the completed-worker/new-
  transaction handoff race and classifies future source time as contradictory
  evidence rather than stale evidence.

The final pinned build identity was:

| Evidence | Exact result |
| --- | --- |
| Target | `qemuarm64`, `cortex-a57`, `aarch64-aos-linux` |
| Compiler | GCC `13.4.0`, tuple `aarch64-aos-linux` |
| Build target | `BB_NO_NETWORK=1 bitbake -c compile aos-servicemanager` |
| Aos Service Manager | `SRCREV 9eecb80c4994937b5c8cbe0464970f81e8ad4c2d` |
| Poco | `1.12.5p2`, `SRCREV 1d6fb3e1383e559cacbada5e3f861c0dafaf5d30` |
| GTest | `1.14.0`, `SRCREV f8d7d77c06936315286eb55f8de22cd23c188571` |
| Pinned Moulin manifest | SHA-256 `b9b49a575798f2bc4a532a794e77352ed21596677ef5aced4304db9e7a87f09e` |
| Qualification `local.conf` | SHA-256 `6bb018cf17ea75041f598552822f068f754a6b4ddf12509e434d13f8f80d0bea` |
| Qualification `bblayers.conf` | SHA-256 `b8a46b9a1dfba561c3dac6bb7e5696d23339268a6387782bfcd122d8cf325a71` |
| Final source tree | commit `4d8800636ded58386e2872a7e415dc1cc322c92c`, tree `db3d316675a0cf0a60574c90634a75207a4a26c4` |
| Final test binary | SHA-256 `3bb5e8070fe511926f30dc09ea35503e405a8c940b51e8fec10a5877577c4956` |
| Final CMake cache | SHA-256 `4c416b7fd196572b2547196a4b3afa22db5ddbec6ecc8af1e5f4f1935e3ae4d1` |

Two consecutive clean compiles completed with `BB_NO_NETWORK=1` against the
same verified cache. After each final compile, the exact target binary was
executed with the target Yocto loader and recipe sysroot in the privileged
execution context used by Service Manager. Both executions reported 53 tests
from five suites: 51 passed and two explicitly skipped real-provider profile
cases whose own message states `real provider qualification is not requested`.
Those two cases require the separate image/disposable-VM qualification and do
not reduce coverage of this packet's Safe Stop, VISS, archive and mocked
Runtime lifecycle requirements.

The isolated product worktree was clean after the final commit. All 20 changed
paths from base `bdc72aba97a83c9868d454588189ef139710a6d7` remain inside the
packet's writable boundary. No upstream AosCore, Poco, KUKSA or GTest source
was patched; no KAC resource or signer seam was guessed. Local verification
also remained green: 37 Python tests, the R6.1 layer validator, the 91-file
quality gate and `git diff --check`.

## Authorization Gate

The operator accepted dependency materialization, the dedicated Builder VM,
the bounded offline compile/test run and the exact corrective source commits
on 2026-08-29. This completion does not authorize merge, push, image build or
live qualification.
