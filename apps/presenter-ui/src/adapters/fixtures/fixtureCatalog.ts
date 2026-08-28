import type {
  Observed,
  PresenterSnapshot,
  QualificationView,
  ReleaseStage,
  ReleaseView,
  TeamId,
  TeamView,
  VehicleRole,
} from "../../domain";

const FIXTURE_TIME = "2026-08-28T10:00:00.000Z";

function observed<T>(owner: string, system: string, value: T): Observed<T> {
  return {
    value,
    source: { owner, system, fixture: true },
    observedAt: FIXTURE_TIME,
    state: "CURRENT",
  };
}

function stages(team: TeamId, state: ReleaseStage["state"] = "current"): ReleaseStage[] {
  const producer = team === "platform" ? "Platform Team" : team === "brake" ? "Brake Team" : "Tire Team";
  return [
    {
      id: "publish",
      label: "Producer Team publishes candidate",
      actor: producer,
      state,
      explanation: "Inspect the prepared immutable candidate, sign it through the fixed producer profile and submit it once.",
      action: "Sign and submit prepared candidate",
    },
    {
      id: "test-authorize",
      label: "Authorize Test Vehicle deployment",
      actor: "OEM Release Authority",
      state: "ready",
      explanation: "The independent authority reviews the exact candidate, evidence and effective Test recipient before AosCloud execution.",
      action: "Authorize Test Vehicle deployment",
    },
    {
      id: "test-accept",
      label: "Test Vehicle validation and Producer Team acceptance",
      actor: producer,
      state: "ready",
      explanation: "Validation ends on the Test Vehicle. The producer accepts the exact evidence before Production authorization.",
      action: "Run Test Vehicle exercise",
    },
    {
      id: "production-authorize",
      label: "Authorize Production rollout",
      actor: "OEM Release Authority",
      state: "ready",
      explanation: "Authorize the identical accepted artifact for the Production Vehicle after an explicit source handover.",
      action: "Authorize Production rollout",
    },
    {
      id: "production-live",
      label: "Production rollout and live operation",
      actor: "Production Vehicle",
      state: "ready",
      explanation: "Show ordinary released behavior. This is live operation, not a second validation lane.",
      action: "Show released behavior",
    },
  ];
}

function release(
  team: TeamId,
  version: number,
  subtitle: string,
  dependency?: string,
): ReleaseView {
  const family = team === "platform" ? "VDP" : team === "brake" ? "Brake" : "Tire";
  const isPlatform = team === "platform";
  return {
    id: `${team}-v${version}`,
    version,
    title: `${family} v${version}`,
    subtitle,
    team,
    motionPolicy: isPlatform ? "Safe Stop required" : "In-motion update allowed",
    dependency,
    status: version === 1 ? "Test authorization ready" : "Prepared",
    stages: stages(team),
    details: {
      summary: subtitle,
      artifact: `${family.toLowerCase()}-v${version}.oci · immutable prepared candidate`,
      digest: `sha256:${String(version).repeat(8)}…${team}-reviewed`,
      dependency: dependency ?? "OEM component runtime and fresh Safe Stop evidence",
      access: isPlatform
        ? "OEM-owned provider capability; no Service quota applies."
        : "Read only the approved vehicle signals and write only the reviewed advisory path.",
      ...(isPlatform ? {} : { quota: team === "brake" ? "CPU 35% · Memory 192 MiB · Storage 64 MiB" : "CPU 20% · Memory 128 MiB · Storage 48 MiB" }),
      target: "Test Vehicle · Verification Unit Set",
      evidence: "Exact candidate, target, verification and validation evidence; private identities are fingerprinted.",
    },
  };
}

function team(
  id: TeamId,
  purpose: string,
  releases: ReleaseView[],
  evidenceTitle: string,
  evidenceBody: string,
): TeamView {
  const name = id === "platform" ? "Platform Team" : id === "brake" ? "Brake Team" : "Tire Team";
  return {
    id,
    name,
    purpose,
    compactStatus: releases[0]?.status ?? "Prepared",
    productStatus: id === "platform" ? "VDP v—" : "Service v—",
    lifecycleStatus: "Prepared · independently viewable",
    source: observed(id === "platform" ? "AosEdge Platform" : `${name} Function Backend`, "Deterministic fixture", "Current fixture projection"),
    evidenceTitle,
    evidenceBody,
    backendStatus: id === "platform" ? "AosEdge state current" : "Connected · no derived events yet",
    ...(id === "platform" ? {} : { quota: releases[0]?.details.quota }),
    ...(id === "tire"
      ? {
          isolation: {
            status: "Ready for proof",
            tireCpu: "18%",
            brake: "Healthy",
            platform: "Healthy",
          },
        }
      : {}),
    releases,
  };
}

