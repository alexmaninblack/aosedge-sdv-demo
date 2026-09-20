import { expect, test } from "vitest";
import { backendBinding, selectProduct, resetBoundary } from "../../src/features/service-team/backendSelection";
import { binding, nativeInstance, confirmedReset } from "./backendFixture";
import type { ProductRow } from "../../src/features/service-team/backendProduct";
const row = (source: string, received: string): ProductRow => ({ backendReceivedAt: received, deliveryState: "DURABLY_RECEIVED",
  message: { unitSystemUid: binding.unitSystemUid, serviceInstance: nativeInstance, serviceVersion: binding.serviceVersion,
    messageType: "BRAKE_HEALTH_ASSESSMENT", sourceEventTime: source, content: { currentBand: "GOOD" } } });
const old = row("2026-09-11T22:00:00.000Z", "2026-09-11T22:03:00.000Z");
const fresh = row("2026-09-11T22:01:00.000Z", "2026-09-11T22:01:01.000Z");
test("shared current result uses source order, not latest backend receipt", () => {
  const result = selectProduct([old, fresh], "brake", binding.serviceVersion, binding);
  expect(result.result).toBe(fresh); expect(result.proof).toBe(binding.serviceVersion);
});
test.each(["PENDING", "FAILED", "REJECTED", "EXPIRED"])("%s reset is not ignored or treated as applied", state => {
  const command = { ...confirmedReset(), state, result: null };
  const result = selectProduct([old, fresh], "brake", binding.serviceVersion, binding, command);
  expect(result.result).toBeUndefined(); expect(result.proof).toBeUndefined();
  expect(result.reset.state).toBe(state === "PENDING" ? "PENDING" : "UNCERTAIN");
});
test("CLEAR boundary is its correlated Gateway observation, not command issue", () => {
  const between = row("2026-09-11T22:00:01.000Z", "2026-09-11T22:02:00.000Z");
  const result = selectProduct([old, between, fresh], "brake", binding.serviceVersion, binding, confirmedReset());
  expect(result.rows).toEqual([fresh]); expect(result.reset.state).toBe("CLEARED");
});
test("a confirmed previous-release reset remains history after SOTA, not an uncertain current reset", () => {
  const command = confirmedReset({ ...binding, serviceVersion: "6.0.0" });
  const result = selectProduct([fresh], "brake", binding.serviceVersion, binding, command);
  expect(result.reset).toEqual({ state: "HISTORICAL", after: undefined });
  expect(result.result).toBe(fresh);
  expect(result.proof).toBe(binding.serviceVersion);
  // A corrupt old result is not reclassified merely because its version differs.
  (command.result as Record<string, unknown>).producerEpoch = "wrong-epoch";
  expect(resetBoundary(command, binding).state).toBe("UNCERTAIN");
});
test.each(["result", "request", "instance", "release", "epoch", "time"])("uncorrelated %s cannot establish reset completion", change => {
  const command = confirmedReset(); const result = command.result as Record<string, unknown>;
  if (change === "result") command.result = null;
  if (change === "request") (result.gatewayStatus as Record<string, unknown>).requestId = "another";
  if (change === "instance") result.serviceInstance = { ...nativeInstance, instanceId: "previous" };
  if (change === "release") command.serviceVersion = "8.0.0";
  if (change === "epoch") result.producerEpoch = "other";
  if (change === "time") (result.gatewayStatus as Record<string, unknown>).gatewayObservedAt = "2026-09-11T21:59:59.000Z";
  expect(resetBoundary(command, binding).state).toBe("UNCERTAIN");
});
test("missing/old native allocation cannot qualify; multiple opaque instances stay ambiguous", () => {
  for (const key of ["serviceId", "subjectId", "instanceIndex"]) {
    const other = structuredClone(fresh); other.message.serviceInstance = { ...nativeInstance, [key]: key === "instanceIndex" ? 1 : "other" };
    expect(selectProduct([other], "brake", binding.serviceVersion, binding).result).toBeUndefined();
  }
  expect(selectProduct([fresh], "brake", binding.serviceVersion).proof).toBeUndefined();
  const other = structuredClone(fresh); other.message.serviceInstance = { ...nativeInstance, instanceId: "other-process" };
  expect(selectProduct([fresh, other], "brake", binding.serviceVersion, binding)).toMatchObject({ ambiguous: true, result: undefined });
  expect(selectProduct([fresh], "brake", binding.serviceVersion, { ...binding, current: false }).proof).toBeUndefined();
});
test("no receipt-time fallback when source is absent/future; incomplete window is not proof", () => {
  for (const source of [undefined, "invalid", "2099-01-01T00:00:00.000Z"]) {
    const invalid = structuredClone(fresh); invalid.message.sourceEventTime = source;
    expect(selectProduct([invalid], "brake", binding.serviceVersion, binding).result).toBeUndefined();
  }
  const partial = structuredClone(fresh); partial.message.messageType = "WINDOW_COMPLETION"; partial.message.content = { status: "PARTIAL" };
  expect(selectProduct([partial], "brake", binding.serviceVersion, binding).proof).toBeUndefined();
});
test("Cloud binding requires exact installed allocation, not a pending instance", () => {
  const row = { subject: nativeInstance.subjectId, service: { id: nativeInstance.serviceId, title: "Brake" }, num_instance: 1,
    service_versions: { installed_service_version: { version: binding.serviceVersion }, pending_service_version: { version: "8.0.0" } },
    instances: { state: "CURRENT", value: [{ instance_id: 0, version: binding.serviceVersion, run_state: "active", error_message: null }] } };
  expect(backendBinding(binding.unitSystemUid, row, true, "v3")).toEqual(binding);
  row.instances.value[0].version = "8.0.0";
  expect(backendBinding(binding.unitSystemUid, row, true, "v3")).toBeUndefined();
});
