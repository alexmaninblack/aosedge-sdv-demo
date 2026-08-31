import type { ReleaseView } from "../../domain";
import { usePresenterReadModel } from "../../app/state/PresenterReadModelProvider";
import { Modal } from "../../shared/components";

export function DetailsDialog({ release, redactionNotice, onClose }: { release: ReleaseView; redactionNotice: string; onClose: () => void }) {
  const readOnly = usePresenterReadModel().readOnly;
  const releaseEvidence = readOnly?.releases.value?.map((item) => `${item.kind}: ${item.state} · ${item.fingerprint}`).join(" | ");
  const rows: Array<[string, string]> = [
    ["Producer", release.team === "platform" ? "Platform Team" : release.team === "brake" ? "Brake Team" : "Tire Team"],
    ["Prepared artifact", release.details.artifact],
    ["Integrity", release.details.digest],
    ["Dependency", release.details.dependency],
    ["Access / permissions", release.details.access],
    ...(release.details.quota ? [["Approved Service quota", release.details.quota] as [string, string]] : []),
    ["Current target", release.details.target],
    ["Evidence", release.details.evidence],
  ];
  if (readOnly) {
    rows.push(
      ["Read contract", `${readOnly.contractClass} · fixture — not live`],
      ["OEM session", `${readOnly.session.state} · ${readOnly.session.value?.role ?? "not confirmed"} · ${readOnly.session.transport}`],
      ["Effective read permissions", readOnly.session.value?.effectivePermissions.join(", ") ?? "not current"],
      ["Lifecycle objects", releaseEvidence ?? "not current"],
      ["Source and freshness", `${readOnly.releases.source.owner} · ${readOnly.releases.state} · ${readOnly.releases.readCompletedAt}`],
      ["Shell source reference", `Deterministic fixture · ${readOnly.session.state} · not live AosEdge state`],
    );
  } else {
    rows.push(["Source and freshness", "Deterministic fixture · current · not live AosEdge state"]);
  }
  rows.push(["Disclosure", redactionNotice]);
  return (
    <Modal title={`${release.title} · Details`} subtitle="Read-only · selected release and stage context preserved" onClose={onClose}>
      <div className="modal-summary">{release.details.summary}</div>
      <dl className="detail-grid">{rows.map(([label, value]) => <div key={label} style={{ display: "contents" }}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    </Modal>
  );
}
