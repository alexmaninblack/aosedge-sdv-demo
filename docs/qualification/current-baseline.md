<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current demo baseline

- Status: engineering candidate; full native E2E and external distribution open
- Version: 2.0
- Prepared: 2026-10-07
- Owner: SDV Lab integration
- Source checkpoint: `candidate/kit028-setup042`

The current implementation is **Kit028 / Setup042 / Factory .41**.
`demo-v1.1 / Factory .39` remains a historical return point, not the current
installer. HLA 1.8 is a document version, not a demo release number.
This page reconciles retained evidence; it is not a fresh observation of a
running Mac, VM or Cloud Unit.

The later source-Factory `1.2.0-rc.1` build candidate has separate media and
build/delivery evidence, not inherited installed qualification. Use
[release selection](../getting-started/release-status.md) to choose between
them. This page retains the exact Kit028 installed evidence and original hashes.

## Immutable Factory

| Item | Selected candidate |
| --- | --- |
| Complete media | `AosEdge-SDV-Lab-Kit028-Setup042.dmg` |
| Media size | 14,150,764,550 bytes |
| Media SHA-256 | `27c4dbcac02c5cefcd3f20c75d7e51e3d54ec9f631bbc48e8d58839ea8e67236` |
| Runtime kit manifest SHA-256 | `1cb2628a3c358d685441644b500a94598c826f976b0bcff13ab5e7144754fbef` |
| Factory | `6.1.1-maninblack.41/main-qemuarm64.img` |
| Factory SHA-256 | `361c187374469f4a97b3b9c74cb755ce432bc5287fb19ccd2f6bfb9c3eb46769` |
| Setup signing | Local Apple Development; not notarized |
| Installed topology | One Test, one OEM, one associated SP; independent Brake and Tire services |

The [source return point](kit028-setup042-source-publication-2026-10-05.md)
and [source lock](../../workspace/checkpoints/installer-kit-028-source-lock.json)
bind the cross-repository commits and original build receipts. The
[Factory checkpoint](../../workspace/checkpoints/factory-41-candidate.json)
owns image provenance. A source tag restores source, not private credentials,
images, release ledgers or provisioned state. Artifact receipts remain immutable.

## Qualified behavior and later corrections

The [candidate checkpoint](../../workspace/checkpoints/installer-kit-028-candidate.json)
and [M1 journey](m1-live-journey-2026-10-03.md) record **98 passed installed
scripted steps on 4 October**. They cover the installed product owners, not
a claim that all those steps were performed through the native UI.

- Sequential VDP releases 134/135/136 (V1/V2/V3), Brake 112/113/114
  (V1/V2/V3), then Tire 60 (V1), with real products and advisory observations.
- Independent Reset Driver Advisory with retained history, and Return to road.
- External OFF for 302.807 seconds, continued local operation, and queued
  delivery after ON.
- Same-identity ignition and new products from both services after boot.
- Normal shutdown with no owned processes/listeners; Docker Engine preserved.
- Partial native proof: Open demo, correct three-window placement, Connect
  into stationary Manual, both backend inputs receiving, retained advisories
  and observed Autopilot movement. This is not a full native journey.

These allocated release numbers identify that run, not inputs to reuse in a
new run. Demo Control allocates new numbers and publishes one version at a
time. Historical candidate successes are not carried forward automatically.

Factory .41 includes retained AosCore corrections and source-timestamp
preservation in KUKSA VAL v1. Current service sources include input/credential
renewal continuity and Tire persistence recovery. Tire packaging requests
600 DMIPS through native signed metadata; the fixed-load isolation experiment
is still not implemented. See [implemented architecture](../architecture/current-implementation.md)
and [protocol status](../../contracts/implementation-status.md).

## Current qualification limitation

**Full E2E: NOT_COMPLETE.** Four candidate gates remain open:

1. Moving-SOTA qualification on this candidate.
2. Native secure-token field entry (API/worker enrollment is not that UI proof).
3. Complete native operator journey.
4. Installation interruption and repair on the target host.

Opening Presenter does not power on a previously stopped retained controller.
The 4 October native review needed separately recorded engineering restoration;
there is no native Power on action in the current Studio lifecycle. Do not
describe that restoration as native first-use or cold-resume acceptance.

Load-sensitive brief readiness transitions and **VDP-TIMEOUT-01** are explicitly
deferred, not repaired by changing freshness limits. **D4-023** fixed CPU-load
worker/control, complete calibration/negative matrices, nonempty-outbox power
loss and broader production/dual-provider qualification remain separate.
Host laptop sleep/wake and external-SSD tests are excluded from this M1
internal-disk campaign; controller ignition does not qualify laptop sleep/wake.

## Current boundaries

The complete DMG contains Setup and its matching Runtime Kit. It is an
engineering preview, not a finished one-click wizard or a notarized public
release. The [installation guide](../getting-started/installed-preview-cloud-first-use.md)
describes actual buttons and prerequisites. Operators do not compile Unreal
or CARLA. Developers use the [source reproduction guide](../getting-started/reproduce-demo.md).

The last recorded M1 disposition on 4 October is **ready for manual installation**:
the owned Test was retired through normal lifecycle cleanup, old installations
were removed, and the verified DMG was delivered without launching Setup.
The earlier successful Test is therefore not still running. Credentials,
compact evidence and development rollback were preserved. This dated record
does not assert the machine's state today.

This documentation revision changes no runtime, Cloud object, published release,
artifact, security policy or qualification verdict. Video material is excluded.

## Historical source audit — 23 September

The [demo-v1.0 return point](demo-v1.0-return-point.md) and
[publication/cleanup receipt](demo-v1.0-publication-cleanup-2026-09-23.md)
retain that source and storage history. The later
[demo-v1.1 return point](demo-v1.1-return-point.md) retains Factory .39,
its [ignition](factory-39-ignition-2026-09-24.md),
[offline](factory-39-offline-2026-09-24.md) and
[cleanup](factory-39-cleanup-2026-09-24.md) evidence. Those inventory statements
apply to their dates, not to the current kit.

## Dated operational summary — 20 September

See the [timing/UI E2E record](presenter-ui-timing-e2e-2026-09-20.md) and
[UI amendments checkpoint](ui-amendments-checkpoint-cleanup-2026-09-20.md).
They preserve observations and exclusions without becoming current setup steps.

## Historical qualification checkpoints through 19 September

The [qualification index](README.md) retains dated reports, including
[Factory .36 E2E](factory-36-e2e-2026-09-19.md). Old `Online`, `current`,
`next` and `not started` statements are checkpoint-local. Use this page for
the selected candidate and the [active distribution plan](../planning/active/installable-distribution-and-reproducibility.md)
for remaining work.
