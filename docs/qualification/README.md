<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Qualification and current evidence

Start with the [current baseline](current-baseline.md). Release selection is
owned by the [launcher catalog](../../workspace/launcher-catalog.json); results
apply only to the exact source, media and profile identified by their receipt.

## Current evidence

- [rc.4 retained-Test and delivery](current-rc4.md): supported package update,
  pending-FOTA recovery, 115 API checks and 42 visible UI stages passed on M1.
  Option A passed exact-media/retained-selection handoff and cleanup without a
  redundant payload download. Fresh first use remains separate.
- [Publisher evidence and procedure](../development/release-campaign.md#publisher-evidence):
  scoped sender transport proof; not another product-release acceptance.
- [Independent developer workspace](developer-reproduction.md):
  the earlier B rebuilt a distinct rc.3 package from fresh sources and verified binary
  archives; its own M1 API and visible UI profiles passed. Existing host/tools
  were reused. This does not qualify the current rc.4 B selection, close
  fresh-host R4 or promote public option A.
- [M1 runtime and native Setup record](m1-clean-install-e2e-2026-10-14.md):
  predecessor rc.3 passed 118 API and 42 visible browser UI checks with actual native driving
  input. The separate rc.2 native Setup profile passed new certificate issuance
  for existing authorized accounts; that proof does not transfer to rc.4.
  Superseded campaigns and failures remain immutable evidence, not another
  current release or a substitute for exact-candidate proof.
- [Release automation and public delivery](release-automation-2026-10-13.md#published-release-120-rc3):
  predecessor main/tag publication and anonymous M1 download/verification/open.
  That public consumer reused the installed certificate
  instance; it is not another clean-first-user proof.
- [D4-003 stimulus calibration plan](d4-003-stimulus-calibration-plan.md):
  an outstanding accepted verification obligation, not a passed calibration.

## Retained-Test correlation

A retained profile preserves the existing Test, model, advisory producer and
history. It does not manufacture or provision another controller. Brake's
accepted advisory policy keeps an active decision across same-band assessments
and ordinary restart/update cycles; its source assessment can therefore predate
the V2 release published by the current campaign.

The API check may use that exact retained assessment only when the pre-exercise
observation already binds its valid inspection condition to Gateway `APPLIED`
evidence from the newly deployed V3 release. The post-exercise observation must
still correlate `APPLIED` for that release and decision. An unrelated historical
assessment, another release's fact or received/expired evidence is not a pass.
See the [accepted Brake policy](../../contracts/brake-health-advisory-policy/README.md).

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
