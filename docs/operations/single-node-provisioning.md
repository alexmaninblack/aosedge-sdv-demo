<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AOS-1: Register and Provision One Main Node

## Objective

Register the qualified AosVM `v6.1.0` ARM64 Main Node as a single-Node Unit in
hosted AosCloud, install its Unit credentials through the official AosEdge SDK,
prove that IAM, Service Manager, and Communication Manager become healthy, and
then deploy the official Hello World service.

The VM continues to run under the repository-owned QEMU/HVF lifecycle. The SDK
owns account authentication, key generation, certificate issuance, cloud
registration, and the provisioning protocol. This repository owns only
non-secret configuration, loopback transport, safety gates, and sanitized
acceptance evidence.

## Current status

| Phase | Status | Exit condition |
| --- | --- | --- |
| AOS-1.1: account and roles | Complete - 2026-08-13 | OEM and SP cloud access confirmed |
| AOS-1.2: CLI environment | Complete - 2026-08-13 | Exact tool versions and single-Node CLI contract verified |
| AOS-1.3: provisioning certificate | Complete - 2026-08-13 | Existing OEM certificate and API check pass |
| AOS-1.4: single-Node cloud model | Complete - 2026-08-13 | Target System matches the Main Node only |
| AOS-1.5: provisioning transport | Complete - 2026-08-13 | Guest IAM was reachable only on host loopback |
| AOS-1.6: persistent lifecycle and recovery checkpoint | Complete - 2026-08-13 | Reset lock and independent pre-provision checkpoint pass |
| AOS-1.7: SDK provisioning | Complete - 2026-08-13 | `aos-prov` completed once for exactly one Node |
| AOS-1.8: post-provision acceptance | Complete - 2026-08-13 | Local core, identity continuity, and cloud Unit gates pass |
| AOS-1.9: Hello World | Complete - 2026-08-14 | Official service reaches `Active` |

The existing AosEdge account and OEM client certificate work on this Mac. A
single-Node `aos-vm` version `1.0.0` Target System exists
in the authenticated OEM and its API read-back exactly matches the tracked
configuration. The SDK provisioned the Main Node with protocol v6 and
`--nodes 1` on the first and only attempt. AosCloud now reports one online,
provisioned Unit containing one provisioned `aos-vm-main` Node. Two normal-mode
starts preserved the Unit, Node, and certificate identity, exposed no
provisioning port, and passed the local core and network acceptance gates. The
VM is running in normal mode with verified pre- and post-provision checkpoints
and lifecycle state `provisioned`. The official Hello World service is
installed as one active ARM64 workload, its cloud log and lifecycle checks
pass, and AOS-1 is complete.

## Fixed decisions

- Use hosted `aoscloud.io` for the first integration.
- Provision one `aos-vm-main` Node; do not start the Secondary image.
- Use `aos-prov provision --nodes 1`, not the VirtualBox-owning `unit-new`
  command.
- Keep the normal SSH and DNS forwards loopback-only.
- Add guest IAM port `8089` only in an explicit provisioning launch mode and
  forward it to `127.0.0.1:18089` by default.
- Remove the provisioning forward from every normal post-provision launch.
- Keep all user and Unit private material outside Git.
- Do not reset a partially or fully provisioned overlay until cloud identity
  and local identity have been reconciled.
- Treat the active overlay as the permanent disk of the cloud Unit from the
  first provisioning attempt onward. It is not disposable after AOS-1.6.
- Never run the active disk and a restored checkpoint at the same time. They
  would carry the same Unit identity.
- Keep this development Unit in a Verification Set only after explicit user
  approval. Membership bypasses additional OEM approval for future SOTA/FOTA
  until the Unit is removed from that set.

## Credential and evidence boundary

The following data must never enter this repository, an issue, a commit, a
terminal transcript attached to the repository, or this chat:

- welcome-email user tokens;
- OEM or SP `.p12` files and their passwords;
- private keys, CSRs containing private metadata, or SDK secure state;
- Unit certificate/key material and PKCS#11 PINs;
- raw provisioning output containing a Unit ID, Node ID, cloud link, subject,
  or account-specific endpoint;
- screenshots that expose tokens, certificate selectors, account names, or
  identifiers.

The official tools store user material under `~/.aos/security` and their
isolated Python environment under `~/.aos/venv`. These locations are outside
the repository. Unit keys are generated and retained through the guest's
PKCS#11-backed provisioning flow. Tracked evidence contains only versions,
pass/fail classifications, generic topology, and sanitized timings.

