import type { TeamView } from "../../domain";
import { Modal, SourceStamp } from "../../shared/components";

export function OperationalLogsDialog({ team, redactionNotice, onClose }: { team: TeamView; redactionNotice: string; onClose: () => void }) {
  const isPlatform = team.id === "platform";
  const label = isPlatform ? "Platform Logs" : "Operational Logs";
  const logs = team.logs;
  const states = logs?.value?.map((item) => `${item.cloudState} · ${item.requestFingerprint}`).join(" | ") ?? "No current scoped log metadata";
  return (
    <Modal title={`${team.name} · ${label}`} subtitle="Read-only fixture · exact owning-team scope" onClose={onClose}>
      <div className="modal-summary">
        {isPlatform
          ? "Unit-log metadata belongs to the exact OEM Current Unit scope."
          : team.id === "brake"
            ? "Service-log metadata belongs only to the Brake Service Provider and selected Brake Service scope."
            : "Tire Service-log integration is not part of this read-only increment."}
        {" "}This fixture cannot request, refresh or delete an external log. Raw download is also outside this read-only increment.
      </div>
      <dl className="detail-grid">
        <dt>Requested by</dt><dd>{team.name}</dd>
        <dt>Scope</dt><dd>{isPlatform ? "Current Unit/system/VDP" : team.id === "brake" ? "Current Service instance and owning provider" : "NOT_APPLICABLE"}</dd>
        <dt>Delivery source</dt><dd>{isPlatform ? "Native systemd journal via AosEdge/AosCloud log delivery" : team.id === "brake" ? "AosCloud native Service-log delivery representation" : "NOT_APPLICABLE"}</dd>
        <dt>Authoritative Cloud states</dt><dd>{states}</dd>
        <dt>Source class</dt><dd>{logs?.source.sourceClass ?? "NOT_APPLICABLE"}</dd>
        <dt>Disclosure</dt><dd>{redactionNotice}</dd>
        <dt>Retention</dt><dd>{isPlatform ? "No VDP or Demo UI log store" : "No second Demo UI archive"} · {logs?.value?.[0]?.retentionNotice ?? "Retention policy not exposed by current API"}</dd>
        <dt>Raw content</dt><dd>Not exposed by this fixture-first read projection</dd>
      </dl>
      {logs ? <SourceStamp observed={logs} /> : null}
    </Modal>
  );
}
