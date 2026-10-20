<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Specialist build and reproduction reference

The ordinary developer route is [README option 2](../../README.md#developer-build).
It prepares tools, fixes the source selection, obtains verified inputs and runs
the reviewed engineering build chain. Do not run a parallel manual workflow
against the same workspace.

## Current selectors and ownership

- [Current developer selection](../../workspace/current-developer-build.json)
  binds the reviewed build/producer plan.
- [Launcher catalog](../../workspace/launcher-catalog.json) independently selects
  operator delivery; a B build is not automatically the current A release.
- [Reproduction contract](../../contracts/release-reproduction/README.md)
  defines immutable inputs, provenance, candidate results and storage.
- [Developer guide](../getting-started/reproduce-demo.md) explains automatic B
  continuation and the separate installation/publication steps.
- [Reusable simulation inputs](reusable-simulation-inputs.md) describes retained
  CARLA dependencies; no engine rebuild is needed for an unchanged dependency.

Sources, verified caches, scratch and results use the selected declared
workspace. Current B accepts internal or external local APFS storage and
checks Docker's actual backing disk separately. Frozen predecessor plans keep
their original storage policy and source identities. Do not mutate those plans
to make another environment pass.

## Read-only specialist inspection

From the selected integration checkout:

```sh
./lab --help
./lab plan --profile developer
./lab plan --profile full-source
./lab factory --help
```

These commands inspect declared interfaces and gates; they are not builds or
evidence of complete reproduction. Full-source readiness remains explicitly
incomplete.

<a id="factory-source-build-on-external-storage"></a>

## ARM64 controller image (Factory)

The Factory image is the clean Linux/AosEdge base for the virtual controller.
The separate ARM64 Linux Builder compiles it. Preparing macOS QEMU/Python tools
does not acquire or prepare that Builder.

The [recorded exact-source Factory procedure](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/development/release-reproduction-r2.md#factory-source-build-on-external-storage)
documents the retained warm Builder and its native/package/image gates.
It is valid only for its declared source/base/cache/layout; it is not a
turnkey fresh-host bootstrap. Use the existing Factory owner adapter, preserve
offline/disk guards and obtain independently reviewed packaging pins for a new
image. Never replace a backing image underneath a provisioned VM.

The [specialist guide](../getting-started/full-source-build.md) distinguishes
fresh Builder requirements, retained-adapter guards and unmeasured cold peaks.
CARLA/Unreal source/licensing/build closure is a separate gate.

## Builds, evidence and delivery

The automatic developer chain returns a receipt and
CHAIN_BUILT_NOT_QUALIFIED, with a readable output path. Its result is not an
installed demo, Cloud publication, notarized app or qualified release.
The [release campaign](release-campaign.md) owns promotion after exact source,
artifact and target-consumer evidence.

## Current independent workspace proof

On 20 October 2026 the published B launcher at integration commit
`315064b2f9d0a6654c472b68ed5a3922f94aaa29` completed its 17-step chain in
a new APFS workspace on the development SSD. It acquired declared Git sources
and reused only the five checksum-verified public archive objects for CARLA,
Gateway SDK, host support, Factory and vehicle bases. No old extracted runtime,
application build output, receipt, provisioned VM or credential was a build
input. CARLA and Factory were not rebuilt. The existing developer host/tools
and authorized signing identity were reused: this is **fresh-workspace proof,
not fresh-macOS or cold-cache proof**.

The reviewed plan selected `1.2.0-rc.3`, producer `13bcc4f48a635f93f1cadaf816b35abe019dff3b`
for the six non-component roles, component producer
`82dc1cca93645e0e5d4597dc41c32d5010fc7c81`, integration application source
`e787b926471dc096ed365efe0178d8d0181de1a5` and Gateway native source
`19354402594ab2facf5f99f58bc3105740b4ad55`. Dependency record
`sdv-lab-rc3-r4-inputs-dropbox` retained the unchanged binary/input-lock closure.
The source gate passed 207 unit tests before assembly. Fixes bound media to the
selected version, preserved immutable catalog records and allowed an explicitly
authorized exact native-source fetch when a shallow producer lacks that commit.

| Independently rebuilt artifact | Identity |
| --- | --- |
| DMG bytes | 14,158,955,472 |
| DMG SHA-256 | `677ece3c80e309499f503381a6ff724c7ac5a350c25b57a49ea0a0a60984f967` |
| Application manifest | `695bd7680356bf8b3431a08900c687b086b26a529eb4430a85ef55a56497ab11` |
| Setup executable SHA-256 | `b84dcee1e05e7754d5ebd1d8cec42a2fb4eedd82b94f2f17314092616f7ce586` |
| Signing | Apple Development engineering preview; not notarized |

This different DMG was installed on the dedicated M1 internal disk using the
authorized existing OEM/SP pair for Production Aos Cloud and a fresh **Test**
vehicle. The previous exact Test was normally retired with explicit authority;
Production-role resources were preserved. The new Test completed 118/118 API
checks and all 42 visible browser stages with actual signed native driving
input. Coverage included serial VDP/Brake updates, Tire, products/advisories,
independent Reset/history, five-minute offline recovery, ignition, Stop/Start
and moving QM updates. Owned windows/processes/listeners, browser/native/UI
transport/display helpers and installer mounts were closed. The stopped Test,
VM disk, models, history and credentials were preserved; shared Docker was not
restarted or stopped. No live demo ran on the development Mac.

| Measurement | Seconds | Scope |
| --- | --- | --- |
| Successful B execution | 933.599 | Fresh source workspace, verified archive-cache reuse |
| Initial install/API attempt | 473.750 | Transfer, signed Setup install/prepare; stopped at local certificate inspection |
| Continued API campaign | 1872.806 | Existing installation reused; 118/118 final checks PASS |
| Visible UI campaign | 1347.450 | 42/42 stages, preflight and confirmed cleanup |
| Recorded campaign wall time | 7412.094 | From initial preflight through final closure, including failures, diagnosis, host preparation and execution-control waits |

Xcode first-launch preparation initially stopped B before source checkout or
compilation. The scoped host initialization resolved it. The first API attempt
could not confirm local certificate inspection; both unchanged certificates
subsequently passed the packaged helper and normal Cloud checks before the
existing scenario continued. Its initial error remains recorded; the underlying
one-off read failure was **not root-caused**. No certificate replacement,
timeout relaxation, repeated installation or second build was used to recover.

The workspace's final `du -sk` inventory reported approximately 112.9 GiB;
APFS clones/shared extents make that unsuitable as exclusive physical usage.
Five-second free-space samples across the shared APFS pool showed approximately
41.4 GiB maximum growth from initial preflight. Other applications share that
pool: this is not an isolated peak-capacity or cold-build requirement.

Private timed attempts, exact candidate/target bindings and closure receipts
are retained under `build/maintenance/r4-rc3-20261020`; the fresh workspace is
`reproduction-rc3/sdv` beneath the selected workspace parent. These are evidence
locations, not required maintainer inputs. Failed attempts remain distinct from
the final passes. Full fresh-host R4, native Setup without ready certificates,
full-source rebuilding and broader formal acceptance remain separate gates.

The rebuilt media remains a separate reproduction result even though its
product-version string is rc.3. The existing published rc.3 DMG, tag, receipts,
Dropbox object and option A selection were not overwritten or promoted.

## Earlier measured procedure

The [original R2 execution and timing record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/development/release-reproduction-r2.md)
preserves earlier warm measurements, input counts, failed attempts and staging
notes. They are evidence, not current inventory or another required checklist.
