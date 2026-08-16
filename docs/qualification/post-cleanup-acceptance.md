<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Post-Cleanup Acceptance

- Accepted: 2026-08-16
- Pre-cleanup checkpoint: `ea75c58`
- Cloud mutation: none
- Provisioning mutation: none
- Release upload, signing, assignment, or rollback: none

## Result

The reviewed repository migration and local housekeeping plan is complete.
Free host storage increased from approximately `260 GiB` to `287 GiB`, a
measured recovery of approximately `27 GiB`. All retained dependencies and
identities passed the required post-cleanup regression.

## Retained Operational State

- CARLA `Build-ego-runtime-m4`, `Build-macos-client-v3`, Python environment,
  active VISS TLS material, Unreal editor output, and generated keyboard app;
- the Main and validation provisioned overlays, private recovery checkpoints,
  provisioning locks, and saved SSH host keys;
- the official AosVM `6.1.0` base image;
- the complete unsigned `.11` rootfs candidate and its repaired, checked
  bootstrap qualification overlay;
- the compact `.1` and `.2` FOTA candidates;
- one verified provider `0.2.0` build, including signed bundle
  `30802d1bcb88a5954cf1e9c6c17573b527efe4f2a62ca3c0c83459f8a2fe35db`
  and layer
  `baf1c29c9264b8f2422dc155540c3b22716bb43d5f80c1cfeb3cc9529f0bf3cb`;
- the provider wheelhouse and the complete `62 GiB` incremental Yocto builder.

The `.11` bootstrap overlay now resolves its backing path in the current
repository and passes `qemu-img check`. A private clone checkpoint made before
the metadata-only path repair remains outside Git.

## Retired Raw Images

Each raw image was `6,997,147,648` bytes. No retained overlay referenced any of
them when they were removed.

| Retired image | SHA-256 |
| --- | --- |
| `.2/main-qemuarm64.img` | `155db230d85824d835ddd76bcfb7a70eafeaf54b7cce1e9dff957be41cccabd2` |
| `.10/main-qemuarm64.img` | `a39d4c97b9a5e28e372b6b44ec654308b6b1d85a765be752deed1d47e57630c8` |
| `upstream/main-qemuarm64.img` | `cc5a14f3ed60bdaa9ad16017d0006ced66aa2670b8f3b9aa498608570fb9e3ee` |

## Retired Iteration Evidence

The following directory digests are SHA-256 values of sorted lines containing
each file SHA-256 and repository-relative path. They retain an immutable
fingerprint without retaining reproducible payloads.

| Directory | Approximate bytes | Tree-manifest SHA-256 |
| --- | ---: | --- |
| `fota-r6-1-5` | `193,564,672` | `0114dd66d01e34dfa81107f24050c1f8ed73383e281fe74ad98ea652f2d48a8f` |
| `fota-r6-1-5-accepted-e972` | `193,564,672` | `009eb2b7fbaa96986e65291f260498aabb34d2c9b33de8c46e819ef3c2f66dc3` |
| `fota-r6-1-5-final` | `193,564,672` | `37e553846339f1aeae197abab121008f402431b7a740bb1bc1a3b515cb89305d` |
| `qualification` | `205,320,192` | `9197b22dfb0c9eb5c57a21ae64fe5249e0ede228487e1e146bd0736624976a99` |

Standalone side-load and policy test binaries were reproducible experimental
outputs. Their retired digests are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `side-load-launcher-12b09c6.bin` | `67,584` | `55dc2e826d639f8434785f54a3dd69e51beef89d6e9c07229718bed72952a071` |
| `side-load-launcher-7cd8de3.bin` | `67,584` | `9f0fcf32c38e57c422230e1f79a32d66a880836bac4f2eb491f949518c46132c` |
| `side-load-policy-12b09c6.bin` | `208,428` | `a1efd6434642210a09a80170a19830b63a6601871d1c32ef7e6f1fd4e3cba2e1` |
| `side-load-policy-7cd8de3.bin` | `11,282` | `c30f3a06fa9febad02fccdbc1ddd916667fada4f6eac2a4caacdec66f7452545` |
| `side-load-policy-r61-runtime-delta-v2.bin` | `11,912` | `0e6f39cf3f799b2455d1037d6983bb632a692618cd549bcc31a26c3c82aba101` |
| `side-load-policy-r61-runtime-delta.bin` | `11,808` | `6e5c2a3bd08778e650b7abfcce7790da1ad80ae4e2cf508300eb4d8066ea4673` |
| `vehicle_data_provider-getcap.pp.bin` | `208,724` | `8ac9637f2ee599e2316a88d6b5b3e56beb329da30b421afd06f1cd54c3cf58a6` |

Other retired state consisted of superseded CARLA and Vehicle Gateway build
directories, duplicate provider A/B builds, obsolete disposable qualification
overlays and credentials, old raw run logs, macOS metadata, and the generated
Unreal configuration containing a local token. The Unreal path now has a
targeted local Git exclusion and no working-tree warning.

## Post-Cleanup CARLA Regression

The first post-cleanup smoke run verified cold startup, Manual, Autopilot, live
VISS telemetry, and the dashboard. A focused repeat corrected an initially too
short test wait and proved that Safe Stop reached stationary state before
shutdown.

| Observation | Result |
| --- | --- |
| Final retained run | `20260816T173914.843Z-0717a83e` |
| CARLA RPC ready | `25.45 s` |
| Vehicle ready | `26.32 s` |
| First VSS frame | `26.66 s` |
| Dashboard ready | `27.16 s` |
| Keyboard ready | `27.32 s` |
| Maximum speed | `19.40 km/h` |
| Final speed | `0.0023 km/h` |
| Final mode | Safe Stop |
| Simulation and dashboard delivery | stable `30 Hz` and `4 Hz` |
| Dashboard events | `453`, live connection, no failure |
| Shutdown | controller and keyboard exit codes `0`; owned simulator stopped |

## Post-Cleanup AosVM and Repository Regression

- Main identity remained
  `55e05719489369c03a6ad7c4934d72611b30bcf0715b09a90a0543c9434b69fa`;
- validation identity remained
  `0df9a062ba9df85726b6aecf66cf960964d1bc922d8d3fb0b871100a66a8de86`;
- both Units remained provisioned and Online with one primary Main Node;
- the incremental builder passed its AArch64 smoke test;
- workspace doctor reported `0` errors and `0` warnings;
- platform, service, and solution tests passed: `35`, `4`, and `81`;
- quality, component-lock, dependency-boundary, and REUSE gates passed;
- all six Git working trees were clean.

The cleaned workspace is the accepted baseline for the next design iteration.
