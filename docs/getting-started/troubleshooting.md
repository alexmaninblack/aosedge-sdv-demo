<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Troubleshooting installation and builds

Start with the exact [release](release-status.md), failed action and message.
Preserve the Test and partial evidence. Do not rebuild the simulator, reinstall
everything or delete state as the first response.

## Installation and first use

| Symptom | Next action |
| --- | --- |
| Runtime Kit missing | Open the complete DMG or explicitly select its matching kit. Never mix packages. |
| Signature or inventory mismatch | Stop and compare the descriptor/checksum. Do not edit installed files or expected pins. |
| Insufficient space | Use Setup's logical payload estimate plus its 90 GiB reserve. Compressed DMG size is not installed size. |
| Docker unavailable | Complete Docker's first-run prompts and check the local ARM64 engine. Leave an already-running engine alone; opening Dashboard is not a preparation step. |
| Cloud access failure | Confirm staging, intended OEM/associated SP and exact access route. Missing objects or an occupied Test are distinct from failed authentication. |
| Uncertain token submission | Use **Inspect saved attempt**. Do not replay the one-time token blindly or replace working credentials. |
| macOS requests access | Grant the specific normal consent to the signed app. Window placement uses Accessibility; installation does not require blanket Full Disk Access. |
| Presenter opens without a controller | **Open demo** opens Presenter only. Use Create Controller for a new Test. Native power-on of a stopped retained controller remains a limitation, not a passed returning-user flow. |

Follow the [installation steps](installed-preview-cloud-first-use.md) and
[operator sequence](../operations/current-demo-workflow.md).

## During the demo

- **Pending update:** uploaded, assigned, installed and functionally ready are
  separate. Check exact profile/release; VDP application needs Safe Stop.
  Publish versions sequentially, not all at once.
- **Unavailable or Monitoring:** inspect local input/advisory readiness
  separately from backend receipt. Missing data alone is not a VDP version
  mismatch. Load-sensitive readiness and the recorded VDP timeout remain
  deferred; do not lower thresholds to hide them.
- **No backend data with external network OFF:** expected delivery loss does
  not prove local services stopped. Check local products, then queued delivery
  after ON.
- **Zero network counters:** native accounting can exclude the private backend
  route. Zero does not prove no traffic, and bytes are not automatically a rate.
- **Delayed reset:** accepted/pending is not applied. Reset Driver Advisory
  affects only the selected service and preserves its result history.

## Build and acquisition

| Failure | Next action |
| --- | --- |
| Root or producer commit missing | Obtain the exact source-handoff revision. An old tag or latest branch is not an implicit substitute. |
| Drive bindings/access missing | Obtain both approved binding files and authorize Google CLI separately. No credentials in Git. |
| Interrupted transfer | Inspect the operation; reconcile its remote ID or reuse verified ranges/cache. Never create a duplicate or retry blindly. |
| Checksum/metadata mismatch | Preserve and investigate the exact object. Do not promote it or accept a new expected hash from the download itself. |
| Wrong/missing SSD | Reconnect the original bound volume. No fallback to the internal disk. |
| Docker disk is internal or remote | Correct this host prerequisite through normal maintenance before building. `lab` does not relocate Docker. |
| Dirty checkout or foreign output | Preserve it. Select an empty owned workspace or resolve the exact change; do not reset another checkout. |
| SSD device number changed | Use explicit `lab revalidate` only for supported completed input groups. It does not adopt changed content or repair all receipt types. |
| A build step fails | Keep earlier outputs, diagnose the first failing owner and repeat the same chain. Gateway resume requires its explicit inspected path. |
| Built but readiness is false | `CHAIN_BUILT_NOT_QUALIFIED` is expected before qualification. Source-ready, input-ready and qualified are separate. |

Use the [developer guide](reproduce-demo.md) and
[recovery reference](../development/release-reproduction-r2.md#storage-and-recovery).
Do not repeat a full transfer merely to refresh status.

## Report an issue and stop safely

Record root revision, descriptor/checksum, host/OS, exact action, bounded error,
last completed stage and whether an external operation began. Redact passwords,
keys, tokens, raw Cloud responses and vehicle/customer data. Keep raw diagnostics
outside Git; share only the necessary sanitized evidence.

Stop demo-owned processes through their owners and close their windows after
testing. Preserve Docker Engine and unrelated workloads. Stopping preserves
state; **Finish demo** irreversibly retires the selected Test and is not a
generic cleanup button. Eject storage only after all consumers release it,
including any separately managed shared Docker disk.
