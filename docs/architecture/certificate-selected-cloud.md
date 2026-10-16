<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Certificate-selected Cloud access

Demo Control derives the Cloud destination from the selected credentials;
Setup and Presenter use the same guarded owner. Production/Staging environments
are distinct from Test/Production vehicle roles. Selecting access does not
provision a vehicle or grant permission for an automatic mutation.

Reusable content and destination-specific signing are separated by
[ADR 0016](decisions/0016-unsigned-packages-and-session-scoped-signing.md).
The [Setup first-use contract](../../contracts/distribution-installation/cloud-first-use.md)
owns enrollment, pair validation and missing-prerequisite preparation. Exact
current evidence belongs to the [baseline](../qualification/current-baseline.md).

## Operator interaction

For ordinary first use, configure the OEM/SP pair in **Setup → Connect to Aos
Cloud**. Exceptional Presenter-side OEM selection is under **Advanced settings**,
not a separate mandatory Session step. The panel reads the configured OEM
certificate locally, or **Choose certificate…** opens the native macOS file
picker. The browser receives public metadata only. **Use this Cloud** confirms
the exact native preview. A changed domain between preview and selection blocks
the operation. Cancellation changes nothing.

The equivalent headless operations use the same Demo Control application:

```sh
democtl cloud inspect
democtl cloud inspect --certificate ~/.aos/security/aos-user-oem.p12
democtl cloud select --certificate ~/.aos/security/aos-user-oem.p12
```

Selection is local configuration only: no VM restart, provisioning, publication,
Subject assignment, Cloud deletion or live connectivity check is implied.

## Domain and trust

The source is the single Organization (`O`) in the PKCS#12 client certificate,
matching the installed Aos SDK's `UserCredentials.cloud_url` implementation.
It is not inferred from the issuer, a server handshake, an unrelated SAN or a
manually typed browser URL. The user confirmed the existing endpoint contract:

| Consumer | Endpoint / source |
| --- | --- |
| OEM and SP API workers | `https://<certificate-domain>:10000/api/v11/` |
| Test Communication Manager | `https://<certificate-domain>:9000/sd/v7/` |
| Further CM transport endpoints | Native Service Discovery response |
| TLS trust | Existing packaged Aos CA; unchanged hostname verification |
| Debug name resolution | Explicit matching entries in the Mac's `/etc/hosts`, projected into Test |

The selected domain is pinned in the active private instance's configuration
under `cloudConnection` (a developer checkout may use `.local/demo-control/status.json`).
Credential paths remain local `cloudProfiles` references;
the key and certificate are neither copied into the repository nor uploaded by
the settings panel. PKCS#12 files must be private to their owner. The existing
SDK credential path supports unencrypted PKCS#12 files; a password-protected
file returns a bounded diagnostic rather than prompting in the browser.

All selected OEM/SP request workers check that their certificate domain matches
the selected domain **before networking or signing**. An SP certificate for
another Cloud is not a fallback and is not silently reused. Legacy profiles
without an explicit selection retain the existing `aoscloud.io` restriction.

## Identity and lifecycle isolation

Switching domains requires an unprovisioned Test with no component/service
operation receipts or unresolved operation. A provisioned/partially provisioned
Test must complete **Finish demo** first. The same explicit selection can repair
an interrupted local config/journal write; a mismatched pair otherwise blocks.

`selectedCloudDomain` pins the current Test context. Legacy `cloudBinding` and
`demoSubjects` remain untouched. Other domains keep their own binding and
retained Subjects under `cloudContexts[domain]`; UUIDs are never transplanted
between Clouds. Release number continuity remains monotonic and is not reset.

Production's VM, Unit, original binding and Subjects are preserved. While a
non-production Cloud is selected, Cloud lifecycle operations target Test only;
`all` and Production mutations are blocked. Cloud status does not send the old
Production UUID to the selected debug API. The old dual-role component path is
not available in debug mode; the normal Studio verification-publication path is.

