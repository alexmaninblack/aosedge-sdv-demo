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

## Make and verify a change

1. Read the accepted requirements and interface contract for the affected
   behavior. Resolve a changed authority, lifecycle or trust boundary in the
   design before implementing it.
2. Add the smallest regression proof and change the owning source. Run its
   local tests before rebuilding dependent packages.
3. Update the owning usage documents. Update integration requirements,
   contracts and evidence only where the change affects them; retain stable IDs.
4. Use the component's documented local checks. For integration documentation,
   run the commands below. Keep build/test scratch on the declared SSD.
5. Commit the bounded change with its test results and exclusions. Do not
   present source-only tests as a deployed or qualified release.

```sh
python3 -B scripts/docs-check --reader-routes
python3 -B scripts/validate-release-definition
```

These two checks work without sibling checkouts or a live demo. The broader
`python3 -B scripts/docs-check` gate covers all specialist documentation and
requires its declared sibling reference files. Full local tests use
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
