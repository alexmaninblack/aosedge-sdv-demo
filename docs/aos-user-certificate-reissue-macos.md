# AosEdge user certificate reissue on a new Mac

## What the reissue email assumes

The certificate-reissue email contains three role-specific `aos-keys new-user`
commands for macOS:

- the personal Admin account uses `--admin`;
- `aa_oem` uses `--oem`;
- `aa_serviceproducer` uses `--sp`.

Each command embeds a different one-time token. The email assumes that a
compatible Python virtual environment already exists at `~/.aos/venv` and that
`aos-keys` 1.10.0 or later is installed. That assumption is false on a new Mac,
so running the email commands first will fail.

The email itself states that the account has not changed yet. Certificate
replacement happens only when the corresponding token command succeeds.

## Security boundary

The email tokens and generated certificates are credentials:

- do not paste a token into source code, Git, a shell script, a chat, or a
  tracked document;
- do not save the email commands in shell history;
- do not commit `~/.aos/security/*.p12`;
- keep the Mac protected by FileVault and the login account password;
- request another reissue email if a token was disclosed before it was used.

The tracked helper never contains or persists tokens. Its `reissue` command
uses Python's private terminal input and calls the installed `aos_keys` library
in that same process. The token therefore does not enter a child-process
argument vector or environment. The helper cannot hide a token from every
privileged local debugger, but it keeps the token out of files, shell history,
ordinary logs, and the process command line.

## Clean installation workflow

On a completely clean Mac, the entire interactive sequence can be started with
one command:

```sh
./scripts/aos-user-setup all
```

It performs the numbered steps below in order. It will pause for Homebrew
installation, macOS Keychain approval, and three hidden token prompts. The
individual subcommands remain useful for inspection and partial recovery.

### 1. Install a supported Python

`aos-keys` 1.10.0 requires Python 3.10 or later. The Apple/Xcode Python 3.9 on
this host is too old. Install native Homebrew Python 3.12:

```sh
brew install python@3.12
```

The project uses 3.12 rather than an unbounded `python3` so this credential
environment remains within the currently published `aos-prov` classifier set.
The AosEdge macOS installation page still says Python 3.9 or later, but the
published metadata for `aos-keys` 1.10.0 is authoritative for the installed
release and specifies Python 3.10 or later.

### 2. Bootstrap the isolated Aos environment

From this repository:

```sh
./scripts/aos-user-setup check-host
./scripts/aos-user-setup bootstrap
```

`bootstrap` creates `~/.aos/venv`, upgrades its private `pip`, and installs
bounded stable tool families:

- `aos-keys >=1.10.0,<2`;
- `aos-signer >=2.0.1,<3`;
- `aos-prov >=5.2.0,<6`.

It verifies the exact installed versions and the generic single-Node
`aos_prov provision` command. Nothing is installed in the repository or in the
Apple system Python.

The qualified installation on the target Mac on 2026-08-14 is Python 3.12.14
ARM64, `aos-keys` 1.10.0, `aos-signer` 2.0.1, and `aos-prov` 5.4.2. Signer 2.x
is required by the schema-v2 official service sample. The
installed provisioning tool accepts an explicit `IP_ADDRESS:PORT` endpoint and
`--nodes`; its default remains two Nodes, so the later provisioning command
must still specify `--nodes 1` explicitly.

The official page currently lists macOS 13, 14, and 15 as tested. This host is
macOS 26.5.2 and therefore outside that published matrix. The native ARM64 CLI
bootstrap, dependency check, key/CSR generation smoke test, and provisioning
module import all pass locally; this is a project qualification, not a claim
that AosEdge has added macOS 26 to its official support matrix.

### 3. Install Aos root trust

```sh
./scripts/aos-user-setup install-root
```

The official tool adds two Aos root certificates to the user's login Keychain.
macOS will request Touch ID or the local account password and an explicit trust
settings confirmation. These prompts require user presence and are not bypassed
by the helper.

### 4. Obtain fresh reissue tokens

Because one-time tokens are credentials, use a newly requested reissue email if
the previous email or its PDF was uploaded, forwarded, logged, or otherwise
disclosed. Confirm that the new email contains three macOS commands for Admin,
OEM, and SP roles.

Do not copy the complete commands. The helper needs only the token value after
`-t` and asks for it with terminal echo disabled.

### 5. Reissue all three certificates

```sh
./scripts/aos-user-setup reissue
```

Paste the three new tokens only into the hidden prompts, in this order:

1. personal Admin;
2. `aa_oem`;
3. `aa_serviceproducer` (SP).

For each role, `aos-keys` generates a new private key locally, requests the
certificate, writes its role-specific PKCS#12 file below `~/.aos/security`, and
imports the client identity into the login Keychain. The helper never
overwrites an existing role file. A repeated run preserves existing
certificates and continues with only the missing roles, allowing safe recovery
from a partial run without deleting credentials blindly.

Expected private files are:

```text
~/.aos/security/aos-user-admin.p12
~/.aos/security/aos-user-oem.p12
~/.aos/security/aos-user-sp.p12
```

### 6. Verify certificate roles and cloud access

```sh
./scripts/aos-user-setup verify
```

The official `aos_keys info` operation validates each certificate and queries
AosCloud for its role and permissions. Review the output locally; do not copy
account identifiers into tracked evidence.

Then visit `https://aoscloud.io/` in Safari or Chrome and select the requested
client certificate. Confirm access separately for the Admin, OEM, and Service
Provider contexts. If the browser caches the wrong identity, use separate
browser profiles or private windows instead of deleting certificate files.

## Recovery rules

- If `bootstrap` fails, no certificate has been consumed; fix Python/package
  installation and repeat `bootstrap`.
- If `install-root` is cancelled, repeat only `install-root`.
- If one `new-user` call fails before creating its `.p12`, do not assume whether
  the token was consumed; request a fresh reissue for that role.
- If one role succeeds and a later role fails, preserve the successful `.p12`
  and Keychain identity. Do not rerun the all-role helper after deleting files;
  classify the partial state first.
- If `info` reports the wrong role, stop before provisioning. Certificate role
  errors must be resolved with AosEdge support, not by renaming `.p12` files.

Successful Admin/OEM/SP verification completes the account and certificate
prerequisites for AOS-1. The OEM certificate will later authorize single-Node
provisioning; the SP certificate will be used for the Hello World and telemetry
service workflow.

## Official references

- [Install Aos command-line tools on macOS](https://docs.aosedge.tech/docs/how-to/aos-tools/install/macos)
- [`aos-keys` release metadata](https://pypi.org/project/aos-keys/)
- [`aos-prov` release metadata](https://pypi.org/project/aos-prov/)
