import { describe, expect, it } from "vitest";
import { FixturePresenterReadAdapter } from "../../src/adapters/fixtures";
import {
  FixtureReadOnlyAdapter,
  aosCloudReadModel,
  brakeCloudReadModel,
  normalizeContractRecord,
  readOnlyFixtureById,
  readOnlyFixtureIds,
  validateReadRequest,
} from "../../src/adapters/read-only";
import type { ContractRecord } from "../../src/adapters/read-only";

const NOW = "2026-08-30T09:00:02.000Z";
const clock = () => NOW;

async function snapshot(id: string) {
  return new FixtureReadOnlyAdapter(new FixturePresenterReadAdapter(id), id, clock).read();
}

describe("closed read request plans", () => {
  it("accepts every catalog request as a fixed GET-only route", () => {
    for (const id of readOnlyFixtureIds) {
      for (const request of readOnlyFixtureById(id).plans) {
        expect(validateReadRequest(request)).toBe(request);
        expect(request.method).toBe("GET");
      }
    }
  });

  it.each([
    [{ source: "AOSCLOUD_OEM", routeId: "OEM_USERS_ME", method: "POST", selectors: { contextId: "x" }, pagination: "SINGLE" }, "READ_METHOD_FORBIDDEN"],
    [{ source: "AOSCLOUD_OEM", routeId: "BRAKE_USERS_ME", method: "GET", selectors: { contextId: "x" }, pagination: "SINGLE" }, "READ_ROUTE_FORBIDDEN"],
    [{ source: "AOSCLOUD_OEM", routeId: "OEM_USERS_ME", method: "GET", selectors: { contextId: "x" }, pagination: "SINGLE", url: "external" }, "READ_PLAN_FIELD_FORBIDDEN"],
    [{ source: "AOSCLOUD_OEM", routeId: "OEM_USERS_ME", method: "GET", selectors: { contextId: "x", path: "arbitrary" }, pagination: "SINGLE" }, "READ_SELECTOR_FORBIDDEN"],
    [{ source: "AOSCLOUD_OEM", routeId: "OEM_USERS_ME", method: "GET", selectors: { contextId: "x" }, pagination: "PARTIAL" }, "READ_PAGINATION_REQUIRED"],
  ])("rejects a non-allowlisted plan", (request, reason) => {
    expect(() => validateReadRequest(request)).toThrow(reason as string);
  });
});

describe("AosCloud fixture projection", () => {
  it("marks Unit-owned groups not applicable before M1 instead of inventing a Unit", () => {
    const fixture = readOnlyFixtureById("m0");
    const cloud = aosCloudReadModel(fixture, clock);
    expect(cloud.bindings).toMatchObject({ value: null, state: "NOT_APPLICABLE", reason: "NO_UNIT_BEFORE_M1" });
    expect(cloud.unitSets.state).toBe("NOT_APPLICABLE");
    expect(brakeCloudReadModel(fixture, clock).brake).toMatchObject({ value: null, state: "NOT_APPLICABLE" });
  });

  it("joins exact Test/Production bindings, Main Nodes and disjoint complete Unit Sets", () => {
    const projection = aosCloudReadModel(readOnlyFixtureById("ready"), clock);
    expect(projection.session.value).toMatchObject({ role: "OEM", routeContext: "oem-delivery-read" });
    expect(projection.bindings.state).toBe("CURRENT");
    expect(projection.bindings.value?.map((item) => [item.label, item.wireRole])).toEqual([
      ["Test Vehicle", "VALIDATION"],
      ["Production Vehicle", "PRODUCTION"],
    ]);
    expect(projection.unitSets.state).toBe("CURRENT");
    expect(projection.unitSets.value?.map((item) => item.memberUnitFingerprints)).toEqual([
      ["unit:test:7c91"],
      ["unit:production:4e22"],
    ]);
  });

  it.each([
    ["read-only-truncated-membership", "UNIT_SET_MEMBERSHIP_INCOMPLETE"],
    ["read-only-crossed-membership", "UNIT_SET_MEMBERSHIP_INCOMPLETE"],
    ["read-only-duplicate-membership", "UNIT_SET_MEMBERSHIP_INCOMPLETE"],
    ["read-only-prior-run-membership", "UNIT_SET_MEMBERSHIP_INCOMPLETE"],
  ])("fails closed for %s", (id, reason) => {
    const projection = aosCloudReadModel(readOnlyFixtureById(id), clock);
    expect(projection.unitSets).toMatchObject({ value: null, state: "INCOMPLETE", transport: "MALFORMED", reason });
  });

  it.each(["read-only-wrong-role", "read-only-missing-permission"])("does not infer OEM authority for %s", (id) => {
    const projection = aosCloudReadModel(readOnlyFixtureById(id), clock);
    expect(projection.session).toMatchObject({ value: null, state: "INCOMPLETE", reason: "OEM_SESSION_SCOPE_MISMATCH" });
    expect(projection.units).toMatchObject({ value: null, state: "UNKNOWN", reason: "OEM_SESSION_NOT_CURRENT" });
  });

  it("keeps Brake SP1 ownership independent", () => {
    const projection = aosCloudReadModel(readOnlyFixtureById("read-only-wrong-owner"), clock);
    expect(projection.brakeSession).toMatchObject({ value: null, state: "INCOMPLETE", reason: "BRAKE_SESSION_SCOPE_MISMATCH" });
    expect(projection.serviceLogs).toMatchObject({ value: null, state: "UNKNOWN", reason: "BRAKE_SESSION_NOT_CURRENT" });
    expect(projection.units.state).toBe("CURRENT");
  });

  it.each(["read-only-extra-pending-recipient", "read-only-missing-pending-recipient"])("rejects mismatched effective recipients for %s", (id) => {
    expect(aosCloudReadModel(readOnlyFixtureById(id), clock).releases).toMatchObject({
      value: null,
      state: "INCOMPLETE",
      reason: "RELEASE_RECIPIENT_SET_MISMATCH",
    });
  });

  it.each(["read-only-campaign-unit-ids", "read-only-campaign-units-ids"])("preserves unresolved Campaign shape without claiming success for %s", (id) => {
    expect(aosCloudReadModel(readOnlyFixtureById(id), clock).releases).toMatchObject({
      value: null,
      state: "INCOMPLETE",
      reason: "CAMPAIGN_RESPONSE_SHAPE_UNRESOLVED",
    });
  });

  it("preserves all documented log states and rejects a cross-owner family", () => {
    const ready = aosCloudReadModel(readOnlyFixtureById("ready"), clock);
    expect(ready.unitLogs.value?.map((item) => item.cloudState)).toEqual([
      "created", "sent", "waiting unit", "receiving", "done", "error", "empty log has been provided",
    ]);
    expect(aosCloudReadModel(readOnlyFixtureById("read-only-wrong-log-family"), clock).serviceLogs).toMatchObject({
      value: null,
      state: "INCOMPLETE",
      reason: "SERVICE_LOG_SCOPE_MISMATCH",
    });
  });
});

