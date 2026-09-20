// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, renderHook } from "@testing-library/react";
import { useResetScenario } from "../../src/features/service-team/ResetScenario";
import { monotonicReset } from "../../src/features/service-team/useBackendObservation";
const controls = vi.hoisted(() => ({ blocked: false, blockReason: null, request: vi.fn(), resetSubmissions: {} as any,
  session: { sessionId: "session", cloudDomain: "stage", jobs: [] as any[], active: null } }));
vi.mock("../../src/app/state/PresenterControls", () => ({ usePresenterControls: () => controls }));
vi.mock("../../src/features/service-team/useBackendObservation", async original => ({ ...await original<any>(), backendSummary: () => ({ resetState: "NONE" }) }));
const binding: any = { unitSystemUid: "unit", serviceId: "b", subjectId: "s", instanceIndex: 0, serviceVersion: "77.0.0", profile: "v3", current: true };
const model: any = { busy: false, error: false, data: { observations: { demoReset: { state: "OBSERVED", data: { connected: true, command: null } } } } };
const scope = JSON.stringify(["stage", "run", "unit", "b", "s", 0, "77.0.0"]);
afterEach(() => { cleanup(); controls.session.jobs = []; controls.resetSubmissions = {}; vi.clearAllMocks(); });

test("card and popup share immediate progress; lost response stays guarded without claiming CLEAR", () => {
  controls.resetSubmissions.brake = { id: "request", sessionId: "session", scope, phase: "SUBMITTING" };
  const hook = renderHook(() => useResetScenario("brake", model, binding, false, "run"));
  expect(hook.result.current.waiting).toBe(true); expect(hook.result.current.disabled).toBe(true);
  controls.resetSubmissions.brake.phase = "UNKNOWN"; hook.rerender();
  expect(hook.result.current.reason).toContain("response lost");
  controls.session.jobs = [{ id: "request", team: "brake", action: "backend-reset", state: "COMPLETED", results: [{ facts: { command: { commandId: "new" } } }] }];
  hook.rerender(); expect(hook.result.current.waiting).toBe(true);
  const correlated = { ...model, data: { observations: { demoReset: { state: "OBSERVED", data: { connected: true, command: { commandId: "new", state: "PENDING" } } } } } };
  expect(renderHook(() => useResetScenario("brake", correlated, binding, false, "run")).result.current.pending).toBe(true);
});

test("a prior run intent cannot appear on a new Test; incompatible Brake cannot reset", () => {
  controls.resetSubmissions.brake = { id: "old", sessionId: "session", scope, phase: "ACCEPTED" };
  const current = renderHook(() => useResetScenario("brake", model, binding, false, "other"));
  expect(current.result.current.pending).toBe(false); current.result.current.request();
  expect(controls.request).toHaveBeenCalledWith({ action: "backend-reset", team: "brake" }, expect.stringContaining("other"));
  expect(renderHook(() => useResetScenario("brake", model, { ...binding, profile: "v2" })).result.current.disabled).toBe(true);
});

test("routine backend refresh does not flicker an otherwise valid Reset button", () => {
  expect(renderHook(() => useResetScenario("brake", { ...model, busy: true }, binding)).result.current.disabled).toBe(false);
  expect(renderHook(() => useResetScenario("brake", { ...model, busy: true, data: null }, binding)).result.current.disabled).toBe(true);
});

test("late pending, missing or old commands do not replace terminal reset evidence", () => {
  const old: any = { state: "OBSERVED", data: { connected: true, command: { commandId: "same", issuedAt: "2026-09-20T10:00:00Z", state: "CLEARED" } } };
  const pending: any = { state: "OBSERVED", data: { connected: false, command: { ...old.data.command, state: "PENDING" } } };
  expect(monotonicReset(pending, old)?.data?.command?.state).toBe("CLEARED");
  expect(monotonicReset(pending, old)?.data?.connected).toBe(false);
  expect(monotonicReset({ ...pending, data: { ...pending.data, command: null } }, old)?.data?.command?.state).toBe("CLEARED");
  pending.data.command = { commandId: "new", issuedAt: "2026-09-20T10:01:00Z", state: "PENDING" };
  expect(monotonicReset(pending, old)?.data?.command?.commandId).toBe("new");
});
