<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current release publication and public delivery

Recorded on 15 October 2026. Product qualification, native first use and the
anonymous operator consumer retain their separate exact-candidate boundaries.

## Successor published on 15 October: 1.2.0-rc.2

All seven release stages passed and option A now selects the immutable
[rc.2 delivery descriptor](../../workspace/releases/1.2.0-rc.2-presenter-preview-dropbox-delivery.json).
The preceding rc.1 descriptor and media remain unchanged for explicit rollback.

| Release item | Accepted identity |
| --- | --- |
| Integration release tag | `sdv-lab-v1.2.0-rc.2` at `9f408472dbb0c9882ea150d65ab4df509f29c221` |
| Platform component tag | same tag at `fade0de2412efa71d739cf6e5d7e41308838f0b8` |
| Gateway component tag | same tag at `b4c505561f9d2bcdf75ee322f973c85d4b18380d` |
| Complete DMG | `AosEdge-SDV-Lab-1.2.0-rc.2.dmg`, 14,159,474,231 bytes |
| DMG SHA-256 | `71063a5d05ce9287feb0964d661b8408343aa85a58b4c3baaed8c0fd14664270` |
| Runtime application manifest | `0f6216c8f300d5106e5ad80cc5ebe25682e397b7ae4174977055018477ffedb8` |
| Public consumer launcher SHA-256 | `8b56db34e20cd7f3a606b29398e51a5ec78a8da2bb7b1f4b20b24b32376a8e59` |

The source-preserving VDP runtime and corrected Setup are in main. Current B
uses its frozen-source successor over the unchanged rc.1 binary-input definition;
historical dependency locks were not rewritten. All 90 application files and
173 UI inputs were checked for equivalence to the qualified runtime. Setup's
own source hashes and executable receipt separately bind its corrected menu/
enrollment-domain handling; the descriptor's producer revision identifies the
unchanged Runtime Kit, not the later Setup compilation.

The [separate first-use profile](m1-clean-install-e2e-2026-10-14.md) passed actual
native Setup input with empty certificate fields, new M1-generated OEM/SP keys,
production Cloud connection and Presenter opening. Its initial installation
evidence was reused for unchanged install helpers. The public consumer then
downloaded this exact new DMG anonymously on M1, verified complete SHA-256 and
signature, opened Setup, reconciled the installed package and opened Presenter.
That public consumer reused the installed certificate instance and did not
create a Test or repeat enrollment. Its own native-click/clean-first-use flags
remain NOT_RUN; they are not substitutes for the separate native first-use proof.

The seven-stage delivery campaign took 1232.423 seconds. Operator promotion,
including actual public transfer, install/open checks and cleanup, took
1095.294 seconds. These are not total elapsed time for this work: first-use
investigation, Setup-only packaging, preliminary main fan-in and Dropbox export
are outside that timer. A failed desktop application-status lookup additionally
consumed 654.148 seconds outside the campaign. A pre-stage nested display-owner
conflict was reconciled before a single-owner run; no payload download or
publication was replayed because of it.

Only after the anonymous consumer passed were the new catalog/helper graph
promoted to main and the integration tag published. Compact stage, consumer and
closure receipts are retained under `build/release-campaign/1.2.0-rc.2-dropbox`
on the selected development SSD. The final DMG and receipts are archived in
`/Volumes/SDV-Releases/1.2.0-rc.2`.

Final closure confirmed no owned demo processes/listeners, closed native/browser
clients, detached installer media and a closed temporary display assertion.
Shared Docker and the installed certificate instance were preserved. The M1
used internal storage; the development Mac ran unit/build/orchestration work,
not live demo tests. The release remains an Apple Development engineering
preview, not notarized or a claim of clean-macOS permission/account-registration
acceptance. The deferred VDP timeout was not changed.

The [original release record](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/cc75541f255f3d2fb0fd670053687ebe406c37ee/docs/qualification/release-automation-2026-10-13.md)
retains preceding rc.1 delivery, Drive quota responses, recovery attempts and
phase timings. They are not current prerequisites or blockers.
