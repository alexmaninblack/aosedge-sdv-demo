import type { PresenterReadPort } from "../../domain";
import type { PresenterCommandPort } from "../../domain/presenterCommandPort";

export interface PresenterDependencies {
  readPort: PresenterReadPort;
  commandPort?: PresenterCommandPort;
}
