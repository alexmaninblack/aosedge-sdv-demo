<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Troubleshooting installation and builds

Start with the exact [release](release-status.md), failed action and message.
Preserve the Test and error details. Do not rebuild the simulator, reinstall
everything or delete state as the first response.

## Installation and first use

| Symptom | Next action |
| --- | --- |
| Runtime Kit missing | Open Setup from the complete matching DMG, with its Runtime Kit beside it. The integrated Setup does not search for substitute kits. Never mix packages. |
| Signature or inventory mismatch | Stop and compare the descriptor/checksum. Do not edit installed files or expected pins. |
| Insufficient space | Use Setup's logical payload estimate plus its 90 GiB reserve. Compressed DMG size is not installed size. |
| Docker unavailable | Complete Docker's first-run prompts and check the local ARM64 engine. Leave an already-running engine alone; opening Dashboard is not a preparation step. |
| Cloud access failure | Confirm the intended Production or Staging domain, OEM/associated SP and exact access route. Existing certificates determine the domain; new enrollment uses the selected environment. Missing objects or an occupied Test are distinct from failed authentication. |
| No accounts or issuance tokens yet | Follow [Cloud access from scratch](installed-preview-cloud-first-use.md#new-cloud-access): register in the intended environment and use its paired OEM/SP welcome emails. Setup issues certificates; it cannot grant account permissions. |
| Existing certificate is rejected locally | Use distinct owner-private, valid, unencrypted PKCS#12 files containing RSA keys for the same environment. Password-protected files and authentication-only EC keys are not this signer's supported input. Obtain a suitable pair through the account owner/Setup; do not upload private keys to a converter. |
| Uncertain token submission | Use **Inspect saved attempt**. Do not replay the one-time token blindly or replace working credentials. |
| VM access asks for an unknown password | Use the public development Factory password documented under [VM access](installed-preview-cloud-first-use.md#open-presenter-and-create-the-test), not your Mac or Cloud password. A custom image uses its owner's own password. |
| macOS requests access | Grant the specific normal consent to the signed app. Window placement uses Accessibility; installation does not require blanket Full Disk Access. |
| Presenter opens without a controller | **Open SDV Lab** opens Presenter only. Use **Create controller** for a new Test, or **Demo controls → Runtime → Start controller** for a stopped retained Test. CARLA and Driving Control follow the readiness guide. Do not recreate an existing Test to start it. |
| Presenter closed, but the demo still consumes resources | **Close Presenter (keep demo running)** closes its window only. Use **Demo controls → Runtime → Stop demo and keep data** for a non-destructive stop. **Delete Test & start over** is not a generic Close button. |

Follow the [installation steps](installed-preview-cloud-first-use.md) and
[operator sequence](../operations/current-demo-workflow.md).

## During the demo

- **Pending update:** uploaded, assigned, installed and functionally ready are
  separate. Check exact profile/release; VDP application needs Safe Stop.
  Publish versions sequentially, not all at once.
- **Only Continue preparation is offered:** inspect Activity and its reported
  reason. Continue the same recorded unfinished work; do not create another
  Test or repeat a publication. The [step-by-step sequence](../operations/current-demo-workflow.md#preparation-and-version-sequence)
  distinguishes Full story from Quick preparation.
- **Unavailable or Monitoring:** inspect local input/advisory readiness
  separately from backend receipt. Missing data alone is not a VDP version
  mismatch. Follow the displayed missing-input or stale-data reason; do not
  change model thresholds to force a Ready indication.
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
| A build command/tool is missing from a fresh Terminal | Rerun the same downloaded launcher and choose **2 / B**. It restores the selected workspace environment and checks tools; no manual shell-variable reconstruction or sourcing is required. See [preparation](macos-developer-tools.md). |
| Node/npm version differs | Rerun **2 / B** and use its version check and isolated workspace installation. Do not replace a global Node or guess a newer version; the launcher owns the exact selected toolchain. |
| No Apple Development signing identity | Follow [Apple signing access](macos-developer-tools.md#apple-signing-access). An Apple Account or certificate without its local private key is not yet a signing identity. A installation needs no personal signing key. |
| Public input catalog or archive unavailable | Check internet access and the reported provider error. Ordinary builds need no Google login or binding JSON files; contact the release owner if a public link is unavailable. |
| Interrupted transfer | Inspect the operation; reconcile its remote ID or reuse verified ranges/cache. Never create a duplicate or retry blindly. |
| Checksum/metadata mismatch | Preserve and investigate the exact object. Do not promote it or accept a new expected hash from the download itself. |
| Wrong/missing build volume | Reconnect the original selected volume. The launcher does not switch to another disk automatically. |
| Docker storage fails capacity or compatibility checks | Use the reported Docker backing-disk requirement. Project and Docker storage may be separate local volumes; an internal disk is not itself an error. The build does not relocate Docker. |
| Dirty checkout or foreign output | Preserve it. Select an empty owned workspace or resolve the exact change; do not reset another checkout. |
| SSD device number changed | Use explicit `lab revalidate` only for supported completed input groups. It does not adopt changed content or repair all receipt types. |
| A build step fails | Keep earlier outputs, diagnose the first failing owner and repeat the same chain. Gateway resume requires its explicit inspected path. |
| Build ends with `CHAIN_BUILT_NOT_QUALIFIED` | The DMG was built; it has not been installed or published by this command. [Mount that exact output and open its Setup](reproduce-demo.md#install-your-build), not route A's selected package. |
| A rejects a DMG that you just built | Expected: A and `--dmg` verify the selected published package, not arbitrary developer output. Follow [install your build](reproduce-demo.md#install-your-build); do not replace the public checksum. |
| Repeating B still uses an older source revision | Repeats resume the retained selection. Use a [new empty parent](unified-macos-launcher.md#start-a-new-build-selection) for a deliberate fresh selection, not a pull/reset inside prepared sources. |

Use the [developer guide](reproduce-demo.md) and
[launcher recovery reference](unified-macos-launcher.md#repeat-and-storage-behavior).
Do not repeat a full transfer merely to refresh status.

## Report an issue and stop safely

Record root revision, descriptor/checksum, host/OS, exact action, bounded error,
last completed stage and whether an external operation began. Redact passwords,
keys, tokens, raw Cloud responses and vehicle/customer data. Keep raw diagnostics
outside Git; share only the necessary sanitized evidence.

Stop demo-owned processes through their owners and close their windows after
testing. Preserve Docker Engine and unrelated workloads. Stopping preserves
state; **Delete Test & start over** irreversibly retires the selected Test and
is not a generic cleanup button. Eject storage only after all consumers release it,
including any separately managed shared Docker disk.
