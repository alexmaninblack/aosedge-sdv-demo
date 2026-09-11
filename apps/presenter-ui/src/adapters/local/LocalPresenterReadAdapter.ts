import type { LocalDemoView, Observed, PresenterReadPort, PresenterSnapshot, ReleaseStage, TeamId, TeamView, VehicleRole, PlatformCloudObservation } from "../../domain";

let monitoringFlight: Promise<unknown> | null = null;
export function readCloudMonitoring(): Promise<unknown> {
  if (!monitoringFlight) monitoringFlight = fetch("/api/presenter/monitoring", { cache: "no-store", signal: AbortSignal.timeout(65000) })
    .then((response) => { if (!response.ok) throw new Error("CLOUD_MONITORING_UNAVAILABLE"); return response.json(); })
    .finally(() => { monitoringFlight = null; });
  return monitoringFlight;
}

export async function readBackendObservation(team: "brake" | "tire", signal: AbortSignal): Promise<unknown> {
  const endpoint = team === "brake" ? "/api/presenter/backend/brake" : "/api/presenter/backend/tire";
  const response = await fetch(endpoint, { cache: "no-store",
    signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]) });
  if (!response.ok) throw new Error("BACKEND_UNAVAILABLE");
  return response.json();
}

const deferred = "Production FOTA is unavailable in the current Aos platform release. Production remains outside the verification set.";
const profiles = [
  "Baseline read-only braking telemetry",
  "Backward-compatible signals for local brake analysis",
  "Tire telemetry and the advisory interface",
];

function observed<T>(value: T | null, time: string | null, reason?: string): Observed<T> {
  return { value, source: { owner: "Demo Control", system: "Local observation", fixture: false },
    observedAt: time, state: reason ? "UNAVAILABLE" : "CURRENT", ...(reason ? { reason } : {}) };
}

function teams(): Record<TeamId, TeamView> {
  const result = {} as Record<TeamId, TeamView>;
  for (const id of ["platform", "brake", "tire"] as const) {
    const platform = id === "platform";
    const name = `${id[0].toUpperCase()}${id.slice(1)} Team`;
    result[id] = { id, name,
      purpose: platform ? "Vehicle Data Platform evolution" : "Service integration follows the Platform pass",
      compactStatus: platform ? "Test Vehicle pass" : "Not connected",
      productStatus: "Not observed", lifecycleStatus: platform ? "Test only · Production FOTA deferred" : "Not connected in this increment",
      source: observed<string>(null, null, "Use explicit Cloud/guest reads; background refresh is local only"),
      evidenceTitle: platform ? "VDP on Test Vehicle" : "Service integration not connected",
      evidenceBody: platform ? "Cloud acceptance, installation, running process and live data will be shown separately. A successful upload is not proof that VDP is running." : "This perspective remains available for navigation. No service status or successful action is simulated.",
      backendStatus: "NOT OBSERVED",
      releases: platform ? profiles.map((subtitle, index) => {
        const version = index + 1;
        const stages: ReleaseStage[] = [
          { id: "publish", label: "Prepare, sign and publish candidate", actor: name, state: "blocked",
            explanation: "Use the v" + version + " content profile with a new, increasing Cloud release number in Test VDP operations above. This card describes the workflow; operation receipts show actual results." },
          { id: "test-authorize", label: "Authorize Test Vehicle deployment", actor: "OEM Release Authority", state: "blocked",
            explanation: "Approve the exact verification batch separately from publication." },
          { id: "test-accept", label: "Validate on Test Vehicle", actor: name, state: "blocked",
            explanation: "While driving, the update waits. After native Safe Stop, confirm installed version, running VDP and live data; then review the result visually." },
          { id: "production-authorize", label: "Authorize Production rollout", actor: "OEM Release Authority", state: "blocked", explanation: deferred },
          { id: "production-live", label: "Production rollout and live operation", actor: "Production Vehicle", state: "blocked", explanation: "Deferred until the platform supports delivery to the Production Unit Set." },
        ];
        return { id: `platform-v${version}`, version, title: `VDP v${version}`, subtitle, team: id,
          motionPolicy: "Safe Stop required" as const, status: "Not observed", stages,
          details: { summary: subtitle, artifact: "No release selected", digest: "Not observed",
            dependency: "OEM component runtime and fresh Safe Stop evidence", access: "OEM Platform component; no Service quota",
            target: "Test Vehicle · Test Vehicles verification set", evidence: "Workflow reference; see timestamped operation results for actual evidence" } };
      }) : [],
    };
  }
  return result;
}

