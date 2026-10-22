<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# rc.4 retained-Test and delivery evidence

Recorded on 22 October 2026. This is scoped evidence for the exact delivered
engineering candidate, not fresh-first-user or general-public acceptance.
The [delivery descriptor](../../workspace/releases/delivery.json) and
[launcher catalog](../../workspace/launcher-catalog.json) own current selection.

## Exact artifact

| Item | Recorded identity |
| --- | --- |
| Delivery version | `1.2.0-rc.4` |
| DMG | `AosEdge-SDV-Lab-1.2.0-rc.4.dmg`, 14,159,664,289 bytes |
| DMG SHA-256 | `420a559daaff3fe6e3b2f9b898fc189c367754aee3a3eeab0164d30c537dc830` |
| Application manifest | `a982ad8f620415669ec92b8b68cc2f82e316c90ad6e44ce5e7c5fb59b3281884` |
| Packaged application/Setup source | `aa289dd8115a68ae36db71ec19a40c2eb575dac3` |
| Setup executable SHA-256 | `b25cb5f8f3771f6a539a46398d269119acdb7aae4b8439fe99e51a7f776eed2e` |
| Signing | Apple Development; not notarized |

These exact bytes were built and tested as `rc.3-FOTA-Recovery`, then assigned
the immutable rc.4 delivery name without recompilation or repackaging. The
delivery label does not rewrite the original build receipt or embedded label.
CARLA, Factory and the five verified input groups were reused.

## M1 retained-Test profile

Supported package update preserved the existing Test, journal, controller disk,
Cloud enrollment, certificates, models and backend history. The engineering
launcher transition used the explicitly authorized exact Apple signing-team
pair; it is not permission to accept arbitrary signing-team changes.

The FOTA correction restores trust only for the validated unchanged boot
projection and the same-enrollment reconnection around a waiting-for-safe-stop
transaction. It preserves the intent and committed selector and lets normal
Service Manager startup resume the transaction. No transaction deletion, new
key/leaf, immutable-rootfs change or security-policy relaxation was used.

| Profile | Result | Execution time |
| --- | --- | --- |
| Retained-Test API campaign | 115/115 PASS; zero failed, blocked, uncertain or unrun checks | 1601.802 s |
| Continuous visible UI campaign | 42/42 stages PASS; actual native Driving Control input | 1248.155 s |
| Campaign master | PASS, including verified final closure | 2910.233 s |

The M1 used internal storage and Production Aos Cloud (`aoscloud.io`) with a
Test vehicle. Final closure stopped owned demo processes/listeners and backends,
closed browser/native/transport/display helpers and detached owned media.
The Test and durable data remained; shared Docker Engine was preserved.
Earlier harness correlation/lock failures retain their separate records.

## Publication and option A

Source fixes and the catalog were pushed to main. Dropbox publication checked
the remote identity, revision, size, provider checksum and anonymous availability.
The M1 option A consumer verified the exact local media checksum/signature,
started signed Setup and confirmed the unchanged installed selection and Test.
The consumer passed in 105.472 s and closed owned Setup/media afterward.
It reused already transferred bytes: this was not another public payload
download, fresh installation, enrollment or replay of the installation journey.

Compact `qualification.json`, `original-build-receipt.json`,
`delivery-provenance.json`, `publication.json`, `operator-promotion.json` and
`consumer-result.json` are retained alongside this exact DMG in the release
store's `1.2.0-rc.4` directory. They are evidence, not build inputs.

## Separate gates

Native first use without ready certificates, moving-SOTA acceptance, secure
native token entry, the full native operator journey and installation
interruption/repair were not established by this campaign. Sleep/wake and
external-SSD runtime checks were excluded; VDP-TIMEOUT-01 remains deferred.
The [baseline](current-baseline.md#remaining-acceptance-limits) retains the
broader calibration, isolation, negative and distribution obligations.

Current B source alignment and a prepared workspace are not an rc.4 B rebuild.
Any newly built/signed B package needs its own artifact and M1 evidence; it
cannot inherit these passes or overwrite option A's DMG.
