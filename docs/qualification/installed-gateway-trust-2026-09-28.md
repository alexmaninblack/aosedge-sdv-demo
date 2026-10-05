<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Gateway Server Trust — 28 September 2026

## Authorized boundary

The operator accepted the [per-instance local server-trust contract](../../contracts/distribution-installation/local-gateway-trust.md)
after the [installed clean-state E2E](installed-clean-e2e-2026-09-28.md) stopped
at `SOURCE_OPERATOR_TLS_REQUIRED`. Demo Control owns the local identity. This
is not an Aos Cloud/OEM certificate authority or a macOS trust-store entry.
The existing client CA, per-role mTLS and selected-Unit admission remain intact.

Source boundary: `source_server_trust.py`, the installed-only preparation hooks
in `source.py`, its reviewed package export and regression tests. The branch is
`codex/installable-demo-stage3`, based on `22ee79e0e21709de34803c6db20047847138eba0`
plus the retained working changes. No new commit/push or release tag is claimed.
Factory `.39`, CARLA/native binaries, model thresholds, service images and
`VDP-TIMEOUT-01` are unchanged.

## Source and rapid proof

The isolated candidate passed 15 tests before promotion into official source.
The final targeted suite passed **170 tests in 22.071 seconds**, including the
installed SourceService ordering and read-only assets check, source lifecycle,
client trust/authentication/guest/restart/boot recovery, host/path separation
and distribution export. Packaged Cloud Python ran with `-I -B`; child Python
also disabled bytecode creation.

Proof includes first-create, unchanged repeat and new-process read, separate
instance identities, real server-authenticated loopback TLS, wrong anchor/name,
expired or wrong-purpose certificates, bad self-signature, key/instance
mismatch, unsafe modes/links, partial/extra/oversized material, interrupted
publication, retained-source rejection and exclusive publication. No error
prints keys, certificate content or fingerprints.

Evidence-only corrections are preserved: the first fixture accidentally created
a parent with mode 0755; a pre-existing runtime-path test expected fake TLS files
to pass. The fixtures were corrected to the stricter accepted contract, not the
product checks relaxed. Initial failed gates are not counted as successful tests.

For the preserved fresh Test, a single-use helper loaded only the reviewed
initializer (source digest
`ea7172cd4d90febbbfc818ecf0f42af9a521fb3d8ac0627c69e18d96d26be97c`) under the
existing installed session and environment writer. It checked the exact private
instance, VM and owner before first-create, verified byte/inode/mtime-identical
reuse and left the lifecycle journal unchanged. The private server pair and
instance record remain under `~/SDV-Lab-Clean/.local/demo-control/tls` by design.
No developer key, Cloud credential or system trust was copied or changed.

This explicit rapid helper does **not** make Kit 009 an automatic initializer.
Its immutable program remains unchanged and the retained-run update guard was
not bypassed.

## Live transport result

After the classified cold-start delay described in the E2E receipt, one normal
warm UI start completed in 43 seconds. The existing dashboard is live; its
startup `viss_verified` event and Gateway status confirm one authenticated
engineering-dashboard role. Gateway remains **DETACHED** from any Cloud Unit.

Read-only loopback checks passed:

- the live dashboard keeps its authenticated connection;
- an anonymous client receives the explicit TLS `certificate required` alert;
- the wrong server hostname fails certificate verification;
- a second dashboard connection is refused by the existing one-per-role rule.

An initial hand-written WebSocket probe omitted `VISSv3` and incorrectly assumed
a second dashboard was allowed; a later evidence read also omitted the instance
root from a relative run path. These were harness mistakes. Source inspection
and corrected scoped checks preserved the running dashboard and security policy.
No disconnected/empty response is used as proof of the no-certificate result.

## Immutable package

Kit 010 manifest:
`08b127ac9d9ba2836e2281d71006133dca418d25e988fda97a0276971c893cb0`.
It contains **17,683 verified files**, **35,114,362,032 logical bytes** and
87 application files. Only `source.py` and the new `source_server_trust.py`
differ from Kit 009; all five large input groups and the old kit are unchanged.
APFS cloning avoided a second physical copy of those large inputs. Full candidate
verification took 233.67 seconds; no Game/Factory rebuild or credential export.

A separate-store installation proof **passed** through the normal Store/Versions
engines, including full transfer verification and explicit revision-0 selection.
The private probe instance is `~/SDV-TLS-Probe`, ID
`5f134250-bc8d-47ae-b389-2aef3ceb0977`; its store is
`SDV-Work/AosEdge-SDV/install-tests/stage3-tls-store-010`. Actual installed Kit 010
code and packaged Python/OpenSSL passed missing-material read-only rejection,
explicit first-create under the existing writer, unchanged repeat, assets
consumption and a second-process unchanged read. All imported runtime modules
came from that kit. No VM, simulator, Cloud credentials or lifecycle journal was
created in this isolated probe. Its normal private identity is retained for
reproducibility; no key was copied from the running Test.

The active Test's Kit 009 selection remained unchanged. Automatic UI first-use,
the native launch action and a genuinely clean Mac remain separate gates; the
direct installed-code proof does not claim them. Final documentation validation
passed for 308 Markdown documents, 662 identifiers and 38 diagrams; the tracked
confidential-input guard and whitespace check also passed.

## Remaining gates and evidence

Resume exact authorized Cloud publication/provisioning and sequential
V1→V2→V3 E2E. Keep
`CARLA-FIRST-START-01` open: the first installed execution remained pre-main
until macOS completed scanning after the readiness deadline; signature integrity
passed. No OS security setting or native timeout was changed. Installer launch
remains after E2E in the operator's requested order.

Ignored evidence is under `CarlaSim/Build-distribution-stage2-20260926/`:
`installed-gateway-tls-proof-intent.json`, `installed-gateway-tls-proof.json`,
`live-gateway-tls-20260928.json`, `kit-010-refresh-20260928.json`,
`kit-010-installed-tls-proof.json`,
`installed-carla-first-start-sample.txt` and
`installed-gateway-start-completed.png`. The isolated candidate and proof scripts
are retained there for reproducibility, not exported as product or credentials.
No cleanup or deletion was performed in this trust continuation.
After live CARLA startup and isolated installation, observed internal free space
was approximately 89.0 GiB and Work approximately 561.4 GiB. The narrow internal
reserve must be restored/rechecked before further large artifact work; this
does not authorize broad cleanup. No additional large build was started.
