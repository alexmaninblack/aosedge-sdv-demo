<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification and current evidence

Start with the [current baseline](current-baseline.md). Release selection is
owned by the [launcher catalog](../../workspace/launcher-catalog.json); results
apply only to the exact source, media and profile identified by their receipt.

## Current evidence

- [Publisher evidence and procedure](../development/release-campaign.md#publisher-evidence):
  scoped sender transport proof; not another product-release acceptance.
- [M1 runtime and native Setup record](m1-clean-install-e2e-2026-10-14.md):
  rc.3 passed 118 API and 42 visible browser UI checks with actual native driving
  input. The separate rc.2 native Setup profile passed new certificate issuance
  for existing authorized accounts; that proof does not transfer to rc.3.
  Earlier failures remain chronological evidence, not the final outcome.
- [Release automation and public delivery](release-automation-2026-10-13.md#published-release-120-rc3):
  main/tag publication and anonymous M1 download/verification/open passed for
  the selected successor. Its public consumer reused the installed certificate
  instance; it is not another clean-first-user proof.
- [D4-003 stimulus calibration plan](d4-003-stimulus-calibration-plan.md):
  an outstanding accepted verification obligation, not a passed calibration.

## Provenance without historical report dependencies

The [current build definition](../../workspace/build-definition.json) binds
current source/input locks and independent developer/operator selections.
The [cache compatibility record](../../workspace/inputs/cache-compatibility.json)
preserves unchanged input provenance and cache identity; it is not a list of
historical reports or proof for different runtime bytes.

Other superseded reports were removed from the current tree. Their original
contents and hashes are recorded by the
[retirement inventory](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/d14e837c4cca30d8d9ebe83df996974b92c46f3b/workspace/checkpoints/documentation-retirement-20261015.json), and
historical citations resolve to the published Git snapshot.

Developer ID/notarization, new-account registration, broader native recovery,
calibration/resource/negative matrices and deferred timeout
work are not closed by a green documentation check. See the current baseline
for the full limits.
