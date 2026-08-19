<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Component Requirement Package Template

- Status: Template
- Package: `CR-<PACKAGE>`
- Version: `0.1`
- Prepared: `YYYY-MM-DD`
- Owner: `<accountable team>`
- Architecture input: `[High-Level Architecture <version>](../../architecture/high-level-architecture.md)`
- Scenario input: `[Demo Scenarios <version>](../../demo/staged-post-sop-brake-health-demo-scenarios.md)`
- Flow input: `[Architecture Flows <version>](../../architecture/demo-scenario-architecture-flows.md)`
- System-requirements input: `[System Requirements <version>](../system-requirements-and-traceability.md)`
- Component-register input: `[Component Register <version>](../component-decomposition-and-interface-register.md)`

Replace every angle-bracket placeholder before requesting package review.
Keep this order unless a package-specific concern makes an additional section
necessary.

## Purpose

Explain why this package exists, what audience-visible or platform behavior it
enables, and which provisional `CR-*` allocation it expands.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | `<one short boundary statement>` |
| What this package does not own | `<adjacent responsibilities and exclusions>` |
| Intended result | `<observable result in plain language>` |
| Accountable lifecycle owner | `<team and FOTA, SOTA or other lifecycle>` |
| Primary repository or external source | `<repository, upstream project or no-code owner>` |

## Component Boundary

### In scope

- `<owned behavior, state or integration responsibility>`

### Out of scope

- `<explicit adjacent or deferred responsibility>`

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| `<named dependency>` | `<owner>` | `<contract/version/state>` | `<visible behavior>` |

## Testability Boundary

Describe the smallest owned units of behavior and the seams used to isolate
external dependencies. State which inputs can be injected, which clocks,
random sources or persistence mechanisms must be controlled, and which outputs
are observable without launching the complete demonstration.

Owned implementation logic shall be structured so its deterministic decisions,
validation, boundary handling and recovery behavior can be tested without
starting Unreal Engine, CARLA, QEMU, AosCloud or a real KUKSA Databroker. Use
mocks, fakes, fixtures or an in-process test double at those boundaries. If the
package owns no executable logic or integrates an unchanged external binary,
record `Not applicable` and identify the contract or integration proof that
replaces an owned unit-test obligation.

## Interface Summary

| Interface | Direction | Data or command | Contract/version | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| `<named IF definition with direct link>` | In / Out | `<payload>` | `<version>` | `<fail/degrade/retry>` | `<source of truth>` |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required for this package | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove one owned decision, transformation, validator or state transition in isolation | External systems replaced by deterministic doubles | Yes / No with rationale | Test report tied to `UT-*` obligations |
| Component | Prove the packaged executable through its public boundary | Controlled dependencies and fixtures | Yes / No with rationale | Component-suite report and logs |
| Contract | Prove producer and consumer agree on schema, semantics, errors and versioning | Versioned fixtures or conformance harness | Yes / No with rationale | Contract-suite result and fixture digest |
| Integration | Prove behavior with real adjacent components | Named integration environment | Yes / No with rationale | Integration record and exact revisions |
| End-to-end | Prove the accepted audience-visible flow | Validation then Demonstration lane | Yes / No with rationale | Qualification record and dashboard evidence |

Unit tests are necessary for owned logic but are not sufficient acceptance
evidence for an interface or complete demo flow. Integration and end-to-end
tests likewise do not replace inexpensive isolated checks of owned branches and
failure handling.

## Requirement Summary

| Requirement | Plain-language obligation | Verification levels | State |
| --- | --- | --- | --- |
| `[Short name (REQ-<PACKAGE>-NNN)](#req-package-nnn)` | `<one-sentence outcome>` | Unit / Contract / Integration / End-to-end | Draft |

## Detailed Requirements

Copy this subsection once per requirement.

### `<Short name>`

<a id="req-package-nnn"></a>

- ID: `REQ-<PACKAGE>-NNN`
- Statement: The `<component>` shall `<observable behavior and conditions>`.
- Rationale: `<why the system or audience needs it>`
- Parent system requirement: `<named SYS definition with direct link>`
- Architecture flow: `<named AF definition with direct link>`
- Components: `<named CMP definition with direct link>`
- Interfaces: `<named IF definition with direct link>`
- Verification levels: Unit / Component / Contract / Integration / End-to-end
- Required evidence: `<report, assertion, log, status or dashboard observation>`
- State: Draft

