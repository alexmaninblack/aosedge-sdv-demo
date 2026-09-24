<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .38 successor candidate — 24 September 2026

Status: source gate in progress; image **not built or live qualified**.

## Scope and source checkpoint

The operator authorized closing the diagnostic/security stage and moving to a
new Factory and fresh E2E. [Diagnostic closure](factory-37-staging-e2e-2026-09-23.md)
records the proof and exclusions. Platform checkpoint:
`378c00efad0ec67b2fb0c90328b68c4e8970b511`.

The candidate keeps the coordinated mainline triplet and adds only the proved
SM asynchronous-status correction, exact three-rule KAC/crun integration and
seven optional VDP-probe deny/dontaudit decisions. No diagnostic collector,
temporary credentials, core, policy lease or live state enters the image.
Demo Control also prepares all VDP profiles with the reviewed common runtime,
preserving7/15/23 signals, V3-only advisory and existing immutable release bytes.

Historical VDP109 SIGSEGV remains unexplained and unclaimed as fixed. The reviewed
current runtime passed deployed-identity transport fault/security tests and live
observation without recurrence. Stop a new run on recurrence and collect bounded
evidence under a separately scoped capture; do not hide or retry a crash away.

## Mandatory ordered gates

1. Clean committed source; Platform202cases/200pass/2skip, policy25/25,
   exact recipe reconstruction, license/secret/whitespace checks.
2. Host and warm Builder each at least60GiB free; offline network/fetch guards,
   effective pins and actual compiled source bindings. Do not clear caches.
3. Compile CM/SM/IAM, KAC and refpolicy. Execute production-toolchain regressions,
   including **32 SM launcher cases** (five additional asynchronous/identity
   negative controls); retain .37's27-case historical matrix unchanged.
4. Package QA, source/configuration checks, then one image/assembly; hash at
   creation and transfer, freeze read-only with BUILT_NOT_LIVE_QUALIFIED manifest.
5. Isolated new overlay clean boot/repeat; expected empty Factory identity and
   metadata, labels, security/manager health, no diagnostic residue.
6. Fresh staging E2E only with exact publication/provision/retirement authority:
   VDP V1→V2→V3 and Brake V1→V2→V3, Tire V1, each next release uploaded only after
   its predecessor is installed and checked. Safe Stop gates VDP, not QM updates.
7. Stable service UID/storage/quotas and Cloud metrics, real local advisories,
   independent Reset/history retention, Return to road and UI timing/status
   observation. External network OFF must stop backend ingress while local
   processing/token renewal continues; ON must recover Online and drain queues
   without duplicates or a manager restart. Cold persistence is a separate check.

Preserve the existing .37 Test, Cloud Unit, storage, .36/.37 images and evidence
until successor acceptance. No new signing, publication, provisioning, retirement
or Production action is implied by the build command. Do not change the accepted
solution baseline pin or call the candidate qualified on compilation alone.

## Execution log

-12:16:25UTC: temporary core collection explicitly disabled/removed; no captured
  real core. Stock policy restored, Enforcing, all live managers/VDP unchanged.
- Source/recipe reconstruction passes for CM4patches/SM4patches/IAM2patches.
  Platform license/secret gate passes244files. No collector/debug pattern found
  in the platform recipes or Factory specifications.
- Demo Control regression1043cases:1027passed/16skipped; focused Factory
  matrix38/38 after the exact .38 pin assertion. Documentation/whitespace pass.
  Printed restart/stop messages in unit tests are mocks, not live mutations.
- Pre-build space: host162GiB, warm Builder106GiB. No image construction yet.
