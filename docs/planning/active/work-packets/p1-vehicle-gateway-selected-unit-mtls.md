<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Gateway Selected-Unit mTLS Work Packet

- ID: `WP-P1-VEH-GATEWAY-SELECTED-UNIT-MTLS-001`
- Lane: `L-VEH`
- Increment: `IMP-02D`
- State: `REBASELINE REQUIRED ON ACCEPTED CONTROLLER-HANDOFF BASE 162eaa3`
- Version: 0.4
- Prepared: 2026-08-29
- Authorized: 2026-08-30 as part of the bounded Demo Interface Train
- Status synchronized: 2026-08-31
- Product edits and local/offline tests authorized only after the corrected
  controller-handoff base is accepted; dependency retrieval, retained real
  certificates, live CARLA, VM, Unit, Cloud, signing, FOTA, push and merge
  authorized: no
- Assessment performed: read-only source, contract and requirement inspection
- Execution train:
  [Consolidated Implementation Execution Trains](../infrastructure-first-critical-path-proposal.md)

## Outcome

Implement the Vehicle Gateway half of the accepted D4-005/D4-006 trust and
exclusive-source boundary. In strict demo mode the embedded VISS server shall:

1. require TLS 1.2 or later, server authentication, a trusted client
   certificate and the `VISSv3` WebSocket subprotocol;
2. distinguish the selected OEM Vehicle Data Platform peer, its distinct
   purpose-bound Platform Update Runtime peer, the independent read-only
   Engineering Dashboard and the qualification-only client;
3. bind both selected-Unit roles to the exact Unit ID, Main Node ID, leaf
   certificate SHA-256 fingerprint and current assignment generation;
4. admit at most one connection for each role, close selected-bound sessions
   on detach and reject unknown, wrong-Unit, wrong-role, wrong-fingerprint,
   expired, non-selected and additional peers;
5. enforce the accepted per-role read surface, including only the ten Safe
   Stop paths for `PLATFORM_UPDATE_RUNTIME`; and
6. prevent a newly selected Unit from receiving a cached pre-assignment frame
   while allowing the independent Engineering Dashboard to remain connected.

This packet does not make a functional Brake or Tire Service a VISS client.
`SELECTED_PLATFORM_UNIT` is the trusted OEM VDP transport role; it is not an
Aos Service Provider role and does not change KUKSA Provider authorization.
Brake and Tire Services continue to use KUKSA only and receive no VISS client
certificate, VISS role or direct Gateway access.

## Frozen sources and digests

### Product source

| Item | Exact value |
| --- | --- |
| Repository | `carla-ego-runtime` |
| Safe Stop projection commit | `8af302dd11c872a564ea7542a126c9886daf2a5a` |
| Historical proposed integration base | `d4a20c85196ef7df81c78f992f6237c5eca8ff6c` |
| Accepted controller-handoff predecessor | `162eaa3c65ed1c4e9a981b4efd133a9287e8ebe2` |
| Accepted predecessor parent | `a8d27194fa74d29f1fc45b7b849ddb727fed9fe6` |
| Accepted predecessor tree | `c58439737b8d1924ad5b9b44fd1e3cd9898a9147` |
| Required base state | clean, after this packet is rebaselined and re-accepted |
| Proposed branch | `codex/imp-02d-selected-unit-mtls` |
| Proposed isolated worktree | `../carla-ego-runtime-imp-02d-selected-unit-mtls` |

The original frozen base has moved only through the accepted controller-
handoff correction train, now integrated at `162eaa3`. Product implementation
must not start from either the historical `d4a20c` snapshot or the new tip
until this packet refreshes its source/tree identities, current-state
assessment, exact writable boundary and affected tests against `162eaa3`, and
that bounded rebaseline is independently accepted. Untracked cache material is
not an input and shall not enter the future worktree.

### Solution source

The committed solution readiness parent is
`aosedge-sdv-demo@107031a353308fc670d4a477e302e7a6bd278e55`; the accepted
correction cascade is pinned by the exact digests below.

