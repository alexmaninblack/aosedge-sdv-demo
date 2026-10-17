<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: current orchestration and authority

Demo Control is the shared operation owner behind the CLI, Presenter and
installed Setup. It composes existing host, VM and Cloud primitives; none of
those interfaces creates a second lifecycle or truth store.
The [implemented architecture](current-implementation.md),
[operator workflow](../operations/current-demo-workflow.md) and
[package command reference](../../apps/demo-orchestrator/README.md) describe
the current source. The [baseline](../qualification/current-baseline.md)
binds actual proof to exact candidates.

## Owners and state

Aos Cloud owns reported/desired Unit and software lifecycle facts.
QEMU/guest processes own local runtime facts; team backends own durable product
receipts/history; Gateway owns motion and typed advisory application.
Presenter displays these independent observations rather than manufacturing
readiness from another subsystem's success.

Immutable programs and inputs are separate from private instance data,
certificate references, release continuity and the current run journal.
Opening windows creates no vehicle journal; Create Controller does.
See [installed state](../../contracts/distribution-installation/installed-state.md)
and [run-state operations](../../contracts/demo-run-state/README.md).

## Ordinary lifecycle

1. Setup installs the matching complete media, connects the selected OEM/SP
   pair, then opens Presenter.
2. Create Controller makes the current Test from the clean ARM64 Linux/AosEdge
   Factory image and starts its prepared backends. It does not provision,
   start CARLA or preinstall all releases.
3. Start the detached simulator; publish VDP V1, provision and observe Online;
   attach the same source to the same Unit, stationary in Manual.
4. Apply component updates through Safe Stop and evolve Brake/Tire releases
   serially, checking installation and real function before the next upload.
5. Stop demo and keep data stops owned simulator/VM/backends, not Docker Engine.
   Start controller starts the retained Test/backends without Create,
   reprovisioning, software replay or automatic Autopilot.
6. Delete Test & start over uses confirmed exact-target retirement. It preserves
   unrelated/Production-role resources, immutable bases and release continuity.

Closing the native Presenter window alone keeps the demo running.
Normal operator stop/start, controller ignition recovery and host sleep/wake
are different paths. The last remains an unimplemented planning item.

## Cloud and publication

[Certificate-selected Cloud](certificate-selected-cloud.md) fixes the domain
and authenticated role/association. Production versus Staging is independent
of Test versus Production vehicle role.
[First-use setup](../../contracts/distribution-installation/cloud-first-use.md) prepares only agreed absent
tenant prerequisites; it does not silently adopt/delete conflicts.

Prepared VDP/service content is unsigned. The selected OEM signs component
FOTA; the associated SP signs services. Publication and assignment have exact
owner/recipient/release identities and durable reconciliation.
Cloud upload, installed software, actual function and driver advisory are
different facts. See [artifact publication](../../contracts/artifact-publication-profile/README.md).

## Security and bounded operations

One writer owns a mutation; no uncertain operation is blindly replayed or
queued by an agent. Browser callers cannot choose arbitrary paths, commands,
credentials or endpoints. Read actions do not start a runtime or repair it.
Private keys, passwords, tokens and reusable certificate material never enter
browser payloads, public logs, packages or Git.

[Native service inputs](demo-control-service-inputs.md),
[backend ownership](demo-control-backends.md),
[selected source assignment](../../contracts/exclusive-live-source-assignment/README.md),
[local hosting](../../contracts/local-demo-hosting/README.md) and
[Safe Stop FOTA](../../contracts/platform-fota-safe-stop/README.md)
own the detailed accepted contracts.

## Observation and recovery

Cloud reads are bounded, panel-scoped REST observations; backend SSE is a
different interface. Missing/stale/uncertain data is not zero, absence or
Offline. Exact installed-profile evidence comes from Cloud plus reviewed
artifact binding, not build-number arithmetic or missing telemetry.

Local service analytics continue during externalOFF; durable outboxes deliver
after reconnect. Guarded ignition restores the same Unit/Node/source only
under its accepted conditions, stationary without Autopilot. It does not
provide laptop sleep/wake, cold externalOFF or nonempty-queue power-loss proof.

Each qualification scenario owns its sequence, independent effects, timing,
bounded diagnostics and final verified shutdown. Source checks do not mutate
Cloud or qualify installation. Preserve shared Docker and unrelated processes.