Certificate issuance and recovery remain separate account-administration
workflows. This repository neither documents token-bearing commands nor
implements certificate replacement.

## Phase AOS-1.1: Create and verify the account

1. First check whether the user already has working OEM and SP access to
   `https://aoscloud.io/`; do not create a duplicate organization or account.
2. If access does not exist, select **Sign Up** and complete email verification.
3. Confirm that both role contexts and their onboarding messages exist:
   - OEM — manages Target Systems, Units, provisioning, and Unit operation;
   - SP — registers, signs, uploads, and publishes services.
4. Keep both token-bearing emails private.
5. Do not add other users or Fleet Owner roles for the first demonstration.

Only the OEM identity is required through Phase AOS-1.8. The SP identity is
prepared now because it is required by the Hello World and telemetry-service
packaging flows.

**Pass:** OEM and SP onboarding messages exist and the user can reach the
certificate-authentication sign-in page.

**Stop:** the emails belong to different organizations, an invitation is
expired, the expected roles are missing, or the account uses a non-production
domain that has not been selected explicitly.

## Phase AOS-1.2: Install the CLI in an isolated environment

Follow the official macOS layout rather than installing packages into the
system Python. The checked-in helper implements these steps and enforces
Python 3.10 or later, which is required by `aos-keys` 1.10.0:

```sh
brew install python@3.12
./scripts/aos-user-setup bootstrap
```

Before using credentials:

1. verify that the selected Python is 3.9 or later;
2. record the exact Python, `aos-keys`, `aos-signer`, and `aos-prov` versions in
   ignored local evidence;
3. inspect `aos-prov provision --help` and confirm that it accepts an
   `IP_ADDRESS:PORT` Unit endpoint and `--nodes`;
4. confirm that no package was installed inside the repository;
5. run the version and import checks without an account token.

The official macOS CLI page currently lists macOS 13, 14, and 15. This host
runs macOS 26.5.2, so the no-credential version, import, help, TLS, and Keychain
smoke checks are mandatory even though the tools are pure Python and expected
to work. Do not treat an unlisted host version as a failure by itself, but do
not proceed past an observed compatibility failure.

The clean-machine qualification installed native ARM64 Python 3.12.14,
`aos-keys` 1.10.0, `aos-signer` 2.0.1, and `aos-prov` 5.4.2 in
`~/.aos/venv`. Package dependency checks, an in-memory RSA/CSR smoke test, and
the complete `aos_prov provision --help` import path pass on macOS 26.5.2.
That host version is outside the official macOS 13/14/15 test matrix and is
qualified here for this project rather than claimed as vendor-supported.
The installed provisioning command accepts `IP_ADDRESS:PORT` and `--nodes`.
Its default is two Nodes, so AOS-1.7 must supply `--nodes 1` explicitly. The
private root, venv, and empty security directory are mode `0700`; no credential
was used or generated during qualification.

**Pass:** the isolated tools run on macOS and the exact versions and CLI
contract are known.

**Stop:** the tool has no single-Node option, requires VirtualBox for the
generic `provision` command, cannot use an explicit port, or is incompatible
with the provisioning protocol reported by the guest.

## Phase AOS-1.3: Verify the Existing OEM Certificate

Certificate issuance, renewal, recovery, root-trust installation, and
one-time-token handling are account-administration workflows outside this
repository. The provisioning workflow assumes that the user already has a
valid OEM PKCS#12 file outside Git, normally at:

```text
~/.aos/security/aos-user-oem.p12
```

Run the guarded local and live role check:

```sh
./scripts/aos-user-setup verify-oem
```

The helper validates the certificate locally and performs a read-only mTLS
Cloud access check. It does not request a token, issue or replace a
certificate, import browser credentials, or mutate AosCloud. Browser sign-in
is optional for visual inspection and is not an execution dependency.

**Pass:** the OEM certificate is valid, the read-only role check succeeds, and
the file remains outside the repository.

**Stop:** the certificate is absent, expired, has the wrong role, fails mTLS,
or any private material appears under the repository.

## Phase AOS-1.4: Define the single-Node cloud model

Before changing AosCloud, verify the unprovisioned guest reports the expected
model and Node type:

```text
Unit model: aos-vm;1.0.0
Node type: aos-vm-main
Node attribute: MainNode
Aos components: cm,iam,sm
```

Use the OEM API to inspect whether `aos-vm` version `1.0.0` already exists. Do
not overwrite an existing two-Node configuration used by another Unit.

