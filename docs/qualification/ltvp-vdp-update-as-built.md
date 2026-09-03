<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP VDP update: specification-to-implementation record

- Recorded: 2026-09-03
- Current evidence vehicle: `.26`
- Current demonstrated update: VDP `1.0.13`
- Release qualification target: `.27` with VDP `1.0.14` and `1.0.15`

## Demonstrated state

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
| Provenance | exact source-to-artifact binding | `1.0.13` metadata does not identify a release source | produce clean `1.0.14`/`1.0.15` |

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

## Open release gates

- reproduce every final source change on clean branches;
- integrate the corrected runtime and network configuration in `.27`;
- build source-traceable VDP `1.0.14` and `1.0.15` deployment bundles;
- prove that Factory placeholder `0.0.0` cannot reclaim the active component
  after Cloud reconciliation or reboot;
- pass two complete E2E cycles from the same immutable `.27` image; and
- push the final branches and record exact commits/artifacts only after both
  cycles pass.

Until those gates close, `.26` and VDP `1.0.13` remain diagnostic evidence and
must not be described as the final Factory or release-qualified update.
