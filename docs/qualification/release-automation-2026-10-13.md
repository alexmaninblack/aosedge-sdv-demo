<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release automation and public delivery on 13 October 2026

## Current outcome — 15 October 2026

The [published successor](#successor-published-on-15-october-120-rc2) completed
all seven release stages, main/tag publication and the anonymous M1 public
consumer. Native Setup first use passed as a separate profile. The preceding
rc.1 and Drive quota notes below are dated history, not current promotion
blockers. Media remains Apple Development engineering preview, not notarized.

## Chronological record — beginning 13 October

The selected engineering DMG passed public Dropbox delivery on M1 and its
operator catalog was promoted to main under `sdv-lab-v1.2.0-rc.1`. The package
is unchanged; existing product evidence remains applicable. This delivery check
reused an installed Test and does not close native Setup button-input or
clean-first-user acceptance.

The earlier anonymous Google Drive attempt hit the provider's quota page.
Its receipts and published object remain preserved; Dropbox is now the selected
operator provider, while reusable developer inputs remain on Drive.

## Confirmed results

| Gate | Result |
| --- | --- |
| Product equivalence | 90 exported application files and 173 UI build inputs matched the retained package |
| Source checks | Documentation, launcher pins, regression fixtures, Presenter units, native semantics, web types and web units passed |
| Artifact | Retained DMG size and full SHA-256 confirmed; no CARLA or Factory rebuild |
| M1 product evidence | Exact unchanged package and scenario reused the passed 42-stage campaign; not new clean-first-user or native Setup input acceptance |
| Main integration | Gateway integrated before the integration repository; active B selection uses the schema 3 successor plan |
| Drive publication | Uploaded once; object identity, parent, size, provider checksum and public sharing confirmed |
| Anonymous A consumer | PASS through Dropbox: complete download, checksum/signature, signed Setup handoff, installed-package/selection reconciliation and visible Presenter |
| Final promotion | Catalog, helper graph and launcher promoted together to integration main; annotated engineering tag confirmed remotely |

The Gateway revision is `b4c505561f9d2bcdf75ee322f973c85d4b18380d`.
The initial source fan-in reached integration revision
`562e03f92c9c105bf3cb25c6a9ef30ea6a168999`; later consumer-tool corrections
preserved the preceding operator selection until the consumer passed. Final
operator source and tag point to `20a4277907c850e3b56aa718ce559a22451181dc`.
Historical build locks remain intact.

## Published artifact

The selected [operator catalog](../../workspace/launcher-catalog.json) contains
the reviewed Dropbox link and [delivery descriptor](../../workspace/releases/1.2.0-rc.1-presenter-preview-dropbox-delivery.json).
The [older Drive publication](https://drive.google.com/file/d/1ddy0TgTCQSCqX8_oBVak2V9rJQAQlYOw/view)
contains the same bytes but is not the current operator locator. This is an
Apple Development engineering preview, not notarized or distribution-qualified.

- Bytes: `14165529112`
- SHA-256: `5e0dbf77f6b48e9efcaee8a38b85157dd691c0bb11369f316e5919fe5fa6f719`
- Application manifest: `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c`

The blocked M1 response was a 2,040-byte HTML page titled “Google Drive - Quota
exceeded”. The file-size guard stopped before mounting or opening Setup. The
invalid response was removed after ownership, no-handoff and no-handle checks;
compact evidence and all installed Test data were preserved. No quota bypass,
authenticated operator fallback, duplicate upload or repeated payload download
was attempted against that Drive object. The later approved Dropbox successor
made one real consumer download; no maintainer loopback download was added.

## Dropbox consumer reconciliation

The consumer verified the full DMG checksum, Setup signature and manifest before
opening Setup. Reuse of the previously installed package then stopped because
Finder had added five `.DS_Store` files. The DMG itself had the exact expected
17,699 files; no payload file was missing from the installed package.

A bounded recovery scenario checked the frozen launcher and downloaded file,
then quarantined only those five owned, unused metadata files outside the
installed package. It preserved their copies and the failed receipt. Full
installed-file verification and selected-version observation passed through
the ordinary Setup owners; inventory checks were not weakened. Presenter then
opened successfully and the normal shutdown confirmed closed owners/listeners.
The existing Test, package, certificates and shared Docker Engine were retained.

macOS had added `com.apple.diskimages.recentcksum` to the mounted DMG, changing
only its `ctime`. Because the consumer verification identity changed, recovery
performed one new complete checksum check rather than trusting the old receipt.
It did not download the payload again or replay the original graphical handoff.

## Consumer corrections

Fixtures now cover the observed large-executable warning, unnamed submit control,
separate HEAD versus HTML/payload size limits, and HTTP 200 quota pages after a
binary HEAD. Actual GET headers are checked before a downloaded response can
become a DMG. Size, checksum, signature and OS protections remain authoritative.

Operator-only corrections require unchanged product inputs, confirmed prior
publication, closed owners and affirmative proof that no media handoff occurred.
Their source gates run again; previous failed receipts remain archived. Successful
earlier mutations are reconciled rather than submitted again.

## Timing and efficiency

| Initial stage | Recorded duration |
| --- | --- |
| Freeze | 1.422 s |
| Source gates | 143.796 s |
| Full artifact verification | 34.398 s |
| Applicable evidence verification | 1.171 s |
| Ordered source main integration | 7.995 s |
| Publication including its old source check and network transfer | 4302.399 s |

These are stage durations, not the whole conversation or implementation time.
Consumer-tool investigations, corrections and additional unit gates are separate;
the three failed consumer stages took 37.094, 12.570 and 13.224 seconds.

| Dropbox continuation | Recorded duration |
| --- | --- |
| Original consumer attempt including download, checks and inventory stop/cleanup | 1067.210 s |
| Bounded metadata recovery, installed verification, open and closure | 119.996 s |
| Final catalog and tag promotion | 6.145 s |
| Last resume invocation, reusing earlier completed stages | 13.583 s |

The resumed consumer segment ran from 20:19:59 UTC to the confirmed promotion
at approximately 20:49:49 UTC: about 29 minutes 49 seconds, including diagnosis
and recovery preparation between script invocations. The last resume's 13.583
seconds is not the total release or consumer duration. Earlier builds, upload,
source investigations and storage migration are outside that interval.

The publication adapter previously rehashed the same file and performed a system
storage check for every 4 MiB. Its observed low effective read rate was not a
measurement of the SSD interface ceiling. The corrected adapter accepts the
private verification receipt only while the full file identity and expected
digest still match. Negative identity tests reject changed sources. The new
optimization is fixture-tested; no extra 14 GB upload was made to benchmark it.

## Closure and remaining acceptance

The M1 demo owners and listeners were observed closed; temporary display
assertions were terminated and verified. Shared Docker, installed packages,
certificates and Test state remain preserved. The development Mac ran unit tests
and orchestration only.

Anonymous A delivery, installed/open reconciliation and final catalog/tag
promotion passed. Native Setup button-input, a clean-first-user walkthrough
and any remaining full installer E2E gates remain separate engineering-preview
boundaries. The prior 42-stage product campaign was reused for the exact
unchanged package, not rerun or relabelled as a fresh complete E2E result.

See the [accepted release plan](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/planning/active/work-packets/consolidated-release-automation.md)
and [campaign operating contract](../development/release-campaign.md).

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
