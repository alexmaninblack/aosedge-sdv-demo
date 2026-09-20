// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { CloudSummary } from "../../src/app/StudioSummaryCards";
import type { CloudInventory, PlatformCloudObservation } from "../../src/domain/platformObservation";
import { cloudSoftwareSummary } from "../../src/domain/cloudSummary";
import { formatResource } from "../../src/domain/resourceFormatting";

afterEach(cleanup);
const now = "2026-09-18T10:00:00Z";
function inventory(): CloudInventory {
  const empty = { state: "CURRENT", value: [], readCompletedAt: now };
  return { unitId: "test-a", systemUid: "native-a", readCompletedAt: now,
    components: { ...empty, value: [{ reported_component_id: "vdp", type: "vehicle-data-provider",
      installed_component: { version: "79.0.0" }, pending_component: null, pending_component_status: null, runtimeState: "NOT_REPORTED" }] },
    services: { ...empty, value: ["brake", "tire"].map(id => ({ service: { id, title: id }, subject: `${id}-subject`, num_instance: 1,
      service_versions: { installed_service_version: { version: "59.0.0" }, pending_service_version: null }, instances: empty })) },
    nodes: empty, layers: empty, assignedSubjects: empty };
}
function observation(): PlatformCloudObservation {
  return { state: "CURRENT", observedAt: now, reason: null, value: {
    target: "test", source: "Aos Cloud", online: "CONNECTED", lifecycle: "provisioned",
    installedVersion: "79.0.0", pendingVersion: null, updateStatus: null, latestPublishedVersion: "80.0.0",
    releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD", inventory: inventory(),
  } };
}

test("Cloud overview describes software and not resource consumption", () => {
  render(<CloudSummary observation={observation()} cloudLabel="CONNECTED" />);
  expect(screen.queryByText("CPU")).not.toBeInTheDocument();
  expect(screen.queryByText("Memory")).not.toBeInTheDocument();
  expect(screen.getByText("1 component · 2 services")).toBeInTheDocument();
  expect(screen.getByText("No pending updates")).toBeInTheDocument();
  expect(screen.getByText("Connected")).toBeInTheDocument();
});

test("missing, partial and stale inventory cannot establish no pending updates", () => {
  expect(cloudSoftwareSummary(null).updatesText).toBe("Not confirmed");
  const value = observation(); value.value!.inventory!.services.state = "UNAVAILABLE";
  expect(cloudSoftwareSummary(value).updatesText).toBe("Not confirmed");
  expect(cloudSoftwareSummary(value).inventoryLastKnown).toBe(true);
  value.value!.inventory!.services.state = "CURRENT";
  value.value!.inventory!.services.value = null;
  expect(cloudSoftwareSummary(value).updatesText).toBe("Not confirmed");
  value.value!.inventory = inventory(); value.state = "STALE";
  expect(cloudSoftwareSummary(value).updatesText).toBe("Not confirmed");
});

test("pending and failures survive summaries even without a pending version", () => {
  const value = observation(); value.value!.pendingVersion = "80.0.0";
  expect(cloudSoftwareSummary(value).updatesText).toBe("1 pending / in progress");
  value.value!.inventory!.components.value![0]!.pending_component = { version: "80.0.0" };
  expect(cloudSoftwareSummary(value).updatesText).toBe("1 pending / in progress");
  value.value!.inventory!.services.value![0]!.service_versions!.pending_service_version_status = "downloading";
  expect(cloudSoftwareSummary(value).updatesText).toBe("2 pending / in progress");
  value.value!.pendingVersion = null;
  value.value!.inventory!.components.value![0]!.pending_component = null;
  value.value!.inventory!.components.value![0]!.pending_component_error = "failed to install";
  expect(cloudSoftwareSummary(value).updatesText).toContain("Software issue");
  value.state = "STALE";
  expect(cloudSoftwareSummary(value).updatesText).toContain("Last reported");
});

test("software counts do not count pending releases or duplicate Subject instances", () => {
  const value = observation(); const rows = value.value!.inventory!.services.value!;
  rows.push({ ...rows[0]!, subject: "another-subject", num_instance: 4 });
  expect(cloudSoftwareSummary(value).inventoryText).toBe("1 component · 2 services");
  rows[1]!.service_versions!.installed_service_version = null;
  rows[1]!.service_versions!.pending_service_version = { version: "35.0.0" };
  expect(cloudSoftwareSummary(value).inventoryText).toBe("1 component · 1 service");
});

test("age follows the oldest relevant software observation, not current resource reads", () => {
  const value = observation(); const old = "2026-09-18T09:00:00Z";
  value.value!.inventory!.components.readCompletedAt = old;
  expect(cloudSoftwareSummary(value).observedAt).toBe(old);
  value.value!.inventory!.components.state = "STALE";
  value.value!.inventory!.components.lastKnownReadCompletedAt = old;
  expect(cloudSoftwareSummary(value).observedAt).toBe(old);
});

test("memory formatting preserves zero, small values, unknown units and CPU DMIPS", () => {
  expect(formatResource(536870912, "bytes", "ram")).toBe("512 MiB");
  expect(formatResource(1610612736, "bytes", "ram")).toBe("1.5 GiB");
  expect(formatResource(0, "bytes", "ram")).toBe("0 MiB");
  expect(formatResource(1, "bytes", "ram")).toBe("<0.01 MiB");
  expect(formatResource(536870912, null, "ram")).toBe("536870912 · unit not specified");
  expect(formatResource(0, "DMIPS", "cpu")).toBe("0 DMIPS");
  expect(formatResource(null, "bytes", "ram")).toBe("Not reported");
  expect(formatResource(20, "KiB", "ram")).toBe("20 KiB");
});
