# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

# R6.1 Provider Runtime and Dependency Discovery

## Status

- Discovery status: complete
- Consolidated product delta: side-loaded, built into `.11`, locally verified,
  and frozen as an unsigned rootfs-only FOTA candidate
- Cloud, provisioned Units, signing identities, and the main demo VM: unchanged
- Disposable VM after discovery: SELinux `Enforcing`, no permissive domains,
  audit enabled with no lost records, and root filesystem read-only

This record consolidates the policy, dependency, recovery, and resource
findings collected before another Yocto image is built. It deliberately avoids
the earlier denial-by-denial build loop.

## Qualified Inputs

- disposable rootfs: `6.1.1-maninblack.10`
- rootfs SHA-256:
  `a39d4c97b9a5e28e372b6b44ec654308b6b1d85a765be752deed1d47e57630c8`
- side-loaded platform revision used for credential-ownership discovery:
  `7cd8de32a7608618a3f45d35f989db3138c455b2`
- compiled consolidated SELinux delta SHA-256:
  `0e6f39cf3f799b2455d1037d6983bb632a692618cd549bcc31a26c3c82aba101`
- consolidated provider unit SHA-256:
  `5c46d2a938c605f4839ef62759f1175c9c3faf51a2b3f116dbb928bc0b8f1c80`
- provider layer SHA-256:
  `baf1c29c9264b8f2422dc155540c3b22716bb43d5f80c1cfeb3cc9529f0bf3cb`
- accepted ARM64 runtime-test SHA-256:
  `f95b051bcbd18bdf1095bc0e373ac9193209b32fb29424d07c552628524a97c0`
- final platform revision:
  `a12c0aa7f8a680b35407776b12bcc025970abc73`
- final rootfs image: `6.1.1-maninblack.11`
- final raw image SHA-256:
  `946a296b7200644bc529080f3512712d8b7ec97dedad520146a4f503cf4006a2`

No private JWT signing key, OEM signing key, Cloud certificate, or Unit identity
was copied into the disposable VM.

## Functional Lifecycle Result

With only `vehicle_data_provider_t` temporarily permissive and global SELinux
remaining `Enforcing`, one targeted run completed all of the following without
another image build:

| Gate | Result |
|---|---|
| First install of provider `0.2.0` through the production profile | Pass |
| Startup without CARLA and seven KUKSA paths unavailable | Pass |
| Live TLS VISS input and seven KUKSA paths available | Pass |
| Read-only KUKSA role denied provider writes | Pass |
| Source loss and explicit unavailability | Pass |
| Provider reload and restart | Pass |
| Update to synthetic `0.3.0` in slot B | Pass |
| Downgrade rejection | Pass |
| Failed synthetic `0.4.0` and rollback to slot B | Pass |
| DynamicUser SOTA boundary, read-only root, and secret exclusion | Pass |

The production first-install test completed in 471 ms. The update and rollback
test completed in 936 ms. The enforcing failure seen before discovery is
therefore isolated to the provider-domain policy boundary rather than the
launcher identity, systemd unit ownership, provider payload, KUKSA token,
VISS bridge, or Service Manager transaction implementation.

## Effective SELinux Findings

Systemd 255 materializes both the private credential directory and the copied
credential with SELinux type `initrc_runtime_t`. DAC access works for the fixed
`aos-vdp` identity with empty Linux capability sets and `no_new_privs`.

The `.10` baseline provider policy has no allow rule from
`vehicle_data_provider_t` to `initrc_runtime_t`. This is the exact cause of the
enforcing `EACCES` at
`/run/credentials/aos-vehicle-data-provider.service`.

The compiled policy already contains the required provider permissions for:

- read, map, and execute access to the dedicated provider store;
- certificate and public-trust reads;
- client-side TCP connections;
- systemd readiness notification and logging;
- shell and interpreter execution without a second domain transition;
- Service Manager control of the provider units.

The `.10` baseline policy does not contain UDP/DNS resolution permissions even though the
root-owned vehicle configuration accepts a `wss://` URI with a hostname. The
standard pinned-refpolicy `sysnet_dns_name_resolve()` interface is therefore a
second required policy delta.

The first consolidated candidate then exposed one additional deterministic
boundary: gRPC TLS aborted because it could not open `/dev/urandom`. The base
policy contains only a conditional `domain`-attribute allow controlled by
`global_ssp`; that boolean is `off` in AosVM. `PrivateDevices=yes`, the device
label `urandom_device_t`, and the fixed non-root identity were all verified as
correct. The final candidate therefore adds the pinned-refpolicy
`dev_read_urand()` interface and checks the direct, unconditional compiled
rule rather than accepting the disabled conditional rule.

The baseline did not emit permissive-domain AVC records, including after a
temporary live `semodule -DB`. Kernel audit remained enabled, auditd was
active, and no records were lost. The full functional result and effective
compiled-policy queries are therefore the discovery evidence; an absent AVC
must not be treated as evidence that an allow rule exists.

## Dependency and Recovery Matrix

### Baseline discovery

