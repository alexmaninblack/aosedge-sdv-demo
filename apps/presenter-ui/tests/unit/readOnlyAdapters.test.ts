import { describe, expect, it } from "vitest";
import { FixturePresenterReadAdapter } from "../../src/adapters/fixtures";
import {
  FixtureReadOnlyAdapter,
  BRAKE_BACKEND_ROUTE_IDS,
  BRAKE_SP1_ROUTE_IDS,
  OEM_ROUTE_IDS,
  aosCloudReadModel,
  brakeCloudReadModel,
  normalizeContractRecord,
  readOnlyFixtureById,
  readOnlyFixtureIds,
  validateReadOnlyFixturePackageEnvelope,
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

  it("rejects an open package, duplicate plan, malformed fingerprint and inconsistent current-Unit context", () => {
    const open = { ...readOnlyFixtureById("ready"), credential: "forbidden" };
    expect(() => validateReadOnlyFixturePackageEnvelope(open)).toThrow("FIXTURE_PACKAGE_MALFORMED");

    const duplicate = readOnlyFixtureById("ready");
    duplicate.plans = [...duplicate.plans, duplicate.plans[0]!];
    expect(() => validateReadOnlyFixturePackageEnvelope(duplicate)).toThrow("READ_PLAN_DUPLICATE");

    expect(() => validateReadRequest({ source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_DETAIL", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "093c912a-aa98-4d23-9a0e-75a8454296e6" }, pagination: "SINGLE" })).toThrow("READ_SELECTOR_MALFORMED");

    const context = readOnlyFixtureById("ready");
    context.brake.contextSystemUidFingerprint = null;
    expect(() => validateReadOnlyFixturePackageEnvelope(context)).toThrow("CURRENT_UNIT_CONTEXT_MALFORMED");
  });

  it("requires the exact per-object page/detail plan set for both vehicle identities", () => {
    const fixture = readOnlyFixtureById("ready");
    const routeIds = fixture.plans.map((request) => request.routeId);
    expect([...OEM_ROUTE_IDS, ...BRAKE_SP1_ROUTE_IDS, ...BRAKE_BACKEND_ROUTE_IDS].every((routeId) => routeIds.includes(routeId))).toBe(true);
    expect(fixture.plans).toHaveLength(36);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_UNIT_DETAIL")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_UNIT_NODES_PAGE")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_NODE_DETAIL")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_SUBJECT_SERVICES_PAGE")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_UNIT_SET_DETAIL")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_UNIT_SET_MEMBERS_PAGE")).toHaveLength(2);
    expect(fixture.plans.filter((request) => request.routeId === "OEM_UNIT_LOG_DETAIL")).toHaveLength(7);

    fixture.plans = fixture.plans.filter((request) => request.routeId !== "OEM_CAMPAIGN_DETAIL");
    expect(() => validateReadOnlyFixturePackageEnvelope(fixture)).toThrow("READ_PLAN_INCOMPLETE");
  });

  it("rejects extra and wrong-object plans and binds backend reads to the exact current Unit", () => {
    const extra = readOnlyFixtureById("ready");
    extra.plans = [...extra.plans, {
      source: "AOSCLOUD_OEM",
      routeId: "OEM_NODE_DETAIL",
      method: "GET",
      selectors: { contextId: "vehicle-inventory", objectFingerprint: "node:other-main:0bad" },
      pagination: "SINGLE",
    }];
    expect(() => validateReadOnlyFixturePackageEnvelope(extra)).toThrow("READ_PLAN_UNEXPECTED");

    const wrong = readOnlyFixtureById("ready");
    wrong.plans = wrong.plans.map((request) => request.routeId === "OEM_NODE_DETAIL" && request.selectors.objectFingerprint === "node:production-main:59bd"
      ? { ...request, selectors: { ...request.selectors, objectFingerprint: "node:other-main:0bad" } }
      : request);
    expect(() => validateReadOnlyFixturePackageEnvelope(wrong)).toThrow("READ_PLAN_UNEXPECTED");

    const production = readOnlyFixtureById("production");
    expect(production.plans.filter((request) => request.source === "BRAKE_BACKEND")).toHaveLength(4);
    expect(production.plans.filter((request) => request.source === "BRAKE_BACKEND").every((request) =>
      request.selectors.contextId === "current-production-unit"
      && request.selectors.objectFingerprint === "uid:production:9b14")).toBe(true);
    expect(readOnlyFixtureById("read-only-brake-context-unavailable").plans.some((request) => request.source === "BRAKE_BACKEND")).toBe(false);
  });

  it("executes declared plans only in their composition-owned route/role context", () => {
    const adapter = new FixtureReadOnlyAdapter(new FixturePresenterReadAdapter("ready"), "ready", clock);
    const request = readOnlyFixtureById("ready").plans.find((plan) => plan.routeId === "OEM_NODE_DETAIL")!;
    const result = adapter.read(request, { routeContext: "oem-delivery-read", role: "OEM" }, clock);
    expect(result).toMatchObject({
      plan: request,
      context: { routeContext: "oem-delivery-read", role: "OEM" },
      readCompletedAt: NOW,
      record: { source: "AOSCLOUD_OEM", outcome: "OK", value: { mainNodeFingerprint: request.selectors.objectFingerprint } },
    });
    expect(Object.isFrozen(result)).toBe(true);
    expect(Object.isFrozen(result.record)).toBe(true);

    expect(() => adapter.read(request, { routeContext: "brake-sp1-read", role: "Service Provider" }, clock)).toThrow("READ_CONTEXT_SCOPE_MISMATCH");
    expect(() => adapter.read(
      { ...request, selectors: { ...request.selectors, objectFingerprint: "node:other-main:0bad" } },
      { routeContext: "oem-delivery-read", role: "OEM" },
      clock,
    )).toThrow("READ_PLAN_NOT_DECLARED");
  });

  it("executes Unit Set membership as separate complete per-Set reads", () => {
    const adapter = new FixtureReadOnlyAdapter(new FixturePresenterReadAdapter("read-only-paginated-membership"), "read-only-paginated-membership", clock);
    const plans = readOnlyFixtureById("read-only-paginated-membership").plans.filter((plan) => plan.routeId === "OEM_UNIT_SET_MEMBERS_PAGE");
    const reads = plans.map((plan) => adapter.read(plan, { routeContext: "oem-delivery-read", role: "OEM" }, clock));
    expect(reads.map((read) => (read.record.value as readonly { role: string }[]).map((page) => page.role))).toEqual([
      ["TEST", "TEST"],
      ["PRODUCTION"],
    ]);
    expect(reads.every((read) => read.plan.pagination === "COMPLETE")).toBe(true);
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

  it("requires authority for every requested OEM read group", () => {
    const projection = aosCloudReadModel(readOnlyFixtureById("read-only-missing-campaign-permission"), clock);
    expect(projection.session).toMatchObject({ value: null, state: "INCOMPLETE", reason: "OEM_SESSION_SCOPE_MISMATCH" });
    expect(projection.releases).toMatchObject({ value: null, state: "UNKNOWN", reason: "OEM_SESSION_NOT_CURRENT" });
    expect(projection.unitLogs).toMatchObject({ value: null, state: "UNKNOWN", reason: "OEM_SESSION_NOT_CURRENT" });
  });

  it.each(["read-only-missing-unit", "read-only-ambiguous-unit", "read-only-wrong-main-node"])("rejects an unprovable Unit/Main Node binding for %s", (id) => {
    expect(aosCloudReadModel(readOnlyFixtureById(id), clock).units).toMatchObject({
      value: null,
      state: "INCOMPLETE",
      reason: "UNIT_NODE_BINDING_MISMATCH",
    });
  });

  it("accepts only a cursor-linked complete multi-page Unit Set", () => {
    expect(aosCloudReadModel(readOnlyFixtureById("read-only-paginated-membership"), clock).unitSets.state).toBe("CURRENT");
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

  it("validates authority, identity, joins, membership, recipients and log scope before retaining STALE facts", () => {
    const authority = readOnlyFixtureById("ready");
    authority.aosCloud.session.freshness = "STALE";
    authority.aosCloud.session.value = { ...authority.aosCloud.session.value!, role: "Fleet Owner" };
    expect(aosCloudReadModel(authority, clock).session).toMatchObject({ value: null, state: "INCOMPLETE", reason: "OEM_SESSION_SCOPE_MISMATCH" });

    const identity = readOnlyFixtureById("ready");
    identity.aosCloud.bindings.freshness = "STALE";
    identity.aosCloud.bindings.value = identity.aosCloud.bindings.value?.map((item) => item.role === "PRODUCTION"
      ? { ...item, systemUidFingerprint: "uid:test:76d2" }
      : item) ?? null;
    expect(aosCloudReadModel(identity, clock).bindings).toMatchObject({ value: null, state: "INCOMPLETE", reason: "VEHICLE_BINDING_AMBIGUOUS" });

    const join = readOnlyFixtureById("ready");
    join.aosCloud.units.freshness = "STALE";
    join.aosCloud.units.value = join.aosCloud.units.value?.map((item) => item.role === "TEST"
      ? { ...item, mainNodeFingerprint: "node:other-main:0bad" }
      : item) ?? null;
    expect(aosCloudReadModel(join, clock).units).toMatchObject({ value: null, state: "INCOMPLETE", reason: "UNIT_NODE_BINDING_MISMATCH" });

    const membership = readOnlyFixtureById("ready");
    membership.aosCloud.unitSets.freshness = "STALE";
    membership.aosCloud.unitSetPages = membership.aosCloud.unitSetPages.map((page) => ({
      ...page,
      members: page.role === "TEST" ? ["unit:production:4e22"] : ["unit:test:7c91"],
    }));
    expect(aosCloudReadModel(membership, clock).unitSets).toMatchObject({ value: null, state: "INCOMPLETE", reason: "UNIT_SET_MEMBERSHIP_INCOMPLETE" });

    const recipient = readOnlyFixtureById("ready");
    recipient.aosCloud.releases.freshness = "STALE";
    recipient.aosCloud.releases.value = recipient.aosCloud.releases.value?.map((item) => item.kind === "VERIFICATION_BATCH"
      ? { ...item, targetFingerprints: ["unit:test:7c91", "unit:production:4e22"] }
      : item) ?? null;
    expect(aosCloudReadModel(recipient, clock).releases).toMatchObject({ value: null, state: "INCOMPLETE", reason: "RELEASE_RECIPIENT_SET_MISMATCH" });

    const logs = readOnlyFixtureById("ready");
    logs.aosCloud.serviceLogs.freshness = "STALE";
    logs.aosCloud.serviceLogs.value = logs.aosCloud.serviceLogs.value?.map((item) => ({ ...item, family: "unit-logs", owner: "OEM" })) ?? null;
    expect(aosCloudReadModel(logs, clock).serviceLogs).toMatchObject({ value: null, state: "INCOMPLETE", reason: "SERVICE_LOG_SCOPE_MISMATCH" });

    const brake = readOnlyFixtureById("ready");
    brake.brake.resources.freshness = "STALE";
    brake.brake.resources.value = brake.brake.resources.value?.map((item) => ({ ...item, unitSystemUidFingerprint: "uid:production:9b14" })) ?? null;
    expect(brakeCloudReadModel(brake, clock).brake).toMatchObject({ value: null, state: "INCOMPLETE", reason: "BRAKE_RESOURCE_SCOPE_MISMATCH" });
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

    const unaccepted = normalizeContractRecord(
      { ...currentRecord, outcome: "SOURCE_UNAVAILABLE", value: null },
      clock,
      "FIXTURE_POLICY_EXPLICIT_V1",
      { ...current, state: "UNKNOWN" },
    );
    expect(unaccepted).toMatchObject({ value: null, state: "UNKNOWN", transport: "SOURCE_UNAVAILABLE" });
  });

  it("treats an empty current Brake page as factual and a notification as reread-only", () => {
    const empty = brakeCloudReadModel(readOnlyFixtureById("read-only-brake-empty"), clock).brake;
    expect(empty.state).toBe("CURRENT");
    expect(empty.value?.every((item) => item.count === 0)).toBe(true);
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-notification"), clock)).toMatchObject({ notificationRereads: 2, brake: { state: "CURRENT" } });
  });

  it("keeps pending-event VDP provenance null and never infers Unit readiness", () => {
    const brake = brakeCloudReadModel(readOnlyFixtureById("ready"), clock).brake;
    expect(brake.value?.find((item) => item.resourceType === "EVENT")).toMatchObject({
      state: "PENDING_ASSESSMENT_CORRELATION",
      vdpVersion: null,
      vdpDigest: null,
    });
    expect(JSON.stringify(brake)).not.toMatch(/Unit ready|Cloud lifecycle/i);
  });

  it("requires the exact current Unit and a complete REST page for Brake", () => {
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-brake-wrong-unit"), clock).brake).toMatchObject({
      value: null,
      state: "INCOMPLETE",
      reason: "BRAKE_RESOURCE_SCOPE_MISMATCH",
    });
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-brake-incomplete-page"), clock).brake).toMatchObject({
      value: null,
      state: "INCOMPLETE",
    });
    expect(brakeCloudReadModel(readOnlyFixtureById("read-only-brake-partial-window"), clock).brake.value?.find((item) => item.resourceType === "WINDOW")).toMatchObject({
      state: "PARTIAL",
      deliveryState: "RECEIVING",
      projectionState: "PARTIAL",
      terminalState: null,
    });
  });

  it("fails closed for an invalid date, unknown enum and cross-owner record", () => {
    expect(aosCloudReadModel(readOnlyFixtureById("read-only-invalid-date"), clock).units).toMatchObject({ value: null, state: "INCOMPLETE", transport: "MALFORMED" });
    expect(aosCloudReadModel(readOnlyFixtureById("read-only-unknown-enum"), clock).units).toMatchObject({ value: null, state: "INCOMPLETE", transport: "MALFORMED" });
    const fixture = readOnlyFixtureById("ready");
    fixture.aosCloud.units.source = "BRAKE_BACKEND";
    expect(aosCloudReadModel(fixture, clock).units).toMatchObject({ value: null, state: "INCOMPLETE", transport: "MALFORMED" });
  });

  it("projects an explicitly hidden fact as REDACTED rather than absent", () => {
    expect(aosCloudReadModel(readOnlyFixtureById("read-only-redacted"), clock).unitLogs).toMatchObject({
      value: null,
      state: "REDACTED",
      transport: "AVAILABLE",
      reason: "LOG_METADATA_REDACTED",
    });
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

  it("never falls an unknown fixture or unauthenticated session back to current readiness", async () => {
    const unknown = await snapshot("not-a-known-fixture");
    expect(unknown.readOnly?.session).toMatchObject({ value: null, state: "UNKNOWN", transport: "SOURCE_UNAVAILABLE" });
    expect(unknown.vehicle.value).toBe("unavailable");

    const unauthenticated = await snapshot("read-only-unauthenticated");
    expect(unauthenticated.vehicle.value).toBe("unavailable");
    expect(unauthenticated.teams.platform.productStatus).toBe("VDP v—");
  });

  it("uses executed detail results as the sole projection input", async () => {
    const rawFixture = readOnlyFixtureById("read-only-missing-log-detail");
    expect(aosCloudReadModel(rawFixture, clock).unitLogs.state).toBe("CURRENT");

    const composed = await snapshot("read-only-missing-log-detail");
    expect(composed.readOnly?.unitLogs).toMatchObject({
      value: null,
      state: "UNKNOWN",
      transport: "NOT_FOUND_OR_INACCESSIBLE",
      reason: "FIXTURE_OBJECT_NOT_FOUND",
    });
  });
});
