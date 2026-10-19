<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current release publication and public delivery

Recorded on 19 October 2026. Product qualification, native first use and the
anonymous operator consumer retain their separate exact-candidate boundaries.

## Published release: 1.2.0-rc.3

All seven release stages passed and option A now selects the immutable
[rc.3 delivery descriptor](../../workspace/releases/delivery.json) and its
[public Dropbox DMG](https://www.dropbox.com/scl/fi/4p5we60443lxxrv5hx1zs/AosEdge-SDV-Lab-1.2.0-rc.3.dmg?rlkey=4ci22xl2q1dletz32z1s03zkb&dl=1).
The preceding rc.2 media remains available for explicit rollback.

| Release item | Accepted identity |
| --- | --- |
| Integration release tag | `sdv-lab-v1.2.0-rc.3` at `50121df7fd4a4361f6337a6c6ac097fdc53fb263` |
| Packaged application source | `e787b926471dc096ed365efe0178d8d0181de1a5` |
| Platform source | `3a09f8c2b1c6f9e13efd25b91f00aa035d7a1938` |
| Gateway source | `19354402594ab2facf5f99f58bc3105740b4ad55` |
| Complete DMG | `AosEdge-SDV-Lab-1.2.0-rc.3.dmg`, 14,156,820,119 bytes |
| DMG SHA-256 | `25b2f89eb64bb8b58cbfca18e46ef2d6c59450dcdb2f316b168155842328355e` |
| Runtime application manifest | `b6884145a5098eeec0bad1a95182a060655b0c6451c1d1a040bf3fea0a9ba595` |
| Public consumer launcher SHA-256 | `c8ab21972b5daa5026aa585e7abbc1224c909ea82dd72079ca8b9ca0bce52338` |

The [exact rc.3 runtime](m1-clean-install-e2e-2026-10-14.md#mainline-candidate-120-rc3-api-and-visible-ui-pass)
passed 118/118 API checks and 42/42 visible browser stages with real native
driving input on M1. Source fan-in separately verified all 90 application files,
172 UI inputs and the signed Setup source receipt against those packaged bytes.
Later qualification/publication-tool and documentation commits did not rebuild
or change the product. CARLA and the Factory controller image were reused.

The release owner resumed the same Dropbox upload session from its confirmed
offset after SSD reconnection. A device-number-only change required a fresh
complete checksum/provider-hash proof and an explicit delivery-only successor;
the original frozen records and pending-upload journal were preserved. No new
upload session or completed payload chunks were replayed. Final provider file
identity, revision, size, block hash and anonymous HEAD passed without a
maintainer payload download.

The actual M1 consumer downloaded the frozen public launcher and exact DMG
anonymously, verified the complete SHA-256 and signed Setup, and opened Setup.
Its first continuation stopped at `INSTALLED_CURRENT_RUN_RETAINED`: the harness
tried to reselect the already selected package while retaining the qualified
Test. The product guard correctly preserved that Test. An operator-tooling-only
amendment verified the already downloaded bytes and existing selection through
read-only Setup owners, then continued the not-yet-started launch. Presenter
opening and final cleanup passed. There was no second download, launcher
handoff replay, selection mutation, Test deletion or product rebuild.

The same amendment corrected the read-only definition gate's coupling between
A's current media and B's earlier cached DMG. The current operator descriptor
is independently validated; frozen developer input locks and cache closure were
not rewritten. Targeted positive/negative tests and the complete release source
gates passed before continuation.

| Delivery phase | Measured time and scope |
| --- | --- |
| Resumed Dropbox publication | 7125.258 s; excludes the preceding parked session and remount checksum work |
| Initial M1 consumer attempt | 782.384 s; includes the public download, verification and retained-selection refusal |
| Successful operator continuation | 79.522 s; reuses confirmed delivery, verifies selection, opens Presenter and closes owners |
| Successful resume execution | 91.531 s; revalidates prior stages; amendment checks occurred before this timer |

These are phase timers, not total elapsed engineering time. The failed
8003.036-second campaign report, amendment/gate timings and original refusal are
retained separately; they were not relabelled PASS or hidden by the short resume.

Only after the consumer passed were the coherent catalog/helper graph promoted
to main and the integration tag published. Later documentation-only main commits
do not move that tag. Compact stage, consumer, remount, amendment and closure
receipts are retained under
`build/release-campaign/1.2.0-rc.3-dropbox-attempt-2` on the selected SSD. The
unchanged final DMG and matching receipts are archived in
`/Volumes/SDV-Releases/1.2.0-rc.3`.

Final closure confirmed no owned demo processes/listeners, closed native/browser
clients, detached installer media and a closed temporary display assertion.
An independent post-campaign check also confirmed the extra bounded delivery
display assertion had closed. Shared Docker retained the same Engine with zero
running containers; the installed Test and certificate instance were preserved. The M1
used internal storage; the development Mac ran unit/build/orchestration work,
not live demo tests. The release remains an Apple Development engineering
preview, not notarized or a claim of clean-macOS permission/account-registration
acceptance. The deferred VDP timeout was not changed.

The public consumer reused the installed certificate instance and did not create
a Test or repeat enrollment. Native Setup clicks and clean first use remain
NOT_RUN for this delivery profile. The separate
[rc.2 native first-use proof](m1-clean-install-e2e-2026-10-14.md#native-setup-with-no-ready-certificates-pass-on-15-october)
does not transfer to rc.3 bytes.

The [preceding rc.2 publication record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/1f4f0b6d6fef9ad0eb2bdb08182f53e242883237/docs/qualification/release-automation-2026-10-13.md)
retains its own exact-candidate delivery and timing evidence. It is not a current
prerequisite or qualification of the successor.