function qualification(status: QualificationView["status"], reason: string): Observed<QualificationView> {
  return observed("System Acceptance", "Sealed qualification fixture", { status, reason });
}

function baseSnapshot(): PresenterSnapshot {
  return {
    fixtureId: "ready",
    fixtureLabel: "Deterministic fixture · not live AosEdge state",
    observedAt: FIXTURE_TIME,
    vehicle: observed("Demo Orchestrator", "Exclusive live-source fixture", "test"),
    workspace: observed("Presenter Launcher", "Measured-workspace fixture", "READY"),
    global: {
      qualification: qualification("QUALIFIED", "Exact fixture baseline is ready for presentation review. No manual override exists."),
      stage: "G0",
      manufactured: true,
      provisioned: true,
      recovery: "No interrupted operation",
      milestone: "G3 capability · 0 of 2 releases ready",
    },
    teams: {
      platform: team(
        "platform",
        "Builds and releases the shared Vehicle Data Platform Component.",
        [
          release("platform", 1, "Baseline read-only braking telemetry contract"),
          release("platform", 2, "Backward-compatible inputs for local brake analysis"),
          release("platform", 3, "Tire telemetry and controlled advisory path"),
        ],
        "Platform capability view",
        "Shows the exact VDP capability reported for the Current Vehicle. Service quota fields are intentionally absent.",
      ),
      brake: team(
        "brake",
        "Develops and releases predictive brake-maintenance Services.",
        [
          release("brake", 1, "Bounded pre/active/post braking window", "Requires VDP v1 or newer"),
          release("brake", 2, "Local derived assessment and event", "Requires VDP v2 or newer"),
          release("brake", 3, "Maintenance advisory and bounded backend state", "Requires VDP v3 or newer"),
        ],
        "Brake Health Function Backend",
        "Current released Brake evidence remains separate from Platform and Tire state.",
      ),
      tire: team(
        "tire",
        "Develops and releases predictive tire-maintenance Services.",
        [release("tire", 1, "Local tire condition and maintenance advisory", "Requires VDP v3 or newer")],
        "Tire Health Function Backend",
        "Tire condition evidence and the bounded isolation proof remain owned by the Tire product.",
      ),
    },
    assetFailure: false,
    eventChain: [
      "Vehicle event · deterministic Test exercise",
      "Signals · Gateway/KUKSA observation current",
      "On-vehicle behavior · local Service result",
      "Driver/backend result · correlated fixture fingerprint",
    ],
    redactionNotice: "Allowlisted fixture only · credentials, raw responses, private paths and private identities are excluded.",
  };
}

function clone(): PresenterSnapshot {
  return structuredClone(baseSnapshot());
}

