<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP VDP update: specification-to-implementation record

- Recorded: 2026-09-04
- Historical engineering vehicle: `.26`
- Qualified Factory image: `.27`
- Qualified update pair: VDP `1.0.15` and version-only successor `1.0.16`

## Historical `.26` engineering state

The `.26` experiment reached a real active VDP component rather than only a
Cloud-installed record. AosCore reported the component active in slot `a`, the
systemd service was `active/running`, and VDP reported `READY`, source `LIVE`
and reason `NONE`. CARLA, controller, Gateway and VM were simultaneously live.

This is engineering evidence, not a release artifact. The running `aos-sm` was
temporarily replaced through `/run`; its source fixes were split between a
local commit and uncommitted files. VDP `1.0.13` was produced by mutating
metadata around an older source candidate and therefore lacks exact release
provenance. DNS was repaired in the disposable overlay after boot.

## Proven implementation differences

| Area | Accepted design | `.26` as built | `.27` disposition |
| --- | --- | --- | --- |
| VISS trust | purpose-bound per-Unit mTLS | Test-only server authentication | retain only as explicit Test-only exception |
| Component runtime | Factory-installed | transient `/run` executable | integrate corrected source into Factory |
| Safe Stop identity | binding documentation said Cloud Node UUID | AosCore supplies 32-hex node/system UID | correct the binding contract |
| Snapshot | ten frame-coherent paths | one multi-path GET required | retain and test |
| Timing | accepted period 50 ms | live controller changed to 50 ms | add dedicated Test-only configuration |
| Component blob | provider archive | Cloud delivers full-gzip component layer | inflate, then validate provider archive |
| Missing stop | idempotent lifecycle | missing component previously failed | retain idempotent `StopInstance` |
| Unit Model | current descriptive schema | stale example added format/vendor fields and blocked delivery | omit those fields and test the payload |
| DNS | functional at first boot | overlay correction required | make Factory/launcher configuration native |
| Publication | signed deployment bundle | evidence accumulated through several upload paths | document one direct deployment-bundle flow |
| Provenance | exact source-to-artifact binding | `1.0.13` metadata does not identify a release source | produced clean `1.0.15`/`1.0.16` |

## Root causes closed by the experiment

1. The runtime originally interpreted the Cloud-delivered full-gzip component
   blob as the embedded provider tar archive.
2. `StopInstance` treated an already absent component as a hard failure during
   normal Service Manager reconciliation.
3. Sequential VISS reads mixed timestamps and frames; the Safe Stop evaluator
   requires one coherent snapshot.
4. The Safe Stop binding required canonical UUID syntax even though AosCore
   supplied its 32-hex node/system UID.
5. Waiting for a peer WebSocket close response could block an otherwise valid
   current snapshot.
6. A 33.3-ms simulation setting could not maintain sufficiently fresh
   wall-clock samples in the demonstrated stack; the accepted contract already
   specifies 50 ms.
7. Run-scoped systemd credentials disappeared after reboot and had to be
   recreated before consumers started.

## Qualified `.27` result

The two clean cycles used the same immutable image bytes:

- image: `$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/factory-images/6.1.1-maninblack.27/main-qemuarm64.img`;
- version: `6.1.1-maninblack.27`;
- byte length: `6997147648`;
- SHA-256: `dbc018cf31dc83accbca82cf26df0b3ca69c66d1135100db8d05552fd2744c56`.

`$DEMO_ARTIFACT_ROOT` is the host-local immutable artifact root outside every
repository and worktree. Git retains only manifests, sizes and digests; it does
not retain VM images, signed deployment bundles or runtime evidence archives.

Cycle A installed and activated VDP `1.0.15`, then the Unit was deprovisioned
and deleted and its disposable overlay, access material and runtime binding
state were removed without backup. Cycle B started from a new overlay whose
backing image had the same SHA-256. Its new Unit
`70e48e60-de2b-444b-a961-258683f324c4` joined only the intended persistent
validation set `Test Vehicles`; the Cloud-created Campaign memberships were
observed but not mutated.

VDP `1.0.16` was uploaded as Deployment Bundle
`a26d87f8-4f23-4e5c-90cb-54cb0729b222`. OEM validation batch
`af02fc92-3c64-41cb-b4d6-3999c4997197` was approved for `arm64` through the
direct Cloud API. The Unit first exposed the normal pending projection. Once
fresh Gateway facts proved Safe Stop, AosCore reported VDP `1.0.16` active with
no error, sent the delta status and received the Cloud acknowledgement. The
Cloud Unit projection then showed `installed` `1.0.16`, no pending batch and
`Online`.

The accepted visual run `20260904T000503.185Z-d76eb0f2` showed CARLA and the
Vehicle Controller live. Autopilot reached `19.50587986414475 km/h`; explicit
Safe Stop returned the vehicle to `0.0 km/h` with full brake, two valid mode
changes and zero rejected control messages. The operator visually accepted
CARLA, Autopilot and Safe Stop on 2026-09-04.

The subsequent cold-restart run `20260904T051849.089Z-a441c387` closed the
remaining persistence gate after restoring the five explicitly run-scoped
Test-only inputs. VDP stayed at `1.0.16`, both `aos-sm` and VDP were
`active/running` with zero restarts, provider health was `HEALTHY`, the
guest-originated VISS source reported selected vehicle data ready, and the
Cloud Unit was `Online`. The CARLA/Gateway manifest completed with all process
exit codes zero, VISS `CONNECTED`, data health `LIVE`, 20-Hz simulation and
4-Hz delivery. Compact evidence is retained below
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/qualifications/vdp-update-on-6.1.1-maninblack.27/clean-reprovision-vdp-1.0.16/cold-restart`.

During resume, the only Cloud-offline interval was traced to a host-profile
port mismatch: the current overlay routed dnsmasq to `18053`, while the
successor launcher selected `18056`. No guest DNS or image correction was made
to pass the gate; the bridge was aligned to the overlay's already accepted
route. The source fix now passes each launcher's selected DNS port into fresh
overlay onboarding, preventing the mismatch for subsequent runs.

The `.26`/VDP `1.0.13` state remains diagnostic evidence only. `.27` with the
`1.0.15`/`1.0.16` pair is the repeatable qualification result. Repository
publication and final disk/branch cleanup are tracked as post-qualification
closeout and do not change these runtime facts. The runtime, visual and
cold-restart gates are closed. The clean-build gate passed from pinned source as recorded in
[`ltvp-27-clean-build.md`](ltvp-27-clean-build.md). Its current state, retained
signed-bundle digests and compact evidence-tree hashes are recorded in
[`ltvp-27-closeout-inventory.v1.json`](../../manifests/r6-1/ltvp-27-closeout-inventory.v1.json).
