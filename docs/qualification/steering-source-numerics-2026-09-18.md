<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 steering-source investigation and numerical regression

Date: 18 September 2026. Status: source corrections, isolated proof, scoped
live activation and bounded moving-source proof completed; full-chain and
all-scenario acceptance remain open.

## Authorized boundary

The operator explicitly approved extending P1 into CARLA/Unreal source
investigation and a targeted correction, retaining strict Gateway rejection.
Simulator rebuilding/replacement must follow a reproducible cause proof.
The retained staging Test, Factory .35, VM overlay, service state and outboxes
are not reset or replaced. Production and Cloud code are untouched.

Gateway base: `10e476d45c28d206d14ab0a3a5a7e1bfab85807f`.
Restricted Unreal dependency base: `2583a3fd4110bc430416d14820c6df2894ccc619`.
Local correction checkpoints: Gateway `d5536e9`, restricted Unreal `9b705d6d2`.
These commits have not been pushed or published as releases by this work.
Engine source remains inside its restricted repository; do not publish it in
the public demo repository.

## Read-only live observations

- A stopped 45-second observation covered 900 frame-coherent samples without
  contradictory wheel signs.
- An Autopilot observation starting 17:52:15 UTC covered 1,800 samples: six
  opposite-sign pairs, all within one observed source frame. One failing
  frame also had a 40-point rather than 41-point Gateway diagnostic event.
  This correlates structural loss but is not a capture naming every missing
  VISS path.
- A subsequent 60-second observation covered 1,200 samples and two opposite
  pairs. Each was read four times while all observed frame boundaries stayed
  identical; each pair remained identical. Both angles were below 0.001
  degrees in magnitude. Signal values were not retained.
- The preserved actor is `vehicle.lincoln.mkz`; its local Blueprint asset
  contains the Ackermann steering selection. CARLA's wheel-angle RPC returns
  the Chaos wheel output, not the normalized command.

These observations supersede the earlier assumption that sequential RPCs
crossing a frame alone explain the failure. A frame-boundary guard would not
remove these reproduced same-frame cases. Independent wheel interpolation is
also present in Unreal's optional asynchronous output path; it has not been
changed or asserted to be the observed cause. Default async-physics ticking is
false, and no configuration override was found in the inspected project and
engine configuration.

## Two distinct numerical defects

### Gateway normalization

The previous tangent-denominator epsilon could discard a valid tiny same-sign
pair; a separate degree epsilon fabricated zero. Multiplying signs could also
underflow. The correction evaluates the same harmonic-mean formula in a
scaled form, tests signs without multiplication, and adds no deadband.
Contradictory nonzero signs, nonfinite angles and angles outside the accepted
range remain unavailable. This correction alone does **not** admit or repair
the observed contradictory CARLA pairs.

Before/after isolated regression: seven failing assertions before, all twelve
passing after. Repository tests cover small positive/negative angles, mixed
signs below ordinary multiplication range, sub-millidegree contradictions,
zero limits and 50 ordinary-formula equivalence cases. All 21 dependency-free
test groups passed. The first sandbox run's three Unix-socket permission
failures were harness restrictions; the unchanged tests passed with socket
access. The Gateway was subsequently rebuilt and activated through the scoped
transition recorded below.

### Chaos Ackermann source

The float linkage calculation and subtraction of two absolute float angles
can reverse a tiny steering delta. An isolated build of the checkout's actual
SteeringSystem/SteeringUtility algorithm, with a small documented adapter for
UE math infrastructure, reproduced this with synthetic inputs:

| Check | Original | Corrected |
| --- | ---: | ---: |
| Small-input wheel pairs | 100,005 | 100,005 |
| Opposite-sign pairs | 24,616 | 0 |
| Wrong-direction pairs | 24,616 | 0 |
| Nonzero inputs collapsed to a zero wheel | 10,224 | 0 |
| Nonfinite outputs | 0 | 0 |
| Left/right mirror violations | 0 | 0 |

The targeted correction retains the configured float linkage geometry,
public types, class layout, steering limits and non-Ackermann modes. It
constructs the arm and subtracts the rest angle in double radians before
narrowing the final delta. It introduces no sign clamp, deadband, remembered
value, interpolation or normalized-command substitution. The existing
no-circle-intersection behavior is retained, not redesigned.

The 10,005 ordinary-input comparison pairs differ by approximately 0.0003
degrees at most in this fixture grid. SingleAngle and AngleRatio checks pass
unchanged. The source correction itself passed the isolated grid; an Unreal
HeadlessChaos regression was added but the full HeadlessChaos suite has not
been executed.

