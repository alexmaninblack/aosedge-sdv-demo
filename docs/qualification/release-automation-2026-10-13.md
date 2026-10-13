<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Release automation and public delivery on 13 October 2026

Source integration passed and the exact engineering DMG was published. Operator
promotion remains blocked: the real anonymous M1 GET returned Google Drive's
quota page instead of the DMG. The preceding operator selection stays in main;
no new release tag or completed operator release is claimed.

## Confirmed results

| Gate | Result |
| --- | --- |
| Product equivalence | 90 exported application files and 173 UI build inputs matched the retained package |
| Source checks | Documentation, launcher pins, regression fixtures, Presenter units, native semantics, web types and web units passed |
| Artifact | Retained DMG size and full SHA-256 confirmed; no CARLA or Factory rebuild |
| M1 product evidence | Exact unchanged package and scenario reused the passed 42-stage campaign; not new clean-first-user or native Setup input acceptance |
| Main integration | Gateway integrated before the integration repository; active B selection uses the schema 3 successor plan |
| Drive publication | Uploaded once; object identity, parent, size, provider checksum and public sharing confirmed |
| Anonymous A consumer | BLOCKED by provider quota; no valid media, installer handoff or catalog promotion |

The Gateway revision is `b4c505561f9d2bcdf75ee322f973c85d4b18380d`.
The initial source fan-in reached integration revision
`562e03f92c9c105bf3cb25c6a9ef30ea6a168999`; later consumer-tool corrections
preserve the preceding operator selection. Historical build locks remain intact.

## Published artifact

[AosEdge SDV Lab 1.2.0-rc.1 DMG on Drive](https://drive.google.com/file/d/1ddy0TgTCQSCqX8_oBVak2V9rJQAQlYOw/view)
is an Apple Development engineering preview, not notarized or distribution-qualified.
The public permission does not guarantee current anonymous download availability.

- Bytes: `14165529112`
- SHA-256: `5e0dbf77f6b48e9efcaee8a38b85157dd691c0bb11369f316e5919fe5fa6f719`
- Application manifest: `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c`

The blocked M1 response was a 2,040-byte HTML page titled “Google Drive - Quota
exceeded”. The file-size guard stopped before mounting or opening Setup. The
invalid response was removed after ownership, no-handoff and no-handle checks;
compact evidence and all installed Test data were preserved. No quota bypass,
authenticated operator fallback, duplicate upload or repeated payload download
was attempted.

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

The publication adapter previously rehashed the same file and performed a system
storage check for every 4 MiB. Its observed low effective read rate was not a
measurement of the SSD interface ceiling. The corrected adapter accepts the
private verification receipt only while the full file identity and expected
digest still match. Negative identity tests reject changed sources. The new
optimization is fixture-tested; no extra 14 GB upload was made to benchmark it.

## Closure and remaining gate

The M1 demo owners and listeners were observed closed; temporary display
assertions were terminated and verified. Shared Docker, installed packages,
certificates and Test state remain preserved. The development Mac ran unit tests
and orchestration only.

The remaining release gate is a successful real anonymous A download, ordinary
install/open proof and final catalog/tag promotion after provider availability
returns or an explicitly approved delivery change. Native Setup button-input
and clean-first-user acceptance remain separate engineering-preview boundaries.

See the [accepted release plan](../planning/active/work-packets/consolidated-release-automation.md)
and [campaign operating contract](../development/release-campaign.md).
