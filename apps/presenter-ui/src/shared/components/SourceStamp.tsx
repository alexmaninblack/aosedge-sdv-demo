import type { Observed, ReadObservation } from "../../domain";

function isReadObservation(observed: Observed<unknown> | ReadObservation<unknown>): observed is ReadObservation<unknown> {
  return "readCompletedAt" in observed;
}

export function SourceStamp({ observed }: { observed: Observed<unknown> | ReadObservation<unknown> }) {
  if (isReadObservation(observed)) {
    return (
      <div className="source-stamp" data-state={observed.state}>
        <span>Source: {observed.source.owner} · {observed.source.sourceClass} · {observed.source.contractClass}</span>
        <span>Freshness: {observed.state} · {observed.transport} · policy {observed.source.freshnessPolicyId}</span>
        <span>Source time: {observed.sourceTimestamp ?? "not exposed"} · Read completed: {observed.readCompletedAt}</span>
        {observed.reason ? <strong>{observed.reason}</strong> : null}
      </div>
    );
  }
  return (
    <div className="source-stamp" data-state={observed.state}>
      <span>Source: {observed.source.owner} · {observed.source.system}</span>
      <span>Freshness: {observed.state}{observed.observedAt ? ` · ${observed.observedAt}` : ""}</span>
      {observed.reason ? <strong>{observed.reason}</strong> : null}
    </div>
  );
}
