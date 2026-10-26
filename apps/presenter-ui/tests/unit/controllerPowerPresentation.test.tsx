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
function view(process = "STOPPED", lifecycle?: any, perspective: "global" | "platform" = "global", sourceState = "RUNNING_UNASSIGNED") {
  return render(<StudioWorkspace perspective={perspective} navigate={vi.fn()} snapshot={composeLocalSnapshot({
    mode: "LOCAL_READ_ONLY", runId: "run", observedAt: new Date().toISOString(), registrationComplete: true,
    images: [], access: {}, lifecycle,
    vehicles: { test: { state: "CURRENT", overlayExists: true, process }, production: { state: "NOT_APPLICABLE" } },
    source: { state: sourceState, currentVehicle: null },
  } as any)} />);
}
test("ignition off is not Finish or legacy Park/Resume; writes remain guarded", () => {
  view();
  expect(screen.getByText("Controller switched off", { selector: "strong" })).toBeVisible();
  expect(screen.queryByText(/Same-run restart is not supported/)).toBeNull();
  expect(screen.queryByText(/Reset unavailable during Finish/)).toBeNull();
  expect(screen.getAllByText(/Reset unavailable while the controller is switched off/)).toHaveLength(2);
  for (const team of ["Brake", "Tire"]) expect(screen.getByRole("button", { name: `Reset Driver Advisory — ${team}` })).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Delete Test & start over" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Start controller" }));
  expect(controls.request).toHaveBeenCalledWith({ action: "start-demo" });
});
test.each(["STOPPED", "NOT_PREPARED"])("ordinary Stop with %s source does not warn about intentionally closed vehicle windows", sourceState => {
  controls.session.workspace = { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } };
  view("STOPPED", undefined, "global", sourceState);
  expect(screen.getByText("Controller switched off", { selector: "strong" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Start controller" })).toBeEnabled();
  expect(screen.queryByLabelText("Desktop window layout")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  fireEvent.click(screen.getByRole("button", { name: /^Advanced settings$/ }));
  expect(screen.getByLabelText("Desktop window layout")).toHaveTextContent("Vehicle windows are not running");
  expect(screen.queryByText(/could not be verified|Window order is not currently verified/)).not.toBeInTheDocument();
  // Advanced settings performs its existing read-only certificate inspection.
  expect(controls.request).not.toHaveBeenCalled();
});
test.each(["UNKNOWN", "RUNNING_UNASSIGNED"])("stopped controller with %s source retains its layout warning", sourceState => {
  controls.session.workspace = { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } };
  view("STOPPED", undefined, "global", sourceState);
  expect(screen.getByLabelText("Desktop window layout")).toHaveTextContent("Window layout could not be verified");
  expect(controls.request).not.toHaveBeenCalled();
});
test("stopped controller with incomplete Create cannot hide its layout warning", () => {
  controls.session.workspace = { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } };
  view("STOPPED", { action: "create", state: "PARTIAL" }, "global", "STOPPED");
  expect(screen.queryByText("Controller switched off", { selector: "strong" })).not.toBeInTheDocument();
  expect(screen.getByLabelText("Desktop window layout")).toHaveTextContent("Window layout could not be verified");
});
test("powered-off controller cannot prepare or publish a release", () => {
  view("STOPPED", undefined, "platform");
  expect(screen.getByRole("button", { name: "Prepare v1" })).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Sign & publish" })).toBeNull();
  expect(screen.queryByText(/Finish the interrupted run/)).toBeNull();
});
test.each(["park", "resume"])("legacy %s stays separate from ignition and actual Finish", action => {
  view("STOPPED", { action, state: "PARTIAL" });
  expect(screen.getByText("Legacy run interrupted", { selector: "strong" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Delete Test & start over" })).toBeVisible();
  expect(screen.queryByText(/Reset unavailable during Finish/)).toBeNull();
});
test("actual partial retirement still offers only Continue Finish", () => {
  view("STOPPED", { action: "retire", state: "PARTIAL", phase: "stop-test" });
  expect(screen.getByText("Retirement paused", { selector: "strong" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Continue Test deletion" })).toBeVisible();
  expect(screen.getAllByText("Reset unavailable during Test deletion.")).toHaveLength(2);
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
  fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  fireEvent.click(screen.getByText("Ignition recovery limits"));
  expect(screen.getByRole("dialog")).toHaveTextContent("After controller ignition off/on");
  expect(screen.getByRole("dialog")).not.toHaveTextContent("Finish before shutting down");
});