| Frozen input after `107031a` | SHA-256 |
| --- | --- |
| VISS Trust and Telemetry 1.1.0 | `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c` |
| Exclusive Live-Source Assignment 1.0.0 | `9434ec3a8abb6a9ef3e283b4d0a505f7dbb4f848b37232df83d8e21a899d4ce2` |
| Demo Run State 1.1.0 | `3cc284f15b0b81f2c145b64e813c6081e255cf74b883f8feb6111db4bf47dcf2` |
| D4 Decision Register | `91842de2ec12a8f802a9bc2ae402e2db77af76ccf9d248ca1a44463a3943e556` |
| Vehicle Gateway requirements | `39aaf18675a8b4160f734c075ca411919d99a90071afb19ab9c070e2eeaa2d8e` |
| Vehicle Data Platform requirements | `32dc38aa98fd94edcb52a60f9fe77953c5244cd2e07acfd9fa7ea40af410bfc1` |
| Factory Substrate requirements | `a3ccea88d138fdbcffbfee52f2561686a637844983201cb65d11a86585bc466d` |
| Component/interface register | `b37205720325f127b9d4a020e64c75f97af18ae58ee74c40abe9fc168c7d0dc3` |
| System requirements/traceability | `674c888657237b4b2ef013c5b5b584101983203dc30e792327a22354710607bd` |
| Accepted Platform P0 decisions | `c5a8ce0ecfb79d85687107fa13ea64638e22bbb3f67dd4f004c2c4e8f07f21cb` |
| Single-node provisioning evidence | `553f8be26c4f29c3e201b5e5d024ad8c57e7a6c2cd35341904b26624a4f15c15` |

Every digest and both product commits must be rechecked immediately before
implementation starts.

## Read-only current-state result

The following is the historical read-only assessment at `d4a20c85`; it must be
revalidated during the required `162eaa3` rebaseline. At that snapshot the
Gateway already provides TLS 1.2+, a server certificate,
`VISSv3`, bounded subscriptions/pending output and server-authenticated
Get/Subscribe/Unsubscribe behavior. It does not yet provide D4-006 mTLS:

- the TLS context has no client trust bundle and does not require a client
  certificate;
- all accepted connections are generic and the configured cap remains eight;
- the server does not extract a leaf certificate, verify a role URI, calculate
  a fingerprint or keep a selected-Unit assignment;
- the VISS protocol has no per-role exact-path policy;
- the current network test disables server verification and presents no
  client certificate;
- the bundled client verifies only the server; and
- no local assignment-control interface, generation compare-and-swap or
  selected-session closure exists.

The accepted VDP source at `aos-vehicle-platform@667afb1512cf43ff27f1ab5327293208bf73045b`
already has partial client-side seams: it can load a client certificate/key
from the systemd credential directory and reads an external `selectedSource`
object containing `unitId`, `nodeId`, `clientCertificateSha256`,
`assignmentGeneration` and `role`. That object has no checked-in canonical
schema or implemented host-side producer, and its `ReadinessTracker` identity
is not wired into the running bridge. It is evidence for field alignment, not
proof of an end-to-end selected-Unit implementation.

No current implementation creates the per-Unit VISS client identities after
provisioning or supplies the purpose-bound Platform Update Runtime client.
Those are real cross-repository integration gaps, not work to hide inside the
Gateway server.

## Proposed exact trust model

This section is the frozen recommended safe-default bundle for the Demo
Interface Train. It becomes the execution contract only when that train
receives its one-time consolidated authorization; it does not need five
separate operator approvals.

### Certificate and fingerprint profile (`MTLS-01`)

- One protected local demo VISS CA remains outside Git and Unit images. The
  Gateway receives an explicit client trust bundle; VDP/runtime/dashboard
  clients continue to receive an explicit server trust anchor. A caller may
  configure the same local root in both directions, but server and client leaf
  certificates have distinct keys and EKUs.
- A client leaf must chain to the configured client CA, be currently valid,
  carry `digitalSignature` key usage and `clientAuth` EKU, and contain exactly
  one recognized URI SAN. CN, OU, source IP, DNS name and request payload are
  never identity authority.
- Proposed selected-role URI SAN syntax is:
  `urn:aosedge:demo:viss-client:v1:<role>:<unit-uuid>:<main-node-uuid>`, where
  `<role>` is `selected-platform-unit` or `platform-update-runtime` and both
  UUIDs use canonical lowercase RFC 4122 text.
- Proposed independent-role URI SAN values are
  `urn:aosedge:demo:viss-client:v1:engineering-dashboard` and
  `urn:aosedge:demo:viss-client:v1:qualification-client`.
- The enrollment fingerprint is SHA-256 over the leaf certificate's DER bytes,
  encoded as exactly 64 lowercase hexadecimal characters without separators.
  This matches the current VDP fingerprint calculation.
- `assignmentGeneration` is never encoded into the certificate. It is mutable
  selection state and is attached by the Gateway to the accepted session.

Malformed, multiple recognized, unrecognized or identity-conflicting SANs
fail closed. No certificate or private-key bytes enter logs, assignment
messages or the current-run journal.

### Selected-assignment control (`MTLS-02`)

