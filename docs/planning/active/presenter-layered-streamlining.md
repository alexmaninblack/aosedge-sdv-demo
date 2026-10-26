<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Layered Presenter implementation and qualification packet

Status: operator accepted, 26 October 2026; implementation in the separate
`codex/presenter-ui-stability` branch. Main and public option A do not advance
until the successor's review. This packet supersedes the previous visual
proposal, not its qualified immutable media or retained evidence.

## Accepted product contract

The owning [installed interaction contract](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract)
and [D4 presentation decisions](../../requirements/d4-decision-register.md#d4-026-8)
remain authoritative. This is a presentation change, not another state store,
orchestrator, data interface or authority.

- Vehicle uses the **Layered** architecture. Independent Brake/Tire services
  sit side by side above their shared VDP capability inside one ARM64 virtual
  controller. AosCore is the platform runtime/lifecycle foundation, not another
  telemetry hop. Factory supplies the Linux/AosCore base; it is not an app.
  Vehicle/Gateway, both product backends and Aos Cloud remain outside that
  controller boundary. Retain the existing B2 miniatures and team colours.
- Platform navigation and VDP use the same component miniature. The hardware
  miniature denotes only the controller. Tabs keep Vehicle/Platform/Brake/Tire.
  Tabs open authoring contexts; installed nodes open read-only installed details.
- Keep Installed on this Test separate from Selected package. Only an exact
  reported pending target/active operation supports waiting-for-installation
  language. An earlier published selection is not a requested downgrade; release
  number order alone cannot establish supersession. Keep unknowns explicit.
- Local power/runtime, Cloud connection/report freshness, backend Now, retained
  assessment and native advisory remain independent facts. Retained values keep
  their source dates; unavailable reads do not mean absence, zero or Offline.
- One contextual primary action; repeat preparation is secondary. Preparation,
  signing/publication, first assignment and installation remain separate gates.
  Completion offers results; Stop/Start and Delete remain discoverable in Session.
- Setup owns normal paired Cloud configuration. Presenter shows access facts
  read-only. Exceptional existing repair/inspection controls remain disclosed
  under recovery; opening Session never initiates certificate inspection.
- One bounded detail surface and explicit Back for a child record/software item.
  Preserve its parent view/filter/scroll/focus rather than stack detail modals.
  Confirmation is still separate and names the target and consequence.
- Backend Now and Last assessment are separate. Neutral model-score display,
  humane state labels, compact history with current/earlier-release filters and
  distinct Loading/Empty/Unavailable/Last known states. Historical completed Reset
  receipts move to history; pending/uncertain/current-release outcomes stay visible.
  No data deletion, deduplication or hidden truncation; keep bounded-read notices.
- Operations shows the active job once and completed receipts newest first.
  Keep failures and technical evidence inspectable. Full identifiers remain on
  the server. Routine reports never move the fixed shell or reset profile input.

## Scope and protected material

Writable: Presenter source/tests, its interaction/readme documentation and the
existing M1 qualification selectors/assertions necessary for the accepted UI.
Do not change service algorithms, freshness/timeout policy, Safe Stop, native
driving authority, Cloud endpoints/owners, command guards or at-most-once protocol.
Adjacent Setup/native findings remain separately owned, not silently fixed here.

Preserve current/rollback DMG, retained Test and working disk, all data/history,
certificates, release ledgers, ready CARLA/Factory inputs and verified caches.
Build/packaging/scratch remain on SDV-Dev. M1 uses its internal storage. Docker
is reused without routine Engine restarts. No public distribution or merge yet.

## Ordered gates

| Gate | Work and acceptance | State |
| --- | --- | --- |
| 1. Contract/source | Update installed interaction text; implement all accepted review groups together with state/navigation regressions | Implemented; a captured Cloud inventory clipping correction follows the installed source freeze |
| 2. Local verification | Unit/type/static/docs/confidentiality gates; no developer-Mac browser or runtime | 390 Presenter unit tests, type/web compilation, 92 Python and 46 JavaScript qualification tests, docs and source gates pass |
| 3. M1 visual fixtures | One semantic fixture scenario on M1; layered boundaries, icon mapping, child navigation, state/geometry assertions | 154/154 pass after the captured Cloud row correction, no skips/retries/flaky tests; 39.889 seconds; browser and fixture server closed |
| 4. Immutable media | Freeze successor source; warm Setup/DMG assembly with existing CARLA/Factory and authorized signature | Canonical chain 17/17 built in 768.850 seconds; matching-M1-team media assembled in 540.183 seconds |
| 5. Retained update | Normal package update and launcher selection on M1; exact signature/capacity and unchanged Test/data bindings | Pass for the frozen `.2` candidate; Test and data retained |
| 6. Complete API/UI | One scenario owns ordered API observations then complete visible UI, real independent effects, source-specific statuses, Platform publication checks, Reset/offline/moving-SOTA/Stop-Start and cleanup | Not complete: retained VM dependency/startup failures stop API acceptance; full UI not run |
| 7. Review handoff | Before/after screenshots, timings and explicit PASS/FAIL/NOT_RUN map; preserve Test/data; close owned check runtimes | Partial screenshots and failed attempts retained; final owned runtime closure confirmed; no acceptance or promotion |

Use normal scripted entries under [qualification](../../../scripts/qualification/README.md).
The agent launches the scenario; routine steps do not wait for agent clicks.
Reconcile an uncertain action without replay. A failure closes later gates until
its bounded cause is corrected. No predecessor's passes qualify successor bytes.

## Source acceptance matrix

The captured audit groups map into this one packet: UX26-01 selected package;
02 access ownership; 03 deduplicated summaries/Layered; 04 action hierarchy;
05 Now/assessment; 06 retained history; 07 one detail surface; 08 operations;
09 read-state vocabulary; 10 names/metadata/spacing; 11 lifecycle guidance.
UX26-12 is adjacent Setup/native work and excluded explicitly.

Required negative regressions include: older selection without pending evidence;
stale assignment; missing profile binding; no initial loading-as-empty; Cloud read
failure while local runtime remains running; source-specific offline; partial
backend history; wrong-release result; pending/uncertain Reset; no navigation
mutation; no automatic certificate inspection; one detail dialog; stable anchors.

## Source-gate evidence

The M1-only source fixture campaign covers the canonical 876×908 composition
and compact/tall viewports. It verifies actual peer/shared/base geometry,
unclipped Reset controls, original icon mapping, one visible detail surface and
Back, scoped installed-versus-selected labels, retained records and source-specific
freshness. A current input report must not hide a conflicting product record or
remove the last-known qualification from an incomplete assessment. A late receipt
must not refresh the input source. These are explicit regressions, not changed
readiness rules.

Back uses the original record's presentation reference, not its old row number,
when background receipts change history ordering. If that row is no longer in
the visible page, focus returns to Records rather than another record. The
background-insertion regression was reproduced before correction and passes
with the final source; no history or data authority changed.

Short-screen history uses compact pagination; retained rows are not deleted.
The fixture harness now awaits its asynchronous monitoring read and permits one
normal five-second idle owner poll before asserting an externally changed job.
No product polling interval or freshness limit changed. Earlier failed fixture
attempts remain private, immutable diagnostics; they are not successor acceptance.

The retained-Test, desktop, Cloud and matching signing identity preflight passed
on M1 before media work. The operator completed the exact M1 keychain helper;
the continuation independently reconciled its signature without signing again.
No private key was exported or password recorded.

## Installed successor and qualification boundary

Final Presenter source is `45de82c5241387bf2a5b2a2e587529099f6713bd`;
the reviewed selection is `c2c463c` in this branch. Candidate version is
`1.2.0-rc.4-presenter.2`, application manifest
`bb81fda0338e159477affdae6abcca4bf6aff9f5ffaee12f6962669e42b3e473`.
The canonical local-development-signed DMG is 14,159,627,471 bytes, SHA-256
`a33845d34f3eb8e3683f43c59c4e77acd8e30e1ec49f5756b8f98d2a2511a0cd`.
That original development-team image is not the matching-team installed media.
The M1-team review DMG is 14,158,457,969 bytes, SHA-256
`378863973e01cb65fad2262ea69a61d0515c77795b9e371f325d3779d2fc418d`.
Its application manifest and runtime bytes are unchanged. Neither image is a
qualified public release.

Before the successful build, normal content revalidation handled only the
same SSD's remount device-number change; original receipts and payloads were
preserved. A subsequent first-source build was interrupted with owned cleanup
when the background-insertion focus regression was reproduced. Neither attempt
was delivered or installed, and neither supplies successor runtime acceptance.

The first media continuation found the predecessor `.1` DMG still occupying
the review mount. No new installation had occurred. Read-only reconciliation
proved the exact old mount and zero open handles; normal detach and the normal
new-media owner then completed the retained update. Original failed records
remain separate. Delivery took 172.637 seconds. The install/selection owner
took 250.236 seconds, including 128.874 seconds for install and 75.057 seconds
for selection; media verification accounts for the remaining time.

The installed API attempt passed ten steps before connection failed with
`SOURCE_GUEST_UNAVAILABLE`; shutdown also remained unresolved initially. The VM
was SSH-reachable. Its KUKSA databroker could not bind port 55555 because
`rpc.mountd` owned it, causing VDP/Service Manager startup failures. Bounded
runtime recovery preserved the NFS exports/configuration, restored mountd and
started the databroker. The same held initial-Manual operation was reconciled,
not replaced; fresh authenticated connection and normal shutdown were observed.
This is a transient environment recovery, **not** a permanent Factory fix.

A separate API attempt after recovery passed eight startup checks, then the
controller-start operation returned `PARTIAL`. Normal shutdown passed. Its total
campaign time was 121.226 seconds. Preserve this as another failed attempt,
not a successful retry or complete API result. No new release publication or
full UI sequence was reached. The final probe confirmed zero demo processes and
listeners; observer browsers and display assertions were closed. Shared Docker,
the retained Test, credentials, VM/data, immutable media and caches are preserved.

The visible API observer captured 497 presentation samples with zero fixed-shell
movement/error findings. This is limited startup evidence, not full-flow UI
acceptance. A captured three-component/two-service Cloud summary also exposed a
22-pixel row containing 30 pixels of text when inventory became last known.
The regression was reproduced on M1 before correction. The source-only layout
correction reallocates the same fixed card height; it changes no data or status
semantics. All 390 unit tests, type/web compilation and 154 M1 browser fixtures
pass after this correction, with no skips, retries or flaky tests. It is
**not included** in the frozen `.2` media above.

Before another immutable-media/full campaign, close these bounded items:

1. Own the native VM startup work separately: prevent the NFS/KUKSA port collision
   without disabling an in-use dependency or weakening policy, and preserve its
   cold-start/restart proof. No Factory rebuild is authorized by this packet.
2. Retain the exact reason for partial controller startup, distinguish a running
   guest from completed whole-demo startup, and qualify normal continuation without
   replaying an uncertain action. Do not silently increase timeouts or call a warm
   prestart a cold-start proof.
3. Freeze/package the verified Cloud row correction only after those native gates
   close, then complete the new candidate's API and continuous visible UI campaign.

Main and option A remain unchanged. Adjacent native startup work, a fresh Setup
first use, notarized distribution and the deferred VDP timeout are not qualified
or silently included by this Presenter packet.

## Authorized native-startup investigation and current gate

The operator authorized the bounded native-startup investigation separately.
It preserves the retained Test, overlay, Unit/Node bindings, credentials, Factory
and CARLA inputs. It does not authorize a Factory rebuild, a weaker boot/trust
guard or a change to the VDP timeout.

The `PARTIAL` cause is now confirmed as
`SOURCE_TRUST_BOOTSTRAP_BINDING_UNCONFIRMED`, not a slow guest or a short API
timeout. The API already gives VM start 90 seconds. Earlier recovery called
the inner source-selection owner and proved TLS connectivity, but did not
complete the outer authentication operation, including anonymous-client rejection
and the onboarding commit. Onboarding correctly remained `PENDING`; the strict
retained-boot guard correctly refused it.

Normal `vehicle.initialize` completed that same onboarding through the full owner
chain. The anonymous client was rejected, the exact existing Unit/Node/overlay
binding was retained, and onboarding became `COMPLETE`. The bounded recovery took
113.877 seconds including simulator preparation and verified normal shutdown.
A subsequent unchanged cold VM start completed normally. No journal editing,
certificate replacement, timeout increase or guard bypass was used.

Qualification now checks that retained onboarding is complete before expensive
preparation. Its bounded job projection also preserves the fixed nested VM reason
without exposing arbitrary facts, private text or identifiers to the browser.
These are harness changes, not a new product recovery or trust interface.

The independent NFS/KUKSA collision remains unresolved. A reversible QEMU-only
proof passed one fixed public `sysctl.extra` setting through SMBIOS, intended to
reserve port 55555 from automatic allocation before services start. Read-only
evidence confirmed the setting in the firmware table, but not in systemd's
imported settings or the effective kernel reservation. Factory's Linux disables
both `CONFIG_DMI_SYSFS` and `CONFIG_FW_CFG_SYSFS`; systemd 255 therefore cannot
read either supported firmware transport. The proof was removed by normal VM
shutdown. It installed no guest configuration file or debug payload and changed
no immutable image; ordinary guest runtime writes remain in the retained overlay.
Failed metadata-only proof attempts are not runtime acceptance.

The proposed fixed-public-setting transport is documented by
[systemd 255](https://www.freedesktop.org/software/systemd/man/255/systemd.html#System%20credentials);
the [kernel port policy](https://kernel.org/doc/html/v6.1/networking/ip-sysctl.html)
excludes reserved ports from automatic allocation, not explicit KUKSA binding.
This does not establish support in the current Factory. Do not include the
ineffective QEMU arguments, disable NFS, add recurring NFS restarts, overwrite
other reserved-port settings or change the established KUKSA endpoint.

The remaining change is owned by Factory: provide an early-boot port
reservation that preserves any existing reservations and takes effect before
NFS/KUKSA startup, then prove first boot, repeat, restart, both consumers and
security under the normal deployed identities. An image rebuild requires separate
authorization because the original packet preserved the ready Factory bytes.
On 26 October the operator authorized that exact fix and a Factory rebuild,
using only external SSD storage. The change is limited to normal early-boot
sysctl configuration reserving KUKSA port 55555, preserving other effective
reservations and rejecting an ambiguous or overriding configuration at build
time. Normal finite boot ordering makes both services require the existing
systemd sysctl pass; no recurring restart or new lifecycle controller is added.
Do not change the kernel, firmware transport, service authority or timeout policy.
Reuse available pinned inputs and run static and transient negative/repeat proofs
before image assembly.
The new image is separate from the retained Test's existing backing image:
never rebase or replace that backing image to make the Test appear upgraded.
Until the new-image gate closes, full API/UI acceptance
remains **NOT COMPLETE / NOT RUN**. The installed `.2` candidate and public
baseline are unchanged. All diagnostic check runtimes are closed; shared Docker,
Test data and caches are preserved.

The transient replacement proof passed in a disposable M1 guest network
namespace: 128 IPv4/IPv6 automatic allocations avoided the reserved pair,
explicit port 55555 remained bindable, an existing reservation survived,
idempotent systemd-sysctl reapplication passed, and no fresh AVC was observed.
The parent guest's policy remained unchanged and normal shutdown confirmed no
owned process/listener. This is kernel/configuration evidence, not image boot
or complete API/UI acceptance.

Factory source candidate `.42` is pinned to Platform
`81d098e5a958710d8c12a6bfdb86c7c493274920` in the same separate review branch.
The ready `.41` lock/default and published package remain unchanged. Image
assembly must verify the resulting sysctl file and exact finite ordering before
disk assembly. Existing native/package/security gates remain required.

The retained Builder disk was absent from all connected project volumes. The
operator explicitly authorized a replacement. A new SSD-only Builder passed
host binding, 220-GiB backing-chain, ARM64/Linux clean-state and pinned tool
checks in 147.012 seconds. The old Ubuntu URL returned 404; the new Builder pins
the dated official Ubuntu 22.04 image of 20 October 2026 and its official
SHA-256, with HTTPS-only redirect policy. This changes the build-host input,
not the Factory's pinned kernel or target source revisions. Eight upstream layer
checkouts were freshly acquired and verified by exact commit. Downloads/sstate
are initially empty; dependency acquisition must be explicit and separate from
offline compilation. Builder disk, caches, sources and image output stay on
SDV-Dev; there is no internal-storage fallback.
Explicit `--cold-build` permits bounded 4-hour compile and 2-hour package/image
budgets for the empty cache; warm defaults remain unchanged. This is not a VM,
VDP, readiness or security timeout change, nor permission to compile online.

The cold Factory campaign completed successfully: 926 fetch tasks, all target
compilation, five placeholder/profile regressions, 466 mainline native checks
(two existing skips and two existing disabled cases), KAC/Provider/verifier
tests, package QA, image QA and the built-rootfs port/order gate passed. The
six-partition raw image is 6,997,147,648 bytes with SHA-256
`da97c8754cf502feb2513319f494baa59cc75dcb56087be5a552d7eb6cc416c1`.
Its state remains `BUILT_NOT_LIVE_QUALIFIED`. The campaign took 9,311.062 seconds,
including 1,499.240 seconds of explicit acquisition and 7,795.023 seconds of
offline compile/test/package/image work. Builder/DNS and the owned sleep
assertion exited; the SSD disk, download cache and shared-state cache remain.
Warnings about systemd's root home and embedded build paths are retained; no
QA guard was bypassed. This is not a new-image M1 boot or full API/UI result.

The next isolated M1 cold-boot check uses the existing disposable VM owner,
read-only image and private child overlay, with restricted networking and only
loopback SSH. The already installed portable QEMU/firmware/virtio ROM are reused;
the qualification adapter accepts an explicit resource directory only with the
same pinned ROM as the installed owner. No Homebrew QEMU installation, retained
Test mutation, Cloud enrollment, replacement backing image or security waiver
is part of this boot-policy check. Per-Unit functional/security acceptance and
the complete candidate API/UI campaign remain separate, uncompleted gates.

The isolated M1 image boot-policy gate subsequently passed two cold boots of a
fresh private overlay, using the same frozen `.42` image. On each boot sysctl
reserved 55555 before a normal explicit systemd activation of `nfs-mountd`;
128 IPv4/IPv6 automatic binds avoided it and explicit binding remained possible.
SELinux was Enforcing with zero fresh AVCs. The normal guest poweroff path
closed the two VMs in 5.507 and 4.091 seconds within the unchanged 90-second
exit budget, with no forced termination. The final complete scenario took
163.947 seconds; prior diagnostic attempts remain separate immutable evidence,
not inherited passes. The read-only base image, installed package and retained
Test journal were unchanged, and no owned listener or sleep assertion remained.

The earlier unprovisioned probe incorrectly expected the full NFS server to be
active. Read-only diagnosis showed that it stops after missing normal AosCore
state/storage directories; `mountd` itself had started and then been stopped
with that server. No artificial directories, exports, identity or credential
were added. The boot-policy gate activates only the existing `mountd` unit and
cleans that fixture before normal guest shutdown. A QMP-only test teardown did
not confirm its first exit within 90 seconds; a separate transient proof of the
existing product's guest-poweroff method passed in 5.158 seconds. No product
stop timeout or runtime lifecycle implementation was changed for this test.

This is `UNPROVISIONED_BOOT_POLICY_ONLY`, not a live registered-Unit, KUKSA
authorization, fresh-controller or API/UI acceptance result. KUKSA correctly
remains inactive behind its unprovisioned condition. The retained Test still
uses its original Factory backing image. Full qualification of `.42` therefore
requires a separately declared fresh Test/Unit policy, leaving that original
Test intact; do not rebase its overlay or infer migration from package selection.
No new Setup/DMG, main merge, public input promotion or option-A update was made
by this Factory build and isolated gate.
