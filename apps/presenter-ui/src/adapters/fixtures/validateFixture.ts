import type { PresenterSnapshot } from "../../domain";

const forbiddenKey = /(credential|password|private.?key|jwt|helper.?capability|raw.?response|absolute.?path)/i;

export function validateFixture(value: PresenterSnapshot): string[] {
  const errors: string[] = [];
  if (!value.fixtureId || !value.fixtureLabel.includes("not live")) {
    errors.push("fixture provenance must be explicit");
  }
  if (!value.vehicle.source.fixture || !value.workspace.source.fixture) {
    errors.push("fixture sources must be marked fixture-only");
  }
  const visit = (node: unknown, path: string): void => {
    if (Array.isArray(node)) {
      node.forEach((entry, index) => visit(entry, `${path}[${index}]`));
      return;
    }
    if (node && typeof node === "object") {
      for (const [key, entry] of Object.entries(node)) {
        if (forbiddenKey.test(key)) errors.push(`forbidden fixture field: ${path}.${key}`);
        visit(entry, `${path}.${key}`);
      }
    }
  };
  visit(value, "fixture");
  for (const [id, team] of Object.entries(value.teams)) {
    if (team.id !== id || team.releases.some((item) => item.team !== id)) errors.push(`team isolation mismatch: ${id}`);
    for (const release of team.releases) {
      if (release.stages.length !== 5) errors.push(`${release.id} must expose five stages`);
      if (release.team === "platform" && release.details.quota) errors.push("Platform Details must not expose Service quota");
      if (release.team !== "platform" && !release.details.quota) errors.push(`${release.id} must expose approved Service quota`);
    }
  }
  return errors;
}
