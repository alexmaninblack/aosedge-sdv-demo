<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Product and build definitions

Start with [build-definition.json](build-definition.json). Schema versions describe
metadata, not installer releases. Validation requires no Git history or network.

| Purpose | Authority |
| --- | --- |
| Install and run (A) | [Launcher catalog](launcher-catalog.json) and [delivery descriptor](releases/delivery.json) |
| Build the demo (B) | [Developer selector](current-developer-build.json) and [producer plan](releases/build-plan.json) |
| Current maintenance owners (no release selection) | [Repository map](repository-map.json) |
| Vehicle preparation firmware and unsigned VDP bases | [Vehicle build inputs](inputs/vehicle-build-inputs.json) |
| Source revisions and access | [Source lock](inputs/sources.lock.json) |
| Runtime manifest identities | [Runtime inputs](inputs/runtime-inputs.lock.json) |
| Prebuilt and independently rebuilt controller images | [Controller images](inputs/controller-images.lock.json); these have distinct digests |
| Reviewed service binaries | [Service inputs](inputs/service-inputs.lock.json) |
| Component graph and build profiles | [Build policy](inputs/build-policy.json) |
| Public package discovery | [Dependency catalog](dependencies/catalog.json); all five payloads are on Dropbox |
| Exact existing cache/prepared-workspace namespace | [Cache compatibility](inputs/cache-compatibility.json) |

Names describe roles. Versions and immutable revisions remain inside records.
The two files in `releases/` select build and delivery independently; neither
folder is an archive of attempts. Historical checkpoints remain in Git history,
not as prerequisites in a clean checkout.

The default `scripts/workspace-doctor` consumes the current repository map;
it does not require Unreal Editor, old launchers or a runtime VM. It checks
local tracking state without fetching. Optional simulator source inspection is
explicit. `repositories.json` and its schema remain hash-bound compatibility
inputs of existing build/payload definitions, not the current maintenance map.
Do not delete or rewrite them while that product depends on their exact bytes.

The former Stage 0 machine-observation report is no longer a build input.
Vehicle preparation reads the current firmware/VDP definition and the service
input lock; host observations, obsolete tool versions and copied service pins
do not participate. This source migration does not modify a frozen producer
checkout, completed recipe receipt, selected DMG or existing cache namespace.

The cache compatibility record preserves exact existing namespaces and retained
input provenance without rewriting receipts, relabeling artifacts or inheriting
qualification. Its old storage label is not the current product identity. A
changed input closure requires an explicitly reviewed successor namespace; the
projection tool refuses automatic rebinding. Frozen producer checkouts retain
their own historical files and are not rewritten during source maintenance.

```sh
python3 -B scripts/validate-release-definition
python3 -B scripts/sync-workspace-inputs --check
python3 -B scripts/sync-preparation-catalog --check
python3 -B scripts/sync-launcher-pins --check
```

After an authorized metadata edit, use `scripts/sync-workspace-inputs --write`,
then `scripts/sync-preparation-catalog` and `scripts/sync-launcher-pins --write`.
Review all projections. These commands never build or publish. Existing package
names and bytes stay unchanged; consumers still check their exact manifests and
hashes. See the [reproduction contract](../contracts/release-reproduction/README.md)
and [current baseline](../docs/qualification/current-baseline.md).
