<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-3.1 Real Provider Interface Closure

- Status: Complete; accepted by the R6.1-5 offline matrix
- Date: 2026-08-15
- Depends on: completed R6.1-3 atomic lifecycle
- Scope: local source, build, and disposable non-provisioned VM work only

## Why This Gate Is Required

R6.1-3 proves the generic component lifecycle with deterministic synthetic
payloads. Before creating the first real FOTA payload, the development
CARLA-to-KUKSA provider must conform to the fixed bootstrap interface.

The existing provider 0.1.1 archive is a guarded side-load package, not an
input that can be wrapped unchanged as a component. Its installer creates a
virtual environment in `/var`, installs systemd units, writes `/etc`, remounts
the root filesystem, and injects credentials and trust material. Every one of
those lifecycle operations belongs to the old R6 mechanism and is forbidden
inside the new component payload.

The current Python provider also supports only ordinary `--config` execution.
The stable R6.1 launcher additionally requires `--self-test` and
`--mark-unavailable`, and its systemd credential path uses
`aos-vehicle-data-provider.service`, not the legacy
`carla-kuksa-provider.service` name. These are real interface gaps, not FOTA
packaging details.

## Contract to Close

### Execution and dependency model

The preferred R6.1 provider payload uses the CPython 3.12 interpreter already
present in the qualified AosVM bootstrap. The exact ARM64 wheel inputs remain
hash locked, but their normalized runtime contents are assembled into the
component at build time. The payload must not run `pip`, create a virtual
environment, download dependencies, or contain interpreter symlinks during
installation.

The final layout must remain compatible with the R6.1-3 validator:

```text
component.json
bin/vehicle-data-provider          # the only executable payload file
config/provider.json               # immutable non-secret defaults/schema
python/carla_viss_kuksa_provider/
python/site-packages/              # normalized locked ARM64 dependencies
licenses/
sbom/
```

The executable must derive its immutable slot root safely, isolate module
resolution from user-site packages, and invoke the pinned bootstrap Python
ABI. All other payload files are regular, non-executable, root-owned content.

R6.1-3.1 must verify CPython and shared-library compatibility in the exact
ARM64 bootstrap image, not merely on the macOS host or builder.

### Provider command interface

The real provider must implement exactly the launcher operations:

| Invocation | Required behavior |
| --- | --- |
| `--config FILE` | Start the provider, authenticate to local KUKSA, mark all owned paths unavailable before waiting for source data, then maintain the VISS bridge. |
| `--self-test --config FILE` | Offline import, payload, schema, and ABI validation with no CARLA, Internet, network namespace, KUKSA credential, or persistent-state dependency. |
| `--mark-unavailable --config FILE` | Authenticate only to local KUKSA, atomically mark all seven owned paths unavailable, close the connection, and exit successfully. |

All modes require bounded execution, deterministic exit codes, English-only
logs, and secret-free errors. Unknown arguments fail closed.

### Configuration, trust, and credentials

The final interface must distinguish three owners:

- component payload: immutable schema, safe defaults, timing limits, and
  contract identifiers;
- vehicle/platform integration: endpoint selection and environment-specific
  public trust anchors in a fixed bootstrap-owned persistent path;
- systemd credentials: the path-scoped KUKSA token materialized only for the
  active provider process.

The current development configuration's legacy `/var/lib` paths and old
systemd credential directory must not enter the 0.2.0 component. R6.1-3.1 must
choose and document the fixed external-configuration and public-trust paths,
their ownership and modes, merge precedence, missing-config behavior, and
their provisioning or integration owner.

No private key, JWT, certificate identity, Unit identity, user-specific path,
or Cloud token may appear in source, component payloads, build logs, SBOMs, or
provenance. Public trust anchors must still be classified explicitly as either
component-owned or environment-owned; they may not be copied implicitly from
the R6 side-load.

### Bootstrap compatibility

If closing the real-provider interface requires changing the stable launcher,
systemd unit, tmpfiles layout, health adapter, SELinux policy, or runtime
configuration, those changes are a bootstrap delta and must be completed
before R6.1-4. The project image and unsigned full-rootfs FOTA output must then
be rebuilt incrementally and rerun the accepted R6.1-2 and R6.1-3 gates.

The runtime interface remains version 1 only if the completed provider can use
it without an undocumented side channel. Otherwise the interface version must
advance deliberately and both bootstrap and payload compatibility metadata
must change together.

## Work Plan

1. Record the exact launcher/provider argument, environment, filesystem,
   Python ABI, configuration, trust, and credential contracts.
2. Replace the side-load assumptions in the provider CLI with normal,
   `--self-test`, and `--mark-unavailable` modes.
3. Build a normalized ARM64 runtime tree from the exact hash-locked wheels;
   do not create the final FOTA envelope yet.
4. Add unit tests for argument rejection, offline self-test, configuration
   merge and bounds, credential-path selection, fail-safe unavailability, and
   secret-free errors.
5. Exercise the assembled provider tree under the fixed launcher and both
   sandboxed systemd units in a disposable ARM64 VM.
6. If a bootstrap delta was required, rebuild it and rerun image, SELinux,
   empty-store, lifecycle, and unsigned rootfs FOTA regressions.
7. Pin the accepted platform and integration revisions before authorizing
   R6.1-4.

## Exit Criteria

R6.1-3.1 is complete only when the actual CARLA-to-KUKSA provider, not a
synthetic shell payload:

- runs under the fixed launcher and DynamicUser sandbox;
- passes offline self-test without source, network, or credentials;
- marks all seven KUKSA paths unavailable through the fixed reload path;
- uses only declared external configuration, trust, and systemd credential
  interfaces;
- imports every locked ARM64 dependency with the bootstrap CPython ABI;
- contains no installer, virtual-environment creation, rootfs remount, `/etc`
  mutation, credential injection, or second systemd unit;
- leaves all R6.1-2 and R6.1-3 regressions green.

All exit criteria passed on the exact ARM64 bootstrap and are recorded in the
[offline qualification](r6-1-offline-provider-qualification.md). Completion
authorized and completed the unsigned R6.1-4 artifact. It does not authorize
OEM signing, Cloud publication, assignment, provisioning, or any change to the
active demonstration Unit.
