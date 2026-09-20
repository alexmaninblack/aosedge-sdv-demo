import { describe, expect, it } from "vitest";
import { afterReset, isProductResult, completedProduct, productRows } from "../../src/features/service-team/backendProduct";

const window = { unitSystemUid: "test", serviceVersion: "43.0.0", backendReceivedAt: "2026-09-15T19:45:49Z",
  deliveryState: "DURABLY_RECEIVED", terminalState: "COMPLETE", receivedSampleCount: 40, receivedChunkCount: 4, expectedChunkCount: 4 };
const resource = (items: unknown[]) => ({ state: "OBSERVED", data: { unitSystemUid: "test", items } });
describe("real backend product projection", () => {
  it("preserves the backend source-event envelope across reset, never substitutes delivery time", () => {
    const row = { backendReceivedAt: "2026-09-18T09:01:00Z", sourceEventTime: "2026-09-18T08:59:00Z",
      message: { unitSystemUid: "test", serviceVersion: "59.0.0", messageType: "BRAKE_ADVISORY_FACT" } };
    const [projected] = productRows({ advisories: resource([row]) }, "test");
    expect(afterReset(projected, "2026-09-18T09:00:00Z")).toBe(false);
    expect(isProductResult(projected, "brake")).toBe(false);
    expect(afterReset({ ...projected, message: { ...projected.message, sourceEventTime: "invalid" } }, "2026-09-18T09:00:00Z")).toBe(false);
  });
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
