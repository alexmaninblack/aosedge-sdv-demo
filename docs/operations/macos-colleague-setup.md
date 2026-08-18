<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Run AosVM on an Apple Silicon Mac

This guide creates a new, independent AosVM 6.1.0 Main Node on an Apple
Silicon Mac. It uses QEMU with Apple's Hypervisor Framework, not VirtualBox.
The result has its own persistent disk and, if provisioned, its own cloud Unit
identity.

Do not copy another person's VM overlay, checkpoints, SSH access directory, or
provisioning state. A provisioned disk contains a unique Unit identity and must
never be cloned while the original Unit exists.

## What the helper does

The workflow deliberately separates three levels of change:

| Command | Local changes | Cloud changes |
| --- | --- | --- |
| `doctor` | None; read-only checks | None |
| `bootstrap` | Installs missing Homebrew packages and an isolated Aos CLI environment | None |
| `setup` | Downloads the pinned official image, creates a private persistent disk, boots it, and applies the two tracked macOS/ARM64 compatibility updates | None |
| `provision-preflight` | Read-only certificate, VM, and Target System checks | Read-only API calls |
| `provision --confirm` | Creates a protected checkpoint and installs the new Unit credentials into this VM | Registers one new Main Node Unit |

`setup` is safe to repeat after an interrupted download or boot. It reuses and
verifies existing files instead of replacing the VM disk. `provision` is never
started implicitly and is never retried automatically after the official SDK
begins.

## Prerequisites

- an Apple Silicon Mac running macOS;
- at least 4 GiB of memory and 20 GiB of free disk space;
- Internet access to GitHub, Homebrew, the AosEdge documentation, and the
  cloud domain encoded in the certificate;
- a working OEM PKCS#12 certificate, normally at
  `~/.aos/security/aos-user-oem.p12`;
- an existing `aos-vm` version `1.0.0` Target System in that OEM with exactly
  one `aos-vm-main` Node configuration.

Admin and Service Provider certificates are not needed to boot or provision
this VM. Certificate recovery and one-time tokens are outside this guide.

## Step 1: Install Homebrew if needed

Open Terminal and check:

```sh
command -v brew
```

