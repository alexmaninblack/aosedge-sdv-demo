import type { Observed, VehicleRole } from "../../domain";
import { Icon } from "../../shared/components";

const labels: Record<VehicleRole, string> = {
  "not-assigned": "Current vehicle · Not assigned",
  test: "Current vehicle · Test Vehicle",
  production: "Current vehicle · Production Vehicle",
  changing: "Changing vehicle...",
  unavailable: "Current Vehicle unavailable",
};

export function CurrentVehicleIndicator({ vehicle, assetFailure, connectionLabel }: { vehicle: Observed<VehicleRole>; assetFailure: boolean; connectionLabel?: string }) {
  const role = vehicle.value ?? "unavailable";
  return (
    <div className={`vehicle-pill vehicle-${role}`} title={vehicle.reason}>
      <Icon name={role === "unavailable" ? "unavailable" : "vehicle"} label="Current vehicle" broken={assetFailure} />
      <span>{labels[role]}{connectionLabel && <small className="vehicle-connection">{connectionLabel}</small>}</span>
    </div>
  );
}
