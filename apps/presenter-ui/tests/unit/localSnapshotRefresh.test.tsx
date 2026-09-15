import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LocalPresenterReadAdapter } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { PresenterReadModelProvider } from "../../src/app/state/PresenterReadModelProvider";
import { PresenterApp } from "../../src/app/PresenterApp";

const vehicle = { state: "CURRENT", process: "STOPPED", overlayExists: true, imageVersion: "Factory .33" };
const paused = { mode: "LOCAL_READ_ONLY", observedAt: "2026-09-13T16:11:18Z", runId: "test-run",
  images: [{ selector: "33/arm64", version: "Factory .33", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }],
  access: {}, vehicles: { test: vehicle, production: vehicle }, source: { state: "STOPPED", currentVehicle: null },
  lifecycle: { action: "retire", state: "PARTIAL", phase: "deprovision-test" } };
const retired = { ...paused, runId: undefined, lifecycle: undefined,
  vehicles: { ...paused.vehicles, test: { ...vehicle, process: "NOT_CREATED", overlayExists: false } } };
const response = (value: unknown) => ({ ok: true, json: async () => value });
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("local lifecycle refresh", () => {
  it("shares an in-flight local snapshot read", async () => {
    let resolve!: (value: ReturnType<typeof response>) => void;
    const fetcher = vi.fn(() => new Promise<ReturnType<typeof response>>(done => { resolve = done; }));
    vi.stubGlobal("fetch", fetcher);
    const adapter = new LocalPresenterReadAdapter();
    const first = adapter.read(), second = adapter.read();
    expect(fetcher).toHaveBeenCalledTimes(1);
    resolve(response(retired));
    expect(await first).toEqual(await second);
  });

  it("reads immediately on return to a visible tab, without waiting for the idle interval", async () => {
    vi.useFakeTimers();
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    const fetcher = vi.fn().mockResolvedValue(response(retired)); vi.stubGlobal("fetch", fetcher);
    const listener = vi.fn(), unsubscribe = new LocalPresenterReadAdapter().subscribe(listener);
    try {
      await vi.advanceTimersByTimeAsync(30000);
      expect(fetcher).not.toHaveBeenCalled();
      visibility.mockReturnValue("visible"); document.dispatchEvent(new Event("visibilitychange"));
      await flush();
      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener.mock.calls[0][0].localDemo.lifecycle).toBeUndefined();
      expect(fetcher.mock.calls[0][0]).toBe("/api/presenter/snapshot");
    } finally { unsubscribe(); }
  });

  it("coalesces foreground events and stops listeners/timers after unsubscribe", async () => {
    vi.useFakeTimers(); vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    let resolve!: (value: ReturnType<typeof response>) => void;
    const fetcher = vi.fn(() => new Promise<ReturnType<typeof response>>(done => { resolve = done; }));
    vi.stubGlobal("fetch", fetcher);
    const listener = vi.fn(), unsubscribe = new LocalPresenterReadAdapter().subscribe(listener);
    window.dispatchEvent(new Event("focus"));
    document.dispatchEvent(new Event("visibilitychange"));
    window.dispatchEvent(new Event("focus"));
    expect(fetcher).toHaveBeenCalledTimes(1);
    unsubscribe(); resolve(response(retired)); await flush();
    window.dispatchEvent(new Event("focus")); await vi.advanceTimersByTimeAsync(30000);
    expect(listener).not.toHaveBeenCalled(); expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("retains the 10-second visible idle poll for CLI changes while the page stays open", async () => {
    vi.useFakeTimers(); vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    const fetcher = vi.fn().mockResolvedValue(response(retired)); vi.stubGlobal("fetch", fetcher);
    const listener = vi.fn(), unsubscribe = new LocalPresenterReadAdapter().subscribe(listener);
    try {
      await vi.advanceTimersByTimeAsync(9999); expect(fetcher).not.toHaveBeenCalled();
      await vi.advanceTimersByTimeAsync(1); expect(listener).toHaveBeenCalledTimes(1);
      await vi.advanceTimersByTimeAsync(10000); expect(listener).toHaveBeenCalledTimes(2);
    } finally { unsubscribe(); }
  });

  it.each(["focus", "manual"])("clears Retirement paused after external CLI cleanup using %s refresh without a page reload", async (trigger) => {
    vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    let local: unknown = paused;
    const fetcher = vi.fn(async (path: string) => {
      if (path === "/api/presenter/snapshot") return response(local);
      if (path === "/api/presenter/client-state") return response({ buildId: "test-build", canReload: true });
      if (path === "/api/presenter/platform") return response({ state: "UNAVAILABLE", observedAt: "2026-09-13T17:00:00Z", value: null, reason: "NO_CURRENT_TEST" });
      throw new Error("Unexpected endpoint");
    });
    vi.stubGlobal("fetch", fetcher);
    const dependencies = { readPort: new LocalPresenterReadAdapter() };
    const view = render(<PresenterReadModelProvider dependencies={dependencies}><PresenterApp /></PresenterReadModelProvider>);
    try {
      expect(await screen.findByText("Retirement paused")).toBeInTheDocument();
      await waitFor(() => expect(screen.getByRole("button", { name: /^Refresh$/ })).toBeEnabled());
      local = retired;
      await act(async () => {
        if (trigger === "focus") window.dispatchEvent(new Event("focus"));
        else fireEvent.click(screen.getByRole("button", { name: /^Refresh$/ }));
      });
      expect(await screen.findByRole("button", { name: "Create controller" })).toBeInTheDocument();
      expect(screen.queryByText("Retirement paused")).not.toBeInTheDocument();
      expect(screen.getByRole("combobox", { name: "Factory image" })).toBeEnabled();
      expect(fetcher.mock.calls.every(([path]) => ["/api/presenter/snapshot", "/api/presenter/platform", "/api/presenter/client-state"].includes(path))).toBe(true);
    } finally { view.unmount(); }
  });
});
