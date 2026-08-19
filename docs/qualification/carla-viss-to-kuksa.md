<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AOS-2 CARLA VISS-to-KUKSA Qualification

> This record describes the accepted AOS-2 side-loaded baseline. R6.1
> supersedes its packaging and runtime lifecycle with provider `0.2.0` and
> rootfs candidate `.11`; the telemetry contract and observed behavior remain
> the compatibility baseline.

## Result

R6/AOS-2 passed on 2026-08-14. This milestone did not rebuild the official
AosVM 6.1.0 base image. It installed a versioned platform package into the
provisioned VM's persistent overlay. A production vehicle program would place
the same provider, policy, and trust inputs into its OEM Yocto/FOTA image
build.

The accepted platform revision is
`d383be118b5fece6a5e1a700623bc1b69ab13937`. The reproducible generated bundle
is `carla-kuksa-provider-0.1.1-arm64.tar.gz` with SHA-256
`8d6b40b3854572cf1706cb43283916640c0ef6116307a805b63fe1323ab0e100`.
The integration baseline records both values and contract 0.1.1. The final
dependency lock uses Protocol Buffers 5.29.6, which fixes CVE-2026-0994; the
previously evaluated 5.29.5 wheel is excluded from the accepted bundle.

## Accepted architecture

```text
macOS host                                      provisioned AosVM Main Node

CARLA -> carla-ego-runtime -> VISS 3.1/TLS -> provider -> KUKSA 0.5.0
                                 127.0.0.1       DynamicUser  kuksa.val.v1
                                 port 6443       systemd      TLS + JWT
```

The provider initiates both connections and exposes no listener. QEMU makes
the host loopback service available to the guest at `10.0.0.1`, while TLS
verifies the certificate's `127.0.0.1` identity. The VISS listener remains
unavailable from the Mac's external interfaces.

The provider publishes only the seven paths in vehicle telemetry profile
0.1.1. Missing, invalid, stale, disconnected, startup, and shutdown states are
represented as KUKSA `NotAvailable`; zero is never a connectivity substitute.

## Credentials and trust

Run the ignored host helper from this repository:

```text
./scripts/host/aos2-kuksa-credentials prepare
./scripts/host/aos2-kuksa-credentials status
```

It keeps one RSA signing key under the ignored mode-0700 `.local` directory
and issues separate short-lived provider and read-only qualification tokens.
The token values are never printed. Only the public verification key and
provider token enter the VM. The provider receives its token through systemd
`LoadCredential`.

This issuance flow is intentionally temporary. The tokens expire after seven
days by default and can be renewed by repeating `prepare` and the guarded
installation. It is retained only to reproduce the historical qualification.
The accepted target in
[ADR 0010](../architecture/decisions/0010-aos-kuksa-credential-broker.md)
keeps upstream KUKSA unchanged and replaces manually issued service tokens
with a thin VDP-owned Credential Broker and short-lived JWTs derived from the
permissions currently registered by Service Manager in Aos IAM. The broker
stores no parallel identity or per-service policy. Its per-Unit signing key is
protected through the Aos IAM/certificate-module and PKCS#11 integration. The
provider replaces this static qualification token with a separately bound
short-lived platform credential; that exact FOTA-component identity mechanism
remains a design and qualification gate.

## Build and installation gates

Before installation:

1. run `./scripts/aosvm lifecycle-status` and require both protected
   checkpoints to verify;
2. run `scripts/guest/aosvm-aos2-readiness` inside the guest;
3. run `tests/guest/aosvm-aos2-vss-check` inside the guest;
4. build twice with
   `../aos-vehicle-platform/packaging/aosvm/build-provider-bundle` and require
   identical archive hashes;
5. import all five wheels in a temporary ARM64 guest virtual environment and
   run the bundled `verify-runtime.py`.

The guarded installer requires AArch64, a provisioned identity, an active
KUKSA Databroker, safe regular credential inputs, and a read-only root before
it changes anything. The versioned runtime and credentials live under
`/var/lib/aos-vehicle-platform`. Only the provider unit and KUKSA verifier
drop-in are installed into the root overlay, which is returned to read-only
mode before services start.

The normal rollback is the tracked platform `uninstall-provider` script. It
removes only those two systemd files, restores the image-default KUKSA
verifier, and preserves `/var` evidence. The verified post-provision checkpoint
is reserved for boot recovery. Never boot a restored copy while the active VM
with the same provisioned identity exists.

## Observed qualification

- All 12 platform unit/contract tests and the 39-file repository quality gate
  passed.
- All seven selected paths and their exact data types and units matched the
  embedded VSS 5.0 tree; steering uses the standard unit `degrees`.
- The ARM64 runtime imported from `kuksa-client` 0.5.0 and four exact runtime
  dependencies without a compiler or guest package-manager mutation.
- KUKSA loaded the project-owned public verifier, and a provider token with
  exactly seven `provide` scopes published an initial unavailable state.
- Live CARLA negotiated verified TLS and `VISSv3` from the guest.
- The read-only qualification client observed 41 atomic seven-path batches at
  20.16 Hz with source timestamps.
- Stopping CARLA immediately marked all seven KUKSA values unavailable; the
  reconnect delay remained bounded from 0.5 to 10 seconds.
- A clean VM stop/start preserved the package and credentials. KUKSA and the
  provider returned active and enabled with zero restarts.
- The root filesystem was read-only, SELinux was Enforcing without a
  provider-related denial, and the VISS listener was bound only to macOS
  `127.0.0.1:6443`.
- Runtime IAM, Service Manager, and Communication Manager remained active.
  AosCloud reported the provisioned Unit Online with exactly one primary
  `aos-vm-main` Node after the restart.
- Both protected lifecycle checkpoints and the destructive-reset lock remained
  valid. No credential, private key, certificate identity, VM disk, or raw log
  is tracked by Git.

The guest qualification readers are:

```text
tests/guest/aosvm-aos2-vss-check
tests/guest/aosvm-aos2-kuksa-read
```

The latter supports unavailable checks, live reads, and a native KUKSA
subscription rate gate with a separate read-only JWT.
