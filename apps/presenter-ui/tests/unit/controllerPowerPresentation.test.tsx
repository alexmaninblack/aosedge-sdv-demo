// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
const controls = vi.hoisted(() => ({ blocked: false, blockReason: null, request: vi.fn(), session: { jobs: [], active: null } as any }));
vi.mock("../../src/app/state/PresenterControls", async original => ({ ...await original<any>(), usePresenterControls: () => controls }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => ({ observation: null, enter: () => () => {}, refresh: vi.fn() }) }));
afterEach(() => { cleanup(); controls.blocked = false; controls.session = { jobs: [], active: null }; vi.clearAllMocks(); });
function view(process = "STOPPED", lifecycle?: any, perspective: "global" | "platform" = "global") {
  return render(<StudioWorkspace perspective={perspective} navigate={vi.fn()} snapshot={composeLocalSnapshot({
    mode: "LOCAL_READ_ONLY", runId: "run", observedAt: new Date().toISOString(), registrationComplete: true,
    images: [], access: {}, lifecycle,
    vehicles: { test: { state: "CURRENT", overlayExists: true, process }, production: { state: "NOT_APPLICABLE" } },
    source: { state: "RUNNING_UNASSIGNED", currentVehicle: null },
  } as any)} />);
}
test("ignition off is not Finish or legacy Park/Resume; writes remain guarded", () => {
  view();
  expect(screen.getByText("Controller switched off", { selector: "strong" })).toBeVisible();
  expect(screen.queryByText(/Same-run restart is not supported/)).toBeNull();
  expect(screen.queryByText(/Reset unavailable during Finish/)).toBeNull();
  expect(screen.getAllByText(/Reset unavailable while the controller is switched off/)).toHaveLength(2);
  for (const team of ["Brake", "Tire"]) expect(screen.getByRole("button", { name: `Reset Driver Advisory — ${team}` })).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Finish demo" })).toBeNull();
  expect(controls.request).not.toHaveBeenCalled();
});
test("powered-off controller cannot prepare or publish a release", () => {
  view("STOPPED", undefined, "platform");
  expect(screen.getByRole("button", { name: "Prepare v1" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Sign & publish" })).toBeDisabled();
  expect(screen.queryByText(/Finish the interrupted run/)).toBeNull();
});
test.each(["park", "resume"])("legacy %s stays separate from ignition and actual Finish", action => {
  view("STOPPED", { action, state: "PARTIAL" });
  expect(screen.getByText("Demo interrupted", { selector: "strong" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Finish demo" })).toBeVisible();
  expect(screen.queryByText(/Reset unavailable during Finish/)).toBeNull();
});
test("actual partial retirement still offers only Continue Finish", () => {
  view("STOPPED", { action: "retire", state: "PARTIAL", phase: "stop-test" });
  expect(screen.getByText("Retirement paused", { selector: "strong" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Continue Finish" })).toBeVisible();
  expect(screen.getAllByText("Reset unavailable during Finish.")).toHaveLength(2);
  expect(screen.queryByText("Controller switched off", { selector: "strong" })).toBeNull();
});
test("recovery busy is not a premature manual-connect instruction", () => {
  controls.blocked = true; controls.session.sourceRecoveryBusy = true;
  view("RUNNING");
  expect(screen.getByText("Restoring controller connection", { selector: "strong" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Connect in Manual" })).toBeNull();
  expect(controls.request).not.toHaveBeenCalled();
});
test("Session describes ignition recovery without destructive shutdown advice", () => {
  view("RUNNING");
  fireEvent.click(screen.getByRole("button", { name: "Session" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("After controller ignition off/on");
  expect(screen.getByRole("dialog")).not.toHaveTextContent("Finish before shutting down");
});
