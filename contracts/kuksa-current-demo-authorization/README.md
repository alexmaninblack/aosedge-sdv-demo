<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current-Demo KUKSA Authorization Exchange

This directory is the canonical machine-readable cross-component contract for
accepted `D4-027.3` through
[`D4-027.8`](../../docs/requirements/d4-decision-register.md#d4-027-8).
It defines the temporary current-AosCore exchange between the Brake/Tire
compatibility bootstrap and `CMP-KAC`; it is not a future native AosCore API.

- [protocol profile 1.7.0](kuksa-auth-compat.v1.json)
- [request schema](kuksa-auth-request.schema.json)
- [response schema](kuksa-auth-response.schema.json)

One Unix stream connection contains exactly one UTF-8 JSON request terminated
by LF, one LF-terminated response and server close. Requests are either
credential-free `status` or `issue` with only opaque `aosSecret`; renewal sends
`issue` again. Resource `kuksa` is implicit. Unknown or duplicate object
members, invalid UTF-8, trailing objects and caller-selected authority are
rejected.

`ready` reports only technical substrate readiness. `issued` carries the JWT
and its expiry/renewal instants. `rejected` carries only a fixed code,
retryability and KAC-generated correlation.

The accepted Service mapping is deliberately narrow: IAM `r` becomes
`read:<exact-path>`, IAM `rw` becomes `actuate:<exact-path>` because the pinned
KUKSA `actuate` permission already includes read, and IAM `w`, unknown modes,
wildcards or any partial-trimming attempt reject the whole issuance. Service
tokens never receive `provide` or `create`.

For the pinned AosCore release, the helper reaches the native
`IAMPublicPermissionsService/GetPermissions` gRPC interface only at fixed
`127.0.0.1:8090`. The client uses TLS, trusts the Aos CA and verifies the
expected server name `main`; neither DNS, caller-selected endpoints nor any
external IP address is allowed. This loopback-only client exception exists
because the released IAM public interface is TCP. It does not create a KAC TCP
listener and it remains available when vehicle external connectivity is
removed.

JWT TTL is 300 seconds and renewal begins 180 seconds after issue, leaving a
120-second recovery reserve. Every renewal repeats the authoritative IAM
lookup. Successful renewal requires the Service to reconnect and recreate its
KUKSA subscriptions with the replacement token; terminal denial deletes the
token and disconnects immediately, while transient failure may use the current
token only until its signed expiry. Cloud connectivity is not part of this
local renewal path.

Each provisioned Unit owns one protected `kuksa-jwt` RSA key pair. The private
key remains non-exportable behind PKCS#11. After provisioning,
`aos-kuksa-verifier-prepare.service` proves the protected sign/verify path and
atomically publishes only the root-owned mode-`0444` public key at
`/run/aos-kuksa-verifier/kuksa-jwt-public.pem`. Unmodified KUKSA must start
with that exact file through `--jwt-public-key`; absence or malformed content
blocks KUKSA and the helper rather than allowing KUKSA's authorization-disabled
fallback. Reboot regenerates the runtime verifier from the same Unit key and
starts the helper with empty state. Live key rotation is outside the first
demo, and R0 retires the key by discarding the provisioned overlay after Cloud
reconciliation.

The current demo uses the pinned SoftHSM/OpenSSL PKCS#11 stack with token label
`aos-kuksa`, a separate root-owned mode-`0600`
`/var/aos/iam/.kuksa-jwt-pin` and no file-key fallback. KAC and the verifier
preparation unit receive the PIN only through systemd credentials; it is never
placed in a URI, environment, argument or log. The public verifier directory
is root-owned mode `0755`, while KAC owns only its mode-`0750` runtime directory
and mode-`0660` private socket. KAC has no persistent state directory and may
not read Service token tmpfs locations.

KAC and verifier preparation run in separate SELinux domains. The KAC domain
has only its socket/runtime files, its private systemd credential, verifier/CA
reads, the fixed PKCS#11 signing path, fixed TLS loopback IAM access, time-sync
evidence and redacted journald events. It has no capabilities, shell, DNS,
external network, arbitrary `/var/aos`, shared AosCore PIN, Service tmpfs,
public-verifier write or systemd-management access. Initial SoftHSM backend
access is read/open/lock only; create, delete or rename requires a separate
review, and policy is never widened automatically from audit output. SoftHSM
is a demo software-token implementation and is not evidence of hardware-HSM
physical isolation or production non-extractability.

Time becomes trusted only after one successful `systemd-timesyncd` NTP
synchronization per boot followed by a 10-second stable window. JWT epoch
claims use UTC `CLOCK_REALTIME`, while renewal/retry scheduling uses
`CLOCK_BOOTTIME`. Before every issue or renewal, the temporary helper compares
their elapsed progression and rejects the operation as `TIME_UNTRUSTED` when
the deviation is greater than five seconds. It deliberately adds no separate
time-guard service, persistent or boot-local anchor, continuous monitor, KUKSA
stop/restart orchestration or instant revocation. An already issued JWT may
remain usable only until its signed expiry. Loss of external connectivity
after the initial gate does not revoke trust; recovery requires synchronized
time and another 10-second stable window. A cold offline boot leaves
authorization `NOT_READY` without blocking unrelated AosCore functions.

This is the minimum current-release compatibility behavior. A future released
native AosCore contract must be requalified for trustworthy time, bounded
credential invalidation and recovery before the helper is removed; this
temporary profile does not prescribe that native implementation.

The helper accepts at most 16-KiB requests, 32-KiB responses, 16-KiB JWTs,
64 exact permissions and 512-byte paths. It permits four concurrent requests,
an eight-connection backlog, bounded per-peer/global token-bucket rates and an
eight-second whole-request deadline. Retry uses 1/2/4/8/16/30-second backoff
with ±20% jitter and never crosses JWT expiry. The process is capped at 32
tasks and 128 file descriptors. The first demo deliberately sets no unmeasured
CPU or memory ceiling for this temporary platform helper; Brake and Tire SOTA
instances remain the only quota-controlled tenants. KAC exposes only its
private Unix socket, permits `AF_INET` solely for the fixed TLS loopback IAM
client, denies external IP traffic and logs only fixed event code,
correlation, outcome and retryability. Secrets, tokens, claims, paths,
permission content, signing input and raw frames are forbidden.

D4-027 is complete. Implementation still requires the broader D4 and change
plan gates; this contract itself authorizes no source, image or Unit mutation.

The package is deleted together with `CMP-KAC` after equivalent released native
AosCore support passes the same authorization and negative qualification.