describe("source, error and Brake mapping", () => {
  it.each([
    ["read-only-unauthenticated", "session", "UNKNOWN", "UNAUTHENTICATED"],
    ["read-only-forbidden", "unitLogs", "UNKNOWN", "FORBIDDEN"],
    ["read-only-not-found", "releases", "UNKNOWN", "NOT_FOUND_OR_INACCESSIBLE"],
    ["read-only-rejected", "units", "UNKNOWN", "REJECTED"],
  ] as const)("maps %s without hidden success", (id, field, state, transport) => {
    const value = aosCloudReadModel(readOnlyFixtureById(id), clock)[field];
    expect(value).toMatchObject({ value: null, state, transport });
  });

  it("retains an accepted prior value only as stale when the source is unavailable", () => {
    const currentRecord: ContractRecord<{ state: string }> = {
      contractClass: "CONTRACT_SYNTHETIC",
      source: "BRAKE_BACKEND",
      outcome: "OK",
      freshness: "CURRENT",
      sourceTimestamp: "2026-08-30T08:59:00.000Z",
      value: { state: "accepted" },
    };
    const current = normalizeContractRecord(currentRecord, clock, "FIXTURE_POLICY_EXPLICIT_V1");
    const unavailable = normalizeContractRecord({ ...currentRecord, outcome: "SOURCE_UNAVAILABLE", value: null }, clock, "FIXTURE_POLICY_EXPLICIT_V1", current);
    expect(unavailable).toMatchObject({ value: { state: "accepted" }, state: "STALE", transport: "SOURCE_UNAVAILABLE", reason: "Current state cannot be confirmed" });
    expect(unavailable.sourceTimestamp).toBe(current.sourceTimestamp);
  });

  it("treats an empty current Brake page as factual and a notification as reread-only", () => {
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-brake-empty"), clock).brake).toMatchObject({ value: [], state: "CURRENT" });
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-notification"), clock)).toMatchObject({ notificationRereads: 2, brake: { state: "CURRENT" } });
  });

  it("keeps pending-event VDP provenance null and never infers Unit readiness", () => {
    const brake = brakeCloudReadModel(readOnlyFixtureById("ready"), clock).brake;
    expect(brake.value?.find((item) => item.resourceType === "events")).toMatchObject({
      state: "PENDING_ASSESSMENT_CORRELATION",
      vdpVersion: null,
      vdpDigest: null,
    });
    expect(JSON.stringify(brake)).not.toMatch(/Unit ready|Cloud lifecycle/i);
  });
});

describe("composed Presenter snapshot", () => {
  it("is immutable, source-scoped and rebuilt without an authoritative adapter cache", async () => {
    const adapter = new FixtureReadOnlyAdapter(new FixturePresenterReadAdapter("ready"), "ready", clock);
    const first = await adapter.read();
    const second = await adapter.read();
    expect(first).not.toBe(second);
    expect(first.readOnly).not.toBe(second.readOnly);
    expect(Object.isFrozen(first)).toBe(true);
    expect(first.readOnly).toMatchObject({ contractClass: "CONTRACT_SYNTHETIC", notificationRereads: 0 });
  });

  it("keeps a Brake source failure independent from AosCloud Unit state", async () => {
    const value = await snapshot("read-only-schema-invalid");
    expect(value.readOnly?.brake).toMatchObject({ state: "UNKNOWN", transport: "SCHEMA_INVALID" });
    expect(value.readOnly?.units.state).toBe("CURRENT");
    expect(value.teams.brake.backendStatus).toContain("UNKNOWN");
  });
});
