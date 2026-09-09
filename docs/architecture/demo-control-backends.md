<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: backend foundation increment

Status: source increment, not P1/live qualification. Updated 10 September 2026.
This implements part of the [accepted Studio plan](../planning/active/demo-studio-delivery-plan.md)
and the [D4-020 hosting profile](../../contracts/local-demo-hosting/local-demo-hosting-profile.v1.json).

## Shared operations

```bash
democtl backend build brake
democtl backend build tire
democtl backend start brake
democtl backend start tire
democtl backend status brake
democtl backend status tire
democtl backend stop brake
democtl backend stop tire
```

Build is development preparation only. It requires committed, clean source
in the owning sibling repository and a running Docker engine. A pinned base
image/dependency may be fetched during this explicit build. It records the
local ARM64 image SHA256 ID and source commit under the artifact catalog's
`backends/<team>/<source-commit>/manifest.json`. No binaries enter Git.

Start never builds, pulls, starts Docker Desktop or replaces an image in an
existing run. It requires a current Test-containing run and a locally present
immutable image. Production is optional; no Production VM is created.
CLI and transport-neutral API use the same operation implementation. API
requests accept only the fixed team and start/stop/status, not builds, paths,
image references, shell commands or credentials.

The containers publish ingestion ports only on loopback (Brake 18091, Tire
18092), use independent labelled networks/volumes, non-root image users and
no new privileges. The current context directory is mounted read-only; no
host keys or broad host directory is mounted. Product dashboard UI ports and
Presenter proxy integration remain later work, not phantom listeners.

## Ownership and recovery

The existing journal records the LOCAL_CREATE operation owner, team, immutable
image ID, source revision, exact Compose path and start/stop intent. Conflicting
container, volume or network ownership blocks rather than adopting/deleting
another run. Lost responses retain UNCERTAIN intent. A repeated start first
observes the exact owned process; it never blindly starts a second container.
Explicit stop is available for an owned partial start and retains storage.

Status reports Docker process health only. A healthy process does not prove
current Unit context, guest connectivity, product ingestion, service execution
or driver advisory. Docker connection errors are unavailable, not absence.

The closed context projection supplies the successfully provisioned current
Test UID and optional successful Production peer. It contains no Cloud state,
keys or telemetry. The same Test may acquire its just-provisioned Production
peer, but an old UID cannot silently be replaced or removed. Cloud deletion
does not erase the retiring UID selector before exact backend cleanup.

## Current boundaries and evidence

Seven isolated lifecycle tests and five context tests pass. Native Brake tests
cover durable SQLite storage, current-Test queries and private exact cleanup.
The independent Tire foundation exposes process/context health and explicitly
returns `501 NOT_IMPLEMENTED` for product routes. Its foundation-only proof is
not a product-record cleanup implementation or an empty product result.

Two explicit `democtl backend build` attempts stopped before compilation:
the Docker engine was unavailable. A subsequent read-only `backend status`
identified `BACKEND_DOCKER_ENGINE_UNAVAILABLE`. No new images, containers,
volumes, guest routes or Cloud resources were created by these attempts.

Remaining P1/P3 gates: real ARM64 container build/start/restart, bounded partial
startup cleanup, composed Create/Park/Resume/Retire, exact backend cleanup
before volume reset, shared native protected-action integration, independent
guest routes and loopback/LAN-negative proof. Do not claim the new complete
preparation command is qualified from these isolated tests.
