// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";
import { useCloudResources } from "../../src/app/state/useCloudResources";
import { readCloudMonitoring } from "../../src/adapters/local/LocalPresenterReadAdapter";
vi.mock("../../src/adapters/local/LocalPresenterReadAdapter", () => ({ readCloudMonitoring: vi.fn() }));
const read = vi.mocked(readCloudMonitoring);
const t = "2026-09-20T10:00:00Z";
const response = (unitId = "test", history = false, time = t) => ({ unitId, readCompletedAt: time,
  [history ? "history" : "monitoring"]: { state: "CURRENT", value: history ? { series: [], coverage: { points: 0 } } : {} } });
afterEach(() => { cleanup(); vi.useRealTimers(); vi.resetAllMocks(); });

test("hung history does not delay latest reads or its independent 30-second cadence", async () => {
  vi.useFakeTimers();
  read.mockImplementation((_scope, history) => history ? new Promise(() => {}) : Promise.resolve(response()));
  const hook = renderHook(() => useCloudResources("test", true, 0, "cloud/run"));
  await act(async () => {});
  expect(hook.result.current.data?.unitId).toBe("test");
  expect(hook.result.current.busy).toBe(false); expect(hook.result.current.history.busy).toBe(true);
  await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
  expect(read.mock.calls.filter(call => !call[1])).toHaveLength(2);
  expect(read.mock.calls.filter(call => call[1])).toHaveLength(1);
});

test("late responses cannot leak into a replacement Cloud or Test", async () => {
  let old: (value: any) => void = () => {};
  read.mockImplementation((scope, history) => scope?.startsWith("old") && !history ? new Promise(resolve => { old = resolve; }) : Promise.resolve(response("test", history)));
  const hook = renderHook(({ scope }) => useCloudResources("test", true, 0, scope), { initialProps: { scope: "old" } });
  hook.rerender({ scope: "new" }); await act(async () => {});
  await act(async () => { old(response("foreign")); });
  expect(hook.result.current.data?.unitId).toBe("test"); expect(hook.result.current.error).toBe(false);
});

test("an older completed read cannot roll back metrics; a failed history preserves latest", async () => {
  let older = false;
  read.mockImplementation((_scope, history) => history ? Promise.reject(new Error("timeout")) : Promise.resolve(response("test", false, older ? "2026-09-20T09:00:00Z" : t)));
  const hook = renderHook(() => useCloudResources("test", true, 0, "cloud")); await act(async () => {});
  older = true; act(() => hook.result.current.refresh()); await act(async () => {});
  expect(hook.result.current.data?.readCompletedAt).toBe(t);
  expect(hook.result.current.history.error).toBe(true); expect(hook.result.current.error).toBe(false);
});

test("resource polling pauses while hidden and does not overlap a pending channel", async () => {
  vi.useFakeTimers();
  const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
  read.mockResolvedValue(response());
  renderHook(() => useCloudResources("test", true, 0, "cloud"));
  await act(async () => { await vi.advanceTimersByTimeAsync(30000); }); expect(read).not.toHaveBeenCalled();
  visibility.mockReturnValue("visible");
  await act(async () => { await vi.advanceTimersByTimeAsync(1000); }); expect(read).toHaveBeenCalledTimes(2);
  visibility.mockRestore();
});
