<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health v3 Advisory Policy

- Decision: D4-016.4 accepted 2026-08-23
- Contract version: 1.0.1 (dependency-only repin to Typed QM Advisory 1.0.2;
  Brake Health policy semantics are unchanged)
- Reuses: [Typed QM Advisory Profile](../qm-advisory-profile/README.md)
- Accepted policy SHA-256:
  `13216b51647525d48b83eb79bd47444ccb392d1a51a7ffd18b593d4c91f52467`

This accepted policy binds the accepted synthetic Brake Health assessment to the
already accepted D4-008 Brake advisory endpoint. It adds no new actuator,
protocol, authority or driver-HMI claim.

An eligible transition into `INSPECTION_RECOMMENDED` creates one canonical
`SET` request whose `decisionId` is the source assessment ID. The same action
occurs once on first v3 activation after a v2→v3 upgrade when accepted
persistent state is already `INSPECTION_RECOMMENDED` and no advisory has been
recorded for its last assessment ID. This activation reuses the accepted
assessment and creates no synthetic assessment or band-change event. While the
condition remains active, v3 refreshes the 30-second lease every 20 seconds.
External vehicle connectivity is not required; KUKSA, VDP, VISS and Gateway
must remain available.

The Service reads the matching Gateway Status and treats only matching
`APPLIED`/`CLEARED` as application evidence. KUKSA or VISS write success is
transport evidence only. A rejected request never falls back to another path
or command. After a crash or loss of the internal advisory chain, lease expiry
removes the indication; it is never claimed as driver acknowledgement.

The accepted persistent epoch and monotonic-sequence policy has one lifecycle
meaning. An ordinary process, container or VM restart preserves the producer
epoch and continues from the persisted next sequence without reuse. Only an
explicit producer replacement or new producer lifecycle rotates the epoch,
exactly once, and starts its sequence at `1`. R0 destroys the producer state.
Delayed evidence from an old epoch may remain historical evidence, but it can
never change the current state or advisory.
