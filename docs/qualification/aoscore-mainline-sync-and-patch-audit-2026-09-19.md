<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore mainline synchronization and demo patch audit

Date: 19 September 2026. Status: source/history research only; no upgrade,
candidate build, deployment, restart or new live qualification.

## Conclusion

Recent upstream fixes are real and relevant to platform reliability. They do
not remove the particular Communication/Monitoring lock cycle captured in the
[preserved CM failure](cm-monitoring-disconnect-deadlock-2026-09-19.md).
Both main and the newer develop were inspected, including their callers, not
only commit subjects or the body of `Disconnect`.

A migration can reduce our patch set. The shared-gRPC-write backport is already
present exactly; other service lifecycle fixes are partly superseded. Permission
capacity and IAM reply sizing are not superseded. The component runtime API
has changed, so simply bumping the source revision is not a complete migration.
These conclusions are source-level; no unmodified-upstream runtime A/B test was
performed, and no patch was removed from Factory .35.

## Exact upstream snapshot

Public Git refs were resolved freshly and history inspected in isolated copies.
The existing platform build checkouts, recipes and running Test were untouched.

| Repository/ref | Resolved commit | Meaning |
| --- | --- | --- |
| `aos_core_cpp/main` | `9d613a46df3c7f550062e2f19ae3406c57715694` | Main at inspection; latest commit dated 14 September |
| `aos_core_lib_cpp/main` | `5560291ba6914e36a5b841ade4d8fc54134a9e91` | Main and peeled v9.1.2 release commit |
| `aos_core_cpp/develop` | `673f857241b9a2c140cbeef93f9901f5597adcc2` | Newer development changes, not main |
| `aos_core_lib_cpp/develop` | `8ceaddfe21c4f6f7ef518c281bf5dfab60bc48ed` | Newer development changes, not main |
| `aos_core_cpp/v9.1.2` | `a46d1cba03955b9c2fde175360de63c32ba1be87` | Peeled release tag; main additionally fixes download-filesystem selection |
| `aos_core_api/main` and v9.1.2 | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` | Already the accepted demo API pin |

The inspected [main CMake dependency declaration](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/CMakeLists.txt#L112)
selects library and API v9.1.2 when no existing dependency directory is supplied.
Our recipes explicitly supply private dependencies, currently library
`60cb83535f773762c61ac5f544b31b7b88c502e3` (v9.1.0) and the API pin above.
Changing only the application revision would therefore not upgrade the library.
Factory image labels and AosCore library release numbers are different version
namespaces; do not infer the source baseline from `.35` or `6.1.1` alone.

## Synchronization fixes that are already in main

| Upstream change | What it actually fixes | Relation to this incident |
| --- | --- | --- |
| [6e0b198: shared gRPC writes](https://github.com/aosedge/aos_core_cpp/commit/6e0b1980e71ea6ee9979292a8aa336574d317f09) | Serializes synchronous requests and asynchronous messages on the same CM–SM gRPC stream | Our exact backport; not the Communication/Monitoring mutex pair |
| [e8cb3ba: UpdateRunStatus deadlock](https://github.com/aosedge/aos_core_cpp/commit/e8cb3ba91461f88528901dd53170692990ad719d) | Releases SM ContainerRuntime lock before invoking a status receiver | Similar AB/BA class, but different objects/process path |
| [6a7c259: MonitorContainers deadlock](https://github.com/aosedge/aos_core_cpp/commit/6a7c259ce7933f8d2c5bd67fc520a9f6f947b230) | Copies Runner status under lock, then calls receivers outside it | Useful precedent for callback discipline; does not modify CM disconnect |
| [96cfae0: container monitoring race](https://github.com/aosedge/aos_core_cpp/commit/96cfae0efea77ba5d2e43d33fd55eb49f30bdf22) | Protects concurrent SM monitoring-cache insert/erase/lookup | Not Cloud connection recovery |
| [c2f7db6: slow CM–SM shutdown](https://github.com/aosedge/aos_core_cpp/commit/c2f7db6665c93eeab599018ec60da3f7d9cf60a1) | Bounds gRPC server shutdown while the SM stream stays connected | Different blocking point from the captured mutex wait |
| [e0d95ec9: timer callback completion](https://github.com/aosedge/aos_core_lib_cpp/commit/e0d95ec9093ede869f455e6d16b4188d2f5047ec) and explicit Stop modes | Adds callback-aware timer stopping and adapts call sites | Changes timer lifecycle, not the nested Monitoring send lock |
| [8775b57f: SharedPtr reference counts](https://github.com/aosedge/aos_core_lib_cpp/commit/8775b57f36e3036e80ec7d1443e1a14ce0ff76a7) | Makes reference counting safe after allocator redesign | Important dependency of the new allocator baseline; unrelated to this wait cycle |
| [ed1dba10: last-instance network teardown](https://github.com/aosedge/aos_core_lib_cpp/commit/ed1dba107430d2ad33cb651faf0f69e567fd77ec) | Atomically claims shared network cleanup among parallel instance removals | Relevant to SOTA/cleanup, not the external network toggle |

The main branches also contain running-container/network adoption, batched
network setup/rollback, failed-stop handling and image-install synchronization
changes. These make migration valuable but enlarge the required regression
scope: successful startup alone cannot qualify the replacement baseline.

## Develop: closer to the symptom, but not closure

[393b188](https://github.com/aosedge/aos_core_cpp/commit/393b188fa8c2462b619612ecdf62de58c7205bdf)
triggers connection teardown after a send-side network error, makes
`mIsConnected` atomic, and suppresses duplicate disconnect notification.
[498b6a0](https://github.com/aosedge/aos_core_cpp/commit/498b6a0e0aa24b7ca6d66da69082902e0d7f2ab3)
ensures a socket shutdown exception does not skip disconnect callbacks.
Neither commit is in the inspected main; both are in develop.

Critically, removing the lock from the body of `Disconnect` did **not** remove
it from the call chain. In
[develop Communication](https://github.com/aosedge/aos_core_cpp/blob/673f857241b9a2c140cbeef93f9901f5597adcc2/src/cm/communication/communication.cpp#L781),
`HandleConnection` takes `mMutex` immediately before calling `Disconnect`.
`CloseConnection` still calls `NotifyConnectionLost`, which invokes subscribers
synchronously. The new send-failure path also calls `CloseConnection` while
holding the send worker's transport lock.

In [develop Monitoring](https://github.com/aosedge/aos_core_lib_cpp/blob/8ceaddfe21c4f6f7ef518c281bf5dfab60bc48ed/src/core/cm/monitoring/monitoring.cpp#L290),
`SendMonitoringData` still holds its own mutex through the external sender call.
`OnDisconnect` still needs that mutex. Thus the demonstrated lock dependency
remains in source. Different recovery timing could affect whether it happens
on a particular run, but is not proof of elimination.

The develop commit
[7c7b9af1, titled lock-order/lock warnings](https://github.com/aosedge/aos_core_lib_cpp/commit/7c7b9af14f24944823571e44476304591740340d),
adds two `NOSONAR` comments in Alerts and ImageManager. It does not change runtime
locking and is not a fix for this deadlock. The newer DNS host-map race fix is
also a different boundary. No assertion is made about unpublished branches or
platform-team changes not present in these refs.

## Disposition of our native deltas on a main migration

“Remove” below means omit when constructing an approved, qualified successor,
not remove from the current .35 image or diagnostic VM.

| Current delta | Upstream comparison | Migration disposition |
| --- | --- | --- |
| CM `0001-serialize-sm-stream-writes` | Exact upstream code already in main. Reverse patch dry-run against the isolated main checkout passed without changing files. | Remove duplicate backport on migration. Retain stream concurrency tests. |
| CM `0002-reconcile-stale-instance-snapshot` | Main `SetStatus` keeps observed status and updates only an exact active identity/version; an unknown old version logs a warning rather than becoming the desired one. The explicit rejection of a status belonging to another node is not present in `UpdateRunningInstances`. | Replace the already-native reconciliation part with upstream; retain/decide the cross-node validation separately. Do not reapply the old whole patch mechanically. |
| CM `0003`/`0004`, periodic idle full status | No `idleFullStatusInterval` implementation was found in main. New reconnect fixes are not equivalent to periodic full status. | Not shown redundant. Requalify the original Cloud-status case before deciding whether this workaround can be dropped. |
| CM `0005-preserve-pending-startup-rebalance` | Main still overwrites `doRebalance` with `SetSubjects` instead of combining it with the pending flag. | Not superseded at this site; retain the regression and determine the minimal adaptation. |
| SM `0001`, systemd-slot VDP component | Demo-owned component integration, not a generic container fix. Native `RuntimeItf` now requires `InitInstances`; our runtime has no implementation of that method. | Retain integration intent and adapt to the new interface. Preserve explicit Safe Stop semantics. |
| SM `0002`, idempotent teardown | Main maps crun ENOENT/ESRCH to not-found and callers tolerate not-found. Network teardown has changed substantially. However namespace unmount still returns an error for EINVAL and the old empty-unmounted-file proof is not implemented; error normalization is not identical to our exact-state guard. | Partly superseded; split into proved obsolete pieces and still-required ownership/error cases. Run exact exited-container, absent namespace/veth and permission-failure tests before pruning. |
| SM `0003`, failed replacement preservation | Main preserves a failed stop task's status, replacing part of our correction. Preparation still resets an existing record to inactive; image removal lacks our surviving-instance guard. | No full equivalence established. Port the failed-stop/network-release/old-version regression to the new lifecycle before deciding the remaining delta. |
| SM `0004`, retry failed same-version preparation | Main `PrepareInstances` resets an existing record to inactive and continues, without the explicit reprepare branch. | Not shown superseded. Re-test transient/permanent preparation failures against the new phases. |
| IAM `0001`, permission reply capacity | Main still allocates `StaticArray<FunctionPermissions, cFuncServiceMaxCount>` in `GetPermissions`, not `cFunctionsMaxCount`; no develop change to that handler was found. | Retain correction and 17–32-function reply regression. |
| Function-key length 256 in CM/SM/IAM | Main default remains 32; develop's equality-operator changes do not increase it. | Keep the accepted build configuration consistently across modules. |
| IAM PKCS#11 allocator/cache overrides | Main allocates SessionContext through injected allocator. `SESSIONS_PER_LIB` remains a definition/constant but no longer sizes that allocator in inspected source. The session-cache-size setting still has a real effect. | Old allocator-capacity override is a pruning candidate; do not conflate it with the three-entry cache. Recheck simultaneous AosCloud/AosCore/KUKSA sessions and renewal before changing the pair. |

The table scopes native patches and directly related build configuration. It
does not authorize deleting KUKSA trust/input projection, service mounts, the
VDP component lifecycle or service application changes. These are integration
requirements, not automatically obsolete because upstream container handling
has improved.

## Other migration blockers and limits

1. **Current reconnect defect:** still present in the inspected main/develop
   source paths. A new baseline is not by itself a demonstrated remedy.
2. **Known shared-storage deletion:** main still removes version-less service
   storage in `ServiceInstance::Remove`, reached from old cached-version cleanup.
   UID-pool and startup-adoption fixes do not establish version-shared storage
   retention. The [separate handoff](aoscore-shared-storage-handoff-2026-09-19.md)
   remains applicable; Park/Resume is not re-enabled by this research.
3. **API/build compatibility:** injected `AllocatorItf` and runtime
   `InitInstances` require coordinated application/library/VDP-integration
   adaptation. Our native launcher extension cannot simply remain byte-for-byte
   unchanged against the new pure-virtual interface. No compile was attempted.
4. **Baseline selection:** use immutable application/library/API revisions,
   not a mixture of mutable main/develop and the old recipe-private library.
   Prefer the platform team's qualified main/release set; develop-only fixes
   need an explicit baseline decision.

## Recommended next sequence

Separate the **upstream convergence** decision from the **immediate reconnect
defect**. They may share a future image, but they have different acceptance.

1. Keep the failing .35 Test and compact evidence unchanged. Give the platform
   team the exact main/develop lock-chain references for review; no external
   message or issue was sent by this audit.
2. First create an isolated deterministic concurrency regression with the real
   Communication/Monitoring relationship (and Alerts equivalent). Use it to
   qualify the team's fix, rather than accepting one successful ON/OFF run.
3. If migration is approved, pin the chosen upstream triplet, omit the exact
   gRPC backport, and adapt only the residual integration/bug-fix deltas in the
   table. Carry forward their existing negative and lifecycle regressions.
4. Compile and run focused CM/SM/IAM, permissions, VDP Safe Stop, service
   replacement and storage tests before a Factory build. Do not conceal a
   failed native test by restoring a removed workaround without recording it.
5. Build one successor after those gates. Qualify clean provisioning, every
   functional version transition, offline local analytics/auth renewal,
   stopped backend ingress, exact queued delivery, Cloud Online and Finish.
   Do not mix this with the preserved diagnostic run or mark excluded storage
   restart retention as passed.

## Evidence and workspace disposition

Performed: fresh official Git ref resolution, isolated full-history inspection,
selected main/develop source comparisons, recipe inventory, exact gRPC reverse
patch applicability check, and documentation gates. Public web rendering failed;
official Git source was available and used instead.

Not performed: binary builds, native tests, live upstream A/B, patch activation,
VM/CM/SM/IAM restart, network toggle, Cloud mutation or production change.

Isolated public-source audit copies are retained at
`/private/tmp/aos-mainline-review.XHIYcT` (17 MiB at inspection); no credentials
or runtime payloads were copied there. The platform worktree remains unchanged.
Only this report and its link in the preceding diagnosis were added/updated.