export function composeLocalSnapshot(data?: LocalDemoView & { observedAt: string; mode: string }, reason?: string): PresenterSnapshot {
  const unavailable = reason ?? (data ? undefined : "Waiting for Demo Control");
  const emptyVehicle = { state: "UNKNOWN", reason: unavailable ?? null, process: null, imageVersion: null, overlayExists: null };
  const localDemo: LocalDemoView = data ? { ...data, available: true } : { available: false, images: [],
    vehicles: { test: emptyVehicle, production: emptyVehicle }, source: { state: "UNKNOWN", currentVehicle: null }, access: {} };
  const source = data?.source;
  // The lightweight endpoint reports the accepted assignment without opening
  // another guest connection. A missing live probe is not an empty assignment.
  const selected = source?.selectedVehicle ?? source?.currentVehicle;
  const conflicting = Boolean(source?.selectedVehicle && source.currentVehicle && source.selectedVehicle !== source.currentVehicle);
  const stable = source && ["SELECTED_NOT_PROBED", "CONNECTED"].includes(source.state) && !source.reason && !conflicting;
  const unassigned = source && ["NOT_PREPARED", "RUNNING_UNASSIGNED", "DETACHED", "STOPPED"].includes(source.state)
    && !source.currentVehicle && !source.selectedVehicle;
  const vehicle: VehicleRole = stable && (selected === "test" || selected === "production") ? selected : unassigned ? "not-assigned" : "unavailable";
  const manufactured = Boolean(data && Object.values(data.vehicles).every((item) => item.state === "CURRENT" && item.overlayExists));
  return { localDemo, fixtureId: "local", fixtureLabel: "Local Demo Control · explicit protected actions", observedAt: data?.observedAt ?? "",
    vehicle: observed(vehicle, data?.observedAt ?? null, unavailable ?? (vehicle === "unavailable" ? source?.reason ?? "Vehicle assignment is unavailable" : undefined)),
    workspace: observed("INCOMPLETE", null, "Native window composition not yet confirmed"),
    global: { qualification: observed({ status: "NOT_QUALIFIED", reason: "UI integration is under review. The accepted .31 Test result is not qualification of this new UI." }, null),
      stage: !data ? "RECOVERY_REQUIRED" : manufactured ? "M0" : "READY_FOR_M0", manufactured, provisioned: false,
      recovery: unavailable ?? "Mutations require explicit confirmation; no automatic retries",
      milestone: "Two-VM preparation · Test-only VDP updates · Production FOTA deferred" },
    teams: teams(), assetFailure: false, eventChain: [],
    redactionNotice: "Local observations only. No credentials, helper capabilities or filesystem paths are sent to the browser." };
}

export class LocalPresenterReadAdapter implements PresenterReadPort {
  private platformRead: Promise<PlatformCloudObservation> | null = null;

  readPlatform(): Promise<PlatformCloudObservation> {
    if (this.platformRead) return this.platformRead;
    this.platformRead = (async (): Promise<PlatformCloudObservation> => {
      try {
        const response = await fetch("/api/presenter/platform", { signal: AbortSignal.timeout(35000), cache: "no-store" });
        if (!response.ok) throw new Error("unavailable");
        const value: PlatformCloudObservation = await response.json();
        if (!["CURRENT", "UNAVAILABLE"].includes(value.state) || typeof value.observedAt !== "string"
            || (value.state === "CURRENT" && (value.value?.source !== "Aos Cloud" || value.value.target !== "test"
              || !Array.isArray(value.value.releases) || value.value.runtimeState !== "NOT_REPORTED_BY_CLOUD"
              || value.value.dataReadiness !== "NOT_REPORTED_BY_CLOUD"))) throw new Error("invalid");
        return value;
      } catch {
        return { state: "UNAVAILABLE", observedAt: null, value: null, reason: "AOS_CLOUD_STATE_UNAVAILABLE" };
      }
    })().finally(() => { this.platformRead = null; });
    return this.platformRead;
  }

  async read(): Promise<Readonly<PresenterSnapshot>> {
    try {
      const response = await fetch("/api/presenter/snapshot", { signal: AbortSignal.timeout(8000), cache: "no-store" });
      if (!response.ok) throw new Error("unavailable");
      const data = await response.json();
      if (data.mode !== "LOCAL_READ_ONLY" || !data.vehicles?.test || !data.vehicles?.production || !data.source
          || !Array.isArray(data.images) || typeof data.observedAt !== "string" || !data.access) throw new Error("invalid");
      return composeLocalSnapshot(data);
    } catch {
      // Do not retain old greens or silently substitute fixture facts.
      return composeLocalSnapshot(undefined, "Demo Control is unavailable — no current state can be confirmed");
    }
  }

  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => { timer = setTimeout(async () => {
      if (document.visibilityState === "visible") {
        const snapshot = await this.read();
        if (!stopped) listener(snapshot);
      }
      if (!stopped) schedule();
    }, 10000); };
    schedule();
    return () => { stopped = true; clearTimeout(timer); };
  }
}
