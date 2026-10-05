<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable host launch inputs

- Status: Accepted Stage 2 integration slice; not installation qualification.
- Version: 1.0
- Prepared: 2026-09-26
- Owner: Demo Solution Team
- Parent: [distribution plan, Stage 2](../../docs/planning/active/installable-distribution-and-reproducibility.md#stage-2-assemble-portable-demo-runtime-artifacts).

## Boundary

An explicit `host-runtime` directory under the existing artifact catalogue's
`aosedge-sdv-demo` directory selects packaged host inputs. Absence retains the
developer path. Presence with missing, altered or unsafe content blocks; no
Editor, Homebrew, Swift/CMake build or developer-interpreter fallback is allowed.
The independent integration-source lock pins the complete host manifest. Paths
are canonical relative regular files, with no links or group/world writes.
Bounds cover at most 20,000 files and 32 GiB; external redistribution remains
unapproved. Known entry paths are fixed in source, not caller-supplied commands.

The candidate supplies prebuilt Presenter/Driving Control, web assets, existing
Gateway helpers/configuration, matching private Python/CARLA API, Gateway/client
native closure, standalone Game and OpenSSL closure/public configuration.
Validate the consumed dependency group before executing it. Check that its
directory contains no undeclared files or linked subdirectories; extra importable
modules/providers are not trusted. Cache hashes only
in-process against unchanged file identities/size/mtime/ctime; status reads do
not repeatedly scan multi-gigabyte Game data. Manifest trust remains independent
of that cache. A new process or changed identity requires verification again.

Do not package credentials, identities, run state or model data. Gateway server
TLS material remains the existing operator-provided `tls` launcher reference;
only that reference is needed from `workspace/repositories.json` in packaged
mode. First-use credential setup is a later installation contract. Local strict
client admission, certificate validity/identity, assignment, guest enrollment
and all VM/Cloud boundaries stay unchanged. Packaged OpenSSL uses a fixed
public minimal request configuration, never an implicit Homebrew config/provider.

Installed first use now follows the accepted
[per-instance server-trust amendment](../distribution-installation/local-gateway-trust.md).
The developer TLS reference and all client-admission rules above remain unchanged.

## Existing lifecycle and visible behavior

Use existing SourceDriver, WorkspaceService, one-writer journal, exact process
ownership, fixed ports, control sockets, normal native Quit and layout/z-order.
Do not add a second launcher/session manager, new state root or port selection.
The isolated qualification app has empty state; existing Test/Production state
is neither copied nor switched. Package changes cannot replace an active owned
simulator or Presenter process silently; existing reconciliation gates apply.

The qualified single-map Game takes no Editor/project arguments. Preserve the
accepted 20 Hz physics/chase cadence, map, vehicle, maneuvers and stationary start.
Its qualified spawn index 88 represents the original Editor index 40 location.
Its initial client rectangle derives from existing built-in display geometry
with the measured 32-point standalone title bar; existing AX verification and
ordering remain authoritative. Do not alter the layout or model thresholds.

On smaller supported displays, the same upper-left CARLA / lower-left combined
Control / right Presenter composition must budget the native Control window's
900 × 502-point outer minimum before placing adjacent surfaces. AppKit must
not enlarge it into the Presenter or Dock after placement. Retain the exact
2056 × 1224 reference geometry; only the proportional split below those native
minimums changes. Do not shrink fonts, clip telemetry, change macOS display/Dock
settings or relax the three-point verification tolerance to hide overlap.

Use the standard Game setting `bShouldWindowPreserveAspectRatio=False` at
packaged launch: Desktop Restore owns the outer rectangle, so a height change
must not implicitly change width. This changes neither camera/physics cadence
nor the accepted desktop layout. Preserve the three-point geometry tolerance.
For borderless Presenter windows, post Accessibility moved/resized notifications
after applying frames; a window-server resize alone leaves stale System Events
geometry on the qualified host. On Restore, await the exact native generation
acknowledgement within the existing two-second budget before observing those
frames. Missing/stale evidence remains incomplete, never a successful fallback.

Native hosts are selected rather than compiled at operator launch. The existing
web server serves packaged web assets. Protected native callbacks use an exact
private Python/script entry, retaining the same shared application dispatch and
state root. UI stop must recognize that exact owned invocation and retain its
idle/uncertain/recovery guards. It must not terminate a listener by port alone.
Editor-only DDC preparation explicitly blocks in packaged mode; it is not a
claim that native graphics need no first-use preparation.

The native host must also recover if it opens before the local HTTP server.
The existing five-second client/session check reloads only while the server is
idle and both previously committed views have no dialog or pending submission.
A view that never committed a document has no client action to discard. Load
the fixed local entry again rather than reloading a nonexistent document;
navigation failures re-arm this same check, except cancellation of a superseded
navigation. Never replay an operation or relax the loopback navigation policy.
Start HTTP before native windows during an operator handoff; late server startup
must nevertheless recover. Geometry alone is not page-load acceptance.

## Qualification

The current Gateway and VISS client must both implement the accepted Brake/Tire
QM Request, Availability and GatewayStatus paths. Reject pre-advisory native
inputs before copying; path presence is only a negative build gate, never a
substitute for the Gateway protocol/access/dashboard tests and live round trip.
Record the exact warm source tree and input digests. Historical inventory
provenance does not establish that its binary matches the current source.
The no-client-certificate admission probe also uses the selected packaged
VISS client, never a developer build hidden behind an otherwise packaged run.

Require absent/present-invalid selector tests, integrity/path/size checks,
no compiler/developer-path fallback, unchanged legacy tests, exact commands,
callback ownership, initial/repeated start, normal stop, layout and fresh
local telemetry. Use a separate app/catalogue and explicit synthetic TLS fixture
for a no-VM/no-Cloud source proof; never copy operator credentials. Source-denied
helper/native checks and the Game's existing App Sandbox are distinct evidence.
Native graphical acceptance and real Cloud/VM binding are not inferred from
command fixtures. Retain the working demo and 90 GiB disk reserve. Reuse Game,
Factory and precompiled hosts; no rebuild for a selector-only change.

Class B: affected are host selection, operator launch/cache preparation,
orchestration requirements, scenario/flows and tests. Revalidated unchanged:
vehicle architecture, strict VISS trust, lifecycle/safety gates and UI layout.
