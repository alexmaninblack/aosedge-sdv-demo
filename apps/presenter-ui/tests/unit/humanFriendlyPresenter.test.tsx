// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { SharedHeader } from "../../src/app/SharedHeader";

const cloud = vi.hoisted(() => ({ observation: null as any, loading: false, refresh: vi.fn(), enter: () => () => {} }));
const controls = vi.hoisted(() => ({ blocked: false, readBlocked: true, blockReason: null, request: vi.fn(),
  session: { jobs: [], active: null } as any }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => cloud }));
vi.mock("../../src/app/state/PresenterControls", async original => ({ ...await original<any>(), usePresenterControls: () => controls }));
afterEach(() => { cleanup(); vi.clearAllMocks(); cloud.observation = null; controls.blocked = false; });
const base: any = { mode: "LOCAL_READ_ONLY", observedAt: new Date().toISOString(), runId: "test-run", registrationComplete: false,
  lifecycle: { action: "create", state: "COMPLETED" }, access: { "oem-delivery": { present: true, state: "NOT_REQUESTED" }, "service-provider": { present: false, state: "NOT_REQUESTED" } },
  images: [{ selector: "41/arm64", version: "Factory .41", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }],
  vehicles: { test: { state: "CURRENT", overlayExists: true, process: "RUNNING", imageVersion: "Factory .41" }, production: { state: "NOT_APPLICABLE" } },
  source: { state: "RUNNING_UNASSIGNED" } };
function view(local = base, perspective: "global" | "platform" | "brake" | "tire" = "global") {
  const snapshot = composeLocalSnapshot(local);
  const navigate = vi.fn();
  return { ...render(<><SharedHeader snapshot={snapshot} perspective={perspective} onNavigate={navigate} /><StudioWorkspace snapshot={snapshot} perspective={perspective} navigate={navigate} /></>), navigate };
}

test("there is one controls entry, no mid-run preparation mode and no single-image selector", () => {
  view();
  expect(screen.getAllByRole("button", { name: "Demo controls" })).toHaveLength(1);
  expect(screen.queryByRole("button", { name: "Session" })).toBeNull();
  expect(screen.queryByLabelText("Preparation")).toBeNull();
  expect(screen.queryByLabelText("Factory image")).toBeNull();
  expect(screen.getByText("Factory .41")).toBeVisible();
});

test("empty cards separate installed details from release management", () => {
  const { navigate } = view();
  for (const team of ["Brake", "Tire"]) expect(screen.getByRole("button", { name: `${team} service details` })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Vehicle Data Platform installed details" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Brake Team" }));
  expect(navigate).toHaveBeenCalledWith("brake");
  fireEvent.click(screen.getByRole("button", { name: "Platform Team" }));
  expect(navigate).toHaveBeenCalledWith("platform");
  expect(controls.request).not.toHaveBeenCalled();
});

test("team guidance names the current action and does not duplicate Prepare", () => {
  const { container, navigate } = view(base, "platform");
  expect(container.querySelector(".studio-guide")).toHaveTextContent("Prepare Platform v1");
  expect(screen.queryByRole("button", { name: "Open Platform" })).toBeNull();
  expect(screen.getAllByRole("button", { name: "Prepare v1" })).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Prepare v1" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "prepare", profile: "v1" });
  expect(navigate).not.toHaveBeenCalled();
});