For a new Target System, use:

- name: `aos-vm`;
- version: `1.0.0`;
- Unit Configuration: the exact tracked
  `config/aosvm-single-node-unitconfig.json` content.

That configuration declares only:

```json
{
  "nodes": [
    {
      "nodeType": "aos-vm-main",
      "labels": ["main"],
      "priority": 100
    }
  ]
}
```

**Pass:** the cloud model/version and the guest model/version match exactly,
and the Unit Configuration contains one Main Node type and no Secondary type.

**Stop:** the model is already associated with an incompatible or in-use
topology, the guest reports another model/type, or cloud validation adds a
second required Node. Resolve model ownership before provisioning; do not
silently patch `/etc/aos/unit_model`.

**Observed:** the initial exact-name/version API lookup returned no match. The
new Unit Model was created once and read back through the OEM API. Its name is
`aos-vm`, version is `1.0.0`, and Unit Configuration contains exactly one
`aos-vm-main` entry. The official release image and its `/etc/aos` model data
were not changed. The installed `aos-prov` obtains model and Node information
from guest IAM and `--nodes 1` prevents waiting for a Secondary.

## Phase AOS-1.5: Add an explicit provisioning transport

`scripts/aosvm` provides an opt-in `start-provisioning` mode. The accepted
network difference is one additional QEMU user-network rule:

```text
127.0.0.1:18089 -> 10.0.0.100:8089/tcp
```

Implementation requirements:

- normal `start` must not expose guest port `8089`;
- provisioning mode must require an explicit flag or subcommand;
- the host port must be configurable but validated as unprivileged and bound
  only to `127.0.0.1`;
- host qualification must reject an occupied or ambiguous port;
- status and smoke output must distinguish normal and provisioning modes;
- lifecycle ownership checks must include the exact forward;
- tests must reject `0.0.0.0`, wildcard, LAN, or implicit provisioning
  listeners;
- stop must remove the forward together with the owned QEMU process;
- no credential may be accepted by the launcher.

The real provisioning start is additionally gated on lifecycle state
`provisioning-locked`; its dry run remains available before the checkpoint.
`tests/host/aosvm-start-dry-run-test` proves the command contract and
`tests/host/aosvm-provisioning-host-gate` proves the live loopback boundary.

The generic provisioning flow does not require the cloud to connect inbound to
the Mac. `aos-prov` connects locally to the loopback forward and separately to
AosCloud; the guest Communication Manager later establishes its own outbound
cloud connection.

**Pass:** provisioning IAM is reachable from the Mac only through
`127.0.0.1:18089`, normal mode has no port `18089` listener, and all existing
AOS-0 exposure and ownership gates continue to pass.

**Stop:** provisioning requires a LAN/global listener, administrator-owned
bridge or packet-filter change, or an unowned forwarding process.

**Observed:** the live host gate proved that QEMU owned the only listener on
`127.0.0.1:18089` and that it was not reachable through a Mac LAN address. IAM
responded with provisioning protocol v6, model `aos-vm;1.0.0`, and exactly one
Node marked Main with type `aos-vm-main`. Normal mode had no port `18089`
listener before or after provisioning.

## Phase AOS-1.6: Lock the persistent lifecycle and create a checkpoint

Provisioning changes both the guest overlay and cloud state. A disk copy alone
is therefore not a complete rollback.

Immediately before provisioning:

1. stop the VM and pass the complete stopped-state gate;
2. verify immutable input hashes and qcow2 integrity;
3. confirm the overlay has the accepted ARM64 and DNS compatibility state;
4. run `scripts/aosvm checkpoint-pre-provision` while QEMU is stopped;
5. confirm that it creates a mode-0600, standalone pre-provision qcow2
   checkpoint with no backing file, records its SHA-256 in mode-0600 lifecycle
   metadata, writes a matching mode-0600 guard beside the active overlay, and
   changes the local lifecycle to `provisioning-locked`;
6. run `scripts/aosvm lifecycle-status` and verify the complete checkpoint;
7. prove that `reset-overlay --confirm` is rejected after the lock;
8. start provisioning mode and rerun the smoke and exposure gates;
9. confirm provisioning IAM is active and the runtime IAM/SM/CM units remain
   correctly condition-gated;
10. confirm time, DNS, and verified HTTPS are healthy.

