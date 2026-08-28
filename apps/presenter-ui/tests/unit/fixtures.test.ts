import { describe, expect, it } from "vitest";
import { fixtureById, fixtureIds, validateFixture } from "../../src/adapters/fixtures";

describe("fixture contract", () => {
  it("validates every deterministic fixture against one read model", () => {
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

  it("contains no credential or privileged helper capability fields", () => {
    const serialized = JSON.stringify(fixtureIds.map(fixtureById));
    expect(serialized).not.toMatch(/password|privateKey|private_key|jwt|helperCapability|rawResponse|absolutePath/i);
    expect(serialized).not.toMatch(/https?:\/\//);
  });
});
