import type { PresenterReadPort, PresenterSnapshot } from "../../domain";
import { fixtureById } from "./fixtureCatalog";
import { validateFixture } from "./validateFixture";

function deepFreeze<T>(value: T): Readonly<T> {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach((entry) => deepFreeze(entry));
  }
  return value;
}

export class FixturePresenterReadAdapter implements PresenterReadPort {
  readonly #snapshot: Readonly<PresenterSnapshot>;

  constructor(fixtureId: string) {
    const snapshot = fixtureById(fixtureId);
    const errors = validateFixture(snapshot);
    if (errors.length) throw new Error(`Invalid presenter fixture: ${errors.join("; ")}`);
    this.#snapshot = deepFreeze(snapshot);
  }

  async read(): Promise<Readonly<PresenterSnapshot>> {
    return this.#snapshot;
  }

  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void {
    listener(this.#snapshot);
    return () => undefined;
  }
}
