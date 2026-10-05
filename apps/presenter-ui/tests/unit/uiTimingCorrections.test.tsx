// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { Monitoring, type CloudResourcesModel } from "../../src/app/StudioReadViews";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";

const leave = vi.hoisted(() => vi.fn());
const state = vi.hoisted(() => ({ observation: null as any, loading: false, refresh: vi.fn(), enter: vi.fn() }));
const controls = vi.hoisted(() => ({ blocked: false, readBlocked: false, blockReason: null, error: null, request: vi.fn(),
  session: { active: null as string | null, cloudDomain: "stage.example", jobs: [] as any[] } }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => state }));
vi.mock("../../src/app/state/PresenterControls", async importOriginal => ({ ...await importOriginal<any>(), usePresenterControls: () => controls }));
const snapshot = (runId: string | null = null) => composeLocalSnapshot({ mode: "LOCAL_READ_ONLY", runId,
  observedAt: new Date().toISOString(), registrationComplete: false, access: {}, images: [],
  vehicles: { test: { state: runId ? "CURRENT" : "NOT_APPLICABLE", reason: "TARGET_NOT_CONFIGURED", overlayExists: Boolean(runId), process: runId ? "RUNNING" : null }, production: { state: "NOT_APPLICABLE" } },
  source: { state: "RUNNING_UNASSIGNED" } } as any);
afterEach(() => { cleanup(); vi.clearAllMocks(); controls.session.active = null; controls.session.jobs = []; state.observation = null; });

test("perspective navigation retains one Cloud visibility subscription", () => {
  state.enter.mockReturnValue(leave);
  const view = render(<StudioWorkspace snapshot={snapshot("run")} perspective="global" navigate={() => {}} />);
  view.rerender(<StudioWorkspace snapshot={snapshot("run")} perspective="brake" navigate={() => {}} />);
  view.rerender(<StudioWorkspace snapshot={snapshot("run")} perspective="platform" navigate={() => {}} />);
  expect(state.enter).toHaveBeenCalledTimes(1); expect(leave).not.toHaveBeenCalled();
  view.unmount(); expect(leave).toHaveBeenCalledTimes(1);
});

test("first Create Trace exposes the active job before a run identity exists", () => {
  state.enter.mockReturnValue(leave);
  controls.session.active = "create-1";
  controls.session.jobs = [{ id: "create-1", action: "create", runId: null, state: "RUNNING", startedAt: new Date().toISOString(), progress: ["Waiting for guest console"], results: [] }];
  render(<StudioWorkspace snapshot={snapshot()} perspective="global" navigate={() => {}} />);
  fireEvent.click(screen.getByRole("button", { name: "View progress" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Waiting for guest console");
  expect(screen.getByRole("dialog")).not.toHaveTextContent("No operations recorded");
});

test.each(["create", "prepare-demo"])("terminal %s failure remains visible before a run is allocated", action => {
  state.enter.mockReturnValue(leave);
  controls.session.jobs = [{ id: "failed", action, runId: null, state: "BLOCKED", startedAt: new Date().toISOString(), progress: [], results: [{ operation: "demo.create", state: "BLOCKED", message: "BACKEND_DOCKER_REQUIRED", facts: {} }] }];
  render(<StudioWorkspace snapshot={snapshot()} perspective="global" navigate={() => {}} />);
  expect(screen.getByText("BACKEND_DOCKER_REQUIRED")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: /Trace · 1/ }));
  expect(screen.getByRole("dialog")).toHaveTextContent("BACKEND_DOCKER_REQUIRED");
  expect(screen.getByRole("dialog")).not.toHaveTextContent("No operations recorded");
});

test("pre-run failures do not leak across an allocated run or its Finish", () => {
  state.enter.mockReturnValue(leave);
  controls.session.jobs = [{ id: "failed", action: "create", runId: null, state: "BLOCKED", startedAt: new Date().toISOString(), progress: [], results: [{ operation: "demo.create", state: "BLOCKED", message: "old failure", facts: {} }] },
    { id: "created", action: "create", runId: "old", state: "COMPLETED", startedAt: new Date().toISOString(), progress: [], results: [] }];
  const view = render(<StudioWorkspace snapshot={snapshot("new")} perspective="global" navigate={() => {}} />);
  expect(screen.queryByText("old failure")).not.toBeInTheDocument();
  view.rerender(<StudioWorkspace snapshot={snapshot()} perspective="global" navigate={() => {}} />);
  expect(screen.queryByText("old failure")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Trace · 0/ }));
  expect(screen.getByRole("dialog")).not.toHaveTextContent("old failure");
});

