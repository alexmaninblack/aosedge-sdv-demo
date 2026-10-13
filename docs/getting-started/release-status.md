<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Select a release and obtain access

The SDV Lab is an engineering preview. Its selected operator DMG and developer
inputs have reviewed public download links; restricted source access and Aos
Cloud credentials remain separate. The preview is not notarized or a fully
qualified public release.

## Which package do I have

| Selection | Use and evidence |
| --- | --- |
| Selected option A preview | The [launcher catalog](../../workspace/launcher-catalog.json) supplies the version, status, approved identity and download link. The selected Dropbox media passed anonymous M1 download, checksum/signature, Setup handoff and installed/open reconciliation. It reused an existing Test; native Setup button-input and clean-first-user acceptance remain open. |
| `1.2.0-rc.1`, earlier source-Factory build | Retained build candidate, distinct from the selected Presenter preview. Assembly and its private delivery passed; its own fresh-environment reproduction, installation and live qualification remain open. Historical input/producer pins remain unchanged. |
| `candidate/kit028-setup042` | Published historical source checkpoint for the earlier installer. Its 98-step scripted M1 evidence and open native gates remain in the qualification baseline. It does not contain the newer reproduction commands. |
| `demo-v1.1` | Earlier Factory .39 source return point, not the current installer or new build candidate. |

Different engineering DMGs can share a product version or filename. A filename
alone is not an identity. Route A follows `operatorDescriptor` in the catalog;
its size, checksum and application manifest must match. The retained
[source-Factory descriptor](../../workspace/releases/1.2.0-rc.1-source-factory-delivery.json)
describes different bytes and must not substitute for the selected preview.

`main` is the current documentation and development entry in all nine maintained
demo repositories, including our CARLA and restricted Unreal forks. Historical
branches remain available; there is no separate maintenance branch to find for
the latest README or current development work.

`sdv-lab-v1.2.0-rc.1` is the published engineering source checkpoint after
the Dropbox consumer check. It does not claim completed native first-use
acceptance. `sdv-lab-v1.2.0` remains reserved for a future qualified release.
To reproduce the earlier R2/R3
candidate, select root checkpoint
`dbfd542d38f3730f151f43dd303af94e4902c74d` and its frozen producer ancestors.
That checkpoint is included in `main`; all six component README updates are
also published on their respective `main` branches. Moving current work to
`main` does not change the existing candidate's exact source pins or bytes.
Source availability does not supply Cloud credentials or restricted source
access, or prove fresh-environment reproduction. The
[qualification baseline](../qualification/current-baseline.md) preserves older
installed results; those results are not promoted to new bytes.

## What the release owner supplies

- **Operator:** the reviewed public DMG link in the source-owned catalog,
  matching immutable descriptor, and complete Setup plus Runtime Kit, with
  supported host and remaining limitations identified. Route A obtains and
  verifies these automatically; no storage-provider login is required.
- **Developer:** the exact root revision and available producer/component
  commits, and approved access to the release catalog plus simulation and
  vehicle/Factory inputs. The preparation wizard obtains the compatible
  references automatically; users do not supply JSON binding files.
- **Both:** instructions for access to the intended Aos Cloud staging instance.
  The first-demo topology uses one OEM and one associated SP for two separate
  services. Credentials and provisioned identities are never included in media.

Dropbox/Google Drive delivery and Aos Cloud access are separate. A public
download does not enroll an OEM/SP or grant Cloud publication rights. A Git
clone does not grant restricted Unreal source access.

If an item is missing, request that specific item from the release owner.
Do not hunt for an old kit, copy private keys or substitute an unreviewed
dependency. Credentials and private account identifiers stay out of this guide.

## Verify once at the consumer

Download the complete DMG once on the installation Mac. Compare size and SHA-256
with the descriptor/index, then let Setup verify its matching payload.
On macOS, `shasum -a 256 /path/to/the-downloaded.dmg` computes that checksum.
Keep a verified local copy for repeats; do not transfer it back and forth solely
to test Drive. Dedicated transport tests are for changed transfer code or a
concrete integrity problem.

Continue with [installation](installed-preview-cloud-first-use.md),
[developer build](reproduce-demo.md), or the gated [full-source route](full-source-build.md).
