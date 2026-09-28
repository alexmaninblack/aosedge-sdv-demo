<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Standalone host layout and ordinary-demo handoff

- Date: 2026-09-26.
- Status: Scoped host proof passed; ordinary simulator selected; complete Stage 2 remains open.
- Input: [portable host contract](../../contracts/portable-host-launch/README.md)
  and [runtime work packet](../planning/active/portable-runtime-artifacts.md).
- Preserved baseline: [demo-v1.1 / Factory .39](demo-v1.1-return-point.md).

## Proven causes and bounded corrections

The previous host-layout failure had two independently reproduced causes.

1. Presenter borderless windows really resized in the window server, but
   System Events retained their old Accessibility rectangles. A native-only
   experiment compared both observers over four requested heights. Posting
   Accessibility moved/resized notifications after applying frames made the
   observations agree. This was then added to Presenter source.
2. Unreal's default Game window aspect-ratio lock resized the width as well as
   the requested height. Requests for 914x612 and 914x608 produced 910x611 and
   904x608. The existing Engine setting
   `bShouldWindowPreserveAspectRatio=False`, supplied as a Game launch override,
   produced the exact requested rectangles without a Game rebuild. This is a
   native window setting, not a camera, physics or model change.

Restore now awaits its exact native generation acknowledgement, within the
existing two-second budget, before observing Presenter geometry. The existing
three-point tolerance, missing-evidence failure and ownership checks remain.
No continuous automatic re-layout policy was introduced. A later change in
macOS visible desktop height can still require another explicit Restore.

## Build and isolated proof

Only the small Presenter executable was compiled (2.55 seconds), then locally
ad-hoc signed and strictly signature-verified. Driving Control and web output
were reused after source/input digest checks. Game, cooked content, Factory,
guest services and warm Unreal/compiler caches were not rebuilt or changed.

The successor host closure contains 14,170 files and 20,790,358,693 logical
payload bytes. Its 3,822,640-byte manifest is pinned independently by source:

`de160d783708b649bb60da979e2b66e4d1e7679b72fd50d0324716f135733d98`

All non-UI inputs match the previous host inventory. The isolated final test
uses the current exported application source, the locked successor, synthetic
local TLS and no attached VM/Cloud authority. It proves fresh frames, one
engineering-dashboard role, zero guest roles, idempotent Start with unchanged
owners, repeated Restore, verified background ordering and clean normal Quit.
Start took 48.26 seconds; the complete guarded probe took 88.9 seconds. Peak
owned physical footprint was 14,900,985,912 bytes and minimum free space was
110,539,980,800 bytes. No resource-stop or cleanup error occurred.

The full orchestrator suite reports **1,106 tests, 16 explicit skips, OK**;
the distribution tools report **92 tests, OK**. Documentation validation passes
for 278 Markdown documents, 658 stable identifiers and 38 Mermaid diagrams;
integration and CARLA whitespace checks pass. The restricted first regression
attempt lacked local socket/process-observation permission; the same tests pass
with that permission. The private simulator interpreter lacks the development
`packaging` module, so distribution-tool tests use the existing development
interpreter, not a newly installed runtime dependency.

Regression child processes initially wrote 22 undeclared bytecode files into
the private interpreter, despite the parent using `-B`. The integrity gate
rejected them. Exact generated files in the two affected candidate copies were
removed only after path, source digest and file identity checks; no declared
payload was removed. Subsequent tests inherit `PYTHONDONTWRITEBYTECODE=1` as
well as using `-B`. The inventory rule was not weakened.

## Ordinary-demo handoff

The successor was moved into the existing default artifact catalogue at
`demo-artifacts/aosedge-sdv-demo/host-runtime`. Same-filesystem rename preserved
its inode and did not copy another approximately 19-GiB payload. The preceding
candidate and Stage 1 build inputs remain retained; this is not further disk
cleanup or an external distribution release.

Before this handoff, the ordinary journal still described a source whose Game
and Controller were already absent. The normal Stop reconciled it; its physical
stop result truthfully remained `NOT_OBSERVED`. The old native Presenter was
closed through its owner. Normal Start then used standalone CARLA, private
Python/Gateway and the prebuilt native hosts, without Unreal Editor or compilers.
The Presenter HTTP server uses the private interpreter and shared app entry.

The existing host DNS bridge also had a pre-existing upstream resolution
failure. The existing owned `vm refresh-dns test` operation restarted only that
host helper; no guest resolver, VM or Aos manager restart was requested. Guest
DNS resolved and the same provisioned Test became Online. Normal vehicle select
then performed its Safe Stop/scene handover and attached that same Test with
active per-Unit mTLS. VDP reported `READY`, source `LIVE`, reason `NONE`.

Preservation and final observations:

- Test QEMU remains PID 37277, started on 24 September at 20:20:06, on Factory .39.
- CM, IAM and SM are active with `NRestarts=0`. Unit and Node identities are unchanged.
- Repeated Start is a no-op. The car remains in Safe Stop, speed zero, brake 100%.
- Final native rectangles match within the unchanged tolerance; background
  ordering is verified. Presenter occupies the right column, Game/Controller
  the left. A four-point desktop-height change required an explicit Restore.
- A later sample used about 12.67 GiB for CARLA, 0.041 GiB for Controller,
  0.021 GiB for native Presenter and 1.734 GiB for Test QEMU; memory pressure
  was normal. Approximately 103 GiB remained free. These are samples, not limits.
- No signing, publication, provisioning, model reset, VM replacement or
  Production mutation occurred. Production .31, histories and video assets remain.

## Explicit open gates

