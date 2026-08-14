<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Repository Boundary Qualification

## Accepted Result

R-5 passed on 2026-08-14. The result qualifies repository ownership and static
dependency direction only. It does not claim that the AOS-2 provider or AOS-3
telemetry consumer has been implemented.

## Qualified Inputs

| Repository | Revision |
| --- | --- |
| `carla-aosedge-integration` candidate gate | `62266dd0b603d45d0b6e2d4ada0398ab4a6d3968` |
| `carla-ego-runtime` | `3fcf1fac52151f30bf04bd3b5c5d67bfd8526aa1` |
| `aos-vehicle-platform` | `4637864297fa42bed3ae1a553bae13fc57d14c79` |
| `vehicle-telemetry-service` | `f4bd0bf49c7601af31dcad83038999bd74a90f56` |

The accepted `components/baseline.lock.json` records upstream AosVM, KUKSA,
VSS, project source, contract, and package-template revisions and digests.

## Evidence

The same qualification gate passed in two independent environments:

1. four new public Git clones in an empty temporary workspace; and
2. GitHub Actions run
   [`31788300464`](https://github.com/alexmaninblack/carla-aosedge-integration/actions/runs/31788300464).

Both runs verified:

- clean work trees and no Git submodules;
- MIT licensing for integration and Apache-2.0 licensing, exact `maninblack`
  notices, DCO policy, and REUSE 3.3 compliance for both new repositories;
- no tracked credential, certificate, binary artifact, private URL, personal
  absolute path, or restricted Unreal/CARLA asset;
- platform independence from service source;
- service independence from CARLA/VISS endpoints, provider source, VM launch,
  and provisioning implementation;
- integration ownership of exact pins and orchestration rather than provider
  or service implementation;
- contract, unit, repository-policy, boundary, and component-lock tests;
- exact project checkout revisions and locked repository-file digests.

REUSE tool 6.2.0 with its charset-normalizer option was used for the local
license checks. The GitHub workflow pins all checkout actions and all project
revisions to full commit identifiers.

## Decision

Accept `repository-separation-r5-accepted-1`. R-0 through R-5 are complete and
R-6/AOS-2 may begin in `aos-vehicle-platform`. Any component revision or
artifact digest change creates a new candidate lock and requires this gate
again.