By default the checkpoint and lifecycle metadata live outside the checkout at
`~/Library/Application Support/CarlaAosEdge/AosVM/backups`. An explicit
absolute `AOSVM_BACKUP_ROOT` may select a different private directory. The
directory and metadata are mode `0700` and `0600`; neither is tracked by Git.
The second, non-secret reset guard lives beside the ignored active overlay.
The launcher requires both copies to match and fails safe if either side is
missing or inconsistent.
The standalone checkpoint remains usable if the repository is moved or
deleted. Its storage must be covered by FileVault or equivalent host
encryption because it contains a complete copy of the guest disk.

The checkpoint is evidence and a local recovery aid. It must not be restored
after cloud registration unless the Unit has first been removed or
deprovisioned through an agreed cloud/local reconciliation procedure. Restoring
it blindly could clone or reuse a cloud identity.

**Pass:** one exact pre-provision state is identifiable, healthy, independent
of the checkout, and recoverable without touching the immutable base; the
active overlay cannot be reset through the normal lifecycle command.

**Stop:** the VM is running during the copy, the overlay is inconsistent, the
checkpoint is inside Git or on unencrypted storage, the reset lock does not
hold, or rollback ownership is unclear.

**Observed:** the stopped-state gate passed immediately before the checkpoint.
The standalone pre-provision qcow2 and its SHA-256 metadata were created under
the private host backup root, lifecycle moved to `provisioning-locked`, and an
explicit destructive reset attempt was rejected. The checkpoint remained
verified through provisioning and every subsequent stop.

## Phase AOS-1.7: Provision exactly one Node

With the OEM certificate verified and the provisioning-only listener active,
run the generic SDK command from a personal terminal:

```sh
~/.aos/venv/bin/python3 -m aos_prov provision \
  -u 127.0.0.1:18089 \
  --nodes 1
```

Before confirming execution, independently verify:

- endpoint `127.0.0.1:18089` belongs to the owned Main VM;
- the guest is still `unprovisioned`;
- the tool selected the OEM certificate;
- the cloud Target System contains exactly one `aos-vm-main` entry;
- no second VM or `unit-new` command is involved.

During execution, observe but do not commit:

- provisioning protocol negotiation;
- exactly one Node ID discovered and identified as Main;
- certificate types requested for that Main Node;
- successful Unit registration and certificate application;
- successful finish-provisioning response.

Do not retry automatically after a failure that occurs after Unit registration.
Preserve the overlay, local tool state, and cloud Unit state; classify the last
completed step first. Never place the returned Unit link or identifiers in
tracked evidence.

**Pass:** `aos-prov` reports successful completion for one Main Node and the
Unit becomes visible to the OEM account.

**Stop:** the tool waits for a Secondary, discovers more than one Node,
registers the wrong model/type, fails after cloud registration, or asks to
replace an existing Unit identity.

**Observed:** all read-only preflight gates passed immediately before the
attempt: OEM mTLS access, supported `aos-prov` version, exact cloud Unit Model
detail, protocol v6, one Main Node, verified checkpoint, and no existing cloud
Unit for the VM identity. The official SDK command ran exactly once with
`--nodes 1`, reached cloud registration, applied the Unit credentials, finished
provisioning, and returned success. Its raw output is mode `0600` outside the
repository; tracked evidence contains no Unit, Node, account, or certificate
identifier.

## Phase AOS-1.8: Accept the provisioned Main Node

After SDK completion, allow the image's provisioning-finish actions and any
expected reboot to complete. Then verify locally:

- `/var/aos/.provisionstate` exists and reports the provisioned state;
- provisioning IAM is inactive;
- runtime IAM, SM, and CM are active with stable restart counts;
- `/dev/sda6` and the expected Aos data paths are initialized and mounted;
- the previously classified NFS dependency failure is resolved;
- IAM, SM, and CM certificates are available through their configured secure
  storage without exporting private keys;
- CM establishes verified outbound cloud communication;
- Service Manager still selects `crun` and reports no runtime crash;
- SELinux remains enforcing with no unexplained denial;
- DNS, time synchronization, and verified HTTPS still pass.

Verify in AosCloud:

- one Unit exists for this system identity;
- it is online;
- it contains exactly one Node;
- the Node type is `aos-vm-main` and its label is `main`;
- no missing/offline Secondary is shown;
- monitoring data arrives.

Finally, cleanly stop the provisioning-mode VM and start it in normal mode.
Prove that ports `18089` and guest IAM `8089` are no longer exposed through the
host while SSH and DNS retain their accepted loopback scope. Repeat a clean
restart and the local/cloud health checks. Across both starts, verify that the
System ID, Node ID, Unit certificate public fingerprints, and cloud Unit are
unchanged; never export or record private key material.