The affected source file also compiled for arm64 using actual generated UBT
definitions and Unreal headers, with warnings as errors. Build setup used
`SkipBuild`; the targeted object was written only to a temporary proof
directory. Running simulator libraries were not overwritten.

A stronger, separate runtime comparison subsequently linked the same test
directly to the installed `UnrealEditor-ChaosVehiclesCore.dylib`, then to the
corrected object and actual Unreal Core libraries. The installed library
produced 25,204 opposite/wrong-direction pairs and 11,542 collapsed-nonzero
cases; the corrected object produced zero of each over 100,005 samples.
Both runs had zero nonfinite outputs and mirror violations. Counts differ
from the infrastructure-adapter fixture above; the installed-library result
is the authoritative binary comparison, not an assertion that the adapter is
bit-identical to the installed build. The ordinary-angle grid comparison
again found approximately 0.0003 degrees maximum difference. No test loaded
code into the running simulator process.

## Separate observations, not hidden fixes

The native controller reported an ownership timeout and rejected an expired
session. One explicit Safe Stop selection reacquired control; Autopilot was
then explicitly selected for the observations above. No scene reset or
simulator restart occurred during those initial observations. The cause of the
missed control heartbeat remains unproved; no timeout was enlarged to conceal it.

An additional VISS diagnostic using the occupied Engineering Dashboard role
was rejected by the existing one-connection-per-role rule. That probe was
removed; the native client was not displaced and authorization was not
weakened. This was a harness identity conflict, not a new VISS outage.

## Scoped live activation

After the production-equivalent proof, the operator explicitly authorized one
CARLA restart and Gateway/Driving Control reconnection. This included scene
and actor recreation, but not VM, Cloud identity, service, model or queue reset.

- Built only the affected complete ChaosVehiclesCore module with generated
  UBT inputs. All 315 exported symbols matched the installed module. The
  complete candidate passed the same 100,005-pair regression with zero
  opposite/wrong-direction or collapsed-nonzero cases; signature verification
  passed. This was not a complete engine or Factory rebuild.
- Completed `simulation stop --target test`, confirmed no running owner of
  the module, retained the original module and Gateway/client binaries in
  `/private/tmp/aos-chaos-steering.ycgRyW/rollback`, then atomically installed
  the verified candidate. Its SHA-256 is
  `f55823c26c0e8b8e1c6c8830ffe1c0f25a209977cde4ad8296aeb5c5d2169db2`;
  the retained original module hash is
  `a74e1977e64814d7f62776cbee57dd583eb5cb52fbc44e13bd609f6cd4779357`.
- Completed `vehicle build-runtime test`, `simulation start --target test`
  and `vehicle select test`. The new source run is
  `09324e5b-5e95-4666-914b-6f5ae9d99a65`. The vehicle remained in Safe Stop.
- The 60-second read-only source observation starting 18:34:44 UTC covered
  1,200 frame-coherent samples with no contradictory pair or probe error.
  This is stationary recovery evidence, not moving-vehicle qualification.
- Read-only service inspection found both native containers running, no
  thread/memory failure counters and zero restarts of the observed SM, KAC,
  KUKSA and time synchronization units. Native telemetry subsequently showed
  Monitoring for both services. This does not establish a new assessment or
  advisory application.

At that stage, the execution safety review rejected automated Autopilot activation despite
operator authorization. The control remained in Safe Stop; no alternate CLI,
keyboard or script path was used to bypass that rejection. Motion-dependent
tests were explicitly unexecuted at that checkpoint. A later fresh screenshot
verification allowed the requested click without changing safeguards. The
[moving follow-up](preserved-test-motion-and-results-2026-09-18.md) subsequently
observed 3,598 coherent Autopilot frames without an invalid pair and traced real
Brake/Tire results and applied advisories. It supersedes the motion blocker,
not the remaining completeness, control-recovery or version-transition gates.
The earlier installed-library comparison predates replacement; its executable
now resolves the current module and must not be mislabeled as the old baseline
if rerun.

## Outstanding gates

1. Moving-source and current-release result/advisory proof passed in the linked
   follow-up; broader duration/scenario qualification remains separate.
2. Correlate named missing-path evidence, VDP invalidation and any remaining
   KUKSA input interruption. Periodic complete-frame counts do not close this.
3. Verify control-session recovery separately. A steering test does not close
   that defect or prove the entire P1–P8 plan.

Temporary structural probes and proof sources are retained locally under
`/private/tmp/aos-chaos-steering.ycgRyW` and
`/private/tmp/aos-p1-normalization.ecuHHh`; these are not release artifacts.
No credentials or raw vehicle telemetry are included in this record.
