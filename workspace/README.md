<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Product and build definitions

Start with [build-definition.json](build-definition.json). Its schema version
is internal; it is a current build selection, not a new installer release.

| Purpose | Authority |
| --- | --- |
| Install the selected demo (A) | [Launcher catalog](launcher-catalog.json), which selects an immutable operator descriptor |
| Build the demo and installer (B) | [Developer selection](current-developer-build.json), which pins the reviewed producer plan |
| Prepared simulator and controller image | [Simulator lock](dependencies/carla-macos-arm64-r1.lock.json) and [controller/input lock](dependencies/developer-factory41-r1.lock.json) |
| Source roles and original portable inputs | The exact compatibility base selected by the current build definition |
| Input/image/package verification | Retained records under `checkpoints/` and `releases/` consumed by existing adapters |

The current definition verifies the unchanged compatibility base, its source,
artifact and dependency closure, both independent selections and maintained
documentation. Historical prose is referenced by immutable Git revision/path
and SHA-256; it is not restored or required in the current source tree.

The compatibility base keeps existing cache, prepared-workspace, producer and
archive identities. Old dates and kit numbers in these machine inputs do not
select an old operator DMG. They are not spare builds or an archive directory.
The source-role map also retains legacy host-launch fields consumed by existing
adapters; ordinary installed use does not require Unreal Editor.

From the integration checkout, inspect without building:

```sh
python3 -B scripts/validate-release-definition
python3 -B scripts/validate-release-definition --historical-evidence
```

The second command additionally needs the declared local Git objects; it never
fetches or writes old reports. Ordinary validation works from a root-only source
archive without those objects. Neither command qualifies a build or release.
See the [reproduction contract](../contracts/release-reproduction/README.md)
and [current product baseline](../docs/qualification/current-baseline.md).
