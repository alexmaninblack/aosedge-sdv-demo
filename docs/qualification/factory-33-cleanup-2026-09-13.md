<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .33 artifact cleanup — 13 September 2026

Status: **Completed**. The user explicitly approved one-off direct deletion of
the audited intermediate outputs, outside Demo Control, without adding a helper.
No new cleanup command or runtime implementation was introduced.

## Result

- Payload removal completed at **2026-09-13T10:24:37.602Z**: 166 exact file/directory
  targets, 3370 contained regular files, zero symlinks and zero open handles.
- Allocated size of removed payloads: **17,020,735,488 bytes**
  (15.85 GiB). Data-volume available-space increase across removal: **15.84 GiB**.
- Available after removal: **247.23 GiB**, compared with 231.40 GiB before it.
  These are dated `df` observations on an active APFS volume, not a purgeable
  estimate or a guarantee of byte-for-byte future capacity.
- Removal is permanent: no Trash or backup copy was made. Old generated
  payloads can only be regenerated/reobtained where preserved sources and
  tooling permit; deleted comparison-VM runtime state cannot be restored.
- Small original manifests, prepared/publication receipts, test evidence and
  source fixtures were retained. Old retained receipts describe **removed**
  payloads and are not reusable prepared bundles or a current build cache.

The .31 comparison journal already recorded Cloud deletion and confirmed absence.
Its stopped child overlay was removed **before** its backing image. The existing
Production .31 is a different VM and its original/copy/overlay were excluded.
Source commits for all selected old Brake/Tire builds were present in their
owning repositories. Immediately before deletion, exact inode/device/type/size/
mtime and zero open handles were reconciled; no broad glob or root deletion ran.

## Allocation by category

| Category | Removed allocated bytes | GiB |
| --- | ---: | ---: |
| disk | 14,831,124,480 | 13.813 |
| manager-proof | 874,647,552 | 0.815 |
| old-vdp | 344,600,576 | 0.321 |
| old-service | 513,306,624 | 0.478 |
| old-service-build | 275,468,288 | 0.257 |
| temporary-build | 181,571,584 | 0.169 |
| temporary-fixture | 16,384 | 0.000 |

## Preserved and verified

- Original .33 and Production .31 images, canonical Factory copies and both
  running overlays; no VM stop/restart, Cloud mutation or new E2E run.
- VDP base inputs 1.0.16/2.0.0/3.0.0 and current .33 VDP21/22/23 packages.
- Brake build76d80e9 profiles V1/V2/V3 and releases9/10/11; Tire buildfc81a37
  profile V1 and releases8/9.
- Release continuity unchanged: VDP23, Brake11, Tire9. No version reset.
- Source/worktrees/Git, current native application/runtime, backend containers/
  volumes, secrets, DNS, Builder/download/sstate caches and compact evidence.
- No stale Cloud object, Subject, Unit Set, remote repository or branch was
  removed by filesystem housekeeping.

Post-cleanup `democtl image list` returns .31 and .33 with no catalog issues;
.32 is absent. No multi-gigabyte image was rehashed just for this observation.
At 10:25:41 UTC `democtl status all` reports Test PID47744 and Production
PID28620 still RUNNING, their overlays present, current selection Test and
native controller Safe Stop at 0 km/h. This is local observation; guest SSH and
Cloud access were NOT_REQUESTED and no new Cloud Online proof is claimed.
All 20 explicitly retained input/state paths were present.

Documentation quality gate passed after the receipt/plan updates: 182 Markdown
documents, 658 stable identifiers and 38 Mermaid diagrams. Solution and Platform
`git diff --check` passed. No commit/push was performed by this cleanup.

## Exact removed payload targets

`$WORKSPACE_ROOT` denotes the private parent directory containing the sibling
repositories and `demo-artifacts`. The execution used fully resolved absolute
paths; this notation only removes personal machine paths from public evidence.
Temporary paths below are their exact validated paths.

