<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Select a release and obtain access

The SDV Lab is an engineering preview for approved testers. Source is public;
large packages and restricted dependencies are delivered privately. There is
no qualified public release or universal one-click installer yet.

## Which package do I have

| Selection | Use and evidence |
| --- | --- |
| `1.2.0-rc.1`, source-Factory build | New build candidate. Assembly and private delivery passed; fresh-environment reproduction, installation and live qualification remain open. The developer build plan retains this candidate's exact input/producer pins; current host preparation uses root main. |
| `candidate/kit028-setup042` | Published historical source checkpoint for the earlier installer. Its 98-step scripted M1 evidence and open native gates remain in the qualification baseline. It does not contain the newer reproduction commands. |
| `demo-v1.1` | Earlier Factory .39 source return point, not the current installer or new build candidate. |

Two engineering DMGs have the `1.2.0-rc.1` name. A filename alone is not an
identity. The selected source-Factory media must match the
[delivery descriptor](../../workspace/releases/1.2.0-rc.1-source-factory-delivery.json):
**14,162,601,112 bytes**, SHA-256
`f2b3d68d9dd4bd084d9fa199cc8053190a0466fb10ee3c5ecf024f877d4de82d`.
Do not substitute the earlier same-named candidate.

`main` is the current documentation and development entry in all nine maintained
demo repositories, including our CARLA and restricted Unreal forks. Historical
branches remain available; there is no separate maintenance branch to find for
the latest README or current development work.

`sdv-lab-v1.2.0-rc.1` and `sdv-lab-v1.2.0` are accepted future tag names,
not tags created by this documentation. To reproduce the existing R2/R3
candidate, select root checkpoint
`dbfd542d38f3730f151f43dd303af94e4902c74d` and its frozen producer ancestors.
That checkpoint is included in `main`; all six component README updates are
also published on their respective `main` branches. Moving current work to
`main` does not change the existing candidate's exact source pins or bytes.
Source availability does not
supply the private build inputs or prove fresh-environment reproduction. The
[qualification baseline](../qualification/current-baseline.md) preserves older
installed results; those results are not promoted to new bytes.

## What the release owner supplies

- **Operator:** the approved private Drive link, matching release index and
  complete DMG containing Setup plus its Runtime Kit, with supported host and
  remaining limitations identified.
- **Developer:** the exact root revision and available producer/component
  commits, release index, and two private Drive binding files for the declared
  simulation and vehicle/Factory inputs.
- **Both:** instructions for access to the intended Aos Cloud staging instance.
  The first-demo topology uses one OEM and one associated SP for two separate
  services. Credentials and provisioned identities are never included in media.

Google Drive and Aos Cloud access are separate. An approved Drive link does
not enroll an OEM/SP or grant publication rights. A Git clone grants neither
private binary access nor restricted Unreal source access.

If an item is missing, request that specific item from the release owner.
Do not hunt for an old kit, copy private keys or substitute an unreviewed
dependency. Account and private file identifiers stay in the approved handoff,
not in this public guide.

## Verify once at the consumer

Download the complete DMG once on the installation Mac. Compare size and SHA-256
with the descriptor/index, then let Setup verify its matching payload.
On macOS, `shasum -a 256 /path/to/the-downloaded.dmg` computes that checksum.
Keep a verified local copy for repeats; do not transfer it back and forth solely
to test Drive. Dedicated transport tests are for changed transfer code or a
concrete integrity problem.

Continue with [installation](installed-preview-cloud-first-use.md),
[developer build](reproduce-demo.md), or the gated [full-source route](full-source-build.md).