| Injection | Observed result | Classification |
|---|---|---|
| Stop KUKSA | Provider became inactive | Expected from current hard dependency |
| Start KUKSA again | Provider required an explicit restart | Confirmed recovery defect |
| Replace credential source while provider is running | Reload continued with the systemd snapshot | Expected `LoadCredential` behavior |
| Restart with an invalid credential | Provider failed closed | Pass |
| Restore the exact credential | Provider recovered and values remained unavailable | Pass |
| Kill provider with `SIGKILL` | Automatic recovery in 3 seconds | Pass |
| Stop provider with `SIGSTOP` | Unit stayed active indefinitely | Confirmed missing hang detection |
| Unresolvable VISS hostname | Provider stayed active and data remained unavailable | Fail-safe pass; policy still lacks DNS allow |
| Invalid VISS TLS server name | Provider stayed active and data remained unavailable | Fail-safe pass |

### Consolidated delta in enforcing mode

The final side-loaded candidate kept global SELinux `Enforcing`, had no
permissive domains, and ran with a read-only root filesystem.

| Gate | Result |
|---|---|
| Provider start with private systemd credential | Pass |
| Resolvable `wss://localhost` VISS hostname and live telemetry | Pass |
| KUKSA stop/start while provider remains active with the same PID | Pass |
| Automatic KUKSA reconnection and live-value recovery | Pass |
| Credential source snapshot while running | Pass |
| Invalid credential after restart | Fail closed |
| `SIGKILL` recovery | Pass in 4 seconds |
| Unresolvable VISS hostname | Fail-safe pass |
| Invalid VISS TLS server name | Fail-safe pass |

The enforcing test proves the three immediate changes as one system: direct
read-only systemd credential access, positive DNS resolution, and a soft KUKSA
dependency with automatic reconnect. It also confirms that provider credential
writes remain absent from the effective policy.

The running service receives a credential snapshot. Credential renewal must
therefore include an explicit provider restart after an atomic source update;
reload alone cannot activate a new token.

## Effective Resource Boundary

The current unit reports:

| Setting | Effective value |
|---|---:|
| `MemoryMax` | `infinity` |
| `CPUQuotaPerSecUSec` | `infinity` |
| `TasksMax` | `2230` |
| `LimitNOFILE` | `524288` |
| `WatchdogUSec` | `0` |

The qualification check proves normal resident memory remains below 256 MiB,
but this is an observation rather than an enforced bound. A hung or runaway
signed component can still remain `active` and consume unbounded CPU or
memory.

## Consolidated Change Boundaries

### Completed for the `.11` rootfs candidate

1. Allow read-only provider access to systemd credentials of type
   `initrc_runtime_t` inside the unit's private credential mount namespace.
2. Add the standard DNS client interface for root-owned VISS hostnames.
3. Add effective-policy preflight checks for credential directory/file reads,
   DNS client sockets, existing store isolation, and absence of capabilities.
4. Replace the hard KUKSA `Requires=` lifecycle coupling with a reviewed
   `Wants=` plus ordering model so a KUKSA restart does not permanently stop
   the FOTA-managed provider. Initial provider readiness must still fail closed
   until KUKSA TLS and authorization work.
5. Re-run only the targeted enforcing provider and dependency matrix against
   the side-loaded delta before one incremental rootfs build.

### Design before production release

1. Make the unavailable-before-switch operation synchronous. The current
   `SIGHUP` reload confirms signal delivery, not completion of the KUKSA
   update.
2. Define credential rotation as an atomic source replacement followed by an
   orchestrated provider restart and health confirmation.
3. Add watchdog signaling and bounded memory, CPU, task, and file-descriptor
   limits based on measured live headroom.
4. Add a rootfs/component compatibility gate so a rootfs FOTA cannot commit an
   ABI that cannot restart an already installed provider component.
5. Test update and rollback while KUKSA or the provider credential is already
   unavailable, and report a platform dependency failure separately from a
   candidate defect.

These production items are not hidden inside the immediate SELinux repair.
They require explicit lifecycle and compatibility decisions and, for watchdog
or reload acknowledgment, a new immutable provider release rather than a
silent modification of accepted provider `0.2.0` bytes.

## Next Review Gate

The consolidated delta and its production follow-ups are recorded. Platform
revision `a12c0aa` is pushed and pinned by exact manifest and graph digests.
One incremental `.11` image was built. Its clean disposable boot passed on
AArch64 with a read-only root, global SELinux `Enforcing`, the fixed-identity
unit contract, the soft KUKSA dependency, and direct effective-policy rules
for credentials, DNS, and `urandom`.

The rootfs-only FOTA target was then regenerated from the accepted `.11`
build. Boot and incremental-rootfs components remained disabled. The exact
unsigned candidate passed structure, path, secret-exclusion, publication,
size, and digest gates and was frozen with these values:

```text
configuration SHA-256: 9bceee031f31e3c0ec3afe2453c51213282d96ca2ed3b2139965038d4a4506b3
rootfs size: 128528384 bytes
rootfs SHA-256: e30406f600ada77568d21178e656a34f444973bf121f5a0b537e24efde8ab9d7
candidate metadata SHA-256: 56c109c30ab1111ba23dffe45634dbd556298f55da79782d867c3ac6be911aa6
signing state: unsigned
```

The next state-changing gate is explicit approval to use the OEM signing
identity for this exact candidate. Cloud upload, assignment, approval, and
provisioned-Unit mutation remain separate later gates. Neither signing nor
Cloud state was touched here.
