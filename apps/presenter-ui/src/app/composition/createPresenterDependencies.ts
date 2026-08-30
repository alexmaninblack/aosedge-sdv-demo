import { FixturePresenterReadAdapter } from "../../adapters/fixtures";
import { FixtureReadOnlyAdapter } from "../../adapters/read-only";
import type { PresenterDependencies } from "./PresenterDependencies";

const FIXTURE_READ_COMPLETED_AT = "2026-08-30T09:00:02.000Z";

export function createPresenterDependencies(location: Pick<Location, "search">): PresenterDependencies {
  const fixtureId = new URLSearchParams(location.search).get("fixture") ?? "ready";
  const shell = new FixturePresenterReadAdapter(fixtureId);
  return {
    readPort: new FixtureReadOnlyAdapter(shell, fixtureId, () => FIXTURE_READ_COMPLETED_AT),
  };
}