If it prints no path, install Homebrew from its official site:
[brew.sh](https://brew.sh/). Complete its instruction for adding
`/opt/homebrew/bin` to the shell path, close Terminal, and open it again.

The onboarding helper intentionally does not execute the remote Homebrew
installer itself because that installer may request administrator approval.

## Step 2: Clone the integration repository

Choose a private working directory and clone the current onboarding branch:

```sh
mkdir -p "$HOME/Projects"
cd "$HOME/Projects"
git clone --branch feature/r6-1-fota-runtime \
  https://github.com/alexmaninblack/aosedge-sdv-demo.git
cd aosedge-sdv-demo
```

Use this branch until the current integration baseline is merged to `main`.

Do not place a `.p12` file in the repository. The repository ignores common
key formats, but the correct location is still `~/.aos/security`.

## Step 3: Run the read-only doctor

```sh
./scripts/aosvm-macos-onboard doctor
```

The report uses three classifications:

- `OK` — the check passed;
- `MISSING` — resolve this item before provisioning;
- `NOTE` — information that does not block local VM use.

It is normal for QEMU, Python, and the Aos CLI to be missing before the next
step. `doctor` does not download, install, start, or provision anything.

## Step 4: Install local tools

```sh
./scripts/aosvm-macos-onboard bootstrap
```

The command:

1. installs missing `qemu`, `jq`, and `python@3.12` Homebrew packages;
2. requires native Apple Silicon Homebrew at `/opt/homebrew`;
3. accepts only QEMU versions qualified by this repository;
4. creates the isolated Aos CLI environment under `~/.aos/venv`;
5. does not issue, replace, import, or upload certificates.

QEMU 11.0.3 and 11.1.0 are currently qualified with the fixed
`virt-11.0,accel=hvf` machine contract. A later Homebrew QEMU is rejected until
it is tested, rather than being used silently.

If Homebrew or the Python package index is temporarily unavailable, rerun the
same command. Existing successful work is preserved.

## Step 5: Create and run the local VM

```sh
./scripts/aosvm-macos-onboard setup
```

The first run downloads about 364 MiB and verifies the exact size and SHA-256
of the official AosVM archive. It then creates a sparse private qcow2 overlay;
the guest disk has an approximately 6.52 GiB virtual size and grows as needed.
The repository requires at least 20 GiB of host free space for safe operation
and later checkpoints.

The first guest boot can take roughly one minute because the official image may
perform a one-time SELinux relabel and reboot. The helper waits for the real SSH
banner, verifies the SSH host key, creates a private per-VM Ed25519 access key,
and uses the official development-image password only once to install that
key. This public development credential is built into the helper; it is not
passed on a command line, copied into a log, or entered into shell history.

The helper then applies two idempotent changes to the writable overlay:

- select the ARM64 `bootaa64.efi` Service Manager loader;
- route the guest's dnsmasq through the loopback-only macOS DNS bridge.

It performs one clean restart and leaves the VM running and unprovisioned. No
cloud API mutation occurs.

## Step 6: Check or operate the local VM

```sh
./scripts/aosvm-macos-onboard status
./scripts/aosvm-macos-onboard stop
./scripts/aosvm-macos-onboard start
./scripts/aosvm dns-check
```

`start` and `stop` are idempotent. The VM disk persists across both commands.
The DNS bridge automatically follows the active macOS resolver set after Mac
sleep or a Wi-Fi/network change. `dns-check` makes a bounded query through the
same bridge used by the VM and is safe to repeat; a successful result means no
VM restart is required.
Normal mode exposes only these host-loopback services:

- `127.0.0.1:10022` — guest SSH;
- `127.0.0.1:18053` — private DNS bridge.

Nothing is exposed on the Mac's LAN address, and the cloud provisioning port
is absent in normal mode.

At this point the colleague has a working local AosVM. Stop here if cloud
registration is not required.

## Step 7: Verify readiness for cloud provisioning

First confirm that the existing OEM certificate file is present:

```sh
ls -l "$HOME/.aos/security/aos-user-oem.p12"
```

Then run the read-only preflight:

```sh
./scripts/aosvm-macos-onboard start
./scripts/aosvm-macos-onboard provision-preflight
```

The preflight extracts the cloud domain from the certificate instead of
hard-coding it. It verifies the local certificate, performs a live OEM role
check, and reads the exact `aos-vm` `1.0.0` Target System. It stops if the
Target System is missing, duplicated, or does not exactly contain this
configuration:

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

The preflight does not create or modify a Target System. That is deliberate:
choosing or creating a cloud model is an OEM ownership decision and should not
be guessed by a laptop setup script.

## Step 8: Provision one Main Node

Provisioning creates a cloud Unit and persistent credentials inside this VM.
Run it only after the preflight passes:

```sh
./scripts/aosvm-macos-onboard provision --confirm
```

The helper performs these guarded operations:

1. proves the guest is still unprovisioned;
2. stops it cleanly and creates an independent pre-provision checkpoint under
   `~/Library/Application Support/CarlaAosEdge/AosVM/backups`;
3. permanently locks destructive overlay reset for this identity;
4. starts a provisioning-only listener at `127.0.0.1:18089`;
5. invokes the official SDK exactly once with `--nodes 1`;
6. checks the provisioned guest services, restarts in normal mode, and checks
   them again;
7. stops the VM and creates a post-provision checkpoint.

Raw provisioning output may contain Unit and Node identifiers. It is stored as
a mode-0600 private log under
`~/Library/Application Support/CarlaAosEdge/AosVM/provisioning`, outside Git.

After success, start the persistent Unit normally:

```sh
./scripts/aosvm-macos-onboard start
```

## Failure and recovery guide

| Symptom | Safe response |
| --- | --- |
| Homebrew is missing | Install only from [brew.sh](https://brew.sh/) and rerun `bootstrap`. |
| Download is interrupted | Rerun `setup`; the pinned archive download resumes and is reverified. |
| Port `10022`, `18053`, or `18089` is busy | Stop the conflicting local process or configure distinct high loopback ports; do not expose the VM on a LAN address. |
| QEMU version is rejected | Do not bypass the version check. Use a repository revision that qualifies that QEMU release or qualify it on a disposable disk first. |
| SSH host key changed | Stop. Confirm that the same overlay is being used. Never delete the saved host key merely to silence the warning. |
| `setup` is interrupted | Rerun `setup`; image preparation, compatibility updates, and key enrollment are idempotent. |
| Unit stays offline after Mac sleep or a network change | Run `./scripts/aosvm dns-check` and allow a few seconds for the network transition. The bridge refreshes macOS resolvers automatically. If the check still fails after the Mac itself can resolve Internet names, preserve `runs/aosvm-main-dns.log` for diagnosis before using a clean `stop`/`start` as a fallback. |
| OEM certificate is missing or expired | Restore or reissue it through the AosEdge account process; do not copy another person's certificate. |
| Live OEM check fails | Confirm network reachability, certificate validity, certificate chain, and the domain encoded in the certificate. Do not hard-code another cloud domain. |
| Target System check fails | Ask the OEM owner to create or reconcile the exact single-Node model. The helper changes nothing. |
| Provisioning fails before or after registration | Do not reset the disk and do not rerun provisioning. Preserve the VM and review the private log and cloud Unit state first. |
| Provisioned VM is lost | Restore only through a coordinated cloud/local recovery. Never boot the active Unit and a restored checkpoint simultaneously. |

When asking another person for help, share only the failing step, sanitized
error category, tool versions, and whether the VM is local-only or provisioned.
Do not share `.p12` files, private keys, one-time tokens, raw provisioning logs,
Unit links, Unit IDs, Node IDs, or checkpoint disks.

## Where local data lives

| Data | Default location | Git status |
| --- | --- | --- |
| Official archive and immutable images | `.cache/aosvm/` | Ignored |
| Active persistent VM overlay | `.local/` | Ignored |
| Per-VM SSH key and known host | `.local/host-access/` | Ignored |
| Runtime sockets and private logs | `.run/`, `runs/` | Ignored |
| Aos user tools and certificates | `~/.aos/` | Outside repository |
| Protected VM checkpoints | `~/Library/Application Support/CarlaAosEdge/AosVM/backups/` | Outside repository |
| Private provisioning attempt log | `~/Library/Application Support/CarlaAosEdge/AosVM/provisioning/` | Outside repository |

Use FileVault or equivalent host encryption for the Mac. Both a provisioned
VM overlay and its checkpoint contain persistent Unit credentials.

## Official references

- [AosEdge: provision a device](https://docs.aosedge.tech/docs/how-to/tutorials/device/provision-device/)
- [AosEdge: single-Node AosVM provisioning](https://docs.aosedge.tech/docs/how-to/register-your-device/with-your-HPC-device)
- [AosEdge: access a Unit over SSH](https://docs.aosedge.tech/docs/how-to/tutorials/device/access-unit/)
- [AosCloud API v11](https://api.aoscloud.io/api/v11/docs#/)
- [Homebrew QEMU formula](https://formulae.brew.sh/formula/qemu)
