<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter platform clarity — source and fixture verification

Date: 18 September 2026. Scope: independent visual slice V of the
[versioned-service work packet](../planning/active/work-packets/versioned-service-observability.md),
accepted decisions 4A–6A. Status: implemented and fixture-verified; not deployed
to the live Presenter and not a service/E2E qualification.

## Implemented increment

- The Aos Cloud summary uses current Unit/installed software/update observations,
  not CPU or memory. Installed service counts deduplicate Subject instances and
  exclude pending-only releases. Missing, partial or stale observations do not
  establish “No pending updates”. Failures remain visible. Observation age uses
  the oldest available relevant software read, never a resource read.
- Resources are requested only while the Cloud dialog's Resources section is
  open. Known byte memory is formatted as MiB/GiB with exact original value in
  its tooltip; unverified units are retained rather than assumed. Zero remains
  zero and CPU remains DMIPS. Real source-unit confirmation remains separate
  from the fixture formatting proof.
- Purple Brake and teal Tire accents connect the corresponding backend, service
  slot, wire and dialog header. Platform blue connects the AosCore/Cloud roles.
  Advisory/connectivity colors remain independent operational indications.
- Factory firmware includes AosCore / In-vehicle runtime and the existing B2
  code-symbol software miniature, distinct from the VDP component stack and
  controller hardware. Aos Cloud says Cloud management. Both identify the
  AosEdge platform. This branding claims neither a Core version nor runtime
  health; the existing Factory picker and empty service slots are preserved.
- Fixed layouts retain source freshness. Content-sized rows avoid cards silently
  overlapping the controller, and connector elbows stay above its heading.
  The native-left area, B2 assets, dialogs and lifecycle actions are unchanged.

## Final verification

Executed from `apps/presenter-ui`, against isolated fixture endpoints on port
18070, not the live demo on port 18080:

| Gate | Result |
| --- | --- |
| Unit suite | 156 passed across 18 files |
| Browser suite | 98 passed |
| TypeScript and Vite production build | Passed; output isolated under `/private/tmp/aos-presenter-clarity.T4NwBG` |
| Whitespace check | `git diff --check` passed before recording this document |

The six new unit cases cover Cloud content, missing/stale inventory, pending
updates/failures, duplicate service instances, oldest observation age and
resource units/zero. Browser additions cover shared reads, no overview resource
poll, last-known resource failures, team identity accents, preserved platform
status colors and visible AosCore. The complete existing regression suite also
passes publication/assignment, confirmations, reset, retirement and scope-change
fixtures. These are simulated API results, not new live operation receipts.

Fixed-size tests cover 1280×720, 1512×982, 1728×1117 and native-panel 1118×1124.
Populated cards, empty/no-contact states, dialog bounds, focus return, exact wire
endpoints and elbows above the controller are checked. The fixture screenshots
were visually inspected at compact, ordinary browser and native-panel sizes.
Generated screenshots and browser reports stay in ignored test output.

Earlier development attempts exposed overflow at compact/medium viewports and
internal overlap at a wide viewport. They were corrected in source; the final
counts above are from the subsequent complete passing run, not cherry-picked
retries. The retained Mockup 2.10 files were not overwritten.

## Not changed / not proved

No live assets replaced, browser reloaded, native application restarted, Cloud
object modified, package signed/uploaded, VM altered, model reset or Factory
image built. Existing dirty work was preserved; no commit or push was made in
this increment. The running Test's current health was not requalified here.

Decisions 1A–3A remain coordinated implementation work: active VDP evidence,
service/backend function observations, native maneuver controls and Return to
road. The later Cloud-first decision and P2 option A supersede the proposed
automatic-refresh facility: there is no outstanding approval for a guest
timer, and no new local profile transport is introduced. See the
[P2 clarification](service-renewal-and-local-capability-2026-09-18.md).
No timer, new evidence schema producer or native manager behavior was
introduced by this visual increment. Preserved-Test and clean UI end-to-end
gates remain open.
