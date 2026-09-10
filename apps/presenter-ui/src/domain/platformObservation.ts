import type { TeamView } from "./model";

export interface PlatformCloudObservation {
  state: "CURRENT" | "STALE" | "UNAVAILABLE";
  observedAt: string | null;
  reason: string | null;
  value: null | {
    target: "test"; source: "Aos Cloud";
    online: string | null; lifecycle: string | null;
    installedVersion: string | null; pendingVersion: string | null;
    updateStatus: string | null; latestPublishedVersion: string | null;
    releases: { version: string; state: string | null }[];
    runtimeState: "NOT_REPORTED_BY_CLOUD";
    dataReadiness: "NOT_REPORTED_BY_CLOUD";
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
      details: { ...release.details, evidence: "Cloud release numbers do not identify v1/v2/v3 content profiles. This Cloud read does not report that mapping." } })),
  };
}
