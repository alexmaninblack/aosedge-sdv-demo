<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP VISS server-authenticated TEST_ONLY exception

- Exception ID: `LTVP_VISS_SERVER_AUTH_TEST_ONLY`
- Version: 1.1.0
- Lifecycle state: accepted for the repeatable `.27` Test Vehicle qualification only

This exception records the server-authenticated VISS path used by the LTVP
engineering demonstration. It does not replace the accepted
[VISS Trust and Telemetry Profile](../viss-trust-telemetry-profile/README.md)
or the [Platform FOTA Safe Stop Contract](../platform-fota-safe-stop/README.md).
Purpose-bound per-Unit mTLS remains the Production design and a separate
Factory/provisioning qualification.

## Closed scope

The provisioned Aos IAM identities remain the only private client identities
inside the VM. This exception creates no VISS client certificate, private key,
PKCS#12 object or new IAM role. The VDP and OEM Component Runtime use a public
Gateway CA and a closed non-secret source binding to read VISS 3.1 through the
fixed QEMU host route:

```text
CARLA Gateway 127.0.0.1:6443
  -> QEMU host route wss://10.0.0.1:6443
  -> guest verifies the Gateway certificate for 127.0.0.1
```

The Gateway binds only to Mac loopback. Server authentication proves the
server and encrypted transport; it provides no client identity or VISS role
authorization. The only permitted audience is `Test Vehicles`. Production and
Campaign use are excluded.

The `.27` Factory Image contains the qualified OEM Component Runtime source.
Unlike the `.26` exploratory proof, `.27` must not replace `aos-sm` or install
its executable through `/run`. Only the public CA and closed binding files are
run-scoped inputs. A fresh VM must become Online without a post-boot DNS or
rootfs correction.

## Exact consumer inputs

The VDP consumes `viss-server-ca.pem` and `viss-selected-source.json`. Its
schema-3 binding identifies the current Cloud Unit and Cloud Main Node record:

```json
{
  "schemaVersion": 3,
  "profile": "LTVP_VISS_SERVER_AUTH_TEST_ONLY",
  "viss": {
    "uri": "wss://10.0.0.1:6443",
    "tlsServerName": "127.0.0.1"
  },
  "selectedSource": {
    "unitId": "<current-test-unit-uuid>",
    "nodeId": "<current-cloud-main-node-uuid>",
    "assignmentGeneration": "<positive-run-integer>",
    "pathSet": "VDP_V1"
  }
}
```

The Safe Stop adapter consumes `viss-update-ca` and
`viss-update-binding`. AosCore supplies a node/system UID as a lowercase
32-hex identifier to the component runtime; this is not the Cloud Node record
UUID. The schema-2 binding therefore uses that exact Aos node/system UID:

```json
{
  "schemaVersion": 2,
  "profile": "LTVP_VISS_SERVER_AUTH_TEST_ONLY",
  "unitId": "<current-test-unit-uuid>",
  "nodeId": "<current-aos-node-system-uid-32hex>",
  "assignmentGeneration": "<positive-run-integer>",
  "endpoint": "wss://10.0.0.1:6443",
  "tlsServerName": "127.0.0.1",
  "pathSet": "PLATFORM_FOTA_SAFE_STOP_1_1_1"
}
```

Both objects reject missing and additional fields. Strict mTLS remains the
default whenever the exact Test-only profile is absent. Mixed Test-only and
private client material fails closed. The inputs contain no secret and are
recreated after reboot before their consumers start.

## Safe Stop and component behavior

The Safe Stop adapter reads all ten required paths with one VISS request. One
accepted snapshot has one source timestamp and one monotonic frame identifier;
sequential reads from different frames are not accepted as a coherent sample.
The profile requires twelve consecutive samples at the accepted 50-ms period,
with the exact freshness and motion thresholds owned by the canonical Safe
Stop contract. Connection shutdown must not block qualification on a peer that
does not complete a WebSocket close handshake.

The component runtime accepts the Aos deployment-bundle component layer media
type `application/vnd.aos.image.component.full.v1+gzip`, inflates it and then
validates the embedded provider archive. Component removal and replacement use
idempotent `StopInstance` behavior when the requested component is already
absent. The Factory placeholder and the Cloud update must not compete after a
cold restart; the installed update remains the active authority.

## Repeatable qualification

Qualification uses one immutable `.27` image twice:

1. provision a clean overlay, join `Test Vehicles`, deliver VDP `1.0.15`,
   apply it after an explicit Safe Stop and prove readiness after reboot;
2. deprovision and delete that Unit, stop the VM and delete its overlay and
   provisioning state without backup;
3. create a new overlay from the unchanged `.27` image SHA, provision a new
   Test Vehicle and repeat the complete flow with VDP `1.0.16`;
4. require `1.0.16` to differ from `1.0.15` only in coherent version-owned
   metadata while using the same accepted source and functional payload.

The only terminal claim is
`TEST_ONLY_SERVER_AUTHENTICATED_VISS_PROVEN`. It requires Cloud installed
state, AosCore active state, VDP `READY/source LIVE`, visual CARLA motion,
visible waiting while moving, explicit Safe Stop release, live data after
resume and successful cold-restart recovery in both cycles. It is not a
strict-mTLS, Production, Campaign or release-homologation claim.