After those identity-continuity and cloud-online gates pass, stop the VM and
run `scripts/aosvm seal-provisioned`. This creates a standalone, mode-0600
post-provision checkpoint, records its SHA-256, and moves the lifecycle from
`provisioning-locked` to `provisioned`. Run `scripts/aosvm lifecycle-status`
to verify both checkpoints. Keep only the active VM runnable. A checkpoint is
for disaster recovery and must never be booted while the original Unit exists.

The overlay, checkpoints, and lifecycle metadata are not Git artifacts. A new
clone reproduces the launcher but not the Unit. Backup retention, restore,
repository relocation, deprovisioning, and factory reset are controlled
operations that must reconcile the local identity with AosCloud before any
disk replacement. The current lifecycle intentionally provides no command to
remove this protection.

**Pass:** one Main Node remains online and healthy after a normal restart, all
local core services are explained, and the provisioning listener is absent.

**Stop:** cloud expects a Secondary, CM cannot connect, storage initialization
is incomplete, core services crash, the Unit duplicates an identity, or port
`18089` survives normal launch.

**Observed:** the provision marker is present; runtime IAM, Service Manager,
Communication Manager, and NFS are active; provisioning IAM and its firewall
unit are inactive. All three AosCore processes reported zero restarts. The
four encrypted Aos data filesystems are mounted read-write, SELinux is
enforcing, DNS and synchronized time pass, and verified TLS and HTTPS succeed.
AosCloud reports exactly one online, provisioned Unit with exactly one
provisioned `aos-vm-main` Node, and its monitoring endpoint returns data.

Two normal-mode starts exposed no provisioning listener and preserved private
hashes of the System, Unit, Node, and five cloud certificate records. Both
accepted cycles ended in a QMP/ACPI guest shutdown and a clean qcow2 gate. The
post-provision standalone checkpoint was then created, both checkpoints were
reverified, lifecycle moved to `provisioned`, and destructive reset remained
locked.

One non-blocking upstream image issue remains classified. On a provisioned
boot, the generic `quotaon.service` runs `quotaon -aug` after the `states` and
`storages` filesystems have already enabled user and group quotas while
mounting. The redundant command returns `EEXIST`/status 4, so systemd records
that helper as failed even though both filesystems are mounted, user and group
quotas report `on`, and IAM, SM, CM, NFS, storage, and cloud connectivity are
healthy. The release image was not modified to mask this diagnostic; it should
be handled as a separate upstream unit-ordering/idempotency issue.

## Phase AOS-1.9: Deploy the official Hello World service

Use the SP certificate and official AosEdge service tooling to register, sign,
and upload the sample. Use the OEM role to approve/bind it to the single Unit as
required by the platform flow. Do not reuse the telemetry service name or
package yet.

Verify that the service:

- is scheduled to the only `aos-vm-main` Node;
- reaches `Active` state;
- runs as an ARM64 OCI workload through Service Manager and `crun`;
- produces the expected bounded English log output;
- can be stopped, restarted, and removed through AosCloud;
- leaves the Unit and core services healthy.

**Pass:** the official sample reaches `Active`, its expected log is visible,
and a cloud-driven restart succeeds.

**Stop:** package architecture is incompatible, scheduling expects a missing
Node type, the runtime violates declared resource boundaries, or deployment
destabilizes AosCore.

**Observed:** the upstream `AosEdge/hello-world` sample was pinned at commit
`eb5f95f92aa5b6744295d977de13668aa77133f2`. Its schema-v2 configuration
validated, signed, and uploaded with `aos-signer` 2.0.1. The ephemeral build
workspace retained the official package structure and service configuration,
but replaced the sample's public webhook call with one bounded local English
log line. This avoided sending test data or identifiers to an unrelated
external receiver. Neither the sample workspace nor its deployment bundle is
tracked here.

The SP verification batch became `Valid` for `arm64`. A dedicated
`AOS-1.9 Hello World` Subject binds exactly one service to the single Unit.
The account's OEM role cannot approve fleet-validation batches, so the user
explicitly authorized an `AOS-1.9 Verification` Unit Set containing only this
development Unit. Membership is intentionally persistent: future SOTA/FOTA
assigned to this Unit bypass additional OEM approval until it is removed from
the Verification Set.

