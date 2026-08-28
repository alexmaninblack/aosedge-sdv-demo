import { describe, expect, it } from "vitest";
import { deriveMilestone, initialPresentationState, presentationReducer } from "../../src/domain";
import { fixtureById } from "../../src/adapters/fixtures";

describe("presentation reducer", () => {
  it("preserves independent team scroll and focus", () => {
    const platform = presentationReducer(initialPresentationState, { type: "remember-team", team: "platform", scroll: 420, focus: "platform-v2-details" });
    const brake = presentationReducer(platform, { type: "remember-team", team: "brake", scroll: 190, focus: "brake-v1-details" });
    expect(brake.scrollByTeam).toEqual({ platform: 420, brake: 190, tire: 0 });
    expect(brake.focusByTeam.platform).toBe("platform-v2-details");
    expect(brake.focusByTeam.brake).toBe("brake-v1-details");
  });

  it("keeps action presentation separate from observed fixture state", () => {
    const fixture = fixtureById("ready");
    const state = presentationReducer(initialPresentationState, { type: "confirm-fixture-action", action: "Authorize Test Vehicle deployment" });
    expect(state.actionNotice).toContain("no external operation submitted");
    expect(fixture.teams.platform.releases[0]?.stages[1]?.state).toBe("ready");
  });

  it("derives a milestone without writing lifecycle state", () => {
    const fixture = fixtureById("production");
    expect(deriveMilestone(fixture.teams.platform, fixture.teams.brake)).toBe("G3 capability · 2 of 2 releases ready");
    expect(fixture.global.milestone).toBe("G3 capability · 2 of 2 releases ready");
  });
});
