# Presenter UI

## Current Studio integration — 13 September 2026

The accepted visual/interaction reference is [Studio 2.8](../../docs/demo/mockups/aosedge-demo-interaction-mockup-2-8.html), qualified by the current [UI-STUDIO-026 amendment](../../docs/demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
The original mockup is unchanged. Live state comes from existing Demo Control operations, not mockup timers.

The physical workspace remains CARLA upper-left, the combined native Driving
Control/telemetry below, and Studio on the right. CARLA is neither embedded nor
restyled. The shared header contains brand, accepted vehicle assignment and
Session; team navigation belongs to the right panel.

### Operator flow

1. Full story: choose Factory firmware, Create controller, start simulator,
   Connect in Manual. Create prepares current Test and the product backends,
   not Production. It does not provision.
2. Platform: choose a capability profile, Prepare, Sign & publish. Release
   allocation stays in Demo Control. Publish before Provision supports the
   warehouse scenario; no forced downgrade or batch-approval step is added.
3. Provision to Test / Continue registration completes only the remaining
   native stages. Cloud Online is not inferred from local connectivity.
4. VDP installation follows native Safe Stop. Installed and Pending are Cloud
   facts; VDP process state is **Not reported by Cloud**.
5. Brake/Tire: Prepare, Sign & publish through the configured Service Provider.
   The first READY release exposes Deploy to Test: Demo Control first runs
   `service runtime-prepare test`, then OEM binds the dedicated retained Group
   Subject and exact service identity, preserving its peer. Preparation failure
   prevents assignment; unchanged inputs are reused without an SM restart.
   Later higher releases use only Publish. No service update requires Safe Stop.
6. Backend cards open product results; Aos Cloud opens Software/Resources.
   Component/service cards expose only their scoped details.
7. Session offers Park, Resume and Finish demo via the existing lifecycle.
   Finish retires only owned Test state; Factory originals, Cloud releases and
   release continuity survive. Production remains untouched.

Quick preparation is an explicit alternative composing the existing Test-only
sequence. Opening a page never starts it. The contextual guide derives the next
action from observations; it cannot manufacture missed intermediate states.
Studio simulation Start/Stop always pass `--target test`; the unscoped CLI
simulation path is not used by Presenter actions.

### Evidence and safety boundaries

- Right-side inventory/runtime/resources are Aos Cloud only. No guest read is
  introduced by tab entry, Refresh, details or monitoring. Resources preserve
  node/service/Subject/instance/partition identity. CPU is DMIPS; unknown units
  remain unconverted. Missing/stale is not zero, absent, Offline or success.
- Team backends use the existing same-origin Demo Control backend read. Product
  receipts are explicitly **synthetic**, current-Test scoped, and versioned.
  They do not qualify vehicle analytics or in-vehicle advisory while the Cloud
  permissions/KUKSA defect remains open.
- Native telemetry observes vehicle data only. It reads the existing advisory
  contract, rejects unknown values, and does not consume synthetic backend data.
- Confirmation shows actor, exact candidate, target and effect. Cancel emits no
  mutation. VM credentials use the existing macOS Use once / Save in Keychain
  dialog; no password, native capability, caller-selected shell/path/endpoint
  enters the browser.
- One writer/job, no queue and no automatic mutation retry. Reload does not
  cancel work. Lost responses reconcile the original request ID. Unknown native
  outcomes refuse new mutations; terminal recovery remains an engineering
  intervention, not an invented Cancel/rollback operation.

### Observation and native refresh

Visible Cloud panels share an in-flight-deduplicated observer. Entry/re-entry
refreshes; pending state backs off from 2 to 10 seconds, idle reads use 10 seconds.
Hidden panels stop scheduling reads. Local operation receipts poll independently
at one second active / five seconds idle. Local snapshot reads do not hash images.
Local lifecycle snapshots refresh immediately when the tab becomes visible or
the window regains focus, and on manual Refresh/post-action observation. These
reads share one in-flight request and otherwise retain the visible-only 10-second
idle interval. CLI retirement therefore returns the open page to Create without
a reload; a still-partial retirement remains blocked. Refresh never retries a
mutation, starts a runtime or substitutes local data for Cloud software status.
Prepared service receipts are a bounded metadata-only projection; published
service processing is observed separately from installed/runtime state.

The native host checks a small build/session descriptor every five seconds.
Both windows reload together only when the native job is idle and neither
window has a dialog or unresolved submission. It never restarts VMs, CARLA or
services. Updated native host source requires an explicit workspace close/restore;
subsequent frontend builds and idle server session changes are detected in place.

### Build and run

Use the project's pinned Node/npm versions. In this package:

```bash
npm ci
npm run typecheck
npm run test:unit
npm run test:browser
npm run build
```

Then, in the installed `apps/demo-orchestrator` environment:

```bash
democtl ui serve
```

Open `http://127.0.0.1:18080/`. With simulation running,
`democtl workspace restore` places the native surfaces. `democtl ui stop` refuses
to stop a busy or uncertain server. `workspace close` closes only Presenter.

`npm run dev -- --host 127.0.0.1 --port 18070` is the development server;
`?fixture=ready` explicitly selects retained deterministic fixture review.
Fixtures never submit external actions and are not live qualification evidence.
Without a fixture selector, an unavailable local backend stays unavailable.

See the [delivery plan](../../docs/planning/active/demo-studio-delivery-plan.md)
and [implementation receipt](../../docs/qualification/studio-2-8-implementation-2026-09-13.md).
The scoped .33 CLI E2E and isolated browser tests do not replace the final fresh
operator UI cycle or human visual acceptance.