| Target | Type | Allocated bytes before removal |
| --- | --- | ---: |
| `$WORKSPACE_ROOT/aosedge-sdv-demo-qual-31/.local/demo-current/validation.qcow2` | file | 836829184 |
| `$WORKSPACE_ROOT/aosedge-sdv-demo-qual-31/.local/factory/oem-demo-factory.img` | file | 6997147648 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.32/main-qemuarm64.img` | file | 6997147648 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-service-prepare-recovery/aos-sm` | file | 108347392 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-clock-skew/aos-sm` | file | 108314624 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-service-update-teardown/aos-sm` | file | 108339200 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-5s/aos-sm` | file | 108171264 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-queued-recovery/aos-sm` | file | 108314624 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-factory-placeholder/aos-sm` | file | 108310528 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-stop-start/aos-sm` | file | 108224512 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-service-update-reconcile/aos-cm` | file | 105426944 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-comparison-20260912/aos-cm-without-patch` | file | 5599232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/runtime-proofs/cm-idle-full-status-20260913/aos_cm_app` | file | 5599232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/1.0.15/vdp-1.0.15-deployment-bundle.tar.gz` | file | 6615040 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/4.0.0/aosedge-vdp-component-4.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/4.0.0/vdp-4.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/4.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/5.0.0/aosedge-vdp-component-5.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/5.0.0/vdp-5.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/5.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/6.0.0/aosedge-vdp-component-6.0.0-linux-arm64.unsigned.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/6.0.0/vdp-6.0.0-deployment-bundle.tar.gz` | file | 6627328 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/6.0.0/vehicle-data-platform` | directory | 6639616 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/7.0.0/aosedge-vdp-component-7.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/7.0.0/vdp-7.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/7.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/8.0.0/aosedge-vdp-component-8.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/8.0.0/vdp-8.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/8.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/9.0.0/aosedge-vdp-component-9.0.0-linux-arm64.unsigned.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/9.0.0/vdp-9.0.0-deployment-bundle.tar.gz` | file | 6627328 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/9.0.0/vehicle-data-platform` | directory | 6639616 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/10.0.0/aosedge-vdp-component-10.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/10.0.0/vdp-10.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/10.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/11.0.0/aosedge-vdp-component-11.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/11.0.0/vdp-11.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/11.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/12.0.0/aosedge-vdp-component-12.0.0-linux-arm64.unsigned.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/12.0.0/vdp-12.0.0-deployment-bundle.tar.gz` | file | 6627328 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/12.0.0/vehicle-data-platform` | directory | 6639616 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/13.0.1/aosedge-vdp-component-13.0.1-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/13.0.1/vdp-13.0.1-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/13.0.1/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/14.0.0/aosedge-vdp-component-14.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/14.0.0/vdp-14.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/14.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/15.0.0/aosedge-vdp-component-15.0.0-linux-arm64.unsigned.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/15.0.0/vdp-15.0.0-deployment-bundle.tar.gz` | file | 6627328 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/15.0.0/vehicle-data-platform` | directory | 6639616 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/16.0.0/aosedge-vdp-component-16.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/16.0.0/vdp-16.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/16.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/17.0.0/aosedge-vdp-component-17.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/17.0.0/vdp-17.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/17.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/18.0.0/aosedge-vdp-component-18.0.0-linux-arm64.unsigned.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/18.0.0/vdp-18.0.0-deployment-bundle.tar.gz` | file | 6627328 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/18.0.0/vehicle-data-platform` | directory | 6639616 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/19.0.0/aosedge-vdp-component-19.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/19.0.0/vdp-19.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/19.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/20.0.0/aosedge-vdp-component-20.0.0-linux-arm64.unsigned.tar.gz` | file | 6619136 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/20.0.0/vdp-20.0.0-deployment-bundle.tar.gz` | file | 6623232 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/20.0.0/vehicle-data-platform` | directory | 6635520 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/1.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/1.0.0/service` | directory | 25190400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/2.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/2.0.0/service` | directory | 25206784 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/3.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/3.0.0/service` | directory | 25190400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/4.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/4.0.0/service` | directory | 25190400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/5.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/5.0.0/service` | directory | 25190400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/6.0.0/deployment-bundle.tar.gz` | file | 9568256 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/6.0.0/service` | directory | 25190400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/7.0.0/deployment-bundle.tar.gz` | file | 9756672 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/7.0.0/service` | directory | 25702400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/8.0.0/deployment-bundle.tar.gz` | file | 9756672 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/releases/8.0.0/service` | directory | 25702400 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/1.0.0/deployment-bundle.tar.gz` | file | 9093120 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/1.0.0/service` | directory | 24178688 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/2.0.0/deployment-bundle.tar.gz` | file | 9097216 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/2.0.0/service` | directory | 24178688 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/3.0.0/deployment-bundle.tar.gz` | file | 9097216 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/3.0.0/service` | directory | 24178688 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/4.0.0/deployment-bundle.tar.gz` | file | 9089024 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/4.0.0/service` | directory | 24178688 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/5.0.0/deployment-bundle.tar.gz` | file | 9097216 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/5.0.0/service` | directory | 24178688 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/6.0.0/deployment-bundle.tar.gz` | file | 9228288 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/6.0.0/service` | directory | 24498176 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/7.0.0/deployment-bundle.tar.gz` | file | 9228288 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/releases/7.0.0/service` | directory | 24498176 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/8bae83066df071f5cb3bf7791ab6dedc00843d3d/v1/output/rootfs` | directory | 25169920 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/8bae83066df071f5cb3bf7791ab6dedc00843d3d/v2/output/rootfs` | directory | 25169920 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/8bae83066df071f5cb3bf7791ab6dedc00843d3d/v3/output/rootfs` | directory | 25169920 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/81e6afc1563239c8d75fb7183a50546cde7ddc58/v1/output/rootfs` | directory | 25165824 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/bc0ed655d87297746955307695c3102881049316/v1/output/rootfs` | directory | 25186304 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/438cac887b7ef248f81b4dbf69285c89d903101d/v3/output/rootfs` | directory | 25698304 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/09358831a27330e9824cdea0cf6370506475e071/v1/output/rootfs` | directory | 25186304 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/09358831a27330e9824cdea0cf6370506475e071/v2/output/rootfs` | directory | 25186304 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/09358831a27330e9824cdea0cf6370506475e071/v3/output/rootfs` | directory | 25186304 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/builds/4deb4e32220525665c011afd4e9433aa65033670/v1/output/rootfs` | directory | 24174592 |
| `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/builds/1698ee4859fb66c210f386f485dad56234e37c15/v1/output/rootfs` | directory | 24174592 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/CMakeFiles` | directory | 13729792 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake-health-bootstrap` | file | 2207744 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_demo_mock_tests` | file | 2162688 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_health_application_tests` | file | 2306048 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_health_runtime_tests` | file | 2035712 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_health_v1_tests` | file | 1015808 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_health_v2_tests` | file | 1200128 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/brake_token_session_tests` | file | 962560 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/libbrake_health_runtime.a` | file | 4808704 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/libbrake_health_v1.a` | file | 1241088 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/libbrake_health_v2.a` | file | 1556480 |
| `/private/tmp/aos-mock-native.GLrY7Y/brake/native_inputs_tests` | file | 1052672 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/CMakeFiles` | directory | 7999488 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/libtire_health_runtime.a` | file | 5083136 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/native_inputs_tests` | file | 1114112 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/tire-health-bootstrap` | file | 1433600 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/tire_demo_mock_tests` | file | 1388544 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/tire_health_tests` | file | 1449984 |
| `/private/tmp/aos-mock-native.GLrY7Y/tire/tire_token_session_tests` | file | 1052672 |
| `/private/tmp/aos-native-brake-host/CMakeFiles` | directory | 20623360 |
| `/private/tmp/aos-native-brake-host/brake-health-bootstrap` | file | 1445888 |
| `/private/tmp/aos-native-brake-host/brake_health_application_tests` | file | 2306048 |
| `/private/tmp/aos-native-brake-host/brake_health_runtime_tests` | file | 2035712 |
| `/private/tmp/aos-native-brake-host/brake_health_v1_tests` | file | 1015808 |
| `/private/tmp/aos-native-brake-host/brake_health_v2_tests` | file | 1200128 |
| `/private/tmp/aos-native-brake-host/brake_token_session_tests` | file | 962560 |
| `/private/tmp/aos-native-brake-host/libbrake_health_runtime.a` | file | 4808704 |
| `/private/tmp/aos-native-brake-host/libbrake_health_v1.a` | file | 1241088 |
| `/private/tmp/aos-native-brake-host/libbrake_health_v2.a` | file | 1556480 |
| `/private/tmp/aos-native-brake-host/native_inputs_tests` | file | 1052672 |
| `/private/tmp/aos-native-tire-host/CMakeFiles` | directory | 10698752 |
| `/private/tmp/aos-native-tire-host/libtire_health_runtime.a` | file | 5083136 |
| `/private/tmp/aos-native-tire-host/native_inputs_tests` | file | 1114112 |
| `/private/tmp/aos-native-tire-host/tire-health-bootstrap` | file | 1056768 |
| `/private/tmp/aos-native-tire-host/tire_health_tests` | file | 1449984 |
| `/private/tmp/aos-native-tire-host/tire_token_session_tests` | file | 1052672 |
| `/private/tmp/brake-growing-build-0NXiVR/CMakeFiles` | directory | 12652544 |
| `/private/tmp/brake-growing-build-0NXiVR/brake-health-bootstrap` | file | 352256 |
| `/private/tmp/brake-growing-build-0NXiVR/brake_health_application_tests` | file | 786432 |
| `/private/tmp/brake-growing-build-0NXiVR/brake_health_runtime_tests` | file | 626688 |
| `/private/tmp/brake-growing-build-0NXiVR/brake_health_v1_tests` | file | 286720 |
| `/private/tmp/brake-growing-build-0NXiVR/brake_health_v2_tests` | file | 458752 |
| `/private/tmp/brake-growing-build-0NXiVR/libbrake_health_runtime.a` | file | 610304 |
| `/private/tmp/brake-growing-build-0NXiVR/libbrake_health_v1.a` | file | 192512 |
| `/private/tmp/brake-growing-build-0NXiVR/libbrake_health_v2.a` | file | 303104 |
| `/private/tmp/brake-studio-product-gate/CMakeFiles` | directory | 237568 |
| `/private/tmp/brake-studio-runtime-build/CMakeFiles` | directory | 21286912 |
| `/private/tmp/brake-studio-runtime-build/brake-health-bootstrap` | file | 1531904 |
| `/private/tmp/brake-studio-runtime-build/brake_health_application_tests` | file | 1495040 |
| `/private/tmp/brake-studio-runtime-build/brake_health_runtime_tests` | file | 1204224 |
| `/private/tmp/brake-studio-runtime-build/brake_health_v1_tests` | file | 815104 |
| `/private/tmp/brake-studio-runtime-build/brake_health_v2_tests` | file | 1007616 |
| `/private/tmp/brake-studio-runtime-build/libbrake_health_runtime.a` | file | 4734976 |
| `/private/tmp/brake-studio-runtime-build/libbrake_health_v1.a` | file | 2134016 |
| `/private/tmp/brake-studio-runtime-build/libbrake_health_v2.a` | file | 2744320 |
| `/private/tmp/tire-health-native-build/CMakeFiles` | directory | 8941568 |
| `/private/tmp/tire-health-native-build/libtire_health_runtime.a` | file | 4431872 |
| `/private/tmp/tire-health-native-build/tire-health-bootstrap` | file | 933888 |
| `/private/tmp/tire-health-native-build/tire_health_tests` | file | 1298432 |
| `/private/tmp/tire-native-2uwfIX` | directory | 16384 |

## Related evidence

After payload removal, only the following five verified empty directory shells
were also removed with non-recursive empty-directory removal:

- `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/1.0.15`
- `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/14d28ae0578cf4c84e7ec170a04ac4df4d29e5b4/v3`
- `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/brake/builds/14d28ae0578cf4c84e7ec170a04ac4df4d29e5b4`
- `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/builds/e3bdfa7011c4965022fcb9e8b47d91eab881505c/v1`
- `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/services/tire/builds/e3bdfa7011c4965022fcb9e8b47d91eab881505c`

- [Consolidation audit and open issues](factory-33-consolidation-audit-2026-09-13.md)
- [Current working baseline](current-baseline.md)
- [Scoped .33 E2E](factory-33-e2e-2026-09-13.md)
- [Active delivery plan](../planning/active/demo-studio-delivery-plan.md)

KUKSA permissions and the Cloud ordering workaround remain open. Cleanup does
not close product/visual acceptance, source publication or upstream review.
