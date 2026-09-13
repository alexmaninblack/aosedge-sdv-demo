# Presenter UI

## Current integration position — 13 September 2026

The accepted target is Studio 2.8 with Test-first shared Demo Control actions.
The architecture map already reads installed service versions from Cloud;
team views read per-Subject instances and their own backend observations via
the same-origin adapter. Unit/browser/build evidence is recorded in the
[Presenter checkpoint](../../docs/qualification/demo-mocked-backend-integration.md#presenter-and-adapter-verification-12-september-2026).

Complete service publication/assignment controls, native visual alignment and
human acceptance remain P4/P8 in the [delivery plan](../../docs/planning/active/demo-studio-delivery-plan.md).
The .33 CLI E2E does not close those UI gates or real KUKSA/advisory operation.
Do not present synthetic backend records as vehicle data. Older dual-VM,
approval and header wording below documents earlier shell increments, not the
final Studio contract or a claim of current visual acceptance.

Platform Team now refreshes its Test state from **Aos Cloud only** on entry
and re-entry, with a manual Refresh Cloud state action. It displays Cloud
Online/lifecycle, installed and pending releases, update state and latest
published release. Running/READY/Safe Stop and functional-profile mapping are
not inferred from Installed or from release numbers. No direct VM status or
guest-log action is available in the panel. Stale/unavailable observations are
explicit, with no background Cloud polling or duplicated native-header read.

The local header distinguishes the accepted vehicle assignment from a fresh
connection probe: `SELECTED_NOT_PROBED` uses `selectedVehicle` and says
“Connection not rechecked”, rather than treating `currentVehicle: null` as
Not assigned. Unknown/conflicting state remains unavailable. This does not
add background guest or Cloud reads.

The accepted Presenter shell exposes local observations and explicitly
authorized Demo Control operations. Mutation buttons show actor, exact selection,
target and effect before confirmation; Cancel does nothing. Credentials and
the private native session capability never enter the browser.

The original fixture-only `WP-P1-UI-001` remains available explicitly through
`?fixture=ready` (or another fixture ID). Fixture actions never submit externally.

The primary operator action is **Prepare demo**, not a sequence of engineering
buttons. It invokes `democtl demo prepare`'s application operation: both VMs,
automatically numbered v1, signing/upload/approval, provisioning, simulation and
initial Test connection in stationary Manual. The native run journal exposes
progress even for a CLI-started run and across UI-server restarts. The page never
auto-starts a mutation on load. Individual steps remain under Engineering steps.

VM access uses a visible macOS dialog with Use once / Save in Keychain / Cancel.
There is no password prompt in a hidden terminal. Access can also be configured
with `democtl access setup`. Keychain storage is only by explicit dialog choice;
passwords never enter the browser, logs, argv or repository. Native input follows
[Apple's hidden-answer dialog guidance](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/PromptforText.html).

Use Node `26.0.0` and npm `11.12.1`:

```text
npm ci
npm run typecheck
npm run test:unit
npm run test:browser
npm run build
npm run dev -- --host 127.0.0.1 --port 18070
```

Append `?fixture=<id>` to select an accepted deterministic presentation state.
Without that parameter, the app requires the local Demo Control backend and
shows unavailable state if it cannot be reached; there is no fixture fallback.
Fixture identifiers are owned by
`src/adapters/fixtures/fixtureCatalog.ts`.

For the local review, build the existing package once with `npm run build`,
then run `democtl ui serve` from `apps/demo-orchestrator` in its installed virtual
environment. Open `http://127.0.0.1:18080/`. Ctrl+C stops only this foreground UI
server, not VMs, simulation or Cloud Units. No daemon or background auto-start
is installed. The server serves only the built entry point and assets, uses
loopback/Host/Origin checks and returns a fixed public projection of existing
`status` and `image list` operations. Background reads do not hash image files,
read guest/Cloud state or expose credentials/host paths. Local
reads repeat every ten seconds while the browser page is visible, without
overlapping polls or retaining old green states after an unavailable response.

The fixed same-origin `/api/presenter/operations` route accepts create/start/stop
both VMs, provision both roles, simulator start/stop, Test connection, selected
VDP prepare/unpack/inspect/sign/verify/upload/approve/Cloud-state,
explicit Cloud access and reset. It invokes the same core as CLI; no arbitrary
commands, paths, profiles, Cloud endpoints or Production FOTA target are accepted.

The backend alone owns a 256-bit capability for private loopback port 18600,
stored in a temporary directory (0700), file (0400). The native API rejects
browser Origin headers and missing capabilities. Normal shutdown removes both
listeners and the capability; no daemon is installed. Enter first-SSH passwords
only in the visible macOS dialog (or reuse Keychain). Keep the server open during jobs.

Submissions return a receipt immediately. Progress is polled locally every
second while a job runs / five seconds while idle, without Cloud polling. One
job, no queue, no automatic retries. Duplicate IDs return the original receipt;
a changed session generation rejects old submissions. Unknown outcomes block
new mutations; reconcile through existing native journals, never blindly repeat.
Page reload does not cancel a job. Stop the UI server only when idle.

Order: create both vehicles → prepare/sign/upload/approve a new v1-profile
release on Platform Team → start VMs → provision → start simulator → connect
Test. Then use increasing v2/v3-profile releases and native Safe Stop. Engineer
CLI guest observations remain separate from the Cloud-only Platform panel:
Cloud approval is not proof of running VDP. Profile
cards describe the workflow; timestamped operation results are actual evidence.

Reset calls applicable existing operations: simulation stop, deprovision,
Unit delete, VM stop, environment retire. Never-provisioned environments skip
Cloud steps from the owned journal; empty environments use existing retire/orphan
checks. A blocker stops the sequence. No backups; original images and Cloud
releases remain. This is engineering cleanup, not qualified scenario R0.

The existing native Presenter physically places the separate CARLA, Controller
and Terminal dashboard windows, the shared header/right panel and black
background. The operator accepted the built-in-display composition. This is
not qualification of a one-click launcher, a fresh-environment UI E2E or the
accepted prebuilt-container hosting contract. The
[native desktop plan](../../docs/planning/active/native-demo-desktop.md) will
combine control/telemetry and add a launcher; CARLA stays separate. Production
FOTA is visibly deferred; Brake/Tire navigation is retained
without simulated service results. VDP functional profiles v1/v2/v3 are
distinct from future monotonically increasing Cloud release versions.
