import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { BrakeWindowDetail, validateWindowDetail } from "../../src/features/service-team/BrakeWindowDetail";
import { readBrakeWindow } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { nativeInstance } from "./backendFixture";
import { windowDeliveryLabel } from "../../src/features/service-team/windowPresentation";
const eventId = "4cba2d80-c04a-4d24-9f03-f4a85d56da13";
test("chunk counts alone do not prove durable delivery; unknown totals stay unknown", () => {
  expect(windowDeliveryLabel({ receivedChunkCount: 3, expectedChunkCount: 3, deliveryState: "RECEIVING" })).toContain("unconfirmed");
  expect(windowDeliveryLabel({ receivedChunkCount: 3, expectedChunkCount: null })).toContain("total not yet reported");
  expect(windowDeliveryLabel({ receivedChunkCount: 4, expectedChunkCount: 3 })).toContain("inconsistent");
  expect(windowDeliveryLabel({ receivedChunkCount: -1, expectedChunkCount: 3 })).toBe("Chunk delivery not confirmed");
});
const row = { backendReceivedAt: "2026-09-11T22:00:00.000Z", message: { messageType: "WINDOW_COMPLETION", eventId,
  unitSystemUid: "current-test", serviceVersion: "7.0.0", serviceInstance: nativeInstance } };
function detail() { return { schemaVersion: 2, contractVersion: "2.0.0", resourceType: "WINDOW_DETAIL", unitRole: "VALIDATION",
  unitSystemUid: "current-test", window: { ...row.message, terminalState: "COMPLETE" }, samples: Array.from({ length: 8 }, (_, i) => ({
    sampleIndex: i + (i > 3 ? 2 : 0), sourceTimestamp: new Date(Date.parse(row.backendReceivedAt) + i * 100).toISOString(),
    phase: i < 2 ? "PRE" : i < 7 ? "ACTIVE" : "POST", speedKph: 50 - i * 3, brakePedalPercent: 70, longitudinalAccelerationMps2: -3,
  })) }; }
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
test("window shows actual phase counts, gaps and paged samples without an invented score", async () => {
  vi.stubGlobal("innerHeight", 900);
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => detail() }); vi.stubGlobal("fetch", fetch);
  render(<BrakeWindowDetail row={row} />);
  expect(await screen.findByText("8 retained samples · 2 missing sample indices")).toBeVisible();
  expect(screen.getByText("Recording complete")).toBeVisible();
  expect(screen.getByRole("img", { name: "Speed: actual retained samples" })).toBeVisible();
  expect(screen.getByRole("img", { name: "Brake pedal: actual retained samples" })).toBeVisible();
  expect(screen.getAllByRole("row")).toHaveLength(6);
  fireEvent.click(screen.getByRole("button", { name: "Next samples" }));
  expect(screen.getAllByRole("row")).toHaveLength(4);
  expect(fetch).toHaveBeenCalledWith(`/api/presenter/backend/brake/windows/${eventId}`, expect.objectContaining({ cache: "no-store" }));
});
test.each(["unit", "instance", "version", "event", "oversize", "index", "time", "value", "phase"])("rejects %s mismatch instead of repairing samples", change => {
  const value = detail();
  if (change === "unit") value.unitSystemUid = "other";
  if (change === "instance") value.window.serviceInstance = { ...nativeInstance, instanceId: "other" };
  if (change === "version") value.window.serviceVersion = "8.0.0";
  if (change === "event") value.window.eventId = "other";
  if (change === "oversize") value.samples = Array(151).fill(value.samples[0]);
  if (change === "index") value.samples[1].sampleIndex = 0;
  if (change === "time") value.samples[1].sourceTimestamp = value.samples[0].sourceTimestamp;
  if (change === "value") value.samples[1].speedKph = NaN;
  if (change === "phase") value.samples[1].phase = "SCORE";
  expect(() => validateWindowDetail(value, row)).toThrow();
});
test("empty acquisition remains empty; an invalid selector makes no request", async () => {
  const value = detail(); value.samples = [];
  expect(validateWindowDetail(value, row).samples).toEqual([]);
  const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
  await expect(readBrakeWindow(eventId + "?target=production", new AbortController().signal)).rejects.toThrow();
  expect(fetch).not.toHaveBeenCalled();
});
test("legacy provenance remains inspectable as history without fabricating a native binding", () => {
  const value = detail();
  const history = { ...row, message: { ...row.message, serviceInstance: undefined, serviceArtifactSha256: "a".repeat(64) } };
  Object.assign(value.window, { serviceInstance: undefined, serviceArtifactSha256: "a".repeat(64) });
  expect(validateWindowDetail(value, history).samples).toHaveLength(8);
  Object.assign(value.window, { serviceArtifactSha256: "b".repeat(64) });
  expect(() => validateWindowDetail(value, history)).toThrow();
});
test("interrupted acquisition and fully delivered retained chunks are separate facts", async () => {
  const value = detail();
  Object.assign(value.window, { terminalState: "INCOMPLETE_SOURCE_GAP", receivedChunkCount: 3,
    expectedChunkCount: 3, deliveryState: "DURABLY_RECEIVED" });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => value }));
  render(<BrakeWindowDetail row={row} />);
  expect(await screen.findByText("Recording interrupted: source data gap")).toBeVisible();
  expect(screen.getByText("All retained chunks received (3/3)")).toBeVisible();
  expect(screen.getByText(/INCOMPLETE_SOURCE_GAP/)).toBeInTheDocument();
});
test("F6 explicit refresh reconciles the same window's late chunks and rejects a changed identity", async () => {
  const first = detail(); Object.assign(first.window, { receivedChunkCount: 1, expectedChunkCount: 2, deliveryState: "RECEIVING" });
  const complete = detail(); Object.assign(complete.window, { receivedChunkCount: 2, expectedChunkCount: 2, deliveryState: "DURABLY_RECEIVED" });
  const wrong = detail(); wrong.window.serviceVersion = "other";
  const fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => first })
    .mockResolvedValueOnce({ ok: true, json: async () => complete }).mockResolvedValueOnce({ ok: true, json: async () => wrong });
  vi.stubGlobal("fetch", fetch); render(<BrakeWindowDetail row={row} />);
  expect(await screen.findByText(/1\/2/)).toBeVisible();
  expect(screen.getByText(/Window snapshot · checked/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Refresh window" }));
  expect(await screen.findByText("All retained chunks received (2/2)")).toBeVisible();
  expect(fetch).toHaveBeenCalledTimes(2);
  fireEvent.click(screen.getByRole("button", { name: "Refresh window" }));
  expect(await screen.findByText(/Window detail unavailable or identity changed/)).toBeVisible();
  expect(screen.queryByText("All retained chunks received (2/2)")).not.toBeInTheDocument();
  expect(fetch.mock.calls.every(call => call[0] === `/api/presenter/backend/brake/windows/${eventId}`)).toBe(true);
});
