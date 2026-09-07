import { FixturePresenterReadAdapter } from "../../adapters/fixtures";
import { FixtureReadOnlyAdapter } from "../../adapters/read-only";
import type { PresenterDependencies } from "./PresenterDependencies";
import { LocalPresenterReadAdapter } from "../../adapters/local/LocalPresenterReadAdapter";
import { LocalPresenterCommandAdapter } from "../../adapters/local/LocalPresenterCommandAdapter";

const FIXTURE_READ_COMPLETED_AT = "2026-08-30T09:00:02.000Z";

export function createPresenterDependencies(location: Pick<Location, "search">): PresenterDependencies {
  if (!new URLSearchParams(location.search).has("fixture")) return { readPort: new LocalPresenterReadAdapter(), commandPort: new LocalPresenterCommandAdapter() };
  const fixtureId = new URLSearchParams(location.search).get("fixture") ?? "ready";
  const shell = new FixturePresenterReadAdapter(fixtureId);
  return {
    readPort: new FixtureReadOnlyAdapter(shell, fixtureId, () => FIXTURE_READ_COMPLETED_AT),
  };
}
