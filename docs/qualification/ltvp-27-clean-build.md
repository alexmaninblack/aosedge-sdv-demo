<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP `.27` clean-build record

- Recorded: 2026-09-04
- Result: pass
- Purpose: reproduce the accepted `.27` factory implementation from pinned
  source after removing all prior Yocto `tmp` output

## Source identity

| Input | Revision | Tree | State |
| --- | --- | --- | --- |
| `aos-vehicle-platform` factory source | `72c0224ba65537bed41a6ca12a7bf3a9c07da194` | `b1e6d1b5ec32c996169d5f10057878f1195e2ec7` | clean |
| `aos_core_lib_cpp` | `60cb83535f773762c61ac5f544b31b7b88c502e3` (`v9.1.0`) | `747a1b50d8428b63423b9011669986f42fa4982e` | clean |
| `aos_core_api` | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` (`v9.1.1`) | `0bf4d8957355f2f0f33844452afbbdc3612ac19a` | clean |
| Rouge project manifest | SHA-256 `b9b49a575798f2bc4a532a794e77352ed21596677ef5aced4304db9e7a87f09e` | n/a | pinned |

The two AosCore directories passed a recursive comparison against their clean
Git checkouts. Their combined normalized source-tree SHA-256 was
`f976aca0ad7b9510a6ade547af56b54907e5447412221567c0ba03fabf332436`.

The effective `auto.conf` had SHA-256
`166cb85b68b0aeaf42f2d78de1a0fd348a079edd0f5b2da7a449379b92f7e3a8` and
set all of the following:

- `AOS_ROOTFS_IMAGE_VERSION:forcevariable = "6.1.1-maninblack.27"`;
- `BB_NO_NETWORK = "1"`;
- `BB_FETCH_PREMIRRORONLY = "1"`;
- the Service Manager `AOS_CORE_DIR` shown above.

## Clean procedure and result

Only `yocto/build-main/tmp` was removed. The shared downloads and sstate caches
were retained. The clean output was then produced directly with:

```text
bitbake aos-image-vm aos-image-initramfs
```

BitBake selected `DISTRO_VERSION=6.1.1-maninblack.27` and Platform revision
`72c0224`. It attempted 7,549 tasks; 7,510 came from valid shared state and all
remaining tasks succeeded. `aos-servicemanager` was unpacked, patched,
configured, compiled, installed, packaged and passed package QA during this
build. Both VM rootfs and initramfs passed image QA.

The clean deploy manifest contains the required AOS/KUKSA integration
packages, including `aos-servicemanager`, `aos-kuksa-auth-compat`,
`aos-kuksa-factory-integration` and
`aos-vehicle-data-provider-platform`. The rootfs reports
`VERSION="6.1.1-maninblack.27"`.

## Output identity

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| clean full-disk candidate | `6997147648` | `1ebbf03f99b98b441d585826e9ddf4509c2121db16b87a3698ae5d75f7954c65` |
| clean rootfs ext4 | `1073741824` | `6878e14f65d9952a8a529350ad6da23fdc40078239b18c2216f10243855652e0` |
| clean initramfs | n/a | `dba46255c914d7ae170c4628cc6e28245c8769cf94fed0c340d0121f5d1d1ee7` |
| clean kernel `Image` | n/a | `257a0312aec4db59834ce8aa20b09855bc097544d7a19b5a020d47e931e84de2` |

The full-disk and ext4 hashes are not expected to equal a prior assembly
because filesystem and GPT identity metadata are regenerated. Kernel and
initramfs hashes did reproduce exactly. The separate accepted canonical image
remains immutable at SHA-256
`dbc018cf31dc83accbca82cf26df0b3ca69c66d1135100db8d05552fd2744c56`.
Per the qualification plan, the repeated E2E cycle uses a new overlay backed
by that same canonical image, not by this clean-build comparison output.

The clean full-disk candidate has a GPT with exactly six partitions: two
256-MiB boot partitions, a 1-GiB root partition, two 512-MiB writable
partitions and one 4-GiB component partition.
