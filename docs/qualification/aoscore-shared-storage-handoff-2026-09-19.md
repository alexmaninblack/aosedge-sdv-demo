<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore CM: old-version cleanup removes current shared service storage

Date: 19 September 2026. Status: reproduced; upstream handoff prepared,
not submitted. This report contains synthetic test identities, not credentials
or runtime payloads. No product fix is included.

Subsequent operator authorization and the separately prepared correction are
recorded in [the local fix qualification](cm-shared-storage-fix-2026-09-19.md).
This original report remains the unchanged-baseline reproduction, not a claim
that the proposed correction is already deployed or accepted upstream.

## Summary

CM stores separate instance records for service versions, but persistent
storage is identified by service ID, Subject ID and instance index, without
the version. Removing an obsolete record unconditionally removes that shared
storage, even when a current-version record with the same identity survives.
Observed consequences were lost model/outbox/observation state after restart.

| Source / proof | Result |
| --- | --- |
| `aosedge/aos_core_lib_cpp`, pin `60cb83535f773762c61ac5f544b31b7b88c502e3` (9.1.0) | Reproduced with unchanged product sources |
| Upstream main inspected at `5560291ba6914e36a5b841ade4d8fc54134a9e91` (9.1.2) | Same unconditional removal found by source inspection; this report does not claim an execution against main |
| Existing launcher test suite | 17 passed |
| Added missing-image and expired-version retention cases | 2 failed, 0 disabled |

## Code path

At the tested pin, all paths below are in `src/core/cm/launcher/`:

1. `instancemanager.cpp:74`: `Start()` calls `ClearInstancesWithDeletedImages()`;
   it also calls `RemoveOutdatedInstances()` at line 80.
2. The missing-image path at line 455 and expired-version path at line 435
   retire a stored service instance through `ServiceInstance::Remove()`.
3. `instance.cpp:416`: removal calls the storage-state interface with only
   `mInfo.mInstanceIdent`, then removes the version-specific instance database
   row with `mInfo.mInstanceIdent` **and** `mInfo.mVersion` at line 424.
4. `instancemanager.hpp:261`: `cRemovePeriod = Time::cDay`; a timer also invokes
   expired-version cleanup during operation. This is not solely a boot path.

The cleanup call therefore has a broader data scope than the record being
retired. Neither Cloud status handling nor SM container execution is required
to reproduce it. No Cloud-side change is proposed here.

## Minimal reproduction

Apply the [test-only patch](../../tests/upstream/cm-shared-storage-retention-regression.patch)
to the exact library pin above. Use the repository's launcher GoogleTest target,
or the [focused harness](../../tests/upstream/cm-storage-harness/CMakeLists.txt) with the
same source checkout and an installed GoogleTest package.

- Create a valid image/configuration for service version `2.0.0`.
- Store an active `2.0.0` record and a cached `1.0.0` record sharing the same
  service/Subject/index. The older record is 25 hours old under the fixture's
  one-day cached TTL.
- Missing-image case: do not retain the old image. Expired-version case: retain
  both images so cleanup is driven by the cached record's expiry.
- Initialize and start the actual native instance manager/launcher.
- Assert that the old version-specific row is gone, the current row remains,
  and the storage-state mock has **no** removal request for that shared identity.

Both added tests fail at the last assertion; the old/current database row
assertions pass. These are production-code executions with mocked dependencies,
not a separate reimplementation of the removal algorithm.

Example, after checking out the pin, applying the patch and installing GTest:

```sh
cmake -S /path/to/cm-storage-harness -B /path/to/proof-build \
  -DCORE=/path/to/aos_core_lib_cpp -DCMAKE_PREFIX_PATH=/path/to/gtest-install
cmake --build /path/to/proof-build --target aos_core_cm_launcher_test
ctest --test-dir /path/to/proof-build --output-on-failure
```

The executed proof used Linux ARM64, networking disabled, and GoogleTest 1.14.0
at `f8d7d77c06936315286eb55f8de22cd23c188571`. The focused harness compiles
the original launcher/tools/crypto/test-utility sources; it avoids unrelated
SoftHSM whole-library fixtures. OpenSSL/mbedTLS are not needed by these cases.
The initial JSON result at 05:42:59 UTC contains 19 tests, 2 failures and
0 disabled (0.336 seconds), SHA-256
`533a9f29d0eb4a104c21f83cee5a56ac71774592f75add2f2f5c825e567f39ee`.

## Live correlation and limitations

The retained demonstration VM's monotonic boot journal showed six shared
storage removals while cached old-version records were cleaned. The active
service versions returned Online, but Brake restarted from its initial model
and Tire had no model. Both durable function counters restarted; unchanged
backend histories correctly rejected conflicting content for reused identities.
See the [local qualification record](preserved-test-function-observation-2026-09-19.md)
for scoped evidence. The isolated unpatched proof separates the defect from
existing demonstration image patches and Cloud timing assumptions.

The expiry regression exercises cleanup on Start with an expired old record;
the periodic timer's use of the same method is source evidence, not a 24-hour
wall-clock experiment. Data loss on every restart or every service upgrade is
not claimed: obsolete records/images must enter the relevant cleanup path.

## Proposed acceptance for an upstream fix

Separate version-record retirement from shared-storage ownership. Preserve
storage while another version with the same service/Subject/index remains;
remove it when the last owner is genuinely retired. This is a proposal for
review, not an implemented patch. Cover active and cached survivors, missing
images, expiry, multiple old records, final-owner cleanup, Subject/index
isolation, repeat startup and error paths; retain all existing launcher tests.

The demo's accepted [ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md)
removes operator Park/Resume without extending native CM. It does not repair
periodic cleanup or claim platform restart retention is qualified.