#### Acceptance criteria

1. Given `<precondition>`, when `<stimulus>`, then `<observable result>`.
2. Boundary and malformed input produces `<bounded result>`.
3. Dependency unavailability produces `<degraded, rejected or recovery result>`.

Requirements must be atomic enough to produce an unambiguous pass/fail result.
Use measurable bounds where the system design defines them. Do not hide a new
architecture decision in an acceptance criterion.

## Unit-Test Obligations

Use one stable obligation for each independently meaningful behavior or branch,
not necessarily for each implementation test function. Several test cases may
satisfy one obligation and one test case may provide evidence for several
requirements when the mapping remains explicit.

| Unit-test obligation | Requirements proved | Behavior and branches | Isolation / doubles | Required assertions | Repository / suite | State |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="ut-package-nnn"></a>`UT-<PACKAGE>-NNN` — `<short name>` | `[REQ-<PACKAGE>-NNN](#req-package-nnn)` | Normal, boundary, malformed, unavailable and recovery cases as applicable | `<fakes, clock, fixture, storage or transport double>` | `<observable outputs, state and prohibited side effects>` | `<repository and suite>` | Draft |

Every owned unit-test obligation shall be deterministic, runnable without
Cloud or simulator credentials, suitable for the normal repository gate, and
blocking when it fails. Tests shall not print secrets or depend on personal
paths, ambient network access, wall-clock timing or execution order.

Code coverage may be retained as supporting evidence, but a percentage alone
does not prove this package. Review is based on required behavior, decisions,
boundaries, negative paths and recovery paths.

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| `[REQ-<PACKAGE>-NNN](#req-package-nnn)` | `[UT-<PACKAGE>-NNN](#ut-package-nnn)` or reasoned N/A | Required / N/A; D4 suite reference | Required / N/A; D4 contract reference | Required / N/A; D4 environment reference | Required / N/A; accepted flow reference |

Every active requirement must have a complete row. `N/A` requires a short
reason; an empty cell is not a decision. D3 fixes the required proof levels and
stable unit-test obligations. D4 replaces provisional suite references with
executable cases, fixtures and evidence locations.

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Security and least privilege | `<named SYS/REQ link>` | `<boundary or policy>` | `<level/evidence>` |
| Privacy and redaction | `<named SYS/REQ link>` | `<data treatment>` | `<level/evidence>` |
| Resource bounds | `<named SYS/REQ link>` | `<CPU/memory/storage/rate bounds>` | `<level/evidence>` |
| Timing | `<named SYS/REQ link>` | `<latency/timeout/retry bounds>` | `<level/evidence>` |
| Offline and recovery | `<named SYS/REQ link>` | `<bounded behavior>` | `<level/evidence>` |
| Observability | `<named SYS/REQ link>` | `<authoritative status/log source>` | `<level/evidence>` |

## Package Acceptance

The package is ready for acceptance when:

1. its boundary agrees with the accepted HLA and Component Register;
2. every allocated parent system requirement is covered or explicitly returned
   to System Architecture as an unresolved allocation;
3. every used interface has a named producer, consumer, authority, version and
   failure behavior;
4. every requirement has measurable acceptance criteria and a complete
   verification-traceability row;
5. owned implementation logic has stable unit-test obligations, or a reasoned
   no-owned-logic/external-component exception is recorded;
6. normal, boundary, malformed, unavailable and recovery behavior is allocated
   to the appropriate verification level;
7. open decisions are visible and no target behavior is presented as current;
8. the documentation gate and repository tests pass.

## Open Issues

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| `<question, unknown or deferred dependency>` | `<requirements/tests affected>` | `<owner>` | `<when and by whom>` |

## Change Rules

- Editorial clarification preserves stable IDs.
- A material semantic replacement receives a new ID; the old definition is
  retained in a clearly labelled retired section with a replacement link.
- A changed interface, authority, lifecycle, trust boundary or data direction
  follows the Level-C architecture cascade before this package changes.
- A changed behavior inside accepted boundaries follows the Level-B cascade and
  updates requirements, obligations, tests and evidence together.
- Implementation test names may change, but accepted `UT-*` obligation IDs and
  their `REQ-*` mappings remain stable until deliberately retired.
