import type { Perspective, PresenterSnapshot, TeamId, VehicleRole } from "../domain";
import { CurrentVehicleIndicator } from "../features/vehicle-context";
import { Icon } from "../shared/components";
import { StudioIcon } from "./StudioWorkspace";
import logo from "../assets/studio/aosedge.svg";

export function vehicleLabel(role: VehicleRole | null): string {
  return role === "test" ? "Test Vehicle" : role === "production" ? "Production Vehicle" : role === "changing" ? "Changing vehicle..." : role === "unavailable" ? "Current Vehicle unavailable" : "Not assigned";
}

export function SharedHeader({ snapshot, perspective, onNavigate }: { snapshot: PresenterSnapshot; perspective: Perspective; onNavigate: (value: Perspective) => void }) {
  const teams: TeamId[] = ["platform", "brake", "tire"];
  return (
    <header className="shared-header">
      <div className="brand-row">
        <button className="title-button" type="button" aria-label="AosEdge Software Evolution Demo" onClick={() => onNavigate("global")} aria-pressed={perspective === "global"}>
          {snapshot.localDemo && <img className="studio-logo" src={logo} alt="AosEdge" />}<strong>AosEdge Software Evolution Demo</strong>
        </button>
        <CurrentVehicleIndicator vehicle={snapshot.vehicle} assetFailure={snapshot.assetFailure} />
      </div>
      <nav className="team-tabs" aria-label="OEM producer perspectives">
        {teams.map((teamId) => {
          const team = snapshot.teams[teamId];
          return (
            <button key={teamId} className="team-tab" type="button" data-team={teamId} aria-pressed={perspective === teamId} onClick={() => onNavigate(teamId)}>
              {snapshot.localDemo ? <StudioIcon name={teamId} /> : <Icon name={teamId} label={team.name} broken={snapshot.assetFailure} />}
              <b>{team.name}</b>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
