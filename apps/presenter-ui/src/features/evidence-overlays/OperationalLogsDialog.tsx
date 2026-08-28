import type { TeamView } from "../../domain";
import { Modal } from "../../shared/components";

export function OperationalLogsDialog({ team, redactionNotice, onClose }: { team: TeamView; redactionNotice: string; onClose: () => void }) {
  const isPlatform = team.id === "platform";
  const label = isPlatform ? "Platform Logs" : "Operational Logs";
  return (
    <Modal title={`${team.name} · ${label}`} subtitle="Read-only fixture · exact owning-team scope" onClose={onClose}>
      <div className="modal-summary">{isPlatform ? "VDP diagnostics originate in the native systemd journal and are represented only through the AosEdge/AosCloud delivery path." : "Service logs are represented only for the exact selected running Service scope."} This fixture cannot request, refresh or delete an external log.</div>
      <dl className="detail-grid">
        <dt>Requested by</dt><dd>{team.name}</dd>
        <dt>Scope</dt><dd>{isPlatform ? "Current Unit/system/VDP" : "Current Service instance and owning provider"}</dd>
        <dt>Status</dt><dd>Fixture result ready · no status re-read submitted</dd>
        <dt>Source</dt><dd>{isPlatform ? "Native systemd journal via AosEdge/AosCloud log delivery" : "AosCloud native Service-log delivery representation"}</dd>
        <dt>Disclosure</dt><dd>{redactionNotice}</dd>
        <dt>Retention</dt><dd>{isPlatform ? "No VDP or Demo UI log store" : "No second Demo UI archive"} · no unrestricted raw output</dd>
      </dl>
    </Modal>
  );
}
