import type { TeamView } from "../../domain";
import { Modal } from "../../shared/components";

export function OperationalLogsDialog({ team, redactionNotice, onClose }: { team: TeamView; redactionNotice: string; onClose: () => void }) {
  return (
    <Modal title={`${team.name} · Operational Logs`} subtitle="Read-only fixture · exact owning-team scope" onClose={onClose}>
      <div className="modal-summary">Logs are represented only for the exact selected running product scope. This fixture cannot request, refresh or delete an external log.</div>
      <dl className="detail-grid">
        <dt>Requested by</dt><dd>{team.name}</dd>
        <dt>Scope</dt><dd>{team.id === "platform" ? "Current Component and Unit" : "Current Service instance and owning provider"}</dd>
        <dt>Status</dt><dd>Fixture result ready · no status re-read submitted</dd>
        <dt>Source</dt><dd>AosCloud native log delivery representation</dd>
        <dt>Disclosure</dt><dd>{redactionNotice}</dd>
        <dt>Retention</dt><dd>No second archive · no unrestricted raw output</dd>
      </dl>
    </Modal>
  );
}
