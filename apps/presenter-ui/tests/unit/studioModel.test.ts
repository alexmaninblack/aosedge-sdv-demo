import { expect, test } from "vitest";
import { groupedMetrics, serviceCandidate, serviceProfile, serviceReleases } from "../../src/domain/studioModel";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import type { ServiceRelease } from "../../src/domain/model";
import type { CloudService, PlatformCloudObservation } from "../../src/domain/platformObservation";
import type { LocalDemoView } from "../../src/domain/model";
import type { DemoJob } from "../../src/domain/presenterCommandPort";

test("prepared service data mode follows the command receipt before inventory refresh", () => {
  const local = { runId: "current-run" } as LocalDemoView;
  for (const demoMockedData of [false, true]) {
    const job: DemoJob = { id: "prepare-fixture", startedAt: "2026-09-15T12:00:00Z", progress: [],
      runId: "current-run", action: "service-prepare", state: "COMPLETED",
      team: "brake", profile: "v1", release: "brake/42.0.0", version: "42.0.0",
      results: [{ operation: "service.prepare", state: "COMPLETED", message: "Prepared", facts: { demoMockedData } }] };
    expect(serviceCandidate(local, [], [job], "brake", "v1")?.demoMockedData).toBe(demoMockedData);
  }
});

test("certificate rotation cannot restore Signed from an older Cloud observation", () => {
  const current = { releaseHandle: "brake/12.0.0", cloudDomain: "staging.example.test", signed: false,
    submitted: true, publication: { stage: "READY", observedAt: "2026-09-15T10:00:00Z" } } as ServiceRelease;
  const local = { serviceReleases: [current] } as LocalDemoView;
  const cached = { serviceReleases: [{ ...current, signed: true }] } as PlatformCloudObservation;
  expect(serviceReleases(local, cached)[0].signed).toBe(false);
  const foreign = { serviceReleases: [{ ...current, cloudDomain: "production.example.test", signed: true,
    publication: { stage: "READY", observedAt: "2026-09-15T11:00:00Z" } }] } as PlatformCloudObservation;
  expect(serviceReleases(local, foreign)[0]).toEqual(current);
});

test("monitoring never mixes nodes, service instances, subjects or partitions and preserves zero", () => {
  const samples = [
    { nodeId: "main", value: 4, time: "2026-09-13T10:00:00Z" },
    { nodeId: "main", value: 0, time: "2026-09-13T10:01:00Z" },
    { nodeId: "main", serviceId: "brake", subjectId: "a", instance: 0, value: 50, time: "2026-09-13T10:02:00Z" },
    { nodeId: "main", serviceId: "brake", subjectId: "b", instance: 0, value: 60, time: "2026-09-13T10:02:00Z" },
    { nodeId: "main", partition: "root", value: 80, time: "2026-09-13T10:02:00Z" },
    { nodeId: "main", partition: "data", value: 90, time: "2026-09-13T10:02:00Z" },
  ];
  const rows = groupedMetrics(samples);
  expect(rows).toHaveLength(5);
  expect(rows[0].sample.value).toBe(0);
  expect(rows.filter(row => row.scope === "Service instance")).toHaveLength(2);
});

test("service profile comes from exact artifact identity, not version major; authoring stays current-run scoped", () => {
  const vehicle = { state: "CURRENT", reason: null, process: "RUNNING", imageVersion: ".33", overlayExists: true };
  const local = composeLocalSnapshot({ mode: "LOCAL_READ_ONLY", available: true, observedAt: "2026-09-13T10:00:00Z", runId: "new-run", images: [], vehicles: { test: vehicle, production: vehicle }, source: { state: "CONNECTED", currentVehicle: "test" }, access: {} }).localDemo!;
  const row = { releaseHandle: "brake/12.0.0", team: "brake", contentProfile: "v1", version: "12.0.0", serviceId: "brake-id", runId: "new-run", signed: true, submitted: true, demoMockedData: true, publication: { stage: "READY" } } as ServiceRelease;
  const old = { ...row, releaseHandle: "brake/99.0.0", version: "99.0.0", runId: "old-run" };
  expect(serviceCandidate(local, [old, row], [], "brake", "v1")).toEqual(row);
  expect(serviceCandidate({ ...local, runId: null }, [row], [], "brake", "v1")).toBeUndefined();
  const installed = { service: { id: "brake-id" }, service_versions: { installed_service_version: { version: "12.0.0" } } } as CloudService;
  expect(serviceProfile(installed, [row])).toBe("v1");
  expect(serviceProfile({ ...installed, service: { id: "another", title: null } }, [row])).toBeUndefined();
});
