<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Local Demo Hosting and VM Route — Design Reviewed

- Decision: `D4-020`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.0.0`
- Subdecision state: prebuilt container topology and presentation packaging
  plus host/toolchain qualification policy and local demo container minimum
  security hygiene, native helper boundary and dual-VM route model accepted
  2026-08-23; simplified local functional transport accepted 2026-08-23;
  startup/shutdown and R0-local-data behavior accepted 2026-08-23

This package freezes the proposed first-demo local hosting shape. The Apple
Silicon Mac runs three prebuilt ARM64 containers: the stateless Software
Delivery Dashboard, the Brake Health Cloud product and the Tire Health Cloud
product. No image is built, pulled or repackaged during presentation.

Every image is ARM64 and referenced by immutable digest; `latest`, build and
pull fallback are forbidden. The stateless Software Delivery Dashboard re-reads
authoritative lifecycle state from AosCloud, while the native Demo Orchestrator
owns the current-run journal. Brake and Tire retain separate containers,
volumes, networks, namespaces, ports, healthchecks and failure boundaries.
Normal shutdown preserves functional volumes; only R0 may reset them after
their accepted exact backend cleanup.

Browser surfaces are published on macOS loopback only. Both AosVMs use the
already accepted QEMU user-network gateway `10.0.0.1` to reach separate Brake
and Tire local ingestion ports. Each Function Team has a separate API
namespace, container, volume and publication/helper capability.

Validation and Production VMs may run concurrently because each has an
independent QEMU user-network namespace. They may therefore both use guest
address `10.0.0.100` and host alias `10.0.0.1` without collision. Host-side
control ports/sockets remain unique per VM. Both VMs may be clients of the same
Brake/Tire backend ports, which correlate messages using `system_uid` rather
than source IP. Exactly one VM owns the live CARLA/Gateway source at a time.
The single Vehicle External Connectivity control applies only to that selected
vehicle and simultaneously removes its AosCloud and both functional-backend
routes; it preserves the other VM, the local in-vehicle data/advisory chain and
Mac-dashboard connectivity to AosCloud.

D4-022.1 realizes that separation with two QEMU network planes per VM: the
VDP-to-VISS/Gateway vehicle plane remains up, while one fixed native-helper QMP
operation changes only the external AosCloud/Brake/Tire plane. This requires a
successor OEM Demo Factory Image network configuration and launcher update,
not an upstream AosCore source change.

The local functional routes deliberately have no per-Unit client certificate
or backend credential lifecycle. A reported `system_uid` is used only for
demo correlation and exact cleanup; it is not presented as authenticated
backend identity. Production backend authentication is owned by each Function
Team and is outside the first-demo claim. Trust in this one controlled local
Mac route is not presented as production authentication. Separate endpoints,
schemas, containers and stores preserve product separation and reject a
cross-function message shape without claiming cryptographic client identity.
Signed FOTA/SOTA publication,
Aos IAM/KUKSA access and Gateway enforcement are unaffected.

The native non-root helper remains outside Docker. It owns protected local
credentials and exposes a loopback-only session API. Every dashboard backend
receives a distinct random session capability through a private file; the
browser receives none. Each capability is pre-bound to an allowlisted role,
profile and operation set, so callers cannot select a credential path, Cloud
URL, arbitrary candidate path, profile, HTTP method or shell command. The Demo
Launcher starts and supervises the helper only for the current session; it is
not installed as a persistent daemon. The helper does not own lifecycle state:
every successful mutation is reconciled through an independent AosCloud
re-read, while an ambiguous result becomes `UNCERTAIN` and is never blindly
retried. Session stop deletes all backend capabilities. This narrow boundary
is required because it protects real signing credentials and Cloud lifecycle
operations, not because the local demo data itself needs production hardening.

The exact host baseline observed for this review is Docker Desktop 4.87.0,
Engine 29.7.2, Compose 5.4.0 and QEMU 11.0.3 on ARM64. This becomes a first-demo
qualification baseline only after the container, guest route, restart and LAN
negative tests pass.

Host status is `QUALIFIED`, `COMPATIBLE_UNQUALIFIED` or `INCOMPATIBLE`.
Official presentation requires `QUALIFIED`; development may use the middle
state, while any engineering override is explicit, visible and forbidden in an
official presentation. macOS 26.5.2/25F84 is the observed host, not a universal
exact-version gate. QEMU 11.0.3 and 11.1.0 are allowlisted by the existing VM
machine contract. A new tool/OS combination requires complete qualification
and a manifest update, but not a container rebuild.

These containers are local demonstration infrastructure on one trusted Mac;
they are not a production deployment architecture. The first-demo security
baseline is therefore limited to low-cost hygiene: loopback-only publication,
no privileged mode, host networking, Docker socket, broad host-filesystem
mount or protected PKCS#12 mount, no real credential embedded in an image or
frontend, separate Brake/Tire data volumes, and non-root execution when the
selected image supports it without additional demo complexity. Read-only root
filesystems, dedicated tmpfs policy, local container RBAC, browser-to-backend
TLS, a production secret manager and production-grade container security
qualification are deliberately not first-demo requirements. Healthchecks,
digest pinning and controlled restart remain reproducibility and operability
rules. The security demonstrated by the solution remains signed FOTA/SOTA,
AosCloud lifecycle and OEM approval, AosCore isolation/quotas and in-vehicle
Service permission enforcement.

Files:

- [`local-demo-hosting-profile.v1.json`](local-demo-hosting-profile.v1.json) —
  ports, names, volumes, routes, helper/session and local-demo hygiene rules;
- [`fixtures/hosting-preflight.valid.json`](fixtures/hosting-preflight.valid.json)
  — proposed machine-readable preflight result.

This package authorizes no container start, credential creation, VM change,
Cloud call, signing, publication or deployment.

Implementation acceptance remains gated by clean and partial-failure startup,
container restart/persistence, helper-loss denial, normal shutdown, exact R0
cleanup, absence of post-shutdown session resources/listeners, both-VM
functional routes and LAN-negative evidence. These are qualification gates,
not unresolved design choices.
