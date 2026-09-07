import type { PresenterSnapshot } from "../../domain";
import { Icon } from "../components/Icon";
import { StatusBadge } from "../components/StatusBadge";

export function VehicleEvidenceReservations({ snapshot }: { snapshot: PresenterSnapshot }) {
  return (
    <aside className="native-reservations" aria-label="Reserved native vehicle evidence workspace">
      <section className="native-slot native-slot-carla" data-native-surface="carla">
        <div className="native-slot-label"><Icon name="vehicle" label="CARLA" broken={snapshot.assetFailure} /> CARLA · native vehicle scene</div>
        <div className="native-reservation-copy"><strong>{snapshot.localDemo ? "CARLA scene" : "Reserved for native CARLA window"}</strong><span>{snapshot.localDemo ? `Source: ${snapshot.localDemo.source.state} · native window not composed yet` : "Browser content intentionally absent"}</span></div>
      </section>
      <div className="native-lower-row">
        <section className="native-slot" data-native-surface="controller">
          <div className="native-slot-label"><Icon name="safe-stop" label="Vehicle Controller" broken={snapshot.assetFailure} /> Vehicle Controller · native</div>
          <div className="native-reservation-copy"><strong>{snapshot.localDemo ? "Autopilot · Safe Stop" : "Reserved for native Controller"}</strong><span>{snapshot.localDemo ? "Native Controller appears here after simulation starts" : "Safe Stop and connectivity stay outside the browser"}</span></div>
        </section>
        <section className="native-slot native-slot-terminal" data-native-surface="terminal">
          <div className="native-slot-label"><Icon name="signals" label="Engineering Telematics" broken={snapshot.assetFailure} /> Engineering Telematics · Terminal</div>
          <div className="terminal-lines" aria-label="Native terminal reservation">
            <span>TEXT-ONLY NATIVE TERMINAL</span><span>NO BITMAP OR INLINE IMAGE CONTENT</span><span>Gateway / KUKSA evidence remains surface-owned</span>
          </div>
        </section>
      </div>
      <div className="workspace-probe"><StatusBadge status={`Workspace ${snapshot.workspace.value ?? "INCOMPLETE"}`} /></div>
    </aside>
  );
}