**Mixed-interpreter DNS ownership must be resolved before complete ordinary
lifecycle acceptance.** The recovered host bridge is still owned by the
development Python invocation. A read-only call of the existing exact-owner
check finds PID 25648 from the old CLI, but returns
`VM_PROCESS_OWNER_CONTRADICTORY` from private Python. Connectivity is working;
this is an ownership-transition limitation, not a new DNS outage. Private-UI
operations that need to own/restart that helper are not qualified. Do not
weaken matching or infer permission to terminate by port. Carry this into the
next VM/DNS selector slice with an explicit preserved-owner migration proof.

Browser visual review was **not performed**: the browser tool denied access to
the local page. It was not retried through another surface. Native geometry,
process checks, existing CLI and authenticated guest/Cloud observations are
independent evidence, not a substitute for visual review of cards and dialogs.

QEMU/firmware, backend and Cloud-worker operator selectors, complete application
assembly, native UI/guest E2E, clean-host testing and redistribution/notarization
gates remain open. The UI-helper payload is not a complete installer: current
new application modules were exported separately into qualification fixtures.
No source commit, push, tag movement or distribution publication is claimed.

## Local evidence index

The initial manifest and handoff above precede the following blank-page repair.
The current source lock selects its successor, not the initial handoff bytes.

### Blank-page follow-up and Presenter-only repair

The operator reported both Presenter panels remaining white. Initial geometry
success was therefore not functional UI acceptance. Native logs and exact
process starts established the sequence: windows opened at 13:03:40 CEST,
both initial navigations failed at 13:03:41, and the HTTP server process was
started at 13:04:54. The existing client check later called `reloadFromOrigin`
on views with no successfully loaded document; the expected pages never loaded.
The server's entry assets existed with the expected JavaScript/CSS MIME types.

An isolated real-WebKit test using synthetic pages, a disposable loopback port
and no operator state reproduced the original failure: both views stayed empty
after the server appeared. The corrected native host instead loads its fixed
local entry URL. Only previously committed pages require the existing DOM
dialog/submission check; server session/idle guards still apply to every view.
Non-cancellation navigation failures re-arm the same five-second check. There
is no immediate retry loop, command replay, new endpoint or weakened navigation
policy. The current handoff starts HTTP before reopening native windows.

The synthetic native proof passes eight observations: delayed server recovery,
dialog guard, pending-submission guard, subsequent idle refresh, unchanged
identity/no extra reload, busy-server guard, return-to-idle refresh, and recovery
after another transport failure with the same requested identity. The fixture
uses actual WKWebView instances and a fixed synthetic HTML marker, not the
real Presenter page or credentials. It is retained as the opt-in
`test_native_presenter_recovery.py`; enable `RUN_NATIVE_PRESENTER_TESTS=1` on a
macOS graphical test host. `NATIVE_PRESENTER_SWIFT_CACHE` can reuse a warm cache.
The repository-native test passes in 71.225 seconds. The 27 workspace tests and
42 Presenter/server/stop tests pass. The full orchestrator regression reports
1,109 tests in 119.877 seconds, OK with 17 explicit skips (including the native
test, which was run separately with opt-in). Documentation and whitespace
checks also pass. The first diagnostic harness required an
explicit test-process exit; an early final asynchronous sample required a
longer collection window. These harness corrections did not change the fix.

Only Presenter was compiled (2.47 seconds) and ad-hoc signed. The release
updates its executable, nested UI manifest and outer host manifest. All 14,168
other runtime file identities remain unchanged; no large runtime copy was made.
Current manifest: 3,822,671 bytes, SHA-256
`da72bce6d1785424b93564d280f9ae7786f8795437fd9019e89a1082b1db1634`.
Presenter Swift source SHA-256 is
`2fc90d8f972db55f257b3bd1df133835f149af70ecd7d618c02e98969756494f`.

The existing exact-owner idle HTTP stop and native workspace close were used.
HTTP was restarted first; Restore then opened native Presenter PID 51041.
At 14:28:10 CEST WebKit recorded successful commit/finish for both frames;
the ordinary initial build/session refresh also completed for both at 14:28:14.
No failed-navigation event appeared in the bounded observation. Native geometry
and z-order pass. WebKit load completion is recorded separately from the
operator's visual review; browser-tool access remains unavailable.

CARLA PID 26084, Controller PID 26136 and Test QEMU PID 37277 are unchanged.
The same Test is Online, mTLS ACTIVE, guest DNS resolves, and CM/IAM/SM are
active with zero restarts. No guest lifecycle, Cloud mutation, model change or
DNS-owner migration was performed. The independent mixed-interpreter DNS
ownership gate above remains open.

Scoped evidence is in `Build-distribution-stage2-20260926/presenter-recovery`:
baseline/candidate native observations, the temporary proof source, and
`release-004/receipt.json`. `release-004/previous` retains exactly the three old
small files for recovery; it is not another CARLA/Factory copy. Formal build
inputs/receipts remain in `ui-inputs-004` and `ui-helper-004`. Source remains
uncommitted in the existing working tree; no push or tag change is claimed.

Compact non-secret receipts are retained under the CARLA workspace's
`Build-distribution-stage2-20260926`:

- `host-launch-assembly-002.json`, `host-catalogue-promotion-001.json`.
- `ui-inputs-003/build-receipt.json`, `test-bytecode-reconciliation-001.json`.
- `layout-regression-001.log`, `host-handoff-checkpoint-002.json`.
- Native-only resize experiments and `app9-resize-proof.json`,
  `app10-resize-proof.json`, `app11-live-proof.json` in their recorded temporary
  proof root. Earlier attempts remain classified rather than overwritten.

The Stage 1 evidence directory retains guard receipts
`stage2-resize-baseline-001`, `stage2-resize-candidate-001` and
`stage2-host-layout-006`. Historical assembly paths precede catalogue promotion;
the durable catalogue path is the current runtime location.
