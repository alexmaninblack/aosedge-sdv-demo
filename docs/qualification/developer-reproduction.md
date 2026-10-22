<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Independent developer reproduction evidence

- Status: scoped fresh-workspace and exact-package M1 proof; not fresh-host acceptance
- Version: 1.0
- Prepared: 2026-10-20
- Owner: SDV Lab integration

The [current baseline](current-baseline.md) separates this independently rebuilt
rc.3 package from the published rc.4 operator DMG and the newer B source
selection. This earlier proof does not qualify a newly assembled rc.4 B package. The
[specialist reference](../development/release-reproduction-r2.md) owns the
reusable build procedure; this page records one completed campaign, not another
required developer checklist.

## Source and input boundary

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

## Exact rebuilt media and M1 result

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

## Measurements and retained failures

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

## Evidence ownership and exclusions

Private timed attempts, exact candidate/target bindings and closure receipts
are retained under `build/maintenance/r4-rc3-20261020`; the fresh workspace is
`reproduction-rc3/sdv` beneath the selected workspace parent. These are evidence
locations, not required maintainer inputs. Failed attempts remain distinct from
the final passes. Full fresh-host R4, native Setup without ready certificates
for this exact rebuilt media, full-source rebuilding and broader formal
acceptance remain separate gates. The rc.2 native Setup proof in the
[M1 record](m1-clean-install-e2e-2026-10-14.md#native-setup-with-no-ready-certificates-pass-on-15-october)
does not transfer to this artifact.

The rebuilt media remains a separate reproduction result even though its
product-version string is rc.3. The existing published rc.3 DMG, tag, receipts,
Dropbox object and option A selection were not overwritten or promoted.
