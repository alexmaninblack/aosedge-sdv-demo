import { useCallback, useEffect } from "react";
import type { Perspective, ReleaseView, TeamId } from "../domain";
import { usePresenterReadModel } from "./state/PresenterReadModelProvider";
import { usePresentationState } from "./state/usePresentationState";
import { GlobalLifecyclePage } from "../features/global-lifecycle";
import { ActionPreviewDialog, DetailsDialog, OperationalLogsDialog } from "../features/evidence-overlays";
import { PresenterWorkspace } from "../shared/layout";
import { ProducerWorkspace } from "./ProducerWorkspace";
import { SharedHeader } from "./SharedHeader";
import { LocalLifecyclePage } from "../features/global-lifecycle/LocalLifecyclePage";
import { OperationProgress, usePresenterControls } from "./state/PresenterControls";

export function PresenterApp() {
  const snapshot = usePresenterReadModel();
  const controls = usePresenterControls();
  const [presentation, dispatch] = usePresentationState(snapshot.localDemo ? "global" : "platform");
  const surface = window.location.hash === "#native-header" ? "header" : window.location.hash === "#native-browser" ? "browser" : null;
  const navigate = useCallback((perspective: Perspective) => {
    dispatch({ type: "navigate", perspective });
    const native = window as Window & { webkit?: { messageHandlers?: { navigation?: { postMessage: (value: string) => void } } } };
    native.webkit?.messageHandlers?.navigation?.postMessage(perspective);
  }, [dispatch]);
  useEffect(() => {
    const receive = (event: Event) => {
      const perspective: unknown = (event as CustomEvent).detail;
      if (perspective === "global" || perspective === "platform" || perspective === "brake" || perspective === "tire") {
        dispatch({ type: "navigate", perspective });
      }
    };
    window.addEventListener("presenter-navigation", receive);
    return () => window.removeEventListener("presenter-navigation", receive);
  }, [dispatch]);
  const overlay = presentation.openOverlay;
  const overlayTeam = overlay?.team ? snapshot.teams[overlay.team] : undefined;
  const overlayRelease: ReleaseView | undefined = overlayTeam?.releases.find((item) => item.id === overlay?.releaseId);
  const closeOverlay = useCallback(() => dispatch({ type: "close-overlay" }), [dispatch]);

  return (
    <div className={`app-shell${snapshot.localDemo ? " local-demo-shell" : ""}${surface ? " native-" + surface : ""}`}>
      <SharedHeader snapshot={snapshot} perspective={presentation.perspective} onNavigate={navigate} />
      <div className="fixture-ribbon" role="note"><strong>{snapshot.localDemo ? "LOCAL DEMO CONTROL" : "FIXTURE ONLY"}</strong><span>{snapshot.localDemo ? controls.session ? "Test VDP actions · Production FOTA deferred" : "Connecting native session…" : snapshot.fixtureLabel}</span></div>
      <PresenterWorkspace snapshot={snapshot}>
        {presentation.actionNotice ? <div className="action-notice" role="status">{presentation.actionNotice}</div> : null}
        {presentation.perspective === "global"
          ? snapshot.localDemo ? <LocalLifecyclePage snapshot={snapshot} onPlatform={() => navigate("platform")} /> : <GlobalLifecyclePage view={snapshot.global} assetFailure={snapshot.assetFailure} eventChain={snapshot.eventChain} onAction={(action) => dispatch({ type: "open-action", action })} />
          : <ProducerWorkspace teamId={presentation.perspective as TeamId} snapshot={snapshot} presentation={presentation} dispatch={dispatch} />}
        {snapshot.localDemo && <OperationProgress />}
        {overlay?.kind === "details" && overlayRelease ? <DetailsDialog release={overlayRelease} redactionNotice={snapshot.redactionNotice} onClose={closeOverlay} /> : null}
        {overlay?.kind === "logs" && overlayTeam ? <OperationalLogsDialog team={overlayTeam} redactionNotice={snapshot.redactionNotice} onClose={closeOverlay} /> : null}
        {overlay?.kind === "action" && overlay.action ? <ActionPreviewDialog action={overlay.action} team={overlayTeam} release={overlayRelease} onClose={closeOverlay} onConfirm={() => dispatch({ type: "confirm-fixture-action", action: overlay.action! })} /> : null}
      </PresenterWorkspace>
    </div>
  );
}
