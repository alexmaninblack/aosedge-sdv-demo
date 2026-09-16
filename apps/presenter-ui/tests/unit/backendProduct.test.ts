import { describe, expect, it } from "vitest";
import { completedProduct, productRows } from "../../src/features/service-team/backendProduct";

const window = { unitSystemUid: "test", serviceVersion: "43.0.0", backendReceivedAt: "2026-09-15T19:45:49Z",
  deliveryState: "DURABLY_RECEIVED", terminalState: "COMPLETE", receivedSampleCount: 40, receivedChunkCount: 4, expectedChunkCount: 4 };
const resource = (items: unknown[]) => ({ state: "OBSERVED", data: { unitSystemUid: "test", items } });
describe("real backend product projection", () => {
  it("projects durable window facts without mock data or fabricated samples", () => {
    const rows = productRows({ productData: resource([window]) }, "test");
    expect(rows).toHaveLength(1);
    expect(rows[0].message.content).toMatchObject({ status: "COMPLETE", receivedSampleCount: 40 });
    expect(completedProduct(rows[0], "43.0.0")).toBe(true);
    expect(completedProduct(rows[0], "44.0.0")).toBe(false);
  });
  it("does not qualify incomplete windows or transport-only advisory facts", () => {
    const rows = productRows({ productData: resource([{ ...window, terminalState: "INCOMPLETE_SOURCE_GAP" }]) }, "test");
    expect(completedProduct(rows[0], "43.0.0")).toBe(false);
    expect(completedProduct({ ...rows[0], message: { serviceVersion: "43.0.0", messageType: "BRAKE_ADVISORY_FACT" } }, "43.0.0")).toBe(false);
  });
  it("rejects records belonging to another Unit", () => {
    expect(() => productRows({ productData: resource([{ ...window, unitSystemUid: "production" }]) }, "test")).toThrow();
    expect(() => productRows({ assessments: resource([{ backendReceivedAt: window.backendReceivedAt, message: { unitSystemUid: "other" } }]) }, "test")).toThrow();
  });
  it("keeps actual assessments separate from mock records", () => {
    const row = { backendReceivedAt: window.backendReceivedAt, deliveryState: "DURABLE_ACCEPTED",
      message: { unitSystemUid: "test", serviceVersion: "44.0.0", messageType: "TIRE_HEALTH_ASSESSMENT", content: { provenance: "DEMO_SYNTHETIC" } } };
    const rows = productRows({ assessments: resource([row]), mockData: { state: "OBSERVED", data: { records: [window] } } }, "test");
    expect(rows).toEqual([row]);
    expect(completedProduct(rows[0], "44.0.0")).toBe(true);
  });
});
