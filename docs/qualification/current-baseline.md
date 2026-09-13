<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current working baseline

Recorded: **13 September 2026**. Engineering Test E2E passed with explicit
synthetic-service and Cloud-ordering exclusions. This is not full product or
human visual acceptance.

## Factory and runtime

| Item | Current value |
| --- | --- |
| Immutable Factory | `6.1.1-maninblack.33/main-qemuarm64` |
| Artifact | `$WORKSPACE_ROOT/demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.33/main-qemuarm64.img` |
| Image SHA-256 | `a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761` |
| Image size | 6,997,147,648 bytes |
| Image build source | `f7922b02b15f6cf816f181e1bf97572b61859aea` in `aos-vehicle-platform` |
| Test Unit | `7e09f53d-d716-4ed3-a8b4-a8f0793c987c` |
| Test system UID | `e1d2fc93c9c84ae79c7de98facee256a` |
| Test role set | Test Vehicles, `f83dee0e-d93c-4dd2-905f-a3b4f8dc9878`, verification set |
| Fleet | Default Fleet, `3871b7c7-c105-4cac-bec9-d9e4447c2a3d` |
| Qualified VDP sequence | 21/V1 -> 22/V2 -> 23/V3; current23, 23 signal paths |
| Qualified Brake sequence | 9/V1 -> 10/V2 -> 11/V3; current11 |
| Qualified Tire sequence | 8/V1 -> 9/V1; current9, no functional Tire V2 claimed |
| Production | Existing .31 preserved and excluded from this Test qualification |

The factory placeholder is not a preinstalled service or VDP application.
Current Unit/installed releases are dated run evidence, never a manufacturing
source. New runs allocate new release numbers automatically through Demo
Control; they do not reset the current number ledger or downgrade Cloud releases.

## Proven and excluded

The [detailed E2E](factory-33-e2e-2026-09-13.md) covers clean provisioning,
VDP Safe Stop gates, service replacement while driving, real native containers,
explicitly synthetic backend delivery/retry, external-network recovery and
cold stop/start without transient manager fixes. Only component application
depends on Safe Stop; Brake/Tire SOTA does not.

**Still open:** native KUKSA permissions and real service/advisory behavior;
Cloud stale connection-event ordering; complete Studio visual/product acceptance;
upstream review and workspace/lock reconciliation. .33 includes an idle full-status CM
workaround, not a Cloud fix. See the
[consolidation audit and open-issue register](factory-33-consolidation-audit-2026-09-13.md)
and [current delivery plan](../planning/active/demo-studio-delivery-plan.md).

The tested source set is now committed and published on `main` in all seven
custom repositories, with `checkpoint/demo-20260913` return-point tags.
See the [exact source and branch-cleanup receipt](factory-33-source-checkpoint-2026-09-13.md).
Historical workspace/lock metadata still needs reconciliation; its older pins
must not be mistaken for this published source set or a fresh-clone qualification.

## Historical evidence

The former contents of this page are preserved as the
[Factory .21 baseline of 30 August](factory-21-baseline-2026-08-30.md).
Older .27/.31/.32 qualification records describe their dated experiments, not
the current Test or permission to operate Production. .31 remains retained for
the existing Production VM; .33 is the current Test image.
