<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable Cloud and backend input integration

- Date: 2026-09-26.
- Status: Source/input checkpoint passed; later preserved-run live proof linked below.
- Parent: [Stage 2 packet](../planning/active/portable-runtime-artifacts.md).
- Contract: [Cloud/backend inputs](../../contracts/portable-cloud-backend-inputs/README.md).
- Preserved baseline: [demo-v1.1 / Factory .39](demo-v1.1-return-point.md).

## Changed boundary

The [complete application continuation](portable-application-2026-09-26.md#preserved-run-functional-proof-26-september-utc)
now selects these inputs through the existing owners. Authenticated packaged
Cloud reads and existing backend volumes pass online/OFF/ON and post-reboot
checks. Starting Docker also restarted unrelated containers under their saved
policies; no container configuration/data was modified. Fresh-engine image
import and first-use credential setup remain unqualified, not inferred from
the preserved engine and identities. The original source-slice details follow.

Existing certificate inspection, component/signing/schema workers, service
catalogue reads, Unit operations and native IAM identity lookup use a common
fixed-worker launcher. A selected `cloud-runtime` supplies the independently
pinned private interpreter. No runtime selection is added to UI configuration
parsing. The SDK adapter receives only a non-secret package-location hint and
checks its executing interpreter and source-locked closure before import.

The private process retains the existing `-I -B`, minimal environment, worker
requests, deadlines and bounded/sanitized output. Native IAM lookup now also
uses that minimal worker environment; SSH transport itself is unchanged.
Local validation precedes Unit attempt marking and native IAM forwarding.
Missing/corrupt input is not reported as a Cloud permission or credential error.

Existing BackendService candidate selection can read `backend-inputs` without
Git or a build. It retains the existing cleanup protocols and immutable image
IDs. A recorded backend remains selected for that run; the explicit activation
gate is unchanged. Candidate selection checks manifest/file metadata, not the
78 MiB archive contents on every Start. The engine still checks the exact
image ID. Explicit archive integrity verification is separate and performs no
import, build, pull, container action or Docker Desktop start.

## Reused artifacts

No artifact was rebuilt or copied. The source locks bind the existing candidates:

| Input | Payload | Manifest SHA-256 |
| --- | --- | --- |
| Cloud Python | 3,204 files / 115,003,292 bytes | `46fe0adf22a6843f9d7c4162208f38caf194ca19e98e1089e3fb931ed2a5bb46` |
| Backend archive | 82,130,944 bytes / two images | `7d0d9b01feab0ce22a6d5e566cb90fab92431f3526c4f46706f99a7b10b422ed` |

Candidates remain at `/private/tmp/aosedge-stage2-native.cir6B1/Cloud Python Candidate 001`
and `/private/tmp/aosedge-stage2-native.cir6B1/Backend Images Candidate 001`.
The backend archive SHA-256 remains
`c15c6f69eddec6d9bc0552215414c9b0b8186fe9524392c4c9cb4f1d3b607a28`.
Its two image identities and cleanup protocols match the retained developer
build receipts, not a newly compiled service or changed model.

The actual source readers validate all SDK files and the backend archive hash.
Measured SDK integrity in this one development-Mac invocation: 0.981 seconds
initially, 0.327 seconds for a repeated unchanged-identity pass. These are local
integrity timings, not Cloud latency, UI benchmarks or clean-host startup claims.
The SDK's earlier source-denied dependency proof is retained; this continuation
does not claim a newly exported full app or a live Cloud session.

## Source checks

- 13 new Cloud-selector tests pass, including all fixed worker routes, absent
  selection, no environment injection, pre-attempt/pre-SSH failure, strict
  adapter identity, invalid manifests/paths/files and asynchronous-config scope.
- 9 new backend-selector tests pass: fixed image/protocol identity, retained
  run record, no implicit engine/build/import, absent developer path, separate
  archive integrity/cache invalidation and corrupt/missing/unsafe inputs.
- The initial Cloud fixture mixed macOS `/var` and `/private/var` aliases.
  Canonicalizing the temporary fixture path fixed the assertion without a
  product ownership/path-policy change; all 13 cases then passed.
- The first broad run completed 1,155 cases with 30 errors and 17 skips.
  Local socket/process visibility restrictions affected the existing suites;
  two old Cloud test doubles also required the new optional root argument and
  a real interpreter path in place of an unrestricted Mock. The 19-case Cloud
  connection suite passes with those fixture corrections. The full rerun uses
  permission for disposable loopback/Unix sockets, not the current demo.

Final full orchestrator regression: **1,155 cases, OK with 17 explicit skips**
(1,138 executed), in **119.297 seconds**. Its VM/CM/SM and UI-stop messages are
fixture output, not operations on the current demo. Native live tests remain
disabled. No product correction was needed after the fixture fixes.

The first distribution-suite invocation used the developer orchestrator's
Python 3.9 environment, which lacks the builder's declared `packaging`
dependency. It stopped at that import (83 discovered cases, one import error).
The same sources were then checked with the existing private Cloud Python 3.12
candidate, which already contains the pinned dependency; no package installation
or candidate rebuild was performed.
That distribution rerun passes **all 100 tests** in 0.418 seconds. Documentation
validation passes for **284 Markdown documents, 658 stable identifiers and
38 Mermaid diagrams**; `git diff --check` also passes.

## Preserved and remaining

No current catalogue selection was installed. Test .39, Production .31,
Docker, CARLA, native panels, credentials, backend/model data and Cloud objects
were not restarted, modified or operated. No release allocation, signing,
publication, cleanup, commit/push or tag change occurred. Observed free disk was
approximately 101.57 GiB, above the unchanged 90 GiB reserve.

Next: export the complete current application and its runtime configuration/
contract dependencies, bind the existing artifact groups, and only then perform
the authorized preserved-owner handoff and integrated live qualification.
Fresh-engine import/setup, declared container-runtime support, guest/Cloud/UI
E2E, installer, clean Mac and redistribution review remain open. The deferred
[backend/advisory symptoms](distribution-deferred-live-checks-2026-09-26.md)
are not claimed fixed by these packaging changes.
