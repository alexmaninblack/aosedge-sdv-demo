import { FixturePresenterReadAdapter } from "../../adapters/fixtures";
import type { PresenterDependencies } from "./PresenterDependencies";

export function createPresenterDependencies(location: Pick<Location, "search">): PresenterDependencies {
  const fixtureId = new URLSearchParams(location.search).get("fixture") ?? "ready";
  return { readPort: new FixturePresenterReadAdapter(fixtureId) };
}
