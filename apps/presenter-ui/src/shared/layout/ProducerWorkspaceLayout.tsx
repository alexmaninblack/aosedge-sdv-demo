import type { ReactNode } from "react";

export function ProducerWorkspaceLayout({ heading, authority, summaries, evidence, releases, releaseRef, onReleaseScroll, onFocusCapture }: {
  heading: ReactNode;
  authority: ReactNode;
  summaries: ReactNode;
  evidence: ReactNode;
  releases: ReactNode;
  releaseRef: React.RefObject<HTMLDivElement | null>;
  onReleaseScroll: () => void;
  onFocusCapture: (focusId: string | null) => void;
}) {
  return (
    <div className="producer-page">
      <div className="team-context" data-testid="fixed-team-context">
        {heading}
        {authority}
        {summaries}
        {evidence}
      </div>
      <div className="release-scroll" data-testid="release-scroll" ref={releaseRef} onScroll={onReleaseScroll} onFocusCapture={(event) => onFocusCapture((event.target as HTMLElement).dataset.focusId ?? null)}>
        {releases}
      </div>
    </div>
  );
}
