import type { PresenterSnapshot } from "./model";

export interface PresenterReadPort {
  read(): Promise<Readonly<PresenterSnapshot>>;
  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void;
}
