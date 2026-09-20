import type { TeamView, ServiceRelease } from "./model";

export interface CloudSection<T> { value: T | null; state: string; reason?: string | null; readCompletedAt?: string; lastKnownReadCompletedAt?: string }
export interface InstalledProfile { state: "CURRENT" | "STALE" | "UNKNOWN"; profile: "v1" | "v2" | "v3" | null; releaseVersion: string | null; cloudVersionId: string | null; source: "CLOUD_INSTALLATION_AND_PACKAGE"; reason: string | null }
export interface CloudComponent { installedProfile?: InstalledProfile; reported_component_id: string | null; type: string | null; installed_component: { id?: string | null; version: string | null } | null; pending_component: { version: string | null } | null; pending_component_status: string | null; pending_component_error?: string | null; runtimeState: string }
export interface CloudService { reportReadCompletedAt?: string | null; subject?: string | null; error_message?: string | null; error_aos_code?: number | null; error_exit_code?: number | null; service: { id: string; title: string | null } | null; num_instance: number | null; service_versions: { installed_service_version: { version: string | null } | null; pending_service_version: { version: string | null } | null; pending_service_version_id?: string | null; pending_service_version_status?: string | null } | null; instances: CloudSection<{ instance_id: number | null; version: string | null; run_state: string | null; error_message: string | null; error_aos_code?: number | null; error_exit_code?: number | null; node_id?: string | null }[]> }
export interface CloudInventory { unitId: string; systemUid: string; teamServiceIds?: Partial<Record<"brake" | "tire", string>>; readCompletedAt: string; components: CloudSection<CloudComponent[]>; services: CloudSection<CloudService[]>; nodes: CloudSection<{ node_id: string | null; status: string | null; num_cpus: number | null; max_dmips: number | null; total_ram: number | null }[]>; layers: CloudSection<unknown[]>; assignedSubjects: CloudSection<unknown[]> }

export interface PlatformCloudObservation {
  serviceReleases?: ServiceRelease[];
  serviceReleasesState?: string;
  state: "CURRENT" | "STALE" | "UNAVAILABLE";
  observedAt: string | null;
  reason: string | null;
  bindingKey?: string;
  publication?: { version: string; stage: string; observedAt?: string; reason?: string | null } | null;
  publications?: { version: string; stage: string; observedAt?: string; reason?: string | null }[];
  value: null | {
    target: "test"; source: "Aos Cloud";
    online: string | null; lifecycle: string | null;
    installedVersion: string | null; pendingVersion: string | null;
    installedProfile?: InstalledProfile;
    updateStatus: string | null; latestPublishedVersion: string | null;
    releases: { version: string; state: string | null }[];
    runtimeState: "NOT_REPORTED_BY_CLOUD";
    dataReadiness: "NOT_REPORTED_BY_CLOUD";
    inventory?: CloudInventory;
  };
}

export function projectCloudPlatform(team: TeamView, cloud: PlatformCloudObservation | null): TeamView {
  const current = cloud?.state === "CURRENT";
  const value = cloud?.value;
  const lastKnown = value && !current ? " · last known" : "";
  return { ...team,
    productStatus: value?.installedVersion ? `VDP ${value.installedVersion} · Cloud installed${lastKnown}` : current ? "No installed release reported" : "Cloud state not current",
    lifecycleStatus: value?.pendingVersion ? `Pending ${value.pendingVersion}${lastKnown}` : current ? "No pending release reported" : "Refresh Cloud state",
    evidenceTitle: "Test Vehicle · Aos Cloud",
    backendStatus: current ? value?.online ?? "Unknown" : cloud?.state ?? "Not observed",
    evidenceBody: "Installed is the Cloud-reported state. Running process, live-data readiness and Safe Stop are not reported by this Cloud read; no direct VM probe is made.",
    source: { value: value ? `Cloud state received${lastKnown}` : null, state: cloud?.state ?? "UNAVAILABLE",
      observedAt: cloud?.observedAt ?? null, source: { owner: "Aos Cloud", system: "Unit and component API", fixture: false },
      ...(!current ? { reason: cloud?.state === "STALE" ? "Previous observation — refresh required" : "Cloud state unavailable" } : {}) },
    releases: team.releases.map((release) => ({ ...release, status: "Content profile reference",
      details: { ...release.details, evidence: "Release numbers do not identify v1/v2/v3 profiles. Installed profiles require exact Cloud installation and package evidence; unresolved bindings remain unconfirmed." } })),
  };
}