The Host Demo Orchestrator owns durable current-run identity references and
the assignment operation. The Gateway owns transport admission and its
in-memory current selection. The proposed handoff is one private local
`AF_UNIX/SOCK_STREAM` control socket, separate from vehicle control and the
controller-facts framed stream:

- pathname is explicit and short enough for the macOS Unix-socket limit;
- parent directory is mode `0700`, socket is mode `0600`;
- the peer effective UID must equal the Gateway effective UID, using
  `getpeereid` on macOS and `SO_PEERCRED` on Linux;
- each connection carries one newline-terminated UTF-8 JSON request, maximum
  4096 bytes, and receives one bounded JSON response before close;
- exact keys are required and unknown keys, invalid UTF-8, duplicate JSON
  members, malformed UUID/fingerprint/integer values and trailing content are
  rejected before mutation; and
- requests are serialized in the Gateway I/O context. There is no network
  assignment endpoint and no bearer token.

Proposed schema version 1 has three actions:

```json
{"schemaVersion":1,"action":"select","requestId":"<bounded-id>","expectedAssignmentGeneration":0,"selectedSource":{"unitId":"<uuid>","nodeId":"<uuid>","selectedPlatformUnitCertificateSha256":"<sha256>","platformUpdateRuntimeCertificateSha256":"<sha256>"}}
```

```json
{"schemaVersion":1,"action":"detach","requestId":"<bounded-id>","expectedAssignmentGeneration":1,"selectedSource":{"unitId":"<uuid>","nodeId":"<uuid>"}}
```

```json
{"schemaVersion":1,"action":"status","requestId":"<bounded-id>"}
```

An accepted `select` requires `DETACHED`, exact expected generation and two
distinct fingerprints; it advances generation by one and enrolls both
selected-bound roles atomically. An accepted `detach` requires the exact
current Unit/Node and generation; it closes and removes both selected-bound
sessions, clears the enrollment and advances generation by one. Direct
selected-Unit replacement is rejected: the accepted demo flow must explicitly
detach, prove no selected consumer, perform the canonical reset, then select.

Responses carry the request ID, result/reason, `DETACHED` or `SELECTED`, and
current generation. `status` returns the current public identity references
and active role counts for reconciliation, never certificate content. A lost
mutation response is reconciled with `status`; blind retry is forbidden and a
stale expected generation has no side effect.

The Gateway process starts detached. The orchestrator supplies the last
validated journal generation through an explicit start option so generation
does not silently return to zero after Gateway restart. A missing/corrupt
journal or inconsistent initial generation prevents strict assignment mode
from becoming ready; the Gateway never invents or persists authoritative run
state.

### Session and data behavior (`MTLS-03`)

- Strict TLS uses `verify_peer | verify_fail_if_no_peer_cert`; CA/validity/EKU
  verification completes before WebSocket upgrade.
- Certificate URI identity and DER fingerprint are matched against the current
  selection or independent-role enrollment before `VISSv3` acceptance.
- Global strict-mode maximum is four active role sessions and every role has
  maximum one. A second session is rejected; it does not evict the accepted
  session.
- The selected VDP role receives only paths whose D4-006 access includes
  `SELECTED_PLATFORM_UNIT`. The Runtime receives exactly the ten frozen Safe
  Stop paths. Dashboard and qualification roles are read-only. Unauthorized
  Get/Subscribe selection returns protocol-valid unavailable data without
  revealing another role's path set. Every Set remains denied in this packet.
- On `select`, the Gateway records the current latest frame as the exclusive
  lower bound for both selected-bound roles. Those roles receive no Get or
  subscription data until a later complete snapshot is published. This
  prevents reuse of the previous Unit/generation's cached frame. The
  independent Dashboard is not subject to that floor and may remain live.
- Every selected-bound session stores the assignment generation accepted at
  handshake. A generation change closes it and clears its subscription state.
- Transport disconnect retains the current selection. The same enrolled
  Unit/role/fingerprint may reconnect with the accepted client backoff of
  500 ms through 10 s. The server never selects a Unit merely because its
  certificate arrives.
- Certificate validity is evaluated at TLS handshake. First-demo code adds no
  mid-session expiry timer, CRL fetch, OCSP or CA rotation daemon. Assignment
  removal is the immediate local revocation mechanism because it closes the
  live session. An expired certificate cannot reconnect.
- In-run client-certificate replacement is not automatic. It requires explicit
  detach, enrollment of the new fingerprint, a higher assignment generation
  and reconnect. Demo CA/server-certificate rotation requires a controlled
  Gateway restart and authoritative journal recovery. R0 destroys Unit-owned
  client material and current-run VISS material in the accepted order.

## Proposed strict configuration ownership

