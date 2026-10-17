<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Orchestrator

Demo Control is the shared CLI/application core used by installed Setup and
Presenter. Operators start with the [root launcher](../../README.md#start-here)
and [current workflow](../../docs/operations/current-demo-workflow.md), not
manual commands from an old Factory experiment.

The [current baseline](../../docs/qualification/current-baseline.md) binds the
selected media and exact API/UI/native Setup/public-consumer evidence.
This package README is a developer/diagnostic reference, not proof that every
expanded architecture obligation is implemented.

## Operator entry and lifecycle ownership

Follow the [operator workflow](../../docs/operations/current-demo-workflow.md)
for installation, serial VDP/service delivery and non-destructive Stop/Start.
Setup, Presenter and this CLI share the same core; none creates a second
vehicle lifecycle. Publication, assignment, Running and functional/advisory
results remain independently observed facts. Retirement is separate from Stop.

## Current command discovery

In a development environment where this Python package is installed, inspect
the actual parser before using an engineering operation:

```sh
democtl --help
democtl cloud --help
democtl component --help
democtl service --help
democtl backend --help
democtl demo --help
```

Bounded read-only status examples:

```sh
democtl status test
democtl status test --guest --cloud
democtl --output json status test --guest --cloud
```

Local VM state, guest access, Cloud Online, installed software and products
remain independently observed facts. Missing data is not zero or success.
Reading status never provisions, publishes, starts or repairs a runtime.

Engineering commands for image selection, VM lifecycle, component/service
preparation, signing, publication and retirement require their explicit
configured context and authorization. The browser's Start/Stop controls
compose existing core operations; do not guess equivalent CLI command names.

## Context, security and persistence

- Configure the ordinary OEM/SP pair in Setup. Existing certificates determine
  the Cloud domain; new enrollment selects Production or Staging.
- Production Aos Cloud with a Test vehicle is not a Production-role vehicle.
- Prepared content is unsigned. Selected OEM credentials sign VDP; the
  associated SP signs services for that same environment.
- Release allocation is monotonic and durable. Re-signing does not justify a
  new payload/profile or replay of an uncertain publication.
- One writer owns each mutation. Conflicting or unknown outcomes reconcile
  the original operation; no silent adoption, queue or blind retry.
- The browser receives no private keys, VM password, caller-selected shell,
  credential path or arbitrary endpoint.
- Programs/inputs, private instance, current run and disposable scratch have
  separate ownership. Stop preserves data; retirement deletes exact owned
  run data only. Neither implicitly deletes shared images or changes Docker.

See [Demo Control architecture](../../docs/architecture/demo-control.md),
[backend ownership](../../docs/architecture/demo-control-backends.md),
[native runtime inputs](../../docs/architecture/demo-control-service-inputs.md),
[certificate-selected Cloud](../../docs/architecture/certificate-selected-cloud.md),
[run-state contract](../../contracts/demo-run-state/README.md) and
[Setup contract](../../contracts/distribution-installation/native-setup.md).

## Development and proof

Use [Contributing](../../CONTRIBUTING.md) and the
[development map](../../docs/development/README.md). Component source changes
need their targeted isolated tests; installed/live checks run on the dedicated
M1, not the development Mac. Actual scenarios own preflight, actions, independent
effects, timings, diagnostics and verified final closure.
