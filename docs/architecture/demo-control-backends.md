<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: backend ownership

Brake and Tire have separate service-owned backends and durable stores.
In this lab they run as Linux ARM64 Docker containers on the Mac, not inside
remote Aos Cloud. The [component map](product-map.md) and
[operator workflow](../operations/current-demo-workflow.md) show the current system.

## Runtime boundary

Installed media supplies the reviewed backend image set. Setup prepares those
images in an already available local Engine; ordinary runtime start reuses
them. Starting a backend is not a build, pull, image activation or Engine start.
The development-only backend build/activation primitives are not operator
installation steps.

Demo Control owns exact container/network/context identities and journaled
operations. Conflicts are not adopted. Lost responses are reconciled before
another mutation. Private instance state and credentials are not exported
through the read-only current-Test context.

## Results and lifecycle

A healthy container does not prove current-vehicle context, service execution,
fresh products or a driver warning. Presenter queries current-Test-scoped
products, observations and history through existing team APIs.
[Brake wire/API](../../contracts/brake-cloud-api/README.md) and
[Tire current wire](../../contracts/tire-cloud-api/studio-current-wire.md)
remain authoritative. The legacy Tire cleanup schema is not the current
one-Test cleanup contract; see [protocol status](../../contracts/implementation-status.md).

Stop demo and keep data stops the two owned backend containers and preserves
their state. Start controller restores the retained Test and backends.
Confirmed Test retirement alone removes exact run-scoped data, preserving
peer/unrelated records. Docker Engine is shared infrastructure and stays running.
