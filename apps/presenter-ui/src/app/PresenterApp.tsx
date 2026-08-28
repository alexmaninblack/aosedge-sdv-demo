import { useCallback } from "react";
import type { Perspective, ReleaseView, TeamId } from "../domain";
import { usePresenterReadModel } from "./state/PresenterReadModelProvider";
import { usePresentationState } from "./state/usePresentationState";
import { GlobalLifecyclePage } from "../features/global-lifecycle";
import { ActionPreviewDialog, DetailsDialog, OperationalLogsDialog } from "../features/evidence-overlays";
import { PresenterWorkspace } from "../shared/layout";
import { ProducerWorkspace } from "./ProducerWorkspace";
import { SharedHeader } from "./SharedHeader";

export function PresenterApp() {
  const snapshot = usePresenterReadModel();
  const [presentation, dispatch] = usePresentationState();
  const navigate = useCallback((perspective: Perspective) => dispatch({ type: "navigate", perspective }), [dispatch]);
  const overlay = presentation.openOverlay;
  const overlayTeam = overlay?.team ? snapshot.teams[overlay.team] : undefined;
  const overlayRelease: ReleaseView | undefined = overlayTeam?.releases.find((item) => item.id === overlay?.releaseId);
  const closeOverlay = useCallback(() => dispatch({ type: "close-overlay" }), [dispatch]);

  return (
    <div className="app-shell">
      <SharedHeader snapshot={snapshot} perspective={presentation.perspective} onNavigate={navigate} />
      <div className="fixture-ribbon" role="note"><strong>FIXTURE ONLY</strong><span>{snapshot.fixtureLabel}</span></div>
      <PresenterWorkspace snapshot={snapshot}>
        {presentation.actionNotice ? <div className="action-notice" role="status">{presentation.actionNotice}</div> : null}
        {presentation.perspective === "global"
          ? <GlobalLifecyclePage view={snapshot.global} assetFailure={snapshot.assetFailure} eventChain={snapshot.eventChain} onAction={(action) => dispatch({ type: "open-action", action })} />
          : <ProducerWorkspace teamId={presentation.perspective as TeamId} snapshot={snapshot} presentation={presentation} dispatch={dispatch} />}
        {overlay?.kind === "details" && overlayRelease ? <DetailsDialog release={overlayRelease} redactionNotice={snapshot.redactionNotice} onClose={closeOverlay} /> : null}
        {overlay?.kind === "logs" && overlayTeam ? <OperationalLogsDialog team={overlayTeam} redactionNotice={snapshot.redactionNotice} onClose={closeOverlay} /> : null}
        {overlay?.kind === "action" && overlay.action ? <ActionPreviewDialog action={overlay.action} team={overlayTeam} release={overlayRelease} onClose={closeOverlay} onConfirm={() => dispatch({ type: "confirm-fixture-action", action: overlay.action! })} /> : null}
      </PresenterWorkspace>
    </div>
  );
}
