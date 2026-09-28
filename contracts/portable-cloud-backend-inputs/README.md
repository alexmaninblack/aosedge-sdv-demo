<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable Cloud and backend inputs

- Status: Accepted Stage 2 implementation slice; integrated live gates deferred.
- Version: 1.0
- Prepared: 2026-09-26
- Owner: Demo Solution Team
- Parent: [distribution Stage 2](../../docs/planning/active/installable-distribution-and-reproducibility.md#stage-2-assemble-portable-demo-runtime-artifacts).

## Cloud worker selection

The existing artifact catalogue's fixed `cloud-runtime` directory selects the
assembled private Python 3.12/SDK closure. Absence preserves configured developer
Python; invalid presence fails closed without fallback. An independent source
lock pins the existing candidate manifest. Validate bounded regular files,
hashes, safe modes, no links and no undeclared files before worker execution.
Cache hashes only while each exact in-process filesystem identity is unchanged.
Do not install packages, upgrade SDKs, copy credentials or change trust stores.

Existing fixed workers, operation requests, certificate selection, OEM/SP roles,
Cloud authority, redaction, attempt/reconciliation and subprocess timeouts remain
unchanged. Launch with `-I -B` and the existing minimal environment. A private,
non-secret `AOSEDGE_CLOUD_RUNTIME` execution hint locates the unchanged pinned
SDK transition adapter; the child verifies both the source lock and its own
interpreter identity before loading it. Invalid hints cannot use developer
adapters. No hint or user environment is inherited from an unselected caller.

Full SDK checks run at worker dispatch, not while parsing UI configuration.
Background observations retain their existing asynchronous worker/cache path.
Failures are explicit unavailable observations or fixed local input errors,
never proof that credentials, permissions or the Cloud service failed. A local
input failure starts no worker, credential transfer or Cloud attempt. Validate
before marking a Unit mutation attempted and before the native IAM SSH forward.

## Backend selection

The fixed catalogue directory `backend-inputs` selects the already exported
untagged OCI archive and its independently source-pinned manifest. The source
lock also records the existing backend cleanup protocols. Exactly one immutable
Linux/arm64 image per team is selected; no latest tag, historical build timestamp,
developer Git tree or Docker build is used by this path.

Existing backend records remain authoritative for an existing run: selecting
new inputs must not upgrade a recorded backend. Explicit activation still
requires the existing owned stopped-container gate and preserves data/ownership.
Malformed selected inputs block candidate selection; ordinary observations,
Stop and recovery do not depend on an unused successor archive.

Start/activation still require the exact image already available in the declared
Docker-compatible engine. They never build, pull, load archives, start Docker
Desktop or alter another container. Archive integrity verification is read-only;
import/installation is a later explicit setup step, not a side effect of status
or navigation. The current container-runtime installation/licensing choice and
fresh-engine import remain open. Missing engine/image remains explicit.

## Gates and exclusions

Class B: source-independent input selection within existing owners. Affected:
worker launch sites, SDK adapter input resolution, backend candidate selection,
scenario/flow/requirements annotations and deterministic tests. Revalidated:
certificate/tenant authority, worker IPC operations, release continuity,
container ownership/data retention and all FOTA/SOTA/offline semantics.

Require positive and negative fixture coverage for absent/invalid selection,
changed pins/files, links/extra files, bounded manifests, unchanged requests and
timeouts, no fallback/build/load, preserved backend records and adapter identity.
Verify the actual assembled inputs without running current Docker/VM/CARLA or
using operator credentials. Reuse candidates; no Game/Factory rebuild or large
payload copy is required. Complete app assembly and later live UI, guest,
Cloud, fresh-engine and clean-Mac qualification remain separate gates.
