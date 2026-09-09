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

Development-only candidate activation is explicit: after stopping one owned
team backend, `democtl backend activate <team>` selects its latest successfully
built immutable image. It removes/recreates no data volume and does not start
a process. The next `backend start <team>` uses that recorded image. A running
container, foreign resource, lost/ambiguous identity or changed candidate during
reconciliation blocks activation. This command is not a browser action and does
not add a step to the operator's demo story. Ordinary Park/Resume preserves the
recorded image even when a newer development candidate exists.

Build is development preparation only. It requires committed, clean source
in the owning sibling repository and a running Docker engine. A pinned base
image/dependency may be fetched during this explicit build. It records the
local ARM64 image SHA256 ID and source commit under the artifact catalog's
`backends/<team>/<source-commit>/manifest.json`. No binaries enter Git.

Start never builds, pulls, starts Docker Desktop or replaces an image in an
existing run. Only explicit stopped development activation changes that binding.
It requires a current Test-containing run and a locally present
immutable image. Production is optional; no Production VM is created.
CLI and transport-neutral API use the same operation implementation. API
requests accept only the fixed team and start/stop/status, not builds, paths,
image references, shell commands or credentials.

The containers publish ingestion ports only on loopback (Brake 18091, Tire
18092), use independent labelled networks/volumes, non-root image users and
no new privileges. The current context directory is mounted read-only; no
host keys or broad host directory is mounted. Product dashboard UI ports and
Presenter proxy integration remain later work, not phantom listeners.

Only the non-secret context export directory is 0755 and its JSON projection
0444, so a different container UID can read the read-only mount. The parent
run directory remains 0700; journal, access keys and Compose files are not
exported. This does not grant the container write access or change guest trust.

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

## Composed Test lifecycle

The following shared commands have source and fixture coverage; the complete
live cycle is not yet qualified. They do not replace the existing engineering
commands for independent Test/Production/all operations.

| Command | Ordered scope | Result boundary |
| --- | --- | --- |
| `demo create --image <catalog-id>` | Create the current Test overlay when absent, boot Test, start both prepared backend images | Controller running; no provisioning, simulator connection or software publication |
| `environment park` | Read current update state; stop/detach the owned simulator, stop Test, stop both backends | Preserve identity, disks, data, selection intent and immutable image bindings |
| `environment resume` | Start retained Test/backends; restore the previously running simulator and Test connection in initial Manual | Local resumption; Cloud Online and product readiness need their own observations |
| `demo retire` | Refuse unresolved updates; stop simulator; establish backend cleanup context; deprovision/delete Test; stop Test; remove exact Test data and local overlay | Preserve Production, published releases and shared dependencies; resume only journaled incomplete steps |

All commands are invoked with the `democtl` prefix. Create accepts the catalog
selector, not a filesystem path. Browser requests remain fixed to Test. Native
VM access uses the same protected-input path as existing preparation.
Park is refused promptly for an unfinished or uncertain update: it does not
queue a shutdown or implicitly cancel an update. Stop preserves backend data;
only scoped Retire may remove it after exact owned-state checks.

For a retained Production peer, backend cleanup deletes only records selected
by the retiring Test UID and preserves storage/nonmatching records. Single-Test
resource deletion additionally requires whole-store emptiness against the
known schema. Tire currently supplies only a foundation-only proof. A retained
demo Subject is not yet integrated: service assignment state blocks retirement
rather than silently leaving or deleting a binding.

## Current boundaries and evidence

Ten isolated lifecycle tests and six context tests pass. The lifecycle suite
also rejects container identity changes, cross-team storage and unrecorded
Compose files. Native Brake tests
cover durable SQLite storage, current-Test queries and private exact cleanup.
The independent Tire foundation exposes process/context health and explicitly
returns `501 NOT_IMPLEMENTED` for product routes. Its foundation-only proof is
not a product-record cleanup implementation or an empty product result.

The initial build attempts stopped while Docker was unavailable. After the
user started Docker, both real ARM64 backend builds and starts succeeded.
Brake also passed explicit stop/activate/start with its existing database
retained. Scoped Test cleanup reached confirmed data proofs and stopped
containers, but local context removal remains blocked by an open file handle.
The exact source/image revisions and current recovery boundary are in the
[implementation checkpoint](../qualification/demo-studio-implementation-progress-2026-09-10.md#resumed-execution).

Remaining P1/P3 live gates include completed scoped retirement, fresh Create,
Park/Resume and full CLI repeat, shared native protected-action integration,
independent guest routes and loopback/LAN-negative proof. Composed source and
fixture coverage are not qualification of the complete preparation command.
