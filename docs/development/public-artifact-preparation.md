<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Public artifact distribution and maintenance

Reviewed developer dependencies are available through the pinned public
catalog. The [developer launcher](../getting-started/reproduce-demo.md)
requires no Google login, publisher credentials or manual binding files.
Operator DMG delivery is independently selected by the
[launcher catalog](../../workspace/launcher-catalog.json) and release descriptor.

The [public companion folder](https://drive.google.com/drive/folders/1DJQkMfbLICXe4LhROdg6pcqUHzp8Tvp7)
contains dependency archives, the catalog and supplementary source/notices.
Public test access is authorized; that is not blanket redistribution clearance
or fresh-source-build qualification. The underlying byte/source locks remain
immutable even when delivery locations change.

## Integrity and content boundaries

Verify each archive against its reviewed identity at the real consumer.
Reuse compatible verified caches. Exporters preserve exact inventory, bytes,
modes, source correspondence and manifests; failed content is not accepted
by replacing its expected checksum.

No credentials, provisioned identity, live VM, raw run data, restricted Unreal
source or build cache belongs in a public package. Retain independent content,
secret-exclusion and producer/source checks before publication. A bounded
filename/marker scan is not semantic inspection of every binary/cooked asset.

Completed copy, acquisition and activation diaries are available in Git
history. They are not current maintainer instructions or extra user steps.

## Outstanding redistribution obligations

The source/notice companion retains upstream archives, recipes, patches,
notices and provenance. It is **partial corresponding-source preparation**,
not a complete license-compliance verdict. Keep these review boundaries:

- Reconcile the full SDK/source/notice mapping, including linked libraries,
  recipe patches and build/relocation transformations; a matching version or
  header alone is insufficient.
- Match CARLA/cooked-asset attribution, provenance and modifications to actual
  shipped content. CARLA code, assets and Unreal terms are distinct.
- Retain Unreal third-party notices and determine applicable product/Engine
  Tools distribution conditions from the actual packaged/linked modules, not
  filenames or Editor descriptors.
- Recover and review the applicable terms for the packaged Metal Shader
  Converter binary. Apple header acknowledgements do not establish its binary
  redistribution terms.
- Adopt appropriate recipient terms and integrate required notices/source
  access with actual distributed media; a draft companion is not an end-user
  agreement.

The owner excluded the separate Factory license/source-record audit from this
preparation, relying on known upstream AosCore/Linux licensing. That scope is
`OMITTED_BY_OWNER`, not a passed audit. Preserve notices, source references,
image identity and credential-protection checks; do not request old SSD/Yocto
reports or rebuild Factory for the omitted audit.

Payload changes require a new reviewed dependency generation. Do not overwrite
existing archives or silently reseal old locks to resolve an obligation.
Consult the [licensing policy](../governance/licensing-and-copyright-policy.md)
and [third-party notices](../../THIRD_PARTY_NOTICES.md).

## Maintainer catalog controls

These controls are optional release-owner maintenance, not route B prerequisites.
Prepare public catalog records from an existing verified receipt and approved
URL mapping:

```sh
python3 -B scripts/preparation-catalog --help
python3 -B scripts/sync-preparation-catalog
python3 -B scripts/sync-launcher-pins --write
python3 -B scripts/sync-launcher-pins --check
```

The catalog generator's `--public-links` preserves byte/source pins and emits
a distinct immutable public record; it neither uploads nor widens permissions.
Publish the small stable `release-index.json`, review its URL/record digest
into `PUBLIC_PIN` in `scripts/developer_catalog.py`, then regenerate the
standalone preparation script and launcher together. Downloaded old launchers
retain their old pins; they are not updated in place.

For explicit private-input maintenance only, `scripts/prepare-macos.sh
--private-inputs` uses the reader's authorized Google account;
`--advanced-inputs` also asks for private binding paths. Neither is a fallback
after public-access failure. Never request the publisher's credentials as a
new user's prerequisite.

Use the [release campaign](release-campaign.md) for source, immutable DMG and
option A promotion. Routine delivery uploads once and checks remote identity,
size, checksum, parent and access metadata. Verify bytes on the actual consumer;
do not download gigabytes back merely to retest the storage provider.

## Primary references

- [Unreal Engine EULA](https://www.unrealengine.com/eula/unreal)
- [CARLA license](https://github.com/carla-simulator/carla#license)
- [QEMU GPLv2](https://www.qemu.org/license-gpl-2/)
- [Yocto license maintenance](https://docs.yoctoproject.org/dev-manual/licenses.html)

These sources identify obligations. This maintenance guide is not a legal
opinion or evidence that all public-distribution obligations are closed.
