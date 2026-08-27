<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# End-to-End Stage Evidence — Design Reviewed

- Decision: `D4-025`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.4.0`
- Accepted subdecisions: D4-025.1 canonical atomic stage record and D4-025.2
  assertion predicates/authoritative evidence references, plus D4-025.3 Demo
  Baseline Qualification Dossier, D4-025.4 exact parameterized stage map and
  D4-025.5 verdict composition/framework qualification, 2026-08-23

The stable `AT-E2E-001` through `AT-E2E-011` identifiers remain acceptance
cases. A case that requires several external actions contains ordered atomic
stages identified as `AT-E2E-NNN/SNN`; it is not renumbered. Every atomic stage
has exactly one bounded action and follows entry assertions, action,
authoritative re-read and exit assertions. The top-level case verdict is
composed from its mandatory stage verdicts.

Each stage record contains case/stage identity and version, the D4-024
correlation-record digest, entry assertions, one action, authoritative re-read,
exit assertions, local orchestration state, a separate acceptance verdict,
sanitized evidence references, start/completion times and claim-boundary codes.

Verbatim external owner state, local orchestration state and acceptance verdict
are never flattened. `BLOCKED` submits nothing. Timeout or lost response enters
`UNCERTAIN`, assigns no automatic verdict and permits no blind retry.
Reconciliation requires an authoritative re-read. `PASSED` requires every
mandatory exit assertion; `FAILED` is a proven mismatch and `ABORTED` is an
intentionally stopped attempt without a success claim. A top-level case cannot
pass while any mandatory stage has not passed.

Ordinary demo runs retain no stage-record history. Records become dossier
material only for an explicitly designated formal qualification or acceptance
run.

D4-026.1 names four non-interchangeable execution modes:
`STATIC_CONFORMANCE`, `CONTROLLED_DISPOSABLE_QUALIFICATION`,
`LIVE_BASELINE_POSITIVE` and `AUDIENCE_PRESENTATION`. Static checks do not prove
the integrated system. Negative, destructive, interrupted and recovery cases
run on separate disposable qualification identities. Only a predesignated
live-positive run of the exact complete baseline may create this dossier.
Audience presentation performs current authoritative preflights but is not a
qualification mode that creates or retains a dossier.

D4-026.2 further separates identity lifetimes. Once-issued OEM, SP1 and SP2
Cloud certificates and their fixed publication/operation profiles are stable
demo infrastructure and are never dossier content or R0 targets. Vehicle
overlays, Unit/Node/`system_uid` values and vehicle credentials are fresh and
disposable for each run. Aos IAM Service-instance identity and its short-lived
KUKSA JWT are runtime-derived. Retained records use fingerprints and never
promote a qualification Unit identity into an audience run.

D4-026.3 allocates all integrated positive cases `AT-E2E-001` through
`AT-E2E-008` and positive R0 `AT-E2E-010` to
`LIVE_BASELINE_POSITIVE`. `AT-E2E-009` owns every accepted stable negative
vector and `AT-E2E-011` every mapped external-mutation interruption/recovery
instance under `CONTROLLED_DISPOSABLE_QUALIFICATION`; those vectors are not
duplicated under their originating positive case IDs. Static conformance is a
dossier prerequisite but not an integrated case verdict. Audience presentation
uses current preflights but contributes no qualification record.

D4-026.4 requires two consecutive complete live-positive cycles without
duplicating owner-specific Brake/Tire/connectivity/quota repeat series. Cycle B
is also a human presenter acceptance rehearsal through reviewed visible
interfaces. Final qualification is `MACHINE_PASSED AND HUMAN_ACCEPTED`: machine
success alone is insufficient, a human rejection vetoes it, and human
acceptance never waives a failed/incomplete/uncertain/stale machine result.
Exact/categorical assertions have zero tolerance; physical, resource and
connectivity bounds remain owned by frozen profiles. In-motion readiness
maxima are characterized and frozen for the exact implementation before
formal qualification rather than guessed in design.

D4-026.5 keeps exactly one current local qualification dossier under
`.local/qualification/current/` and its bounded status at
`.local/qualification/qualification-status.json`. Candidate evidence is built
under `.local/qualification/candidate/`, fully validated and sealed, then
atomically replaces the previous current dossier. The previous dossier remains
intact until replacement verification succeeds and is then deleted; the first
implementation keeps no dossier history. All paths are Git-ignored and nothing
is uploaded automatically.

The short status vocabulary is `ABSENT`, `QUALIFIED`, `STALE`, `WITHDRAWN` and
`NOT_QUALIFIED`. The dashboard reads only that bounded status and sanitized
reason codes. A failed/aborted/incomplete candidate never replaces current
evidence and is removed after reconciliation unless an operator explicitly
retains a separate sanitized incident. Human rejection produces
`NOT_QUALIFIED`; human withdrawal is fail-closed and only a new complete
qualification can restore `QUALIFIED`. R0 preserves the current dossier and
status while deleting ordinary run history.

D4-026.6 defines a 30-minute planned core narrative inside a 45-minute
reserved audience slot, with Q&A outside that slot. This is a presenter-
readiness target, not a Cloud or vehicle performance KPI. Real Cloud waits stay
visible as authoritative `WAITING` state; they are neither hidden nor replaced
by replay. An impractical end-to-end experience may cause human presenter
rejection without converting Cloud duration into a machine qualification
failure.

The mandatory core story covers M0/M1, G0, G1 VDP v1, G2 Brake v1, G3 VDP v2
plus Brake v2, G4 VDP v3 plus Brake v3 with the one external-connectivity
event, T1 independent Tire lifecycle/resource isolation and R0. Current
preflights, VU validation, team acceptance, OEM authorization, recipient-set
equality, authoritative re-reads and R0 gates are real and may be summarized
but never skipped or simulated. Audit/log drill-down, extra CARLA runs,
repeated events and deeper metadata/permission/quota/evidence views are
optional. Negative, destructive, interruption and qualification-framework
work is never an audience step.

Assertions use only the closed predicate set `EXISTS`, `ABSENT`, `EQUALS`,
`NOT_EQUALS`, `STATE_IS`, `STATE_IN`, `COUNT_EQUALS`, `SET_EQUALS`,
`DIGEST_EQUALS`, `UNCHANGED`, `CAUSALLY_LINKED`, `SEQUENCE_COMPLETE` and
`NO_FORBIDDEN_FIELDS`. Each assertion carries a stable ID, mandatory/optional
flag, sanitized expected/actual value or digest, freshness rule, fixed outcome
and reason code, plus references to D4-024 evidence records.

Each evidence reference binds authoritative owner/source, exact subject and
correlation fingerprints, observation/fetch times, request/record fingerprint,
content digest and freshness. It must match the stage Unit, role, source,
Service and artifact. A mutation re-read occurs after action. HTTP success,
screenshot or operator prose alone is never proof, and raw external responses
are not copied into stage records.

All mandatory entry assertions pass before action. Proven mismatch blocks with
that fact; missing/stale/conflicting evidence blocks without claiming a system
failure. All mandatory exits pass for `PASSED`; proven mismatch is `FAILED`.
Missing or ambiguous post-action state remains `UNCERTAIN`/`RECONCILING` with no
automatic verdict. Optional assertions never affect verdict but remain visible.

The `Demo Solution Qualification Run` is the final engineering acceptance of
one exact completed demo baseline before it is shown to an audience. It is not
the per-candidate VU-to-PU release approval inside the scenario. It must be
designated before start, so a successful ordinary run cannot be selected
post-hoc. Ordinary audience runs create no dossier.

The sealed `Demo Baseline Qualification Dossier` contains a manifest,
human-readable generated summary, sanitized stage/evidence records, the
sanitized human presenter review and checksums. Its manifest binds Factory
Image, AosCore/API/repository revision,
all prepared artifact/metadata/configuration/contract digests, VU/PU/source
fingerprints, included cases and verdicts, claim boundary, R0 result and
fingerprinted authoritative audit references.

The summary adds no facts. Screenshots are not proof and the dossier does not
copy AosCloud authority. Raw telemetry/payloads/responses/logs, credentials,
authorization headers, JWTs, certificates/private keys, VIN and full
Unit/Node/`system_uid` values are forbidden. Schema, secret scan and all
digests/references pass before sealing. A sealed dossier is immutable; a
correction creates a new version with `supersedesDossierId`.

The machine dossier may be `INCOMPLETE`, `PASSED`, `FAILED` or `ABORTED`;
`PASSED` requires passed R0 cleanup and uncertain cleanup is `INCOMPLETE`.
The final `QUALIFIED` decision additionally requires the human review outcome
`ACCEPTED`.

The exact stage map uses composite identity: acceptance case, stable stage ID,
`stageInstanceKey` and target/artifact correlation digest. The ten-stage common
release template is instantiated for VDP v1–v3, Brake v1–v3 and Tire v1 rather
than copied. Joint v2/v3 graphs validate both VU instances and record both
owner acceptances before VDP promotion and then dependent-Service promotion.

M0/M1/G0, G1–G4 and T1 have fixed stages. Cross-stage negatives are instances
of stable owner-vector IDs; R0 repeats its Unit retirement template for
Validation and Production roles before shared cleanup; interruption tests
are instances of the external mutation classes actually used by the map.

An entry-blocked stage is `NOT_EVALUATED`; a proven mandatory exit mismatch is
`FAILED`; an intentional stop with proven safe abort is `ABORTED`; an unknown
action result remains `NOT_EVALUATED` in `UNCERTAIN`/`RECONCILING`; only all
mandatory exits passing yields `PASSED`. Optional assertions never affect it.

Case composition applies failure, then abort, then incomplete/not-evaluated
precedence; only every mandatory stage and required instance passing yields a
case pass. Manual override is forbidden and an OEM approval action is evidence,
not an automatic case verdict. Dossier pass requires every D4-026-required case,
R0 and the forbidden-data scan. Proven case failure, intentional abort and any
unresolved evidence map to `FAILED`, `ABORTED` and `INCOMPLETE` respectively.

Framework qualification validates every schema, map/template identity and
dependency, the complete verdict truth table, missing/stale/conflicting and
tamper fixtures, forbidden-data scans, interrupted record writes, deterministic
summary derivation and sealed-dossier immutability. One synthetic controlled
framework run passes before any real operation.

The D4-025 evidence design and all D4-026.1–.6 mode, identity, case-allocation,
repeatability, human acceptance, retention, status, atomic-replacement and
audience-presentation boundaries are closed. D4-026 is `DESIGN_REVIEWED`.
Implementation, UI mockups, measured rehearsal and application to a real demo
baseline remain open. This review authorizes no implementation or external
mutation.
