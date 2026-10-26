// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { cloudPresentation, capabilityLabel, publicationLabel } from "../../src/domain/studioPresentation";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { ResourceGraphs } from "../../src/app/ResourceGraphs";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import type { Perspective } from "../../src/domain";

const cloud = vi.hoisted(() => ({ observation: null as any, loading: false, refresh: vi.fn(), enter: () => () => {} }));
const controls = vi.hoisted(() => ({ blocked: false, readBlocked: false, error: null, blockReason: null, request: vi.fn(), session: { jobs: [], active: null } as any }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => cloud }));
vi.mock("../../src/app/state/PresenterControls", async original => ({ ...await original<any>(), usePresenterControls: () => controls }));
afterEach(() => { cleanup(); vi.clearAllMocks(); cloud.observation = null; cloud.loading = false; controls.session = { jobs: [], active: null }; });
const time = "2026-10-23T10:00:00Z";
const local: any = { mode: "LOCAL_READ_ONLY", observedAt: time, available: true, runId: "retained-test", registrationComplete: true,
  lifecycle: { action: "create", state: "COMPLETED" }, access: {}, images: [],
  vehicles: { test: { state: "CURRENT", overlayExists: true, process: "STOPPED" }, production: { state: "NOT_APPLICABLE" } }, source: { state: "STOPPED" } };
function observation(state = "CURRENT", online = "ONLINE"): any {
  return { state, reason: state === "CURRENT" ? null : "ACTION_COMPLETED_REFRESH_REQUIRED", bindingKey: "retained-test:unit", observedAt: time, value: {
    online, lifecycle: "provisioned", installedVersion: "102.0.0", pendingVersion: null, updateStatus: null,
    inventory: { unitId: "unit", systemUid: "test", components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [] } } } };
}
test.each(["ONLINE", "OFFLINE"])("retained %s is explicitly last confirmed, never current or a new disconnect", online => {
  const value = cloudPresentation(observation("STALE", online), true, "Unknown");
  expect(value.connection).toBe(online === "ONLINE" ? "Online" : "Offline");
  expect(value.current).toBe(false); expect(value.lastKnown).toBe(true);
  expect(value.freshness).toBe("Updating Cloud report");
  expect(value.attention).toBe(false);
});
test("initial missing data and failed data do not imply absence, zero or Online", () => {
  expect(cloudPresentation(null, true, "Cloud not yet observed")).toMatchObject({ current: false, lastKnown: false });
  expect(cloudPresentation({ ...observation(), state: "UNAVAILABLE", value: null, reason: "READ_FAILED" }, false, "Unavailable")).toMatchObject({ connection: "Unavailable", current: false, attention: true });
  expect(capabilityLabel("v3")).toBe("Capability V3"); expect(capabilityLabel("102.0.0")).toBe("102.0.0");
  expect(publicationLabel("ACCEPTED")).toContain("awaiting Cloud processing");
});
test("existing Test initial load has compact resource placeholders, not a provisioning instruction or invented axes", () => {
  render(<ResourceGraphs model={{ data: null, busy: true, error: false, reason: null, refresh() {} }} />);
  expect(screen.getAllByText("Waiting for controller inventory…")).toHaveLength(6);
  expect(screen.queryByText(/Provision Test/)).toBeNull(); expect(screen.queryByRole("img")).toBeNull();
});
test("overview reserves status, removes resource graphs and expands layout diagnostics only on demand", () => {
  controls.session.workspace = { state: "INCOMPLETE", problems: ["WINDOW_MISSING"] };
  const { container } = render(<StudioWorkspace snapshot={composeLocalSnapshot({ ...local, source: { state: "UNKNOWN" } })} perspective="global" navigate={() => {}} />);
  expect(container.querySelector(".studio-status-dock")).toBeVisible();
  expect(container.querySelector(".resource-charts")).toBeNull();
  expect(container.querySelector(".studio-workspace > .operation-progress")).toBeNull();
  fireEvent.click(screen.getByLabelText("Desktop window layout"));
  expect(screen.getByRole("dialog")).toHaveTextContent("Window layout could not be verified");
  expect(controls.request).not.toHaveBeenCalled();
});
test("team re-entry preserves the deliberately selected capability", () => {
  function View() { const [perspective, navigate] = useState<Perspective>("platform"); return <StudioWorkspace snapshot={composeLocalSnapshot(local)} perspective={perspective} navigate={navigate} />; }
  render(<View />);
  fireEvent.click(within(screen.getByRole("group", { name: "Capability profile" })).getByRole("button", { name: /v2/ }));
  fireEvent.click(screen.getByRole("button", { name: "Brake Team" })); fireEvent.click(screen.getByRole("button", { name: "Platform Team" }));
  expect(within(screen.getByRole("group", { name: "Capability profile" })).getByRole("button", { name: /v2/ })).toHaveAttribute("aria-pressed", "true");
  expect(controls.request).not.toHaveBeenCalled();
});
test("submitted candidate makes repeated preparation secondary and does not claim installation", () => {
  cloud.observation = observation();
  const snapshot = composeLocalSnapshot({ ...local, candidates: [{ contentProfile: "v1", version: "105.0.0", submitted: true }] });
  render(<StudioWorkspace snapshot={snapshot} perspective="platform" navigate={() => {}} />);
  const status = screen.getByRole("status", { name: "Selected release status" });
  expect(status).toHaveTextContent("Capability V1 · Cloud release 105.0.0"); expect(status).toHaveTextContent("Awaiting publication report");
  expect(status).not.toHaveTextContent("Installed release confirmed");
  expect(screen.getByTestId("prepare-release")).toHaveTextContent("Prepare another build (v1)");
  expect(screen.getByTestId("prepare-release")).not.toHaveClass("studio-primary-action");
  expect(screen.queryByRole("button", { name: "Sign & publish" })).toBeNull();
});
test("foreign Cloud observation cannot restore a previous Test's Online heading", () => {
  cloud.observation = observation(); cloud.observation.bindingKey = "previous-test:unit";
  render(<StudioWorkspace snapshot={composeLocalSnapshot(local)} perspective="global" navigate={() => {}} />);
  expect(screen.queryByLabelText("Unit connection: Online")).toBeNull();
});
