import type { ReleaseView } from "../../domain";
import { Modal } from "../../shared/components";

export function DetailsDialog({ release, redactionNotice, onClose }: { release: ReleaseView; redactionNotice: string; onClose: () => void }) {
  const rows: Array<[string, string]> = [
    ["Producer", release.team === "platform" ? "Platform Team" : release.team === "brake" ? "Brake Team" : "Tire Team"],
    ["Prepared artifact", release.details.artifact],
    ["Integrity", release.details.digest],
    ["Dependency", release.details.dependency],
    ["Access / permissions", release.details.access],
    ...(release.details.quota ? [["Approved Service quota", release.details.quota] as [string, string]] : []),
    ["Current target", release.details.target],
    ["Evidence", release.details.evidence],
    ["Source and freshness", "Deterministic fixture · current · not live AosEdge state"],
    ["Disclosure", redactionNotice],
  ];
  return (
    <Modal title={`${release.title} · Details`} subtitle="Read-only · selected release and stage context preserved" onClose={onClose}>
      <div className="modal-summary">{release.details.summary}</div>
      <dl className="detail-grid">{rows.map(([label, value]) => <div key={label} style={{ display: "contents" }}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    </Modal>
  );
}
