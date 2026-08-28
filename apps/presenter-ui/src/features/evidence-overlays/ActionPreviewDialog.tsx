import type { ReleaseView, TeamView } from "../../domain";
import { Modal } from "../../shared/components";

export function ActionPreviewDialog({ action, team, release, onClose, onConfirm }: {
  action: string;
  team?: TeamView;
  release?: ReleaseView;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal
      title={action}
      subtitle="Fixture-only protected-action preview"
      onClose={onClose}
      footer={<><button className="button" onClick={onClose}>Cancel</button><button className="button button-primary" onClick={onConfirm}>Confirm fixture presentation</button></>}
    >
      <div className="modal-summary">This button cannot call AosCloud, a helper, a backend, CARLA, a VM or a Unit. Confirmation changes presentation state only.</div>
      <dl className="detail-grid">
        <dt>Organizational actor</dt><dd>{action.includes("Authorize") ? "OEM Release Authority" : team?.name ?? "Demo Orchestrator"}</dd>
        <dt>Candidate</dt><dd>{release?.title ?? "Global fixture chapter"}</dd>
        <dt>Target</dt><dd>{release?.details.target ?? "Current fixture lifecycle"}</dd>
        <dt>Prerequisites</dt><dd>Deterministic fixture facts shown for interaction review only</dd>
        <dt>External submission</dt><dd>Impossible in IMP-01</dd>
        <dt>Authoritative result</dt><dd>Not claimed; no optimistic lifecycle completion</dd>
      </dl>
    </Modal>
  );
}
