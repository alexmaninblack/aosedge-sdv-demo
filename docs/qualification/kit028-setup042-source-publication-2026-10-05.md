<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Kit028 / Setup042 source return point

- Status: review candidate; not a completed native E2E release
- Version: 1.0
- Prepared: 5 October 2026
- Owner: SDV Lab integration
- Candidate tag: `candidate/kit028-setup042`

This checkpoint preserves the source of the existing Kit028 / Setup042 media.
It does not rebuild, re-sign, upload or replace that DMG. It does not change
`demo-v1.0`, `demo-v1.1`, Production, current credentials or the video repository.
The operator still has the same media for the planned manual M1 installation.

## Source and artifact identity

The machine-readable [source lock](../../workspace/checkpoints/installer-kit-028-source-lock.json)
records complete commit IDs, artifact hashes and source-file digest sets.
The [qualification checkpoint](../../workspace/checkpoints/installer-kit-028-candidate.json)
retains the actual installed and native-test results; this source checkpoint
does not turn an open acceptance gate into a pass.

| Repository / role | Retained source commit | Distinction from built inputs |
| --- | --- | --- |
| Demo application and Setup | `638fc8d18b1ee66f10a253fd51ab4238582ba843` | Tag also contains publication documentation and updated workspace/CI pins |
| Factory build tools, `codex/factory40-vlan` | `30ae66148255830b7e29cc82e2cd251d065bb894` | Preserved separately; no unreviewed merge into the application branch |
| Vehicle platform | `92a2138813983cb1c029fd3e61bd90b68241af63` | Factory41 was built from `3fd1f8e`; later changes only add license metadata and test headers |
| Brake service | `5aa652fda603e7621043961331e58236b19204e9` | Same retained service source |
| Tire service | `f0a0f6edadb51aa338775d157aa3bde28f5b76f4` | Same retained service source |
| Gateway / Driving Control | `2e3d1164d491dac25e212f59315057deca0bf3d8` | Commits the native caption fix that was uncommitted at build time |
| CARLA, personal fork | `eb09b82464076596ee47e42b3f5f9b48f9ff5b30` | Commits retained shutdown, cooked-source guard, Metal profile and content-projection helpers |
| Unreal build dependency | `9b705d6d2db5b769ab34edb04f3ca2bb8b960014` | Restricted dependency; not republished here |
| Brake backend | `7c64adf7b3d99535ecc7c8cbe468bc527cbcdc12` | Image built from `42395715`; later change is documentation only |
| Tire backend | `ea2d6deec9b704cb866d362eaefc9d87356ddeb5` | Image built from `47cfa632`; later changes are documentation only |

The workspace manifest and hosted boundary-check pins now select these source
revisions. In that manifest, `acceptedRevision` identifies the source checkout,
not proof that Kit028 has completed native E2E or distribution approval.
Earlier tags retain their original manifests. The integration candidate remains
on `codex/installable-demo-stage3`; no implicit merge to `main` is performed.

The original application manifest records build HEAD `22ee79e`, but the working
tree was dirty. A HEAD alone therefore did not identify the delivered source.
The publication audit compared **Git blobs**, not merely current working files,
against the preserved build receipts:

- 89 application files match the integration source commit.
- 100 Setup inputs match the integration source commit.
- 169 UI build inputs match: 167 integration files and two Gateway files.

These are 358 verified entries across overlapping inventories, not 358 distinct
files. The source lock retains each original path and SHA-256. Existing artifact
manifests are not rewritten to pretend the build started from a clean commit.
This proves the recorded source correspondence, not a byte-identical rebuild of
signed binaries or completeness of every historical compiler environment.
Licensed Unreal/content inputs and cooked assets remain outside public Git.

Media: `AosEdge-SDV-Lab-Kit028-Setup042.dmg`, **14,150,764,550 bytes**.
Its SHA-256 is
`27c4dbcac02c5cefcd3f20c75d7e51e3d54ec9f631bbc48e8d58839ea8e67236`.
The retained creation/transfer records supply the large-artifact digest; the
unchanged file identity and size were checked again, without a redundant rebuild.

## Publication checks and non-product corrections

The existing repository-boundary gate passed: platform contract checks,
223 platform tests (two skipped), 24 Brake tests (five skipped), 759 integration
tests (one skipped), component-lock validation, documentation validation and
platform/Brake REUSE license checks. Presenter type checking and all 336 unit
tests passed; all 144 Gateway Python tests passed. CARLA's eight profile tests
and three retained native shutdown regression tests passed. Tire's 28 Python
tests passed with five native-build-dependent tests skipped.

Before publication, the audit corrected documentation scanning to include the
qualification scripts' Markdown guide, replaced personal home paths in the
public report/checkpoint with portable references, and added missing SPDX
metadata. The two Factory patches retain their exact original bytes; their
license information is in sidecars. None of these changes replaces installed
runtime code in Kit028.

The supplemental orchestration suite is tracked separately from the boundary
gate. Local artifact-catalog selection and a globally overridden artifact root
contaminated initial attempts; those attempts are not passes. A clean Git export
ran 1,371 tests: 1,351 passed, four skipped, and 16 failed/errored because that
export omitted the installed crypto inputs and isolated SDK dependencies. With
the unchanged Kit028 input catalogue and its private Cloud Python interpreter
(`-I -B`), all 26 tests in the two affected modules passed, including all 16
previous failures. No product change or weakened assertion was needed. This is
a full-suite run plus a dependency-corrected targeted rerun, not a claim of one
single uninterrupted all-green run.

For repeat checks, use a disposable source checkout/export and the matching
read-only artifact catalogue, not the developer's moving installed catalogue.
Do not set a global `DEMO_ARTIFACT_ROOT` for the full suite: installed-mode tests
deliberately reject that override and other tests create independent catalogues.
The signer tests launch isolated child Python processes, so supplying SDK modules
only through `PYTHONPATH` is insufficient; use the pinned SDK interpreter itself.

## Preserved limits and local material

The installed scripted journey previously passed 98 main steps, including serial
updates, independent resets, offline recovery and ignition. Full native E2E is
still **NOT_COMPLETE**: moving SOTA, secure native token entry, the complete
native operator journey and interruption/repair remain separate open gates.
Load-sensitive readiness transitions and VDP-TIMEOUT-01 remain deferred;
D4-023 fixed-load CPU isolation remains unimplemented. Setup is locally Apple
Development signed, not notarized or approved for public binary distribution.

CARLA's local `.codex-build`, `.tmp`, `.worktrees` links, historical platform
source snapshot, pinned-API import helpers and personal disk-retention report
are narrowly ignored rather than committed. They are preserved, not deleted.
Build products, private evidence and credentials remain outside source Git.
The pre-existing integration stash and Factory build worktree remain intact.
The video repository is outside the publication and cleanup scope entirely.

## Restore this checkpoint

Check out `candidate/kit028-setup042` in the integration repository, then use
the exact repository pins from the source lock, not moving branch heads. The
Factory-tools row is a separate checkout of the integration repository and is
not a replacement for the application's source checkout. Retrieve the retained
DMG through the approved private transfer path and verify its recorded digest
at the next transfer/trust boundary. Git does not contain the DMG, credentials,
Factory image or proprietary build inputs.

Continue qualification against the same candidate and record actual results
in the existing checkpoint. A source tag is a return point, not acceptance of
unexecuted tests or a promise that a clean machine needs no external access.
