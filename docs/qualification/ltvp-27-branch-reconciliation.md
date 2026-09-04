<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP `.27` Branch Reconciliation

- Recorded: 2026-09-04
- State: reviewed; reconciled LTVP experiment branches/worktrees removed after
  clean build and repeated E2E; final branches awaiting remote publication
- Final Solution branch: `codex/ltvp-finalize-27`
- Final Platform branch: `codex/ltvp-finalize-27`
- Final CARLA branch: `codex/ltvp-traffic-manager-order`

This record separates the implementation that produced the accepted `.27`
runtime result from older experiments. It authorizes no branch or worktree
deletion by itself.

## Solution repository

The old successor branches contain three patch-equivalent commits already in
the final branch. The dirty successor Unit Model was not retained: it restored
`formatVersion` and `vendorVersion`, the fields that prevented AosCloud from
sending desired status. Cold-restart qualification later proved that each
isolated launcher profile must pass its selected host DNS port into guest
overlay onboarding. That behavior was reimplemented minimally in the final
branch and is covered by the successor profile tests; no dirty experimental
Unit Model change was transferred.

The old `ltvp-host` and `ltvp-onboarding-socket` branches are intentionally not
merged. They implement large publication/onboarding helpers around
`/api/v11/update-components/upload/`; the accepted component path is the
Deployment Bundle API. The later attempt to simplify the publication helper
still uses that wrong endpoint. The current Test-only contract is retained in
the final branch. The five run-scoped inputs were restored directly for the
completed cold-restart gate; none of the obsolete helpers was revived.

Unrelated BHS and general demo branches are outside this LTVP closeout. They
remain protected until their owning work is separately reconciled.

## Platform repository

The factory-runtime, KAC, KUKSA scope-parser and VDP-family changes are either
patch-equivalent to the final history or superseded by later corrected files
in it. The dirty `ltvp-vdp-v1-readiness` copies of `providerarchive.hpp` and
`runtime.cpp` are byte-identical to the final branch; the final runtime test
file contains later corrections. No dirty Platform source change needs to be
transferred.

The one non-patch-equivalent KAC factory-integration commit is an older
aggregate. The final branch contains the selected substrate plus subsequent
runtime, PKCS#11 and `.27` corrections. Replaying the aggregate would regress
that reviewed state and is prohibited.

## CARLA repository

Every committed experimental runtime branch is an ancestor of
`codex/ltvp-traffic-manager-order`. No committed CARLA runtime change is
missing.

The dirty `ltvp-launcher-current` worktree contains unqualified installer
hardening for build-root validation and atomic app/command replacement. It did
not produce the accepted runtime behavior and is excluded from the `.27`
runtime branch. It may be handled later as an independent launcher change; it
must not be silently mixed into this clean-build baseline.

## Deletion result

After the clean build and repeated E2E passed, the reconciled LTVP experiment
worktrees and local/remote branches were removed. The following final-state
checks remain:

1. publish the three final branches and verify their remote heads match;
2. retain the immutable `.27`, final VDP bundles and compact evidence;
3. leave unrelated BHS/general-demo work untouched;
4. run the post-publication regression and disk audit.
