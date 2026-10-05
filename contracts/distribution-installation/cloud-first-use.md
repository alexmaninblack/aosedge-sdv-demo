<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Cloud First-use Completion

- Status: Accepted implementation detail of the two user decisions of 29 September 2026
- Version: 1.1
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Parent: [native setup](native-setup.md), [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)

The existing Demo Control writer and selected installed-package leases own
first use. Neither path initializes a vehicle journal, changes package selection,
starts the runtime, adopts a retained run, or grants a role from a certificate
filename. Registration and email confirmation remain official Cloud/operator
actions; never execute an email command or accept terms on the operator's behalf.

## Existing Subject references

Authenticated OEM/SP readers may enumerate the two fixed demo Subject labels.
Enumeration is not adoption. Present exact UUIDs and eligibility; never select
an item automatically. Require one associated OEM/SP pair, an unambiguous exact
Subject of the existing group/type/priority, its recorded creator, exactly the
expected service owned by that SP, and zero desired/reported Unit recipients.
Service recipients through other Subjects also block reuse. Failed or incomplete
reads are not absence. Unknown create responses remain blocked.

Explicit selection re-reads these identities, compares the certificate/config/
package metadata token, and atomically stores only public references under the
existing domain/OEM `cloudSetupContexts` configuration. Retain peer entries;
reject replacement of another recorded reference. An identical selection is a
no-op. Configuration and credentials must still match after the remote read.

At first assignment to a subsequently created Test, the existing assignment
owner revalidates the exact saved reference and zero-recipient conditions before
recording it in the selected tenant's `demoSubjects`. Existing publication and
Test-binding guards still apply. Subsequent repeat/recovery uses that journal's
normal exact-ID reconciliation, not first-use selection. No existing Subject,
service, Unit or assignment is mutated by inspecting/saving references.

After an explicitly authorized single-Test Finish, the old run journal may be
gone while its Subject and service objects remain in Cloud. The same inventory,
explicit exact-reference selection and fresh zero-recipient checks apply; do
not auto-adopt them by label or reconstruct an old vehicle journal. See the
[single-Test cleanup amendment](../demo-run-state/README.md) for required
absence/terminal-receipt proofs before the old journal is removed.

## Token enrollment

Native secure input supplies one explicit domain, OEM/SP role and one-time token
over bounded stdin to the verified private Cloud runtime. Never use arguments,
environment, logs or evidence for the token. Clear native input after dispatch.
Use SDK key/CSR and PKCS#12 primitives, the packaged Aos CA, fixed HTTPS port
10000 and `/api/v11/user-certificates/`. Disable redirects, environment trust/
proxies and retries. Use one POST, bounded connect/read time and response size;
the existing native deadline bounds the full helper process group. Do not call
the SDK CLI's fallback, version check or browser/system certificate installers.

New enrollment explicitly selects the SDK's RSA-2048 key mode. The pinned
official package signer and package verification require RS256 for both OEM
components and SP services; the SDK's default EC key supports authentication
but not this signing path. Local pair inspection rejects non-RSA keys before
save/readiness, and package signing checks again before packing. This does not
change Cloud trust, signature algorithms or permissions. Existing completed
EC attempts remain preserved and replayable as enrollment receipts, not evidence
of package-signing capability; never rotate or delete their keys automatically.

Each role owns a private enrollment directory beneath the existing instance
credentials directory. Store the key and CSR before dispatch, with an atomic
receipt identifying the domain, role and attempt UUID. Record dispatch intent
durably before calling transport. Files are canonical, owner-private, regular,
single-link and bounded; pending/partial/foreign files block, without repair by
deletion. Credentials and attempt data never enter immutable packages or Git.

Validate a returned certificate's key, selected domain and validity before
publishing its private PKCS#12 file with no overwrite. Receipt completion is
separate from successful Cloud role/association checks. First use of the pair
still requires the ordinary explicit inspect/save/check path. Repeat after
success reuses the same output without another issuance request.

After dispatch, TLS/network failure, timeout, ambiguous HTTP/response or process
loss requires reconciliation and must never trigger automatic replay. A status
read sends no request. An explicit local recovery may finish a valid already
written credential/receipt without network. Otherwise preserve the attempt/key;
the operator must reconcile the previous issuance in Cloud and explicitly
confirm that exact attempt before submitting a replacement token. Preserve
prior attempt records and reuse the retained key; a replacement token alone
does not erase uncertainty or authorize dropping the earlier identity.

Qualify first/repeat, restart after each durable boundary, no replay, redaction,
links/modes/oversize/changed inputs, malformed response, wrong certificate,
concurrent owner, native protocol feedback and absence of a vehicle journal.
Synthetic-token tests are not real enrollment or clean-Mac acceptance.
