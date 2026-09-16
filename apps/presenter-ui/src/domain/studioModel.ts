import type { LocalDemoView, ServiceRelease } from "./model";
import type { CloudService, PlatformCloudObservation } from "./platformObservation";
import type { DemoJob } from "./presenterCommandPort";

export type Profile = "v1" | "v2" | "v3";
export type ServiceTeam = "brake" | "tire";
export const versionOrder = (a: string, b: string) => a.localeCompare(b, undefined, { numeric: true });
export function serviceReleases(local: LocalDemoView, cloud?: PlatformCloudObservation | null): ServiceRelease[] {
  const rows = new Map((local.serviceReleases ?? []).map(row => [row.releaseHandle, row]));
  for (const row of cloud?.serviceReleases ?? []) {
    const previous = rows.get(row.releaseHandle);
    if (previous?.cloudDomain && row.cloudDomain !== previous.cloudDomain) continue;
    if (!previous || (row.publication.observedAt ?? "") >= (previous.publication.observedAt ?? "")) rows.set(row.releaseHandle,
      previous ? { ...row, signed: previous.signed } : row);
  }
  return [...rows.values()];
}
export function teamService(team: ServiceTeam, observation?: PlatformCloudObservation | null): CloudService | undefined {
  const inventory = observation?.value?.inventory;
  const id = inventory?.teamServiceIds?.[team];
  return id ? inventory?.services.value?.find(row => row.service?.id === id) : undefined;
}
export function serviceProfile(row: CloudService | undefined, releases: ServiceRelease[]): Profile | undefined {
  return releases.find(release => release.serviceId === row?.service?.id
    && release.version === row?.service_versions?.installed_service_version?.version)?.contentProfile;
}
export function serviceCandidate(local: LocalDemoView, releases: ServiceRelease[], jobs: DemoJob[], team: ServiceTeam, profile: Profile): ServiceRelease | undefined {
  const prepared = jobs.filter(job => job.runId === local.runId && job.action === "service-prepare" && job.state === "COMPLETED"
    && job.team === team && job.profile === profile && job.release && job.version).map(job => ({
      releaseHandle: job.release!, team, contentProfile: profile, version: job.version!, runId: job.runId,
      serviceId: job.serviceId ?? null, signed: false, submitted: false,
      demoMockedData: job.results.find(result => result.operation === "service.prepare")?.facts.demoMockedData !== false,
      publication: {},
    } as ServiceRelease));
  const merged = new Map(prepared.map(row => [row.releaseHandle, row]));
  for (const row of releases) if (row.runId === local.runId && local.runId && row.team === team && row.contentProfile === profile) merged.set(row.releaseHandle, row);
  return [...merged.values()].sort((a, b) => versionOrder(a.version, b.version)).at(-1);
}

export interface MetricSample { value: number | null; time: string | null; nodeId?: string | null; serviceId?: string | null; subjectId?: string | null; instance?: number | null; partition?: string | null; measurementType?: string | null; parameter?: string | null }
export function metricScope(sample: MetricSample): string {
  if (sample.serviceId || sample.subjectId || sample.instance !== null && sample.instance !== undefined) return "Service instance";
  return sample.nodeId ? "Controller" : "Unspecified scope";
}
export function groupedMetrics(samples: MetricSample[]): { key: string; scope: string; sample: MetricSample }[] {
  const groups = new Map<string, MetricSample>();
  for (const sample of samples) {
    const key = JSON.stringify([sample.nodeId ?? null, sample.serviceId ?? null, sample.subjectId ?? null,
      sample.instance ?? null, sample.partition ?? null, sample.parameter ?? null, sample.measurementType ?? null]);
    if (!groups.has(key) || (sample.time ?? "") > (groups.get(key)?.time ?? "")) groups.set(key, sample);
  }
  return [...groups].map(([key, sample]) => ({ key, scope: metricScope(sample), sample }));
}
