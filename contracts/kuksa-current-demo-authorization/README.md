<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current-Demo KUKSA Authorization Exchange

This directory is the canonical machine-readable cross-component contract for
accepted `D4-027.3` through
[`D4-027.8`](../../docs/requirements/d4-decision-register.md#d4-027-8).
It defines the temporary current-AosCore exchange between the Brake/Tire
compatibility bootstrap and `CMP-KAC`; it is not a future native AosCore API.

- [protocol profile 1.4.0](kuksa-auth-compat.v1.json)
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

Time becomes trusted only after one successful `systemd-timesyncd` NTP
synchronization per boot followed by a 10-second stable window. JWT epoch
claims use UTC `CLOCK_REALTIME`, while renewal/retry scheduling uses
`CLOCK_BOOTTIME`. A mode-`0600` boot-ID-bound anchor under `/run` permits helper
restart in the same boot but is never reused after VM reboot. Loss of external
connectivity after this gate does not revoke trust. A wall/boot-clock deviation
greater than five seconds blocks issuance, stops KUKSA and removes cooperating
Service tokens until a new synchronization and stable window complete. A cold
offline boot therefore leaves KUKSA authorization `NOT_READY` without blocking
unrelated AosCore functions.

The helper accepts at most 16-KiB requests, 32-KiB responses, 16-KiB JWTs,
64 exact permissions and 512-byte paths. It permits four concurrent requests,
an eight-connection backlog, bounded per-peer/global token-bucket rates and an
eight-second whole-request deadline. Retry uses 1/2/4/8/16/30-second backoff
with ±20% jitter and never crosses JWT expiry. The process is capped at 64 MiB,
10% CPU, 32 tasks and 128 file descriptors, exposes only `AF_UNIX`, and logs
only fixed event code, correlation, outcome and retryability. Secrets, tokens,
claims, paths, permission content, signing input and raw frames are forbidden.

D4-027 is complete. Implementation still requires the broader D4 and change
plan gates; this contract itself authorizes no source, image or Unit mutation.

The package is deleted together with `CMP-KAC` after equivalent released native
AosCore support passes the same authorization and negative qualification.