test("a pending VDP on Platform opens update details, never navigates back to Platform", () => {
  cloud.observation = { state: "CURRENT", observedAt: new Date().toISOString(), bindingKey: "test-run:unit", value: {
    online: "ONLINE", installedVersion: "12.0.0", pendingVersion: "13.0.0", updateStatus: "pending", inventory: { unitId: "unit",
      components: { state: "CURRENT", value: [{ type: "demo-vehicle-data-provider", reported_component_id: "vdp", installed_component: { version: "12.0.0" }, pending_component: { version: "13.0.0" }, pending_component_status: "pending" }] },
      services: { state: "CURRENT", value: [] } } } };
  const { navigate } = view({ ...base, registrationComplete: true, source: { state: "CONNECTED", currentVehicle: "test", selectedVehicle: "test" } }, "platform");
  expect(screen.queryByRole("button", { name: "Open Platform" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Open update details" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("13.0.0");
  expect(navigate).not.toHaveBeenCalled(); expect(controls.request).not.toHaveBeenCalled();
});

test("recorded quick preparation resumes after reload, without changing the recipe", () => {
  view({ ...base, preparation: { image: "41/arm64", phase: "PROVISIONING" } });
  expect(screen.queryByLabelText("Preparation")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Continue preparation" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "prepare-demo", image: "41/arm64" });
});

test("the live empty preparation sentinel does not hide a completed story's power-on path", () => {
  view({ ...base, preparation: {}, registrationComplete: true,
    vehicles: { ...base.vehicles, test: { ...base.vehicles.test, process: "STOPPED" } },
    source: { state: "STOPPED" } });
  expect(screen.queryByRole("button", { name: "Continue preparation" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Start controller" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "start-demo" });
  expect(controls.request).not.toHaveBeenCalledWith(expect.objectContaining({ action: "prepare-demo" }));
});

test("an empty preparation sentinel retains story continuation for a genuinely incomplete Create", () => {
  view({ ...base, preparation: {}, lifecycle: { action: "create", state: "PARTIAL" } });
  fireEvent.click(screen.getByRole("button", { name: "Continue preparation" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "create", image: "41/arm64" });
});

test("Stop and Delete are separate actions; deletion is hidden until explicitly expanded", () => {
  view();
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  const dialog = screen.getByRole("dialog");
  expect(within(dialog).getByRole("button", { name: "Stop demo and keep data" })).toBeEnabled();
  expect(screen.getByText("Delete Test & start over").closest("details")).not.toHaveAttribute("open");
  expect(screen.getByText("Delete Test & start over")).not.toBeVisible();
  fireEvent.click(screen.getByText("Delete this Test"));
  expect(within(dialog).getByRole("button", { name: "Delete Test & start over" })).toBeEnabled();
  fireEvent.click(within(dialog).getByRole("button", { name: "Stop demo and keep data" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "stop-demo" });
  expect(controls.request).not.toHaveBeenCalledWith({ action: "reset" });
});

test.each(["UNKNOWN", null])("unconfirmed local power %s cannot dispatch Start or Stop", process => {
  view({ ...base, vehicles: { ...base.vehicles, test: { ...base.vehicles.test, process } } });
  expect(screen.getByText("Controller power not confirmed", { selector: "strong" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  expect(within(screen.getByRole("dialog")).getByRole("button", { name: "Stop demo and keep data" })).toBeDisabled();
  expect(controls.request).not.toHaveBeenCalled();
});

test("a pending/uncertain operation disables Stop and Delete, but retains diagnostics", () => {
  controls.blocked = true;
  view();
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  expect(within(screen.getByRole("dialog")).getByRole("button", { name: "Stop demo and keep data" })).toBeDisabled();
  fireEvent.click(screen.getByText("Delete this Test"));
  expect(screen.getByRole("button", { name: "Delete Test & start over" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Advanced settings" })).toBeEnabled();
  expect(controls.request).not.toHaveBeenCalled();
});

test("certificate presence is shown only under explicit settings, not asserted as authenticated access", () => {
  view();
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  expect(screen.queryByText("OEM certificate")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Advanced settings" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("OEM certificateConfigured locallyService Provider certificateNot configured");
  expect(screen.getByRole("dialog")).toHaveTextContent("Local certificate presence is not authenticated Cloud access");
  expect(screen.queryByRole("button", { name: "Choose OEM certificate…" })).toBeNull();
  const recovery = screen.getByText("Recovery & diagnostics").closest("details")!;
  recovery.open = true; fireEvent(recovery, new Event("toggle"));
  expect(controls.request).not.toHaveBeenCalled();
});
