<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo version 1.1 — source return point

Prepared24 September2026 for **AosEdge Platform - SDV Lab**, at the operator's
request to commit and publish the current demo and mark version1.1.
The annotated integration tag is **`demo-v1.1`**, following `demo-v1.0` naming.
Publication was reconciled on 24 September 2026: annotated tag object
`c7207e8fb061c753e66088663f251b8482274f0d` peels to integration commit
`862d48b158e0f0980f80bb40eb0837453e21788e`; local and remote agreed.
Hosted Repository boundaries run `36047149195` passed on that exact commit.
Subsequent documentation corrections do not move this tag or rebuild its image.

## Frozen composition

The integration commit is the commit peeled from `refs/tags/demo-v1.1`.
The tagged [workspace manifest](../../workspace/repositories.json) fixes all
eight dependency repositories; the [checkpoint](../../workspace/checkpoints/demo-v1.1.json)
records retained Factory provenance, native core inputs and dated installed releases.
The dependency manifest SHA-256 is
`59e5e6a4e3117e922e0180cfc58e388321049ec9998a8c7d5aa70e6e2fc60d96`.

| Repository | Source revision |
| --- | --- |
| CARLA | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| Unreal Engine, restricted | `9b705d6d2db5b769ab34edb04f3ca2bb8b960014` |
| Vehicle Gateway | `98b0b70a0c16cb96475d2c34755a80a817e4a190` |
| Vehicle platform | `793b1fc035d2b7c123f9a4161788955f389bb81d` |
| Brake service | `230cdd4515d1be94ef342197ff56f6b76498aff2` |
| Brake backend | `42395715103d9f512c2586a2c9b98c3975c06ab7` |
| Tire service | `8639b57535e32e3fb2ce68f10794c90d39bb5ae5` |
| Tire backend | `026018a47daa3b37ff1f4404954e8e48e70336b4` |

Version1.1 includes the coordinated pinned AosCore migration, retained component
and source restoration at controller boot, security/package corrections and
host ignition recovery. The Gateway delta is a test of the existing native
motion/speed projection, including20,000 synthetic sample transitions; it does
not change production behavior. Workspace and hosted-CI dependency pins agree.
Older immutable component/R6.1 release locks remain historical inputs, not the
effective Factory39 native core pins; those are recorded in the checkpoint and
the platform's pinned recipes, validators and `DEPENDENCIES.json`.

## Retained artifact and evidence

- Factory **6.1.1-maninblack.39**, raw image6,997,147,648 bytes, SHA-256
  `741a9717c4152dfe9baa997fcdd948fa5662e71473b0a7c91faba942aa63c557`.
- Dated current Test installation: **VDP117/V3, Brake92/V3, Tire49/V1**.
  These are independently numbered deployed releases, not renamed to1.1.
- [Factory build and isolated smoke](factory-39-build-2026-09-24.md),
  [raw reboot and full process ignition](factory-39-ignition-2026-09-24.md),
  and [five-minute externalOFF/ON](factory-39-offline-2026-09-24.md)
  retain their exact proof scope and exclusions.
- [Artifact cleanup](factory-39-cleanup-2026-09-24.md) removed superseded
  image/build outputs. Factory39 and Production's dependent Factory31 remain.
  The old36/37/38 image binaries are no longer retained; their source/manifests
  and compact evidence remain. Neither the1.0 nor1.1 tag stores those binaries.

This is a recoverable **source milestone**, not a claim of complete all-version
E2E or fullP8 acceptance. Factory39's manifest remains
`BUILT_NOT_LIVE_QUALIFIED`. Brief advisory readiness transitions, delayed backend
freshness after reconnect and the reused-release117 Presenter profile binding
observation remain open. Cold boot with externalOFF, nonempty-queue power loss,
longer soak and a fresh serial V1→V2→V3 cycle are not newly qualified by this tag.
Automatic host sleep/wake recovery remains separate accepted planning.

## Publication checks and exclusions

Before dependency publication, Platform's contract,217 Python tests (two skips),
repository policy, public-source scan and REUSE passed. The Gateway's native
motion projection test passed locally. The full local Repository boundaries
gate passed: integration365 tests; Platform217 (two skips); Brake23 Python
tests (five skips),8 host CTests and its separate V2 test; source/license gates
and component locks. Presenter typecheck and324 tests across32 files passed.
Documentation passed264 Markdown documents,658 stable identifiers and38 Mermaid
diagrams. Staged and history confidential-input checks passed. The initial
Presenter unit invocation could not write its temporary Vite config in the
sandbox and ran no tests; the properly authorized rerun passed without changes.
Checkpoint hash, all eight local/remote dependency pins and Factory provenance
were independently reconciled. Platform hosted run `36046615364` passed on its
exact published revision. Hosted integration run `36047149195` subsequently
passed on `862d48b158e0f0980f80bb40eb0837453e21788e`, closing that publication gate.
The hosted job covers integration/Platform/Brake/Gateway source boundaries;
it does not run native CARLA, the real VM, all UI/browser cases or the full
Tire/backend suites. No new live E2E, package build or VM restart is implied.

Only demo-owned source, tests and documentation are published. Existing private
video/material scratch, local credential-template experiments, build artifacts,
credentials, runtime journals and warm caches remain outside Git publication.
No broad `git add`, history rewrite or change to upstream restricted visibility
is part of this checkpoint. Production and the running Test are not mutated.

## Restore without overwriting the running setup

Use a **new empty workspace**, not the existing working demo:

```sh
git clone --branch demo-v1.1 https://github.com/alexmaninblack/aosedge-sdv-demo.git
git -C aosedge-sdv-demo rev-parse 'demo-v1.1^{commit}'
git -C aosedge-sdv-demo ls-remote origin 'refs/tags/demo-v1.1*'
```

The local peeled commit must equal the remote `demo-v1.1^{}` entry. Clone each
dependency into its manifest directory and detach the **new clone** at its
exact `acceptedRevision`; restricted Unreal source still requires licensed
access. Use the [reproduction guide](../getting-started/reproduce-demo.md) and
Factory39 build record for prerequisites. Do not reset current checkouts,
replace overlays or start/provision/upload anything just to inspect the tag.

Git restores source and documentation, **not** a VM snapshot, image backup,
Cloud identity, credentials, model data or release ledger. Preserve a separate
Factory39 backup and the Production31 backing chain. Never restore an old
`.local/release-continuity.json` to reuse allocated release numbers. Published
service/component packages and image provenance remain independently versioned.