const catalog: Record<string, () => PresenterSnapshot> = {
  ready: baseSnapshot,
  blocked: () => {
    const value = clone();
    value.fixtureId = "blocked";
    value.teams.brake.releases[1]!.status = "Blocked · requires VDP v2";
    value.teams.brake.releases[1]!.stages[1]!.state = "blocked";
    value.teams.brake.releases[1]!.stages[1]!.explanation = "Deployment blocked by missing VDP v2. Candidate remains visible and inspectable.";
    return value;
  },
  stale: () => {
    const value = clone();
    value.fixtureId = "stale";
    value.teams.platform.source.state = "STALE";
    value.teams.platform.source.reason = "Last observation is outside the accepted freshness window.";
    value.teams.platform.compactStatus = "Stale authoritative state";
    return value;
  },
  submitting: () => {
    const value = clone();
    value.fixtureId = "submitting";
    value.teams.platform.releases[0]!.stages[0]!.state = "submitting";
    value.teams.platform.compactStatus = "VDP v1 · SUBMITTING";
    return value;
  },
  uncertain: () => {
    const value = clone();
    value.fixtureId = "uncertain";
    value.teams.brake.releases[0]!.stages[0]!.state = "uncertain";
    value.teams.brake.compactStatus = "Brake v1 · UNCERTAIN";
    value.global.recovery = "Outcome unknown · authoritative reconciliation required · blind retry unavailable";
    return value;
  },
  reconciling: () => {
    const value = catalog.uncertain!();
    value.fixtureId = "reconciling";
    value.teams.brake.releases[0]!.stages[0]!.state = "reconciling";
    value.teams.brake.compactStatus = "Brake v1 · RECONCILING";
    return value;
  },
  failed: () => {
    const value = clone();
    value.fixtureId = "failed";
    value.teams.tire.releases[0]!.stages[0]!.state = "failed";
    value.teams.tire.compactStatus = "Tire v1 · FAILED";
    value.teams.tire.source.state = "ERROR";
    value.teams.tire.source.reason = "Tire-owned fixture source unavailable. Platform and Brake remain current.";
    return value;
  },
  unavailable: () => {
    const value = clone();
    value.fixtureId = "unavailable";
    value.vehicle.value = "unavailable";
    value.vehicle.state = "UNAVAILABLE";
    value.vehicle.reason = "Exclusive source handover is not proven. Reconcile the exact handover.";
    return value;
  },
  changing: () => {
    const value = clone();
    value.fixtureId = "changing";
    value.vehicle.value = "changing";
    value.vehicle.reason = "Stable stop, detach, reset generation and fresh evidence are in progress.";
    return value;
  },
  production: () => {
    const value = clone();
    value.fixtureId = "production";
    value.vehicle.value = "production";
    for (const teamValue of Object.values(value.teams)) {
      teamValue.productStatus = teamValue.id === "platform" ? "VDP v1" : "Service v1";
      teamValue.releases[0]!.status = "Production ready · live operation";
      teamValue.releases[0]!.stages.forEach((stage) => { stage.state = "complete"; });
    }
    value.global.stage = "ACTIVE";
    value.global.milestone = "G3 capability · 2 of 2 releases ready";
    return value;
  },
  "safe-stop": () => {
    const value = clone();
    value.fixtureId = "safe-stop";
    value.teams.platform.releases[0]!.status = "AosEdge Platform: ACTIVATING";
    value.teams.platform.releases[0]!.stages[1]!.state = "waiting";
    value.teams.platform.releases[0]!.stages[1]!.explanation = "Vehicle Gateway: Safe Stop not established · Waiting for Safe Stop before application. Previous healthy release remains active.";
    return value;
  },
  offline: () => {
    const value = clone();
    value.fixtureId = "offline";
    value.teams.brake.backendStatus = "No new backend events · vehicle external connectivity OFF";
    value.teams.brake.evidenceBody = "Local analysis and driver advisory remain available. Current queue occupancy is not observable while offline.";
    value.teams.tire.backendStatus = "No new backend events · vehicle external connectivity OFF";
    value.teams.tire.evidenceBody = "Last observed backend result remains labelled; no zero-loss or queue-count claim is made.";
    return value;
  },
  reconnected: () => {
    const value = catalog.offline!();
    value.fixtureId = "reconnected";
    value.teams.brake.backendStatus = "Synchronizing · awaiting owner acknowledgement";
    value.teams.tire.backendStatus = "Synchronized · bounded owner summary received";
    return value;
  },
  "asset-failure": () => {
    const value = clone();
    value.fixtureId = "asset-failure";
    value.assetFailure = true;
    return value;
  },
  m0: () => {
    const value = clone();
    value.fixtureId = "m0";
    value.vehicle.value = "not-assigned";
    value.global.stage = "M0";
    value.global.manufactured = true;
    value.global.provisioned = false;
    return value;
  },
  m1: () => {
    const value = clone();
    value.fixtureId = "m1";
    value.global.stage = "M1";
    value.global.manufactured = true;
    value.global.provisioned = true;
    return value;
  },
  r0: () => {
    const value = clone();
    value.fixtureId = "r0";
    value.vehicle.value = "not-assigned";
    value.global.stage = "R0";
    value.global.manufactured = false;
    value.global.provisioned = false;
    value.global.recovery = "R0 complete · READY_FOR_M0 · no automatic M0 or M1";
    return value;
  },
  recovery: () => {
    const value = clone();
    value.fixtureId = "recovery";
    value.vehicle.value = "unavailable";
    value.global.stage = "RECOVERY_REQUIRED";
    value.global.recovery = "Reset incomplete · Recovery required · resume from first unproven step";
    return value;
  },
  "qualification-absent": () => {
    const value = clone();
    value.fixtureId = "qualification-absent";
    value.global.qualification = qualification("ABSENT", "No current sealed qualification dossier is available.");
    return value;
  },
  "qualification-stale": () => {
    const value = clone();
    value.fixtureId = "qualification-stale";
    value.global.qualification = qualification("STALE", "The sealed dossier does not match the current fixture baseline.");
    return value;
  },
  "qualification-withdrawn": () => {
    const value = clone();
    value.fixtureId = "qualification-withdrawn";
    value.global.qualification = qualification("WITHDRAWN", "System Acceptance withdrew this baseline after review.");
    return value;
  },
  "not-qualified": () => {
    const value = clone();
    value.fixtureId = "not-qualified";
    value.global.qualification = qualification("NOT_QUALIFIED", "Required fixture evidence has not passed.");
    return value;
  },
};

export const fixtureIds = Object.freeze(Object.keys(catalog));

export function fixtureById(id: string): PresenterSnapshot {
  return (catalog[id] ?? catalog.ready)!();
}
