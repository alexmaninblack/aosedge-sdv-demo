// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { CloudConnectionPanel } from "../../src/app/CloudConnectionPanel";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { VisibleCloudObserver } from "../../src/domain/visibleCloudObserver";
const state = vi.hoisted(() => ({ observation: null as any, loading: false, refresh() {}, enter() { return () => {}; } }));
const controls = vi.hoisted(() => ({ blocked: false, readBlocked: true, blockReason: null, request() {},
  session: { cloudDomain: "selected-stage.example", jobs: [] as any[] } }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => state }));
vi.mock("../../src/app/state/PresenterControls", () => ({ usePresenterControls: () => controls }));
afterEach(() => { cleanup(); vi.useRealTimers(); state.observation = null; controls.session.jobs = []; });

test.each(["brake", "tire"] as const)("U5 first %s installation pending guides observation, not republishing", team => {
  const now = new Date().toISOString();
  state.observation = { state: "CURRENT", observedAt: now, bindingKey: "run:test", value: { installedVersion: "80.0.0",
    installedProfile: { state: "CURRENT", profile: "v1", releaseVersion: "80.0.0", cloudVersionId: "vdp-id", source: "CLOUD_INSTALLATION_AND_PACKAGE" },
    lifecycle: "provisioned", online: "ONLINE", inventory: { unitId: "test", systemUid: "test", teamServiceIds: { [team]: `${team}-id` },
      components: { state: "CURRENT", value: [{ type: "demo-vehicle-data-provider", installed_component: { version: "80.0.0", id: "vdp-id" } }] },
      services: { state: "CURRENT", value: [{ subject: `${team}-subject`, service: { id: `${team}-id`, title: `${team} Health` },
        service_versions: { installed_service_version: null, pending_service_version: { version: "7.0.0" }, pending_service_version_status: "pending" },
        instances: { state: "CURRENT", value: [] } }] } } } };
  const snapshot = composeLocalSnapshot({ mode: "LOCAL_READ_ONLY", runId: "run", observedAt: now, registrationComplete: true, access: {}, images: [],
    serviceReleases: [{ team, runId: "run", releaseHandle: `${team}/current`, version: "7.0.0", contentProfile: "v1", serviceId: `${team}-id`, submitted: true, publication: { stage: "READY" } }],
    vehicles: { test: { state: "CURRENT", overlayExists: true, process: "RUNNING" }, production: { state: "NOT_APPLICABLE" } },
    source: { state: "CONNECTED", currentVehicle: "test", selectedVehicle: "test" } } as any);
  const { container } = render(<StudioWorkspace snapshot={snapshot} perspective={team} navigate={() => {}} />);
  expect(screen.getByText(/Pending 7.0.0/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign & publish" })).toBeDisabled();
  const guide = container.querySelector(".studio-guide");
  expect(guide).toHaveTextContent("Service update pending");
  expect(guide).toHaveTextContent("Refresh Cloud state");
  expect(guide).not.toHaveTextContent("Prepare and publish");
  expect(guide).toHaveTextContent("Safe Stop is not required");
});

test.each([false, true])("U3 failed certificate read keeps the configured domain with prior selection=%s", prior => {
  controls.session.jobs = [
    ...(prior ? [{ action: "cloud-select", state: "COMPLETED", results: [{ facts: { selectedDomain: "old.example" } }] }] : []),
    { action: "cloud-inspect", state: "BLOCKED", results: [{ state: "BLOCKED", message: "CLOUD_CREDENTIAL_MISSING_OR_UNSAFE", facts: {} }] },
  ];
  render(<CloudConnectionPanel section="connection" />);
  expect(screen.getByText("selected-stage.example")).toBeVisible();
  expect(screen.getByText("CLOUD_CREDENTIAL_MISSING_OR_UNSAFE")).toBeVisible();
  expect(screen.queryByText("Reading configuration…")).not.toBeInTheDocument();
  expect(screen.queryByText("old.example")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Use this Cloud" })).toBeDisabled();
});

test.each(["inventory", "aggregate"])("U4 %s status-only pending uses 2/4/8/10 then idle observation", async source => {
  vi.useFakeTimers();
  const value: any = { pendingVersion: null, inventory: { components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [] } } };
  if (source === "inventory") value.inventory.components.value = [{ pending_component: null, pending_component_status: "downloading" }];
  else value.updateStatus = "downloading";
  const read = vi.fn().mockResolvedValue({ state: "CURRENT", observedAt: new Date().toISOString(), value });
  const observer = new VisibleCloudObserver(read), leave = observer.enter();
  try {
    await vi.advanceTimersByTimeAsync(0); expect(read).toHaveBeenCalledTimes(1);
    for (const [index, delay] of [2000, 4000, 8000, 10000].entries()) {
      await vi.advanceTimersByTimeAsync(delay - 1); expect(read).toHaveBeenCalledTimes(index + 1);
      await vi.advanceTimersByTimeAsync(1); expect(read).toHaveBeenCalledTimes(index + 2);
    }
    value.updateStatus = "completed"; value.inventory.components.value = [];
    await vi.advanceTimersByTimeAsync(10000); const count = read.mock.calls.length;
    await vi.advanceTimersByTimeAsync(2000); expect(read).toHaveBeenCalledTimes(count);
    await vi.advanceTimersByTimeAsync(8000); expect(read).toHaveBeenCalledTimes(count + 1);
  } finally { leave(); }
});