| Configuration/material | Owner | Delivery/use |
| --- | --- | --- |
| Gateway server chain/private key | Demo Orchestrator/local setup | Explicit protected file paths; never journaled or logged |
| VISS client CA bundle | Demo Orchestrator/local setup | Gateway strict TLS context |
| Dashboard/qualification leaf fingerprints | Demo Orchestrator | Explicit public enrollment at strict startup; qualification role may be absent outside qualification |
| Unit/Node identity and both selected-role fingerprints | Demo Orchestrator after provisioning | `select` control request plus fingerprint-only run journal |
| Assignment generation | Demo Orchestrator journal + Gateway CAS | Initial generation at Gateway start, then atomic select/detach increments |
| VDP/runtime client chain and private key | Per-Unit onboarding owner | Root-owned overlay material through systemd `LoadCredential` |
| Role/path enforcement | Vehicle Gateway | Compiled D4-006 policy; never supplied by a client |

Strict configuration absence or inconsistency keeps selected-bound VISS
`NOT_READY`; it never falls back to generic client admission. Historical
server-authenticated loopback tooling may remain available only as an explicit
development profile that cannot bind outside loopback and is never used as
D4-006 evidence. Whether to retain that development profile is a review
decision below, not an implicit compatibility promise.

## Proposed smallest Gateway writable boundary

If `MTLS-01` through `MTLS-05` are accepted, the Gateway-core implementation
is limited to these twenty paths in `carla-ego-runtime`:

1. `CMakeLists.txt`;
2. `include/carla_ego_runtime/viss_access.hpp` — new;
3. `src/viss_access.cpp` — new;
4. `include/carla_ego_runtime/viss_assignment_control.hpp` — new;
5. `src/viss_assignment_control.cpp` — new;
6. `include/carla_ego_runtime/viss_protocol.hpp`;
7. `src/viss_protocol.cpp`;
8. `include/carla_ego_runtime/viss_server.hpp`;
9. `src/viss_server.cpp`;
10. `include/carla_ego_runtime/runtime_options.hpp`;
11. `src/runtime_options.cpp`;
12. `src/runtime_carla.cpp`;
13. `src/viss_client.cpp`;
14. `tests/viss_access_test.cpp` — new;
15. `tests/viss_assignment_control_test.cpp` — new;
16. `tests/viss_protocol_test.cpp`;
17. `tests/viss_network_test.cpp`;
18. `tests/runtime_options_test.cpp`;
19. `docs/viss-profile.md`; and
20. `docs/telemetry-contract.md`.

The bundled client change adds explicit client-chain/private-key inputs for
deterministic Dashboard/qualification testing. It does not create or store
credentials. Existing controller handoff, VSS projection, vehicle-control,
CARLA sampling and launcher files remain frozen. A need to change any launcher
or add an onboarding/config producer returns a separate bounded packet rather
than widening this one silently.

## Deterministic verification

All credentials used by unit/network tests are generated ephemerally in the
test process or temporary directory and destroyed afterward. No external
network, live CARLA or VM is required.

1. **Certificate tests:** valid CA-signed role certificate; missing client
   certificate; wrong CA; self-signed leaf; expired and not-yet-valid leaf;
   absent/wrong EKU; missing, duplicate, malformed and conflicting URI SAN;
   canonical fingerprint; wrong Unit, Node, role and fingerprint.
2. **Assignment tests:** detached startup, restored initial generation, exact
   select/detach CAS, stale generation, direct replacement denial, distinct
   role fingerprints, overflow, malformed/oversize/duplicate-key messages,
   same-UID admission, wrong-UID rejection where the platform permits the
   fixture, lost-response status reconciliation, restart and owned-socket
   cleanup.
3. **Role-policy tests:** selected VDP allowed/denied paths, exact ten-path
   Runtime allowlist, Dashboard/qualification read-only behavior, branch and
   wildcard selections that cannot cross a role boundary, and Set denial.
4. **Real loopback mTLS tests:** all four roles, one connection each, global
   cap four, missing/unknown/additional client denial, `VISSv3` requirement,
   old selected-session closure, old fingerprint reconnect denial, new Unit
   acceptance and independent Dashboard continuity.
5. **No-stale-generation tests:** pre-selection latest snapshot unavailable to
   selected roles, first later frame accepted, detach/select does not leak the
   previous Unit's cached frame, and Dashboard delivery remains continuous.
6. **Regression:** existing controller facts, Safe Stop projection, VSS
   protocol/network, runtime option, Python tool and documentation tests;
   format/static analysis/sanitizers already supported by the repository;
   exact twenty-path boundary and `git diff --check`.