### First-use prerequisites

The selected Cloud needs its own matching Unit Model, node support, Test
verification set and service catalog. Selection alone creates none of them.
Ordinary Setup Connect composes the existing `cloud check` / `cloud prepare`
engines. Check is read-only. Prepare authenticates OEM/SP, reuses Default and
creates only an absent `aos-vm;1.0.0` model with the tracked single-node config
and empty `Test Vehicles` verification set, then rereads authoritative state.
Incompatible/ambiguous objects, denied reads and uncertain creation block;
there is no overwrite, adoption or blind retry.

Node Types are observed, not speculatively created. An empty catalog before
provisioning is `AFTER_PROVISION`; after the journal has a Unit identity, absence
of its expected node type is a failed confirmation. SDK identity must match
`aos-vm-main`. Prepare creates no Unit, service publication or Subject assignment.
Setup readiness confirms prerequisites, not installation or vehicle operation.

### Interrupted registration recovery

A newly provisioned Unit may return `unit_sets: null` before verification-set
assignment. The Unit reader treats this explicit null as an empty membership
list, preserving the reported Online state and node identity. Malformed non-list
values still fail rather than being interpreted as no memberships.

If the current journal already records the Test system UID and a `PROVISIONING`
lifecycle, the Presenter offers **Continue registration**, including when the
local Unit ID has not yet been bound or a publication is still processing.
This is a local recovery hint, not a claim that Cloud is Online. The existing
Unit command observes/binds the exact identity, confirms the guest and existing
source, and completes only missing Test-set assignment. It does not repeat the
SDK registration or reset the simulator. Cloud remains the source of Online and
installation status.

Test-only lifecycle requires only its Test set. An observed or recorded opposite
role still protects against crossed membership, but no Production set is created
just to provision or retire Test. Existing two-role CLI operations retain both
role checks. Setup configuration and release continuity survive Finish.

Authenticated owner IDs distinguish tenants inside a domain; certificate renewal
for the same owner reuses the context. A changed owner with a live/uncertain run
requires Finish/reconciliation, not adoption of its Unit, Subjects or receipts.
Publication history remains owner-scoped across certificate rotation; legacy
receipts are used only when their recorded owner matches the selected authority.

## VDP identity and first publication

The component UUID belongs to one Cloud instance. Demo Control resolves the VDP
by its exact, case-insensitive codename and the authenticated OEM owner in the
selected Cloud's complete `GET /components/` result. It never sends a production
component UUID to another Cloud. Ambiguous matching identities are an error.

A successful complete catalog with no matching component returns `ABSENT`, an
empty version list and no latest version. Preparation can continue. A failed
request is not proof of absence: authentication, permission, TLS and server
errors, including a collection `404`, remain errors. A detail `404` can also
mean access is forbidden; it is not treated as permission to create an identity.

The existing `POST /deployment-bundles/upload/` remains the only publication
route. Bundle metadata identifies the component by type and codename, not a
production UUID. Cloud processing creates the new identity/version. Observation
resolves the actual Cloud UUID and uses it for version reads. `uploaded` and
`building`, or a completed bundle whose version has not yet appeared, remain
`PROCESSING`; HTTP acceptance alone never means ready. No manual component
creation, automatic approval or repeated upload is introduced. Existing Test
recipient checks and the monotonic release ledger remain unchanged.

### Signing authority is the session selection

Every new VDP bundle is signed with the **currently selected OEM PKCS#12**,
referenced by `cloudProfiles.oem-delivery.credential`. Verification before upload
uses that same credential, and upload uses its authenticated OEM account in the
selected Cloud. A missing, changed or incompatible credential blocks the action;
there is no fallback to the original production signing key. Services retain
their distinct SP signing authority and must match the selected Cloud domain.

