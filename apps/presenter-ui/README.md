# Presenter UI

## Current Presenter

Vehicle uses a layered ARM64 controller view: independent Brake/Tire services,
their shared VDP capability, and the AosCore runtime supplied by the Factory
base. Platform and VDP share a component icon; the hardware icon denotes only
the controller. Authoring selection is separate from installed software.
See the [accepted change and qualification packet](../../docs/planning/active/presenter-layered-streamlining.md).

This package implements the SDV Lab operator interface. For installation and
use, start with the [Setup guide](../../docs/getting-started/installed-preview-cloud-first-use.md)
and [operator workflow](../../docs/operations/current-demo-workflow.md).
The sections below describe the component for contributors.

The accepted interaction reference is the current [UI-STUDIO-026 amendment](../../docs/demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
The maintained visual implementation and its regression tests are in this
package. Earlier simulated HTML prototypes are Git history, not parallel
implementations. Live state comes from existing Demo Control operations.

The physical workspace remains CARLA upper-left, the combined native Driving
Control/telemetry below, and Studio on the right. CARLA is neither embedded nor
restyled. The shared header contains brand, accepted vehicle assignment and
no session/configuration controls; team navigation and the single Demo controls
entry belong to the right panel, including the native browser window.

### Operator flow and component transitions

The [operator workflow](../../docs/operations/current-demo-workflow.md) owns the
ordinary action sequence and Stop/Start/Delete semantics. This component keeps
presentation and handler mechanics distinct from that user guide:

- Create prepares only the Test and its backends; provisioning remains separate.
  Simulator connection requires the provisioned/Online Test and starts stationary
  in Manual. Platform publication before Provision supports the warehouse story.
- Demo Control allocates releases. The first READY service release exposes Assign
  to Test: it calls `service runtime-prepare test`, then the OEM binds the retained
  Group Subject and exact service identity without replacing its peer. Preparation
  failure blocks assignment; unchanged inputs reuse preparation without SM restart.
  Later higher releases use Publish only. QM SOTA does not require Safe Stop;
  platform FOTA does.
- Backend cards open real product results; Aos Cloud opens authoritative Software
  and Resources. Installed details and release management are separate actions.
  Preparation, publication, assignment and Running remain different observations.

Quick preparation is a pre-Create alternative under Advanced preparation,
composing the existing Test-only sequence. Its recorded recipe survives reload
and cannot be changed during a run. Opening a page never starts it. The contextual guide derives the next
action from observations; it cannot manufacture missed intermediate states.
Studio simulation Start/Stop always pass `--target test`; the unscoped CLI
simulation path is not used by Presenter actions.

### Evidence and safety boundaries

- Right-side inventory/runtime/resources are Aos Cloud only. No guest read is
  introduced by tab entry, Refresh, details or monitoring. Resources preserve
  node/service/Subject/instance/partition identity. CPU is DMIPS; memory/disk and traffic accounting are bytes, formatted
  without inventing a rate. Missing units/values are not guessed. Missing/stale is not zero, absent, Offline or success.
- Team backends use the existing same-origin Demo Control backend read.
  Products are current-Test scoped and versioned; fixture data is never
  substituted for a live result.
- Native telemetry observes vehicle data only. It reads the existing advisory
  contract, rejects unknown values, and does not consume synthetic backend data.
- Routine local actions require one deliberate click. Publication, assignment,
  provisioning, Cloud changes, quick preparation, stop and deletion retain an
  effect-specific confirmation; technical actor/target checks are expandable.
  Cancel emits no mutation. VM credentials use the existing macOS Use once / Save in Keychain
  dialog; no password, native capability, caller-selected shell/path/endpoint
  enters the browser.
- One writer/job, no queue and no automatic mutation retry. Reload does not
  cancel work. Lost responses reconcile the original request ID. Unknown native
  outcomes refuse new mutations; terminal recovery remains an engineering
  intervention, not an invented Cancel/rollback operation.
- Configure the complete OEM/SP pair in Setup. Presenter offers exceptional
  OEM-only selection and Cloud checks under Advanced settings. Local certificate
  presence is separate from authenticated access. Activity exposes scoped
  operation receipts. Synthetic history is under Engineering history, not
  an ordinary result mode; it retains its explicit mock labels.

### Observation and native refresh

The workspace keeps navigation, Next Step, a bounded status dock and the footer
stable during observation and operation changes. Activity holds full operation
receipts; Window layout opens independent placement details without inspecting
Cloud credentials. Overview cards summarize software/input/results, with resource
charts in Cloud monitoring. Reset remains a secondary action with an accessible
prerequisite and independently correlated CLEAR requirement.

Unit connection and report freshness are separate. Retained connection evidence
is labelled last confirmed, never a current Online claim. Inventory loading is
not missing provisioning. Candidate publication, assignment and Cloud installation
are separate observations; a completed local/API step cannot freshen a Cloud
report. Capability V1/V2/V3 is distinct from the Cloud release number. Team
navigation preserves the chosen profile; suggested next profiles require an
explicit action.

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
npm run build
```

Run browser fixtures on the dedicated M1 through the
[qualification entry](../../scripts/qualification/README.md#presenter-browser-fixtures).
Do not run browser or live checks on the development Mac. Fixture screenshots
are not installed-package API/UI acceptance.

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

Use the [current baseline](../../docs/qualification/current-baseline.md) for
release-specific test results and the
[release campaign](../../docs/development/release-campaign.md) for publication.
Neither belongs to the operator's installation checklist.

## Visual assets

Presenter owns its icons and [selected artwork](src/assets/studio/automotive-b2.png).
Only original, license-cleared assets belong in public source. Keep editable
sources with exports when applicable; preserve exact checks in the
[public visual inventory](../../workspace/public-visual-assets.json).
Do not commit private correspondence, partner screenshots, credentials,
proprietary references or local human-input files. Superseded concept boards
and generation records remain in Git, not another active assets directory.
