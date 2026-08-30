import { describe, expect, it } from "vitest";
import { fixtureById, fixtureIds, validateFixture } from "../../src/adapters/fixtures";
import { readOnlyFixtureById, readOnlyFixtureIds, validateReadRequest } from "../../src/adapters/read-only";

describe("fixture contract", () => {
  it("validates every deterministic shell fixture against one read model", () => {
    expect(fixtureIds.length).toBeGreaterThanOrEqual(20);
    for (const id of fixtureIds) {
      const fixture = fixtureById(id);
      expect(fixture.fixtureId, id).toBe(id);
      expect(validateFixture(fixture), id).toEqual([]);
    }
  });

  it("keeps Platform free of Service quota and Services quota-bound", () => {
    const fixture = fixtureById("ready");
    expect(fixture.teams.platform.releases.every((item) => item.details.quota === undefined)).toBe(true);
    expect(fixture.teams.brake.releases.every((item) => item.details.quota)).toBeTruthy();
    expect(fixture.teams.tire.releases.every((item) => item.details.quota)).toBeTruthy();
  });

  it("labels every new raw fixture contract-synthetic and validates every closed plan", () => {
    expect(readOnlyFixtureIds.length).toBeGreaterThanOrEqual(20);
    for (const id of readOnlyFixtureIds) {
      const fixture = readOnlyFixtureById(id);
      expect(fixture.fixtureId).toBe(id);
      expect(fixture.contractClass).toBe("CONTRACT_SYNTHETIC");
      fixture.plans.forEach((request) => expect(validateReadRequest(request)).toBe(request));
    }
  });

  it("contains no privileged material, arbitrary URL, raw response or full private identity", () => {
    const serialized = JSON.stringify([
      ...fixtureIds.map(fixtureById),
      ...readOnlyFixtureIds.map(readOnlyFixtureById),
    ]);
    expect(serialized).not.toMatch(/password|privateKey|private_key|certificateContent|authHeader|authorizationHeader|helperCapability|rawResponse/i);
    expect(serialized).not.toMatch(/https?:\/\//);
    expect(serialized).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i);
    expect(serialized).not.toMatch(/\b[A-Za-z0-9_-]{48,}\b/);
  });
});
