import { expect, test } from "vitest";
import { functionPage, selectFunction } from "../../src/features/service-team/functionObservation";
import { binding, nativeInstance } from "./backendFixture";
const now = Date.parse("2026-09-18T22:00:00.000Z");
const item = () => ({ backendReceivedAt: new Date(now).toISOString(), authority: "FUNCTION_TEAM_REPORTED_OBSERVATION",
  stale: false, clockSkew: false, deliveryState: "DURABLY_RECEIVED", message: { schemaVersion: 3, contractVersion: "3.0.0",
    messageType: "BRAKE_FUNCTION_OBSERVATION", unitSystemUid: binding.unitSystemUid, unitRole: "VALIDATION",
    serviceInstance: { ...nativeInstance }, serviceVersion: binding.serviceVersion, serviceProfile: "v3", generation: 2, sequence: 10,
    observedAt: new Date(now - 1000).toISOString(), contentSha256: "a".repeat(64), content: {
      connection: "CONNECTED", input: { state: "RECEIVING", reason: "NONE" }, activity: { state: "WAITING", reason: "NOT_QUALIFIED", episodeId: null },
      delivery: { state: "IDLE", queuedMessages: 0, lastReceiptAt: null }, advisory: { state: "WAITING", requestId: null }, lastResult: null } } });
const resource = (items = [item()]) => ({ state: "OBSERVED", data: { schemaVersion: 3, contractVersion: "3.0.0",
  resourceType: "FUNCTION_OBSERVATION", unitSystemUid: binding.unitSystemUid, items, truncated: false } });
test("current allocation/profile source report keeps input and activity separate", () => {
  const selected = selectFunction(resource(), "brake", binding, now);
  expect(selected.state).toBe("CURRENT"); expect(selected.item?.message.content.input.state).toBe("RECEIVING");
  expect(selected.item?.message.content.activity.state).toBe("WAITING");
  expect(selectFunction(resource(), "brake", { ...binding, profile: "v2" }, now).state).toBe("UNREPORTED");
});
test.each(["old", "future", "stale", "partial", "truncated", "cloud-stale"])("%s cannot be fresh from recent receipt", change => {
  const value = resource();
  if (change === "old") value.data.items[0].message.observedAt = new Date(now - 90001).toISOString();
  if (change === "future") value.data.items[0].message.observedAt = new Date(now + 1).toISOString();
  if (change === "stale") value.data.items[0].stale = true;
  if (change === "partial") value.state = "UNAVAILABLE";
  if (change === "truncated") value.data.truncated = true;
  expect(selectFunction(value, "brake", { ...binding, current: change !== "cloud-stale" }, now).state).toBe("LAST_KNOWN");
});
test("source generation/sequence wins over late receipt; conflict never falls back to green", () => {
  const older = item(); older.message.sequence = 9; older.backendReceivedAt = new Date(now + 5000).toISOString();
  expect(selectFunction(resource([older, item()]), "brake", binding, now).item?.message.sequence).toBe(10);
  const conflict = item(); conflict.deliveryState = "CONFLICT";
  expect(selectFunction(resource([older, conflict]), "brake", binding, now).state).toBe("CONFLICT");
});
test("same-release process ambiguity is not resolved by receipt time", () => {
  const other = item(); other.message.serviceInstance.instanceId = "old-process";
  expect(selectFunction(resource([other, item()]), "brake", binding, now).state).toBe("AMBIGUOUS");
});
test.each(["extra", "scope", "profile", "identity", "enum", "semantics", "unsafe-int", "advisory", "result", "digest"])("invalid %s projection is rejected", change => {
  const value = resource(), m = value.data.items[0].message;
  if (change === "extra") Object.assign(m, { secret: "not-a-secret-fixture" });
  if (change === "scope") m.unitSystemUid = "other";
  if (change === "profile") m.serviceProfile = "v8";
  if (change === "identity") m.serviceInstance.instanceId = "a\n";
  if (change === "enum") m.content.input.state = "GOOD";
  if (change === "semantics") m.content.input.reason = "SOURCE_GAP";
  if (change === "unsafe-int") m.sequence = Number.MAX_SAFE_INTEGER + 1;
  if (change === "advisory") m.content.advisory.state = "CONFIRMED";
  if (change === "result") Object.assign(m.content, { lastResult: { kind: "SCORE" } });
  if (change === "digest") m.contentSha256 = "unverified";
  expect(() => functionPage(value, "brake", binding.unitSystemUid)).toThrow();
});
