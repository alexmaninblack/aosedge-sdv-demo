import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { VisibleCloudObserver, type CloudObserverState } from "../../src/domain/visibleCloudObserver";
import type { PlatformCloudObservation } from "../../src/domain/platformObservation";

const current = (pending: string | null = null): PlatformCloudObservation => ({ state: "CURRENT", observedAt: "2026-09-10T01:45:49Z", reason: null,
  value: { target: "test", source: "Aos Cloud", online: "Online", lifecycle: "provisioned", installedVersion: "18.0.0", pendingVersion: pending,
    updateStatus: "installed", latestPublishedVersion: "18.0.0", releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD" } });

describe("shared visible Cloud observer", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());
  it("reads on entry, coalesces panels/manual reads, polls idle, and stops when hidden", async () => {
    const read = vi.fn().mockResolvedValue(current());
    const observer = new VisibleCloudObserver(read);
    await observer.refresh(); expect(read).not.toHaveBeenCalled();
    const leave1 = observer.enter(); const leave2 = observer.enter();
    await Promise.all([observer.refresh(), observer.refresh()]);
    expect(read).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(9999); expect(read).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1); expect(read).toHaveBeenCalledTimes(2);
    leave1(); leave2(); await vi.advanceTimersByTimeAsync(30000); expect(read).toHaveBeenCalledTimes(2);
    observer.afterAction(); await vi.advanceTimersByTimeAsync(30000); expect(read).toHaveBeenCalledTimes(2);
    observer.enter(); await observer.refresh(); expect(read).toHaveBeenCalledTimes(3);
    observer.setForeground(false); await vi.advanceTimersByTimeAsync(30000); expect(read).toHaveBeenCalledTimes(3);
    observer.setForeground(true); await observer.refresh(); expect(read).toHaveBeenCalledTimes(4);
  });
  it("backs pending observations off from 2 to 10 seconds then returns to idle", async () => {
    const read = vi.fn().mockResolvedValue(current("19.0.0"));
    const observer = new VisibleCloudObserver(read); observer.enter(); await observer.refresh();
    for (const [delay, count] of [[2000, 2], [4000, 3], [8000, 4], [10000, 5], [10000, 6]]) {
      await vi.advanceTimersByTimeAsync(delay - 1); expect(read).toHaveBeenCalledTimes(count - 1);
      await vi.advanceTimersByTimeAsync(1); expect(read).toHaveBeenCalledTimes(count);
    }
    read.mockResolvedValue(current()); await vi.advanceTimersByTimeAsync(10000);
    await vi.advanceTimersByTimeAsync(9999); expect(read).toHaveBeenCalledTimes(7);
    await vi.advanceTimersByTimeAsync(1); expect(read).toHaveBeenCalledTimes(8);
  });
  it("keeps last known values/time across returned and thrown read failures", async () => {
    const read = vi.fn().mockResolvedValue(current());
    const observer = new VisibleCloudObserver(read); let value: CloudObserverState | undefined;
    observer.subscribe((next) => { value = next; }); observer.enter(); await observer.refresh();
    read.mockResolvedValue({ state: "UNAVAILABLE", value: null, observedAt: null, reason: "READ_FAILED" });
    await observer.refresh();
    expect(value?.observation).toEqual({ ...current(), state: "STALE", reason: "READ_FAILED" });
    read.mockRejectedValue(new Error("private details")); await observer.refresh();
    expect(value?.observation?.value?.online).toBe("Online");
    expect(value?.observation?.observedAt).toBe(current().observedAt);
    expect(value?.observation?.reason).toBe("AOS_CLOUD_STATE_UNAVAILABLE");
    read.mockResolvedValue(current()); await observer.refresh(); expect(value?.observation?.state).toBe("CURRENT");
  });
  it("queues exactly one post-action read behind the existing request; navigation does not cancel it", async () => {
    let resolve!: (value: PlatformCloudObservation) => void;
    const read = vi.fn().mockImplementationOnce(() => new Promise<PlatformCloudObservation>((done) => { resolve = done; })).mockResolvedValue(current());
    const observer = new VisibleCloudObserver(read); const leave = observer.enter();
    const flight = observer.refresh(); await Promise.resolve();
    observer.afterAction(); observer.afterAction(); expect(read).toHaveBeenCalledTimes(1);
    resolve(current()); await flight; await observer.refresh(); expect(read).toHaveBeenCalledTimes(2);
    leave(); await vi.advanceTimersByTimeAsync(30000); expect(read).toHaveBeenCalledTimes(2);
  });
  it("never retains a previous Unit observation after the owned Test binding changes", async () => {
    const read = vi.fn().mockResolvedValue({ ...current(), bindingKey: "vm-a:unit-a" });
    const observer = new VisibleCloudObserver(read); let value: CloudObserverState | undefined;
    observer.subscribe((next) => { value = next; }); observer.enter(); await observer.refresh();
    read.mockResolvedValue({ state: "UNAVAILABLE", bindingKey: "vm-b:none", value: null,
      observedAt: null, reason: "TEST_NOT_PROVISIONED", publication: { version: "19.0.0", stage: "PROCESSING" } });
    await observer.refresh();
    expect(value?.observation?.value).toBeNull();
    expect(value?.observation?.bindingKey).toBe("vm-b:none");
    expect(value?.observation?.publication?.version).toBe("19.0.0");
    await vi.advanceTimersByTimeAsync(2000);
    expect(read).toHaveBeenCalledTimes(3);
  });
});
