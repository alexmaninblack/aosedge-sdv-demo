<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Contribute to SDV Lab

Start with the [product map](docs/architecture/product-map.md) and choose the
component that owns the behavior. Build the integrated demo through the
[developer guide](docs/getting-started/reproduce-demo.md); do not edit installed
payloads or frozen prepared checkouts in place.

## Choose the owning repository

UI, Setup, orchestration and cross-component contracts belong here. Vehicle
data/FOTA belongs to the platform; Brake and Tire each own their service and
backend. Gateway/control belongs to the simulation tooling. A service change
does not normally require rebuilding Unreal or Factory.

Use a separate working checkout for edits. Follow the owner's branch/review
policy and keep one writer per checkout. External contributions require review;
the single-maintainer direct-main convention is not permission to bypass it.
Never reset or clean another contributor's files.

<a id="from-a-source-change-to-your-own-installer"></a>

## From a source change to your own installer

There are two different tasks: **B reproduces the reviewed build**, whereas
**component development changes the source selection**. Prepared sources under
`<parent>/sdv/source` and `<parent>/sdv/build/sources` are frozen build inputs,
not editable development workspaces. Neither local edits nor a component's
new `main` automatically enter the next DMG.

For an integration change, open Terminal in an existing development folder
outside those prepared trees and create your own working checkout:

```sh
git clone https://github.com/alexmaninblack/aosedge-sdv-demo.git aosedge-sdv-demo-work
cd aosedge-sdv-demo-work
git switch -c feature/my-lab-change
```

For a component change, clone its owning repository from the
[component map](docs/architecture/product-map.md#source-ownership) into a separate
working folder instead. Then:

1. Make and test the change in that working checkout using the owner's local
   instructions below. Commit it; never edit installed programs or use their
   private Python as a build environment.
2. Submit the exact commit for review. Until it is accepted into a successor
   build selection, ordinary B continues reproducing the existing selection.
   A working branch is not automatically a selectable installer candidate.
3. The integration owner creates the reviewed successor input selection from
   `workspace/build-definition.json` and its declared input closure. The
   source lock is `workspace/inputs/sources.lock.json`; the
   ordered producer plan is `workspace/releases/build-plan.json` and its
   selector is `workspace/current-developer-build.json`. For Presenter/Setup
   and native UI changes, the plan's `nativeSources` selects exact integration
   and Gateway commits; its `producers` selects packaging tool commits. The
   maintenance-only `repository-map.json` does not select package code.
4. Keep unchanged CARLA/Factory/input identities and verified cache objects.
   A changed input closure needs an explicitly reviewed successor cache
   namespace; do not rebind the old one. Follow
   [workspace projection maintenance](workspace/README.md) for an authorized
   definition change and [release source selection](docs/development/release-campaign.md#current-ui-source-selection)
   for current UI/native inputs. Review the dependent catalog/source pins
   together; do not guess checksums, rewrite published descriptors or rebind
   an old completed build to new source. Incompatible dependency changes need
   their own reviewed inputs before packaging.
5. After the matching selection/tools are published, start B in a
   [fresh workspace](docs/getting-started/unified-macos-launcher.md#start-a-new-build-selection)
   and install its exact result through [that DMG's Setup](docs/getting-started/reproduce-demo.md#install-your-build).
   Public option A changes only through separate release acceptance/promotion.

There is no downloaded-launcher option to build arbitrary dirty working trees
or choose an unreviewed branch. Use the component's local build for development;
use the reviewed selection above for an integrated installer. This distinction
preserves reproducibility rather than silently shipping different source.

## Make and verify a change

1. Read the accepted requirements and interface contract for the affected
   behavior. Resolve a changed authority, lifecycle or trust boundary in the
   design before implementing it.
2. Add the smallest regression proof and change the owning source. Run its
   local tests before rebuilding dependent packages.
3. Update the owning usage documents. Update integration requirements,
   contracts and evidence only where the change affects them; retain stable IDs.
4. Use the component's documented local checks. For integration documentation,
   run the commands below. Keep build/test scratch in the declared workspace.
5. Commit the bounded change with its test results and exclusions. Do not
   present source-only tests as a deployed or qualified release.

```sh
python3 -B scripts/docs-check --reader-routes
python3 -B scripts/validate-release-definition
```

These two checks work without sibling checkouts or a live demo. The broader
`python3 -B scripts/docs-check` gate covers the full integration documentation.
With all six maintained component checkouts, run `python3 -B scripts/docs-check --workspace`
to verify all seven repositories, current hosted paths/anchors, immutable Git
citations and GitHub-safe navigation without builds. Network probes are an
optional separate `--external` scope. This current-documentation audit is not
for frozen producer/source checkouts; those retain their own matching gates.
Full local tests use
`python3 -B -m unittest discover -s tests -p 'test_*.py'`; some suites require
the declared workspace/tool prerequisites. CI labels root-only fixtures
separately from workspace/native/live qualification.

## Update a release without rewriting history

Changing a component does not automatically update a released demo. The
integration owner selects committed component/producer revisions, updates the
appropriate locks and runs definition/contract checks. Build affected owners
and downstream consumers only. Independently review new group manifests and
Setup pins; never copy an observed digest merely to silence a mismatch.

Keep historical tags, descriptors, input objects and provenance intact. A new
candidate needs a distinct record; signed output need not be byte-identical.
Validate source availability, licenses, distribution signing and the affected
installation/live scenarios before publication. Candidate and stable tags have
different acceptance criteria. Use [release status](docs/getting-started/release-status.md)
to distinguish proposed names from published references.

## Security and operational boundaries

Do not commit keys, tokens, PKCS#12 material, provisioned VM disks, raw Cloud
responses, customer data or compiled packages. Reading docs and running offline
checks does not authorize Cloud changes, signing or Test deletion. Live tests
use their approved scope and serial version sequence. Stop owned test processes
when done, leaving shared Docker and unrelated workloads alone.

For an issue, report exact revision/package, host, failed action, sanitized error
and reproduction steps. See [troubleshooting](docs/getting-started/troubleshooting.md).
Detailed policies are in [development workflow](docs/governance/development-workflow.md),
[documentation management](docs/governance/documentation-and-requirements-management.md)
and [licensing](docs/governance/licensing-and-copyright-policy.md).
