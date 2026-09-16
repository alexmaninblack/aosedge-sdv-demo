<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Staging IAM permission response capacity — 15 September 2026

## Scope and result

Preserved Factory .33 Test, staging only. Production was not touched. No new
Factory image was built. This is a targeted authorization proof, not the full
real-data/advisory or UI acceptance run.

| Item | Evidence |
| --- | --- |
| Test system UID | `6fcf5a740b744ef0a05d44bad598ab94` |
| Cloud Unit | `42c0bf43-4eb7-44e6-8c74-f60f9959da66` |
| Cloud domain | `aws-stage.epmp-aos.projects.epam.com` |
| Components/services retained | VDP67 functional V2, Brake45 functional V2, Tire28 functional V1 |
| Tire Subject | `ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb` |
| Tire release source | `0f84c15677e406932a3a86255a7bd09d5812a558` |
| Tire deployment | `e5900178-7762-43fb-905b-abdd16498cc9` |
| Tire version ID | `157fc192-8335-4fb3-b07d-926f80c1ac51` |
| IAM candidate SHA-256 | `a945cfeabd4edb0c4ba3d2a5772c84a2455b9d8f4d400d69ea4449c29cea472c` |
| Build baseline | Platform `f7922b02b15f6cf816f181e1bf97572b61859aea` with the existing 256-byte key overrides |

## Cause, not a Cloud/Subject workaround

The official pinned IAM app's
[`GetPermissions`](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/iam/iamserver/publicmessagehandler.cpp)
allocates a reply array using `cFuncServiceMaxCount` (16). The
[registered permission map](https://github.com/aosedge/aos_core_lib_cpp/blob/60cb83535f773762c61ac5f544b31b7b88c502e3/src/core/common/types/permissions.hpp)
uses `cFunctionsMaxCount` (32). The
[handler rejects a smaller output array](https://github.com/aosedge/aos_core_lib_cpp/blob/60cb83535f773762c61ac5f544b31b7b88c502e3/src/core/iam/permhandler/permhandler.cpp).
Tire supplies 17 exact permissions; Brake V2 supplies 12. The preserved IAM
journal recorded 39 get-permissions failures and 39 insufficient-memory
messages, with zero registration/parser failures. KAC mapped that RPC error
to `IAM_UNAVAILABLE`.

The patch replaces only the response-array capacity constant. It does not
increase registered permission counts, change path lengths beyond the already
approved 256 bytes, add permissions, alter Subjects or bypass native IAM.

## Execution and proof

All build, package publication and guest operations used Demo Control:

1. Build/prepare/sign/upload Tire28 with fixed non-secret bootstrap rejection
   codes; reconcile Cloud `READY` and native assignment without rebinding.
2. `component core-permissions-build test --iam-response-capacity`: targeted
   ARM64 IAM compilation, 48 C++ target flags checked. The first patch attempt
   stopped before compilation because the monorepo path was wrong; its compact
   log/manifest were preserved. The exact pinned path was corrected, then the
   one-line patch compiled successfully. Builder stopped after both attempts.
3. `component core-permissions-apply test --iam-response-capacity`: hash-checked
   candidate in `/run/democtl-iam-response-32/aos_iam_app`; immutable installed
   bytes preserved. Existing IAM bind drop-in points to that candidate. SM then
   IAM stop, IAM then SM start reconstruct native in-memory registrations. CM
   is neither stopped nor replaced, and committed VDP state is unchanged.
4. Post-read: IAM PID42465, SM PID42482, CM PID10061; all active, NRestarts0.
   IAM's fresh bounded journal has zero permission/insufficient-memory errors.
   Both native service tokens are regular owner-private mode0400 files; no
   credential content was read into evidence. Tire logs authorization READY.
5. Repeat apply reconciles to `noOp: true`, with the same three PIDs.
6. Cloud at21:25UTC reports the same Test Online and both service instances
   active. This does **not** qualify functional analytics.

Artifact manifest: `demo-artifacts/aosedge-sdv-demo/runtime-proofs/core-permission-iam-response-32/manifest.json`.
The earlier 256-byte candidate and failed-patch evidence are retained outside
Git. No build binaries, tokens or runtime state are added to source control.
Platform source-only checkpoint: `35df5be` (local, not pushed in this increment).
The separate, still-unqualified KAC policy/startup changes were excluded from
that commit. Demo Control, Presenter and this receipt remain in the solution
working tree pending closure/review of the current increment.

## Remaining gates / human decisions

- **Tire threads:** runtime observation shows bootstrap1 + product7 threads
  against native pidsLimit8, and repeated `pthread_create failed` / resource
  unavailable messages. Authorization can issue a token, but the product
  cannot establish a stable gRPC session or token-renewal lifecycle. A measured
  change to16 (other quotas unchanged) requires the quota contract's review;
  the question is submitted, not implemented. Latest backend function-status
  records still report access unavailable. Do not mistake those old/error
  reports for current IAM denial after the fix.
- **Brake V2/V3:** no accepted real V2 assessment yet. Exact equality of all
  signal timestamps plus250ms freshness is too strict for the observed chain.
  Pinned KUKSA converts incoming client time into `source_ts` while exposing
  its per-datapoint broker `ts` in VAL output. A truthful five-second assembly
  amendment, changed profile identity and persistent-state compatibility need
  explicit review. No timestamp normalization or model-state reset was applied.
- **Tire model:** raw dispersion/slip-persistence arithmetic remains an open
  accepted-contract question. The product intentionally retains
  `MODEL_CONTRACT_UNRESOLVED`; no synthetic substitute was injected.
- **KAC policy:** the previously authorized hash-guarded six-hour recovery
  under `/run/democtl-kac-time-read-proof` remains transient, with rollback
  deadline approximately02:18UTC on16September. Canonical policy/rootfs remain
  unchanged. This is not a persistent Factory fix or completed security gate.

Presenter displays actual backend function-state/reason and stale-report
markers. Explicit mock history cannot qualify the real-data story. Older
release results do not qualify the active release. The UI correction is not a
claim that the full UI-only scenario passed.
At21:34UTC the refreshed Presenter showed the same Online Test, VDP67, Brake45,
Tire28, and the Tire backend's explicit `NOT READY / SERVICE ACCESS DENIED`
report with its source/receive time. This was a read-only UI verification,
not a substitute for a successful real Tire product result.

## Tests actually completed

- 122 focused Demo Control tests: component/runtime, permission capacity,
  service inputs and backends.
- 133 Presenter unit tests; typecheck and production bundle build passed.
- 3 Platform capacity tests, including native C++ 32/256-byte key boundaries
  and 16/17/32/33-element array boundaries.
- Targeted real ARM64 IAM compilation, live first apply and idempotent repeat.
- Full service processing/advisory, pre-Factory UI replay, consolidated Factory
  build, clean UI run and final transient-policy rollback remain **not passed**.