An implementation completion record must include test commands/results,
ephemeral certificate matrix, per-role allow/deny matrix, assignment traces
with redacted identity fingerprints, base/digest recheck and one clean local
commit. It does not establish live Unit or onboarding qualification.

## Platform limitations

- The Gateway and assignment socket run on macOS in the first demo. macOS Unix
  socket paths are short; the Orchestrator must allocate the path under its
  existing short per-run directory. Linux `sun_path` length must not be used
  as the macOS design bound.
- Peer UID inspection is platform-specific: `getpeereid` on macOS and
  `SO_PEERCRED` on Linux. Absence of either supported API is a compile-time
  stop, not a permission downgrade.
- `systemd LoadCredential` applies to Linux VDP/Runtime clients in the Unit VM,
  not to the macOS Gateway. This packet can test client-certificate behavior
  with the bundled client but cannot prove guest credential delivery.
- OpenSSL performs certificate-chain, time, purpose and TLS checks. Tests must
  not shell out to fetch a CA, CRL or OCSP responder. First-demo revocation is
  explicit fingerprint de-enrollment, not an Internet PKI claim.
- Cross-Unit live proof, client credential custody and overlay destruction
  require disposable VM qualification after Gateway and client integrations
  fan in.

## Explicit exclusions

- per-Unit certificate creation, signing, export, import, renewal or deletion;
- Demo Orchestrator/run-journal implementation and UI actions;
- VDP or Platform Update Runtime client implementation/systemd wiring;
- KUKSA Provider/Service JWTs, KAC, Aos IAM or Cloud credentials;
- Safe Stop policy evaluation, waiting state or FOTA activation;
- D4-008 typed advisory Set implementation;
- source-state/KUKSA `NotAvailable` implementation outside the Gateway role
  gate;
- live CARLA, VM, Unit, Cloud, provisioning, R0, image build or networking;
- dependency or lockfile changes; and
- merge, push or direct mutation of any `main` branch.

## Bundled safe defaults and deferred live blockers

The consolidated Demo Interface Train authorization accepted these five
technical defaults together on 2026-08-30. They preserve the already accepted
business and security boundary and do not create a separate approval round:

| ID | Bundled default | Status before train authorization |
| --- | --- | --- |
| `MTLS-01` | Use one exact URI SAN identity plus lowercase SHA-256 of DER leaf bytes; no CN/OU/IP authority | Accepted |
| `MTLS-02` | Use the private same-UID Unix stream CAS interface and exact select/detach/status schema above; start from the journal generation | Accepted |
| `MTLS-03` | Require explicit detach before replacement; close selected sessions; apply a per-assignment frame floor; keep Dashboard independent | Accepted |
| `MTLS-04` | No automatic first-demo live rotation or mid-session certificate-expiry timer; reconnect revalidates and fingerprint de-enrollment closes active sessions | Accepted |
| `MTLS-05` | Implement only the twenty-file Gateway core here; retain server-auth-only loopback solely as an explicit non-demo development mode; use separate bounded packets for onboarding, VDP/Runtime wiring and Orchestrator production | Accepted |

There is no further product decision inside the Gateway-core packet. The
controller-handoff macOS transport and targeted CARLA-enabled compile/link
blockers are closed at accepted product tip `162eaa3`; however this packet is
not entry-ready because its frozen source, digests, assessment and twenty-file
boundary still describe `d4a20c`. A bounded rebaseline and independent
acceptance are required before implementation. Two cross-repository items
remain intentionally deferred
after Gateway-core and host-only test completion:

1. a reviewed onboarding/config packet must create the two distinct per-Unit
   role certificates only after exact Unit/Main Node identity is known,
   provision root-owned credentials, enroll only fingerprints, populate the
   journal and remove material at R0; and
2. a reviewed client-integration packet must wire the existing VDP mTLS seams,
   complete source-readiness use, add the Platform Update Runtime mTLS client
   and qualify identical assignment generation on both sides.

No placeholder identity, shared VU/PU client certificate, static Factory Image
credential, source-IP trust, client-declared role, guessed AosCloud field or
automatic fallback is permitted to bypass those blockers.

## Stop conditions

Stop before product edits if the consolidated train is not authorized, a
bundled default cannot be implemented, a digest or base mismatches, the
worktree is not clean, a twenty-first product path is needed, peer
verification/path policy would need to be weakened, old sessions cannot be
closed atomically, cached-frame reuse cannot be prevented, Unit/Main Node
encoding is ambiguous, assignment input is unbounded, the required
peer-credential API is unsupported, credential/private identity exposure or
dependency retrieval is required, or any live/external action becomes
necessary.
