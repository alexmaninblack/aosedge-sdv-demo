import type { PresenterSnapshot } from "./model";
import type { PlatformCloudObservation } from "./platformObservation";

export interface PresenterReadPort {
  read(): Promise<Readonly<PresenterSnapshot>>;
  readPlatform?(): Promise<PlatformCloudObservation>;
  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void;
}
