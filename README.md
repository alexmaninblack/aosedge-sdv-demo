<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosEdge Platform SDV Lab

Explore how a vehicle can gain capabilities after production using the real
AosEdge platform. CARLA simulates the vehicle; an ARM64 virtual controller runs
AosCore, the vehicle data platform, and independent Brake and Tire advisory
services. Platform updates use Safe Stop-gated FOTA. Service containers have
their own SOTA lifecycle and do not control steering or braking.

## Choose your route

| I want to | Start here |
| --- | --- |
| Run the demo without compiling anything | [Install and run](docs/getting-started/installed-preview-cloud-first-use.md) |
| Build while reusing the heavy simulation dependency | [Developer build guide](docs/getting-started/reproduce-demo.md) |
| Understand what is simulated and what is real | [Product and component map](docs/architecture/product-map.md) |
| Change a component or contribute a fix | [Contribution guide](CONTRIBUTING.md) |

## Release status

**Engineering preview, not a qualified public release.** The new
`1.2.0-rc.1` build candidate has a complete DMG and privately delivered build
inputs. Fresh-environment installation and end-to-end qualification remain
open. Earlier Kit028 / Setup042 M1 results belong to that earlier package,
not automatically to the new candidate.

Read [release selection and access](docs/getting-started/release-status.md)
before choosing a package or source revision. Do not assume a proposed tag
already exists or that the repository contains downloadable binaries.

## Supported route

The installer targets Apple Silicon and macOS 26 or later. The recorded test
host is an M1 with 16 GiB RAM; this is a tested configuration, not a universal
performance minimum. Running needs Docker Desktop, approved Aos Cloud staging
access and sufficient storage. It does **not** need Unreal Editor, Xcode or a
source checkout. Setup reports the actual storage requirement.

The developer route builds project components on an external SSD using pinned
sources and verified prebuilt CARLA/native inputs. Rebuilding the engine is a
separate, currently gated [full-source route](docs/getting-started/full-source-build.md).

## More information

- [Troubleshooting](docs/getting-started/troubleshooting.md)
- [Documentation map](docs/README.md)
- [Implemented architecture](docs/architecture/current-implementation.md)
- [Qualification record](docs/qualification/current-baseline.md)

This repository owns integration, orchestration, contracts and system
documentation. Components retain their own repositories and lifecycles; the
build command prepares their pinned sources. There are no Git submodules and
no requirement to reconstruct old experiments.

## Security and license

Keep credentials, provisioned VM disks, operational data and compiled artifacts
out of Git. See [confidential source handling](docs/governance/confidential-source-handling.md).
Original integration work is MIT-licensed under `maninblack`; component and
third-party licenses remain separate. See [LICENSE](LICENSE) and
[third-party notices](THIRD_PARTY_NOTICES.md). Public source access does not
grant access to restricted engine source or permission to redistribute binaries.
