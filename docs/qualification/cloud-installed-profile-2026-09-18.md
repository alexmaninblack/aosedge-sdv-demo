<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cloud-confirmed installed VDP profile

Date: 18 September 2026. Scope: authorized P2 read projection in the
[versioned-service work packet](../planning/active/work-packets/versioned-service-observability.md).
Source: uncommitted working-tree increment on `4d1d2a8`; existing unrelated
changes preserved. This is not a full P2 or end-to-end completion report.

## Changes

- Native Aos Cloud remains installation/runtime/resource authority. The
  Presenter binds a VDP profile only through exact Cloud/OEM/Unit identity,
  installed version UUID, READY publication/deployment, successful upload and
  consistent prepared/signed receipts, and validated package provenance/hash.
- Overview and component details receive the same projection. A local prepared
  candidate or job cannot substitute for an installed profile. Unknown profile
  preserves the installed release and does not restart the guide at V1.
- A processing successor cannot starve reconciliation of the installed
  release's receipt after Presenter startup. Publication cache and in-flight
  keys include the selected Cloud/OEM/run/Unit; shared inventory cache also
  includes the selected domain.
- Package inspection is cached by immutable file identity and timestamps.
  No repeated package hashing while unchanged; no new guest read or timer.
- Successful supplementary null fields produce explicit `notices`. Critical
  inventory/group-service absence, errors and stale reads remain `problems`.

See the [projection and notice contract](../architecture/demo-control-cloud-observation.md).

## Selected staging proof

Read-only reconciliation completed at **13:57:03 UTC** through the configured
OEM and existing democtl workers. No signing, upload, guest access or lifecycle
operation was requested.
The final source revision was rechecked at **14:06:57 UTC**, with the same
installed-profile result and current Unit connectivity.

| Fact | Observed |
| --- | --- |
| Cloud | `aws-stage.epmp-aos.projects.epam.com` |
| Current Test Unit | `a842a53e-a30b-481c-8747-f73a96c351d7` |
| Unit connectivity | `ONLINE` |
| Installed VDP | `79.0.0` |
| Installed Cloud version UUID | `d869516c-0956-45c9-ac3f-2732d874a7e4` |
| Recorded deployment | `ea5719d0-6654-4b1c-b9ae-aae3318f0b1c` |
| Publication | `READY`; bundle `done`; version `Ready` |
| Bound functional profile | `CURRENT`, `v3`, `CLOUD_INSTALLATION_AND_PACKAGE` |
| Brake service | `59.0.0`, matching instance version, `active` |
| Tire service | `34.0.0`, matching instance version, `active` |
| Material observation problems | None |
| Supplementary absences | Layers, reported Subjects, protected default Subject service list |

The initial asynchronous read correctly left the profile unknown until its
existing publication read completed; consuming that result established the
binding. No retry of a mutation or invented completion was involved.
Earlier exact catalog/installed reads found no usable functional-profile
field in Cloud metadata. Existing local package inspection matched its
prepared unsigned digest and declared V3 profile, 23 read paths and two
advisory endpoints. These counts describe the package, not live healthy input.

## Verification

Results recorded after the source changes; deterministic fixtures are not
live deployment/vehicle proofs.

| Gate | Result |
| --- | --- |
| Installed-profile resolver | 8 tests passed |
| Cloud observation normalization | 29 tests passed |
| Studio Cloud reader | 10 tests passed |
| Unit lifecycle regression | 40 tests passed |
| Presenter HTTP/security regression | 36 tests passed; isolated sockets |
| Frontend unit suite | 161 tests passed |
| Frontend browser suite | 99 tests passed, isolated port 18070 |
| Typecheck and isolated production build | Passed; `/private/tmp/aos-cloud-profile.3s7vjT` |
| Selected staging installed-profile reconciliation | Passed, as above |

Total: 123 focused Python tests, 161 frontend unit tests and 99 browser tests.
The unchanged concurrent-read and slow-publication regression gates pass;
the final scheduler preserves parallel reads rather than adding their latency.

Negative coverage includes wrong Cloud/OEM/Unit/version UUID, pending or failed
publication, inconsistent receipt/hash/profile, changed or missing artifact,
stale versus Offline, optional versus critical absence and no fallback to local
prepared candidates. The two harness-only sandbox failures (test-cache writes
and loopback sockets) were rerun with required access; no product security or
assertion was weakened to accommodate them.

## Preserved state and remaining work

No VM, CARLA, Driving Control or live Presenter restart; no package publication,
service reset, model-threshold change or Factory rebuild. Production is untouched.
The running Presenter assets were not replaced; activation/visual review is
separate from this isolated build and fresh-reader proof. No credential material
is included in source or evidence. No cleanup or cache deletion was performed.

### Operator-authorized activation — 18 September, 14:13 UTC

The operator subsequently requested immediate Presenter activation. The idle
server reported no active or uncertain operation. Only `democtl ui stop` /
`ui serve` were used; the verified isolated build was copied into the existing
served `dist` directory. The previous build is retained at
`/private/tmp/aos-presenter-before-update.R596jX/dist` for local rollback.
The served entry-point build ID is
`b54cf8a815645a8edca5478bd83e4192f299bdf72fe25db236119b60dbb30d82`.

Live browser inspection confirmed current Test, Online, VDP V3 / 79.0.0,
Brake V3 / 59.0.0 and Tire V1 / 34.0.0; the Cloud card shows installed software
and update state, with identity accents and AosCore branding visible.
VM, CARLA, Driving Control and the native Presenter window host retained their
original process IDs. The existing native host's idle build/session reload
mechanism was preserved; no window-composition command was issued.
Native vehicle telemetry remained LIVE. This is activation and visual smoke,
not new service-function/E2E qualification.

Service-local capability validation and automatic recovery after VDP changes,
the versioned function/episode observation protocol, backend/consumer migration,
native motion controls and preserved-Test/clean-cycle qualification remain open.
Cloud installed/active does not mean that valid telemetry, an assessment or an
applied advisory currently exists. Do not claim the Brake/Tire functional problem
closed by this inventory/provenance increment.
