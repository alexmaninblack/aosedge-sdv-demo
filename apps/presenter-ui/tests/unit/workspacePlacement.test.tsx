// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { WorkspacePlacement } from "../../src/app/WorkspacePlacement";
const controls = vi.hoisted(() => ({ blocked: false, request: vi.fn(), session: { workspace: null as any, active: null as string | null, jobs: [] as any[] } }));
vi.mock("../../src/app/state/PresenterControls", () => ({ usePresenterControls: () => controls }));
afterEach(() => { cleanup(); controls.session.workspace = null; controls.session.active = null; controls.session.jobs = []; controls.blocked = false; vi.clearAllMocks(); });
test("an active restore does not present the old verified result as current", () => {
  controls.session.workspace = { state: "PLACED_AWAITING_VISUAL_REVIEW", zOrder: { state: "VERIFIED" } };
  controls.session.active = "layout";
  controls.session.jobs = [{ id: "layout", action: "workspace-restore" }];
  render(<WorkspacePlacement session />);
  expect(screen.getByText(/Restoring and checking/)).toBeInTheDocument();
  expect(screen.queryByText(/Window positions verified/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Window order verified/)).not.toBeInTheDocument();
});
test("deferred layout is visible despite a healthy running simulator", () => {
  controls.session.workspace = { state: "WAITING_FOR_UNLOCK", retryPending: true };
  render(<WorkspacePlacement />);
  expect(screen.getByRole("status")).toHaveTextContent("waiting for the Mac to be unlocked");
  expect(screen.getByRole("button", { name: "Restore window layout" })).toBeDisabled();
});
test("terminal layout failure offers only the fixed layout action", () => {
  controls.session.workspace = { state: "INCOMPLETE", retryPending: false, problems: ["WORKSPACE_ACCESSIBILITY_REQUIRED"] };
  render(<WorkspacePlacement />);
  expect(screen.getByRole("status")).toHaveTextContent("could not be verified");
  fireEvent.click(screen.getByRole("button", { name: "Restore window layout" }));
  expect(controls.request).toHaveBeenCalledExactlyOnceWith({ action: "workspace-restore" });
});
test("a recovered layout clears warning but remains accessible in Session", () => {
  controls.session.workspace = { state: "PLACED_AWAITING_VISUAL_REVIEW", zOrder: { state: "VERIFIED" } };
  const view = render(<WorkspacePlacement />);
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  view.rerender(<WorkspacePlacement session />);
  expect(screen.getByText(/Window positions verified/)).toBeInTheDocument();
  expect(screen.getByText(/Window order verified/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Restore window layout" })).toBeEnabled();
});

test("confirmed empty lifecycle does not report expected closed vehicle windows as broken layout", () => {
  controls.session.workspace = { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } };
  const view = render(<WorkspacePlacement vehicleWindowsAbsent />);
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Restore window layout" })).not.toBeInTheDocument();
  view.rerender(<WorkspacePlacement vehicleWindowsAbsent session />);
  expect(screen.getByText(/Vehicle windows are not running/)).toBeInTheDocument();
  expect(screen.queryByText(/could not be verified|Window order/)).not.toBeInTheDocument();
});

test("an actual restore remains visible during the empty lifecycle", () => {
  controls.session.active = "layout";
  controls.session.jobs = [{ id: "layout", action: "workspace-restore" }];
  render(<WorkspacePlacement vehicleWindowsAbsent />);
  expect(screen.getByText(/Restoring and checking/)).toBeInTheDocument();
});
