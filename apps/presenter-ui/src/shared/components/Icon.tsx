import { useState } from "react";
import type { TeamId } from "../../domain";
import vehicle from "../../assets/icons/image2.png";
import platform from "../../assets/icons/image4.png";
import authority from "../../assets/icons/image7.png";
import brake from "../../assets/icons/image8.png";
import tire from "../../assets/icons/image11.png";
import unavailable from "../../assets/icons/image12.png";
import qualification from "../../assets/icons/qualification-evidence.png";
import logs from "../../assets/icons/operational-logs.png";
import quota from "../../assets/icons/service-quota-isolation.png";
import safeStop from "../../assets/icons/vehicle-safe-stop.png";
import signals from "../../assets/icons/vehicle-signals-vss.png";
import recovery from "../../assets/icons/recovery-reconcile.png";
import reset from "../../assets/icons/end-reset-demo.png";
import connectivity from "../../assets/icons/connectivity-available.png";

export type IconName = TeamId | "vehicle" | "authority" | "unavailable" | "qualification" | "logs" | "quota" | "safe-stop" | "signals" | "recovery" | "reset" | "connectivity";

const icons: Record<IconName, string> = {
  platform,
  brake,
  tire,
  vehicle,
  authority,
  unavailable,
  qualification,
  logs,
  quota,
  "safe-stop": safeStop,
  signals,
  recovery,
  reset,
  connectivity,
};

export interface IconProps {
  name: IconName;
  label: string;
  broken?: boolean;
  className?: string;
}

export function Icon({ name, label, broken = false, className = "" }: IconProps) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <span className={`icon-fallback ${className}`} role="img" aria-label={`${label} icon unavailable`}>{label.slice(0, 2).toUpperCase()}</span>;
  }
  return (
    <img
      className={`ui-icon ${className}`}
      src={broken ? "/missing-presenter-icon.png" : icons[name]}
      alt=""
      aria-hidden="true"
      onError={() => setFailed(true)}
    />
  );
}
