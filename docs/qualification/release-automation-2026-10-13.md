<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release automation and public delivery on 13 October 2026

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

See the [accepted release plan](../planning/active/work-packets/consolidated-release-automation.md)
and [campaign operating contract](../development/release-campaign.md).
