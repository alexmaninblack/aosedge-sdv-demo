import { afterEach, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ClientBuildNotice } from "../../src/app/ClientBuildNotice";
import { CloudConnectionPanel } from "../../src/app/CloudConnectionPanel";
import { OperationProgress, PresenterControls, usePresenterControls } from "../../src/app/state/PresenterControls";
import { serviceRunning } from "../../src/domain/softwareObservation";
import type { DemoCommand, DemoJob, OperationSession } from "../../src/domain/presenterCommandPort";

afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); });
const state = (): OperationSession => ({ sessionId: "test", active: null, uncertain: false, jobs: [] });
const job = (id: string, domain: string, action: DemoJob["action"] = "cloud-inspect"): DemoJob => ({ id, action, state: "COMPLETED", startedAt: new Date().toISOString(), progress: [], results: [{ operation: "cloud.inspect", state: "OBSERVED", message: "Inspected", facts: { selectedDomain: domain, domain } }] });

test("Running requires current matching instance version and no service issue", () => {
  const row: any = { service_versions: { installed_service_version: { version: "7.0.0" } }, instances: { state: "CURRENT", value: [{ version: "7.0.0", run_state: "active" }] } };
  expect(serviceRunning(row, "7.0.0", true)).toBe(true);
  expect(serviceRunning(row, "8.0.0", true)).toBe(false);
  expect(serviceRunning(row, "7.0.0", false)).toBe(false);
  row.instances.state = "STALE"; expect(serviceRunning(row, "7.0.0", true)).toBe(false);
  row.instances.state = "CURRENT"; row.error_message = "START_FAILED";
  expect(serviceRunning(row, "7.0.0", true)).toBe(false);
});

test("uncertain mutation leaves diagnostics available without enabling Finish or replay", async () => {
  const value = { ...state(), uncertain: true };
  const port = { read: vi.fn(async () => value), submit: vi.fn(async (_command: DemoCommand, id: string) => job(id, "debug.test")) };
  function Actions() { const controls = usePresenterControls(); return <><button disabled={controls.blocked} onClick={() => controls.request({ action: "reset" })}>Finish demo</button><CloudConnectionPanel /></>; }
  render(<PresenterControls port={port}><Actions /></PresenterControls>);
  await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(1));
  expect(port.submit.mock.calls[0][0]).toEqual({ action: "cloud-inspect" });
  expect(screen.getByRole("button", { name: "Finish demo" })).toBeDisabled();
  expect(screen.getByText(/Finish cannot safely overlap/)).toBeVisible();
  await waitFor(() => expect(screen.getByRole("button", { name: "Read configured certificate" })).toBeEnabled());
  fireEvent.click(screen.getByRole("button", { name: "Read configured certificate" }));
  await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(2));
  expect(port.submit.mock.calls.every(([command]) => command.action === "cloud-inspect")).toBe(true);
});

test("fresh configuration inspection outranks an earlier successful Cloud selection", async () => {
  const selected = job("old", "old.test", "cloud-select"); selected.results[0].facts.applied = true;
  const value = { ...state(), jobs: [selected] };
  const port = { read: vi.fn(async () => value), submit: vi.fn(async (_command: DemoCommand, id: string) => job(id, "new.test")) };
  render(<PresenterControls port={port}><CloudConnectionPanel /></PresenterControls>);
  await waitFor(() => expect(screen.getAllByText("new.test")).toHaveLength(2));
  expect(screen.queryByText("old.test")).toBeNull();
  expect(screen.getByText(/does not verify Cloud API or Service Provider/)).toBeVisible();
});

test("explicit empty activity scope never displays a previous run job", async () => {
  const value = { ...state(), jobs: [{ ...job("old", "old.test"), action: "reset" as const }] };
  render(<PresenterControls port={{ read: async () => value, submit: vi.fn() }}><OperationProgress job={null} /></PresenterControls>);
  await act(async () => {});
  expect(screen.queryByText(/Finish demo/)).toBeNull();
});

test("new browser build is announced and reload stays blocked during uncertainty", async () => {
  vi.useFakeTimers();
  let buildId = "a";
  const value = state();
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({ buildId, canReload: true }) })));
  render(<PresenterControls port={{ read: async () => ({ ...value }), submit: vi.fn() }}><ClientBuildNotice /></PresenterControls>);
  await act(async () => { await vi.advanceTimersByTimeAsync(1); });
  expect(screen.queryByRole("button", { name: "Reload UI" })).toBeNull();
  buildId = "b";
  await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
  expect(screen.getByRole("button", { name: "Reload UI" })).toBeEnabled();
  value.uncertain = true;
  await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
  expect(screen.getByRole("button", { name: "Reload UI" })).toBeDisabled();
});
