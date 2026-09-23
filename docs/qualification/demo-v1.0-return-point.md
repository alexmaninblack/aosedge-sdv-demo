<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo version 1.0 — source return point

Prepared 23 September 2026 for **AosEdge Platform - SDV Lab**.
The immutable annotated integration tag is **`demo-v1.0`**. Its creation gate
is a successful hosted boundary run on the tagged commit and verified remote
dependency revisions. Verify the remote tag before using this return point.
The milestone does not renumber VDP, Brake, Tire or Factory releases.

## What defines this version

- Integration: the commit peeled from `refs/tags/demo-v1.0` in this repository.
- Eight dependency repositories: exact `acceptedRevision` values and remotes
  in the tagged [workspace manifest](../../workspace/repositories.json).
- Retained image provenance and package retention:
  [checkpoint manifest](../../workspace/checkpoints/demo-v1.0.json).
- The dependency manifest SHA-256 is
  `087b6c704107db6bb8e07ffcd160283d8012a0c7f42abaaf4dd3b601675aa5b2`.
  Branch tips can subsequently move; use the tagged manifest, not later `main`.

| Dependency | Revision |
| --- | --- |
| CARLA | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| Unreal Engine (restricted) | `9b705d6d2db5b769ab34edb04f3ca2bb8b960014` |
| Vehicle Gateway | `453b7948006d0264b0cede17816aaf551485b3cf` |
| Vehicle platform | `50a66b73dfc11361c2b8457934b3a0d4a7118dfe` |
| Brake service | `230cdd4515d1be94ef342197ff56f6b76498aff2` |
| Brake backend | `42395715103d9f512c2586a2c9b98c3975c06ab7` |
| Tire service | `8639b57535e32e3fb2ce68f10794c90d39bb5ae5` |
| Tire backend | `026018a47daa3b37ff1f4404954e8e48e70336b4` |

## Restore source without overwriting the working demo

Create a **separate empty workspace** and clone integration there:

```sh
git clone --branch demo-v1.0 https://github.com/alexmaninblack/aosedge-sdv-demo.git
git -C aosedge-sdv-demo rev-parse 'demo-v1.0^{commit}'
git -C aosedge-sdv-demo ls-remote origin 'refs/tags/demo-v1.0*'
```

The local peeled commit must equal the remote `demo-v1.0^{}` entry. Clone each
dependency into its specified sibling `directory`, then detach that **new
clone** at its exact `acceptedRevision`. Access to the restricted engine source
and its license remains required. Do not reset current working checkouts,
rebase existing overlays or automatically start/provision/publish anything.
Follow the [reproduction matrix](../getting-started/reproduce-demo.md) for host
toolchain, build and environment prerequisites.

Git restores source and documentation, **not a running demo snapshot**. Image
bytes, credentials, backend data, Cloud identity, published packages and warm
build caches are not stored in this tag. The .36 Factory original is retained
locally; retain a separate backup for recovery from disk failure. The existing
Production overlay still depends on the .31 backing image; neither is deleted
or silently switched to .36. Check the image manifest on transfer, using its
recorded size/digest. No multi-gigabyte image was rebuilt for this milestone.

Do not reset `.local/release-continuity.json` when restoring source. Its audit
values are VDP105, Brake83 and Tire46. Current and rollback packages remain:
VDP base inputs and existing releases89+, Brake70+ and Tire41+. This includes
the scoped readiness correction98/78/44, earlier full UI progression and the
film family99/100/101 +79/80/81 +45. Retention is not a claim that every prepared
candidate has been live-qualified. Obsolete signed payloads selected for cleanup
are not promised reproducible byte-for-byte; their compact receipts are kept
privately outside the active package catalog.

## Evidence and limits

Local source gates passed: Platform193 tests; integration365 tests; Presenter
typecheck and322 unit tests; Brake host8 CTest plus V2 and its Python suite;
Tire host5 CTest, Python suite and20 backend tests. Skips and individual
boundaries are recorded in the [source audit](source-checkpoint-progress-2026-09-23.md).
The subsequent Linux CI correction passed19 targeted local tests.
Platform hosted static/REUSE run `35849649346` and Brake hosted run
`35849650797` passed on the manifest revisions. Integration run `35854668400`
passed on `b3b0f3907c205bf51d94e5a2496134305ad67495`; the final documentation
commit must pass again before tag creation. Integration's Repository boundaries job
checks integration/Platform/Brake/Gateway; Tire is checked out for document
links, not advertised as a standalone Tire CI suite. Verify the successful
integration run attached to the tagged commit in GitHub Actions.

The first integration hosted run exposed macOS-specific temporary paths and
missing CI checkout/tool dependencies. Test fixtures now use the resolved host
temporary directory, and CI provides pinned Tire source and `qemu-img`.
No production launcher security check was disabled to accommodate Linux.
The publication guard permits only57 previously reviewed image path/digest
pairs and the approved QEMU example URLs in exact files. Negative tests retain
secret, changed-image, unrelated-path and unrelated-private-URL rejection.

Latest repository-contained live proof is
[VDP98/V3, Brake78/V3, Tire44/V1 readiness renewal](advisory-readiness-renewal-2026-09-20.md).
The earlier [complete UI lifecycle](presenter-ui-timing-e2e-2026-09-20.md)
records version progression, offline local operation, queued delivery and
Finish. This source milestone is **not a new E2E, full P8 acceptance or Factory
promotion**. The .36 manifest remains `BUILT_NOT_LIVE_QUALIFIED`; remaining
negative/reboot/calibration gates are not erased. Automatic host sleep/wake
recovery is still planned. No current Cloud status was inferred or changed.
Private video materials, active repository runtime files and warm caches are
outside this cleanup/publication packet and remain untouched.
