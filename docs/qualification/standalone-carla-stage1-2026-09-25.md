<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Standalone CARLA — Stage 1 proof

- Prepared: 2026-09-25
- Status: COMPLETE — scoped Stage 1 simulator feasibility proof; not installer acceptance
- Owner: Vehicle Simulation / release integration
- Plan: [Installable distribution Stage 1](../planning/active/installable-distribution-and-reproducibility.md)
- Inputs: [Stage 0 inventory](../research/distribution-stage0-inventory-2026-09-25.md)

Retention update: the [authorized 26 September cleanup](../research/distribution-stage1-retention-audit-2026-09-26.md#authorized-cleanup)
retired three superseded relocated apps, preserving the qualified
`content-profile.a38_dfdp/CarlaUnreal.app`, matching wheel, sources, warm inputs
and all comparison evidence. Earlier statements below about retaining old
comparison apps describe their state at the time of the recorded experiment.

## Current verdict

Stage 1 is complete for the declared Town10HD_Opt / Lincoln MKZ profile on the
tested M5 Pro, macOS 26.6.2 host. The relocated Game runs without Unreal Editor
or readable CARLA/Unreal source content, subject to the explicitly documented
system-executable symlink exceptions below. The matching API also imports from
a separate directory outside the development tree with Python isolated mode
and site packages disabled. This establishes simulator feasibility, not a
clean-Mac installation or portability of all host helpers.

| Required Stage 1 check | Result and evidence |
| --- | --- |
| Matching Game / Python API | PASS; pinned source and retained corrections, arm64 wheel; final isolated import outside the development tree |
| Gateway / Driving Control connection | PASS; real native runtime and authenticated control/VISS paths on isolated ports, no VM/Cloud assignment |
| Manual / Autopilot | PASS; real acceleration, steering and braking through the unchanged Manual bridge; native UI mode selection and physical Autopilot |
| Brake / Tire / Return to road | PASS; unchanged maneuvers on the geometrically matched spawn, stationary Return-to-road completion |
| Actual vehicle signals | PASS; finite wheel/RPM/steering data, consistent front-wheel signs and advancing frames; 1,284.35 m at 20 Hz in the five-minute steady observation |
| First-profile / warm start | PASS in declared cache scope: 8.924 / 7.718 s to RPC; OS/Metal caches retained, not clean-host graphics qualification |
| Stability / resource guard | PASS; 863.12-second native session, clean component/Game exits; owned peak 13.80 GiB, minimum free 97.01 GiB |
| Runtime closure / size | Game package 19.21 GiB logical; no Editor executable or blocking non-system load path; effective source-read checks and loaded-file observations retained |
| Requested native-window handoff | PASS; exact five-surface geometry, idempotent placement and three window-server order observations; final post-resize drive/stop/clean exit |

No Stage 1 blocker remains. Stage 2 must still package the interpreter and
native helpers and integrate the standalone launch identity with ordinary Demo
Control ownership. Stage 5 carries full operator-input/focus-loss/UI-recovery
coverage; Stage 6 carries clean-OS/graphics-cache and full-demo acceptance.
This proof does not claim held-arrow-key UI qualification, all CARLA assets,
every Apple Silicon model, signing/notarization or a restored Cloud connection
for the preserved Test. Existing DNS/Cloud-offline diagnosis remains a separate
live-demo item. Stage 2 has not started.

The remainder preserves the investigation chronologically. Earlier failures,
open gates and intermediate candidates are historical, not competing current
verdicts. No commit/push or immutable release-tag update is claimed here.

## Authorized boundary

Build and verify one standalone Apple Silicon CARLA candidate without an
Editor runtime dependency. Initially preserve the current live Editor, selected Test,
Production, Factory .39/.31, credentials, backends and warm caches. No Cloud
mutation, VM build or video editing. This proof is not installer acceptance.
After the repeated memory-limit finding, the operator explicitly authorized
closing the old live Editor to free resources for this proof. Only that
simulator scene is retired; the other preserved boundaries remain unchanged.

CARLA snapshot `ac7d882cac496ccbf8b40aa543d6b38513e1173c`, Unreal
`9b705d6d2db5b769ab34edb04f3ca2bb8b960014`, content
`639d6eff5aae672da4219e9ace4a2ee891367548`. Required map: Town10HD_Opt;
ego: Lincoln MKZ; retain maneuver actors, sensors and referenced content.

## Isolation and resource guard

Ignored CARLA workspace: `Build-distribution-stage1-20260925/`. A Git-exported
source snapshot has its own project/generated definitions; large content is a
shared build input, not a portable runtime dependency. Existing native client
dependency sources are reused with FetchContent disconnected and build network
access denied. Candidate game outputs must not replace running Editor modules.

Initial free space: approximately 190 GiB. Preserve at least 90 GiB during
build, including the baseline 60-GiB reserve and 30-GiB packaging contingency.
Initial compiler concurrency: four. Proposed isolated RPC/streaming ports:
2100/2101/2102; Traffic Manager: 19000. Recheck immediately before launch;
never connect the candidate to the existing Test or compete for its clock.

## Preparation findings

- The existing standalone Game binary is from August, not a qualified copy of
  the September steering correction. It cannot be used as the acceptance result.
- Existing Editor plugin definition links point to files no longer present
  in the client-only build tree. Recreate definitions only in the isolated
  candidate using the exact source configuration, not in the running project.
- CARLA's `carla_string_option` replaces the command-line CMake engine-path
  value with its environment default. The first configure failed before build;
  the next bounded attempt supplies the documented environment variable.
- Inspect the Game action graph before compiling; no unrelated full Editor
  rebuild is authorized by this proof.

## Build evidence

Native dependencies completed offline: 390 Ninja actions, exit 0, bounded
runner elapsed 150 seconds. Includes server/client LibCarla, the required
static dependencies, RecastBuilder, Boost.Python 3.9 and isolated plugin
definition links. These do not replace any active native runtime.

The Python wheel completed offline in the existing build environment with
`--no-isolation`, without downloading tools or installing into the live venv:

- `carla-0.10.0-cp39-cp39-macosx_26_0_arm64.whl`, 2,255,110 bytes;
- SHA-256 `9c9a7a802a78b96eb2737293a419554ae3ff3058a32e780bdd9864021d3fa594`;
- installed into an isolated test directory; import, client version `0.10.0`
  and wheel-angle method availability PASS;
- Mach-O arm64 extension links only OS libc++ and libSystem. The interpreter
  remains the current CPython 3.9 build/test dependency; a private portable
  interpreter and helper-package closure have not yet been qualified.

CARLA and Boost initially selected different Python versions. Supplying both
`Python3_EXECUTABLE` and `Python_EXECUTABLE` selects 3.9 consistently.

The first Game action preflight ran before the native definition-generation
target completed and failed on its absent file. After that prerequisite
finished, the exported graph completed: 777 actions, 765 clang invocations,
no produced `UnrealEditor` file or Engine/Binaries replacement. Target:
`CarlaUnreal Mac Development arm64`. This is the debuggable standalone proof,
not a Shipping release claim. All 777 actions completed; UBT reports success
and 1,723.45 seconds total. The generated ChaosVehiclesCore unity unit includes
the corrected SteeringSystem source; actual runtime regression remains pending.

After the reported host/session interruption, the original runner completion
JSON was absent but the successful build log and Game receipt survived. The
477,718,240-byte executable is arm64; app signature verification passes with
an ad-hoc local signature, not a distribution signing identity. An incremental
reconciliation completed with exit 0 in 16.57 seconds: only the app finalization
and metadata actions ran, with no C++ recompilation. This supplies a newly
observed completion result without repeating the 777-action build.

The native libraries/Python wheel target macOS 26.0 while Unreal's link target
still declares 13.0, producing deployment-target warnings. This candidate is
for the observed macOS 26.6.2 host only; it is not evidence of compatibility
with macOS 13 or other older systems. Align the release deployment metadata
with the chosen support envelope before distribution qualification.

Existing editor-side project/plugin modules were copied into the isolated
project solely to support the cook tool. They must not appear as dependencies
of the final runnable package. Original modules and the live process were
not changed.

### Cook-tool isolation findings

The first cook failed before processing assets: the copied editor-side Carla
module retained relative LC_RPATH entries based on its original location.
A bounded `-dllerrors` commandlet proved that dyld could not resolve
`UnrealEditor-ChaosVehicles.dylib`. The dependency exists in the original
Engine plugin directory; this was not a Game compile or physics failure.
The cook process receives explicit build-only library search directories;
the runnable package must not inherit this environment.

The next attempt loaded the module but failed initializing the shared Zen
cache inside the network sandbox. Its auto-launch path could not identify the
already-running server and attempted lifecycle management, which did not
succeed. The active server and demo processes remained present. The next
bounded attempt explicitly uses `-NoZenAutoLaunch=127.0.0.1:8558`; the log
confirms an OK connection to the existing cache without auto-launch. Only
that loopback cache port is allowed; external networking remains denied.
Cook outputs use a dedicated candidate directory. The first successful cook
has not yet been established.

### Interrupted cook and bounded resumption

At 14:18 local time the orphaned cook was still waiting in `WaitForAsync`;
both ShaderCompileWorker children were zombies and its log had not advanced
since 14:08. A one-second stack sample measured 21.9 GB physical footprint
(22.2 GB peak), despite a small paged-out RSS. Graceful termination did not
close the cook, so only that verified candidate process was force-terminated.
The source Editor, cache server and Test VM were not stopped. Cache readiness
remained OK. The observed OS uptime was about ten days; a full OS reboot or
the cause of the user's interruption is not established by this evidence.

Resumption reuses the source, binary, content and cache. The build-only guard
now samples the owned process group's Darwin physical footprint every two
seconds, with a 14-GiB ceiling, critical-pressure stop and the existing 90-GiB
disk reserve. Guard success and memory-limit termination were tested on
harmless owned processes. A start record is persisted before lengthy work.

Source inspection found the default cook shader queue permits 8,192 jobs.
The resumed cook bounds it to 64, with two shader workers and a precache limit
of two. It also removes the free-memory prerequisite from the 6-GiB Unreal GC
trigger: Unreal combines minimum-free and maximum-used conditions with AND,
so the earlier 6-GiB setting was not itself a cap. These are transient build
settings, not simulation/runtime behavior changes.

The first bounded resumption still accumulated memory between Unreal's
60-second pressure-GC intervals. Its guard cleanup encountered a process-exit
race; the owned process group was subsequently confirmed absent, but that
attempt did not retain a completion JSON and is not counted as a successful
cook. The guard was corrected and its low-memory termination/finalization test
passed. The next attempt additionally uses `PackagesPerGC=100`, preserving
existing output and cache. This periodic package-count trigger is separate
from the pressure-GC cooldown. After approximately nine minutes its main
process group remained around 12–13 GiB and both shader workers were active.
Shader workers create separate process groups; the main-group guard samples
do not include them. A separate observation measured approximately 0.4 GiB
combined for those two workers. Do not present main-group memory as total
system or total process-tree memory.

The 14-GiB guard then stopped that attempt at 621.29 seconds: peak main-group
footprint 15,300,409,912 bytes; `stopReason=owned-process-memory-budget`,
cleanup error null. This was an observed guard stop, not a compiler failure.
All owned processes were confirmed absent. Whole-tree accounting was added
for children that start independent process groups, with start-identity checks
against PID reuse; an isolated detached-child memory-limit test passed.
The following cook used four shader workers, `PackagesPerGC=10`, and an
18-GiB whole-tree ceiling. Its peak was 17,444,802,288 bytes, below that ceiling.

### Build-tool HTTP cache failure and file-cache path

At 14:43:06 the latter attempt failed inside
`DerivedDataCache/Private/Http/CurlHttpClient.cpp:572` with
`Error in curl_multi operation: Unrecoverable error in select/poll`.
UAT returned 25 after 184.69 seconds; the resource guard did not stop it.
The existing Zen server remained healthy. No Game/runtime crash occurred.

A minimal offline C probe linked the exact Unreal Mac arm64 curl 8.4.0
archive. The low-descriptor socket succeeded; descriptor 1050 failed in
`Curl_poll` with errno 22 while native macOS `poll` succeeded on the same
socket. The archive imports `select`, not `poll`, and its bundled source
rejects descriptors beyond `FD_SETSIZE` in that build configuration. This
reproduces a relevant library limitation; the failed cook's precise descriptor
value was not captured. An upstream
[CARLA issue reports the same assertion](https://github.com/carla-simulator/carla/issues/8364).
That report alone is not proof of this run's cause or of an available fix.

For the isolated build only, use Unreal's existing `NoZenLocalFallback` DDC
graph with `-LocalDataCachePath` pointing to `filesystem-ddc` in the candidate
workspace. This avoids the failing HTTP client without patching the engine or
the live Editor, and preserves the existing Zen cache. The new file cache is
initially cold, so this step repeats derived-resource processing, not C++
compilation. External network access is fully denied for this path.

An initial attempt incorrectly supplied composite INI values on the command
line and failed during cache initialization before cooking. It is retained as
a harness configuration failure, not an asset/build verdict. The corrected
attempt uses the graph's supported separate path override; its startup log
confirms the candidate filesystem cache and four local shader workers, with
no Zen initialization. Completion remains pending.

On the corrected file-cache path the first 6,558 global-shader tasks completed
successfully, followed by map/resource preparation. The file cache and the
existing Zen cache remain distinct and retained. The stock local-control
protocol/orchestration suite passed all 50 tests. Its first invocation had
five Unix-socket bind errors under the tool sandbox; the same suite passed
with temporary local sockets permitted, without changing product code or
authentication. Six tests of the candidate's resource-accounting/static-package
inspection helpers also passed. These checks are not live simulator acceptance.

The newly built Python extension additionally passed 30 source unit tests
(`test_transform` and `test_vehicle.TestVehicleControl`) from the exported
candidate, using only its isolated wheel on `PYTHONPATH`. This checks value
types, transforms, geographic conversions and control bindings; it does not
assert a server connection or physical-vehicle result.

That first file-cache cook subsequently reached 2,820 packages before the
whole-tree 18-GiB guard stopped it at 805.69 seconds (sampled peak
20,654,463,512 bytes; cleanup error null). The preceding log contains concurrent
static-mesh builds, including estimates of 1,350 and 1,476 MB for individual
building meshes. The shader-worker limit does not bound this separate asset
compilation pool. The next bounded attempt therefore retains the same ceiling,
four shader workers and warm file cache, while setting asset/static-mesh/texture
compilation concurrency to one and pending StaticMesh/SkeletalMesh/Texture2D
platform caches to two each. These are supported build-only controls verified
in `AsyncCompilationHelpers.cpp` and `CookOnTheFlyServer.cpp`; no quality,
simulation parameter, asset exclusion or engine source change is involved.

The asset-concurrency-limited attempt was stopped by the same memory guard
after 1,687.47 seconds (28 minutes): 3,418 of 3,875 packages reported cooked,
peak owned-tree footprint 19,617,241,960 bytes (18.27 GiB), exit 143, cleanup
error null. It was not a disk-space stop or a reported compiler crash. The
last samples rise from about 15.5 to 18.27 GiB over approximately 12 seconds.
Only aggregate owned-tree footprint was captured, so attribution of this final
spike to a specific worker/asset is not established. Shader-job cache memory
was only 3.69 MiB at the last statistics record; reducing that cache is not an
evidence-backed remedy. The last log still shows shader/material work and
Unreal's 60-second pressure-GC cooldown. The newly completed file-cache entries
and cooked outputs remain available; no retry has been started.

Post-stop inspection confirms no candidate cook or shader worker remains. The
preserved original Editor is still present with a separately measured 17.54-GiB
Darwin physical footprint (including compressed accounting), while system-wide
swap remains approximately 11.3 GiB. Closing that original Editor would change
the preserved live scene and requires a separately agreed boundary; the current
proof has not done so. Packaging and all live runtime gates remain closed.

### Authorized closure of the old Editor and resource rebudgeting

The operator subsequently authorized closing the original window/process.
The exact original process, PID 25934, was verified against the source project,
Town10 and RPC 2000 arguments and its 24 September start time. A UI selection
unexpectedly opened a separate bare Editor (PID 46769) rather than binding to
that game-mode process. The new process reported a Zen auto-launch error and
exited after its alert was acknowledged; it did not run a build. The original
process did not exit after a TERM request and more than a minute of grace.
A one-second stack sample was preserved, then only that verified original
process was force-terminated under the authorized closure. Neither PID remains.
The ephemeral original simulation scene is lost; no VM, Factory, Cloud object,
credential, backend data or project source was removed.

Observed system-wide swap fell from approximately 11.3 to 2.0 GiB immediately
after closure; free disk rose from approximately 144 to 152–153 GiB. This does
not make all previous swap usage attributable to one process, but it confirms
substantial resource release. System memory-pressure level is normal (1).

One new cook invocation reuses exactly the same source, outputs, file cache
and compilation controls. Its owned-tree ceiling is 24 GiB, below the earlier
combined original-Editor and candidate footprint. The 90-GiB disk reserve and
critical-system-pressure stop remain enforced. Resource samples now include
per-PID footprints so any new peak can be attributed, not guessed. Four
ownership/accounting tests and four static-package tests passed. This run is
`cook-town10-without-live-editor`; it remains a cook-only invocation, with no
C++ recompilation or new full directory copy.

The transient guard also passed an independent normal-parent-exit test: an
owned child in a separate process group was cleaned up after the parent exited
successfully. Its recorded exit is 0 with no cleanup error. A prepared native
session wrapper remains unexecuted and does not assert live acceptance.

The cook without the old live Editor completed successfully: 1,893.26 seconds,
all 3,875 packages, all 10,532 shader jobs, UAT exit 0, no guard stop and no
cleanup error. Peak owned-tree footprint was 18,675,913,608 bytes (17.39 GiB);
minimum free disk was 156,149,854,208 bytes (145.43 GiB). All six recorded
processes were absent after completion. This is the first successful cook,
not yet a packaged-runtime acceptance result. Unreal reports zero errors and
155 warnings, including missing optional startup soft-object paths and the
already recorded tooling reference. Visual/functional inspection remains
required; warnings are not silently treated as qualified content.

The packaging-inspection helper now separately recognizes metadata/artwork
and actual Editor Mach-O files or app bundles. Ten ownership/accounting and
package-inspection tests pass. Offline staging has started using the completed
cook and binary, without requesting another compile or cook.

### Interim disk accounting

At approximately 15:23 CEST the isolated candidate occupies about 48 GiB:
21 GiB of Game compilation intermediates, 16 GiB of cooked resources,
8.6 GiB of filesystem DDC, and roughly 2 GiB of binaries, exported sources
and other inputs. These are rounded allocated sizes, not the eventual
download size. The original large CARLA content tree is a build-input symlink;
the Unreal tree has not been copied. Interrupted cooks reuse the same output
and cache directories rather than creating another complete candidate each time.
The host has about 146 GiB free. System-wide swap usage is approximately
11.4 GiB and must not be attributed entirely to this process. Keep the 90-GiB
reserve through staging; the additional staged runtime size remains unmeasured.
Do not delete useful warm intermediates/cache before the runtime proof passes.

Before staging, source inspection identified a wrapper-layout mismatch:
the single-platform cook writes directly into the explicit output directory,
but UAT staging appends `Mac`. The staging helper uses a build-only `Mac`
directory alias to the completed cook, with checks for the map, registry and
global shader file. This avoids a recook or duplicate large input copy. The
alias is not permitted as a runtime dependency of the relocated package.

### Runtime proof sequence prepared

1. Require successful observed Game reconciliation and map cook before UAT
   staging. Use `-skipcook`, no build request, and an offline guard; do not
   restart compilation just to obtain a package.
2. Inventory staged Mach-O architecture/dependencies, external symlinks,
   Editor executables and size. A staged `.uproject` descriptor is metadata,
   not by itself an Editor runtime dependency.
3. Relocate the package outside the development tree. Start on the reserved
   candidate ports with source/Editor/Homebrew reads denied. Keep VM ownership
   unchanged; the original simulator was separately authorized to close above.
4. Check matching client/server versions, map and empty-world ownership, then
   actual steering (including near-zero signs), wheel telemetry, motion,
   braking, GNSS and Traffic Manager operation. Remove only probe actors.
5. Separately verify real Gateway and native Driving Control integration,
   required maneuvers and Return to road, then cold/warm startup and stability.
   The isolated API probe alone cannot close this integration gate.

### Completed app package and first launch findings

Offline staging/packaging passed in 238.12 seconds (exit 0, no guard stop or
cleanup error). No C++ compile/link action was requested or observed. Modern
Unreal's Xcode packaging copies staged data into both the staged `.app` and
the build-tree `.app`; these temporary duplicates increase the logical build
footprint. Do not equate their summed sizes with independent physical blocks
on APFS. Minimum free disk during packaging was 115,186,094,080 bytes (107.28 GiB).

The runnable app contains 11,556 files / 20,621,982,364 bytes (19.21 GiB), with
18 Mach-O files, no symlinks and no Editor executable/app bundle. Deep strict
signature verification passes; the signature is local ad-hoc, with no Team ID,
not a distribution/notarization result. The app was moved, not copied, to a
private temporary directory outside the development tree; its directory inode
was preserved and a complete per-file digest manifest was recorded once.

Initial static inspection incorrectly treated all absolute LC_RPATH entries
as required libraries. The shipped Apple Metal converter includes historical
Apple build search directories that do not exist on this Mac. Its actual
linked dependencies are packaged or OS libraries. The inspection now records
these search-path warnings separately from blocking dependencies/symlinks;
it does not discard them or claim runtime closure from static inspection.
Eleven helper regression tests pass.

The first explicit read-denial launch trapped in `_libsecinit_appsandbox`
before Unreal initialization. The packaged app already has the stock App
Sandbox entitlement; adding a second inherited `sandbox-exec` profile conflicts
with that initialization. Apple documents this
[sandbox inheritance failure mode](https://developer.apple.com/forums/thread/706390).
The diagnostic crash confirms the loaded third-party libraries came from the
relocated app, but does not qualify runtime behavior. A subsequent bare instance
of this exact test app appeared under Launch Services without the test arguments,
on port 2000; the origin of that relaunch is not fully established. It was stopped
by exact PID after TERM did not complete, and the port was confirmed free. No
automatic test success is inferred from this unintended instance.

A separate functional attempt retains the original signature/App Sandbox and
does not add the conflicting outer profile. The Town10 map rendered visibly
and initialized in 9.01 seconds. An independent read-only matching client
returned server version 0.10.0, world and map in 0.266 seconds. The original
readiness client had been constructed before the listening socket existed;
inspection found its connection CLOSED and no recovery, while the new client
worked. The test harness now waits for the listening socket and constructs a
fresh client for readiness attempts. This is not a Game/physics source change.
Explicit developer-path read exclusion remains unqualified in native App
Sandbox mode. Runtime logs also show missing optional startup soft-object paths;
their visual and functional impact remains open, not silently accepted.

### Real physics proof and unresolved shutdown

The first physics harness applied one command and advanced many simulation
frames while `sticky_control=false`. Canonical Driving Control deliberately
reapplies control every frame. The harness was corrected to do the same;
neither CARLA physics nor product thresholds changed. It also now checks that
steering actually exceeds one degree, rather than accepting finite zero angles,
and advances the actor-removal frame before checking for residual vehicles.

Two subsequent probes on the unchanged relocated binary passed:

- Fresh RPC/world readiness: 10.085 and 9.722 seconds. These are sequential
  host-cache-warm observations, not clean-host cold-start qualification.
- Finite four-wheel telemetry and consistent front steering signs, including
  near-zero steering inputs; physical steering response was present.
- Actual acceleration, engine RPM, wheel rotation and braking to a stop.
- Traffic Manager Autopilot: 15.931 metres travelled in each probe.
- 560 GNSS frames per probe; zero remaining vehicles and no actor-cleanup errors.
- Functional probe durations: 19.667 and 19.418 seconds.

The surrounding restart gate did **not** pass. The first run stopped with exit
0 but the next preflight reported a port still in use. No owner remained at
subsequent inspection; residual TCP state was a hypothesis, not a captured
TIME_WAIT observation. The preflight now rejects a live listener and permits
TIME_WAIT reuse; its occupied/free-port negative checks pass.

On the second run, after `Mac GracefulTerminationHandler`, the app logged
`Secondary server: Operation canceled` followed by an uncaught Boost
`set_option: Bad file descriptor` exception. The bounded owner waited 20 seconds
for TERM and then 5 seconds after KILL; it timed out. The outer guard subsequently
completed with no cleanup error, and process/listener reconciliation found no
remaining Game. This is an unresolved shutdown defect, not a physics failure
and not a successful graceful stop. No live/native integration gate is closed
by these partial results.

Source inspection identified cancellation/re-arm and throwing socket-option
paths in CARLA's multi-GPU listener and streaming sessions. Without a failing
thread stack or a minimal reproducer, the exact throwing call site is **not
proven**. No product-source patch or new build has been started. Next: a bounded
shutdown-specific reproduction/stack capture, then only the affected target if
a source correction is justified; no new full cook from this symptom.

Runtime read isolation remains open. A read-only effective-sandbox query
reported the app sandboxed, but each path query returned EINVAL. Those queries
prove neither developer-path permission nor denial. A corrected foreign-function
prototype has not yet been rerun. No entitlements or security settings changed.

### Disposable staging cleanup

The following generated copies were compared by SHA-256 against the retained
app's existing per-file manifest, with unchanged retained-file size/mtime,
strict deep signature verification and zero open handles:

- `stage/Mac/CarlaUnreal/Content`: 8,665 files, 18,548,592,767 bytes.
- `stage/Mac/Engine/Content`: 2,036 files, 327,739,120 bytes.

Only those two directories were removed. Their approximately 17.58 GiB of
logical content can be regenerated by staging the preserved cooked inputs.
The immutable relocated app, build-tree app, source, compiler intermediates,
cooked inputs, warm caches, staging manifests and compact logs are retained.
Deep signature verification of the retained app still passes after cleanup.
The loose staging tree is now intentionally incomplete and must not be packaged
without re-staging. Free space remained approximately 106 GiB; no equivalent
physical-space recovery is claimed (APFS accounting/sharing was not resolved).

### Shutdown cause, minimal fix and restart proof

The previous unresolved shutdown checkpoint above is superseded by the
following captured evidence. The original relocated app remains preserved.
LLDB attached after normal startup and real physics, with a read-only client
still connected during shutdown, captured `__cxa_throw` in
`carla::multigpu::Primary::Open` -> throwing TCP `set_option` on a closed socket.
A tiny closed-socket reproducer fails on the original code with the same
`Bad file descriptor` exception. This is not inferred from a log message alone.

The transient proof then passed with a minimal CARLA correction, now also in
the canonical source working tree:

- `primary.cpp`: use the error-code overload for TCP no-delay and do not report
  an opened session when the option cannot be set.
- `listener.cpp/.h`: idempotent stop; synchronize acceptor cancel/close versus
  accept initiation; canceled/late callbacks cannot re-arm after stop; retain
  callback lifetime; do not restart the I/O context while its workers run.
- `test_multigpu_shutdown.cpp`: closed socket, 100 late-accept cancellation and
  repeat-stop cycles, and a successful ordinary connection. All three pass.

Only affected targets were rebuilt: four native objects/link in 4.16 seconds;
Game action graph of 12 compile actions, one link, two app finalizations and
one metadata action, completed in 109.26 seconds. No recook, shader compilation
or Unreal Engine rebuild. The candidate app is an APFS clone of the preserved
package with only the rebuilt Game executable replaced and the same ad-hoc
signature/entitlements reapplied. Strict deep signature verification passes.

Fixed app: `/private/tmp/aosedge-stage1-fixed.w9IUrj/CarlaUnreal.app`.
Manifest: `fixed-package-manifest.json`, 11,556 files, 20,621,982,204 bytes.
APFS sharing means this is not another independent 19.21-GiB physical copy.

Two final API/physics/start-stop cycles pass with RPC readiness 9.598/9.999
seconds and Game exit 0 on each owned stop, without forced termination.
An earlier stress harness kept a Python world/client across server restart and
the Python process aborted; that failure remains recorded separately. The
normal harness releases clients before starting the next server. Unexpected
server-crash/client-reconnection resilience is not qualified by orderly restart.

### Native integration and packaged spawn identity

Native Gateway, strict-auth VISS and Driving Control run against the relocated
app on isolated RPC 2100 / VISS 17443. No Test VM/Cloud assignment is made.
`Not linked to Demo Control` and unavailable vehicle-service advisories are
expected for this scope, not a service qualification result.

The first sample-profile run used 30 Hz. Autopilot visibly drove with live
native telemetry. Brake completed (392 frames, 13.067 seconds, maximum
30.867 km/h); Return to road completed in 1.804 seconds, stationary Manual,
without starting Autopilot. Native shutdown removed the actor and sensor,
restored the clock/TM and exited every component and Game with code 0. The
11.8-minute owned run peaked at 14.16 GiB and retained about 106.5 GiB free.

Tire was correctly aborted on collision at the sample's configured spawn 40.
The actual Demo Control override is 20 Hz, not the sample's 30 Hz. A bounded
comparison with 20 Hz and the same spawn also collided, rejecting tick rate
as a sufficient explanation. Neither attempt changed the maneuver or thresholds.

The packaged map enumerates its spawn actors in a different order. Eight
retained demo starts from 21–24 September configured Editor index 40, with
initial GNSS matching packaged index **88** within 2.8–3.1 cm. Packaged index
40 is a different road position near a junction. CARLA currently derives the
list from actor iteration rather than a stable semantic identifier.

On the same candidate with the actual demo cadence and the geometrically
equivalent position, the unchanged control protocol reports:

| Probe | Result |
| --- | --- |
| Tire | COMPLETED; 260 frames / 13.0 s; max 35.110 km/h; Safe Stop/release; 14.694 s end-to-end |
| Brake | COMPLETED; 266 frames / 13.3 s; max 30.534 km/h; Safe Stop/release; 14.951 s end-to-end |
| Return to road | Completed in 1.581 s; stationary Manual; Autopilot remains off |

Evidence: `spawn-parity.json`, `native-{tire,brake,return_to_road}-demo-place.json`.
Only isolated test inputs changed. Do not replace the working Editor config's
index with 88. The package needs its own qualified placement binding and an
identity preflight; a bare numeric index is insufficient across map builds.
The proof helper now rejects changed/missing/ambiguous placement and wrong
heading. Six placement tests pass; 17 total helper regression tests pass.
The new placement guard was also checked read-only against the live map; it
was added after this run started, not falsely reported as its startup gate.

Native Manual selection and authenticated command delivery are observed;
sustained manual motion through held UI keys is not yet qualified. Automated
short key taps did not produce displacement and are not reported as a pass.
API-level real steering, throttle and braking proofs remain separately valid.

The final native demo-placement session completed in 571.455 seconds. Game
readiness was 11.049 seconds; native keyboard readiness followed runner start
by 2.072 seconds. A greater-than-six-minute Autopilot segment retained LIVE
telemetry (20 Hz simulation, approximately 4 display events/s). After Safe Stop
the panel confirmed 0.0 km/h / STOPPED. Controller, Gateway, keyboard and Game
all exited 0 with no forced termination, ownership/command timeouts or rejected
messages. Actor cleanup and isolated-port release were confirmed. Peak owned
footprint was 15.45 GiB; free disk remained about 106.5 GiB. This is bounded
same-host stability evidence, not a long-duration or clean-host acceptance.

### Effective read exclusion and remaining package issues

The sandbox-query prototype was corrected for arm64 variadic calling. A
read-only scan of the running Game's effective `file-read-data` policy found:

- 289,605 CARLA-tree files denied; three allowed paths are symlinks resolving
  to the same Xcode Python executable outside that tree, not CARLA build data.
- 336,972 Unreal-tree files denied, none allowed; no query errors.
- All 18 non-traversed directory symlink targets reported denied at their root.
- Positive control: reading the relocated app executable is allowed.

This is effective-policy evidence for the enumerated snapshot, not a syscall
trace, exhaustive traversal of external symlink targets or clean-host proof.
The helper Python/native tools still use this Mac's developer environment;
their portable dependency closure belongs to Stage 2. No sandbox/entitlement
was weakened. Preserve the inconclusive and detailed scans, not only positives.

Startup still reports missing prop soft-object resources and a handled
CoreRedirects initialization ensure, plus a missing Carla shader-source directory
message despite the cooked shader payload. These need separate package/input
classification; functional vehicle success does not silently clear those errors.
No new full cook has been started to address them.

A read-only catalogue audit identified 82 prop entries: 34 have source and
cooked data, 47 have source but were not cooked, one lacks both. The 48 runtime
missing-package messages match these absent outputs. This distinguishes a
packaging-input gap from a missing-source entry; no entries were silently
removed. Open-file inspection of the running Game showed packaged third-party
libraries and no CARLA/Unreal development-tree, Homebrew or Xcode handles in
the targeted path check. This snapshot complements but does not replace a
file-access trace.

### Presenter and layout observation during isolated testing

The operator reported that Presenter was absent and the two test windows no
longer followed the accepted composition. Read-only observation found no
listener on Presenter port 18080. The retained native window-host process is
still present, but its layout names the original retired simulator/controller
PIDs, not the isolated candidate. Its ordering record reports
`WAITING_FOR_UNLOCK`; that is the host's observation, not proof the operator's
current desktop is actually locked.

A fresh invocation of the existing read-only `Demo Presenter screen` probe
reports `UNLOCKED`, built-in viewport 2056 x 1224 at scale 2, while the retained
host reports `WAITING_FOR_UNLOCK`. Treat this as inconsistent/stale host-session
observation requiring reconciliation, not a request that the operator unlock
an already available desktop. The cause of the absent HTTP server is not yet
established from these checks.

The candidate was deliberately launched outside Demo Control, using explicit
test-window positions; it did not rewrite the working workspace layout. This
is not a qualified Presenter layout test and must not be shown as the final
composition. Add full Presenter availability, correct candidate ownership,
geometry and z-order to the integration handoff. Do not adopt this isolated
simulator into the preserved Test journal or restart the working demo merely
to make the test screen look complete.

### Presenter recovery and package-input proof (continued)

Presenter's existing HTTP service was started after its read-only boot/layout
recovery checks both returned false. The browser loaded the real current read
model, not a fixture. The first UI `Restore window layout` reconciled the old
host; it subsequently disappeared. No crash report or definite exit cause was
found, so do not describe this as a proven host-code defect. A second explicit
UI restore, after confirming the old PID was absent, created a fresh host.

The fresh host reports `VERIFIED` background order, with exact measured bounds:
header `[8,47,2040,76]`, browser `[930,131,1118,1124]`, backdrop
`[0,39,2056,1224]`. The complete composition correctly remains `INCOMPLETE`
because the preserved source's CARLA and Controller processes are stopped.
The bare native host cannot be selected by the current computer-use app
inventory; geometry/order evidence is the existing product observer, while
the real Presenter page was also checked through the browser UI. Do not claim
a visual acceptance of all desktop surfaces. The existing Test VM process,
source run identity, Cloud Unit, service versions and data were not changed.

The minimal-map catalogue mismatch was tested without a cook or engine build.
An APFS clone of the fixed package received a deterministic projection of the
82-entry prop catalogue onto its 34 actually cooked prop meshes. Every one of
the 48 exclusions is recorded; the complete canonical catalogue and previous
app remain unchanged. This is a deliberately limited package profile, not a
claim that missing props were repaired or that the full catalogue is supported.

`content-profile-proof.json` reports zero missing-package errors and zero
handled ensures, down from 48 missing packages and the CoreRedirects ensure.
Steering, motion, RPM/wheel rotation, braking, GNSS, Autopilot and clean stop
pass. RPC readiness was 29.248 seconds for this newly cloned/signed app;
this is not a clean-host timing claim. The 64.48-second guarded operation
peaked at 14.92 GiB and retained at least 106.11 GiB free. Four catalogue helper
regressions were added; all 21 proof-helper tests pass.

The CoreRedirects stack is `AddKnownMissing -> Initialize` on the async-loader
thread after a missing prop load. In the pinned Unreal source, `Initialize`
asserts the game-thread condition **before** checking `bInitialized`. This
does not prove that its first initialization happened on the wrong thread.
The catalogue proof removes this trigger; Unreal source was not modified and
arbitrary missing-package handling remains outside this proof.

The separate shader-directory error comes from CARLA's precheck, whereas
RenderCore's `AddShaderSourceDirectoryMapping` immediately returns for cooked
data or disabled shader compilation. A matching early guard is being tested
in the isolated CARLA source snapshot. The warm action plan contains one
compile, one link and three packaging/metadata actions; build completed in
39.01 seconds without cook, shader compilation or Engine rebuild.

The first attempt to inspect this new app through the desktop app selector
unexpectedly launched a second, argument-free Game process. Global memory
pressure reached critical and the owned-test guard stopped its process tree.
The extra UI-launched instance was closed through its UI. Both were verified
absent, ports free and memory pressure normal before another attempt. Preserve
`content-shader-profile-check.json` as a failed **harness/observation** attempt;
its inner `IN_PROGRESS` report is interrupted, not a successful qualification.
Do not select a directly launched test app by bundle path without proving that
the UI tool will attach to that exact process rather than open another instance.

The same immutable candidate then passed two single-owner starts, physical
API probes and orderly stops with the original App Sandbox. RPC readiness was
7.340 / 7.348 seconds; both Game exits were 0. No missing-prop, CoreRedirects
ensure or shader-source error occurs in those two logs. The guard's total
duration was 59.53 seconds, peak owned footprint 12.99 GiB, minimum free disk
97.13 GiB. The earlier memory-pressure incident increased system-managed swap;
12 GiB allocated / about 11.5 GiB used was observed afterwards. No swap, OS
cache or unrelated application was deleted or stopped to regain disk space.

Qualified transient candidate:
`/private/tmp/aosedge-stage1-fixed.w9IUrj/content-profile.a38_dfdp/CarlaUnreal.app`.
Game executable SHA-256:
`c8fd239c867c7ae6a0cbc1c6b9934d501a2a31df4c2f388d59f77fe5618af076`.
This is still a local engineering candidate, not a distributable release.

After runtime proof, the shader-registration guard was copied to canonical
`Carla.cpp` and verified identical to the compiled source snapshot. Two new
regressions compile the actual early guard for all four cooked/compilation
input combinations and retain the uncooked-directory/duplicate-map guards.
They pass, as do the 21 proof-helper tests and the three canonical shutdown
tests. This does not claim a rebuilt Editor or a complete uncooked cook test.

Two `Actor_29` / `Actor_30` empty instanced-static-mesh errors and material
warnings remain in the map startup log. They also occur in the preceding
native/package runs and are not introduced by the shader guard. They have not
been suppressed or described as resolved. The package-profile projection is
currently a recorded prototype; its production build integration and complete
content/error classification remain open.

## Final-candidate continuation

The same `content-profile.a38_dfdp` package was reused without another cook,
Game link or Engine rebuild. Source fixes and all failed test attempts remain
available; a harness error is not hidden by recreating a candidate.

### First-profile and warm start

`native-app-api-fresh-profile-proof.json` records two successful API/physics
and orderly-stop cycles. The first uses a new Unreal project user directory,
which is verified absent before launch and populated with settings afterwards.
The second uses that same directory. RPC readiness is **8.924 / 7.718 s**;
both Game exit codes are zero. The guard records 63.77 s overall, peak owned
footprint 15.43 GiB and at least 97.09 GiB free.

This is application-profile cold/warm evidence, **not** a cold operating-system
or first-ever Metal-driver measurement. Existing OS/GPU caches were preserved.
Do not delete them to manufacture a cold-machine claim; clean-system graphics
and first-use measurement remains Stage 6. The existence of a generated
CrashReportClient configuration is not, by itself, a crash report.

### Manual control through the production bridge

`manual-bridge-proof-corrected-acceptance.json` exercises the unchanged native
keyboard bridge, authenticated local control protocol, external tick owner,
real vehicle physics and Gateway. An engineering input fixture replaces only
the physical key source for this test. It sends acceleration, right/left
steering and braking, then stops sending commands while bridge heartbeats
continue. Observed results:

- Actual Manual motion above 5 km/h and braking below 0.5 km/h.
- Stale commands select full-brake Safe Stop despite continuing heartbeats.
- Explicit Manual selection re-arms control; final Safe Stop succeeds.
- 61 physical observations; bridge, runtime, controller and Game exit 0.

This is **not** an OS-held-key UI test. The current computer-use interface
exposes short key presses rather than a held-key primitive. Native UI mode
selection is observed separately; the fixture must not be presented as a
human-operated arrow-key acceptance.

The first fixture attempt used a non-UUID observation operation identity and
failed its read-only response check. It was closed cleanly and preserved as
`manual-bridge-qualification`; only the fixture was corrected. A subsequent
native preparation encountered a TIME_WAIT-only port check after the stopped
run. Listener ownership was reconciled, the check corrected to distinguish
TIME_WAIT from a live listener, and a new named attempt used. Neither failure
required rebuilding or changing the product protocol.

### Final native session and sustained observation

The `native-final-proof-qualified` session uses the latest candidate and
checks the exact qualified spawn transform **before** starting consumers.
Canonical local operations again pass:

| Operation | Physical result | End-to-end time |
| --- | --- | --- |
| Tire | 260 frames / 13.0 s; maximum 35.103 km/h; 21 braking frames above 10 km/h | 14.648 s |
| Brake | 266 frames / 13.3 s; maximum 30.515 km/h; 31 braking frames above 10 km/h | 14.933 s |
| Return to road | Stationary Manual, full brake, no automatic Autopilot start | 1.536 s |

Autopilot was then selected through the actual native panel. A 299.409-second
read-only sample interval records **1,284.349 m** of additional travel and
**19.9994 Hz** average simulation cadence. Every observation has an advancing
frame, four finite wheel telemetry values, matching front-wheel steering signs,
Autopilot mode and zero command/ownership timeouts. Waiting for the first
subscription frame is required before enumerating the client's actor cache;
an immediate empty cache is not proof that the vehicle disappeared.

### Dependency and content closure

`final-package-inspection.json` measures **20,621,971,195 bytes (19.21 GiB)**,
no Editor executables and no blocking absolute non-system library dependency
or external/broken package symlink. Apple's converter library retains unused
build-system search paths; those are listed rather than confused with required
loaded libraries. The running Game's open-file snapshot uses its own bundled
third-party libraries and no developer-tree/Homebrew/Xcode files in that check.

The effective sandbox audit of the final Game denies 289,728 CARLA-tree files
and 336,972 Unreal-tree files, with no query errors. The three allowed CARLA
pathnames are the already-recorded symlinks to the external Xcode Python
executable, not files stored in either source tree. Eighteen directory-link
targets are denied. The raw audit intentionally reports `INCOMPLETE_OR_ALLOWED`
because of those symlink exceptions; this classification is not overwritten
with an unqualified all-paths-denied claim. This is effective policy plus
loaded-file evidence, not an exhaustive syscall trace or clean-host test.

The proven catalogue projection is now reproducible from CARLA's
`Util/BuildTools/standalone_content_profile.py`, with a developer README and
three regression tests. It produces a new catalogue and mandatory exclusions
report without editing full source content. Its output matches the tested
34-prop package byte for byte. Three catalogue tests, two shader-guard tests,
21 proof-helper tests and three native shutdown tests pass. The native socket
tests require loopback access; their initial sandbox-denied run did not test
shutdown logic and is not treated as a product failure.

Residual content findings remain visible and bounded:

| Finding | Evidence and affected scope |
| --- | --- |
| Two empty ISM components (`Actor_29/30`) | `GetISMBoundingBox` returns without adding a box when no mesh is assigned. This is static-scene bounding-box metadata; do not claim complete annotation/prop coverage. No broad suppression or Engine change was made. |
| Fuso bus Nanite/translucency warnings | Unsupported material combinations in bundled referenced content; not a Lincoln physics or signal failure. Full vehicle/material-library coverage is not qualified. |
| Lincoln `MaterialNotFound` blueprint message | Also present in earlier preserved package runs; the current car renders, but the message is not claimed repaired. Appearance variants remain outside this limited proof. |
| Optional per-map vehicle metadata and SunPosition icon | Missing optional configuration/UI resource notices remain recorded; required map, Lincoln, sensors and maneuver checks pass. |
| Device-profile console-variable precedence | Log explains that higher-priority settings prevail; not a runtime shader compilation failure. |

### Preserved-demo observations and window handoff

The isolated run is explicitly shown as **Not linked to Demo Control**. It is
not adopted into the real Test journal and cannot be used to claim backend or
Cloud readiness. The retained Test .39 QEMU process is running, SSH works and
CM/IAM/SM report running with zero restarts. External-network policy is ON,
but its DNS path fails: the host-side DNS probe responds without an answer
(rcode 5), and the guest reports temporary DNS resolution errors. Aos Cloud's
authoritative Unit read also reports Offline. Presenter therefore has a real
offline observation, not evidence of a rendering-only synchronization defect.
No DNS/network/service/VM recovery mutation was performed during this proof.

A further read-only comparison at 21:23–21:25 UTC narrows that failure. The
active bridge returns `REFUSED` over both UDP and TCP, with or without EDNS.
macOS currently declares one resolver, `127.0.0.2:53`; direct queries to that
configured resolver succeed. A short-lived diagnostic process using the same
bridge source and Python runtime also returns `NOERROR` and four answers over
both transports, without starting a listener or changing configuration. The
long-lived bridge log last reports failure of `scutil --dns`, retaining six
last-known upstreams, with no subsequent recovery entry. Its source file
predates the process, so this is not evidence of an old source version.

The evidence points to stale resolver state retained after configuration reads
became unavailable in that process. It does not yet prove why that process
cannot read the configuration. No alternate/public DNS, hosts override,
security-filter bypass, bridge restart or VM restart was attempted. A separately
scoped recovery should use the existing owned DNS-recovery operation and verify
guest resolution plus authoritative Cloud Online, not assume success from a
host lookup alone.

Selecting the exact registered `/tmp/` application path attached to the existing
Game; a following process check confirmed a single Game and one native panel.
The earlier `/private/tmp/` lookup incident remains relevant: do not assume
equivalent filesystem spellings are equivalent application identities.
The operator reported wrong test-window placement. At this checkpoint the
geometry/z-order handoff was still open; its subsequent closure is recorded
below. Native windows were never adopted into the retained source run merely
to make its layout/status appear qualified.

### Final owned-session closure

The final native session completed in 863.12 seconds. Runner, runtime,
controller and Game exited with code zero, without a forced-stop timeout.
The surrounding guard recorded 863.59 seconds, a peak owned physical footprint
of 14,817,131,952 bytes (13.80 GiB), and minimum free space of 104,166,850,560
bytes (97.01 GiB). The five-minute Autopilot observation covered 1,284.35 metres
at 20 Hz, with advancing frames, finite wheel signals and zero control timeouts.

The native UI selected Safe Stop, confirmed a stationary vehicle, entered
Manual and closed the panel. The final controller manifest records 630 neutral
Manual commands, zero timeouts/rejections and a released owner. This verifies
UI mode selection, not held-arrow-key or focus-loss behaviour. Physical Manual
acceleration, steering, braking and command-silence fail-safe were independently
verified through the unchanged authenticated production bridge.

The UI observation timed out while its window was closing; authoritative
process and manifest reconciliation confirmed successful completion, so no
blind retry was issued. Owned actor/sensor cleanup and restoration of Traffic
Manager/world settings completed. The controller socket/token were removed.
Test CARLA and Driving Control are stopped; the original Test VM and Presenter
remain running. Short-lived isolated test certificates and compact evidence
remain outside Git for diagnosis; no VM/Cloud mutation or cleanup was performed.

### Native-window closure and final API relocation

The first dedicated layout check reproduced the discrepancy: asking for a
914 × 614 outer CARLA frame produced 898 × 614. The isolated launcher assumed
a 22-point title bar (`ResY=592`), while the standalone AppKit window on the
tested host has a 32-point title bar. Unreal preserves its client aspect ratio
during resizing. The original attempt is retained as `native-layout-closure`;
it shut down cleanly in 106.296 seconds, without a duplicate Game.

Changing only the isolated launch parameter to `ResY=582` resolved the width
discrepancy. No Game rebuild, recook, entitlement or canonical demo journal
change was required. Existing Demo Control window commands were applied only
to the exact test Game/panel PIDs, with explicit primary-window titles. These
selectors also avoid confusing the UI capture indicator with a second primary
application window; process counts remained one Game and one panel.

| Surface | Verified outer rectangle (x, y, width, height), points |
| --- | --- |
| CARLA | 8, 131, 914, 614 |
| Driving Control / Telemetry | 8, 753, 914, 502 |
| Presenter header | 8, 47, 2040, 76 |
| Presenter platform | 930, 131, 1118, 1124 |
| Presenter background | 0, 39, 2056, 1224 |

The repeated placement returned the same exact rectangles. Three read-only
window-server observations confirmed the background below all four working
surfaces, with no surface overlap. Primary CARLA and Control screenshots showed
the rendered car and readable, unclipped controls/telemetry. A later screenshot
selected the transient capture indicator instead of the primary window; that
image is not used as evidence. Safe Stop is verified by authoritative motion
data. This is current geometry/order proof, not an all-focus-transitions or
sleep/wake recovery claim.

After resizing, native-UI Autopilot produced 19.34 km/h and Safe Stop produced
0.0 km/h. The corrected session completed in 282.074 seconds, all component/
Game exits zero, no forced-stop timeout. RPC readiness was 10.044 seconds;
the surrounding guard peaked at 14,305,377,856 bytes (13.32 GiB), with at least
106,302,124,032 bytes (99.00 GiB) free. Relevant evidence:
`window-closure-frame32.json`, `window-frame32-autopilot.json`,
`window-frame32-safe_stop.json`, `native-session-final-frame32.json` and
`native-window-frame32.json`. Both test windows are now deliberately closed;
the original Presenter and Test VM remain running.

The matching wheel was separately extracted outside the development tree,
after verifying its recorded SHA-256, and imported with `-I -S` (plus `-B`).
Value/vehicle-control operations and wheel-angle API availability pass; installed
file bytes are 8,348,424. `python-api-relocation-final.json` retains this proof.
The host CPython 3.9.6 interpreter remains an explicit Stage 2 dependency, not a
claimed portable interpreter. Twenty-three workspace regressions and 21 proof-
helper tests pass. All earlier source/native regression evidence is retained.

## Acceptance evidence

Compile, isolated Python import and one-map cook/package passed. The relocated
native app renders Town10. Native integration, physical Manual bridge control,
UI mode selection, real Brake/Tire/Return-to-road maneuvers, five-minute steady
Autopilot observation and clean repeated shutdown pass on the qualified
geometric placement. Fresh-application-profile/warm RPC readiness is
8.924/7.718 seconds; existing OS/Metal caches were retained. Residual content
findings and source-read exceptions are explicitly bounded above.

Stage 1 is **COMPLETE** for the scoped simulator proof and requested current
window geometry/z-order handoff. Held-arrow-key/focus-loss UI behaviour is not
claimed. Portable helper closure and ordinary standalone-launch ownership
belong to Stage 2; genuinely clean-OS qualification belongs to Stage 6 and is
not replaced by a fresh app profile.
The retained demo's separate DNS/Cloud-offline condition is not a standalone
Game failure and was not repaired by this proof.

Evidence includes `native-app-first-start-control-physics.json`,
`native-app-first-start-restart-physics.json`, both surrounding failed restart
records, `native-app-effective-sandbox.json` (inconclusive),
`staging-duplicate-audit.json` and the retained package digest manifest in the
ignored Stage 1 workspace. No clean-Mac or distributable-installer claim is made.

No model threshold or source-to-Unit authority has changed. The CARLA source
delta contains the proven multi-GPU listener shutdown correction and cooked
shader-source registration guard, with their tests;
the actual demo and its VM/Cloud identities remain preserved.