AosCloud selected version `1.0.0`; Service Manager installed it on the only
`aos-vm-main` Node and started a `crun` container on AArch64. The instance
reached `Active` without an error or resource conflict. A bounded cloud log
request completed and returned both accepted `Hello world!` records. Removing
the Subject-service assignment drove the real instance to `inactive` and
removed its process and network state. Restoring the assignment created a new
`crun` container and returned it to `Active` with a new English log record.

After the lifecycle test, IAM, SM, and CM remained active. The post-provision
guest gate, complete layered network/TLS gate, loopback-only host exposure
gate, cloud monitoring endpoint, one-Main-Node topology, both checkpoint
verifications, and the destructive-reset lock all passed. No private material,
cloud identifier, bundle, or downloaded log is retained in Git.

## AOS-1 acceptance checklist

- [x] OEM and SP account roles are confirmed.
- [x] Exact isolated CLI versions are recorded locally.
- [x] The existing OEM certificate and live provisioning-role check pass.
- [x] No token, private key, certificate, or account identifier is tracked.
- [x] The cloud Target System contains only `aos-vm-main`.
- [x] Normal QEMU mode does not expose provisioning IAM.
- [x] Provisioning mode binds IAM only to `127.0.0.1`.
- [x] A consistent ignored pre-provision checkpoint exists.
- [x] Lifecycle was `provisioning-locked` and overlay reset was rejected before provisioning.
- [x] `aos-prov provision --nodes 1` completed for exactly one Main Node.
- [x] IAM, SM, CM, storage, NFS, SELinux, time, DNS, and HTTPS gates pass.
- [x] AosCloud reports one online Main Node and no missing Secondary.
- [x] Normal restart removes the provisioning listener and preserves health.
- [x] System, Node, certificate, and cloud Unit identity remain identical across two accepted normal starts.
- [x] A verified standalone post-provision checkpoint exists and lifecycle is `provisioned`.
- [x] The active Unit and a restored checkpoint were never run concurrently.
- [x] The official Hello World service reaches `Active` and restarts cleanly.
- [x] Sanitized AOS-1 evidence is committed and the working tree is clean.

## Failure routing

| Failure | Preserve | Next decision |
| --- | --- | --- |
| Account or role mismatch | Welcome emails without sharing tokens | Resolve with AosEdge account support |
| CLI contract changed | Version and help text, sanitized | Pin a compatible official release or update the plan |
| OEM certificate check fails | Local tool error only | Reissue locally; do not expose the token or `.p12` |
| Target System already uses two Nodes | Existing cloud configuration | Do not overwrite; resolve model/version ownership |
| Loopback IAM is unreachable | QEMU command, listener scope, guest service state | Fix transport before invoking `aos-prov` |
| Failure before cloud registration | Overlay and local SDK state | Diagnose and retry only after the state is understood |
| Failure after cloud registration | Overlay, cloud Unit, local SDK secure state | No reset; reconcile cloud and guest identity first |
| Unit online but core unhealthy | Sanitized service/storage classifications | Block Hello World until the local defect is resolved |
| Cloud shows a missing Secondary | Target System and Unit Configuration | Correct topology before deploying a service |
| `quotaon.service` reports `EEXIST` while quotas are already on | Mount options, `quotaon -p`, and sanitized unit status | Track the upstream idempotency defect; block only if quotas or Aos data paths are not operational |
| Hello World cannot schedule | Service architecture and Node selector | Fix the sample package/placement, not the VM identity |

## Official references

- [Create the first AosEdge account](https://docs.aosedge.tech/docs/how-to/register-your-users/create-first-account)
- [Install Aos tools on macOS](https://docs.aosedge.tech/docs/how-to/aos-tools/install/macos)
- [Get AosCloud access](https://docs.aosedge.tech/docs/quick-start/get-access)
- [Provision a device](https://docs.aosedge.tech/docs/how-to/tutorials/device/provision-device)
- [Single-Node provisioning guidance](https://docs.aosedge.tech/docs/how-to/register-your-device/with-your-HPC-device)
- [Unit Configuration reference](https://docs.aosedge.tech/docs/v1/reference/core-component-configs/unit-config)
- [Deploy a generic service](https://docs.aosedge.tech/docs/how-to/run-your-application/run-qm-service)
- [Create the official Hello World service](https://docs.aosedge.tech/docs/quick-start/create-service)
- [Install a service through a Subject](https://docs.aosedge.tech/docs/quick-start/create-subject)
- [Use a Verification Set](https://docs.aosedge.tech/docs/how-to/updates-and-campaigns/test-before-release)
