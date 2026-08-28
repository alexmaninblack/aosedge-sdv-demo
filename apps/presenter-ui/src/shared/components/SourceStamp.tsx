import type { Observed } from "../../domain";

export function SourceStamp({ observed }: { observed: Observed<unknown> }) {
  return (
    <div className="source-stamp" data-state={observed.state}>
      <span>Source: {observed.source.owner} · {observed.source.system}</span>
      <span>Freshness: {observed.state}{observed.observedAt ? ` · ${observed.observedAt}` : ""}</span>
      {observed.reason ? <strong>{observed.reason}</strong> : null}
    </div>
  );
}