The frozen v1/v2/v3 source profiles are canonical unsigned inputs, protected by
the reviewed source digests in ADR 0016. Initial migration checks both the
already pinned legacy archive and its exact unsigned inner archive, including
structure/configuration agreement. Subsequent preparation verifies the pinned
unsigned source directly. No old certificate is required. The legacy
`componentBaselineCertificate` configuration field remains readable for
compatibility, but is not used by normal Prepare or source verification.

Signatures live in selected-context directories, independently of immutable
prepared content. Re-signing with a new certificate changes neither content
nor version. Publication receipts are Cloud/role scoped and retain their owner
and exact response IDs across certificate rotation. A possibly attempted
upload is not repeated by signing again. SP/service IDs are resolved at the
selected destination; they are not reused from an old prepared package.

Sources: [Aos object identification](https://docs.aosedge.tech/docs/reference/ontology/object_identification),
[deployable items and bundle processing](https://docs.aosedge.tech/docs/aos-cloud/entities/deployable_item),
and the [v11 API schema](https://api.aoscloud.io/api/v11/openapi.json), checked on
14 September 2026. The API defines UUIDs and bundle operations; the pinned source
verification and monotonic release policy are Demo Control implementation rules.

## Guest configuration

Production Cloud (`aoscloud.io`) uses the ordinary guest startup/provisioning
path, including when that domain was explicitly selected in the UI. It adds no
Cloud host entries, runtime files, bind mounts or CM configuration overrides.
The Production-role VM is also excluded from all debug projections.

For the selected debug Cloud, the startup order is: VM boot and minimum SSH
access setup → debug `/etc/hosts` projection → selected CM endpoint → normal
guest readiness and role initialization → provisioning. Projection runs inside
the first SSH startup call, not after role initialization or a failed DNS probe.
A failed or uncertain projection blocks later steps; it cannot report ready.
For `.test` domains all six explicit host mappings must exist on the Mac first.
Entries sharing an address are written on one line, preserving unrelated hosts.

`unit provision test` projects the selected Service Discovery URL and the exact
matching host entries **before** SDK registration. It does not repoint an
already provisioned or active CM. API and guest endpoints therefore use the same
selection. The existing `caCert` and all unrelated CM fields are preserved.

The Factory image is read-only. Public files are staged under
`/run/democtl-cloud` and bind-mounted read-only over `/etc/aos/cm.cfg` and, when
needed, `/etc/hosts`, preserving their SELinux labels. No root remount, CM/SM
binary patch, relaxed TLS or Factory rebuild is used.

These are transient debug projections. On the next explicit `democtl vm start
test`, they are recreated. If a provisioned guest has already auto-started CM
with the Factory endpoint after reboot, that start command restarts **CM only,
once**, to load the selected endpoint. An unchanged projection causes no restart.
An unmanaged in-guest reboot is not self-configuring: run `democtl vm start
test` to reapply the selected host-managed configuration. This limitation must
be considered when designing Online/Offline timing experiments; it is not a
claim that the Factory image itself has been updated.

When returning from an already configured debug guest to production, stop/start
the unprovisioned VM first so its transient debug mounts disappear. Merely
selecting production in the UI does not mutate or reset a running guest.

The initial settings delivery is validated with local CLI/certificate reads,
offline scope and guest-projection tests, and the live settings UI. A real
developer-Cloud provision/reboot cycle is a separate live qualification; do not
infer it from a successful selection or from simulated mount tests.

## Evidence boundary

Certificate inspection, access checks, first-use preparation, publication,
provisioning and guest recovery establish separate facts. The current baseline
owns scoped API/UI/native Setup results; it does not close every new-account,
rotation or interruption case. Earlier session-specific tests, legacy source
signature verification and then-unprovisioned Test observations remain in
[Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/a6c095f12f77a947357f504811577ac37784fde0/docs/architecture/certificate-selected-cloud.md),
not current setup prerequisites or evidence of another environment's readiness.
