import type { Clock, PresenterReadPort, PresenterSnapshot } from "../../domain";
import { composePresenterSnapshot } from "./composePresenterSnapshot";
import { readOnlyFixtureById } from "./fixtureCatalog";
import { validateReadRequest } from "./contracts";

export class FixtureReadOnlyAdapter implements PresenterReadPort {
  readonly #base: PresenterReadPort;
  readonly #fixtureId: string;
  readonly #clock: Clock;

  constructor(base: PresenterReadPort, fixtureId: string, clock: Clock) {
    this.#base = base;
    this.#fixtureId = fixtureId;
    this.#clock = clock;
    this.#validatePackage();
  }

  #validatePackage(): void {
    const fixture = readOnlyFixtureById(this.#fixtureId);
    if (fixture.contractClass !== "CONTRACT_SYNTHETIC") throw new Error("FIXTURE_PROVENANCE_REQUIRED");
    fixture.plans.forEach(validateReadRequest);
  }

  async read(): Promise<Readonly<PresenterSnapshot>> {
    const base = await this.#base.read();
    return composePresenterSnapshot(base, readOnlyFixtureById(this.#fixtureId), this.#clock);
  }

  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void {
    return this.#base.subscribe((base) => {
      listener(composePresenterSnapshot(base, readOnlyFixtureById(this.#fixtureId), this.#clock));
    });
  }
}