test("new run resets authoring profile without changing it within the same run", () => {
  state.enter.mockReturnValue(leave);
  const view = render(<StudioWorkspace snapshot={snapshot("old")} perspective="platform" navigate={() => {}} />);
  fireEvent.click(screen.getByRole("button", { name: /v3\s*Tire & advisory/ }));
  view.rerender(<StudioWorkspace snapshot={snapshot("old")} perspective="platform" navigate={() => {}} />);
  expect(screen.getByRole("button", { name: /v3\s*Tire & advisory/ })).toHaveAttribute("aria-pressed", "true");
  view.rerender(<StudioWorkspace snapshot={snapshot("new")} perspective="platform" navigate={() => {}} />);
  expect(screen.getByRole("button", { name: /v1\s*Braking telemetry/ })).toHaveAttribute("aria-pressed", "true");
});

test("open Trace acknowledges Finish after retirement removes the run ID", () => {
  state.enter.mockReturnValue(leave);
  controls.session.jobs = [{ id: "finish", action: "reset", runId: "retired", state: "COMPLETED", startedAt: new Date().toISOString(), finishedAt: new Date().toISOString(), progress: [], results: [{ operation: "demo.retire", state: "COMPLETED", message: "Owned Test removed", facts: {} }] }];
  render(<StudioWorkspace snapshot={snapshot()} perspective="global" navigate={() => {}} />);
  fireEvent.click(screen.getByRole("button", { name: /Trace/ }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Demo finished");
  expect(screen.getByRole("dialog")).not.toHaveTextContent("No operations recorded");
});

test("initial resource loading is not evidence of a missing sample", () => {
  const model: CloudResourcesModel = { data: null, error: false, reason: null, busy: true, refresh() {} };
  const inventory = { unitId: "test", nodes: { value: [{ node_id: "controller" }] } } as any;
  const view = render(<Monitoring inventory={inventory} observation={model} />);
  expect(screen.getByText("Waiting for the first Cloud resource observation…")).toBeVisible();
  expect(screen.queryByText("No sample reported for this scope.")).not.toBeInTheDocument();
  view.rerender(<Monitoring inventory={inventory} observation={{ ...model, busy: false }} />);
  expect(screen.getByText("Waiting for the first Cloud resource observation…")).toBeVisible();
  view.rerender(<Monitoring inventory={inventory} observation={{ ...model, error: true, busy: false }} />);
  expect(screen.getByText("Latest Cloud readings unavailable; history is shown independently below.")).toBeVisible();
  view.rerender(<Monitoring inventory={inventory} observation={{ ...model, busy: false, data: { unitId: "test", monitoring: { state: "CURRENT", value: {} } } }} />);
  expect(screen.getAllByText("No samples in this interval").length).toBeGreaterThan(0);
  view.rerender(<Monitoring inventory={inventory} observation={{ ...model, busy: true, data: { unitId: "test", monitoring: { state: "CURRENT", value: {
    cpu: { state: "CURRENT", unit: "DMIPS", value: [{ nodeId: "controller", value: 758, time: new Date(Date.now() - 1000).toISOString() }] },
  } } } }} />);
  expect(screen.getByText("758 DMIPS")).toBeVisible();
  expect(screen.queryByText(/Waiting for the first/)).not.toBeInTheDocument();
});

test("first Cloud observation is pending, not a failed Cloud connection", () => {
  state.enter.mockReturnValue(leave);
  const value = snapshot("run"); value.localDemo!.registrationComplete = true;
  const view = render(<StudioWorkspace snapshot={value} perspective="global" navigate={() => {}} />);
  const card = () => screen.getByRole("button", { name: "Aos Cloud Unit monitoring" });
  expect(card()).toHaveTextContent("Cloud not yet observed");
  expect(card()).not.toHaveTextContent("Cloud unavailable");
  state.observation = { state: "UNAVAILABLE", value: null, observedAt: null, reason: "HTTP_503" };
  view.rerender(<StudioWorkspace snapshot={value} perspective="global" navigate={() => {}} />);
  expect(card()).toHaveTextContent("Cloud unavailable");
});
