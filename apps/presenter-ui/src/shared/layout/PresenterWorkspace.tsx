import type { ReactNode } from "react";
import type { PresenterSnapshot } from "../../domain";
import { VehicleEvidenceReservations } from "./VehicleEvidenceReservations";

export function PresenterWorkspace({ snapshot, children }: { snapshot: PresenterSnapshot; children: ReactNode }) {
  return (
    <main className="presenter-workspace">
      <VehicleEvidenceReservations snapshot={snapshot} />
      <section className="browser-workspace" aria-label="Presenter browser workspace">{children}</section>
    </main>
  );
}
