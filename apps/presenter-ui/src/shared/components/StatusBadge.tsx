export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const tone = normalized.match(/uncertain|failed|error|unavailable/) ? "danger"
    : normalized.match(/waiting|blocked|stale|offline|submitting|reconcil/) ? "warning"
      : normalized.match(/ready|current|qualified|complete|healthy|connected/) ? "success"
        : "neutral";
  return <span className={`status-badge status-${tone}`}>{status}</span>;
}
