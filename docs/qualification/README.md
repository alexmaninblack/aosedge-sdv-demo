<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification and current evidence

Start with the [current baseline](current-baseline.md). Release selection is
owned by the [launcher catalog](../../workspace/launcher-catalog.json); results
apply only to the exact source, media and profile identified by their receipt.

## Current evidence

- [Dropbox publisher](dropbox-publisher-2026-10-15.md): automatic immutable
  publication, interrupted-transfer reconciliation and private OAuth handling;
  source integration does not republish or replace the selected operator DMG.
- [M1 runtime and native Setup record](m1-clean-install-e2e-2026-10-14.md):
  the 15 October corrected Production runtime passed 118 API and 42 visible
  browser UI checks with actual native driving input. A separate native Setup
  profile passed new certificate issuance for existing authorized accounts.
  Earlier failures remain chronological evidence, not the final outcome.
- [Release automation and public delivery](release-automation-2026-10-13.md#successor-published-on-15-october-120-rc2):
  main/tag publication and anonymous M1 download/verification/open passed for
  the selected successor. Its public consumer reused the installed certificate
  instance; it is not another clean-first-user proof.
- [D4-003 stimulus calibration plan](d4-003-stimulus-calibration-plan.md):
  an outstanding accepted verification obligation, not a passed calibration.

## Preserved locked-release dependencies

Two historical reports remain because the unchanged release definition requires
these exact paths: [Kit028 M1 journey](m1-live-journey-2026-10-03.md) and
[Kit028 source publication](kit028-setup042-source-publication-2026-10-05.md).
They are not current installation instructions or evidence for different bytes.
The earlier definition inventory is similarly retained in development docs.

Other superseded reports were removed from the current tree. Their original
contents and hashes are recorded by the
[retirement inventory](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/d14e837c4cca30d8d9ebe83df996974b92c46f3b/workspace/checkpoints/documentation-retirement-20261015.json), and
historical citations resolve to the published Git snapshot.

Developer ID/notarization, new-account registration, broader native recovery,
calibration/resource/negative matrices and deferred timeout
work are not closed by a green documentation check. See the current baseline
for the full limits.
