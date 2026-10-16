<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed-instance Local Gateway Server Trust

- Status: Accepted; source, installed-code, live transport and automatic UI initialization passed in the recorded engineering scope
- Date: 2026-09-28
- Owner: Demo Control
- Authority: operator accepted a separate local Gateway identity per installed
  instance after reviewing the existing self-signed server / separate client-CA
  model. This is not an OEM or Aos Cloud certificate.
- Parent: [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md),
  [installed state](installed-state.md), `REQ-DEMO-025`, `SYS-DIST-001`.

## Authority and lifecycle

The explicit installed **Start simulator** operation, under Demo Control's
existing writer, initializes server trust before its first native launch. A
read-only status/assets request, package installation, credential selection or
Cloud check never generates trust. Developer mode retains its existing explicit
TLS reference. No automatic adoption/copy of developer or other-instance keys,
system Keychain trust change, external CA request or Cloud mutation is allowed.

Use the existing instance-private `.local/demo-control/tls` directory and fixed
`server-cert.pem` / `server-key.pem` consumer paths. The server certificate is a
unique RSA-2048/SHA-256 self-signed TLS server leaf, valid for 365 days, with
`CA:FALSE`, `digitalSignature,keyEncipherment`, `serverAuth`, and exactly
`DNS:localhost,IP:127.0.0.1`. Its subject includes the canonical instance UUID.
A bounded private `identity.json` records schema 1, the exact instance UUID and
profile `LOCAL_DEMO_SERVER_TLS`. The certificate itself is the explicit local
server trust anchor, delivered by the existing managed SSH enrollment path;
it is not a signing CA for clients. Existing VISS client CA/role leaves, selected
Unit/Node admission and purpose separation are unchanged.

Starting a simulator before Provision creates only local dashboard client trust,
not guest enrollment. Restarting its still-unprovisioned, detached Test uses
ordinary guest readiness without requesting Unit-bound credential restoration.
Only that exact dashboard-only state is exempt from the guest restore check:
Unit/Node or Cloud identity, guest-role fingerprints, onboarding/assignment intent,
a Current Vehicle or a nonzero assignment generation still require the existing
complete matching binding. No identity is synthesized and no admission gate is
opened by this distinction. The current baseline records its scoped proof.

The private key stays on the host, outside Git, Factory, component packages,
Cloud and installer payloads. Output contains only fixed readiness/reuse facts,
not certificate/key content or fingerprints. Directories are owner-only `0700`,
files single-link owner-only regular `0600`, with bounded sizes and canonical
unlinked parents. Crypto uses the verified packaged OpenSSL and its fixed config.

Create a complete validated sibling staging directory, sync it and publish it
with exclusive rename. Do not overwrite even an empty destination. A retained
source run without its server trust blocks recovery; no silent identity rotation.
An interrupted staging directory remains private and blocks creation until
explicit reconciliation; a complete published directory can be reused. Repeat
and process restart validate and reuse byte-identical material. Missing members,
extra members, unsafe paths/modes, foreign identity, mismatched key, invalid
signature/purpose/name or expired certificate fail closed without repair.
Expiry/rotation is an explicit future operation, not a retry or fallback.

## Proof and deployment

Require first-create, unchanged repeat/new-process read, separate-instance keys,
real server-authenticated loopback handshake, wrong-anchor/name refusal,
malformed/expired/wrong-purpose/foreign/linked/partial material refusal,
interrupted-publication preservation, retained-source refusal and redacted
errors. Keep the existing no-client-certificate mTLS admission proof for the real
Gateway: a TLS fixture alone does not qualify live Unit onboarding.

Current installed Start simulator initializes/validates this trust and managed
onboarding supplies the selected Unit's matching mutual-TLS binding. Scoped
first-use/transport/ignition results and remaining negative/recovery cases are
in the [baseline](../../docs/qualification/current-baseline.md). A local TLS
fixture is not full onboarding or clean-install acceptance. Never patch an
immutable installed payload or bypass retained-run version-selection guards.
Earlier kit-specific helper workarounds and then-open UI gates remain in
[Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/a6c095f12f77a947357f504811577ac37784fde0/contracts/distribution-installation/local-gateway-trust.md),
not instructions for the delivered installer.
